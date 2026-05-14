"""Worker CLI — argparse entrypoint, single concern.

Usage:
    python3 -m growthcro.worker.cli                   # loop forever, poll 30s
    python3 -m growthcro.worker.cli --once            # single iteration (debug)
    python3 -m growthcro.worker.cli --poll-interval 10 --batch-limit 3
"""

from __future__ import annotations

import argparse
import sys

from growthcro.worker.daemon import (
    DEFAULT_BATCH_LIMIT,
    DEFAULT_POLL_INTERVAL,
    main_loop,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GrowthCRO pipeline-trigger worker (Sprint 2 / Task 002 Phase A).",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between queue polls (default: {DEFAULT_POLL_INTERVAL}).",
    )
    parser.add_argument(
        "--batch-limit",
        type=int,
        default=DEFAULT_BATCH_LIMIT,
        help=f"Max pending runs fetched per poll (default: {DEFAULT_BATCH_LIMIT}).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll iteration then exit (debug / CI smoke).",
    )
    args = parser.parse_args(argv)
    return main_loop(
        poll_interval=args.poll_interval,
        batch_limit=args.batch_limit,
        once=args.once,
    )


if __name__ == "__main__":
    sys.exit(main())
