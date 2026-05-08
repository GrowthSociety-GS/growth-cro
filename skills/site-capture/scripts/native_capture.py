#!/usr/bin/env python3
"""
native_capture.py v2.0 — Capteur CRO natif Python (SANS Apify).

Fetche le HTML d'une URL, extrait TOUTES les données structurées nécessaires
au scoring CRO des 6 blocs × 9 types de pages, et produit un capture.json
au format identique à Apify.

Couvre :
  - Bloc 1 Hero /18 : H1, subtitle, CTAs, images, social proof, fold estimate
  - Bloc 2 Persuasion /24 : headings, testimonials, trust, FAQ, storytelling signals
  - Bloc 3 UX /24 : hierarchy, rhythm, scan-ability, nav, forms, lazy-load, transitions
  - Bloc 4 Cohérence /18 : H1/meta alignment, persona patterns, tone, CTA focus
  - Bloc 5 Psycho /18 (ANTICIPÉ) : urgency, scarcity, social proof depth, anchoring
  - Bloc 6 Tech /15 (ANTICIPÉ) : perf hints, SEO metas, schema, a11y basics, security

Page types couverts :
  home, pdp, collection, lp_leadgen, lp_sales, blog, quiz_vsl, pricing, checkout

Limitations (Apify-only) :
  - Screenshots, dimensions rendues, contraste couleurs, positions fold exactes
  - Pages SPA (quiz, checkout dynamique) → flag low_confidence

v2.0 — 2026-04-10
"""

import json, sys, re, pathlib, ssl, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse

# ── Args ──────────────────────────────────────────────────────
# Usage :
#   native_capture.py <url> <label> <pageType>
#     → fetch urllib (legacy, fragile vs Cloudflare/Shopify TLS fingerprint)
#
#   native_capture.py <url> <label> <pageType> --html <path>
#     → skip fetch, lit le HTML depuis <path> (produit par ghost_capture.js)
#     → mode SaaS-grade : TLS fingerprint Chrome réel, passe CDN hostiles
#
# Le parser est identique dans les deux cas — seule la source du HTML diffère.
args = sys.argv[1:]
HTML_FROM_FILE = None
if "--html" in args:
    i = args.index("--html")
    HTML_FROM_FILE = args[i + 1]
    args.pop(i); args.pop(i)

if len(args) < 3:
    print("Usage: native_capture.py <url> <label> <pageType> [--html <path>]", file=sys.stderr)
    sys.exit(1)

URL = args[0]
LABEL = args[1]
PAGE_TYPE = args[2]

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "data" / "captures" / LABEL / PAGE_TYPE
OUT_DIR.mkdir(parents=True, exist_ok=True)
CAP_FILE = OUT_DIR / "capture.json"
HTML_FILE = OUT_DIR / "page.html"

# ══════════════════════════════════════════════════════════════
# FETCH (urllib) OU LOAD (fichier HTML rendered pré-produit)
# ══════════════════════════════════════════════════════════════
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ctx = ssl.create_default_context()

if HTML_FROM_FILE:
    # ── Mode SaaS-grade : HTML déjà récupéré par Playwright (ghost_capture) ────
    src = pathlib.Path(HTML_FROM_FILE)
    if not src.exists():
        print(f"❌ --html file missing: {src}", file=sys.stderr)
        sys.exit(3)
    t0 = time.time()
    html = src.read_text(encoding="utf-8", errors="ignore")
    fetch_time = round(time.time() - t0, 2)
    final_url = URL
    http_status = 200  # rendered successfully if we got here
    print(f"✅ Loaded {len(html)} bytes from {src.name} in {fetch_time}s (rendered DOM)")
    # Copy to canonical path si pas déjà là
    if src.resolve() != HTML_FILE.resolve():
        HTML_FILE.write_text(html, encoding="utf-8")
else:
    # ── Mode legacy : fetch urllib (fragile face aux CDN modernes) ─────────────
    print(f"⏳ Fetching {URL} ...")
    t0 = time.time()
    try:
        req = Request(URL, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        })
        resp = urlopen(req, context=ctx, timeout=20)
        html = resp.read().decode("utf-8", errors="ignore")
        final_url = resp.url
        http_status = resp.status
    except Exception as e:
        print(f"❌ Fetch failed: {e}", file=sys.stderr)
        sys.exit(3)

    fetch_time = round(time.time() - t0, 2)
    print(f"✅ Fetched {len(html)} bytes in {fetch_time}s (status {http_status})")
    HTML_FILE.write_text(html, encoding="utf-8")

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def clean(text):
    """Remove HTML tags and decode common HTML entities."""
    import html as _html
    text = re.sub(r"<[^>]+>", "", text)
    text = _html.unescape(text)  # &nbsp; → space, &amp; → &, etc.
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text.strip()

def strip_scripts_styles(h):
    h = re.sub(r"<script[^>]*>.*?</script>", " ", h, flags=re.DOTALL | re.I)
    h = re.sub(r"<style[^>]*>.*?</style>", " ", h, flags=re.DOTALL | re.I)
    return h

body_match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL | re.I)
body_html = body_match.group(1) if body_match else html
BODY_TAGS = strip_scripts_styles(body_html)  # HTML with tags, no scripts/styles
BODY_TEXT = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", BODY_TAGS)).strip()
BODY_L = BODY_TEXT.lower()
body_words = len(BODY_TEXT.split())
dom_nodes = html.count("<") // 2

# SPA Detection
is_spa = body_words < 50 or dom_nodes < 80
confidence = "low" if is_spa else "high"
if is_spa:
    print(f"⚠️  SPA détecté ({body_words} mots, {dom_nodes} nodes) — capture low_confidence")

# ══════════════════════════════════════════════════════════════
# 1. METAS (Blocs 1,4,6)
# ══════════════════════════════════════════════════════════════
def meta_extract(pattern, source=html, group=1):
    m = re.search(pattern, source, re.I | re.DOTALL)
    return m.group(group).strip() if m else ""

title = clean(meta_extract(r"<title>(.*?)</title>"))

# Meta tags: support both name-before-content and content-before-name order
def get_meta(name_val, attr="name"):
    """Extract meta content supporting any attribute order."""
    # Try name first then content
    m = re.search(rf'<meta[^>]*{attr}=["\']?{name_val}["\']?[^>]*content=["\']([^"\']*)', html, re.I)
    if m: return m.group(1).strip()
    # Try content first then name
    m = re.search(rf'<meta[^>]*content=["\']([^"\']*)["\'][^>]*{attr}=["\']?{name_val}["\']?', html, re.I)
    if m: return m.group(1).strip()
    return ""

meta_desc = get_meta("description")
viewport = get_meta("viewport")
lang = meta_extract(r'<html[^>]*lang=["\']([^"\']+)')
og_title = get_meta("og:title", "property")
og_image = get_meta("og:image", "property")
og_desc = get_meta("og:description", "property")
robots = get_meta("robots")

# These have different patterns
canonical = meta_extract(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)')
if not canonical:
    canonical = meta_extract(r'<link[^>]*href=["\']([^"\']*)["\'][^>]*rel=["\']canonical["\']')
charset = meta_extract(r'<meta[^>]*charset=["\']?([^"\'\s>]+)')
favicon_m = re.search(r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']*)', html, re.I)
if not favicon_m:
    favicon_m = re.search(r'<link[^>]*href=["\']([^"\']*)["\'][^>]*rel=["\'](?:shortcut )?icon["\']', html, re.I)
favicon = favicon_m.group(1).strip() if favicon_m else ""

# ══════════════════════════════════════════════════════════════
# 2. HEADINGS + SMART HERO DETECTION (Blocs 1,2,3,4)
# ══════════════════════════════════════════════════════════════

# --- 2a. Extract all headings with their raw HTML context ---
headings = []
heading_raw = []  # (level, text, raw_tag_attrs, position_in_body)
for m in re.finditer(r"<(h[1-6])\b([^>]*)>(.*?)</\1>", BODY_TAGS, re.DOTALL | re.I):
    level = int(m.group(1)[1])
    attrs = m.group(2)
    inner_html = m.group(3)
    text = clean(inner_html)
    if text and level <= 4:
        headings.append({"level": level, "text": text[:200], "order": len(headings) + 1})
    if level <= 2:
        heading_raw.append({
            "level": level,
            "text": text[:200],
            "attrs": attrs,
            "inner_html": inner_html,
            "pos": m.start(),
            "full_match": m.group(0),
        })

# --- 2b. Smart Hero H1 Detection ---
# Problem: Many sites misuse H1 (logo in header, JS widget headings, etc.)
# Strategy: Filter parasitic H1s, score remaining, fall back to H2 in hero containers

# Detect header boundaries (H1 inside <header> is usually logo)
header_end_pos = 0
header_m_pos = re.search(r"</header>", BODY_TAGS, re.I)
if header_m_pos:
    header_end_pos = header_m_pos.end()

# Known parasitic patterns (widgets, nav, footer-like)
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

# Known hero container patterns (for H2 fallback)
HERO_CONTAINER_PATTERNS = re.compile(
    r"slideshow|hero|banner|jumbotron|masthead|splash|"
    r"cover|intro|featured|main-banner|home-banner|"
    r"slider|carousel.*hero|top-section|above-fold",
    re.I
)

def is_parasitic_h1(h):
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

    # Rule 6: H1 very late in page — BUT only if there's a better candidate earlier
    # (Relaxed: review widgets like Judge.Me can push real content to 80%+)
    # Only filter if pos > 90% AND there's a meaningful H2 earlier in the page
    if h["pos"] > len(BODY_TAGS) * 0.92:
        return True

    # Rule 7: Very short generic text (common widget defaults)
    generic_headings = {"avis", "reviews", "tous les avis", "all reviews",
                        "customer reviews", "avis clients", "panier", "cart",
                        "menu", "navigation", "search", "recherche"}
    if text.lower().strip() in generic_headings:
        return True

    return False

    # Parasitic H2 patterns (cart drawers, hidden elements, product tiles, widgets)
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

def is_parasitic_h2(h):
    """Filter out H2s that are clearly not hero content."""
    if PARASITIC_H2_PATTERNS.search(h["attrs"]):
        return True
    if h["text"].lower().strip().rstrip(".") in PARASITIC_H2_TEXT:
        return True
    # H2 inside header area
    if h["pos"] < header_end_pos:
        return True
    return False

def find_hero_h2_fallback():
    """Find best H2 candidate in a hero-like container."""
    # Strategy 1: H2 inside a known hero container class
    for h in heading_raw:
        if h["level"] != 2 or is_parasitic_h2(h):
            continue
        # Check surrounding context (2000 chars before the H2) for hero container
        ctx_start = max(0, h["pos"] - 2000)
        context_before = BODY_TAGS[ctx_start:h["pos"]]
        if HERO_CONTAINER_PATTERNS.search(context_before):
            if len(h["text"]) > 10:  # Must be meaningful
                return h
        # Also check the H2's own class
        if HERO_CONTAINER_PATTERNS.search(h["attrs"]):
            if len(h["text"]) > 10:
                return h

    # Strategy 2: First non-parasitic H2 in the top 40% of the page with meaningful text
    for h in heading_raw:
        if h["level"] != 2 or is_parasitic_h2(h):
            continue
        if h["pos"] < len(BODY_TAGS) * 0.4 and len(h["text"]) > 15:
            return h

    # Strategy 3: First non-parasitic H2 with heading-1 visual class (sites that use H2 as visual H1)
    for h in heading_raw:
        if h["level"] != 2 or is_parasitic_h2(h):
            continue
        if re.search(r"heading-1|type-heading-1|h1\b", h["attrs"], re.I):
            if len(h["text"]) > 10:
                return h

    return None

# Apply smart detection
all_h1s_raw = [h for h in heading_raw if h["level"] == 1]
valid_h1s = [h for h in all_h1s_raw if not is_parasitic_h1(h)]

hero_source = "h1"  # Track which heading became the hero
h1_text = ""
hero_heading_pos = 0

if valid_h1s:
    # Multiple valid H1s: check if they're adjacent (split H1 pattern like oma_me)
    if len(valid_h1s) >= 2:
        first = valid_h1s[0]
        second = valid_h1s[1]
        gap = second["pos"] - first["pos"]
        # If H1s are close together (< 500 chars apart) and short, concatenate
        if gap < 500 and len(first["text"]) < 40 and len(second["text"]) < 40:
            h1_text = first["text"] + " " + second["text"]
            hero_heading_pos = first["pos"]
            hero_source = "h1_concat"
        else:
            h1_text = first["text"]
            hero_heading_pos = first["pos"]
    else:
        h1_text = valid_h1s[0]["text"]
        hero_heading_pos = valid_h1s[0]["pos"]
else:
    # No valid H1 → fall back to best H2 in hero container
    fallback = find_hero_h2_fallback()
    if fallback:
        h1_text = fallback["text"]
        hero_heading_pos = fallback["pos"]
        hero_source = "h2_fallback"

# For the headings list, also tag which ones are hero
h1s = [h for h in headings if h["level"] == 1]

# Log hero detection result
parasitic_count = len(all_h1s_raw) - len(valid_h1s)
if parasitic_count > 0 or hero_source != "h1":
    print(f"🔍 Hero detection: {len(all_h1s_raw)} H1s found, {parasitic_count} filtered as parasitic")
    print(f"   Hero source: {hero_source} → \"{h1_text[:80]}\"")

# --- 2c. Subtitle detection (from hero heading position) ---
subtitle = ""
if h1_text and hero_heading_pos > 0:
    # Find content after the hero heading
    if hero_source == "h2_fallback":
        # For H2 fallback, search after the H2 tag
        search_tag = "<h2"
    else:
        search_tag = "<h1"

    # Find the specific heading position and look after it
    tag_pos = BODY_TAGS.find(search_tag, hero_heading_pos)
    if tag_pos >= 0:
        # Find closing tag
        close_tag = "</h2>" if hero_source == "h2_fallback" else "</h1>"
        close = BODY_TAGS.find(close_tag, tag_pos)
        if close > 0:
            remainder = BODY_TAGS[close + len(close_tag):]
            # Look for multiple text blocks (bullet points like Japhy)
            subs = []
            for sub_m in re.finditer(r"<(p|h2|h3|div|li|span)\b[^>]*>(.*?)</\1>", remainder[:3000], re.DOTALL | re.I):
                t = clean(sub_m.group(2))
                if len(t) > 5 and len(t) < 200:
                    subs.append(t)
                if len(subs) >= 5:
                    break
            subtitle = "\n".join(subs[:5]) if subs else ""

# ══════════════════════════════════════════════════════════════
# 3. CTAs — ALL links and buttons (Blocs 1,3,4,6)
# ══════════════════════════════════════════════════════════════
ACTION_VERBS = re.compile(
    r"\b(créer|découvrir|essayer|commander|acheter|commencer|obtenir|recevoir|profiter|"
    r"tester|s.inscrire|je\s+\w+|voir|en savoir|rejoindre|demander|réserver|"
    r"get|start|try|buy|sign|order|shop|book|learn|join|request|download|subscribe)\b", re.I
)
BUTTON_CLASS = re.compile(r"button|btn|cta|primary|action|submit", re.I)

ctas = []

# <a> links
for m in re.finditer(r'<a\b([^>]*?)>(.*?)</a>', BODY_TAGS, re.DOTALL | re.I):
    attrs = m.group(1)
    label = clean(m.group(2))[:100]
    if not label or len(label) < 2:
        continue

    href_m = re.search(r'href=["\']([^"\']+)', attrs, re.I)
    raw_href = href_m.group(1) if href_m else ""
    href = urljoin(URL, raw_href) if raw_href else ""

    class_m = re.search(r'class=["\']([^"\']+)', attrs, re.I)
    classes = class_m.group(1) if class_m else ""

    is_button = bool(BUTTON_CLASS.search(classes))
    has_action = bool(ACTION_VERBS.search(label))

    # Also check for role="button"
    has_role_btn = 'role="button"' in attrs.lower() or "role='button'" in attrs.lower()

    if is_button or has_action or has_role_btn:
        # Estimate fold position (character position in HTML as proxy)
        in_fold_est = m.start() < 5000
        score = 0
        reasons = []
        if in_fold_est: score += 30; reasons.append("inFold+30")
        if has_action: score += 20; reasons.append("actionVerb+20")
        if is_button: score += 15; reasons.append("buttonClass+15")
        if has_role_btn: score += 10; reasons.append("roleButton+10")
        if href and "/profile" in href.lower() or "/quiz" in href.lower():
            score += 10; reasons.append("actionHref+10")

        ctas.append({
            "label": label,
            "href": href,
            "rawHref": raw_href,
            "tag": "a",
            "classes": classes,
            "inFold": in_fold_est,
            "primaryScore": score,
            "primaryScoreReasons": reasons,
        })

# <button> elements
for m in re.finditer(r"<button\b([^>]*?)>(.*?)</button>", BODY_TAGS, re.DOTALL | re.I):
    label = clean(m.group(2))[:100]
    if not label or len(label) < 2:
        continue
    attrs = m.group(1)
    class_m = re.search(r'class=["\']([^"\']+)', attrs, re.I)
    classes = class_m.group(1) if class_m else ""
    type_m = re.search(r'type=["\']([^"\']+)', attrs, re.I)
    btn_type = type_m.group(1).lower() if type_m else "button"

    ctas.append({
        "label": label,
        "tag": "button",
        "classes": classes,
        "href": "",
        "rawHref": "",
        "inFold": m.start() < 5000,
        "primaryScore": 15 if btn_type == "submit" else 10,
        "primaryScoreReasons": [f"button_{btn_type}+10"],
        "buttonType": btn_type,
    })

ctas.sort(key=lambda c: c.get("primaryScore", 0), reverse=True)
primary_cta = ctas[0] if ctas else None
if primary_cta:
    primary_cta["isPrimary"] = True

# ══════════════════════════════════════════════════════════════
# 4. SOCIAL PROOF (Blocs 1,2,5)
# ══════════════════════════════════════════════════════════════
trust_widgets = []
testimonials = []
review_counts = []

# Trust platform detection
trust_platforms = {
    "trustpilot": r"trustpilot",
    "google_reviews": r"google.*review|avis\s+google",
    "verified_reviews": r"avis\s+vérifiés|verified\s+review|customer\s+review",
    "capterra": r"capterra",
    "g2": r"g2\.com|g2crowd",
    "yelp": r"yelp",
    "tripadvisor": r"tripadvisor",
    "glassdoor": r"glassdoor",
    "facebook_reviews": r"facebook.*review|avis\s+facebook",
    "ekomi": r"ekomi",
    "society_des_avis_garantis": r"société\s+des\s+avis\s+garantis|avis-garantis",
}
for name, pattern in trust_platforms.items():
    if re.search(pattern, html, re.I):
        trust_widgets.append({"type": name, "present": True})

# Testimonial blocks (multiple detection strategies)
testimonial_selectors = [
    r'<(?:blockquote|div|p|section)[^>]*class=["\'][^"\']*(?:testimonial|temoignage|review|avis|quote|client-story)[^"\']*["\'][^>]*>(.*?)</(?:blockquote|div|p|section)>',
    r'<blockquote[^>]*>(.*?)</blockquote>',
]
seen_testimonials = set()
for pat in testimonial_selectors:
    for m in re.finditer(pat, BODY_TAGS, re.DOTALL | re.I):
        text = clean(m.group(1))[:200]
        if len(text) > 20 and text not in seen_testimonials:
            # Try to find author name nearby
            author = ""
            after = BODY_TAGS[m.end():m.end() + 300]
            author_m = re.search(r'(?:class=["\'][^"\']*(?:author|name|reviewer)[^"\']*["\'][^>]*>)(.*?)<', after, re.I)
            if author_m:
                author = clean(author_m.group(1))[:50]
            testimonials.append({"text": text, "author": author, "source": "html_class"})
            seen_testimonials.add(text)

# Quoted text as testimonials fallback
for m in re.finditer(r'[«"](.*?)[»"]', BODY_TEXT):
    text = m.group(1).strip()
    if 20 < len(text) < 200 and text not in seen_testimonials:
        testimonials.append({"text": text, "author": "", "source": "quoted_text"})
        seen_testimonials.add(text)
        if len(testimonials) >= 15:
            break

# Numeric proof patterns (e.g., "+10 000 clients", "4.8/5", "98%")
number_proofs = re.findall(
    r"(\d[\d\s.,]*(?:\+\s*)?(?:clients?|utilisateurs?|users?|avis|reviews?|étoiles?|stars?|/5|%\s*(?:de\s+)?satisfaction|membres?|marques?|entreprises?|pays|countries))",
    BODY_TEXT, re.I
)
review_counts = [{"text": n.strip()[:60]} for n in number_proofs[:10]]

# Star ratings
star_patterns = re.findall(r"(\d[.,]\d)\s*/\s*5|(\d[.,]\d)\s*(?:étoiles?|stars?)", BODY_TEXT, re.I)
for sp in star_patterns[:3]:
    val = sp[0] or sp[1]
    review_counts.append({"text": f"{val}/5", "type": "star_rating"})

social_in_fold = {
    "present": bool(trust_widgets or review_counts),
    "type": trust_widgets[0]["type"] if trust_widgets else None,
    "snippet": ""
}

# ══════════════════════════════════════════════════════════════
# 5. IMAGES — all page images (Blocs 1,3,6)
# ══════════════════════════════════════════════════════════════
all_images = []
for m in re.finditer(r'<img\b([^>]*)/?>', BODY_TAGS, re.I):
    attrs = m.group(1)
    # Multiple src attributes (src, data-src, data-twic-src, data-lazy-src, srcset)
    src = ""
    for src_attr in ["src", "data-src", "data-twic-src", "data-lazy-src"]:
        src_m = re.search(rf'{src_attr}=["\']([^"\']+)', attrs, re.I)
        if src_m:
            src = src_m.group(1)
            break

    alt_m = re.search(r'alt=["\']([^"\']*)', attrs, re.I)
    alt = alt_m.group(1) if alt_m else ""

    loading_m = re.search(r'loading=["\']([^"\']+)', attrs, re.I)
    loading = loading_m.group(1).lower() if loading_m else ""

    # HTML width/height attributes (not rendered, but useful hint)
    w_m = re.search(r'width=["\']?(\d+)', attrs, re.I)
    h_m = re.search(r'height=["\']?(\d+)', attrs, re.I)
    html_width = int(w_m.group(1)) if w_m else None
    html_height = int(h_m.group(1)) if h_m else None

    if src:
        all_images.append({
            "src": urljoin(URL, src),
            "alt": alt[:100],
            "loading": loading,
            "htmlWidth": html_width,
            "htmlHeight": html_height,
            "inFold": m.start() < 5000,  # rough estimate
        })

hero_images = [img for img in all_images if img.get("inFold")][:5]

# ══════════════════════════════════════════════════════════════
# 6. FORMS (Blocs 3,6 — UX friction + Tech)
# ══════════════════════════════════════════════════════════════
forms = []
for m in re.finditer(r"<form\b([^>]*?)>(.*?)</form>", BODY_TAGS, re.DOTALL | re.I):
    form_attrs = m.group(1)
    form_html = m.group(2)

    action_m = re.search(r'action=["\']([^"\']+)', form_attrs, re.I)
    method_m = re.search(r'method=["\']([^"\']+)', form_attrs, re.I)

    inputs = re.findall(r'<input\b[^>]*type=["\'](?!hidden)([^"\']+)', form_html, re.I)
    hidden = re.findall(r'<input\b[^>]*type=["\']hidden', form_html, re.I)
    textareas = re.findall(r"<textarea", form_html, re.I)
    selects = re.findall(r"<select", form_html, re.I)

    submit_m = re.search(r'<(?:button|input)[^>]*(?:type=["\']submit["\'])[^>]*>(.*?)</(?:button|input)>', form_html, re.DOTALL | re.I)
    submit_label = clean(submit_m.group(1)) if submit_m else ""
    if not submit_label:
        btn_m = re.search(r'<button[^>]*>(.*?)</button>', form_html, re.DOTALL | re.I)
        if btn_m:
            submit_label = clean(btn_m.group(1))

    fields = len(inputs) + len(textareas) + len(selects)
    forms.append({
        "fields": fields,
        "inputs": len(inputs),
        "hiddenInputs": len(hidden),
        "textareas": len(textareas),
        "selects": len(selects),
        "action": action_m.group(1)[:100] if action_m else "",
        "method": method_m.group(1).upper() if method_m else "GET",
        "submit": submit_label[:50],
        "submitLabel": submit_label[:50],
    })

# ══════════════════════════════════════════════════════════════
# 7. SCHEMA.ORG (Bloc 6 Tech)
# ══════════════════════════════════════════════════════════════
schemas = []
for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.I):
    try:
        j = json.loads(m.group(1))
        schema_entry = {"@type": j.get("@type", "unknown")}
        # Extract useful fields per type
        if j.get("@type") == "Product":
            schema_entry["name"] = j.get("name", "")[:100]
            if "offers" in j:
                offers = j["offers"] if isinstance(j["offers"], dict) else j["offers"][0] if j["offers"] else {}
                schema_entry["price"] = offers.get("price", "")
                schema_entry["currency"] = offers.get("priceCurrency", "")
            if "aggregateRating" in j:
                schema_entry["ratingValue"] = j["aggregateRating"].get("ratingValue", "")
                schema_entry["reviewCount"] = j["aggregateRating"].get("reviewCount", "")
        elif j.get("@type") == "Organization":
            schema_entry["name"] = j.get("name", "")[:100]
        elif j.get("@type") in ("FAQPage", "FAQ"):
            schema_entry["questionCount"] = len(j.get("mainEntity", []))
        elif j.get("@type") == "BreadcrumbList":
            schema_entry["items"] = len(j.get("itemListElement", []))
        schemas.append(schema_entry)
    except:
        pass

# ══════════════════════════════════════════════════════════════
# 8. NAVIGATION ANALYSIS (Bloc 3 UX)
# ══════════════════════════════════════════════════════════════
# Header
header_html = ""
header_m = re.search(r"<header\b[^>]*>(.*?)</header>", BODY_TAGS, re.DOTALL | re.I)
if header_m:
    header_html = header_m.group(1)
header_links = len(re.findall(r"<a\b", header_html, re.I))

# Nav elements
nav_blocks = re.findall(r"<nav\b[^>]*>(.*?)</nav>", BODY_TAGS, re.DOTALL | re.I)
nav_elements = len(nav_blocks)
nav_links_total = sum(len(re.findall(r"<a\b", nb, re.I)) for nb in nav_blocks)

# Footer
footer_html = ""
footer_m = re.search(r"<footer\b[^>]*>(.*?)</footer>", BODY_TAGS, re.DOTALL | re.I)
if footer_m:
    footer_html = footer_m.group(1)
footer_links = len(re.findall(r"<a\b", footer_html, re.I))

# Exit links (links to external domains)
parsed_url = urlparse(URL)
site_domain = parsed_url.netloc.replace("www.", "")
exit_links = 0
for m in re.finditer(r'href=["\']([^"\']+)', BODY_TAGS, re.I):
    href = m.group(1)
    if href.startswith("http"):
        try:
            link_domain = urlparse(href).netloc.replace("www.", "")
            if link_domain and link_domain != site_domain:
                exit_links += 1
        except:
            pass

# ══════════════════════════════════════════════════════════════
# 9. OVERLAYS / COOKIE BANNERS (Bloc 1 Hero)
# ══════════════════════════════════════════════════════════════
cookie_cmp_map = {
    "tarteaucitron": r"tarteaucitron",
    "axeptio": r"axeptio",
    "didomi": r"didomi",
    "onetrust": r"onetrust",
    "cookiebot": r"cookiebot",
    "quantcast": r"quantcast",
    "hubspot_cookie": r"hs-banner|cookie-banner",
    "custom": r"cookie.?(?:consent|banner|notice|popup)",
}
cmp_detected = "none"
for name, pattern in cookie_cmp_map.items():
    if re.search(pattern, html, re.I):
        cmp_detected = name
        break

# Chat widgets detection
chat_widgets = []
chat_patterns = {
    "intercom": r"intercom",
    "crisp": r"crisp\.chat|crisp\.im",
    "drift": r"drift\.com|driftt",
    "hubspot_chat": r"hubspot.*chat|hs-chat",
    "zendesk_chat": r"zendesk.*chat|zopim",
    "tidio": r"tidio",
    "livechat": r"livechat",
    "freshchat": r"freshchat",
    "tawk": r"tawk\.to",
}
for name, pattern in chat_patterns.items():
    if re.search(pattern, html, re.I):
        chat_widgets.append({"type": name, "present": True})

# ══════════════════════════════════════════════════════════════
# 10. UX SIGNALS (Bloc 3 — extracted from HTML/CSS patterns)
# ══════════════════════════════════════════════════════════════
ux_signals = {
    # Structural rhythm
    "section_tags": len(re.findall(r"<(?:section|article)\b", BODY_TAGS, re.I)),
    "h2_count": len([h for h in headings if h["level"] == 2]),
    "img_count": len(all_images),
    "body_words": body_words,
    "dom_nodes": dom_nodes,

    # Scan-ability
    "bold_count": len(re.findall(r"<(?:strong|b)\b", BODY_TAGS, re.I)),
    "list_items": len(re.findall(r"<li\b", BODY_TAGS, re.I)),
    "bullet_lists": len(re.findall(r"<(?:ul|ol)\b", BODY_TAGS, re.I)),

    # Lazy loading
    "lazy_images": len(re.findall(r'loading\s*=\s*["\']lazy["\']', BODY_TAGS, re.I)),

    # CSS patterns (detectable from inline/embedded CSS)
    "sticky_fixed": len(re.findall(r"position\s*:\s*(?:sticky|fixed)", html, re.I)),
    "smooth_scroll": bool(re.search(r"scroll-behavior\s*:\s*smooth", html, re.I)),
    "css_transitions": len(re.findall(r"transition\s*:", html, re.I)),
    "overflow_x_patterns": len(re.findall(r"overflow-?x\s*:\s*(?:scroll|auto|hidden)", html, re.I)),

    # JS libraries (detectable from script tags and class names)
    "has_swiper": bool(re.search(r"swiper", html, re.I)),
    "has_slick": bool(re.search(r"slick", html, re.I)),
    "has_carousel": bool(re.search(r"carousel|slider", html, re.I)),
    "has_accordion": bool(re.search(r"accordion|collapsible", html, re.I)),
    "has_details_summary": bool(re.search(r"<details", BODY_TAGS, re.I)),
    "has_back_to_top": bool(re.search(r"back.to.top|scroll.to.top|retour.en.haut", html, re.I)),
    "has_progress_bar": bool(re.search(r"progress|progressbar|scroll.indicator", html, re.I)),
}

# ══════════════════════════════════════════════════════════════
# 11. PSYCHO SIGNALS — ANTICIPÉ Bloc 5 /18
# ══════════════════════════════════════════════════════════════
psycho_signals = {
    # Urgency
    "urgency_words": len(re.findall(
        r"\b(urgent|limité|dernière?\s+chance|plus\s+que|expire|se\s+termine|countdown|timer|"
        r"offre\s+flash|derniers?\s+jours?|ne\s+manquez\s+pas|dépêchez|maintenant|today\s+only|"
        r"limited\s+time|hurry|last\s+chance|ends?\s+(?:today|soon|tonight))\b",
        BODY_L)),
    "has_countdown": bool(re.search(r"countdown|timer|chrono|compte.?à.?rebours", html, re.I)),
    "has_deadline": bool(re.search(r"jusqu.?au|before|avant\s+le|deadline|date\s+limite", BODY_L)),

    # Scarcity
    "scarcity_words": len(re.findall(
        r"\b(stock\s+limité|épuisé|plus\s+que\s+\d|reste\s+\d|exclusive?|rare|edition\s+limitée|"
        r"sold\s+out|out\s+of\s+stock|limited\s+edition|only\s+\d+\s+left|few\s+remaining)\b",
        BODY_L)),
    "has_stock_indicator": bool(re.search(r"stock|disponib|en\s+stock|rupture|qty|quantity", BODY_L)),

    # Social proof depth (beyond trust widgets)
    "user_count_mentions": len(re.findall(r"\d[\d\s.,]*\+?\s*(?:clients?|users?|utilisateurs?|membres?|inscrits?)", BODY_L)),
    "media_mentions": len(re.findall(r"vu\s+(?:dans|sur|à)|as\s+seen|featured\s+in|partenaires?\s+média", BODY_L)),
    "award_mentions": len(re.findall(r"prix|award|récompens|lauréat|winner|élu|best\s+of|top\s+\d", BODY_L)),
    "certification_mentions": len(re.findall(r"certifi|label|agré|homologu|norme|iso\s*\d|bio|organic|vegan", BODY_L)),

    # Anchoring (price display patterns)
    "has_crossed_price": bool(re.search(r"<(?:s|del|strike)\b|text-decoration\s*:\s*line-through|barré|ancien\s+prix", html, re.I)),
    "has_discount_badge": bool(re.search(r"promo|réduction|remise|-\d+%|save\s+\d|économi|discount", BODY_L)),
    "has_free_offer": bool(re.search(r"gratuit|offert|cadeau|free\s+(?:trial|shipping)|livraison\s+gratuite|essai\s+gratuit", BODY_L)),
    "has_guarantee": bool(re.search(r"garantie?|garanti|satisfait|remboursé|money.back|risk.free|sans\s+engagement|sans\s+risque", BODY_L)),

    # Loss aversion
    "loss_framing": len(re.findall(
        r"\b(ne\s+(?:ratez|manquez|perdez)|risque|danger|erreur|éviter?|sans\s+(?:risque|engagement)|"
        r"don.t\s+miss|avoid|risk|mistake|stop\s+(?:losing|wasting))\b",
        BODY_L)),

    # Authority
    "expert_mentions": len(re.findall(r"expert|spécialiste|docteur|dr\.?\s|professeur|vétérinaire|nutritionniste|ingénieur|scientifique", BODY_L)),
    "has_press_logos": bool(re.search(r"press|presse|médias?|as\s+seen|vu\s+dans|logo.*(?:press|media)", html, re.I)),
}

# ══════════════════════════════════════════════════════════════
# 12. TECH SIGNALS — ANTICIPÉ Bloc 6 /15
# ══════════════════════════════════════════════════════════════
# Performance hints (from HTML only, no Lighthouse)
external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)', html, re.I)
external_css = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html, re.I)
inline_styles = re.findall(r"<style\b", html, re.I)

tech_signals = {
    # SEO basics
    "has_title": bool(title),
    "title_length": len(title),
    "has_meta_desc": bool(meta_desc),
    "meta_desc_length": len(meta_desc),
    "has_h1": bool(h1_text),
    "h1_count": len(h1s),
    "has_canonical": bool(canonical),
    "has_robots": bool(robots),
    "robots_content": robots,
    "has_lang": bool(lang),
    "has_viewport": bool(viewport),
    "has_og_tags": bool(og_title or og_image),
    "has_schema_org": len(schemas) > 0,
    "schema_types": [s.get("@type") for s in schemas],

    # Performance hints
    "external_scripts_count": len(external_scripts),
    "external_css_count": len(external_css),
    "inline_style_blocks": len(inline_styles),
    "html_size_bytes": len(html.encode("utf-8")),
    "dom_nodes": dom_nodes,
    "images_total": len(all_images),
    "images_lazy_loaded": ux_signals["lazy_images"],
    "images_without_alt": sum(1 for img in all_images if not img.get("alt")),

    # Security
    "is_https": URL.startswith("https"),
    "has_hsts": bool(re.search(r"strict-transport-security", html, re.I)),

    # Accessibility hints (from HTML only)
    "has_skip_link": bool(re.search(r'skip.*(?:nav|content|main)|aller.*contenu', BODY_TAGS, re.I)),
    "images_without_alt_count": sum(1 for img in all_images if not img.get("alt")),
    "has_aria_labels": bool(re.search(r"aria-label", BODY_TAGS, re.I)),
    "has_role_attributes": bool(re.search(r'role=["\']', BODY_TAGS, re.I)),
    "form_labels_count": len(re.findall(r"<label\b", BODY_TAGS, re.I)),
    "form_inputs_count": sum(f["inputs"] for f in forms),

    # Third-party scripts
    "third_party_domains": list(set(
        urlparse(s).netloc for s in external_scripts
        if urlparse(s).netloc and urlparse(s).netloc.replace("www.", "") != site_domain
    ))[:15],

    # Favicon
    "has_favicon": bool(favicon),
    "has_charset": bool(charset),
}

# ══════════════════════════════════════════════════════════════
# 13. PAGE-TYPE SPECIFIC DATA
# ══════════════════════════════════════════════════════════════
page_specific = {}

if PAGE_TYPE == "pdp":
    # Product page specifics
    page_specific = {
        "has_price": bool(re.search(r"\d+[.,]\d{2}\s*€|€\s*\d+|\$\s*\d+|price|prix", BODY_L)),
        "has_add_to_cart": bool(re.search(r"ajouter.*panier|add.*cart|acheter|buy\s+now", BODY_L)),
        "has_product_gallery": bool(re.search(r"gallery|galerie|carousel.*product|slider.*product|thumbnails?", html, re.I)),
        "has_product_description": bool(re.search(r"description|caractéristiques|features|specs|ingrédients|composition", BODY_L)),
        "has_reviews_section": bool(re.search(r"avis.*client|customer.*review|témoignages?|ratings?", BODY_L)),
        "has_related_products": bool(re.search(r"produits?\s+(?:similaires?|associés?|recommandés?)|related|you.*(?:also|may)\s+like", BODY_L)),
        "has_breadcrumb": bool(re.search(r"breadcrumb|fil\s+d.?ariane", html, re.I)),
    }

elif PAGE_TYPE == "collection":
    page_specific = {
        "has_filters": bool(re.search(r"filter|filtre|tri|sort|catégor|facet", html, re.I)),
        "has_pagination": bool(re.search(r"pagination|page\s+\d|suivant|next\s+page|load\s+more|voir\s+plus", html, re.I)),
        "product_cards_count": len(re.findall(r'class=["\'][^"\']*(?:product|card|item|produit)[^"\']*["\']', BODY_TAGS, re.I)),
        "has_breadcrumb": bool(re.search(r"breadcrumb|fil\s+d.?ariane", html, re.I)),
    }

elif PAGE_TYPE == "blog":
    page_specific = {
        "has_toc": bool(re.search(r"table.?(?:of|des).?(?:contents|matières)|sommaire|toc", html, re.I)),
        "has_author": bool(re.search(r"author|auteur|écrit\s+par|written\s+by|par\s+[A-Z]", BODY_TAGS, re.I)),
        "has_date": bool(re.search(r"publié|published|date|mise\s+à\s+jour|updated", BODY_TAGS, re.I)),
        "has_reading_time": bool(re.search(r"min\s+de\s+lecture|reading\s+time|temps\s+de\s+lecture|\d+\s+min\s+read", BODY_L)),
        "has_share_buttons": bool(re.search(r"share|partag|social|twitter|facebook|linkedin", html, re.I)),
        "has_related_articles": bool(re.search(r"articles?\s+(?:similaires?|associés?|récents?)|related\s+(?:posts?|articles?)|lire\s+aussi", BODY_L)),
        "word_count": body_words,
    }

elif PAGE_TYPE == "pricing":
    page_specific = {
        "has_plan_comparison": bool(re.search(r"comparer|compare|versus|vs\b|plans?|forfaits?|pricing.*table|tableau.*tarif", BODY_L)),
        "plan_count": len(re.findall(r'class=["\'][^"\']*(?:plan|pricing|forfait|offer|offre)[^"\']*["\']', BODY_TAGS, re.I)),
        "has_toggle_annual": bool(re.search(r"annuel|annual|monthly|mensuel|billing.*period|facturation", BODY_L)),
        "has_faq": bool(re.search(r"faq|questions?\s+fréquentes?|frequently\s+asked", BODY_L)),
        "has_free_trial": bool(re.search(r"essai\s+gratuit|free\s+trial|try\s+free|période\s+d.?essai", BODY_L)),
        "has_money_back": bool(re.search(r"satisfait\s+ou\s+remboursé|money.?back|remboursement|garanti", BODY_L)),
    }

elif PAGE_TYPE in ("lp_leadgen", "lp_sales"):
    page_specific = {
        "has_form": len(forms) > 0,
        "form_field_count": max((f["fields"] for f in forms), default=0),
        "has_video": bool(re.search(r"<video|youtube|vimeo|wistia|vidyard|embed.*video", html, re.I)),
        "has_countdown": psycho_signals.get("has_countdown", False),
        "has_guarantee": psycho_signals.get("has_guarantee", False),
        "has_exit_intent": bool(re.search(r"exit.?intent|popup.*leave|before.*leave", html, re.I)),
    }

elif PAGE_TYPE == "quiz_vsl":
    page_specific = {
        "has_progress_bar": ux_signals.get("has_progress_bar", False),
        "has_steps": bool(re.search(r"step|étape|question\s*\d|step.*indicator", html, re.I)),
        "spa_detected": is_spa,
    }

elif PAGE_TYPE == "checkout":
    page_specific = {
        "has_order_summary": bool(re.search(r"récapitulatif|résumé|order.*summary|panier|cart", BODY_L)),
        "has_security_badges": bool(re.search(r"ssl|sécurisé|secure|cadenas|lock|paiement.*sécurisé|3d.?secure", BODY_L)),
        "has_payment_methods": bool(re.search(r"visa|mastercard|paypal|apple.?pay|google.?pay|carte.*bancaire|payment.*method", html, re.I)),
        "has_trust_signals": bool(trust_widgets),
        "form_field_count": max((f["fields"] for f in forms), default=0),
    }

# ══════════════════════════════════════════════════════════════
# BUILD capture.json
# ══════════════════════════════════════════════════════════════
capture = {
    "meta": {
        "url": URL,
        "label": f"{LABEL}__{PAGE_TYPE}",
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "finalUrl": final_url,
        "title": title,
        "metaDescription": meta_desc,
        "completeness": 1 if not is_spa else 0.2,
        "stagesCompleted": ["fetch", "extract", "html"],
        "errors": ["SPA_DETECTED: body too empty for static fetch"] if is_spa else [],
        "pageType": PAGE_TYPE,
        "captureLevel": 0,
        "capturedBy": "playwright-rendered-dom-v3" if HTML_FROM_FILE else "native-python-fetch-v2",
        "captureSource": "ghost_capture.js (page.html rendered)" if HTML_FROM_FILE else "urllib (HTTP natif)",
        "confidence": confidence,
        "fetchTimeMs": int(fetch_time * 1000),
    },
    "hero": {
        "h1": h1_text,
        "h1Count": len(h1s),
        "h1Source": hero_source,
        "h1ParasiticFiltered": parasitic_count,
        "subtitle": subtitle,
        "ctas": [c for c in ctas if c.get("inFold")],
        "primaryCta": primary_cta,
        "heroImages": hero_images,
        "socialProofInFold": social_in_fold,
    },
    "structure": {
        "headings": headings,
        "ctas": ctas,
        "forms": forms,
    },
    "socialProof": {
        "trustWidgets": trust_widgets,
        "testimonials": testimonials[:15],
        "reviewCounts": review_counts,
    },
    "overlays": {
        "cookieBanner": {
            "present": cmp_detected != "none",
            "cmpDetected": cmp_detected,
            "removalMethod": "none",
        },
        "chatWidgets": chat_widgets,
    },
    "technical": {
        "title": title,
        "metaDescription": meta_desc,
        "lang": lang,
        "viewport": viewport,
        "ogTitle": og_title,
        "ogImage": og_image,
        "ogDescription": og_desc,
        "canonical": canonical,
        "robots": robots,
        "charset": charset or "utf-8",
        "favicon": favicon,
        "schemaOrg": schemas,
        "domNodes": dom_nodes,
    },
    "uxSignals": ux_signals,
    "psychoSignals": psycho_signals,
    "techSignals": tech_signals,
    "pageSpecific": page_specific,
    "screenshots": {},
    "rawHtml": "page.html",
}

# ── Save ──────────────────────────────────────────────────────
CAP_FILE.write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n📊 Extraction Summary:")
print(f"  H1: {h1_text[:60] or '(none)'}")
print(f"  Subtitle: {subtitle[:60] or '(none)'}")
print(f"  Headings: {len(headings)} (H1={len(h1s)}, H2={len([h for h in headings if h['level']==2])})")
print(f"  CTAs: {len(ctas)} (primary: {primary_cta['label'][:40] if primary_cta else 'none'})")
print(f"  Forms: {len(forms)} ({sum(f['fields'] for f in forms)} fields total)")
print(f"  Images: {len(all_images)} ({ux_signals['lazy_images']} lazy)")
print(f"  Trust: {len(trust_widgets)} widgets, {len(testimonials)} testimonials")
print(f"  Schema.org: {len(schemas)} ({[s.get('@type') for s in schemas]})")
print(f"  Chat widgets: {len(chat_widgets)}")
print(f"  Psycho signals: urgency={psycho_signals['urgency_words']}, scarcity={psycho_signals['scarcity_words']}")
print(f"  Tech: {tech_signals['external_scripts_count']} scripts, {tech_signals['external_css_count']} CSS, {tech_signals['images_without_alt']} imgs sans alt")
print(f"  Page-specific ({PAGE_TYPE}): {len(page_specific)} fields")
print(f"  DOM: ~{dom_nodes} nodes, {body_words} words")
print(f"  Confidence: {confidence} {'⚠️ SPA' if is_spa else ''}")
print(f"\n✅ Saved: {CAP_FILE}")
print(f"✅ Saved: {HTML_FILE}")
