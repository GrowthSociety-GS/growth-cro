#!/usr/bin/env python3
"""Shim — forwards to growthcro.cli.add_client (will be removed in #10)."""
import sys

from growthcro.cli.add_client import main

if __name__ == "__main__":
    sys.exit(main())
