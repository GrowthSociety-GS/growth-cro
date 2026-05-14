-- Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
--
-- Creates `public.experiments` to back the V27 Experiment Engine pane.
-- One row per planned/running/completed AB test. Variants live as JSONB
-- (cardinality is small — 2-4 variants — and the schema is exploratory).
--
-- RLS uses the existing `public.is_org_member(uuid)` /
-- `public.is_org_admin(uuid)` helpers defined in 20260511_0002_rls_policies.
-- Read = any org member ; write = org admin only (mirrors the doctrine that
-- AB-test creation/mutation is a consultant action, not a viewer one).
--
-- Idempotent : create-if-not-exists guards on the table, indexes, and
-- policies. Safe to re-run.

create table if not exists public.experiments (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid references public.clients(id) on delete cascade,
  audit_id uuid references public.audits(id) on delete set null,
  name text not null,
  status text not null default 'planning'
    check (status in ('planning','running','paused','completed','abandoned')),
  variants_json jsonb not null default '[]'::jsonb,
  started_at timestamptz,
  ended_at timestamptz,
  result_json jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_experiments_client
  on public.experiments(client_id);
create index if not exists idx_experiments_org
  on public.experiments(org_id);
create index if not exists idx_experiments_status
  on public.experiments(status)
  where status in ('planning', 'running', 'paused');

alter table public.experiments enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'experiments'
      and policyname = 'experiments_org_select'
  ) then
    create policy experiments_org_select
      on public.experiments
      for select
      using (public.is_org_member(org_id));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'experiments'
      and policyname = 'experiments_admin_write'
  ) then
    create policy experiments_admin_write
      on public.experiments
      for all
      using (public.is_org_admin(org_id))
      with check (public.is_org_admin(org_id));
  end if;
end $$;
