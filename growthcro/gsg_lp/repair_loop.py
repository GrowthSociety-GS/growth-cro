"""V26.Z W3 — multi-judge → repair iteration loop.

Two pieces:

  * ``build_repair_prompt(...)`` — assembles a *targeted* repair prompt
    that consumes the multi-judge verdict (humanlike weaknesses,
    AI-default patterns, signature_nommable, brand reminders, design
    grammar reminders) **without** re-shipping the whole mega-prompt.
    Force-focuses Sonnet on the corrections.
  * ``run_repair_loop(initial_html, args, brand_dna, design_grammar,
    output_path)`` — generate → multi_judge → if score < threshold,
    repair via ``call_sonnet`` → loop. Returns ``(final_html,
    iterations_log)``.

Splits out of ``gsg_generate_lp.py`` (issue #8). The Sonnet-call adapter
is imported from ``lp_orchestrator`` to avoid duplicating the
streaming / non-streaming switch.
"""
from __future__ import annotations

import json
import pathlib
import sys

from .data_loaders import ROOT, SCRIPTS, auto_fix_runtime


def build_repair_prompt(current_html: str, client: str,
                         multi_judge_result: dict,
                         brand_dna: dict, design_grammar: dict,
                         original_mega_prompt_summary: str = "") -> str:
    """V26.Z W3 : prompt de repair ciblé qui consomme les verdicts multi-judge.

    Stratégie : ne PAS régénérer from scratch — corriger SPÉCIFIQUEMENT les
    weaknesses identifiées par le humanlike + les ai_default_patterns détectés.
    Le mega-prompt initial est référencé via summary, pas copié intégralement
    (économie tokens + force le focus sur les corrections).
    """
    judges = multi_judge_result.get("judges") or {}
    humanlike = judges.get("humanlike") or {}
    arbitrage = judges.get("arbitrage") or {}
    agreement = multi_judge_result.get("agreement") or {}

    weaknesses = humanlike.get("humanlike_weaknesses") or []
    ai_patterns = humanlike.get("ai_default_patterns_detected") or []
    sig_nommable = humanlike.get("signature_nommable")
    humanlike_verdict = humanlike.get("verdict_paragraph", "")
    arbitrage_verdict = arbitrage.get("final_verdict_short", "")
    final_pct = multi_judge_result.get("final_score_pct", "?")

    weaknesses_md = "\n".join(f"  - {w}" for w in weaknesses) if weaknesses else "  (aucune)"
    ai_patterns_md = "\n".join(f"  - {p}" for p in ai_patterns) if ai_patterns else "  (aucun)"

    # Compact brand reminder
    bd_summary = ""
    vt = brand_dna.get("visual_tokens") or {}
    voice = brand_dna.get("voice_tokens") or {}
    colors = vt.get("colors") or {}
    palette = colors.get("palette_full") or []
    bd_summary = f"Palette obligatoire: {', '.join(c.get('hex','?') for c in palette[:4])}"
    if voice.get("tone"):
        bd_summary += f" | Tone: {', '.join(voice['tone'][:3])}"
    if voice.get("forbidden_words"):
        bd_summary += f" | Forbidden words: {', '.join(voice['forbidden_words'][:5])}"

    # Compact design_grammar reminder (anti-patterns + composition rule)
    dg_summary = ""
    if design_grammar:
        bfp = (design_grammar.get("brand_forbidden_patterns") or {})
        global_ai = bfp.get("global_anti_ai_patterns") or []
        cr = (design_grammar.get("composition_rules") or {})
        asym = (cr.get("asymmetry") or {}).get("rule", "")
        if global_ai:
            dg_summary += "Anti-patterns brand interdits:\n" + "\n".join(f"  - {p}" for p in global_ai[:8])
        if asym:
            dg_summary += f"\n  - Composition: {asym}"

    return f"""Tu es directeur artistique senior + dev front senior. La LP que tu as générée pour {client.upper()} a été auditée par un multi-judge 3-way. **Score final : {final_pct}%** (en dessous du seuil de qualité).

Le défenseur (audit mécanique) donnait ~95%, mais le directeur créatif senior (humanlike, grille humaine 8 dimensions) a donné {agreement.get('judges_pct', {}).get('humanlike', {}).get('pct', '?')}% en pointant des défauts structurels. L'arbitre a tranché en sa faveur.

**Tu ne régénères PAS from scratch.** Tu corriges SPÉCIFIQUEMENT les défauts identifiés. Le code existant a des forces — garde-les.

## VERDICT DU DA SENIOR (humanlike)
{humanlike_verdict}

## VERDICT FINAL ARBITRE
{arbitrage_verdict}

## SIGNATURE VISUELLE NOMMABLE
{f'Actuelle: "{sig_nommable}"' if sig_nommable else '⚠️ AUCUNE — DOIT être créée. Une signature nommable en 3-5 mots ("Editorial Press SaaS", "Brutalist Tech Warm") doit émerger de cette LP. Pas un kitchen-sink de techniques.'}

## FAIBLESSES À CORRIGER (priorité haute)
{weaknesses_md}

## AI-DEFAULT PATTERNS À ÉLIMINER (interdits absolus dans la version repair)
{ai_patterns_md}

## RAPPELS BRAND (à ne pas violer)
{bd_summary}

## DESIGN GRAMMAR (couche prescriptive — RESPECTER)
{dg_summary}

## HTML ACTUEL À CORRIGER
```html
{current_html[:55000] if len(current_html) > 55000 else current_html}
```

## TON OUTPUT

Régénère le HTML COMPLET en appliquant les corrections ci-dessus. Tu peux :
- Modifier la composition globale (ex: changer asymétrie hero, repenser hiérarchie)
- Remplacer des patterns AI-default par des éléments distinctifs
- Resserrer la voix pour qu'elle soit reconnaissable comme {client.upper()}
- Ajouter une signature visuelle nommable cohérente (UN parti-pris, pas un empilement)
- Activer les principes Cialdini manquants si pointé en weakness
- Éliminer les patterns AI listés ci-dessus

Tu DOIS garder les forces du HTML actuel (les éléments concrets, les chiffres, la structure narrative qui fonctionne) — mais corriger ce que le DA senior a pointé.

Le HTML final doit être auto-contenu, mobile-first, accessible. Pas de markdown, juste le HTML pur.
"""


def run_repair_loop(initial_html: str, args, brand_dna: dict, design_grammar: dict,
                     output_path: pathlib.Path) -> tuple[str, list[dict]]:
    """V26.Z W3 : boucle automatique génération → multi_judge → repair si <threshold.

    Returns:
      (final_html, iterations_log)
      iterations_log = [{iter, score_pct, source, html_size, tokens}, ...]
    """
    # Lazy import — multi-judge has its own heavy deps, keep cold-start light.
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    from gsg_multi_judge import run_multi_judge  # type: ignore  # noqa: E402
    # Imported here (not at module scope) to avoid a cycle with lp_orchestrator
    # which also imports from this module.
    from .lp_orchestrator import call_sonnet  # noqa: E402

    iterations_log = []
    current_html = initial_html

    for it in range(args.max_repairs + 1):
        # Save current iteration HTML to disk for multi_judge to read
        iter_fp = output_path.with_name(output_path.stem + (f".iter{it}" if it > 0 else "") + output_path.suffix)
        iter_fp.parent.mkdir(parents=True, exist_ok=True)
        iter_fp.write_text(current_html)

        print(f"\n══ Repair loop iteration {it} ({iter_fp.name}) ══")

        # Run multi-judge
        mj_result = run_multi_judge(
            iter_fp, args.client,
            threshold=0.7,  # spread threshold for arbitrage trigger (independent of repair threshold)
            verbose=True,
        )
        score_pct = mj_result.get("final_score_pct", 0.0)
        iterations_log.append({
            "iter": it,
            "html_path": str(iter_fp.relative_to(ROOT)) if iter_fp.is_relative_to(ROOT) else str(iter_fp),
            "score_pct": score_pct,
            "source": mj_result.get("final_score_source", "?"),
            "html_size": len(current_html),
            "tokens": mj_result.get("tokens_total", 0),
        })

        # Save multi-judge result for this iteration
        mj_fp = ROOT / "data" / f"_audit_{args.client}_multi_iter{it}.json"
        mj_fp.write_text(json.dumps(mj_result, ensure_ascii=False, indent=2))

        if score_pct >= args.repair_threshold:
            print(f"\n✓ Score {score_pct}% ≥ threshold {args.repair_threshold}% → repair loop done at iter {it}")
            break

        if it >= args.max_repairs:
            print(f"\n⚠️  Max repairs ({args.max_repairs}) atteint — score final {score_pct}% < threshold {args.repair_threshold}%")
            break

        print(f"\n→ Score {score_pct}% < threshold {args.repair_threshold}% — repair iteration {it+1}/{args.max_repairs}")
        repair_prompt = build_repair_prompt(
            current_html=current_html,
            client=args.client,
            multi_judge_result=mj_result,
            brand_dna=brand_dna,
            design_grammar=design_grammar,
        )
        # Save repair prompt for debug
        debug_fp = ROOT / "data" / f"_gsg_repair_prompt_{args.client}_iter{it+1}.md"
        debug_fp.write_text(repair_prompt)
        print(f"  → repair prompt saved : {debug_fp.relative_to(ROOT)} ({len(repair_prompt)} chars)")

        current_html = call_sonnet(repair_prompt, max_tokens=args.max_tokens)
        print(f"✓ Iter {it+1} HTML regenerated ({len(current_html)} chars)")
        # V26.Z P0 : post-process auto également sur chaque iteration repair
        current_html, _ = auto_fix_runtime(current_html, label=f"iter{it+1}")

    return current_html, iterations_log


__all__ = ["build_repair_prompt", "run_repair_loop"]
