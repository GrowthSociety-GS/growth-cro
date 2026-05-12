-- Optional seed for local dev. Run AFTER the user is signed up at least once
-- so that auth.users has Mathis's row.

-- Replace this UUID with Mathis's auth.users.id after first signup.
-- select id from auth.users where email = 'mathis@growthsociety.io';
do $$
declare
  v_owner uuid := (select id from auth.users limit 1);
  v_org   uuid;
begin
  if v_owner is null then
    raise notice 'No auth.users row found — skip seed. Sign up first.';
    return;
  end if;
  insert into public.organizations (slug, name, owner_id)
  values ('growth-society', 'Growth Society', v_owner)
  on conflict (slug) do update set name = excluded.name
  returning id into v_org;
  insert into public.org_members (org_id, user_id, role)
  values (v_org, v_owner, 'admin')
  on conflict do nothing;
end$$;
