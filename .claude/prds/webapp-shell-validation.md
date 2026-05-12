---
name: webapp-shell-validation
description: Valider que la webapp V28 shell (déployée sur Vercel + connectée Supabase EU) est utile avant d'investir dans FastAPI backend deploy. Phase de validation lecture-only avec Mathis comme premier user + 1 consultant Growth Society test. Décide ship/defer Epic 4 FastAPI deploy à l'issue.
status: active
created: 2026-05-12T16:19:28Z
parent_prd: post-stratosphere-roadmap
github_epic: (informal, no GitHub sync — light validation sprint)
wave: B
epic_index: 4-partial
ice_score: 280
---

# PRD: webapp-shell-validation

> Sub-PRD léger du master [`post-stratosphere-roadmap`](post-stratosphere-roadmap.md) (FR-4 Epic 4 partial).
> Sprint de validation avant decision gate FastAPI deploy.
> Pas de sync GitHub (trop léger), tâches tracked en informal todos + commits.

## Executive Summary

L'action Mathis #5 (deploy V28 setup) a été partiellement complétée le 2026-05-12 :
- ✅ **Vercel project** `growth-cro` deployé en production avec auto-deploy GitHub + Root Directory `webapp/` (Project ID `prj_4l9eRL5kJjEkWQvnZI3BN2yVQXzB`)
- ✅ **Supabase project** EU créé (`xyazvwwjckhdmxnohadc`, Frankfurt region) + 4 migrations + seed appliqués (8 tables + 2 views + 2 RPCs)
- ✅ **Vercel ↔ Supabase ↔ GitHub** triple integration : env vars synced auto, GitHub repo lié aux deux
- ⏳ **FastAPI backend deploy** : DÉFÉRÉ (analyse révèle pas critique court-terme — webapp peut fonctionner read-only via Supabase REST)

Ce sub-PRD encadre la phase de **validation read-only** : utiliser la webapp shell pendant 1-2 semaines pour décider si l'investissement FastAPI deploy (~1j) est justifié.

**URLs production** :
- 🌐 https://growth-cro.vercel.app
- 🎛️ https://vercel.com/tech-4696s-projects/growth-cro
- 🗄️ https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc

**Coût API** : $0 (validation only, pas de génération Sonnet).
**Durée cible** : 1-2 semaines (étalable selon feedback).

## Problem Statement

### Pourquoi ce sprint léger

1. **Sunk cost trap évité** : déployer FastAPI sur Fly.io/Railway = ~1j de boulot + budget Browserless cloud + secrets management + container ops. Pas vouloir investir avant d'avoir validé que la webapp shell apporte vraie valeur aux consultants.

2. **Architecture découplée pragmatique** : la chaîne `Mathis local CLI → Python pipeline → Supabase push → Webapp Vercel read` fonctionne sans FastAPI HTTP. La webapp = observatory des données, pas trigger.

3. **Feedback boucle courte** : avant d'industrialiser le trigger UI → FastAPI, valider que la UX read-only répond aux besoins consultants (display recos, navigate audits, exports).

4. **Décision gate explicite** : à l'issue de ce sprint, **Yes/No vote** sur FastAPI deploy basé sur feedback réel, pas sur intuition.

### Ce que ce sub-PRD apporte

- Procédure signup Mathis premier user + bootstrap organization
- Script Python autonome qui push 1-2 clients test à Supabase via service_role
- Checklist UX manuelle à compléter (display navigate, exports, etc.)
- Feedback form / template pour 1 consultant Growth Society test
- Decision matrix structuré pour ship/defer FastAPI à la fin

## User Stories

### US-1 — Mathis (premier user signup)

*Comme founder qui vient de déployer V28, je veux pouvoir signup avec mon email sur `/login`, confirmer mon email, et accéder à la webapp avec une organization perso pré-créée (Growth Society), pour valider que le flow auth Supabase + RLS policies marche.*

**AC** :
- Signup via https://growth-cro.vercel.app/login (form Supabase Auth UI)
- Email de confirmation reçu (Supabase default behavior, peut être désactivé dans dashboard)
- Login successful après confirmation
- Organization "Growth Society" auto-créée OU créée via SQL post-signup, Mathis = admin
- Au moins 1 route protégée accessible sans 401/403

### US-2 — Mathis (push test data en local)

*Comme founder qui veut tester l'affichage de la webapp, je veux pousser 2-3 clients fictifs avec leurs audits depuis mon environnement Python local vers Supabase, pour vérifier que la webapp affiche correctement les listes / details / recos.*

**AC** :
- Script `scripts/seed_supabase_test_data.py` créé (≤200 LOC, mono-concern)
- Push 2 clients fictifs (ex: "Acme Corp", "Demo Brand") avec :
  - 1 audit chacun (status: completed)
  - 5-10 recos enrichies par audit
  - Données réalistes (pas Lorem Ipsum)
- Script idempotent (re-run = mise à jour, pas duplicate)
- Webapp affiche les 2 clients dans la liste (route `/clients` ou équivalent)
- Détail client affiche ses audits + recos

### US-3 — Mathis (UX checklist manuel)

*Comme founder qui veut savoir si la webapp est utile, je veux parcourir toutes les routes principales avec ma propre navigation, prendre des screenshots, et noter ce qui marche/manque.*

**AC** :
- Checklist UX complète (template ci-dessous) couvrant :
  - Login / Logout
  - Dashboard / list clients
  - Détail client (audits, recos)
  - Création / édition (si scope MVP)
  - Erreurs handling (404, 403 RLS, network fail)
  - Mobile responsive
- 5+ screenshots desktop + mobile sauvés dans `deliverables/webapp_v28_validation_2026-05-XX/`
- Doc `WEBAPP_V28_UX_AUDIT.md` rédigé avec verdict per dimension

### US-4 — Mathis (feedback consultant)

*Comme founder qui valide la webapp avant d'investir backend, je veux qu'1 consultant Growth Society (genre Florian, Hugo, le boss CTO) utilise la webapp 30 min sur 1-2 clients test et me dise ce qui marche/manque.*

**AC** :
- 1 consultant ciblé identifié + dispo créneau 30 min
- Onboarding minimal donné (URL + credentials test ou signup)
- Session shadowée par Mathis OU async screen-recording Loom
- Feedback recueilli (verbatim ou template) sur :
  - "Was-tu fais ton job avec ça aujourd'hui ?" (verdict big picture)
  - 3 pain points concrets (manquant, broken, confus)
  - 3 wins (utile, claire, time saver)
- Doc `WEBAPP_V28_CONSULTANT_FEEDBACK.md` ajouté

### US-5 — Mathis (decision gate FastAPI)

*Comme founder qui rationalise les investissements, je veux à l'issue prendre une décision **structurée** ship/defer FastAPI backend deploy, basée sur les inputs des US-3 et US-4, pour ne pas refaire la conversation 2 mois plus tard.*

**AC** :
- Decision matrix complétée (template ci-dessous) :
  - Pain points qui requièrent backend Python : count
  - Pain points résolvables sans backend : count
  - Time-to-value backend deploy vs reward
  - Coût Browserless + Fly.io/Railway estimé
- Verdict explicit : `SHIP` (lance Epic 4 FastAPI deploy) OR `DEFER` (continue read-only N semaines de plus) OR `PIVOT` (refactor besoin sans FastAPI)
- Si SHIP → créer sub-PRD `fastapi-backend-deploy` via /ccpm
- Si DEFER → noter date de prochaine re-évaluation

## Functional Requirements

### FR-1 — Signup bootstrap (Mathis interactive, ~5 min)

1. Open https://growth-cro.vercel.app/login
2. Click "Sign up" link (ou route `/signup` si séparée)
3. Email + password (mémorise / 1Password)
4. Email de confirmation : check ta boîte → click link
5. Login successful → tu landes sur dashboard (peut-être vide, peut-être avec onboarding "create your organization")
6. **Si pas d'onboarding org auto** : via Supabase SQL Editor, run :
   ```sql
   -- Get your user id
   SELECT id, email FROM auth.users WHERE email = 'ton-email@growth-society.com';

   -- Replace YOUR_USER_ID below
   INSERT INTO public.organizations (slug, name, owner_id)
   VALUES ('growth-society', 'Growth Society', 'YOUR_USER_ID')
   RETURNING id;

   -- Replace YOUR_USER_ID + ORG_ID returned above
   INSERT INTO public.org_members (org_id, user_id, role)
   VALUES ('ORG_ID', 'YOUR_USER_ID', 'admin');
   ```

### FR-2 — Test data seed script

- Créer `scripts/seed_supabase_test_data.py` :
  - Lit `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` from `growthcro/config.py`
  - Push 2 clients fictifs via REST API (org_id = ton org)
  - Push 1 audit chacun + 5 recos chacun
  - Idempotent via `on_conflict` upsert
- Run : `python3 scripts/seed_supabase_test_data.py`
- Verify in Supabase Table Editor : 2 clients, 2 audits, 10 recos

### FR-3 — UX checklist

Template `deliverables/webapp_v28_validation_2026-05-XX/UX_CHECKLIST.md` :

```markdown
## Navigation

- [ ] Login form rend correctement (email + password fields visibles)
- [ ] Signup link présent et fonctionnel
- [ ] Confirmation email reçue dans ≤2 min
- [ ] Login successful redirect vers dashboard
- [ ] Logout via menu → redirect /login

## Dashboard

- [ ] Liste clients affiche les 2 clients seedés
- [ ] Click client → navigate vers détail
- [ ] Détail client affiche audits liés
- [ ] Détail audit affiche recos
- [ ] Empty state si pas de clients (clean UI, pas crash)

## Erreurs

- [ ] 404 sur route inexistante : page custom (pas Vercel default)
- [ ] 403 si tu essaies d'accéder à org étrangère (RLS bloque)
- [ ] Erreur network simulée (offline browser) : graceful

## Mobile

- [ ] Login responsive
- [ ] Dashboard responsive (touch targets ≥44px)
- [ ] Détail responsive

## Performance

- [ ] Page load < 2s sur connexion 4G (browser devtools throttling)
- [ ] Pas de layout shift visible
```

### FR-4 — Consultant feedback

Template `deliverables/webapp_v28_validation_2026-05-XX/CONSULTANT_FEEDBACK.md` :

```markdown
## Profil consultant testé
- Nom :
- Rôle :
- Familiarité Growth Society stack : 1-5
- Audits CRO faits cette année :

## Setup
- Méthode : signup direct OR Mathis pré-créé compte
- Durée session : 30 min
- Contexte : "Imagine que tu dois auditer Acme Corp et lire mes recos"

## Feedback verbatim
(quotes direct si possible)

## 3 pain points
1.
2.
3.

## 3 wins
1.
2.
3.

## Decision impact
- Ces pain points peuvent-ils être résolus SANS FastAPI backend ? (Y/N pour chaque)
- Quelles features manquantes seraient un dealbreaker pour utilisation quotidienne ?
```

### FR-5 — Decision matrix

Template `deliverables/webapp_v28_validation_2026-05-XX/FASTAPI_DECISION.md` :

```markdown
## Decision : SHIP / DEFER / PIVOT FastAPI backend deploy

## Inputs résumés

| Source | Pain points blocking | Pain points cosmetic |
|---|---:|---:|
| Mathis UX checklist | N | N |
| Consultant feedback | N | N |
| **Total blocking** | **N** | |

## Pain points blocking — classifiés

| Pain point | Backend Python required ? | Workaround read-only ? |
|---|---|---|
| ... | Y/N | Y/N |

## Effort vs Reward

| Option | Effort | Reward |
|---|---|---|
| SHIP FastAPI | ~1j deploy + ~$10/mo Browserless + Fly/Railway | Trigger audits depuis UI |
| DEFER 2 semaines | 0 | Plus de data UX avant invest |
| PIVOT (refactor besoin) | varie | Possiblement éviter backend si Supabase Edge Functions suffisent |

## Verdict
- [ ] SHIP — créer sub-PRD `fastapi-backend-deploy` ce jour
- [ ] DEFER — re-évaluer le YYYY-MM-DD
- [ ] PIVOT — créer sub-PRD `<alternative>`

## Justification (3 phrases)
```

## Non-Functional Requirements

### Doctrine immuables (héritées)
- V26.AF : prompt persona_narrator gone (vacuous)
- V3.2.1 + V3.3 : doctrine intacte
- Code doctrine : tout nouveau script ≤200 LOC, mono-concern
- Pas de Notion auto-modify
- Pas de credentials en clair dans commit (cf section sécurité ci-dessous)

### Sécurité
- **Service role key Supabase rotation** : Mathis a partagé le service_role JWT dans le chat aujourd'hui. À rotater dans les 24h via Supabase Dashboard → Settings → API → Reset service_role key. Update Vercel env var après rotation.
- **Email confirmation** : maintenir activé sur Supabase prod (anti-spam). Désactiver SEULEMENT si tests blockés.

### Performance
- Webapp page load < 2s sur 4G (Vercel CDN + Next.js streaming)
- Supabase REST < 100ms (EU region, même datacenter que future Mathis France)

## Success Criteria

- [ ] US-1 done : Mathis signed up, org bootstrapped, login successful
- [ ] US-2 done : test data visible dans webapp
- [ ] US-3 done : UX checklist remplie, 5+ screenshots
- [ ] US-4 done : 1 consultant testé, feedback documented
- [ ] US-5 done : decision matrix complétée, verdict explicite
- [ ] Service role key Supabase rotaté
- [ ] Master PRD updated avec verdict (ship/defer FastAPI)

## Constraints & Assumptions

### Constraints
- Pas de modif doctrine V3.2.1/V3.3
- Pas de Notion auto-modify
- Pas de génération Sonnet
- Webapp prod = read-only pendant ce sprint (pas de mutation depuis UI)

### Assumptions
- Le `/login` Supabase Auth UI rend bien côté client (Next.js SSR + hydration)
- Au moins 1 consultant Growth Society dispo 30 min cette/semaine prochaine
- Le seed script peut utiliser `growthcro/config.py` pour lire env vars

## Out of Scope

- **Trigger audits depuis UI** → Epic 4 FastAPI deploy (sub-PRD futur si decision = SHIP)
- **Live capture/scoring** → Epic 4
- **Browserless integration** → Epic 4
- **Modifs webapp shell code** : seulement bugs critiques découverts pendant validation. Refactor UX = sprint séparé.
- **Multi-org switching** : 1 seule org "Growth Society" pour ce sprint
- **OAuth providers** (Google/GitHub login) : email/password suffit pour MVP

## Dependencies

### Externes
- **Mathis time** : ~2h signup + seed + UX checklist
- **1 consultant Growth Society** : 30 min testing
- Optionnel : 1 boss / CTO 15 min pour discuss decision matrix

### Internes
- main HEAD post-deploy V28 partial (commits today)
- Vercel project `growth-cro` live
- Supabase project `xyazvwwjckhdmxnohadc` migrated
- `growthcro/config.py` (env reads pour seed script)

### Sequencing
- US-1 → US-2 (besoin org pour seed FK)
- US-2 → US-3 (besoin data pour tester display)
- US-3 || US-4 (peuvent être paralléles)
- US-5 dépend de {US-3, US-4}

## Programme — Critical Path

```
SEMAINE 1
  US-1 Signup + org bootstrap (~5 min Mathis, 1 SQL exec)
       │
  US-2 Seed script + push 2 clients (~1h dev Mathis OR autonome)
       │
  US-3 UX checklist + screenshots (~1h Mathis solo)

SEMAINE 1 ou 2
  US-4 Consultant feedback (30 min interview + 30 min synthese)

SEMAINE 2
  US-5 Decision matrix + verdict (15 min)
```

**Critical path** : ~3h Mathis cumul, étalable sur 1-2 semaines.

## Next steps post-completion

### Si verdict SHIP
- Créer sub-PRD `fastapi-backend-deploy` via /ccpm
- Decompose : Railway/Fly.io setup, Dockerfile push, env vars Browserless, healthcheck, integrate webapp button "Trigger audit"
- ETA : ~1j

### Si verdict DEFER
- Documenter date prochaine re-évaluation (+2 semaines, +1 mois)
- Continue à pousser data via Python local (boucle Mathis CLI → Supabase → Webapp)
- Note dans master PRD post-stratosphere-roadmap

### Si verdict PIVOT
- Évaluer Supabase Edge Functions vs FastAPI (lighter weight)
- Évaluer si certaines features peuvent être faites côté webapp directement (Next.js Server Actions)
- Sub-PRD adapté à la nouvelle direction
