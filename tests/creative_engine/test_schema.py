"""Tests for ``growthcro.models.creative_models`` (Issue #56, CR-01).

Coverage matrix:
- Happy path: a valid CreativeRoute / CreativeRouteBatch round-trips through
  Pydantic and serialises via ``model_dump`` / ``model_validate``.
- Schema invariants: routes < 3 or > 5 rejected, risks empty rejected,
  why_this_route_fits too short rejected, page_type_modules empty rejected.
- RouteThesis: each thesis field < 20 chars rejected (forces real theses).
- Frozen models: mutation raises ``ValidationError``.
- ``extra='forbid'``: unknown fields rejected at all three levels.
- Batch validator: duplicate ``route_id``s rejected (Visual Judge selects
  by id, so collisions would be silent bugs downstream).
- ``business_category`` Literal: typo rejected (one of 12 verticals only).
- ``route_id`` regex: empty / uppercase / spaces rejected.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from growthcro.models.creative_models import (
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
    CreativeRoute,
    CreativeRouteBatch,
    RouteThesis,
)


# ────────────────────────────────────────────────────────────────────────────
# Factories — minimum-valid inputs we mutate per test
# ────────────────────────────────────────────────────────────────────────────

_THESIS_TEXT = (
    "A real thesis with enough words to clear the 20-char minimum length."
)


def _valid_thesis_kwargs(**overrides: str) -> dict[str, str]:
    base = {
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
    }
    base.update(overrides)
    return base


def _valid_route_kwargs(route_id: str = "editorial-grid-01", **overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "route_id": route_id,
        "route_name": "Editorial Grid — neutral grounding",
        "thesis": RouteThesis(**_valid_thesis_kwargs()),
        "page_type_modules": ["hero_editorial", "proof_strip", "comparison_grid"],
        "risks": ["may feel too restrained vs. competitive listicles"],
        "why_this_route_fits": (
            "The audience is anti-bullshit and scans in 30s; an editorial "
            "grid yields fast hierarchy comprehension."
        ),
    }
    base.update(overrides)
    return base


def _valid_batch_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "client_slug": "weglot",
        "page_type": "lp_listicle",
        "business_category": "saas",
        "routes": [
            CreativeRoute(**_valid_route_kwargs(route_id=f"route-{i:02d}"))
            for i in range(3)
        ],
        "prompt_meta": {"model": "claude-opus-4-7", "system_prompt_chars": 7200},
    }
    base.update(overrides)
    return base


# ────────────────────────────────────────────────────────────────────────────
# Happy path
# ────────────────────────────────────────────────────────────────────────────


def test_valid_batch_constructs_and_round_trips() -> None:
    batch = CreativeRouteBatch(**_valid_batch_kwargs())
    assert len(batch.routes) == 3
    payload = batch.model_dump(mode="json")
    rebuilt = CreativeRouteBatch.model_validate(payload)
    assert rebuilt == batch


def test_batch_accepts_five_routes() -> None:
    batch = CreativeRouteBatch(
        **_valid_batch_kwargs(
            routes=[CreativeRoute(**_valid_route_kwargs(route_id=f"r-{i:02d}")) for i in range(5)],
        )
    )
    assert len(batch.routes) == 5


# ────────────────────────────────────────────────────────────────────────────
# Schema invariants (the failures we want loud)
# ────────────────────────────────────────────────────────────────────────────


def test_batch_rejects_fewer_than_three_routes() -> None:
    with pytest.raises(ValidationError, match="at least 3"):
        CreativeRouteBatch(
            **_valid_batch_kwargs(
                routes=[CreativeRoute(**_valid_route_kwargs(route_id="solo-route"))],
            )
        )


def test_batch_rejects_more_than_five_routes() -> None:
    with pytest.raises(ValidationError, match="at most 5"):
        CreativeRouteBatch(
            **_valid_batch_kwargs(
                routes=[CreativeRoute(**_valid_route_kwargs(route_id=f"r-{i:02d}")) for i in range(6)],
            )
        )


def test_route_rejects_empty_risks() -> None:
    with pytest.raises(ValidationError, match="at least 1"):
        CreativeRoute(**_valid_route_kwargs(risks=[]))


def test_route_rejects_short_why_this_route_fits() -> None:
    with pytest.raises(ValidationError, match="at least 50"):
        CreativeRoute(**_valid_route_kwargs(why_this_route_fits="too short"))


def test_route_rejects_too_few_page_type_modules() -> None:
    with pytest.raises(ValidationError, match="at least 2"):
        CreativeRoute(**_valid_route_kwargs(page_type_modules=["hero_only"]))


def test_thesis_rejects_short_field() -> None:
    with pytest.raises(ValidationError, match="at least 20"):
        RouteThesis(**_valid_thesis_kwargs(hero_mechanism="too short"))


# ────────────────────────────────────────────────────────────────────────────
# Hardening — frozen / extra=forbid / regex / Literal
# ────────────────────────────────────────────────────────────────────────────


def test_route_is_frozen() -> None:
    route = CreativeRoute(**_valid_route_kwargs())
    with pytest.raises(ValidationError):
        route.route_name = "mutated"  # type: ignore[misc]


def test_thesis_is_frozen() -> None:
    thesis = RouteThesis(**_valid_thesis_kwargs())
    with pytest.raises(ValidationError):
        thesis.hero_mechanism = "mutated thesis content that is long enough"  # type: ignore[misc]


def test_batch_rejects_extra_field() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CreativeRouteBatch(**_valid_batch_kwargs(unexpected_field="nope"))


def test_route_rejects_extra_field() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CreativeRoute(**_valid_route_kwargs(unexpected_field="nope"))


def test_batch_rejects_duplicate_route_ids() -> None:
    dup_routes = [
        CreativeRoute(**_valid_route_kwargs(route_id="same-id")),
        CreativeRoute(**_valid_route_kwargs(route_id="same-id")),
        CreativeRoute(**_valid_route_kwargs(route_id="other-id")),
    ]
    with pytest.raises(ValidationError, match="duplicate route_id"):
        CreativeRouteBatch(**_valid_batch_kwargs(routes=dup_routes))


def test_batch_rejects_unknown_business_category() -> None:
    with pytest.raises(ValidationError):
        CreativeRouteBatch(**_valid_batch_kwargs(business_category="not-a-vertical"))


def test_route_id_regex_rejects_uppercase_and_spaces() -> None:
    with pytest.raises(ValidationError):
        CreativeRoute(**_valid_route_kwargs(route_id="HasUpperCase"))
    with pytest.raises(ValidationError):
        CreativeRoute(**_valid_route_kwargs(route_id="has spaces"))
    with pytest.raises(ValidationError):
        CreativeRoute(**_valid_route_kwargs(route_id="ab"))  # too short


# ────────────────────────────────────────────────────────────────────────────
# Sanity — anti-mega-prompt invariant exposed at module level
# ────────────────────────────────────────────────────────────────────────────


def test_hard_limit_constant_exported() -> None:
    """The orchestrator uses this constant to assert prompt length at module
    load. Pin its value here so a silent tweak in the model module is caught
    by CI without depending on the orchestrator being importable."""
    assert SYSTEM_PROMPT_HARD_LIMIT_CHARS == 8000
