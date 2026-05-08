# GrowthCRO RUNBOOK — pipeline end-to-end

**Version** : V26.AH rescue · **Maintenu depuis** : 2026-05-04 (Day 6/7 boundaries)

Ce runbook documente les commandes exactes pour faire tourner le pipeline GrowthCRO, de l'ajout d'un client à la livraison du dashboard enrichi. Tout ce qui est ici est **reproductible** : pas de tribal knowledge, pas de "il faut penser à…".

> Note V26.AH : les sections historiques V17 restent utiles, mais la source actuelle pour les frontières produit est `architecture/PRODUCT_BOUNDARIES_V26AH.md`. Ne pas utiliser les commandes legacy `build_dashboard_v17.py` pour la webapp active.

---

## 0A. Sauvetage V26.AH — commandes de vérité

### Etat disque + anti-oubli

```bash
python3 state.py
python3 scripts/audit_capabilities.py
sed -n '1,220p' CAPABILITIES_SUMMARY.md
```

### Scoring runtime

```bash
python3 -B skills/site-capture/scripts/score_page_type.py weglot home
python3 -B skills/site-capture/scripts/batch_rescore.py --only weglot
```

### Recos quality audit

```bash
python3 skills/site-capture/scripts/reco_quality_audit.py --client weglot --threshold 7 --verbose
```

### Webapp statique active

```bash
python3 skills/site-capture/scripts/build_growth_audit_data.py
node --check deliverables/growth_audit_data.js
```

Entrées statiques :

```text
deliverables/GrowthCRO-V26-WebApp.html
deliverables/GrowthCRO-V27-CommandCenter.html
```

### Audit to GSG handoff V27

```bash
node scripts/build_audit_to_gsg_brief.mjs --client weglot --page home
```

Outputs :

```text
deliverables/gsg_demo/weglot-home-gsg-v27.json
deliverables/gsg_demo/weglot-home-gsg-v27.md
deliverables/gsg_demo/weglot-home-gsg-v27-preview.html
```

### GSG canonical boundary V27

Validation sans génération, sans LLM :

```bash
python3 scripts/check_gsg_canonical.py
python3 scripts/check_gsg_controlled_renderer.py
python3 scripts/run_gsg_full_pipeline.py --help
```

Règle : le seul skill public est `skills/gsg`; le seul moteur public est `moteur_gsg`. Les scripts `skills/growth-site-generator/scripts/*` sont un legacy lab et ne doivent être appelés qu'à travers `moteur_gsg/core/legacy_lab_adapters.py`, sauf reproduction forensic explicite.

### Reality Layer pilote V26.AI

Dry-run sans écrire de faux output :

```bash
PYTHONPATH=skills/site-capture/scripts \
python3 -m reality_layer.orchestrator \
  --client kaiju \
  --page home \
  --days 30 \
  --no-write
```

Run réel après ajout d'au moins un connecteur dans `.env` :

```bash
PYTHONPATH=skills/site-capture/scripts \
python3 -m reality_layer.orchestrator \
  --client kaiju \
  --page home \
  --days 30
```

Le run réel écrit `data/captures/kaiju/home/reality_layer.json` seulement si au moins un connecteur est actif. `--write-empty` existe uniquement pour diagnostic, pas pour la webapp produit.

### GSG minimal canonique V27

Contrats à vérifier avant run :

```bash
python3 scripts/check_gsg_canonical.py
python3 scripts/check_gsg_controlled_renderer.py
```

```bash
python3 scripts/run_gsg_full_pipeline.py \
  --url https://www.weglot.com \
  --page-type lp_listicle \
  --lang FR \
  --mode complete \
  --objective "Convertir en signup / inscription trial Weglot via une LP listicle éditoriale." \
  --audience "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p, deja site live monolingue performant, considere internationalisation 2026. Peurs : backlog dev, SEO multi-langue, qualite traduction. Desirs : speed, ROI mesurable, qualite brand preservee." \
  --angle "10 raisons concretes pour lesquelles une equipe SaaS devrait internationaliser son site maintenant avec Weglot : angle editorial utile, brand-safe, sans chiffre non source, avec schemas produit/process." \
  --primary-cta-label "Tester gratuitement 10 jours" \
  --primary-cta-href "https://dashboard.weglot.com/register" \
  --generation-path minimal \
  --generation-strategy controlled \
  --non-interactive \
  --skip-judges \
  --save-dir data/_pipeline_runs/weglot_lp_listicle_v271_doctrine_brand \
  --save-html deliverables/weglot-lp_listicle-GSG-DOCTRINE-BRAND-V27-1.html
```

V27.1 : le chemin contrôlé branché sur `mode_1_complete` doit remonter doctrine constructive, tokens Brand/AURA, fonts réelles et screenshots capturés si disponibles. Le multi-judge reste post-run, jamais gate bloquant du renderer.

```bash
python3 moteur_multi_judge/orchestrator.py \
  --html deliverables/weglot-lp_listicle-GSG-DOCTRINE-BRAND-V27-1.html \
  --client weglot \
  --page-type lp_listicle \
  --output data/_pipeline_runs/weglot_lp_listicle_v271_doctrine_brand/multi_judge.json
```

Rollback prompt-to-HTML si besoin de comparer :

```bash
python3 scripts/run_gsg_full_pipeline.py \
  --url https://www.weglot.com --page-type lp_listicle --lang FR \
  --generation-path minimal --generation-strategy single_pass --non-interactive
```

Forensic seulement, pas default :

```bash
python3 scripts/run_gsg_full_pipeline.py \
  --url https://www.weglot.com --page-type lp_listicle --lang FR \
  --generation-path sequential --non-interactive
```

### Schema global

```bash
python3 SCHEMA/validate_all.py
```

Etat connu V26.AH post-rescue : cette commande passe sur le baseline local (`3325 files validated — all passing`). Les 6 erreurs Seazon `scoredAt=null` ont été corrigées à la source dans les scorers persuasion/ux/coherence, puis régénérées via `batch_rescore.py --only seazon`.

---

## 0. Prérequis (à faire une fois)

```bash
# 1. Cloner ou cd dans le projet
cd "/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society"

# 2. Virtualenv Python + deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Playwright browsers
playwright install chromium

# 4. Deps Node
npm install

# 5. Configurer les clés API
cp .env.example .env
# puis édite .env et mets ton vrai ANTHROPIC_API_KEY
export $(cat .env | xargs)   # ou utilise direnv/dotenv

# 6. Sanity check
python3 state.py
# Doit afficher : 291 captures / 104 clients / playbooks v3.2.0 locked
```

**Clés API rotation** : si tu viens de recevoir ce projet via Claude Code, les clés dans `WAKE_UP_NOTE_*.md` étaient en clair pré-P10. Regénère-les sur https://console.anthropic.com/settings/keys et https://console.apify.com/account/integrations avant tout premier commit public.

---

## 1. Pipeline "de 0 à audit complet pour 1 client"

Durée totale estimée : ~5-10 min/client (hors capture des pages), ~$1-2 API.

### 1.1 — Ajouter le client à la DB

Prérequis : tu connais l'URL du site.

```bash
python3 add_client.py \
  --slug japhy \
  --brand "Japhy" \
  --url https://japhy.fr
```

Ce script fait un pre-flight liveness check (DNS, 404, 5xx), capture la home via Playwright, parse les liens internes, classifie heuristiquement les pages (home/pdp/pricing/about/blog/quiz…), et écrit une entrée dans `data/clients_database.json`.

**Si l'URL est inconnue** (nom seul) : utilise `enrich_client.py` qui fait le `discover_url` via Claude. Plus lent, plus cher (Haiku × 3 appels).

### 1.2 — Capturer toutes les pages

```bash
# Capture Stage 1 (Playwright) pour un client
node skills/site-capture/scripts/ghost_capture.js \
  --url https://japhy.fr/ \
  --label japhy \
  --page-type home \
  --out-dir data/captures/japhy/home

# Repeat pour chaque page découverte (pdp, collection, quiz_vsl, etc.)
# Ou en batch :
python3 skills/site-capture/scripts/batch_spatial_capture.py --client japhy
```

Vérif : `ls data/captures/japhy/*/screenshots/` doit montrer au moins `desktop_*.png` + `mobile_*.png` par page.

### 1.3 — Perception + intent

```bash
python3 skills/site-capture/scripts/native_capture.py --client japhy
python3 skills/site-capture/scripts/perception_v13.py --client japhy --all
python3 skills/site-capture/scripts/intent_detector_v13.py --client japhy
```

Outputs : `capture.json`, `capture_native.json`, `perception_v13.json`, `client_intent.json`.

### 1.4 — Scoring (6 piliers + overlay v3.2)

```bash
# Page-type detection
python3 skills/site-capture/scripts/score_page_type.py japhy home
# (répète pour chaque page)

# 6 piliers
python3 skills/site-capture/scripts/batch_rescore.py --client japhy

# Overlay applicability v3.2 (7 règles)
python3 skills/site-capture/scripts/score_applicability_overlay.py --client japhy

# Semantic scorer Haiku (18 critères)
export ANTHROPIC_API_KEY=...   # si pas déjà dans l'env
python3 skills/site-capture/scripts/semantic_scorer.py --client japhy
```

Coût estimé : ~$0.50 Haiku pour 1 client complet (toutes pages).

### 1.5 — Recommandations (Sonnet)

```bash
python3 skills/site-capture/scripts/reco_enricher_v13.py --client japhy --prepare
python3 skills/site-capture/scripts/reco_enricher_v13_api.py \
  --client japhy \
  --model claude-sonnet-4-6 \
  --max-concurrent 5
```

Coût estimé : ~$1-2 Sonnet pour 1 client (5-10 pages).  
Output : `recos_enriched.json` + `recos_v13_final.json` par page.

### 1.6 — Build + enrich dashboard

```bash
python3 skills/site-capture/scripts/build_dashboard_v17.py
python3 skills/site-capture/scripts/enrich_dashboard_v17.py
```

Output : `deliverables/growthcro_data_v17.json` (55 MB, contient tous les clients).

### 1.7 — Verify dashboard

```bash
node deliverables/verify_dashboard_v17_2.js
```

Doit afficher `✅ Verification v17.2.0 passed`. Si ça casse, lis la stack trace et répare AVANT de livrer à Mathis.

---

## 2. Pipeline "fleet full re-score" (flotte complète)

⚠ Coûteux : ~$1-2 Haiku + ~$25 Sonnet + ~30 min de wall time.  
À faire uniquement quand la doctrine change (playbook bump) ou sur demande explicite.

```bash
# 1. Backup scores actuels (juste au cas où)
tar czf /tmp/scores_before_$(date +%F).tgz \
  $(find data/captures -name "score_*.json" -o -name "recos_*.json")

# 2. Re-score complet
python3 skills/site-capture/scripts/rerun_score_page_type_all_p2a.py
python3 skills/site-capture/scripts/batch_rescore.py --all
python3 skills/site-capture/scripts/score_applicability_overlay.py --all
python3 skills/site-capture/scripts/semantic_scorer.py --all

# 3. Re-build recos
python3 skills/site-capture/scripts/reco_enricher_v13.py --all --prepare
python3 skills/site-capture/scripts/reco_enricher_v13_api.py --all --model claude-sonnet-4-6 --max-concurrent 5

# 4. Rebuild dashboard
python3 skills/site-capture/scripts/build_dashboard_v17.py
python3 skills/site-capture/scripts/enrich_dashboard_v17.py

# 5. Verify
node deliverables/verify_dashboard_v17_2.js

# 6. Manifest entry (obligatoire)
# Ajouter une ligne dans GROWTHCRO_MANIFEST.md §11 avec :
# - date
# - raison du re-score (quel playbook a bougé)
# - delta moyen sur les scores
# - coût total API réel
```

---

## 3. Pipeline "score-only (recapture pas nécessaire)"

Utile quand tu viens de bumper un scorer mais pas la capture.

```bash
# Skip Stage 1 (capture) et Stage 3 (perception), ils sont déjà à jour
# Jump directement à Stage 4 (scoring)
python3 skills/site-capture/scripts/batch_rescore.py --client japhy
python3 skills/site-capture/scripts/semantic_scorer.py --client japhy
python3 skills/site-capture/scripts/reco_enricher_v13.py --client japhy --prepare
python3 skills/site-capture/scripts/reco_enricher_v13_api.py --client japhy
python3 skills/site-capture/scripts/build_dashboard_v17.py --incremental japhy
```

---

## 4. Troubleshooting connu

### "Playwright timeout 30s sur Shopify"
→ Shopify a des protections bot (Datadome). Utiliser `ghost_capture_cloud.py` (Apify Browser) ou augmenter le timeout à 120s + ajouter un `page.wait_for_selector('body', state='attached', timeout=60000)`.

### "Score psycho_08 à 0/3 alors que j'ai des avis Trustpilot visibles"
→ Correction de 2026-04-17 PM6b : le prompt a été élargi pour voir les badges/compteurs en plus du texte. Si le problème réapparaît, check que `semantic_scorer.py` utilise bien `_get_social_proof_summary()` dans le prompt.

### "Le dashboard V17 rend blanc"
→ Cas typique : un screenshot manquant fait planter silencieusement un render. Ouvre la console JS du browser + lance `node deliverables/verify_dashboard_v17_2.js` pour isoler.

### "Recos vides pour une page"
→ Vérifie les prérequis : `recos_v13_prompts.json` doit exister (produit par `--prepare`), puis `recos_enriched.json` (produit par `_api.py`). Si `--prepare` a échoué, c'est souvent parce qu'un `score_*.json` est manquant ou corrompu.

### "Hero_01 systématiquement à 0 sur les SPA"
→ Fix de 2026-04-18 P3 : les pages SPA nécessitent un deep scroll (Stage 3.5 dans `ghost_capture.js`) pour déclencher le lazy-loading. Re-capture avec `--deep-scroll`.

### "Je veux supprimer un client définitivement"
→ Sur macOS natif (Claude Code) : `rm -rf data/captures/<slug>/` + `jq 'del(.clients."<slug>")' data/clients_database.json > /tmp/db.json && mv /tmp/db.json data/clients_database.json`. Puis rebuild dashboard.  
→ **En environnement CoWork le `rm` est bloqué** (filesystem mount restrictif), `mv` vers `_archive_*` est la seule voie.

---

## 5. Commandes rapides (aliases recommandés)

Ajoute dans ton `.zshrc` / `.bashrc` :

```bash
alias gcro-state="python3 state.py"
alias gcro-capture="node skills/site-capture/scripts/ghost_capture.js"
alias gcro-score="python3 skills/site-capture/scripts/batch_rescore.py"
alias gcro-build="python3 skills/site-capture/scripts/build_dashboard_v17.py && python3 skills/site-capture/scripts/enrich_dashboard_v17.py"
alias gcro-verify="node deliverables/verify_dashboard_v17_2.js"
```

Ou utilise les slash commands Claude Code (`.claude/commands/`) :

- `/audit-client <slug>` — full pipeline
- `/score-page <slug> <pageType>` — scoring ciblé
- `/pipeline-status` — état disque détaillé
- `/doctrine-diff <bloc> <old> <new>` — compare playbooks
- `/full-audit` — santé projet

---

## 6. Coûts API de référence

| Opération | Modèle | Coût approx. |
|---|---|---|
| Ajout client (discover URL) | Haiku | $0.01-0.05 |
| Semantic scorer — 1 page (18 critères) | Haiku 4.5 | $0.003 |
| Semantic scorer — fleet 291 pages | Haiku 4.5 | ~$1-2 |
| Reco enricher — 1 page (~30 critères P0-P3) | Sonnet 4.5 | ~$0.08 |
| Reco enricher — fleet 291 pages | Sonnet 4.5 | ~$20-25 |
| Full pipeline re-score fleet | Haiku + Sonnet | ~$25-30 |

Surveille `console.anthropic.com/settings/usage` après chaque gros run.

---

## 7. Sources de vérité à consulter en cas de doute

1. `python3 state.py` → vérité disque factuelle.
2. `GROWTHCRO_MANIFEST.md` → architecture à jour.
3. `memory/HISTORY.md` → historique des décisions.
4. `playbook/bloc_*_v3.json` → doctrine scoring active.
5. Ce `RUNBOOK.md` → commandes reproductibles.

Si les quatre divergent, le manifest gagne. Si le manifest est flou, `state.py` gagne.
