#!/usr/bin/env python3
"""
batch_enrich.py — Run reco_enricher on every client/page that has score_page_type.json.

Aggregates per-client placeholder count vs real reco count for V12 stress-test.

Usage:
    python batch_enrich.py [--only label1,label2]
"""
import json, sys, pathlib, subprocess, time
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = pathlib.Path(__file__).resolve().parent
CAPTURES = ROOT / "data" / "captures"

args = sys.argv[1:]
ONLY = None
if "--only" in args:
    ONLY = set(args[args.index("--only") + 1].split(","))

client_dirs = []
for d in sorted(CAPTURES.iterdir()):
    if not d.is_dir(): continue
    if any(x in d.name for x in ['.baseline', '_test', '_native', '_v2']): continue
    if ONLY and d.name not in ONLY: continue
    pages = [p for p in d.iterdir() if p.is_dir() and (p / "score_page_type.json").exists()]
    if pages: client_dirs.append((d, pages))

total_pages = sum(len(p) for _, p in client_dirs)
print(f"{'=' * 65}")
print(f"BATCH ENRICH — {len(client_dirs)} clients, {total_pages} pages")
print(f"{'=' * 65}\n")

t0 = time.time()
stats = defaultdict(lambda: {"total": 0, "real": 0, "placeholder": 0, "deferred": 0, "pages": 0, "errors": 0})
errors = []

for cdir, pages in client_dirs:
    cid = cdir.name
    print(f"\n── {cid} ({len(pages)} pages) ──")
    for pdir in pages:
        pt = pdir.name
        try:
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "reco_enricher.py"), cid, pt],
                capture_output=True, text=True, timeout=60, cwd=str(SCRIPTS),
            )
            if proc.returncode != 0:
                stats[cid]["errors"] += 1
                errors.append(f"{cid}/{pt}: {proc.stderr[:200]}")
                print(f"  ❌ {pt}: {proc.stderr[:120]}")
                continue
            # Read recos_enriched.json
            re_file = pdir / "recos_enriched.json"
            if not re_file.exists():
                stats[cid]["errors"] += 1
                print(f"  ⚠️  {pt}: no recos_enriched.json output")
                continue
            doc = json.loads(re_file.read_text())
            recos = doc.get("recos", [])
            total = len(recos)
            placeholder = sum(1 for r in recos if "[reco à générer" in (r.get("reco_text") or ""))
            deferred = sum(1 for r in recos if r.get("deferred", False))
            real = total - placeholder
            stats[cid]["total"] += total
            stats[cid]["real"] += real
            stats[cid]["placeholder"] += placeholder
            stats[cid]["deferred"] += deferred
            stats[cid]["pages"] += 1
            flag = "✅" if placeholder == 0 else "⚠️"
            print(f"  {flag} {pt}: {real}/{total} real ({placeholder} placeholders, {deferred} deferred)")
        except subprocess.TimeoutExpired:
            stats[cid]["errors"] += 1
            errors.append(f"{cid}/{pt}: timeout")
            print(f"  ⏱  {pt}: timeout")
        except Exception as e:
            stats[cid]["errors"] += 1
            errors.append(f"{cid}/{pt}: {e}")
            print(f"  ❌ {pt}: {e}")

# Aggregate
total = sum(s["total"] for s in stats.values())
real = sum(s["real"] for s in stats.values())
placeholder = sum(s["placeholder"] for s in stats.values())
deferred = sum(s["deferred"] for s in stats.values())
errors_n = sum(s["errors"] for s in stats.values())
pages_ok = sum(s["pages"] for s in stats.values())

print(f"\n{'═' * 65}")
print(f"BATCH ENRICH DONE — {time.time() - t0:.1f}s")
print(f"{'═' * 65}")
print(f"  Pages OK:     {pages_ok}/{total_pages}")
print(f"  Errors:       {errors_n}")
print(f"  Total recos:  {total}")
print(f"  Real recos:   {real} ({100*real/max(1,total):.1f}%)")
print(f"  Placeholders: {placeholder}")
print(f"  Deferred:     {deferred}")

# Top 5 clients by placeholder
print("\nTop clients with placeholders:")
sorted_clients = sorted(stats.items(), key=lambda x: -x[1]["placeholder"])
for cid, s in sorted_clients[:10]:
    if s["placeholder"] == 0: break
    print(f"  {cid}: {s['placeholder']} placeholders / {s['total']} total")

# Summary to file
summary = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "pages_total": total_pages,
    "pages_ok": pages_ok,
    "errors": errors_n,
    "recos_total": total,
    "recos_real": real,
    "recos_placeholder": placeholder,
    "recos_deferred": deferred,
    "real_pct": round(100 * real / max(1, total), 2),
    "by_client": {cid: dict(s) for cid, s in stats.items()},
    "errors_detail": errors[:50],
}
out = ROOT / "data" / "batch_enrich_summary.json"
out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(f"\n→ {out}")
