# Cleanup baseline — codebase-cleanup epic — 2026-05-08

> **Issue:** [#2 Inventory & parity instrumentation](https://github.com/GrowthSociety-GS/growth-cro/issues/2)
> **Branch:** `epic/codebase-cleanup` · **Worktree:** `../epic-codebase-cleanup/`
> **Captured (UTC):** 2026-05-09T11:14Z (after V26.AG fresh-history migration)

This document is the regression contract for the cleanup epic. Every Wave-2/3 task must re-run the parity script and the three instruments below, and verify the results match (or improve, in the orphan-count case) what's snapshotted here.

---

## Canonical client

`weglot` (id `weglot`, `https://www.weglot.com/`) is the parity client per epic spec.
The fresh-history baseline carries pipeline scripts but **no `data/captures/<client>/` outputs** for any client. That is the meaningful state on disk today; baseline locks it in.

## What was snapshotted

| Artefact | Path | Size | Notes |
|---|---|---|---|
| Parity script | `scripts/parity_check.sh` | new | bash + jq, no Python deps |
| Parity baseline (weglot) | `_archive/parity_baselines/weglot/2026-05-09T11-13-30Z/` | empty MANIFEST | `latest` symlink → this dir |
| `audit_capabilities.py` JSON | `_archive/parity_baselines/audit_capabilities_baseline.json` | 89 KB | full registry |
| `audit_capabilities.py` stdout | `_archive/parity_baselines/audit_capabilities_baseline.stdout.txt` | – | summary table |
| `state.py` dump | `_archive/parity_baselines/state_baseline.txt` | 8.0 KB | – |
| `SCHEMA/validate_all.py` log | `_archive/parity_baselines/validate_all_baseline.txt` | 1.3 KB | – |

## Baseline counters (gate metrics)

| Metric | Value | Used by |
|---|---:|---|
| Total `.py` scanned | **144** | Task 12 (linter) |
| Active wired (direct) | 4 | Task 9 |
| Active indirect (via output) | 14 | Task 9 |
| Active misc | 79 | Task 9 |
| Orphans `HIGH` (GSG) | **0** | Task 9 (must stay 0) |
| Partial wired | 0 | Task 9 |
| Potentially orphaned | **47** | Task 9 (target = 0) |
| `SCHEMA/validate_all.py` exit code | **0** | every task |
| Files validated by schemas | 8 | every task |

## How to compare

```bash
# After any move/split, from the worktree root:
bash scripts/parity_check.sh weglot --compare    # exits 0 iff no drift

# Re-run the three instruments and diff their outputs:
python3 scripts/audit_capabilities.py > /tmp/ac.txt
diff /tmp/ac.txt _archive/parity_baselines/audit_capabilities_baseline.stdout.txt

python3 state.py > /tmp/state.txt
diff /tmp/state.txt _archive/parity_baselines/state_baseline.txt

python3 SCHEMA/validate_all.py > /tmp/sv.txt    # must exit 0
diff /tmp/sv.txt _archive/parity_baselines/validate_all_baseline.txt
```

Acceptance contract for any subsequent task:
- `parity_check.sh weglot --compare` → exit 0.
- `SCHEMA/validate_all.py` → exit 0.
- `audit_capabilities.py` stats: `potentially_orphaned` ≤ 47 and `orphaned_from_gsg_HIGH` = 0.
- `state.py` pipeline-stage counts unchanged (all stages currently 0 because no captures exist; if a task triggers any capture, document it).

## Parity contract — functional, not nominal

The cleanup epic adopts AD-9 (unified capability-based naming, git as the only versioning). Filenames, class names, and `version=` strings carrying legacy `V##` stamps WILL be renamed across Wave 2/3. The parity contract therefore enforces **byte-equality of pipeline JSON outputs** (scores, reco IDs, payload structure), and is indifferent to:

- file/module renames in the producing code
- removal of `version="…-vNN"` literals
- relocation of a script from `scripts/` → `growthcro/<package>/`

A rename that demonstrably preserves the same scrubbed JSON output for `weglot` is parity-OK; the baseline is re-locked once and the contract follows the *outputs*.

## Mask spec (parity_check.sh)

Volatile keys scrubbed at every JSON depth before hashing:
`timestamp` · `timestamps` · `generated_at` · `generatedAt` · `created_at` · `createdAt` · `updated_at` · `updatedAt` · `mtime` · `run_id` · `runId` · `uuid` · `id_run` · `cache_key` · `fingerprint` · `elapsed_ms` · `elapsed` · `duration_ms` · `started_at` · `finished_at` · `completed_at`.

Preserved (parity-meaningful):
- numeric scores in pillars + page-type
- reco IDs and structure
- captured URLs, page types, payload arrays

Encoding: `jq -S` (sorted keys), UTF-8. Hash: SHA-256 per file, MANIFEST sorted lexicographically.

Smoke-tested: a synthetic input with timestamps + `run_id` + `mtime` round-trips through the mask; scores (`hero=87`, `psycho=62`, `perception.score=41`) and reco IDs (`reco_001`) survive intact.

## Inline note on `audit_capabilities.py` heuristics

`audit_capabilities.py` ran clean (exit 0). The 47 `POTENTIALLY_ORPHANED` count is the legitimate inventory target for Task 9 (wire-up or archive). The instrument's heuristics (active wired vs indirect-via-output vs misc) classify correctly on a spot-check — no obvious mis-classification observed during this baseline run. **No fix to `audit_capabilities.py` itself is in scope for #2** (per task spec); any tweak lands in #10 alongside the orphan wire-up.

## Branch hygiene

- `epic/codebase-cleanup` is created from `2930580` (the V26.AG migration tip on `main`).
- Worktree at `../epic-codebase-cleanup/` is the only place subsequent epic tasks may commit.
- This baseline commit is the gate. No other task may push until #2 is closed.

## Sign-off

After this commit lands, awaiting Mathis sign-off before #3 (config centralization) starts.
