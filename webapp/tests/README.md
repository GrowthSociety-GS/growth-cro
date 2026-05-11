# E2E tests — GrowthCRO V28

Playwright tests live in `tests/e2e/`. Run:

```bash
# Local dev (must start shell first in another terminal: npm run dev:shell)
npx playwright test

# Against a deployed env
PLAYWRIGHT_BASE_URL=https://growthcro-shell.vercel.app npx playwright test

# Specific suite
npx playwright test auth.spec.ts
```

## Suites

| File                       | Coverage                                               |
|----------------------------|--------------------------------------------------------|
| `auth.spec.ts`             | Login UI: methods toggle, required fields, redirects  |
| `nav.spec.ts`              | Public routes (/login, /privacy, /terms) + nav contract |
| `client-detail.spec.ts`    | Audit landing < 2s budget, /reco reachable             |
| `realtime.spec.ts`         | No JS crashes when Supabase realtime channel mounts    |

## CI notes

- Without `SUPABASE_*` env vars: tests assert redirects + graceful fallbacks.
- With env vars + a seeded org + at least one test user: full auth round-trip.
