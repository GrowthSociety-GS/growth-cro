---
issue: 004
started: 2026-05-13T10:02:30Z
last_sync: 2026-05-13T10:20:00Z
completion: 100%
---

# Task 004 — Archive 5 source dirs + run gate-vert + 2 commits

## Status: completed

## Done

- [x] `git mv` 5 microfrontend dirs → `_archive/webapp_microfrontends_2026-05-12/`
- [x] `_archive/webapp_microfrontends_2026-05-12/README.md` créé (mapping + restore-procedure)
- [x] `.gitignore` whitelist `!_archive/webapp_microfrontends_2026-05-12/**`
- [x] `webapp/package-lock.json` regen post-archive (no more `extraneous: true` entries)
- [x] **Gate-vert tous exit 0** :
  - lint_code_hygiene : 1 FAIL pré-existant baseline `scripts/seed_supabase_test_data.py` (≤ 2 baseline, non touché par FR-1)
  - SCHEMA validate_all : ✓ 15 files
  - parity_check weglot : ✓ exit 0
  - audit_capabilities : ✓ 0 orphans HIGH
  - npm install : ✓ exit 0
  - typecheck shell : ✓ exit 0
  - build shell : ✓ exit 0 (17 routes générées, 87.3 KB shared bundle, middleware 78.5 KB)
- [x] **Commit 1** : `871fb6c` `feat(webapp): consolidate 5 microfrontends scaffold → shell single Next.js app (FR-1)`
- [x] MANIFEST §12 updated avec entry 2026-05-13
- [x] Architecture map regen : 240 modules, 17 data artefact patterns, 7 pipelines
- [x] CAPABILITIES_REGISTRY + CAPABILITIES_SUMMARY regen
- [x] **Commit 2** : `c741f6a` `docs: manifest §12 — add 2026-05-13 changelog for webapp consolidate (FR-1)`
- [x] `git status` clean post-commits
- [x] 0 régression V3.2.1/V3.3, parity weglot, SCHEMA, doctrine immutable
- [x] PAS de push (laisse Mathis merger à la fin)

## Output summary

- **110 files changed, 3751 insertions(+), 2054 deletions(-)**
- 5 microfrontends archivés (60 files renamed via git mv)
- 27 new files in shell : 9 pages, 13 components, 3 lib, 1 API route, 1 archive README
- 4 modified files in shell : page.tsx, globals.css, Sidebar.tsx, next.config.js
- 2 modified files in webapp/ : package.json, package-lock.json
- 1 deleted file : microfrontends.json
- 1 modified file : .gitignore (whitelist archive subdir)
- 5 new CCPM files : prd + epic + 4 tasks + 4 progress.md
- 4 modified docs : MANIFEST §12, WEBAPP_ARCHITECTURE_MAP.yaml, CAPABILITIES_REGISTRY.json, CAPABILITIES_SUMMARY.md
