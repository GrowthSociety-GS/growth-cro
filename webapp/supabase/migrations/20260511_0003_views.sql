-- Read-side views used by the dashboards. RLS is enforced by the underlying tables.

-- clients_with_stats: clients + their audit/reco counts + avg score.
create or replace view public.clients_with_stats as
select
  c.id,
  c.org_id,
  c.slug,
  c.name,
  c.business_category,
  c.homepage_url,
  c.brand_dna_json,
  c.panel_role,
  c.panel_status,
  c.created_at,
  c.updated_at,
  coalesce(stats.audits_count, 0) as audits_count,
  coalesce(stats.recos_count, 0) as recos_count,
  stats.avg_score_pct
from public.clients c
left join lateral (
  select
    count(distinct a.id) as audits_count,
    count(r.id) as recos_count,
    avg(a.total_score_pct) as avg_score_pct
  from public.audits a
  left join public.recos r on r.audit_id = a.id
  where a.client_id = c.id
) stats on true;

grant select on public.clients_with_stats to authenticated;

-- recos_with_audit: recos joined to client_id (for per-client lookups).
create or replace view public.recos_with_audit as
select
  r.*,
  a.client_id,
  a.page_type,
  a.page_slug,
  a.doctrine_version
from public.recos r
join public.audits a on a.id = r.audit_id;

grant select on public.recos_with_audit to authenticated;
