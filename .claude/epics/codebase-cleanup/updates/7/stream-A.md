# Issue #7 — Stream A progress

**Branch**: `task/7-perception-scoring`
**Worktree**: `/Users/mathisfronty/Developer/epic-cleanup-task7`
**Status**: implementation complete; commits pending push to epic branch.

## What was done

### Perception split (`growthcro/perception/`, 1066 LOC across 6 files)
- `__init__.py` (29 LOC) — public API re-exports
- `heuristics.py` (149 LOC) — keyword regexes, bbox/font helpers, `compute_noise_score`
- `vision.py` (133 LOC) — `compute_adaptive_eps`, `dbscan_1d_vertical`, `refine_clusters_by_y_gap`
- `intent.py` (154 LOC) — `assign_cluster_role` (HERO/NAV/UTILITY_BANNER/PRICING/FAQ/SOCIAL_PROOF/VALUE_PROPS/FINAL_CTA/FOOTER/MODAL/CONTENT)
- `persist.py` (533 LOC) — `process_page` orchestrator (flatten → noise score → cluster → role assignment → fold-merge → orphan-rescue → tier3 fallback → pricing rescue → write `perception_v13.json`)
- `cli.py` (68 LOC) — argparse entrypoint (`--client`, `--page`, `--all`)

### Scoring split (`growthcro/scoring/`, 1788 LOC across 9 files)
- `__init__.py` (18 LOC) — re-exports of dispatcher + DETECTORS
- `pillars.py` (100 LOC) — **shared dispatcher** (`apply_pagetype_filter`, `apply_weights`, `apply_caps_and_round`, `compute_verdict`) — reused by ux.py
- `ux.py` (576 LOC) — bloc-3 UX scorer (8 criteria + dispatcher) using `pillars.py`
- `persist.py` (112 LOC) — `score_page_type_specific`, `load_capture`, `write_specific_score`
- `cli.py` (47 LOC) — `score_specific()` and `score_ux_main()` entrypoints
- `specific/` sub-package (4 family files + aggregator):
  - `__init__.py` (76 LOC) — TERNARY, `_mk`, `_html`, `_text`, `_h1`, `_nearest_digit`, `d_review_required`, DETECTORS aggregator
  - `listicle.py` (98 LOC) — `list_*` + `blog_*` (9 IDs)
  - `product.py` (117 LOC) — `pdp_*`, `col_*`, shared `d_trust_badges`/`d_social_proof_count` (8 IDs)
  - `sales.py` (352 LOC) — `vsl_*`, `sqz_*`, `lg_*`, `sp_*`, `chal_*`, `web_*`, `quiz_*` (22 IDs)
  - `home_leadgen.py` (292 LOC) — `home_*`, `price_*`, `ck_*`, `typ_*`, `bund_*`, `comp_*`, `adv_*` (21 IDs)

DETECTORS registry: 60 keys (parity with the legacy `score_specific_criteria.py` — verified by diffing `sorted(.keys())`).

### Research split (`growthcro/research/`, 1003 LOC across 5 files)
- `__init__.py` (22 LOC) — re-exports
- `discovery.py` (134 LOC) — `PAGE_CATEGORIES`, `LinkExtractor`, `categorize_url`, `extract_links_from_url`
- `content.py` (130 LOC) — `TextExtractor`, `fetch_page_text`, `ghost_fetch`, `extract_structured_content`
- `brand_identity.py` (485 LOC) — color helpers, `StyleExtractor`, `extract_colors_from_css`, `extract_fonts_from_css`, `extract_style_mood`, `extract_brand_identity`
- `cli.py` (232 LOC) — `run_intelligence` orchestrator + argparse

### Shims (4 files, 34 LOC total)
- `skills/site-capture/scripts/perception_v13.py` (6 LOC) → `growthcro.perception.cli.main`
- `skills/site-capture/scripts/score_specific_criteria.py` (16 LOC) → `growthcro.scoring.cli.score_specific` + re-exports `DETECTORS`, `score_page_type_specific` for any consumer that imported them
- `skills/site-capture/scripts/score_ux.py` (6 LOC) → `growthcro.scoring.cli.score_ux_main`
- `scripts/site_intelligence.py` (6 LOC) → `growthcro.research.cli.main` + re-exports `run_intelligence`

## Acceptance gates

| Gate | Status |
|---|---|
| All package files ≤ 800 LOC | ✅ largest is `scoring/ux.py` at 576 LOC |
| One-line concern docstring per file | ✅ |
| 60-key DETECTORS parity vs legacy | ✅ same keyset |
| `python3 SCHEMA/validate_all.py` | ✅ 8 files validated, all passing |
| `python3 scripts/audit_capabilities.py` | ✅ 0 HIGH orphans (= baseline), 47 potentially-orph (= baseline) |
| All 4 shims importable + callable | ✅ verified |
| Zero `os.environ`/`os.getenv` in new packages | ✅ grep clean |
| Doctrine playbooks untouched | ✅ no `playbook/*.json` writes |

`parity_check.sh weglot` was not run because this fresh worktree contains no `data/captures/`. The test will be run on the epic branch where data is available.

## Deferred / pending

- **`vision.py` Anthropic wiring deferred** — depends on #6's `growthcro/lib/anthropic_client.py`. The current `vision.py` exposes only the pure-geometry DBSCAN primitives (which is all `perception_v13` ever used). When #6 lands the lib, `vision.py` can grow a `call_sonnet(image_path, prompt)` helper without touching the existing API.
- Once #6 merges to epic and we rebase, `score_ux.py`'s soft-import of `perception_bridge`/`spatial_bridge` should be re-evaluated — currently it injects `skills/site-capture/scripts` into `sys.path` to keep the bridge imports working.

## Commit plan

Per the issue brief, commits are kept isolated:
1. `Issue #7: extract growthcro/perception/ from perception_v13`
2. `Issue #7: split growthcro/scoring/specific/ by pageType family + pillars dispatcher`
3. `Issue #7: extract growthcro/scoring/{ux,persist,cli}.py`
4. `Issue #7: sub-split site_intelligence into growthcro/research/{discovery,content,brand_identity,cli}.py`
5. `Issue #7: shim 4 legacy perception/scoring/research entrypoints`

Branch left at `task/7-perception-scoring`. **No push, no merge.**
