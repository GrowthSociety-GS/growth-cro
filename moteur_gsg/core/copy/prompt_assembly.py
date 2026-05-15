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
- The renderer owns layout. Do not mention layout instructions in copy.
- CRITICAL : if the schema includes optional top-level keys (`comparison`, `testimonials`, `faq`), you MUST populate them as separate sections. NEVER fold testimonials, comparison rows, or FAQ Q&A into the body of a reason — they must live in their dedicated top-level keys with their own structure.
- For `testimonials.items[]` : reproduce EXACTLY the testimonials from the brief field `testimonials` (name + position + company + quote verbatim). Never paraphrase the quote, never invent a stat_highlight beyond what is in the brief's sourced_numbers context for that company.
- For `comparison.rows[]` : derive each row from the brief's sourced_numbers + the angle (e.g. "Sans Weglot" vs "Avec Weglot" on 4-6 dimensions like time-to-market, cost, SEO, quality, maintenance).
- For `faq.items[]` : write exactly 5 Q&A. Default topics for SaaS lp_listicle : pricing/cost, integrations, SEO impact, AI translation quality, free trial. Each answer 2-4 sentences, factual, sourced."""

COPY_PROMPT_MAX_CHARS = 16000


def _compact_text(value: Any, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:max_chars]


def _compact_brief_for_copy(brief: dict[str, Any]) -> dict[str, Any]:
    """Keep copy-critical brief fields without dumping the full intake object.

    Sprint 13 / V27.2-G+ — additionally preserve :
      - `testimonials[]` (named items must be reproduced verbatim, not invented)
      - `sourced_numbers[]` (only these numbers may appear in copy)
      - `concept_description` (the LP-Creator structured plan)
      - `anti_references[]` (patterns to actively avoid)
    """
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

    # Sprint 13 — preserve testimonials verbatim (anti-invention)
    testimonials = brief.get("testimonials") or []
    if testimonials:
        out["testimonials"] = [
            {
                "name": _compact_text(t.get("name"), 60),
                "position": _compact_text(t.get("position"), 60),
                "company": _compact_text(t.get("company"), 60),
                "quote": _compact_text(t.get("quote"), 320),
            }
            for t in testimonials[:3]
            if isinstance(t, dict)
        ]

    # Sprint 13 — preserve sourced_numbers (only allowed facts)
    sourced_numbers = brief.get("sourced_numbers") or []
    if sourced_numbers:
        out["sourced_numbers"] = [
            {
                "number": _compact_text(sn.get("number"), 40),
                "context": _compact_text(sn.get("context"), 120),
            }
            for sn in sourced_numbers[:10]
            if isinstance(sn, dict)
        ]

    # Sprint 13 — preserve concept_description (LP-Creator structured plan)
    concept = brief.get("concept_description")
    if concept:
        out["concept_description"] = _compact_text(concept, 800)

    # Sprint 13 — preserve anti_references (active avoidance)
    anti_refs = brief.get("anti_references") or []
    if anti_refs:
        out["anti_references"] = [_compact_text(x, 160) for x in anti_refs[:4]]

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
        # Sprint 13 / V27.2-G+ — extend schema for optional rich sections
        section_ids_set = {s.id for s in plan.sections}
        extra_required_keys: list[str] = []
        if "comparison" in section_ids_set:
            schema["comparison"] = {
                "heading": "string",
                "subtitle": "string|null",
                "without_label": "string (column header, max 32 chars, e.g. 'Sans Weglot')",
                "with_label": "string (column header, max 32 chars, e.g. 'Avec Weglot')",
                "rows": [
                    {"dimension": "string", "without": "string", "with": "string"}
                ],
            }
            extra_required_keys.append(
                "`comparison.rows` must contain 4-6 rows, each with {dimension, without, with} — use only sourced facts"
            )
        if "testimonials" in section_ids_set:
            schema["testimonials"] = {
                "heading": "string|null",
                "items": [
                    {"name": "string", "position": "string", "company": "string", "quote": "string", "stat_highlight": "string|null"}
                ],
            }
            extra_required_keys.append(
                "`testimonials.items` must REPRODUCE EXACTLY the testimonials from the BRIEF — never invent names/quotes. The brief contains the canonical list."
            )
        if "faq" in section_ids_set:
            schema["faq"] = {
                "heading": "string|null",
                "items": [{"question": "string", "answer": "string"}],
            }
            extra_required_keys.append(
                "`faq.items` must contain exactly 5 Q&A pairs covering : pricing/cost, integrations/compatibility, SEO, AI translation quality, free trial. Answers 2-4 sentences max."
            )

        final_instruction = (
            "Return only JSON. The `reasons` array must contain exactly "
            f"{plan.pattern_pack.get('reason_count', 10)} items."
        )
        if extra_required_keys:
            final_instruction += "\n" + "\n".join(f"- {req}" for req in extra_required_keys)
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
