# Architecture Snapshot — Post Cleanup Epic (2026-05-11)

**État** : `main` à `d2b96f9` après merge `epic/codebase-cleanup` (65 commits livrés).
**Pour qui** : Mathis briefing alignment session avant Sprints F-L.
**But** : photo nette du tree actuel pour que Mathis puisse pointer ses inputs Codex GSG et qu'on resync la doctrine racine.

---

## 1. Couche `growthcro/` (NOUVEAU — créée par l'epic)

Package layered cible. Chaque sous-module = un concern unique. 0 file >800 LOC.

```
growthcro/
├── config.py              ← UNIQUE point de lecture .env (Rule 2 doctrine)
├── lib/
│   └── anthropic_client.py  ← shared Anthropic SDK factory
├── capture/               ← capture orchestration (browser + cloud + DOM)
│   ├── browser.py · cloud.py · dom.py · persist.py
│   ├── orchestrator.py    ← retry_with_fallback, batch
│   ├── scorer.py · signals.py  ← extract 150+ data points
│   └── cli.py
├── perception/            ← DOM → 9 cluster roles (HERO/NAV/PRICING/FAQ/...)
│   ├── heuristics.py · vision.py · intent.py · persist.py · cli.py
├── scoring/
│   ├── pillars.py         ← shared dispatcher (filter+weight+cap+verdict)
│   ├── ux.py              ← bloc 3 UX scorers (ux_01..ux_08)
│   ├── persist.py · cli.py
│   └── specific/          ← pageType-unique criteria
│       ├── listicle.py · product.py · sales.py · home_leadgen.py
├── recos/                 ← reco enrichment (single canonical)
│   ├── schema.py · prompts.py · client.py · orchestrator.py · cli.py
├── research/              ← site-wide intel (orthogonal to per-page)
│   ├── discovery.py · content.py · brand_identity.py · cli.py
├── gsg_lp/                ← gsg_generate_lp.py split
│   ├── data_loaders.py · brand_blocks.py · mega_prompt_builder.py
│   ├── repair_loop.py · lp_orchestrator.py
├── api/                   ← FastAPI server (was api_server.py at root)
│   └── server.py
└── cli/                   ← add_client / capture_full / enrich_client (was root)
    ├── add_client.py · capture_full.py · enrich_client.py
```

**Entrypoints canoniques** :
- `python -m growthcro.api.server`
- `python -m growthcro.cli.{add_client,capture_full,enrich_client}`
- `python -m growthcro.capture.{cli,scorer}`
- `python -m growthcro.perception.cli`
- `python -m growthcro.scoring.cli`
- `python -m growthcro.recos.cli {prepare,enrich}`
- `python -m growthcro.research.cli`

---

## 2. Couche `moteur_gsg/` (réorganisé par l'epic)

GSG canonical V27.2-G (premium visual layer) sur base V27.2-F (structured route selector). core/ découpé en concerns + mode_1/ devenu sub-package.

```
moteur_gsg/
├── __init__.py
├── core/
│   ├── intake_wizard.py           ← raw request → BriefV2
│   ├── brief_v2.py · brief_v2_prefiller.py · brief_v2_validator.py
│   ├── brief_v15_builder.py
│   ├── context_pack.py            ← GenerationContextPack
│   ├── doctrine_planner.py        ← DoctrineCreationContract
│   ├── visual_intelligence.py     ← VisualIntelligencePack
│   ├── visual_system.py
│   ├── creative_route_selector.py ← Golden/Creative route (V27.2-F, base)
│   ├── visual_system.py           ← V27.2-G premium visual layer
│   ├── component_library.py
│   ├── pattern_library.py
│   ├── design_tokens.py · design_grammar_loader.py
│   ├── brand_intelligence.py
│   ├── canonical_registry.py
│   ├── copy_writer.py
│   ├── planner.py
│   ├── pipeline_single_pass.py    ← call_sonnet + call_sonnet_multimodal
│   ├── pipeline_sequential.py
│   ├── minimal_guards.py
│   ├── legacy_lab_adapters.py
│   ├── prompt_assembly.py         ← (note : nom dupé avec mode_1/prompt_assembly.py — kept-by-design AD-1)
│   ├── html_escaper.py · asset_resolver.py · fact_assembler.py
│   ├── hero_renderer.py · component_renderer.py · section_renderer.py
│   ├── page_renderer_orchestrator.py   ← dispatch listicle vs component
│   └── css/                       ← 3-file split (≤400 LOC chacun)
│       ├── base.py · components.py · responsive.py
└── modes/
    ├── __init__.py
    ├── mode_1/                    ← sub-package (split de mode_1_persona_narrator.py 1448 LOC)
    │   ├── prompt_assembly.py     ← contient `assert len(prompt) <= 8192` V26.AF GUARD
    │   ├── prompt_blocks.py       ← LITE et FULL variants (FULL = quarantine inert)
    │   ├── api_call.py            ← re-export pipeline_single_pass (à migrer vers lib.anthropic_client)
    │   ├── output_parsing.py · runtime_fixes.py
    │   ├── visual_gates.py · vision_selection.py · philosophy_bridge.py
    │   └── orchestrator.py        ← run_mode_1_persona_narrator
    ├── mode_2_replace.py
    ├── mode_3_extend.py
    ├── mode_4_elevate.py
    ├── mode_5_genesis.py
    └── mode_1_complete.py
```

**État issue #13 (in progress)** : refactor `mode_1/prompt_assembly.py` → `(system_messages cached, user_turns_seq dialogue)` + delete `prompt_mode='full'` path. Sur `task/13-prompt-arch`.

---

## 3. Couche `skills/` (PARTIELLEMENT touché par l'epic)

L'epic n'a PAS splitté les fichiers `skills/`. 5 god files restent en **KNOWN_DEBT** trackés par le linter :

| Fichier | LOC | Statut |
|---|---|---|
| `skills/site-capture/scripts/discover_pages_v25.py` | 970 | DEBT |
| `skills/site-capture/scripts/project_snapshot.py` | 895 | DEBT |
| `skills/site-capture/scripts/playwright_capture_v2.py` | 818 | DEBT |
| `skills/site-capture/scripts/build_growth_audit_data.py` | 803 | DEBT |
| `skills/growth-site-generator/scripts/aura_compute.py` | 816 | DEBT |

**Autres `skills/` survivants** : ~40 fichiers actifs (brand_dna_extractor, capture_site, evidence_ledger, golden_bridge, intent_detector_v13, learning_layer_v29, multi_judge, etc.) → restent dans `skills/site-capture/scripts/` et `skills/growth-site-generator/scripts/` non-touchés.

**Local junk** : `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` (gitignored, ~10 .py untracked dans le repo) — linter flag (Rule 3), à `rm -rf` quand tu veux.

---

## 4. Couche `moteur_multi_judge/` (NON touché)

```
moteur_multi_judge/
├── orchestrator.py           ← run_multi_judge 70/30 doctrine/humanlike
└── judges/
    └── doctrine_judge.py     ← V3.2.1 parallélisé par pilier
```

---

## 5. Couche racine (NETTOYÉE)

```
.  (root)
├── README.md                 ← V27.2-G
├── CLAUDE.md → .claude/CLAUDE.md   (symlink)
├── AGENTS.md → .claude/CLAUDE.md   (symlink)
├── state.py                  ← SEUL .py racine
├── Dockerfile                ← updated `python -m growthcro.api.server`
├── docker-compose.yml
├── package.json · package-lock.json
├── requirements.txt
├── .env.example
├── .gitignore
├── CAPABILITIES_REGISTRY.json   ← auto-généré
├── scripts/
│   ├── audit_capabilities.py       ← anti-oubli (V26.AC)
│   ├── lint_code_hygiene.py        ← NOUVEAU (#12) — doctrine guard
│   ├── parity_check.sh             ← byte-baseline weglot (108 files)
│   ├── agent_smoke_test.sh         ← NOUVEAU (#10) — 5/5 agents
│   ├── doctrine.py · client_context.py
│   ├── reco_enricher_v13.py · reco_enricher_v13_api.py   ← (à vérifier post-cleanup)
│   ├── enrich_v143_public.py → archived in _archive/
│   ├── run_gsg_full_pipeline.py
│   └── check_gsg_*.py
├── playbook/                 ← Doctrine V3.2.1 (intact)
├── data/                     ← captures + golden + briefs + learning
├── SCHEMA/                   ← 7 schemas validate_all
├── deliverables/             ← webapp V26 + V27 + clients/japhy/gsg_demo
└── _archive/                 ← TOUT l'historique
    ├── parity_baselines/weglot/  ← 108 files baseline (regen 2026-05-11)
    └── scripts/2026-05-10/   ← batch_enrich.py + run_full_pipeline.sh archived par #10
```

---

## 6. Doctrine racine (intact, à valider post-cleanup)

```
.claude/
├── CLAUDE.md                ← init obligatoire (10 étapes maintenant, doctrine code ajoutée step #10)
├── README.md                ← index hiérarchie
├── settings.json
├── agents/                  ← 5 sub-agents canonicalisés par #10
│   ├── capabilities-keeper.md · capture-worker.md
│   ├── doctrine-keeper.md · reco-enricher.md · scorer.md
│   └── (chacun a section "Refus" pointant docs/doctrine/CODE_DOCTRINE.md)
├── commands/                ← /audit-client /score-page /full-audit ...
├── docs/
│   ├── doctrine/
│   │   └── CODE_DOCTRINE.md      ← NOUVEAU (#12) — 87 LOC
│   ├── state/
│   │   ├── AUDIT_TOTAL_V26AE_2026-05-04.md
│   │   ├── STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md    ← Sprints F-L roadmap
│   │   ├── CAPABILITIES_SUMMARY.md      ← orphans=0 ✓
│   │   ├── ORPHAN_DISPOSITION_2026-05-10.md   ← (#10) full disposition
│   │   └── ARCHITECTURE_SNAPSHOT_POST_CLEANUP_2026-05-11.md  ← (CE FICHIER)
│   ├── reference/
│   │   ├── GROWTHCRO_MANIFEST.md    ← §12 changelog updated (#11)
│   │   ├── DESIGN_DOC_V26_AA.md
│   │   ├── FRAMEWORK_CADRAGE_GSG_V26AC.md
│   │   └── RUNBOOK.md · HANDOFF · START_HERE
│   └── architecture/
│       ├── GROWTHCRO_ARCHITECTURE_V1.md          ← cible Next.js+Supabase
│       ├── GSG_CANONICAL_CONTRACT_V27_2026-05-05.md
│       ├── GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md
│       └── PRODUCT_BOUNDARIES_V26AH.md · ...
├── memory/                  ← MEMORY.md + project memories
├── epics/codebase-cleanup/  ← l'epic finie (11/11 tasks closed, 100%)
│   ├── epic.md · github-mapping.md
│   ├── 2.md ... 12.md      ← all status: closed
│   ├── split-maps/          ← split maps #5/#6/#7/#8 locked
│   ├── follow-ups/issue-13-prompt-architecture.md   ← spec posted as GH #13
│   └── updates/{2-12}/stream-A.md
└── prds/codebase-cleanup.md
```

---

## 7. Doctrine code (NOUVEAU — anti-régression contract)

`scripts/lint_code_hygiene.py` runs en 0.6s. Wired dans `state.py` qui affiche `CODE HYGIENE — fail:N warn:M info:K debt:D`.

**Hard rules (FAIL) :**
1. No file >800 LOC in active paths (KNOWN_DEBT bypass tracked)
2. No `os.environ`/`os.getenv` outside `growthcro/config.py`
3. No archive folder name (`_archive*`/`_obsolete*`/`*deprecated*`/`*backup*`) inside active path
4. No basename duplicate excl. (`__init__.py`, `cli.py`, AD-1 canonicals `base/orchestrator/persist/prompt_assembly`)

**Soft rules (WARN) :** mixed-concern heuristic via prefix entropy + concern-bundle imports + disjoint top-level classes.

**INFO :** all files >300 LOC + `+no-print-in-pipelines` (auto-update demo).

**État actuel main** : `fail:1 warn:10 info:82 debt:5 +31 print-in-pipeline INFOs`. Le seul FAIL = folder `_archive_deprecated_2026-04-19/` (local junk).

---

## 8. Ce qui doit clarifier avant Sprints F-L

Sprints F-L (`STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`) sont la roadmap GSG stratégique. Mais entre cette roadmap (4 mai) et maintenant :

- L'epic codebase-cleanup (11 issues, 65 commits) a refactor toute la base — la roadmap parle des chemins LEGACY (`skills/site-capture/scripts/perception_v13.py` etc.) qui n'existent plus.
- Mathis a bossé 10 jours sur Codex sur une autre branche → des avancées GSG mergées ailleurs, à mapper.
- #13 (prompt arch refactor) va modifier `mode_1/prompt_assembly.py` + supprimer `prompt_mode='full'` — change la surface GSG.
- 56 clients V27 roulés, 91% Brand DNA+Design Grammar coverage, 51/56 — la fleet est rich.

**Questions ouvertes à clarifier en session alignment** :
1. Quel est l'état GSG REL post-Codex 10 jours ? (Mathis brief)
2. Le `creative_route_selector.py` V27.2-F est-il toujours la vérité ou un nouveau split est arrivé ? **→ RÉSOLU 2026-05-11 alignment Codex : V27.2-F base toujours valide + V27.2-G premium visual layer ajouté dans `visual_system.py`.**
3. Les "69 doctrine proposals" en attente (V29 audit-based) → review en Sprint K, mais quel statut maintenant ?
4. Les modes 2-3-4-5 — bouger pendant Codex 10j ou intacts ?
5. Webapp V27 Command Center vs migration Next.js — Mathis a tranché "V27 HTML incremental" pour MVP. Mais lecture growth_audit_data.js 11.7MB doit être refresh post-cleanup (les paths ont changé ?).
6. Sprints F-L → certains sprints sont OBSOLÈTES (e.g. F "plug existing" partiellement fait par #10). À re-prioriser.

---

## 9. Métriques fleet (snapshot 2026-05-11)

- **56 clients runtime** V27 rôlés
- **185 pages** auditées
- **3,045 recos** LP-level webapp + **170 step-level**
- **8,347 evidence items**
- **51/56 Brand DNA + Design Grammar** (91%)
- **11 panes webapp**
- **doctrine V3.2.1** : 54 critères + 6 killer_rules
- **69 doctrine_proposals** V29 audit-based en attente review → V3.3
- **Orphans : 0** ✓

---

**Pour la session alignment** : Mathis briefs ses inputs Codex GSG, je re-map les zones touchées, on identifie quels Sprints F-L sont encore pertinents post-cleanup, et on attaque la séquence : finir #13 → alignment → Sprints F-L (filtré) → Webapp V27 HTML.
