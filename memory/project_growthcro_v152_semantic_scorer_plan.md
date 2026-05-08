# Semantic Scorer V15.2 — Spec Technique Complète

**Date** : 2026-04-17
**Priorité** : #1 du plan V15.2
**Impact estimé** : résout 70% des problèmes de scoring
**Coût** : ~$0.50 pour batch complet (196 pages × 20 critères)
**Validé par Mathis** : OUI (séquence B — scorer d'abord, golden dataset ensuite)

---

## 1. PROBLÈME

Les 6 scorers actuels (score_hero.py, score_persuasion.py, etc.) utilisent des détecteurs regex/compteurs de mots-clés pour évaluer des critères qui demandent de la compréhension sémantique. Résultat :
- 88% faux négatifs sur hero_01 (H1 promesse)
- 84% faux négatifs sur coh_01 (promesse claire)
- 83% faux négatifs sur hero_04 (visuel pertinent)
- 77% faux négatifs sur coh_02 (persona détectable)
- 65% faux négatifs sur per_02 (storytelling)

Exemples : "Le courtier immobilier qui défend vos intérêts" (Pretto) → score 0/3 car "défend vos intérêts" ne match pas les keywords hardcodés (gagner, transformer, améliorer...).

## 2. SOLUTION : SEMANTIC SCORING LAYER

Script `semantic_scorer.py` qui :
1. Lit `capture.json` + `clients_database.json` pour chaque page
2. Identifie les ~20 critères sémantiques
3. Construit un prompt par critère avec TOUT le contexte nécessaire
4. Appelle Haiku API en batch
5. Parse les réponses → JSON structuré
6. Merge avec scores factuels → score final

## 3. CRITÈRES SÉMANTIQUES (18-20 critères)

### Bloc 1 — Hero (5 critères sémantiques sur 6)
| ID | Label | Contexte nécessaire |
|---|---|---|
| hero_01 | H1 = bonne promesse ? | H1 + sous-titre + page_type + business_type |
| hero_02 | Sous-titre complémente H1 ? | H1 + sous-titre + CTA |
| hero_04 | Visuel hero pertinent ? | Description images + alt texts + page_type + business |
| hero_05 | Preuve sociale crédible ATF ? | Social proof elements + business category |
| hero_06 | Test 5 secondes global | H1 + sous-titre + CTA + visuels + social proof ENSEMBLE |

### Bloc 2 — Persuasion (4 critères sémantiques sur 8)
| ID | Label | Contexte nécessaire |
|---|---|---|
| per_01 | Bénéfices > features ? | Tous les textes body, titres de section |
| per_02 | Storytelling présent ? | Structure narrative page, sections détectées |
| per_03 | Objections levées ? | FAQ + sections rassurance + business_type |
| per_07 | Ton cohérent avec la marque ? | Sample textes + business_type + brand positioning |
| per_08 | Anti-jargon DTC template ? | Sample textes, blacklist patterns |

### Bloc 4 — Cohérence (4 critères sémantiques)
| ID | Label | Contexte nécessaire |
|---|---|---|
| coh_01 | Promesse claire et visible ? | H1 + sous-titre + 1ère section |
| coh_02 | Persona détectable ? | Ensemble page : textes, visuels, ton |
| coh_03 | Scent trail ads → page ? | Meta title + H1 + CTA (proxy — pas d'ads réelles) |
| coh_05 | Voice & Tone cohérent ? | Échantillon 3-5 sections de texte |

### Bloc 5 — Psycho (4 critères sémantiques)
| ID | Label | Contexte nécessaire |
|---|---|---|
| psy_01 | Urgence crédible ? | Éléments urgence détectés + business_type |
| psy_02 | Rareté crédible ? | Éléments rareté + business_type + proof_type |
| psy_05 | Autorité fondateur ? | Section about/fondateur + bio + photo |
| psy_08 | Témoignages authentiques ? | Testimonials détectés + Baymard markers |

### CRITÈRES QUI RESTENT FACTUELS (code actuel OK)
hero_03 (CTA visible ATF — bbox mesurable), tech_01→05, ux_01→08, per_04 (preuves comptables), per_05 (Trustpilot — détection widget), per_06 (FAQ présence)

## 4. ARCHITECTURE DU SCRIPT

```python
# semantic_scorer.py — Architecture cible
#
# Input:
#   - data/captures/<client>/<pageType>/capture.json
#   - data/clients_database.json (business_type, category)
#   - playbook/bloc_*_v3.json (critères + scoring rules)
#
# Output:
#   - data/captures/<client>/<pageType>/score_semantic.json
#
# Modes:
#   --client <label> --page <pageType>    # Single page
#   --all                                  # Batch 196 pages
#   --dry-run                              # Print prompts sans appeler l'API
#   --model haiku|sonnet                   # Default: haiku ($0.50 batch)

import json, os, sys, argparse, asyncio
from anthropic import AsyncAnthropic

# --- Config ---
SEMANTIC_CRITERIA = {
    "hero_01": {"label": "H1 promesse", "bloc": "hero", ...},
    "hero_02": {"label": "Sous-titre", "bloc": "hero", ...},
    # ... 18-20 critères
}

# --- Extraction contexte ---
def extract_hero_context(capture: dict) -> dict:
    """Extrait H1, sous-titre, CTA, visuels, social proof du hero cluster."""
    # Utilise perception_v13 pour localiser le cluster HERO
    # Extrait les éléments pertinents
    pass

def extract_persuasion_context(capture: dict) -> dict:
    """Extrait sections texte, FAQ, preuves, storytelling."""
    pass

def extract_coherence_context(capture: dict) -> dict:
    """Extrait promesse, persona signals, voice & tone samples."""
    pass

def extract_psycho_context(capture: dict) -> dict:
    """Extrait éléments urgence, rareté, fondateur, testimonials."""
    pass

# --- Prompt builder ---
def build_prompt(criterion_id: str, context: dict, page_type: str, business_type: str, business_category: str) -> str:
    """Construit le prompt pour un critère donné."""
    # Template par critère avec contexte complet
    # Scoring ternaire : TOP (3/3) / OK (1.5/3) / CRITIQUE (0/3)
    # Output structuré : score + verdict + rationale
    pass

# --- API caller ---
async def score_batch(prompts: list[dict], model: str = "claude-haiku-4-5-20251001") -> list[dict]:
    """Appelle Haiku en parallèle (max 10 concurrent)."""
    pass

# --- Merger ---
def merge_scores(semantic_scores: dict, existing_scores: dict) -> dict:
    """Fusionne scores sémantiques + factuels → score final."""
    # Les scores factuels existants sont conservés tels quels
    # Les scores sémantiques REMPLACENT les scores regex
    pass
```

## 5. PROMPT TEMPLATES PAR CRITÈRE

### hero_01 — H1 Promesse
```
Tu es un expert CRO senior. Voici le hero d'une page {page_type} pour {business_type} ({business_category}).

H1: "{h1_text}"
Sous-titre: "{subtitle_text}"
CTA principal: "{cta_text}"

Évalue le H1 selon ces critères précis :
- TOP (3/3): Le H1 contient au moins 2 des 3 éléments (bénéfice client, ciblage, différenciateur). Il est spécifique, mémorable, entre 6-15 mots. Exemples : "Le courtier immobilier qui défend vos intérêts", "L'alimentation experte qui change la vie de nos chiens et chats"
- OK (1.5/3): Le H1 est correct mais générique ou trop long. Un seul élément sur 3. Exemples : "Découvrez nos produits", "La solution pour votre business"
- CRITIQUE (0/3): H1 absent, incompréhensible, ou slogan vide sans information. Exemples : "Bienvenue", "Innovation. Passion. Excellence."

IMPORTANT: Évalue le H1 EN CONTEXTE avec le sous-titre. Si le H1 est un hook et le sous-titre apporte la précision, c'est acceptable.

Réponds EXACTEMENT dans ce format JSON :
{"score": X, "verdict": "top|ok|critical", "rationale": "...en français, 1-2 phrases pour un CMO..."}
```

### hero_06 — Test 5 Secondes
```
Tu es un expert CRO. Un visiteur arrive sur cette page {page_type} ({business_type}, {business_category}).

En 5 secondes, il voit :
- H1: "{h1_text}"
- Sous-titre: "{subtitle_text}"
- CTA: "{cta_text}"
- Visuels: {images_description}
- Preuve sociale: {social_proof_text}

Peut-il répondre aux 3 questions :
1. C'est QUOI ? (produit/service)
2. C'est pour QUI ?
3. Quelle ACTION faire ?

- TOP (3/3): Les 3 réponses sont évidentes en < 5 secondes
- OK (1.5/3): 2 sur 3 claires, ou les 3 mais pas immédiatement
- CRITIQUE (0/3): Aucune ou 1 seule question trouvée

{"score": X, "verdict": "top|ok|critical", "rationale": "..."}
```

### coh_01 — Promesse claire
```
Tu es un expert CRO. Page {page_type} pour {business_type} ({business_category}).

Zone ATF (above the fold) :
- H1: "{h1_text}"
- Sous-titre: "{subtitle_text}"
- 1ère section visible: "{first_section_text}"

La page porte-t-elle une PROMESSE claire (transformation promise au visiteur) ?

- TOP (3/3): Promesse spécifique, différenciante, visible en 3 secondes. Le visiteur sait exactement ce qu'il va obtenir.
- OK (1.5/3): Promesse présente mais vague ou enfouie.
- CRITIQUE (0/3): Aucune promesse identifiable. Page descriptive sans engagement.

{"score": X, "verdict": "top|ok|critical", "rationale": "..."}
```

## 6. OUTPUT FORMAT

```json
// score_semantic.json
{
  "meta": {
    "model": "claude-haiku-4-5-20251001",
    "timestamp": "2026-04-17T...",
    "version": "1.0.0",
    "cost_estimate_usd": 0.003,
    "criteria_evaluated": 18,
    "page_type": "home",
    "business_type": "ecommerce",
    "business_category": "dtc_petfood"
  },
  "scores": {
    "hero_01": {
      "score": 3.0,
      "verdict": "top",
      "rationale": "Le H1 contient les 3 éléments : bénéfice (change la vie), cible (chiens et chats), différenciateur (alimentation experte).",
      "method": "semantic_haiku",
      "replaces": "regex_detector"
    },
    "hero_02": { ... },
    // ...
  },
  "factual_preserved": ["hero_03", "tech_01", "tech_02", ...],
  "summary": {
    "semantic_criteria": 18,
    "factual_criteria": 29,
    "total_score_change": "+12.5",
    "biggest_corrections": [
      {"criterion": "hero_01", "old": 0, "new": 3, "delta": "+3"}
    ]
  }
}
```

## 7. INTÉGRATION DANS LE PIPELINE

Le semantic scorer s'insère APRÈS le scoring piliers existant (étape 5) et AVANT score_page_type (étape 6) :

```
étape 5: batch_rescore.py → score_hero.json, score_persuasion.json, etc. (regex, comme avant)
étape 5.5: semantic_scorer.py → score_semantic.json (Haiku, override les critères sémantiques)
étape 6: score_page_type.py → lit score_semantic.json EN PRIORITÉ sur les scores piliers
```

Pas de modification des scorers existants. Le semantic scorer est un OVERLAY qui remplace certains verdicts.

## 8. DÉPENDANCES

- `anthropic` Python SDK (déjà utilisé pour reco_enricher_v13_api.py)
- `ANTHROPIC_API_KEY` env var
- Haiku model : `claude-haiku-4-5-20251001`
- capture.json existant pour chaque page
- clients_database.json pour business context
- playbook/bloc_*_v3.json pour les critères

## 9. PLAN D'IMPLÉMENTATION

1. Écrire les extracteurs de contexte (lire capture.json → éléments par critère)
2. Écrire les prompt templates (18-20 critères)
3. Écrire le caller API async (batch avec throttle)
4. Écrire le merger (semantic + factuel → score final)
5. Tester sur 3 pages connues : Japhy (16.5/18 hero connu), Pretto (H1 faux négatif connu), OCNI
6. Batch run sur 196 pages (~$0.50)
7. Comparer avant/après : combien de scores changent, dans quel sens
8. Validation Mathis sur échantillon
