"""Microsoft Clarity Data Export connector — heatmaps + rage clicks + scroll depth.

Required env vars :
- CLARITY_API_TOKEN_<CLIENT> or CLARITY_API_TOKEN
- CLARITY_PROJECT_ID_<CLIENT>

API : Microsoft Clarity Data Export (free, 24h retention by default)
- POST https://www.clarity.ms/export-data/api/v1/project-live-insights
- Returns : aggregated metrics for last 1-3 days only (Clarity limitation)
- Free tier limits : 10 requests/day per project

Notes :
- Pour de la data historique (>3 days), il faut Clarity Plus ou export manuel
- Coverage : rage clicks, dead clicks, quick backs, excessive scroll, scroll depth
- L'install Clarity sur le site client se fait via tracking script (à mettre en place
  manuellement par le client, sinon impossible de récolter)
"""
from __future__ import annotations

import os
from typing import Any

from .base import Connector, NotConfiguredError, ConnectorError


class ClarityConnector(Connector):
    name = "clarity"
    required_env_vars = ["CLARITY_API_TOKEN", "CLARITY_PROJECT_ID"]

    def _client_env(self, var: str) -> str | None:
        specific = f"{var}_{self.client_slug.upper().replace('-', '_')}"
        return os.environ.get(specific) or os.environ.get(var)

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        """Note : Clarity API only supports last 1-3 days. period_start/end ignored,
        always returns most recent insights."""
        if not self.is_configured():
            raise NotConfiguredError(f"Clarity not configured for client={self.client_slug}")

        token = self._client_env("CLARITY_API_TOKEN")
        project_id = self._client_env("CLARITY_PROJECT_ID")

        try:
            import httpx
        except ImportError:
            raise ConnectorError("httpx not installed")

        url = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        params = {
            "numOfDays": 3,
            "dimension1": "URL",
            "filterValue1": page_url,
        }

        try:
            with httpx.Client(headers=headers, timeout=30.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 401 or resp.status_code == 403:
                    raise ConnectorError("Clarity auth failed (check API token)")
                if resp.status_code == 429:
                    raise ConnectorError("Clarity rate limit exceeded (10 req/day free tier)")
                if resp.status_code != 200:
                    raise ConnectorError(f"Clarity {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.RequestError as e:
            raise ConnectorError(f"Clarity request failed: {e}")

        # Parse response (Clarity returns array of metric objects)
        metrics_dict = {m.get("metricName"): m for m in (data if isinstance(data, list) else [])}

        def _value(name: str) -> Any:
            m = metrics_dict.get(name)
            if not m:
                return None
            info = m.get("information") or []
            if info and isinstance(info, list):
                return info[0].get("metricValue")
            return None

        return {
            "project_id": project_id,
            "period": "last_3_days",
            "sessions": _value("Traffic"),
            "rage_clicks": _value("RageClickCount"),
            "dead_clicks": _value("DeadClickCount"),
            "quick_backs": _value("QuickbackClickCount"),
            "excessive_scroll": _value("ExcessiveScroll"),
            "scroll_depth_p50": _value("ScrollDepthP50"),
            "scroll_depth_p90": _value("ScrollDepthP90"),
            "javascript_errors": _value("JavaScriptErrorCount"),
            "warning": "Clarity free tier: only last 3 days available. For historical data, install retention plan.",
        }
