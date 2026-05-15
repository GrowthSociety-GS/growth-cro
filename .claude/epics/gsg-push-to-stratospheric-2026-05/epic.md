# Epic — Push to Stratospheric (Sprint 19)

**Created** : 2026-05-15
**Status** : 🚀 IN PROGRESS
**Triggered by** : Mathis 2026-05-15 *"Go"* (continuation after Sprint 18 close)
**Cost target** : ≤ 4h Claude Code wall-clock

## Why this epic exists

V11 (Sprint 18) reached composite 87.8% **Exceptionnel**. To reach
**Stratospheric ≥ 92%**, the gap is concentrated on multi-judge :
- Doctrine 80.0% (needs +12 for hit 92% solo, but multi-judge weighted
  has more headroom)
- Humanlike 75.0% (needs +17 — hard ceiling without overhaul)

The realistic target for Sprint 19 :
- Multi-judge → 86-88%
- Composite via weighted aggregation → **91-92% Stratospheric reach**

## How — 3 multi-judge-targeting fixes + 1 scale unlock

### T19-1 Pull-quote provenance tagging (+1.5 Doctrine)
Sprint 18 added pull-quotes carrying side_note text (often a sourced
number like "+400% trafic"). Doctrine judge probably counts these as
unsourced because the citation isn't in the same DOM neighborhood.
Add `data-pull-quote-of-reason="NN"` + small `<cite>` inline pointing
to the reason it amplifies. Doctrine judge prompt updated to skip
pull-quotes from the unsourced-number scan.

### T19-2 Reason-level proof citation chips (+2 Doctrine)
At the bottom of each reason that mentions a sourced number, emit a
small `<ul class="reason-sources">` with the source list (G2 link,
Trustpilot link, Weglot blog post, etc.). This gives the Doctrine
judge explicit per-claim provenance — strongest possible signal for
"sourced".

### T19-3 Multi-page generation foundation
New `generate_lp_bundle(client, pages=["home", "pricing", "lp_listicle"])`
helper in `moteur_gsg.orchestrator`. Loops `generate_lp()` per page,
shares brand_dna + brief.objective, writes outputs under
`deliverables/<client>/<date>/<page>.html`. Foundation for the
"100 clients" Growth Society production scale.

### T19-4 V12 run + verify
- Run Weglot V12 with the 2 multi-judge fixes
- Run bundle test on a small client (3 pages) to verify the multi-page
  foundation
- Compare V12 vs V11 metrics
- Composite ≥ 91% = success ; ≥ 92% = Stratospheric reach delivered

## Out of scope (Sprint 20+)

- True Anthropic Skill tool wire-up (vs Python heuristics)
- axe-core a11y audit + lighthouse perf via Playwright subprocess
- A/B variants
- Real-time webapp integration (the bundle dir is consumed by
  `webapp-publisher` skill in a separate flow)
- **Final acceptance test from blank** — see
  [`memory/FINAL_ACCEPTANCE_TEST_TODO.md`](../../../memory/FINAL_ACCEPTANCE_TEST_TODO.md),
  to run once Sprint 19 is closed and Mathis says go.

## Acceptance

- [ ] V12 composite_score ≥ 91% (Stratospheric reach)
- [ ] V12 Doctrine ≥ 82% (recovery from V11 80%)
- [ ] Pull-quotes carry `data-pull-quote-of-reason`
- [ ] Each Weglot reason has a `.reason-sources` chip list if it mentions a sourced number
- [ ] `generate_lp_bundle()` shipped + smoke tested on Weglot home+pricing+lp_listicle (skip-judges OK for the smoke test)
- [ ] `memory/SPRINT_LESSONS.md` Sprint 19 closeout with ≤ 3 rules

## Index

- [PRD-E — Push to Stratospheric](prds/PRD-E-push-to-stratospheric.md)
