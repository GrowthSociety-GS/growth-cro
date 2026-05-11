"""Mode 1 COMPLETE — canonical GSG autonomous LP generation.

V26.AG note (2026-05-04) :
  This file was restored from `_archive/legacy_pre_v26ae_2026-05-04/` after the
  V26.AF sequential/persona path proved visually too defensive in empirical
  Weglot tests.

V26.AH Day 5 note:
  Minimal guards now make language, CTA, fonts, and numeric proof discipline
  deterministic after the single generation call. No LLM polish over full HTML.

V27 note:
  Default generation_strategy is now `controlled`: deterministic planner,
  pattern library, design tokens, bounded JSON copy, controlled renderer.
  `single_pass` remains available as an explicit rollback path.

Use case (~30-40% des cas business attendus) :
  Le client a un site existant. Il veut une LP nouvelle d'un type qu'il n'a
  pas dans son écosystème (ex: lp_listicle, advertorial, lp_sales).

Inputs :
  - client (slug) : doit avoir un brand_dna.json déjà capturé
  - page_type : ex "lp_listicle", "lp_sales", "pdp"
  - brief : dict {objectif, audience, angle} (3 questions courtes)

Pipeline :
  1. Load brand_dna (si absent : error explicit)
  2. Build deterministic plan + design tokens
  3. Ask LLM for bounded copy JSON only
  4. Render controlled HTML/CSS + deterministic minimal gates
  5. Run multi-judge (doctrine + humanlike + impl_check) unless skipped
  6. Return audit complet + HTML

Output :
  - HTML LP (deliverable)
  - Audit JSON (doctrine V3.2 par critère + humanlike + impl_check)
  - Telemetry (tokens, coût, temps)

Coût attendu : ~$0.30-0.50 par run total (génération $0.10-0.15 + multi-judge
$0.20-0.30).
"""
from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

from ..core.brand_intelligence import load_brand_dna, has_brand_dna, get_brand_summary
from ..core.prompt_assembly import build_mode1_prompt
from ..core.pipeline_single_pass import apply_runtime_fixes, single_pass
from ..core.design_grammar_loader import load_design_grammar
from ..core.minimal_guards import build_minimal_constraints, apply_minimal_postprocess
from ..core.context_pack import build_generation_context_pack
from ..core.creative_route_selector import build_structured_creative_route_contract
from ..core.design_tokens import build_design_tokens, load_aura_tokens
from ..core.doctrine_planner import build_doctrine_pack
from ..core.planner import build_page_plan
from ..core.copy_writer import call_copy_llm, fallback_copy_from_plan
from ..core.page_renderer_orchestrator import render_controlled_page
from ..core.visual_intelligence import build_visual_intelligence_pack
from ..core.legacy_lab_adapters import (
    LegacyLabUnavailable,
    generate_creative_routes,
    render_creative_route_block,
    select_creative_route,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
CAPTURES = ROOT / "data" / "captures"


def _asset_ref_for_html(asset_path: pathlib.Path, save_html_path: str | None) -> str:
    """Return a browser-usable local asset reference for rendered deliverables."""
    if save_html_path:
        out_parent = pathlib.Path(save_html_path)
        if not out_parent.is_absolute():
            out_parent = ROOT / out_parent
        rel = pathlib.Path(asset_path).resolve().relative_to(ROOT)
        return pathlib.Path("..", rel).as_posix() if out_parent.parent == ROOT / "deliverables" else pathlib.Path(
            os.path.relpath(asset_path, out_parent.parent)
        ).as_posix()
    try:
        return asset_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return asset_path.as_posix()


def _select_visual_assets(client: str, page_type: str | None = None, save_html_path: str | None = None) -> dict[str, str]:
    """Select deterministic brand/product screenshots for the controlled renderer."""
    assets: dict[str, str] = {}
    candidates = []
    if page_type:
        candidates.extend([
            ("target_desktop_fold", CAPTURES / client / page_type / "screenshots" / "desktop_clean_fold.png"),
            ("target_mobile_fold", CAPTURES / client / page_type / "screenshots" / "mobile_clean_fold.png"),
            ("target_desktop_full", CAPTURES / client / page_type / "screenshots" / "desktop_clean_full.png"),
            ("target_mobile_full", CAPTURES / client / page_type / "screenshots" / "mobile_clean_full.png"),
            ("target_spatial_annotated", CAPTURES / client / page_type / "screenshots" / "spatial_annotated_desktop.png"),
        ])
    candidates.extend([
        ("desktop_fold", CAPTURES / client / "home" / "screenshots" / "desktop_clean_fold.png"),
        ("mobile_fold", CAPTURES / client / "home" / "screenshots" / "mobile_clean_fold.png"),
        ("desktop_full", CAPTURES / client / "home" / "screenshots" / "desktop_clean_full.png"),
        ("mobile_full", CAPTURES / client / "home" / "screenshots" / "mobile_clean_full.png"),
        ("pricing_fold", CAPTURES / client / "pricing" / "screenshots" / "desktop_clean_fold.png"),
        ("pricing_full", CAPTURES / client / "pricing" / "screenshots" / "desktop_clean_full.png"),
        ("lp_leadgen_fold", CAPTURES / client / "lp_leadgen" / "screenshots" / "desktop_clean_fold.png"),
        ("lp_leadgen_full", CAPTURES / client / "lp_leadgen" / "screenshots" / "desktop_clean_full.png"),
        ("pdp_fold", CAPTURES / client / "pdp" / "screenshots" / "desktop_clean_fold.png"),
        ("pdp_full", CAPTURES / client / "pdp" / "screenshots" / "desktop_clean_full.png"),
    ])
    for key, path in candidates:
        if path.exists():
            assets[key] = _asset_ref_for_html(path, save_html_path)
    return assets


def _generate_and_select_creative_route(
    client: str, page_type: str, brand_dna: dict, brief: dict,
    mode: str = "auto", verbose: bool = True,
) -> tuple[str, dict]:
    """Optional Creative Director route through the explicit legacy-lab adapter.

    mode : "auto" (Sonnet arbitre) | "safe" | "premium" | "bold" | "custom"

    Returns: (block_text, route_data) — block_text injectable dans prompt_assembly.
    """
    # Charger design_grammar (réutilisé par creative_director V26.Z)
    design_grammar = load_design_grammar(client)
    business_context = json.dumps({"brief": brief, "page_type": page_type}, ensure_ascii=False)[:2000]

    if verbose:
        print(f"\n→ Creative Director (mode={mode})...")

    try:
        routes_data = generate_creative_routes(
            client=client,
            page_type=page_type,
            brand_dna=brand_dna,
            design_grammar=design_grammar,
            business_context=business_context,
            verbose=verbose,
        )
        selected = select_creative_route(
            routes_data=routes_data,
            brand_dna=brand_dna,
            business_context=business_context,
            mode=mode,
            verbose=verbose,
        )
        block = render_creative_route_block(
            selected.get("route", selected),
            selected.get("selection_meta") or selected.get("meta"),
        )
        if verbose:
            route_name = (selected.get("route") or selected).get("name", "?")
            risk = (selected.get("route") or selected).get("risk_level", "?")
            print(f"  ✓ Creative route selected: « {route_name} » ({risk})")
        return block, selected
    except LegacyLabUnavailable as e:
        if verbose:
            print(f"  ⚠️  creative_director unavailable: {e}")
        return "", {}
    except Exception as e:
        if verbose:
            print(f"  ⚠️  creative_director failed: {e}")
        return "", {}


def run_mode_1_complete(
    client: str,
    page_type: str,
    brief: dict,
    *,
    n_critical: int = 5,
    target_language: str = "FR",
    primary_cta_label: str | None = None,
    primary_cta_href: str | None = None,
    generation_max_tokens: int = 10000,
    generation_temperature: float = 0.6,
    generation_strategy: str = "controlled",  # V27 default: planner + copy slots + controlled renderer.
    copy_fallback_only: bool = False,  # smoke tests only: render without LLM copy call.
    apply_fixes: bool = True,
    apply_minimal_gates: bool = True,
    skip_judges: bool = False,
    save_html_path: str | None = None,
    save_audit_path: str | None = None,
    creative_route: str | None = None,  # Sprint C.1 V26.AA REVERT : leçon empirique brutale.
                                        # Sprint C.1 test : creative_route=auto + inject_design_grammar=True
                                        # → 52.6% Moyen (vs Sprint 3 setup pur 80.5% Excellent).
                                        # Anti-pattern #1 design doc V26.AA confirmé : "mega-prompt
                                        # sursaturé > 15K chars → Sonnet coche au lieu de créer".
                                        # Doctrine Mathis "concision > exhaustivité" prouvée empiriquement.
                                        # Defaults REVERT au setup Sprint 3 qui marchait.
                                        # creative_route + design_grammar restent OPT-IN explicites.
    inject_design_grammar: bool = False,  # Sprint C.1 REVERT (cf comment ci-dessus).
    verbose: bool = True,
) -> dict:
    """Pipeline complet Mode 1 COMPLETE.

    Args:
      client: slug — doit avoir data/captures/<client>/brand_dna.json
      page_type: ex "lp_listicle"
      brief: dict avec keys objectif/audience/angle
      n_critical: nombre de critères doctrine top à injecter (default 5 Day 5)
      target_language: langue cible deterministe (default FR)
      primary_cta_label/href: override CTA deterministe si fourni
      generation_max_tokens: plafond sortie generation/copy (default 10000)
      generation_temperature: temperature generation (default 0.6)
      generation_strategy: "controlled" (default V27) | "single_pass" (rollback)
      copy_fallback_only: render deterministic placeholder copy, no LLM (tests only)
      apply_fixes: appliquer fix_html_runtime post-génération (default True)
      apply_minimal_gates: CTA/font/proof guard deterministe post-génération
      skip_judges: skipper le multi-judge (debug only)
      save_html_path: où sauver le HTML (None = pas de save)
      save_audit_path: où sauver l'audit JSON (None = pas de save)
      verbose: print progress

    Returns: dict {
        html, audit (multi_judge), gen (single_pass output), prompt_meta, telemetry
    }

    Raises:
      ValueError si brand_dna manquant pour ce client
    """
    if not has_brand_dna(client):
        raise ValueError(
            f"❌ brand_dna manquant pour client='{client}'. "
            f"Lancer brand_dna_extractor avant Mode 1, ou utiliser Mode 5 GENESIS."
        )

    if verbose:
        print(f"\n══ Mode 1 COMPLETE — {client} / {page_type} ══")
        summary = get_brand_summary(client)
        print(f"  Brand : {summary.get('signature_phrase', '?')}")
        print(f"  Tone  : {summary.get('tone', '?')}")
        print(f"  Brief : objectif='{brief.get('objectif','?')[:60]}...' audience='{brief.get('audience','?')[:60]}...'")

    grand_t0 = time.time()
    context_pack, client_ctx = build_generation_context_pack(
        client=client,
        page_type=page_type,
        brief=brief,
        mode="complete",
        target_language=target_language,
    )
    context_pack_dict = context_pack.to_dict()
    brand_dna = client_ctx.brand_dna or load_brand_dna(client)
    minimal_constraints = build_minimal_constraints(
        client=client,
        page_type=page_type,
        brief=brief,
        brand_dna=brand_dna,
        target_language=target_language,
        primary_cta_label=primary_cta_label,
        primary_cta_href=primary_cta_href,
    )

    if generation_strategy not in {"controlled", "single_pass"}:
        raise ValueError("generation_strategy must be 'controlled' or 'single_pass'")

    # ── 1.0 Creative Director legacy adapter — single_pass opt-in only ──
    creative_route_block = ""
    creative_route_data: dict = {}
    if creative_route and generation_strategy == "single_pass":
        creative_route_block, creative_route_data = _generate_and_select_creative_route(
            client, page_type, brand_dna, brief, mode=creative_route, verbose=verbose,
        )

    if generation_strategy == "controlled":
        # ── 1. Build deterministic plan + design tokens ─────────────────────
        doctrine_pack = build_doctrine_pack(
            page_type=page_type,
            brief=brief,
            constraints=minimal_constraints,
            n_critical=max(n_critical, 10),
            context_pack=context_pack_dict,
        )
        visual_pack = build_visual_intelligence_pack(
            context_pack=context_pack_dict,
            doctrine_pack=doctrine_pack.to_dict(),
            brief=brief,
        )
        design_grammar = client_ctx.design_grammar or load_design_grammar(client)
        aura_tokens = client_ctx.aura_tokens or load_aura_tokens(client, page_type)
        creative_route_contract = build_structured_creative_route_contract(
            visual_pack=visual_pack.to_dict(),
            brand_dna=brand_dna,
            brief=brief,
            aura_tokens=aura_tokens,
            preferred_risk=creative_route,
        )
        design_tokens = build_design_tokens(
            client=client,
            brand_dna=brand_dna,
            design_grammar=design_grammar,
            aura_tokens=aura_tokens,
            visual_intelligence=visual_pack.to_dict(),
        )
        visual_assets = _select_visual_assets(client, page_type, save_html_path)
        if visual_assets:
            minimal_constraints = {
                **minimal_constraints,
                "visual_assets": visual_assets,
            }
        plan = build_page_plan(
            client=client,
            page_type=page_type,
            brief=brief,
            design_tokens=design_tokens,
            doctrine_pack=doctrine_pack.to_dict(),
            constraints=minimal_constraints,
            context_pack=context_pack_dict,
            visual_intelligence=visual_pack.to_dict(),
            creative_route_contract=creative_route_contract.to_dict(),
            target_language=target_language,
        )
        if verbose:
            print(
                f"\n→ Controlled planner : layout={plan.layout_name} "
                f"sections={len(plan.sections)} doctrine={len(doctrine_pack.criteria)} "
                f"category={doctrine_pack.business_category} visual={visual_pack.visual_role}"
            )

        # ── 2. Bounded copy JSON only ───────────────────────────────────────
        if copy_fallback_only:
            copy_result = {
                "copy": fallback_copy_from_plan(plan),
                "raw": "",
                "prompt_chars": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "wall_seconds": 0,
                "model": "fallback",
            }
        else:
            copy_result = call_copy_llm(
                plan=plan,
                brand_dna=brand_dna,
                max_tokens=min(generation_max_tokens, 6000),
                temperature=min(generation_temperature, 0.55),
                verbose=verbose,
            )

        # ── 3. Controlled renderer owns HTML/CSS ───────────────────────────
        html_raw = render_controlled_page(plan=plan, copy_doc=copy_result["copy"])
        if apply_fixes:
            html, fixes_info = apply_runtime_fixes(html_raw, verbose=verbose)
        else:
            html, fixes_info = html_raw, {"applied": False, "reason": "skipped"}
        gen = {
            "html": html,
            "html_raw": html_raw,
            "tokens_in": copy_result["tokens_in"],
            "tokens_out": copy_result["tokens_out"],
            "wall_seconds": copy_result["wall_seconds"],
            "model": copy_result["model"],
            "fixes": fixes_info,
            "renderer": "controlled_v27",
            "plan": plan.to_dict(),
            "copy": copy_result["copy"],
            "copy_prompt_chars": copy_result["prompt_chars"],
            "html_chars_raw": len(html_raw),
            "html_chars_fixed": len(html),
        }
        prompt_meta = {
            "generation_strategy": generation_strategy,
            "copy_prompt_chars": copy_result["prompt_chars"],
            "plan_sections": len(plan.sections),
            "layout_name": plan.layout_name,
            "doctrine_upstream": {
                "business_category": doctrine_pack.business_category,
                "criteria_ids": [criterion.id for criterion in doctrine_pack.criteria],
                "pillar_weights": doctrine_pack.pillar_weights,
                "evidence_policy": doctrine_pack.evidence_policy.get("proof_intensity"),
                "page_type_specific_ids": [
                    c.get("id") for c in doctrine_pack.page_type_specific_criteria
                ],
                "excluded_criteria": doctrine_pack.excluded_criteria,
            },
            "context_pack": {
                "version": context_pack.version,
                "available_count": len(context_pack.artefacts.get("available") or []),
                "missing_count": len(context_pack.artefacts.get("missing") or []),
                "risk_flags": context_pack.risk_flags,
                "audit_dependency_policy": context_pack.audit_dependency_policy,
            },
            "visual_intelligence": {
                "version": visual_pack.version,
                "visual_role": visual_pack.visual_role,
                "density": visual_pack.density,
                "energy": visual_pack.energy,
                "proof_visibility": visual_pack.proof_visibility,
                "product_visibility": visual_pack.product_visibility,
            },
            "creative_route_contract": {
                "version": creative_route_contract.version,
                "route_name": creative_route_contract.route_name,
                "risk_level": creative_route_contract.risk_level,
                "source": creative_route_contract.source,
                "golden_ref_count": len(creative_route_contract.golden_references),
                "technique_ref_count": len(creative_route_contract.technique_references),
                "renderer_overrides": creative_route_contract.renderer_overrides,
                "top_golden_refs": [
                    {
                        "site": ref.get("site"),
                        "page": ref.get("page"),
                        "distance": ref.get("distance"),
                    }
                    for ref in creative_route_contract.golden_references[:3]
                ],
            },
            "n_critical": n_critical,
            "target_language": target_language,
            "primary_cta_label": minimal_constraints.get("primary_cta_label"),
            "allowed_number_tokens": minimal_constraints.get("allowed_number_tokens"),
            "visual_assets": sorted((minimal_constraints.get("visual_assets") or {}).keys()),
        }
    else:
        # ── 1. Build prompt ──────────────────────────────────────
        system_prompt, user_message = build_mode1_prompt(
            client=client, page_type=page_type, brief=brief,
            brand_dna=brand_dna, n_critical=n_critical,
            creative_route_block=creative_route_block,
            inject_design_grammar=inject_design_grammar,
            minimal_constraints=minimal_constraints,
        )
        prompt_meta = {
            "generation_strategy": generation_strategy,
            "system_chars": len(system_prompt),
            "user_chars": len(user_message),
            "total_chars": len(system_prompt) + len(user_message),
            "n_critical": n_critical,
            "target_language": target_language,
            "primary_cta_label": minimal_constraints.get("primary_cta_label"),
            "allowed_number_tokens": minimal_constraints.get("allowed_number_tokens"),
        }
        if verbose:
            print(f"\n→ Prompt assembly : system={prompt_meta['system_chars']} user={prompt_meta['user_chars']} chars (total={prompt_meta['total_chars']})")

        # ── 2. Single-pass generation ───────────────────────────
        if verbose:
            print(f"\n→ Single-pass generation (Sonnet 4.5, T={generation_temperature})...")
        gen = single_pass(
            system_prompt, user_message,
            max_tokens=generation_max_tokens, temperature=generation_temperature, apply_fixes=apply_fixes,
            verbose=verbose,
        )
        html = gen["html"]
    minimal_report: dict[str, Any] = {}

    # ── 2b. Minimal deterministic gates (no LLM polish) ────────
    if apply_minimal_gates:
        html, minimal_report = apply_minimal_postprocess(
            html,
            minimal_constraints,
            verbose=verbose,
        )
        gen["html"] = html
        gen["minimal_gates"] = minimal_report

    # ── 3. Save HTML ─────────────────────────────────────────
    if save_html_path:
        out_html = pathlib.Path(save_html_path)
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html)
        if verbose:
            print(f"  ✓ HTML saved : {out_html.relative_to(ROOT) if out_html.is_relative_to(ROOT) else out_html}")

    # ── 4. Multi-judge ──────────────────────────────────────
    audit: dict = {}
    if not skip_judges:
        if verbose:
            print(f"\n→ Multi-judge (doctrine + humanlike + impl_check)...")
        from moteur_multi_judge.orchestrator import run_multi_judge
        audit = run_multi_judge(
            html=html, client=client, page_type=page_type, verbose=verbose,
        )
        if save_audit_path:
            out_audit = pathlib.Path(save_audit_path)
            out_audit.parent.mkdir(parents=True, exist_ok=True)
            out_audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
            if verbose:
                print(f"  ✓ Audit saved : {out_audit.relative_to(ROOT) if out_audit.is_relative_to(ROOT) else out_audit}")

    grand_dt = time.time() - grand_t0

    # ── 5. Telemetry & return ───────────────────────────────
    total_tokens_in = gen["tokens_in"] + audit.get("totals_meta", {}).get("tokens_in", 0)
    total_tokens_out = gen["tokens_out"] + audit.get("totals_meta", {}).get("tokens_out", 0)
    cost = total_tokens_in / 1e6 * 3 + total_tokens_out / 1e6 * 15

    telemetry = {
        "wall_seconds_total": round(grand_dt, 1),
        "wall_seconds_gen": gen["wall_seconds"],
        "wall_seconds_judge": round(grand_dt - gen["wall_seconds"], 1) if not skip_judges else 0,
        "tokens_in_gen": gen["tokens_in"],
        "tokens_out_gen": gen["tokens_out"],
        "tokens_in_total": total_tokens_in,
        "tokens_out_total": total_tokens_out,
        "cost_estimate_usd": round(cost, 3),
        "minimal_gate_pass": (minimal_report.get("audit") or {}).get("pass") if minimal_report else None,
    }
    if verbose:
        print(f"\n══ Mode 1 COMPLETE — DONE ══")
        print(f"  Wall total      : {telemetry['wall_seconds_total']}s")
        print(f"  Coût estimé     : ${telemetry['cost_estimate_usd']}")
        if minimal_report:
            print(f"  Minimal gates   : {'PASS' if telemetry['minimal_gate_pass'] else 'FAIL'}")
        if audit:
            t = audit.get("final", {})
            print(f"  Final score     : {t.get('final_score_pct', '?')}% — {t.get('verdict', '?')}")

    return {
        "html": html,
        "audit": audit,
        "gen": gen,
        "prompt_meta": prompt_meta,
        "telemetry": telemetry,
        "minimal_gates": minimal_report,
        "client": client,
        "page_type": page_type,
        "brief": brief,
        "mode": "complete",
        "generation_strategy": generation_strategy,
        "creative_route": creative_route_data,
    }
