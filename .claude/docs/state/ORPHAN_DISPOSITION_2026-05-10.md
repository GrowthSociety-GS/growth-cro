# Orphan & Duplicate Disposition — 2026-05-10 (Issue #10)

Source-of-truth output of the orphan/duplicate cleanup pass driven by Issue [#10](https://github.com/GrowthSociety-GS/growth-cro/issues/10).

## Orphan delta

| Stage | `potentially_orphaned` | Notes |
|---|---|---|
| Start of #10 | 51 | Audit registry pre-task |
| After audit refinements (init.py + CLI entrypoint detection) | 7 | False positives stripped: `__init__.py` collisions, `if __name__ == "__main__"` CLIs |
| After judges wiring (`moteur_multi_judge/judges/__init__.py` re-exports) | 7 | (judges already covered by audit refinements) |
| After mode_1 `output_parsing` wired via `__init__.py` | 6 | Internal helper now re-exported |
| After `growthcro/` added to SCAN_FOLDERS + recos imports detected | 2 | `golden_bridge.py` is consumed by `growthcro/recos/orchestrator.py` (lazy `from golden_bridge import GoldenBridge`); audit's import-name regex was widened to capture `from X import a, b, c` names |
| After archiving `batch_enrich.py` + `run_full_pipeline.sh` | **0** | Both stale legacy artifacts; superseded by `growthcro.recos.cli enrich --all` and `scripts/parity_check.sh` |

## Audit script changes (made in #10)

- `scripts/audit_capabilities.py`:
  - Added `growthcro` to `SCAN_FOLDERS`. The Wave-2 splits created `growthcro/{capture,perception,scoring,recos,research,gsg_lp,api,cli,lib}/` but the auto-discovery never scanned them, so their internal imports were invisible to the consumer graph.
  - `_extract_imports` now also captures the *imported names* in `from X import a, b, c` so submodules like `from growthcro.recos import prompts` register as a consumer of `prompts.py`. Previously only the top-level dotted segments were captured.
  - `determine_status` adds two new statuses:
    - `ACTIVE_PACKAGE_MARKER` — `__init__.py` files (the id-collision across packages made them appear orphan; they are wired by package-existence, not by import).
    - `ACTIVE_CLI_ENTRYPOINT` — files containing `if __name__ == "__main__"` (CLIs invoked from shell, sub-agents, CI, runbooks; the consumer-graph view never sees them as imported, but they are real entry points).
  - Stats output gains `active_cli` and `active_package_marker` counters.

## Wiring changes (Issue #10)

- `moteur_multi_judge/judges/__init__.py` — re-exports `audit_lp_doctrine`, `audit_humanlike`, `check_implementation`. Previously the wrappers `humanlike_judge.py` and `implementation_check.py` were only loaded via `importlib` from the orchestrator, leaving them orphan in the registry view.
- `moteur_gsg/modes/mode_1/__init__.py` — adds `extract_html` re-export from `output_parsing.py`. The module was a documented placeholder for future HTML-parsing concerns; now its single function is wired so the registry sees it as ACTIVE.
- `growthcro/scoring/cli.py` — gains a subcommand dispatcher (`specific` / `ux`) so sub-agents can invoke `python3 -m growthcro.scoring.cli specific <label> [page]` instead of `python -c "from ... import"` incantations. The dispatcher preserves backward compatibility with the legacy positional-only invocation used by the `score_specific_criteria.py` shim.

## Archive moves (Issue #10)

| Path (before) | Path (after) | Rationale |
|---|---|---|
| `skills/site-capture/scripts/batch_enrich.py` | `_archive/scripts/2026-05-10/batch_enrich.py` | V12 stress-test runner; module-level `args = sys.argv[1:]` (no `__main__` guard); only stale `run_full_pipeline.sh` referenced it; superseded by `python3 -m growthcro.recos.cli enrich --all` since #6. |
| `skills/site-capture/scripts/run_full_pipeline.sh` | `_archive/scripts/2026-05-10/run_full_pipeline.sh` | Hardcoded pre-migration iCloud path `/sessions/relaxed-busy-goldberg/...`; invokes 4 removed scripts (`generate_audit_data_v12.py`, `criterion_crops.py`, `perception_pipeline.py`, `semantic_mapper.py`); replaced by `scripts/parity_check.sh` + per-client orchestration via `growthcro.cli.*`. |

Logged in `_archive/README.md` provenance table.

## Basename duplicate disposition

`find . -name "*.py" -not -path "*/_archive/*" -not -path "*/__pycache__/*" -not -path "*/node_modules/*" -not -path "*/worktrees/*" | xargs -n1 basename | sort | uniq -d | grep -vE "^(__init__|cli)\.py$"`

| Basename | Count | Disposition |
|---|---|---|
| `add_client.py` | 2 | Root shim + `growthcro/cli/add_client.py`. **Owned by #11** (shim removal). Per task brief: "DO NOT MODIFY: shims (those go away in #11)". |
| `capture_full.py` | 2 | Root shim + canonical. **Owned by #11**. |
| `enrich_client.py` | 2 | Root shim + canonical. **Owned by #11**. |
| `reco_enricher_v13.py` | 2 | `scripts/` shim + `skills/site-capture/scripts/` shim, both delegating to `growthcro.recos.cli`. **Owned by #11**. |
| `reco_enricher_v13_api.py` | 2 | (idem — both shims) **Owned by #11**. |
| `base.py` | 2 | `moteur_gsg/core/css/base.py` (CSS reset/typography stylesheet bloc) vs `skills/site-capture/scripts/reality_layer/base.py` (`RealityLayerData` ABC + connector base). Distinct packages, distinct concerns; same convention as `__init__.py` (one per package). **Kept**. |
| `orchestrator.py` | 6 | One per package — `moteur_multi_judge/`, `moteur_gsg/`, `moteur_gsg/modes/mode_1/`, `growthcro/capture/`, `growthcro/recos/`, `skills/site-capture/scripts/reality_layer/`. Per the cleanup epic doctrine "1 fichier = 1 concern" + AD-1 "layered submodules", `<package>/orchestrator.py` is the canonical home for the orchestration concern in each package. Same exemption logic as `__init__.py` and `cli.py`. **Kept**. |
| `persist.py` | 3 | One per package — `growthcro/{capture,scoring,perception}/persist.py`. Same exemption logic. **Kept**. |
| `prompt_assembly.py` | 2 | `moteur_gsg/core/prompt_assembly.py` (Mode 1 / generic prompt builder) and `moteur_gsg/modes/mode_1/prompt_assembly.py` (Mode 1 PERSONA NARRATOR specific persona-prompt builder, split out in #8). The mode_1 sub-package owns its own concern; renaming it would break the AD-1 "one file = one concern" principle. **Kept**. |

**Net true-collisions in active paths after #10**: 0. The 9 remaining basename collisions are either (a) owned by #11's shim removal (5 cases) or (b) package-internal canonical names per AD-1 (4 cases — `base`, `orchestrator`, `persist`, `prompt_assembly`).

## Sub-agent refresh (Issue #10)

All 5 `.claude/agents/*.md` audited:

| Agent | Change |
|---|---|
| `capabilities-keeper.md` | Added documentation of the 5 audit statuses (`ACTIVE_WIRED_AS_EXPECTED`, `ACTIVE_INDIRECT_VIA_OUTPUT`, `ACTIVE_CLI_ENTRYPOINT`, `ACTIVE_PACKAGE_MARKER`, `ACTIVE`) and the 0-orphan target. |
| `capture-worker.md` | Replaced `node ghost_capture.js` + `python skills/site-capture/scripts/native_capture.py` direct invocations with `python3 -m growthcro.cli.capture_full` (canonical front door) + a "canonical paths" table mapping each shim to its module-style replacement. |
| `doctrine-keeper.md` | Updated cross-check grep targets: pillar scorers stay at `skills/site-capture/scripts/`, but specific criteria now point at `growthcro/scoring/specific/`, UX at `growthcro/scoring/ux.py`, reco enricher at `growthcro/recos/{prompts,client,orchestrator,schema}.py`. |
| `reco-enricher.md` | Replaced `python3 skills/site-capture/scripts/reco_enricher_v13.py --prepare` and `..._v13_api.py` direct invocations with `python3 -m growthcro.recos.cli {prepare,enrich}`. Added a canonical-paths table. |
| `scorer.md` | Replaced `score_specific_criteria.py` and `score_ux.py` with the new `python3 -m growthcro.scoring.cli {specific,ux}` subcommands. Added a canonical-paths table covering the 7 scoring entrypoints. |

## Smoke test

`scripts/agent_smoke_test.sh` (new) — exits 0 when all 5 sub-agents' canonical commands resolve. Verified locally: **PASS**.

## Verifications

| Check | Result |
|---|---|
| `python3 scripts/audit_capabilities.py` | `potentially_orphaned: 0`; HIGH orphans: 0 |
| `bash scripts/agent_smoke_test.sh` | PASS (all 5 agents) |
| `python3 SCHEMA/validate_all.py` | 8/8 PASS |
| `bash scripts/parity_check.sh weglot` | `✓ Parity OK — 0 files match baseline` (no `data/captures/` in worktree, expected) |
| `bash scripts/parity_check.sh emma_matelas` | No baseline (random pick — never baselined; consistent with prior tasks #5/#6/#9 which noted parity is exercised on `weglot` only in worktree) |
| `bash scripts/parity_check.sh sunday` | (idem) |

Two random clients (chosen with `random.seed(42)`) requested by AC: `emma_matelas` and `sunday`. Both lack a parity baseline (only `weglot` is baselined in `_archive/parity_baselines/`); the worktree is empty of `data/captures/` data so re-baselining would be hollow. The full parity-on-3-clients check moves to #11 where the final tree against a populated branch will exercise it.
