# GrowthCRO Product Boundaries V26.AH

> Date : 2026-05-04 (initial) · 2026-05-15 (webapp topology revision per D1.A)
> Status : Day 6 du plan de sauvetage. Source de vérité pour ne plus recoller Audit, Recos, GSG, Webapp, Reality, Experiments, Learning et GEO dans un seul flux flou.
> Cross-ref : webapp topology = 1 shell, 0 µfrontend — voir [`MICROFRONTENDS_DECISION_2026-05-14.md`](MICROFRONTENDS_DECISION_2026-05-14.md) (D1.A) et [`DECISIONS_2026-05-14.md`](DECISIONS_2026-05-14.md) §D1.

## 0. Verdict Brutal

GrowthCRO n'est pas "un GSG avec des audits autour". C'est un système interne de consulting CRO automatisé.

Le coeur court terme est :

1. Audit Engine reproductible.
2. Recommendations Engine fiable.
3. Observatoire webapp honnête.
4. Données structurées qui s'accumulent.

Le GSG reste stratégique, mais seulement comme produit interne séparé. Il ne doit plus casser ou complexifier le socle Audit/Reco.

## 1. Frontières Produit

| Produit interne | Rôle | Etat V26.AH | Source de vérité |
|---|---|---|---|
| Audit & Reco Engine | Capturer, interpréter, scorer, générer recos enrichies | Actif, restauré Day 1-2 | `skills/site-capture/scripts/`, `scripts/reco_enricher_v13*.py`, `playbook/` |
| GSG | Générer une LP HTML à partir d'un brief validé | Moteur canonique + renderer contrôlé v1 `lp_listicle`, pas final créatif validé | `moteur_gsg/`, `skills/gsg/SKILL.md`, `architecture/GSG_CANONICAL_CONTRACT_V27_2026-05-05.md` |
| Webapp Observatoire | Lire les données disque et les exposer honnêtement | Static MVP | `deliverables/GrowthCRO-V26-WebApp.html`, `skills/site-capture/scripts/build_growth_audit_data.py` |
| Reality Layer | Importer la vérité business GA4/Meta/Google/Shopify/Clarity | Code prêt, inactive / no data | `skills/site-capture/scripts/reality_layer/` |
| Experiment Engine | Transformer recos en hypothèses mesurables | Calculator disponible, 0 run | `skills/site-capture/scripts/experiment_engine.py` |
| Learning Layer | Proposer updates doctrine depuis signaux observés | Partiel, 69 proposals audit-based | `skills/site-capture/scripts/learning_layer_v29_audit_based.py`, `data/learning/` |
| GEO | Suivre présence ChatGPT/Perplexity/Claude | Partiel, APIs manquantes | `skills/site-capture/scripts/geo_readiness_monitor.py`, `geo_audit.py` |
| Multi-judge | Evaluer HTML généré ou page auditée | Actif partiel | `moteur_multi_judge/` |

## 2. Règle d'Or

Chaque module peut lire des outputs d'autres modules, mais il ne doit pas déclencher silencieusement leur pipeline.

Exemple :
- GSG peut lire `brand_dna.json`, `client_intent.json`, `recos_v13_final.json`, `evidence_ledger.json`.
- GSG ne doit pas lancer `batch_rescore.py`, régénérer les recos, ou modifier les scores.
- GSG ne doit pas appeler `skills/growth-site-generator/scripts` directement : uniquement via `moteur_gsg/core/legacy_lab_adapters.py`.
- Webapp peut afficher GSG comme `frozen` ou `minimal`, mais ne doit pas faire semblant que le GSG complet est product-grade.

## 3. Graphe Cible

```text
Audit Engine
  capture.json / screenshots / perception_v13.json / scores
        |
        v
Recommendations Engine
  recos_v13_final.json / recos_enriched.json / evidence_ledger.json
        |
        +---------------------> Webapp Observatoire (read-only static MVP)
        |
        +---------------------> GSG (read-only context, brief validated first)

Reality Layer
  reality_layer.json
        |
        +---------------------> Webapp Observatoire
        +---------------------> Experiment Engine

Experiment Engine
  experiment specs / measured outcomes
        |
        +---------------------> Learning Layer

Learning Layer
  doctrine proposals
        |
        +---------------------> Doctrine review by Mathis
        +---------------------> playbook/ only after explicit validation

GEO
  geo readiness / monitor cache
        |
        +---------------------> Webapp Observatoire
```

## 3-bis. Topologie Webapp (D1.A monorepo, 2026-05-14)

**Décision verrouillée** : `webapp/` = un seul Next.js 14 App Router app sous `webapp/apps/shell/` (package `@growthcro/shell` v0.28.0). PAS de microfrontends, PAS de `microfrontends.json`, PAS de multi-zone routing.

```text
webapp/
  apps/
    shell/                          ← @growthcro/shell v0.28.0 (only Next.js app)
      app/
        audits/                     ← ex apps/audit-app/
        recos/                      ← ex apps/reco-app/
        gsg/                        ← ex apps/gsg-studio/
        gsg/handoff/                ← ex Brief Wizard relocated (D3.A)
        reality/                    ← ex apps/reality-monitor/
        learning/                   ← ex apps/learning-lab/
        clients/                    ← lifecycle (D, sub-PRD 3)
        settings/                   ← admin
        api/                        ← Next.js API routes (Phase A backend)
      components/
        {audits,recos,gsg,reality,learning}/  ← feature-co-located
  packages/
    data/                           ← @growthcro/data — shared types
    ui/                             ← @growthcro/ui — shared primitives
_archive/
  webapp_microfrontends_2026-05-12/ ← FR-1 archived 5 µfrontends (git mv)
```

**Trigger pour re-évaluer D1.A** :
- Trigger A : 2e dev full-time qui owne une feature cohérente (codeowners boundaries deviennent friction réelle).
- Trigger B : feature qui dépasse l'envelope du bundle partagé (envisage d'abord lazy-load route-level, escalade µfrontends seulement si insuffisant).

Tant qu'aucun trigger n'a fired, **D1.A tient**. Tout nouveau fichier `webapp/apps/<feature>/` autre que `shell/` = anti-pattern bloquant.

**Cross-refs** :
- Decision doc : [`MICROFRONTENDS_DECISION_2026-05-14.md`](MICROFRONTENDS_DECISION_2026-05-14.md)
- DECISIONS §D1 : [`DECISIONS_2026-05-14.md`](DECISIONS_2026-05-14.md)
- FR-1 epic (consolidation 2026-05-13) : [`webapp-consolidate-architecture`](../../prds/webapp-consolidate-architecture.md)
- Skill `vercel-microfrontends` dropped : [`SKILLS_INTEGRATION_BLUEPRINT.md` §4.1.4](../reference/SKILLS_INTEGRATION_BLUEPRINT.md)
- Architecture explorer : `deliverables/architecture-explorer-data.js` (pipelines.webapp_v28 = single shell entry, meta.revision_notes log)

## 4. Dépendances Autorisées

| Source | Peut lire | Peut écrire |
|---|---|---|
| Audit Engine | `playbook/`, `data/clients_database.json`, captures existantes | `data/captures/<client>/<page>/capture*.json`, `score_*.json`, `score_page_type.json` |
| Recos Engine | scores, perception, evidence, playbook, client context | `recos_v13_prompts.json`, `recos_v13_final.json`, `recos_enriched.json`, dedup reports |
| GSG | `scripts/client_context.py`, `brand_dna`, `design_grammar`, `AURA`, recos/evidence read-only, brief user | `deliverables/*GSG*.html`, telemetry/audit GSG, never score source files |
| Webapp | curated panel, captures, recos, module status artifacts | `deliverables/growth_audit_data.js`, static HTML only |
| Reality | credentials/env vars, client mappings | `reality_layer.json`, never scores directly |
| Experiment | recos, reality data, manual status | experiment run specs/results |
| Learning | experiments measured, audits aggregate, manual review inputs | `data/learning/*proposals*`, never playbook directly |
| GEO | client/brand context, API keys | GEO artifacts/cache |

## 5. Dépendances Interdites

| Interdit | Pourquoi |
|---|---|
| GSG déclenche scoring ou recos en arrière-plan | Mélange génération et vérité runtime ; rend les régressions impossibles à isoler |
| Webapp affiche un module inactive comme actif | Dette produit et perte de confiance |
| Learning modifie `playbook/` sans validation Mathis | Doctrine = IP, pas sortie automatique |
| Reality pondère les scores avant 1 client validé | Risque de faux sentiment de vérité business |
| Multi-judge gate bloquant pendant génération | V26.AF a montré que les gates agressifs rendent le design défensif |
| Design Grammar/AURA injectés en mega-prompt | Anti-pattern prouvé ; transformer en tokens/planner/gates |
| GSG séquentiel redevient default | Chemin expérimental, pas baseline stable |
| `gsg_generate_lp.py` redevient entrypoint public | Mega-prompt V26.Z + eval_grid parallèle ; utiliser `moteur_gsg` |

## 6. Entrypoints Officiels V26.AH

### Audit / Scoring

```bash
python3 -B skills/site-capture/scripts/score_page_type.py weglot home
python3 -B skills/site-capture/scripts/score_site.py weglot saas
python3 -B skills/site-capture/scripts/batch_rescore.py --only weglot
```

### Recos

```bash
python3 scripts/reco_enricher_v13.py --client weglot --prepare
python3 scripts/reco_enricher_v13_api.py --pages-file /tmp/weglot_pages.txt --model claude-haiku-4-5-20251001 --max-concurrent 2
python3 skills/site-capture/scripts/reco_quality_audit.py --client weglot
```

### Webapp statique

```bash
python3 skills/site-capture/scripts/build_growth_audit_data.py
node --check deliverables/growth_audit_data.js
```

### GSG canonique minimal

```bash
python3 scripts/check_gsg_canonical.py
python3 scripts/check_gsg_controlled_renderer.py

python3 scripts/run_gsg_full_pipeline.py \
  --url https://www.weglot.com \
  --page-type lp_listicle \
  --lang FR \
  --mode complete \
  --objective "Convertir trial gratuit" \
  --audience "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p..." \
  --angle "Listicle founder-led en francais avec chiffres sources" \
  --generation-path minimal \
  --generation-strategy controlled \
  --non-interactive \
  --primary-cta-label "Tester gratuitement 10 jours" \
  --primary-cta-href "https://dashboard.weglot.com/register" \
  --skip-judges \
  --save-html deliverables/weglot-lp_listicle-GSG-CANONICAL.html
```

## 7. Statut de Gel

| Module | Décision Day 6 | Conditions de dégel |
|---|---|---|
| `moteur_gsg/core/pipeline_sequential.py` | Gel expérimental | Reconstruction avec planner déterministe validé |
| `mode_1_persona_narrator.py` | Forensic only | Ne redevient jamais default sans test comparatif |
| `skills/growth-site-generator/scripts/gsg_generate_lp.py` | Gel legacy lab | Reproduction forensic avec `--allow-legacy-lab` seulement |
| `skills/growth-site-generator/scripts/gsg_multi_judge.py` | Gel legacy lab | Remplacé par `moteur_multi_judge/` |
| `skills/mode-1-launcher/SKILL.md` | FROZEN | Remplacé par `skills/gsg/SKILL.md` |
| Design Grammar en prompt | Gel pre-prompt | Revenir comme tokens/composants/gates |
| AURA en prompt long | Gel pre-prompt | Revenir comme design tokens sélectionnés |
| Learning Layer | Lecture seule | Mathis review des 69 proposals + test doctrine |
| Reality Layer | Inactive jusqu'à credentials | 1 client Kaiju validé avec outputs réels |
| GEO | Partiel | OPENAI/PERPLEXITY keys + protocole mensuel |

## 8. GSG Reconstruction Cible

Le GSG propre n'est pas un prompt plus long. C'est :

1. Brief validé.
2. Planner déterministe : structure de page, sections, CTA, preuves autorisées.
3. Tokenizer Brand DNA/AURA/Design Grammar : palette, typo, spacing, composants autorisés.
4. Copy LLM séparée : uniquement texte de section, pas HTML complet.
5. Renderer contrôlé : HTML/CSS généré par système, pas improvisé.
6. Audit post-run : multi-judge, minimal guards, screenshots, pas gate bloquant en plein run.

## 9. Décision Pour les Prochains Sprints

Avant tout nouveau code :

1. Vérifier `python3 state.py`.
2. Lancer `python3 scripts/audit_capabilities.py`.
3. Lire `CAPABILITIES_SUMMARY.md`.
4. Confirmer quel produit interne est concerné.
5. Refuser les changements transverses si la frontière n'est pas écrite.

Si une demande touche plusieurs produits, créer un plan en deux commits minimum : runtime puis manifest/docs.
