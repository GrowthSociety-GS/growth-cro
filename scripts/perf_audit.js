#!/usr/bin/env node
/**
 * perf_audit.js — V27.2-L Sprint 20 (T20-2).
 *
 * Run lighthouse on a rendered HTML file (file:// URL). Prints single
 * line of JSON on stdout :
 *
 *   {"score": 0-100, "perf_score": 0-1, "lcp_ms": int, "cls": float,
 *    "tbt_ms": int, "fcp_ms": int}
 *
 * Usage : node scripts/perf_audit.js <html-path>
 */
const lighthouse = require('lighthouse').default;
const { launch } = require('chrome-launcher');
const path = require('path');
const fs = require('fs');
const http = require('http');

function startServer(filePath) {
    const html = fs.readFileSync(filePath);
    return new Promise(resolve => {
        const server = http.createServer((req, res) => {
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(html);
        });
        server.listen(0, '127.0.0.1', () => resolve(server));
    });
}

async function main() {
    const htmlPath = process.argv[2];
    if (!htmlPath) {
        console.error(JSON.stringify({ error: 'Usage: node perf_audit.js <html-path>' }));
        process.exit(1);
    }
    let chrome, server;
    try {
        server = await startServer(path.resolve(htmlPath));
        const port = server.address().port;
        const httpUrl = `http://127.0.0.1:${port}/`;
        chrome = await launch({ chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu'] });
        const opts = {
            logLevel: 'error',
            output: 'json',
            onlyCategories: ['performance'],
            port: chrome.port,
            formFactor: 'desktop',
            screenEmulation: {
                mobile: false,
                width: 1440,
                height: 900,
                deviceScaleFactor: 1,
                disabled: false,
            },
            throttlingMethod: 'simulate',
        };
        const runnerResult = await lighthouse(httpUrl, opts);
        const lhr = runnerResult.lhr;
        const perf = lhr.categories.performance;
        const audits = lhr.audits;

        const perfScore = perf.score ?? 0;
        const score100 = Math.round(perfScore * 100);
        const report = {
            version: 'lighthouse-perf-v1.0',
            score: score100,
            perf_score: perfScore,
            passed: score100 >= 70,
            lcp_ms: audits['largest-contentful-paint']?.numericValue ?? null,
            cls: audits['cumulative-layout-shift']?.numericValue ?? null,
            tbt_ms: audits['total-blocking-time']?.numericValue ?? null,
            fcp_ms: audits['first-contentful-paint']?.numericValue ?? null,
            si_ms: audits['speed-index']?.numericValue ?? null,
        };
        console.log(JSON.stringify(report));
    } catch (err) {
        console.log(JSON.stringify({ error: String(err), score: 0, passed: false }));
        process.exitCode = 0;
    } finally {
        if (chrome) await chrome.kill();
        if (server) server.close();
    }
}

main();
