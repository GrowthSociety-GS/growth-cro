-- Sprint 12b / Task 011 — reality-layer-5-connectors-wiring (2026-05-14).
--
-- Adds OAuth-token-backed Reality Layer wiring (Catchr / Meta Ads /
-- Google Ads / Shopify / Microsoft Clarity). This complements the
-- env-var-per-client V26.C pipeline (`growthcro/reality/orchestrator.py`,
-- per-client `.env` keys read via `growthcro.config.reality_client_env`)
-- with a Supabase-resident credentials vault + per-metric snapshot stream
-- consumed by the V30 webapp dashboards.
--
-- Why two stores : the env-var pipeline is per-client page-snapshot rich
-- JSON (GA4 + Catchr + Shopify shaped for `data/reality/<client>/<page>/`).
-- The Task 011 OAuth path is a *cron-polled* (client × connector × metric)
-- key-value stream for the heat map / sparkline / Observatory KPIs. Both
-- coexist : the rich snapshot powers per-page audit drill-downs ; the
-- key-value stream powers fleet trend visualisations.
--
-- Encryption : access_token + refresh_token columns store the *encrypted*
-- form. The encryption uses pgcrypto `encrypt(token, key, 'aes')` with the
-- key fetched from a session-scoped GUC (`app.reality_token_key`) set
-- by the API layer from env var `REALITY_TOKEN_ENCRYPTION_KEY`. When the
-- key is absent the API layer surfaces a clear error rather than writing
-- plaintext.
--
-- RLS : reads gated by `public.is_org_member(org_id)`. Inserts/updates
-- on `client_credentials` gated by `public.is_org_admin(org_id)` (an
-- OAuth handshake is an admin action — non-admin members can VIEW status
-- pills but never see tokens or trigger a handshake).
--
-- Idempotent : `create … if not exists` guards on tables, indexes, and
-- policies. Safe to re-run. The pgcrypto extension was already enabled by
-- migration 20260511_0001_init_schema.sql ; we re-assert it as a no-op.

create extension if not exists "pgcrypto";

-- ─────────────────────────────────────────────────────────────────────
-- client_credentials : OAuth token vault, one row per (client, connector)
-- ─────────────────────────────────────────────────────────────────────
create table if not exists public.client_credentials (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients(id) on delete cascade,
  org_id uuid not null references public.organizations(id) on delete cascade,
  connector text not null
    check (connector in ('catchr','meta_ads','google_ads','shopify','clarity')),
  access_token_encrypted text,
  refresh_token_encrypted text,
  expires_at timestamptz,
  scope text[],
  -- Per-connector identifier (Shopify shop domain, Meta ad account, etc.)
  connector_account_id text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (client_id, connector)
);

create index if not exists idx_client_credentials_org
  on public.client_credentials(org_id);
create index if not exists idx_client_credentials_connector
  on public.client_credentials(connector);

alter table public.client_credentials enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'client_credentials'
      and policyname = 'client_credentials_org_select'
  ) then
    create policy client_credentials_org_select
      on public.client_credentials
      for select
      using (public.is_org_member(org_id));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'client_credentials'
      and policyname = 'client_credentials_admin_write'
  ) then
    create policy client_credentials_admin_write
      on public.client_credentials
      for all
      using (public.is_org_admin(org_id))
      with check (public.is_org_admin(org_id));
  end if;
end $$;

-- ─────────────────────────────────────────────────────────────────────
-- reality_snapshots : (client, connector, metric, ts, value) time-series
-- ─────────────────────────────────────────────────────────────────────
create table if not exists public.reality_snapshots (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients(id) on delete cascade,
  org_id uuid not null references public.organizations(id) on delete cascade,
  connector text not null
    check (connector in ('catchr','meta_ads','google_ads','shopify','clarity')),
  metric text not null
    check (metric in ('cvr','cpa','aov','traffic','impressions')),
  value numeric,
  ts timestamptz not null default now(),
  raw_response_json jsonb
);

create index if not exists idx_reality_snapshots_client_metric_ts
  on public.reality_snapshots(client_id, metric, ts desc);
create index if not exists idx_reality_snapshots_org
  on public.reality_snapshots(org_id);
create index if not exists idx_reality_snapshots_connector
  on public.reality_snapshots(connector, ts desc);

alter table public.reality_snapshots enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'reality_snapshots'
      and policyname = 'reality_snapshots_org_select'
  ) then
    create policy reality_snapshots_org_select
      on public.reality_snapshots
      for select
      using (public.is_org_member(org_id));
  end if;

  -- Inserts come from the cron worker (service_role bypasses RLS) ; admin
  -- members may insert manually for backfill. No update / delete policy.
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'reality_snapshots'
      and policyname = 'reality_snapshots_admin_insert'
  ) then
    create policy reality_snapshots_admin_insert
      on public.reality_snapshots
      for insert
      with check (public.is_org_admin(org_id));
  end if;
end $$;

-- ─────────────────────────────────────────────────────────────────────
-- Encryption helpers (pgcrypto)
-- ─────────────────────────────────────────────────────────────────────
-- The key is fetched from a session GUC set by the API layer immediately
-- before insert/select. If unset, returns the literal sentinel '__no_key__'
-- which the API layer must detect and surface as a clear error (rather
-- than silently writing plaintext).
create or replace function public.reality_encrypt(p_plain text)
returns text language plpgsql as $$
declare
  v_key text := current_setting('app.reality_token_key', true);
begin
  if v_key is null or v_key = '' then
    return '__no_key__';
  end if;
  return encode(
    encrypt(p_plain::bytea, v_key::bytea, 'aes'),
    'base64'
  );
end;
$$;

create or replace function public.reality_decrypt(p_encoded text)
returns text language plpgsql as $$
declare
  v_key text := current_setting('app.reality_token_key', true);
begin
  if v_key is null or v_key = '' then
    return null;
  end if;
  return convert_from(
    decrypt(decode(p_encoded, 'base64'), v_key::bytea, 'aes'),
    'utf8'
  );
exception when others then
  return null;
end;
$$;

comment on table public.client_credentials is
  'Task 011 — OAuth token vault. access/refresh tokens are pgcrypto-encrypted ; the key comes from REALITY_TOKEN_ENCRYPTION_KEY env var set as GUC app.reality_token_key.';
comment on table public.reality_snapshots is
  'Task 011 — Cron-polled (client × connector × metric) time-series. One row per snapshot. Indexed for the V30 heat map + sparkline queries.';
