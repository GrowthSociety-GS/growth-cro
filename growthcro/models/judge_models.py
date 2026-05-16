"""Pydantic v2 models for the Visual Judge (Issue #57, epic gsg-creative-renaissance).

Mono-concern (TYPING axis): data shapes only. No business logic, no I/O,
no env reads, no LLM calls. The judge module
(``moteur_gsg.creative_engine.judge``) consumes a ``CreativeRouteBatch``
(CR-01 output) + brief + brand_dna context and produces a
``RouteSelectionDecision`` at its public boundary; an optional persistence
helper writes it to
``data/captures/<client>/<page>/route_selection_decision.json``.

Why a separate models file (and not extending ``creative_models.py``)?
---------------------------------------------------------------------
CR-01 owns ``creative_models.py``. CR-02 (this layer) adds the judge's
output schema. Keeping them separate respects mono-concern (one module =
one purpose) and prevents merge contention between parallel issues.
Downstream (CR-04 Visual Composer) consumes ``RouteSelectionDecision``
exclusively, never the raw ``CreativeRouteBatch`` — so the judge's
output shape is the contract that matters.

Scoring axes (per PRD §FR-2 + Codex addendum "Visual Judge / Route Selection")
-----------------------------------------------------------------------------
- ``brand_fit`` (weight 0.30) — alignment with Brand DNA voice/visual.
- ``cro_fit`` (weight 0.25) — funnel match audience + page_type.
- ``originality`` (weight 0.15) — uniqueness vs. déjà-vu SaaS templates.
- ``feasibility`` (weight 0.15) — renderer can actually produce it.
- ``visual_potential`` (weight 0.15) — visual ambition vs. safe defaults.

Weights sum to 1.0 (asserted in the judge module at load time). All scores
are integers 1-10 (Pydantic ``ge=1, le=10``). The composite
``weighted_score`` is a ``@computed_field`` — read-only, recomputed on
every access, no risk of being out of sync with the underlying axes.

All models use ``ConfigDict(extra='forbid', frozen=True)`` per typing-strict
rollout doctrine (cf. ``docs/doctrine/CODE_DOCTRINE.md §TYPING``).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# Scoring weights — kept here so they are importable from both the judge
# orchestrator and any downstream consumer (e.g. learning-loop telemetry).
# The judge module asserts ``sum(_DEFAULT_WEIGHTS.values()) == 1.0`` at load.
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_WEIGHTS: dict[str, float] = {
    "brand_fit": 0.30,
    "cro_fit": 0.25,
    "originality": 0.15,
    "feasibility": 0.15,
    "visual_potential": 0.15,
}


# ─────────────────────────────────────────────────────────────────────────────
# RouteScore — one route's 5-axis evaluation
# ─────────────────────────────────────────────────────────────────────────────


class RouteScore(BaseModel):
    """One route's 5-axis Visual Judge evaluation.

    ``route_id`` ties back to ``CreativeRoute.route_id`` (same regex
    constraints carried by the caller — we keep the field as a plain str
    here so this module never imports ``creative_models``, preserving the
    mono-concern boundary). ``rationale`` MUST be ≥50 chars: forces the LLM
    to produce a real justification, not "OK" or "fine".

    ``weighted_score`` is a ``@computed_field`` — read-only, derived from
    the 5 axes via the default weights. Range is 1.0–10.0 by construction
    (every axis is 1–10 and the weights sum to 1.0). Pydantic recomputes
    on every access; frozen models keep this safe.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_id: str = Field(..., pattern=r"^[a-z0-9_-]{3,40}$")
    brand_fit: int = Field(..., ge=1, le=10)
    cro_fit: int = Field(..., ge=1, le=10)
    originality: int = Field(..., ge=1, le=10)
    feasibility: int = Field(..., ge=1, le=10)
    visual_potential: int = Field(..., ge=1, le=10)
    rationale: str = Field(..., min_length=50, max_length=1000)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weighted_score(self) -> float:
        """Composite score using ``_DEFAULT_WEIGHTS``. Range 1.0–10.0."""
        return round(
            self.brand_fit * _DEFAULT_WEIGHTS["brand_fit"]
            + self.cro_fit * _DEFAULT_WEIGHTS["cro_fit"]
            + self.originality * _DEFAULT_WEIGHTS["originality"]
            + self.feasibility * _DEFAULT_WEIGHTS["feasibility"]
            + self.visual_potential * _DEFAULT_WEIGHTS["visual_potential"],
            4,
        )


# ─────────────────────────────────────────────────────────────────────────────
# RouteSelectionDecision — full judge output (selected + alternatives)
# ─────────────────────────────────────────────────────────────────────────────


class RouteSelectionDecision(BaseModel):
    """Full Visual Judge output for one (client_slug, page_type).

    Invariants enforced by ``_check_invariants``:
    - ``selected_route_id == selected_route_score.route_id``
    - Every ``alternatives_evaluated[i].route_id != selected_route_id``
    - All route_ids are unique across (selected + alternatives)

    ``judge_meta`` is free-form telemetry — model name, system_prompt_chars
    (proves the anti-mega-prompt invariant held), tokens in/out, cost_usd,
    wall_seconds, retry_count. Schema-free intentionally so we can iterate
    on what we capture without bumping the typed boundary.

    ``alternatives_evaluated`` carries 2–4 items (CreativeRouteBatch carries
    3–5 routes; the selected one is pulled out, so 2–4 alternatives remain).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client_slug: str = Field(..., pattern=r"^[a-z0-9_-]{2,40}$")
    page_type: str = Field(..., min_length=1, max_length=64)
    selected_route_id: str = Field(..., pattern=r"^[a-z0-9_-]{3,40}$")
    selected_route_score: RouteScore
    alternatives_evaluated: list[RouteScore] = Field(..., min_length=2, max_length=4)
    selection_rationale: str = Field(..., min_length=100, max_length=2000)
    decision_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    judge_meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_invariants(self) -> "RouteSelectionDecision":
        """Cross-field invariants: selected id matches, alternatives differ, all unique."""
        if self.selected_route_id != self.selected_route_score.route_id:
            raise ValueError(
                f"selected_route_id={self.selected_route_id!r} does not match "
                f"selected_route_score.route_id={self.selected_route_score.route_id!r}"
            )
        seen: set[str] = {self.selected_route_id}
        for alt in self.alternatives_evaluated:
            if alt.route_id == self.selected_route_id:
                raise ValueError(
                    f"alternative route_id={alt.route_id!r} duplicates "
                    f"selected_route_id={self.selected_route_id!r}"
                )
            if alt.route_id in seen:
                raise ValueError(
                    f"duplicate route_id={alt.route_id!r} in alternatives_evaluated"
                )
            seen.add(alt.route_id)
        return self


__all__ = [
    "RouteScore",
    "RouteSelectionDecision",
    "_DEFAULT_WEIGHTS",
]
