"""Persistence layer for multi-judge audit reports (Issue #54).

Mono-concern (PERSISTENCE axis): pure file I/O over the dict returned by
``run_multi_judge``. No business logic, no LLM calls, no shape validation
(the audit dict is heterogeneous across sub-judges; we persist as-is).

Why
---
Pre-#54, the orchestrator returned the full audit dict to RAM only.
``canonical_run_summary.json`` recorded telemetry (cost / wall / composite)
but not the detail (which killer rules failed, which gates failed, per
criterion breakdown). Post-hoc debugging was impossible, the webapp had
nothing to render, the learning layer was blind to per-run patterns.

This module writes the complete dict atomically to::

    <root>/data/captures/<client_slug>/<page_type>/multi_judge_audit.json

Atomic write semantics
----------------------
Serialise to a tmpfile in the destination directory, fsync, then
``os.replace`` over the target. Same filesystem guarantees an atomic
rename — a crash mid-write never leaves a partial JSON on disk (existing
file preserved or new file fully present). Same idiom as
``growthcro.opportunities.persist`` (Wave 1 #47).

Failure mode
------------
``save_multi_judge_audit`` is called from the orchestrator wrapped in a
``try / except`` so an I/O issue never breaks the audit run itself —
the dict is returned to the caller even if persistence fails.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import Any

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def multi_judge_audit_path(
    client_slug: str,
    page_type: str,
    *,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Return the canonical on-disk path for one audit.

    Pure function — does not touch the filesystem.
    """
    base = (root or _DEFAULT_ROOT) / "data" / "captures" / client_slug / page_type
    return base / "multi_judge_audit.json"


def save_multi_judge_audit(
    audit: dict[str, Any],
    client_slug: str,
    page_type: str,
    *,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Persist the complete audit dict atomically. Returns the path."""
    out = multi_judge_audit_path(client_slug, page_type, root=root)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ``default=str`` salvages any non-JSON-serialisable value (datetime,
    # Path, set, Pydantic enum) by stringifying it rather than crashing —
    # acceptable here because this artefact is for human debug + webapp
    # display, not for round-tripping back through Pydantic.
    serialised = json.dumps(audit, ensure_ascii=False, indent=2, default=str)

    fd, tmp_name = tempfile.mkstemp(
        prefix=".multi_judge_audit.",
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

    final = audit.get("final", {}) if isinstance(audit.get("final"), dict) else {}
    logger.info(
        "multi_judge_audit.persisted",
        extra={
            "client_slug": client_slug,
            "page_type": page_type,
            "final_score_pct": final.get("final_score_pct"),
            "verdict": final.get("verdict"),
            "killer_violations_count": len(final.get("killer_violations") or []),
            "non_shippable_reasons_count": len(final.get("non_shippable_reasons") or []),
            "path": str(out),
        },
    )
    return out


def load_multi_judge_audit(
    client_slug: str,
    page_type: str,
    *,
    root: pathlib.Path | None = None,
) -> dict[str, Any] | None:
    """Read the on-disk audit dict. Returns ``None`` if absent.

    A malformed file raises ``json.JSONDecodeError`` (loud failure,
    intentional — silent recovery would hide corruption).
    """
    path = multi_judge_audit_path(client_slug, page_type, root=root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
