-- RLS policies — org-based isolation.
-- A user only sees clients / audits / recos / runs that belong to an org they
-- are a member of. Anonymous role has zero read access. Service role bypass.

alter table public.organizations enable row level security;
alter table public.org_members enable row level security;
alter table public.clients enable row level security;
alter table public.audits enable row level security;
alter table public.recos enable row level security;
alter table public.runs enable row level security;

------------------------------------------------------------------------------
-- Helper: is the calling user a member of the given org?
------------------------------------------------------------------------------
create or replace function public.is_org_member(p_org_id uuid)
returns boolean language sql security definer stable as $$
  select exists (
    select 1 from public.org_members m
    where m.org_id = p_org_id and m.user_id = auth.uid()
  );
$$;

create or replace function public.is_org_admin(p_org_id uuid)
returns boolean language sql security definer stable as $$
  select exists (
    select 1 from public.org_members m
    where m.org_id = p_org_id and m.user_id = auth.uid() and m.role = 'admin'
  );
$$;

------------------------------------------------------------------------------
-- organizations
------------------------------------------------------------------------------
drop policy if exists "orgs: member read" on public.organizations;
create policy "orgs: member read" on public.organizations
  for select using (public.is_org_member(id));

drop policy if exists "orgs: admin write" on public.organizations;
create policy "orgs: admin write" on public.organizations
  for update using (public.is_org_admin(id));

drop policy if exists "orgs: owner insert" on public.organizations;
create policy "orgs: owner insert" on public.organizations
  for insert with check (owner_id = auth.uid());

------------------------------------------------------------------------------
-- org_members
------------------------------------------------------------------------------
drop policy if exists "members: self read" on public.org_members;
create policy "members: self read" on public.org_members
  for select using (user_id = auth.uid() or public.is_org_member(org_id));

drop policy if exists "members: admin manage" on public.org_members;
create policy "members: admin manage" on public.org_members
  for all using (public.is_org_admin(org_id))
  with check (public.is_org_admin(org_id));

------------------------------------------------------------------------------
-- clients
------------------------------------------------------------------------------
drop policy if exists "clients: org read" on public.clients;
create policy "clients: org read" on public.clients
  for select using (public.is_org_member(org_id));

drop policy if exists "clients: consultant write" on public.clients;
create policy "clients: consultant write" on public.clients
  for all using (public.is_org_member(org_id))
  with check (public.is_org_member(org_id));

------------------------------------------------------------------------------
-- audits
------------------------------------------------------------------------------
drop policy if exists "audits: org read" on public.audits;
create policy "audits: org read" on public.audits
  for select using (
    exists (
      select 1 from public.clients c
      where c.id = audits.client_id and public.is_org_member(c.org_id)
    )
  );

drop policy if exists "audits: consultant write" on public.audits;
create policy "audits: consultant write" on public.audits
  for all using (
    exists (
      select 1 from public.clients c
      where c.id = audits.client_id and public.is_org_member(c.org_id)
    )
  )
  with check (
    exists (
      select 1 from public.clients c
      where c.id = audits.client_id and public.is_org_member(c.org_id)
    )
  );

------------------------------------------------------------------------------
-- recos
------------------------------------------------------------------------------
drop policy if exists "recos: org read" on public.recos;
create policy "recos: org read" on public.recos
  for select using (
    exists (
      select 1 from public.audits a
      join public.clients c on c.id = a.client_id
      where a.id = recos.audit_id and public.is_org_member(c.org_id)
    )
  );

drop policy if exists "recos: consultant write" on public.recos;
create policy "recos: consultant write" on public.recos
  for all using (
    exists (
      select 1 from public.audits a
      join public.clients c on c.id = a.client_id
      where a.id = recos.audit_id and public.is_org_member(c.org_id)
    )
  )
  with check (
    exists (
      select 1 from public.audits a
      join public.clients c on c.id = a.client_id
      where a.id = recos.audit_id and public.is_org_member(c.org_id)
    )
  );

------------------------------------------------------------------------------
-- runs
------------------------------------------------------------------------------
drop policy if exists "runs: org read" on public.runs;
create policy "runs: org read" on public.runs
  for select using (
    org_id is null or public.is_org_member(org_id)
  );

drop policy if exists "runs: consultant write" on public.runs;
create policy "runs: consultant write" on public.runs
  for all using (
    org_id is null or public.is_org_member(org_id)
  )
  with check (
    org_id is null or public.is_org_member(org_id)
  );
