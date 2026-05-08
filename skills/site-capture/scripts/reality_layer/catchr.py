"""Catchr connector — GA4 wrapper used internally by Growth Society.

Catchr unifies GA4 + Shopify + Stripe + Meta + Google Ads in one API.
For the Reality Layer, we extract GA4-equivalent metrics per landing page.

Required env vars (per client preferred, global fallback) :
- CATCHR_API_KEY_<CLIENT> or CATCHR_API_KEY
- CATCHR_PROPERTY_ID_<CLIENT> (the Catchr-side identifier of the client property)

Endpoint (placeholder — to confirm with Catchr docs) :
- GET https://api.catchr.io/v1/analytics/landing-pages
- Query : property_id, start_date, end_date, page_url

Returns metrics : sessions, users, conversions, conversion_rate,
primary_source/medium, device_split, bounce_rate, avg_session_duration.

Status V26.C : stub fonctionnel — à activer une fois credentials Kaiju
ajoutés au .env.
"""
from __future__ import annotations

import os
from typing import Any

from .base import Connector, NotConfiguredError, ConnectorError


class CatchrConnector(Connector):
    name = "catchr"
    required_env_vars = ["CATCHR_API_KEY", "CATCHR_PROPERTY_ID"]

    def _client_env(self, var: str) -> str | None:
        specific = f"{var}_{self.client_slug.upper().replace('-', '_')}"
        return os.environ.get(specific) or os.environ.get(var)

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"Catchr not configured for client={self.client_slug}")

        api_key = self._client_env("CATCHR_API_KEY")
        property_id = self._client_env("CATCHR_PROPERTY_ID")

        try:
            import httpx
        except ImportError:
            raise ConnectorError("httpx not installed (pip install httpx)")

        # NOTE : confirmer endpoint exact avec doc Catchr (ce qui suit est un placeholder)
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
            raise ConnectorError(f"Catchr request failed: {e}")

        # Normalize the Catchr response into our schema
        rows = data.get("rows", [])
        sessions = sum(r.get("sessions", 0) for r in rows)
        users = sum(r.get("users", 0) for r in rows)
        conversions = sum(r.get("conversions", 0) for r in rows)
        cr = (conversions / sessions) if sessions > 0 else 0.0

        # Device split
        device_sessions: dict[str, int] = {}
        for r in rows:
            dev = (r.get("device_category") or "unknown").lower()
            device_sessions[dev] = device_sessions.get(dev, 0) + r.get("sessions", 0)
        total_dev = sum(device_sessions.values()) or 1
        device_split = {k: round(v / total_dev, 4) for k, v in device_sessions.items()}

        # Primary source/medium
        source_sessions: dict[str, int] = {}
        for r in rows:
            sm = r.get("source_medium") or "(unknown)"
            source_sessions[sm] = source_sessions.get(sm, 0) + r.get("sessions", 0)
        primary_source = max(source_sessions.items(), key=lambda x: x[1])[0] if source_sessions else None

        # Bounce rate (weighted avg by sessions)
        if sessions > 0:
            bounce_rate = sum(r.get("bounce_rate", 0) * r.get("sessions", 0) for r in rows) / sessions
        else:
            bounce_rate = None

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
