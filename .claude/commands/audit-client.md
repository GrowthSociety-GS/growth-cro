---
description: Audit CRO complet d'un client (capture → scoring → recos → dashboard update)
argument-hint: <client-slug>
---

Objectif : produire un audit complet du client `$1` en passant par toutes les étapes du pipeline GrowthCRO.

Étapes à exécuter dans l'ordre :

1. Vérifier que `$1` est dans `data/clients_database.json`. Sinon, stop net et demande à Mathis s'il faut ajouter le client via `python3 add_client.py --slug $1 --brand "..." --url "..."`.
2. Déléguer à l'agent `capture-worker` : "capture toutes les pages de $1".
3. Déléguer à l'agent `scorer` : "score toutes les pages capturées de $1".
4. Déléguer à l'agent `reco-enricher` : "génère les recos pour $1".
5. Rebuild dashboard : `python3 skills/site-capture/scripts/build_dashboard_v17.py --client $1 --update` puis `python3 skills/site-capture/scripts/enrich_dashboard_v17.py`.
6. Vérifier que le dashboard rend bien : `node deliverables/verify_dashboard_v17_2.js` (smoke test).
7. Rapport final à Mathis avec : nombre de pages, scores moyens par pilier, top 5 recos P0, coût API estimé.

Règle : **ne commit rien sans que Mathis valide le rapport**.
