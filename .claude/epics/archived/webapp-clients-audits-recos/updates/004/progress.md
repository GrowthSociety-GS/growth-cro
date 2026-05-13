# T004 — /recos cross-client aggregator progress

## Status
DONE

## Files created / modified
- **Modified** `webapp/apps/shell/app/recos/page.tsx` — replaced the client-picker scaffold (FR-1) with the aggregator. The previous per-client deep-dive at `/recos/[clientSlug]` stays intact.
- **Created** `webapp/apps/shell/components/recos/RecoAggregatorFilters.tsx` — Client Component: priority + criterion + category + sort dropdowns. URL-state via `useRouter().push()` with `scroll: false`.
- **Created** `webapp/apps/shell/components/recos/RecoAggregatorList.tsx` — Server-renderable presentational list with `RecoWithClient` typing. Each card shows priority pill, criterion, business_category, expected_lift_pct gold pill, title, summary, client link, page link, audit link.
- **Modified** `webapp/packages/data/src/queries/recos.ts` — added `RecoWithClient` type + `listRecosAggregate(supabase)` query (2-step: `recos_with_audit` view + `clients` join in-memory).

## Data layer
- **New mono-concern query**: `listRecosAggregate(supabase)` in `@growthcro/data`. Backed by `recos_with_audit` view (already exists in migrations) + a `clients.in(client_ids)` follow-up query, merged in-memory. Returns `RecoWithClient[]` (Reco + client_slug, client_name, client_business_category, page_type, page_slug, doctrine_version).
- Strategy: 2-step query because Supabase PostgREST nested-via-view joins are unreliable. At 100-client × 50-recos scale = 5k rows, the round-trip cost stays under 50 KB.

## URL state contract
- `?priority=P0|P1|P2|P3` — single priority filter (default: all)
- `?criterion=<id>` — single criterion_id filter (default: all)
- `?category=<slug>` — client business_category filter (default: all)
- `?sort=lift_desc|priority_asc` — default: lift_desc (expected_lift_pct desc)
- `?page=N` — 1-indexed, 50 per page

## Acceptance criteria
- [x] `/recos` HTTP 200 wired aggregator query
- [x] Filters priority dropdown (P0/P1/P2/P3/all), criterion_id dropdown, business_category dropdown
- [x] Sort `expected_lift_pct desc` default
- [x] Pagination 50 per page
- [x] Each reco card: client name (link), criterion_id, summary, lift_pct, priority badge
- [x] State persistent URL params (shareable)

## Decisions
- **Replaced the /recos client-picker** since `/clients` (T001) now covers that flow and is the canonical entrypoint. The aggregator is more useful for consultants who want to spot patterns.
- **2-step query** instead of trying to embed clients into recos_with_audit at the SQL level — keeps the data layer simple and reuses existing migrations.
- **In-memory filter/sort/paginate** — same justification as T001 (≤ 5k rows trivial).
- **No client-side debounce** here (no free-text search; all filters are dropdowns).
