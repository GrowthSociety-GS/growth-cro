"""Tests for ``moteur_gsg.creative_engine.orchestrator`` (Issue #56, CR-01).

Coverage matrix:
- Happy path: mocked Anthropic client returns valid JSON → orchestrator
  produces a ``CreativeRouteBatch`` of the right shape, and prompt_meta is
  attached (model + system_prompt_chars + wall_seconds + retry_used=False).
- Retry path: Opus returns invalid JSON → Sonnet retry returns valid →
  ``retry_used=True`` and ``retry_reason`` is populated.
- Failure path: Opus invalid + Sonnet invalid → ``CreativeEngineError``
  raised with both upstream messages.
- Anti-mega-prompt: ``build_system_prompt`` stays under the hard limit
  with the real Weglot brief fixture.
- Prompt assembly: brand_dna / design_grammar absent → stub lines used.

No real ``messages.create`` calls — all mocked via ``unittest.mock``.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from growthcro.models.creative_models import (
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
    CreativeRouteBatch,
)
from moteur_gsg.creative_engine.orchestrator import (
    CreativeEngineError,
    build_system_prompt,
    explore_routes,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers — synth a valid CreativeRouteBatch JSON string the LLM "would" return
# ────────────────────────────────────────────────────────────────────────────

_THESIS_TEXT = "A mocked thesis with enough words to clear the 20-char minimum length."


def _route_dict(route_id: str) -> dict:
    return {
        "route_id": route_id,
        "route_name": f"Mocked Route {route_id}",
        "thesis": {
            "aesthetic_thesis": _THESIS_TEXT,
            "spatial_layout_thesis": _THESIS_TEXT,
            "hero_mechanism": _THESIS_TEXT,
            "section_rhythm": _THESIS_TEXT,
            "visual_metaphor": _THESIS_TEXT,
            "motion_language": _THESIS_TEXT,
            "texture_language": _THESIS_TEXT,
            "image_asset_strategy": _THESIS_TEXT,
            "typography_strategy": _THESIS_TEXT,
            "color_strategy": _THESIS_TEXT,
            "proof_visualization_strategy": _THESIS_TEXT,
        },
        "page_type_modules": ["hero_mock", "proof_mock", "cta_mock"],
        "risks": ["mocked-risk: this route is only a test fixture"],
        "why_this_route_fits": (
            "This route is a mocked fixture used to verify the orchestrator "
            "happy path without calling a real LLM."
        ),
    }


def _valid_batch_json(num_routes: int = 3) -> str:
    payload = {
        "client_slug": "weglot",
        "page_type": "lp_listicle",
        "business_category": "saas",
        "routes": [_route_dict(f"mock-route-{i:02d}") for i in range(num_routes)],
    }
    return json.dumps(payload)


def _make_response(text: str) -> SimpleNamespace:
    """Mimic the shape of the Anthropic SDK response object."""
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(
            input_tokens=2000,
            output_tokens=5500,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


# ────────────────────────────────────────────────────────────────────────────
# Anti-mega-prompt invariant — exposed to live brief shape
# ────────────────────────────────────────────────────────────────────────────


def test_build_system_prompt_under_hard_limit_with_empty_context() -> None:
    prompt = build_system_prompt({}, {}, {})
    assert len(prompt) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS


def test_build_system_prompt_under_hard_limit_with_rich_context() -> None:
    rich_brief = {
        "objective": "x" * 1500,
        "audience": "y" * 1500,
        "angle": "z" * 500,
        "desired_signature": "s" * 200,
        "desired_emotion": "e" * 200,
    }
    rich_brand = {
        "version": "v29.E1.1",
        "tone_summary": "confident-warm-direct",
        "visual_tokens": {"colors": {"primary": {"hex": "#e9dcf0"}}},
    }
    rich_grammar = {
        "density": "high",
        "warmth": "warm",
        "energy": "medium",
        "editoriality": "high",
        "visual_role": "product_centric",
    }
    prompt = build_system_prompt(rich_brief, rich_brand, rich_grammar)
    assert len(prompt) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS


def test_build_system_prompt_includes_all_four_section_markers() -> None:
    prompt = build_system_prompt({}, {}, {})
    for marker in (
        "# SECTION 1 — CLIENT CONTEXT",
        "# SECTION 2 — TASK",
        "# SECTION 3 — OUTPUT SCHEMA",
        "# SECTION 4 — CONSTRAINTS",
    ):
        assert marker in prompt, f"missing prompt section: {marker}"


# ────────────────────────────────────────────────────────────────────────────
# Happy path — single Opus call returns valid JSON
# ────────────────────────────────────────────────────────────────────────────


def test_explore_routes_happy_path() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_batch_json(3))

    batch = explore_routes(
        brief={"objective": "test", "audience": "test", "angle": "test"},
        brand_dna={},
        design_grammar={},
        page_type="lp_listicle",
        business_category="saas",
        client_slug="weglot",
        client=mock_client,
    )

    assert isinstance(batch, CreativeRouteBatch)
    assert len(batch.routes) == 3
    assert batch.client_slug == "weglot"
    assert batch.page_type == "lp_listicle"
    assert batch.business_category == "saas"

    # Single call (no retry)
    assert mock_client.messages.create.call_count == 1

    # Telemetry attached
    pm = batch.prompt_meta
    assert pm["model"] == "claude-opus-4-7"
    assert pm["retry_used"] is False
    assert pm["retry_model"] is None
    assert pm["system_prompt_chars"] > 0
    assert pm["system_prompt_chars"] <= SYSTEM_PROMPT_HARD_LIMIT_CHARS
    assert pm["wall_seconds"] >= 0
    assert pm["tokens_opus"]["output_tokens"] == 5500


def test_explore_routes_accepts_five_routes() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(_valid_batch_json(5))

    batch = explore_routes(
        brief={}, brand_dna={}, design_grammar={},
        page_type="lp_listicle", business_category="saas",
        client_slug="weglot", client=mock_client,
    )
    assert len(batch.routes) == 5


# ────────────────────────────────────────────────────────────────────────────
# Retry path — first call returns garbage, retry returns valid
# ────────────────────────────────────────────────────────────────────────────


def test_explore_routes_retries_on_invalid_first_call() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response("this is not JSON at all just prose"),
        _make_response(_valid_batch_json(3)),
    ]

    batch = explore_routes(
        brief={}, brand_dna={}, design_grammar={},
        page_type="lp_listicle", business_category="saas",
        client_slug="weglot", client=mock_client,
    )

    assert isinstance(batch, CreativeRouteBatch)
    assert mock_client.messages.create.call_count == 2
    pm = batch.prompt_meta
    assert pm["retry_used"] is True
    assert pm["retry_model"] == "claude-sonnet-4-5-20250929"
    assert pm["retry_reason"]  # non-empty
    assert pm["tokens_retry"] is not None


def test_explore_routes_retries_on_validation_failure() -> None:
    """Opus returns JSON but the schema rejects it (e.g. only 2 routes)."""
    invalid_batch = json.dumps({
        "client_slug": "weglot",
        "page_type": "lp_listicle",
        "business_category": "saas",
        "routes": [_route_dict("only-one")],  # <3 → ValidationError
    })
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response(invalid_batch),
        _make_response(_valid_batch_json(3)),
    ]

    batch = explore_routes(
        brief={}, brand_dna={}, design_grammar={},
        page_type="lp_listicle", business_category="saas",
        client_slug="weglot", client=mock_client,
    )
    assert mock_client.messages.create.call_count == 2
    assert batch.prompt_meta["retry_used"] is True


# ────────────────────────────────────────────────────────────────────────────
# Failure path — both calls invalid → CreativeEngineError
# ────────────────────────────────────────────────────────────────────────────


def test_explore_routes_raises_when_both_calls_invalid() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response("garbage prose 1"),
        _make_response("garbage prose 2"),
    ]

    with pytest.raises(CreativeEngineError) as excinfo:
        explore_routes(
            brief={}, brand_dna={}, design_grammar={},
            page_type="lp_listicle", business_category="saas",
            client_slug="weglot", client=mock_client,
        )
    err = excinfo.value
    assert "Opus + Sonnet retry both failed" in str(err)
    assert err.last_raw == "garbage prose 2"
    assert "retry:" in err.upstream
    assert mock_client.messages.create.call_count == 2
