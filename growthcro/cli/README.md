# growthcro.cli

Top-level user-facing CLIs. One subcommand per file.
Were 3 root-level `.py` shims before the #9 reorganization.

## Modules
- `add_client.py` — register a new client in `data/clients_database.json`, run discovery.
- `capture_full.py` — orchestrate stages 1-4 (ghost → native → perception → intent).
- `enrich_client.py` — full audit + recos pipeline for an existing client. Includes pre-flight liveness check (`check_liveness`) reused by `capture_full`.

## Entrypoints
```bash
python -m growthcro.cli.add_client     <label> <url> [<business_type>]
python -m growthcro.cli.capture_full   <url> <label> <business_type> [--cloud --page-type <pt>]
python -m growthcro.cli.enrich_client  <label> [--page <page>] [--dry-run]
```

## Imports from
- `growthcro.config`, `growthcro.capture.*`, `growthcro.perception.cli`, `growthcro.scoring.cli`, `growthcro.recos.cli`.

## Imported by
- Sub-agents under `.claude/agents/capture-worker.md` + `reco-enricher.md`.
