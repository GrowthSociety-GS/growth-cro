# T003 — UsageTab (4 KPIs) + ApiTab (read-only display)

**Status** : done

## Files
- WRITE `webapp/apps/shell/components/settings/UsageTab.tsx` — 4 KpiCard (Clients, Audits, Recos, Runs this month). Server-loaded counts passed in as props.
- WRITE `webapp/apps/shell/components/settings/ApiTab.tsx` — 3 read-only cards (Supabase URL, anon key with masking, project ref) + copy-to-clipboard buttons.
- NEW `webapp/packages/data/src/queries/usage.ts` — `countClients/Audits/Recos`, `countRunsThisMonth`, `loadUsageCounts` (Promise.all wrapper).
- EDIT `webapp/packages/data/src/index.ts` — re-export usage module.

## UsageTab — data
- 4 parallel `count(*)` queries via Supabase `select("*", { count: "exact", head: true })`. Each isolated in `.catch(() => 0)` so a single RLS failure doesn't break the whole tab.
- Runs-this-month filtered server-side with `gte("created_at", first-day-of-utc-month-iso)`.
- Counts org-scoped by Supabase RLS (`audits`, `clients`, `recos`, `runs` policies all check `org_members` membership).

## ApiTab — security
- Only reads from `getAppConfig()` (NEXT_PUBLIC_* values + project_ref derived from URL).
- Service_role key NEVER mentioned in client bundle: explicit comment in source + grep check post-merge.
- Anon key visually masked (first 8 + last 4 chars) but full value still in clipboard payload for legitimate `Copy` usage.
- `navigator.clipboard.writeText` wrapped in try/catch — no-op on permission denial.
