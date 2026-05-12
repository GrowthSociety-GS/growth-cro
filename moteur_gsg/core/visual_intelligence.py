"""Visual intelligence contracts for the canonical GSG.

AURA should not operate as an isolated source of taste. This module translates
GrowthCRO strategy + client context + doctrine into a compact visual language
contract that can feed AURA, Creative Director, Golden Bridge and the renderer.

Issue #30 — Pydantic-ize visual_intelligence (typing-strict-rollout):
The historical dataclasses ``VisualIntelligencePack`` and ``CreativeRouteContract``
are re-exposed here as thin re-exports of Pydantic v2 models living in
``growthcro/models/visual_models.py`` (``VisualReport``, ``CreativeRouteReport``).
The legacy names are kept as aliases for backward compatibility with existing
consumers (mode_1_complete, creative_route_selector, visual_system) that
import them by name. ``.to_dict()`` is preserved on the Pydantic models so
no downstream callsite changes are required.

The 13 union-attr mypy errors in the legacy implementation came from
``Optional[X].attr`` accesses on dict-returning helpers; the Pydantic boundary
guarantees presence of required fields and makes optionals explicit, absorbing
them at the public API frontier.
"""
from __future__ import annotations

from typing import Any

from growthcro.models.visual_models import CreativeRouteReport, VisualReport

# ─────────────────────────────────────────────────────────────────────────────
# Backward-compat aliases — external code imports these names.
# ─────────────────────────────────────────────────────────────────────────────
VisualIntelligencePack = VisualReport
CreativeRouteContract = CreativeRouteReport


PAGE_VISUAL_ROLES: dict[str, str] = {
    "lp_listicle": "premium_editorial_argument",
    "listicle": "premium_editorial_argument",
    "advertorial": "native_editorial_persuasion",
    "lp_sales": "honest_longform_conversion",
    "lp_leadgen": "focused_acquisition_offer",
    "home": "product_manifesto",
    "pdp": "product_decision_surface",
    "pricing": "decision_clarity_matrix",
    "comparison": "category_choice_argument",
    "quiz_vsl": "guided_diagnostic_story",
    "vsl": "video_first_persuasion",
}


def _has_criterion(doctrine_pack: dict[str, Any], criterion_id: str) -> bool:
    return any(c.get("id") == criterion_id for c in (doctrine_pack.get("criteria") or []))


def _traffic_sources(context_pack: dict[str, Any]) -> list[str]:
    scent = context_pack.get("scent_contract") or {}
    raw = scent.get("traffic_source") or []
    return [str(item) for item in raw]


def _proof_visibility(context_pack: dict[str, Any], doctrine_pack: dict[str, Any]) -> str:
    facts = context_pack.get("proof_inventory") or []
    if _has_criterion(doctrine_pack, "per_04") or _has_criterion(doctrine_pack, "psy_05"):
        if len(facts) >= 4:
            return "high_source_led"
        return "light_explicit_no_fake_claims"
    return "moderate_contextual"


def _density(page_type: str, business_category: str, context_pack: dict[str, Any]) -> str:
    if page_type in {"lp_listicle", "listicle", "advertorial", "lp_sales"}:
        return "medium_high_editorial"
    if page_type in {"pricing", "comparison"}:
        return "high_structured"
    if business_category in {"luxury"}:
        return "low_precise"
    if business_category in {"ecommerce", "lead_gen"}:
        return "medium_conversion"
    return "medium"


def _energy(page_type: str, traffic_sources: list[str]) -> str:
    if any("cold_ad" in source for source in traffic_sources):
        return "clear_high_signal"
    if page_type in {"lp_sales", "quiz_vsl", "vsl"}:
        return "narrative_build"
    if page_type in {"lp_listicle", "advertorial"}:
        return "calm_authoritative"
    return "controlled_momentum"


def _image_direction(page_type: str, business_category: str, context_pack: dict[str, Any]) -> list[str]:
    directions: list[str] = []
    assets = context_pack.get("visual_assets") or {}
    if business_category == "saas":
        directions.extend([
            "product UI screenshots in real workflow states",
            "process schematics, annotations and before/after operating states",
        ])
    elif business_category == "ecommerce":
        directions.extend([
            "real product-in-use photography, texture, hands, scale and material detail",
            "proof overlays only when sourced",
        ])
    elif business_category == "lead_gen":
        directions.extend([
            "service outcome visuals, process diagrams, trust markers near forms",
        ])
    elif business_category == "luxury":
        directions.extend([
            "material close-ups, restrained product staging, negative space and craft detail",
        ])
    else:
        directions.append("client-specific real assets before abstract illustration")

    if page_type in {"lp_listicle", "advertorial"}:
        directions.append("editorial marginalia, diagrams, source callouts and useful mini-visuals")
    if assets:
        directions.append("reuse captured client screenshots as first-class visual evidence")
    return directions


def _composition_directives(page_type: str, business_category: str, proof_visibility: str) -> list[str]:
    directives: list[str] = []
    if page_type in {"lp_listicle", "listicle"}:
        directives.extend([
            "single strong reading column with controlled interruptions",
            "numbered sections must have stable rhythm and visual anchors",
            "no hero CTA; conversion happens after editorial trust is built",
        ])
    elif page_type == "advertorial":
        directives.extend([
            "native article shell with sponsor transparency and named author signal",
            "soft CTAs only after narrative proof moments",
        ])
    elif page_type == "pdp":
        directives.extend([
            "product media is the first decision surface",
            "proof, risk reversal and purchase CTA stay close to the product object",
        ])
    elif page_type == "home":
        directives.extend([
            "first viewport must declare category, audience, result and product mechanism",
            "hero visual must materialize the product, not decorate the promise",
        ])
    else:
        directives.append("page structure follows page-type contract before visual flourish")

    if proof_visibility.startswith("high"):
        directives.append("proof is displayed as sourced callouts and evidence modules, not vague badges")
    if business_category == "saas":
        directives.append("avoid generic SaaS card grids; prefer product mechanics and workflow clarity")
    return directives


def build_visual_intelligence_pack(
    *,
    context_pack: dict[str, Any],
    doctrine_pack: dict[str, Any],
    brief: dict[str, Any],
) -> VisualReport:
    """Build the strategy-aware visual contract that feeds AURA and routing.

    Returns ``VisualReport`` (Pydantic v2). The legacy name
    ``VisualIntelligencePack`` is aliased to the same type for backward compat.
    """
    page_type = context_pack.get("page_type") or doctrine_pack.get("page_type") or "unknown"
    business = context_pack.get("business") or {}
    business_category = (
        business.get("category") or doctrine_pack.get("business_category") or "generic_cro"
    )
    traffic_sources = _traffic_sources(context_pack)
    proof_visibility = _proof_visibility(context_pack, doctrine_pack)
    density = _density(page_type, business_category, context_pack)
    energy = _energy(page_type, traffic_sources)
    visual_role = PAGE_VISUAL_ROLES.get(page_type, "contextual_conversion_page")
    brand = context_pack.get("brand") or {}
    risk_flags = list(context_pack.get("risk_flags") or [])

    warmth = "brand_derived"
    if business_category in {"luxury", "ecommerce"}:
        warmth = "material_human"
    elif business_category == "saas":
        warmth = "precise_product_led"

    editoriality = "high" if page_type in {"lp_listicle", "listicle", "advertorial"} else "medium"
    product_visibility = "high" if business_category in {"saas", "ecommerce", "app"} else "contextual"
    motion_profile = "subtle_stateful"
    if page_type in {"quiz_vsl", "vsl"}:
        motion_profile = "story_progressive"
    elif business_category == "luxury":
        motion_profile = "minimal_tactile"

    audience = context_pack.get("audience") or {}
    aura_input: dict[str, Any] = {
        "page_type": page_type,
        "business_category": business_category,
        "visual_role": visual_role,
        "density": density,
        "energy": energy,
        "warmth": warmth,
        "editoriality": editoriality,
        "product_visibility": product_visibility,
        "proof_visibility": proof_visibility,
        "brand_palette": brand.get("palette") or [],
        "brand_display_font": brand.get("display_font"),
        "brand_body_font": brand.get("body_font"),
        "objective": audience.get("objective"),
        "angle": brief.get("angle"),
    }

    return VisualReport(
        version="gsg-visual-intelligence-v27.2",
        slug=str(context_pack.get("slug") or brief.get("slug") or ""),
        page_type=page_type,
        business_category=business_category,
        visual_role=visual_role,
        density=density,
        warmth=warmth,
        energy=energy,
        editoriality=editoriality,
        product_visibility=product_visibility,
        proof_visibility=proof_visibility,
        motion_profile=motion_profile,
        image_direction=_image_direction(page_type, business_category, context_pack),
        composition_directives=_composition_directives(page_type, business_category, proof_visibility),
        aura_input_contract=aura_input,
        creative_director_seed={
            "risk_default": "premium" if page_type in {"lp_listicle", "advertorial", "home"} else "safe_premium",
            "route_question": (
                "What visual thesis best serves this strategy, brand, business category, page type and proof level?"
            ),
            "avoid": [
                "generic SaaS editorial if brand assets indicate stronger visual identity",
                "decorative visuals unrelated to product mechanism",
                "invented proof or fake urgency",
            ],
        },
        golden_bridge_query={
            "match_by": ["visual_role", "business_category", "page_type", "density", "proof_visibility"],
            "avoid_category_lock": True,
            "prefer": ["premium execution patterns", "real asset usage", "strong rhythm systems"],
        },
        risk_flags=risk_flags,
    )


def build_creative_route_contract(
    *,
    visual_pack: dict[str, Any],
    selected_route: dict[str, Any] | None = None,
) -> CreativeRouteReport:
    """Build a deterministic route contract, optionally enriched by Creative Director.

    Returns ``CreativeRouteReport`` (Pydantic v2). The legacy name
    ``CreativeRouteContract`` is aliased to the same type for backward compat.
    """
    route = selected_route or {}
    nested = route.get("route")
    route_body: dict[str, Any] = nested if isinstance(nested, dict) else route
    visual_role = visual_pack.get("visual_role") or "contextual_conversion_page"
    seed = visual_pack.get("creative_director_seed") or {}
    risk_level = route_body.get("risk_level") or seed.get("risk_default") or "premium"
    name = route_body.get("name") or f"{visual_role.replace('_', ' ').title()} Route"

    return CreativeRouteReport(
        version="gsg-creative-route-contract-v27.2",
        route_name=name,
        risk_level=risk_level,
        aesthetic_thesis=route_body.get("aesthetic_philosophy")
            or f"Make the page feel like a {visual_role}, not a generic landing page.",
        typography_thesis=route_body.get("typography_thesis")
            or "Use brand typography as hierarchy system; no negative letter spacing.",
        color_thesis=route_body.get("color_thesis")
            or "Respect brand palette, use accent with restraint, avoid one-note monochrome.",
        motion_thesis=route_body.get("motion_thesis")
            or f"Motion profile: {visual_pack.get('motion_profile', 'subtle_stateful')}.",
        section_rhythm=route_body.get("layout_concept")
            or f"Density: {visual_pack.get('density')}; energy: {visual_pack.get('energy')}.",
        component_emphasis=list(visual_pack.get("composition_directives") or []),
        must_not_do=list(route_body.get("must_not_do") or visual_pack.get("risk_flags") or []),
        golden_references=list(route_body.get("golden_references") or []),
        technique_references=list(route_body.get("technique_references") or []),
        route_decisions=route_body.get("route_decisions") or {},
        renderer_overrides=route_body.get("renderer_overrides") or {},
        source=route_body.get("source") or ("creative_director_adapter" if selected_route else "deterministic_visual_intelligence"),
    )


def format_visual_pack_for_prompt(pack: dict[str, Any]) -> str:
    """Compact copy-facing visual context. This is not a design prompt dump."""
    if not pack:
        return "## VISUAL INTELLIGENCE\n(non disponible)"
    lines = [
        "## VISUAL INTELLIGENCE PACK",
        f"- Visual role: {pack.get('visual_role')}",
        f"- Density: {pack.get('density')}",
        f"- Energy: {pack.get('energy')}",
        f"- Product visibility: {pack.get('product_visibility')}",
        f"- Proof visibility: {pack.get('proof_visibility')}",
    ]
    for directive in (pack.get("composition_directives") or [])[:4]:
        lines.append(f"- Composition: {directive}")
    return "\n".join(lines)


__all__ = [
    "PAGE_VISUAL_ROLES",
    "VisualIntelligencePack",
    "CreativeRouteContract",
    "build_visual_intelligence_pack",
    "build_creative_route_contract",
    "format_visual_pack_for_prompt",
]
