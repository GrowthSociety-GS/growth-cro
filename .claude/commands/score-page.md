---
description: Score une page spécifique d'un client (utile post-recapture)
argument-hint: <client-slug> <page-type>
---

Objectif : scorer la page `$1/$2` uniquement (pas toute la flotte).

Délégue à l'agent `scorer` avec l'argument ciblé. Rappel les pré-requis : la page doit avoir été capturée (existence de `data/captures/$1/$2/capture.json`).

Après le scoring, propose à Mathis :
- De générer les recos : `/score-page` ne fait pas les recos, c'est `/audit-client` ou l'agent `reco-enricher` direct.
- De comparer avec l'ancien scoring : `python3 scripts/compare_scores.py $1 $2 --before "2026-04-18" --after "now"` (si le script existe).
