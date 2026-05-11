# GSG Stratosphere — Live-Run Requirement

**Status post commit (#19 structural landing):** 3 LPs scaffolded via
`generate_lp(mode="complete", copy_fallback_only=True, skip_judges=True)`.
The HTML carries the **full V27.2-G+ pipeline** (deterministic planner,
visual_system, controlled renderer, minimal_guards, Emil Kowalski
animations layer, prefers-reduced-motion gate) BUT **the copy slots
contain deterministic placeholders** from `fallback_copy_from_plan()`
because no `ANTHROPIC_API_KEY` was available in this worktree.

## What the scaffolds prove (without live API)

| Check | japhy-pdp | stripe-pricing | linear-leadgen |
|---|---|---|---|
| HTML structurally complete (`<!DOCTYPE>` … `</html>`) | ✓ | ✓ | ✓ |
| V27.2-G visual system markers (`data-visual-system`) | ✓ | ✓ | ✓ |
| Emil Kowalski animations (`gsg-animations-emil-kowalski-v27.2-g`) | ✓ | ✓ | ✓ |
| `prefers-reduced-motion: reduce` opt-out | ✓ | ✓ | ✓ |
| Minimal gates (CTA / font / language / proof) | PASS | PASS | PASS |
| Impeccable QA (deterministic, no API) | 100/100 | 100/100 | 100/100 |
| Multi-judge regression vs Weglot 70.9% | LIVE-RUN | LIVE-RUN | LIVE-RUN |

## Live-run procedure (Mathis)

```bash
cd /Users/mathisfronty/Developer/task-19-gsg-stratosphere
export ANTHROPIC_API_KEY="sk-ant-..."   # from .env (gitignored)

# 1. Regenerate each LP with live Sonnet copy + multi-judge audit:
python3 -m moteur_gsg.orchestrator \
  --mode complete --client japhy --page-type pdp \
  --objectif "Faire commander dans les 90 prochaines secondes" \
  --audience "Proprietaire de chien adulte ou senior, urbain..." \
  --angle "PDP qui combine preuve produit + recalibrage dosage + risk reversal" \
  --primary-cta-label "Composer la ration" --primary-cta-href "#composer" \
  --save-html deliverables/gsg_stratosphere/japhy-pdp-v27_2_g.html \
  --save-audit data/_pipeline_runs/_regression_19/japhy_pdp_now.json

# 2. Same for stripe-pricing + linear-leadgen (see briefs in
#    .claude/epics/webapp-stratosphere/19.md AC table).

# 3. Run the regression gate:
bash scripts/test_gsg_regression.sh
# Must exit 0 with all 4 (Weglot baseline + 3 new) PASS within 5pt budget.

# 4. Playwright screenshots (desktop + mobile):
for client in japhy stripe linear; do
  case "$client" in
    japhy) page=pdp ;;
    stripe) page=pricing ;;
    linear) page=leadgen ;;
  esac
  node scripts/qa_gsg_html.js \
    "deliverables/gsg_stratosphere/${client}-${page}-v27_2_g.html" \
    "deliverables/gsg_stratosphere/screenshots/${client}-${page}"
done

# 5. doctrine-keeper review (sub-agent), then commit:
#    - `Issue #19: live-run regenerate 3 LPs + multi-judge audit JSON`
#    - `Issue #19: Playwright screenshots desktop + mobile`
```

## Why scaffold-first

Per the issue #19 spec verbatim:

> **IMPORTANT — robustness against API failures**:
> - If Sonnet API fails: gracefully fallback to "scaffold + document
>   live-run" — DO NOT crash
> - Commit structural deliverables FIRST (animations.py, impeccable_qa.py,
>   regression script) before attempting API-dependent steps

The structural code (animations.py + impeccable_qa.py + wiring +
regression script + asset-path robustness) is landed and reversible.
Live-run is one bash invocation away.

## Cost estimate (live run)

* 3 × `generate_lp` Sonnet generation (copy slots ≤ 6K tokens out each):
  ~$0.10-0.15 / LP × 3 = ~$0.45
* 3 × `run_multi_judge` (doctrine + humanlike + impl_check, parallelised
  per pillar): ~$0.25-0.30 / LP × 3 = ~$0.90
* 1 × Weglot baseline re-score: ~$0.30
* **Total: ~$1.50-2.00** (well within the $30-50 programme budget).

Wall time: ~3-5 min per LP including multi-judge.
