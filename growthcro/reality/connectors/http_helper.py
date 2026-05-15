"""Shared HTTP helper for the V30 OAuth connectors (Task 011).

Single concern : minimal stdlib-based HTTP GET (no new dependency vs `httpx`).
The legacy connectors use `httpx` ; the V30 OAuth path uses `urllib.request` to
keep the cold-path simple and avoid bringing httpx into the worker daemon's
imports just for 5 occasional fetches per cron tick.

Defensive : every call returns `(ok, status, body_text)` — never raises. The
caller decides how to interpret the body. JSON parsing is left to the caller.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

DEFAULT_TIMEOUT_SEC = 20


def http_get_json(
    url: str,
    *,
    bearer_token: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT_SEC,
) -> tuple[bool, int, Any]:
    """GET an URL, decode JSON.

    Returns (ok, status, decoded_json_or_text). `ok` is True iff HTTP 2xx and
    the body is valid JSON. On any error (network, timeout, non-2xx, bad
    JSON), `ok` is False and the third element is a short text describing the
    failure (safe to log — never the request body).
    """
    if params:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    if bearer_token:
        req.add_header("Authorization", f"Bearer {bearer_token}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "GrowthCRO-RealityLayer/V30")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            raw = resp.read().decode("utf-8", errors="replace")
            if status < 200 or status >= 300:
                return (False, status, raw[:500])
            try:
                return (True, status, json.loads(raw))
            except json.JSONDecodeError as e:
                return (False, status, f"json_decode_error: {e}")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:  # noqa: BLE001
            body = ""
        return (False, e.code, body or f"http_error_{e.code}")
    except urllib.error.URLError as e:
        return (False, 0, f"url_error: {e.reason}")
    except (TimeoutError, OSError) as e:
        return (False, 0, f"network_error: {e}")
