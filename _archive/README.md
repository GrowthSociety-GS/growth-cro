# `_archive/` — append-only history outside active paths

## Purpose

Anything moved out of an active code/data path goes here. This directory is **append-only**: nothing in `_archive/` is ever deleted. It's where history lives outside `git log` — providing a directory-level browse complement to git history.

The cleanup epic (#1) treats `_archive/` as the destination for:
- Deprecated code that's been replaced but is worth keeping for reference
- Obsolete client capture data superseded by re-runs
- One-shot migration tools that produced refactor commits
- Parity baselines (regression contracts for the cleanup epic)

## Active rules

1. **Active paths must contain no archive folders.** Any directory whose name matches `_archive*`, `_obsolete*`, `*_deprecated*`, `*_backup*` outside this tree is a doctrine violation — relocate it here. The cleanup-epic gate is `find . -type d \( -name "_archive*" -o -name "_obsolete*" -o -name "*deprecated*" -o -name "*backup*" \) -not -path "./_archive/*" -not -path "*/node_modules/*" -not -path "*/worktrees/*" -not -path "*/.git/*"` returns nothing.
2. **Layout**: `_archive/<area>/<ISO-date>/<original-subtree>/`. The original sub-tree is preserved so a future reader can locate where the artefact lived.
3. **Tracked in git only when load-bearing.** `.gitignore` ignores `_archive/*` by default; explicit exceptions are added for paths that subsequent task agents need to read (e.g. `_archive/parity_baselines/`, `_archive/migration_tools/`).
4. **Moves use `git mv`** so commit history follows the file across relocations.

## Provenance log

Append a date-stamped line whenever an archive lands here.

| Date | What | Why | From |
|---|---|---|---|
| 2026-05-09 | `parity_baselines/weglot/2026-05-09T11-13-30Z/` + 3 instrument baselines | Regression contract for the cleanup epic | Issue [#2](https://github.com/GrowthSociety-GS/growth-cro/issues/2) |
| 2026-05-09 | `migration_tools/2026-05-09_env_to_config/{migrate_env_to_config.py,fix_syspath.py}` | One-shot tools that produced the env-centralization commit | Issue [#3](https://github.com/GrowthSociety-GS/growth-cro/issues/3) |
| 2026-05-10 | `README.md` (this file) + audit log of pre-existing legacy folders | Inventory pass after V26.AG fresh-history migration | Issue [#4](https://github.com/GrowthSociety-GS/growth-cro/issues/4) |

## State on 2026-05-10 (Task #4 audit)

The V26.AG fresh-history migration that produced the current `main` baseline (commit `5fb582f`) had already culled the legacy archive folders that issue #4 was originally written to relocate:
- `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` — **not present** on this branch
- `data/captures/<client>/_obsolete_pages_2026-04-29/` for any client — **not present** (no `data/captures/` data on the fresh-history branch at all yet)

The archive-pollution gate is therefore already green. Issue #4's substantive work was implicitly done by the migration; this task formalizes the rule (`_archive/README.md`, the gate, the layout) so future captures and future archived code respect it from the start.
