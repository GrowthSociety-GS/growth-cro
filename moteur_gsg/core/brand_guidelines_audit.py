"""Brand-guidelines runtime audit — V27.2-H Sprint 16 (T16-3).

Python heuristic implementation of the ``brand-guidelines`` Anthropic
skill. Runs at runtime against the rendered HTML + the client's
``brand_dna.json`` to check brand colors propagation, tone keywords
adherence, and forbidden phrases absence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MIN_SCORE = 7


def _load_brand_dna(client: str) -> dict[str, Any]:
    """Load the client's brand_dna.json (best-effort, returns {} on failure)."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "data" / "captures" / client / "brand_dna.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _signature_colors_in_css(html: str, brand_dna: dict[str, Any]) -> tuple[bool, str]:
    """The brand signature colors must appear in the rendered CSS."""
    sig = brand_dna.get("signature_colors") or brand_dna.get("colors") or {}
    if isinstance(sig, dict):
        # Try the common shape : {"primary": "#hex", "accent": "#hex", ...}
        candidates = [v for v in sig.values() if isinstance(v, str) and v.startswith("#")]
    elif isinstance(sig, list):
        candidates = [c for c in sig if isinstance(c, str) and c.startswith("#")]
    else:
        candidates = []
    if not candidates:
        return True, ""  # nothing to check — soft pass
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style> to scan for brand colors"
    css_lower = css_block.group(1).lower()
    matches = sum(1 for c in candidates if c.lower() in css_lower)
    if matches == 0:
        return False, f"None of the brand signature colors ({', '.join(candidates[:3])}) appear in CSS"
    return True, ""


def _tone_keywords_check(html: str, brand_dna: dict[str, Any]) -> tuple[bool, str]:
    """At least 1 brand-tone keyword should be present in the body copy."""
    tone = brand_dna.get("tone") or brand_dna.get("voice", {})
    if isinstance(tone, dict):
        keywords = tone.get("keywords") or tone.get("characteristics") or []
    elif isinstance(tone, list):
        keywords = tone
    else:
        keywords = []
    if not keywords:
        return True, ""  # no tone defined
    # Strip HTML tags to get plain body text
    plain = re.sub(r"<[^>]+>", " ", html).lower()
    keywords_lower = [str(k).lower() for k in keywords if k]
    # Soft check : we're not enforcing literal keyword presence (would
    # be silly — "confident" the adjective rarely appears), but rather
    # that the tone is reflected. Pass if ANY characteristic-related
    # term is present.
    related_terms = {
        "confident": ["sûr", "certain", "garanti", "promesse"],
        "warm": ["bienveillant", "humain", "amical", "ensemble"],
        "direct": ["clair", "concret", "simple", "sans détour"],
        "professional": ["professionnel", "expert", "qualifié"],
        "playful": ["fun", "ludique", "jeu"],
    }
    found_any = False
    for kw in keywords_lower:
        if kw in plain:
            found_any = True
            break
        for related in related_terms.get(kw, []):
            if related in plain:
                found_any = True
                break
    if not found_any:
        return False, f"Brand tone ({', '.join(keywords_lower[:3])}) not reflected in copy keywords"
    return True, ""


def _banned_anti_bullshit_check(html: str) -> tuple[bool, str]:
    """Hard ban : 'révolutionnaire', 'leader', 'disruptif', 'game-changer', etc.

    GrowthCRO doctrine (CLAUDE.md anti-patterns) — never use these in
    copy. This check is independent of the brand_dna : it's a project-
    wide invariant.
    """
    banned = [
        r"\brévolutionnaire\b",
        r"\bleader\s+(?:du|de\s+la)\s+(?:marché|industrie)",
        r"\bdisruptif\b",
        r"\bgame[- ]?changer\b",
        r"\bunique\s+au\s+monde\b",
        r"\bbest[- ]in[- ]class\b",
        r"\bcutting[- ]edge\b",
    ]
    plain = re.sub(r"<[^>]+>", " ", html).lower()
    hits = []
    for pattern in banned:
        if re.search(pattern, plain):
            hits.append(pattern)
    if hits:
        return False, f"Banned anti-bullshit words found : {', '.join(hits)}"
    return True, ""


def _brand_name_density_check(html: str, brand_dna: dict[str, Any]) -> tuple[bool, str]:
    """Brand name should appear ≥ 3 times in the body (recognition)
    but ≤ 30 times (anti-spam)."""
    brand = (brand_dna.get("brand") or brand_dna.get("name") or "").strip()
    if not brand or len(brand) < 2:
        return True, ""
    plain = re.sub(r"<[^>]+>", " ", html).lower()
    count = plain.count(brand.lower())
    if count < 3:
        return False, f"Brand name '{brand}' appears only {count} times — under-mentioned"
    if count > 30:
        return False, f"Brand name '{brand}' appears {count} times — over-spammed"
    return True, ""


def _signature_fonts_check(html: str, brand_dna: dict[str, Any]) -> tuple[bool, str]:
    """If brand_dna lists signature fonts, at least 1 must be loaded."""
    typo = brand_dna.get("typography") or {}
    fonts = []
    if isinstance(typo, dict):
        for v in typo.values():
            if isinstance(v, str):
                fonts.append(v)
            elif isinstance(v, dict) and v.get("family"):
                fonts.append(v["family"])
    if not fonts:
        return True, ""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style> to scan for brand fonts"
    css_lower = css_block.group(1).lower()
    matches = sum(1 for f in fonts if f.lower() in css_lower)
    if matches == 0:
        return False, f"None of the brand fonts ({', '.join(fonts[:3])}) appear in CSS"
    return True, ""


_CHECKS = [
    ("signature_colors_propagation", _signature_colors_in_css, "warning"),
    ("tone_keywords_reflected", _tone_keywords_check, "info"),
    ("banned_anti_bullshit", _banned_anti_bullshit_check, "critical"),
    ("brand_name_density", _brand_name_density_check, "warning"),
    ("signature_fonts", _signature_fonts_check, "info"),
]


def run_brand_guidelines_audit(html: str, client: str | None = None) -> dict[str, Any]:
    """Run the brand-guidelines heuristic audit."""
    brand_dna = _load_brand_dna(client) if client else {}
    gaps: list[dict[str, Any]] = []
    deduction = 0.0
    for check_id, check_fn, severity in _CHECKS:
        try:
            if check_fn is _banned_anti_bullshit_check:
                passed, description = check_fn(html)
            else:
                passed, description = check_fn(html, brand_dna)
        except Exception as exc:
            passed, description = False, f"check raised: {exc}"
        if not passed:
            weight = {"critical": 2.0, "warning": 1.0, "info": 0.5}.get(severity, 1.0)
            deduction += weight
            gaps.append({
                "id": check_id,
                "severity": severity,
                "description": description,
            })
    score = max(0, min(10, int(round(10 - deduction))))
    return {
        "version": "brand-guidelines-audit-v1.0",
        "score": score,
        "passed": score >= MIN_SCORE,
        "gaps": gaps,
        "checks_run": len(_CHECKS),
        "brand_dna_loaded": bool(brand_dna),
    }


__all__ = ["run_brand_guidelines_audit", "MIN_SCORE"]
