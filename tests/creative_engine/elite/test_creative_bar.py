"""Tests for ``moteur_gsg.creative_engine.elite.creative_bar`` (CR-09 #64).

Coverage matrix:
- All 12 BusinessCategory verticals have a Creative Bar entry.
- Each entry is non-empty and within the 1000-char cap.
- ``get_creative_bar`` returns the entry for a valid vertical.
- ``get_creative_bar`` raises KeyError for an unknown vertical.
- Each entry mentions key required signals (anti-patterns / mobile / proof).
"""
from __future__ import annotations

import typing

import pytest

from growthcro.models.creative_models import BusinessCategory
from moteur_gsg.creative_engine.elite.creative_bar import (
    CREATIVE_BAR_BY_VERTICAL,
    get_creative_bar,
)


# ────────────────────────────────────────────────────────────────────────────
# Completeness — all 12 verticals are present
# ────────────────────────────────────────────────────────────────────────────


def _all_verticals() -> list[str]:
    """Extract verticals from the Literal type — single source of truth."""
    return list(typing.get_args(BusinessCategory))


def test_all_12_verticals_have_an_entry() -> None:
    expected = set(_all_verticals())
    assert expected == set(CREATIVE_BAR_BY_VERTICAL.keys()), (
        f"missing verticals: {expected - set(CREATIVE_BAR_BY_VERTICAL.keys())}; "
        f"extra: {set(CREATIVE_BAR_BY_VERTICAL.keys()) - expected}"
    )


def test_exactly_12_verticals() -> None:
    assert len(CREATIVE_BAR_BY_VERTICAL) == 12


# ────────────────────────────────────────────────────────────────────────────
# Per-entry shape: non-empty, ≤ 1000 chars
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("vertical", _all_verticals())
def test_entry_is_non_empty(vertical: str) -> None:
    entry = CREATIVE_BAR_BY_VERTICAL[vertical]
    assert entry.strip(), f"vertical {vertical!r} has empty entry"


@pytest.mark.parametrize("vertical", _all_verticals())
def test_entry_under_1000_chars(vertical: str) -> None:
    entry = CREATIVE_BAR_BY_VERTICAL[vertical]
    assert len(entry) <= 1000, (
        f"vertical {vertical!r} entry is {len(entry)} chars, exceeds 1000 cap"
    )


@pytest.mark.parametrize("vertical", _all_verticals())
def test_entry_mentions_anti_patterns(vertical: str) -> None:
    """Each entry must mention 'Anti' to surface vertical-specific banned patterns."""
    entry = CREATIVE_BAR_BY_VERTICAL[vertical].lower()
    assert "anti" in entry, (
        f"vertical {vertical!r} entry must include explicit Anti-patterns section"
    )


@pytest.mark.parametrize("vertical", _all_verticals())
def test_entry_mentions_mobile(vertical: str) -> None:
    """Each entry must mention mobile expectations (mobile-first or responsive)."""
    entry = CREATIVE_BAR_BY_VERTICAL[vertical].lower()
    assert "mobile" in entry, (
        f"vertical {vertical!r} entry must mention mobile expectations"
    )


# ────────────────────────────────────────────────────────────────────────────
# get_creative_bar API
# ────────────────────────────────────────────────────────────────────────────


def test_get_creative_bar_returns_known_entry() -> None:
    entry = get_creative_bar("saas")
    assert entry
    assert entry == CREATIVE_BAR_BY_VERTICAL["saas"]


def test_get_creative_bar_unknown_raises_key_error() -> None:
    with pytest.raises(KeyError) as excinfo:
        get_creative_bar("not_a_real_vertical")  # type: ignore[arg-type]
    assert "no creative_bar entry" in str(excinfo.value)


@pytest.mark.parametrize("vertical", _all_verticals())
def test_get_creative_bar_for_every_vertical(vertical: str) -> None:
    """API-level smoke: every Literal vertical resolves via get_creative_bar."""
    entry = get_creative_bar(vertical)  # type: ignore[arg-type]
    assert entry == CREATIVE_BAR_BY_VERTICAL[vertical]
