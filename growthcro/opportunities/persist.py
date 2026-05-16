"""Opportunity Layer — read / write ``opportunities.json`` (Issue #47).

Mono-concern (PERSISTENCE axis): pure file I/O, no business logic, no LLM
calls. Atomic writes via ``tmpfile + os.replace`` so a crash mid-write
never leaves a partial JSON on disk (the existing file is preserved or
the new one is fully present).

Path convention
---------------
``<root>/data/captures/<client_slug>/<page_type>/opportunities.json``

``root`` defaults to the repo root (two parents up from this file), which
matches the convention used by ``growthcro.scoring.persist`` for capture
artefacts. Callers (tests, CLIs) can override via ``root=`` for sandboxing.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

from growthcro.models.opportunity_models import OpportunityBatch
from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def opportunities_path(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Return the canonical on-disk path for one batch.

    Pure function — does not touch the filesystem.
    """
    base = (root or _DEFAULT_ROOT) / "data" / "captures" / client_slug / page_type
    return base / "opportunities.json"


def save_opportunities(
    batch: OpportunityBatch,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Write ``batch`` atomically to its canonical path. Returns the path.

    Atomic semantics: serialise to a tmpfile inside the destination
    directory, fsync it, then ``os.replace`` over the target. Same
    filesystem guarantees an atomic rename.
    """
    out = opportunities_path(batch.client_slug, batch.page_type, root=root)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = batch.model_dump(mode="json")
    serialised = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)

    fd, tmp_name = tempfile.mkstemp(
        prefix=".opportunities.",
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
        # On any failure, remove the tmpfile so the dir stays clean.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    logger.info(
        "opportunities.saved",
        extra={
            "client_slug": batch.client_slug,
            "page_type": batch.page_type,
            "count": len(batch.opportunities),
            "path": str(out),
        },
    )
    return out


# Computed fields are written to disk (useful for dashboards / external
# consumers) but must be stripped before re-validation because the models
# use ``extra='forbid'``. Keep this list in sync with the
# ``@computed_field`` declarations in
# ``growthcro/models/opportunity_models.py``.
_COMPUTED_FIELDS_OPPORTUNITY: frozenset[str] = frozenset({"priority_score"})


def _strip_opportunity_computed(opp: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in opp.items() if k not in _COMPUTED_FIELDS_OPPORTUNITY}


def load_opportunities(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> OpportunityBatch | None:
    """Read the on-disk batch. Returns ``None`` when the file is absent.

    Validation is delegated to Pydantic — a malformed file raises
    ``pydantic.ValidationError`` (loud failure, intentional).

    Computed fields persisted on disk are stripped before re-validation
    because the models use ``extra='forbid'``. They are recomputed
    deterministically on the way back out.
    """
    path = opportunities_path(client_slug, page_type, root=root)
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and isinstance(raw.get("opportunities"), list):
        raw["opportunities"] = [
            _strip_opportunity_computed(opp) if isinstance(opp, dict) else opp
            for opp in raw["opportunities"]
        ]
    return OpportunityBatch.model_validate(raw)
