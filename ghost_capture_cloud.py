#!/usr/bin/env python3
"""Shim — forwards to growthcro.capture.cli (will be removed in #11)."""
import sys

from growthcro.capture.cli import main

if __name__ == "__main__":
    sys.exit(main())
