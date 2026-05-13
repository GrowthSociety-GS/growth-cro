# V26 HTML ↔ Next.js webapp — Feature Parity Diff (2026-05-14)

> **Method.** Feature-by-feature line-level audit. V26 source: `deliverables/GrowthCRO-V26-WebApp.html` (3666 LOC, 213 KB, doc title `GrowthCRO V26 — Closed Loop Observatory`, generated 2026-05-05) + its data bundle `deliverables/growth_audit_data.js` (12 MB, `version: v27.0.0-panel-roles`). Next.js source: `webapp/apps/shell/` post-FR-1 consolidation 2026-05-13 (single Next.js shell, was 4 apps).
> **Scope.** Just the 11 V26 panes + global chrome. The "agency tools" (`/audit-gads`, `/audit-meta`) are explicit V26+ additions and only counted in P3.

---

## TL;DR

**Coverage: ~28 % feature-parity, ~12 % visual-DNA-parity.** The Next.js webapp ports the *minimum spine* of V26 (clients list, audits drill-down, recos, doctrine stub, GSG handoff, learning proposals, reality monitor) but **strips out** every distinctive trait that made V26 feel like a high-end observatory: starfield + Cormorant Garamond + sunset-gold gradient KPIs are gone, replaced by a flat IDE-look (Inter only, panel chrome `#121823`, no italic serif anywhere). On the data side, ~6 of the 8 V26 dashboard KPIs are missing (no Closed-Loop coverage strip, no 6-pillar fleet bars, no priority distribution, no business/page-type breakdowns), the Scent Trail and Experiments panes don't exist at all, GEO Monitor is missing, and the per-page audit view has lost the screenshot-with-bbox-overlay crops, the funnel steps panel, the 3-tab synthesis (Problème / Action / Pourquoi), the per-step recos, the converged-tunnel deduplication, and the dual-viewport (desktop/mobile) toggle.

The "écran de fumée" complaint is structurally accurate: the Next.js webapp is *administrationware* over Supabase rows, not the Closed-Loop Observatory V26 designed.

---

## V26 design DNA inventory

Source: lines 11-849 of `deliverables/GrowthCRO-V26-WebApp.html`. This is what Next.js has lost.

### Color palette (verbatim CSS custom properties, L17-78)

```
Night sky (background tiers)
  --night-abyss:  #000207  (page bg)
  --night-deep:   #020510
  --night-mid:    #050c22
  --night-elev:   #0b1634   (card surfaces elevated)
  --night-glow:   #122a5a

Aurora (secondary accent)
  --aurora:        #4d8fff
  --aurora-glow:   rgba(77,143,255,.28)
  --aurora-violet: #8c7ef1
  --aurora-cyan:   #6ee0df

Sunset Gold (V22 signature, for key info)
  --gold-sunset:   #e8c872     ← cult of KPI numbers
  --gold:          #d4a945
  --gold-deep:     #b8863a
  --gold-glow:     rgba(232,200,114,.35)
  --gold-dim:      rgba(232,200,114,.08)
  --bronze:        #a67b3e

Stars (typography tiers)
  --star:          #fbfaf5
  --star-warm:     #f6eed6
  --star-dim:      rgba(251,250,245,.62)
  --star-faint:    rgba(251,250,245,.18)

Glass (glassmorphism cards)
  --glass:                rgba(20,30,65,.35)
  --glass-border:         rgba(232,200,114,.12)   ← gold-tinted!
  --glass-border-strong:  rgba(232,200,114,.28)
  --glass-hover:          rgba(30,45,90,.5)

Semantic (continuous gradient, not flat traffic-lights)
  --ok:    #6bc58a   --ok-soft   --ok-glow
  --warn:  #e8c872   (≡ gold sunset = warn, deliberate harmony)
  --bad:   #e87555   (warm red, never criard)
  --indigo:#a69cff
```

Next.js token set (`webapp/packages/ui/src/styles.css` L1-22): **9 flat tokens**, no glass, no star tier, no gold-tinted borders. `--gc-gold: #d7b46a` is a dirtier mustard than `#e8c872`. `--gc-text: #f4f1e8` ≈ V26 `--star`, but with no `--star-warm` / `--star-dim` tiers there's no typography breathing.

### Typography (L9-10, L69-71)

```
--ff-display: 'Cormorant Garamond', 'Playfair Display', Georgia, serif
              (italic editorial serif — used everywhere for headlines,
               KPI numbers, card titles, prestige numbers)
--ff-body:    'Inter'  (300/400/500/600/700)
--ff-mono:    'JetBrains Mono', SF Mono, Menlo  (KPI subs, badges, labels)
```

Next.js (`app/layout.tsx` L12-17): **only Inter**, no Cormorant Garamond, no JetBrains Mono. Every italic gold KPI value (`.kpi__value` L290-296 gradient text), every `.prestige-gold`, every `.card__title` editorial italic — gone. The `--gc-font-sans` var maps to Inter only.

### Spacing scale (L17-20)

```
--sp-0: 0.236rem   ← φ⁻³
--sp-1: 0.382rem   ← φ⁻²
--sp-2: 0.618rem   ← φ⁻¹
--sp-3: 1rem       ← 1
--sp-4: 1.618rem   ← φ
--sp-5: 2.618rem   ← φ²
--sp-6: 4.236rem   ← φ³
--sp-7: 6.854rem   ← φ⁴
```

Golden-ratio modular scale, explicitly documented in the CSS comment as "puissances du nombre d'or ϕ≈1.618 (éch modulaire stricte)". Next.js uses **no scale at all** — `globals.css` has hardcoded `padding: 22px`, `gap: 14px`, `margin-bottom: 18px` with no design-token discipline.

### Layout grid system (L149-192)

```
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 68px 1fr;
  grid-template-areas: "sidebar header" "sidebar main";
}
```

Two-region layout (sidebar 240px + header 68px sticky-top + main grid). Next.js (`globals.css` L3-7) flattens this to `280px 1fr` columns only — **no top header**, breadcrumb / search / nouvel-audit buttons all live inside individual page topbars, inconsistently rendered.

### Distinctive elements (the visceral DNA)

1. **Starfield canvas (`#starfield-canvas`, L120-128, plus engine at L3365+)** — full multi-layer parallax animated starfield, fade-in 1.8s on load, "RDR2-inspired Alaska night sky" per the CSS comment. **Next.js has none.**
2. **Grain texture (`.grain`, L131-135)** — Perlin SVG noise overlay 3% opacity at `z-index:9999`, mixed `overlay`. Next.js has `gc-grain` element in layout.tsx L35 but its CSS isn't in globals.css (greppable), so it's effectively a hollow div.
3. **Glass cards with gold-tinted borders + hover glow (L196-221)** — `backdrop-filter: blur(22px) saturate(160%)`, double box-shadow inset + outer, micro gold accent on hover. Next.js cards are flat `#121823 panels` with `1px solid #273246` borders.
4. **`.prestige-gold` text + KPI value gradient (L138-143, L290-296)** — `background: linear-gradient(135deg, #fbfaf5 0%, #e8c872 55%, #d4a945 100%)`, italic Cormorant, `drop-shadow(0 0 18px var(--gold-glow))`. Used for KPI numbers, score values. **Completely absent in Next.js** (KPIs are plain `25px bold`).
5. **Score-color gradient continu (HSL `0°→60°→120°`)** L770-776 + JS `scoreColor(pct)` L1556-1565 — a true continuous red→yellow→green color per percentage point. Next.js uses 3 flat tokens (`--gc-red`/`--gc-amber`/`--gc-green`) and switches via if/else.
6. **Critical-card pulse animation (L250-254)** + **`@keyframes pulse`** (L347) — animated alert ring around p0-heavy clients. Absent.
7. **Stagger-in entrance animation (L231-247)** — children of `.stagger-in` fade-up with cumulative `animation-delay` 0→480ms over 9 items. Absent.
8. **Magnetic CTA button hover (L256-261)** — `translateY(-1px)` with snap easing. Next.js `.gc-btn` has `border-color` transition only.

### Animation patterns

- `--ease-aura: cubic-bezier(0.23, 1, 0.32, 1)` (infinitely smooth exit)
- `--ease-snap: cubic-bezier(0.34, 1.56, 0.64, 1)` (overshoot snap)
- `--ease-inertia: cubic-bezier(0.19, 1, 0.22, 1)`
- Durations `--dur-fast: 0.2s`, `--dur: 0.45s`, `--dur-slow: 0.85s`
- Used everywhere — pane fade-in (`@keyframes fadein` L335), pillar bar fills (`transition: width 0.9s var(--ease-aura)` L790), screenshot crop reveal, modal scale-in.

Next.js has **zero ease tokens**. Transitions are linear `0.15s ease` defaults in `.gc-btn:hover { transition: border-color 0.15s, background 0.15s }`.

---

## Per-pane diff (11 V26 panes)

### Pane 1 — Dashboard (V26 `pane-dashboard`, L901-972)

**V26 features inventoried**:
- **Section head** "Dashboard V26 · Closed-Loop Observatory" + sub "Vue agrégée fleet · 7 piliers V26 · Brand DNA + Design Grammar coverage · evidence trail · lifecycle"
- **`#dash-kpis`** (4 cards, italic gold numbers) — P0 Blockers, Clients audités, Total recos (with `P0:N · P1:N · P2:N` sub), Score moyen (n%)
- **`#dash-v26-strip` Closed-Loop coverage card** (gold left-border) — **8 module status KPIs** : Evidence Ledger, Reco Lifecycle, Brand DNA, Design Grammar, Funnel (V24, with canonical count), Reality, GEO, Learning. Each renders `count/total + status + note` with color = `statusColor(status)`. Source: `DATA.module_status` from `growth_audit_data.js`.
- **4 dashboard tabs** (`#dash-tabs`) : `fleet` / `business` / `pagetype` / `critical`
  - **fleet tab** — 2 cards : `#pillar-bars` (6 piliers Hero/Persuasion/UX/Coherence/Psycho/Tech with continuous-HSL fill bars + percentage), `#priority-bars` (P0/P1/P2/P3 distribution bars with reco count)
  - **business tab** — `#business-table` : rows of business types with clients/pages/P0/avg score + sparkline-style bar
  - **pagetype tab** — `#pagetype-table` : home vs pdp vs collection vs pricing breakdown
  - **critical tab** — `#critical-clients` grid of top-20 P0-heavy clients as clickable `client-card`s with pulsing-red dot if P0>3
- **Section subtitle dynamic** — `<span id="dash-total-recos">` injects the count

**Next.js equivalent**: `app/page.tsx` renders `<CommandCenterTopbar>` + `<CommandCenterKpis>` + `<FleetPanel>` (left) + `<ClientHeroDetail>` (right).

**Status**:
- ⚠️ Section head different — "Command Center" + "Fleet, priorités et client focus" subtitle (less doctrine-laden, no V26 vocabulary)
- ⚠️ KPI grid 5 cards : Fleet, P0 recos, Avg score, Recent runs (7d), Active audits (30d). Missing: total recos with priority sub-breakdown. New: runs + audits temporal slice. **Net: ~3/4 V26 KPI signals retained, in flat black-white styling.**
- ❌ **V26 Closed-Loop coverage strip (8 KPIs) — entirely missing.** No Evidence/Lifecycle/Brand DNA/DG/Funnel/Reality/GEO/Learning coverage anywhere on the home.
- ❌ Pillar bars (`#pillar-bars`) — entirely missing on home. Per-client PillarRadialChart exists, but no fleet-aggregate view.
- ❌ Priority distribution bars (`#priority-bars`) — entirely missing.
- ❌ Business type breakdown table (`#business-table`) — entirely missing.
- ❌ Page type breakdown table (`#pagetype-table`) — entirely missing.
- ❌ Critical clients tab (top 20 P0) — entirely missing. FleetPanel does have a "P0 first" sort, but it's a side-panel list with no grid view.
- ❌ Pulsing-red dot for P0-critical client cards — missing.
- ❌ The 4-tab dashboard interaction model — replaced with a 2-column layout (fleet sidebar + selected-client detail).

**Gap severity: HIGH.** The dashboard is the *first impression* and >70 % of the V26 data signals are gone. Mathis sees ~28 % of what V26 showed.

---

### Pane 2 — Growth Audit (V26 `pane-audit`, L975-1005 + drill-down L1914-2577)

**V26 features inventoried**:

#### List view (`#audit-list-view`)
- Section head "Growth Audit · Tous tes audits CRO · X clients · Y pages · clique un client pour ses recos"
- **`+ Lancer un nouvel audit` CTA** opening `modal-new-audit` (URL input + "Éclaireur LLM / multi-state capture / OCR cross-check / phantom filter / scent trail" preset pills + cost+time estimate + simulated run animation L3280-3311)
- **4 filter controls** (`.toolbar`) :
  - text search input (filters on name/id/url/business_type/role)
  - business_type select
  - **panel role select** (Client GS / Client à valider / Golden ref / Benchmark / Choix Mathis / Supplément / Runtime V26)
  - sort select (P0 desc / score asc / score desc / name / recent)
- **`#audit-clients-grid`** — auto-fill grid of `client-card`s, 280px min, each card shows:
  - name (Cormorant italic, 1.05rem)
  - 3 pills (business type · panel role color-coded · n_pages)
  - large gradient score value + "/100 · N recos"
  - progress bar (gradient fill = scoreColor(pct))
  - `⚡ N P0 / N P1` micro-stats + URL preview right-aligned
  - **pulsing red dot if `p0 > 3`** (`.client-card--critical`)
  - hover lifts the card with gold border

#### Client drill-down (`#audit-client-view`, hydrated by `openClient()`)
- Back-button (← Retour à la liste clients)
- **`client-hero`** card with linear-gradient gold→indigo background, 2rem italic name, 4 pills (business / role / pages / recos) + URL link, and **5 KPI cards** : Score moyen (gradient color) · P0 (red if any) · P1 · P2 · Scent trail (verdict + percentage)
- **`#v26-panels`** slot (hydrated async via `renderV26Panels` L1825-1903) — renders Brand DNA / GEO / Reality / Multi-judge / Evidence Ledger / Design Grammar status cards + palette swatches + voice tokens
- **`.page-tabs`** strip — one tab per audited page-type (each tab shows score + ⚡p0 badge); **🌊 Tunnel tab** if `canonical_tunnel` exists with merge convergence indicator (↗) on LP tabs that funnel into a canonical
- **`renderPageAudit()`** — see Audit Detail per page below
- **`renderTunnelView()`** (L2097-2210) — canonical tunnel view: consolidated dedup recos across merging pages, top-50 recos with priority+ICE+criterion, per-step audit with friction_form / progress_visible / cognitive_load / micro_reassurance signals

#### Per-page audit view (`renderPageAudit` L2212-2397)
- Optional converged-LP notice ("↗ LP qui redirige vers le tunnel principal au step X. N recos doublonnées retirées.")
- **`#flow-panel-slot`** — async-loaded funnel V24 steps panel (`renderFlowPanel` L1989-2094) with horizontal scroll of step cards, each showing: step number badge, label, pattern, exec ✓/✗, screenshot image with bbox crop, action + value, DOM widget signals (💳 paiement, iframe Stripe, listbox, calendrier, cgv checkboxes)
- **3-column header**: Screenshot card / Quality card / Pillars card
  - Screenshot card : viewport toggle 💻/📱, utility banner row, primary CTA row, then the actual screenshot iframe (max-height 520px scroll)
  - Quality card : large italic gradient `Score%` value + 3 quality metrics (Capture confidence · Overrides · Rescues) + OCR flag pills
  - Pillars card : 6 pillar bars with continuous-HSL fill + score / max display + KILLER badge for failing pillars
- **Recommandations strip** : badge count cluster + P0/P1/P2/P3 totals + cluster-badge "⚡ N clusters"
- **Reco groups by priority** (L2380-2392) — for each of P0/P1/P2/P3: colored dot + group title + count, then each reco rendered via `renderRecoCard` (L2455-2577) :
  - **Bbox-overlay screenshot crop** (`screenshot-crop` element with `transform: scale(0.4)` + `object-position` shift + red-bordered highlight rectangles at `(x,y,w,h)` from `r.crops[viewport].highlights`)
  - Cluster banner if `r.is_cluster` listing covered criteria
  - **3-tab synthesis** (Problème / Action / Pourquoi) — clickable tabs with first-sentence summary visible collapsed, full text expanded
  - Priority pill + ICE score pill + lifecycle pill (`.lifecycle-pill--implemented/won/lost/archived`) + evidence pill (📜 N preuves)
  - Footer : effort hours · expected lift · notes tooltip · feedback ✓/✗ buttons

**Next.js equivalent**:
- `/audits` (`app/audits/page.tsx`) — just a `ClientPicker` + placeholder Card. No filters, no role select, no grid of cards, no sort, no modal.
- `/audits/[clientSlug]` (`app/audits/[clientSlug]/page.tsx`) — V3.2.1-rich view with PageTypesTabs / ConvergedNotice / PillarsSummary / AuditQualityIndicator / RichRecoCard (top-3 expanded per audit).
- `/audits/[clientSlug]/[auditId]` (`app/audits/[clientSlug]/[auditId]/page.tsx`) — single audit detail with `AuditDetailFull` + `AuditScreenshotsPanel` + `RichRecoCard` (top-5 expanded).
- `/recos/[clientSlug]` (`app/recos/[clientSlug]/page.tsx`) — flat list with `RecoList`.

**Status**:
- ⚠️ List view: **no `+ Lancer audit` CTA from the list page** (the modal `CreateAuditTrigger` only renders on `/clients/[slug]`, not on `/audits`). **No simulated audit progress modal animation.**
- ❌ Filter set incomplete: `/clients` has q + category + score min/max + sort (4 filters), but `/audits` has just the ClientPicker. No `panel_role` filter on either. Sort options reduced to name/score/last-audit.
- ❌ V26 client cards (large gradient score + pulsing red P0 dot + pill cluster + URL preview) — replaced by `.gc-clients-table__row` flat list with `name | category | score | counts` columns.
- ❌ `client-hero` block (gradient gold→indigo backdrop, 2rem italic name, 5-KPI strip with scent trail KPI) — partially replaced by `ClientHeroDetail` + KpiCards on `/clients/[slug]`. **Scent trail KPI missing entirely.**
- ❌ `#v26-panels` per-client coverage block (Evidence + Reality + Multi-judge + GEO + Brand DNA palette + Voice tokens summary) — **entirely missing** as a per-client surface.
- ❌ Page tabs with score + ⚡p0 badge + converged ↗ indicator — replaced by `PageTypesTabs` (different shape, no per-tab score badge).
- ❌ **🌊 Canonical tunnel tab + tunnel deduplication view + per-step audit (friction_form / cognitive_load) — entirely missing.** No `canonical_tunnel` concept anywhere in the Next.js codebase (grep confirms).
- ⚠️ Per-page audit header: 3-column layout (screenshot | quality | pillars). Next.js `AuditDetailFull` renders 2-column (scores+recos | screenshots panel). **Score quality (capture confidence, overrides, rescues) — missing.** Mobile/desktop viewport toggle — missing.
- ❌ Per-reco bbox screenshot crop with red highlight rectangles — **missing**. `RichRecoCard` shows reco_text + anti-patterns sections only.
- ❌ 3-tab synthesis (Problème / Action / Pourquoi) — replaced by AntiPatternSection with "Pourquoi / Comment faire". The cleaner V26 3-tab pattern is gone.
- ❌ Lifecycle pill (`.lifecycle-pill--implemented/won/lost/archived`) — missing. Pill set is just priority+severity+pillar+criterion_id.
- ❌ Evidence pill (📜 N preuves count) — missing.
- ❌ Feedback ✓/✗ buttons on recos — missing.
- ❌ Funnel steps V24 panel (horizontal-scroll step cards with screenshots + DOM signal pills) — **entirely missing**. The `/funnel/[clientSlug]` route exists but renders an entirely different visualization (`FunnelStepsViz` + `FunnelDropOffChart` 5-step waterfall from `brand_dna_json.funnel` or audit-derived estimate) — none of the captured-flow screenshots, exec results, payment-iframe detection, vision pattern badges.
- ⚠️ Recos rendering: priority groups (P0/P1/P2/P3) — kept but ICE score not shown, criterion_id pill shown raw (e.g. "hero_01") not as label "Titre principal". V26 has a 51-entry `CRIT_NAMES_V21` map (L2416-2442) translating crit IDs to readable French labels. Next.js doesn't have this mapping (`grep -r 'CRIT_NAMES' webapp/` → nothing).

**Gap severity: HIGH.** Growth Audit is the most-loaded V26 surface and the Next.js port is missing ~60-65 % of the depth. The reco card especially loses its evidence-trail signature (bbox highlights, lifecycle, ICE, evidence).

---

### Pane 3 — Scent Trail (V26 `pane-scent`, L1008-1037 + JS L2580-2663)

**V26 features inventoried**:
- Section head "Scent Trail · Continuité cross-page ad→LP→PDP→checkout · vocabulaire + offres + persona — concept doctrine V19, toujours actif V26"
- **4 KPIs** : Score fleet moyen (avg of `client.scent_trail.overall_scent_score`) · 🟢 Strong continuity count (≥70 %) · 🟡 Partial breaks count (40–70 %) · 🔴 Severe breaks count (<40 %)
- **Per-client scent diagram** (`#scent-diagram`) — visual flow of pages connected by arrows with continuity score per transition (`.scent-arrow__score--strong/partial/broken`)
- **Breaks list** (`#scent-breaks`) — for each transition with `breaks`, a card listing the rupture reasons
- **Fleet scent table** — sortable list of clients with: name · business · n_transitions · score · verdict pill

**Next.js equivalent**: **none**.

**Status**:
- ❌ No route `/scent`, no `<ScentTrail>` component, no Supabase query for scent data, no UI exposure of `client.scent_trail.*` fields. `grep -r 'scent' webapp/` returns nothing relevant.

**Gap severity: HIGH (entire pane missing).** This is one of the V19+ doctrine signatures Mathis explicitly cares about (cross-page ad→LP→checkout continuity). The data exists in `growth_audit_data.js` (`scent_trail` object per client) but is not migrated to Supabase or exposed in the UI.

---

### Pane 4 — Brand DNA (V26 `pane-branddna`, L1060-1072 + JS L2713-2837)

**V26 features inventoried**:
- Section head with V29 badge + sub explaining Phase 1 Python (Pillow KMeans + Playwright getComputedStyle, 80% deterministic) + Phase 2 LLM Vision (voice + image_direction + asset_rules, 20%)
- **Client selector** (`#branddna-client-select`) — eligible clients with `v26.brand_dna`
- **4 KPIs** : Fleet panel · Brand DNA extraits (coverage %) · Phase 1 only · Phase 2 LLM
- **Client viewer** (`renderBrandDnaFor` L2741-2836) — when a client is selected:
  - Identity card : brand · catégorie · market position · audience · confidence %
  - **Colors card** (`.card--wide`) — Primary / Secondary / Neutrals / Semantic color rows with swatches (24px squares with hex code overlaid)
  - **Typography card** — heading / body / scale / line-height rows, each rendered in its actual font family
  - **Spacing/Shape/Depth/Texture/Motion card** — flat token table
  - **Voice tokens card** (`.card--wide`) — tone array · forbidden words · CTA verbs · sentence rhythm
  - **Asset rules card** (`.card--wide`) — photo style · lighting · composition · do_not_use

**Next.js equivalent**: `/clients/[slug]/dna` (`app/clients/[slug]/dna/page.tsx`).

**Status**:
- ⚠️ Per-client viewer exists with `DnaSwatchesGrid` + `DnaTypographyPreview` + `DnaVoicePanel` + `DnaPersonaPanel` + optional `AuraTokensCard` (V30 sidecar). 5-card layout: Identity + Colors + Voice + Typography + Persona — partially mirrors V26 but **lacks Spacing/Shape/Depth/Texture/Motion** and **lacks Asset rules** sections.
- ❌ **No fleet-level Brand DNA pane.** V26's 4 KPIs (Phase 1 / Phase 2 / coverage %) + client selector — entirely missing as an aggregator. You can only get DNA per client by navigating to `/clients/[slug]/dna`. There is no overview of which clients have DNA, which are Phase 1 vs Phase 2, what the fleet coverage is.
- ❌ The Cormorant Garamond serif headlines + gold-tinted card chrome (which make the DNA viewer look "premium") — gone.

**Gap severity: MEDIUM.** Core data is exposed per-client; fleet aggregator is missing.

---

### Pane 5 — GSG / Design Grammar (V26 `pane-gsg`, L1040-1057 + JS L3067-3245)

**V26 features inventoried**:
- Section head "GSG — Design Grammar V30 · Brand DNA (V29) → Design Grammar déterministe (V30) · 7 fichiers générés par client : tokens.css · component_grammar · section_grammar · composition_rules · brand_forbidden_patterns · quality_gates"
- **Client selector** (`#gsg-client-select`) with 🧬/📐 icons indicating which artefacts exist
- **4 KPIs** : Fleet panel · Brand DNA (coverage % · V29) · Design Grammar (coverage % · V30) · Output déterministe (7)
- **Client viewer** (`renderGSGFor` L3099-3244) :
  - Brand DNA Identity card
  - Palette card with Primary/Secondary/Neutrals/Semantic
  - Typography card (rendered in actual font family)
  - Spacing/Shape card
  - Motion card
  - Voice tokens card
  - **Design Grammar V30 section** (when `dg` exists):
    - `tokens.css` viewer (preformatted, first 1800 chars)
    - `component_grammar` list of keys + truncated values
    - `section_grammar` list of keys + truncated values
    - `composition_rules` mini-JSON viewer
    - **🚫 `brand_forbidden_patterns`** list (anti-IA-slop · anti-générique, top 12)
    - **✅ `quality_gates`** list (checks auto avant ship, top 12)

**Next.js equivalent**: `/gsg` (`app/gsg/page.tsx`) — **completely different concern.**

**Status**:
- ❌ **The Next.js `/gsg` is a "GSG Handoff" page**: deterministic JSON brief builder (5 modes: Complete / Replace / Extend / Elevate / Genesis), copy-brief button, iframe preview of demo HTML files from `deliverables/gsg_demo/`. This is V27.2-G handoff plumbing — **not the V26 Design Grammar viewer**.
- ❌ No fleet-level Design Grammar pane (4 KPIs · client selector).
- ❌ No per-client Design Grammar viewer (tokens.css, component_grammar, section_grammar, composition_rules, brand_forbidden_patterns, quality_gates) — these 7 artefacts are completely absent from any UI surface.
- ❌ The V30 Design Grammar concept is exposed only as a sidecar (`_aura_<slug>.json`) loaded by `lib/aura-fs.ts` and shown as a 1-card flat key-value list at the bottom of `/clients/[slug]/dna`. **None of the rich V30 structure is visible.**

**Gap severity: HIGH.** The "GSG" surface in Next.js is *a completely different feature* than V26 GSG. The V26 surface (Design Grammar viewer) doesn't exist. The Next.js `/gsg` is for a use-case that V26 didn't really expose — copying briefs out-of-band for a yet-to-be-built FastAPI service.

---

### Pane 6 — Reality Layer (V26 `pane-reality`, L1075-1083 + JS L2840-2891)

**V26 features inventoried**:
- Section head with V26.C badge + sub explaining "Connecteurs analytics disponibles, mais le panneau affiche uniquement les outputs disque réels"
- **4 KPIs** : Connecteurs disponibles (5) · Pages avec données (count/total) · Statut runtime · Pilote candidat ("Kaiju")
- **5 connector cards** : Catchr (GA4) · Meta Marketing API · Google Ads API · Shopify · Microsoft Clarity. Each card shows: name · description · env var · script path · status (currently `inactive · no runtime output`)
- **Activation pilote** card with `.env` echo commands and `python3 ... reality_layer/orchestrator.py --client kaiju` runbook

**Next.js equivalent**: `/reality` (`app/reality/page.tsx`) + `/reality/[clientSlug]` (`app/reality/[clientSlug]/page.tsx`).

**Status**:
- ⚠️ Reality fleet listing exists but reframed: lists candidate clients (Supabase + filesystem + 2 pilote hints "weglot", "japhy") with credentials report and latest snapshot date. Per-client deep-dive at `/reality/[clientSlug]`.
- ❌ **Per-connector card grid (5 connectors with env var + script path) — missing from the index page.** Only mentioned in a "How to wire a client" 3-step ol at the bottom.
- ⚠️ Pilote candidat "Kaiju" — V26 hints. Next.js uses "weglot" and "japhy". Drift.
- ⚠️ Module status colored badge — Next.js uses `Pill tone="green/amber"` with `configured/total` count. Less doctrine-feel than V26 4-KPI status grid.

**Gap severity: MEDIUM.** The data plane is there; the UI surface is more administrative than V26's "5 connectors at a glance" observatory feel.

---

### Pane 7 — Experiments (V26 `pane-experiments`, L1086-1149 + JS L2894-2944)

**V26 features inventoried**:
- Section head with V27 badge + sub explaining "Sample size calculator (two-sample proportion z-test) + guardrails business + ramp-up + kill switches"
- **Sample size calculator card** (`.card--wide`) — 4 inputs (baseline %, lift %, alpha, power) + computed result: total sample size + per-variant + traffic-to-time estimates (14j / 21j / 28j) + the full math (Z_α/2, Z_β, p_bar). This is **actual JS implementing the two-sample proportion z-test** (`ppf()` Beasley-Springer-Moro inverse normal CDF L2901-2911, full computation L2895-2937).
- **Guardrails default card** — CPL drift max +20%, ROAS min −15%, LTV monitor 14d, bounce ceiling +10pp, exit floor −5pp
- **Ramp-up phases card** — Smoke 5%/24h, canary 25%/3d, partial 50%/7d, full 100%
- **Kill switches card** — CR drop >30% / revenue drop >25% / bounce spike >40% / server errors >1% with rollback windows

**Next.js equivalent**: **none.**

**Status**:
- ❌ No `/experiments` route, no sample-size calculator component, no guardrails / ramp-up / kill-switch UI. `grep -ri 'experiment' webapp/apps/shell/` only matches the literal word in `runs.type = 'experiment'` for the Run table — but no UI.

**Gap severity: HIGH (entire pane missing).** V27 is one of the seven V26 piliers and one of the few panes where the V26 webapp is **actually interactive** (not just a viewer). Mathis has lost a working statistical-test mini-tool.

---

### Pane 8 — GEO Monitor (V26 `pane-geo`, L1152-1161 + JS L2947-3001)

**V26 features inventoried**:
- Section head with V31+ badge + sub "Generative Engine Optimization · affichage des seuls clients avec `geo_audit.json` ou `geo_monitor_cache.json`. Coverage partiel tant que les engines ne tournent pas sur la fleet."
- **Client selector** (`#geo-client-select`) — eligible clients with `v26.geo_audit || v26.geo_monitor`
- **Per-client viewer** : engine cards (one per engine tested — anthropic / openai / perplexity), each showing presence_pct with color (green ≥60 / warn ≥30 / bad <30), n_queries tested. Plus a "Query bank tested" card listing the top 20 queries.
- Activation runbook in empty state : `echo OPENAI_API_KEY... `+ `python3 geo_readiness_monitor.py --client kaiju --engines anthropic,openai,perplexity`

**Next.js equivalent**: **none.**

**Status**:
- ❌ No `/geo` route, no GEO-related component, no Supabase column or query for `geo_audit_json`. `grep -ri 'geo_audit\|geo_monitor\|geo_readiness' webapp/` → nothing in app code (only in `.next` build artefacts).

**Gap severity: HIGH (entire pane missing).** GEO Monitor is on the manifest §12 changelog as V31+ delivered. The data exists for some clients (per `growth_audit_data.js`) but is not in Supabase / not surfaced.

---

### Pane 9 — Learning Layer (V26 `pane-learning`, L1164-1239 + JS L3004-3064)

**V26 features inventoried**:
- Section head with V28 + V26 badges + sub
- **4 KPIs** : Recos fleet · Evidence trail · Learning proposals (count with status color) · Experiment runs (count with status color)
- **Reco Lifecycle distribution card** (`.card--wide`) — V26.B 13-state bars (`generated` → `reviewed` → `accepted` → `ticket_created` → `implemented` → `qa_passed` → `experiment_started` → `measured` → `won` / `lost` / `inconclusive` → `learning_applied` / `archived`), each with proportional fill + count
- **Evidence Ledger card** (`.card--half`) — V26.A evidence count, distributed across N clients, schema description
- **Multi-judge disagreement card** (`.card--half`) — V26.D status (currently "Aucun disagreement loggé")
- **Experiment Engine summary card** — sample size config, default guardrails, ramp-up, kill switches
- **Bayesian priors card** — "Phase d'apprentissage — première update doctrine prévue après 30 expérimentations mesurées"
- **Doctrine evolution timeline card** — chronological changelog V13 → V31+ with date-prefixed entries

**Next.js equivalent**: `/learning` (`app/learning/page.tsx`) + `/learning/[proposalId]` (proposal detail).

**Status**:
- ⚠️ Completely reframed as a "Learning Lab" with 2 surfaces:
  - **Vote queue** (`ProposalQueue`) — 4-button vote (accept / reject / refine / defer) with optimistic UI
  - **Browse history** (`ProposalList`) — search/filter for audit-trail
- ❌ **Reco Lifecycle 13-state distribution — missing entirely.** No bars, no visualisation of where the fleet's recos sit in the lifecycle.
- ❌ Evidence Ledger fleet count — missing.
- ❌ Multi-judge disagreement panel — missing.
- ❌ Experiment Engine summary — missing.
- ❌ Bayesian priors panel — missing.
- ❌ Doctrine evolution timeline (V13 → V31+ changelog) — missing.

**Gap severity: HIGH.** The Next.js `/learning` is a *useful new feature* (vote queue) but it replaced — rather than complemented — the fleet observatory view. ~80 % of the original Learning pane signals are gone.

---

### Pane 10 — Doctrine (V26 `pane-doctrine`, L1242-1346 + JS L2666-2711)

**V26 features inventoried**:
- Section head "Doctrine V26 · Closed-Loop Architecture · 7 piliers V26 + doctrine v3.2 (47 critères · 6 blocs scoring) + closed loop"
- **Closed Loop Architecture card** — 6-step labeled flow CAPTURE → PERCEPTION → RECO+EVIDENCE → VALIDATION → EXPERIMENT → LEARNING → ↑ back to CAPTURE, each step with description + color-coded left-border
- **7 piliers V26 card** (`.card--half`) — table of pillar status (V26.A active / V26.B 13 états / V26.C code prêt · pas activé / V26.D trigger sur disagreement / V27 calculator + guardrails / V28 après 30 expé / V31+ env vars OPENAI/PERPLEXITY)
- **Brand DNA + Design Grammar card** (`.card--half`) — V29 / V30 / V25 / V24 / V23 / V22 / V21 status table
- **🧬 Our own Brand DNA · Growth Society** dogfood card with **applied tokens** : identity row, dna-colors (primary / secondary / neutrals / semantic with swatches), dna-typo (heading / body / mono in their actual font), dna-voice (tone codes / forbidden words / CTA verbs). This is the *eat-your-own-dogfood* card — V26 tokens shown live, applied to the webapp itself.
- **📚 Doctrine v3.2 — 47 critères × 6 blocs** card — grid of 6 doctrine blocs (hero / persuasion / ux / coherence / psycho / tech) each rendered as a `.doctrine-bloc` with number badge + title + crits range + max points + description
- **Doctrine-first arbitrage table** — 8 hardcoded rules (hero_h1_word_count floor/ceiling, hero_subtitle floor, cta_count_in_fold, social_proof_signals, h1_count ≤1, funnel_steps 1-10, effort_hours 1-80)

**Next.js equivalent**: `/doctrine` (`app/doctrine/page.tsx`).

**Status**:
- ⚠️ V1 stub : renders the 6 + 1 piliers as `.gc-doctrine-bloc` cards (Hero / Persuasion / UX / Coherence / Psycho / Tech / Utility Elements V3.3). Each card shows: block number, pillar, # critères, max points, hint. Plus a "Notes V3.2.1 → V3.3" card with pondération info.
- ❌ Closed Loop Architecture 6-step flow diagram — **missing**.
- ❌ 7 piliers V26 status table (V26.A/B/C/D/V27/V28/V31+) — **missing**.
- ❌ Brand DNA + Design Grammar status table (V29/V30/V25/V24/V23/V22/V21) — **missing**.
- ❌ **🧬 Growth Society dogfood card with applied tokens — completely missing.** This was the visceral proof "we use our own tooling" — gone.
- ❌ Doctrine-first arbitrage table (floors/ceilings) — **missing**.

**Gap severity: HIGH.** The Doctrine pane in V26 is the *narrative spine* — it shows the whole closed-loop architecture as one page. The Next.js stub keeps only the 6-block scoring list. ~80 % of the signal is lost.

---

### Pane 11 — Settings (V26 `pane-settings`, L1349-1411)

**V26 features inventoried**:
- 🔑 API Keys section : Anthropic API Key field (masked) + "Regénérer" button
- 🎨 Préférences V19 section : 5 toggle rows (Éclaireur LLM auto · OCR cross-check obligatoire · Multi-state capture · Doctrine-first arbitrage · Phantom filter déterministe), each with label + description + toggle switch
- Footer note "GrowthCRO V26.0.0 · doctrine v3.2 · closed-loop · fleet N clients · made in 🇫🇷 Growth Society"

**Next.js equivalent**: `/settings` (`app/settings/page.tsx`) with 4 tabs.

**Status**:
- ✅ More feature-complete than V26 (auth-gated). 4 tabs:
  - **Account** — current user email + last sign-in
  - **Team** — org members list with roles
  - **Usage** — counts (clients, audits, recos, runs this month)
  - **API** — Supabase URL + anon key + project ref
- ❌ V19 doctrine toggles (Éclaireur LLM / OCR cross-check / Multi-state capture / Doctrine-first arbitrage / Phantom filter) — **completely absent**. These were the *runtime configuration knobs* exposing what the pipeline does. Gone.
- ❌ Anthropic API Key management — absent (replaced by Supabase config).

**Gap severity: LOW-MEDIUM.** The Next.js Settings is *better-engineered* (auth, multi-tenant, real RBAC). But it's lost the V19 doctrine-toggles narrative.

---

## Cross-cutting gaps (global chrome)

| V26 feature | Source | Next.js status |
|---|---|---|
| **Sticky top header (68px)** with breadcrumb + search + notification icon + "+ Nouvel audit" CTA + avatar | L884-896 | ❌ **Missing entirely.** Next.js puts page-specific topbars inside each page, no global header row. |
| **Global search input** "Chercher un client, une page, une reco..." with Enter-key fuzzy match on `client.name/id` jumping to drill-down | L888-890 + L3335-3351 | ❌ **Missing.** No `Cmd-K` palette, no header search. (`FleetPanel` search is scoped to fleet only.) |
| **Breadcrumb dynamic** (`Dashboard` / `Growth Audit › Kaiju` / `Audit › ...`) updated by `updateBreadcrumb()` | L885-887 + L3269 | ⚠️ Partial — `Breadcrumbs.tsx` exists, derived from `usePathname()`, but not actually rendered anywhere in `app/` (it's exported but unused). Topbar text is hardcoded per-page. |
| **Sidebar 240px** with brand logo (italic Cormorant gold gradient), 11 nav items with emoji icons + badges (`audit-count` / `branddna-count` / V26.C / V27 / V31), footer with fleet stats | L860-882 | ⚠️ Sidebar exists (`Sidebar.tsx`), 280px width, 4 groups (Pipeline / Studio / Agency Tools / Admin) with 11 items. **But: no emoji icons, no V26.C / V27 / V31 badges, no audit-count badge, no italic gold brand text, no fleet-stats footer.** Items use `hint` text instead of count badges. |
| **Starfield canvas** 4-layer parallax animated stars + grain texture overlay | L120-135 + L856 + L3365+ | ❌ **Missing entirely.** `.gc-grain` exists but no CSS rule + no canvas anywhere. |
| **Footer info** "X clients · Y pages" + "GrowthCRO V26.0.0 · doctrine v3.2 · closed-loop · made in 🇫🇷" | L878-881 + L1410 | ❌ Missing. |
| **Modals** : "Nouvel audit" (URL input + V19 preset pills + cost+time estimate + simulated 12-step run animation) + "Audit progress" (live progress bar + log stream) | L1417-1483 + L3271-3311 | ⚠️ `CreateAuditModal` exists (admin-only, only on `/clients/[slug]`) — different shape, no simulated animation, no V19 preset display, no cost preview. |
| **Keyboard shortcuts** : Escape closes modal, Enter on search opens client | L3331-3340 | ⚠️ Partial — modal Escape works via `<dialog>` semantics in `Modal.tsx`. No global search Enter binding. |
| **Avatar badge (top right)** "MF" gradient circle | L893-894 | ❌ Missing. Replaced by sidebar "Session · email · Déconnexion" form. |
| **Notifications icon** 🔔 | L892 | ❌ Missing. |

---

## Coverage scorecard

Approximate LOC counts. V26 `*.tsx` doesn't exist (it's a single HTML file), so V26 numbers are **inline JS + DOM markup contributing to each pane**.

| Pane | V26 source LOC (markup + JS) | Next.js LOC | Coverage % |
|---|---:|---:|---:|
| Dashboard | ~245 (L901-972 + L1590-1715) | ~135 (`page.tsx` + CC components) | ~30 % |
| Growth Audit (list+drill+page) | ~870 (L975-1005 + L1717-2577) | ~620 (audits/[c]/* + RichRecoCard + score-utils) | ~45 % |
| Scent Trail | ~115 (L1008-1037 + L2580-2663) | 0 | **0 %** |
| Brand DNA | ~135 (L1060-1072 + L2713-2837) | ~330 (dna page + 4 panels) | ~75 % (per-client only, no fleet) |
| GSG / Design Grammar | ~205 (L1040-1057 + L3067-3245) | ~225 (gsg page) **but different concern** | ~10 % (V26's actual DG view is missing) |
| Reality Layer | ~110 (L1075-1083 + L2840-2891) | ~170 (reality/* pages) | ~55 % |
| Experiments V27 | ~165 (L1086-1149 + L2894-2944) | 0 | **0 %** |
| GEO Monitor V31+ | ~80 (L1152-1161 + L2947-3001) | 0 | **0 %** |
| Learning Layer | ~165 (L1164-1239 + L3004-3064) | ~290 (learning/* + 5 components) | ~30 % (reframed) |
| Doctrine | ~155 (L1242-1346 + L2666-2711) | ~155 (`doctrine/page.tsx`) | ~25 % |
| Settings | ~65 (L1349-1410) | ~250 (settings/* + 4 tabs) | 110 % (more features, but lost V19 toggles) |
| **TOTAL** | **~2310 V26** | **~2175 Next.js** | **~28 %** weighted by feature signal |

LOC parity is misleading: Next.js spends LOC on auth + Supabase plumbing + TS types + admin RBAC, V26 spends LOC on rich visualisation + animations + per-client viewers. **The Next.js has comparable code volume but much shallower feature coverage.**

---

## Why the Next.js looks "nothing like" V26

Three structural reasons.

**1. The design DNA was never ported.** The V26 doctrine was explicit: stratospheric observatory · Alaska deep night · Cormorant Garamond editorial serif · sunset gold KPI gradient · glass cards with gold-tinted borders · golden-ratio modular spacing · multi-easing animation system. The Next.js shell starts from a generic "dark IDE" baseline (Inter only, flat panels, `#121823 + #273246 borders`, `var(--gc-line)`, no animations beyond `transition: 0.15s ease`). The 9 design tokens in `packages/ui/src/styles.css` are a reductive caricature of the 35+ V26 tokens. There is **no `--gc-font-display` (Cormorant) variable, no glass-border-strong variant, no scoreColor() function for continuous HSL gradient**. The Next.js was designed by a different sensibility — pragmatic engineering rather than premium product — and that shows on every screen.

**2. The closed-loop narrative was lost.** V26's home was *the Closed-Loop Observatory*: 8 module-status KPIs telling you exactly which of the 7 piliers are active across the fleet, 6 fleet pillar bars showing where the agency's average is on each doctrine pillar, a business breakdown, a page-type breakdown, a top-20 critical clients grid. **All of these are missing.** The Next.js home is `KPIs + FleetPanel + ClientHeroDetail` — a *client-picker* shaped like a 2-column ops view. Useful, but it doesn't tell the agency story. The 7 piliers (Evidence Ledger / Reco Lifecycle / Reality / Multi-judge / Experiments / Learning / GEO), the doctrine-first arbitrage table, the 13-state reco lifecycle, the Bayesian priors panel, the multi-judge disagreement panel — none of these exist in the Next.js port. Mathis is staring at a thin layer over Supabase clients/audits/recos tables, not the audit→action→measure→learn→generate→monitor observatory.

**3. The high-signal per-page visualisations were stripped.** The per-page audit drill-down in V26 was the *richest* surface: dual-viewport (desktop/mobile) toggle, screenshot with bbox-overlay crops per reco, 3-tab synthesis (Problème / Action / Pourquoi), funnel V24 steps panel with payment-iframe detection and DOM signal pills, canonical-tunnel deduplication, per-step audit with friction_form / cognitive_load / progress_visible signals, lifecycle pills, evidence pills, ICE-score-sorted recos, criterion-id-to-French-label translation. The Next.js port keeps the *priority groups* and *the pillar bars* and that's it. Recos render with priority+severity+pillar+criterion-id pills (raw `hero_01` instead of "Titre principal") and an anti-patterns Pourquoi/Comment-faire block. This is *80 % data, 20 % presentation* — V26 was *80 % presentation, 20 % data*, by design, because Mathis wanted **decision quality**, not data dumps.

---

## Mega plan — surgical action items

Sequenced as 7 sprint-sized chunks (each 2-4 days). Reach **~65 % feature parity + ~70 % visual DNA parity** by end of Sprint 5; the remaining sprints are V26+ improvements.

### Sprint A1 — Visual DNA restoration (3 days, must-do P0)

The single most-impactful change. Touches *every page* in the app.

1. **Add the V26 token set to `packages/ui/src/styles.css`** as `--gc-display` / `--gc-mono` / `--gc-night-*` / `--gc-star-*` / `--gc-glass*` / `--gc-aurora*` / `--gc-gold-*` (mirroring V26 L17-78). Keep the existing `--gc-line` etc. for backward compat (they map onto the new tokens).
2. **Load Cormorant Garamond + JetBrains Mono via `next/font/google`** in `layout.tsx` next to Inter. Expose as `--gc-font-display` + `--gc-font-mono`.
3. **Reapply glass card styling** to `.gc-panel` : `backdrop-filter: blur(22px) saturate(160%)`, gold-tinted border `rgba(232,200,114,0.12)`, double box-shadow inset+outer, the gradient pseudo-element overlay.
4. **Reapply KPI value gradient** to `.gc-kpi b` : italic Cormorant Garamond, linear-gradient text `#fbfaf5 → #e8c872 → #d4a945`, drop-shadow glow.
5. **Add the starfield canvas** : copy the IIFE engine from V26 L3365+ verbatim into `components/Starfield.tsx` (`use client`), mount it once in `layout.tsx` between `<body>` and the page tree. Keep `prefers-reduced-motion` respect.
6. **Add the grain CSS rule** that backs `<div class="gc-grain">` (V26 L131-135 verbatim).
7. **Add `scoreColor(pct)` helper** in `packages/ui/src/components/` (HSL gradient red 0° → yellow 60° → green 120°) and use it for every pillar bar fill, KPI score color, client card score color. Replace the binary green/amber/red pill pattern wherever a continuous score lives.

Expected impact: the webapp will *look* like V26 on every existing page even before features are restored.

### Sprint A2 — Dashboard parity (3-4 days, P0)

Touch only `app/page.tsx`, `components/command-center/*`, `packages/data/src/queries/*`.

1. **Add a `loadV26ClosedLoopCoverage()` query** to `packages/data/src/queries/`: returns module status for the 8 V26 modules (Evidence, Lifecycle, Brand DNA, Design Grammar, Funnel, Reality, GEO, Learning). Source: Supabase tables `audits.scores_json` (has evidence + lifecycle counts when populated), `clients.brand_dna_json` (has `brand_dna`, `design_grammar`, `geo_audit`, `reality_layer` sub-objects), and `runs` (for Reality + Experiment counts).
2. **Add `<ClosedLoopCoverageStrip>` component** rendering 8 KPIs in a `.gc-grid-kpi-strip` (icon + label + count/total + status color).
3. **Add `<FleetPillarsBars>` component** rendering 6 pillar bars (Hero/Persuasion/UX/Coherence/Psycho/Tech) with continuous-HSL fill + percentage value. Source: `avgPillarsAcrossAudits()` already exists in `clients/score-utils.ts`, just expand to a fleet aggregate.
4. **Add `<PriorityDistributionBars>` component** : 4 horizontal bars (P0/P1/P2/P3) with proportional fills + counts.
5. **Add `<BusinessTypeTable>` + `<PageTypeTable>` + `<CriticalClientsGrid>`** to back the 3 alternative tabs.
6. **Add `<DashboardTabs>` client-island wrapper** wiring fleet / business / pagetype / critical via URL `?tab=`.
7. Move `<FleetPanel>` + `<ClientHeroDetail>` to a secondary `/fleet` or under the "critical" tab — they shouldn't be the home's main surface.

### Sprint A3 — Growth Audit pane (3-4 days, P0)

1. **Restore the `+ Lancer un nouvel audit` CTA** to the `/audits` list page top-right. Open the existing `CreateAuditModal` but **augment it** with the V19 preset pill row (`Éclaireur LLM · Multi-state capture · OCR cross-check · Phantom filter · Scent trail`) + cost+time hint + the 12-step simulated run animation (`runAuditSim` L3280-3311 verbatim, behind a feature flag).
2. **Add a `panel_role` filter** to `/audits` and `/clients`.
3. **Reshape `/audits` list view** into the V26 `clients-grid` card layout (large gradient score, pulsing-red dot if P0>3, 3 pills, micro-stats footer). Replace `gc-clients-table__row` flat list.
4. **Add the `client-hero` block** to `/clients/[slug]` (gradient backdrop, 2rem italic name, 5-KPI strip including scent trail KPI when data exists).
5. **Add a `v26-panels` section** to `/clients/[slug]` summarizing Evidence count + Reality status + Multi-judge disagreement + GEO score + Brand DNA palette preview + Voice tokens phrase. Single composite component, async-loaded.
6. **Add the `CRIT_NAMES_FR` map** (51 entries from V26 L2416-2442) to `clients/score-utils.ts` and use it in `RichRecoCard` to display "Preuve sociale ATF" instead of "hero_05".
7. **Add the per-page audit dual-viewport toggle** (💻/📱) to `AuditDetailFull`, switching between `screenshots.desktop_full` and `screenshots.mobile_full` from the audit row.
8. **Add the bbox-overlay screenshot crop** to each `RichRecoCard` open state (read `content_json.crops[viewport].highlights`, render scaled image with `object-position` + absolutely-positioned red highlight rectangles per highlight).

### Sprint A4 — Missing-pane revival (4-5 days, P1)

The 3 entirely-missing panes.

1. **`/scent` route + `<ScentTrail>` component** : 4 KPIs (fleet score / strong / partial / broken) + per-client scent diagram (`.scent-page` boxes connected by `.scent-arrow` with score badge) + breaks list + fleet table. Source: needs `client.scent_trail` to be ported to Supabase first (currently only in `growth_audit_data.js`). **Migration sub-task** : add `scent_trail_json jsonb` column on `clients` and backfill from the 12 MB bundle.
2. **`/experiments` route + `<SampleSizeCalculator>` component** : port the V26 calculator verbatim (`ppf()` + `compute()` math). Plus the 3 static cards (Guardrails / Ramp-up / Kill switches). Pure-client component, no DB.
3. **`/geo` route + `<GeoMonitor>` component** : client selector + per-engine cards + query bank list. Source: needs `geo_audit_json jsonb` column on `clients`, backfill from bundle.

### Sprint A5 — Doctrine + Learning + Reality fill-in (3 days, P1)

1. **`/doctrine` upgrade** : add the Closed Loop Architecture 6-step flow diagram (verbatim from V26 L1250-1284) + 7-piliers status table + Brand DNA/Design Grammar status table + **Growth Society dogfood card with applied tokens** (use the new V26 tokens from Sprint A1) + Doctrine-first arbitrage table.
2. **`/learning` upgrade** : keep the ProposalQueue (it's a useful addition), but add above it the **Reco Lifecycle 13-state distribution bars** + **Evidence Ledger fleet count** + **Multi-judge disagreement panel** + **Doctrine evolution timeline card** (chronological changelog).
3. **`/reality` upgrade** : add the 5-connector card grid (Catchr / Meta / Google Ads / Shopify / Clarity) with env var + script path per V26 L2842-2887.

### Sprint A6 — V26 GSG / Design Grammar viewer (2-3 days, P1)

Restore the V26 `pane-gsg` actual functionality (not the V27.2-G handoff that currently lives at `/gsg`).

1. **Move the current `/gsg` to `/gsg/handoff`** (preserve the brief builder).
2. **Build a new `/gsg` (V26 parity)** : client selector + 4 KPIs (Fleet panel / Brand DNA coverage / Design Grammar coverage / 7 outputs) + per-client viewer with all 7 design-grammar artefacts (`tokens.css` preformatted, `component_grammar` list, `section_grammar` list, `composition_rules` JSON, `brand_forbidden_patterns` red-bordered list, `quality_gates` green-bordered list).
3. **Migration sub-task** : add `design_grammar_json jsonb` column on `clients` (or store as `_aura_<slug>.json` sidecars and load via `lib/aura-fs.ts` like the current pattern).

### Sprint A7 — Global chrome (2 days, P2)

1. **Add a sticky top header** (`app/layout.tsx` injected component) with: dynamic breadcrumb (use the already-built `Breadcrumbs.tsx`) + global search input (Cmd+K palette) + notifications icon + `+ Nouvel audit` CTA + avatar/email pill.
2. **Add the 11-item flat sidebar** with V26 emoji icons + V26.C/V27/V31 badges + audit-count badge on Growth Audit + brand-dna-count badge + fleet-stats footer. Replace the current 4-group sidebar — or keep the grouping but make the items match V26's eleven (`dashboard / audit / scent / branddna / gsg / reality / experiments / geo / learning / doctrine / settings`).
3. **Add Cmd+K search palette** with fuzzy match on client name/slug/business_type + Enter to open `/clients/[slug]`. Use `cmdk` package.
4. **Wire `<Breadcrumbs />` into `layout.tsx`** so every page (except `/`) gets it for free.
5. **Add the footer info string** "GrowthCRO V26.0.0 · doctrine v3.2 · closed-loop · fleet N clients · made in 🇫🇷 Growth Society" to the sidebar.

### P3 — V26+ improvements (deferred)

- Convert the sample-size calculator into a *measured* experiment runner (post Reality data wire-up)
- Per-step audit V26.X.5 (friction_form / cognitive_load) — needs the funnel V24 capture data in Supabase
- Live trigger to FastAPI for `+ Nouvel audit` (V2 in GSG manifest)
- PDF export of audit (currently disabled in `AuditDetailFull` recos header)
- Real Anthropic API key rotation UI in Settings (currently it shows Supabase config only)
- Audit-trail / undo on the proposal queue
- Mobile sidebar drawer (currently collapses entirely on <1180px)

---

## Appendix A — Tables of route ↔ pane mapping

| V26 pane | V26 ID | Next.js route | Component(s) | Coverage |
|---|---|---|---|---|
| Dashboard | `pane-dashboard` | `/` | `CommandCenter*` | 30 % |
| Growth Audit (list) | `pane-audit` `#audit-list-view` | `/audits` | `ClientPicker` | 20 % |
| Growth Audit (drill) | `pane-audit` `#audit-client-view` | `/audits/[c]`, `/audits/[c]/[a]`, `/clients/[s]`, `/recos/[s]` | `AuditDetailFull`, `RichRecoCard`, `PageTypesTabs`, … | 45 % |
| Scent Trail | `pane-scent` | — | — | 0 % |
| Brand DNA | `pane-branddna` | `/clients/[s]/dna` | `Dna*Panel`, `DnaSwatchesGrid` | 75 % per-client / 0 % fleet |
| Design Grammar (V30) | `pane-gsg` | — (route `/gsg` is V27.2-G handoff, different concern) | — | 10 % |
| Reality Layer | `pane-reality` | `/reality`, `/reality/[s]` | `RecentRunsTracker` | 55 % |
| Experiments | `pane-experiments` | — | — | 0 % |
| GEO Monitor | `pane-geo` | — | — | 0 % |
| Learning Layer | `pane-learning` | `/learning`, `/learning/[id]` | `Proposal*` | 30 % (reframed) |
| Doctrine | `pane-doctrine` | `/doctrine` | inline `<Pilier>` data | 25 % |
| Settings | `pane-settings` | `/settings` | `*Tab` x 4 | 110 % (lost V19 toggles, gained auth) |

## Appendix B — Files referenced

V26 source : `/Users/mathisfronty/Developer/growth-cro/deliverables/GrowthCRO-V26-WebApp.html` (3666 LOC).
V26 data : `/Users/mathisfronty/Developer/growth-cro/deliverables/growth_audit_data.js` (12 MB, `window.GROWTH_AUDIT_DATA` with keys `meta`, `fleet`, `module_status`, `by_panel_role`, `by_business`, `by_page_type`, `clients`, `_growth_society_dna`).

Next.js shell : `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/`
- Routes : `app/{page,layout,error,loading,global-error}.tsx`, `app/{clients,audits,recos,gsg,reality,learning,doctrine,settings,login,auth,terms,privacy,audit-gads,audit-meta,funnel}/`
- Components : `components/{Sidebar,Breadcrumbs,ViewToolbar,RunsLiveFeed}.tsx`, `components/{audits,clients,command-center,common,dna,funnel,gsg,judges,learning,reality,recos,settings}/`
- Lib : `lib/{aura-fs,auth-role,captures-fs,gsg-api,gsg-brief,gsg-fs,proposals-fs,reality-fs,require-admin,safe-redirect,supabase-server,use-supabase,use-url-state}.ts`
- UI package : `webapp/packages/ui/src/{styles.css, components/*.tsx}`
- Data package : `webapp/packages/data/src/{types.ts, queries/*.ts}`
- Global CSS : `webapp/apps/shell/app/globals.css` (1701 LOC)
