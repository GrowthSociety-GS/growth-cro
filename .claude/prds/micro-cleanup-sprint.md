---
name: micro-cleanup-sprint
description: 3 micro-actions XS-cleanup pour clôturer la dette résiduelle Wave A — split copy_writer.py mono-concern · archive growthcro/gsg_lp/ legacy island · clore le drift _archive_deprecated dans skills/site-capture/scripts/. Objectif lint FAIL=0 absolu et 0 anti-pattern #10/#8 actif.
status: active
created: 2026-05-12T13:30:00Z
parent_prd: post-stratosphere-roadmap
github_epic: https://github.com/GrowthSociety-GS/growth-cro/issues/35
wave: A
epic_index: 2
ice_score: 324
---

# PRD: micro-cleanup-sprint

> Sub-PRD du master [`post-stratosphere-roadmap`](post-stratosphere-roadmap.md) (FR-2 Epic 2).
> Wave A autonome, scope file-disjoint avec Epic 1 (déjà mergée). 3 tasks parallélisables, ~6h cumul.

## Executive Summary

Post Epic 1 (typing-strict-rollout livré 2026-05-12), 3 micro-violations résiduelles bloquent encore le "stratosphere-clean" :

| Action | Anti-pattern violé | Effort | ICE |
|---|---|---:|---:|
| Split `moteur_gsg/core/copy_writer.py` (376 LOC, multi-concern) | #8 fichier multi-concern | 2h | 324 |
| Archive `growthcro/gsg_lp/` legacy island (7 fichiers, abandoned) | #10 archive dans active path (par extension : "module island sans consommateur") | 1h | 324 |
| Relocate `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` hors active path + `.gitignore` pattern | #10 archive dans active path | 30min | 200 |

Cible : **lint FAIL=0 absolu** · 0 anti-pattern #8/#10 actif sur le tree · 1 mypy error résiduel cleared (duplicate `score_site` module disparaît avec la relocation).

**Coût API** : $0 (cleanup + refactor mécanique only).
**Critical path** : 3 tasks parallélisables (worktrees disjoints) → ~2h wall-clock.

## Problem Statement

### Pourquoi maintenant

1. **Post Epic 1 main est gate-vert sauf 1 FAIL** : le seul lint FAIL est le local junk `_archive_deprecated_2026-04-19/`. Le clore = lint FAIL=0 absolu pour la première fois depuis le cleanup.
2. **`copy_writer.py` (376 LOC) viole l'anti-pattern #8** : mélange assembly prompt + LLM API call + serializers. Toucher ce fichier sans le splitter d'abord = créer de la dette future.
3. **`growthcro/gsg_lp/` est un island legacy** : 7 fichiers (lp_orchestrator + mega_prompt_builder + repair_loop + brand_blocks + data_loaders + README + __init__), aucun consumer actif identifié post-cleanup. Squatte le namespace `growthcro/` sans valeur.
4. **Le 1 mypy error résiduel** (duplicate module `score_site` au scope `_archive_deprecated_2026-04-19/`) disparaît une fois l'archive relocate hors active path. **0 mypy error global atteignable**.
5. **Bloque doctrine clean** : tant que ces 3 micro-violations existent, le `growthcro-strategist` skill ne peut pas reporter "stratosphère-ready 10/10" en dimension Architecture.

### Ce que ce sub-PRD apporte

- 3 commits isolés (1 par task) + 1 commit doctrine commit séparé per CLAUDE.md rule
- `lint FAIL=0` absolu post-merge
- 0 anti-pattern #8/#10 actif
- 1 mypy error → 0 (le duplicate `score_site`)
- `copy_writer.py` redécomposé : `copy_writer_prompt_assembly.py` (≤200 LOC) + `copy_writer_llm_call.py` (≤200 LOC) + `copy_writer_serializers.py` (≤200 LOC) — chaque module mono-concern, importable indépendamment

## User Stories

### US-1 — Mathis (lint FAIL=0 absolu)

*Comme founder qui veut une codebase 100% gate-vert avant scale, je veux que `python3 scripts/lint_code_hygiene.py` retourne FAIL=0 sur main pour la première fois (vs FAIL=1 persistant depuis 2026-05-09), pour pouvoir promouvoir la règle `print-in-pipeline` WARN→FAIL au prochain epic.*

**AC** : `python3 scripts/lint_code_hygiene.py` exit 0 sur main · FAIL=0 affiché en haut · pas de régression WARN/INFO.

### US-2 — Mathis (anti-pattern #8 cleared)

*Comme founder qui consomme `copy_writer.py` depuis 4 callsites différents, je veux que ce fichier soit redécomposé en 3 modules mono-concern (prompt_assembly + llm_call + serializers) pour faciliter les refactors futurs sans risque de cascade.*

**AC** : 3 nouveaux modules dans `moteur_gsg/core/` · chacun ≤200 LOC · old `copy_writer.py` supprimé ou réduit à un thin re-export pour backward-compat · capabilities-keeper validation post-split · 0 régression callsite.

### US-3 — Mathis (gsg_lp legacy archived)

*Comme founder qui maintient `growthcro/` clean, je veux que `growthcro/gsg_lp/` (legacy island sans consumer actif) soit déplacé sous `_archive/` pour libérer le namespace et clarifier l'architecture map.*

**AC** : `growthcro/gsg_lp/` n'existe plus dans le tree actif · `_archive/growthcro_gsg_lp_<date>/` contient tous les fichiers · architecture map regénérée · capabilities orphans HIGH=0 (vérification : si quelqu'un l'importe encore, faille à traiter).

## Functional Requirements (3 tasks)

### FR-1 — Task 001 : Split `copy_writer.py` mono-concern

**Effort** : 2h (M) · **Parallel** : oui (file-disjoint)

- Lire `moteur_gsg/core/copy_writer.py` (376 LOC) et identifier les 3 concerns :
  - Prompt assembly (build f-strings, inject context, format tokens)
  - LLM API call (Anthropic SDK invocation, response parsing, retry/error handling)
  - Serializers (output to JSON, dict transformations, evidence_id tagging)
- Créer 3 modules dans `moteur_gsg/core/copy/` (nouveau sub-package mono-concern) :
  - `prompt_assembly.py` (≤200 LOC)
  - `llm_call.py` (≤200 LOC)
  - `serializers.py` (≤200 LOC)
- `moteur_gsg/core/copy_writer.py` devient un thin re-export (≤30 LOC) pour backward-compat des imports existants
- Run `python3 scripts/audit_capabilities.py` post-split pour vérifier 0 orphan
- Gates : lint exit 0, parity weglot 108, SCHEMA 3439, 6/6 GSG checks PASS
- Commit : `feat(cleanup): split copy_writer.py into 3 mono-concern modules (#<N>)`

### FR-2 — Task 002 : Archive `growthcro/gsg_lp/` legacy island

**Effort** : 1h (S) · **Parallel** : oui (file-disjoint)

- Vérifier d'abord qu'aucun module actif n'importe `growthcro.gsg_lp.*` :
  ```bash
  grep -r "from growthcro.gsg_lp\|import growthcro.gsg_lp" growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/ 2>&1 | grep -v "_archive" | head -20
  ```
- Si imports trouvés → **STOP**, escalate to user (pas d'archive d'un module utilisé)
- Sinon → `git mv growthcro/gsg_lp _archive/growthcro_gsg_lp_2026-05-12_legacy_island/`
- Run `scripts/update_architecture_map.py` (régénère YAML + MD Mermaid sans gsg_lp)
- Run `scripts/audit_capabilities.py` (vérifie 0 orphan HIGH)
- Gates : lint, parity, SCHEMA, capabilities
- Commit : `chore(cleanup): archive growthcro/gsg_lp/ legacy island (no active consumer) (#<N>)`

### FR-3 — Task 003 : Relocate `_archive_deprecated_2026-04-19` + `.gitignore` pattern

**Effort** : 30min (XS) · **Parallel** : oui (file-disjoint)

- Vérifier d'abord présence : `ls skills/site-capture/scripts/_archive_deprecated_2026-04-19/`
- Relocate hors active path : `git mv skills/site-capture/scripts/_archive_deprecated_2026-04-19/ _archive/skills_site-capture_deprecated_2026-04-19_root_relocate_2026-05-12/`
- Ajouter ligne `.gitignore` (si pas déjà présente) :
  ```
  # Anti-pattern #10 prevention : _archive_deprecated_* doit vivre sous _archive/ racine, jamais dans un active path
  **/_archive_deprecated_*/
  ```
- Run lint : doit retourner FAIL=0
- Run mypy global : doit retourner 0 error (le duplicate module `score_site` disparaît)
- Gates : lint, parity, SCHEMA, mypy global
- Commit : `chore(cleanup): relocate _archive_deprecated_2026-04-19 hors active path + .gitignore guard (#<N>)`

## Non-Functional Requirements

### Doctrine immuables (héritées)
- **V26.AF** : prompt persona_narrator ≤8K chars enforced (vacuously — file n'existe plus, mais ne pas réintroduire le pattern)
- **Code doctrine** : tous nouveaux fichiers ≤800 LOC + mono-concern (target ≤200 LOC pour cleanup modules)
- **V3.2.1 + V3.3** : doctrine intacte
- **Schema** : `SCHEMA/validate_all.py` exit 0 pré/post
- **Parity** : `bash scripts/parity_check.sh weglot` exit 0 pré/post
- **6/6 GSG checks** : tous PASS (sauf pre-existing `creative_route_selector` baseline)
- **Capabilities-keeper** : invoqué avant chaque task

### Performance
- copy_writer split : 0 régression latence (imports indirection minimal)
- Architecture map regen : <30s

### Sécurité
- Aucun changement sécurité

## Success Criteria

- [ ] Task 001 closed : 3 modules mono-concern créés, copy_writer.py thin re-export, 0 régression callsite
- [ ] Task 002 closed : growthcro/gsg_lp/ archivé, capabilities orphans HIGH=0
- [ ] Task 003 closed : archive relocate + .gitignore, lint FAIL=0, mypy global=0
- [ ] `python3 scripts/lint_code_hygiene.py` FAIL=0 (de 1 à 0)
- [ ] `bash scripts/typecheck.sh` exit 0 (strict 0 + global ≤603)
- [ ] `python3 -m mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/` ≤1 error (idéalement 0)
- [ ] Architecture map regénérée (post-archive gsg_lp)
- [ ] 0 régression V3.2.1/V3.3/V26.AF
- [ ] Master PRD post-stratosphere-roadmap Epic 2 ☑ checked

## Constraints & Assumptions

### Constraints
- Pas de Notion auto-modify
- Pas de modif doctrine V3.2.1/V3.3
- Pas de modif webapp V28 fonctionnelle
- Pas de génération Sonnet (refactor + moves only)
- Si `growthcro.gsg_lp` a un import actif → STOP, escalate

### Assumptions
- Aucun consumer actif de `growthcro.gsg_lp.*` (à vérifier en début Task 002)
- `_archive_deprecated_2026-04-19/` est OK à relocate (orphan documenté)
- `copy_writer.py` callsites tolèrent un thin re-export (probable : 4 imports actifs, signature préservée)

## Out of Scope

### Hors scope ce sub-PRD
- **`pylint --duplicate-code` deep analysis** (master PRD action 4 optionnelle) → futur sprint dédié si besoin (~2h)
- **Pydantic-iser top 5 suivants** (capture/orchestrator, mode_1/orchestrator, etc.) → sprint follow-up post Epic 2
- **Cleanup imports cassés `mode_1_persona_narrator`** dans mode_3_extend + mode_4_elevate → sprint follow-up doctrine (drift Epic 1 surfacé)
- **Resolve 4 merge-conflict zones in MANIFEST** → sprint doctrine séparé sous validation Mathis
- **Déprécier V26.AF references dans CLAUDE.md** → sprint doctrine séparé

## Dependencies

### Externes (humaines)
- **Aucune** — Wave A autonome.

### Externes (techniques)
- Pydantic v2 (déjà installé)
- mypy 2.1.0 (déjà installé)

### Internes
- main HEAD `ff586be` (post Epic 1 typing-strict-rollout mergé)
- `scripts/lint_code_hygiene.py` (custom linter)
- `scripts/audit_capabilities.py` (orphan detector)
- `scripts/update_architecture_map.py` (idempotent)
- `bash scripts/typecheck.sh` (Epic 1 gate)

### Sequencing constraints
- 001 ∥ 002 ∥ 003 (parallel safe, file-disjoint, worktrees concurrents)
- Pas de dépendance avec Epic 5 POCs skills (si lancé en parallèle, worktree séparé)

---

## Programme — Critical Path

```
WAVE A — 3 micro-tasks parallèles (~2h wall-clock)
  Task 001 split copy_writer (2h)    ┐
  Task 002 archive gsg_lp (1h)        ├─ worktrees disjoints
  Task 003 relocate _archive (30min)  ┘
```

**Première action** : capabilities-keeper invoqué pour valider qu'aucun split prématuré n'a déjà été tenté, puis créer 3 tasks files via CCPM decompose.

---

**Note finale** : ce sub-PRD est intentionnellement le **plus petit** possible. 3 micro-actions ciblées, scope explicite, AC mesurables. Suite logique d'Epic 1 typing-strict-rollout. Une fois fermé : Wave A est 67% done (2/3 epics ; Epic 5 POCs reste en option étalable).
