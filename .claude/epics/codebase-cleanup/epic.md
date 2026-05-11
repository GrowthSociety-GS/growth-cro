---
name: codebase-cleanup
status: completed
created: 2026-05-08T11:14:20Z
updated: 2026-05-11T07:16:17Z
progress: 100%
prd: .claude/prds/codebase-cleanup.md
github: https://github.com/GrowthSociety-GS/growth-cro/issues/1
---

# Epic: codebase-cleanup

## Overview

Refactor the GrowthCRO codebase from "organic V21→V26 brownfield" to a tree where each capability lives in exactly one canonical module, no file exceeds 800 LOC, env access goes through one config boundary, archives live outside active paths, and the capabilities registry reports zero orphans. The cleanup is **structural** (moves, splits, dedup) — no behaviour changes, no doctrine changes, no schema changes. Pipeline output parity for at least one canonical client is the regression trip-wire.

## Architecture Decisions

### AD-1 — One package, layered submodules
Adopt a `growthcro/` top-level Python package with explicit layers. The conceptual pipeline (capture → perception → scoring → recos → dashboard) becomes the directory structure:

```
growthcro/
├── config.py               # FR-3 — single env boundary
├── lib/                    # FR-6 — shared utilities (anthropic_client, json_io, retries)
├── capture/                # ghost_capture, native_capture, playwright wrappers
├── perception/             # perception_v13 (split), spatial, intent_detector
├── scoring/                # pillars, page_type, specific_criteria, ux
├── recos/                  # enricher (split: prompt/api/persist/orchestrate)
├── api/                    # FastAPI server (was api_server.py at root)
└── cli/                    # add_client, capture_full, enrich_client (was at root)
```

`moteur_gsg/` and `moteur_multi_judge/` keep their identity (they're the GSG and judging engines respectively); their internal god files split following the same separation-of-concerns axes.

### AD-2 — Migration via shim wrappers
For every script with external callers (sub-agents, shell scripts, docker-compose), keep the old path as a **shim** that imports and forwards to the new location. Shims are removed in the final task once all callers are migrated. This keeps each move independently mergeable.

### AD-3 — Parity over tests
We do not add unit tests in this epic (out of scope per PRD). The regression contract is `scripts/parity_check.sh`: capture → score → reco for one canonical client (`weglot`), diff JSON outputs, fail on any byte-level delta in semantically meaningful fields (numeric scores, reco IDs, payload structure — not timestamps).

### AD-4 — Splitting axis = concerns, not lines
A 1,690-line file is not split into "two 845-line files". It's split along the four concerns that bloated it:
1. **Prompt assembly** (data → string)
2. **API client** (string → API call → response)
3. **Persistence** (response → disk)
4. **Orchestration** (loop, batch, CLI)

If after this split a single concern still exceeds 800 LOC, it's broken further by data-shape (e.g. one prompt-assembly file per persona).

### AD-5 — Archives are append-only
Anything moved out of active paths goes to `_archive/<area>/<date>/` with the original sub-tree preserved. `_archive/` is never deleted; it's where history lives outside git. (Git history is also preserved via `git mv`, but `_archive/` provides a directory-level browse.)

### AD-6 — Capabilities-keeper is the gate
Every task ends with `python3 scripts/audit_capabilities.py`. The orphan count must monotonically decrease (or stay equal in the case of pure splits). A task that increases the count fails review.

### AD-7 — Doctrine code = "1 fichier = 1 concern", LOC are a signal
The cleanliness rule is conceptual (single concern), not metric-based. The linter only **fails** on rules it can verify mechanically (>800 LOC, env-outside-config, archive-in-active, basename-duplicate). Files between 300–800 LOC are surfaced as **info**; reviewer or LLM affirms "single concern" or refactors. Mixed-concern detection is heuristic (cross-domain imports, divergent function-name prefixes, multiple unrelated top-level classes) and only emits **warnings**, never failures — the human/LLM judgement remains in the loop. The 8 canonical concern axes (prompt assembly · API client · persistence · orchestration · CLI · config · validation · I/O serialization) are the vocabulary used to classify.

### AD-8 — Doctrine evolves via explicit commits, never silently
When a future Claude session discovers a new anti-pattern that should be codified, it produces a separate commit `docs(doctrine): code +<rule>` with a concrete example. No silent edits. This keeps the doctrine auditable through `git log docs/doctrine/CODE_DOCTRINE.md` and forces the rule-author to articulate the motivating example.

### AD-9 — Unified capability-based naming; git is the only versioning
The codebase carries legacy iCloud-era version stamps (`_v13`, `_v272c`, `V26AE`, `V143`, `gsg-…-v27.2-f`, `GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md`, etc.) that exist because there was no real VCS pre-migration. With GitHub now the source of truth (commit `5fb582f` baseline), the cleanup epic adopts:

1. **Files** are named by *capability*, never by version. `perception_v13.py` becomes `perception/heuristics.py`; `reco_enricher_v13.py` becomes `recos/orchestrator.py`. No `_vNN` suffix anywhere in active paths.
2. **Module-level `version=` constants** in dataclasses and contracts are dropped. The git SHA + tag identifies the version of any contract; the code carries only a stable capability id (`"gsg-page-plan"`, not `"gsg-page-plan-v27.2"`).
3. **Architecture/spec docs** collapse from per-version snapshots (`GSG_RECONSTRUCTION_SPEC_V27_2_*.md`, `AUDIT_TOTAL_V26AE_*.md`) into living documents in `.claude/docs/architecture/<capability>.md`. History lives in `git log`, not in filenames.
4. **Data dirs** stop carrying version stamps: `_briefs_v15/`, `_briefs_v2/`, `weglot_lp_listicle_v272c_true/` move under `briefs/<client>/<iso>_<page>/` and `pipeline_runs/<client>/<iso>_<page>/`.
5. **Webapp release versioning** = git tags (semver `vX.Y.Z` or date-tags `2026.05.0`). Filenames never carry a version.

The parity contract is therefore **functional**, not nominal: `parity_check.sh weglot --compare` enforces byte-equal scrubbed JSON outputs (scores, reco IDs, payload structure), but is indifferent to filename or `version=` field renames in the producing code. Any task that renames a file or strips a `_vNN` field updates the parity baseline once, then re-locks it; the contract follows the *outputs*, not the *paths*.

Anti-rule for new code in this epic: **never introduce a `V##` token in a filename, classname, function name, or `version=` string**. Existing markers in untouched legacy code can stay until that file is split (cf. AD-1) — touching a `_v13` file means renaming it.

## Technical Approach

### Backend Services
- **Config**: `growthcro/config.py` exposes `Config()` singleton with typed accessors. Reads `.env` once at startup; raises `MissingConfigError(var, hint)` for unset required vars. `.env.example` regenerated from the config schema.
- **Capture**: god file `ghost_capture_cloud.py` (1,122 LOC) splits into `capture/ghost.py` (browser orchestration), `capture/cloud.py` (Apify/Browserless adapter), `capture/dom.py` (DOM serialization).
- **Perception**: `perception_v13.py` (1,134 LOC) splits into `perception/heuristics.py`, `perception/vision.py`, `perception/intent.py`, `perception/persist.py`.
- **Scoring**: `score_specific_criteria.py` (1,101) and `score_ux.py` (710) refactor against `playbook/*.json` boundaries — one module per pillar where the pillar shape warrants it.
- **Recos**: `reco_enricher_v13.py` + `reco_enricher_v13_api.py` collapse into `recos/{prompts,client,persist,orchestrator}.py`. Single canonical entrypoint.

### Frontend Components
Out of scope. The dashboard under `deliverables/` is untouched.

### Infrastructure
- `Dockerfile` and `docker-compose.yml` updated to use new entrypoints (e.g. `python -m growthcro.api` instead of `python api_server.py`).
- No new images, no new services, no new deps.
- `.gitignore` already correct (verified: `.env`, `__pycache__/`, `*.key`).

## Implementation Strategy

### Phasing — three waves

**Wave 1 — Inventory & guard-rails (must complete first, fully serial)**
Establish what exists, build the parity check, freeze the doctrine-adjacent paths.

**Wave 2 — Structural moves (mostly parallel, conflict-aware)**
Per-area refactors. Each touches a disjoint sub-tree and can run in parallel. The capabilities-keeper agent runs after each.

**Wave 3 — Wire-up & cleanup (mostly serial)**
Update sub-agent definitions, remove shims, regenerate manifests, final parity & validate.

### Risk mitigation
- **Risk**: A split changes import-time behaviour (e.g. a god file ran a side effect at import). Mitigation: parity check runs end-to-end after each split.
- **Risk**: A sub-agent breaks on a renamed entrypoint. Mitigation: shim wrappers in Wave 2; sub-agent audit in Wave 3 before shim removal.
- **Risk**: Mathis disagrees with a proposed split axis mid-execution. Mitigation: each Wave-2 task posts its proposed split (file-by-file map) as a comment on its issue **before** moving anything. Mathis approves, then the agent proceeds.
- **Risk**: `scripts/audit_capabilities.py` itself has bugs that hide regressions. Mitigation: Task 1 includes a sanity audit of `audit_capabilities.py`'s heuristics.

### Rollback plan
Every task is one commit on `epic/codebase-cleanup`. Rollback = `git revert <sha>`. The branch is never merged to main until Mathis runs the full parity script and approves explicitly.

## Task Breakdown Preview

Aiming for ≤10 tasks per CCPM convention. Order encodes the dependency graph; `parallel: true` tasks within the same wave run concurrently in worktrees.

1. **Inventory & parity instrumentation** — write `scripts/parity_check.sh`; verify `audit_capabilities.py`, `state.py`, `SCHEMA/validate_all.py` all green; snapshot `weglot` outputs as the parity baseline. *[Wave 1, serial]*

2. **Centralize env/config (`growthcro/config.py`)** — create the module, replace all `os.environ`/`os.getenv` calls in active paths with `config.*` accessors, regenerate `.env.example`, raise `MissingConfigError` at startup. *[Wave 1, serial — every other task imports config]*

3. **Move archives out of active paths** — relocate `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` and per-client `_obsolete_pages_2026-04-29/` to `_archive/<area>/<date>/`. Update `audit_capabilities.py` if its scan ranges miss the new layout. *[Wave 2, parallel — touches only archive folders]*

4. **Split capture god files** — `ghost_capture_cloud.py` (1,122) and `native_capture.py` (1,032) split along concern axes; create `growthcro/capture/` package with shims at old paths. *[Wave 2, parallel — capture sub-tree only]*

5. **Split recos god files & dedupe** — collapse `reco_enricher_v13.py` + `reco_enricher_v13_api.py` (1,690 + 743) into `growthcro/recos/{prompts,client,persist,orchestrator}.py`; resolve the cross-tree duplicates between `scripts/` and `skills/site-capture/scripts/`. *[Wave 2, parallel — recos sub-tree only]*

6. **Split perception & scoring god files** — `perception_v13.py` (1,134), `score_specific_criteria.py` (1,101), `score_ux.py` (710) refactored along pillar/concern boundaries; create `growthcro/perception/` and `growthcro/scoring/` packages. *[Wave 2, parallel — perception+scoring sub-tree only]*

7. **Split GSG god files** — `controlled_renderer.py` (1,665), `mode_1_persona_narrator.py` (1,448), `gsg_generate_lp.py` (1,218), `enrich_v143_public.py` (1,339) refactored inside `moteur_gsg/`. Same concern-axis approach. *[Wave 2, parallel — moteur_gsg only]*

8. **Reorganize root-level entrypoints** — move 6 root `.py` files into `growthcro/api/`, `growthcro/cli/`, `growthcro/capture/`. Add shims at root. Update `Dockerfile`, `docker-compose.yml`, `package.json` scripts, `run_enricher.sh`. *[Wave 2, serial — touches root + Docker]*

9. **Wire orphans, kill duplicates, refresh agents** — drive `POTENTIALLY_ORPHANED` to zero (wire or archive); resolve remaining basename duplicates; audit every `.claude/agents/*.md` for stale paths; smoke-test agent commands exist. *[Wave 3, serial]*

10. **Remove shims, regenerate manifests, final parity** — once all sub-agents and external callers updated, delete shim wrappers; regenerate `CAPABILITIES_SUMMARY.md`; add `MANIFEST §12` changelog entry; run final parity check on `weglot` + 2 random clients; update each subpackage `README.md`. *[Wave 3, serial]*

11. **Code doctrine + linter + auto-update loop** — author `docs/doctrine/CODE_DOCTRINE.md` (mono-concern principle, 8 canonical concern axes, hard rules, soft signals, auto-update loop spec); implement `scripts/lint_code_hygiene.py` (rules from PRD FR-10); patch `CLAUDE.md` init step #10 + "Anti-patterns prouvés"; patch `AGENTS.md`; patch every `.claude/agents/*.md` to reference the doctrine and refuse non-compliant emissions; wire the linter summary into `state.py`. *[Wave 3, serial — final task, closes the epic]*

## Dependencies

### External
None. The cleanup is internal refactor — no Notion fetch, no API contract change, no third-party SDK update.

### Internal
- **Doctrine artefacts** (`playbook/`, `SCHEMA/`, `data/clients_database.json`): read-only inputs to parity testing; not modified.
- **Sub-agents** (`.claude/agents/`): Task 9 updates them. Until then, sub-agents may run on shims.
- **Worktree**: `../epic-codebase-cleanup/` (per CCPM convention). Created in Task 1.
- **Capabilities registry**: `CAPABILITIES_REGISTRY.json` regenerated by every task ending; decreasing orphan count is the gate.

### Sequencing constraints
- **Task 1 → all**: parity baseline must exist before any move.
- **Task 2 → 4,5,6,7,8**: all splits import the new `config.py`. Doing it once up-front avoids touching every split twice.
- **Task 3 → 9**: orphan count can only be honestly measured after archives are out of active paths.
- **Tasks 4,5,6,7 parallelizable**: disjoint sub-trees, declared via `conflicts_with` to be safe.
- **Task 9 → 10**: shims can only go away once sub-agents stop pointing at old paths.

## Success Criteria (Technical)

- [ ] `find . -name "*.py" -not -path "*/_archive/*" -not -path "*/__pycache__/*" -not -path "*/node_modules/*" -not -path "*/worktrees/*" | xargs wc -l | awk '$1>800 {c++} END {print c}'` outputs `0`
- [ ] `grep -rE "os\.environ|os\.getenv" --include="*.py" . | grep -v _archive | grep -v __pycache__ | grep -v worktrees | grep -vE "(growthcro/)?config\.py" | wc -l` outputs `0`
- [ ] `python3 scripts/audit_capabilities.py` reports `potentially_orphaned: 0` for active paths
- [ ] `find . -path "*/_archive*" -path "*active*" -o -path "*_obsolete*" 2>/dev/null` finds nothing inside active dirs (`scripts/`, `skills/`, `moteur_*/`, `growthcro/`)
- [ ] `bash scripts/parity_check.sh weglot` exits 0; same for 2 random clients
- [ ] `python3 SCHEMA/validate_all.py` exits 0 pre and post
- [ ] `python3 state.py` reports identical pipeline counts pre/post
- [ ] Each `.claude/agents/*.md` references commands that resolve (smoke test passes)
- [ ] Active LOC reduced from ~69,500 to ≤55,000 (target — accept ≤60,000 if dedup yield is lower than estimated)
- [ ] Active source file count from 175 to ≤140
- [ ] Each subpackage has a 30-line `README.md`
- [ ] `MANIFEST.md §12` has a changelog entry for the cleanup epic
- [ ] `docs/doctrine/CODE_DOCTRINE.md` exists and is referenced from `CLAUDE.md` step #10
- [ ] `scripts/lint_code_hygiene.py` exists, runs <5s on full tree, reports 0 `fail` on the cleaned tree
- [ ] `state.py` final section prints the linter summary
- [ ] Every `.claude/agents/*.md` references `CODE_DOCTRINE.md`

## Estimated Effort

- **Overall timeline**: ~10 working days for a single Claude-Code-driven sprint with Mathis review.
- **Per task** (rough):
  - Tasks 1, 2 (instrumentation, config): 0.5 day each
  - Task 3 (archive moves): 0.5 day (mostly mechanical)
  - Tasks 4–7 (god-file splits): 1.5 days each, parallelizable into ~2 calendar days if 3 worktrees run concurrently
  - Task 8 (root reorg + Docker): 1 day
  - Task 9 (orphans + agents): 1 day
  - Task 10 (shim removal + final): 0.5 day
  - Task 11 (doctrine + linter + agent wiring): 1 day
- **Critical path**: Tasks 1 → 2 → 4 (longest split) → 9 → 10 → 11 ≈ 6–7 days if parallelism is fully exploited.
- **Resources**: 1 main agent (Claude Code) + capabilities-keeper sub-agent at every task end + Mathis review at every Wave boundary (3 review checkpoints total).

## Tasks Created

- [x] #2 Inventory & parity instrumentation (parallel: false, deps: —)
- [x] #3 Centralize env/config in growthcro/config.py (parallel: false, deps: #2)
- [x] #4 Move archives out of active paths (parallel: true, deps: #2)
- [ ] #5 Split capture god files into growthcro/capture/ (parallel: true, deps: #3, conflicts: #9)
- [ ] #6 Split recos god files & dedupe enricher variants (parallel: true, deps: #3)
- [ ] #7 Split perception & scoring god files (parallel: true, deps: #3)
- [ ] #8 Split GSG (moteur_gsg) god files (parallel: true, deps: #3)
- [ ] #9 Reorganize root-level Python entrypoints (parallel: true, deps: #3, #5; conflicts: #5)
- [ ] #10 Wire orphans, kill duplicates, refresh sub-agents (parallel: false, deps: #4, #5, #6, #7, #8, #9)
- [ ] #11 Remove shims, regenerate manifests, final parity (parallel: false, deps: #10)
- [ ] #12 Code doctrine, hygiene linter & auto-update loop (parallel: false, deps: #11)

Total tasks: 11
Parallel tasks: 5 (#4, #5, #6, #7, #8 — disjoint sub-trees within Wave 2; #9 joins after #5 lands)
Sequential tasks: 6 (#2, #3, #9-effective-after-#5, #10, #11, #12)
Estimated total effort: ~95 hours single-threaded (≈ 50–55 hours with Wave-2 parallelism)
Critical path: #2 → #3 → #8 (longest split, XL) → #10 → #11 → #12
