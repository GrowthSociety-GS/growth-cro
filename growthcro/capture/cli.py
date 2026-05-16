"""argparse CLI for cloud capture — single concern: command-line dispatch.

Routes to `orchestrator.run_single` or `orchestrator.run_batch`. Replaces the
`if __name__ == "__main__"` block of ghost_capture_cloud.py.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .orchestrator import run_batch, run_single
from .url_validator import URLValidationError, argparse_url_type, validate_url


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Ghost Capture Cloud — Playwright Python (local + cloud browser)"
    )
    ap.add_argument("--url", type=argparse_url_type,
                    help="URL à capturer (validée contre SSRF avant exécution)")
    ap.add_argument("--label", default="capture", help="Label client")
    ap.add_argument("--page-type", default="home", help="Type de page")
    ap.add_argument("--out-dir", default="./output", help="Répertoire de sortie")
    ap.add_argument("--timeout", type=int, default=120000, help="Timeout en ms")
    ap.add_argument("--cloud", action="store_true",
                    help="Mode cloud : se connecte à BROWSER_WS_ENDPOINT (Browserless.io, etc.)")
    ap.add_argument("--ws-endpoint", default=None,
                    help="WebSocket endpoint explicite (sinon: env BROWSER_WS_ENDPOINT)")
    ap.add_argument("--brightdata", action="store_true",
                    help="Forcer Bright Data Scraping Browser (bypass tous les anti-bots)")
    ap.add_argument("--batch", help="Fichier JSON de batch [{url, label, pageType}]")
    ap.add_argument("--concurrency", type=int, default=3, help="Concurrence batch")
    ap.add_argument("--delay", type=int, default=1000, help="Délai inter-chunk en ms")
    ap.add_argument("--dry-run", action="store_true", help="Afficher sans exécuter")
    args = ap.parse_args()

    if args.dry_run:
        mode = "CLOUD" if args.cloud else "LOCAL"
        if args.batch:
            tasks = json.loads(pathlib.Path(args.batch).read_text())
            print(f"DRY RUN — {len(tasks)} tasks ({mode})")
            for t in tasks:
                print(f"  {t['label']}/{t['pageType']} → {t['url']}")
        elif args.url:
            print(f"DRY RUN — {args.label}/{args.page_type} → {args.url} ({mode})")
        return 0

    if not args.url and not args.batch:
        print("❌ Spécifie --url ou --batch")
        ap.print_help()
        return 1

    # Validate URLs from --batch files upfront (--url already validated by argparse type).
    if args.batch:
        try:
            batch_tasks = json.loads(pathlib.Path(args.batch).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"❌ Batch file unreadable: {exc}")
            return 1
        for task in batch_tasks:
            try:
                validate_url(task.get("url", ""))
            except URLValidationError as exc:
                print(f"❌ Batch task rejected: {exc}")
                return 1

    # Import playwright here (fail-fast with clear message if not installed)
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ playwright non installé.")
        print("   pip install playwright")
        print("   playwright install chromium  # (mode local uniquement)")
        print("")
        print("   En mode --cloud, seul 'pip install playwright' est requis")
        print("   (pas besoin d'installer les navigateurs — ils tournent dans le cloud)")
        return 1

    import asyncio

    async def _main():
        async with async_playwright() as pw:
            if args.batch:
                results = await run_batch(
                    pw, args.batch, args.cloud, args.ws_endpoint,
                    args.concurrency, args.delay, args.timeout, args.out_dir,
                )
                ok = sum(1 for r in results if r.get("ok"))
                return 0 if ok == len(results) else 1
            else:
                result = await run_single(
                    pw, args.url, args.label, args.page_type, args.out_dir,
                    args.cloud, args.ws_endpoint, args.timeout,
                    force_brightdata=args.brightdata,
                )
                return 0 if result["ok"] else 1

    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
