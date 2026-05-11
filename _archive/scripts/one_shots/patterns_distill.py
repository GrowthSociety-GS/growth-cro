#!/usr/bin/env python3
"""
patterns_distill.py — V14.2 distillation infrastructure.

Tasks:
  prepare   → load corpus_5d.json, generate worksheets per bucket, ranked by priority
  merge     → merge a batch of newly distilled patterns into patterns.json (atomic)
  status    → show progress (buckets done/remaining, coverage per pillar)

Usage:
  python3 scripts/patterns_distill.py prepare
  python3 scripts/patterns_distill.py merge outputs_distill/batches/batch_001.json
  python3 scripts/patterns_distill.py status

Doctrine:
  - Each bucket distilled ONCE into one pattern (by Opus in-conversation)
  - Write-per-batch atomic (tmp + rename)
  - Progress tracked in patterns_progress.json
"""
import json, pathlib, sys, time, hashlib, math, collections
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "outputs_distill" / "corpus_5d.json"
PATTERNS = ROOT / "skills" / "cro-library" / "references" / "patterns.json"
PROGRESS = ROOT / "skills" / "cro-library" / "references" / "patterns_progress.json"
WORKSHEETS_DIR = ROOT / "outputs_distill" / "worksheets"
BATCHES_DIR = ROOT / "outputs_distill" / "batches"


def _atomic_write(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(path)


def _load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text())
    return {"version": "14.2.0", "buckets_done": {}, "batches_done": [], "last_update": None}


def _save_progress(prog: dict) -> None:
    prog["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _atomic_write(PROGRESS, prog)


def _bucket_priority(bucket_key: str, n_seeds: int) -> int:
    """Priority score: more seeds + critical score_band + home page = higher prio."""
    parts = bucket_key.split("|")
    if len(parts) != 5:
        return 0
    _, intent, page_type, biz, score_band = parts
    p = n_seeds * 100
    if score_band == "critical": p += 40
    elif score_band == "weak": p += 20
    if page_type == "home": p += 15
    if intent in ("purchase", "signup_commit"): p += 10
    if biz in ("ecommerce", "saas"): p += 5
    return p


def cmd_prepare():
    """Generate worksheets per bucket + ranked batch plan."""
    corpus = json.loads(CORPUS.read_text())["buckets"]
    WORKSHEETS_DIR.mkdir(parents=True, exist_ok=True)
    prog = _load_progress()

    ranked = []
    for key, seeds in corpus.items():
        if len(seeds) < 3:
            continue  # focus on validated first
        priority = _bucket_priority(key, len(seeds))
        ranked.append((priority, key, len(seeds)))
    ranked.sort(reverse=True)

    # Write worksheet per bucket
    n_new = 0
    for priority, key, n in ranked:
        worksheet_name = key.replace("|", "__") + ".json"
        ws_path = WORKSHEETS_DIR / worksheet_name
        if ws_path.exists():
            continue
        seeds = corpus[key]
        # Keep top-8 by ice_score
        seeds_sorted = sorted(seeds, key=lambda s: -(s.get("ice") or 0))[:8]
        parts = key.split("|")
        ws = {
            "bucket_key": key,
            "priority_score": priority,
            "context": {
                "criterion_id": parts[0],
                "intent": parts[1],
                "page_type": parts[2],
                "business_category": parts[3],
                "score_band": parts[4],
            },
            "seed_count_total": len(seeds),
            "seed_count_kept": len(seeds_sorted),
            "seeds": seeds_sorted,
            "stats": {
                "mean_ice": round(sum(s.get("ice", 0) for s in seeds) / len(seeds), 1),
                "mean_lift_pct": round(sum(s.get("lift", 0) or 0 for s in seeds) / len(seeds), 1),
                "mean_effort_hours": round(sum(s.get("effort", 0) or 0 for s in seeds) / len(seeds), 1),
                "dominant_priority": collections.Counter(s.get("pri") for s in seeds).most_common(1)[0][0],
            },
        }
        _atomic_write(ws_path, ws)
        n_new += 1

    # Write batch plan
    plan_path = ROOT / "outputs_distill" / "batch_plan.json"
    plan = {
        "total_validated_buckets": len(ranked),
        "already_distilled": len(prog.get("buckets_done", {})),
        "remaining": len(ranked) - len(prog.get("buckets_done", {})),
        "batches_of_30_needed": math.ceil((len(ranked) - len(prog.get("buckets_done", {}))) / 30),
        "next_batch_keys": [
            {"rank": i + 1, "priority": p, "key": k, "n_seeds": n}
            for i, (p, k, n) in enumerate(ranked)
            if k not in prog.get("buckets_done", {})
        ][:30],
    }
    _atomic_write(plan_path, plan)

    print(f"[prepare] Worksheets generated: {n_new} new, {len(ranked)} total validated buckets")
    print(f"[prepare] Already distilled: {plan['already_distilled']}")
    print(f"[prepare] Remaining: {plan['remaining']}")
    print(f"[prepare] Batches of 30 needed: {plan['batches_of_30_needed']}")
    print(f"[prepare] Next batch plan: {plan_path}")


def cmd_merge(batch_file: str):
    """Merge a distilled batch JSON (list of patterns) into patterns.json atomically."""
    batch_path = pathlib.Path(batch_file)
    if not batch_path.is_absolute():
        batch_path = ROOT / batch_file
    if not batch_path.exists():
        print(f"[merge] ERROR: batch file not found: {batch_path}")
        sys.exit(1)

    batch = json.loads(batch_path.read_text())
    new_patterns = batch.get("patterns", batch) if isinstance(batch, dict) else batch
    if not isinstance(new_patterns, list):
        print("[merge] ERROR: expected list of patterns or {patterns:[...]}")
        sys.exit(1)

    # Load existing patterns.json
    if PATTERNS.exists():
        existing = json.loads(PATTERNS.read_text())
    else:
        existing = {"_meta": {}, "patterns": []}

    existing_ids = {p["pattern_id"] for p in existing.get("patterns", [])}
    added, updated = 0, 0
    for p in new_patterns:
        pid = p.get("pattern_id")
        if not pid:
            continue
        if pid in existing_ids:
            for i, ep in enumerate(existing["patterns"]):
                if ep["pattern_id"] == pid:
                    existing["patterns"][i] = p
                    updated += 1
                    break
        else:
            existing["patterns"].append(p)
            existing_ids.add(pid)
            added += 1

    # Refresh meta
    existing["_meta"]["version"] = "14.2.0"
    existing["_meta"]["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stats = collections.Counter(p.get("status", "draft") for p in existing["patterns"])
    existing["_meta"]["stats"] = {
        "patterns_total": len(existing["patterns"]),
        "patterns_validated": stats["validated"],
        "patterns_draft": stats["draft"],
        "patterns_orphan": stats["orphan"],
    }
    _atomic_write(PATTERNS, existing)

    # Update progress
    prog = _load_progress()
    for p in new_patterns:
        bucket_key = "__".join([
            p.get("context", {}).get("criterion_id", ""),
            p.get("context", {}).get("intent", ""),
            p.get("context", {}).get("page_type", ""),
            p.get("context", {}).get("business_category", ""),
            p.get("context", {}).get("score_band", ""),
        ]).replace("__", "|", 4)  # pipe separator for corpus_5d compatibility
        prog["buckets_done"][bucket_key] = {
            "pattern_id": p.get("pattern_id"),
            "distilled_at": p.get("created_at", existing["_meta"]["last_update"]),
        }
    prog["batches_done"].append(batch_path.name)
    _save_progress(prog)

    print(f"[merge] Added {added} new patterns, updated {updated} existing")
    print(f"[merge] patterns.json now has {len(existing['patterns'])} patterns total")


def cmd_status():
    """Show distillation progress."""
    prog = _load_progress()
    corpus = json.loads(CORPUS.read_text())["buckets"]

    n_validated = sum(1 for k, v in corpus.items() if len(v) >= 3)
    n_draft = sum(1 for k, v in corpus.items() if len(v) == 2)
    n_orphan = sum(1 for k, v in corpus.items() if len(v) == 1)
    n_done = len(prog.get("buckets_done", {}))

    if PATTERNS.exists():
        p_data = json.loads(PATTERNS.read_text())
        n_patterns = len(p_data.get("patterns", []))
        stats = p_data.get("_meta", {}).get("stats", {})
    else:
        n_patterns, stats = 0, {}

    print(f"=== V14.2 patterns.json distillation status ===")
    print(f"Corpus buckets      : {len(corpus)} total")
    print(f"  validated (≥3)    : {n_validated}")
    print(f"  draft (=2)        : {n_draft}")
    print(f"  orphan (=1)       : {n_orphan}")
    print()
    print(f"Buckets distilled   : {n_done} ({100*n_done/max(n_validated,1):.1f}% of validated)")
    print(f"patterns.json count : {n_patterns}")
    print(f"  validated status  : {stats.get('patterns_validated', 0)}")
    print(f"  draft status      : {stats.get('patterns_draft', 0)}")
    print(f"  orphan status     : {stats.get('patterns_orphan', 0)}")
    print(f"Batches merged      : {len(prog.get('batches_done', []))}")
    print(f"Last update         : {prog.get('last_update')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "prepare":
        cmd_prepare()
    elif cmd == "merge":
        if len(sys.argv) < 3:
            print("Usage: patterns_distill.py merge <batch_file>")
            sys.exit(1)
        cmd_merge(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
