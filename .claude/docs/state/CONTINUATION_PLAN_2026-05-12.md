# Continuation Plan — 2026-05-12 (Session Close)

> **⚠️ Document historique** — superseded par [`CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`](CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md). Conservé pour traçabilité du raisonnement (sprint historique). État canonique post-2026-05-17 vit dans le plan Renaissance + nouveau pivot webapp UX refonte ([PRD](../../prds/webapp-product-ux-reconstruction-2026-05.md) · [Epic](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md)).


> **Point d'entrée prochaine session Claude Code.** Lis ce document + le PRD master [`post-stratosphere-roadmap.md`](../../prds/post-stratosphere-roadmap.md) avant de toucher au code.
>
> Une fois lu, tu sais : (1) où on en est exactement, (2) quelles actions humaines Mathis sont pendantes, (3) quelle Wave d'epics est activable, (4) quel sub-PRD créer.

## 1. État de cette session (closing snapshot)

**Date close** : 2026-05-12T08:36Z
**main HEAD** : `d1cba58` (Merge epic/hardening-and-skills-uplift: T28 Observability Migration landed 100%)
**Worktrees actifs** : `growth-cro/` (main) seul · ccpm/ source-of-skill séparé
**Branches preserved** : `epic/codebase-cleanup` · `epic/webapp-stratosphere` · `epic/hardening-and-skills-uplift` · 23 task branches mergées (history pour ref)

### Programmes livrés

| Programme | Tasks | Status | Highlights |
|---|---|---|---|
| **`codebase-cleanup`** | 11/11 | ✅ 100% (2026-05-10) | Layered `growthcro/` package · 0 orphans · doctrine code + linter |
| **`webapp-stratosphere`** | 8/8 | ✅ 100% (2026-05-11) | Architecture map 251 modules · doctrine V3.3 CRE · GSG V27.2-G · webapp V27+V28 · agency products · reality loop V30 |
| **`hardening-and-skills-uplift`** | 4/4 | ✅ 100% (2026-05-12) | bandit HIGH=0 · 4 skills S1 installés · 4 MCPs prod procedures · observability foundation |

### Gates main (final)

```
lint_code_hygiene.py   : FAIL=1 (local junk gitignored — Mathis rm -rf à goût)
parity_check weglot    : ✓ 108 files match baseline
SCHEMA/validate_all    : ✓ 3439 files
audit_capabilities     : ✓ 0 orphans
agent_smoke_test       : ✓ 5/5 agents
6/6 GSG checks         : ✓ ALL PASS
bandit                 : HIGH=0 actif · MEDIUM B608=0 · MEDIUM B314=0
0 hardcoded secrets, 0 env reads outside growthcro/config.py
```

### Livrables clés à connaître

| Livrable | Path | Use |
|---|---|---|
| **Architecture map** machine | `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` | 251 modules indexed, auto-regen via `scripts/update_architecture_map.py` |
| **Architecture map** visuelle | `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.md` + `deliverables/architecture-explorer.html` | 6 Mermaid views + UI interactive |
| **Skills blueprint** | `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` v1.2 | 5 combo packs + 4 skills installés + 5 MCPs server-level (Context7 + 4 prod pending) |
| **MCPs procedures** | `.claude/docs/reference/MCPS_INSTALL_PROCEDURE_2026-05-12.md` | 4 procédures Mathis OAuth (Supabase + Sentry + Meta Ads + Shopify) |
| **CODE_AUDIT** | `reports/CODE_AUDIT_2026-05-11.md` | 968 findings catalogués · top 10 actions ICE-ranked |
| **SKILLS_DISCOVERY** | `reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md` | 28 candidats web search · top 6 stratosphère installés · 5 "Interesting to test" pending POCs |
| **Doctrine code** | `.claude/docs/doctrine/CODE_DOCTRINE.md` (incl. §LOG post-#28) | Mono-concern · ≤800 LOC · env via config · logger structuré |
| **Observability** | `growthcro/observability/logger.py` (131 LOC) | JSON-line stdout · `get_logger(__name__)` · correlation_id contextvar |

## 2. Actions humaines Mathis (cleared avant prochaine session ?)

Status à vérifier en début de session. **5 actions clés** + 2 optionnelles :

| # | Action | Effort | Status à check | Débloque |
|---|---|---|---|---|
| 1 | `claude mcp add context7 -- npx -y @upstash/context7-mcp` | 1min | ☐ | universel — anti-hallucination Next.js 14 / Supabase v2 |
| 2 | OAuth flows × 4 MCPs (Supabase + Sentry + Meta Ads + Shopify) — cf [MCPS_INSTALL_PROCEDURE](../reference/MCPS_INSTALL_PROCEDURE_2026-05-12.md) | 20min | ☐ | Wave B (Epic 4 deploy V28) |
| 3 | Review 69 doctrine_proposals V3.3 dans `data/learning/audit_based_proposals/REVIEW_2026-05-11.md` (pré-catégorisées 10A/28D/31R) | 3-5h focus | ☐ | doctrine V3.4 future |
| 4 | Live-run #19 LPs : `export ANTHROPIC_API_KEY=... && bash scripts/test_gsg_regression.sh` (~$2 + 15min) | 15min | ☐ | Wave C (Epic 3 follow-up #19b + Epic 6 reality loop) |
| 5 | Setup Vercel + Supabase EU + Fly.io/Railway (`vercel link` + `npx supabase init` + choisir backend host) | 1-2h | ☐ | Wave B (Epic 4 deploy V28) |
| 6 *(opt)* | `rm -rf skills/site-capture/scripts/_archive_deprecated_2026-04-19/` (local junk gitignored) | 5sec | ☐ | lint FAIL = 0 absolu |
| 7 *(opt)* | Growth Society direction : tarif + branding agency products (Epic #7 cleanup epic) | 30min | ☐ | commercialisation Google/Meta Ads audits |

### Comment vérifier en début de session

```bash
# 1. Context7 installé ?
claude mcp list 2>&1 | grep -i context7

# 2. 4 MCPs OAuth ?
claude mcp list 2>&1 | grep -E "supabase|sentry|meta-ads|shopify"

# 3. 69 proposals reviewés ?
grep -c "Mathis_final:" data/learning/audit_based_proposals/REVIEW_2026-05-11.md

# 4. Live-run #19 fait ?
ls -la data/_pipeline_runs/_regression_19/_summary.json 2>&1
# OR check screenshots:
ls deliverables/gsg_stratosphere/screenshots/*-live-*.png 2>&1

# 5. Setup deploy ?
ls webapp/.vercel/ 2>&1
cat webapp/.env.local 2>/dev/null | grep -c "SUPABASE_URL"
```

## 3. Waves d'epics activables

### Wave A — Autonome (démarrable immédiatement)

| Epic | Effort | Trigger sub-PRD | File scope (worktree) |
|---|---|---|---|
| **#1 Typing Strict Rollout** | M, 4-5j | "lance sub-PRD typing-strict-rollout" | `moteur_gsg/core/visual_intelligence.py` + `context_pack.py` + `growthcro/recos/orchestrator.py` |
| **#2 Micro-Cleanup Sprint** | XS, 4-6h | "lance sub-PRD micro-cleanup" | `moteur_gsg/core/copy_writer.py` split · `growthcro/gsg_lp/` archive · `.gitignore` pattern |
| **#5 POCs Skills (partiel)** | M étalable | "lance POC <a/b/c/d/e>" | Feature branch par POC, scope défini par POC |

**Parallèle safe** : disjoint file scopes — peuvent tourner en agents background simultanés.

### Wave B — DEPEND Mathis Context7 + 4 OAuth + Vercel/Supabase projets créés (actions #1+#2+#5)

| Epic | Effort | Trigger sub-PRD |
|---|---|---|
| **#4 Production Deploy V28** | XL, 1-2 semaines | "lance sub-PRD production-deploy-v28" |

### Wave C — DEPEND Mathis live-run #19 validé + credentials 3 clients (actions #3+#4)

| Epic | Effort | Trigger sub-PRD |
|---|---|---|
| **#3 Follow-up #19b GSG 4 page_types** | L, 7-10j | "lance sub-PRD 19b-page-types" |
| **#6 Reality + Experiment + Learning Loop Live** | XL étalable 3 sem | "lance sub-PRD reality-loop-live" |

## 4. Recommandation prochaine session

### Si Mathis a fait 0 actions humaines

→ Wave A immédiate (autonome). Recommend Epic 1 ∥ Epic 2 ∥ 1 POC Epic 5 (a/b ou c).

Lancement : 3 worktrees + 3 agents background. ETA ~1 semaine.

### Si Mathis a fait actions 1+2+5 (Context7 + OAuth + setup deploy)

→ Wave B prioritaire. Epic 4 production deploy V28. ~1-2 semaines. Wave A peut tourner en parallèle si bande passante.

### Si Mathis a fait actions 3+4 (review proposals + live-run #19)

→ Wave C activable. Epic 3 follow-up #19b et/ou Epic 6 reality loop.

### Si Mathis a TOUT fait (5 actions cleared)

→ Plein régime. 3 waves en parallèle si ressources le permettent. Sinon prioriser : Wave B (deploy = ROI commercial immédiat) > Wave A (typing/cleanup) > Wave C (validation produit).

## 5. Règles d'optimisation (rappel)

- **Skill cap ≤ 8/session** : respecter les combo packs définis dans [BLUEPRINT.md](../reference/SKILLS_INTEGRATION_BLUEPRINT.md) v1.2
- **MCPs ≠ skills** : MCPs server-level hors compte 8/session
- **Worktrees** pour multi-agent parallèle (scopes disjoints obligatoires)
- **Sub-PRDs au moment du sprint** (AD-9) : éviter specs stale
- **MANIFEST §12** : commit séparé par epic merge
- **Doctrine code** : ≤ 800 LOC + mono-concern + env via `growthcro/config.py`
- **V26.AF immutable** : prompt persona_narrator ≤ 8K chars (assert runtime)
- **V3.2.1 + V3.3 backward compat** : V3.3 opt-in seulement
- **Gates green obligatoire** pré-commit : `lint_code_hygiene.py --staged` exit 0
- **Logger structuré** : utiliser `get_logger(__name__)` dans pipelines (§LOG)

## 6. Quick-access commands

```bash
# Standup / status général
bash .claude/skills/ccpm/references/scripts/status.sh    # si CCPM marketplace dispo
# OR manuel :
git log --oneline -5
gh issue list --state open --limit 10

# Architecture map à jour ?
python3 scripts/update_architecture_map.py  # idempotent

# Audit santé
python3 scripts/lint_code_hygiene.py
python3 scripts/audit_capabilities.py
python3 SCHEMA/validate_all.py
bash scripts/parity_check.sh weglot
bash scripts/agent_smoke_test.sh

# 6/6 GSG checks
for c in canonical controlled_renderer creative_route_selector visual_renderer intake_wizard component_planner; do
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_gsg_$c.py 2>&1 | grep -oE "PASS|FAIL"
done

# Logger smoke test
python3 -c "from growthcro.observability.logger import get_logger, set_correlation_id; set_correlation_id('test'); get_logger('test').info('smoke')"

# Architecture explorer (visuel)
open deliverables/architecture-explorer.html
```

## 7. PRDs disponibles + statut

| PRD | Status | Path |
|---|---|---|
| `codebase-cleanup` | ✅ completed 2026-05-10 | `.claude/prds/codebase-cleanup.md` |
| `webapp-stratosphere` | ✅ completed 2026-05-11 | `.claude/prds/webapp-stratosphere.md` |
| `hardening-and-skills-uplift` | ✅ completed 2026-05-12 | `.claude/prds/hardening-and-skills-uplift.md` |
| **`post-stratosphere-roadmap`** | 🔵 **ACTIVE** (master continuation) | `.claude/prds/post-stratosphere-roadmap.md` |

**Sub-PRDs à créer** au moment de chaque sprint :
- `typing-strict-rollout` (Epic 1)
- `micro-cleanup-sprint` (Epic 2)
- `follow-up-19b-page-types` (Epic 3)
- `production-deploy-v28` (Epic 4)
- `poc-skills-interesting-to-test` (Epic 5 — ou un sub-PRD par POC)
- `reality-loop-live` (Epic 6)

---

**Fin du continuation plan**. Bonne prochaine session 🚀
