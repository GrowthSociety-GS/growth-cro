# growthcro.lib

Cross-cutting utilities shared by every other `growthcro/` submodule (FR-6).
No business logic — only adapters, retries, serialization helpers.

## Modules
- `anthropic_client.py` — single Anthropic SDK wrapper (Sonnet/Haiku). Pulls `ANTHROPIC_API_KEY` via `growthcro.config`. Used by `recos/`, `scoring/` (LLM-review). (`gsg_lp/` archived 2026-05-12, Issue #37.)

## Imports from
- `growthcro.config` (env access).
- `anthropic` SDK.

## Imported by
- `growthcro.recos.client`
- `growthcro.scoring.specific.*` (LLM-review detectors)
- `growthcro.cli.enrich_client`
- ~~`growthcro.gsg_lp.repair_loop`~~ — archived 2026-05-12 (Issue #37), see `_archive/growthcro_gsg_lp_2026-05-12_legacy_island/`
