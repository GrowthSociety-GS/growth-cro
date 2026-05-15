"""GEO Monitor CLI — `python -m growthcro.geo`.

Mono-concern : CLI argparse + loop. Loads the 20-query bank, executes each
(client × engine × query) probe via `growthcro.geo.runner.run_engine`, and
emits one JSON line per probe to stdout (subprocess-parser friendly).

Persistence to Supabase is deliberately NOT done here yet — the daemon /
worker can ingest the stdout lines, or a follow-up sub-task can wire
`supabase-py` (currently not a Python runtime dep). Day-1 acceptance is :
the CLI runs cleanly with no keys, prints one `{"skipped": true}` row per
(engine × query), and exits 0.

Usage :
    python -m growthcro.geo --client weglot --engines anthropic --limit 1
    python -m growthcro.geo --client weglot --engines anthropic,openai,perplexity --limit 5
    python -m growthcro.geo --client weglot --engine all --limit 5  (legacy single-engine arg)

The --engine / --engines flags both accepted to match the dispatcher's
RUN_TYPE_TO_CLI which currently passes `--engine`. We default --engines to
"anthropic,openai,perplexity" so a bare invocation probes the full row.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from growthcro.geo.engine_runner import SUPPORTED_ENGINES, EngineName, RunResult, run_engine
from growthcro.observability.logger import get_logger, set_correlation_id, set_pipeline_name

REPO_ROOT = Path(__file__).resolve().parents[2]
QUERY_BANK_PATH = REPO_ROOT / "data" / "geo_query_bank.json"

logger = get_logger(__name__)


def _parse_engines(arg: str) -> list[EngineName]:
    raw = (arg or "").strip().lower()
    if not raw or raw == "all":
        return list(SUPPORTED_ENGINES)
    out: list[EngineName] = []
    for piece in raw.split(","):
        name = piece.strip()
        if not name:
            continue
        if name not in SUPPORTED_ENGINES:
            raise SystemExit(
                f"unknown engine {name!r} ; valid={','.join(SUPPORTED_ENGINES)} or 'all'",
            )
        out.append(name)  # type: ignore[arg-type]
    return out or list(SUPPORTED_ENGINES)


def _load_query_bank(limit: int) -> list[dict[str, str]]:
    if not QUERY_BANK_PATH.is_file():
        return []
    try:
        raw = json.loads(QUERY_BANK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    queries = raw.get("queries") if isinstance(raw, dict) else None
    if not isinstance(queries, list):
        return []
    cleaned: list[dict[str, str]] = []
    for q in queries:
        if not isinstance(q, dict):
            continue
        text = q.get("query_text")
        qid = q.get("id")
        if not (isinstance(text, str) and isinstance(qid, str)):
            continue
        cleaned.append(
            {
                "id": qid,
                "query_text": text,
                "business_category": str(q.get("business_category") or ""),
                "intent": str(q.get("intent") or ""),
            }
        )
        if limit > 0 and len(cleaned) >= limit:
            break
    return cleaned


def _emit(result: RunResult, client: str, query_id: str) -> None:
    payload = result.to_dict()
    payload["client"] = client
    payload["query_id"] = query_id
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m growthcro.geo",
        description="GEO Monitor — probe ChatGPT / Claude / Perplexity for brand presence.",
    )
    parser.add_argument("--client", required=True, help="Client slug (e.g. weglot).")
    parser.add_argument(
        "--brand",
        default=None,
        help="Brand name passed to the scorer ; defaults to client slug if unset.",
    )
    parser.add_argument(
        "--keywords",
        default="",
        help="Comma-separated brand keywords, e.g. 'translation,localization'.",
    )
    parser.add_argument(
        "--engines",
        default="all",
        help="Comma list of engines (anthropic,openai,perplexity) or 'all'.",
    )
    parser.add_argument(
        "--engine",
        default=None,
        help="Legacy alias for --engines (single engine name or 'all').",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Max queries to run from the bank (0 = all 20).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    set_pipeline_name("geo")
    set_correlation_id()

    engine_arg = args.engine if args.engine else args.engines
    engines = _parse_engines(engine_arg)
    queries = _load_query_bank(args.limit)
    if not queries:
        logger.warning("geo.cli no_queries_loaded", extra={"path": str(QUERY_BANK_PATH)})
    brand = args.brand or args.client
    keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]

    logger.info(
        "geo.cli start",
        extra={
            "client": args.client,
            "engines": engines,
            "n_queries": len(queries),
            "brand": brand,
            "n_keywords": len(keywords),
        },
    )

    n_ok = 0
    n_skipped = 0
    n_error = 0
    for q in queries:
        for engine in engines:
            result = run_engine(engine, q["query_text"], brand, keywords)
            _emit(result, args.client, q["id"])
            if result.skipped:
                n_skipped += 1
            elif result.error:
                n_error += 1
            else:
                n_ok += 1

    logger.info(
        "geo.cli end",
        extra={"client": args.client, "ok": n_ok, "skipped": n_skipped, "error": n_error},
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["main"]
