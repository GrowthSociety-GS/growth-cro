# GrowthCRO — Outil interne d'audit CRO + closed-loop apprenant

**État** : V27.2-F GSG route selector Golden/Creative structuré (2026-05-07) · **Vision** : Notion `Mathis Project x GrowthCRO Web App` + `Le Guide Expliqué Simplement`

---

## 0. Qu'est-ce que GrowthCRO ?

GrowthCRO est un **consultant CRO senior automatisé** pour les ~100 clients de l'agence **Growth Society** (media buying performance Meta/Google/TikTok). C'est un AUDIT engine + closed-loop apprenant qui :

1. **Audite** les LPs des clients (capture → vision → score doctrine V3.2 → recos enrichies)
2. **Mesure** l'impact RÉEL via 5 connecteurs (GA4 / Meta / Google / Shopify / Clarity)
3. **Suit** chaque reco du backlog jusqu'au A/B (lifecycle ticket)
4. **Apprend** de chaque expé (Bayesian update doctrine)
5. **Génère** des LPs fidèles à la marque (Brand DNA + Design Grammar + GSG)
6. **Monitore** la présence dans ChatGPT/Perplexity/Claude (GEO 2026)

→ **Boucle fermée** : Audit → Action → Mesure → Apprentissage → Génération → Monitoring.

**Architecture cible** (`architecture/GROWTHCRO_ARCHITECTURE_V1.md`) : webapp Next.js 14 + Supabase + Vercel. Aujourd'hui : HTML statique V26 `deliverables/GrowthCRO-V26-WebApp.html` + V27 Command Center `deliverables/GrowthCRO-V27-CommandCenter.html` (lit `growth_audit_data.js`, fonctionne en `open html` direct sans serveur).

**Séparation produit active V26.AH** : lire `architecture/PRODUCT_BOUNDARIES_V26AH.md` avant tout nouveau sprint. Audit/Reco, GSG, Webapp, Reality, Experiment, Learning et GEO sont des produits internes séparés avec dépendances explicites.

---

## 1. Point d'entrée nouvelle session

À LIRE dans cet ordre **OBLIGATOIRE** :

1. **`CLAUDE.md`** (= symlink → `.claude/CLAUDE.md`) — entrypoint init session + checklist anti-oubli
2. **`.claude/README.md`** — index de la doctrine (state / reference / architecture / memory)
3. **Notion** : `Mathis Project x GrowthCRO Web App` + `Le Guide Expliqué Simplement` (vision produit canonique)
4. **`.claude/docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`** — plan d'action ordonné (Sprints F-L)
5. **`.claude/docs/state/AUDIT_TOTAL_V26AE_2026-05-04.md`** — diagnostic complet état actuel
6. **`.claude/docs/reference/GROWTHCRO_MANIFEST.md`** — source de vérité architecturale (changelog §12)
7. **`.claude/memory/MEMORY.md`** — index mémoires
8. Run `python3 state.py` + `python3 scripts/audit_capabilities.py` — état disque réel + registry

---

## 2. Architecture — 8 modules

| # | Module | État V26.AI |
|---|---|---|
| 1 | **Audit Engine** (capture + vision + scoring) | ✅ Actif, scoring restauré V26.AG, panel runtime V27 rôlé 56 clients |
| 1b | **Recommendations Engine** | ✅ Actif, Weglot validé Day 2, quality audit durci |
| 2 | **Brand DNA + Design Grammar** (V29 + V30) | ✅ 51/56 fleet (91%) |
| 3 | **GSG** (génération LP, 5 modes COMPLETE/REPLACE/EXTEND/ELEVATE/GENESIS) | ⚠️ Canonique V27.2-F : raw request → intake wizard → BriefV2 → context/doctrine/visual → structured Golden/Creative route selector → renderer ; pas encore assets/motion premium final |
| 4 | **Webapp Observatoire V26/V27** | ✅ V26 static honnête + V27 Command Center Audit/Reco/GSG |
| 5 | **Reality Layer V26.C** (5 connectors GA4/Meta/Google/Shopify/Clarity) | ⚠️ Orchestrator corrigé V26.AI, dry-run OK, env vars manquent |
| 6 | **Multi-judge V26.D** (doctrine + humanlike + implementation) | ⚠️ Disponible post-run, pas gate bloquant GSG |
| 7 | **Experiment Engine V27** (sample size + kill switches) | ⚠️ Calculator OK, pas de A/B déclenchés |
| 8 | **Learning Layer V28+V29** (Bayesian update) | ⚠️ V29 audit-based shippé (69 proposals en attente review) |
| 9 | **GEO Monitor V31+** (ChatGPT/Perplexity/Claude) | ❌ Manque OPENAI_API_KEY + PERPLEXITY_API_KEY |

---

## 3. Structure du dépôt (post-V26.AH Rescue)

```
.
├── README.md                         ← tu es ici
├── CLAUDE.md → .claude/CLAUDE.md     ← symlink (autoload Claude Code)
├── AGENTS.md → .claude/CLAUDE.md     ← symlink (autoload Codex CLI)
├── .claude/                          ← TOUTE la doctrine Claude+Codex (V26.AG)
│   ├── CLAUDE.md                     ← entrypoint compact
│   ├── README.md                     ← index hiérarchie
│   ├── agents/, commands/            ← subagents + slash commands
│   ├── docs/
│   │   ├── state/                    ← AUDIT_TOTAL, STRATEGIC, CAPABILITIES_SUMMARY
│   │   ├── reference/                ← MANIFEST, DESIGN_DOC, RUNBOOK, FRAMEWORK_CADRAGE, HANDOFF, START_HERE
│   │   └── architecture/             ← V27 contracts + reconstruction specs + rescue decision
│   └── memory/                       ← MEMORY/HISTORY/SPECS + project_*.md + snapshots/
├── CAPABILITIES_REGISTRY.json        ← anti-oubli registry (auto-généré, racine)
│
├── playbook/                         ← Doctrine V3.2.1 (25 fichiers)
│   ├── bloc_*_v3.json × 7 (54 critères)
│   ├── killer_rules.json, anti_patterns.json, thresholds_benchmarks.json
│   ├── usp_preservation.json, guardrails.json, page_type_criteria.json
│   └── README.md, AXIOMES.md, LEARNINGS.md
│
├── data/                             ← Captures + golden + learning + briefs
│   ├── captures/<client>/<page>/     ← brand_dna + design_grammar + perception + scores + recos + evidence
│   ├── golden/                       ← 30 sites de référence (Linear, Stripe, Aesop...)
│   ├── learning/audit_based_proposals/  ← 69 proposals doctrine V3.3 (à review)
│   ├── layout_archetypes/            ← 5 archétypes par page_type (Sprint AD-5)
│   ├── doctrine/                     ← matrices criteria_scope + applicability
│   ├── _briefs_v15/, _briefs_v2/
│   ├── clients_database.json (+ v143 inline)
│   └── curated_clients_v26.json (56 clients officiels)
│
├── scripts/                          ← Entrypoints racine partagée
│   ├── doctrine.py                   ← Loader doctrine V3.2.1 (Sprint 1 V26.AA)
│   ├── client_context.py             ← ROUTER RACINE V26.AC (charge tous artefacts)
│   ├── audit_capabilities.py         ← Anti-oubli auto-discovery
│   ├── check_gsg_canonical.py        ← Validation GSG unique sans génération
│   ├── run_gsg_full_pipeline.py      ← Runner GSG canonique raw request/BriefV2, minimal default, sequential forensic opt-in
│   ├── check_gsg_intake_wizard.py    ← Validation demande brute → BriefV2 → rendu fallback sans API
│   ├── check_gsg_creative_route_selector.py ← Validation Golden/Creative route selector sans API
│   ├── enrich_v143_public.py         ← Founder/VoC/Scarcity enrichment
│   └── reco_enricher_v13.py + .api.py
│
├── moteur_gsg/                       ← GSG canonique V27.2-F (intake_wizard + 5 modes + structured route selector + context/doctrine/visual/component/visual-system contracts)
│   ├── orchestrator.py               ← API publique generate_lp(mode, ...)
│   ├── core/                         ← context_pack, doctrine_planner, visual_intelligence, creative_route_selector, component_library, visual_system, planner, pattern_library, design_tokens, copy_writer, controlled_renderer, guards
│   └── modes/                        ← mode_1_persona_narrator, mode_2_replace, mode_3_extend, mode_4_elevate, mode_5_genesis
│
├── moteur_multi_judge/               ← Multi-judge unifié V26.AA
│   ├── orchestrator.py               ← run_multi_judge 70/30 doctrine/humanlike
│   └── judges/doctrine_judge.py      ← V3.2.1 parallélisé pilier (Sprint 2)
│
├── skills/                           ← 10 skills Claude Code + 3 roadmap V27
│   ├── site-capture/scripts/         ← Pipeline AUDIT V26 (~67 .py post-cleanup, 16 actifs)
│   ├── gsg/                          ← seul skill public GSG
│   ├── growth-site-generator/scripts/  ← legacy lab AURA/creative/fix_html via adapters uniquement
│   ├── cro-auditor, client-context-manager, webapp-publisher, mode-1-launcher(FROZEN), audit-bridge-to-gsg, cro-library
│   └── _roadmap_v27/  ← notion-sync, connections-manager, dashboard-engine (vision V27)
│
├── deliverables/                     ← Webapp PROD + livrables LPs
│   ├── GrowthCRO-V26-WebApp.html     ← webapp observatoire V26
│   ├── GrowthCRO-V27-CommandCenter.html ← webapp V27 Audit/Reco/GSG
│   ├── growth_audit_data.js          ← data 11.7 MB (56 clients × 185 pages × 3045 recos webapp)
│   ├── gsg_demo/                     ← QA screenshots GSG Weglot V27/V27.1
│   ├── clients/                      ← 105 .json snapshots
│   ├── japhy/                        ← data Japhy historique
│   └── weglot-listicle-V26AD-PLUS-FULL-STACK.html  ← dernier livrable test
│
├── reports/v143_validator/           ← Baselines validation v143
├── SCHEMA/                           ← 7 schemas + validate_all.py
│
└── _archive/                         ← Tout l'historique gelé (~2500 fichiers consolidés V26.AE)
    ├── data_backups, docs, scripts, skills_legacy, playbook_legacy
    ├── archive_pre_v26ae_2026-05-04/ (ex archive/)
    ├── _archive_V19_feature_fantomes/, _archive_deprecated_2026-04-19/
    └── legacy_pre_v26ae_2026-05-04/  ← V26.AE Cleanup (2026-05-04)
        ├── root_files/, wake_ups_obsolete/, todos_obsolete/, bundles_chatgpt_done/
        ├── deliverables_iter/, data_iter/
        ├── site_capture_scripts/ (~35 fichiers)
        ├── moteur_gsg_legacy/ (mode_1_complete.py)
        ├── tests_oneshots/, skills_legacy/
        ├── outputs/, outputs_distill/, prototype/, test_headed/, test_stealth/, scripts_local/
        └── captures_archive_2026-04-29/
```

---

## 4. Pipeline V26 audit (8 stages)

```
URL client → DISCOVERY → CAPTURE → INTERPRETATION → SCORING → EVIDENCE → RECOS → LIFECYCLE
                                                                              ↓
                                                                          REALITY (V26.C)
                                                                              ↓
                                                                       EXPERIMENT (V27)
                                                                              ↓
                                                                        LEARNING (V29)
                                                                              ↓
                                                                          GSG (V29+V30 → V32+)
                                                                              ↓
                                                                        QA CRITICS
                                                                              ↓
                                                                          CLIENT
```

**Lancement ad-hoc** :
```bash
# Audit single client
python3 capture_full.py <url> <client_label> <business_type>

# Ou via skills
python3 skills/site-capture/scripts/playwright_capture_v2.py
python3 skills/site-capture/scripts/perception_v13.py --client <label>
python3 skills/site-capture/scripts/batch_rescore.py --only <label>
python3 skills/site-capture/scripts/reco_enricher_v13.py --client <label> --prepare
python3 skills/site-capture/scripts/reco_enricher_v13_api.py --client <label>

# Génération LP
python3 -m moteur_gsg.orchestrator --mode complete --client weglot \
  --page-type lp_listicle --objectif "..." --audience "..." --angle "..."
```

Voir `.claude/docs/reference/RUNBOOK.md` pour procédures complètes.

---

## 5. Coûts (récurrents)

- **Onboarding nouveau client** : ~$0.16 (5 pages × Vision + recos Batch)
- **Run fleet entière** (62 clients) : ~$10-15 via Batch API
- **Reality Layer** : $0 (APIs déjà payées par client)
- **GEO Monitor mensuel** : ~$0.30/client × 30 = ~$10/mois
- **Multi-judge** : ~$0.50/run (Sonnet seul sur disagreement)

→ **Coût marginal client géré** : ~$3-4/mois inclusif tout (audit + reality + GEO + experiment + learning).
À comparer aux $2,000-5,000/mois qu'un consultant senior facturerait.

---

## 6. Conventions strictes

- **Qualité > Vitesse** : toujours l'option la plus complète
- **Dual-viewport obligatoire** : Desktop + Mobile séparément
- **Screenshots = proof** : DOM rendered + PNG, pas HTML statique
- **CTA dedup par href** avant ratio 1:1
- **Pas de Notion auto** : jamais modifier sans demande explicite
- **Check before assume** : grep + lire MANIFEST/AUDIT_TOTAL avant d'affirmer
- **Anti-pattern #1** : prompt persona_narrator > 8K chars = STOP (régression -28pts empirique)
- **Doctrine 'concision > exhaustivité'** : enrichissements en POST-PROCESS GATES, pas pre-prompt

---

## 7. État actuel V26.AI (2026-05-05)

**Stats fleet** : 56 clients runtime rôlés V27 · 185 pages auditées · 3045 recos LP-level webapp (3186 déclarées dans l'ancien snapshot V26) + 170 step-level · 8347 evidence items · 51/56 Brand DNA + Design Grammar (91%) · 11 panes webapp · doctrine V3.2.1 (54 critères + 6 killer_rules)

**Marche** : Audit per-page · scoring restauré · schema global vert · score site agrégé depuis `score_page_type.json` · Recos Engine Weglot validé · Funnel V3 DOM-first · Brand DNA + Design Grammar · Evidence Ledger · Lifecycle · Webapp static MVP honnête · V27 Command Center Audit/Reco/GSG · GSG canonique clarifié (`skills/gsg` + `moteur_gsg`) · V27.2 context pack + doctrine creation contract + visual intelligence + creative route contract · V27.2-B component library pour `lp_listicle`, `advertorial`, `lp_sales`, `lp_leadgen`, `home`, `pdp`, `pricing` · V27.2-C visual system deterministic + renderer variants + Playwright QA desktop/mobile · V27.2-D vrai run Weglot copy Sonnet QA PASS + multi-judge `70.9%` Bon · V27.2-E intake wizard raw request → BriefV2 → rendu fallback PASS · V27.2-F Golden Bridge + Creative Director structurés en route selector sans API ni prompt dumping · Discovery V25.B · Learning V29 (69 proposals en review)

**Ne marche pas (encore)** :
- GSG créatif final "stratosphérique" : V27.2-F valide la route créative structurée, mais il manque encore assets/motion/modules premium et tests réels hors SaaS listicle.
- Copy LLM section-level à calibrer sur plus de pages et business categories
- Multi-judge Weglot V27.1 reste Moyen (53.8%) : killer `coh_03` faute de source ad/scent matching, humanlike juge la signature trop "SaaS éditorial propre"
- Reality Layer (orchestrator dry-run OK ; env vars Catchr/Meta/GA/Shopify/Clarity manquent)
- Multi-judge comme contrôle systématique post-run sur tous les flux
- Experiment Engine (calculator OK, pas de A/B déclenchés)
- Learning Layer (besoin ≥30 expé mesurées pour mature)
- GEO Monitor multi-engine (manque OPENAI + PERPLEXITY keys ; Anthropic seul actif sur 4/56)

**Reste à faire (priorité ordonnée)** :
1. Renforcer assets/motion/modules visuels premium par page type.
2. Tester une vraie génération non-SaaS ou non-listicle avec copy Sonnet + QA.
3. Calibrer copy slots par catégorie business et type LP avec `GenerationContextPack` + `DoctrineCreationContract` + `VisualIntelligencePack` + `component_library.py` + `visual_system.py`.
4. Mathis review 69 doctrine_proposals → V3.3.
5. Reality Layer quand credentials disponibles, pas avant.

---

## 8. Pour aller plus loin

- **Vision produit complète** : Notion `Le Guide Expliqué Simplement`
- **Plan d'action ordonné** : `.claude/docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`
- **Diagnostic forensic** : `.claude/docs/state/AUDIT_TOTAL_V26AE_2026-05-04.md`
- **Frontières produit V26.AH** : `.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md`
- **Contrat GSG canonique V27** : `.claude/docs/architecture/GSG_CANONICAL_CONTRACT_V27_2026-05-05.md`
- **Spec reconstruction GSG V27.2** : `.claude/docs/architecture/GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md`
- **Décision sauvetage V26.AH** : `.claude/docs/architecture/RESCUE_DECISION_V26AH_2026-05-04.md`
- **Tracker refonte totale** : `.claude/docs/architecture/REFONTE_TOTAL_TRACKER_2026-05-05.md`
- **Reality Layer pilote V26.AI** : `.claude/docs/architecture/REALITY_LAYER_PILOT_V26AI_2026-05-05.md`
- **Webapp V27 Command Center** : `.claude/docs/architecture/WEBAPP_V27_COMMAND_CENTER_2026-05-05.md`
- **Proposition panel V27** : `.claude/docs/architecture/PANEL_CANONIQUE_V27_PROPOSAL_2026-05-05.md`
- **Contrat panel V27 runtime** : `data/curated_clients_v27.json`
- **Reco quality audit V26.AH** : `reports/RECO_QUALITY_AUDIT_V26AH_2026-05-04.md`
- **Architecture cible Next.js+Supabase** : `architecture/GROWTHCRO_ARCHITECTURE_V1.md`

---

*README V26.AH Rescue — 2026-05-04. Précédentes versions archivées dans `_archive/`.*
