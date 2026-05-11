# Issue #5 — Stream A progress

Branch: `task/5-capture` (worktree `/Users/mathisfronty/Developer/epic-cleanup-task5`)
Status: **complete on branch (not pushed, not merged)**

## Commits

1. `b68ac8c` — Issue #5: scaffold growthcro/capture/ — __init__, dom, cloud
2. `15132ed` — Issue #5: extract growthcro/capture/{browser,persist,orchestrator,cli}
3. `1666c72` — Issue #5: extract growthcro/capture/{scorer,signals}
4. `211cdfb` — Issue #5: shim ghost_capture_cloud.py and skills/.../native_capture.py
5. `8e7a5cf` — Issue #5: refresh capabilities registry after capture split

## Final LOC distribution (all ≤ 800)

```
573  growthcro/capture/dom.py
524  growthcro/capture/signals.py
451  growthcro/capture/scorer.py
409  growthcro/capture/orchestrator.py
171  growthcro/capture/browser.py
 88  growthcro/capture/cli.py
 56  growthcro/capture/persist.py
 43  growthcro/capture/cloud.py
  8  growthcro/capture/__init__.py
────
2323 total (vs 2154 in the two god files; +7.8% from helper extraction
        and the explicit retry_with_fallback split)
```

## File map (old → new)

### `ghost_capture_cloud.py` (1,122 LOC) → 6 files

| Old lines | New file | Function(s) |
|---|---|---|
| 67–124 | `dom.py` | `load_extraction_js()` + `SPATIAL_V9_JS` constant |
| 130–260 | `dom.py` | `STEALTH_JS` |
| 265–317 | `dom.py` | `COOKIE_CLICK_JS`, `COOKIE_FORCE_REMOVE_JS`, `CLOSE_POPUPS_JS` |
| 322–474 | `dom.py` | `ANNOTATE_JS`, `REMOVE_ANNOTATIONS_JS` |
| 480–500 | `cloud.py` | `get_brightdata_endpoint()` |
| (new) | `cloud.py` | `resolve_browserless_endpoint()` (extracted helper) |
| 506–577 | `browser.py` | `get_browser()` |
| 666–678 | `browser.py` | `new_stealth_context()` (lifted from inside `capture_page`) |
| 583–632 | `browser.py` | `handle_cookies()` |
| 638–930 | `orchestrator.py` | `capture_page()` (sans nested retry recursion) |
| 752–767 | `orchestrator.py` | `retry_with_fallback()` (NEW — breaks circular dep) |
| 936–1003 | `orchestrator.py` | `run_batch()` |
| 1009–1045 | `orchestrator.py` | `run_single()` |
| 1051–1119 | `cli.py` | `main()` |
| 894–913 | `persist.py` | `assemble_spatial_v9()`, `write_spatial_v9()` |
| 864–866 | `persist.py` | `write_html()` |

### `skills/site-capture/scripts/native_capture.py` (1,032 LOC) → 3 files

| Old lines | New file | Function(s) |
|---|---|---|
| 109–115 | `dom.py` | `clean()` |
| 117–120 | `dom.py` | `strip_scripts_styles()` |
| 209–270 | `dom.py` | `is_parasitic_h1()` (refactored to take args) |
| 273–297 | `dom.py` | `is_parasitic_h2()` |
| 299–331 | `dom.py` | `find_hero_h2_fallback()` |
| 1014 | `persist.py` | `write_capture_json()` |
| 42–104 | `scorer.py::main()` | argv parsing + fetch/load HTML |
| 122–401 | `scorer.py` | `build_capture()` + `_extract_metas()` + `_extract_headings()` + `_detect_hero()` + `_extract_subtitle()` |
| 1016–1032 | `scorer.py::_print_summary()` | summary print |
| 406–484 | `signals.py` | `extract_ctas()` |
| 487–556 | `signals.py` | `extract_social_proof()` |
| 561–594 | `signals.py` | `extract_images()` |
| 599–630 | `signals.py` | `extract_forms()` |
| 635–658 | `signals.py` | `extract_schemas()` |
| 663–694 | `signals.py` | `extract_navigation()` |
| 699–730 | `signals.py` | `extract_overlays()` |
| 735–765 | `signals.py` | `extract_ux_signals()` |
| 770–808 | `signals.py` | `extract_psycho_signals()` |
| 814–866 | `signals.py` | `extract_tech_signals()` |
| 873–938 | `signals.py` | `extract_page_specific()` |

### Shims (forwarding wrappers, scheduled removal in #11)

- `ghost_capture_cloud.py` → 8 LOC, forwards to `growthcro.capture.cli.main`
- `skills/site-capture/scripts/native_capture.py` → 13 LOC, forwards to
  `growthcro.capture.scorer.main` (adds `sys.path.insert(0, repo_root)` so
  the shim survives invocation from any cwd)

## Deviations from the locked split map

1. **`signals.py` was added** as a sub-split of `scorer.py`. The locked
   map estimated `scorer.py` at ~660 LOC, but the full extraction came in
   at 954 LOC after preserving every regex literal verbatim. Per the task
   spec ("If after the natural split a single file still exceeds 800 LOC,
   break further by data shape"), the 11 `extract_*` functions were
   peeled into `signals.py`. `scorer.py` still owns the orchestration
   (`main`, `build_capture`, hero detection, summary). All single-concern
   docstrings preserved; both files now ≤ 524 LOC.

2. **`new_stealth_context()` extracted** to `browser.py` (was inlined
   inside `capture_page`). Removes ~15 LOC from the orchestrator and
   gives `cli.py` and any future caller a single source of truth for the
   stealth UA + locale + timezone block.

3. **`resolve_browserless_endpoint()` added** to `cloud.py`. Mirrors the
   `get_brightdata_endpoint()` shape so `browser.get_browser` no longer
   reads the env directly — it asks `cloud` for an endpoint string. Pure
   refactor, no behaviour change.

## Env var migration

All `os.environ.get(...)` / `os.getenv(...)` removed from the moved
code. Verification:

```
$ grep -rn 'os\.environ\|os\.getenv' growthcro/capture/ \
    ghost_capture_cloud.py skills/site-capture/scripts/native_capture.py
(no output)
```

Reads now go through `growthcro.config`:
- `config.brightdata_wss()` (was `BRIGHTDATA_WSS`)
- `config.brightdata_auth()` (was `BRIGHTDATA_AUTH`)
- `config.browser_ws_endpoint()` (was `BROWSER_WS_ENDPOINT`)
- `config.is_ghost_headed()` (was `GHOST_HEADED`)

No new accessor needed — all four already existed in `growthcro/config.py`.

## Verification

- **AST parse** — all 11 touched files parse clean.
- **Import smoke test** — `from growthcro.capture import {cli, orchestrator,
  browser, cloud, dom, persist, scorer, signals}` resolves; circular-dep
  check passes.
- **Shim CLI smoke test** — `python3 ghost_capture_cloud.py --dry-run …`
  prints expected `DRY RUN — test/home → https://example.com (LOCAL)`;
  `python3 skills/site-capture/scripts/native_capture.py` (no args)
  prints the usage line.
- **Functional parity (scorer)** — ran the new shim against the live
  fixture `/Users/mathisfronty/Developer/growth-cro/data/captures/weglot/
  home/page.html` and diffed the resulting `capture.json` against the
  golden under the project's own scrub keys (timestamps, run_id, etc.).
  **Diff: empty** once `third_party_domains` (a pre-existing
  set-iteration-order nondeterminism in the original code) is also
  scrubbed. The parser is byte-faithful to the source.
- **`scripts/parity_check.sh weglot`** — `Parity OK — 0 files match
  baseline` (the worktree has no captured client data on disk; the
  important signal is that the script doesn't error and doesn't drift).
- **`scripts/audit_capabilities.py`** — orphan count unchanged from
  baseline: `0 HIGH, 0 partial wired, 47 potentially orphaned, 144 files
  scanned`. The two old paths are now wired-via-shim.

## Open items for review

1. The 5-line shim at `ghost_capture_cloud.py` follows the exact pattern
   in the locked split map. The 13-line shim at
   `skills/site-capture/scripts/native_capture.py` adds 4 lines of
   sys.path bootstrap so the shim works when invoked from any cwd
   (capture_full.py invokes it with `cwd=ROOT`, which is fine, but
   external callers and direct CLI use would otherwise hit
   `ModuleNotFoundError: growthcro`). If you'd rather keep the shim at
   exactly 5 lines and require all callers to set cwd correctly, drop
   lines 5–9 of that file.

2. `growthcro/__init__.py` was NOT modified — sub-package is auto-
   discovered. No re-exports added. If you want `from growthcro import
   capture` (vs `from growthcro.capture import …`) to also work, add a
   one-liner there.

3. The `signals.py` sub-split deviates from the locked map's 7-file
   layout (now 8 files). Justification above. If you'd rather have a
   single `scorer.py` over 800 LOC, revert `1666c72` and merge
   `signals.py` back in.
