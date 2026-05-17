# Continuation Plan — 2026-05-14 (post-clear reprise, MÉTHODE AUDIT-FIRST)

> **⚠️ Document historique** — superseded par [`CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`](CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md). Conservé pour traçabilité du raisonnement (sprint historique). État canonique post-2026-05-17 vit dans le plan Renaissance + nouveau pivot webapp UX refonte ([PRD](../../prds/webapp-product-ux-reconstruction-2026-05.md) · [Epic](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md)).


> **Point d'entrée prochaine session Claude Code** post `/clear` context.
>
> User a clear le context après session 2026-05-13 marathon (13+ commits, 10 sub-PRDs Wave P0/P1/P2 + SP-11) AVEC FRUSTRATION ÉLÉGITIME : "y'a des erreurs de PARTOUT". Le plan a échoué méthodologiquement (velocity > validation).
>
> **Nouvelle méthode 2026-05-14 : AUDIT-FIRST avec ALL skills stratosphère + natives gratuits**. Reprise via ce document + master PRD `webapp-data-fidelity-and-skills-stratosphere-2026-05`.

## 1. État closing 2026-05-13

**Date close** : 2026-05-13T15:00Z
**main HEAD** : `<post commit MEGA PRD>` (à mettre à jour à commit time)
**Working tree** : clean
**origin/main** : synced

### Stats session 2026-05-13

| Catégorie | Stats |
|---|---|
| Commits | 14+ sur main |
| Sub-PRDs shipped | 10 Wave P0/P1/P2 + SP-11 |
| Routes webapp | 24 |
| Bundle First Load | 87.3 KB shared |
| Screenshots upload | 1840/1840 WebP, 866 MB ✓ |
| Skills research | 3 stratosphères + 2 natives identifiés |
| MEGA PRD AUDIT-FIRST | shipped ce commit |

### Honest verdict 2026-05-13 (mathis textuel)

> *"y'a des erreurs de PARTOUT, sur la donnée, les règles, les critères, les images, l'UI/UX de l'app elle même... c'est quoi ce bordel ?"*

**Cause root** : velocity > validation. 10 sub-PRDs shipped sans browser-load test. Migration data sur mauvais bundle (`growth_audit_data.js` V21 cluster pauvre au lieu de `recos_enriched.json` V13 riche). Skills audit jamais utilisés.

### Webapp Production State (live, 2026-05-13 evening)

- 🌐 https://growth-cro.vercel.app
- ✅ Build 24 routes, 87.3 KB shared, auth fonctionne
- ⚠️ Data PAUVRE en Supabase (migration mauvais source)
- ⚠️ Multiple bugs probable non-visibles (brand_dna NULL, judges NULL, funnel NULL, mobile pas testé, etc.)

### Gates état

```
lint_code_hygiene.py   : FAIL=1 (baseline)
typecheck.sh           : ✓
SCHEMA/validate_all    : ✓
audit_capabilities     : ✓ 0 orphans HIGH
parity_check weglot    : ✓
build                  : ✓ 24 routes
```

## 2. Credentials live (à protéger)

### Webapp Mathis
- **URL** : https://growth-cro.vercel.app/login
- **Email** : `tech@growth-society.com`
- **Password** : ⚠️ voir `.env.local`

### Supabase
- **Dashboard** : https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc
- **Project ref** : `xyazvwwjckhdmxnohadc`
- **Region** : Frankfurt (eu-central-1)
- 🔴 **service_role JWT** : URGENT À ROTATER (repo PUBLIC, JWT in git history)

### Vercel
- **Dashboard** : https://vercel.com/tech-4696s-projects/growth-cro
- **Project ID** : `prj_4l9eRL5kJjEkWQvnZI3BN2yVQXzB`
- **Team ID** : `team_iKbzzgWDkWzSObzviFNVmR4Q`

### Supabase Storage
- **Bucket** : `screenshots` (public read)
- **Path** : `<client>/<page>/<filename>.webp`
- **Files** : 1840 WebP uploaded ✓

## 3. PRDs actifs (priority order)

| PRD | Status | Priority |
|---|---|---|
| **`webapp-data-fidelity-and-skills-stratosphere-2026-05`** | 🟢 **ACTIVE master AUDIT-FIRST** | **P0 critical** |
| `webapp-v26-parity-and-beyond` | 🟡 superseded (Wave P0/P1/P2 shipped mais data fail) | reference |
| `skill-stratosphere-2026-05-integration` | 🟡 absorbed by MEGA PRD | reference |
| `post-stratosphere-roadmap` | 🔵 master continuation | reference |

## 4. Priorités prochaine session — MÉTHODE AUDIT-FIRST

### 🔴 PRE-ACTION CRITICAL (5 min, Mathis side)

**Rotater service_role JWT** :
1. https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc/settings/api → Reset
2. Update Vercel env var `SUPABASE_SERVICE_ROLE_KEY`
3. Update `.env.local` racine

### Wave 0 — PREP (~1.5h)

**Goal** : Install skills stratosphère + activate natives. Foundation pour audit.

1. **W0.1** JWT rotated (Mathis, done above)
2. **W0.2** Install `skill-based-architecture` :
   ```bash
   git clone https://github.com/WoJiSama/skill-based-architecture.git skills/skill-based-architecture
   ```
   Then invoke : *"Use skill-based-architecture to consolidate growth-cro project rules into skills/growthcro/"*
3. **W0.3** Install Superpowers + GStack :
   ```bash
   npx skills add obra/superpowers
   npx skills add https://github.com/garrytan/gstack
   ```
4. **W0.4** Vercel Agent enable : Dashboard → Agent → enable AI PR Review

### Wave A — AUDIT EXHAUSTIF (~3-4h)

**Goal** : Cross-validation 12 dimensions par 12 agents parallel. Pas de fix, juste DIAGNOSE.

12 audits run en parallel (batch 2-3 à la fois pour skill cap ≤ 8) :
- A.1 Native `/review` (9 subagents)
- A.2 Vercel Agent PR review
- A.3 `vercel:verification` (3 routes critiques)
- A.4 `webapp-testing` Playwright E2E (10+ tests)
- A.5 `design:design-critique` (5 routes)
- A.6 `design:accessibility-review` WCAG AA
- A.7 `vercel:react-best-practices` TSX audit
- A.8 `vercel:performance-optimizer` Lighthouse
- A.9 `GStack` AI team review
- A.10 Data fidelity audit (Supabase vs disk)
- A.11 Trail of Bits security (codeql + semgrep + variant + supply-chain)
- A.12 Mobile responsive (Playwright multi-breakpoint)

Each → `.claude/docs/state/AUDIT_<dimension>_2026-05-14.md`.

### Wave B — SYNTHESIS (~1h)

**Goal** : Master bug list canonical, severity ranked, effort estimated.

Output : `.claude/docs/state/MASTER_BUG_LIST_2026-05-14.md`

### Wave C — FIX EXECUTION (~8-12h, multi-session)

**Goal** : Sub-PRDs créés POST-audit, prioritized P0 → P3.

Per fix : Superpowers multi-step plan + TDD + commit isolé + gate-vert.

### Wave D — VALIDATION (~2h)

- /review re-run (0 P0 regression)
- Playwright E2E (10+ tests passing)
- Mathis manual validation (Wave D.3)
- Lighthouse > 90 sur 5 main routes

### Wave E — CLOSE (~1h)

- BLUEPRINT v1.3
- MANIFEST §12 changelog
- CONTINUATION_PLAN_2026-05-15

## 5. Trigger phrase post-clear

Tape EXACTEMENT ça dans Claude Code après `/clear` :

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-14.md
2. .claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md (MEGA PRD AUDIT-FIRST)
3. .claude/docs/state/SKILLS_DEEP_RESEARCH_2026-05-13.md

Lance Wave 0 PREP : install skill-based-architecture + Superpowers + GStack, enable Vercel Agent.
Puis Wave A AUDIT : 12 parallel audit reports.
```

## 6. Actions Mathis humaines

| # | Action | Effort | When | Urgency |
|---|---|---|---|---|
| 1 | 🔴 **Rotater service_role JWT** | 5 min | NOW | URGENT |
| 2 | Vercel Agent OAuth enable | 5 min | Wave 0 | P0 |
| 3 | Mathis manual validation Wave D | 1-2h | After Wave C | P0 |
| 4 | Consultant Growth Society feedback | 30 min | After Wave D (optional) | P1 |

## 7. Skills à utiliser (TOUS exploités)

| Skill | Wave | Output |
|---|---|---|
| skill-based-architecture | W0.2 | `skills/growthcro/` consolidé |
| Superpowers | W0.3 + Wave C | Multi-step plans + TDD |
| GStack | W0.3 + W A.9 | AI team personas review |
| Native /review | W A.1 + W D.1 | 9 subagents reports |
| Vercel Agent | W0.4 + W A.2 | Auto PR review + prod investigation |
| vercel:verification | W A.3 | Full-story 3 routes |
| webapp-testing (Playwright) | W A.4 + W D.2 | E2E suite |
| design:design-critique | W A.5 | UX critique 5 routes |
| design:accessibility-review | W A.6 | WCAG 2.1 AA |
| vercel:react-best-practices | W A.7 | 57 perf rules TSX |
| vercel:performance-optimizer | W A.8 | Lighthouse |
| Trail of Bits (codeql, semgrep, etc.) | W A.11 | Security HIGH/MEDIUM |
| data:explore-data + validate-data | W A.10 + W B.1 | Data profiling + QA |
| ccpm | All waves | Orchestration |
| product-management:* | Wave B + C | Sub-PRDs post-audit |

## 8. Commands quick-access

### Skills installs
```bash
git clone https://github.com/WoJiSama/skill-based-architecture.git skills/skill-based-architecture
npx skills add obra/superpowers
npx skills add https://github.com/garrytan/gstack
```

### Verify Supabase Storage
```bash
curl -I "https://xyazvwwjckhdmxnohadc.supabase.co/storage/v1/object/public/screenshots/japhy/collection/desktop_asis_fold.webp"
```

### Verify webapp redirect
```bash
curl -I "https://growth-cro.vercel.app/api/screenshots/japhy/collection/desktop_asis_fold.png"
```

### Login webapp
```bash
open https://growth-cro.vercel.app/login
# Email: tech@growth-society.com
# Password: voir .env.local (post-rotation)
```

### Git state
```bash
git log --oneline -10
git status
git worktree list
```

### Vercel
```bash
vercel ls growth-cro --prod | head -3
vercel env ls production | grep -i supabase
vercel logs --since 1h --query "level:error"
```

## 9. Notes méthodo (anti-velocity)

### Ce qu'on NE FAIT PLUS
- ❌ Velocity-mode 10 sub-PRDs/jour
- ❌ HTTP codes = "ça marche"
- ❌ Trust agents sans cross-check data
- ❌ Plan top-down features (Wave P0 = audit + Brand DNA + etc.)
- ❌ Sub-PRDs créés AVANT audit
- ❌ Skip Mathis-in-loop validation
- ❌ Skip Playwright E2E

### Ce qu'on FAIT MAINTENANT
- ✅ Audit-first avec 12 dimensions cross-validated
- ✅ Master bug list canonical avec severity
- ✅ Sub-PRDs créés POST-audit basés vrais bugs
- ✅ Per-fix : Superpowers TDD + commit isolé + gate-vert
- ✅ Validation : /review + Playwright + Mathis manual
- ✅ Test visuel obligatoire pré-merge
- ✅ Mathis dans la boucle obligatoire

## 10. Récap session 2026-05-13 (énorme journée mais résultat décevant)

**Énorme effort** :
- 14+ commits sur main
- 10 sub-PRDs Wave P0/P1/P2 shipped
- 1840 screenshots WebP uploaded
- Deep research skills 2026 done
- MEGA PRD AUDIT-FIRST shipped

**Résultat user-visible décevant** :
- Webapp encore "écran de fumée" — frustration légitime
- Bugs partout (data + UI + interactions probablement)

**Lesson learned** :
- Velocity ≠ valeur livrée
- Code généré ≠ feature fonctionnelle
- HTTP 200 ≠ UI works
- Test visuel mandatory pré-claim "shipped"

**Next session** : AUDIT-FIRST. Comprendre avant fixer. Avec tous les skills 2026.

---

**À demain. Reprise avec méthode rigoureuse cette fois. AU CARRÉ. 🎯**
