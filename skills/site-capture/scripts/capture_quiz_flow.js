#!/usr/bin/env node
/**
 * capture_quiz_flow.js — Navigateur Playwright pour quiz SPA (Phase 6 Étape 2).
 *
 * Navigue dans un quiz en cliquant heuristiquement à travers les questions
 * et capture (a) intro, (b) chaque step, (c) résultat final quand détecté.
 *
 * Usage :
 *   node capture_quiz_flow.js --url https://japhy.fr/profile-builder \
 *     --label japhy --out-dir ./data/captures/japhy/quiz_vsl/flow \
 *     [--max-steps 15] [--timeout-per-step 10000]
 *
 * Output:
 *   out-dir/
 *     ├── intro.json
 *     ├── intro.png
 *     ├── step_01.json
 *     ├── step_01.png
 *     ├── ...
 *     ├── result.json
 *     ├── result.png
 *     └── flow_summary.json  (aggregate stats for scoring)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function parseArgs() {
    const args = process.argv.slice(2);
    const opts = {
        url: null, label: 'quiz', outDir: './quiz_flow',
        maxSteps: 15, timeoutPerStep: 10000, viewport: 'desktop',
    };
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--url': opts.url = args[++i]; break;
            case '--label': opts.label = args[++i]; break;
            case '--out-dir': opts.outDir = args[++i]; break;
            case '--max-steps': opts.maxSteps = parseInt(args[++i]); break;
            case '--timeout-per-step': opts.timeoutPerStep = parseInt(args[++i]); break;
            case '--viewport': opts.viewport = args[++i]; break;
        }
    }
    if (!opts.url) { console.error('Usage: --url <quiz_url> required'); process.exit(1); }
    return opts;
}

// Heuristic selectors for quiz elements
const START_SELECTORS = [
    'button:has-text("Commencer")', 'button:has-text("Démarrer")',
    'button:has-text("Start")', 'button:has-text("Begin")',
    'button:has-text("C\'est parti")', 'button:has-text("Let\'s go")',
    'a:has-text("Commencer")', 'a:has-text("Start")',
    '[data-testid*="start"]', '[data-quiz-start]',
];

const NEXT_SELECTORS = [
    'button:has-text("Suivant")', 'button:has-text("Next")',
    'button:has-text("Continuer")', 'button:has-text("Continue")',
    'button[type="submit"]:not(:has-text("Retour"))',
    '[data-quiz-next]', '[aria-label*="suivant" i]', '[aria-label*="next" i]',
];

const OPTION_SELECTORS = [
    'input[type="radio"]', 'input[type="checkbox"]',
    'button[role="radio"]', '[data-quiz-option]',
    'label.option', 'label[for*="option"]', 'label[for*="choice"]',
    '.quiz-option', '.option-card', '.choice-card',
];

const RESULT_MARKERS = [
    /votre profil/i, /your profile/i, /votre résultat/i, /your result/i,
    /recommand/i, /personnalisé/i, /personalized/i, /votre plan/i, /your plan/i,
    /découvrez votre/i, /discover your/i,
];

const COOKIE_BANNERS = [
    'button:has-text("Accepter")', 'button:has-text("Accept")',
    'button:has-text("J\'accepte")', 'button:has-text("OK")',
    '#axeptio_btn_acceptAll', '#didomi-notice-agree-button',
    '[data-testid*="accept"]',
];

async function dismissCookies(page) {
    for (const sel of COOKIE_BANNERS) {
        try {
            const btn = await page.$(sel);
            if (btn) { await btn.click({ timeout: 2000 }); await page.waitForTimeout(500); return true; }
        } catch {}
    }
    return false;
}

async function tryClick(page, selectors, label = 'action') {
    for (const sel of selectors) {
        try {
            const el = await page.$(sel);
            if (el && await el.isVisible()) {
                await el.click({ timeout: 3000 });
                return sel;
            }
        } catch {}
    }
    return null;
}

async function selectFirstOption(page) {
    // Try option selectors — pick first visible
    for (const sel of OPTION_SELECTORS) {
        try {
            const els = await page.$$(sel);
            for (const el of els) {
                if (await el.isVisible()) {
                    try { await el.click({ timeout: 2000, force: true }); return sel; } catch {}
                }
            }
        } catch {}
    }
    return null;
}

async function isResultPage(page) {
    try {
        const text = await page.textContent('body') || '';
        const head = text.slice(0, 3000);
        return RESULT_MARKERS.some(r => r.test(head));
    } catch { return false; }
}

async function captureStep(page, outDir, name) {
    const bodyText = (await page.textContent('body') || '').slice(0, 5000);
    const html = await page.content();
    // Count visible form elements (question signals)
    const formStats = await page.evaluate(() => {
        const radios = document.querySelectorAll('input[type=radio]').length;
        const checks = document.querySelectorAll('input[type=checkbox]').length;
        const options = document.querySelectorAll('[data-quiz-option], .quiz-option, .option-card, label.option').length;
        const inputs = document.querySelectorAll('input[type=text], input[type=email], textarea').length;
        const images = document.querySelectorAll('img, svg').length;
        const h1 = (document.querySelector('h1') || {}).innerText || '';
        const h2 = (document.querySelector('h2') || {}).innerText || '';
        const progressText = (document.querySelector('[class*=progress], [role=progressbar]') || {}).innerText || '';
        return { radios, checks, options, inputs, images, h1, h2, progressText };
    });
    const snap = {
        url: page.url(),
        stepName: name,
        capturedAt: new Date().toISOString(),
        formStats,
        bodyText,
        isResult: await isResultPage(page),
    };
    fs.writeFileSync(path.join(outDir, `${name}.json`), JSON.stringify(snap, null, 2));
    try { await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: false }); } catch {}
    try { fs.writeFileSync(path.join(outDir, `${name}.html`), html); } catch {}
    return snap;
}

async function main() {
    const opts = parseArgs();
    fs.mkdirSync(opts.outDir, { recursive: true });

    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext({
        viewport: opts.viewport === 'mobile' ? { width: 390, height: 844 } : { width: 1280, height: 800 },
        userAgent: opts.viewport === 'mobile'
            ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
            : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
    const page = await ctx.newPage();

    const flow = { url: opts.url, label: opts.label, steps: [], startedAt: new Date().toISOString() };

    try {
        await page.goto(opts.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        try { await page.waitForLoadState('networkidle', { timeout: 5000 }); } catch {}
        await page.waitForTimeout(1500);
        await dismissCookies(page);
        await page.waitForTimeout(500);

        // 1. Capture intro
        const intro = await captureStep(page, opts.outDir, 'intro');
        flow.steps.push({ name: 'intro', ...intro.formStats, isResult: intro.isResult, url: intro.url });

        // 2. Click start (if present)
        const startedVia = await tryClick(page, START_SELECTORS, 'start');
        if (startedVia) {
            await page.waitForTimeout(1200);
            flow.startedVia = startedVia;
        }

        // 3. Walk through steps
        let resultReached = false;
        for (let i = 1; i <= opts.maxSteps; i++) {
            const name = `step_${String(i).padStart(2, '0')}`;
            const snap = await captureStep(page, opts.outDir, name);
            flow.steps.push({ name, ...snap.formStats, isResult: snap.isResult, url: snap.url });
            if (snap.isResult) {
                resultReached = true;
                // Final capture as "result" too
                await captureStep(page, opts.outDir, 'result');
                break;
            }
            // Select an option
            const optSel = await selectFirstOption(page);
            await page.waitForTimeout(400);
            // Click next
            const nextSel = await tryClick(page, NEXT_SELECTORS, 'next');
            if (!nextSel) {
                flow.haltedAt = i;
                flow.haltReason = 'no_next_button';
                break;
            }
            // Wait for navigation / transition
            try { await page.waitForLoadState('networkidle', { timeout: opts.timeoutPerStep }); } catch {}
            await page.waitForTimeout(800);
        }

        flow.resultReached = resultReached;
        flow.completedAt = new Date().toISOString();
        flow.stepsCaptured = flow.steps.length - 1;  // exclude intro

        // Aggregate stats
        const stepsOnly = flow.steps.filter(s => s.name.startsWith('step'));
        flow.aggregate = {
            questionsCount: stepsOnly.length,
            avgOptions: stepsOnly.reduce((a, s) => a + Math.max(s.options, s.radios, s.checks), 0) / Math.max(1, stepsOnly.length),
            hasProgressBar: stepsOnly.some(s => s.progressText && s.progressText.length > 0),
            imageRichSteps: stepsOnly.filter(s => s.images >= 3).length,
            textInputSteps: stepsOnly.filter(s => s.inputs > 0).length,
        };

        fs.writeFileSync(path.join(opts.outDir, 'flow_summary.json'), JSON.stringify(flow, null, 2));
        console.log('✅ Flow captured:', JSON.stringify(flow.aggregate, null, 2));
        console.log(`   Result reached: ${resultReached} | Steps: ${flow.stepsCaptured}`);
    } catch (e) {
        flow.error = String(e);
        fs.writeFileSync(path.join(opts.outDir, 'flow_summary.json'), JSON.stringify(flow, null, 2));
        console.error('❌ Error:', e.message);
    } finally {
        await browser.close();
    }
}

main();
