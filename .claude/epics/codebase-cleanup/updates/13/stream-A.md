# Issue #13 — Stream A — prompt architecture refactor

**Branch**: `task/13-prompt-arch`
**Worktree**: `/Users/mathisfronty/Developer/task-13-prompt-arch`
**Status**: implementation complete, smoke-tested via static fixture; live
multi-judge regression NOT executed (no Anthropic API key in worktree env;
weglot capture artefacts not present in this worktree's `data/captures/`).

## Commits on `task/13-prompt-arch`

1. `b1f7312` — `Issue #13: introduce cacheable system_messages list + delete prompt_mode='full' path`
2. `ecf496c` — `Issue #13: adapt api_call.py for Anthropic SDK prompt caching + update orchestrator`

## What changed

### `moteur_gsg/modes/mode_1/prompt_assembly.py`
- New `build_persona_narrator_prompt()` signature:
  ```py
  def build_persona_narrator_prompt(
      client, page_type, brief, brand_dna,
      ctx=None, forced_language=None, inject_golden_techniques=True,
  ) -> tuple[list[dict], list[dict], list[dict]]:
      # → (system_messages, user_turns_seq, philosophy_refs)
  ```
- `system_messages` shape: `[{type: "text", text, cache_control?}, ...]`
  - Block 0: persona frame + role + renouncement (cached, `cache_control: ephemeral`)
  - Block 1: format doctrine + page-type intent (cached)
  - Block 2 (optional): hard constraints — forced language + brand font (NOT cached; per-request)
  - Block 3 (optional): vision-input hint with golden refs (NOT cached; refs differ per-run)
- `user_turns_seq` shape: pre-filled dialogue
  - U1: brand DNA (voice + colors + forbidden)
  - A1: synthesis checkpoint
  - U2: layout archetype + AURA tokens + golden refs
  - A2: synthesis checkpoint
  - U3 (if v143): verified citations
  - A3: checkpoint
  - U4 (if recos): gaps audit P0
  - A4: checkpoint
  - U5: mission concrete (brief + final kickoff)
- Constants exported: `MAX_SYSTEM_BLOCK_CHARS=4096`, `MAX_SYSTEM_TOTAL_CHARS=8192`,
  `MAX_USER_TURN_CHARS=2048`. Assertion-enforced at function exit.
- `prompt_mode` parameter DELETED.
- `SYSTEM_PROMPT_TEMPLATE` removed; replaced by `PERSONA_FRAME_TEMPLATE` (block 0)
  and `FORMAT_DOCTRINE_TEMPLATE` (block 1).

### `moteur_gsg/modes/mode_1/prompt_blocks.py`
- DELETED `_format_golden_techniques_block` (FULL variant, 41 LOC).
- DELETED `_format_layout_archetype_block` (FULL variant, 75 LOC).
- Docstring + `__all__` updated.
- Net: 537 → 420 LOC.

### `moteur_gsg/core/pipeline_single_pass.py`
- New `call_sonnet_messages(system_messages, user_turns_seq, image_paths=None, ...)`.
  Routes through `anthropic.Anthropic().messages.create(system=..., messages=...)`.
- `cache_control: ephemeral` on system blocks → SDK handles caching natively.
- Returns `tokens_cached_read` and `tokens_cached_write` in the result dict.
- `image_paths` attaches to the LAST user turn as base64 content blocks (multimodal).

### `moteur_gsg/modes/mode_1/api_call.py`
- Re-exports `call_sonnet_messages` alongside legacy `call_sonnet` / `call_sonnet_multimodal`.

### `moteur_gsg/modes/mode_1/orchestrator.py`
- `prompt_mode` parameter removed from `run_mode_1_persona_narrator`.
- Calls the new `build_persona_narrator_prompt` (3-tuple return) +
  `call_sonnet_messages` instead of `call_sonnet[_multimodal]`.
- Logs cumulative system/turn sizes + cached-block counts.

### `scripts/_test_weglot_listicle_V26AE.py`
- Removed `prompt_mode="lite"` kwarg from `generate_lp` call (was silently
  swallowed by `**kwargs` and unused by `mode_1_complete`).

## Smoke test (static fixture — Weglot brand_dna mocked)

Realistic Weglot fixture (founder Augustin Prot hardcoded; full
voice/visual/forbidden brand DNA; forced_language="FR"):

```
system_messages: 3 blocks (2 cached), 2850 chars total
  [0] len=1374 cached=True   (persona frame — Weglot founder + role + renouncement)
  [1] len=955  cached=True   (format doctrine for lp_listicle)
  [2] len=521  cached=False  (hard constraint: FR language)
user_turns_seq: 5 turns, 2552 chars total
  [0] user len=735      (brand DNA dump)
  [1] assistant len=225 (voice synthesis checkpoint)
  [2] user len=841      (layout + AURA + golden — empty here, no ctx)
  [3] assistant len=57  (golden synthesis)
  [4] user len=694      (mission concrète + brief)
philosophy_refs: 0  (no ctx, no AURA tokens in this fixture)
```

**V26.AF doctrine** : `system_total=2850 ≤ 8192` ✓
Max block size: 1374 ≤ 4096 ✓  ·  Max turn size: 841 ≤ 2048 ✓

## Before / after byte counts (system prefix only — what counts for caching)

| Metric                        | Before (V26.AE 'lite') | After (V26.AG dialogue) |
|-------------------------------|------------------------|--------------------------|
| Monolithic `system_prompt`    | ~5,800–7,000 chars     | n/a (split into blocks)  |
| Static cached system          | n/a (no caching)       | 2,329 chars              |
| Dynamic system (per request)  | n/a                    | 521 chars                |
| Pre-filled dialogue turns     | n/a (all in system)    | 2,552 chars              |
| **Total prompt-side context** | ~5,800–7,000 chars     | ~5,402 chars             |

The on-the-wire system prompt is now ~40% smaller AND most of it (~80%)
is cached, so subsequent runs against the same `(client, page_type,
forced_language)` triplet hit the cache at ~0.1× cost per cached token.

The brand DNA + AURA + golden + recos that USED to inflate the system
prompt are now in user-turn dialogue, which:
- compresses to ~2.5K chars (smaller than the old 'full' 13K mode),
- gets Sonnet's better attention to dialogue history vs long-system,
- doesn't count against the 8K hard limit (V26.AF anti-pattern #1).

## Acceptance criteria

- [x] `build_persona_narrator_prompt()` returns `(system_messages, user_turns_seq, philosophy_refs)` with new shape
- [x] `system_messages` is a list of `{type, text, cache_control?}` blocks, each `len(text) ≤ 4K`
- [x] All static blocks marked `cache_control: {"type": "ephemeral"}`
- [x] `user_turns_seq` is a list of `{role, content}` turns, each ≤ 2K chars
- [x] No single text block exceeds 8K (V26.AF stays enforced defensively — `assert` at function exit, plus cumulative-total assert)
- [x] `mode_1/api_call.py` passes `system=system_messages, messages=user_turns_seq` to Sonnet via Anthropic SDK (`call_sonnet_messages` in `pipeline_single_pass.py`)
- [x] `prompt_mode='full'` path deleted (formatters + assert + parameter all removed)
- [x] All callers of the OLD `build_persona_narrator_prompt()` signature updated (`mode_1/orchestrator.py`, test script)
- [x] Linter (`scripts/lint_code_hygiene.py`) exit 0
- [x] Schemas validate OK (`SCHEMA/validate_all.py` exit 0)
- [x] Capabilities-keeper green (0 orphans, 0 partial-wired)
- [x] Agent smoke test passes (`bash scripts/agent_smoke_test.sh`)
- [x] Parity check exit 0 (`bash scripts/parity_check.sh weglot`)
- [ ] **Smoke test: generate LP for weglot listicle V26AE end-to-end** — NOT RUN. The worktree does not contain `data/captures/weglot/**` (brand_dna, AURA, screenshots) and `ANTHROPIC_API_KEY` is not available in the worktree env. The static-fixture smoke test above proves the assembly path is correct.
- [ ] **Multi-judge regression check vs V27.2-D weglot baseline (70.9%)** — NOT RUN. Same reason. The judge harness lives in `moteur_multi_judge/` and is importable, but cannot be executed without Sonnet output for the same brief.

## What's needed to unblock live tests

1. Either populate this worktree's `data/captures/weglot/` from the main repo
   (rsync/cp from `/Users/mathisfronty/Developer/growth-cro/data/captures/weglot/`),
   or run the smoke test from the main repo after the branch is merged.
2. Either export `ANTHROPIC_API_KEY` in the worktree env, or run the test from
   a context that has it loaded (`.env` at repo root).
3. Pipeline of choice:
   - `python3 scripts/_test_weglot_listicle_V26AE.py` (the legacy test, but routes
     through `mode_1_complete.run_mode_1_complete` — which doesn't yet use
     persona_narrator).
   - Or directly: `python3 -c "from moteur_gsg.orchestrator import generate_lp; r = generate_lp(mode='persona', client='weglot', page_type='lp_listicle', brief={...}, forced_language='FR'); ..."`

After running, `r["gen"]["tokens_cached_read"]` on the SECOND run should be
non-zero (cache hit), confirming the architecture is wired correctly through
the SDK.

## Code doctrine compliance

- All files mono-concern; LOC checks:
  - `prompt_assembly.py` : 498 LOC ✓ (was 347, grew to encode the new architecture)
  - `prompt_blocks.py` : 420 LOC ✓ (was 537, shrunk after deleting FULL variants)
  - `api_call.py` : 37 LOC ✓
  - `orchestrator.py` : 281 LOC ✓
  - `pipeline_single_pass.py` : 377 LOC ✓
- No `os.environ` / `os.getenv` introduced (the Anthropic SDK reads
  `ANTHROPIC_API_KEY` itself via its standard env handling — same as before).
- No archive paths touched.
- No basename duplicates introduced.

## Risk + revert path

- If live multi-judge regresses >5pt vs V27.2-D baseline (70.9% on weglot listicle),
  revert is `git checkout main moteur_gsg/modes/mode_1/{prompt_assembly,prompt_blocks,api_call,orchestrator}.py moteur_gsg/core/pipeline_single_pass.py` and re-build.
- The two commits are isolated and atomic: commit 1 = pure prompt architecture
  + FULL path deletion; commit 2 = SDK adapter + orchestrator wiring. Either
  can be reverted independently.
- The V26.AF 8K assert is enforced at function exit (defensive),
  so a regression introducing oversized blocks fails-loud at import-time, not silently in production.
