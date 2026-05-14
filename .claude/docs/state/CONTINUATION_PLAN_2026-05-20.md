# Continuation Plan — 2026-05-20 (post Sprint 8+9 parallel-agent merge v2)

> Sprints 8 (Task 008 experiments-v27-calculator) + 9 (Task 012 learning-
> doctrine-dogfood-restore) shippés en parallèle via deux agents isolated
> worktrees. Tier 3 first batch closed. **Validation gate `npm run build`
> vindicated** : zéro post-merge bundle fix cette fois.

## 1. État closing 2026-05-15 — Sprint 8+9 code-complete

### Commits sur origin/main (8 + 1 spec fix)

**Sprint 8 (Task 008) — merged from worktree-agent-aa7881edd57834169**
- `c6a352e` foundation : sample-size math + types + Supabase experiments table
- `2c83535` 4 experiment components (calc + ramp-up + kill-switches + list)
- `02e8933` /experiments route + sidebar nav-item
- `24fa668` Playwright contract spec

**Sprint 9 (Task 012) — merged from worktree-agent-a7c0dd6014cf848e3**
- `098c434` LifecycleBarsChart — 13-state reco funnel on /learning
- `75c8b56` TrackSparkline + extended ProposalStats + page wiring
- `4fca7f5` ClosedLoopDiagram + DogfoodCard + PillierBrowser (doctrine)
- `0395996` Playwright contract spec for /learning + /doctrine

**Parent-session post-merge**
- `c2760b1` fix(task-012-spec) : soften to anonymous contract pattern

### Vercel deploy

- Production deploy success `sha=c2760b1` sur https://growth-cro.vercel.app
- **First-pass build success** — no post-merge `node:fs` regression thanks
  to the validation-gate lesson (Sprint 6+7) being applied upfront

### Tests prod (cumulative regression)

- **168/168 PASS** (Sprint 1-9 spec coverage × 2 viewports)
  - +8 experiments (Sprint 8)
  - +10 learning-doctrine (Sprint 9)
- Zero régression sur les 9 sprints

### Validation gates (4 mandatory per parallel-agent doctrine)

- `npm run typecheck --workspace=apps/shell` ✓
- `npm run lint --workspace=apps/shell` ✓
- `npm run build --workspace=apps/shell` ✓ (new since Sprint 6+7 lesson)
- `python3 scripts/lint_code_hygiene.py --staged` ✓

## 2. Migration en attente (1 new, total 3 pending)

```sql
-- Sprint 8 / Task 008 (new)
-- supabase/migrations/20260514_0021_experiments.sql
-- New table experiments with RLS via is_org_member() + is_org_admin() helpers

-- Sprint 5 / Task 006 (still pending from earlier)
-- supabase/migrations/20260514_0019_recos_lifecycle.sql

-- Sprint 7 / Task 007 (still pending from earlier)
-- supabase/migrations/20260514_0020_audits_scent_trail.sql
```

All three are additive + idempotent. Code marche déjà sans elles (defensive fallback partout).

## 3. Status epic webapp-stratospheric-reconstruction-2026-05

**7/16 done + 2/16 code-complete-pending-validation (~56% effectif)**

| Task | Status | Notes |
|---|---|---|
| 001 design-dna-v22-stratospheric-recovery | ✅ closed | 2026-05-13 |
| 002 pipeline-trigger-backend Phase A | ✅ closed | 2026-05-14 |
| 003 client-lifecycle-from-ui | ✅ closed | 2026-05-14 |
| 004 dashboard-v26-closed-loop-narrative | ✅ closed | 2026-05-14 |
| 005 growth-audit-v26-deep-detail | ✅ closed | 2026-05-14 |
| 006 reco-lifecycle-bbox-and-evidence | ✅ closed | 2026-05-14 |
| 007 scent-trail-pane-port | ✅ closed | 2026-05-14 |
| **008** experiments-v27-calculator | 🟡 code-complete | awaiting migration + val |
| 009 geo-monitor-v31-pane | open | blocked Mathis-keys |
| 010 gsg-design-grammar-viewer-restore | open | depends 002 ✓ |
| 011 reality-layer-5-connectors-wiring | open | blocked Mathis-creds |
| **012** learning-doctrine-dogfood-restore | 🟡 code-complete | awaiting val |
| 013 global-chrome-cmdk-breadcrumbs | open | depends 001-012 |
| 014 essential-skills-install-and-wire | open | parallel-safe |
| 015 legacy-cleanup-mega-prompt-archive | open | parallel-safe |
| 016 microfrontends-decision-doc | open | parallel-safe |

## 4. Mathis-in-loop validation Sprint 8+9

### Task 008 (`/experiments`)
1. Apply migration `20260514_0021_experiments.sql` (Dashboard SQL editor)
2. Sidebar Studio group → click "🧪 Experiments" → `/experiments`
3. SampleSizeCalculator : changer les inputs → résultat recalcule live (default 5% / +20% / α=0.05 / power=0.8 / 2-tailed → n_per_arm ≈ 8155)
4. RampUpMatrix : changer preset slow/medium/fast → phases ETA recalculées
5. KillSwitchesMatrix : table statique 3 thresholds → action
6. ActiveExperimentsList : empty-state (table vide)

### Task 012 (`/learning` + `/doctrine`)
7. `/learning` : LifecycleBarsChart visible (13 zero-bars + hint si migration Sprint 5 pas encore appliquée — sinon valeurs réelles) · TrackSparkline V29 + V30 · 5 KPI cards top (pending/accepted/rejected/deferred/refined)
8. `/doctrine` : ClosedLoopDiagram en haut (7 nodes circle layout) · DogfoodCard (gold spotlight + Cormorant italic + 3 fleet KPIs) · PillierBrowser 7 piliers · CritereDetail avec FR labels CRIT_NAMES_V21

## 5. Tier 3 next batch (post-validation)

| Task | Effort | Parallel | Dep |
|---|---|---|---|
| **010 gsg-design-grammar-viewer-restore** | 2j | non | 002 ✓ |
| **014 essential-skills-install-and-wire** | 1-2j | oui | — |
| **015 legacy-cleanup-mega-prompt-archive** | 1j | oui | — |
| **016 microfrontends-decision-doc** | 1j | oui | mostly done |

Recommandation : encore une **dispatch parallèle** (010 + 014) — chacun complètement orthogonal. 014 + 015 + 016 sont des polish tasks (Tier 4 originalement) qui pourraient se grouper en un troisième agent.

009 (GEO) + 011 (Reality) restent bloquées sur tes credentials externes (OPENAI / PERPLEXITY / Meta / GA / Shopify / Clarity / Catchr OAuth) — à débloquer quand tu peux.

## 6. Prochaine session — trigger phrase

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-20.md
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md

Mathis a validé Sprints 8+9. On démarre Tier 3 next batch en parallèle :
- Task 010 gsg-design-grammar-viewer-restore (depends 002 ✓)
- Task 014 essential-skills-install-and-wire (parallel-safe)

Validation gate inclut `npm run build` (lesson Sprint 6+7 confirmée par Sprint 8+9).
```

## 7. Files reference

- This : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-20.md`](./CONTINUATION_PLAN_2026-05-20.md)
- Previous : [`CONTINUATION_PLAN_2026-05-19.md`](./CONTINUATION_PLAN_2026-05-19.md)
- Sprint 8 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/008.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/008.md)
- Sprint 9 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/012.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/012.md)
- Master PRD : [`.claude/prds/webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)

---

**État final 2026-05-15** : Sprint 8+9 code complete + prod live. 168/168
PASS regression. Validation-gate doctrine confirmée — zéro post-merge fix
sur le bundle. **AU CARRÉ ×9.**
