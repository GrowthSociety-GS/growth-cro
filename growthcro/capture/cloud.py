"""Bright Data / Browserless cloud endpoint resolution — single concern: cloud delegation.

Resolves WSS endpoints from `growthcro.config` accessors. Pure config logic
— no Playwright imports. The actual browser-connect call lives in
`browser.get_browser`, which consumes the endpoint string returned here.
"""
from __future__ import annotations

from typing import Optional

from growthcro.config import config


def get_brightdata_endpoint() -> Optional[str]:
    """
    Construit l'endpoint WebSocket Bright Data Scraping Browser.

    Supporte deux formats d'env vars :
      1. BRIGHTDATA_WSS=wss://brd-customer-XXX-zone-scraping_browser:PWD@brd.superproxy.io:9222
         (endpoint complet — prioritaire)
      2. BRIGHTDATA_AUTH=brd-customer-XXX-zone-scraping_browser:PWD
         (juste le auth, on construit le wss://)
    """
    # Format 1 : endpoint complet
    full = config.brightdata_wss()
    if full:
        return full

    # Format 2 : auth seulement
    auth = config.brightdata_auth()
    if auth:
        return f"wss://{auth}@brd.superproxy.io:9222"

    return None


def resolve_browserless_endpoint(explicit: Optional[str] = None) -> Optional[str]:
    """Browserless / Steel / BrowserBase WSS endpoint (cloud capture path).

    `explicit` wins over the env var (BROWSER_WS_ENDPOINT). Returns None if
    neither is set so callers can decide whether to fail-fast or fall back.
    """
    return explicit or config.browser_ws_endpoint()
