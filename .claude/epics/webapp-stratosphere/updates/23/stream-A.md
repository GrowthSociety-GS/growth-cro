# Issue #23 — Stream A — Reality / Experiment / Learning Loop

**Branch**: `task/23-reality-loop`
**Worktree**: `/Users/mathisfronty/Developer/task-23-reality-loop`
**Status**: Structural readiness complete — Reality Layer connectors promoted to `growthcro/reality/`, Experiment Engine to `growthcro/experiment/`, Learning V30 Bayesian data-driven to `growthcro/learning/v30_data_driven.py`, webapp V28 reality-monitor + learning-lab moved from placeholders to functional. Live runs PENDING per-client credentials in `.env` (Mathis collect ~1.5h for 3 pilote clients).

## Commits on `task/23-reality-loop`

1. `Issue #23: growthcro/config.py + .env.example extended with Reality Layer per-client vars` (d4abe94)
2. `Issue #23: growthcro/reality/ package — credentials + 6 connectors + orchestrator` (222014b)
3. `Issue #23: growthcro/experiment/ package — engine + runner + recorder (zero auto-trigger)` (e080508)
4. `Issue #23: growthcro/learning/v30_data_driven.py — Bayesian update on doctrine V3.3` (f5db114)
5. `Issue #23: webapp V28 reality-monitor + learning-lab deep impl` (f092a90)
6. `Issue #23: WEBAPP_ARCHITECTURE_MAP reality_loop pipeline + SPRINTS_F_L_STATUS doc` (df0a1cc)
7. `Issue #23: refresh CAPABILITIES + WEBAPP_ARCHITECTURE_MAP post growthcro/{reality,experiment,learning} additions` (2f2512f)
8. `docs: manifest §12 — add 2026-05-11 changelog for #23 reality/experiment/learning loop` (this commit, separate per CLAUDE.md rule)

## What shipped

### 1. Reality Layer — `growthcro/reality/` (1220 LOC across 10 files)

- `__init__.py` (64 LOC) — package exports.
- `base.py` (72 LOC) — `Connector` ABC + `RealityLayerData` dataclass + exception classes. Uses `config.reality_client_env(var, slug)` for per-client + global fallback lookup.
- `credentials.py` (134 LOC) — `missing_credentials_report(client_slug)` + `configured_connectors(client_slug)`. CLI: `python3 -m growthcro.reality.credentials --client <slug>`. Never logs credential values.
- `ga4.py` (173 LOC) — NEW. Native GA4 Data API v1 connector (service account flow). Alt to Catchr.
- `catchr.py` (95 LOC) — Catchr API connector (Growth Society SaaS GA4 aggregator).
- `meta_ads.py` (90 LOC) — Meta Marketing API v18 connector.
- `google_ads.py` (110 LOC) — Google Ads API v15+ connector (lazy SDK import).
- `shopify.py` (120 LOC) — Shopify Admin GraphQL 2024-10 connector.
- `clarity.py` (82 LOC) — Microsoft Clarity Data Export (free tier, 3-day window).
- `orchestrator.py` (280 LOC) — `collect_reality_snapshot(client, page_url, page_slug, …)`. Writes `data/reality/<client>/<page>/<iso_date>/reality_snapshot.json` + mirrors to legacy `data/captures/<client>/<page>/reality_layer.json` for V27 dashboards. Idempotent (atomic tmp → replace).

Tested:
```
$ python3 -m growthcro.reality.credentials --client weglot
Reality Layer credentials — client=weglot
  Configured: 0/6 connectors

  -- ga4           missing: GA4_SERVICE_ACCOUNT_JSON, GA4_PROPERTY_ID
  -- catchr        missing: CATCHR_API_KEY, CATCHR_PROPERTY_ID
  -- meta_ads      missing: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID
  -- google_ads    missing: 5 vars
  -- shopify       missing: 2 vars
  -- clarity       missing: 2 vars
```

### 2. Experiment Engine — `growthcro/experiment/` (751 LOC across 4 files)

- `__init__.py` (62 LOC) — package exports.
- `engine.py` (280 LOC) — `compute_sample_size` (z-test for proportions, stdlib-only Beasley-Springer-Moro inverse normal CDF), `build_experiment_spec`, `select_guardrails`, `estimate_duration_days`. Default guardrails per business_category (ecommerce / saas / lead_gen / default).
- `runner.py` (207 LOC) — `propose_experiments(client, page, reality_snapshot, recos, …)`. 5 AB types: `hero_copy`, `cta_wording`, `social_proof_position`, `form_fields_count`, `pricing_display`. Each AB type has its own default `mde_relative` and `primary_metric` override. **Zero auto-trigger** — output is `status="proposed"` specs.
- `recorder.py` (202 LOC) — `record_experiment`, `list_experiments`, `rebuild_index`, `import_outcome`. Index at `data/experiments/_index/experiments_index.json` (regen-able). Atomic writes.

End-to-end smoke-tested: 5 reco inputs → 5 proposals, one per AB type, all `status="proposed"`. Sample size formula verified at baseline 3.4% / MDE 10% → ~46,745 sessions per variant.

### 3. Learning V30 — `growthcro/learning/v30_data_driven.py` (474 LOC)

- `BayesianBetaPosterior` dataclass — α/β tracker per criterion. Prior Beta(1,1) = uniform. Update rules: won → α+=1, lost → β+=1, inconclusive → both += 0.5.
- `compute_data_driven_proposals(outcomes, snapshots, v3_3_criteria, thresholds)` — pure function. 4 patterns:
  - **strengthen_recommendation** : `posterior_mean ≥ 0.65 AND total_trials ≥ 3`
  - **weaken_recommendation** : `posterior_mean ≤ 0.35 AND total_trials ≥ 3`
  - **gather_more_evidence** : `total_trials ≥ 3 AND CI_width ≥ 0.40`
  - **revisit_criterion** : reality CR sustained below 0.5%
- `run_v30_cycle(thresholds, write)` — full filesystem scan + persist to `data/learning/data_driven_proposals/<iso_date>/<id>.json` + `data_driven_stats.json` + `data_driven_summary.md`.
- Output schema matches V29 (proposal_id / type / evidence / proposed_change / risk / requires_human_approval) — review pipeline reused.
- 95% credible interval via normal approximation (stdlib-only).

End-to-end smoke-tested: 4 synthetic outcomes (3 W / 1 L on `hero_01`) → 1 V30 proposal `type=strengthen_recommendation`, posterior_mean ≈ 0.667, CI=[0.32, 1.00].

### 4. Webapp V28 deep-impl (12 new files, ~1100 LOC TS)

**Reality Monitor** (`webapp/apps/reality-monitor/`):
- `lib/reality-fs.ts` — TS port of `growthcro.reality.credentials` inspector + filesystem reader for `data/reality/<client>/<page>/<date>/reality_snapshot.json`. Same per-client + global env-var fallback semantics.
- `app/page.tsx` — root listing of pilote candidates (Supabase clients ∪ filesystem `data/reality/` ∪ hardcoded pilote hints `weglot, japhy`) with credentials status pills + latest snapshot date.
- `app/[clientSlug]/page.tsx` — per-client view: `CredentialsGrid` (5 connectors with configured/missing badges), `SnapshotMetricsCard` (sessions, CR, bounce, ad spend, Meta/Google ROAS, page revenue, friction signals per 1k sessions), historical snapshot list.
- `components/RecentRunsTracker.tsx` — Supabase realtime subscription on `runs` table (type=reality), live INSERT/UPDATE/DELETE.

**Learning Lab** (`webapp/apps/learning-lab/`):
- `lib/proposals-fs.ts` — loads V29 proposals from `data/learning/audit_based_proposals/` + V30 proposals from `data/learning/data_driven_proposals/<date>/`. Sidecar `.review.json` review state.
- `app/page.tsx` — root listing with KPIs (V29 count, V30 count, pending/accepted/rejected/deferred) + `ProposalList` (search + filter by track/status/type).
- `app/[proposalId]/page.tsx` — per-proposal detail view with full evidence dump + Accept/Reject/Defer buttons + note textarea.
- `app/api/proposals/review/route.ts` — POST persists `<id>.review.json` sidecar; GET returns current review state.

Both apps build clean:
```
reality-monitor: 4 routes (/, /[clientSlug], _not-found, …)
learning-lab:    5 routes (/, /[proposalId], /api/proposals/review, …)
TypeScript noEmit: 0 errors on both.
```

### 5. Strategic doc + Architecture map

- `SPRINTS_F_L_STATUS.md` documents verdicts on the 7 strategic sprints (F-L) from `STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md` §6. Summary: F+G+K done by prior epics + this sprint; H partial; I+J explicitly deferred to future `gsg-modes-refactor` epic; L structurally ready.
- `WEBAPP_ARCHITECTURE_MAP.yaml` enriched with:
  - 14 new modules auto-detected (growthcro/reality/*, growthcro/experiment/*, growthcro/learning/*).
  - `pipelines.reality_loop` updated with 6 stages, pilote_clients_proposed, output_paths, webapp_v28_apps, status="V30 structurally READY".
  - 4 entries (`reality/orchestrator`, `reality/credentials`, `experiment/runner`, `learning/v30_data_driven`) given human-curated inputs/outputs/doctrine_refs.
- `CAPABILITIES_REGISTRY.json` refreshed: 228 → 232 active files, 17 → 20 active package markers, orphans=0.

## Gates

| Gate | Result |
|---|---|
| `python3 scripts/lint_code_hygiene.py` | FAIL=0, WARN=0, INFO (print-in-pipeline) only |
| `python3 scripts/audit_capabilities.py` | orphans=0, 232 files scanned |
| `python3 SCHEMA/validate_all.py` | 15 files validated, all passing |
| `bash scripts/agent_smoke_test.sh` | ALL AGENT SMOKE TESTS PASS |
| `python3 scripts/update_architecture_map.py` | exit 0, idempotent (manual additions preserved) |
| `bash scripts/parity_check.sh weglot` | exit 1 (expected: fresh worktree, no per-worktree baseline) |
| `cd webapp/apps/reality-monitor && npx tsc --noEmit` | 0 errors |
| `cd webapp/apps/learning-lab && npx tsc --noEmit` | 0 errors |
| `cd webapp/apps/reality-monitor && npx next build` | clean, 4 routes |
| `cd webapp/apps/learning-lab && npx next build` | clean, 5 routes |

## Open for Mathis

Live runs blocked on per-client credentials. Estimated ~30min per client × 3 = ~1.5h:

| Client | GA4 SA JSON | Meta token | Google Ads OAuth | Shopify Admin | Clarity token |
|---|---|---|---|---|---|
| weglot (SaaS) | needed | needed | needed | N/A | needed |
| japhy (DTC e-com) | needed | needed | needed | needed | needed |
| `<agency_client_TBD>` | needed | needed | needed | depends | needed |

Once credentials in `.env`, the flow per client is:

```bash
# 1. Verify credentials
python3 -m growthcro.reality.credentials --client weglot

# 2. Pull reality snapshot for a specific page
python3 -m growthcro.reality.orchestrator \
  --client weglot \
  --page-url https://weglot.com/listicle/wordpress-multilingual-plugin \
  --page-slug lp_listicle_wordpress \
  --days 30

# 3. (after recos exist) generate 5 experiment proposals
python3 -c "
from growthcro.experiment import propose_experiments
# ... feed recos + reality_snapshot
"

# 4. (after Mathis launches A/Bs externally + records outcomes)
#    Run Bayesian update
python3 -m growthcro.learning.v30_data_driven --min-trials 3
```

## Constraints respected

- No `--force`, `reset --hard`, `clean -fd`, `branch -D`, `checkout -- <file>`, `push --force` used.
- Zero credentials exposed in logs/commits — only var-name presence checked.
- All `os.environ` / `os.getenv` reads go through `growthcro.config` (new `reality_client_env` accessor).
- ≤ 800 LOC per file. Largest new file: `growthcro/learning/v30_data_driven.py` at 474 LOC.
- Zero auto-trigger A/B — `runner.propose_experiments` emits `status="proposed"`.
- No modifications to `playbook/*.json`, `data/clients_database.json`, or Notion.
- Doctrine V3.3 (from #18) consumed read-only by Learning V30.
- V29 audit-based proposals coexist with V30 data-driven (parallel folders).

## NOT pushed, NOT merged

Per task spec: stop on `task/23-reality-loop`. Mathis decides when to merge into `main`.

## Files changed

```
.env.example                                                              | +30 lines (Reality vars)
growthcro/config.py                                                       | +60 lines (Reality vars schema + accessor)
growthcro/reality/__init__.py                                             | new, 64 LOC
growthcro/reality/base.py                                                 | new, 72 LOC
growthcro/reality/credentials.py                                          | new, 134 LOC
growthcro/reality/ga4.py                                                  | new, 173 LOC
growthcro/reality/catchr.py                                               | new, 95 LOC
growthcro/reality/meta_ads.py                                             | new, 90 LOC
growthcro/reality/google_ads.py                                           | new, 110 LOC
growthcro/reality/shopify.py                                              | new, 120 LOC
growthcro/reality/clarity.py                                              | new, 82 LOC
growthcro/reality/orchestrator.py                                         | new, 280 LOC
growthcro/experiment/__init__.py                                          | new, 62 LOC
growthcro/experiment/engine.py                                            | new, 280 LOC
growthcro/experiment/runner.py                                            | new, 207 LOC
growthcro/experiment/recorder.py                                          | new, 202 LOC
growthcro/learning/__init__.py                                            | new, 23 LOC
growthcro/learning/v30_data_driven.py                                     | new, 474 LOC
webapp/apps/reality-monitor/lib/reality-fs.ts                             | new, ~150 LOC
webapp/apps/reality-monitor/components/CredentialsGrid.tsx                | new, ~70 LOC
webapp/apps/reality-monitor/components/SnapshotMetricsCard.tsx            | new, ~115 LOC
webapp/apps/reality-monitor/components/RecentRunsTracker.tsx              | new, ~75 LOC
webapp/apps/reality-monitor/app/page.tsx                                  | rewritten, ~160 LOC
webapp/apps/reality-monitor/app/[clientSlug]/page.tsx                     | new, ~110 LOC
webapp/apps/learning-lab/lib/proposals-fs.ts                              | new, ~140 LOC
webapp/apps/learning-lab/components/ProposalList.tsx                      | new, ~180 LOC
webapp/apps/learning-lab/components/ProposalDetail.tsx                    | new, ~190 LOC
webapp/apps/learning-lab/app/page.tsx                                     | rewritten, ~80 LOC
webapp/apps/learning-lab/app/[proposalId]/page.tsx                        | new, ~45 LOC
webapp/apps/learning-lab/app/api/proposals/review/route.ts                | new, ~70 LOC
.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml                           | +400 lines (14 modules + reality_loop)
.claude/epics/webapp-stratosphere/updates/23/EXISTING_INVENTORY.md        | new doc
.claude/epics/webapp-stratosphere/updates/23/SPRINTS_F_L_STATUS.md        | new doc
.claude/epics/webapp-stratosphere/updates/23/stream-A.md                  | this file
CAPABILITIES_REGISTRY.json                                                | +508 lines (auto-refresh)
.claude/docs/state/CAPABILITIES_SUMMARY.md                                | counts refresh
```

**Net structural Python additions**: ~2400 LOC across 18 files, all mono-concern, all under 500 LOC. Zero new external dependencies (Python). All connectors lazy-import their respective SDKs so the package can be imported and credentials-inspected without installing `google-ads`, `google-analytics-data`, etc. for clients not using those connectors.
