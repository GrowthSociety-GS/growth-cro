"""Runtime font / design-grammar fix-ups for Mode 1 PERSONA NARRATOR.

Sprint AD-2 V26.AD garde-fou + Sprint F V26.AC post-gates. All helpers
here are *defensive*: they assume Sonnet may have ignored the HARD
CONSTRAINT and inject AI-slop fonts (Inter / Roboto / Open Sans / …)
into the CSS, so we rewrite **only** the CSS declarations
(``font-family``, ``--font-*``, Google Fonts URL, ``@font-face``). Body
text is **never** touched (so words like "Internet", "Lateral" survive).

  * ``AI_SLOP_FONTS`` / ``NON_AI_SLOP_BODY_ALTERNATIVES`` — known
    blacklist + curated alternatives (Google-Fonts-loadable).
  * ``_substitute_ai_slop_in_aura(aura)`` — pre-prompt substitution
    inside the AURA tokens block (typography.body + css_custom_properties).
  * ``_extract_brand_font_family(brand_dna)`` — pull the 1st font family
    from ``visual_tokens.typography.h1`` for the HARD CONSTRAINT line.
  * ``_repair_ai_slop_fonts(html, ...)`` — post-call rewrite, returns
    ``(html_repaired, repair_log)``.
  * ``_check_aura_font_violations(html)`` — pure detection, returns the
    list of blacklist fonts still present in the HTML.
  * ``_check_design_grammar_violations(html, design_grammar)`` — checks
    forbidden_patterns from design_grammar V30.
"""
from __future__ import annotations

import copy
import re
from typing import Optional


AI_SLOP_FONTS = {"Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat",
                 "Poppins", "Nunito", "Helvetica"}
NON_AI_SLOP_BODY_ALTERNATIVES = ["DM Sans", "IBM Plex Sans", "Spectral",
                                  "Source Sans 3", "Outfit"]


# Same set as AI_SLOP_FONTS but kept as the legacy mutable list because
# _repair_ai_slop_fonts iterates with a stable order for deterministic logs.
_AI_SLOP_FONT_BLACKLIST = ["Inter", "Roboto", "Open Sans", "Lato", "Montserrat", "Poppins", "Nunito", "Helvetica"]


def _substitute_ai_slop_in_aura(aura: dict) -> tuple[dict, dict]:
    """Sprint G V26.AC fix — substitute AI-slop fonts in AURA before injection.

    If ``aura.typography.body`` is Inter / Roboto / etc → swap for "DM Sans"
    (1st curated non-AI-slop alternative). If
    ``aura.css_custom_properties`` contains ``--font-…: Inter`` → idem.

    Returns: ``(aura_clean, substitutions_log)``.
    """
    aura_clean = copy.deepcopy(aura)
    substitutions: dict = {}

    # Substituer typography.body si AI-slop
    typo = aura_clean.get("typography", {})
    if isinstance(typo, dict):
        body = typo.get("body")
        if body and body in AI_SLOP_FONTS:
            substitutions["typography.body"] = f"{body} → DM Sans (anti-AI-slop)"
            typo["body"] = "DM Sans"
            typo["body_substituted_from"] = body

    # Substituer dans css_custom_properties
    css_props = aura_clean.get("css_custom_properties")
    if isinstance(css_props, dict):
        for key, val in list(css_props.items()):
            if "font" in key.lower() and isinstance(val, str):
                for slop in AI_SLOP_FONTS:
                    if slop in val:
                        new_val = val.replace(slop, "DM Sans")
                        css_props[key] = new_val
                        substitutions[f"css.{key}"] = f"{slop} → DM Sans"
                        break
    elif isinstance(css_props, str):
        for slop in AI_SLOP_FONTS:
            if slop in css_props:
                aura_clean["css_custom_properties"] = css_props.replace(slop, "DM Sans")
                substitutions["css_props_str"] = f"{slop} → DM Sans"
                break

    return aura_clean, substitutions


def _extract_brand_font_family(brand_dna: dict) -> Optional[str]:
    """Extract the primary typography family for HARD CONSTRAINT injection.

    Reads ``visual_tokens.typography.h1.family`` and returns the first
    family in the comma-separated stack (e.g. ``"Ppneuemontreal, Arial,
    sans-serif"`` → ``"Ppneuemontreal"``). ``None`` if absent.
    """
    typo = (brand_dna.get("visual_tokens") or {}).get("typography") or {}
    if not isinstance(typo, dict):
        return None
    h1 = typo.get("h1")
    if isinstance(h1, dict) and h1.get("family"):
        return h1["family"].split(",")[0].strip()
    return None


def _check_aura_font_violations(html: str) -> list[str]:
    """Sprint F V26.AC POST-GATE — detect AURA blacklist fonts in HTML."""
    blacklist = ["Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat", "Poppins", "Nunito", "Helvetica"]
    violations = []
    html_lower = html.lower()
    for font in blacklist:
        # Search font-family / Google Fonts URL forms
        if (
            f"family={font.replace(' ', '+')}".lower() in html_lower
            or f'"{font}"'.lower() in html_lower
            or f"'{font}'".lower() in html_lower
            or f"font-family: {font}".lower() in html_lower
        ):
            violations.append(font)
    return violations


def _check_design_grammar_violations(html: str, design_grammar: Optional[dict]) -> list[str]:
    """Sprint F V26.AC POST-GATE — check forbidden_patterns from design_grammar."""
    if not design_grammar:
        return []
    forbid = design_grammar.get("forbidden") or {}
    if not forbid:
        return []
    patterns = forbid.get("patterns") or forbid.get("forbidden_patterns") or []
    violations = []
    html_lower = html.lower()
    for p in patterns[:10]:
        if isinstance(p, dict):
            rule = p.get("rule") or p.get("pattern") or ""
            check = p.get("html_check") or ""  # optional regex/keyword to detect
            if check and check.lower() in html_lower:
                violations.append(str(rule)[:100])
    return violations


def _repair_ai_slop_fonts(
    html: str,
    *,
    target_display_font: Optional[str] = None,
    target_body_font: str = "DM Sans",
    target_body_alt_loadable: str = "DM Sans",
) -> tuple[str, list[str]]:
    """Sprint AD-2 V26.AD post-gate — rewrite AI-slop fonts in CSS only.

    Variance T=0.85 means Sonnet sometimes re-introduces Inter / Roboto /
    etc. into the CSS despite the HARD CONSTRAINT. This rewrites only the
    declarations (``font-family``, ``--font-*``, Google Fonts URL,
    ``@font-face``). Body text is never touched.

    Args:
      html: HTML produit par Sonnet
      target_display_font: font à utiliser pour h1/h2/h3 (ex: "Ppneuemontreal").
        Si None, fallback sur target_body_alt_loadable (DM Sans).
      target_body_font: font à utiliser pour body/p/li (ex: "DM Sans" — non-AI-slop).
      target_body_alt_loadable: fallback si target_display_font non chargeable
        depuis Google Fonts (ex: Ppneuemontreal commercial → DM Sans loaded).

    Returns: (html_repaired, list of repairs applied)
    """
    repairs = []
    out = html

    # 1. Google Fonts URLs : si family=Inter (ou autre AI-slop), substitute
    # On charge DM Sans qui est Google Fonts, garanti loadable.
    for slop in _AI_SLOP_FONT_BLACKLIST:
        slop_url = slop.replace(" ", "+")
        # match `family=Inter` or `family=Open+Sans` (with optional weight specs after `:`)
        pattern = rf"family={re.escape(slop_url)}(?=[\s\"&:'])"
        if re.search(pattern, out):
            out = re.sub(pattern, f"family={target_body_font.replace(' ', '+')}", out)
            repairs.append(f"google_fonts_url: family={slop} → family={target_body_font}")

    # 2. CSS custom properties --font-* : map AI-slop → display/body target
    # The display fonts go to --font-display, --font-heading, --font-h*
    # The body fonts go to --font-body, --font-text, --font-p
    for slop in _AI_SLOP_FONT_BLACKLIST:
        # --font-display: 'Inter' → --font-display: 'Ppneuemontreal'
        if target_display_font:
            for display_var in ["--font-display", "--font-heading", "--font-h1", "--font-h2", "--font-h3", "--font-title"]:
                pat = rf"({re.escape(display_var)}\s*:\s*['\"])({re.escape(slop)})(['\"])"
                if re.search(pat, out):
                    out = re.sub(pat, rf"\1{target_display_font}\3", out)
                    repairs.append(f"css_var: {display_var}: '{slop}' → '{target_display_font}'")
        # --font-body / --font-text → DM Sans
        for body_var in ["--font-body", "--font-text", "--font-p", "--font-base", "--font-accent"]:
            pat = rf"({re.escape(body_var)}\s*:\s*['\"])({re.escape(slop)})(['\"])"
            if re.search(pat, out):
                out = re.sub(pat, rf"\1{target_body_font}\3", out)
                repairs.append(f"css_var: {body_var}: '{slop}' → '{target_body_font}'")

    # 3. Direct font-family declarations: `font-family: 'Inter', ...` → DM Sans (body)
    # On ne sait pas si c'est display ou body, donc on prend body (safer for content)
    for slop in _AI_SLOP_FONT_BLACKLIST:
        pattern = rf"(font-family\s*:\s*['\"])({re.escape(slop)})(['\"])"
        if re.search(pattern, out):
            out = re.sub(pattern, rf"\1{target_body_font}\3", out)
            repairs.append(f"font-family: '{slop}' → '{target_body_font}'")

    # 4. @font-face url with AI-slop font (rare but possible)
    for slop in _AI_SLOP_FONT_BLACKLIST:
        pattern = rf"@font-face\s*\{{[^}}]*?font-family\s*:\s*['\"]({re.escape(slop)})['\"][^}}]*?\}}"
        if re.search(pattern, out, re.DOTALL):
            repairs.append(f"@font-face: {slop} block detected — left unchanged (safer)")

    return out, repairs


__all__ = [
    "AI_SLOP_FONTS",
    "NON_AI_SLOP_BODY_ALTERNATIVES",
    "_substitute_ai_slop_in_aura",
    "_extract_brand_font_family",
    "_check_aura_font_violations",
    "_check_design_grammar_violations",
    "_repair_ai_slop_fonts",
]
