"""Shopify V30 OAuth snapshot connector (Task 011).

Single concern : Admin REST orders.json → SnapshotResult.

Defensive : `connector_account_id` carries the shop domain
(`<shop>.myshopify.com`). When missing, skip with `not_connected`.

Endpoint : GET `https://<shop>.myshopify.com/admin/api/2024-01/orders.json`.
"""
from __future__ import annotations

from typing import Optional

from growthcro.observability.logger import get_logger
from growthcro.reality.connectors.http_helper import http_get_json
from growthcro.reality.connectors.types import ClientCredential, SnapshotResult

logger = get_logger(__name__)

SHOPIFY_API_VERSION = "2024-01"


def fetch_snapshot(cred: ClientCredential, metric: str) -> SnapshotResult:
    if not cred.access_token:
        return SnapshotResult(skipped=True, reason="not_connected")
    if not cred.connector_account_id:
        return SnapshotResult(skipped=True, reason="not_connected", error_text="missing_shop_domain")

    # Shopify only directly exposes 3 of our 5 metrics ; `cpa` and `impressions`
    # are paid-ads concepts owned by the Meta/Google connectors.
    if metric not in ("cvr", "aov", "traffic"):
        return SnapshotResult(skipped=True, reason="not_supported")

    shop_domain = cred.connector_account_id.strip()
    if not shop_domain.endswith("myshopify.com"):
        return SnapshotResult(skipped=True, reason="api_error", error_text="invalid_shop_domain")

    url = f"https://{shop_domain}/admin/api/{SHOPIFY_API_VERSION}/orders.json"
    params = {
        "status": "any",
        "created_at_min": _yesterday_iso(),
        "limit": 250,
    }
    # Shopify Admin uses X-Shopify-Access-Token header (NOT Authorization Bearer).
    ok, status, body = http_get_json(
        url,
        params=params,
        headers={"X-Shopify-Access-Token": cred.access_token},
    )
    if not ok:
        logger.info(
            "shopify_v30 api_error",
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
        raw_response={"order_count": _safe_len(body)},
    )


def _yesterday_iso() -> str:
    from datetime import datetime, timedelta, timezone
    dt = datetime.now(timezone.utc) - timedelta(days=1)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def _safe_len(body) -> int:
    if isinstance(body, dict):
        orders = body.get("orders")
        if isinstance(orders, list):
            return len(orders)
    return 0


def _extract_value(body, metric: str) -> Optional[float]:
    """Compute the metric from Shopify's orders.json payload.

    - aov : average of `total_price` across paid orders.
    - cvr : we don't have impressions ; estimate as paid_orders / total_orders
            (proxy until GA4 path joins this stream).
    - traffic : total order count (until a `visitors` join is wired).
    """
    if not isinstance(body, dict):
        return None
    orders = body.get("orders")
    if not isinstance(orders, list):
        return None
    if metric == "aov":
        paid = [_safe_price(o) for o in orders if isinstance(o, dict)]
        paid = [p for p in paid if p is not None]
        if not paid:
            return None
        return sum(paid) / len(paid)
    if metric == "traffic":
        return float(len(orders))
    if metric == "cvr":
        if len(orders) == 0:
            return None
        paid_count = sum(
            1
            for o in orders
            if isinstance(o, dict)
            and (o.get("financial_status") in ("paid", "partially_paid"))
        )
        return paid_count / len(orders)
    return None


def _safe_price(o: dict) -> Optional[float]:
    raw = o.get("total_price")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None
