"""Creative Exploration Engine — read / write ``creative_routes.json`` (Issue #56).

Mono-concern (PERSISTENCE axis): pure file I/O, no business logic, no LLM
calls. Atomic writes via ``tmpfile + os.replace`` so a crash mid-write
never leaves a partial JSON on disk (the existing file is preserved or
the new one is fully present).

Pattern is identical to ``growthcro.opportunities.persist`` and
``growthcro.scoring.persist`` — repo-wide convention. Reuse intentional
so reviewers can pattern-match.

Path convention
---------------
``<root>/data/captures/<client_slug>/<page_type>/creative_routes.json``

``root`` defaults to the repo root (three parents up from this file, which
is ``moteur_gsg/creative_engine/persist.py``), matching the convention used
by ``growthcro.opportunities.persist``. Callers (tests, CLIs) can override
via ``root=`` for sandboxing under ``tmp_path``.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

from growthcro.models.creative_models import CreativeRouteBatch
from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def creative_routes_path(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Return the canonical on-disk path for one batch.

    Pure function — does not touch the filesystem.
    """
    base = (root or _DEFAULT_ROOT) / "data" / "captures" / client_slug / page_type
    return base / "creative_routes.json"


def save_creative_routes(
    batch: CreativeRouteBatch,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Write ``batch`` atomically to its canonical path. Returns the path.

    Atomic semantics: serialise to a tmpfile inside the destination
    directory, fsync it, then ``os.replace`` over the target. Same
    filesystem guarantees an atomic rename.
    """
    out = creative_routes_path(batch.client_slug, batch.page_type, root=root)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = batch.model_dump(mode="json")
    serialised = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)

    fd, tmp_name = tempfile.mkstemp(
        prefix=".creative_routes.",
        suffix=".json.tmp",
        dir=str(out.parent),
    )
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(serialised)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, out)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    logger.info(
        "creative_engine.routes.saved",
        extra={
            "client_slug": batch.client_slug,
            "page_type": batch.page_type,
            "routes_count": len(batch.routes),
            "path": str(out),
        },
    )
    return out


def load_creative_routes(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> CreativeRouteBatch | None:
    """Read the on-disk batch. Returns ``None`` when the file is absent.

    Validation is delegated to Pydantic — a malformed file raises
    ``pydantic.ValidationError`` (loud failure, intentional). The model
    has no computed fields so no pre-validation stripping is required
    (contrast with ``opportunities.persist`` which strips
    ``priority_score``).
    """
    path = creative_routes_path(client_slug, page_type, root=root)
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return CreativeRouteBatch.model_validate(raw)


__all__ = [
    "creative_routes_path",
    "load_creative_routes",
    "save_creative_routes",
]
