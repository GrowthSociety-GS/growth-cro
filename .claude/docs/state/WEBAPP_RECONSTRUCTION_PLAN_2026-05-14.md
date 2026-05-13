# Webapp Reconstruction Plan — cross-validated 3-agent synthesis (2026-05-14)

> **Source de vérité** pour le chantier de reconstruction de la webapp Next.js
> vers la vision canonique architecturée par Mathis et incarnée par la V26
> static HTML.
>
> **3 audits cross-validated** : V26-vs-Next.js (diff parity) + architecture-explorer-data.js (canonical inventory) + user-journeys end-to-end (functional reality).
>
> **Position Mathis** (verbatim 2026-05-14) :
> *"Pourquoi notre webapp est nulle, buggée, n'affiche pas les bonnes infos ou que partiellement ? Et surtout ne ressemble en RIEN à la webapp version html que j'ai passé 3 mois à dev et construire avant de deployer sur vercel ?"*
> *"Qu'on ait plus un écran de fumée mais des données dynamiques, une web app qui marche quoi, sur laquelle on pourra partir de zéro, lancer un audit, donner nos inputs, pareil pour le gsg etc."*

## 0. TL;DR brutal

La webapp Next.js actuellement déployée sur `growth-cro.vercel.app` est un **viewer 30% du produit canonique**, sur **12% du visual DNA V26**, avec **0/10 user journeys "partir-de-zéro" fonctionnels**. Les pipelines (capture, score, reco-enrich, GSG) sont **CLI-only** — la webapp affiche les résultats sur disque, elle ne lance rien.

**Le plan** : 4 tiers, 16 sub-PRDs, ~25-34 jours solo dev pour atteindre **65-75% de parité canonique + design DNA restauré + closed-loop opérationnel**.

**Premier sprint blocant (TIER 1)** : 5-8 jours = (a) design DNA V22 Stratospheric Observatory restauré + (b) pipeline trigger backend (FastAPI Fly.io ou alternative) + (c) client lifecycle from UI. Sans ces 3, la webapp reste un écran de fumée même si on porte 100 features.

## 1. Findings cross-validated par agent

### Agent A — V26 HTML ↔ Next.js feature parity diff
**Source** : [`V26_VS_NEXTJS_DIFF_2026-05-14.md`](V26_VS_NEXTJS_DIFF_2026-05-14.md)

| Métrique | Valeur |
|---|---|
| Coverage features | **28%** |
| Coverage visual DNA | **12%** |
| Panes V26 totalement absents | **3/11** (Scent Trail · Experiments V27 · GEO V31) |
| Panes V26 partiels | **5/11** |
| Panes V26 portés ~complet | **3/11** |
| Recommended sprint plan | 7 sprints A1-A7, 18-22 jours, target 65% |

**Top design DNA perdu** :
- Cormorant Garamond italic editorial serif (display)
- Sunset Gold KPI gradient `linear-gradient(135deg, #fbfaf5 0%, #e8c872 55%, #d4a945 100%)`
- Glass cards `backdrop-filter: blur(22px) saturate(160%)` + gold-tinted borders
- Continuous HSL score color `hsl(pct/100*120, 65%, 55%)`
- Multi-layer parallax starfield canvas (4 layers + shooting stars + 1.8s fade-in)
- Golden-ratio φ≈1.618 modular spacing (`--sp-0` à `--sp-7`)
- Growth Society dogfood card in Doctrine (we eat our own tokens)

**Top features absentes** :
1. Dashboard V26 Closed-Loop coverage strip (8 KPI : Evidence/Lifecycle/BrandDNA/DG/Funnel/Reality/GEO/Learning)
2. Scent Trail pane (0% port — fleet KPI + per-client diagram + breaks list + fleet table)
3. Experiments V27 sample-size calculator (z-test + ramp-up + kill switches)
4. GEO Monitor V31+ (3 engines presence% + query bank viewer)
5. Per-reco bbox screenshot crops + 3-tab synthesis (Problème/Action/Pourquoi) + lifecycle pill + evidence pill
6. CRIT_NAMES_V21 (51-entry FR map) — recos affichent `hero_05` brut au lieu de `"Preuve sociale ATF"`
7. Canonical-tunnel dedup (🌊 Tunnel tab quand une LP funnels dans un tunnel canonique)
8. Dual-viewport 💻/📱 toggle

### Agent B — Architecture canonical inventory
**Source** : [`ARCHITECTURE_CANONICAL_INVENTORY_2026-05-14.md`](ARCHITECTURE_CANONICAL_INVENTORY_2026-05-14.md)

| Métrique | Valeur |
|---|---|
| Modules totaux | **251** (233 actifs · 18 legacy) |
| Packages | **25** |
| Pipelines canoniques | **7** (audit · gsg · multi_judge · reality_loop · webapp_meta · webapp_v27 · webapp_v28) |
| Data artefacts canoniques | **17** (12 per-page captures + 1 clients DB + 1 V29 proposals + 2 V27 deliverables + 1 pipeline_runs) |
| Skills essentials | **8** (4 installés, **4 manquants**) |
| Skills on-demand | 6 |
| Combo packs | 3 (disjoints) |
| Anti-cacophonie rules | 8 |
| Mermaid views | 6 |
| Dataset bundle | 11.73 MB · 56 clients · 185 pages · 3045 recos LP · 170 step-recos · 8347 evidence items |

**Top 5 gaps architecture-as-designed vs Next.js-shipped** :
1. **5 microfrontends collapsés en 1 shell** — Architecture v28 designs `shell` (3000) + `audit-app` (3001) + `reco-app` (3002) + `gsg-studio` (3003) + `reality-monitor` (3004) + `learning-lab` (3005) fédérés via `vercel-microfrontends`. Webapp ships single `@growthcro/shell` v0.28.0. Le skill `vercel-microfrontends` **n'est pas installé**.
2. **Pas de FastAPI sur Fly.io** — Architecture explicitement rejette Vercel Edge pour l'API (Playwright + LLM scoring excèdent 30s edge limit) et spécifie `NEXT_PUBLIC_API_BASE_URL → Fly.io`. Webapp ships route handlers Next.js seulement → long pipelines unrunnable depuis prod.
3. **6 stages pipeline sans UI** — `evidence_ledger.json` (per-criterion provenance), `_briefs_v2/*` (GSG briefs), `multi_judge.json` (judges runs), `experiments/*`, V30 Bayesian proposals, `client_intent.json`.
4. **4/8 essential skills manquants** — `vercel-microfrontends` + `cro-methodology` (POST-PROCESS layer recos) + `Emil Kowalski Design Skill` (motion in `core/animations`) + `Impeccable` (`core/impeccable_qa` polish).
5. **18 legacy modules sur disque** — `growthcro/gsg_lp/*` (mega-prompt path responsable régression -28pts V26.AF) + `skills/growth-site-generator/*` 10 modules superseded + `pipeline_sequential` + `brief_v15_builder` + Reality Layer dupliqué (canonical `growthcro/reality/*` 10 modules + legacy `skills/site-capture/scripts/reality_layer/*` 7 modules).

### Agent C — User journeys end-to-end functional audit
**Source** : [`USER_JOURNEYS_AUDIT_2026-05-14.md`](USER_JOURNEYS_AUDIT_2026-05-14.md)

| Journey | Status |
|---|---|
| 1. Onboarder nouveau client | ❌ 0% (no POST /api/clients, no AddClient UI) |
| 2. Lancer un audit sur client existant | ❌ 0% (POST /api/audits creates empty row, no pipeline trigger) |
| 3. Voir audit complet d'une page | ⚠️ 50% (rich recos OK post-C.1-bis, screenshots OK, mais multi-judge + lifecycle + evidence pills missing) |
| 4. Inputs GSG : générer LP | ❌ 10% (BriefWizard exists mais Studio.tsx **code mort** non importé par `/gsg/page.tsx`) |
| 5. Reality Layer — CVR réels | ❌ 5% (placeholder UI, 5 connectors stubbed, no credentials gate) |
| 6. Doctrine — 7 piliers + 54 critères | ⚠️ 40% (partial viewer) |
| 7. Learning — review proposals | ⚠️ 60% (vote queue OK, KPI grid OK post-C.4 router.refresh) |
| 8. Settings — team + account + usage | ⚠️ 40% (tabs OK, password change untested) |
| 9. GEO Monitor multi-engine | ❌ 0% (route doesn't exist) |
| 10. Experiments A/B tracking | ❌ 0% (route doesn't exist) |

**Top 3 blockers** :
1. Pas de `POST /api/clients` ni AddClient UI → onboarding impossible from UI
2. Pipeline trigger zero-wired → tous les `growthcro/*.py` + `moteur_gsg/*.py` CLI-only. FastAPI référencé dans `.env.example` mais **non déployé**. Commentaire `lib/gsg-api.ts` : *"backend deferred V2"*
3. GSG génère JSON brief seulement, pas de LP. BriefWizard component existe mais orphelin (Studio.tsx non importé)

## 2. Convergences cross-agent (= P0 absolu)

| Finding | Agents convergents | Pourquoi P0 |
|---|---|---|
| **Pipeline trigger UI manquant** | A (no "Run audit" CTA) + B (no FastAPI Fly.io) + C (CLI-only) | Sans ça, "partir de zéro → audit" impossible — la promesse produit |
| **Design DNA V22 perdue** | A (visceral pain Mathis) + B (Emil Kowalski Design + Impeccable skills not installed) | Sans ça, "ne ressemble en RIEN à V26" — la promesse visuelle |
| **GSG inputs E2E manquant** | A (/gsg différent feature) + B (gsg-studio placeholder dans architecture) + C (BriefWizard mort + Studio.tsx orphelin) | Sans ça, "donner inputs GSG" impossible |
| **Onboarding client UI manquant** | A (V26 had startAudit() flow in `pane-audit`) + C (no AddClient anywhere) | Bloque tout depuis sign-up |
| **Reality 5 connectors stubbed** | A (UI placeholder seulement) + B (5 connectors canoniques designed) + C (5% functional) | Bloque la mesure closed-loop |
| **Experiments + GEO panes absents** | A (0% port) + B (panes designed) + C (routes missing) | Bloque l'apprentissage end-to-end |

## 3. La VRAIE webapp canonique (verbatim Mathis + architecture)

D'après l'inventory B + le V26 HTML, le produit cible est :

> **Mission Control of a 6-stage closed-loop CRO consultancy engine** pour les ~100 clients de Growth Society.
>
> **Flow** : Onboard → Audit (7 stages, 17 artefacts/page) → Generate LPs (GSG 13-stage, 5 modes, 8K prompt guard) → QA (multi_judge 70/30 + killer veto) → Measure (6 Reality connectors → Experiment Engine) → Learn (dual-track V29 audit-based + V30 Bayesian doctrine evolution feeding back into audit)
>
> **Doctrine V3.2.1→V3.3** est upstream de tout.
>
> **Topologie** : 5 deep microfrontends + FastAPI on Fly.io running 5-min batches + Supabase EU pour persistence + realtime channel `public:runs` + 11 panes elevated from V27 HTML.
>
> **As-shipped** : ~30% de la surface canonique. Single shell. Pas de Fly.io backend. Placeholder gsg-studio/reality-monitor/learning-lab. Pas d'evidence/experiments/judges/V30 UIs. Legacy mega-prompt path encore sur disk. 4/8 essential skills uninstalled.

## 4. Décisions architecturales à valider avec Mathis avant tout sprint

Ces choix conditionnent le scope des sub-PRDs. Le ccpm waitera ces validations.

### Décision D1 — Monorepo shell vs 5 microfrontends ?
- **Option D1.A** (recommandé Claude) : **Garder le shell consolidé**. L'epic `webapp-consolidate-architecture` (FR-1 du master `webapp-full-buildout`, terminée 2026-05-13) a déjà consolidé les 5 microfrontends en 1 shell pour 1 dev solo + ~100 clients. Argument : 6 projets Vercel = overkill. → garder cette décision, MAJ architecture-explorer-data pour refléter.
- **Option D1.B** : Re-fédérer les 5 microfrontends per architecture canonique. Install skill `vercel-microfrontends`. Plus complexe mais aligné avec la vision originale.

### Décision D2 — Backend long-pipeline : où le mettre ?
- **Option D2.A** : **FastAPI sur Fly.io** (architecture canonique). Architecture a explicitement rejeté Vercel Edge. Coût ~$5/mois minimum.
- **Option D2.B** : **Supabase Edge Functions + queue table** (alternative Vercel-native). Limit 60s par function — pas suffisant pour Playwright capture (peut prendre 2-5 min).
- **Option D2.C** : **Vercel Cron + Vercel Sandbox** (nouveau, 2026). Coût minimal. Cold-start moins idéal. À explorer.
- **Option D2.D** : **GitHub Actions on push to runs queue** (poor man's worker). Cron 5min polling. Pas idéal mais zero infra cost.

### Décision D3 — `/gsg` route : Design Grammar viewer ou Brief Wizard ?
- V26 `/gsg` = Design Grammar viewer (7 artefacts per client : tokens.css, component_grammar, brand_forbidden_patterns, quality_gates, etc.)
- Next.js `/gsg` = Brief Wizard for FastAPI service (different feature)
- **Recommandation** : `/gsg` = Design Grammar viewer (V26 surface) + `/gsg/handoff` = Brief Wizard. Deux features distinctes, deux routes.

### Décision D4 — Re-enrichment doctrine V3.3 quand ?
- 69 doctrine_proposals en attente review depuis Sprint B V29 (2026-05-04)
- Si on re-enrichit avant review, on perd la trace V3.2.1 vs V3.3
- **Recommandation** : (a) Mathis review 69 proposals → V3.3 lock (~30 min review + 1h doctrine-keeper), (b) re-run reco-enricher sur 56 panel curated, (c) migrate fresh, (d) archive V13/V21 legacy files per AD-9
- Coût : ~$10-15 API + 6-8h
- Différé Phase C-full séparée (NOT in this MEGA-PRD)

## 5. MEGA-PRD — `webapp-stratospheric-reconstruction-2026-05`

> Voir [`webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md) pour le PRD complet.

Synthèse : **4 tiers, 16 sub-PRDs**, ~25-34 jours solo dev.

### TIER 1 — FOUNDATIONS (P0 blocking, 5-8j) — "Stop the bleeding"
1. **`design-dna-v22-stratospheric-recovery`** (3-4j) — typo Cormorant + palette Alaska + starfield canvas + φ-spacing + glass cards + HSL score + KPI gold gradient. Touche tous les composants → fait baseline.
2. **`pipeline-trigger-backend`** (2-3j) — Décision D2 trancée (option A Fly.io recommandé). Endpoints `/api/runs/{capture,score,recos,gsg}` + Supabase `runs` queue + worker daemon polling. Webhook back to webapp when done.
3. **`client-lifecycle-from-ui`** (1-2j) — `POST /api/clients` + `AddClientModal` + sidebar CTA + `audits.status` column (idle/running/done/failed) + surface `CreateAuditTrigger` partout.

### TIER 2 — V26 FEATURE PARITY (P0, 8-10j) — "Make it feel like V26"
4. **`dashboard-v26-closed-loop-narrative`** (3-4j) — Closed-Loop coverage strip 8 KPIs + 6 pillars fleet bar chart + priority distribution chart + business breakdown table + page-type breakdown table + critical clients grid.
5. **`growth-audit-v26-deep-detail`** (3-4j) — CRIT_NAMES_V21 51-entry FR map + dual-viewport 💻/📱 toggle + per-page client-hero block + v26-panels per-client (brand_dna+design_grammar+evidence+lifecycle) + pulsing P0 dot animation.
6. **`reco-lifecycle-bbox-and-evidence`** (2j) — bbox screenshot crops (canvas + red rect overlay) + 3-tab synthesis (Problème/Action/Pourquoi) + lifecycle pill (13 states) + evidence pill (link to evidence_ledger).

### TIER 3 — MISSING SURFACES (P1, 7-9j) — "Complete the loop"
7. **`scent-trail-pane-port`** (2j) — fleet KPI + per-client diagram + breaks list + fleet table. New route `/scent` + Supabase `scent_trail_json` migration.
8. **`experiments-v27-calculator`** (2j) — sample-size calculator (z-test) + ramp-up % + kill switches matrix. New route `/experiments`.
9. **`geo-monitor-v31-pane`** (2j) — Anthropic/OpenAI/Perplexity engines + presence % per engine + query bank viewer. New route `/geo` + Supabase `geo_audit_json` migration.
10. **`gsg-design-grammar-viewer-restore`** (2j) — Move current `/gsg` → `/gsg/handoff`. Rebuild `/gsg` = Design Grammar viewer (7 artefacts/client).
11. **`reality-layer-5-connectors-wiring`** (3j) — GA4/Meta/Google/Shopify/Clarity OAuth flows + credentials gate UI + per-client CVR+CPA+AOV display. Env vars Catchr-fed.
12. **`learning-doctrine-dogfood-restore`** (2j) — 13-state lifecycle bars + Closed Loop diagram (mermaid render) + Growth Society dogfood card.

### TIER 4 — ENHANCEMENTS (P2, 5-7j) — "Polish + alignment"
13. **`global-chrome-cmdk-breadcrumbs`** (2j) — sticky header + Cmd+K command palette + 11-item sidebar with count badges + breadcrumbs dynamic.
14. **`essential-skills-install-and-wire`** (1-2j) — install `vercel-microfrontends` (Décision D1) + `cro-methodology` + `Emil Kowalski Design Skill` (motion) + `Impeccable` (QA).
15. **`legacy-cleanup-mega-prompt-archive`** (1j) — archive 18 legacy modules → `_archive/2026-05-14_mega_prompt_path/`.
16. **`microfrontends-decision-doc`** (1j) — Décision D1 doc + implementation if option D1.B selected.

## 6. Sequencing & dependencies

```
TIER 1 (P0 blocking) — first 5-8 days
  ├── 1. Design DNA recovery (independent, touches all components)
  ├── 2. Pipeline trigger backend (independent backend work)
  └── 3. Client lifecycle from UI (depends on #2 for triggering)

TIER 2 (P0 feature parity) — next 8-10 days
  ├── 4. Dashboard V26 (depends on #1 for styling)
  ├── 5. Growth Audit deep (depends on #1 + #6 for bbox crops)
  └── 6. Reco lifecycle + bbox (depends on #1)

TIER 3 (P1 missing surfaces) — next 7-9 days
  ├── 7. Scent Trail (independent, new route)
  ├── 8. Experiments (independent, new route)
  ├── 9. GEO Monitor (independent, new route)
  ├── 10. GSG Design Grammar viewer (depends on D3 decision)
  ├── 11. Reality 5 connectors (depends on D2 for backend triggers)
  └── 12. Learning dogfood (independent, polish on existing)

TIER 4 (P2 enhancements) — final 5-7 days
  ├── 13. Global chrome (touches all routes, do near end)
  ├── 14. Essential skills install (independent)
  ├── 15. Legacy cleanup (independent)
  └── 16. Microfrontends decision (depends on D1)

Total: 25-34 days solo dev for ~70% canonical parity
```

## 7. Mathis-side actions (before any sprint starts)

| # | Action | Effort | Pourquoi blocking |
|---|---|---|---|
| 1 | Trancher Décision D1 (monorepo vs 5 µfrontends) | 5 min | Conditionne sub-PRD 16 |
| 2 | Trancher Décision D2 (FastAPI Fly.io vs Vercel Sandbox vs Supabase Edge) | 15 min | Conditionne sub-PRD 2 (entire backend) |
| 3 | Trancher Décision D3 (`/gsg` = viewer ou wizard) | 2 min | Conditionne sub-PRD 10 |
| 4 | Differ ou Acter Décision D4 (re-enrichment V3.3) | 10 min | Si differred → archive sub-PRD pour Phase C-full plus tard |
| 5 | Provider creds Reality connectors (Catchr/Meta/GA/Shopify/Clarity) | ? | Blocking sub-PRD 11 |
| 6 | Provider OPENAI_API_KEY + PERPLEXITY_API_KEY | 2 min | Blocking sub-PRD 9 |
| 7 | Rotate Anthropic API key (still pas rotée selon toi) | 5 min | Sécurité, pas blocking pipeline mais à faire |
| 8 | Confirm push permission for force-push si rebase deeper history needed | — | Blocking si on veut purger pwd from 52ed96e |

## 8. Méthodologie anti-velocity (rappel doctrine)

- ✅ AUDIT-FIRST avec 3 dimensions cross-validated (= cette session)
- ✅ Cross-validation : 6 convergences entre A/B/C
- ✅ Sub-PRDs structured par TIER avec dependencies explicit
- ✅ Mathis-side decisions documented and BLOCKING before code
- ✅ ccpm /epic decompose pour chaque sub-PRD avant sprint
- ✅ 1 sprint = 1 PR-equivalent, gate-vert avant next
- ✅ Test visuel Playwright + manual validation par tier
- ❌ Velocity-mode interdit (10 PRDs/jour = écran de fumée)

## 9. Cross-references

- Master MEGA-PRD : [`webapp-stratospheric-reconstruction-2026-05`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)
- Agent A diff report : [`V26_VS_NEXTJS_DIFF_2026-05-14.md`](V26_VS_NEXTJS_DIFF_2026-05-14.md)
- Agent B inventory : [`ARCHITECTURE_CANONICAL_INVENTORY_2026-05-14.md`](ARCHITECTURE_CANONICAL_INVENTORY_2026-05-14.md)
- Agent C journeys : [`USER_JOURNEYS_AUDIT_2026-05-14.md`](USER_JOURNEYS_AUDIT_2026-05-14.md)
- V26 HTML reference : `deliverables/GrowthCRO-V26-WebApp.html` (3666 lines)
- Architecture canonical data : `deliverables/architecture-explorer-data.js` (5683 lines)
- Architecture viewer : `deliverables/architecture-explorer.html`

---

**État final** : 3 audits cross-validated complete. Décisions D1-D4 en attente Mathis. Sub-PRDs structurés, ccpm prêt à decompose. **Pas un cm de code avant que Mathis tranche D1-D4.**
