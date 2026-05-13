# T001 — /clients page progress

## Status
DONE

## Files created
- `webapp/apps/shell/app/clients/page.tsx` — Server Component, reads `searchParams`, applies filter/sort/pagination in-memory, renders `KpiCard` row + `Card` + `ClientFilters` + `ClientList` + `Pagination`.
- `webapp/apps/shell/components/clients/ClientFilters.tsx` — Client Component: debounced search (300ms), category dropdown, score min/max, sort. URL-state via `useRouter().push()` with `scroll: false`.
- `webapp/apps/shell/components/clients/ClientList.tsx` — Server-renderable presentational list (no interactivity); uses next/link → `/clients/[slug]`.
- `webapp/apps/shell/components/clients/Pagination.tsx` — Client Component prev/next with `useSearchParams`, drops `page` param when page=1.

## Data layer
- `listClientsWithStats(supabase)` — existing query, no change.
- View `clients_with_stats` already provides `avg_score_pct + audits_count + recos_count + updated_at`.

## URL state contract
- `?q=<term>` — debounced search on name + slug
- `?category=<slug>` — exact match on business_category
- `?score_min=N&score_max=N` — numeric range on avg_score_pct
- `?sort=name_asc|score_desc|last_audit_desc` — default name_asc
- `?page=N` — 1-indexed, 25 per page (PER_PAGE constant)

## Acceptance criteria
- [x] `/clients` HTTP 200 wired `listClientsWithStats()`
- [x] Affiche name, slug, business_category, avg_score, audits_count, last_audit (via updated_at proxy)
- [x] Filters dropdown business_category + score min/max range
- [x] Search debounced 300ms
- [x] Sort dropdown name asc / score desc / last_audit desc
- [x] Pagination 25/page via URL `?page=N`
- [x] State persistent URL params (shareable, survives refresh)

## Decisions
- **In-memory filter/sort/paginate** on the result of `listClientsWithStats()` rather than pushing predicates to Supabase. Justification: 3 clients seed → trivial; even at 100-client scale this stays < 100 rows × ~12 cols = < 50 KB JSON, well below network roundtrip cost. If we hit 1k clients, push predicates to `.eq() / .gte() / .lte()` server-side.
- **No `react-query` / SWR**: Server Component re-renders on URL change automatically. Avoid client-side cache invalidation overhead.
- **Debounce 300ms**: matches PRD US-1 spec.
