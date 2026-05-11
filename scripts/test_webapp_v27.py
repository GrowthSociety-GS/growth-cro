#!/usr/bin/env python3
"""
test_webapp_v27.py — Playwright headless smoke test for V27 Command Center.

Validates that `deliverables/GrowthCRO-V27-CommandCenter.html` :
- loads in < 3s without JS errors
- exposes 56 clients via `window.GROWTH_AUDIT_DATA`
- navigates the 4 views (command / audit / gsg / demo)
- audit pane filters priority/effort/lift render & filter recos
- GSG pane exposes 5 modes (complete/replace/extend/elevate/genesis)
- 3 client rows (weglot, japhy, random) load detail without console error

Exit 0 if PASS, 1 if FAIL. Sole-concern: webapp V27 functional smoke.
"""
from __future__ import annotations

import argparse
import pathlib
import random
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = ROOT / "deliverables" / "GrowthCRO-V27-CommandCenter.html"
LOAD_BUDGET_S = 3.0
EXPECTED_CLIENTS_MIN = 50
EXPECTED_VIEWS = ["command", "audit", "gsg", "demo"]
EXPECTED_GSG_MODES = ["complete", "replace", "extend", "elevate", "genesis"]


def fail(checks: list[tuple[str, bool, str]]) -> bool:
    return any(not ok for _, ok, _ in checks)


def fmt(checks: list[tuple[str, bool, str]]) -> str:
    lines = []
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        lines.append(f"  [{mark}] {name}{(' - ' + detail) if detail else ''}")
    return "\n".join(lines)


def run_smoke(headless: bool = True, verbose: bool = False) -> int:
    if not HTML.exists():
        print(f"FATAL: {HTML} missing", file=sys.stderr)
        return 1

    checks: list[tuple[str, bool, str]] = []
    page_errors: list[str] = []
    console_errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on(
            "console",
            lambda m: console_errors.append(m.text) if m.type == "error" else None,
        )

        t0 = time.time()
        page.goto(f"file://{HTML.resolve()}")
        page.wait_for_load_state("networkidle", timeout=30000)
        load_s = time.time() - t0

        checks.append(("Page load < 3s", load_s < LOAD_BUDGET_S, f"{load_s:.2f}s"))

        n_clients = page.evaluate(
            "() => window.GROWTH_AUDIT_DATA ? window.GROWTH_AUDIT_DATA.clients.length : 0"
        )
        checks.append(
            (
                f"DATA exposes >={EXPECTED_CLIENTS_MIN} clients",
                n_clients >= EXPECTED_CLIENTS_MIN,
                f"got {n_clients}",
            )
        )

        fleet = page.evaluate(
            "() => window.GROWTH_AUDIT_DATA && window.GROWTH_AUDIT_DATA.fleet"
        ) or {}
        checks.append(
            (
                "Fleet aggregates present (n_pages, n_recos)",
                bool(fleet.get("n_pages") and fleet.get("n_recos")),
                f"pages={fleet.get('n_pages')} recos={fleet.get('n_recos')}",
            )
        )

        for view in EXPECTED_VIEWS:
            page.click(f'.nav button[data-view="{view}"]')
            page.wait_for_timeout(200)
            visible = page.is_visible(f"#view-{view}")
            checks.append((f"View '{view}' visible after switch", visible, ""))

        page.click('.nav button[data-view="audit"]')
        page.wait_for_timeout(300)
        for fid in ("audit-priority", "audit-effort", "audit-lift", "audit-reset"):
            checks.append(
                (f"Audit filter #{fid}", page.is_visible(f"#{fid}"), "")
            )
        page.select_option("#audit-priority", "P0")
        page.wait_for_timeout(200)
        reset_label = page.text_content("#audit-reset") or ""
        checks.append(
            (
                "Audit filter P0 changes counter",
                "/" in reset_label,
                f"reset label: {reset_label.strip()}",
            )
        )

        page.click('.nav button[data-view="gsg"]')
        page.wait_for_timeout(300)
        modes_count = page.locator("[data-gsg-mode]").count()
        checks.append(
            ("GSG pane exposes 5 modes", modes_count == 5, f"got {modes_count}")
        )
        for mode in EXPECTED_GSG_MODES:
            sel = f'[data-gsg-mode="{mode}"]'
            checks.append((f"GSG mode '{mode}' present", page.locator(sel).count() == 1, ""))
            page.click(sel)
            page.wait_for_timeout(120)
            meta = page.text_content("#briefMeta") or ""
            checks.append(
                (
                    f"GSG mode '{mode}' updates brief meta",
                    mode in meta.lower() or mode.capitalize() in meta,
                    f"meta={meta!r}",
                )
            )

        page.click('.nav button[data-view="command"]')
        page.wait_for_timeout(200)
        client_ids = page.evaluate(
            "() => Array.from(document.querySelectorAll('[data-client]')).map(b => b.dataset.client)"
        )
        targets = ["weglot", "japhy"]
        pool = [c for c in client_ids if c not in targets]
        if pool:
            targets.append(random.choice(pool))
        for cid in targets:
            if cid not in client_ids:
                checks.append((f"Client '{cid}' visible in fleet", False, ""))
                continue
            page.click(f'[data-client="{cid}"]')
            page.wait_for_timeout(250)
            title = page.text_content("#clientTitle") or ""
            checks.append(
                (
                    f"Click client '{cid}' updates detail",
                    bool(title.strip()) and title.lower() != "client",
                    f"clientTitle={title!r}",
                )
            )

        checks.append(("No pageerror events", not page_errors, f"{len(page_errors)} errors"))
        checks.append(
            ("No console.error events", not console_errors, f"{len(console_errors)} errors")
        )

        browser.close()

    print(fmt(checks))
    if verbose:
        for e in page_errors:
            print(f"  pageerror: {e[:300]}")
        for e in console_errors:
            print(f"  console.error: {e[:300]}")

    failed = fail(checks)
    print(f"\nRESULT: {'FAIL' if failed else 'PASS'} ({sum(1 for _, ok, _ in checks if ok)}/{len(checks)} checks)")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="V27 webapp smoke test")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--verbose", action="store_true", help="Print error details")
    args = parser.parse_args()
    return run_smoke(headless=not args.headed, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
