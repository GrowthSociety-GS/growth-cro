# T003 — /audits/[clientSlug]/[auditId] route progress

## Status
DONE

## Files created
- `webapp/apps/shell/app/audits/[clientSlug]/[auditId]/page.tsx` — Server Component, parallel-fetches client + audit + recos, mounts `AuditDetailFull`.
- `webapp/apps/shell/components/audits/AuditDetailFull.tsx` — full audit detail: pillar radial + bars (left col), top-5 recos sorted by expected_lift_pct desc + evidence_ids cliquables (right col). Export-PDF placeholder button disabled (V2).

## Routing decision (PRD asks for `/audits/[id]` OR `/audits/[clientSlug]/[auditId]`)
**Chose `/audits/[clientSlug]/[auditId]`** because:
1. FR-1 already established `/audits/[clientSlug]` as the canonical client-context route.
2. The breadcrumb hierarchy (`Index audits` ← `Audits client X` ← `Audit Y`) is reusable.
3. Internal links from `/clients/[slug]` AuditsTabPanel and Sidebar consistency are clean.
4. The client_id ↔ audit_id guard (`audit.client_id !== client.id → notFound`) is cheap and catches stale URLs.

A flat `/audits/[id]` would have required the audit row to JOIN clients (extra query for breadcrumb) and would orphan the breadcrumb context.

## Data layer
- `getClientBySlug(supabase, clientSlug)` — existing
- `getAudit(supabase, auditId)` — existing (was named `getAudit`, not `getAuditById`)
- `listRecosForAudit(supabase, auditId)` — existing

## Acceptance criteria
- [x] `/audits/[clientSlug]/[auditId]` HTTP 200 wired
- [x] Header: client name + page_type + page_slug + page_url + audit_date + global_score
- [x] Section "Scores par pilier" : SVG radial + ScoreBar fallback
- [x] Section "Recos prioritaires" : top 5 sorted by expected_lift_pct desc
- [x] Each reco: priority badge, criterion_id, content_json.summary, expected_lift_pct, evidence_ids
- [x] Evidence_ids cliquables (open new tab pour future screenshot serving)
- [x] CTA "Export audit PDF" → placeholder disabled, link prepared `/audits/[clientSlug]/[auditId]/export` (V2)

## Decisions
- **No charting library**: reuses `PillarRadialChart` from T002.
- **Expected lift sort**: ties broken by Supabase order (priority asc).
- **Evidence href**: builds `?evidence=<id>` placeholder — actual screenshot serving = future sprint.
- **Export PDF**: visible-but-disabled pill, `aria-disabled` + click prevented. URL slot already reserved.
