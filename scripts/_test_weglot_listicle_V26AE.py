"""Test FINAL Weglot listicle V26.AE — pipeline propre depuis le départ.

V26.AE post-cleanup : prompt_mode="lite" (≤8K cible) pour fight l'anti-pattern #1.
Compare à V26.AD+ qui était à 17K.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.core.brief_v2 import BriefV2
from moteur_gsg.core.brief_v2_validator import (
    parse_brief_v2_from_dict, validate_or_raise, archive_brief_v2,
)
from moteur_gsg.orchestrator import generate_lp


WEGLOT_BRIEF_V2 = {
    "mode": "complete",
    "page_type": "lp_listicle",
    "client_url": "https://www.weglot.com",
    "target_language": "FR",
    "objective": "Concept Tunnel Editorial-to-Conversion. Trafic froid SaaS B2B sur listicle haute valeur ajoutée. Convertir en trial 10j sans CB, après lecture convaincue (pas pushy).",
    "audience": "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p, déjà site live monolingue performant, considère internationalisation 2026. 3 peurs : (1) dev backlog 3 mois, (2) SEO multi-langue cassé, (3) qualité traduction auto. Time-poor, scan 30s avant lecture. Schwartz awareness : solution_aware.",
    "angle": "Listicle éditorial signé Augustin Prot (founder Weglot). Ton journalistique style First Round Review / Y Combinator blog / Stripe Press. 65 000+ sites servis = base empirique solide.",
    "traffic_source": ["cold_ad_meta", "cold_ad_google", "organic_seo"],
    "visitor_mode": "scan_30s",
    "inspiration_urls": [],
    "desired_signature": "Editorial SaaS Research-Driven",
    "desired_emotion": "Le visiteur se dit : ces gens ont vraiment compris mon problème de traduction",
    "available_proofs": ["chiffres_internes", "logos_clients_tier1"],
    "sourced_numbers": [
        {"number": "65 000", "source": "Weglot dashboard interne 2026-04", "context": "sites multilingues servis depuis 2016"},
        {"number": "85%", "source": "étude Weglot interne sur 2300 clients SaaS B2B", "context": "réduction du temps de mise en multilingue vs solution custom"},
        {"number": "10 jours", "source": "Weglot pricing page", "context": "trial gratuit sans CB"},
    ],
    "client_blog_urls": [
        "https://www.weglot.com/blog/saas-internationalization-guide",
        "https://www.weglot.com/blog/seo-multilingual-best-practices",
    ],
    "forbidden_visual_patterns": [
        "stock_photos", "gradient_mesh", "ai_generated_images",
        "checkmark_icons_systematic", "lifestyle_photography_hero",
    ],
    "must_include_elements": ["10 raisons numérotées", "CTA final unique 'Tester gratuitement 10 jours'"],
}


def main():
    print("══ Test FINAL Weglot listicle V26.AE — pipeline propre prompt_mode=lite ══\n")

    print("→ 1. Parse + valide BriefV2 §4 framework cadrage...")
    brief = parse_brief_v2_from_dict(WEGLOT_BRIEF_V2)
    validate_or_raise(brief)
    print(f"  ✓ BriefV2 valide (3 sourced_numbers, 5 forbidden_patterns)")
    archive_path = archive_brief_v2(brief, label="V26AE_test_final")
    print(f"  ✓ Brief archivé : {archive_path.relative_to(ROOT)}")

    legacy_brief = brief.to_legacy_brief()

    print(f"\n→ 2. Call orchestrator.generate_lp(mode='complete', prompt_mode='lite')")

    out_html = ROOT / "deliverables" / "weglot-listicle-V26AE-FINAL.html"
    log_path = ROOT / "data" / "_test_listicle_V26AE_log.txt"
    out_html.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    result = generate_lp(
        mode="complete",
        client="weglot",
        page_type="lp_listicle",
        brief=legacy_brief,
        fallback_page_for_vision="home",
        forced_language=brief.target_language,
        prompt_mode="lite",  # V26.AE : default lite
        save_html_path=str(out_html),
        skip_judges=True,
        verbose=True,
    )
    wall = time.time() - t0

    html = result.get("html", "")
    n_var = html.count("var(--")
    has_pneue = "Ppneuemontreal" in html or "PpneueMontreal" in html
    has_dm_sans = "DM Sans" in html
    has_inter_css = any(p in html for p in ["family=Inter", "'Inter'", '"Inter"'])
    fr_indicators = sum(1 for w in ["pour", "vous", "votre", "ce qui", "le", "la"] if w.lower() in html.lower())
    en_indicators = sum(1 for w in ["the", "your", "this is", "what we", "for"] if f" {w} " in html.lower())

    post_gates = result.get("post_gate_violations") or {}
    aura_v = post_gates.get("aura_font") or []
    grammar_v = post_gates.get("design_grammar") or []
    visual_slop_v = post_gates.get("ai_slop_visual") or []

    ctx_summary = result.get("ctx_summary") or {}
    completeness = ctx_summary.get("completeness_pct", "?")
    n_artefacts = ctx_summary.get("n_available_artefacts", "?")
    n_vision = ctx_summary.get("n_vision_images_used", "?")

    telemetry = result.get("telemetry") or {}
    cost = telemetry.get("cost_estimate_usd", "?")
    wall_total = telemetry.get("wall_seconds_total", "?")

    print(f"\n══ RÉSULTAT V26.AE ══")
    print(f"  HTML chars             : {len(html):,}")
    print(f"  var(--) occurrences    : {n_var}")
    print(f"  Ppneuemontreal présent : {'✓' if has_pneue else '❌'}")
    print(f"  DM Sans présent        : {'✓' if has_dm_sans else '❌'}")
    print(f"  Inter CSS (BAD)        : {'❌ FOUND' if has_inter_css else '✓ absent'}")
    print(f"  FR indicators          : {fr_indicators} / EN : {en_indicators}")
    print(f"  AURA font violations   : {len(aura_v)} {aura_v}")
    print(f"  Grammar violations     : {len(grammar_v)} {grammar_v}")
    print(f"  AI-slop visual         : {len(visual_slop_v)} {[v['pattern'] for v in visual_slop_v[:3]]}")
    print(f"  Router completeness    : {completeness}%")
    print(f"  Artefacts loaded       : {n_artefacts}")
    print(f"  Vision images used     : {n_vision}")
    print(f"  Coût estimé            : ${cost}")
    print(f"  Wall total             : {wall_total}s")
    print(f"\n  HTML saved → {out_html.relative_to(ROOT)}")

    print(f"\n══ COMPARAISON ══")
    print(f"  V26.AC v4 ref      : prompt 8.7K / var=109 / 0 violations / $0.141 / 133s")
    print(f"  V26.AD+ FULL-STACK : prompt 17K / var=104 / 0 violations / $0.158 / 143s")
    print(f"  V26.AE LITE      : prompt ?    / var={n_var} / aura={len(aura_v)} grammar={len(grammar_v)} slop={len(visual_slop_v)} / ${cost} / {wall_total}s")

    log_path.write_text(
        f"V26.AE Final test Weglot listicle\n"
        f"==================================\n"
        f"HTML: {out_html.relative_to(ROOT)}\n"
        f"chars={len(html)} var={n_var} pneue={has_pneue} dm_sans={has_dm_sans} inter={has_inter_css}\n"
        f"fr_indic={fr_indicators} en_indic={en_indicators}\n"
        f"violations: aura={aura_v} grammar={grammar_v} slop={[v['pattern'] for v in visual_slop_v]}\n"
        f"completeness={completeness} vision={n_vision} cost={cost} wall={wall_total}\n"
    )
    print(f"  Log saved → {log_path.relative_to(ROOT)}")

    return result


if __name__ == "__main__":
    main()
