-- GrowthCRO V28 — initial schema.
-- Conventions: snake_case, uuid PKs, timestamptz, jsonb for flexible payloads.
-- Region: eu-central-1 (Frankfurt) for RGPD compliance.

create extension if not exists "pgcrypto";

------------------------------------------------------------------------------
-- Organizations (multi-tenant root)
------------------------------------------------------------------------------
create table if not exists public.organizations (
  id          uuid primary key default gen_random_uuid(),
  slug        text not null unique,
  name        text not null,
  owner_id    uuid not null references auth.users(id) on delete restrict,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table if not exists public.org_members (
  org_id      uuid not null references public.organizations(id) on delete cascade,
  user_id     uuid not null references auth.users(id) on delete cascade,
  role        text not null check (role in ('admin','consultant','viewer')),
  created_at  timestamptz not null default now(),
  primary key (org_id, user_id)
);

create index if not exists idx_org_members_user on public.org_members(user_id);

------------------------------------------------------------------------------
-- Clients (audited brands)
------------------------------------------------------------------------------
create table if not exists public.clients (
  id                 uuid primary key default gen_random_uuid(),
  org_id             uuid not null references public.organizations(id) on delete cascade,
  slug               text not null,
  name               text not null,
  business_category  text,
  homepage_url       text,
  brand_dna_json     jsonb,
  panel_role         text,
  panel_status       text,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique (org_id, slug)
);

create index if not exists idx_clients_org on public.clients(org_id);
create index if not exists idx_clients_category on public.clients(business_category);

------------------------------------------------------------------------------
-- Audits (per page-type scoring run)
------------------------------------------------------------------------------
create table if not exists public.audits (
  id                uuid primary key default gen_random_uuid(),
  client_id         uuid not null references public.clients(id) on delete cascade,
  page_type         text not null,
  page_slug         text not null,
  page_url          text,
  doctrine_version  text not null default 'v3.2.1',
  scores_json       jsonb not null default '{}'::jsonb,
  total_score       numeric,
  total_score_pct   numeric,
  created_at        timestamptz not null default now()
);

create index if not exists idx_audits_client on public.audits(client_id);
create index if not exists idx_audits_doctrine on public.audits(doctrine_version);
create index if not exists idx_audits_page_type on public.audits(page_type);

------------------------------------------------------------------------------
-- Recommendations
------------------------------------------------------------------------------
create table if not exists public.recos (
  id                uuid primary key default gen_random_uuid(),
  audit_id          uuid not null references public.audits(id) on delete cascade,
  criterion_id      text,
  priority          text not null check (priority in ('P0','P1','P2','P3')),
  effort            text check (effort in ('S','M','L')),
  lift              text check (lift in ('S','M','L')),
  title             text not null,
  content_json      jsonb not null default '{}'::jsonb,
  oco_anchors_json  jsonb,
  created_at        timestamptz not null default now()
);

create index if not exists idx_recos_audit on public.recos(audit_id);
create index if not exists idx_recos_priority on public.recos(priority);
create index if not exists idx_recos_criterion on public.recos(criterion_id);

------------------------------------------------------------------------------
-- Runs (pipeline executions: audit | gsg | reality | experiment)
------------------------------------------------------------------------------
create table if not exists public.runs (
  id             uuid primary key default gen_random_uuid(),
  org_id         uuid references public.organizations(id) on delete cascade,
  client_id      uuid references public.clients(id) on delete set null,
  type           text not null check (type in ('audit','gsg','reality','experiment')),
  status         text not null check (status in ('pending','running','completed','failed')),
  started_at     timestamptz,
  finished_at    timestamptz,
  output_path    text,
  metadata_json  jsonb,
  created_at     timestamptz not null default now()
);

create index if not exists idx_runs_org on public.runs(org_id);
create index if not exists idx_runs_client on public.runs(client_id);
create index if not exists idx_runs_status on public.runs(status);
create index if not exists idx_runs_type on public.runs(type);
create index if not exists idx_runs_created on public.runs(created_at desc);

------------------------------------------------------------------------------
-- updated_at trigger (idempotent)
------------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end$$;

drop trigger if exists trg_orgs_updated on public.organizations;
create trigger trg_orgs_updated before update on public.organizations
  for each row execute function public.set_updated_at();

drop trigger if exists trg_clients_updated on public.clients;
create trigger trg_clients_updated before update on public.clients
  for each row execute function public.set_updated_at();
