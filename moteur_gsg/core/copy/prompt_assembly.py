"""Copy prompt assembly — builds the bounded system+user prompt for the GSG copy LLM.

Concern axis: prompt assembly (axis 1).

Composes the user prompt from deterministic plan/context/doctrine/visual/
pattern/brand blocks plus a compacted brief, and ships the system prompt
constant + the prompt size hard limit. No LLM calls here, no I/O — pure
string templating.
"""
from __future__ import annotations

import json
import re
from typing import Any

from moteur_gsg.core.brand_intelligence import format_brand_block
from moteur_gsg.core.context_pack import format_context_pack_for_prompt
from moteur_gsg.core.doctrine_planner import format_doctrine_pack_for_prompt
from moteur_gsg.core.minimal_guards import format_minimal_constraints_block
from moteur_gsg.core.pattern_library import format_pattern_pack_for_prompt
from moteur_gsg.core.planner import GSGPagePlan, format_plan_for_prompt
from moteur_gsg.core.visual_intelligence import format_visual_pack_for_prompt


COPY_SYSTEM_PROMPT = """You are a senior French editorial copywriter for premium CRO landing pages.

You only return valid JSON. You never return HTML.

Rules:
- Write in the target language from the plan.
- Respect the exact section IDs from the plan.
- Do not invent numbers, percentages, dates, client names, quotes, ratings, awards, or case studies.
- Use only numbers listed in the deterministic constraints or already present in the brief.
- Do not create new durations such as "1 journée", "30 minutes", "2 jours", or "24 heures" unless that exact duration appears as an allowed fact.
- If proof is missing, write qualitatively.
- Keep copy specific, concrete, and non-generic.
- The renderer owns layout. Do not mention layout instructions in copy."""

COPY_PROMPT_MAX_CHARS = 10000


def _compact_text(value: Any, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:max_chars]


def _compact_brief_for_copy(brief: dict[str, Any]) -> dict[str, Any]:
    """Keep copy-critical brief fields without dumping the full intake object."""
    out = {
        "objective": _compact_text(brief.get("objectif") or brief.get("objective"), 180),
        "audience": _compact_text(brief.get("audience"), 420),
        "angle": _compact_text(brief.get("angle"), 360),
    }
    for key in ("traffic_source", "visitor_mode"):
        value = brief.get(key)
        if value:
            out[key] = value
    must_include = brief.get("must_include_elements") or []
    if must_include:
        out["must_include_elements"] = must_include[:6]
    copy_forbidden = [
        str(item)
        for item in (brief.get("forbidden_visual_patterns") or [])
        if any(token in str(item).lower() for token in ("mot", "word", "copy", "hedging"))
    ]
    if copy_forbidden:
        out["copy_forbidden"] = copy_forbidden[:3]
    return {key: value for key, value in out.items() if value not in ("", [], None)}


def build_copy_prompt(
    *,
    plan: GSGPagePlan,
    brand_dna: dict[str, Any],
) -> str:
    """Build the bounded copy prompt."""
    is_listicle = plan.page_type == "lp_listicle"
    max_doctrine_criteria = 3 if is_listicle else 3
    max_doctrine_directives = 5 if is_listicle else 4
    max_allowed_facts = 1
    max_brand_chars = 560 if is_listicle else 440

    if is_listicle:
        schema_reason = {
            "heading": "string",
            "paragraphs": ["string", "string"],
            "side_note": "string|null",
        }
        schema = {
            "meta": {"title": "string", "description": "string"},
            "byline": {"author_name": "string", "author_role": "string", "date_label": "string"},
            "hero": {"eyebrow": "string", "h1": "string", "dek": "string"},
            "intro": ["string", "string"],
            "reasons": [schema_reason],
            "final_cta": {"heading": "string", "body": "string", "button_label": "string"},
            "footer": {"brand_line": "string"},
        }
        final_instruction = (
            "Return only JSON. The `reasons` array must contain exactly "
            f"{plan.pattern_pack.get('reason_count', 10)} items."
        )
    else:
        section_ids = [
            section.id for section in plan.sections
            if section.id not in {"hero", "final_cta", "footer", "byline"}
        ]
        schema = {
            "meta": {"title": "string", "description": "string"},
            "byline": {"author_name": "string", "author_role": "string", "date_label": "string"},
            "hero": {"eyebrow": "string", "h1": "string", "dek": "string"},
            "sections": {
                section_id: {
                    "heading": "string",
                    "body": "string",
                    "bullets": ["string", "string", "string"],
                    "microcopy": "string|null",
                }
                for section_id in section_ids
            },
            "final_cta": {"heading": "string", "body": "string", "button_label": "string"},
            "footer": {"brand_line": "string"},
        }
        final_instruction = (
            "Return only JSON. Required `sections` keys: "
            + ", ".join(section_ids)
            + "."
        )
    return "\n\n".join([
        format_plan_for_prompt(plan),
        format_context_pack_for_prompt(plan.context_pack),
        format_doctrine_pack_for_prompt(
            plan.doctrine_pack,
            max_criteria=max_doctrine_criteria,
            max_directives=max_doctrine_directives,
        ),
        format_visual_pack_for_prompt(plan.visual_intelligence),
        format_pattern_pack_for_prompt(plan.pattern_pack),
        format_minimal_constraints_block(plan.constraints, max_facts=max_allowed_facts),
        format_brand_block(brand_dna, max_chars=max_brand_chars),
        "## BRIEF\n" + json.dumps(_compact_brief_for_copy(plan.brief), ensure_ascii=False, separators=(",", ":")),
        "## JSON SHAPE REQUIRED\n" + json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
        final_instruction,
    ])
