---
name: typing-strict-rollout
description: Pydantic-iser les 3 fichiers top-coupling (visual_intelligence + context_pack + recos/orchestrator) pour absorber 37% des mypy errors (88 → ≤55) AVANT scale 100 clients. Sub-PRD Epic 1 du master post-stratosphere-roadmap. Wave A autonome, scope file-disjoint, 4-5j.
status: active
created: 2026-05-12T10:00:00Z
parent_prd: post-stratosphere-roadmap
wave: A
epic_index: 1
ice_score: 360
---

# PRD: typing-strict-rollout

> Sub-PRD du master [`post-stratosphere-roadmap`](post-stratosphere-roadmap.md) (FR-1 Epic 1).
> Activable immédiatement — aucune dépendance Mathis humaine.
> Worktree dédié : scope file-disjoint avec Epic 2 micro-cleanup (peuvent tourner en parallèle).

## Executive Summary

Le programme `hardening-and-skills-uplift` a livré bandit HIGH=0 et observability foundation. Reste 88 mypy errors actifs sur l'arbre Python — dont **33 concentrés sur 3 fichiers top-coupling** identifiés par [CODE_AUDIT_2026-05-11.md §1.2](../../reports/CODE_AUDIT_2026-05-11.md) :

| Fichier | mypy errors | Pattern dominant | LOC |
|---|---:|---|---:|
| `moteur_gsg/core/visual_intelligence.py` | 13 | union-attr (Optional/None déréférencé) | 308 |
| `moteur_gsg/core/context_pack.py` | 10 | dict / TypedDict drift | 341 |
| `growthcro/recos/orchestrator.py` | 10 | retours hétérogènes, args optional | 610 |
| **Total cible** | **33** | | **1259** |

Pydantic-iser ces 3 fichiers absorbe **37% des erreurs mypy actives** (33/88 → ≤55 restant). Permet d'activer `mypy --strict` sur le top-3 et de partir avec un typage solide avant le deploy V28 (Epic 4 Wave B) et le scale 100 clients.

**Durée** : 4-5 jours (M effort).
**Coût API** : $0 (refactor + types only — aucune génération Sonnet).
**Critical path** : Phase 1 (modèles Pydantic) → Phase 2 (callsites) → Phase 3 (strict gate).

## Problem Statement

### Pourquoi maintenant

1. **Avant scale 100 clients** : `recos/orchestrator.py` orchestre les recos enrichies sur 56 clients × 185 pages = 3045 recos. Si on scale à 100 clients sans types stricts, chaque drift de schema produit des erreurs silencieuses en prod.
2. **Avant deploy V28 (Epic 4 Wave B)** : la webapp Next.js V28 consomme les outputs de `recos/orchestrator.py` via Supabase. Un schema mal typé côté Python = drift garanti côté TypeScript.
3. **Top-coupling = blast radius énorme** : ces 3 fichiers sont consommés par capture/scorer.py, mode_1/orchestrator.py, multi_judge/orchestrator.py, gsg_lp/lp_orchestrator.py. Tout le pipeline en dépend.
4. **Window stable post-hardening** : main `d1cba58` est gate-vert intégral. Toucher le typing maintenant ne risque pas d'interférer avec d'autres chantiers en cours (Wave A autonome, scope disjoint Epic 2).

### Ce que ce sub-PRD apporte

- 3 modules de modèles Pydantic mono-concern (≤200 LOC chacun) : `visual_models.py`, `context_models.py`, `recos_models.py`.
- Refactor des 3 fichiers top-coupling : signatures, returns, et args typés `BaseModel` au lieu de `dict`/`Optional[dict]`.
- Callsites mis à jour (consommateurs explicitement listés ci-dessous).
- `mypy --strict` activé sur le top-3 via `mypy.ini` ou `pyproject.toml` overrides.
- Couverture: 88 mypy → **≤55**. Régression-proof via gates parity + schemas + 6/6 GSG checks.

## User Stories

### US-1 — Mathis (scale-readiness)

*Comme founder qui va passer de 56 à 100 clients sur V28, je veux que les contrats de données entre capture → scoring → recos soient des modèles Pydantic validés à la frontière, pour qu'un schema drift se manifeste comme une `ValidationError` explicite plutôt qu'un `KeyError` 3 fichiers plus loin.*

**AC** :
- 3 modules de modèles Pydantic existants (`visual_models.py`, `context_models.py`, `recos_models.py`) ≤200 LOC chacun, mono-concern.
- Tous les `dict[str, Any]` retours/args des 3 fichiers top-coupling remplacés par `BaseModel` ou `TypedDict` strict.
- `pytest tests/ -x` (s'il existe une suite) ou parity check exit 0 — 0 régression.

### US-2 — Mathis (mypy hygiene avant deploy)

*Comme founder, je veux que mypy passe de 88 → ≤55 errors et que `mypy --strict` soit actif sur les 3 fichiers cible, pour que la dette de typing soit absorbable en 1-2 sprints suivants et que les prochains fichiers Pydantic-isés bénéficient de la traction.*

**AC** :
- `mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/` retourne ≤ 55 errors (vs 88 baseline).
- `mypy --strict moteur_gsg/core/visual_intelligence.py moteur_gsg/core/context_pack.py growthcro/recos/orchestrator.py` exit 0.
- Configuration capturée dans `pyproject.toml` ou `mypy.ini` (versionnée).
- 0 nouveau `# type: ignore` ajouté sans justification commentaire.

### US-3 — Mathis (interop TypeScript futur V28)

*Comme producteur webapp V28, je veux que les schémas Pydantic de `recos_models.py` puissent être exportés en JSON Schema pour générer côté TypeScript via `quicktype` ou `pydantic-to-typescript`, pour que les contrats Python ↔ Next.js restent alignés.*

**AC** :
- `recos_models.py` expose `model_json_schema()` testable manuellement.
- Pas d'`Any` non-justifié dans les modèles `recos_models.py` (visible côté TS sinon).
- Note dans la doctrine code (`CODE_DOCTRINE.md`) : "modèles Pydantic à frontière webapp → préférer `BaseModel` avec `model_config = ConfigDict(extra='forbid')`".

## Functional Requirements (3 phases)

### FR-1 — Phase 1 : Modèles Pydantic mono-concern (J1-J2)

- **Livrable** : 3 nouveaux modules dans `growthcro/models/` (ou colocaisés `moteur_gsg/core/_models/`, decision in-sprint) :
  - `visual_models.py` : `VisualBlock`, `VisualHierarchy`, `VisualScore`, `VisualReport` — modèles consommés par `visual_intelligence.py`. Cibler les 13 union-attr (Optional/None déréférencé) en rendant les fields obligatoires ou `Optional[...] = None` avec validation explicite.
  - `context_models.py` : `ContextPackInput`, `ContextPackOutput`, `PageContext`, `ClientContext` — modèles consommés par `context_pack.py`. Cibler les 10 dict/TypedDict drift.
  - `recos_models.py` : `RecoInput`, `RecoEnriched`, `RecoBatch`, `EvidenceLedgerEntry` — modèles consommés par `recos/orchestrator.py`. Cibler les 10 args optional/returns hétérogènes.
- **Contrainte** : chaque module ≤ 200 LOC, mono-concern (modèles uniquement, pas de logique métier).
- **`model_config`** : `ConfigDict(extra='forbid', frozen=True)` par défaut. `frozen=False` exceptionnel + justification commentaire.
- **Doctrine** : code doctrine §AD-1 (mono-concern) + §AD-2 (env via config) respectée.
- **Schema validation** : compatible avec JSON outputs existants `data/captures/<slug>/<page_type>/perception_v13.json`, `data/recos/<slug>/<page_type>/recos_enriched.json` (round-trip test in-script).

### FR-2 — Phase 2 : Refactor 3 fichiers top-coupling (J2-J4)

- **Livrable** : 3 fichiers cibles utilisent les modèles Pydantic en signatures et retours.
- **Scope précis** :
  - `moteur_gsg/core/visual_intelligence.py` (308 LOC, 13 errors)
    - Signatures publiques : `analyze_visual(...) -> VisualReport`, plus de `dict[str, Any]`
    - Internes : variables intermédiaires peuvent rester dict tant que la frontière publique est typée
    - Cible : `mypy --strict` exit 0 sur ce fichier
  - `moteur_gsg/core/context_pack.py` (341 LOC, 10 errors)
    - Signature : `build_context_pack(slug: str, page_type: str) -> ContextPackOutput`
    - Inputs : `PageContext` et `ClientContext` modèles validés
    - Cible : `mypy --strict` exit 0
  - `growthcro/recos/orchestrator.py` (610 LOC, 10 errors)
    - Signature : `orchestrate_recos(input: RecoInput) -> RecoBatch`
    - Args optional explicitement `Optional[...] = None` au lieu de `dict | None` ambigus
    - Cible : `mypy --strict` exit 0
- **Callsites consommateurs** (à mettre à jour) :
  - `growthcro/capture/scorer.py` — consomme visual_intelligence
  - `moteur_gsg/modes/mode_1/orchestrator.py` — consomme context_pack
  - `moteur_multi_judge/orchestrator.py` — consomme context_pack + recos
  - `moteur_gsg/core/persona_narrator.py` — consomme context_pack (⚠️ V26.AF immutable — prompt ≤8K chars, ne pas toucher le prompt body)
  - `growthcro/cli/enrich_client.py` — consomme recos/orchestrator
- **Approche** : Phase 2 commit-par-fichier (3 commits isolés). Chaque commit gate-vert (lint + parity + schemas + 6/6 GSG checks).

### FR-3 — Phase 3 : Gate strict + doc (J5)

- **Livrable** : config `mypy --strict` sur le top-3, doc, validation finale.
- **Actions** :
  - Ajouter section `[tool.mypy]` dans `pyproject.toml` (ou créer `mypy.ini`) :
    ```toml
    [tool.mypy]
    python_version = "3.11"
    strict = false  # global reste loose pour ne pas bloquer

    [[tool.mypy.overrides]]
    module = [
      "moteur_gsg.core.visual_intelligence",
      "moteur_gsg.core.context_pack",
      "growthcro.recos.orchestrator",
      "growthcro.models.*",
    ]
    strict = true
    ```
  - Étendre `scripts/lint_code_hygiene.py` ou créer `scripts/typecheck.sh` qui invoque mypy sur le top-3 et exit 1 si régression sur ces fichiers.
  - Optionnel : pre-commit hook qui exécute typecheck sur staged files appartenant au top-3.
  - **Doctrine** : ajouter §AD-NEW `TYPING` dans `docs/doctrine/CODE_DOCTRINE.md` : "Tout nouveau fichier à frontière inter-module (consommé par ≥2 modules) doit exposer Pydantic models en signatures publiques. `dict[str, Any]` interdit en frontière."
  - **MANIFEST §12** : changelog `2026-05-XX — Typing Strict Rollout: 3 top-coupling files Pydantic-isés, mypy 88 → N`.

## Non-Functional Requirements

### Doctrine immuables (héritées)

- **V26.AF** : prompt persona_narrator ≤ 8K chars enforced. **JAMAIS touché par ce PRD.** `persona_narrator.py` consomme `ContextPackOutput` mais le prompt body reste intact.
- **Code doctrine** : modèles Pydantic ≤ 200 LOC, mono-concern, env via `growthcro/config.py`. Linter exit 0 obligatoire pré-commit.
- **V3.2.1 + V3.3** : doctrine intacte. Aucun touche `playbook/*.json` ni `data/doctrine/*`.
- **Schema validation** : `SCHEMA/validate_all.py` exit 0 pré/post chaque phase.
- **Parity check** : `bash scripts/parity_check.sh weglot` exit 0 pré/post chaque phase (108 files match baseline).
- **6/6 GSG checks** : `scripts/check_gsg_*.py` tous PASS post-Phase 2 (le scoring GSG dépend de context_pack).
- **Capabilities-keeper** : invoqué avant Phase 1 pour valider qu'aucun modèle Pydantic n'existe déjà dans `growthcro/models/`.

### Performance

- `mypy --strict` sur top-3 : < 30s sur main (mesure baseline en début de Phase 3).
- Round-trip JSON Pydantic : ≤ 5ms par enregistrement (capture.json ~50KB, recos_enriched.json ~30KB).
- 0 régression latence pipeline (capture_full < 60s sur 1 client × 5 pages baseline).

### Sécurité

- `ConfigDict(extra='forbid')` par défaut → rejette les champs inattendus = défense en profondeur.
- Pas de désérialisation depuis input utilisateur non-validé (les modèles consomment des JSON déjà passés par `SCHEMA/validate_all.py`).
- 0 hardcoded secret maintenu, 0 env reads outside config maintenu.

### Documentation

- PRD vivant (ce fichier) updaté à chaque phase terminée (cocher la phase, ajuster scope si discovery).
- MANIFEST §12 commit séparé en fin de sprint (per CLAUDE.md rule).
- Doctrine code §TYPING ajoutée Phase 3.
- Architecture map regénérée via `scripts/update_architecture_map.py` (idempotent).

## Success Criteria

### Phase 1 (modèles)
- [ ] 3 modules Pydantic créés ≤ 200 LOC chacun
- [ ] Round-trip JSON test in-script pass (model ↔ existing data file)
- [ ] `lint_code_hygiene.py` exit 0
- [ ] Capabilities-keeper validation pre-commit

### Phase 2 (refactor)
- [ ] 3 fichiers top-coupling refactorisés, 3 commits isolés
- [ ] Callsites consommateurs mis à jour (5 fichiers listés)
- [ ] `mypy --strict` exit 0 sur top-3 individuellement
- [ ] 6/6 GSG checks PASS
- [ ] Parity check exit 0
- [ ] SCHEMA/validate_all exit 0

### Phase 3 (gate)
- [ ] `pyproject.toml` ou `mypy.ini` overrides committed
- [ ] `mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/` ≤ 55 errors (vs 88 baseline)
- [ ] CODE_DOCTRINE §TYPING ajouté
- [ ] MANIFEST §12 changelog commit séparé
- [ ] Architecture map regénérée

### Globaux
- [ ] 0 régression V26.AF / V26.AG / V27.2-G / doctrine V3.3
- [ ] 0 régression parity weglot baseline
- [ ] 0 nouveau `# type: ignore` non-justifié

## Constraints & Assumptions

### Constraints
- **Pas de Notion auto-modify**
- **Pas de modification doctrine V3.2.1 / V3.3** (playbook/bloc_*.json intacts)
- **Pas de modification webapp V28 fonctionnelle** (mais préparation interop Phase 3)
- **V26.AF immutable** : `persona_narrator.py` prompt body intact
- **Pas de Pydantic v1** : Pydantic v2 obligatoire (déjà installé via deps)
- **Skill cap ≤ 8/session** : combo "Webapp Next.js dev" approprié si refactor touche frontière TS, sinon combo léger (skill-creator + Vercel react-best-practices off, focus mypy)

### Assumptions
- Pydantic v2 disponible (vérifier `pip show pydantic`)
- mypy 1.x disponible (vérifier `pip show mypy`) — si non, `pip install mypy` en Phase 3
- Pas de `pytest` suite contractuelle existante sur ces 3 fichiers (vérifier — si existe, ne pas casser)
- `pyproject.toml` existe et accepte des `[tool.mypy]` overrides

## Out of Scope

### Explicitement hors scope ce sub-PRD
- **Pydantic-iser le reste du codebase** (87 autres fichiers) → futur sprint si Phase 3 prouve la traction
- **Génération automatique TypeScript** via `pydantic-to-typescript` → Epic 4 Wave B deploy V28
- **Tests unitaires pytest contractuels** sur ces 3 fichiers → sprint suivant si gap identifié
- **Refactor `persona_narrator.py`** prompt — V26.AF immutable
- **Migration vers `attrs` ou `dataclasses`** — Pydantic v2 est le choix
- **Strict mypy global** sur tout le tree → trop disruptif, après absorption progressive

### Possibles "Phase 2" suite ce sub-PRD
- Pydantic-iser top 5 suivants (capture/orchestrator.py, mode_1/orchestrator.py, multi_judge/orchestrator.py, gsg_lp/lp_orchestrator.py, scorer.py)
- Export JSON Schema → TS pour webapp V28
- Tests pytest contractuels (1 test par modèle)

## Dependencies

### Externes (humaines)
- **Aucune** — Wave A autonome.

### Externes (techniques)
- Pydantic v2 (vérifier `pip show pydantic` en début Phase 1)
- mypy 1.x (vérifier ou installer en début Phase 3)

### Internes (code / data)
- État main `d1cba58` post `hardening-and-skills-uplift`
- `growthcro/config.py` (env reads centralisés — modèles peuvent y référer pour defaults)
- `SCHEMA/*.json` existants (compatibilité round-trip à valider)
- Architecture map `WEBAPP_ARCHITECTURE_MAP.yaml` (regen post-merge)
- CODE_AUDIT §1.2 (source des 33 errors ciblées)

### Sequencing constraints
- Phase 1 → Phase 2 (modèles avant refactor)
- Phase 2 → Phase 3 (refactor avant gate strict)
- Aucune dépendance avec Epic 2 micro-cleanup (worktree parallèle safe)
- Aucune dépendance avec Epic 5 POCs skills (worktree parallèle safe)

---

## Programme — Phases & Critical Path

```
PHASE 1 — Modèles Pydantic (J1-J2, ~12h)
  visual_models.py       ┐
  context_models.py      ├─ peuvent être écrits en parallèle (file disjoint)
  recos_models.py        ┘
       │
PHASE 2 — Refactor top-coupling (J2-J4, ~16h)
  visual_intelligence.py refactor + callsites    (J2-J3)
  context_pack.py refactor + callsites           (J3)
  recos/orchestrator.py refactor + callsites     (J4)
       │
PHASE 3 — Gate strict + doc (J5, ~6h)
  mypy.ini / pyproject.toml overrides
  scripts/typecheck.sh (optionnel)
  CODE_DOCTRINE.md §TYPING
  MANIFEST §12 changelog
  Architecture map regen
```

**Critical path** : Phase 1 (12h) → Phase 2 (16h) → Phase 3 (6h) ≈ **34h ~ 4-5 jours**.

**Première action** : capabilities-keeper invoqué pour valider qu'aucun module `growthcro/models/` n'existe déjà, puis créer la structure `growthcro/models/__init__.py` et démarrer `visual_models.py`.

---

**Note finale** : ce sub-PRD est intentionnellement focalisé sur les 3 fichiers top-coupling. Le reste de la dette mypy (55 errors restants après ce sprint) sera adressée en sprints follow-up dédiés, fichier-par-fichier, avec le pattern établi ici.
