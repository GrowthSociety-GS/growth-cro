"""Experiment Engine runner — emit experiment PROPOSALS (zero auto-trigger).

Issue #23. Given a set of recos for a (client, page) + a reality snapshot,
emit experiment proposals that Mathis can review + launch manually. Output
is `data/experiments/<client>/<exp_id>.json` with `status="proposed"`.

This module never starts a live experiment, never modifies the client's
LP, never calls Optimizely/VWO. It generates JSON specs.

5 A/B types canonical to GrowthCRO (per task spec):
    hero_copy             — vary the H1 / hero promise
    cta_wording           — vary the primary CTA label
    social_proof_position — vary above/below the fold
    form_fields_count     — vary 3 vs 5 fields
    pricing_display       — vary toggle annual/monthly default

Each AB_TYPE maps to a default mde_relative (lower for high-impact changes,
higher for cosmetic ones) and a default primary metric override when the
business_category does not give a strong default.

Public API:
    propose_experiments(client, page, reality_snapshot, recos, …) -> list[dict]
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Optional

from growthcro.experiment.engine import build_experiment_spec


AB_TYPES: dict[str, dict[str, Any]] = {
    "hero_copy": {
        "description": "Vary the H1 / hero promise",
        "mde_relative_default": 0.10,
        "primary_metric_override": None,
        "criterion_id_filters": ["hero_", "h1_", "headline_"],
    },
    "cta_wording": {
        "description": "Vary the primary CTA label (sign-up vs trial vs demo)",
        "mde_relative_default": 0.08,
        "primary_metric_override": "cta_click_rate",
        "criterion_id_filters": ["cta_", "button_"],
    },
    "social_proof_position": {
        "description": "Vary social proof position (above-the-fold vs below)",
        "mde_relative_default": 0.06,
        "primary_metric_override": None,
        "criterion_id_filters": ["social_proof_", "testimonial_", "trust_"],
    },
    "form_fields_count": {
        "description": "Vary form field count (e.g. 5 vs 3)",
        "mde_relative_default": 0.12,
        "primary_metric_override": "form_submit_rate",
        "criterion_id_filters": ["form_", "field_"],
    },
    "pricing_display": {
        "description": "Vary pricing display (annual vs monthly default toggle)",
        "mde_relative_default": 0.07,
        "primary_metric_override": None,
        "criterion_id_filters": ["pricing_", "price_"],
    },
}

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = ROOT / "data" / "experiments"


def _ab_type_for_reco(reco: dict[str, Any]) -> Optional[str]:
    """Heuristic: pick an AB type based on criterion_id prefix."""
    crit = (reco.get("criterion_id") or "").lower()
    for ab_type, meta in AB_TYPES.items():
        for prefix in meta["criterion_id_filters"]:
            if crit.startswith(prefix):
                return ab_type
    return None


def _extract_baseline_rate(
    reality_snapshot: dict[str, Any],
    fallback: float = 0.02,
) -> tuple[float, str]:
    """Find the most reliable conversion_rate in the snapshot. Returns
    (rate, source_label). Falls back to 0.02 if nothing usable."""
    computed = reality_snapshot.get("computed") or {}
    if computed.get("conversion_rate") is not None:
        return float(computed["conversion_rate"]), computed.get(
            "conversion_rate_source", "computed"
        )
    sources = reality_snapshot.get("sources") or {}
    for src_name in ("ga4", "catchr"):
        src = sources.get(src_name) or {}
        if src.get("conversion_rate") is not None:
            return float(src["conversion_rate"]), src_name
    return fallback, f"fallback:{fallback}"


def _extract_daily_traffic(
    reality_snapshot: dict[str, Any],
    fallback: int = 500,
) -> tuple[int, str]:
    """Estimate daily traffic from snapshot sessions / period_days."""
    sources = reality_snapshot.get("sources") or {}
    period_days = max(reality_snapshot.get("period_days") or 1, 1)
    for src_name in ("ga4", "catchr"):
        src = sources.get(src_name) or {}
        sessions = src.get("sessions")
        if sessions:
            return max(int(sessions) // period_days, 1), src_name
    return fallback, f"fallback:{fallback}"


def propose_experiments(
    client: str,
    page: str,
    reality_snapshot: dict[str, Any],
    recos: list[dict[str, Any]],
    business_category: Optional[str] = None,
    max_proposals: int = 5,
    write: bool = True,
) -> list[dict[str, Any]]:
    """Generate experiment proposals from a list of recos + a reality snapshot.

    Args:
        client: client slug.
        page: page slug (e.g. "home", "lp_listicle_wordpress").
        reality_snapshot: output of `growthcro.reality.collect_reality_snapshot`.
        recos: list of reco dicts. Each should have criterion_id + before/after
               (or hypothesis). Recos with `priority="P0"` or `"P1"` are preferred.
        business_category: passed to engine for guardrails.
        max_proposals: cap output count (default 5 — task spec asks for 5).
        write: persist each proposal to
               data/experiments/<client>/<exp_id>.json (atomic).

    Returns:
        List of experiment spec dicts (each with status="proposed").
    """
    baseline_rate, baseline_src = _extract_baseline_rate(reality_snapshot)
    daily_traffic, traffic_src = _extract_daily_traffic(reality_snapshot)

    # Sort recos by priority (P0 first, then P1, P2, P3, P4 — string sort works)
    sorted_recos = sorted(
        recos,
        key=lambda r: (r.get("priority") or "P9", r.get("criterion_id") or ""),
    )

    proposals: list[dict[str, Any]] = []
    seen_ab_types: set[str] = set()

    for reco in sorted_recos:
        if len(proposals) >= max_proposals:
            break
        ab_type = _ab_type_for_reco(reco)
        if not ab_type or ab_type in seen_ab_types:
            # Try to diversify across AB types — first reco per type wins.
            continue
        seen_ab_types.add(ab_type)

        meta = AB_TYPES[ab_type]
        reco_with_keys = dict(reco)
        reco_with_keys["client"] = client
        reco_with_keys["page"] = page

        spec = build_experiment_spec(
            reco=reco_with_keys,
            baseline_conversion_rate=baseline_rate,
            daily_traffic=daily_traffic,
            mde_relative=meta["mde_relative_default"],
            business_category=business_category,
            primary_metric=meta["primary_metric_override"],
            variant_b_source="manual",
        )
        # Tag the AB type + the reality inputs used
        spec["ab_type"] = ab_type
        spec["ab_type_description"] = meta["description"]
        spec["reality_inputs"] = {
            "baseline_conversion_rate": baseline_rate,
            "baseline_source": baseline_src,
            "daily_traffic_estimate": daily_traffic,
            "daily_traffic_source": traffic_src,
            "reality_snapshot_date": reality_snapshot.get("snapshot_date"),
            "reality_snapshot_period_days": reality_snapshot.get("period_days"),
        }
        proposals.append(spec)

    if write:
        for spec in proposals:
            _persist_proposal(spec, client)

    return proposals


def _persist_proposal(spec: dict[str, Any], client: str) -> pathlib.Path:
    """Atomically write a proposal to data/experiments/<client>/<exp_id>.json."""
    out_dir = EXPERIMENTS_DIR / client
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{spec['experiment_id']}.json"
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    tmp.replace(out_path)
    return out_path


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")
