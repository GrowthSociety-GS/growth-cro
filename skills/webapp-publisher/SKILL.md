---
name: webapp-publisher
description: "WebApp Publisher V26.AA : publication d'audits, recos et LPs générées dans la WebApp officielle GrowthCRO V26 (deliverables/GrowthCRO-V26-WebApp.html). Déclencher dès que l'utilisateur mentionne : publier l'audit, ajouter à la webapp, mettre à jour le dashboard, exporter dans growth_audit_data, ajouter ce client à la base curatée, rebuild webapp, refresh dashboard, livrer le rapport client, partager l'audit avec le client. Gère 4 actions : (1) ajouter un client aux 56 curatés, (2) publier un nouveau audit dans la fleet, (3) publier une LP générée dans deliverables/, (4) regénérer growth_audit_data.js complet."
---

# WebApp Publisher V26.AA — Publication des audits/LPs dans la WebApp PROD

> **NOUVEAU SKILL Sprint A V26.AA (2026-05-04)** : créé pour combler le trou architectural identifié par Mathis ("notre webapp ultra-poussée n'a pas de skills associés").

---

## A. RÔLE

Tu es le **publisher** de l'écosystème GrowthCRO V26.AA. Tu es responsable de :
1. **Publier** les audits clients dans la WebApp V26 PROD (`deliverables/GrowthCRO-V26-WebApp.html`)
2. **Maintenir** la base curatée 56 clients V26 (`data/curated_clients_v26.json`)
3. **Livrer** les LPs générées (Mode 1-5) dans `deliverables/`
4. **Régénérer** le fichier de données central `growth_audit_data.js`

**Important** : seules les pages avec audits propres + recos enrichies + brand_dna validé sont publiables. Pas d'industrialisation de masse — Mathis explicite : qualité absolue par client.

## B. ARTEFACTS WEBAPP

```
deliverables/
├── GrowthCRO-V26-WebApp.html           ⭐ PROD — webapp officielle V26 (213KB, design Deep Real Night)
├── growth_audit_data.js                ⭐ DATA — 11MB, 56 clients × 185 pages × 3186 recos
├── weglot-listicle-MODE1-V26AA.html    [LP référence Sprint 3]
├── weglot-listicle-MINIMAL.html        [benchmark gsg_minimal v1]
├── weglot-listicle-MINIMAL_V2.html     [benchmark gsg_minimal v2]
├── _bestof_weglot_premium_quiet_luxury_data.FIXED.html  [V26.Z BESTOF référence]
├── perfect_gsg_simulation_globalflow.html               [ChatGPT benchmark négatif]
├── clients/                             [JSON par client (56 fichiers, output webapp)]
└── japhy/                               [data Japhy historique]

data/
├── clients_database.json               [DB master 105 clients]
├── curated_clients_v26.json            [Base officielle 56 clients V26]
└── captures/<slug>/<page_type>/        [audits per-page]
```

## C. 4 ACTIONS PRINCIPALES

### Action 1 — Ajouter un client aux 56 curatés

**Critères de qualité** (NON négociables, qualité absolue) :
- ✅ `brand_dna.json` propre (palette + polices + voix extraits avec succès, pas de fallback archetype)
- ✅ Au moins 1 page capturée + scorée
- ✅ `score_page_type.json` cohérent avec doctrine V3.2.1 (pas de critères missing)
- ✅ `recos_v13_api.json` enrichies présentes
- ✅ Mathis valide visuellement la qualité

**Processus** :
```bash
# 1. Vérifier les artefacts du client candidat
ls data/captures/<slug>/{brand_dna.json,client_intent.json}
ls data/captures/<slug>/<page_type>/{capture.json,score_page_type.json,recos_v13_api.json}

# 2. Re-build growth_audit_data.js avec ce client inclus
python3 skills/site-capture/scripts/build_growth_audit_data.py \
    --include <slug> \
    --output deliverables/growth_audit_data.js

# 3. Mettre à jour la référence officielle
python3 -c "
import json
d = json.load(open('data/curated_clients_v26.json'))
# Ajouter le nouveau client à la liste
"
```

### Action 2 — Publier un nouveau audit dans la fleet

Quand un client existant a une page nouvelle auditée :
```bash
# Re-build webapp data avec la nouvelle page
python3 skills/site-capture/scripts/build_growth_audit_data.py
# (par défaut, lit tous les clients curatés et leurs pages)
```

### Action 3 — Publier une LP générée Mode 1-5

Quand le GSG V26.AA génère une LP :
```bash
# Le HTML est sauvé via save_html_path dans generate_lp()
# Convention de nommage : <client>-<page_type>-MODE<N>-V26AA[.iter<N>].html
# Ex : weglot-listicle-MODE1-V26AA.html

# Indexer dans deliverables/_lp_registry.json (à créer Sprint C)
```

### Action 4 — Régénérer growth_audit_data.js complet

Quand la doctrine V3.2 change (V3.2.1 → V3.2.2 par ex), re-scorer + rebuild :
```bash
# 1. Re-scorer tous les clients curatés avec la nouvelle doctrine
python3 -c "
import json
clients = json.load(open('data/curated_clients_v26.json'))['clients']
import subprocess
for c in clients:
    for pt in c['page_types']:
        subprocess.run(['python3', 'skills/site-capture/scripts/score_page_type.py', c['id'], pt])
"

# 2. Rebuild le data file central
python3 skills/site-capture/scripts/build_growth_audit_data.py

# 3. Vérifier le checksum (taille attendue ~11MB)
ls -la deliverables/growth_audit_data.js
```

## D. PIPELINE DE PUBLICATION D'UN CLIENT (workflow standard)

```
NOUVEAU CLIENT (ex: client_X)
    │
    ▼
1. add_client.py → entrée dans clients_database.json
    │
    ▼
2. brand_dna_extractor V29 → data/captures/client_X/brand_dna.json
    │
    ▼
3. brand_dna_diff_extractor E1 → diff prescriptif
    │
    ▼
4. playwright_capture_v2 → screenshots + DOM par page
    │
    ▼
5. perception_v13 + intent_detector_v13 → enrichissement
    │
    ▼
6. score_*.py × 6 + score_page_type.py → audit V26.AA
    │
    ▼
7. reco_clustering + reco_enricher_v13_api → recos
    │
    ▼
8. evidence_ledger + reco_lifecycle → traçabilité
    │
    ▼
9. webapp-publisher (CE SKILL) Action 1+2 → publish
    │
    ▼
10. WebApp V26 PROD affiche client_X dans la fleet
```

## E. RÈGLES DE PUBLICATION

1. **Qualité absolue** — pas d'industrialisation. Mathis explicite : "perfection unitaire par client".
2. **Validation visuelle Mathis avant publication** — chaque ajout aux 56 curatés requiert validation Mathis (lecture des screens + recos).
3. **Versioning data** — `growth_audit_data.js` doit toujours avoir `meta.generated_at` cohérent avec les audits sources.
4. **Pas d'écrasement silencieux** — si un client est déjà dans curated, demander confirmation avant remplacement.
5. **Tracking sources** — la WebApp doit pouvoir retracer chaque score à sa capture source (evidence_ledger V26.A).

## F. CONSOMMATION PAR LA WEBAPP

```javascript
// deliverables/GrowthCRO-V26-WebApp.html charge:
window.GROWTH_AUDIT_DATA = { ... }  // depuis growth_audit_data.js (11MB)

// Structure consommée:
GROWTH_AUDIT_DATA.meta              // version, generated_at, note
GROWTH_AUDIT_DATA.fleet             // n_clients, n_pages, n_recos, avg_score_pct
GROWTH_AUDIT_DATA.by_business       // segmentation par business_type
GROWTH_AUDIT_DATA.by_page_type      // segmentation par page_type
GROWTH_AUDIT_DATA.clients[]         // liste 56 clients avec pages + recos détaillées
```

## G. À FAIRE (gaps webapp publisher V26.AA)

- [ ] **Action 3 (publish LP générée)** : pas encore d'index `_lp_registry.json` dans deliverables. Sprint C.
- [ ] **Auto-publish quand audit reaches threshold** : pas auto. Mathis veut validation. Garder manuel pour l'instant.
- [ ] **Export PDF/DOCX** : pas implémenté. Roadmap Sprint D.
- [ ] **Historique versions** : pas de versioning de l'audit dans la webapp (chaque rebuild écrase). Sprint D.
- [ ] **Webapp v2 backend** : actuellement HTML statique + JS data file. Roadmap V27+ (skill `dashboard-engine`).

## H. NE PAS CONFONDRE

- **`webapp-publisher`** (ce skill) = publication des outputs dans la WebApp V26 PROD
- **`client-context-manager-v26-aa`** = création/maintenance du contexte client en amont
- **`growth-audit-v26-aa`** = audit qui produit les données à publier
- **`gsg-v26-aa`** = génération des LPs à publier

## I. LECTURE OBLIGATOIRE À CHAQUE DÉMARRAGE

1. Ce SKILL.md
2. `data/curated_clients_v26.json` (56 clients officiels)
3. `deliverables/GrowthCRO-V26-WebApp.html` (interface PROD)
4. Si publication d'audit : `skills/site-capture/scripts/build_growth_audit_data.py`
