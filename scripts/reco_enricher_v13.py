#!/usr/bin/env python3
"""Shim — use `python3 -m growthcro.recos.cli prepare ...` (will be removed in #11).

Forwards every argument to growthcro.recos.cli:main(). The legacy --prepare
flag-style invocation is still accepted (back-compat in cli._looks_like_legacy_invocation).
"""
import sys
from pathlib import Path

# Ensure the repo root (parent of scripts/) is on sys.path so growthcro.* resolves
# regardless of where this shim is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from growthcro.recos.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
