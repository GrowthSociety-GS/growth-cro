---
name: simplify-sprint-1-2-followup
description: Follow-up sub-PRD pour les findings /simplify Sprint 1 + 2 différés. 6 items déférés post-quickwins E1/E2/R2 appliqués en commit 876fef5. Effort cumulé ~4-6h. Non-bloquant pour Sprint 3.
status: backlog
created: 2026-05-14T13:37:58Z
parent_epic: webapp-stratospheric-reconstruction-2026-05
priority: P2
---

# PRD : simplify-sprint-1-2-followup

> /simplify a surfacé 40+ findings sur Sprint 1+2. 3 quickwins appliqués
> (E1 Realtime filter + E2 Starfield mobile + R2 scoreColor unifié — cf
> commit 876fef5). Ce sub-PRD couvre les 6 findings différés (effort
> plus large, non-bloquant).

## Executive Summary

Findings agent /simplify 2026-05-14 (3 agents : Reuse / Quality / Efficiency, 21 fichiers, +2078 LOC) :
- 🔴 4 hard issues (3 fixés, 1 différé Q1)
- 🟡 12 mid issues (3 différés)
- 🟢 ~24 already-optimal

Doctrine mechanical checks **PASS** (≤800 LOC, env via config, structured logger, Pydantic v2 frozen, no _vNN).

## Items différés (6)

### R1 — Extract `growthcro/lib/supabase_rest.py` (effort M, 30-45 min)
`_request()` + `_env()` + `SupabaseError` triplicated across :
- `growthcro/worker/daemon.py:58-92`
- `scripts/migrate_disk_to_supabase.py:461-486`
- `scripts/migrate_v27_to_supabase.py:168-189`
- `scripts/upload_screenshots_to_supabase.py:229`

Subtle drift already (different `prefer` headers + timeouts). Extract canonical shared module under `growthcro/lib/supabase_rest.py`. ~75 LOC dedup + CODE_DOCTRINE alignment.

### R3 — POST /api/runs use `insertRun()` helper (effort S, 15 min)
`webapp/apps/shell/app/api/runs/route.ts:130-140` raw-inserts. `BriefWizard.tsx:79` uses `insertRun()`. Inconsistent.

**Prerequisite** : update `Run` type to add `org_id` + update `insertRun()` Omit signature to exclude `started_at` + `finished_at` + `output_path`.

### Q1 — daemon error-string sniffing → Postgres code 42703 (effort S, 15 min)
`_patch_run_with_fallback` parses `"could not find"` substring. Brittle. Fix : parse JSON error body, switch on Postgres code `42703` (undefined_column).

### Q2 — `complete_run` / `fail_run` metadata helper (effort XS, 10 min)
Both build a 4-key `metadata_patch`. Extract `_dispatch_result_to_metadata(result) -> dict` helper.

### Q3 — `ALLOWED_TYPES` exhaustiveness check (effort XS, 5 min)
`route.ts:25` declares `ALLOWED_TYPES: RunType[]`. Adding a new `RunType` won't fail compile. Switch to `as const satisfies readonly RunType[]` + compile-time exhaustiveness test.

### E3 — Adaptive worker poll backoff (effort S, 20 min)
Flat 30s polling. Adaptive (5s floor → 120s cap, doubling on empty) cuts idle load ~80% + improves cold pickup to ~5s.

### E (out-of-doctrine-scope) — `styles.css` 1302 LOC split (effort M, ~1h)
Split into : `tokens.css` + `layout.css` + `components.css` + `utilities.css`.

## Acceptance Criteria

- [ ] R1 shipped : `growthcro/lib/supabase_rest.py` + 4 scripts use it
- [ ] R3 shipped : `/api/runs/route.ts` uses `insertRun()`
- [ ] Q1 shipped : Postgres code switch
- [ ] Q2 shipped : helper extracted
- [ ] Q3 shipped : compile-time exhaustiveness
- [ ] E3 shipped : adaptive backoff
- [ ] styles.css split (4 files)
- [ ] All 41 Playwright specs PASS post-refactor

## Effort

~4-6 hours cumulative. Non-bloquant.

## Sequencing (independent items)

1. Q1 + Q2 + E3 = ~45 min → one PR (daemon hardening)
2. R1 = ~45 min → one PR (REST helper extraction)
3. R3 + types update = ~20 min → one PR (API route consistency)
4. Q3 = ~10 min → bundle with any commit
5. styles.css split = ~1h → standalone PR
