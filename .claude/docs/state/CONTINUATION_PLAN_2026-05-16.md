# Continuation Plan — 2026-05-16 (post Sprint 3 code complete)

> **Point d'entrée prochaine session Claude Code** post-clear.
>
> Mathis : la code de Sprint 3 (Task 003 client-lifecycle-from-ui) est shipped
> en local. Avant Tier 2, deux gates manuelles attendent :
> 1. Appliquer la migration `20260514_0018_audits_status.sql` via le SQL editor
>    Supabase (Dashboard → SQL editor → paste contents → Run).
> 2. Smoke E2E sur l'environnement Vercel : connecter en admin → sidebar
>    "+ Ajouter un client" → créer un slug test → atterrir sur `/clients/<slug>`
>    → `+ Nouvel audit` → status pill walks live (avec worker daemon up).

## 1. État closing 2026-05-14 — Sprint 3 code-complete

### Nouvelles surfaces UI (déployable une fois la migration appliquée)

- **Sidebar** : CTA "+ Ajouter un client" toujours visible pour les admins
- **`/` Home** : `QuickActionCard` "Lancer un audit" — AddClient + CreateAudit
- **`/clients/[slug]`** : bouton admin `↻ Capture homepage` (trigger run capture
  pour la homepage du client, RunStatusPill live)
- **`/audits/[c]/[a]`** : `<AuditStatusPill />` next to score Pill +
  `↻ Re-run capture` admin button (relance pipeline pour cette page exacte)

### Migration en attente

```sql
-- Apply via Supabase Dashboard SQL editor (same procedure as Sprint 2) :
-- supabase/migrations/20260514_0018_audits_status.sql
do $$ begin
  if not exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='audits' and column_name='status'
  ) then
    alter table public.audits
      add column status text not null default 'idle'
      check (status in ('idle','capturing','scoring','enriching','done','failed'));
    update public.audits set status = 'done' where status = 'idle';
  end if;
end $$;
create index if not exists idx_audits_status on public.audits(status);
```

### Validation gates locales (toutes vertes 2026-05-14)

- `npm run typecheck --workspace=apps/shell` → **PASS** (data has pre-existing rootDir warning unrelated)
- `npm run lint --workspace=apps/shell` → **PASS** (`No ESLint warnings or errors`)
- `python3 scripts/lint_code_hygiene.py --staged` → **PASS** (0 issues)

### Tests Playwright

- `client-lifecycle.spec.ts` ajouté — 8 cas contract (validation + DOM mount)
- À tourner contre prod post-deploy : `PLAYWRIGHT_BASE_URL=https://<prod>.vercel.app npx playwright test`

## 2. Status epic webapp-stratospheric-reconstruction-2026-05

**2/16 done + 1/16 code-complete-pending-validation (18.75%)**

| Task | Status | Closed |
|---|---|---|
| 001 design-dna-v22-stratospheric-recovery | ✅ closed | 2026-05-13 |
| 002 pipeline-trigger-backend Phase A | ✅ closed | 2026-05-14 |
| 003 client-lifecycle-from-ui | 🟡 code-complete | awaiting validation |
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

## 3. Tier 1 gate avant Tier 2

Per AD-6 (mathis-in-loop validation par tier), Tier 2 ne démarre pas avant
que Mathis confirme :
- [ ] Migration `20260514_0018_audits_status.sql` appliquée prod
- [ ] PR Sprint 3 mergée (à créer)
- [ ] Vercel deploy succès
- [ ] Smoke E2E manuel : add client → run audit → status pill walks live
- [ ] "OK pour Tier 2"

## 4. Mathis-side actions

| # | Action | Effort | Quand |
|---|---|---|---|
| 1 | Apply migration `20260514_0018_audits_status.sql` | 2 min | ASAP |
| 2 | Review + merge Sprint 3 commit(s) | 10 min | Post-migration |
| 3 | Worker daemon up local (`python3 -m growthcro.worker`) | 0 min | À chaque session |
| 4 | Smoke E2E manuel sur prod Vercel | 5 min | Post-deploy |
| 5 | (encore en attente) Rotater Anthropic API key | 5 min | ASAP (security) |
| 6 | OPENAI_API_KEY + PERPLEXITY_API_KEY | 5 min | Avant Task 009 |
| 7 | OAuth creds Reality 5 connectors | 2-3h | Avant Task 011 |

## 5. Prochaine session — trigger phrase

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-16.md
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md
3. .claude/epics/webapp-stratospheric-reconstruction-2026-05/004.md (Tier 2 start)

Mathis a validé Sprint 3. On démarre Tier 2 :
- Task 004 dashboard-v26-closed-loop-narrative (parallel-safe, depends 001 ✓)
- Closed-Loop strip + 6 pillars chart + priority dist + tabs
- Mathis-in-loop validation après Tier 2 complet (004 + 005 + 006).
```

## 6. Files reference

- This continuation : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-16.md`](./CONTINUATION_PLAN_2026-05-16.md)
- Previous : [`CONTINUATION_PLAN_2026-05-15.md`](./CONTINUATION_PLAN_2026-05-15.md)
- Sprint 3 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/003.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/003.md)
- Master PRD : [`.claude/prds/webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)
- Decisions : [`.claude/docs/architecture/DECISIONS_2026-05-14.md`](../architecture/DECISIONS_2026-05-14.md)
- Worker README : [`growthcro/worker/README.md`](../../../growthcro/worker/README.md)
- Migration : [`supabase/migrations/20260514_0018_audits_status.sql`](../../../supabase/migrations/20260514_0018_audits_status.sql)

---

**État final 2026-05-14** : Sprint 3 code complete. Migration en attente
d'apply. PR à ouvrir. Tier 1 verrou levé dès validation Mathis. **AU CARRÉ.**
