"""Catchr connector — Growth Society internal GA4+ aggregator.

Issue #23. Promotes `skills/site-capture/scripts/reality_layer/catchr.py`
into the growthcro/ namespace. We reimplement the thin HTTP shim (rather
than importing the legacy class) so that `isinstance` checks against
`growthcro.reality.base.Connector` work consistently across the package
and so the legacy skills/ folder can be retired in a future sprint.

Required env vars (per-client preferred, global fallback):
    CATCHR_API_KEY_<CLIENT>
    CATCHR_PROPERTY_ID_<CLIENT>
"""
from __future__ import annotations

from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError


class CatchrConnector(Connector):
    name = "catchr"
    required_env_vars = ["CATCHR_API_KEY", "CATCHR_PROPERTY_ID"]

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Catchr not configured for client={self.client_slug}")

        api_key = config.reality_client_env("CATCHR_API_KEY", self.client_slug)
        property_id = config.reality_client_env("CATCHR_PROPERTY_ID", self.client_slug)

        try:
            import httpx
        except ImportError as e:
            raise ConnectorError("httpx not installed (pip install httpx)") from e

        url = "https://api.catchr.io/v1/analytics/landing-pages"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        params = {
            "property_id": property_id,
            "start_date": period_start,
            "end_date": period_end,
            "page_url": page_url,
            "metrics": "sessions,users,conversions,bounce_rate,avg_session_duration",
            "dimensions": "source_medium,device_category",
        }

        try:
            with httpx.Client(headers=headers, timeout=30.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 401:
                    raise ConnectorError("Catchr auth failed (check API key)")
                if resp.status_code != 200:
                    raise ConnectorError(f"Catchr {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.RequestError as e:
            raise ConnectorError(f"Catchr request failed: {e}") from e

        rows = data.get("rows", [])
        sessions = sum(r.get("sessions", 0) for r in rows)
        users = sum(r.get("users", 0) for r in rows)
        conversions = sum(r.get("conversions", 0) for r in rows)
        cr = (conversions / sessions) if sessions > 0 else 0.0

        device_sessions: dict[str, int] = {}
        for r in rows:
            dev = (r.get("device_category") or "unknown").lower()
            device_sessions[dev] = device_sessions.get(dev, 0) + r.get("sessions", 0)
        total_dev = sum(device_sessions.values()) or 1
        device_split = {k: round(v / total_dev, 4) for k, v in device_sessions.items()}

        source_sessions: dict[str, int] = {}
        for r in rows:
            sm = r.get("source_medium") or "(unknown)"
            source_sessions[sm] = source_sessions.get(sm, 0) + r.get("sessions", 0)
        primary_source = (
            max(source_sessions.items(), key=lambda x: x[1])[0] if source_sessions else None
        )

        bounce_rate = None
        if sessions > 0:
            bounce_rate = (
                sum(r.get("bounce_rate", 0) * r.get("sessions", 0) for r in rows) / sessions
            )

        return {
            "sessions": sessions,
            "users": users,
            "conversions": conversions,
            "conversion_rate": round(cr, 4),
            "primary_source_medium": primary_source,
            "device_split": device_split,
            "bounce_rate": round(bounce_rate, 4) if bounce_rate is not None else None,
            "raw_rows_count": len(rows),
        }
