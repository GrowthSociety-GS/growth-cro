#!/usr/bin/env python3
"""Smoke-test V27.2-F GSG visual renderer and optional Playwright screenshots."""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.orchestrator import generate_lp


CASES = [
    ("weglot", "lp_listicle", "SaaS teams launching multilingual acquisition pages without breaking SEO."),
    ("weglot", "advertorial", "SaaS marketing leaders who need an editorial native article for cold acquisition."),
    ("japhy", "pdp", "Product buyers evaluating proof, usage clarity and risk reversal."),
    ("stripe", "pricing", "Finance and product teams comparing SaaS pricing before signup."),
]


def _brief(page_type: str, audience: str) -> dict:
    return {
        "objectif": f"Créer une page {page_type} visuellement contrôlée et spécifique.",
        "audience": (
            f"{audience} Peurs principales : perdre du temps, se tromper de solution, "
            "manquer de preuves. Désirs : comprendre vite, comparer clairement, agir sans risque."
        ),
        "angle": (
            "Faire sentir rapidement pourquoi cette offre est différente, pour qui elle est faite, "
            "et quelle prochaine action mérite vraiment l'attention."
        ),
    }


def _output_path(client: str, page_type: str) -> pathlib.Path:
    return ROOT / "deliverables" / "gsg_demo" / f"{client}-{page_type}-v272c.html"


def _qa_prefix(client: str, page_type: str) -> pathlib.Path:
    return ROOT / "deliverables" / "gsg_demo" / f"{client}-{page_type}-v272c"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-screenshots", action="store_true", help="Run Playwright desktop/mobile QA.")
    parser.add_argument("--screenshot-case", action="append", default=[], help="client/page_type to screenshot, e.g. weglot/lp_listicle.")
    args = parser.parse_args()

    failures: list[str] = []
    screenshot_cases = set(args.screenshot_case or [])
    if args.with_screenshots and not screenshot_cases:
        screenshot_cases = {"weglot/lp_listicle", "weglot/advertorial"}

    print("gsg_visual_renderer_v27_2_f=START")
    for client, page_type, audience in CASES:
        out_html = _output_path(client, page_type)
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
            save_html_path=str(out_html),
            verbose=False,
        )
        html = result["html"]
        visual_system = html.count("data-visual-system")
        visual_kinds = html.count("data-visual-kind")
        component_visuals = html.count("visual-module")
        page_shell = f"visual-shell-" in html
        prompt_meta = result.get("prompt_meta") or {}
        visual_meta = prompt_meta.get("visual_intelligence") or {}
        route_meta = prompt_meta.get("creative_route_contract") or {}
        print(
            f"{client}/{page_type}: html={len(html)} visual_system={visual_system} "
            f"visual_kinds={visual_kinds} modules={component_visuals} "
            f"role={visual_meta.get('visual_role')} route={route_meta.get('route_name')}"
        )
        if '<!DOCTYPE html>' not in html or '</html>' not in html:
            failures.append(f"{client}/{page_type}: incomplete html")
        if not visual_system or not page_shell:
            failures.append(f"{client}/{page_type}: missing visual shell/system")
        if visual_kinds < 1:
            failures.append(f"{client}/{page_type}: missing visual kind markers")
        if page_type != "lp_listicle" and component_visuals < 3:
            failures.append(f"{client}/{page_type}: too few component visual modules")
        if (result.get("minimal_gates") or {}).get("audit", {}).get("pass") is not True:
            failures.append(f"{client}/{page_type}: minimal gates failed")
        if route_meta.get("source") != "structured_golden_creative_selector":
            failures.append(f"{client}/{page_type}: structured route selector missing")

        case_id = f"{client}/{page_type}"
        if args.with_screenshots and case_id in screenshot_cases:
            subprocess.run(
                [
                    "node",
                    "scripts/qa_gsg_html.js",
                    str(out_html),
                    str(_qa_prefix(client, page_type)),
                ],
                cwd=ROOT,
                check=True,
            )

    if failures:
        print("gsg_visual_renderer_v27_2_f=FAIL")
        for failure in failures:
            print("ERROR:", failure)
        return 1
    print("gsg_visual_renderer_v27_2_f=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
