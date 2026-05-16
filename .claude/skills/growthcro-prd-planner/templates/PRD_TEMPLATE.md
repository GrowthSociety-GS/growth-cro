---
name: <slug-kebab-case>
description: <1-2 sentences — what this PRD covers and why now>
status: backlog
created: <YYYY-MM-DDTHH:MM:SSZ>
---

# PRD: <slug-kebab-case>

> Source de vérité primaire : [`<path/to/AUDIT_DECISION_DOSSIER_*.md or other anchor>`](<relative-path>).
> Ce PRD résume sans dupliquer. En cas de conflit : la source de vérité gagne.

## Executive Summary

<2-4 paragraphs. State the user-visible outcome, the current pain, and the chosen direction. Reference the canonical dossier section if relevant.>

## Problem Statement

**Pourquoi maintenant ?**

1. <symptom 1 with concrete evidence — file path, metric, fixture>
2. <symptom 2>
3. <symptom 3>

**Coût de l'inaction** : <what breaks or stays broken if this PRD is not shipped>

## User Stories

### Story 1 — <persona> (<role>)
**En tant que** <persona>,
**je veux** <capability>,
**afin que** <outcome>.
**Acceptance** : <one concrete, testable assertion — fixture, screenshot, exit code>.

### Story 2 — <persona>
...

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | <must-have behavior> | P0 |
| FR-2 | <must-have behavior> | P0 |
| FR-3 | <should-have> | P1 |

## Non-Functional Requirements

- **Performance** : <p95 budgets, throughput>
- **Security** : <SSRF, secrets in env, no JWT in repo, etc.>
- **Observability** : <logs, metrics, fixture replays>
- **Doctrine compliance** : 8 mono-concern axes, LOC ≤300 / file, ≤50 / function (cf. CODE_DOCTRINE.md)

## Success Criteria

- <metric 1> moves from <baseline> to <target>
- <gate> blocks <bad case> in a regression fixture
- 0 hygiene-gate violations on the diff (`python3 scripts/lint_code_hygiene.py --staged` exit 0)
- 0 anti-pattern from CLAUDE.md re-introduced

## Constraints

- Doctrine V3.2.1 frozen for this PRD (modifications = separate PRD via doctrine-keeper).
- No new external skill installation without security audit (cf. SKILLS_REGISTRY_GOVERNANCE.json).
- No `git reset --hard` / `push --force` / `clean -fd` without explicit Mathis approval.
- Manifest §12 bump = SEPARATE commit (`docs: manifest §12 — ...`).

## Out of Scope

> Copy the full content of `OUT_OF_SCOPE_CHECKLIST.md` then extend with PRD-specific items below.

- <PRD-specific out-of-scope 1, with rationale and suggested follow-up issue link>
- <PRD-specific out-of-scope 2>

## Dependencies

- <other PRD or epic that must land first, with link>
- <external service or API required>
- <skill or agent required (audited)>

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| <risk> | low/med/high | low/med/high | <mitigation> |
