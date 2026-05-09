#!/usr/bin/env python3
"""
AURA Extract — Design DNA Extraction from HTML pages.

Extracts the visual identity (palette, fonts, shadows, radii, spacing, animations, layout)
from a captured page's HTML. Works on golden sites, client sites, and inspiration URLs.

Usage:
    # Extract from a single page
    python3 aura_extract.py --page data/captures/glossier/home
    
    # Extract from all golden sites
    python3 aura_extract.py --golden-all
    
    # Extract from a client site
    python3 aura_extract.py --page data/captures/japhy/home
    
    # Extract + Haiku analysis (requires API key)
    python3 aura_extract.py --page data/captures/stripe/home --analyze

Output: design_dna.json in the page directory.
"""

import argparse
import json
import os
import re
import sys
import math
from pathlib import Path
from collections import Counter
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Colors to ignore in extraction
IGNORE_COLORS = {
    "rgba(0, 0, 0, 0)", "transparent", "initial", "inherit", "currentcolor",
    "rgb(0, 0, 0)", "rgb(255, 255, 255)",  # pure black/white tracked separately
}

# ─── HTML-based Design Extraction ─────────────────────────────────────────────

def extract_colors_from_html(html: str) -> dict:
    """Extract color values from inline styles and style tags in HTML."""
    colors = Counter()
    
    # Extract from <style> blocks
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
    all_css = "\n".join(style_blocks)
    
    # Also extract inline styles
    inline_styles = re.findall(r'style="([^"]*)"', html, re.IGNORECASE)
    all_css += "\n".join(inline_styles)
    
    # Find hex colors
    hex_colors = re.findall(r'#([0-9a-fA-F]{3,8})\b', all_css)
    for h in hex_colors:
        if len(h) in (3, 6, 8):
            normalized = f"#{h.lower()}"
            if len(h) == 3:
                normalized = f"#{h[0]*2}{h[1]*2}{h[2]*2}".lower()
            colors[normalized] += 1
    
    # Find rgb/rgba
    rgb_colors = re.findall(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', all_css)
    for r, g, b in rgb_colors:
        hex_val = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        if hex_val not in ("#000000", "#ffffff"):
            colors[hex_val] += 1
    
    # Find hsl/hsla
    hsl_colors = re.findall(r'hsla?\(\s*(\d+)\s*,\s*(\d+)%?\s*,\s*(\d+)%?', all_css)
    for h, s, l in hsl_colors:
        hex_val = hsl_to_hex(int(h), int(s), int(l))
        colors[hex_val] += 1
    
    # Classify colors
    dominant = [c for c, cnt in colors.most_common(20) if cnt >= 2]
    
    # Analyze temperature and saturation
    temps = []
    saturations = []
    for c in dominant[:10]:
        h, s, l = hex_to_hsl(c)
        temps.append(h)
        saturations.append(s)
    
    warm_count = sum(1 for t in temps if t < 60 or t > 300)
    cold_count = sum(1 for t in temps if 180 <= t <= 300)
    
    return {
        "all_colors": [c for c, _ in colors.most_common(30)],
        "dominant_colors": dominant[:8],
        "color_count": len(colors),
        "temperature": "warm" if warm_count > cold_count else ("cold" if cold_count > warm_count else "neutral"),
        "saturation_avg": round(sum(saturations) / max(1, len(saturations)), 1),
        "has_dark_mode": any(hex_to_hsl(c)[2] < 15 for c in dominant[:3]) if dominant else False,
    }


def extract_fonts_from_html(html: str) -> dict:
    """Extract font families from HTML."""
    fonts = Counter()
    
    # From CSS
    font_families = re.findall(r'font-family\s*:\s*([^;}"]+)', html, re.IGNORECASE)
    for ff in font_families:
        # Take the first font in the stack
        primary = ff.split(",")[0].strip().strip("'\"")
        if primary and primary.lower() not in ("serif", "sans-serif", "monospace", "system-ui", "inherit"):
            fonts[primary] += 1
    
    # From Google Fonts links
    gf_links = re.findall(r'fonts\.googleapis\.com/css2?\?family=([^"&]+)', html)
    for link in gf_links:
        families = link.split("|")
        for fam in families:
            name = fam.split(":")[0].replace("+", " ")
            fonts[name] += max(fonts.get(name, 0), 5)  # boost Google Fonts imports
    
    # Classify
    all_fonts = [f for f, _ in fonts.most_common(10)]
    
    display_font = all_fonts[0] if all_fonts else "Unknown"
    body_font = all_fonts[1] if len(all_fonts) > 1 else display_font
    
    # Detect serif vs sans-serif
    SERIF_INDICATORS = ["Playfair", "Serif", "Georgia", "Garamond", "Fraunces", "Cormorant", 
                        "Lora", "Merriweather", "DM Serif", "Recoleta", "Erode", "Zodiak",
                        "Source Serif", "Literata", "Newsreader"]
    
    display_is_serif = any(s.lower() in display_font.lower() for s in SERIF_INDICATORS)
    
    return {
        "all_fonts": all_fonts,
        "display_font": display_font,
        "body_font": body_font,
        "font_count": len(fonts),
        "display_is_serif": display_is_serif,
        "has_mono": any("mono" in f.lower() or "code" in f.lower() for f in all_fonts),
    }


def extract_spacing_from_html(html: str) -> dict:
    """Extract spacing patterns from CSS."""
    paddings = []
    margins = []
    gaps = []
    
    # Extract padding values
    for match in re.finditer(r'padding(?:-(?:top|bottom|left|right))?\s*:\s*(\d+)', html):
        paddings.append(int(match.group(1)))
    
    # Extract margin values
    for match in re.finditer(r'margin(?:-(?:top|bottom|left|right))?\s*:\s*(\d+)', html):
        margins.append(int(match.group(1)))
    
    # Extract gap values
    for match in re.finditer(r'gap\s*:\s*(\d+)', html):
        gaps.append(int(match.group(1)))
    
    all_spacings = paddings + margins + gaps
    
    if not all_spacings:
        return {"avg_padding": 20, "avg_margin": 20, "avg_gap": 16, "spacing_variance": "medium"}
    
    avg = sum(all_spacings) / len(all_spacings)
    
    # Check if spacings follow a modular scale
    phi = 1.618
    phi_scale = [round(8 * phi**i) for i in range(-1, 6)]
    phi_adherence = sum(1 for s in all_spacings if any(abs(s - p) <= 2 for p in phi_scale))
    
    return {
        "avg_padding": round(sum(paddings) / max(1, len(paddings))),
        "avg_margin": round(sum(margins) / max(1, len(margins))),
        "avg_gap": round(sum(gaps) / max(1, len(gaps))) if gaps else 16,
        "max_section_padding": max(paddings) if paddings else 60,
        "spacing_variance": "tight" if avg < 16 else ("generous" if avg > 40 else "medium"),
        "phi_adherence": round(phi_adherence / max(1, len(all_spacings)), 2),
    }


def extract_shadows_from_html(html: str) -> dict:
    """Extract box-shadow patterns."""
    shadows = re.findall(r'box-shadow\s*:\s*([^;}"]+)', html, re.IGNORECASE)
    
    if not shadows:
        return {"count": 0, "layers_avg": 0, "max_blur": 0, "has_colored_shadows": False}
    
    max_blur = 0
    total_layers = 0
    colored = False
    
    for shadow in shadows:
        if shadow.strip() == "none":
            continue
        layers = shadow.split(",")
        total_layers += len(layers)
        
        for layer in layers:
            blur_match = re.search(r'(\d+)px\s+(\d+)px\s+(\d+)px', layer)
            if blur_match:
                blur = int(blur_match.group(3))
                max_blur = max(max_blur, blur)
            
            if "rgba" in layer and "0, 0, 0" not in layer:
                colored = True
    
    return {
        "count": len([s for s in shadows if s.strip() != "none"]),
        "layers_avg": round(total_layers / max(1, len(shadows)), 1),
        "max_blur": max_blur,
        "has_colored_shadows": colored,
    }


def extract_radii_from_html(html: str) -> dict:
    """Extract border-radius patterns."""
    radii = []
    
    for match in re.finditer(r'border-radius\s*:\s*(\d+)', html):
        radii.append(int(match.group(1)))
    
    if not radii:
        return {"avg": 8, "max": 16, "has_pill": False, "style": "moderate"}
    
    avg = sum(radii) / len(radii)
    mx = max(radii)
    has_pill = mx >= 100
    
    return {
        "avg": round(avg),
        "max": mx,
        "has_pill": has_pill,
        "style": "sharp" if avg < 4 else ("rounded" if avg > 16 else "moderate"),
    }


def extract_animations_from_html(html: str) -> dict:
    """Extract animation and transition patterns."""
    
    # Keyframe animations
    keyframes = re.findall(r'@keyframes\s+(\w+)', html)
    
    # Transitions
    transitions = re.findall(r'transition\s*:\s*([^;}"]+)', html, re.IGNORECASE)
    
    # Durations
    durations = []
    for match in re.finditer(r'(\d+\.?\d*)s', " ".join(transitions)):
        durations.append(float(match.group(1)))
    
    # Custom cubic-bezier
    beziers = re.findall(r'cubic-bezier\(([^)]+)\)', html)
    
    # Transform usage
    transforms = re.findall(r'transform\s*:\s*([^;}"]+)', html, re.IGNORECASE)
    has_scale = any("scale" in t for t in transforms)
    has_translate = any("translate" in t for t in transforms)
    has_rotate = any("rotate" in t for t in transforms)
    
    # Scroll-related
    has_intersection_observer = "IntersectionObserver" in html
    has_scroll_listener = "scroll" in html.lower() and "addEventListener" in html
    
    return {
        "keyframe_count": len(keyframes),
        "keyframe_names": keyframes[:10],
        "transition_count": len(transitions),
        "avg_duration": round(sum(durations) / max(1, len(durations)), 2) if durations else 0.3,
        "custom_beziers": beziers[:5],
        "has_scale": has_scale,
        "has_translate": has_translate,
        "has_rotate": has_rotate,
        "has_scroll_animations": has_intersection_observer or has_scroll_listener,
        "animation_intensity": "heavy" if len(keyframes) > 5 else ("moderate" if len(keyframes) > 2 else "light"),
    }


def extract_layout_from_html(html: str) -> dict:
    """Extract layout patterns."""
    
    # Grid usage
    grid_count = len(re.findall(r'display\s*:\s*grid', html, re.IGNORECASE))
    flex_count = len(re.findall(r'display\s*:\s*flex', html, re.IGNORECASE))
    
    # Asymmetric grid detection
    asymmetric_grids = re.findall(r'grid-template-columns\s*:\s*([^;}"]+)', html)
    has_asymmetric = any(
        "fr" in g and g.count("fr") >= 2 and len(set(re.findall(r'[\d.]+fr', g))) > 1
        for g in asymmetric_grids
    )
    
    # Overlap/z-index
    z_indices = re.findall(r'z-index\s*:\s*(\d+)', html)
    has_overlap = len(set(z_indices)) > 3
    
    # Negative margins (intentional overlap)
    neg_margins = re.findall(r'margin-(?:top|left|right|bottom)\s*:\s*-\d+', html)
    
    # Full-width sections
    vw_usage = len(re.findall(r'100vw|width:\s*100%', html))
    
    # Backdrop-filter (glass)
    has_glass = "backdrop-filter" in html
    
    return {
        "grid_count": grid_count,
        "flex_count": flex_count,
        "has_asymmetric_grid": has_asymmetric,
        "has_overlap": has_overlap or len(neg_margins) > 0,
        "overlap_count": len(neg_margins),
        "z_index_layers": len(set(z_indices)),
        "full_width_sections": vw_usage,
        "has_glass": has_glass,
        "grid_type": "asymmetric" if has_asymmetric else ("grid" if grid_count > flex_count else "flex"),
    }


def extract_textures_from_html(html: str) -> dict:
    """Extract texture and visual effect patterns."""
    
    has_noise = bool(re.search(r'feTurbulence|noise|grain', html, re.IGNORECASE))
    has_gradient = bool(re.search(r'linear-gradient|radial-gradient|conic-gradient', html, re.IGNORECASE))
    has_mesh = bool(re.search(r'radial-gradient.*radial-gradient', html, re.DOTALL))
    has_blur = bool(re.search(r'backdrop-filter.*blur|filter.*blur', html, re.IGNORECASE))
    has_svg_filter = bool(re.search(r'<filter|feGaussianBlur|feColorMatrix', html))
    has_clip_path = bool(re.search(r'clip-path', html, re.IGNORECASE))
    has_mask = bool(re.search(r'mask-image|-webkit-mask', html, re.IGNORECASE))
    
    gradient_count = len(re.findall(r'(?:linear|radial|conic)-gradient', html, re.IGNORECASE))
    
    return {
        "has_noise_grain": has_noise,
        "has_gradients": has_gradient,
        "gradient_count": gradient_count,
        "has_mesh_gradient": has_mesh,
        "has_blur_effects": has_blur,
        "has_svg_filters": has_svg_filter,
        "has_clip_path": has_clip_path,
        "has_mask": has_mask,
        "texture_richness": sum([has_noise, has_mesh, has_blur, has_svg_filter, has_clip_path, has_mask]),
    }


# ─── Haiku Visual Analysis ───────────────────────────────────────────────────

ANALYSIS_PROMPT = """Tu es un Directeur Artistique expert mondial. Analyse ce site web et produis un profil design structuré.

DONNÉES TECHNIQUES EXTRAITES :
{technical_data}

CONTEXTE :
- Site : {site_label}
- Page : {page_type}
- Catégorie business : {category}

PRODUIS UN JSON STRICT avec cette structure :
{{
  "aesthetic_vector": {{
    "energy": <1-5 float>,
    "warmth": <1-5 float>,
    "density": <1-5 float>,
    "depth": <1-5 float>,
    "motion": <1-5 float>,
    "editorial": <1-5 float>,
    "playful": <1-5 float>,
    "organic": <1-5 float>
  }},
  "signature": "<1 phrase: l'élément visuel le plus mémorable/distinctif du site>",
  "wow_factor": "<1 phrase: ce qui fait 'wow' quand on voit ce site>",
  "techniques": [
    {{
      "type": "<background|typography|layout|depth|motion|texture|color|signature>",
      "name": "<nom descriptif de la technique>",
      "score": <1-5 float>,
      "css_approach": "<description technique CSS/JS courte>",
      "why_it_works": "<pourquoi cette technique est efficace ici>"
    }}
  ],
  "design_philosophy": "<2-3 phrases résumant la philosophie de design du site>",
  "palette_strategy": "<warm_monochrome|cold_minimal|vivid_contrast|dark_accent|neutral_refined|colorful_playful>",
  "typography_strategy": "<serif_editorial|sans_geometric|sans_humanist|mono_tech|mixed_contrast>",
  "layout_strategy": "<symmetric_grid|asymmetric_tension|editorial_offset|dense_bento|minimal_centered|brutalist_raw>"
}}

IMPORTANT : Note sévèrement. Un 5/5 = top 0.01% mondial (Awwwards Site of the Year). Un 3/5 = bon mais pas remarquable. Sois honnête.
Réponds UNIQUEMENT avec le JSON, rien d'autre."""


async def analyze_with_haiku(technical_data: dict, site_label: str, page_type: str, 
                              category: str, model: str = DEFAULT_MODEL) -> dict:
    """Use Haiku to produce qualitative design analysis from technical extraction."""
    
    api_key = config.anthropic_api_key()
    if not api_key:
        print("WARNING: No ANTHROPIC_API_KEY — skipping Haiku analysis")
        return {}
    
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
    except ImportError:
        print("WARNING: anthropic package not installed — skipping Haiku analysis")
        return {}
    
    prompt = ANALYSIS_PROMPT.format(
        technical_data=json.dumps(technical_data, indent=2, ensure_ascii=False)[:6000],
        site_label=site_label,
        page_type=page_type,
        category=category,
    )
    
    try:
        response = await client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        
        text = response.content[0].text.strip()
        # Extract JSON from response
        if text.startswith("```"):
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        return json.loads(text)
    
    except Exception as e:
        print(f"WARNING: Haiku analysis failed: {e}")
        return {}


# ─── Color Utilities ──────────────────────────────────────────────────────────

def hex_to_hsl(hex_color: str) -> tuple:
    """Convert hex to HSL."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r, g, b = int(hex_color[:2], 16) / 255, int(hex_color[2:4], 16) / 255, int(hex_color[4:6], 16) / 255
    
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    
    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6
    
    return round(h * 360), round(s * 100), round(l * 100)


def hsl_to_hex(h: int, s: int, l: int) -> str:
    """Convert HSL to hex."""
    h, s, l = h / 360, s / 100, l / 100
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


# ─── Aesthetic Vector from Technical Data ─────────────────────────────────────

def compute_vector_from_technical(data: dict) -> dict:
    """Compute an aesthetic vector from purely technical extraction data."""
    
    colors = data.get("colors", {})
    fonts = data.get("typography", {})
    spacing = data.get("spacing", {})
    shadows = data.get("shadows", {})
    radii = data.get("radii", {})
    animations = data.get("animations", {})
    layout = data.get("layout", {})
    textures = data.get("textures", {})
    
    # Energy: derived from animation intensity + saturation + color count
    anim_score = {"light": 2, "moderate": 3, "heavy": 4.5}.get(animations.get("animation_intensity", "light"), 2)
    sat_score = min(5, colors.get("saturation_avg", 40) / 20)
    energy = round(min(5, max(1, (anim_score * 0.6 + sat_score * 0.4))), 1)
    
    # Warmth: from color temperature
    temp = colors.get("temperature", "neutral")
    warmth_base = {"warm": 4.0, "cold": 2.0, "neutral": 3.0}.get(temp, 3.0)
    warmth = round(warmth_base, 1)
    
    # Density: from spacing
    variance = spacing.get("spacing_variance", "medium")
    density = {"tight": 4.0, "medium": 3.0, "generous": 1.5}.get(variance, 3.0)
    
    # Depth: from shadows + glass + textures
    shadow_score = min(5, shadows.get("layers_avg", 0) * 1.5 + (1 if shadows.get("has_colored_shadows") else 0))
    glass_score = 1.5 if layout.get("has_glass") else 0
    texture_score = min(2, textures.get("texture_richness", 0) * 0.5)
    depth = round(min(5, max(1, shadow_score + glass_score + texture_score)), 1)
    
    # Motion: from animations
    motion = round(min(5, max(1, anim_score + (0.5 if animations.get("has_scroll_animations") else 0))), 1)
    
    # Editorial: from layout asymmetry + overlap
    editorial_base = 3.0
    if layout.get("has_asymmetric_grid"): editorial_base += 1.0
    if layout.get("has_overlap"): editorial_base += 0.5
    if textures.get("has_clip_path"): editorial_base += 0.5
    editorial = round(min(5, editorial_base), 1)
    
    # Playful: from radii + saturation + bounce
    radius_score = min(2, radii.get("avg", 8) / 16)
    playful = round(min(5, max(1, radius_score + sat_score * 0.5 + (1 if radii.get("has_pill") else 0))), 1)
    
    # Organic: from border-radius + blob/curve patterns
    organic_base = {"sharp": 1.5, "moderate": 3.0, "rounded": 4.5}.get(radii.get("style", "moderate"), 3.0)
    if textures.get("has_mesh_gradient"): organic_base += 0.5
    organic = round(min(5, organic_base), 1)
    
    return {
        "energy": energy, "warmth": warmth, "density": density, "depth": depth,
        "motion": motion, "editorial": editorial, "playful": playful, "organic": organic,
    }


# ─── Main Extraction Pipeline ────────────────────────────────────────────────

def extract_design_dna(page_dir: str) -> dict:
    """Full extraction pipeline for a single page directory."""
    
    page_dir = Path(page_dir)
    html_path = page_dir / "page.html"
    
    if not html_path.exists():
        print(f"  ERROR: No page.html in {page_dir}")
        return {}
    
    html = html_path.read_text(encoding="utf-8", errors="replace")
    
    # Technical extraction
    colors = extract_colors_from_html(html)
    typography = extract_fonts_from_html(html)
    spacing = extract_spacing_from_html(html)
    shadows = extract_shadows_from_html(html)
    radii = extract_radii_from_html(html)
    animations = extract_animations_from_html(html)
    layout = extract_layout_from_html(html)
    textures = extract_textures_from_html(html)
    
    technical_data = {
        "colors": colors,
        "typography": typography,
        "spacing": spacing,
        "shadows": shadows,
        "radii": radii,
        "animations": animations,
        "layout": layout,
        "textures": textures,
    }
    
    # Compute aesthetic vector from technical data
    vector = compute_vector_from_technical(technical_data)
    
    # Load metadata from capture.json if available
    capture_path = page_dir / "capture.json"
    meta = {}
    if capture_path.exists():
        try:
            cap = json.load(open(capture_path))
            meta = {
                "url": cap.get("meta", {}).get("url", ""),
                "title": cap.get("meta", {}).get("title", ""),
                "label": cap.get("meta", {}).get("label", page_dir.parent.name),
            }
        except:
            pass
    
    # Build design_dna
    design_dna = {
        "version": "16.0.0",
        "extracted_at": __import__("datetime").datetime.now().isoformat(),
        "page_dir": str(page_dir),
        "meta": meta,
        "technical": technical_data,
        "aesthetic_vector": vector,
        # Haiku analysis will be merged in if --analyze is used
    }
    
    return design_dna


async def extract_and_analyze(page_dir: str, site_label: str = "", page_type: str = "", 
                               category: str = "", model: str = DEFAULT_MODEL) -> dict:
    """Extract + Haiku analysis."""
    
    dna = extract_design_dna(page_dir)
    if not dna:
        return {}
    
    # Haiku analysis
    analysis = await analyze_with_haiku(
        technical_data=dna["technical"],
        site_label=site_label or dna.get("meta", {}).get("label", "unknown"),
        page_type=page_type or Path(page_dir).name,
        category=category,
        model=model,
    )
    
    if analysis:
        # Merge Haiku analysis — it overrides the computed vector with a smarter one
        dna["haiku_analysis"] = analysis
        if "aesthetic_vector" in analysis:
            dna["aesthetic_vector_computed"] = dna["aesthetic_vector"]  # keep the computed one
            dna["aesthetic_vector"] = analysis["aesthetic_vector"]  # Haiku's is better
        if "techniques" in analysis:
            dna["techniques"] = analysis["techniques"]
        if "signature" in analysis:
            dna["signature"] = analysis["signature"]
        if "wow_factor" in analysis:
            dna["wow_factor"] = analysis["wow_factor"]
    
    return dna


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AURA Extract — Design DNA Extraction")
    parser.add_argument("--page", type=str, help="Path to a page directory (e.g. data/captures/glossier/home)")
    parser.add_argument("--golden-all", action="store_true", help="Extract all golden sites")
    parser.add_argument("--client-all", action="store_true", help="Extract all client sites")
    parser.add_argument("--analyze", action="store_true", help="Include Haiku visual analysis (requires API key)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of saving")
    args = parser.parse_args()
    
    import asyncio
    
    if args.page:
        # Single page
        page_dir = Path(args.page)
        if not page_dir.is_absolute():
            page_dir = Path.cwd() / page_dir
        
        print(f"Extracting design DNA from {page_dir}...")
        
        if args.analyze:
            dna = asyncio.run(extract_and_analyze(str(page_dir), model=args.model))
        else:
            dna = extract_design_dna(str(page_dir))
        
        if dna:
            if args.dry_run:
                print(json.dumps(dna, indent=2, ensure_ascii=False))
            else:
                out_path = page_dir / "design_dna.json"
                with open(out_path, "w") as f:
                    json.dump(dna, f, indent=2, ensure_ascii=False)
                print(f"  Saved → {out_path}")
                print(f"  Vector: {dna['aesthetic_vector']}")
        else:
            print("  ERROR: extraction failed")
    
    elif args.golden_all or args.client_all:
        # Batch mode
        base = Path.cwd() / "data" / ("golden" if not args.client_all else "captures")
        
        # Find all page directories with page.html
        pages = sorted(base.rglob("page.html"))
        print(f"Found {len(pages)} pages to process")
        
        # Load golden registry for metadata
        registry = {}
        reg_path = Path.cwd() / "data" / "golden" / "_golden_registry.json"
        if reg_path.exists():
            try:
                reg_data = json.load(open(reg_path))
                for site in reg_data.get("sites", []):
                    registry[site["label"]] = site
            except:
                pass
        
        done = 0
        errors = 0
        
        for html_path in pages:
            page_dir = html_path.parent
            site_label = page_dir.parent.name
            page_type = page_dir.name
            
            # Skip if already extracted (unless --analyze adds new data)
            existing = page_dir / "design_dna.json"
            if existing.exists() and not args.analyze:
                done += 1
                continue
            
            category = registry.get(site_label, {}).get("category", "unknown")
            
            print(f"  [{done+1}/{len(pages)}] {site_label}/{page_type}...", end=" ", flush=True)
            
            if args.analyze:
                dna = asyncio.run(extract_and_analyze(
                    str(page_dir), site_label, page_type, category, args.model
                ))
            else:
                dna = extract_design_dna(str(page_dir))
            
            if dna:
                out_path = page_dir / "design_dna.json"
                with open(out_path, "w") as f:
                    json.dump(dna, f, indent=2, ensure_ascii=False)
                v = dna["aesthetic_vector"]
                print(f"OK (e={v['energy']:.1f} w={v['warmth']:.1f} d={v['depth']:.1f})")
                done += 1
            else:
                print("ERROR")
                errors += 1
        
        print(f"\nDone: {done} extracted, {errors} errors")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
