#!/usr/bin/env python3
"""
batch_ghost_recapture.py — Re-capture ghost complète des clients.

Lance capture_full.py sur chaque client (ghost → native --html → perception → intent).
À exécuter depuis la MACHINE LOCALE de Mathis (Node + Playwright requis).

Modes :
  --spa-only     : Ne re-capture QUE les 29 pages SPA sans H1 (priorité 1)
  --all          : Re-capture TOUS les clients (80+)
  --only <label> : Un seul client

Usage:
    python3 batch_ghost_recapture.py --spa-only
    python3 batch_ghost_recapture.py --all
    python3 batch_ghost_recapture.py --only japhy
    python3 batch_ghost_recapture.py --spa-only --dry-run

v1.0 — 2026-04-17
"""

import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
CAPTURES = ROOT / "data" / "captures"
DB_PATH = ROOT / "data" / "clients_database.json"

# 29 pages identifiées comme SPA sans H1 après le batch reparse du 2026-04-17
SPA_NO_H1_PAGES = [
    ("andthegreen", "blog"),
    ("asphalte", "collection"),
    ("asphalte", "home"),
    ("back_market", "lp_sales"),
    ("back_market", "quiz_vsl"),
    ("epycure", "collection"),
    ("epycure", "pdp"),
    ("fygr", "pdp"),
    ("georide", "collection"),
    ("glitch_beauty", "collection"),
    ("japhy", "quiz_vsl"),
    ("kiliba", "blog"),
    ("la_belle_vie", "pdp"),
    ("leboncoin_pro", "home"),
    ("linear", "pricing"),
    ("myvariations", "collection"),
    ("norauto", "home"),
    ("playplay", "pricing"),
    ("reveal", "home"),
    ("seoni", "pdp"),
    ("stan", "home"),
    ("strava", "pricing"),
    ("sunday", "blog"),
    ("thefork", "home"),
    ("trade_republic", "home"),
    ("trade_republic", "lp_sales"),
    ("unbottled", "collection"),
    ("unbottled", "pdp"),
    ("wespriing", "quiz_vsl"),
]


def load_client_urls():
    """Load URL mapping from clients_database.json."""
    urls = {}
    biz = {}
    if DB_PATH.exists():
        db = json.loads(DB_PATH.read_text())
        clients = db.get("clients", db) if isinstance(db, dict) else db
        if isinstance(clients, list):
            for c in clients:
                label = c.get("id", "")
                url = c.get("identity", {}).get("url", "")
                bt = c.get("identity", {}).get("businessType", "ecommerce")
                if label and url:
                    urls[label] = url
                    biz[label] = bt
    return urls, biz


def main():
    ap = argparse.ArgumentParser(description="Batch ghost re-capture (machine locale)")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--spa-only", action="store_true",
                      help="Re-capture uniquement les 29 pages SPA sans H1")
    mode.add_argument("--all", action="store_true",
                      help="Re-capture tous les clients")
    mode.add_argument("--only", help="Re-capture un seul client")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-intent", action="store_true",
                    help="Skip intent detection (stage 4)")
    ap.add_argument("--continue-on-error", action="store_true",
                    help="Continue batch even if a client fails")
    args = ap.parse_args()

    urls, biz = load_client_urls()

    # Build task list
    tasks = []
    if args.spa_only:
        for label, page_type in SPA_NO_H1_PAGES:
            url = urls.get(label, f"https://{label.replace('_', '')}.com")
            bt = biz.get(label, "ecommerce")
            tasks.append((label, page_type, url, bt))
    elif args.only:
        label = args.only
        url = urls.get(label, f"https://{label.replace('_', '')}.com")
        bt = biz.get(label, "ecommerce")
        # Find all page types for this client
        client_dir = CAPTURES / label
        if client_dir.exists():
            for page_dir in sorted(client_dir.iterdir()):
                if page_dir.is_dir():
                    tasks.append((label, page_dir.name, url, bt))
        else:
            tasks.append((label, "home", url, bt))
    else:  # --all
        for client_dir in sorted(CAPTURES.iterdir()):
            if not client_dir.is_dir():
                continue
            label = client_dir.name
            url = urls.get(label, f"https://{label.replace('_', '')}.com")
            bt = biz.get(label, "ecommerce")
            for page_dir in sorted(client_dir.iterdir()):
                if page_dir.is_dir() and (page_dir / "page.html").exists():
                    tasks.append((label, page_dir.name, url, bt))

    print(f"{'='*60}")
    print(f"BATCH GHOST RE-CAPTURE")
    print(f"Mode: {'SPA-only (29 pages)' if args.spa_only else 'ALL' if args.all else args.only}")
    print(f"Tasks: {len(tasks)} pages")
    print(f"Dry run: {args.dry_run}")
    print(f"{'='*60}")

    if args.dry_run:
        for label, page_type, url, bt in tasks:
            print(f"  {label}/{page_type} → {url} ({bt})")
        return 0

    results = {"ok": 0, "partial": 0, "failed": 0}
    errors = []
    t0 = time.time()

    for i, (label, page_type, url, bt) in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {label}/{page_type} ({bt})")

        # Build page-specific URL
        page_url = url
        if page_type != "home":
            # For non-home pages, we'd need the actual URL from captures
            # Check if there's a capture.json with the final URL
            cap_file = CAPTURES / label / page_type / "capture.json"
            if cap_file.exists():
                try:
                    cap = json.loads(cap_file.read_text())
                    meta_url = cap.get("meta", {}).get("url", "")
                    if meta_url:
                        page_url = meta_url
                except:
                    pass

        cmd = [
            sys.executable, str(ROOT / "capture_full.py"),
            page_url, label, bt,
            "--page-type", page_type,
        ]
        if args.no_intent:
            cmd.append("--no-intent")

        try:
            r = subprocess.run(cmd, timeout=120, cwd=str(ROOT))
            if r.returncode == 0:
                results["ok"] += 1
            elif r.returncode == 2:
                results["partial"] += 1
            else:
                results["failed"] += 1
                errors.append(f"{label}/{page_type}: exit={r.returncode}")
                if not args.continue_on_error:
                    print(f"\n❌ Stopping on error. Use --continue-on-error to keep going.")
                    break
        except subprocess.TimeoutExpired:
            results["failed"] += 1
            errors.append(f"{label}/{page_type}: TIMEOUT (120s)")
            if not args.continue_on_error:
                break
        except Exception as e:
            results["failed"] += 1
            errors.append(f"{label}/{page_type}: {e}")
            if not args.continue_on_error:
                break

        # Progress
        elapsed = time.time() - t0
        rate = i / elapsed if elapsed > 0 else 0
        eta = (len(tasks) - i) / rate if rate > 0 else 0
        print(f"  [{i}/{len(tasks)}] ok={results['ok']} partial={results['partial']} "
              f"failed={results['failed']} | {elapsed:.0f}s, ETA {eta:.0f}s")

    dt = time.time() - t0
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE in {dt:.0f}s")
    print(f"  OK:      {results['ok']}")
    print(f"  Partial: {results['partial']}")
    print(f"  Failed:  {results['failed']}")
    if errors:
        print(f"\nErrors:")
        for e in errors:
            print(f"  ❌ {e}")
    print(f"{'='*60}")

    # Next steps
    print(f"\n📋 NEXT STEPS:")
    print(f"  1. Re-run semantic scorer:")
    print(f"     ANTHROPIC_API_KEY=sk-... python3 skills/site-capture/scripts/semantic_scorer.py --all")
    print(f"  2. Re-run page scoring:")
    print(f"     python3 skills/site-capture/scripts/batch_rescore.py")

    return 0 if results["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
