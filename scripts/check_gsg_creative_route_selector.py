#!/usr/bin/env python3
"""Check V27.2-F structured Golden/Creative route selector without API calls."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.orchestrator import generate_lp


def main() -> int:
    print("gsg_creative_route_selector_v27_2_f=START")
    result = generate_lp(
        mode="complete",
        client="weglot",
        page_type="lp_listicle",
        brief={
            "objectif": "Convertir trial gratuit",
            "audience": (
                "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p, site monolingue deja performant, "
                "peur de casser le SEO multilingue, besoin de vitesse, ROI mesurable et controle brand."
            ),
            "angle": "Listicle editorial premium avec preuve, mecanisme produit et direction visuelle Golden sans chiffre non source.",
        },
        target_language="FR",
        primary_cta_label="Tester gratuitement 10 jours",
        primary_cta_href="https://dashboard.weglot.com/register",
        generation_strategy="controlled",
        copy_fallback_only=True,
        skip_judges=True,
        verbose=False,
    )
    meta = result.get("prompt_meta") or {}
    route = meta.get("creative_route_contract") or {}
    plan = result.get("gen", {}).get("plan") or {}
    plan_route = plan.get("creative_route_contract") or {}
    html = result.get("html") or ""
    payload = {
        "route_name": route.get("route_name"),
        "risk_level": route.get("risk_level"),
        "source": route.get("source"),
        "golden_ref_count": route.get("golden_ref_count"),
        "technique_ref_count": route.get("technique_ref_count"),
        "renderer_overrides": route.get("renderer_overrides"),
        "html_has_route_data": "data-route=" in html,
        "visual_system_version": "gsg-visual-system-v27.2-f" in html,
    }
    print("route_contract", json.dumps(payload, ensure_ascii=False))
    failures: list[str] = []
    if route.get("source") != "structured_golden_creative_selector":
        failures.append("route source should be structured_golden_creative_selector")
    if (route.get("golden_ref_count") or 0) < 1:
        failures.append("route should include compact Golden references")
    if (route.get("technique_ref_count") or 0) < 1:
        failures.append("route should include compact technique references")
    if not route.get("renderer_overrides"):
        failures.append("route should expose renderer_overrides")
    if not plan_route.get("golden_references"):
        failures.append("plan should carry golden_references")
    if "data-route=" not in html or "gsg-visual-system-v27.2-f" not in html:
        failures.append("HTML should expose V27.2-F route/visual-system markers")
    if failures:
        print("gsg_creative_route_selector_v27_2_f=FAIL")
        for failure in failures:
            print("ERROR:", failure)
        return 1
    print("gsg_creative_route_selector_v27_2_f=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
