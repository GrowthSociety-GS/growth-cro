# Issue #36 — Split copy_writer.py mono-concern — Progress

## Status: completed (100%)

## Concern mapping (final)

Source: `moteur_gsg/core/copy_writer.py` (was 376 LOC).

### Concern 1 — Prompt assembly (axis 1) — `moteur_gsg/core/copy/prompt_assembly.py` (143 LOC)
- `COPY_SYSTEM_PROMPT` (constant, ~14 lines)
- `COPY_PROMPT_MAX_CHARS = 8000` (constant)
- `_compact_text(value, max_chars)` (helper)
- `_compact_brief_for_copy(brief)` (helper)
- `build_copy_prompt(*, plan, brand_dna)` (main builder)

### Concern 2 — LLM API call (axis 2) — `moteur_gsg/core/copy/llm_call.py` (118 LOC)
- `_strip_json_fences(raw)` (response cleanup)
- `_parse_json(raw)` (response parsing with markdown stripping + brace fallback)
- `call_copy_llm(*, plan, brand_dna, model, max_tokens, temperature, verbose)` (Anthropic call + retry on JSON parse fail)

### Concern 3 — Serializers (axis 8 I/O serialization) — `moteur_gsg/core/copy/serializers.py` (159 LOC)
- `fallback_copy_from_plan(plan)` (deterministic dict builder for smoke/fallback)
- `normalize_copy_doc(copy_doc, plan)` (LLM dict → renderer contract dict)

## Re-export shim — `moteur_gsg/core/copy_writer.py` (27 LOC, was 376)
Thin shim re-exporting all 6 public symbols from `moteur_gsg.core.copy.*`.

## Callsites diff (before vs after)
```
moteur_gsg/modes/mode_1_complete.py:61: from ..core.copy_writer import call_copy_llm, fallback_copy_from_plan
```
Diff empty — only 1 callsite, untouched.

## Gates status (all green)
- `python3 scripts/lint_code_hygiene.py --staged` exit 0 (FAIL=0, 1 WARN print-in-pipeline inherited from original — out of #36 scope; observability migration is #28's job)
- `bash scripts/parity_check.sh weglot` exit 0 (108 files)
- `python3 SCHEMA/validate_all.py` exit 0 (15 files validated)
- `bash scripts/typecheck.sh` exit 0 (mypy strict scope 0 · global 582 ≤ budget 603)
- `python3 scripts/audit_capabilities.py` orphans HIGH = 0
- `python3 scripts/check_gsg_canonical.py` exit 0 (PASS)
- 5 other GSG checks blocked by missing `data/captures/weglot/brand_dna.json` in this worktree (data state, not code) — verified pre-existing on main worktree where they exit 0

## Round-trip imports validated
```
from moteur_gsg.core.copy_writer import *                  → OK
from moteur_gsg.core.copy import *                          → OK
from moteur_gsg.core.copy.prompt_assembly import *          → OK
from moteur_gsg.core.copy.llm_call import *                 → OK
from moteur_gsg.core.copy.serializers import *              → OK
from moteur_gsg.core.copy_writer import call_copy_llm, fallback_copy_from_plan  → OK (legacy callsite)
```
Re-export identity preserved: `build_copy_prompt is moteur_gsg.core.copy.prompt_assembly.build_copy_prompt` → True for all 6 symbols.

## Final LOC summary
| File | LOC | Budget |
|---|---:|---:|
| `moteur_gsg/core/copy_writer.py` | 27 | ≤30 |
| `moteur_gsg/core/copy/__init__.py` | 20 | ≤20 |
| `moteur_gsg/core/copy/prompt_assembly.py` | 143 | ≤200 |
| `moteur_gsg/core/copy/llm_call.py` | 118 | ≤200 |
| `moteur_gsg/core/copy/serializers.py` | 159 | ≤200 |

## Commits
- `787f7a3` — feat(cleanup): split copy_writer.py into 3 mono-concern modules (#36) — note: due to concurrent agent staging race, this commit ended up containing only progress.md files from #37/#38, not the actual code; preserved forward-only per hard rules (no `git reset --soft` allowed without explicit Mathis approval).
- `f1f251e` — Issue #36: split copy_writer.py into copy/{prompt_assembly,llm_call,serializers}.py — the actual code split: 5 files +465/-374.

## Blockers
None. Acceptance criteria met.
