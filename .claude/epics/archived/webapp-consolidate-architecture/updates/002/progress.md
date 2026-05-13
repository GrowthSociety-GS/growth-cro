---
issue: 002
started: 2026-05-13T09:48:30Z
last_sync: 2026-05-13T09:58:00Z
completion: 100%
---

# Task 002 — Move gsg-studio + reality-monitor + learning-lab into shell

## Status: completed

## Done

- [x] Created shell dir structure
- [x] gsg: page.tsx + 3 components + lib/gsg-api.ts
- [x] reality: 2 pages + 3 components + lib/reality-fs.ts
- [x] learning: 2 pages + 2 components + lib/proposals-fs.ts + API route `/api/learning/proposals/review`
- [x] Imports `@/lib/*` and `@/components/<feature>/*`
- [x] fetch URL learning : `/learning/api/proposals/review` → `/api/learning/proposals/review`
- [x] Concat gsg globals.css into shell globals.css
- [x] Layouts microfrontends NOT moved (shell root layout governs all)
- [x] supabase-server.ts + use-supabase.ts source files NOT moved (shell has identical)
