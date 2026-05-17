"""Elite Mode CLI — ``explore`` subcommand (Issue CR-09 #64).

Mono-concern (CLI axis): argparse → load brief / brand_dna → call
``generate_html_candidates`` → persist via ``save_html_candidates``. Zero
business logic of its own.

Usage::

    set -a; source .env; set +a
    python3 -m moteur_gsg.creative_engine.elite.cli explore \\
        --client weglot --page lp_listicle --candidates 3

    # With opt-in creative reference (anti-mimicry: max 1):
    python3 -m moteur_gsg.creative_engine.elite.cli explore \\
        --client weglot --page lp_listicle --candidates 3 \\
        --creative-reference orbital

    # Fallback Opus model (task stop condition #18):
    python3 -m moteur_gsg.creative_engine.elite.cli explore \\
        --client weglot --page lp_listicle \\
        --opus-model claude-opus-4-1

Exit codes
----------
* ``0`` — batch generated + persisted OK.
* ``1`` — business error: brief missing, invalid arguments (--candidates
  out of 1..3, multiple --creative-reference, EliteCreativeError).
* ``2`` — internal error (uncaught exception).

Critical note: imports ``growthcro.config`` first to load .env BEFORE the
Anthropic SDK init (lesson Sprint P1 #53 — env load discipline).
"""
from __future__ import annotations

# CRITICAL: load .env early before any anthropic SDK init.
# Lesson Sprint P1 #53 — every entry script must import config first.
import growthcro.config  # noqa: F401

import argparse
import json
import pathlib
import sys
import traceback
from typing import Any

from growthcro.models.elite_models import EliteCreativeError
from growthcro.observability.logger import get_logger
from moteur_gsg.creative_engine.elite.orchestrator import (
    OPUS_MODEL,
    generate_html_candidates,
)
from moteur_gsg.creative_engine.elite.persist import save_html_candidates

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[3]
_BRIEFS_DIR = "data/_briefs_v2"
_CAPTURES_DIR = "data/captures"
_CLIENTS_DB = "data/clients_database.json"


# ─────────────────────────────────────────────────────────────────────────────
# Brief / brand_dna / business_category loading (same convention as CR-01 CLI)
# ─────────────────────────────────────────────────────────────────────────────


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _find_brief(client: str, page: str, root: pathlib.Path) -> pathlib.Path:
    """Resolve brief V2 path: canonical first, fallback latest in _briefs_v2."""
    canonical = root / _CAPTURES_DIR / client / page / "brief_v2.json"
    if canonical.is_file():
        return canonical
    briefs_dir = root / _BRIEFS_DIR
    if briefs_dir.is_dir():
        candidates = sorted(
            briefs_dir.glob(f"*{client}*{page}*.json"),
            reverse=True,
        )
        if candidates:
            return candidates[0]
    raise FileNotFoundError(
        f"no brief_v2 found for {client}/{page} "
        f"(checked {canonical} and {briefs_dir}/*{client}*{page}*.json)"
    )


def _load_brand_dna(client: str, root: pathlib.Path) -> dict[str, Any]:
    path = root / _CAPTURES_DIR / client / "brand_dna.json"
    if not path.is_file():
        logger.warning(
            "elite.cli.brand_dna_missing",
            extra={"client": client, "expected_path": str(path)},
        )
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_business_category(
    explicit: str | None,
    brief: dict[str, Any],
    client: str,
    root: pathlib.Path,
) -> str:
    """Resolve from CLI arg → brief → clients_database.json → default 'saas'."""
    if explicit:
        return explicit
    if (bc := brief.get("business_category")):
        return str(bc)
    db_path = root / _CLIENTS_DB
    if db_path.is_file():
        try:
            db = json.loads(db_path.read_text(encoding="utf-8"))
            entry = db.get(client) or {}
            if (bc := entry.get("business_category")):
                return str(bc)
        except json.JSONDecodeError:
            pass
    return "saas"


# ─────────────────────────────────────────────────────────────────────────────
# argparse + dispatch
# ─────────────────────────────────────────────────────────────────────────────


def _add_explore_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--client", required=True, help="Client slug (e.g. weglot)")
    p.add_argument("--page", required=True, help="Page type (e.g. lp_listicle)")
    p.add_argument(
        "--candidates",
        default=3,
        type=int,
        help="Number of Opus candidates (1..3, default 3)",
    )
    p.add_argument(
        "--creative-reference",
        action="append",
        default=None,
        help=(
            "Opt-in reference preset name (looked up under "
            "elite/references/<name>.html). Max 1 (anti-patchwork per Codex "
            "correction #4). Can be omitted entirely."
        ),
    )
    p.add_argument(
        "--business-category",
        default=None,
        help="Override business_category (one of 12 Literal verticals).",
    )
    p.add_argument(
        "--opus-model",
        default=OPUS_MODEL,
        help=(
            f"Opus model id (default {OPUS_MODEL}). Use 'claude-opus-4-1' "
            "as fallback if primary 404s (task stop condition #18)."
        ),
    )
    p.add_argument(
        "--root",
        default=None,
        help="Override repo root (test sandboxing). Defaults to repo root.",
    )


def _run_explore(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root) if args.root else _DEFAULT_ROOT

    # ── argument validation at CLI boundary (cheap fail-fast) ────────────
    if args.candidates < 1 or args.candidates > 3:
        print(
            f"ERROR: --candidates must be in 1..3, got {args.candidates}",
            file=sys.stderr,
        )
        return 1
    if args.creative_reference is not None and len(args.creative_reference) > 1:
        print(
            f"ERROR: --creative-reference can be passed at most once "
            f"(anti-patchwork per Codex correction #4), "
            f"got {len(args.creative_reference)}: {args.creative_reference}",
            file=sys.stderr,
        )
        return 1

    try:
        brief_path = _find_brief(args.client, args.page, root)
        brief = _load_json(brief_path)
        brand_dna = _load_brand_dna(args.client, root)
        business_category = _resolve_business_category(
            args.business_category, brief, args.client, root
        )

        batch = generate_html_candidates(
            brief=brief,
            brand_dna=brand_dna,
            page_type=args.page,
            business_category=business_category,  # type: ignore[arg-type]
            client_slug=args.client,
            n_candidates=args.candidates,
            references=args.creative_reference,
            opus_model=args.opus_model,
        )
        out_dir = save_html_candidates(batch, root=root)

        pm = batch.prompt_meta
        print(
            f"OK: {len(batch.candidates)} HTML candidate(s) written to {out_dir}\n"
            f"  brief: {brief_path.name}\n"
            f"  business_category: {business_category}\n"
            f"  opus_model: {pm.get('model')}\n"
            f"  wall_seconds_batch: {pm.get('wall_seconds_batch')}\n"
            f"  extraction_failures: {pm.get('extraction_failures', 0)}\n"
            f"  candidate_ids: {[c.candidate_id for c in batch.candidates]}"
        )
        return 0
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except EliteCreativeError as exc:
        print(
            f"ERROR (elite): {exc}\nupstream: {exc.upstream_error}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"ERROR (validation): {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="moteur_gsg.creative_engine.elite",
        description=(
            "Elite Mode (Opus Unleashed direct-to-HTML) — Opus 4.7 produces "
            "1-3 complete HTML LP candidates from brief V2 + brand DNA. "
            "Persists to data/captures/<client>/<page>/elite_candidates/."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")
    explore = sub.add_parser("explore", help="Generate HTML candidates for one page")
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
