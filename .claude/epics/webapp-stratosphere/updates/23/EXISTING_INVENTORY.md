# Issue #23 — Existing Building Blocks Inventory

**Date**: 2026-05-11
**Branch**: `task/23-reality-loop`
**Purpose**: Document what exists before this sprint, so we know exactly what's net-new vs. what's a thin promotion.

---

## 1. Reality Layer (V26.C / V26.AI)

**Status**: skills-domain, scaffolded with stubs, needs promotion to `growthcro/reality/`.

**Location**: `skills/site-capture/scripts/reality_layer/`

**Files** (1645 LOC total in 8 files):
- `__init__.py` (39 LOC) — package exports
- `base.py` (64 LOC) — `Connector` ABC + `RealityLayerData` dataclass + `NotConfiguredError` + `ConnectorError`. Uses `growthcro.config.config.system_env` for env vars (good — config-boundary respected).
- `catchr.py` (107 LOC) — Catchr API connector (GA4 wrapper). Uses `httpx`. Stub functional, untested live.
- `clarity.py` (92 LOC) — Microsoft Clarity Data Export connector. Free tier: last 3 days only.
- `google_ads.py` (114 LOC) — Google Ads API connector. Requires `google-ads` SDK (currently not installed → graceful error).
- `meta_ads.py` (96 LOC) — Meta Marketing API v18 connector. Uses `httpx`.
- `shopify.py` (134 LOC) — Shopify Admin GraphQL API connector. Uses `httpx`.
- `orchestrator.py` (239 LOC) — Multi-connector aggregator. Writes `data/captures/<client>/<page>/reality_layer.json`. CLI + `collect_for_page()` programmatic API.

**Connector registry**: `{catchr, meta_ads, google_ads, shopify, clarity}` (5 connectors — Catchr serves as GA4 wrapper used internally by Growth Society).

**Existing env-var convention** (good — per-client + global fallback):
- `<VAR>_<CLIENT_SLUG_UPPER>` (per-client, takes precedence)
- `<VAR>` (global fallback)

E.g.: `META_ACCESS_TOKEN_WEGLOT` or `META_ACCESS_TOKEN`.

**Gaps to address**:
- (G1) Not in `growthcro/` package — outside main app surface, harder to import from webapp API/orchestrator.
- (G2) No per-client credential validation helper (`credentials.py` requested in task spec).
- (G3) `.env.example` does not list the per-client vars — Mathis has to discover them via base.py source-reading.
- (G4) `clarity.py` uses old `import os` (only in module-level comment — actual code uses `growthcro.config`). OK.
- (G5) No "native GA4 service account JSON" connector — Catchr (third-party) is in place but task spec also wants direct GA4. Decision: keep Catchr (real Growth Society infra), add direct GA4 as a thin alt for clients without Catchr.
- (G6) `meta_ads.py` requires `META_AD_ACCOUNT_ID` separately from access token — needs better wiring (task spec asks for both).

**Promotion plan**: create thin `growthcro/reality/{base,credentials,catchr,ga4,meta_ads,google_ads,shopify,clarity,orchestrator}.py` that re-exports the skills modules + adds a credentials inspector. Avoid duplicating logic.

---

## 2. Experiment Engine (V27)

**Status**: complete in skills-domain. Sample-size calculator + spec builder + outcome importer all present. Needs promotion to `growthcro/experiment/`.

**Location**: `skills/site-capture/scripts/experiment_engine.py` (333 LOC, single-file).

**Functions**:
- `compute_sample_size(baseline_rate, mde_relative, power, alpha)` — z-test sample size for proportions. Returns `{sample_size_per_variant, sample_size_total, …}`.
- `_z_score(percentile)` — inverse normal CDF approximation (no scipy needed). Stdlib only.
- `estimate_duration_days(sample_total, daily_traffic)` — adds 14-day minimum.
- `select_guardrails(business_category)` — picks default guardrails per business_category from `DEFAULT_GUARDRAILS` (ecommerce/lead_gen/saas/default).
- `build_experiment_spec(reco, baseline_conversion_rate, daily_traffic, mde_relative, business_category, primary_metric, secondary_metrics)` — full A/B spec : hypothesis + metrics + design + statistics + ramp-up + kill-switches + outcome placeholder.
- `save_experiment_spec(spec, client, page)` — writes to `data/captures/<client>/<page>/experiments/<exp_id>.json` (atomic via `.tmp` then `replace`).
- `import_outcome(spec_path, outcome, lift, confidence, notes)` — post-run measurement update.

**Gaps to address**:
- (G7) No "runner" — no code generates A/B variants automatically from a reco. Mathis must manually craft variant B. Per task spec: variant B = generated via GSG. This sprint just provides scaffold (zero auto-trigger).
- (G8) No "recorder" — `save_experiment_spec` is a single write. No log of experiments across clients.
- (G9) Module sits in skills/ not `growthcro/` — webapp API can't easily import it.
- (G10) Hardcoded `mde_relative=0.10` default — fine but should be exposed CLI.

**Promotion plan**: `growthcro/experiment/{engine.py, runner.py, recorder.py}`. `engine.py` re-exports the skills module (sample-size + spec builder). `runner.py` produces "experiment proposals" (NOT auto-trigger). `recorder.py` indexes experiments by client+date.

---

## 3. Learning Layer V29 audit-based

**Status**: complete in skills-domain. Has produced 69 doctrine proposals from 56 curated V26 clients. Pre-categorized by `scripts/precategorize_proposals.py` for #18 review.

**Location**: `skills/site-capture/scripts/learning_layer_v29_audit_based.py` (427 LOC, single-file).

**Logic**:
1. `collect_curated_scores()` — walks 56 clients × 3.3 pages = ~185 `score_page_type.json`.
2. `extract_per_criterion_verdicts(scores)` — flattens each pillar's `kept_criteria` into a list of `{client, page_type, business_category, pillar, criterion_id, verdict, score, weight}`.
3. `aggregate_by_criterion_segment(verdicts)` — groups by `(criterion_id, business_category)`.
4. `generate_proposals(stats, min_pages=5)` — three heuristic patterns:
   - **calibrate_threshold** : `pct_critical ≥ 70%` → rule too strict
   - **tighten_threshold** : `pct_top ≥ 85%` → rule under-discriminating
   - **adjust_page_types** : `pct_na ≥ 50%` → page_type filter mismatch
5. Writes `data/learning/audit_based_stats.json` + `audit_based_proposals/<id>.json` + `audit_based_summary.md`.

**Output structure** (proposal JSON):
```json
{
  "proposal_id": "dup_v29_2026_05_11_<criterion>_calibrate_strict_<biz>",
  "type": "calibrate_threshold | tighten_threshold | adjust_page_types",
  "subtype": "...",
  "affected_criteria": [...],
  "scope": {"business_category": "..."},
  "evidence": {"n_pages_evaluated": ..., "pct_critical": ..., ...},
  "proposed_change": "...",
  "risk": "...",
  "requires_human_approval": true,
  "generated_at": "..."
}
```

**For V30 (data-driven, this sprint)**:
- We reuse the same proposal JSON shape (so review pipeline doesn't need to fork).
- We change the *input* : reality data + experiment outcomes (from `data/reality/*` and `data/captures/*/experiments/*`) instead of audit verdicts.
- We change the *update logic* : Bayesian update on V3.3 doctrine priors (vs. V29 frequentist heuristics).
- We write to `data/learning/data_driven_proposals/<iso_date>/<proposal_id>.json` (parallel folder, not overwriting V29).

---

## 4. Webapp V28 — reality-monitor + learning-lab apps

**Status**: placeholders shipped in #21. Each app has:
- `package.json` + `tsconfig.json` + `next.config.js`
- `app/layout.tsx` + `app/page.tsx` (≈ 60 LOC each, static content only)
- `lib/supabase-server.ts` (server-side Supabase client helper)

**Existing content**:
- `reality-monitor/app/page.tsx` lists 5 data sources with "pending" status pills + a "Reality loop" note pointing to Task #23.
- `learning-lab/app/page.tsx` lists 2 tracks (V29 audit-based, V30 Bayesian pending) + a note saying "this section will list proposals from `data/learning/audit_based_proposals/`".

**Webapp data layer** (`webapp/packages/data/src/`):
- `client.ts` — `getServerSupabase` + browser client helpers.
- `types.ts` — typed entities (Client, Audit, Reco, Run, etc.).
- `queries/clients.ts` — `listClientsWithStats` + `getClientBySlug` + `upsertClient`.
- `queries/runs.ts` — `listRecentRuns` + `insertRun` + `updateRunStatus` + `subscribeRuns` (realtime).
- `queries/audits.ts` + `queries/recos.ts` — similar CRUD wrappers.

**Existing Supabase schema** (`webapp/supabase/migrations/`):
- `runs` table has `type` check constraint accepting `('audit','gsg','reality','experiment')` already — Reality + Experiment runs first-class citizens.
- No dedicated `reality_snapshots` or `experiment_proposals` table yet — but `runs.metadata_json` + `runs.output_path` provide hooks.
- `recos` already has `oco_anchors_json` from #18 doctrine V3.3.

**Webapp UI primitives** (`webapp/packages/ui/src/`):
- `Card`, `Pill`, `Button`, `KpiCard`, `ScoreBar`, `RecoCard`, `ClientRow`, `NavItem`, `ConsentBanner`.

---

## 5. Sprints F-L roadmap items (strategic 2026-05-04)

From task spec, these need verdicts (not necessarily code changes this sprint):

| Sprint | Topic | Pre-sprint status (post #10/#18/#21) |
|---|---|---|
| F | "Plug the existing" | Mostly done by #10 cleanup (orphans=0, capabilities all wired). |
| G | Archivage massif | Done by #10 cleanup. |
| H | Framework cadrage finalisé | Phase 4 of strategic doc; partially addressed by #18 doctrine V3.3 (research-first + ICE codified). |
| I | Mode 2 REPLACE pipeline_sequential_4_stages | Out of scope #23 — needs dedicated GSG modes refactor sprint. |
| J | Refactor Modes 3-4-5 full impl | Out of scope #23 — same as I. |
| K | Review 69 doctrine_proposals | Mutualised with #18 pre-categorization. Mathis review pending. |
| L | Cross-client validation | Covered by 3 pilote clients + #19 multi-judge regression (when scheduled). |

---

## 6. Gate baseline (pre-sprint)

- `python3 scripts/lint_code_hygiene.py` → exit 0 (no FAIL, no WARN beyond known DEBT — verified locally).
- `python3 scripts/audit_capabilities.py` → orphans = 0, 212 files scanned, all categories green.
- `python3 SCHEMA/validate_all.py` → expected exit 0 (TODO confirm pre-flight before commits).
- `bash scripts/agent_smoke_test.sh` → expected exit 0.

---

## 7. Decisions & scope cuts for this sprint

1. **No live runs** — Mathis hasn't shared per-client credentials yet. We deliver structural readiness only. Documented as "Open for Mathis" in MANIFEST §12.
2. **Promote existing skills code to `growthcro/`** — thin re-export wrappers, NOT duplicate implementations. Keep skills code in place (other consumers might still import).
3. **Add a credentials inspector** (`growthcro/reality/credentials.py`) — for a client, lists which connectors have creds and which don't, never exposing the values.
4. **Per-client env vars** are extended in `growthcro/config.py::_KNOWN_VARS` so `.env.example` is regenerated mechanically.
5. **A/B = experiment proposals only** — zero auto-trigger. Module emits proposals; Mathis validates + runs.
6. **Learning V30** lives in `growthcro/learning/v30_data_driven.py` (≤ 500 LOC). Bayesian update consumes reality + experiment data. Output schema identical to V29 (review pipeline reusable).
7. **Webapp deep-impl** — both reality-monitor and learning-lab move past placeholder to real list/detail pages, but data sources are filesystem-mounted JSON OR Supabase `runs` table — no hard dependency on live credentials.
8. **Pilote client selection deferred to Mathis** — task spec proposes Weglot + Japhy + 1 active agency client. We scaffold for those slugs but don't hard-code them.
