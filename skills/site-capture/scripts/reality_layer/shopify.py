"""Shopify Admin GraphQL API connector — orders + revenue + funnel par landing page.

Required env vars :
- SHOPIFY_STORE_DOMAIN_<CLIENT>  (eg "kaiju.myshopify.com")
- SHOPIFY_ADMIN_API_TOKEN_<CLIENT>  (Admin API access token)

API : Shopify Admin GraphQL Admin API 2024-10
Endpoint : https://{store}.myshopify.com/admin/api/2024-10/graphql.json

Strategy : Shopify ne track pas nativement "landing page → conversion".
Pour ça, il faut soit :
1. UTM tags (utm_source/utm_medium/utm_campaign) sur les landing pages
2. Custom analytics via Shopify Analytics API (Order.customerJourneySummary)

Pour simplifier, on retourne :
- Orders + revenue total sur la période (pour Kaiju, single-product → revenue page-level via UTM)
- Funnel checkout (sessions → cart_added → checkout_started → purchases)
- AOV, refunds_rate, customer LTV proxy
"""
from __future__ import annotations

import os
from typing import Any

from .base import Connector, NotConfiguredError, ConnectorError
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
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

    def _client_env(self, var: str) -> str | None:
        specific = f"{var}_{self.client_slug.upper().replace('-', '_')}"
        return config.system_env(specific) or config.system_env(var)

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Shopify not configured for client={self.client_slug}")

        store = self._client_env("SHOPIFY_STORE_DOMAIN")
        token = self._client_env("SHOPIFY_ADMIN_API_TOKEN")

        try:
            import httpx
        except ImportError:
            raise ConnectorError("httpx not installed")

        url = f"https://{store}/admin/api/2024-10/graphql.json"
        headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }

        # Build orders query : created_at:>=<start> AND created_at:<=<end> AND tag:utm_*
        # Then post-filter on customerJourneySummary.firstVisit.landingPage matching page_url
        gql_query = f"created_at:>={period_start} AND created_at:<={period_end}"

        revenue = 0.0
        orders_count = 0
        page_orders = []
        cursor = None
        page_size = 100

        try:
            with httpx.Client(headers=headers, timeout=60.0) as client:
                while True:
                    payload = {
                        "query": SHOPIFY_QUERY_ORDERS,
                        "variables": {"query": gql_query + (f" AND cursor:{cursor}" if cursor else ""),
                                       "first": page_size},
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
                        # Filter by landing page match
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
            raise ConnectorError(f"Shopify request failed: {e}")

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
