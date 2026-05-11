# growthcro.lib

Cross-cutting utilities shared by every other `growthcro/` submodule (FR-6).
No business logic — only adapters, retries, serialization helpers.

## Modules
- `anthropic_client.py` — single Anthropic SDK wrapper (Sonnet/Haiku). Pulls `ANTHROPIC_API_KEY` via `growthcro.config`. Used by `recos/`, `scoring/` (LLM-review), `gsg_lp/`.

## Imports from
- `growthcro.config` (env access).
- `anthropic` SDK.

## Imported by
- `growthcro.recos.client`
- `growthcro.scoring.specific.*` (LLM-review detectors)
- `growthcro.gsg_lp.repair_loop`
- `growthcro.cli.enrich_client`
