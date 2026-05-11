#!/usr/bin/env python3
"""V25.B — Discovery + Classification intelligente (input: home_url + slug).

Workflow imparable pour onboarding propre :

  1. Sitemap fetch  : <root>/sitemap.xml + sitemap_index + robots.txt directives
  2. Crawl fallback : Playwright BFS depth=2 (header + footer nav + CTAs primaires)
                      si sitemap absent ou maigre (<10 URLs)
  3. URL filter     : enlever blog/articles/légales/PDF/feeds (regex)
  4. Health check   : HEAD/GET parallel httpx (top 60 candidates)
  5. Page sampling  : Playwright mini-DOM dump léger sur URLs alive
                      (h1, primary CTA, n_inputs, n_buttons, has_pricing_table,
                      has_quiz_radio, has_signup_form, has_pdp_signals,
                      body_word_count, thumbnail 800px)
  6. Batch classify : Haiku 4.5 batch ou sync (selon --use-batch)
                      → page_type ∈ {home, lp_leadgen, lp_sales, pricing, quiz_vsl,
                                     signup, pdp, collection, lp, faq, contact, blog, other}
                      + confidence 0-100 + reasoning
  7. Sélection      : home (toujours) + 2-4 pages haute valeur audit,
                      1 par page_type max, confidence ≥ 70%.

Output : data/captures/<client>/discovered_pages_v25.json
         (compatible avec add_client_v25.py downstream)

Usage :
    python3 discover_pages_v25.py --client japhy --url https://japhy.fr
    python3 discover_pages_v25.py --client japhy --url https://japhy.fr --max-candidates 80
    python3 discover_pages_v25.py --client japhy --url https://japhy.fr --skip-sampling
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urldefrag

ROOT = pathlib.Path(__file__).resolve().parents[3]
from growthcro.config import config
CAPTURES = ROOT / "data" / "captures"
SCRIPTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from reco_enricher_v13_api import _load_dotenv_if_needed  # noqa

MODEL = "claude-haiku-4-5-20251001"

# ────────────────────────────────────────────────────────────────
# URL filtering — exclude noise (blog, legal, feeds, assets)
# ────────────────────────────────────────────────────────────────

EXCLUDE_PATH_RE = re.compile(
    r"/blog/?|/articles?/?|/posts?/?|/news/?|/press/?|/presse/?|"
    r"/legal/?|/privacy/?|/cgv/?|/cgu/?|/conditions/?|/cookies?/?|"
    r"/mentions/?|/tos/?|/policy/?|/policies/?|/gdpr/?|/rgpd/?|"
    r"/career/?|/careers/?|/job/?|/jobs/?|/recrutement/?|/about/?|/a-propos/?|"
    r"/login/?|/auth/?|/account/?|/dashboard/?|/admin/?|/wp-admin|"
    r"/feed/?|/rss/?|/atom/?|/api/?|/_next/?|/_nuxt/?|"
    r"\.(pdf|xml|json|txt|jpg|jpeg|png|webp|svg|ico|css|js|map|woff|woff2|ttf|mp4|webm|zip)$",
    re.I,
)
INCLUDE_KEYWORDS_RE = re.compile(
    r"pricing|tarif|plan|abonnement|subscri|join|"
    r"quiz|diagnostic|profile|builder|adapt|personnalis|"
    r"essai|trial|demo|free|leadgen|gratuit|reserv|book|"
    r"sign[\s\-_]?up|register|inscription|create|"
    r"product|/p/|/pdp|/detail|item|achat|"
    r"collection|catalog|category|categorie|nos[\s\-_]?produits|/c/|"
    r"sur[\s\-_]?mesure|configur|"
    r"contact|help|faq|aide",
    re.I,
)


def _norm_url(url: str) -> str:
    url, _frag = urldefrag(url)
    return url.rstrip("/")


def _is_same_origin(url: str, root: str) -> bool:
    try:
        u_host = urlparse(url).netloc.lower().lstrip("www.")
        r_host = urlparse(root).netloc.lower().lstrip("www.")
        # Allow subdomain match (eg. shop.japhy.fr ↔ japhy.fr) — keep strict for now
        return u_host == r_host or u_host.endswith("." + r_host) or r_host.endswith("." + u_host)
    except Exception:
        return False


def _filter_url(url: str) -> bool:
    """Return True if URL is a candidate page (not excluded by regex)."""
    if EXCLUDE_PATH_RE.search(url):
        return False
    return True


# ────────────────────────────────────────────────────────────────
# Sitemap parsing
# ────────────────────────────────────────────────────────────────

async def _fetch_text(http, url: str, timeout: float = 10.0) -> Optional[str]:
    try:
        r = await http.get(url, timeout=timeout, follow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def _parse_sitemap_xml(xml_text: str) -> tuple[list[str], list[str]]:
    """Return (page_urls, sub_sitemap_urls). Handles both <urlset> and <sitemapindex>."""
    page_urls = []
    sub_sitemaps = []
    try:
        # Strip namespace for simpler parsing
        xml_no_ns = re.sub(r'xmlns="[^"]+"', "", xml_text, count=1)
        root = ET.fromstring(xml_no_ns)
    except Exception:
        return [], []
    if root.tag.endswith("urlset"):
        for url_el in root.findall(".//url"):
            loc = url_el.find("loc")
            if loc is not None and loc.text:
                page_urls.append(loc.text.strip())
    elif root.tag.endswith("sitemapindex"):
        for sm in root.findall(".//sitemap"):
            loc = sm.find("loc")
            if loc is not None and loc.text:
                sub_sitemaps.append(loc.text.strip())
    return page_urls, sub_sitemaps


async def _discover_via_sitemap(http, root_url: str) -> tuple[list[str], set[str]]:
    """Fetch sitemap.xml + sitemap_index.xml + robots.txt Sitemap: directives.
    Recurses sub-sitemaps WITHOUT origin filter (some sites split sitemaps
    across domain variants — e.g. Notion notion.so/sitemap.xml lists
    notion.com/* sub-sitemaps when the brand migrated).
    Returns (page_urls, allowed_hosts) — caller can filter using the enriched
    host set so same-brand cross-domain URLs are kept."""
    candidates = set()
    visited = set()
    allowed_hosts: set[str] = set()

    # Seed allowed_hosts with root host
    try:
        root_host = urlparse(root_url).netloc.lower().lstrip("www.")
        if root_host:
            allowed_hosts.add(root_host)
    except Exception:
        pass

    # Try common locations + robots.txt
    bases = [
        urljoin(root_url, "/sitemap.xml"),
        urljoin(root_url, "/sitemap_index.xml"),
        urljoin(root_url, "/sitemap-index.xml"),
    ]
    robots = await _fetch_text(http, urljoin(root_url, "/robots.txt"), timeout=5.0)
    if robots:
        for line in robots.splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                bases.append(line.split(":", 1)[1].strip())

    queue = list(dict.fromkeys(bases))
    iterations = 0
    while queue and iterations < 12:
        iterations += 1
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        # Track host of any sitemap we successfully read — the brand owns these
        text = await _fetch_text(http, url, timeout=10.0)
        if not text:
            continue
        try:
            sm_host = urlparse(url).netloc.lower().lstrip("www.")
            if sm_host:
                allowed_hosts.add(sm_host)
        except Exception:
            pass
        page_urls, sub_sitemaps = _parse_sitemap_xml(text)
        for u in page_urls:
            candidates.add(_norm_url(u))
        for s in sub_sitemaps:
            if s not in visited:
                queue.append(s)

    # Filter using allowed_hosts (accepts notion.so URLs AND notion.com URLs
    # when both appeared in the sitemap walk).
    def _allowed(u: str) -> bool:
        try:
            h = urlparse(u).netloc.lower().lstrip("www.")
            return h in allowed_hosts or any(h.endswith("." + a) or a.endswith("." + h) for a in allowed_hosts)
        except Exception:
            return False

    page_urls = [u for u in candidates if _allowed(u)]
    return page_urls, allowed_hosts


# ────────────────────────────────────────────────────────────────
# Playwright BFS fallback (depth=2)
# ────────────────────────────────────────────────────────────────

EXTRACT_LINKS_JS = r"""
() => {
    const out = new Set();
    const ctaUrls = new Set();
    const ctaKeywords = /diagnostic|quiz|commenc|d[ée]marrer|trouver|test|try|start|essai|free trial|sign[\s\-_]?up|inscription|cr[ée]er|abonnement|subscribe|join|book|reserv|achat|buy now|j'ach[èe]te|d[ée]couvrir|explore|configurer|personnaliser|choisir|select|book[\s\-_]?demo|try[\s\-_]?free|tarif|pricing|plans|forfait|product|produit|product tour/i;

    // Standard <a href>
    document.querySelectorAll('a[href]').forEach(a => {
        const h = a.getAttribute('href') || '';
        if (h.startsWith('#') || h.startsWith('mailto:') || h.startsWith('tel:') || h.startsWith('javascript:')) return;
        try {
            const u = new URL(h, location.href);
            const clean = u.origin + u.pathname;
            out.add(clean);
            // Tag CTA-keyword anchors for prioritization
            const t = (a.innerText || a.getAttribute('aria-label') || '').trim();
            if (ctaKeywords.test(t)) ctaUrls.add(clean);
        } catch (e) {}
    });

    // <button> / role=button with data-href / data-url / data-link attrs (common SPA pattern)
    document.querySelectorAll('button, [role="button"]').forEach(b => {
        const candidates = [
            b.getAttribute('data-href'), b.getAttribute('data-url'),
            b.getAttribute('data-link'), b.getAttribute('data-target-url'),
        ].filter(Boolean);
        for (const c of candidates) {
            try {
                const u = new URL(c, location.href);
                const clean = u.origin + u.pathname;
                out.add(clean);
                const t = (b.innerText || b.getAttribute('aria-label') || '').trim();
                if (ctaKeywords.test(t)) ctaUrls.add(clean);
            } catch (e) {}
        }
    });

    return {all: Array.from(out), cta: Array.from(ctaUrls)};
}
"""


async def _crawl_fallback(root_url: str, allowed_hosts: set[str] | None = None,
                          max_pages: int = 60, max_depth: int = 3) -> list[str]:
    """BFS up to max_depth from home using Playwright stealth (handles JS-only
    SPAs, hover dropdowns, dynamic nav). More aggressive than the original :
    - depth=3 (default) instead of 2
    - 60 pages cap (vs 30) — needed for sites with no sitemap
    - hover/scroll-trigger to expose lazy-loaded nav
    - prioritize CTA-text links from home (Diagnostic/Commencer/Try/Sign up)
    Returns deduped URLs that match allowed_hosts (or root host if None)."""
    from playwright.async_api import async_playwright
    visited = set()
    candidates = set()
    cta_seed_urls: set[str] = set()  # CTA-keyword anchors found on home/pages — likely funnel entry points
    queue = [(root_url, 0)]

    if allowed_hosts is None:
        allowed_hosts = set()
    try:
        rh = urlparse(root_url).netloc.lower().lstrip("www.")
        if rh:
            allowed_hosts = allowed_hosts | {rh}
    except Exception:
        pass

    def _host_allowed(u: str) -> bool:
        try:
            h = urlparse(u).netloc.lower().lstrip("www.")
            return any(h == a or h.endswith("." + a) or a.endswith("." + h) for a in allowed_hosts)
        except Exception:
            return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="fr-FR",
        )
        # Stealth init — needed for sites with anti-bot (Cloudflare/Akamai)
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [{name: 'Chrome PDF'}, {name: 'Chrome PDF Viewer'}] });
            Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en'] });
            window.chrome = window.chrome || { runtime: {} };
        """)
        page = await ctx.new_page()
        try:
            while queue and len(visited) < max_pages:
                url, depth = queue.pop(0)
                norm = _norm_url(url)
                if norm in visited or depth > max_depth:
                    continue
                visited.add(norm)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(800)
                    # Trigger lazy-load nav: scroll bottom + hover top-level menu items
                    try:
                        await page.evaluate("""
                        async () => {
                            window.scrollTo(0, document.body.scrollHeight / 2);
                            await new Promise(r => setTimeout(r, 200));
                            window.scrollTo(0, document.body.scrollHeight);
                            await new Promise(r => setTimeout(r, 200));
                            window.scrollTo(0, 0);
                            // Hover top-level nav items to expose dropdowns
                            const navItems = document.querySelectorAll('header nav > ul > li, header nav > div > a, [role="menuitem"]');
                            for (const it of Array.from(navItems).slice(0, 8)) {
                                const e = new MouseEvent('mouseover', {bubbles: true});
                                it.dispatchEvent(e);
                                await new Promise(r => setTimeout(r, 100));
                            }
                        }
                        """)
                    except Exception:
                        pass
                    await page.wait_for_timeout(400)
                    extracted = await page.evaluate(EXTRACT_LINKS_JS)
                    all_links = extracted.get("all", []) if isinstance(extracted, dict) else extracted
                    cta_links = extracted.get("cta", []) if isinstance(extracted, dict) else []
                    # Mark CTA-keyword links (track for priority ranking later)
                    for ln in cta_links:
                        ln_norm = _norm_url(ln)
                        if _host_allowed(ln_norm):
                            cta_seed_urls.add(ln_norm)
                    for ln in all_links:
                        ln_norm = _norm_url(ln)
                        if not _host_allowed(ln_norm):
                            continue
                        candidates.add(ln_norm)
                        if depth < max_depth and ln_norm not in visited:
                            queue.append((ln_norm, depth + 1))
                except Exception:
                    continue
        finally:
            await ctx.close()
            await browser.close()
    # Return both — caller can boost CTA seeds in ranking
    return list(candidates), list(cta_seed_urls)


# ────────────────────────────────────────────────────────────────
# Playwright health-check fallback (anti-bot bypass)
# ────────────────────────────────────────────────────────────────

async def _health_via_playwright(urls: list[str], concurrency: int = 4) -> list[dict]:
    """Health check using a stealth Chromium browser. Bypasses Cloudflare/Akamai
    BMP that blocks plain httpx. Slower (~2s/url) so reserved as fallback when
    httpx returns 0 alive on a non-trivial candidate set."""
    from playwright.async_api import async_playwright
    sem = asyncio.Semaphore(concurrency)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="fr-FR",
        )
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [{name: 'Chrome PDF'}] });
            Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en'] });
            window.chrome = window.chrome || { runtime: {} };
        """)
        async def _one(url):
            async with sem:
                page = await ctx.new_page()
                out = {"url": url, "alive": False, "status": None, "final_url": None}
                try:
                    resp = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    if resp:
                        out["status"] = resp.status
                        out["alive"] = (resp.status == 200)
                        out["final_url"] = page.url
                except Exception as e:
                    out["error"] = f"{type(e).__name__}:{str(e)[:80]}"
                finally:
                    await page.close()
                return out
        results = list(await asyncio.gather(*(_one(u) for u in urls)))
        await ctx.close()
        await browser.close()
    return results


# ────────────────────────────────────────────────────────────────
# Health check (httpx primary, Playwright fallback)
# ────────────────────────────────────────────────────────────────

async def _health_batch(urls: list[str], concurrency: int = 20) -> list[dict]:
    """HEAD/GET parallel. Returns dicts in INPUT URL ORDER (preserves ranking)."""
    import httpx
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        async def _one(u):
            async with sem:
                out = {"url": u, "alive": False, "status": None, "final_url": None}
                try:
                    r = await client.head(u, follow_redirects=True, timeout=8.0)
                    if r.status_code in (403, 404, 405, 501) or r.status_code >= 500:
                        try:
                            r = await client.get(u, follow_redirects=True, timeout=12.0)
                        except Exception:
                            pass
                    out["status"] = r.status_code
                    out["final_url"] = str(r.url)
                    out["alive"] = (r.status_code == 200)
                except Exception as e:
                    out["error"] = f"{type(e).__name__}:{str(e)[:80]}"
                return out
        # asyncio.gather preserves input order in the returned list
        results = await asyncio.gather(*(_one(u) for u in urls))
    return list(results)


# ────────────────────────────────────────────────────────────────
# Page sampling — léger DOM dump + thumbnail
# ────────────────────────────────────────────────────────────────

SAMPLE_DOM_JS = r"""
() => {
    const txt = (el) => ((el?.innerText) || '').trim().replace(/\s+/g, ' ').slice(0, 200);
    const inViewportOrTop = (el, h) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && r.top < (h * 2);
    };

    const h1 = txt(document.querySelector('h1'));
    const h2s = Array.from(document.querySelectorAll('h2')).slice(0, 5).map(el => txt(el));
    const title = (document.title || '').trim().slice(0, 200);
    const metaDesc = (document.querySelector('meta[name="description"]')?.getAttribute('content') || '').slice(0, 200);

    const VP_H = window.innerHeight;
    // Primary CTA — first prominent button/link in upper viewport
    const primaryCta = (() => {
        const cands = Array.from(document.querySelectorAll('button, a[class*="btn" i], a[class*="cta" i], [role="button"]'))
            .filter(el => inViewportOrTop(el, VP_H));
        for (const el of cands.slice(0, 30)) {
            const t = txt(el);
            if (t && t.length >= 2 && t.length < 60) return t;
        }
        return null;
    })();

    // Counts
    const inputs = document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]), textarea, select').length;
    const buttons = document.querySelectorAll('button, [role="button"]').length;
    const radios = document.querySelectorAll('input[type=radio]').length;
    const checkboxes = document.querySelectorAll('input[type=checkbox]').length;

    // Pricing table heuristic (multiple price-like elements + "€" or "$" or "/mois")
    const bodyText = (document.body.innerText || '');
    const priceCount = (bodyText.match(/[€$£]\s*\d+[.,]?\d*|\d+[.,]?\d*\s*[€$£]/g) || []).length;
    const monthCount = (bodyText.match(/\/\s*(mois|month|an|year)/gi) || []).length;
    const hasPricingTable = priceCount >= 4 && monthCount >= 1;

    // Quiz heuristic
    const radioGroups = new Set();
    document.querySelectorAll('input[type=radio][name]').forEach(r => radioGroups.add(r.name));
    const hasQuiz = radioGroups.size >= 2 || /quiz|diagnostic|test|profile/i.test(bodyText.slice(0, 4000));

    // Signup form heuristic
    const hasEmail = !!document.querySelector('input[type=email]');
    const hasPassword = !!document.querySelector('input[type=password]');
    const hasSignupForm = hasEmail && (hasPassword || /sign[\s\-_]?up|inscription|create.*account|cr[ée]er.*compte/i.test(bodyText.slice(0, 4000)));

    // PDP signals (single product page)
    const hasAddToCart = /add to cart|add to bag|ajouter au panier|acheter maintenant|buy now|j'ach[èe]te/i.test(bodyText);
    const hasProductPrice = priceCount >= 1 && priceCount <= 3;
    const hasProductGallery = document.querySelectorAll('img[srcset], [class*="gallery" i] img, [class*="product-image" i]').length >= 2;
    const hasPdpSignals = hasAddToCart && hasProductPrice && hasProductGallery;

    // Collection signals (multiple cards/products listed)
    const productCards = document.querySelectorAll('[class*="product-card" i], [class*="product-tile" i], [class*="product-item" i], article[class*="product" i]').length;
    const hasCollection = productCards >= 4 || /catalog|collection/i.test(location.pathname);

    // Word count for content quantity
    const words = bodyText.split(/\s+/).filter(w => w.length > 1).length;

    return {
        url: location.href,
        title, h1, h2s, metaDesc,
        primaryCta,
        counts: {inputs, buttons, radios, checkboxes, productCards},
        signals: {
            hasPricingTable, hasQuiz, hasSignupForm,
            hasPdpSignals, hasCollection,
            hasEmail, hasPassword, hasAddToCart,
        },
        body_word_count: words,
        body_sample: bodyText.slice(0, 800),
    };
}
"""


async def _sample_pages(urls: list[str], take_thumbnail: bool = True, concurrency: int = 3) -> list[dict]:
    """Visit each URL with Playwright, dump light DOM signals + thumbnail."""
    from playwright.async_api import async_playwright
    sem = asyncio.Semaphore(concurrency)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="fr-FR",
        )
        async def _one(url):
            async with sem:
                page = await ctx.new_page()
                out = {"url": url, "_input_url": url, "error": None}
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(700)
                    dom = await page.evaluate(SAMPLE_DOM_JS)
                    out.update(dom)
                    # SAMPLE_DOM_JS overwrites .url with location.href (post-redirect).
                    # Restore input URL so selection logic can match by input.
                    out["url_post_redirect"] = out.get("url")
                    out["url"] = url
                    if take_thumbnail:
                        try:
                            png_bytes = await page.screenshot(
                                clip={"x": 0, "y": 0, "width": 800, "height": 600},
                                timeout=8000,
                            )
                            out["thumbnail_b64"] = base64.b64encode(png_bytes).decode()
                        except Exception:
                            out["thumbnail_b64"] = None
                except Exception as e:
                    out["error"] = f"{type(e).__name__}:{str(e)[:120]}"
                finally:
                    await page.close()
                sys.stderr.write("." if not out.get("error") else "x")
                sys.stderr.flush()
                return out
        # gather preserves input order
        samples = list(await asyncio.gather(*(_one(u) for u in urls)))
        sys.stderr.write("\n")
        await ctx.close()
        await browser.close()
    return samples


# ────────────────────────────────────────────────────────────────
# LLM classification
# ────────────────────────────────────────────────────────────────

CLASSIFY_SYSTEM = """Tu classifies une page web parmi 13 catégories d'audit CRO.

Tu reçois : URL, titre, h1, h2s, primary CTA, counts (inputs/buttons/radios/checkboxes/cards),
signals booléens (hasPricingTable, hasQuiz, hasSignupForm, hasPdpSignals, hasCollection, hasAddToCart),
extrait body, et un thumbnail 800×600 du fold.

CATÉGORIES (priorité = ordre) :
- "home" : page d'accueil racine (URL = / ou /fr/, etc.) — souvent multi-section, plusieurs CTAs
- "pricing" : page tarifs avec hasPricingTable=true OU body parle clairement de plans/tarifs/abonnements
- "quiz_vsl" : quiz/diagnostic interactif (hasQuiz=true et radioGroups≥2). Pas une simple page de sélection produit.
- "signup" : page d'inscription pure (hasSignupForm=true, pas de paiement encore)
- "lp_sales" : landing page sales (objectif = abonner/acheter direct, page longue, hero+features+price+CTA)
- "lp_leadgen" : landing page lead gen (formulaire email simple, démo/essai/contact)
- "pdp" : page produit unique (hasPdpSignals=true, 1 produit avec galerie + add to cart + prix)
- "collection" : page liste de produits (productCards≥4 OU /collection/, /catalog/)
- "lp" : landing page générique (single-section pas pricing/lp_sales/lp_leadgen)
- "faq" : FAQ
- "contact" : page contact
- "blog" : article ou liste d'articles (à rejeter pour audit CRO mais classer correct)
- "other" : si rien ne match clairement

⚠️ RÈGLES STRICTES :
1. Si hasQuiz=false et que la page montre juste 2-3 cards de "choix produit" (ex: "Le chien" / "Le chat") → c'est `collection` ou `lp` (page de pré-sélection), PAS quiz_vsl.
2. Si hasPricingTable=true → priorité `pricing` (sauf si hasSignupForm aussi → `lp_sales`).
3. Si page = `/` ou `/fr/` ou `/en/` → toujours `home`.
4. Si productCards ≥ 4 → collection (sauf si pdp_signals dominent).
5. Si hasPdpSignals=true ET hasCollection=false → `pdp`.
6. Si rien ne match : `other` confidence ≤30%.

Output JSON STRICT (rien d'autre, pas de markdown) :
{
  "page_type": "home|pricing|quiz_vsl|signup|lp_sales|lp_leadgen|pdp|collection|lp|faq|contact|blog|other",
  "confidence": <0-100>,
  "reasoning": "<phrase courte expliquant le verdict>",
  "audit_value": "<high|medium|low>",
  "skip_reason": "<si audit_value=low : pourquoi (blog, FAQ, contact, etc.)>"
}"""


def _make_classify_msg(sample: dict) -> list:
    """Build user message with DOM summary + thumbnail image."""
    s = sample
    text_parts = [
        f"URL : {s.get('url','')}",
        f"Title : {(s.get('title') or '')[:160]}",
        f"H1 : {(s.get('h1') or '')[:160]}",
        f"H2s : {' | '.join((s.get('h2s') or [])[:3])}",
        f"Primary CTA : {s.get('primaryCta') or '(aucun)'}",
        f"Counts : {s.get('counts')}",
        f"Signals : {s.get('signals')}",
        f"Word count : {s.get('body_word_count', 0)}",
        f"Body sample (400) : {(s.get('body_sample') or '')[:400]}",
        "\nQuelle catégorie ?",
    ]
    msg = [{"type": "text", "text": "\n".join(text_parts)}]
    thumb = s.get("thumbnail_b64")
    if thumb:
        msg.insert(0, {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": thumb},
        })
    return msg


def _parse_json(text: str) -> Optional[dict]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json\n"): text = text[5:]
        if text.endswith("```"): text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try: return json.loads(m.group(0))
            except: pass
    return None


async def _classify_sync(samples: list[dict], anthropic_client) -> list[dict]:
    """Sync (1 call per page). Concurrency 5. Returns enriched samples."""
    sem = asyncio.Semaphore(5)
    loop = asyncio.get_event_loop()
    async def _one(s):
        async with sem:
            user_msg = _make_classify_msg(s)
            try:
                resp = await loop.run_in_executor(
                    None,
                    lambda: anthropic_client.messages.create(
                        model=MODEL, max_tokens=300, temperature=0,
                        system=CLASSIFY_SYSTEM,
                        messages=[{"role": "user", "content": user_msg}],
                    ),
                )
                raw = resp.content[0].text if resp.content else ""
                parsed = _parse_json(raw)
                tokens = (getattr(resp.usage, "input_tokens", 0) + getattr(resp.usage, "output_tokens", 0))
                s["classification"] = parsed or {"page_type": "other", "confidence": 0, "reasoning": "parse_fail"}
                s["classification_tokens"] = tokens
            except Exception as e:
                s["classification"] = {"page_type": "other", "confidence": 0, "reasoning": f"api_error:{type(e).__name__}"}
                s["classification_tokens"] = 0
            sys.stderr.write("c"); sys.stderr.flush()
            return s
    await asyncio.gather(*(_one(s) for s in samples))
    sys.stderr.write("\n")
    return samples


# ────────────────────────────────────────────────────────────────
# Selection
# ────────────────────────────────────────────────────────────────

# Audit value priority (1=highest, lower = picked first when in conflict)
PAGE_TYPE_AUDIT_PRIORITY = {
    "home": 1, "pricing": 2, "lp_sales": 3, "quiz_vsl": 4,
    "lp_leadgen": 5, "signup": 6, "pdp": 7, "collection": 8,
    "lp": 9, "faq": 10, "contact": 11, "other": 12, "blog": 99,
}

DEFAULT_TARGET_TYPES = {"home", "pricing", "lp_sales", "lp_leadgen", "quiz_vsl", "signup", "pdp", "collection"}


def _select_pages(classified: list[dict], root_url: str, root_final_url: str | None = None,
                  min_confidence: int = 70, max_pages: int = 5) -> list[dict]:
    """Select home + 2-4 highest-value distinct page_types from DEFAULT_TARGET_TYPES.
    Never falls back to blog/faq/contact/other (low audit value for CRO)."""
    valid = [
        c for c in classified
        if c.get("classification", {}).get("page_type") and not c.get("error")
    ]
    valid.sort(key=lambda c: c["classification"].get("confidence", 0), reverse=True)

    selected: list[dict] = []
    used_types: set[str] = set()

    # 1. Home detection (3 levels of fallback) :
    #    a. Classifier said "home" explicitly
    #    b. URL matches root_url (rstripped)
    #    c. URL matches root_final_url (after redirect — common case for /bienvenue, /fr/, etc.)
    root_norm = root_url.rstrip("/")
    final_norm = (root_final_url or "").rstrip("/")
    homes = [c for c in valid if c["classification"]["page_type"] == "home"]
    if not homes:
        for c in valid:
            url = (c.get("url") or "").rstrip("/")
            if url == root_norm or (final_norm and url == final_norm):
                c["classification"] = dict(c["classification"], page_type="home", _coerced_home=True)
                homes = [c]
                break
    if homes:
        homes.sort(key=lambda c: c["classification"].get("confidence", 0), reverse=True)
        selected.append(homes[0])
        used_types.add("home")

    # 2. Distinct high-value types in priority order, conf >= min_confidence
    target_types = [t for t in DEFAULT_TARGET_TYPES if t != "home"]
    target_types.sort(key=lambda t: PAGE_TYPE_AUDIT_PRIORITY.get(t, 99))
    for pt in target_types:
        if pt in used_types or len(selected) >= max_pages:
            continue
        cands = [
            c for c in valid
            if c["classification"]["page_type"] == pt
            and c["classification"].get("confidence", 0) >= min_confidence
        ]
        if cands:
            selected.append(cands[0])
            used_types.add(pt)

    # 3. If still <3, fill with relaxed confidence (≥50) but ONLY from DEFAULT_TARGET_TYPES.
    # Never fall back to blog/faq/contact/other — these have no CRO audit value.
    if len(selected) < 3:
        for c in valid:
            pt = c["classification"]["page_type"]
            if pt in used_types or pt not in DEFAULT_TARGET_TYPES:
                continue
            if c["classification"].get("confidence", 0) < 50:
                continue
            if len(selected) >= max_pages:
                break
            selected.append(c)
            used_types.add(pt)

    return selected


# ────────────────────────────────────────────────────────────────
# Main pipeline
# ────────────────────────────────────────────────────────────────

async def discover_client(client_slug: str, root_url: str, max_candidates: int = 60,
                          skip_sampling: bool = False, anthropic_client=None) -> dict:
    import httpx
    t0 = time.time()
    out_dir = CAPTURES / client_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "discovered_pages_v25.json"

    print(f"→ V25 discovery {client_slug} ({root_url})")

    # 1. Sitemap (allowed_hosts may grow when sitemapindex points at sister domain)
    print(f"  [1/6] Sitemap fetch …")
    headers = {"User-Agent": "Mozilla/5.0 GrowthCRO-discovery/1.0"}
    async with httpx.AsyncClient(headers=headers) as http:
        sitemap_urls, allowed_hosts = await _discover_via_sitemap(http, root_url)
    print(f"        sitemap → {len(sitemap_urls)} URLs (allowed_hosts={sorted(allowed_hosts)})")

    # 2. Crawl fallback if sitemap weak — depth=3 + hover dropdowns + CTA seeds
    crawl_urls: list[str] = []
    cta_seed_urls: list[str] = []
    if len(sitemap_urls) < 10:
        print(f"  [2/6] Sitemap maigre, crawl Playwright BFS depth=3 + hover + CTA …")
        crawl_urls, cta_seed_urls = await _crawl_fallback(root_url, allowed_hosts=allowed_hosts, max_pages=60, max_depth=3)
        print(f"        crawl → {len(crawl_urls)} URLs ({len(cta_seed_urls)} CTA seeds)")
    else:
        # Even with rich sitemap, do a quick depth=2 crawl from home to grab CTA seeds
        # (quizzes, /profile-builder, signup pages often absent from sitemap.xml).
        # We follow CTA-keyword links 1 level deeper to catch funnel entry points
        # behind a pre-selection page (e.g. Japhy home → /accueil-chien → /profile-builder).
        print(f"  [2/6] Sitemap suffisant — quick CTA-seed crawl (depth=2, 5 pages)")
        _, cta_seed_urls = await _crawl_fallback(root_url, allowed_hosts=allowed_hosts, max_pages=5, max_depth=2)
        print(f"        crawl CTA seeds → {len(cta_seed_urls)} URLs")

    # Merge + filter — root_url FORCED as first, then CTA seeds (high-priority pages)
    root_norm = _norm_url(root_url)
    all_urls = [root_norm]
    for u in cta_seed_urls:
        if u not in all_urls:
            all_urls.append(u)
    for u in dict.fromkeys(sitemap_urls + crawl_urls):
        if u not in all_urls:
            all_urls.append(u)
    filtered = [u for u in all_urls if _filter_url(u)]
    print(f"  [3/6] Filter regex → {len(filtered)}/{len(all_urls)} candidates")

    # Ranking — root first, then include_keywords, then short paths.
    # Apply soft penalty to paths that look like blog/article slugs even when
    # not caught by EXCLUDE_PATH_RE (long slugs with multiple words).
    blog_slug_re = re.compile(r"/[a-z0-9]+(-[a-z0-9]+){4,}/?$", re.I)  # 5+ word slug
    def rank(u: str):
        path = urlparse(u).path or "/"
        is_root = path in ("/", "")
        kw_match = bool(INCLUDE_KEYWORDS_RE.search(u))
        looks_blog_slug = bool(blog_slug_re.search(path))
        depth = path.count("/")
        return (
            0 if is_root else 1,            # root first
            0 if kw_match else 1,            # then keyword-matched
            1 if looks_blog_slug else 0,     # blog slugs last
            depth,                            # shorter paths first
            len(path),
        )
    filtered.sort(key=rank)

    # Diversify: cap per-prefix-group to 3 URLs (avoids long-tail SEO/blog clusters
    # like /sur-mesure/races-de-chien/X dominating the sample budget).
    def _prefix_key(u: str) -> str:
        path = urlparse(u).path or "/"
        segs = [s for s in path.split("/") if s]
        return "/" + "/".join(segs[:2]) if segs else "/"
    per_prefix: dict[str, int] = {}
    diversified: list[str] = []
    for u in filtered:
        k = _prefix_key(u)
        if per_prefix.get(k, 0) >= 3:
            continue
        diversified.append(u)
        per_prefix[k] = per_prefix.get(k, 0) + 1
    candidates = diversified[:max_candidates]
    print(f"        top {len(candidates)} ranked (diversified per-prefix cap=3)")

    # 3. Health check (httpx primary, Playwright stealth fallback if 0 alive)
    print(f"  [4/6] Health check {len(candidates)} URLs (httpx) …")
    health = await _health_batch(candidates, concurrency=20)
    alive = [h for h in health if h.get("alive")]
    print(f"        alive {len(alive)}/{len(candidates)}")
    # If httpx returns 0 alive (anti-bot likely), retry top-30 via stealth Playwright
    if len(alive) == 0 and len(candidates) > 0:
        print(f"        ⚠️  httpx 0 alive — fallback Playwright stealth (anti-bot bypass)")
        ph_health = await _health_via_playwright(candidates[:30], concurrency=4)
        ph_alive = [h for h in ph_health if h.get("alive")]
        print(f"        playwright alive {len(ph_alive)}/{len(ph_health)}")
        # Replace health with Playwright results for selected subset
        health = ph_health + [h for h in health if h.get("url") not in {x.get("url") for x in ph_health}]
        alive = [h for h in health if h.get("alive")]

    if skip_sampling:
        out = {
            "version": "v25.B.1.0",
            "client": client_slug,
            "root_url": root_url,
            "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stats": {
                "sitemap_urls": len(sitemap_urls),
                "crawl_urls": len(crawl_urls),
                "candidates_filtered": len(filtered),
                "alive": len(alive),
            },
            "alive_urls": [h["url"] for h in alive],
        }
        out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print(f"  → skipped sampling (--skip-sampling), saved {out_file.name}")
        return out

    # 4. Sample alive URLs — cap at 40 (keeps under ~$0.05/client; better recall than 30)
    sample_urls = [h["final_url"] or h["url"] for h in alive[:40]]
    print(f"  [5/6] Sampling {len(sample_urls)} pages (DOM + thumbnail) …")
    samples = await _sample_pages(sample_urls, take_thumbnail=True, concurrency=3)
    valid_samples = [s for s in samples if not s.get("error")]
    print(f"        {len(valid_samples)} valid samples")

    # 5. Classify
    print(f"  [6/6] LLM classify (Haiku) …")
    classified = await _classify_sync(valid_samples, anthropic_client)
    tokens_total = sum(s.get("classification_tokens", 0) for s in classified)

    # Determine root final_url (after redirect) for home fallback in selection
    root_final = None
    for h in health:
        if h.get("url", "").rstrip("/") == root_norm:
            root_final = (h.get("final_url") or h.get("url") or "").rstrip("/")
            break

    # 6. Select
    selected = _select_pages(classified, root_url, root_final_url=root_final,
                              min_confidence=70, max_pages=5)
    print(f"        selected {len(selected)} pages")

    # Output (drop heavy thumbnails from output)
    def _strip(c):
        d = dict(c)
        d.pop("thumbnail_b64", None)
        return d

    out = {
        "version": "v25.B.1.0",
        "client": client_slug,
        "root_url": root_url,
        "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(time.time() - t0, 1),
        "stats": {
            "sitemap_urls": len(sitemap_urls),
            "crawl_urls": len(crawl_urls),
            "candidates_filtered": len(filtered),
            "alive": len(alive),
            "sampled": len(valid_samples),
            "selected": len(selected),
            "tokens_total": tokens_total,
        },
        "selected_pages": [
            {
                "url": c.get("url"),
                "page_type": c["classification"]["page_type"],
                "confidence": c["classification"].get("confidence"),
                "audit_value": c["classification"].get("audit_value", "medium"),
                "reasoning": c["classification"].get("reasoning"),
                "h1": c.get("h1"),
                "title": c.get("title"),
                "primaryCta": c.get("primaryCta"),
                "signals": c.get("signals"),
                "counts": c.get("counts"),
            }
            for c in selected
        ],
        "all_classified": [_strip(c) for c in classified],
        "alive_urls_unsampled": [h["url"] for h in alive[30:]],  # for traceability if want re-run
    }
    tmp = out_file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    tmp.replace(out_file)
    print(f"  ✓ {out_file.name} — {len(selected)} pages, {tokens_total} tokens, {round(time.time()-t0,1)}s")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--url", required=True, help="Home URL of the client (eg https://japhy.fr)")
    ap.add_argument("--max-candidates", type=int, default=60)
    ap.add_argument("--skip-sampling", action="store_true",
                    help="Stop after health check (no LLM, no Playwright sampling)")
    args = ap.parse_args()

    try:
        import anthropic
    except ImportError:
        print("❌ pip install anthropic", file=sys.stderr); sys.exit(1)
    client = anthropic.Anthropic(api_key=config.require_anthropic_api_key(), timeout=60.0, max_retries=2) \
        if not args.skip_sampling else None

    asyncio.run(discover_client(args.client, args.url, args.max_candidates,
                                 args.skip_sampling, client))


if __name__ == "__main__":
    main()
