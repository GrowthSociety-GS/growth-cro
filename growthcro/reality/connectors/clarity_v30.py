"""Microsoft Clarity V30 OAuth snapshot connector (Task 011).

Single concern : Clarity Data Export API → SnapshotResult.

Defensive : Clarity OAuth is private beta (2024-2026). Until the OAuth flow
is publicly available, this connector falls back to API-token auth (the
`access_token` field carries the export token rather than an OAuth bearer).
The `fetch_snapshot_for` dispatch in `dispatch.py` keeps that distinction
transparent.

Endpoint : GET `https://www.clarity.ms/export-data/api/v1/project-live-insights`.
"""
from __future__ import annotations

from typing import Optional

from growthcro.observability.logger import get_logger
from growthcro.reality.connectors.http_helper import http_get_json
from growthcro.reality.connectors.types import ClientCredential, SnapshotResult

logger = get_logger(__name__)

CLARITY_API = "https://www.clarity.ms/export-data/api/v1/project-live-insights"


def fetch_snapshot(cred: ClientCredential, metric: str) -> SnapshotResult:
    if not cred.access_token:
        return SnapshotResult(skipped=True, reason="not_connected")

    # Clarity's metrics surface : sessions, page_views, dead_clicks, rage_clicks,
    # quick_backs, scroll_depth. Map to Task 011 metrics where possible.
    if metric == "traffic":
        clarity_metric = "Sessions"
    elif metric == "impressions":
        clarity_metric = "PageViews"
    else:
        # CVR/CPA/AOV are not behavioural metrics — Clarity doesn't own them.
        return SnapshotResult(skipped=True, reason="not_supported")

    params = {"numOfDays": 1}
    if cred.connector_account_id:
        params["projectId"] = cred.connector_account_id

    ok, status, body = http_get_json(
        CLARITY_API,
        bearer_token=cred.access_token,
        params=params,
    )
    if not ok:
        logger.info(
            "clarity_v30 api_error",
            extra={"client": cred.client_slug, "metric": metric, "status": status},
        )
        return SnapshotResult(
            skipped=True,
            reason="api_error",
            error_text=str(body)[:200],
        )

    value = _extract_value(body, clarity_metric)
    return SnapshotResult(
        skipped=False,
        value=value,
        raw_response=body if isinstance(body, dict) else {"_raw": body},
    )


def _extract_value(body, clarity_metric: str) -> Optional[float]:
    """Pull a numeric value out of Clarity's payload.

    Clarity's `project-live-insights` returns a list of `{"metricName":
    "Sessions", "information": [{"sessionsCount": 1234}, ...]}`. Defensive
    against shape drift.
    """
    if not isinstance(body, list):
        return None
    for entry in body:
        if not isinstance(entry, dict):
            continue
        if entry.get("metricName") == clarity_metric:
            info = entry.get("information")
            if isinstance(info, list) and len(info) > 0:
                row = info[0]
                if isinstance(row, dict):
                    # Take the first numeric value.
                    for v in row.values():
                        try:
                            return float(v)
                        except (TypeError, ValueError):
                            continue
    return None
