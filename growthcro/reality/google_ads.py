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

import re
from datetime import date as _date_cls
from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError

# ISO-8601 date (YYYY-MM-DD) — strict Pydantic-style validator
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Whitelist landing-page URLs to defang any GAQL injection via final_urls CONTAINS ANY
_PAGE_URL_RE = re.compile(r"^https?://[\w\-\.]+(:\d+)?(/[\w\-\./%~?&=#:+,]*)?$")


def _validate_iso_date(value: str, field: str) -> str:
    """Strict YYYY-MM-DD validator. Raises ConnectorError on invalid input.

    Defends growthcro/reality/google_ads.py GAQL builder against B608
    SQL-injection via the BETWEEN clause (bandit MEDIUM B608).
    """
    if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
        raise ConnectorError(
            f"{field} must be ISO-8601 YYYY-MM-DD, got {value!r}"
        )
    # Re-parse to catch impossible dates (e.g. 2026-02-30)
    try:
        _date_cls.fromisoformat(value)
    except ValueError as exc:
        raise ConnectorError(f"{field} invalid calendar date: {value!r}") from exc
    return value


def _validate_page_url(url: str) -> str:
    """Whitelist landing-page URLs against ^https?://[\\w\\-\\.]+/.*$.

    Defends the `CONTAINS ANY ('<page_url>')` GAQL clause against B608
    injection by rejecting any URL containing quotes, control chars,
    GAQL keywords, or other unexpected punctuation.
    """
    if not isinstance(url, str) or not _PAGE_URL_RE.match(url):
        raise ConnectorError(f"page_url failed whitelist regex: {url!r}")
    if "'" in url or '"' in url or "\\" in url:
        raise ConnectorError(f"page_url contains disallowed quote/escape: {url!r}")
    return url


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

        # B608 defense: validate all values interpolated into the GAQL string.
        # We cannot use prepared-statement binds (GAQL builder is f-string-only);
        # so we enforce strict whitelists at the boundary instead.
        page_url = _validate_page_url(page_url)
        period_start = _validate_iso_date(period_start, "period_start")
        period_end = _validate_iso_date(period_end, "period_end")

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
            # B608 defense: `period_start`, `period_end` constrained to YYYY-MM-DD,
            # `page_url` constrained to ^https?://[\w\-\.]+/.*$ by the validators
            # above; GAQL has no bind-parameter API in the official SDK.
            _gaql_select = (
                "SELECT metrics.cost_micros, metrics.clicks, metrics.impressions, "
                "metrics.conversions, metrics.conversions_value, metrics.ctr, "
                "metrics.average_cpc FROM ad_group_ad WHERE segments.date BETWEEN "
            )
            query = (
                f"{_gaql_select}'{period_start}' AND '{period_end}' "  # nosec B608
                f"AND ad_group_ad.ad.final_urls CONTAINS ANY ('{page_url}')"
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
