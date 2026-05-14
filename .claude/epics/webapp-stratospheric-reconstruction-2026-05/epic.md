---
name: webapp-stratospheric-reconstruction-2026-05
status: in-progress
created: 2026-05-13T17:12:51Z
updated: 2026-05-14T13:37:58Z
progress: 13%
prd: .claude/prds/webapp-stratospheric-reconstruction-2026-05.md
github: (will be set on sync)
---

# Epic: webapp-stratospheric-reconstruction-2026-05

## Overview

Reconstruction systémique de la webapp Next.js post-audit-first 3-agent cross-validated. Restaure le visual DNA V22 Stratospheric Observatory perdu lors du port V26→Next.js, wirer le pipeline trigger from UI (actuellement CLI-only), et porter les 3 panes V26 totalement absentes (Scent Trail · Experiments V27 · GEO V31) — en 4 tiers progressifs sur 25-34 jours solo dev pour ~70% canonical parity.

Décisions architecturales actées (cf [DECISIONS_2026-05-14.md](../../docs/architecture/DECISIONS_2026-05-14.md)) :
- **D1.A** Monorepo shell consolidé (pas de re-fédération 5 µfrontends)
- **D2.C-Phase-A** Supabase Edge Functions + queue + worker local Python ($0)
- **D3.A** `/gsg` = Design Grammar viewer + `/gsg/handoff` = Brief Wizard relocated
- **D4.B** Re-enrichment V3.3 différé Phase C-full séparé

## Architecture Decisions

### AD-1 — Visual DNA V22 = source de vérité unique
Le V26 HTML (`deliverables/GrowthCRO-V26-WebApp.html` L17-100) est la source canonique du design system. Toutes les nouvelles variables CSS (`--night-*`, `--gold-*`, `--aurora-*`, `--sp-*` φ-ratio) sont extraites de ce fichier sans modification. Les noms `--gc-*` existants sont DÉPRÉCIÉS au profit du nouveau système. Migration des call sites via Tier 1 #1.

### AD-2 — Worker daemon = bridge UI↔Python CLI
Le bridge entre webapp UI et pipelines Python est un script `growthcro/worker/daemon.py` (NEW) qui poll `Supabase runs` queue et exécute les CLI existants (`growthcro/capture/*`, `moteur_gsg/*`, etc.) — pas de rewrite Python. Phase A = run local sur machine Mathis (zero cost). Phase B = migrate to Fly.io ($5/mo) quand scaling.

### AD-3 — Supabase Realtime = backbone notifications
Channel `public:runs` émet updates de `runs.status` (pending → running → completed/failed). UI subscribes via `@supabase/ssr` realtime client. Pattern réutilisable pour audits, GSG runs, Reality polls, GEO scans.

### AD-4 — `/gsg` route purpose = Design Grammar viewer (D3.A)
Move current `/gsg` (BriefWizard orphan) → `/gsg/handoff`. Rebuild `/gsg` = V26 surface Design Grammar viewer (7 artefacts/client). Two distinct features, two distinct routes.

### AD-5 — Aucun `_vNN` dans les nouveaux fichiers (per AD-9 cleanup epic)
Tout nouveau fichier créé dans ce epic respecte la doctrine "files named by capability, never by version". Les noms `recos_v13_final.json` / `recos_v21_cluster_*.json` legacy restent intacts mais ne sont JAMAIS référencés dans le nouveau code (utiliser l'output canonique `migrate_disk_to_supabase.py` dual-schema merge en attendant `recos.json` canonical de Phase C-full).

### AD-6 — Mathis-in-loop validation par tier
Avant transition tier suivant, validation manuelle Mathis sur l'environnement Vercel prod (post-merge). Pas de "shipped" claim avant validation. Doctrine anti-velocity.

## Technical Approach

### Frontend Components (TIER 1 + TIER 2 + TIER 3 + TIER 4)
- `@growthcro/ui` design system V22 : tokens.css refonte complète (1#1)
- Starfield canvas component `<StarfieldBackground />` (1#1)
- KPI gradient utility classes (1#1)
- `<TriggerRunButton>` reusable wiring vers `/api/runs/*` (1#2)
- `<RunStatusPill>` realtime channel subscriber (1#2)
- `<AddClientModal>` + `<RunAuditButton>` (1#3)
- Dashboard sections : Closed-Loop strip + pillars chart + priority chart + breakdowns (2#4)
- Audit detail enhancements : CRIT_NAMES_V21 map + dual-viewport toggle + bbox crops (2#5+6)
- New routes : `/scent`, `/experiments`, `/geo` (3#7+8+9)
- `/gsg` rebuild as Design Grammar viewer + `/gsg/handoff` Brief Wizard (3#10)
- Reality 5 connector OAuth flows + credentials gate (3#11)
- Doctrine + Learning polish (mermaid Closed Loop diagram + dogfood card) (3#12)
- Global chrome : Cmd+K palette + sticky header + 11-sidebar (4#13)

### Backend Services (TIER 1 #2 + TIER 3 #11)
- Supabase Edge Functions `/runs/{capture,score,recos,gsg,multi_judge,reality}` (1#2)
- Supabase `runs` table + RLS write policies + Realtime channel `public:runs` (1#2)
- `growthcro/worker/daemon.py` Python polling worker (1#2)
- 5 OAuth callback handlers for Reality connectors (3#11)
- Supabase `reality_snapshots` + `geo_audits` + `experiments` tables (TIER 3)

### Infrastructure
- Aucune nouvelle infra Phase A (worker tourne local Mathis machine)
- Phase B Fly.io migration = sub-PRD séparé V2
- Supabase EU project existant utilisé
- Vercel project existant utilisé (1 deploy per push to main)

## Implementation Strategy

### Stratégie tiers progressifs avec mathis-in-loop gates
**TIER 1 (P0 blocking)** d'abord car (a) visual DNA = "ça redevient V26 immédiatement", (b) pipeline trigger = sortie durable de l'écran de fumée, (c) client lifecycle = "partir de zéro" possible.

**TIER 2 (P0 V26 parity)** après TIER 1 car dépend du DNA #1 + lifecycle infra #3.

**TIER 3 (P1 missing surfaces)** parallel-friendly (Scent · Experiments · GEO · Learning) sauf #11 Reality qui dépend de #2 pipeline trigger.

**TIER 4 (P2 enhancements)** en fin pour ne pas perdre de temps sur polish avant que les fondations ne soient stables.

### Risk mitigation
- Test visuel Playwright + manual Mathis validation par tier
- Lighthouse perf budget ≥85 (backdrop-filter `blur(22px)` peut peser)
- 1 sub-PRD = 1 PR-equivalent = commit isolé
- Code hygiene gate `lint_code_hygiene.py --staged` exit 0 avant commit
- Typecheck shell `npx tsc --noEmit` exit 0 avant commit

## Task Breakdown Preview

16 tasks répartis en 4 tiers. Parallelization opportunities identifiées :

| # | Task | Tier | Effort | Depends on | Parallel-safe |
|---|---|---|---|---|---|
| 001 | design-dna-v22-stratospheric-recovery | 1 | 3-4d | — | yes |
| 002 | pipeline-trigger-backend (Phase A) | 1 | 2-3d | — | yes (different files) |
| 003 | client-lifecycle-from-ui | 1 | 1-2d | 002 | no |
| 004 | dashboard-v26-closed-loop-narrative | 2 | 3-4d | 001 | yes |
| 005 | growth-audit-v26-deep-detail | 2 | 3-4d | 001, 006 | no (depends on bbox utilities) |
| 006 | reco-lifecycle-bbox-and-evidence | 2 | 2d | 001 | yes |
| 007 | scent-trail-pane-port | 3 | 2d | — | yes |
| 008 | experiments-v27-calculator | 3 | 2d | — | yes |
| 009 | geo-monitor-v31-pane | 3 | 2d | Mathis-keys | yes |
| 010 | gsg-design-grammar-viewer-restore | 3 | 2d | 002 (for trigger) | no |
| 011 | reality-layer-5-connectors-wiring | 3 | 3d | 002, Mathis-creds | no |
| 012 | learning-doctrine-dogfood-restore | 3 | 2d | 001 | yes |
| 013 | global-chrome-cmdk-breadcrumbs | 4 | 2d | 001-012 done | no (touches all) |
| 014 | essential-skills-install-and-wire | 4 | 1-2d | — | yes |
| 015 | legacy-cleanup-mega-prompt-archive | 4 | 1d | — | yes |
| 016 | microfrontends-decision-doc | 4 | 1d | — (DECISIONS already documented) | yes |

**Total parallel tasks** : 11/16 — fortement parallélisable une fois TIER 1 #1+#2 terminés.

## Dependencies

### Externes (Mathis-side)
- D1-D4 décisions ✅ tranchées (cf DECISIONS_2026-05-14.md)
- 🔴 Rotater Anthropic API key (security, pas blocking pipeline mais à faire ASAP)
- 🟡 OPENAI_API_KEY + PERPLEXITY_API_KEY (avant task 009)
- 🟡 OAuth creds Reality 5 connectors (avant task 011)
- 🟡 Mathis manual validation par tier (~3 × 1h)

### Externes (techniques)
- Supabase EU project (existant)
- Vercel project (existant)
- @supabase/ssr Realtime client (existant)
- next/font/google (existant)
- Playwright (existant pour tests)

### Internes
- `deliverables/GrowthCRO-V26-WebApp.html` = source visual DNA (L17-100)
- `deliverables/architecture-explorer-data.js` = source architecture canonique
- `growthcro/capture/*` `growthcro/perception/*` `growthcro/scoring/*` `growthcro/recos/*` (CLI fonctionnels, à wirer)
- `moteur_gsg/*` `moteur_multi_judge/*` (CLI fonctionnels, à wirer)

## Success Criteria (Technical)

### TIER 1 (foundations)
- [ ] Visual DNA V22 actif : Cormorant Garamond + Sunset Gold + starfield + φ-spacing visibles
- [ ] Pipeline trigger UI : POST /api/runs/capture → row Supabase → worker pickup → completion notification
- [ ] AddClient → AddAudit → result viewable end-to-end < 5 min

### TIER 2 (V26 parity)
- [ ] Dashboard 8-KPI strip + 6 pillars chart + priority dist + business/page-type tabs
- [ ] Reco display FR labels via CRIT_NAMES_V21 (51 mappings)
- [ ] Dual-viewport 💻/📱 toggle desktop/mobile
- [ ] Bbox screenshot crops + 3-tab synthesis + lifecycle pill

### TIER 3 (missing surfaces)
- [ ] `/scent` `/experiments` `/geo` routes fonctionnelles
- [ ] `/gsg` Design Grammar viewer + `/gsg/handoff` Brief Wizard
- [ ] Reality 5 connectors OAuth flows + credentials gates

### TIER 4 (enhancements)
- [ ] Cmd+K palette + 11-sidebar avec count badges
- [ ] 8/8 essential skills installés ou rationale documentée
- [ ] 18 legacy modules archivés

### Cross-tier metrics
- [ ] Feature parity V26 ≥65% (vs 28% actuel)
- [ ] Visual DNA parity ≥80% (vs 12% actuel)
- [ ] Architecture canonical alignment ≥70% (vs 30% actuel)
- [ ] 9/10 user journeys fonctionnels (vs 4/10 actuel)
- [ ] Mathis manual validation : "OUI ça ressemble enfin à V26 + ça marche end-to-end"

## Estimated Effort

| Tier | Effort range | Sub-PRDs | Mathis validation |
|---|---|---|---|
| 1 | 5-8 jours | 3 tasks (#001, #002, #003) | ~1h gate après #003 |
| 2 | 8-10 jours | 3 tasks (#004, #005, #006) | ~1h gate après #006 |
| 3 | 7-9 jours | 6 tasks (#007–#012) | ~1h gate après #012 |
| 4 | 5-7 jours | 4 tasks (#013–#016) | ~30min final validation |
| **Total** | **25-34 jours solo dev** | **16 tasks** | **~3.5h cumulé Mathis** |

## Tasks Created

(Tasks listed below — see individual files for full scope)

### TIER 1 — Foundations (P0 blocking)
- [x] 001.md - design-dna-v22-stratospheric-recovery ✅ done 2026-05-13 (commits 358a75e + 772961e)
- [x] 002.md - pipeline-trigger-backend Phase A ✅ done 2026-05-14 (commits 725021a + fe33d1f + 2b572a1 + f337df7 + 5cf1432 + f147bfa; migration applied + worker E2E validated live)
- [ ] 003.md - client-lifecycle-from-ui (parallel: false, depends 002) ← **NEXT SPRINT**

### TIER 2 — V26 Parity (P0)
- [ ] 004.md - dashboard-v26-closed-loop-narrative (parallel: true, depends 001)
- [ ] 005.md - growth-audit-v26-deep-detail (parallel: false, depends 001+006)
- [ ] 006.md - reco-lifecycle-bbox-and-evidence (parallel: true, depends 001)

### TIER 3 — Missing Surfaces (P1)
- [ ] 007.md - scent-trail-pane-port (parallel: true)
- [ ] 008.md - experiments-v27-calculator (parallel: true)
- [ ] 009.md - geo-monitor-v31-pane (parallel: true, depends Mathis-keys)
- [ ] 010.md - gsg-design-grammar-viewer-restore (parallel: false, depends 002)
- [ ] 011.md - reality-layer-5-connectors-wiring (parallel: false, depends 002+Mathis-creds)
- [ ] 012.md - learning-doctrine-dogfood-restore (parallel: true, depends 001)

### TIER 4 — Enhancements (P2)
- [ ] 013.md - global-chrome-cmdk-breadcrumbs (parallel: false, depends 001-012)
- [ ] 014.md - essential-skills-install-and-wire (parallel: true)
- [ ] 015.md - legacy-cleanup-mega-prompt-archive (parallel: true)
- [ ] 016.md - microfrontends-decision-doc (parallel: true, mostly done in DECISIONS_2026-05-14.md)

**Total tasks**: 16
**Done**: 2/16 (12.5%)
**In progress**: 0
**Next up**: task 003 (client-lifecycle-from-ui, depends on 002 ✓)
**Parallel tasks**: 11
**Sequential tasks**: 5
**Estimated total effort**: 200-272 hours (25-34 jours solo dev) — ~24-32h consumed (Sprint 1 + 2)

## Progress log

### 2026-05-13 — Sprint 1 (Task 001) ✅
**Visual DNA V22 Stratospheric Observatory recovery foundation**
- Commits : 358a75e (foundation) + 772961e (Playwright spec 7/7 PASS)
- 4 typefaces loaded via next/font (Cormorant + Playfair + Inter + JetBrains Mono)
- Alaska Boreal Night palette + Sunset Gold + Aurora + 4-layer body bg
- φ-ratio spacing (--sp-0 to --sp-7)
- KPI value editorial italic gold-gradient (.gc-kpi b automatic + .gc-kpi-value opt-in)
- Glass cards (.gc-glass-card) with backdrop-filter
- Aura cubic-bezier easings
- StarfieldBackground canvas component (4 layers parallax + shooting stars + 1.8s fade-in + prefers-reduced-motion)
- scoreColor(pct) HSL utility (red→gold→green continuous)
- Backward-compat --gc-* aliases preserve all existing component renders

### 2026-05-14 — Sprint 2 (Task 002) ✅
**Pipeline-trigger backend Phase A — UI ↔ CLI bridge via Supabase runs queue**
- Commits : 725021a (backend) + fe33d1f (frontend) + 2b572a1 (tests) + f337df7 (routing fix) + 5cf1432 (spec fix) + f147bfa (defensive worker)
- Supabase migration 20260514_0017_runs_extend.sql APPLIED LIVE by Mathis :
  - runs.type enum extended (capture/score/recos/gsg/multi_judge/reality/geo)
  - runs.error_message + runs.progress_pct columns added
  - idx_runs_pending_fifo partial index for worker polling
- Python worker (growthcro/worker/) :
  - daemon.py : poll Supabase queue every 30s, atomic claim, subprocess dispatch
  - dispatcher.py : RUN_TYPE_TO_CLI mapping for 9 types
  - cli.py + __main__.py : `python -m growthcro.worker --once` / loop
  - README.md : Mathis-facing operational doc
- Pydantic models (growthcro/models/runs_models.py) : RunCreate / RunRow / RunUpdate
- Next.js API routes : POST /api/runs (admin gated) + GET /api/runs + GET /api/runs/[id]
- UI components : <TriggerRunButton /> + <RunStatusPill /> (live Supabase Realtime channel public:runs)
- Playwright runs-trigger.spec.ts : 10/10 PASS on prod
- Defensive PATCH fallback : worker functions even pre-migration
- Live E2E smoke validated 2026-05-14T15:29Z : insert pending → worker pickup → dispatch → status=completed in 0.02s

**Cumulative tests** : 41/41 PASS on prod (10 runs-trigger + 7 visual-dna-v22 + 24 wave-a-2026-05-14)
