"""Brief V15 Builder V26.AA Sprint B (skeleton, full impl Sprint C).

Trou architectural identifié : pas de format Brief formalisé entre l'audit V26
et le GSG Mode 2 REPLACE. Ce module va combler le trou.

Sprint B = SKELETON (signatures + structure, pas de logique complexe).
Sprint C = FULL IMPL (consume score_page_type + recos_v13_api + brand_dna +
client_intent → dict §1-§8 structuré pour Mode 2).

Référence : `skills/audit-bridge-to-gsg/SKILL.md` §B (structure Brief V15 §1-§8).
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]


def build_brief_v15(
    client: str,
    page_type: str,
    target_score_pct: float = 85.0,
    pipeline_recommended: str = "sequential_4_stages",
    creative_route: str = "premium",
) -> dict:
    """Construit le Brief V15 §1-§8 pour Mode 2 REPLACE.

    Args:
      client: slug client (doit avoir brand_dna + audit V26 sur page_type)
      page_type: page à refondre (doit avoir score_page_type + recos_v13_api)
      target_score_pct: cible Mode 2 (default 85% Excellent)
      pipeline_recommended: "single_pass" | "sequential_4_stages" | "best_of_n"
      creative_route: "safe" | "premium" | "bold" | None

    Returns: dict §1-§8 structuré.

    Raises:
      ValueError si artefacts manquants (brand_dna, audit, recos)

    NOTE Sprint B : skeleton seulement. Sprint C = full implementation.
    """
    captures_dir = ROOT / "data" / "captures" / client

    # Validations prérequis
    brand_dna_fp = captures_dir / "brand_dna.json"
    if not brand_dna_fp.exists():
        raise ValueError(f"❌ brand_dna manquant pour {client} : {brand_dna_fp}")
    score_fp = captures_dir / page_type / "score_page_type.json"
    if not score_fp.exists():
        raise ValueError(f"❌ score_page_type manquant : {score_fp}")
    # Cherche le fichier reco selon plusieurs conventions de nommage V13
    recos_fp = None
    for candidate in ("recos_v13_final.json", "recos_v13_api.json", "recos_enriched.json"):
        cfp = captures_dir / page_type / candidate
        if cfp.exists():
            recos_fp = cfp
            break
    if recos_fp is None:
        raise ValueError(f"❌ recos manquant (cherché : recos_v13_final.json, recos_v13_api.json, recos_enriched.json) dans {captures_dir / page_type}")

    # Chargement
    brand_dna = json.loads(brand_dna_fp.read_text())
    score = json.loads(score_fp.read_text())
    recos = json.loads(recos_fp.read_text())
    intent_fp = captures_dir / "client_intent.json"
    intent = json.loads(intent_fp.read_text()) if intent_fp.exists() else {}

    # Brief skeleton §1-§8 (Sprint B)
    brief = {
        "version": "15.0.1-sprint-b-v26-aa-skeleton",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "client": client,
        "page_type": page_type,
        "mode": "2_replace",

        # §1 — Identité brand (à enrichir Sprint C)
        "section_1_identity": {
            "client_id": client,
            "name": brand_dna.get("client", client),
            "url": brand_dna.get("home_url"),
            "voice_signature_phrase": (brand_dna.get("voice_tokens") or {}).get("voice_signature_phrase"),
            "tone": (brand_dna.get("voice_tokens") or {}).get("tone", []),
            "_TODO_sprint_c": "fully populate identity from brand_dna + clients_database",
        },

        # §2 — Page audit résumé (à enrichir Sprint C)
        "section_2_page_audit": {
            "audit_url": brand_dna.get("home_url"),  # fallback (notes est list pas dict dans V13)
            "audit_date": score.get("generatedAt"),
            "audit_score_total_pct": (score.get("aggregate") or {}).get("score100"),
            "_TODO_sprint_c": "extract by_pillar + top_critical_recos with evidence_ids",
        },

        # §3 — Audience
        "section_3_audience": {
            "primary_intent": intent.get("primary_intent"),
            "schwartz_awareness": intent.get("audience_awareness_schwartz"),
            "objections": intent.get("objections_principales", []),
            "_TODO_sprint_c": "structure persona detailed + triggers_buy",
        },

        # §4 — Copy par bloc (à enrichir Sprint C avec audit overrides)
        "section_4_copy_blocks": {
            "_TODO_sprint_c": "6 blocs canoniques (hero/body/social_proof/faq/cta_final/footer) avec overrides depuis recos audit",
        },

        # §5 — Couche technique
        "section_5_technical": {
            "responsive": "dual_viewport_required",
            "perf_targets": {"LCP": "<2.5s", "CLS": "<0.1", "FID": "<100ms"},
            "accessibility": "WCAG_AA",
            "seo_required": True,
        },

        # §6 — Brand Identity V15 (palette + polices + diff prescriptif)
        "section_6_brand_identity": {
            "palette_priority_1_client_real": (brand_dna.get("visual_tokens") or {}).get("colors", {}),
            "typography": (brand_dna.get("visual_tokens") or {}).get("typography", {}),
            "diff_prescriptif": brand_dna.get("diff", {}),
            "_TODO_sprint_c": "extract faits_vérifiés from brand_dna for use as claims",
        },

        # §7 — Assets
        "section_7_assets": {
            "screenshots_existants": str(captures_dir / page_type / "screenshots"),
            "inspirations_externes": [],  # Mode 2 REPLACE = vide (Mode 4 ELEVATE = utilisé)
        },

        # §8 — Directives Mode 2
        "section_8_directives_mode_2": {
            "page_to_replace_url": brand_dna.get("home_url"),
            "current_score_pct": (score.get("aggregate") or {}).get("score100"),
            "target_score_pct": target_score_pct,
            "pipeline_recommended": pipeline_recommended,
            "creative_route": creative_route,
            "_TODO_sprint_c": "extract gaps audit comme contraintes constructives explicites",
        },
    }

    return brief


def save_brief_v15(brief: dict, output_path: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Sauve le brief V15 sur disque (default : data/_briefs_v15/<client>_<page_type>.json)."""
    if output_path is None:
        briefs_dir = ROOT / "data" / "_briefs_v15"
        briefs_dir.mkdir(parents=True, exist_ok=True)
        output_path = briefs_dir / f"{brief['client']}_{brief['page_type']}.json"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2))
    return output_path


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", required=True)
    ap.add_argument("--target-score", type=float, default=85.0)
    ap.add_argument("--output")
    args = ap.parse_args()

    brief = build_brief_v15(args.client, args.page_type, target_score_pct=args.target_score)
    out = save_brief_v15(brief, pathlib.Path(args.output) if args.output else None)
    print(f"\n✓ Brief V15 saved: {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print(f"  Sections: §1-§8")
    print(f"  Status: SKELETON (Sprint B). Full impl Sprint C.")
