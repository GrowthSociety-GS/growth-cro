"""Page-type component blueprints for the canonical GSG.

V27.2-B turns the strategic contracts into concrete section/component plans.
The renderer can still be modest, but the planner must stop pretending that all
non-listicle pages are three generic blocks.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


PRIORITY_PAGE_TYPES = [
    "lp_listicle",
    "advertorial",
    "lp_sales",
    "lp_leadgen",
    "home",
    "pdp",
    "pricing",
]


SLOT_PRESETS = {
    "hero": [
        {"key": "eyebrow", "role": "Small positioning or series label.", "max_chars": 54, "required": False},
        {"key": "h1", "role": "Primary promise, specific and non-generic.", "max_chars": 86, "required": True},
        {"key": "dek", "role": "Dense supporting paragraph with audience, mechanism and outcome.", "max_chars": 260, "required": True},
    ],
    "body": [
        {"key": "heading", "role": "Section heading, concrete and short.", "max_chars": 88, "required": True},
        {"key": "body", "role": "One or two concise paragraphs.", "max_chars": 520, "required": True},
        {"key": "bullets", "role": "Optional concrete bullets.", "max_chars": 360, "required": False},
        {"key": "microcopy", "role": "Optional source/proof/transition line.", "max_chars": 150, "required": False},
    ],
    "cta": [
        {"key": "heading", "role": "Closing conversion sentence.", "max_chars": 90, "required": True},
        {"key": "body", "role": "One paragraph that reduces friction without fake urgency.", "max_chars": 240, "required": True},
        {"key": "button_label", "role": "Must match deterministic CTA label.", "max_chars": 60, "required": True},
    ],
    "footer": [
        {"key": "brand_line", "role": "Tiny brand footer line.", "max_chars": 120, "required": True},
    ],
}


PAGE_COMPONENT_BLUEPRINTS: dict[str, list[dict[str, Any]]] = {
    "home": [
        {
            "id": "hero",
            "kind": "hero_conversion",
            "label": "Hero Manifesto",
            "intent": "Declare category, audience, result and product mechanism in one first-viewport system.",
            "slots": SLOT_PRESETS["hero"],
            "renderer": {"layout": "split_product", "cta_allowed": True, "visual": "product_mechanism"},
        },
        {
            "id": "mechanism",
            "kind": "mechanism_explainer",
            "label": "Product Mechanism",
            "intent": "Show how the product creates the promised result, not just why the brand is nice.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "two_column", "visual": "process_schematic"},
        },
        {
            "id": "proof_stack",
            "kind": "proof_stack",
            "label": "Proof Stack",
            "intent": "Convert available evidence into sourced trust, avoiding vague badges.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "proof_grid", "proof_required": True},
        },
        {
            "id": "audience_paths",
            "kind": "audience_paths",
            "label": "Audience Paths",
            "intent": "Help different visitor segments find the right next action without fragmenting the main CTA.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "pathways", "max_items": 3},
        },
        {
            "id": "final_cta",
            "kind": "final_cta",
            "label": "Final CTA",
            "intent": "Close with one primary action and one friction reducer.",
            "slots": SLOT_PRESETS["cta"],
            "renderer": {"placement": "after_proof", "style": "decisive"},
        },
        {"id": "footer", "kind": "footer_minimal", "label": "Footer", "intent": "Silent footer.", "slots": SLOT_PRESETS["footer"], "renderer": {}},
    ],
    "lp_leadgen": [
        {
            "id": "hero",
            "kind": "hero_offer",
            "label": "Offer Hero",
            "intent": "Make the lead magnet or consultation promise obvious, specific and low-friction.",
            "slots": SLOT_PRESETS["hero"],
            "renderer": {"layout": "offer_form_split", "cta_allowed": True},
        },
        {
            "id": "value_exchange",
            "kind": "value_exchange",
            "label": "Value Exchange",
            "intent": "Explain why giving contact details is worth it, in concrete outcomes.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "benefit_stack"},
        },
        {
            "id": "trust_near_form",
            "kind": "trust_near_form",
            "label": "Trust Near Form",
            "intent": "Reduce spam/privacy/perceived effort anxiety near the conversion moment.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "trust_strip", "proof_required": True},
        },
        {
            "id": "objection_resolver",
            "kind": "objection_resolver",
            "label": "Objection Resolver",
            "intent": "Answer the top doubts before the form or CTA.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "faq_compact"},
        },
        {"id": "final_cta", "kind": "final_cta", "label": "Final CTA", "intent": "Repeat the one action.", "slots": SLOT_PRESETS["cta"], "renderer": {"style": "form_anchor"}},
        {"id": "footer", "kind": "footer_minimal", "label": "Footer", "intent": "Silent footer.", "slots": SLOT_PRESETS["footer"], "renderer": {}},
    ],
    "lp_sales": [
        {
            "id": "hero",
            "kind": "sales_letter_open",
            "label": "Sales Letter Open",
            "intent": "Open with a strong thesis: who this is for, what changed, why now.",
            "slots": SLOT_PRESETS["hero"],
            "renderer": {"layout": "editorial_sales", "cta_allowed": True},
        },
        {
            "id": "problem_mechanism",
            "kind": "problem_mechanism",
            "label": "Problem Mechanism",
            "intent": "Name the real mechanism behind the pain, not a generic problem.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "diagnostic"},
        },
        {
            "id": "new_way",
            "kind": "new_way",
            "label": "New Way",
            "intent": "Show the product as a new operating model, not a pile of features.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "before_after"},
        },
        {
            "id": "proof_logic",
            "kind": "proof_logic",
            "label": "Proof Logic",
            "intent": "Use source-led proof, named mechanism or transparent reasoning.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "evidence_ledger"},
        },
        {
            "id": "objection_resolver",
            "kind": "objection_resolver",
            "label": "Objection Resolver",
            "intent": "Resolve cost/time/risk objections honestly.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "objection_cards"},
        },
        {"id": "final_cta", "kind": "final_cta", "label": "Final CTA", "intent": "Close the argument with one action.", "slots": SLOT_PRESETS["cta"], "renderer": {"style": "letter_close"}},
        {"id": "footer", "kind": "footer_minimal", "label": "Footer", "intent": "Silent footer.", "slots": SLOT_PRESETS["footer"], "renderer": {}},
    ],
    "advertorial": [
        {
            "id": "byline",
            "kind": "byline",
            "label": "Byline",
            "intent": "Signal named editorial authorship and source discipline.",
            "slots": [
                {"key": "author_name", "role": "Named editorial author or desk.", "max_chars": 48, "required": True},
                {"key": "author_role", "role": "Short role.", "max_chars": 72, "required": True},
                {"key": "date_label", "role": "Date or reading time.", "max_chars": 40, "required": False},
            ],
            "renderer": {"position": "top"},
        },
        {
            "id": "hero",
            "kind": "editorial_hero",
            "label": "Editorial Hero",
            "intent": "Frame the story like a premium native article, not an ad.",
            "slots": SLOT_PRESETS["hero"],
            "renderer": {"layout": "article_hero", "cta_allowed": False},
        },
        {
            "id": "narrative_problem",
            "kind": "narrative_problem",
            "label": "Narrative Problem",
            "intent": "Start with a recognizable situation and tension.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "article_body"},
        },
        {
            "id": "sponsored_disclosure",
            "kind": "sponsored_disclosure",
            "label": "Disclosure",
            "intent": "Keep sponsored/native status transparent and brand-safe.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "disclosure"},
        },
        {
            "id": "product_bridge",
            "kind": "product_bridge",
            "label": "Product Bridge",
            "intent": "Introduce the product as the natural answer to the article tension.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "native_bridge"},
        },
        {
            "id": "proof_moment",
            "kind": "proof_moment",
            "label": "Proof Moment",
            "intent": "Add sourced credibility without turning into a testimonial carousel.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "source_callout", "proof_required": True},
        },
        {"id": "final_cta", "kind": "final_cta", "label": "Final CTA", "intent": "Soft conversion after editorial trust.", "slots": SLOT_PRESETS["cta"], "renderer": {"style": "soft_native"}},
        {"id": "footer", "kind": "footer_minimal", "label": "Footer", "intent": "Silent footer.", "slots": SLOT_PRESETS["footer"], "renderer": {}},
    ],
    "pdp": [
        {
            "id": "hero",
            "kind": "product_decision_hero",
            "label": "Product Decision Hero",
            "intent": "Make the product object, use case, price/value and CTA feel immediate.",
            "slots": SLOT_PRESETS["hero"],
            "renderer": {"layout": "product_media_buybox", "cta_allowed": True},
        },
        {
            "id": "benefit_stack",
            "kind": "benefit_stack",
            "label": "Benefit Stack",
            "intent": "Translate features into tangible usage outcomes.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "feature_benefit_stack"},
        },
        {
            "id": "material_detail",
            "kind": "material_detail",
            "label": "Material Detail",
            "intent": "Show composition, texture, mechanism or specs transparently.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "detail_panel"},
        },
        {
            "id": "proof_risk_reversal",
            "kind": "proof_risk_reversal",
            "label": "Proof + Risk Reversal",
            "intent": "Keep reviews, guarantee, delivery and returns near purchase intent.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "trust_purchase", "proof_required": True},
        },
        {
            "id": "usage_steps",
            "kind": "usage_steps",
            "label": "Usage Steps",
            "intent": "Reduce uncertainty by showing what happens after purchase.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "steps"},
        },
        {"id": "final_cta", "kind": "final_cta", "label": "Final CTA", "intent": "One purchase action, no competing path.", "slots": SLOT_PRESETS["cta"], "renderer": {"style": "purchase"}},
        {"id": "footer", "kind": "footer_minimal", "label": "Footer", "intent": "Silent footer.", "slots": SLOT_PRESETS["footer"], "renderer": {}},
    ],
    "pricing": [
        {
            "id": "hero",
            "kind": "pricing_decision_hero",
            "label": "Pricing Hero",
            "intent": "Clarify who should choose what and why the pricing model is fair.",
            "slots": SLOT_PRESETS["hero"],
            "renderer": {"layout": "pricing_intro", "cta_allowed": True},
        },
        {
            "id": "plan_logic",
            "kind": "plan_logic",
            "label": "Plan Logic",
            "intent": "Explain the organizing principle behind tiers before showing details.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "tier_logic"},
        },
        {
            "id": "comparison_matrix",
            "kind": "comparison_matrix",
            "label": "Comparison Matrix",
            "intent": "Support comparison without overwhelming the buyer.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "matrix"},
        },
        {
            "id": "risk_reversal",
            "kind": "risk_reversal",
            "label": "Risk Reversal",
            "intent": "Address cancellation, trial, support and implementation risk.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "risk_band", "proof_required": True},
        },
        {
            "id": "pricing_faq",
            "kind": "pricing_faq",
            "label": "Pricing FAQ",
            "intent": "Answer the objections that block price selection.",
            "slots": SLOT_PRESETS["body"],
            "renderer": {"layout": "faq_compact"},
        },
        {"id": "final_cta", "kind": "final_cta", "label": "Final CTA", "intent": "One final pricing action.", "slots": SLOT_PRESETS["cta"], "renderer": {"style": "pricing"}},
        {"id": "footer", "kind": "footer_minimal", "label": "Footer", "intent": "Silent footer.", "slots": SLOT_PRESETS["footer"], "renderer": {}},
    ],
}


def _normalize(page_type: str) -> str:
    return "lp_listicle" if page_type in {"listicle", "lp_listicle"} else page_type


def get_component_blueprints(
    *,
    page_type: str,
    pattern_pack: dict[str, Any] | None = None,
    visual_intelligence: dict[str, Any] | None = None,
    creative_route_contract: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return section/component blueprints for a page type."""
    normalized = _normalize(page_type)
    blueprints = deepcopy(PAGE_COMPONENT_BLUEPRINTS.get(normalized) or PAGE_COMPONENT_BLUEPRINTS["home"])
    visual_intelligence = visual_intelligence or {}
    creative_route_contract = creative_route_contract or {}
    pattern_pack = pattern_pack or {}

    for blueprint in blueprints:
        renderer = blueprint.setdefault("renderer", {})
        renderer.setdefault("visual_role", visual_intelligence.get("visual_role"))
        renderer.setdefault("density", visual_intelligence.get("density"))
        renderer.setdefault("route_name", creative_route_contract.get("route_name"))
        renderer.setdefault("layout_name", pattern_pack.get("layout_name"))
    return blueprints


def component_library_status() -> dict[str, Any]:
    """Generation-free status for canonical validation."""
    return {
        "version": "gsg-component-library-v27.2",
        "priority_page_types": PRIORITY_PAGE_TYPES,
        "implemented_page_types": sorted(PAGE_COMPONENT_BLUEPRINTS.keys()),
        "component_count_by_page_type": {
            page_type: len(blueprints)
            for page_type, blueprints in sorted(PAGE_COMPONENT_BLUEPRINTS.items())
        },
    }
