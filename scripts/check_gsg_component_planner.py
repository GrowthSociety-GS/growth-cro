#!/usr/bin/env python3
"""Smoke-test V27.2-B GSG component planner without LLM calls."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.orchestrator import generate_lp


CASES = [
    ("weglot", "lp_listicle", "SaaS teams launching multilingual acquisition pages without breaking SEO."),
    ("weglot", "advertorial", "SaaS marketing leaders who need an editorial native article for cold acquisition."),
    ("weglot", "lp_sales", "SaaS growth and product teams comparing website translation operating models."),
    ("weglot", "lp_leadgen", "B2B marketers considering a guided multilingual website assessment."),
    ("weglot", "home", "SaaS buyers who need a clear product-led homepage story."),
    ("japhy", "pdp", "Pet owners evaluating a product page with proof, usage clarity and risk reversal."),
    ("stripe", "pricing", "Finance and product teams comparing SaaS pricing options before signup."),
]


def _brief(page_type: str, audience: str) -> dict:
    return {
        "objectif": f"Créer une page {page_type} contrôlée et spécifique.",
        "audience": (
            f"{audience} Peurs principales : perdre du temps, se tromper de solution, "
            "manquer de preuves. Désirs principaux : comprendre vite, comparer clairement, agir sans risque."
        ),
        "angle": (
            "Transformer le contexte stratégique en composants précis : promesse, mécanisme, preuves, "
            "objections et CTA unique, sans laisser le LLM inventer la structure."
        ),
    }


def main() -> int:
    failures = []
    print("gsg_component_planner_v27_2=START")
    for client, page_type, audience in CASES:
        result = generate_lp(
            mode="complete",
            client=client,
            page_type=page_type,
            brief=_brief(page_type, audience),
            target_language="FR",
            primary_cta_label="Démarrer gratuitement",
            primary_cta_href="#start",
            generation_strategy="controlled",
            copy_fallback_only=True,
            skip_judges=True,
            verbose=False,
        )
        html = result["html"]
        plan = result["gen"]["plan"]
        audit = (result.get("minimal_gates") or {}).get("audit") or {}
        pattern_pack = plan.get("pattern_pack") or {}
        sections = plan.get("sections") or []
        page_specific = ((result.get("prompt_meta") or {}).get("doctrine_upstream") or {}).get("page_type_specific_ids") or []
        layout = plan.get("layout_name")
        component_count = len([s for s in sections if s.get("id") not in {"hero", "footer", "final_cta", "byline"}])
        has_component_markup = "component-section" in html if page_type != "lp_listicle" else "class=\"reason\"" in html
        print(
            f"{client}/{page_type}: layout={layout} sections={len(sections)} "
            f"components={component_count} specific={','.join(page_specific) or 'none'} "
            f"cro_patterns={len(pattern_pack.get('cro_patterns') or [])} gates={audit.get('pass')}"
        )
        if "<!DOCTYPE html>" not in html or "</html>" not in html:
            failures.append(f"{client}/{page_type}: incomplete html")
        if len(sections) < 5:
            failures.append(f"{client}/{page_type}: too few sections")
        if not page_specific:
            failures.append(f"{client}/{page_type}: missing page-type criteria")
        if not has_component_markup:
            failures.append(f"{client}/{page_type}: missing expected renderer markup")
        if not audit.get("pass"):
            failures.append(f"{client}/{page_type}: minimal gates failed")
    if failures:
        print("gsg_component_planner_v27_2=FAIL")
        for failure in failures:
            print("ERROR:", failure)
        return 1
    print("gsg_component_planner_v27_2=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
