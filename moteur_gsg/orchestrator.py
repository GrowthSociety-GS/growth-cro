"""moteur_gsg.orchestrator — canonical public GSG API.

Point d'entrée unique pour générer une LP, quel que soit le mode :

    from moteur_gsg.orchestrator import generate_lp
    result = generate_lp(
        mode="complete",        # complete | replace | extend | elevate | genesis
        client="weglot",
        page_type="lp_listicle",
        brief={
            "objectif": "Convertir trial gratuit",
            "audience": "Head of Growth SaaS B2B",
            "angle": "Listicle éditorial enquête Growth Society",
        },
    )
    # result["html"]      = HTML LP livrable
    # result["audit"]     = audit doctrine (alias)
    # result["minimal_gates"] = audit déterministe CTA/langue/fonts/preuves
    # result["telemetry"] = tokens, coût, wall time

──────────────────────────────────────────────────────────────────────────────
V26.AG (2026-05-04) — GSG rollback minimal :
──────────────────────────────────────────────────────────────────────────────
- `complete` revient sur Mode 1 V26.AA single-pass court : baseline la moins cassée.
- `persona` garde explicitement V26.AC/AD/AE persona_narrator pour forensic/comparaison.
- Le pipeline V26.AF/AG conversationnel reste disponible via `scripts/run_gsg_full_pipeline.py`,
  mais n'est plus le chemin par défaut tant que le rendu visuel reste trop blanc.

V26.AH (2026-05-04) — Day 5 minimal stable :
- `complete` garde le single-pass court mais ajoute des gates déterministes locaux
  pour la langue, le CTA, les fonts et les preuves numériques. Pas de polish LLM
  sur HTML complet.

V27 canonical (2026-05-05) :
- `moteur_gsg` is the only public GSG engine.
- `skills/gsg` is the only public GSG skill.
- `skills/growth-site-generator/scripts` is a frozen legacy lab and can only be
  consumed through explicit adapters in `moteur_gsg.core.legacy_lab_adapters`.
- Run `python3 scripts/check_gsg_canonical.py` before GSG reconstruction work.
──────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations



# Modes registry V26.AE — 5 modes type business
_MODE_REGISTRY = {
    # V26.AH : Mode 1 V26.AA single-pass court + minimal deterministic gates.
    "complete": "moteur_gsg.modes.mode_1_complete:run_mode_1_complete",
    "complete_v26aa": "moteur_gsg.modes.mode_1_complete:run_mode_1_complete",
    # V26.AC/AD/AE persona narrator remains opt-in, not default.
    "persona": "moteur_gsg.modes.mode_1_persona_narrator:run_mode_1_persona_narrator",  # alias explicite
    "replace": "moteur_gsg.modes.mode_2_replace:run_mode_2_replace",
    "extend": "moteur_gsg.modes.mode_3_extend:run_mode_3_extend",
    "elevate": "moteur_gsg.modes.mode_4_elevate:run_mode_4_elevate",
    "genesis": "moteur_gsg.modes.mode_5_genesis:run_mode_5_genesis",
}


def _resolve_mode_callable(mode: str):
    """Charge le callable du mode demandé."""
    spec = _MODE_REGISTRY.get(mode)
    if not spec:
        available = ", ".join(_MODE_REGISTRY.keys()) or "(aucun mode disponible)"
        raise ValueError(f"Mode '{mode}' non supporté Sprint 3. Disponibles : {available}")
    module_path, func_name = spec.split(":")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, func_name)


def generate_lp(
    mode: str,
    client: str,
    page_type: str,
    brief: dict,
    **kwargs,
) -> dict:
    """API publique pour générer une LP.

    Args:
      mode: "complete" | "replace" | "extend" | "elevate" | "genesis"
      client: slug du client (doit avoir brand_dna.json sauf mode genesis)
      page_type: ex "lp_listicle", "home", "pdp", "lp_sales"
      brief: dict avec keys mode-specific (cf design doc V26.AA §3)
      kwargs: options propagées au mode (n_critical, save_html_path, ...)

    Returns: dict {html, audit, gen, telemetry, ...} cf mode_1_complete.run_mode_1_complete

    Raises:
      ValueError si mode non supporté
    """
    runner = _resolve_mode_callable(mode)
    return runner(client=client, page_type=page_type, brief=brief, **kwargs)


def list_supported_modes() -> list[str]:
    """Retourne la liste des modes implémentés actuellement."""
    return list(_MODE_REGISTRY.keys())


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="complete")
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", required=True)
    ap.add_argument("--objectif", required=True)
    ap.add_argument("--audience", required=True)
    ap.add_argument("--angle", required=True)
    ap.add_argument("--save-html")
    ap.add_argument("--save-audit")
    ap.add_argument("--target-language", default="FR")
    ap.add_argument("--primary-cta-label")
    ap.add_argument("--primary-cta-href")
    ap.add_argument("--generation-strategy", choices=["controlled", "single_pass"], default="controlled")
    ap.add_argument("--copy-fallback-only", action="store_true")
    ap.add_argument("--skip-judges", action="store_true")
    args = ap.parse_args()

    brief = {"objectif": args.objectif, "audience": args.audience, "angle": args.angle}
    out = generate_lp(
        mode=args.mode, client=args.client, page_type=args.page_type, brief=brief,
        save_html_path=args.save_html, save_audit_path=args.save_audit,
        target_language=args.target_language,
        primary_cta_label=args.primary_cta_label,
        primary_cta_href=args.primary_cta_href,
        generation_strategy=args.generation_strategy,
        copy_fallback_only=args.copy_fallback_only,
        skip_judges=args.skip_judges,
    )
    if not args.save_html:
        print(out["html"][:500])
