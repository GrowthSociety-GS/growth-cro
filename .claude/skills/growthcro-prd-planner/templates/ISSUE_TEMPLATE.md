---
name: <Imperative-title-starting-with-verb>
status: open
created: <YYYY-MM-DDTHH:MM:SSZ>
updated: <YYYY-MM-DDTHH:MM:SSZ>
github: <github issue URL once synced, else TBD>
depends_on: [<list of issue numbers, or empty>]
parallel: <true if disjoint files with siblings in same wave, else false>
conflicts_with: [<list of issue numbers that touch overlapping files>]
---

# Task: <Imperative-title>

> Before coding, invoke `growthcro-anti-drift` and print the pre-flight block (CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS / FILES_ALLOWED / FILES_FORBIDDEN). Source: `.claude/skills/growthcro-anti-drift/SKILL.md`.

## Description

<2-4 sentences. What this task delivers, why, and the smallest user-visible / system-visible change.>

Source : `<path/to/AUDIT_DECISION_DOSSIER_*.md>` §<X.Y>.

## Acceptance Criteria

- [ ] <concrete, testable assertion>
- [ ] <concrete, testable assertion>
- [ ] `python3 scripts/lint_code_hygiene.py --staged` exit 0
- [ ] Regression fixture (Weglot or equivalent) still green
- [ ] Commit conventional : `<type>(<scope>): <subject> [#<issue>]`

## Technical Details

**Files Affected** (grouped by mono-concern axis per CODE_DOCTRINE.md) :

| Axis | File | Action | Approx LOC delta |
|------|------|--------|-------------------|
| validation | `<path>` | create | +120 |
| orchestration | `<path>` | modify | +30 / -10 |
| CLI | `<path>` | create | +60 |

**Implementation notes** :
- <key design choice 1>
- <key design choice 2>

## Files Affected (flat list)

- create: `<path>`
- modify: `<path>`
- delete: `<path>`

## Out of Scope

- <thing NOT to touch, even if tempting, with rationale>
- <follow-up worth doing as a separate issue, with suggested P-level>

## Stop Conditions

The 13 canonical conditions from `AUDIT_DECISION_DOSSIER_2026-05-16` §8 PLUS:
- <issue-specific stop condition 1>
- <issue-specific stop condition 2>

## Dependencies

- depends_on: <#N — why>
- blocks: <#M — why>

## Effort Estimate

- Size: <S / M / L>
- Hours: <number>

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] Tests run (commands listed in post-flight)
- [ ] Hygiene gate green
- [ ] Docs updated if applicable (PROJECT_STATUS.md, CHANGELOG_AI.md, MANIFEST §12 separate commit if brique majeure)
- [ ] Commit conventional with `[#<issue>]` suffix
- [ ] GitHub issue closed via `gh issue close <N> -c "Closed: <commit-sha>"`
