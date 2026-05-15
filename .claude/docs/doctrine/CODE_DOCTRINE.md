# CODE_DOCTRINE.md — GrowthCRO code hygiene contract

**Status**: active, ≤200 LOC, enforced by `scripts/lint_code_hygiene.py`.
**Anchor**: CLAUDE.md "Init obligatoire" step #10. Every Claude session reads this.
**Origin**: codebase-cleanup epic (Wave-1 → Wave-3, issues #1-#11). Encodes the rules that prevented the V21→V26 brownfield from re-forming.

## Principle

**Un fichier = un concern.** A source file expresses exactly one of the 8 axes below. 300 LOC is a *signal* (reviewer affirms the file is still single-concern). 800 LOC is a **hard fail** — split or refuse to merge.

## The 8 canonical concern axes

Every active `.py` source file self-classifies into exactly one:

1. **prompt assembly** — composes LLM prompts from blocks/templates. *Ex.* `growthcro/recos/prompts.py`, `moteur_gsg/modes/mode_1/prompt_assembly.py`.
2. **API client** — wraps an external SDK / HTTP service. *Ex.* `growthcro/lib/anthropic_client.py`.
3. **persistence** — reads/writes the disk pipeline (`data/captures/.../*.json`, manifests, baselines). *Ex.* `growthcro/scoring/persist.py`, `growthcro/capture/persist.py`.
4. **orchestration** — sequences other modules (pipeline driver). *Ex.* `growthcro/recos/orchestrator.py`, `moteur_gsg/core/pipeline_sequential.py`.
5. **CLI** — `argparse` entrypoint, `python -m growthcro.X.cli`. *Ex.* `growthcro/recos/cli.py`.
6. **config** — env access, paths, constants. **Only `growthcro/config.py` reads env.**
7. **validation** — schema-checks, guard-rails, gates. *Ex.* `growthcro/scoring/validators.py`, `SCHEMA/validate_all.py`.
8. **I/O serialization** — pure dict↔JSON / dict↔text transforms, no I/O. *Ex.* `growthcro/recos/serializers.py`.

If a file mixes two axes, split it. If you can't name the axis, the file is the bug.

## Rules — hard (mechanical, linter FAIL)

1. **No file >800 LOC in active paths.** Violation example: a single `score_pages.py` doing capture loading + scoring + persistence + CLI ≥800 lines. Fix: extract `load_capture.py`, `score_pillars.py`, `persist.py`, `cli.py`.
2. **Env reads (`os.environ`, `os.getenv`) only inside `growthcro/config.py`.** Violation example: `api_key = os.environ["ANTHROPIC_API_KEY"]` in `growthcro/lib/anthropic_client.py`. Fix: `from growthcro.config import ANTHROPIC_API_KEY`.
3. **No `_archive*` / `_obsolete*` / `*deprecated*` / `*backup*` directory inside active paths.** Violation example: `skills/site-capture/scripts/_archive_v24/` exists. Fix: move under root `_archive/`.
4. **No basename duplicates in active paths** (excluding `__init__.py`, `__main__.py`, `cli.py`). Violation example: two `scoring.py` in different packages. Fix: rename one (`pillar_scoring.py` vs `page_scoring.py`) OR keep the canonical package-prefix convention (`{pkg}/base.py`, `{pkg}/orchestrator.py`, `{pkg}/persist.py`, `{pkg}/prompt_assembly.py`) which is AD-1-sanctioned and excluded by the linter's allow-list. `__main__.py` was added to the allow-list 2026-05-15 — Python's `python -m <pkg>` convention is unavoidable when ≥2 packages support module execution (e.g. `growthcro.worker` + `growthcro.geo`).

## Rules — soft (heuristic, linter WARN / INFO)

- **WARN — mixed-concern signal**: file >300 LOC AND any of:
  - function-prefix entropy ≥3 distinct prefixes each ≥20% of total functions (`assemble_*` + `save_*` + `run_*` in the same file),
  - imports drawn from ≥3 concern-bundles: `{requests, httpx, urllib}`, `{sqlite3, sqlalchemy, json+pathlib}`, `{jinja2, markdown}`, `{argparse, click}`, `{anthropic, openai}`, `{playwright, selenium}`,
  - ≥2 top-level classes that don't reference each other (per AST).
- **INFO — single-concern affirmation**: file >300 LOC — reviewer must affirm "still single concern" at PR time.
- **WARN — `print()` in pipeline modules** (promoted from INFO 2026-05-12 via Task #28 observability migration): files under `growthcro/`, `moteur_gsg/`, `moteur_multi_judge/` ≥100 LOC and not a CLI entrypoint must use `growthcro.observability.logger.get_logger(__name__)`, not `print()`. After top-10 migration (300 prints → logger), 27 files remain WARN — low-call-count utilities scheduled for follow-up. See §LOG below for pattern + exceptions.

False positives in the WARN tier are acceptable. Hard FAILs aren't.

## Known debt (linter DEBT block)

5 files in `skills/` exceed 800 LOC — pre-existing structural debt, **out of the cleanup-epic god-file scope** (none in the #5/#6/#7/#8/#9 split inventory). They're tracked in `scripts/lint_code_hygiene.py`'s `KNOWN_DEBT` set and printed under `DEBT N files` (linter still exits 0). **Removing a file from `KNOWN_DEBT` is the same commit as splitting it — failing-back is mechanically impossible.**

| Path | LOC | Concern (target after split) |
|---|---:|---|
| `skills/site-capture/scripts/discover_pages_v25.py` | 970 | orchestration + persistence — split |
| `skills/site-capture/scripts/project_snapshot.py` | 895 | persistence + serialization — split |
| `skills/site-capture/scripts/playwright_capture_v2.py` | 818 | orchestration + I/O — split |
| `skills/growth-site-generator/scripts/aura_compute.py` | 816 | scoring + persistence — split |
| `skills/site-capture/scripts/build_growth_audit_data.py` | 803 | orchestration + serialization — split |

## Auto-update loop

When an agent observes a new anti-pattern, it commits a separate `docs(doctrine): code +<rule>` containing:

1. **One-line rule** (imperative, mechanical when possible).
2. **Concrete violation example** (path + ≤5-line snippet from the current tree, or `INFO`-tier hits enumerated).
3. **Tier**: `fail` (mechanical, exit 1), `warn` (heuristic), or `info` (judgment-based, doctrine text only).
4. **Linter delta** (when fail/warn): the matching check added to `scripts/lint_code_hygiene.py`.

No tool auto-edits the doctrine. The auto-update loop is a *social contract* — one commit, named that way, reviewed like any other change.

## How to add / promote / retire a rule

- **Add**: write the example, write the linter check (or accept it's text-only), commit `docs(doctrine): code +<rule>`.
- **Promote** (info→warn, warn→fail): same commit format, body explains the empirical signal-to-noise that justified the upgrade.
- **Retire** (false-positive epidemic): same commit format, body explains why the rule under-served. Linter check removed in same commit.

## Linter contract

`scripts/lint_code_hygiene.py` is **stdlib-only**, runs <5s, exits:
- `0` — green (or only DEBT/WARN/INFO),
- `1` — at least one FAIL,
- `2` — internal error (file walk crashed).

Flags: `--quiet` (FAIL only), `--json` (machine output), `--staged` (only files in `git diff --staged --name-only`). The `--staged` mode is the pre-commit gate — **immuable rule** in CLAUDE.md: before any `git add` of source files, the linter must exit 0 on the staged set.

## §LOG — Structured logging (V26.AH+, post Task #28)

**Rule**: dans `growthcro/*`, `moteur_gsg/*`, `moteur_multi_judge/*`
(orchestrators / pipelines), utiliser
`growthcro.observability.logger.get_logger(__name__)` au lieu de `print()`.
Le linter `print-in-pipeline` est WARN (promu de INFO le 2026-05-12).

**API publique** (foundation Logfire/Axiom/Sentry future) :

```python
from growthcro.observability.logger import (
    get_logger, set_correlation_id, set_pipeline_name, clear_context,
)

logger = get_logger(__name__)
set_correlation_id()                 # auto uuid12 if no arg
set_pipeline_name("audit_pipeline")
logger.info("Starting capture", extra={"client": "weglot", "page_type": "lp_listicle"})
```

**Format output** : JSON-line stdout. Le formatter émet
`{ts, level, logger, msg, correlation_id?, pipeline?, ...extra}` —
drop-in compatible avec les ingestion SDK Logfire/Axiom/Sentry.

**Log level** : `GROWTHCRO_LOG_LEVEL` (`DEBUG|INFO|WARNING|ERROR`),
défaut `INFO`. Lu via `growthcro.config.config.log_level()`.

**Exceptions OK** (pas de WARN levé) :
- CLIs (`growthcro/cli/*`) — la règle linter exempt déjà ce dossier ; en pratique on migre quand même pour uniformité, sauf si la sortie est consommée par un parser humain interactif.
- Scripts utilitaires (`scripts/*`) — `print()` reste autorisé.
- Tests (`tests/*`) — `print()` reste autorisé.
- Subprocess markers (`__GHOST_RESULT__`, etc.) — **doivent rester `print()`** pour préserver le parsing downstream. Le pattern `__[A-Z_]+_RESULT__` est sanctuarisé.

**Anti-pattern** : `print()` dans un orchestrator post-Task #28 → WARN.
Fix : `logger = get_logger(__name__)` + remplacer `print(x)` par `logger.info(x)`.

**Migration historique (Task #28, 2026-05-12)** : top-10 pipelines migrés
(290 prints → logger.info), 1 commit par fichier. Parity check `weglot` OK
sur tous les commits (108/108).

## §TYPING — Modèles Pydantic à frontière inter-module (depuis 2026-05-12)

**Règle** : tout fichier dont la sortie publique est consommée par ≥2 modules différents DOIT exposer cette sortie via un modèle Pydantic v2 (`pydantic.BaseModel`).

**Pourquoi** :
1. Validation runtime à la frontière catche les schema drifts comme `ValidationError` explicites au lieu de `KeyError` propagés 3 fichiers plus loin.
2. `model_json_schema()` permet l'interop TypeScript pour la webapp V28 (Next.js) via `quicktype` ou `pydantic-to-typescript`.
3. Typage strict mypy actif sur les fichiers à blast radius élevé.
4. Évite l'anti-pattern #8 (fichier multi-concern dict-typed difficile à raisonner sur).

**Comment** :
- Modèles dans `growthcro/models/<topic>_models.py` (mono-concern, ≤200 LOC).
- `model_config = ConfigDict(extra='forbid', frozen=True)` par défaut. `frozen=False` exceptionnel + justification commentaire.
- `dict[str, Any]` interdit en signature publique. Toléré en escape-hatch interne (dict intermédiaire avant assemblage Pydantic) uniquement, et à typer dans un sprint follow-up dédié.
- Invariants métier (ex : V26.A non-empty `evidence_ids`) enforced via `Field(..., min_length=1)` ou validators Pydantic.

**Gate** : `bash scripts/typecheck.sh` doit exit 0. Le script vérifie :
1. `mypy --strict` sur top-3 + `growthcro.models.*` (zero error)
2. `mypy` global sous le budget calibré (régression-proof)

Le budget global est sous-calibré : il diminue à chaque epic qui Pydantic-ise des fichiers supplémentaires. Tightening graduel.

**Config** (`pyproject.toml`) :

```toml
[tool.mypy]
python_version = "3.13"
ignore_missing_imports = true
follow_imports = "silent"
warn_unused_configs = true
strict = false

[[tool.mypy.overrides]]
module = ["moteur_gsg.core.visual_intelligence", "moteur_gsg.core.context_pack", "growthcro.recos.orchestrator", "growthcro.models.visual_models", "growthcro.models.context_models", "growthcro.models.recos_models"]
strict = true
```

**Scope initial (typing-strict-rollout, 2026-05-12)** :
- `moteur_gsg/core/visual_intelligence.py` → `growthcro/models/visual_models.py` (4 models : VisualBlock, VisualHierarchy, VisualScore, VisualReport)
- `moteur_gsg/core/context_pack.py` → `growthcro/models/context_models.py` (5 models : PageContext, ClientContext, ContextPackInput, ContextPackOutput, EvidenceFactModel)
- `growthcro/recos/orchestrator.py` → `growthcro/models/recos_models.py` (4 models : RecoInput, RecoEnriched, RecoBatch, EvidenceLedgerEntry — V26.A invariant enforced)

**Extension future** : top 5 suivants par coupling (capture/orchestrator, mode_1/orchestrator, multi_judge/orchestrator, gsg_lp/lp_orchestrator, scorer) — sprints follow-up dédiés. Chacun fait baisser le budget global.

**Anti-pattern explicite** : ne JAMAIS introduire de `# type: ignore` pour silencer une erreur mypy strict sur le scope. Fixer la cause racine (narrowing, validators, Optional explicite).

## Cross-references

- CLAUDE.md "Init obligatoire" step #10 — doctrine is mandatory init reading.
- CLAUDE.md "Anti-patterns prouvés" entries 8-11 — same rules in narrative form.
- `.claude/agents/*.md` "Refus / Refuse to emit" sections — sub-agents enforce the 4 hard rules before code emission.
- `state.py` — final line shows `CODE HYGIENE — fail: N, warn: M, info: K, debt: D` on every run.
