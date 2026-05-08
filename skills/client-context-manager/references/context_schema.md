# Client Context Schema — Référence complète

## Vue d'ensemble

Le Client Context est structuré en 7 blocs. Chaque bloc a un niveau de complétude qui contribue au **Context Score** global.

| Bloc | Poids | Champs | Minimum requis |
|------|-------|--------|----------------|
| Identity | 10% | 8 | Nom + URL ou secteur |
| Strategy | 20% | 12 | Objectif principal |
| Audience | 25% | 15 | Persona principal + pain + desire |
| Brand | 20% | 14 | Palette OU URL (pour extraction) |
| Competition | 10% | 6 | 1 concurrent minimum |
| Traffic | 10% | 8 | Source principale |
| Performance | 5% | 6 | CVR actuel ou "inconnu" |

### Context Score
- **0-30%** : Squelette — suffisant pour un audit rapide
- **31-60%** : Fonctionnel — suffisant pour un audit standard et une génération basique
- **61-80%** : Solide — toutes les features GrowthCRO fonctionnent bien
- **81-100%** : Premium — outputs IA de qualité maximale

### Règle d'or
**Ne jamais bloquer un workflow parce que le contexte est incomplet.** Toujours permettre de travailler avec ce qu'on a, mais signaler ce qui manque et proposer l'enrichissement.

---

## Champs détaillés par bloc

### 1. IDENTITY

| Champ | Type | Requis | Auto-enrichi | Exemple |
|-------|------|--------|--------------|---------|
| name | string | ✅ | ❌ | "Luko Insurance" |
| legal_name | string | ❌ | ❌ | "Luko SAS" |
| logo_url | url | ❌ | ✅ (extraction) | "https://..." |
| url | url | ✅* | ❌ | "https://luko.eu" |
| urls_secondary | url[] | ❌ | ✅ (crawl) | ["https://luko.eu/blog"] |
| sector | enum | ✅ | ✅ (détection) | "InsurTech" |
| sub_sector | string | ❌ | ✅ | "Assurance habitation" |
| business_model | object | ✅ | ✅ | {type, revenue, ticket_moyen} |

*URL requise sauf si client sans site web (pré-lancement)

#### Taxonomy des secteurs
```
E-commerce / D2C
SaaS / B2B
SaaS / B2C
Services / B2B
Services / B2C
Lead Gen
InsurTech
FinTech
HealthTech / Wellness
EdTech
FoodTech
PropTech / Immobilier
Travel / Hospitality
Fashion / Luxury
Beauty / Cosmetics
Sport / Fitness
Media / Entertainment
Non-profit
Marketplace
App Mobile
Autre
```

### 2. STRATEGY

| Champ | Type | Requis | Auto-enrichi |
|-------|------|--------|--------------|
| objective_primary | object | ✅ | ❌ |
| objective_primary.type | enum | ✅ | ✅ |
| objective_primary.kpi | string | ❌ | ❌ |
| objective_primary.deadline | date | ❌ | ❌ |
| objectives_secondary | object[] | ❌ | ❌ |
| budget_ads_monthly | number | ❌ | ❌ |
| team_capacity | string | ❌ | ❌ |
| technical_constraints | string[] | ❌ | ❌ |
| pipeline_stage | enum | ✅ | ✅ (= "brief_recu") |
| manager | string | ❌ | ❌ |
| priority | enum(P0,P1,P2,P3) | ❌ | ✅ (= P1) |
| tags | string[] | ❌ | ❌ |

#### Pipeline stages
```
brief_recu → audit_en_cours → recos_generees → recos_validees → build_en_cours → review → deploye → monitoring → archive
```

### 3. AUDIENCE

| Champ | Type | Requis | Auto-enrichi |
|-------|------|--------|--------------|
| persona_primary.name | string | ✅ | ✅ |
| persona_primary.demographics | object | ❌ | ✅ |
| persona_primary.pain_primary | string | ✅ | ✅ |
| persona_primary.pains_secondary | string[] | ❌ | ✅ |
| persona_primary.desire_primary | string | ✅ | ✅ |
| persona_primary.objections | string[] | ✅ | ✅ |
| persona_primary.awareness_level | enum | ✅ | ✅ |
| persona_primary.channels | string[] | ❌ | ✅ |
| persona_primary.triggers | string[] | ❌ | ✅ |
| personas_secondary | object[] | ❌ | ❌ |
| anti_personas | string[] | ❌ | ❌ |

#### Niveaux de conscience Schwartz
```
1. unaware — Ne sait pas qu'il a un problème
2. problem_aware — Sait qu'il a un problème, cherche une solution
3. solution_aware — Connaît le type de solution, compare les options
4. product_aware — Connaît le produit, hésite encore
5. most_aware — Prêt à acheter, cherche le meilleur deal/moment
```

### 4. BRAND

| Champ | Type | Requis | Auto-enrichi |
|-------|------|--------|--------------|
| palette.primary | hex | ✅* | ✅ |
| palette.secondary | hex | ❌ | ✅ |
| palette.accent | hex[] | ❌ | ✅ |
| palette.background | hex | ❌ | ✅ |
| palette.text | hex | ❌ | ✅ |
| palette.cta | hex | ❌ | ✅ |
| typography.display | string | ❌ | ✅ |
| typography.body | string | ❌ | ✅ |
| tone | object(5 axes) | ❌ | ✅ |
| ambiance_register | enum(8) | ❌ | ✅ |
| visual_keywords | string[3-5] | ❌ | ✅ |
| references_liked | url[] | ❌ | ❌ |
| references_disliked | url[] | ❌ | ❌ |

*Requis sauf si URL fournie (extraction auto)

### 5. COMPETITION

| Champ | Type | Requis | Auto-enrichi |
|-------|------|--------|--------------|
| competitors_direct | object[] | ✅ (1 min) | ✅ |
| competitors_indirect | object[] | ❌ | ✅ |
| substitutes | string[] | ❌ | ✅ |
| positioning | object | ❌ | ✅ |

### 6. TRAFFIC

| Champ | Type | Requis | Auto-enrichi |
|-------|------|--------|--------------|
| paid.platforms | enum[] | ❌ | ❌ |
| paid.budget_monthly | number | ❌ | ❌ |
| paid.best_audiences | string[] | ❌ | ❌ |
| organic.seo_keywords | string[] | ❌ | ✅ |
| organic.social | string[] | ❌ | ❌ |
| primary_source | enum | ✅ | ✅ |

### 7. PERFORMANCE

| Champ | Type | Requis | Auto-enrichi |
|-------|------|--------|--------------|
| traffic_monthly | number | ❌ | ❌ |
| bounce_rate | number | ❌ | ❌ |
| current_cvr | number | ❌ | ❌ |
| target_cvr | number | ❌ | ❌ |
| best_cvr | number | ❌ | ❌ |
| cpa_current | number | ❌ | ❌ |
