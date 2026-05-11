"""Playwright browser lifecycle + cookie handling — single concern: browser sessions.

Owns: browser launch (local Chromium, cloud WSS, Bright Data CDP), the stealth
init script injection, cookie-banner dismissal. Stateless module — every call
takes a Playwright instance and returns a `Browser`/`Page`.
"""
from __future__ import annotations

import sys
from typing import Optional

from growthcro.config import config

from .cloud import get_brightdata_endpoint, resolve_browserless_endpoint
from .dom import CLOSE_POPUPS_JS, COOKIE_CLICK_JS, COOKIE_FORCE_REMOVE_JS


# ══════════════════════════════════════════════════════════════
# BROWSER CONNECTION (local, cloud, or Bright Data)
# ══════════════════════════════════════════════════════════════
async def get_browser(pw, cloud: bool, ws_endpoint: Optional[str] = None,
                      force_brightdata: bool = False):
    """
    Retourne un browser Playwright.

    Mode LOCAL     : lance Chromium embarqué (identique à ghost_capture.js)
    Mode CLOUD     : se connecte via WebSocket (Browserless.io, Steel, etc.)
    Mode BRIGHTDATA: se connecte à Bright Data Scraping Browser
                     (anti-bot intégré, IPs résidentielles, CAPTCHA solving)

    Mode DUAL (recommandé) :
        Si BRIGHTDATA_AUTH est défini + mode cloud, on utilise Browserless par défaut.
        Si une capture échoue (403), capture_page() peut relancer via Bright Data.
    """
    # ── Bright Data (prioritaire si forcé) ──
    if force_brightdata:
        bd_endpoint = get_brightdata_endpoint()
        if not bd_endpoint:
            print("❌ Bright Data demandé mais BRIGHTDATA_AUTH / BRIGHTDATA_WSS non défini.")
            print("   export BRIGHTDATA_AUTH='brd-customer-XXXXX-zone-scraping_browser:PASSWORD'")
            print("   Ou : export BRIGHTDATA_WSS='wss://brd-customer-XXXXX-zone-scraping_browser:PWD@brd.superproxy.io:9222'")
            sys.exit(1)
        print(f"  🔶 Connexion Bright Data Scraping Browser...")
        print(f"      Endpoint: {bd_endpoint[:70]}...")
        browser = await pw.chromium.connect_over_cdp(bd_endpoint)
        print(f"  🔶 Connecté à Bright Data! (anti-bot + IPs résidentielles)")
        return browser

    # ── Cloud standard (Browserless, Steel, etc.) ──
    if cloud:
        endpoint = resolve_browserless_endpoint(ws_endpoint)
        if not endpoint:
            print("❌ Mode cloud activé mais BROWSER_WS_ENDPOINT non défini.")
            print("   Exemple : export BROWSER_WS_ENDPOINT='wss://chrome.browserless.io?token=YOUR_TOKEN'")
            print("   Services compatibles : Browserless.io, Steel.dev, BrowserBase.com")
            sys.exit(1)
        print(f"  ☁️  Connexion au navigateur distant...")
        print(f"      Endpoint: {endpoint[:60]}...")
        try:
            browser = await pw.chromium.connect_over_cdp(endpoint)
        except Exception as e:
            print(f"  ⚠️  connect_over_cdp échoué ({e}), tentative connect()...")
            browser = await pw.chromium.connect(endpoint)
        print(f"  ☁️  Connecté!")
        return browser

    # ── Local (headed ou headless) ──
    use_headed = config.is_ghost_headed()
    mode_label = "HEADED (visible)" if use_headed else "headless stealth v2"
    print(f"  💻 Lancement de Chromium local ({mode_label})...")
    browser = await pw.chromium.launch(
        headless=not use_headed,
        channel="chrome" if use_headed else None,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1440,900",
            "--disable-extensions",
            "--disable-default-apps",
            "--disable-component-extensions-with-background-pages",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=IsolateOrigins,site-per-process,TranslateUI",
            "--lang=fr-FR,fr",
        ],
    )
    print(f"  💻 Chromium lancé (local, stealth v2)")
    return browser


# ══════════════════════════════════════════════════════════════
# CONTEXT + PAGE FACTORY
# ══════════════════════════════════════════════════════════════
async def new_stealth_context(browser, *, viewport_width: int = 1440,
                              viewport_height: int = 900):
    """Create a fresh Playwright BrowserContext with stealth init script injected.

    Centralises the User-Agent / locale / timezone block previously inlined
    inside `capture_page`.
    """
    from .dom import STEALTH_JS  # local to avoid loading at import time
    context = await browser.new_context(
        viewport={"width": viewport_width, "height": viewport_height},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="fr-FR",
        timezone_id="Europe/Paris",
        java_script_enabled=True,
        bypass_csp=True,
    )
    await context.add_init_script(STEALTH_JS)
    return context


# ══════════════════════════════════════════════════════════════
# COOKIE HANDLING
# ══════════════════════════════════════════════════════════════
async def handle_cookies(page) -> str:
    """Accepte les cookie banners et ferme les popups. Returns dismissal method tag."""
    # Try known selectors first
    selectors = [
        "#didomi-notice-agree-button",
        "#onetrust-accept-btn-handler",
        'button[id*="accept" i]',
        'button[class*="accept" i]',
        'button[aria-label*="accepter" i]',
        'button[aria-label*="accept" i]',
    ]
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click(delay=50)
                await page.wait_for_timeout(600)
                return "click-selector"
        except Exception:
            pass

    # Try text-based click
    try:
        clicked = await page.evaluate(COOKIE_CLICK_JS)
        if clicked:
            await page.wait_for_timeout(600)
            return "click-text"
    except Exception:
        pass

    # Close popups
    try:
        await page.evaluate(CLOSE_POPUPS_JS)
        await page.wait_for_timeout(300)
    except Exception:
        pass

    # Force remove if still present
    try:
        still_there = await page.evaluate(
            '() => !!document.querySelector(\'[id*="cookie" i][class*="banner" i]\')'
        )
        if still_there:
            removed = await page.evaluate(COOKIE_FORCE_REMOVE_JS)
            if removed > 0:
                return "dom-removed"
    except Exception:
        pass

    return "none"
