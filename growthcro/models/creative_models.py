"""Pydantic v2 models for the Creative Exploration Engine (Issue #56, epic gsg-creative-renaissance).

Mono-concern (TYPING axis): data shapes only. No business logic, no I/O, no
env reads, no LLM calls. The orchestrator
(``moteur_gsg.creative_engine.orchestrator``) consumes a brief / brand_dna
context and produces a ``CreativeRouteBatch`` at its public boundary; the
persist module writes it via ``CreativeRouteBatch.model_dump`` to
``data/captures/<client>/<page>/creative_routes.json``.

Why a dedicated model layer?
----------------------------
The Renaissance epic introduces a *Creative Exploration Engine* upstream of
the page-type planner / renderer. It calls Claude Opus 4.7 to imagine 3–5
bold creative directions for a given LP context, then downstream layers
(CR-02 Visual Judge, CR-03 Contracts, CR-04 Visual Composer) consume the
typed batch. By pinning the schema first we let CR-02 + CR-03 parallelise
without blocking on the full orchestrator landing.

Source for the 11 thesis fields:
``.claude/docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md``
§"Proposed New Layer: Creative Exploration Engine" → "Outputs".

All models use ``ConfigDict(extra='forbid', frozen=True)`` per typing-strict
rollout doctrine (cf. ``docs/doctrine/CODE_DOCTRINE.md §TYPING``).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# Domain enums — kept Literal so callers get IDE autocomplete + Pydantic
# generates a typed JSON schema. Adding a new vertical here is one commit.
# ─────────────────────────────────────────────────────────────────────────────

BusinessCategory = Literal[
    "saas",
    "ecommerce",
    "luxury",
    "marketplace",
    "app_acquisition",
    "media_editorial",
    "local_service",
    "health_wellness",
    "finance",
    "creator_course",
    "enterprise",
    "consumer_brand",
]


# Anti-mega-prompt invariant — also referenced by orchestrator at module load.
SYSTEM_PROMPT_HARD_LIMIT_CHARS: int = 8000

# Minimum length per thesis field — forces the LLM (and any hand-crafted
# fixture) to write real theses, not one-liners. 20 chars is the smallest
# threshold under which we considered any output to be a placeholder.
_THESIS_MIN_LEN: int = 20


# ─────────────────────────────────────────────────────────────────────────────
# RouteThesis — the 11 art-direction axes for one creative route
# ─────────────────────────────────────────────────────────────────────────────


class RouteThesis(BaseModel):
    """The 11 art-direction theses that define one creative route.

    Each field is a free-form prose thesis (min 20 chars) so the LLM cannot
    cheat with `"TBD"` or empty strings. Mirrors the addendum's §Outputs
    list 1:1. Frozen so downstream layers (Visual Judge, Composer) can hash
    or memoise on the route without defensive copies.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    aesthetic_thesis: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    spatial_layout_thesis: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    hero_mechanism: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    section_rhythm: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    visual_metaphor: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    motion_language: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    texture_language: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    image_asset_strategy: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    typography_strategy: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    color_strategy: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)
    proof_visualization_strategy: str = Field(..., min_length=_THESIS_MIN_LEN, max_length=600)


# ─────────────────────────────────────────────────────────────────────────────
# CreativeRoute — one full direction (id + name + thesis + modules + risks)
# ─────────────────────────────────────────────────────────────────────────────


class CreativeRoute(BaseModel):
    """One creative direction the engine proposes.

    ``route_id`` is a slug (regex ``^[a-z0-9_-]{3,40}$``) — the Visual Judge
    selects by this id. ``risks`` MUST be non-empty: forcing the LLM to name
    at least one risk filters out the "everything is amazing" failure mode
    we kept seeing on raw Opus runs. ``why_this_route_fits`` MUST be ≥50
    chars: a real rationale that ties the route back to brief / brand_dna /
    audience.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_id: str = Field(..., pattern=r"^[a-z0-9_-]{3,40}$")
    route_name: str = Field(..., min_length=10, max_length=80)
    thesis: RouteThesis
    page_type_modules: list[str] = Field(..., min_length=2, max_length=12)
    risks: list[str] = Field(..., min_length=1, max_length=10)
    why_this_route_fits: str = Field(..., min_length=50, max_length=800)


# ─────────────────────────────────────────────────────────────────────────────
# CreativeRouteBatch — what the engine writes to disk for one (client, page)
# ─────────────────────────────────────────────────────────────────────────────


class CreativeRouteBatch(BaseModel):
    """All creative routes produced by Opus for one (client_slug, page_type).

    Persisted by ``moteur_gsg.creative_engine.persist`` to
    ``data/captures/<client_slug>/<page_type>/creative_routes.json``.

    ``prompt_meta`` is free-form telemetry — model name, system_prompt_chars
    (proves the anti-mega-prompt invariant held), tokens in/out, cost_usd,
    wall_seconds, retry_count. Schema-free intentionally so we can iterate
    on what we capture without bumping the typed boundary.

    Invariants:
    - ``routes`` carries 3–5 items (LLM must produce that range; below 3 →
      not enough exploration, above 5 → noise / decision paralysis).
    - All ``route_id``s in ``routes`` are unique (Visual Judge selects by id).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client_slug: str = Field(..., pattern=r"^[a-z0-9_-]{2,40}$")
    page_type: str = Field(..., min_length=1, max_length=64)
    business_category: BusinessCategory
    routes: list[CreativeRoute] = Field(..., min_length=3, max_length=5)
    prompt_meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _unique_route_ids(self) -> "CreativeRouteBatch":
        """Route ids MUST be unique within a batch — the Judge selects by id."""
        seen: set[str] = set()
        for r in self.routes:
            if r.route_id in seen:
                raise ValueError(
                    f"duplicate route_id={r.route_id!r} in batch "
                    f"({self.client_slug}/{self.page_type})"
                )
            seen.add(r.route_id)
        return self


__all__ = [
    "BusinessCategory",
    "CreativeRoute",
    "CreativeRouteBatch",
    "RouteThesis",
    "SYSTEM_PROMPT_HARD_LIMIT_CHARS",
]
