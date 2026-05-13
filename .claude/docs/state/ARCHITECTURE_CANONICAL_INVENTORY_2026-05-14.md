# Architecture Canonical Inventory — extracted from architecture-explorer-data.js (2026-05-14)

> Source: `deliverables/architecture-explorer-data.js` (5683 lines, 198 KB) — generated 2026-05-11T14:19:24Z by `scripts/update_architecture_map.py` from commit `1e339f3edd4d67cc1f95c7162d6bb87378a786d6`.
> Skills integration block is 100% human-curated; module structure is AST-scanned + human-augmented purpose/inputs/outputs/doctrine_refs.
> This document is the **canonical exhaustive snapshot** of the architecture as Mathis designed it. Compare it against `webapp/apps/shell/` to see the design-vs-shipped delta.

## TL;DR

- **251 modules** across 25 packages (233 active, 18 legacy, 0 pending)
- **7 pipelines** (audit_pipeline, gsg_pipeline, multi_judge, reality_loop, webapp [meta], webapp_v27, webapp_v28)
- **17 canonical data_artefacts** (12 captures/* per-page artefacts, 1 global clients DB, 1 learning proposals dir, 2 deliverable HTML/JS bundles, 1 pipeline runs report)
- **8 essential skills** + **6 on-demand** slash-command-activated + **5 explicitly excluded** (with rationale)
- **3 combo packs** (audit_run, gsg_generation, webapp_nextjs) — each ≤4 skills/session per anti-cacophonie rule
- **8 anti-cacophonie rules** governing skill loading order
- **6 mermaid views** (global · audit · gsg · multi-judge · webapp v27→v28 · reality/experiment/learning loop)
- Lifecycle phases: 192 runtime · 22 qa · 20 infrastructure · 15 onboarding · 2 learning

**Top-level architecture**: GrowthCRO is a Python monorepo organized in 8 functional modules behind a single CLI entry. The audit pipeline (capture → perception → scoring → recos) emits a per-page artefact tree under `data/captures/<client>/<page>/`. A consolidator (`build_growth_audit_data`) bundles 56 clients × 185 pages → a 12 MB JS file that today powers the V27 HTML Command Center (file://). A parallel GSG pipeline (`moteur_gsg/orchestrator`) generates LPs via a 12-stage controlled renderer with a 70/30 multi-judge QA gate (`moteur_multi_judge`). A reality loop (GA4/Meta/Google/Shopify/Clarity connectors via `growthcro/reality`) feeds an experiment engine (`growthcro/experiment`) and Bayesian learning (`growthcro/learning/v30_data_driven`). The target webapp V28 is a Next.js shell + 5 microfrontends (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) on Vercel + Supabase EU. Skill integration is governed by 3 disjoint combo packs and an 8-rule anti-cacophonie discipline (max 8 skills/session, never load `Taste Skill` + `brand-guidelines` simultaneously, etc.).

---

## 1. Pipelines

### 1.1 `audit_pipeline`

- **Description**: per-client audit chain (capture → perception → scoring → recos → lifecycle)
- **Status**: (no status set — implicitly active, 56 clients × 185 pages migrated as of 2026-05-11)
- **Stages** (in order):
  1. `discovery (growthcro/research/discovery)`
  2. `capture (growthcro/capture/orchestrator → spatial_v9 + capture.json + page.html)`
  3. `perception (growthcro/perception/persist → perception_v13.json)`
  4. `scoring (growthcro/scoring/persist + scoring/specific/* → score_*.json)`
  5. `evidence (skills/site-capture/scripts/evidence_ledger → evidence_ledger.json)`
  6. `recos (growthcro/recos/orchestrator → recos_enriched.json)`
  7. `lifecycle (skills/site-capture/scripts/reco_lifecycle)`
- **Entrypoint**: `python -m growthcro.cli.capture_full <url> <client>`
- **Duration**: `< 5min per client` (target)
- **Extra metadata**: none.

### 1.2 `gsg_pipeline`

- **Description**: deterministic landing-page generation with bounded LLM use (V27.2-G controlled path)
- **Status**: (no status — active, baseline Weglot 70.9 multi-judge)
- **Stages** (in order):
  1. `intake_wizard (moteur_gsg/core/intake_wizard)`
  2. `brief_v2 (moteur_gsg/core/brief_v2 + prefiller + validator)`
  3. `context_pack (moteur_gsg/core/context_pack)`
  4. `doctrine_pack (moteur_gsg/core/doctrine_planner)`
  5. `visual_intelligence (moteur_gsg/core/visual_intelligence)`
  6. `creative_route_selector V27.2-F (moteur_gsg/core/creative_route_selector)`
  7. `visual_system V27.2-G (moteur_gsg/core/visual_system)`
  8. `page_plan (moteur_gsg/core/planner + component_library)`
  9. `copy_llm (moteur_gsg/core/copy_writer — JSON slots only)`
  10. `controlled_renderer (moteur_gsg/core/page_renderer_orchestrator)`
  11. `qa_runtime (moteur_gsg/core/minimal_guards)`
  12. `minimal_gates (moteur_gsg/modes/mode_1/visual_gates + runtime_fixes)`
  13. `multi_judge_optional (moteur_multi_judge/orchestrator)`
- **Entrypoint**: `python -m moteur_gsg.orchestrator --mode <complete|replace|extend|elevate|genesis>`
- **Duration**: `< 3min lite, < 8min with multi-judge`
- **Extra metadata**: none.

### 1.3 `multi_judge`

- **Description**: post-render QA layer with weighted aggregation
- **Status**: V26.AA Sprint 3 (active)
- **Stages**:
  1. `doctrine_judge V3.2.1 (moteur_multi_judge/judges/doctrine_judge)` — 54 critères + 6 killers
  2. `humanlike_judge (moteur_multi_judge/judges/humanlike_judge)` — 8 dimensions
  3. `implementation_check (moteur_multi_judge/judges/implementation_check)` — runtime bug detection
- **Entrypoint**: (none — orchestrated from inside GSG pipeline)
- **Duration**: (not stated)
- **Extra metadata**:
  - invocation: post-GSG QA, post-audit verification
  - weighting: 70% doctrine / 30% humanlike (V26.AA Sprint 3)

### 1.4 `reality_loop`

- **Description**: closed-loop Reality → Experiment → Learning (V26.C + V27 + V30)
- **Status**: **V30 structurally READY** — connectors + orchestrator + experiment engine + Bayesian learning all in place. **Live runs PENDING per-client credentials in `.env`** (Mathis collects, ~1.5h for 3 pilote clients).
- **Stages**:
  1. `reality_collect (growthcro/reality/orchestrator — 6 connectors GA4/Catchr/Meta/Google/Shopify/Clarity, per-client credentials via growthcro.config.reality_client_env)`
  2. `experiment_propose (growthcro/experiment/runner — 5 AB types, ZERO auto-trigger, status="proposed")`
  3. `experiment_record (growthcro/experiment/recorder — atomic spec persistence + index)`
  4. `experiment_measure_outcomes (growthcro/experiment/recorder.import_outcome — Mathis triggers post live A/B)`
  5. `learning_v29_audit_based (skills/site-capture/scripts/learning_layer_v29_audit_based — 69 proposals from 56 curated V26 clients)`
  6. `learning_v30_data_driven (growthcro/learning/v30_data_driven — Beta-Binomial Bayesian update on V3.3, fed by reality snapshots + experiment outcomes)`
- **Extra metadata**:
  - pilote_clients_proposed: `weglot` (SaaS, ref Weglot V27.2-D listicle), `japhy` (DTC e-com, ref AD-5 non-SaaS-listicle), `<agency_client_TBD>` (1 active Growth Society client)
  - output_paths:
    - `data/reality/<client>/<page_slug>/<iso_date>/reality_snapshot.json`
    - `data/captures/<client>/<page>/reality_layer.json` (legacy mirror for V27 dashboards)
    - `data/experiments/<client>/<exp_id>.json`
    - `data/experiments/_index/experiments_index.json` (regen-able)
    - `data/learning/data_driven_proposals/<iso_date>/<proposal_id>.json`
    - `data/learning/data_driven_stats.json`
    - `data/learning/data_driven_summary.md`
  - webapp_v28_apps consumers:
    - `webapp/apps/reality-monitor` (lists pilote clients, credentials grid per client, snapshot KPIs, realtime runs)
    - `webapp/apps/learning-lab` (V29+V30 proposals listing, filter by track/status/type, accept/reject/defer with `.review.json` sidecar)
  - issue ref: `#23` (epic webapp-stratosphere)

### 1.5 `webapp` (meta-pipeline)

- **Description**: webapp surface evolution V27 HTML → V28 Next.js
- **Status**: V27 HTML active (12 MB growth_audit_data.js, 56 clients, 185 pages); **V28 Next.js 0% — Epic #6** (still labeled 0% in the architecture export, though webapp/apps/shell/ exists today — see §6 cross-references)
- **Stages_v27_html**:
  1. `growthcro/cli/capture_full per-client run`
  2. `skills/site-capture/scripts/build_growth_audit_data consolidates data/captures/* → deliverables/growth_audit_data.js`
  3. `deliverables/GrowthCRO-V27-CommandCenter.html consumes the JS bundle`
- **Stages_v28_nextjs_target**:
  1. `growthcro/api/server FastAPI exposed via Vercel edge functions`
  2. `5 microfrontends: audit-app, reco-app, gsg-studio, reality-monitor, learning-lab`
  3. `Supabase EU region (auth + tables clients/audits/recos/runs + realtime)`

### 1.6 `webapp_v27`

- **Description**: Static HTML/JS MVP — frozen data snapshot regenerated from `data/captures/*`. No server, opened via `file://`.
- **Status**: V27 MVP honest — Issue (number not specified)
- **Flow**:
  - `data/captures/*` (3.7 GB gitignored artifacts produced by audit_pipeline)
  - `skills/site-capture/scripts/build_growth_audit_data.py` (803 LOC, KNOWN_DEBT — pure IO, no growthcro/* imports)
  - `deliverables/growth_audit_data.js` (11.73 MB, `window.GROWTH_AUDIT_DATA`)
  - `deliverables/GrowthCRO-V27-CommandCenter.html` (4 views: command / audit / gsg / demo)
- **Smoke test**: `python3 scripts/test_webapp_v27.py`
- **Target load_s**: 3.0
- **Measured load_s**: 0.61
- **Panes**:
  - **command** — Fleet KPIs + per-client detail (screenshots, pillars, top recos); filters: search query, panel role, sort by P0/score/name
  - **audit** — Page-level audit detail + filtered recos backlog; filters: priority (P0/P1/P2/P3), effort (1-4h / 4-16h / 16h+), lift (1-5% / 5-15% / 15%+); KPIs: page score, P0 count, P1 count, evidence count (+step recos count when present)
  - **gsg** — Deterministic GSG brief preview — copy-only LLM boundary, no full-HTML in browser; modes: complete (M1), replace (M2), extend (M3), elevate (M4), genesis (M5); outputs: JSON brief (gsg_mode + brand_tokens + top_recos + layout + cta_label) + HTML preview tile (screenshot + headline + CTA)
  - **demo** — End-to-end Weglot showcase: Audit → Reco → Brief → Renderer → Judges

### 1.7 `webapp_v28`

- **Description**: Next.js 14 (App Router) + Supabase EU + Vercel microfrontends. 5 microfrontends + 2 placeholders. Scale Growth Society 100+ clients.
- **Status**: V28 v1 — scaffold + migrations + 3 deep microfrontends + 2 placeholders. **Deploy Vercel + Supabase EU PENDING Mathis credentials.**
- **Microfrontends**:
  - `shell (3000)` — auth + nav + dashboard + realtime runs feed `[DEEP]`
  - `audit-app (3001)` — clients + audits + scores + recos `[DEEP]`
  - `reco-app (3002)` — recos browser + filters + priority counts `[DEEP]`
  - `gsg-studio (3003)` — brief wizard + LP preview + multi-judge stage strip `[DEEP]`
  - `reality-monitor (3004)` — data sources panel GA4/Meta/Google/Shopify/Clarity `[PLACEHOLDER]`
  - `learning-lab (3005)` — doctrine proposals V29 + Bayesian V30 tracks `[PLACEHOLDER]`
- **Backend**: Option B chosen — **FastAPI on Railway/Fly.io** (rationale: long-running Playwright capture + LLM scoring incompatible with Vercel edge 30 s limit). `NEXT_PUBLIC_API_BASE_URL` points to Fly.io URL.
- **Auth**: Supabase auth — email/password + magic link via OTP. Cookie httpOnly via `@supabase/ssr`. Middleware gates everything except `/login`, `/auth/callback`, `/privacy`, `/terms`.
- **Realtime**: Supabase channel `public:runs` subscribed by shell (postgres_changes on `runs` table).
- **RLS**: org-based isolation via `is_org_member(org_id)` + `is_org_admin(org_id)` security-definer helpers. Anon role zero read. Service role bypass for migration scripts.
- **Region**: `eu-central-1` (Frankfurt) — RGPD compliance.
- **Target load_s**: 2.0
- **Target audience**: 100+ clients agence Growth Society + futures agences.
- **Skills combo**: frontend-design + web-artifacts-builder + vercel-microfrontends + Figma Implement Design (≤4 per CLAUDE.md anti-pattern #12)
- **Task ref**: Issue #21 webapp-stratosphere
- **Migration script**: `scripts/migrate_v27_to_supabase.py` (idempotent, 56 clients × 185 audits × 3045 recos)
- **Architecture doc**: `architecture/GROWTHCRO_ARCHITECTURE_V1.md`

---

## 2. Data Artefacts (17 canonical)

### 2.1 `data/_briefs_v2/<timestamp>_<client>_<page_type>_<run>.json`
- **Producer**: `moteur_gsg/core/brief_v2` + `brief_v2_prefiller`
- **Consumers**: `moteur_gsg/orchestrator`, `moteur_gsg/modes/*`
- **Schema**: implicit — BriefV2 contract
- **Cardinality**: 1 per GSG intake

### 2.2 `data/_pipeline_runs/<run-id>/multi_judge.json`
- **Producer**: `moteur_multi_judge/orchestrator`
- **Consumers**: `scripts/run_gsg_full_pipeline`, Mathis review
- **Schema**: implicit — `final_score_pct` + doctrine + humanlike + killers
- **Cardinality**: 1 per GSG run

### 2.3 `data/captures/<client>/<page>/capture.json`
- **Producer**: `growthcro/capture/scorer`
- **Consumers**: `growthcro/perception/persist`, `growthcro/scoring/persist`, `skills/site-capture/scripts/multi_judge`
- **Schema**: `SCHEMA/score_pillar.schema.json` (capture is upstream of pillar scores)
- **Cardinality**: 1 per client per page

### 2.4 `data/captures/<client>/<page>/evidence_ledger.json`
- **Producer**: `skills/site-capture/scripts/evidence_ledger`
- **Consumers**: `growthcro/recos/orchestrator`, `deliverables/GrowthCRO-V27-CommandCenter.html`
- **Schema**: implicit — evidence per criterion
- **Cardinality**: 1 per client per page

### 2.5 `data/captures/<client>/<page>/perception_v13.json`
- **Producer**: `growthcro/perception/persist`
- **Consumers**: `growthcro/scoring/persist`, `growthcro/recos/orchestrator`, `skills/site-capture/scripts/perception_bridge`
- **Schema**: `SCHEMA/perception_v13.schema.json`
- **Cardinality**: 1 per client per page

### 2.6 `data/captures/<client>/<page>/recos_enriched.json`
- **Producer**: `growthcro/recos/orchestrator`
- **Consumers**: `skills/site-capture/scripts/build_growth_audit_data`, `growthcro/api/server`
- **Schema**: `SCHEMA/recos_enriched.schema.json`
- **Cardinality**: 1 per client per page

### 2.7 `data/captures/<client>/<page>/score_page_type.json`
- **Producer**: `growthcro/scoring/persist` + `growthcro/scoring/specific/*`
- **Consumers**: `growthcro/recos/orchestrator`
- **Schema**: `SCHEMA/score_page_type.schema.json`
- **Cardinality**: 1 per client per page

### 2.8 `data/captures/<client>/<page>/score_{hero,persuasion,ux,coherence,psycho,tech}.json`
- **Producer**: `growthcro/scoring/persist` + `growthcro/scoring/ux` + legacy `skills/score_*.py`
- **Consumers**: `growthcro/recos/orchestrator`, `growthcro/scoring/cli`
- **Schema**: `SCHEMA/score_pillar.schema.json`
- **Cardinality**: **6 per client per page** (one per pillar)

### 2.9 `data/captures/<client>/<page>/spatial_v9.json`
- **Producer**: `growthcro/capture/orchestrator` (via `spatial_v9.js` DOM payload)
- **Consumers**: `growthcro/perception/persist`, `growthcro/perception/heuristics`
- **Schema**: implicit — sections / bbox / hierarchy
- **Cardinality**: 1 per client per page

### 2.10 `data/captures/<client>/brand_dna.json`
- **Producer**: `skills/site-capture/scripts/brand_dna_extractor`
- **Consumers**: `moteur_gsg/core/brand_intelligence`, `moteur_gsg/core/context_pack`
- **Schema**: implicit — palette / typography / voice / proof
- **Cardinality**: 1 per client

### 2.11 `data/captures/<client>/client_intent.json`
- **Producer**: `growthcro/perception/intent` + `skills/site-capture/scripts/intent_detector_v13`
- **Consumers**: `growthcro/recos/prompts`, `moteur_gsg/core/context_pack`
- **Schema**: implicit — intent matrix
- **Cardinality**: 1 per client

### 2.12 `data/captures/<client>/design_grammar/*`
- **Producer**: `skills/site-capture/scripts/design_grammar`
- **Consumers**: `moteur_gsg/core/design_grammar_loader`, `moteur_gsg/core/design_tokens`
- **Schema**: implicit — V30 design tokens
- **Cardinality**: 1 per client (multi-file)

### 2.13 `data/captures/<client>/discovered_pages_v25.json`
- **Producer**: `skills/site-capture/scripts/discover_pages_v25`
- **Consumers**: `growthcro/cli/enrich_client`, `growthcro/research/discovery`
- **Schema**: implicit — sitemap-style page inventory
- **Cardinality**: 1 per client

### 2.14 `data/clients_database.json`
- **Producer**: `growthcro/cli/add_client` + `skills/webapp-publisher`
- **Consumers**: `growthcro/api/server`, `skills/site-capture/scripts/build_growth_audit_data`
- **Schema**: `SCHEMA/clients_database.schema.json`
- **Cardinality**: 1 (global)

### 2.15 `data/learning/audit_based_proposals/*.json`
- **Producer**: `skills/site-capture/scripts/learning_layer_v29_audit_based`
- **Consumers**: `playbook/*` (Mathis review)
- **Schema**: implicit — 69 proposals V29
- **Cardinality**: 1 per proposal (currently 69)

### 2.16 `deliverables/GrowthCRO-V27-CommandCenter.html`
- **Producer**: human-curated (V27)
- **Consumers**: browser (`file://`), `scripts/test_webapp_v27`
- **Schema**: (none)
- **Cardinality**: 1 (global)
- **Extra**: status=active; views = command (fleet+client detail) · audit (P0/P1/Evidence KPIs + priority/effort/lift filters) · gsg (5 modes: complete/replace/extend/elevate/genesis + deterministic brief) · demo (end-to-end Weglot showcase)

### 2.17 `deliverables/growth_audit_data.js`
- **Producer**: `skills/site-capture/scripts/build_growth_audit_data`
- **Consumers**: `deliverables/GrowthCRO-V27-CommandCenter.html`, `scripts/test_webapp_v27`
- **Schema**: `SCHEMA/dashboard_v17_data.schema.json`
- **Cardinality**: 1 (global)
- **Extra**: 11.73 MB · status active · last_regen 2026-05-11 (Issue #20 post-cleanup) · **56 clients · 185 pages · 3045 LP-level recos · 170 step-level recos · 8347 evidence items**

---

## 3. Modules grouped by package (251 total)

### 3.1 `SCHEMA` (2 modules)

- **SCHEMA/validate** (`SCHEMA/validate.py`) — active/infrastructure — Validate one JSON file against a JSON schema — building block for `validate_all`. *Inputs*: JSON file, schema file. *Outputs*: exit 0 (valid) or stderr + exit 1.
- **SCHEMA/validate_all** (`SCHEMA/validate_all.py`) — active/infrastructure — Validate ALL pipeline files against their schemas — stops at first error (exit 1). *Inputs*: `data/captures/<client>/<page>/*.json`, `playbook/bloc_*_v3.json`. *Outputs*: exit 0/1.

### 3.2 `growthcro` (1 module)

- **growthcro** (`growthcro/__init__.py`) — active/runtime — Top-level package.

### 3.3 `growthcro/api` (3 modules)

- **growthcro/api** (`growthcro/api/__init__.py`) — active/infrastructure — FastAPI surface root.
- **growthcro/api/audits** (`growthcro/api/audits.py`) — active/infrastructure — Agency audit routes (axis #4 — orchestration).
- **growthcro/api/server** (`growthcro/api/server.py`) — active/infrastructure — FastAPI server: POST `/capture`, GET `/captures`, `/audits`, `/clients`. Exposed via Vercel edge functions in V28 target. *Inputs*: HTTP requests. *Outputs*: JSON + pipeline kicks.

### 3.4 `growthcro/audit_gads` (4 modules)

- **growthcro/audit_gads** — active/runtime — Google Ads audit module, thin wrapper around the `anthropic-skills:gads-auditor` skill.
- **growthcro/audit_gads/cli** — active/runtime — Google Ads audit CLI (axis #5).
- **growthcro/audit_gads/notion_export_gads** — active/runtime — Notion-template renderer for Google Ads audits (axis #8 — I/O serialization).
- **growthcro/audit_gads/orchestrator** — active/runtime — Google Ads audit orchestration (axis #4 — orchestration).

### 3.5 `growthcro/audit_meta` (4 modules)

- **growthcro/audit_meta** — active/runtime — Meta Ads audit module, thin wrapper around `anthropic-skills:meta-ads-auditor`.
- **growthcro/audit_meta/cli** — active/runtime — Meta Ads audit CLI (axis #5).
- **growthcro/audit_meta/notion_export_meta** — active/runtime — Notion-template renderer for Meta Ads audits (axis #8).
- **growthcro/audit_meta/orchestrator** — active/runtime — Meta Ads audit orchestration (axis #4).

### 3.6 `growthcro/capture` (9 modules)

- **growthcro/capture** — active/runtime — Single concern: collect raw page artifacts.
- **growthcro/capture/browser** — active/runtime — Playwright browser lifecycle + cookie handling — owns local Chromium / cloud WSS / Bright Data CDP launch. *Inputs*: `BROWSER_WS_ENDPOINT`, `BRIGHT_DATA_CDP`, growthcro.config. *Outputs*: `playwright.async_api.Browser`, `BrowserContext`.
- **growthcro/capture/cli** — active/onboarding — argparse CLI for cloud capture — single-page + batch dispatchers.
- **growthcro/capture/cloud** — active/runtime — Bright Data / Browserless cloud endpoint resolution — pure config logic, no I/O.
- **growthcro/capture/dom** — active/runtime — Browser-side JS payloads + static-HTML cleaning helpers — DOM serialization only, no scoring logic. *Inputs*: raw HTML / rendered DOM. *Outputs*: spatial_v9 JSON payload, cleaned HTML.
- **growthcro/capture/orchestrator** — active/runtime — Single + batch capture pipelines — coordinates browser → page → screenshots → DOM extraction → persistence. *Outputs*: `data/captures/<client>/<page>/{spatial_v9.json, capture.json, page.html, screenshots/*.png}`.
- **growthcro/capture/persist** — active/runtime — Pure I/O assemblers for `spatial_v9.json` + `capture.json` + `page.html`.
- **growthcro/capture/scorer** — active/runtime — Static-HTML CRO data extraction — parses rendered DOM into `capture.json` (150+ data points: CTAs, headings, trust signals…).
- **growthcro/capture/signals** — active/runtime — Static-HTML signal extractors — pure functions, one `extract_*` per criterion bloc.

### 3.7 `growthcro/cli` (4 modules)

- **growthcro/cli** — active/onboarding — Command-line entrypoints (add_client, capture_full, enrich_client).
- **growthcro/cli/add_client** — active/onboarding — Quickly add a client (slug + URL) to `data/clients_database.json`.
- **growthcro/cli/capture_full** — active/onboarding — Orchestrator V13 SaaS-grade — full per-client pipeline (capture → perception → scoring → recos) in one command.
- **growthcro/cli/enrich_client** — active/onboarding — Discovery + URL validation + page selection for a new client — pre-capture intake.

### 3.8 `growthcro/config` (1 module)

- **growthcro/config** — active/infrastructure — **Single env-var boundary** (Rule 2 doctrine). All other modules read env exclusively through `config`. *Inputs*: `.env`, `os.environ`. *Outputs*: config singleton, `MissingConfigError` on `require_*`.

### 3.9 `growthcro/experiment` (4 modules)

- **growthcro/experiment** — active/runtime — V27 promoted to growthcro/.
- **growthcro/experiment/engine** — active/runtime — Sample-size calculator + spec builder.
- **growthcro/experiment/recorder** — active/runtime — Index + outcome import.
- **growthcro/experiment/runner** — active/runtime — Emit experiment PROPOSALS, ZERO auto-trigger. *Inputs*: client_slug, page_slug, reality_snapshot dict, recos list. *Outputs*: `data/experiments/<client>/<exp_id>.json` (status="proposed").

### 3.10 `growthcro/gsg_lp` (6 modules) — **ALL LEGACY**

- **growthcro/gsg_lp** — active/runtime — Growth Site Generator — landing-page mega-prompt orchestrator (legacy entry).
- **growthcro/gsg_lp/brand_blocks** — **legacy**/runtime — Mega-prompt block renderers for brand DNA + design grammar + AURA — 4 `render_*_block` helpers.
- **growthcro/gsg_lp/data_loaders** — **legacy**/runtime — Data loaders for the GSG mega-prompt pipeline — thin wrappers around file reads or subprocess calls.
- **growthcro/gsg_lp/lp_orchestrator** — **legacy**/runtime — Legacy CLI entry point + Sonnet text-call wrapper.
- **growthcro/gsg_lp/mega_prompt_builder** — **legacy**/runtime — Mega-prompt builder for the legacy LP pipeline (3 concerns: assembly, output parsing, persistence).
- **growthcro/gsg_lp/repair_loop** — **legacy**/qa — V26.Z W3 — multi-judge → repair iteration loop (post-render gates).

### 3.11 `growthcro/learning` (2 modules)

- **growthcro/learning** — active/runtime — Learning Layer root.
- **growthcro/learning/v30_data_driven** — active/runtime — V30 Bayesian update on doctrine V3.3. *Inputs*: experiments with outcome != null + reality snapshots. *Outputs*: `data/learning/data_driven_proposals/<iso_date>/<proposal_id>.json` + `data_driven_stats.json` + `data_driven_summary.md`.

### 3.12 `growthcro/lib` (2 modules)

- **growthcro/lib** — active/infrastructure — Shared infrastructure utilities.
- **growthcro/lib/anthropic_client** — active/infrastructure — Shared Anthropic SDK factory — single point of API client construction with retries and graceful key validation. *Inputs*: `ANTHROPIC_API_KEY` via growthcro.config. *Outputs*: `anthropic.Anthropic` instance.

### 3.13 `growthcro/perception` (6 modules)

- **growthcro/perception** — active/runtime — DOM heuristics + adaptive DBSCAN clustering + role intent.
- **growthcro/perception/cli** — active/onboarding — argparse entrypoint (single page or fleet-wide `--all`).
- **growthcro/perception/heuristics** — active/runtime — DOM-driven keyword heuristics + bbox/font helpers + noise scoring 0-100.
- **growthcro/perception/intent** — active/runtime — Cluster role assignment — 9 canonical roles (HERO/NAV/PRICING/FAQ/...).
- **growthcro/perception/persist** — active/runtime — Page-level orchestration — flatten elements, score noise, cluster, assign roles, write `perception_v13.json`. *Inputs*: `spatial_v9.json`, `capture.json`.
- **growthcro/perception/vision** — active/runtime — Adaptive 1-D vertical DBSCAN + cluster refinement (no Anthropic call yet — Sonnet vision integration **deferred**).

### 3.14 `growthcro/reality` (10 modules)

- **growthcro/reality** — active/runtime — V26.C / V26.AI promoted to `growthcro/`.
- **growthcro/reality/base** — active/runtime — Base interface (promoted from `skills/site-capture`).
- **growthcro/reality/catchr** — active/runtime — Catchr connector — Growth Society internal GA4+ aggregator.
- **growthcro/reality/clarity** — active/runtime — Microsoft Clarity Data Export connector — heatmaps + rage clicks + scroll depth.
- **growthcro/reality/credentials** — active/runtime — **Credentials inspector** (Issue #23) — for a given client_slug, reports configured vs missing connectors. Never logs values.
- **growthcro/reality/ga4** — active/runtime — Native Google Analytics 4 Data API v1 connector.
- **growthcro/reality/google_ads** — active/runtime — Google Ads API connector — campaign metrics per landing page.
- **growthcro/reality/meta_ads** — active/runtime — Meta Marketing API connector — `ad_spend` + ROAS + CTR per landing page.
- **growthcro/reality/orchestrator** — active/runtime — Multi-connector aggregator (Issue #23). *Inputs*: client_slug, page_url, page_slug, period_days. *Outputs*: `data/reality/<client>/<page_slug>/<iso_date>/reality_snapshot.json` + legacy mirror `data/captures/<client>/<page_slug>/reality_layer.json`.
- **growthcro/reality/shopify** — active/runtime — Shopify Admin GraphQL — orders + revenue + funnel per landing page.

### 3.15 `growthcro/recos` (6 modules)

- **growthcro/recos** — active/runtime — Reco V13 generation pipeline.
- **growthcro/recos/cli** — active/onboarding — Single argparse entrypoint with `prepare` / `enrich` subcommands.
- **growthcro/recos/client** — active/runtime — Anthropic SDK calls + structured retry — wraps `growthcro.lib.anthropic_client.get_anthropic_client()` with reco-specific retry logic.
- **growthcro/recos/orchestrator** — active/runtime — Per-page prompt prep + per-page LLM batch loop. Coordinates schema/prompts/client. *Outputs*: `data/captures/<client>/<page>/recos_enriched.json`.
- **growthcro/recos/prompts** — active/runtime — Turns page-level data into prompt strings (no LLM call, no I/O).
- **growthcro/recos/schema** — active/runtime — Reco doctrine + scope matrix caches, JSON validation, ICE compute, fallback template.

### 3.16 `growthcro/research` (5 modules)

- **growthcro/research** — active/onboarding — Full-site crawler + brand-identity extractor (orthogonal to perception).
- **growthcro/research/brand_identity** — active/onboarding — CSS-based brand identity extraction — palette, typography, mood, logos, favicon.
- **growthcro/research/cli** — active/onboarding — argparse entrypoint — runs full discovery + content + brand-identity pipeline.
- **growthcro/research/content** — active/onboarding — Page content fetching + structured extraction (text, certifications, prices, ratings).
- **growthcro/research/discovery** — active/onboarding — URL discovery + categorization — sitemap-style crawl.

### 3.17 `growthcro/scoring` (10 modules)

- **growthcro/scoring** — active/runtime — Scoring layer — pillars dispatcher + UX bloc + page-type-specific detectors + persist.
- **growthcro/scoring/cli** — active/onboarding — argparse entrypoints (`score_specific`, `score_ux`) — unified subcommand dispatcher.
- **growthcro/scoring/persist** — active/runtime — Page-type-specific scoring persist — writes `score_specific.json` + `score_page_type.json`.
- **growthcro/scoring/pillars** — active/runtime — Shared pillar dispatcher — pageType filtering, weight, caps, verdict. Used by every bloc scorer.
- **growthcro/scoring/specific** — active/runtime — Page-type-specific detector aggregator — exports `DETECTORS`, `TERNARY`, helpers, fallback.
- **growthcro/scoring/specific/home_leadgen** — active/runtime — Home, pricing, checkout, bundle, advertorial, comparison, thank-you-page detectors.
- **growthcro/scoring/specific/listicle** — active/runtime — Listicle/blog detectors — `list_*` and `blog_*` criteria.
- **growthcro/scoring/specific/product** — active/runtime — Product/collection detectors — `pdp_*`, `col_*` + shared trust/social-proof helpers.
- **growthcro/scoring/specific/sales** — active/runtime — Sales-page detectors — `vsl_*`, `sqz_*`, `lg_*`, `sp_*`, `web_*`, `chal_*`, `quiz_*` criteria.
- **growthcro/scoring/ux** — active/runtime — Bloc-3 UX scorer (`ux_01..ux_08`).

### 3.18 `moteur_gsg` (1 module)

- **moteur_gsg** — active/runtime — Growth Site Generator V26.AA.

### 3.19 `moteur_gsg/core` (37 modules)

- **moteur_gsg/core** — active/runtime — Building blocs réutilisés par les 5 modes.
- **moteur_gsg/core/animations** — active/runtime — Emil Kowalski motion layer for the controlled GSG renderer (V27.2-G+).
- **moteur_gsg/core/asset_resolver** — active/runtime — Visual-asset key resolution — maps logical asset keys to actual URLs/paths from plan constraints.
- **moteur_gsg/core/brand_intelligence** — active/runtime — Brand Intelligence wrapper — combines `brand_dna_extractor` + `brand_dna_diff_extractor` outputs.
- **moteur_gsg/core/brief_v15_builder** — **legacy**/runtime — Brief V15 builder — bridge format between audit V26 and GSG Mode 2 REPLACE (legacy).
- **moteur_gsg/core/brief_v2** — active/runtime — BriefV2 schema + builder — 30+ inputs canonical brief format (V26.AD Sprint I).
- **moteur_gsg/core/brief_v2_prefiller** — active/runtime — BriefV2 prefiller — auto-fills brief from known client data via the root `client_context` router.
- **moteur_gsg/core/brief_v2_validator** — active/runtime — BriefV2 validator — parses + validates a BriefV2 from JSON file or dict.
- **moteur_gsg/core/canonical_registry** — active/qa — **Canonical GSG contract** — single source of truth for the 'one GSG' boundary.
- **moteur_gsg/core/component_library** — active/runtime — Page-type component blueprints — V27.2-B turns strategic contracts into concrete section/component plans.
- **moteur_gsg/core/component_renderer** — active/runtime — Reason/component visual + bullet-list rendering — three helpers.
- **moteur_gsg/core/context_pack** — active/runtime — Generation context pack — loads brand DNA, audience, proof inventory, scent contract, visual assets via the root `client_context`.
- **moteur_gsg/core/copy_writer** — active/runtime — **Bounded copy writer** — Sonnet writes JSON copy slots only, no layout/visuals.
- **moteur_gsg/core/creative_route_selector** — active/runtime — V27.2-F structured Golden/Creative route selector — no LLM, no prompt dumping. Bridges VisualIntelligencePack, AURA and Golden Bridge.
- **moteur_gsg/core/css** — active/runtime — CSS package root.
- **moteur_gsg/core/css/base** — active/runtime — CSS base layer (reset, body chrome, typography, byline, hero scaffold, brand-shot).
- **moteur_gsg/core/css/components** — active/runtime — CSS components layer (argument lines, mechanism nodes, atlas hero, system-map, intro/proof).
- **moteur_gsg/core/css/responsive** — active/runtime — CSS responsive + animations layer (@keyframes, prefers-reduced-motion, breakpoints).
- **moteur_gsg/core/design_grammar_loader** — active/runtime — Design Grammar Loader V30 — branches design_grammar V30 into Mode 1.
- **moteur_gsg/core/design_tokens** — active/runtime — Deterministic design tokens — turns Brand DNA / Design Grammar / AURA into compact tokens.
- **moteur_gsg/core/doctrine_planner** — active/runtime — Constructive doctrine pack — turns audit doctrine into a creation contract (applicable criteria, evidence policy, copy directives, renderer directives).
- **moteur_gsg/core/fact_assembler** — active/runtime — Fact-list selection + proof-strip rendering — pulls `allowed_facts` from plan evidence pack.
- **moteur_gsg/core/hero_renderer** — active/runtime — Hero-visual variant dispatch.
- **moteur_gsg/core/html_escaper** — active/runtime — HTML-escaping micro-helpers.
- **moteur_gsg/core/impeccable_qa** — active/runtime — Impeccable post-render QA layer for the controlled GSG renderer.
- **moteur_gsg/core/intake_wizard** — active/runtime — Deterministic GSG intake/wizard contract — turns rough user request into complete BriefV2 (V27.2-E).
- **moteur_gsg/core/legacy_lab_adapters** — active/runtime — Explicit adapters for the V26.Z growth-site-generator legacy lab.
- **moteur_gsg/core/minimal_guards** — active/qa — Deterministic guards for the minimal GSG path (V26.AH Day 5).
- **moteur_gsg/core/page_renderer_orchestrator** — active/runtime — Public entry: `render_controlled_page(plan, copy_doc)` dispatches listicle vs component pages.
- **moteur_gsg/core/pattern_library** — active/runtime — Structured pattern library — small, deterministic pattern packs replacing prompt dumping.
- **moteur_gsg/core/pipeline_sequential** — **legacy**/runtime — Pipeline 4 stages séquentiels (V26.AF Sprint AF-1.B.2) — Strategy → Copy → Composer → Polish. **NOT default since V26.AG**.
- **moteur_gsg/core/pipeline_single_pass** — active/runtime — Single-pass Sonnet pipeline (V26.AA Sprint 3) — 1 call Sonnet → HTML (default Mode 1).
- **moteur_gsg/core/planner** — active/runtime — Deterministic page planner — decides structure before the LLM writes copy.
- **moteur_gsg/core/prompt_assembly** — active/runtime — Short prompt (≤10K chars hard limit) for Mode 1 COMPLETE.
- **moteur_gsg/core/section_renderer** — active/runtime — Component-section + component-page assembly.
- **moteur_gsg/core/visual_intelligence** — active/runtime — Visual intelligence contracts — translates context+doctrine into AURA input, creative director seed, golden bridge query (no LLM).
- **moteur_gsg/core/visual_system** — active/runtime — V27.2-G deterministic visual system contract — emits `gsg-visual-system-v27.2-g` + `gsg-premium-visual-layer-v27.2-g` markers.

### 3.20 `moteur_gsg/modes` (16 modules)

- **moteur_gsg/modes** — active/runtime — 5 situations type GSG (V26.AH minimal).
- **moteur_gsg/modes/mode_1** — active/runtime — Mode 1 PERSONA NARRATOR — split sub-package.
- **moteur_gsg/modes/mode_1/api_call** — active/runtime — Sonnet API call adapters — re-exports `pipeline_single_pass` wrappers.
- **moteur_gsg/modes/mode_1/orchestrator** — active/runtime — Master pipeline for Mode 1 — uses the root `client_context` router (PIVOT V26.AC).
- **moteur_gsg/modes/mode_1/output_parsing** — active/runtime — HTML extraction helpers for Mode 1 responses.
- **moteur_gsg/modes/mode_1/philosophy_bridge** — active/runtime — Golden Design Bridge cache + aesthetic-vector extraction.
- **moteur_gsg/modes/mode_1/prompt_assembly** — active/runtime — Mode 1 prompt assembly entry point — returns ≤8K-char prompt (V26.AF GUARD).
- **moteur_gsg/modes/mode_1/prompt_blocks** — active/runtime — Prompt block formatters — `_format_*_block` helpers (LITE variant active, FULL variant quarantined inert).
- **moteur_gsg/modes/mode_1/runtime_fixes** — active/qa — Runtime font / design-grammar fix-ups for Mode 1.
- **moteur_gsg/modes/mode_1/vision_selection** — active/runtime — Vision input picker — selects ≤N screenshots from per-page artefacts.
- **moteur_gsg/modes/mode_1/visual_gates** — active/qa — **Anti-AI-slop visual pattern detection** + repair via regex on CSS signatures.
- **moteur_gsg/modes/mode_1_complete** — active/runtime — Mode 1 COMPLETE — canonical GSG autonomous LP generation. Calls the full controlled pipeline.
- **moteur_gsg/modes/mode_2_replace** — active/runtime — REPLACE V26.AD — refonte d'une page existante avec audit comparatif (~25-30% des cas).
- **moteur_gsg/modes/mode_3_extend** — active/runtime — EXTEND V26.AD — concept nouveau pour client existant (~15-20% des cas).
- **moteur_gsg/modes/mode_4_elevate** — active/runtime — ELEVATE V26.AD — challenger DA via inspirations URLs (~5-10% des cas).
- **moteur_gsg/modes/mode_5_genesis** — active/runtime — GENESIS V26.AD — brief seul sans URL existante (<5% des cas).

### 3.21 `moteur_gsg/orchestrator` (1 module)

- **moteur_gsg/orchestrator** — active/runtime — **Canonical public GSG API** — single entrypoint for `generate_lp()` across all modes (1-5).

### 3.22 `moteur_multi_judge` (6 modules)

- **moteur_multi_judge** — active/qa — Multi-juge unifié sur doctrine V3.2 (V26.AA).
- **moteur_multi_judge/judges** — active/qa — Judges individuels.
- **moteur_multi_judge/judges/doctrine_judge** — active/qa — **Doctrine Judge V26.AA** — juge unifié sur les 54 critères V3.2 (racine partagée Audit + GSG).
- **moteur_multi_judge/judges/humanlike_judge** — active/qa — Humanlike Judge V26.AE — wraps `skills/growth-site-generator/scripts/gsg_humanlike_audit.py`.
- **moteur_multi_judge/judges/implementation_check** — active/qa — Implementation Check V26.AE — wraps `skills/growth-site-generator/scripts/fix_html_runtime.py` for runtime bug detection.
- **moteur_multi_judge/orchestrator** — active/qa — Multi-Judge Orchestrator V26.AA Sprint 3 — 3 complementary judges (doctrine 70%, humanlike 30%, implementation_check).

### 3.23 `scripts` (19 modules)

- **scripts/_test_weglot_listicle_V26AE** — active/qa — End-to-end smoke test for the Weglot listicle pipeline.
- **scripts/audit_capabilities** — active/infrastructure — **Anti-oubli auto-discovery** — scans repo and produces `CAPABILITIES_REGISTRY.json` + `CAPABILITIES_SUMMARY.md`.
- **scripts/build_bloc_v3_3** — active/infrastructure — Build `playbook/bloc_*_v3-3.json` from existing `bloc_*_v3.json` files.
- **scripts/check_gsg_canonical** — active/qa — Validate the canonical GSG boundary without generating an LP.
- **scripts/check_gsg_component_planner** — active/qa — Smoke-test V27.2-B GSG component planner.
- **scripts/check_gsg_controlled_renderer** — active/qa — Smoke-test the canonical GSG controlled renderer.
- **scripts/check_gsg_creative_route_selector** — active/qa — Check V27.2-G structured Golden/Creative route selector.
- **scripts/check_gsg_intake_wizard** — active/qa — Check the canonical GSG intake/wizard path.
- **scripts/check_gsg_visual_renderer** — active/qa — Smoke-test V27.2-G GSG visual renderer (4 cases: weglot listicle, weglot advertorial, japhy pdp, stripe pricing).
- **scripts/client_context** — active/infrastructure — **ROUTER RACINE GrowthCRO** (V26.AC Sprint F) — single read-only router that knows where every per-client artefact lives.
- **scripts/compare_doctrine_v3_v3_3** — active/infrastructure — Deterministic comparison V3.2.1 vs V3.3 doctrine per-criterion.
- **scripts/doctrine** — active/infrastructure — Doctrine Loader (V26.Z W4) — loads `playbook/*.json` + applies applicability matrix.
- **scripts/lint_code_hygiene** — active/infrastructure — Mechanical hygiene gate — enforces `docs/doctrine/CODE_DOCTRINE.md`.
- **scripts/migrate_v27_to_supabase** — active/infrastructure — Migrate V27 static dataset to Supabase V28.
- **scripts/precategorize_proposals** — active/infrastructure — Pre-categorize 69 audit-based doctrine proposals for Mathis review.
- **scripts/run_gsg_full_pipeline** — active/onboarding — **Canonical GSG intake runner** — conversational orchestrator for FULL GSG workflow.
- **scripts/test_agency_audits** — active/infrastructure — Smoke test for `audit_gads` + `audit_meta` modules.
- **scripts/test_webapp_v27** — active/infrastructure — Playwright headless smoke test for V27 Command Center.
- **scripts/update_architecture_map** — active/infrastructure — AST scan generator for `WEBAPP_ARCHITECTURE_MAP.yaml` (preserves human-curated fields between regens).

### 3.24 `skills/growth-site-generator` (10 modules) — **ALL LEGACY**

- **skills/growth-site-generator/scripts/aura_compute** — **legacy**/runtime — AURA Compute — Design Token Calculator (wrapped via `legacy_lab_adapters`).
- **skills/growth-site-generator/scripts/aura_extract** — **legacy**/runtime — AURA Extract — Design DNA Extraction from HTML pages.
- **skills/growth-site-generator/scripts/creative_director** — **legacy**/runtime — GSG Creative Director V26.Z E2 — produces 3 named visual theses.
- **skills/growth-site-generator/scripts/fix_html_runtime** — **legacy**/qa — Patches LPs broken by counter-without-JS. Used by `moteur_multi_judge/judges/implementation_check`.
- **skills/growth-site-generator/scripts/golden_design_bridge** — **legacy**/runtime — Cross-category aesthetic matching.
- **skills/growth-site-generator/scripts/gsg_best_of_n** — **legacy**/runtime — V26.Z P2 — génère N LPs (1 par route Safe/Premium/Bold).
- **skills/growth-site-generator/scripts/gsg_humanlike_audit** — **legacy**/qa — V26.Z W1.b solo judge on 8 human dimensions. Wrapped by `humanlike_judge`.
- **skills/growth-site-generator/scripts/gsg_multi_judge** — **legacy**/qa — Legacy V26.Z W1 — 2 judges + Sonnet arbitration. **Superseded by `moteur_multi_judge/orchestrator`**.
- **skills/growth-site-generator/scripts/gsg_pipeline_sequential** — **legacy**/runtime — V26.Z P1 — 4 stages chained (Strategy → Copy → Composer → Polish). Superseded by `moteur_gsg/core/pipeline_sequential`.
- **skills/growth-site-generator/scripts/scrap_inspiration** — **legacy**/runtime — V26.Y.7 scrap_inspiration.

### 3.25 `skills/site-capture` (82 modules)

> Largest package. Mix of active scripts feeding the audit pipeline + 9 archived/deprecated (`_archive_deprecated_2026-04-19/*`) that are still tagged active in the architecture export.

**Archived (still marked `active` in export — see hygiene gap)**:
- `_archive_deprecated_2026-04-19/apify_enrich` — Enrichit un `capture.json` natif avec les données visuelles Apify.
- `_archive_deprecated_2026-04-19/build_dashboard_v12` — Consolidate every client/page audit into a single JSON.
- `_archive_deprecated_2026-04-19/component_detector` — V12 Phase 5.2: Component Detector multi-signal.
- `_archive_deprecated_2026-04-19/component_perception` — Oracle V11 Perception Sémantique & Spatiale.
- `_archive_deprecated_2026-04-19/component_validator` — V12 Phase 5.4 Critic/Validator.
- `_archive_deprecated_2026-04-19/perception_pipeline` — V12 Phase 5 Orchestrateur Layer 2 Perception.
- `_archive_deprecated_2026-04-19/reco_enricher` — V12 Phase 4.5 enrichit les recommandations.
- `_archive_deprecated_2026-04-19/score_site` — Agrégateur multi-pages.
- `_archive_deprecated_2026-04-19/spatial_scoring` — Spatial enrichment layer for V9.

**Active scoring/perception scripts** (legacy lineage, still consumed):
- `analyze_capture` — Helpers pour lire un SiteCapture et servir de base au scoring V3.
- `audit_fleet_health` — V25.A audit santé fleet existante.
- `audit_funnel_steps` — V26.X.5 audit per-step tunnel.
- `batch_rescore` — Re-score toutes les pages de tous les clients.
- `batch_site` — Batch scoring 6 blocs pour tous les clients.
- `brand_dna_diff_extractor` — GSG Brand DNA Diff V26.Z E1 — ajoute le 4e quadrant "Fix" au brand_dna.
- `brand_dna_extractor` — V29 GSG Brand DNA Extractor — Python+LLM hybrid (palette/voice/diff E1 per client). *Outputs*: `data/captures/<client>/brand_dna.json`.
- `build_growth_audit_data` — **Build consolidated JS bundle for V27 Command Center** (12 MB, 56 clients).
- `capture_site` — Orchestrateur hybride.
- `compress_flow_steps` — V26.X.3 compresse flow_summary steps.
- `criterion_crops_v2` — V20.CAPTURE C3 mapping critère → crop.
- `design_grammar` — Design Grammar V30 extractor — per-client design system tokens (colors, fonts, spacing, components patterns).
- `detect_canonical_tunnel` — V26.X.2 detect canonical tunnel par client.
- `discover_pages_v25` — V25.B Discovery + Classification intelligente.
- `dom_vision_reconciler` — V20.CAPTURE C1'b réconciliation DOM ↔ Vision.
- `eclaireur_llm` — P11.11 (V19) Éclaireur LLM Discovery & Routing.
- `enrich_scores_with_evidence` — V26.A.2 post-process `score_*.json` files to attach Evidence Ledger entries.
- `evidence_ledger` — **V26.A Evidence Ledger** — verifiable proofs per score and reco (criterion-level provenance).
- `experiment_engine` — V27 A/B test specs + sample size calculator + guardrails. Reality Layer dependent.
- `geo_audit` — V24 axe 4 GEO audit (Generative Engine Optimization).
- `geo_readiness_monitor` — V31+ GEO Readiness Monitor multi-engine (ChatGPT + Perplexity + Claude + AI Overviews).
- `golden_bridge` — Golden Dataset Bridge for `reco_enricher` V16 — matches a target page against 29 golden references.
- `golden_calibration_check` — V21.F.3 Golden Calibration Loop.
- `golden_differential` — P11.2 Golden Differential Engine (online helper).
- `golden_percentiles` — P11.2 Golden Differential Engine (offline batch).
- `intent_detector_v13` — Couche 2 Oracle Perception V13 — per-element intent (CTA, trust, social_proof, …).
- `learning_layer_v29_audit_based` — V29 Sprint B Learning Layer Audit-Based — 69 proposals pending review for V3.3.
- `multi_judge` — **legacy**/qa — V26.D Multi-judge — disagreement tracking. Superseded by `moteur_multi_judge/orchestrator`.
- `overlay_burn` — V12 Phase 5.3b Overlay burned-in PNG.
- `overlay_renderer` — V12 Phase 5.3 Overlay honnête renderer.
- `page_cleaner` — V12 Phase 5.1 nettoyage post-capture.
- `page_context` — P11.5/P11.9 (V19) PageContext threadé + contrats Pydantic 4 stages.
- `page_type_filter` — Source of truth for pageType applicability (V12 doctrine v3.1.0).
- `perception_bridge` — Bridge Layer 2 Perception → Scoring V3.
- `perception_inject` — Injecte les composants perçus dans les données que les scoreurs consomment.
- `pick_diverse_pages` — sélection équitable de N pages pour batch reco ciblé.
- `playwright_capture_v2` — V20.CAPTURE C1c robust 2-pass Playwright capture.
- `project_snapshot` — V12 full project state snapshot.
- `reality_layer` (+ submodules `base, catchr, clarity, google_ads, meta_ads, orchestrator, shopify`) — V26.C Reality Layer — 6 connecteurs **(these are the legacy mirrors; growthcro/reality is the canonical path)**.
- `reco_lifecycle` — V26.B Reco Lifecycle — state machine pour le cycle de vie des recos.
- `reco_quality_audit` — Scan des `recos_v13_final.json` existants et quality score.
- `recos_dedup` — V23.B semantic dedup post-LLM.
- `recos_rewrite_fr` — V23.2.fr rewrite ciblé style FR consultant.
- `run_capture` — Apify orchestrateur.
- `run_discover` — Apify orchestrateur découverte.
- `run_spatial_capture` — Lance `spatial_capture_v9.js` pour une page.
- `scent_trail_analyzer` — P11.15 (V19) mesure cross-page scent trail CRO.
- `schwartz_detector` — V12 S-05 Schwartz Awareness Scale auto-detection.
- `score_applicability_overlay` — P2.A doctrine v3.2.0-draft.
- `score_coherence` — Scorer Bloc 4 Cohérence V3.
- `score_contextual_overlay` — P1.B doctrine v3.2.0-draft.
- `score_funnel` — V21.H score le funnel COMPLET (vs juste l'intro).
- `score_hero` — Scorer Hero V3.
- `score_page_type` — Orchestrateur pageType-aware V12 doctrine v3.1.0.
- `score_persuasion` — Scorer Bloc 2 Persuasion V3.
- `score_psycho` — Scorer Psycho V3.
- `score_site` — Agrégateur multi-pages.
- `score_tech` — Scorer Tech V3.
- `score_universal_extensions` — Scorers pour les 8 critères universels ajoutés en doctrine v3.1.0.
- `score_utility_banner` — Scorer Bloc 7 Utility Elements V3.
- `spatial_bridge` — Bridge entre `spatial_v9.json` et les 6 scorers existants.
- `spatial_enrich` — Corrige `capture.json` avec les données spatiales Ghost.
- `usp_detector` — V21.F.2 USP detector — extracts USPs from hero + above-the-fold copy. *Outputs*: `data/captures/<client>/<page>/usp_signals.json`.
- `validate_utility_banner` — Validation Étape 1a Bloc 7 UTILITY_BANNER.
- `vision_spatial` — V20.CAPTURE C1' Claude Vision Haiku 4.5 comme extracteur spatial.
- `web_vitals_adapter` — V12 S-04 adapter Web Vitals.

---

## 4. Skills integration

> Blueprint doc: `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` · version 1.0 · last_updated 2026-05-11 · task ref Issue #17.

### 4.1 Combo packs (3 disjoint contexts)

#### `audit_run`
- **Skills (always)**: `claude-api`, `cro-methodology`
- **On-demand additions**: `form-cro`, `page-cro`, `signup-flow-cro`, `onboarding-cro`, `paywall-upgrade-cro`, `popup-cro`
- **Max session**: 4
- **Activation**: auto on `python -m growthcro.cli.capture_full <url> <client>`
- **Modules impacted**: `growthcro/recos/orchestrator`, `growthcro/recos/prompts`, `growthcro/scoring/cli`
- **Pipeline stage**: `audit_pipeline.recos`
- **Rationale**: doctrine V3.2.1 (→ V3.3 post #18) reste UPSTREAM. `cro-methodology` enrichit en aval (POST-PROCESS). On-demand déclenchés selon `page_type`.

#### `gsg_generation`
- **Skills**: `frontend-design`, `brand-guidelines`, `Emil Kowalski Design Skill`, `Impeccable`
- **Max session**: 4
- **Activation**: auto on `python -m moteur_gsg.orchestrator --mode <complete|replace|extend|elevate|genesis>`
- **Modules impacted**: `moteur_gsg/core/visual_system`, `moteur_gsg/core/page_renderer_orchestrator`, `moteur_gsg/core/brand_intelligence`, `moteur_gsg/core/design_grammar_loader`, `moteur_gsg/modes/mode_1/visual_gates`, `moteur_gsg/modes/mode_1/runtime_fixes`, `moteur_gsg/core/minimal_guards`
- **Pipeline stages**: `gsg_pipeline.visual_system`, `gsg_pipeline.controlled_renderer`, `gsg_pipeline.qa_runtime`, `gsg_pipeline.minimal_gates`
- **Rationale**: 4 skills = direction artistique × couleur/typo per-client × motion × QA polish. Cônes d'action distincts → pas de signaux contraires.
- **Anti-regression**: hard assert prompt persona_narrator ≤ 8K chars (cf. anti-pattern #1 CLAUDE.md).

#### `webapp_nextjs`
- **Skills**: `frontend-design`, `web-artifacts-builder`, `vercel-microfrontends`, `Figma Implement Design`
- **Max session**: 4
- **Activation**: manual at start of sprint webapp V28 (Epic #21)
- **Modules impacted**: `growthcro/api/server`
- **Pipeline stages**: `webapp.stages_v28_nextjs_target`
- **Rationale**: `frontend-design` pour composants, `web-artifacts-builder` pour shadcn/Tailwind, `vercel-microfrontends` pour archi multi-zones, Figma si Mathis fournit un design.

### 4.2 Essentials (always-loaded baseline)

| name | source | installed | combo |
|---|---|---|---|
| `frontend-design` | anthropic-builtin | true | gsg_generation + webapp_nextjs |
| `brand-guidelines` | anthropic-builtin | true | gsg_generation |
| `web-artifacts-builder` | anthropic-builtin | true | webapp_nextjs |
| `vercel-microfrontends` | skills.sh/vercel/microfrontends/vercel-microfrontends | **false** (install_cmd: `npx skills add https://github.com/vercel/microfrontends --skill vercel-microfrontends`) | webapp_nextjs |
| `cro-methodology` | skills.sh/wondelai/skills/cro-methodology | **false** (install_cmd: `npx skills add https://github.com/wondelai/skills --skill cro-methodology`) | audit_run |
| `Emil Kowalski Design Skill` | emilkowal.ski/skill | **false** (install_cmd: `npx skills add emilkowalski/skill`) | gsg_generation |
| `Impeccable` | impeccable.style | **false** (install_cmd: `npx skills add pbakaus/impeccable`) | gsg_generation |
| `Figma Implement Design` | figma (nocodefactory list) | true | webapp_nextjs |

> **4 of 8 essentials are NOT installed yet** — `vercel-microfrontends`, `cro-methodology`, `Emil Kowalski Design Skill`, `Impeccable`.

### 4.3 On-demand (slash-command activated)

| name | source | trigger | page types |
|---|---|---|---|
| `page-cro` | coreyhaines31 | `/page-cro` on any audited page | home, pdp, landing, all |
| `form-cro` | coreyhaines31 | `/form-cro` when page_type = `lp_leadgen` \| `signup` \| `pricing-with-form` | — |
| `signup-flow-cro` | coreyhaines31 | `/signup-flow-cro` for SaaS B2B multi-step signup | — |
| `onboarding-cro` | coreyhaines31 | `/onboarding-cro` when page_type = onboarding | — |
| `paywall-upgrade-cro` | coreyhaines31 | `/paywall-upgrade-cro` for SaaS freemium pricing/paywall | — |
| `popup-cro` | coreyhaines31 | `/popup-cro` when audit detects popups (`capture.json.has_popup=true`) | — |

### 4.4 Excluded (audited + rejected)

| name | source | rationale |
|---|---|---|
| `lp-creator` | anthropic-builtin | `moteur_gsg/orchestrator` is more evolved (12 stages vs 30 critique auto-eval). Out-of-band autorisé. |
| `lp-front` | anthropic-builtin | `moteur_gsg/core/visual_system V27.2-G` + `page_renderer_orchestrator` produisent le front avec plus de couches. |
| `theme-factory` | anthropic-builtin | 10 thèmes pre-set imposent une grille → conflit avec Brand DNA per-client. |
| `Taste Skill` | third-party | Impose un parti pris visuel dark/premium → conflit Brand DNA per-client. Signaux contraires empiriques. |
| `Canvas Design` | anthropic-builtin | Hors scope CRO core (visuels statiques marketing). |

### 4.5 Anti-cacophonie rules (verbatim, 8 rules)

1. 1 parti pris visuel par projet: ne JAMAIS activer `Taste Skill` + `brand-guidelines` simultanément.
2. Skills design en `/nom` ponctuel, pas auto-load permanent hors combo pack.
3. Limite Claude Code = 8 skills max session, donc combos disjoints (audit / GSG / webapp).
4. Skills CRO methodo en POST-PROCESS, jamais pre-prompt mega-system (anti-pattern #1 V26.AF).
5. Notre doctrine V3.2.1 → V3.3 reste UPSTREAM. Skills externes en aval, jamais remplacer source.
6. `lp-creator` + `lp-front` exclus → ne pas charger pour générer une LP. Utiliser `moteur_gsg/orchestrator`.
7. `theme-factory` exclu → ne pas appliquer un thème. Utiliser `brand-guidelines` + `design_grammar_loader`.
8. `Canvas Design` exclu → pas pour GSG. Utiliser `visual_system V27.2-G`.

---

## 5. Mermaid views — architectural diagrams (6)

### 5.1 "1. Global view — the whole program in one diagram"

Five subgraphs (Onboarding, Audit Engine, GSG Engine, QA/Multi-Judge, Webapp Surface, Reality/Experiment/Learning, Infrastructure) wired together with the audit → reco → evidence → V27 HTML and intake → brief → planner → renderer → multi-judge paths. Pending nodes (Webapp V28 Next.js, Reality connectors live, V30 Bayesian) are highlighted dashed yellow. Visualizes the full closed loop: Audit → Action → Mesure → Apprentissage → Génération → Monitoring.

### 5.2 "2. Audit pipeline — capture to reco"

Linear flowchart from `client URL + slug` through `add_client → enrich_client → capture_full → orchestrator → scorer → perception → scoring (persist + specific) → score_*.json artefacts → recos/orchestrator + Anthropic → recos_enriched.json → reco_lifecycle → growth_audit_data.js` (12 MB · 56 clients · 185 pages). Each artefact is highlighted as a node (`discovered_pages_v25.json`, `spatial_v9 + capture + page.html + screenshots/`, `perception_v13.json`, 6 pillar scores + page_type, `evidence_ledger.json`, `recos_enriched.json`, final consolidated JS bundle).

### 5.3 "3. GSG pipeline — V27.2-G controlled path"

12-stage pipeline: `raw user request → intake_wizard → brief_v2 (builder + prefiller + validator) → context_pack + doctrine_planner → visual_intelligence → creative_route_selector V27.2-F (with AURA tokens + Golden Bridge legacy adapters) → visual_system V27.2-G → design_tokens + design_grammar_loader → planner + component_library + pattern_library → copy_writer (Sonnet JSON slots only) → page_renderer_orchestrator + hero/section/component renderers + CSS layers + Emil Kowalski animations → runtime_fixes → visual_gates anti-AI-slop → minimal_guards → impeccable_qa → LP HTML`. Optional multi-judge + regression gate at the end.

### 5.4 "4. Multi-Judge — post-render QA layer"

LP HTML → `moteur_multi_judge/orchestrator` → 3 parallel judges (`doctrine_judge V3.2.1` at 70% weight, `humanlike_judge` at 30%, `implementation_check` for runtime bugs) → weighted aggregation with killer veto → `multi_judge.json` artefact → decision: `final_score_pct ≥ 70 + killers = 0?` → YES Ship (Weglot V27.2-D baseline 70.9) / NO `repair_loop` legacy lab → iterate back.

### 5.5 "5. Webapp — V27 HTML today, V28 Next.js target"

Two subgraphs side by side. **V27** (active, 56 clients): audit pipeline → `data/captures/<client>/<page>/*` (~150 artefacts/page) → `build_growth_audit_data` → 12 MB `growth_audit_data.js` → `GrowthCRO-V27-CommandCenter.html` (11 panes: Audit/Reco/GSG/…) with FastAPI server as optional programmatic interface. **V28** (target, Epic #6, all pending dashed): Supabase EU auth + tables → 5 microfrontends (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) coordinated by `vercel-microfrontends` routing, fed by `growthcro/api/server` via Vercel edge functions. Same data tree feeds both.

### 5.6 "6. Reality / Experiment / Learning loop"

`56 audits sur disque (data/captures/*) → learning_layer_v29_audit_based → 69 proposals V29 → Mathis review (accept/reject/defer) → playbook/bloc_*_v3-3.json doctrine V3.3 CRE fusion (pending)`. Parallel **Reality subgraph** (all pending): GA4/Meta/Google/Shopify/Clarity connectors → `Reality collector` → `data/reality/<client>/*.json`. **Experiment subgraph**: `recos/orchestrator → experiment_engine → A/B test specs → Reality collector → reality data → Learning V30 Bayesian update → data-driven doctrine proposals (≥10 by Q4) → Mathis review → V3.3 → audit engine consumes new doctrine (56 clients stay on V3.2.1 until next audit)`.

---

## 6. Cross-references — what's missing from the Next.js webapp

> **Comparing architecture (`window.ARCH`) against current `webapp/apps/shell/` (single Next.js app, `@growthcro/shell` v0.28.0).**

### 6.1 Microfrontend topology — 5 → 1 collapse

| Architecture (V28 design) | Webapp reality (2026-05-13) | Status |
|---|---|---|
| `shell (3000)` DEEP — auth + nav + dashboard + realtime runs | `webapp/apps/shell/` (exists, has `app/page.tsx`) | **PRESENT (consolidated)** |
| `audit-app (3001)` DEEP — clients + audits + scores + recos | `webapp/apps/shell/app/clients/`, `app/audits/[clientSlug]/[auditId]/` | **MERGED into shell** |
| `reco-app (3002)` DEEP — recos browser + filters + priority counts | `webapp/apps/shell/app/recos/`, `app/recos/[clientSlug]/` | **MERGED into shell** |
| `gsg-studio (3003)` DEEP — brief wizard + LP preview + multi-judge stage strip | `webapp/apps/shell/app/gsg/page.tsx` (single page) | **MERGED, surface depth unclear** |
| `reality-monitor (3004)` PLACEHOLDER — connectors panel GA4/Meta/Google/Shopify/Clarity | `webapp/apps/shell/app/reality/page.tsx`, `app/reality/[clientSlug]/` | **MERGED, still placeholder-shaped** |
| `learning-lab (3005)` PLACEHOLDER — V29+V30 proposals + accept/reject/defer | `webapp/apps/shell/app/learning/`, `app/learning/[proposalId]/page.tsx` | **MERGED, surface depth unclear** |
| `vercel-microfrontends` routing | **absent** — single Next.js shell, no microfrontends.json | **NOT IMPLEMENTED** |

**Gap**: the V28 design was 5+ microfrontends federated via `vercel-microfrontends` routing on ports 3000-3005; the webapp ships as a single Next.js shell with 12 route groups. The combo pack `webapp_nextjs` lists `vercel-microfrontends` as essential, but skill is **not installed**.

### 6.2 Routes present in webapp NOT in architecture pipelines

These webapp routes exist but have no pipeline counterpart in the architecture export:
- `app/audit-gads/` — surfaces `growthcro/audit_gads/*` (4 modules in architecture, but no pipeline definition)
- `app/audit-meta/` — surfaces `growthcro/audit_meta/*` (4 modules, no pipeline)
- `app/funnel/[clientSlug]/` — funnel UX (consumes `score_funnel.py` output from skills/site-capture, no pipeline named "funnel")
- `app/doctrine/` — UI on top of `playbook/*.json` (no pipeline; consumes V3.2.1/V3.3 directly)
- `app/clients/[slug]/dna/` — Brand DNA viewer (consumes `data/captures/<client>/brand_dna.json` artefact 2.10, no pipeline)
- `app/settings/`, `app/login/`, `app/auth/`, `app/privacy/`, `app/terms/` — auth + legal scaffolding (Supabase auth, listed in webapp_v28 description but not enumerated as pipelines)

### 6.3 Pipeline stages NOT visible in webapp UI

These architecture stages have no corresponding webapp surface beyond raw data display:
1. **`audit_pipeline.discovery`** (research/discovery + discover_pages_v25) — no UI to trigger or visualize discovery; `data/captures/<client>/discovered_pages_v25.json` artefact (2.13) has no consumer in webapp.
2. **`audit_pipeline.evidence`** (evidence_ledger) — `evidence_ledger.json` artefact (2.4) has no dedicated UI tab; data may be folded into audit detail but not surfaced as proof per criterion.
3. **`gsg_pipeline` 12 stages** — `app/gsg/page.tsx` is a single page; architecture calls for `gsg-studio` DEEP with "brief wizard + LP preview + multi-judge stage strip".
4. **`multi_judge`** pipeline — no `judges/` route despite `components/judges/` folder existing; multi_judge.json artefact (2.2) consumption unclear.
5. **`reality_loop.experiment_propose/record/measure_outcomes`** — experiments have no webapp surface (no `/experiments` route); only Reality monitor lists are sketched.
6. **`reality_loop.learning_v30_data_driven`** — V30 Bayesian outputs (`data/learning/data_driven_proposals/*`) have no route; `app/learning/` likely only shows V29 audit-based proposals (artefact 2.15) which are pre-review.

### 6.4 Data artefacts NOT consumed by webapp

| Artefact | Status in webapp |
|---|---|
| 2.1 `_briefs_v2/*` | **Not consumed** — GSG brief storage, no UI |
| 2.2 `_pipeline_runs/<run>/multi_judge.json` | **Not consumed** — judges surface absent |
| 2.4 `evidence_ledger.json` | **Likely not surfaced** — no dedicated UI |
| 2.9 `spatial_v9.json` | **Internal** — perception input only, no UI |
| 2.10 `brand_dna.json` | Partial — `app/clients/[slug]/dna/` exists |
| 2.11 `client_intent.json` | **Not surfaced** |
| 2.12 `design_grammar/*` | **Not surfaced** |
| 2.13 `discovered_pages_v25.json` | **Not surfaced** |
| Reality artefacts (`data/reality/<client>/*`) | UI = placeholder |
| Experiment artefacts (`data/experiments/<client>/*`) | **Not surfaced** |
| V30 data-driven proposals (`data_driven_proposals/*`) | **Not surfaced** |

### 6.5 API surface — FastAPI on Fly.io vs Next.js route handlers

Architecture (`webapp_v28.backend`) chose **FastAPI on Railway/Fly.io** because Vercel edge 30 s limit is incompatible with long-running Playwright capture + LLM scoring. The webapp ships with **Next.js route handlers** (`app/api/audits/route.ts`, `app/api/clients/[id]/route.ts`, `app/api/gsg/[slug]/html/route.ts`, `app/api/learning/proposals/review/route.ts`, `app/api/recos/[id]/route.ts`, `app/api/screenshots/[client]/[page]/[filename]/route.ts`, `app/api/team/invite/route.ts`). The architecture's `NEXT_PUBLIC_API_BASE_URL` → Fly.io pattern is **not implemented**: no `growthcro/api/server` is exposed in production, and long pipelines are not callable from the webapp.

### 6.6 Missing skill installations

Architecture essentials marked `installed: false`:
- `vercel-microfrontends` — explains §6.1 gap.
- `cro-methodology` — POST-PROCESS layer for `audit_pipeline.recos` absent.
- `Emil Kowalski Design Skill` — motion layer for `moteur_gsg/core/animations` absent (architecture wired it; module exists, skill not).
- `Impeccable` — QA polish for `moteur_gsg/core/impeccable_qa` absent.

### 6.7 Legacy modules still loaded

18 modules tagged `legacy`, including:
- All 6 in `growthcro/gsg_lp/*` — the mega-prompt path that V26.AF regressed by -28 pts (anti-pattern #1). Still on disk but should never be invoked alongside `moteur_gsg/orchestrator`.
- All 10 in `skills/growth-site-generator/scripts/*` — superseded by `moteur_gsg/core/*` + `moteur_multi_judge/*`, kept only via `legacy_lab_adapters`.
- `moteur_gsg/core/pipeline_sequential` + `brief_v15_builder` — experimental V26.AF, not default since V26.AG.
- `skills/site-capture/scripts/multi_judge` — superseded by `moteur_multi_judge/orchestrator`.

### 6.8 Reality Layer parallel implementations

Architecture has Reality Layer **twice**:
- `growthcro/reality/*` (10 modules, canonical, post-promotion)
- `skills/site-capture/scripts/reality_layer/*` (7 modules, legacy mirror)

Both packages list the same 6 connectors (GA4/Catchr/Meta/Google/Shopify/Clarity) and same orchestrator function. Webapp `app/reality/` should consume only the canonical `growthcro/reality/*` path; the architecture map doesn't flag the duplicate as resolved.

---

## 7. What this tells us about the canonical webapp Mathis envisioned

**The product Mathis is building** is a closed-loop CRO consultancy engine for the 100+ clients of agency Growth Society. It's NOT a static dashboard, NOT a one-shot audit tool — it's a six-stage automation: (1) **Onboard** a client URL via `add_client + enrich_client + discovered_pages_v25`; (2) **Audit** with the 7-stage `audit_pipeline` producing 17 canonical artefacts per page (capture/perception/6 pillars + page-type + evidence + 3045 recos across the fleet); (3) **Generate** elevated landing pages via the 13-stage controlled `gsg_pipeline` with 5 modes (complete/replace/extend/elevate/genesis) and a hard 8K-char prompt guard; (4) **QA** every output through `multi_judge` with 70/30 weighting + killer veto; (5) **Measure** real impact via the 6-connector Reality Layer feeding the Experiment Engine; (6) **Learn** via dual-track doctrine evolution — `V29 audit-based` (69 proposals already cooked) and `V30 Bayesian data-driven` (target ≥10 by Q4). The doctrine itself (V3.2.1 → V3.3) is upstream of every step — it dictates which criteria fire, which recos LLM gets seeded with, which judge thresholds are applied, and which experiments are proposed. This is precisely what "consultant CRO senior automatisé" means in CLAUDE.md.

**The canonical webapp** should be the Mission Control of that loop: 5 deep microfrontends federated by `vercel-microfrontends`, a FastAPI backend on Fly.io running Playwright captures and LLM batch scoring, Supabase EU for persistence + realtime, and 11 panes from the V27 HTML elevated to a proper Next.js shell. Each microfrontend has a clear scope — audit-app surfaces the 7-stage audit pipeline with per-criterion evidence, reco-app exposes filterable backlog with priority/effort/lift, gsg-studio walks the 13-stage GSG with a brief wizard and stage strip, reality-monitor presents the credentials grid + KPI snapshots, learning-lab handles V29+V30 proposal review with accept/reject/defer side-cars. The architecture even pre-specifies port allocation (3000-3005), RLS helpers (`is_org_member`, `is_org_admin`), realtime channel (`public:runs`), and migration script (`migrate_v27_to_supabase.py` for 56 clients × 185 audits × 3045 recos).

**The gap as-shipped (2026-05-13)** is structural, not cosmetic. The webapp ships as a **single Next.js shell** (`@growthcro/shell` v0.28.0) with 12 route groups stuffed inside one app — the 5 microfrontends collapsed into one. There is **no Fly.io FastAPI backend** (the Next.js route handlers cannot run Playwright + 5-min scoring batches). There is **no `vercel-microfrontends`** topology. There is **no UI for evidence_ledger**, **no UI for experiments**, **no UI for V30 Bayesian proposals**, **no UI for multi_judge runs**, and the gsg-studio + reality-monitor + learning-lab were explicitly tagged "PLACEHOLDER" in the architecture export. **18 legacy modules** are still on disk including the entire `growthcro/gsg_lp/*` mega-prompt path that caused the V26.AF -28pt regression. **4 of 8 essential skills are not installed** (`vercel-microfrontends`, `cro-methodology`, `Emil Kowalski Design Skill`, `Impeccable`) — meaning the combo packs `audit_run` and `gsg_generation` cannot run at full strength today. The architecture export is dated 2026-05-11; the Wave A audit notes (`AUDIT_DATA_FIDELITY_2026-05-14.md`, `AUDIT_SUMMARY_2026-05-14.md`) and the current CLAUDE.md flag the webapp as **"écran de fumée"** with the data migration pointed at the wrong source. The canonical webapp Mathis envisioned is ~30% surface-area shipped; the next sprint (per `CONTINUATION_PLAN_2026-05-14.md`) is to re-anchor on `recos_enriched.json` (artefact 2.6, the V13-rich source) and the 6 pillar scores (artefact 2.8) + fix screenshots in prod, then push toward the canonical 5-microfrontend topology with a real FastAPI backend.
