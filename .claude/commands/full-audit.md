---
description: Audit complet du projet (doctrine + code + data + dashboard)
---

Objectif : check de santé profond. À lancer avant gros changement ou après long silence.

Sections :

1. **Doctrine** : toutes les versions des playbooks sont-elles cohérentes ? (`grep version playbook/bloc_*_v3.json`). Les scripts `score_*.py` réfèrent-ils aux bonnes versions ?
2. **Pipeline state** : `/pipeline-status`.
3. **Orphans** : fichiers dans `data/captures/**/` qui n'ont pas de `score_page_type.json` (pages pas scorées). Fichiers `.bak*` oubliés.
4. **Dashboard** : `node deliverables/verify_dashboard_v17_2.js` + taille `deliverables/growthcro_data_v17.json` + comptage des clés.
5. **Git** : uncommitted files, branches divergentes.
6. **Secrets leaks** : `grep -rE "sk-ant-api[0-9]|apify_api_[A-Za-z0-9]+" --include="*.md" --include="*.json" .` (le grep devrait être vide).
7. **Cost estimate** : si on devait tout re-scorer depuis zéro, combien ça coûte ?

Livrable : rapport markdown concentré + prio des actions correctives.
