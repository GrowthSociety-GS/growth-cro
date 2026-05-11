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
4. **No basename duplicates in active paths** (excluding `__init__.py`, `cli.py`). Violation example: two `scoring.py` in different packages. Fix: rename one (`pillar_scoring.py` vs `page_scoring.py`) OR keep the canonical package-prefix convention (`{pkg}/base.py`, `{pkg}/orchestrator.py`, `{pkg}/persist.py`, `{pkg}/prompt_assembly.py`) which is AD-1-sanctioned and excluded by the linter's allow-list.

## Rules — soft (heuristic, linter WARN / INFO)

- **WARN — mixed-concern signal**: file >300 LOC AND any of:
  - function-prefix entropy ≥3 distinct prefixes each ≥20% of total functions (`assemble_*` + `save_*` + `run_*` in the same file),
  - imports drawn from ≥3 concern-bundles: `{requests, httpx, urllib}`, `{sqlite3, sqlalchemy, json+pathlib}`, `{jinja2, markdown}`, `{argparse, click}`, `{anthropic, openai}`, `{playwright, selenium}`,
  - ≥2 top-level classes that don't reference each other (per AST).
- **INFO — single-concern affirmation**: file >300 LOC — reviewer must affirm "still single concern" at PR time.

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

## Cross-references

- CLAUDE.md "Init obligatoire" step #10 — doctrine is mandatory init reading.
- CLAUDE.md "Anti-patterns prouvés" entries 8-11 — same rules in narrative form.
- `.claude/agents/*.md` "Refus / Refuse to emit" sections — sub-agents enforce the 4 hard rules before code emission.
- `state.py` — final line shows `CODE HYGIENE — fail: N, warn: M, info: K, debt: D` on every run.
