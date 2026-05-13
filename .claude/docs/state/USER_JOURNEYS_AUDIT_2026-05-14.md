# User Journeys Audit — Next.js webapp (2026-05-14)

Audit cible : `webapp/apps/shell/` deployé sur Vercel (https://growth-cro.vercel.app)
Source : code walk Server Components + API routes + `lib/*-fs.ts` + Sidebar nav.
Position Mathis : *"qu'on ait plus un écran de fumée mais des données dynamiques, une web app qui marche quoi, sur laquelle on pourra partir de zéro, lancer un audit, donner nos inputs, pareil pour le gsg etc."*

## TL;DR

Sur 10 user journeys core demandés : **0 sont fully functional pour le use case "partir de zéro"**, **4 sont half-built** (lecture-only sur données existantes), **6 sont missing entirely**. La webapp **n'a aucun moyen de partir de zéro** parce que :

1. **Aucune CTA "Add client"** n'existe nulle part. Aucune route `POST /api/clients`. Sidebar ne contient aucune action de création. Mathis ne peut pas onboarder un nouveau client depuis l'UI.
2. **Le CreateAuditModal existe** (page `/clients/[slug]` admin only) mais il **n'insère qu'une row Supabase vide** (scores_json={}, total_score_pct=null, page_url optionnel) — **aucun pipeline de capture/scoring/recos n'est déclenché**. L'audit créé reste inerte.
3. **GSG génère un JSON brief mais ne déclenche aucune génération**. La page `/gsg` produit un JSON déterministe (Brand DNA-derived) que l'utilisateur doit **copier-coller manuellement** dans un terminal pour `moteur_gsg`. Bouton "Lancer le run GSG" existe uniquement dans `BriefWizard.tsx` (composant orphelin **non mounté** par `app/gsg/page.tsx` — code mort).
4. **Reality / Learning / GSG dependencies lisent le filesystem** (`data/reality/`, `data/learning/`, `deliverables/gsg_demo/`) qui n'existe pas sur Vercel → ces pages affichent toujours leur empty state en prod.
5. **Captures screenshots Supabase Storage** sont configurées (bucket public + 302 redirect), mais le fallback canonique 8-filenames (`screenshotPath()` whitelist absent en prod) signifie qu'on render des `<img>` qui 404 silencieusement si l'upload n'a pas été fait. À vérifier avec le screenshot prod test.

**Ce que l'utilisateur PEUT faire** (sur les 51 clients × 229 audits × 6524 recos déjà en base) :
- Voir la fleet et naviguer entre clients (Command Center + `/clients`)
- Voir le détail d'un audit existant (scores 6 piliers, recos riches, captures via Supabase Storage)
- Voir la cross-clients aggregator `/recos` avec filtres priority/critère/category
- Voir Brand DNA d'un client (si `brand_dna_json` est seedé)
- Voir Funnel viz (depuis brand_dna_json.funnel ou dérivé d'un audit)
- Voir multi-juges `/audits/[c]/[a]/judges` (si `scores_json.judges_json` présent)
- Voir Doctrine V3.2.1 (statique hardcodé, pas browsable critère par critère)
- Voter une proposition Learning (en local dev seulement — Vercel n'a pas le filesystem)
- Inviter un team member par email
- Changer son mot de passe
- Editer / supprimer un audit ou une reco (admin only)

**Ce que l'utilisateur NE PEUT PAS faire** :
- Créer un client depuis l'UI
- Déclencher un capture/scoring pipeline depuis l'UI
- Déclencher une génération GSG end-to-end depuis l'UI (sans terminal)
- Voir un audit "en cours" / live progress
- Voir une reco lifecycle (backlog/active/done)
- Voir Evidence ledger
- Voir GEO Monitor (route inexistante)
- Voir Experiments / A/B (route inexistante)
- Connecter Reality data en prod (Vercel n'a pas les `data/reality/*.json`)
- Reviewer learning proposals en prod (Vercel n'a pas les `data/learning/*.json`)
- Browser les 54 critères doctrine (page statique hardcodée 7 piliers seulement)
- Lancer un audit Google Ads / Meta Ads depuis l'UI (CSV upload désactivé, CTA explicitement `disabled`)

**Symptômes "écran de fumée" reportés par Mathis** = combinaison de :
- Les pages existent et rendent quelque chose, mais les **boutons d'action sont décoratifs** (`disabled`, "V2 deferred", lien vers terminal CLI).
- La data lue depuis `data/*/` revient vide sur Vercel → empty states partout sur Reality/Learning/GSG demo.
- Les recos minimalistes : `RichRecoCard` est résilient et dégrade gracieusement quand `content_json` est shallow → l'UI affiche juste un titre. **Migration data sur mauvais fichier source** (cf. master PRD : il faut re-migrer depuis `recos_enriched.json` au lieu de `recos_v13_final.json`).

## Per-journey assessment

### Journey 1 — Onboarder un nouveau client (partir de zéro)
- **Status** : MISSING ENTIRELY
- **What exists** :
  - `DELETE /api/clients/[id]` (supprime un client + cascade) — `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/api/clients/[id]/route.ts`
  - `ClientDeleteTrigger` UI button (admin)
- **What's broken/missing** :
  - **Pas de `POST /api/clients`** — aucune route de création
  - **Pas de bouton "Add client"** dans Sidebar, Command Center, `/clients`, ou nulle part
  - **Pas de form/modal** pour saisir name + slug + business_category + panel_role + homepage_url
  - **Pas de trigger de capture** post-création (même si la row était créée, aucun pipeline ne se lance)
  - Les 51 clients déjà en base ont été seedés via migration directe SQL/Python — pas via webapp
- **Files inspected** : `app/api/clients/[id]/route.ts`, `app/clients/page.tsx`, `components/Sidebar.tsx`, `components/clients/ClientList.tsx`, `components/command-center/*`
- **Fix scope** : 6-10h
  - 2h : `POST /api/clients` route handler (validation + slugify + insert RLS-aware + return id)
  - 2h : `CreateClientModal` + `CreateClientTrigger` (parallèle de `CreateAuditModal`)
  - 1h : Sidebar entry + `/clients` page CTA button
  - 1-5h : pipeline trigger (FastAPI POST `/capture/run` ou enqueue Supabase `runs` row + worker daemon) — voir cross-cutting issue #1

### Journey 2 — Lancer un audit sur un client existant
- **Status** : HALF-BUILT
- **What exists** :
  - `CreateAuditTrigger` button on `/clients/[slug]` (admin only) — `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/CreateAuditTrigger.tsx`
  - `CreateAuditModal` with full form (client_slug datalist + page_type + page_url + page_slug + doctrine_version) — `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/components/audits/CreateAuditModal.tsx`
  - `POST /api/audits` (validates + inserts row) — `/Users/mathisfronty/Developer/growth-cro/webapp/apps/shell/app/api/audits/route.ts`
- **What's broken/missing** :
  - L'insert crée une row avec `scores_json={}, total_score=null` — **pas de scoring derrière**. Citation du commentaire : `// page_slug defaults to page_type when not provided (lightweight pattern kept while the dedicated scoring run is not wired up)`.
  - **Aucun appel à FastAPI / pipeline de capture** depuis le route handler
  - L'utilisateur clique "Créer", la modal se ferme, `router.refresh()` → un audit avec 0 score apparaît dans la liste (cassé/inutilisable)
  - Pas de notion "pending/running/completed" dans l'UI — pas de `AuditQualityIndicator` faisant la distinction
  - Le bouton n'apparaît pas sur `/audits/[clientSlug]` (la page liste-audits) — seulement sur `/clients/[slug]`. Mathis doit naviguer en arrière pour lancer un audit
- **Files inspected** : ci-dessus + `lib/require-admin.ts`
- **Fix scope** : 4-8h
  - 1h : ajouter `CreateAuditTrigger` aussi sur `/audits/[clientSlug]` et `/audits` (avec ClientPicker)
  - 1h : ajouter colonne `status` (pending/running/completed/failed) sur `audits` + UI badge
  - 2-6h : wire pipeline — soit POST FastAPI `/capture/run` + worker poll Supabase, soit insert dans `runs` table + Edge Function listener

### Journey 3 — Voir l'audit complet d'une page
- **Status** : FULLY FUNCTIONAL (sur la data riche actuelle)
- **What exists** :
  - `/audits/[clientSlug]/[auditId]/page.tsx` Server Component avec parallel fetch (client+audit+recos+siblings+role)
  - `AuditDetailFull` : 2-col grid (ScoresCard avec 6 piliers radial + ScoreBar | screenshots panel desktop+mobile fold)
  - `RichRecoCard` : full reco_text + anti_patterns (pattern/why_bad/instead_do/examples_good) + collapsible debug footer (ICE/effort/enricher_version/evidence_ids)
  - Top-5 expanded + collapsed remainder
  - Multi-judge link → `/audits/[c]/[a]/judges`
  - `AuditEditTrigger` (admin) + per-reco `RecoEditTrigger`
  - `ConvergedNotice` pour audits de même page_type
  - Screenshots via `/api/screenshots/[c]/[p]/[f]/route.ts` → 302 redirect Supabase Storage (SP-11)
- **What's broken/missing** :
  - **`utility_banner` non rendu** : `getAuditScores` cap à 8 axes mais `KNOWN_MAX` ne contient pas le pilier `utility_elements` (V3.3 bloc 7) — il sera rendu avec un max fallback de 30 alors que le vrai max est 21
  - **Pas de lifecycle status per reco** (backlog/active/done) — pas de colonne en base ni d'UI
  - **Pas d'Evidence ledger** standalone (les `evidence_ids` sont juste affichés dans le debug footer collapsable)
  - **Multi-judge verdict optionnel** : la page judges fonctionne mais si `scores_json.judges_json` est absent (cas seed actuel probable), affiche empty state — `payload` est null sur la majorité des 229 audits
  - **Screenshots prod 404** : `getScreenshotsForPageOrCanonical` retourne `CANONICAL_SCREENSHOT_FILENAMES` (8 fichiers fixes) sur Vercel parce que `data/captures/` est absent. Si l'upload Supabase Storage SP-11 n'a pas couvert toutes les (client, page) paires, les `<img>` 404 silencieusement (broken-image icon)
  - **Export PDF** affiché en pill décoratif disabled (`opacity:0.5, cursor:not-allowed, title="Export PDF — V2"`)
  - Captures attendent `.webp` (suffix swap dans `screenshotPublicUrl`) — si l'upload a poussé du `.png`, mismatch silent 404
- **Files inspected** : `app/audits/[c]/[a]/page.tsx`, `app/audits/[c]/[a]/judges/page.tsx`, `components/audits/AuditDetailFull.tsx`, `components/audits/RichRecoCard.tsx`, `components/audits/AuditScreenshotsPanel.tsx`, `lib/captures-fs.ts`, `app/api/screenshots/[c]/[p]/[f]/route.ts`, `components/clients/score-utils.ts`, `components/audits/PillarsSummary.tsx`
- **Fix scope** : 6-10h
  - 1h : ajouter `utility_elements: 21` à `KNOWN_MAX`
  - 2h : ajouter colonne `lifecycle_status` sur `recos` + UI dropdown sur `RichRecoCard`
  - 2h : vérifier upload SP-11 couvre les 438 (client, page) paires en Storage + corriger mismatch png↔webp
  - 1-3h : Evidence ledger standalone view (panel ou modal listant `evidence_ids` avec liens vers captures + DOM snippets)
  - 2h : Export PDF (Puppeteer ou react-pdf depuis l'audit detail)

### Journey 4 — Inputs GSG : générer une LP
- **Status** : HALF-BUILT (lecture-only, génération hors-app)
- **What exists** :
  - `/gsg/page.tsx` Server Component avec :
    - 5 modes selector (`GsgModesSelector`)
    - `buildDeterministicBrief` qui produit un JSON typed (mode/page_type/page_url/doctrine_version/brand_tokens/layout)
    - `ControlledPreviewPanel` qui iframe les `deliverables/gsg_demo/*.html` si présent
    - `CopyBriefButton` → copy-paste manuel
    - `EndToEndDemoFlow` : 4-step visualization (Audit → Reco → Brief → Preview)
    - `ClientPicker` form GET pour switcher de client
- **What's broken/missing** :
  - **Aucun trigger pipeline** : pas de bouton "Lancer le run GSG" sur la page active. Commentaire ligne 250 : *"Live trigger FastAPI reviendra en V2"*
  - L'utilisateur copie le brief JSON et doit le donner manuellement à `moteur_gsg` en local
  - **`BriefWizard` est code mort** : il contient le bouton `triggerGsgRun()` (ligne 188 `<Button onClick={runGsg}>`) mais il n'est mounté que par `Studio.tsx` qui n'est utilisé nulle part dans `app/`
  - **Preview iframe vide en prod** : `listGsgDemoFiles()` scan `deliverables/gsg_demo/*.html` qui n'existe pas sur Vercel → demos.length = 0 → "Open preview in new tab" est désactivé (`aria-disabled`)
  - **Brief deterministe quasi-vide** quand `brand_dna_json` est null (3 seed clients sans DNA) — `primary_color="#d7b46a"`, `signature=""`, etc.
  - **Pas de wizard inputs personnalisés** : Mathis ne peut pas saisir un brief custom (target_audience, pitch, page_url custom) depuis l'UI active — seul le composant orphelin `BriefWizard` le fait
  - **Pas de Brand DNA / Doctrine pack visible** dans le flow GSG (le V27.2-G pipeline `intake → context_pack → visual_intelligence → controlled_renderer → multi_judge` est seulement un schéma dans `Studio.tsx` code mort)
- **Files inspected** : `app/gsg/page.tsx`, `lib/gsg-brief.ts`, `lib/gsg-fs.ts`, `lib/gsg-api.ts`, `components/gsg/*` (Studio.tsx, BriefWizard.tsx, EndToEndDemoFlow.tsx, ControlledPreviewPanel.tsx)
- **Fix scope** : 10-16h
  - 4h : déployer FastAPI sur Railway/Fly.io + sécurité (CORS + auth bearer)
  - 2h : ajouter `BriefWizard` (custom inputs) sur `/gsg` à côté du brief déterministe
  - 2h : ajouter bouton "Lancer le run GSG" qui POST FastAPI `/gsg/run` + insert `runs` table + spinner
  - 2h : RecentRunsTracker (existe pour reality) à dupliquer pour GSG runs
  - 2-4h : preview iframe live des résultats (objet HTML stocké Supabase Storage post-génération)
  - 2h : afficher Brand DNA + Doctrine pack résolus dans le panneau de droite

### Journey 5 — Reality Layer (CVR/CPA/AOV réels)
- **Status** : HALF-BUILT (lecture-only depuis filesystem qui n'existe pas en prod)
- **What exists** :
  - `/reality/page.tsx` : listing 6 connectors (ga4/catchr/meta_ads/google_ads/shopify/clarity) avec credentials status pills
  - `/reality/[clientSlug]/page.tsx` : CredentialsGrid + SnapshotMetricsCard + history list
  - `RecentRunsTracker` client island avec Supabase Realtime subscription (filtré `type=reality`)
  - `clientCredentialsReport()` qui check les env vars (e.g. `META_ACCESS_TOKEN_WEGLOT`)
- **What's broken/missing** :
  - **Toutes les data viennent du filesystem** (`data/reality/<client>/<page>/<date>/reality_snapshot.json`) → absent sur Vercel → empty state partout en prod
  - **5 connectors annoncés en TL;DR mais 6 en réalité** (ga4/catchr/meta_ads/google_ads/shopify/clarity)
  - **Pas de form pour saisir credentials depuis l'UI** : la doc dit "Drop per-client credentials in `.env` (e.g. `META_ACCESS_TOKEN_WEGLOT=…`)" → manuel, hors-app, redéploiement nécessaire
  - **Pas de bouton "Run snapshot"** : la doc dit "Run `python3 -m growthcro.reality.orchestrator --client <slug> --page-url …`" → CLI manuel
  - **Pas de Clarity / Shopify SnapshotMetrics rendus** : seul `SnapshotMetricsCard` existe (struct générique) — pas de breakdowns par connecteur
- **Files inspected** : `app/reality/page.tsx`, `app/reality/[clientSlug]/page.tsx`, `lib/reality-fs.ts`, `components/reality/*`
- **Fix scope** : 16-30h
  - 2h : migrer le storage de `data/reality/*.json` vers une table Supabase `reality_snapshots`
  - 4h : form pour saisir credentials par client (encryption via Supabase Vault ou variables Vercel par client)
  - 4h : bouton "Run snapshot" qui POST FastAPI `/reality/run` + display realtime
  - 6h : per-connector metric cards (GA4 CVR, Meta CPA, Shopify AOV) avec drill-down
  - 4h+ : auth OAuth GA4/Meta/Google Ads (au lieu de tokens manuels)

### Journey 6 — Doctrine (7 piliers + 54 critères)
- **Status** : HALF-BUILT (vue résumée seulement)
- **What exists** :
  - `/doctrine/page.tsx` : 7 piliers cards (hero/persuasion/ux/coherence/psycho/tech/utility_elements) avec label + max + nombre de critères + hint
  - Notes V3.2.1 → V3.3 explicatives
- **What's broken/missing** :
  - **Hardcoded inline dans `page.tsx`** : les 7 piliers sont une constante locale, pas browsables critère par critère
  - **Pas de drill-down** sur un pilier pour voir les 6/11/8/9/8/5/7 critères
  - **Pas de killer rules** affichés
  - **Pas d'anti-patterns** affichés
  - **Pas de scoring rules** par critère
  - Le commentaire ligne 6 reconnaît : *"V1 stub: piliers metadata hardcoded inline (mirrors playbook/bloc_*_v3-3.json) since Vercel functions don't ship the playbook/ folder. A future SP can wire this to a Supabase-stored doctrine_versions table or a build-time JSON import."*
- **Files inspected** : `app/doctrine/page.tsx`
- **Fix scope** : 8-12h
  - 2h : créer Supabase table `doctrine_versions` + seed depuis `playbook/bloc_*_v3-3.json`
  - 3h : page browse-by-pillar avec liste critères (id/label/max/scoring_rules)
  - 2h : afficher killer rules + anti-patterns
  - 1h : navigation tabs entre 7 piliers
  - 2h : page par critère (showing examples + recos historiques liées à ce critère)

### Journey 7 — Learning (review doctrine proposals)
- **Status** : HALF-BUILT (vote queue OK en dev, vide en prod)
- **What exists** :
  - `/learning/page.tsx` : `ProposalStats` + `ProposalQueue` (vote 1-click accept/reject/refine/defer) + `ProposalList` (browse history)
  - `/learning/[proposalId]/page.tsx` : détail proposal
  - `POST /api/learning/proposals/review` : write `.review.json` sidecar (admin gated)
- **What's broken/missing** :
  - **Filesystem-bound** : `listV29Proposals()` lit `data/learning/audit_based_proposals/*.json` + `listV30Proposals()` lit `data/learning/data_driven_proposals/<date>/*.json` → tous absents en prod Vercel → page vide
  - **Le PR/PRD mentionne 69 doctrine_proposals** mais sur Vercel `all = []`
  - **Pas de KPI grid post-vote refresh** dynamique (la stats card render au server load, pas de refresh sans `router.refresh()` global)
  - **Reviews écrits sur filesystem éphémère Vercel** : un POST vers `/api/learning/proposals/review` écrit un `.review.json` qui sera détruit au prochain cold start. Non persistant.
- **Files inspected** : `app/learning/*`, `app/api/learning/proposals/review/route.ts`, `lib/proposals-fs.ts`, `components/learning/*`
- **Fix scope** : 12-16h
  - 3h : migrer proposals vers Supabase table `doctrine_proposals` (sync depuis filesystem en bootstrap)
  - 3h : migrer reviews vers Supabase table `doctrine_proposal_reviews` (drop filesystem sidecar)
  - 2h : refresh KPI live post-vote (optimistic update + revalidate route)
  - 2h : filtres / search côté Supabase (au lieu de in-memory `applyFilters`)
  - 2-6h : "Merge doctrine" automation (downstream pipeline encore manuel selon commentaire `/learning/page.tsx` L31)

### Journey 8 — Settings (team + account + usage)
- **Status** : FULLY FUNCTIONAL (avec caveats)
- **What exists** :
  - `/settings/page.tsx` avec 4 tabs (Account / Team / Usage / API)
  - `AccountTab` : password change via Supabase auth (re-verify current password + updateUser)
  - `TeamTab` : list members + invite par email (`POST /api/team/invite` admin-only + service_role)
  - `UsageTab` : counts clients/audits/recos/runsThisMonth
  - `ApiTab` : Supabase URL + anonKey + projectRef (read-only)
- **What's broken/missing** :
  - **Email enrichment limité** : seul l'email du current user est affiché, les autres members affichent `null` (commentaire L48-49 : *"Email enrichment requires service_role; on the read path we show the truncated user_id when the row is the current user (which is the common single-tenant case for V1)"*)
  - **Pas de remove member** : seul invite est wired
  - **Pas de rotation de service_role JWT** depuis l'UI (cf. CLAUDE.md "rotater service_role JWT Supabase (repo PUBLIC + JWT in git history)" — risque sécurité)
  - **Pas de rotate anon key** UI
- **Files inspected** : `app/settings/page.tsx`, `components/settings/*`, `app/api/team/invite/route.ts`
- **Fix scope** : 4-6h
  - 1h : service_role lookup pour enrichir tous les emails members
  - 2h : `DELETE /api/team/members/[id]` + UI button
  - 2h : rotate key + role change UI
  - 1h : invite email customization (template)

### Journey 9 — GEO Monitor (ChatGPT/Perplexity/Claude presence)
- **Status** : MISSING ENTIRELY
- **What exists** : Rien.
- **What's broken/missing** :
  - **Pas de route `/geo`** : `find webapp/apps/shell/app` ne retourne aucun `geo/*`
  - **Pas de composant `GeoMonitor`** ou similaire (grep retourne 0 résultats)
  - **Pas d'entrée Sidebar**
- **Files inspected** : `app/`, `components/`, `lib/` (greps systématiques)
- **Fix scope** : 16-30h (V31+, hors scope MVP probable)

### Journey 10 — Experiments (A/B test tracking)
- **Status** : MISSING ENTIRELY
- **What exists** : Rien.
- **What's broken/missing** :
  - **Pas de route `/experiments`**
  - **Pas de composant Experiments**
  - **Pas d'entrée Sidebar**
  - **Pas de table `experiments` en base** (vérifié sur `@growthcro/data` exports : Client, Audit, Reco, Run, ClientWithStats, RecoWithClient seulement)
- **Files inspected** : `app/`, `components/`, `lib/`, `@growthcro/data` exports
- **Fix scope** : 12-20h (V27+, hors scope MVP probable)

## Cross-cutting issues

### 1. Pipeline triggers — RIEN N'EST WIRED FROM UI
- **Constat** : aucune action UI ne déclenche une capture, scoring, ou enrichment pipeline.
- **Où sont les pipelines** : `growthcro/capture/*.py`, `growthcro/scoring/*.py`, `growthcro/recos/*.py`, `growthcro/reality/orchestrator.py`, `moteur_gsg/*.py` — tous CLI-only.
- **Couches manquantes** :
  - **FastAPI** (`growthcro/api/server.py`) est référencée par `webapp/.env.example` (`NEXT_PUBLIC_API_BASE_URL=https://growthcro-api.fly.dev`) mais **pas déployée** (URL n'est qu'un exemple). `lib/gsg-api.ts` peut POSTer mais ne marche pas en prod.
  - **Worker daemon** absent : pas de service qui poll Supabase `runs` table pour exécuter les pipelines en background.
  - **Vercel cron** : pas de `vercel.json` cron jobs visibles.
- **Impact** : Mathis ne peut pas "partir de zéro" depuis l'UI. La webapp est un viewer pour data déjà calculée hors-app.

### 2. Filesystem-bound modules cassés sur Vercel
- `lib/proposals-fs.ts` (Learning), `lib/reality-fs.ts` (Reality), `lib/gsg-fs.ts` (GSG demo), `lib/aura-fs.ts` (Brand DNA AURA sidecar) — tous lisent `data/*/` ou `deliverables/*/` qui n'existent pas sur Vercel.
- `lib/captures-fs.ts` a SP-11 fallback (Supabase Storage 302 redirect) mais seul ce module fait ce travail. Les 4 autres `*-fs.ts` n'ont pas de fallback.

### 3. Real-time updates — partiel
- `RecentRunsTracker` (Reality) et `RunsLiveFeed` (Sidebar) ont une Supabase Realtime subscription sur `runs` table.
- Mais aucun pipeline ne POST dans `runs` depuis l'UI → la live feed est vide.

### 4. Permissions admin — cohérentes mais limitatives
- `require-admin.ts` enforce `role==='admin'` sur tous les mutating endpoints (`/api/audits`, `/api/clients/[id]`, `/api/recos/[id]`, `/api/team/invite`, `/api/learning/proposals/review`).
- Cohérent. Mais consultants et viewers ne peuvent **rien créer** depuis l'UI (cohérent avec V1 policy mais c'est dur pour Growth Society où plusieurs consultants veulent collaborer).

### 5. Error states — souvent silencieux
- Pattern récurrent : `.catch(() => null)` ou `.catch(() => [])` partout dans les Server Components (`/clients/[slug]/page.tsx` L26-36, `/audits/[c]/[a]/page.tsx` L27-40, `/audits/[c]/page.tsx` L171-183, etc.).
- Quand Supabase fail, l'UI affiche un empty state ou une 404 sans message clair. Mathis voit "Pas de scores" sans savoir si c'est un seed-vide ou un service down.
- Exception : home `loadOverview()` qui collecte les erreurs et les affiche en bas de page (mais à 12px muted, facilement oublié).

### 6. Screenshots prod — risque silencieux
- `screenshotPath()` whitelist via `listScreenshotsForPage()` qui lit `data/captures/<c>/<p>/screenshots/` → vide sur Vercel → `screenshotPath()` retourne null toujours.
- Le route handler `/api/screenshots/[c]/[p]/[f]` skip ce check si `NEXT_PUBLIC_SUPABASE_URL` est set → 302 redirect vers Storage CDN.
- **Mais** `getScreenshotsForPageOrCanonical()` retourne les 8 `CANONICAL_SCREENSHOT_FILENAMES` toujours, donc les `<img>` se font monter même si Storage n'a pas l'objet → broken-image icon silencieux.
- À vérifier : l'upload SP-11 (`scripts/upload_screenshots_to_supabase.py`) a-t-il couvert les 438 paires (client, page) ? La conversion png→webp est-elle systématique ?

## Top 5 missing capabilities for "partir de zéro → audit → inputs"

1. **`POST /api/clients` + AddClientModal** — Mathis ne peut pas créer un client depuis l'UI. Bloquant absolu pour "partir de zéro".

2. **Pipeline trigger wiring (capture/scoring/recos)** — `POST /api/audits` insère une row vide sans déclencher de pipeline. FastAPI non déployée. Aucune route pour `POST /capture/run`, `POST /score/run`, `POST /recos/enrich`. Bloquant pour "lancer un audit".

3. **GSG end-to-end trigger** — `/gsg` produit un JSON brief mais aucun bouton ne lance la génération. `BriefWizard` (avec le bouton `triggerGsgRun`) est code mort. Bloquant pour "pareil pour le gsg".

4. **Audit lifecycle status + progress** — Pas de `status` field sur audits (pending/running/completed/failed). Pas d'UI de progress. Une fois pipeline trigger wired, l'utilisateur ne saurait pas où il en est.

5. **Reality + Learning data persistence en prod** — Les deux modules dépendent du filesystem absent sur Vercel. Les 69 doctrine_proposals + tous les reality_snapshots existants ne sont pas visibles depuis la webapp prod.

## Recommended fix sequence (3-5 sprint-sized chunks)

### Sprint 1 — Unblock "partir de zéro" (ETA 8-12h)
- `POST /api/clients` + `AddClientModal` + Sidebar/Command Center CTA
- Ajouter colonne `status` sur `audits` table + migration de l'existant
- Surfacer `CreateAuditTrigger` aussi sur `/audits/[c]` et `/audits` (avec ClientPicker)
- Sortir tous les `.catch(() => null)` silent → toast d'erreur user-facing

### Sprint 2 — Pipeline trigger via Supabase runs queue (ETA 12-20h)
- Décider : FastAPI Railway/Fly.io OU worker daemon polling Supabase OU Vercel Cron.
- Recommandé pour V1 simple : insert dans `runs` table (`type=capture|score|reco_enrich|gsg`), un worker Python sur Railway poll et exécute, update `runs.status`.
- POST endpoints `/api/runs/capture`, `/api/runs/score`, `/api/runs/recos`, `/api/runs/gsg` qui font juste l'insert.
- UI : bouton "Run capture" / "Re-score" / "Re-enrich" sur `/clients/[slug]` + `/audits/[c]/[a]`
- Live feed via `RunsLiveFeed` + Supabase Realtime.

### Sprint 3 — GSG inputs end-to-end (ETA 10-16h)
- Migrer `BriefWizard` (custom inputs) vers `/gsg/page.tsx` à côté du brief déterministe (2 modes : auto-derived vs custom).
- Ajouter "Lancer le run GSG" qui POST `/api/runs/gsg` (Sprint 2 wiring)
- Stocker l'HTML généré sur Supabase Storage (bucket `gsg_outputs`)
- Preview iframe live de l'output post-run
- Multi-judge score affiché à côté du preview

### Sprint 4 — Data fidelity + filesystem migration (ETA 12-18h)
- Re-migrer recos depuis `recos_enriched.json` (cf. master PRD Wave A) au lieu du minimaliste `recos_v13_final.json` actuel
- Migrer `data/learning/*.json` → Supabase table `doctrine_proposals` + `doctrine_proposal_reviews`
- Migrer `data/reality/*.json` → Supabase table `reality_snapshots`
- Vérifier upload SP-11 captures (438 paires) — fixer les 404 silent + mismatch png↔webp
- Ajouter `utility_elements: 21` à `KNOWN_MAX` dans `score-utils.ts`

### Sprint 5 — Polish + missing journeys (ETA 16-30h, optionnel V1)
- Lifecycle status per reco (backlog/active/done) + UI dropdown
- Evidence ledger standalone view
- Doctrine browse-by-pillar avec 54 critères depuis Supabase
- Export PDF audit
- Settings : remove member + key rotation
- (V2+) GEO Monitor route
- (V2+) Experiments route

## Conclusion

La webapp est un **viewer compétent pour data pré-calculée** mais **n'est pas une working tool end-to-end**. L'écran de fumée vient de l'écart entre :
- Une UI sophistiquée (5-col KPI grid, 6-piliers radial, Rich reco cards, Multi-judge panel, etc.) qui suggère un outil complet
- Une absence totale de **glue pipeline** entre les actions UI et les modules Python (`growthcro/*`, `moteur_gsg/*`)

Pour "partir de zéro → audit → inputs GSG" la priorité absolue est **Sprint 1 + Sprint 2 + Sprint 3** (30-50h cumulé). Sans cette glue, ajouter de nouvelles features est cosmétique.
