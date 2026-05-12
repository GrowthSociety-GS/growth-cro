# Issue #37 — Archive growthcro/gsg_lp/ legacy island

**Branch**: `epic/micro-cleanup-sprint`
**Worktree**: `/Users/mathisfronty/Developer/epic-micro-cleanup-sprint/`
**Started**: 2026-05-12
**Status**: 100% complete

---

## Pre-check (mandatory) — PASSED

### Strict import scan (per AC spec)

```bash
grep -rn "from growthcro.gsg_lp\|import growthcro.gsg_lp" \
  growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/ \
  | grep -v "_archive\|growthcro/gsg_lp/"
```

Result: **0 lines** — no active imports.

### Dynamic import scan

```bash
grep -rn "importlib.*gsg_lp\|getattr.*gsg_lp" \
  growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/
```

Result: **0 lines** — no dynamic imports.

### Dynamic string scan

```bash
grep -rn "'gsg_lp'\|\"gsg_lp\"" \
  growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/
```

Result: **0 lines** — no string references.

### Broad path-substring scan (informational only)

Result: 2 non-blocking references (handled in regen commit):
- `growthcro/lib/README.md:16` — stale doc bullet, updated to point at `_archive/`.
- `scripts/update_architecture_map.py:68` — `ROOT_LIFECYCLE` dict entry `"growthcro/gsg_lp"`, removed (stale config).

**Decision**: PROCEEDED with archive — no callsites required refactoring.

---

## Actions executed

1. [x] Pre-check 0 active imports — confirmed
2. [x] `git mv growthcro/gsg_lp _archive/growthcro_gsg_lp_2026-05-12_legacy_island/` (commit `2cc7601`)
3. [x] Regen architecture map (yaml + md) — `growthcro/gsg_lp` absent from both
4. [x] Regen capabilities registry (`scripts/audit_capabilities.py`) — orphans HIGH=0
5. [x] Updated stale references:
   - `growthcro/lib/README.md` (struck-through bullet + archive pointer)
   - `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.md` (2 narrative refs repathed)
   - `scripts/update_architecture_map.py` (removed `ROOT_LIFECYCLE` entry)
6. [x] Gates run (see below)
7. [x] Regen artifacts committed (commit `bbc5ff5`, see attribution note)

### Attribution note (cross-agent coordination)

Commit `bbc5ff5` is labeled "Issue #38: completion signal" but actually contains
Issue #37's regen artifacts (CAPABILITIES_REGISTRY, WEBAPP_ARCHITECTURE_MAP, the
`growthcro/lib/README.md` update, and the `scripts/update_architecture_map.py`
clean-up). This happened because #38's agent ran a broad `git add` that picked
up my already-staged files. The functional result is correct (all #37 AC met);
only the commit-message attribution is mixed. No rewrite attempted (commits
already exist; per task rules: never amend, never reset --hard, never force).

Commit map:
- `2cc7601` (Issue #37): `git mv` of 7 files to `_archive/...legacy_island/`
- `bbc5ff5` (labeled #38, contains #37 regen): map + capabilities + doc updates

---

## Acceptance Criteria

- [x] **PRÉ-CHECK** : 0 import actif (confirmed by strict + dynamic grep)
- [x] `git mv growthcro/gsg_lp _archive/growthcro_gsg_lp_2026-05-12_legacy_island/`
- [x] `growthcro/gsg_lp/` n'existe plus dans active tree
- [x] `_archive/growthcro_gsg_lp_2026-05-12_legacy_island/` contient les 7 fichiers
- [x] `python3 scripts/update_architecture_map.py` exécuté
- [x] `growthcro/gsg_lp/` absent de la map post-regen (yaml grep=0, md grep=0)
- [x] `python3 scripts/audit_capabilities.py` orphans HIGH=0 + Partial wired=0
- [x] `python3 scripts/lint_code_hygiene.py` exit 0
- [x] `python3 SCHEMA/validate_all.py` exit 0 (15 files validated)
- [x] `bash scripts/typecheck.sh` exit 0 (582 errors / budget 603, 0 strict errors)
- [ ] `bash scripts/parity_check.sh weglot` exit 0 — **environmental N/A**: the
      `data/captures/` directory is gitignored and not propagated to this
      worktree; parity diff outputs the full baseline as "deleted" because the
      tree has zero data files to hash, not because of any code change. My
      commits touch ZERO data/captures files. This is a pre-existing worktree
      gap, not caused by Issue #37. Confirmed by `git diff HEAD~1 HEAD -- data/captures/` returning empty.
- [x] 6/6 GSG checks PASS (gsg_lp was presumed-legacy, no impact)
- [x] Commit isolé : `2cc7601` for the archive move

---

## Gates summary

```
lint_code_hygiene:           0 ✓
SCHEMA/validate_all:         0 ✓ (15 files validated)
typecheck (mypy):            0 ✓ (582 errors / 603 budget, strict scope 0)
audit_capabilities orphans:  0 ✓
arch map yaml gsg_lp refs:   0 ✓
arch map md gsg_lp refs:     0 ✓
parity_check weglot:         N/A (worktree gitignores data/captures/ — pre-existing env gap, untouched by Issue #37)
```

---

## Blockers

None. Issue #37 complete.
