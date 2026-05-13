# Audit A.1 — Code Review (simulated /review) — 2026-05-14

Scope: 83 files / +6509 −359 LOC across SP-7 (modals/CRUD) → SP-11 (screenshots Supabase Storage) + RSC fix + MEGA PRDs.
Range reviewed: `7646619^..f510c49` (full SP-7→SP-11 + post-merge fixes).
Method: Linter + Code Reviewer + Quality + Security focuses.

## Summary
**27 findings**: 3 P0 / 9 P1 / 11 P2 / 4 P3

## Findings

### P0 (broken / blocking)

- [webapp/apps/shell/components/learning/ProposalQueue.tsx:67-69] **`voted` map never cleared on re-vote** — `ProposalVotePanel.setReview(null)` (line 105) toggles the local re-vote UI but the parent `ProposalQueue.voted[proposal_id]` retains the prior review. Re-clicking "re-vote" appears to clear in the row UI but the `enriched` `useMemo` (line 47) keeps applying the stale local review, so the row will silently snap back to "voted" on next parent re-render OR keep the wrong status if the user then casts a NEW vote with `note=""` — the panel sends the new decision but the queue filter still has the old one in `voted`. Worst case: user thinks they revoted but the persisted review on disk diverges from UI optimistic state. Fix: in `ProposalVotePanel`, expose `onCleared` callback (or pass `onVoted(id, null)` cast); in `ProposalQueue.handleVoted`, branch on `review === null` and `delete` from voted map.

- [scripts/upload_screenshots_to_supabase.py:201-237] **`_upload` declared `-> int` but never returns** — Function signature claims to return bytes uploaded (`Returns the number of bytes uploaded`, line 209) but has no `return` statement. Type-only contract is wrong; `mypy --strict` would flag. Currently the caller at line 315 ignores the return value, so no runtime crash, but the contract is broken and future callers depending on the byte count would silently get `None`. Fix: either `return len(payload)` after success or change signature to `-> None` and drop the docstring claim.

- [webapp/apps/shell/app/api/learning/proposals/review/route.ts:1-78] **POST /api/learning/proposals/review has NO auth check, writes to filesystem** — The route accepts unauthenticated POST and writes arbitrary `.review.json` sidecar to `data/learning/.../<id>.review.json`. While `findProposalById` validates the ID against the known list (so the user can't write to arbitrary paths via the proposal_id), there is zero authentication. In prod with Supabase user accounts active, a non-admin (or unauthenticated) user can POST and forge `reviewed_by: "mathis"` (default at line 47, but `body.reviewed_by` is accepted as user input — line 19/47). This is also explicitly acknowledged in the comment "Authentication is not enforced here yet" but the comment then says "V28 shell is single-tenant" which is false post SP-7 (role-based admin gate now exists). Fix: wrap with `requireAdmin()` like SP-7 routes did.

### P1 (degraded UX / important)

- [webapp/apps/shell/lib/captures-fs.ts:202-211] **Hardcoded swap `.png → .webp` is doctrine drift** — `screenshotPublicUrl` rewrites the extension on the fly based on the upload script's convention (line 215-216 of upload script). The two places must stay in sync; a stale convention will produce 404s. The route handler comment at line 200-204 documents it but the doctrine is "single source of truth". Fix: lift the extension swap into a shared `objectKeyFor(clientSlug, pageSlug, filename)` helper used by BOTH the upload script (via subprocess or a shared JSON manifest) and `captures-fs.ts`.

- [webapp/apps/shell/components/audits/AuditDetailFull.tsx:78-92] **`RecosCard` receives unused `clientSlug` prop** — Type declares `clientSlug: string`, parent passes it (line 158), but the function body never reads it. Dead prop. TypeScript noUnusedParameters doesn't catch destructured object fields. Fix: remove `clientSlug` from the inner `RecosCard` Props OR add an action like "← Tous ses audits du même type" link inside the card.

- [webapp/apps/shell/app/api/screenshots/[client]/[page]/[filename]/route.ts:52] **`export const dynamic = "force-dynamic"` defeats CDN cache** — Every screenshot request hits the function (even with `Cache-Control: public, max-age=300` set). Combined with Vercel's billing per invocation and the 8 screenshots × audits load pattern, this can become expensive. The route only does shape validation + a 302 (fast) so the function execution itself is cheap, but the routing-layer cache miss is unnecessary. Fix: drop `force-dynamic` and let Next infer (route handlers are static-ish by default), OR explicitly set `revalidate = 300` and rely on ISR.

- [webapp/apps/shell/components/audits/CreateAuditModal.tsx:107] **`page_slug` derived from `slugify(page_type)` server-side, but client never passes it** — Line 107 of API route: `body.page_slug ? slugify(body.page_slug) : slugify(pageType)`. The CreateAuditModal client has a `page_slug` input (line 142) but it's optional. When two audits are created for the same `(client, page_type)` they get the SAME `page_slug`. The DB likely has `unique (client_id, page_slug)` or the screenshots collide. Verify schema constraint; if no uniqueness enforced, the screenshots panel will show whatever PNG exists for the first audit. Fix: server-side append `-<short_uuid>` when the slug already exists, or surface a uniqueness error.

- [webapp/apps/shell/components/learning/ProposalVotePanel.tsx:67-71] **Optimistic fallback hides server error** — When the server returns 200 OK but `data.review` is missing (malformed response), line 66 falls back to a synthetic review with `reviewed_by: "mathis"` hardcoded. This masks a server bug. Fix: throw if `data.review` is missing on a `2xx` response.

- [webapp/apps/shell/components/funnel/funnel-utils.ts:120] **`generated_at: audit.created_at` may be stale** — When deriving a funnel, the "generated_at" claim uses the audit's `created_at`. The funnel itself was just computed (synchronously, at render time). Misleading for users who interpret it as the funnel's freshness. Fix: use `new Date().toISOString()` for derived funnels (matching the `parseCapturedFunnel` fallback at line 46-48).

- [webapp/apps/shell/components/audits/EditRecoModal.tsx:51] **`payload.severity = severity || null` swallows valid empty string but `severity` is a `<select>` with explicit empty option (line 27)** — When user picks "— aucune" the empty string is sent to server which treats it as "set null" (route.ts line 105). OK behavior but the API route's `ALLOWED_SEVERITY` doesn't include `""` so without the `severity !== null` guard at line 82 of the route, a literal `""` would 400. The current code works because the modal sends `null` not `""` (line 50). But the API contract `severity?: Severity | null` doesn't match real wire format (which can be `null` only). Fix: tighten type or accept `""` server-side explicitly.

- [webapp/apps/shell/components/learning/ProposalDetail.tsx:79] **`Generated: {proposal.generated_at}` prints raw ISO string** — Inconsistent with the rest of the app which uses `toLocaleString()` or `toLocaleDateString("fr-FR")`. UX inconsistency. Fix: format via `new Date(...).toLocaleString()`.

- [webapp/apps/shell/components/funnel/FunnelDropOffChart.tsx:33] **`steps[0].value || 1` non-null assertion masks invariant** — line 32 returns early on `steps.length === 0`, so `steps[0]` exists, but `steps[0].value` could be `0` (legal per type, e.g. measured 0 visitors). The `|| 1` keeps the chart from crashing but produces a misleading bar of 100% width. Fix: when baseline === 0, render an explicit "No traffic" empty state instead.

- [webapp/apps/shell/components/judges/JudgesConsensusPanel.tsx:51-52] **`new Date(payload.generated_at).toLocaleDateString()` without locale arg drifts between Vercel regions** — Server-rendered date will hydrate differently if browser locale differs. Fix: pass `"fr-FR"` for stable hydration.

### P2 (improvement)

- [webapp/apps/shell/components/audits/RichRecoCard.tsx:73] **`<li key={i}>{ex}</li>` uses index as key** — Anti-pattern when the list could be reordered (here it isn't, but consistency suggests using a content-hash). Fix: `key={ex.slice(0, 40) + i}` or just trust array ordering (low value to fix).

- [webapp/apps/shell/components/judges/JudgeScoreCard.tsx:86-100] **Mixed inline styles + class selectors** — `gc-doctrine-bloc` provides the structure but a dozen inline `style={}` overrides cascade on top. Hard to theme. CODE_DOCTRINE mono-concern says presentation lives in `.css`. Fix: extract a `.gc-judge-card` class with modifiers.

- [webapp/apps/shell/lib/use-url-state.ts:50-58] **`useEffect` with `urlValue` dependency + eslint-disable warning baked in** — The comment block at line 53-57 documents a known potential loop. Current `setDraft(urlValue)` is idempotent when `urlValue === draft`, but in React 18 strict mode the effect runs twice and could theoretically queue a fight with a pending debounced write. The mitigation comment promises "useRef ci-dessous gere ca" but the useRef only handles the timer, not the loop. Fix: add an early `if (urlValue === draft) return;` guard or store a `lastWrittenRef` and skip the resync when the change came from our own `writeToUrl`.

- [webapp/apps/shell/components/learning/ProposalQueue.tsx:203] **`inputStyle` constant `React.CSSProperties` typed correctly but duplicated across ProposalQueue/Detail/List** — Three files declare nearly identical `selectStyle`/`inputStyle`. Doctrine code-hygiene says no basename duplicates. Fix: lift to `components/learning/styles.ts` or use foundation `.gc-input` class (already exists per line 87 of ProposalList).

- [webapp/apps/shell/components/audits/EditRecoModal.tsx:131-132] **`SEVERITIES.map((s) => <option key={s || "none"}>)` — `key="none"` collides with hypothetical `s === "none"`** — Not present in current `ALLOWED_SEVERITY`, but a future addition would silently break. Fix: `key={s || "__empty"}`.

- [webapp/apps/shell/components/funnel/funnel-utils.ts:32-37] **`step.drop_pct` parser allows infinity** — `Number.isFinite` guard exists but `Infinity` and negative values pass `typeof === "number"` and get rejected only by `isFinite`. Still, `step.value` line 28 only checks `>= 0` not `isFinite`. A captured `value: Infinity` would propagate. Fix: add `Number.isFinite(step.value)` check.

- [webapp/apps/shell/app/api/clients/[id]/route.ts:21] **No PATCH endpoint** — Audit/recos have PATCH; clients only have DELETE. Inconsistent CRUD surface. (Comment line 5 acknowledges "client edition is V2 scope".) Fix: tracked in V2, OK to defer.

- [scripts/upload_screenshots_to_supabase.py:75-77] **`_env(name, default=None)` returns `default` on empty-string env** — Edge case: if `SUPABASE_URL=""` (empty but set), `system_env` returns `""`, then `value if value else default` returns `default=None`, then `_dry_run()` returns True. Probably correct behavior, but the doctrine `system_env` returns "" not None — the wrapper indirection breaks `Optional[str]` cleanly. Fix: `return value or default` is cleaner and same behavior.

- [webapp/apps/shell/components/audits/AuditScreenshotsPanel.tsx:66-84] **Manual dedup + reorder logic 18 lines** — Could be a one-liner with a Set + array literal. Not wrong, just verbose. Fix: `[...new Set([picks.desktopFold, picks.mobileFold, picks.desktopFull, picks.mobileFull, ...filenames].filter(Boolean))]`.

- [webapp/apps/shell/components/learning/ProposalVotePanel.tsx:29-34] **`BUTTON_BG` hex literals hardcoded** — Brand colors should live in CSS vars (`var(--gc-green)` etc.). Same darkening applied four times. Fix: define `.gc-vote-btn--accept` etc. in globals.css.

- [webapp/apps/shell/components/funnel/FunnelDropOffChart.tsx:44-54] **Color gradient logic by index instead of pillar mapping** — `i === 0 → gold`, `i === last → green`, otherwise cyan. If the 5-step funnel grows to 7 steps, the gradient still works but the visual meaning (gold=start, green=converted) is lost. Fix: pass color via FunnelStep type (`color?: string`) so the caller controls semantics.

### P3 (nice-to-have)

- [webapp/apps/shell/components/audits/CreateAuditModal.tsx:126/140] **French accents replaced with ASCII** — "Optionnel — https:// si renseigne" should be "renseignée". "derive" → "dérivée". Same in `EditRecoModal` line 91/98. Likely encoding loss during paste. Fix: re-encode UTF-8.

- [webapp/apps/shell/components/audits/EditRecoModal.tsx:81] **Hardcoded `maxLength={500}` magic number** — Mirrors API constraint (route.ts line 56). Fix: lift to a shared `RECO_TITLE_MAX_LEN` constant in `@growthcro/data`.

- [webapp/apps/shell/components/funnel/FunnelDropOffChart.tsx:14-18] **Magic numbers WIDTH/HEIGHT_PER_BAR/PADDING_X** — Documented at top, fine as-is but a CSS-var pull would let the user override. Cosmetic.

- [scripts/upload_screenshots_to_supabase.py:162-164] **Docstring says "Quality 85 is the sweet spot" but `quality=75` default at line 162** — Stale comment from the SP-11 fix commit (7e0dddb changed q=85→75). Same drift at line 219. Fix: align docstring to current default.

## Recurring patterns observed

- **Inline `style={}` everywhere** (RichRecoCard, JudgeScoreCard, ProposalQueue, ProposalDetail, FunnelStepsViz). Mixed with `className` foundation classes. ~40 inline styles across new SP-7→10 components. CODE_DOCTRINE.md says mono-concern (presentation in CSS) — soft violation pattern across the entire batch.
- **Defensive parsers returning `null`** (parseCapturedFunnel, parseJudgesPayload, judgesFromAudit). Solid. Consistent pattern. Keep.
- **Optimistic UI without rollback on failure** (ProposalVotePanel, all SP-7 modals): they set local state, call API, on error display the error but the local state often diverges (e.g. ProposalQueue voted map). Pattern needs a `revertOnError` wrapper.
- **Server Components calling `getCurrentRole().catch(() => null)`** in many pages. Good defensive default but it means a Supabase outage = silent demotion to "no admin UI". Consider surfacing an explicit "role check failed, contact admin" notice when the call fails vs returns null cleanly.
- **`force-dynamic` everywhere on Server Components** (clients page, audits page, learning page, funnel page, judges page, recos page, all SP-9 routes). Defeats ISR. Each page is dynamic by data nature (cookies + filters in searchParams) but `force-dynamic` is the heaviest knob. SP-11 screenshots route particularly impactful.
- **API routes return `ok: false, error: <string>` schema** but the strings are inconsistent ("invalid_json", "missing_id", "not_found", "no_fields_to_update", "client_lookup_failed: <pg-error>") — mixing snake_case codes with prose `: details`. Fix toward stable codes + separate `details` field would help client-side error handling.
- **Comment-as-doctrine** — Many SP-9 components have 8-15 line preamble comments. Useful for archeology but a `// SP-N spec` link would suffice. Not wrong, just verbose.

## Recommendations for Wave C (priority order)

1. **Fix P0 #3 (auth on `/api/learning/proposals/review`)** — single largest hole; wrap with `requireAdmin()` to match SP-7 pattern. 30 min.
2. **Fix P0 #1 (ProposalQueue voted map)** — add `onCleared` to `ProposalVotePanel`, clear parent map on re-vote. 45 min.
3. **Fix P1 page_slug collision risk** — server-side append suffix when `(client_id, page_slug)` exists, or surface 409. Verify DB constraint. 1h.
4. **Drop `force-dynamic` on screenshots route + audit force-dynamic on other routes** — cost reduction + perf win. 30 min.
5. **Lift inline styles into CSS classes for SP-10 components** — 6-8 components, mostly mechanical. 2-3h.
6. **Add error rollback to optimistic UI helpers** — wrap fetch in a reusable hook `useOptimisticMutation`. 2h.
7. **Stabilise API error envelope** — define `{ ok: false, code: ALLOWED_CODE, details?: unknown }` and migrate the 8 routes touched in SP-7. 2h.
8. **Doctrine alignment on `quality=75` comments + p0 `_upload -> int`** — type/doc hygiene. 15 min.
9. **Inline `Number.isFinite` guards on funnel `step.value`** — robustness. 15 min.
10. **Stable `toLocaleDateString("fr-FR")` across new components** — hydration parity. 30 min.

Total estimate Wave C: ~10-12h for full sweep, but P0 + top-3 P1 ship in <3h.
