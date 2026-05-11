"""Bounded copy writer for the canonical GSG.

The LLM writes JSON copy slots only. It does not decide layout and it does not
emit HTML. The renderer owns structure and implementation.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from .brand_intelligence import format_brand_block
from .context_pack import format_context_pack_for_prompt
from .doctrine_planner import format_doctrine_pack_for_prompt
from .minimal_guards import format_minimal_constraints_block
from .pattern_library import format_pattern_pack_for_prompt
from .planner import GSGPagePlan, format_plan_for_prompt
from growthcro.lib.anthropic_client import get_anthropic_client
from .pipeline_single_pass import SONNET_MODEL
from .visual_intelligence import format_visual_pack_for_prompt


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

COPY_PROMPT_MAX_CHARS = 8000


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_json(raw: str) -> dict[str, Any]:
    text = _strip_json_fences(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


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


def fallback_copy_from_plan(plan: GSGPagePlan) -> dict[str, Any]:
    """Deterministic fallback copy so the renderer can be smoke-tested without LLM."""
    objective = plan.brief.get("objectif") or plan.brief.get("objective") or "Transformer l'intention en action"
    audience = plan.brief.get("audience") or "equipes growth et produit"
    angle = plan.brief.get("angle") or "un angle editorial concret"
    cta = plan.constraints.get("primary_cta_label") or "Demarrer"
    if plan.page_type != "lp_listicle":
        page_label = plan.page_type.replace("_", " ")
        sections: dict[str, dict[str, Any]] = {}
        for section in plan.sections:
            if section.id in {"hero", "final_cta", "footer", "byline"}:
                continue
            sections[section.id] = {
                "heading": section.label,
                "body": (
                    f"{section.intent} Cette partie aide l'audience a avancer vers "
                    f"l'objectif suivant : {objective}."
                ),
                "bullets": [
                    "Promesse lisible des les premiers instants.",
                    "Preuves utilisees seulement quand elles sont disponibles.",
                    "Un CTA principal garde en fil conducteur.",
                ],
                "microcopy": section.kind,
            }
        return {
            "meta": {
                "title": f"{plan.client} — {page_label}",
                "description": f"{objective}. Page controlee pour {audience}.",
            },
            "byline": {
                "author_name": "GrowthCRO",
                "author_role": "Editorial desk",
                "date_label": "Lecture terrain",
            },
            "hero": {
                "eyebrow": plan.layout_name.replace("_", " "),
                "h1": f"{plan.client}: une page {page_label} plus claire",
                "dek": f"{angle}. Le parcours clarifie la promesse, les preuves et la prochaine action sans multiplier les chemins.",
            },
            "sections": sections,
            "final_cta": {
                "heading": "Une seule prochaine action, clairement assumee.",
                "body": "La page garde une promesse, des preuves et un CTA principal jusqu'au bout.",
                "button_label": cta,
            },
            "footer": {"brand_line": f"{plan.client} x GrowthCRO"},
        }
    count = int(plan.pattern_pack.get("reason_count") or 10)
    return {
        "meta": {
            "title": f"{count} raisons de repenser votre landing page",
            "description": f"{objective}. Une lecture pour {audience}.",
        },
        "byline": {
            "author_name": "Growth Society Research",
            "author_role": "CRO editorial desk",
            "date_label": "Lecture terrain",
        },
        "hero": {
            "eyebrow": "GrowthCRO Field Notes",
            "h1": f"{count} raisons de regarder {plan.client} autrement",
            "dek": f"{angle}. La page avance par preuves, objections et exemples utiles, sans forcer la conversion trop tot.",
        },
        "intro": [
            f"Le sujet n'est pas d'ajouter une page de plus. Il s'agit d'aider {audience} a comprendre pourquoi cette decision compte maintenant.",
            "Le parcours prend le temps d'installer une these claire, de separer les raisons, puis de reserver l'appel a l'action au moment ou il devient naturel.",
        ],
        "reasons": [
            {
                "heading": f"Raison {i}: une decision plus lisible",
                "paragraphs": [
                    "Chaque section isole une tension precise au lieu d'empiler des promesses generiques.",
                    "Le lecteur peut scanner, s'arreter, puis reprendre sans perdre le fil de l'argument.",
                ],
                "side_note": None if i % 3 else "La clarte gagne quand chaque preuve garde sa source et son contexte.",
            }
            for i in range(1, count + 1)
        ],
        "final_cta": {
            "heading": "Quand le raisonnement est clair, l'action devient simple.",
            "body": "Le CTA arrive apres la preuve, pas avant. Il conclut le parcours sans forcer la main.",
            "button_label": cta,
        },
        "footer": {"brand_line": f"{plan.client} x GrowthCRO"},
    }


def call_copy_llm(
    *,
    plan: GSGPagePlan,
    brand_dna: dict[str, Any],
    model: str = SONNET_MODEL,
    max_tokens: int = 5000,
    temperature: float = 0.45,
    verbose: bool = True,
) -> dict[str, Any]:
    """Generate bounded copy JSON from the deterministic page plan."""
    prompt = build_copy_prompt(plan=plan, brand_dna=brand_dna)
    if len(prompt) > COPY_PROMPT_MAX_CHARS:
        raise ValueError(
            f"copy prompt too large ({len(prompt)} chars > {COPY_PROMPT_MAX_CHARS}). "
            "Compact upstream context instead of running a mega-prompt."
        )
    api = get_anthropic_client()
    if verbose:
        print(f"  -> Sonnet copy slots (prompt={len(prompt)} chars, max_tokens={max_tokens}, T={temperature})...", flush=True)

    def _call(user_prompt: str, temp: float, tokens: int):
        t_start = time.time()
        message = api.messages.create(
            model=model,
            max_tokens=tokens,
            temperature=temp,
            system=COPY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message, time.time() - t_start

    t0 = time.time()
    msg, dt_first = _call(prompt, temperature, max_tokens)
    raw = msg.content[0].text
    tokens_in = msg.usage.input_tokens
    tokens_out = msg.usage.output_tokens
    retry_count = 0

    try:
        copy_doc = _parse_json(raw)
    except Exception as parse_error:
        retry_count = 1
        if verbose:
            print(f"  ! copy JSON parse failed, retry strict JSON: {parse_error}", flush=True)
        retry_prompt = (
            prompt
            + "\n\n## RETRY JSON STRICT\n"
            "Your previous answer was invalid JSON. Return MINIFIED valid JSON only. "
            "No markdown, no comments, no trailing commas, no unescaped line breaks inside strings. "
            "Keep each paragraph as a short string. The root object must start with { and end with }."
        )
        msg2, dt_second = _call(retry_prompt, 0.15, max_tokens)
        raw = msg2.content[0].text
        tokens_in += msg2.usage.input_tokens
        tokens_out += msg2.usage.output_tokens
        copy_doc = _parse_json(raw)
        dt_first += dt_second

    dt = time.time() - t0
    if verbose:
        print(f"  <- Sonnet copy slots: in={tokens_in} out={tokens_out} retries={retry_count} ({dt:.1f}s)", flush=True)
    return {
        "copy": normalize_copy_doc(copy_doc, plan),
        "raw": raw,
        "prompt_chars": len(prompt),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "wall_seconds": round(dt, 1),
        "model": model,
        "retries": retry_count,
    }


def normalize_copy_doc(copy_doc: dict[str, Any], plan: GSGPagePlan) -> dict[str, Any]:
    """Normalize LLM copy JSON to the renderer contract."""
    fallback = fallback_copy_from_plan(plan)
    if not isinstance(copy_doc, dict):
        return fallback

    out = fallback
    for key in ("meta", "byline", "hero", "final_cta", "footer"):
        if isinstance(copy_doc.get(key), dict):
            out[key].update({k: v for k, v in copy_doc[key].items() if isinstance(v, str)})
    if plan.page_type != "lp_listicle":
        if isinstance(copy_doc.get("sections"), dict):
            for section_id, section_copy in copy_doc["sections"].items():
                if not isinstance(section_copy, dict):
                    continue
                target = out.setdefault("sections", {}).setdefault(str(section_id), {})
                for key in ("heading", "body", "microcopy"):
                    if isinstance(section_copy.get(key), str):
                        target[key] = section_copy[key].strip()
                if isinstance(section_copy.get("bullets"), list):
                    target["bullets"] = [
                        str(item).strip()
                        for item in section_copy["bullets"]
                        if isinstance(item, str) and item.strip()
                    ][:4]
        out["final_cta"]["button_label"] = plan.constraints.get("primary_cta_label") or out["final_cta"]["button_label"]
        return out

    if isinstance(copy_doc.get("intro"), list):
        intro = [str(x) for x in copy_doc["intro"] if isinstance(x, str) and x.strip()]
        if intro:
            out["intro"] = (intro + fallback["intro"])[:2]

    count = int(plan.pattern_pack.get("reason_count") or 10)
    reasons = []
    if isinstance(copy_doc.get("reasons"), list):
        for item in copy_doc["reasons"][:count]:
            if not isinstance(item, dict):
                continue
            paragraphs = item.get("paragraphs")
            if isinstance(paragraphs, str):
                paragraphs = [paragraphs]
            if not isinstance(paragraphs, list):
                paragraphs = []
            reasons.append({
                "heading": str(item.get("heading") or "").strip() or f"Raison {len(reasons)+1}",
                "paragraphs": [str(p).strip() for p in paragraphs if isinstance(p, str) and p.strip()][:3],
                "side_note": str(item.get("side_note")).strip() if item.get("side_note") else None,
            })
    out["reasons"] = (reasons + fallback["reasons"])[:count]
    out["final_cta"]["button_label"] = plan.constraints.get("primary_cta_label") or out["final_cta"]["button_label"]
    return out
