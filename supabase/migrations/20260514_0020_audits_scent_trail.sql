-- Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
--
-- Adds `audits.scent_trail_json` (JSONB, nullable) to expose the narrative
-- continuity signal of a visitor's ad → LP → product journey. Source data
-- lives on disk under `data/captures/<client>/scent_trail.json` (one file per
-- client — not per page) and is migrated into the most-recent audit row for
-- that client by `scripts/migrate_disk_to_supabase.py:load_scent_trail()`.
--
-- The column carries the full payload (flow + breaks + scent_score) — the
-- webapp `<ScentTrailDiagram>` + `<BreaksList>` parse it client-side rather
-- than relying on derived columns. No constraint : a missing scent trail is
-- a legitimate state (V1 panels surface "no scent capture yet" empty).
--
-- NO backfill : the disk data is per-client not per-audit, so a server-side
-- DEFAULT would lie about cardinality. The migration script's UPSERT is the
-- single source of writes.
--
-- Idempotent (column-existence guarded), additive only.

do $$
begin
  if not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'audits'
      and column_name = 'scent_trail_json'
  ) then
    alter table public.audits
      add column scent_trail_json jsonb;
  end if;
end $$;

-- Partial index for fleet-overview queries that filter on "clients with at
-- least one scent trail captured". Tiny — only audits carrying a payload are
-- indexed. The fleet pane sorts by `scent_score` so we cover that path too.
create index if not exists idx_audits_scent_trail_present
  on public.audits((scent_trail_json is not null))
  where scent_trail_json is not null;
