---
name: cro-library-v26-aa
description: "CRO Library V26.AA : Pattern Library auto-alimentée depuis les 56 clients curatés V26 + outputs Mode 1-5 V26.AA. Déclencher dès que l'utilisateur mentionne : ajouter un template, chercher un template, ajouter un pattern, chercher un pattern, ajouter une référence LP, chercher une référence, teardown, audit concurrent, bibliothèque CRO, library, templates validés, patterns réutilisables. Hub centralisé : Templates (LPs Mode 1-5 score ≥80%), Patterns (composants extraits audits), Références LP (29 sites golden_dataset), Teardowns (analyses concurrentielles). Auto-add depuis cycle apprenant V29 (data/learning/audit_based_proposals/ — 69 proposals générés sur 56 curés)."
---

# CRO Library V26.AA — Pattern Library auto-alimentée

> **PROMU** depuis `_roadmap_v27/` vers actif Sprint C V26.AA (2026-05-04).
> **MAJ** : SKILL.md original (avril 16) décrivait /153 et auto-add depuis GSG hypothétique.
> **V26.AA réel** : auto-add depuis Mode 1-5 V26.AA (multi_judge ≥80%) + cycle apprenant V29.

---

## A. RÔLE

Tu es le **CRO librarian + knowledge engineer** de l'écosystème V26.AA. Tu :
1. Catalogues les LPs Mode 1-5 V26.AA qui scorent ≥80% (Excellent) → **Template Library**
2. Extrais les patterns récurrents des audits 56 curatés → **Pattern Library**
3. Maintiens les 29 sites golden comme **Références LP** (data/golden/)
4. Stockes les teardowns concurrentiels → **Teardowns**
5. Alimentes le **cycle apprenant V29** (`data/learning/audit_based_proposals/`)

## B. ARTEFACTS V26.AA RÉELS

| Sous-module | Source de vérité | État |
|---|---|---|
| Template Library | `deliverables/*-MODE<N>-V26AA.html` (LPs Mode 1-5) + manifest registry | À CRÉER : `data/cro_library/templates_registry.json` |
| Pattern Library | `data/learning/audit_based_stats.json` (329 segments criterion×business) | ACTIF (Sprint B V26.AA) |
| Références LP | `data/golden/` (29 sites bench) + `data/golden/_golden_registry.json` | ACTIF |
| Teardowns | (à créer) — outputs audit competitor | TODO Sprint C+ |

## C. AUTO-ADD V26.AA (cycle apprenant activé Sprint B)

### Trigger 1 — Mode 1-5 LP ≥80% Excellent
```
moteur_gsg.orchestrator.generate_lp() RESULT
├── audit.final.final_score_pct ≥ 80
└── audit.humanlike.signature_nommable not None
    ↓
CRO Library AUTO-CREATE template entry
├── id: tpl_<client>_<page_type>_mode<N>_<date>
├── score: from multi_judge
├── signature: from humanlike
├── HTML: deliverables/<file>
└── Update data/cro_library/templates_registry.json
```

### Trigger 2 — learning_layer V29 doctrine_proposals
```
data/learning/audit_based_proposals/*.json
├── 69 proposals générés (Sprint B V26.AA)
├── 37 calibrate_threshold (règles trop strictes)
└── 32 tighten_threshold (règles sous-discriminantes)
    ↓
CRO Library Pattern Library
├── Mark patterns as "validated" si proposal merge dans doctrine V3.3
└── Update data/cro_library/patterns_validated.json
```

## D. COMMANDES CLI (V26.AA)

```bash
# Run cycle apprenant (généré 69 proposals sur 56 curés)
python3 skills/site-capture/scripts/learning_layer_v29_audit_based.py

# Voir summary patterns
cat data/learning/audit_based_summary.md

# Lister proposals par type
ls data/learning/audit_based_proposals/ | head -20
```

## E. POSITIONNEMENT VS VISION ORIGINALE (avril 16)

Le SKILL.md original (40K) décrivait un hub avec auto-add depuis GSG hypothétique
score /153, schémas data détaillés, recherche sémantique. **Réalité V26.AA** :
- Pattern Library = data/learning/ (généré V29 audit-based)
- Templates = LPs Mode 1-5 V26.AA dans deliverables/
- Références LP = data/golden/ (29 sites bench)
- Teardowns = pas encore créés (TODO)

→ La VISION était bonne, l'IMPLÉMENTATION est différente (distribuée vs hub centralisé).

## F. PROMOTION DEPUIS _roadmap_v27/ (Sprint C V26.AA)

Pourquoi promu maintenant ? Sprint B V26.AA a activé `learning_layer_v29_audit_based.py`
qui génère vraiment les patterns/proposals depuis les 56 curatés. Le concept "library
auto-alimentée" est désormais opérationnel (même si distribué).

## G. À FAIRE Sprint C+ (full library V26.AA)

- [ ] `data/cro_library/templates_registry.json` (auto-add depuis Mode 1-5 ≥80%)
- [ ] `data/cro_library/patterns_validated.json` (depuis doctrine_proposals merged)
- [ ] Teardowns auto-build depuis audits competitor (nouveau pipeline)
- [ ] Recherche sémantique (pgvector, V27)

## H. NE PAS CONFONDRE

- **`cro-library-v26-aa`** (ce skill, promu) = Pattern Library V26.AA (réelle)
- **`growth-audit-v26-aa`** = audit qui produit les inputs de la library
- **`gsg-v26-aa`** = génération qui produit les Templates
- **`learning_layer_v29_audit_based.py`** = générateur de patterns/proposals
