# growthcro.scoring

Scores a `(client, page_type)` pair against the V3.2.1 doctrine.
6 pillars (hero/persuasion/ux/coherence/psycho/tech) + page-type-specific criteria.

## Modules
- `cli.py` — subcommand dispatcher: `specific` | `ux`.
- `pillars.py` — shared scoring primitives across the 6 pillars.
- `specific/` — page-type-specific detectors (35+ regex/heuristic/LLM-review hybrids).
- `ux.py` — UX pillar scorer (was `score_ux.py`).
- `persist.py` — `load_capture`, `score_page_type_specific`, `write_specific_score`.

## Entrypoints
```bash
python -m growthcro.scoring.cli specific <label> [page_type]
python -m growthcro.scoring.cli ux <label> [page_type]
```

## Imports from
- `growthcro.config` (LLM-review fallback API key).
- `growthcro.lib.anthropic_client` (Haiku review for ambiguous detectors).
- `playbook/*.json` (read-only doctrine).

## Imported by
- `skills/site-capture/scripts/score_page_type.py` (orchestrator across all pillars).
- `skills/site-capture/scripts/batch_rescore.py`.
