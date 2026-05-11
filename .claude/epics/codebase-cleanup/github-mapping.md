# GitHub Issue Mapping — codebase-cleanup

Synced: 2026-05-09T11:04:58Z
Repo: [GrowthSociety-GS/growth-cro](https://github.com/GrowthSociety-GS/growth-cro)
Worktree: `../epic-codebase-cleanup/` on branch `epic/codebase-cleanup`

## Epic

- **#1** — [Epic: codebase-cleanup](https://github.com/GrowthSociety-GS/growth-cro/issues/1)

## Tasks (sub-issues of #1)

| Local file | Issue | Title | URL |
|---|---|---|---|
| `2.md`  | #2  | Inventory & parity instrumentation                              | https://github.com/GrowthSociety-GS/growth-cro/issues/2  |
| `3.md`  | #3  | Centralize env/config in growthcro/config.py                    | https://github.com/GrowthSociety-GS/growth-cro/issues/3  |
| `4.md`  | #4  | Move archives out of active paths                               | https://github.com/GrowthSociety-GS/growth-cro/issues/4  |
| `5.md`  | #5  | Split capture god files into growthcro/capture/                 | https://github.com/GrowthSociety-GS/growth-cro/issues/5  |
| `6.md`  | #6  | Split recos god files & dedupe enricher variants                | https://github.com/GrowthSociety-GS/growth-cro/issues/6  |
| `7.md`  | #7  | Split perception & scoring god files                            | https://github.com/GrowthSociety-GS/growth-cro/issues/7  |
| `8.md`  | #8  | Split GSG (moteur_gsg) god files                                | https://github.com/GrowthSociety-GS/growth-cro/issues/8  |
| `9.md`  | #9  | Reorganize root-level Python entrypoints                        | https://github.com/GrowthSociety-GS/growth-cro/issues/9  |
| `10.md` | #10 | Wire orphans, kill remaining duplicates, refresh sub-agents     | https://github.com/GrowthSociety-GS/growth-cro/issues/10 |
| `11.md` | #11 | Remove shims, regenerate manifests, final parity                | https://github.com/GrowthSociety-GS/growth-cro/issues/11 |
| `12.md` | #12 | Code doctrine, hygiene linter & auto-update loop                | https://github.com/GrowthSociety-GS/growth-cro/issues/12 |

## Dependency graph (issue numbers)

```
#2 (baseline)
 │
 ├─→ #3 (config) ──┬─→ #5 (capture)              ─┐
 │                  ├─→ #6 (recos)                │
 │                  ├─→ #7 (perception/scoring)   │
 │                  ├─→ #8 (GSG)                  │
 │                  └─→ #9 (root reorg, after #5) │
 │
 └─→ #4 (archives — independent of #3)            │

  #4, #5, #6, #7, #8, #9 ──→ #10 (orphans+agents) ──→ #11 (shims+manifests) ──→ #12 (doctrine+linter)
```

## Conflicts

- **#5 ↔ #9** — both touch root-level files. #9 declares `depends_on: [#3, #5]` and `conflicts_with: [#5]` → it waits for #5 to land its shim before starting.

## Labels applied

- Epic #1: `epic`, `epic:codebase-cleanup`, `feature`
- Tasks #2–#12: `task`, `epic:codebase-cleanup`
