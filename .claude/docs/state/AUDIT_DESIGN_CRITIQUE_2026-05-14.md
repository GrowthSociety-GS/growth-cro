# Audit A.5 — Design Critique (5 routes) — 2026-05-14

> **Method note**: the brief mentioned Tailwind, but the webapp ships zero Tailwind config. The actual design system is a hand-rolled CSS one — CSS custom properties in `webapp/packages/ui/src/styles.css` + `webapp/packages/ui/src/tokens.ts` + page-level styles in `apps/shell/app/globals.css`, surfaced via `gc-*` utility classes. The critique below evaluates THAT system. Pure static review, no live browser, no axe-core, no LH visuals.

## TL;DR

The webapp lands in a coherent "consultant noir + gold" palette and the macro information architecture (sidebar/topbar/card grid) is competent — it does not look like the typical bootstrap dashboard. But on close inspection it is undeniably a **generic dark-mode SaaS** with strong design debt: 339 inline style usages, two parallel button systems (`.gc-btn` vs `.gc-pill`), no actual font loaded (Inter referenced but not preconnected/`next/font`-injected), and zero motion design beyond two trivial keyframes. Premium ambition is signaled (gold accent, grain overlay, drop-shadow on panels), but the execution stays on the safe side of "Linear-ish dashboard" and never reaches Aesop/Stripe-grade typography or composition.

**Premium-meter average: 5.2 / 10** — capable, internally consistent, but not yet avant-garde.

---

## Per-route findings

### `/` (Home — Command Center)

Files reviewed: `apps/shell/app/page.tsx`, `components/command-center/CommandCenterTopbar.tsx`, `CommandCenterKpis.tsx`, `FleetPanel.tsx`, `ClientHeroDetail.tsx`, `app/globals.css` (lines 112–195, 1355–1435).

- **Hierarchy**: Single H1 ("Command Center", 28px/850) → 5 KPI cards (25px bold numbers + 12px labels) → 2-col layout (Fleet `0.8fr` + Hero `1.2fr`). H2 inside `.gc-panel-head` is 15px — the H1/H2 jump is **28→15 (~1.87x ratio)**, which is too wide; H2 should be ~18–20px for proper Major Third / Perfect Fourth scale. KPI value/label ratio is fine (25/12 ≈ 2x).
- **Spacing**: Consistent on the macro grid (`gap-14`, `padding 22`) — but inside hero panels there is mixed `marginTop: 16` inline (page.tsx:105), `marginTop: 8` (ClientHeroDetail:41), `marginTop: 6` (CommandCenterTopbar implicit). No 4/8/12/16 scale enforcement.
- **Color**: KPI cards use the same `--gc-panel` / `--gc-line` as every other surface — no visual emphasis difference between "Fleet (35)" and "P0 recos (12)". A P0 KPI should glow red-tinted or carry an accent border; here it's flat.
- **States**: The CC input has a proper `:focus` outline (gold, 2px). Client rows have hover/active border-color swap. But the error case is rendered as a raw `<p style={{ color: "var(--gc-muted)" }}>` (page.tsx:104-108) — error treated as throwaway grey text, not a proper `<ErrorBanner>` with icon + tone.
- **Issues**:
  - **P0** `apps/shell/app/page.tsx:105` — error state is muted grey, blends into chrome. Should be `--gc-amber` with icon.
  - **P1** `components/command-center/CommandCenterTopbar.tsx:18` — "Open V26 archive" CTA in topbar links to a *legacy artifact*. This is dev-only debris on a "production" landing.
  - **P1** `components/command-center/ClientHeroDetail.tsx:38-43` — inline-styled `<p>` blocks. Empty state copy is in English ("Select a client...") then French — language inconsistency on the same view.
  - **P2** No KPI accent: all 5 cards visually identical, no scannability.
- **Premium-meter**: **5/10** — competent, but feels like a Linear knock-off without Linear's typography polish.

---

### `/clients`

Files reviewed: `apps/shell/app/clients/page.tsx`, `components/clients/ClientList.tsx`, `components/common/FiltersBar.tsx`, `components/common/SortDropdown.tsx`, `components/common/Pagination.tsx`, `globals.css` (lines 671–815).

- **Hierarchy**: H1 (28px) + subtitle + 5 KPIs + Card("Portefeuille · N") + filters + list + pagination. The 5 KPIs (lines 150-164) are dimensionally identical to home's, so the page reads as "same shell, different data" — that consistency is good. But the H1/H2 ratio repeats the 28→15 problem.
- **Spacing**: Filters bar is `gc-filters-row` (grid `1fr auto`) — clean. Client row is a 4-col grid (`1.4fr 1fr 70px 1fr`) — column widths are eye-balled, not tied to a scale. There's a `<div style={{ marginTop: 12 }}>` wrapping `<ClientList>` (page.tsx:175) — magic number, not a class.
- **Color**: Score column (`.gc-clients-table__score`) is hard-coded `var(--gc-gold)` regardless of value — a client at 45% reads identical to a client at 92%. Should map score → green/amber/red.
- **States**: Row hover swaps border-color to cyan — fine. But the row is a `<Link>` containing nested `<Pill>` components (ClientList.tsx:24-44) — clickable area is the whole row, but the inner Pills look interactive too (cyan border) and aren't. Affordance is muddled.
- **Issues**:
  - **P0** `components/clients/ClientList.tsx:36-39` — Score color is constant gold; this kills the "fleet at a glance" job-to-be-done. A red score 30% should scream red.
  - **P1** `components/common/FiltersBar.tsx:64` — Reset button styled as `.gc-pill .gc-pill--soft` (a pill = data badge, in the rest of the app). This breaks the affordance contract: pills are display, buttons are action. Mixing them is a Linear/Stripe no-no.
  - **P1** `components/clients/ClientList.tsx:31-33` — `<span>—</span>` for missing category — should be a soft pill "Non catégorisé" or similar for visual rhythm.
  - **P2** `apps/shell/app/clients/page.tsx:175,178` — inline `style={{ marginTop: 12 }}` twice in the same render — extract to a CSS class `.gc-stack-12` or use the existing `.gc-stack`.
- **Premium-meter**: **5/10** — dense, scannable in theory, but score-color flattening and pill-as-button confuse the visual language.

---

### `/audits/[clientSlug]`

Files reviewed: `apps/shell/app/audits/[clientSlug]/page.tsx`, `components/audits/PageTypesTabs.tsx`, `ConvergedNotice.tsx`, `PillarsSummary.tsx`, `AuditQualityIndicator.tsx`, `RichRecoCard.tsx` (preview), `globals.css` (lines 261–337, 1239–1353).

- **Hierarchy**: H1 (client name, 28px) → tabs (per page-type) → for each audit a Card titled "<page_type> · <page_slug>". Cards stack vertically (`.gc-stack`). H1 → H2 (card title 15px) → H3 (font-size 13, uppercase, letterSpacing 0.06em, inline-styled at AuditDetailFull pattern, repeated here lines 108–119) — the H3 is inline-styled instead of class `.gc-section-eyebrow` → repeated noise.
- **Spacing**: Pillar bars (`.gc-pillar-row` grid 130/1fr/70) are clean. But each audit card body has inline `marginTop` (10, 14, 8, 12 — page.tsx:107, 116, 127, 131) — no rhythm.
- **Color**: Pillar fill color comes from `scoreColor(pct)` — good, score-aware. But `.gc-converged-notice` is gold-tinted, `.gc-rich-reco--p0` is red-bordered, and KPI cards are flat — three different "emphasis languages" in one page.
- **States**: Tabs are `.gc-tabs button.active` with cyan underline + soft cyan background — fine. Buttons inside `.gc-evidence-list` use `.gc-pill` styling — same affordance mixup as `/clients`.
- **Issues**:
  - **P0** `apps/shell/app/audits/[clientSlug]/page.tsx:108-120,127-134,146-155` — three large `style={{}}` literals per render. The "Top N reco prioritaires" eyebrow + the "Aucune reco générée" italic + the "+ N autres recos" link are all inline-styled. Hard to theme, hard to reuse.
  - **P1** Inconsistent button system between this page and `/clients`: here actions are `.gc-pill .gc-pill--cyan` ("Voir détail →"), on Home they're `.gc-btn` ("Open V26 archive"). Same intent, two visual languages.
  - **P1** `components/audits/ConvergedNotice.tsx:31-34` — banner uses `<strong>↗ N audits convergent</strong>` with a glyph in the text. The arrow is decorative but tagged inside `<strong>` — should be `aria-hidden` span next to it.
  - **P2** `PageTypesTabs` hints are `${n} audits` but only show when `n > 1` (tabs without hints look unbalanced when at least one tab carries a hint).
- **Premium-meter**: **5.5/10** — the per-pillar score-color mapping is the strongest design moment in the whole app. Killed by inline-style noise around it.

---

### `/audits/[clientSlug]/[auditId]`

Files reviewed: `apps/shell/app/audits/[clientSlug]/[auditId]/page.tsx`, `components/audits/AuditDetailFull.tsx`, `RichRecoCard.tsx`, `AuditScreenshotsPanel.tsx`, `globals.css` (lines 894–1237).

- **Hierarchy**: H1 with **embedded subtitle in a `<span style={{ color: "var(--gc-muted)", fontWeight: 600, fontSize: 18 }}>`** (page.tsx:50) — this is the most egregious example of stylistic shortcut: the secondary info (page_type · page_slug) gets a custom 18px-grey-bold treatment via inline `style`, breaking the existing `.gc-title h1` rules. Layout grid is `1.3fr 0.7fr` (left = scores+recos, right = screenshots).
- **Spacing**: The `RichRecoCard` is the most decorated unit in the app — 4 levels of nested cards (`.gc-rich-reco` → `__head` → `__title` → `__sections` → `__why`/`__how` → `__footer`). Internal spacing is well-defined in CSS (padding 12 14, gap 12, etc). But the wrapper `<Card>` adds yet another bordered surface, so a single reco visually has 3 border lines competing (Card, Rich-reco card, Why/How sub-panel).
- **Color**: Priority border-left color mapping (P0 red / P1 amber / P2 green) is the most "design-system-correct" choice in the codebase — keeps it. Same logic should apply to fleet score color.
- **States**: Collapse/expand with `aria-expanded` + `aria-controls` is correct a11y-wise. But the toggle button (`.gc-rich-reco__toggle`) styling is identical to `.gc-rich-reco__debug-toggle` — two distinct actions look the same.
- **Issues**:
  - **P0** `apps/shell/app/audits/[clientSlug]/[auditId]/page.tsx:50-53` — H1 contains an 18px inline-styled `<span>` for the page_type/page_slug. This pattern (mixing two type sizes inside one H1) appears nowhere else; it's a one-off cheat instead of a proper title + eyebrow component.
  - **P0** Triple-border nesting on recos: `<Card>` (border) → `<article.gc-rich-reco>` (border + border-left) → `<div.gc-rich-reco__why>` (border). Visual noise; need to drop the outer `<Card>` border or make the rich-reco fully bleed.
  - **P1** `components/audits/AuditDetailFull.tsx:97-106` — "Export PDF" rendered as a *disabled-looking pill* (`opacity: 0.5, cursor: "not-allowed"`). User-hostile: dangling promise of a V2 feature. Either ship it or hide it.
  - **P1** `AuditScreenshotsPanel.tsx:108-122` — uses `<img>` with `loading="lazy"` and `max-height: 280px object-fit: cover object-position: top center` — fine, but no skeleton/placeholder during fetch, no "image failed" empty state on broken 404s (just the API route silently fails).
  - **P2** Pills as actions appear yet again: "Voir détail →" / "Tous ses audits" — `<a className="gc-pill gc-pill--soft">`. A pill is a metadata badge, not a navigation primitive.
- **Premium-meter**: **6/10** — the RichRecoCard is the closest thing to "premium feel" in the app, but it's surrounded by inline-style noise that betrays the careful CSS work underneath.

---

### `/gsg` (GSG Handoff)

Files reviewed: `apps/shell/app/gsg/page.tsx`, `components/gsg/Studio.tsx` (alt), `globals.css` (lines 384–504, 625–900 in styles.css).

- **Hierarchy**: H1 "GSG Handoff" → 2-col grid (`0.95fr 1.05fr`) Brief + Preview → "End-to-end Demo" card with the 5-step flow. Each `.gc-e2e__node` carries a numbered circle (gold bg, 28x28, font 14/800) — that's the closest to a true "design moment" in the app — but it lives buried at the bottom of a card.
- **Spacing**: The `.gc-preview` (Studio's preview iframe placeholder) uses **a beige background `#f7f4ee` and black text `#111318`** (globals.css:474) — a deliberate "render in another universe" choice, which is actually good editorial design. But it's only used in the Studio alt-route, not on this main /gsg.
- **Color**: The mode pill ("Complete / Replace / Extend / Elevate / Genesis") uses gold/cyan/soft tones — fine. The mode-selector card-grid (`.gc-modes__grid`, 5-col) is the second-best design moment.
- **States**: Copy-brief button has a toast (`.gc-copy__toast`) animated via the same `gc-fade-in` keyframe — re-used animation, that's good system thinking. But there's no loading / success / error state on the preview iframe load.
- **Issues**:
  - **P0** `apps/shell/app/gsg/page.tsx:198-205` — `aria-disabled` is used as a styling proxy but the link is still `<a href={demo ? ... : "#"}>` clickable, and the visual state is identical whether disabled or not. Either render `<span>` when disabled or apply `pointer-events: none`.
  - **P1** Body copy in Header (page.tsx:246-252) crams "default-src 'self'" + "X-Frame-Options SAMEORIGIN" as `<code>` inside the H1 subtitle — that's engineering-speak in a customer-facing area. Premium consultants don't expose CSP headers in their hero subtitle.
  - **P1** `components/gsg/Studio.tsx:38-44` — the `.gc-flow` 5-card horizontal strip uses `<b>` for the step label and `<span>` for the note. No semantic structure (no `<ol>`, no `<li>`), no aria-current for the active stage.
  - **P2** "V27.2-G" version pill in the header (page.tsx:259) — internal version tag exposed in UI. Either it's a dev badge (then hide in prod) or it's user-facing (then it needs context).
- **Premium-meter**: **5.5/10** — the bones of an editorial layout exist (numbered steps, light preview surface), but the page leaks engineering jargon and never commits to the editorial direction.

---

## Cross-cutting (chrome: Sidebar, Topbar, Breadcrumbs)

Files reviewed: `components/Sidebar.tsx`, `components/Breadcrumbs.tsx`, `components/ViewToolbar.tsx`, `components/command-center/CommandCenterTopbar.tsx`, `globals.css` (lines 1–145).

- **Sidebar (`gc-side`)**:
  - 280px sticky column, dark `#0a0e15` (slightly darker than `--gc-bg #0c1018` — intentional layering, good).
  - "GROWTHCRO V28" brand string is 13px uppercase letter-spaced 0.12em gold-bold-800 (globals.css:19-26). **The brand mark is a literal text string** — no logo, no iconography. For a "premium consultant" positioning, this is the single most "AI-slop SaaS" tell.
  - 4 groups (Pipeline / Studio / Agency Tools / Admin), each with `gc-side-group__label` (10px uppercase, opacity 0.7). 11 nav items total — manageable. But every item carries a "hint" badge ("Command", "Fleet", "V3.2.1", "Brief + LP", "Soon", "V29/V30", "Agency", "Admin") — and "Soon" is shipped as a label on a clickable item (Reality). That's a broken promise badge.
  - No icons on nav items (`gc-nav-item__icon` class exists in CSS but no items use it). The icon slot is reserved but empty.
  - Sign-out button at bottom — full-width ghost button — fine, but lives in a `.gc-side-block` with a 12px muted email above. The email is the only personalized element in the chrome.

- **Topbar (`gc-topbar`)**:
  - Same H1 + subtitle + right-aligned toolbar pattern reused across 5 pages. Consistency = strong. But every page reimplements it (`CommandCenterTopbar.tsx` for `/`, raw markup in `clients/page.tsx`, raw markup in `audits/[c]/page.tsx`, raw markup in `audits/[c]/[a]/page.tsx`, raw markup in `gsg/page.tsx`). The `ViewToolbar.tsx` wrapper exists but is **used by zero of the 5 reviewed routes**. Dead abstraction.

- **Breadcrumbs (`gc-breadcrumbs`)**:
  - URL-derived, humanizes known segments (`SEGMENT_LABELS` map). Slug segments stay verbatim ("weglot" not "Weglot"). 12px font, gold-on-hover.
  - But breadcrumbs are **not rendered on any of the 5 reviewed routes** — because none of them use `<ViewToolbar>`. The breadcrumbs component is shipped but orphaned.

- **Consent banner (`gc-consent`)** rendered globally in `layout.tsx:24` — bottom 16px on every page. Fine.

- **Grain overlay (`gc-grain`)** — fixed full-page SVG noise, opacity 0.035, `mix-blend-mode: overlay`. **This is the strongest premium signal in the entire app.** Quietly elevates the dark surface from "Bootstrap dark" to "considered". Keep it. Add a `prefers-reduced-motion` opt-out? Not needed — it's static.

---

## Brand consistency

- **Tokens system**: Used partially. There are TWO sources of truth: `webapp/packages/ui/src/tokens.ts` (TypeScript object) and `webapp/packages/ui/src/styles.css` `:root` (CSS custom properties). They're kept in sync **by hand** — fragile. No build step verifies they match. The `tokens.ts` is referenced by zero components in the 5 reviewed routes (grep). It's a sketch of a token system, not an enforced one.
- **Color palette**: Coherent on the macro level (dark blue-grey ink + cream text + gold/cyan/green/amber/red accents). The 12 named colors all earn their keep. But the rules of **when to use which** are unwritten: `--gc-gold` is used for brand, for score, for converged-notice accent, for KPI hover — overloaded. Cyan is used for links, for tabs-active, for CTAs (`.gc-pill--cyan`), for some headers. The palette has no semantic layer (no `--gc-color-emphasis`, `--gc-color-critical`, `--gc-color-action` aliases).
- **Typography**: Single weight family (Inter) referenced in CSS but **never actually loaded** (no `next/font`, no Google Fonts `<link>`, no `@font-face`). The browser falls back to `ui-sans-serif` / system-ui. So on macOS users see SF Pro, on Windows users see Segoe UI, on Linux they see whatever — and the "Inter" intent is fictional. Weights used range from 600 to 900 (`fontWeight: 850` in `.gc-title h1` — non-standard weight, falls back to 800 or 900 depending on the actual loaded font). Type scale: 11/12/13/14/15/16/18/22/25/28 — 10 different sizes, no modular ratio (it's not 1.2x, not 1.25x, not 1.333x — it's eyeballed).
- **Spacing scale**: Mostly 4/6/8/10/12/14/16/18/22 in CSS. Not a strict scale; closer to a "what looks right" multiset. Inline `marginTop` values include 6, 8, 10, 12, 14, 16 — same eyeballed approach in TSX.
- **Iconography**: Almost none. ASCII arrows (→ ← ↗ ↑ ↓) substitute for icons throughout: "← Shell", "Voir détail →", "Open ↗", "↗ N audits convergent". A consultancy positioning as "avant-garde" should ship at least a tight icon set (Lucide / Phosphor / custom) — ASCII arrows are the visual marker of a 2010 admin panel.
- **Motion**: Three keyframes total — `gc-fade-in` (modal/toast), `gc-modal-in` (modal entrance), `gc-skeleton-shimmer` (loading shimmer). No page-transition motion, no view-flip on tab change, no scroll-driven moments, no spring physics. The transitions defined inline (`transition: border-color 0.15s, background 0.15s`) are functional but undifferentiated.

---

## Cohesion verdict

**Looks like**: A capable Linear-ish dark dashboard with a gold accent, made by a serious senior eng on a deadline. **Not** premium consultancy. **Not** Aesop/Stripe/Linear-grade. Closer to "Notion meets Vercel admin meets Posthog" — internally consistent, visually safe, ergonomically OK. The grain overlay + gold accent earn it half a point above the median; the inline-style sprawl, the unused `ViewToolbar`/`Breadcrumbs`, the unloaded Inter font, the "Open V26 archive" debris, the pill-as-button affordance bug, and the 1-bit iconography drag it back down.

**Pattern**: shipped V26 doctrine semantics, postponed visual identity to V27/V28 that never got the typography/iconography pass.

---

## Recommendations Wave C priority

1. **(P0) Kill the inline-style sprawl** — extract the 339 `style={{}}` usages into 6–8 named CSS classes (`.gc-stack-12`, `.gc-eyebrow`, `.gc-h1-meta`, `.gc-callout-muted`, `.gc-cta-disabled`). Single sweep across the 5 routes.
2. **(P0) Load Inter via `next/font`** — `import { Inter } from "next/font/google"` in `app/layout.tsx`, attach `className` to `<html>`. Without this, the type direction is fiction. ETA 15 min.
3. **(P0) Score-color mapping fleet-wide** — apply `scoreColor(pct)` to `/clients` table score column + KPI accent on `/` ("P0 recos" should glow red when > 0). Same function, three new call sites.
4. **(P0) Choose ONE action primitive** — either `.gc-btn` everywhere or a new `.gc-action` class; **demote `.gc-pill` to data-only**. Audit and refactor `/clients` reset button, `/audits/[c]` "Voir détail →", `/audits/[c]/[a]` toolbar nav.
5. **(P1) Adopt the unused `<ViewToolbar>`** — wire breadcrumbs into all 4 non-home routes. Currently shipped but invisible.
6. **(P1) Triple-border surgery on `RichRecoCard`** — drop the outer `<Card>` border when the inner `.gc-rich-reco` already carries the priority-left accent. Or: extract a `<RichRecoStack>` that bleeds inside a borderless parent.
7. **(P1) Type scale lockdown** — replace the 10 eyeballed sizes with a 7-step modular scale (11/12/14/16/18/22/28 = ratio 1.25, "Major Third"). Document in `tokens.ts` + enforce in CSS.
8. **(P1) Icon system** — ship a 24-icon Lucide subset wired through `<Icon name="...">`, replace ASCII arrows. Estimated 2h.
9. **(P1) Semantic color aliases** — add `--gc-color-action` / `--gc-color-emphasis` / `--gc-color-critical` aliases in `:root`, rebind component CSS to the aliases (raw `--gc-gold`/`--gc-cyan` only at the alias layer).
10. **(P2) Brand mark** — replace the "GROWTHCRO V28" text string in the sidebar with a 32x32 wordmark + tagline. Even a hand-letter G with the gold accent would 2x the perceived polish.
11. **(P2) Move "Open V26 archive" to settings/admin** — out of the home topbar.
12. **(P2) Audit-detail H1 split** — replace the inline-styled `<span>` subtitle inside H1 with a proper `<header>` block: H1 + dim eyebrow line + meta pills row.

**Net effect target**: premium-meter from 5.2 → 7.5 in 1 sprint (≤ 2 days), 8.5 with iconography + brand mark.
