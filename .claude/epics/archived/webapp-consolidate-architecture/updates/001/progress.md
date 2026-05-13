---
issue: 001
started: 2026-05-13T09:42:30Z
last_sync: 2026-05-13T09:48:00Z
completion: 100%
---

# Task 001 — Move audit-app + reco-app into shell

## Status: completed

## Done

- [x] Read all source files (audit-app + reco-app)
- [x] Created shell/app/audits/page.tsx + audits/[clientSlug]/page.tsx
- [x] Created shell/app/recos/page.tsx + recos/[clientSlug]/page.tsx
- [x] Created shell/components/audits/AuditDetail.tsx + ClientPicker.tsx
- [x] Created shell/components/recos/RecoList.tsx
- [x] Updated imports : `@/components/X` → `@/components/<feature>/X`
- [x] Updated cross-feature links : `/audit/${slug}` → `/audits/${slug}`, `/reco/${slug}` → `/recos/${slug}`
- [x] Concatenated audit + reco globals.css into shell globals.css
- [x] supabase-server.ts source NOT moved (shell already has identical file)
- [x] Layouts NOT moved (shell root layout governs all)
