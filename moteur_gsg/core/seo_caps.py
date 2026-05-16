"""SEO meta caps for the GSG renderer (tech_03 killer rule, 2026-05-16).

Single concern: enforce the SEO contract that Google SERPs truncate
``<title>`` around 60 characters and ``<meta name="description">``
around 160 characters. Past this, the snippet is clipped with an
ellipsis by Google and our multi-judge ``tech_03`` rule fires.

This module is the single source of truth for those caps. It is called
from the renderer (``page_renderer_orchestrator`` + ``section_renderer``)
right before HTML emission, so any path that produces a ``copy_doc.meta``
(LP-Creator canonical copy, Sonnet generator, fallback hero derivation)
is normalised at the same wire.

``cap_text`` trims at the nearest word boundary that fits under
``max_chars - 1`` (1 char reserved for the ellipsis), then appends ``…``.
If no word boundary exists (single long word), it hard-cuts and still
appends the ellipsis. Empty / ``None`` input returns ``""`` without
raising — defensive against partially-populated copy docs.
"""
from __future__ import annotations

# SEO contract — Google SERP truncation thresholds. If these change, the
# multi-judge ``tech_03`` thresholds in
# ``moteur_multi_judge`` must change in lockstep.
TITLE_MAX_CHARS: int = 60
DESCRIPTION_MAX_CHARS: int = 160

_ELLIPSIS: str = "…"  # "…" (1 char)


def cap_text(text: str | None, max_chars: int) -> str:
    """Return ``text`` trimmed to fit within ``max_chars`` (inclusive).

    Empty / ``None`` input returns ``""``. Texts already within budget
    are returned unchanged. When truncation is needed, the cut happens
    at the nearest preceding whitespace if one exists in the budget,
    falling back to a hard cut. The ellipsis (``…``, 1 char) is then
    appended so the total length is always ``<= max_chars``.
    """
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    # Reserve 1 char for the ellipsis.
    budget = max(1, max_chars - 1)
    head = text[:budget]
    # Cut at the last whitespace inside the budget if one exists; this
    # avoids slicing mid-word ("Weglo" → "Weglot"). Strip trailing
    # punctuation glue so we don't end on ", " or " — ".
    boundary = head.rfind(" ")
    if boundary > 0:
        head = head[:boundary]
    head = head.rstrip(" ,;:—-–")
    return f"{head}{_ELLIPSIS}"


def cap_title(text: str | None) -> str:
    """Convenience wrapper: cap a ``<title>`` value to ``TITLE_MAX_CHARS``."""
    return cap_text(text, TITLE_MAX_CHARS)


def cap_description(text: str | None) -> str:
    """Convenience wrapper: cap a ``<meta name="description">`` value to
    ``DESCRIPTION_MAX_CHARS``."""
    return cap_text(text, DESCRIPTION_MAX_CHARS)


__all__ = [
    "TITLE_MAX_CHARS",
    "DESCRIPTION_MAX_CHARS",
    "cap_text",
    "cap_title",
    "cap_description",
]
