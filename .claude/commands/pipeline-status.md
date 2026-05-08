---
description: Dump l'état disque réel du pipeline (équivalent python3 state.py enrichi)
---

Objectif : donner à Mathis une photo instantanée de l'état du projet.

Étapes :

1. Run `python3 state.py` et capture la sortie.
2. Ajoute : taille totale `data/captures/` (du -sh), nombre de recos produites (`find data/captures -name "recos_enriched.json" | wc -l`), age du dernier scoring (`find data/captures -name "score_page_type.json" -printf "%T@ %p\n" | sort -nr | head -1`).
3. Ajoute : diff git si le repo est init (`git status --porcelain | wc -l` uncommitted files).
4. Ajoute : dernière entrée du changelog manifest (`grep -A 20 "^### 2026" GROWTHCRO_MANIFEST.md | tail -25`).
5. Présente sous forme tableau + petit résumé narratif de 3 lignes max.
