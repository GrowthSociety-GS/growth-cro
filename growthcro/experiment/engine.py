"""Experiment Engine — sample-size calculator + spec builder.

Issue #23. Promoted (re-implemented mono-concern) from
`skills/site-capture/scripts/experiment_engine.py`. The math is unchanged:

- Sample size: z-test for proportions
    n_per_variant = (z_α/2 + z_β)² × (p1·(1-p1) + p2·(1-p2)) / (p2 - p1)²
- Inverse normal CDF: Beasley-Springer-Moro approximation, stdlib-only.
- Duration: max(raw_days, 14) — covers weekly seasonal cycles.
- Guardrails: defaults per business_category (ecommerce / saas / lead_gen).

Public API:
    compute_sample_size(baseline_rate, mde_relative, power, alpha) -> dict
    estimate_duration_days(sample_total, daily_traffic) -> dict
    select_guardrails(business_category) -> list[dict]
    build_experiment_spec(reco, baseline_conversion_rate, …) -> dict

No I/O — persistence lives in `growthcro/experiment/recorder.py`.
"""
from __future__ import annotations

import math
import time
from typing import Any, Optional


DEFAULT_GUARDRAILS: dict[str, list[dict[str, Any]]] = {
    "ecommerce": [
        {"metric": "aov", "direction": "no_degradation", "max_drop_pct": 0.05},
        {"metric": "refund_rate", "direction": "no_increase", "max_increase_pct": 0.10},
        {
            "metric": "checkout_abandonment",
            "direction": "no_increase",
            "max_increase_pct": 0.05,
        },
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
    ],
    "lead_gen": [
        {
            "metric": "lead_quality_score",
            "direction": "no_degradation",
            "max_drop_pct": 0.10,
        },
        {
            "metric": "form_abandonment",
            "direction": "no_increase",
            "max_increase_pct": 0.10,
        },
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
    ],
    "saas": [
        {
            "metric": "trial_to_paid_conversion",
            "direction": "no_degradation",
            "max_drop_pct": 0.05,
        },
        {
            "metric": "demo_request_quality",
            "direction": "no_degradation",
            "max_drop_pct": 0.10,
        },
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
    ],
    "default": [
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
        {"metric": "bounce_rate", "direction": "no_increase", "max_increase_pct": 0.05},
    ],
}


def select_guardrails(business_category: Optional[str]) -> list[dict[str, Any]]:
    return DEFAULT_GUARDRAILS.get(
        (business_category or "default").lower(), DEFAULT_GUARDRAILS["default"]
    )


def _z_score(percentile: float) -> float:
    """Inverse normal CDF approximation (no scipy)."""
    cached = {
        0.80: 0.8416,
        0.90: 1.2816,
        0.95: 1.6449,
        0.975: 1.96,
        0.99: 2.3263,
        0.995: 2.5758,
    }
    if percentile in cached:
        return cached[percentile]
    if percentile < 0 or percentile > 1:
        raise ValueError("percentile must be in [0,1]")
    if percentile < 0.5:
        return -_z_score(1 - percentile)
    p = percentile - 0.5
    r = p * p
    a = [-39.69683, 220.94609, -275.92851, 138.35775, -30.66479, 2.50662]
    b = [-54.47609, 161.58586, -155.69897, 66.80131, -13.28068]
    num = (
        ((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]
    ) * p
    den = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
    return num / den


def compute_sample_size(
    baseline_rate: float,
    mde_relative: float = 0.10,
    power: float = 0.80,
    alpha: float = 0.05,
    two_sided: bool = True,
) -> dict[str, Any]:
    """Sample size per variant for a 2-prop z-test.

    Returns a dict with `sample_size_per_variant` + diagnostics. On invalid
    input (baseline ≤ 0 or ≥ 1, etc.) returns `{"error": "..."}` without
    raising — keeps the caller pipeline simple.
    """
    if not (0 < baseline_rate < 1):
        return {"error": f"baseline_rate must be in (0, 1), got {baseline_rate}"}
    if not (0 < mde_relative < 5):
        return {"error": f"mde_relative must be in (0, 5), got {mde_relative}"}

    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde_relative)
    if p2 >= 1:
        return {"error": f"treatment rate p2={p2} >= 1, impossible"}

    if two_sided:
        z_alpha = 1.96 if alpha == 0.05 else _z_score(1 - alpha / 2)
    else:
        z_alpha = 1.645 if alpha == 0.05 else _z_score(1 - alpha)
    z_beta = _z_score(power)

    var_pooled = p1 * (1 - p1) + p2 * (1 - p2)
    delta = p2 - p1
    n = (z_alpha + z_beta) ** 2 * var_pooled / (delta**2)
    n = math.ceil(n)

    return {
        "baseline_rate": p1,
        "estimated_treatment_rate": round(p2, 5),
        "mde_relative": mde_relative,
        "mde_absolute": round(delta, 5),
        "alpha": alpha,
        "power": power,
        "two_sided": two_sided,
        "z_alpha": round(z_alpha, 3),
        "z_beta": round(z_beta, 3),
        "sample_size_per_variant": n,
        "sample_size_total": n * 2,
    }


def estimate_duration_days(sample_size_total: int, daily_traffic: int) -> dict[str, Any]:
    """Days needed (50/50 split, daily_traffic uniform). Adds 14-day minimum."""
    if daily_traffic <= 0:
        return {"error": "daily_traffic must be > 0"}
    raw_days = math.ceil(sample_size_total / daily_traffic)
    min_days = 14
    return {
        "raw_days": raw_days,
        "min_days_recommended": min_days,
        "duration_days": max(raw_days, min_days),
        "rationale": (
            "Min 14j to cover weekly seasonal cycles"
            if raw_days < min_days
            else "Sample size requirement"
        ),
    }


def build_experiment_spec(
    reco: dict[str, Any],
    baseline_conversion_rate: float,
    daily_traffic: int = 1000,
    mde_relative: float = 0.10,
    business_category: Optional[str] = None,
    primary_metric: Optional[str] = None,
    secondary_metrics: Optional[list[str]] = None,
    variant_b_source: str = "manual",
) -> dict[str, Any]:
    """Build a full experiment spec from a reco object.

    Args:
        reco: reco dict (criterion_id, before, after, hypothesis, evidence_ids…).
        baseline_conversion_rate: actual rate from Reality Layer (GA4/Catchr).
        daily_traffic: sessions/day from Reality Layer (orchestrator output).
        mde_relative: minimum effect to detect (default 10% relative).
        business_category: picks guardrails.
        primary_metric: defaults from business_category.
        secondary_metrics: defaults to a reasonable triplet.
        variant_b_source: "manual" | "gsg" | "claude_haiku" — metadata only.

    Returns:
        Spec dict ready to persist via `recorder.record_experiment`.
    """
    crit = reco.get("criterion_id", "unknown")
    exp_id = (
        f"exp_{reco.get('client', 'unknown')}_{reco.get('page', 'unknown')}_"
        f"{crit}_{time.strftime('%Y%m%d')}"
    )

    sample = compute_sample_size(baseline_conversion_rate, mde_relative=mde_relative)
    duration = estimate_duration_days(sample.get("sample_size_total", 0), daily_traffic)
    guardrails = select_guardrails(business_category)

    if primary_metric is None:
        primary_metric = {
            "ecommerce": "purchase_rate",
            "saas": "trial_signup_rate",
            "lead_gen": "form_submit_rate",
        }.get(
            (business_category or "").lower(), "landing_page_conversion_rate"
        )

    if secondary_metrics is None:
        secondary_metrics = ["cta_click_rate", "scroll_depth_50_pct", "session_duration"]

    return {
        "experiment_id": exp_id,
        "version": "v30.0.0-issue-23",
        "status": "proposed",  # never "running" auto — Mathis must launch
        "variant_b_source": variant_b_source,
        "linked_reco": {
            "criterion_id": crit,
            "client": reco.get("client"),
            "page": reco.get("page"),
            "evidence_ids": reco.get("evidence_ids", []),
        },
        "hypothesis": reco.get("hypothesis")
        or reco.get("why")
        or (
            f"If we apply '{(reco.get('after') or '')[:120]}', "
            f"{primary_metric} will improve by ≥ {mde_relative * 100:.0f}%."
        ),
        "variants": {
            "A_control": {
                "label": "Current LP (control)",
                "description": reco.get("before") or "Current state",
            },
            "B_treatment": {
                "label": "Proposed change (treatment)",
                "description": reco.get("after") or "Proposed change",
                "source": variant_b_source,
            },
        },
        "metrics": {
            "primary": primary_metric,
            "secondary": secondary_metrics,
            "guardrails": guardrails,
        },
        "design": {
            "type": "A/B (control vs treatment)",
            "split": "50/50",
            "traffic_allocation_pct": 1.0,
            "exclusion_criteria": ["bot traffic", "internal IPs", "QA accounts"],
        },
        "statistics": {**sample, "duration": duration},
        "ramp_up": {
            "phase_1_pct": 0.10,
            "phase_1_days": 1,
            "phase_2_pct": 0.50,
            "phase_2_days": 2,
            "full_pct": 1.00,
            "rationale": "Catch implementation bugs early on 10% before exposing 100%",
        },
        "kill_switches": [
            {"trigger": "javascript_error_rate > +50%", "action": "stop_immediately"},
            {"trigger": "primary_metric drops > 30%", "action": "stop_immediately"},
            {
                "trigger": "checkout_completion drops > 10%",
                "action": "review_within_24h",
            },
        ],
        "outcome": None,
        "outcome_at": None,
        "winner": None,
        "lift_observed": None,
        "confidence_observed": None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
