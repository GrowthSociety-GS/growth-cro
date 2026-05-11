# Split map — Issue #5 (capture god files → `growthcro/capture/`)

> **Mathis decisions (2026-05-10) — locked**:
> - **Keep `native_capture.scorer.main()` standalone** (preserve decorator chain `ghost → native --html <path>`).
> - `growthcro.config` API confirmed: `from growthcro.config import config; config.brightdata_wss()` etc. (lazy validation, returns Optional).
> - **Extract `orchestrator.retry_with_fallback()`** wrapping `capture_page()` calls — break the circular nested-capture_page dep.
> - Pas de besoin Anthropic SDK ici (capture pure).


## File 1: `ghost_capture_cloud.py` (~1,122 LOC)

Playwright-based browser orchestration for cloud-native page capture. Replaces Node.js `ghost_capture.js` with Python. Three browser modes (local, cloud WSS, Bright Data), stealth-script injection, full-page screenshots/DOM at multiple viewports, perception-tree extraction, batch concurrency. Two async entry points: single-page + batch.

| New file | Source lines (≈) | Concern | Est. LOC |
|---|---|---|---|
| `browser.py` | 66–576 | Playwright context/page lifecycle, stealth injection, viewport mgmt, navigation | 480 |
| `cloud.py` | 479–577 | Bright Data WSS endpoint resolution, Browserless/Steel fallback, CDPconnect | 140 |
| `dom.py` | 129–473 | STEALTH_JS, COOKIE_CLICK_JS, ANNOTATE_JS, CLOSE_POPUPS_JS, REMOVE_ANNOTATIONS_JS | 310 |
| `persist.py` | 656–912 | Write `spatial_v9.json`, `page.html`, `screenshots/` | 110 |
| `orchestrator.py` | 637–1002 | Single + batch capture pipelines, retries, concurrency | 380 |
| `cli.py` | 1050–1122 | argparse, dry-run, single vs batch routing | 75 |

**Mega-function `capture_page()` (637–929) split horizontally:**
- 664–680 context setup → `browser.py`
- 682–693 navigate + wait-for-load → `browser.py`
- 695–770 human-behavior + 403 detection + Bright Data retry → `orchestrator.py` + `cloud.py`
- 772–882 screenshot/scroll/extraction → `persist.py` + `dom.py`
- 894–912 JSON assembly + write → `persist.py`
- 917–929 result dict → `persist.py`

**Env vars (route through `growthcro.config`):**
- L490 `BRIGHTDATA_WSS`, L495 `BRIGHTDATA_AUTH`, L535 `BROWSER_WS_ENDPOINT`, L552 `GHOST_HEADED`

## File 2: `native_capture.py` (~1,032 LOC)

Static HTML parser for CRO scoring extraction. Ingests raw HTML via urllib OR pre-rendered DOM from Playwright. Extracts 150+ data points across six scoring blocs: hero/H1 (smart parasitic filtering), CTAs, social proof, forms, images, navigation, schema.org, overlays, UX/psycho/tech signals, page-type fields. Outputs `capture.json`.

| New file | Source lines (≈) | Concern | Est. LOC |
|---|---|---|---|
| `dom.py` (extend) | 109–286 | clean, strip_scripts_styles, heading detection, parasitic H1/H2 filters | +260 |
| `persist.py` (extend) | 59–61, 1013–1032 | write `capture.json`, summary print | +40 |
| `scorer.py` (NEW) | 404–951 | All 150+ data-point extraction, signal detection | 660 |

**Extraction blocks (all → `scorer.py`):**
- 406–485 `extract_ctas()`
- 487–557 `extract_social_proof()`
- 559–595 `extract_images()`
- 597–630 `extract_forms()`
- 633–658 `extract_schemas()`
- 661–695 `extract_navigation()`
- 697–730 `extract_overlays()`
- 732–765 UX signals
- 768–808 psycho + tech signals
- 870–938 page-type specifics
- 943–1011 JSON assembly → `persist.py`

**Env vars:** none.

## Cross-file overlaps

No duplicated functions. Decorator relationship: `ghost_capture_cloud.py` writes `page.html` → `native_capture.py --html <path>` consumes it. After split, both import from shared `dom.py` + `persist.py`.

## Shim plan

`ghost_capture_cloud.py`:
```python
#!/usr/bin/env python3
"""Shim — use growthcro.capture.cli (removed in #11)."""
from growthcro.capture.cli import main
if __name__ == "__main__":
    main()
```

`skills/site-capture/scripts/native_capture.py`:
```python
#!/usr/bin/env python3
"""Shim — use growthcro.capture.scorer (removed in #11)."""
import sys
from growthcro.capture.scorer import main as capture_main
if __name__ == "__main__":
    sys.exit(capture_main())
```

## Final layout

```
growthcro/capture/
├── __init__.py
├── browser.py       (~480 LOC)
├── cloud.py         (~140)
├── dom.py           (~570)  ← shared, ghost+native
├── persist.py       (~150)  ← shared
├── orchestrator.py  (~380)
├── scorer.py        (~660)
└── cli.py           (~75)
```

All ≤ 800 LOC. Total ~2,455 LOC (vs 2,154 original; +14% from helper extraction — acceptable for single-concern clarity).

## Open questions for Mathis

1. **`native_capture.py` argv flow**: keep `scorer.main()` standalone callable (current decorator chain `ghost → native --html <path>` survives), or unify under `growthcro.capture.cli` with subcommand? **Recommendation: keep separate** — preserves chain.
2. **`growthcro.config` API** (from #3): confirm signature is `from growthcro.config import get_env` returning `Optional[str]` with default.
3. **403-detection / Bright Data auto-retry** (capture_page L738–770): extract to `orchestrator.retry_with_fallback()` wrapping `capture_page()` calls, breaking the current circular dep on a nested second `capture_page()`. **Recommendation: yes, extract.**
