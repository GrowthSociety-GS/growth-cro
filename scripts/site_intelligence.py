#!/usr/bin/env python3
"""Shim — delegates to growthcro.research.cli (issue #7 split)."""
from growthcro.research.cli import main, run_intelligence  # noqa: F401

if __name__ == "__main__":
    main()
