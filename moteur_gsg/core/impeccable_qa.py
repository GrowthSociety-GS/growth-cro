"""Impeccable post-render QA layer for the controlled GSG renderer.

Skill ref: ``Impeccable`` / impeccable.style (combo "GSG generation" — see
``.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`` §2). The skill
documents ~200 production-grade anti-patterns for LP HTML/CSS. This
module is the deterministic, offline detection layer — pure HTML/CSS
string parsing, no API call, no JS exec.

Detection categories (mapped to Impeccable taxonomy):
* CRO killers — lorem-ipsum, dummy testimonials, checkmark spam,
  round inflation numbers, unresolved placeholders, empty AI-slop verbs.
* Visual sloppiness — Inter/Roboto/Helvetica default leak, opacity:0
  without an animation, Tailwind class blast.
* Accessibility — missing alt on <img>, missing/multiple <h1>, no lang
  on <html>, button with no accessible name, missing
  prefers-reduced-motion media query.
* Mobile-first regressions — fixed hero width in px, hard-coded
  desktop widths > 1440px.
* Performance — embedded data URIs > 50KB, @import cascades.

Public API:
* :func:`run_impeccable_qa` — HTML in → dict with score (0-100),
  passed (score >= MIN_PASSING_SCORE), severity_breakdown,
  anti_patterns_detected. Score < 70 ⇒ hard fail per task #19 spec.
* :func:`impeccable_status` — generation-free meta for canonical
  validation.

CODE_DOCTRINE compliance: pure stdlib (re, html.parser), deterministic,
mono-concern (HTML in → QA report out, no mutation, no network),
≤ 400 LOC. V26.AF safety: consumed AFTER render_controlled_page and
BEFORE run_multi_judge — does not contribute to system_messages and
cannot expand the 8K persona-prompt hard limit.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any


__all__ = [
    "IMPECCABLE_VERSION",
    "MIN_PASSING_SCORE",
    "ANTI_PATTERNS",
    "run_impeccable_qa",
    "impeccable_status",
]


IMPECCABLE_VERSION = "gsg-impeccable-qa-v27.2-g"
MIN_PASSING_SCORE = 70  # task #19 spec — hard fail below this
SEVERITY_WEIGHTS = {"critical": 12, "warning": 4, "info": 1}
SEVERITY_LEVELS = ("critical", "warning", "info")


# Anti-pattern catalogue: {id, severity, description, pattern, allowed}.
# A hit registers when match_count > allowed, weighted by severity.
ANTI_PATTERNS: tuple[dict[str, Any], ...] = (
    # CRO killers
    {
        "id": "lorem_ipsum",
        "severity": "critical",
        "description": "Lorem ipsum placeholder copy in the HTML",
        "pattern": re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
        "allowed": 0,
    },
    {
        "id": "dummy_testimonial_pattern",
        "severity": "critical",
        "description": "Generic invented testimonial pattern ('Sarah, 32 ans')",
        "pattern": re.compile(
            r"(?:Sarah|John|Jane|Marie|Pierre|Sophie)[ ,]+\d{2}\s*ans", re.IGNORECASE
        ),
        "allowed": 0,
    },
    {
        "id": "checkmark_spam",
        "severity": "warning",
        "description": "Stacked checkmarks (✓✓✓ or ✅✅✅) — AI-slop tell",
        "pattern": re.compile(r"(?:✓\s*){3,}|(?:✅\s*){3,}"),
        "allowed": 0,
    },
    {
        "id": "round_inflation_number",
        "severity": "warning",
        "description": "Round inflation number (+50%, +127%, +200%) — likely invented",
        "pattern": re.compile(r"\+\s*(?:50|100|127|200|300|500)\s*%"),
        "allowed": 2,
    },
    {
        "id": "verbe_vide",
        "severity": "info",
        "description": "Empty French marketing verbs (boostez, optimisez, transformez, découvrez)",
        "pattern": re.compile(
            r"\b(?:boostez|optimisez|transformez|d[ée]couvrez|explorez)\b",
            re.IGNORECASE,
        ),
        "allowed": 3,
    },
    {
        "id": "empty_placeholder_token",
        "severity": "warning",
        "description": "Unresolved templating placeholder ({{ }} or [[ ]])",
        "pattern": re.compile(r"\{\{\s*\w+\s*\}\}|\[\[\s*\w+\s*\]\]"),
        "allowed": 0,
    },
    # Visual sloppiness
    {
        "id": "anthropic_default_font",
        "severity": "warning",
        "description": "Default sans-serif leak (Inter/Roboto/Helvetica/Arial) instead of brand font",
        "pattern": re.compile(
            r"font-family\s*:\s*[\"']?(?:Inter|Roboto|Helvetica|Arial|Open Sans|Lato|Montserrat|Poppins)\b",
            re.IGNORECASE,
        ),
        "allowed": 0,
    },
    {
        "id": "opacity_zero_no_anim",
        "severity": "critical",
        "description": "opacity:0 declared but no animation keyframe references it (invisible content)",
        "pattern": re.compile(r"opacity\s*:\s*0\s*;(?![^{}]*animation)", re.MULTILINE),
        "allowed": 0,
    },
    {
        "id": "tailwind_class_blast",
        "severity": "info",
        "description": "Excessive Tailwind classes on a single element (>10 utility classes)",
        "pattern": re.compile(
            r'class\s*=\s*"(?:[\w:-]+\s+){11,}[\w:-]+"', re.IGNORECASE
        ),
        "allowed": 0,
    },
    # Accessibility
    {
        "id": "img_no_alt",
        "severity": "warning",
        "description": "<img> without alt attribute and no role=presentation",
        "pattern": re.compile(
            r"<img\b(?![^>]*\balt\s*=)(?![^>]*role\s*=\s*[\"']presentation[\"'])[^>]*>",
            re.IGNORECASE,
        ),
        "allowed": 0,
    },
    {
        "id": "html_no_lang",
        "severity": "warning",
        "description": "<html> without lang attribute",
        "pattern": re.compile(r"<html\b(?![^>]*\blang\s*=)[^>]*>", re.IGNORECASE),
        "allowed": 0,
    },
    {
        "id": "button_no_text",
        "severity": "warning",
        "description": "<button> with no text content and no aria-label",
        "pattern": re.compile(
            r"<button\b(?![^>]*\baria-label\s*=)[^>]*>\s*</button>", re.IGNORECASE
        ),
        "allowed": 0,
    },
    # Mobile-first regressions
    {
        "id": "fixed_hero_width_px",
        "severity": "warning",
        "description": "Fixed pixel width on .hero or section (mobile-first violation)",
        "pattern": re.compile(
            r"(?:\.hero|main|section)\s*\{[^}]*\bwidth\s*:\s*\d{4,}px", re.IGNORECASE
        ),
        "allowed": 0,
    },
    {
        "id": "hardcoded_desktop_width",
        "severity": "info",
        "description": "Hard-coded width > 1440px somewhere in CSS",
        "pattern": re.compile(r"\bwidth\s*:\s*(?:1[5-9]|[2-9])\d{3,}px"),
        "allowed": 1,
    },
    # Performance
    {
        "id": "large_data_uri",
        "severity": "warning",
        "description": "Embedded data URI > 50KB (preferred: real asset)",
        "pattern": re.compile(r"data:[^,)\"']{50000,}"),
        "allowed": 0,
    },
    {
        "id": "css_import_cascade",
        "severity": "info",
        "description": "@import in CSS (blocks parallel download)",
        "pattern": re.compile(r"@import\b", re.IGNORECASE),
        "allowed": 1,
    },
)


# Structural checks (require parsing, not regex)
class _StructuralCheck(HTMLParser):
    """Parse-once collector for structural Impeccable signals."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.reduced_motion_seen = False
        self.lang_seen = False
        self.has_doctype = False
        self.style_buffer: list[str] = []
        self._in_style = False

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        if tag_l == "h1":
            self.h1_count += 1
        if tag_l == "html":
            for name, val in attrs:
                if name.lower() == "lang" and val:
                    self.lang_seen = True
        if tag_l == "style":
            self._in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.style_buffer.append(data)
            if "prefers-reduced-motion" in data:
                self.reduced_motion_seen = True


def _structural_hits(html: str) -> list[dict[str, Any]]:
    """Return structural anti-pattern hits (post-parse)."""
    p = _StructuralCheck()
    try:
        p.feed(html)
    except Exception:
        # Malformed HTML — surface as a critical hit
        return [{
            "id": "html_parse_failure",
            "severity": "critical",
            "description": "HTMLParser raised on input",
            "count": 1,
            "excerpt": "",
        }]
    hits: list[dict[str, Any]] = []
    if not p.has_doctype:
        hits.append({
            "id": "missing_doctype",
            "severity": "warning",
            "description": "Missing <!DOCTYPE html> declaration",
            "count": 1,
            "excerpt": html[:80],
        })
    if p.h1_count == 0:
        hits.append({
            "id": "no_h1",
            "severity": "critical",
            "description": "No <h1> in the document",
            "count": 1,
            "excerpt": "",
        })
    elif p.h1_count > 1:
        hits.append({
            "id": "multiple_h1",
            "severity": "warning",
            "description": f"{p.h1_count} <h1> tags (should be exactly one)",
            "count": p.h1_count,
            "excerpt": "",
        })
    if not p.lang_seen:
        hits.append({
            "id": "html_no_lang_struct",
            "severity": "warning",
            "description": "<html> tag without lang attribute (parsed)",
            "count": 1,
            "excerpt": "",
        })
    if not p.reduced_motion_seen and "@keyframes" in html:
        hits.append({
            "id": "animations_no_reduced_motion",
            "severity": "warning",
            "description": "Animations defined but no prefers-reduced-motion block",
            "count": 1,
            "excerpt": "",
        })
    return hits


def _score_from_hits(hits: list[dict[str, Any]]) -> tuple[int, dict[str, int]]:
    """Convert hit list → score (0-100) + severity breakdown."""
    breakdown = {s: 0 for s in SEVERITY_LEVELS}
    deduction = 0
    for hit in hits:
        sev = hit.get("severity") or "info"
        if sev not in breakdown:
            sev = "info"
        breakdown[sev] += 1
        deduction += SEVERITY_WEIGHTS[sev]
    score = max(0, 100 - deduction)
    return score, breakdown


def _excerpt(match: re.Match[str], window: int = 60) -> str:
    """Return a short context window around a regex match (1 line max)."""
    s, e = match.span()
    snippet = match.string[max(0, s - window): min(len(match.string), e + window)]
    return snippet.replace("\n", " ").strip()[:200]


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def run_impeccable_qa(html: str) -> dict[str, Any]:
    """Run the Impeccable QA layer on a rendered HTML page.

    Parameters
    ----------
    html
        Full HTML string of the rendered LP (post ``render_controlled_page``
        and post ``apply_minimal_postprocess``).

    Returns
    -------
    dict
        Keys:
          * ``version`` (str) — module version
          * ``score`` (int, 0-100) — overall Impeccable score
          * ``passed`` (bool) — True iff ``score >= MIN_PASSING_SCORE``
          * ``severity_breakdown`` (dict) — count per severity
          * ``anti_patterns_detected`` (list) — per-hit detail
          * ``checked_count`` (int) — total patterns checked
    """
    if not isinstance(html, str) or not html.strip():
        return {
            "version": IMPECCABLE_VERSION,
            "score": 0,
            "passed": False,
            "severity_breakdown": {"critical": 1, "warning": 0, "info": 0},
            "anti_patterns_detected": [{
                "id": "empty_html",
                "severity": "critical",
                "description": "Empty or non-string HTML passed to impeccable_qa",
                "count": 1,
                "excerpt": "",
            }],
            "checked_count": 0,
        }

    hits: list[dict[str, Any]] = []
    for entry in ANTI_PATTERNS:
        matches = list(entry["pattern"].finditer(html))
        if len(matches) > entry["allowed"]:
            excess = len(matches) - entry["allowed"]
            hits.append({
                "id": entry["id"],
                "severity": entry["severity"],
                "description": entry["description"],
                "count": excess,
                "excerpt": _excerpt(matches[0]) if matches else "",
            })
    hits.extend(_structural_hits(html))

    score, breakdown = _score_from_hits(hits)
    return {
        "version": IMPECCABLE_VERSION,
        "score": score,
        "passed": score >= MIN_PASSING_SCORE,
        "severity_breakdown": breakdown,
        "anti_patterns_detected": hits,
        "checked_count": len(ANTI_PATTERNS) + 5,  # 5 structural checks
    }


def impeccable_status() -> dict[str, Any]:
    """Generation-free status for canonical / smoke validation."""
    return {
        "version": IMPECCABLE_VERSION,
        "min_passing_score": MIN_PASSING_SCORE,
        "anti_patterns_count": len(ANTI_PATTERNS),
        "structural_checks": [
            "missing_doctype",
            "no_h1",
            "multiple_h1",
            "html_no_lang_struct",
            "animations_no_reduced_motion",
        ],
        "severity_levels": list(SEVERITY_LEVELS),
        "severity_weights": dict(SEVERITY_WEIGHTS),
        "deterministic": True,
        "uses_api": False,
        "uses_javascript": False,
    }
