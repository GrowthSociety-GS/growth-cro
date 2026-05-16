"""Tests for ``moteur_gsg.core.claims_source_gate`` (Issue #51).

Coverage matrix:
- Happy path: testimonial with valid ``data-evidence-id`` + strict source_type
  → ``gate_passed=True``.
- Missing source: testimonial without ``data-evidence-id`` → gate fails with
  ``claims_missing_source`` populated.
- Invalid source: ``data-evidence-id`` resolves but ``source_type="llm_classifier"``
  → gate fails with ``claims_invalid_source`` populated.
- Free-text claim: bare ``78%`` outside any DOM marker → gate fails (no source
  possible without ``data-evidence-id``).
- Neutral HTML: a paragraph with no claim patterns → ``gate_passed=True``
  (vacuously, no claim to validate).
- Exception: ``raise_if_failed()`` on a failed report raises ``ClaimsSourceError``;
  on a passing report it is a no-op.
- Ledger shape robustness: accepts both on-disk JSON shape (``{"items": [...]}``)
  and ``EvidenceLedger`` objects exposing ``items()``.
- Evidence ID not in ledger: claim points to unknown id → invalid_source.
"""
from __future__ import annotations

import pytest

from moteur_gsg.core.claims_source_gate import (
    Claim,
    ClaimsSourceError,
    ClaimsSourceReport,
    is_strict_source_type,
    validate_claims_sources,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _ledger_with(*entries: dict) -> dict:
    """Build an on-disk-shaped ledger ({"items": [...]})."""
    return {
        "version": "v26.A.1.0",
        "client": "test",
        "page": "home",
        "viewport": "desktop",
        "n_items": len(entries),
        "items": list(entries),
    }


def _evidence(evidence_id: str, source_type: str = "vision",
              text: str = "Demo") -> dict:
    return {
        "evidence_id": evidence_id,
        "client": "test",
        "page": "home",
        "viewport": "desktop",
        "source_type": source_type,
        "text_observed": text,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Happy path
# ─────────────────────────────────────────────────────────────────────────────


def test_valid_testimonial_with_strict_source_passes() -> None:
    html = """
    <main>
      <p>Welcome to the site.</p>
      <blockquote class="testimonial" data-evidence-id="ev-001">
        This product saved our team weeks of work.
      </blockquote>
    </main>
    """
    ledger = _ledger_with(_evidence("ev-001", source_type="vision"))
    report = validate_claims_sources(html, ledger)

    assert isinstance(report, ClaimsSourceReport)
    assert report.gate_passed is True
    assert report.claims_total == 1
    assert report.claims_with_valid_source == 1
    assert report.claims_missing_source == []
    assert report.claims_invalid_source == []
    assert report.claims_found[0].is_valid is True
    assert report.claims_found[0].evidence_id == "ev-001"


# ─────────────────────────────────────────────────────────────────────────────
# Missing source: no data-evidence-id at all
# ─────────────────────────────────────────────────────────────────────────────


def test_testimonial_without_evidence_id_fails() -> None:
    html = """
    <main>
      <blockquote class="testimonial">
        Another great review without any source.
      </blockquote>
    </main>
    """
    report = validate_claims_sources(html, _ledger_with())

    assert report.gate_passed is False
    assert report.claims_total == 1
    assert report.claims_with_valid_source == 0
    assert len(report.claims_missing_source) == 1
    missing = report.claims_missing_source[0]
    assert missing.evidence_id is None
    assert missing.is_valid is False
    assert "blockquote" in missing.selector


# ─────────────────────────────────────────────────────────────────────────────
# Invalid source: data-evidence-id resolves but source_type=llm_classifier
# ─────────────────────────────────────────────────────────────────────────────


def test_evidence_id_with_llm_classifier_source_fails() -> None:
    html = """
    <div class="testimonial-card" data-evidence-id="ev-002">
      Five stars from a happy customer.
    </div>
    """
    ledger = _ledger_with(_evidence("ev-002", source_type="llm_classifier"))
    report = validate_claims_sources(html, ledger)

    assert report.gate_passed is False
    assert len(report.claims_invalid_source) == 1
    invalid = report.claims_invalid_source[0]
    assert invalid.evidence_id == "ev-002"
    assert invalid.is_valid is False


# ─────────────────────────────────────────────────────────────────────────────
# Free-text claim: 78% without DOM marker → missing source
# ─────────────────────────────────────────────────────────────────────────────


def test_free_text_percentage_without_source_fails() -> None:
    html = """
    <main>
      <p>Our customers report a 78% lift in conversion.</p>
    </main>
    """
    report = validate_claims_sources(html, _ledger_with())

    assert report.gate_passed is False
    excerpts = [c.text_excerpt for c in report.claims_missing_source]
    assert any("78%" in e for e in excerpts)
    # Selector for text-detected claims uses the synthetic "text:" prefix.
    selectors = [c.selector for c in report.claims_missing_source]
    assert any(s.startswith("text:") for s in selectors)


# ─────────────────────────────────────────────────────────────────────────────
# Neutral HTML: no claim patterns → vacuously passes
# ─────────────────────────────────────────────────────────────────────────────


def test_neutral_html_with_no_claims_passes() -> None:
    html = """
    <main>
      <h1>Welcome</h1>
      <p>Browse our catalog and discover the experience.</p>
    </main>
    """
    report = validate_claims_sources(html, _ledger_with())

    assert report.gate_passed is True
    assert report.claims_total == 0
    assert report.claims_missing_source == []
    assert report.claims_invalid_source == []


# ─────────────────────────────────────────────────────────────────────────────
# ClaimsSourceError lifecycle
# ─────────────────────────────────────────────────────────────────────────────


def test_raise_if_failed_raises_on_failure() -> None:
    html = '<blockquote class="testimonial">Source-less quote.</blockquote>'
    report = validate_claims_sources(html, _ledger_with())

    with pytest.raises(ClaimsSourceError) as exc:
        report.raise_if_failed()
    assert exc.value.report is report
    assert "ClaimsSourceGate refused ship" in str(exc.value)


def test_raise_if_failed_noop_on_pass() -> None:
    html = "<p>Just prose, nothing to validate.</p>"
    report = validate_claims_sources(html, _ledger_with())
    # Must not raise.
    report.raise_if_failed()


# ─────────────────────────────────────────────────────────────────────────────
# Ledger-shape robustness
# ─────────────────────────────────────────────────────────────────────────────


def test_ledger_as_evidence_ledger_object_works() -> None:
    """Accepts an `EvidenceLedger`-style object exposing `items() -> list[dict]`."""

    class _FakeLedger:
        def __init__(self, entries: list[dict]) -> None:
            self._entries = entries

        def items(self) -> list[dict]:  # noqa: D401 — mimics real interface
            return list(self._entries)

    html = '<span class="number" data-evidence-id="ev-005">42</span>'
    fake = _FakeLedger([_evidence("ev-005", source_type="dom")])
    report = validate_claims_sources(html, fake)
    assert report.gate_passed is True
    assert report.claims_with_valid_source == 1


def test_ledger_id_not_found_marks_invalid() -> None:
    html = '<span class="number" data-evidence-id="ev-missing">99</span>'
    report = validate_claims_sources(html, _ledger_with(_evidence("ev-other")))
    assert report.gate_passed is False
    assert len(report.claims_invalid_source) == 1
    assert report.claims_invalid_source[0].evidence_id == "ev-missing"


# ─────────────────────────────────────────────────────────────────────────────
# is_strict_source_type unit checks
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("source_type,expected", [
    ("vision", True),
    ("dom", True),
    ("api_external", True),
    ("rule_deterministic", True),
    ("vision+dom", True),
    ("hybrid_vision_dom", True),
    ("llm_classifier", False),
    ("", False),
    (None, False),
    ("unknown_made_up", False),
])
def test_is_strict_source_type(source_type: str | None, expected: bool) -> None:
    assert is_strict_source_type(source_type) is expected


# ─────────────────────────────────────────────────────────────────────────────
# Mixed scenario: one valid, one missing
# ─────────────────────────────────────────────────────────────────────────────


def test_mixed_claims_reports_individual_status() -> None:
    html = """
    <main>
      <li class="proof-strip" data-evidence-id="ev-good">10,000 users</li>
      <li class="proof">No source attached</li>
      <img class="trust-logo" data-evidence-id="ev-good-2" alt="Acme" />
    </main>
    """
    ledger = _ledger_with(
        _evidence("ev-good", source_type="dom"),
        _evidence("ev-good-2", source_type="vision+dom"),
    )
    report = validate_claims_sources(html, ledger)
    assert report.claims_total == 3
    assert report.claims_with_valid_source == 2
    assert len(report.claims_missing_source) == 1
    assert report.gate_passed is False  # one missing source blocks
