# T002 — AccountTab (password change) + TeamTab (invite) + /api/team/invite

**Status** : done

## Files
- WRITE `webapp/apps/shell/components/settings/AccountTab.tsx` — 3-input form (current pwd, new pwd, confirm) + identity panel (email, last sign-in).
- WRITE `webapp/apps/shell/components/settings/TeamTab.tsx` — list `org_members` (passed in from server page) + invite form.
- NEW `webapp/apps/shell/app/api/team/invite/route.ts` — POST handler. Validates email + role, authenticates the caller, resolves org_id, uses service_role to invite + upsert org_members row.
- NEW `webapp/packages/data/src/queries/org-members.ts` — `listOrgMembers()` + `getCurrentOrgId()` helpers (RLS-aware).
- EDIT `webapp/packages/data/src/index.ts` — re-export new query module.

## AccountTab — flow
1. User types current pwd + new pwd + confirm.
2. Client-side validates: new pwd ≥ 8 chars, both fields match.
3. Re-verifies current pwd via `supabase.auth.signInWithPassword(email, current)`. Wrong pwd → "Mot de passe actuel incorrect.".
4. Calls `supabase.auth.updateUser({ password })` to rotate.
5. Success toast + auto-redirect `/` after 2s.

## TeamTab — flow
1. Initial members fetched server-side via `listOrgMembers()` (RLS).
2. Invite form POSTs to `/api/team/invite` (server-only route handler).
3. On success, prepended to local state to avoid re-fetch.
4. Email validation client-side (regex) + server-side (regex + role enum).

## /api/team/invite — security
- Auth-gated: bails 401 if caller is not authenticated (uses `createServerSupabase()` cookie-bound client).
- Role-gated: only `admin` role in caller's org can invite (403 otherwise).
- Uses `getServiceRoleSupabase()` exclusively inside the handler — service_role NEVER returned in response or surfaced to client.
- `supabase.auth.admin.inviteUserByEmail()` to send the magic-link invite (Supabase free tier rate-limit handled by Supabase itself).
- Upserts `org_members` row on `(org_id, user_id)` so re-invite is idempotent.
