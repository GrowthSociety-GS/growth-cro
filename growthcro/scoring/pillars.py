"""Shared pillar dispatcher — pageType filtering, weight, caps, verdict (used by every bloc).

V3.3 (CRE Fusion, 2026-05-11): adds doctrine_version='3.3' option to resolve_doctrine_paths()
so callers (recos/schema.py, scoring/specific/*) can opt into V3.3 enrichments
(bloc_*_v3-3.json + applicability_matrix_v2.json + cre_oco_tables.json). Default '3.2.1'
preserves backward compatibility — 56 existing clients continue to score unchanged.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional


# ────────────────────────────────────────────────────────────────
# V3.3 — doctrine version resolution (backward compatible default)
# ────────────────────────────────────────────────────────────────
DOCTRINE_VERSIONS = ("3.2.1", "3.3")
DEFAULT_DOCTRINE_VERSION = "3.2.1"


def resolve_doctrine_paths(
    doctrine_version: str = DEFAULT_DOCTRINE_VERSION,
    playbook_dir: Path | None = None,
    doctrine_dir: Path | None = None,
) -> dict[str, Path | str | bool]:
    """Return doctrine artefact paths for the requested version.

    V3.2.1 (default): bloc_*_v3.json + applicability_matrix_v1.json. oco_tables absent.
    V3.3: bloc_*_v3-3.json + applicability_matrix_v2.json + cre_oco_tables.json.

    Both versions share scope matrix V1 (ASSET vs ENSEMBLE classification is invariant).

    Caller pattern (recos/schema.load_doctrine):
        paths = resolve_doctrine_paths(doctrine_version='3.3')
        for f in paths['playbook_dir'].glob(paths['bloc_glob']):
            ...
    """
    if doctrine_version not in DOCTRINE_VERSIONS:
        raise ValueError(
            f"doctrine_version must be one of {DOCTRINE_VERSIONS}; got {doctrine_version!r}"
        )

    pb = playbook_dir or Path("playbook")
    dd = doctrine_dir or Path("data/doctrine")

    if doctrine_version == "3.3":
        return {
            "doctrine_version": "3.3",
            "playbook_dir": pb,
            "bloc_glob": "bloc_*_v3-3.json",
            "applicability_matrix": dd / "applicability_matrix_v2.json",
            "applicability_matrix_legacy": dd / "applicability_matrix_v1.json",
            "scope_matrix": dd / "criteria_scope_matrix_v1.json",
            "oco_tables": dd / "cre_oco_tables.json",
            "has_oco_tables": True,
            "has_research_first": True,
        }
    # 3.2.1 default — V3 files, V1 matrix, no oco_tables
    return {
        "doctrine_version": "3.2.1",
        "playbook_dir": pb,
        "bloc_glob": "bloc_*_v3.json",
        "applicability_matrix": dd / "applicability_matrix_v1.json",
        "applicability_matrix_legacy": dd / "applicability_matrix_v1.json",
        "scope_matrix": dd / "criteria_scope_matrix_v1.json",
        "oco_tables": None,
        "has_oco_tables": False,
        "has_research_first": False,
    }


def attach_oco_anchors_to_reco(
    reco: dict,
    criterion_oco_refs: list[str] | None,
) -> dict:
    """V3.3 — attach oco_anchors field to a reco from criterion.oco_refs.

    Called by reco enricher when doctrine_version='3.3'. No-op when oco_refs empty/None,
    which preserves V3.2.1 reco shape (oco_anchors absent → backward compatible).

    The shape is intentionally minimal — just the IDs from cre_oco_tables.json. Downstream
    consumers (dashboard, Notion sync) resolve full objection text by ID.
    """
    if not criterion_oco_refs:
        return reco
    reco["oco_anchors"] = list(criterion_oco_refs)
    return reco


def apply_pagetype_filter(
    results: list[dict],
    page_type: str,
    is_applicable: Callable[[str, str], bool],
) -> tuple[list[dict], list[dict]]:
    """Split results into (active, skipped) based on `is_applicable(criterion_id, page_type)`.

    Skipped results have score=0 and verdict='skipped'. The original list is mutated in place.
    """
    active: list[dict] = []
    skipped: list[dict] = []
    for r in results:
        if is_applicable(r["id"], page_type):
            r["applicable"] = True
            active.append(r)
        else:
            r["applicable"] = False
            r["score"] = 0
            r["verdict"] = "skipped"
            r["rationale"] = f"Critère non applicable pour pageType={page_type}"
            skipped.append(r)
    return active, skipped


def apply_weights(
    active: list[dict],
    skipped: list[dict],
    weights: dict,
    page_type: str,
) -> tuple[float, float, float, int]:
    """Apply per-criterion×pageType weights. Returns (raw_total, weighted_sum, weighted_max, active_max_raw).

    Mutates active items by setting `weight` and `weightedScore`. Skipped items get weight=0.
    """
    raw_total = sum(r["score"] for r in active)
    active_count = len(active)
    active_max_raw = active_count * 3

    weighted_sum = 0.0
    weighted_max = 0.0
    for r in active:
        w = weights.get(r["id"], {}).get(page_type, 1.0)
        weighted_sum += r["score"] * w
        weighted_max += 3 * w
        r["weight"] = w
        r["weightedScore"] = round(r["score"] * w, 2)

    for r in skipped:
        r["weight"] = 0
        r["weightedScore"] = 0

    return raw_total, weighted_sum, weighted_max, active_max_raw


def apply_caps_and_round(
    weighted_sum: float,
    weighted_max: float,
    active_max_raw: int,
    killers: list[tuple[str, bool, float]],
    active_ids: set[str],
) -> tuple[float, float, float, list[str]]:
    """Apply killer caps then round to nearest .5.

    `killers`: list of (criterion_id, killer_triggered, cap_fraction_of_max). The cap is
    expressed as a fraction of `active_max_raw` (e.g. 0.33 → cap to active_max_raw/3).

    Returns (final_normalized, final_capped, final_rounded, caps_applied_log).
    """
    final_normalized = (weighted_sum / weighted_max) * active_max_raw if weighted_max else 0
    final_capped = final_normalized
    caps_applied: list[str] = []

    for cid, triggered, cap_fraction in killers:
        if triggered and cid in active_ids:
            cap_val = round(active_max_raw * cap_fraction)
            if cap_val < final_capped:
                final_capped = cap_val
            caps_applied.append(f"{cid}_killer cap {cap_val}/{active_max_raw}")

    final_rounded = round(final_capped * 2) / 2
    return final_normalized, final_capped, final_rounded, caps_applied


def compute_verdict(score_100: float, caps_applied: list[str]) -> str:
    """Bloc verdict label from /100 score."""
    if caps_applied:
        return "Killer triggered"
    if score_100 >= 80:
        return "TOP"
    if score_100 >= 60:
        return "SOLIDE"
    if score_100 >= 40:
        return "MOYEN"
    return "FAIBLE"
