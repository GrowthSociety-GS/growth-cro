# Audit A.8 — Performance (static perf-optimizer review) — 2026-05-14

Scope : `webapp/apps/shell/` (Next.js 14.2 App Router, RSC-first, Supabase auth/data, deployed on Vercel). STATIC review — no live Lighthouse / WebPageTest run. Estimates based on code patterns, bundle decisions, caching strategy, image loading, font loading, RSC boundaries.

---

## TL;DR

The perf posture is **surprisingly clean for a V26 webapp in flux**: lean dep tree (3 third-party libs total — `@supabase/ssr`, `@supabase/supabase-js`, `clsx`), aggressive RSC-first architecture (every chart/panel is server-rendered SVG, no Recharts/Chart.js), and only **55 `"use client"` files** in total (mostly leaves : modals, edit triggers, form widgets). The 5 biggest wins are all **architectural fixes, not code rewrites** : (1) the home `loadOverview()` does 3 sequential awaits where `Promise.all` would cut TTFB by ~2x, (2) `Inter` is referenced everywhere in CSS but never loaded (silent FOUT to `system-ui`), (3) `/audits/[clientSlug]` fan-out-fetches recos for ALL audits of a client when only the active page_type group is rendered, (4) every route is `force-dynamic` with zero `revalidate` / `unstable_cache` even though most reads change every few minutes, not on every request, (5) the `/api/screenshots/*` route runs the auth middleware on every redirect (fixable via the matcher regex).

---

## Rendering strategy summary

| Route | RSC default? | "use client" leaves only? | Suspense? | revalidate? | Notes |
|-------|--------------|--------------------------|-----------|-------------|-------|
| `/` (Command Center) | Yes (page is RSC) | Yes (FleetPanel + Sidebar = islands) | No | `force-dynamic` | `loadOverview` does 3 sequential awaits (waterfall) |
| `/clients` | Yes | Yes | No | `force-dynamic` | OK — single `listClientsWithStats` query, sort/filter in JS |
| `/clients/[slug]` | Yes | Yes (ClientDetailTabs island) | No | `force-dynamic` | Parallel `Promise.all` for audits/clients/role — OK |
| `/clients/[slug]/dna` | Yes | Yes | No | `force-dynamic` | — |
| `/audits` | Yes | Yes | No | `force-dynamic` | trivial |
| `/audits/[clientSlug]` | Yes | Yes | No | `force-dynamic` | **N+1 recos fetch** for ALL audits of client, only active page_type rendered |
| `/audits/[clientSlug]/[auditId]` | Yes | Yes (RichRecoCard) | No | `force-dynamic` | Good — `Promise.all([client, audit])` then `Promise.all([recos, siblings, role])` |
| `/audits/[clientSlug]/[auditId]/judges` | Yes | No | No | `force-dynamic` | — |
| `/recos` | Yes | Yes | No | `force-dynamic` | Loads `listRecosAggregate` (full cross-client recos table) every request |
| `/recos/[clientSlug]` | Yes | Yes | No | `force-dynamic` | — |
| `/funnel/[clientSlug]` | Yes | No | No | `force-dynamic` | Pure-SVG chart, lean |
| `/gsg`, `/learning`, `/reality`, `/doctrine`, `/settings`, `/login`, `/privacy`, `/terms` | Mostly RSC, GSG Studio is "use client" | Mixed | login has `<Suspense>` | mostly `force-dynamic` | — |

- **22 routes carry `force-dynamic`** — most are reasonable (auth-gated reads) but `/recos` (cross-client aggregator), `/clients` (fleet), `/audits` (index) could benefit from `revalidate=60` or `unstable_cache`.
- **No Suspense boundaries** except `/login` → no progressive streaming. The audits detail page awaits 5 Supabase round-trips before rendering anything; a Suspense around `<AuditDetailFull>` with skeleton would unblock the topbar.
- **No PPR / Cache Components** (Next.js 14.2 — PPR is opt-in, Cache Components is 16+). Migration to Next 15 + PPR is a Wave C candidate.
- **Heavy components stay server-rendered**: `AuditDetailFull` (171 LOC, all server), `AuditScreenshotsPanel` (146, server), `PillarRadialChart` (128, server), `FunnelDropOffChart` (94, server), `JudgesConsensusPanel` (96, server). Only `RichRecoCard` is `"use client"` (collapse state). This is the ideal RSC pattern.

---

## Data fetching audit

- **Pattern** : every page-level Server Component imports `createServerSupabase()` (cookies()-aware SSR client) and calls typed wrappers from `@growthcro/data/queries/*`. No `fetch()` with `next: { revalidate }`. No `unstable_cache`. No tag-based invalidation.
- **Waterfalls found** :
  - `app/page.tsx::loadOverview()` lines 47-61 — `clients`, `metrics`, `p0Counts` awaited **sequentially**, each in its own try/catch. Fix : single `Promise.allSettled([...])`. Estimated TTFB savings: ~60-200ms (3 RTTs collapsed to 1).
  - `components/command-center/ClientHeroDetail.tsx` lines 54-57 — `getClientBySlug` then `listAuditsForClient` are sequential (the second needs `client.id`). Acceptable.
  - `app/audits/[clientSlug]/page.tsx` lines 178-186 — `Promise.all(audits.map(a => listRecosForAudit(...)))`. Parallel inside, but **over-fetches**: every audit gets its recos even when only the active `page_type` group will be rendered. Fix : filter audits to active page_type first, then fan-out only on those.
- **Over-fetching risks** :
  - `/recos` aggregator loads `listRecosAggregate(supabase)` — the entire `recos_with_audit` view (potentially ~1k+ rows across 56 clients × 185 audits × N recos). Pagination is done **in memory** (JS slice). Server-side `range()` / `offset()` would cut payload by 50x on first paint.
  - `/clients` loads `listClientsWithStats` (the full view) then sorts/filters/paginates in JS. With ≤100 clients this is fine.
  - `/audits/[clientSlug]` loads ALL audits for the client even when filtered to one page_type (acceptable today — N audits per client ≤ 10).
- **Caching strategy** : zero. Every page hit re-runs Supabase queries. No `revalidate`, no `unstable_cache`, no Vercel Edge cache (`Cache-Control: s-maxage=...`). Cross-client data (`listRecosAggregate`, fleet stats) changes minutes-not-seconds; could be cached 60-300s.

---

## Bundle size opportunities

- **Heavy deps** : none. Production `dependencies` in `webapp/apps/shell/package.json` :
  - `@growthcro/config`, `@growthcro/data`, `@growthcro/ui` (workspace, all source — `transpilePackages` correctly set in next.config.js)
  - `@supabase/ssr ^0.3.0`
  - `@supabase/supabase-js ^2.43.0`
  - `next ^14.2.0`, `react ^18.2.0`, `react-dom ^18.2.0`
  - `@growthcro/ui` deps : `clsx` (1KB)
  - **No** lodash, moment, date-fns, full Recharts, Chart.js, AG-Grid, etc. All formatting is hand-rolled (`formatValue`, `formatPct`).
- **Build output** (`.next/static/chunks/`) :
  - Largest chunk : `1362-*.js` at 180KB (likely framework + supabase-js)
  - `framework-*.js` : 140KB (React + Next runtime)
  - `1dd3208c-*.js` : 172KB (likely Supabase auth helpers)
  - `1528-*.js` : 124KB
  - `main-*.js` : 116KB
  - `polyfills-*.js` : 112KB
  - **Total first-load JS estimate : ~280-320KB gzipped** for the typical Server Component route, ~350KB for routes with many client islands (gsg/Studio). Well under the 500KB watershed.
- **Dynamic import candidates** :
  - `components/audits/EditAuditModal.tsx`, `EditRecoModal.tsx`, `CreateAuditModal.tsx`, `common/DeleteConfirmModal.tsx`, `gsg/EndToEndDemoFlow.tsx` — all modals could be `dynamic(() => import('...'), { ssr: false })`. Saves ~10-30KB on initial load when modal is closed.
  - `components/gsg/Studio.tsx`, `BriefWizard.tsx` — heavy multi-step UIs. Only loaded on `/gsg`, but `BriefWizard` is 203 LOC and could be split per-step.
  - **Legacy `components/audits/AuditDetail.tsx`** : 121-LOC `"use client"` component imported nowhere by pages (only self-references). Verify it's tree-shaken in production build; if it leaks into a chunk it's dead weight.
- **Tree-shaking** : ESM-only (`"main": "./src/index.ts"` in workspace packages). `transpilePackages` ensures Next compiles the workspace, no CJS interop tax.

---

## Images

- **`next/image` usage : ZERO**. Confirmed via `grep -rn "next/image"` — no occurrences in app source. Only `next-env.d.ts` types reference. Screenshots in `AuditScreenshotsPanel.tsx` line 52 use raw `<img loading="lazy" src={src} alt={alt} />` with an explicit ESLint disable.
- **Why this matters in this app** : the screenshots are PNG/WebP at `1840×*` (desktop) and `390×*` (mobile fold) — way larger than any rendered thumbnail (≈200×width grid cell). Without `next/image` :
  - No automatic responsive `srcset` — desktop browsers download full 1840-wide WebPs to display at 200px.
  - No format negotiation (Vercel Image Optim auto-AVIF for Safari 16+, etc.).
  - No blur placeholder → CLS risk when thumbnails load.
  - Each thumbnail is ~150-400KB instead of ~10-25KB.
- **Mitigating factor** : Supabase Storage objects ARE WebP (q=75) per SP-11. So we save ~70% vs PNG, but still ~80KB/thumbnail vs ~15KB if Vercel Image Optim resized to 200px width.
- **Supabase remote pattern : NOT configured**. `next.config.js` has no `images.remotePatterns` block — so `<Image src="https://cqu...supabase.co/...">` would error today even if migrated.
- **Lazy loading** : `loading="lazy"` is set on the `<img>` tags. Good for below-fold thumbs but doesn't help LCP (the desktop fold thumbnail IS often the LCP element on `/audits/[id]`).
- **Decorative image** : `<div className="gc-grain" aria-hidden />` (layout.tsx line 23) — likely a CSS background-image grain texture. Verify it's compressed.

---

## Fonts

- **`next/font` usage : ZERO**. Confirmed via grep.
- **Inter referenced but never loaded** : `packages/ui/src/styles.css:32` sets `font-family: Inter, ui-sans-serif, system-ui, ...` and `packages/ui/src/tokens.ts:24` exports `font: 'Inter, ui-sans-serif, ...'`. `FunnelDropOffChart.tsx` line 63 sets `fontFamily="Inter, system-ui, sans-serif"` on SVG `<text>`. **No `<link rel="preconnect">` to Google Fonts, no `@font-face` rule, no `next/font/google` import.** Browsers silently fall back to `ui-sans-serif`/`system-ui` (San Francisco on macOS, Segoe UI on Windows, Roboto on Android).
- **Impact** : not a perf bug per se (no FOUT — system fonts load instantly), but a **visual fidelity drift** : design intent was Inter, render reality is system. CLS = 0 from fonts (good side effect of accidental system-font use).
- **monospace fallback stack** : `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` — system-only. OK.
- **font display swap** : N/A — no custom font is loaded.
- **Action** : either (a) accept system fonts and remove `Inter` from CSS/tokens (perf-positive, fewer surprises), or (b) wire `next/font/google` Inter in `app/layout.tsx`, propagate the CSS variable, and add `priority` on the home route. Option (a) is faster, option (b) preserves design intent.

---

## HTTP / Edge / Runtime cache

- **API route headers** : `/api/screenshots/[client]/[page]/[filename]/route.ts` sets `Cache-Control: public, max-age=3600` on the fs-fallback path (line 124) and `max-age=300` on the 302 redirect to Supabase (line 93). Reasonable.
- **All other API routes** (`/api/audits/*`, `/api/recos/*`, `/api/clients/*`, `/api/learning/*`, `/api/team/*`, `/api/gsg/*`) — **no explicit cache headers**. They're auth-gated mutations mostly, so default `no-store` is fine.
- **Page-level cache** : zero — every page exports `dynamic = "force-dynamic"`. No `revalidate`, no `s-maxage`. Vercel will not cache any HTML.
- **Runtime Cache API** : not used. Could memoize fleet-wide aggregates (P0 counts, recos aggregator) per-region for 60-300s to drop TTFB from ~400-800ms to ~30-80ms.
- **Edge runtime** : the screenshots route pins `runtime = "nodejs"` (justified — `fs.readFileSync` fallback). Other routes default to Node. None opt into Edge runtime — fine given Supabase auth latency profile.

---

## Middleware / Edge

- **`webapp/apps/shell/middleware.ts`** : runs `createServerClient` (Supabase SSR) and `supabase.auth.getUser()` on EVERY request except public paths. The matcher excludes `_next/static`, `_next/image`, `favicon.ico`, and direct image extensions BUT includes `/api/screenshots/[client]/[page]/[filename]` — so each thumbnail load triggers a Supabase auth round-trip before the 302 to Storage CDN.
- **Impact** : every `<img src="/api/screenshots/...">` adds ~50-200ms cold-call to Supabase auth-getUser before redirecting. With 8 thumbnails per audit page = 8 × 50-200ms = 400ms-1.6s waterfall on first paint. Even with `loading="lazy"` the desktop+mobile fold thumbs render eagerly.
- **Fix** : extend the matcher exclusion to `^/api/screenshots/`. Screenshots are public objects (no PII — Supabase bucket is `public=true`), gating them via auth middleware adds latency for zero security gain (the API route already validates slug shape).
- **No other heavy logic** in middleware — just auth check + redirect to `/login` if unauth. Acceptable.

---

## Third-party scripts

- **`next/script` usage : ZERO**.
- **Confirmed deps for third-party JS** : none. No GA, no Hotjar, no Sentry, no PostHog, no Datadog RUM, no Vercel Analytics, no Vercel Speed Insights. The only third-party fetch is **Supabase** (auth + queries, server-side).
- **`<ConsentBanner />`** (layout.tsx line 24) — internal `@growthcro/ui` component. Renders client-side but loads with the main bundle, not a third-party tag. OK.
- **Implication** : no `strategy=afterInteractive` / `lazyOnload` concerns. The downside is **no production RUM** — perf regressions ship undetected. Wave C should at minimum install `@vercel/speed-insights` (it's ~3KB gzipped, runs after `load`).

---

## Server Actions vs API routes

- **Server Actions : not used**. All mutations go through traditional REST API routes (`/api/audits/[id]` PATCH, `/api/recos/[id]` PATCH, etc.).
- **Cost** : extra round-trip per mutation (browser → API → Supabase → API → browser), no automatic revalidation, no `useOptimistic` ergonomics. With 6-8 modals in the codebase, migrating to Server Actions would cut ~50-100ms per save AND simplify the code (`<form action={saveAudit}>` vs `fetch + setState + revalidate`).
- **Not blocking** — REST routes work. Wave C/D candidate.

---

## Identify the heaviest component

The heaviest rendered tree on the hot path (audit detail) is **`AuditDetailFull` + children**, totaling ~171 + 146 + 128 + 184 = **~630 LOC of TSX** (all server-rendered except `RichRecoCard`). HTML output per audit detail page is ~30-80KB depending on reco count. Render-time cost is dominated by **Supabase data fetches in the parent page** (5 round-trips, ~150-400ms total), NOT by component rendering.

The heaviest client bundle contributor is **`gsg/Studio.tsx` + `BriefWizard.tsx` + `EndToEndDemoFlow.tsx` (`"use client"` × 358 LOC combined)** on `/gsg`. They're loaded only when visiting `/gsg`, so first-load JS for other routes is unaffected.

The **highest LCP risk** is the **`AuditScreenshotsPanel` desktop+mobile fold thumbnails on `/audits/[clientSlug]/[auditId]`** : two raw `<img>` tags loading 80-300KB each from Supabase Storage CDN (3rd-party origin, no preconnect), with a 50-200ms middleware auth hop in between. **Estimated LCP : 1.8-3.2s on cable, 3-6s on Slow 3G**. Replacing with `next/image` + `priority` on the desktop-fold thumb and configuring the Supabase remote pattern would cut this by ~2x.

---

## P0 perf bugs (real broken)

1. **Middleware runs on `/api/screenshots/*`** → every thumbnail load hits Supabase auth. File : `webapp/apps/shell/middleware.ts:49`. Fix : add `api/screenshots` to the matcher negative lookahead, e.g. `/((?!_next/static|_next/image|favicon.ico|api/screenshots|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)`. Impact : -50-200ms per thumbnail × 8 thumbs/page = potentially -1s on `/audits/[id]` first paint.
2. **`Inter` font referenced but never loaded** → silent fallback to system fonts everywhere. File : `webapp/packages/ui/src/styles.css:32`, `tokens.ts:24`. Not a perf regression (system fonts are free) but a design-fidelity bug. Decide : adopt system fonts officially OR wire `next/font/google` Inter in `app/layout.tsx`. **Recommend (a)** : remove `Inter` from CSS/tokens, save 30-50KB font file + 1 connection, accept system fonts.
3. **`loadOverview()` waterfall on `/`** → 3 sequential awaits. File : `webapp/apps/shell/app/page.tsx:47-61`. Fix : wrap in `Promise.allSettled([listClientsWithStats(supabase), loadCommandCenterMetrics(supabase), loadP0CountsByClient(supabase)])`. Impact : -60-200ms TTFB on home.

## P1 perf opportunities (visible win)

4. **No `next/image` for screenshots** → no responsive `srcset`, no AVIF, no blur placeholder. Files : `webapp/apps/shell/components/audits/AuditScreenshotsPanel.tsx:52`. Fix : add `images.remotePatterns` for the Supabase Storage hostname in `next.config.js`, swap `<img>` for `<Image src="https://<project>.supabase.co/storage/v1/object/public/screenshots/..." width={1840} height={...} sizes="(max-width: 768px) 100vw, 33vw" priority={isFirstFold} />`. Impact : -50-70% bytes on screenshot thumbnails, -1-2s LCP on audit detail page.
5. **`/audits/[clientSlug]` over-fetches recos for all audits, not just active page_type** → File : `webapp/apps/shell/app/audits/[clientSlug]/page.tsx:178-186`. Fix : compute `activeGroup` BEFORE the recos fan-out, then `Promise.all(activeAudits.map(...))`. Impact : -50-70% query volume on clients with many page_types.
6. **`/recos` aggregator paginates in memory** → loads entire `listRecosAggregate` table every request. File : `webapp/apps/shell/app/recos/page.tsx:79`. Fix : push pagination/sort to Supabase via `.range(start, start+PER_PAGE-1)` + DB-side `.order()`. Impact : -90% payload on first paint with 50/page (1000 rows → 50).
7. **Zero caching layer** → all reads re-run on every request. Files : all `app/**/page.tsx` with `dynamic = "force-dynamic"`. Fix : for fleet-wide aggregations (`listClientsWithStats`, `listRecosAggregate`, `loadCommandCenterMetrics`), wrap in `unstable_cache(fn, ['key'], { revalidate: 60, tags: ['recos'] })` and call `revalidateTag('recos')` from mutation API routes. Impact : -150-400ms TTFB on cached hits.
8. **No `Suspense` boundaries** → audit detail page awaits 5 round-trips serially before rendering anything. Files : `app/audits/[clientSlug]/[auditId]/page.tsx`. Fix : split the topbar (uses `client`/`audit` only) from `<AuditDetailFull>` (uses `recos`/`siblings`), wrap the second in `<Suspense fallback={<Skeleton/>}>`. Impact : -200-400ms perceived FCP.

## P2 perf nice-to-haves

9. **Modals load eagerly** → `EditAuditModal`, `EditRecoModal`, `CreateAuditModal`, `DeleteConfirmModal` all ship in initial bundle. Fix : `const EditAuditModal = dynamic(() => import('./EditAuditModal'), { ssr: false })`. Impact : -10-30KB on routes that have triggers but rarely open the modal.
10. **No `@vercel/speed-insights`** → blind to RUM regressions in prod. Fix : `npm i @vercel/speed-insights`, mount `<SpeedInsights />` in `app/layout.tsx`. Cost : +3KB gzipped, async after-load. Benefit : real CWV trendlines.
11. **No `@vercel/analytics`** → same logic for page views. Optional.
12. **Sequential `getClientBySlug` → `listAuditsForClient` in `ClientHeroDetail`** : can't easily parallelize (audits need client.id) BUT could be one combined Supabase RPC. Low priority.
13. **GSG Studio split** : `BriefWizard.tsx` is 203 LOC monolith — could be split per-step with `dynamic` imports. Only visited from `/gsg`. Low priority.
14. **Legacy `AuditDetail.tsx`** (121-LOC `"use client"`, unused by pages) — verify it's tree-shaken or delete. Low impact.
15. **No Edge runtime** anywhere — could move read-only API routes (`/api/audits/[id]` GET) to Edge for ~50-100ms global latency cut. Tradeoff : Supabase Node SDK isn't fully Edge-friendly; only worth it for heavy routes.
16. **PPR / Cache Components** (Next.js 15/16) : long-term refactor. Static-shell + dynamic-island pattern would let the Sidebar + KPI grid prerender while only the FleetPanel data streams. Major win on cold cache. Wave D+.

---

## Lighthouse expected scores (rough estimate based on patterns)

For typical authenticated routes (`/`, `/clients`, `/audits/[id]`) on cable + desktop :

- **Performance : ~72-85** — drag from (a) no `next/image` on screenshot-heavy routes (~-10-15pts), (b) no caching → high TTFB (~-5-10pts), (c) Supabase auth middleware on every request (~-3-5pts). After P0+P1 fixes : **88-95**.
- **Best Practices : ~92-96** — good ESM bundle, no console errors expected. Minor : missing `<link rel="preconnect">` to Supabase Storage hostname.
- **SEO : ~70-80** — `robots: "noindex,nofollow"` is intentional (admin tool), so SEO score is partly forced down. Title/meta/lang are correct.
- **A11y : see A.6 audit** (separate file).
- **Estimated TBT (Total Blocking Time)** : **low** (~50-150ms). Most rendering is server-side, client islands are small. Only risk : initial hydration of `RichRecoCard` × 10-20 on `/audits/[id]` could push TBT to ~200ms.
- **Estimated LCP** :
  - `/` (Command Center, no images) : **~1.4-2.2s** on cable, likely the KPI grid or FleetPanel.
  - `/audits/[id]` (with screenshots) : **~2.5-4s** cable, **~5-8s on Slow 3G**. The Supabase Storage thumbnails ARE the LCP element. Biggest single win = next/image migration.
- **Estimated CLS** : **~0.02-0.08** — `<img>` without explicit `width`/`height` on screenshots can shift layout, but the `gc-audit-screens__grid` CSS likely fixes the cell size. Verify.

---

## Recommendations Wave C priority

1. **Exclude `/api/screenshots/*` from the middleware matcher** (1-line fix, P0).
2. **Configure `images.remotePatterns` + migrate `<img>` to `next/image`** in `AuditScreenshotsPanel.tsx`, with `priority` on desktop+mobile fold and `sizes="(max-width: 768px) 100vw, 33vw"` (P0/P1).
3. **Parallelize `loadOverview()`** with `Promise.allSettled` (P0, 5 LOC change).
4. **Add `Suspense` around `<AuditDetailFull>`** on `/audits/[clientSlug]/[auditId]` with a skeleton fallback (P1).
5. **Decide on Inter** : either remove from CSS/tokens (simple) or wire `next/font/google` Inter in `app/layout.tsx` (preserves design intent, +1 connection) (P1).
6. **Push pagination to Supabase** for `/recos` aggregator (P1, ~10 LOC).
7. **Wrap fleet-wide aggregations in `unstable_cache(fn, [...], { revalidate: 60, tags })`** + `revalidateTag` from mutation routes (P1, ~30 LOC across 3-5 queries).
8. **Filter recos fan-out to active page_type** in `/audits/[clientSlug]/page.tsx` (P1, 3-line fix).
9. **Install `@vercel/speed-insights`** to start tracking RUM (P2, 5min).
10. **Dynamic-import the 5 modals** (`EditAuditModal`, etc.) (P2, ~15 LOC).

**Expected cumulative impact** (P0+P1 done) :
- Home `/` TTFB : 400-800ms → 200-400ms.
- Audit detail LCP : 2.5-4s → 1.5-2.5s.
- First-load JS on home : 280KB → ~250KB (modal dynamic imports).
- Lighthouse Performance score : **72-85 → 88-95** on the hot routes.

---

## Notes / non-issues spotted

- `reactStrictMode: true` (next.config.js) — good (catches lifecycle bugs in dev, no prod cost).
- `experimental.typedRoutes: false` — fine, no perf impact.
- `transpilePackages: ["@growthcro/ui", "@growthcro/data", "@growthcro/config"]` — correct for monorepo workspace packages.
- All SVG charts (PillarRadialChart, FunnelDropOffChart, FunnelStepsViz, JudgesConsensusPanel) are pure server-side SVG, zero JS overhead — **excellent pattern, preserve in Wave C**.
- Tree-shaking : ESM-only workspace packages, good.
- `globals.css` : 1600+ lines (single file). Consider CSS Modules for route-scoped styles to reduce per-route CSS payload (currently every route ships the full sheet). Low priority — gzipped CSS is small.
- No `__esModule` shims, no `'use client'` on package entrypoints — clean.
- `force-dynamic` on every page is **defensible for an admin tool** (always-fresh data, no SEO concern, ~100 users), but caching the heavy aggregations would still help TTFB.
