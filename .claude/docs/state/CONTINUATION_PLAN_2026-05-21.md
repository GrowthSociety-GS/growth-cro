# Continuation Plan — 2026-05-21 (post Sprint 10 parallel-agent merge v3)

> **⚠️ Document historique** — superseded par [`CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`](CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md). Conservé pour traçabilité du raisonnement (sprint historique). État canonique post-2026-05-17 vit dans le plan Renaissance + nouveau pivot webapp UX refonte ([PRD](../../prds/webapp-product-ux-reconstruction-2026-05.md) · [Epic](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md)).


> Sprints 10a (Task 010 gsg-design-grammar-viewer-restore) + 10b (Task 016
> microfrontends-decision-doc) shippés en parallèle. Server-only/pure split
> pattern fully internalised — zéro post-merge bundle fix. Reste 4 tasks
> open : 2 blockées par tes credentials externes (009 GEO, 011 Reality),
> 2 demandent ta main (014 skills install, 015 legacy `--gc-*` cleanup).

## 1. État closing 2026-05-15 — Sprint 10 code-complete

### Commits poussés sur origin/main (7 + docs close)

**Task 010 (Sprint 10a) — merged from worktree-agent-aed9dcfc515075dd4**
- `a041d97` design-grammar types + server-only fs reader
- `5505384` /api/design-grammar/[client]/[file] redirect+proxy route
- `5ea0cb0` Design Grammar viewer + Brief Wizard relocation to /handoff
- `5c13636` Playwright contract spec

**Task 016 (Sprint 10b) — merged from worktree-agent-abd14eb3e7ac0b73a**
- `3e7636b` decision doc + manifest §12
- `63587c3` architecture-explorer-data.js + utility script
- `9921714` PRODUCT_BOUNDARIES §3-bis + BLUEPRINT v1.4

### Vercel deploy

- Production deploy success sha=`2ff15fb` sur https://growth-cro.vercel.app
- Zero post-merge bundle fix this time (Sprint 7 lesson internalised)

### Tests prod (cumulative regression)

- **182/182 PASS** (Sprint 1-10 spec coverage × 2 viewports)
  - +14 nouveaux pour Sprint 10 (gsg-design-grammar contract)
- Zero régression sur les 10 sprints

### Validation gates (4 mandatory)

- `npm run typecheck --workspace=apps/shell` ✓
- `npm run lint --workspace=apps/shell` ✓
- `npm run build --workspace=apps/shell` ✓ (no `node:fs` client-bundle leak)
- `python3 scripts/lint_code_hygiene.py --staged` ✓

## 2. Status epic webapp-stratospheric-reconstruction-2026-05

**9/16 done + 2/16 code-complete-pending-validation (~69% effectif)**

| Task | Status | Notes |
|---|---|---|
| 001 design-dna-v22-stratospheric-recovery | ✅ closed | 2026-05-13 |
| 002 pipeline-trigger-backend Phase A | ✅ closed | 2026-05-14 |
| 003 client-lifecycle-from-ui | ✅ closed | 2026-05-14 |
| 004 dashboard-v26-closed-loop-narrative | ✅ closed | 2026-05-14 |
| 005 growth-audit-v26-deep-detail | ✅ closed | 2026-05-14 |
| 006 reco-lifecycle-bbox-and-evidence | ✅ closed | 2026-05-14 |
| 007 scent-trail-pane-port | ✅ closed | 2026-05-14 |
| 008 experiments-v27-calculator | ✅ closed | 2026-05-15 |
| 012 learning-doctrine-dogfood-restore | ✅ closed | 2026-05-15 |
| **010** gsg-design-grammar-viewer-restore | 🟡 code-complete | awaiting val |
| **016** microfrontends-decision-doc | 🟡 code-complete | awaiting sign-off |
| 009 geo-monitor-v31-pane | open | **blocked Mathis-keys** |
| 011 reality-layer-5-connectors-wiring | open | **blocked Mathis-creds** |
| 013 global-chrome-cmdk-breadcrumbs | open | depends 001-012 (after 014+015) |
| 014 essential-skills-install-and-wire | open | **Mathis-side** (perms + URLs) |
| 015 legacy-cleanup-mega-prompt-archive | open | **Mathis-side** (high blast radius) |

## 3. Mathis-in-loop validation Sprint 10

### Task 010 (`/gsg` + `/gsg/handoff`)
1. Aller sur https://growth-cro.vercel.app/gsg
2. Vérifier : Design Grammar viewer avec sidebar client selector · 7-artefact grid si data dispo (la plupart des clients dev n'auront pas tous les fichiers) · TokensCssPreview iframe sandboxed · ForbiddenPatternsAlert
3. Aller sur `/gsg/handoff`
4. Vérifier : BriefWizard accessible · click submit → `<TriggerRunButton type="gsg">` déclenche un run via Task 002 backend · GsgRunPreview subscribe Realtime

### Task 016 (docs + architecture-explorer)
5. `open deliverables/architecture-explorer.html` — vérifie qu'il rend toujours et que la mermaid view 5 ne montre plus 6 µfrontends mais 1 shell
6. Lire `.claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md` (126 lignes) — sign-off sur les Triggers A/B de re-introduction
7. Vérifier `PRODUCT_BOUNDARIES_V26AH.md §3-bis` cross-référence DECISIONS

## 4. Pending Mathis-side work (non-agent)

### Task 014 — essential-skills-install-and-wire
Demande ta main parce que :
- 4 skills à installer : `vercel-microfrontends` (mais Sprint 10b a déjà DROPPED celui-ci, donc plus que 3 : `cro-methodology`, `Emil Kowalski Design Skill`, `Impeccable`)
- Source URLs spéculatives dans le spec — il faut chercher manuellement sur GitHub (`emilkowalski/skills` ?, `obra/impeccable` ?)
- `npx skills add <source>` demande perms locales + auto-classifier bypass
- Validation per-skill demande invocations test manuelles

Procédure suggérée :
```bash
# Pour chaque skill, après URL trouvée :
npx skills add <github-url>
# Vérifier que le skill apparaît dans :
npx skills list --project
# Wire dans SKILLS_INTEGRATION_BLUEPRINT.md v1.5
```

### Task 015 — legacy-cleanup-mega-prompt-archive
Demande ta main parce que :
- Inventaire `--gc-*` palette aliases : grep extensif requis (j'ai vu `var(--gc-muted)`, `var(--gc-cyan)`, `var(--gc-line)`, `var(--gc-panel)`, etc. dans ~30 composants)
- Archive de 18 modules legacy via `git mv` — vérification que NULLE active code path n'importe les modules avant archive (la doctrine V3.2.1 dit `parity_check.sh weglot` zero deltas requis)
- Cleanup des aliases dans `packages/ui/src/styles.css` ne peut se faire qu'AVEC un remplacement coordonné de tous les call-sites — bombe potentielle de régression visuelle

Procédure suggérée :
```bash
# 1. Inventaire
grep -rn "growthcro.gsg_lp\|growth-site-generator\|pipeline_sequential\|brief_v15_builder" --include="*.py" .
# 2. Archive avec git mv (preserve history)
git mv growthcro/gsg_lp _archive/2026-05-15_mega_prompt_path/gsg_lp
# 3. Audit capabilities (DECREASE expected)
python3 scripts/audit_capabilities.py
# 4. Parity check (zero deltas requis)
bash scripts/parity_check.sh weglot
```

### Tasks 009 + 011 (toujours bloquées)
- **009 GEO** : besoin `OPENAI_API_KEY` + `PERPLEXITY_API_KEY` dans `.env.local`
- **011 Reality** : besoin OAuth creds 5 connectors (Catchr / Meta / GA / Shopify / Clarity), ~2-3h de config Mathis

## 5. Prochaine session — trigger phrase

### Option A — Tier 3 close après Mathis valide 010 + 016

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-21.md
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md

Mathis a validé Sprints 10a + 10b. On attaque ce qui reste :
- Tasks 014 + 015 = Mathis-side (perms + blast radius), pas agent dispatch
- Tasks 009 + 011 = bloquées sur credentials externes
- Task 013 cmd+K palette dépend de 014/015 → ne démarre pas avant

Bouclage epic possible après 014 + 015 + 013, OU on déclare l'epic Tier 4
out-of-scope et on clôt à 11/16 (~69%) + on ouvre un nouveau PRD pour le
reste.
```

### Option B — Démarrer un nouveau PRD pendant la pause

Si Mathis veut prendre une pause sur le webapp-stratospheric-reconstruction et attaquer autre chose (e.g. les autres modules dans la vision GrowthCRO : GSG génération créative, Reality Layer Phase B, etc.), c'est le bon moment.

## 6. Files reference

- This continuation : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-21.md`](./CONTINUATION_PLAN_2026-05-21.md)
- Previous : [`CONTINUATION_PLAN_2026-05-20.md`](./CONTINUATION_PLAN_2026-05-20.md)
- Sprint 10a task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/010.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/010.md)
- Sprint 10b task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/016.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/016.md)
- Decision doc D1.A : [`.claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md`](../architecture/MICROFRONTENDS_DECISION_2026-05-14.md)
- Architecture utility : [`scripts/update_architecture_explorer.py`](../../../scripts/update_architecture_explorer.py)

---

**État final 2026-05-15** : Sprint 10 code complete + prod live. 182/182
PASS regression. Validation-gate doctrine confirmée à nouveau — zéro
post-merge bundle fix sur Sprint 8/9/10. **AU CARRÉ ×10.**
