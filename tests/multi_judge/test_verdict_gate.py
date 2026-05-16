"""Tests for the Verdict Gate aggregator (Wave 3 #50).

Covers the four canonical cases from the task spec:

  * composite=92% + killer_rules_violated=True   → verdict forced to Non shippable
  * composite=92% + impeccable_passed=False      → verdict forced to Non shippable
  * composite=70% + all gates OK                 → verdict left untouched
  * composite=92% + all gates OK                 → verdict left untouched (🏆 Exceptionnel)

Plus 2 unit-level checks on ``aggregate_blocking_gates`` directly.

The orchestrator tests stub the doctrine/humanlike/impl judges so we don't
need real LLM calls. They exercise ``run_multi_judge`` end-to-end with a
controlled composite + controlled gate inputs.
"""
from __future__ import annotations

from unittest.mock import patch

from moteur_multi_judge.judges.blocking_gates import (
    BlockingGatesReport,
    VerdictGateError,
    aggregate_blocking_gates,
)
from moteur_multi_judge.orchestrator import run_multi_judge


# ─────────────────────────────────────────────────────────────────────────────
# Helper stubs — replace the 3 sub-judges so we control doctrine_pct + flags.
# ─────────────────────────────────────────────────────────────────────────────

def _make_doctrine_stub(pct: float, *, killer: bool = False) -> dict:
    """Return what ``audit_lp_doctrine`` would return for a given pct + killer flag."""
    return {
        "totals": {"total_pct": pct, "total": pct, "total_max": 100},
        "killer_rules_violated": killer,
        "killer_violations": ["KR_test"] if killer else [],
        "tokens_in": 0,
        "tokens_out": 0,
    }


def _make_humanlike_stub(pct: float) -> dict:
    return {
        "totals": {"total": pct, "total_max": 100},
        "tokens_in": 0,
        "tokens_out": 0,
    }


def _patch_judges(doctrine_pct: float, *, killer: bool = False, humanlike_pct: float = 90.0):
    """Stack of patches that replace the 3 sub-judges with fixed-output stubs."""
    doctrine_p = patch(
        "moteur_multi_judge.orchestrator.audit_lp_doctrine",
        return_value=_make_doctrine_stub(doctrine_pct, killer=killer),
    )
    humanlike_p = patch(
        "moteur_multi_judge.orchestrator._load_humanlike_module",
        return_value=None,  # forces fallback path; humanlike skipped → orchestrator uses doctrine only
    )
    impl_p = patch(
        "moteur_multi_judge.orchestrator._load_implementation_module",
        return_value=None,
    )
    return doctrine_p, humanlike_p, impl_p


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests on aggregate_blocking_gates directly
# ─────────────────────────────────────────────────────────────────────────────


def test_aggregate_all_gates_pass_returns_no_failure():
    """When every input is healthy, any_gate_failed must be False."""
    report = aggregate_blocking_gates(
        impeccable_report={"passed": True},
        doctrine_audit={"killer_rules_violated": False},
        implementation_audit={"impl_penalty_pp": 0.0},
        skip_subprocess_checks=True,
    )
    assert isinstance(report, BlockingGatesReport)
    assert report.any_gate_failed is False
    assert report.failed_gates == []


def test_aggregate_killer_rule_violation_flags_failure():
    """A killer-rule violation alone must trip the gate."""
    report = aggregate_blocking_gates(
        impeccable_report={"passed": True},
        doctrine_audit={"killer_rules_violated": True},
        implementation_audit={"impl_penalty_pp": 0.0},
        skip_subprocess_checks=True,
    )
    assert report.any_gate_failed is True
    assert "doctrine_killer_rules" in report.failed_gates


def test_aggregate_impeccable_failure_flags_failure():
    """impeccable_qa.passed=False alone must trip the gate."""
    report = aggregate_blocking_gates(
        impeccable_report={"passed": False},
        doctrine_audit={"killer_rules_violated": False},
        implementation_audit={"impl_penalty_pp": 0.0},
        skip_subprocess_checks=True,
    )
    assert report.any_gate_failed is True
    assert "impeccable_qa" in report.failed_gates


def test_aggregate_impl_penalty_threshold_triggers():
    """impl_penalty > 10pp must trip impl_penalty_exceeded."""
    report = aggregate_blocking_gates(
        impeccable_report={"passed": True},
        doctrine_audit={"killer_rules_violated": False},
        implementation_audit={"impl_penalty_pp": 12.0},
        skip_subprocess_checks=True,
    )
    assert report.impl_penalty_exceeded is True
    assert report.any_gate_failed is True


def test_aggregate_impl_penalty_recomputed_from_bug_list():
    """When impl_penalty_pp is absent, recompute from `bugs_detected` list."""
    report = aggregate_blocking_gates(
        impeccable_report={"passed": True},
        doctrine_audit={"killer_rules_violated": False},
        implementation_audit={
            "bugs_detected": [
                {"severity": "critical"},  # -10pp
                {"severity": "warning"},   #  -2pp
            ],
        },
        skip_subprocess_checks=True,
    )
    # Total -12pp = exceeds 10pp threshold.
    assert report.impl_penalty_pp == 12.0
    assert report.impl_penalty_exceeded is True


def test_verdict_gate_error_accepts_dict():
    """VerdictGateError must accept a dict (the serialized form stored in audit)."""
    err = VerdictGateError({"failed_gates": ["impeccable_qa", "doctrine_killer_rules"]})
    msg = str(err)
    assert "impeccable_qa" in msg
    assert "doctrine_killer_rules" in msg


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator integration — the 4 canonical fixtures from the spec
# ─────────────────────────────────────────────────────────────────────────────


def _patch_subprocess_all_pass():
    """Force every check_gsg_*.py + SCHEMA/validate_all.py subprocess to pass.

    Without this, the orchestrator tests would spawn 7 real subprocesses
    each, costing ~30s/test and producing flaky pass/fail dependent on the
    repo's data state. Used in every orchestrator test for both speed and
    determinism."""
    return patch(
        "moteur_multi_judge.judges.blocking_gates._run_script_exit_0",
        return_value=True,
    )


def test_orchestrator_composite_92_with_killer_rule_forces_non_shippable():
    """composite=92% + killer rule → verdict='🔴 Non shippable', final=0."""
    doctrine_p, humanlike_p, impl_p = _patch_judges(doctrine_pct=92.0, killer=True)
    with doctrine_p, humanlike_p, impl_p, _patch_subprocess_all_pass():
        audit = run_multi_judge(
            html="<html></html>",
            client="weglot",
            page_type="lp_listicle",
            weight_doctrine=1.0,
            weight_humanlike=0.0,
            skip_humanlike=True,
            skip_implementation=True,
            upstream_impeccable_report={"passed": True},
            verbose=False,
        )
    final = audit["final"]
    assert final["verdict"] == "🔴 Non shippable"
    assert final["final_score_pct"] == 0
    assert "doctrine_killer_rules" in final["non_shippable_reasons"]


def test_orchestrator_composite_92_with_impeccable_fail_forces_non_shippable():
    """composite=92% + impeccable_qa.passed=False → verdict='🔴 Non shippable'."""
    doctrine_p, humanlike_p, impl_p = _patch_judges(doctrine_pct=92.0, killer=False)
    with doctrine_p, humanlike_p, impl_p, _patch_subprocess_all_pass():
        audit = run_multi_judge(
            html="<html></html>",
            client="weglot",
            page_type="lp_listicle",
            weight_doctrine=1.0,
            weight_humanlike=0.0,
            skip_humanlike=True,
            skip_implementation=True,
            upstream_impeccable_report={"passed": False},
            verbose=False,
        )
    final = audit["final"]
    assert final["verdict"] == "🔴 Non shippable"
    assert final["final_score_pct"] == 0
    assert "impeccable_qa" in final["non_shippable_reasons"]


def test_orchestrator_composite_70_all_gates_ok_keeps_verdict():
    """composite=70% + all gates OK → verdict left as-is (🟡 Bon @ 70%)."""
    doctrine_p, humanlike_p, impl_p = _patch_judges(doctrine_pct=70.0, killer=False)
    with doctrine_p, humanlike_p, impl_p, _patch_subprocess_all_pass():
        audit = run_multi_judge(
            html="<html></html>",
            client="weglot",
            page_type="lp_listicle",
            weight_doctrine=1.0,
            weight_humanlike=0.0,
            skip_humanlike=True,
            skip_implementation=True,
            upstream_impeccable_report={"passed": True},
            verbose=False,
        )
    final = audit["final"]
    # _verdict_tier(70.0) → "🟡 Bon" (≥70 < 78)
    assert final["verdict"] == "🟡 Bon"
    assert final["final_score_pct"] == 70.0
    assert "non_shippable_reasons" not in final


def test_orchestrator_composite_92_all_gates_ok_keeps_verdict():
    """composite=92% + all gates OK → verdict='🚀 Stratospheric' (≥92)."""
    doctrine_p, humanlike_p, impl_p = _patch_judges(doctrine_pct=92.0, killer=False)
    with doctrine_p, humanlike_p, impl_p, _patch_subprocess_all_pass():
        audit = run_multi_judge(
            html="<html></html>",
            client="weglot",
            page_type="lp_listicle",
            weight_doctrine=1.0,
            weight_humanlike=0.0,
            skip_humanlike=True,
            skip_implementation=True,
            upstream_impeccable_report={"passed": True},
            verbose=False,
        )
    final = audit["final"]
    assert final["verdict"] == "🚀 Stratospheric"
    assert final["final_score_pct"] == 92.0
    assert "non_shippable_reasons" not in final
