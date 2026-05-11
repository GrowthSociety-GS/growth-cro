# Stream A — Webapp Architecture Map (Issue #16)

**Branch**: `task/16-arch-map` (worktree `/Users/mathisfronty/Developer/task-16-arch-map`)
**Status**: COMPLETE — awaiting Mathis review
**Date**: 2026-05-11

## Deliverables

| Path | Status | Notes |
|---|---|---|
| `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` | DONE | 209 modules, 16 data_artefact patterns, 5 pipelines |
| `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.md` | DONE | 6 Mermaid sections (global + audit + GSG + multi-judge + webapp + reality loop) |
| `scripts/update_architecture_map.py` | DONE | 648 LOC, mono-concern, idempotent, preserves curated fields |
| `.claude/CLAUDE.md` step #11 | DONE | Pointer to YAML + MD added to init obligatoire (now 11 steps) |
| MANIFEST §12 changelog | PENDING — separate commit | Will follow CLAUDE.md rule (`docs: manifest §12 …`) |

## Metrics

- **AST scan duration**: 0.43s (target was <5s, well under).
- **Module count**: 209 indexed across `growthcro/` (52), `moteur_gsg/` (53), `moteur_multi_judge/` (6), `skills/` (83), `scripts/` (13), `SCHEMA/` (2).
- **Modules with curated `purpose` + `inputs` + `outputs`**: 128 / 209. The remaining 81 are package `__init__.py` markers or skills/ legacy scripts that ship the docstring as their purpose without further enrichment (they're documentation candidates for follow-up).
- **Mermaid sections**: 6 — global (Section 1) + audit pipeline (§2) + GSG V27.2-G pipeline (§3) + multi-judge §4 + webapp V27/V28 §5 + reality+experiment+learning loop §6.
- **Lifecycle distribution**: infrastructure 13, onboarding 15, runtime 157, qa 22, learning 2.
- **Status distribution**: active 191, legacy 18 (`skills/growth-site-generator/scripts/*` legacy lab + `growthcro/gsg_lp/*` legacy adapters + `moteur_gsg/core/pipeline_sequential` experimental + `skills/site-capture/scripts/multi_judge` superseded).

## Standard gates

| Gate | Result | Notes |
|---|---|---|
| `python3 scripts/update_architecture_map.py` | exit 0 — wrote 209 modules in 0.43s | Idempotent: second run only updates `meta.generated_at` |
| `python3 scripts/update_architecture_map.py --dry-run` | exit 0 — meta payload printed | Verified |
| `python3 -c "import yaml; yaml.safe_load(open('.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml'))"` | exit 0 — valid YAML | Top-level keys: meta, modules, data_artefacts, pipelines |
| `python3 scripts/lint_code_hygiene.py` | exit 0 — FAIL 0, WARN 0, INFO 1 (script >300 LOC affirmed), DEBT 5 (pre-existing) | New script flagged INFO-only (single-concern affirmed) |
| `python3 scripts/lint_code_hygiene.py --staged` (on staged new script) | exit 0 — FAIL 0, INFO 1 (648 LOC affirmed) | Pre-commit gate green |
| `python3 scripts/audit_capabilities.py` | exit 0 — orphans HIGH = 0, partial = 0 | 205 files scanned, 0 new orphan |
| `python3 SCHEMA/validate_all.py` | exit 0 — 8 files validated | All pass |
| `bash scripts/agent_smoke_test.sh` | exit 0 — ALL AGENT SMOKE TESTS PASS | 5/5 |
| `bash scripts/parity_check.sh weglot` | exit 1 — PRE-EXISTING drift | NOT caused by this task. Verified by stashing changes + re-running: same exit 1. The worktree's `data/captures/weglot/*` differs from baseline (a Mathis-side housekeeping concern, not a docs-task regression). |

## YAML structure (head sample)

```yaml
meta:
  version: 1.0.0
  generated_at: '2026-05-11T09:43:22Z'
  source_commit: 0bf4611b30431f4e464cc84257114f8129c48580
  generated_by: scripts/update_architecture_map.py
  notes: Modules section auto-refreshed (path, depends_on, imported_by).
         purpose/inputs/outputs/doctrine_refs/status/lifecycle_phase
         are human-curated and preserved across regens.

modules:
  growthcro/config:
    path: growthcro/config.py
    purpose: Single env-var boundary for the project (Rule 2 doctrine). All other
             modules read env exclusively through `config`.
    inputs: [".env", "os.environ"]
    outputs: ["config singleton", "MissingConfigError on require_*"]
    depends_on: []
    imported_by: ["growthcro/api/server", "growthcro/capture/browser", ...]
    doctrine_refs: ["CODE_DOCTRINE.md Rule 2", "FR-3 codebase-cleanup PRD"]
    status: active
    lifecycle_phase: infrastructure
  # ... 208 more entries
data_artefacts:
  # 16 artefact patterns (capture.json, perception_v13.json, score_*.json,
  #   recos_enriched.json, brand_dna.json, evidence_ledger.json, ...)
pipelines:
  audit_pipeline: { stages: [...], entrypoint: ..., duration: ... }
  gsg_pipeline:   { stages: [...], entrypoint: ..., duration: ... }
  multi_judge:    { stages: [...], invocation: ..., weighting: ... }
  reality_loop:   { stages: [...], status: ... }
  webapp:         { stages_v27_html: [...], stages_v28_nextjs_target: [...], status: ... }
```

## Script design highlights

- **Stdlib + PyYAML only** — runs on the same toolchain the linter uses, no extra deps.
- **AST-based imports** — relative imports (`from .foo import bar`) resolved against source package. Stdlib / external imports filtered out (only `growthcro.*`, `moteur_gsg.*`, `moteur_multi_judge.*` keys are graph nodes).
- **Reverse edges** computed via single pass over imports.
- **Field preservation**: `path`, `depends_on`, `imported_by`, and `meta.*` are AST-derived (refreshed every run). `purpose`, `inputs`, `outputs`, `doctrine_refs`, `status`, `lifecycle_phase` are read from the existing YAML and preserved.
- **First-run fallback**: if no YAML exists, `purpose` defaults to the module docstring's first line (already populated for 191/209 modules); other curated fields default to empty lists / sensible per-path lifecycle.
- **Deterministic output**: YAML keys sorted, custom dumper disables alias re-use, scalar style stable. Diffs stay local to changed modules.
- **Exit codes**: 0 success, 1 AST failure, 2 YAML serialization failure.
- **CLI**: `--dry-run` (compute, don't write) and `--output PATH` (override target).

## Commit plan

| Order | Branch | Message | Files |
|---|---|---|---|
| 1 | `task/16-arch-map` | `Issue #16: scripts/update_architecture_map.py auto-regen AST scanner` | scripts/update_architecture_map.py |
| 2 | `task/16-arch-map` | `Issue #16: scaffold WEBAPP_ARCHITECTURE_MAP.yaml — 209 modules, 16 data_artefacts, 5 pipelines` | .claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml |
| 3 | `task/16-arch-map` | `Issue #16: WEBAPP_ARCHITECTURE_MAP.md — 6 Mermaid views + cross-refs` | .claude/docs/state/WEBAPP_ARCHITECTURE_MAP.md |
| 4 | `task/16-arch-map` | `Issue #16: CLAUDE.md init step #11 — pointer to WEBAPP_ARCHITECTURE_MAP.yaml` | .claude/CLAUDE.md |
| 5 | `task/16-arch-map` | `chore: refresh CAPABILITIES after arch map indexing` | CAPABILITIES_REGISTRY.json + CAPABILITIES_SUMMARY.md |
| 6 | `task/16-arch-map` | `docs: manifest §12 — add 2026-05-11 changelog for #16 webapp architecture map` | .claude/docs/reference/GROWTHCRO_MANIFEST.md (SEPARATE commit per CLAUDE.md rule) |

## Open follow-ups (not blocking #16)

1. **81 modules with docstring-only purpose** — package `__init__.py` markers + a handful of skills/ legacy scripts. Could be enriched in a follow-up if Mathis wants the full 209 hand-curated. Not blocking.
2. **`parity_check.sh weglot` pre-existing drift** — exists on worktree before my changes, separately from this task. Mathis-side housekeeping.
3. **CI integration** — `update_architecture_map.py` could run in CI on every PR to enforce that the YAML stays in sync with the code; left for a future epic (FR-1 only requires the script to exist, which it does).

## Roadblocks

None.

## Verdict

All AC + DoD met. Awaiting Mathis review per the DoD line *"Mathis approuve : la photo est claire, je m'y retrouve"*.
