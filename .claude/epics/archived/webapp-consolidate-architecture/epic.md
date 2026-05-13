---
name: webapp-consolidate-architecture
status: in_progress
created: 2026-05-13T09:42:00Z
updated: 2026-05-13T09:42:00Z
progress: 0%
prd: .claude/prds/webapp-consolidate-architecture.md
github: (no GitHub sync — solo worktree)
---

# Epic: webapp-consolidate-architecture

## Overview

Refactor mécanique : consolider 5 microfrontends Next.js scaffold (`webapp/apps/{audit-app,reco-app,gsg-studio,reality-monitor,learning-lab}`) dans le shell unique `webapp/apps/shell/`. Préserve 100% du comportement observable. Archive les 5 dirs source sous `_archive/webapp_microfrontends_2026-05-12/`. 1 deploy Vercel, 1 typecheck, 1 build.

## Architecture Decisions

### AD-1 — Routes en pluriel REST-style
`/audits` et `/recos` (pas `/audit` et `/reco`) — convention cohérente avec les collections data Supabase (table `audits`, `recos`) et avec les futures sections `/clients`, `/recos?priority=P0`.

### AD-2 — Components groupés par feature dans le shell
`webapp/apps/shell/components/{audits,recos,gsg,reality,learning}/*.tsx` plutôt que flat. Évite collision de noms (`Studio.tsx` GSG vs un futur `Studio.tsx` ailleurs) et donne un dossier de search facile par feature.

### AD-3 — Lib factorisé seulement quand identique
- `supabase-server.ts` identique cross-app → garde celui du shell, supprime les 4 doublons des microfrontends.
- `use-supabase.ts` identique cross-app → idem.
- `reality-fs.ts`, `proposals-fs.ts`, `gsg-api.ts` feature-specific → déplacés `lib/` shell (pas sous-dossier — convention Next.js).

### AD-4 — Globals CSS concaténés, pas factorisés
Les classes `.gc-audit-shell`, `.gc-reco-shell`, `.gc-gsg-shell` sont concaténées dans `webapp/apps/shell/app/globals.css`. Pas de split CSS module = simpler. Doctrine permet : 1 fichier CSS shell global.

### AD-5 — Layouts microfrontends absorbés par root layout
Les `layout.tsx` des microfrontends (qui déclaraient `<html lang="fr"><body>`) sont supprimés car le `webapp/apps/shell/app/layout.tsx` les gouverne déjà.

### AD-6 — Archive via `git mv`, pas `rm`
Préservation history. `_archive/webapp_microfrontends_2026-05-12/` avec README explicatif.

## Tasks Breakdown

1. **001** — Move audit-app + reco-app routes/components → shell
2. **002** — Move gsg-studio + reality-monitor + learning-lab → shell (incl. API route `learning/proposals/review`)
3. **003** — Update Sidebar + delete microfrontends.json + update package.json scripts
4. **004** — Archive 5 dirs + run gate-vert + 2 commits + architecture map regen

## Acceptance Criteria

- [ ] 5 microfrontends absents de `webapp/apps/`
- [ ] `webapp/microfrontends.json` supprimé
- [ ] Sidebar pointe `/audits` + `/recos`
- [ ] Tous les gates exit 0 (lint, schemas, parity, audit_capabilities, install, typecheck, build)
- [ ] 2 commits sur `epic/webapp-consolidate-architecture`
- [ ] `git status` clean
- [ ] Architecture map regen committed

## Dependencies

- `main` HEAD `e38939b` post 2026-05-13.
- `@growthcro/{data,ui,config}` packages stables (pas de modif).
- Doctrine V3.2.1 + V3.3 immuables.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Import paths break post-move | M | H | Test typecheck après chaque task |
| `reality-fs.ts` path resolution casse | L | M | `process.cwd(),"..","..",".."` reste valide (même profondeur) |
| Globals CSS conflict avec shell | L | L | Concaténation simple, pas de redéfinition |
| Layout duplication régresse `<html lang>` | L | L | Shell `app/layout.tsx` déjà déclare `lang="fr"` |
| Gate fail bloque commit | M | H | Diagnostic + fix, jamais skip |
| Architecture map ne se regen pas | L | L | Run manuel `python3 scripts/update_architecture_map.py` |

## Definition of Done

- Code changes shipped : 5 microfrontends consolidés dans shell.
- 2 commits propres avec messages descriptifs.
- Gate-vert tous exit 0.
- Architecture map regen + committed.
- Working tree clean.
- README archive explique la migration.
