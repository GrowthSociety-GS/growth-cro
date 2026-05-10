# growthcro

Top-level Python package for the GrowthCRO audit + recommendation pipeline.
Layered submodules mirror the conceptual flow: capture → perception → scoring → recos.

## Layout
- `config.py` — single env boundary (FR-3). Every other module reads `.env` only via `growthcro.config.config`.
- `lib/` — shared utilities (Anthropic client, retries, JSON I/O).
- `capture/` — DOM + screenshot acquisition (Playwright, Browserless, urllib fallback).
- `perception/` — DBSCAN clustering + spatial role detection from `spatial_v9.json`.
- `scoring/` — 6 pillars + page-type-specific criteria (regex + heuristic + LLM-review fallback).
- `recos/` — prompt assembly, Sonnet calls, persistence (split from `reco_enricher_v13`).
- `research/` — site intelligence (brand identity, content discovery).
- `api/` — FastAPI server (was `api_server.py` at root).
- `cli/` — top-level CLIs (`add_client`, `capture_full`, `enrich_client`).
- `gsg_lp/` — frozen legacy GSG LP lab (kept inside the package post-#8 split).

## Imports from
- Standard library + `anthropic` SDK + `playwright` (capture only).

## Imported by
- `moteur_gsg/`, `moteur_multi_judge/`, `skills/site-capture/scripts/`, sub-agents under `.claude/agents/`.

## Common entrypoints
```bash
python -m growthcro.cli.capture_full <url> <label> <business_type>
python -m growthcro.scoring.cli {specific|ux} <label> <page>
python -m growthcro.recos.cli {prepare|enrich} --client <label>
python -m growthcro.api.server
```
