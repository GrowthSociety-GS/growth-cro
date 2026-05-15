# Epic — GSG Stratospheric Final Polish (Sprint 17)

**Created** : 2026-05-15
**Status** : 🚀 IN PROGRESS
**Triggered by** : Mathis 2026-05-15 V9 review — *"c'est mieux mais y'a bcp de problèmes"*
**Cost target** : ≤ 4h Claude Code wall-clock

## Why this epic exists

V9 multi-judge said **82.1% Excellent** — but Mathis disagrees visually:

1. **"Mini images à côté des numéros sont nulles, on les voit pas"** → contextual screenshots are 88px high, too small + not topically rich
2. **"T'es même pas allé chercher des vraies images de la vie"** → no Unsplash / image-bank fetches, no professionally-curated illustrations
3. **"Le bandeau (screen) qui veut rien dire"** → redundant English proof strip mixing capture-derived EN facts with FR brief facts
4. **"Pas stratosphérique, pas de textures travaillées, ça sort pas du AI-like"** → flat surfaces, no grain / depth / editorial details
5. **"Texte réduit, certaines tournures incompréhensibles"** → LP-Creator copy preserved verbatim BUT not edited for clarity
6. **"Revoir tous les critères de jugement et le système de notation"** → the scoring system says "Excellent" but Mathis says it's not — recalibration needed
7. **"Scanne tes skills au complet"** → audit reveals brand-guidelines & frontend-design are NOT real external skills — they're Python modules I wrote with skill-sounding names

## 3 sub-PRDs

### [PRD-A — Recalibrate notation system](prds/PRD-A-recalibrate-notation.md)
- Audit every scoring module's weights + thresholds
- Update doctrine : "Excellent" requires ≥ 90% (was ≥ 80%)
- Document skills overlap matrix : avoid double-counting
- Recalibrate impeccable_qa / cro_methodology severity weights based on Mathis's "visceral" reaction patterns

### [PRD-B — Visual jump to stratospheric](prds/PRD-B-visual-jump.md)
- Remove redundant English proof strip (the "bandeau qui veut rien dire")
- Create `reason_illustration.py` : 10 line-art SVG illustrations (280×200) per reason topic
- Add `paper-grain.svg` texture overlay (1-2% opacity) for editorial feel
- Hero editorial details : vertical accent line, drop cap in intro paragraph
- Real Unsplash photos for the 3 testimonials (avatar replacement)

### [PRD-C — Skills truthful audit](prds/PRD-C-skills-audit.md)
- Document what's actually a real skill vs a Python module masquerading as one
- Rename `brand_guidelines_audit.py` / `frontend_design_audit.py` honestly OR install the real skills if available
- Skills overlap map : ensure no contradictions between cro-methodology + emil-design-eng + impeccable
- Recommend installs : if there's a real `unsplash-images` skill, add it ; otherwise document Unsplash CDN URL pattern as the standard fetch route

## Out of scope (Sprint 18+)

- Multi-page generation
- A/B variants generation
- True Anthropic Skill tool wire-up (vs Python heuristic modules)
- Sprint 19+ : webapp integration of the new audit suite

## Acceptance gates

- [ ] V10 generated end-to-end : Playwright screenshot desktop+mobile
- [ ] 0 redundant EN proof strip ; 10/10 reasons have a custom SVG illustration ≥ 200px height
- [ ] Multi-judge ≥ 85% with the NEW calibration (which is stricter — proves the page is truly excellent)
- [ ] Documentation updated : `docs/state/SKILLS_HONEST_AUDIT_2026-05-15.md` + doctrine
- [ ] `memory/SPRINT_LESSONS.md` Sprint 17 closeout with 3 rules

## PRDs index

- [PRD-A — Recalibrate notation system](prds/PRD-A-recalibrate-notation.md)
- [PRD-B — Visual jump to stratospheric](prds/PRD-B-visual-jump.md)
- [PRD-C — Skills truthful audit](prds/PRD-C-skills-audit.md)
