# Audit A.12 — Mobile Responsive (static) — 2026-05-14

## TL;DR

GrowthCRO webapp shell has a **partial mobile foundation** (V26 already shipped 1180px/640px/720px CSS media queries on most layout classes) but ships with **NO explicit `<meta viewport>` nor Next.js `viewport` export** — relying on Next 13.4+ implicit default. Multiple components silently break the mobile fallback via **inline `style={{ gridTemplateColumns: ... }}` overrides** that bypass `@media` queries. Net verdict: **partially mobile-ready (~60%)**; usable at 768px tablet, broken-or-degraded at 360px mobile. **5 P0 bugs**, **10 P1 issues**, **8 P2 polish items**. Worst offenders: `UsageTab.tsx:24`, `ProposalList.tsx:80`, `AuditsTabPanel.tsx:28`.

## Viewport config

- **meta viewport**: NOT declared in `app/layout.tsx` (lines 1-28). No `<meta name="viewport">` anywhere in the tree.
- **Next.js `generateViewport` export**: NOT defined. `grep -rn "viewport:" webapp/apps/shell` (excluding `.next/`) returns 0 hits.
- **`next.config.js`**: bare config, no viewport setting.
- **Implicit default**: Next.js 14 falls back to `<meta name="viewport" content="width=device-width">` automatically since 13.4. Pixels render at native ratio. However, **best practice mandates explicit declaration** (Next.js documentation, WCAG 1.4.10 Reflow).
- **Severity**: **P1** — works in modern browsers but fragile, no `initial-scale`, no `maximum-scale=5` for a11y.

## Per-component mobile audit

| Component | Breakpoint usage | Issue at 360px | Issue at 768px | Severity |
|---|---|---|---|---|
| `app/layout.tsx` | None — no viewport | Implicit Next default only; no explicit meta | Same | P1 |
| `app/globals.css` | `@media 1180/640/480` on `.gc-app`, `.gc-grid-kpi`, `.gc-main`, `.gc-topbar` | OK base CSS shrinks | OK | — |
| `Sidebar.tsx` | None (component) — relies on `.gc-side` CSS | At <1180px sidebar collapses to top via CSS `grid-template-columns: 1fr` — but `position: sticky` becomes `relative` and `height: auto`, takes ~340px vertical above content (long item list). No hamburger / drawer. | Sidebar takes full row, content below | **P0** |
| `CommandCenterTopbar.tsx` | None — relies on `.gc-topbar` flex | At <640px CSS turns flex → block (good); 2 actions render below title (OK) | OK | P2 |
| `AuditDetailFull.tsx` | Uses `.gc-audit-detail__grid` (responsive at 980px) | Grid stacks to 1fr (good). Reco cards (RichRecoCard) inherit responsive `.gc-rich-reco__sections` (720px breakpoint to 1fr) | Stacks at 980px | P2 |
| `AuditScreenshotsPanel.tsx` | `.gc-audit-screens__grid` `@media 720px → 1fr` | Stacks to 1 col (OK). Thumbnails `max-height: 280px object-fit: cover` — readable | OK | — |
| `RichRecoCard.tsx` | `.gc-rich-reco__sections` `@media 720px → 1fr` | "Pourquoi"/"Comment" stack (good). Header has buttons that wrap via `flex-wrap: wrap` (OK) | OK | P2 |
| `CreateAuditModal.tsx` | `width="560px"` hardcoded prop to `<Modal>` | **Modal forces 560px wide**, viewport is 360px → modal overflows horizontally inside backdrop (backdrop has `padding: 16px` so capped at ~328px visible). Form fields get cut. | OK at 768px | **P0** |
| `EditAuditModal.tsx` | `width="540px"` hardcoded | Same overflow issue | OK | **P0** |
| `EditRecoModal.tsx` | `width="640px"` hardcoded | Worse — 640px vs 360px viewport | OK | **P0** |
| `DeleteConfirmModal.tsx` | `width="460px"` | Overflow at 360px (less severe but still breaks) | OK | P1 |
| `FunnelDropOffChart.tsx` | SVG `viewBox` + `style={{ width: 100%, height: auto }}` | Scales correctly. **BUT** `PADDING_X=110` for labels → label area dominates at small widths, bars become tiny | Acceptable | P1 |
| `FunnelStepsViz.tsx` | `.gc-funnel-steps` `@media 720px → 1fr` | Stacks to 1 column — readable, vertical scroll | OK | — |
| `JudgesConsensusPanel.tsx` | `.gc-grid-kpi` (responsive) + `.gc-doctrine-grid` (`auto-fill minmax(220px,1fr)`) | KPI grid 1fr at 640px (good). Doctrine grid auto-stacks (good) | OK | P2 |
| `JudgeScoreCard.tsx` | None — pure render in `.gc-doctrine-bloc` | Single column at small widths (good). 3-pill verdict header uses flex-justify-between → may compress badly with long verdicts | OK | P2 |
| `ProposalDetail.tsx` | `display: flex; gap: 8` row of 4 buttons (Accept/Reject/Refine/Defer) line 112-157 | **4 buttons + 16px padding each** ≈ 4×100px = 400px → overflows 360px viewport, no `flex-wrap`. Decision panel unusable. | Marginal at 768px | **P0** |
| `ProposalList.tsx` | Inline `gridTemplateColumns: "1fr auto auto auto"` line 80-85 | **4-column grid forced** → input + 3 selects don't fit at 360px (need ~480px min). Filter row breaks. | Cramped | **P0** |
| `ProposalQueue.tsx` | Inline `gridTemplateColumns: "1fr auto auto"` line 82-88 | 3 cols on 360px → narrow input + 2 selects, may overlap or overflow | Marginal | P1 |
| `ProposalStats.tsx` | `.gc-grid-kpi` (responsive) | OK — stacks at 640px | OK | — |
| `ProposalVotePanel.tsx` | `display: flex; flex-wrap: wrap` line 122-127 | Wraps 5 buttons → multi-line acceptable | OK | P2 |
| `Breadcrumbs.tsx` | `.gc-breadcrumbs__list` has `flex-wrap: wrap` | Wraps to multiple lines (good) — deep paths take 3+ rows | OK | P2 |
| `ViewToolbar.tsx` | Uses `.gc-topbar` (responsive) + `.gc-toolbar` (`flex-wrap: wrap`) | OK | OK | — |
| `FleetPanel.tsx` (command-center) | `.gc-cc-filters` `@media 640px → 1fr` | Stacks to 1 col (good). `.gc-cc-client-list` `max-height: calc(100vh - 310px)` may be tiny at 360px (small screens have less vh) | OK | P2 |
| `ClientHeroDetail.tsx` | `.gc-cc-hero__actions` flex-wrap | 4 action buttons wrap. PillarRadialChart `size=220` SVG scales via viewBox (OK) | OK | P2 |
| `CommandCenterKpis.tsx` | `.gc-grid-kpi` (responsive @640px → 1fr) | OK | OK | — |
| `ClientList.tsx` | `.gc-clients-table__row` `@media 720px → 1fr` | OK — stacks rows vertically | OK | — |
| `AuditsTabPanel.tsx` | Inline `gridTemplateColumns: "minmax(0, 1.5fr) minmax(0, 1fr) 90px 110px"` line 28-31 | **Inline override forces 4-col grid** → page_url column gets squeezed to <100px at 360px, text truncated | Acceptable | **P0** |
| `HistoryTabPanel.tsx` | Uses `.gc-stack` + raw flex | Single column timeline (good) | OK | — |
| `BrandDNATabPanel.tsx` | `<pre>` with `overflow: auto` for JSON | OK — JSON scrolls horizontally if long | OK | P2 |
| `ClientDetailTabs.tsx` | `.gc-tabs` flex-wrap | 3 tabs wrap if needed (good) | OK | — |
| `ApiTab.tsx` | `.gc-settings__api-row` `@media 880px → column` | Stacks label + button vertically (good). `<code>` has `word-break: break-all max-width: 100%` (good) | OK | — |
| `UsageTab.tsx` | Inline `gridTemplateColumns: "repeat(4, minmax(0, 1fr))"` line 24 | **Inline override forces 4 KPIs in one row** → 360px / 4 = ~90px per KPI → KpiCard text wraps awfully, numbers may overflow | Cramped at 768px (4×190px = 760px just fits) | **P0** |
| `SettingsTabs.tsx` | `.gc-settings` `@media 880px → 1fr` | Tab bar becomes horizontal scroll (`overflow-x: auto`) — OK | OK | — |
| `RunsLiveFeed.tsx` | Inline `display: flex; justify-content: space-between` | Run name + status pill on one row — may compress if name long | OK | P2 |
| `PillarRadialChart.tsx` | SVG viewBox + `.gc-radial svg { max-width: 280px }` | Scales correctly | OK | — |
| `PillarsSummary.tsx` | `.gc-pillar-row` `@media 720px → 100px 1fr 56px` | OK shrinks at small widths | OK | — |
| `ConvergedNotice.tsx` | `.gc-converged-notice` text content | OK — wraps naturally | OK | — |
| `AuditQualityIndicator.tsx` | `.gc-audit-quality` `flex-wrap: wrap` | OK | OK | — |
| `Studio.tsx` (GSG) | `.gc-flow` `@media 640px → 1fr` + `.gc-gsg-grid` `@media 1180px → 1fr` | OK stacks | OK | — |
| `FunnelPage` route | Inline `style={{ padding: 22 }}` on `<main>` line 85 | **Bypasses `@media 480px → padding 12px`** → no padding reduction on small screens | Acceptable | P1 |
| `LearningPage` route | Inline `padding: 22` line 26 | Same bypass | OK | P1 |
| `JudgesPage` route | Inline `padding: 22` line 35 | Same | OK | P1 |
| `ProposalDetail` page | Inline `padding: 22` line 22 | Same | OK | P1 |

## P0 (broken on mobile)

1. **`UsageTab.tsx:24`** — `gridTemplateColumns: "repeat(4, minmax(0, 1fr))"` inline overrides responsive `.gc-grid-kpi`. At 360px each KPI gets ~75px → numbers/labels overflow, unreadable. **Fix**: remove inline style, let global CSS handle it.

2. **`ProposalList.tsx:80-85`** — `gridTemplateColumns: "1fr auto auto auto"` forces 4-col filter row → input + 3 dropdowns don't fit at 360px (min ~120px each = 480px required). **Fix**: wrap inline `style` with media query check or use `grid-template-columns: 1fr` + flex-wrap on mobile.

3. **`AuditsTabPanel.tsx:28-31`** — `gridTemplateColumns: "minmax(0, 1.5fr) minmax(0, 1fr) 90px 110px"` inline override on `.gc-clients-table__row` bypasses the 720px → 1fr media query. **Fix**: drop the inline override or wrap in a wider client-side mobile check.

4. **`CreateAuditModal.tsx:85` / `EditAuditModal.tsx:76` / `EditRecoModal.tsx:77`** — Modals hardcoded with `width="560px"`/`540px`/`640px`. Modal CSS default `width: min(640px, 100%)` works, but the inline `style={{ width }}` in `Modal.tsx:49` overrides → fixed pixel width overflows viewport at 360px. **Fix**: change Modal width prop to use `min(640px, 100%)` clamp, OR change all callers to pass nothing (default).

5. **`ProposalDetail.tsx:112-157`** — Row of 4 buttons (Accept/Reject/Refine/Defer) with `display: flex; gap: 8` and `padding: "8px 16px"` (~100px each) → 4 buttons = 400px width minimum, **NO flex-wrap**, overflows 360px viewport. Decision panel is broken on mobile. **Fix**: add `flexWrap: "wrap"` or stack to 2x2 grid.

## P1 (degraded UX on mobile)

1. **No explicit `<meta viewport>`** in `app/layout.tsx`. Relies on Next.js 14 implicit default. Best practice: add `export const viewport = { width: 'device-width', initialScale: 1, maximumScale: 5 }`.

2. **`Sidebar.tsx`** — at <1180px collapses inline above main content (~340px tall), no hamburger/drawer. User on 360px scrolls through 9 nav items before reaching page content.

3. **6 page routes** use inline `padding: 22` (`funnel`, `learning`, `learning/[proposalId]`, `reality`, `reality/[clientSlug]`, `audits/[c]/[a]/judges`) which bypasses the `@media 480px → padding: 12px` rule. Content gets squeezed against viewport edge.

4. **`ProposalQueue.tsx:82-88`** — `gridTemplateColumns: "1fr auto auto"` 3-col filter row marginal at 360px.

5. **`DeleteConfirmModal.tsx`** — `width="460px"` still overflows 360px viewport. Less severe than other modals (smaller content) but same root issue.

6. **`FunnelDropOffChart.tsx`** — SVG `PADDING_X=110` for left labels is too wide at narrow widths → bars become microscopic. Should scale label area down or stack vertically below 480px.

7. **Sticky elements**: `.gc-side` was `position: sticky` desktop, becomes `relative` mobile (good). But no equivalent fixed mobile drawer.

8. **Touch targets**: `.gc-btn { padding: 9px 12px; font-size: 13px }` → ~34px tall, below WCAG 2.5.5 AAA (44×44px) and 2.5.8 AA (24×24px barely met). Pills used as buttons (`<button className="gc-pill">`) at `padding: 3px 7px` = ~18px tall, well below recommended 24px floor.

9. **`Modal.tsx:49`** — `style={width ? { width } : undefined}` should clamp: `style={{ width: width ? `min(${width}, 100%)` : undefined }}`.

10. **Inline 4-column KPI overrides**: also applies to potentially `JudgesConsensusPanel.tsx` `.gc-grid-kpi` (uses default — OK) but the pattern is risky.

## P2 (improvement)

1. **Pills as buttons**: `<button className="gc-pill gc-pill--cyan">` (e.g. `RecoEditTrigger`, `ClientDeleteTrigger`, `CreateAuditTrigger`) have only 18-24px touch target. Promote to `.gc-btn` (34px) or new `.gc-btn--sm` (≥40px) for mobile.

2. **Long text overflow**: `<code>` elements in audit toolbars (e.g. page slugs, anon keys) lack `word-break: break-all` consistently. ApiTab has it (good); other locations don't.

3. **`Breadcrumbs.tsx`** — deep paths (4-5 segments) wrap to 2-3 rows at 360px, eating vertical real estate. Consider truncation with ellipsis after segment 3.

4. **`ProposalVotePanel.tsx`** — buttons compact mode has `padding: 5px 10px font-size: 11px` → ~22px tall, fails 24px AA floor. Switch to `gap: 8` and bigger padding.

5. **`PillarRadialChart`** — labels at fontSize=9 are below WCAG 1.4.12 readable text guidance on mobile. Consider 11px+ at mobile.

6. **`gc-cc-client-list`** — `max-height: calc(100vh - 310px)` is tight on landscape phones (vh=375px → 65px scrollable list). Bump to `calc(100vh - 250px)` mobile.

7. **`AuditDetailFull` Card actions** include "Export PDF" pill on same row as title — wraps OK but visually noisy on small screens.

8. **No mobile-specific CSS animations override** for `prefers-reduced-motion` checks already done — confirm the `.gc-rich-reco__fill` transition respects it.

## Charts responsiveness

- **PillarRadialChart**: SVG viewBox + `max-width: 280px` ceiling. Scales correctly. **Verdict OK**.
- **FunnelDropOffChart**: SVG viewBox + `width: 100%, height: auto`. Scales correctly. **BUT**: `PADDING_X=110` for label gutter eats too much horizontal at narrow viewports. **Verdict P1**: needs adaptive padding (or stack labels above bars on mobile).
- **FunnelStepsViz**: Pure CSS grid `.gc-funnel-steps` with `@media 720px → 1fr`. **Verdict OK**.
- **ScoreBar primitive**: from `@growthcro/ui`. Uses `.gc-bar` grid `110px 1fr 44px` at all widths. Could be tight at 360px (label column 110px = 30% of viewport). **Verdict P2**.

No Recharts/Chart.js dependency — all custom SVG, which sidesteps a major mobile pitfall (Recharts `ResponsiveContainer` needed). Good doctrine here.

## Modals responsiveness

- **`Modal.tsx`** base CSS: `width: min(640px, 100%)`. This DOES clamp. **GOOD.**
- **Problem**: when callers pass `width="560px"` (or any string), the inline `style={{ width }}` (`Modal.tsx:49`) **fully overrides** the CSS rule because of cascade specificity (inline style wins over class). At 360px viewport, modal renders 560px wide → either overflows or breaks into horizontal scroll inside the backdrop.
- **Backdrop**: `.gc-modal-backdrop { padding: 16px }` so modal max-visible = 328px on 360px viewport — modal IS visually clipped or scrolls.
- **Modals affected**: `CreateAuditModal` (560px), `EditAuditModal` (540px), `EditRecoModal` (640px), `DeleteConfirmModal` (460px).
- **Fix recommendation**: Modal.tsx line 49 should be:
  ```ts
  style={width ? { width: `min(${width}, calc(100vw - 32px))` } : undefined}
  ```

## Tables responsiveness

- **`ClientList.tsx`** uses `.gc-clients-table__row` with `@media 720px → grid-template-columns: 1fr` (stacks). **GOOD.**
- **`AuditsTabPanel.tsx`** inline `gridTemplateColumns` override breaks this → **P0**.
- No `<table>` elements in scope — all tabular data is grid-based, which avoids horizontal overflow if responsive media queries are respected.

## Forms responsiveness

- **`FormRow` primitive** (assumed `@growthcro/ui`) — not inspected but inputs all use `gc-form-row__input` which the docs show as `width: 100%`. OK.
- **`EditRecoModal.tsx:103-108`** uses `gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))"` — **correctly responsive**, will wrap to 1-col at 360px (140px min + gap doesn't fit, auto-fit collapses). 
- **`gc-filters`** (audits) has `grid-template-columns: 1fr 1fr` — 2-col search + select. At 360px → 2×144px = 288px + gap, fits. **OK.**
- **Native `<select>` / `<input type=number>`** open OS-native pickers, work well on mobile.

## Touch targets

- **`.gc-btn`**: 34px tall. Below WCAG 2.5.5 AAA (44×44) but at WCAG 2.5.8 AA (24×24). Acceptable but not great.
- **`.gc-pill` used as button**: 18-22px tall. **Below WCAG 2.5.8 AA (24×24)** — P2 issue across many components.
- **`.gc-modal__close`**: 28×28px. Marginal.
- **`.gc-page-strip button`**: `padding: 8px 10px font-size: 12px` ≈ 32px. Acceptable AA.
- **`.gc-tabs button`**: `padding: 9px 12px font-size: 13px` ≈ 34px. AA.
- **Inline buttons in `ProposalDetail`**: `padding: 8px 16px font-size: 14px` ≈ 35px. AA.
- **`ProposalVotePanel` compact**: 22px. **Below AA**.

## Sticky elements

- **`.gc-side`**: sticky desktop, relative mobile (via @1180px). **OK**.
- No header/topbar is sticky — pages scroll naturally. **OK**.
- **`.gc-modal-backdrop`**: `position: fixed; inset: 0` with `padding: 16px`. Good — content scrolls inside, backdrop full coverage.

## Images responsiveness

- **`AuditScreenshotsPanel.tsx`**: `<img loading="lazy" src={src}>` inherits `.gc-audit-screens__thumb img { width: 100%; height: auto; max-height: 280px; object-fit: cover; object-position: top center }`. **Excellent** — responsive + bounded + lazy. **OK**.

## Recommendations Wave C priority

1. **Add explicit viewport export** in `app/layout.tsx` (P1, 5 LOC):
   ```ts
   export const viewport: Viewport = {
     width: 'device-width',
     initialScale: 1,
     maximumScale: 5, // a11y — allow user zoom
   };
   ```

2. **Patch Modal to clamp width** (`packages/ui/src/components/Modal.tsx:49`) — clamp inline width prop to `min(${width}, calc(100vw - 32px))`. Fixes all 4 modal P0 bugs at once.

3. **Strip inline `gridTemplateColumns` overrides** that bypass responsive CSS:
   - `UsageTab.tsx:24` — remove `style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}`
   - `ProposalList.tsx:80-85` — wrap with min-width media query or use FiltersBar
   - `ProposalQueue.tsx:82-88` — same
   - `AuditsTabPanel.tsx:28-31` — drop inline grid style
   - Audit ALL inline `gridTemplateColumns` in components (scan for `gridTemplateColumns:` regex)

4. **Fix `ProposalDetail` button row** — add `flexWrap: "wrap"` to the 4-button bar OR rebuild as `display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr))`.

5. **Convert page-level inline padding** (`<main style={{ padding: 22 }}>`) to a class `.gc-page-shell` that includes the responsive `@media 480px` reduction. Apply to all 6 affected pages (`funnel`, `learning`×2, `reality`×2, `judges`).

6. **Add mobile drawer for Sidebar** — currently the sidebar collapses inline above main content, eating 300px+ vertical. Implement a hamburger toggle in `gc-topbar` for `< 768px` viewports. Sidebar becomes `position: fixed; transform: translateX(-100%)` with overlay backdrop.

7. **Promote `.gc-pill` to `.gc-btn--sm`** when used as a clickable button (currently `<button className="gc-pill ...">` is common). New class with `min-height: 40px; padding: 8px 12px` would lift touch targets to AA+.

8. **FunnelDropOffChart**: at viewports < 480px, drop the left label gutter and render labels above each bar (CSS sibling element) instead of inside SVG. Reduces effective `PADDING_X` from 110 → 0.

9. **Add `prefers-reduced-motion` checks** to modal entrance animation (`@keyframes gc-modal-in`) — currently animates regardless of OS preference.

10. **Documentation note**: All new components MUST avoid inline `style={{ gridTemplateColumns }}` — use CSS classes or `auto-fit minmax()` patterns only.
