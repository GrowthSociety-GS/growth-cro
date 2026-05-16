"""Tests for the GSG renderer ``data-evidence-id`` injection (Issue #52).

Coverage matrix:

* **Helper-level** (``moteur_gsg.core.evidence_id_injector``):
  - Deterministic id stability across calls (same inputs → same id).
  - Brief → :class:`ClaimIndex` build for numbers / testimonials / logos.
  - Lookups: matched + unmatched paths.
  - Number wrapping: matched token → ``<span class="number"
    data-evidence-id="…">``; unmatched → bare text; year skip.
  - ``build_brief_evidence_items`` source_type assignment
    (``api_external`` when ``source_url`` present, ``rule_deterministic``
    otherwise) + idempotent ledger merge.

* **Renderer-level** (``moteur_gsg.core.page_renderer_orchestrator``):
  - Listicle render with brief.sourced_numbers + testimonials + logos
    produces ``data-evidence-id`` on testimonial card, logo `<li>`, and
    wraps reason side_note numbers with ``span.number``.
  - End-to-end: feed rendered HTML into ``validate_claims_sources`` with
    the merged ledger → ``gate_passed=True`` for matched claims;
    unmatched claims remain ``claims_missing_source`` (V26.A fail-loud
    invariant intact).
  - Empty brief / no claim index → no ``data-evidence-id`` injection
    anywhere (no crash, gate still flags every free-text claim).
"""
from __future__ import annotations

from typing import Any

import pytest

from moteur_gsg.core.claims_source_gate import validate_claims_sources
from moteur_gsg.core.design_tokens import build_design_tokens
from moteur_gsg.core.evidence_id_injector import (
    ClaimIndex,
    augment_evidence_ledger_with_brief,
    build_brief_evidence_items,
    build_claim_index,
    find_id_for_logo,
    find_id_for_number,
    find_id_for_testimonial,
    make_evidence_id,
    wrap_numbers_with_evidence,
)
from moteur_gsg.core.page_renderer_orchestrator import render_controlled_page
from moteur_gsg.core.planner import GSGPagePlan


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


SOURCED_NUMBER_111K = {
    "number": "111 368",
    "source": "Weglot homepage fr — footer counter",
    "context": "Brands using Weglot in production today",
    "source_url": "https://www.weglot.com/fr",
}
SOURCED_NUMBER_RATING = {
    "number": "4.9/5",
    "source": "Trustpilot — Weglot company page",
    "context": "Average rating from verified buyers",
    "source_url": "https://www.trustpilot.com/review/weglot.com",
}
SOURCED_NUMBER_NO_URL = {
    "number": "5 minutes",
    "source": "Internal benchmark",
    "context": "Median setup time",
    # NB: no source_url → source_type should fall back to rule_deterministic
}

TESTIMONIAL_POLAAR = {
    "name": "Sophie von Kirchmann",
    "position": "E-Store Manager",
    "company": "Polaar",
    "quote": "Le gain de temps avec la traduction instantanée de Weglot est indiscutable.",
    "source_url": "https://www.weglot.com/customers/polaar",
    "authorized": True,
}

LOGO_AMAZON = "Amazon"
LOGO_MICROSOFT = "Microsoft"


@pytest.fixture
def brief_full() -> dict[str, Any]:
    return {
        "sourced_numbers": [
            SOURCED_NUMBER_111K,
            SOURCED_NUMBER_RATING,
            SOURCED_NUMBER_NO_URL,
        ],
        "testimonials": [TESTIMONIAL_POLAAR],
        "client_logos_tier1": [LOGO_AMAZON, LOGO_MICROSOFT],
    }


@pytest.fixture
def brief_empty() -> dict[str, Any]:
    return {
        "sourced_numbers": [],
        "testimonials": [],
        "client_logos_tier1": [],
    }


def _minimal_plan(brief: dict[str, Any]) -> GSGPagePlan:
    """Build a no-frills listicle plan that exercises every claim path."""
    tokens = build_design_tokens(client="weglot", brand_dna={})
    return GSGPagePlan(
        version="test",
        client="weglot",
        page_type="lp_listicle",
        target_language="fr",
        layout_name="listicle_v27",
        brief=brief,
        sections=[],
        design_tokens=tokens,
        pattern_pack={},
        doctrine_pack={},
        constraints={
            "primary_cta_label": "Tester gratuitement",
            "primary_cta_href": "https://weglot.com/start",
            "visual_assets": {},
        },
    )


def _minimal_copy_doc() -> dict[str, Any]:
    return {
        "meta": {"title": "Test", "description": "Test page"},
        "byline": {"author_name": "Test Author", "author_role": "CRO", "date_label": "Mai 2026"},
        "hero": {
            "eyebrow": "Eyebrow",
            "h1": "Hero with 111 368 brands inline",
            "dek": "A dek line with 4.9/5 rating and 5 minutes setup.",
            "primary_cta_label": "Start",
            "microcopy": "No card required",
            "logos_line": "Amazon · Microsoft",
        },
        "intro": ["Intro paragraph with 111 368 marques mentioned."],
        "reasons": [
            {
                "heading": "Reason one with the 4.9/5 rating",
                "paragraphs": ["Body paragraph touching 5 minutes setup."],
                "side_note": "111 368 marques en production aujourd'hui.",
            }
        ],
        "comparison": {},
        "testimonials": {
            "heading": "What customers say",
            "items": [
                {
                    "name": TESTIMONIAL_POLAAR["name"],
                    "position": TESTIMONIAL_POLAAR["position"],
                    "company": TESTIMONIAL_POLAAR["company"],
                    "quote": TESTIMONIAL_POLAAR["quote"],
                    "source_url": TESTIMONIAL_POLAAR["source_url"],
                    "stat_highlight": "+400% trafic",
                }
            ],
        },
        "faq": {},
        "final_cta": {"heading": "Ready?", "body": "Setup in 5 minutes."},
        "footer": {"brand_line": "Weglot"},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helper-level — deterministic IDs
# ─────────────────────────────────────────────────────────────────────────────


def test_make_evidence_id_is_deterministic() -> None:
    a = make_evidence_id("weglot", "lp_listicle", "number", "111 368")
    b = make_evidence_id("weglot", "lp_listicle", "number", "111 368")
    assert a == b
    assert a.startswith("ev_brief_")
    assert len(a) == len("ev_brief_") + 12  # 12 hex chars


def test_make_evidence_id_changes_with_inputs() -> None:
    a = make_evidence_id("weglot", "lp_listicle", "number", "111 368")
    b = make_evidence_id("weglot", "lp_listicle", "number", "111 369")
    c = make_evidence_id("weglot", "home", "number", "111 368")
    d = make_evidence_id("weglot", "lp_listicle", "testimonial", "111 368")
    assert len({a, b, c, d}) == 4


def test_make_evidence_id_normalisation_collapses_whitespace() -> None:
    a = make_evidence_id("weglot", "lp_listicle", "number", "111 368")
    b = make_evidence_id("weglot", "lp_listicle", "number", " 111 368 ")
    assert a == b


# ─────────────────────────────────────────────────────────────────────────────
# Helper-level — index build + lookups
# ─────────────────────────────────────────────────────────────────────────────


def test_build_claim_index_counts(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    assert isinstance(idx, ClaimIndex)
    assert len(idx.numbers) == 3
    assert len(idx.testimonials) == 1
    assert len(idx.logos) == 2


def test_build_claim_index_on_none_brief() -> None:
    idx = build_claim_index(None, "weglot", "lp_listicle")
    assert idx.numbers == []
    assert idx.testimonials == []
    assert idx.logos == []


def test_find_id_for_number_substring_match(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    found = find_id_for_number("111 368", idx)
    assert found is not None
    assert found == make_evidence_id("weglot", "lp_listicle", "number", "111 368")
    # Substring containment in both directions
    assert find_id_for_number("111 368 brands worldwide", idx) == found


def test_find_id_for_number_miss(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    assert find_id_for_number("99 999", idx) is None
    assert find_id_for_number("", idx) is None


def test_find_id_for_testimonial(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    found = find_id_for_testimonial(TESTIMONIAL_POLAAR["quote"], idx)
    assert found is not None
    assert find_id_for_testimonial("totally different quote text here", idx) is None


def test_find_id_for_logo(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    assert find_id_for_logo("Amazon", idx) is not None
    assert find_id_for_logo("amazon", idx) is not None  # case-insensitive
    assert find_id_for_logo("Unknown Brand", idx) is None


# ─────────────────────────────────────────────────────────────────────────────
# Helper-level — wrap_numbers_with_evidence
# ─────────────────────────────────────────────────────────────────────────────


def test_wrap_numbers_matched_token(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    out = wrap_numbers_with_evidence("We power 111 368 brands today.", idx)
    assert '<span class="number" data-evidence-id="ev_brief_' in out
    assert "111 368" in out


def test_wrap_numbers_unmatched_token_stays_bare(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    out = wrap_numbers_with_evidence("We have 99 999 unmatched widgets.", idx)
    assert "<span" not in out
    assert "99 999" in out


def test_wrap_numbers_year_is_skipped(brief_full: dict[str, Any]) -> None:
    idx = build_claim_index(brief_full, "weglot", "lp_listicle")
    out = wrap_numbers_with_evidence("Founded in 2015 and still growing.", idx)
    # 2015 should not be wrapped even if it superficially matches the
    # round-number pattern — years are explicitly excluded.
    assert "<span" not in out


def test_wrap_numbers_empty_index_passthrough() -> None:
    idx = build_claim_index({}, "weglot", "lp_listicle")
    out = wrap_numbers_with_evidence("Plenty of 100% claims here.", idx)
    assert out == "Plenty of 100% claims here."


def test_wrap_numbers_handles_none_and_empty() -> None:
    idx = build_claim_index({}, "weglot", "lp_listicle")
    assert wrap_numbers_with_evidence("", idx) == ""


# ─────────────────────────────────────────────────────────────────────────────
# Helper-level — ledger items + merge
# ─────────────────────────────────────────────────────────────────────────────


def test_build_brief_evidence_items_source_type(brief_full: dict[str, Any]) -> None:
    items = build_brief_evidence_items(brief_full, "weglot", "lp_listicle")
    # 3 numbers + 1 testimonial + 2 logos
    assert len(items) == 6
    by_text = {it["text_observed"]: it for it in items}
    assert by_text["111 368"]["source_type"] == "api_external"
    assert by_text["4.9/5"]["source_type"] == "api_external"
    assert by_text["5 minutes"]["source_type"] == "rule_deterministic"
    assert by_text["Amazon"]["source_type"] == "rule_deterministic"


def test_augment_evidence_ledger_idempotent(brief_full: dict[str, Any]) -> None:
    base = {"items": []}
    once = augment_evidence_ledger_with_brief(base, brief_full, "weglot", "lp_listicle")
    twice = augment_evidence_ledger_with_brief(once, brief_full, "weglot", "lp_listicle")
    assert len(once["items"]) == 6
    assert len(twice["items"]) == 6  # no duplicates


def test_augment_evidence_ledger_preserves_existing() -> None:
    base = {
        "items": [
            {
                "evidence_id": "ev_capture_001",
                "source_type": "vision",
                "text_observed": "Existing capture",
            }
        ]
    }
    out = augment_evidence_ledger_with_brief(
        base, {"sourced_numbers": [SOURCED_NUMBER_111K]}, "weglot", "lp_listicle",
    )
    assert len(out["items"]) == 2
    ids = {it["evidence_id"] for it in out["items"]}
    assert "ev_capture_001" in ids


# ─────────────────────────────────────────────────────────────────────────────
# Renderer-level — HTML produced by render_controlled_page
# ─────────────────────────────────────────────────────────────────────────────


def test_renderer_injects_data_evidence_id_on_testimonial_card(brief_full: dict[str, Any]) -> None:
    plan = _minimal_plan(brief_full)
    html = render_controlled_page(plan=plan, copy_doc=_minimal_copy_doc())
    # The testimonial card carries `data-testimonial="1"` (so the gate
    # detects it regardless of `<article>` tag) plus the brief-derived
    # evidence id.
    assert 'data-testimonial="1"' in html
    assert 'data-evidence-id="ev_brief_' in html


def test_renderer_injects_data_logo_on_hero_logos(brief_full: dict[str, Any]) -> None:
    plan = _minimal_plan(brief_full)
    html = render_controlled_page(plan=plan, copy_doc=_minimal_copy_doc())
    # Logo <li> items carry data-logo and (when matched) data-evidence-id.
    assert 'data-logo="1"' in html
    # At least one of the two logos (Amazon, Microsoft) resolved to an id.
    amazon_id = make_evidence_id("weglot", "lp_listicle", "logo", "Amazon")
    microsoft_id = make_evidence_id("weglot", "lp_listicle", "logo", "Microsoft")
    assert amazon_id in html or microsoft_id in html


def test_renderer_wraps_numbers_in_reason_side_note(brief_full: dict[str, Any]) -> None:
    plan = _minimal_plan(brief_full)
    html = render_controlled_page(plan=plan, copy_doc=_minimal_copy_doc())
    # The side_note "111 368 marques en production" must be wrapped with
    # the span.number marker carrying the brief evidence id.
    assert '<span class="number" data-evidence-id="ev_brief_' in html
    assert "111 368" in html


def test_renderer_with_empty_brief_emits_no_evidence_id(brief_empty: dict[str, Any]) -> None:
    plan = _minimal_plan(brief_empty)
    html = render_controlled_page(plan=plan, copy_doc=_minimal_copy_doc())
    # No brief data → no evidence id. data-testimonial / data-logo are
    # still injected (structural, not evidence) so the gate still
    # recognises the elements and reports them as missing source.
    assert "data-evidence-id" not in html


def test_renderer_does_not_crash_on_missing_brief() -> None:
    plan = _minimal_plan({})
    html = render_controlled_page(plan=plan, copy_doc=_minimal_copy_doc())
    assert "<!DOCTYPE html>" in html


# ─────────────────────────────────────────────────────────────────────────────
# Renderer ⇄ ClaimsSourceGate end-to-end
# ─────────────────────────────────────────────────────────────────────────────


def test_end_to_end_renderer_then_gate_passes_on_matched_claims(
    brief_full: dict[str, Any],
) -> None:
    """Render with a full brief, merge brief items into ledger, feed both
    into the gate. Matched DOM-anchored claims (testimonial, logo,
    wrapped number) should land in ``claims_with_valid_source``. Any free
    text leftover may still register as missing — V26.A fail-loud is
    intact, this test only asserts the matched claims pass."""
    plan = _minimal_plan(brief_full)
    html = render_controlled_page(plan=plan, copy_doc=_minimal_copy_doc())
    ledger = augment_evidence_ledger_with_brief(
        {"items": []}, brief_full, "weglot", "lp_listicle",
    )
    report = validate_claims_sources(html, ledger)
    # The renderer must produce at least one valid claim now (vs zero
    # before this issue's fix).
    assert report.claims_with_valid_source >= 1


def test_end_to_end_unmatched_claims_remain_missing(brief_full: dict[str, Any]) -> None:
    """A free-text "78%" not present in the brief must still be flagged
    as missing — the fix must NOT silently make every claim valid."""
    plan = _minimal_plan(brief_full)
    copy_doc = _minimal_copy_doc()
    copy_doc["intro"].append("This intro has an unmatched 78% claim.")
    html = render_controlled_page(plan=plan, copy_doc=copy_doc)
    ledger = augment_evidence_ledger_with_brief(
        {"items": []}, brief_full, "weglot", "lp_listicle",
    )
    report = validate_claims_sources(html, ledger)
    excerpts = [c.text_excerpt for c in report.claims_missing_source]
    assert any("78%" in t for t in excerpts), (
        f"Free-text 78% should appear in claims_missing_source; got {excerpts!r}"
    )
