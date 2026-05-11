# Issue #21 — Stream A — Webapp V28 Next.js Migration

**Branch**: `task/21-webapp-v28`
**Worktree**: `/Users/mathisfronty/Developer/task-21-webapp-v28`
**Status**: V28 v1 scaffold complete — 67 TS/TSX files, 6 microfrontends build clean, Supabase migrations + RLS ready, migration script (DRY-RUN) parses 56 clients × 185 audits × 3045 recos. Deploy Vercel + Supabase EU pending Mathis credentials.

## Commits on `task/21-webapp-v28`

1. `Issue #21: scaffold webapp/ Next.js 14 root + monorepo structure (config/data/ui packages)`
2. `Issue #21: shell microfrontend — Supabase auth (email+magic link) + nav + dashboard with realtime runs`
3. `Issue #21: audit-app microfrontend port from V27 audit pane (clients + audits + recos + scores)`
4. `Issue #21: reco-app microfrontend port from V27 reco pane (list + filters + priority counts)`
5. `Issue #21: gsg-studio microfrontend port from V27 GSG pane + brief wizard + LP preview`
6. `Issue #21: reality-monitor + learning-lab placeholder microfrontends (V26.C + V29/V30 wireframes)`
7. `Issue #21: Supabase migrations SQL — clients/audits/recos/runs/orgs + RLS policies + realtime + views`
8. `Issue #21: scripts/migrate_v27_to_supabase.py — 56 clients / 185 audits / 3045 recos idempotent UPSERT`
9. `Issue #21: Playwright e2e tests — auth/nav/client-detail/realtime (4 suites, desktop+mobile)`
10. `Issue #21: architecture/GROWTHCRO_ARCHITECTURE_V1.md update with V28 choices (Option B + microfrontends + RLS)`
11. `Issue #21: WEBAPP_ARCHITECTURE_MAP.yaml — add webapp_v28 pipeline + migrate_v27_to_supabase module`
12. `Issue #21: refresh CAPABILITIES + WEBAPP_ARCHITECTURE_MAP post webapp/scripts additions`
13. `Issue #21: fix build — lazy Supabase browser client + Suspense wrapper for /login + tsconfig refresh`
14. `docs: manifest §12 — add 2026-05-11 changelog for #21 webapp V28 Next.js migration` *(separate commit per CLAUDE.md rule)*

## What shipped

### 1. Webapp Next.js 14 monorepo — `webapp/`

Structure (npm workspaces) :

```
webapp/
├── package.json                ← workspaces: apps/*, packages/*
├── microfrontends.json         ← Vercel @vercel/microfrontends config
├── tsconfig.base.json
├── .env.example
├── apps/
│   ├── shell/                  ← DEEP: auth + nav + dashboard + realtime
│   ├── audit-app/              ← DEEP: V27 Audit pane port
│   ├── reco-app/               ← DEEP: V27 Reco pane port
│   ├── gsg-studio/             ← DEEP: brief wizard + LP preview
│   ├── reality-monitor/        ← PLACEHOLDER: data sources wireframe
│   └── learning-lab/           ← PLACEHOLDER: V29/V30 tracks wireframe
├── packages/
│   ├── ui/                     ← shared primitives + tokens.css + styles.css
│   ├── data/                   ← Supabase client + typed entities + queries
│   └── config/                 ← env-derived config (mirror growthcro/config.py)
├── supabase/migrations/        ← 4 SQL migrations
├── tests/e2e/                  ← 4 Playwright spec suites
└── playwright.config.ts
```

**File counts** (excl. node_modules/.next):

- 67 TypeScript files (`.ts` + `.tsx`)
- 4 SQL migrations (init schema / RLS / views / realtime)
- 4 Playwright spec files
- 4325 LOC total (TS/TSX/CSS/SQL/JSON/JS)

### 2. Microfrontends — DEEP vs PLACEHOLDER

| App                | Status      | What's wired                                                                      |
|--------------------|-------------|-----------------------------------------------------------------------------------|
| `shell`            | DEEP        | `/login` (email+pwd + magic link), `/`, `/audit`, `/reco`, `/gsg`, `/reality`, `/learning`, `/privacy`, `/terms`. Realtime runs feed (Supabase channels). Middleware auth gate. |
| `audit-app`        | DEEP        | `/audit` client picker (filters search+category) + `/audit/[slug]` with audits tabs + ScoreBar viz + RecoCard panel. |
| `reco-app`         | DEEP        | `/reco` client listing + `/reco/[slug]` with priority filter + search + counts. |
| `gsg-studio`       | DEEP        | `/gsg` brief wizard (8 fields), LP preview, 5-stage flow strip, `/api/gsg/run` trigger (backend). |
| `reality-monitor`  | PLACEHOLDER | Wireframe of 5 data sources (GA4/Meta/Google/Shopify/Clarity) — pending credentials. |
| `learning-lab`     | PLACEHOLDER | Wireframe of V29 audit-based (69 proposals) + V30 Bayesian tracks.                 |

### 3. Supabase schema + RLS (4 SQL migrations)

- `20260511_0001_init_schema.sql` — Tables: `organizations`, `org_members`, `clients`, `audits`, `recos`, `runs` + triggers
- `20260511_0002_rls_policies.sql` — RLS policies via `is_org_member(org_id)` / `is_org_admin(org_id)` security-definer helpers. Anon role zero read. Service role bypass.
- `20260511_0003_views.sql` — `clients_with_stats` (audits/recos counts + avg score) + `recos_with_audit` (per-client lookups)
- `20260511_0004_realtime.sql` — Publication `supabase_realtime` enriched with `runs`

**6 tables, 6 RLS policies enforced** (one read + one write per data table, member-only).

### 4. Migration script — `scripts/migrate_v27_to_supabase.py`

- 329 LOC, stdlib-only (urllib for PostgREST REST calls — no `pip install` needed).
- Parses `deliverables/growth_audit_data.js` (5.5MB JSON inline).
- **DRY-RUN automatic** if `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` absent — CI smoke safe.
- **Idempotent live mode**: UPSERT clients via `(org_id, slug)`, delete-then-insert audits/recos per client. Re-run safe.
- **Output (verified DRY-RUN)**: 56 clients · 185 audits · 3045 recos.
- **Env access doctrine**: uses `growthcro.config.get_config().system_env(...)` — no raw `os.environ`/`os.getenv`. Code hygiene FAIL=0.

### 5. Auth flow

- Email/password + magic link (OTP) via `@supabase/ssr` (cookies httpOnly).
- `/auth/callback?code=...&redirect=...` handler.
- `/auth/signout` POST handler.
- Middleware gate in `apps/shell/middleware.ts` — bypasses gracefully if Supabase env missing (allows builds).

### 6. Realtime pipeline updates

- `subscribeRuns(supabase, onChange)` in `@growthcro/data` subscribes to `public.runs` postgres_changes.
- `RunsLiveFeed` component in shell shows last 12 runs + live INSERT/UPDATE/DELETE.
- GSG Studio "Lancer le run" writes a `pending` row to `runs` so the shell sees it immediately, then calls FastAPI to actually run.

### 7. Backend choice — Option B (FastAPI Railway/Fly.io)

Rationale documented in `architecture/GROWTHCRO_ARCHITECTURE_V1.md` §4:

| Critère                  | Option A (Vercel edge) | Option B (FastAPI Fly.io) |
|--------------------------|------------------------|---------------------------|
| Long-running tasks       | Non (30s limit)        | OUI                       |
| Playwright capture       | Incompatible           | OUI                       |
| Réutilise code Python    | Non                    | OUI (zero change)         |
| Coût                     | Pay-per-invoke         | $5-10/mo                  |

→ **Option B chosen**. Webapp fetches `NEXT_PUBLIC_API_BASE_URL=https://growthcro-api.fly.dev`.

### 8. Architecture target doc — `architecture/GROWTHCRO_ARCHITECTURE_V1.md`

248 LOC. 13 sections:

1. Goal · 2. Diagram · 3. Microfrontend topology · 4. Backend choice · 5. Supabase data model · 6. RLS policies · 7. Auth flow · 8. Migration progressive · 9. RGPD · 10. Skills combo · 11. Anti-patterns guard-rail · 12. Open questions Mathis · 13. References.

### 9. Playwright tests — 4 suites

- `auth.spec.ts` (3 tests) — login UI methods + validation + redirect
- `nav.spec.ts` (3 tests) — public routes + nav contract
- `client-detail.spec.ts` (2 tests) — <2s budget + reco reachable
- `realtime.spec.ts` (1 test) — no JS crash when channel mounts

Desktop Chrome + Pixel 7 mobile projects. Run: `npx playwright test` (after `npm run dev:shell`).

### 10. RGPD compliance

- Hosting EU : Supabase eu-central-1 (Frankfurt) — pinned in `webapp/supabase/README.md`.
- Consent banner UI : `@growthcro/ui/ConsentBanner` mounted in shell layout. `localStorage` opt-in.
- `/privacy` page : droits utilisateurs (accès/rectif/effacement/portabilité), sous-traitants (Supabase/Vercel/Anthropic) + DPAs, conservation 24 mois.
- `/terms` page : usage interne agence + non-engagement de résultat CRO.

### 11. WEBAPP_ARCHITECTURE_MAP.yaml — new sections

- `pipelines.webapp_v28` — full description: 6 microfrontends, backend Option B, auth/realtime/RLS/region/skills_combo/status/task_ref/migration_script/architecture_doc
- `modules.scripts/migrate_v27_to_supabase` — auto-added by `update_architecture_map.py`
- Idempotent regen verified (only timestamps + source_commit change between runs).

## Gate results

| Gate                                                           | Status                                                                 |
|----------------------------------------------------------------|-----------------------------------------------------------------------|
| `python3 scripts/lint_code_hygiene.py`                         | exit 0 — FAIL=0                                                       |
| `python3 scripts/audit_capabilities.py`                        | exit 0 — orphans HIGH=0, partial=0                                    |
| `python3 SCHEMA/validate_all.py`                               | exit 0 — 15 files validated                                            |
| `bash scripts/agent_smoke_test.sh`                             | exit 0 — ALL AGENT SMOKE TESTS PASS                                   |
| `python3 scripts/update_architecture_map.py` (idempotent run)  | exit 0 — only timestamp/commit changes between runs                    |
| `bash scripts/parity_check.sh weglot`                          | exit 0                                                                |
| `webapp/apps/shell/npm run build`                              | exit 0 — 7 routes (3 static, 4 dynamic), 87 kB shared JS              |
| `webapp/apps/audit-app/npm run build`                          | exit 0                                                                |
| `webapp/apps/reco-app/npm run build`                           | exit 0                                                                |
| `webapp/apps/gsg-studio/npm run build`                         | exit 0                                                                |
| `webapp/apps/reality-monitor/npm run build`                    | exit 0                                                                |
| `webapp/apps/learning-lab/npm run build`                       | exit 0                                                                |
| `npx tsc --noEmit` (each app)                                  | exit 0                                                                |
| Playwright tests                                                | Not executed (requires dev server up) — written + ready              |

## Migration progressive

- V27 HTML `deliverables/GrowthCRO-V27-CommandCenter.html` **reste accessible** — Mathis l'utilise en parallèle.
- Bascule Mathis-driven : seulement quand V28 atteint parité fonctionnelle visuelle complète.

## Open for Mathis

Documented in `architecture/GROWTHCRO_ARCHITECTURE_V1.md` §12:

1. **Vercel project setup** — créer projets `growthcro-shell` + 5 sous-apps, OU livrer `vercel-init.sh`.
2. **Supabase project EU** — créer projet eu-central-1 (Frankfurt), partager connection string + service role key via `.env.local`.
3. **Backend host** — Fly.io (volume persistant Playwright) vs Railway (plus simple à wire).
4. **Test consultant agence** — inviter user test (auth + org_member `consultant`) pour valider RLS.

## Files referenced

- `architecture/GROWTHCRO_ARCHITECTURE_V1.md` — 248 LOC, choix techniques V28 documentés
- `webapp/supabase/migrations/*.sql` — 4 migrations
- `webapp/supabase/README.md` — instructions Supabase CLI
- `webapp/README.md` — quick-start dev
- `webapp/tests/README.md` — Playwright runbook
- `scripts/migrate_v27_to_supabase.py` — data migration
- `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` (pipelines.webapp_v28 section)
- `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 (changelog entry — separate commit)

## DO NOT do (per spec)

- ✅ Did NOT push to remote (`git push` blocked — Mathis decides when to merge)
- ✅ Did NOT merge to main
- ✅ Did NOT activate `Taste Skill` / `theme-factory` (Brand DNA per-client conflict)
- ✅ Did NOT modify Notion / `playbook/*.json` / `data/clients_database.json`
- ✅ Did NOT delete V27 HTML (parallel transition strategy)
- ✅ Did NOT exceed 800 LOC on any `.py` file (max = 329 in migrate script — INFO tier reviewer-affirmed single-concern)
