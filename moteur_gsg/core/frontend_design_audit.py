"""Frontend-design runtime audit — V27.2-H Sprint 16 (T16-2).

Python heuristic implementation of the ``frontend-design`` Anthropic
skill. Runs at runtime against the rendered HTML to check visual
hierarchy + design tokens consistency.

Same scoring convention as the other runtime audits (0-10). Reports
``gaps`` so the orchestrator can route low-scoring runs back through a
polish pass (Sprint 17+).
"""
from __future__ import annotations

import re
from typing import Any


MIN_SCORE = 7


def _single_h1_check(html: str) -> tuple[bool, str]:
    """Exactly 1 ``<h1>`` per page (SEO + accessibility + hierarchy)."""
    matches = re.findall(r"<h1\b[^>]*>", html, re.IGNORECASE)
    if len(matches) == 0:
        return False, "No <h1> found — page lacks a primary heading"
    if len(matches) > 1:
        return False, f"{len(matches)} <h1> tags — exactly 1 expected"
    return True, ""


def _semantic_landmarks_check(html: str) -> tuple[bool, str]:
    """At minimum: <header>, <main>, <footer>."""
    needed = ["<header", "<main", "<footer"]
    missing = [t for t in needed if not re.search(t, html, re.IGNORECASE)]
    if missing:
        return False, f"Missing semantic landmark(s) : {', '.join(missing)}"
    return True, ""


def _design_tokens_used_check(html: str) -> tuple[bool, str]:
    """CSS should use --gsg-* custom properties — not raw hex everywhere."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style> block found"
    css = css_block.group(1)
    custom_props = len(re.findall(r"--gsg-[\w-]+", css))
    raw_hex = len(re.findall(r"#[0-9a-fA-F]{3,8}\b", css))
    # We want custom_props >> raw_hex (allow some raw hex for transparent overlays).
    if custom_props < 12:
        return False, f"Only {custom_props} --gsg-* custom properties — design tokens not fully wired"
    if raw_hex > custom_props // 2 + 20:
        return False, f"Too many raw hex colors ({raw_hex} vs {custom_props} tokens) — switch to tokens"
    return True, ""


def _responsive_breakpoints_check(html: str) -> tuple[bool, str]:
    """Mobile-first : ``@media (max-width: ...)`` OR ``min-width`` rules required."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style> block to scan for media queries"
    css = css_block.group(1)
    media_count = len(re.findall(r"@media\s*\(\s*(?:max|min)-width", css))
    if media_count < 1:
        return False, "No responsive media queries — page is desktop-only"
    return True, ""


def _viewport_meta_check(html: str) -> tuple[bool, str]:
    """``<meta name="viewport" content="width=device-width...">`` required."""
    if not re.search(r'<meta\s+name="viewport"', html, re.IGNORECASE):
        return False, "No <meta name='viewport'> — mobile rendering broken"
    if "width=device-width" not in html.lower():
        return False, "viewport meta lacks width=device-width"
    return True, ""


def _focus_visible_check(html: str) -> tuple[bool, str]:
    """``:focus`` or ``:focus-visible`` rules present (a11y)."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style> to check focus styles"
    css = css_block.group(1)
    if not re.search(r":focus(-visible)?\b", css):
        return False, "No :focus / :focus-visible rules — keyboard navigation invisible"
    return True, ""


def _contrast_indication_check(html: str) -> tuple[bool, str]:
    """Heuristic : at least one ``.cta-button*`` rule sets both an
    explicit ``background`` and a ``color``. Scans ALL matching rules
    so it doesn't get fooled by ``.mid-cta .cta-button { margin-top: 0 }``
    which is a descendant override (V9 bug)."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style>"
    css = css_block.group(1)
    # Find all rules whose selector ends with `.cta-button` or `.cta-button-*`
    # (not nested descendants).
    blocks = re.findall(r"(^|[\n}])(\s*\.cta-button[\w-]*\s*\{[^}]+\})", css)
    if not blocks:
        return False, ".cta-button rule not found"
    for _prefix, block in blocks:
        if "background" in block and re.search(r"\bcolor\s*:", block):
            return True, ""
    return False, ".cta-button missing explicit background OR color (contrast risk)"


def _spacing_scale_check(html: str) -> tuple[bool, str]:
    """Heuristic : at least 4 distinct padding values in tokens (8/16/24/32+)."""
    css_block = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not css_block:
        return False, "No <style>"
    css = css_block.group(1)
    paddings = set(re.findall(r"padding\s*:\s*(\d+)px", css))
    if len(paddings) < 4:
        return False, f"Only {len(paddings)} distinct padding values — spacing scale too flat"
    return True, ""


_CHECKS = [
    ("single_h1", _single_h1_check, "critical"),
    ("semantic_landmarks", _semantic_landmarks_check, "critical"),
    ("design_tokens_used", _design_tokens_used_check, "warning"),
    ("responsive_breakpoints", _responsive_breakpoints_check, "critical"),
    ("viewport_meta", _viewport_meta_check, "critical"),
    ("focus_visible", _focus_visible_check, "warning"),
    ("contrast_indication", _contrast_indication_check, "warning"),
    ("spacing_scale", _spacing_scale_check, "info"),
]


def run_frontend_design_audit(html: str) -> dict[str, Any]:
    """Run the frontend-design heuristic audit on the rendered HTML."""
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
        "version": "frontend-design-audit-v1.0",
        "score": score,
        "passed": score >= MIN_SCORE,
        "gaps": gaps,
        "checks_run": len(_CHECKS),
    }


__all__ = ["run_frontend_design_audit", "MIN_SCORE"]
