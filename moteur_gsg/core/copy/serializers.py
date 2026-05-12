"""Copy serializers — dict transforms for the bounded GSG copy writer.

Concern axis: I/O serialization (axis 8).

Pure dict-in / dict-out helpers:
- `fallback_copy_from_plan` builds a deterministic copy doc from the page plan
  so the renderer can be smoke-tested without an LLM round-trip.
- `normalize_copy_doc` reconciles an LLM-returned dict against the renderer
  contract, filling missing keys from the fallback and stripping invalid types.

No LLM calls, no prompt assembly, no I/O — just dict transformations.
"""
from __future__ import annotations

from typing import Any

from moteur_gsg.core.planner import GSGPagePlan


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
