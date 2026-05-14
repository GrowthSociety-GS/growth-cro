-- Sprint 2 / Task 002 — pipeline-trigger-backend Phase A (2026-05-14).
--
-- Extends public.runs to support the granular pipeline trigger surface :
--  - granular `type` enum : capture/score/recos/gsg/multi_judge/reality/geo +
--    legacy umbrellas audit/experiment kept for backward-compat
--  - `error_message` for failure traceability
--  - `progress_pct` for in-flight UI status pills
--
-- The base `runs` table + RLS policies + supabase_realtime publication are
-- defined in migrations 20260511_{0001,0002,0004}. This migration is additive
-- only (no breaking schema changes).

-- ──────────────────────────────────────────────────────────────────────────
-- Extend the `type` check constraint
-- ──────────────────────────────────────────────────────────────────────────
alter table public.runs
  drop constraint if exists runs_type_check;

alter table public.runs
  add constraint runs_type_check
  check (type in (
    -- legacy umbrellas (preserve historical rows)
    'audit', 'experiment',
    -- granular pipeline stages (Sprint 2)
    'capture', 'score', 'recos', 'gsg', 'multi_judge', 'reality', 'geo'
  ));

-- ──────────────────────────────────────────────────────────────────────────
-- Add `error_message` for failed runs
-- ──────────────────────────────────────────────────────────────────────────
alter table public.runs
  add column if not exists error_message text;

-- ──────────────────────────────────────────────────────────────────────────
-- Add `progress_pct` for live status pills (0-100, NULL when unknown)
-- ──────────────────────────────────────────────────────────────────────────
alter table public.runs
  add column if not exists progress_pct numeric check (progress_pct is null or (progress_pct >= 0 and progress_pct <= 100));

-- ──────────────────────────────────────────────────────────────────────────
-- Index for worker polling — `status=pending` rows sorted by created_at
-- (FIFO pickup). Partial index keeps it tiny (only pending rows indexed).
-- ──────────────────────────────────────────────────────────────────────────
create index if not exists idx_runs_pending_fifo
  on public.runs (created_at asc)
  where status = 'pending';

-- ──────────────────────────────────────────────────────────────────────────
-- Ensure realtime publication still covers `runs` (idempotent — no-op if
-- already a publication member from migration 20260511_0004).
-- ──────────────────────────────────────────────────────────────────────────
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'runs'
  ) then
    alter publication supabase_realtime add table public.runs;
  end if;
end $$;
