---
name: typing-strict-rollout
status: backlog
created: 2026-05-12T10:11:22Z
updated: 2026-05-12T10:11:22Z
progress: 0%
prd: .claude/prds/typing-strict-rollout.md
github: (will be set on sync)
parent_prd: post-stratosphere-roadmap
wave: A
ice_score: 360
---

# Epic: typing-strict-rollout

## Overview

Pydantic-iser les 3 fichiers top-coupling identifiés par [CODE_AUDIT §1.2](../../../reports/CODE_AUDIT_2026-05-11.md) — `moteur_gsg/core/visual_intelligence.py` (13 mypy union-attr), `moteur_gsg/core/context_pack.py` (10 dict/TypedDict drift), `growthcro/recos/orchestrator.py` (10 args/returns drift) — pour absorber 37% des 88 mypy errors actives avant le deploy V28 et le scale à 100 clients.

Approche : créer 3 modules de modèles mono-concern (`visual_models.py`, `context_models.py`, `recos_models.py`) ≤200 LOC chacun, refactor file-par-file avec callsites mis à jour, puis activer `mypy --strict` sur le top-3 via overrides `pyproject.toml`. Aucune génération Sonnet, $0 API cost.

## Architecture Decisions

1. **Pydantic v2 (BaseModel + ConfigDict)** plutôt que `dataclasses`, `attrs`, ou `TypedDict` pur — la validation à la frontière inter-module est un objectif explicite (US-1), et Pydantic v2 expose `model_json_schema()` pour interop TS future (US-3).
2. **`ConfigDict(extra='forbid', frozen=True)` par défaut** — défense en profondeur contre schema drift silencieux. `frozen=False` exceptionnel + justification commentaire.
3. **Co-location modèles** : `growthcro/models/` package central (préféré) plutôt que `moteur_gsg/core/_models/` colocaisé. Raison : `recos_models.py` est dans `growthcro/`, `visual_models.py` + `context_models.py` sont dans `moteur_gsg/` — un package central simplifie l'import depuis n'importe où et facilite l'export JSON Schema unifié pour la webapp V28.
4. **Strict typing localisé via overrides** — `[[tool.mypy.overrides]]` strict=true sur top-3 + `growthcro.models.*`, global reste loose pour ne pas bloquer les autres fichiers (absorption progressive en sprints futurs).
5. **3 commits isolés en Phase 2** — un fichier refactoré par commit, gate-vert intermédiaire entre chaque. Évite les rollbacks lourds si discovery in-sprint.
6. **V26.AF immutable** — `persona_narrator.py` consomme `ContextPackOutput` mais son prompt body (≤8K chars assert runtime) **n'est pas touché**. La frontière entre context_pack output et persona prompt assembly reste un assemblage de strings, pas un Pydantic.

## Technical Approach

### Frontend Components
Non-applicable — sprint backend-only. Préparation pour Epic 4 Wave B (deploy V28) via JSON Schema exportable côté TS.

### Backend Services

**3 modules nouveaux** dans `growthcro/models/` :

| Module | LOC max | Modèles principaux | Consommé par |
|---|---:|---|---|
| `visual_models.py` | 200 | `VisualBlock`, `VisualHierarchy`, `VisualScore`, `VisualReport` | `moteur_gsg/core/visual_intelligence.py`, `growthcro/capture/scorer.py` |
| `context_models.py` | 200 | `ContextPackInput`, `ContextPackOutput`, `PageContext`, `ClientContext` | `moteur_gsg/core/context_pack.py`, `moteur_gsg/modes/mode_1/orchestrator.py`, `moteur_multi_judge/orchestrator.py`, `moteur_gsg/core/persona_narrator.py` (lecture seule) |
| `recos_models.py` | 200 | `RecoInput`, `RecoEnriched`, `RecoBatch`, `EvidenceLedgerEntry` | `growthcro/recos/orchestrator.py`, `growthcro/cli/enrich_client.py` |

**3 fichiers refactorisés** :

| Fichier | LOC | mypy errors | Pattern de fix |
|---|---:|---:|---|
| `moteur_gsg/core/visual_intelligence.py` | 308 | 13 | Signature `analyze_visual(...) -> VisualReport` ; internes peuvent rester dict tant que frontière publique typée |
| `moteur_gsg/core/context_pack.py` | 341 | 10 | Signature `build_context_pack(slug: str, page_type: str) -> ContextPackOutput` |
| `growthcro/recos/orchestrator.py` | 610 | 10 | Signature `orchestrate_recos(input: RecoInput) -> RecoBatch` ; args optional explicitement `Optional[...] = None` |

**Callsites consommateurs mis à jour** (5 fichiers) :
- `growthcro/capture/scorer.py`
- `moteur_gsg/modes/mode_1/orchestrator.py`
- `moteur_multi_judge/orchestrator.py`
- `moteur_gsg/core/persona_narrator.py` (lecture du ContextPackOutput, prompt body intact V26.AF)
- `growthcro/cli/enrich_client.py`

### Infrastructure

- **Config mypy** : `[[tool.mypy.overrides]]` dans `pyproject.toml` (créer fichier si absent) — `strict = true` ciblé sur top-3 + `growthcro.models.*`.
- **Gate `scripts/typecheck.sh`** : invoque `mypy --strict` sur top-3, exit 1 si régression. Optionnel : pre-commit hook sur staged files appartenant au scope.
- **CI** : aucun changement requis (pas de pipeline CI actif aujourd'hui), gate manuel via le script.

## Implementation Strategy

**Approche** : 5 tasks, dont 3 totalement parallélisables (file-disjoint) et 2 séquentielles dépendantes.

**Phasage** :
1. **Phase 1** (Tasks 001 + 002 + 003 en parallèle) : pour chaque fileset (visual / context / recos), créer le module Pydantic puis refactor le fichier top-coupling + ses callsites. Commit isolé par fileset.
2. **Phase 2** (Task 004) : activer `mypy --strict` via overrides, créer `scripts/typecheck.sh`. Dépend de 001+002+003 mergées.
3. **Phase 3** (Task 005) : doctrine §TYPING ajoutée, MANIFEST §12 changelog, architecture map regénérée. Dépend de 004.

**Risk mitigation** :
- Round-trip JSON test in-script à chaque création de modèle (round-trip avec un fichier réel `data/captures/.../perception_v13.json` ou `data/recos/.../recos_enriched.json`) avant refactor.
- Gate-vert après chaque commit (lint + parity + schemas + 6/6 GSG checks). Stash + revert si discovery in-sprint.
- `persona_narrator.py` touché en lecture-seule du ContextPackOutput — assert runtime ≤8K chars préservé (V26.AF).
- Pas de touche aux playbooks JSON ni à `data/doctrine/*` (V3.2.1 + V3.3 intacts).

**Testing approach** :
- Pas de pytest contractuel ajouté (out of scope). Validation via gates existants : parity weglot · SCHEMA · 6/6 GSG checks · capabilities-keeper.
- Round-trip Pydantic ↔ JSON validé in-task (test script discardable, pas committé).

## Task Breakdown Preview

5 tasks décomposées :
- **001** — Pydantic-ize visual_intelligence (visual_models.py + refactor + scorer.py callsite)
- **002** — Pydantic-ize context_pack (context_models.py + refactor + 3 callsites)
- **003** — Pydantic-ize recos/orchestrator (recos_models.py + refactor + enrich_client.py callsite)
- **004** — Mypy strict gate (pyproject.toml overrides + typecheck.sh)
- **005** — Doctrine §TYPING + MANIFEST §12 + architecture map regen

Les 3 premières sont **parallel: true** (file scopes disjoints, peuvent tourner en worktrees concurrents). Task 004 dépend de 001+002+003 mergées. Task 005 dépend de 004.

## Dependencies

### Externes (humaines)
- **Aucune** — Wave A autonome, démarrable immédiatement.

### Externes (techniques)
- Pydantic v2 (vérifier `pip show pydantic` en début Task 001 — installer si absent)
- mypy 1.x (vérifier ou installer en début Task 004)

### Internes (code / data)
- Branche `main` à `9a79076` (post post-stratosphere PRD commit)
- `growthcro/config.py` (env reads centralisés — modèles peuvent y référer pour defaults)
- `SCHEMA/*.json` existants (compatibilité round-trip à valider Phase 1)
- Architecture map `WEBAPP_ARCHITECTURE_MAP.yaml` (regen post-merge Task 005)
- CODE_AUDIT §1.2 (source des 33 errors ciblées)

### Sequencing constraints
- 001 ∥ 002 ∥ 003 (parallel safe, worktrees disjoints recommandés)
- 004 dépend de {001, 002, 003} closed
- 005 dépend de 004 closed
- Aucune dépendance avec Epic 2 micro-cleanup (si lancé en parallèle, worktree dédié)
- Aucune dépendance avec Epic 5 POCs skills

## Success Criteria (Technical)

### Mesurables
- [ ] `mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/` ≤ 55 errors (vs 88 baseline)
- [ ] `mypy --strict moteur_gsg/core/visual_intelligence.py moteur_gsg/core/context_pack.py growthcro/recos/orchestrator.py growthcro/models/` exit 0
- [ ] `python3 scripts/lint_code_hygiene.py` exit 0 (FAIL=0)
- [ ] `python3 SCHEMA/validate_all.py` exit 0 (3439 files)
- [ ] `bash scripts/parity_check.sh weglot` exit 0 (108 files baseline)
- [ ] `bash scripts/agent_smoke_test.sh` 5/5 PASS
- [ ] 6/6 GSG checks PASS
- [ ] `python3 scripts/audit_capabilities.py` orphans HIGH=0

### Doctrine
- [ ] 0 régression V26.AF (assert ≤8K chars sur persona_narrator prompt)
- [ ] 0 régression V3.2.1 / V3.3 (playbooks + data/doctrine intacts)
- [ ] 3 modèles modules ≤ 200 LOC chacun (mono-concern)
- [ ] 0 nouveau `# type: ignore` non-justifié
- [ ] CODE_DOCTRINE §TYPING ajouté
- [ ] MANIFEST §12 changelog commit séparé

### Performance
- [ ] `mypy --strict` top-3 < 30s
- [ ] 0 régression latence pipeline capture_full (< 60s sur 1 client × 5 pages baseline)

## Estimated Effort

**Total** : ~34h ≈ 4-5 jours

| Task | Effort | Parallel |
|---|---:|---|
| 001 visual_intelligence | 8h (M) | yes |
| 002 context_pack | 10h (M) | yes (with 001, 003) |
| 003 recos/orchestrator | 12h (M) | yes (with 001, 002) |
| 004 mypy strict gate | 2h (S) | no (depends on 001+002+003) |
| 005 doctrine + manifest | 2h (S) | no (depends on 004) |

**Critical path** : max(001, 002, 003) + 004 + 005 ≈ 12h + 2h + 2h = **16h critical path** si 3 worktrees parallèles.

**Mathis bandwidth** : pas requis pour gates / OAuth / credentials. Review final PR uniquement.

## Tasks Created
- [ ] 001.md - Pydantic-ize visual_intelligence (parallel: true)
- [ ] 002.md - Pydantic-ize context_pack (parallel: true)
- [ ] 003.md - Pydantic-ize recos/orchestrator (parallel: true)
- [ ] 004.md - Mypy strict gate (parallel: false, depends_on [001, 002, 003])
- [ ] 005.md - Doctrine TYPING + Manifest + Architecture map regen (parallel: false, depends_on [004])

Total tasks: 5
Parallel tasks: 3 (001, 002, 003 — file-disjoint, worktrees concurrents)
Sequential tasks: 2 (004 → 005)
Estimated total effort: 34 hours
Critical path (with parallel execution): ~16 hours (max(8,10,12) + 2 + 2)
