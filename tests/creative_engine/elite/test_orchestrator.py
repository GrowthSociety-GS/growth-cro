"""Tests for ``moteur_gsg.creative_engine.elite.orchestrator`` (Issue CR-09 #64).

Coverage matrix:
- Happy path: mocked Opus returns valid HTML 3 times → HtmlCandidateBatch
  with 3 candidates + telemetry.
- Retry path: Opus returns prose → Sonnet retry returns valid HTML →
  candidate succeeds with retry_used=True in telemetry.
- Failure path: Opus + Sonnet both return prose for ALL N candidates →
  EliteCreativeError raised.
- Partial failure: 1 of 3 candidates fails extraction → batch still
  returned with 2 candidates + extraction_failures=1 in prompt_meta.
- n_candidates argument validation: 0 / 4 / 5 → ValueError.
- references argument validation: >1 reference → ValueError.
- System prompt fits under the 6K hard cap with rich brand DNA + forbidden
  patterns.

All Anthropic calls mocked via ``unittest.mock`` — no real LLM calls.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from growthcro.models.elite_models import (
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
    EliteCreativeError,
    HtmlCandidateBatch,
)
from moteur_gsg.creative_engine.elite.orchestrator import (
    OPUS_MODEL,
    SONNET_RETRY_MODEL,
    TEMPERATURE,
    build_system_prompt,
    generate_html_candidates,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers — synthetic Opus responses
# ────────────────────────────────────────────────────────────────────────────


def _valid_html(filler_chars: int = 2_500) -> str:
    filler = "x" * max(0, filler_chars - 200)
    return (
        "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8'>\n<title>Test page</title>\n</head>\n"
        f"<body><h1>Hero</h1><p>{filler}</p></body>\n</html>"
    )


def _make_response(text: str, *, input_tokens: int = 2000, output_tokens: int = 8000) -> SimpleNamespace:
    """Mimic the shape of the Anthropic SDK response object."""
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


# ────────────────────────────────────────────────────────────────────────────
# build_system_prompt — anti-mega-prompt invariant under load
# ────────────────────────────────────────────────────────────────────────────


def test_build_system_prompt_empty_context_under_cap() -> None:
    prompt = build_system_prompt("saas", {}, [])
    assert len(prompt) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS


def test_build_system_prompt_rich_context_under_cap() -> None:
    rich_brand = {
        "version": "v29.E1.1",
        "tone_summary": "confident-warm-direct-editorial",
        "visual_tokens": {
            "colors": {
                "primary": {"hex": "#e9dcf0"},
                "secondary": {"hex": "#0a0a0a"},
                "accent": {"hex": "#ff6b58"},
            },
            "typography": {
                "heading": {"family": "Editorial New"},
                "body": {"family": "Inter"},
            },
        },
        "voice_keywords": ["confident", "warm", "direct", "editorial", "premium", "human"],
    }
    forbidden = [
        "no neon colors",
        "no gradient mesh AI slop",
        "no pop-up urgency timer",
        "no stock photo handshake",
        "no checkmark icon list",
    ]
    prompt = build_system_prompt("luxury", rich_brand, forbidden)
    assert len(prompt) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS
    assert "luxury" in prompt
    assert "Brand DNA" in prompt or "brand" in prompt.lower()


def test_build_system_prompt_includes_5_sections() -> None:
    prompt = build_system_prompt("saas", {}, [])
    for marker in (
        "# SECTION 1 - ROLE",
        "# SECTION 2 - CREATIVE BAR",
        "# SECTION 3 - BRAND DNA",
        "# SECTION 4 - TOOLBOX",
        "# SECTION 5 - HARD CONSTRAINTS",
    ):
        assert marker in prompt, f"missing prompt section marker: {marker}"


def test_build_system_prompt_unknown_vertical_raises() -> None:
    with pytest.raises(KeyError):
        build_system_prompt("not_a_vertical", {}, [])  # type: ignore[arg-type]


# ────────────────────────────────────────────────────────────────────────────
# generate_html_candidates — argument validation
# ────────────────────────────────────────────────────────────────────────────


def test_generate_rejects_0_candidates() -> None:
    with pytest.raises(ValueError, match="n_candidates"):
        generate_html_candidates(
            brief={}, brand_dna={}, page_type="lp_listicle",
            business_category="saas", client_slug="weglot",
            n_candidates=0,
        )


def test_generate_rejects_4_candidates() -> None:
    with pytest.raises(ValueError, match="n_candidates"):
        generate_html_candidates(
            brief={}, brand_dna={}, page_type="lp_listicle",
            business_category="saas", client_slug="weglot",
            n_candidates=4,
        )


def test_generate_rejects_5_candidates() -> None:
    with pytest.raises(ValueError, match="n_candidates"):
        generate_html_candidates(
            brief={}, brand_dna={}, page_type="lp_listicle",
            business_category="saas", client_slug="weglot",
            n_candidates=5,
        )


def test_generate_rejects_multiple_references() -> None:
    with pytest.raises(ValueError, match="anti-patchwork"):
        generate_html_candidates(
            brief={}, brand_dna={}, page_type="lp_listicle",
            business_category="saas", client_slug="weglot",
            n_candidates=1,
            references=["ref_a", "ref_b"],  # > 1 not allowed
        )


def test_generate_accepts_one_reference() -> None:
    """One reference is OK even if file doesn't exist — orchestrator just warns."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())
    batch = generate_html_candidates(
        brief={"objective": "test"}, brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, references=["nonexistent_ref"],
        client=mock_client,
    )
    assert len(batch.candidates) == 1
    assert batch.prompt_meta["reference_used"] == "nonexistent_ref"


# ────────────────────────────────────────────────────────────────────────────
# Happy path — 3 candidates, all valid first try
# ────────────────────────────────────────────────────────────────────────────


def test_generate_happy_path_3_candidates() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())

    batch = generate_html_candidates(
        brief={"objective": "test obj", "audience": "test aud", "angle": "test angle"},
        brand_dna={},
        page_type="lp_listicle",
        business_category="saas",
        client_slug="weglot",
        n_candidates=3,
        client=mock_client,
    )

    assert isinstance(batch, HtmlCandidateBatch)
    assert len(batch.candidates) == 3
    assert batch.client_slug == "weglot"
    assert batch.page_type == "lp_listicle"
    assert batch.business_category == "saas"

    # 3 Opus calls (no retry).
    assert mock_client.messages.create.call_count == 3

    # Telemetry
    pm = batch.prompt_meta
    assert pm["model"] == OPUS_MODEL
    assert pm["temperature"] == TEMPERATURE
    assert pm["n_candidates_requested"] == 3
    assert pm["n_candidates_succeeded"] == 3
    assert pm["extraction_failures"] == 0
    assert pm["system_prompt_chars"] <= SYSTEM_PROMPT_HARD_LIMIT_CHARS

    # Per-candidate telemetry
    assert len(pm["per_candidate_telemetry"]) == 3
    for t in pm["per_candidate_telemetry"]:
        assert t["model"] == OPUS_MODEL
        assert t["temperature_used"] == TEMPERATURE
        assert t["retry_used"] is False


def test_generate_happy_path_1_candidate() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())

    batch = generate_html_candidates(
        brief={}, brand_dna={}, page_type="lp_listicle",
        business_category="ecommerce", client_slug="weglot",
        n_candidates=1, client=mock_client,
    )
    assert len(batch.candidates) == 1
    assert mock_client.messages.create.call_count == 1


def test_generate_with_custom_opus_model() -> None:
    """opus_model override propagates to the SDK call (CR-09 stop condition #18)."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())

    batch = generate_html_candidates(
        brief={}, brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, opus_model="claude-opus-4-1",
        client=mock_client,
    )
    assert batch.prompt_meta["model"] == "claude-opus-4-1"
    # Verify the SDK call was made with the override.
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-1"


# ────────────────────────────────────────────────────────────────────────────
# Retry path — Opus prose → Sonnet correction → valid HTML
# ────────────────────────────────────────────────────────────────────────────


def test_generate_retry_on_invalid_first_output() -> None:
    mock_client = MagicMock()
    # First call returns prose (no HTML), retry returns valid.
    mock_client.messages.create.side_effect = [
        _make_response("Here is your landing page idea: " + "x" * 200),
        _make_response(_valid_html()),
    ]

    batch = generate_html_candidates(
        brief={}, brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, client=mock_client,
    )
    assert len(batch.candidates) == 1
    # 1 Opus call + 1 Sonnet retry = 2 total.
    assert mock_client.messages.create.call_count == 2
    # Verify retry model used.
    second_call = mock_client.messages.create.call_args_list[1]
    assert second_call.kwargs["model"] == SONNET_RETRY_MODEL

    t = batch.prompt_meta["per_candidate_telemetry"][0]
    assert t["retry_used"] is True
    assert t["retry_model"] == SONNET_RETRY_MODEL


def test_generate_extracts_html_when_wrapped_in_fences() -> None:
    """Opus might wrap HTML in markdown fences despite instructions."""
    fenced = "```html\n" + _valid_html() + "\n```"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(fenced)

    batch = generate_html_candidates(
        brief={}, brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, client=mock_client,
    )
    assert len(batch.candidates) == 1
    assert batch.candidates[0].html_content.startswith("<!DOCTYPE")


# ────────────────────────────────────────────────────────────────────────────
# Failure path — Opus + Sonnet both fail for all candidates
# ────────────────────────────────────────────────────────────────────────────


def test_generate_raises_when_all_candidates_fail() -> None:
    mock_client = MagicMock()
    # Every call returns garbage (no HTML extractable).
    mock_client.messages.create.return_value = _make_response("just prose, no HTML")

    with pytest.raises(EliteCreativeError) as excinfo:
        generate_html_candidates(
            brief={}, brand_dna={}, page_type="lp_listicle",
            business_category="saas", client_slug="weglot",
            n_candidates=2, client=mock_client,
        )
    err = excinfo.value
    assert "All 2 candidates failed" in str(err)
    assert err.upstream_error == "extraction_failed_all_candidates"
    # 2 Opus + 2 Sonnet retries = 4 calls.
    assert mock_client.messages.create.call_count == 4


# ────────────────────────────────────────────────────────────────────────────
# Partial failure — 1 of 3 candidates fails, batch still returned
# ────────────────────────────────────────────────────────────────────────────


def test_generate_partial_failure_returns_batch_with_survivors() -> None:
    """If 1 of 3 candidates fails extraction (Opus + Sonnet), the other 2 succeed."""
    mock_client = MagicMock()
    # Candidate 1: success (Opus valid).
    # Candidate 2: Opus fails, Sonnet retry succeeds.
    # Candidate 3: Opus fails, Sonnet retry fails too.
    mock_client.messages.create.side_effect = [
        _make_response(_valid_html()),                # cand 1, Opus OK
        _make_response("prose 2"),                    # cand 2, Opus fail
        _make_response(_valid_html()),                # cand 2, Sonnet retry OK
        _make_response("prose 3 opus"),               # cand 3, Opus fail
        _make_response("prose 3 sonnet"),             # cand 3, Sonnet retry fail
    ]

    batch = generate_html_candidates(
        brief={}, brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=3, client=mock_client,
    )
    assert len(batch.candidates) == 2
    assert batch.prompt_meta["n_candidates_requested"] == 3
    assert batch.prompt_meta["n_candidates_succeeded"] == 2
    assert batch.prompt_meta["extraction_failures"] == 1
    assert mock_client.messages.create.call_count == 5


# ────────────────────────────────────────────────────────────────────────────
# Brief forbidden_visual_patterns propagation
# ────────────────────────────────────────────────────────────────────────────


def test_generate_propagates_forbidden_patterns_to_prompt() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())

    generate_html_candidates(
        brief={
            "objective": "test",
            "forbidden_visual_patterns": ["no neon", "no gradient mesh"],
        },
        brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, client=mock_client,
    )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system_text = call_kwargs["system"][0]["text"]
    assert "no neon" in system_text
    assert "no gradient mesh" in system_text


def test_generate_handles_non_list_forbidden_patterns_gracefully() -> None:
    """forbidden_visual_patterns not a list → treat as None (no crash)."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())

    batch = generate_html_candidates(
        brief={"forbidden_visual_patterns": "should be list not str"},
        brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, client=mock_client,
    )
    assert len(batch.candidates) == 1


# ────────────────────────────────────────────────────────────────────────────
# No tool_use — Elite is direct HTML, not JSON
# ────────────────────────────────────────────────────────────────────────────


def test_generate_does_not_use_tool_use() -> None:
    """Codex correction: Elite output is raw HTML — no tool_use forced JSON."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_html())

    generate_html_candidates(
        brief={}, brand_dna={}, page_type="lp_listicle",
        business_category="saas", client_slug="weglot",
        n_candidates=1, client=mock_client,
    )
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "tools" not in call_kwargs, "Elite must NOT use tool_use (raw HTML output)"
    assert "tool_choice" not in call_kwargs
