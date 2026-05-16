"""Opportunity orchestrator — internal plumbing (Issue #48).

Mono-concern (TYPING + helpers) sibling of ``orchestrator.py``: the small
frozen dataclasses + static mapping tables the orchestrator needs but
that would clutter its top-level reading order.

Underscore-prefixed module → not part of the public ``growthcro.opportunities``
API. Importers outside this package should reach for ``Opportunity`` /
``generate_opportunities`` instead.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from growthcro.models.opportunity_models import Category, Owner, Severity

# Threshold below which a criterion is considered an opportunity (cf. task #48
# spec: ``score < weight * 0.8``). Centralised so the rule can be amended in
# one place if doctrine V3.3 raises the bar.
GAP_RATIO_THRESHOLD = 0.8

# Doctrine pillars → Opportunity.category enum. Hero/persuasion are copy-led;
# UX/coherence are structure-led; psycho is trust; tech is tech.
PILLAR_TO_CATEGORY: dict[str, Category] = {
    "hero": "copy",
    "persuasion": "copy",
    "ux": "structure",
    "coherence": "structure",
    "psycho": "trust",
    "tech": "tech",
}

# Effort by category — heuristic per task #48 spec.
EFFORT_BY_CATEGORY: dict[Category, int] = {
    "copy": 2,
    "structure": 3,
    "design": 4,
    "dev": 4,
    "trust": 3,
    "offer": 3,
    "friction": 2,
    "tech": 4,
    "tracking": 3,
    "mobile": 4,
    "a11y": 3,
}

# Pillar → typical owner (kept narrow; the model enum allows growth/analytics
# but those rarely apply to playbook V3.2.1 pillars).
PILLAR_TO_OWNER: dict[str, Owner] = {
    "hero": "copy",
    "persuasion": "copy",
    "ux": "design",
    "coherence": "design",
    "psycho": "copy",
    "tech": "dev",
}

# Metric to track per category — task #48 dict (re-exported by orchestrator).
METRIC_BY_CATEGORY: dict[Category, str] = {
    "copy": "hero_cta_click_through_rate",
    "design": "scroll_depth_to_section_2",
    "structure": "conversion_rate",
    "trust": "form_completion_rate",
    "offer": "pricing_page_to_signup_rate",
    "friction": "bounce_rate",
    "tech": "page_load_time_p75",
    "tracking": "event_coverage_pct",
    "mobile": "mobile_conversion_rate",
    "a11y": "a11y_score",
}

HYPOTHESIS_TEMPLATE = (
    "If we improve {criterion_id} from {current}/100 to {target}/100, "
    "we expect {metric} to improve by ~{estimated_lift}% "
    "because {doctrine_rationale}."
)


@dataclass(frozen=True)
class CriterionGap:
    """One under-scoring criterion that may yield an Opportunity.

    Reference holder used between :func:`_identify_opportunity_candidates`
    and :func:`_compute_priority`. Mutually referenced by ``PriorityData``
    via consumers — keeps the mixed-concern linter signal C off.
    """
    criterion_id: str
    pillar: str
    current: float       # 0..100 (normalised from raw score / max * 100)
    target: float        # 0..100 (target = 100 = full weight)
    weight: float        # criterion weight from playbook
    description: str     # one-line doctrine rationale for the hypothesis


@dataclass(frozen=True)
class PriorityData:
    """Heuristic ICE inputs for one :class:`CriterionGap` post applicability boost."""
    impact: int
    effort: int
    confidence: int
    severity: Severity


@dataclass(frozen=True)
class ScoringSnapshot:
    """All artefacts the orchestrator needs for one (client, page_type)."""
    score_page_type: dict[str, Any]
    applicability_overlay: dict[str, Any]
    evidence_ledger: dict[str, Any]
    playbook_index: dict[str, dict[str, Any]]  # criterion_id → criterion dict
