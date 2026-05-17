---
name: webapp-product-ux-reconstruction-2026-05
description: Refonte totale de l'expérience produit/UX de la webapp GrowthCRO sans réécriture du socle backend. 5 espaces (Command Center, Clients, Audits & Recos, GSG Studio, Advanced Intelligence), worker liveness visible, GSG Studio E2E réel, Module Maturity Model honnête.
status: backlog
created: 2026-05-17T15:00:00Z
---

# PRD: webapp-product-ux-reconstruction-2026-05

> Source de vérité primaire : [`.claude/docs/state/WEBAPP_PRODUCT_AUDIT_2026-05-17.md`](../docs/state/WEBAPP_PRODUCT_AUDIT_2026-05-17.md).
> Ce PRD résume sans dupliquer. En cas de conflit : la source de vérité gagne.

## Executive Summary

La webapp GrowthCRO V28 (Next.js single shell + Supabase EU, locked D1.A 2026-05-14) est un **produit core viable** (≈60% des routes E2E fonctionnelles : home, clients, recos, learning, experiments, doctrine, settings, audits drill-down) entouré de **skeleton honnêtes** (Reality, GEO, Scent, GSG viewer ≈25%) et de **dead UI** (audit-gads, audit-meta, CommandCenterTopbar legacy ≈15%). Le socle technique est sain. **Ce qui ne va pas, c'est l'expérience produit posée par-dessus.**

Ce PRD organise une **refonte UX/produit totale** au-dessus du socle existant, sans réécriture backend. On garde Next.js single shell, Supabase, worker daemon polling, les moteurs Python (Audit, Reco, GSG, multi-judge, Reality, GEO), doctrine V3.2.1, Brand DNA, AURA, Opportunity Layer, Gates. On reconstruit information architecture (5 espaces), navigation workflow-first, Command Center actionnable, GSG Studio E2E réel, Client Workspace progressive disclosure, Audit/Reco workspace orchestré (capture → score → recos chained), worker liveness visible, système d'édition global, Module Maturity Model honnête, design system productif calme.

Deux modules sont déférés à des research/decision spikes avant tout UI build :
- **Reality Layer** (Meta/Google/TikTok/GA4/Shopify/Clarity) : architecture + UX préparées, **backend wiring deferred** (coût/value Mathis pending).
- **Learning Layer** : **OPEN QUESTION** sur l'approche fondamentale (Bayesian doctrine update vs LLM-as-judge vs RAG outcome-driven vs skills evolutifs vs memory files). Research spike avant build UI.

## Problem Statement

**Pourquoi maintenant ?**

1. **Home dense** sans hiérarchie actionnable — mur de KPIs + fleet + recent runs + 5+ panels (`webapp/apps/shell/app/page.tsx` ≈230 lignes RSC orchestrant 9 queries Supabase parallèles + 4 client islands). Pas de "today / next best action".
2. **Navigation orientée architecture interne** (20 routes plates : audits, recos, gsg, reality, learning, experiments, scent, geo, clients, ...) pas workflows utilisateur.
3. **Worker liveness invisible** — aucune route `/api/worker/health`, aucun badge UI, aucun signal si daemon down. Les `runs` stagnent en `pending` indéfiniment ; `RunStatusPill` affiche amber "en attente" sans expliquer.
4. **`/gsg` ≠ Studio** — c'est uniquement le Design Grammar viewer. Le brief/run/preview vit ailleurs (`/gsg/handoff`). Aucun CTA croisé. User atterrit dessus, croit que c'est le studio, ne trouve pas le wizard.
5. **GSG output_path race** — worker écrit `output_path` **après** status=`completed`. Race possible → preview affiche "worker doit être patché". Pas de validation post-completion.
6. **Audit run pas chaîné** — `POST /api/audits` crée row sans run. UI doit POST 3x `/api/runs` (capture, score, recos) séparément. Aucune orchestration côté backend. Refresh manuel pour voir résultats.
7. **Modules avancés mentent** — Reality/GEO affichent skeleton "0/5 configured" sans clarifier "ready_to_configure" vs "blocked" vs "no_data". Scent affiche "Aucun scent trail" sur 95% installs sans expliquer captures cross-channel deferred.
8. **Edit/save inconsistant** — PATCH `/api/recos/[id]` pour fields, PATCH `/api/recos/[id]/lifecycle` pour status enum. Deux endpoints, deux patterns côté UI. Pas de hook `useEdit` global.
9. **Docs contradictoires** — `webapp/README.md` décrivait 5 microfrontends alors que D1.A locked single shell (corrigé J0.1 dans ce PR). 2 epics master concurrentes (`webapp-stratosphere` completed May 11 vs `webapp-stratospheric-reconstruction-2026-05` closed May 13). 4 epics GSG orphelines sans GitHub.
10. **Dead UI en prod** — `/audit-gads` et `/audit-meta` ont des boutons "New audit (CSV)" disabled avec title="Form UI post-MVP". CommandCenterTopbar legacy coexiste avec StickyHeader. `/funnel` route ghost. Table `screenshots` créée mais jamais writée. Table `experiments` créée mais dispatcher = `print("not implemented")`.

**Coût de l'inaction** : la webapp reste un assemblage technique au lieu d'un produit. Un nouveau membre Growth Society ne comprend pas où cliquer en <30s. Les runs "completed" peuvent mentir (experiment dispatcher noop). Les actions ne donnent pas confiance. La valeur du moteur (audit + GSG + multi-judge) reste enterrée derrière une UX qui ne montre pas ce qu'il faut faire maintenant.

## User Stories

### Story 1 — Mathis (CRO Lead, Growth Society)
**En tant que** Mathis,
**je veux** ouvrir la home et voir en <10 secondes "qu'est-ce que je dois faire aujourd'hui",
**afin que** je ne perde pas 5 minutes à fouiller 11 panels pour trouver le client critique.
**Acceptance** : home expose 3-5 actions urgentes ranked (clients à risque, runs failed, recos validés à shipper), pas un mur de KPIs.

### Story 2 — Mathis (lancer un audit)
**En tant que** Mathis,
**je veux** créer un nouveau client et lancer son premier audit complet en un seul flow,
**afin que** je n'aie pas à orchestrer manuellement capture → score → recos via 3 POSTs séparés.
**Acceptance** : depuis `/clients/[slug]`, bouton "Audit page X" → 1 POST déclenche un run `audit_full` côté worker qui chaîne capture→score→recos séquentiellement. Statut chaque étape visible realtime. Résultats auto-affichés à completion (pas de refresh manuel).

### Story 3 — Mathis (GSG Studio)
**En tant que** Mathis,
**je veux** générer une LP via le GSG Studio sans coller un UUID nulle part,
**afin que** mon flow soit : wizard → submit → preview iframe live → export HTML.
**Acceptance** : `/gsg/studio` wizard 6-8 étapes produit un BriefV2 valide → POST `/api/runs` `type=gsg` → redirect automatique vers `/gsg/runs/[id]` avec preview iframe et QA status (gates, evidence, killer_rules) en realtime.

### Story 4 — Mathis (worker down)
**En tant que** Mathis,
**je veux** voir immédiatement si le worker local est offline,
**afin que** je ne croie pas que les runs sont cassés.
**Acceptance** : topbar globale affiche badge worker {online <60s / lagging 60-300s / offline >300s}. Sur run `pending` >5min avec worker offline, panel affiche "Worker offline — vos runs attendront son redémarrage. [Voir logs]".

### Story 5 — Mathis (Module Maturity honest)
**En tant que** Mathis,
**je veux** voir clairement le statut de chaque module (active / ready_to_configure / no_data / blocked / experimental / archived),
**afin que** je ne croie pas qu'un module est cassé alors qu'il attend juste des credentials.
**Acceptance** : chaque module top-level (Reality, GEO, Learning, Experiments, Scent) affiche un `<ModuleHeader>` avec statut + reason + next_step CTA. Aucune fake data, aucune fake interactivity.

### Story 6 — Mathis (edit reco)
**En tant que** Mathis,
**je veux** éditer une reco avec un pattern uniforme partout dans l'app (form → save explicite → toast feedback),
**afin que** je n'aie pas à apprendre 3 patterns d'édition différents.
**Acceptance** : un seul hook `useEdit({ resource, id, fields })`. Save explicit (jamais auto-save). Lifecycle pill séparé du form (dropdown explicit draft/validated/shipped). Confirm typed pour delete.

### Story 7 — Nouveau member Growth Society
**En tant que** un consultant junior qui rejoint l'agence,
**je veux** comprendre en <30s où cliquer pour trouver le score d'audit d'un client,
**afin que** je sois autonome après onboarding 15min.
**Acceptance** : test 3 personnes externes ou heuristique 10s. Sidebar workflow-first (5 espaces), pas de jargon interne dans la nav.

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Sidebar workflow-first 5 espaces (Command Center, Clients, Audits & Recos, GSG Studio, Advanced Intelligence) + Doctrine + Settings | P0 |
| FR-2 | Sidebar rendue uniformément sur toutes routes sauf public (/login, /privacy, /terms) | P0 |
| FR-3 | Worker health endpoint `/api/worker/health` + heartbeat depuis daemon (30s) + topbar badge global | P0 |
| FR-4 | Table `system_health` migration Supabase (last_seen_at, version, status) | P0 |
| FR-5 | Module Maturity Model `<ModuleHeader>` component + contract `Maturity` exposé par chaque loader | P0 |
| FR-6 | 5 canonical states components (`EmptyState`, `LoadingSkeleton`, `BlockedState`, `WorkerOfflineState`, `ErrorBoundary`) | P0 |
| FR-7 | `<ActionButton>` primitive avec pending/success/failure + next_step + retry/cancel | P0 |
| FR-8 | Home Command Center 4 zones (Today/Urgent · Fleet Health · Recent Runs · Next Best Actions). Détails en drill-down. | P0 |
| FR-9 | Audit run orchestré : nouveau worker handler `audit_full` qui chaîne capture→score→recos. UI déclenche 1 run, voit 3 étapes. | P0 |
| FR-10 | GSG Studio : route `/gsg/studio` = wizard + run trigger ; `/gsg/runs/[id]` = preview iframe + QA + export ; `/gsg/runs` history ; `/gsg/design-grammar/[client]` viewer ; redirect `/gsg` → `/gsg/studio` | P0 |
| FR-11 | GSG run wiring : submit wizard → redirect automatique `/gsg/runs/[id]`, plus de paste UUID | P0 |
| FR-12 | GSG preview validates output_path post-completion (re-fetch + fallback message si HTML absent) | P0 |
| FR-13 | Edit/save pattern global : hook `useEdit` + bouton Save explicit + toast feedback + revert on fail | P0 |
| FR-14 | Reco lifecycle pill séparé (dropdown explicit) — merge endpoint OU clarifier deux patterns | P1 |
| FR-15 | Opportunities board (lire Opportunity Layer module Python existant) + Promote reco → opportunity | P1 |
| FR-16 | Reality Layer : **UX/architecture/maturity only** ; pas de wire OAuth, pas de poller config (deferred Mathis) | P1 |
| FR-17 | GEO Layer : **UX honest activation** (keys missing visible, query bank visible, no_data state propre) | P1 |
| FR-18 | Learning Layer : **research spike** doc `LEARNING_LAYER_APPROACH_DECISION.md` AVANT tout UI build (OPEN QUESTION §6 audit) | P0 |
| FR-19 | Experiments : decision spike "implement vs archive" + execution selon décision | P1 |
| FR-20 | DataTable générique réutilisable (sort/filter/pagination/empty/loading) | P1 |
| FR-21 | Visual simplification : retirer fond étoilé/glass excessif, typo lisible, density de travail, no card-in-card | P1 |
| FR-22 | Mobile/tablet sanity : no overlap, tables scrollables, forms lisibles | P1 |
| FR-23 | Playwright smoke suite 9 parcours (login, home, create-client, audit-trigger, audit-result, reco-edit, gsg-wizard, gsg-preview, worker-offline) desktop + mobile | P0 |
| FR-24 | Drop dead code : CommandCenterTopbar legacy import, `/funnel` ghost route, `screenshots` table migration | P1 |
| FR-25 | Hide from nav : `/audit-gads`, `/audit-meta` jusqu'à form UI + skill wiring | P0 |
| FR-26 | Doc cleanup : `webapp/README.md` (J0.1 fait), epic hierarchy clarification (J0.2), CONTINUATION_PLAN cascade consolidation (J0.3) | P0 |
| FR-27 | Manifest §12 entries pour chaque phase shipped | P0 |

## Non-Functional Requirements

- **Performance** : home TTFB p50 <500ms sur Vercel prod (baseline à mesurer Phase A1). Lighthouse perf >85.
- **Security** : RLS Supabase actif (already OK). No JWT in repo (already OK). No env reads outside `growthcro/config.py`. Worker service_role token only in `.env` (already gitignored).
- **Observability** : worker heartbeat 30s, error_message exposed UI, structured logs daemon side, Playwright smoke suite green sur prod.
- **Doctrine compliance** : 8 mono-concern axes pour toute nouvelle module Python (worker handler `audit_full`, system_health migration). LOC ≤300 / file pour nouveaux fichiers. Hard fail lint hygiene gate before commits.
- **Anti-régression** : PRESERVE_CREATIVE_LATITUDE = True dans Elite Mode jamais touché. 215 tests Renaissance restent verts. Doctrine V3.2.1 frozen.

## Success Criteria

1. **TTFB home** p50 baseline (Phase A1) → target <500ms Vercel prod (mesure Phase I1)
2. **Lighthouse perf** home >85 (mesure Phase I1)
3. **9 Playwright smoke** green sur prod URL (Phase I3)
4. **0 hygiene violations** : `python3 scripts/lint_code_hygiene.py --staged` exit 0 sur chaque commit
5. **0 anti-pattern CLAUDE.md** re-introduced
6. **Worker badge** visible 100% des pages authenticated
7. **Module Maturity** affiché honnêtement pour 100% des modules top-level
8. **Audit run orchestré** : 1 POST → 3 étapes chained → résultats auto-affichés (test E2E vert)
9. **GSG Studio E2E** : wizard → submit → preview iframe → export HTML (test E2E vert, pas de paste UUID)
10. **Learning Layer decision** : doc `LEARNING_LAYER_APPROACH_DECISION.md` produit + tranchée Mathis avant build UI G3
11. **Dead UI removed** : `/audit-gads`, `/audit-meta` cachés ; CommandCenterTopbar dropped ; `/funnel` ghost retiré ; tables `screenshots` + `experiments` archivées si pas wired
12. **Docs cohérence** : `grep "microfrontends"` retourne archive-only refs, manifest §12 à jour, 1 seul CONTINUATION_PLAN current
13. **Heuristique 30s** : test 3 personnes externes "où trouver le score audit d'un client X" → <30s mediane

## Constraints

- **Doctrine V3.2.1 frozen** pour ce PRD. Modifications V3.3 routent vers PRD séparé via doctrine-keeper.
- **D1.A single shell locked** — pas de retour aux microfrontends.
- **PRESERVE_CREATIVE_LATITUDE** dans `moteur_gsg/creative_engine/elite/orchestrator.py` jamais touché depuis la webapp.
- **Renaissance Wave 2/3** (CR-04..CR-08) en gel pendant cet epic. Reprise post-acceptance.
- **No new external skill installation** sans security audit (cf. `SKILLS_REGISTRY_GOVERNANCE.json`).
- **No `git reset --hard` / `push --force` / `clean -fd`** sans accord explicite Mathis (perte irréversible).
- **Manifest §12 bump** = SEPARATE commit (`docs: manifest §12 — ...`).
- **Hygiene gate** non-négociable : `python3 scripts/lint_code_hygiene.py --staged` exit 0 avant chaque `git add` source.
- **Skills combo** : Webapp Next.js dev ≤5 skills simultanés. Respecter `SKILLS_INTEGRATION_BLUEPRINT.md` v1.4 §4.1.4.
- **Notion** : aucune modification sans demande explicite Mathis.
- **Reality Layer backend** : pas de wire OAuth/polling. UX/architecture only.
- **Learning Layer UI build** : bloqué sur research spike (FR-18).

## Out of Scope

Inherits `OUT_OF_SCOPE_CHECKLIST.md` verbatim :

| Item | Why out of scope | Suggested P-level | Follow-up issue link |
|------|------------------|-------------------|----------------------|
| Doctrine V3.2.1 modifications | Frozen until V3.3 Mathis review; touch via `doctrine-keeper` only | P1 (separate PRD) | TBD |
| Microfrontends architecture | Locked single shell per `PRODUCT_BOUNDARIES_V26AH §3-bis` D1.A | never (anti-pattern) | n/a |
| Refactor of >5 unrelated files | Anti-drift; split into focused refactor PRD | P2 | TBD |
| Multi-file rename / `git mv` massif | Migration destructive — stop condition #1 | P1 | TBD |
| New external skill install | Requires security audit (cf. `SKILLS_REGISTRY_GOVERNANCE.json`) before install | P1 | TBD |
| LLM call without Pydantic v2 strict validation | Stop condition #5 | n/a (always required) | n/a |
| New env read outside `growthcro/config.py` | Anti-pattern #9 | n/a (always required) | n/a |
| File at `*_archive*`, `*_obsolete*`, `*deprecated*`, `*backup*` in active path | Anti-pattern #10 | n/a (always required) | n/a |
| Persona narrator prompt >8K chars | Anti-pattern #1 | n/a (always required) | n/a |
| Anti-AI-slop too aggressive | Anti-pattern #2 | n/a (always required) | n/a |
| Notion modification | No Notion writes without explicit Mathis request | n/a | n/a |
| Secret in clear (commit, log, comment) | Stop condition #2 | n/a (always required) | n/a |
| Skipping hygiene gate | Non-negotiable | n/a (always required) | n/a |
| Bundling manifest §12 with implementation commit | SEPARATE commit | n/a (always required) | n/a |
| Loading >8 simultaneous skills or forbidden combos | Anti-pattern #12 | n/a (always required) | n/a |
| Loading legacy `.claude/skills/` install scripts unaudited | Skill governance | n/a | n/a |
| Webapp data fidelity Wave A / Wave B | Pending Mathis confirmation | P1 (separate epic) | `.claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md` |

PRD-specific extensions :

| Item | Why out of scope | Suggested P-level | Follow-up issue link |
|------|------------------|-------------------|----------------------|
| Backend Python rewrite (`moteur_gsg/`, `moteur_multi_judge/`, `growthcro/*` sauf worker handlers ajoutés) | Socle technique préservé par décision Mathis 2026-05-17 | n/a | n/a |
| Reality Layer OAuth wiring (Catchr/Meta/Google/Shopify/Clarity/GA4/TikTok) | Deferred Mathis decision (coût/value) — UX/architecture only | P1 (separate epic) | TBD |
| Learning Layer Bayesian update implementation | Approche fondamentale questionnée — research spike d'abord | P0 (G3 spike) | TBD |
| Experiments dispatcher implementation | Decision spike "implement vs archive" requis | P1 (G4 spike) | TBD |
| Tailwind / Radix / shadcn migration | Si pas déjà installé, pas dans ce PRD. Évaluation post-acceptance. | P2 | TBD |
| Server Actions migration partout | Optionnel, pas requis pour livrer les FR. | P2 | TBD |
| Mega-prompt persona_narrator changes côté webapp | PRESERVE_CREATIVE_LATITUDE intouché | never | n/a |
| Renaissance Wave 2/3 (CR-04..CR-08) | Gel jusqu'à acceptance epic | P0 reprise post | `.claude/epics/gsg-creative-renaissance/` |

## Dependencies

- **Renaissance Wave 1.5 shipped** (Elite Mode #64 closed 2026-05-17) — webapp UX peut afficher Elite outputs. ✅ done.
- **D1.A locked** (2026-05-14) — single shell foundation. ✅ done.
- **Worker daemon stable** (`growthcro/worker/daemon.py`) — base pour heartbeat extension. ✅ stable.
- **Supabase RLS + auth** (`@growthcro/data` + helpers) — base auth/data layer. ✅ stable.
- **Opportunity Layer module Python** (shipped via #47/#48 dans stratosphere-p0) — pour Phase E3.
- **MCP Playwright** installed via `.mcp.json` — pour Phase I3 smoke suite + Phase A1 Vercel deployed screenshots.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Refactor casse routes existantes en prod | med | high | Redirects 301 from old paths, Playwright smoke gate par phase, feature flag `FEATURE_NEW_UX_<phase>` |
| Worker heartbeat ajoute charge daemon | low | low | 30s polling déjà actif, ajout d'un PATCH léger par cycle |
| Realtime channel surcharge si abonnement central | low | med | Single provider, debounce, fallback polling |
| Phase trop longue → drift | med | high | `growthcro-anti-drift` skill par issue + stop conditions explicites + 1-6 fichiers max par issue |
| Learning Layer spike paralyse Phase G | med | low | Spike timeboxé 1-2j ; si pas tranché, OPEN QUESTION reste, G3 UI deferred mais autres phases continuent |
| Reality UX prep créera UI inutile si Mathis change avis | low | med | Sketches first, build seulement après green light |
| Mathis pas dispo pour validation par phase | high | high | Préparer screenshots dual-viewport + Playwright CI screenshots auto-uploaded comme proof |
| TTFB budget pas atteignable sur Vercel free tier | low | med | Mesurer baseline Phase I1, ajuster target ou upgrader plan |
| Anti-régression Renaissance casse pendant chantier | low | high | 215 tests Renaissance + multi-judge fixtures restent dans CI |

## Open Questions

Voir `WEBAPP_PRODUCT_AUDIT_2026-05-17.md` §6 pour détail :

- **Q1** — Reality Layer connectors deploy timing (Mathis decision pending coût/value)
- **Q2** — Learning Layer fundamental approach (research spike avant build)
- **Q3** — Experiments implement vs archive (decision spike Phase G4)
