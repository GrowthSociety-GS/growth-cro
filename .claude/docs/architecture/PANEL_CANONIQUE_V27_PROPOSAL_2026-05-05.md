# Panel Canonique V27 — Proposition À Valider

> Date : 2026-05-05
> Status : proposition produit matérialisée en JSON et branchée dans la webapp, pas encore business-lockée.
> Runtime webapp actuel : `data/curated_clients_v27.json` (56 clients), dérivé de `data/curated_clients_v26.json`.

## 0. Pourquoi Ce Document Existe

Mathis a challengé `captain_contrat` : "c'était pas dans nos clients ?"

Réponse disque : oui, `captain_contrat` est dans le panel runtime V26.
Réponse produit : il ne faut pas le considérer comme client business validé sans décision explicite.

Ce document propose donc une couche de rôles au-dessus du panel V26. Cette couche existe maintenant dans `data/curated_clients_v27.json`.

## 1. Rôles Proposés

| Rôle | Définition |
|---|---|
| `business_client` | Client Growth Society réel à suivre comme compte agence |
| `business_client_candidate` | Probablement client réel, mais à valider |
| `golden_reference` | Site référence avant-garde / benchmark premium |
| `benchmark` | Site benchmark utile, pas client GS |
| `mathis_pick` | Choix explicite Mathis historique |
| `diversity_supplement` | Ajout pour couvrir un vertical/intent manquant |
| `review` | Incertain, ne pas utiliser pour décisions business |

## 2. Décisions À Prendre

| Décision | Pourquoi |
|---|---|
| Garder ou retirer `captain_contrat` | Actuellement supplement lead gen, pas client business confirmé |
| Séparer goldens du panel client | Evite de mélanger benchmark et vérité agence |
| Valider les `business_client_candidate` | Nécessaire avant Reality/Webapp cible |
| Décider si `benchmark` reste dans la webapp observatoire | Utile pour comparaison, dangereux si affiché comme client |
| Valider `data/curated_clients_v27.json` | Nouveau contrat propre avec `panel_role`, déjà branché runtime mais pas business-locké |

## 3. Proposition De Classification

| Client | Type | Pages | Rôle proposé | Statut | Décision Mathis |
|---|---|---|---|---|---|
| `aesop` | ecommerce | pdp | benchmark | review | |
| `airbnb` | app | collection,home,signup | benchmark | review | |
| `alan_golden` | insurtech | home,lp_sales,signup | golden_reference | keep | |
| `andthegreen` | ecommerce | collection,home,lp_sales,pdp,quiz_vsl | business_client_candidate | review | |
| `asphalte_golden` | ecommerce | collection,home,pdp | golden_reference | keep | |
| `back_market` | ecommerce | home | mathis_pick | keep | |
| `canva` | saas | home,pricing,signup | benchmark | review | |
| `captain_contrat` | lead_gen | home,lp_leadgen,signup | diversity_supplement | review | |
| `coursera` | saas | home,lp_leadgen,lp_sales,pdp,pricing | benchmark | review | |
| `cuure` | ecommerce | collection,home,pdp,quiz_vsl | mathis_pick | keep | |
| `detective_box` | ecommerce | collection,home,lp_sales,pdp | mathis_pick | keep | |
| `doctolib` | lead_gen | home,lp_leadgen,quiz_vsl,signup | mathis_pick | keep | |
| `dollar_shave_club` | ecommerce | collection,home,pdp | benchmark | review | |
| `drunk_elephant` | ecommerce | collection,home | benchmark | review | |
| `duolingo` | app | home,pricing | benchmark | review | |
| `edone_paris` | ecommerce | collection,home,pdp | benchmark | review | |
| `emma_matelas` | ecommerce | collection,home,pdp | benchmark | review | |
| `epycure` | ecommerce | collection,home,quiz_vsl | mathis_pick | keep | |
| `furifuri` | unknown | collection,home,pdp | business_client_candidate | review | |
| `fygr` | saas | home,lp_leadgen,lp_sales,pricing,signup | benchmark | review | |
| `gymshark` | ecommerce | collection,home | benchmark | review | |
| `headspace` | app | home,lp_leadgen,lp_sales,pdp,pricing | benchmark | review | |
| `hellofresh` | ecommerce | home,lp_leadgen | benchmark | review | |
| `japhy` | ecommerce | collection,home,lp_leadgen,lp_sales,quiz_vsl | business_client_candidate | review | |
| `kaiju` | ecommerce | home,pdp | business_client_candidate | review | |
| `la-marque-en-moins` | unknown | collection,home,pdp | business_client_candidate | review | |
| `le_labo` | ecommerce | collection,home,pdp | benchmark | review | |
| `linear_golden` | saas | home,lp_leadgen,pricing,signup | golden_reference | keep | |
| `maison_martin` | ecommerce | collection,home,pdp,signup | business_client_candidate | review | |
| `masterclass` | saas | quiz_vsl | benchmark | review | |
| `matera` | saas | collection,home,lp_leadgen,lp_sales,quiz_vsl | benchmark | review | |
| `may` | unknown | home,lp_leadgen | business_client_candidate | review | |
| `monday` | saas | home,lp_leadgen,pricing | benchmark | review | |
| `myvariations` | ecommerce | collection,home,pdp | mathis_pick | keep | |
| `nobo` | lead_gen | home,lp_leadgen | benchmark | review | |
| `notion` | saas | home,lp_leadgen,lp_sales,quiz_vsl | benchmark | review | |
| `oma` | unknown | collection,home,lp_leadgen,pdp,quiz_vsl | business_client_candidate | review | |
| `pennylane` | saas | home,lp_leadgen,lp_sales,pricing | diversity_supplement | review | |
| `petit_bambou` | app | home,lp_leadgen,lp_sales,pricing,signup | diversity_supplement | review | |
| `poppins_mila_learn` | app | home,lp_leadgen,lp_sales,pricing,quiz_vsl | diversity_supplement | review | |
| `pretto` | lead_gen | home,lp_leadgen,lp_sales,quiz_vsl | benchmark | review | |
| `qonto` | fintech | home,lp_leadgen,lp_sales,pricing,quiz_vsl | benchmark | review | |
| `respire` | ecommerce | collection,home,pdp | mathis_pick | keep | |
| `reverso` | saas | pricing | benchmark | review | |
| `revolut` | fintech | home,lp_sales,pricing | benchmark | review | |
| `seazon` | ecommerce | home,lp_sales,pdp | business_client_candidate | review | |
| `selectra` | lead_gen | home,lp_leadgen,lp_sales | diversity_supplement | review | |
| `steamone` | unknown | home | business_client_candidate | review | |
| `stripe` | saas | home,lp_leadgen,pricing | benchmark | review | |
| `typology` | ecommerce | collection,home,pdp,quiz_vsl | benchmark | review | |
| `vercel` | saas | home,lp_leadgen,pdp,pricing,signup | benchmark | review | |
| `vinted` | ecommerce | collection,home,signup | benchmark | review | |
| `voggt` | app | collection,home,pdp | benchmark | review | |
| `weglot` | saas | home,lp_leadgen,pricing | benchmark | review | |
| `whoop` | ecommerce | home,lp_leadgen,lp_sales,signup | benchmark | review | |
| `wise` | saas | collection,home,lp_leadgen,pricing,signup | benchmark | review | |

## 4. Points À Réconcilier

Le manifest historique mentionne :

- 29 goldens identifiés via `_golden_registry.json`
- 18 actifs réels
- 9 extras Mathis
- 5 supplements diversité
- panel final 57 clients (+5 active à onboarder = 62)

Le runtime actuel contient :

- 56 clients
- seulement 3 IDs explicitement suffixés `_golden`
- 5 unknown business type
- plusieurs benchmarks célèbres mélangés aux clients

Conclusion : le runtime V26 est utilisable techniquement, mais pas assez propre sémantiquement pour la webapp cible.

## 5. Transformation Réalisée

Créé :

```text
data/curated_clients_v27.json
```

Le bloc `fleet` V27 reflète le build webapp actuel : 56 clients, 185 pages, 3045 recos LP-level. Les compteurs V26 historiques restent dans `meta.created_from_declared_fleet`.

Contrat minimal :

```json
{
  "id": "japhy",
  "display_name": "Japhy",
  "business_type": "ecommerce",
  "panel_role": "business_client_candidate",
  "status": "review",
  "page_types": ["collection", "home", "lp_leadgen", "lp_sales", "quiz_vsl"],
  "reason_in_panel": "candidate business client from V26 runtime panel",
  "source": "curated_clients_v26"
}
```

Adapté :

- `skills/site-capture/scripts/build_growth_audit_data.py`
- `deliverables/GrowthCRO-V26-WebApp.html`

Reste à adapter après validation business :

- reports
- Reality pilot selection
- Learning segmentation

## 6. Verdict

Ne plus dire "56 clients officiels" sans préciser :

```text
56 clients du panel runtime V26
```

La formule propre jusqu'à validation :

```text
panel runtime V27 rôlé : 56 entrées auditées
panel business Growth Society : à verrouiller
goldens / benchmarks : à séparer
```
