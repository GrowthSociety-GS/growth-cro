---
issue: 6
title: Split recos god files & dedupe enricher variants
analyzed: 2026-05-10T12:30:00Z
estimated_hours: 14
parallelization_factor: 1.0
---

# Parallel Work Analysis: Issue #6

## Overview

Collapse 4 reco_enricher variants into `growthcro/recos/` (one canonical entrypoint), extract shared Anthropic client to `growthcro/lib/anthropic_client.py`, archive `enrich_v143_public.py` (Mathis decision: archive now).

## Parallel Streams

### Stream A: Recos package + lib extraction
**Scope**: All recos splits, shims, lib extraction, v143 archive.
**Files**:
- CREATE: `growthcro/recos/{__init__.py, schema.py, prompts.py, client.py, orchestrator.py, cli.py}`
- CREATE: `growthcro/lib/{__init__.py, anthropic_client.py}` ← also used by #7/#8
- MODIFY → SHIM: `scripts/reco_enricher_v13.py`, `scripts/reco_enricher_v13_api.py`, `skills/site-capture/scripts/reco_enricher_v13.py`, `skills/site-capture/scripts/reco_enricher_v13_api.py`
- MOVE → ARCHIVE: `scripts/enrich_v143_public.py` → `_archive/scripts/enrich_v143_public_2026-05-10/` + README
**Can Start**: immediately
**Dependencies**: none
**Estimated Hours**: 14

## Coordination Points

### Shared Files
- `growthcro/lib/anthropic_client.py` — **#6 owns creation**. #7/#8 must `git pull --rebase origin epic/codebase-cleanup` before importing.
- `growthcro/__init__.py` — read-only

### Sequential Requirements
- Within #6: extract lib first → then recos/client.py imports it.
- Inter-issue: #6 must commit lib BEFORE #7/#8 reach their api_call/vision modules. Easy: #6 commits the lib in commit 1, then the rest of #6 follows.

## Conflict Risk Assessment

MEDIUM — `growthcro/lib/anthropic_client.py` shared with #7/#8. Mitigated by commit ordering (lib first) + agent instruction to pull-rebase.

## Parallelization Strategy

#6 launches first commit (lib extraction) immediately. #7/#8 agents instructed to wait for lib commit on origin before they touch their Anthropic-using files.

## Expected Timeline

- Wall time: ~14h
- Critical path inside epic: yes — gates #7/#8 on the lib commit (small, ~1-2h to land)
