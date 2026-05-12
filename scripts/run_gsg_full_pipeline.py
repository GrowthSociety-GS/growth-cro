"""scripts/run_gsg_full_pipeline.py — canonical GSG intake runner.

Orchestrateur conversationnel COMPLET du GSG. Workflow canonique :

  1. Mathis formule une demande brute ("je veux générer une LP...")
  2. `intake_wizard.py` résout client + page_type + target_language + mode
  3. Script charge tout ce qu'on sait du client (router racine client_context)
  4. Script PRÉ-REMPLIT BriefV2 depuis brand_dna + intent + v143 + recos + design_grammar
  5. Script présente le brief pré-rempli en markdown pour validation Mathis
  6. Mathis confirme / fournit les champs manquants (audience principalement)
  7. Default V27 : lance `moteur_gsg.orchestrator.generate_lp()` chemin minimal
  8. Option forensic : pipeline_sequential 4 stages (Strategy → Copy → Composer → Polish)
  9. Script sauve HTML + audit + intermédiaires + brief archive

Usage :
    # Mode produit / future webapp : demande brute -> questions ou génération
    python3 scripts/run_gsg_full_pipeline.py --request "Génère une LP listicle Weglot en FR." --prepare-only

    # Mode interactif (questions posées en stdin)
    python3 scripts/run_gsg_full_pipeline.py --url https://www.weglot.com --page-type lp_listicle --lang FR

    # Mode JSON brief (skip questions)
    python3 scripts/run_gsg_full_pipeline.py --brief data/_briefs_v2/weglot_listicle.json

    # Mode pré-remplit + override quelques champs
    python3 scripts/run_gsg_full_pipeline.py --url https://www.weglot.com --page-type lp_listicle \
      --audience "Head of Growth SaaS B2B 50-500p, time-poor scan 30s..." \
      --angle "Listicle éditorial signé Augustin Prot, ton First Round Review"

    # Forensic only : ancien pipeline 4 stages
    python3 scripts/run_gsg_full_pipeline.py --url https://www.weglot.com --page-type lp_listicle \
      --generation-path sequential --non-interactive
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env
from moteur_gsg.core.brief_v2_validator import (
    parse_brief_v2_from_dict, archive_brief_v2,
)
from moteur_gsg.core.brief_v2_prefiller import (
    prefill_brief_v2_from_client, format_brief_for_mathis_review,
)
from moteur_gsg.modes.mode_1.prompt_assembly import build_founder_persona
from moteur_gsg.modes.mode_1.prompt_blocks import (
    _format_intent_for_page_type,
    _format_aura_tokens_block,
    _load_tokens_css,
    _format_layout_archetype_block_LITE,
    _format_golden_techniques_block_LITE,
)
from moteur_gsg.modes.mode_1.vision_selection import _select_vision_screenshots
from moteur_gsg.modes.mode_1.visual_gates import (
    _check_ai_slop_visual_patterns,
    _repair_ai_slop_visual_patterns,
)
from moteur_gsg.modes.mode_1.runtime_fixes import (
    _check_aura_font_violations,
    _repair_ai_slop_fonts,
    _check_design_grammar_violations,
    _extract_brand_font_family,
)


def main():
    p = argparse.ArgumentParser(description="GSG canonical runner (minimal default, sequential forensic opt-in)")
    p.add_argument("--url", help="Client URL (ex: https://www.weglot.com)")
    p.add_argument("--request", help="Raw user request, e.g. \"Je veux un listicle Weglot FR pour signup trial\"")
    p.add_argument("--page-type", default=None, help="lp_listicle / home / pdp / lp_sales / advertorial")
    p.add_argument("--lang", default=None, help="Target language : FR / EN / ES / DE / IT / PT / NL / JP")
    p.add_argument("--mode", default=None, help="complete / replace / extend / elevate / genesis")
    p.add_argument("--brief", help="Path JSON brief V2 (skip questions)")
    p.add_argument("--audience", help="Override audience field")
    p.add_argument("--angle", help="Override angle field")
    p.add_argument("--objective", help="Override objective field")
    p.add_argument("--save-html", help="Output HTML path")
    p.add_argument("--save-dir", help="Save intermediates dir")
    p.add_argument("--prepare-only", action="store_true",
                   help="Stop after raw request/intake + BriefV2 draft. Useful for webapp wizard preview.")
    p.add_argument("--archive-draft-label", default="GSG_INTAKE_V27_2_E",
                   help="Label for data/_briefs_v2_drafts when --request is used.")
    p.add_argument("--generation-path", choices=["minimal", "sequential"], default="minimal",
                   help="minimal=canonical moteur_gsg.generate_lp default; sequential=forensic 4-stage pipeline")
    p.add_argument("--generation-strategy", choices=["controlled", "single_pass"], default="controlled",
                   help="Mode 1 minimal strategy: controlled=planner+copy slots+renderer, single_pass=rollback prompt-to-HTML")
    p.add_argument("--copy-fallback-only", action="store_true",
                   help="Smoke test only: render deterministic placeholder copy without LLM")
    p.add_argument("--primary-cta-label", help="Deterministic CTA label override")
    p.add_argument("--primary-cta-href", help="Deterministic CTA href override")
    p.add_argument("--non-interactive", action="store_true", help="Skip stdin prompts (for CI)")
    p.add_argument("--skip-judges", action="store_true", help="Skip multi-judge final (default = run judges)")
    p.add_argument("--repair-visual-slop", action="store_true", help="Legacy aggressive repair for visual AI-slop patterns. Default is report-only.")
    args = p.parse_args()

    print("══════════════════════════════════════════════════════════════════════════════")
    print("  GSG Canonical — minimal moteur_gsg default, sequential forensic opt-in")
    print("══════════════════════════════════════════════════════════════════════════════\n")

    # ─── Étape 1 : récupère URL + page_type ─────────────────────────────────
    request_cta_label = None
    request_cta_href = None

    if args.brief:
        # Mode JSON : load brief direct
        print(f"→ Mode JSON brief : load {args.brief}")
        raw = json.loads(pathlib.Path(args.brief).read_text())
        brief = parse_brief_v2_from_dict(raw)
        from urllib.parse import urlparse
        slug = urlparse(brief.client_url).netloc.replace("www.", "").split(".")[0]
        from scripts.client_context import load_client_context
        ctx = load_client_context(slug, brief.page_type)
        sources = {k: "user-provided JSON" for k in ["mode", "page_type", "client_url", "target_language", "objective", "audience", "angle"]}
    elif args.request:
        print("→ Étape 1 : parse demande brute via GSG intake wizard...")
        print(f"  Request      : {args.request}")
        print()
        from moteur_gsg.core.intake_wizard import (
            archive_intake_draft,
            build_intake_from_user_request,
            format_intake_for_review,
        )

        intake = build_intake_from_user_request(
            args.request,
            client_url=args.url,
            page_type=args.page_type,
            mode=args.mode,
            target_language=args.lang,
            objective=args.objective,
            audience=args.audience,
            angle=args.angle,
        )
        print("\n" + "─" * 80)
        print(format_intake_for_review(intake))
        print("─" * 80 + "\n")

        draft_path = archive_intake_draft(intake, label=args.archive_draft_label)
        print(f"✓ Intake draft archivé : {draft_path.relative_to(ROOT)}")

        request_cta_label = intake.request.primary_cta_label
        request_cta_href = intake.request.primary_cta_href

        if args.prepare_only:
            return 0
        if not intake.ready_to_generate:
            print("\n❌ Intake incomplet : répondre aux questions wizard avant génération.")
            for q in intake.questions:
                print(f"   - [{q.priority}] {q.field}: {q.question}")
            return 2

        brief = intake.brief
        from scripts.client_context import load_client_context
        ctx = load_client_context(intake.request.client_slug, brief.page_type)
        sources = intake.sources
    else:
        # Mode pre-fill from URL
        if not args.url:
            print("❌ --url required (ou --brief ou --request)")
            return 1

        print("→ Étape 1 : pré-fill BriefV2 depuis client context...")
        print(f"  URL          : {args.url}")
        requested_page_type = args.page_type or "lp_listicle"
        requested_lang = args.lang or "FR"
        requested_mode = args.mode or "complete"
        print(f"  Page type    : {requested_page_type}")
        print(f"  Lang         : {requested_lang}")
        print(f"  Mode         : {requested_mode}")
        print()

        brief, sources, ctx = prefill_brief_v2_from_client(
            client_url=args.url,
            page_type=requested_page_type,
            target_language=requested_lang,
            mode=requested_mode,
            objective_override=args.objective,
            audience_override=args.audience,
            angle_override=args.angle,
        )

    # ─── Étape 2 : présente le brief pré-rempli ─────────────────────────────
    print("\n" + "─" * 80)
    print(format_brief_for_mathis_review(brief, sources, ctx))
    print("─" * 80 + "\n")

    # ─── Étape 3 : interactive — Mathis fournit les champs manquants ────────
    errors = brief.validate()
    if errors and not args.non_interactive:
        print(f"⚠️  BriefV2 invalide ({len(errors)} erreurs). Fournis les manquants :")
        for err in errors:
            print(f"   - {err}")
        # For each empty critical field, ask
        for field_name, prompt_text in [
            ("audience", "Audience (≥100 chars, format : Persona + 3 peurs + 3 désirs + Schwartz level)"),
            ("objective", "Objective (1-2 phrases, ex: 'Convertir en trial 10j')"),
            ("angle", "Angle éditorial (50-300 chars, hook qui rend la page mémorable)"),
        ]:
            current = getattr(brief, field_name)
            if not current or len(current.strip()) < 10:
                print(f"\n→ {prompt_text}")
                print(f"  (current: {current[:60] if current else '(empty)'})")
                try:
                    user_input = input(f"  Nouveau {field_name} (laisse vide pour skip) : ").strip()
                    if user_input:
                        setattr(brief, field_name, user_input)
                except (KeyboardInterrupt, EOFError):
                    print("\nAbandon.")
                    return 1

    # Re-validate
    errors = brief.validate()
    if errors:
        print("\n❌ BriefV2 toujours invalide :")
        for err in errors:
            print(f"   - {err}")
        return 2

    # Archive le brief validé
    archive_path = archive_brief_v2(brief, label="GSG_CANONICAL_V27")
    print(f"\n✓ BriefV2 valide → archivé : {archive_path.relative_to(ROOT)}")

    save_dir = pathlib.Path(args.save_dir) if args.save_dir else (ROOT / "data" / "_pipeline_runs" / f"{ctx.client}_{brief.page_type}_{int(time.time())}")
    if not save_dir.is_absolute():
        save_dir = ROOT / save_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    # ─── Étape 4A : chemin canonique minimal ────────────────────────────────
    if args.generation_path == "minimal":
        print("\n→ Étape 4 : chemin canonique minimal via moteur_gsg.orchestrator.generate_lp()...")
        from moteur_gsg.orchestrator import generate_lp

        if args.save_html:
            out_path = pathlib.Path(args.save_html)
        else:
            out_path = ROOT / "deliverables" / f"{ctx.client}-{brief.page_type}-GSG-CANONICAL.html"

        generation_kwargs = {
            "skip_judges": args.skip_judges,
            "save_html_path": str(out_path),
            "verbose": True,
        }
        if brief.mode == "complete":
            generation_kwargs.update({
                "target_language": brief.target_language,
                "primary_cta_label": args.primary_cta_label or request_cta_label,
                "primary_cta_href": args.primary_cta_href or request_cta_href,
                "generation_strategy": args.generation_strategy,
                "copy_fallback_only": args.copy_fallback_only,
            })
        elif brief.mode in {"extend", "elevate"}:
            generation_kwargs.update({
                "target_language": brief.target_language,
                "primary_cta_label": args.primary_cta_label or request_cta_label,
                "primary_cta_href": args.primary_cta_href or request_cta_href,
                "generation_strategy": args.generation_strategy,
                "copy_fallback_only": args.copy_fallback_only,
            })
        else:
            generation_kwargs["forced_language"] = brief.target_language

        brief_payload = brief.to_legacy_brief() if brief.mode == "complete" else brief

        result = generate_lp(
            mode=brief.mode,
            client=ctx.client,
            page_type=brief.page_type,
            brief=brief_payload,
            **generation_kwargs,
        )

        summary = {
            "version": "GSG_CANONICAL_MINIMAL_V27",
            "generation_path": args.generation_path,
            "mode": brief.mode,
            "client": ctx.client,
            "page_type": brief.page_type,
            "target_language": brief.target_language,
            "html_path": str(out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path),
            "brief_archive": str(archive_path.relative_to(ROOT)),
            "telemetry": result.get("telemetry", {}),
            "prompt_meta": result.get("prompt_meta", {}),
            "minimal_gates": result.get("minimal_gates", {}).get("audit", {}),
        }
        summary_path = save_dir / "canonical_run_summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

        print("\n══ DONE ══")
        print("  Generation path  : canonical minimal")
        print(f"  HTML saved       : {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}")
        print(f"  Summary saved    : {summary_path.relative_to(ROOT)}")
        print(f"  BriefV2 archive  : {archive_path.relative_to(ROOT)}")
        return 0

    # ─── Étape 4 : Charge contexte enrichi pour pipeline ────────────────────
    print("\n→ Étape 4 : prepare context pour pipeline 4 stages (forensic)...")

    founder_persona = build_founder_persona(ctx.client, ctx.brand_dna or {})
    archetype_summary = _format_layout_archetype_block_LITE(brief.page_type)
    format_intent = _format_intent_for_page_type(brief.page_type)

    aura_css_block = ""
    if ctx.aura_tokens:
        tokens_css = _load_tokens_css(ctx.client)
        aura_css_block = _format_aura_tokens_block(ctx.aura_tokens, tokens_css=tokens_css)

    # Vision images : client fallback home + golden refs proches si dispo.
    # V26.AG rollback: do not let Composer code blind for new page types like lp_listicle.
    philosophy_refs = []
    if ctx.aura_tokens:
        _, philosophy_refs = _format_golden_techniques_block_LITE(ctx.aura_tokens, brief.page_type)
    vision_images = _select_vision_screenshots(
        ctx,
        fallback_page_for_vision="home",
        max_images=2,
        philosophy_refs=philosophy_refs,
        max_golden_inspirations=2,
    )

    forced_font = _extract_brand_font_family(ctx.brand_dna or {})

    print(f"  Founder persona : {len(founder_persona)} chars")
    print(f"  Archetype       : {len(archetype_summary)} chars")
    print(f"  AURA CSS block  : {len(aura_css_block)} chars")
    print(f"  Golden refs     : {len(philosophy_refs)}")
    print(f"  Vision images   : {len(vision_images) if vision_images else 0}")
    print(f"  Forced font     : {forced_font}")

    # ─── Étape 5 : Lance pipeline 4 stages ──────────────────────────────────
    print("\n→ Étape 5 : lance pipeline_sequential 4 stages...")
    print(f"  Save dir : {save_dir.relative_to(ROOT) if save_dir.is_relative_to(ROOT) else save_dir}\n")

    from moteur_gsg.core.pipeline_sequential import run_pipeline_sequential_4_stages

    result = run_pipeline_sequential_4_stages(
        brief=brief,
        ctx=ctx,
        founder_persona=founder_persona,
        archetype_summary=archetype_summary,
        format_intent=format_intent,
        aura_css_block=aura_css_block,
        vision_images=vision_images,
        forced_font=forced_font,
        save_intermediates=True,
        save_dir=save_dir,
        verbose=True,
    )

    if "error" in result:
        print(f"\n❌ Pipeline failed at {result['error']}")
        return 3

    html_final = result["html_final"]

    # ─── Étape 6 : Post-process gates ────────────────────────────────────────
    print("\n→ Étape 6 : post-process gates...")

    # AD-2 fonts
    html_final, font_repairs = _repair_ai_slop_fonts(
        html_final,
        target_display_font=forced_font,
        target_body_font="DM Sans",
    )
    if font_repairs:
        print(f"  🔧 Font repairs : {len(font_repairs)}")
        for r in font_repairs[:5]:
            print(f"     - {r}")

    # AD-6 anti-slop visual — V26.AG rollback: report-only by default.
    # Empirical V26.AF showed aggressive repair flattened pages into "anti-design".
    visual_violations = _check_ai_slop_visual_patterns(html_final)
    if visual_violations:
        print(f"  ⚠️ Visual AI-slop patterns reported : {len(visual_violations)}")
        for v in visual_violations[:5]:
            print(f"     - {v['pattern']} (severity={v['severity']}, count={v['count']})")
        if args.repair_visual_slop:
            html_final, visual_repairs = _repair_ai_slop_visual_patterns(html_final, visual_violations)
            if visual_repairs:
                print(f"  🔧 Visual repairs : {len(visual_repairs)}")
                for r in visual_repairs:
                    print(f"     - {r}")
        else:
            print("  ↳ report-only (use --repair-visual-slop for legacy flattening repair)")

    # Final post-gate checks
    aura_font_v = _check_aura_font_violations(html_final)
    grammar_v = _check_design_grammar_violations(html_final, ctx.design_grammar)
    visual_v_final = _check_ai_slop_visual_patterns(html_final)

    print(f"\n  ✓ AURA font violations  : {len(aura_font_v)} {aura_font_v}")
    print(f"  ✓ Grammar violations    : {len(grammar_v)} {grammar_v}")
    print(f"  ✓ AI-slop visual final  : {len(visual_v_final)} {[v['pattern'] for v in visual_v_final[:3]]}")

    # ─── Étape 7 : Save HTML final ────────────────────────────────────────────
    if args.save_html:
        out_path = pathlib.Path(args.save_html)
    else:
        out_path = ROOT / "deliverables" / f"{ctx.client}-{brief.page_type}-V26AG-ROLLBACK.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_final)

    # ─── Étape 8 : Multi-judge — note réelle (V26.AF FIX 2) ──────────────────
    judge_note = None
    if not args.skip_judges:
        print("\n→ Étape 8 : multi-judge (doctrine V3.2.1 + humanlike + impl_check)...")
        try:
            from moteur_multi_judge.orchestrator import run_multi_judge
            judge_audit = run_multi_judge(
                html=html_final, client=ctx.client, page_type=brief.page_type, verbose=True,
            )
            final = judge_audit.get("final", {}) if isinstance(judge_audit, dict) else {}
            doctrine_pct = final.get("doctrine_pct") or final.get("doctrine_score_pct")
            humanlike_pct = final.get("humanlike_pct") or final.get("humanlike_score_pct")
            final_pct = final.get("final_score_pct")
            verdict = final.get("verdict")

            judge_note = {
                "doctrine_pct": doctrine_pct,
                "humanlike_pct": humanlike_pct,
                "final_pct": final_pct,
                "verdict": verdict,
            }
            audit_path = save_dir / "audit_multi_judge.json"
            audit_path.write_text(json.dumps(judge_audit, ensure_ascii=False, indent=2))

            print("\n  📊 NOTE FINALE V26.AF :")
            print(f"     Doctrine V3.2.1 : {doctrine_pct}% / Humanlike : {humanlike_pct}% / Final 70-30 : {final_pct}% — {verdict}")
            print(f"     Audit saved : {audit_path.relative_to(ROOT)}")
        except Exception as e:
            print(f"  ⚠️ multi-judge failed : {e}")
            import traceback
            traceback.print_exc()

    print("\n══ DONE ══")
    print(f"  Cost total       : ${result['total_cost_usd']}")
    print(f"  Wall total       : {result['total_wall_seconds']}s")
    print(f"  HTML size        : {len(html_final):,} chars")
    print(f"  HTML saved       : {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}")
    print(f"  Intermediates    : {save_dir.relative_to(ROOT) if save_dir.is_relative_to(ROOT) else save_dir}")
    print(f"  BriefV2 archive  : {archive_path.relative_to(ROOT)}")
    if judge_note:
        print(f"  📊 Note doctrine : {judge_note['doctrine_pct']}% / humanlike : {judge_note['humanlike_pct']}% / final : {judge_note['final_pct']}% ({judge_note['verdict']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
