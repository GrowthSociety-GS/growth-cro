-- Sprint 3 / Task 003 — client-lifecycle-from-ui (2026-05-14).
--
-- Adds `audits.status` to expose the pipeline lifecycle of an audit (idle →
-- capturing → scoring → enriching → done/failed). The Python worker daemon
-- (growthcro/worker) writes the column as the pipeline progresses ; the UI
-- consumes it via <AuditStatusPill /> with realtime updates (Phase B will
-- wire Supabase Realtime ; Phase A relies on `router.refresh()` triggered by
-- the surrounding RunStatusPill subscription).
--
-- Backfill rule : every existing audit is considered `done` because all rows
-- visible in Supabase today were seeded with `total_score_pct` populated.
-- New audits default to `idle` and walk through the enum as the worker runs.
--
-- Idempotent (column-existence guarded), additive only.

do $$
begin
  if not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'audits'
      and column_name = 'status'
  ) then
    alter table public.audits
      add column status text not null default 'idle'
      check (status in (
        'idle',
        'capturing',
        'scoring',
        'enriching',
        'done',
        'failed'
      ));

    -- Backfill existing audits to 'done' (they were seeded with scores
    -- already ; the default 'idle' only applies going forward).
    update public.audits set status = 'done' where status = 'idle';
  end if;
end $$;

create index if not exists idx_audits_status on public.audits(status);
