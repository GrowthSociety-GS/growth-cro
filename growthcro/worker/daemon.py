"""Worker daemon — poll Supabase `runs` queue + dispatch CLI executions.

Sprint 2 / Task 002 — Phase A : local Python worker. Phase B = Fly.io migration
(deferred V2). Architecture cf .claude/docs/architecture/DECISIONS_2026-05-14.md.

Flow per iteration :
  1. SELECT * FROM runs WHERE status='pending' ORDER BY created_at LIMIT N
  2. For each pending row :
     a. UPDATE status='running', started_at=now  (claim — racing-safe via
        optimistic concurrency on `status` field)
     b. dispatch_run() invokes the matching CLI
     c. On returncode=0 : UPDATE status='completed', finished_at, output_path
     d. On returncode≠0 : UPDATE status='failed', finished_at, error_message
        (stderr tail), metadata_json.log_tail (stdout tail)
  3. Sleep `--poll-interval` seconds (default 30s)

Graceful shutdown : SIGINT/SIGTERM sets `running=False`, daemon completes the
in-flight run before exiting.

Stdlib + urllib only (no supabase-py / requests dep). Same pattern as
`scripts/migrate_disk_to_supabase.py`.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

# Add repo root to sys.path (single-file invocation safety net).
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from growthcro import config as gc_config  # noqa: E402
from growthcro.models.runs_models import RunRow, RunStatus  # noqa: E402
from growthcro.observability.logger import get_logger, set_correlation_id, set_pipeline_name  # noqa: E402
from growthcro.worker.dispatcher import DispatchResult, dispatch_run  # noqa: E402

logger = get_logger(__name__)
_cfg = gc_config.get_config()

DEFAULT_POLL_INTERVAL = 30
DEFAULT_BATCH_LIMIT = 5
THROTTLE_BETWEEN_RUNS = 1.0  # seconds


# ──────────────────────────────────────────────────────────────────────────
# Supabase REST (PostgREST) thin client — stdlib only
# ──────────────────────────────────────────────────────────────────────────


class SupabaseError(RuntimeError):
    """Wraps any HTTP / network failure from the PostgREST endpoint."""


def _env(name: str, default: str | None = None) -> str | None:
    value = _cfg.system_env(name, default or "")
    return value if value else default


def _request(method: str, path: str, body: Any | None = None, headers: dict[str, str] | None = None) -> Any:
    url_base = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url_base or not key:
        raise SupabaseError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
    full = f"{url_base.rstrip('/')}/rest/v1/{path.lstrip('/')}"
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req_headers = {
        "apikey": key,
        "authorization": f"Bearer {key}",
        "content-type": "application/json",
        "prefer": "return=representation",
        **(headers or {}),
    }
    req = urlrequest.Request(full, data=payload, method=method, headers=req_headers)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SupabaseError(f"HTTP {e.code} {method} {path}: {detail}") from e


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────────
# Run lifecycle — fetch / claim / complete / fail
# ──────────────────────────────────────────────────────────────────────────


def fetch_pending_runs(limit: int) -> list[RunRow]:
    """SELECT pending rows in FIFO order. Returns parsed RunRow models."""
    raw = _request(
        "GET",
        f"runs?status=eq.pending&order=created_at.asc&limit={limit}&select=*",
    )
    return [RunRow.model_validate(r) for r in (raw or [])]


def claim_run(run_id: str) -> bool:
    """Try to atomically transition pending → running. Returns True on success.

    Uses PostgREST `?status=eq.pending` filter on the PATCH so two workers
    racing on the same row only succeed for one. The other gets an empty
    response (no row updated) and skips this run.
    """
    res = _request(
        "PATCH",
        f"runs?id=eq.{run_id}&status=eq.pending",
        body={"status": "running", "started_at": _now_iso()},
    )
    return bool(res) and len(res) > 0


def complete_run(run_id: str, result: DispatchResult) -> None:
    metadata_patch: dict[str, Any] = {
        "stdout_tail": result.stdout_tail,
        "stderr_tail": result.stderr_tail,
        "duration_sec": round(result.duration_sec, 2),
        "returncode": result.returncode,
    }
    _request(
        "PATCH",
        f"runs?id=eq.{run_id}",
        body={
            "status": "completed",
            "finished_at": _now_iso(),
            "output_path": result.output_path,
            "metadata_json": metadata_patch,
            "progress_pct": 100,
        },
    )


def fail_run(run_id: str, result: DispatchResult | None, error: str) -> None:
    metadata_patch: dict[str, Any] = {}
    if result is not None:
        metadata_patch.update({
            "stdout_tail": result.stdout_tail,
            "stderr_tail": result.stderr_tail,
            "duration_sec": round(result.duration_sec, 2),
            "returncode": result.returncode,
        })
    _request(
        "PATCH",
        f"runs?id=eq.{run_id}",
        body={
            "status": "failed",
            "finished_at": _now_iso(),
            "error_message": error[:2000],
            "metadata_json": metadata_patch,
        },
    )


# ──────────────────────────────────────────────────────────────────────────
# Main poll loop
# ──────────────────────────────────────────────────────────────────────────


def process_one_run(run: RunRow) -> None:
    """Claim + dispatch + complete/fail a single run."""
    set_correlation_id(run.id[:12])
    set_pipeline_name(f"worker-{run.type}")
    logger.info("processing run", extra={"run_id": run.id, "type": run.type, "client_id": run.client_id})

    if not claim_run(run.id):
        logger.info("run already claimed by another worker", extra={"run_id": run.id})
        return

    try:
        result = dispatch_run(run.type, run.metadata_json or {})
        if result.returncode == 0:
            complete_run(run.id, result)
            logger.info(
                "run completed",
                extra={"run_id": run.id, "duration_sec": result.duration_sec},
            )
        else:
            fail_run(
                run.id,
                result,
                f"CLI exited with code {result.returncode}: {result.stderr_tail[-500:]}",
            )
            logger.warning(
                "run failed (non-zero exit)",
                extra={"run_id": run.id, "returncode": result.returncode},
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("run dispatch raised", extra={"run_id": run.id})
        try:
            fail_run(run.id, None, f"worker exception: {exc!r}")
        except SupabaseError:
            logger.error("failed to write fail status back to Supabase", extra={"run_id": run.id})


def main_loop(
    *,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    batch_limit: int = DEFAULT_BATCH_LIMIT,
    once: bool = False,
) -> int:
    """Daemon entry. SIGINT/SIGTERM → graceful exit after current run."""
    running = {"state": True}

    def shutdown(signum: int, _frame: Any) -> None:
        logger.info("shutdown signal received", extra={"signum": signum})
        running["state"] = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info(
        "worker daemon started",
        extra={"poll_interval": poll_interval, "batch_limit": batch_limit, "once": once},
    )

    iterations = 0
    while running["state"]:
        iterations += 1
        try:
            pending = fetch_pending_runs(limit=batch_limit)
        except SupabaseError as exc:
            logger.error("fetch_pending_runs failed", extra={"err": str(exc)})
            time.sleep(poll_interval)
            continue
        except Exception:  # noqa: BLE001
            logger.exception("fetch_pending_runs unexpected error")
            time.sleep(poll_interval)
            continue

        if not pending:
            logger.debug("no pending runs", extra={"iteration": iterations})
        for run in pending:
            if not running["state"]:
                break
            process_one_run(run)
            time.sleep(THROTTLE_BETWEEN_RUNS)

        if once:
            break
        if running["state"]:
            time.sleep(poll_interval)

    logger.info("worker daemon stopped", extra={"iterations": iterations})
    return 0
