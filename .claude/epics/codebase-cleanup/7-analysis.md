---
issue: 7
title: Split perception & scoring god files
analyzed: 2026-05-10T12:30:00Z
estimated_hours: 18
parallelization_factor: 1.0
---

# Parallel Work Analysis: Issue #7

## Overview

Split 4 god files (perception_v13 1,134 / score_specific_criteria 1,101 / score_ux 710 / site_intelligence 1,070) into 3 packages: `growthcro/perception/`, `growthcro/scoring/` (with `specific/` sub-pkg per Mathis decision), `growthcro/research/` (site_intel sub-split also per decision).

## Parallel Streams

### Stream A: Perception + scoring + research splits
**Scope**: All perception/scoring/research splits and shims.
**Files**:
- CREATE: `growthcro/perception/{__init__.py, heuristics.py, vision.py, intent.py, persist.py, cli.py}`
- CREATE: `growthcro/scoring/{__init__.py, pillars.py, ux.py, persist.py, cli.py}`
- CREATE: `growthcro/scoring/specific/{__init__.py, listicle.py, product.py, sales.py, home_leadgen.py}`
- CREATE: `growthcro/research/{__init__.py, discovery.py, content.py, brand_identity.py, cli.py}`
- MODIFY → SHIM: `skills/site-capture/scripts/perception_v13.py`, `score_specific_criteria.py`, `score_ux.py`, `scripts/site_intelligence.py`
**Can Start**: immediately (parallel with #5/#6/#8)
**Dependencies**: none for splits. If `vision.py` uses Anthropic SDK, wait for #6's lib commit.
**Estimated Hours**: 18

## Coordination Points

### Shared Files
- `growthcro/lib/anthropic_client.py` — created by #6. Pull-rebase before importing.
- No overlap with #5/#6/#8 file trees.

### Sequential Requirements
- Within #7: pillars.py before ux.py (ux imports the dispatcher).
- Within #7: scoring/specific/__init__.py aggregator built last.

## Conflict Risk Assessment

LOW — disjoint from other Wave-2 issues. Only soft dep on #6's lib.

## Parallelization Strategy

Single stream. Split execution order:
1. perception/ (all 5 files)
2. scoring/ (pillars + ux + specific/ sub-pkg)
3. research/ (site_intel sub-split)
4. Shims at old paths
5. Capabilities-keeper

## Expected Timeline

- Wall time: ~18h (largest split — 4 god files)
- Critical path inside epic: yes — largest issue in Wave 2
