"""argparse entrypoints for scoring CLIs (score_specific, score_ux).

Issue #10 — exposes a unified subcommand dispatcher so sub-agents can call
``python3 -m growthcro.scoring.cli specific <label> [page]`` or ``ux <label>
[page]`` without falling back to ``-c "from ... import"`` incantations.

Backwards-compatible: invoking the module without a subcommand still routes
to ``score_specific`` to keep the legacy ``score_specific_criteria.py`` shim
behaviour identical.
"""
from __future__ import annotations

import pathlib
import sys

from growthcro.scoring.persist import write_specific_score
from growthcro.scoring.ux import score_ux


def _project_root() -> pathlib.Path:
    """Project root (parent of `growthcro/`)."""
    return pathlib.Path(__file__).resolve().parents[2]


def _parse_label_page(argv: list[str], usage: str) -> tuple[str, str]:
    if not argv or argv[0] in {"-h", "--help"}:
        print(f"Usage: {usage}", file=sys.stderr)
        sys.exit(0 if argv and argv[0] in {"-h", "--help"} else 1)
    label = argv[0]
    page_type = argv[1] if len(argv) > 1 else "home"
    return label, page_type


def score_specific() -> None:
    """``python3 -m growthcro.scoring.cli specific <label> [pageType]``.

    Equivalent to the legacy ``score_specific_criteria.py <label> [pageType]``.
    """
    argv = sys.argv[1:]
    # Support both `cli.py specific <label>` and legacy `cli.py <label>`.
    if argv and argv[0] == "specific":
        argv = argv[1:]
    label, page_type = _parse_label_page(
        argv, "python3 -m growthcro.scoring.cli specific <label> [pageType]"
    )

    from growthcro.scoring.persist import _import_page_type_filter
    _, _, list_page_types = _import_page_type_filter()
    if page_type not in list_page_types():
        print(f"Unknown pageType '{page_type}'. Known: {list_page_types()}", file=sys.stderr)
        sys.exit(2)

    write_specific_score(label, page_type, _project_root())


def score_ux_main() -> None:
    """``python3 -m growthcro.scoring.cli ux <label> [pageType]``."""
    argv = sys.argv[1:]
    if argv and argv[0] == "ux":
        argv = argv[1:]
    label, page_type = _parse_label_page(
        argv, "python3 -m growthcro.scoring.cli ux <label> [pageType]"
    )
    score_ux(label, page_type, _project_root())


def main() -> None:
    """Subcommand dispatcher (issue #10)."""
    argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print(
            "Usage: python3 -m growthcro.scoring.cli <subcommand> <label> [pageType]\n"
            "\n"
            "Subcommands:\n"
            "  specific   Score page-type-specific criteria (default).\n"
            "  ux         Score the UX pillar.\n"
            "\n"
            "Without a subcommand, defaults to `specific` for backward\n"
            "compatibility with the legacy `score_specific_criteria.py` shim.",
            file=sys.stderr,
        )
        sys.exit(0 if argv else 1)

    sub = argv[0]
    if sub == "ux":
        score_ux_main()
    elif sub == "specific":
        score_specific()
    else:
        # Legacy positional invocation `cli.py <label> [pageType]`.
        score_specific()


if __name__ == "__main__":
    main()
