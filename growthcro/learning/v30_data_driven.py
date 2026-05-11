"""Learning V30 — data-driven Bayesian update on doctrine V3.3.

Issue #23. Consume Reality Layer snapshots + Experiment Engine outcomes,
emit doctrine_proposals via a Beta-Binomial Bayesian update.

Why Bayesian vs. V29 frequentist:
- V29 audit-based counts CRITICAL/TOP rates across 185 curated audits and
  generates proposals via fixed thresholds (`pct_critical ≥ 70%`).
- V30 consumes *outcomes* (won/lost/inconclusive) from real A/B tests.
  Each criterion starts with a flat Beta(1,1) prior + evidence accumulates:
  α += wins, β += losses. The posterior mean gives a "win probability"
  estimate. A proposal is emitted when:
    (a) posterior_mean ≥ 0.65 AND total_trials ≥ 3 → `strengthen_recommendation`
    (b) posterior_mean ≤ 0.35 AND total_trials ≥ 3 → `weaken_recommendation`
    (c) total_trials ≥ 5 AND credible_interval_width ≥ 0.4 → `gather_more_evidence`

Reality data complements this:
- If `reality_snapshot.computed.conversion_rate` is consistently below a sane
  baseline AND criterion is RESPECTED (high score) → propose `revisit_criterion`
  (doctrine criterion not yielding observable impact).

Output schema matches V29 proposals so review pipeline is reused. Source field
is `learning v30 data-driven (n experiments × n reality snapshots)` to
distinguish from V29 `audit-based learning v29 (56 curated clients V26)`.

Output path:
    data/learning/data_driven_proposals/<iso_date>/<proposal_id>.json
    data/learning/data_driven_stats.json
    data/learning/data_driven_summary.md

CLI:
    python3 -m growthcro.learning.v30_data_driven
    python3 -m growthcro.learning.v30_data_driven --min-trials 3
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = ROOT / "data" / "experiments"
REALITY_DIR = ROOT / "data" / "reality"
LEARNING_DIR = ROOT / "data" / "learning"
PROPOSALS_DIR = LEARNING_DIR / "data_driven_proposals"
PLAYBOOK_DIR = ROOT / "playbook"

# Thresholds — tunable, kept stdlib for backward compat with V29 review pipeline.
DEFAULT_THRESHOLDS = {
    "min_trials": 3,
    "strengthen_threshold": 0.65,  # posterior mean above → strengthen reco
    "weaken_threshold": 0.35,  # below → weaken reco
    "wide_ci_threshold": 0.40,  # credible interval width above → gather more
    "reality_low_cr_threshold": 0.005,  # below 0.5% CR sustained → flag
}


@dataclass
class BayesianBetaPosterior:
    """Beta(α, β) posterior tracker for a single criterion.

    Prior: Beta(1, 1) = uniform. Each experiment outcome updates:
      - won (treatment beats control)  → alpha += 1
      - lost (control beats treatment) → beta += 1
      - inconclusive (no significant)  → both += 0.5 (weak signal)
    """

    criterion_id: str
    alpha: float = 1.0
    beta: float = 1.0
    n_won: int = 0
    n_lost: int = 0
    n_inconclusive: int = 0

    def update(self, outcome: str) -> None:
        if outcome == "won":
            self.alpha += 1
            self.n_won += 1
        elif outcome == "lost":
            self.beta += 1
            self.n_lost += 1
        elif outcome == "inconclusive":
            self.alpha += 0.5
            self.beta += 0.5
            self.n_inconclusive += 1

    @property
    def total_trials(self) -> int:
        return self.n_won + self.n_lost + self.n_inconclusive

    @property
    def posterior_mean(self) -> float:
        """E[θ | data] for Beta(α, β) = α / (α + β)."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def credible_interval_95(self) -> tuple[float, float]:
        """Approximate 95% credible interval via the normal approximation.

        For a Beta(α, β), Var = αβ / ((α+β)²(α+β+1)). The mean is α/(α+β).
        For our use-case (decision support, not inference), normal approx is
        sufficient — keeps stdlib-only. Falls back to (0, 1) if degenerate.
        """
        import math

        a, b = self.alpha, self.beta
        mean = a / (a + b)
        var = (a * b) / ((a + b) ** 2 * (a + b + 1))
        if var <= 0:
            return (mean, mean)
        sd = math.sqrt(var)
        low = max(0.0, mean - 1.96 * sd)
        high = min(1.0, mean + 1.96 * sd)
        return (round(low, 4), round(high, 4))

    def to_dict(self) -> dict[str, Any]:
        ci = self.credible_interval_95
        return {
            "criterion_id": self.criterion_id,
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 4),
            "n_won": self.n_won,
            "n_lost": self.n_lost,
            "n_inconclusive": self.n_inconclusive,
            "total_trials": self.total_trials,
            "posterior_mean": round(self.posterior_mean, 4),
            "credible_interval_95": ci,
            "credible_interval_width": round(ci[1] - ci[0], 4),
        }


def _safe_load(path: pathlib.Path) -> Optional[dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _collect_experiment_outcomes() -> list[dict[str, Any]]:
    """Walk data/experiments/ and pull every spec with a recorded outcome."""
    out: list[dict[str, Any]] = []
    if not EXPERIMENTS_DIR.exists():
        return out
    for client_dir in EXPERIMENTS_DIR.iterdir():
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue
        for spec_path in client_dir.glob("exp_*.json"):
            spec = _safe_load(spec_path)
            if spec and spec.get("outcome") in ("won", "lost", "inconclusive"):
                out.append({
                    "experiment_id": spec.get("experiment_id"),
                    "client": client_dir.name,
                    "page": (spec.get("linked_reco") or {}).get("page"),
                    "criterion_id": (spec.get("linked_reco") or {}).get("criterion_id"),
                    "ab_type": spec.get("ab_type"),
                    "outcome": spec["outcome"],
                    "lift_observed": spec.get("lift_observed"),
                    "confidence_observed": spec.get("confidence_observed"),
                    "outcome_at": spec.get("outcome_at"),
                    "path": str(spec_path.relative_to(ROOT)),
                })
    return out


def _collect_reality_snapshots() -> list[dict[str, Any]]:
    """Walk data/reality/ and load every reality_snapshot.json."""
    out: list[dict[str, Any]] = []
    if not REALITY_DIR.exists():
        return out
    for client_dir in REALITY_DIR.iterdir():
        if not client_dir.is_dir():
            continue
        for page_dir in client_dir.iterdir():
            if not page_dir.is_dir():
                continue
            for date_dir in page_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                snap_path = date_dir / "reality_snapshot.json"
                snap = _safe_load(snap_path)
                if snap:
                    snap["_path"] = str(snap_path.relative_to(ROOT))
                    out.append(snap)
    return out


def _load_v3_3_criteria() -> dict[str, dict[str, Any]]:
    """Load every criterion from `playbook/bloc_*_v3-3.json` indexed by id."""
    out: dict[str, dict[str, Any]] = {}
    if not PLAYBOOK_DIR.exists():
        return out
    for path in PLAYBOOK_DIR.glob("bloc_*_v3-3.json"):
        d = _safe_load(path)
        if not d:
            continue
        for crit in d.get("criteria", []):
            cid = crit.get("id")
            if cid:
                out[cid] = {
                    "id": cid,
                    "label": crit.get("label"),
                    "pillar": crit.get("pillar"),
                    "weight": crit.get("weight"),
                    "page_types": crit.get("pageTypes") or [],
                    "business_categories": crit.get("businessCategories") or [],
                    "playbook_file": path.name,
                }
    return out


def compute_data_driven_proposals(
    experiment_outcomes: list[dict[str, Any]],
    reality_snapshots: list[dict[str, Any]],
    v3_3_criteria: dict[str, dict[str, Any]],
    thresholds: Optional[dict[str, float]] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Pure function: compute V30 proposals from inputs. Returns (proposals, stats)."""
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    today = time.strftime("%Y_%m_%d")
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")

    # Bayesian update per criterion
    posteriors: dict[str, BayesianBetaPosterior] = {}
    for exp in experiment_outcomes:
        cid = exp.get("criterion_id")
        if not cid:
            continue
        post = posteriors.setdefault(cid, BayesianBetaPosterior(criterion_id=cid))
        post.update(exp["outcome"])

    # Reality lookup: average conversion rate per criterion (via criterion → page link)
    # Cheap heuristic: any reality_snapshot whose page_slug starts with a known page_type
    # contributes to the "observed CR" for criteria tagged for that page_type.
    cr_by_page_slug: dict[str, list[float]] = defaultdict(list)
    for snap in reality_snapshots:
        cr = (snap.get("computed") or {}).get("conversion_rate")
        if cr is not None:
            cr_by_page_slug[snap.get("page_slug") or ""].append(float(cr))

    avg_cr_per_page_slug = {
        slug: sum(rates) / len(rates)
        for slug, rates in cr_by_page_slug.items()
        if rates
    }

    proposals: list[dict[str, Any]] = []

    # Pattern 1+2+3: Bayesian proposals from experiment outcomes
    for cid, post in posteriors.items():
        if post.total_trials < th["min_trials"]:
            continue
        crit_meta = v3_3_criteria.get(cid, {"id": cid, "label": cid})
        ci = post.credible_interval_95
        ci_width = ci[1] - ci[0]

        base_evidence = {
            **post.to_dict(),
            "doctrine_label": crit_meta.get("label"),
            "doctrine_pillar": crit_meta.get("pillar"),
            "source": "learning v30 data-driven (experiment outcomes + reality snapshots)",
        }

        if post.posterior_mean >= th["strengthen_threshold"]:
            proposals.append({
                "proposal_id": f"dup_v30_{today}_{cid}_strengthen",
                "type": "strengthen_recommendation",
                "subtype": "bayesian_posterior_high",
                "affected_criteria": [cid],
                "scope": {"all_business_categories": True},
                "evidence": base_evidence,
                "proposed_change": (
                    f"Criterion {cid} ({crit_meta.get('label')}) won {post.n_won}/{post.total_trials} "
                    f"A/B tests (posterior mean={post.posterior_mean:.2f}, "
                    f"95% CI=[{ci[0]:.2f}, {ci[1]:.2f}]). Strengthen the recommendation "
                    f"weight or promote from OK threshold to TOP threshold."
                ),
                "risk": (
                    "Strengthening too early on a narrow sample may overfit to lucky outcomes. "
                    "Require 5+ trials and CI width < 0.30 before promoting weight."
                ),
                "requires_human_approval": True,
                "generated_at": now_iso,
            })
        elif post.posterior_mean <= th["weaken_threshold"]:
            proposals.append({
                "proposal_id": f"dup_v30_{today}_{cid}_weaken",
                "type": "weaken_recommendation",
                "subtype": "bayesian_posterior_low",
                "affected_criteria": [cid],
                "scope": {"all_business_categories": True},
                "evidence": base_evidence,
                "proposed_change": (
                    f"Criterion {cid} ({crit_meta.get('label')}) lost {post.n_lost}/{post.total_trials} "
                    f"A/B tests (posterior mean={post.posterior_mean:.2f}, "
                    f"95% CI=[{ci[0]:.2f}, {ci[1]:.2f}]). Weaken doctrine weight or move "
                    f"to research_first=True (let consultant decide per client)."
                ),
                "risk": (
                    "Weakening a criterion that fails in some contexts but wins in others "
                    "may bias the doctrine. Cross-check business_category breakdown."
                ),
                "requires_human_approval": True,
                "generated_at": now_iso,
            })
        elif ci_width >= th["wide_ci_threshold"]:
            proposals.append({
                "proposal_id": f"dup_v30_{today}_{cid}_gather_more",
                "type": "gather_more_evidence",
                "subtype": "bayesian_ci_wide",
                "affected_criteria": [cid],
                "scope": {"all_business_categories": True},
                "evidence": base_evidence,
                "proposed_change": (
                    f"Criterion {cid} ({crit_meta.get('label')}): {post.total_trials} A/B tests "
                    f"with posterior CI={ci_width:.2f} (still wide). Schedule 3+ additional "
                    f"experiments before doctrine update."
                ),
                "risk": "No risk — pure evidence-gathering signal.",
                "requires_human_approval": False,
                "generated_at": now_iso,
            })

    # Pattern 4: reality-driven — criteria where doctrine respected but reality bad
    # (heuristic; refined when we have more data).
    if avg_cr_per_page_slug:
        very_low_slugs = [
            slug
            for slug, cr in avg_cr_per_page_slug.items()
            if cr < th["reality_low_cr_threshold"]
        ]
        if very_low_slugs:
            proposals.append({
                "proposal_id": f"dup_v30_{today}_reality_low_cr_pages",
                "type": "revisit_criterion",
                "subtype": "reality_signal_underwhelming",
                "affected_criteria": [],  # broad
                "scope": {"page_slugs": sorted(very_low_slugs)},
                "evidence": {
                    "n_page_slugs_flagged": len(very_low_slugs),
                    "threshold_cr": th["reality_low_cr_threshold"],
                    "n_reality_snapshots_total": len(reality_snapshots),
                    "source": "learning v30 data-driven (reality snapshots aggregated)",
                },
                "proposed_change": (
                    f"{len(very_low_slugs)} page(s) show sustained CR below "
                    f"{th['reality_low_cr_threshold'] * 100:.1f}% across reality snapshots. "
                    f"Audit these pages with V3.3 doctrine and check if currently-respected "
                    f"criteria need stricter thresholds."
                ),
                "risk": "Cohort may be too small early in the program — confirm by re-audit.",
                "requires_human_approval": True,
                "generated_at": now_iso,
            })

    # Synthesise stats
    stats = {
        "version": "v30.0.0-issue-23",
        "generated_at": now_iso,
        "n_experiment_outcomes": len(experiment_outcomes),
        "n_reality_snapshots": len(reality_snapshots),
        "n_criteria_with_evidence": len(posteriors),
        "n_proposals": len(proposals),
        "thresholds": th,
        "posteriors": {cid: p.to_dict() for cid, p in posteriors.items()},
        "avg_cr_per_page_slug": {
            slug: round(cr, 5) for slug, cr in avg_cr_per_page_slug.items()
        },
        "proposals_by_type": {
            t: sum(1 for p in proposals if p["type"] == t)
            for t in {p["type"] for p in proposals}
        },
    }
    return proposals, stats


def _render_summary(
    proposals: list[dict[str, Any]],
    stats: dict[str, Any],
) -> str:
    lines = [
        f"# Learning V30 Data-Driven — Summary ({time.strftime('%Y-%m-%d %H:%M')})",
        "",
        f"**Experiment outcomes consumed**: {stats['n_experiment_outcomes']}",
        f"**Reality snapshots consumed**: {stats['n_reality_snapshots']}",
        f"**Criteria with evidence**: {stats['n_criteria_with_evidence']}",
        f"**Proposals generated**: {stats['n_proposals']} (requires Mathis approval)",
        "",
        "## Proposals by type",
        "",
    ]
    for ptype, count in sorted((stats.get("proposals_by_type") or {}).items()):
        lines.append(f"- {ptype}: {count}")
    lines.append("")
    if not proposals:
        lines.append(
            "_No proposals yet — feed the engine with experiment outcomes "
            "(`growthcro.experiment.import_outcome`) and reality snapshots "
            "(`growthcro.reality.collect_reality_snapshot`)._"
        )
        return "\n".join(lines)

    lines.append("## Top proposals")
    lines.append("")
    for p in proposals[:15]:
        ev = p["evidence"]
        crit = ", ".join(p["affected_criteria"]) or "(broad)"
        lines.append(f"- **{crit}** [{p['type']}] — {p['proposed_change'][:200]}")
    return "\n".join(lines)


def run_v30_cycle(
    thresholds: Optional[dict[str, float]] = None,
    write: bool = True,
) -> dict[str, Any]:
    """Full cycle: scan filesystem, compute, persist, return summary."""
    experiment_outcomes = _collect_experiment_outcomes()
    reality_snapshots = _collect_reality_snapshots()
    v3_3_criteria = _load_v3_3_criteria()

    proposals, stats = compute_data_driven_proposals(
        experiment_outcomes,
        reality_snapshots,
        v3_3_criteria,
        thresholds=thresholds,
    )

    if write:
        LEARNING_DIR.mkdir(parents=True, exist_ok=True)
        today_iso = time.strftime("%Y-%m-%d")
        out_dir = PROPOSALS_DIR / today_iso
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in proposals:
            (out_dir / f"{p['proposal_id']}.json").write_text(
                json.dumps(p, ensure_ascii=False, indent=2)
            )
        (LEARNING_DIR / "data_driven_stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2)
        )
        summary_md = _render_summary(proposals, stats)
        (LEARNING_DIR / "data_driven_summary.md").write_text(summary_md)

    return {
        "n_experiment_outcomes": stats["n_experiment_outcomes"],
        "n_reality_snapshots": stats["n_reality_snapshots"],
        "n_criteria_with_evidence": stats["n_criteria_with_evidence"],
        "n_proposals": stats["n_proposals"],
        "proposals_by_type": stats["proposals_by_type"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--min-trials",
        type=int,
        default=DEFAULT_THRESHOLDS["min_trials"],
        help="Min A/B trials per criterion to consider for a proposal",
    )
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    thresholds = {**DEFAULT_THRESHOLDS, "min_trials": args.min_trials}
    result = run_v30_cycle(thresholds=thresholds, write=not args.no_write)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
