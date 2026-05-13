---
name: webapp-full-buildout
description: Programme complet pour rendre la webapp V28 fonctionnelle de bout en bout — pages remplies de data Supabase, navigation cohérente, vues détaillées clients/audits/recos/GSG/learning. Stratégie consolidation 6 microfrontends scaffold → 1 single Next.js shell deploy. Out-of-scope volontaire : Google Ads + Meta Ads (deferred), FastAPI trigger backend (decision gate post-validation).
status: active
created: 2026-05-12T17:00:00Z
parent_prd: post-stratosphere-roadmap
github_epic: (will be set on sync)
wave: B-extended
epic_index: 4-extended
---

# PRD: webapp-full-buildout

> **Programme multi-jours** de buildout webapp V28. Compose 6 sub-PRDs ordonnés par priorité business + dépendances techniques.
>
> Décisions stratégiques actées :
> - **Consolidation** 6 microfrontends scaffold → 1 shell unique (vs déployer 6 projets Vercel)
> - **Pattern data** : Mathis pipelines locaux Python → push Supabase via service_role → webapp consomme via REST/PostgREST (pas de FastAPI trigger backend pour V1)
> - **Out-of-scope V1** : Google Ads + Meta Ads (audit-gads, audit-meta) — `defer for V2`
> - **Auth** : Supabase Email+Password + magic link (déjà live)

## Executive Summary

Post Wave A (Epic 1 typing + Epic 2 micro-cleanup) + Wave B partial (Vercel + Supabase + shell scaffold live), la webapp **shell tourne** mais n'a **qu'une coquille vide visible** : 1 home dashboard + 1 login page. Les 6 microfrontends scaffolded (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab + shell) ne sont **pas déployés** — leurs URLs fallback dans `microfrontends.json` retournent des erreurs 404.

Ce master PRD encadre le **buildout complet** : consolider les 6 microfrontends DANS le shell (1 single Next.js app, multi-routes), wirer toutes les pages aux data Supabase existantes, livrer une UX fonctionnelle bout-en-bout pour validation consultants Growth Society.

**Durée estimée** : 4-7 jours développement (M-L epic), étalable en sprints jour-par-jour avec agents background parallèles.
**Coût API** : ~$0 (refactor + wiring, aucune génération Sonnet).
**Critical path** : Phase 1 foundation → Phase 2 features parallèles → Phase 3 polish + validation.

## État de l'art (snapshot main d217310, 2026-05-12 evening)

### Live
- ✅ https://growth-cro.vercel.app shell deployed (HTTP 200 sur /, /login, /privacy, /terms)
- ✅ Auth : `tech@growth-society.com` logged in via email+password (magic link rate-limited free tier)
- ✅ Supabase : 8 tables + 2 views + 2 RPCs migrated, 3 clients/6 audits/30 recos/4 runs seedés
- ✅ Vercel ↔ Supabase ↔ GitHub triple integration : env vars synced, auto-deploy GitHub
- ✅ Data layer TypeScript : queries existantes dans `webapp/packages/data/src/queries/` (clients, audits, recos, runs)

### Scaffold non-deployed
- ⏳ 5 microfrontends : audit-app, reco-app, gsg-studio, reality-monitor, learning-lab (présents dans `webapp/apps/`)
- ⏳ Shell routes manquantes : `/clients`, `/clients/[slug]`, `/audits/[id]`, `/recos`, `/recos/[id]`, `/gsg`, `/learning`, `/reality`, `/settings`
- ⏳ Trigger d'audit depuis UI (requires FastAPI backend — déféré decision-gate)

### Out-of-scope V1 (decision Mathis 2026-05-12)
- 🔴 `/audit-gads` et `/audit-meta` (déjà scaffolded shell-side) — Mathis dit "on s'en fiche, pour plus tard"
- 🔴 FastAPI backend deploy (Fly.io/Railway) — decision gate post-validation
- 🔴 Reality Monitor live (besoin credentials GA4 + Meta + Google + Shopify + Clarity)
- 🔴 GSG live trigger from UI (besoin FastAPI + Browserless cloud)

## Problem Statement

### Pourquoi maintenant

1. **La webapp est live mais vide** → consultants Growth Society ne peuvent pas l'évaluer
2. **Architecture microfrontends overkill** : 1 dev solo + 100 clients ne justifie pas 6 projets Vercel séparés. Refactor maintenant = 2j, refactor dans 6 mois = 2 semaines (sunk cost).
3. **Data layer existante** : queries `listClients`, `listAuditsForClient`, `listRecosForAudit`, `listRecentRuns` déjà implémentées. Manque juste les UI pages qui les consomment.
4. **Decision gate FastAPI** : valider UX read-only AVANT de déployer FastAPI nous économise potentiellement 1j + budget cloud.

### Ce que ce master PRD apporte

- **Consolidation** des 6 microfrontends scaffold dans le shell unique (1 deploy, 1 maintenance, simpler routing)
- **Wiring complet** de chaque section feature à la data Supabase existante
- **Roadmap claire** en 6 sub-PRDs ordonnés ICE + dépendance
- **Decision gate explicite** post-V1 pour FastAPI deploy

## User Stories

### US-1 — Mathis (consolider architecture)
*Comme founder solo, je veux que les 6 microfrontends scaffold soient consolidés en 1 seul Next.js shell avec routing /clients, /audits, /recos, /gsg, /learning, /reality, pour simplifier le deploy + maintenance.*

**AC** : 1 single Vercel project (growth-cro), microfrontends.json deleted, toutes pages dans `webapp/apps/shell/app/`, navigation Sidebar updated.

### US-2 — Consultant Growth Society (consulter audits)
*Comme consultant, je veux naviguer `/clients` → voir liste des clients audités → click un client → voir ses audits → click un audit → voir ses 5+ recos enriched avec evidence_ids, pour comprendre et présenter les findings.*

**AC** : 3 routes wired Supabase : `/clients`, `/clients/[slug]`, `/audits/[id]`. Recos affichées avec priority badge + criterion_id + content_json.summary + expected_lift_pct.

### US-3 — Consultant (filtrer + chercher)
*Comme consultant qui a 100 clients, je veux filtrer la liste clients par business_category + chercher par nom + trier par score moyen, pour aller vite.*

**AC** : Filtres UI sur `/clients` (category dropdown + search input + sort dropdown). State persistent en URL params (shareable links).

### US-4 — Mathis (livret GSG)
*Comme founder qui produit des LPs GSG, je veux une page `/gsg` qui liste les LPs scaffolded (Weglot, Stripe, Japhy) + leur état (scaffold / multi-judge / live) + un viewer iframe des fichiers HTML générés.*

**AC** : `/gsg` lit `deliverables/gsg_demo/*.html` paths depuis Supabase metadata OU file system (via API route Next.js). Iframe viewer responsive. Badge state per LP.

### US-5 — Consultant (recos cross-clients)
*Comme consultant qui audite 5+ clients similaires, je veux une vue `/recos?priority=P0` qui agrège les recos P0 cross-clients triées par expected_lift_pct desc, pour identifier les patterns récurrents.*

**AC** : `/recos` agrégateur cross-clients. Filtres : priority, criterion_id, business_category. Sort par lift. Pagination 50 par page.

### US-6 — Mathis (settings + admin)
*Comme founder, je veux une page `/settings` pour : changer mon password, voir mes credentials API, manage org members (invite consultants), regénérer service_role key, voir billing usage.*

**AC** : `/settings` 4 onglets (Account, API, Team, Usage). Password change via Supabase Auth UI. Team invites via service_role API.

### US-7 — Consultant (learning lab — V3.4 doctrine)
*Comme consultant qui valide V3.4 doctrine, je veux `/learning` qui liste les 69 doctrine_proposals avec leur statut (accept/decline/refine/defer), filtrable, avec un bouton Mathis_final pour casting le vote.*

**AC** : `/learning` lit table `doctrine_proposals` (à créer dans schema?). Sort par confidence. UI vote 4 buttons. Persistence Mathis_final.

## Functional Requirements (6 sub-PRDs)

### FR-1 — Sub-PRD `webapp-consolidate-architecture` (foundation, blocking) ✅ COMPLETED 2026-05-13
- **Effort** : M, 1-1.5j → réalisé en **~1h wall-clock** (1 agent background séquentiel T001→T004 + gate-vert)
- **Sub-PRD** : [`webapp-consolidate-architecture.md`](webapp-consolidate-architecture.md) (4 tasks file-disjoint)
- **Livré** :
  - 5 microfrontends archivés `_archive/webapp_microfrontends_2026-05-12/{audit-app,reco-app,gsg-studio,reality-monitor,learning-lab}/` (60 files git mv préservant l'historique)
  - 27 nouveaux fichiers shell : 9 pages, 13 components groupés `components/{audits,recos,gsg,reality,learning}/`, 3 lib (`gsg-api.ts`, `reality-fs.ts`, `proposals-fs.ts`), 1 API route (`app/api/learning/proposals/review/route.ts`)
  - `webapp/microfrontends.json` supprimé · Sidebar.tsx updated (`/audits`, `/recos` pluriel)
  - Build local + Vercel : 17 routes générées, 87.3 KB shared first load, deploy 59s
  - 2 commits : `871fb6c` refactor + `f2ac207` manifest §12 → merged via `0e5daf3`
- **Prod verification** : https://growth-cro.vercel.app
  - `/login`, `/privacy`, `/terms` → 200 (public OK)
  - `/`, `/audits`, `/recos`, `/gsg`, `/reality`, `/learning`, `/audit-gads`, `/audit-meta` → 307 redirect `/login?redirect=...` (auth middleware OK, routes existent)
  - `/api/learning/proposals/review` → 307 redirect (auth middleware also protects API)
  - 0 erreur 404 / 500
- **Gates verts** : lint FAIL=1 baseline (pré-existant scripts/, hors scope FR-1), parity ✓, schemas ✓ 3439 files, capabilities ✓ 0 orphans HIGH, typecheck ✓, build ✓
- **Foundation prête** pour FR-2/3/4/5/6

### FR-1 — Original spec (préservé pour traçabilité)
- **Effort** : M, 1-1.5j
- **Cible** : refactor 5 microfrontends scaffold dans `webapp/apps/shell/app/` :
  - `apps/audit-app/app/*` → `apps/shell/app/audits/`
  - `apps/reco-app/app/*` → `apps/shell/app/recos/`
  - `apps/gsg-studio/app/*` → `apps/shell/app/gsg/`
  - `apps/reality-monitor/app/*` → `apps/shell/app/reality/`
  - `apps/learning-lab/app/*` → `apps/shell/app/learning/`
- Delete `webapp/microfrontends.json` + `webapp/apps/{audit,reco,gsg-studio,reality,learning}-*` (archive sous `_archive/webapp_microfrontends_2026-05-12/`)
- Update `webapp/apps/shell/components/Sidebar.tsx` : remove host-based links, use Next.js Link internal routing
- Update `vercel.json` build command : pas de change (déjà build apps/shell)
- 1 commit isolé, gate-vert (lint + parity + schemas + build local)
- **Blocking** : tous les sub-PRDs suivants en dépendent

### FR-2 — Sub-PRD `webapp-clients-audits-recos` ✅ COMPLETED 2026-05-13
- **Effort** : M, 1-2j → réalisé en **~3h wall-clock** (1 agent background, 4 tasks file-disjoint)
- **Sub-PRD** : [`webapp-clients-audits-recos.md`](webapp-clients-audits-recos.md)
- **Livré** : 11 components + 3 pages NEW (`/clients`, `/clients/[slug]`, `/audits/[clientSlug]/[auditId]`), `/recos` aggregator wired
  - SVG radial chart 6 piliers (no charting lib dep)
  - URL-state filters/search/sort/pagination
  - `listRecosAggregate()` NEW query in @growthcro/data
  - Decision: nested `[clientSlug]/[auditId]` route (vs flat `/audits/[id]`) for breadcrumb hierarchy
- **Build** : `/clients` 1.84 KB · `/clients/[slug]` 880 B · `/audits/[..]/[..]` ~88 KB · `/recos` 1.73 KB
- **Commit** : `6d69953` → merged `a980eab`

### FR-3 — Sub-PRD `webapp-gsg-studio` ✅ COMPLETED 2026-05-13
- **Effort** : S-M, 0.5-1j → réalisé en **~1.5h wall-clock**
- **Sub-PRD** : [`webapp-gsg-studio.md`](webapp-gsg-studio.md)
- **Livré** :
  - `lib/gsg-fs.ts` auto-discover `deliverables/gsg_demo/*.html` + parse filename + sidecar JSON
  - API route `/api/gsg/[slug]/html` (whitelist + XFO + CSP + 5min cache)
  - Page `/gsg` Server Component grid 2 cards/row + GsgLpCard component
  - 5 LPs detected: Japhy PDP, Stripe pricing, Weglot advertorial/home/listicle
  - Path traversal blocked (tested `/api/gsg/..%2F..%2Fetc%2Fpasswd/html` → 404)
- **Build** : `/gsg` 624 B / 87.9 KB First Load
- **Commit** : `ee34483` → merged `a97999f`

### FR-4 — Sub-PRD `webapp-learning-lab` (US-7)
- **Effort** : S-M, 1j
- **Cible** : `/learning` doctrine proposals review
- **Prereq schema** : nouvelle table `doctrine_proposals` (id, criterion_id, proposal_md, mathis_final, confidence, created_at) — migration à écrire
- UI : list + filter + vote 4 buttons (accept/decline/refine/defer)
- Persist via service_role REST upsert
- AC : si Mathis action #3 review 69 proposals fait, les données apparaissent

### FR-5 — Sub-PRD `webapp-settings-admin` ✅ COMPLETED 2026-05-13
- **Effort** : S, 0.5j → réalisé en **~2h wall-clock**
- **Sub-PRD** : [`webapp-settings-admin.md`](webapp-settings-admin.md)
- **Livré** :
  - `/settings` page Server Component + SettingsTabs client component (URL hash routing)
  - 4 tabs : AccountTab (password change), TeamTab (members + invite form), UsageTab (4 KpiCard), ApiTab (read-only public metadata + copy buttons)
  - API route `/api/team/invite` (service_role server-only, admin check + idempotent upsert)
  - 2 NEW @growthcro/data query modules : `org-members.ts`, `usage.ts`
  - Sidebar.tsx adds Settings link
  - Security verified: service_role JWT never in client bundle (grep on .next/static)
- **Build** : `/settings` 5.25 KB / 155 KB First Load · `/api/team/invite` route registered
- **Commit** : `48a4527` → merged `e72a104`

### FR-6 — Sub-PRD `webapp-polish-validation` (US-2/3/4 polish + UX validation)
- **Effort** : S, 0.5-1j
- **Cible** : loading states, error boundaries, empty states, mobile responsive
- + UX validation manuel (5+ screenshots desktop+mobile)
- + 1 consultant Growth Society feedback session (30min)
- + decision matrix FastAPI ship/defer (cf webapp-shell-validation sub-PRD)

## Non-Functional Requirements

### Doctrine
- V26.AF immutable (vacuous — persona_narrator gone)
- V3.2.1 + V3.3 intact
- Code doctrine : tous fichiers TS/TSX ≤ 800 LOC, mono-concern
- Mono-concern : 1 file = 1 page OR 1 hook OR 1 component
- Pas de `process.env[key]` dynamic dans webapp (bug fixed via PUBLIC_ENV static map)

### Performance
- Page load < 2s sur 4G (Vercel CDN + RSC streaming)
- Supabase queries < 200ms (EU region)
- Bundle size shell : < 250 KB gzip (audit bundle analyzer post-buildout)

### Sécurité
- Service_role JWT à rotater (déjà flaggé, action Mathis dans 24h)
- Password Mathis temp `<REDACTED>` à changer après login (déjà flaggé) — voir doc locale ou Supabase Dashboard pour recovery
- RLS policies actives (déjà testé : Mathis voit son org, pas autres)
- Pas de service_role exposé côté client (server-only via Next.js Route Handlers)

### Documentation
- MANIFEST §12 changelog post-merge
- Architecture map regen post-consolidation (gsg_lp/, audit-app/, etc. retirés)
- Capabilities-keeper invocation pre-each-sub-PRD

## Success Criteria

### Globaux V1 (cible aspirational)
- [x] FR-1 done 2026-05-13 : 5 microfrontends consolidés dans shell, 1 deploy ✅ — see `webapp-consolidate-architecture.md`
- [x] FR-2 done 2026-05-13 : 4 routes core data wired Supabase ✅ — see `webapp-clients-audits-recos.md`
- [x] FR-3 done 2026-05-13 : `/gsg` iframe preview 5 LPs ✅ — see `webapp-gsg-studio.md`
- [x] FR-5 done 2026-05-13 : `/settings` 4 tabs ✅ — see `webapp-settings-admin.md`
- [ ] FR-2 done : 4 routes wired Supabase (/clients, /clients/[slug], /audits/[id], /recos)
- [ ] FR-3 done : /gsg avec 4 LPs preview iframe
- [ ] FR-4 done : /learning si Mathis action #3 review proposals fait
- [ ] FR-5 done : /settings 4 onglets fonctionnels
- [ ] FR-6 done : polish + consultant validation + decision FastAPI
- [ ] Vercel auto-deploy fonctionne sur chaque push main
- [ ] 0 régression doctrine V3.2.1/V3.3/V26.AF
- [ ] Bundle size < 250 KB gzip
- [ ] Lighthouse score > 85 (Performance + Accessibility + Best Practices)

### Partial V1 (réaliste cette semaine)
- FR-1 + FR-2 + FR-3 + FR-5 = MVP utilisable consultants
- FR-4 + FR-6 = polish, post-MVP

## Constraints & Assumptions

### Constraints
- Pas de Notion auto-modify
- Pas de FastAPI deploy V1 (decision gate)
- Pas de Google Ads + Meta Ads pages (Mathis out-of-scope)
- Pas de Reality Monitor live (besoin credentials clients)
- Pas de GSG live trigger UI (besoin FastAPI)
- Pas de modif doctrine V3.2.1/V3.3

### Assumptions
- Mathis disponible ~2h pour validation finale + feedback consultant (FR-6)
- Consultant Growth Society dispo 30min cette/semaine prochaine
- Data layer queries (`@growthcro/data`) stable, pas de breaking change
- Vercel free tier suffit pour ~100 clients

## Out of Scope

### V1 (explicitement)
- Google Ads page (`/audit-gads`) — defer V2
- Meta Ads page (`/audit-meta`) — defer V2
- Reality Monitor live (`/reality`) — defer V2 (credentials)
- GSG trigger UI (`/gsg` "Generate new LP" button) — defer V2 (FastAPI)
- FastAPI backend deploy — decision gate post FR-6

### V2+ (post-validation)
- FastAPI deploy + Browserless cloud + Fly.io/Railway
- Reality Monitor connectors (GA4, Meta, Google, Shopify, Clarity)
- Multi-judge UI panel
- Experiment Engine UI (A/B testing)
- GEO Monitor tracking

## Dependencies

### Externes (humaines)
- Mathis ~2h validation + feedback session orchestration (FR-6)
- 1 consultant Growth Society 30min (FR-6)
- Mathis action #3 review 69 proposals (FR-4 prereq, optional V1)

### Externes (techniques)
- Vercel CDN + GitHub auto-deploy (live)
- Supabase EU + RLS policies (live)
- Node 20+, npm workspaces (live)
- Pydantic v2 (live), mypy 2.1.0 (live)

### Internes
- main HEAD `d217310` post seed script
- `webapp/packages/data/src/queries/*.ts` data layer existant
- `webapp/packages/ui` reusable components
- `webapp/apps/shell` Next.js 14 RSC
- Doctrine V3.2.1 + V3.3 schemas

### Sequencing
- FR-1 (consolidation) blocking pour FR-2/3/4/5/6 (route paths changent)
- FR-2 + FR-3 + FR-5 parallel safe après FR-1 (scopes UI disjoints)
- FR-4 prereq schema (doctrine_proposals table migration)
- FR-6 dépend de FR-2 + FR-3 + FR-5 (besoin features pour valider)

---

## Programme — Critical Path

```
JOUR 1 (foundation, blocking)
  FR-1 Consolidate microfrontends → shell (M, 1-1.5j)
       │
JOUR 2-3 (features parallèles, agents background)
  FR-2 clients/audits/recos (M, 1-2j)  ┐
  FR-3 gsg-studio          (S-M, 0.5-1j) ├─ worktrees disjoints
  FR-5 settings            (S, 0.5j)    ┘
       │
JOUR 4 (polish + validation)
  FR-6 polish + UX checklist + consultant feedback
       │
DECISION GATE FastAPI ship/defer
       │
JOUR 5+ (optional V1.5)
  FR-4 learning lab (S-M, 1j) — only if Mathis action #3 done
```

**Critical path** : FR-1 (1.5j) + max(FR-2, FR-3, FR-5) (2j) + FR-6 (1j) = **~4-5 jours wall-clock** avec parallélisation.

**Première action** : créer sub-PRD `webapp-consolidate-architecture.md` via /ccpm, decompose en 4-5 tasks, lance agent.

---

## Next Steps post-buildout

### Si FR-6 valide la webapp comme utile
- Ship FastAPI backend (sub-PRD `fastapi-backend-deploy`)
- Add trigger audits UI button → backend → push results to Supabase → live update
- Roll out à 5+ consultants Growth Society
- Collect 2-4 semaines de feedback réel
- Iterate sur V1.5

### Si FR-6 montre que la webapp est meh
- Pivot : focus sur les pipelines Python (CLI uniquement)
- Webapp = "nice to have" downgraded
- Investir effort ailleurs (Reality Layer, GSG live, Learning V30)

### Si FR-6 montre un besoin spécifique inattendu
- Sub-PRD ad-hoc selon le besoin
- Pas de roadmap prédéfinie au-delà de cette V1

---

**Note finale** : ce master PRD est intentionnellement scope-limited V1. La webapp V2 (FastAPI + Reality + GSG live + Google/Meta Ads) sera planifiée AU MOMENT du V2 sprint, basée sur la realité du feedback consultant. AD-9 "sub-PRDs created at sprint time, never stale" appliqué.
