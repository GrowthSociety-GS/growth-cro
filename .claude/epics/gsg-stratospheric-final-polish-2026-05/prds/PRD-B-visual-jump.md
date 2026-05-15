# PRD-B — Visual Jump to Stratospheric

**Sprint 17 / Epic** : gsg-stratospheric-final-polish-2026-05
**Estimated** : 2h

## Problem

V9 is *correct* but not *stratospheric*. Specific complaints from Mathis 2026-05-15:

1. Reason mini-images are 88px tall, illegible
2. No real photos / illustrations — feels AI-generated
3. Redundant English proof strip "111,368+ global brands rely on Weglot to translate their websites" → meaningless to the FR reader, mixes EN+FR
4. Flat surfaces, no textures
5. Some copy phrasings are unclear

## Solution

### B1. Remove the redundant English proof strip

Current code at `page_renderer_orchestrator.py:280` : `{_proof_strip(plan)}` rendered after intro.
The strip pulls 3 facts from `plan.constraints.allowed_facts` — but for Weglot the first two are EN captures and the third is FR brief : **mixed-language + redundant with reason 01**.

Decision : **HIDE for lp_listicle** when the angle already loads the same facts in H1 + reasons. Keep for advertorial / lp_sales where the strip plays a different role.

### B2. New module `moteur_gsg/core/reason_illustration.py`

10 inline-SVG illustrations, each ~280×200 px, line-art editorial style with brand color accents :

| Icon key | Illustration | Reason topic example |
|----------|--------------|---------------------|
| users | Grid of 5×6 monogram circles | "111 368 marques" |
| clock | Clock face with progress arc 1/12 sliced violet | "Setup en 5 minutes" |
| search | URL-tree diagram /fr /en /de with hreflang lines | "SEO multilingue" |
| sparkle | Neural-net node graph with French/English glossary labels | "IA fidèle à la marque" |
| gift | Gift box icon with arrow up + "free" ribbon | "Plan gratuit perpétuel" |
| plug | 8 mini wordmarks WP / Shopify / Webflow / Wix laid in 2×4 grid | "70+ intégrations" |
| globe | Stylized globe (longitude/latitude) with 6 hotspot dots | "110 langues" |
| shield | Pen icon + speech bubble + checkmark | "Révision humaine" |
| star | 3 stacked rating cards (4.8 / 4.9 / 4.9) | "Notes G2 + WP + Trustpilot" |
| trending | Upward chart with milestone dots | "Zéro maintenance" |

Each illustration ≥ 220 px tall on desktop, embedded inline (no external dependency, scales infinitely, themes via `currentColor` / `var(--gsg-primary)`).

### B3. Paper-grain texture overlay

Add to `core/css/base.py` a subtle SVG noise background on `body` :

```css
body::before {
  content: "";
  position: fixed; inset: 0;
  pointer-events: none;
  background-image: url("data:image/svg+xml;utf8,<svg ...turbulence noise...>");
  opacity: 0.04;
  mix-blend-mode: multiply;
  z-index: 9999;
}
```

Editorial paper-grain feel without affecting interactivity.

### B4. Hero editorial details

- Vertical accent line `2px × full-height` on the left edge of the hero (editorial gutter)
- Drop cap on intro paragraph (first letter ~3em, brand color, float left)
- Sub-h1 (italic display, lighter weight, sized between H1 and dek)

### B5. Logos grid : wordmark refinements

Currently `<li>HBO</li><li>Nielsen</li>...` with `opacity: 0.55`. Refinements :
- Increase font-size from 16px to 18px
- Add a vertical separator pipe between names (CSS `::after` content)
- Animate hover : opacity 0.55 → 1.0 + slight slide

## Acceptance

- [ ] `<ul class="proof-strip">` NOT in V10 HTML
- [ ] 10/10 reasons have a `.reason-illustration` SVG (custom per topic) ≥ 220px tall
- [ ] `body::before` paper-grain present
- [ ] V10 Playwright desktop screenshot shows visible textures and lively reason illustrations
- [ ] No reason has a generic SVG icon (the 11 inline icons from Sprint 14 are now only fallback for unknown topics)

## Out of scope

- Real photographs (Unsplash) — V11 / Sprint 18 if Mathis wants
- AI image generation (DALL-E / Midjourney) — out of scope of this codebase
- Custom illustrator-style logos for clients tier-1 (V11)
