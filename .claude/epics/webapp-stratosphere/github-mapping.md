# GitHub Issue Mapping — webapp-stratosphere

Synced: 2026-05-11T09:30:01Z
Repo: [GrowthSociety-GS/growth-cro](https://github.com/GrowthSociety-GS/growth-cro)
Worktree: `../epic-webapp-stratosphere/` on branch `epic/webapp-stratosphere`

## Epic

- **#14** — [Epic: webapp-stratosphere](https://github.com/GrowthSociety-GS/growth-cro/issues/14)

## Tasks (sub-issues of #14)

| Local file | Issue | Title | URL |
|---|---|---|---|
| `16.md` | #16 | Webapp Architecture Map (YAML + Mermaid, vivant) | https://github.com/GrowthSociety-GS/growth-cro/issues/16 |
| `17.md` | #17 | Skill Integration Blueprint (16 skills, combo packs) | https://github.com/GrowthSociety-GS/growth-cro/issues/17 |
| `18.md` | #18 | Doctrine V3.3 CRE Fusion (O/CO tables + research-first + 69 proposals) | https://github.com/GrowthSociety-GS/growth-cro/issues/18 |
| `19.md` | #19 | GSG Stratosphere (3 LPs non-SaaS-listicle multi-judge ≥70) | https://github.com/GrowthSociety-GS/growth-cro/issues/19 |
| `20.md` | #20 | Webapp V27 Completion (HTML refresh + 56 clients live) | https://github.com/GrowthSociety-GS/growth-cro/issues/20 |
| `21.md` | #21 | Webapp V28 Next.js Migration (Vercel microfrontends + Supabase EU) | https://github.com/GrowthSociety-GS/growth-cro/issues/21 |
| `22.md` | #22 | Agency Products Extension (gads-auditor + meta-ads-auditor) | https://github.com/GrowthSociety-GS/growth-cro/issues/22 |
| `23.md` | #23 | Reality / Experiment / Learning Loop | https://github.com/GrowthSociety-GS/growth-cro/issues/23 |

## Dependency graph (issue numbers)

```
#16 (architecture-map, foundation)
 │
 ├──→ #17 (skill-integration) ──→ #18 (doctrine-v3-3) ──→ #19 (gsg-stratosphere)
 │                                                                │
 └──→ #20 (webapp-v27) ──────────────────────────────────────────┐│
                                                                  ↓↓
                                  #21 (webapp-v28-nextjs) ←──────┤
                                            │
                            ┌───────────────┴───────────────┐
                            ↓                                ↓
                  #22 (agency-products)            #23 (reality-loop)
                                       (dep aussi sur #18)
```

## Labels applied

- Epic #14: `epic`, `epic:webapp-stratosphere`, `feature`
- Tasks #16-#23: `task`, `epic:webapp-stratosphere`

## Worktree convention

- Branch : `epic/webapp-stratosphere` (sibling worktree pattern, per CCPM)
- Sub-task worktrees créés à la volée par sprint si parallélisation : `task/<N>-<short-name>` (ex `task/16-arch-map`)
- Merge stratégie : chaque task branche → merge --no-ff dans `epic/webapp-stratosphere` → merge final dans `main` post-validation Mathis

## Phasing

- Phase 1 (Foundation) : #16 → #17 → ~1-2 semaines
- Phase 2 (Doctrine + GSG) : #18 → #19 → ~2-3 semaines
- Phase 3 (Webapp) : #20 → #21 → ~3-4 semaines
- Phase 4 (Scale + Loop) : #22 ∥ #23 → ~2-3 semaines
