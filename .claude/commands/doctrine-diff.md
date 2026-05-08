---
description: Compare deux versions d'un playbook doctrine (bloc_N) et chiffre l'impact
argument-hint: <bloc-name> <old-version> <new-version>
---

Objectif : diffing propre d'un playbook entre deux versions, avec estimation d'impact sur les scores déjà produits.

1. Read `playbook/_archive/bloc_$1_v$2.json` (ou cherche la version dans git log si disponible).
2. Read `playbook/bloc_$1_v3.json` courant (ou `v$3` si fourni).
3. Diff critère par critère : lequel a changé de barème ? Lequel a un nouveau scale ? Lequel a été ajouté/supprimé ?
4. Pour chaque critère modifié, compter combien de pages existantes ont un score sur ce critère (via `grep -r "{criterion_id}" data/captures/*/*/score_*.json`).
5. Estimer le coût de re-scoring : `nb_pages_affected * $0.01 Haiku` ou `$0.05 Sonnet` selon le pilier.
6. Rapport avec recommandation : re-scorer ou pas ?
