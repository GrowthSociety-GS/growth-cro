#!/usr/bin/env python3
"""Shim — delegates to growthcro.scoring.cli.score_specific (issue #7 split)."""
from growthcro.scoring.cli import score_specific

# Re-export legacy public API so dependent scripts that imported from here keep working.
from growthcro.scoring.persist import (  # noqa: F401
    score_page_type_specific,
)
from growthcro.scoring.specific import (  # noqa: F401
    DETECTORS,
    TERNARY,
    d_review_required,
)

if __name__ == "__main__":
    score_specific()
