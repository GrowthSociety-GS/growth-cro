"""Shared types for the V30 OAuth Reality Layer connectors (Task 011).

Single concern : dataclass surface + connector/metric enum literals. No I/O,
no HTTP, no env reads. Pure type module — kept small so each connector can
import the surface without circular deps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# Source of truth — must mirror migration 20260514_0023 CHECK constraints +
# webapp `reality-types.ts` REALITY_CONNECTORS.
REALITY_CONNECTORS: tuple[str, ...] = (
    "catchr",
    "meta_ads",
    "google_ads",
    "shopify",
    "clarity",
)

REALITY_METRICS: tuple[str, ...] = (
    "cvr",
    "cpa",
    "aov",
    "traffic",
    "impressions",
)


@dataclass(frozen=True)
class ClientCredential:
    """One row from Supabase `client_credentials`, projected for connector use.

    The access_token is **already decrypted** at the call site (by the poller,
    via pgcrypto `reality_decrypt`). Connectors NEVER see the encrypted form.
    Defensive : when the credential row doesn't exist for a (client, connector)
    pair, the poller passes `access_token=None` and each connector returns a
    skipped SnapshotResult.
    """

    client_id: str
    client_slug: str
    org_id: str
    connector: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    connector_account_id: Optional[str] = None
    expires_at: Optional[str] = None  # ISO timestamp


@dataclass(frozen=True)
class SnapshotResult:
    """Outcome of one `fetch_snapshot(cred, metric)` call.

    Discriminated by `skipped` :
      - skipped=True  → row NOT written to Supabase. `reason` ∈ {'not_connected',
        'api_error', 'token_expired', 'not_supported'}. `error_text` carries
        the upstream message when reason='api_error'.
      - skipped=False → row WRITTEN with `value` + `raw_response_json`.
    """

    skipped: bool
    reason: Optional[str] = None
    value: Optional[float] = None
    raw_response: Optional[dict[str, Any]] = None
    error_text: Optional[str] = None
