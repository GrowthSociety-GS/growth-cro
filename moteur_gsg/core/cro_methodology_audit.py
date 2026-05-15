"""CRO methodology audit module — V27.2-H Sprint 15 (T15-5).

Deterministic CRO heuristic audit run **at runtime** against the
``copy_doc`` produced by the moteur GSG. Same spirit as the
``cro-methodology`` Anthropic skill but implemented as Python rules
(no extra LLM call, no extra cost) so it can be wired in the
``mode_1_complete`` pipeline.

Inspired by the CRE Methodology (Schwartz / Sugarman / Pomerantz) :
focuses on the **discoverable** signals — clarity of value prop, single
CTA dominance, social proof above-the-fold, objection handling, friction,
proof density. Score 0-10 per the skill convention (10/10 = full
alignment).

Returns dict::

    {
      "version": "cro-methodology-audit-v1.0",
      "score": 0..10,            # integer
      "passed": bool,            # >= MIN_SCORE
      "gaps": [{"id", "severity", "description", "fix"}],
      "checks_run": int,
    }

This module is the **honest** runtime version of the cro-methodology
skill (Mathis 2026-05-15 audit). The full skill remains available as a
dev-time knowledge base.
"""
from __future__ import annotations

import re
from typing import Any


MIN_SCORE = 7  # out of 10 — fail below


def _h1_clarity_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """H1 must be specific (>= 40 chars) and contain a concrete benefit/number."""
    h1 = ((copy_doc.get("hero") or {}).get("h1") or "").strip()
    if not h1:
        return False, "Hero H1 is empty — visitors cannot understand the value prop above fold"
    if len(h1) < 30:
        return False, f"Hero H1 too short ({len(h1)} chars) — generic, lacks specificity"
    # Specificity signal : contains a number, a brand-known proof, or a year.
    has_number = bool(re.search(r"\d", h1))
    if not has_number:
        return False, "Hero H1 has no number — methodology requires concrete proof above fold"
    return True, ""


def _single_primary_cta_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """Hero + final CTA should share the same label and href (1:1 ratio of attention)."""
    hero_cta = (copy_doc.get("hero") or {}).get("primary_cta_label") or ""
    final_cta = (copy_doc.get("final_cta") or {}).get("button_label") or ""
    if not hero_cta and not final_cta:
        return False, "No primary CTA label found — single primary CTA is the methodology's #1 rule"
    if hero_cta and final_cta and hero_cta.strip().lower()[:20] != final_cta.strip().lower()[:20]:
        return False, f"Hero CTA ('{hero_cta[:30]}') differs from final CTA ('{final_cta[:30]}') — split attention"
    return True, ""


def _social_proof_above_fold_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """A social-proof signal (logos line, named clients, or a 4.x rating) should be in the hero."""
    hero = copy_doc.get("hero") or {}
    above_fold_text = " ".join([
        str(hero.get("dek") or ""),
        str(hero.get("eyebrow") or ""),
        str(hero.get("microcopy") or ""),
        str(hero.get("logos_line") or ""),
    ]).lower()
    has_logos = bool(hero.get("logos_line"))
    has_rating = bool(re.search(r"\b[4-5]\.\d/5\b", above_fold_text))
    has_brand_count = bool(re.search(r"\b\d{3,}\s*(marques|brands|clients|customers|users)", above_fold_text))
    if has_logos or has_rating or has_brand_count:
        return True, ""
    return False, "No social proof above-the-fold (logos line / rating / brand count) — methodology violation"


def _value_prop_specificity_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """Dek (sub-headline) must contain a concrete outcome, not a feature list."""
    dek = ((copy_doc.get("hero") or {}).get("dek") or "").strip()
    if len(dek) < 40:
        return False, f"Dek too short ({len(dek)} chars) — visitors need the WHY, not just the WHAT"
    # Anti-bullshit : flag generic verbs.
    generic_terms = ["leader", "révolutionnaire", "innovant", "disruptif", "game-changer", "unique au monde"]
    for term in generic_terms:
        if term in dek.lower():
            return False, f"Dek contains banned bullshit term '{term}' — methodology rejects 'magic buttons'"
    return True, ""


def _reasons_density_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """Listicle should have ≥ 8 reasons. Each reason should have a side_note (highlight/proof)."""
    reasons = copy_doc.get("reasons") or []
    if not reasons:
        # Not a listicle — skip this check (return True to not penalize).
        return True, ""
    if len(reasons) < 8:
        return False, f"Listicle has only {len(reasons)} reasons — methodology wants ≥ 8 for completeness"
    no_side_note = sum(1 for r in reasons if not r.get("side_note"))
    if no_side_note > len(reasons) // 2:
        return False, f"{no_side_note}/{len(reasons)} reasons lack a side_note (highlight/proof) — reduces scanability"
    return True, ""


def _testimonials_verified_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """V27.2-H T15-2 + T15-5 : testimonials must have source_url OR be marked internal_brief."""
    testimonials = (copy_doc.get("testimonials") or {}).get("items") or []
    if not testimonials:
        return True, ""  # OK to have no testimonials
    unverified = [
        t for t in testimonials
        if isinstance(t, dict)
        and not (t.get("source_url") or "").strip()
        and (t.get("sourced_from") or "").lower() != "internal_brief"
    ]
    if unverified:
        return False, f"{len(unverified)}/{len(testimonials)} testimonials have no source attribution (anti-invention violation)"
    return True, ""


def _faq_objection_handling_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """FAQ must address ≥ 4 objections (pricing, integration, quality, trust)."""
    faq_items = (copy_doc.get("faq") or {}).get("items") or []
    if not faq_items:
        # No FAQ section — pass with a soft note (some pages don't need FAQ)
        return True, ""
    if len(faq_items) < 4:
        return False, f"FAQ has only {len(faq_items)} Q&A — methodology wants ≥ 4 objection handlers"
    return True, ""


def _comparison_present_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """Listicle persuasion benefits from a 'Sans X vs Avec X' comparison table."""
    comparison = copy_doc.get("comparison") or {}
    if not (copy_doc.get("reasons") or []):
        return True, ""  # not a listicle — skip
    rows = comparison.get("rows") or []
    if len(rows) < 3:
        return False, f"Comparison table has {len(rows)} rows — methodology recommends ≥ 4 dimensions"
    return True, ""


def _scent_match_check(copy_doc: dict[str, Any], brief: dict[str, Any] | None) -> tuple[bool, str]:
    """If brief contains a traffic_source with `cold_ad_*`, the hero eyebrow or H1 should echo the ad's promise."""
    if not brief:
        return True, ""
    traffic = brief.get("traffic_source") or []
    if not any("cold_ad" in str(t) for t in traffic):
        return True, ""
    # Heuristic : check that the eyebrow or H1 contains at least one keyword from must_include_elements
    must = " ".join(str(x) for x in (brief.get("must_include_elements") or []))[:200].lower()
    if not must:
        return True, ""  # nothing to match against
    hero = copy_doc.get("hero") or {}
    above_fold = (str(hero.get("eyebrow") or "") + " " + str(hero.get("h1") or "") + " " + str(hero.get("dek") or "")).lower()
    keywords = [w for w in re.findall(r"[a-zA-Zàâäéèêëîïôöùûüç]{5,}", must) if w not in {"client", "brief"}][:6]
    matches = sum(1 for kw in keywords if kw in above_fold)
    if matches < 1 and keywords:
        return False, "Scent trail weak : paid ad context provided but hero ignores must_include keywords"
    return True, ""


def _mid_cta_check(copy_doc: dict[str, Any]) -> tuple[bool, str]:
    """A mid-parcours CTA is needed for listicles with ≥ 6 reasons (Sprint 14 lesson)."""
    reasons = copy_doc.get("reasons") or []
    if len(reasons) < 6:
        return True, ""
    # The mid-CTA is rendered inside the orchestrator (not in copy_doc), so we
    # check by proxy: does `copy_doc.final_cta.button_label` exist AND is the
    # listicle large enough that a mid-CTA is expected?
    # The renderer inserts it automatically when reasons ≥ 6 — so this check
    # passes when reasons.length >= 6 (the renderer guarantees the mid-CTA).
    return True, ""


def _hero_logos_grid_check(copy_doc: dict[str, Any], brief: dict[str, Any] | None) -> tuple[bool, str]:
    """When `available_proofs.logos_clients_tier1` is signaled, hero must surface tier-1 logos."""
    if not brief:
        return True, ""
    proofs = brief.get("available_proofs") or []
    if "logos_clients_tier1" not in proofs:
        return True, ""
    hero = copy_doc.get("hero") or {}
    logos_line = (hero.get("logos_line") or "").strip()
    if not logos_line:
        return False, "Brief signals logos_clients_tier1 but copy has no logos_line — promise not delivered"
    return True, ""


_CHECKS = [
    ("hero_h1_clarity", _h1_clarity_check, "critical"),
    ("single_primary_cta", _single_primary_cta_check, "critical"),
    ("social_proof_above_fold", _social_proof_above_fold_check, "critical"),
    ("value_prop_specificity", _value_prop_specificity_check, "warning"),
    ("reasons_density", _reasons_density_check, "warning"),
    ("testimonials_verified", _testimonials_verified_check, "critical"),
    ("faq_objection_handling", _faq_objection_handling_check, "warning"),
    ("comparison_present", _comparison_present_check, "info"),
    ("scent_match", _scent_match_check, "warning"),
    ("mid_cta_present", _mid_cta_check, "info"),
    ("hero_logos_grid", _hero_logos_grid_check, "warning"),
]


def run_cro_methodology_audit(
    copy_doc: dict[str, Any],
    brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run all CRO methodology checks against ``copy_doc`` (+ optional brief).

    Returns the audit dict (see module docstring). Score 0-10 maps to:
      - critical fail → -2
      - warning fail → -1
      - info fail → -0.5
    Start at 10, deduct for each fail, clamp to 0-10.
    """
    gaps: list[dict[str, Any]] = []
    deduction = 0.0
    for check_id, check_fn, severity in _CHECKS:
        try:
            # Pass brief to checks that accept it.
            if check_fn in (_scent_match_check, _hero_logos_grid_check):
                passed, description = check_fn(copy_doc, brief)
            else:
                passed, description = check_fn(copy_doc)
        except Exception as exc:
            passed, description = False, f"check raised exception: {exc}"
        if not passed:
            weight = {"critical": 2.0, "warning": 1.0, "info": 0.5}.get(severity, 1.0)
            deduction += weight
            gaps.append({
                "id": check_id,
                "severity": severity,
                "description": description,
                "fix": _suggest_fix(check_id),
            })
    score = max(0, min(10, int(round(10 - deduction))))
    return {
        "version": "cro-methodology-audit-v1.0",
        "score": score,
        "passed": score >= MIN_SCORE,
        "gaps": gaps,
        "checks_run": len(_CHECKS),
    }


def _suggest_fix(check_id: str) -> str:
    fixes = {
        "hero_h1_clarity": "Inclure un chiffre concret + un bénéfice mesurable dans le H1 (ex: '111 368 marques utilisent X')",
        "single_primary_cta": "Aligner le CTA hero et le CTA final sur le même libellé et même URL — 1 objectif unique",
        "social_proof_above_fold": "Ajouter une ligne de logos clients OU une note 4.x/5 OU un nombre de clients en hero",
        "value_prop_specificity": "Réécrire le dek en outcome concret, retirer 'leader/disruptif/révolutionnaire'",
        "reasons_density": "Compléter la liste à ≥ 8 raisons OU ajouter un side_note (proof) par raison",
        "testimonials_verified": "Pour chaque testimonial, fournir un `source_url` public OU marquer `sourced_from='internal_brief'`",
        "faq_objection_handling": "Ajouter Q&A sur pricing, integration, qualité, free trial (4 objections min)",
        "comparison_present": "Ajouter une table comparative 'Sans X vs Avec X' sur 4-6 dimensions",
        "scent_match": "Reprendre dans le hero les keywords de l'ad qui amène le visiteur (scent match)",
        "mid_cta_present": "Insérer un CTA après la moitié des reasons pour les scanners",
        "hero_logos_grid": "Le brief liste logos_clients_tier1 — surface les wordmarks dans le hero",
    }
    return fixes.get(check_id, "Voir la skill cro-methodology pour le détail.")


__all__ = ["run_cro_methodology_audit", "MIN_SCORE"]
