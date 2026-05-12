---
name: hardening-and-skills-uplift
status: completed
updated: 2026-05-12T07:31:54Z
created: 2026-05-12T07:16:27Z
progress: 100%
prd: .claude/prds/hardening-and-skills-uplift.md
github: https://github.com/GrowthSociety-GS/growth-cro/issues/24
---

# Epic: hardening-and-skills-uplift

## Overview

Programme court (~1 semaine) entre l'epic `webapp-stratosphere` livré 100% et les 5 actions humaines Mathis. **Durcit la base** (hygiene quick-wins + 2 fix security réels du CODE_AUDIT) ET **installe le palier skills suivant** (Top 6 du SKILLS_DISCOVERY : Vercel labs/agent-skills + Trail of Bits + Anthropic webapp-testing + Context7 MCP + 4 MCPs production). 4 epics, critical path ~1 semaine.

## Architecture Decisions

### AD-1 — Programme court, scope précis
Pas un mega-PRD. 4 epics atomiques, chacun ≤1 semaine, livrables binaires (PASS/FAIL). Évite scope-creep.

### AD-2 — Sub-PRDs détaillés AU MOMENT du sprint
Reprise AD-9 du précédent PRD. Le PRD master haut-niveau, sub-PRDs créés à l'exécution de chaque epic. Évite specs stale.

### AD-3 — Parallèle Epic 1 ∥ Epic 2
Scopes disjoints : Epic 1 modifie code Python (`growthcro/`, `moteur_gsg/`, `skills/`, etc.), Epic 2 modifie skills registry + BLUEPRINT.md + CLAUDE.md. Worktrees séparés.

### AD-4 — MCPs ≠ Skills
Skills compte vers cap 8/session ; MCPs server-level (hors compte). Documenté dans BLUEPRINT.md section MCPs.

### AD-5 — Supabase MCP dev-only
Anti-pattern explicite : jamais connecter à projet Supabase prod via MCP. Documenté en `red flag` dans BLUEPRINT.md (Supabase doc le dit aussi).

### AD-6 — Trail of Bits = pre-merge / quarterly
CodeQL build DB 5-15min → trop lourd pour pre-commit. Activation : avant chaque epic merge majeur OU trimestriel.

### AD-7 — Observability = foundation, pas Logfire/Axiom
Epic 4 livre `growthcro/observability/logger.py` (stdlib) + migration. Décision backend (Logfire vs Axiom vs Sentry SDK) → POC séparé futur, hors ce PRD.

### AD-8 — V26.AF + V3.2.1 + V3.3 intacts
Ce PRD ne touche pas la doctrine ni le persona prompt. Aucune régression possible sur ces axes.

## Technical Approach

### Backend Services
- `growthcro/observability/logger.py` NOUVEAU (Epic 4) — module stdlib mono-concern, lecture log level via `growthcro/config.py`, format JSON structuré, correlation ID auto-générée.
- Pas de changement majeur sur `growthcro/{capture, perception, scoring, recos, research, gsg_lp, api, cli, reality, experiment, learning, audit_gads, audit_meta}` — déjà refactorisés par cleanup epic.
- `moteur_gsg/` non touché (sauf Epic 4 migration print → logger sur 2 fichiers).

### Frontend Components
- Aucun changement webapp V27/V28 dans ce PRD. Les skills Vercel installés (Epic 2) prépareront les FUTURS sprints webapp.

### Infrastructure
- 4 MCPs prod ajoutés (Supabase + Sentry + Meta Ads + Shopify) — server-level, n'affecte pas la stack de prod tant que Mathis ne déploie pas.

### Doctrine / Data
- Aucun changement `playbook/*.json` ou `data/doctrine/*`
- `CODE_DOCTRINE.md` étendu (Epic 4) : nouveau §LOG (pattern logger structuré)
- `CLAUDE.md` éventuellement anti-pattern #12 reviewé (Epic 2 si cap skills/session ajusté)

## Implementation Strategy

### Phasing — 3 phases courtes

**Phase 1 — Hardening (Epic 1 ∥ Epic 2, ~3-4 jours)**
Epic 1 et Epic 2 lancés en parallèle sur worktrees disjoints. Foundation pour Phase 2.

**Phase 2 — Equipment (Epic 3, ~1 jour)**
4 MCPs production installés post-Epic 2 (combo packs définis). Mathis OAuth flows (~20min total).

**Phase 3 — Observability (Epic 4, ~4-5 jours)**
Logger module + migration top-10 pipelines + règle linter promue. Foundation pour POC Logfire/Axiom futur.

### Risk mitigation
- **Risk** : `ruff --fix` casse une logique métier subtile. Mitigation : commit isolé `chore: ruff --fix`, run `parity_check.sh weglot` + `update_architecture_map.py` post-fix, revert si régression.
- **Risk** : Skills install (vercel-labs / trailofbits) bloqués par sandbox sécurité (comme #17). Mitigation : fallback procédure manuelle Mathis documentée + commit structurel sans install live.
- **Risk** : Supabase MCP connecté à prod par erreur. Mitigation : documentation explicite + smoke test uniquement sur projet dev.
- **Risk** : Migration print → logger casse stdout/stderr capture downstream (subprocess parsing). Mitigation : logger.info() écrit aussi sur stdout par défaut, behaviour preservé. Tests parity check.
- **Risk** : Context7 MCP overhead trop élevé (sync fetch doc). Mitigation : si dégradation perçue, désactiver ou cache local.

### Rollback plan
Chaque epic = une branche `task/<N>-<short>` mergeable indépendamment à `epic/hardening-and-skills-uplift` puis à `main`. Rollback = `git revert <merge-commit>`. Le PRD master + epic.md restent inchangés.

## Task Breakdown Preview

4 tasks atomiques. Numérotation CCPM ; renommée à l'issue GitHub après sync.

1. **Hygiene Quick-Wins** — ruff --fix + 4 bare except + 4 HIGH bandit tags + 1 archive move + defusedxml + 2 SQL injection fix. *[Phase 1, parallel avec #2]*

2. **Skills Stratosphère S1 Install** — Vercel labs + Trail of Bits + Anthropic webapp-testing + Context7 MCP + skill-creator formalisation + BLUEPRINT.md updates. *[Phase 1, parallel avec #1]*

3. **MCPs Production** — Supabase MCP + Sentry MCP + Meta Ads MCP officiel + Shopify MCP. OAuth flows Mathis. Smoke tests. *[Phase 2, après #2]*

4. **Observability Migration** — `growthcro/observability/logger.py` + migration top-10 pipelines print → logger + règle linter INFO → WARN. *[Phase 3, après #1]*

## Dependencies

### Externes (humaines / process)
- Mathis OAuth flows ~20min (4 MCPs × 5min)
- Mathis crée projet dev Supabase + Sentry si absents
- Mathis OK installation skills externes (sandbox peut bloquer like #17)

### Externes (techniques)
- `npx skills add ...` ou `/plugin install ...` fonctionnels
- `defusedxml` package installable
- Python ≥3.9 (`hashlib.usedforsecurity`)

### Internes (code / data)
- Tout post epic `webapp-stratosphere`
- 2 rapports source : `reports/CODE_AUDIT_2026-05-11.md` + `reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md`
- `scripts/lint_code_hygiene.py` (à étendre Epic 4)
- `growthcro/config.py` (à étendre Epic 4 pour `GROWTHCRO_LOG_LEVEL`)

### Sequencing constraints
- Epic 1 ∥ Epic 2 parallélisables
- Epic 3 → après Epic 2 (combo packs définis)
- Epic 4 → après Epic 1 (linter passe à 0 avant promotion règle)

## Success Criteria (Technical)

- [ ] `python3 scripts/lint_code_hygiene.py` FAIL = 0 sur main (vs 1 actuel = local junk)
- [ ] `bandit` HIGH = 0 actif, MEDIUM B608 = 0, MEDIUM B314 = 0
- [ ] 4 nouveaux skills installés (Vercel bundle, Trail of Bits, webapp-testing, Context7 MCP)
- [ ] `skill-creator` formalisé dans BLUEPRINT.md
- [ ] 4 MCPs prod installés + OAuth complétés + smoke tests PASS
- [ ] `growthcro/observability/logger.py` créé ≤200 LOC mono-concern
- [ ] Top-10 pipelines migrés print → logger (~300 prints converted)
- [ ] Règle linter `INFO[print-in-pipeline]` promue → `WARN`
- [ ] `CODE_DOCTRINE.md` étendu §LOG
- [ ] BLUEPRINT.md updaté avec 3 nouveaux combos (Webapp Next.js dev étendu + Security audit + Production observability) + section MCPs server-level
- [ ] `python3 scripts/audit_capabilities.py` orphans = 0
- [ ] `python3 SCHEMA/validate_all.py` exit 0
- [ ] `bash scripts/parity_check.sh weglot` exit 0
- [ ] `bash scripts/agent_smoke_test.sh` exit 0
- [ ] 6/6 GSG checks PASS
- [ ] Chaque epic merge → MANIFEST §12 changelog entry (commit séparé per CLAUDE.md rule)
- [ ] 0 régression V26.AF / V26.AG / V27.2-G / doctrine V3.3

## Estimated Effort

- **Overall timeline** : ~1 semaine (5-7 jours) avec parallélisation Phase 1.
- **Per task** :
  - Task 1 (Hygiene) : S, 3-4h
  - Task 2 (Skills S1) : S, 2h
  - Task 3 (MCPs) : XS, 1h
  - Task 4 (Observability) : M, 4-5 jours
- **Critical path** : Task 1 (4h) ∥ Task 2 (2h) → Task 3 (1h) → Task 4 (4-5j) ≈ **5-7 jours total**
- **Resources** : Mathis (OAuth flows ~30min total) + Claude (code) + ~$0 API budget (pas de génération Sonnet)
- **Phases parallèles** : Task 1 ↔ Task 2

## Tasks Created

(à créer par décomposition en phase Structure CCPM — voir 28.md / 28.md / 28.md / 28.md)

Total tasks: 4
Parallel tasks: 2 (#24 ↔ #25 en phase 1)
Sequential tasks: 2 (#26 après #25, #27 après #24)
Estimated total effort: 5-7 jours single-threaded · 4-5 jours avec parallélisation
Critical path: #24 ∥ #25 → #26 → #27
