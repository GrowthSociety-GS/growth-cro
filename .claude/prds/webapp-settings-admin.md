---
name: webapp-settings-admin
description: Wire la route /settings avec 4 onglets minimaux (Account, API, Team, Usage) pour permettre password change, view API keys, manage org members, voir usage basic.
status: active
created: 2026-05-13T09:36:29Z
parent_prd: webapp-full-buildout
wave: B-extended
fr_index: FR-5
---

# PRD: webapp-settings-admin

> Sub-PRD du master [`webapp-full-buildout`](webapp-full-buildout.md) — FR-5 (post-FR-1, S effort).
>
> Wirer `/settings` avec 4 onglets minimaux pour admin compte. Aucune nouvelle table Supabase, réutilisation de `auth.users`, `org_members`, `clients`. Focus : UX form basique + Supabase Auth UI password change.

## Executive Summary

Sans `/settings`, Mathis (et futurs consultants invités) ne peut pas :
- Changer son password depuis la webapp (doit aller sur Supabase Dashboard)
- Voir ses API keys de session
- Inviter un membre dans son org Growth Society
- Voir usage basic (clients tracked, audits this month, recos created)

FR-5 wire `/settings` avec 4 onglets minimaux (UX standard SaaS settings) :
- **Account** : password change + email display + session info
- **API** : list API keys (read-only, scaffold pour V2 keys management)
- **Team** : invite member email → Supabase magic link admin invite
- **Usage** : 4 KPI cards (clients, audits, recos, runs this month)

**Effort** : S, 0.5j wall-clock · ~1-2h agent background.
**Coût API** : $0.
**Bloque** : aucun (parallel-safe avec FR-2 + FR-3).

## Problem Statement

### Pourquoi maintenant

1. **Pwd lost recurrent** : Mathis a déjà perdu son pwd 2x (signal du sub-PRD). Sans UI in-app, doit toujours aller Supabase Dashboard. UX friction inacceptable pour scale.
2. **Magic link rate-limited** : Supabase free tier = 4 magic links/h. Sans password fallback solid, lockout possible.
3. **Team invite manuel** : consultants Growth Society inviter doit passer par admin API curl (cf seed_supabase_test_data.py pattern). Pas viable.
4. **Usage visibility** : Mathis veut voir "combien de clients je track, combien d'audits ce mois" pour usage personnel + future billing decision.

### Ce que FR-5 apporte

- 4 onglets settings réseau dans la webapp shell
- Password change in-app (no Supabase Dashboard detour)
- Team invite UI (1 form, 1 click)
- Usage KPIs aggregated cross-clients de l'org
- Foundation pour V2 (API keys management, billing tier, role-based access)

## User Stories

### US-1 — Mathis (change password)
*Comme founder qui perd régulièrement son pwd, je veux `/settings#account` qui me permet de change pwd en 1 form + auto-update Supabase Auth.*

**Acceptance Criteria** :
- ✓ `/settings` HTTP 200, tab `Account` actif par défaut
- ✓ Form fields : current password, new password, confirm new password
- ✓ Submit → Supabase Auth `updateUser({ password })` via client
- ✓ Success message + auto-redirect `/` après 2s
- ✓ Error display si current password wrong OR new password < 8 chars
- ✓ Affiche : email connecté (read-only) + last sign in date

### US-2 — Mathis (manage team)
*Comme founder qui veut inviter 2-3 consultants Growth Society, je veux `/settings#team` qui me permet d'inviter par email avec role.*

**Acceptance Criteria** :
- ✓ Tab `Team` : table des org_members actuels (email, role, joined_at)
- ✓ Form "Invite member" : email input + role dropdown (admin/member)
- ✓ Submit → API route `/api/team/invite` qui appelle Supabase Auth admin `inviteUserByEmail()` + insert org_member row
- ✓ Confirmation toast post-invite
- ✓ Error handling : email déjà membre, email invalide

### US-3 — Mathis (view usage)
*Comme founder qui veut quantifier son usage, je veux `/settings#usage` qui montre 4 KPIs : clients tracked, audits all-time, recos all-time, runs this month.*

**Acceptance Criteria** :
- ✓ Tab `Usage` : 4 KpiCard `@growthcro/ui`
- ✓ Clients : count from `clients` table where org_id = current
- ✓ Audits : count from `audits` table joined `clients`
- ✓ Recos : count from `recos` table joined `audits`
- ✓ Runs this month : count from `runs` table where started_at >= first day of month

### US-4 — Mathis (view API keys placeholder)
*Comme founder qui veut éventuellement intégrer la webapp à des automations, je veux `/settings#api` qui montre les API keys disponibles (scaffold V1, real V2).*

**Acceptance Criteria** :
- ✓ Tab `API` : show "API Keys management — V2 deferred" placeholder
- ✓ Affiche : Supabase URL (public-safe), anon key (public-safe), project ref
- ✓ Hidden : service_role key (never show client-side)
- ✓ Copy-to-clipboard buttons pour URL + anon key

## Functional Requirements

### Task Breakdown (3 tasks file-disjoint)

#### T001 — Page `/settings/page.tsx` + tabs layout
**Effort** : S, 30-45 min
**Files** :
- `webapp/apps/shell/app/settings/page.tsx` (NEW)
- `webapp/apps/shell/components/settings/SettingsTabs.tsx` (NEW client component)
- `webapp/apps/shell/components/settings/{AccountTab,TeamTab,UsageTab,ApiTab}.tsx` (4 NEW components)
**Cible** :
- Server Component page : fetch current user + org_members + counts
- Client Component `SettingsTabs` : 4 tabs avec URL hash `#account`, `#team`, `#usage`, `#api`
- Default tab : `#account`

**Acceptance** :
- [ ] `/settings` 200 + redirect to `/settings#account` si pas de hash
- [ ] Tab switch sans re-render full page (client component)
- [ ] URL hash persistent

#### T002 — AccountTab (password change) + TeamTab (invite)
**Effort** : S-M, 45-60 min
**Files** :
- `webapp/apps/shell/components/settings/AccountTab.tsx` (form + submit)
- `webapp/apps/shell/components/settings/TeamTab.tsx` (table + invite form)
- `webapp/apps/shell/app/api/team/invite/route.ts` (NEW POST handler)
**Data** :
- Account : Supabase Auth `updateUser()` client-side
- Team : Supabase admin API server-side (service_role)
**Cible** :
- AccountTab : 3-input form + submit handler with error/success state
- TeamTab : list org_members + invite form
- API route `/api/team/invite` : validate email + admin `inviteUserByEmail` + insert org_members row

**Acceptance** :
- [ ] Password change : form valid → Supabase updates → success toast
- [ ] Team invite : form valid → invite email sent → org_member inserted → table refreshes

#### T003 — UsageTab (KPIs) + ApiTab (placeholder)
**Effort** : XS-S, 30-45 min
**Files** :
- `webapp/apps/shell/components/settings/UsageTab.tsx` (4 KpiCard)
- `webapp/apps/shell/components/settings/ApiTab.tsx` (read-only display)
**Data** :
- Usage : Supabase queries `count()` 4 tables (server-side via Server Component)
- API : public env vars only
**Cible** :
- UsageTab : 4 KpiCard `@growthcro/ui` avec count + label + last update
- ApiTab : 2-3 read-only cards (Supabase URL, anon key, project ref) + Copy buttons

**Acceptance** :
- [ ] UsageTab affiche 4 counts corrects (3 clients seed → "3 clients tracked")
- [ ] ApiTab affiche public-safe metadata, jamais service_role
- [ ] Copy buttons fonctionnent (navigator.clipboard.writeText)

## Non-Functional Requirements

### Doctrine
- Mono-concern : 1 tab = 1 component, separate concerns
- ≤ 800 LOC par fichier
- Pas de service_role exposé côté client (T002 invite API doit être server-only Route Handler)
- Anti-pattern #11 : pas de basename collision (composants nommés `AccountTab` etc., dans `components/settings/`)

### Sécurité
- **Critical** : `/api/team/invite` uses service_role server-side ONLY. Never expose JWT to client.
- Validate email format server-side
- Rate-limit invite (max 10/h per user, via Supabase Auth built-in)
- CSRF protection : Next.js default (same-origin only for POST)

### Performance
- Page load < 2s
- Tab switch instant (client component, no fetch)
- Usage counts fetched server-side via parallel `Promise.all`

### Documentation
- MANIFEST §12 changelog
- Architecture map regen

## Success Criteria

### Routes
- [ ] `/settings` HTTP 200, default tab Account
- [ ] `/settings#team` URL hash works
- [ ] `/api/team/invite` POST endpoint works (200 success, 4xx error cases)

### Gates
- [ ] Lint, parity, schemas ✓
- [ ] Typecheck + build exit 0

### Runtime
- [ ] Password change flow works end-to-end (test : change pwd Mathis to memorable value)
- [ ] Team invite : send invite to test email → email arrives → invitee can login
- [ ] Usage tab : 3 clients + 6 audits + 30 recos counts visibles
- [ ] ApiTab : Supabase URL + anon key visible, service_role NEVER visible

### Doctrine
- [ ] 0 régression
- [ ] 1 commit isolé
- [ ] MANIFEST §12 commit séparé

## Constraints & Assumptions

### Constraints
- **Pas de role-based access full** : V1 = admin can do all. V2 = role per-feature.
- **Pas de delete member** : V1 only invite. Delete = V2.
- **Pas de billing tier** : usage display only, no upgrade button.
- **Pas de SMTP custom config UI** : Mathis doit aller Supabase Dashboard pour ça.

### Assumptions
- Supabase service_role JWT accessible côté server (env var `SUPABASE_SERVICE_ROLE_KEY` valid)
- Mathis a un email valide accessible pour test invite flow
- `@growthcro/data` queries `getCurrentUser()`, `listOrgMembers()`, `countClients/Audits/Recos/Runs()` existent OU créées dans ce sub-PRD si manquantes
- Supabase Auth email magic link OR password set enabled (currently password enabled cf FR-1)

## Out of Scope

### Hors scope V1
- **Multi-org switching** : 1 user = 1 org pour V1
- **Role-based feature gates** : admin/member symbolic only
- **Member delete** : V2
- **Billing/Pricing tier UI** : V2
- **SMTP custom config** : Supabase Dashboard
- **2FA/MFA** : V2
- **Session management** (list active sessions, revoke) : V2
- **Audit log** (who did what) : V2
- **API key creation/rotation** : V2

## Dependencies

### Externes
- Mathis ~15 min validation (test password change + 1 invite)
- Supabase Auth admin API (active, service_role available)

### Internes
- **FR-1 SHIPPED** : shell deployed, auth working
- `@growthcro/data` queries (verify count* available, else create in this sprint)
- `@growthcro/ui` KpiCard component
- `@supabase/ssr` already installed

### Sequencing
- T001 (page + tabs) → T002 + T003 parallel (each implements own tab content)
- Internal sequencing OK with 1 agent worktree
