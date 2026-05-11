"""Microsoft Clarity Data Export connector — heatmaps + rage clicks + scroll depth.

Issue #23. Promoted from skills/site-capture/scripts/reality_layer/clarity.py.

Required env vars (per-client preferred, global fallback):
    CLARITY_API_TOKEN_<CLIENT>
    CLARITY_PROJECT_ID_<CLIENT>

Notes:
- Free tier limits: last 3 days only, 10 requests/day per project.
- For historical data (>3 days), client needs Clarity Plus or manual export.
"""
from __future__ import annotations

from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError


class ClarityConnector(Connector):
    name = "clarity"
    required_env_vars = ["CLARITY_API_TOKEN", "CLARITY_PROJECT_ID"]

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        """Note: Clarity API only supports last 1-3 days. period_start/end are
        accepted but ignored — Clarity always returns most recent insights."""
        if not self.is_configured():
            raise NotConfiguredError(f"Clarity not configured for client={self.client_slug}")

        token = config.reality_client_env("CLARITY_API_TOKEN", self.client_slug)
        project_id = config.reality_client_env("CLARITY_PROJECT_ID", self.client_slug)

        try:
            import httpx
        except ImportError as e:
            raise ConnectorError("httpx not installed") from e

        url = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        params = {"numOfDays": 3, "dimension1": "URL", "filterValue1": page_url}

        try:
            with httpx.Client(headers=headers, timeout=30.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code in (401, 403):
                    raise ConnectorError("Clarity auth failed (check API token)")
                if resp.status_code == 429:
                    raise ConnectorError("Clarity rate limit (10 req/day free tier)")
                if resp.status_code != 200:
                    raise ConnectorError(f"Clarity {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.RequestError as e:
            raise ConnectorError(f"Clarity request failed: {e}") from e

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
            "warning": (
                "Clarity free tier: only last 3 days available. period_start/end ignored. "
                "For historical data, install retention plan."
            ),
        }
