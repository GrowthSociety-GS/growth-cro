"""Tests for SEO meta caps (tech_03 killer rule quickfix 2026-05-16).

Doctrine: Google SERP truncates ``<title>`` around 60 chars and
``<meta name="description">`` around 160 chars. Anything longer is
rendered as ``... (tronqué)`` in the snippet and triggers the multi-judge
``tech_03`` killer rule (SEO on-page foundations).

The cap is enforced mechanically at the renderer level (single source of
truth) by ``moteur_gsg.core.seo_caps``. Trim happens at the nearest word
boundary under the limit; an ellipsis (``…``, 1 char) is appended when
the text was actually truncated, so the on-page string ends cleanly.

Coverage:
- unit cap helper: short text unchanged, long text trimmed at word
  boundary, single long word hard-cut, empty input safe, exact-fit
  unchanged
- module-level constants match the SEO contract (60 / 160)
- renderer integration: when the parsed ``copy_doc.meta.title`` /
  ``description`` arrive overlong (e.g. from the Sonnet generator or a
  re-validated LP-Creator copy), the emitted ``<title>`` and
  ``<meta name="description">`` are within their caps.
"""
from __future__ import annotations

import pytest

from moteur_gsg.core.seo_caps import (
    DESCRIPTION_MAX_CHARS,
    TITLE_MAX_CHARS,
    cap_text,
)


# ---------------------------------------------------------------------------
# Unit: cap_text behavior
# ---------------------------------------------------------------------------


def test_cap_text_short_input_unchanged() -> None:
    assert cap_text("Short title", 60) == "Short title"


def test_cap_text_exact_fit_unchanged() -> None:
    text = "A" * 60
    assert cap_text(text, 60) == text


def test_cap_text_long_input_trimmed_with_ellipsis_at_word_boundary() -> None:
    text = (
        "Pourquoi 111 368 marques utilisent Weglot — 10 leviers que ni "
        "Google Translate ni DeepL ne couvrent vraiment"
    )
    out = cap_text(text, 60)
    # Total length (including ellipsis) MUST be <= cap
    assert len(out) <= 60
    # Truncation marker present
    assert out.endswith("…")
    # Cut at a word boundary: the char before "…" is a letter/digit, not a
    # half-word like "Weglo" (this is a regression assertion against naive
    # ``text[:cap]`` slicing).
    assert not out[-2].isspace()
    # Prefix must remain a real prefix of the input (no rewriting)
    assert text.startswith(out[:-1].rstrip())


def test_cap_text_single_long_word_hard_cut() -> None:
    # No word boundary in the budget → fall back to hard cut + ellipsis,
    # never longer than the cap.
    text = "A" * 200
    out = cap_text(text, 60)
    assert len(out) <= 60
    assert out.endswith("…")


def test_cap_text_empty_input_safe() -> None:
    assert cap_text("", 60) == ""
    assert cap_text(None, 60) == ""  # type: ignore[arg-type]


def test_cap_text_meta_description_long_input() -> None:
    text = (
        "Polaar revenue US 5% → 17% en 3 mois grâce à Weglot. Découvrez "
        "les 10 leviers concrets qui ont permis à 111 368 marques de "
        "tripler leur trafic international sans refonte technique."
    )
    out = cap_text(text, 160)
    assert len(out) <= 160
    assert out.endswith("…")


# ---------------------------------------------------------------------------
# Module-level SEO contract
# ---------------------------------------------------------------------------


def test_seo_contract_constants() -> None:
    # If these change, multi-judge tech_03 thresholds must change too.
    assert TITLE_MAX_CHARS == 60
    assert DESCRIPTION_MAX_CHARS == 160


# ---------------------------------------------------------------------------
# Integration: rendered HTML respects the caps
# ---------------------------------------------------------------------------


@pytest.fixture
def overlong_copy_doc() -> dict:
    """A copy_doc.meta with values that violated tech_03 on Weglot smoke."""
    return {
        "meta": {
            "title": (
                "Pourquoi 111 368 marques utilisent Weglot — 10 leviers "
                "que ni Google Translate ni DeepL ne couvrent vraiment"
            ),
            "description": (
                "Polaar revenue US 5% → 17% en 3 mois grâce à Weglot. "
                "Découvrez les 10 leviers concrets qui ont permis à "
                "111 368 marques de tripler leur trafic international "
                "sans refonte technique."
            ),
        },
        "byline": {"author_name": "GrowthCRO", "author_role": "QA", "date_label": "2026-05-16"},
        "hero": {
            "eyebrow": "Test",
            "h1": "Test H1",
            "dek": "Test dek copy short enough.",
        },
        "intro": ["Intro paragraph."],
        "reasons": [],
        "final_cta": {"heading": "CTA", "body": "Click", "button_label": "Go"},
        "footer": {"brand_line": "GrowthCRO"},
    }


def _minimal_plan():
    """A minimal GSGPagePlan-compatible stub for the orchestrator.

    Mirrors ``tests/gsg/test_renderer_evidence_id.py::_minimal_plan`` —
    keeps this test independent and avoids importing test internals.
    """
    from moteur_gsg.core.design_tokens import build_design_tokens
    from moteur_gsg.core.planner import GSGPagePlan

    tokens = build_design_tokens(client="weglot", brand_dna={})
    return GSGPagePlan(
        version="test",
        client="weglot",
        page_type="lp_listicle",
        target_language="fr",
        layout_name="listicle_v27",
        brief={},
        sections=[],
        design_tokens=tokens,
        pattern_pack={},
        doctrine_pack={},
        constraints={
            "primary_cta_label": "Demarrer",
            "primary_cta_href": "#",
            "visual_assets": {},
        },
    )


def test_renderer_caps_title_in_emitted_html(overlong_copy_doc: dict) -> None:
    from moteur_gsg.core.page_renderer_orchestrator import render_controlled_page

    plan = _minimal_plan()
    html = render_controlled_page(plan=plan, copy_doc=overlong_copy_doc)
    # Extract the <title>...</title> content
    import re

    m = re.search(r"<title>(.*?)</title>", html, re.S)
    assert m, "no <title> tag emitted"
    title = m.group(1)
    # The original was ~100+ chars; the rendered must respect the cap.
    assert len(title) <= TITLE_MAX_CHARS, f"title still {len(title)} chars: {title!r}"


def test_renderer_caps_meta_description_in_emitted_html(overlong_copy_doc: dict) -> None:
    from moteur_gsg.core.page_renderer_orchestrator import render_controlled_page

    plan = _minimal_plan()
    html = render_controlled_page(plan=plan, copy_doc=overlong_copy_doc)
    import re

    m = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
    assert m, "no <meta name=\"description\"> tag emitted"
    desc = m.group(1)
    assert len(desc) <= DESCRIPTION_MAX_CHARS, (
        f"meta description still {len(desc)} chars: {desc!r}"
    )
