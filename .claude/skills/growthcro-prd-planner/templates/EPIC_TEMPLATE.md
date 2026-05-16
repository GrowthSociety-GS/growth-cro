---
name: <slug-kebab-case>
status: backlog
created: <YYYY-MM-DDTHH:MM:SSZ>
updated: <YYYY-MM-DDTHH:MM:SSZ>
progress: 0%
prd: .claude/prds/<slug>.md
github: <github issue URL once synced, else TBD>
---

# Epic: <slug-kebab-case>

> Source de vérité primaire : [`<path/to/AUDIT_DECISION_DOSSIER_*.md>`](<relative-path>). PRD : [`.claude/prds/<slug>.md`](../../prds/<slug>.md).

## Overview

<2-3 paragraphs. The three or four lines of force of the epic. What gates land. What modules get created. What stays untouched.>

## Architecture Decisions

| Décision | Rationale |
|----------|-----------|
| **Mono-concern 8-axes** for all new Python modules | Per CODE_DOCTRINE.md. One module = one axis (validation / persistence / orchestration / CLI / prompt / API / scoring / capture). |
| **Conventional commits, 1 issue per commit** | Traceability + rollback granulaire. `<type>(<scope>): <subject> [#<issue>]`. |
| **No doctrine V3.2.1 modification** | If GSG-adjacent, modifications route to a separate doctrine-keeper PRD. |
| **Manifest §12 bump as SEPARATE commit** | Per CLAUDE.md `Mise à jour du manifest`. Never bundled with implementation. |
| <epic-specific decision> | <rationale> |

## Technical Approach

### Backend Services / Python modules

**New modules (mono-concern)** :
- `growthcro/<package>/schema.py` — Pydantic v2 validation (axe `validation`)
- `growthcro/<package>/persist.py` — read/write artefacts (axe `persistence`)
- `growthcro/<package>/orchestrator.py` — sequence (axe `orchestration`)
- `growthcro/<package>/cli.py` — argparse entrypoint (axe `CLI`)

**Targeted modifications** (1–2 axes touched max per file):
- `<file>` : <what changes, which axis>

### Frontend (if applicable)

- <component or page changes, with file paths>

### Infrastructure

- <env vars, secrets, deploy targets, fixtures>

## Implementation Strategy

- **Phases** : <e.g. Wave 1 parallel — gates + skills; Wave 2 sequential — verdict aggregation; Wave 3 — security + docs>
- **Risk mitigation** : <e.g. add Weglot regression fixture before any change to multi-judge>
- **Testing approach** : TDD per `test-driven-development` skill; fixtures live under `tests/fixtures/`.

## Task Breakdown Preview

| # | Title | Size | Hours | Parallel? | Depends on |
|---|-------|------|-------|-----------|------------|
| 40 | <title> | S | 3 | yes | — |
| 41 | <title> | M | 5 | no | #40 |
| ... |

## Dependencies

```
DEPENDENCIES GRAPH:
  #N → #M (M depends on N)
  #A, #B parallel (no shared files)

PARALLELIZATION WAVES:
  Wave 1 (parallel): #40, #41, #42
  Wave 2 (parallel, depends on Wave 1): #43, #44
  Wave 3 (sequential): #45 → #46
```

## Success Criteria

- All FR from PRD map to ≥1 acceptance criterion in ≥1 task.
- All regression fixtures green (`pytest`, `python3 SCHEMA/validate_all.py`, `python3 scripts/lint_code_hygiene.py --staged`).
- 0 new file >300 LOC without single-concern reviewer affirmation.
- 0 anti-pattern from CLAUDE.md re-introduced.

## Estimated Effort

- Total hours: <sum>
- Critical path: <issues on critical path>
- Calendar: <weeks if dispatched 1 agent at a time vs N agents parallel>

## Tasks Created

> Populated by CCPM at sync time.

- [ ] #40 — <title> — <slug>/40.md
- [ ] #41 — <title> — <slug>/41.md
- ...
