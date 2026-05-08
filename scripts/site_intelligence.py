#!/usr/bin/env python3
"""
site_intelligence.py — V15 Full Site Crawler & Content Extractor

Crawl a client's entire site from a base URL, discover all pages,
categorize them, extract useful content → site_intel.json

Usage:
    python3 scripts/site_intelligence.py --url https://japhy.fr --client japhy
    python3 scripts/site_intelligence.py --url https://asphalte.com --client asphalte --max-pages 30

Output:
    data/captures/<client>/site_intel.json

Architecture:
    1. Ghost-capture homepage → extract all internal links
    2. Categorize discovered pages (about, team, history, testimonials, press, products, blog, FAQ, legal)
    3. Fetch top-priority pages (about/history/testimonials first)
    4. Extract structured content from each page
    5. Aggregate into site_intel.json
"""

import argparse
import json
import re
import sys
import subprocess
import os
import time
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

# ── Paths ──
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "captures"
GHOST = ROOT / "scripts" / "ghost_capture.js"

# ── Page categories with URL patterns ──
PAGE_CATEGORIES = {
    "about": [
        r"/a-propos", r"/about", r"/qui-sommes-nous", r"/notre-histoire",
        r"/our-story", r"/histoire", r"/company", r"/team", r"/equipe",
        r"/notre-equipe", r"/our-team", r"/fondateur", r"/founder"
    ],
    "testimonials": [
        r"/avis", r"/temoignages", r"/testimonials", r"/reviews",
        r"/clients?[\-/]", r"/success-stories", r"/cas-clients",
        r"/retours-clients", r"/customer-stories"
    ],
    "quality": [
        r"/qualite", r"/quality", r"/engagements", r"/commitments",
        r"/certifications", r"/notre-demarche", r"/fabrication",
        r"/manufacturing", r"/ingredients", r"/composition",
        r"/notre-savoir-faire", r"/expertise"
    ],
    "how_it_works": [
        r"/comment-[cç]a-marche", r"/how-it-works", r"/fonctionnement",
        r"/process", r"/decouvrir", r"/getting-started",
        r"/comment-[cç]a-fonctionne"
    ],
    "press": [
        r"/presse", r"/press", r"/media", r"/actualites", r"/news",
        r"/blog/presse", r"/ils-parlent-de-nous", r"/in-the-press"
    ],
    "faq": [
        r"/faq", r"/aide", r"/help", r"/questions", r"/support",
        r"/centre-aide"
    ],
    "values": [
        r"/valeurs", r"/values", r"/mission", r"/impact",
        r"/responsabilite", r"/rse", r"/csr", r"/durabilite",
        r"/sustainability", r"/manifeste", r"/manifesto"
    ],
    "pricing": [
        r"/prix", r"/pricing", r"/tarifs", r"/plans", r"/offres",
        r"/formules", r"/abonnement"
    ],
    "product": [
        r"/produits?", r"/products?", r"/collections?", r"/shop",
        r"/boutique", r"/catalogue"
    ],
    "blog": [
        r"/blog", r"/articles?", r"/journal", r"/magazine",
        r"/ressources", r"/resources", r"/guides?"
    ],
    "legal": [
        r"/mentions-legales", r"/legal", r"/cgv", r"/cgu",
        r"/privacy", r"/confidentialite", r"/cookies"
    ]
}

# Priority order — about/testimonials/quality first (most useful for LP generation)
PRIORITY_CATEGORIES = [
    "about", "testimonials", "quality", "how_it_works", "values",
    "press", "pricing", "faq", "product", "blog", "legal"
]


# ── DA Extraction — Color / Font / Style helpers ──

# Standard CSS color names → hex mapping (top 30 + black/white)
CSS_NAMED_COLORS = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "yellow": "#ffff00", "orange": "#ffa500", "purple": "#800080",
    "pink": "#ffc0cb", "grey": "#808080", "gray": "#808080", "brown": "#a52a2a",
    "navy": "#000080", "teal": "#008080", "maroon": "#800000", "olive": "#808000",
    "coral": "#ff7f50", "salmon": "#fa8072", "gold": "#ffd700", "silver": "#c0c0c0",
    "beige": "#f5f5dc", "ivory": "#fffff0", "khaki": "#f0e68c", "lavender": "#e6e6fa",
    "cyan": "#00ffff", "magenta": "#ff00ff", "indigo": "#4b0082", "turquoise": "#40e0d0",
    "crimson": "#dc143c", "tomato": "#ff6347", "transparent": None, "inherit": None,
    "initial": None, "unset": None, "currentcolor": None, "none": None,
}

# Colors to IGNORE (too generic / utility)
IGNORED_COLORS = {
    "#000000", "#ffffff", "#000", "#fff", "rgb(0,0,0)", "rgb(255,255,255)",
    "rgba(0,0,0,0)", "rgba(0,0,0,1)", "rgba(255,255,255,1)", "transparent",
}

# Fonts to IGNORE (system defaults, not brand choices)
SYSTEM_FONTS = {
    "arial", "helvetica", "verdana", "georgia", "times", "times new roman",
    "courier", "courier new", "sans-serif", "serif", "monospace", "system-ui",
    "cursive", "fantasy", "-apple-system", "blinkmacsystemfont", "segoe ui",
    "roboto", "oxygen", "ubuntu", "cantarell", "fira sans", "droid sans",
    "helvetica neue", "apple color emoji", "segoe ui emoji", "segoe ui symbol",
    "noto color emoji", "inherit", "initial", "unset",
}


def _normalize_hex(hex_str):
    """Normalize a hex color to 6-digit lowercase. Returns None if invalid."""
    hex_str = hex_str.strip().lower()
    if not hex_str.startswith("#"):
        return None
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) == 8:
        hex_str = hex_str[:6]  # strip alpha
    if len(hex_str) != 6:
        return None
    try:
        int(hex_str, 16)
    except ValueError:
        return None
    return f"#{hex_str}"


def _rgb_to_hex(r, g, b):
    """Convert RGB values to hex."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _hex_to_rgb(hex_color):
    """Convert hex to (r, g, b)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _color_luminance(hex_color):
    """Get relative luminance (0=black, 1=white)."""
    r, g, b = _hex_to_rgb(hex_color)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _color_saturation(hex_color):
    """Get saturation (0=grey, 1=vivid)."""
    r, g, b = _hex_to_rgb(hex_color)
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == 0:
        return 0
    return (mx - mn) / mx


def _color_distance(hex1, hex2):
    """Simple Euclidean distance in RGB space."""
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def _dedupe_similar_colors(colors_with_counts, threshold=30):
    """Merge colors that are very close together, keeping the most frequent."""
    result = []
    used = set()
    # Sort by count descending
    sorted_colors = sorted(colors_with_counts, key=lambda x: x[1], reverse=True)
    for hex_c, count in sorted_colors:
        if hex_c in used:
            continue
        # Check if too close to an existing result color
        merged = False
        for i, (existing, ex_count) in enumerate(result):
            if _color_distance(hex_c, existing) < threshold:
                result[i] = (existing, ex_count + count)
                merged = True
                break
        if not merged:
            result.append((hex_c, count))
        used.add(hex_c)
    return result


def _classify_color_role(hex_color, all_colors):
    """Classify a color as background/text/accent/primary based on luminance + saturation."""
    lum = _color_luminance(hex_color)
    sat = _color_saturation(hex_color)

    if lum > 0.85 and sat < 0.15:
        return "background_light"
    elif lum < 0.15 and sat < 0.15:
        return "text_dark"
    elif sat > 0.4:
        return "accent"  # vivid colors = likely brand/CTA
    elif lum > 0.6:
        return "background_mid"
    elif lum < 0.4:
        return "text_mid"
    else:
        return "neutral"


class StyleExtractor(HTMLParser):
    """Extract CSS content from <style> tags, inline styles, and linked stylesheet URLs."""

    def __init__(self):
        super().__init__()
        self.style_blocks = []
        self.inline_styles = []
        self.stylesheet_urls = []
        self.font_links = []  # Google Fonts etc
        self.meta_theme = None
        self.logo_urls = []
        self.favicon_url = None
        self._in_style = False
        self._current_style = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "style":
            self._in_style = True
            self._current_style = []

        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            if "stylesheet" in rel and href:
                self.stylesheet_urls.append(href)
                # Detect Google Fonts / Typekit / Adobe Fonts
                if any(provider in href.lower() for provider in
                       ["fonts.googleapis.com", "use.typekit.net", "use.fontawesome.com",
                        "fonts.adobe.com", "cloud.typography.com"]):
                    self.font_links.append(href)
            elif "icon" in rel and href:
                self.favicon_url = href

        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            content = attrs_dict.get("content", "")
            if name == "theme-color" and content:
                self.meta_theme = content

        elif tag == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "").lower()
            cls = attrs_dict.get("class", "").lower()
            # Detect logos
            if any(kw in alt for kw in ["logo", "marque", "brand"]) or \
               any(kw in cls for kw in ["logo", "brand"]) or \
               any(kw in src.lower() for kw in ["logo", "brand"]):
                self.logo_urls.append(src)

        # Inline style on any element
        style = attrs_dict.get("style", "")
        if style:
            self.inline_styles.append(style)

    def handle_data(self, data):
        if self._in_style:
            self._current_style.append(data)

    def handle_endtag(self, tag):
        if tag == "style" and self._in_style:
            self._in_style = False
            block = "".join(self._current_style)
            if block.strip():
                self.style_blocks.append(block)

    def get_all_css(self):
        """Return all CSS text (style blocks + inline styles as pseudo-rules)."""
        parts = list(self.style_blocks)
        for s in self.inline_styles:
            parts.append(f"_inline {{ {s} }}")
        return "\n".join(parts)


def extract_colors_from_css(css_text):
    """Extract all color values from CSS text. Returns Counter of normalized hex colors."""
    colors = Counter()

    # 1. Hex colors (#RGB, #RRGGBB, #RRGGBBAA)
    for m in re.finditer(r'#([0-9a-fA-F]{3,8})\b', css_text):
        hex_c = _normalize_hex(f"#{m.group(1)}")
        if hex_c and hex_c not in IGNORED_COLORS:
            colors[hex_c] += 1

    # 2. rgb() and rgba()
    for m in re.finditer(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', css_text):
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            hex_c = _rgb_to_hex(r, g, b)
            if hex_c not in IGNORED_COLORS:
                colors[hex_c] += 1

    # 3. CSS named colors (in property values)
    for m in re.finditer(r':\s*([a-zA-Z]+)\s*[;}\s]', css_text):
        name = m.group(1).lower()
        if name in CSS_NAMED_COLORS:
            hex_c = CSS_NAMED_COLORS[name]
            if hex_c and hex_c not in IGNORED_COLORS:
                colors[hex_c] += 1

    # 4. CSS custom properties (--color-*, --brand-*, --primary, etc.)
    for m in re.finditer(r'--([\w-]*(?:color|brand|primary|secondary|accent|bg|background|text|cta|button)[\w-]*)\s*:\s*([^;]+)', css_text):
        var_name = m.group(1).lower()
        var_value = m.group(2).strip()
        hex_c = _normalize_hex(var_value)
        if hex_c and hex_c not in IGNORED_COLORS:
            # Custom properties with semantic names get a weight bonus
            bonus = 5 if any(kw in var_name for kw in ["primary", "brand", "accent", "cta"]) else 2
            colors[hex_c] += bonus

    return colors


def extract_fonts_from_css(css_text, font_links=None):
    """Extract font families from CSS. Returns dict with heading/body/all."""
    font_links = font_links or []
    all_fonts = Counter()
    heading_fonts = Counter()
    body_fonts = Counter()

    # Parse @font-face declarations
    font_face_families = set()
    for m in re.finditer(r'@font-face\s*\{[^}]*font-family\s*:\s*["\']?([^"\'};]+)', css_text, re.I):
        family = m.group(1).strip().strip("'\"").lower()
        if family and family not in SYSTEM_FONTS:
            font_face_families.add(family)
            all_fonts[family] += 3  # @font-face = strong signal

    # Parse Google Fonts URLs for family names
    for link in font_links:
        for m in re.finditer(r'family=([^&:]+)', link):
            families = m.group(1).replace("+", " ").split("|")
            for f in families:
                fname = f.split(":")[0].strip().lower()
                if fname and fname not in SYSTEM_FONTS:
                    all_fonts[fname] += 5  # Google Fonts = explicit brand choice

    # Parse font-family declarations in selectors
    # Match selector { ... font-family: ... }
    for m in re.finditer(r'([^{}]+)\{([^}]*font-family\s*:[^}]+)\}', css_text, re.I):
        selector = m.group(1).strip().lower()
        block = m.group(2)

        ff_match = re.search(r'font-family\s*:\s*([^;]+)', block, re.I)
        if not ff_match:
            continue

        families_str = ff_match.group(1)
        families = [f.strip().strip("'\"").lower() for f in families_str.split(",")]

        # First non-system font is the brand choice
        brand_font = None
        for f in families:
            if f and f not in SYSTEM_FONTS:
                brand_font = f
                break

        if brand_font:
            all_fonts[brand_font] += 1

            # Detect heading vs body context
            is_heading = any(kw in selector for kw in
                            ["h1", "h2", "h3", "h4", "h5", "h6", ".title", ".heading",
                             ".hero", ".headline", "header", ".display"])
            is_body = any(kw in selector for kw in
                          ["body", "html", "p", ".text", ".content", ".paragraph",
                           "main", "article", ".description", "*"])

            if is_heading:
                heading_fonts[brand_font] += 2
            if is_body:
                body_fonts[brand_font] += 2

    # Also check CSS custom properties for font
    for m in re.finditer(r'--([\w-]*font[\w-]*)\s*:\s*([^;]+)', css_text, re.I):
        var_name = m.group(1).lower()
        val = m.group(2).strip().strip("'\"").lower()
        families = [f.strip().strip("'\"").lower() for f in val.split(",")]
        for f in families:
            if f and f not in SYSTEM_FONTS:
                all_fonts[f] += 3
                if "heading" in var_name or "title" in var_name or "display" in var_name:
                    heading_fonts[f] += 3
                elif "body" in var_name or "text" in var_name or "base" in var_name:
                    body_fonts[f] += 3
                break

    # Build result
    result = {"all_fonts": [], "heading_font": None, "body_font": None}

    if all_fonts:
        result["all_fonts"] = [f for f, _ in all_fonts.most_common(8)]

    if heading_fonts:
        result["heading_font"] = heading_fonts.most_common(1)[0][0]
    elif all_fonts:
        # If no specific heading detection, assume the 1st font-face / Google Font
        for f, _ in all_fonts.most_common():
            if f in font_face_families:
                result["heading_font"] = f
                break

    if body_fonts:
        result["body_font"] = body_fonts.most_common(1)[0][0]
    elif len(all_fonts) >= 2:
        # 2nd most common font as body
        candidates = [f for f, _ in all_fonts.most_common(3) if f != result.get("heading_font")]
        if candidates:
            result["body_font"] = candidates[0]

    return result


def extract_style_mood(css_text):
    """Detect visual mood from CSS properties."""
    mood = {}

    # Border-radius → sharp vs rounded
    radii = []
    for m in re.finditer(r'border-radius\s*:\s*([^;]+)', css_text, re.I):
        val = m.group(1).strip()
        # Extract numeric values
        nums = re.findall(r'(\d+)', val)
        if nums:
            radii.extend(int(n) for n in nums)
    if radii:
        avg_radius = sum(radii) / len(radii)
        mood["border_radius_avg_px"] = round(avg_radius, 1)
        if avg_radius < 4:
            mood["corners"] = "sharp"
        elif avg_radius < 12:
            mood["corners"] = "slightly_rounded"
        elif avg_radius < 24:
            mood["corners"] = "rounded"
        else:
            mood["corners"] = "very_rounded"

    # Box-shadow → flat vs elevated
    shadow_count = len(re.findall(r'box-shadow\s*:', css_text, re.I))
    if shadow_count > 5:
        mood["elevation"] = "elevated"
    elif shadow_count > 0:
        mood["elevation"] = "subtle_shadow"
    else:
        mood["elevation"] = "flat"

    # Gradients → presence
    gradient_count = len(re.findall(r'(?:linear|radial|conic)-gradient', css_text, re.I))
    mood["gradients"] = gradient_count > 0
    mood["gradient_count"] = gradient_count

    # Text-transform uppercase → boldness
    uppercase_count = len(re.findall(r'text-transform\s*:\s*uppercase', css_text, re.I))
    mood["uppercase_usage"] = uppercase_count

    # Letter-spacing → typographic precision
    ls_matches = re.findall(r'letter-spacing\s*:\s*([^;]+)', css_text, re.I)
    mood["letter_spacing_used"] = len(ls_matches) > 0

    # Transitions / animations → dynamic vs static
    transition_count = len(re.findall(r'(?:transition|animation)\s*:', css_text, re.I))
    mood["animations"] = transition_count > 3

    # Overall mood summary
    descriptors = []
    if mood.get("corners") in ("sharp", "slightly_rounded"):
        descriptors.append("geometric")
    else:
        descriptors.append("organic")

    if mood.get("elevation") == "elevated":
        descriptors.append("elevated")
    elif mood.get("elevation") == "flat":
        descriptors.append("flat")

    if gradient_count > 3:
        descriptors.append("gradient-rich")

    if uppercase_count > 5:
        descriptors.append("bold-typographic")

    if transition_count > 5:
        descriptors.append("dynamic")

    mood["descriptors"] = descriptors

    return mood


def extract_brand_identity(html_content, base_url="", verbose=False):
    """
    Full DA extraction from a single HTML page.
    Returns a brand_identity dict with palette, fonts, style_mood, logos.
    """
    # 1. Parse HTML for style blocks, inline styles, stylesheet URLs, logos, favicon
    se = StyleExtractor()
    try:
        se.feed(html_content)
    except Exception:
        pass

    css_text = se.get_all_css()

    # 2. Try to fetch linked stylesheets (top 3 only, skip CDN/third-party)
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc if parsed_base.netloc else ""

    fetched_css_count = 0
    for css_url in se.stylesheet_urls[:5]:
        # Only fetch same-domain stylesheets
        if css_url.startswith("//"):
            css_url = f"https:{css_url}"
        elif css_url.startswith("/"):
            css_url = f"{parsed_base.scheme}://{base_domain}{css_url}"
        elif not css_url.startswith("http"):
            css_url = f"{parsed_base.scheme}://{base_domain}/{css_url}"

        parsed_css = urlparse(css_url)
        # Skip third-party (CDNs, analytics, etc.)
        if base_domain and base_domain not in parsed_css.netloc:
            if not any(p in css_url for p in ["fonts.googleapis", "typekit", "adobe"]):
                continue

        try:
            result = subprocess.run(
                ["curl", "-sL", "--max-time", "10", "-A",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                 css_url],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and len(result.stdout) > 50:
                css_text += "\n" + result.stdout
                fetched_css_count += 1
                if verbose:
                    print(f"   🎨 Fetched CSS: {css_url[:80]}... ({len(result.stdout)} chars)")
        except Exception:
            pass

        if fetched_css_count >= 3:
            break

    if verbose:
        print(f"   🎨 Total CSS: {len(css_text)} chars ({len(se.style_blocks)} blocks, "
              f"{len(se.inline_styles)} inline, {fetched_css_count} external)")

    # 3. Extract colors
    raw_colors = extract_colors_from_css(css_text)
    color_list = [(hex_c, count) for hex_c, count in raw_colors.items()]
    deduped = _dedupe_similar_colors(color_list, threshold=25)

    # Build palette with roles
    palette = []
    for hex_c, count in sorted(deduped, key=lambda x: x[1], reverse=True)[:12]:
        role = _classify_color_role(hex_c, deduped)
        palette.append({
            "hex": hex_c,
            "role": role,
            "frequency": count,
            "luminance": round(_color_luminance(hex_c), 3),
            "saturation": round(_color_saturation(hex_c), 3),
        })

    # Identify key roles
    primary_candidates = [c for c in palette if c["role"] == "accent" and c["saturation"] > 0.3]
    bg_candidates = [c for c in palette if c["role"].startswith("background")]
    text_candidates = [c for c in palette if c["role"].startswith("text")]

    palette_summary = {
        "primary": primary_candidates[0]["hex"] if primary_candidates else None,
        "secondary": primary_candidates[1]["hex"] if len(primary_candidates) > 1 else None,
        "background": bg_candidates[0]["hex"] if bg_candidates else None,
        "text": text_candidates[0]["hex"] if text_candidates else None,
        "all_colors": palette,
    }

    # If meta theme-color exists, that's a strong primary signal
    if se.meta_theme:
        theme_hex = _normalize_hex(se.meta_theme)
        if theme_hex:
            palette_summary["meta_theme_color"] = theme_hex
            if not palette_summary["primary"]:
                palette_summary["primary"] = theme_hex

    # 4. Extract fonts
    fonts = extract_fonts_from_css(css_text, se.font_links)

    # 5. Extract style mood
    style_mood = extract_style_mood(css_text)

    # 6. Logos
    logos = list(set(se.logo_urls))[:5]
    favicon = se.favicon_url

    # 7. Assemble
    brand_identity = {
        "palette": palette_summary,
        "fonts": fonts,
        "style_mood": style_mood,
        "logos": logos,
        "favicon": favicon,
        "css_stats": {
            "total_css_chars": len(css_text),
            "style_blocks": len(se.style_blocks),
            "inline_styles": len(se.inline_styles),
            "external_sheets_fetched": fetched_css_count,
            "font_links": se.font_links,
        },
        "_note": "Extracted from live CSS. Palette/fonts are the CLIENT's real brand identity."
    }

    return brand_identity


class TextExtractor(HTMLParser):
    """Extract visible text from HTML, stripping scripts/styles."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.skip_tags = {"script", "style", "noscript", "svg", "path"}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip = True

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())

    def get_text(self):
        return "\n".join(self.text)


class LinkExtractor(HTMLParser):
    """Extract all internal links from HTML."""

    def __init__(self, base_domain):
        super().__init__()
        self.links = set()
        self.base_domain = base_domain

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self._process_link(value)

    def _process_link(self, href):
        # Skip anchors, mailto, tel, javascript
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return
        # Skip common non-content extensions
        if any(href.lower().endswith(ext) for ext in [".pdf", ".jpg", ".png", ".gif", ".svg", ".css", ".js", ".zip"]):
            return

        parsed = urlparse(href)

        # Relative URL
        if not parsed.netloc:
            path = parsed.path
            if path and not path.startswith("/"):
                path = "/" + path
            if path:
                self.links.add(path)
        # Absolute URL on same domain
        elif self.base_domain in parsed.netloc:
            if parsed.path:
                self.links.add(parsed.path)


def categorize_url(path):
    """Categorize a URL path into a content category."""
    path_lower = path.lower()

    for category, patterns in PAGE_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, path_lower):
                return category

    return "other"


def fetch_page_text(url, tmp_dir, timeout=30):
    """Fetch a page via web_fetch and extract text. Returns (text, success)."""
    try:
        # Try simple fetch first (faster)
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=timeout + 5
        )

        if result.returncode == 0 and len(result.stdout) > 500:
            extractor = TextExtractor()
            extractor.feed(result.stdout)
            text = extractor.get_text()
            if len(text) > 100:
                return text, True

        return "", False
    except Exception as e:
        return f"ERROR: {e}", False


def ghost_fetch(url, output_path, timeout=35):
    """Fetch a page via ghost_capture.js (Playwright). Returns (html_content, success)."""
    if not GHOST.exists():
        return "", False

    try:
        result = subprocess.run(
            ["node", str(GHOST), "--url", url, "--output", str(output_path)],
            capture_output=True, text=True, timeout=timeout
        )

        html_file = Path(str(output_path).replace(".json", "") + "/page.html")
        if not html_file.exists():
            # Try alternate path
            html_file = output_path.parent / "page.html"

        if html_file.exists():
            html = html_file.read_text(errors="replace")
            extractor = TextExtractor()
            extractor.feed(html)
            return extractor.get_text(), True

        return "", False
    except Exception as e:
        return f"ERROR: {e}", False


def extract_links_from_url(url, timeout=20):
    """Fetch a page and extract all internal links."""
    parsed = urlparse(url)
    domain = parsed.netloc

    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=timeout + 5
        )

        if result.returncode == 0:
            extractor = LinkExtractor(domain)
            extractor.feed(result.stdout)
            return extractor.links
    except Exception:
        pass

    return set()


def extract_structured_content(text, category, url):
    """Extract structured data from page text based on category."""
    extracted = {
        "url": url,
        "category": category,
        "text_length": len(text),
        "raw_text_preview": text[:2000]
    }

    # Category-specific extraction
    if category == "about":
        # Look for founder names, years, story elements
        year_matches = re.findall(r'\b(19\d{2}|20[0-2]\d)\b', text)
        if year_matches:
            extracted["years_mentioned"] = list(set(year_matches))

        # Look for team size
        team_match = re.search(r'(\d+)\s*(?:collaborateurs|personnes|salariés|employés|membres|people|employees)', text, re.I)
        if team_match:
            extracted["team_size_mentioned"] = int(team_match.group(1))

    elif category == "testimonials":
        # Look for rating patterns
        rating_match = re.search(r'(\d[.,]\d)\s*/\s*5', text)
        if rating_match:
            extracted["rating_found"] = rating_match.group(0)

        # Look for review counts
        count_match = re.search(r'(\d[\d\s,.]*)\s*(?:avis|reviews|témoignages|notes)', text, re.I)
        if count_match:
            extracted["review_count_mentioned"] = count_match.group(0).strip()

    elif category == "quality":
        # Look for certifications
        cert_patterns = [
            r'ISO\s*\d+', r'IFS\s*\w+', r'FEDIAF', r'BIO', r'AB',
            r'HACCP', r'GMP', r'NF\s*\w+', r'CE', r'AFNOR',
            r'B\s*Corp', r'Ecocert', r'Cosmos'
        ]
        certs = []
        for pattern in cert_patterns:
            if re.search(pattern, text, re.I):
                match = re.search(pattern, text, re.I)
                certs.append(match.group(0))
        if certs:
            extracted["certifications_found"] = certs

    elif category == "pricing":
        # Look for prices
        prices = re.findall(r'(\d+[.,]?\d*)\s*€', text)
        if prices:
            extracted["prices_found"] = prices[:10]

    return extracted


def run_intelligence(base_url, client_id, max_pages=25, verbose=True):
    """Main intelligence pipeline."""
    parsed = urlparse(base_url)
    domain = parsed.netloc
    base = f"{parsed.scheme}://{domain}"

    output_dir = DATA / client_id
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path("/tmp") / f"site_intel_{client_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"🔍 Site Intelligence — {base_url}")
        print(f"   Client: {client_id} | Max pages: {max_pages}")
        print()

    # ── Step 1: Discover pages from homepage ──
    if verbose:
        print("📡 Step 1: Discovering pages from homepage...")

    links = extract_links_from_url(base_url)

    # Also try common about pages directly
    common_paths = [
        "/a-propos", "/about", "/a-propos/notre-histoire", "/a-propos/avis-clients",
        "/a-propos/qualite", "/a-propos/comment-fonctionne", "/notre-histoire",
        "/avis", "/temoignages", "/qualite", "/faq", "/prix", "/tarifs",
        "/engagements", "/valeurs", "/presse", "/blog"
    ]
    for path in common_paths:
        links.add(path)

    # Deduplicate and clean
    clean_links = set()
    for link in links:
        # Normalize
        link = link.rstrip("/")
        if not link:
            link = "/"
        # Skip very long URLs (usually product variants)
        if len(link) > 150:
            continue
        # Skip URLs with query params or fragments
        if "?" in link or "#" in link:
            continue
        clean_links.add(link)

    if verbose:
        print(f"   Found {len(clean_links)} unique paths")

    # ── Step 2: Categorize all discovered URLs ──
    categorized = {}
    for path in clean_links:
        cat = categorize_url(path)
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(path)

    if verbose:
        print("\n📂 Step 2: Categories discovered:")
        for cat in PRIORITY_CATEGORIES:
            if cat in categorized:
                print(f"   {cat}: {len(categorized[cat])} pages — {categorized[cat][:3]}")

    # ── Step 3: Fetch priority pages ──
    if verbose:
        print(f"\n🌐 Step 3: Fetching priority pages (max {max_pages})...")

    pages_fetched = {}
    fetch_count = 0

    # Always fetch homepage first
    if verbose:
        print(f"   → Fetching: / (homepage)")
    text, ok = fetch_page_text(base_url, tmp_dir)
    if ok:
        pages_fetched["homepage"] = extract_structured_content(text, "homepage", base_url)
        fetch_count += 1

    # Then fetch by priority category
    for category in PRIORITY_CATEGORIES:
        if fetch_count >= max_pages:
            break

        paths = categorized.get(category, [])
        # Sort by path length (shorter = more likely to be the main page)
        paths.sort(key=len)

        for path in paths[:3]:  # Max 3 pages per category
            if fetch_count >= max_pages:
                break

            url = base + path
            if verbose:
                print(f"   → Fetching: {path} ({category})")

            text, ok = fetch_page_text(url, tmp_dir)

            # If curl failed, check if it's a soft-404
            if ok and len(text) < 200:
                ok = False

            if ok:
                page_key = f"{category}_{path.replace('/', '_').strip('_')}"
                pages_fetched[page_key] = extract_structured_content(text, category, url)
                fetch_count += 1
            else:
                if verbose:
                    print(f"     ✗ Failed or empty")

            time.sleep(0.5)  # Rate limit

    # ── Step 4: Extract Brand Identity (DA) from homepage HTML ──
    if verbose:
        print(f"\n🎨 Step 4: Extracting brand identity (colors, fonts, style)...")

    brand_identity = {}
    homepage_html = ""

    # Try to get homepage HTML — first check if ghost already captured it
    ghost_page = DATA / client_id / "home" / "page.html"
    if ghost_page.exists():
        homepage_html = ghost_page.read_text(errors="replace")
        if verbose:
            print(f"   Using cached ghost capture: {ghost_page} ({len(homepage_html)} chars)")
    else:
        # Fetch homepage HTML fresh
        try:
            result = subprocess.run(
                ["curl", "-sL", "--max-time", "20", "-A",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                 base_url],
                capture_output=True, text=True, timeout=25
            )
            if result.returncode == 0 and len(result.stdout) > 500:
                homepage_html = result.stdout
                if verbose:
                    print(f"   Fetched homepage HTML: {len(homepage_html)} chars")
        except Exception as e:
            if verbose:
                print(f"   ✗ Failed to fetch homepage: {e}")

    if homepage_html:
        brand_identity = extract_brand_identity(homepage_html, base_url, verbose=verbose)
        if verbose:
            p = brand_identity.get("palette", {})
            f = brand_identity.get("fonts", {})
            print(f"   ✅ Palette: primary={p.get('primary')}, bg={p.get('background')}, "
                  f"{len(p.get('all_colors', []))} colors total")
            print(f"   ✅ Fonts: heading={f.get('heading_font')}, body={f.get('body_font')}, "
                  f"{len(f.get('all_fonts', []))} fonts total")
            mood = brand_identity.get("style_mood", {})
            print(f"   ✅ Mood: {', '.join(mood.get('descriptors', []))}")
    else:
        if verbose:
            print("   ⚠️ No HTML available — brand identity extraction skipped")

    # ── Step 5: Build site_intel.json ──
    site_intel = {
        "meta": {
            "crawl_date": time.strftime("%Y-%m-%d"),
            "base_url": base_url,
            "client_id": client_id,
            "pages_discovered": len(clean_links),
            "pages_fetched": fetch_count,
            "categories_found": {cat: len(paths) for cat, paths in categorized.items() if cat != "other"},
            "has_brand_identity": bool(brand_identity),
            "note": "All content extracted from live pages. Never invented or assumed."
        },
        "brand_identity": brand_identity,
        "sitemap": {cat: paths for cat, paths in categorized.items()},
        "pages": pages_fetched,
        "summary": _build_summary(pages_fetched, client_id, base_url)
    }

    # Save
    output_path = output_dir / "site_intel.json"
    output_path.write_text(json.dumps(site_intel, indent=2, ensure_ascii=False))

    if verbose:
        print(f"\n✅ Done! {fetch_count} pages extracted → {output_path}")
        print(f"   Categories: {', '.join(cat for cat in PRIORITY_CATEGORIES if cat in categorized)}")

    return site_intel


def _build_summary(pages, client_id, base_url):
    """Build a summary from all fetched pages."""
    summary = {
        "client_id": client_id,
        "base_url": base_url,
        "content_available": {}
    }

    for key, page in pages.items():
        cat = page.get("category", "other")
        if cat not in summary["content_available"]:
            summary["content_available"][cat] = []
        summary["content_available"][cat].append({
            "url": page["url"],
            "text_length": page["text_length"],
            "has_useful_content": page["text_length"] > 300
        })

    return summary


def main():
    parser = argparse.ArgumentParser(description="V15 Site Intelligence Crawler")
    parser.add_argument("--url", required=True, help="Base URL to crawl")
    parser.add_argument("--client", required=True, help="Client ID (slug)")
    parser.add_argument("--max-pages", type=int, default=25, help="Max pages to fetch (default 25)")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    args = parser.parse_args()

    result = run_intelligence(
        base_url=args.url,
        client_id=args.client,
        max_pages=args.max_pages,
        verbose=not args.quiet
    )

    print(json.dumps({"status": "OK", "pages_fetched": result["meta"]["pages_fetched"]}, indent=2))


if __name__ == "__main__":
    main()
