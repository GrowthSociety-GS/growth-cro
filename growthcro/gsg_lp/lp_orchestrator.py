"""GSG legacy lab — CLI entry point + Sonnet text-call wrapper.

Two pieces:

  * ``call_sonnet(prompt, max_tokens=16000)`` — single-prompt Sonnet
    call (text only). Streams when ``max_tokens > 16000``.
  * ``main()`` — argparse CLI matching the legacy
    ``skills/growth-site-generator/scripts/gsg_generate_lp.py`` flags
    one-for-one. Steps:
      1. Load brand_dna / design_grammar / AURA / golden bridge.
      2. Optional Creative Director (3 routes + selection).
      3. Either sequential pipeline (P1, 4 stages) OR mega-prompt
         one-shot (legacy default).
      4. Auto-fix runtime bugs (P0).
      5. Optional auto-repair loop (W3 — multi-judge → repair).

Splits out of ``gsg_generate_lp.py`` (issue #8). Path constants come
from ``data_loaders``; the mega-prompt assembler lives in
``mega_prompt_builder``; the repair loop in ``repair_loop``.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .data_loaders import (
    ROOT,
    SCRIPTS,
    auto_fix_runtime,
    compute_aura_tokens,
    golden_bridge_prompt,
    load_brand_dna,
    load_design_grammar,
)
from .mega_prompt_builder import (
    _CREATIVE_DIRECTOR_AVAILABLE,
    build_mega_prompt,
    cd_generate_routes,
    cd_select_route,
)
from .repair_loop import run_repair_loop


SONNET_MODEL = "claude-sonnet-4-5-20250929"


def call_sonnet(prompt: str, max_tokens: int = 16000) -> str:
    """Appelle Sonnet pour générer le HTML. Streaming si max_tokens > 16K."""
    import anthropic
    client = anthropic.Anthropic()
    print(f"  → Sonnet call (max_tokens={max_tokens}, prompt={len(prompt)} chars, streaming={max_tokens > 16000}) ...", flush=True)
    if max_tokens > 16000:
        # Streaming mandatory pour > 16K tokens
        text_chunks = []
        in_tokens = out_tokens = 0
        stop_reason = None
        with client.messages.stream(
            model=SONNET_MODEL,
            max_tokens=max_tokens,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for chunk in stream.text_stream:
                text_chunks.append(chunk)
            final = stream.get_final_message()
            in_tokens = final.usage.input_tokens
            out_tokens = final.usage.output_tokens
            stop_reason = final.stop_reason
        raw = "".join(text_chunks)
        print(f"  ← Sonnet streaming: in={in_tokens} out={out_tokens} stop_reason={stop_reason}", flush=True)
    else:
        msg = client.messages.create(
            model=SONNET_MODEL,
            max_tokens=max_tokens,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        print(f"  ← Sonnet response: in={msg.usage.input_tokens} out={msg.usage.output_tokens}"
              f" stop_reason={msg.stop_reason}", flush=True)
    # Strip markdown fences if any
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("html\n"):
            text = text[5:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-legacy-lab", action="store_true",
                    help="Required acknowledgement: this V26.Z mega-prompt script is frozen legacy lab. Use moteur_gsg/orchestrator.py for canonical GSG.")
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", default="listicle")
    ap.add_argument("--energy", type=float, default=4.0)
    ap.add_argument("--tonality", type=float, default=3.0)
    ap.add_argument("--business", default="saas")
    ap.add_argument("--registre", default="editorial")
    ap.add_argument("--target-url", default="")
    ap.add_argument("--context-file", help="Path to .md/.txt with business audit context")
    ap.add_argument("--copy-hints-file", help="Path to .md with copy hints (10 raisons brief, etc.)")
    ap.add_argument("--reference-html", help="Path to HTML reference (e.g. concurrent version) à dépasser")
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-tokens", type=int, default=16000)
    # V26.Z W3 : auto-repair flags (opt-in, default off pour rétrocompat)
    ap.add_argument("--auto-repair", action="store_true",
                    help="V26.Z W3 : si activé, lance multi_judge après génération et "
                         "re-génère jusqu'à --repair-threshold ou --max-repairs.")
    ap.add_argument("--repair-threshold", type=float, default=70.0,
                    help="Score pct multi-judge final en dessous duquel on déclenche un repair (default 70)")
    ap.add_argument("--max-repairs", type=int, default=2,
                    help="Nombre max d'itérations de repair (default 2 → 3 calls Sonnet max au pire)")
    # V26.Z E2 : Creative Director multi-routes (opt-in, force une thèse visuelle nommable)
    ap.add_argument("--creative-mode", choices=["off", "auto", "safe", "premium", "bold", "custom"],
                    default="off",
                    help="V26.Z E2 : génère 3 routes nommées + sélectionne avant le mega-prompt. "
                         "off=skip (legacy V26.Z W2 sans creative director). "
                         "auto=Sonnet arbitre. safe/premium/bold=Mathis choisit explicitement. "
                         "custom=charge route depuis --custom-route-file.")
    ap.add_argument("--custom-route-file",
                    help="Path JSON pour route custom (mode=custom uniquement)")
    # V26.Z P1 : Sequential pipeline (4 stages chaînés vs mega-prompt one-shot)
    ap.add_argument("--sequential", action="store_true",
                    help="V26.Z P1 : utilise le pipeline 4 stages (Strategy → Copy → "
                         "Composer → Polish) au lieu du mega-prompt one-shot. Chaque stage "
                         "produit un artefact validable. Coût similaire ~$0.30 mais plus "
                         "diciplinaire.")
    args = ap.parse_args()

    if not args.allow_legacy_lab:
        sys.exit(
            "❌ FROZEN LEGACY LAB: gsg_generate_lp.py is no longer a public GSG entrypoint.\n"
            "Use `moteur_gsg.orchestrator.generate_lp()` or `scripts/run_gsg_full_pipeline.py --generation-path minimal`.\n"
            "For forensic reproduction only, re-run with `--allow-legacy-lab`."
        )

    print(f"\n══ GSG Generate LP — {args.client} / {args.page_type} ══\n")
    brand_dna = load_brand_dna(args.client)
    print("✓ Brand DNA loaded")

    design_grammar = load_design_grammar(args.client)
    if design_grammar:
        print(f"✓ Design Grammar V30 loaded ({len(design_grammar)} prescriptive files: {', '.join(design_grammar.keys())})")
    else:
        print(f"⚠️  No design_grammar/ found for {args.client} — degraded mode (brand_dna only)")

    aura = compute_aura_tokens(args.client, args.energy, args.tonality, args.business, args.registre)
    print("✓ AURA computed (vector + palette + typo + motion)")

    golden = golden_bridge_prompt(aura["vector"], top=5)
    print(f"✓ Golden Design Bridge ({len(golden)} chars)")

    business_context = ""
    if args.context_file and pathlib.Path(args.context_file).exists():
        business_context = pathlib.Path(args.context_file).read_text()
    copy_hints = ""
    if args.copy_hints_file and pathlib.Path(args.copy_hints_file).exists():
        copy_hints = pathlib.Path(args.copy_hints_file).read_text()
    reference_html = ""
    if args.reference_html and pathlib.Path(args.reference_html).exists():
        reference_html = pathlib.Path(args.reference_html).read_text()
        print(f"✓ Reference HTML loaded ({len(reference_html)} chars) — Sonnet doit le surpasser")

    # V26.Z E2 : Creative Director — génère 3 routes nommées + sélectionne
    creative_route = None
    route_selection_meta = None
    if args.creative_mode != "off":
        if not _CREATIVE_DIRECTOR_AVAILABLE:
            print("⚠️  --creative-mode demandé mais creative_director.py introuvable — skipping")
        else:
            print(f"\n══ Creative Director (mode={args.creative_mode}) ══")
            if args.creative_mode == "custom":
                custom_path = pathlib.Path(args.custom_route_file) if args.custom_route_file else None
                if not custom_path or not custom_path.exists():
                    sys.exit(f"❌ --creative-mode custom requires --custom-route-file (got: {custom_path})")
                custom_route = json.loads(custom_path.read_text())
                creative_route = custom_route
                route_selection_meta = {
                    "mode": "custom", "confidence": 1.0,
                    "reason": f"Custom route loaded from {custom_path.name}",
                    "warning": None,
                }
                print(f"✓ Custom route loaded: {creative_route.get('name', '?')}")
            else:
                # Generate 3 routes (Safe + Premium + Bold)
                print("[1/2] Generate 3 routes...")
                routes_data = cd_generate_routes(
                    brand_dna, design_grammar, business_context,
                    args.page_type, args.client, args.target_url
                )
                routes_fp = ROOT / "data" / f"_routes_{args.client}.json"
                routes_fp.write_text(json.dumps(routes_data, ensure_ascii=False, indent=2))
                print(f"  ✓ 3 routes generated, saved to {routes_fp.relative_to(ROOT)}")
                for r in routes_data.get("routes", []):
                    print(f"    [{r.get('risk_level', '?'):8s}] {r.get('name', '?')}")

                # Select route (auto Sonnet, ou explicit safe/premium/bold)
                print(f"\n[2/2] Select route (mode={args.creative_mode})...")
                selection = cd_select_route(
                    routes_data, brand_dna, business_context,
                    mode=args.creative_mode,
                )
                creative_route = selection["route"]
                route_selection_meta = selection["selection_meta"]
                sel_fp = ROOT / "data" / f"_route_selected_{args.client}.json"
                sel_fp.write_text(json.dumps(selection, ensure_ascii=False, indent=2))
                print(f"  ✓ Selected: \"{creative_route.get('name')}\" (risk={creative_route.get('risk_level')})")
                print(f"    Confidence: {route_selection_meta.get('confidence')}")
                print(f"    Reason: {route_selection_meta.get('reason')[:200]}")
                if route_selection_meta.get("warning"):
                    print(f"    ⚠️  {route_selection_meta['warning']}")

    # V26.Z P1 — Sequential pipeline (option) vs mega-prompt one-shot (legacy)
    if args.sequential:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        try:
            from gsg_pipeline_sequential import run_sequential_pipeline  # type: ignore
        except ImportError as e:
            sys.exit(f"❌ --sequential requires gsg_pipeline_sequential.py : {e}")
        print("\n══ Sequential pipeline (P1, 4 stages) ══")
        seq_result = run_sequential_pipeline(
            client=args.client, brand_dna=brand_dna, design_grammar=design_grammar,
            aura=aura, creative_route=creative_route,
            business_context=business_context, copy_hints=copy_hints,
            page_type=args.page_type, target_url=args.target_url or "",
            verbose=True,
        )
        html = seq_result["html_final"]
        # Save telemetry
        telem_fp = ROOT / "data" / f"_pipeline_{args.client}_telemetry.json"
        telem_fp.write_text(json.dumps(seq_result["telemetry"], ensure_ascii=False, indent=2))
        print(f"\n✓ Sequential pipeline complete : tokens_total={seq_result['telemetry']['tokens_total']}")
        print(f"  → telemetry saved : {telem_fp.relative_to(ROOT)}")
    else:
        # Mega-prompt one-shot (legacy)
        prompt = build_mega_prompt(
            client=args.client, brand_dna=brand_dna, aura=aura, golden_prompt=golden,
            page_type=args.page_type, business_context=business_context,
            copy_hints=copy_hints, target_url=args.target_url or "",
            reference_competitor_html=reference_html,
            design_grammar=design_grammar,
            creative_route=creative_route,
            route_selection_meta=route_selection_meta,
        )
        print(f"✓ Mega-prompt assembled ({len(prompt)} chars)")
        # Save prompt for debug
        debug_fp = ROOT / "data" / f"_gsg_prompt_{args.client}.md"
        debug_fp.write_text(prompt)
        print(f"  → debug prompt saved : {debug_fp.relative_to(ROOT)}")

        html = call_sonnet(prompt, max_tokens=args.max_tokens)

    print(f"✓ HTML generated ({len(html)} chars · {html.count(chr(10))+1} lines)")

    # V26.Z P0 : post-process auto rendering bugs (counter à 0, reveal-class, opacity 0)
    # → garantit un rendu visible peu importe ce que Sonnet a généré.
    html, fix_report = auto_fix_runtime(html, label="iter0")

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    # V26.Z W3 : si --auto-repair, on entre dans la boucle multi_judge → repair → ...
    if args.auto_repair:
        print(f"\n══ Auto-repair activé (threshold={args.repair_threshold}%, max_repairs={args.max_repairs}) ══")
        final_html, iter_log = run_repair_loop(html, args, brand_dna, design_grammar, out)
        out.write_text(final_html)
        # Save iterations log
        log_fp = ROOT / "data" / f"_gsg_iter_log_{args.client}.json"
        log_fp.write_text(json.dumps({
            "client": args.client,
            "page_type": args.page_type,
            "iterations": iter_log,
            "best_iter": max(range(len(iter_log)), key=lambda i: iter_log[i]["score_pct"]),
            "final_iter": len(iter_log) - 1,
            "threshold": args.repair_threshold,
        }, ensure_ascii=False, indent=2))
        print("\n══ Repair loop summary ══")
        for entry in iter_log:
            mark = "✓" if entry["score_pct"] >= args.repair_threshold else "✗"
            print(f"  {mark} iter {entry['iter']}: {entry['score_pct']}% ({entry['html_size']} chars, {entry['tokens']} tokens)")
        print(f"\n  Iter log saved: {log_fp.relative_to(ROOT)}")
    else:
        out.write_text(html)

    print(f"\n✓ Saved : {out}")
    print(f"  Open : open {out}")


__all__ = ["call_sonnet", "main", "SONNET_MODEL"]


if __name__ == "__main__":
    main()
