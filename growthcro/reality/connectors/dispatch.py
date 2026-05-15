"""Connector dispatch — connector name → `fetch_snapshot` function (Task 011).

Single concern : tiny map + dispatcher. Keeps `__init__.py` free of business
logic so importing `growthcro.reality.connectors` is cheap (~ms cold start).
"""
from __future__ import annotations

from growthcro.reality.connectors.catchr_v30 import fetch_snapshot as _catchr_fetch
from growthcro.reality.connectors.clarity_v30 import fetch_snapshot as _clarity_fetch
from growthcro.reality.connectors.google_ads_v30 import fetch_snapshot as _gads_fetch
from growthcro.reality.connectors.meta_ads_v30 import fetch_snapshot as _meta_fetch
from growthcro.reality.connectors.shopify_v30 import fetch_snapshot as _shopify_fetch
from growthcro.reality.connectors.types import ClientCredential, SnapshotResult

_FETCHERS = {
    "catchr": _catchr_fetch,
    "meta_ads": _meta_fetch,
    "google_ads": _gads_fetch,
    "shopify": _shopify_fetch,
    "clarity": _clarity_fetch,
}


def fetch_snapshot_for(connector: str, cred: ClientCredential, metric: str) -> SnapshotResult:
    """Route to the per-connector `fetch_snapshot`.

    Defensive : unknown connector → SnapshotResult(skipped=True,
    reason='not_supported'). Mismatch between `connector` arg and
    `cred.connector` is tolerated — the explicit arg wins.
    """
    fetcher = _FETCHERS.get(connector)
    if not fetcher:
        return SnapshotResult(skipped=True, reason="not_supported")
    return fetcher(cred, metric)
