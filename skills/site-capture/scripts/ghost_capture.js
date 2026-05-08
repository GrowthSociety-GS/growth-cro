#!/usr/bin/env node
/**
 * ghost_capture.js — Moteur de capture spatial V9 local
 * Remplace Apify par Playwright + Stealth en local
 * 0€, pas de quota, contrôle total
 *
 * Usage:
 *   node ghost_capture.js --url https://japhy.fr --label japhy --page-type home --out-dir ./output
 *   node ghost_capture.js --url https://japhy.fr --label japhy --page-type home --out-dir ./output --concurrency 4
 *
 * Output: out-dir/spatial_v9.json + screenshots/*.png
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// ──────────────────────────────────────────────
// CLI ARGS
// ──────────────────────────────────────────────
function parseArgs() {
    const args = process.argv.slice(2);
    const opts = {
        url: null,
        label: 'capture',
        pageType: 'home',
        outDir: './output',
        timeout: 120000,
        // Batch mode: JSON file with [{url, label, pageType}]
        batch: null,
        concurrency: 3,
        delay: 1000,
    };
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--url': opts.url = args[++i]; break;
            case '--label': opts.label = args[++i]; break;
            case '--page-type': opts.pageType = args[++i]; break;
            case '--out-dir': opts.outDir = args[++i]; break;
            case '--timeout': opts.timeout = parseInt(args[++i]); break;
            case '--batch': opts.batch = args[++i]; break;
            case '--concurrency': opts.concurrency = parseInt(args[++i]); break;
            case '--delay': opts.delay = parseInt(args[++i]); break;
        }
    }
    return opts;
}

// ──────────────────────────────────────────────
// COOKIE BANNER HANDLING (Playwright version)
// ──────────────────────────────────────────────
async function clickCookieAccept(page) {
    const selectors = [
        '#didomi-notice-agree-button',
        '#onetrust-accept-btn-handler',
        'button[id*="accept" i]',
        'button[class*="accept" i]',
        'button[aria-label*="accepter" i]',
        'button[aria-label*="accept" i]',
    ];
    for (const sel of selectors) {
        try {
            const el = await page.$(sel);
            if (el) { await el.click({ delay: 50 }); await page.waitForTimeout(600); return true; }
        } catch (e) {}
    }
    try {
        const clicked = await page.evaluate(() => {
            const texts = ['Tout accepter', "J'accepte", 'Accepter', 'Accept all', 'I agree'];
            const buttons = Array.from(document.querySelectorAll('button, a[role="button"]'));
            for (const b of buttons) {
                const t = (b.innerText || '').trim();
                if (texts.some(x => t.toLowerCase().includes(x.toLowerCase()))) { b.click(); return true; }
            }
            return false;
        });
        if (clicked) await page.waitForTimeout(600);
        return clicked;
    } catch (e) { return false; }
}

async function forceRemoveBanner(page) {
    return await page.evaluate(() => {
        const KEYWORDS = /cookie|consent|rgpd|gdpr|politique de confidentialit|vie priv/i;
        let removed = 0;
        const walk = function* (root) { const stack = [root]; while (stack.length) { const n = stack.pop(); if (!n) continue; yield n; if (n.shadowRoot) stack.push(n.shadowRoot); if (n.children) for (const c of n.children) stack.push(c); } };
        for (const el of walk(document.documentElement)) {
            if (!(el instanceof Element)) continue;
            let s; try { s = getComputedStyle(el); } catch (e) { continue; }
            if (!s || (s.position !== 'fixed' && s.position !== 'sticky')) continue;
            const r = el.getBoundingClientRect();
            if (r.width < 200 || r.height < 60) continue;
            const txt = (el.innerText || '').slice(0, 800);
            if (KEYWORDS.test(txt)) { try { el.remove(); removed++; } catch (e) {} }
        }
        return removed;
    });
}

async function closePopups(page) {
    try {
        await page.evaluate(() => {
            const closeSel = ['button[aria-label*="close" i]', 'button[class*="close" i]', '.modal-close', '.popup-close'];
            closeSel.forEach(s => document.querySelectorAll(s).forEach(el => { try { el.click(); } catch (e) {} }));
        });
        await page.waitForTimeout(300);
    } catch (e) {}
}

// ──────────────────────────────────────────────
// LOAD PERCEPTION TREE EXTRACTION CODE
// ──────────────────────────────────────────────
// We load the extractPerceptionTree evaluate function from spatial_capture_v9.js
// But since it's embedded in a pageFunction wrapper, we read the raw JS and extract
// the evaluate block. For simplicity, we inline the reference file path.

function loadExtractionCode() {
    const refPath = path.join(__dirname, '..', 'references', 'spatial_capture_v9.js');
    const code = fs.readFileSync(refPath, 'utf-8');

    // Extract the evaluate function body between the markers
    // The extractPerceptionTree function contains: return await page.evaluate(() => {
    // We need everything inside that evaluate call
    const startMarker = 'async function extractPerceptionTree() {';
    const startIdx = code.indexOf(startMarker);
    if (startIdx === -1) throw new Error('Cannot find extractPerceptionTree in spatial_capture_v9.js');

    // Find the matching closing brace for extractPerceptionTree
    let braceCount = 0;
    let foundStart = false;
    let extractEnd = -1;
    for (let i = startIdx; i < code.length; i++) {
        if (code[i] === '{') { braceCount++; foundStart = true; }
        if (code[i] === '}') { braceCount--; }
        if (foundStart && braceCount === 0) { extractEnd = i + 1; break; }
    }

    // Extract just the page.evaluate(() => { ... }) body
    const fnBody = code.substring(startIdx, extractEnd);

    // Find the evaluate callback body
    const evalStart = fnBody.indexOf('return await page.evaluate(() => {');
    if (evalStart === -1) throw new Error('Cannot find page.evaluate in extractPerceptionTree');

    // Get the code from after "return await page.evaluate(() => {" to the matching "})"
    const evalCodeStart = evalStart + 'return await page.evaluate(() => {'.length;
    let evalBraceCount = 1;
    let evalEnd = -1;
    for (let i = evalCodeStart; i < fnBody.length; i++) {
        if (fnBody[i] === '{') evalBraceCount++;
        if (fnBody[i] === '}') evalBraceCount--;
        if (evalBraceCount === 0) { evalEnd = i; break; }
    }

    // Return the inner body of the evaluate function
    return fnBody.substring(evalCodeStart, evalEnd);
}

// ──────────────────────────────────────────────
// SINGLE PAGE CAPTURE
// ──────────────────────────────────────────────
async function capturePage(browser, url, label, pageType, outDir, timeout) {
    const startTime = Date.now();
    const screenshotsDir = path.join(outDir, 'screenshots');
    fs.mkdirSync(screenshotsDir, { recursive: true });

    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2,
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        locale: 'fr-FR',
        timezoneId: 'Europe/Paris',
        // Stealth-like settings
        javaScriptEnabled: true,
        bypassCSP: true,
    });

    // Extra stealth: override navigator properties
    await context.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en-US', 'en'] });
        window.chrome = { runtime: {} };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);
    });

    const page = await context.newPage();
    page.setDefaultTimeout(timeout);
    page.setDefaultNavigationTimeout(timeout);

    const errors = [];
    const stagesCompleted = [];
    let perceptionTree = null;
    let completeness = 0.0;

    try {
        // Navigate — use domcontentloaded + extra wait (networkidle hangs on tracker-heavy sites)
        console.log(`  ⏳ Navigating to ${url}...`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: Math.min(timeout, 60000) });
        // Wait for additional resources (images, fonts, lazy-loaded content)
        await page.waitForTimeout(3000);
        // Try to wait for network to calm down (but don't block)
        try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch (e) { /* OK, continue */ }
        stagesCompleted.push('navigate');

        // Stage 1: Settle
        await page.waitForTimeout(1500);
        stagesCompleted.push('settle');

        // Stage 2: Screenshots (fold desktop)
        try {
            await page.evaluate(() => window.scrollTo(0, 0));
            await page.waitForTimeout(600);
            await page.screenshot({ path: path.join(screenshotsDir, 'spatial_fold_desktop.png'), type: 'png' });
            stagesCompleted.push('fold_desktop');
        } catch (e) { errors.push({ stage: 'fold_desktop', msg: String(e).slice(0, 200) }); }

        // Stage 2b: Fold mobile
        try {
            await page.setViewportSize({ width: 390, height: 844 });
            await page.evaluate(() => window.scrollTo(0, 0));
            await page.waitForTimeout(600);
            await page.screenshot({ path: path.join(screenshotsDir, 'spatial_fold_mobile.png'), type: 'png' });
            stagesCompleted.push('fold_mobile');
            // Reset to desktop
            await page.setViewportSize({ width: 1440, height: 900 });
            await page.waitForTimeout(300);
        } catch (e) { errors.push({ stage: 'fold_mobile', msg: String(e).slice(0, 200) }); }

        // Stage 3: Cookie handling
        try {
            await clickCookieAccept(page);
            await closePopups(page);
            await page.waitForTimeout(800);
            const stillThere = await page.evaluate(() => !!document.querySelector('[id*="cookie" i][class*="banner" i]'));
            if (stillThere) await forceRemoveBanner(page);
            stagesCompleted.push('cookie_dismiss');
        } catch (e) { errors.push({ stage: 'cookie_dismiss', msg: String(e).slice(0, 200) }); }

        // Stage 4: Perception tree extraction
        try {
            const evaluateCode = loadExtractionCode();
            // Wrap in an IIFE that returns the result
            const wrappedCode = `(async () => { ${evaluateCode} })()`;
            perceptionTree = await page.evaluate(wrappedCode);
            completeness = 0.8;
            stagesCompleted.push('extract');
        } catch (e) {
            errors.push({ stage: 'extract', msg: String(e).slice(0, 400) });
            console.error(`  ⚠️  Extract error: ${String(e).slice(0, 200)}`);
        }

        // Stage 5: Full page screenshot (clean, no annotations)
        try {
            await page.setViewportSize({ width: 1440, height: 900 });
            await page.evaluate(() => window.scrollTo(0, 0));
            await page.waitForTimeout(400);
            await page.screenshot({ path: path.join(screenshotsDir, 'spatial_full_page.png'), type: 'png', fullPage: true });
            stagesCompleted.push('full_page');
        } catch (e) { errors.push({ stage: 'full_page', msg: String(e).slice(0, 200) }); }

        // Stage 5b: Dump HTML rendered (SaaS-grade capture — source pour native_capture --html)
        // Playwright TLS fingerprint = Chrome réel → passe Cloudflare/Shopify/Akamai qui bloquent urllib.
        // Ce page.html est ensuite parsé par native_capture.py --html pour produire capture.json.
        try {
            const renderedHtml = await page.content();
            const htmlPath = path.join(outDir, 'page.html');
            fs.writeFileSync(htmlPath, renderedHtml);
            console.log(`  💾 page.html dumped (${(renderedHtml.length / 1024).toFixed(1)} KB rendered DOM)`);
            stagesCompleted.push('dump_html');
        } catch (e) { errors.push({ stage: 'dump_html', msg: String(e).slice(0, 200) }); }

        // Stage 6: ANNOTATED screenshots — draw bounding boxes on key elements
        // This creates a separate screenshot with visual overlays for the audit UI
        try {
            await page.evaluate(() => window.scrollTo(0, 0));
            await page.waitForTimeout(300);

            // Inject annotation overlay into the page
            await page.evaluate(() => {
                // Create overlay container
                const overlay = document.createElement('div');
                overlay.id = '__growthcro_annotations__';
                overlay.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 999999;';
                document.body.appendChild(overlay);

                function drawBox(rect, color, label, style = 'solid') {
                    const box = document.createElement('div');
                    box.style.cssText = `
                        position: absolute;
                        left: ${rect.x}px; top: ${rect.y}px;
                        width: ${rect.w || rect.width}px; height: ${rect.h || rect.height}px;
                        border: 3px ${style} ${color};
                        border-radius: 4px;
                        pointer-events: none;
                        z-index: 999999;
                    `;
                    if (label) {
                        const tag = document.createElement('div');
                        tag.style.cssText = `
                            position: absolute; top: -22px; left: -2px;
                            background: ${color}; color: #fff;
                            font: bold 10px system-ui; padding: 2px 6px;
                            border-radius: 3px 3px 0 0;
                            white-space: nowrap;
                        `;
                        tag.textContent = label;
                        box.appendChild(tag);
                    }
                    overlay.appendChild(box);
                }

                // Annotate H1
                const h1 = document.querySelector('h1');
                if (h1) {
                    const r = h1.getBoundingClientRect();
                    const fontSize = parseFloat(getComputedStyle(h1).fontSize);
                    const color = fontSize >= 32 ? '#7cf0c4' : '#ffa032'; // green if good size, orange if small
                    drawBox({ x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
                        color, `H1 · ${Math.round(fontSize)}px`);
                }

                // Annotate primary CTA (first prominent button/link above fold)
                const ctaCandidates = Array.from(document.querySelectorAll('a, button')).filter(el => {
                    try {
                        const r = el.getBoundingClientRect();
                        if (r.height < 20 || r.width < 60) return false;
                        if (r.top > 900) return false; // below fold
                        const s = getComputedStyle(el);
                        const bg = s.backgroundColor;
                        // Has background color (not transparent)
                        const hasColor = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
                        const text = (el.textContent || '').trim();
                        const isNav = el.closest('nav, header [class*="nav"], [role="navigation"]');
                        return (hasColor || el.tagName === 'BUTTON') && text.length > 1 && text.length < 60 && !isNav;
                    } catch (e) { return false; }
                });

                if (ctaCandidates.length > 0) {
                    // Score each candidate
                    const scored = ctaCandidates.map(el => {
                        const r = el.getBoundingClientRect();
                        const area = r.width * r.height;
                        const aboveFold = r.top < 900 ? 1 : 0;
                        const isBtn = el.tagName === 'BUTTON' ? 1 : 0;
                        const text = (el.textContent || '').trim().toLowerCase();
                        const actionWords = ['découvrir', 'créer', 'commencer', 'essayer', 'commander', 'acheter', 'réserver', 'tester', 'obtenir', 'voir', 'je'];
                        const hasAction = actionWords.some(w => text.includes(w)) ? 1 : 0;
                        return { el, score: area * 0.001 + aboveFold * 100 + isBtn * 50 + hasAction * 80 };
                    }).sort((a, b) => b.score - a.score);

                    // Annotate top 3 CTAs
                    scored.slice(0, 3).forEach((item, i) => {
                        const el = item.el;
                        const r = el.getBoundingClientRect();
                        const dims = `${Math.round(r.width)}×${Math.round(r.height)}px`;
                        const text = (el.textContent || '').trim().slice(0, 30);
                        const minOk = r.width >= 44 && r.height >= 44;
                        const color = i === 0 ? (minOk ? '#7cf0c4' : '#ff8a93') : '#f5c97b';
                        const label = i === 0 ? `CTA Principal · ${dims}` : `CTA ${i+1} · ${dims}`;
                        drawBox(
                            { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
                            color, `${label} · "${text}"`, i === 0 ? 'solid' : 'dashed'
                        );
                    });
                }

                // Annotate hero section boundary (first section / first screen)
                const heroSection = document.querySelector('section, [class*="hero"], [class*="banner"], main > div:first-child');
                if (heroSection) {
                    const r = heroSection.getBoundingClientRect();
                    drawBox(
                        { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: Math.min(r.height, 1200) },
                        'rgba(143,212,255,0.5)', `Hero Section · ${Math.round(r.height)}px`, 'dashed'
                    );
                }

                // Draw fold line at 900px
                const foldLine = document.createElement('div');
                foldLine.style.cssText = `
                    position: absolute; top: 900px; left: 0; width: 100%;
                    border-top: 2px dashed rgba(255,138,147,0.7);
                    z-index: 999998; pointer-events: none;
                `;
                const foldLabel = document.createElement('div');
                foldLabel.style.cssText = `
                    position: absolute; top: 900px; right: 20px;
                    background: rgba(255,138,147,0.8); color: #fff;
                    font: bold 11px system-ui; padding: 2px 8px;
                    border-radius: 0 0 4px 4px; z-index: 999999;
                `;
                foldLabel.textContent = '▼ FOLD LINE · 900px';
                overlay.appendChild(foldLine);
                overlay.appendChild(foldLabel);

                // Annotate images in hero (first 3 above fold)
                const heroImages = Array.from(document.querySelectorAll('img')).filter(img => {
                    const r = img.getBoundingClientRect();
                    return r.top < 900 && r.width > 100 && r.height > 60;
                }).slice(0, 3);

                heroImages.forEach((img, i) => {
                    const r = img.getBoundingClientRect();
                    const nat = `${img.naturalWidth}×${img.naturalHeight}`;
                    const render = `${Math.round(r.width)}×${Math.round(r.height)}`;
                    const isLazy = img.loading === 'lazy';
                    const color = isLazy ? '#ffa032' : '#7cf0c4';
                    drawBox(
                        { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
                        color, `IMG ${i+1} · ${render} (nat: ${nat})${isLazy ? ' · LAZY!' : ''}`, 'dashed'
                    );
                });

                // Annotate social proof elements (trust widgets, testimonials)
                const trustSelectors = [
                    '[class*="trustpilot"]', '[class*="review"]', '[class*="avis"]',
                    '[class*="rating"]', '[class*="testimonial"]', '[class*="trust"]',
                    '[class*="social-proof"]', 'iframe[src*="trustpilot"]'
                ];
                trustSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        try {
                            const r = el.getBoundingClientRect();
                            if (r.width < 50 || r.height < 20) return;
                            const yPct = Math.round((r.top + window.scrollY) / document.body.scrollHeight * 100);
                            drawBox(
                                { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height },
                                '#b7a4ff', `Social Proof · ${yPct}% page`, 'dashed'
                            );
                        } catch (e) {}
                    });
                });
            });

            // Take annotated screenshot
            await page.screenshot({ path: path.join(screenshotsDir, 'spatial_annotated_desktop.png'), type: 'png', fullPage: true });

            // Clean up annotations
            await page.evaluate(() => {
                const overlay = document.getElementById('__growthcro_annotations__');
                if (overlay) overlay.remove();
                // Remove fold lines
                document.querySelectorAll('[style*="999998"], [style*="999999"]').forEach(el => {
                    if (el.id !== '__growthcro_annotations__') { try { el.remove(); } catch(e) {} }
                });
            });

            stagesCompleted.push('annotated_screenshot');
        } catch (e) { errors.push({ stage: 'annotated_screenshot', msg: String(e).slice(0, 200) }); }

        // Completeness
        completeness = stagesCompleted.includes('extract') && stagesCompleted.includes('full_page') ? 1.0 : 0.8;

    } catch (e) {
        errors.push({ stage: 'navigation', msg: String(e).slice(0, 300) });
    }

    // Build final JSON
    const finalCapture = {
        meta: perceptionTree?.meta || { url, label, capturedAt: new Date().toISOString(), completeness },
        stagesCompleted,
        errors,
        ...(perceptionTree || {}),
    };

    // Save spatial_v9.json
    const jsonPath = path.join(outDir, 'spatial_v9.json');
    fs.writeFileSync(jsonPath, JSON.stringify(finalCapture, null, 2));

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    const sections = (finalCapture.sections || []).length;

    await context.close();

    return { ok: errors.length === 0 || completeness >= 0.8, label, pageType, sections, completeness, elapsed, errors };
}

// ──────────────────────────────────────────────
// BATCH MODE
// ──────────────────────────────────────────────
async function runBatch(batchFile, opts) {
    const tasks = JSON.parse(fs.readFileSync(batchFile, 'utf-8'));
    console.log(`\n═══════════════════════════════════════════════════`);
    console.log(`GHOST CAPTURE — BATCH MODE`);
    console.log(`  Tasks: ${tasks.length}`);
    console.log(`  Concurrency: ${opts.concurrency}`);
    console.log(`  Delay: ${opts.delay}ms`);
    console.log(`═══════════════════════════════════════════════════\n`);

    const launchBrowser = () => chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
        ],
    });

    let browser = await launchBrowser();
    const BROWSER_RESTART_EVERY = 10; // restart browser every N captures to avoid crashes
    let chunkCounter = 0;

    const results = [];
    let completed = 0;

    // Process in chunks of concurrency
    for (let i = 0; i < tasks.length; i += opts.concurrency) {
        // Restart browser periodically to avoid accumulated state / crashes
        if (chunkCounter > 0 && (chunkCounter % BROWSER_RESTART_EVERY === 0 || !browser.isConnected())) {
            try { await browser.close(); } catch (e) {}
            console.log(`  [browser] relaunch after ${chunkCounter} chunks`);
            browser = await launchBrowser();
        }
        const chunk = tasks.slice(i, i + opts.concurrency);
        const promises = chunk.map(async (task) => {
            const outDir = task.outDir || path.join(opts.outDir, task.label, task.pageType);
            try {
                const result = await capturePage(browser, task.url, task.label, task.pageType, outDir, opts.timeout);
                completed++;
                const status = result.ok ? '✅' : '❌';
                console.log(`  [${completed}/${tasks.length}] ${status} ${task.label}/${task.pageType}: ${result.sections} sections (${result.elapsed}s)`);
                results.push(result);
                return result;
            } catch (e) {
                completed++;
                const errMsg = String(e).slice(0, 200);
                console.log(`  [${completed}/${tasks.length}] ❌ ${task.label}/${task.pageType}: ${errMsg.slice(0, 100)}`);
                results.push({ ok: false, label: task.label, pageType: task.pageType, error: errMsg });
                // If browser died, relaunch for next chunk
                if (errMsg.includes('browser has been closed') || errMsg.includes('Target closed')) {
                    try { await browser.close(); } catch (_) {}
                    browser = await launchBrowser();
                    console.log(`  [browser] relaunched after crash`);
                }
            }
        });
        await Promise.all(promises);
        chunkCounter++;
        if (i + opts.concurrency < tasks.length) {
            await new Promise(r => setTimeout(r, opts.delay));
        }
    }

    try { await browser.close(); } catch (e) {}

    const okCount = results.filter(r => r.ok).length;
    console.log(`\n═══════════════════════════════════════════════════`);
    console.log(`BATCH COMPLETE — ${okCount}/${results.length} OK`);
    console.log(`═══════════════════════════════════════════════════\n`);

    return results;
}

// ──────────────────────────────────────────────
// SINGLE MODE
// ──────────────────────────────────────────────
async function runSingle(opts) {
    if (!opts.url) {
        console.error('Usage: node ghost_capture.js --url <URL> --label <LABEL> --page-type <TYPE> --out-dir <DIR>');
        process.exit(1);
    }

    console.log(`\n═══════════════════════════════════════════════════`);
    console.log(`GHOST CAPTURE — ${opts.label}/${opts.pageType}`);
    console.log(`  URL: ${opts.url}`);
    console.log(`  Output: ${opts.outDir}`);
    console.log(`═══════════════════════════════════════════════════\n`);

    const browser = await chromium.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
        ],
    });

    const result = await capturePage(browser, opts.url, opts.label, opts.pageType, opts.outDir, opts.timeout);
    await browser.close();

    const status = result.ok ? '✅' : '❌';
    console.log(`\n${status} ${result.label}/${result.pageType}: ${result.sections} sections, completeness=${result.completeness} (${result.elapsed}s)`);
    if (result.errors.length > 0) {
        console.log(`  Errors: ${result.errors.map(e => `${e.stage}: ${e.msg.slice(0, 80)}`).join('; ')}`);
    }

    // Output JSON result to stdout for Python bridge
    console.log(`\n__GHOST_RESULT__${JSON.stringify(result)}`);

    process.exit(result.ok ? 0 : 1);
}

// ──────────────────────────────────────────────
// MAIN
// ──────────────────────────────────────────────
(async () => {
    const opts = parseArgs();
    try {
        if (opts.batch) {
            await runBatch(opts.batch, opts);
        } else {
            await runSingle(opts);
        }
    } catch (e) {
        console.error(`Fatal: ${e.message}`);
        process.exit(1);
    }
})();
