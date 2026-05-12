#!/usr/bin/env python3
"""V23.B — Semantic dedup post-LLM des recos individuelles + cluster par page.

Le pipeline reco produit 2 outputs :
  - recos_v13_final.json (individual, 1 reco par criterion)
  - recos_v21_cluster_final.json (cluster, 1 reco par SYNERGY_GROUP)

Quand un cluster couvre déjà hero_01/03/05 et qu'une reco individual hero_03 est
aussi générée, ou qu'une reco per_04 dit "ajouter du proof" alors qu'un cluster
SOCIAL_PROOF_STACK le dit déjà → DOUBLON. Coût pour l'utilisateur : redondance,
charge cognitive, dilution des priorités.

Approche : Jaccard token-similarity sur (target_element + after) avec stopwords FR.
Pas d'API LLM (0$). Marque le perdant `_superseded_by = <id_winner>`.

Output : modifie in-place `recos_v13_final.json` avec flags _superseded_by + _dedup_kept.
        Émet aussi `recos_dedup_report.json` pour traçabilité.

Usage:
    python3 recos_dedup.py --client japhy --page home
    python3 recos_dedup.py --all
    python3 recos_dedup.py --all --dry-run   # pas d'écriture, juste report
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

# Stopwords FR/EN minimalist — empêche faux positifs sur mots vides
STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "à", "au", "aux", "et",
    "ou", "mais", "dans", "sur", "pour", "par", "avec", "sans", "sous", "que",
    "qui", "quoi", "qu'", "ne", "pas", "se", "te", "me", "vous", "nous", "ils",
    "elle", "il", "ce", "ces", "son", "sa", "ses", "leur", "leurs", "ceux",
    "cette", "tout", "tous", "toute", "toutes", "plus", "moins", "très", "bien",
    "the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with", "is",
    "are", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "cant",
    "votre", "vos", "notre", "nos", "mon", "ton", "ma", "ta", "moi", "toi",
    "lui", "leur", "y", "en", "n", "l", "d", "s",
}

# Target-element extraction : on utilise le criterion_id pour catégoriser
ELEMENT_BY_PREFIX = {
    "hero_01": "hero_h1", "hero_02": "hero_subtitle", "hero_03": "hero_cta",
    "hero_04": "hero_visual", "hero_05": "hero_proof", "hero_06": "hero_overall",
    "per_01": "feature_benefit", "per_02": "cta_specificity", "per_03": "narrative",
    "per_04": "social_proof", "per_05": "pricing", "per_06": "testimonial",
    "per_07": "case_study", "per_08": "value_stack", "per_09": "schwartz_aware",
    "per_10": "proof_diversity", "per_11": "benefit_laddering",
    "ux_01": "navigation", "ux_02": "form", "ux_03": "page_speed", "ux_04": "mobile_layout",
    "ux_05": "scroll_depth", "ux_06": "touch_target",
    "coh_01": "scent_trail", "coh_02": "vocab_consistency", "coh_03": "scent_external",
    "coh_04": "page_consistency", "coh_05": "intent_match", "coh_06": "narrative_coh",
    "psy_01": "urgency", "psy_02": "scarcity", "psy_03": "authority",
    "psy_04": "reciprocity", "psy_05": "loss_aversion", "psy_06": "commitment",
    "tech_01": "perf_loading", "tech_02": "perf_fcp", "tech_03": "tech_cwv",
    "funnel_01": "funnel_length", "funnel_02": "funnel_progress",
    "funnel_03": "funnel_friction", "funnel_04": "funnel_result",
    "funnel_05": "funnel_final_cta", "funnel_06": "funnel_proof",
    "funnel_07": "funnel_recovery",
}

# Cluster names ↔ touched elements
CLUSTER_TOUCHES = {
    "HERO_ENSEMBLE": {"hero_h1", "hero_subtitle", "hero_cta", "hero_visual", "hero_proof", "hero_overall"},
    "BENEFIT_FLOW": {"feature_benefit", "narrative", "value_stack", "benefit_laddering"},
    "SOCIAL_PROOF_STACK": {"social_proof", "testimonial", "case_study", "proof_diversity"},
    "VISUAL_HIERARCHY": {"hero_visual", "scroll_depth", "navigation"},
    "COHERENCE_FULL": {"scent_trail", "vocab_consistency", "scent_external", "page_consistency", "intent_match", "narrative_coh"},
    "EMOTIONAL_DRIVERS": {"urgency", "scarcity", "authority", "loss_aversion", "commitment"},
}


def _tokenize(text: str) -> set[str]:
    """Lowercase tokens (≥ 3 chars) sans stopwords."""
    if not text:
        return set()
    text = text.lower()
    # Remove markdown/quotes
    text = re.sub(r"[\"\'`*_~\[\]()]+", " ", text)
    # Tokens ≥ 3 chars
    tokens = re.findall(r"[a-zàâäéèêëîïôöùûüç0-9]{3,}", text, re.UNICODE)
    return {t for t in tokens if t not in STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _element_of(criterion_id: str) -> Optional[str]:
    """Returns canonical element touched by this criterion."""
    if criterion_id in ELEMENT_BY_PREFIX:
        return ELEMENT_BY_PREFIX[criterion_id]
    # Try prefix
    for k, v in ELEMENT_BY_PREFIX.items():
        if criterion_id.startswith(k.split("_")[0] + "_"):
            return v.split("_")[0]
    return None


def _ice_score_of(reco: dict) -> float:
    """Returns numeric ICE score (handle both dict shape and legacy float)."""
    ice = reco.get("ice_score")
    if isinstance(ice, dict):
        return float(ice.get("computed_score") or 0)
    if isinstance(ice, (int, float)):
        return float(ice)
    return 0.0


def _build_fingerprint(reco: dict) -> dict:
    """Build dedup fingerprint from a reco."""
    crit_id = reco.get("criterion_id") or reco.get("cluster_id") or ""
    after = reco.get("after") or ""
    why = reco.get("why") or ""
    element = _element_of(crit_id)
    # If it's a cluster reco, derive elements from criteria_covered
    if not element and reco.get("cluster_id"):
        cluster_name = reco.get("cluster_id") or ""
        elements = CLUSTER_TOUCHES.get(cluster_name, set())
        element = "+".join(sorted(elements)) if elements else cluster_name.lower()
    return {
        "id": crit_id,
        "is_cluster": bool(reco.get("cluster_id") and not reco.get("criterion_id")),
        "element": element,
        "after_tokens": _tokenize(after) | _tokenize(why),
        "ice": _ice_score_of(reco),
        "priority": reco.get("priority"),
    }


def _is_duplicate(fp1: dict, fp2: dict, sim_threshold: float = 0.45) -> tuple[bool, float]:
    """Two recos are duplicates if they touch overlapping elements AND have similar after content."""
    # Element overlap: simple substring or set overlap
    e1, e2 = fp1["element"] or "", fp2["element"] or ""
    if not e1 or not e2:
        return False, 0.0
    s1 = set(e1.split("+"))
    s2 = set(e2.split("+"))
    elem_overlap = bool(s1 & s2) or e1 == e2 or e1 in e2 or e2 in e1
    if not elem_overlap:
        return False, 0.0
    sim = _jaccard(fp1["after_tokens"], fp2["after_tokens"])
    return sim >= sim_threshold, sim


def dedup_page(client: str, page: str, dry_run: bool = False) -> dict:
    """Dedup recos individuelles ET clusters d'une page. Marque les superseded.
    Cluster wins on tie (cluster covers wider scope = more value)."""
    page_dir = CAPTURES / client / page
    indiv_path = page_dir / "recos_v13_final.json"
    cluster_path = page_dir / "recos_v21_cluster_final.json"
    if not indiv_path.exists():
        return {"client": client, "page": page, "skipped": "no_individual_recos"}

    indiv = json.load(open(indiv_path))
    cluster = json.load(open(cluster_path)) if cluster_path.exists() else {"clusters": []}

    indiv_recos = indiv.get("recos") or []
    cluster_recos = cluster.get("clusters") or []

    # Build fingerprints
    fps_indiv = [(i, r, _build_fingerprint(r)) for i, r in enumerate(indiv_recos)]
    fps_cluster = [(i, r, _build_fingerprint(r)) for i, r in enumerate(cluster_recos)]

    superseded_by_indiv: dict[int, str] = {}  # idx → winner_id
    pairs_logged = []

    # Pass 1A : explicit cluster-vs-individual via criteria_covered
    # Si un cluster déclare couvrir crit_X et qu'on a une reco individual sur crit_X
    # → SUPERSEDED par construction (le cluster traite le critère dans son contexte holistique).
    cluster_covered_to_id: dict[str, str] = {}
    for ci, cr, cfp in fps_cluster:
        cid = cr.get("cluster_id") or f"cluster_{ci}"
        for crit in (cr.get("criteria_covered") or []):
            cluster_covered_to_id.setdefault(crit, cid)

    for ii, ir, ifp in fps_indiv:
        crit = ir.get("criterion_id")
        if crit and crit in cluster_covered_to_id:
            if ir.get("_skipped") or ir.get("_fallback"):
                continue
            superseded_by_indiv[ii] = cluster_covered_to_id[crit]
            pairs_logged.append({
                "loser_id": crit, "loser_kind": "individual",
                "winner_id": cluster_covered_to_id[crit], "winner_kind": "cluster",
                "similarity": 1.0, "reason": "cluster.criteria_covered includes this criterion_id",
            })

    # Pass 1B : cluster vs individual via semantic similarity (catch fringe cases not in criteria_covered)
    for ci, cr, cfp in fps_cluster:
        winner_id = cr.get("cluster_id") or f"cluster_{ci}"
        for ii, ir, ifp in fps_indiv:
            if ii in superseded_by_indiv:
                continue
            if ifp.get("_skipped") or ir.get("_skipped"):
                continue
            is_dup, sim = _is_duplicate(cfp, ifp)
            if is_dup:
                superseded_by_indiv[ii] = winner_id
                pairs_logged.append({
                    "loser_id": ifp["id"],
                    "loser_kind": "individual",
                    "winner_id": winner_id,
                    "winner_kind": "cluster",
                    "similarity": round(sim, 3),
                    "reason": "cluster covers same element + similar after",
                })

    # Pass 2 : individual vs individual — best ICE wins
    for i, (ii_a, r_a, fp_a) in enumerate(fps_indiv):
        if ii_a in superseded_by_indiv:
            continue
        if r_a.get("_skipped") or r_a.get("_fallback"):
            continue
        for ii_b, r_b, fp_b in fps_indiv[i + 1:]:
            if ii_b in superseded_by_indiv:
                continue
            if r_b.get("_skipped") or r_b.get("_fallback"):
                continue
            is_dup, sim = _is_duplicate(fp_a, fp_b)
            if is_dup:
                # Higher ICE wins (tie-break: lower index wins)
                if fp_b["ice"] > fp_a["ice"]:
                    superseded_by_indiv[ii_a] = fp_b["id"]
                    pairs_logged.append({
                        "loser_id": fp_a["id"], "loser_kind": "individual",
                        "winner_id": fp_b["id"], "winner_kind": "individual",
                        "similarity": round(sim, 3), "reason": "lower ICE",
                    })
                    break  # a is dead, no point comparing further
                else:
                    superseded_by_indiv[ii_b] = fp_a["id"]
                    pairs_logged.append({
                        "loser_id": fp_b["id"], "loser_kind": "individual",
                        "winner_id": fp_a["id"], "winner_kind": "individual",
                        "similarity": round(sim, 3), "reason": "lower ICE",
                    })

    # Apply flags
    n_kept = 0
    n_superseded = 0
    for ii, ir, ifp in fps_indiv:
        if ii in superseded_by_indiv:
            ir["_superseded_by"] = superseded_by_indiv[ii]
            ir["_dedup_kept"] = False
            n_superseded += 1
        else:
            ir["_dedup_kept"] = True
            ir.pop("_superseded_by", None)
            n_kept += 1

    # Summary
    report = {
        "client": client,
        "page": page,
        "n_individual_total": len(indiv_recos),
        "n_individual_kept": n_kept,
        "n_individual_superseded": n_superseded,
        "n_clusters": len(cluster_recos),
        "pairs_logged": pairs_logged,
        "dedup_version": "V23.B-jaccard-0.45",
    }

    if not dry_run:
        # Write back individual recos
        indiv["recos"] = indiv_recos
        indiv["_dedup_applied"] = True
        indiv["_dedup_report"] = {
            "n_kept": n_kept,
            "n_superseded": n_superseded,
            "version": report["dedup_version"],
        }
        tmp = indiv_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(indiv, ensure_ascii=False, indent=2))
        tmp.replace(indiv_path)
        # Write report
        report_path = page_dir / "recos_dedup_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.all:
        for cd in sorted(CAPTURES.iterdir()):
            if not cd.is_dir() or cd.name.startswith(("_", ".")):
                continue
            for pd in sorted(cd.iterdir()):
                if pd.is_dir() and (pd / "recos_v13_final.json").exists():
                    targets.append((cd.name, pd.name))
    elif args.client and args.page:
        targets.append((args.client, args.page))
    else:
        ap.error("--client+--page OR --all")

    total_kept = total_superseded = 0
    for c, p in targets:
        r = dedup_page(c, p, dry_run=args.dry_run)
        if r.get("skipped"):
            continue
        kept = r["n_individual_kept"]
        sup = r["n_individual_superseded"]
        total_kept += kept
        total_superseded += sup
        if sup:
            print(f"  • {c}/{p}: {sup} superseded / {kept} kept" +
                  (f" (cluster wins: {sum(1 for x in r['pairs_logged'] if x['winner_kind']=='cluster')})"
                   if r['pairs_logged'] else ""))

    n_total = total_kept + total_superseded
    pct = 100 * total_superseded / n_total if n_total else 0
    print(f"\n═══ Dedup complete: {len(targets)} pages ═══")
    print(f"  Kept       : {total_kept}")
    print(f"  Superseded : {total_superseded} ({pct:.1f}%)")
    if args.dry_run:
        print("  (dry-run — no files written)")


if __name__ == "__main__":
    main()
