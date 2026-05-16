---
name: growthcro-anti-drift
description: Enforces GrowthCRO project scope, issue discipline, LOC constraints, non-goals and anti-drift protocol before any code-emission task. Triggers when starting a GitHub issue tagged P0/P1/P2 on the GrowthCRO project, when launching a wave of the `growthcro-stratosphere-p0` epic, when invoking subagent-driven-development on GrowthCRO, or when the user mentions "scope", "drift", "issue start", "before coding", "anti-drift". Do NOT trigger for exploratory conversations, ad-hoc debugging, code review, brainstorming, or non-GrowthCRO repos.
---

# growthcro-anti-drift

## Why this skill exists

Past sessions drifted: refactored files outside the issue scope, implemented "useful adjacent" features that bloated PRs to >800 LOC, modified doctrine without an ADR, or touched the manifest without a separate commit. Each drift caused a rollback or a manual cleanup commit. This skill makes the drift impossible to forget by forcing a structured **pre-flight** before the first line of code and a **post-flight** before the final commit.

It is a thin discipline wrapper. It **references** the doctrine; it does not duplicate it. Source of truth is always the linked file.

## When to invoke

- Starting any GitHub issue on the GrowthCRO project (label `P0`, `P1`, `P2`, or any task file under `.claude/epics/*/N.md`)
- Before the first `Write` / `Edit` of an implementation session
- When a parent agent dispatches you via `subagent-driven-development` or `dispatching-parallel-agents`
- When the user says: "start working on issue N", "let's ship issue N", "wave N of the epic", "implement task N"

## Mandatory pre-flight (print verbatim, fill every field)

```
CURRENT ISSUE       : #<N> — <Title>
LINKED PRD          : <.claude/prds/<slug>.md or N/A>
LINKED EPIC         : <.claude/epics/<slug>/epic.md or N/A>
LINKED DOSSIER ref  : <docs/state/AUDIT_DECISION_DOSSIER_*.md §X.Y or N/A>
IN SCOPE            : <bullet list — files + behaviors that MAY be touched>
OUT OF SCOPE        : <bullet list — files + behaviors that MUST NOT be touched, even if tempting>
EXPECTED FILES      : <create: ...   modify: ...   delete: ...   (max 6 unless task file says otherwise)>
DRIFT RISK          : <low | medium | high> — <one-sentence prediction of the most likely drift>
STOP CONDITIONS     : the 13 conditions below + any issue-specific ones from the task file
FILES_ALLOWED       : <glob patterns the session may touch>
FILES_FORBIDDEN     : <glob patterns the session must NOT touch>
```

If any field cannot be filled, **stop and ask** before coding.

## The 13 stop conditions (always active)

Reference: [`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`](../../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md) §8.

1. Migration destructive (DB schema change, `git mv` massif) → ask Mathis.
2. Secret detected in clear (commit, log, comment) → stop, scrub, ask.
3. Unresolved product contradiction (e.g. scope opportunity vs scope reco) → stop, ask.
4. External skill required to proceed → security audit + Mathis approval first.
5. Critical LLM output not validated by a strict Pydantic v2 schema → stop, add schema.
6. A claim is rendered in test HTML without an evidence proof → stop, wire `ClaimsSourceGate` or remove.
7. A file outside `IN SCOPE` must be touched → stop, propose a separate issue, do **not** touch.
8. LOC budget: source file >300 → split obligatory; >800 → hard fail, refuse to add.
9. Critical gate (`check_gsg_*.py`, `SCHEMA/validate_all.py`, Weglot regression fixture) fails → stop, investigate.
10. `python3 scripts/lint_code_hygiene.py --staged` returns `fail > 0` → fix, re-run, then commit.
11. Any of the 12 anti-patterns in `.claude/CLAUDE.md` would be re-introduced (mega-prompt >8K, archive in active path, basename duplicate outside allow-list, env read outside `growthcro/config.py`, >8 simultaneous skills, forbidden combo) → stop.
12. Doctrine V3.2.1 needs to change → route to a `doctrine-keeper` flow, not this issue.
13. `docs/reference/GROWTHCRO_MANIFEST.md` §12 must be bumped → that goes in a **separate commit** (`docs: manifest §12 — ...`).

## Hard rules

- **One issue at a time.** Do not also "quickly fix" a sibling issue you noticed.
- **No future-phase work.** P1/P2 items belong in their own issues even if obvious now.
- **No refactor of unrelated files.** Use the spawn-task tool to flag follow-ups; do not implement them inline.
- **Conventional commits, one issue per commit.** `<type>(<scope>): <subject> [#<issue>]`.
- **`git status` clean before batch.** If unstaged changes from a previous session exist, stash or resolve before starting.
- **No `git reset --hard`, `push --force`, `clean -fd`, `branch -D`, `checkout -- <file>`** without explicit Mathis approval (anti-pattern #6 of immutable rules).
- **Hygiene gate is non-negotiable.** `python3 scripts/lint_code_hygiene.py --staged` must exit 0 before `git commit`.

## Mandatory post-flight (print verbatim, before final commit)

```
DONE                : <bullet list — acceptance criteria satisfied>
FILES CHANGED       : <full list, grouped by created / modified / deleted>
LOC DELTA           : <+added / -removed> (and per-file if any >300)
TESTS RUN           : <commands + pass/fail per command>
HYGIENE GATE        : python3 scripts/lint_code_hygiene.py --staged → exit <0|N>
DOCS UPDATED        : <bullets — PROJECT_STATUS, CHANGELOG_AI, MANIFEST §12 (separate commit), SPRINT_LESSONS, ADRs>
RISKS               : <bullets — known limitations, follow-ups>
DRIFT CHECK         : <list anything you touched that fell outside the pre-flight IN SCOPE, or "none">
NEXT ISSUE          : <#N if known, else "ask Mathis">
```

If `DRIFT CHECK` is not "none", surface it explicitly to the user before merging — do not bury it.

## References (do not duplicate, link)

- [`.claude/CLAUDE.md`](../../CLAUDE.md) — "Anti-patterns prouvés" (12 entries), "Règles immuables", "Mise à jour du manifest"
- [`.claude/docs/doctrine/CODE_DOCTRINE.md`](../../docs/doctrine/CODE_DOCTRINE.md) — 8 mono-concern axes, LOC limits, learning loop
- [`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`](../../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md) §8 — 13 stop conditions canonical source
- [`.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`](../../docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md) — combo packs and the ≤8 simultaneous skills hard cap
- CCPM workflow: PRD → Epic → Issue → Branch → PR (see `growthcro-prd-planner` skill)

## Related GrowthCRO skills

- `growthcro-prd-planner` — produces the PRD / Epic / Issues that this skill then guards
- `growthcro-status-memory` — runs at the **post-flight** to update status files and (separately) the manifest
