---
name: webapp-stratosphere
description: Programme stratégique 8-10 semaines pour finir la webapp V28, intégrer écosystème skills, atteindre niveau "stratosphère" (avant-garde, moat unique agence Growth Society)
status: active
created: 2026-05-11T09:19:02Z
updated: 2026-05-11T09:30:01Z
github_epic: https://github.com/GrowthSociety-GS/growth-cro/issues/14
---

# PRD: webapp-stratosphere

> **PRD vivant**. Mis à jour à chaque epic terminé. Chacun des 8 axes ci-dessous deviendra un sub-PRD détaillé au moment où on l'attaque (pas avant — éviter les specs obsolètes).

## Executive Summary

GrowthCRO est aujourd'hui un audit engine + GSG canonique propre (V27.2-G post-cleanup epic + alignment Codex 2026-05-11). 56 clients V27 runtime rôlés, doctrine V3.2.1 validée, 0 orphans, code doctrine + linter actifs. **Mais** : la webapp PROD est encore du HTML statique V27, la doctrine n'intègre pas la méthodologie CRE (Conversion Rate Experts), le GSG n'a pas livré son premier vrai run hors-SaaS/listicle, et l'écosystème de 16 skills externes audités n'est pas intégré.

Ce programme livre la dernière marche vers le produit "stratosphère" : webapp Next.js scalable 100+ clients, doctrine V3.3 fusion CRE, GSG premier vrai run non-SaaS validé, écosystème skills intégré sans cacophonie, boucle fermée Reality→Experiment→Learning active, + 2 produits agence parallèles (Google Ads + Meta Ads audit).

**Durée** : 8-10 semaines (~50-70 jours-homme avec parallélisation possible)
**Coût API estimé** : ~$30-50 (audits + GSG runs + tests cross-business)
**Critical path** : architecture-map → skill-integration → doctrine-v3-3 → gsg-stratosphere → webapp-v27-completion → webapp-v28-nextjs → agency-products → reality-loop

## Problem Statement

### Pourquoi maintenant

1. **Cleanup epic livré (2026-05-10)** — base code saine, 0 orphans, doctrine code en place. Plus d'excuse d'attendre un refactor.
2. **Codex alignment OK (2026-05-11)** — 6/6 GSG checks PASS, V27.2-G canonique, runtime débloqué.
3. **#13 prompt arch livré** — 80% cacheable, plus de mega-prompt, prêt pour vrai run.
4. **Écosystème skills mature** — 16 skills externes audités (8 installés via page nocodefactory + 8 trouvés skills.sh). Conversion Rate Experts publie sa méthodologie en skill (cro-methodology). Vercel publie microfrontends skill. C'est le bon moment pour absorber.
5. **Agence Growth Society scale** — ~100 clients prévus, le V27 HTML statique ne tient pas.

### Ce qui manque

- **Architecture webapp non-mappée** : chaque conversation Claude re-découvre le tree. Pas de doc source-of-truth machine-readable.
- **Skills intégrés en silo** : risque de cacophonie (Taste vs Brand DNA, lp-creator vs GSG, etc.). Pas de blueprint.
- **Doctrine V3.2.1 incomplète** : pas d'O/CO tables CRE, pas de research-first principle codifié, 69 doctrine_proposals V29 en attente review.
- **GSG en V27.2-G mais non validé hors SaaS-listicle** : Weglot V27.2-D 70.9% reste la seule preuve. Pas de premier run e-com / leadgen / pricing avec multi-judge.
- **Webapp V27 Command Center** : HTML statique, 11.7MB `growth_audit_data.js` à refresh post-cleanup. Panes Audit/Reco/GSG incomplets.
- **Webapp V28 Next.js** : architecture cible existe (`GROWTHCRO_ARCHITECTURE_V1.md`) mais 0% implémenté.
- **Produits agence parallèles** : gads-auditor + meta-ads-auditor disponibles, jamais brandés pour Growth Society.
- **Boucle fermée** : Reality (credentials manquent) + Experiment (0 A/B déclenché) + Learning V29 (69 proposals stagnent).

## User Stories

### US-1 — Mathis (founder, builder)
*Comme founder qui orchestre 100 clients via webapp, je veux que toutes mes conversations Claude/Codex/futur LLM partent de la même photo architecturale machine-readable, pour qu'aucun assistant ne re-découvre le repo à chaque session.*

**AC** : `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` existe, listé dans `CLAUDE.md` init step, généré automatiquement à chaque epic terminé via `scripts/update_architecture_map.py`. Vue Mermaid auto-rendue depuis le YAML.

### US-2 — Mathis (CRO expert)
*Comme expert CRO qui veut atteindre un niveau "avant-garde", je veux que la doctrine V3.3 fusionne notre V3.2.1 avec la méthodologie CRE (Conversion Rate Experts) — incluant O/CO tables, ICE scoring, research-first principle — pour que mes audits livrent des recos basées sur preuves comportementales et pas sur best-practices génériques 2024.*

**AC** : doctrine V3.3 sortie, scorer V3.3 actif, 69 doctrine_proposals reviewés (accept/reject/defer), au moins 3 audits clients re-runs sur V3.3 montrent des recos qualitativement supérieures (Mathis valide à l'œil).

### US-3 — Mathis (GSG director)
*Comme producteur de LPs premium, je veux que le GSG livre son premier vrai run sur 3 page-types non-SaaS-listicle (ex: e-com PDP, leadgen home, pricing comparison) avec multi-judge ≥70%, animations Emil Kowalski intégrées et Impeccable QA layer activé, pour valider que la stratosphère n'est plus une promesse mais un fait livrable.*

**AC** : 3 LPs générées + multi-judge ≥70 sur chaque + 0 régression V26.AF + screenshots desktop+mobile PASS + Mathis valide visuellement.

### US-4 — Agence Growth Society (consultants media buying)
*Comme consultant agence qui audite 100 clients, je veux ouvrir la webapp V28 Next.js et voir l'état audit + recos + GSG live de chaque client en <2 secondes, avec auth + real-time updates Supabase, pour ne plus jamais ouvrir un HTML statique de 11.7MB.*

**AC** : webapp V28 déployée Vercel + Supabase auth + microfrontends scalable + 56 clients live + temps de chargement <2s page client.

### US-5 — Agence Growth Society (offre commerciale)
*Comme agence performance Meta/Google/TikTok, je veux pouvoir vendre 3 audits différents à mes clients (CRO LP + Google Ads + Meta Ads) à partir de la même webapp, pour augmenter le ticket moyen sans déployer 3 outils séparés.*

**AC** : 3 produits audit accessibles depuis la webapp (CRO via notre engine, Google Ads via skill gads-auditor, Meta Ads via skill meta-ads-auditor), branding cohérent, exports Notion-ready, factures unifiées via Stripe.

### US-6 — Mathis (data scientist du moat)
*Comme founder qui veut un moat dans les data accumulées, je veux que la boucle fermée Reality (data réelle) → Experiment (A/B) → Learning (Bayesian update doctrine) tourne sur 3 clients minimum d'ici 3 mois, pour qu'à la fin de l'année on ait 30+ expés mesurées et une doctrine V3.4+ qui apprend.*

**AC** : Reality Layer connecté (credentials GA4/Meta/Google/Shopify/Clarity sur 3 clients), Experiment Engine ayant déclenché 5+ A/B mesurés, Learning V30 ayant proposé ≥10 doctrine updates issues de data réelle (pas audit-based).

## Functional Requirements (8 axes / futurs epics)

### FR-1 — Webapp Architecture Map (Epic #1)
- **Livrable** : `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` (machine) + `WEBAPP_ARCHITECTURE_MAP.md` (Mermaid, humain).
- **Contenu YAML** : tous modules `growthcro/`, `moteur_gsg/`, `moteur_multi_judge/`, `skills/`, `scripts/`, `deliverables/`, `playbook/`, `data/`, `SCHEMA/`. Pour chaque : `purpose` (1 ligne), `inputs` (typed), `outputs` (typed), `depends_on` (paths), `imported_by` (paths), `doctrine_refs` (playbook ou doc), `status` (active/legacy/deprecated), `lifecycle_phase` (onboarding/runtime/qa/learning).
- **Contenu Mermaid** : 1 vue globale + 5 vues détaillées (audit pipeline / GSG pipeline / multi-judge / webapp / reality+experiment+learning).
- **Auto-update** : script `scripts/update_architecture_map.py` regénère le YAML depuis le code (AST scan) après chaque epic terminé.

### FR-2 — Skill Integration Blueprint (Epic #2)
- **Livrable** : `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` + skills installés (~6) + skills exclus documentés.
- **Décisions par skill** :
  - ESSENTIELS (8) : `frontend-design`, `brand-guidelines`, `web-artifacts-builder`, `vercel-microfrontends`, `cro-methodology`, `Emil Kowalski Design`, `Impeccable`, `Figma Implement Design`.
  - ON-DEMAND (6) : `page-cro`, `form-cro`, `signup-flow-cro`, `onboarding-cro`, `paywall-upgrade-cro`, `popup-cro`.
  - EXCLUS (4) : `lp-creator`, `lp-front`, `theme-factory`, `Taste Skill`, `Canvas Design` (5 en fait).
- **Combo packs par contexte** : 
  - "Audit run" : 3 skills max (claude-api + cro-methodology + page-cro on-demand selon page_type)
  - "GSG generation" : 4 skills max (frontend-design + brand-guidelines + Emil Kowalski + Impeccable)
  - "Webapp Next.js dev" : 4 skills max (frontend-design + web-artifacts-builder + vercel-microfrontends + Figma)
- **Anti-cacophonie** : règle "1 parti pris visuel par projet" enforced via documentation `CLAUDE.md` anti-pattern #12 (à ajouter).

### FR-3 — Doctrine V3.3 — CRE Fusion (Epic #3)
- **Livrable** : `playbook/bloc_*_v3-3.json` (7 fichiers updatés) + `data/doctrine/applicability_matrix_v2.json` + `data/doctrine/cre_oco_tables.json` (nouveau).
- **Apports CRE** :
  - O/CO Tables (Objections / Counter-Objections cartographiées par page_type)
  - ICE scoring renforcé (Impact / Confidence / Ease — déjà partiel dans recos)
  - "Don't guess, discover" principle codifié dans `AXIOMES.md`
  - 9-step CRO process intégré comme template d'audit
  - Research-first checklist (visitor surveys, chat logs, support tickets) → ajout au `client_intent.json` schema
- **Review 69 proposals** : Mathis tranche accept/reject/defer pour chacun via doctrine-keeper sub-agent.
- **Migration** : scorer V3.2.1 → V3.3 backward compatible (les 56 clients existants restent scorés V3.2.1 jusqu'au prochain audit, ensuite V3.3).

### FR-4 — GSG Stratosphere (Epic #4)
- **Livrable** : 3 LPs validées multi-judge ≥70 sur 3 page-types non-SaaS-listicle.
- **Cas de test proposés** :
  - **E-com PDP** : Japhy `pdp` (alimentation chien, brand existante)
  - **Leadgen home** : Stripe `home` ou client agence en lead-gen
  - **Pricing comparison** : Linear ou client SaaS B2B en pricing
- **Intégrations** : Emil Kowalski animations dans `visual_system.py` (premium visual layer V27.2-G+). Impeccable QA layer comme post-render gate (potentiellement remplace partie multi-judge `humanlike_judge`).
- **Multi-judge regression check** : chaque run vs Weglot listicle V27.2-D baseline (70.9%). Toute régression >5pt → rollback obligatoire.
- **Pas avant Epic #2 (skill integration) et Epic #3 (doctrine V3.3)** — les deux alimentent le GSG.

### FR-5 — Webapp V27 Completion (Epic #5)
- **Livrable** : `deliverables/GrowthCRO-V27-CommandCenter.html` refresh + `growth_audit_data.js` regen post-cleanup paths.
- **Panes attendus** :
  - Audit pane : 56 clients × 185 pages avec scores par pillar + page-type + verdicts
  - Reco pane : 3045 recos LP-level + 170 step-level avec filtres priorité/effort/lift
  - GSG pane : 5 modes accessibles + brief V2 wizard intégré + outputs HTML preview
- **Sources data refreshees** : ré-exécuter `scripts/build_growth_audit_data.py` post-cleanup (les imports ont changé). Vérifier les chemins migrés `growthcro/*` vs ancien `skills/site-capture/scripts/*`.
- **Pas de nouvelle feature majeure** — juste finir l'existant, livrer un MVP honnête avant Epic #6.

### FR-6 — Webapp V28 Next.js Migration (Epic #6)
- **Livrable** : webapp Next.js 14 + Supabase + Vercel microfrontends déployée.
- **Architecture cible** (`.claude/docs/architecture/GROWTHCRO_ARCHITECTURE_V1.md` à mettre à jour) :
  - Microfrontends : `audit-app`, `reco-app`, `gsg-studio`, `reality-monitor`, `learning-lab`
  - Routing : `microfrontends.json` configuré Vercel
  - Supabase : auth (Mathis + consultants agence) + tables clients/audits/recos/runs + real-time pour updates pipeline
  - APIs : `growthcro/api/server.py` exposée via Vercel edge functions OR FastAPI sur Railway
  - Brand : skill `frontend-design` + `brand-guidelines` activés sur tous les sprints front
- **Skills activés** : `frontend-design`, `web-artifacts-builder`, `vercel-microfrontends`, `Figma Implement Design`.
- **Migration progressive** : les 5 microfrontends développés et déployés un par un, le V27 HTML reste accessible en parallèle pendant la transition.

### FR-7 — Agency Products Extension (Epic #7)
- **Livrable** : 2 nouveaux produits audit accessibles depuis webapp V28.
- **Google Ads Audit** :
  - Skill `gads-auditor` activé (déjà disponible côté Anthropic)
  - Module `growthcro/audit_gads/` créé (pattern similaire à `growthcro/recos/`)
  - Inputs : Google Ads CSV export ou API
  - Outputs : Notion page structuré template agence (sections A-H)
  - Tarif client agence : à définir avec Growth Society
- **Meta Ads Audit** :
  - Skill `meta-ads-auditor` activé
  - Module `growthcro/audit_meta/` créé
  - Inputs : Meta Ads Manager export ou API
  - Outputs : pareil
- **Branding cohérent** : tous les audits Growth Society depuis la même webapp, mêmes templates Notion, même style PDF export.

### FR-8 — Reality / Experiment / Learning Loop (Epic #8)
- **Livrable** : boucle fermée active sur 3 clients minimum, 30+ expés mesurées d'ici Q4.
- **Sub-epics** (Sprints F-L de la roadmap stratégique 2026-05-04, filtrés post-cleanup) :
  - F : "Plug the existing" (partiellement fait par #10 cleanup, restes à wirer)
  - G : Archivage massif (fait par #10)
  - H : Framework cadrage finalisé
  - I : Mode 2 REPLACE pipeline_sequential_4_stages dédié
  - J : Refactor Modes 3-4-5 full impl
  - K : Review 69 doctrine_proposals → V3.3 (MUTUALISÉ avec Epic #3)
  - L : Cross-client validation
- **Reality Layer** : credentials GA4/Meta/Google/Shopify/Clarity sur 3 clients (Mathis collecte). Orchestrator V26.AI dry-run OK, juste env vars manquent.
- **Experiment Engine** : sample-size calculator OK, déclencher 5 A/B mesurés sur les 3 clients pilote.
- **Learning V30** : Bayesian update qui consomme reality data (pas juste audit-based comme V29). 10+ doctrine_proposals data-driven générées.

## Non-Functional Requirements

### Doctrine / Qualité
- **Anti-régression V26.AF** : prompt persona_narrator ≤ 8K chars enforced par assert, jamais bypass.
- **Code doctrine** (`docs/doctrine/CODE_DOCTRINE.md`) : tous nouveaux fichiers ≤ 800 LOC + mono-concern + env via `growthcro/config.py`. Lint exit 0 pré-commit.
- **Capabilities-keeper** : invoké avant tout sprint code (anti-oubli).
- **Doctrine-keeper** : invoké pour toute modif doctrine V3.3.
- **Schema validation** : `SCHEMA/validate_all.py` exit 0 pré/post chaque epic.
- **Parity check** : `bash scripts/parity_check.sh weglot` exit 0 pré/post chaque epic.

### Performance
- Webapp V28 page load < 2s
- Pipeline audit per-client < 5min end-to-end
- GSG run per-LP < 3min (lite mode) / < 8min (avec multi-judge)
- Coût marginal client < $4/mois inclusif tout

### Sécurité
- Clés API dans `.env` (gitignored), jamais commit
- Supabase auth pour webapp V28
- RGPD : data clients hébergée EU (Supabase EU region)

### Documentation
- PRD vivant (ce fichier) updaté à chaque epic terminé
- Architecture map (FR-1) auto-générée
- MANIFEST §12 changelog à chaque epic merge
- Sub-PRDs détaillés créés au moment du sprint (pas en avance)

## Success Criteria

### Globaux (programme entier)
- [ ] 8/8 epics livrés
- [ ] Webapp V28 Next.js déployée + 56 clients live
- [ ] Doctrine V3.3 publiée + scorer actif + 3 audits re-runs validés Mathis
- [ ] GSG : 3 LPs non-SaaS-listicle multi-judge ≥70
- [ ] 2 produits agence parallèles (Google + Meta Ads) accessibles
- [ ] 5 A/B mesurés via Reality Layer + 10 doctrine_proposals data-driven
- [ ] Architecture map auto-mise-à-jour à chaque epic
- [ ] 0 régression V26.AF / V26.AG / V27.2-G doctrines

### Par axe (success criteria détaillés dans sub-PRD au moment du sprint)
- Cf. AC dans US-1 à US-6 ci-dessus

## Constraints & Assumptions

### Constraints
- **Pas de Notion auto-modify** sans demande explicite Mathis
- **Pas de génération Sonnet live** sans gates verts (parity + schemas + lint + 6/6 GSG checks)
- **Pas de mega-prompt** (>8K chars)
- **Pas de réécriture architecture sans validation** (cf cleanup epic risk mitigation : split plan validé avant exécution)
- **`skills/gsg` + `moteur_gsg` restent canoniques**
- **Mode 2 seul dépend de Audit/Reco** (autres modes indépendants)
- **AURA alimenté par contexte+doctrine+business+page_type**, pas autonome

### Assumptions
- API key Anthropic dispo + budget ~$50 sur 8-10 semaines
- Credentials Reality (GA4/Meta/Google/Shopify/Clarity) collectables auprès de 3 clients agence pilote
- 8-10 semaines de focus Mathis (peut être étiré si gros chantier client agence en parallèle)
- Skills externes (cro-methodology, Emil Kowalski, Impeccable) installables sans friction
- Vercel + Supabase plans gratuits suffisent jusqu'à 100 clients (sinon budget à reviser)

## Out of Scope

### Explicitement hors scope ce programme
- **Migration desktop app / mobile native** — webapp uniquement
- **Marketplace public** (vente outil à autres agences que Growth Society) — décision business future
- **AI Agent autonome qui audit-fix-relance sans humain** — Mathis reste in-the-loop
- **GEO Monitor multi-engine** (manque OPENAI + PERPLEXITY keys) — sera un sub-epic futur si budget débloqué
- **Refactor `skills/` god files restants** (5 KNOWN_DEBT tracé par linter) — sprint dédié post-programme
- **Local junk cleanup** (`_archive_deprecated_2026-04-19/` untracked) — Mathis fait `rm -rf` à son goût

### Possibles "Phase 2" (après programme)
- Marketplace public si Growth Society veut commercialiser
- AI Agent autonome (avec safeguards)
- GEO Monitor (ChatGPT/Perplexity/Claude tracking)
- Refactor skills/ residuel
- Migration vers Claude Opus 5+ quand dispo

## Dependencies

### Externes (humaines / process)
- **Mathis review 69 doctrine_proposals** (~30min × 69 = ~3-5h focused work)
- **Mathis collecte credentials 3 clients Reality Layer**
- **Growth Society direction stratégique** : valider tarif + branding produits agence (Epic #7)
- **Mathis valide visuellement** : 3 LPs GSG stratosphère (Epic #4) + 56 clients webapp V28 (Epic #6)

### Externes (techniques / skills)
- Skills installables : `cro-methodology`, `Emil Kowalski Design`, `Impeccable`, `vercel-microfrontends`, + 6 on-demand
- Vercel project créé
- Supabase project créé + EU region
- Anthropic API key valide + budget

### Internes (code / data)
- `growthcro/*` packages (epic cleanup ✓)
- `moteur_gsg/` V27.2-G (alignment Codex ✓)
- `playbook/*.json` V3.2.1 → V3.3 (Epic #3 fait la migration)
- `data/clients_database.json` 56 clients + métadonnées
- `data/captures/<client>/` artefacts (185 pages auditées)
- `data/learning/audit_based_proposals/` (69 proposals)
- Architecture target doc `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (Epic #6 met à jour)

---

## Programme — Phases & Critical Path

```
Phase 1 — Foundation (~1-2 semaines)
  Epic #1 webapp-architecture-map ───────► Epic #2 skill-integration-blueprint
                                                        │
Phase 2 — Doctrine + GSG (~2-3 semaines)                ▼
  Epic #3 doctrine-v3-3-cre-fusion ──────► Epic #4 gsg-stratosphere
                                                        │
Phase 3 — Webapp (~3-4 semaines)                        ▼
  Epic #5 webapp-v27-completion ─────────► Epic #6 webapp-v28-nextjs-migration
                                                        │
Phase 4 — Scale + Loop (~2-3 semaines)                  ▼
  Epic #7 agency-products-extension  ────► Epic #8 reality-experiment-learning-loop
```

**Total estimé** : 8-12 semaines selon parallélisation et profondeur des sub-epics.

**Première action** : créer l'epic technique `webapp-stratosphere/epic.md` qui décompose ce PRD en 8 tasks (1 task = 1 future sub-PRD/sub-epic). Chacun de ces 8 tasks/sub-PRDs sera détaillé au moment du sprint correspondant.
