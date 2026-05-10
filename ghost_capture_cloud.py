#!/usr/bin/env python3
"""
ghost_capture_cloud.py — Moteur de capture cloud-native (Python Playwright).

Remplace ghost_capture.js (Node) par une version Python pure qui supporte
à la fois le mode local (Chromium embarqué) et le mode cloud (navigateur
distant via WebSocket — Browserless.io, Steel, BrowserBase, etc.).

ZERO dépendance Node.js — tout le pipeline GrowthCRO est désormais Python pur.

Modes :
    LOCAL  : Lance Chromium localement (pip install playwright && playwright install chromium)
    CLOUD  : Se connecte à un navigateur distant via WebSocket
             (env BROWSER_WS_ENDPOINT=wss://chrome.browserless.io?token=XXX)

Le code JavaScript d'extraction (spatial_capture_v9.js) tourne dans le NAVIGATEUR
via page.evaluate() — identique qu'on soit en local ou cloud.

Usage :
    # Mode local (comme ghost_capture.js)
    python3 ghost_capture_cloud.py --url https://japhy.fr --label japhy --page-type home

    # Mode cloud (Browserless.io)
    BROWSER_WS_ENDPOINT="wss://chrome.browserless.io?token=XXX" \\
    python3 ghost_capture_cloud.py --url https://japhy.fr --label japhy --page-type home --cloud

    # Batch mode
    python3 ghost_capture_cloud.py --batch tasks.json --cloud --concurrency 3

    # Dry-run
    python3 ghost_capture_cloud.py --url https://japhy.fr --label japhy --dry-run

Output identique à ghost_capture.js :
    <out-dir>/
    ├── spatial_v9.json          (bbox clusters + perception tree)
    ├── page.html                (DOM rendered complet)
    └── screenshots/
        ├── spatial_fold_desktop.png
        ├── spatial_fold_mobile.png
        ├── spatial_full_page.png
        └── spatial_annotated_desktop.png

v1.0 — 2026-04-17 (pivot cloud-native, remplacement ghost_capture.js)
"""

import argparse
import json
import os
import pathlib
import random
import re
import sys
import time
from typing import Optional

# ══════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════
ROOT = pathlib.Path(__file__).resolve().parent
from growthcro.config import config
SPATIAL_V9_JS = ROOT / "skills" / "site-capture" / "references" / "spatial_capture_v9.js"


# ══════════════════════════════════════════════════════════════
# JAVASCRIPT EXTRACTION CODE LOADER
# ══════════════════════════════════════════════════════════════
def load_extraction_js() -> str:
    """
    Charge le code JavaScript d'extraction depuis spatial_capture_v9.js.
    Ce code tourne dans le NAVIGATEUR via page.evaluate() — c'est du JS
    pur qui ne dépend ni de Node ni de Python.

    Extrait le corps de extractPerceptionTree() → page.evaluate(() => { ... })
    """
    if not SPATIAL_V9_JS.exists():
        print(f"  ⚠️  spatial_capture_v9.js introuvable à {SPATIAL_V9_JS}")
        print(f"      La capture spatiale sera dégradée (pas de perception tree)")
        return ""

    code = SPATIAL_V9_JS.read_text(encoding="utf-8")

    # Find extractPerceptionTree function
    start_marker = "async function extractPerceptionTree() {"
    start_idx = code.find(start_marker)
    if start_idx == -1:
        print("  ⚠️  extractPerceptionTree non trouvé dans spatial_capture_v9.js")
        return ""

    # Find matching closing brace
    brace_count = 0
    found_start = False
    extract_end = -1
    for i in range(start_idx, len(code)):
        if code[i] == "{":
            brace_count += 1
            found_start = True
        if code[i] == "}":
            brace_count -= 1
        if found_start and brace_count == 0:
            extract_end = i + 1
            break

    fn_body = code[start_idx:extract_end]

    # Find the evaluate callback body
    eval_marker = "return await page.evaluate(() => {"
    eval_start = fn_body.find(eval_marker)
    if eval_start == -1:
        print("  ⚠️  page.evaluate non trouvé dans extractPerceptionTree")
        return ""

    eval_code_start = eval_start + len(eval_marker)
    eval_brace_count = 1
    eval_end = -1
    for i in range(eval_code_start, len(fn_body)):
        if fn_body[i] == "{":
            eval_brace_count += 1
        if fn_body[i] == "}":
            eval_brace_count -= 1
        if eval_brace_count == 0:
            eval_end = i
            break

    return fn_body[eval_code_start:eval_end]


# ══════════════════════════════════════════════════════════════
# STEALTH INIT SCRIPT (injected before every page load)
# ══════════════════════════════════════════════════════════════
STEALTH_JS = """
() => {
    // ═══════════════════════════════════════════════════════════
    // STEALTH v2 — Anti-detection militaire
    // Basé sur puppeteer-extra-plugin-stealth + playwright-stealth
    // Cible : CloudFlare, DataDome, Akamai, PerimeterX, CloudFront
    // ═══════════════════════════════════════════════════════════

    // 1. navigator.webdriver — le test #1 de tous les anti-bots
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    // Aussi supprimer la propriété du prototype
    delete Object.getPrototypeOf(navigator).webdriver;

    // 2. Chrome runtime — simuler un vrai Chrome (pas headless)
    window.chrome = {
        runtime: {
            onConnect: { addListener: function() {} },
            onMessage: { addListener: function() {} },
            sendMessage: function() {},
            connect: function() { return { onMessage: { addListener: function() {} } }; }
        },
        loadTimes: function() { return {}; },
        csi: function() { return {}; },
    };

    // 3. Plugins — simuler des vrais plugins Chrome (PDF viewer etc.)
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1 },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', length: 1 },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '', length: 2 },
            ];
            plugins.refresh = () => {};
            return plugins;
        }
    });

    // 4. Languages — French locale
    Object.defineProperty(navigator, 'languages', {
        get: () => ['fr-FR', 'fr', 'en-US', 'en']
    });

    // 5. Platform — Mac par défaut (le plus commun en France luxury)
    Object.defineProperty(navigator, 'platform', {
        get: () => 'MacIntel'
    });

    // 6. Hardware concurrency — simuler un vrai Mac
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8
    });

    // 7. Device memory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8
    });

    // 8. Permissions API — répondre comme un vrai navigateur
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);

    // 9. WebGL — simuler un vrai GPU (les anti-bots fingerprint le WebGL)
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';           // UNMASKED_VENDOR_WEBGL
        if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
        return getParameter.call(this, parameter);
    };

    // 10. Canvas fingerprint — ajouter du bruit imperceptible
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png') {
            const ctx = this.getContext('2d');
            if (ctx) {
                const style = ctx.fillStyle;
                ctx.fillStyle = 'rgba(0,0,0,0.001)';
                ctx.fillRect(0, 0, 1, 1);
                ctx.fillStyle = style;
            }
        }
        return toDataURL.apply(this, arguments);
    };

    // 11. Connection API — simuler une connexion Wi-Fi domestique
    if (navigator.connection) {
        Object.defineProperty(navigator.connection, 'rtt', { get: () => 50 });
        Object.defineProperty(navigator.connection, 'downlink', { get: () => 10 });
        Object.defineProperty(navigator.connection, 'effectiveType', { get: () => '4g' });
    }

    // 12. Headless detection — plusieurs tests utilisés par les anti-bots
    // Notification constructor
    try {
        const notifPerm = Notification.permission;
    } catch(e) {}

    // 13. iframe contentWindow — test classique anti-headless
    try {
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                return window;
            }
        });
    } catch(e) {}

    // 14. Date.getTimezoneOffset — cohérent avec locale FR
    // (Europe/Paris = UTC+1 en hiver, UTC+2 en été)
    // Ne pas override — laisser le système local

    // 15. Media devices — simuler micro + caméra
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const origEnum = navigator.mediaDevices.enumerateDevices;
        navigator.mediaDevices.enumerateDevices = async () => {
            const devices = await origEnum.call(navigator.mediaDevices);
            if (devices.length === 0) {
                return [
                    { deviceId: 'default', kind: 'audioinput', label: '', groupId: 'default' },
                    { deviceId: 'default', kind: 'videoinput', label: '', groupId: 'default' },
                    { deviceId: 'default', kind: 'audiooutput', label: '', groupId: 'default' },
                ];
            }
            return devices;
        };
    }
}
"""

# ══════════════════════════════════════════════════════════════
# COOKIE BANNER HANDLING (in-browser JavaScript)
# ══════════════════════════════════════════════════════════════
COOKIE_CLICK_JS = """
() => {
    const texts = ['Tout accepter', "J'accepte", 'Accepter', 'Accept all', 'I agree', 'Accept cookies'];
    const buttons = Array.from(document.querySelectorAll('button, a[role="button"]'));
    for (const b of buttons) {
        const t = (b.innerText || '').trim();
        if (texts.some(x => t.toLowerCase().includes(x.toLowerCase()))) {
            b.click();
            return true;
        }
    }
    return false;
}
"""

COOKIE_FORCE_REMOVE_JS = """
() => {
    const KEYWORDS = /cookie|consent|rgpd|gdpr|politique de confidentialit|vie priv/i;
    let removed = 0;
    const walk = function* (root) {
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
        let s; try { s = getComputedStyle(el); } catch (e) { continue; }
        if (!s || (s.position !== 'fixed' && s.position !== 'sticky')) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 200 || r.height < 60) continue;
        const txt = (el.innerText || '').slice(0, 800);
        if (KEYWORDS.test(txt)) { try { el.remove(); removed++; } catch (e) {} }
    }
    return removed;
}
"""

CLOSE_POPUPS_JS = """
() => {
    const closeSel = [
        'button[aria-label*="close" i]', 'button[class*="close" i]',
        '.modal-close', '.popup-close'
    ];
    closeSel.forEach(s =>
        document.querySelectorAll(s).forEach(el => { try { el.click(); } catch (e) {} })
    );
}
"""

# ══════════════════════════════════════════════════════════════
# ANNOTATED SCREENSHOT (in-browser JavaScript)
# ══════════════════════════════════════════════════════════════
ANNOTATE_JS = """
() => {
    const overlay = document.createElement('div');
    overlay.id = '__growthcro_annotations__';
    overlay.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 999999;';
    document.body.appendChild(overlay);

    function drawBox(rect, color, label, style = 'solid') {
        const box = document.createElement('div');
        box.style.cssText = `
            position: absolute;
            left: ${rect.x}px; top: ${rect.y}px;
            width: ${rect.w || rect.width}px; height: ${rect.h || rect.height}px;
            border: 3px ${style} ${color};
            border-radius: 4px;
            pointer-events: none;
            z-index: 999999;
        `;
        if (label) {
            const tag = document.createElement('div');
            tag.style.cssText = `
                position: absolute; top: -22px; left: -2px;
                background: ${color}; color: #fff;
                font: bold 10px system-ui; padding: 2px 6px;
                border-radius: 3px 3px 0 0;
                white-space: nowrap;
            `;
            tag.textContent = label;
            box.appendChild(tag);
        }
        overlay.appendChild(box);
    }

    // H1
    const h1 = document.querySelector('h1');
    if (h1) {
        const r = h1.getBoundingClientRect();
        const fontSize = parseFloat(getComputedStyle(h1).fontSize);
        const color = fontSize >= 32 ? '#7cf0c4' : '#ffa032';
        drawBox({ x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
            color, `H1 · ${Math.round(fontSize)}px`);
    }

    // Primary CTA
    const ctaCandidates = Array.from(document.querySelectorAll('a, button')).filter(el => {
        try {
            const r = el.getBoundingClientRect();
            if (r.height < 20 || r.width < 60) return false;
            if (r.top > 900) return false;
            const s = getComputedStyle(el);
            const bg = s.backgroundColor;
            const hasColor = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
            const text = (el.textContent || '').trim();
            const isNav = el.closest('nav, header [class*="nav"], [role="navigation"]');
            return (hasColor || el.tagName === 'BUTTON') && text.length > 1 && text.length < 60 && !isNav;
        } catch (e) { return false; }
    });

    if (ctaCandidates.length > 0) {
        const scored = ctaCandidates.map(el => {
            const r = el.getBoundingClientRect();
            const area = r.width * r.height;
            const aboveFold = r.top < 900 ? 1 : 0;
            const isBtn = el.tagName === 'BUTTON' ? 1 : 0;
            const text = (el.textContent || '').trim().toLowerCase();
            const actionWords = ['découvrir', 'créer', 'commencer', 'essayer', 'commander', 'acheter', 'réserver', 'tester', 'obtenir', 'voir', 'je'];
            const hasAction = actionWords.some(w => text.includes(w)) ? 1 : 0;
            return { el, score: area * 0.001 + aboveFold * 100 + isBtn * 50 + hasAction * 80 };
        }).sort((a, b) => b.score - a.score);

        scored.slice(0, 3).forEach((item, i) => {
            const el = item.el;
            const r = el.getBoundingClientRect();
            const dims = `${Math.round(r.width)}×${Math.round(r.height)}px`;
            const text = (el.textContent || '').trim().slice(0, 30);
            const minOk = r.width >= 44 && r.height >= 44;
            const color = i === 0 ? (minOk ? '#7cf0c4' : '#ff8a93') : '#f5c97b';
            const label = i === 0 ? `CTA Principal · ${dims}` : `CTA ${i+1} · ${dims}`;
            drawBox(
                { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
                color, `${label} · "${text}"`, i === 0 ? 'solid' : 'dashed'
            );
        });
    }

    // Hero section
    const heroSection = document.querySelector('section, [class*="hero"], [class*="banner"], main > div:first-child');
    if (heroSection) {
        const r = heroSection.getBoundingClientRect();
        drawBox(
            { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: Math.min(r.height, 1200) },
            'rgba(143,212,255,0.5)', `Hero Section · ${Math.round(r.height)}px`, 'dashed'
        );
    }

    // Fold line
    const foldLine = document.createElement('div');
    foldLine.style.cssText = `position: absolute; top: 900px; left: 0; width: 100%; border-top: 2px dashed rgba(255,138,147,0.7); z-index: 999998; pointer-events: none;`;
    const foldLabel = document.createElement('div');
    foldLabel.style.cssText = `position: absolute; top: 900px; right: 20px; background: rgba(255,138,147,0.8); color: #fff; font: bold 11px system-ui; padding: 2px 8px; border-radius: 0 0 4px 4px; z-index: 999999;`;
    foldLabel.textContent = '▼ FOLD LINE · 900px';
    overlay.appendChild(foldLine);
    overlay.appendChild(foldLabel);

    // Hero images
    const heroImages = Array.from(document.querySelectorAll('img')).filter(img => {
        const r = img.getBoundingClientRect();
        return r.top < 900 && r.width > 100 && r.height > 60;
    }).slice(0, 3);

    heroImages.forEach((img, i) => {
        const r = img.getBoundingClientRect();
        const nat = `${img.naturalWidth}×${img.naturalHeight}`;
        const render = `${Math.round(r.width)}×${Math.round(r.height)}`;
        const isLazy = img.loading === 'lazy';
        const color = isLazy ? '#ffa032' : '#7cf0c4';
        drawBox(
            { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
            color, `IMG ${i+1} · ${render} (nat: ${nat})${isLazy ? ' · LAZY!' : ''}`, 'dashed'
        );
    });

    // Social proof
    const trustSelectors = [
        '[class*="trustpilot"]', '[class*="review"]', '[class*="avis"]',
        '[class*="rating"]', '[class*="testimonial"]', '[class*="trust"]',
        '[class*="social-proof"]', 'iframe[src*="trustpilot"]'
    ];
    trustSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            try {
                const r = el.getBoundingClientRect();
                if (r.width < 50 || r.height < 20) return;
                const yPct = Math.round((r.top + window.scrollY) / document.body.scrollHeight * 100);
                drawBox(
                    { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
                    '#b7a4ff', `Social Proof · ${yPct}% page`, 'dashed'
                );
            } catch (e) {}
        });
    });
}
"""

REMOVE_ANNOTATIONS_JS = """
() => {
    const overlay = document.getElementById('__growthcro_annotations__');
    if (overlay) overlay.remove();
    document.querySelectorAll('[style*="999998"], [style*="999999"]').forEach(el => {
        if (el.id !== '__growthcro_annotations__') { try { el.remove(); } catch(e) {} }
    });
}
"""


# ══════════════════════════════════════════════════════════════
# BRIGHT DATA SCRAPING BROWSER
# ══════════════════════════════════════════════════════════════
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
        endpoint = ws_endpoint or config.browser_ws_endpoint()
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
# COOKIE HANDLING
# ══════════════════════════════════════════════════════════════
async def handle_cookies(page):
    """Accepte les cookie banners et ferme les popups."""
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


# ══════════════════════════════════════════════════════════════
# SINGLE PAGE CAPTURE
# ══════════════════════════════════════════════════════════════
async def capture_page(
    browser,
    url: str,
    label: str,
    page_type: str,
    out_dir: pathlib.Path,
    timeout: int = 120000,
    extraction_js: str = "",
    _is_brightdata_retry: bool = False,
) -> dict:
    """
    Capture une page complète — identique à ghost_capture.js capturePage().

    Produit :
        - spatial_v9.json (perception tree + bbox clusters)
        - page.html (DOM rendered complet)
        - screenshots/ (fold desktop, fold mobile, full page, annotated)
    """
    t0 = time.time()
    screenshots_dir = out_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    errors = []
    stages = []
    perception_tree = None
    completeness = 0.0

    # Create browser context with stealth settings
    context = await browser.new_context(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="fr-FR",
        timezone_id="Europe/Paris",
        java_script_enabled=True,
        bypass_csp=True,
    )

    # Inject stealth script before every page load
    await context.add_init_script(STEALTH_JS)

    page = await context.new_page()
    page.set_default_timeout(timeout)
    page.set_default_navigation_timeout(timeout)

    try:
        # ── Navigate ──
        print(f"  ⏳ Navigation vers {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=min(timeout, 60000))
        # Wait for lazy-loaded content
        await page.wait_for_timeout(3000)
        # Try networkidle (but don't block)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        stages.append("navigate")

        # ── Stage 0.5: Human behavior (anti-bot evasion) ──
        # Simuler un comportement humain : mouvements de souris, scroll progressif
        # Les anti-bots (DataDome, CloudFront) analysent les patterns de navigation
        try:
            # Mouvement de souris aléatoire
            await page.mouse.move(random.randint(100, 800), random.randint(100, 400))
            await page.wait_for_timeout(random.randint(200, 500))
            await page.mouse.move(random.randint(300, 1000), random.randint(200, 600))
            await page.wait_for_timeout(random.randint(100, 300))
            # Scroll progressif (pas d'un coup — pattern humain)
            for scroll_y in [200, 400, 300, 100, 0]:
                await page.evaluate(f"() => window.scrollTo({{top: {scroll_y}, behavior: 'smooth'}})")
                await page.wait_for_timeout(random.randint(300, 700))
        except Exception:
            pass  # Ne pas bloquer si ça échoue

        # ── Stage 1: Settle (SPA-aware) ──
        # Les SPAs lourds (Nuxt, Next, React) mettent parfois 5-10s à rendre.
        # On attend que le body ait du vrai contenu (> 100 nodes ou > 500 chars)
        # plutôt qu'un simple timeout fixe.
        for attempt in range(6):  # max 6 × 2s = 12s d'attente SPA
            body_stats = await page.evaluate("""() => {
                const body = document.body;
                if (!body) return {nodes: 0, text: 0};
                return {
                    nodes: body.querySelectorAll('*').length,
                    text: body.innerText.length
                };
            }""")
            nodes = body_stats.get("nodes", 0)
            text_len = body_stats.get("text", 0)
            if nodes > 50 or text_len > 500:
                break
            if attempt < 5:
                await page.wait_for_timeout(2000)
                # Scroll to trigger lazy rendering
                await page.evaluate("() => { window.scrollTo(0, 300); window.scrollTo(0, 0); }")
        if nodes <= 50 and text_len <= 500:
            print(f"  ⚠️  SPA lent : {nodes} nodes, {text_len} chars après {(attempt+1)*2}s d'attente")
        else:
            print(f"  ✅ Contenu rendu : {nodes} nodes, {text_len} chars")
        stages.append("settle")

        # ── 403 / Bot-block Detection + Bright Data Auto-Retry ──
        # Si la page est une erreur 403/CloudFront, on détecte et retry via Bright Data
        if not _is_brightdata_retry:
            block_check = await page.evaluate("""() => {
                const h1 = document.querySelector('h1');
                const title = document.title || '';
                const body = (document.body && document.body.innerText) || '';
                const is403 = (h1 && /403|ERROR|Forbidden|Access Denied/i.test(h1.textContent))
                    || /403 ERROR|Request blocked|Access Denied/i.test(title)
                    || (body.length < 2000 && /CloudFront|Request blocked|security service|Forbidden/i.test(body));
                return { blocked: is403, h1: h1 ? h1.textContent.trim().slice(0, 100) : '', title: title.slice(0, 100) };
            }""")
            if block_check.get("blocked"):
                bd_endpoint = get_brightdata_endpoint()
                if bd_endpoint:
                    print(f"  🚫 BLOQUÉ (403) — H1: \"{block_check.get('h1', '')}\"")
                    print(f"  🔶 Retry automatique via Bright Data Scraping Browser...")
                    await context.close()
                    # Import playwright ici pour créer une nouvelle instance
                    from playwright.async_api import async_playwright
                    async with async_playwright() as pw_bd:
                        bd_browser = await get_browser(pw_bd, cloud=False, force_brightdata=True)
                        result = await capture_page(
                            bd_browser, url, label, page_type, out_dir,
                            timeout, extraction_js, _is_brightdata_retry=True,
                        )
                        await bd_browser.close()
                        result["brightdata_retry"] = True
                        return result
                else:
                    print(f"  🚫 BLOQUÉ (403) — H1: \"{block_check.get('h1', '')}\"")
                    print(f"  ⚠️  Pas de Bright Data configuré. Pour activer le fallback automatique :")
                    print(f"      export BRIGHTDATA_AUTH='brd-customer-XXX-zone-scraping_browser:PASSWORD'")

        # ── Stage 2: Fold desktop screenshot ──
        try:
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(600)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_fold_desktop.png"), type="png"
            )
            stages.append("fold_desktop")
        except Exception as e:
            errors.append({"stage": "fold_desktop", "msg": str(e)[:200]})

        # ── Stage 2b: Fold mobile screenshot ──
        try:
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(600)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_fold_mobile.png"), type="png"
            )
            stages.append("fold_mobile")
            # Reset to desktop
            await page.set_viewport_size({"width": 1440, "height": 900})
            await page.wait_for_timeout(300)
        except Exception as e:
            errors.append({"stage": "fold_mobile", "msg": str(e)[:200]})

        # ── Stage 3: Cookie handling ──
        try:
            cookie_method = await handle_cookies(page)
            await page.wait_for_timeout(800)
            stages.append("cookie_dismiss")
            if cookie_method != "none":
                print(f"  🍪 Cookie banner handled ({cookie_method})")
        except Exception as e:
            errors.append({"stage": "cookie_dismiss", "msg": str(e)[:200]})

        # ── Stage 3.5: Deep scroll (trigger lazy-loading for SPAs) ──
        # SPAs (Nuxt, Next, Shopify Hydrogen, etc.) only render content on scroll.
        # We scroll the entire page in 800px increments, waiting for lazy content.
        try:
            total_h = await page.evaluate("() => document.body.scrollHeight")
            pos = 0
            scroll_passes = 0
            while pos < total_h and scroll_passes < 60:  # cap 60 steps (~48000px max)
                pos += 800
                await page.evaluate(f"() => window.scrollTo({{top: {pos}, behavior: 'smooth'}})")
                await page.wait_for_timeout(400)
                scroll_passes += 1
                # Page height can grow as lazy content loads
                new_h = await page.evaluate("() => document.body.scrollHeight")
                if new_h > total_h:
                    total_h = new_h
            # Scroll back to top before extraction
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(800)
            final_h = await page.evaluate("() => document.body.scrollHeight")
            final_nodes = await page.evaluate("() => document.body.querySelectorAll('*').length")
            print(f"  📜 Deep scroll: {scroll_passes} steps, {total_h}→{final_h}px, {final_nodes} nodes")
            stages.append("deep_scroll")
        except Exception as e:
            errors.append({"stage": "deep_scroll", "msg": str(e)[:200]})

        # ── Stage 4: Perception tree extraction ──
        if extraction_js:
            try:
                wrapped = f"(async () => {{ {extraction_js} }})()"
                perception_tree = await page.evaluate(wrapped)
                completeness = 0.8
                stages.append("extract")
            except Exception as e:
                errors.append({"stage": "extract", "msg": str(e)[:400]})
                print(f"  ⚠️  Extract error: {str(e)[:200]}")
        else:
            print(f"  ⚠️  Extraction JS non chargé — spatial_v9 sera vide")

        # ── Stage 5: Full page screenshot (clean) ──
        try:
            await page.set_viewport_size({"width": 1440, "height": 900})
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(400)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_full_page.png"),
                type="png",
                full_page=True,
            )
            stages.append("full_page")
        except Exception as e:
            errors.append({"stage": "full_page", "msg": str(e)[:200]})

        # ── Stage 5b: Dump rendered HTML ──
        try:
            rendered_html = await page.content()
            html_path = out_dir / "page.html"
            html_path.write_text(rendered_html, encoding="utf-8")
            html_kb = len(rendered_html) / 1024
            print(f"  💾 page.html dumped ({html_kb:.1f} KB rendered DOM)")
            stages.append("dump_html")
        except Exception as e:
            errors.append({"stage": "dump_html", "msg": str(e)[:200]})

        # ── Stage 6: Annotated screenshot ──
        try:
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(300)
            await page.evaluate(ANNOTATE_JS)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_annotated_desktop.png"),
                type="png",
                full_page=True,
            )
            await page.evaluate(REMOVE_ANNOTATIONS_JS)
            stages.append("annotated_screenshot")
        except Exception as e:
            errors.append({"stage": "annotated_screenshot", "msg": str(e)[:200]})

        # Completeness
        completeness = 1.0 if ("extract" in stages and "full_page" in stages) else 0.8

    except Exception as e:
        errors.append({"stage": "navigation", "msg": str(e)[:300]})

    # ── Build and save spatial_v9.json ──
    final_capture = {
        "meta": (perception_tree or {}).get("meta", {
            "url": url,
            "label": label,
            "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "completeness": completeness,
        }),
        "stagesCompleted": stages,
        "errors": errors,
        **(perception_tree or {}),
    }
    # Enrich meta
    final_capture["meta"]["label"] = label
    final_capture["meta"]["pageType"] = page_type
    final_capture["meta"]["engine"] = "ghost_capture_cloud.py"
    final_capture["meta"]["completeness"] = completeness

    json_path = out_dir / "spatial_v9.json"
    json_path.write_text(json.dumps(final_capture, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = time.time() - t0
    sections = len(final_capture.get("sections", []))

    await context.close()

    result = {
        "ok": len(errors) == 0 or completeness >= 0.8,
        "label": label,
        "pageType": page_type,
        "sections": sections,
        "completeness": completeness,
        "elapsed": f"{elapsed:.1f}",
        "errors": errors,
        "stages": stages,
    }
    return result


# ══════════════════════════════════════════════════════════════
# BATCH MODE
# ══════════════════════════════════════════════════════════════
async def run_batch(pw, batch_file: str, cloud: bool, ws_endpoint: str,
                    concurrency: int, delay: int, timeout: int, out_base: str):
    """Exécute un batch de captures (même API que ghost_capture.js --batch)."""
    import asyncio

    tasks = json.loads(pathlib.Path(batch_file).read_text())
    extraction_js = load_extraction_js()

    print(f"\n{'='*60}")
    print(f"GHOST CAPTURE CLOUD — BATCH MODE")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Mode: {'CLOUD' if cloud else 'LOCAL'}")
    print(f"  Concurrency: {concurrency}")
    print(f"{'='*60}\n")

    browser = await get_browser(pw, cloud, ws_endpoint)
    RESTART_EVERY = 10
    chunk_counter = 0
    results = []
    completed = 0

    for i in range(0, len(tasks), concurrency):
        # Restart browser periodically
        if chunk_counter > 0 and (chunk_counter % RESTART_EVERY == 0):
            try:
                await browser.close()
            except Exception:
                pass
            print(f"  [browser] relancement après {chunk_counter} chunks")
            browser = await get_browser(pw, cloud, ws_endpoint)

        chunk = tasks[i : i + concurrency]

        async def process_task(task):
            nonlocal completed
            task_out = pathlib.Path(task.get("outDir", f"{out_base}/{task['label']}/{task['pageType']}"))
            try:
                result = await capture_page(
                    browser, task["url"], task["label"], task["pageType"],
                    task_out, timeout, extraction_js,
                )
                completed += 1
                status = "✅" if result["ok"] else "❌"
                print(f"  [{completed}/{len(tasks)}] {status} {task['label']}/{task['pageType']}: "
                      f"{result['sections']} sections ({result['elapsed']}s)")
                return result
            except Exception as e:
                completed += 1
                print(f"  [{completed}/{len(tasks)}] ❌ {task['label']}/{task['pageType']}: {str(e)[:100]}")
                return {"ok": False, "label": task["label"], "pageType": task["pageType"], "error": str(e)[:200]}

        chunk_results = await asyncio.gather(*[process_task(t) for t in chunk])
        results.extend(chunk_results)
        chunk_counter += 1

        if i + concurrency < len(tasks):
            await asyncio.sleep(delay / 1000)

    try:
        await browser.close()
    except Exception:
        pass

    ok_count = sum(1 for r in results if r.get("ok"))
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE — {ok_count}/{len(results)} OK")
    print(f"{'='*60}\n")
    return results


# ══════════════════════════════════════════════════════════════
# SINGLE MODE
# ══════════════════════════════════════════════════════════════
async def run_single(pw, url: str, label: str, page_type: str, out_dir: str,
                     cloud: bool, ws_endpoint: str, timeout: int,
                     force_brightdata: bool = False):
    """Capture une seule page (mode par défaut)."""
    extraction_js = load_extraction_js()
    out_path = pathlib.Path(out_dir)

    if force_brightdata:
        mode_str = "BRIGHT DATA"
    elif cloud:
        mode_str = "CLOUD"
    else:
        bd_available = get_brightdata_endpoint() is not None
        mode_str = "LOCAL" + (" + Bright Data fallback" if bd_available else "")

    print(f"\n{'='*60}")
    print(f"GHOST CAPTURE CLOUD — {label}/{page_type}")
    print(f"  URL:    {url}")
    print(f"  Mode:   {mode_str}")
    print(f"  Output: {out_path}")
    print(f"{'='*60}\n")

    browser = await get_browser(pw, cloud, ws_endpoint, force_brightdata=force_brightdata)
    result = await capture_page(browser, url, label, page_type, out_path, timeout, extraction_js)
    await browser.close()

    status = "✅" if result["ok"] else "❌"
    print(f"\n{status} {result['label']}/{result['pageType']}: "
          f"{result['sections']} sections, completeness={result['completeness']} ({result['elapsed']}s)")
    if result["errors"]:
        err_parts = [f"{e['stage']}: {e['msg'][:80]}" for e in result["errors"]]
        print(f"  Errors: {'; '.join(err_parts)}")

    # Output JSON result to stdout for Python bridge (same as ghost_capture.js)
    print(f"\n__GHOST_RESULT__{json.dumps(result)}")

    return result


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Ghost Capture Cloud — Playwright Python (local + cloud browser)"
    )
    ap.add_argument("--url", help="URL à capturer")
    ap.add_argument("--label", default="capture", help="Label client")
    ap.add_argument("--page-type", default="home", help="Type de page")
    ap.add_argument("--out-dir", default="./output", help="Répertoire de sortie")
    ap.add_argument("--timeout", type=int, default=120000, help="Timeout en ms")
    ap.add_argument("--cloud", action="store_true",
                    help="Mode cloud : se connecte à BROWSER_WS_ENDPOINT (Browserless.io, etc.)")
    ap.add_argument("--ws-endpoint", default=None,
                    help="WebSocket endpoint explicite (sinon: env BROWSER_WS_ENDPOINT)")
    ap.add_argument("--brightdata", action="store_true",
                    help="Forcer Bright Data Scraping Browser (bypass tous les anti-bots)")
    ap.add_argument("--batch", help="Fichier JSON de batch [{url, label, pageType}]")
    ap.add_argument("--concurrency", type=int, default=3, help="Concurrence batch")
    ap.add_argument("--delay", type=int, default=1000, help="Délai inter-chunk en ms")
    ap.add_argument("--dry-run", action="store_true", help="Afficher sans exécuter")
    args = ap.parse_args()

    if args.dry_run:
        mode = "CLOUD" if args.cloud else "LOCAL"
        if args.batch:
            tasks = json.loads(pathlib.Path(args.batch).read_text())
            print(f"DRY RUN — {len(tasks)} tasks ({mode})")
            for t in tasks:
                print(f"  {t['label']}/{t['pageType']} → {t['url']}")
        elif args.url:
            print(f"DRY RUN — {args.label}/{args.page_type} → {args.url} ({mode})")
        return 0

    if not args.url and not args.batch:
        print("❌ Spécifie --url ou --batch")
        ap.print_help()
        return 1

    # Import playwright here (fail-fast with clear message if not installed)
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ playwright non installé.")
        print("   pip install playwright")
        print("   playwright install chromium  # (mode local uniquement)")
        print("")
        print("   En mode --cloud, seul 'pip install playwright' est requis")
        print("   (pas besoin d'installer les navigateurs — ils tournent dans le cloud)")
        return 1

    import asyncio

    async def _main():
        async with async_playwright() as pw:
            if args.batch:
                results = await run_batch(
                    pw, args.batch, args.cloud, args.ws_endpoint,
                    args.concurrency, args.delay, args.timeout, args.out_dir,
                )
                ok = sum(1 for r in results if r.get("ok"))
                return 0 if ok == len(results) else 1
            else:
                result = await run_single(
                    pw, args.url, args.label, args.page_type, args.out_dir,
                    args.cloud, args.ws_endpoint, args.timeout,
                    force_brightdata=args.brightdata,
                )
                return 0 if result["ok"] else 1

    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
