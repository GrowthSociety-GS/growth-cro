#!/usr/bin/env python3
"""
batch_site.py — Batch scoring 6 blocs pour tous les clients.

Lit clients_database.json, lance capture_site.py en mode natif pour chacun.
Produit un résumé CSV + JSON avec les scores de chaque client.

Usage :
    python batch_site.py [--apify] [--level N] [--skip-existing] [--only <label1,label2>]

    --skip-existing   Ne pas re-capturer les clients qui ont déjà un site_audit.json
    --only label1,..  Ne traiter que ces labels
    --apify           Activer le mode hybride Apify (screenshots)
    --level N         Niveau proxy Apify

v1.0 — 2026-04-10
"""

import json, sys, os, time, pathlib, subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
SCRIPTS = pathlib.Path(__file__).resolve().parent
DB_FILE = ROOT / "data" / "clients_database.json"
CAPTURES_DIR = ROOT / "data" / "captures"

# ── Args ──────────────────────────────────────────────────────
args = sys.argv[1:]
USE_APIFY = False
USE_SPATIAL = False
APIFY_LEVEL = 1
SKIP_EXISTING = False
ONLY_LABELS = None

if "--apify" in args:
    USE_APIFY = True
    args.remove("--apify")
if "--spatial" in args:
    USE_SPATIAL = True
    args.remove("--spatial")
if "--level" in args:
    i = args.index("--level")
    APIFY_LEVEL = int(args[i + 1])
    args.pop(i); args.pop(i)
if "--skip-existing" in args:
    SKIP_EXISTING = True
    args.remove("--skip-existing")
if "--only" in args:
    i = args.index("--only")
    ONLY_LABELS = set(args[i + 1].split(","))
    args.pop(i); args.pop(i)

# ── Load clients ──────────────────────────────────────────────
db = json.loads(DB_FILE.read_text())
clients = db["clients"]

# Map businessType to capture_site.py category
BIZ_MAP = {
    "ecommerce": "ecommerce",
    "saas": "saas",
    "app": "app",
    "lead_gen": "lead_gen",
    "fintech": "fintech",
}

# Filter
if ONLY_LABELS:
    clients = [c for c in clients if c["id"] in ONLY_LABELS]

print("=" * 60)
print(f"BATCH SITE SCORING — {len(clients)} clients")
bmode = "NATIF"
if USE_APIFY and USE_SPATIAL: bmode = "HYBRIDE + SPATIAL V9"
elif USE_APIFY: bmode = "HYBRIDE"
elif USE_SPATIAL: bmode = "NATIF + SPATIAL V9"
print(f"Mode: {bmode}")
print(f"Skip existing: {SKIP_EXISTING}")
print("=" * 60)

# ── Batch ─────────────────────────────────────────────────────
results = []
skipped = 0
errors = 0
t_total = time.time()

for idx, client in enumerate(clients):
    label = client["id"]
    identity = client.get("identity", {})
    url = identity.get("url", "").rstrip("/")
    biz_type = identity.get("businessType", "unknown")
    biz_cat = BIZ_MAP.get(biz_type, "unknown")

    if not url:
        print(f"\n[{idx+1}/{len(clients)}] {label}: ❌ No URL — skip")
        results.append({"label": label, "status": "no_url", "score": None})
        errors += 1
        continue

    # Skip existing?
    audit_file = CAPTURES_DIR / label / "site_audit.json"
    if SKIP_EXISTING and audit_file.exists():
        # Check if it has 6 pillars
        try:
            audit = json.loads(audit_file.read_text())
            pillars = len(audit.get("activePillars", []))
            if pillars >= 6:
                score = audit.get("siteScore", {}).get("final", 0)
                print(f"\n[{idx+1}/{len(clients)}] {label}: ⏭️  Skip (existing 6-pillar audit: {score}/100)")
                results.append({"label": label, "status": "existing", "score": score, "pillars": pillars})
                skipped += 1
                continue
        except:
            pass

    print(f"\n{'─' * 60}")
    print(f"[{idx+1}/{len(clients)}] {label} — {url} [{biz_cat}]")
    print(f"{'─' * 60}")

    t0 = time.time()

    cmd = [sys.executable, str(SCRIPTS / "capture_site.py"), url, label, biz_cat]
    if USE_APIFY:
        cmd.append("--apify")
        cmd.extend(["--level", str(APIFY_LEVEL)])
    if USE_SPATIAL:
        cmd.append("--spatial")
        if not USE_APIFY:
            cmd.extend(["--level", str(APIFY_LEVEL)])

    env = config.system_env_copy()
    if USE_APIFY and config.apify_token():
        env["APIFY_TOKEN"] = config.require_apify_token()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180,
            env=env,
        )
        elapsed = round(time.time() - t0, 2)

        if result.returncode == 0:
            # Read site audit
            audit_file = CAPTURES_DIR / label / "site_audit.json"
            if audit_file.exists():
                audit = json.loads(audit_file.read_text())
                score = audit.get("siteScore", {}).get("final", 0)
                pillars = audit.get("activePillars", [])
                pages_audited = audit.get("pagesAudited", [])
                n_pages = len(pages_audited)
                pillars_count = audit.get("totalPillars", 0)
                print(f"  ✅ {label}: {score}/100 ({n_pages} pages, {pillars_count} pillars) in {elapsed}s")
                results.append({
                    "label": label, "status": "ok", "score": score,
                    "pillars": pillars_count, "pages": n_pages, "elapsed": elapsed,
                    "url": url, "bizCat": biz_cat,
                })
            else:
                print(f"  ⚠️  {label}: capture OK but no site_audit.json ({elapsed}s)")
                results.append({"label": label, "status": "no_audit", "score": None, "elapsed": elapsed})
                errors += 1
        else:
            elapsed = round(time.time() - t0, 2)
            err_msg = result.stderr[:200] if result.stderr else result.stdout[-200:]
            print(f"  ❌ {label}: failed ({elapsed}s) — {err_msg}")
            results.append({"label": label, "status": "error", "score": None, "error": err_msg[:200], "elapsed": elapsed})
            errors += 1
    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - t0, 2)
        print(f"  ❌ {label}: TIMEOUT ({elapsed}s)")
        results.append({"label": label, "status": "timeout", "score": None, "elapsed": elapsed})
        errors += 1
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        print(f"  ❌ {label}: exception ({elapsed}s) — {str(e)[:100]}")
        results.append({"label": label, "status": "exception", "score": None, "error": str(e)[:200], "elapsed": elapsed})
        errors += 1

total_time = round(time.time() - t_total, 2)

# ── Summary ───────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"BATCH COMPLETE — {total_time}s")
print(f"{'=' * 60}")

ok_results = [r for r in results if r["status"] == "ok"]
existing_results = [r for r in results if r["status"] == "existing"]
all_scored = ok_results + existing_results

print(f"  OK: {len(ok_results)}")
print(f"  Existing: {len(existing_results)}")
print(f"  Errors: {errors}")
print(f"  Skipped: {skipped}")

if all_scored:
    scores = [r["score"] for r in all_scored if r["score"] is not None]
    scores.sort(reverse=True)
    mean = sum(scores) / len(scores)
    median = scores[len(scores) // 2]
    print(f"\n  📊 Stats ({len(scores)} scored):")
    print(f"     Mean:   {mean:.1f}/100")
    print(f"     Median: {median:.1f}/100")
    print(f"     Best:   {scores[0]:.1f}/100")
    print(f"     Worst:  {scores[-1]:.1f}/100")

    print(f"\n  🏆 Classement:")
    all_scored.sort(key=lambda r: r.get("score", 0) or 0, reverse=True)
    for i, r in enumerate(all_scored):
        s = r.get("score", 0) or 0
        tier = "🟢" if s >= 70 else "🟡" if s >= 50 else "🔴"
        elapsed_str = f" ({r.get('elapsed', '?')}s)" if r.get("elapsed") else ""
        print(f"     {i+1:2d}. {tier} {r['label']:25s} {s:5.1f}/100{elapsed_str}")

# ── Save results ──────────────────────────────────────────────
batch_output = {
    "batchId": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
    "totalClients": len(clients),
    "ok": len(ok_results),
    "existing": len(existing_results),
    "errors": errors,
    "totalTime": total_time,
    "mode": bmode.lower(),
    "results": results,
}

out_file = ROOT / "data" / f"batch_6blocs_{batch_output['batchId']}.json"
out_file.write_text(json.dumps(batch_output, ensure_ascii=False, indent=2))
print(f"\n  📄 Résultats: {out_file}")
