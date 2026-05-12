"""V27 — Experiment Engine : A/B test specs + sample size + guardrails.

Réponse à la roadmap ChatGPT §11 (V28 Experiment Engine) :
"A/B test specs, sample size, metric guardrails, outcome importer."

Pour chaque reco passant en `experiment_started` (Reco Lifecycle V26.B),
le système doit produire :
- Un experiment spec lisible (hypothesis, primary metric, MDE, sample size)
- Des guardrails (metrics qui ne doivent PAS dégrader)
- Un test plan (durée min, ramp-up, kill switches)
- Un outcome importer (post-mesure : winner/loser/inconclusive)

Le calcul de sample size utilise les statistiques classiques :
  n = (Z_alpha/2 + Z_beta)^2 × 2 × p × (1 - p) / MDE^2
  (Z_alpha/2 = 1.96 pour α=0.05 two-sided)
  (Z_beta = 0.84 pour power=80%)

Storage : data/captures/<client>/<page>/experiments/<exp_id>.json

Usage :
  from experiment_engine import build_experiment_spec, compute_sample_size

  spec = build_experiment_spec(
      reco={...},
      baseline_conversion_rate=0.034,
      mde_pct=0.10,  # detect 10% relative lift
      power=0.80,
      alpha=0.05,
  )
  # Returns dict with sample_size, duration_min_days, guardrails, test_plan
"""
from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"


# ────────────────────────────────────────────────────────────────
# Sample size calculation
# ────────────────────────────────────────────────────────────────

def compute_sample_size(baseline_rate: float, mde_relative: float = 0.10,
                        power: float = 0.80, alpha: float = 0.05,
                        two_sided: bool = True) -> dict:
    """Calcule le sample size par variant pour détecter un effet de taille
    `mde_relative` (relative lift, ex: 0.10 = +10%) sur `baseline_rate`.

    Formule classique pour proportions (z-test two-sample) :
      n_per_variant = (z_α/2 + z_β)² × (p1×(1-p1) + p2×(1-p2)) / (p2 - p1)²

    Args:
      baseline_rate : conversion rate actuelle (0-1)
      mde_relative  : Minimum Detectable Effect en relatif (0.10 = 10% lift)
      power         : 1 - β (default 80%)
      alpha         : seuil significativité (default 5%)
      two_sided     : test bilatéral

    Returns dict with sample_size_per_variant, sample_size_total,
    estimated_treatment_rate, mde_absolute.
    """
    if not (0 < baseline_rate < 1):
        return {"error": f"baseline_rate must be in (0, 1), got {baseline_rate}"}
    if not (0 < mde_relative < 5):
        return {"error": f"mde_relative must be in (0, 5), got {mde_relative}"}

    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde_relative)
    if p2 >= 1:
        return {"error": f"treatment rate p2={p2} >= 1, impossible"}

    # Z-scores (normal approx)
    if two_sided:
        z_alpha = 1.96 if alpha == 0.05 else _z_score(1 - alpha / 2)
    else:
        z_alpha = 1.645 if alpha == 0.05 else _z_score(1 - alpha)
    z_beta = _z_score(power)

    var_pooled = p1 * (1 - p1) + p2 * (1 - p2)
    delta = p2 - p1
    n = (z_alpha + z_beta) ** 2 * var_pooled / (delta ** 2)
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


def _z_score(percentile: float) -> float:
    """Inverse normal CDF approximation (no scipy needed)."""
    if percentile == 0.80: return 0.8416
    if percentile == 0.90: return 1.2816
    if percentile == 0.95: return 1.6449
    if percentile == 0.975: return 1.96
    if percentile == 0.99: return 2.3263
    if percentile == 0.995: return 2.5758
    # Beasley-Springer-Moro approximation
    if percentile < 0 or percentile > 1:
        raise ValueError("percentile must be in [0,1]")
    if percentile < 0.5:
        return -_z_score(1 - percentile)
    p = percentile - 0.5
    r = p * p
    a = [-39.69683, 220.94609, -275.92851, 138.35775, -30.66479, 2.50662]
    b = [-54.47609, 161.58586, -155.69897, 66.80131, -13.28068]
    num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * p
    den = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
    return num / den


def estimate_duration_days(sample_size_total: int, daily_traffic: int) -> dict:
    """Estim duration in days for the experiment (assuming 50/50 split).
    Adds a 14-day minimum (CXL/Optimizely standard for weekly cycle coverage)."""
    if daily_traffic <= 0:
        return {"error": "daily_traffic must be > 0"}
    raw_days = math.ceil(sample_size_total / daily_traffic)
    min_days = 14
    return {
        "raw_days": raw_days,
        "min_days_recommended": min_days,
        "duration_days": max(raw_days, min_days),
        "rationale": (
            "Min 14j to cover weekly seasonal cycles" if raw_days < min_days
            else "Sample size requirement"
        ),
    }


# ────────────────────────────────────────────────────────────────
# Guardrails — metrics qui ne doivent PAS dégrader
# ────────────────────────────────────────────────────────────────

DEFAULT_GUARDRAILS = {
    "ecommerce": [
        {"metric": "aov", "direction": "no_degradation", "max_drop_pct": 0.05},
        {"metric": "refund_rate", "direction": "no_increase", "max_increase_pct": 0.10},
        {"metric": "checkout_abandonment", "direction": "no_increase", "max_increase_pct": 0.05},
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
    ],
    "lead_gen": [
        {"metric": "lead_quality_score", "direction": "no_degradation", "max_drop_pct": 0.10},
        {"metric": "form_abandonment", "direction": "no_increase", "max_increase_pct": 0.10},
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
    ],
    "saas": [
        {"metric": "trial_to_paid_conversion", "direction": "no_degradation", "max_drop_pct": 0.05},
        {"metric": "demo_request_quality", "direction": "no_degradation", "max_drop_pct": 0.10},
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
    ],
    "default": [
        {"metric": "page_load_time", "direction": "no_increase", "max_increase_pct": 0.10},
        {"metric": "bounce_rate", "direction": "no_increase", "max_increase_pct": 0.05},
    ],
}


def select_guardrails(business_category: str | None) -> list[dict]:
    return DEFAULT_GUARDRAILS.get((business_category or "default").lower(),
                                    DEFAULT_GUARDRAILS["default"])


# ────────────────────────────────────────────────────────────────
# Build experiment spec
# ────────────────────────────────────────────────────────────────

def build_experiment_spec(
    reco: dict,
    baseline_conversion_rate: float,
    daily_traffic: int = 1000,
    mde_relative: float = 0.10,
    business_category: str | None = None,
    primary_metric: str | None = None,
    secondary_metrics: list[str] | None = None,
) -> dict:
    """Build a full experiment spec from a reco object.

    Args:
      reco : reco dict (criterion_id, before, after, hypothesis, expected_lift_range...)
      baseline_conversion_rate : actual rate from Catchr/GA4 (Reality Layer V26.C)
      daily_traffic : sessions/day (also from Reality Layer)
      mde_relative : minimum effect to detect (default 10% relative)
      business_category : ecommerce|saas|lead_gen → picks guardrails
      primary_metric : default 'landing_page_signup_rate' or 'purchase_rate'
      secondary_metrics : list of metrics to track

    Returns dict ready to be saved as data/captures/<client>/<page>/
    experiments/<exp_id>.json
    """
    crit = reco.get("criterion_id", "unknown")
    exp_id = f"exp_{reco.get('client', 'unknown')}_{reco.get('page', 'unknown')}_{crit}_{time.strftime('%Y%m%d')}"

    sample = compute_sample_size(baseline_conversion_rate, mde_relative=mde_relative)
    duration = estimate_duration_days(sample.get("sample_size_total", 0), daily_traffic)
    guardrails = select_guardrails(business_category)

    # Default primary metric by business category
    if primary_metric is None:
        primary_metric = {
            "ecommerce": "purchase_rate",
            "saas": "trial_signup_rate",
            "lead_gen": "form_submit_rate",
        }.get((business_category or "").lower(), "landing_page_conversion_rate")

    if secondary_metrics is None:
        secondary_metrics = ["cta_click_rate", "scroll_depth_50_pct", "session_duration"]

    return {
        "experiment_id": exp_id,
        "version": "v27.1.0",
        "linked_reco": {
            "criterion_id": crit,
            "client": reco.get("client"),
            "page": reco.get("page"),
            "evidence_ids": reco.get("evidence_ids", []),
        },
        "hypothesis": reco.get("hypothesis") or reco.get("why") or (
            f"If we apply '{(reco.get('after') or '')[:120]}', "
            f"{primary_metric} will improve by ≥ {mde_relative * 100:.0f}%."
        ),
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
        "statistics": {
            **sample,
            "duration": duration,
        },
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
            {"trigger": "checkout_completion drops > 10%", "action": "review_within_24h"},
        ],
        "outcome": None,  # filled post-experiment
        "outcome_at": None,
        "winner": None,
        "lift_observed": None,
        "confidence_observed": None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def save_experiment_spec(spec: dict, client: str, page: str) -> pathlib.Path:
    out_dir = CAPTURES / client / page / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{spec['experiment_id']}.json"
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    tmp.replace(out_path)
    return out_path


# ────────────────────────────────────────────────────────────────
# Outcome importer — post-experiment
# ────────────────────────────────────────────────────────────────

def import_outcome(experiment_spec_path: pathlib.Path, outcome: str,
                   lift_observed: float, confidence_observed: float,
                   notes: Optional[str] = None) -> dict:
    """Update an experiment spec with the measured outcome (won/lost/inconclusive)."""
    if outcome not in ("won", "lost", "inconclusive"):
        return {"error": f"Invalid outcome: {outcome}"}
    if not experiment_spec_path.exists():
        return {"error": "spec_not_found"}

    spec = json.loads(experiment_spec_path.read_text())
    spec["outcome"] = outcome
    spec["winner"] = "treatment" if outcome == "won" else ("control" if outcome == "lost" else None)
    spec["lift_observed"] = round(lift_observed, 5)
    spec["confidence_observed"] = round(confidence_observed, 4)
    spec["outcome_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if notes:
        spec["outcome_notes"] = notes

    tmp = experiment_spec_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    tmp.replace(experiment_spec_path)

    return {"ok": True, "experiment_id": spec["experiment_id"],
            "outcome": outcome, "lift": lift_observed}


if __name__ == "__main__":
    # Demo
    reco = {
        "criterion_id": "hero_01",
        "client": "kaiju",
        "page": "home",
        "before": "H1 vague 'Bienvenue'",
        "after": "H1 spécifique 'Croquettes premium pour chiens, livrées chez vous'",
        "hypothesis": "If we clarify the hero promise, cold paid traffic will convert faster.",
        "evidence_ids": ["ev_kaiju_home_hero_01_001"],
    }
    spec = build_experiment_spec(
        reco=reco,
        baseline_conversion_rate=0.034,
        daily_traffic=500,
        mde_relative=0.15,
        business_category="ecommerce",
    )
    print(json.dumps(spec, indent=2, ensure_ascii=False)[:2000])
    print("...")
    print(f"\nSample size per variant : {spec['statistics']['sample_size_per_variant']:,}")
    print(f"Duration : {spec['statistics']['duration']['duration_days']} days")
