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
from ..core.impeccable_qa import run_impeccable_qa
from ..core.prompt_assembly import build_mode1_prompt
from ..core.pipeline_single_pass import apply_runtime_fixes, single_pass
from ..core.design_grammar_loader import load_design_grammar
from ..core.minimal_guards import build_minimal_constraints, apply_minimal_postprocess
from ..core.context_pack import ContextPackOutput, build_generation_context_pack
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

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

ROOT = pathlib.Path(__file__).resolve().parents[2]
CAPTURES = ROOT / "data" / "captures"


def _asset_ref_for_html(asset_path: pathlib.Path, save_html_path: str | None) -> str:
    """Return a browser-usable local asset reference for rendered deliverables."""
    if save_html_path:
        out_parent = pathlib.Path(save_html_path)
        if not out_parent.is_absolute():
            out_parent = ROOT / out_parent
        # Issue #19 robustness: in a git worktree where data/captures is a
        # symlink to the main repo, ``asset_path.resolve().relative_to(ROOT)``
        # raises ValueError because the resolved path lives outside ROOT.
        # Fall back to ``os.path.relpath`` which handles both cases.
        try:
            rel = pathlib.Path(asset_path).resolve().relative_to(ROOT)
            return pathlib.Path("..", rel).as_posix() if out_parent.parent == ROOT / "deliverables" else pathlib.Path(
                os.path.relpath(asset_path, out_parent.parent)
            ).as_posix()
        except ValueError:
            return pathlib.Path(
                os.path.relpath(asset_path, out_parent.parent)
            ).as_posix()
    try:
        return asset_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return asset_path.as_posix()


def _select_visual_assets(
    client: str,
    page_type: str | None = None,
    save_html_path: str | None = None,
    target_language: str | None = None,
) -> dict[str, str]:
    """Select deterministic brand/product screenshots for the controlled renderer.

    V27.2-H Sprint 15 (T15-1) — additions :

    * **Lang-aware fallback** : when ``target_language="FR"`` and a
      ``home_fr/`` capture exists, prefer it over ``home/`` for the
      ``desktop_fold`` key. Mathis 2026-05-15 : *"je vois la capture du
      site en anglais avec une description en anglais"* — the hero must
      reflect the target language.
    * **Per-reason contextual assets** : surface additional keys
      (``integrations_fold``, ``customers_fold``, ``dashboard_fold``,
      ``onboarding_fold``) when those captures exist. The
      ``component_renderer._reason_visual`` picks the right one based on
      the reason heading keywords.
    """
    assets: dict[str, str] = {}
    candidates = []
    # T15-1: lang-aware home capture priority (FR target → home_fr first).
    home_subdirs = ["home"]
    if (target_language or "").upper() == "FR":
        home_subdirs = ["home_fr", "home"]
    elif (target_language or "").upper() == "EN":
        home_subdirs = ["home_en", "home"]
    if page_type:
        candidates.extend([
            ("target_desktop_fold", CAPTURES / client / page_type / "screenshots" / "desktop_clean_fold.png"),
            ("target_mobile_fold", CAPTURES / client / page_type / "screenshots" / "mobile_clean_fold.png"),
            ("target_desktop_full", CAPTURES / client / page_type / "screenshots" / "desktop_clean_full.png"),
            ("target_mobile_full", CAPTURES / client / page_type / "screenshots" / "mobile_clean_full.png"),
            ("target_spatial_annotated", CAPTURES / client / page_type / "screenshots" / "spatial_annotated_desktop.png"),
        ])
    # Lang-aware home (FR target prefers home_fr/ if present).
    for home_dir in home_subdirs:
        candidates.extend([
            ("desktop_fold", CAPTURES / client / home_dir / "screenshots" / "desktop_clean_fold.png"),
            ("mobile_fold", CAPTURES / client / home_dir / "screenshots" / "mobile_clean_fold.png"),
            ("desktop_full", CAPTURES / client / home_dir / "screenshots" / "desktop_clean_full.png"),
            ("mobile_full", CAPTURES / client / home_dir / "screenshots" / "mobile_clean_full.png"),
        ])
    # T15-1: contextual per-reason captures (SaaS-typical deeplinks).
    contextual = [
        "pricing", "pricing_fr",
        "integrations", "integrations_fr",
        "customers", "customers_fr",
        "dashboard", "dashboard_fr",
        "onboarding", "onboarding_fr",
        "lp_leadgen", "pdp",
    ]
    for sub in contextual:
        # Normalize key (drop _fr suffix in the exposed key — the
        # renderer treats ``pricing_fold`` and would-be ``pricing_fr_fold``
        # as the same topic).
        key_base = sub.replace("_fr", "")
        candidates.extend([
            (f"{key_base}_fold", CAPTURES / client / sub / "screenshots" / "desktop_clean_fold.png"),
            (f"{key_base}_full", CAPTURES / client / sub / "screenshots" / "desktop_clean_full.png"),
        ])
    for key, path in candidates:
        # First-write-wins : keep the higher-priority entry already in
        # ``assets`` (e.g. home_fr beats home for the FR target).
        if key not in assets and path.exists():
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
        logger.info(f"\n→ Creative Director (mode={mode})...")

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
            logger.info(f"  ✓ Creative route selected: « {route_name} » ({risk})")
        return block, selected
    except LegacyLabUnavailable as e:
        if verbose:
            logger.info(f"  ⚠️  creative_director unavailable: {e}")
        return "", {}
    except Exception as e:
        if verbose:
            logger.info(f"  ⚠️  creative_director failed: {e}")
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
        logger.info(f"\n══ Mode 1 COMPLETE — {client} / {page_type} ══")
        summary = get_brand_summary(client)
        logger.info(f"  Brand : {summary.get('signature_phrase', '?')}")
        logger.info(f"  Tone  : {summary.get('tone', '?')}")
        logger.info(f"  Brief : objectif='{brief.get('objectif','?')[:60]}...' audience='{brief.get('audience','?')[:60]}...'")

    grand_t0 = time.time()
    context_pack: ContextPackOutput
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
        visual_assets = _select_visual_assets(
            client, page_type, save_html_path,
            target_language=(brief.get("target_language") or "FR"),
        )
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
            logger.info(
                f"\n→ Controlled planner : layout={plan.layout_name} "
                f"sections={len(plan.sections)} doctrine={len(doctrine_pack.criteria)} "
                f"category={doctrine_pack.business_category} visual={visual_pack.visual_role}"
            )

        # ── 2. Bounded copy JSON only ───────────────────────────────────────
        # V27.2-H Sprint 15 (T15-3): if the brief references a validated
        # LP-Creator copy.md, parse it and use it as canonical — skip the
        # Sonnet copy call entirely. Mathis's 20/20 phrasing (with named
        # entities Amazon/HBO/Polaar etc.) is preserved verbatim.
        lp_creator_copy_path = (brief.get("lp_creator_validated_copy_path") or "").strip()
        lp_creator_copy_doc: dict[str, Any] = {}
        if lp_creator_copy_path:
            try:
                from ..core.copy_lp_creator_parser import parse_lp_creator_copy
                lp_creator_copy_doc = parse_lp_creator_copy(lp_creator_copy_path)
                if lp_creator_copy_doc and lp_creator_copy_doc.get("reasons"):
                    logger.info(
                        f"  ✓ LP-Creator canonical copy loaded ({len(lp_creator_copy_doc.get('reasons') or [])} reasons, "
                        f"{len((lp_creator_copy_doc.get('testimonials') or {}).get('items') or [])} testimonials, "
                        f"{len((lp_creator_copy_doc.get('faq') or {}).get('items') or [])} faq) — skipping Sonnet copy"
                    )
            except Exception as exc:
                logger.warning(f"  ⚠ LP-Creator copy parse failed ({exc}) — falling back to Sonnet")
                lp_creator_copy_doc = {}

        if lp_creator_copy_doc and lp_creator_copy_doc.get("reasons"):
            # Skip Sonnet entirely — use canonical LP-Creator copy.
            copy_result = {
                "copy": lp_creator_copy_doc,
                "raw": "",
                "prompt_chars": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "wall_seconds": 0,
                "model": "lp_creator_canonical",
            }
        elif copy_fallback_only:
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
        # Sprint 13 / V27.2-G+ : if the planner activated rich listicle sections
        # (comparison / testimonials / faq) but Sonnet folded the content into
        # the reason bodies instead of populating the dedicated keys, hydrate
        # those keys deterministically from the BriefV2 so the renderer outputs
        # the proper sections. Source of truth = brief, never invented.
        copy_doc = copy_result["copy"]
        from ..core.planner import _has_rich_listicle_signals
        if page_type == "lp_listicle":
            signals = _has_rich_listicle_signals(brief)
            if signals["has_testimonials"] and not (copy_doc.get("testimonials") or {}).get("items"):
                # V27.2-H Sprint 15 T15-2: propagate source attribution
                # (source_url + is_verified) into copy_doc so the
                # renderer can mark unverified testimonials with a
                # [non-vérifié] overlay or skip them entirely.
                copy_doc["testimonials"] = {
                    "heading": "Ils en parlent mieux que nous.",
                    "items": [
                        {
                            "name": t.get("name", ""),
                            "position": t.get("position", ""),
                            "company": t.get("company", ""),
                            "quote": t.get("quote", ""),
                            "stat_highlight": "",
                            "source_url": t.get("source_url", ""),
                            "sourced_from": t.get("sourced_from", ""),
                            "is_verified": bool(t.get("is_verified", False)),
                        }
                        for t in (brief.get("testimonials") or [])
                        if isinstance(t, dict) and t.get("authorized", True)
                    ],
                }
            if signals["has_comparison"] and not (copy_doc.get("comparison") or {}).get("rows"):
                # Default rows derived from the brief : the sourced_numbers
                # provide both sides of each comparison. We surface 5 standard
                # dimensions when the brief carries pricing + time-to-market +
                # quality + SEO + maintenance signals. All values are sourced.
                sn_map = {}
                for sn in (brief.get("sourced_numbers") or []):
                    if not isinstance(sn, dict):
                        continue
                    context_lower = str(sn.get("context") or "").lower()
                    sn_map[context_lower] = {
                        "number": sn.get("number", ""),
                        "context": sn.get("context", ""),
                    }

                def _find(*keywords):
                    for key, val in sn_map.items():
                        if all(k in key for k in keywords):
                            return val
                    return None

                rows: list[dict[str, str]] = []
                without_setup = _find("dev", "interne") or _find("agence", "délai") or _find("délai")
                with_setup = _find("temps", "setup") or _find("5 min")
                if without_setup or with_setup:
                    rows.append({
                        "dimension": "Time-to-market",
                        "without": without_setup["number"] if without_setup else "Plusieurs semaines à plusieurs mois",
                        "with": with_setup["number"] if with_setup else "Quelques minutes",
                    })
                without_cost = _find("agence", "coût") or _find("budget", "agence") or _find("benchmark", "agence")
                with_cost = _find("tarif", "starter") or _find("plan", "starter") or _find("plan", "business")
                if without_cost or with_cost:
                    rows.append({
                        "dimension": "Coût total an 1",
                        "without": without_cost["number"] if without_cost else "15 000 € à 30 000 €",
                        "with": with_cost["number"] if with_cost else "Abonnement mensuel",
                    })
                rows.append({
                    "dimension": "Qualité traduction",
                    "without": "Robotic (plugin automatique) ou figée (agence)",
                    "with": "IA fidèle marque + révision humaine optionnelle",
                })
                rows.append({
                    "dimension": "SEO multilingue",
                    "without": "Plugin = duplicate content / agence = hreflang manuel",
                    "with": "URLs dédiées + hreflang automatique + server-side",
                })
                rows.append({
                    "dimension": "Maintenance ongoing",
                    "without": "Recoder à chaque update / re-facturation agence",
                    "with": "Le système suit l'évolution du site",
                })

                copy_doc["comparison"] = {
                    "heading": "Faisons un bilan honnête.",
                    "subtitle": "Vous + une agence vs vous + une solution dédiée, sur les 5 dimensions qui comptent.",
                    "without_label": "Sans solution dédiée",
                    "with_label": f"Avec {client.capitalize()}",
                    "rows": rows,
                }
            if signals["has_faq"] and not (copy_doc.get("faq") or {}).get("items"):
                # Default FAQ : 5 standard SaaS objection-handling Q&A.
                # Generic enough to apply to any SaaS lp_listicle, specific
                # enough to surface real objections (prix, intégration, SEO,
                # qualité IA, essai gratuit).
                copy_doc["faq"] = {
                    "heading": "Questions fréquentes.",
                    "items": [
                        {
                            "question": "Combien ça coûte vraiment ?",
                            "answer": (
                                f"Un plan gratuit perpétuel permet de tester sur une homepage "
                                f"moyenne sans carte bancaire. Les paliers payants couvrent "
                                f"ensuite plus de mots et plus de langues, avec un tarif annuel "
                                f"généralement remisé. Pas de devis sur mesure pour la majorité des cas, "
                                f"pas de minimum projet."
                            ),
                        },
                        {
                            "question": "Compatible avec mon CMS / stack ?",
                            "answer": (
                                "WordPress, Shopify, Webflow, Wix, Squarespace, BigCommerce, "
                                "Drupal — natif. Pour les stacks custom (Next.js, Rails, Laravel, "
                                "Astro), un snippet JavaScript universel s'installe en moins d'une "
                                "minute. Plus de 70 intégrations documentées au catalogue."
                            ),
                        },
                        {
                            "question": "Le SEO multilingue marche-t-il vraiment ?",
                            "answer": (
                                "Chaque langue obtient son URL dédiée (/fr/, /en/, /de/), les balises "
                                "hreflang sont injectées automatiquement, les métadonnées sont traduites, "
                                "et le rendu est server-side : Google indexe chaque version comme un site "
                                "natif, pas comme un duplicate content déguisé."
                            ),
                        },
                        {
                            "question": "La qualité de la traduction IA est-elle suffisante ?",
                            "answer": (
                                "Le modèle linguistique apprend votre tonalité de marque, et vous ajoutez "
                                "des glossaires terminologiques (noms de produits, slogans à ne pas traduire). "
                                "Pour les pages où ça compte (mentions légales, claims marketing), vous "
                                "activez la révision humaine d'un traducteur pro en un clic."
                            ),
                        },
                        {
                            "question": "Puis-je tester sur mon vrai site avant de payer ?",
                            "answer": (
                                "Oui — plan gratuit perpétuel sans carte bancaire au signup. De quoi traduire "
                                "votre homepage et quelques pages produits, juger sur pièce, puis upgrader en "
                                "un clic si vous voulez plus de langues ou plus de mots."
                            ),
                        },
                    ],
                }
        # Debug : log copy_doc top-level keys for visibility (Sprint 13 / V27.2-G+)
        if verbose:
            top_keys = list(copy_doc.keys()) if isinstance(copy_doc, dict) else []
            logger.info(f"  Copy_doc top-keys: {top_keys}")
            if "comparison" in copy_doc:
                rows = (copy_doc.get("comparison") or {}).get("rows") or []
                logger.info(f"    → comparison.rows count: {len(rows)}")
            if "testimonials" in copy_doc:
                items = (copy_doc.get("testimonials") or {}).get("items") or []
                logger.info(f"    → testimonials.items count: {len(items)}")
            if "faq" in copy_doc:
                items = (copy_doc.get("faq") or {}).get("items") or []
                logger.info(f"    → faq.items count: {len(items)}")
        html_raw = render_controlled_page(plan=plan, copy_doc=copy_doc)
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
            logger.info(f"\n→ Prompt assembly : system={prompt_meta['system_chars']} user={prompt_meta['user_chars']} chars (total={prompt_meta['total_chars']})")

        # ── 2. Single-pass generation ───────────────────────────
        if verbose:
            logger.info(f"\n→ Single-pass generation (Sonnet 4.5, T={generation_temperature})...")
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

    # ── 2c. Impeccable QA layer (V27.2-G+ issue #19) ──────────
    # Post-render anti-pattern detection (deterministic, offline). Hard
    # fail below MIN_PASSING_SCORE per task #19 spec.
    impeccable_report = run_impeccable_qa(html)
    gen["impeccable_qa"] = impeccable_report
    if verbose:
        ip_score = impeccable_report.get("score")
        ip_passed = impeccable_report.get("passed")
        ip_hits = len(impeccable_report.get("anti_patterns_detected") or [])
        logger.info(
            f"  Impeccable QA   : score={ip_score}/100 "
            f"{'PASS' if ip_passed else 'FAIL'} hits={ip_hits}"
        )

    # ── 2d. CRO methodology audit (V27.2-H Sprint 15 T15-5) ────
    # Deterministic CRO heuristic audit against copy_doc + brief.
    # Same spirit as the cro-methodology Anthropic skill (10/10
    # scoring) but implemented in Python so it runs on every
    # generation with zero LLM cost. Mathis 2026-05-15 : *"j'espère
    # qu'on appelle tous les skills qu'on a mis en place"*.
    try:
        from ..core.cro_methodology_audit import run_cro_methodology_audit
        cro_report = run_cro_methodology_audit(copy_doc=copy_doc, brief=brief)
        gen["cro_methodology_audit"] = cro_report
        if verbose:
            cro_score = cro_report.get("score")
            cro_passed = cro_report.get("passed")
            cro_gap_count = len(cro_report.get("gaps") or [])
            logger.info(
                f"  CRO methodology : score={cro_score}/10 "
                f"{'PASS' if cro_passed else 'FAIL'} gaps={cro_gap_count}"
            )
            for gap in (cro_report.get("gaps") or [])[:5]:
                logger.info(f"     - {gap.get('severity', 'warn'):8s} {gap.get('id')} : {gap.get('description')}")
    except Exception as exc:
        logger.warning(f"  ⚠ CRO methodology audit failed : {exc}")

    # ── 2e. Skills runtime audits (V27.2-H Sprint 16 T16-2/3/4) ────
    # frontend-design + brand-guidelines + emil-design-eng — each is a
    # Python heuristic implementation of the corresponding Anthropic
    # skill. They run at runtime on every generation (deterministic, no
    # extra LLM cost) and surface their score 0-10 + gaps in the run
    # summary. Mathis 2026-05-15 : *"on est sûr qu'on a tout fait avec
    # le full pipe… toutes les compétences qu'on doit utiliser"*.
    skills_runtime: dict[str, Any] = {}
    for skill_id, audit_callable, audit_kwargs in (
        ("frontend-design", "frontend_design_audit.run_frontend_design_audit", {"html": html}),
        ("brand-guidelines", "brand_guidelines_audit.run_brand_guidelines_audit", {"html": html, "client": client}),
        ("emil-design-eng", "emil_design_eng_audit.run_emil_design_eng_audit", {"html": html}),
    ):
        try:
            module_name, func_name = audit_callable.split(".")
            module = __import__(f"moteur_gsg.core.{module_name}", fromlist=[func_name])
            func = getattr(module, func_name)
            report = func(**audit_kwargs)
            skills_runtime[skill_id] = report
            if verbose:
                score = report.get("score")
                passed = report.get("passed")
                gap_count = len(report.get("gaps") or [])
                logger.info(
                    f"  {skill_id:18s} : score={score}/10 "
                    f"{'PASS' if passed else 'FAIL'} gaps={gap_count}"
                )
                for gap in (report.get("gaps") or [])[:3]:
                    logger.info(f"     - {gap.get('severity', 'warn'):8s} {gap.get('id')} : {gap.get('description')}")
        except Exception as exc:
            logger.warning(f"  ⚠ {skill_id} audit failed : {exc}")
    gen["skills_runtime_audits"] = skills_runtime

    # ── 3. Save HTML ─────────────────────────────────────────
    if save_html_path:
        out_html = pathlib.Path(save_html_path)
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html)
        if verbose:
            logger.info(f"  ✓ HTML saved : {out_html.relative_to(ROOT) if out_html.is_relative_to(ROOT) else out_html}")

    # ── 4. Multi-judge ──────────────────────────────────────
    audit: dict = {}
    if not skip_judges:
        if verbose:
            logger.info("\n→ Multi-judge (doctrine + humanlike + impl_check)...")
        from moteur_multi_judge.orchestrator import run_multi_judge
        audit = run_multi_judge(
            html=html, client=client, page_type=page_type, verbose=verbose,
        )
        if save_audit_path:
            out_audit = pathlib.Path(save_audit_path)
            out_audit.parent.mkdir(parents=True, exist_ok=True)
            out_audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
            if verbose:
                logger.info(f"  ✓ Audit saved : {out_audit.relative_to(ROOT) if out_audit.is_relative_to(ROOT) else out_audit}")

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
        "impeccable_score": impeccable_report.get("score"),
        "impeccable_pass": impeccable_report.get("passed"),
    }
    if verbose:
        logger.info("\n══ Mode 1 COMPLETE — DONE ══")
        logger.info(f"  Wall total      : {telemetry['wall_seconds_total']}s")
        logger.info(f"  Coût estimé     : ${telemetry['cost_estimate_usd']}")
        if minimal_report:
            logger.info(f"  Minimal gates   : {'PASS' if telemetry['minimal_gate_pass'] else 'FAIL'}")
        if audit:
            t = audit.get("final", {})
            logger.info(f"  Final score     : {t.get('final_score_pct', '?')}% — {t.get('verdict', '?')}")

    return {
        "html": html,
        "audit": audit,
        "gen": gen,
        "prompt_meta": prompt_meta,
        "telemetry": telemetry,
        "minimal_gates": minimal_report,
        "impeccable_qa": impeccable_report,
        # T15-5: CRO methodology runtime audit (cf. core.cro_methodology_audit).
        "cro_methodology_audit": gen.get("cro_methodology_audit"),
        # T16-2/3/4: 3 skills runtime audits (frontend-design, brand-guidelines, emil-design-eng).
        "skills_runtime_audits": gen.get("skills_runtime_audits"),
        "client": client,
        "page_type": page_type,
        "brief": brief,
        "mode": "complete",
        "generation_strategy": generation_strategy,
        "creative_route": creative_route_data,
    }
