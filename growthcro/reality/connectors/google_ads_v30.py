"""Google Ads V30 OAuth snapshot connector (Task 011).

Single concern : one search-stream query against Google Ads API v15 →
SnapshotResult.

Defensive : the real Google Ads API requires a developer_token + login
customer ID in HTTP headers in addition to the OAuth access_token. The V1
connector returns `not_connected` when `connector_account_id` (the customer
ID) is missing, and `api_error` for any non-2xx response. A future sprint
will wire the developer_token from env (`GOOGLE_ADS_DEVELOPER_TOKEN`) once
Mathis registers the Growth Society Google Ads MCC.

Endpoint : POST `https://googleads.googleapis.com/v15/customers/{cid}/googleAds:searchStream`.
This module uses GET against the lower-rate `googleAds:search` flavour for
simplicity (single-metric snapshot, no need to stream).
"""
from __future__ import annotations

from typing import Optional

from growthcro.config import config
from growthcro.observability.logger import get_logger
from growthcro.reality.connectors.http_helper import http_get_json
from growthcro.reality.connectors.types import ClientCredential, SnapshotResult

logger = get_logger(__name__)

GADS_API_BASE = "https://googleads.googleapis.com/v15"

# Map Task 011 metric → Google Ads metrics.* column.
METRIC_MAP: dict[str, str] = {
    "cvr": "metrics.conversions_from_interactions_rate",
    "cpa": "metrics.cost_per_conversion",
    "aov": "metrics.average_order_value_micros",
    "traffic": "metrics.clicks",
    "impressions": "metrics.impressions",
}


def fetch_snapshot(cred: ClientCredential, metric: str) -> SnapshotResult:
    if not cred.access_token:
        return SnapshotResult(skipped=True, reason="not_connected")
    if not cred.connector_account_id:
        return SnapshotResult(skipped=True, reason="not_connected", error_text="missing_customer_id")
    gads_field = METRIC_MAP.get(metric)
    if not gads_field:
        return SnapshotResult(skipped=True, reason="not_supported")

    # The developer_token lives in env (global, agency-level — not per-client).
    # Reuse the legacy `GOOGLE_ADS_DEVELOPER_TOKEN` declared in `_KNOWN_VARS`
    # via the system_env passthrough (read-only, no fallback). When missing,
    # skip with reason='not_connected' rather than crash.
    dev_token = config.system_env("GOOGLE_ADS_DEVELOPER_TOKEN") or None
    if not dev_token:
        return SnapshotResult(skipped=True, reason="not_connected", error_text="missing_developer_token")
    login_cid = config.system_env("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or None

    customer_id = cred.connector_account_id.replace("-", "")
    query = (
        f"SELECT {gads_field} FROM customer "
        f"WHERE segments.date DURING YESTERDAY"
    )
    url = f"{GADS_API_BASE}/customers/{customer_id}/googleAds:search"
    extra_headers: dict[str, str] = {"developer-token": dev_token}
    if login_cid:
        # When the OAuth account is a manager (MCC), Google Ads also
        # expects `login-customer-id`. Defensive : populated when env set.
        extra_headers["login-customer-id"] = login_cid
    ok, status, body = http_get_json(
        url,
        bearer_token=cred.access_token,
        params={"query": query, "pageSize": 1},
        headers=extra_headers,
    )
    if not ok:
        logger.info(
            "google_ads_v30 api_error",
            extra={"client": cred.client_slug, "metric": metric, "status": status},
        )
        return SnapshotResult(
            skipped=True,
            reason="api_error",
            error_text=str(body)[:200],
        )

    value = _extract_value(body, metric)
    return SnapshotResult(
        skipped=False,
        value=value,
        raw_response=body if isinstance(body, dict) else {"_raw": body},
    )


def _extract_value(body, metric: str) -> Optional[float]:
    """Project `results[0].metrics.<field>` into a float.

    Google Ads search returns `{"results": [{"metrics": {"clicks": "123", ...}}]}`
    with values as strings. micros fields (cost_per_conversion, AOV) are in
    millionths — convert.
    """
    if not isinstance(body, dict):
        return None
    results = body.get("results")
    if not isinstance(results, list) or len(results) == 0:
        return None
    metrics_obj = results[0].get("metrics") if isinstance(results[0], dict) else None
    if not isinstance(metrics_obj, dict):
        return None
    field = METRIC_MAP.get(metric, "").split(".")[-1]
    raw = metrics_obj.get(field)
    if raw is None:
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if "micros" in field:
        v = v / 1_000_000.0
    return v
