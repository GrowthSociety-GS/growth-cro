"""Tests for the deterministic opportunity orchestrator (Issue #48).

The orchestrator reads four artefacts on disk for one (client, page_type)
pair and emits an ``OpportunityBatch``. Each test below sets up an
isolated sandbox via ``tmp_path``, copies the canonical fixture from
``tests/opportunities/fixtures/weglot_home/``, and asserts behaviour.

Fixtures are deliberately small (5 pillars × a handful of criteria) so
the test stays readable and runs in <100 ms. The Weglot home fixture
mirrors the structural shape of the real ``score_page_type.json``
without dragging in 39 evidence rows.

Coverage
--------
1. ``generate_opportunities`` on the Weglot home fixture → ≥5 opportunities
2. Severity boost when an applicability rule fires on a pillar
3. Priority score formula respects ``(impact * confidence * severity_weight) / effort``
4. ``FileNotFoundError`` raised when ``score_page_type.json`` is missing
5. V26.A invariant — a gap with zero matching evidence is skipped with a WARN log
"""
from __future__ import annotations

import json
import logging
import pathlib
import shutil

import pytest

from growthcro.models.opportunity_models import Opportunity, OpportunityBatch
from growthcro.opportunities.orchestrator import generate_opportunities


# ─────────────────────────────────────────────────────────────────────────────
# Sandbox helpers
# ─────────────────────────────────────────────────────────────────────────────

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures" / "weglot_home"


def _stub_playbook_bloc(
    root: pathlib.Path,
    bloc_n: int,
    pillar: str,
    criteria: list[dict],
) -> None:
    """Write a minimal ``playbook/bloc_<n>_<pillar>_v3.json`` file.

    The orchestrator only consumes ``criteria[*].id``, ``label``, ``weight``
    — we trim everything else away.
    """
    playbook_dir = root / "playbook"
    playbook_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "block": str(bloc_n),
        "pillar": pillar,
        "label": pillar.capitalize(),
        "version": "3.2.1-test",
        "criteria": criteria,
    }
    (playbook_dir / f"bloc_{bloc_n}_{pillar}_v3.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _build_sandbox(tmp_path: pathlib.Path) -> pathlib.Path:
    """Copy the weglot_home fixture into ``tmp_path/data/captures/weglot/home`` and
    seed minimal playbook stubs. Returns ``tmp_path`` (the sandbox root)."""
    captures = tmp_path / "data" / "captures" / "weglot" / "home"
    captures.mkdir(parents=True, exist_ok=True)
    for src in FIXTURES_DIR.iterdir():
        shutil.copy2(src, captures / src.name)

    # Minimal playbook stubs covering every criterion the fixture references.
    _stub_playbook_bloc(tmp_path, 1, "hero", [
        {"id": "hero_01", "label": "H1 = promesse spécifique", "weight": 3},
        {"id": "hero_03", "label": "CTA primary clair (verbe action, taille >= 44px)", "weight": 3},
        {"id": "hero_04", "label": "Visuel hero présent et démonstratif", "weight": 3},
    ])
    _stub_playbook_bloc(tmp_path, 2, "persuasion", [
        {"id": "per_02", "label": "Angle narratif / storytelling fondateur présent", "weight": 3},
        {"id": "per_06", "label": "Bénéfice émotionnel ou identitaire articulé", "weight": 3},
    ])
    _stub_playbook_bloc(tmp_path, 4, "coherence", [
        {"id": "coh_02", "label": "Cohérence visuelle ad → LP", "weight": 3},
        {"id": "coh_04", "label": "Voice tone cohérent et identitaire", "weight": 3},
    ])
    _stub_playbook_bloc(tmp_path, 6, "tech", [
        {"id": "tech_01", "label": "LCP < 2.5s sur mobile", "weight": 3},
        {"id": "tech_02", "label": "CLS < 0.1", "weight": 3},
    ])
    return tmp_path


def _set_applicability_rules(sandbox: pathlib.Path, rules: list[str]) -> None:
    """Overwrite the embedded ``applicability_overlay.rules_matched`` of the
    fixture's ``score_page_type.json``."""
    score_path = sandbox / "data" / "captures" / "weglot" / "home" / "score_page_type.json"
    payload = json.loads(score_path.read_text(encoding="utf-8"))
    payload["applicability_overlay"]["rules_matched"] = rules
    payload["applicability_overlay"]["rules_matched_count"] = len(rules)
    score_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_weglot_home_fixture_produces_at_least_five_opportunities(tmp_path):
    """Acceptance criterion of the task: ≥5 opportunities on Weglot home."""
    sandbox = _build_sandbox(tmp_path)
    batch = generate_opportunities("weglot", "home", root=sandbox)

    assert isinstance(batch, OpportunityBatch)
    assert batch.client_slug == "weglot"
    assert batch.page_type == "home"
    assert len(batch.opportunities) >= 5, (
        f"Expected >=5 opportunities, got {len(batch.opportunities)}"
    )
    # Every opportunity carries non-empty evidence_ids (V26.A invariant)
    for opp in batch.opportunities:
        assert opp.evidence_ids, f"{opp.id} has empty evidence_ids"
        # And every evidence_id is a string token (not None / empty)
        assert all(isinstance(e, str) and e for e in opp.evidence_ids)


def test_severity_boost_when_applicability_rule_fires(tmp_path):
    """If ``rule_saas_coherence_required`` fires, coherence opps escalate
    their severity by one tier."""
    sandbox = _build_sandbox(tmp_path)
    # Baseline run (no rules matched) — capture coherence severities.
    baseline = generate_opportunities("weglot", "home", root=sandbox)
    baseline_coh = {o.criterion_ref: o.severity for o in baseline.opportunities
                    if o.criterion_ref.startswith("coh_")}
    assert baseline_coh, "fixture should produce at least one coherence opp"

    # Now fire the SaaS coherence rule and re-run.
    _set_applicability_rules(sandbox, ["rule_saas_coherence_required"])
    boosted = generate_opportunities("weglot", "home", root=sandbox)
    boosted_coh = {o.criterion_ref: o.severity for o in boosted.opportunities
                   if o.criterion_ref.startswith("coh_")}

    rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    for cid, sev in baseline_coh.items():
        assert rank[boosted_coh[cid]] >= rank[sev], (
            f"{cid}: boosted severity {boosted_coh[cid]!r} should be >= "
            f"baseline {sev!r}"
        )
    # At least one coherence opp should have moved up strictly.
    assert any(rank[boosted_coh[c]] > rank[baseline_coh[c]] for c in baseline_coh), (
        "expected at least one coherence opp to escalate when rule fires"
    )


def test_priority_score_matches_ice_formula():
    """``priority_score = (impact * confidence * severity_weight) / effort``.

    With ``impact=5, confidence=5, severity=critical (weight 5), effort=1``
    the computed priority is ``(5 * 5 * 5) / 1 = 125.0``.
    """
    opp = Opportunity(
        id="opp_unit_test",
        criterion_ref="hero_01",
        page_type="home",
        client_slug="unit",
        current_score=10.0,
        target_score=100.0,
        impact=5,
        effort=1,
        confidence=5,
        severity="critical",
        category="copy",
        problem="Hero H1 is generic and untranslated.",
        evidence_ids=["ev_unit_001"],
        hypothesis="If we sharpen the H1 we lift CTR by 20%.",
        recommended_action="Rewrite H1 toward 100/100 by adding the differentiator.",
        metric_to_track="hero_cta_click_through_rate",
        owner="copy",
    )
    assert opp.priority_score == pytest.approx(125.0)


def test_missing_score_page_type_raises_filenotfound(tmp_path):
    """If ``score_page_type.json`` is missing, the orchestrator raises loud."""
    captures = tmp_path / "data" / "captures" / "weglot" / "home"
    captures.mkdir(parents=True, exist_ok=True)
    # Only seed evidence_ledger; omit score_page_type
    (captures / "evidence_ledger.json").write_text(
        json.dumps({"items": []}), encoding="utf-8"
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        generate_opportunities("weglot", "home", root=tmp_path)
    assert "score_page_type.json" in str(exc_info.value)


def test_gap_without_evidence_is_skipped_with_warning(tmp_path, caplog):
    """V26.A invariant: criterion under-scoring AND missing from evidence_ledger
    must not yield an Opportunity — log a WARN and continue with the rest."""
    sandbox = _build_sandbox(tmp_path)

    # Strip evidence for hero_04 specifically.
    evidence_path = sandbox / "data" / "captures" / "weglot" / "home" / "evidence_ledger.json"
    ledger = json.loads(evidence_path.read_text(encoding="utf-8"))
    ledger["items"] = [it for it in ledger["items"] if it["criterion_ref"] != "hero_04"]
    evidence_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    # ``growthcro.observability.logger`` configures the "growthcro" root with
    # ``propagate=False`` and its own JSON StreamHandler, so caplog's
    # auto-attached handler never sees the records. Attach caplog's handler
    # directly to the namespace for the duration of this test.
    target = logging.getLogger("growthcro.opportunities.orchestrator")
    target.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.WARNING, logger="growthcro.opportunities.orchestrator"):
            batch = generate_opportunities("weglot", "home", root=sandbox)
    finally:
        target.removeHandler(caplog.handler)

    # hero_04 must NOT appear in the batch
    refs = {o.criterion_ref for o in batch.opportunities}
    assert "hero_04" not in refs, "hero_04 should be skipped (no evidence)"
    # Other gaps still produce opportunities
    assert "hero_03" in refs, "hero_03 should still be produced (has evidence)"

    # A WARN log was emitted for hero_04
    skip_logs = [r for r in caplog.records
                 if r.levelno == logging.WARNING
                 and "opportunity.skipped_no_evidence" in r.getMessage()]
    assert skip_logs, "expected a WARN log for the skipped hero_04 opportunity"
    assert any(getattr(r, "criterion_id", None) == "hero_04" for r in skip_logs)
