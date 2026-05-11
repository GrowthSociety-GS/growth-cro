"""Google Ads API connector — campaign metrics per landing page.

Issue #23. Promoted from skills/site-capture/scripts/reality_layer/google_ads.py.

Required env vars (per-client preferred, global fallback):
    GOOGLE_ADS_DEVELOPER_TOKEN[_<CLIENT>]
    GOOGLE_ADS_CLIENT_ID[_<CLIENT>]
    GOOGLE_ADS_CLIENT_SECRET[_<CLIENT>]
    GOOGLE_ADS_REFRESH_TOKEN[_<CLIENT>]
    GOOGLE_ADS_CUSTOMER_ID_<CLIENT>  (10-digit, no dashes — always per-client)

API: Google Ads API v15+. Requires `google-ads` SDK.

GAQL:
    SELECT metrics.cost_micros, metrics.clicks, metrics.impressions,
           metrics.conversions, metrics.conversions_value
    FROM ad_group_ad
    WHERE segments.date BETWEEN '<start>' AND '<end>'
      AND ad_group_ad.ad.final_urls CONTAINS ANY ('<landing_page_url>')

Cost = micros / 1_000_000.
"""
from __future__ import annotations

from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError


class GoogleAdsConnector(Connector):
    name = "google_ads"
    required_env_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CUSTOMER_ID",
    ]

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Google Ads not configured for client={self.client_slug}")

        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError as e:
            raise ConnectorError(
                "google-ads SDK not installed. Run: pip install google-ads"
            ) from e

        cfg = {
            "developer_token": config.reality_client_env(
                "GOOGLE_ADS_DEVELOPER_TOKEN", self.client_slug
            ),
            "client_id": config.reality_client_env("GOOGLE_ADS_CLIENT_ID", self.client_slug),
            "client_secret": config.reality_client_env(
                "GOOGLE_ADS_CLIENT_SECRET", self.client_slug
            ),
            "refresh_token": config.reality_client_env(
                "GOOGLE_ADS_REFRESH_TOKEN", self.client_slug
            ),
            "use_proto_plus": True,
        }
        customer_id = config.reality_client_env("GOOGLE_ADS_CUSTOMER_ID", self.client_slug)

        try:
            client = GoogleAdsClient.load_from_dict(cfg)
            ga_service = client.get_service("GoogleAdsService")
            query = (
                f"SELECT metrics.cost_micros, metrics.clicks, metrics.impressions, "
                f"metrics.conversions, metrics.conversions_value, metrics.ctr, "
                f"metrics.average_cpc FROM ad_group_ad WHERE segments.date BETWEEN "
                f"'{period_start}' AND '{period_end}' AND ad_group_ad.ad.final_urls "
                f"CONTAINS ANY ('{page_url}')"
            )
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
            raise ConnectorError(
                f"Google Ads fetch failed: {type(e).__name__}: {str(e)[:200]}"
            ) from e
