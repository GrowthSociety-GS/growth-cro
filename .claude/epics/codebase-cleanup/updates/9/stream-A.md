# Issue #9 — Stream A: root entrypoint reorg

**Branch:** `task/9-root-reorg`  
**Worktree:** `/Users/mathisfronty/Developer/epic-cleanup-task9`  
**Status:** READY for review (not pushed, not merged).

## Commits (4)

| SHA | Message |
| --- | --- |
| `bb7b9ec` | Issue #9: move api_server.py to growthcro/api/server.py + shim |
| `9e50274` | Issue #9: move {add_client,capture_full,enrich_client}.py into growthcro/cli/ + shims |
| `a0bafb3` | Issue #9: update Dockerfile + run_enricher.sh for module entrypoints |
| `8e61d22` | Issue #9: refresh capabilities registry after root reorg |

(Note: git's rename detection bundled the 4 `git mv` operations into the first
commit's diff, even though only the api_server work was the focus. The CLI
*content* edits — import rewrites, ROOT recompute, anthropic-client switch,
shim creation — are isolated in commit `9e50274`. History for all 4 files
is preserved as renames.)

## File map

### Moved (with `git mv` — history preserved)

| Old path | New path | LOC |
| --- | --- | --- |
| `api_server.py` | `growthcro/api/server.py` | 313 |
| `add_client.py` | `growthcro/cli/add_client.py` | 335 |
| `capture_full.py` | `growthcro/cli/capture_full.py` | 505 |
| `enrich_client.py` | `growthcro/cli/enrich_client.py` | 626 |

All under the AD-1 800-LOC ceiling — no splits performed.

### New package init files

- `growthcro/api/__init__.py` (1-line docstring)
- `growthcro/cli/__init__.py` (1-line docstring)

### Root shims (5–10 lines each)

- `api_server.py` — re-exports `app`, boots uvicorn via `config.port()`
- `add_client.py` — `from growthcro.cli.add_client import main`
- `capture_full.py` — `from growthcro.cli.capture_full import main`
- `enrich_client.py` — `from growthcro.cli.enrich_client import main`

## Internal rewiring

- `growthcro/api/server.py`
  - `ROOT = Path(__file__).resolve().parents[2]` (was `.parent`)
  - Capture worker now `subprocess`-runs `python -m growthcro.cli.capture_full`
    instead of resolving a path.
- `growthcro/cli/add_client.py`
  - `from enrich_client import …` → `from growthcro.cli.enrich_client import …`
- `growthcro/cli/capture_full.py`
  - `ROOT = parents[2]`; pre-flight import switched to absolute package path
    (no more `sys.path.insert` hack).
- `growthcro/cli/enrich_client.py`
  - `PROJECT_ROOT = parents[2]`
  - `_require_anthropic` + bare `anthropic.Anthropic()` removed; replaced
    with `from growthcro.lib.anthropic_client import get_anthropic_client`
    (per task spec, ties into the lib factory from #6).

## Env-boundary check

```
$ grep -n "os\.environ\|os\.getenv" growthcro/api/server.py growthcro/cli/*.py
# (no matches)
```

All 4 files hit env exclusively via `growthcro.config`.

## Infra changes

- **Dockerfile**
  - `CMD ["python3", "api_server.py"]` → `CMD ["python3", "-m", "growthcro.api.server"]`
  - Header usage examples updated to `python3 -m growthcro.cli.capture_full …`
  - `COPY . .` left as-is (already copies the whole tree, so the new package ships).
- **docker-compose.yml** — no change needed: services rely on the Dockerfile
  CMD; no inline `command:` references the moved files. YAML parses cleanly
  (`python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))"`).
- **package.json** — no change needed: `"scripts"` references only
  `node skills/site-capture/scripts/ghost_capture.js`,
  `node deliverables/verify_dashboard_v17_2.js`, and `python3 state.py`.
  None of the moved Python entrypoints are referenced.
- **run_enricher.sh** — fully rewritten. Pre-existing script was broken: it
  `cd`'d to `Documents/Claude/Projects/Mathis - Stratégie CRO Interne -
  Growth Society` (stale iCloud path from the V25/V26 migration) and tried
  to run `scripts/reco_enricher_v13_batch.py` (file does not exist in this
  repo). New version `cd`s to its own directory and forwards to
  `scripts/reco_enricher_v13_api.py` (the real batch caller).

## Verification

| Check | Result |
| --- | --- |
| `python3 -m py_compile` on all 4 moved + 4 shims | OK |
| `python3 -m growthcro.cli.add_client --help` | OK (usage prints) |
| `python3 -m growthcro.cli.capture_full --help` | OK |
| `python3 -m growthcro.cli.enrich_client --help` | OK |
| `python3 add_client.py --help` (shim) | OK |
| `python3 capture_full.py --help` (shim) | OK |
| `python3 enrich_client.py --help` (shim) | OK |
| `from growthcro.api.server import app` (with stubbed fastapi) | OK — `app.title == "GrowthCRO API"` |
| `bash scripts/parity_check.sh weglot` | OK (0 diffs vs baseline) |
| `python3 SCHEMA/validate_all.py` | 8/8 PASS |
| `python3 scripts/audit_capabilities.py` | 0 HIGH orphans, 51 potentially-orphan (= baseline) |
| `docker compose config` | not run — `docker` not installed in worktree env. YAML lint via PyYAML passes. |
| `python3 -m growthcro.api.server` boot + `/health 200` | not run — `fastapi`/`uvicorn` not installed in worktree env. Import wiring validated via stubbed module test (above). |

## Agent audit (per task step 13)

`grep -rn '<file>.py' .claude/agents/` for the 4 moved files: only one hit:

- `.claude/agents/capture-worker.md:10` — mentions `add_client.py` in
  documentation prose ("c'est le job de `add_client.py`"). Not a shell-out;
  the shim covers it regardless. **Issue #10 (agent refresh) should update
  the prose to reference `growthcro.cli.add_client` for clarity, but no code
  path is broken today.**

## Deviations from the brief

- **`docker compose up` smoke test:** skipped (docker not installed in this
  worktree environment). YAML schema validated; Dockerfile change is a
  one-line CMD swap with no semantic risk.
- **Live `/health` endpoint test:** skipped (no fastapi installed locally).
  Replaced by stubbed-import smoke test that exercises the entire module
  init path including `growthcro.config.config` access.
- **`run_enricher.sh`:** the brief suggested calling
  `python -m growthcro.cli.enrich_client`, but `enrich_client` is the
  client-onboarding tool (URL + page discovery), not the reco enricher
  batch. The shell script was already a thin wrapper around the
  reco-enricher pipeline (despite the misleading name). I kept its semantics
  (forwards to `scripts/reco_enricher_v13_api.py`) and only fixed its
  brokenness. If the intent was to *replace* it with a CLI shim for
  `growthcro.cli.enrich_client`, please flag.

## Open items

- Issue #10 should:
  - Update `.claude/agents/capture-worker.md` prose to reference the new
    `growthcro.cli.add_client` path (cosmetic — shim works).
  - Refresh `.claude/docs/state/AUDIT_TOTAL_V26AE_2026-05-04.md` Stage-table
    paths (4 rows mention old root paths).
  - Refresh `.claude/docs/reference/HANDOFF_TO_CLAUDE_CODE.md` repo-tree
    diagram (4 lines).
  - Refresh `.claude/docs/reference/RUNBOOK.md` example invocations.
  - Refresh `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §code-tree.
  - Eventually retire the 4 root shims once all docs/agents are clean.
