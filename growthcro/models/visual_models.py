"""Pydantic v2 models for the visual_intelligence frontier (Issue #30).

Mono-concern: this module declares data shapes only. No business logic, no I/O,
no env reads.

Two layers exposed:

1. **Strategy contracts** — Pydantic v2 replacements for the historical
   ``VisualIntelligencePack`` and ``CreativeRouteContract`` dataclasses defined
   in ``moteur_gsg/core/visual_intelligence.py``. These are the *public* output
   of ``build_visual_intelligence_pack`` / ``build_creative_route_contract``
   and feed AURA, Creative Director, Golden Bridge and the renderer.
2. **Perception clusters** — ``VisualBlock`` / ``VisualHierarchy`` / ``VisualScore``
   model the shape of ``data/captures/<slug>/<page_type>/perception_v13.json``
   (DBSCAN clusters + role classification). These satisfy the round-trip JSON
   validation requirement of Issue #30 and are referenced from ``VisualReport``
   when perception data is bundled with the strategy contract.

All models use ``ConfigDict(extra='forbid', frozen=True)`` by default to lock
the public boundary. Mutable fields (``image_direction``, ``composition_directives``,
etc.) are still allowed inside frozen models — frozen forbids reassignment of the
field, not mutation of a list contained within (we rely on consumers not to mutate
shared lists; doctrine §AD-1).

Exception: ``VisualReport.metadata`` uses ``dict[str, Any]`` as an explicit
escape hatch for debug-only payloads not yet promoted to typed fields. See
``docs/doctrine/CODE_DOCTRINE.md`` §AD-1 — to be typed in a follow-up sprint.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ─────────────────────────────────────────────────────────────────────────────
# Perception clusters (round-trip target: perception_v13.json)
# ─────────────────────────────────────────────────────────────────────────────

VisualBlockRole = Literal[
    "hero", "cta", "social_proof", "feature", "footer", "nav", "other"
]


class VisualBlock(BaseModel):
    """Bloc visuel détecté (cluster spatial perception V13)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    block_id: str
    role: VisualBlockRole
    bbox: tuple[int, int, int, int]
    text_content: str | None = None
    confidence: float


class VisualHierarchy(BaseModel):
    """Ordered collection of visual blocks with reading order + primary anchor."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    blocks: list[VisualBlock] = Field(default_factory=list)
    primary_block_id: str
    reading_order: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Scoring pillar
# ─────────────────────────────────────────────────────────────────────────────

VisualScorePillar = Literal[
    "hero", "persuasion", "ux", "coherence", "psycho", "tech"
]


class VisualScore(BaseModel):
    """One pillar score on the 6-pillar scoring axis."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pillar: VisualScorePillar
    score: float  # 0-1 normalized
    raw_points: int  # absolute points (per doctrine V3.2.1 grid)
    notes: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Strategy contracts (Pydantic replacements for legacy dataclasses)
# ─────────────────────────────────────────────────────────────────────────────


class VisualReport(BaseModel):
    """Output public de visual_intelligence — frontière inter-module.

    Replaces the legacy ``VisualIntelligencePack`` dataclass. Carries the
    full strategy-aware visual contract that feeds AURA, Creative Director,
    Golden Bridge and the renderer. ``hierarchy`` and ``scores`` are optional
    embeds for when perception data is bundled at the boundary.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Identity
    version: str
    slug: str = ""  # client slug; empty when unset upstream
    page_type: str
    business_category: str

    # Strategy axes (mirrors VisualIntelligencePack 1:1)
    visual_role: str
    density: str
    warmth: str
    energy: str
    editoriality: str
    product_visibility: str
    proof_visibility: str
    motion_profile: str

    # Composed directives
    image_direction: list[str] = Field(default_factory=list)
    composition_directives: list[str] = Field(default_factory=list)

    # Downstream contracts
    aura_input_contract: dict[str, Any] = Field(default_factory=dict)
    creative_director_seed: dict[str, Any] = Field(default_factory=dict)
    golden_bridge_query: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)

    # Optional perception bundle (when round-tripping perception_v13.json)
    hierarchy: VisualHierarchy | None = None
    scores: list[VisualScore] = Field(default_factory=list)

    # Escape hatch — debug-only, to be typed in a follow-up sprint (§AD-1).
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Backward-compat shim — preserves the dataclass `.to_dict()` API
        used by ``moteur_gsg/modes/mode_1_complete.py`` and downstream consumers.
        """
        return self.model_dump(mode="python")


class CreativeRouteReport(BaseModel):
    """Pydantic replacement for the legacy ``CreativeRouteContract`` dataclass.

    Render-facing contract emitted by Creative Director / Golden selector.
    Kept separate from ``VisualReport`` because its consumers (the renderer)
    care only about route execution, not strategy upstream.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    route_name: str
    risk_level: str
    aesthetic_thesis: str
    typography_thesis: str
    color_thesis: str
    motion_thesis: str
    section_rhythm: str
    component_emphasis: list[str] = Field(default_factory=list)
    must_not_do: list[str] = Field(default_factory=list)
    golden_references: list[dict[str, Any]] = Field(default_factory=list)
    technique_references: list[dict[str, Any]] = Field(default_factory=list)
    route_decisions: dict[str, Any] = Field(default_factory=dict)
    renderer_overrides: dict[str, Any] = Field(default_factory=dict)
    source: str = "deterministic_visual_intelligence"

    def to_dict(self) -> dict[str, Any]:
        """Backward-compat shim — preserves the dataclass `.to_dict()` API."""
        return self.model_dump(mode="python")


__all__ = [
    "VisualBlock",
    "VisualBlockRole",
    "VisualHierarchy",
    "VisualScore",
    "VisualScorePillar",
    "VisualReport",
    "CreativeRouteReport",
]
