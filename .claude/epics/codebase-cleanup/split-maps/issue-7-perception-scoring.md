# Split map — Issue #7 (perception + scoring god files)

> **Mathis decisions (2026-05-10) — locked**:
> - **Sub-split `score_specific_criteria.py`** par pageType family : `growthcro/scoring/specific/{listicle,product,sales,home_leadgen}.py` + `__init__.py` aggregator. Tout ≤800 LOC.
> - **Sub-split `site_intelligence.py`** dans la même issue (1,070 LOC viole cap) → `growthcro/research/{discovery,content,brand_identity,cli}.py`.
> - `pillars.py` = thin shared dispatcher (110 LOC), réutilisé par les 6 blocs.
> - Perception→scoring bridge (score_ux L654–670) : keep best-effort fallback, document as optional enrichment.
> - `growthcro.config` API confirmed (cf #6).
> - Si besoin Anthropic SDK : import `growthcro.lib.anthropic_client` créé par #6 — `git pull --rebase` avant.


## File: `perception_v13.py` (1,134 LOC)

DOM-to-perception pipeline. Reads `spatial_v9_clean.json` + `capture.json` → emits 9 cluster roles (HERO, NAV, UTILITY_BANNER, PRICING, FAQ, SOCIAL_PROOF, VALUE_PROPS, FINAL_CTA, FOOTER) via adaptive DBSCAN + rule-based role assignment.

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `heuristics.py` | 42–221 | NOISE/FOOTER/NAV/CTA keyword constants + bbox/font helpers + `compute_noise_score` | 180 |
| `vision.py` | 223–322 | `dbscan_1d_vertical`, `refine_clusters_by_y_gap`, `compute_adaptive_eps` | 100 |
| `intent.py` | 328–473 | `assign_cluster_role`, role-score logic | 146 |
| `persist.py` | 480–590 | `process_page` flatten/dedup/page_context, output write | 111 |
| `cli.py` | 1077–1134 | argparse, `walk_clients` | 57 |

**Env vars**: 0.

## File: `score_specific_criteria.py` (1,101 LOC)

Page-type doctrine engine. Reads `playbook/page_type_criteria.json` → dispatches 50+ detector functions per `(pageType, criterion_id)` → ternary scores `{top:3, ok:1.5, critical:0}`.

**Boundary vs `pillars.py`**: this file handles **pageType-unique criteria** (e.g., `list_01: H1 with number` only for listicles). `pillars.py` (new) will handle the **6 universal pillars** (Hero, Persuasion, UX, Coherence, Psycho, Tech) across all pageTypes.

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `specific_criteria.py` | 50–987 | All 50+ pageType detectors + DETECTORS registry | **938** ⚠️ |
| `persist.py` | 1006–1100 | `score_page_type_specific`, `_load_capture`, main | 95 |

**⚠️ 938 LOC violates 800 cap.** Split further: group detectors by pageType family →
- `specific/listicle.py` (list_*) ~250
- `specific/product.py` (pdp_*) ~200
- `specific/sales.py` (vsl_*, sales_*) ~250
- `specific/leadgen.py` + `specific/home.py` etc. ~240
- `specific/__init__.py` aggregates DETECTORS dict ~50

**Env vars**: 0.

## File: `score_ux.py` (710 LOC) — **REFACTOR (mixed concern)**

Function-prefix histogram:
- L140–575: `ux_01..ux_08` scorers (8 blocks, 35–50 LOC each) — bloc-3 internal
- L30–100 + L577–701: pageType filter / weight / cap / verdict — **dispatcher framework** (belongs to all 6 blocs)
- L16–28, 75–80, 652–670: optional `spatial_bridge` / `perception_bridge` enrichment — cross-bloc

**Verdict: SPLIT.**

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `ux.py` | 140–575 | `ux_01..ux_08` heuristics only | 435 |
| `pillars.py` (shared dispatcher) | 593–701 | pageType filtering, weighting, normalization, caps, verdict — reused by all 6 blocs | 110 |

## File: `site_intelligence.py` (1,070 LOC) — **INDEPENDENT**

Full-site crawler + content extractor. Discovers internal URLs, categorizes (about/testimonials/press/blog/FAQ/pricing/legal), fetches text+HTML, extracts brand identity (colors/fonts/mood from CSS), produces `site_intel.json`.

**Verdict: NOT perception.** Reasons:
1. Operates on whole site, not single page.
2. No reuse: perception_v13/score_ux don't consume `site_intel.json`.
3. Different output contract (sitemap + brand inventory vs page scores).
4. Different lifecycle (once per client at start vs per page capture).

**Action**: move to `growthcro/research/site_intelligence.py` with module docstring documenting the boundary.

## Doctrine touch — ✅ verified clean

None of the 4 files modify `playbook/*.json`. All read-only consumers. Safe.

## Final layout

```
growthcro/perception/
├── __init__.py
├── heuristics.py          (~180)
├── vision.py              (~100)
├── intent.py              (~146)
├── persist.py             (~111)
└── cli.py                 (~57)

growthcro/scoring/
├── __init__.py
├── pillars.py             (~110)  ← shared dispatcher
├── specific/
│   ├── __init__.py        (~50)   ← DETECTORS registry aggregator
│   ├── listicle.py        (~250)
│   ├── product.py         (~200)
│   ├── sales.py           (~250)
│   └── home_leadgen.py    (~240)
├── ux.py                  (~435)
├── persist.py             (~95)
└── cli.py                 (new, ~50)

growthcro/research/
└── site_intelligence.py   (~1,070) — wrap as-is or split if >800 by sub-concern
```

**Note**: `site_intelligence.py` itself ~1,070 LOC also violates cap. Sub-split if doing this issue means splitting it too:
- `discovery.py` (URL crawl + categorization) ~400
- `content.py` (text/HTML fetch + extract) ~350
- `brand_identity.py` (CSS color/font/mood extraction) ~250
- `cli.py` ~70

## Shim plan

```python
# skills/site-capture/scripts/perception_v13.py
"""Shim — use growthcro.perception.cli (removed in #11)."""
from growthcro.perception.cli import main
if __name__ == "__main__": main()

# skills/site-capture/scripts/score_specific_criteria.py
"""Shim — use growthcro.scoring.cli (removed in #11)."""
from growthcro.scoring.cli import score_specific
if __name__ == "__main__": score_specific()

# skills/site-capture/scripts/score_ux.py — same pattern
# scripts/site_intelligence.py — same pattern, points at growthcro.research.site_intelligence.cli
```

## Open questions for Mathis

1. **`pillars.py` cardinality**: do all 6 blocs (hero/persuasion/ux/coherence/psycho/tech) share identical pageType filter+weight logic, or per-bloc customization needed? Decides whether `pillars.py` is a thin shared framework or just a base class.
2. **Perception→scoring bridge** (score_ux L654–670): formalize as `growthcro.perception.bridges`, or keep best-effort fallback, or remove (one-way data flow)? **Recommendation: keep best-effort**, document as an optional enrichment.
3. **`site_intelligence.py` placement**: confirm `growthcro/research/` (orthogonal product) vs `growthcro/perception/discovery/` (pre-phase). **Recommendation: `research/`** — different lifecycle, different output.
