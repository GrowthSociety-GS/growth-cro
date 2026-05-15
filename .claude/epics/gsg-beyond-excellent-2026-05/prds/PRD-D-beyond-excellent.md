# PRD-D — Beyond Excellent

**Sprint 18 / Epic** : gsg-beyond-excellent-2026-05
**Estimated** : 2h

## Goal

Push composite_score from 88.2% Exceptionnel → ≥ 92% Stratospheric.
Focus on Humanlike judge (gap 72.5% Bon).

## Solution

### D1. sub-h1 parser fix

Current regex in `copy_lp_creator_parser._RE_FIELD` matches
`**Label**\s*(?::\s*content|\s*\n>\s*content)`. But LP-Creator format
can have a parenthetical descriptor after the label :

```
**Sub-H1** (italique léger)
> (et pas une agence à 20 000 €)
```

Fix : accept optional `\s*\([^)]*\)` between the closing `**` and the
content. Renderer already supports `<p class="sub-h1">` (Sprint 17).

### D2. Real Unsplash testimonial portraits

Replace letter-monograms with curated Unsplash portrait photos.

3 portrait IDs (verified 2026-05-15) :
- Polaar / Équipe Growth → `1573497019940-1c28c88b4f3e` (female founder casual)
- Respond.io / Marketing Lead → `1507003211169-0a1dd7228f2d` (male professional)
- L'Équipe Creative / Direction technique → `1494790108377-be9c29b29330` (female professional)

URL pattern : `https://images.unsplash.com/photo-<id>?w=240&h=240&fit=crop&crop=faces`

Embed in testimonial card via `<img class="testimonial-avatar-photo">`
when `unsplash_portrait_id` is present on the testimonial. Falls back
to the letter-monogram otherwise.

### D3. Pull-quote callouts every 3rd reason

Insert a styled `<aside class="pull-quote">` after reasons 3, 6, 9
of a 10-reason listicle. Content = the side_note (highlight) of the
PREVIOUS reason, displayed XL display italic with a quote mark
flourish. Premium magazine convention.

### D4. Hero accent line + bigger drop cap

- Add a `<span class="hero-accent-bar">` 4px vertical line, brand
  primary, on the left of the eyebrow → editorial gutter device
- Bump intro `:first-letter` drop cap from 5.2rem → 6.4rem with
  serif fallback

### D5. Verify

Run V11 end-to-end, check :
- composite_score ≥ 92 (Stratospheric)
- Humanlike score ≥ 82 (was 72.5)
- 0 letter-monogram avatars (3 unsplash photos rendered)
- 3 pull-quotes in body

## Files to modify

- `moteur_gsg/core/copy_lp_creator_parser.py` (regex tweak)
- `moteur_gsg/core/brief_v2.py` (Testimonial dataclass : add
  `unsplash_portrait_id: Optional[str]`)
- `moteur_gsg/core/page_renderer_orchestrator.py` (testimonial card
  rendering + pull-quote injection)
- `moteur_gsg/core/css/components.py` (avatar-photo + pull-quote +
  drop-cap CSS)
- `moteur_gsg/core/css/base.py` (hero-accent-bar)
- `deliverables/gsg_demo/weglot-listicle-brief-v2-FROM-LP-CREATOR.json`
  (add `unsplash_portrait_id` per testimonial)
