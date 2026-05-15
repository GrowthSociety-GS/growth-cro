"""V30 OAuth-token Reality Layer connectors (Task 011).

Each module exports `fetch_snapshot(client_credential, metric) -> SnapshotResult`
— pulls one metric from a connector's REST API using an OAuth access_token
stored in Supabase `client_credentials`. Defensive : every connector returns
`SnapshotResult(skipped=True, reason='not_connected')` when the access_token
is missing, and `reason='api_error'` on any HTTP/parsing failure.

Naming : the per-connector files use a `_v30` basename suffix to disambiguate
from the V26.C env-driven connectors that live alongside in
`growthcro/reality/{catchr,meta_ads,…}.py`. The V26.C path writes rich per-page
JSON snapshots ; the V30 path writes per-metric time-series rows to Supabase
`reality_snapshots`.

Public API
----------
    from growthcro.reality.connectors import SnapshotResult, ClientCredential
    from growthcro.reality.connectors import fetch_snapshot_for

    result = fetch_snapshot_for("catchr", cred, "cvr")
    # SnapshotResult(skipped=True, reason='not_connected') when cred.access_token is None
"""
from __future__ import annotations

from growthcro.reality.connectors.types import (
    ClientCredential,
    SnapshotResult,
    REALITY_CONNECTORS,
    REALITY_METRICS,
)
from growthcro.reality.connectors.dispatch import fetch_snapshot_for

__all__ = (
    "ClientCredential",
    "SnapshotResult",
    "REALITY_CONNECTORS",
    "REALITY_METRICS",
    "fetch_snapshot_for",
)
