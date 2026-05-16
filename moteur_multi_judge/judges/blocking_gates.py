"""VerdictGate — aggregate the hard-stop gates that override the composite.

Mono-concern (axis: validation). Stdlib + Pydantic v2 only. No LLM.

The multi-judge composite (``orchestrator.run_multi_judge``) is a *quality*
signal — it does not know whether a page is *shippable*. Shipping requires
a deterministic set of gates to pass:

  1. impeccable_qa heuristic (``impeccable_report.passed == True``)
  2. doctrine killer rules (``doctrine_judge.killer_rules_violated == False``)
  3. implementation runtime penalty (``impl_penalty_pp <= 10pp``)
  4. six ``scripts/check_gsg_*.py`` schema/contract validators exit 0
  5. ``SCHEMA/validate_all.py`` exits 0 (canonical JSON schemas hold)

Any gate failing means *non-shippable*, regardless of composite score.
Wave 3 #50 wires the orchestrator to force ``final_score_pct=0`` and
``verdict="🔴 Non shippable"`` when ``any_gate_failed`` is True.
``mode_1_complete`` raises ``VerdictGateError`` when ``ship_strict=True``.

Audit source : §6 P0.1 + §7 ISSUE-P0-01 + §10.2 of
``.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]

# Subprocess hard timeout per script. Timeout → soft-fail (passed=False).
_SUBPROCESS_TIMEOUT_S = 60

# The six check_gsg_*.py boundary validators (verified 2026-05-16). The
# audit dossier said "7" counting SCHEMA/validate_all.py — that one is
# tracked separately as `schema_validate_passed` below.
_CHECK_GSG_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("canonical",              "scripts/check_gsg_canonical.py"),
    ("component_planner",      "scripts/check_gsg_component_planner.py"),
    ("controlled_renderer",    "scripts/check_gsg_controlled_renderer.py"),
    ("creative_route_selector","scripts/check_gsg_creative_route_selector.py"),
    ("intake_wizard",          "scripts/check_gsg_intake_wizard.py"),
    ("visual_renderer",        "scripts/check_gsg_visual_renderer.py"),
)
_SCHEMA_VALIDATE_SCRIPT = "SCHEMA/validate_all.py"

# Above this threshold (in pp), runtime penalty kills shipping. 10pp = one
# critical bug OR five warning bugs given the orchestrator's scoring.
_IMPL_PENALTY_THRESHOLD_PP = 10.0

VerdictTier = Literal["🔴 Non shippable"]


class VerdictGateError(Exception):
    """Raised when ``run_mode_1_complete(ship_strict=True)`` and any gate failed.

    Carries the full ``BlockingGatesReport`` (or its serialized dict form)
    so callers can render the failed-gate list for the user. Accepts a dict
    too because the orchestrator stores the report serialised in the audit
    payload and may pass that dict directly.
    """

    def __init__(self, report: "BlockingGatesReport | dict") -> None:
        self.report = report
        if isinstance(report, dict):
            failed = report.get("failed_gates") or []
        else:
            failed = report.failed_gates
        super().__init__(
            f"VerdictGate refused ship: {len(failed)} gate(s) failed: "
            f"{', '.join(failed)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Report shape
# ─────────────────────────────────────────────────────────────────────────────


class BlockingGatesReport(BaseModel):
    """Aggregated pass/fail of every blocking gate for one GSG run.

    A ``True`` per-gate means the gate *passed*. ``any_gate_failed`` is the
    single shipping signal. ``failed_gates`` lists the failing gates.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    impeccable_passed: bool
    killer_rules_violated: bool
    impl_penalty_pp: float = Field(ge=0)
    impl_penalty_exceeded: bool
    # Six check_gsg_*.py boundary validators (see _CHECK_GSG_SCRIPTS).
    check_gsg_canonical_passed: bool
    check_gsg_component_planner_passed: bool
    check_gsg_controlled_renderer_passed: bool
    check_gsg_creative_route_selector_passed: bool
    check_gsg_intake_wizard_passed: bool
    check_gsg_visual_renderer_passed: bool
    # SCHEMA/validate_all.py — JSON schema canonical contracts.
    schema_validate_passed: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def any_gate_failed(self) -> bool:
        """True iff any blocking gate failed — the single shipping signal."""
        return (
            not self.impeccable_passed
            or self.killer_rules_violated
            or self.impl_penalty_exceeded
            or not self.check_gsg_canonical_passed
            or not self.check_gsg_component_planner_passed
            or not self.check_gsg_controlled_renderer_passed
            or not self.check_gsg_creative_route_selector_passed
            or not self.check_gsg_intake_wizard_passed
            or not self.check_gsg_visual_renderer_passed
            or not self.schema_validate_passed
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def failed_gates(self) -> list[str]:
        """Names of gates that failed, in stable order."""
        failed: list[str] = []
        if not self.impeccable_passed:
            failed.append("impeccable_qa")
        if self.killer_rules_violated:
            failed.append("doctrine_killer_rules")
        if self.impl_penalty_exceeded:
            failed.append(f"implementation_penalty_>{_IMPL_PENALTY_THRESHOLD_PP}pp")
        if not self.check_gsg_canonical_passed:
            failed.append("check_gsg_canonical")
        if not self.check_gsg_component_planner_passed:
            failed.append("check_gsg_component_planner")
        if not self.check_gsg_controlled_renderer_passed:
            failed.append("check_gsg_controlled_renderer")
        if not self.check_gsg_creative_route_selector_passed:
            failed.append("check_gsg_creative_route_selector")
        if not self.check_gsg_intake_wizard_passed:
            failed.append("check_gsg_intake_wizard")
        if not self.check_gsg_visual_renderer_passed:
            failed.append("check_gsg_visual_renderer")
        if not self.schema_validate_passed:
            failed.append("schema_validate_all")
        return failed


# ─────────────────────────────────────────────────────────────────────────────
# Subprocess runner — captures exit codes from existing GSG schema checkers
# ─────────────────────────────────────────────────────────────────────────────


def _run_script_exit_0(script_rel_path: str) -> bool:
    """Run a Python script via subprocess. True iff it exits 0 in <=60s.

    Soft-fail: any exception (missing file, timeout, etc.) → False so the
    gate registers a failure rather than crashing the pipeline.
    """
    script_path = ROOT / script_rel_path
    if not script_path.exists():
        logger.warning(
            "blocking_gates.script_not_found",
            extra={"script": script_rel_path},
        )
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            capture_output=True,
            check=False,
            timeout=_SUBPROCESS_TIMEOUT_S,
        )
        passed = result.returncode == 0
        if not passed:
            logger.warning(
                "blocking_gates.script_failed",
                extra={
                    "script": script_rel_path,
                    "returncode": result.returncode,
                    "stderr_tail": (result.stderr or b"")[-200:].decode("utf-8", "replace"),
                },
            )
        return passed
    except subprocess.TimeoutExpired:
        logger.warning(
            "blocking_gates.script_timeout",
            extra={"script": script_rel_path, "timeout_s": _SUBPROCESS_TIMEOUT_S},
        )
        return False
    except Exception as exc:
        logger.warning(
            "blocking_gates.script_error",
            extra={"script": script_rel_path, "error": str(exc)[:200]},
        )
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Public entrypoint
# ─────────────────────────────────────────────────────────────────────────────


def aggregate_blocking_gates(
    impeccable_report: dict,
    doctrine_audit: dict,
    implementation_audit: dict,
    *,
    skip_subprocess_checks: bool = False,
) -> BlockingGatesReport:
    """Aggregate every blocking gate into a single ``BlockingGatesReport``.

    Args:
        impeccable_report: output of ``moteur_gsg.core.impeccable_qa.run_impeccable_qa``.
        doctrine_audit:    output of ``moteur_multi_judge.judges.doctrine_judge.audit_lp_doctrine``.
        implementation_audit: orchestrator's ``audit["implementation"]`` dict
            (output of ``fix_html_runtime.detect_runtime_bugs``). The function
            recomputes the penalty locally from the bug list using the same
            formula as ``orchestrator._impl_penalty`` so callers can hand the
            raw report directly.
        skip_subprocess_checks: if True, mark the 7 subprocess gates as
            ``True`` without running them. Used by unit tests.

    Returns:
        ``BlockingGatesReport`` with one bool per gate plus computed
        ``any_gate_failed`` and ``failed_gates``.
    """
    impeccable_passed = bool(impeccable_report.get("passed", False))
    killer_rules_violated = bool(doctrine_audit.get("killer_rules_violated", False))

    # Impl penalty: explicit field wins (test fixtures); otherwise recompute
    # from the raw bug list using the same formula as `orchestrator._impl_penalty`.
    impl_penalty_pp = float(implementation_audit.get("impl_penalty_pp", 0.0))
    if impl_penalty_pp == 0.0 and implementation_audit:
        fixes = (
            implementation_audit.get("bugs_detected")
            or implementation_audit.get("warnings")
            or []
        )
        if isinstance(fixes, list):
            n_crit = sum(
                1 for it in fixes
                if isinstance(it, dict)
                and (it.get("severity") or "warning").lower() in ("critical", "error", "fatal")
            )
            n_warn = len(fixes) - n_crit
            impl_penalty_pp = float(min(25.0, n_crit * 10 + n_warn * 2))
    impl_penalty_exceeded = impl_penalty_pp > _IMPL_PENALTY_THRESHOLD_PP

    if skip_subprocess_checks:
        script_results: dict[str, bool] = {name: True for name, _ in _CHECK_GSG_SCRIPTS}
        schema_validate_passed = True
    else:
        script_results = {
            name: _run_script_exit_0(path) for name, path in _CHECK_GSG_SCRIPTS
        }
        schema_validate_passed = _run_script_exit_0(_SCHEMA_VALIDATE_SCRIPT)

    report = BlockingGatesReport(
        impeccable_passed=impeccable_passed,
        killer_rules_violated=killer_rules_violated,
        impl_penalty_pp=impl_penalty_pp,
        impl_penalty_exceeded=impl_penalty_exceeded,
        check_gsg_canonical_passed=script_results["canonical"],
        check_gsg_component_planner_passed=script_results["component_planner"],
        check_gsg_controlled_renderer_passed=script_results["controlled_renderer"],
        check_gsg_creative_route_selector_passed=script_results["creative_route_selector"],
        check_gsg_intake_wizard_passed=script_results["intake_wizard"],
        check_gsg_visual_renderer_passed=script_results["visual_renderer"],
        schema_validate_passed=schema_validate_passed,
    )
    logger.info(
        "blocking_gates.report",
        extra={
            "any_gate_failed": report.any_gate_failed,
            "failed_gates": report.failed_gates,
            "impl_penalty_pp": report.impl_penalty_pp,
        },
    )
    return report


__all__ = [
    "BlockingGatesReport",
    "VerdictGateError",
    "VerdictTier",
    "aggregate_blocking_gates",
]
