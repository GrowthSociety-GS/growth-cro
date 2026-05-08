# GrowthCRO — Spécifications techniques

> Source de vérité des specs : entités, store, grille critères V2, data shapes, APIs futures.

## Stack

- **Front** : Next.js 15 (App Router) + React 19 + TypeScript strict + Tailwind.
- **State** : GrowthStore (React Context + useReducer + localStorage persistence).
- **UI kit** : lucide-react, sonner, Fraunces serif + Geist sans/mono.
- **Backend futur** : Supabase (auth + DB + storage). Pour l'instant : JSON + localStorage.
- **Prototypes** : HTML standalone dans `prototype/` pour itérer sans `npm run dev`.

## Entités principales

```ts
Client { id, name, url, icon, category, pipelineStage, ... }
Audit { id, clientId, pageType, score, maxScore, verdict, categories, criteriaDetails, problems, wins, waves, rewrites, createdAt }
Recommendation { id, auditId, priority: 'P0'|'P1'|'P2', title, why, how, effort, impact, status: 'open'|'implemented' }
Page { id, clientId, type, html, score, createdAt }           // sortie GSG
GrowthAsset { id, type, tags, url, source }                   // Library
GrowthRef { id, brand, url, category, businessType, audited Pages[], patterns[] }
NotionDoc { id, notionId, title, ... }                        // read-only
Connexion { id, type, status }
```

## GrowthStore API (Context + useReducer)

Actions :
`selectClient`, `upsertClient`, `upsertAudit`, `selectAudit`, `upsertReco`, `markRecoImplemented`, `upsertPage`, `upsertGrowthAsset`, `upsertRef`, `setNotionDocs`, `setConnexions`.

Persistence : `localStorage.setItem('growthcro:v1', JSON.stringify(state))` sur chaque action (debounced).

## Pipeline stage heuristique (depuis score)

```
score === 0          → Discovery
0 < score < 55       → Audit
55 ≤ score < 65      → Recos
65 ≤ score < 75      → Build
score ≥ 75           → Live
```

## Grille CRO V2 — segmentée par type de page

### Types de page couverts

1. **Home** (acquisition + réassurance globale)
2. **LP Produit / Service** (advertorial, sales, squeeze, lead-gen, e-com PDP)
3. **Collection / Catégorie**
4. **Blog / Article (listicle, SEO, advertorial éditorial)**
5. **Quiz / VSL / Challenge**
6. **Pricing**
7. **Checkout / Cart**

### Catégories business couvertes

DTC Beauty, DTC Food, SaaS B2B, SaaS B2C, Fintech, Formation / Infoproduit, Abonnement / Box, Marketplace, Luxe / Premium, Health / Wellness.

### Structure de la grille V2

Chaque couple `(pageType, businessCategory)` active un sous-ensemble de **piliers** avec pondérations spécifiques.

**6 piliers universels** (toujours présents, poids variables) :

| Pilier | Description | Poids défaut |
|---|---|---|
| **Cohérence Stratégique** | Message-market fit, promesse claire, alignement ad→LP, cible identifiable. | /18 |
| **Hero / ATF** | H1, sous-titre, visuel, CTA principal, preuve sociale visible sans scroll. | /18 |
| **Persuasion & Copy** | Angle, bénéfices > features, storytelling, preuves, objections levées, ton. | /24 |
| **Structure & UX** | Hiérarchie, rythme, scan-ability, navigation, friction, micro-interactions. | /24 |
| **Qualité Technique** | LCP, CLS, mobile, accessibilité, SEO on-page, tracking. | /15 |
| **Psychologie & Biais** | Preuve sociale, autorité, scarcité, réciprocité, loss aversion, ancrage, storytelling émotionnel. | /18 |

**Total : /117** (remplace l'ancien /90 + /18 psycho dispersés).

Design ajouté par le GSG : /45. **GSG score global : /162**.

### Critères par page type (extrait)

Chaque pilier contient **N critères** de 0 à 3 points. Chaque critère a : `id`, `label`, `description`, `pageTypes[]`, `businessTypes[]|"*"`, `weight`, `checkMethod` (visual/textual/technical/heuristic), `examples[]`, `antiPatterns[]`.

Exemples de critères spécifiques :
- **Home × DTC Food** : "Hero montre le produit en contexte d'usage (main tenant le produit, table dressée)" (Hero, 3 pts).
- **LP Produit × DTC Beauty** : "Avant/après visible dans le fold 1 ou 2" (Persuasion, 3 pts).
- **Pricing × SaaS B2B** : "Plan recommandé visuellement ancré (badge + scale)" (Psycho/Ancrage, 3 pts).
- **Checkout × tous** : "Nombre d'étapes ≤ 3 et indicateur de progression" (Structure, 3 pts).

Fichier complet : `data/cro_criteria_v2.json`.

## Data shapes clés

### Audit (shape V5.1 → V5.2)

```json
{
  "id": "audit_ocni_home_v2",
  "clientId": "ocni",
  "pageType": "home",
  "businessCategory": "dtc_food",
  "url": "https://ocnifactory.com",
  "score": 00,
  "maxScore": 117,
  "verdict": "…",
  "categories": {
    "coherence": { "label": "Cohérence Stratégique", "score": 0, "max": 18, "pct": 0, "color": "amber" },
    "hero":      { "label": "Hero / ATF",           "score": 0, "max": 18, "pct": 0, "color": "red" },
    "persuasion":{ "label": "Persuasion & Copy",    "score": 0, "max": 24, "pct": 0, "color": "amber" },
    "ux":        { "label": "Structure & UX",       "score": 0, "max": 24, "pct": 0, "color": "green" },
    "tech":      { "label": "Qualité Technique",    "score": 0, "max": 15, "pct": 0, "color": "green" },
    "psycho":    { "label": "Psychologie & Biais",  "score": 0, "max": 18, "pct": 0, "color": "amber" }
  },
  "criteriaDetails": [
    { "cat": "1", "id": "…", "label": "…", "score": 0, "max": 3, "status": "critical|ok|top", "comment": "…" }
  ],
  "problems": [ { "title": "…", "impact": "high|medium|low", "detail": "…" } ],
  "wins":     [ { "title": "…", "detail": "…" } ],
  "waves": [
    { "id": 1, "label": "Quick wins", "horizon": "< 48h", "actions": [ { "title": "…", "effort": "low|medium|high", "impact": "…", "owner": "copy|design|dev|growth" } ] }
  ],
  "rewrites": [ { "section": "Hero", "before": "…", "after": "…", "why": "…" } ],
  "benchmarks": [ { "refId": "oatly", "dimension": "Hero", "insight": "…" } ]
}
```

### GrowthRef

```json
{
  "id": "oatly",
  "brand": "Oatly",
  "url": "https://oatly.com",
  "category": "dtc_food",
  "businessType": "e-commerce",
  "pagesAudited": ["home", "pdp", "collection"],
  "patterns": [
    { "pillar": "Hero", "pattern": "Hero typographique oversized + ton absurde", "impact": "Mémorable, différenciant", "criteriaIds": ["hero_h1_impact", "copy_ton_unique"] }
  ],
  "whyItConverts": "…",
  "screenshots": []
}
```

## Sidebar V4/V5 (structure figée)

1. **Vision** — Dashboard
2. **Clients** — Liste + détail projet
3. **Audit** — Hub + détail (onglets Overview/Critères/Waves/Rewrites)
4. **Recommandations** — Builder
5. **GSG** (Growth Site Generator) — Brief + génération
6. **Growth Library** (expandable)
   - Growth Assets
   - Growth Refs
   - Growth Patterns
7. **Notion** — Read-only browser
8. **Connexions** — MCPs + intégrations

## Règles de mémoire

- Lire `PROJECT_MEMORY.md` (index) à chaque début de session.
- Lire `memory/HISTORY.md` pour la chronologie.
- Lire `memory/SPECS.md` pour les specs techniques.
- Mettre à jour les 3 fichiers à chaque milestone.
- Notion : **jamais d'écriture sans permission explicite** par occurrence.
