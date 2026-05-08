# SCHEMA/ — JSON Schemas GrowthCRO

Chaque schéma valide un fichier produit par le pipeline. Source de vérité quand un script modifie la data : il doit re-matcher le schéma.

## Fichiers

| Schema | Cible | Producer |
|---|---|---|
| `score_pillar.schema.json` | `data/captures/{slug}/{pageType}/score_{hero,persuasion,ux,coherence,psycho,tech}.json` | `batch_rescore.py` |
| `score_page_type.schema.json` | `data/captures/{slug}/{pageType}/score_page_type.json` | `score_page_type.py` |
| `perception_v13.schema.json` | `data/captures/{slug}/{pageType}/perception_v13.json` | `perception_v13.py` |
| `recos_enriched.schema.json` | `data/captures/{slug}/{pageType}/recos_enriched.json` | `reco_enricher_v13_api.py` |
| `bloc_v3.schema.json` | `playbook/bloc_*_v3.json` | Édition manuelle via agent `doctrine-keeper` |
| `clients_database.schema.json` | `data/clients_database.json` | `add_client.py` |
| `dashboard_v17_data.schema.json` | `deliverables/growthcro_data_v17.json` | `build_dashboard_v17.py` + `enrich_dashboard_v17.py` |

## Validation

```bash
pip install jsonschema   # dev dep optionnelle
python3 SCHEMA/validate.py data/captures/japhy/home/score_hero.json SCHEMA/score_pillar.schema.json
```

Ou tout d'un coup :

```bash
python3 SCHEMA/validate_all.py
```
