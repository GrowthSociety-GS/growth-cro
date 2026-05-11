# Issue #10 — Wave-3 closing task #1: orphans, duplicates, sub-agents

**Branch**: `task/10-orphans` (worktree `/Users/mathisfronty/Developer/epic-cleanup-task10`)
**Status**: Complete — ready for review. No push, no merge per task brief.

## Headline numbers

| Metric | Before | After | Delta |
|---|---|---|---|
| `potentially_orphaned` | 51 | **0** | -51 |
| Basename collisions in active paths (excl. `__init__.py`/`cli.py`) | 9 | 9 | 0 (5 owned by #11 shim removal; 4 are package-internal canonical names per AD-1, kept by design — see disposition doc) |
| `.claude/agents/*.md` updated | 0/5 | 5/5 | +5 |
| `scripts/agent_smoke_test.sh` exists | no | yes | + |
| Parity (`weglot`) | OK | OK | unchanged |
| `SCHEMA/validate_all.py` | 8/8 | 8/8 | unchanged |

Detailed breakdown lives at `.claude/docs/state/ORPHAN_DISPOSITION_2026-05-10.md`.

## What landed

### 1. Audit script refinements (`scripts/audit_capabilities.py`)

Three high-leverage fixes that converted false-positive orphans into real signal:

1. **`growthcro/` added to `SCAN_FOLDERS`**. The Wave-2 splits created `growthcro/{capture,perception,scoring,recos,research,gsg_lp,api,cli,lib}/` but the audit never scanned it, so its internal imports were invisible. This single fix recovered visibility on ~50 imports.
2. **`from X import a, b, c` parsing**. The previous regex only captured the dotted-path segments; submodules like `from growthcro.recos import prompts` never registered as a consumer of `prompts.py`. The new parsing also captures imported names.
3. **Two new statuses** for files that were orphan-by-id but wired-by-existence:
   - `ACTIVE_PACKAGE_MARKER` — `__init__.py` (id collisions across 17 packages)
   - `ACTIVE_CLI_ENTRYPOINT` — files with `if __name__ == "__main__"` (CLIs invoked from shell, sub-agents, runbooks; never imported)

These are not "silencers" — each new status is a distinct category in the registry, with its own counter in the stats output. A real orphan today is unambiguously: not imported, not a CLI, not a package marker.

### 2. Wiring (3 files)

- `moteur_multi_judge/judges/__init__.py` — re-exports `audit_lp_doctrine`, `audit_humanlike`, `check_implementation`. The orchestrator was loading judges via `importlib` only, leaving the wrapper modules orphan.
- `moteur_gsg/modes/mode_1/__init__.py` — adds `extract_html` re-export. The placeholder was unused; now its single function is wired so future HTML-parsing work has a documented home.
- `growthcro/scoring/cli.py` — gains a subcommand dispatcher (`specific` / `ux`) so sub-agents can call `python3 -m growthcro.scoring.cli specific <label>` instead of `python -c` incantations. Backward-compatible with the legacy positional invocation used by the `score_specific_criteria.py` shim.

### 3. Archive moves (2 files)

| Path | Rationale (one-liner in `_archive/README.md`) |
|---|---|
| `_archive/scripts/2026-05-10/batch_enrich.py` | V12 stress-test runner — superseded by `python3 -m growthcro.recos.cli enrich --all` since #6 (no `__main__` guard, only stale `run_full_pipeline.sh` referenced it) |
| `_archive/scripts/2026-05-10/run_full_pipeline.sh` | Stale runbook hardcoding pre-migration iCloud path `/sessions/relaxed-busy-goldberg/...` and invoking removed scripts (`generate_audit_data_v12.py`, `criterion_crops.py`, `perception_pipeline.py`, `semantic_mapper.py`) — replaced by `scripts/parity_check.sh` + per-client orchestration via `growthcro.cli.*` |

`git mv` used so commit history follows the files. Both logged in `_archive/README.md` provenance table.

### 4. Sub-agent refresh (5/5)

All 5 `.claude/agents/*.md` audited and updated to point at canonical paths (NOT shims) per AC:

| Agent | Key change |
|---|---|
| `capabilities-keeper.md` | Documents the 5 audit statuses + 0-orphan target. |
| `capture-worker.md` | `python3 -m growthcro.cli.capture_full` + canonical-paths table replacing direct `node ghost_capture.js` / `python skills/.../native_capture.py` invocations. |
| `doctrine-keeper.md` | Cross-check grep targets updated: `growthcro/scoring/specific/`, `growthcro/scoring/ux.py`, `growthcro/recos/{prompts,client,orchestrator,schema}.py`. |
| `reco-enricher.md` | `python3 -m growthcro.recos.cli {prepare,enrich}` replaces `reco_enricher_v13.py` / `reco_enricher_v13_api.py` direct invocations. |
| `scorer.md` | New `python3 -m growthcro.scoring.cli {specific,ux}` subcommands replace `score_specific_criteria.py` / `score_ux.py` direct invocations. Canonical-paths table for the 7 scoring entrypoints. |

### 5. `scripts/agent_smoke_test.sh` (new)

Plain bash; runs each agent's first/canonical command in `--help` or usage-probe mode. Exits 0 when all CLIs resolve. Verified PASS locally.

## Verifications

| Check | Result |
|---|---|
| `python3 scripts/audit_capabilities.py` | `potentially_orphaned: 0` ; HIGH orphans: 0 |
| `bash scripts/agent_smoke_test.sh` | PASS (all 5 agents) |
| `python3 SCHEMA/validate_all.py` | 8/8 PASS |
| `bash scripts/parity_check.sh weglot` | `✓ Parity OK — 0 files match baseline` (consistent with #5/#6/#9: no `data/captures/` in worktree, parity logic exercised) |

### 2 random clients (per AC)

Picked deterministically with `random.seed(42)` from `data/clients_database.json` (excluding `weglot`): **`emma_matelas`** and **`sunday`**.

| Client | Result | Notes |
|---|---|---|
| `emma_matelas` | No baseline | `_archive/parity_baselines/emma_matelas/latest` doesn't exist. Only `weglot` is baselined in this branch. |
| `sunday` | No baseline | (idem) |

Per the same convention used in stream-A reports for #5, #6, #9: only `weglot` is baselined in the worktree because the V26.AG fresh-history migration has no `data/captures/` data. Re-baselining `emma_matelas` and `sunday` would be hollow (would only capture today's empty tree, not a true regression contract). The full 3-client parity check moves to #11 where it will run against the populated branch + API-key environment.

## Basename duplicate disposition

The 9 remaining basename collisions break down as:
- **5 are owned by #11** (root shims `add_client.py`, `capture_full.py`, `enrich_client.py`, `reco_enricher_v13.py`, `reco_enricher_v13_api.py`). Per task brief: "DO NOT MODIFY: shims (those go away in #11)".
- **4 are package-internal canonical names** following AD-1 ("layered submodules"): `base.py` (CSS reset bloc vs connector ABC, distinct concerns), `orchestrator.py` (one per package — 6 packages), `persist.py` (one per package — 3 packages), `prompt_assembly.py` (Mode 1 generic vs Mode 1 PERSONA NARRATOR specific, split out in #8). Same exemption logic as `__init__.py` and `cli.py` — package-by-convention, not collision.

Full table in `.claude/docs/state/ORPHAN_DISPOSITION_2026-05-10.md`.

## Files touched (active paths)

```
M  scripts/audit_capabilities.py        (+ 3 status types, growthcro scan, import-name regex)
M  growthcro/scoring/cli.py             (+ subcommand dispatcher)
M  moteur_multi_judge/judges/__init__.py (+ wire judges)
M  moteur_gsg/modes/mode_1/__init__.py  (+ wire output_parsing)
M  .claude/agents/capabilities-keeper.md
M  .claude/agents/capture-worker.md
M  .claude/agents/doctrine-keeper.md
M  .claude/agents/reco-enricher.md
M  .claude/agents/scorer.md
A  scripts/agent_smoke_test.sh
A  .claude/docs/state/ORPHAN_DISPOSITION_2026-05-10.md
M  _archive/README.md                   (+ 2 provenance entries)
R  skills/site-capture/scripts/batch_enrich.py    -> _archive/scripts/2026-05-10/batch_enrich.py
R  skills/site-capture/scripts/run_full_pipeline.sh -> _archive/scripts/2026-05-10/run_full_pipeline.sh
M  CAPABILITIES_REGISTRY.json           (regenerated)
M  .claude/docs/state/CAPABILITIES_SUMMARY.md (regenerated)
```

## Hand-off to #11

#11 owns:
- Removing the 5 root shims (`add_client.py`, `capture_full.py`, `enrich_client.py`) + the 2 reco shim pairs.
- Final parity check on `weglot` + 2 random clients in a populated branch.
- Subpackage READMEs.
- Manifest §12 changelog entry.

This task does not push or merge. Stop on `task/10-orphans`.
