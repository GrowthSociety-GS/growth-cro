#!/usr/bin/env python3
"""
lint_code_hygiene.py — mechanical hygiene gate for GrowthCRO source tree.

Enforces docs/doctrine/CODE_DOCTRINE.md. Stdlib only (pathlib, re, ast, argparse,
json, subprocess). Designed to run <5s on the cleaned tree.

Exit codes:
    0  green (no FAIL, or only DEBT/WARN/INFO)
    1  at least one FAIL rule violated
    2  internal error (file walk failed, etc.)

Flags:
    --quiet    print FAIL only (silent on green)
    --json     machine-readable JSON output
    --staged   lint only files in `git diff --staged --name-only` (pre-commit gate)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
ACTIVE_ROOTS = ["growthcro", "skills", "moteur_gsg", "moteur_multi_judge",
                "scripts", "SCHEMA"]
EXCLUDE_PARTS = {"_archive", "__pycache__", "node_modules", "worktrees",
                 ".git", ".venv", "venv", "build", "dist"}
CONFIG_FILE = "growthcro/config.py"  # only file allowed to read env

# ─────────────────────────────────────────────────────────────────────────────
# Known structural debt — files allowed to exceed 800 LOC pending follow-up split
# sprint (skills/ god files, out of cleanup-epic god-file inventory). Removing
# a file from this set is the same commit as splitting it — failing-back is
# mechanically impossible. See docs/doctrine/CODE_DOCTRINE.md §debt.
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_DEBT = {
    "skills/site-capture/scripts/discover_pages_v25.py",
    "skills/site-capture/scripts/project_snapshot.py",
    "skills/site-capture/scripts/playwright_capture_v2.py",
    "skills/growth-site-generator/scripts/aura_compute.py",
    "skills/site-capture/scripts/build_growth_audit_data.py",
}

# Basename duplicates allowed by AD-1 (package-prefix disambiguates).
# `__main__.py` is a Python language convention — any package that supports
# `python -m <pkg>` needs one ; multiple such packages in the tree is
# legitimate (e.g. growthcro.worker + growthcro.geo). Added 2026-05-15.
BASENAME_ALLOWLIST = {"__init__.py", "__main__.py", "cli.py", "base.py",
                      "orchestrator.py", "persist.py", "prompt_assembly.py",
                      "README.md"}

# Archive folder pattern — FAIL rule #3
ARCHIVE_PATTERN = re.compile(r"^(_archive|_obsolete|.*deprecated|.*backup).*", re.IGNORECASE)

# Env-read pattern — FAIL rule #2 (AST-based; regex used only as fast prefilter)
ENV_PRE_RX = re.compile(r"\bos\.(environ|getenv)\b")

# Concern-bundle imports — WARN heuristic #2
CONCERN_BUNDLES = [
    {"requests", "httpx", "urllib", "urllib3"},
    {"sqlite3", "sqlalchemy"},
    {"jinja2", "markdown"},
    {"argparse", "click"},
    {"anthropic", "openai"},
    {"playwright", "selenium"},
]

# print()-in-pipeline pattern — WARN rule (promoted from INFO in Task #28,
# post observability migration of top-10 pipelines).
# See docs/doctrine/CODE_DOCTRINE.md §LOG.
PIPELINE_DIRS = ("growthcro/", "moteur_gsg/", "moteur_multi_judge/")


# ─────────────────────────────────────────────────────────────────────────────
def is_active_path(p: Path) -> bool:
    rel = p.relative_to(ROOT)
    parts = rel.parts
    if any(seg in EXCLUDE_PARTS for seg in parts):
        return False
    if not parts:
        return False
    return parts[0] in ACTIVE_ROOTS


def _is_excluded_seg(seg: str) -> bool:
    # Standard exclude list + archive-pattern dirs (Rule 3 flags the dir itself
    # once via iter_active_dirs; we don't double-flag its contents here).
    if seg in EXCLUDE_PARTS:
        return True
    if ARCHIVE_PATTERN.match(seg):
        return True
    return False


def iter_active_py(staged_paths: list[Path] | None = None) -> list[Path]:
    if staged_paths is not None:
        return [p for p in staged_paths if p.suffix == ".py" and p.exists()
                and is_active_path(p)
                and not any(_is_excluded_seg(s) for s in p.relative_to(ROOT).parts)]
    out: list[Path] = []
    for top in ACTIVE_ROOTS:
        base = ROOT / top
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if any(_is_excluded_seg(seg) for seg in p.relative_to(ROOT).parts):
                continue
            out.append(p)
    return out


def iter_active_dirs(staged_paths: list[Path] | None = None) -> list[Path]:
    """For archive-folder detection — walks active dirs once."""
    if staged_paths is not None:
        # On staged mode, only check parent dirs of staged files.
        seen: set[Path] = set()
        for p in staged_paths:
            for parent in p.parents:
                if parent == ROOT:
                    break
                if parent in seen:
                    continue
                seen.add(parent)
        return [p for p in seen if is_active_path(p)]
    out: list[Path] = []
    for top in ACTIVE_ROOTS:
        base = ROOT / top
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_dir():
                continue
            if any(seg in EXCLUDE_PARTS for seg in p.relative_to(ROOT).parts):
                continue
            out.append(p)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Checks
# ─────────────────────────────────────────────────────────────────────────────
def check_size(p: Path) -> tuple[str | None, int]:
    """Returns (tier, loc). tier ∈ {None, 'fail', 'debt', 'info'}."""
    try:
        loc = sum(1 for _ in p.open("rb"))
    except OSError:
        return None, 0
    rel = str(p.relative_to(ROOT))
    if loc > 800:
        if rel in KNOWN_DEBT:
            return "debt", loc
        return "fail", loc
    if loc > 300:
        return "info", loc
    return None, loc


def check_env_read(p: Path) -> bool:
    """True if this file reads env outside growthcro/config.py."""
    rel = str(p.relative_to(ROOT))
    if rel == CONFIG_FILE:
        return False
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if not ENV_PRE_RX.search(text):
        return False
    # Confirm with AST (skip strings/comments)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return True  # syntax err in a non-config file with os.environ string → flag
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "os" and node.attr in ("environ", "getenv"):
                return True
    return False


def check_archive_dir(d: Path) -> bool:
    name = d.name
    return bool(ARCHIVE_PATTERN.match(name))


def collect_basenames(files: list[Path]) -> dict[str, list[str]]:
    """basename → list[rel_path]. Excludes allowlist."""
    by_name: dict[str, list[str]] = {}
    for p in files:
        n = p.name
        if n in BASENAME_ALLOWLIST:
            continue
        by_name.setdefault(n, []).append(str(p.relative_to(ROOT)))
    return {k: v for k, v in by_name.items() if len(v) > 1}


def warn_mixed_concern(p: Path, loc: int) -> tuple[bool, str]:
    """WARN heuristics on files >300 LOC. Returns (triggered, signal_str)."""
    if loc <= 300:
        return False, ""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except (OSError, SyntaxError):
        return False, ""

    # Signal A: function-prefix entropy
    fn_names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    fn_names += [n.name for n in tree.body if isinstance(n, ast.AsyncFunctionDef)]
    prefixes: dict[str, int] = {}
    for n in fn_names:
        pfx = n.split("_", 1)[0] if "_" in n else n
        prefixes[pfx] = prefixes.get(pfx, 0) + 1
    total = sum(prefixes.values())
    big_pfx = [p_ for p_, c in prefixes.items() if total and c / total >= 0.2]
    signal_a = total >= 5 and len(big_pfx) >= 3

    # Signal B: imports from ≥3 concern bundles
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    hit_bundles = sum(1 for b in CONCERN_BUNDLES if imports & b)
    signal_b = hit_bundles >= 3

    # Signal C: ≥2 top-level classes that don't reference each other
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    signal_c = False
    if len(classes) >= 2:
        class_names = {c.name for c in classes}
        refs = []
        for c in classes:
            ref_set = set()
            for sub in ast.walk(c):
                if isinstance(sub, ast.Name) and sub.id in class_names - {c.name}:
                    ref_set.add(sub.id)
            refs.append(ref_set)
        if all(len(r) == 0 for r in refs):
            signal_c = True

    triggered = signal_a or signal_b or signal_c
    if not triggered:
        return False, ""
    parts = []
    if signal_a:
        parts.append(f"prefix-entropy({len(big_pfx)} prefixes ≥20%)")
    if signal_b:
        parts.append(f"{hit_bundles} concern-bundles imported")
    if signal_c:
        parts.append(f"{len(classes)} disjoint top-level classes")
    return True, "; ".join(parts)


def check_print_in_pipeline(p: Path, loc: int) -> int:
    """WARN: count print() calls in long-running pipeline modules.

    Promoted from INFO → WARN in Task #28 (observability migration). Pipeline
    modules (growthcro/, moteur_*/) >100 LOC with print() should use
    `growthcro.observability.logger.get_logger(__name__)` instead.

    See `docs/doctrine/CODE_DOCTRINE.md` §LOG. CLIs (`/cli/`) are exempt.
    """
    rel = str(p.relative_to(ROOT))
    if not any(rel.startswith(d) for d in PIPELINE_DIRS):
        return 0
    if rel.endswith("cli.py") or "/cli/" in rel:
        return 0  # CLIs legitimately print
    if loc < 100:
        return 0
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "print":
            count += 1
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def get_staged_files() -> list[Path]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--staged", "--name-only"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [ROOT / line.strip() for line in out.splitlines() if line.strip()]


def run(staged: bool = False) -> dict:
    staged_paths = get_staged_files() if staged else None
    py_files = iter_active_py(staged_paths)
    dirs = iter_active_dirs(staged_paths)

    fails: list[str] = []
    debts: list[str] = []
    warns: list[str] = []
    infos: list[str] = []
    print_infos: list[str] = []

    # FAIL #3 — archive folders
    for d in dirs:
        if check_archive_dir(d):
            fails.append(f"{d.relative_to(ROOT)}/: archive folder name in active path")

    # FAIL #4 — basename duplicates (only meaningful on full-tree mode)
    if not staged:
        dupes = collect_basenames(py_files)
        for basename, paths in sorted(dupes.items()):
            fails.append(f"{basename}: basename duplicate in active paths ({', '.join(paths)})")

    for p in py_files:
        rel = str(p.relative_to(ROOT))

        # FAIL #1 + DEBT + INFO — size
        tier, loc = check_size(p)
        if tier == "fail":
            fails.append(f"{rel}: {loc} LOC (limit 800)")
        elif tier == "debt":
            debts.append(f"{rel}: {loc} LOC (tracked debt)")
        elif tier == "info":
            infos.append(f"{rel}: {loc} LOC")

        # FAIL #2 — env reads outside config
        if check_env_read(p):
            fails.append(f"{rel}: os.environ/getenv outside {CONFIG_FILE}")

        # WARN — mixed concern
        triggered, signal = warn_mixed_concern(p, loc)
        if triggered:
            warns.append(f"{rel}: {loc} LOC + mixed-concern signal ({signal})")

        # WARN[print-in-pipeline] — promoted from INFO in Task #28
        n_prints = check_print_in_pipeline(p, loc)
        if n_prints > 0:
            print_infos.append(f"{rel}: {n_prints} print() calls (should use logger)")
            warns.append(f"{rel}: {n_prints} print() calls — use growthcro.observability.logger (§LOG)")

    return {
        "date": date.today().isoformat(),
        "fail": fails,
        "warn": warns,
        "info": infos,
        "debt": debts,
        "print_info": print_infos,
        "n_files_scanned": len(py_files),
    }


def render(result: dict, quiet: bool) -> None:
    fails = result["fail"]
    warns = result["warn"]
    infos = result["info"]
    debts = result["debt"]
    print_infos = result["print_info"]

    if quiet:
        if fails:
            print(f"FAIL {len(fails)} issues:")
            for line in fails:
                print(f"  {line}")
        return

    print(f"CODE HYGIENE — {result['date']}")
    print("─" * 60)
    print(f"FAIL {len(fails)} issues:")
    for line in fails:
        print(f"  {line}")
    print(f"WARN {len(warns)} issues:")
    for line in warns:
        print(f"  {line}")
    print(f"INFO {len(infos)} files >300 LOC (single-concern affirmed by reviewer):")
    for line in infos[:20]:
        print(f"  {line}")
    if len(infos) > 20:
        print(f"  ... and {len(infos) - 20} more")
    print(f"DEBT {len(debts)} files (tracked, see CODE_DOCTRINE.md §debt):")
    for line in debts:
        print(f"  {line}")
    if print_infos:
        print(f"WARN[print-in-pipeline] {len(print_infos)} files (use growthcro.observability.logger — §LOG):")
        for line in print_infos[:10]:
            print(f"  {line}")
        if len(print_infos) > 10:
            print(f"  ... and {len(print_infos) - 10} more")
    print()
    print(f"Scanned {result['n_files_scanned']} active .py files")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()

    try:
        result = run(staged=args.staged)
    except Exception as e:
        print(f"INTERNAL ERROR: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        render(result, quiet=args.quiet)

    return 1 if result["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
