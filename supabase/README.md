# Supabase migrations — GrowthCRO V28

Schema source-of-truth: 4 SQL files run in order.

| File                              | Purpose                                                                |
|-----------------------------------|------------------------------------------------------------------------|
| `20260511_0001_init_schema.sql`   | Tables: orgs / members / clients / audits / recos / runs + triggers   |
| `20260511_0002_rls_policies.sql`  | RLS policies — org-based isolation                                     |
| `20260511_0003_views.sql`         | Read views: `clients_with_stats`, `recos_with_audit`                   |
| `20260511_0004_realtime.sql`      | Enable Supabase Realtime on `runs`                                     |

## Apply locally (with the Supabase CLI)

```bash
# 1. Login + link the project (EU region)
supabase login
supabase link --project-ref YOUR-EU-PROJECT-REF

# 2. Push migrations
supabase db push

# 3. (Optional) seed Growth Society org after first signup
supabase db remote commit
```

## Apply on Vercel deploy

Vercel build hooks should NOT run migrations. Use a one-shot GitHub Action
or `supabase db push` from a trusted operator workstation.

## RLS contract

- `auth.uid()` must be a member of `org_members` for the relevant `org_id` to read/write.
- Service role bypasses RLS — used by `scripts/migrate_v27_to_supabase.py`.
- Anonymous role has zero read access.

## EU region pinning

The Supabase project MUST be created with region `eu-central-1` (Frankfurt) or
`eu-west-3` (Paris). This is a deployment-time choice — the SQL doesn't enforce it.
