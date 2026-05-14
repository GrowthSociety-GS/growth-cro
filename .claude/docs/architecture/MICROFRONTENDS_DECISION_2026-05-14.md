# Microfrontends Decision — 2026-05-14 (D1.A monorepo confirmed)

> **Status** : locked.
> **Authority** : Mathis, 2026-05-14T16:30Z.
> **Source-of-truth** : [`DECISIONS_2026-05-14.md` §D1](DECISIONS_2026-05-14.md).
> **Scope** : this doc expands the D1 ruling and freezes the surface that downstream artefacts
> (`architecture-explorer-data.js`, `PRODUCT_BOUNDARIES_V26AH.md`, `SKILLS_INTEGRATION_BLUEPRINT.md`,
> `GROWTHCRO_MANIFEST.md` §12) must mirror. Future drift "architecture says X, code does Y"
> is the failure mode this file exists to prevent.

## 1. Decision

**D1.A — keep the consolidated shell. Do NOT re-federate into 5 microfrontends.**

The webapp is a single Next.js 14 App Router application living at
`webapp/apps/shell/` (package `@growthcro/shell` v0.28.0). All product surfaces
(`/audits`, `/recos`, `/gsg`, `/reality`, `/learning`, `/clients`, `/settings`)
are routes inside that shell. There is **no** `microfrontends.json`, no Vercel
multi-zone routing, no per-feature Vercel project.

## 2. Why (expanded rationale)

The original V28 plan (2026-05-11, Epic #21) scaffolded 5 Vercel microfrontends
(`audit-app`, `reco-app`, `gsg-studio`, `reality-monitor`, `learning-lab`) +
shell, using `@vercel/microfrontends` for routing. The FR-1 sub-PRD
[`webapp-consolidate-architecture`](../../prds/webapp-consolidate-architecture.md)
rolled that back to a single shell on 2026-05-13. The reasons, in priority order:

1. **Solo dev reality** — Mathis is the only engineer. 6 Vercel projects = 6
   deploys to babysit, 6 sets of env vars, 6 preview URLs, 6 typecheck runs per
   PR. That overhead trades 0 isolation benefit (no team boundaries to defend)
   against measurable daily friction.

2. **~100 clients target, not 100 engineers** — Microfrontends solve org-scale
   problems (codeowners boundaries, independent release cadence per team).
   GrowthCRO has zero of those. The "scale" axis here is *audited clients*, not
   *frontend teams*.

3. **Simpler ops** — 1 deploy, 1 typecheck, 1 build, 1 bundle analysis, 1
   middleware, 1 set of auth cookies. The FR-1 consolidation measured the
   delta: 17 routes generated in `apps/shell`, 87.3 KB shared first-load,
   middleware 78.5 KB, 0 regression on doctrine / parity / SCHEMA / lint.

4. **No coupling tax avoided** — Microfrontends pay off when sub-apps share
   nothing (different stacks, different teams, different release windows). Our
   5 surfaces share Supabase auth, the same `@growthcro/data` types, the same
   design tokens, the same Realtime channel `public:runs`. Splitting them
   *re-introduces* coupling through shared packages instead of removing it.

5. **Aligned with FR-1** — The FR-1 epic completed 2026-05-13 already
   physically consolidated the 5 µfrontends into `apps/shell/app/{audits,
   recos, gsg, reality, learning}/`. Re-federating would un-do shipped work.

## 3. Trade-offs honestly stated

### Pros (kept by D1.A)

- **1 deploy / 1 build / 1 typecheck** — daily friction floor.
- **1 middleware** for auth gating (`requireAdmin()`, route guards).
- **No cross-zone routing config** to maintain (`microfrontends.json` deleted
  in FR-1).
- **Code mobility** — moving a component from `/audits` to `/recos` is a file
  move inside one app, not a package extraction.
- **Faster cold start** for users — one Next.js server, no cross-zone hop.

### Cons (accepted by D1.A)

- **No isolation between features** — a bad bundle import in
  `components/recos/` can blow up bundle size for `/audits` users too. Mitigation:
  bundle analyzer in CI, `vercel-react-best-practices` skill catching barrel
  imports + waterfalls.
- **Single point of failure** — one bad deploy takes down all features.
  Mitigation: Vercel preview + Playwright smoke (`runs-trigger.spec.ts`,
  `visual-dna-v22.spec.ts`, `wave-a*`) gate prod.
- **No independent release cadence** — can't ship `/gsg` without re-deploying
  `/audits`. Acceptable: solo dev never wants partial deploys anyway.
- **TypeScript / shared lib growth pressure** — as features grow, `apps/shell`
  can drift toward god-app. Mitigation: feature folders under
  `apps/shell/app/<feature>/` + components co-located, see §5 doctrine.

## 4. Migration path (if we ever outgrow the shell)

The trigger to re-evaluate D1.A is **organizational**, not technical:

- **Trigger A** — a 2nd full-time engineer joins, owns a coherent feature
  (e.g. GSG Studio), and codeowners boundaries become a real friction. Then
  evaluate D1.B re-federation, starting with the highest-cohesion feature
  (likely `/gsg` because of the BriefWizard + multi-judge stage strip + LP
  preview iframe).
- **Trigger B** — a feature outgrows the shared bundle envelope (e.g. GSG
  Studio adds a 1MB WASM renderer that we don't want on the `/audits` critical
  path). Then evaluate **lazy-loaded route-level code splitting first**, and
  only escalate to microfrontends if the split is still insufficient.

Until either trigger fires, D1.A holds. The migration path *back to
microfrontends* is documented in
[FR-1 epic](../../prds/webapp-consolidate-architecture.md) §restore-procedure +
the archive under `_archive/webapp_microfrontends_2026-05-12/` (git history
preserved, README + mapping + restore steps shipped).

## 5. Doctrine implications

- `webapp/apps/shell/` is the **single canonical surface**. New Next.js apps
  inside `webapp/apps/` are forbidden unless D1.B is unlocked.
- `microfrontends.json` is a banned filename in active paths.
- `vercel.json` stays scoped to `apps/shell`.
- Skill `vercel-microfrontends` is **dropped** from the permanent Webapp Next.js
  dev combo (see `SKILLS_INTEGRATION_BLUEPRINT.md` v1.4 §4.1.4). Rationale: a
  skill optimizing for an architecture we just rejected is a cacophony signal.
- Routes are folder-co-located under `apps/shell/app/<feature>/`. Cross-feature
  imports use `@/components/*` aliases, not relative paths across features.

## 6. Cross-references

- [`DECISIONS_2026-05-14.md` §D1](DECISIONS_2026-05-14.md) — locked decision.
- [`webapp-consolidate-architecture`](../../prds/webapp-consolidate-architecture.md) — FR-1 epic that physically did the consolidation.
- [`GROWTHCRO_MANIFEST.md` §12, 2026-05-13 entry](../reference/GROWTHCRO_MANIFEST.md) — FR-1 ship report.
- [`GROWTHCRO_MANIFEST.md` §12, 2026-05-15 entry](../reference/GROWTHCRO_MANIFEST.md) — D1.A confirmation via Task 016 (this doc).
- [`PRODUCT_BOUNDARIES_V26AH.md` §3 webapp topology](PRODUCT_BOUNDARIES_V26AH.md) — boundary note "1 shell, 0 µfrontend".
- [`SKILLS_INTEGRATION_BLUEPRINT.md` v1.4 §4.1.4](../reference/SKILLS_INTEGRATION_BLUEPRINT.md) — `vercel-microfrontends` dropped.
- [`architecture-explorer-data.js`](../../../deliverables/architecture-explorer-data.js) — `pipelines.webapp_v28.extra.microfrontends` collapsed to a single `@growthcro/shell` entry; `meta.revision_notes` records the revision.
- Archive : `_archive/webapp_microfrontends_2026-05-12/` (5 dirs `git mv`'d with history).

---

**Locked 2026-05-14, formalized 2026-05-15 via Sprint 10 / Task 016. Re-open only on Trigger A or B above.**
