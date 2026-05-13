# T002 — /clients/[slug] detail page progress

## Status
DONE

## Files created
- `webapp/apps/shell/app/clients/[slug]/page.tsx` — Server Component, parallel-fetches `getClientBySlug()` + `listAuditsForClient()`, computes pillar averages + global score, mounts `ClientDetailTabs`.
- `webapp/apps/shell/components/clients/PillarRadialChart.tsx` — pure SVG/CSS radial chart (n axes, n=6 typical). No charting lib dep (no recharts, no victory). 4 grid rings (25/50/75/100%), data polygon w/ gold fill, dot markers, axis labels.
- `webapp/apps/shell/components/clients/ClientDetailTabs.tsx` — Client Component tabs container (audits / brand_dna / history), local state only.
- `webapp/apps/shell/components/clients/AuditsTabPanel.tsx` — list audits with link to `/audits/[clientSlug]/[auditId]`.
- `webapp/apps/shell/components/clients/BrandDNATabPanel.tsx` — renders `brand_dna_json` or amber "Pending V29" placeholder.
- `webapp/apps/shell/components/clients/HistoryTabPanel.tsx` — chronological audit timeline (left rule + date + score).
- `webapp/apps/shell/components/clients/score-utils.ts` — mono-concern helpers: `getAuditScores()`, `avgPillarsAcrossAudits()`, `extractRecoContent()`. Doctrine V3.2.1 known pillar ceilings table; fallback 30.

## Data layer
- `getClientBySlug(supabase, slug)` — existing
- `listAuditsForClient(supabase, clientId)` — existing
- Pillar averages computed in-memory across audits (small data).

## Radial chart approach
- 6 axes by default (driven by data — whatever piliers are in scores_json).
- Uses `<polygon>` for data, `<line>` for axes, `<text>` for labels.
- Known per-pillar ceilings: hero=20, persuasion=35, ux=25, coherence=30, psycho=25, tech=20, intent/value_clarity/social_proof/motivation_friction=30.
- Fallback ceiling 30 for unknown pillars.

## Acceptance criteria
- [x] `/clients/[slug]` HTTP 200 wired `getClientBySlug()` + `listAuditsForClient()`
- [x] Header: client name + business_category + 6 piliers radial chart
- [x] Tabs: Audits (default), Brand DNA (Pending placeholder if null), Historique
- [x] Tab Audits: list with link to `/audits/[clientSlug]/[auditId]`
- [x] Empty states gracieux (no audits → message, no brand DNA → Pending V29 pill)

## Decisions
- **No charting library**: SVG polygon-based radial chart, 100% pure JSX. Zero new dep.
- **Pillar averages** instead of "select an audit" UI: the radial chart shows the *signature* of the client across all audits, which is more useful for a portfolio overview. Per-audit pillar detail is on `/audits/[clientSlug]/[auditId]` (T003).
- **Brand DNA placeholder**: explicitly out-of-scope per PRD. We surface raw JSON if present, otherwise an amber pill + explanation. Full V29 wiring is a future sprint.
- **History tab = audit timeline** rather than score-delta chart (deferred to FR-6 polish).
