#!/usr/bin/env python3
"""
AURA Compute — Design Token Calculator.

Takes inputs (smart intake, brand DNA, inspirations) and computes
a complete set of design tokens: palette, typography, spacing, motion, depth.

Everything is DERIVED, not chosen. The Golden Ratio, color theory, and
motion physics drive every value.

Usage:
    # From smart intake (Mode B — from scratch)
    python3 aura_compute.py --energy 3 --tonality 4 --business ecom --registre organic
    
    # From brand DNA (Mode A — client URL)
    python3 aura_compute.py --brand-dna data/captures/japhy/home/design_dna.json
    
    # Hybrid (Mode C)
    python3 aura_compute.py --brand-dna data/captures/japhy/home/design_dna.json --energy 3 --tonality 4

Output: aura_tokens.json
"""

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

# ─── Constants ────────────────────────────────────────────────────────────────

PHI = 1.618033988749895

# ─── Font Pools (NEVER AI-slop) ──────────────────────────────────────────────

FONT_BLACKLIST = {
    "Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat", 
    "Poppins", "Nunito", "Helvetica", "Verdana", "Tahoma", "Calibri",
}

FONT_POOLS = {
    "display_serif_elegant": [
        "Playfair Display", "Fraunces", "DM Serif Display", "Cormorant",
        "Lora", "Recoleta", "Erode", "Zodiak", "Instrument Serif",
    ],
    "display_sans_bold": [
        "Clash Display", "Syne", "Unbounded", "Space Grotesk",
        "Bricolage Grotesque", "Cabinet Grotesk", "Switzer", "Archivo Black",
    ],
    "display_sans_clean": [
        "General Sans", "Satoshi", "Outfit", "Plus Jakarta Sans",
        "Manrope", "Geist", "DM Sans", "Wix Madefor Display",
    ],
    "display_mono": [
        "Space Mono", "JetBrains Mono", "IBM Plex Mono", "Fira Code",
    ],
    "body_readable": [
        "Plus Jakarta Sans", "Satoshi", "General Sans", "Outfit",
        "Manrope", "Geist", "IBM Plex Sans", "DM Sans",
    ],
    "body_serif": [
        "Source Serif 4", "Literata", "Newsreader", "Charter", "Lora",
    ],
}

# ─── Motion Profiles ─────────────────────────────────────────────────────────

MOTION_PROFILES = {
    "inertia": {
        "name": "Inertia (Soie)",
        "curve": "cubic-bezier(0.23, 1, 0.32, 1)",
        "duration_base": "0.8s",
        "stagger_delay": "100ms",
        "hover_scale": 1.015,
        "hover_translate_y": "-2px",
        "scroll_reveal": "fade-up",
        "scroll_duration": "1s",
        "best_for": {"energy": (1, 2.5), "editorial": (3.5, 5)},
    },
    "smooth": {
        "name": "Smooth (Respiration)",
        "curve": "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        "duration_base": "0.6s",
        "stagger_delay": "80ms",
        "hover_scale": 1.03,
        "hover_translate_y": "-4px",
        "scroll_reveal": "fade-up",
        "scroll_duration": "0.8s",
        "best_for": {"energy": (2, 3.5), "organic": (3, 5)},
    },
    "spring": {
        "name": "Spring (Précision)",
        "curve": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "duration_base": "0.35s",
        "stagger_delay": "50ms",
        "hover_scale": 1.05,
        "hover_translate_y": "-3px",
        "scroll_reveal": "slide-up",
        "scroll_duration": "0.5s",
        "best_for": {"energy": (3, 4.5), "organic": (1, 2.5)},
    },
    "bounce": {
        "name": "Bounce (Élastique)",
        "curve": "cubic-bezier(0.68, -0.55, 0.27, 1.55)",
        "duration_base": "0.5s",
        "stagger_delay": "60ms",
        "hover_scale": 1.08,
        "hover_translate_y": "-6px",
        "scroll_reveal": "pop-in",
        "scroll_duration": "0.6s",
        "best_for": {"energy": (4, 5), "playful": (3.5, 5)},
    },
    "snap": {
        "name": "Snap (Impact)",
        "curve": "cubic-bezier(0.16, 1, 0.3, 1)",
        "duration_base": "0.25s",
        "stagger_delay": "30ms",
        "hover_scale": 1.0,
        "hover_translate_y": "0px",
        "scroll_reveal": "clip-reveal",
        "scroll_duration": "0.4s",
        "best_for": {"editorial": (4, 5), "playful": (1, 2)},
    },
}

# ─── Business Modifiers ──────────────────────────────────────────────────────

BUSINESS_MODIFIERS = {
    "ecom":      {"density": +0.5, "motion": +0.3, "playful": +0.3},
    "saas":      {"depth": +1.0, "density": +0.5, "organic": -0.8, "editorial": -0.3},
    "service":   {"editorial": +0.5, "warmth": +0.3},
    "leadgen":   {"density": -0.3, "editorial": +0.3},
    "app":       {"playful": +0.5, "motion": +0.5, "organic": +0.3},
    "formation": {"warmth": +0.5, "editorial": +0.3},
    "luxury":    {"density": -1.5, "editorial": +1.5, "depth": +1.0, "motion": -0.5},
}

REGISTRE_OVERRIDES = {
    "minimal":    {"density": 1.5, "depth": 2.0, "motion": 2.0, "editorial": 3.5},
    "editorial":  {"editorial": 5.0, "density": 2.0, "depth": 3.5},
    "organique":  {"organic": 5.0, "warmth": 4.0, "depth": 3.5},
    "tech":       {"organic": 1.0, "depth": 4.5, "warmth": 1.5},
    "brutalist":  {"organic": 1.0, "playful": 1.0, "depth": 1.5, "editorial": 4.5, "energy": 4.0},
    "dark":       {"depth": 4.5, "warmth": 1.5, "energy": 3.5},
    "colore":     {"playful": 4.5, "warmth": 4.0, "energy": 4.0},
    "luxe":       {"density": 1.0, "depth": 4.0, "editorial": 4.5, "motion": 2.0, "warmth": 2.5},
}

# ─── Color Utilities ──────────────────────────────────────────────────────────

def hex_to_hsl(hex_color: str) -> tuple:
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
        if mx == r: h = (g - b) / d + (6 if g < b else 0)
        elif mx == g: h = (b - r) / d + 2
        else: h = (r - g) / d + 4
        h /= 6
    return round(h * 360), round(s * 100), round(l * 100)


def hsl_to_hex(h: int, s: int, l: int) -> str:
    h, s, l = h / 360, max(0, min(100, s)) / 100, max(0, min(100, l)) / 100
    if s == 0:
        r = g = b = l
    else:
        def hue2rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def hsl_to_rgb_str(h: int, s: int, l: int) -> str:
    hex_c = hsl_to_hex(h, s, l).lstrip("#")
    return f"{int(hex_c[:2],16)},{int(hex_c[2:4],16)},{int(hex_c[4:6],16)}"


def clamp(val, lo=1.0, hi=5.0):
    return round(max(lo, min(hi, val)), 1)


# ─── Vector Computation ──────────────────────────────────────────────────────

def intake_to_vector(energy: float, tonality: float, business: str = "", registre: str = "") -> dict:
    """Convert Smart Intake answers to an aesthetic vector."""
    
    v = {
        "energy": energy,
        "warmth": tonality * 0.7 + (0.8 if business in ("ecom", "food", "app") else 0),
        "density": 3.0,
        "depth": 3.0,
        "motion": energy * 0.7 + 0.5,
        "editorial": max(1.5, 5.5 - energy),
        "playful": tonality * 0.55 + (0.5 if energy > 3.5 else 0),
        "organic": tonality * 0.45 + (0.8 if business in ("wellness", "food", "organic") else 0),
    }
    
    # Apply business modifiers
    mods = BUSINESS_MODIFIERS.get(business, {})
    for key, delta in mods.items():
        if key in v:
            v[key] += delta
    
    # Apply registre overrides (these SET values, not add)
    if registre and registre in REGISTRE_OVERRIDES:
        overrides = REGISTRE_OVERRIDES[registre]
        for key, val in overrides.items():
            # Blend: 60% override + 40% current (so intake still matters)
            v[key] = val * 0.6 + v[key] * 0.4
    
    # Clamp all to [1, 5]
    return {k: clamp(val) for k, val in v.items()}


def blend_vectors(v_client: dict, v_intake: dict, v_inspi: dict = None, 
                  weights: tuple = (0.5, 0.3, 0.2)) -> dict:
    """Blend multiple aesthetic vectors with weights."""
    w_client, w_intake, w_inspi = weights
    
    result = {}
    for key in v_client:
        val = v_client[key] * w_client + v_intake[key] * w_intake
        if v_inspi and key in v_inspi:
            val += v_inspi[key] * w_inspi
        else:
            # Redistribute inspi weight to client
            val += v_client[key] * w_inspi
        result[key] = clamp(val)
    
    return result


# ─── Palette Computation ─────────────────────────────────────────────────────

def compute_palette(primary_hex: str, vector: dict) -> dict:
    """Compute a full palette from primary color + aesthetic vector."""
    
    h, s, l = hex_to_hsl(primary_hex)
    warmth = vector["warmth"]
    energy = vector["energy"]
    depth = vector["depth"]
    playful = vector["playful"]
    
    # Secondary: analogous warm or cold
    if warmth > 3:
        sec_h = (h + 30) % 360
    else:
        sec_h = (h - 30) % 360
    sec_s = max(10, min(100, s * (0.7 + energy * 0.06)))
    sec_l = l
    
    # Accent: split-complementary with controlled randomness
    random.seed(h * 1000 + int(energy * 100))  # deterministic from inputs
    offset = random.uniform(135, 165)
    acc_h = (h + offset) % 360
    acc_s = min(100, s * 1.2 + playful * 3)
    acc_l = max(35, min(65, 50 + (energy - 3) * 5))
    
    # Background
    is_dark = depth > 4.0
    if is_dark:
        bg_l = max(5, 12 - (depth - 4) * 3)
        bg_s = max(2, s * 0.12)
        bg_alt_l = bg_l + 3
        text_l = 92
        text_s = max(3, s * 0.08)
    else:
        bg_l = min(99, 97 - warmth * 0.8)
        bg_s = max(2, s * 0.06)
        bg_alt_l = bg_l - 2.5
        text_l = max(8, 15 - warmth * 1.2)
        text_s = max(5, s * 0.15)
    
    # Muted
    muted_s = max(5, sec_s * 0.25)
    muted_l = 55 if not is_dark else 40
    
    # Shadow tint (colored shadows from primary)
    shadow_s = max(5, s * 0.25)
    shadow_l = 20 if not is_dark else 10
    shadow_opacity = 0.08 + depth * 0.015
    
    # Proprietary: triadic complement
    prop_h = (h + 120) % 360
    prop_s = max(15, s * 0.5)
    prop_l = 70 if not is_dark else 30
    
    primary_rgb = hsl_to_rgb_str(h, s, l)
    shadow_rgb = hsl_to_rgb_str(h, shadow_s, shadow_l)
    
    return {
        "primary": primary_hex,
        "primary_rgb": primary_rgb,
        "secondary": hsl_to_hex(sec_h, sec_s, sec_l),
        "accent": hsl_to_hex(acc_h, acc_s, acc_l),
        "bg": hsl_to_hex(h, bg_s, bg_l),
        "bg_alt": hsl_to_hex(h, bg_s, bg_alt_l),
        "text": hsl_to_hex(h, text_s, text_l),
        "muted": hsl_to_hex(h, muted_s, muted_l),
        "success": hsl_to_hex(145, 50, 42),
        "error": hsl_to_hex(0, 65, 50),
        "proprietary": hsl_to_hex(prop_h, prop_s, prop_l),
        "shadow_tint": f"rgba({shadow_rgb},{round(shadow_opacity, 3)})",
        "is_dark_mode": is_dark,
    }


def infer_primary_color(vector: dict) -> str:
    """When no client color is available, infer a primary from the vector."""
    warmth = vector["warmth"]
    energy = vector["energy"]
    playful = vector["playful"]
    
    # Hue from warmth
    if warmth > 4:
        base_h = random.choice([15, 25, 35, 145, 155])  # warm: orange, terracotta, green
    elif warmth < 2:
        base_h = random.choice([210, 220, 240, 260])  # cold: blue, indigo
    else:
        base_h = random.choice([170, 180, 200, 150, 280])  # neutral: teal, sage, purple
    
    # Saturation from energy + playful
    base_s = 35 + energy * 8 + playful * 5
    
    # Lightness
    base_l = 40 + (energy - 3) * 3
    
    return hsl_to_hex(base_h, min(85, base_s), max(25, min(55, base_l)))


# ─── Typography Selection ────────────────────────────────────────────────────

def select_typography(vector: dict, recent_fonts: list = None) -> dict:
    """Select a typography pairing from the aesthetic vector."""
    
    editorial = vector["editorial"]
    playful = vector["playful"]
    organic = vector["organic"]
    warmth = vector["warmth"]
    energy = vector["energy"]
    
    # Determine display font pool
    if editorial > 3.5 and organic > 3:
        pool_key = "display_serif_elegant"
    elif energy > 3.5 and playful > 3:
        pool_key = "display_sans_bold"
    elif organic < 2 and (editorial > 3 or energy < 2.5):
        pool_key = "display_mono"
    else:
        pool_key = "display_sans_clean"
    
    # Filter recently used fonts
    available = [f for f in FONT_POOLS[pool_key] if f not in (recent_fonts or [])]
    if not available:
        available = FONT_POOLS[pool_key]
    
    random.seed(int(energy * 100 + warmth * 10 + editorial))
    display_font = random.choice(available)
    
    # Body font: complement the display
    if pool_key.startswith("display_serif"):
        body_pool = "body_readable"
    elif pool_key == "display_mono":
        body_pool = "body_readable"
    else:
        body_pool = "body_serif" if editorial > 4 else "body_readable"
    
    body_candidates = [f for f in FONT_POOLS[body_pool] if f != display_font]
    body_font = random.choice(body_candidates) if body_candidates else FONT_POOLS[body_pool][0]
    
    # Accent font
    if organic < 2.5:
        accent_font = random.choice(FONT_POOLS["display_mono"])
    else:
        accent_font = display_font
    
    return {
        "display": display_font,
        "body": body_font,
        "accent": accent_font,
        "letter_spacing_display": "-0.03em" if editorial > 4 else ("-0.02em" if editorial > 3 else "-0.01em"),
        "letter_spacing_body": "0em",
        "letter_spacing_caps": "0.12em" if editorial > 3 else "0.08em",
        "line_height_display": "1.05" if editorial > 4 else ("1.1" if editorial > 3 else "1.2"),
        "line_height_body": "1.7" if editorial > 3 else "1.6",
    }


# ─── Spacing (φ Scale) ───────────────────────────────────────────────────────

def compute_spacing(base: int = 8) -> dict:
    """Compute spacing tokens from Golden Ratio."""
    scale = []
    for i in range(-2, 8):
        scale.append(round(base * (PHI ** i)))
    
    labels = ["3xs", "2xs", "xs", "sm", "md", "lg", "xl", "2xl", "3xl", "4xl"]
    return {labels[i]: f"{scale[i]}px" for i in range(len(labels))}


def compute_type_scale(base_rem: float = 1.0) -> dict:
    """Compute typographic scale from Golden Ratio."""
    return {
        "xs":      f"{base_rem / PHI / PHI:.3f}rem",
        "sm":      f"{base_rem / PHI:.3f}rem",
        "base":    f"{base_rem:.3f}rem",
        "md":      f"{base_rem * 1.125:.3f}rem",
        "lg":      f"{base_rem * PHI * 0.78:.3f}rem",
        "xl":      f"{base_rem * PHI:.3f}rem",
        "2xl":     f"{base_rem * PHI * PHI * 0.62:.3f}rem",
        "3xl":     f"{base_rem * PHI * PHI:.3f}rem",
        "display": f"{base_rem * PHI * PHI * PHI * 0.62:.3f}rem",
        "hero":    f"clamp(2.5rem, 8vw, {base_rem * PHI**3:.1f}rem)",
    }


# ─── Motion Profile Selection ────────────────────────────────────────────────

def select_motion_profile(vector: dict) -> dict:
    """Select the optimal motion profile from the aesthetic vector."""
    
    scores = {}
    for name, profile in MOTION_PROFILES.items():
        score = 0
        for dim, (lo, hi) in profile["best_for"].items():
            val = vector.get(dim, 3.0)
            if lo <= val <= hi:
                score += 2.0
            else:
                score += max(0, 2.0 - abs(val - (lo + hi) / 2) * 0.5)
        scores[name] = score
    
    best = max(scores, key=scores.get)
    result = dict(MOTION_PROFILES[best])
    result["profile_name"] = best
    del result["best_for"]
    return result


# ─── Depth & Texture Tokens ──────────────────────────────────────────────────

def compute_depth(vector: dict, shadow_tint: str) -> dict:
    """Compute depth tokens (radii, shadows, noise, glass)."""
    
    depth = vector["depth"]
    organic = vector["organic"]
    
    # Border-radius scale
    if organic > 4:
        radii = [10, 14, 20, 28, 999]
    elif organic > 3:
        radii = [6, 10, 14, 20, 999]
    elif organic < 2:
        radii = [0, 2, 3, 4, 6]
    else:
        radii = [4, 6, 8, 12, 16]
    
    # Multi-layer shadows
    layers = max(1, round(depth))
    
    def make_shadow(base_blur):
        parts = []
        for i in range(layers):
            factor = (i + 1) / layers
            blur = round(base_blur * factor)
            y = round(blur * 0.5)
            opacity = round(0.03 + (0.06 / layers) * (layers - i), 3)
            # Replace opacity in tint
            tint_with_opacity = shadow_tint.rsplit(",", 1)[0] + f",{opacity})"
            parts.append(f"0 {y}px {blur}px {round(-blur*0.1)}px {tint_with_opacity}")
        return ", ".join(parts)
    
    return {
        "radius": {
            "sm": f"{radii[0]}px", "md": f"{radii[1]}px", "lg": f"{radii[2]}px",
            "xl": f"{radii[3]}px", "full": f"{radii[4]}px",
        },
        "shadows": {
            "sm": make_shadow(6),
            "md": make_shadow(16),
            "lg": make_shadow(32),
            "xl": make_shadow(56),
        },
        "noise_opacity": round(0.01 + depth * 0.008, 3),
        "glass_enabled": depth > 3,
        "glass_blur": f"{round(8 + depth * 2)}px",
        "glass_saturation": f"{round(150 + depth * 10)}%",
        "glass_bg_opacity": round(0.6 + (5 - depth) * 0.05, 2),
    }


# ─── CSS Custom Properties Generator ─────────────────────────────────────────

def tokens_to_css(tokens: dict) -> str:
    """Convert aura_tokens to CSS custom properties."""
    lines = [":root {"]
    
    # Palette
    p = tokens["palette"]
    lines.append("  /* Palette */")
    for key in ["primary", "primary_rgb", "secondary", "accent", "bg", "bg_alt", "text", "muted", "success", "error", "proprietary"]:
        if key in p:
            lines.append(f"  --{key.replace('_', '-')}: {p[key]};")
    
    # Typography
    t = tokens["typography"]
    lines.append("\n  /* Typography */")
    lines.append(f"  --font-display: '{t['display']}', {'serif' if 'Serif' in t['display'] or t['display'] in ('Fraunces','Cormorant','Lora','Recoleta','Erode','Zodiak') else 'sans-serif'};")
    lines.append(f"  --font-body: '{t['body']}', {'serif' if t['body'] in ('Source Serif 4','Literata','Newsreader','Charter','Lora') else 'sans-serif'};")
    lines.append(f"  --font-accent: '{t['accent']}', monospace;")
    
    # Type scale
    ts = tokens["type_scale"]
    lines.append("\n  /* Type Scale (φ) */")
    for key, val in ts.items():
        lines.append(f"  --fs-{key}: {val};")
    
    lines.append(f"  --ls-display: {t['letter_spacing_display']};")
    lines.append(f"  --lh-display: {t['line_height_display']};")
    lines.append(f"  --ls-body: {t['letter_spacing_body']};")
    lines.append(f"  --lh-body: {t['line_height_body']};")
    lines.append(f"  --ls-caps: {t['letter_spacing_caps']};")
    
    # Spacing
    sp = tokens["spacing"]
    lines.append("\n  /* Spacing (φ scale) */")
    for key, val in sp.items():
        lines.append(f"  --sp-{key}: {val};")
    
    # Motion
    m = tokens["motion"]
    lines.append("\n  /* Motion */")
    lines.append(f"  --ease: {m['curve']};")
    lines.append(f"  --duration: {m['duration_base']};")
    lines.append(f"  --stagger: {m['stagger_delay']};")
    lines.append(f"  --hover-scale: {m['hover_scale']};")
    lines.append(f"  --hover-y: {m['hover_translate_y']};")
    
    # Depth
    d = tokens["depth"]
    lines.append("\n  /* Depth */")
    for key, val in d["radius"].items():
        lines.append(f"  --radius-{key}: {val};")
    for key, val in d["shadows"].items():
        lines.append(f"  --shadow-{key}: {val};")
    lines.append(f"  --noise-opacity: {d['noise_opacity']};")
    if d["glass_enabled"]:
        lines.append(f"  --glass-blur: {d['glass_blur']};")
        lines.append(f"  --glass-saturation: {d['glass_saturation']};")
        lines.append(f"  --glass-bg-opacity: {d['glass_bg_opacity']};")
    
    lines.append("}")
    return "\n".join(lines)


# ─── Full Token Computation ──────────────────────────────────────────────────

def _color_signature_score(hex_color: str) -> float:
    """Score "signature" : saturation × clamp(lightness mid-range).
    Une signature color est typiquement vive (sat>40) ET moyennement claire (l 25-65).
    Pas un blanc cassé (l=95), pas un noir charbon (l=8)."""
    try:
        h, s, l = hex_to_hsl(hex_color)
    except Exception:
        return 0.0
    # Pénaliser extrêmes lightness
    if l > 90 or l < 8:
        return 0.0
    # Pondérer saturation × distance au mid-range
    l_score = 1.0 - abs(l - 50) / 50.0  # 1 at l=50, 0 at l=0 or 100
    return s * l_score


def _extract_primary_from_v29_brand_dna(bd: dict) -> str | None:
    """V26.Y.2 fix : adapter aura_compute au schéma V29 brand_dna_extractor.
    Préférence : couleur saturée (signature) plutôt que la plus présente (souvent un bg pâle).

    Heuristique signature : score = saturation × lightness_mid_range
    On parcourt palette_full + secondary[] et on retient le score max.
    Fallback : primary.hex tel quel si rien de saturé."""
    if not bd:
        return None
    vt = bd.get("visual_tokens") or {}
    colors = vt.get("colors") or {}

    # Collect all candidates
    candidates: list[str] = []
    primary_obj = colors.get("primary") or {}
    if isinstance(primary_obj, dict) and primary_obj.get("hex"):
        candidates.append(primary_obj["hex"])
    elif isinstance(primary_obj, str):
        candidates.append(primary_obj)
    for sec in (colors.get("secondary") or []):
        if isinstance(sec, dict) and sec.get("hex"):
            candidates.append(sec["hex"])
    for p in (colors.get("palette_full") or []):
        if isinstance(p, dict) and p.get("hex"):
            candidates.append(p["hex"])

    # Legacy fallback
    if not candidates:
        legacy = bd.get("technical", {}).get("colors", {}).get("dominant_colors") or []
        if legacy:
            return legacy[0]
        return None

    # Pick highest signature score
    scored = [(c, _color_signature_score(c)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    if scored[0][1] > 30:  # threshold : il faut au moins une couleur saturée
        return scored[0][0]
    # Sinon retourne la primary brute (cas où le brand est volontairement neutre)
    return candidates[0]


def _extract_secondary_accent_from_v29(bd: dict) -> tuple[str | None, str | None]:
    """V29 secondary[0] = secondary, secondary[1] (or palette_full[2]) = accent override."""
    if not bd:
        return None, None
    vt = bd.get("visual_tokens") or {}
    colors = vt.get("colors") or {}
    sec_list = colors.get("secondary") or []
    sec_hex = None
    acc_hex = None
    if sec_list and isinstance(sec_list, list):
        if isinstance(sec_list[0], dict):
            sec_hex = sec_list[0].get("hex")
        if len(sec_list) > 1 and isinstance(sec_list[1], dict):
            acc_hex = sec_list[1].get("hex")
    return sec_hex, acc_hex


def _extract_typography_from_v29(bd: dict) -> dict | None:
    """V29 schema : visual_tokens.typography.{h1,h2,h3,body,button}.family."""
    if not bd:
        return None
    vt = bd.get("visual_tokens") or {}
    typo = vt.get("typography") or {}
    if not typo:
        return None

    def first_font(family_str: str | None) -> str | None:
        if not family_str:
            return None
        # Strip quotes + take first font in stack
        raw = family_str.split(",")[0].strip().strip('"').strip("'")
        return raw if raw else None

    h1 = (typo.get("h1") or {}).get("family")
    body = (typo.get("body") or {}).get("family")
    button = (typo.get("button") or {}).get("family")
    display = first_font(h1)
    body_f = first_font(body)
    accent_f = first_font(button) or "JetBrains Mono"
    if not display and not body_f:
        return None
    return {
        "display": display or "Inter",
        "body": body_f or "Inter",
        "accent": accent_f,
        "letter_spacing_display": "-0.025em",
        "letter_spacing_body": "0em",
        "letter_spacing_caps": "0.14em",
        "line_height_display": "1.05",
        "line_height_body": "1.65",
        "_source": "brand_dna_v29",
    }


def compute_tokens(
    vector: dict,
    primary_color: str = None,
    brand_dna: dict = None,
    recent_fonts: list = None,
    mode: str = "B",
) -> dict:
    """Full token computation from an aesthetic vector.

    V26.Y.2 — fixé pour respecter brand_dna V29 (visual_tokens.colors + typography).
    Mode B (avec brand_dna) :
      • palette primary = brand_dna.visual_tokens.colors.primary.hex
      • palette secondary = brand_dna.visual_tokens.colors.secondary[0].hex (si dispo)
      • palette accent = brand_dna.visual_tokens.colors.secondary[1].hex (si dispo)
      • typography display+body+button = familles client préservées
    AURA calcule encore : bg, bg_alt, text, muted, success, error, shadow_tint,
    type_scale (φ), spacing (8px grid), motion (spring/ease selon vector),
    depth (shadows + radius selon vector).
    """
    # Determine primary color (V29-aware)
    if primary_color:
        primary = primary_color
    else:
        v29_primary = _extract_primary_from_v29_brand_dna(brand_dna)
        if v29_primary:
            primary = v29_primary
        else:
            primary = infer_primary_color(vector)

    # Compute palette mathematically derived from primary
    palette = compute_palette(primary, vector)

    # Override secondary + accent with brand_dna client values if available
    bd_sec, bd_acc = _extract_secondary_accent_from_v29(brand_dna)
    if bd_sec:
        palette["secondary"] = bd_sec
    if bd_acc:
        palette["accent"] = bd_acc

    # Typography : preserve client fonts if brand_dna present
    bd_typo = _extract_typography_from_v29(brand_dna)
    if bd_typo:
        typography = bd_typo
    else:
        typography = select_typography(vector, recent_fonts)

    spacing = compute_spacing()
    type_scale = compute_type_scale()
    motion = select_motion_profile(vector)
    depth = compute_depth(vector, palette["shadow_tint"])
    
    tokens = {
        "version": "16.0.0",
        "mode": mode,
        "vector": vector,
        "palette": palette,
        "typography": typography,
        "spacing": spacing,
        "type_scale": type_scale,
        "motion": motion,
        "depth": depth,
    }
    
    # Generate CSS
    tokens["css_custom_properties"] = tokens_to_css(tokens)
    
    return tokens


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AURA Compute — Design Token Calculator")
    parser.add_argument("--energy", type=float, default=3.0, help="Energy slider (1-5)")
    parser.add_argument("--tonality", type=float, default=3.0, help="Tonality slider (1-5)")
    parser.add_argument("--business", type=str, default="", help="Business type")
    parser.add_argument("--registre", type=str, default="", help="Registre override")
    parser.add_argument("--primary-color", type=str, default=None, help="Primary color hex")
    parser.add_argument("--brand-dna", type=str, default=None, help="Path to design_dna.json")
    parser.add_argument("--output", type=str, default=None, help="Output path for aura_tokens.json")
    parser.add_argument("--css-only", action="store_true", help="Output only CSS custom properties")
    args = parser.parse_args()
    
    # Load brand DNA if provided
    brand_dna = None
    client_vector = None
    if args.brand_dna:
        brand_dna = json.load(open(args.brand_dna))
        client_vector = brand_dna.get("aesthetic_vector", {})
    
    # Compute intake vector
    intake_vector = intake_to_vector(args.energy, args.tonality, args.business, args.registre)
    
    # Blend vectors if hybrid mode
    if client_vector:
        mode = "C" if args.energy != 3.0 or args.tonality != 3.0 else "A"
        if mode == "C":
            vector = blend_vectors(client_vector, intake_vector, weights=(0.5, 0.4, 0.1))
        else:
            vector = blend_vectors(client_vector, intake_vector, weights=(0.7, 0.3, 0.0))
    else:
        mode = "B"
        vector = intake_vector
    
    # Compute tokens
    tokens = compute_tokens(
        vector=vector,
        primary_color=args.primary_color,
        brand_dna=brand_dna,
        mode=mode,
    )
    
    if args.css_only:
        print(tokens["css_custom_properties"])
    elif args.output:
        with open(args.output, "w") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        print(f"Saved → {args.output}")
        print(f"Vector: {tokens['vector']}")
        print(f"Palette: {tokens['palette']['primary']} → {tokens['palette']['accent']}")
        print(f"Fonts: {tokens['typography']['display']} + {tokens['typography']['body']}")
        print(f"Motion: {tokens['motion']['name']}")
    else:
        print(json.dumps(tokens, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
