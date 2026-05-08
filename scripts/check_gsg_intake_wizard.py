#!/usr/bin/env python3
"""Check the canonical GSG intake/wizard path without API calls."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.core.intake_wizard import build_intake_from_user_request
from moteur_gsg.orchestrator import generate_lp


VALID_WEGLOT_REQUEST = (
    "Je veux générer une LP listicle Weglot en FR pour convertir en signup trial 10 jours. "
    "Audience: Head of Growth / PM / Engineering Lead SaaS B2B 50-500p, site monolingue déjà performant, "
    "prépare l'internationalisation 2026. 3 peurs: backlog dev de 3 mois, SEO multilingue cassé, "
    "qualité traduction auto incohérente. 3 désirs: vitesse, ROI mesurable, qualité brand préservée. "
    "Schwartz: solution_aware. Angle: 10 raisons concrètes pour lesquelles une équipe SaaS devrait "
    "internationaliser son site maintenant avec Weglot, avec schémas produit/process et sans chiffre non sourcé."
)

INCOMPLETE_WEGLOT_REQUEST = "Génère une LP listicle Weglot en FR."


def _assert(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    print("gsg_intake_wizard_v27_2_e=START")

    incomplete = build_intake_from_user_request(INCOMPLETE_WEGLOT_REQUEST)
    print(
        "incomplete_request",
        json.dumps({
            "client": incomplete.request.client_slug,
            "page_type": incomplete.request.page_type,
            "ready": incomplete.ready_to_generate,
            "questions": [q.field for q in incomplete.questions],
        }, ensure_ascii=False),
    )
    _assert(incomplete.request.client_slug == "weglot", "incomplete: client should resolve to weglot", failures)
    _assert(incomplete.request.page_type == "lp_listicle", "incomplete: page_type should resolve to lp_listicle", failures)
    _assert(not incomplete.ready_to_generate, "incomplete: should not be ready", failures)
    _assert(any(q.field == "audience" for q in incomplete.questions), "incomplete: should ask audience", failures)

    valid = build_intake_from_user_request(VALID_WEGLOT_REQUEST)
    print(
        "valid_request",
        json.dumps({
            "client": valid.request.client_slug,
            "url": valid.request.client_url,
            "page_type": valid.request.page_type,
            "lang": valid.request.target_language,
            "ready": valid.ready_to_generate,
            "prompt_inputs": {
                "objective": valid.brief.objective if valid.brief else None,
                "audience_chars": len(valid.brief.audience) if valid.brief else 0,
                "angle_chars": len(valid.brief.angle) if valid.brief else 0,
            },
        }, ensure_ascii=False),
    )
    _assert(valid.ready_to_generate, f"valid: should be ready, errors={valid.validation_errors}", failures)
    _assert(valid.request.client_slug == "weglot", "valid: client should be weglot", failures)
    _assert(valid.request.page_type == "lp_listicle", "valid: page_type should be lp_listicle", failures)
    _assert(valid.request.target_language == "FR", "valid: language should be FR", failures)

    if valid.ready_to_generate and valid.brief:
        result = generate_lp(
            mode=valid.brief.mode,
            client=valid.request.client_slug,
            page_type=valid.brief.page_type,
            brief=valid.brief.to_legacy_brief(),
            target_language=valid.brief.target_language,
            primary_cta_label=valid.request.primary_cta_label,
            primary_cta_href=valid.request.primary_cta_href,
            generation_strategy="controlled",
            copy_fallback_only=True,
            skip_judges=True,
            verbose=False,
        )
        gates = (result.get("minimal_gates") or {}).get("audit") or {}
        html = result.get("html") or ""
        print(
            "valid_render",
            json.dumps({
                "html_chars": len(html),
                "minimal_gate_pass": gates.get("pass"),
                "copy_prompt_chars": result.get("gen", {}).get("copy_prompt_chars"),
            }, ensure_ascii=False),
        )
        _assert("<!DOCTYPE html>" in html and "</html>" in html, "valid render: incomplete html", failures)
        _assert(gates.get("pass") is True, f"valid render: minimal gates failed {gates}", failures)

    if failures:
        print("gsg_intake_wizard_v27_2_e=FAIL")
        for failure in failures:
            print("ERROR:", failure)
        return 1
    print("gsg_intake_wizard_v27_2_e=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
