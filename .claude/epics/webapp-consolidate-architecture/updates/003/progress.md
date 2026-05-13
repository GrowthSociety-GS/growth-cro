---
issue: 003
started: 2026-05-13T09:58:30Z
last_sync: 2026-05-13T10:02:00Z
completion: 100%
---

# Task 003 — Update Sidebar + delete microfrontends.json + update workspace

## Status: completed

## Done

- [x] Sidebar.tsx labels: Audit→Audits, hrefs: /audit→/audits, /reco→/recos
- [x] Shell home page : 3 references updated (`/audit` button, top clients href, "Tout voir")
- [x] next.config.js: rewrites localhost retiré (microfrontends localhost ports removed)
- [x] webapp/microfrontends.json: supprimé via `git rm`
- [x] webapp/package.json: scripts `dev:audit, dev:reco, dev:gsg, dev:reality, dev:learning` retirés
- [x] vercel.json: UNCHANGED (verified by Read)
- [x] grep validation: no stale `/audit"`, `/reco"`, `/audit/`, `/reco/`, `/learning/api` references in shell
