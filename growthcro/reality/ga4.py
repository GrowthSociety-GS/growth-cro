"""Native Google Analytics 4 Data API v1 connector.

Issue #23. Alternative to the Catchr aggregator — for clients that have
GA4 set up directly and provide a Google service account JSON. Mathis can
pick whichever fits the client.

Required env vars (per-client preferred, global fallback):
    GA4_SERVICE_ACCOUNT_JSON_<CLIENT>  → path to a Google service account JSON
                                          (the service account must be a Viewer
                                          on the GA4 property)
    GA4_PROPERTY_ID_<CLIENT>           → GA4 numeric property ID (e.g. "375629104")

API: GA4 Data API v1 — `runReport` against `properties/<id>`.

Returns metrics: sessions, total_users, conversions, bounce_rate, average_session_duration,
device split, primary source/medium for the landing page URL filter.

Live-run requirement:
    pip install google-analytics-data  (or just `google-analytics-data`)
    + a valid service-account JSON whose path is in the env var.

Without the SDK installed, `fetch()` raises `ConnectorError` with a clear
"install google-analytics-data" message — never silently fails.
"""
from __future__ import annotations

from typing import Any

from growthcro.config import config
from growthcro.reality.base import Connector, ConnectorError, NotConfiguredError


class GA4Connector(Connector):
    """Native Google Analytics Data API v1 connector."""

    name = "ga4"
    required_env_vars = ["GA4_SERVICE_ACCOUNT_JSON", "GA4_PROPERTY_ID"]

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        if not self.is_configured():
            raise NotConfiguredError(f"GA4 not configured for client={self.client_slug}")

        sa_path = config.reality_client_env("GA4_SERVICE_ACCOUNT_JSON", self.client_slug)
        property_id = config.reality_client_env("GA4_PROPERTY_ID", self.client_slug)

        # Lazy import — keeps module import cheap and lets `credentials.py`
        # report status without requiring the SDK.
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import (
                DateRange,
                Dimension,
                Filter,
                FilterExpression,
                Metric,
                RunReportRequest,
            )
        except ImportError as e:
            raise ConnectorError(
                "google-analytics-data SDK not installed. "
                "Run: pip install google-analytics-data"
            ) from e

        # Path-based filter: GA4 stores landing pages as page paths, so we
        # extract path from URL.
        path = _url_to_path(page_url)
        try:
            client = BetaAnalyticsDataClient.from_service_account_json(sa_path)
        except Exception as e:
            raise ConnectorError(
                f"GA4 service account load failed (check GA4_SERVICE_ACCOUNT_JSON path "
                f"+ JSON validity): {type(e).__name__}"
            ) from e

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=period_start, end_date=period_end)],
            dimensions=[
                Dimension(name="landingPage"),
                Dimension(name="sessionSourceMedium"),
                Dimension(name="deviceCategory"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="conversions"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="landingPage",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.CONTAINS,
                        value=path,
                    ),
                )
            ),
            limit=10000,
        )

        try:
            response = client.run_report(request=request)
        except Exception as e:
            raise ConnectorError(
                f"GA4 runReport failed: {type(e).__name__}: {str(e)[:200]}"
            ) from e

        # Aggregate rows
        sessions = 0
        users = 0
        conversions = 0.0
        weighted_bounce_num = 0.0
        weighted_duration_num = 0.0
        device_sessions: dict[str, int] = {}
        source_sessions: dict[str, int] = {}
        for row in response.rows:
            dims = {d.name: row.dimension_values[i].value for i, d in enumerate(response.dimension_headers)}
            mets = {m.name: row.metric_values[i].value for i, m in enumerate(response.metric_headers)}
            try:
                s = int(mets.get("sessions") or 0)
                u = int(mets.get("totalUsers") or 0)
                cv = float(mets.get("conversions") or 0)
                br = float(mets.get("bounceRate") or 0)
                dur = float(mets.get("averageSessionDuration") or 0)
            except (TypeError, ValueError):
                continue
            sessions += s
            users += u
            conversions += cv
            weighted_bounce_num += br * s
            weighted_duration_num += dur * s
            dev = (dims.get("deviceCategory") or "unknown").lower()
            device_sessions[dev] = device_sessions.get(dev, 0) + s
            sm = dims.get("sessionSourceMedium") or "(unknown)"
            source_sessions[sm] = source_sessions.get(sm, 0) + s

        conversion_rate = (conversions / sessions) if sessions > 0 else 0.0
        bounce_rate = (weighted_bounce_num / sessions) if sessions > 0 else None
        avg_duration = (weighted_duration_num / sessions) if sessions > 0 else None
        total_dev = sum(device_sessions.values()) or 1
        device_split = {k: round(v / total_dev, 4) for k, v in device_sessions.items()}
        primary_source = (
            max(source_sessions.items(), key=lambda x: x[1])[0] if source_sessions else None
        )

        return {
            "property_id": property_id,
            "sessions": sessions,
            "users": users,
            "conversions": round(conversions, 2),
            "conversion_rate": round(conversion_rate, 4),
            "bounce_rate": round(bounce_rate, 4) if bounce_rate is not None else None,
            "avg_session_duration_s": round(avg_duration, 2) if avg_duration is not None else None,
            "primary_source_medium": primary_source,
            "device_split": device_split,
            "rows_returned": len(response.rows),
            "filter_landing_path": path,
        }


def _url_to_path(url: str) -> str:
    """Best-effort: extract pathname from a URL for the landingPage filter."""
    if "://" in url:
        url = url.split("://", 1)[1]
    if "/" in url:
        path = "/" + url.split("/", 1)[1]
    else:
        path = "/"
    # Strip query string + fragment
    path = path.split("?", 1)[0].split("#", 1)[0]
    # Trailing slash normalisation: leave as-is (GA4 CONTAINS is forgiving)
    return path
