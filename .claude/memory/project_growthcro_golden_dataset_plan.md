# Golden Dataset ("Panthéon") — Plan de Sélection

**Date** : 2026-04-17
**Priorité** : #2 du plan V15.2 (après semantic scorer)
**Objectif** : 25-30 sites best-in-class comme référence de calibration
**Validé par Mathis** : OUI (séquence B — scorer d'abord, golden dataset ensuite)
**Mathis a demandé** : que Claude propose la sélection

---

## 1. POURQUOI UN GOLDEN DATASET

Le scoring actuel n'a PAS de ground truth. On ne sait pas à quoi ressemble un "3/3" sur chaque critère. Le golden dataset sert à :
1. **Calibrer** : vérifier que les sites parfaits scorent bien 3/3 sur les critères pertinents
2. **Détecter les faux négatifs** : si un site best-in-class score 0/3, le détecteur est cassé
3. **Entraîner les prompts** : les exemples réels améliorent les prompts du semantic scorer
4. **Benchmarker** : donner un point de comparaison aux clients

## 2. COUVERTURE REQUISE

### Business Types (10 catégories)
1. E-commerce DTC (beauty, food, fashion, wellness)
2. SaaS B2B
3. SaaS B2C
4. Lead gen / Services
5. Fintech
6. Luxury / Premium
7. Marketplace
8. Subscription / Box
9. App mobile
10. Formation / Infoproduit

### Page Types (8 types)
- home, pdp, collection, blog, pricing, checkout, landing_paid, quiz_vsl

### Matrice cible
Chaque site couvre 2-4 page types. Total : 25-30 sites × 3 pages en moyenne = 75-90 pages de référence.

## 3. SÉLECTION PROPOSÉE (28 sites)

### E-commerce DTC Beauty (3)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Glossier** (glossier.com) | Pioneer DTC beauty, hero minimaliste impactant, social proof native, parcours produit impeccable | home, pdp, collection |
| **Typology** (typology.com) | Quiz personnalisation, copy scientifique, UX mobile exemplaire | home, pdp, quiz_vsl |
| **Drunk Elephant** (drunkelephant.com) | Storytelling ingrédients, bénéfices > features, éducation produit | home, pdp |

### E-commerce DTC Food (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Japhy** (japhy.fr) | Déjà capturé, hero 16.5/18, baseline parfaite, DTC subscription | home, pdp |
| **Feed.** (feed.co) | Hero promesse claire, parcours quiz-to-purchase, copy bénéfices | home, quiz_vsl, pdp |

### E-commerce DTC Fashion (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Sézane** (sezane.com) | Luxe accessible, brand story exceptionnelle, UX collection benchmark | home, pdp, collection |
| **Asphalte** (asphalte.com) | Transparence radicale, precommande, copy anti-bullshit, pricing justifié | home, pdp, pricing |

### SaaS B2B (3)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Linear** (linear.app) | Hero 5 mots parfait, UX design benchmark SaaS, pricing transparent | home, pricing |
| **Notion** (notion.so) | Versatilité messaging, social proof enterprise, landing pages par persona | home, pricing, landing_paid |
| **Vercel** (vercel.com) | Hero technique mais clair, performance obsession, developer audience | home, pricing, blog |

### SaaS B2C (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Duolingo** (duolingo.com) | Gamification UX, hero simple, onboarding benchmark, social proof massive | home, pricing |
| **Canva** (canva.com) | Hero "design for everyone", freemium pricing, LP par use case | home, pricing, landing_paid |

### Fintech (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Qonto** (qonto.com) | Hero B2B clair, social proof chiffrée, pricing transparent, LP par segment | home, pricing, landing_paid |
| **Wise** (wise.com) | Transparence tarifaire radicale, hero calculateur interactif, confiance | home, pricing |

### Luxury / Premium (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Aesop** (aesop.com) | Minimalisme radical, brand consistency parfaite, PDP exemplaire | home, pdp, collection |
| **Le Labo** (lelabofragrances.com) | Storytelling artisanal, hero atmosphérique, expérience premium | home, pdp |

### Marketplace (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Airbnb** (airbnb.com) | UX recherche benchmark, social proof intégrée, hero adaptatif | home, pdp |
| **Vinted** (vinted.com) | Hero simple, UX mobile-first, gamification, collection dynamique | home, collection |

### Subscription / Box (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **HelloFresh** (hellofresh.com) | Hero promesse + prix, social proof chiffrée, quiz, LP paid exemplaire | home, quiz_vsl, landing_paid |
| **Dollar Shave Club** (dollarshaveclub.com) | Copy iconique, hero humoristique, storytelling brand | home, pdp |

### App Mobile (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Headspace** (headspace.com) | Hero émotionnel, design apaisant, social proof médiatique | home, pricing |
| **Whoop** (whoop.com) | Hero data-driven, social proof athlètes, design premium-tech | home, pdp, pricing |

### Formation / Infoproduit (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **MasterClass** (masterclass.com) | Hero visuel iconique, social proof célébrités, pricing value | home, pdp, pricing |
| **Coursera** (coursera.org) | Hero éducatif, social proof universitaire, collection cours | home, collection, pricing |

### Lead Gen / Services (2)
| Site | Pourquoi | Pages à capturer |
|---|---|---|
| **Pretto** (pretto.fr) | H1 "Le courtier qui défend vos intérêts" — cas d'école faux négatif actuel | home, landing_paid |
| **Alan** (alan.com) | Hero santé B2B clair, social proof entreprises, pricing transparent | home, pricing |

## 4. RÉCAPITULATIF

- **28 sites** couvrant **10 business types** et **8 page types**
- **~82 pages** à capturer au total
- **Estimation coût capture** : ~$0.03/page (ghost_capture) = ~$2.50
- **Estimation coût scoring sémantique** : ~$0.003/page × 20 critères = ~$5 total
- **Budget total golden dataset** : ~$8

## 5. UTILISATION DU GOLDEN DATASET

### Phase 1 : Capture (après semantic scorer)
- Ghost capture des 28 sites × 2-4 pages
- Stocker dans `data/golden/<site>/<pageType>/`

### Phase 2 : Scoring de référence
- Semantic scorer sur toutes les pages golden
- Annotation manuelle Mathis : override si le score Haiku est faux
- Constitue le "ground truth"

### Phase 3 : Calibration
- Comparer scores golden vs scores clients
- Ajuster les prompts si les golden scorent mal
- Identifier les critères encore problématiques

### Phase 4 : Enrichissement continu
- Ajouter des sites au golden dataset quand on en découvre d'excellents
- Les patterns des golden alimentent les recos (benchmarks)
- `learning_log.json` stocke les corrections

## 6. STRUCTURE DE DONNÉES

```
data/golden/
├── _golden_registry.json       # Liste des sites + métadonnées + scores de référence
├── glossier/
│   ├── home/
│   │   ├── capture.json
│   │   ├── score_semantic.json
│   │   └── golden_annotations.json  # Scores de référence validés humainement
│   ├── pdp/
│   └── collection/
├── linear/
│   ├── home/
│   └── pricing/
└── ...
```

## 7. GOLDEN ANNOTATIONS SCHEMA

```json
{
  "site": "glossier",
  "page_type": "home",
  "annotated_by": "mathis",
  "annotated_at": "2026-04-...",
  "reference_scores": {
    "hero_01": {"score": 3.0, "note": "H1 exemplaire : bénéfice + cible + différenciateur"},
    "hero_02": {"score": 3.0, "note": "Sous-titre complète parfaitement le H1"},
    // ...
  },
  "patterns_extracted": [
    {"pillar": "Hero", "pattern": "Hero minimaliste avec 1 produit hero + H1 bénéfice pur", "reusable": true}
  ]
}
```
