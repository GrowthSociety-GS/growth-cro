# Issue #12 — Code doctrine, hygiene linter & auto-update loop

**Branch**: `task/12-doctrine` (worktree at `/Users/mathisfronty/Developer/epic-cleanup-task12`).
**Status**: ready for sign-off and merge of `epic/codebase-cleanup` to `main`.
**Date**: 2026-05-11.

## Summary

Final anti-regression contract for the codebase-cleanup epic. Three artifacts encode the rules so future Claude sessions cannot drift back into the V21→V26 brownfield:

1. **`.claude/docs/doctrine/CODE_DOCTRINE.md`** — 87-line dense doctrine (target ≤200). Principle + 8 axes + 4 hard rules + 3 soft rules + KNOWN_DEBT mechanism + auto-update loop format.
2. **`scripts/lint_code_hygiene.py`** — stdlib-only mechanical gate, ~0.5s on the cleaned tree (target <5s). Exit 0 on the cleaned tree with debt acknowledged.
3. **`CLAUDE.md` / `AGENTS.md` / 5 sub-agent patches** — doctrine becomes mandatory init reading (step #10), anti-patterns 8-11 added, `lint --staged` becomes immuable rule, every sub-agent gains a "Refus / Refuse to emit" section bound to the 4 hard rules.

Plus one functional auto-update demo commit (`docs(doctrine): code +no-print-in-pipelines`) showing the loop is live, not just specified.

## Commits on `task/12-doctrine`

```
106e30c  docs(doctrine): code +no-print-in-pipelines
0a30922  docs(agents): add refusal sections to all 5 sub-agents
985fddb  docs(claude): doctrine init step #10 + anti-patterns 8-11 + lint immuable
f242a41  feat: wire lint summary into state.py
d1ef9c9  feat: scripts/lint_code_hygiene.py (mechanical hygiene gate)
c85be60  feat(doctrine): write docs/doctrine/CODE_DOCTRINE.md
```

6 small themed commits. None push, none merge — branch stays on `task/12-doctrine`.

## Linter timing & scope

- **Tree scan (full)**: 0.50s user / 0.05s system / 0.60s wall (target <5s) — **8× under budget**.
- **Files scanned**: 208 active `.py` files across `growthcro/`, `skills/`, `moteur_gsg/`, `moteur_multi_judge/`, `scripts/`, `SCHEMA/`.
- **Output tiers on cleaned tree**: `fail: 0, warn: 10, info: 82, debt: 5`.
- **Exit code**: 0 (debt is acknowledged via `KNOWN_DEBT` set; not a fail).

## KNOWN_DEBT — the 5 oversize `skills/` files

Hard-coded in `scripts/lint_code_hygiene.py` `KNOWN_DEBT` set and documented in `CODE_DOCTRINE.md` §debt. Linter prints them under a separate `DEBT N files (tracked, see CODE_DOCTRINE.md §debt)` block — exit code stays 0.

| Path | LOC | Concern (split target) |
|---|---:|---|
| `skills/site-capture/scripts/discover_pages_v25.py` | 970 | orchestration + persistence |
| `skills/site-capture/scripts/project_snapshot.py` | 895 | persistence + serialization |
| `skills/site-capture/scripts/playwright_capture_v2.py` | 818 | orchestration + I/O |
| `skills/growth-site-generator/scripts/aura_compute.py` | 816 | scoring + persistence |
| `skills/site-capture/scripts/build_growth_audit_data.py` | 803 | orchestration + serialization |

**Failing-back mechanically impossible**: removing a file from `KNOWN_DEBT` is the same commit as splitting it (the linter is the post-condition).

Path correction vs. stream-A.md from #11: that report listed `skills/site-capture/scripts/aura_compute.py`. The actual file lives at `skills/growth-site-generator/scripts/aura_compute.py`. Same file, correct path now in `KNOWN_DEBT`.

## CODE_DOCTRINE.md table of contents

1. **Principle** — 1 file = 1 concern; 300 = signal; 800 = hard fail.
2. **The 8 canonical concern axes** — prompt assembly · API client · persistence · orchestration · CLI · config · validation · I/O serialization. Each with a real `growthcro/`-tree example.
3. **Rules — hard (4)** — file >800 LOC, env-read outside config, archive in active, basename dup.
4. **Rules — soft (3)** — WARN mixed-concern (3 sub-signals), INFO >300 LOC, INFO print-in-pipeline (loop demo).
5. **Known debt (linter DEBT block)** — the 5 files above.
6. **Auto-update loop** — commit format `docs(doctrine): code +<rule>` · rule · example · tier · linter delta.
7. **How to add / promote / retire a rule** — same commit format for all 3 lifecycle stages.
8. **Linter contract** — stdlib, <5s, exits 0/1/2, flags `--quiet --json --staged`.
9. **Cross-references** — CLAUDE.md step #10, anti-patterns 8-11, sub-agent refusal, `state.py` line.

87 lines total.

## Auto-update loop — chosen example

**Rule**: `+no-print-in-pipelines`. Tier: `info` initially.

**Detection** (grep-based on the cleaned tree):

| Module | print() calls |
|---|---:|
| `growthcro/capture/orchestrator.py` | 34 |
| `growthcro/gsg_lp/lp_orchestrator.py` | 33 |
| `growthcro/capture/scorer.py` | 26 |
| `growthcro/capture/browser.py` | 15 |
| ... (28 more) | ... |
| **Total** | **31 files** |

**Linter check**: `check_print_in_pipeline()` in `scripts/lint_code_hygiene.py` — already wired in the linter commit. Output appears under `INFO[print-in-pipeline] N files (auto-update demo rule)`.

**Promotion plan**: stays `info` until a canonical logger pattern is decided (separate sprint). Promote to `warn` once `growthcro/lib/logger.py` exists and at least 5 pipelines use it.

**Why this rule**: pipelines that print() can't be redirected to structured logs (no levels, no timestamps, mixed with reco outputs). The lint surfaces the offenders so the next sprint can canonicalize a logger without guessing the blast radius.

## CLAUDE.md / AGENTS.md changes

`.claude/CLAUDE.md` (single source — `CLAUDE.md` and `AGENTS.md` at root are symlinks):

- **Init obligatoire**: added step **#10** "Lire `docs/doctrine/CODE_DOCTRINE.md`". Closing line bumped from "9 étapes" to "10 étapes".
- **Anti-patterns prouvés**: added entries **8** (multi-concern), **9** (env outside config), **10** (archive in active), **11** (basename dup). Wording mirrors the 4 hard FAIL rules.
- **Règles immuables**: added "Code hygiene gate — avant tout `git add`, `python3 scripts/lint_code_hygiene.py --staged` doit exit 0".

## Sub-agent refusal sections

All 5 `.claude/agents/*.md` patched with an identical 12-line "Refus / Refuse to emit" section listing the 4 hard rules and the pre-emission `lint --staged` gate:

| Agent | LOC before | LOC after |
|---|---:|---:|
| `capabilities-keeper.md` | 125 | 136 |
| `capture-worker.md` | 46 | 57 |
| `doctrine-keeper.md` | 33 | 44 |
| `reco-enricher.md` | 51 | 62 |
| `scorer.md` | 58 | 69 |

Section wording is uniform across agents — same text, same link to `docs/doctrine/CODE_DOCTRINE.md`.

## state.py wiring

New `render_lint_summary()` calls `python3 scripts/lint_code_hygiene.py --json` (15s subprocess timeout, graceful fallback if unavailable) and prints the canonical summary line:

```
────────────────────────────────────────────────────────────────────────
  CODE HYGIENE (docs/doctrine/CODE_DOCTRINE.md)
────────────────────────────────────────────────────────────────────────
CODE HYGIENE — fail: 0, warn: 10, info: 82, debt: 5
```

Surfaced on every `python3 state.py` (init step #7), so every Claude session sees the linter status before doing anything.

## Final gates

```
python3 scripts/lint_code_hygiene.py     → exit 0    (fail 0)
python3 scripts/audit_capabilities.py    → orphans 0 (HIGH 0, partial 0)
bash scripts/parity_check.sh weglot      → exit 0    (Parity OK)
bash scripts/agent_smoke_test.sh         → exit 0    (ALL AGENT SMOKE TESTS PASS)
python3 SCHEMA/validate_all.py           → exit 0    (8 files validated)
python3 state.py                         → ends on the CODE HYGIENE summary line
```

All green.

## DoD checklist (task spec)

- [x] `CODE_DOCTRINE.md` written, 87 LOC (target ≤200), example-driven
- [x] `lint_code_hygiene.py` runs in 0.60s (target <5s), exits 0 on the cleaned tree
- [x] `state.py` prints linter summary
- [x] `CLAUDE.md` step #10 added; anti-patterns 8-11 added; immuable rule added
- [x] `AGENTS.md` patched (via the symlink — single source `.claude/CLAUDE.md`)
- [x] Every `.claude/agents/*.md` patched with refusal section (5/5)
- [x] One `docs(doctrine): code +<rule>` example commit demonstrating the loop (`+no-print-in-pipelines`)

## Final state

- Worktree clean (`git status` shows only `CAPABILITIES_REGISTRY.json` / `CAPABILITIES_SUMMARY.md` if `audit_capabilities.py` was re-run — those are generated artifacts, not part of this issue).
- Branch on `task/12-doctrine`. **Not pushed, not merged** per task instructions.
- Awaiting Mathis sign-off — this is the gate for merging `epic/codebase-cleanup` to `main`.

## Follow-ups (post-merge sprint candidates)

1. **`skills/` split sprint** — empty `KNOWN_DEBT` by splitting the 5 oversize files into mono-concern modules. Linter will then enforce 0 oversize files in active paths.
2. **Canonical logger** — `growthcro/lib/logger.py` + migrate the 31 print()-in-pipeline files. Promote the `+no-print-in-pipelines` rule from `info` → `warn`.
3. **205 → ≤140 file count** — already documented in #11's scorecard as a placeholder target invalidated by AD-1 (single-concern splits mechanically increase file count). Recommend retiring this target and replacing with "≤60 KLOC active" (already met).
4. **Pre-commit hook installation** — wire `python3 scripts/lint_code_hygiene.py --staged` as a real git pre-commit hook (currently it's a doctrine rule, not a mechanical hook). One-line addition to `.git/hooks/pre-commit` once Mathis confirms.
