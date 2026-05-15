#!/usr/bin/env node
/**
 * a11y_audit.js — V27.2-L Sprint 20 (T20-1).
 *
 * Run axe-core WCAG2A + WCAG2AA + WCAG21AA scan on a rendered HTML
 * file. Prints a single line of JSON on stdout :
 *
 *   {"score": 0-100, "violations": [...], "passes": int, "incomplete": int}
 *
 * Usage : node scripts/a11y_audit.js <html-path>
 */
const { chromium } = require('playwright');
const { AxeBuilder } = require('@axe-core/playwright');
const fs = require('fs');
const path = require('path');

async function main() {
    const htmlPath = process.argv[2];
    if (!htmlPath) {
        console.error(JSON.stringify({ error: 'Usage: node a11y_audit.js <html-path>' }));
        process.exit(1);
    }
    const fileUrl = 'file://' + path.resolve(htmlPath);
    let browser;
    try {
        browser = await chromium.launch();
        const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        const page = await ctx.newPage();
        await page.goto(fileUrl, { waitUntil: 'networkidle' });
        await page.waitForTimeout(500);

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
            .analyze();

        // Score : start at 100, deduct per violation severity.
        const weights = { critical: 12, serious: 6, moderate: 3, minor: 1 };
        let deduction = 0;
        const violations_summary = [];
        for (const v of results.violations) {
            const w = weights[v.impact] || 1;
            const count = v.nodes ? v.nodes.length : 1;
            deduction += w * Math.min(count, 5);
            violations_summary.push({
                id: v.id,
                impact: v.impact,
                description: v.description,
                nodes_count: count,
                help: v.helpUrl,
            });
        }
        const score = Math.max(0, Math.min(100, Math.round(100 - deduction)));
        const report = {
            version: 'axe-core-a11y-v1.0',
            score,
            passed: score >= 70,
            violations: violations_summary,
            n_violations: results.violations.length,
            n_passes: results.passes.length,
            n_incomplete: results.incomplete.length,
        };
        console.log(JSON.stringify(report));
    } catch (err) {
        console.log(JSON.stringify({ error: String(err), score: 0, passed: false }));
        process.exitCode = 0;  // don't hard-fail the pipeline
    } finally {
        if (browser) await browser.close();
    }
}

main();
