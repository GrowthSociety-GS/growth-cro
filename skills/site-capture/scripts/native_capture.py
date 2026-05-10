#!/usr/bin/env python3
"""Shim — forwards to growthcro.capture.scorer (will be removed in #11)."""
import pathlib
import sys

# Ensure repo root on sys.path so the shim survives invocation from any cwd.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from growthcro.capture.scorer import main as capture_main

if __name__ == "__main__":
    sys.exit(capture_main())
