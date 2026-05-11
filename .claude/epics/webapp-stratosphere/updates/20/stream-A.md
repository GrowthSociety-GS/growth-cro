# Issue #20 — Stream A — Webapp V27 Completion

**Branch**: `task/20-webapp-v27`
**Worktree**: `/Users/mathisfronty/Developer/task-20-webapp-v27`
**Status**: complete — 56 clients live, 3 panes functional, Playwright 28/28 PASS, page load 0.61s (<3s target).

## Commits on `task/20-webapp-v27`

1. `Issue #20: regen deliverables/growth_audit_data.js with 56 clients post-cleanup paths`
2. `Issue #20: fix V27 HTML audit pane — add priority/effort/lift filters`
3. `Issue #20: fix V27 HTML GSG pane — surface 5 modes selector + brief mode injection`
4. `Issue #20: scripts/test_webapp_v27.py Playwright headless smoke (28 checks)`
5. `Issue #20: update WEBAPP_ARCHITECTURE_MAP.yaml data_artefacts + pipelines.webapp_v27`
6. `docs: manifest §12 — add 2026-05-11 changelog for #20 webapp V27 completion` *(separate commit per CLAUDE.md rule)*

## What changed

### `deliverables/growth_audit_data.js` — regenerated
- Source build script: `skills/site-capture/scripts/build_growth_audit_data.py` (803 LOC, KNOWN_DEBT — unchanged this sprint).
- **Path migration check**: the script has NO `skills.site-capture.*` or `growthcro.*` imports. It is pure JSON IO on
  `data/captures/<client>/<page_type>/*.json` plus `data/clients_database.json` and `data/curated_clients_v27.json`.
  Therefore no path migration was needed in the build script post-cleanup. The script was simply re-run.
- **Symlink trick for worktree**: `data/captures/` is gitignored (3.7 GB heavy artifacts). Symlinked from main repo:
  ```bash
  ln -s /Users/mathisfronty/Developer/growth-cro/data/captures data/captures
  ```
- Regen output (verified against task spec):
  - 56 clients (panel_built = panel_size = 56 from `curated_clients_v27.json`)
  - 185 pages
  - 3045 LP-level recos (P0=932 / P1=1115 / P2=50 / P3=948)
  - 170 step-level recos across 13 pages (Japhy, Weglot, Oma, May, Seazon, Andthegreen, Matera, etc.)
  - 8347 evidence items
  - 11.73 MB output size
  - Generated at: 2026-05-11T11:10:06Z
  - Version: `v27.0.0-panel-roles` (unchanged)

### `deliverables/GrowthCRO-V27-CommandCenter.html` — completed
Current state was already in good shape (0.63s load, 0 console errors, 4 views wired). Two targeted completions to
match Issue #20 ACs:

**1. Audit pane — added priority / effort / lift filters** (~25 LOC JS, no new CSS):
- `auditFilters = {priority, effort, lift}` mutable state
- `filterRecos(recos)` pure filter applied between sort and render
- 4-column filter row: priority dropdown · effort bucket (1-4h / 4-16h / 16h+) · lift bucket (1-5% / 5-15% / 15%+) · reset button with live counter `X/Y`
- Reuses existing `.filters`, `.select`, `.btn`, `.reco-list` classes
- Step-recos count surfaced in Evidence KPI tile when present (e.g. Weglot/oma show "X step recos" instead of "client trail")

**2. GSG pane — added 5-mode selector** (~15 LOC JS, no new CSS):
- `GSG_MODES = {complete, replace, extend, elevate, genesis}` const with label + description per mode
- 5-button row at the top of the brief panel; active mode highlighted via `.btn.primary`
- Title attribute = mode description (hover tooltip)
- Brief JSON now embeds `gsg_mode: {id, label, intent}` so the downstream CLI consumer can route to the right mode
- Preview tile and brief meta both update with the active mode label

**Decisions explicitly NOT taken** (out of scope per task spec "PAS DE NOUVELLE FEATURE"):
- No actual mode execution from the browser — V27 stays static HTML, modes are run via `python -m moteur_gsg.orchestrator --mode <X>`
- No Brief V2 wizard UI re-implementation — V27 already exposes a deterministic brief; the V2 wizard lives in `moteur_gsg/core/intake_wizard.py` and is invoked from the CLI
- No KNOWN_DEBT 803-LOC split for `build_growth_audit_data.py` (deferred to a dedicated sprint)
- No lazy-load per-client JSON split — page load is 0.61s, far under the 3s budget; the 11.73 MB upfront load is acceptable

### `scripts/test_webapp_v27.py` — new (188 LOC ≤ 200)
- Mono-concern: Playwright headless smoke test of the V27 HTML.
- 28 checks split across:
  - Page load < 3s
  - DATA exposes ≥50 clients with fleet aggregates
  - 4 views switch correctly
  - Audit pane filter widgets present + functional (P0 filter changes counter)
  - GSG pane exposes 5 modes; each mode toggles active state and updates brief meta
  - 3 clients click load detail (weglot, japhy, random) without console error
  - 0 pageerror, 0 console.error
- CLI: `python3 scripts/test_webapp_v27.py [--headed] [--verbose]`
- Exit 0 if all 28 PASS, 1 if any FAIL.

### `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`
- `data_artefacts.deliverables/growth_audit_data.js`: added consumers (`scripts/test_webapp_v27`), size_mb, status, last_regen, contents breakdown.
- `data_artefacts.deliverables/GrowthCRO-V27-CommandCenter.html`: new entry with views inventory (command / audit / gsg / demo).
- `pipelines.webapp_v27`: new pipeline section describing the static-HTML MVP flow, smoke test, measured load time, pane details + filters + modes.
- `pipelines.webapp` legacy section preserved (talks about both V27 and V28).
- 2 consecutive `python3 scripts/update_architecture_map.py` runs → only `meta.generated_at` differs → idempotent.

## Gates run

| Gate | Result |
| --- | --- |
| `python3 scripts/lint_code_hygiene.py` | exit 0 (10 WARN pre-existing, build_growth_audit_data.py = tracked DEBT 803 LOC) |
| `python3 scripts/audit_capabilities.py` | 0 HIGH orphans, 0 partial |
| `python3 SCHEMA/validate_all.py` | 3325 files validated |
| `bash scripts/agent_smoke_test.sh` | ALL PASS |
| `bash scripts/parity_check.sh weglot` | 108 files match baseline |
| `python3 scripts/update_architecture_map.py` | exit 0, idempotent (only timestamp differs between runs) |
| `python3 scripts/test_webapp_v27.py` | 28/28 PASS, load 0.61s |

## Page load + 56 clients accessibility — verified

- **Measured load time**: 0.61s (file://) — well under the 3s target
- **DATA.clients.length**: 56
- **DATA.fleet**: `{n_clients: 56, n_pages: 185, n_recos: 3045, p0: 932, p1: 1115, p2: 50, p3: 948}`
- Weglot click → clientTitle "Weglot" ✓
- Japhy click → clientTitle "Japhy" ✓
- Random client (Pretto from one run) → clientTitle "Pretto" ✓

## What is NOT shipped this sprint

- Lazy-load split per-client (page load 0.61s makes it unnecessary)
- `build_growth_audit_data.py` 803-LOC split (still KNOWN_DEBT, tracked by linter)
- Real GSG mode execution from the browser (V27 stays static; V28 Epic #21 will introduce server-driven mode runs)
- Reality / Experiment / Learning panes (Epic #23, separate sub-PRD)

## Acceptance Criteria — final crosswalk

| AC | Status | Evidence |
| --- | --- | --- |
| HTML opens without JS error | ✓ | `test_webapp_v27.py` — 0 pageerror, 0 console.error |
| `growth_audit_data.js` regenerated post-cleanup | ✓ | 2026-05-11T11:10:06Z, 56 × 185 × 3045 confirmed |
| `build_growth_audit_data.py` updated for new paths | N/A — script has no `skills.*` or `growthcro.*` imports; pure JSON IO. Documented in this stream-A. |
| 56 clients accessible from Audit pane | ✓ | DATA exposes 56; Playwright clicks 3/56 confirmed |
| 185 pages auditées affichées | ✓ | `fleet.n_pages == 185` |
| 3045 + 170 recos with filters | ✓ | LP-level 3045 in fleet; step-level 170 across 13 pages in source data; priority/effort/lift filters wired in audit pane |
| GSG pane: 5 modes accessible | ✓ | `[data-gsg-mode]` × 5 visible; brief embeds `gsg_mode.id` |
| Playwright test < 3s + nav 3 panes + 3 clients | ✓ | 28/28 checks, load 0.61s |
| 0 console JS error | ✓ | Confirmed |
| Linter / schemas / capabilities green | ✓ | All gates green above |
| MANIFEST §12 entry | ✓ | Separate commit per CLAUDE.md rule |
