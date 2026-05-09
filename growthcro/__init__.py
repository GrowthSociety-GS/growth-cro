"""GrowthCRO — top-level package.

Layered submodules following the conceptual pipeline:
    config       — single env boundary
    lib          — shared utilities
    capture      — site capture (browser orchestration)
    perception   — DOM + vision perception
    scoring      — pillars, page-type, criteria
    recos        — reco enrichment
    api          — FastAPI server
    cli          — entrypoints

This file stays empty on purpose; importing the package has no side effect.
"""
