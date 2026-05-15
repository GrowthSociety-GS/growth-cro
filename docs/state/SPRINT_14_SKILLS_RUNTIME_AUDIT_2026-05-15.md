# Sprint 14 — Honest Skills Runtime Audit (2026-05-15)

**Why this exists** : Mathis flagged a doctrine ↔ implementation gap on
2026-05-15 — the GSG doctrine documents 4+ "design DNA" skills as
mandatory parts of the pipeline (`frontend-design`, `brand-guidelines`,
`emil-design-eng`, `cro-methodology`), but only `impeccable_qa` is
actually invoked at runtime by `moteur_gsg.modes.mode_1_complete`.
This document records the **real** state, not the aspirational one,
so the next sprint can make a deliberate decision.

## Wired at runtime ✅

| Skill | Call site | Trigger | Effect on output |
|------|----------|---------|------------------|
| `impeccable_qa` | [`moteur_gsg/modes/mode_1_complete.py`](../../moteur_gsg/modes/mode_1_complete.py) — `run_impeccable_qa(html=...)` after `apply_minimal_postprocess`, before `run_multi_judge` | Always, on every page render | Hard-gates the HTML against the 88-rule no-AI-slop ruleset. Returns `pass=true/false` + `hits[]`. If `gate_strict=True`, refuses to ship pages with hits. Output : `impeccable_qa.json` next to HTML. |

That's it. **One skill** out of the ~5 the doctrine claims are wired.

## Installed but NOT wired ❌

| Skill | Doctrine claim | Actual call site in code | Decision needed |
|------|----------------|--------------------------|-----------------|
| `frontend-design` (Anthropic skill) | "Used by `visual_system.py` to pick layout treatments" | **None.** `visual_system.py` uses a hardcoded `PAGE_RENDER_PROFILES` dict + `LAYOUT_VISUAL_KINDS`. No `Skill` tool invocation. | Either invoke at runtime (cost + latency) OR document as aspirational/manual |
| `brand-guidelines` (Anthropic skill) | "Per-client brand DNA enforcement at copy + visual time" | **None.** `brand_intelligence.py` reads `data/captures/<client>/brand_dna.json` directly. No `Skill` tool call. | Same |
| `emil-design-eng` (Anthropic skill) | "Drives the V27.2-G+ motion layer (`animations.py`)" | **None.** `animations.py` hardcodes the Emil Kowalski-inspired easing + reveal patterns. No `Skill` call. | Same |
| `cro-methodology` (Anthropic skill) | "Post-process copy gate" | **None.** Only doctrine v3.2.1 YAML criteria are loaded via `doctrine_planner.py`. No `Skill` call. | Same |

## Multi-judge

`scripts/run_gsg_full_pipeline.py` exposes `--skip-judges` flag. In the
Weglot FUSED-FINAL run on 2026-05-15 it was **skipped** (developer
shortcut to iterate fast). The judges (`run_multi_judge`) do exist and
are wired in `mode_1_complete.py` — they just weren't run for that
specific output.

→ **Decision for Sprint 14 close** : re-run Weglot WITHOUT
`--skip-judges` so the artefact includes the doctrine score + humanlike
score.

## Why this matters

The user's frustration on 2026-05-15 was : *"t'es sûr qu'on a tout fait
avec le full pipe et le GSG end to end à jour avec toutes les
compétences qu'on doit utiliser et qui respecte l'architecture qu'on
s'est donné ?"*

The honest answer is **no, not exactly** :

- The doctrine documents skills as wired
- The implementation only wires `impeccable_qa`
- The other 4 skills are knowledge-bases that **the model uses during
  development** (when Claude Code writes the renderer code), not
  runtime invocations during page generation

This is fine — but the doctrine must reflect that distinction or
Sprint X will need to wire them all.

## Recommended next step (NOT Sprint 14 — too big)

**Option A** (conservative) : update [`docs/doctrine/CODE_DOCTRINE.md`](../doctrine/CODE_DOCTRINE.md)
and [`docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`](../reference/SKILLS_INTEGRATION_BLUEPRINT.md)
to mark these 4 skills as **dev-time references** (knowledge that
guided the renderer architecture) and leave the runtime alone. Cheap,
honest, no behavior change.

**Option B** (ambitious) : wire one Skill call per generation
(e.g. `cro-methodology` post-process pass on copy_doc, similar to
`impeccable_qa`). Costs ~1-3s extra latency + token budget per
generation. Worth a separate sprint.

**Sprint 14 close picks Option A** : document the truth, ship the
visual fixes, defer the wiring decision to Sprint 15+.

---

**Visual fixes shipped in Sprint 14** (cf. epic file) :

1. `hero_renderer.py` `proof_atlas` variant : abstract "Proof atlas
   A/B/C ledger" replaced by clean browser-chrome + real Weglot
   screenshot + optional signature stat badge.
2. `component_renderer.py` `_reason_visual` : abstract "FIELD NOTE
   A/B" / "SYSTEM" / "SEO/UX/ROI" labels replaced by 11 inline SVG
   icons (globe, clock, sparkle, search, plug, users, star, trending,
   shield, gift, check) auto-picked from reason heading keywords.
3. `page_renderer_orchestrator.py` : mid-parcours CTA inserted after
   reason `floor(N/2)` when total reasons ≥ 6. Places a soft CTA card
   at ~40-50% scroll instead of relying only on the post-comparison
   CTA at ~70%.
4. `css/components.py` : new rules for `.hero-shot-frame`,
   `.hero-signature`, `.reason-icon-frame`, `.reason-icon-number`,
   `.mid-cta` + mobile media query.
