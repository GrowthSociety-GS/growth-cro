"""argparse entrypoints for scoring CLIs (score_specific, score_ux)."""
from __future__ import annotations

import pathlib
import sys

from growthcro.scoring.persist import write_specific_score
from growthcro.scoring.ux import score_ux


def _project_root() -> pathlib.Path:
    """Project root (parent of `growthcro/`)."""
    return pathlib.Path(__file__).resolve().parents[2]


def score_specific() -> None:
    """`score_specific_criteria.py <label> [pageType]` entrypoint."""
    if len(sys.argv) < 2:
        from growthcro.scoring.persist import _import_page_type_filter
        _, _, list_page_types = _import_page_type_filter()
        print("Usage: score_specific_criteria.py <label> [pageType]", file=sys.stderr)
        print(f"Known pageTypes: {list_page_types()}", file=sys.stderr)
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"

    from growthcro.scoring.persist import _import_page_type_filter
    _, _, list_page_types = _import_page_type_filter()
    if page_type not in list_page_types():
        print(f"Unknown pageType '{page_type}'. Known: {list_page_types()}", file=sys.stderr)
        sys.exit(2)

    write_specific_score(label, page_type, _project_root())


def score_ux_main() -> None:
    """`score_ux.py <label> [pageType]` entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: score_ux.py <label> [pageType]", file=sys.stderr)
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    score_ux(label, page_type, _project_root())


if __name__ == "__main__":
    score_specific()
