#!/usr/bin/env python3
"""
playwright_capture_v2.py — V20.CAPTURE C1c : capture robuste en deux passes.

Objectifs vs V17 (ghost_capture.js) :
  1. Dual state par viewport : "asis" (avec popup) + "clean" (popup fermé)
  2. Vérification post-close : DOM scan + OCR signature check, si popup encore
     visible → flag `popup_close_failed` et on garde "asis" comme référence
  3. Lazy-load scroll priming : scroll incremental bottom puis retour top
     → déclenche IntersectionObserver + lazy images
  4. Screenshots page-relative (scrollX=0) avec bbox absolute cohérent DOM
  5. Pipeline Python (plus unifié, plus facile à débugger)
  6. Desktop (1440x900@2x) + Mobile (iPhone 14 : 390x844@3x) séparés proprement

Sortie par page :
    data/captures/<client>/<page>/
        screenshots/
            desktop_asis_fold.png      (fold, popup visible)
            desktop_asis_full.png      (fullpage, popup visible)
            desktop_clean_fold.png     (popup fermé)
            desktop_clean_full.png     (popup fermé, lazy-load déclenché)
            mobile_asis_fold.png
            mobile_asis_full.png
            mobile_clean_fold.png
            mobile_clean_full.png
        spatial_v10.json               (DOM dump post-render + isReallyVisible)
        capture_v2.json                (hero extraction v2, native style)
        capture_v2_meta.json           (popup flags, timing, errors)

Usage :
    python3 playwright_capture_v2.py --url https://japhy.fr --client japhy --page home
    python3 playwright_capture_v2.py --batch <json_file>  # [{url, client, page}, ...]

Prérequis : pip install playwright && playwright install chromium

v1.0 — 2026-04-20
"""
from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import re
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
from growthcro.config import config
CAPTURES = ROOT / "data" / "captures"
SPATIAL_JS = ROOT / "skills" / "site-capture" / "references" / "spatial_capture_v9.js"

# ── Viewports ─────────────────────────────────────────────────
VIEWPORTS = {
    "desktop": {
        "width": 1440,
        "height": 900,
        "device_scale": 2,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "is_mobile": False,
    },
    "mobile": {
        "width": 390,
        "height": 844,
        "device_scale": 3,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "is_mobile": True,
    },
}

# Popup / cookie signatures used to verify closure via DOM text
POPUP_KEYWORDS_RE = re.compile(
    r"cookies?|consentement|accepter|refuser|rgpd|gdpr|newsletter|s'?inscrir|politique de confidentialité|vie privée",
    re.IGNORECASE,
)

COOKIE_SELECTORS = [
    # ── Didomi (multiple variants) ────────────────────────────
    "#didomi-notice-agree-button",
    ".didomi-continue-without-agreeing",
    "button[aria-label*='Tout accepter' i]",
    "button[data-testid='didomi-accept-all']",
    # ── OneTrust (multiple variants) ──────────────────────────
    "#onetrust-accept-btn-handler",
    "#accept-recommended-btn-handler",
    "button.ot-pc-refuse-all-handler",
    "#onetrust-pc-btn-handler",
    "[aria-label='Accept Cookies']",
    # ── Cookiebot (NEW V21.A) ─────────────────────────────────
    "#CybotCookiebotDialogBodyLevelButtonAccept",
    "#CybotCookiebotDialogBodyLevelButtonAcceptAll",
    "#CybotCookiebotDialogBodyButtonAccept",
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    # ── Usercentrics (NEW V21.A — variants) ───────────────────
    "[data-testid='uc-accept-all-button']",
    "button[data-testid='uc-accept-all']",
    ".uc-btn-accept",
    "button#uc-btn-accept-banner",
    "button[mode='primary']",
    # ── Axeptio ───────────────────────────────────────────────
    "#axeptio_btn_acceptAll",
    "button.axeptio-widget--button-accept",
    "[data-testid='axeptio-acceptAll']",
    # ── Tarteaucitron ─────────────────────────────────────────
    "#tarteaucitronPersonalize2",
    "#tarteaucitronAllAllowed",
    "button#tarteaucitronAllAllowed2",
    # ── Iubenda ───────────────────────────────────────────────
    "button.iubenda-cs-accept-btn",
    ".iubenda-cs-customize-btn",
    # ── TrustArc (NEW V21.A) ──────────────────────────────────
    "#truste-consent-button",
    "a.call",
    "button.truste-button1",
    # ── Quantcast ─────────────────────────────────────────────
    "button.qc-cmp2-summary-buttons button[mode='primary']",
    "button.qc-cmp2-button[mode='primary']",
    # ── Klaro / Cookiehub ─────────────────────────────────────
    ".klaro .cm-btn-success",
    ".cookiehub-button-accept",
    # ── Crisp / Hotjar ────────────────────────────────────────
    ".cc-btn.cc-allow",
    ".cookieconsent .cc-allow",
    # ── Shopify / app native ──────────────────────────────────
    ".shopify-section-cookie button[name='accept']",
    "button[id*='cookie' i][id*='accept' i]",
    # ── Generic ───────────────────────────────────────────────
    "button[id*='accept' i]",
    "button[class*='accept' i]",
    "button[aria-label*='accepter' i]",
    "button[aria-label*='accept' i]",
    "button[data-action='accept']",
    "button[data-cy='accept-cookies']",
    "button[data-test='accept-cookies']",
]

# Text fallback (multilingue : FR / EN / DE / ES / IT — pour goldens internationaux)
COOKIE_TEXTS_FR = [
    # FR
    "Tout accepter", "Tout autoriser", "J'accepte", "Accepter tous", "Accepter",
    "OK", "J'ai compris", "Continuer sans accepter", "Accepter et continuer",
    # EN
    "Accept all", "Accept All Cookies", "I accept", "Allow all", "Allow All",
    "Agree", "Agree and continue", "Got it", "Continue", "I understand", "Yes, I accept",
    # DE
    "Alle akzeptieren", "Akzeptieren", "Ich stimme zu", "Einverstanden",
    # ES
    "Aceptar todo", "Aceptar todas", "Aceptar", "Acepto",
    # IT
    "Accetta tutto", "Accetta tutti", "Accetta", "Accetto",
]


# ────────────────────────────────────────────────────────────────
# Extraction code loader — reuse spatial_capture_v9.js
# ────────────────────────────────────────────────────────────────

def load_extraction_code() -> str:
    """Extract the inner body of `extractPerceptionTree()` → `page.evaluate(() => {...})`."""
    code = SPATIAL_JS.read_text()
    start_marker = "async function extractPerceptionTree() {"
    idx = code.find(start_marker)
    if idx < 0:
        raise RuntimeError("extractPerceptionTree not found in spatial_capture_v9.js")
    # Find matching closing brace
    brace = 0
    started = False
    end = -1
    for i in range(idx, len(code)):
        if code[i] == "{":
            brace += 1
            started = True
        elif code[i] == "}":
            brace -= 1
        if started and brace == 0:
            end = i + 1
            break
    fn_body = code[idx:end]
    eval_start = fn_body.find("return await page.evaluate(() => {")
    if eval_start < 0:
        raise RuntimeError("page.evaluate() not found inside extractPerceptionTree")
    eval_code_start = eval_start + len("return await page.evaluate(() => {")
    brace = 1
    eval_end = -1
    for i in range(eval_code_start, len(fn_body)):
        if fn_body[i] == "{":
            brace += 1
        elif fn_body[i] == "}":
            brace -= 1
        if brace == 0:
            eval_end = i
            break
    return fn_body[eval_code_start:eval_end]


# ────────────────────────────────────────────────────────────────
# Popup close helpers (JavaScript executed in page context)
# ────────────────────────────────────────────────────────────────

CLICK_COOKIE_JS = """
async (payload) => {
    const selectors = payload.selectors;
    const texts = payload.texts;
    let clicked = null;

    // Helper: try selectors + text in a given root (document or iframe doc)
    const tryRoot = (root) => {
        // Try selectors first
        for (const sel of selectors) {
            try {
                const el = root.querySelector(sel);
                if (el && el.offsetParent !== null) {
                    el.click();
                    return {via: 'selector', selector: sel};
                }
            } catch (e) {}
        }
        // Text fallback
        try {
            const buttons = Array.from(root.querySelectorAll('button, a[role="button"], input[type="submit"], [role="button"]'));
            for (const b of buttons) {
                const t = (b.innerText || b.value || b.textContent || '').trim().toLowerCase();
                if (!t || t.length > 60) continue;
                for (const target of texts) {
                    if (t === target.toLowerCase() || t.includes(target.toLowerCase())) {
                        try { b.click(); return {via: 'text', match: t.slice(0, 60)}; } catch (e) {}
                    }
                }
            }
        } catch (e) {}
        return null;
    };

    // V21.A — Try main document first
    clicked = tryRoot(document);

    // V21.A — Try same-origin iframes (Didomi/OneTrust often run in iframes)
    if (!clicked) {
        const iframes = Array.from(document.querySelectorAll('iframe'));
        for (const ifr of iframes) {
            try {
                const idoc = ifr.contentDocument || (ifr.contentWindow && ifr.contentWindow.document);
                if (idoc) {
                    const c = tryRoot(idoc);
                    if (c) { clicked = {...c, in_iframe: true, iframe_src: (ifr.src || '').slice(0, 120)}; break; }
                }
            } catch (e) {}  // cross-origin iframe — can't access
        }
    }

    // V21.A — Try shadow DOM (some CMPs use shadow root)
    if (!clicked) {
        try {
            const allEls = document.querySelectorAll('*');
            for (const el of allEls) {
                if (el.shadowRoot) {
                    const c = tryRoot(el.shadowRoot);
                    if (c) { clicked = {...c, in_shadow: true}; break; }
                }
            }
        } catch (e) {}
    }

    return clicked;
}
"""

FORCE_REMOVE_BANNERS_JS = """
() => {
    const KEYWORDS = /cookie|consent|rgpd|gdpr|politique de confidentialit|vie priv|newsletter|preferences|accepter|refuser|j.?accepte|consentement/i;
    let removed = 0;
    const walk = function*(root) {
        const stack = [root];
        while (stack.length) {
            const n = stack.pop();
            if (!n) continue;
            yield n;
            if (n.shadowRoot) stack.push(n.shadowRoot);
            if (n.children) for (const c of n.children) stack.push(c);
        }
    };
    for (const el of walk(document.documentElement)) {
        if (!(el instanceof Element)) continue;
        let s;
        try { s = getComputedStyle(el); } catch (e) { continue; }
        if (!s) continue;
        // Accept fixed, sticky, OR absolute with high z-index (>= 100)
        const isFixedLike = s.position === 'fixed' || s.position === 'sticky';
        const zi = parseInt(s.zIndex, 10);
        const isFloating = s.position === 'absolute' && !Number.isNaN(zi) && zi >= 100;
        if (!isFixedLike && !isFloating) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 200 || r.height < 60) continue;
        // Skip if element is the body or main wrapper (keyword may appear in page content)
        if (el === document.body || el === document.documentElement) continue;
        // Skip if element is too large (likely full-page wrapper)
        if (r.width > window.innerWidth * 0.95 && r.height > window.innerHeight * 0.9) continue;
        const txt = (el.innerText || '').slice(0, 800);
        if (KEYWORDS.test(txt)) {
            try { el.remove(); removed++; } catch (e) {}
        }
    }
    return removed;
}
"""

CLOSE_POPUPS_JS = """
() => {
    const closeSel = [
        'button[aria-label*="close" i]',
        'button[aria-label*="fermer" i]',
        'button[class*="close" i]:not([class*="menu"])',
        '.modal-close',
        '.popup-close',
        '[data-dismiss="modal"]',
        '[aria-label="Close dialog"]',
    ];
    let closed = 0;
    closeSel.forEach(s => document.querySelectorAll(s).forEach(el => {
        try {
            const r = el.getBoundingClientRect();
            if (r.width > 10 && r.height > 10) { el.click(); closed++; }
        } catch (e) {}
    }));
    return closed;
}
"""


# V23.A — Aggressive force-remove (mode --aggressive-cmp seulement)
# Plus radical : enlève TOUT [role=dialog], [aria-modal], .modal-backdrop, et les
# overlays fixés/sticky même sans keyword (heuristique dangereuse mais ciblée
# sur les pages où les retries standards ont échoué).
FORCE_REMOVE_AGGRESSIVE_JS = """
() => {
    let removed = 0;
    // ARIA dialogs / modals
    document.querySelectorAll('[role="dialog"], [role="alertdialog"], [aria-modal="true"]').forEach(el => {
        try { el.remove(); removed++; } catch (e) {}
    });
    // Modal backdrops + cookie banner classes
    document.querySelectorAll(
        '.modal-backdrop, .modal-overlay, .modal-bg, .overlay, ' +
        '[class*="modal-backdrop" i], [class*="cookie-banner" i], ' +
        '[class*="cookie-consent" i], [class*="cookie-popup" i], ' +
        '[class*="consent-banner" i], [class*="consent-popup" i], ' +
        '[id*="cookie-banner" i], [id*="cookie-consent" i], [id*="consent-banner" i], ' +
        '[id*="cookieBanner" i], [id*="cookieConsent" i]'
    ).forEach(el => {
        try {
            const r = el.getBoundingClientRect();
            if (r.width > 100 && r.height > 30) { el.remove(); removed++; }
        } catch (e) {}
    });
    // Fixed/sticky overlays anywhere on screen (no keyword filter — aggressive)
    document.querySelectorAll('*').forEach(el => {
        try {
            const s = getComputedStyle(el);
            if (s.position !== 'fixed' && s.position !== 'sticky') return;
            const r = el.getBoundingClientRect();
            // Bottom 30% or top 25% banners are the typical popup/cookie zones
            const isBanner = (r.bottom > window.innerHeight * 0.7 && r.height > 50 && r.width > window.innerWidth * 0.5)
                          || (r.top < window.innerHeight * 0.25 && r.height > 60 && r.width > window.innerWidth * 0.5);
            if (!isBanner) return;
            // Avoid removing main nav: must NOT contain primary nav links
            const txt = (el.innerText || '').slice(0, 400).toLowerCase();
            if (/^(home|accueil|menu|profile|login|sign in|connexion|s.?inscrire)/.test(txt.trim())) return;
            // Looks like a banner-zone overlay → remove
            el.style.display = 'none';
            removed++;
        } catch (e) {}
    });
    // Body/html overflow restore (sometimes locked by modals)
    try { document.body.style.overflow = ''; document.documentElement.style.overflow = ''; } catch (e) {}
    return removed;
}
"""

# V23.A — Scroll-then-back, helps reveal lazy CMPs that only appear after user interaction
SCROLL_INTERACT_JS = """
async () => {
    window.scrollTo({ top: 300, behavior: 'instant' });
    await new Promise(r => setTimeout(r, 600));
    window.scrollTo({ top: 0, behavior: 'instant' });
    await new Promise(r => setTimeout(r, 400));
    // Synthetic mouse move to trigger user-interaction-gated CMPs
    document.dispatchEvent(new MouseEvent('mousemove', { clientX: 100, clientY: 100, bubbles: true }));
    return true;
}
"""

SCAN_POPUP_SIGNATURES_JS = """
() => {
    // Look for fixed/sticky elements with popup keywords and measurable size.
    const KEYWORDS = /cookie|consentement|accepter|politique de confidentialit|newsletter|s'inscr/i;
    const candidates = [];
    const walk = function*(root) {
        const stack = [root];
        while (stack.length) {
            const n = stack.pop();
            if (!n) continue;
            yield n;
            if (n.shadowRoot) stack.push(n.shadowRoot);
            if (n.children) for (const c of n.children) stack.push(c);
        }
    };
    for (const el of walk(document.documentElement)) {
        if (!(el instanceof Element)) continue;
        let s; try { s = getComputedStyle(el); } catch(e) { continue; }
        if (!s) continue;
        if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < 0.05) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 150 || r.height < 50) continue;
        if (s.position !== 'fixed' && s.position !== 'sticky' && s.position !== 'absolute') continue;
        const txt = (el.innerText || '').slice(0, 500);
        if (KEYWORDS.test(txt) && txt.length > 20) {
            candidates.push({
                tag: el.tagName.toLowerCase(),
                text_preview: txt.slice(0, 200),
                bbox: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                position: s.position,
                z_index: s.zIndex,
            });
            if (candidates.length >= 10) break;
        }
    }
    return candidates;
}
"""

SCROLL_TO_BOTTOM_JS = """
async () => {
    // Scroll to bottom slowly to trigger lazy-load, then return to top.
    const totalHeight = document.documentElement.scrollHeight;
    const step = Math.min(600, Math.floor(window.innerHeight * 0.8));
    let y = 0;
    while (y < totalHeight) {
        y += step;
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 250));
    }
    await new Promise(r => setTimeout(r, 1000));
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 500));
    return document.documentElement.scrollHeight;
}
"""


# ────────────────────────────────────────────────────────────────
# Per-viewport capture routine
# ────────────────────────────────────────────────────────────────

async def capture_one_viewport(browser, url: str, viewport: str, out_dir: pathlib.Path,
                                extraction_code: str, timeout_ms: int = 60000) -> dict:
    """Capture all screenshots and DOM for one viewport."""
    vp = VIEWPORTS[viewport]
    ss_dir = out_dir / "screenshots"
    ss_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "viewport": viewport,
        "viewport_size": {"w": vp["width"], "h": vp["height"], "scale": vp["device_scale"]},
        "stages": [],
        "errors": [],
        "popup_close": {"attempted": False, "method": None, "verified_clean": False},
        "popup_signatures_after_close": [],
        "page_height": None,
        "timing_ms": {},
    }

    context = await browser.new_context(
        viewport={"width": vp["width"], "height": vp["height"]},
        device_scale_factor=vp["device_scale"],
        user_agent=vp["user_agent"],
        is_mobile=vp["is_mobile"],
        has_touch=vp["is_mobile"],
        locale="fr-FR",
        timezone_id="Europe/Paris",
        bypass_csp=True,
    )

    # Stealth shims
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en-US', 'en'] });
        window.chrome = { runtime: {} };
    """)

    page = await context.new_page()
    page.set_default_timeout(timeout_ms)
    page.set_default_navigation_timeout(timeout_ms)

    try:
        t0 = time.time()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as e:
            # Retry with load (some sites block goto timeout artificially)
            result["errors"].append({"stage": "navigate", "msg": str(e)[:200]})
            await page.goto(url, wait_until="load", timeout=timeout_ms)
        await page.wait_for_timeout(2000)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        result["timing_ms"]["nav"] = int((time.time() - t0) * 1000)
        result["stages"].append("navigate")

        # ── ASIS captures (état naturel avec popup) ─────────────
        t0 = time.time()
        await page.evaluate("() => window.scrollTo(0, 0)")
        await page.wait_for_timeout(400)
        try:
            await page.screenshot(path=str(ss_dir / f"{viewport}_asis_fold.png"), type="png")
            result["stages"].append("asis_fold")
        except Exception as e:
            result["errors"].append({"stage": "asis_fold", "msg": str(e)[:200]})
        try:
            await page.screenshot(path=str(ss_dir / f"{viewport}_asis_full.png"), type="png", full_page=True)
            result["stages"].append("asis_full")
        except Exception as e:
            result["errors"].append({"stage": "asis_full", "msg": str(e)[:200]})
        result["timing_ms"]["asis"] = int((time.time() - t0) * 1000)

        # ── Pre-close signature scan (baseline) ─────────────────
        try:
            pre_signatures = await page.evaluate(SCAN_POPUP_SIGNATURES_JS)
            result["popup_signatures_before_close"] = pre_signatures
        except Exception as e:
            result["errors"].append({"stage": "scan_pre", "msg": str(e)[:200]})

        # ── CLOSE popups (accept cookies + close banners) — V21.A retry loop ───
        result["popup_close"]["attempted"] = True
        result["popup_close"]["attempts"] = []

        async def _try_click_cookie():
            try:
                return await page.evaluate(
                    CLICK_COOKIE_JS,
                    {"selectors": COOKIE_SELECTORS, "texts": COOKIE_TEXTS_FR}
                )
            except Exception as e:
                result["errors"].append({"stage": "cookie_accept", "msg": str(e)[:200]})
                return None

        # First attempt — immediate
        clicked = await _try_click_cookie()
        result["popup_close"]["attempts"].append({"delay_ms": 0, "result": clicked})
        if clicked:
            result["popup_close"]["method"] = clicked
            await page.wait_for_timeout(800)

        # V21.A — Retry after extra delay (for late-firing CMPs : OneTrust async, Didomi delay)
        if not clicked:
            await page.wait_for_timeout(2500)
            clicked = await _try_click_cookie()
            result["popup_close"]["attempts"].append({"delay_ms": 2500, "result": clicked})
            if clicked:
                result["popup_close"]["method"] = clicked
                await page.wait_for_timeout(800)

        # V21.A — Third try after even longer delay (some CMPs > 4s on slow connections)
        if not clicked:
            await page.wait_for_timeout(2500)
            clicked = await _try_click_cookie()
            result["popup_close"]["attempts"].append({"delay_ms": 5000, "result": clicked})
            if clicked:
                result["popup_close"]["method"] = clicked
                await page.wait_for_timeout(800)

        # V23.A — Aggressive 4th try (only if AGGRESSIVE_CMP=1 env): scroll-interact + 8s delay + retry
        if not clicked and config.is_aggressive_cmp():
            try:
                await page.evaluate(SCROLL_INTERACT_JS)
            except Exception:
                pass
            await page.wait_for_timeout(3000)  # +5s already passed → total 8s+
            clicked = await _try_click_cookie()
            result["popup_close"]["attempts"].append({"delay_ms": 8000, "result": clicked, "aggressive": True})
            if clicked:
                result["popup_close"]["method"] = clicked
                await page.wait_for_timeout(800)

        try:
            closed = await page.evaluate(CLOSE_POPUPS_JS)
            if closed:
                result["popup_close"]["popup_close_count"] = closed
                await page.wait_for_timeout(400)
        except Exception as e:
            result["errors"].append({"stage": "close_popups", "msg": str(e)[:200]})

        # ── Post-close verification ─────────────────────────────
        try:
            post_signatures = await page.evaluate(SCAN_POPUP_SIGNATURES_JS)
            result["popup_signatures_after_close"] = post_signatures
            # Force-remove if signatures persist
            if post_signatures:
                removed = await page.evaluate(FORCE_REMOVE_BANNERS_JS)
                result["popup_close"]["force_removed"] = removed
                await page.wait_for_timeout(400)
                # Re-scan after force-remove
                post_signatures = await page.evaluate(SCAN_POPUP_SIGNATURES_JS)
                result["popup_signatures_after_close"] = post_signatures
                # V23.A — If still present AND AGGRESSIVE_CMP=1, escalate to brutal removal
                if post_signatures and config.is_aggressive_cmp():
                    aggr_removed = await page.evaluate(FORCE_REMOVE_AGGRESSIVE_JS)
                    result["popup_close"]["aggressive_removed"] = aggr_removed
                    await page.wait_for_timeout(400)
                    post_signatures = await page.evaluate(SCAN_POPUP_SIGNATURES_JS)
                    result["popup_signatures_after_close"] = post_signatures
            result["popup_close"]["verified_clean"] = not bool(post_signatures)
        except Exception as e:
            result["errors"].append({"stage": "scan_post", "msg": str(e)[:200]})

        result["stages"].append("popup_close")

        # ── Lazy-load priming (scroll full + back to top) ───────
        t0 = time.time()
        try:
            page_height = await page.evaluate(SCROLL_TO_BOTTOM_JS)
            result["page_height"] = page_height
            # Extra networkidle after scroll for late lazy loads
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            result["stages"].append("lazy_load_prime")
        except Exception as e:
            result["errors"].append({"stage": "scroll", "msg": str(e)[:200]})
        result["timing_ms"]["scroll"] = int((time.time() - t0) * 1000)

        # ── CLEAN captures (popup fermé + lazy-load déclenché) ──
        t0 = time.time()
        await page.evaluate("() => window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        try:
            await page.screenshot(path=str(ss_dir / f"{viewport}_clean_fold.png"), type="png")
            result["stages"].append("clean_fold")
        except Exception as e:
            result["errors"].append({"stage": "clean_fold", "msg": str(e)[:200]})
        try:
            await page.screenshot(path=str(ss_dir / f"{viewport}_clean_full.png"), type="png", full_page=True)
            result["stages"].append("clean_full")
        except Exception as e:
            result["errors"].append({"stage": "clean_full", "msg": str(e)[:200]})
        result["timing_ms"]["clean"] = int((time.time() - t0) * 1000)

        # ── Extract DOM spatial tree (only on desktop — one source of truth) ─
        # Mobile has different DOM (responsive), we capture it for mobile bbox
        # but keep desktop as canonical.
        t0 = time.time()
        try:
            wrapped = f"(async () => {{ {extraction_code} }})()"
            tree = await page.evaluate(wrapped)
            (out_dir / f"spatial_v10_{viewport}.json").write_text(
                json.dumps(tree, ensure_ascii=False, indent=2)
            )
            result["stages"].append("spatial_tree")
            result["spatial_elements"] = sum(len(s.get("elements", [])) for s in tree.get("sections", []))
        except Exception as e:
            result["errors"].append({"stage": "spatial_tree", "msg": str(e)[:300]})
        result["timing_ms"]["extract"] = int((time.time() - t0) * 1000)

    finally:
        await context.close()

    return result


# ────────────────────────────────────────────────────────────────
# Main orchestrator
# ────────────────────────────────────────────────────────────────

async def capture_page(url: str, client: str, page_type: str, viewports: Optional[list] = None) -> dict:
    """Full capture for one page across viewports."""
    from playwright.async_api import async_playwright

    if viewports is None:
        viewports = ["desktop", "mobile"]

    out_dir = CAPTURES / client / page_type
    out_dir.mkdir(parents=True, exist_ok=True)

    extraction_code = load_extraction_code()

    meta = {
        "url": url,
        "client": client,
        "page_type": page_type,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "viewports": {},
        "version": "v20_capture_v2",
    }

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
            ],
        )
        try:
            for vp in viewports:
                print(f"  → {client}/{page_type} @ {vp} ...")
                vp_result = await capture_one_viewport(browser, url, vp, out_dir, extraction_code)
                meta["viewports"][vp] = vp_result
                popup_state = vp_result.get("popup_close", {})
                if popup_state.get("verified_clean"):
                    print(f"    ✓ popup fermé ({popup_state.get('method')})")
                elif popup_state.get("attempted"):
                    print(f"    ⚠ popup NON vérifié clean ({len(vp_result.get('popup_signatures_after_close', []))} signatures restantes)")
                if vp_result.get("errors"):
                    print(f"    ⚠ {len(vp_result['errors'])} erreurs : {[e['stage'] for e in vp_result['errors']][:5]}")
        finally:
            await browser.close()

    # Write unified meta
    (out_dir / "capture_v2_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

async def _batch_runner(entries: list, viewports: list, max_concurrent: int, skip_done: bool) -> None:
    """V21.A — Parallel batch runner with semaphore + skip-if-done."""
    sem = asyncio.Semaphore(max_concurrent)
    total = len(entries)
    done_count = 0
    skipped_count = 0
    failed_count = 0
    lock = asyncio.Lock()

    async def _process(idx: int, e: dict):
        nonlocal done_count, skipped_count, failed_count
        async with sem:
            client = e["client"]
            page = e["page"]
            url = e["url"]
            out_dir = CAPTURES / client / page
            meta_path = out_dir / "capture_v2_meta.json"

            # Skip-if-done : skip when capture_v2_meta exists AND verified clean (V21.A)
            if skip_done and meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                    all_clean = all(
                        v.get("popup_close", {}).get("verified_clean") is True
                        for v in (meta.get("viewports") or {}).values()
                    )
                    if all_clean:
                        async with lock:
                            skipped_count += 1
                            done_count += 1
                            print(f"[{done_count}/{total}] ⏭  SKIP (already clean): {client}/{page}")
                        return
                except Exception:
                    pass

            print(f"[{idx + 1}/{total}] === {client}/{page} → {url} ===")
            try:
                await capture_page(url, client, page, viewports)
                async with lock:
                    done_count += 1
                    print(f"[{done_count}/{total}] ✓ done: {client}/{page}")
            except Exception as exc:
                async with lock:
                    failed_count += 1
                    done_count += 1
                    print(f"[{done_count}/{total}] ❌ failed {client}/{page}: {str(exc)[:120]}")

    tasks = [asyncio.create_task(_process(i, e)) for i, e in enumerate(entries)]
    await asyncio.gather(*tasks, return_exceptions=True)

    print("\n═══ Batch summary ═══")
    print(f"  Total      : {total}")
    print(f"  Skipped    : {skipped_count}")
    print(f"  Captured   : {total - skipped_count - failed_count}")
    print(f"  Failed     : {failed_count}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--client")
    ap.add_argument("--page", default="home")
    ap.add_argument("--viewports", default="desktop,mobile",
                    help="Comma-separated list of viewports (desktop, mobile, tablet)")
    ap.add_argument("--batch", help="Path to JSON file : [{url, client, page}]")
    ap.add_argument("--max-concurrent", type=int, default=1,
                    help="V21.A — Max concurrent page captures in batch mode (default 1, recommended 4-6)")
    ap.add_argument("--skip-done", action="store_true",
                    help="V21.A — Skip pages that already have a clean capture_v2_meta.json")
    ap.add_argument("--no-skip-done", dest="skip_done", action="store_false")
    ap.set_defaults(skip_done=True)
    args = ap.parse_args()

    viewports = [v.strip() for v in args.viewports.split(",") if v.strip()]

    if args.batch:
        entries = json.loads(pathlib.Path(args.batch).read_text())
        asyncio.run(_batch_runner(entries, viewports, args.max_concurrent, args.skip_done))
        return

    if not args.url or not args.client:
        ap.error("--url and --client required (or use --batch)")
    asyncio.run(capture_page(args.url, args.client, args.page, viewports))


if __name__ == "__main__":
    main()
