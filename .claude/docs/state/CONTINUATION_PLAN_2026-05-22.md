# Continuation Plan — 2026-05-22 (Epic webapp-stratospheric-reconstruction-2026-05 closeout)

> **⚠️ Document historique** — superseded par [`CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`](CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md). Conservé pour traçabilité du raisonnement (sprint historique). État canonique post-2026-05-17 vit dans le plan Renaissance + nouveau pivot webapp UX refonte ([PRD](../../prds/webapp-product-ux-reconstruction-2026-05.md) · [Epic](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md)).


> **EPIC CLOSEOUT STATE** — 12/16 tasks landed (75% validated + Sprint 11 013 awaiting Mathis val + 015 no-op confirmed). 3 remaining slots (014 + 009 + 011) deferred to a follow-up PRD pending Mathis-side credentials + perms. 4 parallel-agent dispatch batches v1-v4 delivered the V26 parity restoration in 2 days wall-clock.

## 1. État closing 2026-05-15 — Sprint 11 closeout

### Commits poussés sur origin/main (3 + 1 close commit ahead)

**Task 013 (Sprint 11) — merged from worktree-agent-a9e52364e647af483**
- `0e17cd9` foundation : cmdk-items registry + use-keyboard-shortcuts hook + V22 chrome CSS
- `5cfd70a` chrome components (StickyHeader + CmdKPalette + DynamicBreadcrumbs + SidebarNavBadge) + Sidebar refactor + Breadcrumbs shim
- `f02f393` wire StickyHeader + sidebar badges into / + global-chrome.spec.ts

**Task 015 (Sprint 11) — NO-OP confirmed** (worktree auto-cleaned, 0 commits)

### Vercel deploy

- Production deploy success `sha=f78b439` sur https://growth-cro.vercel.app

### Tests prod (cumulative regression)

- **190/190 PASS** (Sprint 1-11 spec coverage × 2 viewports)
  - +8 nouveaux pour Sprint 11 (global-chrome contract spec)
- Zero régression sur les 11 sprints

### Validation gates (4 mandatory per parallel-agent doctrine)

- `npm run typecheck --workspace=apps/shell` ✓
- `npm run lint --workspace=apps/shell` ✓
- `npm run build --workspace=apps/shell` ✓ (27/27 pages)
- `python3 scripts/lint_code_hygiene.py --staged` ✓

## 2. Status epic — closeout

**12/16 tasks landed (~75% validated)** + **1 code-complete pending Mathis val (013)** + **3 out-of-scope deferred (014 + 009 + 011)**

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
| 010 gsg-design-grammar-viewer-restore | ✅ closed | 2026-05-15 |
| 012 learning-doctrine-dogfood-restore | ✅ closed | 2026-05-15 |
| 016 microfrontends-decision-doc | ✅ closed | 2026-05-15 |
| **013** global-chrome-cmdk-breadcrumbs | 🟡 code-complete | awaiting Mathis val |
| **015** legacy-cleanup-mega-prompt-archive | ✅ closed (no-op) | already shipped in prior commits |
| 014 essential-skills-install-and-wire | open | **Mathis-side** (npx perms + URL research) |
| 009 geo-monitor-v31-pane | open | **blocked Mathis-keys** (OPENAI + PERPLEXITY) |
| 011 reality-layer-5-connectors-wiring | open | **blocked Mathis-creds** (5 OAuth) |

## 3. Mathis validation Sprint 11

### Task 013 (global chrome)
1. Aller sur https://growth-cro.vercel.app — login admin
2. Hit Cmd+K (Mac) ou Ctrl+K — vérifier que le palette s'ouvre
3. Tape "client" — la filtre fuzzy doit afficher les nav items + actions
4. Click un item nav → navigation OK
5. Click "+ Add client" → AddClientModal s'ouvre (admin gate marche)
6. ESC → palette ferme, focus revient au trigger
7. Hit `/` (slash) — focus va sur search bar dans StickyHeader
8. Naviguer entre routes (`/clients/<slug>`, `/audits/<c>/<a>`, etc.) — breadcrumbs renderent correctement (segment FR labels + UUID truncation)
9. Sidebar : vérifier badges (Clients 51 / Audits / P0 recos gold) + GEO entry greyed avec `title="Task 009 — coming soon"` + active route gold accent
10. Recent items section (localStorage `gc-cmdk-recent`) — visite 3 routes différentes, réouvre Cmd+K → "Recent" section les liste

## 4. Mathis-side work — follow-up PRD candidate

Si tu veux fermer le reste, voici la procédure suggérée. Sinon, on déclare l'epic done à 13/16 (~81%) et on ouvre un nouveau PRD `webapp-followup-skills-credentials-cleanup-2026-06` quand tu auras les credentials/perms.

### Task 014 — essential-skills-install-and-wire (~2-3h)

```bash
# 1. Find canonical sources (search GitHub):
#    cro-methodology         — likely obra/skills or Mathis custom
#    Emil Kowalski Design    — emilkowalski/skills ?
#    Impeccable              — obra/impeccable ?
# (vercel-microfrontends already DROPPED per Sprint 10b decision)

# 2. Install:
npx skills add <github-url>           # × 3 skills

# 3. Verify:
npx skills list --project             # should show 8/8 essentials

# 4. Wire combo packs in SKILLS_INTEGRATION_BLUEPRINT.md v1.5:
#    audit_run combo : add cro-methodology POST-PROCESS
#    gsg_generation combo : add Impeccable polish
#    webapp_nextjs combo : add Emil Kowalski Design motion

# 5. Validate per-skill: invoke each with a small test fixture
```

### Task 009 — geo-monitor-v31-pane (~30 min once keys provisioned)

```bash
# 1. Drop in webapp/.env.local AND root .env.local:
echo "OPENAI_API_KEY=sk-..." >> .env.local
echo "PERPLEXITY_API_KEY=pplx-..." >> .env.local

# 2. Re-deploy webapp (vercel env add NEXT_PUBLIC_ + add server-side keys)
# 3. Open a follow-up PRD or reopen this epic ; the actual /geo route + GEOMonitorPanel code work is a fresh ~2-day sprint
```

### Task 011 — reality-layer-5-connectors-wiring (~3-4h once OAuth provisioned)

Same shape — Catchr / Meta Ads / Google Analytics / Shopify / Microsoft Clarity OAuth flows + token refresh + per-client credential storage.

### `--gc-*` palette alias cleanup (sub-part of 015, ~3-4h manual)

```bash
# 1. Inventory:
grep -rn "var(--gc-" webapp/apps/shell/components/ webapp/apps/shell/app/ | wc -l
# (expect ~30+ call sites across Sprint 1-10 surfaces)

# 2. For each --gc-* alias, find the canonical V22 token replacement in packages/ui/src/styles.css:
#    --gc-muted     → var(--star-dim) or similar
#    --gc-cyan      → var(--aurora-cyan)
#    --gc-line      → var(--night-glow)
#    --gc-panel     → var(--night-elev)
#    --gc-gold      → var(--gold-sunset)
#    etc.

# 3. Replace per-component with visual regression check
# 4. Remove aliases from packages/ui/src/styles.css
# 5. Playwright visual snapshot diff
```

## 5. Décision epic closeout

L'epic peut être déclaré **fermé à 13/16 ≡ ~81%** (Mathis valide 013 → flip à closed) avec les 3 tasks restantes officiellement out-of-scope, OU **reouvert** à 16/16 si tu prends les ~6-10h Mathis-side avant.

Recommandation : **fermer à 13/16**, ouvrir un PRD followup `webapp-followup-skills-credentials-cleanup-2026-06` qui regroupe :
- 014 (skills install)
- 009 (GEO)
- 011 (Reality)
- `--gc-*` alias cleanup
- `growth-site-generator/*` real port to `moteur_multi_judge/judges/`

Permet d'attaquer une autre brique GrowthCRO (GSG génération créative final, Reality Layer Phase B, ou la doctrine V3.3 review des 69 proposals en attente) sans rester bloqué sur ces 3 tasks externes.

## 6. Prochaine session — trigger phrase

### Option A — Mathis valide 013 et on ferme l'epic

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-22.md
2. .claude/epics/webapp-stratospheric-reconstruction-2026-05/epic.md

Mathis a validé Sprint 11 (Task 013). On ferme l'epic
webapp-stratospheric-reconstruction-2026-05 à 13/16 (~81%) avec les
3 tasks restantes (014 + 009 + 011) tracked dans un nouveau PRD
webapp-followup-skills-credentials-cleanup-2026-06.

Action immédiate : flip epic status `in-progress → closed`, manifest §12
ajouter entrée closeout, et créer le squelette du PRD followup.
```

### Option B — Démarrer une autre brique

```
Lis CLAUDE.md init steps. Puis évalue la roadmap GrowthCRO V26.AI :
- GSG génération créative final (assets/motion premium par page type)
- Doctrine V3.3 review (69 proposals en attente)
- Reality Layer Phase B (orchestrator dry-run OK, missing env vars Catchr/Meta/GA/Shopify/Clarity)
- GEO Monitor (manque OPENAI + PERPLEXITY keys)
- Brand DNA + Design Grammar V29/V30 finalization (51/56 fleet)
- Multi-judge V26.D comme contrôle systématique post-run

Mathis choisit la prochaine brique. webapp-stratospheric-reconstruction-2026-05
est fermable à 13/16 dès que Mathis valide Sprint 11 Task 013.
```

## 7. Files reference

- This continuation : [`.claude/docs/state/CONTINUATION_PLAN_2026-05-22.md`](./CONTINUATION_PLAN_2026-05-22.md)
- Previous : [`CONTINUATION_PLAN_2026-05-21.md`](./CONTINUATION_PLAN_2026-05-21.md)
- Sprint 11 task : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/013.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/013.md)
- Sprint 11 no-op : [`.claude/epics/webapp-stratospheric-reconstruction-2026-05/015.md`](../../epics/webapp-stratospheric-reconstruction-2026-05/015.md)
- Master PRD : [`.claude/prds/webapp-stratospheric-reconstruction-2026-05.md`](../../prds/webapp-stratospheric-reconstruction-2026-05.md)

---

**État final 2026-05-15** : Sprint 11 closeout. 12/16 done + 1 pending Mathis val (013). 190/190 PASS regression prod. V26 parity restoration shippée en 2 jours wall-clock via 4 batches parallel-agent dispatch. **AU CARRÉ ×11.**
