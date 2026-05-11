#!/usr/bin/env python3
"""Deterministic comparison V3.2.1 vs V3.3 doctrine on a per-criterion basis.

When live scoring data is unavailable on the fresh worktree, we still compare:
- For each criterion: V3.2.1 thresholds (scoring.top/ok/critical) vs V3.3 (same shape but enriched)
- V3.3 net additions: research_first flag, oco_refs count, ice_template presence
- Pillar-level cre_alignment

Then for 3 reference clients (weglot/japhy/stripe), simulate the V3.3 ICE delta:
- Load _archive/parity_baselines/weglot/.../score_*.json to get current V3.2.1 scores
- Re-compute ICE estimates with doctrine_version='3.3' (research_inputs unavailable on fresh worktree)
- Report Confidence delta (typically -2 on research_first criteria) and priority shift

Output to .claude/epics/webapp-stratosphere/updates/18/V3_3_DELTA_REPORT.md and
to stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from growthcro.recos.schema import load_doctrine, compute_ice_estimate


def diff_criterion(c_v3: dict, c_v33: dict) -> dict:
    """Return diff dict between V3.2.1 and V3.3 versions of a criterion."""
    return {
        "label_unchanged": c_v3.get("label") == c_v33.get("label"),
        "scoring_unchanged": c_v3.get("scoring") == c_v33.get("scoring"),
        "weight_unchanged": c_v3.get("weight") == c_v33.get("weight"),
        "pageTypes_unchanged": c_v3.get("pageTypes") == c_v33.get("pageTypes"),
        "v33_additions": {
            "research_first": c_v33.get("research_first"),
            "oco_refs_count": len(c_v33.get("oco_refs", [])),
            "has_ice_template": bool(c_v33.get("ice_template")),
        },
    }


def collect_doctrine_diff() -> dict:
    """Per-pillar comparison of V3.2.1 vs V3.3 doctrine."""
    d32 = load_doctrine("3.2.1")
    d33 = load_doctrine("3.3")
    out = {}
    for pillar_key, bloc33 in (d33.get("blocs") or {}).items():
        bloc32 = (d32.get("blocs") or {}).get(pillar_key)
        if not bloc32:
            continue
        cri32 = {c["id"]: c for c in bloc32.get("criteria", []) if c.get("id")}
        cri33 = {c["id"]: c for c in bloc33.get("criteria", []) if c.get("id")}
        diffs = {}
        for cid, c33 in cri33.items():
            c32 = cri32.get(cid)
            if not c32:
                continue
            diffs[cid] = diff_criterion(c32, c33)
        out[pillar_key] = {
            "v33_cre_alignment": bloc33.get("cre_alignment"),
            "criteria_count": len(cri33),
            "label_changes": sum(1 for d in diffs.values() if not d["label_unchanged"]),
            "scoring_changes": sum(1 for d in diffs.values() if not d["scoring_unchanged"]),
            "weight_changes": sum(1 for d in diffs.values() if not d["weight_unchanged"]),
            "research_first_count": sum(1 for d in diffs.values() if d["v33_additions"]["research_first"]),
            "total_oco_refs": sum(d["v33_additions"]["oco_refs_count"] for d in diffs.values()),
            "ice_templates_attached": sum(1 for d in diffs.values() if d["v33_additions"]["has_ice_template"]),
        }
    return out


def find_archived_scores(client: str) -> dict[str, Path]:
    """Find archived per-pillar score JSONs for a client (worktree fresh = data live absent)."""
    base = ROOT / "_archive" / "parity_baselines" / client
    if not base.exists():
        return {}
    # Get most recent timestamp dir
    ts_dirs = [d for d in base.iterdir() if d.is_dir()]
    if not ts_dirs:
        return {}
    latest = max(ts_dirs, key=lambda d: d.name)
    captures = latest / "data" / "captures" / client
    if not captures.exists():
        return {}
    out = {}
    for page_dir in captures.iterdir():
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        for pillar in ("hero", "persuasion", "ux", "coherence", "psycho", "tech"):
            score_path = page_dir / f"score_{pillar}.json"
            if score_path.exists():
                out[f"{page_dir.name}/{pillar}"] = score_path
    return out


def simulate_v3_3_ice_delta(client: str) -> list[dict]:
    """For each archived score, recompute ICE with V3.3 (no research_inputs available).

    Returns a list of dicts with: page_type, pillar, crit_id, current_score, max_score,
    ice_v3 (Confidence/Priority), ice_v3_3_no_research (Confidence/Priority).
    """
    scores = find_archived_scores(client)
    rows = []
    if not scores:
        return rows
    for key, path in sorted(scores.items()):
        page_type, pillar = key.split("/")
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        for crit in data.get("criteria", []):
            cid = crit.get("id") or crit.get("criterion_id")
            if not cid:
                continue
            cur = float(crit.get("score", 0))
            mx = float(crit.get("max", 3))
            killer = bool(crit.get("killer_violated"))
            ice32 = compute_ice_estimate(cid, pillar, cur, mx, False, False, killer)
            ice33 = compute_ice_estimate(
                cid, pillar, cur, mx, False, False, killer,
                doctrine_version="3.3",
                research_inputs_available=False,  # fresh worktree, no live data
                voc_verbatims_available=False,
            )
            rows.append({
                "page_type": page_type,
                "pillar": pillar,
                "crit_id": cid,
                "current_score": cur,
                "max_score": mx,
                "ice_v3_confidence": ice32["confidence_estimate"],
                "ice_v3_priority": ice32["priority_suggested"],
                "ice_v3_3_confidence": ice33["confidence_estimate"],
                "ice_v3_3_priority": ice33["priority_suggested"],
                "delta_confidence": ice33["confidence_estimate"] - ice32["confidence_estimate"],
                "priority_shifted": ice33["priority_suggested"] != ice32["priority_suggested"],
            })
    return rows


def main():
    print("=" * 70)
    print("V3.2.1 vs V3.3 Doctrine Comparison")
    print("=" * 70)
    diff = collect_doctrine_diff()
    for pillar, info in diff.items():
        print(f"\n── {pillar} ──")
        print(f"  criteria_count: {info['criteria_count']}")
        print(f"  label_changes (should be 0): {info['label_changes']}")
        print(f"  scoring_changes (should be 0): {info['scoring_changes']}")
        print(f"  weight_changes (should be 0): {info['weight_changes']}")
        print(f"  V3.3 research_first_count: {info['research_first_count']}")
        print(f"  V3.3 total_oco_refs: {info['total_oco_refs']}")
        print(f"  V3.3 ice_templates_attached: {info['ice_templates_attached']}")
        cre = info.get("v33_cre_alignment") or {}
        if cre:
            print(f"  V3.3 cre_alignment.9step_phase: {cre.get('9step_phase')}")
            print(f"  V3.3 cre_alignment.principle: {cre.get('principle','')[:80]}")

    # 3 audits simulation
    print("\n" + "=" * 70)
    print("3 Audits Simulation: V3.2.1 vs V3.3 ICE delta")
    print("=" * 70)
    for client in ("weglot", "japhy", "stripe"):
        rows = simulate_v3_3_ice_delta(client)
        if not rows:
            print(f"\n── {client} ── (no archived data available)")
            continue
        print(f"\n── {client} ── ({len(rows)} criterion-page evaluations)")
        delta_minus2 = sum(1 for r in rows if r["delta_confidence"] == -2)
        delta_zero = sum(1 for r in rows if r["delta_confidence"] == 0)
        delta_plus2 = sum(1 for r in rows if r["delta_confidence"] == 2)
        priority_shifted = sum(1 for r in rows if r["priority_shifted"])
        print(f"  Confidence delta -2 (research_first missing): {delta_minus2}")
        print(f"  Confidence delta 0 (asset-level criteria): {delta_zero}")
        print(f"  Confidence delta +2 (would apply with VOC): {delta_plus2}")
        print(f"  Priority shifted V3.2.1 → V3.3: {priority_shifted}")
        # Show sample top-3 priority shifts
        shifted = [r for r in rows if r["priority_shifted"]]
        if shifted:
            print(f"  Sample priority shifts (first 3):")
            for r in shifted[:3]:
                print(f"    {r['page_type']}/{r['crit_id']}: {r['ice_v3_priority']} → {r['ice_v3_3_priority']} (conf {r['ice_v3_confidence']}→{r['ice_v3_3_confidence']})")


if __name__ == "__main__":
    main()
