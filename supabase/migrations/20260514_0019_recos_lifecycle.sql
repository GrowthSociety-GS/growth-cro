-- Sprint 5 / Task 006 — reco-lifecycle-bbox-and-evidence (2026-05-14).
--
-- Adds `recos.lifecycle_status` to track each recommendation across the V26
-- backlog → ab_positive → shipped → learned funnel. 13-state enum.
-- The webapp `<LifecyclePill>` reads this column and exposes an admin
-- dropdown that PATCHes `/api/recos/[id]/lifecycle`.
--
-- Backfill rule : every existing reco is parked in `backlog` because nothing
-- in the current dataset has progressed past discovery.
--
-- Idempotent (column-existence guarded), additive only.

do $$
begin
  if not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'recos'
      and column_name = 'lifecycle_status'
  ) then
    alter table public.recos
      add column lifecycle_status text not null default 'backlog'
      check (lifecycle_status in (
        'backlog',
        'prioritized',
        'scoped',
        'designing',
        'implementing',
        'qa',
        'staged',
        'ab_running',
        'ab_inconclusive',
        'ab_negative',
        'ab_positive',
        'shipped',
        'learned'
      ));

    -- Explicit backfill so the closed-loop coverage strip on the home
    -- dashboard (Task 004) reports an honest "all in backlog" baseline
    -- rather than relying on the default applying retroactively.
    update public.recos set lifecycle_status = 'backlog' where lifecycle_status is null;
  end if;
end $$;

-- Partial index for the dashboard query that powers the Closed-Loop
-- "Lifecycle" tile (`status NOT IN ('backlog', null)`). Tiny — only rows
-- that have moved past backlog are indexed.
create index if not exists idx_recos_lifecycle_active
  on public.recos(lifecycle_status)
  where lifecycle_status <> 'backlog';
