"""Pydantic v2 models for the Opportunity Layer (Issue #47).

Mono-concern: this module declares data shapes only. No business logic, no
I/O, no env reads. The opportunity orchestrator (#48) and CLI (#49) consume
these models at their public boundaries.

V26.A invariant — Evidence Ledger
---------------------------------
Every ``Opportunity`` MUST carry a non-empty ``evidence_ids: list[str]`` so
that downstream consumers (dashboards, experiment engine, learning loop)
can trace any opportunity back to its grounding signals (captures,
perception clusters, scoring criteria, doctrine excerpts). This is
enforced by ``Field(..., min_length=1)`` — instantiating ``Opportunity``
with an empty ``evidence_ids`` raises ``ValidationError``.

Priority score — deterministic, computed
----------------------------------------
``priority_score`` is a ``@computed_field`` derived from
``(impact * confidence * severity_weight) / effort`` so the orchestrator
never has to "remember" to recompute it after editing a field. With
``frozen=True`` models, the computed field is recomputed on every access
because the underlying fields are immutable — the cost is negligible.

All models use ``ConfigDict(extra='forbid', frozen=True)`` — typing-strict
rollout doctrine (cf. ``docs/doctrine/CODE_DOCTRINE.md §TYPING``).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# Domain enums
# ─────────────────────────────────────────────────────────────────────────────

Severity = Literal["low", "medium", "high", "critical"]
Owner = Literal["copy", "design", "dev", "growth", "analytics", "mixed"]
Category = Literal[
    "copy", "design", "structure", "trust", "offer",
    "friction", "tech", "tracking", "mobile", "a11y",
]
DoctrineVersion = Literal["v3.2.1", "v3.3"]

_SEVERITY_WEIGHT: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 5,
}


# ─────────────────────────────────────────────────────────────────────────────
# Opportunity
# ─────────────────────────────────────────────────────────────────────────────

class Opportunity(BaseModel):
    """One actionable CRO opportunity on a single page.

    V26.A invariant: ``evidence_ids`` MUST be non-empty. Stripping that
    constraint breaks downstream traceability — do not relax it.

    ``priority_score`` is a deterministic computed field; consumers can sort
    by it without re-implementing the formula.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1, max_length=120)
    criterion_ref: str = Field(..., min_length=1, max_length=120)
    page_type: str = Field(..., min_length=1, max_length=64)
    client_slug: str = Field(..., min_length=1, max_length=64)

    current_score: float = Field(..., ge=0, le=100)
    target_score: float = Field(..., ge=0, le=100)

    impact: int = Field(..., ge=1, le=5)
    effort: int = Field(..., ge=1, le=5)
    confidence: int = Field(..., ge=1, le=5)
    severity: Severity

    category: Category
    problem: str = Field(..., min_length=1, max_length=280)
    evidence_ids: list[str] = Field(..., min_length=1)
    hypothesis: str = Field(..., min_length=10, max_length=280)
    recommended_action: str = Field(..., min_length=10, max_length=500)
    metric_to_track: str = Field(..., min_length=3, max_length=120)
    owner: Owner

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _target_above_current(self) -> "Opportunity":
        """Enforce that the target_score actually improves on current_score."""
        if self.target_score <= self.current_score:
            raise ValueError(
                f"target_score ({self.target_score}) must be > "
                f"current_score ({self.current_score})"
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def priority_score(self) -> float:
        """Deterministic ICE-style score: (impact * confidence * severity_weight) / effort.

        Range is roughly 0.2 (low,low,low,5) → 125.0 (5,5,critical,1).
        """
        weight = _SEVERITY_WEIGHT[self.severity]
        return round((self.impact * self.confidence * weight) / self.effort, 4)


# ─────────────────────────────────────────────────────────────────────────────
# Batch wrapper
# ─────────────────────────────────────────────────────────────────────────────

class OpportunityBatch(BaseModel):
    """All opportunities produced for one (client_slug, page_type) pair.

    The persistence module (``growthcro.opportunities.persist``) writes
    this as ``data/captures/<client_slug>/<page_type>/opportunities.json``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client_slug: str = Field(..., min_length=1, max_length=64)
    page_type: str = Field(..., min_length=1, max_length=64)
    doctrine_version: DoctrineVersion = "v3.2.1"
    opportunities: list[Opportunity] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _batch_keys_match(self) -> "OpportunityBatch":
        """Every opportunity in the batch must match the batch's (client, page)."""
        for opp in self.opportunities:
            if opp.client_slug != self.client_slug:
                raise ValueError(
                    f"opportunity {opp.id} client_slug={opp.client_slug!r} "
                    f"does not match batch {self.client_slug!r}"
                )
            if opp.page_type != self.page_type:
                raise ValueError(
                    f"opportunity {opp.id} page_type={opp.page_type!r} "
                    f"does not match batch {self.page_type!r}"
                )
        return self


__all__ = [
    "Category",
    "DoctrineVersion",
    "Opportunity",
    "OpportunityBatch",
    "Owner",
    "Severity",
]
