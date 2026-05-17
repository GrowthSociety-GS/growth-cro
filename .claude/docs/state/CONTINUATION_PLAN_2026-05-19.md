# Continuation Plan — 2026-05-19 (post Sprint 6+7 parallel-agent merge)

> **⚠️ Document historique** — superseded par [`CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`](CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md). Conservé pour traçabilité du raisonnement (sprint historique). État canonique post-2026-05-17 vit dans le plan Renaissance + nouveau pivot webapp UX refonte ([PRD](../../prds/webapp-product-ux-reconstruction-2026-05.md) · [Epic](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md)).


> Sprints 6 (Task 005) + 7 (Task 007) shippés en parallèle via deux agents
> isolated worktrees. Tier 2 closing strip + Tier 3 first surface live.
> 3 sprints pending Mathis manual validation (005, 006, 007) — quand validés,
> Tier 2 fermé et on attaque Tier 3 (008 / 010 / 012, ou Tier 4 polish).

## 1. État closing 2026-05-14 — Sprint 6+7 code-complete

### Commits poussés sur origin/main (10)

**Sprint 6 (Task 005) — branch worktree-agent-a2c26c2abd4e6c5bc merged via `git merge --no-ff`**
- `15158fb` foundation — CRIT_NAMES_V21 + viewport hook + P0 pulse CSS
- `4745fa4` V26 components — ClientHeroBlock + V26Panels + CanonicalTunnelTab
- `a03ac12` integration — viewport-aware screenshots + criteria labels + sticky tabs + P0 pulse
- `b5f4b34` Playwright contract spec
- `ff6725c` fix(spec) — drop cross-workspace dynamic TS import (Playwright loader limitation)

**Sprint 7 (Task 007) — branch worktree-agent-aa64f945a103ee522 merged via `git merge --no-ff`**
- `4dca965` foundation — supabase migration + scent_trail loader + scent-fs lib
- `563017c` 4 scent components — mono-concern panes
- `a0785db` /scent route + sidebar nav entry
- `20076ff` Playwright contract spec
- `1a041b8` fix(post-merge) — scent-types split + server-only guard (Vercel build was failing on `node:fs` leaking into client bundle)

### Vercel deploy

- Production deploy success `sha=1a041b8` sur https://growth-cro.vercel.app
- Initial deploy at `ff6725c` failed (webpack `UnhandledSchemeError: node:fs/promises` — see post-merge fix)
- Fix : extracted pure types/helpers into `webapp/apps/shell/lib/scent-types.ts` + added `import "server-only";` guard to `scent-fs.ts`

### Tests prod (cumulative regression)

- **152/152 PASS** (Sprint 1-7 spec coverage × 2 viewports)
- Sprint 6 new : 8/8 growth-audit-v26.spec.ts (route never-500 + /login mount, V22 next/font fingerprint)
- Sprint 7 new : 8/8 scent-trail.spec.ts (route never-500 + /login mount + anonymous never sees admin)
- **Zero régression** sur les 7 sprints

### Validation gates locales

- `npm run typecheck --workspace=apps/shell` ✓
- `npm run lint --workspace=apps/shell` ✓
- `npm run build --workspace=apps/shell` ✓ (run before pushing to confirm Vercel build success)
- `python3 scripts/lint_code_hygiene.py --staged` ✓

## 2. Migrations en attente (2)

```sql
-- Sprint 5 / Task 006 (pas encore appliquée)
-- supabase/migrations/20260514_0019_recos_lifecycle.sql
-- 13-state lifecycle enum on recos

-- Sprint 7 / Task 007 (pas encore appliquée)
-- supabase/migrations/20260514_0020_audits_scent_trail.sql
-- additive JSONB column audits.scent_trail_json
```

Les deux sont additives + idempotentes. Code marche déjà sans les migrations (defensive fallback : `lifecycle_status` default backlog, `scent_trail_json` reste null, UI gracefully degrade).

## 3. Status epic webapp-stratospheric-reconstruction-2026-05

**4/16 done + 3/16 code-complete-pending-validation (~44% effectif)**

| Task | Status | Notes |
|---|---|---|
| 001 design-dna-v22-stratospheric-recovery | ✅ closed | 2026-05-13 |
| 002 pipeline-trigger-backend Phase A | ✅ closed | 2026-05-14 |
| 003 client-lifecycle-from-ui | ✅ closed | 2026-05-14 |
| 004 dashboard-v26-closed-loop-narrative | ✅ closed | 2026-05-14 |
| 005 growth-audit-v26-deep-detail | 🟡 code-complete | parallel-agent worktree merged |
| 006 reco-lifecycle-bbox-and-evidence | 🟡 code-complete | awaiting migration apply + val |
| 007 scent-trail-pane-port | 🟡 code-complete | awaiting migration apply + val |
| 008 experiments-v27-calculator | open | parallel-safe |
| 009 geo-monitor-v31-pane | open | blocked Mathis-keys |
| 010 gsg-design-grammar-viewer-restore | open | depends 002 ✓ |
| 011 reality-layer-5-connectors-wiring | open | blocked Mathis-creds |
| 012 learning-doctrine-dogfood-restore | open | parallel-safe |
| 013 global-chrome-cmdk-breadcrumbs | open | depends 001-012 |
| 014 essential-skills-install-and-wire | open | parallel-safe |
| 015 legacy-cleanup-mega-prompt-archive | open | parallel-safe |
| 016 microfrontends-decision-doc | open | parallel-safe |

## 4. Mathis-in-loop validation matrix

Trois sprints attendent validation. Tu peux les batch-valider en une seule passe sur prod :

### Sprint 5 / Task 006 (reco-lifecycle, on `/audits/<c>/<a>`)
1. Apply migration `20260514_0019_recos_lifecycle.sql` (Dashboard SQL editor)
2. Login admin → ouvre n'importe quelle audit detail page
3. Vérifie sur chaque reco card : `LifecyclePill` visible · dropdown admin marche · 3 tabs Problème/Action/Pourquoi switchent · bbox crop apparaît quand data dispo · EvidencePill quand `evidence_ids` non-vide

### Sprint 6 / Task 005 (V26 deep-detail, on `/audits/<c>/<a>` + `/clients/<slug>`)
4. Sur `/audits/<c>/<a>` : `V26Panels` visible · `CanonicalTunnelTab` 🌊 visible si la data l'autorise (sinon silencieux) · viewport toggle 💻/📱 switche les screenshots + bbox crops · pulsing P0 dot rouge à côté des noms clients avec P0 > 0 · pills criterion_id affichent label FR ("Mobile-first (ux_05)")
5. Sur `/clients/<slug>` : `<ClientHeroBlock>` visible en haut · palette swatches + voice samples + typo
6. Sur `/audits/<clientSlug>` : sticky page-type tabs au scroll

### Sprint 7 / Task 007 (scent-trail, on `/scent`)
7. Apply migration `20260514_0020_audits_scent_trail.sql` (Dashboard SQL editor)
8. Sidebar Studio group → click "🔄 Scent Trail" → `/scent`
9. Empty-state visible (V26 disk a 0 scent_trail.json files) · KPI cards rendent à 0/0/-

## 5. Tier 3 next batch (post-validation)

| Task | Effort | Parallel | Dep |
|---|---|---|---|
| **008 experiments-v27-calculator** | 2j | oui | — |
| **012 learning-doctrine-dogfood-restore** | 2j | oui | 001 ✓ |
| **014 essential-skills-install-and-wire** | 1-2j | oui | — |
| **015 legacy-cleanup-mega-prompt-archive** | 1j | oui | — |

Recommandation : encore une **dispatch parallèle** (008 + 012) en agent-worktree mode, avec la lesson-learned appliquée : la validation gate doit inclure `npm run build` (pas juste `tsc`).

## 6. Prochaine session — trigger phrase

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-19.md
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md

Mathis a validé Sprints 5+6+7. On démarre Tier 3 en parallèle via agents
worktree-isolés :
- Task 008 experiments-v27-calculator (parallel-safe)
- Task 012 learning-doctrine-dogfood-restore (parallel-safe, depends 001 ✓)

⚠️ Important : agent validation gate doit inclure `npm run build`
(pas juste `tsc`) — leçon Sprint 6+7 sur le `node:fs` client-bundle leak.
```

## 7. Files reference

- This continuation : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-19.md`](./CONTINUATION_PLAN_2026-05-19.md)
- Previous : [`CONTINUATION_PLAN_2026-05-18.md`](./CONTINUATION_PLAN_2026-05-18.md)
- Sprint 6 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/005.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/005.md)
- Sprint 7 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/007.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/007.md)
- Master PRD : [`.claude/prds/webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)

---

**État final 2026-05-14** : Sprint 6+7 code complete + prod live. Trois
sprints pending Mathis validation (005 🟡 + 006 🟡 + 007 🟡). Tier 2 close-out
au bout d'un click. **AU CARRÉ ×7.**
