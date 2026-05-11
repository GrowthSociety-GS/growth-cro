# growthcro.recos

Turns scored captures into prioritized recommendations.
Was `reco_enricher_v13.py` (1,690 LOC) + `reco_enricher_v13_api.py` (743 LOC) before the #6 split.

## Modules
- `cli.py` — subcommand dispatcher: `prepare` (assemble prompts) | `enrich` (call Sonnet).
- `prompts.py` — prompt assembly per criterion.
- `client.py` — Anthropic API client (max-concurrent, dry-run, force).
- `persist.py` — `recos_v13_prompts.json` + `recos_v13_final.json` writers.
- `orchestrator.py` — end-to-end pipeline (loads `perception_v13.json` + score outputs, calls API, persists).
- `schema.py` — `compute_recos_brutes_from_scores` doctrine bridge.

## Entrypoints
```bash
python -m growthcro.recos.cli prepare --client <label> [--page <page>]
python -m growthcro.recos.cli enrich  --client <label> --model claude-sonnet-4-6 --max-concurrent 5
```

## Imports from
- `growthcro.config`, `growthcro.lib.anthropic_client`.

## Imported by
- `growthcro.cli.enrich_client`.
- `run_enricher.sh`.
