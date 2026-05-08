"""Structured creative route selector for the canonical GSG.

This is the V27.2-F bridge between VisualIntelligencePack, AURA and Golden
Bridge. It keeps the valuable Creative Director idea -- choose one named route
before rendering -- but makes it deterministic and render-facing. No LLM call,
no prompt dumping.
"""
from __future__ import annotations

import re
from typing import Any

from .legacy_lab_adapters import LegacyLabUnavailable, get_golden_design_benchmark
from .visual_intelligence import CreativeRouteContract

VECTOR_KEYS = ("energy", "warmth", "density", "depth", "motion", "editorial", "playful", "organic")


def _compact(value: Any, max_chars: int = 220) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:max_chars]


def _numeric(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _visual_bias(label: str, *, high: float = 4.0, mid: float = 3.0, low: float = 2.0) -> float:
    text = str(label or "").lower()
    if any(token in text for token in ("high", "bold", "clear_high", "narrative_build")):
        return high
    if any(token in text for token in ("low", "minimal", "calm")):
        return low
    return mid


def build_target_aesthetic_vector(
    *,
    visual_pack: dict[str, Any],
    aura_tokens: dict[str, Any] | None,
) -> dict[str, float]:
    """Compile AURA + VisualIntelligencePack into Golden Bridge vector input."""
    aura_tokens = aura_tokens or {}
    aura_vector = aura_tokens.get("vector") or aura_tokens.get("aesthetic_vector") or {}
    business = visual_pack.get("business_category")
    warmth_default = 2.2 if business == "saas" else 3.4 if business in {"ecommerce", "luxury"} else 3.0
    out = {
        "energy": _visual_bias(visual_pack.get("energy"), high=4.1, mid=3.2, low=2.4),
        "warmth": warmth_default,
        "density": _visual_bias(visual_pack.get("density"), high=3.9, mid=3.0, low=2.1),
        "depth": 3.4 if visual_pack.get("product_visibility") == "high" else 2.8,
        "motion": 3.3 if visual_pack.get("motion_profile") != "minimal_tactile" else 2.1,
        "editorial": 4.2 if visual_pack.get("editoriality") == "high" else 3.1,
        "playful": 2.1 if business == "saas" else 2.8,
        "organic": 1.6 if business == "saas" else 3.2,
    }
    for key in VECTOR_KEYS:
        if key in aura_vector:
            out[key] = _numeric(aura_vector.get(key), out[key])
    return {key: round(max(1.0, min(5.0, value)), 2) for key, value in out.items()}


def _golden_benchmark(target_vector: dict[str, float]) -> dict[str, Any]:
    try:
        return get_golden_design_benchmark(target_vector)
    except LegacyLabUnavailable:
        return {"philosophy_refs": [], "technique_refs": {}, "unavailable": "legacy_lab_unavailable"}
    except Exception as exc:
        return {"philosophy_refs": [], "technique_refs": {}, "error": str(exc)}


def _compact_golden_refs(benchmark: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    refs = []
    for ref in (benchmark.get("philosophy_refs") or [])[:limit]:
        refs.append({
            "site": ref.get("site"),
            "page": ref.get("page"),
            "category": ref.get("category"),
            "distance": ref.get("distance"),
            "signature": _compact(ref.get("signature"), 180),
            "wow_factor": _compact(ref.get("wow_factor"), 180),
            "why_matched": _compact(ref.get("why_matched"), 120),
        })
    return refs


def _compact_techniques(benchmark: dict[str, Any], limit: int = 7) -> list[dict[str, Any]]:
    out = []
    technique_refs = benchmark.get("technique_refs") or {}
    preferred_order = ("layout", "typography", "depth", "motion", "texture", "signature", "color", "background")
    for technique_type in preferred_order:
        for item in technique_refs.get(technique_type) or []:
            out.append({
                "type": technique_type,
                "name": _compact(item.get("name"), 90),
                "source_site": item.get("source_site"),
                "source_page": item.get("source_page"),
                "score": item.get("score"),
                "css_approach": _compact(item.get("css_approach"), 180),
                "why_it_works": _compact(item.get("why_it_works"), 160),
            })
            if len(out) >= limit:
                return out
    return out


def _select_risk(*, preferred: str | None, visual_pack: dict[str, Any], brief: dict[str, Any]) -> str:
    preferred = (preferred or "").lower()
    if preferred in {"safe", "premium", "bold"}:
        return preferred
    text = " ".join(_compact(brief.get(k), 220).lower() for k in ("angle", "desired_signature", "objectif", "objective"))
    if any(token in text for token in ("bold", "avant-garde", "stratos", "rupture", "signature forte")):
        return "bold"
    page_type = visual_pack.get("page_type")
    proof = str(visual_pack.get("proof_visibility") or "")
    if page_type in {"pricing", "pdp"} and "light" in proof:
        return "safe"
    return "premium"


def _route_template(
    *,
    risk: str,
    visual_pack: dict[str, Any],
    golden_refs: list[dict[str, Any]],
    techniques: list[dict[str, Any]],
) -> dict[str, Any]:
    page_type = visual_pack.get("page_type") or "page"
    role = visual_pack.get("visual_role") or "conversion_page"
    business = visual_pack.get("business_category") or "generic_cro"
    top_ref = golden_refs[0] if golden_refs else {}
    top_site = top_ref.get("site") or "golden corpus"
    top_signature = top_ref.get("signature") or "premium execution discipline"
    motion = next((t for t in techniques if t.get("type") == "motion"), {})
    layout = next((t for t in techniques if t.get("type") == "layout"), {})
    typography = next((t for t in techniques if t.get("type") == "typography"), {})

    names = {
        "safe": {
            "lp_listicle": "Editorial Product Brief",
            "advertorial": "Native Trust Dispatch",
            "pdp": "Product Proof Surface",
            "pricing": "Decision Clarity Desk",
        },
        "premium": {
            "lp_listicle": "Proof Atlas Editorial",
            "advertorial": "Field Report Premium",
            "pdp": "Material Decision Room",
            "pricing": "Choice Architecture Ledger",
        },
        "bold": {
            "lp_listicle": "Operating System Map",
            "advertorial": "Narrative Evidence Lab",
            "pdp": "Object Theatre",
            "pricing": "Pricing Command Surface",
        },
    }
    route_name = names.get(risk, {}).get(page_type) or {
        "safe": "Polished Brand System",
        "premium": "Premium Mechanism Atlas",
        "bold": "Distinctive Conversion Theatre",
    }[risk]

    overrides_by_risk = {
        "safe": {"hero_variant": None, "rhythm": None, "proof_mode": None},
        "premium": {"hero_variant": "proof_atlas", "rhythm": "atlas_marginalia", "proof_mode": "source_strip"},
        "bold": {"hero_variant": "system_map", "rhythm": "system_map", "proof_mode": "source_strip"},
    }
    if page_type in {"pdp", "pricing", "lp_leadgen"}:
        overrides_by_risk["premium"]["hero_variant"] = None
        overrides_by_risk["bold"]["hero_variant"] = None
    renderer_overrides = {
        key: value
        for key, value in overrides_by_risk[risk].items()
        if value
    }

    return {
        "route_name": route_name,
        "risk_level": risk,
        "aesthetic_thesis": (
            f"{route_name} turns {role} into a named visual system for {business}. "
            f"It borrows execution discipline from {top_site}, not its style: {top_signature}"
        ),
        "typography_thesis": (
            typography.get("css_approach")
            or "Use brand display type as editorial hierarchy, pull-quote scale and section rhythm; letter spacing stays 0."
        ),
        "color_thesis": (
            "Brand palette remains structural: neutral reading surface, one primary action color, one micro-accent for proof and rhythm."
        ),
        "motion_thesis": (
            motion.get("css_approach")
            or f"Motion profile follows {visual_pack.get('motion_profile')}: stateful, subtle, never decorative noise."
        ),
        "section_rhythm": (
            layout.get("css_approach")
            or f"Rhythm follows {visual_pack.get('density')} density and {visual_pack.get('energy')} energy."
        ),
        "component_emphasis": list(visual_pack.get("composition_directives") or []) + [
            "Use Golden references as execution bar only; never copy their sector style.",
            "Give each major section one visual job: proof, mechanism, objection or product state.",
        ],
        "must_not_do": list(visual_pack.get("risk_flags") or []) + [
            "no mega-prompt design mashup",
            "no unsourced visual proof",
            "no generic SaaS card grid",
            "no decorative motif without product or proof job",
        ],
        "renderer_overrides": renderer_overrides,
        "route_decisions": {
            "selected_risk": risk,
            "selection_reason": f"{risk} route selected from visual role, page type, proof level and brief ambition.",
            "target_vector_source": "aura_tokens_plus_visual_intelligence",
            "top_golden_site": top_site,
            "technique_types": [t.get("type") for t in techniques if t.get("type")],
        },
    }


def build_structured_creative_route_contract(
    *,
    visual_pack: dict[str, Any],
    brand_dna: dict[str, Any] | None = None,
    brief: dict[str, Any] | None = None,
    aura_tokens: dict[str, Any] | None = None,
    preferred_risk: str | None = None,
) -> CreativeRouteContract:
    """Return the final render-facing CreativeRouteContract."""
    brief = brief or {}
    target_vector = build_target_aesthetic_vector(visual_pack=visual_pack, aura_tokens=aura_tokens)
    benchmark = _golden_benchmark(target_vector)
    golden_refs = _compact_golden_refs(benchmark)
    techniques = _compact_techniques(benchmark)
    risk = _select_risk(preferred=preferred_risk, visual_pack=visual_pack, brief=brief)
    route = _route_template(
        risk=risk,
        visual_pack=visual_pack,
        golden_refs=golden_refs,
        techniques=techniques,
    )
    route["route_decisions"]["target_vector"] = target_vector
    route["route_decisions"]["brand_signature"] = _compact(
        (((brand_dna or {}).get("voice_tokens") or {}).get("voice_signature_phrase")),
        160,
    )

    return CreativeRouteContract(
        version="gsg-creative-route-contract-v27.2-f",
        route_name=route["route_name"],
        risk_level=route["risk_level"],
        aesthetic_thesis=route["aesthetic_thesis"],
        typography_thesis=route["typography_thesis"],
        color_thesis=route["color_thesis"],
        motion_thesis=route["motion_thesis"],
        section_rhythm=route["section_rhythm"],
        component_emphasis=route["component_emphasis"],
        must_not_do=route["must_not_do"],
        golden_references=golden_refs,
        technique_references=techniques,
        route_decisions=route["route_decisions"],
        renderer_overrides=route["renderer_overrides"],
        source="structured_golden_creative_selector",
    )


def creative_route_selector_status() -> dict[str, Any]:
    return {
        "version": "gsg-creative-route-selector-v27.2-f",
        "inputs": ["VisualIntelligencePack", "AURA vector", "Golden Bridge benchmark", "BriefV2 ambition"],
        "llm_calls": 0,
        "risk_routes": ["safe", "premium", "bold"],
        "renderer_override_keys": ["hero_variant", "rhythm", "proof_mode"],
    }
