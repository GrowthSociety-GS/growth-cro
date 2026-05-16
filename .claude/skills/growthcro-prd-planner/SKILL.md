---
name: growthcro-prd-planner
description: Converts GrowthCRO project ideas, sprints or feature requests into CCPM-compliant PRDs, technical epics and atomic GitHub issues. Triggers on "create PRD", "write a PRD for", "plan this feature", "scope this sprint", "decompose epic", "split this into issues", "let's plan X" — when X is a GrowthCRO concern (audit engine, GSG, multi-judge, opportunity layer, capture, recos, webapp, skill registry, gates, doctrine). Do NOT trigger for PRDs in other repos, for raw exploratory brainstorming (use `brainstorming` first), or for one-line bug fixes.
---

# growthcro-prd-planner

## Why this skill exists

GrowthCRO already uses the [CCPM](../../../.claude/skills/ccpm/SKILL.md) workflow (PRD → Epic → GitHub Issues → parallel agents). The generic `ccpm` skill handles the lifecycle. **This skill is the GrowthCRO-opinionated wrapper** that:

1. Injects the project-specific **out-of-scope checklist** (doctrine V3.2.1 modifications, microfrontends, refactor >5 files, etc.)
2. Enforces the **8-axes mono-concern** CODE_DOCTRINE on every issue's `Files Affected` section
3. Adds **LOC budgets** (300 / 800 hard fail) and **per-issue stop conditions** referencing the 13 canonical ones
4. Wires the **anti-drift pre-flight** of `growthcro-anti-drift` into every generated issue's body
5. Points the PRD/Epic at the relevant **AUDIT_DECISION_DOSSIER_*.md** section as source of truth

## When to invoke

- "create a PRD for `<topic>`" / "écris un PRD pour `<sujet>`"
- "plan the next sprint" / "scope this chantier"
- "decompose `<epic>` into issues"
- "let's plan `<feature>` for GrowthCRO"
- "split this into atomic tasks"

**Do not invoke for**: pure brainstorming (use `brainstorming` first, then this skill), CCPM operations on non-GrowthCRO repos (use `ccpm` directly), or sprint retrospectives (use `growthcro-status-memory`).

## Workflow

### Step 1 — Anchor

Before generating anything, identify and confirm with the user:
- **Source of truth** : which `docs/state/AUDIT_*.md` or Notion page anchors the work?
- **Master PRD link** : is this a sub-epic of an existing PRD (e.g. `growthcro-stratosphere-p0.md`)?
- **Manifest impact** : will any brique majeure (GSG, multi-judge, opportunity layer, capture, scoring, recos, webapp) be touched? → flag for `MANIFEST.md §12` bump (separate commit).

### Step 2 — Produce the PRD

Copy `templates/PRD_TEMPLATE.md` to `.claude/prds/<slug>.md` and fill every section. Keep `Out of Scope` rich — pull from `templates/OUT_OF_SCOPE_CHECKLIST.md` and add domain-specific items.

### Step 3 — Produce the Epic

Copy `templates/EPIC_TEMPLATE.md` to `.claude/epics/<slug>/epic.md`. The `Architecture Decisions` table must include:
- "Mono-concern 8-axes per CODE_DOCTRINE" if any new Python module is created
- "Conventional commits, 1 commit per issue" (always)
- "No doctrine V3.2.1 modification" if the topic is GSG-adjacent
- "Manifest §12 bump as SEPARATE commit" if a brique majeure is touched

### Step 4 — Decompose into atomic issues

Copy `templates/ISSUE_TEMPLATE.md` to `.claude/epics/<slug>/<N>.md` for each task. Atomicity rules:
- **One issue = one behavior or one artifact.** No bundles.
- **1–6 files touched** per issue (more = split).
- **50–300 LOC added** per issue (less = trivial, fold into adjacent; more = split).
- Each issue carries its own `Stop Conditions` section: the 13 canonical + any issue-specific.
- Each issue's `Files Affected` section lists files by mono-concern axis (validation / persistence / orchestration / CLI / prompt / API / scoring / capture).

### Step 5 — Dependencies graph + parallelization waves

Append to the epic a `Dependencies` block:
```
DEPENDENCIES GRAPH:
  #N → #M (M depends on N)
  ...

PARALLELIZATION WAVES:
  Wave 1 (parallel): #A, #B, #C
  Wave 2 (parallel, depends on Wave 1): #D, #E
  ...
```

Use `dispatching-parallel-agents` discipline: issues in the same wave must touch disjoint files (no shared state, no sequential dependency).

### Step 6 — Sync to GitHub (CCPM)

Delegate to the generic `ccpm` skill for `gh issue create` per task and update of `github-mapping.md`. This skill does not directly call `gh` — it produces the artifacts CCPM consumes.

## Hard rules

- **Do not touch doctrine V3.2.1.** If a proposed issue would modify `docs/doctrine/*.md` for GSG scoring, escalate to a `doctrine-keeper` agent flow.
- **OUT_OF_SCOPE_CHECKLIST.md is mandatory.** Every PRD copies it verbatim into its own Out of Scope section, then extends.
- **Each generated issue references `growthcro-anti-drift`.** Add a top-of-body note: *"Before coding, invoke `growthcro-anti-drift` and print the pre-flight block."*
- **No automatic `gh` calls from this skill.** Producing files is in scope; pushing to GitHub goes through `ccpm` so the user can review.
- **Manifest §12 lives in a SEPARATE commit.** Never bundle it with implementation issues.

## File outputs (what the user gets)

1. `.claude/prds/<slug>.md` — the PRD
2. `.claude/epics/<slug>/epic.md` — the technical epic
3. `.claude/epics/<slug>/<N>.md` for each atomic task (numbering continues from the project's last issue number, not from 1)
4. `.claude/epics/<slug>/github-mapping.md` — placeholder, populated by `ccpm` sync
5. `.claude/epics/<slug>/EXECUTION_PLAN_WAVE_<K>.md` — one per wave, listing the parallel dispatch plan

## References

- [`.claude/skills/ccpm/SKILL.md`](../ccpm/SKILL.md) — generic PRD/Epic/Issue lifecycle
- [`.claude/docs/doctrine/CODE_DOCTRINE.md`](../../docs/doctrine/CODE_DOCTRINE.md) — 8 mono-concern axes, LOC budgets
- [`.claude/CLAUDE.md`](../../CLAUDE.md) — 12 anti-patterns, immutable rules, manifest §12 convention
- [`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`](../../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md) — example of a canonical source of truth a PRD anchors on
- [`.claude/prds/growthcro-stratosphere-p0.md`](../../prds/growthcro-stratosphere-p0.md) + [`.claude/epics/growthcro-stratosphere-p0/epic.md`](../../epics/growthcro-stratosphere-p0/epic.md) — reference example produced by this workflow

## Companion templates

- [`templates/PRD_TEMPLATE.md`](templates/PRD_TEMPLATE.md)
- [`templates/EPIC_TEMPLATE.md`](templates/EPIC_TEMPLATE.md)
- [`templates/ISSUE_TEMPLATE.md`](templates/ISSUE_TEMPLATE.md)
- [`templates/OUT_OF_SCOPE_CHECKLIST.md`](templates/OUT_OF_SCOPE_CHECKLIST.md)

## Related GrowthCRO skills

- `growthcro-anti-drift` — referenced inside every generated issue body
- `growthcro-status-memory` — invoked at sprint close to update PROJECT_STATUS / CHANGELOG_AI / SPRINT_LESSONS
