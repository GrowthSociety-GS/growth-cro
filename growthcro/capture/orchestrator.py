"""Single + batch capture pipelines — single concern: orchestration.

Coordinates browser → page → screenshots → DOM extraction → persistence.
Owns the 403/Bright-Data fallback (`retry_with_fallback`) which used to
recurse inside `capture_page`; the recursion is now broken explicitly.
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import random
import time
from typing import Optional

from .browser import get_browser, handle_cookies, new_stealth_context
from .cloud import get_brightdata_endpoint
from .dom import ANNOTATE_JS, REMOVE_ANNOTATIONS_JS, load_extraction_js
from .persist import assemble_spatial_v9, write_html, write_spatial_v9


# ══════════════════════════════════════════════════════════════
# SINGLE PAGE CAPTURE
# ══════════════════════════════════════════════════════════════
async def capture_page(
    browser,
    url: str,
    label: str,
    page_type: str,
    out_dir: pathlib.Path,
    timeout: int = 120000,
    extraction_js: str = "",
    _is_brightdata_retry: bool = False,
) -> dict:
    """
    Capture une page complète — identique à ghost_capture.js capturePage().

    Produit :
        - spatial_v9.json (perception tree + bbox clusters)
        - page.html (DOM rendered complet)
        - screenshots/ (fold desktop, fold mobile, full page, annotated)
    """
    t0 = time.time()
    screenshots_dir = out_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    errors: list = []
    stages: list = []
    perception_tree = None
    completeness = 0.0
    nodes = 0
    text_len = 0
    attempt = 0

    # Create stealth context + page
    context = await new_stealth_context(browser)
    page = await context.new_page()
    page.set_default_timeout(timeout)
    page.set_default_navigation_timeout(timeout)

    try:
        # ── Navigate ──
        print(f"  ⏳ Navigation vers {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=min(timeout, 60000))
        # Wait for lazy-loaded content
        await page.wait_for_timeout(3000)
        # Try networkidle (but don't block)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        stages.append("navigate")

        # ── Stage 0.5: Human behavior (anti-bot evasion) ──
        try:
            await page.mouse.move(random.randint(100, 800), random.randint(100, 400))
            await page.wait_for_timeout(random.randint(200, 500))
            await page.mouse.move(random.randint(300, 1000), random.randint(200, 600))
            await page.wait_for_timeout(random.randint(100, 300))
            for scroll_y in [200, 400, 300, 100, 0]:
                await page.evaluate(f"() => window.scrollTo({{top: {scroll_y}, behavior: 'smooth'}})")
                await page.wait_for_timeout(random.randint(300, 700))
        except Exception:
            pass

        # ── Stage 1: Settle (SPA-aware) ──
        for attempt in range(6):  # max 6 × 2s = 12s d'attente SPA
            body_stats = await page.evaluate("""() => {
                const body = document.body;
                if (!body) return {nodes: 0, text: 0};
                return {
                    nodes: body.querySelectorAll('*').length,
                    text: body.innerText.length
                };
            }""")
            nodes = body_stats.get("nodes", 0)
            text_len = body_stats.get("text", 0)
            if nodes > 50 or text_len > 500:
                break
            if attempt < 5:
                await page.wait_for_timeout(2000)
                await page.evaluate("() => { window.scrollTo(0, 300); window.scrollTo(0, 0); }")
        if nodes <= 50 and text_len <= 500:
            print(f"  ⚠️  SPA lent : {nodes} nodes, {text_len} chars après {(attempt+1)*2}s d'attente")
        else:
            print(f"  ✅ Contenu rendu : {nodes} nodes, {text_len} chars")
        stages.append("settle")

        # ── 403 / Bot-block Detection + Bright Data Auto-Retry ──
        if not _is_brightdata_retry:
            block_check = await page.evaluate("""() => {
                const h1 = document.querySelector('h1');
                const title = document.title || '';
                const body = (document.body && document.body.innerText) || '';
                const is403 = (h1 && /403|ERROR|Forbidden|Access Denied/i.test(h1.textContent))
                    || /403 ERROR|Request blocked|Access Denied/i.test(title)
                    || (body.length < 2000 && /CloudFront|Request blocked|security service|Forbidden/i.test(body));
                return { blocked: is403, h1: h1 ? h1.textContent.trim().slice(0, 100) : '', title: title.slice(0, 100) };
            }""")
            if block_check.get("blocked"):
                bd_endpoint = get_brightdata_endpoint()
                if bd_endpoint:
                    print(f"  🚫 BLOQUÉ (403) — H1: \"{block_check.get('h1', '')}\"")
                    print(f"  🔶 Retry automatique via Bright Data Scraping Browser...")
                    await context.close()
                    result = await retry_with_fallback(
                        url, label, page_type, out_dir, timeout, extraction_js,
                    )
                    return result
                else:
                    print(f"  🚫 BLOQUÉ (403) — H1: \"{block_check.get('h1', '')}\"")
                    print(f"  ⚠️  Pas de Bright Data configuré. Pour activer le fallback automatique :")
                    print(f"      export BRIGHTDATA_AUTH='brd-customer-XXX-zone-scraping_browser:PASSWORD'")

        # ── Stage 2: Fold desktop screenshot ──
        try:
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(600)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_fold_desktop.png"), type="png"
            )
            stages.append("fold_desktop")
        except Exception as e:
            errors.append({"stage": "fold_desktop", "msg": str(e)[:200]})

        # ── Stage 2b: Fold mobile screenshot ──
        try:
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(600)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_fold_mobile.png"), type="png"
            )
            stages.append("fold_mobile")
            # Reset to desktop
            await page.set_viewport_size({"width": 1440, "height": 900})
            await page.wait_for_timeout(300)
        except Exception as e:
            errors.append({"stage": "fold_mobile", "msg": str(e)[:200]})

        # ── Stage 3: Cookie handling ──
        try:
            cookie_method = await handle_cookies(page)
            await page.wait_for_timeout(800)
            stages.append("cookie_dismiss")
            if cookie_method != "none":
                print(f"  🍪 Cookie banner handled ({cookie_method})")
        except Exception as e:
            errors.append({"stage": "cookie_dismiss", "msg": str(e)[:200]})

        # ── Stage 3.5: Deep scroll (trigger lazy-loading for SPAs) ──
        try:
            total_h = await page.evaluate("() => document.body.scrollHeight")
            pos = 0
            scroll_passes = 0
            while pos < total_h and scroll_passes < 60:  # cap 60 steps (~48000px max)
                pos += 800
                await page.evaluate(f"() => window.scrollTo({{top: {pos}, behavior: 'smooth'}})")
                await page.wait_for_timeout(400)
                scroll_passes += 1
                new_h = await page.evaluate("() => document.body.scrollHeight")
                if new_h > total_h:
                    total_h = new_h
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(800)
            final_h = await page.evaluate("() => document.body.scrollHeight")
            final_nodes = await page.evaluate("() => document.body.querySelectorAll('*').length")
            print(f"  📜 Deep scroll: {scroll_passes} steps, {total_h}→{final_h}px, {final_nodes} nodes")
            stages.append("deep_scroll")
        except Exception as e:
            errors.append({"stage": "deep_scroll", "msg": str(e)[:200]})

        # ── Stage 4: Perception tree extraction ──
        if extraction_js:
            try:
                wrapped = f"(async () => {{ {extraction_js} }})()"
                perception_tree = await page.evaluate(wrapped)
                completeness = 0.8
                stages.append("extract")
            except Exception as e:
                errors.append({"stage": "extract", "msg": str(e)[:400]})
                print(f"  ⚠️  Extract error: {str(e)[:200]}")
        else:
            print(f"  ⚠️  Extraction JS non chargé — spatial_v9 sera vide")

        # ── Stage 5: Full page screenshot (clean) ──
        try:
            await page.set_viewport_size({"width": 1440, "height": 900})
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(400)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_full_page.png"),
                type="png",
                full_page=True,
            )
            stages.append("full_page")
        except Exception as e:
            errors.append({"stage": "full_page", "msg": str(e)[:200]})

        # ── Stage 5b: Dump rendered HTML ──
        try:
            rendered_html = await page.content()
            write_html(out_dir, rendered_html)
            html_kb = len(rendered_html) / 1024
            print(f"  💾 page.html dumped ({html_kb:.1f} KB rendered DOM)")
            stages.append("dump_html")
        except Exception as e:
            errors.append({"stage": "dump_html", "msg": str(e)[:200]})

        # ── Stage 6: Annotated screenshot ──
        try:
            await page.evaluate("() => window.scrollTo(0, 0)")
            await page.wait_for_timeout(300)
            await page.evaluate(ANNOTATE_JS)
            await page.screenshot(
                path=str(screenshots_dir / "spatial_annotated_desktop.png"),
                type="png",
                full_page=True,
            )
            await page.evaluate(REMOVE_ANNOTATIONS_JS)
            stages.append("annotated_screenshot")
        except Exception as e:
            errors.append({"stage": "annotated_screenshot", "msg": str(e)[:200]})

        # Completeness
        completeness = 1.0 if ("extract" in stages and "full_page" in stages) else 0.8

    except Exception as e:
        errors.append({"stage": "navigation", "msg": str(e)[:300]})

    # ── Build and save spatial_v9.json ──
    final_capture = assemble_spatial_v9(
        url=url, label=label, page_type=page_type,
        perception_tree=perception_tree, stages=stages,
        errors=errors, completeness=completeness,
    )
    write_spatial_v9(out_dir, final_capture)

    elapsed = time.time() - t0
    sections = len(final_capture.get("sections", []))

    await context.close()

    return {
        "ok": len(errors) == 0 or completeness >= 0.8,
        "label": label,
        "pageType": page_type,
        "sections": sections,
        "completeness": completeness,
        "elapsed": f"{elapsed:.1f}",
        "errors": errors,
        "stages": stages,
    }


# ══════════════════════════════════════════════════════════════
# 403 → BRIGHT DATA FALLBACK (extracted from nested capture_page)
# ══════════════════════════════════════════════════════════════
async def retry_with_fallback(url: str, label: str, page_type: str,
                              out_dir: pathlib.Path, timeout: int,
                              extraction_js: str) -> dict:
    """Re-run capture_page through Bright Data after a 403/CloudFront block.

    Owns the second Playwright instance — breaks the previous self-recursion
    inside capture_page where it imported async_playwright mid-flight.
    """
    from playwright.async_api import async_playwright
    async with async_playwright() as pw_bd:
        bd_browser = await get_browser(pw_bd, cloud=False, force_brightdata=True)
        result = await capture_page(
            bd_browser, url, label, page_type, out_dir,
            timeout, extraction_js, _is_brightdata_retry=True,
        )
        await bd_browser.close()
        result["brightdata_retry"] = True
        return result


# ══════════════════════════════════════════════════════════════
# BATCH MODE
# ══════════════════════════════════════════════════════════════
async def run_batch(pw, batch_file: str, cloud: bool, ws_endpoint: Optional[str],
                    concurrency: int, delay: int, timeout: int, out_base: str):
    """Exécute un batch de captures (même API que ghost_capture.js --batch)."""
    tasks = json.loads(pathlib.Path(batch_file).read_text())
    extraction_js = load_extraction_js()

    print(f"\n{'='*60}")
    print(f"GHOST CAPTURE CLOUD — BATCH MODE")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Mode: {'CLOUD' if cloud else 'LOCAL'}")
    print(f"  Concurrency: {concurrency}")
    print(f"{'='*60}\n")

    browser = await get_browser(pw, cloud, ws_endpoint)
    RESTART_EVERY = 10
    chunk_counter = 0
    results = []
    completed = 0

    for i in range(0, len(tasks), concurrency):
        # Restart browser periodically
        if chunk_counter > 0 and (chunk_counter % RESTART_EVERY == 0):
            try:
                await browser.close()
            except Exception:
                pass
            print(f"  [browser] relancement après {chunk_counter} chunks")
            browser = await get_browser(pw, cloud, ws_endpoint)

        chunk = tasks[i : i + concurrency]

        async def process_task(task):
            nonlocal completed
            task_out = pathlib.Path(task.get("outDir", f"{out_base}/{task['label']}/{task['pageType']}"))
            try:
                result = await capture_page(
                    browser, task["url"], task["label"], task["pageType"],
                    task_out, timeout, extraction_js,
                )
                completed += 1
                status = "✅" if result["ok"] else "❌"
                print(f"  [{completed}/{len(tasks)}] {status} {task['label']}/{task['pageType']}: "
                      f"{result['sections']} sections ({result['elapsed']}s)")
                return result
            except Exception as e:
                completed += 1
                print(f"  [{completed}/{len(tasks)}] ❌ {task['label']}/{task['pageType']}: {str(e)[:100]}")
                return {"ok": False, "label": task["label"], "pageType": task["pageType"], "error": str(e)[:200]}

        chunk_results = await asyncio.gather(*[process_task(t) for t in chunk])
        results.extend(chunk_results)
        chunk_counter += 1

        if i + concurrency < len(tasks):
            await asyncio.sleep(delay / 1000)

    try:
        await browser.close()
    except Exception:
        pass

    ok_count = sum(1 for r in results if r.get("ok"))
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE — {ok_count}/{len(results)} OK")
    print(f"{'='*60}\n")
    return results


# ══════════════════════════════════════════════════════════════
# SINGLE MODE (top-level entry point used by the CLI)
# ══════════════════════════════════════════════════════════════
async def run_single(pw, url: str, label: str, page_type: str, out_dir: str,
                     cloud: bool, ws_endpoint: Optional[str], timeout: int,
                     force_brightdata: bool = False):
    """Capture une seule page (mode par défaut)."""
    extraction_js = load_extraction_js()
    out_path = pathlib.Path(out_dir)

    if force_brightdata:
        mode_str = "BRIGHT DATA"
    elif cloud:
        mode_str = "CLOUD"
    else:
        bd_available = get_brightdata_endpoint() is not None
        mode_str = "LOCAL" + (" + Bright Data fallback" if bd_available else "")

    print(f"\n{'='*60}")
    print(f"GHOST CAPTURE CLOUD — {label}/{page_type}")
    print(f"  URL:    {url}")
    print(f"  Mode:   {mode_str}")
    print(f"  Output: {out_path}")
    print(f"{'='*60}\n")

    browser = await get_browser(pw, cloud, ws_endpoint, force_brightdata=force_brightdata)
    result = await capture_page(browser, url, label, page_type, out_path, timeout, extraction_js)
    await browser.close()

    status = "✅" if result["ok"] else "❌"
    print(f"\n{status} {result['label']}/{result['pageType']}: "
          f"{result['sections']} sections, completeness={result['completeness']} ({result['elapsed']}s)")
    if result["errors"]:
        err_parts = [f"{e['stage']}: {e['msg'][:80]}" for e in result["errors"]]
        print(f"  Errors: {'; '.join(err_parts)}")

    # Output JSON result to stdout for Python bridge (same as ghost_capture.js)
    print(f"\n__GHOST_RESULT__{json.dumps(result)}")

    return result
