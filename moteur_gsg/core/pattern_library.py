"""Structured pattern library for canonical GSG planning.

This module replaces prompt dumping with small, deterministic pattern packs.
The first production target is `lp_listicle`.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARCHETYPES_DIR = ROOT / "data" / "layout_archetypes"
PAGE_TYPE_CRITERIA = ROOT / "playbook" / "page_type_criteria.json"
CRO_PATTERNS = ROOT / "skills" / "cro-library" / "references" / "patterns.json"

LAYOUT_NAMES = {
    "lp_listicle": "editorial_listicle_longform",
    "listicle": "editorial_listicle_longform",
    "advertorial": "native_editorial_advertorial",
    "lp_sales": "honest_longform_sales_letter",
    "lp_leadgen": "focused_leadgen_offer",
    "home": "product_manifesto_home",
    "pdp": "product_decision_page",
    "pricing": "decision_clarity_pricing",
    "comparison": "structured_comparison_page",
    "quiz_vsl": "guided_diagnostic_vsl",
    "vsl": "video_first_persuasion",
}


def _safe_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def infer_listicle_count(brief: dict[str, Any], default: int = 10) -> int:
    """Infer requested reason count while staying within editorial bounds."""
    text = " ".join(str(v) for v in (brief or {}).values() if isinstance(v, (str, int, float)))
    for match in re.finditer(r"\b(5|6|7|8|9|10|11|12)\s+(?:raisons?|reasons?|points?|erreurs?|leviers?)\b", text, re.I):
        return max(5, min(12, int(match.group(1))))
    return default


def _normalize_page_type(page_type: str) -> str:
    return "lp_listicle" if page_type in {"listicle", "lp_listicle"} else page_type


def _page_type_spec(page_type: str) -> dict[str, Any]:
    data = _safe_json(PAGE_TYPE_CRITERIA)
    specs = data.get("pageTypeSpecs") or {}
    return specs.get(page_type) or specs.get("listicle" if page_type == "lp_listicle" else page_type) or {}


def _business_aliases(category: str) -> set[str]:
    aliases = {category}
    if category in {"saas", "b2b_saas"}:
        aliases.update({"saas", "b2b_saas"})
    if category in {"ecommerce", "ecommerce_dtc", "dtc"}:
        aliases.update({"ecommerce", "ecommerce_dtc", "dtc"})
    if category in {"lead_gen", "leadgen", "leadgen_service"}:
        aliases.update({"lead_gen", "leadgen", "leadgen_service"})
    return aliases


def _selected_cro_patterns(
    *,
    page_type: str,
    business_category: str,
    criterion_ids: list[str],
    limit: int = 8,
) -> list[dict[str, Any]]:
    data = _safe_json(CRO_PATTERNS)
    patterns = data.get("patterns") or []
    if not isinstance(patterns, list):
        return []
    resolved_page = "listicle" if page_type == "lp_listicle" else page_type
    aliases = _business_aliases(business_category)
    selected = []
    for pattern in patterns:
        context = pattern.get("context") if isinstance(pattern, dict) else {}
        if not isinstance(context, dict):
            continue
        criterion_id = context.get("criterion_id")
        page_match = context.get("page_type") in {page_type, resolved_page}
        business_match = context.get("business_category") in aliases
        criterion_match = criterion_id in criterion_ids if criterion_ids else True
        if page_match and business_match and criterion_match:
            score = 4
        elif business_match and criterion_match:
            score = 3
        elif page_match and criterion_match:
            score = 2
        elif criterion_match:
            score = 1
        else:
            continue
        selected.append((score, pattern))
    selected.sort(key=lambda item: (-item[0], item[1].get("status") != "validated", item[1].get("pattern_id", "")))
    out = []
    for score, pattern in selected[:limit]:
        context = pattern.get("context") or {}
        out.append({
            "pattern_id": pattern.get("pattern_id"),
            "status": pattern.get("status"),
            "criterion_id": context.get("criterion_id"),
            "page_type": context.get("page_type"),
            "business_category": context.get("business_category"),
            "match_score": score,
            "name": pattern.get("name"),
            "summary": pattern.get("summary"),
            "layout_directives": pattern.get("layout_directives") or {},
        })
    return out


def _generic_pack(
    *,
    normalized: str,
    archetype: dict[str, Any],
    page_spec: dict[str, Any],
    business_category: str,
    cro_patterns: list[dict[str, Any]],
) -> dict[str, Any]:
    required = list(page_spec.get("structure_required") or page_spec.get("requiredSections") or [])
    specific = list(page_spec.get("specificCriteria") or [])
    return {
        "page_type": normalized,
        "version": "gsg-patterns-v27.2",
        "layout_name": LAYOUT_NAMES.get(normalized, "contextual_conversion_page"),
        "reason_count": 0,
        "business_category": business_category,
        "source_archetype": f"data/layout_archetypes/{normalized}.json" if archetype else None,
        "page_type_role": page_spec.get("role") or archetype.get("philosophy", ""),
        "specific_criteria": specific,
        "required_sections": required or ["hero", "proof", "body", "final_cta", "footer"],
        "forbidden": (
            list(page_spec.get("universalExclusions") or [])
            + list(archetype.get("structure_forbidden") or [])
            + ["fake_urgency", "unsourced_numbers"]
        ),
        "copy_policy": {"numbers_policy": "only allowed facts from deterministic constraints"},
        "visual_policy": {
            "letter_spacing": "0",
            "cards": "contextual_only",
            "philosophy": archetype.get("philosophy", ""),
            "decorative_required": archetype.get("decorative_techniques_required") or [],
            "decorative_forbidden": archetype.get("decorative_techniques_forbidden") or [],
        },
        "cro_patterns": cro_patterns,
        "archetype_summary": {
            "philosophy": archetype.get("philosophy", ""),
            "color_strategy": archetype.get("color_strategy", ""),
            "examples_to_imitate": (archetype.get("examples_to_imitate") or [])[:5],
        },
    }


def get_pattern_pack(
    page_type: str,
    brief: dict[str, Any] | None = None,
    *,
    doctrine_pack: dict[str, Any] | None = None,
    context_pack: dict[str, Any] | None = None,
    creative_route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a compact pattern pack for the target page type."""
    normalized = _normalize_page_type(page_type)
    archetype = _safe_json(ARCHETYPES_DIR / f"{normalized}.json")
    page_spec = _page_type_spec(normalized)
    business_category = (
        ((context_pack or {}).get("business") or {}).get("category")
        or (doctrine_pack or {}).get("business_category")
        or "generic_cro"
    )
    criterion_ids = [item.get("id") for item in (doctrine_pack or {}).get("criteria") or [] if item.get("id")]
    criterion_ids.extend(
        item.get("id")
        for item in (doctrine_pack or {}).get("page_type_specific_criteria") or []
        if item.get("id")
    )
    cro_patterns = _selected_cro_patterns(
        page_type=normalized,
        business_category=business_category,
        criterion_ids=criterion_ids,
    )

    if normalized == "lp_listicle":
        reason_count = infer_listicle_count(brief or {}, default=10)
        return {
            "page_type": "lp_listicle",
            "version": "gsg-patterns-v27.2",
            "layout_name": "editorial_listicle_longform",
            "reason_count": reason_count,
            "business_category": business_category,
            "source_archetype": "data/layout_archetypes/lp_listicle.json" if archetype else None,
            "signature": [
                "byline before h1",
                "no hero CTA",
                "single reading column",
                "oversized reason numbers",
                "desktop marginalia",
                "one quiet final CTA",
            ],
            "required_sections": [
                "byline",
                "hero",
                "toc",
                "intro",
                "numbered_reasons",
                "final_cta",
                "footer",
            ],
            "specific_criteria": page_spec.get("specificCriteria") or [],
            "forbidden": [
                "hero_cta",
                "three_column_cards",
                "testimonial_slider",
                "pricing_card_inline",
                "gradient_mesh_background",
                "fake_urgency",
                "unsourced_numbers",
            ],
            "copy_policy": {
                "h1_max_chars": 80,
                "intro_paragraphs": 2,
                "reason_paragraphs_min": 2,
                "reason_paragraphs_max": 3,
                "side_note_frequency": "every 3 reasons max",
                "numbers_policy": "only allowed facts from minimal constraints",
            },
            "visual_policy": {
                "content_width": "760px",
                "accent_ratio": "micro only",
                "cards": "forbidden",
                "letter_spacing": "0",
                "section_separators": "hairlines",
                "mobile": "single column, stable reason blocks",
            },
            "archetype_summary": {
                "philosophy": archetype.get("philosophy", ""),
                "color_strategy": archetype.get("color_strategy", ""),
                "examples_to_imitate": (archetype.get("examples_to_imitate") or [])[:5],
            },
            "cro_patterns": cro_patterns,
            "creative_route": creative_route or {},
            "golden_references": (creative_route or {}).get("golden_references") or [],
            "technique_references": (creative_route or {}).get("technique_references") or [],
        }

    pack = _generic_pack(
        normalized=normalized,
        archetype=archetype,
        page_spec=page_spec,
        business_category=business_category,
        cro_patterns=cro_patterns,
    )
    pack["creative_route"] = creative_route or {}
    pack["golden_references"] = (creative_route or {}).get("golden_references") or []
    pack["technique_references"] = (creative_route or {}).get("technique_references") or []
    return pack


def format_pattern_pack_for_prompt(pattern_pack: dict[str, Any]) -> str:
    """Compact prompt block for bounded copy generation."""
    lines = [
        "## STRUCTURE SYSTEME GSG",
        f"- Layout: {pattern_pack.get('layout_name')}",
        f"- Page type: {pattern_pack.get('page_type')}",
    ]
    if pattern_pack.get("reason_count"):
        lines.append(f"- Numbered reasons required: {pattern_pack['reason_count']}")
    if pattern_pack.get("signature"):
        lines.append("- Signature: " + ", ".join(pattern_pack["signature"]))
    if pattern_pack.get("specific_criteria"):
        ids = [item.get("id") for item in pattern_pack["specific_criteria"] if item.get("id")]
        if ids:
            lines.append("- Page-type criteria: " + ", ".join(ids))
    if pattern_pack.get("cro_patterns"):
        names = [
            (p.get("name") or "")[:120]
            for p in pattern_pack["cro_patterns"][:3]
            if p.get("name")
        ]
        if names:
            lines.append("- CRO patterns selected: " + " | ".join(names))
    if pattern_pack.get("forbidden"):
        lines.append("- Forbidden: " + ", ".join(pattern_pack["forbidden"]))
    policy = pattern_pack.get("copy_policy") or {}
    for key in ("h1_max_chars", "intro_paragraphs", "reason_paragraphs_min", "reason_paragraphs_max", "numbers_policy"):
        if key in policy:
            lines.append(f"- {key}: {policy[key]}")
    return "\n".join(lines)
