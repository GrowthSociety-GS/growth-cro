"""V29 Sprint B V26.AA — Learning Layer Audit-Based : doctrine_proposals depuis 56 clients curatés.

Réponse au trou architectural identifié 2026-05-04 (audit profond Mathis) :
le `learning_layer.py` original (V28) attendait des `experiments/*.json` A/B-tested
pour générer des doctrine_proposals. Mais ces experiments n'existent pas (0 outcomes
mesurés). Conséquence : `data/learning/doctrine_proposals/` est VIDE depuis création.

V29 audit-based bypass ce blocage en exploitant **la donnée disponible** :
- 56 clients curatés V26 × ~3.3 pages = 185 pages avec score_page_type.json
- 1 disagreement multi-judge (V26.D rare)
- 72 lifecycles progressés (V26.B)

Approche : agréger les scores audit par (criterion_id, business_category) sur la base
empirique des 185 pages curatées et générer des proposals quand pattern fort.

Heuristiques :
- Critère CRITICAL sur >70% des pages d'un business_category → règle peut être trop stricte
  → Proposal type "calibrate_threshold" : assouplir scoring.critical
- Critère TOP sur >85% des pages → règle sous-discriminante (tout le monde réussit)
  → Proposal type "tighten_threshold" : durcir scoring.top
- Critère N/A sur >50% des pages d'un business_category → pageTypes filter mal calibré
  → Proposal type "adjust_page_types" : retirer business_category de pageTypes
- Critère absent du score (jamais évalué) → orphelin doctrine
  → Proposal type "review_applicability"

Inputs :
- data/curated_clients_v26.json (56 clients)
- data/captures/<slug>/<page_type>/score_page_type.json (× 185)
- playbook/bloc_*_v3.json (doctrine V3.2.1 — 54 critères)

Outputs :
- data/learning/audit_based_stats.json
- data/learning/audit_based_proposals/<proposal_id>.json
- data/learning/audit_based_summary.md (pour Mathis review)

Usage CLI :
    python3 skills/site-capture/scripts/learning_layer_v29_audit_based.py
    python3 skills/site-capture/scripts/learning_layer_v29_audit_based.py --min-coverage 5
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from collections import defaultdict
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"
LEARNING_DIR = ROOT / "data" / "learning"
PROPOSALS_DIR = LEARNING_DIR / "audit_based_proposals"

# Thresholds
THRESHOLDS = {
    "critical_alert_pct": 0.70,    # >70% pages CRITICAL → règle trop stricte
    "top_alert_pct": 0.85,         # >85% pages TOP → règle sous-discriminante
    "na_alert_pct": 0.50,          # >50% pages N/A → pageTypes mal calibré
    "min_pages_per_segment": 5,    # min échantillon par (criterion_id, business_category)
}


def _load_json_safe(p: pathlib.Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def collect_curated_scores() -> list[dict]:
    """Walk les 56 clients curatés V26, charge tous les score_page_type.json."""
    curated = json.load(open(ROOT / "data" / "curated_clients_v26.json"))
    out = []
    for c in curated["clients"]:
        cd = CAPTURES / c["id"]
        if not cd.exists():
            continue
        for pt in c["page_types"]:
            f = cd / pt / "score_page_type.json"
            d = _load_json_safe(f)
            if d:
                d["_client"] = c["id"]
                d["_business_category"] = c.get("business_type", "unknown")
                d["_page_type"] = pt
                out.append(d)
    return out


def extract_per_criterion_verdicts(scores: list[dict]) -> list[dict]:
    """Extrait les verdicts par critère.

    Structure réelle score_page_type.json :
      universal.byPillar.<pillar>.kept_criteria[] = [{id, score, max, tier}, ...]
      specific.byPillar.<pillar>.kept_criteria[] = idem (utility, applicable)
    """
    verdicts = []
    for s in scores:
        # universal piliers (hero/persuasion/ux/coherence/psycho/tech)
        universal = s.get("universal", {}) or {}
        by_pillar = universal.get("byPillar", {}) or {}
        for pillar_name, pillar_data in by_pillar.items():
            if not isinstance(pillar_data, dict):
                continue
            for c in pillar_data.get("kept_criteria", []):
                cid = c.get("id")
                if not cid:
                    continue
                score_val = c.get("score")
                weight = c.get("max", 3)
                tier = c.get("tier")  # may be null
                verdict = _verdict_from_tier_or_score(tier, score_val, weight)
                verdicts.append({
                    "client": s["_client"],
                    "page_type": s["_page_type"],
                    "business_category": s["_business_category"],
                    "pillar": pillar_name,
                    "criterion_id": cid,
                    "verdict": verdict,
                    "score": score_val,
                    "weight": weight,
                })
        # specific piliers (utility...)
        specific = s.get("specific", {}) or {}
        spec_by_pillar = specific.get("byPillar", {}) or {}
        for pillar_name, pillar_data in spec_by_pillar.items():
            if not isinstance(pillar_data, dict):
                continue
            for c in pillar_data.get("kept_criteria", []):
                cid = c.get("id")
                if not cid:
                    continue
                score_val = c.get("score")
                weight = c.get("max", 3)
                tier = c.get("tier")
                verdict = _verdict_from_tier_or_score(tier, score_val, weight)
                verdicts.append({
                    "client": s["_client"],
                    "page_type": s["_page_type"],
                    "business_category": s["_business_category"],
                    "pillar": pillar_name,
                    "criterion_id": cid,
                    "verdict": verdict,
                    "score": score_val,
                    "weight": weight,
                })
    return verdicts


def _verdict_from_tier_or_score(tier: Optional[str], score, weight) -> str:
    """tier peut être 'top'/'ok'/'critical'/None. Si None, infère depuis score/weight."""
    if tier:
        return tier.upper()
    if score is None:
        return "N/A"
    try:
        s = float(score)
        w = float(weight or 3)
    except (ValueError, TypeError):
        return "?"
    if s >= w * 0.95:
        return "TOP"
    elif s == 0:
        return "CRITICAL"
    elif s >= w * 0.40:
        return "OK"
    else:
        return "OK"


def _infer_verdict(score, weight) -> str:
    if score is None:
        return "N/A"
    try:
        s = float(score)
        w = float(weight or 3)
    except (ValueError, TypeError):
        return "?"
    if s >= w * 0.95:
        return "TOP"
    elif s >= w * 0.40:
        return "OK"
    elif s == 0:
        return "CRITICAL"
    else:
        return "OK"


def aggregate_by_criterion_segment(verdicts: list[dict]) -> list[dict]:
    """Aggregate verdicts par (criterion_id, business_category)."""
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    for v in verdicts:
        key = (v["criterion_id"], v["business_category"])
        by_key[key].append(v)

    stats = []
    for (cid, biz), vs in sorted(by_key.items()):
        n = len(vs)
        n_top = sum(1 for v in vs if v["verdict"] == "TOP")
        n_ok = sum(1 for v in vs if v["verdict"] == "OK")
        n_critical = sum(1 for v in vs if v["verdict"] == "CRITICAL")
        n_na = sum(1 for v in vs if v["verdict"] == "N/A")
        scored = n - n_na  # pages où le critère a été évalué
        avg_score_pct = (sum((v.get("score") or 0) / max(v.get("weight") or 3, 1) for v in vs if v.get("score") is not None) / max(scored, 1)) * 100 if scored > 0 else None
        stats.append({
            "criterion_id": cid,
            "business_category": biz,
            "n_pages": n,
            "n_top": n_top,
            "n_ok": n_ok,
            "n_critical": n_critical,
            "n_na": n_na,
            "pct_top": round(n_top / n * 100, 1) if n > 0 else 0,
            "pct_ok": round(n_ok / n * 100, 1) if n > 0 else 0,
            "pct_critical": round(n_critical / n * 100, 1) if n > 0 else 0,
            "pct_na": round(n_na / n * 100, 1) if n > 0 else 0,
            "avg_score_pct": round(avg_score_pct, 1) if avg_score_pct is not None else None,
        })
    return stats


def generate_proposals(stats: list[dict], min_pages: int = 5) -> list[dict]:
    """Generate doctrine_proposals quand pattern fort détecté."""
    proposals = []
    today = time.strftime("%Y_%m_%d")

    for s in stats:
        cid = s["criterion_id"]
        biz = s["business_category"]
        n = s["n_pages"]

        # Filtrage : min échantillon
        if n < min_pages:
            continue

        # Pattern 1 : CRITICAL >70% → règle trop stricte
        if s["pct_critical"] >= THRESHOLDS["critical_alert_pct"] * 100:
            proposals.append({
                "proposal_id": f"dup_v29_{today}_{cid}_calibrate_strict_{biz}",
                "type": "calibrate_threshold",
                "subtype": "strict_rule_too_punitive",
                "affected_criteria": [cid],
                "scope": {"business_category": biz},
                "evidence": {
                    "n_pages_evaluated": n,
                    "pct_critical": s["pct_critical"],
                    "pct_top": s["pct_top"],
                    "avg_score_pct": s["avg_score_pct"],
                    "source": "audit-based learning v29 (56 curated clients V26)",
                },
                "proposed_change": (
                    f"Critère {cid} marqué CRITICAL sur {s['pct_critical']:.0f}% des pages "
                    f"de {biz} ({s['n_critical']}/{n}). La règle peut être trop stricte "
                    f"pour ce segment business — vérifier le scoring.critical définition. "
                    f"Score moyen : {s['avg_score_pct']:.0f}%."
                ),
                "risk": (
                    f"Si le pattern est légitime (vraie faiblesse marché), assouplir "
                    f"masquerait un signal CRO réel. Vérifier sur 3-5 pages échantillon."
                ),
                "requires_human_approval": True,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })

        # Pattern 2 : TOP >85% → règle sous-discriminante
        if s["pct_top"] >= THRESHOLDS["top_alert_pct"] * 100:
            proposals.append({
                "proposal_id": f"dup_v29_{today}_{cid}_tighten_lax_{biz}",
                "type": "tighten_threshold",
                "subtype": "lax_rule_under_discriminating",
                "affected_criteria": [cid],
                "scope": {"business_category": biz},
                "evidence": {
                    "n_pages_evaluated": n,
                    "pct_top": s["pct_top"],
                    "pct_critical": s["pct_critical"],
                    "avg_score_pct": s["avg_score_pct"],
                    "source": "audit-based learning v29 (56 curated clients V26)",
                },
                "proposed_change": (
                    f"Critère {cid} marqué TOP sur {s['pct_top']:.0f}% des pages "
                    f"de {biz} ({s['n_top']}/{n}). Règle sous-discriminante — "
                    f"presque tout le monde l'atteint. Durcir scoring.top pour "
                    f"identifier les vraies excellences."
                ),
                "risk": "Durcir trop pourrait pénaliser pages déjà bonnes",
                "requires_human_approval": True,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })

        # Pattern 3 : N/A >50% → pageTypes filter mal calibré
        if s["pct_na"] >= THRESHOLDS["na_alert_pct"] * 100:
            proposals.append({
                "proposal_id": f"dup_v29_{today}_{cid}_filter_na_{biz}",
                "type": "adjust_page_types",
                "subtype": "page_type_filter_mismatch",
                "affected_criteria": [cid],
                "scope": {"business_category": biz},
                "evidence": {
                    "n_pages_evaluated": n,
                    "pct_na": s["pct_na"],
                    "n_na": s["n_na"],
                    "source": "audit-based learning v29 (56 curated clients V26)",
                },
                "proposed_change": (
                    f"Critère {cid} marqué N/A sur {s['pct_na']:.0f}% des pages "
                    f"de {biz} ({s['n_na']}/{n}). Soit le critère ne s'applique pas "
                    f"à ce business_category (retirer de pageTypes), soit il y a "
                    f"un bug de filtering."
                ),
                "risk": "Si on enlève à tort, on perd un signal CRO valide pour quelques cas",
                "requires_human_approval": True,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })

    return proposals


def render_summary_md(stats: list[dict], proposals: list[dict], total_pages: int) -> str:
    """Render summary markdown for Mathis review."""
    lines = [
        f"# Learning Layer V29 Audit-Based — Summary ({time.strftime('%Y-%m-%d %H:%M')})",
        "",
        f"**Source data** : {total_pages} pages (56 clients curatés V26)",
        f"**Statistics computed** : {len(stats)} (criterion_id × business_category)",
        f"**Proposals generated** : {len(proposals)} (requires Mathis approval)",
        "",
        "## Proposals par type",
        "",
    ]
    by_type = defaultdict(list)
    for p in proposals:
        by_type[p["type"]].append(p)
    for ptype, ps in sorted(by_type.items()):
        lines.append(f"### {ptype} ({len(ps)})")
        for p in ps[:10]:  # top 10 par type
            scope = p["scope"].get("business_category", "?")
            crit = p["affected_criteria"][0]
            ev = p["evidence"]
            lines.append(f"- **{crit} / {scope}** — {p['proposed_change'][:200]}")
        if len(ps) > 10:
            lines.append(f"- ... +{len(ps) - 10} more (voir audit_based_proposals/)")
        lines.append("")

    # Top patterns CRITICAL
    lines.append("## Top 10 critères les plus CRITICAL (toutes business_categories)")
    lines.append("")
    lines.append("| Criterion | Business | n pages | % CRITICAL | % TOP | Avg score |")
    lines.append("|---|---|---:|---:|---:|---:|")
    crit_sorted = sorted([s for s in stats if s["n_pages"] >= 5], key=lambda s: -s["pct_critical"])[:10]
    for s in crit_sorted:
        lines.append(f"| {s['criterion_id']} | {s['business_category']} | {s['n_pages']} | {s['pct_critical']}% | {s['pct_top']}% | {s['avg_score_pct']}% |")

    # Top patterns TOP
    lines.append("")
    lines.append("## Top 10 critères les plus TOP (potentiellement sous-discriminants)")
    lines.append("")
    lines.append("| Criterion | Business | n pages | % TOP | % CRITICAL | Avg score |")
    lines.append("|---|---|---:|---:|---:|---:|")
    top_sorted = sorted([s for s in stats if s["n_pages"] >= 5], key=lambda s: -s["pct_top"])[:10]
    for s in top_sorted:
        lines.append(f"| {s['criterion_id']} | {s['business_category']} | {s['n_pages']} | {s['pct_top']}% | {s['pct_critical']}% | {s['avg_score_pct']}% |")

    return "\n".join(lines)


def run(min_pages: int = 5) -> dict:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n══ Learning Layer V29 Audit-Based — Sprint B V26.AA ══\n")
    scores = collect_curated_scores()
    print(f"  ✓ Loaded {len(scores)} score_page_type.json (56 clients curatés)")

    verdicts = extract_per_criterion_verdicts(scores)
    print(f"  ✓ Extracted {len(verdicts)} criterion verdicts")

    stats = aggregate_by_criterion_segment(verdicts)
    print(f"  ✓ Aggregated {len(stats)} (criterion_id × business_category) segments")

    proposals = generate_proposals(stats, min_pages=min_pages)
    print(f"  ✓ Generated {len(proposals)} doctrine proposals (min {min_pages} pages/segment)")

    # Save outputs
    (LEARNING_DIR / "audit_based_stats.json").write_text(
        json.dumps({
            "version": "v29.0.0-sprint-b-v26-aa",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "56 curated clients V26 (data/curated_clients_v26.json)",
            "n_pages_analyzed": len(scores),
            "n_verdicts_extracted": len(verdicts),
            "n_segments": len(stats),
            "thresholds": THRESHOLDS,
            "stats": stats,
        }, ensure_ascii=False, indent=2)
    )
    for p in proposals:
        (PROPOSALS_DIR / f"{p['proposal_id']}.json").write_text(
            json.dumps(p, ensure_ascii=False, indent=2)
        )
    summary_md = render_summary_md(stats, proposals, len(scores))
    (LEARNING_DIR / "audit_based_summary.md").write_text(summary_md)

    print(f"\n  ✓ Outputs saved:")
    print(f"    data/learning/audit_based_stats.json ({len(stats)} segments)")
    print(f"    data/learning/audit_based_proposals/ ({len(proposals)} proposals)")
    print(f"    data/learning/audit_based_summary.md (Mathis review)")

    return {
        "n_pages_analyzed": len(scores),
        "n_verdicts": len(verdicts),
        "n_segments": len(stats),
        "n_proposals": len(proposals),
        "proposals_by_type": {
            t: sum(1 for p in proposals if p["type"] == t)
            for t in set(p["type"] for p in proposals)
        } if proposals else {},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-coverage", type=int, default=5,
                    help="Min pages per (criterion, business) segment to consider")
    args = ap.parse_args()
    result = run(min_pages=args.min_coverage)
    print(json.dumps(result, indent=2, ensure_ascii=False))
