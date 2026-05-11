"""CSS package for the controlled GSG renderer.

Three sub-modules hold the renderer's stylesheet split by concern (issue #8
sub-split — keeps each module ≤ 800 LOC instead of a 1,130 LOC monolith):

  * base.py        — reset, body, typography, hero scaffold, brand-shot,
                     locale stack, pricing/form/product/article panels.
  * components.py  — argument lines, atlas/system-map, reasons, final CTA,
                     component sections + visuals, keyframes.
  * responsive.py  — prefers-reduced-motion query, decorative inner specs,
                     footer, (max-width: 720px) mobile query.

Public API: ``render_renderer_css(tokens)`` — concatenates the three
constants in canonical order, prefixed by the design-tokens CSS, returning
a single byte-identical block to what `controlled_renderer._css(tokens)`
historically produced. Order is **NOT** swappable (later rules override
earlier ones — base + components + responsive).
"""
from __future__ import annotations

from typing import Any

from ..design_tokens import render_design_tokens_css
from .base import BASE_CSS
from .components import COMPONENTS_CSS
from .responsive import RESPONSIVE_CSS


def render_renderer_css(tokens: dict[str, Any]) -> str:
    """Return the full controlled-renderer stylesheet for ``tokens``.

    Byte-equivalent to the legacy ``controlled_renderer._css(tokens)``
    output — split is verbatim concatenation, no rule reordered.
    """
    return render_design_tokens_css(tokens) + BASE_CSS + COMPONENTS_CSS + RESPONSIVE_CSS


__all__ = ["render_renderer_css", "BASE_CSS", "COMPONENTS_CSS", "RESPONSIVE_CSS"]
