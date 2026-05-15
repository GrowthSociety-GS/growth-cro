"""V30 Reality Layer poller — orchestrates (client × connector × metric) (Task 011).

Single concern : iterate over the (client × connector × metric) grid, call
`fetch_snapshot_for`, insert into Supabase `reality_snapshots`. Driven by the
worker daemon via `dispatch.py` ('reality' run type) OR by the Vercel cron
endpoint via `runs` insert.

Defensive everywhere :
  - No Supabase config → poller logs + exits 0 (no rows inserted, no crash).
  - No `client_credentials` row for a (client, connector) pair → connector
    receives `access_token=None` and returns `skipped=True`. Poller logs and
    moves on.
  - Connector API failure → snapshot skipped, error logged, never re-raised.

CLI :
    python -m growthcro.reality.poller --client <slug>
    python -m growthcro.reality.poller --all
    python -m growthcro.reality.poller --client <slug> --dry-run

Programmatic :
    from growthcro.reality.poller import fetch_for_pair
    r = fetch_for_pair("weglot", "catchr", "cvr")
    # SnapshotResult(skipped=True, reason='not_connected') when no creds
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional

from growthcro.observability.logger import get_logger, set_correlation_id, set_pipeline_name
from growthcro.reality.connectors import (
    ClientCredential,
    REALITY_CONNECTORS,
    REALITY_METRICS,
    SnapshotResult,
    fetch_snapshot_for,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class PollerStats:
    """Counts emitted by one poller run."""

    pairs_tried: int
    snapshots_written: int
    skipped_not_connected: int
    skipped_api_error: int
    skipped_other: int


def fetch_for_pair(
    client_slug: str,
    connector: str,
    metric: str,
    *,
    cred: Optional[ClientCredential] = None,
) -> SnapshotResult:
    """Public helper — fetch one snapshot for a (client, connector, metric).

    Returns SnapshotResult. When `cred` is None, a defensive placeholder with
    `access_token=None` is used → returns `skipped=True, reason='not_connected'`.
    This is what the post-build sanity check exercises.
    """
    if cred is None:
        cred = ClientCredential(
            client_id="",
            client_slug=client_slug,
            org_id="",
            connector=connector,
        )
    return fetch_snapshot_for(connector, cred, metric)


def _load_credentials(client_slug: Optional[str]) -> list[ClientCredential]:
    """Read `client_credentials` from Supabase, decrypted in-DB.

    Defensive : returns `[]` on any Supabase or auth error. Caller treats
    empty as "no work to do" — no exceptions propagated.
    """
    try:
        from supabase import create_client  # type: ignore
    except ImportError:
        logger.info("poller_skip", extra={"reason": "supabase_sdk_not_installed"})
        return []

    from growthcro.config import config
    url = config.system_env("NEXT_PUBLIC_SUPABASE_URL") or config.system_env("SUPABASE_URL")
    key = config.system_env("SUPABASE_SECRET_KEY") or config.system_env("SUPABASE_SERVICE_ROLE_KEY")
    enc_key = config.reality_token_encryption_key()
    if not url or not key:
        logger.info("poller_skip", extra={"reason": "missing_supabase_config"})
        return []
    if not enc_key:
        logger.info("poller_skip", extra={"reason": "missing_token_encryption_key"})
        return []

    try:
        sb = create_client(url, key)
        # Set the pgcrypto session key (postgres GUC) for reality_decrypt().
        sb.rpc("set_config", {"setting_name": "app.reality_token_key", "new_value": enc_key, "is_local": False}).execute()
        # Pull credentials. Join clients table to get slug.
        q = sb.table("client_credentials").select(
            "id, client_id, org_id, connector, expires_at, scope, connector_account_id, "
            "access_token_decrypted:reality_decrypt(access_token_encrypted), "
            "refresh_token_decrypted:reality_decrypt(refresh_token_encrypted), "
            "client:clients(slug)"
        )
        if client_slug:
            # Filter by slug — Supabase doesn't support filtering by joined
            # field directly via .eq(), so we fetch all then filter in-memory.
            # Defensive : with ~100 clients × 5 connectors = ~500 rows max.
            pass
        data = q.execute()
        rows = data.data or []
    except Exception as e:  # noqa: BLE001
        logger.info("poller_supabase_error", extra={"error": str(e)[:200]})
        return []

    out: list[ClientCredential] = []
    for row in rows:
        client_obj = row.get("client") if isinstance(row, dict) else None
        slug = (client_obj or {}).get("slug") if isinstance(client_obj, dict) else None
        if not slug:
            continue
        if client_slug and slug != client_slug:
            continue
        out.append(
            ClientCredential(
                client_id=row.get("client_id", ""),
                client_slug=slug,
                org_id=row.get("org_id", ""),
                connector=row.get("connector", ""),
                access_token=row.get("access_token_decrypted"),
                refresh_token=row.get("refresh_token_decrypted"),
                connector_account_id=row.get("connector_account_id"),
                expires_at=row.get("expires_at"),
            )
        )
    return out


def _insert_snapshot(
    cred: ClientCredential,
    metric: str,
    result: SnapshotResult,
) -> bool:
    """Write one `reality_snapshots` row. Returns True iff inserted."""
    if result.skipped or result.value is None:
        return False
    try:
        from supabase import create_client  # type: ignore
    except ImportError:
        return False

    from growthcro.config import config
    url = config.system_env("NEXT_PUBLIC_SUPABASE_URL") or config.system_env("SUPABASE_URL")
    key = config.system_env("SUPABASE_SECRET_KEY") or config.system_env("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return False

    try:
        sb = create_client(url, key)
        sb.table("reality_snapshots").insert({
            "client_id": cred.client_id,
            "org_id": cred.org_id,
            "connector": cred.connector,
            "metric": metric,
            "value": result.value,
            "raw_response_json": result.raw_response or {},
        }).execute()
        return True
    except Exception as e:  # noqa: BLE001
        logger.info(
            "poller_insert_failed",
            extra={"client": cred.client_slug, "connector": cred.connector, "metric": metric, "error": str(e)[:200]},
        )
        return False


def run_poller(
    client_slug: Optional[str] = None,
    *,
    dry_run: bool = False,
) -> PollerStats:
    """Iterate (cred × metric), fetch + insert.

    When `client_slug` is None, polls every credentialed client. With
    `dry_run=True`, no rows are inserted — useful for `--dry-run` smoke tests.
    """
    set_correlation_id()
    set_pipeline_name("reality.poller")
    creds = _load_credentials(client_slug)
    if not creds:
        logger.info(
            "poller_no_credentials",
            extra={"client_filter": client_slug, "dry_run": dry_run},
        )
        return PollerStats(0, 0, 0, 0, 0)

    pairs = 0
    written = 0
    skip_nc = 0
    skip_ae = 0
    skip_other = 0

    for cred in creds:
        for metric in REALITY_METRICS:
            pairs += 1
            try:
                result = fetch_snapshot_for(cred.connector, cred, metric)
            except Exception as e:  # noqa: BLE001
                # Hard belt-and-braces — connector must never raise but we
                # protect the poller loop just in case.
                logger.warning(
                    "poller_connector_raised",
                    extra={"client": cred.client_slug, "connector": cred.connector, "metric": metric, "error": str(e)[:200]},
                )
                skip_other += 1
                continue

            if result.skipped:
                if result.reason == "not_connected":
                    skip_nc += 1
                elif result.reason == "api_error":
                    skip_ae += 1
                else:
                    skip_other += 1
                continue

            if dry_run:
                logger.info(
                    "poller_dry_run_snapshot",
                    extra={"client": cred.client_slug, "connector": cred.connector, "metric": metric, "value": result.value},
                )
                continue

            if _insert_snapshot(cred, metric, result):
                written += 1

    logger.info(
        "poller_done",
        extra={
            "client_filter": client_slug,
            "pairs_tried": pairs,
            "snapshots_written": written,
            "skipped_not_connected": skip_nc,
            "skipped_api_error": skip_ae,
            "skipped_other": skip_other,
            "dry_run": dry_run,
        },
    )
    return PollerStats(pairs, written, skip_nc, skip_ae, skip_other)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--client", help="Client slug (e.g. weglot) to poll. Defaults to all.")
    g.add_argument("--all", action="store_true", help="Poll every credentialed client.")
    ap.add_argument("--dry-run", action="store_true", help="Skip Supabase inserts.")
    args = ap.parse_args(argv)

    slug: Optional[str] = args.client if args.client else None
    stats = run_poller(slug, dry_run=args.dry_run)

    # Always exit 0 — the poller is best-effort. Caller observes stats via logs.
    _ = stats
    return 0


if __name__ == "__main__":
    sys.exit(main())
