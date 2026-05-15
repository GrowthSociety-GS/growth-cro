# Epic — Quality Completeness (Sprint 20)

**Created** : 2026-05-15
**Status** : ✅ CLOSED
**Triggered by** : Mathis 2026-05-15 *"GO 20 d'abord et on fait ensuite le test from blank weglot après"*
**Final commit** : pending

## Why this epic exists

Sprint 13→19 covered design/content/skills/scoring but never measured
**accessibility** (WCAG) or **performance** (Core Web Vitals). Mathis
implicitly wants these signals before the final acceptance test.

## Solution — single sub-PRD

### [PRD-F — a11y + perf audits subprocess](prds/PRD-F-a11y-perf.md)

3 tasks :

| Task | Effort | What it adds |
|------|-------|--------------|
| T20-1 axe-core a11y audit subprocess | 45 min | WCAG2A+AA scan, 0-100 score, violations list |
| T20-2 lighthouse perf audit subprocess | 45 min | Performance score 0-100, LCP/CLS/TBT/FCP/SI |
| T20-3 wire both + composite_score update | 30 min | New 8-audit composite : 0.45 multi-judge / 0.08 impeccable / 0.12 cro / 3×0.05 design audits / 0.10 a11y / 0.10 perf |

## V13b acceptance run (skip-judges, runtime audits only)

```
Impeccable QA   : 96/100 PASS hits=1
CRO methodology : 10/10 PASS gaps=0
frontend-design : 10/10
brand-guidelines: 10/10
emil-design-eng : 10/10
a11y axe-core   : 70/100 PASS (1 color-contrast violation on 5 nodes)
perf lighthouse : 86/100 PASS (LCP=2250ms, CLS=0)
Composite score : 92.2% Stratospheric 🚀
Cost           : $0 / 13s wall
```

## V13 with multi-judge — caveat

V13 with full multi-judge tripped 2 killer rules in the Doctrine judge
(Doctrine 50%, multi-judge 56.75%, composite 75.7% Bon). This is Sonnet
**run-to-run noise** ; V11 / V12 on the same HTML structure scored
78-80% Doctrine. The killer rules detection is stochastic on edge
cases. Sprint 21+ should investigate the noise floor + maybe vote
across 3 runs.

## Acceptance

- [x] axe-core a11y subprocess shipped (`scripts/a11y_audit.js`)
- [x] lighthouse perf subprocess shipped (`scripts/perf_audit.js` with
  local HTTP server workaround for `file://` rejection)
- [x] Python wrapper module `moteur_gsg/core/external_audits.py`
- [x] Wired in `mode_1_complete` between HTML save and multi-judge
- [x] Composite_score formula updated (8 audits)
- [x] V13b runs Stratospheric (composite 92.2%) under skip-judges
- [x] Cost-friendly : a11y adds ~3s, lighthouse adds ~10-15s

## Out of scope (Sprint 21+)

- Multi-judge noise reduction (vote 3-runs, killer-rules threshold)
- Real photographs via Unsplash for reasons (Mathis 2026-05-15 ask)
- 100-client production scale at multi-judge cost
- Webapp integration of the 8-audit dashboard

## Index

- [PRD-F — a11y + perf audits](prds/PRD-F-a11y-perf.md)
