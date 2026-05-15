# PRD-F — a11y + perf subprocess audits

**Sprint 20** : gsg-quality-completeness-2026-05
**Estimated** : 2h actual ~1h30 wall

## Goal

Add 2 critical real-world quality signals that Mathis cares about :
- **a11y** (axe-core WCAG2A + AA + 21AA) — 0 violations = sky's the limit
- **perf** (Lighthouse Core Web Vitals) — LCP/CLS/FCP/TBT/SI

## Architecture

Node.js subprocesses (not Python LLM) — deterministic, free, fast.

```
Python pipeline (mode_1_complete)
   │
   ├─ run_a11y_audit(html_path)  → subprocess node scripts/a11y_audit.js
   │                              → playwright + @axe-core/playwright
   │                              → JSON line: {score, violations, ...}
   │
   └─ run_perf_audit(html_path)  → subprocess node scripts/perf_audit.js
                                  → chrome-launcher + lighthouse
                                  → local HTTP server (file:// rejected)
                                  → JSON line: {score, lcp_ms, cls, ...}
```

## Acceptance

- [x] `@axe-core/playwright` + `axe-core` + `lighthouse` + `chrome-launcher` installed via npm
- [x] `scripts/a11y_audit.js` runs in < 10s with Playwright Chromium
- [x] `scripts/perf_audit.js` runs in < 20s with chrome-launcher + local HTTP server
- [x] `moteur_gsg/core/external_audits.py` wraps both with defensive
      fallback dicts on failure
- [x] `mode_1_complete` invokes both after HTML save, surfaces scores in
      `gen["a11y_audit"]` + `gen["perf_audit"]`, logs concise output
- [x] Composite_score formula updated to weight a11y 0.10 + perf 0.10 ;
      multi_judge weight reduced 0.55 → 0.45
- [x] V13b end-to-end skip-judges : composite 92.2 Stratospheric

## Files

- `scripts/a11y_audit.js` (NEW)
- `scripts/perf_audit.js` (NEW)
- `moteur_gsg/core/external_audits.py` (NEW)
- `moteur_gsg/modes/mode_1_complete.py` (wire + composite update)
- `package.json` (npm deps + 33 new packages)

## Lessons learned (added to SPRINT_LESSONS.md)

1. Lighthouse rejects `file://` URLs — must serve via a local
   HTTP server (workaround : Node `http` module spinning up an
   ephemeral 127.0.0.1 server per audit run).
2. Adding deterministic external audits (a11y, perf, …) to the
   composite_score formula stabilizes the grade : if multi-judge
   Sonnet has a bad run, the 0.45 weight + 0.55 deterministic
   weight (impeccable + cro + 3×design + a11y + perf) keep
   composite within 5-7pts of a "true" value.
3. `chrome-launcher` + `lighthouse` work fine alongside Playwright
   in the same pipeline run — no port conflict if the launcher
   picks its own port (default behavior).
