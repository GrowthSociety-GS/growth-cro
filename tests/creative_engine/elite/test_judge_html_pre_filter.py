"""Tests for ``moteur_gsg.creative_engine.judge.judge_html_pre_filter`` (CR-09 #64).

Coverage matrix:
- Happy path: 3 candidates → Sonnet scores 3 → report has scored=3 +
  partition into survivors / eliminated based on deterministic thresholds.
- Elimination: parsing_valid<5 → eliminated.
- Elimination: brand_alignment<3 → eliminated.
- Elimination: obvious_issues>3 → eliminated.
- Safety net: if all candidates fall below thresholds, the best one is
  rescued so Phase 2 has at least 1 survivor.
- Retry path: first Sonnet response invalid → retry succeeds.
- Failure: both first + retry invalid → CreativeEngineError.

All Anthropic calls mocked — no real LLM.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from growthcro.models.elite_models import (
    HtmlCandidate,
    HtmlCandidateBatch,
    HtmlCandidatePreFilterReport,
)
from moteur_gsg.creative_engine.elite.judge_html import judge_html_pre_filter
from moteur_gsg.creative_engine.orchestrator import CreativeEngineError


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────


def _valid_html(filler_chars: int = 2_500) -> str:
    filler = "x" * max(0, filler_chars - 200)
    return (
        "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8'>\n<title>Test page</title>\n</head>\n"
        f"<body><h1>Hero</h1><p>{filler}</p></body>\n</html>"
    )


def _make_batch(n: int = 3) -> HtmlCandidateBatch:
    candidates = [
        HtmlCandidate(
            candidate_id=f"opus-candidate-{i:02d}",
            candidate_name=f"Elite Opus candidate {i}",
            html_content=_valid_html(2_500 + i * 50),
            opus_metadata={"model": "claude-opus-4-7"},
        )
        for i in range(1, n + 1)
    ]
    return HtmlCandidateBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        candidates=candidates,
    )


def _make_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(
            input_tokens=2000,
            output_tokens=500,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


def _scores_json(*entries: dict) -> str:
    return json.dumps({"scores": list(entries)})


def _score(
    candidate_id: str,
    parsing: int = 8,
    brand: int = 7,
    issues: int = 0,
    rationale: str = "Looks well-formed and brand-aligned with no obvious issues.",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "parsing_valid": parsing,
        "brand_alignment_text_only": brand,
        "obvious_issues_count": issues,
        "rationale": rationale,
    }


# ────────────────────────────────────────────────────────────────────────────
# Happy path
# ────────────────────────────────────────────────────────────────────────────


def test_pre_filter_all_pass_thresholds_all_survive() -> None:
    """All 3 candidates score well → all 3 survive, 0 eliminated."""
    batch = _make_batch(3)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(
        _scores_json(
            _score("opus-candidate-01"),
            _score("opus-candidate-02"),
            _score("opus-candidate-03"),
        )
    )

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert isinstance(report, HtmlCandidatePreFilterReport)
    assert len(report.candidates_scored) == 3
    assert set(report.survivors) == {f"opus-candidate-{i:02d}" for i in range(1, 4)}
    assert report.eliminated_candidate_ids == []


def test_pre_filter_eliminates_low_parsing() -> None:
    """parsing_valid<5 → eliminated (threshold violation)."""
    batch = _make_batch(3)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(
        _scores_json(
            _score("opus-candidate-01", parsing=2),  # eliminate
            _score("opus-candidate-02", parsing=9),
            _score("opus-candidate-03", parsing=8),
        )
    )

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert "opus-candidate-01" in report.eliminated_candidate_ids
    assert "opus-candidate-02" in report.survivors
    assert "opus-candidate-03" in report.survivors


def test_pre_filter_eliminates_low_brand_alignment() -> None:
    """brand_alignment_text_only<3 → eliminated."""
    batch = _make_batch(2)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(
        _scores_json(
            _score("opus-candidate-01", brand=2),  # eliminate
            _score("opus-candidate-02", brand=8),
        )
    )

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert "opus-candidate-01" in report.eliminated_candidate_ids
    assert "opus-candidate-02" in report.survivors


def test_pre_filter_eliminates_too_many_issues() -> None:
    """obvious_issues_count>3 → eliminated."""
    batch = _make_batch(2)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(
        _scores_json(
            _score("opus-candidate-01", issues=8),  # eliminate
            _score("opus-candidate-02", issues=0),
        )
    )

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert "opus-candidate-01" in report.eliminated_candidate_ids
    assert "opus-candidate-02" in report.survivors


# ────────────────────────────────────────────────────────────────────────────
# Safety net — if all eliminated, keep the best
# ────────────────────────────────────────────────────────────────────────────


def test_pre_filter_rescues_best_if_all_eliminated() -> None:
    """If all 3 fall below thresholds, keep the best-scored as survivor."""
    batch = _make_batch(3)
    mock_client = MagicMock()
    # All have very low parsing OR very high issues → all flagged for elimination.
    mock_client.messages.create.return_value = _make_response(
        _scores_json(
            _score("opus-candidate-01", parsing=3, brand=2, issues=8),
            _score("opus-candidate-02", parsing=4, brand=5, issues=2),  # least-bad
            _score("opus-candidate-03", parsing=2, brand=1, issues=9),
        )
    )

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert len(report.survivors) >= 1, "Phase 1 must always leave ≥1 survivor for Phase 2"
    # The best one (candidate-02 has highest parsing+brand=9, lowest issues=2) survives.
    assert "opus-candidate-02" in report.survivors


# ────────────────────────────────────────────────────────────────────────────
# Retry path
# ────────────────────────────────────────────────────────────────────────────


def test_pre_filter_retries_on_invalid_first_response() -> None:
    batch = _make_batch(2)
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response("not JSON, just prose"),
        _make_response(
            _scores_json(
                _score("opus-candidate-01"),
                _score("opus-candidate-02"),
            )
        ),
    ]

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert mock_client.messages.create.call_count == 2
    assert report.pre_filter_meta["retry_used"] is True
    assert report.pre_filter_meta["retry_reason"]


def test_pre_filter_retries_on_missing_candidate_id() -> None:
    """First response only covers 1 of 2 candidates → retry."""
    batch = _make_batch(2)
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response(_scores_json(_score("opus-candidate-01"))),  # missing #2
        _make_response(
            _scores_json(
                _score("opus-candidate-01"),
                _score("opus-candidate-02"),
            )
        ),
    ]

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert mock_client.messages.create.call_count == 2
    assert report.pre_filter_meta["retry_used"] is True


# ────────────────────────────────────────────────────────────────────────────
# Failure
# ────────────────────────────────────────────────────────────────────────────


def test_pre_filter_raises_on_double_failure() -> None:
    """Both first + retry invalid → CreativeEngineError."""
    batch = _make_batch(2)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response("just prose, no JSON")

    with pytest.raises(CreativeEngineError) as excinfo:
        judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    assert "pre-filter" in str(excinfo.value).lower()
    assert mock_client.messages.create.call_count == 2


def test_pre_filter_raises_on_short_rationale() -> None:
    """rationale<30 chars → validation fails → retry, retry also fails → error."""
    batch = _make_batch(1)
    mock_client = MagicMock()
    bad_resp = _make_response(
        _scores_json(
            _score("opus-candidate-01", rationale="too short"),
        )
    )
    mock_client.messages.create.return_value = bad_resp
    with pytest.raises(CreativeEngineError):
        judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)


# ────────────────────────────────────────────────────────────────────────────
# Telemetry
# ────────────────────────────────────────────────────────────────────────────


def test_pre_filter_telemetry_includes_thresholds() -> None:
    batch = _make_batch(1)
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(
        _scores_json(_score("opus-candidate-01"))
    )

    report = judge_html_pre_filter(batch, brief={}, brand_dna={}, client=mock_client)
    thresholds = report.pre_filter_meta["elimination_thresholds"]
    assert thresholds["parsing_below"] == 5
    assert thresholds["brand_alignment_below"] == 3
    assert thresholds["obvious_issues_above"] == 3
    assert report.pre_filter_meta["model"]
    assert report.pre_filter_meta["wall_seconds"] >= 0
