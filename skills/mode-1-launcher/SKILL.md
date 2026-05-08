---
name: mode-1-launcher
description: "FROZEN / DEPRECATED. Ne pas déclencher comme skill public. Utiliser `skills/gsg/SKILL.md` et `moteur_gsg.orchestrator.generate_lp()` pour tout GSG canonique. Ce fichier reste uniquement comme trace V26.AA historique du workflow Mode 1."
---

# FROZEN — Mode 1 Launcher V26.AA

> **Statut V27 canonical** : skill public déprécié. Le seul skill actif GSG est `skills/gsg/SKILL.md`. Ce fichier reste en lecture historique pour expliquer le Mode 1 V26.AA, mais ne doit plus être invoqué comme entrypoint.

---

## A. RÔLE

Tu es l'**orchestrateur opérationnel** du Mode 1 COMPLETE GSG V26.AA. Tu prends une demande utilisateur ("génère une LP listicle pour Japhy"), tu vérifies les prérequis, tu lances la génération, tu publies l'output.

## B. PRÉREQUIS À VÉRIFIER (Phase 0 qualification)

Avant tout lancement Mode 1 :

### Q1. Client identifié + en base
```bash
grep "<slug>" data/clients_database.json
ls data/captures/<slug>/  # doit exister
```
Si absent → invoquer `client-context-manager-v26-aa` Mode 1 Quick Create d'abord.

### Q2. Brand DNA disponible (NON négociable)
```bash
ls data/captures/<slug>/brand_dna.json
```
Si absent → lancer `brand_dna_extractor.py` :
```bash
python3 skills/site-capture/scripts/brand_dna_extractor.py <url> --client <slug>
```

### Q3. Page type valide
Page types supportés (cf `playbook/page_type_criteria.json`) :
- `home`, `pdp`, `collection`, `lp_sales`, `lp_leadgen`, `lp_listicle` (alias `listicle`)
- `pricing`, `quiz_vsl`, `vsl`, `challenge`, `bundle_standalone`, `squeeze`, `webinar`
- `advertorial`, `comparison`, `signup`, `blog`, `thank_you_page`

### Q4. Brief client (3 questions courtes)
Si l'utilisateur n'a pas fourni :
```
- Objectif business : [convertir trial / capturer lead / vendre produit / ...]
- Audience cible : [décrire persona en 1-2 phrases]
- Angle / hook éditorial : [signature visuelle souhaitée, ton, framework copy]
```

## C. WORKFLOW STANDARD (5 étapes)

### Étape 1 — Lancer Mode 1
```python
from moteur_gsg.orchestrator import generate_lp

result = generate_lp(
    mode="complete",
    client="<slug>",
    page_type="<type>",
    brief={
        "objectif": "...",
        "audience": "...",
        "angle": "...",
    },
    n_critical=7,                            # top N critères doctrine injectés
    apply_fixes=True,                         # fix_html_runtime auto
    save_html_path=f"deliverables/<slug>-<type>-MODE1-V26AA.html",
    save_audit_path=f"data/_audit_<slug>_mode1.json",
    verbose=True,
)
```

### Étape 2 — Inspecter le résultat
```python
audit = result["audit"]
print(f"Final: {audit['final']['final_score_pct']}%")
print(f"Doctrine: {audit['final']['breakdown']['doctrine_pct']}%")
print(f"Humanlike: {audit['final']['breakdown']['humanlike_pct']}%")
print(f"Signature: {audit['humanlike'].get('signature_nommable')}")
```

### Étape 3 — Vérifier killer rules
```python
if audit['final']['killer_rules_violated']:
    print("⛔ Killer violations:")
    for v in audit['final']['killer_violations']:
        print(f"  - {v['id']}: {v['label']}")
    # → décider : itérer ou accepter ?
```

### Étape 4 — Décision livraison
| Final score | Action |
|---|---|
| ≥85% Exceptionnel | Livrer direct + ajouter aux références internes |
| 75-84% Excellent | Livrer + commentaire sur les points faibles |
| 65-74% Bon | Livrer + proposer Mode 2 REPLACE pour itérer |
| <65% Insuffisant | Ne pas livrer, lancer Mode 1 best_of_n (3 routes parallel) |

### Étape 5 — Publier (optionnel)
Si Mathis valide la qualité visuelle :
- Invoquer `webapp-publisher` Action 3 pour ajouter au registre LPs
- Ajouter aux benchmarks internes si meilleur que best run actuel (80.5% Weglot)

## D. OPTIONS AVANCÉES

### D1. Best-of-N (3 routes parallèles)
Si single_pass < 70%, lancer best_of_n :
```python
result = generate_lp(
    mode="complete",
    client="<slug>",
    page_type="<type>",
    brief={...},
    pipeline="best_of_n",                    # SPRINT C — pas encore implémenté
    creative_routes=["safe", "premium", "bold"],
)
# Coût : ~$1.50, wall ~6min, retourne le meilleur des 3
```

### D2. Skip judges (debug only)
```python
result = generate_lp(
    mode="complete", client="<slug>", page_type="<type>", brief={...},
    skip_judges=True,                         # juste génération, pas de multi-judge
)
```

### D3. Variations de prompt
```python
result = generate_lp(
    mode="complete", client="<slug>", page_type="<type>", brief={...},
    n_critical=10,                            # plus de critères doctrine (au lieu de 7)
)
```

## E. BEST RUN DE RÉFÉRENCE (à battre)

**Mode 1 V26.AA Weglot listicle** (Sprint 3, 2026-05-03) :
| Métrique | Valeur |
|---|---|
| Final score | 80.5% Excellent |
| Doctrine V3.2.1 | 81.2% |
| Humanlike | 78.8% |
| Coût | $0.44 |
| Wall | 4min |
| Signature | « Editorial SaaS Research-Driven » |
| HTML | `deliverables/weglot-listicle-MODE1-V26AA.html` |

**Bat tous benchmarks** :
- V26.Z BESTOF Premium (4 stages) : 70% / $1.50 / 25min
- gsg_minimal v2 (1 prompt + doctrine injectée) : 76.2% / $0.04 / <1min
- gsg_minimal v1 (1 prompt + renoncement) : 65% / $0.02 / <1min
- ChatGPT GlobalFlow (1 prompt manuel) : 66% / manuel
- Collègue humain : 67/80 (~83.75% humanlike)

## F. ANTI-PATTERNS À ÉVITER

1. **Mega-prompt sursaturé > 15K chars** → Sonnet coche les cases au lieu de créer. Le hard limit est ≤10K chars (cf `prompt_assembly.estimate_prompt_size()`)
2. **Re-inventer une grille de jugement** → tous les juges consomment `scripts/doctrine.py` racine
3. **Industrialiser sur 56 clients en batch** → Mathis explicite : qualité unitaire absolue
4. **Bypasser les killer rules** → si killer CRITICAL, score capé. Pas de bypass.
5. **Lancer sans brand_dna** → erreur explicite. Sauf si Mode 5 GENESIS (brief seul, pas de brand existante)

## G. INTÉGRATION ÉCOSYSTÈME

```
ENTRÉE
  - Demande user "génère une LP X pour client Y"
  - OU brief automatique depuis audit-bridge-to-gsg

PRÉREQUIS (Phase 0)
  - Vérifier client-context-manager-v26-aa : brand_dna OK ?
  - Si non : lancer brand_dna_extractor

EXÉCUTION (Mode 1)
  - moteur_gsg/orchestrator.py generate_lp(mode="complete", ...)
  - moteur_gsg/modes/mode_1_complete.py orchestre les 5 étapes
  - moteur_gsg/core/{brand_intelligence, prompt_assembly, pipeline_single_pass}
  - moteur_multi_judge/orchestrator.py multi_judge final

OUTPUT
  - deliverables/<slug>-<type>-MODE1-V26AA.html
  - data/_audit_<slug>_mode1.json

PUBLICATION (optionnelle)
  - webapp-publisher Action 3 si validation qualité OK
```

## H. À FAIRE (gaps Mode 1 Launcher V26.AA)

- [ ] **Best-of-N pour Mode 1** : actuellement single_pass uniquement. Sprint C.
- [ ] **Mode 1 batch sur N clients** : Mathis ne veut pas industrialisation, garder unitaire.
- [ ] **Auto-iteration si <65%** : actuellement manuel. Sprint C.
- [ ] **Webapp UI launcher** : actuellement CLI. Sprint D webapp v2.

## I. NE PAS CONFONDRE

- **`mode-1-launcher`** (ce skill) = workflow Mode 1 COMPLETE
- **`gsg-v26-aa`** = description architecture des 5 modes
- **Modes 2-3-4-5** : chacun aura son skill launcher Sprint C
- **`audit-bridge-to-gsg`** = bridge audit→Mode 2 REPLACE (input du launcher)

## J. LECTURE OBLIGATOIRE À CHAQUE DÉMARRAGE

1. Ce SKILL.md
2. `moteur_gsg/orchestrator.py` (API publique)
3. `moteur_gsg/modes/mode_1_complete.py` (pipeline 5 étapes)
4. `moteur_gsg/core/prompt_assembly.py` (limite ≤10K chars)
5. `data/_audit_weglot_mode1_v26aa.json` (audit de référence)
