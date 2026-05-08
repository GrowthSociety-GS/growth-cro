# GrowthCRO — Architecture Complète de la Webapp

> Version 1.0 — 5 avril 2026
> Stack : Next.js 14 (App Router) + Supabase (Auth, DB, Storage, Realtime) + Vercel
> Philosophie : "Mille fois mieux que Rocket" — UI light mode premium, anti-dashboard-générique
>
> Note V26.AH (2026-05-04) : ce document reste la cible produit long-terme. Le runtime actuel est un static MVP + moteurs Python séparés. Avant de coder, lire `architecture/PRODUCT_BOUNDARIES_V26AH.md` et `architecture/RESCUE_DECISION_V26AH_2026-05-04.md`.

---

## 1. VISION PRODUIT

GrowthCRO est l'outil interne de Growth Society qui centralise tout le workflow CRO :
**Auditer → Recommander → Générer → Déployer → Mesurer → Apprendre**

Contrairement à Rocket (qui empile des features), GrowthCRO est conçu comme un **système vivant** où chaque module nourrit les autres. L'IA n'est pas un gadget en sidebar — elle EST le moteur de chaque étape.

### Ce qu'on garde de Rocket (les bonnes idées)
- Navigation latérale claire avec sections logiques
- Pipeline client visuel
- Onglet Pages & Assets par client
- Notion sync comme base de connaissance

### Ce qu'on fait disparaître (les faiblesses de Rocket)
- Dark mode forcé qui rend tout pareil → **Light mode premium avec accents de couleur**
- Formulaires plats sans intelligence → **Formulaires conversationnels IA-assistés**
- Preview statique → **Live preview temps réel avec device switching**
- Audit = formulaire à cocher → **Audit = IA qui crawl, analyse, et score automatiquement**
- Bibliothèque de templates inerte → **Bibliothèque vivante qui apprend de chaque génération**
- Aucune donnée de performance → **Dashboard connecté aux vraies métriques via Catchr**
- Pas de versioning → **Historique complet, comparaison A/B, rollback**

---

## 2. ARCHITECTURE NAVIGATION — SIDEBAR

```
┌─────────────────────────────────┐
│  ◆ GrowthCRO                   │
│  by Growth Society              │
│                                 │
│  ─── OVERVIEW ───               │
│  📊 Dashboard                   │
│                                 │
│  ─── CRO WORKFLOW ───           │
│  🔍 Growth Audit                │
│  ⚡ Site Generator (GSG)        │
│                                 │
│  ─── PROJETS ───                │
│  👥 Clients                     │
│                                 │
│  ─── INTELLIGENCE ───           │
│  📚 Bibliothèque CRO           │
│  🖼️ Bibliothèque Assets         │
│  🔗 Références LP              │
│  🧩 Pattern Library             │
│                                 │
│  ─── SAVOIRS ───                │
│  📓 Base Notion CRO             │
│                                 │
│  ─── SYSTÈME ───                │
│  🔌 Connexions                  │
│  ⚙️ Paramètres                  │
│                                 │
│  ───────────────                │
│  🤖 AI Status                   │
│  Growth Society © 2026          │
└─────────────────────────────────┘
```

**Différence clé vs Rocket** : la section "INTELLIGENCE" regroupe les 4 bibliothèques (CRO, Assets, Références LP, Patterns) au lieu de les disperser. La section "SYSTÈME" isole les connexions et paramètres proprement.

---

## 3. MODULE PAR MODULE — DÉTAIL COMPLET

---

### 3.1 — 📊 DASHBOARD (page d'accueil)

**Route** : `/dashboard`

**Rocket faisait** : KPIs statiques + bar chart basique + fil d'activité
**GrowthCRO fait** : Dashboard dynamique connecté aux vraies données avec actions directes

#### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Bonjour Mathis 👋           [Période: 30j ▼]  [+ Nouveau]  │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│ Projets  │ Pages    │ Délai    │ Score    │ Lift CRO         │
│ actifs   │ générées │ moyen    │ audit Ø  │ estimé Ø         │
│   12     │   47     │  3.1j    │  62/108  │  +24.7%          │
│  +3 ↑    │  +8 ↑    │ -0.8j ↓ │  +5 ↑    │  +6.2% ↑         │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                                                              │
│  ┌─── Pipeline CRO ────────────────────────────────────┐     │
│  │ Brief(4) → Audit(3) → Recos(2) → Build(2) → Live(1)│     │
│  │ [═══════  ══════   ════    ════   ══]               │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─── Activité récente ──┐  ┌─── Performance Catchr ──────┐ │
│  │ • LP Luko v3 générée  │  │  CVR moyen : 4.2% (+0.3%)   │ │
│  │   il y a 2h — Sofia   │  │  CPA moyen : 18.40€ (-12%)  │ │
│  │                       │  │  ROAS moyen : 3.8x (+0.4x)  │ │
│  │ • Audit PayFit        │  │                              │ │
│  │   terminé — Score 71  │  │  [Mini graphe sparkline]     │ │
│  │                       │  │                              │ │
│  │ • 3 recos validées    │  │  Top pages :                 │ │
│  │   Qonto — Théo        │  │  1. Luko LP v2 — 6.1% CVR   │ │
│  │                       │  │  2. PayFit HP — 4.8% CVR     │ │
│  │ • Brief Shine reçu    │  │  3. Qonto LP — 4.2% CVR     │ │
│  └───────────────────────┘  └──────────────────────────────┘ │
│                                                              │
│  ┌─── Apprentissages IA récents ───────────────────────────┐ │
│  │ "Les CTA avec prix barré convertissent +31% mieux en    │ │
│  │  InsurTech (basé sur 4 audits récents)"                 │ │
│  │ "Le hero split 60/40 surperforme le hero centré pour    │ │
│  │  les pages SaaS B2B (+18% engagement)"                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

#### KPIs dynamiques (cartes du haut)
| KPI | Source | Calcul |
|-----|--------|--------|
| Projets actifs | Supabase `clients` table | `WHERE status != 'archived'` |
| Pages générées | Supabase `pages` table | `COUNT WHERE created_at > period` |
| Délai moyen | Supabase `projects` | `AVG(completed_at - created_at)` |
| Score audit Ø | Supabase `audits` | `AVG(score)` |
| Lift CRO estimé | Supabase `recommendations` | `AVG(estimated_lift)` |

#### Blocs spécifiques
- **Pipeline CRO** : kanban horizontal simplifié (Brief → Audit → Recos → Build → Live → Monitoring), drag & drop pour bouger un client
- **Performance Catchr** : widget connecté à l'API Catchr, affiche CVR/CPA/ROAS moyens avec sparklines
- **Activité récente** : feed temps réel (Supabase Realtime) des actions de l'équipe
- **Apprentissages IA** : insights auto-générés par l'IA à partir des audits et résultats — ÇA c'est unique, Rocket n'a rien de comparable

#### Actions rapides (bouton "+ Nouveau")
- Nouveau client
- Nouvel audit
- Nouvelle page
- Importer un brief

---

### 3.2 — 🔍 GROWTH AUDIT

**Route** : `/audit` (liste) → `/audit/new` (wizard) → `/audit/[id]` (résultat)

**Powered by** : skill `cro-auditor` (Growth Audit)

#### Wizard de création (3 étapes)

**Étape 1 — Input**
```
┌────────────────────────────────────────────┐
│  Que veux-tu auditer ?                     │
│                                            │
│  [Coller une URL]                          │
│  [Uploader un HTML]                        │
│  [Uploader un screenshot]                  │
│  [Sélectionner un client existant ▼]       │
│                                            │
│  Type de page : [Auto-detect ▼]            │
│  Landing Page | Home | Produit | Funnel    │
└────────────────────────────────────────────┘
```

**Étape 2 — Contexte (pré-rempli si client existant)**
- Client, secteur, business model
- Objectif de la page (leads, ventes, signup...)
- Source de trafic principale
- Audience/persona cible

**Étape 3 — Configuration audit**
- Sections à auditer (toutes activées par défaut, toggle pour désactiver)
- Profondeur : Standard (rapide, 36 critères) / Deep (108 critères, +psychologie)
- Benchmark sectoriel : activer/désactiver

#### Page résultat d'audit (`/audit/[id]`)

```
┌──────────────────────────────────────────────────────────┐
│  Client: Luko Insurance        Score: 42/108             │
│  URL: luko.eu/assurance-habitation                       │
│  Type: Landing Page   Secteur: InsurTech                 │
│                                                          │
│  [Vue d'ensemble] [Détail critères] [Recommandations]    │
│  [Exporter ▼]                                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌── Radar CRO ──┐  ┌── Score par catégorie ──────────┐ │
│  │   (spider      │  │  Hero & Above the fold  6/15    │ │
│  │    chart)      │  │  Proposition de valeur  8/12    │ │
│  │                │  │  CTAs                   4/12    │ │
│  │                │  │  Social Proof           5/9     │ │
│  │                │  │  Copywriting            7/18    │ │
│  │                │  │  Design & UX            6/18    │ │
│  │                │  │  Technique              4/12    │ │
│  │                │  │  Psychologie            2/12    │ │
│  └────────────────┘  └────────────────────────────────┘ │
│                                                          │
│  ┌── Top 5 Quick Wins ──────────────────────────────────┐│
│  │ 1. Ajouter Trustpilot 4.8/5 dans le hero  +8-15%    ││
│  │ 2. Reformuler H1 avec bénéfice chiffré    +5-10%    ││
│  │ 3. Réduire formulaire de 8 à 4 champs     +12-20%   ││
│  │ 4. Ajouter urgency timer                  +3-8%     ││
│  │ 5. Contraste bouton CTA (ratio 2.8→4.5)   +3-5%    ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  [💡 Générer les recos complètes]                        │
│  [⚡ Envoyer au GSG pour rebuild]                        │
└──────────────────────────────────────────────────────────┘
```

#### Différences vs Rocket
- **Auto-detect du type de page** (Rocket = sélection manuelle)
- **Pré-remplissage contexte client** quand on part d'un client existant
- **Score /108** (vs /10 sur Rocket — plus granulaire)
- **Bouton direct "Envoyer au GSG"** = le résultat de l'audit alimente directement la génération
- **Export** : HTML rapport, PDF client, Brief GSG (JSON structuré)

---

### 3.3 — ⚡ SITE GENERATOR (GSG)

**Route** : `/generator` (hub) → `/generator/new` (wizard) → `/generator/[id]` (éditeur)

**Powered by** : skill `growth-site-generator` + Design Engine v2.0

#### Hub GSG (`/generator`)
Liste de toutes les générations avec filtres (client, type, statut, score).
Bouton "Nouvelle génération" + "Quick Start (3 champs)".

#### Wizard de création (4 étapes)

**Étape 1 — Brief** (conversationnel, pas un formulaire plat)
```
┌────────────────────────────────────────────────┐
│  Nouveau projet GSG                            │
│                                                │
│  ┌─ Quick Start ─────────────────────────────┐ │
│  │ Client: [_____________▼]                  │ │
│  │ Type:   [Landing Page ▼]                  │ │
│  │ URL de référence: [________________]      │ │
│  │                     [▶ Démarrer]          │ │
│  └───────────────────────────────────────────┘ │
│                                                │
│  ou [Brief complet →]                          │
│                                                │
│  ┌─ Depuis un audit ─────────────────────────┐ │
│  │ Audits disponibles :                      │ │
│  │ • Luko — 42/108 — 7 recos P1             │ │
│  │ • PayFit — 67/108 — 4 recos P1           │ │
│  │ [Sélectionner un audit pour pré-remplir]  │ │
│  └───────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

**Étape 2 — Direction Artistique** (Design Engine v2.0)
- Registre d'ambiance (8 options visuelles, pas un dropdown)
- Analyse de marque automatique (si URL fournie)
- Accélérateur de palette (10 palettes sectorielles + custom)
- Preview du mood board généré
- Mode de livraison : HTML pur / React bundle

**Étape 3 — Copywriting**
- Framework auto-sélectionné (PAS, AIDA, PASTOR...) avec possibilité d'override
- Tonalité, persona, niveau de conscience Schwartz
- IA génère le copy section par section, éditable inline

**Étape 4 — Génération & Live Preview**

```
┌────────────────────────────────────────────────────────────┐
│  [📱 Mobile] [💻 Desktop] [📟 Tablet]    [Score: 128/153] │
│  ┌────────────────────────────────────────────────────────┐│
│  │                                                        ││
│  │              LIVE PREVIEW                              ││
│  │              (iframe responsive)                       ││
│  │                                                        ││
│  │                                                        ││
│  └────────────────────────────────────────────────────────┘│
│                                                            │
│  ┌── Panneau latéral ──────────────────┐                   │
│  │ Sections :                          │                   │
│  │ ☑ Hero          [↕ drag to reorder] │                   │
│  │ ☑ Social Proof  [↕]                 │                   │
│  │ ☑ Features      [↕]                 │                   │
│  │ ☑ Testimonials  [↕]                 │                   │
│  │ ☑ Pricing       [↕]                 │                   │
│  │ ☑ FAQ           [↕]                 │                   │
│  │ ☑ CTA Final     [↕]                 │                   │
│  │ [+ Ajouter section]                 │                   │
│  │                                     │                   │
│  │ Score auto-évaluation :             │                   │
│  │ CRO:    42/90  ████████░░           │                   │
│  │ Design: 52/45  █████████████        │                   │
│  │ Psycho: 34/18  ██████████████       │                   │
│  │ Total: 128/153                      │                   │
│  └─────────────────────────────────────┘                   │
│                                                            │
│  [Régénérer] [Éditer le code] [💾 Sauvegarder] [🚀 Deploy]│
└────────────────────────────────────────────────────────────┘
```

#### Différences vs Rocket
- **Import depuis audit** = un clic et le brief est pré-rempli avec les findings
- **DA visuelle** (pas des dropdowns "couleur primaire") → mood board, registre d'ambiance
- **Score /153** en temps réel pendant la preview
- **Drag & drop des sections** pour réordonner
- **Édition inline du copy** directement sur la preview
- **Historique de versions** avec diff visuel

---

### 3.4 — 👥 CLIENTS (Client Context Manager)

**Route** : `/clients` (table) → `/clients/[id]` (fiche détaillée)

C'est LE module qui n'existait pas correctement dans Rocket et qui est le cœur de GrowthCRO.

#### Table clients (`/clients`)

| Colonne | Type | Triable | Filtrable |
|---------|------|---------|-----------|
| Client | text + avatar | ✅ | search |
| Secteur | badge | ✅ | multi-select |
| Business Model | badge | ✅ | multi-select |
| Budget Ads | currency | ✅ | range |
| Pipeline Stage | kanban badge | ✅ | multi-select |
| Score Audit Ø | score bar | ✅ | range |
| Pages actives | number | ✅ | — |
| Lift CRO estimé | % + trend | ✅ | range |
| Manager | avatar | ✅ | multi-select |
| Dernière activité | relative date | ✅ | date range |

**Actions batch** : Exporter sélection, Archiver, Assigner manager, Lancer audit groupé

#### Fiche client (`/clients/[id]`)

**Onglets** :

**Vue d'ensemble** — Le "one-pager" du client
```
┌──────────────────────────────────────────────────────────────┐
│  LUKO INSURANCE                                    [Éditer] │
│  InsurTech • B2C • Budget: 45K€/mois • Pipeline: Build      │
│                                                              │
│  ┌─── Contexte IA ───────────────────────────────────────┐   │
│  │ Proposition de valeur : Assurance habitation 100%     │   │
│  │ digitale avec IA pour les sinistres < 2h.             │   │
│  │ Audience : 25-40 ans, propriétaires urbains,          │   │
│  │ digital-native, sensibles au prix.                    │   │
│  │ Ton : Moderne, rassurant, pas corporate.              │   │
│  │ Concurrents : Lemonade, Lovys, Alan (adj.)            │   │
│  │ USP : Remboursement en 2h garanti                     │   │
│  │                                     [✏️ Enrichir]     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌── KPIs ──────────┐  ┌── Radar CRO ────────────────────┐  │
│  │ Score Audit: 42   │  │ (spider chart comparatif        │  │
│  │ Pages: 4          │  │  avant/après recos)             │  │
│  │ Recos: 11 (7 P1)  │  │                                │  │
│  │ Lift estimé: +38% │  │                                │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Audit CRO** — Historique de tous les audits du client, comparaison dans le temps

**Recommandations** — Toutes les recos avec statut (Draft, Validé, Implémenté, Rejeté), filtre par priorité

**Pages & Assets** — Galerie des pages générées + assets uploadés, avec vignettes et statuts

**Activité & Notes** — Journal chronologique, notes manuelles, tags, résumé IA du projet

**Brand Context** — Données de marque (logo, palette, typo, tone of voice, guidelines). Ce contexte alimente automatiquement le GSG quand on génère pour ce client.

---

### 3.5 — 📚 BIBLIOTHÈQUE CRO

**Route** : `/library/cro`

**Powered by** : `competitive_library.md` + `swipe_library.md` du GSG

Bibliothèque vivante de templates et patterns CRO.

#### Sous-onglets

**Templates** — Templates de pages validés, filtrables par :
- Type (Landing Page, Home, Produit, Blog, Listicle...)
- Secteur (SaaS, E-commerce, FinTech, InsurTech, Services...)
- Score range
- Lift range

Chaque template = vignette + métadonnées + bouton "Utiliser comme base" (lance le GSG avec ce template pré-chargé)

**Patterns** — Composants isolés (hero, CTA, pricing table, FAQ, testimonial...) avec :
- Preview visuel
- Score du pattern
- Contextes d'utilisation recommandés
- Code HTML copiable

**Teardowns** — Analyses de concurrents stockées (issus des audits), avec points forts/faibles identifiés

#### Auto-alimentation
- Chaque page générée par le GSG avec score > 120/153 → automatiquement ajoutée aux templates
- Chaque audit → alimente les teardowns
- Patterns validés par l'équipe → enrichissent la swipe library

---

### 3.6 — 🖼️ BIBLIOTHÈQUE ASSETS

**Route** : `/library/assets`

Assets visuels organisés par client.

#### Features
- **Upload** : drag & drop, multi-fichier, depuis Frame.io (connexion)
- **Filtres** : par client, type (image, vidéo, logo, icône), tag, AI-generated
- **Tagging IA** : description automatique, détection de contenu, suggestion de tags
- **Lien GSG** : sélectionner un asset → il devient disponible dans le générateur
- **Versions** : historique des versions d'un même asset

---

### 3.7 — 🔗 RÉFÉRENCES LP

**Route** : `/library/references`

Bibliothèque d'URLs de landing pages de référence classées par catégorie.

#### Structure
- Catégories : SaaS, E-commerce, Lead Gen, B2B, Service, App Mobile, Advertorial, Squeeze Page, Quiz, VSL
- Chaque référence : URL + screenshot auto + tags "Bon exemple" / "Mauvais exemple" + notes
- Compteurs : total URLs, URLs analysées
- **Bouton "Analyser"** : lance un audit léger sur l'URL pour scorer automatiquement
- **Bouton "S'inspirer"** : envoie l'URL au GSG comme référence visuelle (Phase 0.1 du skill)

---

### 3.8 — 🧩 PATTERN LIBRARY

**Route** : `/library/patterns`

Catalogue vivant de composants/patterns validés (issu du `swipe_library.md`).

#### Structure
- Classement par catégorie de composant (Hero, CTA, Social Proof, Pricing, FAQ, Footer...)
- Chaque pattern : preview, code, score, secteurs recommandés
- Tags : "Testé A/B", "Nouveau", "Top performer"
- **Import** : scanner une URL pour extraire ses patterns
- **Export** : copier le HTML d'un pattern

---

### 3.9 — 📓 BASE NOTION CRO

**Route** : `/knowledge`

Connexion au workspace Notion de Growth Society pour le knowledge management CRO.

#### Features principales

**Sync bidirectionnel** :
```
┌────────────────────────────────────────────────────────┐
│  Notion Knowledge Base                                 │
│  Dernière sync : il y a 12 min  [🔄 Synchroniser]     │
│  13 pages • 47 blocs de connaissance indexés           │
│                                                        │
│  📄 Template CRO                          ↗ Notion     │
│  📄 Doc Process CRO - Mission Media B.    ↗ Notion     │
│  📄 Rosegold Paris                        ↗ Notion     │
│  📄 Les erreurs de formulaire dans les... ↗ Notion     │
│  📄 Des éléments de réassurance sont...   ↗ Notion     │
│  📄 Humble +                              ↗ Notion     │
│  📄 La vitesse de chargement doit être... ↗ Notion     │
│  📄 Challenge le titre du Hero            ↗ Notion     │
│  ...                                                   │
│                                                        │
│  ┌── Contextualisation IA ──────────────────────────┐  │
│  │ ✅ Tout le contenu Notion est indexé comme        │  │
│  │ contexte IA. Il est automatiquement injecté       │  │
│  │ dans les audits, recommandations et générations.  │  │
│  │                                                   │  │
│  │ Derniers apprentissages extraits :                │  │
│  │ • "Toujours tester le hero en version splitée"   │  │
│  │ • "Les formulaires > 5 champs = -30% CVR"        │  │
│  │ • "Trustpilot > Avis client maison en InsurTech" │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

**Bouton Synchroniser** :
1. Pull les nouvelles pages/modifications depuis Notion API
2. Ré-indexe le contenu (embeddings vectoriels dans Supabase pgvector)
3. Met à jour le contexte IA disponible pour tous les modules
4. Affiche un résumé des changements

**Auto-apprentissage** :
- Quand un audit est validé → les patterns découverts sont proposés en ajout Notion
- Quand une reco performe (données Catchr) → insight ajouté automatiquement
- L'IA peut proposer de nouvelles entrées Notion basées sur ses apprentissages

---

### 3.10 — 🔌 CONNEXIONS

**Route** : `/settings/connections`

Hub de toutes les intégrations externes.

#### Connexions prévues

| Service | Usage | API | Priorité |
|---------|-------|-----|----------|
| **Notion** | Knowledge base CRO, sync bidirectionnel | Notion API v1 | P0 |
| **Catchr** | Analytics multi-plateforme (80+ sources), KPIs dashboard | REST API | P0 |
| **Frame.io** | Upload/gestion des assets vidéo et visuels | Frame.io API v2 | P1 |
| **Ads Society** | Données des campagnes paid (Meta, Google, TikTok) | Custom API | P1 |
| **Netlify** | Déploiement des pages générées | Netlify API | P1 |
| **Vercel** | Déploiement alternatif | Vercel API | P2 |
| **Cloudflare** | CDN + domaines custom | CF API | P2 |
| **Slack** | Notifications d'activité, alertes | Slack Webhooks | P2 |
| **Google Analytics** | Données de performance pages | GA4 Data API | P2 |

#### UI de chaque connexion

```
┌──────────────────────────────────────────┐
│  🟢 Notion        Connecté               │
│  Workspace: Growth Society CRO           │
│  Dernière sync: il y a 12 min            │
│  [Configurer] [Déconnecter]              │
├──────────────────────────────────────────┤
│  🟡 Catchr         En attente            │
│  API Key: ****_7f3a                       │
│  [Tester la connexion] [Configurer]      │
├──────────────────────────────────────────┤
│  ⚪ Frame.io       Non connecté           │
│  [Connecter]                              │
└──────────────────────────────────────────┘
```

---

### 3.11 — ⚙️ PARAMÈTRES

**Route** : `/settings`

#### Sous-pages

**Général** :
- Nom de l'organisation
- Logo
- Langue par défaut
- Fuseau horaire
- Thème UI (light/dark/auto)

**Équipe** :
- Liste des membres (nom, email, rôle, avatar)
- Rôles : Admin, Manager, Éditeur, Viewer
- Invitations

**IA** :
- Modèle par défaut (Claude Sonnet / Opus)
- Température de génération
- Profondeur d'audit par défaut
- Auto-apprentissage ON/OFF
- Mémoire IA : voir/éditer/purger

**Déploiement** :
- Domaine par défaut pour les pages générées
- Configuration Netlify/Vercel
- Template de déploiement
- Préfixe de nommage des fichiers

**Notifications** :
- Email, Slack, In-app
- Quand notifier : audit terminé, reco validée, page déployée, sync Notion, alerte performance

---

## 4. CRUD — OPÉRATIONS TRANSVERSALES

Chaque entité principale supporte le CRUD complet :

| Entité | Create | Read | Update | Delete | Historique |
|--------|--------|------|--------|--------|------------|
| Client | ✅ Form + import CSV | ✅ Fiche détaillée | ✅ Inline edit | ✅ Archive (soft) | ✅ |
| Audit | ✅ Wizard 3 étapes | ✅ Rapport complet | ✅ Ré-audit | ✅ Archive | ✅ |
| Recommandation | ✅ Auto (audit) + manuelle | ✅ Détail + copy | ✅ Statut, priorité, copy | ✅ Supprimer | ✅ |
| Page (GSG) | ✅ Wizard 4 étapes | ✅ Preview + code | ✅ Inline edit + regen | ✅ Archive | ✅ Versions |
| Asset | ✅ Upload + Frame.io | ✅ Preview + meta | ✅ Tags, description | ✅ Supprimer | ✅ |
| Template | ✅ Auto (score>120) + manuelle | ✅ Preview + meta | ✅ Tags, score | ✅ Retirer | ✅ |
| Pattern | ✅ Extraction + manuelle | ✅ Preview + code | ✅ Score, tags | ✅ Retirer | ✅ |
| Référence LP | ✅ URL + screenshot auto | ✅ Preview + notes | ✅ Tags, analyse | ✅ Supprimer | ✅ |
| Notion Page | ✅ Depuis Notion (sync) | ✅ Contenu indexé | ✅ Via Notion | — | Via Notion |

### Principes CRUD
- **Soft delete partout** — rien n'est supprimé définitivement, tout va en archive
- **Historique/Versioning** — chaque modification est enregistrée avec diff
- **Sauvegarde auto** — toutes les 30 secondes en mode édition
- **Undo/Redo** — Ctrl+Z/Y fonctionnel sur toutes les éditions
- **Duplication** — chaque entité peut être dupliquée en un clic
- **Export** — chaque vue peut être exportée (CSV, JSON, PDF selon le contexte)

---

## 5. SCHÉMA DE BASE DE DONNÉES (Supabase / PostgreSQL)

### Tables principales

```sql
-- Organisations
organizations (id, name, logo_url, settings_json, created_at)

-- Utilisateurs
users (id, org_id, email, name, avatar_url, role, created_at)

-- Clients
clients (id, org_id, name, sector, business_model, budget_ads,
         pipeline_stage, brand_context_json, manager_id,
         created_at, updated_at, archived_at)

-- Audits
audits (id, client_id, user_id, input_type, input_url, input_html,
        page_type, config_json, score_total, score_breakdown_json,
        findings_json, status, created_at, completed_at)

-- Recommandations
recommendations (id, audit_id, client_id, priority, category,
                 title, description, copy_rewrite, effort,
                 impact_low, impact_high, status, validated_by,
                 created_at, updated_at)

-- Pages (GSG)
pages (id, client_id, user_id, page_type, brief_json,
       da_config_json, html_content, score_total,
       score_breakdown_json, version, status,
       deployed_url, created_at, updated_at)

-- Page Versions
page_versions (id, page_id, version, html_content,
               score_total, diff_json, created_at, created_by)

-- Assets
assets (id, client_id, file_url, file_type, file_size,
        name, description, tags, ai_generated, source,
        created_at, uploaded_by)

-- Templates (bibliothèque CRO)
templates (id, name, page_type, sector, html_content,
           score, lift_range, tags, source_page_id,
           created_at, curated_by)

-- Patterns (swipe library)
patterns (id, category, name, html_snippet, score,
          sectors, tags, source, created_at)

-- Références LP
lp_references (id, url, screenshot_url, category, tags,
               is_good_example, notes, audit_score,
               created_at, added_by)

-- Notion Sync
notion_pages (id, notion_page_id, title, content_text,
              embedding, last_synced_at, created_at)

-- Connexions
connections (id, org_id, service_name, config_json,
             status, last_checked_at, created_at)

-- Activité
activity_log (id, org_id, user_id, entity_type, entity_id,
              action, details_json, created_at)

-- Apprentissages IA
ai_learnings (id, org_id, insight, source_type, source_id,
              confidence, tags, created_at)
```

### Index recommandés
- `clients`: org_id, pipeline_stage, sector, manager_id
- `audits`: client_id, status, score_total
- `recommendations`: audit_id, client_id, status, priority
- `pages`: client_id, status, score_total
- `activity_log`: org_id, entity_type, created_at (DESC)
- `notion_pages`: embedding (pgvector ivfflat index pour la recherche sémantique)

---

## 6. FLUX PRINCIPAUX (USER JOURNEYS)

### Flux 1 — Nouveau client complet
```
1. Dashboard → "+ Nouveau" → "Nouveau client"
2. Formulaire client (nom, secteur, budget, URL site, brand context)
3. → Fiche client créée
4. → Bouton "Lancer un audit" → Wizard audit (URL pré-remplie)
5. → Audit terminé → Score + Findings
6. → Bouton "Générer les recos" → Liste de recos priorisées
7. → Bouton "Envoyer au GSG" → Wizard GSG (brief pré-rempli depuis audit+recos)
8. → Page générée → Preview → Score /153
9. → Déployer → URL live
10. → Catchr commence à tracker → Données remontent au Dashboard
```

### Flux 2 — Quick audit d'une URL
```
1. Sidebar → Growth Audit → "Nouvel audit"
2. Coller URL → Auto-detect type de page
3. Audit express (pas de client associé)
4. Résultat → Quick Wins immédiats
5. Option : "Associer à un client" / "Sauvegarder dans les références"
```

### Flux 3 — Génération rapide
```
1. Sidebar → GSG → "Quick Start"
2. 3 champs : Client, Type, URL de référence
3. IA génère brief + DA + copy + page en un shot
4. Preview → Ajustements → Deploy
```

### Flux 4 — Apprentissage continu
```
1. Catchr détecte une page avec CVR > 5%
2. → Notification : "La LP Luko v3 performe exceptionnellement"
3. → IA analyse ce qui fonctionne → Génère un insight
4. → Insight ajouté à ai_learnings
5. → Pattern hero extrait → Ajouté à la Pattern Library
6. → Template marqué "Top performer"
7. → Prochaine génération pour un client InsurTech = enrichie de cet apprentissage
```

---

## 7. CARTE DES SKILLS & INTÉGRATIONS INTER-MODULES

### 7.0 — Écosystème de skills Claude (Phase 1 — cerveau IA)

Chaque module de la webapp est alimenté par un skill Claude dédié. En Phase 1 (actuelle), ces skills fonctionnent via conversation Claude. En Phase 2 (webapp), ils seront appelés via l'API Claude en backend.

```
                    ┌─────────────────────┐
                    │   CLIENT CONTEXT     │
                    │     MANAGER          │
                    │  (hub central)       │
                    └──────┬──────────────┘
                           │ brand, persona,
                           │ objectifs, historique
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
    │  GROWTH     │ │    GSG      │ │   DASHBOARD     │
    │  AUDIT      │ │  + Design   │ │   ENGINE        │
    │  /108       │ │  Engine v2  │ │   KPIs + AI     │
    │             │ │  /153       │ │   Insights      │
    └──────┬──────┘ └──────┬──────┘ └────────┬────────┘
           │               │                  │
           │  findings     │  pages           │  métriques
           │  teardowns    │  templates       │  alertes
           ▼               ▼                  ▼
    ┌─────────────────────────────────────────────────┐
    │              CRO LIBRARY                         │
    │  Templates + Patterns + Références + Teardowns   │
    └──────────────────────┬──────────────────────────┘
                           │
                           │ knowledge enrichi
                           ▼
    ┌─────────────────────────────────────────────────┐
    │         NOTION SYNC & AI LEARNING ENGINE         │
    │  Sync bidirectionnel + Embeddings + Insights     │
    └──────────────────────┬──────────────────────────┘
                           │
                           │ données externes
                           ▼
    ┌─────────────────────────────────────────────────┐
    │           CONNECTIONS MANAGER                     │
    │  Notion | Catchr | Frame.io | Ads Society |      │
    │  Netlify | Slack | GA4 | Meta Ads | Google Ads   │
    └─────────────────────────────────────────────────┘
```

### Matrice d'intégrations skill ↔ skill

| Source ↓ / Cible → | Client Context | Growth Audit | GSG | CRO Library | Dashboard | Notion Sync | Connexions |
|---------------------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Client Context** | — | contexte audit | brand+DA | filtre secteur | KPIs client | — | — |
| **Growth Audit** | historique | — | brief GSG | teardowns+patterns | score Ø | insights | Catchr data |
| **GSG** | pages générées | — | — | auto-add templates | pages count | patterns DA | deploy+assets |
| **CRO Library** | — | benchmarks | templates+patterns | — | — | knowledge | — |
| **Dashboard** | — | alertes | — | — | — | insights | Catchr+Ads |
| **Notion Sync** | — | knowledge CRO | knowledge CRO | knowledge | insights | — | Notion API |
| **Connexions** | perf data | perf data | deploy+assets | — | live metrics | Notion API | — |

### Skills créés

| Skill | Dossier | Fichiers |
|-------|---------|----------|
| Client Context Manager | `skills/client-context-manager/` | SKILL.md, context_schema.md, enrichment_prompts.md, brand_analysis.md, memory.md |
| Growth Audit (existant, mis à jour) | `skills/cro-auditor/` | SKILL.md (intégrations ajoutées), audit_criteria.md, reco_engine.md, memory.md |
| GSG (existant, mis à jour) | `skills/growth-site-generator/` | SKILL.md (Phase 0.0 + intégrations), design_engine.md, conversion_psychology.md, memory.md |
| CRO Library | `skills/cro-library/` | SKILL.md, library_schema.md, memory.md |
| Dashboard Engine | `skills/dashboard-engine/` | SKILL.md, kpi_definitions.md, memory.md |
| Notion Sync & AI Learning | `skills/notion-sync/` | SKILL.md, sync_protocol.md, learning_engine.md, memory.md |
| Connections Manager | `skills/connections-manager/` | SKILL.md, integrations_spec.md, memory.md |

---

## 8. STACK TECHNIQUE DÉTAILLÉE

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Frontend** | Next.js 14 (App Router) | SSR/SSG, RSC, routing natif, déploiement Vercel |
| **UI Components** | shadcn/ui + Tailwind CSS | Composants accessibles, customisables, pas de vendor lock |
| **State** | Zustand (global) + React Query (server) | Léger, performant, cache intelligent |
| **DB** | Supabase PostgreSQL | Hébergé, temps réel, pgvector, Row Level Security |
| **Auth** | Supabase Auth | Magic link + Google SSO |
| **Storage** | Supabase Storage | Assets, screenshots, HTML générés |
| **Realtime** | Supabase Realtime | Activity feed, notifications |
| **Vector Search** | pgvector (Supabase) | Recherche sémantique dans la base Notion |
| **AI** | Claude API (Anthropic) | Audits, recos, génération, insights |
| **Déploiement app** | Vercel | Edge functions, preview branches, analytics |
| **Déploiement pages** | Netlify / Vercel | Pages générées par le GSG |
| **Analytics pages** | Catchr API | 80+ sources de données |
| **Assets vidéo** | Frame.io API | Upload, review, versions |
| **Knowledge** | Notion API | Sync bidirectionnel |
| **Monitoring** | Sentry + Vercel Analytics | Erreurs + performance |

---

## 8. PRIORITÉS DE DÉVELOPPEMENT

### Phase 1 — MVP (Semaines 1-4)
- [ ] Auth + org setup
- [ ] Sidebar navigation
- [ ] Dashboard (KPIs statiques d'abord)
- [ ] CRUD Clients complet
- [ ] Client Context Manager (brand context)
- [ ] Growth Audit wizard (connecté au skill cro-auditor)
- [ ] Recommandations (auto-générées depuis audit)

### Phase 2 — Générateur (Semaines 5-8)
- [ ] GSG wizard (connecté au skill growth-site-generator)
- [ ] Live preview avec device switching
- [ ] Score /153 en temps réel
- [ ] Page versioning
- [ ] Déploiement Netlify

### Phase 3 — Intelligence (Semaines 9-12)
- [ ] Bibliothèque CRO (templates + patterns)
- [ ] Bibliothèque Assets
- [ ] Références LP
- [ ] Base Notion CRO (sync)
- [ ] Pattern Library

### Phase 4 — Connexions & Performance (Semaines 13-16)
- [ ] Connexion Catchr → Dashboard dynamique
- [ ] Connexion Frame.io
- [ ] Connexion Ads Society
- [ ] Système d'apprentissage IA
- [ ] Insights automatiques
- [ ] Notifications (email, Slack, in-app)

### Phase 5 — Polish & Scale (Semaines 17-20)
- [ ] Paramètres complets
- [ ] Export PDF rapports clients
- [ ] Comparaison A/B de versions
- [ ] Dashboard avancé (graphiques temps réel)
- [ ] Onboarding flow
- [ ] Documentation interne

---

## 9. CE QUI FAIT QUE C'EST "MILLE FOIS MIEUX" QUE ROCKET

| Dimension | Rocket | GrowthCRO |
|-----------|--------|-----------|
| **Design UI** | Dark mode forcé, générique | Light mode premium, anti-AI-slop |
| **Intelligence** | IA en sidebar, décorative | IA = le moteur de chaque feature |
| **Audit** | Formulaire à cocher | Crawl IA automatique, /108 |
| **Génération** | Templates statiques | Design Engine v2.0, /153, DA unique |
| **Apprentissage** | Aucun | Auto-apprentissage continu (Notion + patterns + insights) |
| **Performance** | Pas de données réelles | Catchr intégré, métriques live |
| **CRUD** | Basique | Versioning, historique, soft delete, undo |
| **Connexions** | Basique | Frame.io, Catchr, Ads Society, Notion, Netlify |
| **Copy** | Manuel | Frameworks copy IA (PAS, AIDA...) + Psychology Engine |
| **Collaboration** | Mono-user feeling | Multi-user, activité temps réel, assignations |
| **Export** | HTML seulement | HTML, PDF, Brief GSG, CSV, React bundle |
