"""Mode 4 ELEVATE V26.AD — challenger DA via inspirations URLs (~5-10% des cas).

Use case : Client veut alternative encore plus quali en proposant URLs
d'inspirations supplémentaires (ex: "fais-moi du Linear/Stripe sur ma marque").

Inputs :
  - client (slug)
  - page_type
  - inspiration_urls : list[str] (1-5 URLs marques de référence)
  - brief : BriefV2 OU dict legacy

Pipeline V27 canonical :
  Délègue par défaut au Mode 1 minimal (`mode_1_complete`) en injectant
  `inspiration_urls` + raisons dans l'angle. L'ancien persona_narrator reste
  disponible en opt-in forensic via pipeline="persona_single_pass".

Future Sprint J+ : `brand_dna_extractor(inspiration_urls)` pour extraire
les patterns visuels à fusionner via creative_director Bold + best_of_n 3 routes.

Coût attendu : ~$0.15-0.20 single_pass V1 (V26.AD) / ~$1.50-2.00 best_of_n V2 (post-Sprint J).
"""
from __future__ import annotations

from typing import Optional, Union

from ..core.brief_v2 import BriefV2


def run_mode_4_elevate(
    client: str,
    page_type: str,
    brief: Union[BriefV2, dict, None] = None,
    *,
    inspiration_urls: Optional[list[str]] = None,
    inspiration_reasons: Optional[str] = None,
    pipeline: str = "minimal_complete",
    fallback_page_for_vision: Optional[str] = None,
    forced_language: Optional[str] = None,
    **kwargs,
) -> dict:
    """Mode 4 ELEVATE : challenger DA via URLs inspirations.

    Args:
      client: slug
      page_type: ex "lp_listicle"
      brief: BriefV2 OU dict legacy. Si BriefV2, `inspiration_urls` lu depuis
             brief.inspiration_urls si non fourni en kwarg.
      inspiration_urls: 1-5 URLs (override BriefV2.inspiration_urls)
      inspiration_reasons: pourquoi ces réfs ? (signature / ton / structure)
      pipeline: "minimal_complete" (default canonique) | "persona_single_pass" (forensic)
      forced_language: override langue

    Returns: dict {html, audit, gen, ctx_summary, telemetry, inspiration_urls, mode='elevate'}
    """
    # Normalize brief
    legacy_brief = _to_legacy_brief(brief)

    # Inspirations fallback : kwarg > BriefV2.inspiration_urls
    if not inspiration_urls and isinstance(brief, BriefV2):
        inspiration_urls = brief.inspiration_urls
    if not inspiration_reasons and isinstance(brief, BriefV2):
        inspiration_reasons = brief.inspiration_reasons

    if not inspiration_urls:
        raise ValueError(
            "Mode 4 ELEVATE requiert `inspiration_urls` (≥1 URL marque de référence). "
            "Passer via kwarg ou via BriefV2.inspiration_urls."
        )
    if len(inspiration_urls) > 5:
        raise ValueError(f"inspiration_urls trop nombreuses ({len(inspiration_urls)} > 5)")

    # Inject inspirations dans angle
    urls_block = "\n  - ".join(inspiration_urls)
    inspiration_block = (
        f"INSPIRATIONS (Mode 4 ELEVATE) — études de référence à imiter en signature éditoriale :\n"
        f"  - {urls_block}"
    )
    if inspiration_reasons:
        inspiration_block += f"\nPourquoi ces réfs : {inspiration_reasons}"
    inspiration_block += (
        "\nNote : la palette/typo restent celles de TA marque (AURA tokens). "
        "Les inspirations guident le ton, la structure éditoriale, et le niveau de polish."
    )

    enriched_angle = (
        f"{inspiration_block}\n\n{legacy_brief.get('angle') or ''}"
    ).strip()
    legacy_brief["angle"] = enriched_angle
    notes = legacy_brief.get("notes", "")
    legacy_brief["notes"] = (notes + "\n\n" if notes else "") + f"MODE 4 ELEVATE : {len(inspiration_urls)} inspiration_urls"

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
        raise ValueError("Mode 4 pipeline must be 'minimal_complete' or 'persona_single_pass'")
    result["mode"] = "elevate"
    result["inspiration_urls"] = list(inspiration_urls)
    result["inspiration_reasons"] = inspiration_reasons
    result["pipeline_used"] = pipeline
    return result


def _to_legacy_brief(brief: Union[BriefV2, dict, None]) -> dict:
    if brief is None:
        return {"objectif": "", "audience": "", "angle": "", "notes": ""}
    if isinstance(brief, BriefV2):
        return brief.to_legacy_brief()
    if isinstance(brief, dict):
        return {
            "objectif": brief.get("objectif") or brief.get("objective") or "",
            "audience": brief.get("audience") or "",
            "angle": brief.get("angle") or "",
            "notes": brief.get("notes") or "",
        }
    raise TypeError(f"brief must be BriefV2 | dict | None, got {type(brief).__name__}")
