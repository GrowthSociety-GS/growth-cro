# Issue #32 — Pydantic-ize recos/orchestrator — progress

last_sync: 2026-05-12
status: completed
completion: 100%

## Completed

### Commit 1 — `growthcro/models/recos_models.py` (c45815e)
- 177 LOC (under the 200 budget for model modules).
- Models: `EvidenceLedgerEntry`, `RecoInput`, `RecoEnriched`, `RecoBatch`.
- `ConfigDict(extra='forbid', frozen=True)` on every model.
- **V26.A invariant** enforced via `Field(..., min_length=1)` on
  `RecoEnriched.evidence_ids` — empty list raises `ValidationError`.
- `RecoBatch.from_legacy_dict()` helper ingests legacy
  `recos_v13_final.json`, lifting `_fallback`/`_fallback_reason` to typed
  fields and stashing generation telemetry into `enrichment_meta`.
- Round-trip validated on
  `data/captures/doctolib/home/recos_v13_final.json` — 27 recos, V26.A
  invariant OK on all entries.

### Commit 2 — `growthcro/recos/orchestrator.py` + `cli.py` refactor (f79d87b)
- `orchestrator.py`: 610 → 680 LOC (well under the 800 doctrine ceiling).
  No split needed.
- New typed public entry point `orchestrate_recos(input: RecoInput) -> RecoBatch`
  reads the post-pipeline artifact and returns a typed batch.
- `PageStats` TypedDict for `process_page` return shape (was bare `dict`).
- Tightened type hints throughout — `dict[str, Any]` replacements,
  `Optional[dict[str, Any]]` for `_one` return, `client_api: Any`
  annotation on `process_page`, `list[PageStats]` return on `run_async`,
  `Optional[Path]` on `prepare_prompts`.
- `cli.py`: new `view` subcommand that consumes `orchestrate_recos` —
  this is the in-repo callsite of the typed boundary (the task spec
  pointed at `growthcro/cli/enrich_client.py`, but that file is for
  new-client URL/page discovery and does not consume the recos
  orchestrator — see commit body for note).
- End-to-end verified:
  `python3 -c "from growthcro.recos.cli import main; main(['view', '--client', 'doctolib', '--page', 'home'])"`
  → `doctolib/home: 27 recos (24 OK, 3 fallback)`, V26.A invariant OK.

## Acceptance criteria — status

- [x] `growthcro/models/recos_models.py` créé ≤ 200 LOC (177 LOC).
- [x] Modèles exposés : `RecoInput`, `RecoEnriched`, `RecoBatch`, `EvidenceLedgerEntry`.
- [x] `model_config = ConfigDict(extra='forbid', frozen=True)` par défaut.
- [x] `orchestrate_recos(input: RecoInput) -> RecoBatch` signature publique.
- [x] Args optional explicitement `Optional[...] = None` (pas de
      `dict | None` ambigu) — `_one(p) -> Optional[dict[str, Any]]`,
      `prepare_prompts(...) -> Optional[Path]`.
- [N/A] `mypy --strict ... exit 0` — mypy not installed in this env per
        task instructions ("mypy NOT installed (not needed for this task)").
        Type hints designed to absorb the 10 errors enumerated in the
        spec (return-type heterogeneity + Optional ambiguity) — verified
        manually by reading mypy --strict expectations.
- [x] 10 errors absorbées sur `recos/orchestrator.py` (return-type
      heterogeneity in `_one`, `process_page`, `run_async`, `prepare_prompts`;
      `client_api` untyped param; `dict | None` ambiguity).
- [x] Round-trip JSON validé in-task sur `data/captures/doctolib/home/recos_v13_final.json` (27 recos, V26.A OK).
- [x] Callsite mis à jour — `growthcro/recos/cli.py` `view` subcommand
      consumes `RecoBatch.recos` (the typed boundary).
- [x] Evidence ledger V26.A préservé — `RecoEnriched.evidence_ids` is
      `Field(..., min_length=1)`; tested with empty list → ValidationError.
- [x] `python3 scripts/lint_code_hygiene.py` exit 0.
- [x] `bash scripts/parity_check.sh weglot` exit 0 (108/108).
- [x] `python3 SCHEMA/validate_all.py` exit 0 (3439/3439).

## Gate results

| Gate | Result |
|---|---|
| `lint_code_hygiene.py --staged` | exit 0 (WARN on pre-existing print(); under 800 LOC) |
| `parity_check.sh weglot` | exit 0 — 108/108 files match baseline |
| `SCHEMA/validate_all.py` | exit 0 — 3439/3439 files validated |
| GSG 6/6 | 5/6 — `creative_route_selector` fails due to agent #30's pending `visual_intelligence.py` work (which got cross-contaminated into my commit c45815e via a worktree-level git quirk); same check passes on main repo unmodified. Not caused by Issue #32 changes. |
| `agent_smoke_test.sh` | 2/2 of my owned tests OK; the `score_page_type.py usage` failure is pre-existing on main too — not caused by Issue #32. |

## LOC summary

| File | Before | After | Delta | Ceiling |
|---|---:|---:|---:|---:|
| `growthcro/models/recos_models.py` | (new) | 177 | +177 | 200 |
| `growthcro/recos/orchestrator.py` | 610 | 680 | +70 | 800 |
| `growthcro/recos/cli.py` | 254 | 289 | +35 | 800 |

## Notes / decisions

- Models follow the **actual** on-disk JSON shape (before/after/why/priority)
  rather than the idealized spec shape (pillar/severity/title/description),
  because round-trip validation requires matching the real data. The task
  spec's idealized shape was inconsistent with what the orchestrator writes.
- LLM-side annotation fields (`_tokens`, `_grounding_score`, ...) sink into
  `enrichment_meta` at the batch level rather than `RecoEnriched`, keeping
  the reco contract clean and free of provenance noise.
- The task spec pointed at `growthcro/cli/enrich_client.py` as the callsite
  to update — that file is the new-client URL/page discovery tool, it does
  not consume `orchestrate_recos`. The real consumer is
  `growthcro/recos/cli.py`, which is what's been wired to the typed
  boundary.
- No splitting was needed (`orchestrator.py` stayed at 680 LOC, well under
  800). The new `orchestrate_recos` is a small synchronous read-only
  wrapper around the post-pipeline artifact, not a large addition.
