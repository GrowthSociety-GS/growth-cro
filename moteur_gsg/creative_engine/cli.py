"""Creative Exploration Engine CLI — single ``explore`` subcommand (Issue #56).

Mono-concern (CLI axis): argparse → load brief / brand_dna / grammar → call
``explore_routes`` → persist via ``save_creative_routes``. Zero business
logic of its own.

Usage::

    python3 -m moteur_gsg.creative_engine.cli explore \\
        --client weglot --page lp_listicle [--business-category saas]

Exit codes
----------
* ``0`` — batch generated + persisted OK.
* ``1`` — business error: brief missing, page directory missing, invalid
  arguments, ``CreativeEngineError`` (Opus + retry both failed).
* ``2`` — internal error (uncaught exception).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import traceback
from typing import Any

from growthcro.observability.logger import get_logger
from moteur_gsg.creative_engine.orchestrator import (
    CreativeEngineError,
    explore_routes,
)
from moteur_gsg.creative_engine.persist import save_creative_routes

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
_BRIEFS_DIR = "data/_briefs_v2"
_CAPTURES_DIR = "data/captures"


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    """Load a JSON file; raise FileNotFoundError if absent, ValueError if malformed."""
    if not path.is_file():
        raise FileNotFoundError(f"missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _find_brief(client: str, page: str, root: pathlib.Path) -> pathlib.Path:
    """Resolve the brief V2 file.

    Strategy:
    1. Look for ``data/captures/<client>/<page>/brief_v2.json`` (canonical).
    2. Fallback to the most recent ``data/_briefs_v2/*<client>*<page>*.json``.

    Raises ``FileNotFoundError`` if neither resolves.
    """
    canonical = root / _CAPTURES_DIR / client / page / "brief_v2.json"
    if canonical.is_file():
        return canonical
    briefs_dir = root / _BRIEFS_DIR
    if briefs_dir.is_dir():
        candidates = sorted(
            briefs_dir.glob(f"*{client}*{page}*.json"),
            reverse=True,  # newest first by lexicographic timestamp prefix
        )
        if candidates:
            return candidates[0]
    raise FileNotFoundError(
        f"no brief_v2 found for {client}/{page} "
        f"(checked {canonical} and {briefs_dir}/*{client}*{page}*.json)"
    )


def _load_brand_dna(client: str, root: pathlib.Path) -> dict[str, Any]:
    """Load brand_dna.json; return empty dict if absent (stub mode)."""
    path = root / _CAPTURES_DIR / client / "brand_dna.json"
    if not path.is_file():
        logger.warning(
            "creative_engine.cli.brand_dna_missing",
            extra={"client": client, "expected_path": str(path)},
        )
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_design_grammar(client: str, root: pathlib.Path) -> dict[str, Any]:
    """Load a compact design_grammar summary; return empty dict if absent."""
    grammar_dir = root / _CAPTURES_DIR / client / "design_grammar"
    if not grammar_dir.is_dir():
        return {}
    # We surface the small/typed JSONs only; full grammar can be 30+ KB.
    summary: dict[str, Any] = {}
    for fname in ("tokens.json", "composition_rules.json"):
        path = grammar_dir / fname
        if path.is_file():
            try:
                summary[fname.replace(".json", "")] = json.loads(
                    path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError:
                continue
    return summary


def _resolve_business_category(
    explicit: str | None,
    brief: dict[str, Any],
) -> str:
    """Resolve business_category from CLI arg → brief.business_category → default 'saas'.

    Returns a string; the Pydantic Literal validator at the boundary catches typos.
    """
    if explicit:
        return explicit
    if (bc := brief.get("business_category")):
        return str(bc)
    return "saas"


def _add_explore_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--client", required=True, help="Client slug (e.g. weglot)")
    p.add_argument("--page", required=True, help="Page type (e.g. lp_listicle)")
    p.add_argument(
        "--business-category",
        default=None,
        help=(
            "Override business_category (one of the 12 Literal verticals). "
            "Defaults to brief.business_category, then to 'saas'."
        ),
    )
    p.add_argument(
        "--root",
        default=None,
        help="Override repo root (test sandboxing). Defaults to repo root.",
    )


def _run_explore(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root) if args.root else _DEFAULT_ROOT
    try:
        brief_path = _find_brief(args.client, args.page, root)
        brief = _load_json(brief_path)
        brand_dna = _load_brand_dna(args.client, root)
        grammar = _load_design_grammar(args.client, root)
        business_category = _resolve_business_category(args.business_category, brief)

        batch = explore_routes(
            brief=brief,
            brand_dna=brand_dna,
            design_grammar=grammar,
            page_type=args.page,
            business_category=business_category,  # type: ignore[arg-type]
            client_slug=args.client,
        )
        out_path = save_creative_routes(batch, root=root)
        print(
            f"OK: {len(batch.routes)} routes written to {out_path} "
            f"(brief={brief_path.name}, retry={batch.prompt_meta.get('retry_used')})"
        )
        return 0
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except CreativeEngineError as exc:
        print(
            f"ERROR (creative_engine): {exc}\nupstream: {exc.upstream}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"ERROR (validation): {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="moteur_gsg.creative_engine",
        description=(
            "Creative Exploration Engine — call Opus 4.7 for 3-5 creative "
            "directions, persist to data/captures/<client>/<page>/creative_routes.json."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")
    explore = sub.add_parser("explore", help="Generate creative routes for one page")
    _add_explore_args(explore)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.cmd == "explore":
        try:
            return _run_explore(args)
        except Exception:  # noqa: BLE001 — top-level safety net
            traceback.print_exc()
            return 2
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
