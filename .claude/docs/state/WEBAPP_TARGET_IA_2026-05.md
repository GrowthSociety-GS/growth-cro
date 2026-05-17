# Webapp Target Information Architecture — 2026-05

> Document canonique d'IA cible 5 espaces. Source pour B1 (refonte app shell sidebar/topbar/breadcrumbs/cmd-k) + C1 (home Command Center) + D1 (workspace client tabs) + F5 (GSG Studio routes) + G* (Advanced Intelligence groupé). Anchore le PRD [`webapp-product-ux-reconstruction-2026-05`](../../prds/webapp-product-ux-reconstruction-2026-05.md).
>
> Issue #67 (A2), epic [`webapp-product-ux-reconstruction-2026-05`](../../epics/webapp-product-ux-reconstruction-2026-05/A2.md). Consomme [`WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md`](WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md) (A1) signed-off 2026-05-17 par Mathis (§10 + §11 décisions formalisées).

**Auteur** : Claude Code (Opus 4.7 1M-ctx).
**Date** : 2026-05-17.
**Périmètre** : information architecture cible de `webapp/apps/shell/` après refonte UX. Pas de code applicatif touché — pure documentation.
**Statut** : DRAFT — pending Mathis sign-off §7.

---

## 0. Vision IA — workflow-first, pas architecture-internal

### 0.1 Le problème actuel (rappel A1 §2.1 + audit Phase A §1)

La sidebar actuelle (`webapp/apps/shell/lib/cmdk-items.ts:40-67`) reflète l'**architecture interne** du repo, pas les workflows utilisateur :

```
NAV_GROUPS actuels :
  - Pipeline   : Overview · Clients · Audits · Recos
  - Studio     : GSG Studio · Doctrine · Reality · Learning · Scent · Experiments · GEO
  - Agency     : Audit Google Ads · Audit Meta Ads
  - Admin      : Settings
```

Conséquences observées :
- **11 entries plates** sans hiérarchie de workflow → l'user ne sait pas où cliquer en <30s
- **Groupes ad-hoc** : "Pipeline" mélange home + fleet + audits + recos (4 concepts différents). "Studio" mélange GSG (génération LP) + Doctrine (référence) + Reality (data layer) + Learning (méta-apprentissage) — c'est un groupe fourre-tout.
- **`/recos` cross-client** + **`/recos/[slug]`** + **`/audits/[c]/[id]` (avec recos par audit)** = 3 façons de voir des recos, friction sans valeur.
- **Sidebar rendue sur 5 routes / absente sur 20** (A1 §2.1) → inconsistance shell = chrome perçu comme "cassé"
- **GSG Studio label pointe vers `/gsg`** qui n'est PAS le studio (c'est le Design Grammar viewer) → confusion produit majeure (A1 §1.11)
- **Module Maturity invisible** : Reality affiche "0/5 configured" sans dire si c'est ready_to_configure / blocked / no_data → user croit que c'est cassé (A1 §1.16-1.20)

### 0.2 Le principe cible — IA workflow-first

L'IA cible reflète les **workflows utilisateur**, pas l'architecture du repo. Chaque espace répond à une question utilisateur :

| Espace | Question utilisateur | Persona principale |
|---|---|---|
| **Command Center** | "Qu'est-ce que je dois faire maintenant ?" | Mathis 9h du matin, café à la main |
| **Clients** | "Où en est le client X ?" | Mathis avant un call client |
| **Audits & Recos** | "Quelles actions sont à shipper sur X audit ?" | Mathis en revue de recos |
| **GSG Studio** | "Je veux générer une LP" | Mathis en mode création |
| **Advanced Intelligence** | "Quel est l'état des modules avancés ?" (Reality/GEO/Learning/Experiments/Scent) | Mathis en mode exploration / debug |

Les **utilitaires** (Doctrine, Settings) sont hors workflow — ils sont accessibles mais ne sont pas un espace produit principal.

### 0.3 Principes structurels (cf. PRD §FR-1, FR-2)

1. **5 espaces produit + 2 utilitaires** — pas plus (stop condition A2 : >7 espaces = mur d'IA).
2. **Sidebar uniforme sur toutes routes authenticated** sauf public (`/login`, `/privacy`, `/terms`, `/auth/*`) (FR-2).
3. **Workflow-first labels** : "Command Center", "Audits & Recos", "GSG Studio" — pas "Pipeline", "Studio", "Agency" (jargon interne).
4. **Module Maturity Model honnête** sur chaque module top-level (A3 livrable, mais labels nav reflètent l'état réel : Reality/GEO/Learning/Experiments/Scent sous parent unique avec sous-nav).
5. **Hide ≠ Delete** : `/audit-gads` et `/audit-meta` sont CACHÉS de la nav (FR-25), URL accessible. `/funnel/[slug]` est SUPPRIMÉ (FR-24, décision Mathis A1 §11.1).
6. **Cmd+K = actions globales actionnables** : chaque item produit un effet réel (navigate, modal, action). Pas de fake placeholder.
7. **Breadcrumbs dynamiques** suivent la hiérarchie d'espace (pas la hiérarchie URL brute).

---

## 1. Les 5 espaces principaux

### 1.1 Espace 1 — Command Center (`/`)

**Description** : vue exécutive du portefeuille clients. Réponse à la question **"Qu'est-ce que je dois faire maintenant ?"** en <10 secondes.

**Persona principale** : Mathis (CRO Lead Growth Society) à 9h du matin, café à la main, qui ouvre la webapp pour piloter sa journée sur ~100 clients en portefeuille.

**Routes incluses** :
- `/` (home unique)

**4 zones canoniques** (cf. PRD FR-8, hard limit 4 zones — pas un mur de panels) :

1. **Today / Urgent actions** — 3-5 actions ranked
   - Clients à risque (score audit chuté, run failed, OAuth expiré)
   - Runs failed nécessitant intervention
   - Recos validés à shipper (lifecycle=`validated` mais pas encore `shipped`)
   - Proposals learning en attente review >7j
   - Source data : `loadCommandCenterMetrics` + nouvelles queries `loadUrgentActions` (à créer Phase C1)

2. **Fleet Health** — KPIs agrégés sobres
   - X clients audités / Y clients total
   - Z recos en attente review
   - Moyenne score pillars fleet
   - Coverage closed-loop modules
   - Source data : `loadFleetPillarAverages` + `loadClosedLoopCoverage` (already E2E)

3. **Recent Runs** — derniers 5-10 runs avec statut realtime
   - Type · client · status (`pending`/`running`/`completed`/`failed`) · duration · trigger time
   - Subscribe Realtime channel `public:runs` (already wired via `RecentRunsTracker`)
   - Click → navigate vers detail page (audit detail / GSG run detail / reality client)

4. **Next Best Actions** — suggestions IA produit "next thing to do"
   - Basées sur état du backlog (clients sans audit récent, recos P0 non-shippées, GSG Design Grammar manquant)
   - Format : card avec titre + 1-line reason + CTA action
   - Source data : new lib `next-best-actions.ts` (Phase C1)
   - Honest empty state si rien d'urgent ("Tout est à jour — explore les Advanced Intelligence pour aller plus loin")

**Drill-down** :
- Click sur item Today/Urgent → route appropriée (`/clients/[slug]`, `/audits/[c]/[id]`, `/gsg/runs/[id]`)
- Click sur Fleet Health metric → drill `/clients?sort=score_asc` etc.
- Click sur Recent Run → drill detail
- Click sur Next Best Action → trigger action ou navigate

**Composants prévus** (cf. existant + Phase C1) :
- `CommandCenterTopbar` LEGACY → DROP (FR-24)
- New `TodayPanel`, `FleetHealthPanel`, `RecentRunsPanel` (reuse `RecentRunsTracker`), `NextBestActionsPanel`
- 5-KPI grid actuel → reduce à 3-4 KPIs essentiels (no mur)

**État cible** : Active (E2E fonctionnel post-Phase C1)

**Décision A1** : `🟢 VERT` structurellement, refonte UX seulement (FR-8). Drop `CommandCenterTopbar` legacy. Drop "Open V26 archive" CTA. Drop redondance `DashboardTabs` (peut migrer en drill-down Fleet Health).

---

### 1.2 Espace 2 — Clients (`/clients` + `/clients/[slug]`)

**Description** : portefeuille agence + workspace central par client. Réponse à la question **"Où en est le client X ?"**. C'est le hub canonique tous artefacts produits liés à un client passent par ici.

**Persona principale** : Mathis avant un call client. Veut voir en 1 vue : score audit, dernier run, recos en attente, statut Reality (si configuré), Brand DNA.

**Routes incluses** :
- `/clients` — liste paginée filtrable triable du portefeuille (status A1 §1.2 : 🟢 VERT)
- `/clients/[slug]` — workspace central per-client avec tabs (cf. décision Mathis A1 §11.3)

**Tabs proposés pour `/clients/[slug]`** (URL state `?tab=`) — **6 tabs core** (décision Mathis 2026-05-17 : alignement progressive disclosure D3 + workflow-first, vs 9 tabs initial draft) :

| Tab key | Label | Contenu | Source data | État A1 | Notes |
|---|---|---|---|---|---|
| `overview` (default) | Overview | Score résumé 6-pilier radial + KPIs (audits count, score moyen, dernier run) + Brand DNA preview compact + 3-5 alertes principales | `getClientBySlug` + `listAuditsForClient` (top-3) + `clientCredentialsReport` | New (refonte D1) | Default tab landing |
| `audits` | Audits | Liste audits du client groupés par `page_type` (= contenu actuel `/audits/[clientSlug]` réutilisé inline) ou empty state | `listAuditsForClient` | 🟢 VERT existant | Wire vers `/audits/[clientSlug]/[auditId]` sur click |
| `recos` | Recos | Toutes recos du client (FUSION ancien `/recos/[clientSlug]` — décision Mathis A1 §11.3). Filters priority/criterion + lifecycle pills. | `listRecosForClient` | 🟠 ORANGE FUSION | Drop la route `/recos/[clientSlug]` → redirect 301 ici |
| `brand-dna` | Brand DNA | Viewer Brand DNA V29 + AURA V30 (FUSION ancien `/clients/[slug]/dna` — décision A1 §1.4) | `getClientBySlug.brand_dna_json` + `loadAuraTokens` | 🟠 ORANGE FUSION | Drop la route séparée `/dna` → redirect 301 ici |
| `gsg` | GSG | Design Grammar viewer scoped + lien "Open Studio for X" → `/gsg/studio?client=<slug>` + history runs GSG client | `loadDesignGrammar(slug)` + `listGsgRunsByClient(slug)` | New (post-F5) | Convergence Studio entry-point |
| `advanced` | Advanced | **3 cards stackées** : Reality (CredentialsGateGrid + 5 sparklines), GEO (engines × queries per-client), Scent (trail diagram ou no_data) — chacune avec `<ModuleMaturityBadge>` visible. Drill-down par card → routes dédiées `/reality/[slug]`, `/geo/[slug]`. | `clientCredentialsReport` + `listGeoAudits(client.id)` + `listScentTrails(slug)` | 🟠 ORANGE (3 modules sous-jacents) | UX only G1/G2, backend deferred Mathis |

**Tabs hors workspace client (décision 2026-05-17, alignement plan refonte)** :
- **Learning** + **Experiments** → cross-client par nature (doctrine proposals + A/B globaux), restent dans espace top-level Advanced Intelligence, **PAS** dans `/clients/[slug]` tabs.
- **Opportunities** → top-level espace Audits & Recos (priorisation cross-client per FR-15/E3), **PAS** tab client.
- **History** tab → defer post-MVP (timeline actions client). Reprise post-Wave 4 si valeur prouvée.
- **Funnel** → SUPPRIMÉ entièrement (décision Mathis A1 §11.1). Route `/funnel/[slug]` disparaît + link source dans `clients/[slug]/page.tsx:80` retiré.

**Drill-down patterns** :
- `audits` tab item → `/audits/[clientSlug]/[auditId]` (existant)
- `recos` tab item → modal edit ou inline edit (FR-13 useEdit pattern)
- `gsg` tab "Open Studio" → `/gsg/studio?client=<slug>`
- `advanced` tab Reality card → `/reality/[clientSlug]` (deep-dive per connector)
- `advanced` tab GEO card → `/geo/[clientSlug]` (deep-dive per engine)
- `advanced` tab Scent card → drill-down inline ou expand (pas de route dédiée per-client pour scent encore)
- Top-level Advanced Intelligence sidebar item → `/reality`, `/geo`, `/learning`, `/experiments`, `/scent` (cross-client dashboards)

**Composants prévus** :
- `ClientWorkspaceTabs` (extension de `ClientDetailTabs` existant) — Tabs primitive de `@growthcro/ui`, **6 tabs**
- `ClientHeroBlock` (existant, GARDÉ)
- `PillarRadialChart` (existant, GARDÉ)
- Per-tab :
  - `OverviewTabPanel` (new) — alertes + KPIs + Brand DNA preview compact
  - `AuditsTabPanel` (réutilise contenu actuel `/audits/[clientSlug]`)
  - `RecosTabPanel` (new, FUSION) — lifecycle pills + RichRecoCard items
  - `BrandDnaTabPanel` (réutilise actuel `/clients/[slug]/dna`, FUSION)
  - `GsgTabPanel` (new) — Design Grammar viewer + GSG runs history + CTA "Open Studio"
  - `AdvancedTabPanel` (new) — 3 sous-cards : `RealityModuleCard`, `GeoModuleCard`, `ScentModuleCard`, chacune avec `<ModuleMaturityBadge>`

**État cible** : Active (E2E fonctionnel post-Phase D1)

**Décision A1 + A2 (2026-05-17)** : `🟢 VERT` structurellement, refonte UX progressive disclosure (FR-21). **6 tabs core** (vs 9 plats initialement draft) : Overview · Audits · Recos · Brand DNA · GSG · Advanced. Fusion 2 routes (`/dna` + `/recos/[clientSlug]`) en tabs. Reality/GEO/Scent groupés sous `advanced` tab avec cards + Maturity badges + drill-down vers routes dédiées top-level Advanced Intelligence. Learning/Experiments restent cross-client (top-level uniquement). Opportunities = top-level Audits & Recos. History tab post-MVP. Funnel SUPPRIMÉ.

---

### 1.3 Espace 3 — Audits & Recos (`/audits` + sub-routes)

**Description** : workflow audit → score → recos → opportunity. Réponse à la question **"Quelles actions sont à shipper sur X audit ?"**.

**Persona principale** : Mathis en revue de recos sur un audit spécifique, ou en post-mortem sur un audit qui a tourné mal.

**Routes incluses** (toutes GARDÉES, décision Mathis A1 §11.2) :

| Route | Rôle | État A1 | Décision |
|---|---|---|---|
| `/audits` | Landing client picker | 🟢 VERT minimal | GARDÉ (décision Mathis A1 §11.2) |
| `/audits/[clientSlug]` | Drill-down audits per client groupés par `page_type` + tabs page-types + top-3 recos per audit | 🟢 VERT | GARDÉ + sidebar uniformisée |
| `/audits/[clientSlug]/[auditId]` | Detail single audit + AuditDetailFull + re-run capture + edit modal | 🟢 VERT | GARDÉ + sidebar uniformisée |
| `/audits/[clientSlug]/[auditId]/judges` | Multi-judge V26.D panel (`scores_json.judges_json`) | 🟢 VERT | GARDÉ + sidebar uniformisée |

**Note importante : pas de vue cross-client `/recos`** (décision Mathis A1 §11.3) :
- `/recos` cross-client view → **DROP** (redirect 301 vers `/clients` ou message "Sélectionnez un client")
- `/recos/[clientSlug]` → **FUSIONNÉ en tab `/clients/[slug]?tab=recos`** (redirect 301)
- Toutes les recos sont vues dans contexte client uniquement. Focus client > vue agrégée.

**Flow nominal post-refonte** (cf. PRD FR-9 Story 2 — audit orchestré) :
1. Mathis depuis `/clients/[slug]` clique "Audit page X" → 1 POST `/api/runs` `type=audit_full`
2. Worker handler `audit_full` (nouveau, Phase D2) chaîne capture → score → recos séquentiellement
3. UI affiche les 3 étapes en realtime (subscribe `public:runs`)
4. Résultats auto-affichés à completion, redirect optionnel vers `/audits/[clientSlug]/[auditId]`

**Composants prévus** :
- `ClientPicker` (existant, GARDÉ pour landing `/audits`)
- `PageTypesTabs`, `AuditQualityIndicator`, `ConvergedNotice`, `PillarsSummary`, `RichRecoCard` (existants)
- `AuditDetailFull`, `AuditEditTrigger`, `AuditStatusPill`, `TriggerRunButton` (existants)
- `JudgesConsensusPanel` (existant)
- New `OpportunitiesBoard` (FR-15 PRD, Phase E3) — lecture Opportunity Layer module Python, promote reco → opportunity
- Use new `useEdit` hook (FR-13) pour reco inline editing

**État cible** : Active (E2E fonctionnel + opportunity board post-Phase E3)

**Décision A1** : `🟢 VERT` structurellement. Refonte UX modeste : Sidebar uniforme + Module Maturity + opportunities board (FR-15).

---

### 1.4 Espace 4 — GSG Studio

**Description** : vrai studio de génération LP E2E (wizard → run → preview → export). Réponse à la question **"Je veux générer une LP"**.

**Persona principale** : Mathis en mode création — veut tester un nouveau brief sur client X, voir la LP en preview iframe, exporter le HTML.

**Routes incluses** (cf. PRD FR-10, FR-11, FR-12 — refonte F5) :

| Route | Rôle | État actuel | Décision |
|---|---|---|---|
| `/gsg` | Design Grammar viewer (TROMPEUR — pas le studio) | 🟠 ORANGE | **RENOMMER** + REDIRECT 301 → `/gsg/studio` (FR-10) |
| `/gsg/studio` | **NEW — wizard 6-8 étapes** = entry-point canonique du studio | n/a | Créer Phase F2 |
| `/gsg/runs` | **NEW — history des runs GSG** | n/a | Créer Phase F2 |
| `/gsg/runs/[id]` | **NEW — preview iframe + QA status + export HTML** | n/a | Créer Phase F2/F3 (refactor `HandoffBriefSection`) |
| `/gsg/design-grammar/[client]` | **NEW — viewer Design Grammar dédié** (anciennement `/gsg`) | renommage | Créer Phase F5 (extrait de `/gsg` actuel) |
| `/gsg/handoff` | Wizard fragile actuel (UUID paste manual, output_path race) | 🟠 ORANGE | **REFONDRE** → migre vers `/gsg/studio` (FR-10/FR-11/FR-12). Drop UUID paste seam (HandoffBriefSection.tsx:75-100). Redirect 301 `/gsg/handoff` → `/gsg/studio` |

**Flow nominal post-refonte** (cf. PRD FR-11 Story 3) :
1. Mathis depuis `/gsg/studio` complète wizard 6-8 étapes (client, page_type, audience, mode, brand DNA scope, copy guidance, etc.)
2. Submit wizard → POST `/api/runs` `type=gsg` → redirect automatique vers `/gsg/runs/[id]`
3. `/gsg/runs/[id]` affiche preview iframe live (subscribe `public:runs`) + QA status (gates, evidence count, killer_rules violations) + export button
4. Output_path validé post-completion (FR-12) — fallback message si HTML absent
5. Click export → download HTML ou copy permalink

**Sub-pages atteignables depuis Studio** :
- `/gsg/design-grammar/[client]` — viewer per-client de la Design Grammar V30 (7 artefacts : tokens.css/json, component_grammar, section_grammar, composition_rules, brand_forbidden_patterns, quality_gates)
- `/gsg/runs` — history pour reprendre un run précédent ou comparer 2 LPs

**Composants prévus** :
- `BriefWizard` (existant mais extrait de `HandoffBriefSection` → autonome dans `/gsg/studio`)
- `GsgRunPreview` (existant) — preview iframe + realtime subscribe
- New `GsgRunsHistoryList` (Phase F2)
- New `GsgQaPanel` (gates status, evidence count, killer_rules violations — Phase F3)
- `DesignGrammarViewer` (existant, GARDÉ pour sub-page)
- Drop `EndToEndDemoFlow` (legacy demo)
- Drop UUID paste input (HandoffBriefSection.tsx:75-100)

**État cible** : Active (E2E fonctionnel post-Phase F5)

**Décision A1** : `🟠 ORANGE` → refonte structurelle. Renommage `/gsg` → `/gsg/design-grammar/[client]`. Création `/gsg/studio` + `/gsg/runs` + `/gsg/runs/[id]`.

---

### 1.5 Espace 5 — Advanced Intelligence

**Description** : modules avancés (Reality / GEO / Learning / Experiments / Scent) groupés sous un parent avec **Module Maturity Model honnête**. Réponse à la question **"Quel est l'état des modules avancés ?"** sans mentir sur ce qui est ready/blocked/no_data.

**Persona principale** : Mathis en mode exploration ou debug — veut voir l'état réel d'un module avant d'engager du temps à le configurer.

**Pourquoi grouper** : ces 5 modules partagent les caractéristiques suivantes :
- Backend partiellement déployé (skeleton honnête) — pas E2E pour 100% des clients
- Dépendances externes (OAuth, API keys, pipelines disk)
- Module Maturity ≠ Active sur la plupart des installs
- Pas dans le workflow quotidien (vs Audits & Recos qui sont quotidiens)

**Routes incluses** :

| Sous-module | Route | État actuel | Maturity probable | Décision A1 |
|---|---|---|---|---|
| Reality Layer | `/reality` + `/reality/[clientSlug]` | 🟠 ORANGE — skeleton honnête, OAuth absentes | `ready_to_configure` | GARDER UX only (FR-16) |
| GEO Monitor | `/geo` + `/geo/[clientSlug]` | 🟠 ORANGE — empty state honnête (keys missing) | `ready_to_configure` | GARDER UX only (FR-17) |
| Learning Lab | `/learning` + `/learning/[proposalId]` | 🟢 VERT functional BUT OPEN QUESTION (FR-18 spike) | `experimental` | NE PAS refondre UI avant G3 spike (FR-18) |
| Experiments | `/experiments` | 🟢 calc OK BUT dispatcher noop | `experimental` ou `archived` selon G4 | NE PAS refondre UI avant G4 spike (FR-19) |
| Scent Trail | `/scent` | 🟠 ORANGE — 95% "Aucun scent trail" | `no_data` | GARDER + UX honest empty state |

**Sub-nav schema** (proposé) :

L'espace Advanced Intelligence a un sous-menu déroulant dans la sidebar avec les 5 modules. Chaque module top-level affiche un `<ModuleMaturity>` badge visible (cf. A3 livrable) :

```
🧠 Advanced Intelligence  [▼ expand/collapse]
   ├── 📊 Reality           [ready_to_configure]
   ├── 🔍 GEO Monitor       [ready_to_configure]
   ├── 🧪 Learning Lab      [experimental ⓘ G3 spike pending]
   ├── ⚗️ Experiments       [experimental ⓘ G4 spike pending]
   └── 🌫️ Scent Trail       [no_data]
```

**Décision UX sub-menu** :
- Expand/collapse via click sur le parent "Advanced Intelligence"
- État expansion persisté en localStorage (`gc-sidebar-advanced-expanded`)
- Active deep-match : si pathname start `/reality` ou `/geo` ou `/learning` ou `/experiments` ou `/scent` → parent expanded + child highlighted
- Badge maturity affiché à droite du label (variant `soft` pour ready_to_configure, `amber` pour experimental, `red` pour blocked, `green` pour active)
- Max 5 children sous un parent (anti-pattern UX si >5 — cf. stop condition A2)

**Composants prévus** (par sub-module) :

**Reality Layer** :
- `<ModuleMaturity status="ready_to_configure" reason="OAuth credentials missing" next_step="Configurer Catchr/Meta/Google/Shopify/Clarity/GA4/TikTok dans Settings" />` (FR-5/FR-16)
- `RealityHeatMap` (existant) — fleet view
- `CredentialsGateGrid`, `RealitySparkline` (existants) — per-client
- Backend OAuth wiring DEFERRED (PRD §Out of Scope)

**GEO Monitor** :
- `<ModuleMaturity status="ready_to_configure" reason="OPENAI_API_KEY / PERPLEXITY_API_KEY missing" next_step="Ajouter clés dans .env / Vercel env" />` (FR-5/FR-17)
- `EnginePresenceCards`, `QueryBankViewer`, `PerClientGeoGrid` (existants)

**Learning Lab** :
- `<ModuleMaturity status="experimental" reason="Bayesian approach OPEN QUESTION — spike G3 en cours" />` (FR-18)
- `ProposalQueue`, `ProposalStats`, `LifecycleBarsChart`, `ProposalDetail` (existants)
- UI re-build DEFERRED jusqu'à `LEARNING_LAYER_APPROACH_DECISION.md` tranché (FR-18)

**Experiments** :
- `<ModuleMaturity status="experimental" reason="Dispatcher worker noop — decision spike G4 implement vs archive" />` (FR-19)
- `SampleSizeCalculator` (calc functional), `RampUpMatrix`, `KillSwitchesMatrix`, `ActiveExperimentsList` (existants)
- UI re-build DEFERRED jusqu'à G4 tranché

**Scent Trail** :
- `<ModuleMaturity status="no_data" reason="Cross-channel captures pipeline deferred" next_step="Manual scent_trail.json drop ou attendre batch capture pipeline" />`
- `ScentFleetKPIs`, `ScentFleetTable`, `ScentTrailDiagram`, `BreaksList` (existants)

**État cible** : Mixed
- Reality, GEO, Scent : UX honest skeleton (Active UX, Backend deferred)
- Learning, Experiments : NE PAS REFONDRE UI avant spikes G3/G4

**Décision A1** : groupage en sous-menu + Module Maturity sur chacun.

---

## 2. Utilitaires + Public

### 2.1 Doctrine (`/doctrine`) — utility reference

**Description** : référence pédagogique V3.2.1 piliers + critères. Hors workflow quotidien. C'est la "doc produit" embarquée.

**Routes incluses** :
- `/doctrine` — viewer pédagogique 7-piliers (existant, A1 §1.22 🟢 VERT)

**Composants** : `ClosedLoopDiagram`, `DogfoodCard`, `PillierBrowser` (existants). Drop `ViewToolbar` (A1 §2.4 décision SUPPRIMER) → refactor en pattern `gc-topbar` inline comme autres routes.

**Position sidebar** : section "Reference" séparée du bloc 5-espaces. Visible mais discret.

**État cible** : Active (E2E fonctionnel) — GARDER tel quel + drop ViewToolbar.

---

### 2.2 Settings (`/settings`) — utility admin

**Description** : org / team / usage / API config. Admin-only majoritairement.

**Routes incluses** :
- `/settings` (4 tabs : Account / Team / Usage / API) — existant A1 §1.23 🟢 VERT

**Composants** : `SettingsTabs`, `AccountTab`, `TeamTab`, `UsageTab`, `ApiTab` (existants).

**Position sidebar** : section "Admin" séparée du bloc 5-espaces. Footer position (avec session block).

**État cible** : Active — GARDER tel quel.

---

### 2.3 Public — hors sidebar

**Routes incluses** :
- `/login` (Supabase password + magic link) — A1 §1.26 🟢 VERT
- `/auth/callback`, `/auth/signout` (route handlers) — A1 §1.27 🟢 VERT
- `/privacy` (RGPD static) — A1 §1.28 🟢 VERT
- `/terms` (CGU static) — A1 §1.29 🟢 VERT

**Décision A1** : aucun changement. Sidebar **NE rend PAS** sur ces routes (cf. FR-2 exclusion list).

---

## 3. Nav schema cible

### 3.1 Sidebar — structure workflow-first

**Structure proposée** :

```
SIDEBAR (gc-side)
├── [Brand] GrowthCRO V28
├── [+ Ajouter un client]               (admin only — AddClientTrigger pill gold)
├── ─────────────────────────────────── (separator)
│
├── ── ESPACES ──                       (group label "Spaces")
├── 🏠 Command Center        →  /
├── 🏢 Clients               →  /clients                    [badge: clients count]
├── 🔍 Audits & Recos        →  /audits                     [badge: audits + recos P0]
├── ✨ GSG Studio            →  /gsg/studio                 [badge: runs in progress]
├── 🧠 Advanced Intelligence [▼ expand/collapse]
│     ├── 📊 Reality          →  /reality                   [maturity: ready_to_configure]
│     ├── 🔍 GEO Monitor      →  /geo                       [maturity: ready_to_configure]
│     ├── 🧪 Learning Lab     →  /learning                  [maturity: experimental + badge: pending review]
│     ├── ⚗️ Experiments      →  /experiments               [maturity: experimental]
│     └── 🌫️ Scent Trail      →  /scent                     [maturity: no_data]
│
├── ─────────────────────────────────── (separator)
├── ── REFERENCE ──                     (group label "Reference")
├── 📚 Doctrine              →  /doctrine
│
├── ─────────────────────────────────── (separator)
├── ── ADMIN ──                         (group label "Admin")
├── ⚙️ Settings              →  /settings
│
├── ── SESSION ──                       (footer block)
├── [email]
└── [Déconnexion] (form POST /auth/signout)
```

**Décisions structurelles** :

| Décision | Rationale | Source |
|---|---|---|
| Sidebar rendue uniformément sur toutes routes sauf public | Fix inconsistance A1 §2.1 (5/25 routes seulement aujourd'hui) | FR-2 |
| 5 espaces principaux groupés sous "Spaces" | Workflow-first vs architecture-internal | FR-1 |
| Advanced Intelligence comme parent expand/collapse | Grouper 5 modules avancés sous 1 parent (anti-pattern UX si plat) | A2 stop condition + cf. §1.5 |
| Reference (Doctrine) séparé des espaces | Doctrine = utility référence, pas un espace produit | A2 IA |
| Admin (Settings) en footer | Convention UX — utility admin discret | A2 IA |
| Badges counts computed server-side | Existant (`SidebarBadges` interface) — étendre avec recos+runs | Sidebar.tsx:31 |
| Active deep-match (highlight chemin actif) | Existant (`isActive` helper) | Sidebar.tsx:40 |
| `/audit-gads`, `/audit-meta` **HIDE de sidebar** | Dead UI (buttons disabled "post-MVP") — URL accessible directement | FR-25 |
| `/funnel/[slug]` **SUPPRIMÉE** | Décision Mathis A1 §11.1 | FR-24 |
| Sous-menu Advanced Intelligence : max 5 children | Stop condition A2 (anti-pattern UX si >5) | A2 stop conditions |
| Module Maturity badge inline (variant `soft`/`amber`/`red`) | Honnêteté produit — user voit l'état réel | FR-5 |

**Icônes proposées** (emoji unicode — peut migrer Lucide post-Phase H si Mathis préfère) :
- 🏠 Command Center (home/maison)
- 🏢 Clients (building/portefeuille)
- 🔍 Audits & Recos (loupe/audit)
- ✨ GSG Studio (sparkles/génération)
- 🧠 Advanced Intelligence (cerveau)
- 📊 Reality (chart/data)
- 🔍 GEO Monitor (loupe SEO/GEO)
- 🧪 Learning Lab (tube à essai/expérimentation)
- ⚗️ Experiments (alambic/A-B test)
- 🌫️ Scent Trail (brume/trail)
- 📚 Doctrine (livre/référence)
- ⚙️ Settings (engrenage)

**Note Mathis-décidable** : si emojis trop "fun" pour le ton produit (perfectionniste / avant-garde), migrer vers Lucide icons (`Home`, `Building2`, `Search`, `Sparkles`, `Brain`, etc.) en Phase H design system pass.

### 3.2 Topbar (StickyHeader uniformisé)

**Composition** (left to right) :

```
[StickyHeader rendu sur toutes routes authenticated]
│
├── [Left]    DynamicBreadcrumbs       (existant — pathname-derived)
├── [Center]  Cmd+K trigger button     ("Search… ⌘K")
├── [Right]   WorkerHealthPill         (FR-3 new — global liveness badge)
├── [Right]   User menu                (avatar dropdown : email, settings shortcut, logout)
└── [Right]   Notifications badge      (OPTIONAL post-MVP, defer if scope creep)
```

**Décisions topbar** :

| Décision | Rationale | Source |
|---|---|---|
| StickyHeader rendu sur toutes routes authenticated | Fix A1 §2.2 (1/25 routes seulement aujourd'hui) | FR-2 |
| WorkerHealthPill global visible (online/lagging/offline) | Fix A1 §1 issue #5 — worker liveness invisibility | FR-3/FR-4 |
| Cmd+K trigger central (mac-style) | UX convention (Linear, Vercel, Slack) | A2 IA |
| "/" focus shortcut | Existant Sprint 11 | A1 §2.2 |
| Drop CommandCenterTopbar legacy | A1 §2.3 — coexistance avec StickyHeader | FR-24 |
| Drop ViewToolbar | A1 §2.4 — 1 caller seulement (`/doctrine`) | FR-24 |
| Notifications badge — defer post-MVP | Scope creep si embarqué dans cet epic | A2 stop condition |

### 3.3 Breadcrumbs rules

**Composant** : `DynamicBreadcrumbs` (existant — `webapp/apps/shell/components/chrome/DynamicBreadcrumbs.tsx`), uniformisé global via StickyHeader.

**Règles déclaratives** :

| Pattern URL | Breadcrumb rendu | Notes |
|---|---|---|
| `/` | (caché — HIDDEN_PATHS) | Home seul, pas de breadcrumb |
| `/clients` | Clients | Top-level espace |
| `/clients/[slug]` | Clients › **[client name]** | Resolve slug → name via SEGMENT_LABELS ou lookup côté breadcrumb |
| `/clients/[slug]?tab=audits` | Clients › [client name] › Audits | Tab key surfacé dans breadcrumb (NEW) |
| `/clients/[slug]?tab=brand-dna` | Clients › [client name] › Brand DNA | Tab key |
| `/clients/[slug]?tab=recos` | Clients › [client name] › Recos | Tab key |
| `/audits` | Audits & Recos | Top-level espace |
| `/audits/[slug]` | Audits & Recos › **[client name]** | Resolve slug |
| `/audits/[slug]/[auditId]` | Audits & Recos › [client name] › Audit [shortId] | UUID humanize (existant) |
| `/audits/[slug]/[auditId]/judges` | Audits & Recos › [client name] › Audit [shortId] › Judges | Deep |
| `/gsg/studio` | GSG Studio | Top-level espace |
| `/gsg/runs` | GSG Studio › Runs | Sub-page |
| `/gsg/runs/[id]` | GSG Studio › Runs › Run [shortId] | Deep |
| `/gsg/design-grammar/[client]` | GSG Studio › Design Grammar › [client name] | Deep |
| `/reality` | Advanced Intelligence › Reality | Sub-module |
| `/reality/[slug]` | Advanced Intelligence › Reality › [client name] | Deep |
| `/geo` | Advanced Intelligence › GEO Monitor | Sub-module |
| `/geo/[slug]` | Advanced Intelligence › GEO Monitor › [client name] | Deep |
| `/learning` | Advanced Intelligence › Learning Lab | Sub-module |
| `/learning/[proposalId]` | Advanced Intelligence › Learning Lab › Proposal [shortId] | Deep |
| `/experiments` | Advanced Intelligence › Experiments | Sub-module |
| `/scent` | Advanced Intelligence › Scent Trail | Sub-module |
| `/doctrine` | Doctrine | Utility |
| `/settings` | Settings | Utility |
| `/login`, `/privacy`, `/terms`, `/auth/*` | (caché — HIDDEN_PATHS) | Public |
| `/audit-gads`, `/audit-meta` | Audit Google/Meta Ads (hidden from sidebar but rendered if user lands via URL) | FR-25 |

**Note** : breadcrumb pour le parent virtuel "Advanced Intelligence" est un crumb non-clickable (pas de page `/advanced` — c'est juste un groupage sidebar). Click sur le crumb top-level → no-op ou retour à `/` (à décider Phase B1).

**Updates à `DynamicBreadcrumbs.tsx`** (Phase B1) :
- Étendre `SEGMENT_LABELS` map FR avec nouveaux segments (`gsg/studio`, `gsg/runs`, `gsg/design-grammar`)
- Tab state surface : si URL contient `?tab=X`, append crumb tab label
- Resolve slug → client name via lookup côté breadcrumb (utiliser cookie/cache léger, pas refetch Supabase à chaque render)
- HIDDEN_PATHS étendu si besoin (mais a priori inchangé)

### 3.4 Cmd+K palette items — actions globales canoniques

**Composant** : `CmdKPalette` (existant — `webapp/apps/shell/components/chrome/CmdKPalette.tsx`), source `lib/cmdk-items.ts`. Uniformisé global via StickyHeader (FR-2).

**Principes Cmd+K** :
1. Chaque item est **actionnable** (navigate / open modal / trigger action) — pas de fake placeholder
2. Items groupés par espace (Command Center, Clients, Audits & Recos, GSG Studio, Advanced Intelligence)
3. Section "Recent" en haut (localStorage `gc-cmdk-recent`, max 5 — existant)
4. Section "Admin actions" en bas (admin-gated, existant)
5. Autocomplete fuzzy sur label / hint / href (existant `filterEntries`)

**Items canoniques proposés** (mise à jour de `lib/cmdk-items.ts` Phase B1) :

#### Command Center
| Label | Hint | Action | Type |
|---|---|---|---|
| "Open Command Center" | "Home overview" | navigate `/` | nav |

#### Clients
| Label | Hint | Action | Type |
|---|---|---|---|
| "Browse clients" | "Fleet · list" | navigate `/clients` | nav |
| "Add client" | "+ create" | open `AddClientModal` (admin only) | action |
| "Go to client [autocomplete]" | "Workspace" | navigate `/clients/[slug]` (autocomplete via `clients_database` query) | nav + autocomplete |

#### Audits & Recos
| Label | Hint | Action | Type |
|---|---|---|---|
| "Open Audits" | "Picker" | navigate `/audits` | nav |
| "Run new audit" | "Capture → score → recos" | open `CreateAuditModal` (FR-9 audit_full orchestrated) | action |
| "Find audit [autocomplete]" | "By client or ID" | navigate `/audits/[slug]/[id]` (autocomplete recent audits) | nav + autocomplete |
| "Find reco [autocomplete]" | "By client or text" | navigate `/clients/[slug]?tab=recos` + scroll to reco | nav + autocomplete |

#### GSG Studio
| Label | Hint | Action | Type |
|---|---|---|---|
| "New GSG brief" | "Open Studio wizard" | navigate `/gsg/studio` | nav |
| "View latest run" | "Last GSG output" | navigate `/gsg/runs/[id]` (most recent) | nav |
| "Browse GSG runs" | "History" | navigate `/gsg/runs` | nav |
| "Browse Design Grammar" | "Per-client viewer" | navigate `/gsg/design-grammar/[client]` (autocomplete clients with DG) | nav + autocomplete |

#### Advanced Intelligence
| Label | Hint | Action | Type |
|---|---|---|---|
| "Reality status" | "Fleet heat map" | navigate `/reality` | nav |
| "Connect Reality connector" | "OAuth" | scroll to `CredentialsGateGrid` in `/clients/[slug]?tab=reality` (UX only) | nav |
| "GEO results" | "Engines presence" | navigate `/geo` | nav |
| "Review Learning proposals" | "Queue" | navigate `/learning` | nav |
| "Open Experiments" | "Calculator + active" | navigate `/experiments` | nav |
| "Scent trails" | "Cross-channel" | navigate `/scent` | nav |

#### Reference
| Label | Hint | Action | Type |
|---|---|---|---|
| "Search doctrine criteria" | "V3.2.1" | navigate `/doctrine` + scroll (advanced filter post-MVP) | nav |
| "View pillar [autocomplete]" | "V3.2.1" | navigate `/doctrine?pillar=<N>` | nav |

#### Settings / Admin
| Label | Hint | Action | Type |
|---|---|---|---|
| "Open settings" | "Account/Team/Usage/API" | navigate `/settings` | nav |
| "Invite team member" | "Admin" | navigate `/settings?tab=team` + open invite form (admin only) | action |
| "Switch team / Manage usage" | "Admin" | navigate `/settings?tab=usage` (admin only) | nav |
| "View privacy policy" | "RGPD" | navigate `/privacy` | nav |
| "Sign out" | "End session" | trigger form POST `/auth/signout` | action |

**Autocomplete sources** (Phase B1 wiring) :
- Clients : `clients_database` table (existant — déjà loadé `listClientsWithStats`)
- Audits : `audits` recent (last 50 par admin / 20 par user)
- GSG runs : `runs` where type=`gsg` (last 20)
- Design Grammar clients : `listClientsWithDesignGrammar()` (FS walk existant)

**Items hidden from Cmd+K** :
- `/audit-gads`, `/audit-meta` — drop entries from `lib/cmdk-items.ts:63-64` (FR-25). URL accessible directement, mais pas listés.
- `/funnel/[clientSlug]` — déjà absent de `cmdk-items.ts`, route SUPPRIMÉE entièrement (FR-24).

---

## 4. Mapping ancien → nouveau (consolidé A1 §7 + décisions Mathis §11)

### 4.1 Tableau complet de transition

| Route actuelle | Nouvel espace cible | Nouvelle URL probable | Action | Redirect 301 | Notes |
|---|---|---|---|---|---|
| `/` | Command Center | `/` | GARDER + refondre UX | n/a | Refonte 4 zones (C1) |
| `/clients` | Clients | `/clients` | GARDER + refondre UX | n/a | Progressive disclosure (D1) |
| `/clients/[slug]` | Clients | `/clients/[slug]` | GARDER + refondre en workspace tabs | n/a | Default tab `overview` |
| `/clients/[slug]/dna` | Clients | `/clients/[slug]?tab=brand-dna` | FUSIONNER en tab | `/clients/[slug]/dna` → `/clients/[slug]?tab=brand-dna` (301) | Décision A1 §1.4 |
| `/audits` | Audits & Recos | `/audits` | GARDER (picker) | n/a | Décision Mathis A1 §11.2 |
| `/audits/[clientSlug]` | Audits & Recos | `/audits/[clientSlug]` | GARDER + sidebar uniformisée | n/a | Pattern intelligent (page_types tabs) |
| `/audits/[clientSlug]/[auditId]` | Audits & Recos | `/audits/[clientSlug]/[auditId]` | GARDER tel quel | n/a | Excellent E2E |
| `/audits/[clientSlug]/[auditId]/judges` | Audits & Recos | `/audits/[clientSlug]/[auditId]/judges` | GARDER + uniformiser shell | n/a | Multi-judge V26.D |
| `/recos` | n/a | n/a | **DROP** vue cross-client | `/recos` → `/clients` (301) | Décision Mathis A1 §11.3 |
| `/recos/[clientSlug]` | Clients | `/clients/[slug]?tab=recos` | FUSIONNER en tab | `/recos/[clientSlug]` → `/clients/[slug]?tab=recos` (301) | Décision Mathis A1 §11.3 |
| `/gsg` | GSG Studio | (redirect) | RENOMMER + redirect | `/gsg` → `/gsg/studio` (301) | FR-10 |
| (nouveau) | GSG Studio | `/gsg/studio` | **CRÉER** Phase F2 | n/a | Wizard entry-point |
| (nouveau) | GSG Studio | `/gsg/runs` | **CRÉER** Phase F2 | n/a | History |
| (nouveau) | GSG Studio | `/gsg/runs/[id]` | **CRÉER** Phase F2/F3 | n/a | Preview + QA + export |
| (nouveau) | GSG Studio | `/gsg/design-grammar/[client]` | **CRÉER** Phase F5 (extrait `/gsg`) | n/a | Viewer dédié |
| `/gsg/handoff` | GSG Studio | `/gsg/studio` | REFONDRE + redirect | `/gsg/handoff` → `/gsg/studio` (301) | FR-10/FR-11/FR-12 |
| `/learning` | Advanced Intelligence | `/learning` | GARDER + Module Maturity | n/a | UI rebuild DEFERRED jusqu'à G3 spike (FR-18) |
| `/learning/[proposalId]` | Advanced Intelligence | `/learning/[proposalId]` | GARDER + uniformiser shell | n/a | Idem |
| `/experiments` | Advanced Intelligence | `/experiments` | GARDER + Module Maturity | n/a | UI rebuild DEFERRED jusqu'à G4 spike (FR-19) |
| `/reality` | Advanced Intelligence | `/reality` | GARDER + Module Maturity | n/a | UX only, backend deferred (FR-16) |
| `/reality/[clientSlug]` | Advanced Intelligence | `/reality/[clientSlug]` | GARDER + Module Maturity | n/a | Per-client. Cross-link depuis `/clients/[slug]?tab=reality` |
| `/geo` | Advanced Intelligence | `/geo` | GARDER + Module Maturity | n/a | UX honest activation (FR-17) |
| `/geo/[clientSlug]` | Advanced Intelligence | `/geo/[clientSlug]` | GARDER + Module Maturity | n/a | Per-client. Cross-link depuis `/clients/[slug]?tab=geo` |
| `/scent` | Advanced Intelligence | `/scent` | GARDER + UX honest no_data state | n/a | Cross-channel pipeline deferred |
| `/funnel/[clientSlug]` | n/a | n/a | **SUPPRIMER** | ❌ pas de redirect | Décision Mathis A1 §11.1 |
| `/doctrine` | Reference | `/doctrine` | GARDER + drop ViewToolbar | n/a | Refactor pattern inline `gc-topbar` |
| `/settings` | Admin | `/settings` | GARDER tel quel | n/a | E2E fonctionnel |
| `/login` | Public | `/login` | GARDER tel quel | n/a | Sidebar absent |
| `/auth/callback`, `/auth/signout` | Public | unchanged | GARDER | n/a | Route handlers |
| `/privacy` | Public | `/privacy` | GARDER | n/a | RGPD |
| `/terms` | Public | `/terms` | GARDER | n/a | CGU |
| `/audit-gads` | (hidden) | `/audit-gads` | **CACHER** de nav | n/a | URL accessible. Retirer de `cmdk-items.ts:63` (FR-25) |
| `/audit-meta` | (hidden) | `/audit-meta` | **CACHER** de nav | n/a | URL accessible. Retirer de `cmdk-items.ts:64` (FR-25) |

### 4.2 Décisions Mathis 2026-05-17 (rappel formel — cf. A1 §11)

Ces 4 décisions sont **tranchées et signed-off** par Mathis le 2026-05-17 :

| # | Décision | Action |
|---|---|---|
| 11.1 | `/funnel/[clientSlug]` → **SUPPRIMER** | Retirer route + drop link source `clients/[slug]/page.tsx:80`. Pas de redirect (route invisible nav avant suppression). |
| 11.2 | `/audits` landing → **GARDER** picker | Landing minimale (34 LOC, ClientPicker) reste comme entrée Audits & Recos top-level |
| 11.3 | `/recos` cross-client → **FUSIONNER** en tab `?tab=recos` | Drop vue cross-fleet. Redirect 301 `/recos` → `/clients` + `/recos/[clientSlug]` → `/clients/[slug]?tab=recos` |
| 11.4 | Tables fantômes → **NE PAS toucher en A1** | `screenshots` = bucket Storage ACTIF (NE PAS DROP). `experiments` = table relationnelle lue par UI, décision DROP/keep différée à G4 decision spike |

---

## 5. Redirects 301 plan

### 5.1 Liste complète (compatibilité backward bookmarks)

À implémenter via `webapp/apps/shell/middleware.ts` ou Next.js `redirects()` config (à choisir Phase B1). Liste consolidée :

| From (ancien) | To (nouveau) | Justification | FR |
|---|---|---|---|
| `/gsg` | `/gsg/studio` | Renommage entry-point GSG Studio | FR-10 |
| `/gsg/handoff` | `/gsg/studio` | Refonte wizard | FR-10/FR-11 |
| `/clients/[slug]/dna` | `/clients/[slug]?tab=brand-dna` | Fusion en tab | D1 / Décision A1 §1.4 |
| `/recos` | `/clients` | Drop vue cross-client (décision Mathis §11.3) | A1 §11.3 |
| `/recos/[clientSlug]` | `/clients/[slug]?tab=recos` | Fusion en tab | A1 §11.3 |

**Total : 5 redirects 301**. Conforme à la stop condition A2 (max 3 redirects par espace) : Clients=2, GSG Studio=2, drop=1. Respecte la limite.

**Routes SUPPRIMÉES sans redirect** :
- `/funnel/[clientSlug]` → ❌ pas de redirect (route invisible nav avant suppression — pas de bookmark connu Mathis). Drop link source dans `clients/[slug]/page.tsx:80`.

**Routes CACHÉES mais URL accessible** (pas de redirect — l'URL fonctionne, juste invisible nav) :
- `/audit-gads`
- `/audit-meta`

### 5.2 Implémentation suggérée (Phase B1)

**Option A — Next.js `redirects()` config** (statique, dans `next.config.js`) :
```js
async redirects() {
  return [
    { source: '/gsg', destination: '/gsg/studio', permanent: true },
    { source: '/gsg/handoff', destination: '/gsg/studio', permanent: true },
    { source: '/clients/:slug/dna', destination: '/clients/:slug?tab=brand-dna', permanent: true },
    { source: '/recos', destination: '/clients', permanent: true },
    { source: '/recos/:slug', destination: '/clients/:slug?tab=recos', permanent: true },
  ];
}
```

**Option B — Middleware** (dynamique, dans `middleware.ts`) :
Plus de logique custom mais ajoute latency edge. Pas justifié pour ces 5 redirects statiques.

**Préférence A2** : Option A (statique `next.config.js`). Plus simple, plus rapide, indexé par Next.js compiler.

---

## 6. Risques refonte IA

### 6.1 Risques propres au changement d'IA

| Risque | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bookmarks Mathis cassés après redirect 301 | med | low | Redirects 301 = browser caches. Mathis re-bookmarks en 1 visit. Smoke test pour vérifier que chaque ancien URL résout. |
| User junior perd ses repères (changement sidebar) | low | med | Doc onboarding court (1 page) avec mapping ancien → nouveau. Tour interactif Phase H optional. |
| `/funnel` suppression casse référence externe inconnue | low | low | Vérifier `grep "funnel/" .claude/docs/`. Si reference doc, archiver. |
| Tab state `?tab=` non préservé sur navigation back | low | med | Tabs URL state defensive (existant pattern `ClientDetailTabs` — `?tab=` already URL-driven). |
| Active deep-match sidebar mal calculé pour `/advanced/X` virtuel | med | low | `Sidebar.tsx:40 isActive` étendre : if pathname start `/reality\|geo\|learning\|experiments\|scent` → expand parent Advanced Intelligence. |
| Sub-menu Advanced Intelligence trop chargé visuellement | med | med | Max 5 children (stop condition A2). Module Maturity badge variant `soft` (calm). Collapse par défaut OK (localStorage persist). |
| Cmd+K autocomplete clients query loadée à chaque ouverture (perf) | low | low | Cache léger côté client (`useMemo` sur `listClientsWithStats` déjà loadé pour Sidebar badges). |
| Workspace tabs `/clients/[slug]?tab=X` ne preload pas le contenu (waterfall RSC) | med | high | Server-fetch les data des tabs critiques (audits, recos, brand-dna) en parallèle dès `/clients/[slug]` load. Defer non-critical (geo, reality, scent) à click tab. |
| `/recos` aggregator existant supprimé casse les CTAs depuis home Today/Urgent panel | low | med | Phase C1 (Today/Urgent) link vers `/clients/[slug]?tab=recos` directement, pas `/recos`. |
| Module Maturity badges trompeurs (ex: Reality "ready_to_configure" alors que Mathis pensait "experimental") | low | high | Phase A3 (Module Maturity matrix initiale) sera validée par Mathis avant B1. Pas de wire surprise. |
| GSG Studio refonte casse `/gsg/handoff` smoke test existant | med | high | Feature flag `FEATURE_GSG_STUDIO_V2` par Phase F2. Smoke Playwright wizard → preview. Garder `/gsg/handoff` redirect au lieu de drop hard. |

### 6.2 Mitigations transverses (cf. PRD §Risks)

- **Feature flag par phase** : `FEATURE_NEW_UX_<phase>` (PRD risque #1)
- **Playwright smoke suite** 9 parcours desktop + mobile (FR-23)
- **Redirects 301 tolérance** : tous old URLs continuent à fonctionner pendant ≥3 mois
- **Anti-régression** : 215 tests Renaissance + multi-judge fixtures restent dans CI
- **Doctrine V3.2.1 frozen** : pas de modif Doctrine dans cet epic
- **PRESERVE_CREATIVE_LATITUDE** : intouché dans GSG Studio refonte

---

## 7. Sign-off

**Validé par Mathis 2026-05-17** (décisions formalisées dans cette section).

- [x] **5 espaces** (§1.1-1.5) — Command Center · Clients · Audits & Recos · GSG Studio · Advanced Intelligence ✅
- [x] **Sous-routes de chaque espace** (§1.X tableaux routes incluses) ✅
- [x] **Tabs `/clients/[slug]`** — décision 2026-05-17 : **6 tabs core** (Overview · Audits · Recos · Brand DNA · GSG · Advanced) au lieu de 9 plats. Reality/GEO/Scent regroupés sous `advanced` tab avec cards + Maturity badges + drill-down vers routes dédiées. Learning/Experiments restent cross-client (top-level uniquement). Opportunities = top-level Audits & Recos. History tab post-MVP. Funnel SUPPRIMÉ. ✅
- [x] **Sidebar schema** (§3.1) — sous-menu Advanced Intelligence **expand/collapse** confirmé (5 children Reality/GEO/Learning/Experiments/Scent sous parent unique, pattern Linear/Vercel). Icônes emoji acceptées pour V1, migration Lucide reportée à Phase H1 si esthétique trop "fun" pour le ton produit. ✅
- [x] **Mapping ancien → nouveau** (§4.1) ✅
- [x] **Redirects 301** (§5.1) — 5 redirects via `next.config.js` Option A ✅
- [x] **Cmd+K items canoniques** (§3.4) — par espace, autocomplete sources, items hidden ✅
- [x] **Breadcrumbs rules** (§3.3) — patterns URL → breadcrumb mapping ✅
- [x] **Sous-menu Advanced Intelligence** (§1.5 + §3.1) — 5 modules avec Module Maturity badges visibles, collapse persisté localStorage ✅
- [x] **Implémentation redirects** Option A `next.config.js` static (§5.2) ✅

A3 (Module Maturity Model + matrix initiale, issue #68) + B1 (refonte app shell, post Wave 2 dispatch) peuvent démarrer sur cette base signed-off.

---

## 8. Annexe — Refs croisés

### 8.1 Documents amont consommés

- [`WEBAPP_PRODUCT_AUDIT_2026-05-17.md`](WEBAPP_PRODUCT_AUDIT_2026-05-17.md) — audit Phase A (4 audits parallèles read-only)
- [`WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md`](WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md) — A1 inventaire routes signed-off Mathis 2026-05-17 (§10 + §11 décisions)
- [PRD `webapp-product-ux-reconstruction-2026-05.md`](../../prds/webapp-product-ux-reconstruction-2026-05.md) — §FR-1, FR-2, FR-8, FR-10, FR-11, FR-12, FR-13, FR-25, FR-24
- [Epic `webapp-product-ux-reconstruction-2026-05/A2.md`](../../epics/webapp-product-ux-reconstruction-2026-05/A2.md) — spec issue #67 (acceptance criteria, implementation notes)

### 8.2 Sources code consultées (read-only)

- `webapp/apps/shell/lib/cmdk-items.ts` (100 LOC) — single source of truth nav metadata
- `webapp/apps/shell/components/Sidebar.tsx` (155 LOC) — sidebar markup + badge wiring
- `webapp/apps/shell/components/chrome/StickyHeader.tsx` (99 LOC) — topbar shell global
- `webapp/apps/shell/components/chrome/CmdKPalette.tsx` — palette Cmd+K
- `webapp/apps/shell/components/chrome/DynamicBreadcrumbs.tsx` (108 LOC) — breadcrumbs dynamiques
- `webapp/apps/shell/app/page.tsx` (273 LOC) — home Command Center actuel
- `webapp/apps/shell/app/clients/[slug]/page.tsx` (163 LOC) — fiche client actuelle
- `webapp/apps/shell/app/audits/[clientSlug]/page.tsx` (289 LOC) — audits drill-down pattern
- `webapp/apps/shell/app/gsg/page.tsx` (198 LOC) — Design Grammar viewer (à renommer)
- `webapp/apps/shell/app/gsg/handoff/page.tsx` (316 LOC) — wizard actuel (à refondre)

### 8.3 Documents avals dépendants (bloqués par ce document)

- **A3** (Issue #68) — Module Maturity Model + matrix initiale (bloqué par §1.5 sub-menu Advanced Intelligence)
- **B1** (Phase B1) — refonte app shell (Sidebar + StickyHeader + Breadcrumbs + Cmd+K nested layout) — bloqué par §3.1, §3.2, §3.3, §3.4
- **C1** (Phase C1) — home Command Center 4 zones — bloqué par §1.1
- **D1** (Phase D1) — workspace client tabs progressive disclosure — bloqué par §1.2
- **F5** (Phase F5) — GSG Studio routes (`/gsg/studio`, `/gsg/runs`, `/gsg/runs/[id]`, `/gsg/design-grammar/[client]`) — bloqué par §1.4
- **G\*** (Phase G) — Advanced Intelligence groupé + Module Maturity — bloqué par §1.5 + A3

---

**Document créé 2026-05-17. Source de vérité primaire pour le shell refonte (B1) et toutes les phases workflow-first downstream (C1, D1, F5, G\*). Mise à jour : à chaque clôture de phase, ajouter une section "Post-Phase X delta" listant ce qui a changé.**
