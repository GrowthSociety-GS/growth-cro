# GitHub Issue Mapping — hardening-and-skills-uplift

Synced: 2026-05-12T07:31:54Z
Repo: [GrowthSociety-GS/growth-cro](https://github.com/GrowthSociety-GS/growth-cro)
Worktree: `../epic-hardening-and-skills-uplift/` on branch `epic/hardening-and-skills-uplift`

## Epic

- **#24** — [Epic: hardening-and-skills-uplift](https://github.com/GrowthSociety-GS/growth-cro/issues/24)

## Tasks (sub-issues of #24)

| Local file | Issue | Title | URL |
|---|---|---|---|
| `25.md` | #25 | Hygiene Quick-Wins | https://github.com/GrowthSociety-GS/growth-cro/issues/25 |
| `26.md` | #26 | Skills Stratosphère S1 Install | https://github.com/GrowthSociety-GS/growth-cro/issues/26 |
| `27.md` | #27 | MCPs Production | https://github.com/GrowthSociety-GS/growth-cro/issues/27 |
| `28.md` | #28 | Observability Migration | https://github.com/GrowthSociety-GS/growth-cro/issues/28 |

## Dependency graph (issue numbers)

```
#25 (Hygiene) ─────┐
                   ├──→ #27 (MCPs prod)
#26 (Skills S1) ───┘            │
                   ↓
#25 ──────────→ #28 (Observability)
```

## Labels applied

- Epic #24: `epic`, `epic:hardening-and-skills-uplift`, `feature`
- Tasks #25–#28: `task`, `epic:hardening-and-skills-uplift`

## Phasing

- **Phase 1 — Hardening (parallel ~3-4j)** : #25 ∥ #26
- **Phase 2 — Equipment (~1j)** : #27
- **Phase 3 — Observability (~4-5j)** : #28

**Critical path** : #25 (4h) ∥ #26 (2h) → #27 (1h) → #28 (4-5j) ≈ ~5-7 jours total.
