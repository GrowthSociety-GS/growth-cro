"""Catchr V30 OAuth snapshot connector (Task 011).

Single concern : one HTTP GET against Catchr's metrics endpoint, projected
into a `SnapshotResult` for a (client_credential, metric) pair.

Defensive : `access_token=None` → SnapshotResult(skipped=True,
reason='not_connected'). HTTP error → reason='api_error'.

API reference : https://api.catchr.io/v1/metrics  (agency-side aggregator
covering Meta Ads spend + revenue + CVR + AOV for Growth Society clients).
The Task 011 spec calls this connector "Catchr (Meta Ads agency-side)".
"""
from __future__ import annotations

from typing import Optional

from growthcro.observability.logger import get_logger
from growthcro.reality.connectors.http_helper import http_get_json
from growthcro.reality.connectors.types import ClientCredential, SnapshotResult

logger = get_logger(__name__)

CATCHR_API_BASE = "https://api.catchr.io/v1"

# Metric → Catchr-API metric-key. Catchr aggregates GA4 + Meta Ads + Shopify
# under the canonical names below — if a future Catchr version changes them,
# update here only.
METRIC_MAP: dict[str, str] = {
    "cvr": "conversion_rate",
    "cpa": "cost_per_acquisition",
    "aov": "average_order_value",
    "traffic": "sessions",
    "impressions": "impressions",
}


def fetch_snapshot(cred: ClientCredential, metric: str) -> SnapshotResult:
    """Fetch one Catchr metric for the credentialed client.

    Args:
        cred: Decrypted `ClientCredential` row.
        metric: One of REALITY_METRICS.

    Returns:
        SnapshotResult — skipped iff token missing or API fails.
    """
    if not cred.access_token:
        return SnapshotResult(skipped=True, reason="not_connected")
    catchr_metric = METRIC_MAP.get(metric)
    if not catchr_metric:
        return SnapshotResult(skipped=True, reason="not_supported")

    url = f"{CATCHR_API_BASE}/metrics"
    params = {
        "metric": catchr_metric,
        "window_days": 1,
        "aggregate": "last",
    }
    if cred.connector_account_id:
        params["property_id"] = cred.connector_account_id

    ok, status, body = http_get_json(url, bearer_token=cred.access_token, params=params)
    if not ok:
        logger.info(
            "catchr_v30 api_error",
            extra={"client": cred.client_slug, "metric": metric, "status": status},
        )
        return SnapshotResult(
            skipped=True,
            reason="api_error",
            error_text=str(body)[:200],
        )

    value = _extract_value(body, catchr_metric)
    return SnapshotResult(
        skipped=False,
        value=value,
        raw_response=body if isinstance(body, dict) else {"_raw": body},
    )


def _extract_value(body, metric_key: str) -> Optional[float]:
    """Pull a single numeric value out of Catchr's response.

    Catchr v1 returns `{ "data": [{"metric": "...", "value": 0.0327}] }`.
    Defensive : returns None when shape doesn't match.
    """
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if not isinstance(data, list) or len(data) == 0:
        return None
    first = data[0]
    if not isinstance(first, dict):
        return None
    raw = first.get("value")
    if isinstance(raw, (int, float)):
        return float(raw)
    return None
