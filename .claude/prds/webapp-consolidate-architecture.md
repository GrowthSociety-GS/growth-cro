---
name: webapp-consolidate-architecture
description: Refactor mécanique des 5 microfrontends Next.js scaffold (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) dans le shell unique webapp/apps/shell/. 1 deploy Vercel, 1 maintenance, routing /audits, /recos, /gsg, /reality, /learning. Préserve 100% de la fonctionnalité observable, aucun changement de doctrine/schema/Supabase.
status: active
created: 2026-05-13T09:42:00Z
parent_prd: webapp-full-buildout
github_epic: (no GitHub sync — solo worktree)
wave: B-extended
epic_index: 4-extended.FR1
ice_score: 350
---

# PRD: webapp-consolidate-architecture

> Sub-PRD **FR-1** du master [`webapp-full-buildout`](webapp-full-buildout.md). Foundation blocking — tous les sub-PRDs suivants (FR-2/3/5/6) dépendent du paysage routing post-consolidation.

## Executive Summary

Le repo `webapp/` contient 6 apps Next.js workspaces : 1 `shell` deployé (live https://growth-cro.vercel.app) + 5 microfrontends scaffold (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) non-deployés. Les microfrontends ne sont accessibles que sur localhost (`microfrontends.json` route les paths `/audit/*`, `/reco/*`, `/gsg/*`, `/reality/*`, `/learning/*` vers fallbacks 404 en production).

**Décision Mathis 2026-05-12** : pour 1 dev solo + ~100 clients, déployer 6 projets Vercel séparés est overkill. Consolider tout dans 1 single Next.js shell = 1 deploy + 1 typecheck + 1 build + routing simple via Next.js App Router.

**Scope FR-1 (cette PRD)** : refactor mécanique sans changement de comportement utilisateur observable. 100% des composants/routes des 5 microfrontends sont déplacés dans `webapp/apps/shell/` selon le mapping :
- `apps/audit-app/app/page.tsx` → `apps/shell/app/audits/page.tsx`
- `apps/audit-app/app/[clientSlug]/page.tsx` → `apps/shell/app/audits/[clientSlug]/page.tsx`
- `apps/reco-app/app/page.tsx` → `apps/shell/app/recos/page.tsx`
- `apps/reco-app/app/[clientSlug]/page.tsx` → `apps/shell/app/recos/[clientSlug]/page.tsx`
- `apps/gsg-studio/app/page.tsx` → `apps/shell/app/gsg/page.tsx`
- `apps/reality-monitor/app/page.tsx` → `apps/shell/app/reality/page.tsx`
- `apps/reality-monitor/app/[clientSlug]/page.tsx` → `apps/shell/app/reality/[clientSlug]/page.tsx`
- `apps/learning-lab/app/page.tsx` → `apps/shell/app/learning/page.tsx`
- `apps/learning-lab/app/[proposalId]/page.tsx` → `apps/shell/app/learning/[proposalId]/page.tsx`
- `apps/learning-lab/app/api/proposals/review/route.ts` → `apps/shell/app/api/learning/proposals/review/route.ts`

Composants → `apps/shell/components/{audits,recos,gsg,reality,learning}/`.
Lib feature-specific → `apps/shell/lib/{reality-fs,proposals-fs}.ts` (supabase-server.ts factorisé sur celui du shell, identique cross-app).
Layouts microfrontends absorbés par le root layout du shell (déjà fait, redondant). Globals CSS feature-specific concaténés dans le `shell/app/globals.css`.

**Sidebar update** : `/audit` → `/audits` (pluriel), `/reco` → `/recos` (pluriel), labels "Audits" + "Recos". Suppression du rewrite localhost dans `next.config.js`.

Les 5 dirs source archivés sous `_archive/webapp_microfrontends_2026-05-12/` (préservation history via `git mv`).

**Coût API** : $0 (refactor mécanique).
**Effort** : M, 1-1.5j wall-clock. Cette session : ~45-60 min agent run.

## Problem Statement

### Pourquoi maintenant

1. **Coût d'opération** : 6 projets Vercel = 6× environnement + 6× CI + 6× domain. Pour Mathis solo, c'est 6× la mainternance pour 1× la valeur.
2. **Bug latent** : `microfrontends.json` route `/audit/*` vers `growthcro-audit.vercel.app` qui retourne 404. Les liens du shell (Sidebar.tsx) pointent vers `/audit` → expérience cassée.
3. **Sunk cost** : refactor mécanique maintenant = 1.5j. Dans 3 mois, avec features ajoutées dans chaque microfrontend, = 2 semaines.
4. **Foundation blocking** : FR-2 (clients/audits/recos), FR-3 (gsg-studio), FR-4 (learning-lab), FR-5 (settings), FR-6 (polish) doivent tous savoir où vivent les pages.

### Ce que ce sub-PRD apporte

- **1 deploy Vercel** : `growth-cro` shell unique, tous les paths `/audits`, `/recos`, `/gsg`, `/reality`, `/learning` servi par le même build Next.js.
- **Mono-concern préservé** : chaque composant déplacé reste 1 file = 1 concern. Pas de split, pas de merge sémantique. Just move.
- **Tooling simplifié** : 1 typecheck (`npm --workspace @growthcro/shell run typecheck`), 1 build, 1 ESLint config.
- **Archive history** : les 5 microfrontends archivés (pas supprimés) avec README explicatif. Restaurable si décision V2 inverse.
- **Sidebar cohérent** : Next.js Link interne, pas de host-based routing.

## User Stories

### US-1 — Mathis (dev solo)
*Comme founder solo qui maintient la webapp, je veux 1 single Next.js project à déployer/débugguer, pour gagner 5× de temps sur chaque commit.*

**AC** : `vercel.json` inchangé build `apps/shell`. Aucun rebuild des 5 microfrontends. 0 référence à `microfrontends.json` côté production.

### US-2 — Consultant Growth Society (futur user)
*Comme consultant qui clique sur les liens Sidebar, je veux que `/audits` charge la page audit et `/recos` charge la page reco, sans erreur 404.*

**AC** : Sidebar liens `/audits` et `/recos` (pluriel, cohérent avec la convention REST). Click → page Next.js RSC rendue, pas 404.

### US-3 — Mathis (audit history préservée)
*Comme founder qui veut pouvoir revoir l'historique du repo, je veux les 5 microfrontends archivés via `git mv`, pas supprimés.*

**AC** : `git log --follow webapp/apps/audit-app/app/page.tsx` montre les commits d'origine après archive. `_archive/webapp_microfrontends_2026-05-12/audit-app/` contient les fichiers d'origine inchangés.

## Functional Requirements (4 tasks)

### T001 — Move audit-app + reco-app routes/components/lib
- **Effort** : S, 15-20 min
- **Cible** :
  - `webapp/apps/audit-app/app/*` → `webapp/apps/shell/app/audits/*` (page.tsx + [clientSlug]/page.tsx)
  - `webapp/apps/audit-app/components/*` → `webapp/apps/shell/components/audits/*` (AuditDetail, ClientPicker)
  - `webapp/apps/reco-app/app/*` → `webapp/apps/shell/app/recos/*` (page.tsx + [clientSlug]/page.tsx)
  - `webapp/apps/reco-app/components/*` → `webapp/apps/shell/components/recos/*` (RecoList)
  - `webapp/apps/audit-app/app/globals.css` + `webapp/apps/reco-app/app/globals.css` concaténés dans `webapp/apps/shell/app/globals.css`
  - Imports `@/components/AuditDetail` → `@/components/audits/AuditDetail` (cf shell tsconfig paths `@/* → ./*`)
  - `supabase-server.ts` source-file mis au rebut (shell a le sien identique déjà)
  - Cross-feature links updated : `/audit/${slug}` → `/audits/${slug}`, `/reco/${slug}` → `/recos/${slug}`
- **AC** : `npm --workspace @growthcro/shell run typecheck` exit 0 après cette task isolément.

### T002 — Move gsg-studio + reality-monitor + learning-lab
- **Effort** : M, 20-25 min
- **Cible** :
  - `webapp/apps/gsg-studio/app/*` → `webapp/apps/shell/app/gsg/*` (page.tsx)
  - `webapp/apps/gsg-studio/components/*` → `webapp/apps/shell/components/gsg/*` (BriefWizard, LpPreview, Studio)
  - `webapp/apps/gsg-studio/lib/api.ts` → `webapp/apps/shell/lib/gsg-api.ts`
  - `webapp/apps/gsg-studio/lib/use-supabase.ts` → utiliser `@/lib/use-supabase` du shell (identique)
  - `webapp/apps/gsg-studio/app/globals.css` concaténé dans `webapp/apps/shell/app/globals.css`
  - `webapp/apps/reality-monitor/app/*` → `webapp/apps/shell/app/reality/*` (page.tsx + [clientSlug]/page.tsx)
  - `webapp/apps/reality-monitor/components/*` → `webapp/apps/shell/components/reality/*`
  - `webapp/apps/reality-monitor/lib/reality-fs.ts` → `webapp/apps/shell/lib/reality-fs.ts` (path `process.cwd()` 3 levels: still correct after move)
  - `webapp/apps/learning-lab/app/*` → `webapp/apps/shell/app/learning/*` (page.tsx + [proposalId]/page.tsx)
  - `webapp/apps/learning-lab/app/api/proposals/review/route.ts` → `webapp/apps/shell/app/api/learning/proposals/review/route.ts`
  - `webapp/apps/learning-lab/components/*` → `webapp/apps/shell/components/learning/*`
  - `webapp/apps/learning-lab/lib/proposals-fs.ts` → `webapp/apps/shell/lib/proposals-fs.ts`
  - Imports relatifs (`../lib/proposals-fs`, `../../lib/reality-fs`, etc.) ajustés selon nouvelle profondeur
  - Client `fetch('/learning/api/proposals/review')` → `fetch('/api/learning/proposals/review')` dans `ProposalDetail.tsx` déplacé
- **AC** : `npm --workspace @growthcro/shell run typecheck` exit 0 après cette task.

### T003 — Update Sidebar + delete microfrontends.json + update workspace
- **Effort** : XS, 10 min
- **Cible** :
  - `webapp/apps/shell/components/Sidebar.tsx` : items array updated
    - `{label:"Audit", href:"/audit"}` → `{label:"Audits", href:"/audits"}`
    - `{label:"Recos", href:"/reco"}` → `{label:"Recos", href:"/recos"}`
  - `webapp/apps/shell/app/page.tsx` : liens `/audit` → `/audits`, `/audit/${slug}` → `/audits/${slug}`
  - `webapp/apps/shell/next.config.js` : retirer le bloc `rewrites()` complètement (plus de microfrontends localhost)
  - `webapp/microfrontends.json` : supprimer (rm via git)
  - `webapp/package.json` : retirer scripts `dev:audit`, `dev:reco`, `dev:gsg`, `dev:reality`, `dev:learning`
  - `webapp/vercel.json` : inchangé (build apps/shell already correct)
- **AC** : grep `/audit ` (espace, pas slug) côté shell retourne 0 résultats hors comments. Sidebar montre 6 items (Overview, Audits, Recos, GSG Studio, Reality, Learning) + 2 agency (audit-gads, audit-meta) inchangés.

### T004 — Archive 5 source dirs + run gate-vert + 2 commits
- **Effort** : S, 10-15 min
- **Cible** :
  - `git mv webapp/apps/audit-app _archive/webapp_microfrontends_2026-05-12/audit-app`
  - `git mv webapp/apps/reco-app _archive/webapp_microfrontends_2026-05-12/reco-app`
  - `git mv webapp/apps/gsg-studio _archive/webapp_microfrontends_2026-05-12/gsg-studio`
  - `git mv webapp/apps/reality-monitor _archive/webapp_microfrontends_2026-05-12/reality-monitor`
  - `git mv webapp/apps/learning-lab _archive/webapp_microfrontends_2026-05-12/learning-lab`
  - Écrire `_archive/webapp_microfrontends_2026-05-12/README.md` (raison, mapping, restore-procedure)
  - Run gate-vert obligatoire (lint, schemas, parity, audit_capabilities, npm install, typecheck, build)
  - Commit 1 : `feat(webapp): consolidate 5 microfrontends scaffold → shell single Next.js app (FR-1)`
  - Update `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 changelog + regenerate architecture map
  - Commit 2 : `docs: manifest §12 — add 2026-05-13 changelog for webapp consolidate (FR-1)`
- **AC** : `git status` clean post-commits. Tous les gates exit 0.

## Non-Functional Requirements

### Doctrine
- V26.AF immutable. V3.2.1 + V3.3 immutable. Doctrine code mono-concern.
- Tous les fichiers TS/TSX déplacés restent ≤ 800 LOC (vérification post-move).
- Préservation 100% du comportement observable : mêmes pages, mêmes composants, mêmes data queries.

### Compatibilité
- Aucun breaking change `@growthcro/data`, `@growthcro/ui`, `@growthcro/config`.
- Aucun breaking change Supabase schema, migrations, seed.
- Vercel auto-deploy fonctionne sur push main post-merge.

### Sécurité
- Pas d'exposition de service_role côté client (route handlers serveur uniquement).
- Auth middleware shell `middleware.ts` couvre tous les paths consolidés automatiquement (matcher `((?!...))` exclut seulement les assets).

### Documentation
- MANIFEST §12 changelog post-merge.
- Architecture map regénéré post-consolidation (5 modules `webapp_microfrontend_*` retirés, paths `apps/shell/app/{audits,recos,gsg,reality,learning}` ajoutés).

## Success Criteria

- [ ] 5 microfrontends absents de `webapp/apps/` (présents sous `_archive/webapp_microfrontends_2026-05-12/`).
- [ ] `webapp/microfrontends.json` supprimé.
- [ ] `webapp/apps/shell/app/` contient les 5 sections (audits, recos, gsg, reality, learning).
- [ ] `webapp/apps/shell/components/` contient les 5 sous-dirs (audits/, recos/, gsg/, reality/, learning/).
- [ ] Sidebar.tsx pointe vers `/audits` + `/recos`.
- [ ] `python3 scripts/lint_code_hygiene.py` exit 0 (≤ baseline FAIL count).
- [ ] `python3 SCHEMA/validate_all.py` exit 0.
- [ ] `bash scripts/parity_check.sh weglot` exit 0.
- [ ] `python3 scripts/audit_capabilities.py` exit 0 (0 orphans HIGH).
- [ ] `cd webapp && npm install` resolve sans erreur.
- [ ] `npm --workspace @growthcro/shell run typecheck` exit 0.
- [ ] `npm --workspace @growthcro/shell run build` exit 0.
- [ ] 2 commits sur `epic/webapp-consolidate-architecture`.
- [ ] Working tree clean.
- [ ] Architecture map regen committed.

## Constraints & Assumptions

### Constraints
- Pas de push (Mathis merge à la fin).
- Pas de modif Notion.
- Pas de modif schema doctrine V3.2.1/V3.3.
- Pas de modif Supabase migrations/seed.
- Pas de modif `vercel.json`.
- Pas d'introduction de fichier TS/TSX > 800 LOC (split si nécessaire).

### Assumptions
- Les microfrontends scaffold sont **non-deployés** (Mathis confirmé : URLs fallback retournent 404).
- Personne ne consomme actuellement les routes `/audit`, `/reco`, `/gsg`, `/reality`, `/learning` en production (validation : seul user logged in est Mathis, qui voit la home page).
- `@growthcro/ui`, `@growthcro/data`, `@growthcro/config` packages stables, pas de breaking change.
- Node 20+, npm workspaces fonctionnels.

## Out of Scope

### Cette PRD (explicitement)
- Pas de modif fonctionnelle (juste le mécanique du move).
- Pas de nouvelle data query (`@growthcro/data` inchangé).
- Pas d'amélioration UX (responsive, loading states, error boundaries) → FR-6 polish.
- Pas de modif des pages `/audit-gads` et `/audit-meta` (déjà dans shell, hors-scope).
- Pas de modif de l'auth flow (`/login`, `/auth/callback`, middleware).

### Futur (deferred)
- FR-2 : wiring data Supabase aux pages clients/audits/recos avancées.
- FR-3 : GSG studio avec preview iframe des 4 LPs deliverables.
- FR-4 : learning lab table doctrine_proposals + vote UI.
- FR-5 : /settings 4 onglets.
- FR-6 : polish + validation.

## Dependencies

### Externes (humaines)
- Mathis review + merge post-PR.

### Externes (techniques)
- Aucune.

### Internes
- `main` HEAD `e38939b` post 2026-05-13 continuation plan.
- `webapp/packages/*` (data, ui, config) stables.
- Doctrine V3.2.1 + V3.3 schemas immuables.

### Sequencing
- T001 ⟶ T002 ⟶ T003 ⟶ T004 (séquentiel, agent solo dans worktree).

---

**Note finale** : cette PRD est intentionnellement scope-limited refactor mécanique. Les améliorations fonctionnelles sont reportées aux sub-PRDs suivants FR-2 à FR-6 du master `webapp-full-buildout`.
