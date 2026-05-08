# GrowthCRO — Routing & Dataflow V1

> Document de référence : la carte des routes Next.js, des sous-onglets,
> et **la communication bidirectionnelle** entre modules via le `GrowthStore`.
>
> Note V26.AH (2026-05-04) : ce document décrit la cible webapp long-terme. Pour le runtime actuel et les frontières anti-régression, lire `architecture/PRODUCT_BOUNDARIES_V26AH.md`. La bidirectionnalité cible ne doit pas redevenir des déclenchements silencieux entre moteurs.
>
> ⚠️ **Principe fondateur** : GrowthCRO n'est PAS un pipeline linéaire
> (audit → reco → GSG → fin). C'est un **graphe bidirectionnel** où
> chaque module lit ET écrit dans le store commun, et où chaque action
> dans un module peut déclencher des mises à jour dans n'importe quel
> autre module. C'est ce qui permet l'auto-apprentissage continu.

---

## 1. Routes Next.js (App Router)

| Route | Module | Sidebar group |
|---|---|---|
| `/client-dashboard` | Dashboard | Overview |
| `/cro-audit-generator` | Audit & Recos | CRO Workflow |
| `/recommendations-builder` | Recos (détail) | (interne) |
| `/html-page-generator` | Site Generator (GSG) | CRO Workflow |
| `/client-project-detail` | Clients (CRM) | Projets |
| `/growth-library?tab=clients` | Growth Library — Clients Assets | Growth Library |
| `/growth-library?tab=growth` | Growth Library — Growth Assets | Growth Library |
| `/growth-library?tab=refs` | Growth Library — Growth Refs | Growth Library |
| `/notion-knowledge-base` | Base Notion CRO | Agence |
| `/connexions` *(à créer)* | Connexions | Système |
| `/parametres` *(à créer)* | Paramètres | Système |

Les anciennes routes `asset-library`, `template-library`, `reference-library`
sont **dépréciées** au profit de `/growth-library` unifiée.

---

## 2. Le Store global (`growthStore.tsx`)

Un seul `GrowthProvider` monté dans `app/layout.tsx`. Tous les modules
appellent `useGrowth()` pour lire et écrire.

### Entités persistées
- **Client**, **Audit**, **Recommendation**, **Asset**, **LpReference**, **GeneratedPage**

### État de navigation (partagé entre modules)
- `selectedClientId` — le contexte client actif, injecté partout
- `selectedAuditId` — audit actif
- `selectedAssetIdsForGsg[]` — assets piqués pour la prochaine génération

### Persistance
LocalStorage `growthcro:state:v1` (en attendant Supabase).

---

## 3. Communication BIDIRECTIONNELLE — la matrice complète

**Chaque cellule = un flux de données entre un module Source (ligne) et un module Cible (colonne).**
Un même module peut apparaître à la fois comme source et comme cible.

| Source ↓ / Cible → | Dashboard | Clients | Audit | Recos | GSG | Library-Clients | Library-Growth | Library-Refs | Notion | Connexions |
|---|---|---|---|---|---|---|---|---|---|---|
| **Dashboard** | — | drill-down vers fiche | alerte "ré-auditer" | alerte "reco stale" | alerte "page underperform" | — | — | — | affiche derniers insights | affiche statut sync |
| **Clients** | feed KPIs (pipeline, scores Ø) | — | lance audit (URL pré-remplie + brand context) | filtre recos par client | brief GSG pré-rempli (brand context) | filtre assets du client | — | — | contexte client → contexte IA | perf Catchr du client |
| **Audit** | MAJ score Ø client, alerte dashboard | MAJ statut pipeline ("audit" → "recos") | — | génère recos auto (P0/P1/P2) | envoie findings + URL au brief GSG | — | — | alimente LpReference si URL externe auditée | propose ajout Notion sur patterns découverts | tire données Catchr pour pondérer |
| **Recos** | feed "Recos validées this week" | MAJ statut client ("recos" → "build") | — | — | envoie reco.copy_rewrite au GSG step copy | — | — | — | propose ajout Notion sur reco validée | — |
| **GSG** | feed "Pages générées", score moyen /153 | ajoute page à la galerie client | MAJ audit cible ("addressed by page X") | marque recos "implemented" quand page deployée | — | **lit** assets sélectionnés (clients) | **lit** assets sélectionnés (growth) | utilise refs comme inspiration DA | lit knowledge CRO pour enrichir copy | deploy Netlify/Vercel |
| **Library — Clients Assets** | feed nombre d'assets par client | lié à fiche client | — | — | **écrit** dans selectedAssetIdsForGsg | — | cross-ref (variantes) | — | — | upload Frame.io |
| **Library — Growth Assets** | feed nombre d'assets totaux | — | — | — | **écrit** dans selectedAssetIdsForGsg | — | — | — | — | gen IA externe |
| **Library — Growth Refs** | feed "nouvelles refs indexées" | — | **déclenche** un audit sur l'URL de ref | — | envoie l'URL comme référence visuelle DA | — | — | — | enrichit Notion avec teardowns | — |
| **Notion** | feed derniers learnings IA | — | injecte knowledge dans contexte audit | injecte knowledge dans reco templates | injecte knowledge dans prompts copy | — | — | tag refs avec insights Notion | — | sync Notion API |
| **Connexions (Catchr, Frame, Ads, Netlify, Notion)** | alimente TOUS les KPIs live | perf par client | pondère scores par données réelles | valide/invalide recos par perf | tracking post-deploy | Frame → assets | — | — | Notion API | — |

### Lectures clés par module

Quand tu ouvres un module, voici ce qu'il **lit** du store et où il **écrit** :

**Dashboard** `/client-dashboard`
- LIT : `clients`, `audits`, `recommendations`, `pages`, `ai_learnings` (tous)
- ÉCRIT : rien directement, déclenche navigation

**Clients** `/client-project-detail`
- LIT : `clients`, `getAuditsForClient()`, `getClientAssets()`, `pages` filtrées
- ÉCRIT : `upsertClient()`, `selectClient()`

**Audit** `/cro-audit-generator`
- LIT : `getSelectedClient()` (brand context auto-injecté), `lpReferences` (benchmarks secteur), `notionContext` (knowledge CRO)
- ÉCRIT : `upsertAudit()`, `upsertReco(×N)`, MAJ score Ø du client

**Recos** `/recommendations-builder`
- LIT : `getRecosForAudit()`, `getSelectedClient()`
- ÉCRIT : `upsertReco()` (changement de statut), push vers GSG

**GSG** `/html-page-generator`
- LIT : `getSelectedClient()` (brand), `getRecosForAudit()` (copy & priorités), `selectedAssetIdsForGsg[]` (médias), `lpReferences` (DA), `notionContext` (frameworks copy)
- ÉCRIT : `upsertPage()`, marque recos "implemented", ajoute patterns à la Library si score > 120

**Growth Library** (3 sous-onglets) `/growth-library`
- LIT : `assets`, `lpReferences`, `clients`
- ÉCRIT : `upsertAsset()`, `upsertLpRef()`, `toggleAssetForGsg()`

**Notion** `/notion-knowledge-base`
- LIT : pages Notion via API, `audits` et `recommendations` validés
- ÉCRIT : propose ajout de nouveaux insights au workspace Notion

**Connexions** `/connexions`
- LIT : config des services
- ÉCRIT : alimente en tâche de fond Catchr→pages perf, Frame→assets, etc.

---

## 4. Le graphe de flux (vue d'ensemble bidirectionnelle)

```
                         ┌──────────────────┐
                         │    DASHBOARD     │◄────────────┐
                         │  agrège TOUT     │             │
                         └────┬─────────────┘             │
                              │ alertes / drill-down      │ KPIs live
                              ▼                            │
          ┌───────────────────────────────────────┐        │
          │                                        │        │
          ▼                                        ▼        │
   ┌────────────┐  brand ctx  ┌─────────────┐  findings    │
   │  CLIENTS   │◄───────────►│    AUDIT    │─────────────►│
   │  (CRM)     │             │   /90       │              │
   └─────┬──────┘             └──┬──────┬───┘              │
         │ pipeline stage        │      │ génère           │
         │                       │      ▼                  │
         │                       │  ┌────────┐             │
         │                       │  │ RECOS  │             │
         │                       │  │P0/P1/P2│             │
         │                       │  └───┬────┘             │
         │                       │      │ copy_rewrite     │
         │                       │      │                  │
         │         brand ctx +   ▼      ▼                  │
         └──────────────────► ┌─────────────┐              │
                              │     GSG     │              │
         ┌──assets────────────►│  wizard 4   │◄───refs──┐   │
         │                    │   /153     │           │   │
         │                    └──┬──────┬──┘           │   │
         │                       │      │ upsertPage   │   │
         │                       │      ▼              │   │
         │                       │  ┌────────────┐     │   │
         │                       │  │ PAGES      │─────┼───┘
         │                       │  │ deployées  │     │ Catchr
         │                       │  └──┬─────────┘     │
         │                       │     │ perf          │
         │                       │     ▼               │
   ┌─────┴─────┐           ┌────────────────┐          │
   │  GROWTH   │           │  AI LEARNINGS  │          │
   │  LIBRARY  │◄──patterns│  (boucle       │          │
   │  ┌──────┐ │           │   d'appren-    │          │
   │  │clients│ │           │   tissage)    │          │
   │  ├──────┤ │           └───┬─────────┬──┘          │
   │  │growth│ │               │         │             │
   │  ├──────┤ │               ▼         ▼             │
   │  │refs  │─┼──────────► ┌──────┐  ┌────────────┐   │
   │  └──────┘ │ auto-audit │NOTION│  │ CONNEXIONS │◄──┘
   └───────────┘            │ sync │  │ Catchr/FIO │
                            │   ↕  │  │ Ads/Netlify│
                            └──┬───┘  └────────────┘
                               │
                               └─► enrichit TOUS les modules
                                    (injection contexte IA)
```

**Points cruciaux de bidirectionnalité** :
- **Client ↔ Audit** : le client injecte son brand context dans l'audit ; l'audit met à jour le score Ø et le pipeline stage du client.
- **Audit ↔ GSG** : l'audit pousse ses findings au GSG ; le GSG, quand il génère une page, marque les findings "addressed".
- **GSG ↔ Growth Library** : la Library pousse ses assets au GSG ; le GSG, quand il produit une page avec score > 120, pousse automatiquement ses patterns dans la Library.
- **Growth Refs ↔ Audit** : on ajoute une URL → audit auto déclenché → score renvoyé à la ref ; l'audit d'un client peut enrichir les refs si on analyse des concurrents.
- **Notion ↔ TOUT** : sync bidirectionnel. Notion alimente en contexte IA tous les modules ; en retour, les patterns/recos validés sont proposés en ajout Notion.
- **Catchr ↔ Pages ↔ Recos** : Catchr pousse la perf réelle ; les recos dont l'implémentation a produit du lift sont marquées "performante" ; celles qui n'ont rien changé sont marquées "inefficace" → apprentissage.
- **Dashboard ↔ TOUT** : le Dashboard lit l'état de tous les modules ET déclenche des actions (re-auditer, re-générer, alerter).

---

## 5. Points de branchement (où câbler dans les pages existantes)

| # | Flux | Source | Cible | Implémenté |
|---|---|---|---|---|
| 1 | select client → audit | `/client-project-detail` | `/cro-audit-generator` | ⏳ |
| 2 | audit terminé → recos | `/cro-audit-generator` | `/recommendations-builder` | ⏳ |
| 3 | recos → GSG | `/recommendations-builder` | `/html-page-generator` | ⏳ |
| 4 | library → GSG (assets) | `/growth-library` | `state.selectedAssetIdsForGsg` | ✅ |
| 5 | GSG lit brief complet | `/html-page-generator` | store reads | ⏳ |
| 6 | GSG → marque recos implemented | `/html-page-generator` | `upsertReco()` | ⏳ |
| 7 | GSG → ajoute patterns library si score > 120 | `/html-page-generator` | `upsertAsset()` | ⏳ |
| 8 | Growth Refs → auto-audit URL | `/growth-library?tab=refs` | `/cro-audit-generator` | ⏳ |
| 9 | Audit → enrichit Refs si URL externe | `/cro-audit-generator` | `upsertLpRef()` | ⏳ |
| 10 | Notion sync → contexte IA injecté | `/notion-knowledge-base` | tous les modules | partiel |
| 11 | Catchr → perf pages | `/connexions` | `pages[].perfMetrics` | ⏳ |
| 12 | Dashboard → alertes drill-down | `/client-dashboard` | navigations | ⏳ |

---

## 6. API du store (TL;DR)

```tsx
'use client';
import { useGrowth } from '@/lib/growthStore';

function MyModule() {
  const {
    state,
    selectClient, selectAudit,
    toggleAssetForGsg, clearAssetsForGsg,
    upsertClient, upsertAudit, upsertReco,
    upsertAsset, upsertLpRef, upsertPage,
    getSelectedClient, getAuditsForClient, getRecosForAudit,
    getClientAssets, getGrowthAssets,
  } = useGrowth();
  // ...
}
```

Toutes les écritures sont persistées en localStorage.
Quand Supabase sera branché, on remplace les `upsert*` par des mutations
Supabase + realtime subscriptions (les modules autres que celui qui écrit
verront les updates en live — vraie bidirectionnalité distribuée).

---

## 7. Sidebar — structure cible (V4)

```
Overview
  └ Dashboard

CRO Workflow
  ├ Audit & Recos      [3]
  └ Site Generator

Projets
  └ Clients            [7]

Growth Library         (expandable)
  ├ Clients Assets
  ├ Growth Assets
  └ Growth Refs

Agence
  └ Base Notion CRO

Système
  ├ Connexions
  └ Paramètres
```
