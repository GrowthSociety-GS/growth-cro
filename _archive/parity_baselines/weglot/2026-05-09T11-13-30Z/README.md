# Parity baseline — `weglot` — 2026-05-09T11-13-30Z

- Files snapshotted: 0
- Mask: keys matching `timestamp|generated_at|mtime|run_id|uuid|...` scrubbed at every depth.
- Encoding: `jq -S` (sorted keys), UTF-8.
- Compare command: `bash scripts/parity_check.sh weglot --compare`

## Stage coverage
- `capture.json`: 0
- `spatial_v9.json`: 0
- `perception_v13.json`: 0
- `client_intent.json`: 0
- `score_hero.json`: 0
- `score_psycho.json`: 0
- `score_persuasion.json`: 0
- `score_coherence.json`: 0
- `score_utility_banner.json`: 0
- `score_specific_criteria.json`: 0
- `score_page_type.json`: 0
- `recos_v13_prompts.json`: 0
- `recos_v13_final.json`: 0
- `recos_enriched.json`: 0


## Notes
If `Files snapshotted` is 0, the client has no `data/captures/weglot/` outputs
on disk at the time of baseline. The parity contract still applies: any future
run that produces stage files for this client must reproduce identical scrubbed
JSON when re-run on the same code+inputs. The cleanup epic does not regenerate
data; baseline locks the *output shape* the pipeline currently emits.
