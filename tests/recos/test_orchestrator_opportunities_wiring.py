"""Tests for recos ↔ opportunities wiring (Issue #49).

Covers three behaviours of the orchestrator's Opportunity Layer wire-up:

1. ``build_opportunity_link_map`` correctly maps ``criterion_ref → id`` and
   tolerates a ``None`` batch (backward compat for pages with no
   ``opportunities.json`` yet).
2. ``RecoEnriched`` accepts the new optional ``linked_opportunity_id`` field
   (None default + string value); ``RecoBatch.from_legacy_dict`` round-trips
   a legacy JSON that pre-dates the field.
3. ``process_page``'s wiring path attaches ``linked_opportunity_id`` to
   skipped recos (no LLM call → deterministic) when a matching opportunity
   exists, and stays ``None`` for legacy pages with no opportunities file.

These tests deliberately use the deterministic "skipped" branch (perception
cluster missing → reco generated without LLM call) so we never need to mock
the Anthropic SDK.
"""
from __future__ import annotations

import asyncio
import json
import pathlib

import pytest

from growthcro.models.opportunity_models import Opportunity, OpportunityBatch
from growthcro.models.recos_models import RecoBatch, RecoEnriched
from growthcro.opportunities import save_opportunities
from growthcro.recos.orchestrator import process_page
from growthcro.recos.schema import build_opportunity_link_map


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_opp(client: str, page: str, crit_ref: str) -> Opportunity:
    return Opportunity(
        id=f"opp_{client}_{page}_{crit_ref}",
        criterion_ref=crit_ref,
        page_type=page,
        client_slug=client,
        current_score=20.0,
        target_score=100.0,
        impact=4,
        effort=3,
        confidence=4,
        severity="high",
        category="copy",
        problem=f"Criterion {crit_ref} under target.",
        evidence_ids=[f"ev_{crit_ref}_001"],
        hypothesis="Improving this criterion should lift the metric by 10%.",
        recommended_action=f"Iterate on {crit_ref} per doctrine V3.2.1.",
        metric_to_track="hero_cta_click_through_rate",
        owner="copy",
    )


def _write_prompts_file(
    page_dir: pathlib.Path,
    client: str,
    page: str,
    crit_ids: list[str],
) -> pathlib.Path:
    """Write a recos_v13_prompts.json where every prompt is pre-skipped.

    Skipped prompts let ``process_page`` build the reco deterministically
    without calling the LLM.
    """
    page_dir.mkdir(parents=True, exist_ok=True)
    prompts = [
        {
            "criterion_id": cid,
            "skipped": True,
            "skipped_reason": "no_cluster_for_ensemble",
            "scope": "ENSEMBLE",
            "v12_reco_text": f"v12 baseline for {cid}",
        }
        for cid in crit_ids
    ]
    payload = {
        "version": "v17.0.0-test",
        "client": client,
        "page": page,
        "intent": "test",
        "top_n": len(prompts),
        "prompts": prompts,
    }
    out = page_dir / "recos_v13_prompts.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_build_opportunity_link_map_handles_batch():
    """Mapping should expose every (criterion_ref → id) pair from the batch."""
    batch = OpportunityBatch(
        client_slug="acme",
        page_type="home",
        opportunities=[
            _make_opp("acme", "home", "hero_01"),
            _make_opp("acme", "home", "per_02"),
            _make_opp("acme", "home", "tech_04"),
        ],
    )
    m = build_opportunity_link_map(batch)
    assert m == {
        "hero_01": "opp_acme_home_hero_01",
        "per_02": "opp_acme_home_per_02",
        "tech_04": "opp_acme_home_tech_04",
    }


def test_build_opportunity_link_map_none_batch_returns_empty_dict():
    """Backward compat: pages without opportunities.json yield empty map, no exception."""
    assert build_opportunity_link_map(None) == {}


def test_reco_enriched_accepts_linked_opportunity_id_optional():
    """The new field must default to None (backward compat with legacy disk JSON)."""
    payload = {
        "criterion_id": "hero_01",
        "priority": "P1",
        "before": "before",
        "after": "after",
        "why": "why",
        "expected_lift_pct": 5.0,
        "effort_hours": 2,
        "implementation_notes": "do the thing",
        "evidence_ids": ["ev_001"],
    }
    re = RecoEnriched.model_validate(payload)
    assert re.linked_opportunity_id is None

    payload["linked_opportunity_id"] = "opp_acme_home_hero_01"
    re2 = RecoEnriched.model_validate(payload)
    assert re2.linked_opportunity_id == "opp_acme_home_hero_01"


def test_reco_batch_from_legacy_dict_omits_linked_opportunity_id_field():
    """Legacy JSON pre-dates the field — ``from_legacy_dict`` must default to None."""
    legacy = {
        "version": "v13.test",
        "recos": [
            {
                "criterion_id": "hero_01",
                "priority": "P1",
                "before": "b",
                "after": "a",
                "why": "w",
                "expected_lift_pct": 5.0,
                "effort_hours": 2,
                "implementation_notes": "do",
                "evidence_ids": ["ev_001"],
            }
        ],
    }
    batch = RecoBatch.from_legacy_dict("acme", "home", legacy)
    assert len(batch.recos) == 1
    assert batch.recos[0].linked_opportunity_id is None


def test_process_page_attaches_linked_opportunity_id_when_opps_exist(tmp_path):
    """Run the deterministic 'skipped' branch end-to-end and verify wiring.

    Acceptance: with 5 prompts and 4 matching opportunities → 4/5 recos
    carry a non-None ``linked_opportunity_id`` (80% coverage).
    """
    client, page = "acme", "home"
    crit_ids = ["hero_01", "per_02", "ux_05", "tech_04", "psy_07"]
    matching = crit_ids[:4]  # 4 opportunities, 1 reco unmatched

    # Real on-disk layout under tmp_path so load_opportunities (which uses
    # the package's _DEFAULT_ROOT) finds the file. Patch the persist module
    # to redirect both reads and writes into the sandbox.
    page_dir = tmp_path / "data" / "captures" / client / page
    page_dir.mkdir(parents=True, exist_ok=True)

    # Seed opportunities.json
    batch = OpportunityBatch(
        client_slug=client,
        page_type=page,
        opportunities=[_make_opp(client, page, c) for c in matching],
    )
    save_opportunities(batch, root=tmp_path)
    assert (page_dir / "opportunities.json").is_file()

    # Seed prompts
    prompts_file = _write_prompts_file(page_dir, client, page, crit_ids)
    out_file = page_dir / "recos_v13_final.json"

    # Monkeypatch the persist module's _DEFAULT_ROOT so load_opportunities
    # (called inside process_page without a root override) finds the sandbox.
    import growthcro.opportunities.persist as _persist
    original_root = _persist._DEFAULT_ROOT
    _persist._DEFAULT_ROOT = tmp_path
    try:
        asyncio.run(process_page(
            client_api=None,  # never called — every prompt is pre-skipped
            prompts_file=prompts_file,
            out_file=out_file,
            model="claude-test",
            semaphore=asyncio.Semaphore(1),
            force=False,
        ))
    finally:
        _persist._DEFAULT_ROOT = original_root

    written = json.loads(out_file.read_text(encoding="utf-8"))
    by_crit = {r["criterion_id"]: r for r in written["recos"]}
    assert set(by_crit.keys()) == set(crit_ids), "every prompt must produce a reco"

    # Matched criteria get a linked_opportunity_id; unmatched stays None.
    for cid in matching:
        assert by_crit[cid]["linked_opportunity_id"] == f"opp_{client}_{page}_{cid}", (
            f"reco {cid} should be linked to its opportunity"
        )
    assert by_crit["psy_07"]["linked_opportunity_id"] is None

    n_linked = sum(1 for r in written["recos"] if r.get("linked_opportunity_id"))
    coverage = n_linked / len(written["recos"])
    assert coverage >= 0.8, f"expected >=80% coverage, got {coverage:.0%}"


def test_process_page_legacy_no_opportunities_file_no_exception(tmp_path):
    """When opportunities.json is absent (legacy page), recos still emit with linked_opportunity_id=None."""
    client, page = "acme", "home"
    page_dir = tmp_path / "data" / "captures" / client / page
    page_dir.mkdir(parents=True, exist_ok=True)

    prompts_file = _write_prompts_file(page_dir, client, page, ["hero_01", "per_02"])
    out_file = page_dir / "recos_v13_final.json"

    import growthcro.opportunities.persist as _persist
    original_root = _persist._DEFAULT_ROOT
    _persist._DEFAULT_ROOT = tmp_path
    try:
        # Should not raise even though opportunities.json never exists.
        asyncio.run(process_page(
            client_api=None,
            prompts_file=prompts_file,
            out_file=out_file,
            model="claude-test",
            semaphore=asyncio.Semaphore(1),
            force=False,
        ))
    finally:
        _persist._DEFAULT_ROOT = original_root

    written = json.loads(out_file.read_text(encoding="utf-8"))
    for r in written["recos"]:
        assert r.get("linked_opportunity_id") is None, (
            f"legacy reco {r['criterion_id']} should have None linked_opportunity_id"
        )
