# Webapp Product Route Audit — 2026-05

> Document canonique d'inventaire route-par-route. Source pour A2 (IA cible 5 espaces) + A3 (Module Maturity Model). Issue #66, livrable A1 de l'epic `webapp-product-ux-reconstruction-2026-05`.
>
> Étend [`WEBAPP_PRODUCT_AUDIT_2026-05-17.md`](WEBAPP_PRODUCT_AUDIT_2026-05-17.md) §1 avec décisions explicit **GARDER / GARDER + refondre UX / FUSIONNER / RENOMMER / CACHER / SUPPRIMER** et mapping ancien → nouveau (5 espaces cible). Pas de copy-paste de l'audit Phase A — uniquement décisions et détails route-par-route. Pure documentation, aucune modification de code.

**Auteur** : Claude Code (Opus 4.7 1M-ctx).
**Date** : 2026-05-17.
**Périmètre lecture** : `webapp/apps/shell/app/**` (32 fichiers route — `page.tsx` + `layout.tsx` + `loading.tsx` + `error.tsx` + `route.ts`) + `webapp/apps/shell/components/**` (117 composants) + `webapp/apps/shell/lib/**` (24 modules) + `webapp/packages/ui/src/**` (16 primitives) + `webapp/apps/shell/middleware.ts`.
**Mode** : READ-ONLY pure doc. Zero modification code applicatif.

---

## 0. Méthode

Audit exhaustif route-par-route. Pour chacune :

- **Chemin** disque + ligne count
- **Rôle supposé** (label sidebar/cmdk + URL)
- **Rôle réel** (qu'est-ce que le code fait vraiment, path:line de référence)
- **Type rendu** (RSC server-only / RSC + client islands / "use client" / static)
- **Data fetched** (queries Supabase, FS reads, lib helpers)
- **Actions UI** présentes (boutons, forms, modals, drag/drop)
- **Effet réel** par action (POST/mutation/server action/navigate) vs décoratif (no-op, disabled, TODO)
- **Composants** consommés
- **Perfs probables** (waterfalls, fetches sériels, gros bundles, RSC payload)
- **État honnête** : 🟢 vert / 🟠 orange / 🔴 rouge avec raison
- **Cible IA** (5 espaces : Command Center · Clients · Audits & Recos · GSG Studio · Advanced Intelligence ; ou utilitaire Doctrine/Settings ; ou public Login/Privacy/Terms)
- **DÉCISION** : GARDER tel quel · GARDER + refondre UX · FUSIONNER avec [route] · RENOMMER en [route] · CACHER de nav · SUPPRIMER

Codes couleur :
- 🟢 = E2E fonctionnel, garder le pattern, refonte UX seulement
- 🟠 = Partiel, repenser le rôle ou la wiring (mais préserver le code)
- 🔴 = Décoratif, fantôme ou cassé → cacher/supprimer/archiver

---

## 1. Inventaire routes — détail

### 1.1 `/` (home / Command Center)

- **Chemin** : `webapp/apps/shell/app/page.tsx` (273 LOC, `export const dynamic = "force-dynamic"`)
- **Rôle supposé** : nav "Overview · Command" (cf. `lib/cmdk-items.ts:49`)
- **Rôle réel** : home Command Center V26-parity, exécutif. Topbar + 5-col KPI grid + dashboard tabs + 2-col layout (Fleet sidebar + ClientHeroDetail).
- **Type rendu** : RSC server-only avec 4 client islands (`FleetPanel`, `ClientHeroDetail`, `StickyHeader`, `DashboardTabs`)
- **Data fetched** : `loadOverview()` parallèle via `Promise.allSettled` 9 queries Supabase (`page.tsx:74-94`) :
  1. `listClientsWithStats(supabase)` — clients avec recos_count/audits_count/avg_score_pct
  2. `loadCommandCenterMetrics(supabase)` — recosP0 + recentRuns + recentAudits
  3. `loadP0CountsByClient(supabase)` — Map<slug, count>
  4. `loadClosedLoopCoverage(supabase)` — coverage 4 modules
  5. `loadFleetPillarAverages(supabase)` — 6-pilier moyennes
  6. `loadPriorityDistribution(supabase)` — P0/P1/P2/P3 counts
  7. `loadBusinessBreakdown(supabase)` — table par business_category
  8. `loadPageTypeBreakdown(supabase)` — table par page_type
  9. `loadCriticalClients(supabase, 12)` — top 12
- **Actions UI** :
  - `QuickActionCard` (admin only, page.tsx:233-237) → CTAs création (effet réel)
  - URL state `?client=<slug>` ré-utilisé par `ClientHeroDetail` (page.tsx:150-153, effet réel : navigation client-side)
  - `FleetPanel` → click client → patch `?client=` (effet réel)
  - `StickyHeader` → Cmd+K palette (effet réel)
  - **`CommandCenterTopbar` → 2 actions legacy (page.tsx:224)** : "Open V26 archive" et "Copy GSG brief" (effet réel mais redondants — l'archive est un HTML statique d'avant-vente, et la copy GSG brief redirige vers `/gsg` qui n'est pas le studio)
- **Composants utilisés** : `Sidebar`, `StickyHeader`, `CommandCenterTopbar` (legacy coexistant), `CommandCenterKpis`, `FleetPanel`, `ClientHeroDetail`, `QuickActionCard`, `ClosedLoopStrip`, `DashboardTabs`, `PillarBarsFleet`, `PriorityDistribution`, `BusinessBreakdownTable`, `PageTypeBreakdownTable`, `CriticalClientsGrid`, `Card`
- **Perfs probables** : ✅ Promise.allSettled parallèle — pas de waterfall. ⚠️ Mais 9 round-trips Supabase = TTFB sensitive si latence EU. ⚠️ Page payload lourd (3 tabs dashboard + 6 panels + 5 KPIs + hero detail). Pas mesuré.
- **État honnête** : 🟢 **VERT** structurellement (RSC orchestration propre, graceful fallback). 🟠 **ORANGE UX** : mur dense de KPIs/charts/panels, pas de "today/urgent" actionnable, pas de hiérarchie. Deux topbars coexistent (`StickyHeader` + `CommandCenterTopbar` legacy).
- **Cible IA** : **Command Center** (espace 1, FR-8 PRD)
- **DÉCISION** : **GARDER + refondre UX** (FR-8) — 4 zones max (Today/Urgent · Fleet Health · Recent Runs · Next Best Actions). Drop `CommandCenterTopbar` (FR-24). Drop "Open V26 archive" CTA (lien vers HTML pré-launch sans valeur produit). Drop redondance `DashboardTabs` (peut migrer en drill-down Fleet Health). Garder `listClientsWithStats` + `loadCommandCenterMetrics`, possiblement déférer 3 dashboard queries (business/pagetype/critical) en drill-down.

### 1.2 `/clients`

- **Chemin** : `webapp/apps/shell/app/clients/page.tsx` (189 LOC)
- **Rôle supposé** : nav "Clients · Fleet"
- **Rôle réel** : Portefeuille agence — liste paginée filtrable triable des clients. URL-driven via `useUrlState` (`<FiltersBar>` + `<SortDropdown>` + `<Pagination>`, refacto SP-8).
- **Type rendu** : RSC server, filters/sort/pagination = client islands purement URL-driven
- **Data fetched** : `listClientsWithStats(supabase)` une seule query, filter/sort/paginate côté server après (`clients/page.tsx:75-91`)
- **Actions UI** : filtres (search/category/score_min/score_max), sort dropdown, pagination — tous URL state (effet réel : `router.replace` via hook)
- **Composants** : `ClientList`, `FiltersBar`, `SortDropdown`, `Pagination`, `Card`, `KpiCard`. **AUCUN `Sidebar`** (rendu inconsistant — voir §2.1).
- **Perfs probables** : ✅ 1 query → server-side filter/sort. PER_PAGE=25 = render léger.
- **État honnête** : 🟢 **VERT** — pattern propre et réutilisable
- **Cible IA** : **Clients** (espace 2)
- **DÉCISION** : **GARDER + refondre UX** modeste (PRD D1 progressive disclosure). Uniformiser Sidebar rendering (FR-2).

### 1.3 `/clients/[slug]`

- **Chemin** : `webapp/apps/shell/app/clients/[slug]/page.tsx` (163 LOC)
- **Rôle réel** : Fiche client server-rendered. Topbar (name + business_category + pills d'actions vers `/clients`, `/audits/<slug>`, `/recos/<slug>`, `/clients/<slug>/dna`, **`/funnel/<slug>`**). Hero block Brand DNA. KPIs (audits, score moyen, piliers, homepage, panel). Grid 2-col : signature radial 6-piliers + ClientDetailTabs (Audits/BrandDNA/History).
- **Type rendu** : RSC server-only avec `ClientDetailTabs` client island (tab switch local)
- **Data fetched** : `Promise.all` 3 queries (`clients/[slug]/page.tsx:30-38`) — `getClientBySlug`, `listAuditsForClient`, `listClients`, `getCurrentRole`
- **Actions UI** :
  - Links pills topbar (effet réel : navigation)
  - **`<CreateAuditTrigger>` modal** (admin only, ligne 85) — POST `/api/audits` (effet réel)
  - **`<TriggerRunButton type="capture">`** (admin only, ligne 92) — POST `/api/runs` (effet réel)
  - **`<ClientDeleteTrigger>`** (admin only, ligne 102) — DELETE `/api/clients/[id]` (effet réel)
- **Composants** : `PillarRadialChart`, `ClientHeroBlock`, `ClientDetailTabs`, `AuditsTabPanel`, `BrandDNATabPanel`, `HistoryTabPanel`, `Card`, `KpiCard`, `Pill`. **AUCUN `Sidebar`**.
- **Perfs probables** : ✅ 3 queries parallèles. ⚠️ Rich hero + chart radial peuvent être lourds sur mobile.
- **État honnête** : 🟢 **VERT** structurellement, 🟠 **ORANGE** densité — beaucoup de surfaces à digérer
- **Cible IA** : **Clients** (workspace central, espace 2)
- **DÉCISION** : **GARDER + refondre UX** (D1 progressive disclosure). Workspace central → tabs Audits / Recos / GSG / Reality / Scent / History (cf. A2 PRD). Drop link vers `/funnel/<slug>` jusqu'à ce que funnel soit re-activé ou décidé out-of-scope (cf. §1.18). Uniformiser Sidebar.

### 1.4 `/clients/[slug]/dna` (Brand DNA viewer)

- **Chemin** : `webapp/apps/shell/app/clients/[slug]/dna/page.tsx` (329 LOC)
- **Rôle réel** : Brand DNA V29 + AURA V30 viewer (palette/voice/typo/persona + sidecar tokens AURA depuis disk via `lib/aura-fs.ts`)
- **Type rendu** : RSC pur
- **Data fetched** : `getClientBySlug` + `loadAuraTokens(slug)` (FS read disk side-car JSON)
- **Actions UI** : pills nav vers `/clients/<slug>` et `/clients`. **Empty state** : bouton "Run AURA pipeline (V2)" **disabled** (ligne 312-321) titre `Trigger AURA pipeline — déféré V2`. Décoratif.
- **Composants** : `DnaSwatchesGrid`, `DnaTypographyPreview`, `DnaVoicePanel`, `DnaPersonaPanel`, `AuraTokensCard` (interne), `Card`, `KpiCard`, `Pill`. **AUCUN `Sidebar`**.
- **Perfs probables** : ✅ 1 query + 1 FS read.
- **État honnête** : 🟠 **ORANGE** — viewer solide mais "Run AURA pipeline" disabled → user comprend rien si AURA pas run. Pas de Module Maturity Model honnête.
- **Cible IA** : **Clients** (tab Brand DNA dans workspace, espace 2)
- **DÉCISION** : **FUSIONNER en tab `/clients/[slug]?tab=brand-dna`** — pas de page séparée. La fiche client devient le workspace canonique. Cacher le bouton disabled "Run AURA pipeline" ou le remplacer par `<ModuleMaturity status="ready_to_configure" reason="Pipeline V29 jamais run pour ce client" next_step={...} />` (FR-5).

### 1.5 `/audits`

- **Chemin** : `webapp/apps/shell/app/audits/page.tsx` (34 LOC — minimal)
- **Rôle réel** : Landing client picker. Charge `listClientsWithStats`, rend `<ClientPicker>` dans une Card.
- **Type rendu** : RSC, ClientPicker = client island
- **Actions UI** : sélection client → navigation `/audits/<slug>` (effet réel)
- **Composants** : `ClientPicker`, `Card`. **AUCUN Sidebar**.
- **État honnête** : 🟢 **VERT** mais minimal — c'est juste un picker
- **Cible IA** : **Audits & Recos** (espace 3)
- **DÉCISION** : **FUSIONNER** avec `/recos` en un seul "Audits & Recos" workspace (cf. PRD A2 espace 3). Cette landing peut soit (a) disparaître complètement remplacée par `/clients` (puisque audits = client-scoped), soit (b) devenir `/audits-recos` overview workspace cross-client. **Préférence : (a) drop la landing, audits accessible depuis `/clients/[slug]?tab=audits`**, sauf si l'IA cible décide de garder une vue cross-client agrégée.

### 1.6 `/audits/[clientSlug]`

- **Chemin** : `webapp/apps/shell/app/audits/[clientSlug]/page.tsx` (289 LOC)
- **Rôle réel** : Liste audits pour un client groupés par `page_type`. Tabs des page-types (URL state `?page_type=`). Pour chaque audit dans le page-type actif : `AuditQualityIndicator`, `PillarsSummary`, top-3 recos via `RichRecoCard`, lien "Voir détail".
- **Type rendu** : RSC avec parallel fetch
- **Data fetched** : `Promise.all` 2 queries + 1 boucle parallèle pour recosByAudit (`audits/[clientSlug]/page.tsx:175-191`). N audits × 1 query = `Promise.all` parallel.
- **Actions UI** : tabs page-types (URL state), liens "Voir détail" + recos cards (effet réel), pills nav
- **Composants** : `ClientPicker` (sidebar gauche), `PageTypesTabs`, `PillarsSummary`, `AuditQualityIndicator`, `ConvergedNotice`, `RichRecoCard`, `Card`, `Pill`. **AUCUN Sidebar global**.
- **Perfs probables** : 🟠 N+1 queries (1 par audit) en parallel — OK si <20 audits par client, mais pas scalable au-delà.
- **État honnête** : 🟢 **VERT** — pattern solide, "converged page-type" est intelligent
- **Cible IA** : **Audits & Recos** (drill-down par client, espace 3)
- **DÉCISION** : **GARDER + refondre UX** modeste. Uniformiser Sidebar. Refactor possible : remplacer ClientPicker sidebar par Sidebar globale + ClientPicker en topbar dropdown.

### 1.7 `/audits/[clientSlug]/[auditId]`

- **Chemin** : `webapp/apps/shell/app/audits/[clientSlug]/[auditId]/page.tsx` (150 LOC)
- **Rôle réel** : Drill-down single audit. Topbar avec score + status pill + lien vers `/audits/<slug>/<id>/judges`. Re-run capture + edit modal admin. `AuditDetailFull` payload (= scores + recos rich + screenshots).
- **Type rendu** : RSC parallèle (`Promise.all` 4 queries)
- **Data fetched** : `getClientBySlug` + `getAudit` (parallèle) puis `listRecosForAudit` + `listAuditsForClient` + `getCurrentRole` (parallèle)
- **Actions UI** :
  - `<TriggerRunButton type="capture">` (effet réel)
  - `<AuditEditTrigger>` modal admin (PATCH `/api/audits/[id]`, effet réel)
  - Link "Multi-juges" → `/audits/<slug>/<id>/judges`
  - Pills nav
- **Composants** : `AuditDetailFull`, `ConvergedNotice`, `AuditEditTrigger`, `AuditStatusPill`, `TriggerRunButton`, `Pill`. **AUCUN Sidebar**.
- **Perfs probables** : ✅ 4 queries parallel — OK
- **État honnête** : 🟢 **VERT** — pattern E2E excellent
- **Cible IA** : **Audits & Recos** (espace 3)
- **DÉCISION** : **GARDER tel quel** (refonte UX H mineure : Sidebar uniforme, design system pass)

### 1.8 `/audits/[clientSlug]/[auditId]/judges`

- **Chemin** : `webapp/apps/shell/app/audits/[clientSlug]/[auditId]/judges/page.tsx` (87 LOC)
- **Rôle réel** : Panel multi-judge V26.D — lit `audit.scores_json.judges_json` (forward-compat) ou `audit.scores_json.judges` (current). Affiche `JudgesConsensusPanel`. Empty state si pas de judges.
- **Type rendu** : RSC, mostly static
- **Data fetched** : `getClientBySlug` + `getAudit` (parallèle)
- **Actions UI** : pills nav uniquement
- **Composants** : `JudgesConsensusPanel`, `Card`, `Pill`. **`<main style={{ padding: 22 }}>`** (anti-pattern shell — pas de `gc-app`, pas de Sidebar)
- **État honnête** : 🟢 **VERT** functional mais 🟠 **ORANGE** chrome (no Sidebar)
- **Cible IA** : **Audits & Recos** (espace 3)
- **DÉCISION** : **GARDER + uniformiser shell** (FR-2 Sidebar)

### 1.9 `/recos`

- **Chemin** : `webapp/apps/shell/app/recos/page.tsx` (197 LOC)
- **Rôle réel** : Aggregator cross-clients. Filters (priority/criterion/category) + sort (lift_desc/priority_asc) + pagination. KPIs (total/clients/criteria/filtered/per-page). `RecoAggregatorList` rend les rows.
- **Type rendu** : RSC server, filters/sort/pagination URL state
- **Data fetched** : `listRecosAggregate(supabase)` — 1 query joinable
- **Actions UI** : filtres, sort, pagination, pills nav (tous effet réel)
- **Composants** : `RecoAggregatorList`, `FiltersBar`, `SortDropdown`, `Pagination`, `Card`, `KpiCard`, `Pill`. **AUCUN Sidebar**.
- **Perfs probables** : ✅ 1 query → server-side filter/sort
- **État honnête** : 🟢 **VERT**
- **Cible IA** : **Audits & Recos** (espace 3)
- **DÉCISION** : **FUSIONNER ou TAB** dans "Audits & Recos" workspace. Soit (a) garder `/recos` comme vue dédiée cross-client agrégée + `/audits` drill-down par client + `/audits/[c]/[id]` détail, soit (b) en faire un tab dans un workspace fusionné. Préférence Mathis-dépendante. Uniformiser Sidebar (FR-2).

### 1.10 `/recos/[clientSlug]`

- **Chemin** : `webapp/apps/shell/app/recos/[clientSlug]/page.tsx` (44 LOC — minimal)
- **Rôle réel** : Liste recos pour un client précis. Counts P0/P1/P2/P3. `RecoList` rend.
- **Type rendu** : RSC pur
- **Data fetched** : `getClientBySlug` + `listRecosForClient` (séquentiel par await — ⚠️ pas `Promise.all`)
- **Actions UI** : pills nav
- **Composants** : `RecoList`, `Card`, `Pill`. **AUCUN Sidebar**.
- **Perfs probables** : ⚠️ Mini-waterfall (2 awaits séquentiels au lieu de parallel)
- **État honnête** : 🟠 **ORANGE** — fonctionnel mais minimal et waterfall
- **Cible IA** : **Audits & Recos** (espace 3)
- **DÉCISION** : **FUSIONNER en tab `/clients/[slug]?tab=recos`** + uniformiser Sidebar. Ou rediriger vers `/audits/[clientSlug]` (qui montre déjà les top recos par audit). Évaluer redondance avec D2 PRD.

### 1.11 `/gsg`

- **Chemin** : `webapp/apps/shell/app/gsg/page.tsx` (198 LOC)
- **Rôle réel** : **Design Grammar viewer V30** (7 artefacts par client : tokens.css, tokens.json, component_grammar, section_grammar, composition_rules, brand_forbidden_patterns, quality_gates) via `lib/design-grammar-fs.ts`. ClientPicker form GET. Link header vers `/gsg/handoff` (Brief Wizard).
- **Type rendu** : RSC, viewer = `DesignGrammarViewer` (et un `TokensCssPreview` iframe client island)
- **Data fetched** : `listClientsWithStats` + `listClientsWithDesignGrammar()` (FS walk) + `loadDesignGrammar(slug)` (FS read JSON)
- **Actions UI** : ClientPicker dropdown form GET (effet réel), pills nav vers `/gsg/handoff`
- **Composants** : `DesignGrammarViewer`, `Card`, `Pill`. **AUCUN Sidebar**.
- **Perfs probables** : ✅ FS reads server-side rapides en local, ⚠️ Vercel ne sert pas `data/captures/` → graceful empty
- **État honnête** : 🟠 **ORANGE** — **viewer de référence Design Grammar mais l'utilisateur croit que c'est le Studio**. Aucun CTA "Start a new run" cross-route au-delà du link "Brief Wizard →" header.
- **Cible IA** : **GSG Studio** (espace 4)
- **DÉCISION** : **RENOMMER en `/gsg/design-grammar/[client]`** (FR-10). La route `/gsg` devient un **redirect → `/gsg/studio`** (qui sera créé en F5 PRD). Le viewer Design Grammar reste comme sous-page atteignable depuis le Studio. Aujourd'hui c'est trompeur.

### 1.12 `/gsg/handoff`

- **Chemin** : `webapp/apps/shell/app/gsg/handoff/page.tsx` (316 LOC)
- **Rôle réel** : **C'est ICI que le brief wizard vit, pas dans `/gsg`**. 5 modes (complete/replace/extend/elevate/genesis), `<GsgModesSelector>`, `<BriefJsonViewer>`, `<ControlledPreviewPanel>`, `<CopyBriefButton>`, `<EndToEndDemoFlow>`, et enfin `<HandoffBriefSection>` qui paire `<BriefWizard>` + `<GsgRunPreview>`.
- **Type rendu** : RSC + multiples client islands
- **Data fetched** : `listClientsWithStats` + `listGsgDemoFiles()` (FS) + `listAuditsForClient(client.id)` (first audit pour brief metadata)
- **Actions UI** :
  - `GsgModesSelector` : URL state `?mode=` (effet réel)
  - ClientPicker form GET (effet réel)
  - `CopyBriefButton` : clipboard write (effet réel)
  - "Open preview in new tab" → `/api/gsg/[slug]/html` (effet réel)
  - **`BriefWizard` + `TriggerRunButton`** dans `HandoffBriefSection` → POST `/api/runs` `type=gsg` (effet réel)
  - **`GsgRunPreview` iframe** subscribe Realtime channel `public:runs` filtrée sur `id=runId` (effet réel)
  - **⚠️ "Subscribe to a run UUID manually (smoke test)"** input texte (`HandoffBriefSection.tsx:75-100`) — paste UUID pour preview. **C'est un seam de dev oublié en prod**. Décoratif/dev-only.
- **Composants** : `GsgModesSelector`, `BriefJsonViewer`, `ControlledPreviewPanel`, `CopyBriefButton`, `EndToEndDemoFlow`, `HandoffBriefSection`, `BriefWizard`, `GsgRunPreview`, `Card`, `Pill`. **AUCUN Sidebar**.
- **Perfs probables** : ✅ Parallèle propre
- **État honnête** : 🟠 **ORANGE** — wizard solide mais 3 problèmes : (1) `output_path` race worker (preview affiche "worker doit être patché" si race) ; (2) UUID paste manual seam exposé en prod ; (3) le wizard n'a pas son URL stable (vit comme une section dans `/gsg/handoff` qui mixe brief déterministe + wizard live)
- **Cible IA** : **GSG Studio** (espace 4)
- **DÉCISION** : **REFONDRE en `/gsg/studio` + `/gsg/runs/[id]`** (FR-10/FR-11/FR-12). Le wizard devient la home du Studio. À la submit du wizard → redirect automatique vers `/gsg/runs/[id]` (preview iframe + QA + export). **Drop l'input "paste UUID manuel"**. `/gsg/handoff` peut soit (a) rediriger vers `/gsg/studio`, soit (b) être renommée et garder uniquement le viewer "brief déterministe" (sans wizard live, qui migre vers le Studio).

### 1.13 `/learning`

- **Chemin** : `webapp/apps/shell/app/learning/page.tsx` (114 LOC)
- **Rôle réel** : Learning Lab — proposals V29 (audit-based) + V30 (data-driven) lus depuis FS `data/learning/{audit_based,data_driven}_proposals/`. KPI strip `ProposalStats`. `<LifecycleBarsChart>` 13-state. **Vote queue `<ProposalQueue>` 4 boutons (accept/reject/refine/defer) avec optimistic UI** → PATCH `/api/learning/proposals/review` (effet réel — écrit sidecar `<id>.review.json`).
- **Type rendu** : RSC + client islands (ProposalQueue, LifecycleBarsChart)
- **Data fetched** : `listV29Proposals()` (FS) + `listV30Proposals()` (FS) + `loadLifecycleCounts(supabase)` (Supabase view)
- **Actions UI** :
  - Vote queue : POST per vote (effet réel)
  - Browse list filter (effet réel)
  - Pills nav
- **Composants** : `ProposalList`, `ProposalQueue`, `ProposalStats`, `LifecycleBarsChart`, `Card`, `Pill`. **`<main style={{ padding: 22 }}>`** anti-pattern shell.
- **Perfs probables** : ✅ FS rapide, Supabase view 1 query
- **État honnête** : 🟢 **VERT** functional MAIS 🔴 **OPEN QUESTION** : Mathis a explicitement questionné l'approche Bayesian doctrine update (PRD §6 Q2). UI build deferred bloqué sur research spike `LEARNING_LAYER_APPROACH_DECISION.md` (FR-18).
- **Cible IA** : **Advanced Intelligence** (espace 5, regroupé avec Reality/GEO/Experiments/Scent)
- **DÉCISION** : **GARDER tel quel** structurellement (vote queue fonctionne) mais **NE PAS REFONDRE l'UI avant la decision spike G3** (FR-18). Le risque c'est de construire une refonte UX par-dessus une approche que Mathis va changer. Uniformiser Sidebar (FR-2).

### 1.14 `/learning/[proposalId]`

- **Chemin** : `webapp/apps/shell/app/learning/[proposalId]/page.tsx` (44 LOC)
- **Rôle réel** : Detail d'une proposal. `<ProposalDetail>` rend le form accept/reject/defer (écrit sidecar `<id>.review.json`).
- **Type rendu** : RSC + client island ProposalDetail
- **Data fetched** : `findProposalById(proposalId)` (FS walk)
- **Actions UI** : form vote (effet réel)
- **Composants** : `ProposalDetail`, `Pill`. **`<main style={{ padding: 22 }}>`** anti-pattern.
- **État honnête** : 🟢 fonctionnel — mais **bloqué par la decision spike** comme `/learning`
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER** (post-decision spike G3). Uniformiser Sidebar.

### 1.15 `/experiments`

- **Chemin** : `webapp/apps/shell/app/experiments/page.tsx` (76 LOC)
- **Rôle réel** : V27 Experiment Engine pane. 4 panels : `<SampleSizeCalculator>` (interactif, calcul stats power/effect-size), `<RampUpMatrix>` (presets), `<KillSwitchesMatrix>` (static reference), `<ActiveExperimentsList>` (server-fetched depuis Supabase `experiments` table).
- **Type rendu** : RSC + 3 client islands interactives
- **Data fetched** : `listExperiments()` (`lib/experiments-data.ts`) — swallow errors → []
- **Actions UI** : Calculator interactif (effet réel sur state local), ramp-up presets, **`<ActiveExperimentsList>`** affiche les rows. **Aucune UI pour CRÉER un experiment** depuis l'app.
- **Composants** : `SampleSizeCalculator`, `RampUpMatrix`, `KillSwitchesMatrix`, `ActiveExperimentsList`, `Card`. **AUCUN Sidebar**.
- **État honnête** : 🟢 calc fonctionne, 🔴 **Dispatcher `experiment` worker = `print("not implemented")`** (`growthcro/worker/dispatcher.py:36-47` cf. audit Phase A §2.2). Si un experiment était trigger via POST `/api/runs`, le worker le marquerait "completed" sans rien faire. Le table `experiments` est créé (migration `20260514_0021`) avec RLS, mais zéro mutation côté API (audit Phase A §2.1). **Mensonge UX potentiel**.
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER tel quel** mais **bloquer par decision spike G4 "implement vs archive"** (FR-19). Options : (a) implement vraiment le dispatcher (run A/B contre Reality Layer ou GrowthBook), (b) archive type+route+table, (c) garder calculator standalone retirer dispatcher. **Pas de refonte UX avant décision Mathis**. Uniformiser Sidebar.

### 1.16 `/reality`

- **Chemin** : `webapp/apps/shell/app/reality/page.tsx` (190 LOC)
- **Rôle réel** : Reality Monitor V30 — fleet root. 51 clients × 5 metrics heat map (`fetchFleetHeatMap` depuis `reality_snapshots` Supabase). Pilote candidates list mixant Supabase + filesystem + 2 hardcoded hints (`weglot`, `japhy`). RecentRunsTracker. "How to wire a client" card guide.
- **Type rendu** : RSC + client islands (RealityHeatMap, RecentRunsTracker)
- **Data fetched** : `listClientsWithStats(supabase)` + `listRealityClients()` (FS) + `clientCredentialsReport(slug)` per row (cycle de N FS reads + N `latestSnapshotForClient`) + `fetchFleetHeatMap(supabase, ...)` + `listRecentRuns(supabase, { limit: 20, type: "reality" })`
- **Actions UI** : liens vers `/reality/<slug>`, pills nav. RecentRunsTracker = client island Realtime subscribe.
- **Composants** : `RecentRunsTracker`, `RealityHeatMap`, `Card`, `Pill`. **`<main style={{ padding: 22 }}>`** anti-pattern shell.
- **Perfs probables** : 🟠 N FS reads + Supabase = potentiel waterfall. 51 clients × 5 cells = render heat map non-trivial.
- **État honnête** : 🟠 **ORANGE** — skeleton honnête (graceful "0/N configured") MAIS aucun **Module Maturity Model** explicite : l'user ne sait pas si c'est cassé, pas configuré, ou en attente. Backend wiring OAuth deferred (cf. PRD §6 Q1 Mathis decision pending coût/value).
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER + refondre UX honest activation** (FR-5/FR-16). Ajouter `<ModuleHeader status="ready_to_configure" reason="OAuth credentials missing" next_step={...}>`. **Pas de wire OAuth, pas de poller config** (deferred Mathis). Uniformiser Sidebar.

### 1.17 `/reality/[clientSlug]`

- **Chemin** : `webapp/apps/shell/app/reality/[clientSlug]/page.tsx` (191 LOC)
- **Rôle réel** : Per-client drilldown. CredentialsGateGrid (5 OAuth cards avec Connect CTA) + 5 sparklines metrics + grille V26.C legacy + snapshot metrics.
- **Type rendu** : RSC + client islands
- **Data fetched** : `clientCredentialsReport(slug)` (FS) + `listSnapshotsForClient(slug)` (FS) + Supabase clientId lookup + `fetchClientCredentialsGate(supabase, clientId)` + 5 `fetchMetricSparkline(...)` (Promise.all)
- **Actions UI** : "Connect" CTAs dans `CredentialsGateGrid` (effet réel : redirect vers OAuth flow `/auth/<connector>/callback`) — mais credentials ne sont PAS provisionnées côté Mathis (cf. audit Phase A).
- **Composants** : `CredentialsGateGrid`, `CredentialsGrid`, `RealitySparkline`, `SnapshotMetricsCard`, `Card`, `Pill`. **`<main style={{ padding: 22 }}>`** anti-pattern.
- **Perfs probables** : ⚠️ 7 round-trips Supabase + 2 FS reads (semi-sequential)
- **État honnête** : 🟠 **ORANGE** — backend OK skeleton mais OAuth dance post-MVP, credentials manquantes
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER + Module Maturity** (FR-5/FR-16). Uniformiser Sidebar.

### 1.18 `/funnel/[clientSlug]`

- **Chemin** : `webapp/apps/shell/app/funnel/[clientSlug]/page.tsx` (190 LOC). **L'audit Phase A §1.3 disait "ghost route, pas de page.tsx" → FAUX. Cette route existe.** Mais elle n'est pas dans `lib/cmdk-items.ts` (donc invisible dans la sidebar/cmdk).
- **Rôle réel** : Viz funnel pour un client. Lit `client.brand_dna_json.funnel` (V2 schema) sinon dérive de l'audit le plus récent. 5-step cohort cascade + retention bars. Source pill (ga4_measured / ga4_estimate / manual / audit_derived).
- **Type rendu** : RSC pur
- **Data fetched** : `getClientBySlug` + (fallback) `listAuditsForClient`
- **Actions UI** : pills nav
- **Composants** : `FunnelStepsViz`, `FunnelDropOffChart`, `Card`, `KpiCard`, `Pill`. **`<main style={{ padding: 22 }}>`** anti-pattern.
- **État honnête** : 🟠 **ORANGE** — route fonctionnelle mais (a) non listée dans cmdk-items donc invisible (`clients/[slug]/page.tsx:80` est le SEUL link vers `/funnel/<slug>`), (b) source data fragile (`brand_dna_json.funnel` n'est pas dans le schéma Supabase canonique, lecture défensive), (c) zéro mécanisme de capture funnel
- **Cible IA** : ambigu — **Clients** (tab funnel) ou **Advanced Intelligence** (vue funnel-fleet ?)
- **DÉCISION** : **CACHER de la nav** (FR-25) jusqu'à décision Mathis : (a) le promouvoir en module first-class avec capture funnel pipeline (= grosse pièce, hors scope epic UX), (b) le fusionner en tab `/clients/[slug]?tab=funnel` (mais sans capture pipeline c'est juste un viewer d'estimation audit-derived), (c) supprimer la route + drop le link dans `/clients/[slug]:80`. **Préférence MVP : (c) supprimer** — l'audit Phase A le voyait comme "ghost", c'est en réalité une route orpheline non documentée. Marquer SUPPRIMER (FR-24) dans la liste rouge.

### 1.19 `/geo`

- **Chemin** : `webapp/apps/shell/app/geo/page.tsx` (70 LOC)
- **Rôle réel** : GEO Monitor fleet. `<EnginePresenceCards>` (Claude/ChatGPT/Perplexity) + `<QueryBankViewer>` (20-query bank from disk).
- **Type rendu** : RSC pur
- **Data fetched** : `Promise.all([listGeoAudits(null), loadQueryBank()])`
- **Actions UI** : pills nav
- **Composants** : `EnginePresenceCards`, `QueryBankViewer`, `Card`. **AUCUN Sidebar**.
- **État honnête** : 🟠 **ORANGE** — fonctionnel mais `rows.length === 0` empty state explique que OPENAI_API_KEY + PERPLEXITY_API_KEY manquent (cf. `/geo/page.tsx:51-67`). Skeleton honnête, mais pas de Module Maturity Model.
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER + UX honest activation** (FR-5/FR-17). `<ModuleMaturity status="ready_to_configure" reason="OPENAI_API_KEY / PERPLEXITY_API_KEY missing" next_step={...} />`. Uniformiser Sidebar.

### 1.20 `/geo/[clientSlug]`

- **Chemin** : `webapp/apps/shell/app/geo/[clientSlug]/page.tsx` (84 LOC)
- **Rôle réel** : Per-client GEO drilldown. EnginePresenceCards scoped + PerClientGeoGrid (engines × queries).
- **Type rendu** : RSC pur
- **Data fetched** : `getClientBySlug` puis `Promise.all([listGeoAudits(client.id), loadQueryBank()])`
- **Actions UI** : pills nav
- **Composants** : `EnginePresenceCards`, `PerClientGeoGrid`, `Card`. **AUCUN Sidebar**.
- **État honnête** : 🟠 **ORANGE** — fonctionnel + empty state honnête mais sans Maturity
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER + UX honest activation**. Uniformiser Sidebar.

### 1.21 `/scent`

- **Chemin** : `webapp/apps/shell/app/scent/page.tsx` (123 LOC)
- **Rôle réel** : Scent Trail fleet. Lit `data/captures/<client>/scent_trail.json` via `listScentTrails()` (FS). KPIs + Fleet table + top-6 drilldown (worst scent_score d'abord) avec `<ScentTrailDiagram>` + `<BreaksList>` par client.
- **Type rendu** : RSC pur
- **Data fetched** : `listScentTrails()` (FS walk)
- **Actions UI** : pills nav
- **Composants** : `ScentFleetKPIs`, `ScentFleetTable`, `ScentTrailDiagram`, `BreaksList`, `Card`. **AUCUN Sidebar**.
- **État honnête** : 🟠 **ORANGE** — fonctionnel mais "Aucun scent trail" sur 95% des installs (cross-channel capture pipeline jamais run en prod, cf. audit Phase A). Le viewer est solide, l'input data est absent.
- **Cible IA** : **Advanced Intelligence** (espace 5)
- **DÉCISION** : **GARDER + UX honest empty state** ou **CACHER de nav** jusqu'à ce qu'il y ait un pipeline batch runs configurable. Préférence : `<ModuleMaturity status="no_data" reason="Cross-channel captures deferred" next_step={...} />`. Uniformiser Sidebar.

### 1.22 `/doctrine`

- **Chemin** : `webapp/apps/shell/app/doctrine/page.tsx` (152 LOC)
- **Rôle réel** : V3.2.1 piliers viewer pédagogique. ClosedLoopDiagram SVG inline (7 nodes) + DogfoodCard + PillierBrowser (7 piliers tab + CritereDetail grid) + Notes V3.2.1→V3.3.
- **Type rendu** : RSC pur + client island PillierBrowser
- **Data fetched** : `getUserEmail()` (Supabase auth) + `getCurrentRole()` — PILIERS metadata = constante inline (hardcoded)
- **Actions UI** : tabs piliers (client state), pills nav
- **Composants** : `Sidebar`, `ViewToolbar`, `Card`, `ClosedLoopDiagram`, `DogfoodCard`, `PillierBrowser`. **A LE Sidebar** (consistant avec home/settings).
- **État honnête** : 🟢 **VERT** — stateless, propre, pédagogique. ⚠️ Seule route qui utilise `ViewToolbar` (autres pages utilisent `<div className="gc-topbar">`). Redondance pattern. Cf. §2.3.
- **Cible IA** : **Utility · Doctrine** (référence, hors workflow)
- **DÉCISION** : **GARDER tel quel** + drop `ViewToolbar` import (le remplacer par `gc-topbar` pattern). Audit Phase A §1.4 le note : "ViewToolbar utilisé seulement sur /doctrine, redondant".

### 1.23 `/settings`

- **Chemin** : `webapp/apps/shell/app/settings/page.tsx` (116 LOC)
- **Rôle réel** : Settings admin avec 4 tabs (Account, Team, Usage, API). Role-gated via `getCurrentRole()`. Server-loaded usage counts + org members list.
- **Type rendu** : RSC + client island SettingsTabs
- **Data fetched** : `supabase.auth.getUser()` + `loadUsageCounts(supabase)` + `listOrgMembers(supabase)` + `getCurrentRole()` + `getAppConfig()`
- **Actions UI** : tabs (client state), team invite form (TeamTab → POST `/api/team/invite`, effet réel), reveal anon key + signed-URLs (ApiTab)
- **Composants** : `Sidebar`, `SettingsTabs`, `AccountTab`, `TeamTab`, `UsageTab`, `ApiTab`. **A LE Sidebar**.
- **État honnête** : 🟢 **VERT**
- **Cible IA** : **Utility · Settings**
- **DÉCISION** : **GARDER tel quel**

### 1.24 `/audit-gads`

- **Chemin** : `webapp/apps/shell/app/audit-gads/page.tsx` (107 LOC)
- **Rôle réel** : Placeholder "produit parallèle Growth Society" Audit Google Ads. Render instructions CLI : `python -m growthcro.audit_gads.cli --client <slug> --csv <path>`. Bouton "New audit (CSV)" **disabled** avec `title="Form UI à brancher post-MVP"` (`audit-gads/page.tsx:46`).
- **Type rendu** : RSC quasi-statique
- **Data fetched** : `loadUser()` + `getCurrentRole()` (juste pour Sidebar)
- **Actions UI** : link README GitHub external, bouton disabled, **aucune action réelle**
- **Composants** : `Sidebar`, `Card`. **A LE Sidebar**.
- **État honnête** : 🔴 **ROUGE** — décoratif. Le user clique "New audit (CSV)" et rien ne se passe.
- **Cible IA** : (caché) ou future Audits & Recos extension
- **DÉCISION** : **CACHER de la nav** (FR-25) — retirer `/audit-gads` de `lib/cmdk-items.ts:63` (group `agency`). La route reste accessible par URL directe pour ne pas casser les bookmarks, mais invisible dans Sidebar/CmdK. Reviendra quand form UI + skill orchestration (skill `anthropic-skills:gads-auditor`) seront wirés.

### 1.25 `/audit-meta`

- **Chemin** : `webapp/apps/shell/app/audit-meta/page.tsx` (107 LOC)
- **Rôle réel** : Idem `/audit-gads` mais pour Meta Ads. Bouton disabled, instructions CLI.
- **Type rendu** : RSC quasi-statique
- **Actions UI** : aucune action réelle
- **Composants** : `Sidebar`, `Card`. **A LE Sidebar**.
- **État honnête** : 🔴 **ROUGE** — décoratif
- **Cible IA** : (caché)
- **DÉCISION** : **CACHER de la nav** (FR-25) — retirer `/audit-meta` de `lib/cmdk-items.ts:64`.

### 1.26 `/login` (public)

- **Chemin** : `webapp/apps/shell/app/login/page.tsx` (110 LOC)
- **Rôle réel** : Connexion Supabase password OR magic link. URL state `?redirect=`.
- **Type rendu** : `"use client"` (form, useState, useRouter)
- **Data fetched** : aucune (auth call directe)
- **Actions UI** : signInWithPassword OR signInWithOtp (effet réel)
- **Composants** : `Button`. Pas de Sidebar (public).
- **État honnête** : 🟢 **VERT**
- **Cible IA** : **Public** (hors espaces, middleware passe)
- **DÉCISION** : **GARDER tel quel**

### 1.27 `/auth/callback` + `/auth/signout` (route handlers)

- **Chemin** : `webapp/apps/shell/app/auth/callback/route.ts` + `webapp/apps/shell/app/auth/signout/route.ts`
- **Rôle réel** : Supabase auth callbacks (code exchange / signout)
- **Type rendu** : route.ts (GET/POST)
- **Actions UI** : N/A (server route)
- **État honnête** : 🟢 **VERT**
- **DÉCISION** : **GARDER tel quel**

### 1.28 `/privacy` (public)

- **Chemin** : `webapp/apps/shell/app/privacy/page.tsx` (38 LOC)
- **Rôle réel** : Page RGPD statique. Droits utilisateurs, données collectées, conservation, sous-traitants.
- **Type rendu** : RSC statique
- **État honnête** : 🟢 **VERT**
- **Cible IA** : **Public**
- **DÉCISION** : **GARDER tel quel**

### 1.29 `/terms` (public)

- **Chemin** : `webapp/apps/shell/app/terms/page.tsx` (20 LOC)
- **Rôle réel** : CGU statiques.
- **Type rendu** : RSC statique
- **État honnête** : 🟢 **VERT**
- **Cible IA** : **Public**
- **DÉCISION** : **GARDER tel quel**

### 1.30 API routes — résumé

19 routes API. Toutes admin-gated via `requireAdmin()` ou RLS-bound. Sources : `webapp/apps/shell/app/api/**`. Pour info :

| Route | Méthodes | Effet | Statut |
|---|---|---|---|
| `/api/audits` | GET POST | List + create audit row (sans run chained) | 🟢 LIVE |
| `/api/audits/[id]` | GET PATCH DELETE | CRUD audit | 🟢 LIVE |
| `/api/clients` | GET POST | List + create | 🟢 LIVE |
| `/api/clients/[id]` | GET PATCH DELETE | CRUD client | 🟢 LIVE |
| `/api/recos/[id]` | GET PATCH DELETE | CRUD reco | 🟢 LIVE |
| `/api/recos/[id]/lifecycle` | PATCH | Update lifecycle_status enum | 🟢 LIVE (2 endpoints pour reco update — FR-13/FR-14) |
| `/api/runs` | GET POST | Trigger pipeline run (worker daemon picks up). 9 types whitelist (`runs/route.ts:25-35`) | 🟢 LIVE |
| `/api/runs/[id]` | GET | Read run + stdout/stderr tail | 🟢 LIVE |
| `/api/team/invite` | POST | Invite member | 🟢 LIVE |
| `/api/learning/proposals/review` | POST | Write `<id>.review.json` sidecar | 🟢 LIVE |
| `/api/cron/reality-poll` | GET | External cron trigger reality poll | ⚠️ UNTESTED (depends external Vercel cron config) |
| `/api/screenshots/[client]/[page]/[filename]` | GET | Serve PNG from FS or Storage redirect | 🟢 LIVE (excluded from auth middleware) |
| `/api/design-grammar/[client]/[file]` | GET | Serve DG artefact (JSON/CSS) | 🟢 LIVE |
| `/api/gsg/[slug]/html` | GET | Serve GSG HTML with CSP strict | 🟢 LIVE |
| `/api/auth/catchr/callback` | GET | OAuth callback Catchr | 🟢 LIVE (creds missing) |
| `/api/auth/clarity/callback` | GET | OAuth callback Microsoft Clarity | 🟢 LIVE (creds missing) |
| `/api/auth/google-ads/callback` | GET | OAuth callback Google Ads | 🟢 LIVE (creds missing) |
| `/api/auth/meta-ads/callback` | GET | OAuth callback Meta Ads | 🟢 LIVE (creds missing) |
| `/api/auth/shopify/callback` | GET | OAuth callback Shopify | 🟢 LIVE (creds missing) |

**Trou critique connu (cf. audit Phase A §2.3)** : `POST /api/audits` crée audit row mais **ne déclenche aucun run**. L'UI doit POST 3x `/api/runs` (capture, score, recos) séparément. **Aucune orchestration chained** côté backend. FR-9 propose nouveau worker handler `audit_full` qui chaîne les 3 étapes.

---

## 2. Composants globaux — inventaire

### 2.1 Sidebar (`webapp/apps/shell/components/Sidebar.tsx`)

- **Fichier** : 155 LOC, `"use client"`
- **Source nav** : `lib/cmdk-items.ts` (single source of truth Sprint 11/Task 013, partagé avec CmdKPalette)
- **Nav groups** (`cmdk-items.ts:40-45`) : Pipeline (Overview/Clients/Audits/Recos) · Studio (GSG/Doctrine/Reality/Learning/Scent/Experiments/GEO) · Agency Tools (audit-gads/audit-meta) · Admin (Settings)
- **Badges** : counts clients/audits/recosP0/learning passés par parent (home seul aujourd'hui)
- **Utilisé dans** : `app/page.tsx:214`, `app/settings/page.tsx:93`, `app/audit-gads/page.tsx:26`, `app/doctrine/page.tsx:110`, `app/audit-meta/page.tsx:26`, **+ shells de `app/loading.tsx` et `app/error.tsx`** comme placeholder.
- **NON utilisé dans** : `/clients`, `/clients/[slug]`, `/clients/[slug]/dna`, `/audits`, `/audits/[clientSlug]`, `/audits/[clientSlug]/[auditId]`, `/audits/[clientSlug]/[auditId]/judges`, `/recos`, `/recos/[clientSlug]`, `/gsg`, `/gsg/handoff`, `/learning`, `/learning/[proposalId]`, `/experiments`, `/reality`, `/reality/[clientSlug]`, `/funnel/[clientSlug]`, `/geo`, `/geo/[clientSlug]`, `/scent`. **20 routes sur 25 sans Sidebar**.
- **Cohérence** : 🔴 **incohérence majeure** — la sidebar n'apparaît que sur 5 routes (home + settings + audit-gads + audit-meta + doctrine). C'est précisément les 5 routes qui ont `<div className="gc-app">` comme wrapper (cf. grep §config).
- **DÉCISION** : **GARDER + uniformiser** (FR-2 PRD). Rendre Sidebar sur toutes les routes sauf `/login`, `/privacy`, `/terms`, `/auth/*`. Probablement via `<RootShell>` component dans un nested layout (à concevoir B1 PRD).

### 2.2 StickyHeader (`webapp/apps/shell/components/chrome/StickyHeader.tsx`)

- **Fichier** : 99 LOC, `"use client"`
- **Rôle** : Layout shell global page chrome — DynamicBreadcrumbs (left) + Cmd+K search button (center) + actions slot (right). Cmd+K et "/" shortcuts (sprint 11).
- **Utilisé dans** : `app/page.tsx:222` (home seul, conditionnel sur `user` connecté)
- **NON utilisé dans** : aucune autre route
- **Cohérence** : 🔴 **présent sur 1 seule route** alors qu'il devrait être chrome global
- **DÉCISION** : **GARDER + uniformiser**. Le déplacer dans un nested layout pour qu'il render sur toutes les routes authenticated avec Sidebar.

### 2.3 CommandCenterTopbar (`webapp/apps/shell/components/command-center/CommandCenterTopbar.tsx`)

- **Fichier** : 31 LOC, server component
- **Rôle** : H1 "Command Center" + subtitle + 2 actions ("Open V26 archive" → `/deliverables/GrowthCRO-V26-WebApp.html` HTML statique pré-launch ; "Copy GSG brief" → `/gsg`)
- **Utilisé dans** : `app/page.tsx:224` (uniquement)
- **Conflit avec StickyHeader** : oui — `app/page.tsx:222-224` rend les DEUX, le commentaire `page.tsx:218-220` admet "V1 ships with the legacy CommandCenterTopbar still in place ; cleanup of the per-page topbars is tracked as a follow-up"
- **DÉCISION** : **SUPPRIMER** (FR-24). Dead code legacy. Aucun replacement nécessaire — StickyHeader + page-level `<div className="gc-topbar">` couvrent le besoin.

### 2.4 ViewToolbar (`webapp/apps/shell/components/ViewToolbar.tsx`)

- **Fichier** : 35 LOC, server component
- **Rôle** : Composition Breadcrumbs + title + subtitle + actions (compatibility wrapper SP-6)
- **Utilisé dans** : `app/doctrine/page.tsx:112` seul
- **Cohérence** : 🔴 redondant — toutes les autres routes utilisent un `<div className="gc-topbar"><div className="gc-title"><h1>...</h1></div>...</div>` inline pattern. ViewToolbar duplicate ce pattern dans une abstraction qui n'a qu'un seul caller.
- **DÉCISION** : **SUPPRIMER** (FR-24) — refactor `/doctrine` pour utiliser le pattern inline `gc-topbar` comme les autres routes. Drop `ViewToolbar.tsx`. Drop `Breadcrumbs.tsx` deprecation shim aussi.

### 2.5 Breadcrumbs (`webapp/apps/shell/components/Breadcrumbs.tsx`)

- **Fichier** : 10 LOC, **DEPRECATED shim re-export DynamicBreadcrumbs**
- **Utilisé dans** : `components/ViewToolbar.tsx:13` seul (qui sera supprimé en 2.4)
- **DÉCISION** : **SUPPRIMER** (FR-24) — drop le shim après cleanup ViewToolbar.

### 2.6 DynamicBreadcrumbs (`webapp/apps/shell/components/chrome/DynamicBreadcrumbs.tsx`)

- **Fichier** : 108 LOC, `"use client"`
- **Rôle** : Pathname-derived breadcrumbs. SEGMENT_LABELS map FR, UUID humanize, HIDDEN_PATHS = `["/", "/login", "/privacy", "/terms"]`
- **Utilisé dans** : `StickyHeader` (donc indirectement uniquement sur home)
- **DÉCISION** : **GARDER + uniformiser** (devient global avec StickyHeader)

### 2.7 CmdKPalette (`webapp/apps/shell/components/chrome/CmdKPalette.tsx`)

- **Rôle** : Palette Cmd+K — list nav entries + recent items (localStorage `gc-cmdk-recent`) + admin actions
- **Source** : `lib/cmdk-items.ts` (NAV_ENTRIES)
- **Utilisé dans** : `StickyHeader` (donc home seul)
- **DÉCISION** : **GARDER + uniformiser** (rendre global avec StickyHeader)

### 2.8 TriggerRunButton (`webapp/apps/shell/components/runs/TriggerRunButton.tsx`)

- **Fichier** : 101 LOC, `"use client"`
- **Rôle** : Bouton CTA → POST `/api/runs` avec metadata typé (client_slug, page_type, url, mode, audience, ...). Affiche `<RunStatusPill>` inline avec runId + Realtime subscribe.
- **Utilisé dans** : `/clients/[slug]` (capture), `/audits/[c]/[id]` (re-run capture), `/gsg/handoff` (gsg) via `HandoffBriefSection`
- **Cohérence** : 🟢 pattern propre et réutilisable
- **DÉCISION** : **GARDER tel quel** — primitive d'action canonical. FR-7 propose un `<ActionButton>` plus générique mais TriggerRunButton est déjà un bon foundation.

### 2.9 RunStatusPill (`webapp/apps/shell/components/runs/RunStatusPill.tsx`)

- **Rôle** : Pill amber "pending" → cyan "running" → green "completed" / red "failed". Subscribe Realtime channel `public:runs` filtré sur `id=runId`.
- **Utilisé dans** : `TriggerRunButton`, `AuditStatusPill`
- **DÉCISION** : **GARDER tel quel** (mais worker liveness invisibility doit être adressée par FR-3/FR-4 system_health table)

### 2.10 Modals patterns (`CreateAuditModal`, `EditAuditModal`, `EditRecoModal`, `AddClientModal`, `DeleteConfirmModal`, `AuditEditTrigger`, `RecoEditTrigger`, `ClientDeleteTrigger`)

- **Pattern** : Trigger button + Modal opens + form + Submit → POST/PATCH/DELETE API → toast + close
- **Primitive** : `@growthcro/ui Modal`
- **Cohérence** : 🟠 — pattern manuel à chaque fois (state, isOpen, onClose, onSubmit, error). Pas de hook `useEdit` global (FR-13).
- **DÉCISION** : **GARDER + factoriser** en `useEdit` hook + Modal canonical (FR-13). Pas de refonte structurelle — les modals fonctionnent.

### 2.11 Forms patterns

- **Pattern** : Form inline avec validation manuelle, error inline rouge, success inline vert
- **Exemples** : login (password/magic), AddClientModal, CreateAuditModal, BriefWizard
- **Cohérence** : 🟠 inconsistant — chacun gère sa validation
- **DÉCISION** : **GARDER + uniformiser** via `useEdit` + `FormRow` primitive (FR-13)

### 2.12 Tables (`ClientList`, `RecoList`, `RecoAggregatorList`, `ActiveExperimentsList`, `BusinessBreakdownTable`, `PageTypeBreakdownTable`, `ScentFleetTable`)

- **Pattern** : Ad-hoc — chaque table a son implémentation, son tri, ses cellules
- **Cohérence** : 🟠 — pas de DataTable générique (FR-20). Mais c'est OK pour le V1.
- **DÉCISION** : **GARDER + extraire DataTable générique** (FR-20) — refactor progressif sans tout casser.

### 2.13 Cards / KpiCard / Pill

- **Localisation** : `webapp/packages/ui/src/components/Card.tsx`, `KpiCard.tsx`, `Pill.tsx`
- **Card** : 22 LOC, propre, expose `title` + `actions` slot + children, className `gc-panel`
- **KpiCard** : présentation label + value + hint
- **Pill** : tone variants (`red`, `amber`, `green`, `cyan`, `gold`, `soft`)
- **Cohérence** : 🟢 — primitives canoniques bien utilisées partout
- **DÉCISION** : **GARDER tel quel** + polish design system phase H (no card-in-card, density)

### 2.14 Charts (`PillarRadialChart`, `PillarBarsFleet`, `PriorityDistribution`, `FunnelStepsViz`, `FunnelDropOffChart`, `RealitySparkline`, `GeoSparkline`, `TrackSparkline`)

- **Pattern** : SVG inline, calculs server-side, props typés
- **Cohérence** : 🟢 ad-hoc mais soigné
- **DÉCISION** : **GARDER tel quel** + design system pass (palette unifiée)

### 2.15 Status Pills (`AuditStatusPill`, `LifecyclePill`, `EvidencePill`)

- **Rôle** : Status mapping vers Pill tones (amber pending, cyan running, green completed, red failed)
- **Cohérence** : 🟢
- **DÉCISION** : **GARDER tel quel**. Ajouter `WorkerHealthPill` global (FR-3/FR-4) post `system_health` table.

### 2.16 Empty / Loading / Error states

- **EmptyState** (`common/EmptyState.tsx`, 77 LOC) : icon + title + description + actionLabel/actionHref. Pattern V1 stable.
- **LoadingSkeleton** (`common/LoadingSkeleton.tsx`, 136 LOC) : PageSkeleton + DetailSkeleton + SkeletonBlock
- **ErrorFallback** (`common/ErrorFallback.tsx`) : utilisé par error.tsx routes
- **Cohérence** : 🟢 primitives propres et utilisées en `loading.tsx` / `error.tsx` granulaires (`audits/error.tsx`, `audits/[clientSlug]/loading.tsx`, etc.)
- **DÉCISION** : **GARDER + étendre** avec `BlockedState`, `WorkerOfflineState`, `ModuleMaturity` components (FR-5/FR-6)

### 2.17 Drag/drop / interactive surfaces

- **Constat** : pas de drag/drop dans la webapp actuelle (sauf possiblement Cmd+K reordering — pas trouvé). UI principalement form/list/detail.
- **DÉCISION** : N/A

---

## 3. Design system applicatif

### 3.1 Primitives `@growthcro/ui` (`webapp/packages/ui/src/components/`)

Inventaire exports (`packages/ui/src/index.ts:7-23`) :

| Primitive | Fichier | Rôle | Utilisation count approx |
|---|---|---|---|
| `Button` | `Button.tsx` | Variants primary/default/ghost | partout (≥40 usages) |
| `Card` | `Card.tsx` | `.gc-panel` wrapper avec title + actions slot | ubiquitous (≥80 usages) |
| `KpiCard` | `KpiCard.tsx` | Label + value + hint | partout en haut de pages stats |
| `ScoreBar` | `ScoreBar.tsx` | Progress bar 0-100 colorée | recos + audits pillars |
| `RecoCard` | `RecoCard.tsx` | Reco preview card | recos pages |
| `Pill` | `Pill.tsx` | Tone variants (red/amber/green/cyan/gold/soft) | ubiquitous (≥150 usages) |
| `ClientRow` | `ClientRow.tsx` | Row pattern pour client list | clients |
| `NavItem` | `NavItem.tsx` | Sidebar nav entry | Sidebar |
| `ConsentBanner` | `ConsentBanner.tsx` | RGPD banner global | layout.tsx |
| `Modal` | `Modal.tsx` | Backdrop + dialog + close | tous les modals |
| `Tabs` | `Tabs.tsx` | Tabs primitive | DashboardTabs, ClientDetailTabs, SettingsTabs |
| `FormRow` | `FormRow.tsx` | Label + input + error pattern | forms |
| `StarfieldBackground` | `StarfieldBackground.tsx` | V22 4-layer parallax canvas | layout.tsx (global) |
| `scoreColor`, `scoreColorMuted` | `score-color.ts` | Score → CSS color | tables/charts |
| `tokens` | `tokens.ts` | Token export object | TBD |

- **Cohérence** : 🟢 — primitives propres, naming consistant, 1 file = 1 component (mono-concern)
- **DÉCISION** : **GARDER tel quel**, étendre minimalement (FR-5/FR-6/FR-7 ajoutent `ModuleHeader`, `BlockedState`, `WorkerOfflineState`, `ActionButton`)

### 3.2 Tokens CSS (`webapp/apps/shell/app/globals.css`)

- **Fichier** : **2017 LOC** (massif)
- **Tokens** : variables `--gc-*` (couleurs, typographie, spacing). Pas grepables au pattern simple — embedded inline dans selectors.
- **Fontes** : `Inter` (body), `Cormorant Garamond` (display italic), `Playfair Display` (display alt), `JetBrains Mono` (metrics). Variables `--gc-font-sans/display/display-alt/mono`. Chargées via `next/font/google` dans `layout.tsx`.
- **Background** : `StarfieldBackground` canvas + `gc-grain` overlay (cf. `layout.tsx:65, 71`) — fond étoilé V22 Stratospheric Observatory
- **Cohérence** : 🟠 — design tokens existent (cf. `tokens.ts`) mais utilisés inline en `style={{}}` JSX dans beaucoup de composants (cf. inline styles dans `clients/[slug]/dna/page.tsx:131-163`, `clients/[slug]/page.tsx:60, 81`, etc.). Pas de système BEM strict, pas de CSS-in-JS unifié, pas de Tailwind.
- **État honnête** : 🟢 fonctionnel mais ad-hoc — c'est consistant à 80% mais 20% inline styles dégradent la maintenabilité
- **DÉCISION** : **GARDER + polish phase H** — FR-21 retire fond étoilé/glass excessif, typo lisible, density de travail. Pas de migration Tailwind/Radix/shadcn dans cet epic (cf. PRD Out of Scope).

### 3.3 Layout & responsive

- **Pattern principal** : `<div className="gc-app">` (sidebar + main 2-col grid) sur 5 routes, `<main className="gc-XXX-shell">` sur les autres, `<main style={{ padding: 22 }}>` (anti-pattern brut) sur 7 routes (reality, reality/[slug], scent, learning, learning/[proposalId], funnel/[slug], audits/[c]/[id]/judges).
- **Breakpoint** : mentionné `.gc-client-detail__grid` qui collapse à 980px (cf. `clients/[slug]/dna/page.tsx:9-10`)
- **Mobile** : pas testé Playwright dual-viewport encore (FR-22)
- **État honnête** : 🟠 — l'inconsistance des wrappers est un signal "le layout n'a pas été pensé comme un système"
- **DÉCISION** : **REFONDRE en nested layout** (FR-2 + Phase B1 PRD) — `<RootShell>` standardise Sidebar + StickyHeader + main wrapper pour toutes les routes authenticated.

---

## 4. LISTE ROUGE — à archiver / supprimer / cacher de la nav

| Surface | Raison | Action | FR PRD |
|---|---|---|---|
| `app/audit-gads/page.tsx` | Bouton "New audit (CSV)" disabled "post-MVP" (ligne 46). Instructions CLI uniquement. Aucune action UI. | **CACHER de nav** : retirer de `lib/cmdk-items.ts:63`. Route reste accessible URL directe. | FR-25 |
| `app/audit-meta/page.tsx` | Idem `/audit-gads`. Bouton disabled, instructions CLI. | **CACHER de nav** : retirer de `lib/cmdk-items.ts:64`. | FR-25 |
| `app/funnel/[clientSlug]/page.tsx` | Route fonctionnelle mais non listée dans cmdk-items, source data fragile (`brand_dna_json.funnel` hors schema). Audit Phase A la croyait "ghost". | **SUPPRIMER** + drop link dans `clients/[slug]/page.tsx:80`. (Ou alternative : tab dans `/clients/[slug]?tab=funnel` post-décision Mathis.) | FR-24 |
| `components/command-center/CommandCenterTopbar.tsx` | Legacy V26 topbar coexistant avec StickyHeader sur home seule (`page.tsx:224`). Commentaire `page.tsx:218-220` admet "legacy still in place". | **SUPPRIMER** | FR-24 |
| `components/ViewToolbar.tsx` | Utilisé sur 1 seule route (`/doctrine`). Pattern redondant avec inline `gc-topbar`. | **SUPPRIMER** + refactor `/doctrine` pour pattern inline | FR-24 |
| `components/Breadcrumbs.tsx` | Deprecated shim re-export DynamicBreadcrumbs (10 LOC). Utilisé seulement par ViewToolbar. | **SUPPRIMER** post cleanup ViewToolbar | FR-24 |
| Bouton "Run AURA pipeline (V2)" `clients/[slug]/dna/page.tsx:312-321` | Disabled, no-op | Remplacer par `<ModuleMaturity>` (FR-5) ou retirer | FR-5/FR-24 |
| Lien "Open V26 archive" `CommandCenterTopbar.tsx:17` | Pointe vers `/deliverables/GrowthCRO-V26-WebApp.html` HTML statique pré-launch | **SUPPRIMER** avec le composant CommandCenterTopbar | FR-24 |
| Input "Subscribe to a run UUID manually (smoke test)" `HandoffBriefSection.tsx:75-100` | Seam de dev exposé en prod | **SUPPRIMER** lors de refonte GSG Studio (FR-11 : wizard submit → redirect direct vers `/gsg/runs/[id]`) | FR-11/FR-24 |
| Table `experiments` (`supabase/migrations/20260514_0021`) | CREATE TABLE + RLS définies. Lue par `listExperiments()` `lib/experiments-data.ts:51` (page `/experiments`). Aucune mutation : worker dispatcher `experiment` = `print("not implemented")`. | **NE PAS DROP en A1** — décision DROP/keep tranchée dans **G4 decision spike** (implement vs archive). Si G4 → archive : DROP TABLE + migration cleanup + retirer `lib/experiments-data.ts` + retirer page `/experiments`. | FR-19 |

**Total LISTE ROUGE = 10 items** *(corrigé 2026-05-17 après vérification grep : `screenshots` retiré de la liste — c'est un bucket Supabase Storage actif `storage.buckets` créé par migration `20260513_0005`, utilisé par `lib/captures-fs.ts:32` `STORAGE_BUCKET = "screenshots"` pour servir 14GB de PNG via `/api/screenshots/*` 302-redirect — pas une table relationnelle morte comme l'audit Phase A le supposait. `experiments` conservé en rouge avec action mise à jour : table lue par UI, DROP risqué sans G4 tranché — décision DROP/keep différée à G4 decision spike).*

---

## 5. LISTE ORANGE — à repenser

| Surface | Problème | Refonte cible | FR PRD |
|---|---|---|---|
| `app/gsg/page.tsx` (Design Grammar viewer) | Pas le Studio, aucun CTA croisé fort. Le label "GSG Studio" dans cmdk-items pointe ici → confusion. | **RENOMMER en `/gsg/design-grammar/[client]`**. `/gsg` → REDIRECT vers `/gsg/studio` (FR-10) | FR-10 |
| `app/gsg/handoff/page.tsx` | Wizard fragile : `output_path` race, UUID paste manual seam, wizard sans URL stable | **REFONDRE en `/gsg/studio` + `/gsg/runs/[id]`** (FR-10/FR-11/FR-12) | FR-10/FR-11/FR-12 |
| `app/reality/page.tsx` + `/reality/[clientSlug]` | Skeleton "0/N configured" sans Module Maturity Model. Backend OK mais creds OAuth absentes. | **UX honest activation** : `<ModuleMaturity status="ready_to_configure">` (FR-5/FR-16). **Pas de wire OAuth** (deferred Mathis). | FR-5/FR-16 |
| `app/geo/page.tsx` + `/geo/[clientSlug]` | Empty state explique keys missing, mais pas de Module Maturity Model formal | **UX honest** : `<ModuleMaturity status="ready_to_configure" reason="keys missing">` | FR-5/FR-17 |
| `app/scent/page.tsx` | 95% "Aucun scent trail" — pipeline cross-channel jamais run | **UX honest empty state** : `<ModuleMaturity status="no_data">` OR cacher tant que pas batch runs configurable | FR-5 |
| `app/learning/page.tsx` + `/learning/[proposalId]` | Bayesian approach questionnée par Mathis (PRD §6 Q2) | **NE PAS REFONDRE UI** avant decision spike G3 `LEARNING_LAYER_APPROACH_DECISION.md` | FR-18 |
| `app/experiments/page.tsx` | Dispatcher worker noop | **NE PAS REFONDRE UI** avant decision spike G4 "implement vs archive" | FR-19 |
| `app/clients/[slug]/dna/page.tsx` | Page séparée pour un tab logique du workspace client | **FUSIONNER en tab `/clients/[slug]?tab=brand-dna`** | D1 |
| `app/recos/[clientSlug]/page.tsx` | Minimal (44 LOC) + waterfall 2 awaits séquentiels | **FUSIONNER en tab `/clients/[slug]?tab=recos`** ou redirect `/audits/[clientSlug]` | D1/D2 |
| `app/audits/page.tsx` (landing 34 LOC) | Juste un ClientPicker dans une Card | **FUSIONNER** : accès via `/clients/[slug]?tab=audits` ou évolution vers vue "Audits & Recos" cross-client | A2 espace 3 |
| Sidebar inconsistent rendering | Présent sur 5 routes / absent sur 20 | **Uniformiser via nested layout** (B1 PRD) sur toutes routes authenticated | FR-2 |
| StickyHeader sur 1 seule route | Devrait être chrome global | **Uniformiser via nested layout** | FR-2 |
| 2 endpoints PATCH pour reco update (`/api/recos/[id]` + `/api/recos/[id]/lifecycle`) | Deux patterns côté UI = friction | **FUSIONNER endpoint** OU **clarifier deux usages** (lifecycle pill séparé du form, FR-14) | FR-13/FR-14 |
| Inline styles `style={{}}` JSX | 20% des composants ad-hoc | **Polish phase H** — extraire en classes CSS / design tokens. Pas de Tailwind migration dans cet epic. | FR-21 |
| 7 routes `<main style={{ padding: 22 }}>` (anti-pattern wrapper) | Inconsistance shell | **Refactor en nested layout** (B1 PRD) | FR-2 |

**Total LISTE ORANGE = 15 items**.

---

## 6. LISTE VERTE — à garder tel quel

| Surface | Pourquoi solide |
|---|---|
| `/` (Command Center) home pattern (RSC + 9 queries parallel) | Pattern d'orchestration RSC propre. Refonte UX seulement (FR-8), pas structure. |
| `/clients` pattern (FiltersBar + SortDropdown + Pagination URL-state) | Pattern réutilisable. Préserver. |
| `/clients/[slug]` pattern (workspace 6-pilier radial + ClientDetailTabs) | Pattern solide. Étendre en workspace canonical (D1). |
| `/audits/[clientSlug]` (groupage par page_type + ConvergedNotice) | Pattern intelligent. Préserver. |
| `/audits/[clientSlug]/[auditId]` (drill-down + AuditDetailFull) | Excellent pattern E2E. |
| `/audits/[clientSlug]/[auditId]/judges` (multi-judge V26.D) | Fonctionnel + empty state honnête. |
| `/recos` (cross-client aggregator) | Pattern propre. |
| `/doctrine` (pédagogique stateless) | Solid reference page. |
| `/settings` (4 tabs + role-gated) | E2E fonctionnel. |
| `/login`, `/auth/*`, `/privacy`, `/terms` | Public, lecture seule, OK. |
| TriggerRunButton + RunStatusPill pattern | Primitive d'action canonical. |
| Primitives `Card` / `KpiCard` / `Pill` / `Button` / `Modal` / `Tabs` / `NavItem` | Design system foundation. |
| Sidebar + CmdKPalette source-of-truth `lib/cmdk-items.ts` | Single source design. |
| DynamicBreadcrumbs | Smart segment mapping. |
| Common states : `EmptyState` / `LoadingSkeleton` / `ErrorFallback` | Primitives propres. |
| 19 API routes admin-gated | Pattern d'auth solide. |
| Server Components orchestration + RSC parallel fetches | Standard Next.js 14 propre. |

**Pas de refonte structurelle pour ces surfaces — uniquement polish UX/design system Phase H + uniformisation chrome (Sidebar + StickyHeader nested layout).**

---

## 7. Mapping ancien → nouvel espace IA (préparation A2)

5 espaces cible (cf. PRD `webapp-product-ux-reconstruction-2026-05` §FR-1 + A2.md `Implementation notes`) :

1. **Command Center** — vue exécutive (home `/`)
2. **Clients** — workspace central par client
3. **Audits & Recos** — workflow audit→reco→opportunity
4. **GSG Studio** — vrai studio E2E (wizard + runs + design-grammar)
5. **Advanced Intelligence** — Reality + GEO + Learning + Experiments + Scent groupés sous un menu avec Module Maturity Model

+ 2 utilitaires : **Doctrine** · **Settings**
+ public hors espaces : `/login`, `/auth/*`, `/privacy`, `/terms`

| Route actuelle | Nouvel espace cible | Nouvelle URL probable | Notes |
|---|---|---|---|
| `/` | Command Center | `/` | Refonte 4 zones (C1) |
| `/clients` | Clients | `/clients` | Refonte progressive disclosure (D1) |
| `/clients/[slug]` | Clients | `/clients/[slug]` | Workspace central avec tabs (Audits, Recos, GSG, Reality, Brand DNA, History, Scent éventuel) |
| `/clients/[slug]/dna` | Clients | `/clients/[slug]?tab=brand-dna` | **FUSIONNER** en tab |
| `/audits` | Audits & Recos | `/audits` ou drop landing | Soit landing picker (forme actuelle), soit drop et passer par `/clients/[slug]?tab=audits` |
| `/audits/[clientSlug]` | Audits & Recos | `/audits/[clientSlug]` | Drill-down per client — GARDER |
| `/audits/[clientSlug]/[auditId]` | Audits & Recos | `/audits/[clientSlug]/[auditId]` | Drill-down detail — GARDER |
| `/audits/[clientSlug]/[auditId]/judges` | Audits & Recos | `/audits/[clientSlug]/[auditId]/judges` | Sub-page judges — GARDER |
| `/recos` | Clients (via tab) | `/clients/[slug]?tab=recos` | **FUSIONNER** en tab client (décision Mathis 2026-05-17). Drop la vue cross-client agrégée. Redirect 301 `/recos` → `/clients` (landing) ou message "Sélectionnez un client". |
| `/recos/[clientSlug]` | Clients (via tab) | `/clients/[slug]?tab=recos` | **FUSIONNER** en tab client (idem) |
| `/gsg` | GSG Studio | `/gsg/design-grammar/[client]` + redirect `/gsg` → `/gsg/studio` | **RENOMMER** (F5 PRD) |
| `/gsg/handoff` | GSG Studio | `/gsg/studio` | **REFONDRE** (F2/F3/F4 PRD) en wizard submit → `/gsg/runs/[id]` |
| (nouveau) | GSG Studio | `/gsg/runs` | History — à créer F2 |
| (nouveau) | GSG Studio | `/gsg/runs/[id]` | Preview iframe + QA + export — à créer F2/F3 |
| `/reality` | Advanced Intelligence | `/reality` | UX only (G1) — Module Maturity |
| `/reality/[clientSlug]` | Advanced Intelligence | `/reality/[clientSlug]` ou `/clients/[slug]?tab=reality` | UX only |
| `/geo` | Advanced Intelligence | `/geo` | UX only (G2) |
| `/geo/[clientSlug]` | Advanced Intelligence | `/geo/[clientSlug]` ou `/clients/[slug]?tab=geo` | UX only |
| `/learning` | Advanced Intelligence | `/learning` | Post research spike G3 (FR-18) |
| `/learning/[proposalId]` | Advanced Intelligence | `/learning/[proposalId]` | Post research spike |
| `/experiments` | Advanced Intelligence | `/experiments` | Post decision spike G4 (FR-19) |
| `/scent` | Advanced Intelligence | `/scent` | UX honest empty state ou cacher (G5) |
| `/doctrine` | Utility · Doctrine | `/doctrine` | GARDER tel quel + drop ViewToolbar |
| `/settings` | Utility · Settings | `/settings` | GARDER tel quel |
| `/login` | Public | `/login` | GARDER |
| `/auth/callback`, `/auth/signout` | Public | inchangé | GARDER |
| `/privacy` | Public | `/privacy` | GARDER |
| `/terms` | Public | `/terms` | GARDER |
| `/audit-gads` | (caché de nav) | `/audit-gads` | **CACHER** jusqu'à form UI + skill wiring (FR-25) |
| `/audit-meta` | (caché de nav) | `/audit-meta` | **CACHER** (FR-25) |
| `/funnel/[clientSlug]` | (supprimé) | n/a | **SUPPRIMER** + drop link dans `/clients/[slug]:80` (FR-24) |

**Redirects 301 nécessaires** (pour ne pas casser les bookmarks) :
- `/gsg` → `/gsg/studio`
- `/gsg/handoff` → `/gsg/studio` (TBD selon décision PRD F2)
- `/clients/[slug]/dna` → `/clients/[slug]?tab=brand-dna`
- `/recos` → `/clients` (landing — pas de cross-client view décision Mathis 2026-05-17)
- `/recos/[clientSlug]` → `/clients/[slug]?tab=recos`
- `/funnel/[clientSlug]` → ❌ pas de redirect, retirer link source (décision Mathis : SUPPRIMER)

---

## 8. Risques refonte par route

| Route | Risque refonte | Mitigation |
|---|---|---|
| `/` (home Command Center) | Très utilisée, refonte 4 zones risque régression UX si on perd des panels critiques | Feature flag `FEATURE_NEW_HOME`, Playwright smoke (FR-23), screenshot dual-viewport, comparaison TTFB baseline (Phase I1) |
| `/gsg/handoff` → `/gsg/studio` | URLs changent, bookmarks Mathis cassent, wiring runs en sortie wizard fragile | Redirect 301, smoke tests wizard → preview, garder l'URL existante en alias temporaire |
| Sidebar uniformisation (B1) | Toutes les routes touchées en même temps = risque casse globale | Nested layout introduit progressivement, smoke E2E par route, feature flag par batch |
| `/clients/[slug]` workspace tabs | URLs `/clients/[slug]/dna` deviennent `?tab=brand-dna` | Redirect 301, tabs URL state defensif |
| `/audits/page.tsx` landing drop | Si on retire la landing, link cmdk "Audits" doit pointer ailleurs | Decision A2 explicit (TBD avec Mathis) |
| `/learning` + `/experiments` | NE PAS toucher avant decision spikes G3/G4 | Block UI rebuild jusqu'à doc decision écrit + tranché |
| `/reality` Module Maturity | Risque de surprendre Mathis si maturity affichée "ready_to_configure" alors qu'il pensait "experimental" | Wire `<ModuleMaturity>` sketches first, Mathis valide les status avant code |
| `CommandCenterTopbar` drop | Risque casse home seul (link "Copy GSG brief" → `/gsg`) | Replacer par CTA "Open GSG Studio" dans StickyHeader actions ou QuickActionCard |
| `ViewToolbar` drop | Risque casse `/doctrine` (seul caller) | Refactor `/doctrine` en pattern `gc-topbar` inline en même commit que drop |
| Tables `screenshots` + `experiments` | Drop migrations = perte schema | Archive migration (renommer en `_archived_*`), pas DROP TABLE en prod sans Mathis green light |

---

## 9. Métriques baseline à mesurer Phase I1

À mesurer **avant** toute refonte structurelle (FR-PRD §Success Criteria #1-2) :

| Route | Métrique | Outil | Target post-refonte |
|---|---|---|---|
| `/` | TTFB p50, p95 | Vercel Analytics + Lighthouse | <500ms p50 |
| `/` | Lighthouse perf score | Lighthouse | >85 |
| `/` | Bundle size (JS first load) | Next.js build report | <300KB gzip |
| `/` | RSC payload size | Next.js build | <100KB |
| `/clients` | TTFB | Vercel | <300ms |
| `/audits/[c]/[id]` | TTFB | Vercel | <500ms |
| `/gsg/handoff` (future `/gsg/studio`) | Wizard submit → preview latency | Playwright E2E | <30s worker pickup + render |
| `/reality` | Queries count + waterfall | Server logs | reduce to ≤5 round-trips |
| All routes | Sidebar render coverage | Static grep | 100% authenticated routes |
| Worker daemon | Heartbeat freshness | `/api/worker/health` (FR-3) | <60s online, <300s lagging |

---

## 10. Sign-off

**Validé par Mathis 2026-05-17** (décisions formalisées en §11 ci-dessous).

- [x] Mathis valide la **LISTE ROUGE §4** (9 items à supprimer/cacher après correction screenshots)
- [x] Mathis valide la **LISTE ORANGE §5** (15 items à repenser, en particulier la non-refonte UI de `/learning` + `/experiments` avant decision spikes G3/G4)
- [x] Mathis valide la **LISTE VERTE §6** (à garder tel quel + polish phase H)
- [x] Mathis valide le **mapping ancien → nouvel espace §7** (notamment fusion `/clients/[slug]/dna` → `?tab=brand-dna`, drop `/funnel/[clientSlug]`, cacher `/audit-gads` + `/audit-meta`)
- [x] Mathis valide les **redirects 301 §7** (compatibilité backward bookmarks)
- [x] **`/funnel/[clientSlug]`** → **SUPPRIMER** (Mathis 2026-05-17). Pas de capture funnel pipeline planifiée, source data fragile, invisible nav.
- [x] **`/audits` landing** → **GARDER** picker comme entrée Audits & Recos (Mathis 2026-05-17).
- [x] **`/recos` cross-client** → **FUSIONNER** en tab `/clients/[slug]?tab=recos` uniquement (Mathis 2026-05-17). Drop la vue cross-fleet. Focus client workspace.
- [x] **Tables fantômes** → **NE PAS toucher en A1** (Mathis 2026-05-17). Correction post-vérification grep : `screenshots` est un **bucket Supabase Storage actif**, pas une table morte (l'audit Phase A se trompait). `experiments` table est **lue par UI** (`lib/experiments-data.ts:51` → page `/experiments`) ; DROP risqué sans G4 tranché. Décision DROP/keep reportée à **G4 decision spike** (implement vs archive).

A2 (`#67`) peut démarrer sur cette base signed-off.

---

## 11. Décisions Mathis 2026-05-17 (formalisé)

Session A1 : 4 trade-offs proposés via `AskUserQuestion`, 4 décisions tranchées + 1 correction d'erreur d'audit après vérification.

### 11.1 `/funnel/[clientSlug]` → **SUPPRIMER**
- Décision : retirer la route + link source dans `clients/[slug]/page.tsx:80`
- Rationale : pas de capture funnel pipeline planifiée, source data `brand_dna_json.funnel` hors schema, route invisible nav (absente de `cmdk-items.ts`)
- Impact downstream : ne fait pas partie de l'espace Clients tabs. Fichier à supprimer en phase D ou nettoyage J0/J1.

### 11.2 `/audits` landing → **GARDER** (picker)
- Décision : landing minimal (34 LOC, ClientPicker) reste comme entrée Audits & Recos top-level
- Rationale : workflow utilisateur clair (click "Audits" dans sidebar → picker → drill-down `/audits/[clientSlug]`). Pas de surcharge à drop.
- Impact downstream : pas de redirect, espace Audits & Recos garde sa landing.

### 11.3 `/recos` cross-client → **FUSIONNER en tab `?tab=recos`**
- Décision : drop la vue cross-fleet agrégée. Toutes les recos vues dans contexte client uniquement via tab workspace.
- Rationale : focus client > vue agrégée. Simplifie nav. Moins de surface UI.
- Impact downstream : redirect 301 `/recos` → `/clients` (ou message "Sélectionnez un client") ; redirect 301 `/recos/[clientSlug]` → `/clients/[slug]?tab=recos`. Composant `RecoAggregatorList` cross-client peut être archivé ou réutilisé dans tab.

### 11.4 Tables Supabase fantômes — **CORRECTION D'AUDIT** + DÉCISION DIFFÉRÉE
- Erreur d'audit Phase A initial : avait classé `screenshots` et `experiments` comme "tables fantômes". Vérification grep 2026-05-17 révèle :
  - **`screenshots`** : c'est un **bucket Supabase Storage** (`storage.buckets`), PAS une table relationnelle. Migration `20260513_0005_screenshots_storage.sql` crée le bucket + RLS sur `storage.objects`. Utilisé activement par `webapp/apps/shell/lib/captures-fs.ts:32` `STORAGE_BUCKET = "screenshots"` pour servir 14GB de PNG via `/api/screenshots/*` 302-redirect vers public URL (parce que FS local pas bundlé sur Vercel). **CRITICAL : NE PAS toucher.**
  - **`experiments`** : table relationnelle créée par `20260514_0021_experiments.sql`. **Lue par UI** via `lib/experiments-data.ts:51` `.from("experiments").select(...)` consommée par page `/experiments`. **Jamais writée** (worker dispatcher `experiment` = `print("not implemented")`). DROP TABLE casserait pas la page (try/catch → empty list) mais perdrait le schema.
- Décision Mathis 2026-05-17 : **NE PAS DROP en A1**. La décision DROP/keep est reportée au **G4 decision spike** ("Experiments implement vs archive"). Si G4 → archive : DROP TABLE + migration cleanup + retirer `lib/experiments-data.ts` + retirer page `/experiments`. Si G4 → implement : wire dispatcher worker + UI mutations.

### Process learning
Avant de proposer une option DROP/destructive dans une `AskUserQuestion`, vérifier exhaustivement les refs code (`grep` table name dans TS/Python/SQL) — l'audit Phase A se trompait sur 2 items sur 2. Reco process : intégrer un grep verification step dans l'audit avant de proposer des actions destructive.

---

## Annexe — File counts confirmés

- **32 fichiers `route.ts`/`page.tsx`/`loading.tsx`/`error.tsx`/`layout.tsx`/`middleware.ts`** sous `webapp/apps/shell/app/` (cf. `find` 2026-05-17)
- **25 routes utilisateur** (dont 2 décoratives + 1 ghost-funnel + 2 public + 2 auth route handlers)
- **117 composants** `.tsx` sous `webapp/apps/shell/components/`
- **27 modules** sous `webapp/apps/shell/lib/`
- **16 primitives** `@growthcro/ui` (`packages/ui/src/`)
- **19 API routes** sous `webapp/apps/shell/app/api/`
- **2017 LOC** `webapp/apps/shell/app/globals.css`
- **Sidebar rendue dans 5 routes** : `/`, `/settings`, `/audit-gads`, `/audit-meta`, `/doctrine` (+ shells `app/loading.tsx` et `app/error.tsx`)
- **StickyHeader rendu dans 1 route** : `/` (home, conditionnel `if (user)`)
- **CommandCenterTopbar rendu dans 1 route** : `/` (legacy coexistant)
- **ViewToolbar rendu dans 1 route** : `/doctrine`
- **7 routes avec `<main style={{ padding: 22 }}>` anti-pattern shell** : `/reality`, `/reality/[clientSlug]`, `/scent`, `/learning`, `/learning/[proposalId]`, `/funnel/[clientSlug]`, `/audits/[clientSlug]/[auditId]/judges`

---

**Document créé 2026-05-17 par Claude Code (Opus 4.7 1M-ctx) pour l'issue #66 (A1). Source de vérité primaire pour A2 (IA cible 5 espaces). Pure documentation, aucune modification de code applicatif. À signer-off par Mathis avant que A2 démarre.**
