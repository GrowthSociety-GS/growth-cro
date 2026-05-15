"""Emil-design-eng runtime audit — V27.2-H Sprint 16 (T16-4).

Python heuristic implementation of the ``emil-design-eng`` Anthropic
skill — Emil Kowalski-inspired motion design policy. Audits the
rendered HTML/CSS for premium-motion adherence : subtle reveals,
``cubic-bezier`` premium easing, sane durations, and
``prefers-reduced-motion`` respect.
"""
from __future__ import annotations

import re
from typing import Any


MIN_SCORE = 7


def _reduced_motion_respected(html: str) -> tuple[bool, str]:
    """``@media (prefers-reduced-motion: reduce)`` must be present."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style> block"
    if not re.search(r"@media\s*\([^)]*prefers-reduced-motion[^)]*\)", css_block.group(1)):
        return False, "Missing @media (prefers-reduced-motion: reduce) — accessibility regression"
    return True, ""


def _premium_easing_check(html: str) -> tuple[bool, str]:
    """At least one premium ``cubic-bezier(...)`` curve in the CSS.

    Emil Kowalski signature curves : 0.22 1 0.36 1 (premium reveal),
    0.32 0.72 0 1 (smooth), etc. Linear / step / pure ``ease`` are
    discouraged for premium feel.
    """
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style>"
    css = css_block.group(1)
    bezier_count = len(re.findall(r"cubic-bezier\s*\(", css))
    if bezier_count == 0:
        return False, "No cubic-bezier(...) easing — motion feels generic (use 0.22, 1, 0.36, 1)"
    return True, ""


def _no_aggressive_animations(html: str) -> tuple[bool, str]:
    """Reject high-rotation, infinite-spin, ping-pong, or shake animations."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return True, ""
    css = css_block.group(1)
    flagged = []
    # > 180deg rotation in a single keyframe = excessive
    for m in re.finditer(r"rotate\s*\(\s*(\d{3,4})deg", css):
        if int(m.group(1)) > 180:
            flagged.append(f"rotate({m.group(1)}deg)")
    if "animation-iteration-count: infinite" in css.replace(" ", ""):
        flagged.append("infinite animation")
    if "alternate" in css and "animation" in css:
        # alternate is OK for pulsing, but we flag for review
        pass
    if "shake" in css.lower():
        flagged.append("shake keyword")
    if flagged:
        return False, f"Aggressive animation patterns : {', '.join(flagged[:3])}"
    return True, ""


def _sane_durations_check(html: str) -> tuple[bool, str]:
    """Transition / animation durations should be < 1.2s (premium = subtle)."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return True, ""
    css = css_block.group(1)
    # Collect durations expressed in s or ms
    durations_s = re.findall(r"transition[^;]*?(\d+(?:\.\d+)?)s\b", css)
    too_long = [d for d in durations_s if float(d) > 1.2]
    if too_long:
        return False, f"Long transition durations ({too_long[:3]}s) — premium motion = subtle, < 1.2s"
    return True, ""


def _scroll_reveal_intersection_observer(html: str) -> tuple[bool, str]:
    """If the page uses scroll-reveal animations, prefer IntersectionObserver
    over throttled scroll listeners (perf + signal quality)."""
    # Look at the inline JS or attached scripts
    if "scroll" in html.lower() and "intersectionobserver" not in html.lower():
        # Only flag if there's evidence of scroll-driven reveal CSS
        if ".reveal" in html or "data-reveal" in html or "@keyframes reveal" in html:
            return False, "Scroll-reveal pattern detected without IntersectionObserver — use IO for premium perf"
    return True, ""


def _hover_transitions_present(html: str) -> tuple[bool, str]:
    """Premium interactivity : ``:hover`` rules must have transitions
    (not abrupt swaps)."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return True, ""
    css = css_block.group(1)
    hover_rules = re.findall(r":hover\s*\{[^}]+\}", css)
    if not hover_rules:
        return True, ""  # No hover rules at all — neutral
    # Check that hover transitions are paired with a parent transition rule
    if "transition" not in css:
        return False, "Hover rules without any transition property — abrupt UX"
    return True, ""


def _no_legacy_animation_libs(html: str) -> tuple[bool, str]:
    """AOS, WOW.js, animate.css = anti-pattern in premium motion."""
    legacy = ["aos.js", "wow.js", "animate.css", "anime.min.js"]
    html_lower = html.lower()
    found = [lib for lib in legacy if lib in html_lower]
    if found:
        return False, f"Legacy animation library detected : {', '.join(found)}"
    return True, ""


_CHECKS = [
    ("reduced_motion_respected", _reduced_motion_respected, "critical"),
    ("premium_easing", _premium_easing_check, "warning"),
    ("no_aggressive_animations", _no_aggressive_animations, "warning"),
    ("sane_durations", _sane_durations_check, "warning"),
    ("scroll_reveal_intersection_observer", _scroll_reveal_intersection_observer, "info"),
    ("hover_transitions_present", _hover_transitions_present, "info"),
    ("no_legacy_animation_libs", _no_legacy_animation_libs, "warning"),
]


def run_emil_design_eng_audit(html: str) -> dict[str, Any]:
    """Run the emil-design-eng motion policy audit."""
    gaps: list[dict[str, Any]] = []
    deduction = 0.0
    for check_id, check_fn, severity in _CHECKS:
        try:
            passed, description = check_fn(html)
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
        "version": "emil-design-eng-audit-v1.0",
        "score": score,
        "passed": score >= MIN_SCORE,
        "gaps": gaps,
        "checks_run": len(_CHECKS),
    }


__all__ = ["run_emil_design_eng_audit", "MIN_SCORE"]
