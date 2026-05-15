# Epic — Beyond Excellent → Stratospheric (Sprint 18)

**Created** : 2026-05-15
**Status** : 🚀 IN PROGRESS
**Triggered by** : Mathis 2026-05-15 — *"Let's go !"* (continuation after Sprint 17 close)
**Cost target** : ≤ 3h Claude Code wall-clock

## Why this epic exists

Sprint 17 closed with V10 composite_score = 88.2% **Exceptionnel** — but
Mathis's bar is **Stratospheric ≥ 92%**. The gap is concentrated in the
**Humanlike judge** (72.5% Bon) — the sensorial / DA-senior perception
of the page. The Doctrine judge is already at 81.2% Excellent.

## Diagnostic — why Humanlike is at 72.5%

Hypothesis after reviewing the LP-Creator copy + V10 screenshots :

1. **Testimonials use letter monograms** ("É" "M" "D") for avatars —
   feels placeholder-y, not human. Humanlike judges grade sensorial
   richness ; abstract initials cost points.
2. **No editorial typographic devices** — no pull-quotes, no marginalia,
   no drop caps beyond the intro paragraph. Premium magazines
   (NYT / FRR / Stripe Press) interleave visual rhythm devices.
3. **sub-h1 LP-Creator field is parsed away** — V10 has no italic
   subtitle between H1 and dek (regex edge case `**Sub-H1** (italique
   léger)\n> ...`).

## Sprint 18 — single sub-PRD

### [PRD-D — Beyond Excellent](prds/PRD-D-beyond-excellent.md)

5 tactical fixes targeting Humanlike judge :

| Task | Effort | Expected ΔHumanlike |
|------|-------|---------------------|
| T18-1 sub-h1 parser fix | 5 min | +1pt (visible italic display rhythm) |
| T18-2 Real Unsplash testimonial portraits | 30 min | +5pts (sensorial human signal) |
| T18-3 Pull-quote callouts every 3rd reason | 40 min | +3pts (editorial rhythm) |
| T18-4 Hero left accent line + bigger drop cap on intro | 20 min | +1pt (print feel) |
| T18-5 Run V11 + verify composite ≥ 92 | 30 min | — |

**Acceptance gate** : V11 composite_score ≥ 92% → "Stratospheric" tier.

## Out of scope (Sprint 19+)

- Multi-page generation (home + pricing + lp_listicle batch)
- Real Anthropic Skill tool wiring
- A11y audit (axe-core)
- A/B variants

## Index

- [PRD-D — Beyond Excellent](prds/PRD-D-beyond-excellent.md)
