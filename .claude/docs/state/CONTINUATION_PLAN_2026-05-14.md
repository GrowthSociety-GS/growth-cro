# Continuation Plan — 2026-05-14 (post-clear reprise)

> **Point d'entrée prochaine session Claude Code** post `/clear` context.
>
> User a clear le context après session 2026-05-13 marathon (13+ commits, 10 sub-PRDs Wave P0/P1/P2 + SP-11 + RSC fix + skills deep research). Reprise via ce document + master PRD `webapp-data-fidelity-and-skills-stratosphere-2026-05`.

## 1. État de la session précédente (closing 2026-05-13)

**Date close** : 2026-05-13T15:00Z (estimé)
**main HEAD** : `83bad9a` (deep research + sub-PRD skills stratosphère)
**Working tree** : clean
**origin/main** : synced

### Programmes shipped 2026-05-13 (énorme journée — 13+ commits)

| Programme | État | Highlight |
|---|---|---|
| **Wave P0** webapp-v26-parity-and-beyond | ✅ 6/6 sub-PRDs shipped + merged | SP-1 design-system, SP-2 command-center, SP-3 brand-dna, SP-4 audit-pillars, SP-5 gsg-handoff, SP-6 navigation |
| **Wave P1** interactivité | ✅ 2/2 shipped | SP-7 modals + CRUD, SP-8 search/filter/sort URL state |
| **Wave P2** polish + beyond | ✅ 2/2 shipped | SP-9 a11y + loading/error, SP-10 funnel + multi-judge + learning |
| **SP-11** screenshots Supabase Storage | ✅ shipped + uploaded | 1840/1840 WebP, 866 MB, 0% fail, 35 min |
| **RSC crash fix** | ✅ `60f62a7` | Server Component onClick crash on /audits/[c]/[a] |
| **Deep research skills** | ✅ `83bad9a` | 3 skills + 2 natives identifiés |
| **MEGA PRD reset** | ✅ `<commit>` | webapp-data-fidelity-and-skills-stratosphere-2026-05 |

### Webapp Production State (live)

- 🌐 **URL** : https://growth-cro.vercel.app
- ✅ Build OK : 24 routes, 87.3 KB shared First Load
- ✅ Auth Supabase email + password
- ⚠️ **Data riche pas affichée** : recos minimalistes (criterion_id only, no reco_text), "Pas de scores disponibles", broken-image captures
- ⚠️ **Migration sur mauvaise source** : `growth_audit_data.js` (V21 cluster pauvre) au lieu de `recos_enriched.json` (V13 riche)

### Gates état (main HEAD `<83bad9a OR new>`)

```
lint_code_hygiene.py   : FAIL=1 (baseline seed_supabase_test_data.py)
typecheck.sh           : ✓ exit 0
SCHEMA/validate_all    : ✓ 15 files
audit_capabilities     : ✓ 0 orphans HIGH
parity_check weglot    : ✓
build                  : ✓ 24 routes, 87.3 KB shared
```

## 2. Credentials live (à protéger)

### Webapp Mathis
- **URL login** : https://growth-cro.vercel.app/login
- **Email** : `tech@growth-society.com`
- **Password** : ⚠️ **À ROTATER** (`.env.local` contains current value, see `WEBAPP_LOGIN_PASSWORD`)

### Supabase
- **Dashboard** : https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc
- **Project ref** : `xyazvwwjckhdmxnohadc`
- **Region** : Frankfurt (eu-central-1)
- **service_role JWT** : 🔴 **URGENT À ROTATER** — repo PUBLIC, JWT in git history (commits 52ed96e+ pre-redact dc26e35)

### Vercel
- **Dashboard** : https://vercel.com/tech-4696s-projects/growth-cro
- **Project ID** : `prj_4l9eRL5kJjEkWQvnZI3BN2yVQXzB`
- **Team ID** : `team_iKbzzgWDkWzSObzviFNVmR4Q`
- **Production URL** : https://growth-cro.vercel.app

### Supabase Storage
- **Bucket** : `screenshots` (public read, service_role write)
- **Path scheme** : `<client>/<page>/<filename>.webp`
- **Files** : 1840 WebP uploaded 2026-05-13 (95 clients, 231 pages)

### Key DB IDs
- **Organization Growth Society** : `571e55b2-b499-4126-831a-86a1ffa8a03a`
- **Mathis auth.users.id** : `1d9c9c4c-6859-42a6-aa57-c261ac1b6e05`

## 3. Active PRDs

| PRD | Status | Path | Priority |
|---|---|---|---|
| `post-stratosphere-roadmap` | 🔵 master continuation | `.claude/prds/post-stratosphere-roadmap.md` | reference |
| `webapp-v26-parity-and-beyond` | ✅ 10 sub-PRDs done | `.claude/prds/webapp-v26-parity-and-beyond.md` | done |
| **`webapp-data-fidelity-and-skills-stratosphere-2026-05`** | 🟢 **ACTIVE master** | `.claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md` | **P0 critical reset** |
| `skill-stratosphere-2026-05-integration` | 🟡 superseded by MEGA PRD | `.claude/prds/skill-stratosphere-2026-05-integration.md` | reference |
| `webapp-screenshots-storage-migration` | ✅ shipped | `.claude/prds/webapp-screenshots-storage-migration.md` | done |
| `webapp-rich-ux-and-screens` | ✅ shipped | `.claude/prds/webapp-rich-ux-and-screens.md` | done |

### Sub-PRDs MEGA PRD à créer next session (via /ccpm)

**Wave A — Data Fidelity (P0 critique, blocking)** :
- SP-A1 `webapp-remigrate-recos-enriched` (M, 2-3h) — re-migrate depuis `recos_enriched.json` (438 files)
- SP-A2 `webapp-remigrate-scores-pillars` (M, 2-3h) — re-migrate depuis `score_*.json` per pillar
- SP-A3 `webapp-screenshots-prod-debug` (S, 1h) — verify + fix screenshots Supabase Storage prod redirect
- SP-A4 `webapp-native-review-vercel-agent` (S, 30-60 min) — activate /review + Vercel Agent

**Wave B — Skills Stratosphère (P1)** :
- SP-B1 `skill-based-architecture-install` (S-M, 45 min) — consolide doctrine → skills/growthcro/
- SP-B2 `superpowers-poc` (M, 1-2h) — multi-step plans + TDD enforcement POC
- SP-B3 `gstack-poc` (M, 1-2h) — AI team personas POC

**Wave C — Cleanup (P2)** :
- SP-C1 `blueprint-v1-3-update` (S, 30 min) — BLUEPRINT.md v1.2 → v1.3
- SP-C2 `continuation-plan-2026-05-15` (S, 30 min) — close

## 4. Priorités demain (ordered)

### 🔴 Critical security (5 min, AVANT toute autre action)

1. **Rotater service_role JWT Supabase**
   - https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc/settings/api
   - Click "Reset" sur service_role secret
   - Copier nouvelle clé
   - Update Vercel env var `SUPABASE_SERVICE_ROLE_KEY` (Production + Preview)
   - Update `.env.local` racine si présente

### Wave A — Data Fidelity (BLOCKING, ~6-8h)

**Pourquoi P0** : le user a vu la webapp et constaté que c'est "écran de fumée". Recos minimalistes (`per_01`, `ux_07`) + "Pas de scores disponibles" + broken screenshots. Le fix data fidelity est BLOCKING pour la satisfaction user.

**Trigger** : *"Lis le master PRD `webapp-data-fidelity-and-skills-stratosphere-2026-05` et lance Wave A. Crée 3 worktrees + 3 agents background pour SP-A1, SP-A2, SP-A3 en parallèle, puis SP-A4 en foreground."*

**Steps Wave A** :
1. Read MEGA PRD : `.claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md`
2. Read deep research : `.claude/docs/state/SKILLS_DEEP_RESEARCH_2026-05-13.md`
3. /ccpm prd-new for SP-A1, SP-A2, SP-A3 if not already created
4. Create 3 worktrees (epic-spA1-recos, epic-spA2-scores, epic-spA3-screens)
5. Launch 3 agents background avec briefings précis du MEGA PRD
6. Wait notifications, merge sequential, push
7. Run SP-A4 (/review + Vercel Agent) en foreground

### Wave B — Skills Stratosphère (~3-5h)

**Pourquoi P1** : durabilité long-terme. Skills stratosphère identifiés répondent au besoin user "comprendre comme un humain". Pas immédiatement visible côté user mais foundation critique.

**Trigger** : *"Wave A merged ?, OK launch Wave B. Foreground SP-B1 skill-based-architecture, puis 2 agents background pour SP-B2 Superpowers + SP-B3 GStack."*

### Wave C — Cleanup

**Trigger** : Wave A + B done → BLUEPRINT v1.3 + CONTINUATION_PLAN 2026-05-15

## 5. Actions Mathis humaines pending

| # | Action | Effort | Urgency |
|---|---|---|---|
| 1 | 🔴 **Rotater service_role JWT** | 5 min | URGENT (repo public, JWT exposed) |
| 2 | Test post Wave A : login + 5 clients audits checks | 15 min | After Wave A done |
| 3 | Vercel Agent enable Dashboard | 5 min | During Wave A SP-A4 |
| 4 | Context7 MCP install (action #1 v1.2) | 1 min | When ready |
| 5 | Review 69 doctrine_proposals V3.3 | 3-5h focus | Optional (FR-4 webapp-learning-lab future) |

## 6. Commands quick-access

### Login webapp
```bash
open https://growth-cro.vercel.app/login
# Email: tech@growth-society.com
# Password: voir .env.local (post-rotation)
```

### Verify Supabase Storage screenshots
```bash
curl -I "https://xyazvwwjckhdmxnohadc.supabase.co/storage/v1/object/public/screenshots/japhy/collection/desktop_asis_fold.webp"
# Expect: HTTP/2 200
```

### Verify webapp screenshot redirect
```bash
curl -I "https://growth-cro.vercel.app/api/screenshots/japhy/collection/desktop_asis_fold.png"
# Expect: HTTP/2 302 with Location header to Supabase
```

### Run data fidelity scripts (Wave A)
```bash
# SP-A1 (after script created)
SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY="<rotated-key>" \
  python3 scripts/migrate_recos_enriched_to_supabase.py

# SP-A2 (after script created)
SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY="<rotated-key>" \
  python3 scripts/migrate_scores_to_supabase.py
```

### Git state
```bash
git log --oneline -10
git status
git worktree list
git stash list
```

### Vercel status
```bash
vercel ls growth-cro --prod | head -3
vercel env ls production | grep -i supabase
```

## 7. Trigger phrase prochaine session

Tape ça à Claude Code post `/clear` :

```
Lis CLAUDE.md init steps. Puis lis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-14.md
2. .claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md
3. .claude/docs/state/SKILLS_DEEP_RESEARCH_2026-05-13.md

Lance Wave A : SP-A1 (re-migrate recos) + SP-A2 (re-migrate scores) + SP-A3 (debug screenshots) en parallèle via 3 worktrees + 3 agents background. Notif à chaque completion, merge sequential, push.
```

## 8. Notes critiques

### Vrai problem identifié 2026-05-13
- **Migration data sur mauvais fichier source** : `growth_audit_data.js` (V21 cluster pauvre) au lieu de `recos_enriched.json` (V13 riche)
- Conséquence : webapp affiche `per_01`, `ux_07`, `tech_03` minimalistes au lieu de reco_text + anti_patterns rich
- Fix = re-migration depuis `recos_enriched.json` (Wave A SP-A1)

### Score doctrine "Pas de scores"
- Migration n'a pas inclus `score_*.json` (6 pillars per page) qui contient la vraie data
- Fix = re-migrate depuis `score_*.json` (Wave A SP-A2)

### Screenshots prod
- Upload Supabase Storage = 1840/1840 ✓ confirmed
- Visibility prod = à débugger (env vars, redirect, CORS)
- Fix = verify + adjust (Wave A SP-A3, prob ~30 min)

### Skills stratosphère découverts
- `skill-based-architecture` (WoJiSama) — meta-skill que le user demandait depuis "quelques jours"
- `Superpowers` (obra), `GStack` (garrytan), native `/review`, Vercel Agent
- Install Wave B après Wave A merged

### Service_role security
- Repo PUBLIC + JWT in git history = bot scanners trouvent en heures/jours
- Risque : DROP TABLE clients (perte 56 clients data) + spam Supabase
- Mitigation : rotation 5 min, Mathis side

---

## 9. Récap honnête fin de journée 2026-05-13

**Énorme journée — 13+ commits, 10+ sub-PRDs, 24 routes webapp, skills research :**

- ✅ Wave P0+P1+P2 (10 sub-PRDs) shipped + merged
- ✅ SP-11 screenshots Supabase Storage : 1840 WebP uploaded, 866 MB
- ✅ Deep research skills 2026 : 3 skills + 2 natives identifiés
- ✅ MEGA PRD reset documented (this PRD)
- ✅ Tout pushed sur origin/main

**Pas fait (programmé Wave A/B/C demain) :**
- Wave A : data fidelity re-migration (recos_enriched.json + score_*.json)
- Wave A : screenshots prod debug
- Wave A : /review + Vercel Agent
- Wave B : skill-based-architecture + Superpowers + GStack
- Wave C : BLUEPRINT v1.3

**Énergie utilisée** : ~12h focus pour Wave P0/P1/P2 + audit + deep research. User frustré (légitime) car écran de fumée visible.

**Action urgente Mathis** : rotater service_role JWT (5 min) **AVANT** Wave A.

---

**À demain. La webapp tourne sur https://growth-cro.vercel.app mais montre data minimaliste. Wave A va fix ça en ~6-8h. 🎯**
