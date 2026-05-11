"""Emil Kowalski motion layer for the controlled GSG renderer (V27.2-G+).

Skill ref: ``Emil Kowalski Design Skill`` (combo "GSG generation" — see
``.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`` §2). The skill
documents *patterns* (delicate transitions, spring-ish easing, staggered
reveals, reduced-motion respect). This module materialises those patterns
as **deterministic CSS** appended to the renderer stylesheet by
``page_renderer_orchestrator``. No API call. No JS dependency.

Why a dedicated module
======================

The legacy ``css/responsive.py`` already ships a base ``@keyframes
gsgReveal`` + ``@keyframes gsgSlowDrift`` + a ``prefers-reduced-motion:
no-preference`` block. That's the foundation. This module **extends**
that foundation with the Emil Kowalski polish layer:

* hero entrance with a fold-aware translateY (no jank, no overshoot)
* staggered list reveals (proof strip, reasons, pricing tiers) using
  per-child ``animation-delay`` so the eye reads in rhythm rather than
  in a blast
* smooth-scroll for in-page anchors (CTAs that link to ``#pricing`` etc)
* CTA micro-interactions (hover lift, focus ring, active translateY)
* link underline draw on hover
* respect ``prefers-reduced-motion: reduce`` HARD (everything off — no
  exception, that's the Emil rule and the WCAG 2.1 SC 2.3.3 line)

Public API
==========

* :func:`render_animations_css` — returns the full motion CSS block.
  Concatenated AFTER the renderer stylesheet so its rules win on cascade
  ties.

* :func:`animations_status` — generation-free meta for canonical checks.

Design constraints
==================

* No `<script>` injection. CSS only.
* No new `<link>` external. Stays self-contained.
* Idempotent: rendering twice produces byte-identical output.
* ≤ 400 LOC (file target per task #19 spec).
"""
from __future__ import annotations

from typing import Any


__all__ = [
    "ANIMATIONS_VERSION",
    "STAGGER_DELAYS_MS",
    "render_animations_css",
    "animations_status",
]


ANIMATIONS_VERSION = "gsg-animations-emil-kowalski-v27.2-g"

# Stagger delays for the first N siblings of any staggered list
# (proof strip cells, reasons articles, pricing tiers, component-section
# cards). Increment is 80ms — empirically the Emil sweet spot between
# "instant" and "ceremonial". The list caps at 12 children; subsequent
# siblings share the last delay so very long lists don't drag.
STAGGER_DELAYS_MS: tuple[int, ...] = (
    0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800, 880,
)


# ──────────────────────────────────────────────────────────────────────
# CSS building blocks
# ──────────────────────────────────────────────────────────────────────

def _stagger_block(selector: str, kind: str = "reveal") -> str:
    """Generate per-nth-child animation-delay declarations for a parent.

    ``kind`` selects the animation name. ``selector`` targets the parent
    container (e.g. ``.proof-strip``, ``.intro``, ``main``).
    """
    anim = "gsgEmilReveal" if kind == "reveal" else "gsgEmilFadeUp"
    rules = []
    for i, delay in enumerate(STAGGER_DELAYS_MS, start=1):
        rules.append(
            f"  {selector} > *:nth-child({i}) {{ animation-delay: {delay}ms; }}"
        )
    rules.append(
        f"  {selector} > *:nth-child(n+13) {{ animation-delay: {STAGGER_DELAYS_MS[-1]}ms; }}"
    )
    return "\n".join(rules)


# ──────────────────────────────────────────────────────────────────────
# Animations stylesheet
# ──────────────────────────────────────────────────────────────────────

KEYFRAMES_CSS = """/* Emil Kowalski motion layer — V27.2-G */
@keyframes gsgEmilReveal {
  from { opacity: 0; transform: translate3d(0, 18px, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}
@keyframes gsgEmilFadeUp {
  from { opacity: 0; transform: translate3d(0, 10px, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}
@keyframes gsgEmilCtaPulse {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--gsg-primary) 32%, transparent); }
  60% { box-shadow: 0 0 0 14px color-mix(in srgb, var(--gsg-primary) 0%, transparent); }
  100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--gsg-primary) 0%, transparent); }
}
@keyframes gsgEmilUnderlineDraw {
  from { background-size: 0% 1px; }
  to { background-size: 100% 1px; }
}
"""


# Spring-ish easing variables — defined on :root so any consumer can
# pull --gsg-emil-ease without re-declaring the bezier. Numbers come
# from the Emil Kowalski talk on "fast, soft, deterministic" timing.
TIMING_VARIABLES_CSS = """:root {
  --gsg-emil-ease: cubic-bezier(0.22, 0.61, 0.36, 1);
  --gsg-emil-ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --gsg-emil-duration-fast: 200ms;
  --gsg-emil-duration-base: 360ms;
  --gsg-emil-duration-slow: 640ms;
}
html { scroll-behavior: smooth; }
"""


# Motion shells. Wrapped in prefers-reduced-motion: no-preference so a
# user who set the OS-level "reduce motion" flag (or the
# CSS media query) gets zero motion. We only paint static states then.
MOTION_SHELL_CSS = """@media (prefers-reduced-motion: no-preference) {
  /* Hero copy + visual — fold reveal */
  .hero .hero-copy { animation: gsgEmilReveal var(--gsg-emil-duration-slow) var(--gsg-emil-ease-out) both; }
  .hero .hero-visual { animation: gsgEmilReveal var(--gsg-emil-duration-slow) var(--gsg-emil-ease-out) both 80ms; }
  /* Eyebrow → H1 → dek in rhythm */
  .hero .eyebrow { animation: gsgEmilFadeUp var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both 40ms; }
  .hero h1 { animation: gsgEmilFadeUp var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both 120ms; }
  .hero .dek { animation: gsgEmilFadeUp var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both 200ms; }
  /* Proof strip — staggered children */
  .proof-strip > * { animation: gsgEmilReveal var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both; }
__PROOF_STRIP_STAGGER__
  /* Reasons cards — staggered */
  .reason { animation: gsgEmilReveal var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both; }
__REASONS_STAGGER__
  /* Component sections — staggered */
  .component-section { animation: gsgEmilReveal var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both; }
__COMPONENT_STAGGER__
  /* Pricing tiers — staggered */
  .pricing-board > * { animation: gsgEmilReveal var(--gsg-emil-duration-base) var(--gsg-emil-ease-out) both; }
__PRICING_STAGGER__
}
@media (prefers-reduced-motion: reduce) {
  /* WCAG 2.1 SC 2.3.3 — opt-out is total */
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-delay: 0ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
"""


# Hover + focus micro-interactions on the CTA and inline links. These
# are transitions (state-driven), so they don't loop and are fine even
# under "no-preference" — but we still gate them behind no-preference
# to keep the WCAG opt-out clean.
CTA_INTERACTIONS_CSS = """@media (prefers-reduced-motion: no-preference) {
  .cta-button {
    transition:
      transform var(--gsg-emil-duration-fast) var(--gsg-emil-ease-out),
      box-shadow var(--gsg-emil-duration-fast) var(--gsg-emil-ease-out),
      background-color var(--gsg-emil-duration-fast) var(--gsg-emil-ease-out);
  }
  .cta-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 32px color-mix(in srgb, var(--gsg-primary) 22%, transparent);
  }
  .cta-button:active {
    transform: translateY(0);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--gsg-primary) 18%, transparent);
  }
  .cta-button:focus-visible {
    outline: 2px solid var(--gsg-primary);
    outline-offset: 3px;
    animation: gsgEmilCtaPulse 1.2s var(--gsg-emil-ease-out) 1;
  }
  /* Inline editorial link — underline draws on hover */
  main a:not(.cta-button) {
    background-image: linear-gradient(to right, var(--gsg-primary), var(--gsg-primary));
    background-repeat: no-repeat;
    background-position: 0 100%;
    background-size: 0% 1px;
    text-decoration: none;
    transition: background-size var(--gsg-emil-duration-fast) var(--gsg-emil-ease-out);
  }
  main a:not(.cta-button):hover,
  main a:not(.cta-button):focus-visible {
    background-size: 100% 1px;
  }
  /* Reason hover lift — already partially in responsive.py, we deepen */
  .reason {
    transition:
      transform var(--gsg-emil-duration-base) var(--gsg-emil-ease-out),
      border-color var(--gsg-emil-duration-base) var(--gsg-emil-ease-out);
  }
  .reason:hover {
    transform: translateY(-2px);
  }
}
"""


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def render_animations_css(tokens: dict[str, Any] | None = None) -> str:
    """Return the Emil Kowalski motion-layer stylesheet.

    Parameters
    ----------
    tokens
        Currently unused — reserved for future per-client motion tuning
        (e.g. reduce stagger for very dense pricing tables). Kept in the
        signature so the renderer can wire it without breakage when the
        feature lands.

    Returns
    -------
    str
        A CSS block ready to concatenate after ``render_renderer_css``.
        Idempotent: same input → byte-identical output.
    """
    motion = MOTION_SHELL_CSS
    motion = motion.replace(
        "__PROOF_STRIP_STAGGER__", _stagger_block(".proof-strip"),
    )
    motion = motion.replace(
        "__REASONS_STAGGER__", _stagger_block("main"),
    )
    motion = motion.replace(
        "__COMPONENT_STAGGER__", _stagger_block(".component-section"),
    )
    motion = motion.replace(
        "__PRICING_STAGGER__", _stagger_block(".pricing-board"),
    )
    return (
        f"\n/* === {ANIMATIONS_VERSION} === */\n"
        + TIMING_VARIABLES_CSS
        + "\n"
        + KEYFRAMES_CSS
        + "\n"
        + motion
        + "\n"
        + CTA_INTERACTIONS_CSS
    )


def animations_status() -> dict[str, Any]:
    """Generation-free status for canonical / smoke tests."""
    return {
        "version": ANIMATIONS_VERSION,
        "stagger_max_children": len(STAGGER_DELAYS_MS),
        "stagger_step_ms": STAGGER_DELAYS_MS[1] - STAGGER_DELAYS_MS[0],
        "respects_reduced_motion": True,
        "selectors_targeted": [
            ".hero .hero-copy",
            ".hero .hero-visual",
            ".hero h1",
            ".proof-strip > *",
            ".reason",
            ".component-section",
            ".pricing-board > *",
            ".cta-button",
            "main a:not(.cta-button)",
        ],
        "easing_tokens": [
            "--gsg-emil-ease",
            "--gsg-emil-ease-out",
            "--gsg-emil-duration-fast",
            "--gsg-emil-duration-base",
            "--gsg-emil-duration-slow",
        ],
        "uses_javascript": False,
        "uses_external_assets": False,
    }
