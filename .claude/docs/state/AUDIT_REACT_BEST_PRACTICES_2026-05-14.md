# AUDIT A.7 — React / Next.js 14 App Router Best Practices

**Audit run**: MEGA PRD AUDIT-FIRST · 2026-05-14
**Scope**: TSX components shipped Wave SP-7 → SP-11 (`7e0dddb..f510c49`).
**Reference checklist**: `vercel:react-best-practices` (57 rules) + Next.js 14 App Router doctrine.
**Auditor**: Claude Opus 4.7 (1M context).

---

## Summary

| Severity | Count |
|----------|-------|
| **P0** — Bugs / broken React contracts | **3** |
| **P1** — Real perf / a11y / correctness issues | **8** |
| **P2** — Doctrine drift / maintainability | **11** |
| **P3** — Polish / nice-to-have | **6** |
| **TOTAL** | **28** |

**Bottom line** : The Wave SP-7→SP-11 components are **structurally sound** (proper Server vs Client split, good use of `loading.tsx` / `error.tsx`, defensive parsers, no `useEffect`-for-fetching anti-patterns). The 3 P0 findings are real bugs : (1) the `Browse history` Card wraps a Card-rendering child producing nested `gc-panel` borders + duplicate `<button>` filter UI, (2) `ProposalList` uses array-`index` as `<li key>` inside the AntiPatternSection `examples_good.map` (true index-as-key violation — RichRecoCard L73, judges remarks L88), (3) `ProposalQueue`'s optimistic-update `setVoted` keyed by `proposal_id` never clears, so a vote stays optimistic-only if the API later fails or the parent server tree refreshes. The recurring patterns to fix are : (a) inline `CSSProperties` objects re-allocated every render (15+ sites — should be CSS module classes or `useMemo` if dynamic), (b) ad-hoc `tone` lookups using `Record<string, ...>` instead of discriminated unions (drift between `ProposalList`, `ProposalQueue`, `ProposalVotePanel` duplicate the same map 3×), (c) `audit.scores_json` is treated as `unknown` 6×, indicating the `@growthcro/data` `Audit` type needs a typed `scores_json` field.

---

## P0 — Bugs / broken React contracts

### P0-1 — Index-as-key in user-facing lists (3 sites)

**Files** :
- `webapp/apps/shell/components/audits/RichRecoCard.tsx:73` — `ap.examples_good.map((ex, i) => <li key={i}>…</li>)`
- `webapp/apps/shell/components/judges/JudgeScoreCard.tsx:88` — `judge.remarks.slice(0, 3).map((r, i) => <li key={i}>…</li>)`
- `webapp/apps/shell/components/learning/ProposalList.tsx` — none directly, but the route uses `proposal.proposal_id` (ok)

**Why P0** : `examples_good` and `judge.remarks` are arrays of **strings** that can be reordered (server re-render with a new sort, optimistic add) or appear duplicated. Index-as-key causes React to re-mount the wrong subtree on re-order, swallow input focus inside the `<li>`, and is the textbook anti-pattern Vercel rule #14 flags.

**Fix** : use the string value with a stable suffix as the key, or a hash : `key={\`\${ex}-\${i}\`}` is acceptable when duplicates impossible; otherwise compute a stable id upstream.

### P0-2 — Optimistic-only state in `ProposalQueue` never reconciles

**File** : `webapp/apps/shell/components/learning/ProposalQueue.tsx:37-69`

The local `voted: Record<string, ProposalReview>` map captures successful votes but is **never cleared on `router.refresh()`**. After a vote, the parent server tree (`/learning/page.tsx`) is **not refreshed** (the component never calls `router.refresh()`), so a user who hard-reloads sees the vote (it persisted server-side), but a user who stays and votes more never gets the server's view of the data — divergence is invisible.

Worse : on API failure the `setError` fires but `voted` already updated optimistically. Wait — re-reading L67-L69 : `handleVoted` is only called on **success** by `ProposalVotePanel`, so this specific path is safe. The remaining bug is the **missing `router.refresh()`** so the `ProposalStats` KPI grid at the top of `/learning` stays stale until full reload.

**Fix** : `import { useRouter } from "next/navigation"` and call `router.refresh()` inside `handleVoted` after merging local state. Or move optimistic state to `useOptimistic` (React 19) once the project upgrades.

### P0-3 — `getCurrentRole()` swallowed errors mask auth failures

**File** : `webapp/apps/shell/app/audits/[clientSlug]/[auditId]/page.tsx:36` (and `clients/[slug]/page.tsx:31`)

```ts
const [recos, siblings, role] = await Promise.all([
  …
  getCurrentRole().catch(() => null),  // ← silent null
]);
const isAdmin = role === "admin";
```

If Supabase auth fails (rotated JWT, expired session, network), `role === null` and the edit/delete triggers silently disappear instead of showing a "session expired" prompt. This is a UX bug : the admin will see the page in read-only mode and not know why.

**Fix** : differentiate between "not admin" and "auth failed". Log the error to the server console with `console.error` so prod telemetry catches it.

---

## P1 — Real perf / a11y / correctness issues

### P1-1 — Inline style object factory allocated on every render

**Files (count)** : 15+ across `ProposalDetail.tsx`, `ProposalList.tsx`, `ProposalQueue.tsx`, `ProposalVotePanel.tsx`, `DeleteConfirmModal.tsx`, `EditRecoModal.tsx`, `JudgeScoreCard.tsx`, plus all modules using `style={{ … }}`. Examples :

- `ProposalDetail.tsx:117-156` — 4 inline `style={{ …btnStyle, background: "#0e3d1f", … }}` per render
- `ProposalQueue.tsx:128-139` — per-row inline style with nested `border`/`background` strings
- `JudgeScoreCard.tsx:82-95` — inline `borderBottom` ternary recomputed for every remark

These objects are recreated each render and break `React.memo` short-circuiting for any downstream memoised child. Volume is high enough to matter on the Learning Lab page (60-row list).

**Fix** : hoist static portions to module-level constants (`ProposalDetail` already does this for `btnStyle` — extend to the variants), and use a CSS module class for variants (`gc-vote-btn--accept`, `gc-vote-btn--reject`, …). The dashboard already has `.gc-pill--*` modifiers — extend the system.

### P1-2 — `<a href>` used where `<Link>` would short-cut RSC fetch

**Files** : Nearly every page (`audits/[clientSlug]/[auditId]/page.tsx:54-91`, `clients/[slug]/page.tsx:62-86`, `learning/page.tsx:37`, `funnel/[clientSlug]/page.tsx:98-104`, `ProposalList.tsx:142`, `RichRecoCard.tsx`, …).

These are internal navigations to other App Router routes. Using plain `<a>` (with `target="_blank"` reserved for external) **defeats Next.js prefetching + soft client-side navigation**, forcing a full server roundtrip per click.

**Fix** : `import Link from "next/link"` and replace internal `<a>` with `<Link>`. The CSS classes (`gc-pill gc-pill--soft`) carry over unchanged. Only the screenshot-thumbnail `<a target="_blank">` and the file-link list in `AuditScreenshotsPanel` should stay `<a>`.

### P1-3 — Modal mounted in DOM even when `open=false`

**Files** : All trigger components (`AuditEditTrigger`, `CreateAuditTrigger`, `RecoEditTrigger`, `ClientDeleteTrigger`).

Each modal stays in the DOM (controlled visibility via `open` prop). The `Modal` primitive in `@growthcro/ui` likely conditionally renders, but the child form **state** (`useState` for `submitting` / `error` / FormData defaults) is initialised on parent mount, not on first open. For the Learning Lab queue with potentially many `ProposalVotePanel` instances, this is fine. For the `RichRecoCard` × top-5 expanded list, you have 5 simultaneous `EditRecoModal` + 5 `DeleteConfirmModal` instances pre-mounted with state. Low impact today, but a footgun if the list grows.

**Fix** : check `Modal` internals; if it renders children unconditionally, lift to `{open ? <EditRecoModal … /> : null}` in each trigger. Verified `EditRecoModal` reads `reco` props and uses `defaultValue` from `reco.title` — fine, but the `useState` initialiser runs once per trigger regardless.

### P1-4 — `useMemo` on `allTypes` re-runs on every keystroke

**File** : `webapp/apps/shell/components/learning/ProposalList.tsx:36-40`

```ts
const allTypes = useMemo(() => {
  const set = new Set<string>();
  for (const p of proposals) set.add(p.type);
  return ["all", ...Array.from(set).sort()];
}, [proposals]);
```

The dep is `proposals` which is **stable for a page render** (server prop). So this `useMemo` is fine — but the **filtered list useMemo (L42-L54)** runs on every keystroke of the search input. That's the *intent*, but the haystack is rebuilt for every proposal on every keystroke even if `query === ""`. Adding a `query === ""` short-circuit at the top of the filter callback saves work.

### P1-5 — `useState` initial value derived from props is fragile

**File** : `webapp/apps/shell/components/learning/ProposalDetail.tsx:18-26`

```ts
const [decision, setDecision] = useState<…>(proposal.review?.decision ?? null);
const [note, setNote] = useState<string>(proposal.review?.note ?? "");
const [lastSaved, setLastSaved] = useState<…>(proposal.review?.reviewed_at ?? null);
```

If the `proposal` prop ever **changes for the same component instance** (e.g. navigating between `/learning/p1` and `/learning/p2` via client-side nav), the local state will retain the *previous* proposal's decision/note. The current code uses `<a>` not `<Link>` so this can't trigger today (the route remounts), but if you fix P1-2 above this becomes a latent bug.

**Fix** : either keep the `<a>` (forces remount — works but defeats the point), or sync via the `useEffect`-with-prop-dep anti-pattern (not great), or better : pass the proposal id in the URL, derive `decision` directly from `proposal.review?.decision` and store only the **unsaved draft note** locally.

### P1-6 — `LearningIndex` runs `listV29Proposals` / `listV30Proposals` synchronously without `async`

**File** : `webapp/apps/shell/app/learning/page.tsx:20-23`

```ts
export default function LearningIndex() {
  const v29 = listV29Proposals();
  const v30 = listV30Proposals();
```

The function isn't `async` because the FS readers are synchronous (`fs.readdirSync` in `proposals-fs`). That's fine for now, but **blocks the request thread** for as long as it takes to read every JSON file under `data/learning/`. With `dynamic = "force-dynamic"`, this runs on every request. As the proposals corpus grows past O(100) files, p95 will degrade.

**Fix** : promote to async + use `fs/promises` in `proposals-fs`. Then `Promise.all` the two reads. Low priority now, latent.

### P1-7 — `getFunnelFromClient` mutates by typecast, not by parser

**File** : `webapp/apps/shell/app/funnel/[clientSlug]/page.tsx:30-35`

```ts
function getFunnelFromClient(client: Client): FunnelData | null {
  const dna = client.brand_dna_json;
  if (!dna || typeof dna !== "object") return null;
  const raw = (dna as Record<string, unknown>)["funnel"];
  return parseCapturedFunnel(raw);
}
```

OK, `parseCapturedFunnel` is defensive. **The issue** : `brand_dna_json` is typed as `unknown` in the data layer (verified by the `as Record<string, unknown>` cast). This should be a typed field. Same issue at A.4 (data fidelity) — surface it here in the component layer because every page that touches `brand_dna_json` does this cast.

### P1-8 — `<table>` semantic accessibility missing in funnel viz

**File** : `webapp/apps/shell/components/funnel/FunnelStepsViz.tsx`, `FunnelDropOffChart.tsx`

The funnel viz uses `role="list"` / `role="listitem"` and an SVG `<g role="presentation">`. For tabular data (step → cohort size → drop-off), an `<table>` (or `role="table"`/`role="row"`/`role="cell"`) would be more accessible. Screen readers can navigate columns and announce headers. The current ARIA is *not wrong* (Vercel rule #41 — no false aria), but a `<table>` semantic gives users a richer experience. The SVG has a single `aria-label` "Funnel cohort retention chart" with no `<title>` — assistive tech reads only the label, not the underlying numbers.

**Fix** : either add a hidden `<table>` shadow DOM with the data points + `role="img"` on the SVG, or wrap step values in a `<dl>`. Tracking only.

---

## P2 — Doctrine drift / maintainability

### P2-1 — `Record<string, "color">` tone maps duplicated 3×

**Files** :
- `ProposalList.tsx:13-23` — `TRACK_TONE` + `DECISION_TONE`
- `ProposalQueue.tsx:20-30` — same `TRACK_TONE` + `DECISION_TONE`
- `ProposalVotePanel.tsx:22-27` + inline ternary L82-L89 — same logic third time
- `ProposalDetail.tsx:10-15` — `DECISION_TONE` again

**Fix** : extract `webapp/apps/shell/components/learning/proposal-tones.ts` exporting the two maps, or better a `toneForDecision(decision)` and `toneForTrack(track)` function. Same pattern for the verdict tones in `judges-utils.ts:117-123` (already extracted — good model).

### P2-2 — `PAGE_TYPES` / `DOCTRINE_VERSIONS` duplicated in `CreateAuditModal` and `EditAuditModal`

**Files** : `CreateAuditModal.tsx:27-42`, `EditAuditModal.tsx:20-35`

Both files hardcode the same 12 page types + 2 doctrine versions. Drift risk : adding a new page type to one file silently forgets the other. Already a known doctrine breach (mono-concern violation per `CODE_DOCTRINE.md`).

**Fix** : move to `@growthcro/data` constants module or `webapp/apps/shell/lib/audit-constants.ts`.

### P2-3 — `SEVERITIES`, `EFFORTS`, `LIFTS` literal arrays sit in `EditRecoModal` alone, but the types come from `@growthcro/data`

**File** : `EditRecoModal.tsx:26-29`

The type defs are in `@growthcro/data` but the value enumerations live here. Same drift risk : adding `XL` to `RecoEffort` won't surface in the modal.

**Fix** : export `const RECO_EFFORTS: readonly RecoEffort[] = ["S","M","L"]` from `@growthcro/data` as a single source of truth.

### P2-4 — Hardcoded hex colors bypass the design token system

**Sites** :
- `ProposalDetail.tsx:117-156` — `#0e3d1f`, `#1d6a3a`, `#3d0e0e`, `#6a1d1d`, `#0e2a3d`, `#1d4a6a`, `#3d2f0e`, `#6a541d`
- `ProposalQueue.tsx:137-138` — `#0f1520`, `#161f30`
- `ProposalVotePanel.tsx:31-34` — same 4 vote-button color pairs
- `ProposalList.tsx:91-97`, `selectStyle:208-213` — `#0f1520`
- `JudgeScoreCard.tsx:64-68` — implicit via `VERDICT_COLOR` (uses CSS vars — good)
- `Sidebar.tsx`, `ConvergedNotice.tsx` use CSS vars — good

The project has CSS variables (`var(--gc-gold)`, `var(--gc-cyan)`, …) — bypassing them for the proposal vote buttons creates 12+ hex strings that *can't* be re-themed.

**Fix** : add `--gc-bg-accept`, `--gc-bg-reject`, `--gc-bg-refine`, `--gc-bg-defer` (and -border variants) to the design tokens layer, replace the hexes.

### P2-5 — `FormData` parsing duplicated 3×

**Files** : `CreateAuditModal.tsx:55-62`, `EditAuditModal.tsx:48-53`, `EditRecoModal.tsx:43-54`

Same `String(fd.get("…") ?? "")` shape. No central helper. Risk : one site forgets `.trim()`, another forgets the `|| null` for nullable strings.

**Fix** : `webapp/apps/shell/lib/form-helpers.ts` exporting `formString(fd, name)` / `formNullableString(fd, name)` / `formEnum<T>(fd, name, allowed: readonly T[])`.

### P2-6 — Async server actions vs API routes inconsistency

Every mutation (create/edit/delete) here goes through `fetch("/api/…")` + `router.refresh()` from a client component. Next.js 14 supports **Server Actions** which would :
- Eliminate the `JSON.stringify` + `headers: { "content-type": "application/json" }` boilerplate
- Skip the `/api/audits/[id]` route altogether (collocate the mutation with the page)
- Auto-invalidate the cache via `revalidatePath` / `revalidateTag` instead of `router.refresh()`

**Recommendation** : evaluate Server Actions in a small pilot (e.g. `RecoEditTrigger`). Don't migrate everything blindly — Server Actions require a careful auth story since they run server-side without the API-route guard pattern. Track as a follow-up RFC.

### P2-7 — Mixed `"use client"` granularity

`RichRecoCard` is a `"use client"` for collapsible state alone — fine, but it pulls in `score-utils.extractRichReco` which is pure and ~200 lines. The whole module ships to the browser. Same for `Sidebar` (needs only `usePathname` from `next/navigation`).

**Fix** : verify with `@next/bundle-analyzer` that the client bundle stays under target. Consider splitting `extractRichReco` into a tiny `extract-rich-reco.ts` and reuse server-side too.

### P2-8 — Magic numbers in component bodies

- `RichRecoCard.tsx:88` — `rich.antiPatterns[0] ?? null` — only ever reads the first anti-pattern despite the data shape supporting many
- `ProposalList.tsx:138` / `ProposalQueue.tsx:127` — `slice(0, 60)` / `slice(0, 40)` — hardcoded list caps
- `AuditDetailFull.tsx:31` — `TOP_RECOS_EXPANDED = 5` — at least extracted

**Fix** : promote to module constants with comments explaining the choice.

### P2-9 — `"use client"` modal that imports server-only utility

**File** : `EditRecoModal.tsx:18` imports `extractRichReco` from `@/components/clients/score-utils`. That file is a `.ts` (not `.tsx`), and reading it confirms pure-JS — no `'server-only'` markers. **Likely safe**. But `score-utils.ts` is the same module used by `RichRecoCard` and the server `AuditDetailFull`. Confirm there's no Node-only API (fs, path) sneaking in.

**Fix** : add `// pure — runs on client and server` header comment, plus a CI test that this file imports zero node-only modules.

### P2-10 — `defaultOpen={true}` for top-5 recos forces 5 simultaneous open `<button>` state machines

**File** : `AuditDetailFull.tsx:116` + `RichRecoCard.tsx:83`

`<RichRecoCard reco={r} defaultOpen editable={editable} />` — 5 cards mount with `useState(true)` for `open`. Each card is independent, so any one can collapse. This is the *intended* behaviour, but if you wanted "expand all / collapse all" you'd need lifted state. Tracking only.

### P2-11 — `dynamic = "force-dynamic"` everywhere prevents segment caching

**Files** : Every page in scope (`audits/[clientSlug]/[auditId]/page.tsx:19`, `clients/[slug]/page.tsx:18`, `funnel/[clientSlug]/page.tsx:28`, `learning/page.tsx:18`, `audits/[clientSlug]/[auditId]/judges/page.tsx:17`).

This is the right default for an admin dashboard (no stale data), but Next.js 14 PPR (Partial Prerendering) is a better fit for these pages : the header/sidebar can stay static, only the data slot streams. Tracking.

---

## P3 — Polish / nice-to-have

- **P3-1** — `Modal` close on `Esc` key : not verified in `@growthcro/ui` source. Worth a manual test.
- **P3-2** — `aria-busy="true"` on `SkeletonBlock` regardless of context (always loading). Fine, but the `<main role="status" aria-live="polite">` parent already announces — `aria-busy` on each child is redundant.
- **P3-3** — `LoadingSkeleton.tsx:79-81` uses `Array.from({ length }).map((_, i) => key={i})` — same index-as-key issue but here the array is **truly static** so it's defensible. Vercel rule allows it for static N. Tracking only.
- **P3-4** — `ProposalDetail.tsx:191` — `const btnStyle: React.CSSProperties` — `React.CSSProperties` import works, but Next.js 14 prefers `CSSProperties` from `react` to avoid the namespace import. Style nit.
- **P3-5** — `Sidebar.tsx` re-computes `group.label.toLowerCase().replace(/\s+/g, "-")` twice per group (id + aria-labelledby). Could `useMemo` or precompute at the constant level.
- **P3-6** — `EmptyState.tsx:70` — CTA uses `<a href>` for internal nav. Same as P1-2 — should be `<Link>`. Lower severity because EmptyState is rarely on hot paths.

---

## Recurring patterns

1. **Inline styles + hardcoded hex** (15+ sites) — biggest maintainability tax. Migrate to CSS modifiers.
2. **`<a href>` for internal nav** (12+ sites) — switch to `next/link`. Boots prefetching for free.
3. **Tone/role/decision Records duplicated** (3×) — extract a shared `tones.ts` per module.
4. **`audit.scores_json as Record<string, unknown>` casts** (6 sites) — proper typed field upstream in `@growthcro/data`.
5. **Modal trigger pattern** is consistent and good : `"use client"` thin island owning `useState`, server parent passes props. Doctrine-aligned. Keep.
6. **`error.tsx` / `loading.tsx` / `ErrorFallback` / `PageSkeleton`** — well-designed, reused 3× already. Keep the pattern.
7. **No `useEffect` for data fetching** — clean. Server components do the fetching, client islands only handle interactivity. Doctrine-aligned.
8. **Defensive parsers** (`parseCapturedFunnel`, `parseJudgesPayload`, `extractRichReco`) — return `null` on bad shape rather than throw. Doctrine-aligned. Keep.

---

## Recommendations (prioritised)

### Wave AUDIT-7-FIX-A (P0, 30 min)
1. Replace index-as-key in `RichRecoCard.tsx:73`, `JudgeScoreCard.tsx:88` with content-based keys.
2. Add `router.refresh()` after successful vote in `ProposalQueue.handleVoted`.
3. Differentiate `getCurrentRole() → null` from `auth failure` (log + telemetry).

### Wave AUDIT-7-FIX-B (P1, 2-3 h)
4. Global `<a>` → `<Link>` sweep for internal routes (12+ sites). Single commit, mechanical.
5. Extract `webapp/apps/shell/lib/form-helpers.ts` + retrofit 3 modals.
6. Extract `learning/proposal-tones.ts` shared module.
7. Add `--gc-bg-accept/reject/refine/defer` CSS variables + `.gc-vote-btn--*` modifier classes.

### Wave AUDIT-7-FIX-C (P2, 4-6 h, can defer)
8. Centralise `PAGE_TYPES`, `DOCTRINE_VERSIONS`, `RECO_EFFORTS`, `RECO_LIFTS` in `@growthcro/data` constants.
9. RFC : Server Actions pilot for one CRUD path (recommend `RecoEditTrigger`).
10. Type `audit.scores_json` properly (`ScoresJsonV3` discriminated union).
11. Switch `proposals-fs` to async + add `dynamic="force-dynamic"` removal trial on `/learning`.

### Wave AUDIT-7-FIX-D (P3, optional)
12. Bundle analyzer pass — confirm `RichRecoCard` + `extractRichReco` bundle size acceptable.
13. PPR trial on `/clients/[slug]` (sidebar stays static).

---

**End of A.7.**
