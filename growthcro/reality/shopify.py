"""Shopify Admin GraphQL API connector — orders + revenue + funnel per landing page.

Issue #23. Promoted from skills/site-capture/scripts/reality_layer/shopify.py.

Required env vars (per-client preferred, global fallback):
    SHOPIFY_STORE_DOMAIN_<CLIENT>      (e.g. "shop.myshopify.com")
    SHOPIFY_ADMIN_API_TOKEN_<CLIENT>   (Admin API access token, `shpat_…`)

API: Shopify Admin GraphQL Admin API 2024-10.
Attribution: `Order.customerJourneySummary.firstVisit.landingPage`.
"""
from __future__ import annotations

from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError

SHOPIFY_QUERY_ORDERS = """
query getOrders($query: String!, $first: Int!) {
  orders(first: $first, query: $query) {
    edges {
      node {
        id
        createdAt
        totalPriceSet { shopMoney { amount currencyCode } }
        customerJourneySummary {
          firstVisit { source sourceType utmParameters { campaign source medium } landingPage }
          lastVisit { source sourceType utmParameters { campaign source medium } landingPage }
          customerOrderIndex
          daysToConversion
        }
        refunds { totalRefundedSet { shopMoney { amount } } }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


class ShopifyConnector(Connector):
    name = "shopify"
    required_env_vars = ["SHOPIFY_STORE_DOMAIN", "SHOPIFY_ADMIN_API_TOKEN"]

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Shopify not configured for client={self.client_slug}")

        store = config.reality_client_env("SHOPIFY_STORE_DOMAIN", self.client_slug)
        token = config.reality_client_env("SHOPIFY_ADMIN_API_TOKEN", self.client_slug)

        try:
            import httpx
        except ImportError as e:
            raise ConnectorError("httpx not installed") from e

        url = f"https://{store}/admin/api/2024-10/graphql.json"
        headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }

        gql_query = f"created_at:>={period_start} AND created_at:<={period_end}"
        revenue = 0.0
        orders_count = 0
        page_orders: list[dict[str, Any]] = []
        cursor: str | None = None
        page_size = 100

        try:
            with httpx.Client(headers=headers, timeout=60.0) as client:
                while True:
                    payload = {
                        "query": SHOPIFY_QUERY_ORDERS,
                        "variables": {
                            "query": gql_query + (f" AND cursor:{cursor}" if cursor else ""),
                            "first": page_size,
                        },
                    }
                    resp = client.post(url, json=payload)
                    if resp.status_code != 200:
                        raise ConnectorError(f"Shopify {resp.status_code}: {resp.text[:200]}")
                    data = resp.json()
                    if "errors" in data:
                        raise ConnectorError(f"Shopify GraphQL errors: {data['errors']}")
                    orders_data = data.get("data", {}).get("orders", {})
                    edges = orders_data.get("edges", [])
                    for e in edges:
                        node = e["node"]
                        orders_count += 1
                        amount = float(node["totalPriceSet"]["shopMoney"]["amount"])
                        revenue += amount
                        cjs = node.get("customerJourneySummary") or {}
                        lp = (cjs.get("firstVisit") or {}).get("landingPage") or ""
                        if page_url in lp or lp in page_url:
                            page_orders.append({"amount": amount, "id": node["id"]})

                    page_info = orders_data.get("pageInfo", {})
                    if not page_info.get("hasNextPage"):
                        break
                    cursor = page_info.get("endCursor")
                    if orders_count >= 5000:  # safety cap
                        break

        except httpx.RequestError as e:
            raise ConnectorError(f"Shopify request failed: {e}") from e

        page_revenue = sum(o["amount"] for o in page_orders)
        page_aov = (page_revenue / len(page_orders)) if page_orders else 0.0

        return {
            "store_domain": store,
            "orders_total_period": orders_count,
            "revenue_total_period": round(revenue, 2),
            "orders_attributed_to_page": len(page_orders),
            "revenue_attributed_to_page": round(page_revenue, 2),
            "aov_attributed_to_page": round(page_aov, 2),
            "attribution_method": "customerJourneySummary.firstVisit.landingPage",
        }
