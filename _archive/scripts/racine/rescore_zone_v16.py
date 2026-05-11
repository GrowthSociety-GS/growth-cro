#!/usr/bin/env python3
"""Re-score hero_* and per_* criteria with V16 zone context. Patches score_semantic.json."""
import json, os, sys, pathlib, asyncio, glob, time

sys.path.insert(0, str(pathlib.Path(__file__).parent / "skills" / "site-capture" / "scripts"))
from semantic_scorer import _build_prompt, _call_haiku, SEMANTIC_CRITERIA
from anthropic import AsyncAnthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not set"); sys.exit(1)

client = AsyncAnthropic(api_key=API_KEY)
MODEL = "claude-haiku-4-5-20251001"
MAX_CONCURRENT = 8

# Only re-score criteria that benefit from zone context
ZONE_CRITERIA = [c for c in SEMANTIC_CRITERIA if c.startswith("hero_") or c.startswith("per_")]
print(f"Zone criteria to re-score: {ZONE_CRITERIA}")

async def rescore_page(page_dir_str: str):
    page_dir = pathlib.Path(page_dir_str)
    cap_path = page_dir / "capture.json"
    sem_path = page_dir / "score_semantic.json"
    if not cap_path.exists() or not sem_path.exists():
        return 0

    capture = json.load(open(cap_path))
    sem = json.load(open(sem_path))
    page_type = capture.get("pageType", "home")
    btype = capture.get("businessType", "")
    bcat = capture.get("businessCategory", "")
    label = page_dir.parent.name

    changes = 0
    scores = sem.get("scores", {})

    for crit_id in ZONE_CRITERIA:
        crit_def = SEMANTIC_CRITERIA[crit_id]
        pt = crit_def["page_types"]
        if pt != "*" and page_type not in pt:
            continue

        old_score = scores.get(crit_id, {}).get("score")

        prompt = _build_prompt(crit_id, capture, page_type, btype, bcat, label, page_dir=str(page_dir))
        result = await _call_haiku(client, prompt, MODEL, crit_id)

        new_score = result.get("score")
        scores[crit_id] = result

        if old_score != new_score:
            changes += 1

    sem["scores"] = scores
    with open(sem_path, "w") as f:
        json.dump(sem, f, ensure_ascii=False, indent=2)

    return changes

async def main():
    # Collect all page dirs (captures only, not golden)
    dirs = []
    for f in sorted(glob.glob("data/captures/*/*/score_semantic.json")):
        dirs.append(os.path.dirname(f))

    print(f"Pages to re-score: {len(dirs)}")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    total_changes = 0

    async def bounded(d):
        async with sem:
            return await rescore_page(d)

    batch_size = 3  # Small batches to stay within timeout
    for i in range(0, len(dirs), batch_size):
        batch = dirs[i:i+batch_size]
        results = await asyncio.gather(*[bounded(d) for d in batch], return_exceptions=True)
        batch_changes = 0
        for r in results:
            if isinstance(r, int):
                batch_changes += r
                total_changes += r
            elif isinstance(r, Exception):
                print(f"  ERR: {r}", flush=True)
        done = min(i + batch_size, len(dirs))
        labels = [os.path.basename(os.path.dirname(d)) + "/" + os.path.basename(d) for d in batch]
        print(f"  [{done}/{len(dirs)}] {', '.join(labels)} → {batch_changes} changes", flush=True)

    print(f"\nDone. Total changes: {total_changes}")

asyncio.run(main())
