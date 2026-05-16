"""Tests for ``moteur_multi_judge.persist`` (Issue #54).

Coverage matrix:
- Path convention: ``data/captures/<client>/<page>/multi_judge_audit.json``.
- Round-trip: save then load returns an equivalent dict.
- Missing file → ``load_multi_judge_audit`` returns None (does not raise).
- Atomic write: a crash during write does not leave a partial file on disk
  AND does not leave a stray tmpfile.
- Directory auto-creation: nested missing parents are created.
- Persisted shape includes the load-bearing audit details (killer
  violations + non-shippable reasons) so the webapp / learning layer can
  actually read what they need.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from moteur_multi_judge import (
    load_multi_judge_audit,
    multi_judge_audit_path,
    save_multi_judge_audit,
)


def _make_audit(client: str = "weglot", page: str = "lp_listicle") -> dict:
    """Return a realistic-shaped audit dict (mirrors orchestrator output)."""
    return {
        "client": client,
        "page_type": page,
        "audit_version": "V26.AA.multi_judge",
        "doctrine": {
            "totals": {"total_pct": 88.5, "total": 88.5, "total_max": 100},
            "killer_rules_violated": True,
            "killer_violations": ["KR_hero_offer_missing", "KR_cta_below_fold"],
        },
        "humanlike": {"totals": {"total": 65, "total_max": 80}},
        "implementation": {"bugs_detected": []},
        "final": {
            "final_score_pct": 0,
            "weighted_score_pct": 81.5,
            "verdict": "🔴 Non shippable",
            "impl_penalty_pct": 0.0,
            "breakdown": {"doctrine_pct": 88.5, "humanlike_pct": 81.25},
            "killer_rules_violated": True,
            "killer_violations": ["KR_hero_offer_missing", "KR_cta_below_fold"],
            "non_shippable_reasons": [
                "doctrine_killer_rule_KR_hero_offer_missing",
                "doctrine_killer_rule_KR_cta_below_fold",
            ],
            "blocking_gates_report": {
                "any_gate_failed": True,
                "failed_gates": ["doctrine.killer_rules"],
            },
        },
        "totals_meta": {
            "wall_seconds": 42.3,
            "tokens_in": 12000,
            "tokens_out": 4500,
            "cost_estimate_usd": 0.104,
        },
    }


def test_path_convention(tmp_path: pathlib.Path) -> None:
    path = multi_judge_audit_path("weglot", "lp_listicle", root=tmp_path)
    assert path == (
        tmp_path / "data" / "captures" / "weglot" / "lp_listicle" / "multi_judge_audit.json"
    )


def test_load_missing_returns_none(tmp_path: pathlib.Path) -> None:
    assert load_multi_judge_audit("absent", "lp_listicle", root=tmp_path) is None


def test_round_trip(tmp_path: pathlib.Path) -> None:
    audit = _make_audit()
    out = save_multi_judge_audit(audit, "weglot", "lp_listicle", root=tmp_path)
    assert out.is_file()
    assert out == multi_judge_audit_path("weglot", "lp_listicle", root=tmp_path)

    loaded = load_multi_judge_audit("weglot", "lp_listicle", root=tmp_path)
    assert loaded == audit


def test_save_creates_missing_directories(tmp_path: pathlib.Path) -> None:
    # No data/captures/<client>/<page>/ tree yet — save must build it.
    audit = _make_audit(client="fresh_client", page="advertorial")
    out = save_multi_judge_audit(audit, "fresh_client", "advertorial", root=tmp_path)
    assert out.parent.is_dir()
    assert out.is_file()


def test_persists_killer_violations_and_non_shippable_reasons(
    tmp_path: pathlib.Path,
) -> None:
    """The load-bearing detail (which rules + which gates) must survive disk."""
    audit = _make_audit()
    save_multi_judge_audit(audit, "weglot", "lp_listicle", root=tmp_path)
    loaded = load_multi_judge_audit("weglot", "lp_listicle", root=tmp_path)

    assert loaded is not None
    final = loaded["final"]
    assert final["killer_rules_violated"] is True
    assert final["killer_violations"] == [
        "KR_hero_offer_missing",
        "KR_cta_below_fold",
    ]
    assert final["non_shippable_reasons"] == [
        "doctrine_killer_rule_KR_hero_offer_missing",
        "doctrine_killer_rule_KR_cta_below_fold",
    ]
    assert final["blocking_gates_report"]["any_gate_failed"] is True


def test_atomic_write_failure_preserves_previous(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a crash mid-rename: previous file untouched, no stray tmpfile."""
    first = _make_audit()
    save_multi_judge_audit(first, "weglot", "lp_listicle", root=tmp_path)
    target = multi_judge_audit_path("weglot", "lp_listicle", root=tmp_path)
    before = target.read_text(encoding="utf-8")

    import moteur_multi_judge.persist as persist_mod

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated crash during rename")

    monkeypatch.setattr(persist_mod.os, "replace", boom)

    different = _make_audit()
    different["final"]["final_score_pct"] = 99  # detectable diff
    with pytest.raises(RuntimeError, match="simulated crash"):
        save_multi_judge_audit(different, "weglot", "lp_listicle", root=tmp_path)

    # Previous file untouched.
    assert target.read_text(encoding="utf-8") == before

    # No leftover tmpfile.
    leftovers = list(target.parent.glob(".multi_judge_audit.*.json.tmp"))
    assert leftovers == [], f"tmpfile not cleaned up: {leftovers}"


def test_persisted_json_is_well_formed(tmp_path: pathlib.Path) -> None:
    """Sanity: on-disk file is valid UTF-8 JSON, indented, parses back."""
    save_multi_judge_audit(_make_audit(), "weglot", "lp_listicle", root=tmp_path)
    target = multi_judge_audit_path("weglot", "lp_listicle", root=tmp_path)
    raw = target.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert parsed["client"] == "weglot"
    assert parsed["page_type"] == "lp_listicle"
    assert parsed["final"]["verdict"] == "🔴 Non shippable"
