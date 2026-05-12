# MCPs Production — Install Procedure (Task #27)

**Date** : 2026-05-12
**Task** : #27 du programme `hardening-and-skills-uplift`, PRD FR-3
**Pré-requis** : Task #26 mergée (Context7 MCP setup documenté, BLUEPRINT.md section 4bis introduite)
**Public** : Mathis (exécution manuelle — l'agent Claude Code ne dispose pas de la CLI `claude` dans son sandbox, donc ne peut pas exécuter `claude mcp add` lui-même)
**Durée totale estimée** : 4 OAuth flows × ~5min = **~20min Mathis**

---

## 0. Pré-requis machine

```bash
# Vérifier que la CLI Claude Code est dispo et à jour
which claude        # /opt/homebrew/bin/claude (macOS) ou équivalent
claude --version    # >= 0.x (vérifier dernière version supportant `mcp add --transport http`)

# Lister les MCPs déjà installés
claude mcp list
# Devrait afficher au minimum `context7` (post Task #26 si Mathis l'a déjà ajouté).
```

**Important** : tous les MCPs ci-dessous sont **server-level** (config Claude Code globale, hors compte des 8 skills/session). Cf BLUEPRINT.md §4bis pour la doctrine MCPs ≠ Skills.

---

## 1. Supabase MCP officiel (ICE 810)

### 1.1 Pré-requis spécifique
- **CRITICAL** : avoir un projet Supabase **dev/staging** dédié. Si pas existant → en créer un avant l'install (~5min via dashboard Supabase). **NE PAS** utiliser le projet prod (cf §1.5 anti-pattern).
- Compte Supabase actif relié à l'organisation Growth Society.

### 1.2 Install command

```bash
claude mcp add --transport http supabase https://mcp.supabase.com/mcp
```

### 1.3 OAuth flow (~3min)
1. La commande ouvre une URL OAuth Supabase dans le navigateur.
2. Mathis se connecte avec son compte Supabase.
3. Page de consent : sélectionner **l'organisation Growth Society** + **projet dev/staging UNIQUEMENT** (pas le prod). Scopes demandés (typique) :
   - `read:projects` · `write:projects` · `read:schemas` · `write:schemas` · `execute:sql` · `manage:branches` · `manage:edge-functions`
4. Cliquer "Authorize". Le navigateur affiche une page de succès et redirige vers `localhost`.
5. Retour terminal : `MCP supabase added successfully`.

### 1.4 Transport & config
- **Transport** : HTTP (remote MCP server hébergé par Supabase à `https://mcp.supabase.com/mcp`).
- **Auth** : OAuth 2.0 + token PAT stocké chiffré dans `~/.claude/mcp/credentials.json`.
- **Environnement requis** : projet Supabase **dev** (URL `https://<dev-ref>.supabase.co`).

### 1.5 ANTI-PATTERN CRITICAL — DEV ONLY, NEVER PRODUCTION

> **Documenté explicitement par Supabase** : https://supabase.com/blog/supabase-is-now-an-official-claude-connector
>
> Si Claude exécute `DROP TABLE` / `DELETE WHERE …` / `ALTER TABLE` via le MCP, ça doit toucher **uniquement** la base dev. Aucune session Claude Code ne doit jamais avoir le projet prod sélectionné dans le scope OAuth Supabase.

**Mesures de défense en profondeur** :
- Sélectionner **uniquement le projet dev** lors du consent OAuth (étape 3).
- Si plus tard Mathis veut basculer vers un autre projet dev → révoquer et ré-installer (cf §1.7).
- Ne **jamais** lier le projet prod V28 au MCP. Pour des opérations prod → SQL manuel via dashboard Supabase + review humain.

### 1.6 Smoke test

Dans une session Claude Code post-install :
> "Liste les schemas du projet Supabase dev connecté."

OU directement via tool call :
```
mcp__supabase__list_schemas
```

Attendu : liste des schemas (`public`, `auth`, `storage`, `extensions`, etc.). Si réponse vide ou erreur OAuth → vérifier `claude mcp list` puis `claude mcp restart supabase`.

Alternative smoke test : demander à Claude `SELECT 1` (devrait retourner `[{"?column?": 1}]`).

### 1.7 Revoke / re-install

```bash
# Remove MCP
claude mcp remove supabase

# Côté Supabase dashboard : Settings > Access Tokens > revoke le PAT généré par Claude Code
# Puis re-installer : claude mcp add --transport http supabase https://mcp.supabase.com/mcp
```

---

## 2. Sentry MCP (ICE 576)

### 2.1 Pré-requis
- Compte Sentry actif Growth Society (organisation Sentry).
- Projet Sentry dev/staging créé (peut être vide initialement, le MCP fonctionne quand même).

### 2.2 Install command

```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

### 2.3 OAuth flow (~3min)
1. URL OAuth Sentry s'ouvre.
2. Connexion compte Sentry Mathis.
3. Consent page — scopes demandés :
   - `org:read` · `project:read` · `event:read` · `member:read`
   - Optionnel selon usage : `event:write` (NON recommandé pour MCP — keep read-only).
4. Sélectionner l'organisation Growth Society + le(s) projet(s) à exposer (peut être tous read-only).
5. Authorize → redirect → terminal `MCP sentry added successfully`.

### 2.4 Transport & config
- **Transport** : HTTP + SSE (Server-Sent Events pour streaming d'issues).
- **Auth** : OAuth 2.0.
- **Environnement requis** : aucun spécifique (le MCP filtre automatiquement par org/projets autorisés à l'OAuth).

### 2.5 Smoke test

```
mcp__sentry__list_issues  (ou équivalent)
```

OU dans Claude Code :
> "Liste les 5 dernières issues Sentry du projet dev."

Attendu : liste des issues récentes (peut être vide si projet propre, dans ce cas réponse `[]` valide).

### 2.6 Revoke / re-install

```bash
claude mcp remove sentry
# Sentry dashboard : Settings > Auth Tokens > révoquer le token
# Re-install : claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

---

## 3. Meta Ads MCP officiel (ICE 640)

### 3.1 Pré-requis
- Compte Meta Business Suite actif (Growth Society).
- Au moins 1 Ad Account accessible (idéalement un compte test agence, ou un compte client avec autorisation explicite).
- **Optionnel** : Mathis peut créer un compte test Meta dédié pour les sessions Claude Code (pour ne pas exposer les données clients en live).

### 3.2 Install command

```bash
claude mcp add --transport http meta-ads https://mcp.facebook.com/ads
```

### 3.3 OAuth flow (~5min — plus long car Meta Business)
1. URL OAuth Meta s'ouvre (Facebook login).
2. Connexion Meta Business Mathis.
3. Page de consent Meta Business — scopes demandés (typique) :
   - `ads_read` · `ads_management` (lecture campagnes/audiences/creatives)
   - `business_management` (lecture structure Business Manager)
   - `pages_read_engagement` (optionnel si on veut accès Pages)
4. **Sélection critique** : Meta affiche la liste des **Ad Accounts** disponibles. Cocher uniquement le(s) compte(s) test agence + clients autorisés. **NE PAS** tout cocher par défaut.
5. Authorize → redirect → terminal `MCP meta-ads added successfully`.

### 3.4 Transport & config
- **Transport** : HTTP + OAuth Meta long-lived token (60 jours par défaut, refresh auto via MCP).
- **Auth** : OAuth 2.0 Meta Business.
- **29 tools exposés** (cf docs Meta) : campaigns, ad sets, ads, audiences, creatives, insights, Pixel/CAPI diagnostics.

### 3.5 Smoke test

```
mcp__meta_ads__list_ad_accounts
```

OU :
> "Liste les Ad Accounts Meta connectés."

Attendu : liste des accounts cochés au step 3.4 (au moins 1). Si vide → vérifier scope OAuth + ad account permissions côté Meta Business.

### 3.6 Revoke / re-install

```bash
claude mcp remove meta-ads
# Meta Business : Business Settings > Integrations > Claude Code MCP > Remove
# OU directement Facebook : Account Center > Apps and websites > Claude Code > Remove
# Re-install : claude mcp add --transport http meta-ads https://mcp.facebook.com/ads
```

---

## 4. Shopify MCP (ICE 504)

### 4.1 Pré-requis
- Compte Shopify Partners OU accès à un Admin shop Shopify (dev store recommandé).
- **Optionnel** : si Mathis n'a pas accès à un compte test live au moment de l'install → documenter `pending live shop` dans stream-A.md. Le MCP peut être installé en mode "no shop connected" et activé plus tard.

### 4.2 Install command

```bash
# Voie 1 (Shopify CLI plugin, recommandée si Shopify CLI installé) :
claude mcp add shopify

# Voie 2 (fallback HTTP transport si Voie 1 pas dispo — vérifier doc Shopify) :
claude mcp add --transport http shopify https://mcp.shopify.com/mcp
```

> Note : la commande `claude mcp add shopify` repose sur le plugin Shopify CLI publié April 2026. Si la résolution du package échoue, fallback Voie 2.

### 4.3 OAuth flow (~5min)
1. URL OAuth Shopify s'ouvre.
2. Connexion compte Shopify Mathis.
3. Sélection du shop (development store recommandé pour le smoke test).
4. Consent page — scopes Admin API typiques :
   - `read_products` · `read_orders` · `read_customers` · `read_inventory` · `read_collections`
   - Optionnel `write_products` / `write_collections` si Mathis veut tests dynamic pricing (NON recommandé pour smoke initial — keep read-only).
5. Authorize → redirect → terminal `MCP shopify added successfully`.

### 4.4 Transport & config
- **Transport** : CLI plugin (stdio JSON-RPC via le plugin Shopify CLI) ou HTTP en fallback.
- **Auth** : OAuth 2.0 Shopify Admin API.
- **API** : Admin API + GraphQL schemas — products, orders, collections, dynamic pricing.

### 4.5 Smoke test

```
mcp__shopify__list_products  (ou équivalent — vérifier nom exact via `claude mcp tools shopify`)
```

OU :
> "Liste les 10 premiers produits du shop dev connecté."

Attendu : array de products du dev store (peut être vide si shop nouveau). Si erreur "no shop authorized" → ré-exécuter OAuth.

**Si `pending live shop`** : documenter dans stream-A.md `Shopify MCP installed but no shop connected at install time — smoke test deferred to next sprint when Mathis adds a shop`.

### 4.6 Revoke / re-install

```bash
claude mcp remove shopify
# Shopify admin : Apps > Claude Code MCP > Uninstall app
# Re-install : claude mcp add shopify
```

---

## 5. Validation post-install (récap)

Après les 4 installs, Mathis lance :

```bash
claude mcp list
# Attendu : context7, supabase, sentry, meta-ads, shopify (5 MCPs au total).

# Tester chaque MCP avec un tool call rapide depuis une session Claude Code :
# 1. Supabase  → list_schemas
# 2. Sentry    → list_issues (peut être vide, OK)
# 3. Meta Ads  → list_ad_accounts
# 4. Shopify   → list_products (OU note `pending live shop`)
```

Updater ensuite `WEBAPP_ARCHITECTURE_MAP.yaml > skills_integration.mcps_server_level[*].installed: true` et la date d'install pour chaque MCP confirmé.

---

## 6. Combo pack associé — "Production observability"

Cf BLUEPRINT.md §2 (post-#27) :
- **Skills** : aucun (MCPs only)
- **MCPs** : Supabase MCP + Sentry MCP (+ Context7 ambient)
- **Activation** : post-deploy V28 webapp (Epic #6 hardening-and-skills-uplift suite)
- **Rationale** : debugging prod en live depuis Claude Code (issues Sentry + schema Supabase dev pour repro)

---

## 7. Notes de sécurité (récap doctrine)

1. **Supabase MCP** : **DEV ONLY**. Voir §1.5.
2. **Sentry MCP** : keep read-only (`event:read` only, pas `event:write`).
3. **Meta Ads MCP** : sélectionner uniquement comptes test/autorisés. Token Meta = 60j, auto-refresh par MCP.
4. **Shopify MCP** : keep read-only au smoke initial. Dev store recommandé.
5. **Tous** : credentials stockés dans `~/.claude/mcp/credentials.json` (chiffré OS-level). **NE JAMAIS** commit ce fichier.
6. Révocation : toujours combiner `claude mcp remove <name>` **+** révocation côté provider (Supabase/Sentry/Meta/Shopify dashboard) pour invalider le token.

---

**Fin de la procédure**. Mathis exécute les 4 installs (~20min) puis valide via §5. Une fois OK → MAJ YAML (script `update_architecture_map.py`) + commit BLUEPRINT v1.2 (sera fait Task #27 post-confirm).
