---
issue: 5
title: Split capture god files into growthcro/capture/
analyzed: 2026-05-10T12:30:00Z
estimated_hours: 12
parallelization_factor: 1.0
---

# Parallel Work Analysis: Issue #5

## Overview

Split two god files (`ghost_capture_cloud.py` 1,122 LOC, `skills/site-capture/scripts/native_capture.py` 1,032 LOC) into `growthcro/capture/` package. One stream — internally sequential because the moves cascade (extract dom → extract persist → extract orchestrator → leave shim).

## Parallel Streams

### Stream A: Capture package creation
**Scope**: All capture-related splits and shims.
**Files**:
- CREATE: `growthcro/capture/{__init__.py, browser.py, cloud.py, dom.py, persist.py, orchestrator.py, scorer.py, cli.py}`
- MODIFY → SHIM: `ghost_capture_cloud.py`, `skills/site-capture/scripts/native_capture.py`
**Can Start**: immediately (deps #2, #3 closed)
**Dependencies**: none
**Estimated Hours**: 12

## Coordination Points

### Shared Files
- `growthcro/__init__.py` — read-only (no edit needed; sub-package is auto-discovered via Python imports)
- No conflict with #6, #7, #8 — disjoint sub-trees

### Sequential Requirements
- N/A inside this issue (one stream)
- Inter-issue: #9 (root reorg) waits for #5's shim to land before touching root files

## Conflict Risk Assessment

LOW — disjoint file scope from #6/#7/#8. Only shared touchpoint is `growthcro/__init__.py` which doesn't need edit.

## Parallelization Strategy

This issue runs as one stream within the broader Wave-2 parallelism (alongside #6/#7/#8).

## Expected Timeline

- Wall time: ~12h (single agent in worktree)
- Critical path inside epic: not on it (capture splits don't gate any other Wave-2 task)
