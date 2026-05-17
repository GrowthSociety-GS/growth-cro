"""Elite Mode persistence — atomic write of HTML candidates (Issue CR-09 #64).

Mono-concern (PERSISTENCE axis): pure file I/O, no business logic, no LLM
calls. Atomic writes via ``tmpfile + os.replace`` so a crash mid-write
never leaves a partial file on disk.

Layout on disk
--------------
``<root>/data/captures/<client_slug>/<page_type>/elite_candidates/``
  ├── <candidate_id>.html              # raw HTML, exact bytes from Opus
  ├── <candidate_id>.metadata.json     # HtmlCandidate Pydantic dump (sans html_content)
  ├── ...                              # one pair per candidate
  └── batch_meta.json                  # HtmlCandidateBatch.prompt_meta + identity scalars

The ``.html`` files are persisted raw (not nested in JSON) so a human can
``open`` them directly in a browser to inspect. The ``.metadata.json``
sidecars carry the typed metadata (cost / tokens / wall_seconds / etc.).

Codex Constraint Statements (verbatim, non-negotiable):
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output preserves layout/CSS/motion unless a deterministic gate
   finds a concrete blocking issue.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence between structured and elite modes happens at post-process
   gates, NEVER at rendering layer.

Pattern is identical to ``moteur_gsg.creative_engine.persist`` and
``growthcro.opportunities.persist`` — repo-wide convention.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

from growthcro.models.elite_models import HtmlCandidate, HtmlCandidateBatch
from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[3]


def elite_candidates_dir(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Return the canonical on-disk directory for one Elite batch.

    Pure function — does NOT touch the filesystem.
    """
    base = (root or _DEFAULT_ROOT) / "data" / "captures" / client_slug / page_type
    return base / "elite_candidates"


def _atomic_write_text(path: pathlib.Path, content: str, *, prefix: str) -> None:
    """Atomic tmpfile + ``os.replace`` write of UTF-8 text. Same fs only."""
    fd, tmp_name = tempfile.mkstemp(
        prefix=prefix,
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def save_html_candidates(
    batch: HtmlCandidateBatch,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Write ``batch`` atomically to its canonical directory. Returns the dir.

    Each candidate produces two files (``<id>.html`` raw + ``<id>.metadata.json``).
    Plus one ``batch_meta.json`` summary at the directory root.

    Atomic semantics per-file: serialize to tmpfile inside the destination
    directory, fsync, then ``os.replace`` over the target. Same-filesystem
    guarantees atomic rename.
    """
    out_dir = elite_candidates_dir(batch.client_slug, batch.page_type, root=root)
    out_dir.mkdir(parents=True, exist_ok=True)

    for candidate in batch.candidates:
        # Raw HTML — exact bytes from Opus.
        html_path = out_dir / f"{candidate.candidate_id}.html"
        _atomic_write_text(
            html_path,
            candidate.html_content,
            prefix=f".{candidate.candidate_id}.html.",
        )
        # Metadata sidecar — Pydantic dump minus html_content (already on disk).
        meta_path = out_dir / f"{candidate.candidate_id}.metadata.json"
        meta_payload = candidate.model_dump(mode="json", exclude={"html_content"})
        # Add html_chars for quick reading without loading the .html file.
        meta_payload["html_chars"] = len(candidate.html_content)
        _atomic_write_text(
            meta_path,
            json.dumps(meta_payload, indent=2, ensure_ascii=False),
            prefix=f".{candidate.candidate_id}.metadata.",
        )

    # Batch-level summary at directory root.
    batch_meta_path = out_dir / "batch_meta.json"
    batch_meta_payload: dict = {
        "client_slug": batch.client_slug,
        "page_type": batch.page_type,
        "business_category": batch.business_category,
        "candidate_ids": [c.candidate_id for c in batch.candidates],
        "prompt_meta": batch.prompt_meta,
    }
    _atomic_write_text(
        batch_meta_path,
        json.dumps(batch_meta_payload, indent=2, ensure_ascii=False),
        prefix=".batch_meta.",
    )

    logger.info(
        "elite.batch.saved",
        extra={
            "client_slug": batch.client_slug,
            "page_type": batch.page_type,
            "n_candidates": len(batch.candidates),
            "dir": str(out_dir),
        },
    )
    return out_dir


def load_html_candidates(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> HtmlCandidateBatch | None:
    """Read all candidates from the on-disk directory. ``None`` if absent.

    Reconstructs ``HtmlCandidateBatch`` by walking ``*.metadata.json``
    sidecars (each implies a sibling ``.html`` file).
    """
    out_dir = elite_candidates_dir(client_slug, page_type, root=root)
    if not out_dir.is_dir():
        return None
    batch_meta_path = out_dir / "batch_meta.json"
    if not batch_meta_path.is_file():
        return None

    batch_meta = json.loads(batch_meta_path.read_text(encoding="utf-8"))
    candidates: list[HtmlCandidate] = []
    for candidate_id in batch_meta.get("candidate_ids", []):
        meta_path = out_dir / f"{candidate_id}.metadata.json"
        html_path = out_dir / f"{candidate_id}.html"
        if not meta_path.is_file() or not html_path.is_file():
            logger.warning(
                "elite.batch.partial_load",
                extra={
                    "client_slug": client_slug,
                    "page_type": page_type,
                    "missing": candidate_id,
                },
            )
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        # html_chars is informational only — strip before re-validate (not on model).
        meta.pop("html_chars", None)
        meta["html_content"] = html_path.read_text(encoding="utf-8")
        candidates.append(HtmlCandidate.model_validate(meta))

    if not candidates:
        return None

    return HtmlCandidateBatch(
        client_slug=batch_meta["client_slug"],
        page_type=batch_meta["page_type"],
        business_category=batch_meta["business_category"],
        candidates=candidates,
        prompt_meta=batch_meta.get("prompt_meta", {}),
    )


__all__ = [
    "elite_candidates_dir",
    "load_html_candidates",
    "save_html_candidates",
]
