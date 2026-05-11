"""Mode 1 PERSONA NARRATOR — master pipeline.

PIVOT V26.AC : utilise le ROUTER RACINE ``client_context`` qui charge
automatiquement TOUS les artefacts disponibles (brand_dna + AURA +
screenshots + perception + recos + v143 + design_grammar +
reality_layer + evidence). Plus jamais d'oubli.

Stages:
  0. ROUTER RACINE — load all context.
  1. ``build_persona_narrator_prompt`` — V26.AG architecture (issue #13):
     returns (system_messages, user_turns_seq, philosophy_refs) with
     static system blocks cached via cache_control: ephemeral. The V26.AF
     8K hard limit stays enforced defensively.
  2. ``_select_vision_screenshots`` — client + AD-4 golden inspirations.
  3. ``call_sonnet_messages`` — single Anthropic SDK call with native
     prompt caching + multi-turn dialogue + optional vision images.
  4. ``apply_runtime_fixes`` (P0 rendering bugs).
  4a. ``_repair_ai_slop_fonts`` (Sprint AD-2 garde-fou).
  4a-bis. ``_check_ai_slop_visual_patterns`` (report-only by default V26.AG).
  4b. POST-GATES (AURA font blacklist + design_grammar forbidden).
  5. (Optional) doctrine_judge V3.2.1 GATE info-only.
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Optional

from ...core.brand_intelligence import has_brand_dna, load_brand_dna  # noqa: F401  re-exported for back-compat
from .api_call import apply_runtime_fixes, call_sonnet_messages
from .philosophy_bridge import ROOT
from .prompt_assembly import KNOWN_FOUNDERS, build_persona_narrator_prompt
from .runtime_fixes import (
    _check_aura_font_violations,
    _check_design_grammar_violations,
    _extract_brand_font_family,
    _repair_ai_slop_fonts,
)
from .vision_selection import _select_vision_screenshots, load_client_context
from .visual_gates import _check_ai_slop_visual_patterns, _repair_ai_slop_visual_patterns


def run_mode_1_persona_narrator(
    client: str,
    page_type: str,
    brief: dict,
    *,
    fallback_page_for_vision: Optional[str] = None,  # Sprint F V26.AC : fallback screenshots si page demandée non capturée
    forced_language: Optional[str] = None,  # Sprint F.fix V26.AC : "FR"/"EN"/etc — override vision bias
    apply_fixes: bool = True,
    apply_post_gates: bool = True,  # Sprint F V26.AC : AURA font + design_grammar forbidden
    repair_visual_slop: bool = False,  # V26.AG rollback : visual gate report-only by default
    skip_judges: bool = True,
    save_html_path: str | None = None,
    save_audit_path: str | None = None,
    temperature: float = 0.85,
    max_tokens: int = 8000,
    verbose: bool = True,
) -> dict:
    """Pipeline Mode 1 Persona Narrator V26.AC Sprint F.

    PIVOT V26.AC : utilise le ROUTER RACINE `client_context` qui charge automatiquement
    TOUS les artefacts disponibles (brand_dna + AURA + screenshots + perception + recos
    + v143 + design_grammar + reality_layer + evidence). Plus jamais d'oubli.

    Args:
      client: slug
      page_type: ex "home", "lp_listicle"
      brief: dict {objectif, audience, angle}
      fallback_page_for_vision: si page_type pas capturé (ex: lp_listicle nouveau pour
        Weglot), utilise screenshots de cette page pour vision input (ex: "home").
      apply_post_gates: AURA font blacklist check + design_grammar forbidden check.
      temperature: 0.85 (vs 0.7 Mode 1 V26.AA)
      skip_judges: True default

    Returns: dict {html, gen, ctx_summary, post_gate_violations, telemetry}
    """
    if verbose:
        print(f"\n══ Mode 1 PERSONA NARRATOR V26.AC — {client} / {page_type} ══")

    grand_t0 = time.time()

    # ── 0. ROUTER RACINE — charge TOUT ce qui existe ──
    ctx = load_client_context(client, page_type)
    if not ctx.has_brand_dna:
        raise ValueError(f"❌ brand_dna manquant pour {client}")

    if verbose:
        print(f"  Router racine : {ctx.completeness_pct}% completeness ({len(ctx.available_artefacts)} artefacts)")
        print(f"    Available : {', '.join(ctx.available_artefacts[:8])}")
        if ctx.missing_artefacts:
            print(f"    Missing   : {', '.join(ctx.missing_artefacts[:6])}{' ...' if len(ctx.missing_artefacts) > 6 else ''}")

    # ── 1. Build prompt enrichi (router-aware + hard constraints + golden bridge AD-3) ──
    # V26.AG (issue #13) — returns (system_messages, user_turns_seq, philosophy_refs).
    system_messages, user_turns_seq, philosophy_refs = build_persona_narrator_prompt(
        client, page_type, brief, ctx.brand_dna, ctx=ctx,
        forced_language=forced_language,
    )
    if verbose:
        sys_chars = sum(len(b["text"]) for b in system_messages)
        user_chars = sum(
            len(t["content"]) if isinstance(t["content"], str) else 0
            for t in user_turns_seq
        )
        cached_blocks = sum(1 for b in system_messages if "cache_control" in b)
        founder_used = client in KNOWN_FOUNDERS
        print(
            f"  Prompt V26.AG : system={sys_chars}c ({len(system_messages)} blocks, "
            f"{cached_blocks} cached) user_turns={len(user_turns_seq)} ({user_chars}c)"
        )
        if sys_chars > 8192:
            print(f"  ⚠️  ANTI-PATTERN #1 ALERT : system {sys_chars} > 8K (régression -28pts)")
        print(f"  Founder persona : {'hardcoded ⭐' if founder_used else 'extracted from brand_dna'}")
        if philosophy_refs:
            ref_names = [f"{r['site']}/{r['page']}" for r in philosophy_refs[:3]]
            print(f"  Golden refs (AD-3) : {len(philosophy_refs)} matches — top : {ref_names}")

    # ── 2. Sélection screenshots vision multimodal (client + AD-4 golden inspirations) ──
    vision_images = _select_vision_screenshots(
        ctx, fallback_page_for_vision, max_images=2,
        philosophy_refs=philosophy_refs, max_golden_inspirations=2,
    )
    if verbose:
        if vision_images:
            print(f"  Vision input : {len(vision_images)} screenshots — {[p.name for p in vision_images]}")
        else:
            print(f"  Vision input : ❌ aucun screenshot disponible (Sonnet code à l'aveugle)")

    # ── 3. Single-pass Sonnet via V26.AG dialogue + caching (issue #13) ──
    if verbose:
        print(f"\n→ Sonnet call_sonnet_messages (T={temperature}, max_tokens={max_tokens})...")
    gen = call_sonnet_messages(
        system_messages, user_turns_seq,
        image_paths=vision_images if vision_images else None,
        max_tokens=max_tokens, temperature=temperature, verbose=verbose,
    )
    html_raw = gen["html"]

    # ── 4. fix_html_runtime auto ──
    if apply_fixes:
        html_fixed, fixes_info = apply_runtime_fixes(html_raw, verbose=verbose)
    else:
        html_fixed, fixes_info = html_raw, {"applied": False}

    # ── 4a. AUTO-REPAIR garde-fou défensif AI-slop fonts (Sprint AD-2 V26.AD) ──
    # Si Sonnet a dérivé (variance T=0.85) et a inclu Inter/Roboto/etc dans le CSS
    # malgré le HARD CONSTRAINT, on rewrite UNIQUEMENT les déclarations CSS
    # (font-family, --font-*, Google Fonts URL). Texte body intouché.
    repairs_applied: list[str] = []
    if apply_post_gates:
        target_display = _extract_brand_font_family(ctx.brand_dna) if ctx.brand_dna else None
        # Body fallback : DM Sans (loadable Google Fonts, non-AI-slop)
        html_fixed, repairs_applied = _repair_ai_slop_fonts(
            html_fixed,
            target_display_font=target_display,
            target_body_font="DM Sans",
        )
        if verbose:
            if repairs_applied:
                print(f"  🔧 AUTO-REPAIR fonts: {len(repairs_applied)} substitution(s)")
                for r in repairs_applied[:5]:
                    print(f"     - {r}")
            else:
                print(f"  ✓ AUTO-REPAIR fonts : 0 substitution nécessaire")

    # ── 4a-bis. SPRINT AD-6 — Anti-AI-slop visuel patterns ──
    # V26.AG rollback: report-only by default. The V26.AF aggressive repair path
    # removed too much depth and produced "anti-design" white pages empirically.
    visual_slop_violations: list[dict] = []
    visual_slop_repairs: list[str] = []
    if apply_post_gates:
        visual_slop_violations = _check_ai_slop_visual_patterns(html_fixed)
        if visual_slop_violations:
            if verbose:
                print(f"  ⚠️ AI-slop visual patterns détectés : {len(visual_slop_violations)}")
                for v in visual_slop_violations[:5]:
                    print(f"     - {v['pattern']} (severity={v['severity']}, count={v['count']})")
            if repair_visual_slop:
                html_fixed, visual_slop_repairs = _repair_ai_slop_visual_patterns(html_fixed, visual_slop_violations)
                if verbose and visual_slop_repairs:
                    print(f"  🔧 Auto-repaired : {len(visual_slop_repairs)} pattern(s)")
                    for r in visual_slop_repairs:
                        print(f"     - {r}")
                # Re-check post-repair
                remaining = _check_ai_slop_visual_patterns(html_fixed)
                if verbose and remaining:
                    print(f"  ⚠️ Patterns restants après repair (structurels, à refondre) : {len(remaining)}")
                    for v in remaining[:3]:
                        print(f"     - {v['pattern']} : {v['fix']}")
            elif verbose:
                print("  ↳ report-only (repair_visual_slop=True pour l'ancien repair agressif)")
        else:
            if verbose:
                print(f"  ✓ AI-slop visual patterns : 0 détection")

    # ── 4b. POST-GATES (AURA font blacklist + design_grammar forbidden) ──
    post_gate_violations = {"aura_font": [], "design_grammar": [], "ai_slop_visual": visual_slop_violations}
    if apply_post_gates:
        post_gate_violations["aura_font"] = _check_aura_font_violations(html_fixed)
        post_gate_violations["design_grammar"] = _check_design_grammar_violations(html_fixed, ctx.design_grammar)
        # ai_slop_visual already populated above (re-check post-repair)
        post_gate_violations["ai_slop_visual"] = _check_ai_slop_visual_patterns(html_fixed)
        if verbose:
            if post_gate_violations["aura_font"]:
                print(f"  ⚠️ AURA font blacklist VIOLATIONS post-repair : {post_gate_violations['aura_font']}")
            else:
                print(f"  ✓ AURA font blacklist : OK (post-repair)")
            if post_gate_violations["design_grammar"]:
                print(f"  ⚠️ design_grammar VIOLATIONS : {post_gate_violations['design_grammar']}")
            else:
                print(f"  ✓ design_grammar forbidden patterns : OK")

    # ── 4. Save HTML ──
    if save_html_path:
        out_html = pathlib.Path(save_html_path)
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html_fixed)
        if verbose:
            print(f"\n  ✓ HTML saved : {out_html.relative_to(ROOT) if out_html.is_relative_to(ROOT) else out_html}")

    # ── 5. (Optionnel) doctrine_judge en POST-PROCESS GATE info-only ──
    audit: dict = {}
    if not skip_judges:
        if verbose:
            print(f"\n→ doctrine_judge V3.2.1 GATE (info only, NE bloque PAS la livraison)...")
        from moteur_multi_judge.judges.doctrine_judge import audit_lp_doctrine
        audit = audit_lp_doctrine(html_fixed, client, page_type, verbose=verbose, parallel=True)
        if save_audit_path:
            pathlib.Path(save_audit_path).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(save_audit_path).write_text(json.dumps(audit, ensure_ascii=False, indent=2))

    grand_dt = time.time() - grand_t0

    cost = (gen["tokens_in"] / 1e6 * 3) + (gen["tokens_out"] / 1e6 * 15)
    telemetry = {
        "wall_seconds_total": round(grand_dt, 1),
        "wall_seconds_gen": gen["wall_seconds"],
        "tokens_in": gen["tokens_in"],
        "tokens_out": gen["tokens_out"],
        "cost_estimate_usd": round(cost, 3),
    }

    if verbose:
        print(f"\n══ Mode 1 PERSONA NARRATOR — DONE ══")
        print(f"  Wall total      : {telemetry['wall_seconds_total']}s")
        print(f"  Coût estimé     : ${telemetry['cost_estimate_usd']}")
        print(f"  HTML chars      : {len(html_fixed)}")
        if audit:
            t = audit.get("totals", {})
            print(f"  Doctrine score  : {t.get('total_pct','?')}% (info only — pas blocking)")

    return {
        "html": html_fixed,
        "html_raw": html_raw,
        "gen": gen,
        # API stability alias — caller can do result["audit"] across all modes (Sprint AD-1).
        "audit": audit,
        "audit_doctrine_info_only": audit,
        "fixes": fixes_info,
        "font_repairs_applied": repairs_applied,  # Sprint AD-2 V26.AD garde-fou
        "post_gate_violations": post_gate_violations,
        "ctx_summary": {
            "completeness_pct": ctx.completeness_pct,
            "n_available_artefacts": len(ctx.available_artefacts),
            "available": ctx.available_artefacts,
            "missing": ctx.missing_artefacts,
            "n_vision_images_used": gen.get("n_images", 0),
        },
        "founder_persona_used": KNOWN_FOUNDERS.get(client, "extracted_from_brand_dna"),
        "telemetry": telemetry,
        "client": client,
        "page_type": page_type,
        "brief": brief,
        "mode": "persona_narrator",
        "version": "V26.AD.sprint_ad1",
    }


__all__ = ["run_mode_1_persona_narrator"]
