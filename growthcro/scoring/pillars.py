"""Shared pillar dispatcher — pageType filtering, weight, caps, verdict (used by every bloc)."""
from __future__ import annotations

from typing import Callable, Optional


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
