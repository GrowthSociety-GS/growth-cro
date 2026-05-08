#!/usr/bin/env python3
"""
score_site.py — Agrégateur multi-pages GrowthCRO.

Lit la synthèse page-type quand elle existe (score_page_type.json), puis fallback
sur les anciens scores individuels par page (score_hero.json, score_persuasion.json,
etc.) et produit un score global site en moyenne pondérée.

Usage :
    python score_site.py <client_id> [business_category]

Reads :  data/captures/<client_id>/pages_discovered.json
         data/captures/<client_id>/<pageType>/score_page_type.json
         data/captures/<client_id>/<pageType>/score_*.json
Writes : data/captures/<client_id>/site_audit.json

Pondération :
    - home (primary) : ×1.3
    - pages mandatory : ×1.0
    - pages optional :  ×0.7
    - page obligatoire manquante : -3 pts (max -9)
"""

import json
import sys
import pathlib
from datetime import datetime, timezone

if len(sys.argv) < 2:
    print("Usage: score_site.py <client_id> [business_category]", file=sys.stderr)
    sys.exit(1)

CLIENT_ID = sys.argv[1]
BIZ_CAT = sys.argv[2] if len(sys.argv) > 2 else "unknown"

ROOT = pathlib.Path(__file__).resolve().parents[3]
CLIENT_DIR = ROOT / "data" / "captures" / CLIENT_ID
DISCOVER_FILE = CLIENT_DIR / "pages_discovered.json"

# ---------------------------------------------------------------------------
# TIER WEIGHTS
# ---------------------------------------------------------------------------
TIER_WEIGHTS = {
    "primary": 1.3,
    "mandatory": 1.0,
    "optional": 0.7,
}
MISSING_MANDATORY_PENALTY = 3  # pts /100 per missing mandatory page
MAX_PENALTY = 9

# Tout est ramené sur /100
SCORE_BASE = 100
SITE_SCORE_VERSION = "v26ah-page-type-aggregate"
SCORE_SOURCE_PRIORITY = ["score_page_type.json", "score_*.json legacy fallback"]

# All scorer files we know about (add more as blocs get locked)
SCORER_FILES = {
    "hero":       "score_hero.json",
    "persuasion": "score_persuasion.json",
    "ux":         "score_ux.json",
    "coherence":  "score_coherence.json",
    "psycho":     "score_psycho.json",
    "tech":       "score_tech.json",
}

PILLAR_MAX = {
    "hero": 18,
    "persuasion": 24,
    "ux": 24,
    "coherence": 18,
    "psycho": 18,
    "tech": 15,
}


def read_page_scores(page_dir: pathlib.Path) -> dict:
    """Read all available legacy pillar scorer outputs for a page directory."""
    scores = {}
    for pillar, fname in SCORER_FILES.items():
        fpath = page_dir / fname
        if fpath.exists():
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                # Prefer score100 if available (V2 scorers)
                score100 = data.get("score100")
                if score100 is not None:
                    scores[pillar] = {
                        "score100": float(score100),
                        "score": float(data.get("finalRounded") or data.get("finalTotal") or data.get("rawTotal") or 0),
                        "max": data.get("max") or data.get("finalMax") or PILLAR_MAX.get(pillar, 0),
                        "killerTriggered": data.get("killerTriggered", False) or bool(data.get("capsApplied")),
                    }
                else:
                    # Legacy V1 scorers — calculate score100 from score/max
                    final = (
                        data.get("finalRounded")
                        or data.get("finalCapped")
                        or data.get("finalTotal")
                        or data.get("rawTotal")
                        or 0
                    )
                    pmax = data.get("max") or data.get("finalMax") or PILLAR_MAX.get(pillar, 0)
                    s100 = round((float(final) / pmax) * 100, 1) if pmax > 0 else 0
                    scores[pillar] = {
                        "score100": s100,
                        "score": float(final),
                        "max": pmax,
                        "killerTriggered": data.get("killerTriggered", False) or bool(data.get("capsApplied")),
                    }
            except Exception as e:
                print(f"  [WARN] Error reading {fpath}: {e}")
    return scores


def _safe_float(value, default=0.0) -> float:
    """Coerce numeric JSON values without letting one bad field kill the site score."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pillar_scores_from_page_type(score_page: dict) -> dict:
    by_pillar = ((score_page.get("universal") or {}).get("byPillar") or {})
    pillar_scores = {}
    for pillar, pdata in by_pillar.items():
        pillar_scores[pillar] = {
            "score100": round(_safe_float(pdata.get("score100")), 1),
            "score": round(_safe_float(pdata.get("rawTotal")), 1),
            "max": _safe_float(pdata.get("rawMax")),
            "killerTriggered": False,
            "source": "score_page_type.universal.byPillar",
        }
    return pillar_scores


def read_page_type_score(page_dir: pathlib.Path) -> dict | None:
    """Read the modern page-type aggregate score if present.

    score_page_type.py already applies page-type applicability, semantic lifts,
    specific criteria and normalized maxes. Site aggregation must therefore use
    this file as the source of truth instead of recomputing a partial legacy max.
    """
    fpath = page_dir / "score_page_type.json"
    if not fpath.exists():
        return None

    try:
        data = _read_json(fpath)
    except Exception as e:
        print(f"  [WARN] Error reading {fpath}: {e}")
        return None

    aggregate = data.get("aggregate") or {}
    max_per_page_type = data.get("maxPerPageType") or {}
    raw_total = _safe_float(aggregate.get("rawTotal"))
    raw_max = _safe_float(aggregate.get("rawMax") or max_per_page_type.get("rawMax"))
    score100 = _safe_float(aggregate.get("score100"))

    if raw_max <= 0:
        print(f"  [WARN] Invalid score_page_type rawMax for {page_dir.name}")
        return None

    return {
        "scoreSource": "score_page_type",
        "doctrineVersion": data.get("doctrineVersion"),
        "generatedAt": data.get("generatedAt"),
        "pageType": data.get("pageType") or page_dir.name,
        "pillarScores": _pillar_scores_from_page_type(data),
        "pageScoreRaw": round(raw_total, 1),
        "pageMaxRaw": round(raw_max, 1),
        "pageScore100": round(score100, 1),
        "expectedRawMax": aggregate.get("expectedRawMax"),
        "deltaVsExpected": aggregate.get("delta_vs_expected"),
        "maxPerPageType": max_per_page_type,
        "specific": data.get("specific"),
        "funnel": data.get("funnel"),
        "note": "Scored from score_page_type aggregate (universal + specific + applicability)",
    }


def read_legacy_page_score(page_dir: pathlib.Path) -> dict | None:
    """Fallback for old captures that have pillar files but no page-type aggregate."""
    pillar_scores = read_page_scores(page_dir)
    if not pillar_scores:
        return None

    page_total = sum(s["score"] for s in pillar_scores.values())
    page_max = sum(s["max"] for s in pillar_scores.values())
    page_score_100 = round((page_total / page_max) * SCORE_BASE, 1) if page_max > 0 else 0

    return {
        "scoreSource": "legacy_pillars",
        "pillarScores": pillar_scores,
        "pageScoreRaw": round(page_total, 1),
        "pageMaxRaw": page_max,
        "pageScore100": page_score_100,
        "note": f"Legacy fallback — scored {len(pillar_scores)}/{len(PILLAR_MAX)} pillars available",
    }


def read_page_score(page_dir: pathlib.Path) -> dict | None:
    return read_page_type_score(page_dir) or read_legacy_page_score(page_dir)


def main():
    print(f"\n{'='*60}")
    print(f"SCORE SITE — {CLIENT_ID}")
    print(f"{'='*60}\n")

    # Load pages_discovered.json
    if DISCOVER_FILE.exists():
        discover = json.loads(DISCOVER_FILE.read_text(encoding="utf-8"))
        selected_pages = discover.get("selectedPages", [])
        missing_mandatory = discover.get("missingMandatoryPages", [])
    else:
        # Fallback: just look for subdirs with capture.json
        print("[INFO] No pages_discovered.json — scanning subdirectories...")
        selected_pages = []
        missing_mandatory = []
        for subdir in sorted(CLIENT_DIR.iterdir()):
            if subdir.is_dir() and (subdir / "capture.json").exists():
                page_type = subdir.name
                tier = "primary" if page_type == "home" else "optional"
                selected_pages.append({
                    "pageType": page_type,
                    "url": "",
                    "tier": tier,
                })

    if not selected_pages:
        print("[ERR] No pages to aggregate", file=sys.stderr)
        sys.exit(1)

    # Score each page
    page_results = []
    for page_info in selected_pages:
        page_type = page_info["pageType"]
        page_dir = CLIENT_DIR / page_type

        if not page_dir.exists() or not (page_dir / "capture.json").exists():
            print(f"  [SKIP] {page_type} — no capture found")
            continue

        page_score = read_page_score(page_dir)
        if not page_score:
            print(f"  [SKIP] {page_type} — no scorer outputs found")
            continue

        pillar_scores = page_score.get("pillarScores", {})
        page_total = _safe_float(page_score.get("pageScoreRaw"))
        page_max = _safe_float(page_score.get("pageMaxRaw"))
        page_score_100 = _safe_float(page_score.get("pageScore100"))

        tier = page_info.get("tier", "optional")
        weight = TIER_WEIGHTS.get(tier, 0.7)

        result = {
            "pageType": page_type,
            "url": page_info.get("url", ""),
            "tier": tier,
            "weight": weight,
            "scoreSource": page_score.get("scoreSource"),
            "doctrineVersion": page_score.get("doctrineVersion"),
            "scoreGeneratedAt": page_score.get("generatedAt"),
            "pillarScores": pillar_scores,
            "pageScoreRaw": page_total,
            "pageMaxRaw": page_max,
            "pageScore100": round(page_score_100, 1),
            "expectedRawMax": page_score.get("expectedRawMax"),
            "deltaVsExpected": page_score.get("deltaVsExpected"),
            "maxPerPageType": page_score.get("maxPerPageType"),
            "specific": page_score.get("specific"),
            "funnel": page_score.get("funnel"),
            "note": page_score.get("note"),
        }
        page_results.append(result)

        tier_icon = {"primary": "★", "mandatory": "●", "optional": "○"}.get(tier, "?")
        source = result["scoreSource"]
        print(f"  {tier_icon} [{page_type:12}] {page_score_100:.1f}/100 (brut {page_total:.1f}/{page_max}, ×{weight}) — {source}")
        for pname, pdata in pillar_scores.items():
            killer = " ⚠️KILLER" if pdata.get("killerTriggered") else ""
            print(f"      {pname:12} {pdata['score']:.1f}/{pdata['max']}{killer}")

    if not page_results:
        print("[ERR] No pages could be scored", file=sys.stderr)
        sys.exit(1)

    # Aggregate: weighted average of scores /100
    weighted_sum = 0
    weight_total = 0
    for pr in page_results:
        weighted_sum += pr["pageScore100"] * pr["weight"]
        weight_total += SCORE_BASE * pr["weight"]

    if weight_total > 0:
        site_score_raw = (weighted_sum / weight_total) * SCORE_BASE
    else:
        site_score_raw = 0

    # Apply missing mandatory penalty
    penalty = min(len(missing_mandatory) * MISSING_MANDATORY_PENALTY, MAX_PENALTY)
    site_score_final = max(0, round(site_score_raw - penalty, 1))

    # Verdict
    if site_score_final >= 80:
        verdict = "TOP"
    elif site_score_final >= 60:
        verdict = "SOLIDE"
    elif site_score_final >= 40:
        verdict = "MOYEN"
    else:
        verdict = "FAIBLE"

    print(f"\n{'='*60}")
    print(f"SCORE GLOBAL SITE : {site_score_final}/100 ({verdict})")
    if penalty > 0:
        print(f"  (avant malus: {round(site_score_raw, 1)}/100, malus pages manquantes: -{penalty})")
    if missing_mandatory:
        print(f"  ⚠️  Pages obligatoires manquantes : {', '.join(missing_mandatory)}")
    print(f"  Pages scorées : {len(page_results)}")
    print(f"  Source priorité : {' > '.join(SCORE_SOURCE_PRIORITY)}")
    print(f"{'='*60}\n")

    doctrine_versions = sorted({
        pr["doctrineVersion"]
        for pr in page_results
        if pr.get("doctrineVersion")
    })

    # Build output
    output = {
        "clientId": CLIENT_ID,
        "businessCategory": BIZ_CAT,
        "auditedAt": datetime.now(timezone.utc).isoformat(),
        "gridVersion": SITE_SCORE_VERSION,
        "doctrineVersions": doctrine_versions,
        "scoreSourcePriority": SCORE_SOURCE_PRIORITY,
        "activePillars": list(SCORER_FILES.keys()),
        "totalPillars": len(PILLAR_MAX),
        "pagesAudited": page_results,
        "missingMandatoryPages": missing_mandatory,
        "siteScore": {
            "raw": round(site_score_raw, 1),
            "penalty": penalty,
            "final": site_score_final,
            "max": SCORE_BASE,
            "formula": "Σ(page_score_100 × page_weight) / Σ(100 × page_weight) × 100 - missing_penalty",
        },
        "verdict": verdict,
        "verdictThresholds": {
            "TOP": ">= 80/100",
            "SOLIDE": ">= 60/100",
            "MOYEN": ">= 40/100",
            "FAIBLE": "< 40/100",
        },
        "note": "Score site V26.AH — uses score_page_type.json when available, legacy pillar files only as fallback."
    }

    out_path = CLIENT_DIR / "site_audit.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[SAVED] {out_path}")


if __name__ == "__main__":
    main()
