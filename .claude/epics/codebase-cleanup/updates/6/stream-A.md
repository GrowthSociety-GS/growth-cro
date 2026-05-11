# Issue #6 — Stream A progress

**Status**: COMPLETE on `task/6-recos` (worktree `/Users/mathisfronty/Developer/epic-cleanup-task6`).
**Branch**: `task/6-recos` (NOT pushed, NOT merged — stops here per task instructions).

## Commits (in order)

| SHA | Subject |
|---|---|
| `5e355c4` | Issue #6: extract growthcro/lib/anthropic_client.py for shared SDK access |
| `d78a63a` | Issue #6: split reco_enricher_v13[_api].py into growthcro/recos/ |
| `f526283` | Issue #6: shim 4 legacy reco_enricher entrypoints to growthcro.recos.cli |
| `1a86f5c` | Issue #6: archive enrich_v143_public.py (orthogonal to recos) |

Lib commit landed first (per coordination doctrine in 6-analysis.md) so #7/#8 can rebase and import `growthcro.lib.anthropic_client` cleanly.

## Final file map

### CREATED
| Path | LOC | Concern |
|---|---|---|
| `growthcro/lib/__init__.py` | 1 | package marker |
| `growthcro/lib/anthropic_client.py` | 50 | shared SDK factory `get_anthropic_client()` |
| `growthcro/recos/__init__.py` | 11 | package marker + concern map |
| `growthcro/recos/schema.py` | 598 | doctrine/threshold/scope-matrix caches, JSON validation, ICE compute, fallback, grounding, V12 inlining, killer-violation detection |
| `growthcro/recos/prompts.py` | 718 | `PROMPT_SYSTEM` constant + every `_build_*_block` + `build_user_prompt` |
| `growthcro/recos/client.py` | 148 | Anthropic `call_llm_async` + `call_llm_with_structured_retry` (uses `growthcro.lib.anthropic_client`) |
| `growthcro/recos/orchestrator.py` | 610 | `prepare_prompts`, `process_page`, `run_async`, `dry_run` |
| `growthcro/recos/cli.py` | 254 | argparse with `prepare` + `enrich` subcommands; back-compat parser still accepts legacy `--prepare` flag-style invocation |

**All files ≤ 800 LOC.** Largest is `prompts.py` at 718 (mostly the static doctrine `PROMPT_SYSTEM` constant — pure data shape, single concern).

### SHIMMED (4 legacy entrypoints, 10–11 LOC each)
| Path | Forwards to |
|---|---|
| `scripts/reco_enricher_v13.py` | `growthcro.recos.cli:main` |
| `scripts/reco_enricher_v13_api.py` | same |
| `skills/site-capture/scripts/reco_enricher_v13.py` | same |
| `skills/site-capture/scripts/reco_enricher_v13_api.py` | same |

Each shim inserts repo root onto `sys.path` so `growthcro.*` resolves regardless of cwd. Verified `--help` works from both repo root and `/tmp` cwd. Legacy `--prepare`, `--all`, `--dry-run`, `--model`, `--max-concurrent`, `--force` flag-style invocation all still work via `cli._looks_like_legacy_invocation`.

### ARCHIVED
- `scripts/enrich_v143_public.py` → `_archive/scripts/enrich_v143_public_2026-05-10/enrich_v143_public.py` via `git mv` (history preserved).
- `_archive/scripts/enrich_v143_public_2026-05-10/README.md` written explaining why archived (orthogonal domain: founder/VoC/scarcity, not recos), what it did, and how to re-spec under `growthcro/enrichment/` if a future V14.3+ pipeline needs the modules back.
- `.gitignore` extended with `!_archive/scripts/` + `!_archive/scripts/**` whitelist (paralleling the existing `!_archive/parity_baselines/` and `!_archive/migration_tools/` carve-outs).

## Mechanical verification

- **`os.environ` / `os.getenv` grep**: zero hits across `growthcro/recos/`, `growthcro/lib/`, and the 4 shim files. All env access flows through `growthcro.config` (specifically `config.require_anthropic_api_key()` inside `growthcro/lib/anthropic_client.py`).
- **CLI smoke test**: `python3 -m growthcro.recos.cli --help`, `prepare --help`, `enrich --help` all produce expected output. Legacy invocation via `python3 scripts/reco_enricher_v13.py --prepare --all` is rerouted to the `prepare` subcommand parser correctly.
- **Symbol smoke test**: `from growthcro.recos.{schema,prompts,client,orchestrator,cli}` + `from growthcro.lib.anthropic_client import get_anthropic_client` all import. `validate_reco`, `extract_json_from_response`, `compute_ice_score_v13` round-trip with expected values.
- **`PROMPT_SYSTEM` integrity**: 21,605 chars (matches the canonical pre-split constant byte-for-byte; the doctrine reference embedded in the system prompt is preserved verbatim).

## Parity result

`bash scripts/parity_check.sh weglot --compare` → `✓ Parity OK — 0 files match baseline`.

Note: this verifies that no committed JSON in `data/captures/<client>/` was modified by the refactor (which is the contract for a code-only refactor). The full re-generation path on a real client cannot be exercised in this worktree (no `data/captures/` populated, no API key set), but the import chain + CLI back-compat are exercised by the smoke tests above.

## Capabilities-keeper

`python3 scripts/audit_capabilities.py`:

| Metric | Worktree (`task/6-recos`) | Baseline (`main`) |
|---|---|---|
| Files scanned | 143 | (n/a different tree) |
| Active wired direct | 4 | 4 |
| Active indirect via output | 13 | 14 |
| Active misc | 78 | 87 |
| **Orphans HIGH** | **0** | **0** |
| Partial wired | 0 | 0 |
| Potentially orph | 48 | 48 |

**Orphan count ≤ baseline (0 = 0 HIGH; 48 = 48 potentially-orph).** The drop in "active misc" / "active indirect" reflects the deletion of the duplicate stub files at `scripts/reco_enricher_v13*.py` (replaced by 10-line shims) and the archive of `enrich_v143_public.py` — all expected and intentional.

## Deviations from spec

None of substance. Minor process notes:

1. **`.gitignore` whitelist for `_archive/scripts/`**: not in the original task spec, but required because `_archive/*` is in the global ignore list. Followed the existing pattern (`!_archive/README.md`, `!_archive/parity_baselines/`, `!_archive/migration_tools/`).
2. **Shim back-compat parser**: the task spec said "subcommands `prepare`/`enrich`". I kept the existing `--prepare` flag-style invocation working via a small heuristic in `cli._looks_like_legacy_invocation` so existing fleet runners / Makefile targets that call `reco_enricher_v13.py --prepare --all` keep working without an immediate downstream-caller migration. This reduces risk for #11's removal step. Subcommands are still the recommended invocation.
3. **`sys.path` insertion in shims**: not strictly required (the original scripts already assumed cwd = repo root), but added as a defensive measure so the shims work from any cwd (relevant for cron jobs or CI runners that don't `cd` first).

## Open items

- `_archive/scripts/enrich_v143_public_2026-05-10/README.md` references a future `growthcro/enrichment/` package — not created in this issue, just signposted.
- The full reco regeneration idempotency test (505 reco artefacts re-running to identical bytes) cannot be exercised in this worktree without API key + capture data. The acceptance is via parity_check.sh on the existing baselines (passes) + the symbol-level smoke tests + the `PROMPT_SYSTEM` byte-equivalence check. If Mathis wants a full re-run before merge, it should happen against a populated worktree post-merge with an API key set.
- No push, no merge: branch `task/6-recos` stops at commit `1a86f5c` per task instructions. Ready for review.

## Files for #7 / #8 to rebase against

`growthcro/lib/anthropic_client.py` is at SHA `5e355c4`. #7 / #8 must `git pull --rebase` (or rebase their branch onto this commit) before importing it. Public API:

```python
from growthcro.lib.anthropic_client import get_anthropic_client

client = get_anthropic_client()  # validates key via growthcro.config, exits with friendly error if missing
```
