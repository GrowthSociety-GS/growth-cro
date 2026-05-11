"""Meta Marketing API connector — ad_spend + ROAS + CTR par landing page.

Required env vars :
- META_ACCESS_TOKEN_<CLIENT> or META_ACCESS_TOKEN
- META_AD_ACCOUNT_ID_<CLIENT>  (eg "act_1234567890")

API : Graph API v18+
- GET /{ad-account-id}/insights with `breakdowns=landing_destination`
- Returns : spend, impressions, clicks, ctr, cpc, conversions (purchase),
  conversion_value, action_breakdown.
"""
from __future__ import annotations

import os
from typing import Any

from .base import Connector, NotConfiguredError, ConnectorError
from growthcro.config import config
class MetaAdsConnector(Connector):
    name = "meta_ads"
    required_env_vars = ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]

    def _client_env(self, var: str) -> str | None:
        specific = f"{var}_{self.client_slug.upper().replace('-', '_')}"
        return config.system_env(specific) or config.system_env(var)

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Meta Ads not configured for client={self.client_slug}")

        token = self._client_env("META_ACCESS_TOKEN")
        ad_account = self._client_env("META_AD_ACCOUNT_ID")

        try:
            import httpx
        except ImportError:
            raise ConnectorError("httpx not installed")

        # Insights endpoint with landing_destination breakdown (Facebook ad-level)
        # Filter by URL match on landing_destination
        url = f"https://graph.facebook.com/v18.0/{ad_account}/insights"
        params = {
            "access_token": token,
            "fields": "spend,impressions,clicks,ctr,cpc,actions,action_values",
            "time_range": f'{{"since":"{period_start}","until":"{period_end}"}}',
            "level": "ad",
            "breakdowns": "landing_destination",
            "filtering": f'[{{"field":"landing_destination","operator":"CONTAIN","value":"{page_url}"}}]',
            "limit": 500,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 401 or resp.status_code == 403:
                    raise ConnectorError("Meta Ads auth failed (check token + ad_account)")
                if resp.status_code != 200:
                    raise ConnectorError(f"Meta Ads {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.RequestError as e:
            raise ConnectorError(f"Meta Ads request failed: {e}")

        rows = data.get("data", [])
        spend = sum(float(r.get("spend", 0)) for r in rows)
        impressions = sum(int(r.get("impressions", 0)) for r in rows)
        clicks = sum(int(r.get("clicks", 0)) for r in rows)

        purchases = 0
        purchase_value = 0.0
        leads = 0
        for r in rows:
            for a in (r.get("actions") or []):
                if a.get("action_type") == "purchase":
                    purchases += int(a.get("value", 0))
                elif a.get("action_type") == "lead":
                    leads += int(a.get("value", 0))
            for av in (r.get("action_values") or []):
                if av.get("action_type") == "purchase":
                    purchase_value += float(av.get("value", 0))

        roas = (purchase_value / spend) if spend > 0 else 0.0
        cpa = (spend / purchases) if purchases > 0 else None
        ctr = (clicks / impressions) if impressions > 0 else 0.0

        return {
            "ad_spend": round(spend, 2),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 4),
            "cpc": round(spend / clicks, 4) if clicks > 0 else None,
            "purchases": purchases,
            "purchase_value": round(purchase_value, 2),
            "leads": leads,
            "roas": round(roas, 2),
            "cpa": round(cpa, 2) if cpa else None,
        }
