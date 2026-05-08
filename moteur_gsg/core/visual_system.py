"""Deterministic visual system contract for the controlled GSG renderer.

V27.2-C keeps visual ambition out of the copy prompt. The system turns page
type, VisualIntelligencePack, CreativeRouteContract, renderer blueprints and
available assets into renderable visual modules.
"""
from __future__ import annotations

from typing import Any

from .planner import GSGPagePlan, SectionPlan


PAGE_RENDER_PROFILES: dict[str, dict[str, Any]] = {
    "lp_listicle": {
        "shell": "visual-shell-editorial",
        "hero_variant": "research_browser",
        "rhythm": "editorial_marginalia",
        "proof_mode": "source_strip",
    },
    "advertorial": {
        "shell": "visual-shell-article",
        "hero_variant": "native_article",
        "rhythm": "article_interruption",
        "proof_mode": "sourced_native",
    },
    "lp_sales": {
        "shell": "visual-shell-sales",
        "hero_variant": "sales_argument",
        "rhythm": "argument_build",
        "proof_mode": "evidence_ledger",
    },
    "lp_leadgen": {
        "shell": "visual-shell-leadgen",
        "hero_variant": "offer_form",
        "rhythm": "offer_trust",
        "proof_mode": "near_form_trust",
    },
    "home": {
        "shell": "visual-shell-home",
        "hero_variant": "product_manifesto",
        "rhythm": "product_story",
        "proof_mode": "product_proof",
    },
    "pdp": {
        "shell": "visual-shell-product",
        "hero_variant": "product_surface",
        "rhythm": "purchase_decision",
        "proof_mode": "risk_reversal",
    },
    "pricing": {
        "shell": "visual-shell-pricing",
        "hero_variant": "pricing_matrix",
        "rhythm": "decision_matrix",
        "proof_mode": "choice_reassurance",
    },
}


LAYOUT_VISUAL_KINDS: dict[str, str] = {
    "split_product": "product_mechanism",
    "two_column": "process_schematic",
    "process_schematic": "process_schematic",
    "proof_grid": "proof_ledger",
    "pathways": "decision_paths",
    "offer_form_split": "lead_form",
    "benefit_stack": "benefit_ladder",
    "trust_strip": "proof_ledger",
    "faq_compact": "objection_stack",
    "editorial_sales": "sales_argument",
    "diagnostic": "diagnostic_map",
    "before_after": "before_after",
    "evidence_ledger": "proof_ledger",
    "objection_cards": "objection_stack",
    "article_hero": "native_article",
    "article_body": "editorial_marginalia",
    "disclosure": "disclosure_bar",
    "native_bridge": "product_bridge",
    "source_callout": "proof_ledger",
    "product_media_buybox": "product_surface",
    "feature_benefit_stack": "benefit_ladder",
    "detail_panel": "product_detail",
    "trust_purchase": "purchase_trust",
    "steps": "usage_sequence",
    "pricing_intro": "pricing_matrix",
    "tier_logic": "tier_logic",
    "matrix": "pricing_matrix",
    "risk_band": "purchase_trust",
}


def _normalize(page_type: str) -> str:
    return "lp_listicle" if page_type in {"listicle", "lp_listicle"} else page_type


def _slug(value: Any) -> str:
    out = "".join(ch if ch.isalnum() else "-" for ch in str(value or "").lower()).strip("-")
    return "-".join(part for part in out.split("-") if part)[:72] or "route"


def _asset_keys(plan: GSGPagePlan) -> list[str]:
    return sorted((plan.constraints.get("visual_assets") or {}).keys())


def _preferred_asset(page_type: str, visual_kind: str, available: list[str]) -> str | None:
    preferences: list[str] = []
    if page_type in {"pdp"} or visual_kind in {"product_surface", "product_detail", "purchase_trust"}:
        preferences.extend(["target_desktop_fold", "target_desktop_full", "pdp_fold", "pdp_full", "desktop_fold", "desktop_full"])
    elif page_type == "pricing" or visual_kind in {"pricing_matrix", "tier_logic"}:
        preferences.extend(["target_desktop_fold", "target_desktop_full", "pricing_fold", "pricing_full", "desktop_fold", "desktop_full"])
    elif page_type == "lp_leadgen" or visual_kind in {"lead_form", "benefit_ladder"}:
        preferences.extend(["target_desktop_fold", "target_desktop_full", "lp_leadgen_fold", "lp_leadgen_full", "desktop_fold", "desktop_full"])
    elif visual_kind in {"native_article", "editorial_marginalia", "product_bridge", "process_schematic"}:
        preferences.extend(["target_desktop_full", "desktop_full", "target_desktop_fold", "desktop_fold"])
    else:
        preferences.extend(["target_desktop_fold", "target_desktop_full", "desktop_fold", "desktop_full", "pricing_fold", "lp_leadgen_fold"])

    for key in preferences:
        if key in available:
            return key
    return available[0] if available else None


def _module_for_section(
    *,
    plan: GSGPagePlan,
    section: SectionPlan,
    idx: int,
    available_assets: list[str],
) -> dict[str, Any]:
    renderer = section.renderer or {}
    layout = renderer.get("layout") or renderer.get("visual") or section.kind
    visual_kind = LAYOUT_VISUAL_KINDS.get(str(layout), LAYOUT_VISUAL_KINDS.get(section.kind, "concept_panel"))
    asset_key = _preferred_asset(plan.page_type, visual_kind, available_assets)
    return {
        "section_id": section.id,
        "index": idx,
        "layout": layout,
        "visual_kind": visual_kind,
        "asset_key": asset_key,
        "proof_required": bool(renderer.get("proof_required")),
        "classes": [
            "visual-module",
            f"visual-{visual_kind}",
            f"rhythm-{(idx - 1) % 3}",
            "component-reverse" if idx % 2 == 0 and plan.page_type not in {"pdp", "pricing"} else "",
        ],
    }


def _premium_layer(
    *,
    page_type: str,
    visual: dict[str, Any],
    route: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    risk = route.get("risk_level") or "premium"
    hero_variant = profile.get("hero_variant")
    if page_type == "lp_listicle" and hero_variant == "proof_atlas":
        name = "editorial-proof-atlas"
        reason_visual = "atlas_file_rail"
        section_transition = "folio_hairline"
    elif hero_variant == "system_map":
        name = "system-map-theatre"
        reason_visual = "network_map"
        section_transition = "circuit_hairline"
    elif page_type in {"pdp", "pricing"}:
        name = "decision-surface-premium"
        reason_visual = "decision_matrix"
        section_transition = "precision_grid"
    elif page_type in {"advertorial", "lp_sales"}:
        name = "narrative-evidence-premium"
        reason_visual = "source_column"
        section_transition = "editorial_cut"
    else:
        name = "brand-mechanism-premium"
        reason_visual = "signal_rail"
        section_transition = "mechanism_hairline"
    return {
        "version": "gsg-premium-visual-layer-v27.2-g",
        "name": name,
        "texture": "paper_grain" if visual.get("editoriality") == "high" else "subtle_interface_grain",
        "motion": "editorial_reveal" if risk != "bold" else "kinetic_map_reveal",
        "asset_strategy": "client_real_assets_first",
        "module_frame": "proof_folio" if "proof" in name or "evidence" in name else "mechanism_panel",
        "reason_visual": reason_visual,
        "section_transition": section_transition,
    }


def build_visual_system(plan: GSGPagePlan) -> dict[str, Any]:
    """Return render-facing visual decisions for a page plan."""
    page_type = _normalize(plan.page_type)
    visual = plan.visual_intelligence or {}
    route = plan.creative_route_contract or {}
    base_profile = PAGE_RENDER_PROFILES.get(page_type) or PAGE_RENDER_PROFILES["home"]
    overrides = route.get("renderer_overrides") or {}
    profile = {
        **base_profile,
        **{
            key: value
            for key, value in overrides.items()
            if key in {"shell", "hero_variant", "rhythm", "proof_mode"} and value
        },
    }
    available_assets = _asset_keys(plan)
    sections = [
        section for section in plan.sections
        if section.id not in {"hero", "final_cta", "footer", "byline"}
    ]
    modules = {
        section.id: _module_for_section(
            plan=plan,
            section=section,
            idx=idx,
            available_assets=available_assets,
        )
        for idx, section in enumerate(sections, start=1)
    }
    density = visual.get("density") or "medium"
    energy = visual.get("energy") or "controlled_momentum"
    proof_visibility = visual.get("proof_visibility") or "moderate_contextual"
    return {
        "version": "gsg-visual-system-v27.2-g",
        "page_type": page_type,
        "business_category": visual.get("business_category") or "generic_cro",
        "visual_role": visual.get("visual_role") or "contextual_conversion_page",
        "density": density,
        "energy": energy,
        "motion_profile": visual.get("motion_profile") or "subtle_stateful",
        "proof_visibility": proof_visibility,
        "route_name": route.get("route_name") or "deterministic_route",
        "risk_level": route.get("risk_level") or "premium",
        "shell_classes": " ".join([
            "page-shell",
            profile["shell"],
            f"route-{_slug(route.get('route_name'))}",
            f"risk-{_slug(route.get('risk_level') or 'premium')}",
            f"density-{str(density).replace('_', '-')}",
            f"energy-{str(energy).replace('_', '-')}",
        ]),
        "hero_variant": profile["hero_variant"],
        "rhythm": profile["rhythm"],
        "proof_mode": profile["proof_mode"],
        "premium_layer": _premium_layer(
            page_type=page_type,
            visual=visual,
            route=route,
            profile=profile,
        ),
        "asset_keys": available_assets,
        "modules": modules,
        "golden_ref_count": len(route.get("golden_references") or []),
        "technique_ref_count": len(route.get("technique_references") or []),
        "renderer_overrides": overrides,
    }


def visual_system_status() -> dict[str, Any]:
    """Generation-free status for canonical validation."""
    return {
        "version": "gsg-visual-system-v27.2-g",
        "page_profiles": sorted(PAGE_RENDER_PROFILES.keys()),
        "visual_kinds": sorted(set(LAYOUT_VISUAL_KINDS.values())),
        "layout_bindings": len(LAYOUT_VISUAL_KINDS),
        "route_override_keys": ["shell", "hero_variant", "rhythm", "proof_mode"],
        "premium_layer": "gsg-premium-visual-layer-v27.2-g",
    }
