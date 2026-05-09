#!/usr/bin/env python3
"""
run_spatial_capture.py — Lance spatial_capture_v9.js pour une page.

Supporte 2 moteurs :
  --engine ghost  (défaut) Playwright local via ghost_capture.js — 0€, rapide
  --engine apify  Apify API (nécessite APIFY_TOKEN) — fallback cloud

Usage :
  python run_spatial_capture.py <url> <label> [pageType] [--engine ghost|apify] [--level N]

Output :
  data/captures/<label>/<pageType>/spatial_v9.json
  data/captures/<label>/<pageType>/screenshots/spatial_fold_desktop.png
  data/captures/<label>/<pageType>/screenshots/spatial_fold_mobile.png
  data/captures/<label>/<pageType>/screenshots/spatial_full_page.png

v2.0 — 2026-04-13 — Ghost engine (local Playwright) par défaut
"""
import os, sys, json, time, pathlib, subprocess, shutil
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
# ──────────────────────────────────────────────
# PARSE ARGS
# ──────────────────────────────────────────────
args = sys.argv[1:]
LEVEL = 1
ENGINE = "ghost"

if "--level" in args:
    i = args.index("--level")
    LEVEL = int(args[i + 1])
    args.pop(i); args.pop(i)

if "--engine" in args:
    i = args.index("--engine")
    ENGINE = args[i + 1].lower()
    args.pop(i); args.pop(i)

if len(args) < 2:
    print("Usage: run_spatial_capture.py <url> <label> [pageType] [--engine ghost|apify] [--level N]", file=sys.stderr)
    sys.exit(1)

URL = args[0]
LABEL = args[1]
PAGE_TYPE = args[2] if len(args) > 2 else "home"

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE
(OUT / "screenshots").mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# GHOST ENGINE (LOCAL PLAYWRIGHT)
# ──────────────────────────────────────────────
def run_ghost():
    ghost_script = SCRIPTS_DIR / "ghost_capture.js"
    if not ghost_script.exists():
        print(f"ERROR: ghost_capture.js not found at {ghost_script}", file=sys.stderr)
        sys.exit(1)

    # Ghost writes to a temp dir, then we move to OUT
    import tempfile
    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="ghost_"))

    print(f"[spatial-v9] engine=GHOST (local Playwright)")
    print(f"[spatial-v9] Capturing {URL} → {OUT}")

    t0 = time.time()
    cmd = [
        "node", str(ghost_script),
        "--url", URL,
        "--label", LABEL,
        "--page-type", PAGE_TYPE,
        "--out-dir", str(tmp_dir),
        "--timeout", "90000",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=str(SCRIPTS_DIR))
    elapsed = round(time.time() - t0, 2)

    # Parse result from stdout
    result = None
    for line in proc.stdout.split("\n"):
        if line.startswith("__GHOST_RESULT__"):
            result = json.loads(line[len("__GHOST_RESULT__"):])
            break

    if proc.returncode != 0 and result is None:
        print(f"ERROR: ghost_capture.js failed (exit {proc.returncode})", file=sys.stderr)
        print(f"  stdout: {proc.stdout[-500:]}", file=sys.stderr)
        print(f"  stderr: {proc.stderr[-500:]}", file=sys.stderr)
        sys.exit(2)

    # Check spatial_v9.json exists
    spatial_json = tmp_dir / "spatial_v9.json"
    if not spatial_json.exists():
        print(f"ERROR: ghost produced no spatial_v9.json", file=sys.stderr)
        sys.exit(3)

    # Load and enrich with metadata
    spatial = json.loads(spatial_json.read_text())
    spatial.setdefault("meta", {})
    spatial["meta"]["pageType"] = PAGE_TYPE
    spatial["meta"]["captureLevel"] = LEVEL
    spatial["meta"]["capturedBy"] = "ghost-playwright-local"
    spatial["meta"]["spatialCapturedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    spatial["meta"]["elapsedSeconds"] = elapsed

    # Save spatial_v9.json to final location
    spatial_out = OUT / "spatial_v9.json"
    spatial_out.write_text(json.dumps(spatial, ensure_ascii=False, indent=2))
    print(f"[spatial-v9] Saved: {spatial_out}")

    # Move screenshots
    tmp_screenshots = tmp_dir / "screenshots"
    dl_count = 0
    if tmp_screenshots.exists():
        for f in tmp_screenshots.iterdir():
            if f.suffix == ".png":
                dest = OUT / "screenshots" / f.name
                shutil.copy2(str(f), str(dest))
                dl_count += 1
                print(f"  [screenshot] {f.name} ({f.stat().st_size // 1024} KB)")

    # Cleanup temp
    shutil.rmtree(str(tmp_dir), ignore_errors=True)

    # Summary
    n_sections = len(spatial.get("sections", []))
    completeness = spatial.get("meta", {}).get("completeness", result.get("completeness", 0))
    print(f"\n[spatial-v9] DONE in {elapsed}s")
    print(f"  Sections: {n_sections}")
    print(f"  Screenshots: {dl_count}")
    print(f"  Completeness: {completeness}")
    print(f"  Output: {spatial_out}")

    return n_sections, completeness, elapsed


# ──────────────────────────────────────────────
# APIFY ENGINE (CLOUD FALLBACK)
# ──────────────────────────────────────────────
def run_apify():
    import urllib.request, urllib.error

    TOKEN = config.apify_token()
    if not TOKEN:
        print("ERROR: APIFY_TOKEN env var missing (required for --engine apify)", file=sys.stderr)
        sys.exit(1)

    SPATIAL_FN_PATH = SKILL_DIR / "references" / "spatial_capture_v9.js"
    if not SPATIAL_FN_PATH.exists():
        print(f"ERROR: {SPATIAL_FN_PATH} not found", file=sys.stderr)
        sys.exit(1)

    SPATIAL_FN = SPATIAL_FN_PATH.read_text()
    KV_PREFIX = f"{LABEL}__{PAGE_TYPE}"
    BASE = "https://api.apify.com/v2"

    LEVEL_CONFIG = {
        1: {"actor": "apify~puppeteer-scraper", "proxy": {"useApifyProxy": True}, "label": "puppeteer-datacenter"},
        2: {"actor": "apify~puppeteer-scraper", "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"], "apifyProxyCountry": "FR"}, "label": "puppeteer-residential-fr"},
    }
    CFG = LEVEL_CONFIG.get(LEVEL, LEVEL_CONFIG[1])
    ACTOR = CFG["actor"]
    print(f"[spatial-v9] engine=APIFY level={LEVEL} actor={ACTOR}")

    def http(method, url, data=None, headers=None):
        req = urllib.request.Request(url, method=method, headers=headers or {})
        if data is not None:
            req.data = data if isinstance(data, bytes) else json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)

    payload = {
        "startUrls": [{"url": URL, "userData": {"label": KV_PREFIX, "captureLevel": LEVEL}}],
        "pageFunction": SPATIAL_FN,
        "proxyConfiguration": CFG["proxy"],
        "pageLoadTimeoutSecs": 180,
        "pageFunctionTimeoutSecs": 300,
        "navigationTimeoutSecs": 180,
        "requestHandlerTimeoutSecs": 480,
        "requestTimeoutSecs": 480,
        "waitUntil": ["domcontentloaded"],
        "maxRequestsPerCrawl": 1,
        "maxRequestRetries": 0,
        "maxPagesPerCrawl": 1,
        "headless": True,
        "injectJQuery": False,
        "injectUnderscore": False,
        "maxScrollHeightPixels": 0,
        "useChrome": True,
    }

    print(f"[spatial-v9] Starting {ACTOR} for {URL}...")
    t0 = time.time()
    status, body, _ = http("POST", f"{BASE}/acts/{ACTOR}/runs?token={TOKEN}", data=payload)
    if status not in (200, 201):
        print(f"ERROR: start run failed {status}: {body[:500]}", file=sys.stderr)
        sys.exit(2)

    run = json.loads(body)["data"]
    run_id = run["id"]
    kv_id = run["defaultKeyValueStoreId"]
    print(f"[spatial-v9] run_id={run_id} kv={kv_id}")

    while True:
        time.sleep(5)
        try:
            s, b, _ = http("GET", f"{BASE}/actor-runs/{run_id}?token={TOKEN}")
            st = json.loads(b)["data"]["status"]
        except Exception as e:
            print(f"  ... poll error: {e}")
            continue
        print(f"  ... status={st}")
        if st in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
            break

    elapsed = round(time.time() - t0, 2)
    if st != "SUCCEEDED":
        print(f"ERROR: run finished with {st} ({elapsed}s)", file=sys.stderr)
        sys.exit(3)

    def get_record(key):
        s, b, _ = http("GET", f"{BASE}/key-value-stores/{kv_id}/records/{key}?token={TOKEN}")
        return b if s == 200 else None

    spatial_raw = get_record(f"{KV_PREFIX}__spatial_v9")
    if not spatial_raw:
        print(f"ERROR: spatial_v9 record missing (key={KV_PREFIX}__spatial_v9)", file=sys.stderr)
        sys.exit(4)

    spatial = json.loads(spatial_raw)
    spatial.setdefault("meta", {})
    spatial["meta"]["pageType"] = PAGE_TYPE
    spatial["meta"]["captureLevel"] = LEVEL
    spatial["meta"]["capturedBy"] = f"spatial-v9-{CFG['label']}"
    spatial["meta"]["spatialCapturedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    spatial["meta"]["elapsedSeconds"] = elapsed

    spatial_out = OUT / "spatial_v9.json"
    spatial_out.write_text(json.dumps(spatial, ensure_ascii=False, indent=2))
    print(f"[spatial-v9] Saved: {spatial_out}")

    screenshot_keys = {
        "fold_desktop": f"{KV_PREFIX}__fold_desktop",
        "fold_mobile": f"{KV_PREFIX}__fold_mobile",
        "full_page": f"{KV_PREFIX}__full_page",
    }
    dl_count = 0
    for local_name, kv_key in screenshot_keys.items():
        data = get_record(kv_key)
        if data:
            out_path = OUT / "screenshots" / f"spatial_{local_name}.png"
            out_path.write_bytes(data)
            dl_count += 1
            print(f"  [screenshot] {local_name} ({len(data) // 1024} KB)")

    n_sections = len(spatial.get("sections", []))
    completeness = spatial.get("meta", {}).get("completeness", 0)
    print(f"\n[spatial-v9] DONE in {elapsed}s")
    print(f"  Sections: {n_sections}")
    print(f"  Screenshots: {dl_count}")
    print(f"  Completeness: {completeness}")
    print(f"  Output: {spatial_out}")

    return n_sections, completeness, elapsed


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if ENGINE == "ghost":
        run_ghost()
    elif ENGINE == "apify":
        run_apify()
    else:
        print(f"ERROR: unknown engine '{ENGINE}'. Use 'ghost' or 'apify'", file=sys.stderr)
        sys.exit(1)
