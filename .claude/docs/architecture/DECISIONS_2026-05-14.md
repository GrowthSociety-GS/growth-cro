# Architecture Decisions — 2026-05-14 (post 3-agent audit + MEGA-PRD)

> Décisions tranchées par Mathis 2026-05-14T16:30Z pour débloquer le sprint
> Stratospheric Reconstruction. Chaque décision = section verrouillée
> (rationale + alternatives examinées + impact sub-PRDs).

## D1 — Architecture topologie : monorepo shell ✅

**Décision** : **D1.A — garder le shell consolidé**. Pas de re-fédération en 5 microfrontends.

**Rationale** :
- 1 dev solo (Mathis) + ~100 clients = 6 projets Vercel séparés = overkill
- Epic `webapp-consolidate-architecture` (FR-1) terminé 2026-05-13 a déjà consolidé les 5 µfrontends en 1 shell `@growthcro/shell` v0.28.0
- 1 deploy Vercel + 1 typecheck + 1 build au lieu de 6
- Decision aligned avec spec FR-1 et MANIFEST §12 2026-05-13

**Alternatives rejetées** :
- D1.B re-fédérer 5 µfrontends via `vercel-microfrontends` — overengineering pour solo dev

**Impact sub-PRDs** :
- sub-PRD 14 : `vercel-microfrontends` skill **PAS installé** (rationale documentée)
- sub-PRD 16 : decision doc = ce fichier (✅ fait)
- Update `architecture-explorer-data.js` pour refléter shell consolidé (= un task de sub-PRD 16)

## D2 — Backend long-pipeline : Phase A local + Phase B Fly.io ✅

**Décision** : **D2.C-Phase-A** maintenant — Supabase Edge Functions + queue + **worker local Python**. **Phase B** plus tard quand scaling : migrate worker vers Fly.io tiny VM.

**Rationale** :
- Free tier Supabase Edge Functions (500K invocations/mois) couvre largement notre usage estimé (~1500 runs/mois)
- Worker local réutilise les pipelines CLI existants (`growthcro/capture/*.py`, `moteur_gsg/*`, etc.) — pas de rewrite
- $0 coût ajouté pour TIER 1
- Phase B Fly.io migration = sub-PRD séparé quand prêt (architecture canonique aligned)

**Architecture Phase A** :
```
Webapp UI
  ↓ POST /api/runs/{capture,score,recos,gsg}
Supabase Edge Function
  ↓ insert into runs table (status=pending)
Supabase `runs` queue
  ↑ poll every 30s
Local Python worker (growthcro/worker/daemon.py — TO BUILD)
  ↓ executes existing CLI pipeline
  ↓ writes artefacts to Supabase Storage
  ↓ update runs.status=completed
Supabase Realtime channel public:runs
  ↓ webapp UI receives notification
Webapp UI live status pill
```

**Alternatives rejetées** :
- D2.A FastAPI Fly.io immediate — ~$5/mo + setup overhead, can defer to Phase B
- D2.B Vercel Sandbox — pas mature, exploration plus tard
- D2.D GitHub Actions polling — works but 5-min cron lag pas idéal pour UX

**Impact sub-PRDs** :
- sub-PRD 2 `pipeline-trigger-backend` scope : Edge Functions API + Supabase `runs` table migration + worker daemon `growthcro/worker/daemon.py` + Supabase Realtime channel
- sub-PRD 11 `reality-layer-5-connectors-wiring` : worker pickup pour OAuth flows aussi
- Phase B Fly.io migration = nouveau sub-PRD `worker-fly-io-migration` (V2)

## D3 — Route `/gsg` : Design Grammar viewer + sub-route handoff ✅

**Décision** : **D3.A** — `/gsg` = Design Grammar viewer (V26 surface). `/gsg/handoff` = Brief Wizard (current Next.js feature relocated).

**Rationale** :
- V26 HTML L2666-2754 expose `/gsg` = Design Grammar viewer 7 artefacts/client (tokens.css + component_grammar + section_grammar + composition_rules + brand_forbidden_patterns + quality_gates + design tokens)
- Surface canonique selon `architecture-explorer-data.js`
- Current Next.js `/gsg` = orphan Brief Wizard (Studio.tsx code mort) — relocate plutôt que delete
- 2 features distinctes, 2 routes distinctes

**Alternatives rejetées** :
- D3.B garder `/gsg` = Brief Wizard, drop Design Grammar viewer — perd la surface canonique V26

**Impact sub-PRDs** :
- sub-PRD 10 `gsg-design-grammar-viewer-restore` : full scope (move + rebuild)
- BriefWizard component wired at `/gsg/handoff` après move
- `<TriggerRunButton>` connecté à `/api/runs/gsg` (depends sub-PRD 2)
- Preview iframe live de l'output généré via Supabase Realtime

## D4 — Re-enrichment doctrine V3.3 : différé Phase C-full ✅

**Décision** : **D4.B** — différer la re-enrichment campaign. Pas dans ce MEGA-PRD.

**Rationale** :
- 69 doctrine_proposals en attente review Mathis depuis Sprint B V29 (2026-05-04) — bloquant
- Re-enrichment avant review = perte de la trace V3.2.1 vs V3.3
- Coût $10-15 API + 6-8h non blocant pour TIER 1-4
- Wave C.1-bis dual-schema merge (recos_v13_final + recos_enriched) couvre déjà 81% rich text + 71% fresh before/after/why

**Séquencement recommandé Phase C-full (V2, séparé)** :
1. Mathis review 69 doctrine_proposals (~30 min review + 1h doctrine-keeper)
2. Lock V3.3 doctrine
3. Re-run reco-enricher sur 56 panel curated
4. Migrate fresh via existing `migrate_disk_to_supabase.py`
5. Archive V13/V21 legacy files per AD-9

**Impact sub-PRDs** : 
- Aucun sub-PRD de ce MEGA-PRD ne dépend de D4
- Nouveau PRD séparé `phase-c-full-v3.3-re-enrichment` à créer post-TIER 1-4

## Mathis-side actions résiduelles (parallel to sprint)

| # | Action | Effort | Quand | Bloque sub-PRD |
|---|---|---|---|---|
| 1 | 🔴 Rotater Anthropic API key | 5 min | ASAP | none here, security |
| 2 | OPENAI_API_KEY + PERPLEXITY_API_KEY | 5 min | Avant sub-PRD 9 | 9 GEO |
| 3 | OAuth creds Reality 5 connectors (Catchr/Meta/GA/Shopify/Clarity) | 2-3h | Avant sub-PRD 11 | 11 |
| 4 | Confirmer push permissions (si force-push pour legacy cleanup) | — | Avant sub-PRD 15 | 15 (probably no force-push needed) |

## Sequencing post-decisions

```
NOW (this session)
  D1-D4 documented ✅
  Epic folder created
  Sub-PRD 1 decomposed into tasks
  Sprint 1 starts
              │
SPRINT 1 (TIER 1 #1, 3-4d)
  design-dna-v22-stratospheric-recovery
              │
SPRINT 2 (TIER 1 #2, 2-3d)
  pipeline-trigger-backend (Phase A)
              │
SPRINT 3 (TIER 1 #3, 1-2d)
  client-lifecycle-from-ui
              │
  *** Mathis manual validation TIER 1 ***
              │
SPRINT 4-6 (TIER 2, 8-10d)
SPRINT 7-12 (TIER 3, 7-9d)
SPRINT 13-16 (TIER 4, 5-7d)
              │
CLOSE : BLUEPRINT v1.4 + MANIFEST §12 + CONTINUATION_PLAN
```

## Cross-references

- MEGA-PRD : [`webapp-stratospheric-reconstruction-2026-05`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)
- Reconstruction plan : [`WEBAPP_RECONSTRUCTION_PLAN_2026-05-14`](../state/WEBAPP_RECONSTRUCTION_PLAN_2026-05-14.md)
- 3-agent audit : `V26_VS_NEXTJS_DIFF_2026-05-14.md` + `ARCHITECTURE_CANONICAL_INVENTORY_2026-05-14.md` + `USER_JOURNEYS_AUDIT_2026-05-14.md`

---

**Décisions verrouillées 2026-05-14. Sprint 1 démarre.**
