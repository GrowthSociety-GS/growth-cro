# growthcro.capture

Acquires the rendered DOM + screenshots + spatial signals for a target page.
Single source of truth for the "what does this page look like?" half of the pipeline.

## Modules
- `cli.py` — argparse entrypoint (was `ghost_capture_cloud.py`). Drives `orchestrator`.
- `orchestrator.py` — `run_single` / `run_batch` (Playwright local OR Browserless cloud).
- `browser.py` — Chromium launch + stealth tweaks.
- `cloud.py` — Browserless / Brightdata adapter.
- `dom.py` — DOM serialization → `page.html`.
- `signals.py` — spatial bbox extraction → `spatial_v9.json`.
- `persist.py` — writes `capture.json` meta + outputs.
- `scorer.py` — DOM → `capture.json` (6 piliers, was `native_capture.py`).

## Entrypoints
```bash
python -m growthcro.capture.cli --url <url> --label <label> --page-type <pt> --out-dir <path>
python -m growthcro.capture.scorer <url> <label> <page_type> [--html <path>]
```

## Imports from
- `growthcro.config` (Browserless WS endpoint, residential proxy creds).
- `playwright.sync_api`.

## Imported by
- `growthcro.cli.capture_full` (orchestrates all 4 stages).
