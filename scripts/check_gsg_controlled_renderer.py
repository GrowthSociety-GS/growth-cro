#!/usr/bin/env python3
"""Smoke-test the canonical GSG controlled renderer without LLM calls."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.orchestrator import generate_lp


def main() -> int:
    result = generate_lp(
        mode="complete",
        client="weglot",
        page_type="lp_listicle",
        brief={
            "objectif": "Convertir trial gratuit",
            "audience": "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p, deja site live monolingue, considere internationalisation, peur de casser le SEO, desir de lancer vite plusieurs marches.",
            "angle": "Listicle editorial en francais, structure controlee, chiffres uniquement sources.",
        },
        target_language="FR",
        primary_cta_label="Tester gratuitement 10 jours",
        primary_cta_href="https://dashboard.weglot.com/register",
        generation_strategy="controlled",
        copy_fallback_only=True,
        skip_judges=True,
        verbose=False,
    )
    html = result["html"]
    plan = result["gen"]["plan"]
    audit = (result.get("minimal_gates") or {}).get("audit") or {}
    doctrine = (result.get("prompt_meta") or {}).get("doctrine_upstream") or {}
    context_pack = (result.get("prompt_meta") or {}).get("context_pack") or {}
    visual = (result.get("prompt_meta") or {}).get("visual_intelligence") or {}
    route = (result.get("prompt_meta") or {}).get("creative_route_contract") or {}
    visual_assets = (result.get("prompt_meta") or {}).get("visual_assets") or []
    print("controlled_renderer=PASS")
    print(f"strategy={result.get('generation_strategy')}")
    print(f"layout={plan.get('layout_name')}")
    print(f"sections={len(plan.get('sections') or [])}")
    print(f"doctrine_criteria={len(doctrine.get('criteria_ids') or [])}")
    print(f"page_type_specific={','.join(doctrine.get('page_type_specific_ids') or []) or 'none'}")
    print(f"business_category={doctrine.get('business_category')}")
    print(f"context_pack={context_pack.get('version')} risks={','.join(context_pack.get('risk_flags') or []) or 'none'}")
    print(
        f"visual_role={visual.get('visual_role')} route={route.get('route_name')} "
        f"route_source={route.get('source')} golden_refs={route.get('golden_ref_count')} techniques={route.get('technique_ref_count')}"
    )
    print(f"visual_assets={','.join(visual_assets) or 'none'}")
    print(f"html_chars={len(html)}")
    print(f"minimal_gate_pass={audit.get('pass')}")
    if "<!DOCTYPE html>" not in html or "</html>" not in html:
        print("ERROR: rendered HTML is incomplete")
        return 1
    if "class=\"reason\"" not in html:
        print("ERROR: listicle reasons missing")
        return 1
    if len(doctrine.get("criteria_ids") or []) < 5:
        print("ERROR: doctrine upstream pack missing")
        return 1
    if not doctrine.get("page_type_specific_ids"):
        print("ERROR: page-type specific criteria missing")
        return 1
    if not context_pack.get("version") or not visual.get("visual_role"):
        print("ERROR: V27.2 context/visual contracts missing")
        return 1
    if route.get("source") != "structured_golden_creative_selector":
        print("ERROR: structured creative route selector missing")
        return 1
    if (route.get("golden_ref_count") or 0) < 1:
        print("ERROR: Golden Bridge references missing from route")
        return 1
    if audit.get("pass") is not True:
        print(f"ERROR: minimal gates failed {audit}")
        return 1
    if not visual_assets:
        print("ERROR: visual assets missing for Weglot smoke test")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
