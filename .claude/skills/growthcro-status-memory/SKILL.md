---
name: growthcro-status-memory
description: Updates GrowthCRO project memory files after significant implementation steps — epic completion, sprint close, major PR (>200 LOC or new module), architectural decisions. Triggers on "update status", "log this sprint", "close the epic", "wrap up Wave N", "post mortem", "ADR for decision X", "what changed", "log the change", "memory bump". Do NOT trigger for trivial commits, typo fixes, or minor refactors.
---

# growthcro-status-memory

## Why this skill exists

Between Claude Code sessions, project memory leaks. Last week's epic is forgotten next week. The "Pack GPT + Skills Addendum" audit identified this as **problem #1**: lost context drives drift. This skill is the discipline that keeps the project narrative in writeable, human-readable files that any future session loads in its init sequence.

It is a **mechanical update protocol**, not an interpretation layer. It writes facts (what changed, what's mocked, what works, what's at risk) and leaves the strategy to humans.

## When to invoke

- **After a completed epic** — when the last issue is closed
- **At sprint close** — even if no formal epic, when a body of work ships
- **After any architectural decision** that future-Claude needs to know about → write an ADR
- **After a major PR** (>200 LOC or a new module/package)
- When Mathis says: "log this", "update status", "wrap up", "what changed", "post mortem"

**Do not invoke for**: a typo fix commit, a 1-line config change, a routine refactor that does not change behavior.

## Files this skill maintains

| # | File | Cadence | Append vs Rewrite |
|---|------|---------|-------------------|
| 1 | `docs/status/PROJECT_STATUS.md` | After every significant change | Rewrite (living summary) |
| 2 | `docs/status/NEXT_ACTIONS.md` | After every significant change | Rewrite (priority list) |
| 3 | `docs/status/CHANGELOG_AI.md` | After every significant change | Append-only |
| 4 | `docs/adr/ADR-<NNN>-<slug>.md` | When an architectural decision is taken | New file, never edit existing |
| 5 | `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 | When a brique majeure is touched | Append; **SEPARATE commit** |
| 6 | `memory/SPRINT_LESSONS.md` | At sprint close | Append 1–3 lessons; **SAME commit** as the closing `feat(gsg)`/`fix(gsg)` |

If `docs/status/`, `docs/adr/`, or any file does not yet exist, **create it** — do not fail silently.

## Format per file

### 1. `docs/status/PROJECT_STATUS.md` (living summary, rewrite each time)

```markdown
# GrowthCRO — Project Status

_Last updated: <YYYY-MM-DD> by Claude session (model: <id>) on commit <sha>_

## WHAT CHANGED (since last status)
- <bullet — concise, with file paths or issue numbers>

## CURRENT STATE
- Pipeline version: <e.g. V26.AI Sprint 21>
- Clients runtime: <e.g. 56>
- GSG canonical: <e.g. V27.2-F/G>
- Composite score (last bench): <e.g. 88.6% Exceptionnel, Weglot V14b>

## WHAT IS MOCKED
- <bullet — fixtures, fake data, stub gates>

## WHAT WORKS (verified)
- <bullet — gate, fixture, e2e flow with proof location>

## KNOWN RISKS
- <bullet — with severity>

## DO NOT FORGET
- <bullet — recurring trap, anti-pattern resurfacing risk>
```

### 2. `docs/status/NEXT_ACTIONS.md` (priority list, rewrite each time)

```markdown
# GrowthCRO — Next Actions

_Last updated: <YYYY-MM-DD>_

## P0 (blocking)
1. <action — owner — link to PRD/issue>
2. ...

## P1 (next wave)
1. ...

## P2 (moat)
1. ...

## Out of scope for now
- <item — why, when to revisit>
```

### 3. `docs/status/CHANGELOG_AI.md` (append-only)

```markdown
## <YYYY-MM-DD> — <short title>

### Files
- created: <path>
- modified: <path>
- deleted: <path>

### Why
<1–3 sentences. Link to PRD, dossier, issue.>

### Risks
- <bullet>

### Agent / commit
- Agent: Claude session (model: <id>)
- Commits: <sha1>, <sha2>
```

### 4. `docs/adr/ADR-<NNN>-<slug>.md` (one per architectural decision)

Numbering is sequential. To find next number: `ls docs/adr/ | sort | tail -1`.

```markdown
# ADR-<NNN>: <Decision title>

- Status: accepted | superseded by ADR-<MMM> | rejected
- Date: <YYYY-MM-DD>
- Deciders: Mathis + Claude session
- Source: <link to PRD / dossier / discussion>

## Context
<what problem, what forced the decision, what was tried>

## Decision
<the choice, in 1–3 sentences>

## Consequences
- Positive: ...
- Negative: ...
- Neutral: ...

## Alternatives considered
- <option A> — rejected because ...
- <option B> — rejected because ...
```

Create an ADR when (any of):
- A module gains a new mono-concern axis
- A schema changes shape (Pydantic v2 model field added/removed)
- A doctrine constant or threshold changes
- An external service / skill / agent is added or retired
- A security boundary moves (e.g. SSRF validator added)

Do NOT create an ADR for: a bug fix, a refactor that preserves behavior, a config bump.

### 5. `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 (changelog of briques majeures)

```markdown
## §12 — Changelog

- **<YYYY-MM-DD>** — <brique majeure> : <1 line summary> (`<commit-sha>`)
```

**Hard rule** (per `.claude/CLAUDE.md` "Mise à jour du manifest"): this update lives in its **own commit**, with message `docs: manifest §12 — add <YYYY-MM-DD> changelog for <change>`. Never bundle with implementation.

A "brique majeure" is one of: Audit Engine, Brand DNA + Design Grammar, GSG, Webapp Observatoire, Reality Layer, Multi-judge, Experiment Engine, Learning Layer, GEO Monitor, Opportunity Layer, Capture, Skill Registry governance.

### 6. `memory/SPRINT_LESSONS.md` (1–3 lessons at sprint close)

**Hard rule** (per `CODE_DOCTRINE.md` §Learning loop): the closing commit of a sprint (`feat(gsg):` or `fix(gsg):`) **must** touch this file in the **same commit**.

Format:
```markdown
## Sprint <N> — <YYYY-MM-DD>

### Lesson 1 — <short rule>
- **Règle** : <imperative one-liner>
- **Déclencheur** : <when this lesson applies>
- **Conséquence si violée** : <what breaks, with past evidence>

### Lesson 2 — <short rule>
...
```

Maximum 3 lessons per sprint. Distill ruthlessly — `memory/SPRINT_LESSONS.md` has 24+ rules from past sprints and must remain readable.

## Workflow

1. **Identify trigger** (epic closed? sprint? major PR? ADR-worthy decision?).
2. **Check pre-existence** of `docs/status/`, `docs/adr/`, target files. Create folders/files if missing.
3. **Rewrite** PROJECT_STATUS.md and NEXT_ACTIONS.md from current ground truth (`git log`, closed issues, open PRDs).
4. **Append** to CHANGELOG_AI.md.
5. **If architectural decision**: write a new ADR with the next sequential number.
6. **If brique majeure touched**: update `MANIFEST.md §12`. **Stage and commit this file ALONE** with `docs: manifest §12 — ...`.
7. **If sprint closed**: append 1–3 lessons to `memory/SPRINT_LESSONS.md` and ensure the closing `feat(gsg):` / `fix(gsg):` commit includes it.
8. **Surface to user**: list the files updated, the new ADR number if any, and any "manifest §12 SEPARATE commit pending" warning.

## Hard rules (non-negotiable)

- **Manifest §12 = SEPARATE commit.** Bundling with implementation is a stop condition (CLAUDE.md §Mise à jour du manifest, stop condition #13).
- **SPRINT_LESSONS.md = SAME commit** as the closing `feat(gsg)`/`fix(gsg)` (CODE_DOCTRINE §Learning loop).
- **No Notion modification** from this skill. Notion writes require explicit Mathis request.
- **No automatic `git push`.** This skill prepares files and proposes commits. The user pushes.
- **Append-only files stay append-only** (CHANGELOG_AI.md, SPRINT_LESSONS.md). Never rewrite history; only add entries.
- **ADRs are immutable once accepted.** To change a decision, write a new ADR that supersedes (and update the old one's `Status` line to `superseded by ADR-<NNN>`).

## References

- [`.claude/CLAUDE.md`](../../CLAUDE.md) §Mise à jour du manifest, §Règles immuables
- [`.claude/docs/doctrine/CODE_DOCTRINE.md`](../../docs/doctrine/CODE_DOCTRINE.md) §Learning loop
- [`memory/SPRINT_LESSONS.md`](../../../memory/SPRINT_LESSONS.md) — existing 24+ rules to read before adding new ones
- [`.claude/docs/reference/GROWTHCRO_MANIFEST.md`](../../docs/reference/GROWTHCRO_MANIFEST.md) §12

## Related GrowthCRO skills

- `growthcro-anti-drift` — invoked at issue start; this skill is its post-flight counterpart
- `growthcro-prd-planner` — produces the artifacts this skill later records the status of
