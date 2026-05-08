#!/usr/bin/env python3
"""V21.F.3 — Golden Calibration Loop

Vérifie que les sites de référence (golden Pantheon) atteignent leur cible
de score (>= 70%). Si pas, identifie les écarts par critère / par bloc /
par site pour driver V21.E (recalibration scoring).

Logique :
  - Cible : goldens doivent scorer >= 70% sur leur business_type natif
  - Pour chaque golden, charger:
      - score_page_type.aggregate.score100 (global page)
      - score_<pillar>.score100 (par bloc)
      - per-criterion scores
  - Compute deltas vs cible 70/100
  - Output un rapport actionable pour la recalibration

Usage :
  python3 golden_calibration_check.py
  python3 golden_calibration_check.py --target 70
  python3 golden_calibration_check.py --output data/golden/_calibration_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "captures"
GOLDEN_REGISTRY = ROOT / "data" / "golden" / "_golden_registry.json"


def load_goldens() -> list[dict]:
    if not GOLDEN_REGISTRY.exists():
        return []
    return json.load(open(GOLDEN_REGISTRY)).get("sites", [])


PILLAR_FILES = {
    "hero": "score_hero.json",
    "persuasion": "score_persuasion.json",
    "ux": "score_ux.json",
    "coherence": "score_coherence.json",
    "psycho": "score_psycho.json",
    "tech": "score_tech.json",
}


def load_page_scores(client: str, page: str) -> dict:
    """Return all score signals for a page."""
    page_dir = DATA_DIR / client / page
    out = {
        "client": client,
        "page": page,
        "exists": page_dir.exists(),
        "global_score": None,
        "bt_weighted_score": None,
        "pillars": {},
        "criteria": {},
    }
    if not page_dir.exists():
        return out

    # Global score from score_page_type.aggregate.score100
    spt = page_dir / "score_page_type.json"
    if spt.exists():
        try:
            d = json.load(open(spt))
            agg = d.get("aggregate", {}) or {}
            out["global_score"] = agg.get("score100")
            out["bt_weighted_score"] = agg.get("bt_weighted_score100")
        except Exception:
            pass

    # Pillar scores + per-criterion
    for pillar, fname in PILLAR_FILES.items():
        f = page_dir / fname
        if not f.exists():
            continue
        try:
            d = json.load(open(f))
            out["pillars"][pillar] = {
                "score100": d.get("score100"),
                "killer_triggered": d.get("killerTriggered"),
                "raw_total": d.get("rawTotal"),
                "raw_max": d.get("max") or d.get("maxFull"),
            }
            for c in d.get("criteria", []) or d.get("criterions", []):
                cid = c.get("id") or c.get("criterion_id")
                if not cid:
                    continue
                if not c.get("applicable", True):
                    continue
                score = c.get("score")
                max_score = c.get("max")
                pct = None
                if score is not None and max_score:
                    try:
                        pct = round(100 * float(score) / float(max_score), 1)
                    except Exception:
                        pct = None
                out["criteria"][cid] = {
                    "score_pct": pct,
                    "raw_score": score,
                    "max": max_score,
                    "label": c.get("label"),
                    "verdict": c.get("verdict"),
                    "pillar": pillar,
                }
        except Exception:
            pass

    return out


def build_calibration_report(target: float = 70.0) -> dict:
    goldens = load_goldens()
    if not goldens:
        return {"error": "No goldens registry"}

    per_site = []
    per_criterion: dict[str, list[float]] = defaultdict(list)
    per_pillar: dict[str, list[float]] = defaultdict(list)
    per_category: dict[str, list[float]] = defaultdict(list)
    fleet_global_scores = []

    for site in goldens:
        label = site["label"]
        category = site.get("category") or site.get("biz")
        pages_def = site.get("pages") or {}

        site_pages = []
        for page_name in pages_def:
            if page_name == "label":
                continue
            scores = load_page_scores(label, page_name)
            if scores["exists"] and scores["global_score"] is not None:
                site_pages.append(scores)
                fleet_global_scores.append(scores["global_score"])
                if category:
                    per_category[category].append(scores["global_score"])

                # Aggregate per criterion + per pillar
                for pillar, p_data in scores["pillars"].items():
                    if p_data.get("score100") is not None:
                        per_pillar[pillar].append(p_data["score100"])

                for cid, c_data in scores["criteria"].items():
                    if c_data.get("score_pct") is not None:
                        per_criterion[cid].append(c_data["score_pct"])

        if not site_pages:
            per_site.append({
                "label": label,
                "category": category,
                "n_pages": 0,
                "avg_score": None,
                "status": "NO_DATA",
            })
            continue

        scores = [p["global_score"] for p in site_pages if p["global_score"] is not None]
        avg = mean(scores) if scores else None
        weakest_pages = sorted(site_pages, key=lambda p: p["global_score"])[:2]
        per_site.append({
            "label": label,
            "category": category,
            "n_pages": len(site_pages),
            "avg_score": round(avg, 1) if avg else None,
            "min_score": round(min(scores), 1) if scores else None,
            "max_score": round(max(scores), 1) if scores else None,
            "status": "PASS" if avg and avg >= target else ("FAIL_HARD" if avg and avg < 50 else "FAIL_MEDIUM"),
            "weakest_pages": [
                {"page": p["page"], "score": round(p["global_score"], 1)}
                for p in weakest_pages
            ],
            "weakest_pillars": _weakest_pillars(site_pages),
        })

    # Build per-criterion calibration directives
    criterion_calibration = []
    for cid, scores in per_criterion.items():
        if not scores:
            continue
        avg = mean(scores)
        gap = avg - target
        action = _calibration_action(avg, target, len(scores))
        criterion_calibration.append({
            "criterion_id": cid,
            "n_observations": len(scores),
            "golden_avg": round(avg, 1),
            "golden_min": round(min(scores), 1),
            "golden_max": round(max(scores), 1),
            "golden_stddev": round(stdev(scores), 1) if len(scores) > 1 else 0,
            "gap_to_target": round(gap, 1),
            "calibration_action": action,
        })
    criterion_calibration.sort(key=lambda x: x["gap_to_target"])

    # Build per-pillar calibration
    pillar_calibration = {}
    for pillar, scores in per_pillar.items():
        if scores:
            avg = mean(scores)
            pillar_calibration[pillar] = {
                "n_observations": len(scores),
                "golden_avg": round(avg, 1),
                "gap_to_target": round(avg - target, 1),
                "calibration_action": _calibration_action(avg, target, len(scores)),
            }

    # Fleet summary
    n_above = sum(1 for s in per_site if s.get("avg_score") and s["avg_score"] >= target)
    n_below = sum(1 for s in per_site if s.get("avg_score") and s["avg_score"] < target)

    # Per-category summary
    category_summary = {}
    for cat, scores in per_category.items():
        if scores:
            avg = mean(scores)
            category_summary[cat] = {
                "n_pages": len(scores),
                "golden_avg": round(avg, 1),
                "gap_to_target": round(avg - target, 1),
            }

    return {
        "version": "V21.F.3",
        "target_score": target,
        "generated_at": _now_iso(),
        "fleet_summary": {
            "total_goldens": len(per_site),
            "goldens_above_target": n_above,
            "goldens_below_target": n_below,
            "goldens_no_data": len([s for s in per_site if s["status"] == "NO_DATA"]),
            "fleet_avg_score": round(mean(fleet_global_scores), 1) if fleet_global_scores else None,
            "fleet_min_score": round(min(fleet_global_scores), 1) if fleet_global_scores else None,
            "fleet_max_score": round(max(fleet_global_scores), 1) if fleet_global_scores else None,
        },
        "category_summary": category_summary,
        "pillar_calibration": pillar_calibration,
        "criterion_calibration": criterion_calibration[:30],  # top 30 worst gap
        "criterion_calibration_full": criterion_calibration,
        "per_site": sorted(per_site, key=lambda s: (s.get("avg_score") or 999)),
    }


def _calibration_action(avg: float, target: float, n: int) -> str:
    if avg >= target:
        return "OK_NO_ACTION"
    gap = target - avg
    if gap > 30:
        return "URGENT — large gap, revoir les rules de scoring du critère (probable floor trop haut ou overlay trop strict)"
    elif gap > 15:
        return "RECALIBRATE — adjuster floors/ceilings ou pondération overlay"
    elif gap > 5:
        return "TUNE — petit ajustement de scoring rules"
    else:
        return "CLOSE — proche cible, surveille"


def _weakest_pillars(site_pages: list[dict]) -> list[dict]:
    """Trouve les pillars les plus faibles à travers les pages d'un site."""
    pillar_scores: dict[str, list[float]] = defaultdict(list)
    for p in site_pages:
        for pillar, pdata in p["pillars"].items():
            if pdata.get("score100") is not None:
                pillar_scores[pillar].append(pdata["score100"])
    out = []
    for pillar, scores in pillar_scores.items():
        if scores:
            out.append({"pillar": pillar, "avg": round(mean(scores), 1)})
    return sorted(out, key=lambda x: x["avg"])[:3]


def _now_iso() -> str:
    from datetime import datetime, UTC
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=float, default=70.0, help="Cible de score (default 70)")
    parser.add_argument("--output", default="data/golden/_calibration_report.json")
    parser.add_argument("--print", action="store_true", help="Print summary to stdout")
    args = parser.parse_args()

    report = build_calibration_report(target=args.target)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✓ Report → {out_path}")

    if args.print or True:  # always print summary
        s = report["fleet_summary"]
        print(f"\n═══ Fleet Summary (target={args.target}) ═══")
        print(f"  Total goldens : {s['total_goldens']}")
        print(f"  ≥ target      : {s['goldens_above_target']}")
        print(f"  < target      : {s['goldens_below_target']}")
        print(f"  No data       : {s['goldens_no_data']}")
        print(f"  Fleet avg     : {s['fleet_avg_score']}%")
        print(f"  Range         : {s['fleet_min_score']}% – {s['fleet_max_score']}%")

        print(f"\n═══ Pillar Calibration ═══")
        for pillar, p in report["pillar_calibration"].items():
            print(f"  {pillar:12s} avg={p['golden_avg']:5.1f}%  gap={p['gap_to_target']:+6.1f}  → {p['calibration_action']}")

        print(f"\n═══ TOP 15 critères les plus en écart (priorité recalibration) ═══")
        for c in report["criterion_calibration"][:15]:
            print(f"  {c['criterion_id']:12s} avg={c['golden_avg']:5.1f}%  gap={c['gap_to_target']:+6.1f}  n={c['n_observations']}  → {c['calibration_action']}")

        print(f"\n═══ TOP 5 goldens les plus faibles ═══")
        for site in report["per_site"][:5]:
            if site.get("avg_score"):
                weakest = ", ".join(f"{p['pillar']}({p['avg']}%)" for p in site.get("weakest_pillars", [])[:3])
                print(f"  {site['label']:25s} avg={site['avg_score']:5.1f}%  weakest: {weakest}")


if __name__ == "__main__":
    main()
