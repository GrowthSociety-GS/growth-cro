# GrowthCRO Architecture V1 (V28 target)

**Version**: 1.0 — 2026-05-11
**Scope**: Webapp V28 (Next.js 14 + Supabase EU + Vercel microfrontends).
**Status**: Active. Updated at each epic merge.

---

## 1. Goal

Industrialiser le consultant CRO senior automatisé GrowthCRO sur ~100 clients
de l'agence Growth Society — passer du V27 HTML statique (déjà livré comme
MVP honnête) à une webapp Next.js multi-tenant temps-réel.

Métriques cibles V28:

- < 2s pour charger la page client (P50).
- Auth fluide email/password + magic link.
- Realtime feed des `runs` (audit / gsg / reality / experiment).
- 56 clients live depuis Supabase.
- RGPD compliant (hosting EU, consent banner, droits documentés).

---

## 2. High-level diagram

```
                    +---------------------+
                    |  Vercel Edge (FRA)  |
                    |  microfrontends.json|
                    +---------------------+
                              |
        +-------+----------+--+--+----------+-------+
        |       |          |     |          |       |
      shell  audit-app  reco-app gsg-st.  reality  learning
       (3000)  (3001)    (3002)  (3003)   (3004)   (3005)
        \      \         /         |        |       /
         \      \       /          |        |      /
          \     +--- @growthcro/{ui,data,config} ---+
           \                       |
            \                      |  HTTPS
             \                     v
              +------------+    +------------------+
              | Supabase   |<-->| FastAPI backend  |
              | EU-central |    | (Railway/Fly.io) |
              | auth+pg+rt |    | growthcro/api    |
              +------------+    +------------------+
                                         |
                                         v
                          local pipelines (capture/perception/
                          scoring/recos/research/gsg_lp/multi_judge)
```

---

## 3. Microfrontend topology

| App                | Port | Role                                                      | Status (V28 v1)      |
|--------------------|------|-----------------------------------------------------------|----------------------|
| `shell`            | 3000 | Auth + nav + dashboard + realtime runs feed              | DEEP                 |
| `audit-app`        | 3001 | Audit pane port V27 (clients + audits + scores + recos)  | DEEP                 |
| `reco-app`         | 3002 | Recos browser + filters + priority counts                 | DEEP                 |
| `gsg-studio`       | 3003 | Brief wizard + LP preview + multi-judge stage strip      | DEEP                 |
| `reality-monitor`  | 3004 | Data sources panel (GA4/Meta/Google/Shopify/Clarity)     | PLACEHOLDER          |
| `learning-lab`     | 3005 | Doctrine proposals (V29) + Bayesian (V30) tracks         | PLACEHOLDER          |

Routing : `microfrontends.json` à la racine de `webapp/`. Chaque sous-app sous
son own basePath (`/audit`, `/reco`, `/gsg`, `/reality`, `/learning`) — Vercel
proxie via `@vercel/microfrontends`. En dev, Next.js rewrites locaux pointent
vers `localhost:3001..3005`.

Shared packages :

- `@growthcro/config` — env-derived config (mirror Python `growthcro/config.py`)
- `@growthcro/data` — Supabase client (browser + server + service role) + typed entities + queries
- `@growthcro/ui` — primitives (Button, Card, KpiCard, ScoreBar, RecoCard, Pill, ClientRow, NavItem, ConsentBanner) + tokens.css

---

## 4. Backend exposure — décision

**Option choisie : B — FastAPI sur Railway/Fly.io.**

Rationale :

| Critère                      | Option A (Vercel edge fn TS rewrite) | Option B (FastAPI sur Railway/Fly.io) |
|------------------------------|--------------------------------------|---------------------------------------|
| Réutilise code existant      | Non (rewrite endpoints en TS)        | OUI (zero changement `server.py`)     |
| Long-running tasks (audit)   | Non (timeout edge 30s)               | OUI (workers async + Playwright)      |
| Playwright/capture pipeline  | Non (incompatible edge)              | OUI (Chrome headless dispo)           |
| Cold start                   | < 100ms                              | ~ 500ms                                |
| Coût                         | Pay-per-invocation                   | $5-10/mo Fly volume                    |
| Complexité ops               | Faible (Vercel managed)              | Moyenne (Dockerfile + deploy hook)     |

Option B gagne. La capture Playwright + research + LLM scoring ne tient pas
dans 30s edge runtime. Le `Dockerfile` à la racine du repo est déjà aligné
(Python 3.11 + Playwright). Reste : workflow Fly.io deploy + secret manager
(à finaliser dans un sub-PRD si Mathis veut formaliser).

URL backend : `NEXT_PUBLIC_API_BASE_URL=https://growthcro-api.fly.dev` (env).

CORS : whitelist domaine Vercel + `localhost:3000-3005`.

---

## 5. Supabase data model

Tables (4 migrations SQL dans `webapp/supabase/migrations/`):

```sql
organizations(id, slug, name, owner_id → auth.users, ...)
org_members(org_id, user_id → auth.users, role: admin|consultant|viewer)
clients(id, org_id, slug, name, business_category, homepage_url, brand_dna_json, panel_role, panel_status, ...)
audits(id, client_id, page_type, page_slug, page_url, doctrine_version, scores_json, total_score, total_score_pct, ...)
recos(id, audit_id, criterion_id, priority: P0|P1|P2|P3, effort: S|M|L, lift: S|M|L, title, content_json, oco_anchors_json, ...)
runs(id, org_id, client_id, type: audit|gsg|reality|experiment, status: pending|running|completed|failed, started_at, finished_at, output_path, metadata_json, ...)
```

Views (read-side, RLS héritée des tables sous-jacentes) :

- `clients_with_stats` — clients + audits_count + recos_count + avg_score_pct
- `recos_with_audit` — recos joined au client_id pour lookups per-client

Realtime : publication `supabase_realtime` enrichie de `runs` — la shell
souscrit `postgres_changes` sur ce canal.

---

## 6. RLS policies — isolation org-based

- **Anon role** : zéro accès lecture (sauf `auth.users` insert pour signup).
- **Authenticated** : accès via `is_org_member(org_id)` helper (security definer).
- **Service role** : bypass (utilisé par `scripts/migrate_v27_to_supabase.py` et
  par le backend FastAPI quand il écrit côté serveur).

Helper functions :

```sql
public.is_org_member(p_org_id uuid) -> boolean  -- user is in org_members
public.is_org_admin(p_org_id uuid)  -> boolean  -- AND role = 'admin'
```

Effet : un consultant Growth Society voit uniquement les `clients`, `audits`,
`recos`, `runs` de la table `organizations` dont il est membre. Croisement
inter-agences impossible par construction.

---

## 7. Auth flow

- **Email/password** : `supabase.auth.signInWithPassword`. Mot de passe stocké
  bcrypt côté Supabase. MFA optionnel (à activer en config projet).
- **Magic link** : `supabase.auth.signInWithOtp` → email → `/auth/callback?code=…`
  → `exchangeCodeForSession`. Redirection préservée via `?redirect=…`.
- **Cookies** : `@supabase/ssr` gère les cookies httpOnly côté Next.js — pas
  de token JWT en localStorage. Refresh automatique.
- **Middleware** : `webapp/apps/shell/middleware.ts` gate tout sauf `/login`,
  `/auth/callback`, `/privacy`, `/terms`. Si Supabase env manquant (CI/build),
  bypass gracieux pour ne pas casser le build.

---

## 8. Migration progressive V27 → V28

Pendant la transition :

- `deliverables/GrowthCRO-V27-CommandCenter.html` **reste accessible** (le V27
  HTML est livré comme MVP honnête — Task #20 ✅). Mathis l'utilise en parallèle.
- Bascule Mathis-driven : quand V28 atteint parité fonctionnelle (à valider
  visuellement page-par-page), on retire l'accès au V27. Pas avant.

Data migration : `python3 scripts/migrate_v27_to_supabase.py` parse
`deliverables/growth_audit_data.js` (5.5MB JSON inline) et UPSERT 56 clients
+ 185 audits + 3045 recos. **Idempotent** : re-run safe (delete-then-insert
sur les audits/recos par client, UPSERT sur clients via `(org_id, slug)`).

Mode DRY-RUN automatique si `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
absent — utile en CI smoke.

---

## 9. RGPD compliance

| Exigence                       | Implémentation                                                |
|--------------------------------|---------------------------------------------------------------|
| Hosting UE                     | Supabase eu-central-1 (Frankfurt) + Vercel Frankfurt edge    |
| Consent banner                 | `@growthcro/ui/ConsentBanner` mounted dans shell layout       |
| Droits utilisateurs            | `/privacy` page — accès / rectif / effacement / portabilité  |
| Sous-traitants documentés      | `/privacy` page liste Supabase / Vercel / Anthropic + DPAs   |
| Conservation                   | Audits 24 mois ; logs auth 90j (Supabase défaut)              |
| Chiffrement at-rest            | Supabase (AES-256) + Vercel deploy (TLS 1.3)                  |
| Pas de transfert hors UE       | Sauf Anthropic API (zero retention DPA)                       |

---

## 10. Skills combo "Webapp Next.js dev"

Per `SKILLS_INTEGRATION_BLUEPRINT.md` §combo packs :

- `frontend-design` — direction artistique générique
- `web-artifacts-builder` — shadcn/Tailwind/state-mgmt patterns
- `vercel-microfrontends` — archi microfrontends Next.js + zones
- `Figma Implement Design` — Figma→code si Mathis amène un design

≤ 4 skills/session pour éviter cacophonie (CLAUDE.md anti-pattern #12).

Skills *exclus* dans ce sprint :

- `Taste Skill` — impose dark/premium → conflit Brand DNA per-client.
- `theme-factory` — 10 thèmes pré-set → conflit Brand DNA.
- `lp-creator` / `lp-front` — notre GSG est plus évolué.

---

## 11. Anti-patterns guard-rail

Hard rules from CLAUDE.md re-asserted :

1. Mega-prompt persona_narrator > 8K chars → STOP (V26.AA régression -28pts)
2. `os.environ` / `os.getenv` hors `growthcro/config.py` → linter FAIL
3. Archives hors `_archive/` racine → linter FAIL
4. Notion modif sans demande explicite Mathis → interdit
5. Code avant design doc validé → interdit

Dans la TS-side, on miroir la règle env via `@growthcro/config` (un seul
chemin d'accès aux `process.env`).

---

## 12. Open questions pour Mathis

1. **Vercel project setup** : tu crées le projet `growthcro-shell` (+ 5 sous-apps)
   ou tu préfères que je te livre un script `vercel-init.sh` ?
2. **Supabase project EU** : tu crées le projet EU et tu partages la connection
   string + service role key (via .env local — pas en clair dans commit) ?
3. **Fly.io ou Railway** pour le backend FastAPI ? Fly.io a l'avantage volume
   persistant pour les captures Playwright ; Railway plus simple à wire.
4. **Test consultant agence** : tu invites un consultant test (email auth +
   org_member 'consultant') pour valider les RLS policies ?

---

## 13. Reference

- **Code doctrine** : `.claude/docs/doctrine/CODE_DOCTRINE.md`
- **Skills blueprint** : `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`
- **Architecture map (machine-readable)** : `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`
- **Manifest §12 changelog** : `.claude/docs/reference/GROWTHCRO_MANIFEST.md`
