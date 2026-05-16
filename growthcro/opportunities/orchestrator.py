"""Opportunity engine — deterministic orchestrator (Issue #48).

Mono-concern (ORCHESTRATION axis): read scoring + applicability + evidence
artefacts on disk, apply rules from doctrine V3.2.1, emit an
``OpportunityBatch`` for one (client_slug, page_type) pair.

Zero LLM call. Pure read + transform + Pydantic build. LLM enrichment is
an explicit future epic (P1).

Plumbing dataclasses (``CriterionGap``, ``PriorityData``,
``ScoringSnapshot``) and static lookup tables live in
:mod:`growthcro.opportunities._internals` so this file stays a workflow.

V26.A invariant — evidence_ids
------------------------------
For each criterion gap we look up matching entries in
``evidence_ledger.json``. If a gap has **no** evidence in the ledger we
log a WARN and skip that opportunity rather than fabricating one — this
preserves the doctrine V26.A invariant that every opportunity is
traceable back to a captured signal.

Path conventions (read-only inputs)
-----------------------------------
- ``<root>/data/captures/<client>/<page_type>/score_page_type.json``
- ``<root>/data/captures/<client>/<page_type>/score_applicability_overlay.json``
  (optional — falls back to the ``applicability_overlay`` key embedded in
  ``score_page_type.json``, which is the historical location)
- ``<root>/data/captures/<client>/<page_type>/evidence_ledger.json``
- ``<root>/data/captures/<client>/<page_type>/brief_v2.json`` (optional, advisory)
- ``<root>/playbook/bloc_*_v3.json`` (criterion weights + descriptions)

Callable as ``generate_opportunities(client_slug, page_type, *, root=None,
doctrine_version="v3.2.1")``. ``root`` is a sandbox override used by tests.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from growthcro.models.opportunity_models import (
    Category,
    DoctrineVersion,
    Opportunity,
    OpportunityBatch,
    Owner,
    Severity,
)
from growthcro.observability.logger import get_logger
from growthcro.opportunities._internals import (
    EFFORT_BY_CATEGORY,
    GAP_RATIO_THRESHOLD,
    HYPOTHESIS_TEMPLATE,
    METRIC_BY_CATEGORY,
    PILLAR_TO_CATEGORY,
    PILLAR_TO_OWNER,
    CriterionGap,
    PriorityData,
    ScoringSnapshot,
)

logger = get_logger(__name__)

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]

# Match e.g. "rule_saas_coherence_required" → "coherence".
_RULE_PILLAR_RE = re.compile(r"_(hero|persuasion|ux|coherence|psycho|tech)_")


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

def _captures_dir(client_slug: str, page_type: str, root: pathlib.Path) -> pathlib.Path:
    return root / "data" / "captures" / client_slug / page_type


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_playbook_index(root: pathlib.Path) -> dict[str, dict[str, Any]]:
    """Build a flat ``criterion_id → criterion dict`` index from ``playbook/bloc_*_v3.json``."""
    index: dict[str, dict[str, Any]] = {}
    playbook_dir = root / "playbook"
    for path in sorted(playbook_dir.glob("bloc_*_v3.json")):
        # Skip v3-3 variants — the orchestrator anchors on the locked V3.2.1.
        if "v3-3" in path.name:
            continue
        try:
            bloc = _read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "playbook.bloc_unreadable",
                extra={"path": str(path), "error": str(exc)},
            )
            continue
        for crit in bloc.get("criteria", []):
            cid = crit.get("id")
            if cid:
                index[cid] = crit
    return index


def _load_scoring_artifacts(
    client_slug: str,
    page_type: str,
    root: pathlib.Path,
) -> ScoringSnapshot:
    """Read all on-disk inputs the orchestrator depends on.

    Raises ``FileNotFoundError`` if ``score_page_type.json`` or
    ``evidence_ledger.json`` is missing — those are non-negotiable.
    """
    base = _captures_dir(client_slug, page_type, root)
    score_path = base / "score_page_type.json"
    evidence_path = base / "evidence_ledger.json"

    if not score_path.is_file():
        raise FileNotFoundError(
            f"score_page_type.json missing for {client_slug}/{page_type} at {score_path}"
        )
    if not evidence_path.is_file():
        raise FileNotFoundError(
            f"evidence_ledger.json missing for {client_slug}/{page_type} at {evidence_path}"
        )

    score_page_type = _read_json(score_path)
    evidence_ledger = _read_json(evidence_path)

    overlay_path = base / "score_applicability_overlay.json"
    if overlay_path.is_file():
        applicability_overlay = _read_json(overlay_path)
    else:
        applicability_overlay = score_page_type.get("applicability_overlay", {}) or {}

    return ScoringSnapshot(
        score_page_type=score_page_type,
        applicability_overlay=applicability_overlay,
        evidence_ledger=evidence_ledger,
        playbook_index=_build_playbook_index(root),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Candidate identification + priority computation
# ─────────────────────────────────────────────────────────────────────────────

def _doctrine_rationale(crit: dict[str, Any]) -> str:
    """Short rationale sentence cut from a playbook criterion ``label``."""
    label = (crit.get("label") or "").strip()
    if label:
        return label[:140]
    return "doctrine V3.2.1 criterion under target"


def _identify_opportunity_candidates(snapshot: ScoringSnapshot) -> list[CriterionGap]:
    """Walk every kept criterion under every pillar; emit gaps below threshold."""
    gaps: list[CriterionGap] = []
    universal = snapshot.score_page_type.get("universal", {}).get("byPillar", {})
    for pillar_name, pillar_data in universal.items():
        for crit in pillar_data.get("kept_criteria", []):
            score = float(crit.get("score") or 0.0)
            max_ = float(crit.get("max") or 0.0)
            if max_ <= 0:
                continue
            if score >= max_ * GAP_RATIO_THRESHOLD:
                continue
            cid = crit.get("id")
            if not cid:
                continue
            playbook_crit = snapshot.playbook_index.get(cid, {})
            weight = float(playbook_crit.get("weight") or max_)
            gaps.append(CriterionGap(
                criterion_id=cid,
                pillar=pillar_name,
                current=round((score / max_) * 100.0, 1),
                target=100.0,
                weight=weight,
                description=_doctrine_rationale(playbook_crit),
            ))
    return gaps


def _pillars_boosted_by_rules(applicability: dict[str, Any]) -> set[str]:
    """Return the set of pillar names mentioned by any matched applicability rule."""
    rules = applicability.get("rules_matched") or []
    boosted: set[str] = set()
    for rule in rules:
        m = _RULE_PILLAR_RE.search(str(rule))
        if m:
            boosted.add(m.group(1))
    return boosted


def _impact_score(weight: float, current: float, target: float) -> int:
    """Map ``weight × (target-current)/100`` onto the 1..5 ICE scale."""
    delta_ratio = max(0.0, min(1.0, (target - current) / 100.0))
    raw = weight * delta_ratio
    if raw >= 2.4:
        return 5
    if raw >= 1.8:
        return 4
    if raw >= 1.2:
        return 3
    if raw >= 0.6:
        return 2
    return 1


def _confidence_score(miss_pct: float) -> int:
    """Deeper gaps = more confident."""
    if miss_pct >= 80:
        return 5
    if miss_pct >= 50:
        return 4
    if miss_pct >= 30:
        return 3
    return 2


def _severity_for_current(current: float) -> Severity:
    if current <= 25:
        return "critical"
    if current <= 50:
        return "high"
    if current <= 70:
        return "medium"
    return "low"


def _boost_severity(severity: Severity) -> Severity:
    upgrade: dict[Severity, Severity] = {
        "low": "medium",
        "medium": "high",
        "high": "critical",
        "critical": "critical",
    }
    return upgrade[severity]


def _compute_priority(
    gap: CriterionGap,
    boosted_pillars: set[str],
) -> PriorityData:
    """Heuristic ICE + severity. Pure function, no I/O."""
    category: Category = PILLAR_TO_CATEGORY.get(gap.pillar, "copy")
    severity = _severity_for_current(gap.current)
    if gap.pillar in boosted_pillars:
        severity = _boost_severity(severity)
    return PriorityData(
        impact=_impact_score(gap.weight, gap.current, gap.target),
        effort=EFFORT_BY_CATEGORY.get(category, 3),
        confidence=_confidence_score(gap.target - gap.current),
        severity=severity,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Evidence wiring + final build
# ─────────────────────────────────────────────────────────────────────────────

def _select_evidence_ids(gap: CriterionGap, evidence_ledger: dict[str, Any]) -> list[str]:
    """Return ``evidence_id`` values whose ``criterion_ref`` matches the gap."""
    out: list[str] = []
    for item in evidence_ledger.get("items", []) or []:
        if item.get("criterion_ref") == gap.criterion_id:
            ev_id = item.get("evidence_id")
            if ev_id:
                out.append(str(ev_id))
    return out


def _estimated_lift_pct(gap: CriterionGap, priority: PriorityData) -> int:
    """Coarse % uplift figure that goes into the hypothesis sentence.

    Deliberately conservative (3..25) so downstream readers do not
    over-trust the number — this is a heuristic, not a forecast.
    """
    base = (gap.target - gap.current) / 10.0  # 0..10
    bump = {"low": 1, "medium": 2, "high": 4, "critical": 6}[priority.severity]
    lift = int(round(base + bump))
    return max(3, min(25, lift))


def _build_opportunity(
    gap: CriterionGap,
    priority: PriorityData,
    evidence_ids: list[str],
    client_slug: str,
    page_type: str,
) -> Opportunity:
    category: Category = PILLAR_TO_CATEGORY.get(gap.pillar, "copy")
    metric = METRIC_BY_CATEGORY[category]
    owner: Owner = PILLAR_TO_OWNER.get(gap.pillar, "mixed")

    hypothesis = HYPOTHESIS_TEMPLATE.format(
        criterion_id=gap.criterion_id,
        current=int(round(gap.current)),
        target=int(round(gap.target)),
        metric=metric,
        estimated_lift=_estimated_lift_pct(gap, priority),
        doctrine_rationale=gap.description,
    )[:280]

    problem = (
        f"{gap.pillar.capitalize()} criterion {gap.criterion_id} scoring "
        f"{gap.current:.0f}/100 (target {gap.target:.0f})."
    )[:280]

    recommended_action = (
        f"Lift {gap.criterion_id} toward {gap.target:.0f}/100 by addressing: "
        f"{gap.description}"
    )[:500]

    return Opportunity(
        id=f"opp_{client_slug}_{page_type}_{gap.criterion_id}",
        criterion_ref=gap.criterion_id,
        page_type=page_type,
        client_slug=client_slug,
        current_score=gap.current,
        target_score=gap.target,
        impact=priority.impact,
        effort=priority.effort,
        confidence=priority.confidence,
        severity=priority.severity,
        category=category,
        problem=problem,
        evidence_ids=evidence_ids,
        hypothesis=hypothesis,
        recommended_action=recommended_action,
        metric_to_track=metric,
        owner=owner,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def generate_opportunities(
    client_slug: str,
    page_type: str,
    *,
    root: pathlib.Path | None = None,
    doctrine_version: DoctrineVersion = "v3.2.1",
) -> OpportunityBatch:
    """Build an ``OpportunityBatch`` for one (client, page_type) pair.

    Deterministic. Reads scoring + applicability + evidence artefacts on
    disk. Skips any candidate gap with zero matching evidence_ledger
    entries (logs a WARN). Raises ``FileNotFoundError`` if the two
    non-optional inputs are missing.
    """
    root_path = root or _DEFAULT_ROOT

    snapshot = _load_scoring_artifacts(client_slug, page_type, root_path)
    candidates = _identify_opportunity_candidates(snapshot)
    boosted = _pillars_boosted_by_rules(snapshot.applicability_overlay)

    opportunities: list[Opportunity] = []
    skipped_no_evidence: list[str] = []

    for gap in candidates:
        ev_ids = _select_evidence_ids(gap, snapshot.evidence_ledger)
        if not ev_ids:
            logger.warning(
                "opportunity.skipped_no_evidence",
                extra={
                    "client_slug": client_slug,
                    "page_type": page_type,
                    "criterion_id": gap.criterion_id,
                },
            )
            skipped_no_evidence.append(gap.criterion_id)
            continue
        priority = _compute_priority(gap, boosted)
        opportunities.append(_build_opportunity(
            gap=gap,
            priority=priority,
            evidence_ids=ev_ids,
            client_slug=client_slug,
            page_type=page_type,
        ))

    logger.info(
        "opportunities.generated",
        extra={
            "client_slug": client_slug,
            "page_type": page_type,
            "doctrine_version": doctrine_version,
            "candidates": len(candidates),
            "produced": len(opportunities),
            "skipped_no_evidence": len(skipped_no_evidence),
            "boosted_pillars": sorted(boosted),
        },
    )

    return OpportunityBatch(
        client_slug=client_slug,
        page_type=page_type,
        doctrine_version=doctrine_version,
        opportunities=opportunities,
    )


__all__ = [
    "HYPOTHESIS_TEMPLATE",
    "METRIC_BY_CATEGORY",
    "generate_opportunities",
]
