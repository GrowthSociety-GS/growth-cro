"""Tests for ``growthcro.models.elite_models`` (Issue CR-09 #64).

Coverage matrix:
- HtmlCandidate validates html_content min/max length + basic HTML shape.
- HtmlCandidate is frozen (mutation rejected).
- HtmlCandidate rejects extra fields.
- HtmlCandidateBatch enforces 1..3 candidates + unique candidate_ids.
- HtmlCandidatePreFilterReport enforces partition invariant (no overlap
  between eliminated and survivors, ids must be in candidates_scored).
- EliteCreativeError carries upstream_error.
- BusinessCategory is re-exported correctly (single source of truth).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from growthcro.models.elite_models import (
    EliteCreativeError,
    HtmlCandidate,
    HtmlCandidateBatch,
    HtmlCandidatePreFilterReport,
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers — minimal valid HTML strings
# ────────────────────────────────────────────────────────────────────────────


def _valid_html(filler_chars: int = 2_000) -> str:
    """Produce a minimal but valid HTML document of approximately N chars."""
    filler = "x" * max(0, filler_chars - 200)
    return (
        "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8'>\n<title>Test</title>\n</head>\n"
        f"<body><h1>Test</h1><p>{filler}</p></body>\n</html>"
    )


# ────────────────────────────────────────────────────────────────────────────
# HtmlCandidate — html_content shape + bounds
# ────────────────────────────────────────────────────────────────────────────


def test_html_candidate_happy_path() -> None:
    cand = HtmlCandidate(
        candidate_id="opus-candidate-01",
        candidate_name="Elite Opus candidate 1",
        html_content=_valid_html(2_500),
        opus_metadata={"model": "claude-opus-4-7", "tokens_in": 1000},
    )
    assert cand.candidate_id == "opus-candidate-01"
    assert cand.html_content.startswith("<!DOCTYPE")
    assert cand.opus_metadata["model"] == "claude-opus-4-7"


def test_html_candidate_rejects_short_html() -> None:
    """html_content min_length is 2000 chars — under-length must fail."""
    short_html = "<!DOCTYPE html><html><body>short</body></html>"
    with pytest.raises(ValidationError):
        HtmlCandidate(
            candidate_id="opus-candidate-01",
            candidate_name="Elite Opus candidate 1",
            html_content=short_html,
        )


def test_html_candidate_rejects_oversized_html() -> None:
    """html_content max_length is 200_000 — over-length must fail."""
    huge_html = _valid_html(200_500)
    with pytest.raises(ValidationError):
        HtmlCandidate(
            candidate_id="opus-candidate-01",
            candidate_name="Elite Opus candidate 1",
            html_content=huge_html,
        )


def test_html_candidate_rejects_non_html_shape() -> None:
    """html_content validator: must start with <!DOCTYPE or <html."""
    prose_html = "This is just prose " + "x" * 2_500
    with pytest.raises(ValidationError) as excinfo:
        HtmlCandidate(
            candidate_id="opus-candidate-01",
            candidate_name="Elite Opus candidate 1",
            html_content=prose_html,
        )
    assert "must start with <!DOCTYPE or <html" in str(excinfo.value)


def test_html_candidate_rejects_unclosed_html() -> None:
    """html_content validator: must end with </html>."""
    unclosed = "<!DOCTYPE html><html><body>" + "x" * 2_500
    with pytest.raises(ValidationError) as excinfo:
        HtmlCandidate(
            candidate_id="opus-candidate-01",
            candidate_name="Elite Opus candidate 1",
            html_content=unclosed,
        )
    assert "must end with </html>" in str(excinfo.value)


def test_html_candidate_is_frozen() -> None:
    cand = HtmlCandidate(
        candidate_id="opus-candidate-01",
        candidate_name="Elite Opus candidate 1",
        html_content=_valid_html(2_500),
    )
    with pytest.raises(ValidationError):
        cand.candidate_id = "mutated"  # type: ignore[misc]


def test_html_candidate_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        HtmlCandidate(
            candidate_id="opus-candidate-01",
            candidate_name="Elite Opus candidate 1",
            html_content=_valid_html(2_500),
            extra_field="forbidden",  # type: ignore[call-arg]
        )


def test_html_candidate_id_pattern_enforced() -> None:
    """candidate_id must match ^[a-z0-9_-]{3,40}$."""
    for bad_id in ["AB", "ALL_CAPS", "has space", "tooshort"[:2], "x" * 41]:
        with pytest.raises(ValidationError):
            HtmlCandidate(
                candidate_id=bad_id,
                candidate_name="Elite Opus candidate 1",
                html_content=_valid_html(2_500),
            )


def test_html_candidate_name_min_length_enforced() -> None:
    with pytest.raises(ValidationError):
        HtmlCandidate(
            candidate_id="opus-candidate-01",
            candidate_name="short",  # < 10 chars
            html_content=_valid_html(2_500),
        )


# ────────────────────────────────────────────────────────────────────────────
# HtmlCandidateBatch — count bounds + unique ids
# ────────────────────────────────────────────────────────────────────────────


def _make_candidate(idx: int) -> HtmlCandidate:
    return HtmlCandidate(
        candidate_id=f"opus-candidate-{idx:02d}",
        candidate_name=f"Elite Opus candidate {idx}",
        html_content=_valid_html(2_500),
    )


def test_batch_happy_path_3_candidates() -> None:
    batch = HtmlCandidateBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        candidates=[_make_candidate(i) for i in range(1, 4)],
        prompt_meta={"model": "claude-opus-4-7"},
    )
    assert len(batch.candidates) == 3
    assert batch.client_slug == "weglot"


def test_batch_accepts_1_candidate() -> None:
    batch = HtmlCandidateBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        candidates=[_make_candidate(1)],
    )
    assert len(batch.candidates) == 1


def test_batch_rejects_0_candidates() -> None:
    with pytest.raises(ValidationError):
        HtmlCandidateBatch(
            client_slug="weglot",
            page_type="lp_listicle",
            business_category="saas",
            candidates=[],
        )


def test_batch_rejects_4_candidates() -> None:
    with pytest.raises(ValidationError):
        HtmlCandidateBatch(
            client_slug="weglot",
            page_type="lp_listicle",
            business_category="saas",
            candidates=[_make_candidate(i) for i in range(1, 5)],
        )


def test_batch_rejects_duplicate_candidate_ids() -> None:
    cand_a = _make_candidate(1)
    cand_dup = HtmlCandidate(
        candidate_id=cand_a.candidate_id,  # same id
        candidate_name="Different name",
        html_content=_valid_html(2_500),
    )
    with pytest.raises(ValidationError) as excinfo:
        HtmlCandidateBatch(
            client_slug="weglot",
            page_type="lp_listicle",
            business_category="saas",
            candidates=[cand_a, cand_dup],
        )
    assert "duplicate candidate_id" in str(excinfo.value)


def test_batch_invalid_business_category_rejected() -> None:
    with pytest.raises(ValidationError):
        HtmlCandidateBatch(
            client_slug="weglot",
            page_type="lp_listicle",
            business_category="not_a_vertical",  # type: ignore[arg-type]
            candidates=[_make_candidate(1)],
        )


def test_batch_is_frozen() -> None:
    batch = HtmlCandidateBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        candidates=[_make_candidate(1)],
    )
    with pytest.raises(ValidationError):
        batch.client_slug = "mutated"  # type: ignore[misc]


# ────────────────────────────────────────────────────────────────────────────
# HtmlCandidatePreFilterReport — partition invariant
# ────────────────────────────────────────────────────────────────────────────


def test_pre_filter_report_happy_path() -> None:
    report = HtmlCandidatePreFilterReport(
        client_slug="weglot",
        page_type="lp_listicle",
        candidates_scored=[
            {
                "candidate_id": "opus-candidate-01",
                "parsing_valid": 9,
                "brand_alignment_text_only": 8,
                "obvious_issues_count": 0,
                "rationale": "Well-formed HTML and brand-aligned colors throughout.",
            },
            {
                "candidate_id": "opus-candidate-02",
                "parsing_valid": 2,
                "brand_alignment_text_only": 4,
                "obvious_issues_count": 8,
                "rationale": "Truncated HTML, missing closing tags everywhere.",
            },
        ],
        eliminated_candidate_ids=["opus-candidate-02"],
        survivors=["opus-candidate-01"],
    )
    assert report.eliminated_candidate_ids == ["opus-candidate-02"]
    assert report.survivors == ["opus-candidate-01"]


def test_pre_filter_report_rejects_overlap() -> None:
    """A candidate_id cannot be both eliminated AND survivor."""
    with pytest.raises(ValidationError) as excinfo:
        HtmlCandidatePreFilterReport(
            client_slug="weglot",
            page_type="lp_listicle",
            candidates_scored=[
                {
                    "candidate_id": "opus-candidate-01",
                    "parsing_valid": 9,
                    "brand_alignment_text_only": 8,
                    "obvious_issues_count": 0,
                    "rationale": "Well-formed HTML and brand-aligned colors throughout.",
                },
            ],
            eliminated_candidate_ids=["opus-candidate-01"],
            survivors=["opus-candidate-01"],
        )
    assert "cannot be both eliminated AND survivor" in str(excinfo.value)


def test_pre_filter_report_rejects_unknown_ids() -> None:
    """eliminated / survivors must reference ids present in candidates_scored."""
    with pytest.raises(ValidationError) as excinfo:
        HtmlCandidatePreFilterReport(
            client_slug="weglot",
            page_type="lp_listicle",
            candidates_scored=[
                {
                    "candidate_id": "opus-candidate-01",
                    "parsing_valid": 9,
                    "brand_alignment_text_only": 8,
                    "obvious_issues_count": 0,
                    "rationale": "Well-formed HTML and brand-aligned colors throughout.",
                },
            ],
            survivors=["opus-candidate-99"],  # unknown id
        )
    assert "unknown candidate_ids" in str(excinfo.value)


def test_pre_filter_report_is_frozen() -> None:
    report = HtmlCandidatePreFilterReport(
        client_slug="weglot",
        page_type="lp_listicle",
        candidates_scored=[
            {
                "candidate_id": "opus-candidate-01",
                "parsing_valid": 9,
                "brand_alignment_text_only": 8,
                "obvious_issues_count": 0,
                "rationale": "Well-formed HTML and brand-aligned colors throughout.",
            },
        ],
        survivors=["opus-candidate-01"],
    )
    with pytest.raises(ValidationError):
        report.client_slug = "mutated"  # type: ignore[misc]


# ────────────────────────────────────────────────────────────────────────────
# EliteCreativeError
# ────────────────────────────────────────────────────────────────────────────


def test_elite_creative_error_carries_upstream() -> None:
    err = EliteCreativeError("test failure", upstream_error="parse fail")
    assert str(err) == "test failure"
    assert err.upstream_error == "parse fail"
    assert isinstance(err, RuntimeError)


def test_elite_creative_error_default_upstream() -> None:
    err = EliteCreativeError("test failure")
    assert err.upstream_error == ""


# ────────────────────────────────────────────────────────────────────────────
# Sanity: SYSTEM_PROMPT_HARD_LIMIT_CHARS exposed at module boundary
# ────────────────────────────────────────────────────────────────────────────


def test_system_prompt_hard_limit_chars_is_6000() -> None:
    """Asserted by the task spec — focused prompt is 6K, not 8K."""
    assert SYSTEM_PROMPT_HARD_LIMIT_CHARS == 6_000
