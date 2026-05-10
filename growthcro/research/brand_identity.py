"""CSS-based brand identity extraction — palette, typography, mood, logos, favicon."""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlparse


# ─── Color helpers ───────────────────────────────────────────────────────
CSS_NAMED_COLORS: dict[str, str | None] = {
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

IGNORED_COLORS = {
    "#000000", "#ffffff", "#000", "#fff", "rgb(0,0,0)", "rgb(255,255,255)",
    "rgba(0,0,0,0)", "rgba(0,0,0,1)", "rgba(255,255,255,1)", "transparent",
}

SYSTEM_FONTS = {
    "arial", "helvetica", "verdana", "georgia", "times", "times new roman",
    "courier", "courier new", "sans-serif", "serif", "monospace", "system-ui",
    "cursive", "fantasy", "-apple-system", "blinkmacsystemfont", "segoe ui",
    "roboto", "oxygen", "ubuntu", "cantarell", "fira sans", "droid sans",
    "helvetica neue", "apple color emoji", "segoe ui emoji", "segoe ui symbol",
    "noto color emoji", "inherit", "initial", "unset",
}


def _normalize_hex(hex_str: str) -> str | None:
    hex_str = hex_str.strip().lower()
    if not hex_str.startswith("#"):
        return None
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) == 8:
        hex_str = hex_str[:6]
    if len(hex_str) != 6:
        return None
    try:
        int(hex_str, 16)
    except ValueError:
        return None
    return f"#{hex_str}"


def _rgb_to_hex(r, g, b) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _color_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _color_saturation(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == 0:
        return 0
    return (mx - mn) / mx


def _color_distance(hex1: str, hex2: str) -> float:
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def _dedupe_similar_colors(colors_with_counts, threshold: int = 30):
    result: list[tuple[str, int]] = []
    used: set[str] = set()
    sorted_colors = sorted(colors_with_counts, key=lambda x: x[1], reverse=True)
    for hex_c, count in sorted_colors:
        if hex_c in used:
            continue
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


def _classify_color_role(hex_color: str, all_colors) -> str:
    lum = _color_luminance(hex_color)
    sat = _color_saturation(hex_color)
    if lum > 0.85 and sat < 0.15:
        return "background_light"
    elif lum < 0.15 and sat < 0.15:
        return "text_dark"
    elif sat > 0.4:
        return "accent"
    elif lum > 0.6:
        return "background_mid"
    elif lum < 0.4:
        return "text_mid"
    return "neutral"


# ─── HTML extractor ──────────────────────────────────────────────────────
class StyleExtractor(HTMLParser):
    """Extract CSS content from <style> tags, inline styles, and linked stylesheet URLs."""

    def __init__(self):
        super().__init__()
        self.style_blocks: list[str] = []
        self.inline_styles: list[str] = []
        self.stylesheet_urls: list[str] = []
        self.font_links: list[str] = []
        self.meta_theme: str | None = None
        self.logo_urls: list[str] = []
        self.favicon_url: str | None = None
        self._in_style = False
        self._current_style: list[str] = []

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
            if any(kw in alt for kw in ["logo", "marque", "brand"]) or \
               any(kw in cls for kw in ["logo", "brand"]) or \
               any(kw in src.lower() for kw in ["logo", "brand"]):
                self.logo_urls.append(src)

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

    def get_all_css(self) -> str:
        parts = list(self.style_blocks)
        for s in self.inline_styles:
            parts.append(f"_inline {{ {s} }}")
        return "\n".join(parts)


# ─── CSS feature extraction ─────────────────────────────────────────────
def extract_colors_from_css(css_text: str) -> Counter:
    colors: Counter = Counter()

    for m in re.finditer(r'#([0-9a-fA-F]{3,8})\b', css_text):
        hex_c = _normalize_hex(f"#{m.group(1)}")
        if hex_c and hex_c not in IGNORED_COLORS:
            colors[hex_c] += 1

    for m in re.finditer(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', css_text):
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            hex_c = _rgb_to_hex(r, g, b)
            if hex_c not in IGNORED_COLORS:
                colors[hex_c] += 1

    for m in re.finditer(r':\s*([a-zA-Z]+)\s*[;}\s]', css_text):
        name = m.group(1).lower()
        if name in CSS_NAMED_COLORS:
            hex_c = CSS_NAMED_COLORS[name]
            if hex_c and hex_c not in IGNORED_COLORS:
                colors[hex_c] += 1

    for m in re.finditer(r'--([\w-]*(?:color|brand|primary|secondary|accent|bg|background|text|cta|button)[\w-]*)\s*:\s*([^;]+)', css_text):
        var_name = m.group(1).lower()
        var_value = m.group(2).strip()
        hex_c = _normalize_hex(var_value)
        if hex_c and hex_c not in IGNORED_COLORS:
            bonus = 5 if any(kw in var_name for kw in ["primary", "brand", "accent", "cta"]) else 2
            colors[hex_c] += bonus

    return colors


def extract_fonts_from_css(css_text: str, font_links: list[str] | None = None) -> dict:
    font_links = font_links or []
    all_fonts: Counter = Counter()
    heading_fonts: Counter = Counter()
    body_fonts: Counter = Counter()

    font_face_families: set[str] = set()
    for m in re.finditer(r'@font-face\s*\{[^}]*font-family\s*:\s*["\']?([^"\'};]+)', css_text, re.I):
        family = m.group(1).strip().strip("'\"").lower()
        if family and family not in SYSTEM_FONTS:
            font_face_families.add(family)
            all_fonts[family] += 3

    for link in font_links:
        for m in re.finditer(r'family=([^&:]+)', link):
            families = m.group(1).replace("+", " ").split("|")
            for f in families:
                fname = f.split(":")[0].strip().lower()
                if fname and fname not in SYSTEM_FONTS:
                    all_fonts[fname] += 5

    for m in re.finditer(r'([^{}]+)\{([^}]*font-family\s*:[^}]+)\}', css_text, re.I):
        selector = m.group(1).strip().lower()
        block = m.group(2)

        ff_match = re.search(r'font-family\s*:\s*([^;]+)', block, re.I)
        if not ff_match:
            continue

        families_str = ff_match.group(1)
        families = [f.strip().strip("'\"").lower() for f in families_str.split(",")]

        brand_font = None
        for f in families:
            if f and f not in SYSTEM_FONTS:
                brand_font = f
                break

        if brand_font:
            all_fonts[brand_font] += 1

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

    result: dict = {"all_fonts": [], "heading_font": None, "body_font": None}

    if all_fonts:
        result["all_fonts"] = [f for f, _ in all_fonts.most_common(8)]

    if heading_fonts:
        result["heading_font"] = heading_fonts.most_common(1)[0][0]
    elif all_fonts:
        for f, _ in all_fonts.most_common():
            if f in font_face_families:
                result["heading_font"] = f
                break

    if body_fonts:
        result["body_font"] = body_fonts.most_common(1)[0][0]
    elif len(all_fonts) >= 2:
        candidates = [f for f, _ in all_fonts.most_common(3) if f != result.get("heading_font")]
        if candidates:
            result["body_font"] = candidates[0]

    return result


def extract_style_mood(css_text: str) -> dict:
    mood: dict = {}

    radii = []
    for m in re.finditer(r'border-radius\s*:\s*([^;]+)', css_text, re.I):
        val = m.group(1).strip()
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

    shadow_count = len(re.findall(r'box-shadow\s*:', css_text, re.I))
    if shadow_count > 5:
        mood["elevation"] = "elevated"
    elif shadow_count > 0:
        mood["elevation"] = "subtle_shadow"
    else:
        mood["elevation"] = "flat"

    gradient_count = len(re.findall(r'(?:linear|radial|conic)-gradient', css_text, re.I))
    mood["gradients"] = gradient_count > 0
    mood["gradient_count"] = gradient_count

    uppercase_count = len(re.findall(r'text-transform\s*:\s*uppercase', css_text, re.I))
    mood["uppercase_usage"] = uppercase_count

    ls_matches = re.findall(r'letter-spacing\s*:\s*([^;]+)', css_text, re.I)
    mood["letter_spacing_used"] = len(ls_matches) > 0

    transition_count = len(re.findall(r'(?:transition|animation)\s*:', css_text, re.I))
    mood["animations"] = transition_count > 3

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


def extract_brand_identity(html_content: str, base_url: str = "", verbose: bool = False) -> dict:
    """Full DA extraction from a single HTML page → palette, fonts, mood, logos."""
    se = StyleExtractor()
    try:
        se.feed(html_content)
    except Exception:
        pass

    css_text = se.get_all_css()

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc if parsed_base.netloc else ""

    fetched_css_count = 0
    for css_url in se.stylesheet_urls[:5]:
        if css_url.startswith("//"):
            css_url = f"https:{css_url}"
        elif css_url.startswith("/"):
            css_url = f"{parsed_base.scheme}://{base_domain}{css_url}"
        elif not css_url.startswith("http"):
            css_url = f"{parsed_base.scheme}://{base_domain}/{css_url}"

        parsed_css = urlparse(css_url)
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

    raw_colors = extract_colors_from_css(css_text)
    color_list = [(hex_c, count) for hex_c, count in raw_colors.items()]
    deduped = _dedupe_similar_colors(color_list, threshold=25)

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

    if se.meta_theme:
        theme_hex = _normalize_hex(se.meta_theme)
        if theme_hex:
            palette_summary["meta_theme_color"] = theme_hex
            if not palette_summary["primary"]:
                palette_summary["primary"] = theme_hex

    fonts = extract_fonts_from_css(css_text, se.font_links)
    style_mood = extract_style_mood(css_text)
    logos = list(set(se.logo_urls))[:5]
    favicon = se.favicon_url

    return {
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
