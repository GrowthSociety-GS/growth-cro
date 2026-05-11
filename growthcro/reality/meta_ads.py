"""Meta Marketing API connector — ad_spend + ROAS + CTR per landing page.

Issue #23. Promoted from skills/site-capture/scripts/reality_layer/meta_ads.py.

Required env vars (per-client preferred, global fallback):
    META_ACCESS_TOKEN_<CLIENT>
    META_AD_ACCOUNT_ID_<CLIENT>  (eg "act_1234567890")
"""
from __future__ import annotations

from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError


class MetaAdsConnector(Connector):
    name = "meta_ads"
    required_env_vars = ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Meta Ads not configured for client={self.client_slug}")

        token = config.reality_client_env("META_ACCESS_TOKEN", self.client_slug)
        ad_account = config.reality_client_env("META_AD_ACCOUNT_ID", self.client_slug)

        try:
            import httpx
        except ImportError as e:
            raise ConnectorError("httpx not installed") from e

        url = f"https://graph.facebook.com/v18.0/{ad_account}/insights"
        params = {
            "access_token": token,
            "fields": "spend,impressions,clicks,ctr,cpc,actions,action_values",
            "time_range": f'{{"since":"{period_start}","until":"{period_end}"}}',
            "level": "ad",
            "breakdowns": "landing_destination",
            "filtering": (
                f'[{{"field":"landing_destination","operator":"CONTAIN","value":"{page_url}"}}]'
            ),
            "limit": 500,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code in (401, 403):
                    raise ConnectorError("Meta Ads auth failed (check token + ad_account)")
                if resp.status_code != 200:
                    raise ConnectorError(f"Meta Ads {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.RequestError as e:
            raise ConnectorError(f"Meta Ads request failed: {e}") from e

        rows = data.get("data", [])
        spend = sum(float(r.get("spend", 0)) for r in rows)
        impressions = sum(int(r.get("impressions", 0)) for r in rows)
        clicks = sum(int(r.get("clicks", 0)) for r in rows)

        purchases = 0
        purchase_value = 0.0
        leads = 0
        for r in rows:
            for a in r.get("actions") or []:
                if a.get("action_type") == "purchase":
                    purchases += int(a.get("value", 0))
                elif a.get("action_type") == "lead":
                    leads += int(a.get("value", 0))
            for av in r.get("action_values") or []:
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
