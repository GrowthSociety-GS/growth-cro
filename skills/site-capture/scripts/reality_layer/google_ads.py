"""Google Ads API connector — campaign metrics par landing page.

Required env vars :
- GOOGLE_ADS_DEVELOPER_TOKEN
- GOOGLE_ADS_CLIENT_ID
- GOOGLE_ADS_CLIENT_SECRET
- GOOGLE_ADS_REFRESH_TOKEN
- GOOGLE_ADS_CUSTOMER_ID_<CLIENT>  (10-digit, no dashes)

API : Google Ads API v15+
- GoogleAdsService.search_stream with GAQL :
  SELECT campaign.name, ad_group.name, ad_group_ad.ad.final_urls,
         metrics.cost_micros, metrics.clicks, metrics.impressions,
         metrics.conversions, metrics.conversions_value
  FROM ad_group_ad
  WHERE segments.date BETWEEN '<start>' AND '<end>'
    AND ad_group_ad.ad.final_urls CONTAINS ANY ('<landing_page_url>')

Cost = micros / 1_000_000 (Google Ads stores in micros).

Notes :
- Requires google-ads-python SDK (pip install google-ads)
- OAuth2 refresh token flow needed for production
"""
from __future__ import annotations

import os
from typing import Any

from .base import Connector, NotConfiguredError, ConnectorError
from growthcro.config import config
class GoogleAdsConnector(Connector):
    name = "google_ads"
    required_env_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CUSTOMER_ID",
    ]

    def _client_env(self, var: str) -> str | None:
        specific = f"{var}_{self.client_slug.upper().replace('-', '_')}"
        return config.system_env(specific) or config.system_env(var)

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Google Ads not configured for client={self.client_slug}")

        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            raise ConnectorError(
                "google-ads SDK not installed (pip install google-ads). "
                "Connector implemented as pseudocode for V26.C — activate per client."
            )

        config = {
            "developer_token": self._client_env("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": self._client_env("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": self._client_env("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": self._client_env("GOOGLE_ADS_REFRESH_TOKEN"),
            "use_proto_plus": True,
        }
        customer_id = self._client_env("GOOGLE_ADS_CUSTOMER_ID")

        try:
            client = GoogleAdsClient.load_from_dict(config)
            ga_service = client.get_service("GoogleAdsService")
            query = f"""
                SELECT
                    metrics.cost_micros,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.ctr,
                    metrics.average_cpc
                FROM ad_group_ad
                WHERE segments.date BETWEEN '{period_start}' AND '{period_end}'
                  AND ad_group_ad.ad.final_urls CONTAINS ANY ('{page_url}')
            """
            stream = ga_service.search_stream(customer_id=customer_id, query=query)
            spend_micros = 0
            clicks = 0
            impressions = 0
            conversions = 0.0
            conversion_value = 0.0
            for batch in stream:
                for row in batch.results:
                    spend_micros += row.metrics.cost_micros
                    clicks += row.metrics.clicks
                    impressions += row.metrics.impressions
                    conversions += row.metrics.conversions
                    conversion_value += row.metrics.conversions_value

            spend = spend_micros / 1_000_000
            roas = (conversion_value / spend) if spend > 0 else 0.0
            cpa = (spend / conversions) if conversions > 0 else None
            ctr = (clicks / impressions) if impressions > 0 else 0.0

            return {
                "ad_spend": round(spend, 2),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr, 4),
                "cpc": round(spend / clicks, 4) if clicks > 0 else None,
                "conversions": round(conversions, 2),
                "conversion_value": round(conversion_value, 2),
                "roas": round(roas, 2),
                "cpa": round(cpa, 2) if cpa else None,
            }
        except Exception as e:
            raise ConnectorError(f"Google Ads fetch failed: {type(e).__name__}: {str(e)[:200]}")
