#!/usr/bin/env python3
"""
patterns_schema_harmonize.py — V14.2 schema harmonization pass 1.
Normalizes all patterns in patterns.json to canonical Format A:

  expected_lift_pct = {low, high, mean, basis, confidence?}
  seed_variance    = {jaccard, cosine_tfidf, mean, computed_inline, note?}

- Heroes (8): rename expected_lift -> expected_lift_pct (low_pct/high_pct/
  mean_across_seeds_pct -> low/high/mean), rename variance fields.
- Ux/psy (5): expand scalar lift using seed_instances min/max/avg when
  available, else leave low/high null; expand scalar variance to dict with
  mean only and computed_inline=false + note.
- Coh/per (17): untouched (already Format A).

Bumps version 1.0.0 -> 1.0.2 on modified patterns, bumps _meta.version to
14.2.1. Writes to tmp then atomic rename.
"""
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PATTERNS = ROOT / "skills" / "cro-library" / "references" / "patterns.json"


def harmonize_hero(pat):
    """8 heroes: rename expected_lift and seed_variance field names."""
    changed = False

    old_lift = pat.get("expected_lift")
    if isinstance(old_lift, dict) and "expected_lift_pct" not in pat:
        new_lift = {
            "low": old_lift.get("low_pct"),
            "high": old_lift.get("high_pct"),
            "mean": old_lift.get("mean_across_seeds_pct"),
            "basis": old_lift.get("basis"),
        }
        if "confidence" in old_lift:
            new_lift["confidence"] = old_lift["confidence"]
        pat["expected_lift_pct"] = new_lift
        del pat["expected_lift"]
        changed = True

    old_var = pat.get("seed_variance")
    if isinstance(old_var, dict) and "jaccard_est" in old_var:
        new_var = {
            "jaccard": old_var.get("jaccard_est"),
            "cosine_tfidf": old_var.get("cosine_tfidf_est"),
            "mean": old_var.get("combined_est"),
            "computed_inline": True,
        }
        if "note" in old_var:
            new_var["note"] = old_var["note"]
        pat["seed_variance"] = new_var
        changed = True

    return pat, changed


def harmonize_scalar(pat):
    """5 ux/psy: expand scalar expected_lift_pct and seed_variance to dicts."""
    changed = False

    lift = pat.get("expected_lift_pct")
    if isinstance(lift, (int, float)):
        # derive from seed_instances if possible
        seeds = pat.get("seed_instances", [])
        lift_values = [s.get("lift") for s in seeds if isinstance(s.get("lift"), (int, float))]
        if lift_values and len(lift_values) >= 2:
            low = min(lift_values)
            high = max(lift_values)
            mean = round(sum(lift_values) / len(lift_values), 2)
            basis = f"n={len(lift_values)} seeds computed inline (min/max/avg)"
        else:
            low = None
            high = None
            mean = float(lift)
            basis = "batch 1 pre-harmo, fourchette non calculée"
        pat["expected_lift_pct"] = {
            "low": low,
            "high": high,
            "mean": mean,
            "basis": basis,
        }
        changed = True

    var = pat.get("seed_variance")
    if isinstance(var, (int, float)):
        pat["seed_variance"] = {
            "jaccard": None,
            "cosine_tfidf": None,
            "mean": float(var),
            "computed_inline": False,
            "note": "batch 1 pre-harmo, décomposition jaccard/cosine non calculée — à recomputer lors du gap diagnostic",
        }
        changed = True

    return pat, changed


def bump_version(v):
    """1.0.0 -> 1.0.1, 1.0.1 -> 1.0.2 etc. Conservative patch bump."""
    try:
        parts = [int(x) for x in v.split(".")]
        while len(parts) < 3:
            parts.append(0)
        parts[2] += 1
        return ".".join(str(x) for x in parts)
    except Exception:
        return v + ".harmo1"


def main(dry_run=False):
    data = json.loads(PATTERNS.read_text())
    patterns = data["patterns"]

    stats = {"hero_migrated": 0, "scalar_migrated": 0, "untouched": 0}
    diffs = []

    for pat in patterns:
        pid = pat.get("pattern_id", "?")
        pillar = pid.replace("pat_", "").split("_")[0]

        before_snapshot = {
            "expected_lift_pct": pat.get("expected_lift_pct"),
            "expected_lift": pat.get("expected_lift"),
            "seed_variance": pat.get("seed_variance"),
        }

        if pillar == "hero":
            pat, changed = harmonize_hero(pat)
            if changed:
                stats["hero_migrated"] += 1
                pat["version"] = bump_version(pat.get("version", "1.0.0"))
                diffs.append((pid, before_snapshot, {
                    "expected_lift_pct": pat.get("expected_lift_pct"),
                    "seed_variance": pat.get("seed_variance"),
                    "version": pat["version"],
                }))
        elif pillar in ("ux", "psy"):
            pat, changed = harmonize_scalar(pat)
            if changed:
                stats["scalar_migrated"] += 1
                pat["version"] = bump_version(pat.get("version", "1.0.0"))
                diffs.append((pid, before_snapshot, {
                    "expected_lift_pct": pat.get("expected_lift_pct"),
                    "seed_variance": pat.get("seed_variance"),
                    "version": pat["version"],
                }))
            else:
                stats["untouched"] += 1
        else:
            stats["untouched"] += 1

    data["_meta"]["version"] = "14.2.1"
    if "harmo_history" not in data["_meta"]:
        data["_meta"]["harmo_history"] = []
    data["_meta"]["harmo_history"].append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pass": "schema_harmonize_format_A",
        "hero_migrated": stats["hero_migrated"],
        "scalar_migrated": stats["scalar_migrated"],
        "total_patterns": len(patterns),
    })

    print(f"\n=== HARMO STATS ===")
    print(f"Hero migrated   : {stats['hero_migrated']}")
    print(f"Scalar migrated : {stats['scalar_migrated']}")
    print(f"Untouched       : {stats['untouched']}")
    print(f"Total patterns  : {len(patterns)}")

    if dry_run:
        print(f"\n=== DRY RUN — 3 sample diffs ===")
        for pid, before, after in diffs[:3]:
            print(f"\n--- {pid} ---")
            print("BEFORE:")
            print(json.dumps(before, indent=2, ensure_ascii=False))
            print("AFTER:")
            print(json.dumps(after, indent=2, ensure_ascii=False))
        return

    tmp = PATTERNS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    backup = PATTERNS.with_suffix(f".json.bak.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    shutil.copy2(PATTERNS, backup)
    tmp.replace(PATTERNS)
    print(f"\nBackup: {backup.name}")
    print(f"Written: {PATTERNS}")
    print(f"Meta version: {data['_meta']['version']}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv or "--preview" in sys.argv
    main(dry_run=dry)
