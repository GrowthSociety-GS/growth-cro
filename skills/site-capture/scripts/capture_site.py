#!/usr/bin/env python3
"""
capture_site.py — Orchestrateur hybride GrowthCRO.

Architecture :
  1. Discover : détecte les pages du site (nav, sitemap, patterns connus)
  2. Capture native (Python fetch) : gratuit, 0.2s/page, données textuelles complètes
  3. Détection SPA automatique : body_words < 50 = flag low_confidence
  4. Score immédiat : 24/28 critères textuels scorés instantanément
  5. Capture Apify (optionnelle) : screenshots + données visuelles pour les 4 critères restants
  6. Score final : merge natif + Apify, agrégation site

Usage :
    python capture_site.py <site_url> <label> [business_category] [--apify] [--level N]

    --apify     Lancer aussi la capture Apify (screenshots + visuels)
    --level N   Niveau proxy Apify (1=datacenter, 2=residential)

Exemples :
    # Natif seulement (gratuit, rapide)
    python capture_site.py https://www.japhy.fr japhy dtc_food

    # Hybride complet (natif + Apify screenshots)
    APIFY_TOKEN=xxx python capture_site.py https://www.japhy.fr japhy dtc_food --apify

    # Hybride avec residential proxy
    APIFY_TOKEN=xxx python capture_site.py https://www.japhy.fr japhy dtc_food --apify --level 2

v1.0 — 2026-04-10
"""

import json, sys, os, re, time, pathlib, subprocess
from datetime import datetime, timezone
from growthcro.config import config
# ── Args ──────────────────────────────────────────────────────
args = sys.argv[1:]
USE_APIFY = False
USE_SPATIAL = False
APIFY_LEVEL = 1

if "--apify" in args:
    USE_APIFY = True
    args.remove("--apify")
if "--spatial" in args:
    USE_SPATIAL = True
    args.remove("--spatial")
if "--level" in args:
    i = args.index("--level")
    APIFY_LEVEL = int(args[i + 1])
    args.pop(i); args.pop(i)

if len(args) < 2:
    print("Usage: capture_site.py <site_url> <label> [business_category] [--apify] [--spatial] [--level N]")
    sys.exit(1)

SITE_URL = args[0].rstrip("/")
LABEL = args[1]
BIZ_CAT = args[2] if len(args) > 2 else "unknown"

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = pathlib.Path(__file__).resolve().parent
CLIENT_DIR = ROOT / "data" / "captures" / LABEL

# ── Business category → page types ───────────────────────────
PAGE_TYPE_CONFIGS = {
    "dtc_food": {
        "primary": ["home"],
        "mandatory": ["pdp", "collection"],
        "optional": ["quiz_vsl", "blog"],
    },
    "dtc_beauty": {
        "primary": ["home"],
        "mandatory": ["pdp", "collection"],
        "optional": ["quiz_vsl", "blog"],
    },
    "saas": {
        "primary": ["home"],
        "mandatory": ["pricing", "lp_leadgen"],
        "optional": ["blog"],
    },
    "lead_gen": {
        "primary": ["home"],
        "mandatory": ["lp_leadgen"],
        "optional": ["blog", "pricing"],
    },
    "ecommerce": {
        "primary": ["home"],
        "mandatory": ["pdp", "collection"],
        "optional": ["checkout", "blog"],
    },
    "app": {
        "primary": ["home"],
        "mandatory": ["pricing"],
        "optional": ["lp_leadgen", "blog"],
    },
    "fintech": {
        "primary": ["home"],
        "mandatory": ["pricing"],
        "optional": ["lp_leadgen", "blog"],
    },
    "unknown": {
        "primary": ["home"],
        "mandatory": [],
        "optional": [],
    },
}

config = PAGE_TYPE_CONFIGS.get(BIZ_CAT, PAGE_TYPE_CONFIGS["unknown"])

# ══════════════════════════════════════════════════════════════
# PHASE 1 : DISCOVER — trouver les URLs des pages
# ══════════════════════════════════════════════════════════════
print("=" * 60)
print(f"CAPTURE SITE — {LABEL}")
print(f"URL: {SITE_URL}")
print(f"Business: {BIZ_CAT}")
mode_str = "NATIF seulement"
if USE_APIFY and USE_SPATIAL: mode_str = "HYBRIDE + SPATIAL V9"
elif USE_APIFY: mode_str = "HYBRIDE (natif + Apify)"
elif USE_SPATIAL: mode_str = "NATIF + SPATIAL V9"
print(f"Mode: {mode_str}")
print("=" * 60)

# ── PHASE 1a : Auto-discover pages si nécessaire ─────────────
DISCOVER_FILE = CLIENT_DIR / "pages_discovered.json"
discovered = None

if DISCOVER_FILE.exists():
    discovered = json.loads(DISCOVER_FILE.read_text())
    n_pages = len(discovered.get("selectedPages", discovered.get("pages", [])))
    print(f"\n📁 pages_discovered.json existant ({n_pages} pages)")

if not discovered or len(discovered.get("selectedPages", discovered.get("pages", []))) < 2:
    # Auto-discover : on lance discover_pages.py qui parse le HTML home existant
    print(f"\n🔍 Auto-discover des pages...")

    # Map businessType to discover_pages categories
    BIZ_DISCOVER_MAP = {
        "ecommerce": "dtc_beauty",  # ecommerce generic → dtc pattern (pdp/collection)
        "dtc_food": "dtc_food",
        "saas": "saas_b2b",
        "lead_gen": "saas_b2c",
        "fintech": "fintech",
        "app": "saas_b2c",
        "unknown": "unknown",
    }
    discover_biz = BIZ_DISCOVER_MAP.get(BIZ_CAT, BIZ_CAT)

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "discover_pages.py"),
         SITE_URL, "--business", discover_biz,
         "--client-id", LABEL, "--max-pages", "5"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0 and DISCOVER_FILE.exists():
        discovered = json.loads(DISCOVER_FILE.read_text())
        n_pages = len(discovered.get("selectedPages", []))
        print(f"  ✅ Discover OK : {n_pages} pages trouvées")
    else:
        print(f"  ⚠️  Discover failed — home only")
        if result.stderr:
            print(f"     {result.stderr[:150]}")
        discovered = {"selectedPages": [], "source": "fallback"}

# ── PHASE 1b : Build page list from discover + config ────────
pages_to_capture = []
all_tiers = []

# Use selectedPages from discover (new format) or pages (old format)
disc_pages = discovered.get("selectedPages", discovered.get("pages", []))

for tier_name in ["primary", "mandatory", "optional"]:
    for pt in config.get(tier_name, []):
        # Try to find URL in discovered pages
        url = None
        for dp in disc_pages:
            if dp.get("pageType") == pt:
                url = dp.get("url")
                break
        if not url:
            if pt == "home":
                url = SITE_URL
            else:
                url = None
        all_tiers.append({"pageType": pt, "tier": tier_name, "url": url})
        if url:
            pages_to_capture.append({"pageType": pt, "tier": tier_name, "url": url})

# Also add discovered pages not in config (e.g., discover found a blog for an ecommerce)
config_types = {pt for tier in ["primary", "mandatory", "optional"] for pt in config.get(tier, [])}
for dp in disc_pages:
    pt = dp.get("pageType", "unknown")
    if pt not in config_types and pt != "unknown" and pt != "home" and dp.get("url"):
        pages_to_capture.append({"pageType": pt, "tier": dp.get("tier", "optional"), "url": dp["url"]})
        all_tiers.append({"pageType": pt, "tier": dp.get("tier", "optional"), "url": dp["url"]})

print(f"\n📋 Pages à capturer ({BIZ_CAT}):")
for p in all_tiers:
    status = "✅" if p.get("url") else "❌ URL manquante"
    print(f"  [{p['tier'][:3]}] {p['pageType']:12s} {status} {(p.get('url') or '')[:60]}")

if not pages_to_capture:
    print("\n❌ Aucune page à capturer")
    sys.exit(2)

# ══════════════════════════════════════════════════════════════
# PHASE 2 : CAPTURE NATIVE (Python fetch)
# ══════════════════════════════════════════════════════════════
print(f"\n{'═' * 60}")
print("PHASE 2 : CAPTURE NATIVE (Python fetch)")
print(f"{'═' * 60}")

native_results = {}
t_total = time.time()

for page in pages_to_capture:
    pt = page["pageType"]
    url = page["url"]
    print(f"\n  ⏳ [{pt}] {url[:60]}...")

    t0 = time.time()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "native_capture.py"), url, LABEL, pt],
        capture_output=True, text=True, timeout=30,
    )
    elapsed = round(time.time() - t0, 2)

    if result.returncode == 0:
        # Check capture quality
        cap_file = CLIENT_DIR / pt / "capture.json"
        if cap_file.exists():
            cap = json.loads(cap_file.read_text())
            confidence = cap.get("meta", {}).get("confidence", "unknown")
            h1 = cap.get("hero", {}).get("h1", "")[:50]
            n_ctas = len(cap.get("structure", {}).get("ctas", []))
            n_headings = len(cap.get("structure", {}).get("headings", []))
            spa = confidence == "low"

            native_results[pt] = {
                "status": "ok",
                "confidence": confidence,
                "spa": spa,
                "elapsed": elapsed,
                "h1": h1,
                "ctas": n_ctas,
                "headings": n_headings,
            }
            icon = "⚠️ SPA" if spa else "✅"
            print(f"  {icon} [{pt}] {elapsed}s — H1:'{h1}' CTAs:{n_ctas} Headings:{n_headings} ({confidence})")
        else:
            native_results[pt] = {"status": "error", "msg": "capture.json not created"}
            print(f"  ❌ [{pt}] capture.json not found")
    else:
        native_results[pt] = {"status": "error", "msg": result.stderr[:200]}
        print(f"  ❌ [{pt}] {result.stderr[:100]}")

native_time = round(time.time() - t_total, 2)
ok_count = sum(1 for r in native_results.values() if r["status"] == "ok")
spa_count = sum(1 for r in native_results.values() if r.get("spa"))
print(f"\n  📊 Natif terminé: {ok_count}/{len(pages_to_capture)} OK, {spa_count} SPA détectées, {native_time}s total")

# ══════════════════════════════════════════════════════════════
# PHASE 3 : SCORING IMMÉDIAT (critères textuels)
# ══════════════════════════════════════════════════════════════
print(f"\n{'═' * 60}")
print("PHASE 3 : SCORING IMMÉDIAT (critères textuels)")
print(f"{'═' * 60}")

SCORERS = [
    ("hero", "score_hero.py"),
    ("persuasion", "score_persuasion.py"),
    ("ux", "score_ux.py"),
    ("coherence", "score_coherence.py"),
    ("psycho", "score_psycho.py"),
    ("tech", "score_tech.py"),
]

scoring_results = {}

for page in pages_to_capture:
    pt = page["pageType"]
    nr = native_results.get(pt, {})
    if nr.get("status") != "ok":
        print(f"\n  ⏭️  [{pt}] Skipped (capture failed)")
        continue
    if nr.get("spa"):
        print(f"\n  ⚠️  [{pt}] SPA détecté — scoring partiel (données textuelles insuffisantes)")
        # Score anyway but flag as low confidence

    page_scores = {}
    for pillar, scorer_file in SCORERS:
        scorer_path = SCRIPTS / scorer_file
        if not scorer_path.exists():
            continue
        result = subprocess.run(
            [sys.executable, str(scorer_path), LABEL, pt],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            # Parse score from output
            score_file = CLIENT_DIR / pt / f"score_{pillar}.json"
            if score_file.exists():
                data = json.loads(score_file.read_text())
                s100 = data.get("score100", 0)
                page_scores[pillar] = s100
                # Extract short summary from stdout
                for line in result.stdout.strip().split("\n"):
                    if f"{pillar}" in line.lower() and "/100" in line:
                        print(f"  {line.strip()}")
                        break
        else:
            print(f"  ❌ [{pt}] {pillar} scorer failed: {result.stderr[:80]}")

    scoring_results[pt] = page_scores

# ══════════════════════════════════════════════════════════════
# PHASE 4 : APIFY (optionnel — screenshots + visuels)
# ══════════════════════════════════════════════════════════════
if USE_APIFY:
    print(f"\n{'═' * 60}")
    print("PHASE 4 : ENRICHISSEMENT APIFY (screenshots + données visuelles)")
    print(f"{'═' * 60}")

    token = config.apify_token()
    if not token:
        print("  ⚠️  APIFY_TOKEN non défini — skip Apify")
    else:
        apify_results = {}
        for page in pages_to_capture:
            pt = page["pageType"]
            url = page["url"]
            nr = native_results.get(pt, {})
            if nr.get("status") != "ok":
                print(f"\n  ⏭️  [{pt}] Skipped (native capture failed)")
                continue

            level = APIFY_LEVEL
            # SPA pages → force residential
            if nr.get("spa"):
                level = max(level, 2)
                print(f"\n  🔄 [{pt}] SPA → RESIDENTIAL proxy (level {level})")
            else:
                print(f"\n  🔄 [{pt}] Enrichissement visuel (level {level})")

            t_apify = time.time()
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "apify_enrich.py"), LABEL, pt, url, "--level", str(level)],
                capture_output=True, text=True, timeout=360,
                env={**config.system_env_copy(), "APIFY_TOKEN": token},
            )
            t_apify = round(time.time() - t_apify, 2)

            if result.returncode == 0:
                apify_results[pt] = {"status": "ok", "elapsed": t_apify}
                print(f"  ✅ [{pt}] Enrichi en {t_apify}s")
                # Show enrichment summary from stdout
                for line in result.stdout.strip().split("\n"):
                    if "Enriched fields" in line or "Screenshots" in line or "Hero CTAs" in line:
                        print(f"    {line.strip()}")
            else:
                apify_results[pt] = {"status": "error", "msg": result.stderr[:200]}
                print(f"  ❌ [{pt}] Enrichissement failed ({t_apify}s): {result.stderr[:100]}")

        apify_ok = sum(1 for r in apify_results.values() if r["status"] == "ok")
        print(f"\n  📊 Apify enrichissement: {apify_ok}/{len(apify_results)} OK")

        # Re-score ALL pages with enriched data
        print(f"\n  🔄 Re-scoring avec données enrichies...")
        for page in pages_to_capture:
            pt = page["pageType"]
            nr = native_results.get(pt, {})
            if nr.get("status") != "ok":
                continue

            page_scores = {}
            for pillar, scorer_file in SCORERS:
                scorer_path = SCRIPTS / scorer_file
                if not scorer_path.exists():
                    continue
                result = subprocess.run(
                    [sys.executable, str(scorer_path), LABEL, pt],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode == 0:
                    score_file = CLIENT_DIR / pt / f"score_{pillar}.json"
                    if score_file.exists():
                        data = json.loads(score_file.read_text())
                        s100 = data.get("score100", 0)
                        page_scores[pillar] = s100
                        for line in result.stdout.strip().split("\n"):
                            if f"{pillar}" in line.lower() and "/100" in line:
                                print(f"  {line.strip()}")
                                break

            scoring_results[pt] = page_scores
else:
    print(f"\n  ℹ️  Mode natif seulement (pas de --apify)")
    print(f"  → 24/28 critères scorés à 100% de précision")
    print(f"  → 4 critères visuels en mode estimation (hero_03 taille, hero_04 visuel, hero_06 focus, ux_05 touch)")
    print(f"  → Pas de screenshots")
    print(f"  → Pour le mode complet: ajoutez --apify")

# ══════════════════════════════════════════════════════════════
# PHASE 4b : SPATIAL V9 CAPTURE (optionnel — Perception Tree + screenshots)
# ══════════════════════════════════════════════════════════════
spatial_results = {}
if USE_SPATIAL:
    print(f"\n{'═' * 60}")
    print("PHASE 4b : SPATIAL V9 CAPTURE (Perception Tree)")
    print(f"{'═' * 60}")

    token = config.apify_token()
    if not token:
        print("  ⚠️  APIFY_TOKEN non défini — skip spatial capture")
    else:
        for page in pages_to_capture:
            pt = page["pageType"]
            url = page["url"]
            nr = native_results.get(pt, {})
            if nr.get("status") != "ok":
                print(f"\n  ⏭️  [{pt}] Skipped (native capture failed)")
                continue

            level = APIFY_LEVEL
            if nr.get("spa"):
                level = max(level, 2)
                print(f"\n  🔄 [{pt}] SPA → RESIDENTIAL proxy (level {level})")
            else:
                print(f"\n  📐 [{pt}] Spatial V9 capture (level {level})")

            t_sp = time.time()
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "run_spatial_capture.py"), url, LABEL, pt, "--level", str(level)],
                capture_output=True, text=True, timeout=480,
                env={**config.system_env_copy(), "APIFY_TOKEN": token},
            )
            t_sp = round(time.time() - t_sp, 2)

            if result.returncode == 0:
                spatial_results[pt] = {"status": "ok", "elapsed": t_sp}
                print(f"  ✅ [{pt}] Spatial V9 OK ({t_sp}s)")
                for line in result.stdout.strip().split("\n"):
                    if "Sections:" in line or "Completeness:" in line:
                        print(f"    {line.strip()}")
            else:
                spatial_results[pt] = {"status": "error", "msg": result.stderr[:200]}
                print(f"  ❌ [{pt}] Spatial failed ({t_sp}s): {result.stderr[:100]}")

        sp_ok = sum(1 for r in spatial_results.values() if r["status"] == "ok")
        print(f"\n  📊 Spatial V9: {sp_ok}/{len(spatial_results)} OK")

        # Re-score with spatial data now available
        if sp_ok > 0:
            print(f"\n  🔄 Re-scoring avec données spatiales V9...")
            for page in pages_to_capture:
                pt = page["pageType"]
                nr = native_results.get(pt, {})
                if nr.get("status") != "ok":
                    continue

                page_scores = {}
                for pillar, scorer_file in SCORERS:
                    scorer_path = SCRIPTS / scorer_file
                    if not scorer_path.exists():
                        continue
                    result = subprocess.run(
                        [sys.executable, str(scorer_path), LABEL, pt],
                        capture_output=True, text=True, timeout=60,
                    )
                    if result.returncode == 0:
                        score_file = CLIENT_DIR / pt / f"score_{pillar}.json"
                        if score_file.exists():
                            data = json.loads(score_file.read_text())
                            s100 = data.get("score100", 0)
                            page_scores[pillar] = s100

                scoring_results[pt] = page_scores
else:
    if not USE_APIFY:
        pass  # Already printed no-apify message above

# ══════════════════════════════════════════════════════════════
# PHASE 5 : AGRÉGATION SITE
# ══════════════════════════════════════════════════════════════
print(f"\n{'═' * 60}")
print("PHASE 5 : AGRÉGATION SITE")
print(f"{'═' * 60}")

result = subprocess.run(
    [sys.executable, str(SCRIPTS / "score_site.py"), LABEL, BIZ_CAT],
    capture_output=True, text=True, timeout=60,
)
print(result.stdout)
if result.stderr:
    print(result.stderr)

# ══════════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ══════════════════════════════════════════════════════════════
total_time = round(time.time() - t_total, 2)

print(f"\n{'═' * 60}")
print(f"TERMINÉ en {total_time}s")
print(f"{'═' * 60}")
print(f"  Mode: {mode_str}")
print(f"  Pages capturées: {ok_count}/{len(pages_to_capture)}")
print(f"  SPA détectées: {spa_count}")
if USE_SPATIAL:
    sp_ok = sum(1 for r in spatial_results.values() if r["status"] == "ok")
    print(f"  Spatial V9: {sp_ok}/{len(spatial_results)} pages")
apify_cost = ok_count * 0.01 if USE_APIFY else 0
spatial_cost = ok_count * 0.01 if USE_SPATIAL else 0
total_cost = apify_cost + spatial_cost
print(f"  Coût Apify: ~${total_cost:.2f}")
print(f"  Résultats: {CLIENT_DIR}/site_audit.json")

# Save orchestration metadata
mode_name = "native"
if USE_APIFY and USE_SPATIAL: mode_name = "hybrid+spatial"
elif USE_APIFY: mode_name = "hybrid"
elif USE_SPATIAL: mode_name = "native+spatial"
meta = {
    "label": LABEL,
    "siteUrl": SITE_URL,
    "businessCategory": BIZ_CAT,
    "mode": mode_name,
    "apifyLevel": APIFY_LEVEL if USE_APIFY else None,
    "capturedAt": datetime.now(timezone.utc).isoformat(),
    "totalTimeSeconds": total_time,
    "nativeTimeSeconds": native_time,
    "pagesAttempted": len(pages_to_capture),
    "pagesOk": ok_count,
    "spaDetected": spa_count,
    "nativeResults": native_results,
    "scoringResults": scoring_results,
}
meta_file = CLIENT_DIR / "capture_meta.json"
meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
print(f"  Metadata: {meta_file}")
