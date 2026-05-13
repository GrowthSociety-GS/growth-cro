---
name: webapp-stratospheric-reconstruction-2026-05
description: MEGA-PRD post-audit 3-agent cross-validated — reconstruction systémique de la webapp Next.js pour atteindre la vision canonique architecturée par Mathis (5-microfrontend Mission Control + FastAPI Fly.io + closed-loop 6 stages) tout en restaurant le visual DNA V22 Stratospheric Observatory perdu lors du port V26 HTML → Next.js. 4 tiers, 16 sub-PRDs, ~25-34 jours solo dev.
status: active
created: 2026-05-14T16:00:00Z
parent_prd: post-stratosphere-roadmap
supersedes: webapp-v26-parity-and-beyond
wave: stratospheric-reconstruction
priority: P0-critical
blocking_decisions: D1, D2, D3, D4 (cf §Constraints)
---

# PRD : webapp-stratospheric-reconstruction-2026-05

> **MEGA-PRD canonique reconstruction systémique webapp** post audit-first 3-agent cross-validated 2026-05-14.
>
> Verbatim Mathis : *"qu'on ait plus un écran de fumée mais des données dynamiques, une web app qui marche quoi, sur laquelle on pourra partir de zéro, lancer un audit, donner nos inputs, pareil pour le gsg etc."*

## Executive Summary

### Diagnostic empirique cross-validated
3 audits parallèles indépendants ont confirmé :
- **28% feature parity vs V26 HTML** (Agent A : 11 panes, 8 absentes ou partielles)
- **12% visual DNA parity** (Agent A : Cormorant Garamond + Sunset Gold gradient + starfield + φ-spacing + glass + HSL score color tous perdus)
- **~30% canonical architecture surface** (Agent B : 251 modules · 7 pipelines · 17 artefacts ; 5/8 essential skills + FastAPI Fly.io + 5 microfrontends manquants)
- **0/10 user journeys "partir de zéro"** (Agent C : pipelines CLI-only, AddClient UI absent, GSG Studio.tsx code mort orphelin)

### Convergences (= P0 absolu)
1. **Pipeline trigger UI manquant** (A+B+C convergent)
2. **Design DNA V22 perdue** (A visceral + B essential skills missing + C UX assessment)
3. **GSG inputs E2E manquant** (A+B+C)
4. **Onboarding client UI manquant** (A+C)
5. **Reality 5 connectors stubbed** (A+B+C)
6. **Experiments + GEO panes absents** (A+B+C)

### Stratégie 2026-05-14 — Stratospheric Reconstruction
4 tiers ordonnés par dépendance + impact perception utilisateur :
1. **TIER 1 — FOUNDATIONS** (P0 blocking, ~5-8 jours) : visual DNA + backend trigger + client lifecycle
2. **TIER 2 — V26 PARITY** (P0, ~8-10 jours) : dashboard narrative + audit deep + reco lifecycle
3. **TIER 3 — MISSING SURFACES** (P1, ~7-9 jours) : Scent / Experiments / GEO / GSG fix / Reality wiring / Learning dogfood
4. **TIER 4 — ENHANCEMENTS** (P2, ~5-7 jours) : chrome + skills install + cleanup + architecture decision

**Total** : 25-34 jours solo dev pour ~70% canonical parity + design DNA restaurée + closed-loop opérationnel.

## Problem Statement

### Pourquoi le port V26→Next.js a échoué
| Erreur | Conséquence |
|---|---|
| Port admin spine, abandon visual DNA | "Ne ressemble en RIEN à V26" |
| Pipelines laissés CLI-only | Pas de "lancer un audit depuis l'UI" |
| Microfrontends collapsés pour simplifier (epic FR-1 2026-05-13) | Architecture canonique non respectée |
| FastAPI référencé mais non déployé | Backend long pipelines unrunnable depuis prod |
| Skills essential `Emil Kowalski Design` + `Impeccable` + `cro-methodology` + `vercel-microfrontends` non installés | Combo packs ne peuvent pas tourner à pleine puissance |
| GSG Brief Wizard codé puis orphelin (Studio.tsx jamais importé) | "Donner inputs GSG" cassé |
| Velocity-mode 10 sub-PRDs/jour | 0 test visuel pré-merge |

### Ce que ce MEGA-PRD remet AU CARRÉ
- AUDIT-FIRST 3 dimensions cross-validated AVANT toute action (déjà fait)
- TIER 1 blocking = restaure les 3 fondations avant tout porting features
- Mathis-side decisions D1-D4 BLOCKING avant sprint
- 1 sprint = 1 sub-PRD = 1 PR-equivalent
- Test visuel Playwright + manual validation par TIER
- Pas de claim "shipped" sans Mathis-in-loop validation

## User Stories

### US-1 — Mathis (sortir DURABLEMENT de l'écran de fumée)
*Comme founder qui a vu un écran de fumée pendant 12h post-déploiement Vercel, je veux que la webapp Next.js (a) ressemble visuellement à la V26 HTML que j'ai construite en 3 mois, (b) supporte les 10 user journeys end-to-end, (c) corresponde à l'architecture canonique que j'ai documentée dans architecture-explorer-data.js.*

**Acceptance Criteria** :
- ✓ Visual DNA V22 restored : Cormorant Garamond + Sunset Gold gradient + starfield canvas + φ-spacing + glass cards
- ✓ ≥8/10 user journeys functional end-to-end (current : 4/10)
- ✓ Feature parity vs V26 HTML ≥65% (current : 28%)
- ✓ Architecture canonical alignment ≥70% (current : 30%)

### US-2 — Consultant Growth Society (Mission Control opérationnel)
*Comme consultant CRO de Growth Society qui gère ~30 clients en parallèle, je veux pouvoir (a) onboarder un nouveau client depuis l'UI en 1 minute, (b) lancer un audit complet sur une URL en 1 clic et voir la progression, (c) reviewer les recos rich avec bbox crops + lifecycle status, (d) lancer la génération GSG d'une LP, (e) voir le réalisme via Reality Layer.*

**Acceptance Criteria** :
- ✓ AddClient → audit en ≤2 min (URL form + auto pipeline trigger)
- ✓ Live progress UI (Supabase realtime channel `public:runs`)
- ✓ Recos affichées avec FR labels + bbox crops + 3-tab + lifecycle pill
- ✓ GSG : Brief Wizard → trigger run → preview iframe LP
- ✓ Reality 5 connectors visible + credentials gate + per-client CVR

### US-3 — Mathis (architecture canonique respectée)
*Comme founder qui a documenté l'architecture canonique dans architecture-explorer-data.js (5683 lignes), je veux que le code shipped correspond à cette architecture (5 microfrontends OU décision documentée de la garder collapsée, FastAPI Fly.io OU alternative documentée, 8 essential skills installés OU justification).*

**Acceptance Criteria** :
- ✓ Décision D1 documentée (monorepo confirmé OU port 5 µfrontends)
- ✓ Décision D2 documentée (FastAPI Fly.io OU Vercel Sandbox OU Supabase Edge + queue)
- ✓ 8/8 essential skills installés OU 4 exclus avec rationale documentée
- ✓ 18 legacy modules archivés vers `_archive/2026-05-14_mega_prompt_path/`

## Functional Requirements

### TIER 1 — FOUNDATIONS (P0 blocking, ~5-8 jours)

#### sub-PRD 1 — `design-dna-v22-stratospheric-recovery` (3-4j)
Restaurer le visual DNA V22 sur tous les composants existants.

**Scope** :
- `webapp/packages/ui/src/styles.css` : import 4 typefaces via `next/font/google` (Cormorant Garamond + Playfair Display + Inter + JetBrains Mono)
- Replace `--gc-*` palette → `--night-abyss/--gold-sunset/--aurora-*/--star-*` (Alaska Boreal Night)
- Add `--sp-0` à `--sp-7` (golden ratio φ spacing)
- Add KPI value gradient `linear-gradient(135deg, #fbfaf5 0%, #e8c872 55%, #d4a945 100%)` + drop-shadow
- Add glass cards `backdrop-filter: blur(22px) saturate(160%)` + gold border `rgba(232,200,114,0.12)`
- Add `body::before` + `body::after` 4-layer parallax background
- Add starfield canvas component (4 layers + shooting stars + 1.8s fade-in)
- Add `score-color.ts` utility : `hsl(pct/100*120, 65%, 55%)` continuous gradient
- Add Tailwind/CSS easing `cubic-bezier(0.23, 1, 0.32, 1)` aura motion

**Acceptance** :
- Cormorant Garamond rendered on H1/H2 (verify devtools)
- Sunset Gold gradient visible on all KPI values
- Starfield canvas animated background visible at `/`
- φ-spacing utility classes available
- Lighthouse score ≥85 (perf budget for backdrop-filter)

#### sub-PRD 2 — `pipeline-trigger-backend` (2-3j)
Backend long pipeline trigger from UI. Bloque toutes les user journeys "partir de zéro".

**Décision D2 BLOCKING** (Mathis à trancher avant sprint) :
- D2.A FastAPI Fly.io (architecture canonique recommandée)
- D2.B Vercel Sandbox (2026 GA)
- D2.C Supabase Edge Functions + queue
- D2.D GitHub Actions polling

**Scope (D2.A path)** :
- Deploy `growthcro/api/server.py` to Fly.io (eu-central region, RGPD)
- Endpoints `/api/runs/{capture,score,recos,gsg,multi_judge,reality}` accepting `{client_slug, page_type, params}` → returns `run_id`
- Supabase `runs` table : `id, type, status, started_at, finished_at, output_path, metadata_json` + RLS write policies
- Worker daemon polling `runs.status=pending` → execute pipeline → update status + write artefacts to Supabase storage / disk
- Webhook back to webapp via Supabase realtime channel `public:runs`
- Webapp Next.js `/api/runs/*` route handlers proxying to Fly.io with auth
- UI integration : `<TriggerRunButton>` component reusable

**Acceptance** :
- `POST /api/runs/capture` from webapp → row in `runs` table status=pending
- Worker picks up → status=running → status=completed
- Realtime channel emits update to webapp
- UI shows live status pill
- Smoke test : trigger weglot/home capture from UI → see artefacts on disk in 2-5 min

#### sub-PRD 3 — `client-lifecycle-from-ui` (1-2j)
Onboarding + lifecycle CRUD complet from UI.

**Scope** :
- `POST /api/clients` route handler (admin gated) creates client row
- `<AddClientModal>` component : URL + name + business_category + panel_role (dropdown 5 roles V27)
- Sidebar CTA "+ Add client" always visible (admin only)
- `audits.status` column migration (idle/running/done/failed)
- Surface `<CreateAuditTrigger>` on every client detail page
- Surface `<CreateAuditTrigger>` from home dashboard quick-action
- `<DeleteClientModal>` with confirm (admin only)
- Lifecycle pill per audit/page : pending → capturing → scoring → enriching → done

**Acceptance** :
- Login → click "+ Add client" → fill form → submit → row in Supabase
- Click new client → "Run audit" → status pill shows progression
- Audit completes → recos visible

### TIER 2 — V26 PARITY (P0, ~8-10 jours)

#### sub-PRD 4 — `dashboard-v26-closed-loop-narrative` (3-4j)
Restaure le dashboard V26 narrative complet.

**Scope** :
- Closed-Loop coverage strip 8 KPIs (Evidence/Lifecycle/BrandDNA/DG/Funnel/Reality/GEO/Learning) per V26 lines 909-919
- 6 pillars fleet bar chart (`pillar-bars` Recharts ou SVG inline)
- Priority distribution chart (`priority-bars`)
- Business breakdown table (`business-table`)
- Page-type breakdown table
- Tabs : fleet / business / pagetype
- Critical clients grid (top P0 count)
- KPI grid header avec Cormorant Garamond italic gold gradient values

**Acceptance** :
- Visit `/` → 8-KPI strip visible
- All 6 pillars displayed with HSL color
- Tabs switch business/pagetype
- KPI values gold gradient italic Cormorant

#### sub-PRD 5 — `growth-audit-v26-deep-detail` (3-4j)
Audit detail page V26 parity.

**Scope** :
- `CRIT_NAMES_V21` 51-entry FR labels map (extracted from V26 HTML L2416-2442)
- `useViewport()` hook + dual-viewport 💻/📱 toggle
- Per-page `<ClientHeroBlock>` (brand_dna palette + voice samples)
- `<V26Panels>` per-client : brand_dna + design_grammar + evidence + lifecycle counters
- Pulsing P0 dot animation
- Sticky page-tabs (home / blog / collection / pricing / ...)
- Funnel canonical-tunnel dedup with 🌊 Tunnel tab

**Acceptance** :
- Visit `/audits/weglot/home` → recos display "Preuve sociale ATF" not "hero_05"
- Dual-viewport toggle switches desktop/mobile screenshots
- Brand DNA palette visible in client hero
- V26 panels show evidence count + lifecycle counters

#### sub-PRD 6 — `reco-lifecycle-bbox-and-evidence` (2j)
Reco card V26 deep features.

**Scope** :
- `<RecoBboxCrop>` component : canvas drawing scaled-down screenshot + red rect overlay at `bbox = [x1,y1,x2,y2]`
- 3-tab synthesis : Problème / Action / Pourquoi (replaces current single body)
- Lifecycle pill (13 states from V26 enum)
- Evidence pill linking to `evidence_ledger.json` viewer
- Hover preview : full screenshot at native resolution

**Acceptance** :
- Visit `/audits/weglot/home` → each reco shows bbox crop with red rect
- 3 tabs functional
- Lifecycle pill colored per state

### TIER 3 — MISSING SURFACES (P1, ~7-9 jours)

#### sub-PRD 7 — `scent-trail-pane-port` (2j)
Port complet du pane Scent Trail V26 (0% actuellement).

**Scope** :
- Supabase migration : `audits.scent_trail_json` JSONB column
- Migrate `data/captures/<c>/scent_trail.json` to Supabase
- New route `/scent` + sidebar nav-item
- Fleet KPI cards : total breaks · clients with break · avg break severity
- Per-client `<ScentTrailDiagram>` (ad → LP → product flow visualisation)
- Breaks list (where scent breaks down)
- Fleet table sortable

**Acceptance** : `/scent` route renders fleet KPIs + per-client diagram on selection

#### sub-PRD 8 — `experiments-v27-calculator` (2j)
Port pane Experiments V27 (0% actuellement).

**Scope** :
- New route `/experiments` + sidebar nav-item with V27 badge
- Sample-size calculator : z-test 2-sample proportion (with z_alpha + z_beta)
- Inputs : baseline CVR + MDE + alpha + power → output : sample size per arm + total runtime estimate
- Ramp-up % matrix (10% → 50% → 100%)
- Kill switches matrix (CVR drop threshold + traffic threshold)
- Active experiments list (Supabase `experiments` table — to migrate)

**Acceptance** : `/experiments` route calculates sample size correctly (verify with known z-test values)

#### sub-PRD 9 — `geo-monitor-v31-pane` (2j)
Port pane GEO Monitor V31 (0% actuellement).

**Scope** :
- Provider env vars : `OPENAI_API_KEY` + `PERPLEXITY_API_KEY` (Mathis-side)
- Supabase migration : `geo_audits` table (client_id, engine, query, response, presence_score, ts)
- Worker : run query bank against Anthropic + OpenAI + Perplexity engines per client
- New route `/geo` + sidebar nav-item with V31 badge
- Presence % per engine (last 30j)
- Query bank viewer
- Per-client per-engine drilldown

**Acceptance** : `/geo` shows weglot presence % across 3 engines for last 7 queries

#### sub-PRD 10 — `gsg-design-grammar-viewer-restore` (2j)
Fix `/gsg` qui est actuellement le mauvais feature (Décision D3).

**Décision D3 BLOCKING** :
- D3.A `/gsg` = Design Grammar viewer (V26 surface), `/gsg/handoff` = Brief Wizard (current Next.js feature)
- D3.B Keep `/gsg` = Brief Wizard, drop Design Grammar viewer

**Scope (D3.A path recommandé)** :
- Move current `/gsg` page → `/gsg/handoff`
- Rebuild `/gsg` = Design Grammar viewer per V26 L2666-2754 :
  - 7 artefacts/client : tokens.css preview + component_grammar + section_grammar + composition_rules + brand_forbidden_patterns + quality_gates
  - Live tokens.css render
  - Forbidden patterns warning UI
- Wire BriefWizard component (was orphan) at `/gsg/handoff`
- `<TriggerRunButton>` at end of Wizard → calls `/api/runs/gsg`
- Preview iframe live de l'output généré (post-completion via realtime)

**Acceptance** :
- `/gsg` shows weglot Design Grammar 7 artefacts
- `/gsg/handoff` shows Brief Wizard → submit → GSG run triggered

#### sub-PRD 11 — `reality-layer-5-connectors-wiring` (3j)
Wirer les 5 connectors live (actuellement stubbed).

**Scope** :
- 5 OAuth flows : GA4 + Meta Ads + Google Ads + Shopify + Microsoft Clarity
- Supabase `client_credentials` table (RLS strict per-client per-user)
- Credentials gate UI per connector (status pill + "Connect" CTA)
- Reality polling worker (cron 1h) → `reality_snapshots` table
- Per-client display : CVR + CPA + AOV + traffic + impressions
- Sparkline 30j per metric

**Acceptance** : Connect GA4 with test account → CVR visible on `/reality/weglot`

#### sub-PRD 12 — `learning-doctrine-dogfood-restore` (2j)
Polish on existing Learning + Doctrine routes.

**Scope** :
- 13-state lifecycle bars chart (audit → enrich → review → vote → merge → ...)
- Closed Loop diagram (mermaid rendered via `mermaid.js`)
- Growth Society dogfood card in `/doctrine` showing our own tokens applied live (Cormorant + Sunset Gold)
- Doctrine viewer : 7 pillars browsable + 54 criteria + 6 killer_rules + anti_patterns

**Acceptance** : `/doctrine` shows mermaid Closed Loop diagram + dogfood card

### TIER 4 — ENHANCEMENTS (P2, ~5-7 jours)

#### sub-PRD 13 — `global-chrome-cmdk-breadcrumbs` (2j)
Chrome global aligné V26.

**Scope** :
- Sticky header avec search bar (Cmd+K)
- Cmd+K command palette (cmdk lib or custom) : navigate to client/page/reco/setting
- 11-item sidebar avec count badges (audit count, brand_dna count, etc.)
- Breadcrumbs dynamic per route

**Acceptance** : Cmd+K opens palette + navigates to any client/page in ≤2 keystrokes

#### sub-PRD 14 — `essential-skills-install-and-wire` (1-2j)
Install les 4 essential skills manquants.

**Décision D1 BLOCKING** :
- D1.A Garder shell consolidé (recommandé) → install `vercel-microfrontends` skill juste pour future option
- D1.B Re-fédérer 5 µfrontends → install + wire

**Scope** :
- Install `vercel-microfrontends` (skill OR decision doc if D1.A)
- Install `cro-methodology` (POST-PROCESS layer)
- Install `Emil Kowalski Design Skill` (motion in `core/animations`)
- Install `Impeccable` (`core/impeccable_qa`)
- Wire into combo packs (audit_run + gsg_generation + webapp_nextjs)

**Acceptance** : `npx skills list` shows 8/8 essentials + combo packs run at full strength

#### sub-PRD 15 — `legacy-cleanup-mega-prompt-archive` (1j)
Archive les 18 legacy modules.

**Scope** :
- `git mv growthcro/gsg_lp _archive/2026-05-14_mega_prompt_path/gsg_lp` (responsable régression -28pts V26.AF)
- `git mv skills/growth-site-generator _archive/2026-05-14_mega_prompt_path/growth-site-generator` (10 modules)
- Archive `pipeline_sequential` + `brief_v15_builder`
- Archive `skills/site-capture/scripts/reality_layer/*` (duplicate of `growthcro/reality/*`)
- Update CAPABILITIES_REGISTRY + verify orphans count = 0

**Acceptance** : `python3 scripts/audit_capabilities.py` reports 0 orphans + 0 duplicates

#### sub-PRD 16 — `microfrontends-decision-doc` (1j)
Documenter Décision D1 + implementer si D1.B.

**Scope** :
- Decision doc dans `.claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md` justifiant choix D1.A ou D1.B
- Update `architecture-explorer-data.js` si D1.A pour refléter shell consolidé
- Update MANIFEST §12

**Acceptance** : Decision doc référencé dans CLAUDE.md + architecture-explorer aligned

## Non-Functional Requirements

### Doctrine immutables
- V26.AF + V3.2.1 + V3.3 doctrines intactes
- Code doctrine ≤ 800 LOC, mono-concern, 8 axes (CODE_DOCTRINE)
- Anti-patterns #1-12 respectés
- Skill cap ≤ 8/session (combo packs respectés)
- Aucun `_vNN` suffix dans nouveaux fichiers (AD-9)
- `os.environ`/`os.getenv` uniquement dans `growthcro/config.py`
- Pas de `git push --force` sans accord explicite Mathis
- Code hygiene gate `python3 scripts/lint_code_hygiene.py --staged` exit 0 avant commit

### Méthodologie anti-velocity
- **AUDIT-FIRST** : déjà fait (cette session 3-agent cross-validated)
- **Décisions BLOCKING** : D1-D4 doivent être tranchées AVANT sprint
- **1 sprint = 1 sub-PRD = 1 PR-equivalent**
- **Gate-vert obligatoire** : typecheck + lint + playwright avant commit
- **Mathis-in-loop validation manuelle** : par tier avant claim
- **Test visuel Playwright** : couvre chaque nouveau composant

### Performance
- Lighthouse Performance ≥85 (target 90)
- Largest Contentful Paint < 2.5s
- Bundle size shared chunk < 200KB
- Backdrop-filter perf budget : si Lighthouse <85 → fallback no-blur

### Sécurité
- Service_role JWT rotation déjà faite (sb_secret_... format)
- Anthropic key rotation à confirmer (Mathis P0)
- RLS Supabase strict per-org per-client per-reco
- API routes mutating gated par `requireAdmin()`
- Aucun secret en clair dans audit docs (lesson learned 2026-05-14)

### Documentation
- 1 sub-PRD ccpm-decomposé par sprint avant code
- Per-fix : commit isolé + message verbose explaining "what + why"
- BLUEPRINT v1.4 update à chaque tier complet
- MANIFEST §12 changelog par tier

## Success Criteria

### TIER 1 (foundations)
- [ ] Visual DNA V22 visible sur tous les composants
- [ ] Cormorant Garamond + Sunset Gold + starfield + φ-spacing actifs
- [ ] Pipeline trigger fonctionnel : UI → run → completion notification
- [ ] AddClient → AddAudit → result viewable in ≤5 min E2E

### TIER 2 (V26 parity)
- [ ] Dashboard 8-KPI strip + 6 pillars + priority dist + business + page-type tabs
- [ ] Reco FR labels via CRIT_NAMES_V21
- [ ] Dual-viewport toggle desktop/mobile
- [ ] Bbox screenshot crops + 3-tab synthesis + lifecycle pill

### TIER 3 (missing surfaces)
- [ ] `/scent` route functional (fleet + per-client)
- [ ] `/experiments` calculator returns correct z-test values
- [ ] `/geo` route shows 3-engine presence
- [ ] `/gsg` Design Grammar viewer + `/gsg/handoff` Brief Wizard
- [ ] Reality 5 connectors with credentials gates
- [ ] `/doctrine` Closed Loop mermaid + dogfood card

### TIER 4 (enhancements)
- [ ] Cmd+K command palette functional
- [ ] 11-sidebar items avec count badges
- [ ] 8/8 essential skills installés
- [ ] 18 legacy modules archivés
- [ ] Décision D1 documentée

### Overall
- [ ] Feature parity V26 ≥65% (current 28%)
- [ ] Visual DNA parity ≥80% (current 12%)
- [ ] Architecture canonical alignment ≥70% (current 30%)
- [ ] 9/10 user journeys functional (current 4/10)
- [ ] Mathis manual validation : "OUI ça ressemble enfin à la V26 + ça marche end-to-end"

## Constraints & Assumptions

### Décisions BLOCKING (Mathis avant tout sprint)

| # | Décision | Options | Recommandation Claude | Bloque |
|---|---|---|---|---|
| **D1** | Monorepo shell vs 5 microfrontends | D1.A garder shell consolidé / D1.B re-fédérer | D1.A (1 dev solo + ~100 clients = µfrontends overkill) | sub-PRDs 14, 16 |
| **D2** | Backend long pipeline | D2.A FastAPI Fly.io / D2.B Vercel Sandbox / D2.C Supabase Edge + queue / D2.D GitHub Actions | D2.A (architecture canonique) ou D2.C (Vercel-native, cheaper) | sub-PRDs 2, 11 |
| **D3** | `/gsg` route purpose | D3.A viewer (V26) + handoff sub-route / D3.B keep wizard | D3.A (V26 surface canonique) | sub-PRD 10 |
| **D4** | Re-enrichment doctrine V3.3 | D4.A do now ($10-15 API + 6-8h) / D4.B differ Phase C-full | D4.B (orthogonal to this MEGA-PRD) | none here, separate PRD |

### Externes (Mathis-side)
- ~30-40h Mathis cumulé sur 25-34 jours :
  - Décisions D1-D4 (~30 min)
  - Reality 5 OAuth flows + creds (~2-3h)
  - OPENAI + PERPLEXITY API keys (~5 min)
  - Anthropic key rotation (~5 min)
  - Manual validation par tier (~3 × 1h)
  - Consultant Growth Society feedback (~1h, optional Final)

### Techniques
- Claude Code Team/Enterprise (native /review + parallel agents)
- Vercel Pro (if Vercel Sandbox D2.C path)
- Fly.io (if D2.A path, ~$5/mois minimum)
- Supabase Pro (already in use)
- Playwright + Pillow + supabase-py (déjà installés)

### Internes
- main HEAD `09d91f2` (Wave 0/A/C complete + Supabase keys 2026 fix)
- 51 panel-curated clients migrated to Supabase
- 8 essential skills (4 installed, 4 to install in sub-PRD 14)
- Design DNA V22 specs in `deliverables/GrowthCRO-V26-WebApp.html` L17-100

## Out of Scope

### V1 (this MEGA-PRD)
- ❌ Re-enrichment doctrine V3.3 (= sub-PRD séparé Phase C-full)
- ❌ Multi-tenant org switching (~V2 enterprise)
- ❌ Real-time multi-user collab on same audit
- ❌ Mobile-first redesign (current desktop-first acceptable)
- ❌ Internationalization (i18n) au-delà du FR

### V2 deferred
- Multi-judge runner UI (judges currently visible read-only)
- GSG Vanilla Chat fallback (Mathis admitted "vanilla mieux que pipeline" empirically V26.AF)
- A/B test platform integration (Optimizely, VWO, etc.)
- White-label for sub-agencies

## Dependencies

### Externes (humaines)
- Mathis : ~30-40h cumulé over 25-34 jours
- Consultant Growth Society : ~1h final feedback (optional)

### Externes (techniques)
- Décision D2 backend path (Fly.io / Vercel Sandbox / Supabase Edge / GitHub Actions)
- Reality 5 OAuth providers (Catchr / Meta / GA / Shopify / Clarity)
- OPENAI + PERPLEXITY API keys

### Internes
- `growthcro/api/server.py` (FastAPI exists, needs deploy)
- `growthcro/capture/*`, `growthcro/perception/*`, `growthcro/scoring/*`, `growthcro/recos/*` (all CLI-functional)
- `moteur_gsg/*` (functional CLI)
- `moteur_multi_judge/*` (functional CLI)
- `V26 HTML L1-3666` source de vérité visuelle

### Sequencing
```
PRE-SPRINT (Mathis, ~30 min)
  D1 + D2 + D3 + D4 décisions documentées
                  │
TIER 1 (P0, 5-8 jours)
  ├── 1. Design DNA recovery
  ├── 2. Pipeline trigger backend (depends D2)
  └── 3. Client lifecycle from UI (depends #2)
                  │
TIER 2 (P0, 8-10 jours)
  ├── 4. Dashboard V26 (depends #1)
  ├── 5. Growth Audit deep (depends #1, #6)
  └── 6. Reco lifecycle + bbox (depends #1)
                  │
TIER 3 (P1, 7-9 jours)
  ├── 7. Scent Trail
  ├── 8. Experiments calculator
  ├── 9. GEO Monitor
  ├── 10. GSG /gsg fix (depends D3)
  ├── 11. Reality 5 connectors (depends #2)
  └── 12. Learning dogfood
                  │
TIER 4 (P2, 5-7 jours)
  ├── 13. Global chrome
  ├── 14. Essential skills (depends D1)
  ├── 15. Legacy cleanup
  └── 16. Microfrontends decision (depends D1)
                  │
CLOSE
  Mathis manual validation par tier
  BLUEPRINT v1.4
  CONTINUATION_PLAN_2026-05-15+
```

**Total wall-clock** : 25-34 jours sur 5-7 semaines solo dev.

## Plan d'exécution session-par-session

### Session 1 (NEXT) — Décisions + Sprint setup
1. Mathis tranche D1-D4 (30 min)
2. ccpm decompose chaque sub-PRD prioritaire (1, 2, 3) en epic + issues
3. Setup branches : `epic/tier-1-foundations`
4. Sub-PRD 1 design-dna démarre (sprint 1)

### Session 2-3 — TIER 1 execution (5-8 jours)
1. Sprint 1 design-dna (per-component touches)
2. Sprint 2 pipeline-trigger-backend (depends D2)
3. Sprint 3 client-lifecycle-from-ui

### Session 4-6 — TIER 2 execution (8-10 jours)

### Session 7-9 — TIER 3 execution (7-9 jours)

### Session 10-11 — TIER 4 + close (5-7 jours)

### Final session — Mathis validation + BLUEPRINT v1.4 + CONTINUATION_PLAN

## Trigger phrase post-decisions

```
Décisions D1-D4 tranchées. Lis :
1. .claude/docs/state/WEBAPP_RECONSTRUCTION_PLAN_2026-05-14.md
2. .claude/prds/webapp-stratospheric-reconstruction-2026-05.md
3. Décisions documentées dans .claude/docs/architecture/DECISIONS_2026-05-14.md

Lance ccpm decompose sub-PRD 1 (design-dna-v22-stratospheric-recovery)
puis sprint 1 démarre.
```

---

## Skills à exploiter (chaque skill explicitement intégré)

| Skill | Sub-PRDs | Output attendu |
|---|---|---|
| `Emil Kowalski Design Skill` (à installer) | 1, 4, 5, 6 | Motion + transitions premium |
| `Impeccable` (à installer) | 1, 4-12 | QA polish |
| `cro-methodology` (à installer) | 5, 6 | POST-PROCESS layer recos |
| `vercel-microfrontends` (à installer si D1.B) | 16 | µfrontends federation |
| `frontend-design` | 1, 4-12 | Premium frontend per-fix |
| `vercel:nextjs` | 2, 3, 10 | App Router expert |
| `vercel:ai-architect` | 2 | FastAPI Fly.io path |
| `vercel:performance-optimizer` | 1, 4-6 | Lighthouse budget |
| `vercel:vercel-functions` | 2 (D2.C path) | Edge functions + cron |
| `vercel:vercel-sandbox` | 2 (D2.B path) | Sandbox 2026 alternative |
| `webapp-testing` (Playwright) | All tiers gate-vert | E2E per sub-PRD |
| `design:design-critique` | 1, 4-12 | Critique visuelle V22 |
| `design:accessibility-review` | All tiers | WCAG AA throughout |
| `design:design-system` | 1 | V22 system formalized |
| `Superpowers` (TDD + plans + parallel agents) | All tiers | Multi-step + tests |
| `GStack` | 5, 6, 10 | QA persona + design persona |
| `ccpm` | All sub-PRDs | PRD → epic → issues → sync |
| `product-management:write-spec` | Pre-sprint each | Sub-PRD detail |
| `product-management:sprint-planning` | Pre-tier | Capacity plan |
| `product-management:roadmap-update` | Tier transitions | Roadmap visibility |
| `Trail of Bits (codeql, semgrep, etc.)` | Per tier | Security audit |
| `data:write-query` + `data:validate-data` | 2, 3, 7-11 | SQL migrations + QA |
| `simplify` | Per commit post-fix | Reuse + quality |

---

## Notes critiques

1. **Méthodologie AUDIT-FIRST cross-validated** = 3 agents A/B/C indépendants ont convergé sur les mêmes findings critiques. Confiance haute.
2. **Décisions D1-D4 BLOCKING** = pas un cm de code avant que Mathis tranche.
3. **Visual DNA d'abord (sub-PRD 1)** = Mathis "sentira immédiatement V26 revenue" même avant les features.
4. **Pipeline trigger (sub-PRD 2)** = critique pour sortir de l'écran de fumée durablement.
5. **Mathis-in-loop validation par tier** = obligatoire pré-tier-suivant.
6. **Pas de hubris velocity** = 0 commit sub-PRD sans gate-vert + Playwright test + Mathis validation.
7. **Architecture canonique respectée** = architecture-explorer-data.js est source de vérité, on l'aligne ou on documente la divergence.

---

**Première action post-publication** : Mathis tranche D1-D4. Puis ccpm decompose sub-PRD 1 et sprint 1 démarre.
