"""Deterministic design tokens for the canonical GSG renderer.

The goal is to turn Brand DNA / Design Grammar / AURA into a compact token
contract the system can render from. No prose dumping, no mega-prompt.
"""
from __future__ import annotations

import pathlib
import re
from typing import Any

from .minimal_guards import choose_target_fonts

ROOT = pathlib.Path(__file__).resolve().parents[2]

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _hex(value: Any, fallback: str) -> str:
    if isinstance(value, dict):
        value = value.get("hex")
    if isinstance(value, str) and HEX_RE.match(value.strip()):
        return value.strip()
    return fallback


def _first_palette_color(colors: dict[str, Any], index: int, fallback: str) -> str:
    palette = colors.get("palette_full")
    if isinstance(palette, list) and len(palette) > index:
        return _hex(palette[index], fallback)
    return fallback


def _palette(colors: dict[str, Any]) -> list[str]:
    raw = colors.get("palette_full")
    out: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            hx = _hex(item, "")
            if hx:
                out.append(hx)
    for key in ("primary", "accent", "background", "text"):
        hx = _hex(colors.get(key), "")
        if hx and hx not in out:
            out.append(hx)
    secondary = colors.get("secondary")
    if isinstance(secondary, list):
        for item in secondary:
            hx = _hex(item, "")
            if hx and hx not in out:
                out.append(hx)
    return out


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _luminance(hex_color: str) -> float:
    r, g, b = _rgb(hex_color)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def _saturation(hex_color: str) -> float:
    r, g, b = [v / 255 for v in _rgb(hex_color)]
    mx, mn = max(r, g, b), min(r, g, b)
    return 0 if mx == 0 else (mx - mn) / mx


def _pick_dark(palette: list[str], fallback: str) -> str:
    return min(palette, key=_luminance) if palette else fallback


def _pick_saturated(palette: list[str], fallback: str, *, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    candidates = [
        hx for hx in palette
        if hx not in exclude and 0.12 <= _luminance(hx) <= 0.82 and _saturation(hx) >= 0.25
    ]
    if not candidates:
        return fallback
    return max(candidates, key=lambda hx: (_saturation(hx), -abs(_luminance(hx) - 0.42)))


def _tokens_from_grammar(design_grammar: dict[str, Any] | None) -> dict[str, Any]:
    if not design_grammar:
        return {}
    tokens = design_grammar.get("tokens") if isinstance(design_grammar, dict) else {}
    return tokens if isinstance(tokens, dict) else {}


def load_aura_tokens(client: str, page_type: str | None = None) -> dict[str, Any] | None:
    """Load AURA tokens without pulling the full client context router."""
    candidates = []
    if page_type:
        candidates.append(ROOT / "data" / "captures" / client / page_type / "aura_tokens.json")
    candidates.append(ROOT / "data" / f"_aura_{client}.json")
    for fp in candidates:
        if fp.exists():
            try:
                import json

                data = json.loads(fp.read_text())
                return data if isinstance(data, dict) else None
            except Exception:
                return None
    return None


def build_design_tokens(
    *,
    client: str,
    brand_dna: dict[str, Any],
    design_grammar: dict[str, Any] | None = None,
    aura_tokens: dict[str, Any] | None = None,
    visual_intelligence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic design tokens for controlled rendering."""
    grammar_tokens = _tokens_from_grammar(design_grammar)
    colors = (
        grammar_tokens.get("colors")
        or ((brand_dna.get("visual_tokens") or {}).get("colors") or {})
    )
    colors = colors if isinstance(colors, dict) else {}
    fonts = choose_target_fonts(brand_dna)

    palette = _palette(colors)
    ink = _hex(colors.get("text"), _pick_dark(palette, "#17123a"))
    primary = _pick_saturated(palette, _hex(colors.get("primary"), "#493ce0"), exclude={ink})
    accent = _pick_saturated(palette, _first_palette_color(colors, 7, primary), exclude={ink, primary})
    soft = _first_palette_color(colors, 0, "#f5f1fa")
    soft_alt = _first_palette_color(colors, 1, "#edf7ff")
    muted = "#5d5871"
    border = "#ddd8e8"
    on_primary = "#ffffff" if _luminance(primary) < 0.46 else ink

    shape = grammar_tokens.get("shape") if isinstance(grammar_tokens.get("shape"), dict) else {}
    spacing = grammar_tokens.get("spacing") if isinstance(grammar_tokens.get("spacing"), dict) else {}
    motion = grammar_tokens.get("motion") if isinstance(grammar_tokens.get("motion"), dict) else {}

    aura_vector = {}
    if isinstance(aura_tokens, dict):
        aura_vector = aura_tokens.get("vector") or aura_tokens.get("aesthetic_vector") or {}
    visual_intelligence = visual_intelligence or {}

    def _rhythm_value(key: str, fallback: float) -> float:
        if not aura_vector:
            return fallback
        try:
            return float(aura_vector.get(key, fallback) or fallback)
        except Exception:
            return fallback

    density_label = visual_intelligence.get("density", "")
    energy_label = visual_intelligence.get("energy", "")
    density_bias = 0.5 if "high" in density_label else (-0.5 if "low" in density_label else 0)
    energy_bias = 0.5 if "high" in energy_label else 0

    return {
        "client": client,
        "version": "gsg-design-tokens-v27.2",
        "colors": {
            "bg": "#fbfaf7",
            "surface": "#ffffff",
            "surface_alt": soft_alt,
            "ink": ink,
            "muted": muted,
            "primary": primary,
            "on_primary": on_primary,
            "accent": accent,
            "soft": soft,
            "border": border,
        },
        "typography": {
            "display": fonts["display"],
            "body": fonts["body"],
            "mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
        },
        "spacing": {
            "content": "min(760px, calc(100vw - 40px))",
            "wide": "min(1120px, calc(100vw - 40px))",
            "section_y": spacing.get("section_y") or "112px",
            "paragraph_gap": "1.2em",
        },
        "shape": {
            "radius": shape.get("border_radius") or "8px",
            "radius_subtle": shape.get("radius_subtle") or "6px",
        },
        "motion": {
            "duration": motion.get("duration") or "180ms",
            "easing": motion.get("easing") or "cubic-bezier(.2,.8,.2,1)",
        },
        "aura_vector": aura_vector,
        "aura_input_contract": visual_intelligence.get("aura_input_contract") or {},
        "visual_rhythm": {
            "energy": round(max(1, min(5, _rhythm_value("energy", 3) + energy_bias)), 2),
            "density": round(max(1, min(5, _rhythm_value("density", 3) + density_bias)), 2),
            "depth": round(max(1, min(5, _rhythm_value("depth", 2))), 2),
            "motion": round(max(1, min(5, _rhythm_value("motion", 2))), 2),
            "editorial": round(max(1, min(5, _rhythm_value("editorial", 3) + (1 if visual_intelligence.get("editoriality") == "high" else 0))), 2),
        },
        "policy": {
            "one_accent_only": True,
            "gradient_policy": "forbid_ai_slop_mesh_allow_subtle_brand_depth",
            "no_card_grid": True,
            "letter_spacing": "0",
            "visual_role": visual_intelligence.get("visual_role"),
        },
    }


def render_design_tokens_css(tokens: dict[str, Any]) -> str:
    """Render CSS variables for the controlled renderer."""
    c = tokens["colors"]
    t = tokens["typography"]
    s = tokens["spacing"]
    sh = tokens["shape"]
    m = tokens["motion"]
    vr = tokens.get("visual_rhythm") or {}
    return f""":root {{
  --gsg-bg: {c['bg']};
  --gsg-surface: {c['surface']};
  --gsg-surface-alt: {c['surface_alt']};
  --gsg-ink: {c['ink']};
  --gsg-muted: {c['muted']};
  --gsg-primary: {c['primary']};
  --gsg-on-primary: {c.get('on_primary', '#ffffff')};
  --gsg-accent: {c['accent']};
  --gsg-soft: {c['soft']};
  --gsg-border: {c['border']};
  --gsg-font-display: {t['display']};
  --gsg-font-body: {t['body']};
  --gsg-font-mono: {t['mono']};
  --gsg-content: {s['content']};
  --gsg-wide: {s['wide']};
  --gsg-section-y: {s['section_y']};
  --gsg-radius: {sh['radius']};
  --gsg-radius-subtle: {sh['radius_subtle']};
  --gsg-duration: {m['duration']};
  --gsg-easing: {m['easing']};
  --gsg-energy: {vr.get('energy', 3)};
  --gsg-density: {vr.get('density', 3)};
  --gsg-depth: {vr.get('depth', 2)};
  --gsg-motion: {vr.get('motion', 2)};
}}"""
