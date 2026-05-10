"""Sprint AD-6 V26.AD+ — anti-AI-slop visual pattern detection + repair.

Pure regex-based detection of "obvious AI-generated 2024" CSS signatures
(135deg avatar gradients, gradient mesh, RGBA gradient boxes, blog-2018
border-left callouts, neumorphism, glassmorphism, pill-button-999px,
3-cards SaaS-2018 templates, fake stars, FOMO countdown timers).

V26.AG default = report-only. ``_repair_ai_slop_visual_patterns()`` is
opt-in (the V26.AF aggressive auto-repair path produced anti-design
"white pages"). Structural patterns (3-cards grid, FOMO countdown) are
flagged but never auto-fixed — Sonnet has to avoid them upstream.
"""
from __future__ import annotations

import re


def _check_ai_slop_visual_patterns(html: str) -> list[dict]:
    """Detect AI-slop visual signatures in ``html``.

    Returns: list of ``{pattern, severity, count, sample, fix}`` dicts.
    """
    violations = []
    html_lower = html.lower()  # noqa: F841 — kept for parity (legacy used it)

    # 1. Gradient 135deg avatar (signature ChatGPT/Claude design 2024)
    pattern_135 = re.findall(r"linear-gradient\(\s*135deg[^)]+\)", html, re.IGNORECASE)
    if pattern_135:
        violations.append({
            "pattern": "gradient_135deg_avatar",
            "severity": "high",
            "count": len(pattern_135),
            "sample": pattern_135[0][:120],
            "fix": "Use a real photo, monochrome monogramme initials on white bg, or solid color circle.",
        })

    # 2. Gradient mesh / radial multi-stop background
    radial_mesh = re.findall(r"radial-gradient\([^)]+\)", html, re.IGNORECASE)
    if len(radial_mesh) >= 2:
        violations.append({
            "pattern": "gradient_mesh_background",
            "severity": "high",
            "count": len(radial_mesh),
            "sample": radial_mesh[0][:120],
            "fix": "Solid neutral background. If you need depth, use subtle hairline rules, not gradients.",
        })

    # 3. RGBA gradient box (insight-box pattern AI 2023-2024)
    rgba_gradient = re.findall(r"linear-gradient\([^)]*rgba?\s*\([^)]+\)[^)]*rgba?\s*\([^)]+\)[^)]*\)", html, re.IGNORECASE)
    if rgba_gradient:
        violations.append({
            "pattern": "rgba_gradient_box",
            "severity": "medium",
            "count": len(rgba_gradient),
            "sample": rgba_gradient[0][:120],
            "fix": "Use solid neutral background or pure white box with hairline border.",
        })

    # 4. Border-left colored callout (template blog 2018)
    border_left_callout = re.findall(r"border-left\s*:\s*\d+px\s+solid\s+var\(--[\w-]*(?:primary|accent|secondary)[\w-]*\)", html, re.IGNORECASE)
    if border_left_callout:
        violations.append({
            "pattern": "border_left_callout_blog2018",
            "severity": "medium",
            "count": len(border_left_callout),
            "sample": border_left_callout[0][:120],
            "fix": "Use marginalia (offset to side), inline stat callout (number + caption), or pull quote with italic only.",
        })

    # 5. Neumorphism shadows (2020 trend dépassée)
    neumorphism = re.findall(r"box-shadow\s*:\s*[^;]*-?\d+px\s+-?\d+px\s+\d+px[^;]+inset", html, re.IGNORECASE)
    if neumorphism:
        violations.append({
            "pattern": "neumorphism_shadow",
            "severity": "high",
            "count": len(neumorphism),
            "sample": neumorphism[0][:120],
            "fix": "Use single subtle drop shadow OR no shadow + hairline border.",
        })

    # 6. Glassmorphism (backdrop-filter blur cards)
    glassmorphism = re.findall(r"backdrop-filter\s*:\s*blur\s*\(", html, re.IGNORECASE)
    if glassmorphism:
        violations.append({
            "pattern": "glassmorphism_blur",
            "severity": "medium",
            "count": len(glassmorphism),
            "sample": glassmorphism[0][:120],
            "fix": "Use solid card or semi-transparent overlay without blur (2024 trend → out).",
        })

    # 7. Pill button radius 999px on regular CTA (= cheap signal sauf si signature brand)
    pill_buttons = re.findall(r"\.cta[^{]*\{[^}]*border-radius\s*:\s*999", html, re.IGNORECASE)
    if pill_buttons:
        violations.append({
            "pattern": "pill_button_999px",
            "severity": "low",
            "count": len(pill_buttons),
            "sample": pill_buttons[0][:80],
            "fix": "Use radius 4-8px (= signal pro éditorial) sauf si pill 999px est signature explicite de la brand.",
        })

    # 8. 3-cards grid with icons (template SaaS 2018)
    # Heuristic: ≥3 sibling .card / .feature classes
    card_count = len(re.findall(r"class=[\"'][^\"']*(?:feature-card|value-card|pricing-card)[^\"']*[\"']", html, re.IGNORECASE))
    if card_count >= 3:
        violations.append({
            "pattern": "three_cards_grid_template2018",
            "severity": "medium",
            "count": card_count,
            "sample": f"{card_count} feature-/value-/pricing-card detected",
            "fix": "Replace with prose narrative + UI screenshot alternance (Linear/Vercel pattern).",
        })

    # 9. Star rating fake ⭐ ⭐ ⭐ ⭐ ⭐ inline
    stars = re.findall(r"⭐\s*⭐\s*⭐", html)
    if stars:
        violations.append({
            "pattern": "fake_stars_inline",
            "severity": "high",
            "count": len(stars),
            "sample": "⭐⭐⭐ inline detected",
            "fix": "Use named testimonial with photo + position OR specific number (4.7/5 from 234 reviews).",
        })

    # 10. FOMO countdown timer
    countdown = re.findall(r"\b(?:countdown|timer|expires?-in|ends-in)\b[^>]*>\s*\d+\s*[hms:]", html, re.IGNORECASE)
    if countdown:
        violations.append({
            "pattern": "fomo_countdown_timer",
            "severity": "high",
            "count": len(countdown),
            "sample": countdown[0][:80],
            "fix": "Remove countdown — fake urgency = trust killer. Honest reassurance line instead.",
        })

    return violations


def _repair_ai_slop_visual_patterns(html: str, violations: list[dict]) -> tuple[str, list[str]]:
    """Sprint AD-6 — opt-in CSS-only repair of select AI-slop patterns.

    Only the safe-to-rewrite CSS patterns are touched (font-family is
    handled separately by ``runtime_fixes._repair_ai_slop_fonts``). For
    structural patterns (3-cards grid, FOMO countdown), we just flag —
    Sonnet has to avoid them upstream via the prompt.
    """
    repairs = []
    out = html

    for v in violations:
        if v["pattern"] == "gradient_135deg_avatar":
            # Replace `linear-gradient(135deg, A, B)` background sur avatar par color solid neutre
            # Heuristique : garde la couleur A, drop le gradient
            def replace_avatar_gradient(m):
                inner = m.group(0)
                # Extract first color
                color_match = re.search(r"#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)", inner)
                first_color = color_match.group(0) if color_match else "#1a1a1a"
                return first_color
            new_out = re.sub(r"linear-gradient\(\s*135deg[^)]+\)", replace_avatar_gradient, out)
            if new_out != out:
                out = new_out
                repairs.append(f"gradient_135deg_avatar: replaced {v['count']} gradient(s) by solid color")

        # rgba_gradient_box — replace by solid neutral
        if v["pattern"] == "rgba_gradient_box":
            new_out = re.sub(
                r"linear-gradient\([^)]*rgba?\s*\([^)]+\)[^)]*rgba?\s*\([^)]+\)[^)]*\)",
                "var(--color-surface, #f5f5f5)",
                out,
            )
            if new_out != out:
                out = new_out
                repairs.append(f"rgba_gradient_box: replaced {v['count']} rgba gradient(s) by solid surface var")

        # border_left_callout_blog2018 — replace by left padding only (cleaner)
        if v["pattern"] == "border_left_callout_blog2018":
            new_out = re.sub(
                r"border-left\s*:\s*\d+px\s+solid\s+var\(--[\w-]*(?:primary|accent|secondary)[\w-]*\)\s*;?",
                "padding-left: 1.5rem;",
                out,
            )
            if new_out != out:
                out = new_out
                repairs.append(f"border_left_callout: replaced colored border-left by padding-left")

    return out, repairs


__all__ = ["_check_ai_slop_visual_patterns", "_repair_ai_slop_visual_patterns"]
