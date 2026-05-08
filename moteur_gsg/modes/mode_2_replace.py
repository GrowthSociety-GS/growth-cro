"""Mode 2 REPLACE V26.AD — refonte d'une page existante avec audit comparatif.

Use case (~25-30% des cas business) :
  Le client a une page existante audité (V26 pipeline). Il veut une refonte
  qui CORRIGE les gaps audit et atteint une cible quality.

Inputs :
  - client (slug) : doit avoir brand_dna + audit V26 complet sur page_to_replace
  - page_type : ex "lp_listicle", "home", "pdp"
  - brief : BriefV2 OU dict legacy (objectif, audience, angle)

Pipeline V26.AD :
  Délègue persona_narrator (V26.AC : router racine + multimodal + AURA CSS +
  post-gates), MAIS enrichi avec :
    1. Brief V15 §1-§8 construit depuis recos audit V26
    2. Recos hint block déjà injecté par persona_narrator via router racine
    3. Audit comparatif before/after (delta scores doctrine V3.2.1)

Sprint Mode 2 V26.AD : single_pass persona_narrator. Si <85% Excellent, fallback
prévu (Sprint J+) → pipeline_sequential_4_stages dédié.

Coût attendu : ~$0.15-0.20 single_pass + audit (~$0.30-0.50 si skip_judges=False).
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Optional, Union

from ..core.brand_intelligence import has_brand_dna
from ..core.brief_v15_builder import build_brief_v15, save_brief_v15
from ..core.brief_v2 import BriefV2

ROOT = pathlib.Path(__file__).resolve().parents[2]


def run_mode_2_replace(
    client: str,
    page_type: str,
    brief: Union[BriefV2, dict, None] = None,
    *,
    target_score_pct: float = 85.0,
    pipeline: str = "persona_single_pass",  # V26.AD : persona_narrator V26.AC default. sequential_4_stages WIP Sprint J+.
    fallback_page_for_vision: Optional[str] = None,
    forced_language: Optional[str] = None,
    apply_fixes: bool = True,
    apply_post_gates: bool = True,
    skip_judges: bool = False,  # Mode 2 produit audit comparatif → judges utiles par défaut
    save_html_path: Optional[str] = None,
    save_audit_path: Optional[str] = None,
    save_brief_path: Optional[str] = None,
    verbose: bool = True,
) -> dict:
    """Pipeline Mode 2 REPLACE V26.AD.

    Args:
      client: slug — doit avoir brand_dna + audit V26 sur page_type
      page_type: page à refondre (doit avoir score_page_type + recos enrichies)
      brief: BriefV2 OU dict legacy. Si None, brief sera dérivé du Brief V15.
      target_score_pct: cible Mode 2 (default 85% Excellent)
      pipeline: "persona_single_pass" (V26.AD default) | "sequential_4_stages" (Sprint J+ WIP)
      forced_language: override langue Sonnet (sinon depuis BriefV2.target_language)

    Returns: dict {html, audit, before_audit_summary, delta_pct, brief_v15, gen, telemetry, mode='replace'}

    Raises:
      ValueError si artefacts manquants (brand_dna, score, recos)
    """
    if not has_brand_dna(client):
        raise ValueError(f"❌ brand_dna manquant pour {client} — Mode 2 REPLACE requiert brand_dna + audit V26")

    score_fp = ROOT / "data" / "captures" / client / page_type / "score_page_type.json"
    if not score_fp.exists():
        raise ValueError(f"❌ Mode 2 REPLACE requiert audit V26 sur {client}/{page_type} : {score_fp} manquant")
    recos_fp = None
    for candidate in ("recos_v13_final.json", "recos_v13_api.json", "recos_enriched.json"):
        cfp = ROOT / "data" / "captures" / client / page_type / candidate
        if cfp.exists():
            recos_fp = cfp
            break
    if recos_fp is None:
        raise ValueError(f"❌ Mode 2 REPLACE requiert recos enrichies dans {client}/{page_type}")

    if pipeline == "sequential_4_stages":
        raise NotImplementedError(
            "pipeline='sequential_4_stages' n'est pas encore branché V26.AD. "
            "Utiliser pipeline='persona_single_pass' (default) pour l'instant. "
            "Sprint J+ ajoutera le sequential si le single_pass V26.AC ne suffit pas pour ≥85%."
        )

    if verbose:
        print(f"\n══ Mode 2 REPLACE V26.AD — {client} / {page_type} ══")

    grand_t0 = time.time()
    before_audit = json.loads(score_fp.read_text())
    before_score_pct = (before_audit.get("aggregate") or {}).get("score100")

    if verbose:
        print(f"  Score actuel : {before_score_pct}% / Cible : {target_score_pct}%")

    # ── 1. Construire Brief V15 §1-§8 (réutilisé pour traçabilité + future seq pipeline) ──
    brief_v15 = build_brief_v15(
        client=client, page_type=page_type,
        target_score_pct=target_score_pct,
        pipeline_recommended=pipeline,
        creative_route="premium",
    )
    if save_brief_path:
        save_brief_v15(brief_v15, pathlib.Path(save_brief_path))
        if verbose:
            print(f"  ✓ Brief V15 saved : {save_brief_path}")

    # ── 2. Build legacy brief enrichi avec gaps audit ──
    legacy_brief = _to_legacy_brief(brief)
    section_3 = brief_v15.get("section_3_audience", {})
    section_8 = brief_v15.get("section_8_directives_mode_2", {})

    if not legacy_brief["objectif"]:
        legacy_brief["objectif"] = (
            f"REFONTE Mode 2 — corriger les gaps audit pour atteindre score ≥{target_score_pct}%"
        )
    if not legacy_brief["audience"]:
        legacy_brief["audience"] = (
            f"Persona: {section_3.get('primary_intent', '?')}. "
            f"Schwartz awareness: {section_3.get('schwartz_awareness', '?')}. "
            f"Objections principales: {', '.join(section_3.get('objections', [])[:3]) or '?'}. "
            f"Brief V15 §3 disponible — utilise-le pour adresser leurs peurs/désirs."
        )
    if not legacy_brief["angle"]:
        legacy_brief["angle"] = (
            f"Refonte premium ciblée — score actuel {before_score_pct}% → cible {target_score_pct}%. "
            f"Doit corriger les top critères CRITICAL identifiés en audit V26."
        )
    notes_lines = [
        legacy_brief.get("notes", ""),
        f"PAGE_TO_REPLACE_URL : {section_8.get('page_to_replace_url', '?')}",
        f"SCORE_BEFORE : {before_score_pct}%",
        f"TARGET : {target_score_pct}%",
        "DOIT corriger TOUS les critères CRITICAL identifiés en audit V26.",
        "Recos V13 enrichies disponibles via router racine — utilise-les comme contraintes constructives.",
    ]
    legacy_brief["notes"] = "\n  ".join([l for l in notes_lines if l])

    if verbose:
        print(f"  ✓ Brief enrichi : objectif='{legacy_brief['objectif'][:70]}...'")

    # ── 3. Délègue persona_narrator V26.AC ──
    if not forced_language and isinstance(brief, BriefV2):
        forced_language = brief.target_language

    from .mode_1_persona_narrator import run_mode_1_persona_narrator
    result = run_mode_1_persona_narrator(
        client=client,
        page_type=page_type,
        brief=legacy_brief,
        fallback_page_for_vision=fallback_page_for_vision,
        forced_language=forced_language,
        apply_fixes=apply_fixes,
        apply_post_gates=apply_post_gates,
        skip_judges=skip_judges,
        save_html_path=save_html_path,
        save_audit_path=save_audit_path,
        verbose=verbose,
    )

    # ── 4. Audit comparatif before/after ──
    after_audit = result.get("audit", {})
    after_score_pct = None
    if after_audit:
        # persona_narrator audit_doctrine_info_only → totals.total_pct
        totals = after_audit.get("totals", {})
        after_score_pct = totals.get("total_pct") or totals.get("score100")
    delta = (after_score_pct - before_score_pct) if (after_score_pct is not None and before_score_pct is not None) else None

    if verbose:
        print(f"\n══ Mode 2 REPLACE — DELTA AUDIT ══")
        print(f"  Score AVANT (page existante) : {before_score_pct}%")
        print(f"  Score APRÈS (refonte V26.AD) : {after_score_pct}%" if after_score_pct is not None else "  Score APRÈS : (skip_judges=True, audit non calculé)")
        if delta is not None:
            print(f"  DELTA : {delta:+.1f}pp")
            if delta < 0:
                print(f"  ⚠️ Régression — la refonte score MOINS que l'original. À investiguer.")
            elif after_score_pct < target_score_pct:
                print(f"  ⚠️ Sous la cible {target_score_pct}% — pipeline sequential_4_stages recommandé (Sprint J+).")

    grand_dt = time.time() - grand_t0
    return {
        "html": result.get("html"),
        "audit": after_audit,
        "before_audit_summary": {
            "score_pct": before_score_pct,
            "tier": _tier_from_pct(before_score_pct or 0),
        },
        "delta_pct": delta,
        "brief_v15": brief_v15,
        "gen": result.get("gen"),
        "post_gate_violations": result.get("post_gate_violations"),
        "ctx_summary": result.get("ctx_summary"),
        "founder_persona_used": result.get("founder_persona_used"),
        "telemetry": {
            **(result.get("telemetry", {})),
            "wall_total_mode_2": round(grand_dt, 1),
        },
        "client": client,
        "page_type": page_type,
        "mode": "replace",
        "pipeline_used": pipeline,
        "version": "V26.AD.sprint_ad1",
    }


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


def _tier_from_pct(pct: float) -> str:
    if pct >= 85: return "Exceptionnel"
    if pct >= 75: return "Excellent"
    if pct >= 65: return "Bon"
    return "Insuffisant"
