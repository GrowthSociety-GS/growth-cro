# Continuation Plan — 2026-05-15 (post Sprint 1 + 2 + migration applied)

> **⚠️ Document historique** — superseded par [`CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`](CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md). Conservé pour traçabilité du raisonnement (sprint historique). État canonique post-2026-05-17 vit dans le plan Renaissance + nouveau pivot webapp UX refonte ([PRD](../../prds/webapp-product-ux-reconstruction-2026-05.md) · [Epic](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md)).


> **Point d'entrée prochaine session Claude Code** post-clear.
>
> Tu (Mathis) viens de clear le context. Cette doc + l'epic + le MEGA-PRD
> suffisent à reprendre où on s'est arrêté.

## 1. État closing 2026-05-14 (post-Sprint 2)

### Commits live origin/main (8 commits this 2-day push)

```
f147bfa fix(worker): defensive PATCH fallback for pre-migration schema
5cf1432 test(task-002): runs-trigger spec — maxRedirects:0 (10/10 PASS prod)
f337df7 fix(task-002): consolidate POST /api/runs (Next.js routing constraint)
2b572a1 test(task-002-C): Playwright runs-trigger contract spec
fe33d1f feat(task-002-B): pipeline-trigger frontend — API routes + UI components
725021a feat(task-002-A): pipeline-trigger backend — migration + worker daemon
772961e test(sprint-1): Playwright visual-dna-v22 spec — 7/7 PASS on prod
358a75e feat(sprint-1): V22 Stratospheric Observatory design DNA recovery — foundation
```

Plus 5 commits prior (planning + audit) :
- `bf97ec5` epic + 16 task files via ccpm convention
- `154ce0c` D1-D4 decisions locked
- `c5a6e99` MEGA-PRD + 3-agent audit synthesis
- `aa70cf2` Wave D validation status
- `09d91f2` Supabase keys 2026 fix (login OK)

### Tests cumulative on prod
- `wave-a-2026-05-14.spec.ts` : 24/24 PASS
- `visual-dna-v22.spec.ts` : 7/7 PASS
- `runs-trigger.spec.ts` : 10/10 PASS
- **Total : 41/41 PASS** zero regression

### Supabase migration applied
- `20260514_0017_runs_extend.sql` applied via Dashboard SQL editor 2026-05-14 ✓
- New columns `runs.progress_pct` + `runs.error_message` live
- Extended `runs.type` enum (capture/score/recos/gsg/multi_judge/reality/geo)
- `idx_runs_pending_fifo` partial index for worker polling

### Live E2E smoke validated 2026-05-14T15:29Z
```
INSERT pending experiment run via REST
→ python3 -m growthcro.worker --once
→ atomic claim (pending→running)
→ subprocess.run(["python3", "-c", "print(...)"]) returncode=0 in 0.02s
→ PATCH status=completed + progress_pct=100 + metadata_json.duration ✓
```

## 2. Status epic webapp-stratospheric-reconstruction-2026-05

**2/16 tasks done (12.5%)**

| Task | Status | Closed |
|---|---|---|
| 001 design-dna-v22-stratospheric-recovery | ✅ closed | 2026-05-13 |
| 002 pipeline-trigger-backend Phase A | ✅ closed | 2026-05-14 |
| **003 client-lifecycle-from-ui** | 🟡 **NEXT** | — |
| 004 dashboard-v26-closed-loop-narrative | open | — |
| 005 growth-audit-v26-deep-detail | open | — |
| 006 reco-lifecycle-bbox-and-evidence | open | — |
| 007 scent-trail-pane-port | open | — |
| 008 experiments-v27-calculator | open | — |
| 009 geo-monitor-v31-pane | open | blocked Mathis-keys |
| 010 gsg-design-grammar-viewer-restore | open | — |
| 011 reality-layer-5-connectors-wiring | open | blocked Mathis-creds |
| 012 learning-doctrine-dogfood-restore | open | — |
| 013 global-chrome-cmdk-breadcrumbs | open | depends 001-012 |
| 014 essential-skills-install-and-wire | open | — |
| 015 legacy-cleanup-mega-prompt-archive | open | — |
| 016 microfrontends-decision-doc | open | — |

## 3. Sprint 3 — Task 003 client-lifecycle-from-ui (NEXT, 1-2 jours)

### Scope (`.claude/epics/webapp-stratospheric-reconstruction-2026-05/003.md`)

Wire le complete journey "partir de zéro → audit visible" depuis l'UI. Sans cette task, l'utilisateur ne peut PAS onboarder un nouveau client ni lancer un audit depuis la webapp (le worker Task 002 est wired backend mais l'UI ne le déclenche encore nulle part).

### Acceptance criteria (extrait)
- [ ] `POST /api/clients` route handler (admin gated) + `<AddClientModal>` modal
- [ ] Sidebar CTA "+ Add client" always visible (admin only)
- [ ] `audits.status` column migration (idle/capturing/scoring/enriching/done/failed)
- [ ] Surface `<TriggerRunButton type="capture">` per client/page sur :
  - Home `/` (QuickActionCard)
  - `/clients/[slug]` (per page_type)
  - `/audits/[c]/[a]` (re-run button)
- [ ] `<AuditStatusPill audit={...} />` rendu sur chaque audit (utilise existing RunStatusPill underneath)
- [ ] `<DeleteClientModal>` confirm dialog (admin)
- [ ] Playwright E2E : login → add client → run audit → see lifecycle pill update live

### Effort 1-2 jours (8-16h)

### Dépendances
- ✅ Task 002 (Worker daemon + Supabase runs queue + API routes + TriggerRunButton/RunStatusPill components)
- ❌ aucune autre

## 4. Mathis-side actions (parallel to Sprint 3)

| # | Action | Effort | Quand | Bloque sub-PRD |
|---|---|---|---|---|
| 1 | 🔴 Rotater Anthropic API key | 5 min | ASAP | none (security) |
| 2 | OPENAI_API_KEY + PERPLEXITY_API_KEY | 5 min | Avant Task 009 GEO | 009 |
| 3 | OAuth creds Reality 5 connectors (Catchr/Meta/GA/Shopify/Clarity) | 2-3h | Avant Task 011 Reality | 011 |
| 4 | Sprint 3 manual validation post-completion (~30min) | 30 min | Post-Task 003 | tier 1 close |
| 5 | Mathis runs worker daemon when triggering audits depuis UI : `python3 -m growthcro.worker` (Phase A : run local) | 0 min | À chaque session | uses Task 003 result |

## 5. Trigger phrase post-clear

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-15.md (ce fichier)
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md
3. .claude/epics/webapp-stratospheric-reconstruction-2026-05/003.md (task à lancer)

Lance Sprint 3 — task 003 client-lifecycle-from-ui :
- POST /api/clients route handler + AddClientModal
- audits.status column migration
- Surface <TriggerRunButton> sur Home + clients/[slug] + audits/[c]/[a]
- AuditStatusPill wrapping RunStatusPill
- Playwright E2E "login → add client → run audit → status pill live"

Effort 1-2 jours. Sprint 3 = closes TIER 1 (Foundations). Mathis-in-loop
validation manual après.
```

## 6. Architecture state (recap pour reprise)

### V22 design DNA ✅ active
- 4 fonts loaded via next/font (Cormorant, Playfair, Inter, JetBrains Mono)
- Alaska Boreal Night palette + Sunset Gold + Aurora + 4-layer body bg
- Spacing φ-ratio (--sp-0 to --sp-7)
- Glass cards + KPI gradient + score-color HSL utility
- StarfieldBackground canvas animated background
- Aura easings (cubic-bezier(0.23, 1, 0.32, 1))
- Backward-compat --gc-* aliases (cleanup task 015)

### Pipeline trigger backend ✅ active
- `growthcro/worker/` daemon : `python3 -m growthcro.worker --once`
- Supabase `runs` queue + 9-type enum + RLS + Realtime channel public:runs
- Next.js API : POST /api/runs (admin gated) + GET /api/runs[/<id>]
- UI components : `<TriggerRunButton type="..." metadata={...} />` + `<RunStatusPill runId={...} />`
- Defensive write to optional columns (pre-migration safe)

### What still doesn't work (intentional, in plan)
- ❌ "Add client" UI (Task 003 next)
- ❌ "Run audit" UI button surfaced on routes (Task 003)
- ❌ V26 dashboard narrative (Closed-Loop strip + 6 pillars chart + breakdowns) (Task 004)
- ❌ CRIT_NAMES_V21 FR labels in recos (Task 005)
- ❌ Bbox screenshot crops in RichRecoCard (Task 006)
- ❌ Scent Trail / Experiments / GEO panes (Tasks 007/008/009)
- ❌ /gsg Design Grammar viewer (currently wrong feature) (Task 010)
- ❌ Reality 5 connectors live (Task 011)
- ❌ Cmd+K palette (Task 013)

## 7. Files reference

- This continuation : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-15.md`](./CONTINUATION_PLAN_2026-05-15.md)
- Previous : [`CONTINUATION_PLAN_2026-05-14.md`](./CONTINUATION_PLAN_2026-05-14.md)
- Master PRD : [`.claude/prds/webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)
- Epic : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/epic.md)
- Decisions : [`.claude/docs/architecture/DECISIONS_2026-05-14.md`](../architecture/DECISIONS_2026-05-14.md)
- 3-agent audit reports : `.claude/docs/state/AUDIT_*_2026-05-14.md` + `WEBAPP_RECONSTRUCTION_PLAN_2026-05-14.md`
- Worker README : [`growthcro/worker/README.md`](../../../growthcro/worker/README.md)

---

**État final** : Sprint 1 + 2 closed. Migration live. Backend pipeline fully wired E2E. Task 003 next = surface UI buttons partout. ~1-2 jours pour clore TIER 1. **AU CARRÉ.**
