#!/usr/bin/env python3
"""
score_page_type.py — Orchestrateur pageType-aware GrowthCRO V12 doctrine v3.1.0.

Pour un (label, pageType) donné :
  1. Applique les exclusions universelles (page_type_criteria.json)
  2. Lance les 6 bloc scorers existants (score_hero/persuasion/ux/coherence/psycho/tech)
     → chacun reçoit le pageType pour filtrer ses critères
  3. Score les critères spécifiques via score_specific_criteria
  4. Agrège sur le maxPerPageType correct (baseline 47 universal - exclusions + specific)
  5. Émet `score_page_type.json` avec vue unifiée + traçabilité exclusions

Usage:
    python score_page_type.py <label> [pageType]
Reads:  data/captures/<label>/<pageType>/capture.json + page.html + score_*.json déjà écrits
Writes: data/captures/<label>/<pageType>/score_page_type.json

Design notes
------------
- Les bloc scorers existants (score_hero.py etc.) sont lancés en subprocess pour ne pas
  recoder leur logique. Ils produisent score_<pillar>.json qu'on relit.
- Les exclusions universelles sont POST-appliquées : on lit le score_<pillar>.json,
  on retire les critères exclus, on recalcule rawTotal/rawMax du pillar.
- Ce design permet un retrofit progressif : tant que tous les bloc scorers ne sont
  pas câblés à page_type_filter, l'orchestrateur applique les exclusions en aval.
"""
from __future__ import annotations

import json
import subprocess
import sys
import pathlib
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from page_type_filter import (
    get_exclusions,
    get_page_type_multipliers,
    get_exclusion_reasons,
    get_max_for_page_type,
    get_specific_criteria,
    list_page_types,
)
# Canonical post-#11 — score_specific_criteria.py shim removed; pull from
# growthcro.scoring.{persist,specific}. _load_capture (legacy private helper)
# is replaced by growthcro.scoring.persist.load_capture (label, page_type, root).
from growthcro.scoring.persist import (
    load_capture as _scoring_load_capture,
    score_page_type_specific as _scoring_score_page_type_specific,
)
import score_universal_extensions as sue


class _SsCompat:
    """Back-compat shim for the legacy `import score_specific_criteria as ssc` API.

    Pre-#11, score_page_type called ssc._load_capture(label, page_type) returning
    (cap, page_html, capture_dir). The canonical helper now lives in
    growthcro.scoring.persist.load_capture(label, page_type, root). Same return
    shape, with `root` injected from this script's resolved ROOT.
    """

    @staticmethod
    def _load_capture(label, page_type):
        return _scoring_load_capture(label, page_type, ROOT)

    score_page_type_specific = staticmethod(_scoring_score_page_type_specific)


ssc = _SsCompat()

# V23.D — Page types qui ont un parcours funnel à scorer (intro statique + flow interactif)
FUNNEL_PAGE_TYPES = {"quiz_vsl", "lp_sales", "lp_leadgen", "signup", "lead_gen_simple"}
# Pondération aggregate pour pages funnel : 40% intro statique / 60% flow funnel
FUNNEL_WEIGHT_INTRO = 0.4
FUNNEL_WEIGHT_FLOW = 0.6
try:
    import score_contextual_overlay as sco  # P1.B doctrine v3.2.0-draft
except ImportError:
    sco = None
try:
    import score_applicability_overlay as sao  # P2.A doctrine v3.2.0-draft
except ImportError:
    sao = None

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = pathlib.Path(__file__).resolve().parent

PILLARS = ["hero", "persuasion", "ux", "coherence", "psycho", "tech"]
SCORER_MODULES = {
    "hero": "score_hero.py",
    "persuasion": "score_persuasion.py",
    "ux": "score_ux.py",
    "coherence": "score_coherence.py",
    "psycho": "score_psycho.py",
    "tech": "score_tech.py",
}

# Map criterion_id prefix → pillar
PREFIX_TO_PILLAR = {
    "hero": "hero",
    "per": "persuasion",
    "ux": "ux",
    "coh": "coherence",
    "psy": "psycho",
    "tech": "tech",
}


def _prefix_of(cid: str) -> str:
    for pref in PREFIX_TO_PILLAR:
        if cid.startswith(pref + "_") or cid.startswith(pref):
            return pref
    return ""


def _pillar_of_criterion(cid: str) -> str | None:
    pref = _prefix_of(cid)
    return PREFIX_TO_PILLAR.get(pref)


def _load_funnel_score(capture_dir: pathlib.Path, page_type: str) -> dict | None:
    """V23.D — Load score_funnel.json if applicable to page_type.

    Returns dict with score100, criteria, flow_meta, OR None if:
    - page_type not in FUNNEL_PAGE_TYPES
    - score_funnel.json missing
    - file unreadable
    """
    if page_type not in FUNNEL_PAGE_TYPES:
        return None
    f = capture_dir / "score_funnel.json"
    if not f.exists():
        return None
    try:
        return json.load(open(f))
    except Exception:
        return None


def _run_bloc_scorer(pillar: str, label: str, page_type: str, capture_dir: pathlib.Path) -> dict | None:
    """Run a bloc scorer subprocess and load its output JSON.

    V21.E — Si score_<pillar>.json existe AVEC _vision_lift_applied=True,
    on skip le subprocess (qui écraserait les lifts) et on lit le fichier
    existant directement. Permet d'orchestrate sans détruire les lifts Vision.
    """
    out_file = capture_dir / f"score_{pillar}.json"

    # V21.E + V21.G — Preserve vision_lifts AND intelligence_lifts:
    # skip subprocess if file is lifted (vision OR intelligence)
    if out_file.exists():
        try:
            existing = json.loads(out_file.read_text(encoding="utf-8"))
            if existing.get("_vision_lift_applied") or existing.get("_intelligence_applied"):
                return existing
        except Exception:
            pass  # fallthrough to re-run

    # Post-#11: score_ux.py shim removed → invoke canonical module via -m.
    # Other pillar scorers (hero/persuasion/coherence/psycho/tech) are still
    # real scripts under skills/site-capture/scripts/.
    if pillar == "ux":
        cmd = [sys.executable, "-m", "growthcro.scoring.cli", "ux", label, page_type]
    else:
        script = SCRIPTS / SCORER_MODULES[pillar]
        if not script.exists():
            return {"error": f"scorer script missing: {script.name}"}
        cmd = [sys.executable, str(script), label, page_type]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            return {
                "error": f"scorer failed (rc={r.returncode})",
                "stderr": r.stderr[-500:],
                "stdout": r.stdout[-500:],
            }
    except subprocess.TimeoutExpired:
        return {"error": "scorer timeout"}
    except Exception as e:
        return {"error": f"scorer exception: {e}"}
    if out_file.exists():
        try:
            return json.loads(out_file.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"output parse: {e}"}
    return {"error": "no output file after scorer run"}


def _extract_criteria_from_bloc_result(result: dict) -> list[dict]:
    """Try common shapes used by bloc scorers : breakdown[], criteria[], results[]."""
    for key in ("breakdown", "criteria", "results", "scores", "items"):
        v = result.get(key)
        if isinstance(v, list) and v:
            return v
    # Some scorers return a dict keyed by id
    sc = result.get("byCriterion") or result.get("per_criterion")
    if isinstance(sc, dict):
        return [{"id": k, **v} for k, v in sc.items()]
    return []


def _load_semantic_scores(capture_dir: pathlib.Path) -> dict:
    """Load score_semantic.json if present.

    Returns {crit_id: {score, verdict, rationale, method}} with skipped/error entries removed.
    These are the 18 creative criteria evaluated by Haiku 4.5 that regex can't reliably score
    (e.g. hero_01 H1 quality, per_01 benefit-first copy, coh_03 scent-trail…).
    """
    sf = capture_dir / "score_semantic.json"
    if not sf.exists():
        return {}
    try:
        data = json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for cid, entry in (data.get("scores") or {}).items():
        verdict = entry.get("verdict")
        if verdict in ("skipped", "dry_run", "error"):
            continue
        score = entry.get("score")
        if score is None:
            continue
        out[cid] = {
            "score": float(score),
            "verdict": verdict,
            "rationale": entry.get("rationale"),
            "method": "semantic_haiku",
        }
    return out


def _apply_semantic_overlay(bloc_results: dict, semantic_scores: dict) -> dict:
    """Override regex scores with semantic scores for the 18 Haiku-evaluated criteria.

    Mutates bloc_results in-place:
      - For each criterion present in both: record regex_score/regex_verdict, override score/tier,
        recompute pillar rawTotal and score100.
      - Regex-only criteria (no semantic evaluation) are untouched.

    Returns overlay metadata block for inclusion in score_page_type.json output.
    """
    if not semantic_scores:
        return {
            "applied": False,
            "reason": "no score_semantic.json found",
            "criteria_overridden": [],
            "criteria_count": 0,
            "total_delta": 0.0,
            "by_pillar_delta": {},
        }

    applied_crits = []
    by_pillar_delta = {}

    for pillar, blk in bloc_results.items():
        items = blk.get("kept_criteria") or []
        if not items:
            by_pillar_delta[pillar] = 0.0
            continue
        old_total = float(blk.get("rawTotal") or 0)
        pillar_delta = 0.0
        for item in items:
            cid = item.get("id") or item.get("criterion_id") or item.get("code")
            if not cid or cid not in semantic_scores:
                continue
            try:
                old_score = float(item.get("score") or 0)
            except (TypeError, ValueError):
                old_score = 0.0
            new = semantic_scores[cid]
            new_score = float(new.get("score") or 0)

            # V21.E.A1 + V21.G — Préserver vision_lift ET intelligence_lift :
            # prendre le MAX si critère a été lifté par Vision ou par Intelligence.
            # Sans ce fix, le semantic_overlay (Haiku 4.5 per-critère) peut écraser
            # un lift qui a démontré que l'asset est OK dans son contexte business.
            vision_lifted = bool(item.get("_vision_lift"))
            intelligence_lifted = bool(item.get("_intelligence_lift"))
            if (vision_lifted or intelligence_lifted) and old_score > new_score:
                lift_type = "vision" if vision_lifted else "intelligence"
                if vision_lifted and intelligence_lifted:
                    lift_type = "vision+intelligence"
                item["regex_score"] = old_score
                item["regex_verdict"] = item.get("tier") or item.get("verdict")
                item["semantic_score_seen"] = new_score
                item["semantic_rationale_skipped"] = new.get("rationale")
                item["method"] = f"{lift_type}_lift_preserved_over_semantic"
                continue

            item["regex_score"] = old_score
            item["regex_verdict"] = item.get("tier") or item.get("verdict")
            item["score"] = new_score
            item["tier"] = new["verdict"]
            item["semantic_rationale"] = new["rationale"]
            item["method"] = "semantic_haiku"
            pillar_delta += new_score - old_score
            applied_crits.append({
                "id": cid,
                "pillar": pillar,
                "regex_score": round(old_score, 2),
                "semantic_score": round(new["score"], 2),
                "delta": round(new["score"] - old_score, 2),
                "verdict": new["verdict"],
            })
        by_pillar_delta[pillar] = round(pillar_delta, 2)
        if abs(pillar_delta) > 0.001:
            new_total = round(old_total + pillar_delta, 2)
            raw_max = float(blk.get("rawMax") or 0)
            blk["pre_semantic_rawTotal"] = round(old_total, 2)
            blk["rawTotal"] = new_total
            blk["score100"] = round(new_total / raw_max * 100, 1) if raw_max else 0.0
            blk["semantic_delta"] = round(pillar_delta, 2)

    total_delta = round(sum(a["delta"] for a in applied_crits), 2)
    return {
        "applied": True,
        "version": "1.0",
        "model": "claude-haiku-4-5-20251001",
        "criteria_overridden": applied_crits,
        "criteria_count": len(applied_crits),
        "total_delta": total_delta,
        "by_pillar_delta": by_pillar_delta,
        "semantic_criteria_available": sorted(semantic_scores.keys()),
    }


def _apply_exclusions_to_bloc(bloc: str, bloc_result: dict, exclusions: set[str]) -> dict:
    """Post-filter bloc_result : retire critères exclus, recalcule rawTotal/rawMax."""
    if not bloc_result or bloc_result.get("error"):
        return {**(bloc_result or {}), "bloc": bloc, "applied_exclusions": []}

    items = _extract_criteria_from_bloc_result(bloc_result)
    if not items:
        # Nothing to filter — return as-is but flag
        return {
            **bloc_result,
            "bloc": bloc,
            "applied_exclusions": [],
            "_filter_note": "could not locate criteria list in result; pass-through",
        }

    kept = []
    removed = []
    for item in items:
        cid = item.get("id") or item.get("criterion_id") or item.get("code")
        if cid and cid in exclusions:
            removed.append(cid)
            continue
        kept.append(item)

    # Recompute raw totals if score fields present
    def _score_of(it):
        for k in ("score", "points", "finalScore", "rawScore"):
            if k in it and isinstance(it[k], (int, float)):
                return float(it[k])
        # tier mapping
        tier = (it.get("tier") or it.get("level") or "").lower()
        return {"top": 3.0, "ok": 1.5, "critical": 0.0}.get(tier, 0.0)

    def _max_of(it):
        for k in ("max", "maxScore", "rawMax"):
            if k in it and isinstance(it[k], (int, float)):
                return float(it[k])
        return 3.0

    raw_total_kept = sum(_score_of(i) for i in kept)
    raw_max_kept = sum(_max_of(i) for i in kept)
    score100_kept = round((raw_total_kept / raw_max_kept) * 100, 1) if raw_max_kept else 0.0

    return {
        "bloc": bloc,
        "original_rawTotal": bloc_result.get("rawTotal") or bloc_result.get("finalTotal"),
        "original_rawMax": bloc_result.get("max") or bloc_result.get("rawMax") or bloc_result.get("finalMax"),
        "original_score100": bloc_result.get("score100"),
        "kept_criteria_count": len(kept),
        "rawTotal": round(raw_total_kept, 2),
        "rawMax": round(raw_max_kept, 2),
        "score100": score100_kept,
        "applied_exclusions": removed,
        "kept_criteria": [
            {
                "id": i.get("id") or i.get("criterion_id") or i.get("code"),
                "tier": i.get("tier") or i.get("level"),
                "score": _score_of(i),
                "max": _max_of(i),
                # V21.E + V21.G — preserve lift annotations through projection
                "_vision_lift": i.get("_vision_lift"),
                "_intelligence_lift": i.get("_intelligence_lift"),
                "method": i.get("method"),
            }
            for i in kept
        ],
    }


def orchestrate(label: str, page_type: str) -> dict:
    """Full V12 scoring for (label, pageType)."""
    if page_type not in list_page_types():
        raise ValueError(f"Unknown pageType '{page_type}'")

    # Look in both captures (clients) and golden (reference dataset)
    capture_dir_candidates = [
        ROOT / "data" / "captures" / label / page_type,
        ROOT / "data" / "captures" / label,
        ROOT / "data" / "golden" / label / page_type,
        ROOT / "data" / "golden" / label,
    ]
    capture_dir = next((d for d in capture_dir_candidates if (d / "capture.json").exists()), None)
    if capture_dir is None:
        raise FileNotFoundError(f"No capture.json for {label}/{page_type}")

    exclusions = set(get_exclusions(page_type))
    exclusion_reasons = get_exclusion_reasons(page_type)
    max_per = get_max_for_page_type(page_type)

    # ── 1. Run 6 bloc scorers and filter results ──────────────────────────
    bloc_results: dict[str, dict] = {}
    for pillar in PILLARS:
        raw = _run_bloc_scorer(pillar, label, page_type, capture_dir)
        bloc_results[pillar] = _apply_exclusions_to_bloc(pillar, raw or {}, exclusions)

    # ── 1b. Score v3.1.0 universal extensions (per_09/10/11, coh_07/08/09, psy_07/08) ──
    cap, page_html, _ = ssc._load_capture(label, page_type)
    applicable_ext_ids = [cid for cid in sue.EXTENSIONS.keys() if cid not in exclusions]
    extensions_result = sue.score_extensions(cap, page_html, page_type, applicable_ext_ids)
    # Merge extensions into corresponding pillar bloc_results
    for pillar, ext_block in extensions_result["byPillar"].items():
        blk = bloc_results.setdefault(pillar, {"bloc": pillar, "rawTotal": 0, "rawMax": 0,
                                                "kept_criteria": [], "applied_exclusions": []})
        blk.setdefault("kept_criteria", []).extend(ext_block["criteria"])
        blk["rawTotal"] = round((blk.get("rawTotal") or 0) + ext_block["rawTotal"], 2)
        blk["rawMax"] = round((blk.get("rawMax") or 0) + ext_block["rawMax"], 2)
        blk["score100"] = round(blk["rawTotal"] / blk["rawMax"] * 100, 1) if blk["rawMax"] else 0.0
        blk["v3_1_0_extensions_applied"] = [c["id"] for c in ext_block["criteria"]]

    # ── 1c. Apply SEMANTIC OVERLAY (Haiku 4.5) ────────────────────────────
    # Fix bug 2026-04-18 : semantic scores were generated (score_semantic.json)
    # mais jamais consommés par l'orchestrateur. Les 18 critères créatifs évalués
    # par Haiku (hero_01 H1 quality, per_01 benefit-first, coh_03 scent-trail…)
    # remplacent maintenant leurs équivalents regex dans les kept_criteria.
    semantic_scores = _load_semantic_scores(capture_dir)
    semantic_overlay = _apply_semantic_overlay(bloc_results, semantic_scores)

    # ── 1d. Apply CONTEXTUAL OVERLAY (P1.B doctrine v3.2) ─────────────────
    # Post-semantic, apply synergy-group compensation rules so ENSEMBLE
    # criteria (H1, subtitle, CTA, proofs, coherence signals…) aren't judged
    # in isolation. A weak H1 can be rescued by strong subtitle+CTA+visual;
    # pushy urgency without risk reversal flags manipulation; etc.
    if sco is not None:
        contextual_overlay = sco.apply_contextual_overlay(
            bloc_results, page_type, capture_dir=capture_dir
        )
    else:
        contextual_overlay = {"applied": False, "reason": "score_contextual_overlay module not loaded"}

    # ── 1e. Apply APPLICABILITY OVERLAY (P2.A doctrine v3.2) ──────────────
    # Reads data/doctrine/applicability_matrix_v1.json — enforces NA/REQUIRED/
    # BONUS/OPTIONAL per (pageType × business_type) and computes weight_bias.
    if sao is not None:
        applicability_overlay = sao.apply_applicability_overlay(
            bloc_results, label, page_type
        )
    else:
        applicability_overlay = {"applied": False, "reason": "score_applicability_overlay module not loaded"}

    # ── 2. Score specific criteria ────────────────────────────────────────
    specific_result = ssc.score_page_type_specific(cap, page_html, page_type)

    # ── 2b. Score UTILITY_BANNER (Bloc 7) — Étape 1a 2026-04-15 ────────────
    # Scorer dédié qui ne s'active que si perception_v13 détecte un cluster UTILITY_BANNER.
    # Contribution au score page : 5-10% selon variant/pageType (cf score_utility_banner.py).
    utility_result = None
    try:
        utility_script = SCRIPTS / "score_utility_banner.py"
        if utility_script.exists():
            r = subprocess.run(
                [sys.executable, str(utility_script), label, page_type],
                capture_output=True, text=True, timeout=30,
            )
            ub_file = capture_dir / "score_utility_banner.json"
            if ub_file.exists():
                utility_result = json.loads(ub_file.read_text(encoding="utf-8"))
    except Exception as e:
        utility_result = {"error": f"utility_banner scorer: {e}"}

    # ── 3. Aggregate into pageType-aware total ────────────────────────────
    universal_raw_total = sum((b.get("rawTotal") or 0) for b in bloc_results.values())
    universal_raw_max = sum((b.get("rawMax") or 0) for b in bloc_results.values())
    specific_raw_total = specific_result.get("rawTotal") or 0
    specific_raw_max = specific_result.get("rawMax") or 0

    combined_raw_total = universal_raw_total + specific_raw_total
    combined_raw_max = universal_raw_max + specific_raw_max

    # Expected max per doctrine (sanity check)
    expected_max = max_per.get("rawMax", 0)
    delta_vs_expected = round(combined_raw_max - expected_max, 2) if expected_max else None

    # Default linear aggregation
    linear_score100 = round((combined_raw_total / combined_raw_max) * 100, 1) if combined_raw_max else 0.0

    # Apply pageTypeMultipliers if defined (e.g. quiz_vsl : 70% specific / 30% universal)
    multipliers = get_page_type_multipliers(page_type)
    weighted_score100 = None
    if multipliers:
        uni_s = (universal_raw_total / universal_raw_max * 100) if universal_raw_max else 0.0
        spe_s = (specific_raw_total / specific_raw_max * 100) if specific_raw_max else 0.0
        weighted_score100 = round(
            uni_s * multipliers["universalWeight"] + spe_s * multipliers["specificWeight"],
            1,
        )
        score100 = weighted_score100
    else:
        score100 = linear_score100

    review_count = specific_result.get("reviewRequiredCount", 0)

    # ── 3b. Business-type weighted aggregate (P2.A) ───────────────────────
    bt_weighted_score100 = None
    bt_weight_bias = {}
    if applicability_overlay.get("applied") or applicability_overlay.get("weight_bias"):
        bt_weight_bias = applicability_overlay.get("weight_bias", {})
    elif sao is not None:
        bt_weight_bias = sao.get_weight_bias(
            sao.get_business_type_for_label(label)
        ) if applicability_overlay is not None else {}
    if bt_weight_bias and any(v != 1.0 for v in bt_weight_bias.values()):
        # Weighted average of pillar score100s using weight_bias
        total_w = 0.0
        total_ws = 0.0
        for pillar, blk in bloc_results.items():
            s = float(blk.get("score100") or 0)
            max_pts = float(blk.get("rawMax") or 0)
            w = bt_weight_bias.get(pillar, 1.0) * max_pts  # importance scales with raw capacity × bias
            total_ws += s * w
            total_w += w
        bt_weighted_score100 = round(total_ws / total_w, 1) if total_w else None

    # ── 3c. V23.D — Funnel-aware aggregate (40% intro / 60% flow) ─────────
    # Pour les pages funnel, le score "intro statique" seul est insuffisant :
    # un quiz_vsl avec hero superbe mais flow cassé (84% halt) reste mauvais.
    # On lit score_funnel.json (produit par score_funnel.py) et on rebalance
    # l'aggregate.score100 si applicable. L'intro-only est conservé pour traçabilité.
    funnel_data = _load_funnel_score(capture_dir, page_type)
    intro_score100 = score100  # canonical intro score (computed above)
    funnel_score100 = None
    funnel_aware_score100 = None
    funnel_weight_applied = None
    if funnel_data:
        funnel_score100 = funnel_data.get("score100")
        if isinstance(funnel_score100, (int, float)):
            funnel_aware_score100 = round(
                intro_score100 * FUNNEL_WEIGHT_INTRO + funnel_score100 * FUNNEL_WEIGHT_FLOW,
                1,
            )
            funnel_weight_applied = {
                "intro": FUNNEL_WEIGHT_INTRO,
                "flow": FUNNEL_WEIGHT_FLOW,
            }
            # Replace canonical aggregate with funnel-aware
            score100 = funnel_aware_score100

    # ── 4. Emit ───────────────────────────────────────────────────────────
    return {
        "doctrineVersion": "v3.2.0-draft — doctrine V13 — 2026-04-18 (ensemble-aware)",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "label": label,
        "pageType": page_type,
        "maxPerPageType": max_per,
        "exclusions": {
            "applied": sorted(exclusions),
            "reasons": {k: v for k, v in exclusion_reasons.items() if k in exclusions},
            "count": len(exclusions),
        },
        "universal": {
            "byPillar": bloc_results,
            "rawTotal": round(universal_raw_total, 2),
            "rawMax": round(universal_raw_max, 2),
            "score100": round((universal_raw_total / universal_raw_max) * 100, 1) if universal_raw_max else 0.0,
        },
        "specific": {
            "result": specific_result,
            "rawTotal": round(specific_raw_total, 2),
            "rawMax": round(specific_raw_max, 2),
            "score100": specific_result.get("score100"),
            "reviewRequiredCount": review_count,
        },
        "aggregate": {
            "rawTotal": round(combined_raw_total, 2),
            "rawMax": round(combined_raw_max, 2),
            "expectedRawMax": expected_max,
            "delta_vs_expected": delta_vs_expected,
            "score100": score100,
            "linearScore100": linear_score100,
            "weightedScore100": weighted_score100,
            "pageTypeMultipliers": multipliers,
            "bt_weighted_score100": bt_weighted_score100,
            "bt_weight_bias": bt_weight_bias,
            # V23.D — Funnel-aware fields (only set for FUNNEL_PAGE_TYPES with score_funnel.json)
            "score100_intro_only": intro_score100,
            "score100_funnel_aware": funnel_aware_score100,
            "funnel_weight_applied": funnel_weight_applied,
        },
        "funnel": (
            {
                "applicable": True,
                "score100": funnel_score100,
                "criteria": funnel_data.get("criteria") if funnel_data else None,
                "flow_meta": funnel_data.get("flow_meta") if funnel_data else None,
            }
            if funnel_data
            else {"applicable": page_type in FUNNEL_PAGE_TYPES, "score100": None}
        ),
        "utility_banner": utility_result,
        "semantic_overlay": semantic_overlay,
        "contextual_overlay": contextual_overlay,
        "applicability_overlay": applicability_overlay,
        "notes": [
            "Universal criteria are filtered post-scorer using page_type_criteria.json.universalExclusions.",
            "Specific criteria are scored by score_specific_criteria.py (35 detectors + LLM-review fallback).",
            "Dual-viewport aggregation is delegated to bloc scorers' own viewport_check logic.",
            "delta_vs_expected should be ≈ 0 once all bloc scorers expose criterion IDs cleanly.",
            "Semantic overlay (v1.0, 2026-04-18): Haiku scores replace regex for 18 creative criteria when score_semantic.json exists. Each kept_criterion with method='semantic_haiku' also stores regex_score/regex_verdict for traceability. Pillar rawTotal / score100 are recomputed post-overlay; aggregate follows.",
            "Contextual overlay (P1.B, doctrine v3.2.0-draft, 2026-04-18): ENSEMBLE-scope criteria may be rescued upwards by strong peers in the same synergy group (HERO_ENSEMBLE, BENEFIT_FLOW, SOCIAL_PROOF_STACK…) or penalized for contradictions (manipulation flag: urgency without risk reversal). Each affected kept_criterion records pre_contextual_score/tier + contextual_rule + rationale. ASSET-scope criteria (tech_*, counts) are INVARIANT.",
        ],
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: score_page_type.py <label> [pageType]", file=sys.stderr)
        print(f"Known pageTypes: {list_page_types()}", file=sys.stderr)
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"

    result = orchestrate(label, page_type)
    # Write alongside the actual capture_dir (captures OR golden)
    out_dir = None
    for root_name in ("captures", "golden"):
        cand = ROOT / "data" / root_name / label / page_type
        if (cand / "capture.json").exists():
            out_dir = cand
            break
        cand2 = ROOT / "data" / root_name / label
        if (cand2 / "capture.json").exists():
            out_dir = cand2
            break
    if out_dir is None:
        out_dir = ROOT / "data" / "captures" / label / page_type
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "score_page_type.json"
    out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    agg = result["aggregate"]
    uni = result["universal"]
    spec = result["specific"]
    print(f"✅ {label}/{page_type} (doctrine {result['doctrineVersion'][:6]})")
    print(f"   Universal: {uni['rawTotal']}/{uni['rawMax']} = {uni['score100']}/100 "
          f"(exclusions applied: {result['exclusions']['count']})")
    print(f"   Specific : {spec['rawTotal']}/{spec['rawMax']} = {spec['score100']}/100 "
          f"(review_required: {spec['reviewRequiredCount']})")
    print(f"   Aggregate: {agg['rawTotal']}/{agg['rawMax']} = {agg['score100']}/100 "
          f"(expected rawMax={agg['expectedRawMax']}, Δ={agg['delta_vs_expected']})")
    so = result.get("semantic_overlay") or {}
    if so.get("applied"):
        print(f"   Semantic : {so['criteria_count']} critères overridés par Haiku "
              f"(Δtotal={so['total_delta']:+.1f} sur rawTotal)")
    else:
        print(f"   Semantic : non appliqué ({so.get('reason','unknown')})")
    co = result.get("contextual_overlay") or {}
    if co.get("applied"):
        print(f"   Contextual: {co['adjustments_count']} rescues "
              f"(Δtotal={co['total_delta']:+.1f}, rules={','.join(co.get('rules_fired', []))})")
    else:
        print(f"   Contextual: non appliqué ({co.get('reason','no rules fired')})")
    fnl = result.get("funnel") or {}
    if fnl.get("score100") is not None:
        intro_only = agg.get("score100_intro_only")
        print(f"   Funnel   : intro={intro_only}/100 + flow={fnl['score100']}/100 → aware={agg['score100']}/100 "
              f"(weights {FUNNEL_WEIGHT_INTRO:.0%}/{FUNNEL_WEIGHT_FLOW:.0%})")
    elif fnl.get("applicable"):
        print(f"   Funnel   : applicable mais score_funnel.json absent — run capture_funnel_pipeline.py + score_funnel.py")
    print(f"   → {out_file}")


if __name__ == "__main__":
    main()
