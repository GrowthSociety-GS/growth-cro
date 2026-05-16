"""Pydantic v2 contracts for the Visual Composer layer (Issue #58, epic gsg-creative-renaissance).

Mono-concern (TYPING axis): data shapes only. No business logic, no I/O,
no env reads, no LLM calls. These are the *frontier* contracts between:

1. CR-04 ``moteur_gsg.creative_engine.visual_composer`` (producer) — turns
   the Visual Judge's ``RouteSelectionDecision`` into a
   ``VisualComposerContract`` describing every section / module / motion /
   asset the renderer must emit.
2. CR-06 renderer (consumer) — instantiates HTML from this contract.
3. CR-07 QA (consumer) — reads it to know what to screenshot-diff.

Why a separate models file (not extending ``creative_models.py``)?
-----------------------------------------------------------------
CR-01 owns ``creative_models.py`` (creative engine outputs). CR-03 (this
layer) owns the *contract* schemas that downstream renderer / composer /
QA layers consume. Different concern, different consumers, different
ownership → separate file per mono-concern (anti-pattern #8 in
``.claude/CLAUDE.md``).

We *import* ``CreativeRoute`` / ``RouteThesis`` / ``BusinessCategory``
from CR-01 — never redefine them. ``CreativeRouteContract`` is a
deterministic façade over ``CreativeRoute`` (post-Judge selection) and
adds ``decision_metadata`` (selected_at, model_used, scores) so any
downstream consumer can audit the routing decision without re-loading
the original ``CreativeRouteBatch``.

Image-gen scope note
--------------------
Per Mathis 2026-05-16 decision (commit ec02491, CR-04 rescope L 18h),
v1 SKIPS image generation. ``AssetSpec`` carries the *resolution* tree
only (``brand_dna`` / ``vocabulary_svg`` / ``stock_fallback`` /
``css_placeholder``) — there is NO ``prompt_for_image_gen`` field. If an
asset cannot be resolved, ``unresolved=True`` so the renderer can fail
loud (or substitute a CSS placeholder per fail-safe v1 policy).

All models use ``ConfigDict(extra='forbid', frozen=True)`` per typing-strict
rollout doctrine (cf. ``docs/doctrine/CODE_DOCTRINE.md §TYPING``).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from growthcro.models.creative_models import (
    BusinessCategory,
    CreativeRoute,
    RouteThesis,
)

# ─────────────────────────────────────────────────────────────────────────────
# Domain enums — kept Literal so typos are caught at boundary.
# Lists are intentionally expandable: adding a new section_type / module_type
# is a one-commit change here + a downstream renderer/composer update.
# ─────────────────────────────────────────────────────────────────────────────

SectionType = Literal[
    "hero",
    "proof_strip",
    "intro",
    "listicle_item",
    "testimonials",
    "comparison",
    "faq",
    "final_cta",
    "footer",
    "navigation",
    "byline",
    "value_props",
    "social_proof",
    "feature_highlight",
    "pricing",
    "trust_signals",
]

ModuleType = Literal[
    "gradient_bg",
    "grain_overlay",
    "dashboard_panel",
    "stats_grid",
    "logo_strip",
    "testimonial_card",
    "proof_strip",
    "comparison_table",
    "faq_accordion",
    "video_embed",
    "lottie_animation",
    "svg_pattern",
    "image_block",
    "code_snippet",
    "chart",
]

MotionTrigger = Literal["scroll", "hover", "load", "click", "focus"]
MotionAnimation = Literal["fade", "slide", "scale", "rotate", "blur", "morph", "parallax"]
MotionEasing = Literal[
    "linear", "ease", "ease-in", "ease-out", "ease-in-out", "cubic-bezier",
]

AssetType = Literal[
    "hero_image",
    "texture",
    "illustration",
    "logo",
    "background",
    "icon",
    "screenshot",
    "video_thumbnail",
    "svg_pattern",
]

AssetPlacement = Literal["foreground", "background", "inline", "decorative"]

# Decision tree applied by CR-04 ``asset_resolver`` per Mathis 2026-05-16:
# brand_dna (extracted assets) → vocabulary_svg (canonical SVG library) →
# stock_fallback (curated, licensed) → css_placeholder (deterministic shape,
# fail-safe). NO image generation in v1.
AssetSourceStrategy = Literal[
    "brand_dna", "vocabulary_svg", "stock_fallback", "css_placeholder",
]

_ID_PATTERN: str = r"^[a-z0-9_-]{3,40}$"


# ─────────────────────────────────────────────────────────────────────────────
# CreativeRouteContract — deterministic façade post Visual Judge selection
# ─────────────────────────────────────────────────────────────────────────────


class CreativeRouteContract(BaseModel):
    """Façade snapshot over the route the Visual Judge selected.

    Built once by CR-04 ``visual_composer.bootstrap`` via
    :meth:`from_creative_route`, then handed down to renderer / QA. Carries
    ``decision_metadata`` (selected_at, model_used, scores) so any consumer
    can audit *why* this route won without re-loading
    ``creative_routes.json`` + ``route_selection_decision.json``.

    All ``thesis`` fields are inherited from CR-01 ``RouteThesis`` — we do
    NOT redefine them here (mono-concern, single source of truth).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_id: str = Field(..., pattern=_ID_PATTERN)
    route_name: str = Field(..., min_length=10, max_length=80)
    thesis: RouteThesis
    page_type_modules: list[str] = Field(..., min_length=2, max_length=12)
    risks: list[str] = Field(..., min_length=1, max_length=10)
    why_this_route_fits: str = Field(..., min_length=50, max_length=800)
    # selected_at: datetime, model_used: str, scores: dict — schema-free
    # so we can iterate on judge telemetry without bumping this contract.
    decision_metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_creative_route(
        cls,
        route: CreativeRoute,
        decision_metadata: dict[str, Any],
    ) -> "CreativeRouteContract":
        """Build the contract from a ``CreativeRoute`` (CR-01) + judge metadata.

        Snapshot pattern: we copy the route fields rather than holding a
        reference, so downstream consumers can serialise / hash / diff this
        contract independently of the original batch file.
        """
        return cls(
            route_id=route.route_id,
            route_name=route.route_name,
            thesis=route.thesis,
            page_type_modules=list(route.page_type_modules),
            risks=list(route.risks),
            why_this_route_fits=route.why_this_route_fits,
            decision_metadata=dict(decision_metadata),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Composer building blocks — Sections, Modules, Motion, Assets, Breakpoints
# ─────────────────────────────────────────────────────────────────────────────


class SectionSpec(BaseModel):
    """One page section the renderer must emit (hero, proof_strip, FAQ...).

    ``visual_modules`` lists ``module_id``s that *target* this section — the
    foreign-key direction is enforced by ``VisualComposerContract`` validator
    (``VisualModule.target_section`` MUST point to a valid section_id).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str = Field(..., pattern=_ID_PATTERN)
    section_type: SectionType
    layout: str = Field(..., min_length=3, max_length=80)  # e.g. "full-bleed-hero"
    copy_slots: list[str] = Field(default_factory=list)
    visual_modules: list[str] = Field(default_factory=list)
    order_index: int = Field(..., ge=0)


class VisualModule(BaseModel):
    """One visual decoration / structural component attached to a section.

    ``params`` is module-specific (e.g. gradient stops, panel layout
    dimensions). Schema-free intentionally — each module_type has its own
    contract enforced downstream by the renderer's typed visitor.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    module_id: str = Field(..., pattern=_ID_PATTERN)
    module_type: ModuleType
    target_section: str = Field(..., pattern=_ID_PATTERN)  # FK to SectionSpec.section_id
    params: dict[str, Any] = Field(default_factory=dict)


class MotionSpec(BaseModel):
    """One animation the renderer must wire (scroll/hover/load triggers).

    Durations capped at 3000ms to prevent UX-hostile slow animations; delays
    capped at 5000ms (anything longer is a content reveal, not motion).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    motion_id: str = Field(..., pattern=_ID_PATTERN)
    target_selector: str = Field(..., min_length=1, max_length=200)
    trigger: MotionTrigger
    animation_type: MotionAnimation
    duration_ms: int = Field(..., ge=50, le=3000)
    easing: MotionEasing
    delay_ms: int = Field(default=0, ge=0, le=5000)
    params: dict[str, Any] = Field(default_factory=dict)


class AssetSpec(BaseModel):
    """One image / texture / illustration / SVG the renderer must place.

    Resolution invariant (v1, no image-gen)
    ---------------------------------------
    Exactly ONE of the four resolution slots can be populated:
    - ``resolved_path`` (local file path under deliverables/ or assets/)
    - ``resolved_svg_inline`` (inline SVG string)
    - ``resolved_url`` (remote / CDN URL)
    - ``unresolved=True`` (fail-loud signal for renderer fallback)

    ``target_dimensions`` is dict-typed (width, height, optionally
    ratio_w/ratio_h) — width/height are required, ratio fields optional.
    Schema-light because asset_type-specific constraints belong to the
    renderer (e.g. logos prefer SVG inline, hero_images prefer URL).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_id: str = Field(..., pattern=_ID_PATTERN)
    asset_type: AssetType
    target_section: str = Field(..., pattern=_ID_PATTERN)  # FK to SectionSpec.section_id
    placement: AssetPlacement
    target_dimensions: dict[str, int] = Field(default_factory=dict)
    source_strategy: AssetSourceStrategy
    resolved_path: str | None = None
    resolved_svg_inline: str | None = None
    resolved_url: str | None = None
    unresolved: bool = False

    @model_validator(mode="after")
    def _exactly_one_resolution(self) -> "AssetSpec":
        """Exactly one of (resolved_path | resolved_svg_inline | resolved_url | unresolved=True).

        Image-gen SKIP v1 per Mathis 2026-05-16: if none of the first three
        resolve, ``unresolved=True`` is the only legal terminal state.
        """
        slots = [
            self.resolved_path is not None,
            self.resolved_svg_inline is not None,
            self.resolved_url is not None,
            self.unresolved,
        ]
        n_set = sum(slots)
        if n_set != 1:
            raise ValueError(
                f"AssetSpec {self.asset_id!r} must have EXACTLY one resolution "
                f"slot set (path | svg_inline | url | unresolved=True); got "
                f"{n_set} set."
            )
        return self


class ResponsiveBreakpoints(BaseModel):
    """Page breakpoints in pixels — defaults match Brand DNA dual-viewport.

    Bounds prevent absurd values: mobile 320-480 (covers iPhone SE → Plus),
    tablet 600-900 (covers iPad Mini → Pro), desktop 1024-1920 (covers
    laptops → 1080p monitors).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    mobile: int = Field(default=375, ge=320, le=480)
    tablet: int = Field(default=768, ge=600, le=900)
    desktop: int = Field(default=1440, ge=1024, le=1920)


# ─────────────────────────────────────────────────────────────────────────────
# VisualComposerContract — top-level deliverable from CR-04 to renderer/QA
# ─────────────────────────────────────────────────────────────────────────────


class VisualComposerContract(BaseModel):
    """Complete spec for one (route, client, page) that the renderer materialises.

    Invariants validated at construction:
    - All collection IDs are unique (sections / modules / motions / assets).
    - All ``VisualModule.target_section`` FKs resolve to a real section_id.
    - All ``AssetSpec.target_section`` FKs resolve to a real section_id.
    - All ``SectionSpec.order_index`` values are unique (no overlap).

    ``composer_metadata`` is free-form telemetry (composer version,
    generated_at, route_id provenance, etc.) — same pattern as CR-01
    ``prompt_meta`` and ``recos_models.RecoBatch.enrichment_meta``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_id: str = Field(..., pattern=_ID_PATTERN)  # FK to CreativeRouteContract.route_id
    client_slug: str = Field(..., pattern=r"^[a-z0-9_-]{2,40}$")
    page_type: str = Field(..., min_length=1, max_length=64)
    business_category: BusinessCategory

    sections: list[SectionSpec] = Field(..., min_length=3, max_length=24)
    modules: list[VisualModule] = Field(default_factory=list)
    motion_specs: list[MotionSpec] = Field(default_factory=list)
    asset_specs: list[AssetSpec] = Field(default_factory=list)

    responsive_breakpoints: ResponsiveBreakpoints = Field(
        default_factory=ResponsiveBreakpoints,
    )
    composer_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_invariants(self) -> "VisualComposerContract":
        """Enforce unique IDs + foreign keys in one pass.

        Bundled into a single validator so the error message can list all
        violations at once instead of failing on the first dupe + hiding
        the rest behind a re-raise.
        """
        # 1. Unique section_ids + collect valid set for FK checks
        section_ids: set[str] = set()
        for s in self.sections:
            if s.section_id in section_ids:
                raise ValueError(
                    f"duplicate section_id={s.section_id!r} in "
                    f"VisualComposerContract({self.client_slug}/{self.page_type})"
                )
            section_ids.add(s.section_id)

        # 2. Unique order_index across sections
        order_seen: set[int] = set()
        for s in self.sections:
            if s.order_index in order_seen:
                raise ValueError(
                    f"duplicate section order_index={s.order_index} in "
                    f"VisualComposerContract({self.client_slug}/{self.page_type})"
                )
            order_seen.add(s.order_index)

        # 3. Unique module_ids + FK to section_ids
        module_ids: set[str] = set()
        for m in self.modules:
            if m.module_id in module_ids:
                raise ValueError(f"duplicate module_id={m.module_id!r}")
            module_ids.add(m.module_id)
            if m.target_section not in section_ids:
                raise ValueError(
                    f"VisualModule {m.module_id!r} target_section="
                    f"{m.target_section!r} is not a valid section_id "
                    f"(known: {sorted(section_ids)})"
                )

        # 4. Unique motion_ids
        motion_ids: set[str] = set()
        for mo in self.motion_specs:
            if mo.motion_id in motion_ids:
                raise ValueError(f"duplicate motion_id={mo.motion_id!r}")
            motion_ids.add(mo.motion_id)

        # 5. Unique asset_ids + FK to section_ids
        asset_ids: set[str] = set()
        for a in self.asset_specs:
            if a.asset_id in asset_ids:
                raise ValueError(f"duplicate asset_id={a.asset_id!r}")
            asset_ids.add(a.asset_id)
            if a.target_section not in section_ids:
                raise ValueError(
                    f"AssetSpec {a.asset_id!r} target_section="
                    f"{a.target_section!r} is not a valid section_id "
                    f"(known: {sorted(section_ids)})"
                )

        return self


__all__ = [
    "AssetPlacement",
    "AssetSourceStrategy",
    "AssetSpec",
    "AssetType",
    "CreativeRouteContract",
    "ModuleType",
    "MotionAnimation",
    "MotionEasing",
    "MotionSpec",
    "MotionTrigger",
    "ResponsiveBreakpoints",
    "SectionSpec",
    "SectionType",
    "VisualComposerContract",
    "VisualModule",
]
