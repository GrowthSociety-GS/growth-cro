# Audit A.6 — Accessibility WCAG 2.1 AA — 2026-05-14

**Auditor**: static review (no live axe/lighthouse) of TSX semantics, ARIA usage, Tailwind/CSS classes
**Scope**: Wave SP-4..SP-11 shipped + chrome (Sidebar, Breadcrumbs, ViewToolbar, CommandCenterTopbar, modals, common components, layout.tsx, key pages)
**Method**: WCAG 2.1 Level A + AA criteria, severity P0 (blocks AT users) / P1 (degrades UX) / P2 (best-practice)

---

## TL;DR

The webapp **does NOT meet WCAG 2.1 AA** out of the box. The foundation is solid — skip link present, `:focus-visible` ring, `prefers-reduced-motion` honored, modals trap with ESC + body scroll lock, all forms have `<label htmlFor>`, native `<button>` everywhere — but the **dark theme (`#0c1018` background) combined with `var(--gc-muted) = #98a2b3`** fails the 4.5:1 contrast minimum for the dozens of muted text strings, and several other recurring patterns block screen-reader and keyboard users. Net: **6 P0 violations, 11 P1, 9 P2** spread across ~25 files.

---

## WCAG compliance by criterion

| Criterion | Level | Status | Failures |
|---|---|---|---|
| 1.1.1 Non-text Content | A | PARTIAL | 2 (SVG `role="img"` without sufficient alt context, decorative grain layer OK) |
| 1.3.1 Info and Relationships | A | PARTIAL | 4 (`<ul>`/`<ol>` mostly correct, but radial chart axis labels lack association; some headings skipped — h1 → h3 directly) |
| 1.3.2 Meaningful Sequence | A | PASS | 0 |
| 1.3.4 Orientation | AA | PASS | 0 |
| 1.4.1 Use of Color | A | PARTIAL | 2 (severity in funnel viz conveyed by color only; pillar fill color is sole signal) |
| 1.4.3 Contrast (Minimum) | AA | **FAIL** | 8+ (extensive use of `var(--gc-muted) #98a2b3` on `var(--gc-bg) #0c1018` ≈ 4.13:1 — fails 4.5:1 for small text. `var(--gc-line-soft)` borders ≈ 1.3:1 OK for non-text. Pill borders 0.45 alpha ≈ 2.3:1 fails 3:1 for UI components 1.4.11) |
| 1.4.4 Resize Text | AA | PASS | 0 (rem/em + viewBox SVG scales) |
| 1.4.5 Images of Text | AA | PASS | 0 |
| 1.4.10 Reflow | AA | PASS | 0 (responsive media queries at 480/640/720/1180px) |
| 1.4.11 Non-text Contrast | AA | **FAIL** | 3 (focus-visible OK, but pill borders, form `var(--gc-line)` borders < 3:1 against panel bg) |
| 1.4.12 Text Spacing | AA | PASS | 0 |
| 1.4.13 Content on Hover or Focus | AA | PASS | 0 |
| 2.1.1 Keyboard | A | PARTIAL | 1 (modal closes ESC OK; backdrop click OK; **no focus trap** — Tab leaves the modal) |
| 2.1.2 No Keyboard Trap | A | PASS | 0 |
| 2.4.1 Bypass Blocks (skip link) | A | PASS | 0 (`<a href="#gc-main">` present in `layout.tsx:19`) |
| 2.4.2 Page Titled | A | PASS | 0 (`metadata.title` in layout) |
| 2.4.3 Focus Order | A | PARTIAL | 1 (modal not focus-trapped; restore-focus on close not implemented) |
| 2.4.4 Link Purpose (in Context) | A | PARTIAL | 3 ("Voir détail →", "+ {n} autres", "↗" icons used as link text without sr-only context) |
| 2.4.6 Headings and Labels | AA | PARTIAL | 2 (some `<h3>` after `<h1>` skipping `<h2>` in audit detail; quality indicator uses `<span>` not heading) |
| 2.4.7 Focus Visible | AA | PASS | 0 (`globals.css:1490` defines `:focus-visible` for all interactive) |
| 2.5.3 Label in Name | A | PASS | 0 |
| 2.5.5 Target Size (AAA) | AAA | PARTIAL | 4 (close-modal button 28×28 px, pill links 24×∼px height — below 44×44 rec) |
| 3.2.1 On Focus | A | PASS | 0 |
| 3.2.2 On Input | A | PASS | 0 |
| 3.3.1 Error Identification | A | PARTIAL | 1 (modal forms render `role="alert"` for top-level error; no per-field `aria-invalid` or `aria-describedby` linkage) |
| 3.3.2 Labels or Instructions | A | PASS | 0 |
| 3.3.3 Error Suggestion | AA | PARTIAL | 1 (errors surface HTTP/server message verbatim — no contextual remediation copy) |
| 3.3.4 Error Prevention (Legal/Financial/Data) | AA | PASS | 0 (DeleteConfirmModal asks for confirmation) |
| 4.1.2 Name, Role, Value | A | PARTIAL | 5 (`role="presentation"` on modal backdrop OK, but `<details>` toggles miss `aria-expanded` parity; `<input list="...">` autocomplete OK; vote buttons use color-only state) |
| 4.1.3 Status Messages | AA | PARTIAL | 1 (Loading skeleton has `role="status" aria-live="polite"` OK; toast on copy uses class `--ok/--err` but no `role="status"`) |

---

## P0 violations (block users)

### P0-1 — Contrast failure: muted text on background (WCAG 1.4.3)
**Where**: pervasive — `var(--gc-muted) = #98a2b3` over `var(--gc-bg) = #0c1018` ≈ **4.13:1**, fails the 4.5:1 minimum for small text (<18pt or <14pt bold). Affected files include almost every page:
- `webapp/apps/shell/components/Sidebar.tsx:89` (email under sidebar)
- `webapp/apps/shell/components/Breadcrumbs.tsx:86` (`.gc-breadcrumbs__link` color)
- `webapp/apps/shell/components/audits/AuditDetailFull.tsx:55,109,134` ("Pas de scores", "Aucune reco", footer audit metadata)
- `webapp/apps/shell/components/audits/AuditScreenshotsPanel.tsx:89,93` ("Pas de captures disponibles", file path hint)
- `webapp/apps/shell/components/audits/PillarsSummary.tsx:33,67` ("Pas de scores structurés", "Score global")
- `webapp/apps/shell/components/audits/RichRecoCard.tsx` (via `gc-rich-reco__text` → `var(--gc-soft)` is OK at #c8cfda but `gc-rich-reco__pattern { color: var(--gc-muted) }` fails)
- `webapp/apps/shell/components/common/EmptyState.tsx:67` (`gc-empty-state__desc` uses `--gc-muted`)
- `webapp/apps/shell/components/common/LoadingSkeleton.tsx` (skeleton OK, but `<span className="gc-sr-only">` reading by AT, not visual)
- `webapp/apps/shell/components/Pagination.tsx:42,55,71` ("Précédent" disabled `opacity: 0.4` makes a4 lower further)
- `webapp/apps/shell/app/page.tsx:106` ("Supabase non configuré" error)
- Almost every page uses `style={{ color: "var(--gc-muted)", fontSize: 12 }}` as inline meta — multiplied across all pages

**Impact**: blocks low-vision users completely on dim text and any user in bright ambient light. Fix: bump `--gc-muted` to `#b6c0d0` (≥ 5.2:1) or use `--gc-soft = #c8cfda` (≈ 8.5:1) for prose, reserve `--gc-muted` for icons only.

### P0-2 — Modal does NOT trap focus (WCAG 2.1.1, 2.4.3)
**Where**: `webapp/packages/ui/src/components/Modal.tsx:32-37` — the ref is focused on open, but Tab moves focus outside the dialog into the obscured page content.
- No focus trap loop on Tab/Shift+Tab.
- No restore-focus to the trigger button when modal closes.

**Impact**: keyboard + screen-reader users lose orientation; they can interact with elements they cannot see. Affects every modal (CreateAuditModal, EditAuditModal, EditRecoModal, DeleteConfirmModal). Fix: add a focus-trap (e.g. focus the first focusable child on mount, intercept Tab to wrap; store `document.activeElement` on open and restore on close).

### P0-3 — `aria-disabled="true"` on `<span>` link clones (WCAG 4.1.2, 2.1.1)
**Where**:
- `webapp/apps/shell/app/gsg/page.tsx:198-205` — `<a ... aria-disabled={!demo}>` Open preview in new tab still receives focus and is clickable (href="#")
- `webapp/apps/shell/components/audits/AuditDetailFull.tsx:99-105` — `<span ... aria-disabled="true" title="Export PDF — V2" ...>` Export PDF visually styled like a pill but is a span (not focusable, role unclear)
- `webapp/apps/shell/components/common/Pagination.tsx:55,71` — `<span ... aria-disabled="true">` for prev/next

**Impact**: AT announces "link, dimmed" without semantics; keyboard users can still focus the `<a>` and trigger an empty href, or cannot focus the span at all. Fix: use `<button disabled type="button">` or actually remove from DOM. `<a aria-disabled>` is **not equivalent** to `<button disabled>` — anchors do not honor disabled.

### P0-4 — Pill borders fail UI contrast 3:1 (WCAG 1.4.11)
**Where**: `webapp/packages/ui/src/styles.css:162-221` — all `.gc-pill--*` variants use a 0.45-alpha border on a transparent-0.08 background. Against the page bg `#0c1018`:
- Red border ≈ rgba(240,113,120,0.45) on #0c1018 → ~2.4:1
- Amber border ≈ rgba(243,199,107,0.45) on #0c1018 → ~2.6:1
- Cyan border ≈ rgba(101,214,207,0.45) on #0c1018 → ~2.3:1
- Gold border ≈ rgba(215,180,106,0.45) on #0c1018 → ~2.5:1

**Impact**: low-vision users cannot perceive the pill boundary; they must rely on text alone, which often duplicates context (P0/P1/P2). Fix: use solid 0.65+ alpha or rely on text-color contrast only.

### P0-5 — Form errors lack per-field association (WCAG 3.3.1, 4.1.2)
**Where**: `CreateAuditModal.tsx:167-171`, `EditAuditModal.tsx:119-123`, `EditRecoModal.tsx:170-174`, `DeleteConfirmModal.tsx:100-104` — a single top-level `<p role="alert">` shows the server error, but:
- The offending field is never marked with `aria-invalid="true"`.
- The error message is not linked to the field via `aria-describedby`.
- Required fields (e.g. `client_slug`, `title`) lack `aria-required="true"` despite `required` attribute (which auto-implies but AT support is inconsistent).

**Impact**: AT users hear "Une erreur est survenue" but cannot tell which input failed validation. Fix: parse server error → set `aria-invalid` on the corresponding input + `aria-describedby` to the error node.

### P0-6 — `ClientPicker` and `FiltersBar` inputs miss visible labels (WCAG 3.3.2, 1.3.1)
**Where**:
- `webapp/apps/shell/components/audits/ClientPicker.tsx:34-46` — `<input placeholder="Rechercher un client…">` and `<select>` have no `<label>`, no `aria-label`. Placeholder is not a label substitute.
- `webapp/apps/shell/components/common/FiltersBar.tsx:79-86, 97-107, 117-129` — inputs/selects have `aria-label={def.label}` (good), but the **rendered** label text is only inside `placeholder`. Voice-control users cannot say "Click X".

**Impact**: voice-control + AT users cannot target the controls by visible name. Fix: render the label visually OR keep the visible placeholder while also adding a visually-hidden `<label>` per input.

---

## P1 violations (degraded UX for assistive tech)

### P1-1 — Heading hierarchy skips levels (WCAG 1.3.1, 2.4.6)
- `webapp/apps/shell/components/audits/AuditDetailFull.tsx` — Card title renders `<h2>` (in `Card.tsx:16`), then `<h3>` (RichRecoCard title:120) which is OK, but `<h3>` for "Top N reco" in `audits/[clientSlug]/page.tsx:109-118` is rendered with inline style not semantic ranks.
- `webapp/apps/shell/components/learning/ProposalDetail.tsx:84,86,88` — `<h3>` after Card `<h2>` mostly OK but `<h3>` "Decision" right after `<h2>` from Card without intermediate `<h2>` per section.

### P1-2 — `<details>` collapsible toggles miss `aria-expanded` (WCAG 4.1.2)
Native `<details>`/`<summary>` is OK for sighted/keyboard, but the **custom** toggle buttons in RichRecoCard (lines 108-117, 148-155) use `aria-expanded` correctly. However:
- `webapp/apps/shell/components/audits/AuditDetailFull.tsx:119` — `<details className="gc-audit-recos__more">` — native, OK.
- `webapp/apps/shell/components/audits/AuditScreenshotsPanel.tsx:125,144` — native `<details>`, OK.

(actually these are largely correct; downgrading from initially-reported violations)

### P1-3 — Icon-only buttons rely on text content for AT (WCAG 4.1.2)
- `webapp/packages/ui/src/components/Modal.tsx:64` — close button "×" has `aria-label="Fermer"` GOOD.
- `webapp/apps/shell/components/learning/ProposalVotePanel.tsx:103-114` — "re-vote" button has `aria-label="Re-vote"` GOOD.
- BUT `webapp/apps/shell/components/audits/PageTypesTabs.tsx` `Tabs` (UI lib) uses `role="tab"` + `aria-selected` but no `aria-controls` linking to a `<panel id>` — AT users can't navigate from tab → panel via shortcuts.

### P1-4 — Arrow-only links: "← Shell", "+ {n} autres", "Voir détail →" (WCAG 2.4.4)
- `webapp/apps/shell/app/clients/page.tsx:141-147`, `audits/[clientSlug]/page.tsx:204,244` — links named "← Shell", "Voir détail →" rely on positional context. AT-only users hear "left arrow Shell" or "voir detail right arrow". Use `aria-label="Retour au shell"` or replace arrow with text equivalent.

### P1-5 — Empty-state CTA is `<a className="gc-btn">` (WCAG 4.1.2)
- `webapp/apps/shell/components/common/EmptyState.tsx:70-72` — anchor styled as button is OK semantically (it's a link to a route), but it lacks any context if the link target is the same page (e.g. "Importer un client" → /clients).

### P1-6 — Vote panel "+ note" toggle uses dashed border for state (WCAG 1.4.1, 4.1.2)
- `webapp/apps/shell/components/learning/ProposalVotePanel.tsx:153-168` — `aria-expanded={showNote}` is set GOOD; but the visual state difference is only border-style (dashed). Add a non-color cue (e.g. icon).

### P1-7 — Radial chart axis labels (WCAG 1.1.1, 1.3.1)
- `webapp/apps/shell/components/clients/PillarRadialChart.tsx:54,93-108` — `<svg role="img" aria-label="Scores par pilier">` is set, but the underlying data points and individual pillar values are only accessible via the visual legend (lines 111-122). For AT, the chart says "Scores par pilier" with no data. Provide `<title>` and `<desc>` inside the SVG with the data summary, or render a visually-hidden `<table>` mirror.

### P1-8 — Empty-state container missing live region (WCAG 4.1.3)
- `webapp/apps/shell/components/common/EmptyState.tsx` doesn't carry `role="status"`. If the empty state appears after a filter change (e.g. "no client matches"), AT users won't be notified. Add `role="status"` or `aria-live="polite"`.

### P1-9 — `<select>` outside `<label>` in inline GSG picker (WCAG 1.3.1)
- `webapp/apps/shell/app/gsg/page.tsx:284-292` — has `<label htmlFor="gsg-client">Client</label>` linked GOOD.
- `webapp/apps/shell/components/learning/ProposalList.tsx:99-130` — all `<select>` elements have no `<label>` and no `aria-label`. Three filters anonymous to AT.
- `webapp/apps/shell/components/audits/ClientPicker.tsx:39` — `<select>` (category) no label.

### P1-10 — Funnel viz: drop-pct as color-only signal (WCAG 1.4.1)
- `webapp/apps/shell/components/funnel/FunnelStepsViz.tsx:43-58` — "↘" vs "→" arrow gives some non-color cue GOOD, but `style={{ color: severe ? "var(--gc-red)" : "var(--gc-green)" }}` is the primary cue. The kept-pct number is in muted color (already a P0-1 issue). Add explicit textual indicator: "WARN" or "OK".

### P1-11 — `<a target="_blank">` without screen-reader cue (WCAG 3.2.5)
- Many anchors use `target="_blank" rel="noopener noreferrer"` GOOD security but don't announce "opens in new tab" to AT. E.g. `audits/[c]/[a]/page.tsx:59`, `audits/[clientSlug]/page.tsx:96-103`, `AuditScreenshotsPanel.tsx:48-50`, `command-center/ClientHeroDetail.tsx:88-94`. Add a visually-hidden span: `<span className="gc-sr-only">(ouvre dans un nouvel onglet)</span>` or `aria-label`.

---

## P2 violations (recommended)

### P2-1 — Touch target size (WCAG 2.5.5 AAA)
- Modal close `.gc-modal__close { width: 28px; height: 28px }` — below 44×44 recommended.
- `.gc-pill { padding: 3px 7px; font-size: 11px }` clickable pills (e.g. CreateAuditTrigger, ClientDeleteTrigger) reach ~22-26 px height — below 44.
- `.gc-rich-reco__toggle, .gc-rich-reco__debug-toggle { padding: 3px 8px }` ≈ 22 px height — below 44.

### P2-2 — Skip link not styled on first focus visually
- `.gc-skip-link:focus, :focus-visible { top: 8px }` works, BUT the `transition: top 0.15s ease` causes a flash for keyboard users. Already honors `prefers-reduced-motion`. OK as-is, but contrast ratio of skip-link gold-on-near-black is excellent.

### P2-3 — `<button>` without explicit `type="button"` defaults to "submit"
- `webapp/packages/ui/src/components/NavItem.tsx:35-41` — `<button>` no `type` → submits any ancestor `<form>`. Sidebar wraps NavItems in `<nav>` so risk is low, but signing-out button in Sidebar:91-99 is inside a `<form>` and uses `type="submit"` correctly. Audit all `<button>` for explicit type.
- `webapp/packages/ui/src/components/ClientRow.tsx:14` — `<button>` no `type`.
- `webapp/apps/shell/components/clients/ClientDetailTabs.tsx:29` — `<button type="button">` GOOD.

### P2-4 — Animations not feature-detected
- `globals.css:1517 @keyframes gc-skeleton-shimmer` honored via `prefers-reduced-motion: reduce` GOOD.
- `webapp/packages/ui/src/styles.css:416,438 @keyframes gc-fade-in, gc-modal-in` — NOT wrapped in `prefers-reduced-motion`. Modal still animates for users who requested reduced motion.

### P2-5 — `<dl>` debug list in RichRecoCard not labeled (WCAG 1.3.1)
- `webapp/apps/shell/components/audits/RichRecoCard.tsx:157-178` — `<dl className="gc-rich-reco__debug">` has no `<caption>` or aria-label. AT users won't know it's a "debug metadata" cluster.

### P2-6 — Page title not updated per route (WCAG 2.4.2)
- `webapp/apps/shell/app/layout.tsx:7-11` — `metadata.title` is global; individual routes don't override. AT users hear the same title at every page. Add `export const metadata = { title: "..." }` per `page.tsx`.

### P2-7 — `<code>` and `<pre>` blocks not announced as code (WCAG 1.3.1)
- `webapp/apps/shell/components/learning/ProposalDetail.tsx:89-101` — `<pre>{JSON.stringify(...)}</pre>` no `aria-label`. AT reads char-by-char.

### P2-8 — Settings tab list missing tablist structure (WCAG 4.1.2)
- `webapp/apps/shell/components/clients/ClientDetailTabs.tsx:26-39` — `role="tablist"`/`role="tab"`/`aria-selected` set GOOD, but the `<div className="gc-tab-panel">` (line 40-44) is missing `role="tabpanel"` and `aria-labelledby` linking to the active tab.

### P2-9 — `lang="fr"` consistent but mixed-language content
- `webapp/apps/shell/app/layout.tsx:16` — `<html lang="fr">` GOOD. But English strings ("Open preview in new tab", "Switch", "Pending", "Accepted", proposal types) are scattered. Use `lang="en"` on English subtrees, or translate.

---

## Recommendations Wave C priority

1. **Fix contrast (P0-1)**: bump `--gc-muted` from `#98a2b3` to `#b6c0d0` (or use existing `--gc-soft` `#c8cfda` for prose). One-line CSS change → unblocks ~70 % of text contrast failures across the app.
2. **Implement focus trap + restore on Modal (P0-2)**: 30 LOC in `packages/ui/src/components/Modal.tsx`. Use the `inert` attribute on the rest of the document, or implement a Tab cycle listener. Restore `previousActiveElement` on close.
3. **Replace `<a aria-disabled>` and `<span aria-disabled>` with real `<button disabled>` (P0-3)**: ~10 LOC changes across 3 files.
4. **Bump pill alpha (P0-4)**: change pill borders from 0.45 → 0.65 alpha in `packages/ui/src/styles.css` (5 lines).
5. **Per-field error association (P0-5)**: parse server error → `aria-invalid` + `aria-describedby` in the 4 modals (~20 LOC each).
6. **Add visible labels to ClientPicker + ProposalList filters (P0-6)**: render the label outside placeholder. ~5 LOC each.
7. **Heading hierarchy pass (P1-1)**: replace inline-styled `<h3>` with structurally appropriate `<h2>`/`<h3>` per page; one PR.
8. **Per-route `<title>` metadata (P2-6)**: add `export const metadata` to every `app/*/page.tsx`. Easy SEO + a11y win.
9. **`<svg>` accessible mirror for radial chart (P1-7)**: add visually-hidden table summarizing pillar/value pairs.
10. **`aria-live` regions for filter empty-states (P1-8)**: `role="status"` on `EmptyState` and the "Aucun client correspondant" inline messages.
11. **"opens in new tab" cue (P1-11)**: append visually-hidden span to all `target="_blank"` anchors. Project-wide grep-and-replace.
12. **Wrap modal/fade animations in `prefers-reduced-motion: reduce` (P2-4)**: 4 LOC in `styles.css`.

---

**File paths inventoried**:
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/layout.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/globals.css`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/page.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/clients/page.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/audits/[clientSlug]/page.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/audits/[clientSlug]/[auditId]/page.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/gsg/page.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/settings/page.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/Sidebar.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/Breadcrumbs.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/ViewToolbar.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/command-center/CommandCenterTopbar.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/command-center/CommandCenterKpis.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/command-center/FleetPanel.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/command-center/ClientHeroDetail.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/CreateAuditModal.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/EditAuditModal.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/EditRecoModal.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/CreateAuditTrigger.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/AuditEditTrigger.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/RecoEditTrigger.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/RichRecoCard.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/AuditDetailFull.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/AuditDetail.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/AuditScreenshotsPanel.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/PageTypesTabs.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/PillarsSummary.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/ClientPicker.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/AuditQualityIndicator.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/ConvergedNotice.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/clients/ClientList.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/clients/ClientDeleteTrigger.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/clients/ClientDetailTabs.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/clients/PillarRadialChart.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/DeleteConfirmModal.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/EmptyState.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/ErrorFallback.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/LoadingSkeleton.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/FiltersBar.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/SortDropdown.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/common/Pagination.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/funnel/FunnelStepsViz.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/funnel/FunnelDropOffChart.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/judges/JudgeScoreCard.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/judges/JudgesConsensusPanel.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/learning/ProposalDetail.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/learning/ProposalList.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/learning/ProposalQueue.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/learning/ProposalVotePanel.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/learning/ProposalStats.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/Modal.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/FormRow.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/Button.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/NavItem.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/Card.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/Tabs.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/ClientRow.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/components/ConsentBanner.tsx`
- `/Users/mathisfronty/Developer/growth-cro/webapp/packages/ui/src/styles.css`
