---
name: codebase-cleanup
description: Refactor GrowthCRO codebase for human + LLM readability — kill god files, dedupe scripts, centralize env/config, enforce separation of concerns, retire obsolete artefacts.
status: backlog
created: 2026-05-08T11:14:20Z
---

# PRD: codebase-cleanup

## Executive Summary

The GrowthCRO codebase has organically grown into a state where neither a human reader nor an LLM agent can confidently navigate it. Six 1,000+ line "god files" hold most of the pipeline logic, 20+ basename duplicates exist across `scripts/` vs `skills/site-capture/scripts/` vs `_archive/`, environment variables are read via five different patterns scattered through 30+ files, and obsolete data/scripts (`_obsolete_pages_2026-04-29/`, `_archive_deprecated_2026-04-19/`) live inside *active* directories. This PRD scopes a doctrine-aware cleanup that produces a tree where every file's purpose is obvious from its path, every function fits in a screen, secrets/env are read in exactly one place, and 48 currently "potentially orphaned" files are either wired or removed.

The cleanup must not regress any V26.AG capability — pipeline counts (524 captures, 525 perceptions, 505 recos) stay identical pre/post, and `state.py` keeps reporting green.

## Problem Statement

### Why now

V26.AG just landed (commit `2930580`) and consolidated docs under `.claude/`. That was the *paperwork* cleanup. The *code* underneath is still the iCloud-migrated brownfield from V21 → V26, with every iteration adding a `_v[N+1]` file alongside the previous one rather than replacing it. The consequence:

1. **LLM agents stall** when asked to extend the pipeline because they can't tell which `reco_enricher` is canonical (3 active copies, 1 archived, 1 batch variant).
2. **Mathis loses time** answering "is `scripts/X` or `skills/site-capture/scripts/X` the real one?" on every session.
3. **Sub-agents (`scorer`, `reco-enricher`, `capture-worker`)** were built to wrap god files; their prompts contain hardcoded paths into 1,500-line modules that nobody could re-derive.
4. **Capabilities-keeper** already flags 48 orphaned files; without action this number grows every sprint.
5. **Sprints F–L** in `STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md` will compound the mess if we ship them on top of the current tree.

### What "broken" looks like, concretely

- `ghost_capture_cloud.py` (1,122 LOC) at repo root — should be inside a module
- `reco_enricher_v13.py` (1,690 LOC) — single file holds prompt assembly, API calls, retry logic, output validation, persistence, batch loop
- `controlled_renderer.py` (1,665 LOC), `mode_1_persona_narrator.py` (1,448 LOC) — same pattern in `moteur_gsg/`
- `_archive_deprecated_2026-04-19/` *inside* `skills/site-capture/scripts/` — agents reading the directory pick up archived code as if active
- `os.environ["ANTHROPIC_API_KEY"]` directly in 30+ files; no `config.py` boundary
- `__pycache__/` exists at root despite `.gitignore` (untracked but visually polluting)

## User Stories

### US-1: Mathis asks "where does X happen?"

**As** Mathis, **I want** every pipeline stage to live in exactly one importable module with a one-line purpose docstring, **so that** "where is the scoring done?" answers itself by reading the directory tree.

**Acceptance:**
- `find . -name "*.py" -not -path "*/_archive/*" | xargs grep -l "def main"` returns ≤15 entrypoints (currently 40+)
- Each top-level dir (`moteur_gsg/`, `skills/site-capture/`, `scripts/`) has a `README.md` listing its modules and entry-points
- No file >800 LOC in active code paths; ≤5 files between 500–800 LOC, each justified

### US-2: A sub-agent (`scorer`, `capture-worker`, …) needs to invoke a capability

**As** a Claude Code sub-agent, **I want** to call one canonical entrypoint per capability with a stable CLI signature, **so that** my prompt doesn't need to encode internal file structure.

**Acceptance:**
- `CAPABILITIES_REGISTRY.json` has 0 `POTENTIALLY_ORPHANED` files in active paths
- Every sub-agent definition under `.claude/agents/` references entrypoints that exist and are wired
- A new sub-agent can be written using only `CAPABILITIES_REGISTRY.json` + `docs/state/CAPABILITIES_SUMMARY.md` as reference

### US-3: A new contributor (or LLM cold-start) reads the repo

**As** a fresh reader, **I want** the import graph to mirror the conceptual architecture (capture → perception → scoring → recos → dashboard), **so that** I can predict where new code goes without asking.

**Acceptance:**
- A directory tree printed at depth 2 is self-explanatory: e.g., `moteur_gsg/scoring/pillars.py` not `scripts/batch_rescore.py`
- `MANIFEST §12` references the new structure; old paths flagged as deprecated
- `tree -L 3 -I 'node_modules|_archive|__pycache__|data|deliverables'` fits on one screen

### US-4: Env / secrets handling

**As** the security boundary, **I want** all env/API-key reads funneled through one config module, **so that** rotating a key, adding a new provider, or auditing what's read happens in one diff.

**Acceptance:**
- A single `config.py` (or `growthcro/config.py`) exposes typed accessors: `config.anthropic_api_key()`, `config.apify_token()`, etc.
- `grep -rE "os\.environ|os\.getenv" --include="*.py"` returns only that one file (in active paths)
- `.env.example` lists every variable the config module knows about; nothing else
- Missing-required-env errors are raised at startup with a clear message, not at first API call

### US-5: Doctrine-as-code stays untouched in scope

**As** Mathis (doctrine guardian), **I want** the cleanup to touch *only* code/script organisation, **so that** `playbook/*.json`, `data/`, `deliverables/`, and Notion content are bit-for-bit unchanged.

**Acceptance:**
- `git diff --stat` after migration shows zero changes under `playbook/`, `data/`, `deliverables/`, `SCHEMA/`
- `python3 SCHEMA/validate_all.py` passes pre and post
- `state.py` pipeline counts (capture/perception/intent/score/recos) identical pre/post on the same DB

### US-6: The cleanup must hold over time (anti-regression doctrine)

**As** Mathis, **I want** every future Claude instance that touches the code to *automatically* know and enforce the cleanliness rules — single concern per file, central config, no archives in active paths, no basename duplicates — **so that** the codebase doesn't drift back into V21→V26 brownfield mode after the next 5 sprints.

**Acceptance:**
- A code doctrine document `docs/doctrine/CODE_DOCTRINE.md` exists and codifies the rules with examples (mono-concern principle, the 8 canonical concern axes, env/config boundary, archive convention, dedup convention).
- `CLAUDE.md` init checklist gains step #10: "Lire `docs/doctrine/CODE_DOCTRINE.md`" — making it mandatory reading at every session start, on the same level as the playbook doctrine.
- `AGENTS.md` and every sub-agent under `.claude/agents/*.md` references the doctrine and refuses to produce code that violates the **hard** rules (the deterministic ones below).
- A linter `scripts/lint_code_hygiene.py` runs in <5s on the whole tree and enforces the **mechanical** rules:
  - `fail` on file >800 LOC
  - `fail` on `os.environ`/`os.getenv` outside `growthcro/config.py`
  - `fail` on `_archive*` / `_obsolete*` / `*deprecated*` directories nested inside active paths
  - `fail` on basename duplicates across active paths
  - `info` listing for files >300 LOC (signal, not error — the reviewer/LLM must affirm "single concern")
  - `warning` when a >300 LOC file shows mixed-concern signals (cross-domain imports, divergent function-name prefixes, multiple unrelated top-level classes)
- A documented **auto-update loop**: when an instance Claude detects a new anti-pattern not yet covered by the doctrine, it proposes an addition via a separate commit `docs(doctrine): code +<rule>` — never a silent edit. The loop is described in `CODE_DOCTRINE.md` itself.
- `state.py` (or a sibling) prints the linter summary as part of the standard project-state dump, so doctrine drift is visible at every session start.

## Functional Requirements

### FR-1 — Single source of truth per capability
- Identify every capability with multiple implementations (e.g. `reco_enricher_v13.py` vs `reco_enricher_v13_api.py`); pick the canonical one; replace all callers; move the rest to `_archive/`.
- Concretely: at least 20 known basename duplicates to resolve.

### FR-2 — Hunt and split god files
- Hard cap: no active source file >800 LOC.
- Targets: `reco_enricher_v13.py` (1,690), `controlled_renderer.py` (1,665), `mode_1_persona_narrator.py` (1,448), `enrich_v143_public.py` (1,339), `gsg_generate_lp.py` (1,218), `perception_v13.py` (1,134), `ghost_capture_cloud.py` (1,122), `score_specific_criteria.py` (1,101), `site_intelligence.py` (1,070), `native_capture.py` (1,032).
- Each split must follow concern boundaries (prompt assembly / API client / persistence / orchestration), not arbitrary line cuts.

### FR-3 — Centralize env/config
- New module `growthcro/config.py` (or equivalent at root). Single import surface.
- All `os.environ[...]` and `os.getenv(...)` calls in active paths replaced.
- Lazy + memoized; raises `MissingConfigError` with which variable is missing.

### FR-4 — Move archives out of active paths
- `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` → `_archive/site-capture/2026-04-19/`
- `data/captures/*/[_obsolete_pages_2026-04-29|_obsolete_*]/` → `_archive/data_obsolete/`
- Active dirs contain *only* live code and live data after migration.

### FR-5 — Top-level reorganization
- The 6 root-level Python files (`add_client.py`, `api_server.py`, `capture_full.py`, `enrich_client.py`, `ghost_capture_cloud.py`, `state.py`) move into named subpackages (`api/`, `cli/`, `growthcro/capture/`, …) with thin shim wrappers if external scripts call them.
- Root contains: `README.md`, `CLAUDE.md`, `AGENTS.md`, package metadata, `Dockerfile`, `docker-compose.yml`, `.gitignore`, `requirements.txt`, `package.json`/`package-lock.json`, `.env.example`, `state.py` (kept at root by convention — entrypoint of init).

### FR-6 — Deduplicate snippets
- Identify ≥3-line code blocks repeated across files (e.g. JSON loading boilerplate, Anthropic client construction, retry/backoff loops).
- Extract to shared utilities under `growthcro/lib/` or `moteur_gsg/core/`.
- Target: reduce duplicate-block count by ≥70 % (measure with a duplicate detector before/after).

### FR-7 — Wire or kill orphans
- Every file flagged `POTENTIALLY_ORPHANED` by `audit_capabilities.py` is either:
  - imported by an active entrypoint (wired), or
  - moved to `_archive/`.
- Final registry: 0 orphans in active paths.

### FR-8 — Sub-agent contract refresh
- After moves, audit every `.claude/agents/*.md` for stale paths; update.
- Add a smoke test that each agent's referenced commands exist (a CI-style script).

### FR-9 — Documentation regenerated
- `MANIFEST.md §12` adds a changelog entry.
- `CAPABILITIES_SUMMARY.md` regenerated from the new tree.
- Each subpackage gets a 30-line `README.md` (purpose, entrypoints, dependencies).

### FR-10 — Code doctrine + linter + agent wiring (anti-regression)
- Author `docs/doctrine/CODE_DOCTRINE.md`: principles + 8 canonical concern axes + the rules listed in US-6 + the auto-update loop spec.
- Implement `scripts/lint_code_hygiene.py` with the rules from US-6. Plain stdout report; exit code 0/1; <5s on full tree.
- Patch `CLAUDE.md` init sequence (add step #10) and the "Anti-patterns prouvés" section (add: "fichier multi-concern", "env hors `config.py`", "archive dans path actif", "basename dupliqué").
- Patch `AGENTS.md` similarly.
- Patch every `.claude/agents/*.md` so each sub-agent references the doctrine and refuses to emit non-compliant code.
- Wire the linter into `state.py` (final section: "Hygiene check — N info, M warn, K fail").
- Auto-update loop is documented (not automated): an instance Claude that wants to add a rule must produce a `docs(doctrine): code +<rule>` commit with a concrete example of the anti-pattern that motivated it.

## Non-Functional Requirements

### NFR-1 — Behavioural parity
- Pipeline outputs (perception JSON, score JSON, reco JSON) are byte-equivalent for one canonical client (e.g. `weglot`) before and after migration.
- A `scripts/parity_check.sh` is added and run at the end of each task.

### NFR-2 — Reversibility
- Every move uses `git mv` (preserve history).
- Each task is one commit, one PR, mergeable independently of subsequent tasks.
- Doctrine immutables enforced: no `git reset --hard`, no `--force`, no `clean -fd`.

### NFR-3 — LLM-readability metric
- A "robot readability" check: pick 5 hard questions ("where is intent detection wired?", "what reads `playbook/bloc_5_psycho_v3.json`?", "what raises `MissingConfigError`?"), confirm an LLM with no prior context can answer each within 3 file reads.

### NFR-4 — Performance neutrality
- No measurable change in pipeline runtime (within ±5 %) for full-fleet rescore + reco regeneration.

## Success Criteria

| Metric | Before | After (target) |
|---|---:|---:|
| Active source files | 175 | ≤140 |
| Active LOC | 69,482 | ≤55,000 |
| Files >800 LOC | 17+ | 0 |
| Files >500 LOC | 30+ | ≤10 (justified) |
| Root-level `.py` files | 6 | 1 (`state.py`) |
| Basename duplicates (active) | 20+ | 0 |
| `os.environ` reads (active) | 30+ files | 1 file |
| `POTENTIALLY_ORPHANED` count | 48 | 0 |
| `_archive*`/`_obsolete*` inside active dirs | 19+ | 0 |
| `state.py` pipeline counts | 524/525/505 | 524/525/505 (identical) |
| Sub-agents with stale paths | unknown | 0 |
| `lint_code_hygiene.py` `fail` count (active) | n/a | 0 |
| Sub-agents referencing `CODE_DOCTRINE.md` | 0 | all |
| `CLAUDE.md` init steps | 9 | 10 (incl. doctrine code) |

## Constraints & Assumptions

- **Constraint**: Cleanup happens on a dedicated branch (`epic/codebase-cleanup`) with a worktree at `../epic-codebase-cleanup/`. No direct commits to `main` until the parity check passes for every reorg task.
- **Constraint**: No structural change inside `playbook/`, `data/`, `deliverables/`, `SCHEMA/`, `.claude/`. Those are owned by other doctrines (doctrine-keeper, capabilities-keeper).
- **Constraint**: No new dependencies. The cleanup must succeed with the current `requirements.txt` + `package.json`.
- **Constraint**: Mathis approves each major move before execution (worktree-style review, not rubber-stamp). Hard limit: no destructive op without explicit `OK Mathis`.
- **Assumption**: `state.py` and `audit_capabilities.py` are the canonical instruments to verify "before/after". If they disagree with reality, fix them first as a prelude task.
- **Assumption**: Sub-agents under `.claude/agents/` are the only stable consumers of the current paths; one-off shell scripts may break and that's acceptable if documented.

## Out of Scope

- Doctrine changes (no edit to `playbook/*.json`)
- Schema changes (no edit to `SCHEMA/*.json`)
- New capabilities, new modules, new providers
- Rewriting the dashboard (`deliverables/`)
- Notion content reorganization
- Test coverage expansion (we add only the **parity check**, not unit tests)
- Performance optimization (no profiling-driven rewrites)
- TypeScript/JS reorg (only Python is in scope; JS/TS files in `skills/site-capture/references/` stay where they are *unless* trivially mis-placed)

## Dependencies

- **Internal**: `audit_capabilities.py` must work (it does, last run 2026-05-08); `state.py` must work (idem); `SCHEMA/validate_all.py` must work.
- **Internal**: An up-to-date `data/clients_database.json` snapshot for parity testing on at least one client.
- **External**: None — cleanup is local refactor, no API contract changes, no Notion sync, no external service touched.
- **Process**: The doctrine-keeper agent should be consulted *only if* a move appears to touch any playbook reference — otherwise it's not in the loop. The capabilities-keeper agent is consulted *every task* (it's the regression trip-wire for orphans).
