-- SP-11 — Screenshots Supabase Storage bucket (replaces 14 GB FS captures).
--
-- Context : `data/captures/<client>/<page>/screenshots/*.png` = 14 GB / 4831
-- PNG. Not deployable to Vercel serverless (~250 MB limit). The webapp's
-- `/api/screenshots/...` route returns 404 in prod because the filesystem is
-- not bundled. Migration : upload all PNG to a public Supabase Storage
-- bucket; the route handler 302-redirects to the public URL.
--
-- Bucket layout preserved : `<client>/<page>/<filename>.png` (matches the
-- on-disk path scheme so the route can construct URLs deterministically).
--
-- Public read (V1) : screenshots are not confidential and exposing them via
-- predictable URLs is acceptable for an internal dev tool. V2 may move to
-- signed URLs with 1h expiry if a confidentiality requirement appears.
--
-- Write access : service_role only — uploads driven by the offline Python
-- script `scripts/upload_screenshots_to_supabase.py`. The webapp never
-- writes to this bucket.

-- ---------------------------------------------------------------------------
-- Bucket
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
  values ('screenshots', 'screenshots', true)
  on conflict (id) do update set public = excluded.public;

-- ---------------------------------------------------------------------------
-- RLS policies on storage.objects (scoped to bucket_id = 'screenshots')
-- ---------------------------------------------------------------------------
-- SELECT : public — anyone (anon + authenticated) can read. The bucket is
-- already declared `public = true` above, which enables the Storage CDN
-- public URL endpoint. The explicit policy mirrors that intent at the SQL
-- layer for defence in depth (and survives future bucket-flag changes).
drop policy if exists "screenshots: public read" on storage.objects;
create policy "screenshots: public read" on storage.objects
  for select
  using (bucket_id = 'screenshots');

-- INSERT / UPDATE / DELETE : service_role only. PostgREST presents
-- service_role JWT as role = 'service_role'; checking `auth.role()` is the
-- canonical way to scope to it inside an RLS policy.
drop policy if exists "screenshots: service_role insert" on storage.objects;
create policy "screenshots: service_role insert" on storage.objects
  for insert
  with check (bucket_id = 'screenshots' and auth.role() = 'service_role');

drop policy if exists "screenshots: service_role update" on storage.objects;
create policy "screenshots: service_role update" on storage.objects
  for update
  using (bucket_id = 'screenshots' and auth.role() = 'service_role')
  with check (bucket_id = 'screenshots' and auth.role() = 'service_role');

drop policy if exists "screenshots: service_role delete" on storage.objects;
create policy "screenshots: service_role delete" on storage.objects
  for delete
  using (bucket_id = 'screenshots' and auth.role() = 'service_role');
