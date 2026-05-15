-- Sprint 12a / Task 009 — geo-monitor-v31-pane (2026-05-15).
--
-- Creates `public.geo_audits` to back the V31+ GEO Monitor pane (Generative
-- Engine Optimization). One row per (engine × query) probe : how often a
-- client's brand surfaces in ChatGPT / Claude / Perplexity responses to
-- standard buyer-intent queries.
--
-- Defensive shape : `presence_score` is nullable (when the engine call is
-- skipped — typically no_api_key — we still persist the attempt with
-- `skipped` reason via `response_text` for auditability). The runner is
-- intentionally tolerant : the migration ships before keys are provisioned
-- so the table exists from day-1 (empty), the UI renders empty-state, and
-- rows start flowing once Mathis sets OPENAI_API_KEY / PERPLEXITY_API_KEY.
--
-- RLS uses the existing `public.is_org_member(uuid)` /
-- `public.is_org_admin(uuid)` helpers defined in 20260511_0002_rls_policies.
-- Read = any org member ; write = org admin (the runner connects via the
-- service_role from the worker — RLS exempt by design).
--
-- Idempotent : create-if-not-exists on table, indexes, and policies.

create table if not exists public.geo_audits (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  engine text not null
    check (engine in ('anthropic', 'openai', 'perplexity')),
  query text not null,
  response_text text,
  presence_score numeric
    check (presence_score is null or (presence_score >= 0 and presence_score <= 1)),
  mentioned_terms jsonb not null default '[]'::jsonb,
  ts timestamptz not null default now(),
  cost_usd numeric not null default 0
    check (cost_usd >= 0)
);

create index if not exists idx_geo_audits_client_engine_ts
  on public.geo_audits(client_id, engine, ts desc);
create index if not exists idx_geo_audits_org
  on public.geo_audits(org_id);

alter table public.geo_audits enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'geo_audits'
      and policyname = 'geo_audits_org_select'
  ) then
    create policy geo_audits_org_select
      on public.geo_audits
      for select
      using (public.is_org_member(org_id));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'geo_audits'
      and policyname = 'geo_audits_admin_write'
  ) then
    create policy geo_audits_admin_write
      on public.geo_audits
      for all
      using (public.is_org_admin(org_id))
      with check (public.is_org_admin(org_id));
  end if;
end $$;
