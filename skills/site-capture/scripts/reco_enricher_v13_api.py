#!/usr/bin/env python3
"""Shim — use `python3 -m growthcro.recos.cli enrich ...` (will be removed in #11).

Forwards every argument to growthcro.recos.cli:main(). Legacy flag-style invocation
(--all / --client / --page / --dry-run / --model / --max-concurrent / --force) is
still accepted (back-compat in cli._looks_like_legacy_invocation).
"""
import sys
from pathlib import Path

# Repo root is 3 parents up from skills/site-capture/scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from growthcro.recos.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
