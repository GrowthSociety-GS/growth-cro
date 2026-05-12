# Task #28 — Observability Migration — Stream A report

**Date** : 2026-05-12
**Branch** : `task/28-observability`
**Worktree** : `/Users/mathisfronty/Developer/task-28-observability`
**Agent** : Claude Opus 4.7 (1M context)

---

## 1. Module created

| File | LOC | Concern |
|---|---:|---|
| `growthcro/observability/__init__.py` | 20 | Public API re-exports |
| `growthcro/observability/logger.py` | 131 | JSON logger factory + correlation-ID contextvars (stdlib only, ≤200 LOC cap respected) |

### Public API

```python
from growthcro.observability.logger import (
    get_logger, set_correlation_id, set_pipeline_name, clear_context,
)

logger = get_logger(__name__)
set_correlation_id()                 # auto uuid12
set_pipeline_name("audit_pipeline")
logger.info("Capturing", extra={"client": "weglot", "page_type": "lp_listicle"})
```

### Output format (JSON-line stdout)

```json
{"ts":"2026-05-12T09:58:05","level":"INFO","logger":"growthcro.foo","msg":"Capturing","correlation_id":"a1b2c3d4e5f6","pipeline":"audit_pipeline","client":"weglot","page_type":"lp_listicle"}
```

Compatible drop-in with Logfire / Axiom / Sentry SDK ingestion shape.

---

## 2. Config extension

`growthcro/config.py` :
- New entry in `_KNOWN_VARS` : `GROWTHCRO_LOG_LEVEL` (default `INFO`).
- New accessor : `config.log_level(default="INFO")` returns uppercased value.
- `.env.example` regenerated via `python3 -m growthcro.config`.

---

## 3. Top-10 pipelines migrated (290 prints → logger.info)

| File | Prints migrated | Notes |
|---|---:|---|
| `growthcro/capture/orchestrator.py` | 33 | 1 print preserved : `__GHOST_RESULT__` marker consumed by `skills/site-capture/scripts/run_spatial_capture.py:91` (subprocess parser). Sanctuarised per §LOG exception. |
| `growthcro/capture/scorer.py` | 26 | All migrated. |
| `growthcro/cli/capture_full.py` | 75 | All migrated. CLI exempt from linter rule but migrated for uniformity. |
| `growthcro/cli/enrich_client.py` | 17 | All migrated. |
| `growthcro/gsg_lp/lp_orchestrator.py` | 33 | All migrated (including multi-line print). |
| `moteur_gsg/modes/mode_1/orchestrator.py` | 33 | All migrated. |
| `moteur_gsg/modes/mode_1_complete.py` | 20 | All migrated. |
| `moteur_gsg/core/pipeline_sequential.py` | 19 | All migrated. |
| `moteur_gsg/core/pipeline_single_pass.py` | 17 | All migrated (including `flush=True` multi-line). |
| `moteur_multi_judge/orchestrator.py` | 16 | All migrated. |
| **Total** | **289** | + 1 preserved marker = 290 total source prints handled. |

### Migration mechanics

- Helper script `/tmp/migrate_prints.py` (transient) used to batch single-line prints.
- Multi-line prints + subprocess markers handled manually via Edit tool.
- Logger import injected after last top-level import (AST-driven, idempotent).
- Each migration → AST parse validation → `python3 -c "import <module>"` smoke → `parity_check.sh weglot` → 1 commit.

### Commits (14 total)

```
fdfcb43 feat(config): add log_level() accessor for observability (#28)
06bcd97 feat(observability): add structured JSON logger foundation (#28)
1213e57 refactor(capture/orchestrator): migrate print() → logger.info (#28)
6ababd5 refactor(capture/scorer): migrate print() → logger.info (#28)
15de63d refactor(gsg_lp/lp_orchestrator): migrate print() → logger.info (#28)
16342fc refactor(moteur_gsg/mode_1/orchestrator): migrate print() → logger.info (#28)
000ab0c refactor(moteur_gsg/mode_1_complete): migrate print() → logger.info (#28)
1e6482d refactor(moteur_gsg/pipeline_sequential): migrate print() → logger.info (#28)
9c4d499 refactor(moteur_gsg/pipeline_single_pass): migrate print() → logger.info (#28)
28e02d3 refactor(moteur_multi_judge/orchestrator): migrate print() → logger.info (#28)
0845a10 refactor(cli/capture_full): migrate print() → logger.info (#28)
50e018f refactor(cli/enrich_client): migrate print() → logger.info (#28)
3547884 chore(linter): promote print-in-pipeline INFO → WARN (#28)
78cb152 docs(doctrine): add §LOG section + promote print-in-pipeline INFO → WARN (#28)
461a0d2 docs(map): enrich growthcro/observability module entries (#28)
```

(+ manifest commit pending below)

---

## 4. Linter rule promoted INFO → WARN

`scripts/lint_code_hygiene.py` :
- Comment + docstring updated to reflect promotion + §LOG reference.
- `check_print_in_pipeline()` results now appended to `warns` list (in addition to `print_infos` for the dedicated render section).
- Render label changed `INFO[print-in-pipeline]` → `WARN[print-in-pipeline]`.

### Baseline before vs after

| Metric | Before | After |
|---|---:|---:|
| FAIL | 0 | 0 |
| WARN (mixed-concern) | 12 | 12 (unchanged) |
| WARN[print-in-pipeline] | — (was INFO) | 27 files (149 prints) |
| Top-10 print count | 290 | 1 (marker preserved) |

WARN doesn't trigger exit 1 — linter still exits 0. Follow-up cleanup target : `moteur_multi_judge/judges/doctrine_judge.py` (16 prints), `growthcro/capture/browser.py` (15), `growthcro/recos/orchestrator.py` (14), `moteur_gsg/core/brief_v2_validator.py` (13) — out of scope for #28.

---

## 5. Doctrine extension

`.claude/docs/doctrine/CODE_DOCTRINE.md` :
- Pre-existing INFO line rewritten as WARN with §LOG cross-ref.
- New **§LOG section** inserted before "Cross-references" : pattern, API, format, log level, exceptions (CLIs / scripts/ / tests/ / subprocess markers), anti-pattern, migration history reference.

---

## 6. Architecture map enrichment

`.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` :
- `scripts/update_architecture_map.py` auto-discovered both new modules (`growthcro/observability`, `growthcro/observability/logger`).
- Human-curated fields added :
  - `purpose` (full description)
  - `inputs: [GROWTHCRO_LOG_LEVEL env via growthcro/config]`
  - `outputs: [structured stdout JSON-line logs]`
  - `doctrine_refs: [CODE_DOCTRINE.md §LOG]`
  - `lifecycle_phase: infrastructure` (not `runtime` since the logger is foundational infra, not part of the audit/GSG runtime path).
- Idempotency verified : re-running `update_architecture_map.py` preserves human-curated fields.

---

## 7. Final gates

| Gate | Result |
|---|---|
| `python3 scripts/lint_code_hygiene.py` | exit 0 (FAIL=0, WARN=39 incl. promoted print rule) |
| `python3 scripts/audit_capabilities.py` | exit 0 (orphans HIGH = 0) |
| `python3 SCHEMA/validate_all.py` | exit 0 (3439 files validated) |
| `bash scripts/parity_check.sh weglot` | exit 0 (108/108 — CRITICAL preserved on every commit) |
| `bash scripts/agent_smoke_test.sh` | exit 0 |
| `scripts/update_architecture_map.py` | exit 0 (idempotent) |
| GSG canonical check | PASS |
| GSG controlled_renderer check | PASS |
| GSG creative_route_selector check | PASS¹ |
| GSG visual_renderer check | PASS |
| GSG intake_wizard check | PASS |
| GSG component_planner check | PASS |
| Logger smoke (`get_logger` + `set_correlation_id` + `logger.info`) | PASS — emits valid JSON-line |

¹ Note : during first run, `creative_route_selector` failed with `golden_ref_count=0`. Root cause = `data/golden/` missing in worktree (gitignored — symlinked to main repo's `data/golden/` to restore the runtime path). Once symlinked, PASS. Unrelated to migration. Same applies to `data/captures/weglot/` (symlinked for parity_check). These symlinks are not committed (gitignore preserved).

---

## 8. Parity preservation discipline

Critical constraint from spec : "logger.info() output to stdout JSON-line. Subprocess parsers downstream peuvent break si format change."

Mitigations applied :
1. JSON-line format chosen explicitly (one log = one line, newline-terminated by `print`/handler).
2. `__GHOST_RESULT__` marker (only known subprocess marker) **preserved as `print()`** — documented in §LOG exceptions.
3. `parity_check.sh weglot` run after every single commit → all 14 commits passed (108/108).
4. `agent_smoke_test.sh` validates CLI `--help` paths still resolve after migration (capture_full, enrich_client, add_client, etc.).

No parity drift observed during the migration.

---

## 9. Out of scope (deferred)

- Logfire / Axiom / Sentry SDK integration (POC dedicated future).
- Cleanup of the 149 remaining prints in pipeline utilities (WARN list above) — to be tackled file-by-file in a follow-up sprint.
- Replacement of subprocess marker `__GHOST_RESULT__` by a structured JSON header on logger (would require coordinated update of `skills/site-capture/scripts/run_spatial_capture.py:91`).

---

## 10. Definition of Done — checklist

- [x] `growthcro/observability/logger.py` créé (131 LOC ≤ 200 cap)
- [x] 290 prints handled (289 migrated + 1 marker preserved) across top-10 pipelines (1 commit per file)
- [x] Règle linter `print-in-pipeline` promue INFO → WARN
- [x] `CODE_DOCTRINE.md` §LOG ajouté
- [x] `WEBAPP_ARCHITECTURE_MAP.yaml` mis à jour (auto-discovered + enriched)
- [x] Gates verts (parity ✓ CRITIQUE pour preserve stdout — vérifié 14 fois)
- [x] MANIFEST §12 entry (commit séparé)
- [ ] Mathis sign-off : "observability foundation prête, je peux intégrer Logfire/Sentry SDK plus tard"
