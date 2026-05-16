"""Opportunity Layer CLI — generate ``opportunities.json`` per (client, page).

Mono-concern (CLI axis): argparse → orchestrator → persist. Zero business
logic of its own — every decision lives in
``growthcro.opportunities.orchestrator`` (deterministic generation) and
``growthcro.opportunities.persist`` (atomic on-disk write).

Three modes for ``prepare``:

* ``--client <slug> --page <page>`` — single page
* ``--client <slug>``                — every page under
  ``data/captures/<slug>/*/`` that has a ``score_page_type.json``
* ``--all``                          — every client under
  ``data/captures/*/`` that has at least one scoreable page

Exit codes:

* ``0`` — every targeted page produced its batch
* ``1`` — at least one page failed (missing scoring artefact, doctrine
  mismatch, Pydantic validation error) OR no targets resolved
* ``2`` — internal error (uncaught exception)
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import traceback

from growthcro.observability.logger import get_logger
from growthcro.opportunities.orchestrator import generate_opportunities
from growthcro.opportunities.persist import save_opportunities

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
_REQUIRED_SCORE_FILE = "score_page_type.json"


def _iter_pages_for_client(client_slug: str, root: pathlib.Path) -> list[str]:
    client_dir = root / "data" / "captures" / client_slug
    if not client_dir.is_dir():
        return []
    return sorted(
        e.name for e in client_dir.iterdir()
        if e.is_dir() and (e / _REQUIRED_SCORE_FILE).is_file()
    )


def _iter_clients(root: pathlib.Path) -> list[str]:
    captures_dir = root / "data" / "captures"
    if not captures_dir.is_dir():
        return []
    return sorted(
        e.name for e in captures_dir.iterdir()
        if e.is_dir() and _iter_pages_for_client(e.name, root)
    )


def _resolve_targets(args: argparse.Namespace, root: pathlib.Path) -> list[tuple[str, str]]:
    """Translate CLI flags to a flat ``[(client, page), ...]`` plan."""
    if args.all:
        return [
            (c, p) for c in _iter_clients(root) for p in _iter_pages_for_client(c, root)
        ]
    if args.client and args.page:
        return [(args.client, args.page)]
    if args.client:
        return [(args.client, p) for p in _iter_pages_for_client(args.client, root)]
    return []


def _prepare_one(client: str, page: str, root: pathlib.Path) -> tuple[bool, int, str | None]:
    """Generate + persist one batch. Returns ``(ok, count, error)``."""
    try:
        batch = generate_opportunities(client, page, root=root)
        save_opportunities(batch, root=root)
    except (FileNotFoundError, ValueError) as exc:
        logger.error(
            "opportunities.cli.page_failed",
            extra={
                "client_slug": client,
                "page_type": page,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        return False, 0, str(exc)
    return True, len(batch.opportunities), None


def _run_prepare(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve() if args.root else _DEFAULT_ROOT

    targets = _resolve_targets(args, root)
    if not targets:
        print(
            "no targets resolved — pass --all, --client <slug> [--page <type>]",
            file=sys.stderr,
        )
        return 1

    results = [_prepare_one(c, p, root) for c, p in targets]
    ok_count = sum(1 for ok, _, _ in results if ok)
    fail_count = len(results) - ok_count
    total_opps = sum(n for ok, n, _ in results if ok)

    logger.info(
        "opportunities.cli.summary",
        extra={
            "pages_total": len(results),
            "pages_ok": ok_count,
            "pages_failed": fail_count,
            "opportunities_total": total_opps,
        },
    )
    print(
        f"opportunities prepare: {ok_count}/{len(results)} pages OK, "
        f"{total_opps} opportunities written"
        + (f", {fail_count} failed" if fail_count else ""),
        file=sys.stderr,
    )
    return 0 if fail_count == 0 else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="growthcro.opportunities",
        description=(
            "Generate opportunities.json per (client, page) pair from "
            "scoring artefacts (deterministic, 0 LLM call)."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")
    prep = sub.add_parser("prepare", help="Generate opportunities.json for one/many pages")
    prep.add_argument("--client", help="Client slug (e.g. weglot)")
    prep.add_argument("--page", help="Page type (e.g. home, lp_listicle)")
    prep.add_argument("--all", action="store_true",
                      help="Iterate every client/page with a scoreable capture")
    prep.add_argument("--root", help="Repo root override (defaults to package root)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if args.cmd == "prepare":
        try:
            return _run_prepare(args)
        except Exception as exc:  # noqa: BLE001 — surface as process exit 2
            logger.error(
                "opportunities.cli.internal_error",
                extra={"error": str(exc), "trace": traceback.format_exc()},
            )
            print(f"internal error: {exc}", file=sys.stderr)
            return 2

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
