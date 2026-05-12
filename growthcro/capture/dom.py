"""Browser-side JS payloads + static-HTML cleaning helpers — single concern: DOM serialization.

Two distinct surfaces share this module:
  * Playwright capture path injects the JS constants (STEALTH_JS, COOKIE_*, ANNOTATE_JS, …)
    into the page via ``page.evaluate`` / ``page.add_init_script``.
  * Static HTML scorer (native parser) reuses ``clean`` / ``strip_scripts_styles``
    plus the parasitic-heading detection helpers to keep one canonical
    parser implementation.
"""
from __future__ import annotations

import pathlib
import re
from typing import Optional

# ══════════════════════════════════════════════════════════════
# JAVASCRIPT EXTRACTION CODE LOADER
# ══════════════════════════════════════════════════════════════
ROOT = pathlib.Path(__file__).resolve().parents[2]
SPATIAL_V9_JS = ROOT / "skills" / "site-capture" / "references" / "spatial_capture_v9.js"


def load_extraction_js() -> str:
    """
    Charge le code JavaScript d'extraction depuis spatial_capture_v9.js.
    Ce code tourne dans le NAVIGATEUR via page.evaluate() — c'est du JS
    pur qui ne dépend ni de Node ni de Python.

    Extrait le corps de extractPerceptionTree() → page.evaluate(() => { ... })
    """
    if not SPATIAL_V9_JS.exists():
        print(f"  ⚠️  spatial_capture_v9.js introuvable à {SPATIAL_V9_JS}")
        print("      La capture spatiale sera dégradée (pas de perception tree)")
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
# STATIC HTML PARSING HELPERS (used by scorer.py)
# ══════════════════════════════════════════════════════════════
def clean(text: str) -> str:
    """Remove HTML tags and decode common HTML entities."""
    import html as _html
    text = re.sub(r"<[^>]+>", "", text)
    text = _html.unescape(text)  # &nbsp; → space, &amp; → &, etc.
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text.strip()


def strip_scripts_styles(h: str) -> str:
    h = re.sub(r"<script[^>]*>.*?</script>", " ", h, flags=re.DOTALL | re.I)
    h = re.sub(r"<style[^>]*>.*?</style>", " ", h, flags=re.DOTALL | re.I)
    return h


# ── Parasitic-heading detection (used by scorer.py hero detection) ──
PARASITIC_H1_PATTERNS = re.compile(
    r"data-fera-widget|data-judge-widget|data-stamped|data-loox|"          # Review widgets
    r"data-yotpo|data-rivyo|data-ali-review|data-okendo|"                  # More review widgets
    r"widget-heading|reviews?-heading|all-reviews|tous-les-avis|"          # Generic review headings
    r"header__heading|site-header|logo-heading|brand-heading|"             # Logo/nav H1s
    r"footer__heading|footer-heading|"                                      # Footer H1s
    r"cart__heading|panier|your-cart|votre-panier|"                         # Cart drawer H1s
    r"menu__heading|drawer__heading|sidebar__heading",                      # Drawer/menu H1s
    re.I
)

HERO_CONTAINER_PATTERNS = re.compile(
    r"slideshow|hero|banner|jumbotron|masthead|splash|"
    r"cover|intro|featured|main-banner|home-banner|"
    r"slider|carousel.*hero|top-section|above-fold",
    re.I
)

PARASITIC_H2_PATTERNS = re.compile(
    r"cart|panier|drawer|sidebar|visually-hidden|sr-only|"
    r"product-tile|card-information|cross-sells?|"
    r"jdgm-|judge-?me|fera-|stamped-|yotpo-|loox-|okendo-|"
    r"footer|menu|nav-|search-result",
    re.I
)

PARASITIC_H2_TEXT = {
    "votre panier", "your cart", "panier", "cart", "recommandé pour vous",
    "recommended for you", "you may also like", "customer reviews",
    "let customers speak", "recently viewed", "search", "recherche",
    "monnaie", "currency", "tous les avis", "all reviews",
}

GENERIC_HEADING_TEXT = {
    "avis", "reviews", "tous les avis", "all reviews",
    "customer reviews", "avis clients", "panier", "cart",
    "menu", "navigation", "search", "recherche",
}


def is_parasitic_h1(h: dict, *, header_end_pos: int, body_tags: str, title: str) -> bool:
    """Determine if an H1 is NOT the real hero heading."""
    attrs = h["attrs"]
    text = h["text"]
    inner = h["inner_html"]

    # Rule 1: H1 inside <header> block (before </header>) → usually logo
    if h["pos"] < header_end_pos:
        return True

    # Rule 2: H1 with known parasitic class/data attributes
    if PARASITIC_H1_PATTERNS.search(attrs):
        return True

    # Rule 3: H1 whose text matches parasitic content
    if PARASITIC_H1_PATTERNS.search(text.lower().replace(" ", "-")):
        return True

    # Rule 4: H1 containing ONLY an image (logo H1)
    inner_stripped = re.sub(r"<[^>]+>", "", inner).strip()
    if not inner_stripped and re.search(r"<img\b", inner, re.I):
        return True

    # Rule 5: H1 text is just the brand name (< 3 words, matches <title> first word)
    if title and len(text.split()) <= 2:
        title_first = title.split()[0].lower().strip("|-–—") if title else ""
        if text.lower().strip() == title_first or len(text) < 3:
            return True

    # Rule 6: H1 very late in page — relaxed: only filter past 92% of body
    if h["pos"] > len(body_tags) * 0.92:
        return True

    # Rule 7: Very short generic text (common widget defaults)
    if text.lower().strip() in GENERIC_HEADING_TEXT:
        return True

    return False


def is_parasitic_h2(h: dict, *, header_end_pos: int) -> bool:
    """Filter out H2s that are clearly not hero content."""
    if PARASITIC_H2_PATTERNS.search(h["attrs"]):
        return True
    if h["text"].lower().strip().rstrip(".") in PARASITIC_H2_TEXT:
        return True
    if h["pos"] < header_end_pos:
        return True
    return False


def find_hero_h2_fallback(heading_raw: list, body_tags: str, *, header_end_pos: int) -> Optional[dict]:
    """Find best H2 candidate in a hero-like container."""
    # Strategy 1: H2 inside a known hero container class
    for h in heading_raw:
        if h["level"] != 2 or is_parasitic_h2(h, header_end_pos=header_end_pos):
            continue
        ctx_start = max(0, h["pos"] - 2000)
        context_before = body_tags[ctx_start:h["pos"]]
        if HERO_CONTAINER_PATTERNS.search(context_before):
            if len(h["text"]) > 10:
                return h
        if HERO_CONTAINER_PATTERNS.search(h["attrs"]):
            if len(h["text"]) > 10:
                return h

    # Strategy 2: First non-parasitic H2 in the top 40% of the page with meaningful text
    for h in heading_raw:
        if h["level"] != 2 or is_parasitic_h2(h, header_end_pos=header_end_pos):
            continue
        if h["pos"] < len(body_tags) * 0.4 and len(h["text"]) > 15:
            return h

    # Strategy 3: First non-parasitic H2 with heading-1 visual class
    for h in heading_raw:
        if h["level"] != 2 or is_parasitic_h2(h, header_end_pos=header_end_pos):
            continue
        if re.search(r"heading-1|type-heading-1|h1\b", h["attrs"], re.I):
            if len(h["text"]) > 10:
                return h

    return None
