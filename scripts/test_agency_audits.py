#!/usr/bin/env python3
"""
test_agency_audits.py — Smoke test for the audit_gads + audit_meta modules.

Runs both CLIs end-to-end against synthetic CSV fixtures under
`data/audits/_fixtures/` and asserts:

- CLI exits 0 in `--no-write` mode (preview only).
- CLI exits 0 in default write mode → 3 artefacts persisted.
- `bundle.json` round-trips to the expected schema (platform + sections A-H).
- `notion.md` includes all 8 section headings (A. through H.).
- `notion_payload.json` declares at least 30 children blocks (deterministic
  preview keeps the page substantial).
- KPIs roll-up are positive (sanity).

Exits 0 if all checks PASS, 1 otherwise.

Usage:
    python3 scripts/test_agency_audits.py [--keep] [--verbose]

The synthetic fixtures live under `data/audits/_fixtures/`; the test outputs
land under `data/audits/<platform>/_smoke_<period>/`. By default the test
directory is removed after running; pass `--keep` to inspect manually.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "audits" / "_fixtures"

PLATFORMS = (
    {
        "name": "gads",
        "csv": FIXTURES / "gads_synthetic_30d.csv",
        "module": "growthcro.audit_gads.cli",
        "expected_platform": "google_ads",
        "expected_skill": "anthropic-skills:gads-auditor",
        "kpi_keys": ("campaigns", "impressions", "clicks", "cost", "roas"),
        "min_rows": 5,
    },
    {
        "name": "meta",
        "csv": FIXTURES / "meta_synthetic_30d.csv",
        "module": "growthcro.audit_meta.cli",
        "expected_platform": "meta_ads",
        "expected_skill": "anthropic-skills:meta-ads-auditor",
        "kpi_keys": ("campaigns", "impressions", "reach", "spend", "roas"),
        "min_rows": 5,
    },
)

SECTION_PREFIXES = tuple(f"## {letter}." for letter in "ABCDEFGH")


def _run_cli(module: str, args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _validate_bundle(bundle_path: pathlib.Path, plat: dict) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    checks.append(
        (
            f"{plat['name']}: bundle.platform={plat['expected_platform']}",
            data.get("platform") == plat["expected_platform"],
            data.get("platform", ""),
        )
    )
    checks.append(
        (
            f"{plat['name']}: bundle.skill_name={plat['expected_skill']}",
            data.get("skill_name") == plat["expected_skill"],
            data.get("skill_name", ""),
        )
    )
    sections = data.get("sections", {})
    for letter in "ABCDEFGH":
        section = sections.get(letter, {})
        checks.append(
            (
                f"{plat['name']}: section {letter} present + has title",
                bool(section) and bool(section.get("title")),
                section.get("title", "")[:50],
            )
        )
    kpis = data.get("kpis", {})
    for key in plat["kpi_keys"]:
        value = kpis.get(key, 0)
        checks.append(
            (
                f"{plat['name']}: KPI {key} > 0",
                bool(value),
                str(value),
            )
        )
    rows = data.get("row_count", 0)
    checks.append(
        (
            f"{plat['name']}: row_count >= {plat['min_rows']}",
            rows >= plat["min_rows"],
            f"{rows} rows",
        )
    )
    return checks


def _validate_markdown(md_path: pathlib.Path, plat: dict) -> list[tuple[str, bool, str]]:
    text = md_path.read_text(encoding="utf-8")
    checks: list[tuple[str, bool, str]] = []
    for prefix in SECTION_PREFIXES:
        checks.append(
            (
                f"{plat['name']}: markdown contains '{prefix}'",
                prefix in text,
                prefix,
            )
        )
    checks.append(
        (
            f"{plat['name']}: markdown mentions skill",
            plat["expected_skill"] in text,
            plat["expected_skill"],
        )
    )
    return checks


def _validate_payload(payload_path: pathlib.Path, plat: dict) -> list[tuple[str, bool, str]]:
    data = json.loads(payload_path.read_text(encoding="utf-8"))
    children = data.get("children", [])
    checks: list[tuple[str, bool, str]] = []
    checks.append(
        (
            f"{plat['name']}: notion payload >= 30 blocks",
            len(children) >= 30,
            f"{len(children)} blocks",
        )
    )
    h2 = [
        c
        for c in children
        if c.get("type") == "heading_2"
    ]
    checks.append(
        (
            f"{plat['name']}: notion payload has 8 heading_2 (sections A-H)",
            len(h2) == 8,
            f"{len(h2)} heading_2",
        )
    )
    return checks


def _audit_one(plat: dict, slug: str, period: str, keep: bool, verbose: bool) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    # 1. preview mode --no-write
    res = _run_cli(
        plat["module"],
        [
            "--client",
            slug,
            "--csv",
            str(plat["csv"]),
            "--period",
            period,
            "--no-write",
        ],
        cwd=ROOT,
    )
    checks.append(
        (
            f"{plat['name']}: cli --no-write exits 0",
            res.returncode == 0,
            res.stderr.strip()[:100] if res.returncode else "ok",
        )
    )

    # 2. default mode (writes artefacts)
    out_dir = ROOT / "data" / "audits" / plat["name"] / slug / period
    if out_dir.exists():
        shutil.rmtree(out_dir)
    res2 = _run_cli(
        plat["module"],
        [
            "--client",
            slug,
            "--csv",
            str(plat["csv"]),
            "--period",
            period,
        ],
        cwd=ROOT,
    )
    checks.append(
        (
            f"{plat['name']}: cli write-mode exits 0",
            res2.returncode == 0,
            res2.stderr.strip()[:100] if res2.returncode else "ok",
        )
    )

    bundle_path = out_dir / "bundle.json"
    md_path = out_dir / "notion.md"
    payload_path = out_dir / "notion_payload.json"

    for path, label in (
        (bundle_path, "bundle.json"),
        (md_path, "notion.md"),
        (payload_path, "notion_payload.json"),
    ):
        checks.append(
            (
                f"{plat['name']}: {label} exists",
                path.exists(),
                str(path) if not path.exists() else f"{path.stat().st_size} bytes",
            )
        )

    if bundle_path.exists():
        checks.extend(_validate_bundle(bundle_path, plat))
    if md_path.exists():
        checks.extend(_validate_markdown(md_path, plat))
    if payload_path.exists():
        checks.extend(_validate_payload(payload_path, plat))

    if not keep and out_dir.exists():
        shutil.rmtree(out_dir)
        if verbose:
            print(f"  cleaned up {out_dir}")
    elif keep and verbose:
        print(f"  kept artefacts under {out_dir}")

    return checks


def _format_checks(checks: list[tuple[str, bool, str]]) -> str:
    lines = []
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {name}"
        if detail:
            line += f"  ({detail})"
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test agency audit modules (gads + meta).")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the artefact directory after the run (default: clean up).",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    if not FIXTURES.exists():
        print(f"[agency-audits-smoke] FAIL — fixtures missing: {FIXTURES}", file=sys.stderr)
        return 1

    all_checks: list[tuple[str, bool, str]] = []
    period = "_smoke_30d"
    slug = "_smoke_synthetic"

    for plat in PLATFORMS:
        if not plat["csv"].exists():
            print(f"[agency-audits-smoke] FAIL — fixture missing: {plat['csv']}", file=sys.stderr)
            return 1
        if args.verbose:
            print(f"[agency-audits-smoke] running {plat['name']} on {plat['csv'].name}")
        all_checks.extend(_audit_one(plat, slug, period, args.keep, args.verbose))

    print("[agency-audits-smoke] results:")
    print(_format_checks(all_checks))

    failed = [c for c in all_checks if not c[1]]
    if failed:
        print(f"\n[agency-audits-smoke] FAIL — {len(failed)} check(s) failed.", file=sys.stderr)
        return 1
    print(f"\n[agency-audits-smoke] PASS — all {len(all_checks)} checks green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
