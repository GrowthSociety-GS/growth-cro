# T001 — gsg-fs.ts (auto-discover GSG LPs)

**Status** : done
**Effort** : S, 30-45 min

## Goal
Create `webapp/apps/shell/lib/gsg-fs.ts` that scans `deliverables/gsg_demo/*.html` and returns a typed array of `GsgDemo` objects with metadata parsed from filenames + sidecar `*.multi_judge.json` if exists.

## Plan
- Repo root path via `path.resolve(process.cwd(), "..", "..", "..")` (matches `reality-fs.ts`)
- Parse filename for `slug` (basename without `.html`), `page_type` (segment between brand and version, e.g. `weglot-lp_listicle-v272c.html` → `lp_listicle`), `doctrine_version` (last segment, e.g. `v272c`)
- Read sidecar `<slug>.multi_judge.json` if exists → score from `final_score_pct` or fallback `totals.total_pct`
- Empty-dir safe : returns `[]` if dir missing
- Server-only (Node fs)

## Files
- `webapp/apps/shell/lib/gsg-fs.ts` (NEW)
