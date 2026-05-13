---
name: webapp-clients-audits-recos
description: Wire les 4 routes core data (/clients, /clients/[slug], /audits/[id], /recos) aux queries Supabase existantes. Foundation features pour consultants Growth Society.
status: active
created: 2026-05-13T09:36:29Z
parent_prd: webapp-full-buildout
wave: B-extended
fr_index: FR-2
---

# PRD: webapp-clients-audits-recos

> Sub-PRD du master [`webapp-full-buildout`](webapp-full-buildout.md) — FR-2 (post-FR-1, M effort).
>
> Wirer les 4 routes core data aux queries `@growthcro/data` existantes. Aucune nouvelle query Supabase à écrire — toute la data layer est déjà disponible. Focus : pages Server Components qui consomment les queries + filtres/search/pagination URL-state.

## Executive Summary

Post FR-1, les routes `/audits`, `/recos` existent dans le shell mais affichent du content scaffold (placeholder). FR-2 wire **4 routes** aux data Supabase (3 clients seed + 6 audits + 30 recos) :
- **`/clients`** : liste paginée des clients avec filtres + search + sort
- **`/clients/[slug]`** : détail d'un client + ses audits + brand DNA
- **`/audits/[id]`** : détail d'un audit + scores par pilier + 5 recos enrichies
- **`/recos`** : aggregator cross-clients filtrable (priority, criterion, business_category)

**Effort** : M, 1-2j wall-clock · ~3-5h agent background (Server Components + data wiring).
**Coût API** : $0 (read-only Supabase queries).
**Bloque** : aucun (parallel-safe avec FR-3 + FR-5).
**Débloque** : FR-6 polish + validation consultants Growth Society.

## Problem Statement

### Pourquoi maintenant

1. **Routes scaffolds insuffisantes** : `/audits/[clientSlug]/page.tsx` est wired Supabase (via FR-1 move from audit-app), mais `/clients` n'existe pas du tout. `/recos` (cross-clients) idem.
2. **Data déjà seedée** : 3 clients (Acme SaaS, Japhy, Doctolib) × 2 audits × 5 recos chacun = 30 recos en Supabase EU. Inutilisable sans UI.
3. **Consultants pending** : Mathis a promis aux consultants Growth Society une demo. Sans `/clients` paginé filtrable, pas de valeur perçue.
4. **Foundation FR-6** : la validation consultant (`FR-6 webapp-polish-validation`) suppose ces 4 routes fonctionnelles.

### Ce que FR-2 apporte

- 4 routes 200 wired Supabase data (vs scaffolds)
- Filtres URL-state (shareable links pour Mathis cross-team)
- Pagination + sort + search côté serveur (scalable à 100 clients)
- Pattern réutilisable pour les futures listes (FR-3 GSG, FR-4 Learning, FR-6 polish)

## User Stories

### US-1 — Consultant (liste clients)
*Comme consultant Growth Society qui a 100 clients en portefeuille, je veux `/clients` paginée avec filtres (business_category, score range) + search par nom + sort (score, last_audit_date), pour aller vite sur le client cherché.*

**Acceptance Criteria** :
- ✓ `/clients` HTTP 200 wired `listClientsWithStats()` (existing query)
- ✓ Affiche : name, slug, business_category, avg_score, audits_count, last_audit_date
- ✓ Filters : dropdown business_category + score min/max range
- ✓ Search : input free-text sur name + slug (debounced 300ms)
- ✓ Sort : dropdown (name asc, score desc, last_audit_date desc)
- ✓ Pagination : 25 per page, query params `?page=N&per_page=25`
- ✓ State persistent URL params (shareable)

### US-2 — Consultant (détail client)
*Comme consultant qui prépare un meeting, je veux `/clients/[slug]` qui montre tous les audits du client + scores par pilier + brand DNA si dispo, pour avoir le full context en 1 page.*

**Acceptance Criteria** :
- ✓ `/clients/[slug]` HTTP 200 wired `getClientBySlug()` + `listAuditsForClient()`
- ✓ Header : client name + business_category + 6 piliers radial chart (V3.2.1 score)
- ✓ Tabs : `Audits` (default), `Brand DNA` (V29 si dispo, sinon "Pending"), `History`
- ✓ Tab Audits : liste des audits + link `/audits/[id]`
- ✓ Empty states gracieux (no audits, no brand DNA)

### US-3 — Consultant (détail audit)
*Comme consultant qui explique un audit à un client, je veux `/audits/[id]` qui montre : 6 piliers + sub-scores + 5 recos prioritaires avec evidence_ids cliquables vers screenshots.*

**Acceptance Criteria** :
- ✓ `/audits/[id]` HTTP 200 wired `getAuditById()` + `listRecosForAudit()`
- ✓ Header : client name + page_url + audit_date + global_score
- ✓ Section "Scores par pilier" : 6 piliers V3.2.1 (intent, value_clarity, social_proof, coherence, ux, motivation_friction)
- ✓ Section "Recos prioritaires" : top 5 par expected_lift_pct desc
- ✓ Each reco : priority badge (P0/P1/P2), criterion_id, content_json.summary, expected_lift_pct, evidence_ids
- ✓ Evidence_ids cliquables vers screenshots (modal lightbox OR new tab)
- ✓ CTA "Export audit PDF" (link vers /audits/[id]/export — out of scope V1, just placeholder button)

### US-4 — Consultant (recos cross-clients)
*Comme consultant qui audite 5+ clients similaires, je veux `/recos` aggregator cross-clients filtré par priority + criterion + business_category, pour identifier les patterns récurrents et formuler une playbook agency.*

**Acceptance Criteria** :
- ✓ `/recos` HTTP 200 wired aggregate query (new `listRecosAggregate()` si nécessaire OR client-side filter on `listAllRecos()`)
- ✓ Filters : priority dropdown (P0/P1/P2/all), criterion_id dropdown, business_category dropdown
- ✓ Sort : `expected_lift_pct desc` default
- ✓ Pagination 50 per page
- ✓ Each reco card : client name (link to client) + criterion_id + summary + lift_pct + priority badge
- ✓ State persistent URL params

## Functional Requirements

### Task Breakdown (4 tasks file-disjoint, parallel-safe)

#### T001 — `/clients` route (US-1)
**Effort** : S-M, 1-2h
**Files** : `webapp/apps/shell/app/clients/page.tsx` + `webapp/apps/shell/components/clients/{ClientList,ClientFilters,ClientSortDropdown}.tsx`
**Data** : `listClientsWithStats()` (existing query in `@growthcro/data`)
**Pattern** : Server Component page + 1 Client Component for filters interactivity. URL params via Next.js `searchParams`.

#### T002 — `/clients/[slug]` route (US-2)
**Effort** : S-M, 1-2h
**Files** : `webapp/apps/shell/app/clients/[slug]/page.tsx` + `webapp/apps/shell/components/clients/{ClientDetail,PillarRadialChart,AuditsTab,BrandDNATab}.tsx`
**Data** : `getClientBySlug()` + `listAuditsForClient()` (both existing)
**Pattern** : Server Component page + Client Component tabs. Radial chart via SVG + CSS (no charting lib dep).

#### T003 — `/audits/[id]` route enrichment (US-3)
**Effort** : S, 1h
**Files** : Edit `webapp/apps/shell/app/audits/[clientSlug]/page.tsx` (already exists from FR-1, was originally audit-app pattern) + add scores/recos sections. OR create NEW route `webapp/apps/shell/app/audits/[id]/page.tsx` (by audit ID, not client slug).
**Decision** : keep `[clientSlug]` route from FR-1 BUT add child page `audits/[clientSlug]/[auditId]/page.tsx` for specific audit detail. OR migrate to `audits/[id]/page.tsx` and update internal links. **T003 decides at execution time based on data layer query shape.**
**Data** : `getAuditById(audit_id)` or `getAuditByClientAndPage()` (check `@growthcro/data` exports)

#### T004 — `/recos` cross-client aggregator (US-4)
**Effort** : S-M, 1-2h
**Files** : `webapp/apps/shell/app/recos/page.tsx` (already exists from FR-1, currently scaffold) + `webapp/apps/shell/components/recos/{RecoAggregator,RecoFiltersCrossClient}.tsx`
**Data** : may need new query `listRecosAggregate()` OR `listAllRecos()` client-side filter. **T004 inspects @growthcro/data and decides.**
**Constraint** : page 50 per page max (vs 25 for /clients) to surface more patterns.

### Notes techniques

- **URL state** : tous les filtres/search/sort/page via `searchParams`. RSC re-render quand params changent.
- **Performance** : Server Components rendrent côté serveur, fetch parallel via `Promise.all` quand possible.
- **Cache** : pas de `unstable_cache` dans ce sub-PRD (FR-6 polish décidera).
- **Filtres client-side vs server-side** : préférer server-side (`.eq()`, `.gte()`) dans Supabase queries pour scale 100 clients. Client-side seulement pour search debounced.

## Non-Functional Requirements

### Doctrine
- V3.2.1 + V3.3 piliers respectés (radial chart affiche les 6 piliers V3.2.1)
- Code doctrine : TS/TSX ≤ 800 LOC, mono-concern
- Composants groupés par feature (`components/clients/`, `components/recos/`)
- Pas de `process.env[key]` dynamic
- Anti-pattern #11 OK : composants nommés par contexte (`ClientList` vs `RecoList`)

### Performance
- Page load < 2s sur 4G
- Supabase queries < 200ms (EU region)
- Filter changes via URL → < 500ms RSC re-render
- Bundle size shell : ne doit pas augmenter > 30% (mesure post-FR-2)

### Sécurité
- RLS Supabase enforcée (Mathis voit son org, pas autres)
- Pas de service_role exposé côté client
- Pas de SQL injection (utiliser Supabase client typés)

### Documentation
- MANIFEST §12 changelog post-merge
- Architecture map regen
- Capabilities-keeper invocation pre-task (idempotent)

## Success Criteria

### Routes
- [ ] `/clients` HTTP 200 wired Supabase, paginé filtrable searchable
- [ ] `/clients/[slug]` HTTP 200 wired, 6 piliers radial + audits list + brand DNA placeholder
- [ ] `/audits/[id]` ou `/audits/[clientSlug]/[auditId]` HTTP 200, scores + recos prioritaires + evidence_ids cliquables
- [ ] `/recos` HTTP 200 aggregator cross-clients, 50 per page, filtres URL-state

### Gates
- [ ] `python3 scripts/lint_code_hygiene.py` FAIL ≤ baseline (1 pré-existant)
- [ ] `bash scripts/parity_check.sh weglot` ✓
- [ ] `python3 SCHEMA/validate_all.py` ✓
- [ ] `npm --workspace @growthcro/shell run typecheck` exit 0
- [ ] `npm --workspace @growthcro/shell run build` exit 0
- [ ] Bundle First Load JS < 110 KB shared (vs 87.3 KB baseline post-FR-1)

### Runtime
- [ ] 4 routes 200 sur prod URL
- [ ] Filters URL params persistent post-refresh
- [ ] 30 recos seed visibles sur `/recos` aggregator
- [ ] Pagination fonctionne (page=2 affiche page 2)
- [ ] Empty states pour clients sans audits, audits sans recos

### Doctrine
- [ ] 0 régression V26.AF / V3.2.1 / V3.3
- [ ] 0 file > 800 LOC introduit
- [ ] 1 commit isolé pour le wiring
- [ ] MANIFEST §12 changelog commit séparé

## Constraints & Assumptions

### Constraints
- Pas de nouvelle query Supabase (utiliser `@growthcro/data` existing)
- Pas de modif schema Supabase
- Pas de Charting lib (recharts, victory) — SVG/CSS only pour radial chart
- Pas de FastAPI backend deploy
- Pas de modif `webapp/packages/data/` queries

### Assumptions
- `@growthcro/data` queries listClientsWithStats, getClientBySlug, listAuditsForClient, listRecosForAudit existent et fonctionnent (verified FR-1)
- Data seedée intacte (3 clients × 2 audits × 5 recos)
- Mathis disponible ~30 min validation visuelle post-deploy
- `@growthcro/ui` Card + Pill + KpiCard suffisent pour les nouveaux composants

## Out of Scope

### Explicitement hors scope ce sub-PRD
- **Brand DNA full content** : si une `brand_dna` table existe, juste afficher "Pending" tab. Full wire = sprint future.
- **Export PDF audit** : juste placeholder button. Implem = sprint future.
- **Charting library** : pas d'install recharts/victory. SVG/CSS only.
- **GSG iframe** : c'est FR-3
- **Settings page** : c'est FR-5
- **Learning lab data** : c'est FR-4
- **Reality monitor** : V2 deferred
- **A/B testing** : V2 deferred
- **Notifications/Realtime** : pas de subscription Supabase realtime (out of scope V1)

## Dependencies

### Externes
- Mathis ~30 min validation
- Vercel auto-deploy (active)
- Supabase EU (active)

### Internes
- **FR-1 SHIPPED** : routes `/audits`, `/recos` existent dans shell (foundation)
- `@growthcro/data` queries stables
- `@growthcro/ui` components réutilisables
- 3 clients seed + 30 recos en Supabase

### Sequencing
- T001 ∥ T002 ∥ T003 ∥ T004 (all file-disjoint, parallel-safe)
- Pas de blocking interne

### Parallel avec FR-3 + FR-5
- FR-2 touche `app/clients/`, `app/recos/`, `app/audits/[…]/`, `components/clients/`, `components/recos/`
- FR-3 touche `app/gsg/`, `components/gsg/`
- FR-5 touche `app/settings/`, `components/settings/`
- File-disjoint ✓ — peut tourner en 3 worktrees parallèles
