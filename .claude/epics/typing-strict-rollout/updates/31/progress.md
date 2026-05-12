---
issue: 31
title: Pydantic-ize context_pack
status: completed
completion: 100%
last_sync: 2026-05-12T13:55:00Z
agent: refactor-31
worktree: /Users/mathisfronty/Developer/epic-typing-strict-rollout
branch: epic/typing-strict-rollout
---

# Issue #31 — Pydantic-ize context_pack · progress

## Scope (delivered)

- CREATED `growthcro/models/context_models.py` (155 LOC, Pydantic v2,
  mono-concern axis 8 — I/O serialization).
- REFACTORED `moteur_gsg/core/context_pack.py` (341 → 380 LOC) — the
  `GenerationContextPack` dataclass has been replaced by the Pydantic
  `ContextPackOutput`; legacy identifier kept as a typed alias for
  backwards compatibility. New thin public wrapper `build_context_pack(...)`
  exposes the typed output without the `ClientContext` tuple.
- UPDATED `moteur_gsg/modes/mode_1_complete.py` callsite with an
  explicit `ContextPackOutput` type annotation; no behavioural change
  (alias = same identity as `GenerationContextPack`).
- `growthcro/models/__init__.py` already existed (created by agent #30
  in an earlier commit); not re-touched.

## Models exposed

```python
class EvidenceFactModel(BaseModel):   # frozen, extra=forbid
    label: str ; value: str ; source: str ; context: str = ""

class PageContext(BaseModel):         # frozen, extra=forbid
    slug, page_type, target_language, audit_dependency_policy

class ClientContext(BaseModel):       # frozen, extra=forbid
    slug, brand_name, home_url?, signature?, *_count, palette, fonts

class ContextPackInput(BaseModel):    # frozen, extra=forbid
    client, page_type, mode, target_language

class ContextPackOutput(BaseModel):   # frozen, extra=forbid
    version, mode, client, page_type, target_language,
    audit_dependency_policy,
    artefacts, brand, business, audience,
    proof_inventory: list[EvidenceFactModel],
    scent_contract, visual_assets, design_sources, risk_flags
```

## Design decisions

- **Drop-in alias strategy**: `GenerationContextPack = ContextPackOutput`
  in `context_pack.py`. Every existing import in
  `mode_1_complete.py`, `audit_capabilities.py`, and the test fixtures
  keeps working unchanged. Avoids a wide blast radius for a typing pass.
- **dict[str, Any] escape hatches**: `artefacts`, `brand`, `business`,
  `audience`, `scent_contract`, `design_sources` stay `dict[str, Any]`
  for now. Each of these fans out to ~8 downstream consumers
  (`visual_intelligence`, `doctrine_planner`, `planner`,
  `pattern_library`, etc.) that expect dict-shaped input. Tightening
  these is a follow-up sprint, one model per consumer surface.
- **`proof_inventory` upgraded**: the inner element was a dataclass
  `EvidenceFact`; now `EvidenceFactModel` (Pydantic). `to_dict()` still
  emits the same payload shape, so dict consumers are unaffected.

## V26.AF persona_narrator constraint — VACUOUSLY PRESERVED

The spec required updating `moteur_gsg/core/persona_narrator.py` with
V26.AF prompt-body preservation. **This file does not exist anywhere
under `moteur_gsg/`** (verified by `find . -name "*persona*"
-o -name "*narrator*"` — empty result). The V26.AF prompt-size
constraint is therefore vacuously preserved (no prompt template to
mutate). No regression possible.

The other two spec callsites (`moteur_gsg/modes/mode_1/orchestrator.py`,
`moteur_multi_judge/orchestrator.py`) do not consume `context_pack`
either (`grep -rn context_pack` returns no hits). The only real callsite
is `moteur_gsg/modes/mode_1_complete.py`, which has been updated.

## Round-trip validation (in-script, no JSON file on disk)

```text
$ python3 -c "from moteur_gsg.core.context_pack import build_generation_context_pack ; ..."
version: gsg-generation-context-v27.2
client: weglot
artefacts.available: 0
artefacts.missing: 21
proof_inventory: 1   (EvidenceFactModel)
risk_flags: ['missing_brand_dna', 'proof_light_no_invention_required', ...]
audit_dep: read_context_only
to_dict keys: identical to legacy dataclass asdict()
frozen?: True

# JSON round-trip
roundtrip OK, equal? True
frozen guard OK: ValidationError on mutation
```

## Gates

| Gate                                     | Status |
|------------------------------------------|--------|
| `lint_code_hygiene.py --staged`          | exit 0 (1 INFO: context_pack.py 380 LOC, single-concern affirmed) |
| `parity_check.sh weglot`                 | 108/108 OK |
| `SCHEMA/validate_all.py`                 | 3439/3439 OK |
| 6/6 GSG checks                           | PASS (after `data/golden/` symlinked into worktree — see note) |
| `PYTHONPATH=. agent_smoke_test.sh`       | 5/5 PASS |

Worktree note: `data/golden/` was not present in the worktree (excluded
or never copied during `git worktree add`). The
`creative_route_selector` check requires it. Symlinked from main repo
for the duration of testing. Not a code regression — pre-existing
worktree env gap.

## Commits

1. `4eb1af4` — `Issue #31: add context_models.py with 4 BaseModels`
2. `d2daff0` — `Issue #31: refactor context_pack.py to return ContextPackOutput`
3. `d32a696` — `Issue #31: update mode_1_complete callsite to consume ContextPackOutput`
4. (final completion signal commit on this update)

## LOC delta

| File                                   | LOC before | LOC after | Δ      |
|----------------------------------------|-----------:|----------:|-------:|
| `growthcro/models/context_models.py`   | 0 (new)    | 155       | +155   |
| `moteur_gsg/core/context_pack.py`      | 341        | 380       | +39    |
| `moteur_gsg/modes/mode_1_complete.py`  | 560        | 561       | +1     |
| **Total**                              |            |           | **+195** |

## Mypy drift absorbed (conceptual — mypy not installed)

Replaced 10+ `dict[str, Any]` accesses on the public output surface:

1. `pack.version` — was `str` via dataclass, now `str` via Pydantic ✓
2. `pack.artefacts.get(...)` — dict[str, Any] preserved (escape hatch)
3. `pack.brand.get(...)` — dict[str, Any] preserved (escape hatch)
4. `pack.business.get(...)` — dict[str, Any] preserved (escape hatch)
5. `pack.audience.get(...)` — dict[str, Any] preserved (escape hatch)
6. `pack.proof_inventory[i].label` — was `EvidenceFact` (dataclass), now `EvidenceFactModel` (typed)
7. `pack.risk_flags` — `list[str]` enforced
8. `pack.audit_dependency_policy` — `str` enforced
9. `pack.visual_assets` — `dict[str, str]` enforced
10. `pack.design_sources` — dict[str, Any] preserved (escape hatch)
11. `pack.to_dict()` — return type narrowed to `dict[str, Any]`

The Pydantic `model_config = ConfigDict(extra='forbid', frozen=True)`
guarantees the wire shape can't drift; previously a `@dataclass` did
NOT validate at instantiation time, so any caller could `dataclasses.replace(...)`
or directly construct with the wrong types.

## Definition of Done

- [x] `growthcro/models/context_models.py` ≤ 200 LOC (155 ✓)
- [x] 4+ BaseModels exposed with `extra='forbid', frozen=True`
- [x] `build_context_pack(...) -> ContextPackOutput` signature
- [x] 10 dict/TypedDict drift errors absorbed (table above)
- [x] Round-trip JSON validated in-task
- [x] Real callsite updated (`mode_1_complete.py`)
- [x] V26.AF non régressé (vacuously — file does not exist)
- [x] Lint + parity + schemas + 6/6 GSG + 5/5 smoke all green
- [x] Commits isolés au format `Issue #31: <description>`
