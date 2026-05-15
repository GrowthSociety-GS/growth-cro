#!/usr/bin/env node
/**
 * Minimal Playwright screenshot tool — V27.2-H Sprint 16 (T16-6).
 *
 * Usage: node scripts/screenshot_html.js <html-path> <out-dir>
 *
 * Outputs:
 *   <out-dir>/desktop_fold.png   (1440x900)
 *   <out-dir>/desktop_full.png   (full scroll)
 *   <out-dir>/mobile_fold.png    (375x812)
 *   <out-dir>/mobile_full.png    (full scroll)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function main() {
    const htmlPath = process.argv[2];
    const outDir = process.argv[3];
    if (!htmlPath || !outDir) {
        console.error('Usage: node screenshot_html.js <html-path> <out-dir>');
        process.exit(1);
    }
    fs.mkdirSync(outDir, { recursive: true });
    const fileUrl = 'file://' + path.resolve(htmlPath);

    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    await page.goto(fileUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);

    // Desktop fold
    await page.screenshot({ path: path.join(outDir, 'desktop_fold.png'), fullPage: false });
    // Desktop full
    await page.screenshot({ path: path.join(outDir, 'desktop_full.png'), fullPage: true });

    // Mobile
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(outDir, 'mobile_fold.png'), fullPage: false });
    await page.screenshot({ path: path.join(outDir, 'mobile_full.png'), fullPage: true });

    await browser.close();
    console.log('✓ screenshots written to', outDir);
}

main().catch(err => { console.error(err); process.exit(1); });
