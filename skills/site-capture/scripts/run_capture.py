#!/usr/bin/env python3
"""
run_capture.py — orchestrateur Apify pour site-capture.

Usage :
  APIFY_TOKEN=apify_api_xxx python run_capture.py <url> <label> [pageType] [businessCategory] [--level N]

Niveaux (cascade documentée dans references/backend_cascade.md) :
  --level 1  Puppeteer datacenter (défaut, 80-90% des sites)
  --level 2  Puppeteer + RESIDENTIAL FR (sites WAF/geo/IP-burn — everever, fichet)
  --level 3  Playwright + Firefox + RESIDENTIAL FR (bot detection JS Chrome-only)
  --level 4  Puppeteer + slowMo + human scroll simulation (anti-bot comportemental)
  --level 5  Sandbox local Playwright Python (backend hors Apify, 0 CU)
  --level 6  curl_cffi + selectolax (HTML statique only, completeness 0.3)

Lance l'actor correspondant, télécharge capture.json + 6 PNG + html dans data/captures/<label>/.
Tag `capturedBy` + `confidence` dans capture.json pour traçabilité.
"""
import sys
import json
import time
import pathlib
import urllib.request
import urllib.error
from growthcro.config import config
TOKEN = config.apify_token()
if not TOKEN:
    print("ERROR: APIFY_TOKEN env var missing", file=sys.stderr); sys.exit(1)

# Parse args
args = sys.argv[1:]
LEVEL = 1
if "--level" in args:
    i = args.index("--level")
    LEVEL = int(args[i+1])
    args.pop(i); args.pop(i)

if len(args) < 2:
    print("Usage: run_capture.py <url> <label> [pageType] [businessCategory] [--level N]", file=sys.stderr); sys.exit(1)

URL = args[0]
LABEL = args[1]
PAGE_TYPE = args[2] if len(args) > 2 else "home"
BIZ_CAT   = args[3] if len(args) > 3 else None

ROOT = pathlib.Path(__file__).resolve().parents[3]  # project root
SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
PAGE_FN = (SKILL_DIR / "references" / "apify_page_function.js").read_text()
# Multi-page storage: data/captures/<label>/<pageType>/
OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE
(OUT / "screenshots").mkdir(parents=True, exist_ok=True)
# KV Store key prefix includes pageType to avoid collisions
KV_PREFIX = f"{LABEL}__{PAGE_TYPE}"

BASE = "https://api.apify.com/v2"

# Level-based actor + payload overrides
LEVEL_CONFIG = {
    1: {
        "actor": "apify~puppeteer-scraper",
        "proxy": {"useApifyProxy": True},
        "label": "puppeteer-datacenter",
        "confidence": "high",
    },
    2: {
        "actor": "apify~puppeteer-scraper",
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"], "apifyProxyCountry": "FR"},
        "label": "puppeteer-residential-fr",
        "confidence": "high",
    },
    3: {
        "actor": "apify~playwright-scraper",
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"], "apifyProxyCountry": "FR"},
        "browser": "firefox",
        "label": "playwright-firefox-residential",
        "confidence": "high",
    },
    4: {
        "actor": "apify~puppeteer-scraper",
        "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"], "apifyProxyCountry": "FR"},
        "slowMo": True,
        "label": "puppeteer-human-residential",
        "confidence": "medium",
    },
}
if LEVEL not in LEVEL_CONFIG:
    print(f"ERROR: level {LEVEL} not implemented via Apify (see references/backend_cascade.md for levels 5-6)", file=sys.stderr)
    sys.exit(1)
CFG = LEVEL_CONFIG[LEVEL]
ACTOR = CFG["actor"]
print(f"[level {LEVEL}] actor={ACTOR} proxy={CFG['proxy'].get('apifyProxyGroups',['DATACENTER'])[0]}")

def http(method, url, data=None, headers=None):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    if data is not None:
        req.data = data if isinstance(data, bytes) else json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

payload = {
    "startUrls": [{"url": URL, "userData": {"label": KV_PREFIX, "captureLevel": LEVEL, "capturedBy": CFG["label"]}}],
    "pageFunction": PAGE_FN,
    "proxyConfiguration": CFG["proxy"],
    "pageLoadTimeoutSecs": 180,
    "pageFunctionTimeoutSecs": 300,
    "navigationTimeoutSecs": 180,
    "requestHandlerTimeoutSecs": 480,
    "requestTimeoutSecs": 480,
    "waitUntil": ["domcontentloaded"] if LEVEL != 3 else "domcontentloaded",
    "maxRequestsPerCrawl": 1,
    "maxRequestRetries": 0,
    "maxPagesPerCrawl": 1,
    "headless": True,
    # Crawlee pre-pageFunction behaviors — disable to prevent "Execution context destroyed" on sites with JS redirects
    "injectJQuery": False,
    "injectUnderscore": False,
    # maxScrollHeightPixels=0 disables Crawlee's auto-infiniteScroll which crashed on jomarine
    "maxScrollHeightPixels": 0,
}
if LEVEL == 3:
    payload["launcher"] = CFG.get("browser", "firefox")
else:
    payload["useChrome"] = True
if LEVEL == 4:
    payload["launchContext"] = {"launchOptions": {"slowMo": 50}}

print(f"[run] Starting actor {ACTOR} for {URL}…")
status, body, _ = http("POST", f"{BASE}/acts/{ACTOR}/runs?token={TOKEN}", data=payload)
if status not in (200, 201):
    print(f"ERROR: start run failed {status}: {body[:500]}"); sys.exit(2)
run = json.loads(body)["data"]
run_id = run["id"]; kv_id = run["defaultKeyValueStoreId"]
print(f"[run] id={run_id} kvStore={kv_id}")

# Wait for completion
while True:
    time.sleep(5)
    try:
        s, b, _ = http("GET", f"{BASE}/actor-runs/{run_id}?token={TOKEN}")
        st = json.loads(b)["data"]["status"]
    except Exception as e:
        print(f"  … poll error (retry): {e}")
        continue
    print(f"  … status={st}")
    if st in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"):
        break
if st != "SUCCEEDED":
    print(f"ERROR: run finished with {st}"); sys.exit(3)

# Download keys
def get_record(key, binary=False):
    s, b, _ = http("GET", f"{BASE}/key-value-stores/{kv_id}/records/{key}?token={TOKEN}")
    if s != 200: return None
    return b if binary else b

cap_raw = get_record(f"{KV_PREFIX}__capture")
if not cap_raw:
    print(f"ERROR: capture record missing (key={KV_PREFIX}__capture)"); sys.exit(4)
capture = json.loads(cap_raw)

# Add context + backend traceability
capture.setdefault("meta", {})
capture["meta"]["pageType"] = PAGE_TYPE
if BIZ_CAT: capture["meta"]["businessCategory"] = BIZ_CAT
capture["meta"]["captureLevel"] = LEVEL
capture["meta"]["capturedBy"] = CFG["label"]
capture["meta"]["confidence"] = CFG["confidence"]

# Download screenshots
for local, key in capture["screenshots"].items():
    data = get_record(key, binary=True)
    if data:
        (OUT / "screenshots" / f"{local}.png").write_bytes(data)
        capture["screenshots"][local] = f"screenshots/{local}.png"
        print(f"  ✓ {local}.png ({len(data)//1024} KB)")

# HTML
html = get_record(f"{KV_PREFIX}__html", binary=True)
if html:
    (OUT / "page.html").write_bytes(html)
    capture["rawHtml"] = "page.html"

(OUT / "capture.json").write_text(json.dumps(capture, ensure_ascii=False, indent=2))
print(f"[done] {OUT / 'capture.json'}")
