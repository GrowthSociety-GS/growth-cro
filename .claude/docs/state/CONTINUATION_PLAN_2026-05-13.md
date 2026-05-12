# Continuation Plan — 2026-05-13 (Next Session Entry Point)

> **Point d'entrée prochaine session Claude Code (reprise après /clear).**
> Lis ce document + le PRD master [`webapp-full-buildout`](../../prds/webapp-full-buildout.md) avant de toucher au code.
>
> Une fois lu, tu sais : (1) où on en est exactement post-session 2026-05-12, (2) credentials live, (3) priorité immédiate (FR-1 consolidate microfrontends), (4) actions Mathis humaines toujours pending.

## 1. État de la session précédente (closing snapshot 2026-05-12T17:06Z)

**Date close** : 2026-05-12T17:06Z
**main HEAD** : `52ed96e` (feat(ccpm): webapp-full-buildout master PRD — 6 sub-PRDs roadmap)
**Working tree** : clean
**origin/main** : synchronisé (tout pushed)
**Worktrees actifs** : `growth-cro/` (main) seul
**Stashes** : 3 (regen artifacts pré-merges, non-pertinents — voir §6 cleanup optionnel)

### Programmes/Epics livrés 2026-05-12 (énorme journée — 25 commits)

| Programme | État | Highlight |
|---|---|---|
| **Wave A Epic 1** typing-strict-rollout | ✅ Merged main (Epic #29, 5/5 tasks) | mypy strict scope 13→0, 3 Pydantic models, gate régression-proof |
| **Wave A Epic 2** micro-cleanup-sprint | ✅ Merged main (Epic #35, 3/3 tasks) | copy_writer split mono-concern, gsg_lp archived, .gitignore wildcard |
| **Wave B Epic 4 PARTIAL** | 🟡 In progress | Vercel + Supabase EU + Mathis logged in + seed data |
| **Sub-PRDs validation** | ✅ Written | webapp-shell-validation + webapp-full-buildout (6 sub-PRDs roadmap) |

### Webapp Production State

- 🌐 **URL** : https://growth-cro.vercel.app
- ✅ HTTP 200 sur `/`, `/login`, `/privacy`, `/terms`
- ✅ Auth fonctionnel : email + password (magic link rate-limited free tier — bypass via admin API)
- ✅ Dashboard wired Supabase (vue `clients_with_stats` + table `runs`)
- ✅ 3 clients seedés avec data réaliste (Acme SaaS / Japhy / Doctolib × 2 audits × 5 recos)
- ⚠️ Routes `/audit`, `/reco`, `/gsg`, `/reality`, `/learning` → 404 (microfrontends scaffold non deployés)
- 🔴 Out-of-scope V1 confirmé : Google Ads, Meta Ads, Reality live, GSG trigger UI, FastAPI deploy

### Gates état final (main HEAD `52ed96e`)

```
lint_code_hygiene.py   : FAIL=1 (local junk _archive_deprecated, gitignored)
typecheck.sh           : strict scope 0 errors + global 1/603 budget
SCHEMA/validate_all    : ✓ 3439 files
audit_capabilities     : ✓ 0 orphans HIGH
parity_check weglot    : ✓ 108 files
bandit                 : HIGH=0 actif
```

## 2. Credentials live (à protéger)

### Webapp Mathis
- **URL login** : https://growth-cro.vercel.app/login
- **Email** : `tech@growth-society.com`
- **Password** : ⚠️ **TEMP, set via admin API 2026-05-12** — **À CHANGER immédiatement** au prochain login (Supabase Dashboard → Authentication → Users → tech@growth-society.com → Reset password)

### Supabase
- **Dashboard** : https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc
- **Project ref** : `xyazvwwjckhdmxnohadc`
- **Region** : Frankfurt (eu-central-1)
- **service_role JWT** : ⚠️ **PARTAGÉ DANS CHAT 2026-05-12** — **À ROTATER** (Settings → API → "Reset service_role key") + update Vercel env var après rotation

### Vercel
- **Dashboard** : https://vercel.com/tech-4696s-projects/growth-cro
- **Project ID** : `prj_4l9eRL5kJjEkWQvnZI3BN2yVQXzB`
- **Team ID** : `team_iKbzzgWDkWzSObzviFNVmR4Q`
- **Production URL** : https://growth-cro.vercel.app

### Key DB IDs (pour scripts/dev)
- **Organization Growth Society** : `571e55b2-b499-4126-831a-86a1ffa8a03a`
- **Mathis auth.users.id** : `1d9c9c4c-6859-42a6-aa57-c261ac1b6e05`
- **Mathis role** : admin (in org_members)

## 3. Active PRDs (où regarder)

| PRD | Status | Path | Use |
|---|---|---|---|
| `post-stratosphere-roadmap` | 🔵 master continuation | `.claude/prds/post-stratosphere-roadmap.md` | Wave A done, Wave B EXTENDED in progress |
| `webapp-full-buildout` | 🟢 ACTIVE master | `.claude/prds/webapp-full-buildout.md` | 6 sub-PRDs roadmap, ~4-5j critical path |
| `webapp-shell-validation` | 🟢 active gate | `.claude/prds/webapp-shell-validation.md` | Decision matrix FastAPI ship/defer |

### Sub-PRDs to CREATE next session (via /ccpm)
- `webapp-consolidate-architecture` (FR-1, blocking, 1-1.5j) ← **première priorité**
- `webapp-clients-audits-recos` (FR-2, M, 1-2j)
- `webapp-gsg-studio` (FR-3, S-M, 0.5-1j)
- `webapp-learning-lab` (FR-4, S-M, 1j, conditional)
- `webapp-settings-admin` (FR-5, S, 0.5j)
- `webapp-polish-validation` (FR-6, S, 0.5-1j)

## 4. Priorités demain (ordered)

### 🔥 Critical security cleanup (5 min, à faire AVANT toute autre action)

1. **Login webapp** → change ton temp password
   - https://growth-cro.vercel.app/login
   - Login avec credentials de §2
   - Supabase dashboard → Authentication → ton user → Reset password → choisir un mdp fort
2. **Rotate service_role JWT**
   - https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc/settings/api
   - Click "Reset" sur service_role secret
   - Update Vercel env var `SUPABASE_SERVICE_ROLE_KEY` avec nouvelle valeur (via Vercel dashboard OR via my API call si tu redonnes accès)

### Phase 1 — FR-1 Consolidate microfrontends (BLOCKING, M 1-1.5j)

**Pourquoi** : les 5 microfrontends scaffold (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) ne sont pas déployés. Consolider DANS shell = 1 deploy, simplifie tout le reste.

**Trigger CCPM** : dis à Claude *"lance sub-PRD webapp-consolidate-architecture via /ccpm"*

**Étapes** :
1. /ccpm parse master PRD FR-1 → epic.md + tasks
2. Move `webapp/apps/{audit,reco,gsg-studio,reality,learning}-*/app/*` → `webapp/apps/shell/app/{audits,recos,gsg,reality,learning}/`
3. Delete `webapp/microfrontends.json`
4. Archive `_archive/webapp_microfrontends_2026-05-12/`
5. Update Sidebar component : internal Next.js Link routing
6. Gate-vert : lint + parity + schemas + Vercel rebuild ok

**ETA** : ~30-60 min wall-clock avec agent background (mostly file moves + refactor mécanique).

### Phase 2 — FR-2/3/5 parallel agents (post FR-1 merge)

3 worktrees parallèles, file-disjoint :
- FR-2 `webapp-clients-audits-recos` : routes `/clients`, `/clients/[slug]`, `/audits/[id]`, `/recos`
- FR-3 `webapp-gsg-studio` : route `/gsg` avec iframe preview des LPs
- FR-5 `webapp-settings-admin` : route `/settings` 4 onglets

**ETA** : ~2-4h wall-clock total avec 3 agents background.

### Phase 3 — FR-6 polish + validation (post FR-2/3/5 merge)

- UX checklist manuel + 5+ screenshots
- 1 consultant Growth Society feedback session (30min)
- Decision matrix FastAPI ship/defer

### Phase 4 — Conditional FR-4 learning-lab

Activé uniquement si Mathis action #3 (review 69 doctrine_proposals) fait.

## 5. Actions Mathis humaines toujours pending

| # | Action | Effort | Débloque |
|---|---|---|---|
| 1 | Context7 MCP install (`claude mcp add context7 ...`) | 1min | Anti-hallucination universel |
| 2 | 4 OAuth MCPs : Supabase DEV ONLY + Sentry + Meta Ads + Shopify | 20min | Wave B Epic 4 deploy V28 (mais déjà partial done) |
| 3 | Review 69 doctrine_proposals V3.3 → assign Mathis_final | 3-5h focus | V3.4 doctrine future + FR-4 learning lab UI |
| 4 | Live-run #19 LPs (`bash scripts/test_gsg_regression.sh`) | 15min + $2 | Wave C Epic 3 follow-up GSG + Epic 6 reality |
| 5 | (PARTIAL DONE) Vercel + Supabase setup | ✅ done | — |
| 6 (opt) | `rm -rf skills/site-capture/scripts/_archive_deprecated_2026-04-19/` | 5sec | Lint FAIL=0 local (gitignored déjà donc impact 0) |

## 6. Cleanup optionnel (low priority)

### 3 stashes git à dropper si non-pertinents

```bash
git stash list
# stash@{0}: pre-merge Epic 2: regen artifacts on main
# stash@{1}: pre-merge: CAPABILITIES regen + progress stubs (superseded by epic merge)
# stash@{2}: regen artifacts during Phase 1 (CAPABILITIES + gsg_demo HTMLs)

# Inspect avant de drop :
git stash show stash@{0}

# Drop all si OK :
git stash clear
```

### Vercel cleanup
- Vieilles deployments en preview/errored peuvent être supprimées si tu fais le ménage (Vercel dashboard → Deployments)

### Browser
- Garde le tab https://growth-cro.vercel.app/login bookmarké
- Si "Failed to fetch" : incognito + hard refresh (le bug code est fix mais cache JS peut persister)

## 7. Comment démarrer la session demain

### Option 1 — Reprise structurée (recommandé)

```
1. Ouvre Claude Code dans /Users/mathisfronty/Developer/growth-cro
2. /clear  (fresh context — fenêtre 1M tokens dispo)
3. Dis à Claude :

   "Lis CLAUDE.md, lance growthcro-strategist diagnostic pour avoir l'état,
    puis lance FR-1 webapp-consolidate-architecture via /ccpm."

4. Claude exécutera :
   - Init step #12 (lire ce continuation plan)
   - Diagnostic skill (state-of-project + 5 actions Mathis status)
   - Create sub-PRD webapp-consolidate-architecture via /ccpm
   - Decompose + sync GitHub + launch agent
```

### Option 2 — Reprise libre

```
1. /clear
2. "Reprend le programme webapp-full-buildout. On part sur FR-1."
3. Claude lit le master PRD + démarre
```

### Option 3 — Audit avant action

```
1. /clear
2. "Lance growthcro-strategist diagnostic complet. Donne-moi un état des lieux honnête
    + recommendations next steps."
3. Tu lis, tu valides la direction, puis on lance FR-1
```

## 8. Quick-access commands (copy-paste)

### Login webapp
```bash
open https://growth-cro.vercel.app/login
# Email: tech@growth-society.com
# Password: voir chat session 2026-05-12 OU reset via Supabase dashboard
```

### Check Supabase
```bash
open https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc
```

### Check Vercel
```bash
open https://vercel.com/tech-4696s-projects/growth-cro
```

### Audit santé local
```bash
cd /Users/mathisfronty/Developer/growth-cro
python3 scripts/lint_code_hygiene.py
python3 scripts/audit_capabilities.py
bash scripts/typecheck.sh
bash scripts/parity_check.sh weglot
python3 SCHEMA/validate_all.py
```

### Re-seed test data (si DB reset)
```bash
SUPABASE_SERVICE_ROLE_KEY="<ta-key-rotatée>" \
  python3 scripts/seed_supabase_test_data.py
```

### Git state
```bash
git log --oneline -10
git status
git stash list
git worktree list
```

## 9. Récap honnête fin de journée

**Énorme journée — 25 commits, 3 epics, 1 webapp deployée :**

- ✅ Wave A 2/3 epics (typing strict + micro-cleanup) shipped + closed GitHub
- ✅ Wave B Epic 4 PARTIAL : Vercel + Supabase + auth working + dashboard with data
- ✅ Master plan multi-jours ready (webapp-full-buildout)
- ✅ Tout pushed sur GitHub origin/main
- ✅ Continuation plan dated 2026-05-13 = ce fichier

**Pas fait (pas grave, programmé) :**
- FR-1..FR-6 buildout features (planned, ~4-5j critical path)
- Security cleanup (password change, service_role rotation)
- Mathis actions humaines #1, #2, #3, #4

**Énergie utilisée tonight** : ~10h focus. Tu as fait un boulot énorme.

---

**Bonne nuit. À demain. La webapp tourne sur https://growth-cro.vercel.app pendant que tu dors 😴**
