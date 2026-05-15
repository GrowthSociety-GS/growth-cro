"""Meta Ads V30 OAuth snapshot connector (Task 011).

Single concern : Graph API v18.0 insights → SnapshotResult.

Endpoint : GET `https://graph.facebook.com/v18.0/<ad_account_id>/insights`.
Defensive : `access_token=None` or `connector_account_id=None` → skipped.
"""
from __future__ import annotations

from typing import Optional

from growthcro.observability.logger import get_logger
from growthcro.reality.connectors.http_helper import http_get_json
from growthcro.reality.connectors.types import ClientCredential, SnapshotResult

logger = get_logger(__name__)

META_GRAPH_BASE = "https://graph.facebook.com/v18.0"

# Meta insights metric names per Task 011 metric.
METRIC_MAP: dict[str, str] = {
    "cvr": "conversion_rate",  # custom — derived from actions/clicks
    "cpa": "cost_per_action_type",
    "aov": "purchase_roas",  # proxy ; Meta doesn't expose AOV directly
    "traffic": "clicks",
    "impressions": "impressions",
}


def fetch_snapshot(cred: ClientCredential, metric: str) -> SnapshotResult:
    if not cred.access_token:
        return SnapshotResult(skipped=True, reason="not_connected")
    if not cred.connector_account_id:
        return SnapshotResult(skipped=True, reason="not_connected", error_text="missing_ad_account_id")
    meta_field = METRIC_MAP.get(metric)
    if not meta_field:
        return SnapshotResult(skipped=True, reason="not_supported")

    # Meta Marketing API : access_token is a query param (or Bearer header).
    url = f"{META_GRAPH_BASE}/{cred.connector_account_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,actions",
        "date_preset": "yesterday",
        "access_token": cred.access_token,
    }
    ok, status, body = http_get_json(url, params=params)
    if not ok:
        logger.info(
            "meta_ads_v30 api_error",
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
    """Project Meta's `data[0]` row into the requested metric.

    Meta returns `{"data": [{"impressions": "1234", "clicks": "56", ...}]}`
    with values as strings (Graph API convention). Defensive : numeric parse
    on every field.
    """
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if not isinstance(data, list) or len(data) == 0:
        return None
    row = data[0]
    if not isinstance(row, dict):
        return None
    if metric == "impressions":
        return _as_float(row.get("impressions"))
    if metric == "traffic":
        return _as_float(row.get("clicks"))
    if metric == "cpa":
        # Derive : spend / actions[purchase]
        spend = _as_float(row.get("spend"))
        actions = row.get("actions")
        purchases = 0.0
        if isinstance(actions, list):
            for a in actions:
                if isinstance(a, dict) and a.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
                    purchases += _as_float(a.get("value")) or 0.0
        if spend is None or purchases <= 0:
            return None
        return spend / purchases
    if metric == "cvr":
        clicks = _as_float(row.get("clicks"))
        actions = row.get("actions")
        purchases = 0.0
        if isinstance(actions, list):
            for a in actions:
                if isinstance(a, dict) and a.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
                    purchases += _as_float(a.get("value")) or 0.0
        if clicks is None or clicks <= 0:
            return None
        return purchases / clicks
    if metric == "aov":
        # Use purchase_roas if present, else None.
        roas = row.get("purchase_roas")
        if isinstance(roas, list) and len(roas) > 0:
            return _as_float(roas[0].get("value"))
        return None
    return None


def _as_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
