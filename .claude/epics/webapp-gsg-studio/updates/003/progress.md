# T003 — /gsg page + GsgLpCard component

**Status** : done
**Effort** : S-M, 45-60 min

## Goal
Replace the FR-1 scaffold `/gsg/page.tsx` with a Server Component that auto-discovers LPs from `deliverables/gsg_demo/`, renders a responsive 2-col grid of cards (1-col mobile), each with iframe preview + metadata pills + "Open full" CTA.

## Plan
- `page.tsx` Server Component → calls `listGsgDemoFiles()`
- Empty state if `[]`
- Grid layout via inline styles using `gridTemplateColumns` responsive
- Card component `GsgLpCard.tsx`:
  - Title = slug
  - Pills: page_type / doctrine_version / multi-judge score
  - Score color: ≥70 green, 50-69 amber, <50 red
  - iframe `src=/api/gsg/[slug]/html` height 600px
  - CTA "Open full" → new tab to same API URL
- Keep scaffold `Studio.tsx` / `BriefWizard.tsx` / `LpPreview.tsx` untouched (V2 deferred per briefing)

## Files
- `webapp/apps/shell/app/gsg/page.tsx` (REPLACE)
- `webapp/apps/shell/components/gsg/GsgLpCard.tsx` (NEW)

## Gate-vert results

| Gate | Result |
| ---- | ------ |
| `lint_code_hygiene.py` | FAIL 1 (baseline `seed_supabase_test_data.py`, untouched) |
| `SCHEMA/validate_all.py` | 15 files, all passing |
| `parity_check.sh weglot` | OK |
| `audit_capabilities.py` | 0 HIGH orphans |
| `npm install` | 142 pkgs (preexisting audit warnings) |
| `tsc --noEmit` (shell) | exit 0 |
| `next build` (shell) | exit 0, `/gsg` = 625 B + 87.9 KB First Load, shared 87.3 KB < 95 KB |

## Smoke tests (dev server)

| Request | Expected | Result |
| ------- | -------- | ------ |
| `GET /gsg` | 200 | 200 |
| `GET /api/gsg/weglot-lp_listicle-v272c/html` | 200 | 200 |
| `GET /api/gsg/..%2F..%2Fetc%2Fpasswd/html` | 404 | 404 |
| `GET /api/gsg/nope/html` | 404 | 404 |
| Response headers | XFO + CSP + Cache-Control | all 3 present |

