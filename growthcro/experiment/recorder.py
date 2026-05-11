"""Experiment Engine recorder — index + outcome import.

Issue #23. Mono-concern: filesystem index of all experiment specs across
clients, plus the outcome importer (post-experiment measurement).

Storage layout:
    data/experiments/<client>/<experiment_id>.json     ← spec (proposed/running/done)
    data/experiments/_index/experiments_index.json     ← derived index, regen-able

Public API:
    record_experiment(spec) -> Path           ← persist a spec atomically
    list_experiments(client?, status?) -> list[dict]  ← query the index
    rebuild_index() -> dict                   ← scan files, regen the index
    import_outcome(experiment_id, outcome, lift, confidence, notes?) -> dict
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = ROOT / "data" / "experiments"
INDEX_DIR = EXPERIMENTS_DIR / "_index"
INDEX_PATH = INDEX_DIR / "experiments_index.json"

VALID_OUTCOMES = ("won", "lost", "inconclusive")
VALID_STATUSES = ("proposed", "running", "stopped", "completed", "abandoned")


def record_experiment(spec: dict[str, Any]) -> pathlib.Path:
    """Persist a spec atomically. Returns the path.

    Idempotent: re-recording the same `experiment_id` overwrites.
    """
    client = spec.get("linked_reco", {}).get("client") or "unknown"
    exp_id = spec.get("experiment_id")
    if not exp_id:
        raise ValueError("spec missing 'experiment_id'")
    out_dir = EXPERIMENTS_DIR / client
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{exp_id}.json"
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    tmp.replace(out_path)
    return out_path


def _safe_load(path: pathlib.Path) -> Optional[dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _scan_specs() -> list[dict[str, Any]]:
    """Walk EXPERIMENTS_DIR and load every experiment spec (skipping _index)."""
    out: list[dict[str, Any]] = []
    if not EXPERIMENTS_DIR.exists():
        return out
    for client_dir in EXPERIMENTS_DIR.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue
        for spec_path in client_dir.glob("exp_*.json"):
            spec = _safe_load(spec_path)
            if spec:
                spec["_client"] = client_dir.name
                spec["_path"] = str(spec_path.relative_to(ROOT))
                out.append(spec)
    return out


def rebuild_index() -> dict[str, Any]:
    """Walk the experiments dir, rebuild the index JSON, return it."""
    specs = _scan_specs()
    by_status: dict[str, int] = {}
    by_client: dict[str, int] = {}
    by_ab_type: dict[str, int] = {}

    rows = []
    for s in specs:
        status = s.get("status", "unknown")
        ab_type = s.get("ab_type", "unspecified")
        client = s["_client"]
        by_status[status] = by_status.get(status, 0) + 1
        by_client[client] = by_client.get(client, 0) + 1
        by_ab_type[ab_type] = by_ab_type.get(ab_type, 0) + 1
        rows.append({
            "experiment_id": s.get("experiment_id"),
            "client": client,
            "page": (s.get("linked_reco") or {}).get("page"),
            "criterion_id": (s.get("linked_reco") or {}).get("criterion_id"),
            "ab_type": ab_type,
            "status": status,
            "outcome": s.get("outcome"),
            "winner": s.get("winner"),
            "lift_observed": s.get("lift_observed"),
            "confidence_observed": s.get("confidence_observed"),
            "created_at": s.get("created_at"),
            "outcome_at": s.get("outcome_at"),
            "path": s["_path"],
        })

    index = {
        "version": "v30.0.0-issue-23",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_experiments": len(rows),
        "by_status": dict(sorted(by_status.items())),
        "by_client": dict(sorted(by_client.items())),
        "by_ab_type": dict(sorted(by_ab_type.items())),
        "experiments": sorted(rows, key=lambda r: r.get("created_at") or ""),
    }
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    tmp.replace(INDEX_PATH)
    return index


def list_experiments(
    client: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Query the index (rebuilding it first to ensure freshness).

    Cheap because the filesystem scan is small (<1000 specs typical).
    """
    index = rebuild_index()
    rows = index["experiments"]
    if client:
        rows = [r for r in rows if r["client"] == client]
    if status:
        rows = [r for r in rows if r["status"] == status]
    return rows


def import_outcome(
    experiment_id: str,
    outcome: str,
    lift_observed: float,
    confidence_observed: float,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Update the spec for `experiment_id` with the measured outcome.

    Args:
        experiment_id: full experiment_id (e.g. exp_weglot_home_hero_01_20260511).
        outcome: one of `won` | `lost` | `inconclusive`.
        lift_observed: observed relative lift (e.g. 0.12 = +12%).
        confidence_observed: observed confidence (e.g. 0.957 = 95.7%).
        notes: optional free-text note for the audit trail.

    Returns:
        Dict with `ok=True` + spec summary, or `error=...` on failure.
    """
    if outcome not in VALID_OUTCOMES:
        return {"error": f"invalid outcome (must be one of {VALID_OUTCOMES})"}
    spec_path = _find_spec_path(experiment_id)
    if not spec_path:
        return {"error": f"experiment_id not found: {experiment_id}"}

    spec = _safe_load(spec_path)
    if not spec:
        return {"error": f"failed to load {spec_path}"}

    spec["outcome"] = outcome
    spec["winner"] = (
        "treatment" if outcome == "won" else ("control" if outcome == "lost" else None)
    )
    spec["lift_observed"] = round(lift_observed, 5)
    spec["confidence_observed"] = round(confidence_observed, 4)
    spec["outcome_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    spec["status"] = "completed"
    if notes:
        spec["outcome_notes"] = notes

    tmp = spec_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    tmp.replace(spec_path)

    rebuild_index()
    return {
        "ok": True,
        "experiment_id": experiment_id,
        "outcome": outcome,
        "lift_observed": lift_observed,
        "confidence_observed": confidence_observed,
    }


def _find_spec_path(experiment_id: str) -> Optional[pathlib.Path]:
    """Locate the spec file by experiment_id, searching all client dirs."""
    if not EXPERIMENTS_DIR.exists():
        return None
    for client_dir in EXPERIMENTS_DIR.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue
        candidate = client_dir / f"{experiment_id}.json"
        if candidate.exists():
            return candidate
    return None
