"""GrowthCRO Experiment Engine — V27 promoted to growthcro/.

Issue #23. Single concern: turn a reco + reality data into an A/B test
spec, persist it, and import outcomes when the experiment ends.

ZERO auto-trigger. The runner produces "experiment proposals" that Mathis
must manually validate + launch. Live A/B traffic-split happens in the
client's own platform (Optimizely, VWO, Convert, GTM, etc.) — this engine
just emits the spec.

Public API:
    from growthcro.experiment import (
        compute_sample_size,
        build_experiment_spec,
        propose_experiments,
        record_experiment,
        import_outcome,
    )

Module layout:
- engine.py   — sample-size calculator + spec builder (reuses V27 logic).
- runner.py   — generates experiment proposals from a set of recos + reality
                snapshots. Output: data/experiments/<client>/<exp_id>.json
                with `status="proposed"`. No traffic split.
- recorder.py — indexes all proposals across clients, exposes a query API
                + outcome importer. Output:
                data/experiments/_index/experiments_index.json
                (regen-able from the per-experiment files).
"""
from __future__ import annotations

from growthcro.experiment.engine import (
    DEFAULT_GUARDRAILS,
    build_experiment_spec,
    compute_sample_size,
    estimate_duration_days,
    select_guardrails,
)
from growthcro.experiment.recorder import (
    import_outcome,
    list_experiments,
    rebuild_index,
    record_experiment,
)
from growthcro.experiment.runner import (
    AB_TYPES,
    propose_experiments,
)

__all__ = (
    "DEFAULT_GUARDRAILS",
    "AB_TYPES",
    "build_experiment_spec",
    "compute_sample_size",
    "estimate_duration_days",
    "select_guardrails",
    "propose_experiments",
    "record_experiment",
    "list_experiments",
    "rebuild_index",
    "import_outcome",
)
