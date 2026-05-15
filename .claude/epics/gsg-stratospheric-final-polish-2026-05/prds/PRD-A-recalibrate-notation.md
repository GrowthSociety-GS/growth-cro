# PRD-A — Recalibrate Notation System

**Sprint 17 / Epic** : gsg-stratospheric-final-polish-2026-05
**Estimated** : 45 min

## Problem

V9 scores 82.1% "Excellent" but Mathis disagrees visually. The bar is set too low. **"Excellent" must mean "Mathis can ship to a paying agency client without editing"** — which V9 isn't.

## Solution

### A1. Threshold recalibration

Update `moteur_multi_judge/orchestrator.py` thresholds :

| Tier | Old | NEW |
|------|-----|-----|
| Stratospheric | n/a | ≥ 90% |
| Excellent | ≥ 80% | ≥ 85% |
| Bon | ≥ 70% | ≥ 75% |
| Moyen | ≥ 50% | ≥ 60% |
| Insuffisant | < 50% | < 60% |

### A2. Skill weights

Today: equal-weight average. New: weighted by Mathis-perceived importance.

| Skill | Old weight | NEW weight | Reason |
|-------|-----------|-----------|--------|
| Multi-judge (Doctrine + Humanlike) | 0.70 | 0.55 | Still the main signal but doesn't capture visual texture |
| Impeccable QA | 0.10 | 0.10 | OK as gate |
| CRO methodology | 0.10 | 0.15 | Up — Mathis cares about conversion fundamentals |
| frontend-design | 0.10 | 0.10 | Same |
| brand-guidelines | n/a | 0.05 | New small weight (mostly anti-bullshit gate) |
| emil-design-eng | n/a | 0.05 | New small weight (motion polish) |

### A3. New "visual_density" rule in impeccable_qa

Add anti-pattern : `visual_density_too_low` — fails when a section has ratio (text area / total pixel area) > 70% AND no image / illustration. This catches the "flat slabs of text" feel Mathis hates.

### A4. New "redundant_proof_section" in impeccable_qa

Anti-pattern : two consecutive sections repeating the same fact (e.g. proof strip echoing reason 01 highlight). Mathis 2026-05-15 : *"le bandeau qui veut rien dire"*.

## Acceptance

- [ ] `moteur_multi_judge/orchestrator.py` thresholds updated + tested with V9 (must drop to "Bon" not "Excellent")
- [ ] Final score formula = weighted avg of 6 audits (multi-judge / impeccable / cro / frontend-design / brand-guidelines / emil-design-eng)
- [ ] New 2 impeccable_qa rules wired
- [ ] `canonical_run_summary.json` gets a new top-level `final_grade` field = "Stratospheric / Excellent / Bon / Moyen / Insuffisant"

## Out of scope

- New judges (vibes judge, taste judge) — Sprint 18
- LLM-based recalibration loop — Sprint 19
