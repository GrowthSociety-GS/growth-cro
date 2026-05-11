---
name: webapp-stratosphere
status: in_progress
created: 2026-05-11T09:21:13Z
updated: 2026-05-11T11:36:46Z
progress: 50%
prd: .claude/prds/webapp-stratosphere.md
github: https://github.com/GrowthSociety-GS/growth-cro/issues/14
---

# Epic: webapp-stratosphere

## Overview

Programme stratégique 8-12 semaines pour livrer le dernier saut produit GrowthCRO. 8 sub-epics couvrant : mapping architecture, intégration écosystème skills externes, fusion doctrine V3.3 (CRE), GSG premier vrai run hors-SaaS-listicle, complétion webapp V27 HTML, migration Next.js+Supabase V28, extension produits agence (Google + Meta Ads audit), boucle fermée Reality→Experiment→Learning. Le PRD est vivant — chacun des 8 axes deviendra un sub-PRD détaillé au moment de son sprint.

## Architecture Decisions

### AD-1 — Le PRD master reste vivant
Plutôt que de créer 8 sub-PRDs détaillés aujourd'hui (qui deviendront stale dans 4 semaines), on garde le PRD master comme source de vérité haut-niveau et on crée chaque sub-PRD AU MOMENT du sprint correspondant. Cela évite la dette de specs.

### AD-2 — Architecture map auto-générée
`scripts/update_architecture_map.py` scanne le code via AST + lit `playbook/`, `SCHEMA/`, agents, et regénère `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`. Le `.md` Mermaid est dérivé du `.yaml`. Évite la divergence map vs réalité.

### AD-3 — Skills "essentiels" auto-load, "on-demand" invocation explicite
Les 8 skills essentiels (frontend-design, brand-guidelines, web-artifacts-builder, vercel-microfrontends, cro-methodology, Emil Kowalski, Impeccable, Figma) sont activés via combo packs par contexte (audit / GSG / webapp). Les 6 on-demand (page-cro, form-cro, signup-flow-cro, onboarding-cro, paywall-upgrade-cro, popup-cro) sont invoqués `/<skill-name>` ponctuellement.

### AD-4 — Doctrine V3.3 backward compatible
Migration progressive : les 56 clients existants restent scorés V3.2.1 jusqu'au prochain audit ; au prochain run, ils basculent V3.3. Pas de re-score forcé global (évite régression silencieuse).

### AD-5 — GSG stratosphère = preuve par 3 page-types non-SaaS-listicle
3 LPs validées multi-judge ≥70 sur e-com PDP / leadgen home / pricing comparison. Si les 3 PASS, on peut affirmer "stratosphère atteinte". Si <3 PASS, on rollback ce qui régresse et on documente.

### AD-6 — Webapp V27 finie AVANT migration V28
On ne lance pas Next.js avant que V27 HTML soit livrable comme MVP honnête. Évite d'avoir 2 webapps inutilisables en parallèle.

### AD-7 — Produits agence parallèles = skill Anthropic + module thin wrapper
`gads-auditor` et `meta-ads-auditor` sont des skills Anthropic complets. On ne réinvente pas l'audit ads — on wrap dans des modules `growthcro/audit_gads/` + `growthcro/audit_meta/` qui pipent vers Notion template agence. Réutilisation maximale.

### AD-8 — Boucle fermée = 3 clients pilotes minimum
Pas 56 clients d'un coup. 3 clients pilote → 5 A/B → 10 doctrine_proposals data-driven → V3.4 (sub-epic futur).

### AD-9 — Skip brainstorming pour le PRD master, mais brainstorm chaque sub-PRD au moment du sprint
Mathis a validé scope haut-niveau (8 epics). Brainstorming détaillé conserve la valeur pour chaque sprint réel : on apprend en cours de route et le sub-PRD reflète la réalité du moment.

## Technical Approach

### Backend Services
- `growthcro/api/server.py` exposée via Vercel edge functions (Epic #6)
- Nouveaux modules : `growthcro/audit_gads/` + `growthcro/audit_meta/` (Epic #7)
- Pas de changement majeur sur `growthcro/{capture, perception, scoring, recos, research, gsg_lp}` — déjà refactorisés par cleanup epic
- `moteur_gsg/` étendu avec animations layer (Epic #4)

### Frontend Components
- V27 HTML : `deliverables/GrowthCRO-V27-CommandCenter.html` refresh (Epic #5)
- V28 Next.js : 5 microfrontends (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) (Epic #6)
- Skills layer activés : frontend-design + brand-guidelines + web-artifacts-builder

### Infrastructure
- Vercel project + microfrontends config (Epic #6)
- Supabase EU region + auth + tables clients/audits/recos/runs (Epic #6)
- Existing : GitHub Actions CI (lint + parity + schemas), `_archive/parity_baselines/`

### Doctrine / Data
- `playbook/bloc_*_v3-3.json` (7 fichiers) (Epic #3)
- `data/doctrine/cre_oco_tables.json` (Epic #3)
- `data/doctrine/applicability_matrix_v2.json` (Epic #3)
- `data/learning/audit_based_proposals/` review (Epic #3 + #8)

## Implementation Strategy

### Phasing — 4 phases

**Phase 1 — Foundation (1-2 semaines, parallel)**
Establish architecture map source-of-truth + skill integration blueprint. Sets the ground rules for all subsequent phases.

**Phase 2 — Doctrine + GSG core (2-3 semaines, séquentiel)**
Doctrine V3.3 (Epic #3) DOIT précéder GSG stratosphère (Epic #4) — le GSG consomme la doctrine. Skills de #2 alimentent le GSG.

**Phase 3 — Webapp completion (3-4 semaines, séquentiel)**
V27 fini (#5) avant V28 démarré (#6). Migration progressive 5 microfrontends.

**Phase 4 — Scale + Loop (2-3 semaines, parallèle possible)**
Agency products (#7) parallèle Reality loop (#8) si ressources OK. Sinon séquentiel.

### Risk mitigation
- **Risk** : doctrine V3.3 introduit régression sur audits existants. Mitigation : V3.2.1 reste actif pour les 56 clients existants ; V3.3 s'applique seulement aux NOUVEAUX audits jusqu'à validation Mathis sur 3 audits re-runs (#3 AC).
- **Risk** : GSG stratosphère régresse vs Weglot V27.2-D baseline. Mitigation : multi-judge regression check obligatoire sur chaque run (#4 AC). Régression >5pt → rollback.
- **Risk** : Webapp V28 prend 6 semaines au lieu de 4. Mitigation : V27 HTML reste live en parallèle (#6 strategy) ; pas de bascule forcée.
- **Risk** : Skills externes deviennent obsolètes / cassent. Mitigation : versions épinglées dans `requirements.txt` + sub-PRDs notent le SHA skill au moment du sprint.
- **Risk** : Credentials Reality Layer 3 clients pas collectables. Mitigation : Reality Loop (#8) reporté Phase 5 hors programme si bloqué — n'affecte pas #1-#7.

### Rollback plan
Chaque epic = une branche `epic/<sub-epic-name>` mergeable indépendamment à `main`. Rollback = `git revert <merge-commit>`. Le PRD master + epic.md restent inchangés.

## Task Breakdown Preview

Ces 8 tasks correspondent aux 8 sub-PRDs/sub-epics à créer au moment du sprint. Numérotation pour CCPM ; renommée à l'issue GitHub après sync.

1. **Webapp Architecture Map** — YAML + Mermaid + auto-update script. *[Phase 1, parallel]*
2. **Skill Integration Blueprint** — 16 skills audités, combo packs par contexte, installation des 8 essentiels (sauf 6 on-demand). *[Phase 1, parallel after #1]*
3. **Doctrine V3.3 CRE Fusion** — bloc_v3-3 + cre_oco_tables + applicability_matrix_v2 + review 69 proposals. *[Phase 2, sequential after #2]*
4. **GSG Stratosphere** — 3 LPs non-SaaS-listicle + Emil Kowalski animations + Impeccable QA + multi-judge regression. *[Phase 2, sequential after #3]*
5. **Webapp V27 Completion** — V27 HTML refresh + growth_audit_data.js regen post-cleanup + 56 clients live. *[Phase 3, parallel with #4 if resources]*
6. **Webapp V28 Next.js Migration** — Next.js + Supabase + vercel-microfrontends + 5 microfrontends. *[Phase 3, sequential after #5]*
7. **Agency Products Extension** — gads-auditor + meta-ads-auditor + modules growthcro/audit_{gads,meta}/ + Notion template intégration. *[Phase 4, parallel with #8]*
8. **Reality / Experiment / Learning Loop** — 3 clients pilote credentials + 5 A/B mesurés + V30 Bayesian update data-driven. *[Phase 4, parallel with #7]*

Total : 8 tasks. Parallel possible : #1 → #2 (en partie), #4 ↔ #5, #7 ↔ #8. Critical path : #1 → #2 → #3 → #4 → #5 → #6 → (#7 ∥ #8) ≈ 8-12 semaines.

## Dependencies

### External (humaines / process)
- Mathis review 69 doctrine_proposals (~3-5h focused)
- Mathis collecte credentials 3 clients Reality Layer
- Growth Society direction tarif + branding produits agence (#7)
- Mathis valide visuellement LPs GSG (#4) + webapp V28 (#6)

### External (techniques / skills)
- Skills installables : cro-methodology, Emil Kowalski, Impeccable, vercel-microfrontends + 6 on-demand
- Vercel + Supabase projects créés EU region
- Anthropic API key + budget ~$50

### Internal (code / data)
- Tout existing post cleanup epic + alignment Codex
- Architecture target `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (Epic #6 met à jour)

### Sequencing constraints
- #1 → all (architecture map = source of truth pour tous)
- #2 → #3, #4, #6 (skill integration blueprint définit ce qui s'utilise où)
- #3 → #4 (GSG consomme doctrine)
- #5 → #6 (V27 livré avant V28 démarré)
- #7 et #8 parallélisables si ressources

## Success Criteria (Technical)

- [ ] `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` + `.md` existent, à jour
- [ ] `scripts/update_architecture_map.py` exit 0, regénère le YAML
- [ ] `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` existe
- [ ] 8 skills essentiels installés / 6 on-demand documentés
- [ ] `playbook/bloc_*_v3-3.json` 7 fichiers existent + `SCHEMA/validate_all.py` exit 0
- [ ] 69 doctrine_proposals reviewées (accept/reject/defer)
- [ ] 3 LPs GSG non-SaaS-listicle multi-judge ≥70 chacune
- [ ] V27 HTML `growth_audit_data.js` refresh + 56 clients accessibles
- [ ] Webapp V28 déployée Vercel + Supabase live
- [ ] Produits agence Google Ads + Meta Ads accessibles depuis V28
- [ ] 3 clients Reality Layer connectés + 5 A/B mesurés + 10 doctrine_proposals data-driven
- [ ] Linter exit 0, schemas exit 0, parity exit 0 sur main à chaque epic merge
- [ ] 0 régression V26.AF / V26.AG / V27.2-G
- [ ] `MANIFEST §12` changelog entry à chaque epic merge

## Estimated Effort

- **Overall timeline** : 8-12 semaines avec parallélisation possible (8 minimum si tout va bien et Mathis disponible focus).
- **Per task** (rough — sub-PRD au moment du sprint affine) :
  - Task 1 (architecture-map) : S, 3 jours
  - Task 2 (skill-integration) : S, 2 jours
  - Task 3 (doctrine-v3-3) : M, 5 jours
  - Task 4 (gsg-stratosphere) : L, 7-10 jours
  - Task 5 (webapp-v27-completion) : M, 5 jours
  - Task 6 (webapp-v28-nextjs) : XL, 3-4 semaines
  - Task 7 (agency-products) : M, 4 jours
  - Task 8 (reality-loop) : XL, 3 semaines (mais étalable sur le programme)
- **Critical path** : #1 → #2 → #3 → #4 → #5 → #6 ≈ 7-8 semaines
- **Resources** : Mathis (review + validation visuelle + credentials) + Claude (code) + ~$30-50 API budget
- **Phases parallèles possibles** : #4 ↔ #5, #7 ↔ #8

## Tasks Created

- [x] #16 — Webapp Architecture Map (YAML + Mermaid, vivant) — S/2-3j (parallel: false, deps: —)
- [x] #17 — Skill Integration Blueprint (16 skills, combo packs anti-cacophonie) — S/2j (parallel: false, deps: #16)
- [x] #18 — Doctrine V3.3 CRE Fusion — M/4-5j (parallel: false, deps: #16, #17)
- [ ] #19 — GSG Stratosphere (3 LPs non-SaaS-listicle ≥70) — L/7-10j (parallel: false, deps: #17, #18)
- [x] #20 — Webapp V27 Completion (HTML refresh + 56 clients live) — M/4-5j (parallel: true with #19, deps: #16)
- [ ] #21 — Webapp V28 Next.js Migration — XL/3-4 semaines (parallel: false, deps: #17, #20)
- [ ] #22 — Agency Products Extension (Google + Meta Ads) — M/3-4j (parallel: true with #23, deps: #21)
- [ ] #23 — Reality / Experiment / Learning Loop — XL/3 semaines étalable (parallel: true with #22, deps: #18, #21)

Total tasks: 8
Parallel tasks: 3 paires possibles (#19↔#20, #22↔#23, partiellement #17↔#20)
Sequential tasks: 5 sur critical path
Estimated total effort: 70-90 jours-homme single-threaded · 40-60 avec parallélisation
Critical path: #16 → #17 → #18 → #19 → #20 → #21 (~7-8 semaines)
Programme total : 8-12 semaines
