# growthcro.perception

DBSCAN clustering + role detection on `spatial_v9.json` → `perception_v13.json`.
Bridges raw bbox geometry to semantic component types (HERO, CTA_PRIMARY, PROOF_STRIP, …).

## Modules
- `cli.py` — argparse entry (single page or `--all`).
- `heuristics.py` — DBSCAN params + cluster scoring.
- `vision.py` — screenshot-aware role refinement.
- `intent.py` — page-type-specific intent overlay.
- `persist.py` — `process_page` orchestrator (flatten → noise_score → cluster → roles → write).

## Entrypoints
```bash
python -m growthcro.perception.cli --client <label> --page <page>
python -m growthcro.perception.cli --all
```

## Imports from
- `growthcro.config`.
- `sklearn` (DBSCAN), `numpy`.

## Imported by
- `growthcro.cli.capture_full` (stage 3).
- `growthcro.recos.orchestrator` (reads `perception_v13.json`).
- `scripts/client_context.py` (router).
