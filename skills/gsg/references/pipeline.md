# GSG Pipeline V15 — Scripts et Commandes

## Pipeline complet (dans l'ordre)

### 1. Ajout client (si nouveau)
```bash
python3 add_client.py --url https://example.com --brand "NomMarque"
```
→ Crée l'entrée dans `data/clients_database.json`
→ Lance `ghost_capture.js` pour la homepage

### 2. Capture complète (si pas déjà fait)
```bash
python3 capture_full.py --client {slug}
```
→ Ghost capture + spatial_v9 + perception + intent
→ Output : `data/captures/{slug}/home/{capture.json, spatial_v9.json, ...}`

### 3. Scoring V13
```bash
python3 scripts/score_page_type.py --client {slug} --page home
```
→ Score /100 sur 47 critères × 6 blocs

### 4. Recos V13 (LLM Sonnet)
```bash
python3 scripts/reco_enricher_v13.py --client {slug} --page home --prepare
python3 scripts/reco_enricher_v13_api.py --client {slug} --page home
```
→ Output : `data/captures/{slug}/home/recos_v13_final.json`

### 5. Enrichissement V14.3.1 (public sources)
```bash
python3 scripts/enrich_v143_public.py --client {slug}
```
→ Enrichit `v143.*` dans clients_database (VoC, founder, archetype, etc.)

### 6. Site Intelligence V15 (crawl + DA)
```bash
python3 scripts/site_intelligence.py --url {URL} --client {slug} --max-pages 15
```
→ Output : `data/captures/{slug}/site_intel.json`
→ Contient : brand_identity (palette, fonts, mood), pages crawlées, faits vérifiés

### 7. Bridge Audit → Brief V15
```bash
python3 scripts/generate_lp_from_audit.py --client {slug} --page home --mode internal_agency
```
→ Output : `deliverables/{slug}/home/lp_blueprint.json` + `lp_brief.md`
→ Brief V15 avec §6 Brand Identity (palette réelle, polices réelles)

### 8. Production HTML (via lp-front skill)
→ Charger le brief en Mode A
→ lp-front applique la DA depuis §6
→ Self-audit ≥85/120

---

## Scripts clés et leur localisation

| Script | Chemin | Rôle |
|--------|--------|------|
| `site_intelligence.py` | `scripts/` | Crawl site + DA extraction |
| `generate_lp_from_audit.py` | `scripts/` | Bridge audit → brief V15 |
| `ghost_capture.js` | `scripts/` | Playwright capture (stealth) |
| `capture_full.py` | racine | Pipeline capture complet |
| `add_client.py` | racine | Ajout client lean |
| `score_page_type.py` | `scripts/` | Orchestrateur scoring |
| `reco_enricher_v13.py` | `scripts/` | Prépare payload recos |
| `reco_enricher_v13_api.py` | `scripts/` | Appel Sonnet pour recos |
| `enrich_v143_public.py` | `scripts/` | Enrichissement public |

## Données clés

| Fichier | Chemin type | Contenu |
|---------|-------------|---------|
| `site_intel.json` | `data/captures/{client}/` | Crawl complet + brand_identity |
| `recos_v13_final.json` | `data/captures/{client}/home/` | Recos enrichies LLM |
| `capture.json` | `data/captures/{client}/home/` | Capture brute |
| `spatial_v9.json` | `data/captures/{client}/home/` | Données spatiales sections |
| `lp_blueprint.json` | `deliverables/{client}/home/` | Blueprint machine-readable |
| `lp_brief.md` | `deliverables/{client}/home/` | Brief Mode A pour lp-front |
| `clients_database.json` | `data/` | Base clients (identity, v143, etc.) |
| `patterns.json` | `skills/cro-library/references/` | Patterns V14.2 (58 patterns) |
