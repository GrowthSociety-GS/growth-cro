"""Mode 5 GENESIS V26.AD — brief seul sans URL existante (<5% des cas).

Use case : Nouvelle brand sans site live. Brief 8-12 questions structurées
+ uploads assets éventuels.

Inputs (brief OU BriefV2 legacy mapping) :
  - brand_name, category, audience, offer, cta_type, proofs, niveau_visuel,
    voice_tone, palette_preference (REQUIRED)
  - voice_signature, optional fields (palette hex, fonts override)

Pipeline V26.AD :
  1. Construire pseudo-brand_dna in-line depuis le brief (so persona_narrator
     loadclient_context() ne plante pas)
  2. Déléguer à `mode_1_persona_narrator` en mode "no client" — Sonnet construit
     le founder narrative depuis les 8-12 réponses brief.
  3. Pas de screenshots vision multimodal (no client URL = no captures)

Coût attendu : ~$0.15-0.20 single_pass V1 (V26.AD) / ~$1.50 best_of_n V2 (Sprint J+).

NOTE V26.AD : pseudo-brand_dna minimal. Sprint J+ remplacera par appel Sonnet
qui génère un brand_dna structuré complet depuis les 8-12 réponses.
"""
from __future__ import annotations

import json
import pathlib
from typing import Optional, Union

from ..core.brief_v2 import BriefV2

ROOT = pathlib.Path(__file__).resolve().parents[2]


REQUIRED_BRIEF_FIELDS_MODE_5 = [
    "brand_name", "category", "audience", "offer", "cta_type",
    "proofs", "niveau_visuel", "voice_tone", "palette_preference",
]


def run_mode_5_genesis(
    client: Optional[str],
    page_type: str,
    brief: Union[BriefV2, dict, None] = None,
    *,
    fallback_page_for_vision: Optional[str] = None,
    forced_language: Optional[str] = None,
    **kwargs,
) -> dict:
    """Mode 5 GENESIS : brief seul, pas de brand_dna existant.

    V26.AD : délègue persona_narrator (vs V26.AA legacy_complete). Construit
    pseudo-brand_dna in-line. Pas de vision input (no captures).

    Args:
      client: optional slug. Si None, généré depuis brand_name.
      page_type: ex "lp_sales", "home"
      brief: BriefV2 OU dict avec REQUIRED_BRIEF_FIELDS_MODE_5

    Raises:
      ValueError si champs brief manquants.
    """
    from .mode_1_persona_narrator import run_mode_1_persona_narrator

    # Extract brief en dict-like (BriefV2 has limited fields, GENESIS dict has many extras)
    brief_dict = _normalize_genesis_brief(brief)

    # Validate REQUIRED fields for Mode 5 GENESIS
    missing = [f for f in REQUIRED_BRIEF_FIELDS_MODE_5 if not brief_dict.get(f)]
    if missing:
        raise ValueError(
            f"❌ Mode 5 GENESIS requiert champs brief : {missing}. "
            f"Mode 5 est pour nouvelle brand sans URL — toutes les infos doivent venir du brief."
        )

    # Slug fallback depuis brand_name
    if not client:
        client = brief_dict["brand_name"].lower().replace(" ", "_").replace("-", "_")[:30]

    # Construire pseudo-brand_dna in-line (so persona_narrator router ne plante pas)
    pseudo_brand_dna_path = _build_pseudo_brand_dna(client, brief_dict)

    # Build legacy brief pour persona_narrator
    legacy_brief = {
        "objectif": brief_dict.get("objectif") or brief_dict.get("objective")
                    or f"Lancer la nouvelle brand {brief_dict['brand_name']} avec une LP {page_type}",
        "audience": brief_dict.get("audience", ""),
        "angle": (
            f"GENESIS Mode 5 — création from scratch. "
            f"Voice tone : {brief_dict.get('voice_tone', '?')}. "
            f"Niveau visuel : {brief_dict.get('niveau_visuel', '?')}. "
            f"{brief_dict.get('angle', '')}"
        ),
        "notes": (
            f"MODE 5 GENESIS — pseudo brand_dna généré in-line.\n"
            f"BRAND_NAME : {brief_dict['brand_name']}\n"
            f"CATEGORY : {brief_dict.get('category')}\n"
            f"OFFER : {brief_dict.get('offer')}\n"
            f"CTA_TYPE : {brief_dict.get('cta_type')}\n"
            f"PROOFS_AVAILABLE : {brief_dict.get('proofs')}\n"
            f"VOICE_TONE : {brief_dict.get('voice_tone')}\n"
            f"PALETTE_PREFERENCE : {brief_dict.get('palette_preference')}\n"
        ),
    }

    if not forced_language and isinstance(brief, BriefV2):
        forced_language = brief.target_language

    # No vision images possibles (pas de captures pour pseudo-client)
    result = run_mode_1_persona_narrator(
        client=client,
        page_type=page_type,
        brief=legacy_brief,
        fallback_page_for_vision=fallback_page_for_vision,
        forced_language=forced_language,
        **kwargs,
    )
    result["mode"] = "genesis"
    result["pseudo_brand_dna_path"] = str(pseudo_brand_dna_path)
    return result


def _normalize_genesis_brief(brief: Union[BriefV2, dict, None]) -> dict:
    """Normalise un BriefV2/dict en dict GENESIS-compatible.

    Mode 5 a des fields spécifiques (brand_name, category, ...) qui ne sont
    pas dans BriefV2 standard. On suppose qu'ils sont passés en dict raw, ou
    en BriefV2 avec les fields packés dans `desired_signature` / `must_include_elements`
    / etc.
    """
    if brief is None:
        return {}
    if isinstance(brief, dict):
        return dict(brief)
    if isinstance(brief, BriefV2):
        # Mapping BriefV2 → GENESIS dict (best effort)
        d = brief.to_dict()
        # Augmente avec les champs natifs BriefV2 mappables
        d.setdefault("audience", brief.audience)
        d.setdefault("objectif", brief.objective)
        d.setdefault("angle", brief.angle)
        d.setdefault("voice_tone", brief.desired_signature or "")
        d.setdefault("niveau_visuel", brief.desired_emotion or "")
        return d
    raise TypeError(f"brief must be BriefV2 | dict | None, got {type(brief).__name__}")


def _build_pseudo_brand_dna(client: str, brief: dict) -> pathlib.Path:
    """Construit un pseudo-brand_dna.json depuis le brief 8-12 questions.

    V26.AD V1 : minimal (pour que load_brand_dna() ne renvoie pas vide).
    Sprint J+ : appel Sonnet pour générer un brand_dna structuré complet.
    """
    capture_dir = ROOT / "data" / "captures" / client
    capture_dir.mkdir(parents=True, exist_ok=True)

    # Palette : si brief.palette_preference est dict {primary, secondary}, garder
    palette = brief.get("palette_preference", {})
    if isinstance(palette, str):
        palette = {"primary": palette}

    pseudo = {
        "client": client,
        "home_url": None,
        "version": "v29-genesis-mode-5-v26ad",
        "visual_tokens": {
            "colors": palette,
            "typography": {
                "h1": {"family": brief.get("font_override", "Inter")},
                "body": {"family": brief.get("font_override", "Inter")},
            },
        },
        "voice_tokens": {
            "tone": [brief.get("voice_tone", "neutral")],
            "voice_signature_phrase": brief.get("voice_signature", ""),
        },
        "method": "mode_5_genesis_brief_only",
        "_genesis_brief": brief,
    }

    fp = capture_dir / "brand_dna.json"
    fp.write_text(json.dumps(pseudo, ensure_ascii=False, indent=2))
    return fp
