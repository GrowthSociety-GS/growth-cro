-- Enable realtime broadcast on `runs` so the shell live-feed gets updates.
-- Supabase Realtime publishes via the `supabase_realtime` publication.

alter publication supabase_realtime add table public.runs;
