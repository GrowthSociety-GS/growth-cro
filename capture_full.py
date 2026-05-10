#!/usr/bin/env python3
"""Shim — forwards to growthcro.cli.capture_full (will be removed in #10)."""
import sys

from growthcro.cli.capture_full import main

if __name__ == "__main__":
    sys.exit(main())
