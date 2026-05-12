# Issue #38 — Relocate `_archive_deprecated_2026-04-19` + `.gitignore` guard

**Branch**: `epic/micro-cleanup-sprint`
**Worktree**: `/Users/mathisfronty/Developer/epic-micro-cleanup-sprint/`
**Started**: 2026-05-12

---

## State discovery

In this worktree (`epic/micro-cleanup-sprint`, fork point `ff586be`), the directory
`skills/site-capture/scripts/_archive_deprecated_2026-04-19/` does **not exist**.

The dir is **gitignored** (existing rule `.gitignore:137` — `_archive_deprecated_*/`)
and is therefore an **untracked local-only artefact** on Mathis's main checkout
(`/Users/mathisfronty/Developer/growth-cro/`). Since worktrees only carry tracked
files + their own untracked working tree, the dir never propagated to this
worktree.

Concrete proof:
- `git ls-tree -r main skills/site-capture/scripts/ | grep archive_deprecated`
  → 0 lines (never tracked).
- `git status --ignored` in main repo shows it under
  "Ignored files" — confirmed untracked.

Implications:
- Lint in the worktree already shows **FAIL=0** at fork point.
- No `score_site.py` duplicate exists in the worktree active tree (only the
  canonical `skills/site-capture/scripts/score_site.py` is present).
- Mypy `python3 -m mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/`
  reports 583 errors in the worktree (`typecheck.sh` reports 585, well within
  the 603 budget; both exit 0 via `typecheck.sh`).

## Pre-check (mandatory)

### Static path references

```bash
grep -rn "_archive_deprecated_2026-04-19" \
  growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/ \
  | grep -v "Binary file\|^_archive\|^skills/site-capture/scripts/_archive_deprecated"
```

Result: **0 lines** — no active references.

### Dynamic string references

```bash
grep -rn "'_archive_deprecated_2026-04-19'\|\"_archive_deprecated_2026-04-19\"" \
  growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/
```

Result: **0 lines** — no string references.

**Decision**: PROCEED — `.gitignore` upgrade is the only required worktree change.
The local untracked dir in `growth-cro/` can be cleaned up by Mathis post-merge
(or via a follow-up local mv); it is no risk to lint/mypy/CI because it is and
will remain gitignored.

## Plan

1. Upgrade `.gitignore` from `_archive_deprecated_*/` to also include explicit
   `**/_archive_deprecated_*/` wildcard pattern + Anti-pattern #10 doctrine
   comment (keeps existing rule for backward compat; adds the per-task spec
   wildcard).
2. Verify all gates still pass.
3. Commit single isolated change.

## Execution log

### Commit 1 — `.gitignore` guard

Added under `# ─── Archives locales (_archive_deprecated_*, archive/) ─`:

```gitignore
# Anti-pattern #10 prevention (CLAUDE.md) — _archive_deprecated_* doit vivre
# sous _archive/ racine, jamais dans un active path. Linter custom (Rule 3 de
# scripts/lint_code_hygiene.py) flagge ce drift en FAIL. Wildcard pattern
# **/_archive_deprecated_*/ empêche la réintroduction n'importe où dans l'arbre.
**/_archive_deprecated_*/
```

(Existing `_archive_deprecated_*/` line kept — both patterns coexist for
belt-and-suspenders.)

## Gates (post-change)

- [x] `python3 scripts/lint_code_hygiene.py` → **FAIL=0** (was already 0 at
      fork — worktree never carried the offending dir)
- [x] `python3 -m mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/`
      → 583 errors in 72 files (no duplicate `score_site`)
- [x] `bash scripts/typecheck.sh` → **exit 0**, "✓ mypy: 585 errors (budget 603)"
- [x] `bash scripts/parity_check.sh weglot` → exit 0
- [x] `python3 SCHEMA/validate_all.py` → exit 0, 15 files validated
- [x] `python3 scripts/audit_capabilities.py` → 🔴 Orphans HIGH: 0

## Notes for Mathis (post-merge cleanup)

The local untracked directory in your main checkout can be optionally moved out
of the active path with:

```bash
cd /Users/mathisfronty/Developer/growth-cro
mv skills/site-capture/scripts/_archive_deprecated_2026-04-19 \
   _archive/skills_site-capture_deprecated_2026-04-19_root_relocate_2026-05-12
```

This is **purely local hygiene** — neither path is tracked by git, so the move
is invisible to GitHub. The new `**/_archive_deprecated_*/` rule will catch
any future drift if a similar dir is ever recreated in an active path.

## Status

**COMPLETE — 100%** — `.gitignore` upgraded, all gates green, AC met for worktree.

Commits in this branch (Issue #38):
- `5742ea6` Issue #38: add .gitignore guard **/_archive_deprecated_*/ pattern
- `787f7a3` (carried) progress.md status sync via #36 commit (concurrent sweep)
- this commit: Issue #38: completion signal

Final gate snapshot (post all #36/#37/#38 commits on branch):
- lint FAIL=0 / WARN=39 / INFO=91 / DEBT=5
- mypy 582 errors (budget 603), typecheck.sh exit 0
- parity weglot exit 0 / SCHEMA exit 0 / Orphans HIGH=0

## Coordination note

A concurrent worktree process (Issue #36 agent) auto-included this file's
"Status" block update inside commit `787f7a3` ("feat(cleanup): split
copy_writer.py..."). This is harmless — the progress.md content is correct,
just sequenced inside another commit. The completion signal below is the
explicit closure marker for #38.
