# Task #25 — Hygiene Quick-Wins · Stream A progress

**Branch** : `task/25-hygiene` (worktree `/Users/mathisfronty/Developer/task-25-hygiene`)
**Status** : COMPLETE — 7 granular commits + 1 manifest commit. Awaiting Mathis sign-off / merge.
**Date** : 2026-05-12

## Actions sequenced by ICE

| # | ICE | Action | Status | Commit |
|---|-----|--------|--------|--------|
| 1 | 800 | `ruff --fix` on Python tree | **PASS** (333 fixes) | `af417a9` |
| 2 | 630 | Fix 2 SQL injection B608 (`google_ads.py`) | **PASS** (1 active + 1 already archived) | `353d59e` |
| 3 | 500 | Tag 4 HIGH bandit hash findings `usedforsecurity=False` | **PASS** | `6564120` |
| 4 | 490 | Replace 4 bare `except:` with `except Exception:` | **PASS** | `5c30c0b` |
| 5 | 490 | Migrate sitemap XML parsing to `defusedxml` | **PASS** | `24065fa` |
| 6 | 300 | Move stale archive folder | **SKIP** (already relocated by prior cleanup; FAIL count was 0 at baseline) | n/a |
| — | — | Regenerate CAPABILITIES_REGISTRY post-ruff | **PASS** | `82a492b` |
| — | — | MANIFEST §12 changelog | **PASS** | `0d10aba` |

## Final gates

| Gate | Result |
|------|--------|
| `python3 scripts/lint_code_hygiene.py` | **FAIL = 0** (12 WARN, 90 INFO over-300-LOC tracked, 34 print-in-pipeline INFO) |
| `python3 scripts/audit_capabilities.py` | **0 orphaned**, 0 partial_wired, 0 potentially_orphaned |
| `python3 SCHEMA/validate_all.py` | **3439 files ✓** |
| `bash scripts/parity_check.sh weglot` | **✓ Parity OK — 108 files match baseline** (exit 0) |
| `bash scripts/agent_smoke_test.sh` | exit 0 (pre-existing `✗ score_page_type.py usage missing` warning — not introduced by this task) |
| `bandit -r growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/` | **HIGH = 0**, MEDIUM B608 = 0, MEDIUM B314 = 0 (remaining medium = 4 hardcoded_password, 8 misc) |
| 6/6 GSG checks | **PASS** (canonical, controlled_renderer, creative_route_selector, visual_renderer, intake_wizard, component_planner) |

## Notes

- **Worktree environment**: `data/captures/`, `data/golden/`, `data/brand_dna/` are gitignored, so they don't exist natively in any new worktree. To run the full gate set (parity + GSG checks), I symlinked these from the main repo. The symlinks are not committed (gitignored). Recommend documenting this in the CCPM worktree setup or pre-populating from main when spawning new task worktrees.
- **Action 6 SKIP rationale**: the path `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` referenced in the task spec does not exist in this branch — it was already relocated by a prior cleanup epic. The custom linter (`lint_code_hygiene.py`) already returned `FAIL = 0` at baseline. No move needed.
- **Pre-existing smoke-test warning**: `✗ score_page_type.py usage missing` appears in `agent_smoke_test.sh` output before and after these commits — orthogonal to Task #25.
- **CAPABILITIES regen necessary**: removing unused imports (F401) changed the import graph, causing the registry's `total_files` to drop 240 → 231 and `active_cli` 49 → 48. Committed separately to keep the registry consistent with the post-ruff source tree.

## Commit log

```
0d10aba docs: manifest §12 — add 2026-05-12 changelog for #25 hygiene quick-wins
82a492b docs: regenerate CAPABILITIES_REGISTRY after Task #25 ruff cleanup
24065fa fix(security): migrate sitemap XML parsing to defusedxml (B314 untrusted XML)
5c30c0b fix(bugs): replace 4 bare except with except Exception (skills/ legacy)
6564120 fix(security): tag 4 weak-hash non-crypto findings usedforsecurity=False (bandit HIGH → 0)
353d59e fix(security): B608 SQL injection google_ads.py — paramétrer GAQL + whitelist page_url
af417a9 chore: ruff --fix on Python tree (333 fixes mécaniques absorbés)
```

## Doctrine preserved

- ≤8 K char persona_narrator prompt — untouched (no V26.AF modifications)
- doctrine V3.2.1 / V3.3 (`playbook/*.json`, `data/doctrine/*`) — untouched
- Notion / `data/clients_database.json` — untouched
- No file > 800 LOC introduced
- Every commit is single-concern and passes `lint_code_hygiene.py --staged` FAIL=0
- No `--force`, no `reset --hard`, no `checkout -- <file>`, no `clean -fd`
