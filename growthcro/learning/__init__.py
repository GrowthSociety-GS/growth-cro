"""GrowthCRO Learning Layer.

Issue #23. V29 is audit-based (`skills/site-capture/scripts/learning_layer_v29_audit_based.py`,
69 proposals from 56 curated clients V26 — pre-categorized for Mathis review).
V30 is data-driven: consumes Reality Layer snapshots + Experiment outcomes and
performs Bayesian updates on the V3.3 doctrine priors.

Both tracks coexist; this package only owns the V30 implementation. V29
remains in `skills/` until the future cleanup sprint promotes it too.
"""
from __future__ import annotations

from growthcro.learning.v30_data_driven import (
    BayesianBetaPosterior,
    compute_data_driven_proposals,
    run_v30_cycle,
)

__all__ = (
    "BayesianBetaPosterior",
    "compute_data_driven_proposals",
    "run_v30_cycle",
)
