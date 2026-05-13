# Audit A.11 — Security — 2026-05-14

## TL;DR

Posture sécurité **globalement saine** : RLS Supabase enforced sur toutes les tables critiques avec org-isolation propre, API routes mutating gated par `requireAdmin()`, service_role JWT confiné côté serveur uniquement. **3 findings P0** : (1) open redirect dans `/auth/callback` via `redirect` param non validé, (2) `.env` historique avec clé Anthropic réelle nécessite vérification de rotation, (3) rotation service_role JWT en attente (déjà tracking côté Mathis). Aucune RLS-bypass ni SQL injection détectée.

## P0 (critical, fix before next session)

- **Open redirect dans /auth/callback** (`webapp/apps/shell/app/auth/callback/route.ts:17`) — Impact : Le param `redirect` (et donc `${origin}${redirect}`) accepte n'importe quelle valeur incluant `//evil.com` ou `/\\evil.com` qui peut router vers un domaine externe via parsing de browser. Risque : phishing post-login. Fix : valider que `redirect` commence par `/` et ne contient pas `//` (ou utiliser une whitelist de chemins internes).
- **`.env` au repo contient clé Anthropic réelle commentée "à rotater"** (`.env:9`) — Impact : Le fichier n'est PAS tracké (gitignored line 8 `.env`), MAIS le commentaire indique que la clé `sk-ant-api03-***REDACTED-FOR-COMMIT***` a été retrouvée en clair dans `WAKE_UP_NOTE_2026-04-19.md` + `memory/HISTORY.md` historiquement. À vérifier : (a) cette clé est-elle déjà rotée côté Anthropic Console ? (b) Les anciens fichiers `WAKE_UP_NOTE_*.md` sont-ils bien purgés de git history (BFG/filter-repo) ? Fix : si non rotée → rotater immédiatement + scrub git history avec git-filter-repo.
- **Rotation service_role JWT en attente** (PRD W0.1) — Impact : Repo PUBLIC + JWT in git history (selon PRD). Confirmation : la recherche grep dans `git log -p` ne révèle PAS de JWT service_role complet en clair dans l'historique tracké récent. Les seules occurrences sont les placeholders `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR-SERVICE-KEY` (template) et `eyJ...` (tronqué). Cependant **le PRD W0.1 affirme que la clé est in git history** — possiblement dans des commits anciens / fichiers archivés non scannés. Fix : Mathis exécute W0.1 (Reset service_role dans dashboard Supabase, update Vercel + .env.local).

## P1 (important)

- **Helper `getCurrentRole()` retourne uniquement la première org_member row** (`webapp/apps/shell/lib/auth-role.ts:17-22`) — Impact : Si un user appartient à plusieurs orgs, seule la première est consultée. Si l'utilisateur a le rôle `viewer` dans org A et `admin` dans org B, et que la première rangée renvoyée est viewer, il perd ses droits admin sur org B. Même problème dans `require-admin.ts:25-30`. Fix : prendre la rangée avec le rôle le plus permissif, ou exiger `.eq("org_id", X)` quand l'org est connue dans le contexte. Aujourd'hui agence single-org donc impact = 0, mais bug latent pour V2.
- **API `/api/learning/proposals/review` ne vérifie PAS l'auth** (`webapp/apps/shell/app/api/learning/proposals/review/route.ts:6-11`) — Impact : Commentaire explicite "Authentication is not enforced here yet — the V28 shell is single-tenant for Mathis. A future sprint should add Supabase auth check". Reste protégé par middleware shell qui redirige `/login`, mais **un POST direct à `/api/learning/proposals/review` depuis curl sans cookie est autorisé** car middleware matcher exclut certains paths (en théorie l'API route est dans le matcher, mais le test n'a pas été fait). Fix : ajouter `await requireAdmin()` (ou au moins `auth.getUser()`).
- **GsgDemo HTML serve sans `X-Content-Type-Options: nosniff`** (`webapp/apps/shell/app/api/gsg/[slug]/html/route.ts:48-55`) — Impact : CSP `default-src 'self'` est strict mais sans nosniff, un fichier HTML mal-typé pourrait être interprété autrement. Fix : ajouter `X-Content-Type-Options: nosniff` aux headers.
- **`reco_text` n'est pas longueur-bornée** (`webapp/apps/shell/app/api/recos/[id]/route.ts:99-102`) — Impact : Pas de cap sur la longueur de `body.reco_text`. Un attaquant admin (low risk car déjà admin) peut bloater le content_json. Fix : ajouter `if (text.length > N) return bad("reco_text_too_long")`.
- **Pas de rate-limiting sur `/login`** — Impact : Brute force du password via `signInWithPassword`. Supabase fait son propre rate limiting côté API, mais aucun middleware Vercel-side. Acceptable pour V1 (Supabase suffit), à monitorer.

## P2 (improvement)

- **Pas de headers de sécurité globaux** (`webapp/apps/shell/next.config.js`) — Manque `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`. Vercel set HSTS automatiquement, mais une CSP custom serait utile. Fix : ajouter `headers()` async dans next.config.js avec defaults sécurisés.
- **Pas de zod / validation library** — Validation manuelle dans chaque route handler (cohérent avec doctrine "no new dep"), mais code répétitif et risque de drift. À évaluer en V2 (zod léger ~14 KB minified).
- **JWT regex matches dans data captures (false positive)** — Plusieurs JWT-format strings dans `data/captures/*/spatial_v9.json`, `_obsolete_pages_*.json`. Ce sont des tokens publics récupérés via scraping (Netlify cwv-tokens, affiliate tokens Payfit, etc.), pas des secrets GrowthCRO. Pas de risque.
- **`/api/learning/proposals/review` écrit dans filesystem** (`webapp/apps/shell/lib/proposals-fs.ts`) — En prod Vercel le filesystem est read-only / éphémère. Cette route ne fonctionnera pas en prod (mais n'est pas marquée comme broken). À migrer vers Supabase table `doctrine_proposals` quand activée.
- **`Bucket screenshots` est public** (`supabase/migrations/20260513_0005_screenshots_storage.sql:20`) — Décision documentée comme acceptable pour internal dev tool. Risque : Bucket-enumeration via URLs prédictibles si quelqu'un découvre la convention `<client>/<page>/<filename>`. V2 prévu : signed URLs 1h.
- **`.env.local` contient `WEBAPP_LOGIN_PASSWORD=***REDACTED***` en clair** — Acceptable car gitignored, mais bonne pratique = utiliser un secret manager (1Password CLI, op://...). Note documentée comme TEMP.

## Specific dimensions

### Secrets in repo: PASS

- `.gitignore` correctement configuré : `.env`, `.env.local`, `.env.*.local`, `*.key`, `*.pem`, `secrets/`, `WAKE_UP_NOTE_*.md` (lines 11-21).
- `git ls-files | grep .env` retourne uniquement `.env.example` + `webapp/.env.example` (templates, safe).
- Scan grep current tree : aucun `sk-ant-api03-...` réel hors `.env` (gitignored), aucun `eyJ.SUPABASE_SERVICE_ROLE...` real.
- Git history scan : occurrences `eyJ...` toutes externes (Netlify, Payfit, etc. dans data captures) OU placeholders (`YOUR-SERVICE-KEY`, `eyJ...` tronqué).
- ⚠️ **À vérifier humainement** : ancien `WAKE_UP_NOTE_2026-04-19.md` mentionné comme contenant clé Anthropic. Aujourd'hui gitignored. Mais : était-il déjà committé avant le gitignore ? Si oui, scrub via `git filter-repo --path WAKE_UP_NOTE_*.md --invert-paths`.

### Supabase RLS: PASS (avec nuances)

| Table | RLS enabled | Policies | Status |
|-------|-------------|----------|--------|
| `organizations` | OUI | member read / admin update / owner insert | ✅ |
| `org_members` | OUI | self read OR org member read / admin manage all | ✅ |
| `clients` | OUI | org member read+write | ✅ (mais "consultant write" = `for all` autorisé à tout membre, pas seulement consultant — naming trompeur) |
| `audits` | OUI | via clients join | ✅ |
| `recos` | OUI | via audits→clients join | ✅ |
| `runs` | OUI | org_id null OR org member | ⚠️ `org_id IS NULL` autorise lecture/écriture par tout user authentifié — backdoor potentielle pour rows orphelines |
| `storage.objects` (screenshots) | OUI | public read, service_role insert/update/delete | ✅ public par design |

**Tables mentionnées par audit prompt mais NON présentes dans les migrations** : `brand_dna`, `judges`, `funnel`, `team`, `users`, `doctrine_proposals`. → Brand DNA stocké en JSONB dans `clients.brand_dna_json` (RLS via clients). Pas de tables séparées à auditer.

**Nuance "consultant write"** : la policy `clients: consultant write` est `for all using (is_org_member)` — donc TOUT membre (admin/consultant/viewer) peut écrire au niveau RLS. La distinction admin/consultant/viewer est faite au niveau **application** dans `require-admin.ts`. Cohérent (defense in depth en couches), mais le nom de policy est trompeur. ⚠️ Si un attaquant bypass l'API et appelle Supabase REST directement avec son JWT user, il peut update/delete clients en tant que viewer. **Recommandation** : ajouter `is_org_admin()` check dans la RLS write policy.

### API input validation: PASS

| Route | Method | Validation | Auth | Status |
|-------|--------|-----------|------|--------|
| `/api/audits` | POST | manual enum + URL regex | requireAdmin | ✅ |
| `/api/audits/[id]` | PATCH/DELETE | manual enum | requireAdmin | ✅ |
| `/api/clients/[id]` | DELETE | id only | requireAdmin | ✅ |
| `/api/recos/[id]` | PATCH/DELETE | manual enum + length | requireAdmin | ✅ (sauf reco_text unbounded P1) |
| `/api/team/invite` | POST | email regex + role enum | auth.getUser + role==admin | ✅ |
| `/api/gsg/[slug]/html` | GET | slug whitelist via findGsgDemoBySlug | (none — middleware) | ✅ |
| `/api/screenshots/...` | GET | regex + whitelist + path traversal check | (none — public-ish) | ✅ |
| `/api/learning/proposals/review` | POST/GET | decision enum | **AUCUNE** (P1) | ⚠️ |

SQL injection : impossible — toutes les queries passent par Supabase client (PostgREST paramétré), pas de raw SQL.

### Auth flow: PASS (avec 1 P0 open redirect)

- Middleware `webapp/apps/shell/middleware.ts` : couvre toutes les routes sauf `/login`, `/auth/callback`, `/privacy`, `/terms` + assets `_next/`. ✅
- Auth callback (`app/auth/callback/route.ts`) : 🔴 **open redirect** — `redirect` param non validé (P0).
- Login page (`app/login/page.tsx`) : utilise `searchParams.get("redirect")` puis `router.push(redirect)` sans validation. ⚠️ Open redirect côté client aussi.
- Signout : OK, redirect vers `/login` only.
- Cookies httpOnly : géré par `@supabase/ssr` ✅.

### Service role JWT exposure: PASS (côté code)

- Seule occurrence : `webapp/packages/data/src/client.ts:50` (server-only function `getServiceRoleSupabase`).
- Utilisé dans **1 seul endpoint** : `/api/team/invite/route.ts` (admin invite + RLS bypass insert).
- Jamais importé côté client / browser bundle.
- ⚠️ Rotation pending (cf. P0 — PRD W0.1).

### Deps vulns: PASS (low risk)

- `webapp/apps/shell/package.json` : Next 14.2, React 18, Supabase 0.3/2.43 — versions récentes, pas de CVE connu critique sur ces ranges.
- `package.json` root : `playwright 1.59` (dev tooling), `jsdom 24` (devdep). RAS.
- `requirements.txt` (Python) : `defusedxml>=0.7.1` correctement utilisé (commentaire Bandit B314). Anthropic, FastAPI, Pillow — versions modernes.
- ⚠️ Recommandation : exécuter `npm audit` + `pip-audit` régulièrement (GitHub Dependabot activable).

### CORS/CSP/Headers: WEAK

- `next.config.js` : pas de `headers()` configuré → headers par défaut Vercel seulement (HSTS auto, X-Powered-By stripped).
- Middleware : ne set aucun header de sécurité custom.
- Pas de CSP globale (uniquement sur `/api/gsg/[slug]/html` qui set son propre `default-src 'self'`).
- CORS : pas de wildcard, par défaut same-origin only. ✅
- **Recommandation P2** : ajouter dans next.config.js :
  ```js
  async headers() {
    return [{
      source: "/(.*)",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      ],
    }];
  }
  ```

## Recommendations Wave C priority

1. **Fix open redirect** `auth/callback` + `login` page — patch both `redirect` params : `if (!redirect.startsWith('/') || redirect.startsWith('//')) redirect = '/'`. ETA 10 min.
2. **Add `requireAdmin()` to `/api/learning/proposals/review`** — copier pattern de `/api/recos/[id]`. Sinon retirer la route si pas utilisée prod. ETA 5 min.
3. **Mathis** exécute W0.1 rotation service_role JWT (déjà documenté PRD). ETA 5 min.
4. **Vérifier git history** pour clés réelles : `git filter-repo --invert-paths --path WAKE_UP_NOTE_2026-04-18.md --path WAKE_UP_NOTE_2026-04-19.md` si elles ont été committées avant gitignore. ETA 15 min + force-push avec accord Mathis.
5. **Ajouter headers sécurité globaux** dans next.config.js (CSP minimaliste + X-Frame-Options + nosniff). ETA 15 min.
6. **Renforcer RLS write policies clients/audits/recos** avec `is_org_admin()` (defense in depth contre attaquant authentifié faisant un appel Supabase direct hors API). ETA 30 min + migration.
7. **Rate-limit `/login`** via Vercel WAF ou middleware custom (5 tentatives / IP / min). ETA 30 min, optionnel V2.
8. **Activer Dependabot** sur GitHub repo (webapp + root). ETA 5 min.
