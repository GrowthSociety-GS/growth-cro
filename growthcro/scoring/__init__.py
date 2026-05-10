"""Scoring layer — pillars dispatcher + UX bloc + page-type-specific detectors + persist."""
from growthcro.scoring.pillars import (
    apply_pagetype_filter,
    apply_weights,
    apply_caps_and_round,
    compute_verdict,
)
from growthcro.scoring.specific import DETECTORS, TERNARY, d_review_required

__all__ = [
    "apply_pagetype_filter",
    "apply_weights",
    "apply_caps_and_round",
    "compute_verdict",
    "DETECTORS",
    "TERNARY",
    "d_review_required",
]
