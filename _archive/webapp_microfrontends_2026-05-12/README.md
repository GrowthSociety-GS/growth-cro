# webapp/apps/ microfrontends scaffold — archived 2026-05-12

## Why archived

Sub-PRD `webapp-consolidate-architecture` (FR-1 of master `webapp-full-buildout`),
decision Mathis 2026-05-12 : pour 1 dev solo + ~100 clients, 6 projets Vercel
séparés est overkill. Consolidation dans 1 single Next.js shell.

## Contents

- `audit-app/` — Audit pane scaffold (déplacé vers `webapp/apps/shell/app/audits/`)
- `reco-app/` — Recos pane scaffold (déplacé vers `webapp/apps/shell/app/recos/`)
- `gsg-studio/` — GSG Studio scaffold (déplacé vers `webapp/apps/shell/app/gsg/`)
- `reality-monitor/` — Reality Monitor scaffold (déplacé vers `webapp/apps/shell/app/reality/`)
- `learning-lab/` — Learning Lab scaffold (déplacé vers `webapp/apps/shell/app/learning/`)

## Mapping détaillé (source → target dans le shell)

| Source archivée | Target dans `webapp/apps/shell/` |
|-----------------|----------------------------------|
| `audit-app/app/page.tsx` | `app/audits/page.tsx` |
| `audit-app/app/[clientSlug]/page.tsx` | `app/audits/[clientSlug]/page.tsx` |
| `audit-app/components/AuditDetail.tsx` | `components/audits/AuditDetail.tsx` |
| `audit-app/components/ClientPicker.tsx` | `components/audits/ClientPicker.tsx` |
| `reco-app/app/page.tsx` | `app/recos/page.tsx` |
| `reco-app/app/[clientSlug]/page.tsx` | `app/recos/[clientSlug]/page.tsx` |
| `reco-app/components/RecoList.tsx` | `components/recos/RecoList.tsx` |
| `gsg-studio/app/page.tsx` | `app/gsg/page.tsx` |
| `gsg-studio/components/{BriefWizard,LpPreview,Studio}.tsx` | `components/gsg/*.tsx` |
| `gsg-studio/lib/api.ts` | `lib/gsg-api.ts` |
| `reality-monitor/app/page.tsx` | `app/reality/page.tsx` |
| `reality-monitor/app/[clientSlug]/page.tsx` | `app/reality/[clientSlug]/page.tsx` |
| `reality-monitor/components/*.tsx` | `components/reality/*.tsx` |
| `reality-monitor/lib/reality-fs.ts` | `lib/reality-fs.ts` |
| `learning-lab/app/page.tsx` | `app/learning/page.tsx` |
| `learning-lab/app/[proposalId]/page.tsx` | `app/learning/[proposalId]/page.tsx` |
| `learning-lab/app/api/proposals/review/route.ts` | `app/api/learning/proposals/review/route.ts` |
| `learning-lab/components/*.tsx` | `components/learning/*.tsx` |
| `learning-lab/lib/proposals-fs.ts` | `lib/proposals-fs.ts` |

Layouts microfrontends (`<name>/app/layout.tsx`) supprimés — le root layout du
shell (`webapp/apps/shell/app/layout.tsx`) gouverne. Globals CSS feature
(`audit-app/app/globals.css`, `reco-app/app/globals.css`, `gsg-studio/app/globals.css`)
concaténés dans `webapp/apps/shell/app/globals.css`. `supabase-server.ts` et
`use-supabase.ts` (identiques cross-app) ne sont pas dupliqués — seul le shell
les conserve.

## Routing changes (visible côté user)

- `/audit` → `/audits` (REST plural)
- `/audit/<slug>` → `/audits/<slug>`
- `/reco` → `/recos`
- `/reco/<slug>` → `/recos/<slug>`
- `/gsg`, `/reality`, `/reality/<slug>`, `/learning`, `/learning/<id>` : inchangés
- `/learning/api/proposals/review` → `/api/learning/proposals/review` (Next.js API route shell-scoped)

## Restore procedure (si décision V2 inverse)

1. `git mv _archive/webapp_microfrontends_2026-05-12/<name> webapp/apps/<name>`
2. Restore `webapp/microfrontends.json` depuis git history (commit antérieur à `feat(webapp): consolidate`)
3. Restore `webapp/package.json` scripts `dev:audit`, `dev:reco`, `dev:gsg`, `dev:reality`, `dev:learning`
4. Restore `webapp/apps/shell/next.config.js` bloc `rewrites()`
5. Setup 5 nouveaux projets Vercel avec hosts `growthcro-{name}.vercel.app`
6. Restaurer la Sidebar.tsx pour pointer vers les URLs host-based externes

## Original migration commit

Cf commit `feat(webapp): consolidate 5 microfrontends scaffold → shell single Next.js app (FR-1)`.

## See also

- Master PRD : `.claude/prds/webapp-full-buildout.md` (FR-1 lines 107-119)
- Sub-PRD : `.claude/prds/webapp-consolidate-architecture.md`
- Epic : `.claude/epics/webapp-consolidate-architecture/epic.md`
