"""Tests for ``growthcro.opportunities.persist`` (Issue #47).

Coverage matrix:
- Round-trip: save then load returns an equivalent batch.
- Path convention: ``data/captures/<client>/<page>/opportunities.json``.
- Missing file → ``load_opportunities`` returns None (does not raise).
- Atomic write: a crash during write must not leave a partial
  ``opportunities.json`` on disk.
- Directory auto-creation: nested missing parents are created.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from growthcro.opportunities import (
    Opportunity,
    OpportunityBatch,
    load_opportunities,
    opportunities_path,
    save_opportunities,
)


def _make_batch(client: str = "weglot", page: str = "landing_page") -> OpportunityBatch:
    opp = Opportunity(
        id="opp_hero_01",
        criterion_ref="hero_01",
        page_type=page,
        client_slug=client,
        current_score=40.0,
        target_score=80.0,
        impact=4,
        effort=2,
        confidence=5,
        severity="high",
        category="copy",
        problem="Hero CTA copy is generic and does not surface the offer.",
        evidence_ids=["evidence_capture_01"],
        hypothesis="If we surface the offer in the hero CTA, CTR will lift because intent matches.",
        recommended_action="Rewrite hero CTA to 'Translate your site in 1 click — 10-day free trial'.",
        metric_to_track="hero_cta_click_through_rate",
        owner="copy",
    )
    return OpportunityBatch(
        client_slug=client,
        page_type=page,
        opportunities=[opp],
    )


def test_path_convention(tmp_path: pathlib.Path) -> None:
    path = opportunities_path("weglot", "landing_page", root=tmp_path)
    assert path == tmp_path / "data" / "captures" / "weglot" / "landing_page" / "opportunities.json"


def test_load_missing_returns_none(tmp_path: pathlib.Path) -> None:
    assert load_opportunities("absent_client", "landing_page", root=tmp_path) is None


def test_round_trip(tmp_path: pathlib.Path) -> None:
    batch = _make_batch()
    out = save_opportunities(batch, root=tmp_path)
    assert out.is_file()
    assert out == opportunities_path("weglot", "landing_page", root=tmp_path)

    loaded = load_opportunities("weglot", "landing_page", root=tmp_path)
    assert loaded is not None
    assert loaded == batch


def test_round_trip_preserves_priority_score(tmp_path: pathlib.Path) -> None:
    batch = _make_batch()
    save_opportunities(batch, root=tmp_path)
    loaded = load_opportunities("weglot", "landing_page", root=tmp_path)
    assert loaded is not None
    assert loaded.opportunities[0].priority_score == batch.opportunities[0].priority_score


def test_save_creates_missing_directories(tmp_path: pathlib.Path) -> None:
    # No `data/captures/...` tree yet — save must build it.
    batch = _make_batch(client="fresh_client")
    out = save_opportunities(batch, root=tmp_path)
    assert out.parent.is_dir()
    assert out.is_file()


def test_save_overwrites_existing(tmp_path: pathlib.Path) -> None:
    save_opportunities(_make_batch(), root=tmp_path)
    new_batch = OpportunityBatch(
        client_slug="weglot",
        page_type="landing_page",
        opportunities=[],
    )
    save_opportunities(new_batch, root=tmp_path)
    loaded = load_opportunities("weglot", "landing_page", root=tmp_path)
    assert loaded is not None
    assert loaded.opportunities == []


def test_atomic_write_failure_preserves_previous(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a crash mid-write: os.replace raises.

    Acceptance: (a) the previous file is untouched, (b) no stray tmpfile
    is left behind in the destination directory.
    """
    original = _make_batch()
    save_opportunities(original, root=tmp_path)
    target = opportunities_path("weglot", "landing_page", root=tmp_path)
    before = target.read_text(encoding="utf-8")

    import growthcro.opportunities.persist as persist_mod

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated crash during rename")

    monkeypatch.setattr(persist_mod.os, "replace", boom)

    # Second save with a different payload must fail.
    different = OpportunityBatch(
        client_slug="weglot",
        page_type="landing_page",
        opportunities=[],
    )
    with pytest.raises(RuntimeError, match="simulated crash"):
        save_opportunities(different, root=tmp_path)

    # Previous file untouched.
    assert target.read_text(encoding="utf-8") == before

    # No leftover tmpfile.
    leftovers = list(target.parent.glob(".opportunities.*.json.tmp"))
    assert leftovers == [], f"tmpfile not cleaned up: {leftovers}"


def test_persisted_json_is_valid(tmp_path: pathlib.Path) -> None:
    """Sanity: the on-disk file is well-formed JSON, indented, UTF-8."""
    save_opportunities(_make_batch(), root=tmp_path)
    target = opportunities_path("weglot", "landing_page", root=tmp_path)
    raw = target.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert parsed["client_slug"] == "weglot"
    assert parsed["page_type"] == "landing_page"
    assert isinstance(parsed["opportunities"], list)
    assert parsed["opportunities"][0]["id"] == "opp_hero_01"
