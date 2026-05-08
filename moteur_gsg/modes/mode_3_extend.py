"""Mode 3 EXTEND V26.AD — concept nouveau pour client existant (~15-20% des cas).

Use case : Site existant a brand_dna mais le concept demandé n'existe pas dans
son écosystème (ex: advertorial alors que le client n'a fait que home/pdp).

Inputs :
  - client (slug) : doit avoir brand_dna
  - page_type : ex "advertorial", "lp_listicle"
  - concept : description courte du concept nouveau (1-2 phrases)
  - brief : BriefV2 OU dict legacy {objectif, audience, angle}

Pipeline V27 canonical :
  Délègue par défaut au Mode 1 minimal (`mode_1_complete`) en injectant le
  `concept` dans l'angle. L'ancien persona_narrator reste disponible en opt-in
  forensic via pipeline="persona_single_pass".

Coût attendu : ~$0.15-0.20 single_pass multimodal (vs $0.40-0.50 V26.AA legacy).
"""
from __future__ import annotations

from typing import Any, Optional, Union

from ..core.brief_v2 import BriefV2


def run_mode_3_extend(
    client: str,
    page_type: str,
    brief: Union[BriefV2, dict, None] = None,
    *,
    concept: Optional[str] = None,
    pipeline: str = "minimal_complete",
    fallback_page_for_vision: Optional[str] = None,
    forced_language: Optional[str] = None,
    **kwargs,
) -> dict:
    """Mode 3 EXTEND : nouveau concept pour client existant.

    Args:
      client: slug
      page_type: page_type cible (ex: "advertorial")
      brief: BriefV2 OU dict legacy. Si BriefV2, `concept` est lu depuis
             `brief.concept_description` si non fourni en kwarg.
      concept: description du concept nouveau (override BriefV2.concept_description)
      pipeline: "minimal_complete" (default canonique) | "persona_single_pass" (forensic)
      fallback_page_for_vision: si page_type pas capturé, screenshots d'une autre page
      forced_language: "FR"/"EN"/etc (override Sonnet vision bias)

    Returns: dict {html, audit, gen, ctx_summary, telemetry, concept, mode='extend', ...}
    """
    # Normalize brief : BriefV2 → legacy dict, ou dict tel quel
    legacy_brief = _to_legacy_brief(brief)

    # Concept fallback : kwarg > BriefV2.concept_description > brief.notes
    if not concept and isinstance(brief, BriefV2):
        concept = brief.concept_description
    if not concept:
        raise ValueError(
            "Mode 3 EXTEND requiert un `concept` (description du concept nouveau, ≥20 chars). "
            "Passer via kwarg `concept=...` ou via BriefV2.concept_description."
        )

    # Inject concept dans l'angle (persona_narrator format-aware basé sur page_type)
    enriched_angle = (
        f"CONCEPT NOUVEAU (Mode 3 EXTEND) : {concept}\n\n"
        f"{legacy_brief.get('angle') or ''}"
    ).strip()
    legacy_brief["angle"] = enriched_angle
    # Notes pour traçabilité downstream
    notes = legacy_brief.get("notes", "")
    legacy_brief["notes"] = (notes + "\n\n" if notes else "") + f"MODE 3 EXTEND : concept_description = {concept}"

    # Forced language : prefer kwarg > BriefV2.target_language
    if not forced_language and isinstance(brief, BriefV2):
        forced_language = brief.target_language

    if pipeline == "minimal_complete":
        from .mode_1_complete import run_mode_1_complete

        target_language = forced_language or kwargs.pop("target_language", "FR")
        kwargs.pop("target_language", None)
        result = run_mode_1_complete(
            client=client,
            page_type=page_type,
            brief=legacy_brief,
            target_language=target_language,
            **kwargs,
        )
    elif pipeline == "persona_single_pass":
        from .mode_1_persona_narrator import run_mode_1_persona_narrator

        result = run_mode_1_persona_narrator(
            client=client,
            page_type=page_type,
            brief=legacy_brief,
            fallback_page_for_vision=fallback_page_for_vision,
            forced_language=forced_language,
            **kwargs,
        )
    else:
        raise ValueError("Mode 3 pipeline must be 'minimal_complete' or 'persona_single_pass'")
    result["mode"] = "extend"
    result["concept"] = concept
    result["pipeline_used"] = pipeline
    return result


def _to_legacy_brief(brief: Union[BriefV2, dict, None]) -> dict:
    if brief is None:
        return {"objectif": "", "audience": "", "angle": "", "notes": ""}
    if isinstance(brief, BriefV2):
        return brief.to_legacy_brief()
    if isinstance(brief, dict):
        # ensure required keys present
        return {
            "objectif": brief.get("objectif") or brief.get("objective") or "",
            "audience": brief.get("audience") or "",
            "angle": brief.get("angle") or "",
            "notes": brief.get("notes") or "",
        }
    raise TypeError(f"brief must be BriefV2 | dict | None, got {type(brief).__name__}")
