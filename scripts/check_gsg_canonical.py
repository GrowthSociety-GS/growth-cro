#!/usr/bin/env python3
"""Validate the canonical GSG boundary without generating a landing page."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_gsg.core.canonical_registry import format_markdown, validate_canonical_contract


def main() -> int:
    report = validate_canonical_contract()
    print(f"Canonical GSG check: {'PASS' if report['ok'] else 'FAIL'}")
    for err in report["errors"]:
        print(f"ERROR: {err}")
    for warn in report["warnings"]:
        print(f"WARN: {warn}")
    print()
    print(format_markdown(report["snapshot"]))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
