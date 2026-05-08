# GrowthCRO — Journal chronologique complet

> Historique détaillé du projet depuis le premier jour. Toute session Claude doit lire ce fichier pour reprendre sans perdre de contexte.

## Vision (citations Mathis)

> "On va développer un outil ensemble qui permet de s'auto enrichir de données, d'auditer des sites et LPs de client pour donner un score selon des critères à ses pages et ce qui est optimisable et ensuite de générer lui même un outil de fabrication de site et de LPs de lui même, avec la DA, l'esthétique, les copys pertinents par rapport au client, ainsi que toutes les sections nécessaires en fonction du type de business etc"

> "C'est pas un flux à sens unique" — chaque module lit ET écrit dans un store commun.

> "Mille fois mieux que Rocket" — Rocket.new est l'inspiration visuelle, pas le plafond.

**Nom produit :** GrowthCRO — outil interne Growth Society (Mathis, tech@growth-society.com).

## Acteurs & contexte

- **Mathis** : fondateur/opérateur Growth Society, seul utilisateur du produit au départ.
- **Rocket.new** : outil utilisé initialement, jugé insuffisant → déclencheur du projet.
- **Notion CRO doc** : source de vérité des critères CRO Growth Society (accès MCP read-only).
- **Règle Notion gravée** : jamais d'écriture Notion sans permission explicite par occurrence.

## Phase 0 — Genèse & scaffolding Next.js

- Skills internes créés (`lp-creator`, `lp-front`) pour la production de LP haute-conversion.
- Next.js 15 + React 19 + TypeScript + Tailwind, dossier `growthcro/`.
- Design tokens : deep navy, Fraunces serif + Geist sans/mono, accents emerald/cyan/violet/amber/red, grain + ambient glow.
- Supabase prévu pour plus tard ; démarrage avec store client.

## Phase 1 — GrowthStore bidirectionnel

- `GrowthStore` = React Context + `useReducer` + persistence `localStorage` (bus commun).
- Entités : Client, Audit, Recommendation, Page, GrowthAsset, GrowthRef, NotionDoc, Connexion.
- Principe **bidirectionnel** : chaque module lit ET écrit. 12 points de branchement identifiés.

### Les 12 points de branchement

| # | Flux |
|---|---|
| 1 | Clients → Audit |
| 2 | Audit → Recos |
| 3 | Recos → GSG |
| 4 | Library → GSG (assets) |
| 5 | GSG lit brief complet |
| 6 | GSG → marque recos implemented |
| 7 | GSG → patterns vers Library si score>120 |
| 8 | Growth Refs → auto-audit URL |
| 9 | Audit → enrichit Refs si URL externe |
| 10 | Notion → injection contexte IA |
| 11 | Catchr → perf pages |
| 12 | Dashboard → alertes drill-down |

## Phase 2 — Dashboard 31 clients

- Dashboard Next.js avec 31 clients réels Growth Society.
- `clients_database.json` = source de vérité (dict `{clients, metadata}`).
- Pipeline stage heuristique dérivée du score : Live ≥75, Build ≥65, Recos ≥55, Audit >0, Discovery 0.

## Phase 3 — Prototypes V1 → V3

- Itérations rapides en HTML standalone pour valider la sidebar, les modules et la navigation sans passer par `npm run dev`.
- V1/V2/V3 : exploration des écrans Dashboard/Clients/Audit/Recos/GSG/Library/Notion/Connexions.

## Phase 4 — Prototype V4 (2026-04-07)

**Fichier :** `prototype/GrowthCRO-Prototype-V4.html` (~1400 lignes, standalone).

- Sidebar V4 complète : 6 groupes + Growth Library expandable (3 sous-onglets).
- 8 modules interactifs : Dashboard, Clients, Audit, Recos, GSG, Library, Notion, Connexions.
- Store JS interne : 7 clients, 14 growthAssets, 8 refs, 8 Notion pages, 8 connexions.
- Démos bidirectionnelles via banner `showFlow()` : Library→GSG, Clients→Audit, Audit→Recos, Recos→GSG, Refs→Audit, Refs→GSG.
- Double-clic ouvre le prototype sans serveur.

### Bridges Next.js câblés (#1 → #5)

`growthcro/src/components/StoreBridge.tsx` ajoute 4 mini composants client :
- `ClientToAuditBridge` (#1) : `?clientId=` → `selectClient` + badge contexte injecté.
- `AuditToRecosBridge` (#2) : "Terminer audit & créer recos" → `upsertAudit` + 3 `upsertReco` puis `router.push('/recommendations-builder?auditId=…')`.
- `RecosToGsgBridge` (#3) : `?auditId=` → sélection → "Envoyer au GSG" → `/html-page-generator?fromAudit=…`.
- `GsgBriefBridge` (#5) : `?fromAudit=` → agrège client+audit+recos+assets → carte "Brief auto-rempli" avec top 3 recos.

Pages mises à jour : `cro-audit-generator`, `recommendations-builder`, `html-page-generator`, `client-project-detail`. Chacune wrap les bridges dans `<Suspense>` pour `useSearchParams`.

## Phase 5 — Prototype V5 (2026-04-07 soir)

**Fichier :** `prototype/GrowthCRO-Prototype-V5.html`.

- Renommage V4 → V5 (l'ancien contenait encore "V4" dans le titre, Mathis a flashé).
- Audit des 30 clients : `data/audits_all_dashboard_v2.html` (source initiale) + merge dans le prototype via `GS_DATA` blob injecté.
- Pipeline stage + hub clients enrichis.

## Phase 6 — Prototype V5.1 (2026-04-08 matin) — refonte vue détail audit

**Déclencheur Mathis (screenshot + fichier `uploads/audit-ocni-factory.html`) :**

> "Je trouve que la meilleure expérience visuelle et pertinence en termes d'affichage de la donnée (clair et synthétique d'abord mais aussi détaillé par la suite et avec un plan d'action temporel) est ce que tu as fait pour l'audit de OCNI. C'est bizarre mais on retrouve pas du tout ça dans GrowthCRO v5. […] C'est pas 'générer les recos' elles sont déjà générées."

**Décisions validées via AskUserQuestion :**
- Onglets internes dans la vue détail (overview / critères / waves / rewrites).
- Enrichir façon OCNI : ring + verdict + breakdown 5 barres + quick wins + critiques + radar + grille 30 critères + 3 waves temporelles + rewrites.
- CTA header : "Envoyer GSG" primary + "Re-auditer" + "Export PDF" ghost. Supprimer "Générer les recos".

**Livré :**
- Extraction complète de `audit-ocni-factory.html` (943 lignes) via Python regex → `data/audit_ocni_full.json`.
- OCNI : score 46.5/90, verdict "Page sous-performante, refonte partielle recommandée", 5 catégories × 6 critères × 3 pts, 4 problèmes, 5 wins, 30 critiques détaillées, 3 waves d'actions.
- `data/audits.json` mergé : OCNI full + 30 autres clients en shape light (empty states UI).
- `data/_proto_data_blob.json` rebuilt (114 KB).
- Prototype V5.1 : +470 lignes CSS (score-hero-v5, breakdown-v5, issues-grid, issue-item-v5 critical/quick, criteria-section/row-v5 grid 50/1fr/90/320, action-plan-v5/wave-header-v5/action-row-v5, hub-card-mini-ring, hub-card-verdict, hub-card-weak w-tag, empty-v5).
- JS : `buildShortVerdict`, `buildWeakTags`, `switchAuditTab`, `renderAuditHub` (mini-ring r=22), `openAuditDetail` entièrement réécrit.
- Fix collision ID `btn-send-to-gsg` (recos page vs audit detail) → `btn-audit-send-to-gsg`.
- Fix classes CSS `.visible` → `.show`/`.open` selon les cas.

## Phase 7 — V5.2 (en cours, 2026-04-08)

**Déclencheur Mathis :**

> "On a commencé à sauvegarder la mémoire de ce gros projet assez tard et entre temps y'a des données qui ont été perdues. Je vois du coup plein de choses fausses dans l'audit. Du coup on va entraîner ton modèle d'audit et reco et ton IA avant de passer sur les autres client en faisant l'audit d'OCNI jusqu'à ce qu'il soit parfait. Oublie pas de sauvegarder la mémoire du projet dans les moindre détails depuis le début."

**Décisions validées (AskUserQuestion) :**
- **Grille profonde V2** segmentée par type de page ET catégorie business (Home, LP Produit, Collection, Blog, Article, Quiz/VSL, Pricing, Checkout) — issu de la doc CRO Notion + critères psycho ajoutés par Claude.
- **Growth Refs** : 30 marques × 10 catégories business (3 par catégorie).
- **OCNI** : audit from scratch avec la nouvelle grille.
- **Mémoire** : `PROJECT_MEMORY.md` enrichi + journal dédié (ce fichier) + `memory/SPECS.md`.

**État d'avancement V5.2 (2026-04-08 après-midi) :**
1. ✅ Restructure mémoire en 3 fichiers (`PROJECT_MEMORY.md` + `memory/HISTORY.md` + `memory/SPECS.md`).
2. ✅ Grille V2 par page type → `data/cro_criteria_v2.json` : 6 piliers universels (Cohérence 18 / Hero 18 / Persuasion 24 / UX 24 / Tech 15 / Psycho 18 = **/117**), 9 types de page, 10 catégories business, pondérations par type de page.
3. ✅ Growth Refs 30 marques (3 × 10 catégories) → `data/growth_refs.json` : Typology, Glossier, Merit, Oatly, Feastables, Magic Spoon, Linear, Notion, Attio, Duolingo, Cal.com, Headspace, Revolut, Qonto, Wise, Growth Tribe, LiveMentor, Koober, HelloFresh, Dollar Shave Club, Nuud, Vinted, Malt, Etsy, Aesop, Loro Piana, Sézane, Whoop, Oura, Asphalte. Chaque ref est réconciliée avec les `criteriaIds` de la grille V2.
4. ✅ Audit OCNI Home from scratch avec grille V2 → `data/audit_ocni_v2.json` : score 54/117 (46%), verdict "Refonte Hero + Persuasion + Psycho recommandée", 6 catégories scorées, 36 critères détaillés, 6 problèmes, 4 wins, 3 waves (Quick Wins / Optimisations structurelles / Refonte créative), 4 rewrites, 5 benchmarks Growth Refs. **NB** : `ocnifactory.com` bloqué par le proxy egress → critères marqués `unverified` à revalider en live avec Mathis.
5. ⏳ Injection du nouvel audit OCNI dans le prototype (audits.json + blob + HTML V5.2) — à faire après validation Mathis.
6. ⏳ Généralisation aux 30 autres clients une fois OCNI validé.

## Conventions techniques (historique)

- `'use client'` en tête de fichier pour tout composant utilisant hooks.
- Pas de `any` en TypeScript.
- lucide-react pour les icônes, sonner pour les toasts, dark mode natif.
- Tailwind + design tokens centralisés.
- GrowthStore = Context + useReducer + localStorage. Pas de Zustand/Redux.
- Prototypes HTML standalone pour itération rapide sans serveur.
- Skills lus AVANT toute création de fichier (pptx/docx/xlsx/pdf).

## Framework CRO /90 (V1)

| Catégorie | Points |
|---|---|
| Cohérence Stratégique | /18 |
| Hero / ATF | /15 |
| Persuasion & Copy | /21 |
| Structure & UX | /21 |
| Qualité Technique | /15 |

Score global GSG /153 = CRO /90 + Design /45 + Psycho /18.

(Remplacé par la grille V2 segmentée — voir `SPECS.md`.)

---

## Phase 7.bis — Fin de session 2026-04-08 — blocage egress & décision "nouvelle session"

**Contexte :** après livraison de la mémoire 3 fichiers + grille V2 + Growth Refs 30 + audit OCNI V2, Mathis a tenu à ce que l'audit OCNI soit **réellement sourcé en live** (plus aucun critère `unverified`).

**Tentatives :**
1. `WebFetch https://ocnifactory.com` → `EGRESS_BLOCKED` par le proxy réseau Cowork.
2. `WebFetch https://www.ocnifactory.com` → même blocage.
3. Claude in Chrome disponible → `tabs_context_mcp` échoue : "Multiple Chrome extensions connected. Open the Claude extension in the browser you want to use and click 'Connect'." → action manuelle Mathis requise.
4. Mathis propose Apify ("tu es déjà connecté normalement") → **faux** : aucun outil `mcp__apify__*` exposé dans la session, Apify pas branché côté Cowork.
5. Guide donné à Mathis pour brancher Apify MCP (console.apify.com → Settings → Integrations → API token → Claude Desktop Settings → Connectors → Add custom connector → `https://mcp.apify.com` + Bearer token → redémarrer Claude Desktop complètement).
6. Mathis a redémarré, mais les MCP nouvellement ajoutés **ne sont pas chargés dans une session Cowork déjà ouverte** — il faut ouvrir une **nouvelle session** pour qu'ils apparaissent.

**Décision Mathis (validée) :** Option A — ouvrir une nouvelle session Cowork dans le même projet. Toute la mémoire est dans les 3 fichiers, la prochaine session reprend instantanément.

**Outils actifs confirmés dans cette session (pour info handoff) :**
- File tools (Read/Write/Edit/Bash), WebFetch (egress-limited), WebSearch
- Notion MCP (`mcp__0eae5e51...__notion-*`) — read-only
- Claude in Chrome (`mcp__Claude_in_Chrome__*`) — nécessite action manuelle "Connect"
- Cowork (`mcp__cowork__*`)
- Scheduled tasks (`mcp__scheduled-tasks__*`)
- Plugins + MCP registry (`mcp__plugins__*`, `mcp__mcp-registry__*`)
- Session info (`mcp__session_info__*`)
- **PAS d'Apify** (à confirmer dans la prochaine session)

**État final des livrables V5.2 :**
- ✅ `PROJECT_MEMORY.md` (index) — racine projet
- ✅ `memory/HISTORY.md` — ce fichier
- ✅ `memory/SPECS.md` — specs techniques
- ✅ `data/cro_criteria_v2.json` — grille V2 /117 segmentée
- ✅ `data/growth_refs.json` — 30 marques × 10 catégories
- ✅ `data/audit_ocni_v2.json` — audit OCNI from scratch (avec critères `unverified` à revalider)
- ⏳ Injection prototype V5.2 — bloquée en attente d'audit live sourcé OCNI

**Instructions exactes pour la prochaine session (handoff) :**
1. Lire `PROJECT_MEMORY.md` → `memory/HISTORY.md` → `memory/SPECS.md` en premier.
2. Lire `data/cro_criteria_v2.json`, `data/growth_refs.json`, `data/audit_ocni_v2.json`.
3. Vérifier les outils dispo : `ToolSearch("apify")` et `ToolSearch("scrape crawler")`.
4. Si Apify actif → lancer `Website Content Crawler` sur `https://ocnifactory.com` (startUrls, maxCrawlPages: 1, renderJs: true) et récupérer texte + structure.
5. Sinon → demander à Mathis de cliquer "Connect" sur l'extension Claude in Chrome, puis `tabs_context_mcp` + `navigate(https://ocnifactory.com)` + `get_page_text` + `read_page`.
6. Refaire l'audit OCNI V2 **sourcé à 100%** (plus aucun `unverified`) → écraser `data/audit_ocni_v2.json`.
7. Faire valider par Mathis.
8. Injecter dans le prototype V5.2 : update `data/audits.json` (shape OCNI enrichie V2), rebuild `data/_proto_data_blob.json`, re-injecter dans `prototype/GrowthCRO-Prototype-V5.html` (copier en V5.2 ou garder V5.1 selon préférence Mathis).
9. Mettre à jour la grille côté prototype : le JS utilise actuellement `categories` avec 5 clés legacy — il faut adapter pour afficher les 6 piliers V2 (`coherence`, `hero`, `persuasion`, `ux`, `tech`, `psycho`) et la max /117 (au lieu de /90).
10. Mettre à jour HISTORY.md + PROJECT_MEMORY.md avec le milestone "V5.2 final — OCNI live-sourced + prototype injecté".

---

## Phase 8 — Audit Japhy V2 + pivot "Playbook unifié" (2026-04-08)

**Contexte du pivot :** Après le blocage Apify sur OCNI (egress proxy refusé par l'origine, pas un bug Apify), bascule sur un audit Japhy pour valider le connecteur. Résultat : Japhy scoré 70/117 (60%) en live-sourcing Apify, avec 39 criteriaDetails, 6 problèmes, 4 wins, 3 vagues, 5 rewrites, 5 benchmarks. Fichier : `data/audit_japhy_v2.json`. Bug corrigé en vol : pilier Persuasion incohérent (13 déclaré vs 15 sommé) → corrigé à 15, total passé de 63 à 70, pct de 54% à 60%.

**Pivot stratégique demandé par Mathis :** arrêter de courir en parallèle sur tous les modules. Travailler **bloc par bloc**, validé humainement à chaque étape. Focus actuel = module **Audit + Recos**. Objectif : machine imparable, apprentissage continu, excellente sur tous types de clients/sites/produits/LPs. Question posée sur Supabase vs alternatives, et sur GitHub (concurrent ou pas ?).

**Réponse archi stockage :** Supabase = meilleure solution pragmatique (Postgres managé + auth + storage + realtime + RLS + edge functions). Alternatives évaluées : Firebase (NoSQL, lock-in Google), Neon (Postgres pur, pas de storage/auth), PlanetScale (MySQL, pas de vecteurs pgvector), Airtable (pas une DB, API lente, pas de jointures). **GitHub n'est PAS un concurrent** : GitHub = versioning code, Supabase = DB live. Complémentaires. Décision : on reste JSON+localStorage jusqu'à ce que la V3 soit figée, puis migration Supabase.

**Étape 0 — Inventaire exhaustif du savoir CRO existant (2026-04-08) :**

**Découverte majeure :** 4 couches de savoir CRO parallèles jamais fusionnées :

1. **Couche A — Notion database "Checklist CRO"** (id `3207148e-95a5-80b0-aa86-c81cc9c40e71`, parent path : Réunion 13/03/26 → Apprentissage Nobo → CRM Clients → Nobo). ~100 critères opérationnels granulaires. Schema : Nom (title), Priorité (Moyenne/Forte/Très forte), Coût (Faible/Moyen/Élevé), Sélectionner (Top/OK/Critique), Quelles pages ? (Toutes/Home/PDP/Funnel/Catégories/Footer/Menu). Instanciée sur au moins 3 clients : **Checklist CRO - OCNI** (id `3227148e-95a5-80ec-a0f2-c908f8bc720e`), **Checklist CRO Travelbase** (id `3347148e-95a5-80b4-af17-e177caa74bc7`), + &TheGreen. Chaque instance client est une sous-database liée. **C'est l'ADN CRO originel de Growth Society, jamais branché à GrowthCRO.**

2. **Couche B — `skills/cro-auditor/`** (339 lignes SKILL.md + 5 refs). Méthodologie complète déjà formalisée : Phase 0 Qualification → Phase 1 Collecte → Phase 2 Scoring → Phase 3 Rapport (6 blocs) → Phase 4 Recos Détaillées → Phase 5 Livrable → Phase 6 Apprentissage Automatique, 15 règles transversales, Quick Commands. Références : `audit_criteria.md` (1084 lignes, 30 critères CRO formalisés /90, 6 psycho évoqués mais NON formalisés), `memory.md` (100 lignes, 1 audit validé : &TheGreen 40.5/108 du 2026-04-04), `cro_principles.md` (1075 lignes, 11 erreurs classiques + 9 principes fondamentaux), `reco_engine.md` (2372 lignes, matrice Impact×Effort 5×5, formule `Score = Impact × (6-Effort)`, P1/P2/P3, templates graduées par catégorie), `reco_templates.md` (2252 lignes, 4 formats : Dashboard HTML / PDF-DOCX / Brief GSG / adaptation rules).

3. **Couche C — `data/cro_criteria_v2.json`** (146 lignes). Grille V2 /117, 6 piliers, 39 critères, 9 page types, 10 business categories, `pageTypeWeighting`. Structure moderne mais critères encore génériques, ne descendent pas à la granularité Notion.

4. **Couche D — Architecture + prototype** : `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (895 lignes), `architecture/ROUTING_AND_DATAFLOW_V1.md` (246 lignes), 30 Growth Refs, prototype V5.2, audit_japhy_v2.json live-sourced.

**6 règles implicites extraites du corpus (les axiomes) :**
1. **Falsifiabilité** — un critère se prouve visuellement ou textuellement, jamais en prose vague.
2. **Discrétisation ternaire** — Top (3) / OK (1.5) / Critique (0). Jamais continu.
3. **Contextualité** — un critère sans page-type n'existe pas. Champ obligatoire partout.
4. **Priorisation ROI** — Impact × Effort pilote l'action, pas le score absolu. D'où Quick Wins / Structural / Creative.
5. **Livrable actionnable** — tout audit produit `before → after → why` en rewrite. Sinon pas d'audit.
6. **Double boucle d'apprentissage** — apprendre des erreurs ET des succès. `memory_validated.md` + `memory_corrections.md`.

**Angles morts identifiés :**
- 6 critères psycho non formalisés en grille (vivent en principes dans cro_principles.md).
- Aucun pont Notion Checklist ↔ cro_criteria_v2.json.
- Aucun pont audits Notion clients (OCNI/Travelbase/&TheGreen) ↔ memory.md du skill.
- Aucune pondération business-category (seulement page-type).
- Aucun mécanisme de "critère killer" (plafonnage de score).
- Aucun versioning des critères.

**Décision architecture V3 (playbook unifié) :**
- **Couche 1 — Axiomes** : 6 règles non-négociables (fichier `playbook/AXIOMES.md`).
- **Couche 2 — Grille V3 /117** : fusion V1×V2×Notion, ~60 critères enrichis (contre 39 actuels), avec `id`, `pillar`, `label`, `pageTypes[]`, `businessCategories[]`, `weight`, `scoring` ternaire falsifiable, `checkMethod`, `examples[]`, `antiPatterns[]`, `killer`, `notionRefId`, `principleRefs[]`, `version`, `updatedAt`. Ajout `businessCategoryWeighting`.
- **Couche 3 — Moteur reco + apprentissage** : ~50 reco templates mappés 1:1 aux critères V3, priorisation P0/P1/P2 (harmonisation SPECS), `memory_validated.md` + `memory_corrections.md`, fonction `syncNotionChecklist(clientId)`.

**Plan d'attaque validé :** bloc par bloc, pilier par pilier, 4 étapes par bloc (extraction brute → formalisation V3 → validation humaine critère par critère → application sur 2 cas). Ordre : **Bloc 1 Hero /18** → Bloc 2 Persuasion /24 → Bloc 3 UX /24 → Bloc 4 Cohérence /18 → Bloc 5 Psycho /18 → Bloc 6 Tech /15. Validation Mathis : "go on attaque" (2026-04-08).

**Livrables sauvegardés pour éviter la perte de contexte cross-session :**
- `playbook/AXIOMES.md` — les 6 règles non-négociables
- `playbook/README.md` — architecture V3 + plan bloc par bloc
- `playbook/bloc_1_hero_DRAFT.json` — Bloc 1 Hero V3 formalisé (6 critères)
- Cette section HISTORY.md (Phase 8)
- PROJECT_MEMORY.md mis à jour avec état Phase 8

**Bloc 1 Hero — validation Mathis (2026-04-08) :**
- Grille Hero V3 validée intégralement par Mathis après test en direct sur Japhy.
- Décisions actées :
  - **Fusion CTA-bénéfice dans hero_03 CONSERVÉE** (option A). Le texte du CTA est jugé dans le pilier Hero, pas en Persuasion. Raison : un CTA visible avec un mauvais texte = mauvais CTA, c'est l'expérience utilisateur réelle. Pas de double-comptage en Persuasion.
  - **Scoring ternaire plus sévère dans le haut du tableau ASSUMÉ** : "1.5 ou 3, pas d'entre-deux".
  - **hero_06 killer calibré correctement** (ne s'est pas déclenché sur Japhy qui a 1 CTA primaire propre).
  - **businessCategoryWeighting validé** (beauty/formation 1.2, luxe 0.9).
  - **Anti-patterns V3 validés** (AI slop, trust badges SSL en hero, autoplay carrousel, bannière promo > H1).
- Résultat Japhy Hero V3 : **7.5/18** (vs 8/18 en V2). Diagnostic qualitatif : 5 OK + 1 Critique (preuve sociale ATF). Plus lisible que V2.
- Demande Mathis à traiter : **capacité de screen les parties visuelles auditées (desktop + mobile) et re-analyse autonome des screenshots pour vérifier les jugements visuels**. À documenter comme feature attendue du futur moteur d'audit.

**Phase 8.1 — Screenshots Apify + découverte des erreurs markdown (2026-04-08, suite) :**

Capture Apify réussie via `apify~puppeteer-scraper` custom pageFunction. Screenshots stockés dans `data/screenshots/japhy/` : desktop_asis_fold, desktop_clean_fold, desktop_clean_full, mobile_asis_fold, mobile_clean_fold, mobile_clean_full (coût ~0.03$, ~65s end-to-end). Problèmes résolus en vol : (1) run 1 timeout 60s avec `networkidle2` → corrigé en `domcontentloaded` + `navigationTimeoutSecs:120` ; (2) dataset Apify cap sur base64 → migré vers Key-Value Store ; (3) desktop_fold capturé à mi-page → corrigé avec `page.evaluate(() => window.scrollTo(0,0))` avant screenshot. Script final dans `/tmp/apify_screenshot3.py` (capture mobile+desktop, as-is+clean, auto-click cookies).

**Découverte majeure : 4 critères Hero sur 6 étaient FAUX en scoring markdown-only.** La re-analyse visuelle a révélé :

- **hero_01 H1 :** le vrai H1 est *"L'alimentation experte qui change la vie de nos chiens et chats"* (pas *"L'alimentation sur-mesure pour chiens et chats"* comme extrait par le markdown Apify — probablement un meta title ou H2 confondu). **Score markdown 1.5/3 → score visuel 3/3** (+1.5). Bénéfice + cible pleins, différenciateur implicite "experte".
- **hero_03 CTA :** le vrai label est **"Créer son menu 2mn"** avec icône horloge (pas "Je découvre" comme deviné). Verbe + bénéfice temps, excellent. **Score markdown 1.5/3 → visuel 3/3** (+1.5). Cause : markdown Apify renvoyait `<a>[](url)` sans texte car le label est dans un span enfant non linéarisé.
- **hero_04 Visuel :** chat roux + dalmatien mangeant dans cuisine, **2 packs Japhy avec prénoms Nala/Enzo visibles** (démonstration visuelle de la personnalisation sans un mot). **Score markdown 1.5/3 → visuel 3/3** (+1.5). Verdict : on ne peut PAS juger un visuel depuis du markdown.
- **hero_05 Preuve sociale :** widget Trustpilot *"Excellent ★★★★½ — 14 100 avis"* visible ATF mobile ET desktop, juste sous le CTA. **Score markdown 0/3 (Critique) → visuel 3/3 (Top)** (+3.0) ← PLUS GROS ÉCART. Cause : widget Trustpilot chargé en JS après DOM, invisible au crawler cheerio/markdown.
- **hero_02 et hero_06 :** notes inchangées (1.5/3 chacun).

**Total Hero V3 Japhy : 7.5/18 (markdown) → 15/18 (visuel).** Diagnostic retourné : Japhy n'est PAS un hero moyen, c'est un **hero excellent saboté par une pop-up cookies intrusive** qui masque la preuve sociale et introduit 2 CTAs en concurrence avec "Créer son menu" pendant les 10-15 premières secondes. Le vrai insight livrable devient : *"Quick win = refondre la bannière cookies en slide-in bas (type Axeptio) plutôt que modal XXL."*

**Validation Mathis des Q1/Q2/Q3 :**
- **Q1 validé :** scoring 15/18 adopté.
- **Q2 validé :** ajouter un critère overlay/popup intrusif. Décision : le créer comme **critère transverse UX `ux_09 Overlay non-essentiel intrusif ATF`** dans le Bloc 3, plutôt que d'élargir hero_06. Raison : les overlays touchent aussi checkout, PDP, LP, pas juste le Hero.
- **Q3 validé :** relancer l'audit Japhy complet avec screenshots comme cas de référence propre.

**Challenge Mathis sur la méthode d'extraction :** "les screens c'est bien pour le rendu et pour toi vérifier, mais y'a pas mieux que ça pour récupérer complètement et justement les URLs et données d'un site ? Quitte à développer un skill." Mathis a 100% raison. Diagnostic livré :

**Diagnostic erreurs markdown** — le problème n'est pas Apify mais le mauvais actor utilisé (`website-content-crawler` + `cheerio-scraper` = linéariseurs RAG, pas auditeurs). 4 défauts : (1) cheerio = HTML statique pré-JS, widgets JS invisibles ; (2) content-crawler linéarise en markdown et perd hiérarchie DOM, labels boutons, iframes, overlays, CSS, visibilité ; (3) pas de séparation mobile/desktop ; (4) pas de as-is vs clean.

**Solution validée par Mathis : skill `site-capture` V1.** Un seul appel `apify~puppeteer-scraper` avec pageFunction costaud qui retourne :

- **A. DOM rendu réel** : HTML post-JS, innerText visible filtré (`offsetParent !== null`), séparation 375/1440.
- **B. Structure sémantique exacte** : H1/H2/H3 + positionY, buttons/links + aria-label + position + contraste + visibilité, images + alt + poids + format, iframes (où vivent les widgets tierces).
- **C. Éléments CRO détectés par heuristique** : fold 1 réel, CTA primaire (bouton le plus contrasté + grand + ATF), widgets preuve sociale (Trustpilot/Yotpo/Judge.me/Google/Stamped/Reviews.io/Loox/Okendo par signature DOM et iframe), overlays (position:fixed + z-index>1000 + visible ATF), logos presse (sections "as seen in"/"featured in").
- **D. Performance mesurée** : LCP, CLS, FCP, TTFB via PerformanceObserver in-page, poids total, requêtes, contrastes WCAG ATF, erreurs console, tracking scripts détectés (GA/GTM/Meta/TikTok).
- **E. Screenshots** : 4 par viewport × 2 = 8 PNG (asis_fold, clean_fold, clean_full, scroll_sequence mobile + desktop) dans KV store.
- **F. Métadonnées** : title, meta, OG, Twitter, canonical, lang, JSON-LD schema.org, robots.txt, sitemap.xml, headers HTTP, CDN détecté.

**Architecture skill `site-capture` validée :**
```
skills/site-capture/
├── SKILL.md                    # Quand déclencher, contrats input/output
├── references/
│   ├── apify_page_function.js  # pageFunction Playwright complète
│   ├── heuristics.md           # Détection CTA/widgets/overlays
│   └── capture_schema.json     # Shape SiteCapture
└── scripts/
    ├── run_capture.py          # Orchestrateur Apify
    └── analyze_capture.py      # Helpers get_hero(), get_cta_primary()
```

**Contrat d'interface :** tout audit V3 commence par `capture = SiteCapture(url)`. Output = `data/captures/<client>-<date>.json` + 8 PNG à côté. **Source de vérité unique** pour tous les audits. Si la grille change, on re-score sans re-capturer.

**Alternatives écartées :** Firecrawl (pas de pageFunction custom), ScrapingBee/ScraperAPI (juste proxy+JS), Browserless (doublon avec Apify), Lighthouse CLI (lourd, phase 2), HTTrack (hors scope). **PageSpeed Insights API** gardée en complément gratuit pour tech_01/tech_02 (vraies CWV terrain CrUX).

**Coût/temps :** ~0.01-0.03$ par capture, 60-90s end-to-end, scalable 30 clients en ~15 min.

**Plan validé par Mathis :**
1. Construire skill `site-capture` (~45 min)
2. L'appliquer à Japhy → `SiteCapture` propre
3. Re-scorer Hero V3 depuis SiteCapture (vérifier que ça reproduit le scoring visuel 15/18)
4. Enchaîner Bloc 2 Persuasion avec la bonne méthode
5. Plus tard : re-capturer les 30 clients d'un coup

**Token Apify actif en mémoire :** `[REDACTED - see .env]` (toujours valide, a fait tourner Japhy 2x, ~90M repas de compute units utilisés).

**État des décisions Bloc 1 Hero à ne pas perdre :**
- Grille V3 Hero : 6 critères × 3 pts = 18 pts, scoring ternaire Top(3)/OK(1.5)/Critique(0)
- hero_03 fusion CTA-bénéfice VALIDÉE (option A conservée)
- hero_06 killer validé (< 2 questions ET ratio 1:1 cassé simultanément → plafond 6/18)
- `businessCategoryWeighting` validé (beauty/formation 1.2, luxe 0.9)
- Anti-patterns V3 validés (AI slop, trust badges SSL, autoplay carrousel, bannière promo > H1)
- `ux_09 Overlay non-essentiel intrusif ATF` à créer au Bloc 3 (décision Q2)
- Screenshots obligatoires pour tout audit V3 à partir de maintenant (conséquence Axiome 1)

**Handoff Phase 8.1 → 8.2 :**
Prochaine action = construction du skill `site-capture` (invoquer `skill-creator`, puis créer l'arborescence sous `skills/site-capture/`, écrire SKILL.md + pageFunction + scripts orchestrateurs). Ensuite appliquer à Japhy, re-scorer Hero V3, comparer au scoring visuel 15/18, puis enchaîner Bloc 2 Persuasion.

---

## Phase 8.2 — Site-capture validé + Bloc 1 Hero V3 LOCKED (2026-04-09)

**Milestone : skill `site-capture` opérationnel end-to-end sur Japhy, Hero V3 automatiquement reproduit en 16.5/18 (vs 15/18 baseline visuelle).**

### Ce qui a été construit
- `skills/site-capture/` : SKILL.md, `references/apify_page_function.js` (Puppeteer custom pageFunction), `scripts/run_capture.py` (orchestrateur Apify), `scripts/score_hero.py` (scorer Hero V3 auto lisant capture.json).
- Philosophie actée : **screenshots = preuve** (dossier audit + verification humaine), **DOM rendu = source de vérité** pour le scoring.
- Cookie handling : **détection AS-IS → clic accept → re-check → force-remove → tag `removalMethod`**. But : capture workable dans tous les cas et détection fiable du CMP.

### Refinements itératifs appliqués au skill
1. Timeouts Crawlee/Puppeteer forcés (pageLoadTimeoutSecs 180, pageFunctionTimeoutSecs 300, requestHandlerTimeoutSecs 480, `setDefaultNavigationTimeout(120000)` in pageFunction).
2. `page.waitForTimeout` remplacé partout par `new Promise(r => setTimeout(r, ms))`.
3. Shadow DOM walker générateur (`walkAll()`) pour traverser les CMPs custom.
4. CMP fingerprinting 9 plateformes (Didomi, OneTrust, Cookiebot, Axeptio, Tarteaucitron, Osano, Quantcast, Iubenda, CookieYes).
5. Cookie banner detection : find accept buttons by text → walk up to smallest ancestor containing cookie keyword + assez large.
6. CTA primary scoring multi-signaux 0-100 + disqualifiers.
7. Regex actionVerb supporte apostrophes droites ET courbes (fix "J'essaie").
8. `effectiveBg()` walk parent chain pour contraste non-transparent.
9. `contrastText` comme proxy fiable (contrastVsPage souvent cassé par wrappers transparents).
10. `score_hero.py` dédup CTAs par href avant check focus ratio 1:1 (fix faux conflit sticky-header vs hero).

### Résultat Japhy (capture.json → score_hero.json)
- **Bloc 1 Hero : 16.5/18** (raw 16.5, no killer)
- H1 : "L'alimentation experte qui change la vie de nos chiens et chats" — 3/3 signaux (cible+bénéfice+diff), 11 mots
- CTA primary : "Créer son menu" → /profile-builder/, 244×48, contrastText 17.9, primaryScore 60
- Cookie banner : **Axeptio détecté par fingerprint**, coverage 11%, flag `no-reject-all-button-cnil-risk` automatique
- Widget Trustpilot détecté
- hero_06 = 1.5/3 : 3/3 questions + focus OK après dédup, -1.5 pour distraction cookie (2 CTAs concurrents)

### Learnings portés en dur dans le playbook
- `playbook/bloc_1_hero_v3.json` promoted from DRAFT → **status: locked**, avec `validatedOn: japhy` et `automationNotes` (règles du scorer auto).
- `playbook/LEARNINGS.md` créé : log chronologique des apprentissages (double boucle d'apprentissage, axiome 6). 6 apprentissages Japhy consolidés.
- `data/captures/japhy/audit_report.md` : template canonique du format livrable audit client (markdown structuré).
- Reco prioritaire détectée automatiquement : "Ajouter bouton Refuser tout au cookie banner Axeptio (CNIL + CRO)".

### Décisions Mathis validées pendant la phase
- Ordre des étapes : (3) scorer Japhy auto → (2) capturer les 30 clients → (1) attaquer Bloc 2 Persuasion. Tout validé séquentiellement.
- Philosophie : screenshots pour preuve, pas pour scoring.
- Cookie handling "remove first to detect" → implémenté en remove-if-needed (plus robuste que systematic remove).

**Handoff Phase 8.2 → 8.3 :**
Prochaine action = capture batch des 30 clients Growth Society via `scripts/run_capture.py` en boucle. Le scorer Hero V3 s'appliquera automatiquement sur chaque `capture.json`. Une fois les 30 scorés, validation Mathis puis attaque du Bloc 2 Persuasion /24.

---

## Phase 8.2bis — Batch 28/31 + questionnement outil de capture (2026-04-09)

### Batch capture complété (28 clients sur 31)

- 6 URLs manquantes complétées via WebSearch : mium_lab (miumlab.com), stan (stan.store), reveal (reveal.co), jomarine (jomarine.be), massena_formation (massena-formations.fr), lea_hassid (fridzie.com — son agence). Validées par Mathis.
- `skills/site-capture/scripts/batch_capture.py` créé (orchestrateur séquentiel, skip auto, log incrémental dans `data/captures/_batch_log.json`).
- Runs par chunks de 3 (contrainte timeout Bash 10min).
- **3 sites résistent au crawl Apify de façon reproductible** : everever.fr, jomarine.be, fichetgroupe.fr. Pattern "capture record missing" (actor SUCCEEDED mais pageFunction n'a pas pushData). Cause possiblement multiple : timeout structural, anti-bot Cloudflare, erreur dans pageFunction sur DOM inattendu.

### Scoreboard Bloc 1 Hero (28/31, `data/captures/_scoreboard.md`)

**Top 5** : Japhy 16.5 · Wespriing 13.5 · GeoRide 12 · Détective Box 10.5 · Edone Paris / Kaiju / Seoni 9
**Moyenne 6.4/18 (35 %)**, médiane 6, top quartile ≥9 (7 clients), bottom quartile ≤4.5 (9 clients).
**Insight stratégique** : Japhy est outlier positif, 22/28 clients sont sous 9/18 → **le Hero est le quick-win CRO #1 pour le portefeuille Growth Society**. Opportunité business claire pour pitcher des refontes Hero.

Dernier classé : Léa Hassid (Fridzie) 1.5/18 — à valider que c'est bien le bon site pour elle chez Growth Society.

### Questionnement de direction (décision Mathis 2026-04-09)

Mathis a challengé la solution "proxy résidentiel Apify + Claude in Chrome" comme trop étroite. Demande : "N'oublie pas que je veux pas une solution temporaire, le but c'est de cadrer définitivement et de valider un module et ses skills et que ce soit imparable ça marche à chaque coup."

Analyse réalisée : panorama de 10 options (Apify, Browserless, Scrapfly, ZenRows, Bright Data, Playwright local, Puppeteer-extra+stealth, Claude in Chrome, Firecrawl, fetch+jsdom), 7 familles d'échec distinctes (WAF réseau, bot detection JS, geo/locale, rate limit, timeout structural, erreur applicative pageFunction, Crawlee wrapping).

**Architecture cible proposée** (en attente validation Mathis pour Phase 8.3) :
- **Niveau 1 — Browserless.io** en défaut (remplace Apify Puppeteer-scraper). Plus rapide, plus direct, pas de Crawlee wrapping, on envoie notre pageFunction telle quelle.
- **Niveau 2 — Scrapfly** fallback pour sites anti-bot (Cloudflare/DataDome/Akamai/PerimeterX tous solvés auto via ASP). Résidentiel FR natif.
- **Niveau 3 — Claude in Chrome** escape hatch manuel pour les rarissimes cas qui résistent même à Scrapfly.
- Apify reste dispo comme niveau 1.5 de secours mais n'est plus le défaut.
- Contrat unique `capture(url, options) → capture.json` partagé entre backends, scorer Hero V3 s'en fiche du backend utilisé, chaque résultat tagué `capturedBy` + `confidence`.
- Dossier `skills/site-capture/references/backends/` avec un fichier par backend + `backend_decision_matrix.md`.
- Coût estimé 30 clients/mois : ~$35 (Browserless Starter $20 + Scrapfly fallback $15).

**Pourquoi cette architecture est "imparable"** : chaque backend est remplaçable sans toucher au scorer, cascade garantit un résultat, les apprentissages nourrissent LEARNINGS.md (quel backend marche sur quel type de site), pas de lock-in.

**Décision en attente** : Mathis doit choisir entre (A) full refactor multi-backend Browserless+Scrapfly+ClaudeInChrome, (B) consolidation Apify-only avec puppeteer-extra-stealth + residential proxy. Recommandation claude = (A) car objectivement supérieure sur le critère "imparable".

**Prochaine action après validation** : créer comptes Browserless + Scrapfly (free tiers), refactor `skills/site-capture/` en multi-backend, retester les 3 sites résistants à travers la cascade, valider régression sur 2-3 sites déjà capturés, locker v1.0 du skill, passer au Bloc 2 Persuasion.

---

## Phase 8.2ter — Lock skill site-capture v1.0.0 (2026-04-09, fin de journée)

**Contexte** : Après Phase 8.2bis (batch 28/31 + panorama 10 outils + cascade 6 niveaux proposée), Mathis a tranché : garder **Apify-only** (pas de Browserless/Scrapfly/Claude-in-Chrome, non reproductibles), cascade 6 niveaux implémentée dans `run_capture.py` via `LEVEL_CONFIG`.

**Vérifications concrètes faites cette session** :
- Compte Apify vérifié via `GET /users/me` : plan **FREE**, username `Growth_Society`
- Proxy groups via console : Datacenter `BUYPROXIES94952` (5 IPs, inclus), **RESIDENTIAL** ($8/GB, "Too many to count" IPs, pay-as-you-go actif même en FREE)
- Tests cascade sur everever.fr : level 1 (datacenter) → ERR_TUNNEL_CONNECTION_FAILED, level 2 (residential FR) → idem 11 retries, level 3 (Playwright Firefox + residential) → run SUCCEEDED mais pas de record (pageFunction Puppeteer incompatible Playwright API), level 4 (Puppeteer + slowMo + residential) → idem tunnel errors 11 retries
- **Conclusion** : pool RESIDENTIAL FR du plan FREE Apify est entièrement cramé sur everever.fr par le WAF (probablement DataDome ou Cloudflare Bot Fight). Ne se débloquera JAMAIS via Apify sur plan FREE. Même diagnostic attendu pour fichetgroupe.fr.

**Décision Mathis** : skip everever + fichet, les documenter comme "waf_resistant_unreachable_apify_free" dans `_batch_log.json` avec `nextLevelRequired: 5`, ne PAS brûler plus de CU dessus, passer direct au Bloc 2.

**Refactor pageFunction niveau 0 défensif** (apify_page_function.js) :
- Backup v1.0.0 sauvegardé dans `apify_page_function.v1.0.backup.js`
- Flow principal (lignes 437-502) réécrit avec :
  - `flushCapture()` helper qui push un snapshot `__capture` à chaque étape (0.0 → 0.3 → 0.7 → 1.0)
  - Initial flush immédiat avec `completeness: 0.0` → garantit qu'un record existe TOUJOURS, même si tout crash
  - Try/catch par section : settle, desktop_asis_fold, mobile_asis_fold, cookie_detect, cookie_dismiss, extract, desktop_clean_fold, desktop_clean_full, mobile_clean_fold, mobile_clean_full, html
  - `safeCapture()` helper qui isole les erreurs screenshot dans `errors[]`
  - `stagesCompleted[]` tracking
  - `meta.completeness` computed à la fin (1.0 si 6 screenshots + hero + html, dégradé sinon)
  - `meta.errors[]` avec `{stage, msg}` pour chaque échec partiel
- Résultat : plus JAMAIS de "capture record missing" silencieux — les sites qui échouent partiellement laissent au moins une trace exploitable pour diagnostic.

**Régression Japhy level 1** (post-refactor) :
- Run Apify SUCCEEDED, 6/6 screenshots téléchargés (2092, 594, 2089, 3683, 594, 1330 KB)
- Score auto : **16.5/18** (baseline maintenu au pixel près)
- `completeness: 1.0`, stages: 11/11, errors: [] → pageFunction défensive validée zéro régression

**Documentation** : `skills/site-capture/references/backend_cascade.md` créée, 6 niveaux détaillés avec failure families observées (7 familles), cas documentés du portefeuille (everever, fichet, jomarine, japhy), règle opérateur one-liner.

**Lock site-capture v1.0.0** : ajouté au frontmatter SKILL.md (version, status: locked, lockedAt, lockedBy, contract garanti, backlog v1.1). Skill production-ready pour le portefeuille Growth Society.

**État final batch** : 28/31 scorés en level 1 datacenter, 2 WAF-resistant (everever, fichet) en backlog level 5, 1 CMP-blocked (jomarine 1.5/18 KILLER) en backlog level 0.5 CMP bypass.

**Next** : **Bloc 2 Persuasion /24** — ouverture immédiate, même méthodo que Bloc 1 (playbook draft → critères scorables → baseline Japhy → automation score_persuasion.py → validation → lock).

---

## Phase 8.3 — Bloc 2 Persuasion /24 (2026-04-09)

### Méthodo sourcing rigoureuse (rappel user)

Moment important : après le lock site-capture, j'ai proposé un draft Bloc 2 trop rapidement "de tête". Mathis m'a corrigé fermement : *"Attends mais on a établi toute une liste de critères en blocs basé la dessus ! pas juste de tête de ton côté, mais avec la doc CRO notion tes connaissances, l'apprentissage continu etc. [...] on a passé des dizaines d'heure à construire ça, avec la DOC + mes inputs + tes recherches + les meilleurs sites + de la doc en plus sur la psychologie la persuasion etc."*

→ Vérification immédiate : Bloc 1 `hero_01` contient bien `notionRefId: "3207148e-95a5-81ac-a349-d87342dec780"` → confirmation que Bloc 1 a été sourcé rigoureusement. Reconnaissance de l'erreur, pivot vers le pipeline de sourcing complet pour Bloc 2.

### Pipeline de sourcing exécuté (5 sources internes)

1. **Notion CRO doc** — fetchée via `notion-fetch` sur `https://www.notion.so/growth-society/Doc-Process-suivi-CRO-Mission-Media-buying-2e67148e95a5805b8fafe8531ad5159e`. Fichier trop gros (453k chars) → déléguation subagent général pour extraction exhaustive des sections persuasion. Retour : sections Bénéfices 🟢 / Preuves sociales 🟢 / FAQ 🟢 / Comparaison 🟠 / Personae / Reason Why / Before-After. Règles Growth Society verbatim capturées.
2. **`audit_criteria.md` V1 Catégorie 3** — 7 critères /21 (3.1 hiérarchie narrative / 3.2 preuves dispersées / 3.3 FAQ conversion / 3.4 objections / 3.5 claims vérifiables / 3.6 urgence crédible / 3.7 CTA bénéfice). Décision : 3.6 et 3.7 migrent vers autres blocs (urgence → Psycho, CTA → Hero déjà), 3.1 partiellement vers Cohérence.
3. **`cro_criteria_v2.json` pillar persuasion** — 8 critères V2 per_01→per_08 déjà cadrés (bénéfices, storytelling, objections, preuves, témoignages, FAQ, ton, anti-jargon). **On conserve cette structure en V3.**
4. **`cro_principles.md`** — §2.4 Hiérarchie Preuve Sociale (vidéo > avis vérifiés > screenshots > chiffres > logos > badges > anonyme), §2.9 Benefit Laddering (Feature→Avantage→Bénéfice→Transformation + test "Et alors ?"), §2.10 Niveaux de conscience Schwartz (unaware→most aware), §2.5.1 Friction cognitive (headline 15+ mots, jargon, multi-VP).
5. **`audit_japhy_v2.json` criteriaDetails_persuasion** — baseline Japhy V2 = **15/24** avec détails verbatim par critère :
   - per_01 Bénéfices = 2 (ok, 80% des formulations restent centrées produit)
   - per_02 Storytelling = 1 (weak, aucune histoire fondatrice)
   - per_03 Objections = 2 (ok, FAQ couvre mais manque objection prix)
   - per_04 Preuves = 2 (ok, '45M repas' + '80% protéines' mais manque études/before-after)
   - per_05 Témoignages = 2 (ok, Dr Masson + Tony Silvestre nommés mais pas de vidéo)
   - per_06 FAQ = **3 (TOP)** — "meilleure section de la page", 9 Q toutes business
   - per_07 Ton = 2 (ok, chaleureux mais trop lisse "DTC moyen")
   - per_08 Anti-jargon = 1 (weak, "créée avec soin / haut niveau d'exigence / plusieurs dizaines de recettes" = DTC 2018 template)

### Synthèse → `playbook/bloc_2_sources.md`

Document consolidé écrit avec : 5 sources détaillées verbatim, tableau V1 7 critères, tableau V2 8 critères, hiérarchie preuve sociale tabulée, Benefit Laddering, Schwartz, baseline Japhy complet, **5 décisions de design**.

### Décisions de design D1-D5 — validées user 2026-04-09

Présentées au user en 3 vraies décisions à trancher :

**D1 — 8 critères × 3 pts = /24** (ajouter per_08 anti-jargon à la V1 7-critères). Justification : sur Japhy, per_08 a isolé le pattern DTC 2018 template ("créée avec soin", etc.) que les 7 autres critères ne capturaient pas. **User : validé.**

**D2 — Pondération pageType activée** (coefficients 0.7/1/1.2/1.3 par critère × type de page, total renormalisé /24). Exemples : storytelling (per_02) pèse fort sur lp_sales/advertorial, peu sur PDP/lp_leadgen. FAQ (per_06) pèse fort sur PDP/pricing/lp_sales, peu sur home/advertorial. **User : validé.**

**D3 — 3 killers** :
- `per_01 critical` (page 100% features zéro outcome) → cap Bloc 2 à **8/24**
- `per_04 critical` (zéro preuve concrète) → cap Bloc 2 à **10/24**
- `per_08 critical` (jargon creux en volume) → cap Bloc 2 à **20/24** (pénalité non éliminatoire)
- **User : validé.**

**D4** — checkMethod par critère (textual / heuristic / visual / combinaisons) — technique, pas de choix user.
**D5** — dépendance `capture.json` v1.0 avec fallback regex si `structure.faqs` ou `socialProof.testimonials` absents — technique.

### Draft `playbook/bloc_2_persuasion_v3.json` écrit

Structure identique à `bloc_1_hero_v3.json` (pattern répliqué). Contenu :

- `max: 24`, `version: 3.0.0-draft`, `status: draft`, `sourcesConsolidated: [...]`
- `designDecisions` objet avec D1/D2/D3/D4/D5 + timestamp user validation
- `pageTypeWeights` : matrice complète 8 critères × 9 pageTypes
- `normalization` : formule `(total_pondéré / Σ(3 × weight_i)) × 24`
- `killers` : 3 règles formalisées
- 8 `criteria` complets avec pour chacun :
  - `label`, `pillar`, `weight`, `pageTypes`, `businessCategories`, `checkMethod`
  - `scoring.top` / `scoring.ok` / `scoring.critical` verbatim détaillés (3 paragraphes chacun)
  - `examples.top` / `examples.ok` / `examples.critical` (exemples réels Japhy + top class)
  - `antiPatterns` array
  - `killer` flag + `killerRule` le cas échéant
  - `notionRefId`, `principleRefs`, `v1Mapping`, `v2Mapping`
- Spécifique per_08 : `blacklistRegex` array de 11 patterns (créée avec soin, avec passion, haut niveau d'exigence, point d'honneur, plusieurs dizaines de, solution innovante, expertise reconnue, leader du marché, qualité irréprochable, équipe passionnée, haut de gamme)
- `automationNotes.rules` : 8 règles de scoring par critère pour `score_persuasion.py`
- `backlog` v1.1/v2.0 : ton of voice ads via Meta Ads Library, detection before/after visuelle, blacklist multi-langue, dérivation Schwartz depuis URL ads

### Prochaines étapes Phase 8.3

1. ⏳ **Baseline Japhy V3 manuel** : re-scorer Japhy avec la grille V3 (8 critères + pondération home + killers) et vérifier cohérence avec baseline V2 15/24 (tolérance ±1 pt)
2. ⏳ **`skills/site-capture/scripts/score_persuasion.py`** : scorer auto consommant `capture.json`
3. ⏳ **Validation 3 sites contrastés** : Japhy (DTC) + OCNI (advertorial) + 1 SaaS B2B — écart manuel vs auto ≤ 2 pts
4. ⏳ **Lock `bloc_2_persuasion_v3.json` v1.0** avec frontmatter status:locked + lockedAt + lockedBy
5. ⏳ Ouverture Bloc 3 UX /24

---

## Phase 9 — Audit Fondamental V15.2 + Plan Semantic Scorer (2026-04-17)

### Contexte
Mathis, très insatisfait après des centaines d'heures de dev, a uploadé Plan V16.pdf (45 pages documentant toutes les frustrations V15) + une analyse Gemini indépendante du projet. Résultat : audit fondamental du système complet.

### Audit Fondamental V15.2 — TERMINÉ
Document `AUDIT_FONDAMENTAL_V15.md` : confrontation systématique doctrine CRO (PDF 168K + Notion complet 47 critères) vs code réel vs données terrain (75 clients × 196 pages × 7034 critères).

**7 problèmes racines identifiés :**
1. Détecteurs regex au lieu d'intelligence sémantique → 88% faux négatifs hero_01
2. Critères en isolation (H1 scoré sans sous-titre) → test 5s incohérent
3. Pas de dual-viewport réel → 1 verdict desktop+mobile fusionné
4. 35% clients mono-page → audit incomplet
5. Recos déconnectées du business context → génériques
6. Crops approximatifs → highlights décalés
7. Pas d'adaptation logique par type de page → blogs scorés comme LP

**Ce qui fonctionne bien :** architecture pipeline solide, tech pillar 99%, killer rules, playbooks JSON, ghost capture, CTA phantom filter, social proof detection, reco format before/after/why.

### Plan V15.2 — 7 étapes validées
| # | Étape | Impact | État |
|---|---|---|---|
| 1 | **Semantic Scoring Layer** (semantic_scorer.py) | Résout 70% | PRIORITÉ 1 |
| 2 | Dual Viewport | Desktop vs Mobile séparés | ⏳ |
| 3 | Page Coverage Expansion | 35% clients mono-page | ⏳ |
| 4 | Contextual Recos | Business-spécifiques | ⏳ |
| 5 | Screenshot Fix | Crops centrés | ⏳ |
| 6 | Page Type Intelligence | Blog ≠ LP | ⏳ |
| 7 | Learning Layer | Feedback → prompts | ⏳ futur |

### Décisions Mathis validées
- **Séquence B** : Semantic Scorer d'abord → Golden Dataset ensuite → Page coverage
- **Golden Dataset** : 25-30 sites best-in-class pour calibrer les règles (Claude propose la sélection)
- **Page coverage** : crawler les pages manquantes (PDP, collection, blog, pricing) des 26+ clients mono-page
- Analyse Gemini = "directionnellement correcte mais trop théorique, le vrai fix c'est du code pas du prompting"

### Livrables de mémoire créés
- `AUDIT_FONDAMENTAL_V15.md` — diagnostic complet
- `NOTION_CRO_DOCTRINE_SUMMARY.md` — synthèse doctrine CRO
- `GROWTHCRO_MANIFEST.md` §11 — TO-DO V15.2
- `WAKE_UP_NOTE_2026-04-17.md` — wake-up note V3 post-compression
- `memory/project_growthcro_v152_semantic_scorer_plan.md` — spec technique complète du semantic scorer
- `memory/project_growthcro_golden_dataset_plan.md` — plan golden dataset + sélection 28 sites

### 7 fixes Hero déjà appliqués (session précédente, documentés dans Plan V16.pdf)
1. Evidence cloning (196→5 instances par critère)
2. hero_04 spatial bbox fallback
3. hero_05 fold conditioning
4. CTA phantom filter
5. subtitle=nav filter
6. hero_06 5sec reconciliation
7. H1 multi tolerance

### Handoff Phase 9 → 10
Prochaine action = **construire `semantic_scorer.py`** selon la spec dans `memory/project_growthcro_v152_semantic_scorer_plan.md`. Puis proposer formellement les 28 sites golden dataset à Mathis pour validation. Puis capturer et scorer le golden dataset. Puis page coverage expansion.

### Stats pipeline actuelles (state.py)
- 201 captures, 197 spatial_v9, 197 perception, 83 intent
- 201 score_pillars, 196 score_page, 191 recos
- 80 clients total, 79 captured, 1 missing (tudigo)

---

## Phase 10 — Golden Dataset Pipeline Complet (2026-04-17 PM6)

**Objectif :** Exécuter le plan PM5 de bout en bout — recapturer les pages golden dégradées, capturer les 5 nouveaux sites, scorer l'ensemble avec le pipeline complet incluant le semantic scorer Haiku.

### Recaptures (10 pages dégradées/invalides)

Via Bright Data Scraping Browser (anti-bot + IPs résidentielles) :

- **Aesop** ×3 (home, collection, pdp) — local bloqué par Akamai, Bright Data OK. PDP : ancienne URL (`parsley-seed-anti-oxidant-serum`) retournait 500, corrigée vers `lucent-facial-concentrate` via scraping de la collection page.
- **Le Labo** ×2 (home, pdp) — country selector "SELECT YOUR LOCATION" bloquait la page. Fix : URL racine (`/`) + click "ENTER SITE" via Playwright. PDP : URL changée de `santal-33-702.html` vers `santal-33.html`.
- **Dollar Shave Club** ×2 (home, pdp) — cookie banner + panier auto-ouvert. Fix : dismiss cookie avant capture.
- **Asphalte home** — page Nuxt SPA avec portal genre ("L'Homme"/"La Femme"). Fix : dismiss Cookiebot PUIS click "L'homme" pour naviguer vers `/h`, puis deep scroll.
- **Drunk Elephant home** — OK. PDP reste avec modale "Welcome to Drunk Elephant" non dismissée (Bright Data crédits épuisés avant la recapture).

### Captures nouveaux sites (15 pages)

- **Gymshark** : home (57K capture), collection (50K), pdp (48K) — PDP URL trouvée en scraping la collection
- **Stripe** : home (44K), pricing (74K), /payments LP (60K) — parfait
- **Emma Matelas** : home (29K), pdp matelas (16K), LP quiz (15K)
- **Revolut** : home (35K), pricing (35K), /business LP (36K)
- **Monday.com** : home (59K), pricing (20K), /crm LP (34K)

### Modifications code

1. **`ghost_capture_cloud.py`** — Stage 3.5 deep scroll ajouté (entre cookie dismiss et perception extraction). 60 passes max, 800px/step, détecte expansion hauteur pour les SPA lazy-loading. Retour scroll top + attente 800ms avant capture.

2. **`golden_recapture.py`** — Nouveau script. Liste RECAPTURE_TASKS avec hooks pre-capture par site (cookie dismiss, portal click, modal close, deep scroll). Supporte Bright Data et local.

3. **`data/golden/_golden_registry.json`** — v2.0 : Feed supprimé (SSL mort, domaine devenu OKR), 5 nouveaux sites ajoutés, URLs corrigées (Aesop PDP, Le Labo PDP, Asphalte home). Total = 30 sites, 78 dossiers (75 actifs + 3 Feed legacy).

4. **`data/clients_database.json`** — 8 nouveaux clients ajoutés pour les sites golden pas encore dans la DB (gymshark, stripe, emma_matelas, revolut, monday, alan_golden, asphalte_golden, linear_golden). Total = 88 clients.

### Pipeline scoring golden — résultats

| Stage | Script | Résultat |
|-------|--------|----------|
| 2 | native_capture.py | 75/75 capture.json ✅ |
| 3 | perception_v13.py | 75/75 spatial_v9.json ✅ |
| 4 | batch_rescore.py (6 blocs) | 75/75 score_*.json ✅ |
| 5.5 | semantic_scorer.py (Haiku) | 75/75 score_semantic.json ✅ (~$0.50) |

### Audit visuel final

| Site | Status | Notes |
|------|--------|-------|
| Aesop (home, collection, pdp) | ✅ | Contenu complet, cookie banner visible mais non bloquant |
| Le Labo home | ⚠️ | Country selector OK, images lazy non chargées (contenu texte OK) |
| Le Labo PDP (Santal 33) | ✅ | Parfait — 2206 nodes, page complète |
| Dollar Shave Club (home, pdp) | ✅ | Hero complet, produits visibles |
| Asphalte (home, pdp, pricing) | ✅ | Hero plein écran, navigation complète |
| Drunk Elephant home | ✅ | OK |
| Drunk Elephant PDP | ❌ | Modale "Welcome" non dismissée — Bright Data suspendu |
| Gymshark (home, collection, pdp) | ⚠️ | Cookie banner + popup localisation, produits visibles |
| Stripe (home, pricing, LP) | ✅ | Parfait |
| Monday (home, pricing, LP) | ⚠️ | Hero légèrement coupé, AI chatbot prominent |
| Revolut (home, pricing, LP) | ✅ | Bon |
| Emma Matelas (home, pdp, LP) | ✅ | Parfait |

### Bright Data — épuisé

Crédits essai gratuit épuisés après les recaptures Le Labo. Compte suspendu. Pour la suite, options :
- Souscrire un plan payant Bright Data (~$1.50/1K req)
- Ou migrer vers ZenRows ($69/mois) ou Oxylabs ($300/mois)
- Ou utiliser le mode local (suffisant pour la plupart des sites non protégés Akamai)

### Handoff Phase 10 → suite

Golden dataset 75/75 scoré. Prochaines actions possibles :
1. **Annotation manuelle Mathis** : reviewer les scores sémantiques Haiku et annoter les écarts
2. **Calibration** : ajuster les poids/seuils du semantic scorer basé sur les annotations
3. **Drunk Elephant PDP** : recapturer quand Bright Data ou alternative disponible
4. **Nettoyage Feed** : supprimer les 3 dossiers Feed legacy de data/golden/
5. **Étape 2 V15.2** : Dual Viewport (desktop + mobile séparés)

## Phase 11 — Calibration sémantique & fix psy_08 (2026-04-17)

### Calibration auto
- Comparaison golden (75 pages) vs clients (291 pages) sur 18 critères sémantiques Haiku
- 15/18 critères immédiatement ✅ OK (delta < 0.3, pas de biais)
- 3 critères flaggés LOW (hero_04, per_02, psy_02) : barèmes exigeants mais deltas < 0.06 → pas de biais, juste difficiles
- 1 critère problématique : psy_08 (témoignages) — golden 0.39, clients 0.36, 77% à 0/3

### Fix psy_08
- Cause racine : `_get_testimonials_text()` dépend de `capture.socialProof.testimonials`, souvent vide car widgets JS (Trustpilot, Avis Vérifiés) pas rendus dans le HTML capturé
- Fix : prompt élargi pour injecter aussi `_get_social_proof_summary()` (badges, notes, compteurs, logos) + barème assoupli pour signaux indirects
- Re-scoring 366 pages via Haiku 4.5 (en 3 batches, ~$0.50)
- Résultat : psy_08 golden 0.39→1.42, clients 0.36→1.41, delta 0.01 ✅

### Bug corrigé
- Première exécution du rescore avec modèle `claude-3-5-haiku-latest` (déprécié) → scores `None` sur 366 pages
- Fix : switch vers `claude-haiku-4-5-20251001`, re-exécution complète

### État final calibration
- 18/18 critères bien calibrés, aucune anomalie de discrimination
- Scorer sémantique validé comme fiable pour production

## Phase 12 — Golden Bridge V16 & Recos enrichies (2026-04-17)

### Golden Bridge
- Nouveau module `golden_bridge.py` dans `skills/site-capture/scripts/`
- Charge le golden registry + scores/captures de chaque golden site
- Pour chaque (client_category, page_type, criterion) : trouve les 5 golden les plus proches, calcule avg score, génère un bloc d'inspiration avec H1/CTA/structure
- CATEGORY_MAP : 16 golden categories → clients categories compatibles
- Trois signaux : Annihilation (avg ≤ 1.0), Neutre, Fort (avg ≥ 2.5)

### Intégration dans reco_enricher_v13.py
- `build_user_prompt()` étendu avec param `golden_context`
- Bloc `## GOLDEN BENCHMARK` ajouté au prompt avec exemples concrets
- Consignes LLM : annihiler (P3) si signal ⚠️, renforcer si signal 🎯
- Métadonnées `golden_annihilate` et `golden_avg` ajoutées aux prompts JSON
- Version bumped : v16.0.0-reco-prompts-golden

### Résultats
- 3574 prompts : 40% annihilés, 9% signal fort, 50% neutres
- 127 pages × ~28 recos = 3531 recos V16 golden-aware
- Test Japhy/home : 6/6 critères annihilés correctement rétrogradés en P2/P3
- Distribution finale : P0=53%, P1=41%, P2=1%, P3=3%

### Réponse au challenge Gemini
- Gemini avait raison sur le fond : le reco enricher manquait le bridge golden
- Mais surestimait le gap : on avait déjà intent-aware, cluster perceptuel, anti-patterns, vocabulaire contrôlé
- Ce qui manquait vraiment : injection du benchmark golden comme filtre de pertinence + inspiration concrète

## Phase 13 — Module AURA V16 (2026-04-18)

**Module AURA V16 déployé** — Aesthetic Universal Reasoning Architecture.

Scripts créés :
- `aura_extract.py` (748 lignes) — Extraction Design DNA depuis HTML : couleurs, fonts, spacing, shadows, radii, animations, layout, textures → vecteur esthétique 8D + analyse Haiku (signature, techniques, philosophie)
- `aura_compute.py` (678 lignes) — Calcul des design tokens : échelle φ (nombre d'or), chromatisme psychologique, 5 profils motion (inertia/smooth/spring/bounce/snap), profondeur multicouche, sélection typo anti-AI-slop → aura_tokens.json + CSS custom properties
- `golden_design_bridge.py` (391 lignes) — Matching esthétique cross-catégorie : distance euclidienne pondérée sur vecteur 8D, matching par INTENTION esthétique (pas business), injection benchmark prompt

Architecture :
- `AURA_ARCHITECTURE.md` (1025 lignes) — Source de vérité : 3 modes d'entrée (client URL / from scratch / hybride), Smart Intake 5 questions, vecteur esthétique 8D, Technique Library, Self-Learning Loop

Golden Design Intelligence :
- 75 pages golden profilées (design_dna.json + vecteur 8D technique)
- 13 pages prioritaires analysées par Haiku (96 techniques cataloguées)
- Matching validé cross-catégorie : wellness→Headspace+Aesop, SaaS dark→Monday+Stripe, fun ecom→Emma+Alan

Intégration :
- SKILL.md mis à jour : Phase 0 = Smart Intake + AURA Extract/Compute/Bridge, Phase 2 DA via AURA tokens, Phase 4 Self-Learning Loop
- Manifest mis à jour : section GSG V16 complète avec arbre des fichiers AURA
## Phase 14 — Opus Golden Analysis + Quality Audit (2026-04-18)
- 75 golden pages re-analysées en qualité Opus (42 par Opus direct, 33 par Sonnet agents)
- 290 techniques cataloguées (upgrade from 96 Haiku techniques)
- Audit qualité captures : 15/210 clients cassées, 7/75 golden cassées, 14 pages DOM<50
- reco_enricher passé de Sonnet à Haiku
- 20 clients mono-home identifiés pour capture complémentaire future

## Phase 15 — Dashboard GrowthCRO V16 Interactive + LP Japhy (2026-04-18)

### LP Japhy V16 livrée
- `deliverables/japhy/home/japhy_lp_v16.html` — Quiz Page cold traffic, BAB+AIDA hybride, 9 sections
- AURA tokens appliqués : primary #B8CC00, secondary #d6790f, Wix Madefor Display + Satoshi
- Copy Phase 3 LP-Creator intégré verbatim, 4 VoC Trustpilot vérifiés, founder Thomas+Nelson

### Dashboard V16 — construction et problèmes
- Dashboard SPA HTML interactif : `deliverables/GrowthCRO-V16-Dashboard.html`
- Design Alaska Boreal Night : starfield multi-layer parallax (3 couches), aurora borealis (3 bandes animées), milky way, nebula gradients, shooting stars procédurales, grain overlay
- Palette : deep navy void → twilight, white + gold accents, cyan/indigo/violet highlights, ok/warn/bad pour métriques
- Typography : Cormorant Garamond (display) + DM Sans (body) + JetBrains Mono (code)
- Architecture SPA : sidebar 7 tabs (Overview, Clients, Audits, Recos, AURA, Pipeline, Livrables), slide-in detail panel, search/filter/sort
- Données : 105 clients, 291 pages scorées, 372 screenshots base64 par page type, 3531 recos

### Problèmes rencontrés et fixés
1. **Dashboard vide (JS crash)** — `\n` littéraux (203 occurrences) dans les champs texte reco cassaient le JSON inline dans `<script>`. Fix : `json.dumps(data, ensure_ascii=True)`.
2. **Scores >100%** — certains blocs avaient `max=0` dans le JSON. Fix : fallback sur somme critères max, cap à 100%.
3. **Screenshots identiques Home/PDP** — n'encodait qu'un screenshot par client. Fix : encoder par page type avec clés `{client}__{pagetype}__desktop`.
4. **Toutes les recos P3 (vertes) alors que scores rouges** — utilisait `recos_enriched.json` avec priorités cassées. Fix : basculé sur `recos_v13_final.json` avec priorités dérivées du score critère (≤33% → P1, ≤60% → P2, >60% → P3).
5. **Recos illisibles** — format texte blob sans structure. Fix : format AVANT/APRÈS/POURQUOI structuré avec criterion_id, bloc, ICE, lift.
6. **`</script>` dans les données JSON** — les recos tech mentionnaient `<script>` GTM littéralement, ce qui coupait le bloc `<script>` HTML. Fix : échapper tous les `<` et `>` en `\u003c`/`\u003e` dans le JSON.

### État actuel du dashboard (à fixer)
- Le fichier 10.9 MB se charge mais l'affichage reste problématique
- Mathis rapporte "tellement de choses qui vont pas" — nécessite un audit profond du rendu JS dans la prochaine session
- Les données sont correctes (vérifié : Oma Me home = 49.6% avec P1=17, P2=3, P3=4) mais le rendu côté JS doit être débugué en profondeur

### Fichiers dashboard
- `deliverables/GrowthCRO-V16-Dashboard.html` — dashboard SPA (10.9 MB, données inline)
- `deliverables/growthcro_data_safe.js` — données corrigées séparées (11.2 MB)
- `deliverables/growthcro_dashboard_data.json` — ancien format, supercédé
- `deliverables/growthcro_screenshots.json` — ancien format screenshots par client, supercédé

### Décision Mathis
- "On va reprendre dans une nouvelle conversation" — audit profond de tout le projet, ménage fichiers, vérification architecture
- Session suivante = audit méga profond de l'intégralité des fichiers, architecture, optimisation dossiers, connexions manquantes


## Phase 18 — 2026-04-18/19 : P5 Dashboard V17 → P6 UX redesign → P4 Cleanup

### P5 — Dashboard V17 "Observatoire" (18 avril)
Ménage complet + reconstruction dashboard avec doctrine V16 appliquée (Galaxie Alaska Boreal Night).

**Livrables** :
- `skills/site-capture/scripts/build_dashboard_v17.py` — pipeline data
- `deliverables/GrowthCRO-V17-Dashboard.html` (44 KB shell V17)
- `deliverables/dashboard_v17_app.js` (44 KB app renderer)
- `deliverables/growthcro_data_v17.{js,json}` (55.7 MB data embed)

**5 vues V17 initiales** :
1. Galaxie (landing : KPI + 6 gauges cliquables)
2. Radar P0 (105 blockers triés Impact Score)
3. Portfolio (105 cards, pulse si P0>0)
4. Labo Audit (screenshot Desktop+Mobile + piliers + règles v3.2)
5. Doctrine (6 histogrammes des piliers)

**Learning loop** : localStorage verdicts ✓/✗ par critère + export `learning_log.json`.

**Data contract** : `window.DASHBOARD_V17_DATA = {meta, clients[], pages_flat[], recos_flat[], p0_index[], rules_firing, schwartz_dist, business_type_dist, overlay_stats_agg, priority_distribution_fleet, bloc_names, pillar_max, screenshots}`.

### P6 — UX redesign (19 avril)
Feedback Mathis : drawer trop étroit, pas de screenshots, termes techniques incompréhensibles.

**P6.A — Data enrichment** :
- 582 screenshots base64 embed (format `{client}__{page}__{viewport}`)
- 54 `criterion_labels` human-readable
- 7 `rule_labels` V3.2 avec why + evidence
- 6 `pillar_descriptions`

**P6.B — Full-width Client route (6e onglet nav)** :
- Breadcrumb + titre + pills + screenshots Desktop+Mobile grand format
- 3 onglets : Overview (gauges + rules + top recos) / Pages (cards par page avec killer) / All Recos (groupées pilier + filtres)
- Reco text parsé en sections colorées (Problème rouge, AVANT jaune, APRÈS vert, Pourquoi cyan, Comment indigo, Contexte violet)
- Legacy drawer désactivé

**P6.C — Labo upgrade** :
- Breadcrumb Portfolio > {client} > {pageType}
- Hero gros screenshots Desktop+Mobile
- Règles v3.2 expliquées via RULE_LABELS[rid].why
- 3 recos max dépliées avec sections parsées

**P6.D — Verification JSDOM** ✅ :
- 582 screenshots, 54 criterion_labels, 7 rule_labels, 6 pillar_descriptions chargés
- 6 routes actives
- `showClient('qonto')` → 29 KB DOM, 2 hero screenshots, 3 tabs
- `gotoLabo('qonto', 'blog')` → breadcrumb + 2 labo screens + 6 KPI + 3 recos parsées

Dashboard v17.2.0 livré (55.9 KB HTML + 64.3 KB app.js + 55.7 MB data).

### P4 — Disk cleanup (19 avril)
Archivage sans suppression (mount refuse `rm`, seul `mv` autorisé).

**Tier 1** → `deliverables/archive/v16_dashboard_2026-04-18/` : 5 fichiers V16 (29 MB).

**Tier 2** → `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` : 10 scripts DEPRECATED (apify_enrich, reco_enricher V11, perception_pipeline, component_*, score_site, spatial_scoring, build_dashboard_v12, _dashboard_template).

**Tier 2b** → `_archive_deprecated_2026-04-19/` racine : reco_engine.py, spatial_reco.py.

**Tier 3** → `deliverables/archive/gemini_audit_package_2026-04-14/` : 1.4 GB snapshot d'audit one-shot.

Chaque archive contient un `ARCHIVE_README.md` avec mapping des remplaçants actifs + procédure rollback.

**Deliverables/ racine post-P4** : V17 dashboard (HTML + JS + data) + 4 sous-dossiers clients actifs + archive/.

### Transition V18
Mathis : "On passe au Projet GrowthCRO V18 parce que là y'a encore des choses que t'as pas comprises". Scope V18 à clarifier.
