# Continuation Plan — 2026-05-18 (post Sprint 5 code complete)

> Sprint 5 (Task 006 reco-lifecycle-bbox-and-evidence) shippé end-to-end.
> Tier 2 batch (006 → 005 sequential, 007 parallel-safe) maintenant débloqué
> dès que Mathis valide visuellement les recos enrichies sur prod.

## 1. État closing 2026-05-14 — Sprint 5 code-complete

### Commits poussés sur origin/main (4 + docs)

- `862cb17` feat(task-006-A): foundation — migration + 13-state enum + bbox extraction
- B-hash feat(task-006-B): API + 5 NEW components (LifecyclePill / EvidencePill / EvidenceModal / RecoBboxCrop / RecoSynthesisTabs)
- `84cd681` feat(task-006-C): RichRecoCard integration + callsites
- `694f027` test(task-006-D): Playwright reco-lifecycle contract — 7 cases

### Vercel deploy

- Production deploy success sha=`694f027` sur https://growth-cro.vercel.app

### Tests prod (regression suite cumulative)

- **138/138 PASS** (Sprint 1 + 2 + 3 + 4 + 5 spec coverage × 2 viewports)
  - 24 wave-a-2026-05-14
  - 7 visual-dna-v22
  - 10 runs-trigger
  - 16 client-lifecycle
  - 8 dashboard-v26
  - 14 reco-lifecycle (Sprint 5)
  - 59 ancillary (auth / nav / realtime / client-detail)
- **Zero régression** sur les 5 sprints.

### Validation gates locales

- `npm run typecheck --workspace=apps/shell` ✓
- `npm run lint --workspace=apps/shell` ✓
- `python3 scripts/lint_code_hygiene.py --staged` ✓

## 2. Migration en attente

```sql
-- Apply via Supabase Dashboard SQL editor (procedure identique aux Sprint 2/3) :
-- supabase/migrations/20260514_0019_recos_lifecycle.sql
do $$ begin
  if not exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='recos' and column_name='lifecycle_status'
  ) then
    alter table public.recos
      add column lifecycle_status text not null default 'backlog'
      check (lifecycle_status in (
        'backlog','prioritized','scoped','designing','implementing','qa',
        'staged','ab_running','ab_inconclusive','ab_negative','ab_positive',
        'shipped','learned'
      ));
    update public.recos set lifecycle_status = 'backlog' where lifecycle_status is null;
  end if;
end $$;
create index if not exists idx_recos_lifecycle_active
  on public.recos(lifecycle_status) where lifecycle_status <> 'backlog';
```

Le code est defensive : marche déjà sans migration (lifecycle pill default `backlog`, dropdown admin tentera PATCH et reverra l'erreur du DB).

## 3. Status epic webapp-stratospheric-reconstruction-2026-05

**4/16 done + 1/16 code-complete-pending-validation (~31% effectif)**

| Task | Status | Closed |
|---|---|---|
| 001 design-dna-v22-stratospheric-recovery | ✅ closed | 2026-05-13 |
| 002 pipeline-trigger-backend Phase A | ✅ closed | 2026-05-14 |
| 003 client-lifecycle-from-ui | ✅ closed | 2026-05-14 |
| 004 dashboard-v26-closed-loop-narrative | ✅ closed | 2026-05-14 |
| 006 reco-lifecycle-bbox-and-evidence | 🟡 code-complete | awaiting Mathis val |
| 005 growth-audit-v26-deep-detail | open | unblocked (depends 001 ✓ + 006 🟡) |
| 007 scent-trail-pane-port | open | parallel-safe |
| 008 experiments-v27-calculator | open | parallel-safe |
| 009 geo-monitor-v31-pane | open | blocked Mathis-keys |
| 010 gsg-design-grammar-viewer-restore | open | depends 002 ✓ |
| 011 reality-layer-5-connectors-wiring | open | blocked Mathis-creds |
| 012 learning-doctrine-dogfood-restore | open | parallel-safe |
| 013 global-chrome-cmdk-breadcrumbs | open | depends 001-012 |
| 014 essential-skills-install-and-wire | open | parallel-safe |
| 015 legacy-cleanup-mega-prompt-archive | open | parallel-safe |
| 016 microfrontends-decision-doc | open | parallel-safe |

## 4. Mathis-in-loop validation Sprint 5

Aller sur https://growth-cro.vercel.app, login admin, naviguer vers `/audits/<un-client>/<un-audit>` (n'importe quel client avec des recos) :

1. **🆕 LifecyclePill** — visible dans le header de chaque reco card, à côté du priority/severity/pillar/criterion_id. Affiche `backlog` par défaut (V22 soft tone). En vue admin (Mathis), un petit `<select>` apparaît à côté qui permet de choisir entre les 13 états.
2. **🆕 Click sur dropdown lifecycle** (admin) → PATCH `/api/recos/[id]/lifecycle` → pill change de couleur live. Si la migration n'est pas appliquée, le PATCH va échouer et la pill rollback au précédent état + affiche l'erreur en rouge.
3. **🆕 Détails → 3 tabs Problème / Action / Pourquoi** — click "Détails ↓" sur une reco, la body s'ouvre. Au lieu d'un seul long paragraphe, 3 onglets en pill style stratosphérique (cyan gradient sur l'actif). Tab "Problème" = before. Tab "Action" = after. Tab "Pourquoi" = why ou reco_text.
4. **🆕 Bbox crop** — si la reco a des coordonnées bbox dans `content_json.perception.bbox`, un screenshot canvas avec un rectangle rouge `#e87555` apparaît au-dessus des tabs. Click → ouvre la full-res. **La plupart des recos n'auront PAS de bbox** car le scorer ne le produit pas systématiquement — c'est attendu, gracefully `null`.
5. **🆕 EvidencePill** — pill cyan "📜 N evidences" dans la meta footer (à côté du lift/effort), apparaît uniquement quand `evidence_ids` est non vide. Click → modal qui liste les IDs raw. **La plupart des recos n'auront PAS d'evidence** non plus.
6. **🆕 Debug footer** — affiche la bbox tuple si présente (sous "bbox").

## 5. Tier 2 next batch

Vu que 006 est code-complete et débloque 005 :

| Task | Effort | Parallel | Recommandation |
|---|---|---|---|
| **005 growth-audit-v26-deep-detail** | 3-4j | non | démarrer après que Mathis valide 006 |
| **007 scent-trail-pane-port** | 2j | oui | **commencer maintenant**, indépendant |
| **008 experiments-v27-calculator** | 2j | oui | indépendant, P1 |

Recommandation : enchaîner sur **007** (scent-trail-pane-port) tant que Mathis valide 006 en parallèle. 007 est totalement orthogonal à 006 (nouvelle route `/scent`, nouveau pane fleet, aucune surface partagée).

Alternative : si Mathis veut serrer le close-out de Tier 2 d'abord, attendre validation 006 puis démarrer 005 (depends 001+006).

## 6. Prochaine session — trigger phrase

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-18.md
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md
3. .claude/epics/webapp-stratospheric-reconstruction-2026-05/007.md (Tier 3 parallel-safe)

Mathis a validé Sprint 5. On démarre Tier 3 en parallèle :
- Task 007 scent-trail-pane-port (parallel-safe, no dep)
- nouvelle route /scent + 4 NEW components + Supabase migration audits.scent_trail_json
- migrate_disk_to_supabase.py extension load_scent_trail()
- Playwright + Mathis-in-loop validation après
```

## 7. Files reference

- This continuation : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-18.md`](./CONTINUATION_PLAN_2026-05-18.md)
- Previous : [`CONTINUATION_PLAN_2026-05-17.md`](./CONTINUATION_PLAN_2026-05-17.md)
- Sprint 5 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/006.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/006.md)
- Master PRD : [`.claude/prds/webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)
- Migration : [`supabase/migrations/20260514_0019_recos_lifecycle.sql`](../../../supabase/migrations/20260514_0019_recos_lifecycle.sql)

---

**État final 2026-05-14** : Sprint 5 code complete + prod live. 138/138 PASS
regression. Tier 2 batch (006 🟡, 005 unblocked, 007 parallel-safe) attendent
validation. **AU CARRÉ ×5.**
