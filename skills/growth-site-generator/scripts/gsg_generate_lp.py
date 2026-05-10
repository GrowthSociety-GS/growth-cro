"""Compat shim — split into ``growthcro.gsg_lp`` (issue #8).

The original 1,218 LOC monolith is gone. Use the sub-package:

    python3 -m growthcro.gsg_lp --client weglot --page-type listicle ...

or import the helpers directly:

    from growthcro.gsg_lp.data_loaders import load_brand_dna
    from growthcro.gsg_lp.mega_prompt_builder import build_mega_prompt
    from growthcro.gsg_lp.repair_loop import run_repair_loop

This shim keeps the legacy CLI invocation working
(``python3 skills/growth-site-generator/scripts/gsg_generate_lp.py ...``)
because external sub-agents (skills/, deliverables/) reference this
path. Removed in issue #11 once consumers migrate.
"""
from __future__ import annotations

import pathlib
import sys

# Allow this script to import the growthcro package even when invoked
# directly (cwd may be skills/growth-site-generator/scripts/).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from growthcro.gsg_lp.lp_orchestrator import main  # noqa: E402

__all__ = ["main"]


if __name__ == "__main__":
    main()
