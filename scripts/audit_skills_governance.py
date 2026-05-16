"""audit_skills_governance.py — validate SKILLS_REGISTRY_GOVERNANCE.json.

Mono-concern: validation. Stdlib only. No LLM call. No network.

For each entry in `growthcro/SKILLS_REGISTRY_GOVERNANCE.json`:
  1. If `invocation_proof` is of the form `<path>:<line>`: verify the file
     exists, the line exists, and that line still mentions the skill id (or
     a normalized variant: dash↔underscore). If broken: drift, exit 1.
  2. If `invocation_proof == "no occurrence found via grep"`:
     - For `installed_external_dormant`: re-grep across *.py to confirm the
       skill is STILL dormant. If a new invocation appeared, the label
       drifted (the skill is no longer dormant) → exit 1.
     - For other types: tolerated (skill is session-level or doc-only).

Exit codes:
  0 — registry consistent with code state
  1 — drift detected (broken proof line, or dormant became active)
  2 — registry file unreadable / schema invalid

Pattern reference: scripts/lint_code_hygiene.py (CODE_DOCTRINE §Linter contract).

Usage:
    python3 scripts/audit_skills_governance.py
    python3 scripts/audit_skills_governance.py --verbose
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "growthcro" / "SKILLS_REGISTRY_GOVERNANCE.json"

# Folders to scan when checking dormant-vs-active. Mirrors active source tree.
SCAN_DIRS = [
    "growthcro",
    "moteur_gsg",
    "moteur_multi_judge",
    "skills",
    "scripts",
    "state.py",
]

# Folders/file substrings to ignore when grepping (no real invocations).
EXCLUDE_SUBSTR = (
    "_archive",
    "/.git/",
    "/node_modules/",
    "/__pycache__/",
    "/tests/",
    "/test_",
    "/SKILLS_REGISTRY_GOVERNANCE.json",
    "/audit_skills_governance.py",
)


def _iter_py_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Walk SCAN_DIRS for .py files, excluding noise paths."""
    found: list[pathlib.Path] = []
    for entry in SCAN_DIRS:
        target = root / entry
        if not target.exists():
            continue
        if target.is_file() and target.suffix == ".py":
            found.append(target)
            continue
        for path in target.rglob("*.py"):
            posix = path.as_posix()
            if any(sub in posix for sub in EXCLUDE_SUBSTR):
                continue
            found.append(path)
    return found


def _normalize_variants(skill_id: str) -> tuple[str, ...]:
    """Return search variants for a skill id (handle dash↔underscore)."""
    return (skill_id, skill_id.replace("-", "_"), skill_id.replace("_", "-"))


def _grep_files(skill_id: str, files: list[pathlib.Path]) -> list[tuple[pathlib.Path, int, str]]:
    """Return (file, lineno, line) hits for skill_id across files."""
    variants = _normalize_variants(skill_id)
    hits: list[tuple[pathlib.Path, int, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(v in line for v in variants):
                hits.append((path, lineno, line.rstrip()))
                break  # 1 file = 1 hit is enough to disprove dormancy
    return hits


def _check_proof_line(skill_id: str, proof: str, root: pathlib.Path) -> str | None:
    """Verify a file:line proof. Return None if OK, else a diagnostic."""
    if ":" not in proof:
        return f"malformed proof (expected file:line): {proof!r}"
    raw_path, _, raw_line = proof.rpartition(":")
    try:
        line_no = int(raw_line)
    except ValueError:
        return f"malformed line number in proof: {proof!r}"
    path = root / raw_path
    if not path.exists():
        return f"proof file does not exist: {path}"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"could not read proof file {path}: {exc}"
    if line_no < 1 or line_no > len(lines):
        return f"proof line {line_no} out of range (file has {len(lines)} lines)"
    line_text = lines[line_no - 1]
    variants = _normalize_variants(skill_id)
    if not any(v in line_text for v in variants):
        return (
            f"proof line {line_no} of {raw_path} no longer mentions {skill_id} "
            f"(variants {variants}); got: {line_text.strip()!r}"
        )
    return None


def _load_registry(path: pathlib.Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[FATAL] Registry not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as exc:
        print(f"[FATAL] Registry is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="Print OK lines too")
    args = parser.parse_args(argv)

    registry = _load_registry(REGISTRY_PATH)
    entries = registry.get("entries")
    if not isinstance(entries, list):
        print("[FATAL] Registry missing 'entries' list", file=sys.stderr)
        return 2

    py_files = _iter_py_files(ROOT)
    if args.verbose:
        print(f"[info] scanning {len(py_files)} .py files for dormancy checks")

    drift: list[str] = []
    checked = 0
    for entry in entries:
        skill_id = entry.get("id")
        proof = entry.get("invocation_proof", "")
        kind = entry.get("type", "")
        if not skill_id or not kind:
            drift.append(f"entry missing id or type: {entry}")
            continue
        checked += 1

        if proof and proof != "no occurrence found via grep":
            err = _check_proof_line(skill_id, proof, ROOT)
            if err:
                drift.append(f"[{skill_id}] {err}")
            elif args.verbose:
                print(f"  ok  {skill_id} -> {proof}")
            continue

        # proof == "no occurrence found via grep"
        if kind == "installed_external_dormant":
            hits = _grep_files(skill_id, py_files)
            if hits:
                first = hits[0]
                drift.append(
                    f"[{skill_id}] labeled installed_external_dormant but found "
                    f"{len(hits)} invocation(s); first: {first[0].relative_to(ROOT)}:{first[1]}"
                )
            elif args.verbose:
                print(f"  ok  {skill_id} (dormant confirmed, 0 hits)")
        else:
            # Session-level / doc-only entries: no Python grep expected.
            if args.verbose:
                print(f"  ok  {skill_id} (session-level, grep not required)")

    print(f"\n[summary] {checked} entries checked, {len(drift)} drift event(s).")
    if drift:
        print("\n[DRIFT DETECTED]")
        for msg in drift:
            print(f"  - {msg}")
        return 1
    print("[OK] Registry consistent with code state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
