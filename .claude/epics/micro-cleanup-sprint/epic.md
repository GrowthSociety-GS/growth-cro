---
name: micro-cleanup-sprint
status: backlog
created: 2026-05-12T13:30:00Z
updated: 2026-05-12T13:30:00Z
progress: 0%
prd: .claude/prds/micro-cleanup-sprint.md
github: (will be set on sync)
parent_prd: post-stratosphere-roadmap
wave: A
epic_index: 2
ice_score: 324
---

# Epic: micro-cleanup-sprint

## Overview

3 micro-actions XS cleanup pour clôturer la dette résiduelle Wave A post Epic 1 typing-strict-rollout (livré 2026-05-12 main `ff586be`). Cible : **lint FAIL=0 absolu** + 0 anti-pattern #8/#10 actif + 0 mypy error global. 3 tasks parallélisables (worktrees disjoints), ~2h wall-clock.

## Architecture Decisions

1. **3 tasks file-disjoint, parallélisables** — chaque task touche un scope distinct (copy_writer dans moteur_gsg, gsg_lp dans growthcro, _archive_deprecated dans skills/site-capture). Aucun overlap.
2. **`copy_writer.py` split en sub-package `copy/`** plutôt que 3 fichiers à plat dans `moteur_gsg/core/` — préfixe `copy_writer_*` éviterait le sub-package mais 3 fichiers à plat plombent la lisibilité de `core/`. Sub-package mono-concern aligned avec doctrine §AD-1.
3. **Thin re-export pour backward-compat** — `copy_writer.py` reste comme stub d'import (≤30 LOC) pour ne pas casser les ~4 callsites identifiés.
4. **`growthcro/gsg_lp/` archive complet, pas partiel** — l'island a 7 fichiers cohésifs (lp_orchestrator + mega_prompt_builder + repair_loop + brand_blocks + data_loaders), archiver morceau par morceau créerait du noise. Archive complet sous `_archive/growthcro_gsg_lp_2026-05-12_legacy_island/`.
5. **`.gitignore` pattern préventif** — règle `**/_archive_deprecated_*/` empêche la future réintroduction de ce drift dans des active paths.
6. **Capabilities-keeper invoqué avant chaque task** — anti-régression sur les orphans + duplications.

## Technical Approach

### Frontend Components
Non-applicable.

### Backend Services

**Task 001 — Split `copy_writer.py`**

Création de `moteur_gsg/core/copy/` (sub-package mono-concern) :
- `__init__.py` (≤20 LOC, exports publics)
- `prompt_assembly.py` (≤200 LOC) : f-string templating, context injection, token formatting
- `llm_call.py` (≤200 LOC) : Anthropic SDK invocation, response parsing, retry, error handling
- `serializers.py` (≤200 LOC) : output to JSON, dict transformations, evidence_id tagging

`moteur_gsg/core/copy_writer.py` réduit à thin re-export (~25 LOC) :
```python
"""Backward-compat shim. Real implementation moved to moteur_gsg.core.copy/ sub-package."""
from moteur_gsg.core.copy.prompt_assembly import *  # noqa: F401,F403
from moteur_gsg.core.copy.llm_call import *  # noqa: F401,F403
from moteur_gsg.core.copy.serializers import *  # noqa: F401,F403
```

**Task 002 — Archive `growthcro/gsg_lp/`**

Move complet : `git mv growthcro/gsg_lp _archive/growthcro_gsg_lp_2026-05-12_legacy_island/`. Pas de stub backward-compat (l'island est orphan).

**Task 003 — Relocate `_archive_deprecated_2026-04-19` + .gitignore**

Move : `git mv skills/site-capture/scripts/_archive_deprecated_2026-04-19/ _archive/skills_site-capture_deprecated_2026-04-19_root_relocate_2026-05-12/`
+ ajouter `**/_archive_deprecated_*/` à `.gitignore` (avant `_archive/` ou en section anti-pattern dédiée).

### Infrastructure

- Aucun nouveau gate. Reuse `lint_code_hygiene.py`, `typecheck.sh`, `parity_check.sh weglot`, `SCHEMA/validate_all.py`, `audit_capabilities.py`, `agent_smoke_test.sh`, `update_architecture_map.py`.
- CI : aucun changement.

## Implementation Strategy

**Phasing** :
1. **Phase 1** (3 tasks en parallèle) : worktrees disjoints concurrents, file scopes 100% disjoints. ~2h wall-clock.
2. **Phase 2** (closeout) : merge sequential via les completion signals des 3 tasks. Pas de Task 004 séparée (vs Epic 1 où le mypy gate et la doctrine étaient des tasks dédiées) — l'epic closer (mise à jour MANIFEST §12 + master PRD ☑) peut être un commit final post-merge.

**Risk mitigation** :
- Task 001 (split) : capabilities-keeper invoqué AVANT le split. Round-trip test : `python3 -c "from moteur_gsg.core.copy_writer import *"` doit fonctionner post-split.
- Task 002 (archive) : grep pour callsite consumers AVANT move. Si trouvé → STOP escalate.
- Task 003 : vérifier qu'aucun script ne référence le chemin `_archive_deprecated_2026-04-19/` AVANT relocate.
- Gates verts obligatoires après chaque commit.

**Testing approach** :
- Validation via gates existants (lint + typecheck + parity + schemas + 6/6 GSG + smoke + capabilities)
- Pas de pytest contractuel ajouté

## Task Breakdown Preview

3 tasks décomposées :
- **001** — Split copy_writer.py mono-concern (M 2h, parallel)
- **002** — Archive growthcro/gsg_lp/ legacy island (S 1h, parallel)
- **003** — Relocate _archive_deprecated + .gitignore pattern (XS 30min, parallel)

Tous **parallel: true**, file scopes disjoints. Effort total cumul ~3.5h, critical path ~2h avec parallélisation.

## Dependencies

### Externes (humaines)
- **Aucune** — Wave A autonome.

### Externes (techniques)
- Aucune nouvelle deps (mypy + Pydantic déjà installés via Epic 1)

### Internes (code / data)
- main HEAD `ff586be` (post Epic 1 mergé + pushed)
- `scripts/typecheck.sh` actif (gate Epic 1)
- `pyproject.toml` mypy overrides actives
- `growthcro/models/` package existant (Epic 1 livrable)

### Sequencing constraints
- 001 ∥ 002 ∥ 003 (parallel safe, worktrees disjoints obligatoires)
- Aucune dépendance avec Epic 5 POCs skills

## Success Criteria (Technical)

### Mesurables
- [ ] `python3 scripts/lint_code_hygiene.py` exit 0 — **FAIL=0** (vs FAIL=1 baseline)
- [ ] `bash scripts/typecheck.sh` exit 0 (strict 0 + global ≤ budget)
- [ ] `python3 -m mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/` ≤ 1 error (idéalement 0 — duplicate `score_site` disparaît avec Task 003)
- [ ] `bash scripts/parity_check.sh weglot` exit 0 (108 files)
- [ ] `python3 SCHEMA/validate_all.py` exit 0 (3439 files)
- [ ] `python3 scripts/audit_capabilities.py` orphans HIGH=0
- [ ] 6/6 GSG checks PASS (sauf pre-existing creative_route_selector baseline)
- [ ] `bash scripts/agent_smoke_test.sh` 5/5 PASS

### Doctrine
- [ ] 0 régression V26.AF / V3.2.1 / V3.3
- [ ] 3 nouveaux modules dans `moteur_gsg/core/copy/` ≤ 200 LOC chacun, mono-concern
- [ ] `copy_writer.py` thin re-export ≤ 30 LOC
- [ ] 0 file >800 LOC ajouté
- [ ] 0 nouveau `# type: ignore` ajouté

### Architecture
- [ ] Architecture map regénérée (post-archive gsg_lp)
- [ ] `growthcro/gsg_lp/` n'apparaît plus dans `WEBAPP_ARCHITECTURE_MAP.yaml`
- [ ] `moteur_gsg/core/copy/` apparaît avec 3 modules indexed
- [ ] `_archive_deprecated_2026-04-19/` n'apparaît plus dans paths actifs

## Estimated Effort

**Total cumul** : ~3.5h (1 dev sequential)
**Critical path parallèle** : ~2h wall-clock (max(2h, 1h, 30min))

| Task | Effort | Parallel |
|---|---:|---|
| 001 split copy_writer | 2h (M) | yes |
| 002 archive gsg_lp | 1h (S) | yes |
| 003 relocate _archive + .gitignore | 30min (XS) | yes |

**Mathis bandwidth** : pas requis pendant exécution. Review final merge uniquement.

## Tasks Created
- [ ] 001.md - Split copy_writer.py mono-concern (parallel: true)
- [ ] 002.md - Archive growthcro/gsg_lp/ legacy island (parallel: true)
- [ ] 003.md - Relocate _archive_deprecated + .gitignore pattern (parallel: true)

Total tasks: 3
Parallel tasks: 3 (all)
Sequential tasks: 0
Estimated total effort: 3.5 hours
Critical path: ~2 hours
