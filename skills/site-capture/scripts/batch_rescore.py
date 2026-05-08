#!/usr/bin/env python3
"""
batch_rescore.py — Re-score toutes les pages de tous les clients (avec données spatiales).

Relance les 6 scorers sur chaque page qui a un capture.json,
puis score_site.py pour chaque client.

Usage :
    python batch_rescore.py [--only label1,label2]
"""
import json, sys, os, time, pathlib, subprocess
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = pathlib.Path(__file__).resolve().parent
CAPTURES_DIR = ROOT / "data" / "captures"
DB_FILE = ROOT / "data" / "clients_database.json"

# Parse args
args = sys.argv[1:]
ONLY_LABELS = None
if "--only" in args:
    i = args.index("--only")
    ONLY_LABELS = set(args[i + 1].split(","))

SCORERS = ["score_hero.py", "score_persuasion.py", "score_ux.py", "score_coherence.py", "score_psycho.py", "score_tech.py"]
# Aggregators/specifics que l'enricher attend (score_page_type.json, score_specific.json)
EXTRA_SCORERS = ["score_specific_criteria.py", "score_page_type.py"]

# Load clients database for business type
db = json.loads(DB_FILE.read_text())
client_biz = {}
for c in db["clients"]:
    biz = c.get("identity", {}).get("businessType", "unknown")
    client_biz[c["id"]] = biz

# Find all client dirs with pages
client_dirs = []
for d in sorted(CAPTURES_DIR.iterdir()):
    if not d.is_dir():
        continue
    if any(x in d.name for x in ['.baseline', '_test', '_native', '_v2']):
        continue
    if ONLY_LABELS and d.name not in ONLY_LABELS:
        continue
    # Must have at least one page with capture.json
    pages = [p for p in d.iterdir() if p.is_dir() and (p / "capture.json").exists()]
    if pages:
        client_dirs.append((d, pages))

total_pages = sum(len(pages) for _, pages in client_dirs)
print(f"{'=' * 65}")
print(f"BATCH RE-SCORE (avec données spatiales V9)")
print(f"{'=' * 65}")
print(f"  Clients: {len(client_dirs)}")
print(f"  Pages: {total_pages}")
print(f"  Scorers: {len(SCORERS)}")
print(f"  Total scorer runs: {total_pages * len(SCORERS)}")
print(f"{'=' * 65}\n")

t_total = time.time()
results = defaultdict(lambda: {"ok": 0, "err": 0, "spatial": 0})
page_count = 0

for client_dir, pages in client_dirs:
    cid = client_dir.name
    biz = client_biz.get(cid, "unknown")
    has_spatial_total = sum(1 for p in pages if (p / "spatial_v9.json").exists())

    print(f"\n{'─' * 65}")
    print(f"  {cid} ({len(pages)} pages, {has_spatial_total} with spatial, biz={biz})")
    print(f"{'─' * 65}")

    for page_dir in pages:
        pt = page_dir.name
        page_count += 1
        has_spatial = (page_dir / "spatial_v9.json").exists()
        spatial_flag = " 📐" if has_spatial else ""

        # Run 6 scorers + aggregators (page_type + specific)
        all_ok = True
        for scorer in SCORERS + EXTRA_SCORERS:
            try:
                proc = subprocess.run(
                    [sys.executable, str(SCRIPTS / scorer), cid, pt],
                    capture_output=True, text=True, timeout=45,
                    cwd=str(SCRIPTS),
                )
                if proc.returncode != 0:
                    all_ok = False
            except Exception:
                all_ok = False

        if all_ok:
            results[cid]["ok"] += 1
            if has_spatial:
                results[cid]["spatial"] += 1
            print(f"    ✅ {pt}{spatial_flag}")
        else:
            results[cid]["err"] += 1
            print(f"    ❌ {pt}")

    # Run score_site.py
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "score_site.py"), cid, biz],
            capture_output=True, text=True, timeout=30,
            cwd=str(SCRIPTS),
        )
        if proc.returncode == 0:
            # Read site score
            sa = json.loads((client_dir / "site_audit.json").read_text())
            score = sa.get("siteScore", {}).get("final", 0)
            print(f"    📊 Site score: {score}/100")
        else:
            print(f"    ⚠️  score_site failed: {proc.stderr[:100]}")
    except Exception as e:
        print(f"    ⚠️  score_site error: {e}")

total_time = round(time.time() - t_total, 2)
total_ok = sum(r["ok"] for r in results.values())
total_err = sum(r["err"] for r in results.values())
total_spatial = sum(r["spatial"] for r in results.values())

print(f"\n{'═' * 65}")
print(f"BATCH RE-SCORE COMPLETE — {total_time}s ({total_time // 60:.0f}min)")
print(f"{'═' * 65}")
print(f"  ✅ OK:        {total_ok}/{page_count}")
print(f"  ❌ Errors:    {total_err}")
print(f"  📐 Spatial:   {total_spatial} pages enrichies")
