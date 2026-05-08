"""GSG Best-of-N V26.Z P2 — génère N LPs (1 par route Safe/Premium/Bold) et garde la meilleure.

Réponse au constat empirique des phases précédentes : le mode `auto` du
creative_director (qui choisit UNE route avant la génération) prend des
décisions parfois sous-optimales :
  - Phase 1 W123 (no creative)        : humanlike 62/80
  - E2 mode auto → Safe (Editorial)   : humanlike 57/80 ← regression
  - FINAL Premium (Quiet Luxury)      : humanlike 52/80 ← regression
  - P1SEQ + Premium (sequential)      : humanlike 65/80 ← best so far

Le choix de route a un IMPACT MAJEUR sur le résultat final, et l'arbitre
auto se trompe une fois sur deux. Plus robuste : générer LP pour CHAQUE
route, juger les 3, garder la meilleure.

ARCHITECTURE
============

1. creative_director.generate_routes() → 3 routes (Safe / Premium / Bold)
2. Pour chaque route :
   a. run_sequential_pipeline(creative_route=route)  → HTML
   b. auto_fix_runtime(html)                         → HTML safe rendering
   c. run_multi_judge(html_path, client)             → score
3. Compare les 3 final_score_pct
4. Garde la meilleure → output

Coût estimé : ~$1.50-2.00 par run total (3 × pipeline ~$0.32 + 3 × multi-judge ~$0.20).
Vs mode `auto` : ~$0.50 mais résultat aléatoire. Le X3 vaut le coup pour bench.

Usage CLI :
    python3 skills/growth-site-generator/scripts/gsg_best_of_n.py \\
        --client weglot --page-type listicle \\
        --target-url "https://www.weglot.com" \\
        --context-file ... --copy-hints-file ... \\
        --output deliverables/weglot-best.html \\
        [--routes safe,premium,bold]   # default = toutes les 3

Usage module :
    from gsg_best_of_n import run_best_of_n
    result = run_best_of_n(client="weglot", routes=["safe", "premium", "bold"])
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "captures"
SCRIPTS = ROOT / "skills" / "growth-site-generator" / "scripts"

# Make sibling scripts importable
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from creative_director import generate_routes, render_creative_route_block  # noqa: E402
from gsg_pipeline_sequential import run_sequential_pipeline  # noqa: E402
from gsg_multi_judge import run_multi_judge  # noqa: E402
from fix_html_runtime import fix_html_runtime, detect_runtime_bugs  # noqa: E402


def load_brand_dna(client: str) -> dict:
    fp = DATA / client / "brand_dna.json"
    if not fp.exists():
        sys.exit(f"❌ {fp} not found")
    return json.loads(fp.read_text())


def load_design_grammar(client: str) -> dict:
    dg_dir = DATA / client / "design_grammar"
    if not dg_dir.is_dir():
        return {}
    grammar = {}
    for json_file in ("composition_rules.json", "section_grammar.json",
                      "component_grammar.json", "brand_forbidden_patterns.json",
                      "quality_gates.json", "tokens.json"):
        fp = dg_dir / json_file
        if fp.exists():
            try:
                grammar[json_file.replace(".json", "")] = json.loads(fp.read_text())
            except json.JSONDecodeError:
                pass
    return grammar


def compute_aura_tokens(client: str, energy: float, tonality: float,
                         business: str, registre: str) -> dict:
    """Lance aura_compute en mode B fixé (copie de gsg_generate_lp logic)."""
    import subprocess
    bd_fp = DATA / client / "brand_dna.json"
    out_fp = ROOT / "data" / f"_aura_{client}.json"
    cmd = [
        "python3", str(SCRIPTS / "aura_compute.py"),
        "--brand-dna", str(bd_fp),
        "--energy", str(energy),
        "--tonality", str(tonality),
        "--business", business,
        "--registre", registre,
        "--output", str(out_fp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(f"❌ aura_compute failed: {r.stderr}")
    return json.loads(out_fp.read_text())


def run_best_of_n(client: str, page_type: str = "listicle",
                  target_url: str = "",
                  business_context: str = "", copy_hints: str = "",
                  routes_filter: Optional[list[str]] = None,
                  energy: float = 4.0, tonality: float = 3.0,
                  business: str = "saas", registre: str = "editorial",
                  verbose: bool = True) -> dict:
    """Génère N LPs (1 par route) + juge + garde la meilleure.

    Args:
      routes_filter: liste de risk_levels à tester (ex: ['safe', 'premium', 'bold']).
                     Default = les 3 toutes.

    Returns:
      {
        "best_html": str,
        "best_route_name": str,
        "best_score_pct": float,
        "all_results": [
          {
            "route_name": "...", "risk_level": "safe|premium|bold",
            "html_path": "...", "multi_judge_result": {...},
            "final_score_pct": float, "humanlike_score": float
          }, ...
        ],
        "tokens_total": int
      }
    """
    routes_filter = routes_filter or ["safe", "premium", "bold"]

    if verbose:
        print(f"\n══════════════════════════════════════════════════════════")
        print(f"  GSG Best-of-N V26.Z P2 — {client} / {page_type}")
        print(f"  Routes to test : {', '.join(routes_filter)}")
        print(f"══════════════════════════════════════════════════════════\n")

    # Load static inputs
    brand_dna = load_brand_dna(client)
    design_grammar = load_design_grammar(client)
    aura = compute_aura_tokens(client, energy, tonality, business, registre)
    if verbose:
        print(f"✓ Loaded brand_dna + design_grammar ({len(design_grammar)} files) + aura")

    # Generate 3 routes (1 call Sonnet)
    if verbose:
        print(f"\n[Routes generation] 1 call Sonnet → 3 routes...")
    routes_data = generate_routes(
        brand_dna, design_grammar, business_context, page_type,
        client, target_url, verbose=verbose,
    )
    routes_fp = ROOT / "data" / f"_routes_{client}.json"
    routes_fp.write_text(json.dumps(routes_data, ensure_ascii=False, indent=2))
    available_routes = {r.get("risk_level"): r for r in (routes_data.get("routes") or [])}
    if verbose:
        for risk, r in available_routes.items():
            print(f"  [{risk:8s}] {r.get('name', '?')}")

    # For each requested route, generate via sequential pipeline + judge
    all_results = []
    tokens_total = 0
    for risk_level in routes_filter:
        route = available_routes.get(risk_level)
        if not route:
            if verbose:
                print(f"\n⚠️  No route with risk_level={risk_level} found — skipping")
            continue

        route_name = route.get("name", f"unknown_{risk_level}")
        slug = "".join(c if c.isalnum() else "_" for c in route_name.lower())[:40]

        if verbose:
            print(f"\n══════════════════════════════════════════════════════════")
            print(f"  ROUTE [{risk_level.upper()}] : \"{route_name}\"")
            print(f"══════════════════════════════════════════════════════════")

        # Stage : sequential pipeline with this specific route
        try:
            seq_result = run_sequential_pipeline(
                client=client, brand_dna=brand_dna, design_grammar=design_grammar,
                aura=aura, creative_route=route,
                business_context=business_context, copy_hints=copy_hints,
                page_type=page_type, target_url=target_url, verbose=verbose,
            )
            html = seq_result["html_final"]
            tokens_total += seq_result["telemetry"]["tokens_total"]
        except Exception as e:
            if verbose:
                print(f"  ❌ Pipeline failed for {route_name}: {e}")
            all_results.append({
                "route_name": route_name, "risk_level": risk_level,
                "error": str(e)[:200],
                "final_score_pct": 0.0, "humanlike_score": 0.0,
            })
            continue

        # Auto-fix rendering
        html, _ = fix_html_runtime(html, inject_js=True, fix_reveal_pattern=True)

        # Save HTML for this route
        html_fp = ROOT / "deliverables" / f"_bestof_{client}_{risk_level}_{slug}.html"
        html_fp.parent.mkdir(parents=True, exist_ok=True)
        html_fp.write_text(html)
        if verbose:
            print(f"\n  ✓ HTML generated for [{risk_level}] : {html_fp.relative_to(ROOT)}")

        # Multi-judge
        if verbose:
            print(f"\n  [Multi-judge] evaluating {route_name}...")
        try:
            mj_result = run_multi_judge(html_fp, client, threshold=0.7,
                                          skip_arbitrage=False, verbose=verbose)
            tokens_total += mj_result.get("tokens_total", 0)
        except Exception as e:
            if verbose:
                print(f"  ⚠️  Multi-judge failed: {e}")
            mj_result = {"final_score_pct": 0.0, "error": str(e)[:200]}

        # Save per-route audit
        audit_fp = ROOT / "data" / f"_bestof_{client}_{risk_level}_audit.json"
        audit_fp.write_text(json.dumps(mj_result, ensure_ascii=False, indent=2))

        # Extract humanlike score for tie-break / display
        humanlike_score = (
            (mj_result.get("agreement") or {}).get("judges_pct", {})
            .get("humanlike", {}).get("pct", 0.0)
        )
        all_results.append({
            "route_name": route_name,
            "risk_level": risk_level,
            "html_path": str(html_fp.relative_to(ROOT)),
            "audit_path": str(audit_fp.relative_to(ROOT)),
            "final_score_pct": mj_result.get("final_score_pct", 0.0),
            "humanlike_score": humanlike_score,
            "implementation_severity": (mj_result.get("implementation_check") or {}).get("broken_severity", "?"),
            "needs_arbitrage": mj_result.get("needs_arbitrage", False),
        })

    # Find best
    if not all_results:
        return {"error": "no_results", "all_results": [], "tokens_total": tokens_total}

    # Sort by final_score_pct desc, tie-break by humanlike_score desc
    sorted_results = sorted(
        [r for r in all_results if "error" not in r],
        key=lambda r: (-r["final_score_pct"], -r["humanlike_score"]),
    )
    best = sorted_results[0] if sorted_results else None

    if verbose:
        print(f"\n══════════════════════════════════════════════════════════")
        print(f"  BEST-OF-N COMPARISON")
        print(f"══════════════════════════════════════════════════════════")
        print(f"\n  {'Route':40s} {'Final pct':>10s} {'Humanlike':>10s} {'Impl':>10s}")
        print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*10}")
        for r in all_results:
            if "error" in r:
                print(f"  {r['route_name'][:40]:40s} {'ERROR':>10s} {'-':>10s} {'-':>10s}")
            else:
                marker = " ⭐" if r is best else "  "
                print(f"  {r['route_name'][:40]:40s} {r['final_score_pct']:>9.1f}% {r['humanlike_score']:>9.1f}% {r['implementation_severity']:>10s}{marker}")
        print()
        if best:
            print(f"  ⭐ WINNER : \"{best['route_name']}\" ({best['risk_level']})")
            print(f"     Final score : {best['final_score_pct']}%")
            print(f"     Humanlike   : {best['humanlike_score']}%")
            print(f"     HTML        : {best['html_path']}")

    if best:
        best_html = (ROOT / best["html_path"]).read_text()
    else:
        best_html = ""

    return {
        "best_html": best_html,
        "best_route_name": best["route_name"] if best else None,
        "best_risk_level": best["risk_level"] if best else None,
        "best_score_pct": best["final_score_pct"] if best else 0.0,
        "best_humanlike": best["humanlike_score"] if best else 0.0,
        "all_results": all_results,
        "routes_data": routes_data,
        "tokens_total": tokens_total,
        "judged_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", default="listicle")
    ap.add_argument("--target-url", default="")
    ap.add_argument("--context-file")
    ap.add_argument("--copy-hints-file")
    ap.add_argument("--output", required=True,
                    help="Path output for the WINNING HTML")
    ap.add_argument("--routes", default="safe,premium,bold",
                    help="Comma-sep risk_levels to test (default: safe,premium,bold)")
    ap.add_argument("--energy", type=float, default=4.0)
    ap.add_argument("--tonality", type=float, default=3.0)
    ap.add_argument("--business", default="saas")
    ap.add_argument("--registre", default="editorial")
    args = ap.parse_args()

    business_context = ""
    if args.context_file and pathlib.Path(args.context_file).exists():
        business_context = pathlib.Path(args.context_file).read_text()
    copy_hints = ""
    if args.copy_hints_file and pathlib.Path(args.copy_hints_file).exists():
        copy_hints = pathlib.Path(args.copy_hints_file).read_text()

    routes_filter = [r.strip() for r in args.routes.split(",") if r.strip()]

    result = run_best_of_n(
        client=args.client, page_type=args.page_type,
        target_url=args.target_url,
        business_context=business_context, copy_hints=copy_hints,
        routes_filter=routes_filter,
        energy=args.energy, tonality=args.tonality,
        business=args.business, registre=args.registre,
        verbose=True,
    )

    # Save winner HTML
    out_fp = pathlib.Path(args.output)
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(result["best_html"])

    # Save full report
    report_fp = ROOT / "data" / f"_bestof_{args.client}_report.json"
    report_lite = {k: v for k, v in result.items() if k != "best_html"}
    report_fp.write_text(json.dumps(report_lite, ensure_ascii=False, indent=2))

    print(f"\n══════════════════════════════════════════════════════════")
    print(f"  Winner HTML saved : {out_fp}")
    print(f"  Full report saved : {report_fp.relative_to(ROOT)}")
    print(f"  Tokens total       : {result['tokens_total']} (~${result['tokens_total'] * 3 / 1e6:.3f})")
    print(f"══════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
