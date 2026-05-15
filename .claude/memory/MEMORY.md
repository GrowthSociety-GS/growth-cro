# MEMORY.md — Index de la mémoire projet GrowthCRO

**Convention** : ce fichier liste les mémoires et leur portée, sans dupliquer leur contenu. Pour une info précise, référer au fichier source listé ici.

Mise à jour : 2026-05-07 (post V27.2-F — GSG route selector Golden/Creative structuré).

**Pivot empirique majeur** : test pipeline V26.AF (workflow conversationnel + doctrine V3.2.1 + multi-judge) vs Sonnet vanilla chat sans pipeline. Verdict Mathis : pipeline V26.AF NÉGATIF visuellement (anti-AI-slop = anti-design), vanilla "BCP mieux" mais reste IA-like, copy reste IA-like (manque vraies images + anecdotes humaines). Conclusion : **Linear-grade ≠ atteignable par Sonnet single-shot** peu importe le pipeline.

Notes empiriques V26.AF :
- Doctrine V3.2.1 raw : 61% / capped 50% (2 killers : coh_01 + ux_04)
- Humanlike : 75% (bond +14% vs V26.Z BESTOF 66/80) — le copy doctrine + persona narrator a progressé
- Final 70/30 : 57.5% (Moyen)
- 3 options stratégiques en attente Mathis : (1) accept 80% Claude + 20% polish humain, (2) PIVOT focus AUDIT engine + webapp Next.js+Supabase+Vercel = vraie IP, (3) ChatGPT+GPT-image multi-modal effort 2 mois.

**Recommandation honnête Claude** : Option 2 — l'IP différenciante = AUDIT + closed-loop (Reality + Lifecycle + Learning + Multi-judge), PAS la génération LP automatique.

**Mise à jour post-rescue V27.2-F** : Mathis a validé de reprendre le GSG sans repartir dans les mega-prompts. Le moteur canonique est `skills/gsg` + `moteur_gsg`. Mode 1 contrôlé construit maintenant `GenerationContextPack`, `DoctrineCreationContract`, `VisualIntelligencePack`, `CreativeRouteContract`, `component_library.py`, puis `visual_system.py`. Le vrai run Weglot listicle V27.2-D a généré avec Sonnet sous budget (`7867` chars), réparé déterministiquement un chiffre non sourcé, passé QA Playwright desktop/mobile, puis obtenu `70.9%` Bon au multi-judge (`67.5%` doctrine, `78.8%` humanlike, 0 killer, impl OK). V27.2-E ajoute le point d'entrée produit : `intake_wizard.py` parse une demande brute, résout client/page type/langue/mode, préremplit BriefV2 via router racine, liste les questions manquantes, puis `run_gsg_full_pipeline.py --request` peut générer par le chemin canonique. V27.2-F ajoute `creative_route_selector.py` : AURA + VisualIntelligencePack + Golden Bridge deviennent un `CreativeRouteContract` structuré, sans LLM ni prompt dumping, et `visual_system.py` applique des overrides de route au renderer. Ne pas survendre : c'est techniquement sain, mais pas encore stratosphérique. Prochaine étape = assets/motion/modules premium + second vrai cas hors SaaS listicle.

---

## Fichiers racine projet (lecture obligatoire en début de session)

| Fichier | Portée | Quand le lire |
|---|---|---|
| `CLAUDE.md` | Entrypoint + ordre d'init en 5 étapes | Tout début de session |
| `GROWTHCRO_MANIFEST.md` | Source de vérité architecturale (changelog §12 horodaté) | À chaque session, si doute architecture |
| `DESIGN_DOC_V26_AA.md` | Architecture cible V26.AA (5 modes + multi-judge unifié) | Avant tout code Sprint 4+ |
| `WAKE_UP_NOTE_2026-05-03_V26AA_PIVOT.md` | État final session 2026-05-03 — pivot architectural doctrine racine | Premier wake-up V26.AA |
| `WAKE_UP_NOTE_2026-05-02_V26Z_SHIPPED.md` | Snapshot pré-pivot (V26.Z final shipped) | Référence forensic du pivot |
| `TODO_2026-04-30_FULL.md` | TODOs ouverts hiérarchisés P0-P2 | Avant code |
| `RUNBOOK.md` | Procédures opérationnelles (audit, GSG, learning) | Occasionnel |
| `START_HERE_NEW_SESSION.md` | TL;DR quick-start | Premier message |
| `HANDOFF_TO_CLAUDE_CODE.md` | Setup Claude Code | Référence |

## Fichiers memory/ (référencés par CLAUDE.md)

| Fichier | Portée | Quand le lire |
|---|---|---|
| **`FINAL_ACCEPTANCE_TEST_TODO.md`** | 🎯 **TEST D'ACCEPTANCE FINAL** demandé par Mathis 2026-05-15. Refaire le listicle Weglot from blank page (LP-Creator 4 phases interactives → moteur_gsg → review). À exécuter APRÈS la clôture des sprints planifiés (Sprint 19+ todo avant). | Avant chaque session post-clear + à la clôture des sprints en cours |
| **`CONTENT_INPUT_DOCTRINE.md`** | 🛑 **DOCTRINE HARD GATE** "content-input-from-blank" — Mathis 2026-05-15 a constaté que je recyclais l'angle Sprint 13 sans questionner. Désormais : avant toute Phase 1 brief, l'agent DOIT fetcher 6 catégories de sources (homepage / pricing / customers index + 2-3 case studies individuelles / about / blog index + top articles / features), synthétiser des fresh insights, et PROPOSER 3 ANGLES DISTINCTS avant pré-remplissage. À wirer dans Sprint 21+ pipeline (slash command + BriefV2 field + audit gate). | À chaque from-blank brief, tous clients, tous types LP |
| `SPRINT_LESSONS.md` | **Boucle d'apprentissage** — règles distillées sprint par sprint (Sprint 13/14/15…). Format `règle \| déclencheur \| conséquence`. À mettre à jour à la clôture de chaque sprint (1-3 règles max). | Avant ouverture d'un nouveau sprint + à la clôture |
| `HISTORY.md` | Journal chronologique phases 1-18 | Skim dernier tiers seulement (forensic) |
| `SPECS.md` | Specs figées modules (capture, perception, scoring, reco) | Avant modif d'un module |

## Fichiers de projet (one-offs, vivants)

| Fichier | Portée | Status |
|---|---|---|
| `project_growthcro_v152_semantic_scorer_plan.md` | Design V15.2 semantic scorer (Haiku 4.5, 18 critères) | **Actif** (base évolutions semantic) |
| `project_growthcro_golden_dataset_plan.md` | Plan constitution golden dataset | **Actif** (référence pour ajouter golden) |
| `project_growthcro_v26_aa.md` | **V26.AA pivot architectural 2026-05-03 — doctrine V3.2 racine partagée. Sprint 1 (doctrine.py) + Sprint 2 (doctrine_judge.py) + Sprint 2.5 (calibration V3.2.1) + Sprint 3 (moteur_gsg/ Mode 1 COMPLETE 80.5% Excellent Weglot) shippés. Cleanup V26.AA Phase A+B 2026-05-04 : ~120 fichiers archivés vers `_archive/`, racine propre, .gitignore renforcé.** | **Actif (référence architecture courante)** |
| `architecture/GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md` | **GSG V27.2 reconstruction — context/doctrine/visual contracts, component library 7 page types, visual system renderer, intake wizard V27.2-E, route selector Golden/Creative V27.2-F.** | **Actif (référence GSG courante)** |

## Fichiers archivés (memory/_archive_legacy_projects_2026-05-04/)

| Fichier | Raison archive |
|---|---|
| `project_growthcro_cloud_native_pivot_20260417.md` | Pivot Bright Data/Apify Browser → local Playwright conclu |
| `project_growthcro_golden_audit_20260417.md` | Audit 75 golden pages conclu 2026-04-17 |
| `project_growthcro_v26_z.md` | Superseded par V26.AA |

## Snapshots (`memory/snapshots/`)

Garde **uniquement** :
- `2026-04-19_P6_P4_complete.json` — État post-P6 (dashboard V17.2.0 final) + post-P4 (disk cleanup). **Baseline "où en est la boîte aujourd'hui".**

16 snapshots pré-V15 (2026-04-13/14) déplacés vers `_archive/memory_snapshots_pre_v15/` lors du cleanup V26.AA Phase A3 (2026-05-04). Utilité forensic uniquement.

## Règles de consolidation

- **Ne PAS dupliquer** entre HISTORY ↔ MANIFEST ↔ wake-ups. Manifest = architecture courante. HISTORY = comment on y est arrivé. Wake-up = plan du jour.
- **Quand une phase se termine**, appender un paragraphe à HISTORY (pas un nouveau fichier).
- **Un nouveau project_*.md** uniquement pour un gros chantier en cours (> 1 session). Archiver dans `_archive/memory_legacy_projects/` quand terminé.
- **Skill `consolidate-memory`** existe pour passe nettoyage périodique.

## Où se trouve la vérité

Si une info diverge entre manifest / memory / wake-up-note, l'ordre de priorité est :

1. **`state.py` output** → vérité disque factuelle (nombre de fichiers, versions playbooks, dates)
2. **`GROWTHCRO_MANIFEST.md`** → vérité architecturale à jour (changelog §12)
3. **`memory/HISTORY.md`** → contexte narratif
4. **Wake-up notes** → plan du jour (potentiellement périmé après quelques heures)

## Architecture racine V26.AA (post Sprints A+B+C 2026-05-04)

```
GrowthCRO/
├── CLAUDE.md, GROWTHCRO_MANIFEST.md, README.md       [entrypoints]
├── DESIGN_DOC_V26_AA.md                              [architecture cible 5 modes]
├── WAKE_UP_NOTE_2026-05-04_V26AA_SPRINTS_ABC.md      [current — fin Sprints A+B+C]
├── WAKE_UP_NOTE_2026-05-{02,03}*.md                  [snapshots pré-pivot + pivot]
├── TODO_2026-05-04_V26AA_POST_SPRINTS.md             [refresh post-A+B+C]
├── RUNBOOK.md, HANDOFF_TO_CLAUDE_CODE.md, START_HERE_NEW_SESSION.md
│
├── moteur_gsg/                                        [V26.AA — 5 modes registrés]
│   ├── orchestrator.py (generate_lp 5 modes)
│   ├── core/
│   │   ├── brand_intelligence.py (V29 + diff E1)
│   │   ├── prompt_assembly.py (≤12K chars hard limit)
│   │   ├── pipeline_single_pass.py
│   │   ├── design_grammar_loader.py [Sprint B branché OPT-IN]
│   │   └── brief_v15_builder.py [Sprint B skeleton]
│   └── modes/
│       ├── mode_1_complete.py [Sprint 3 SHIPPED — Weglot 80.5%]
│       ├── mode_2_replace.py  [Sprint C SHIPPED — Weglot home +17.5pp]
│       ├── mode_3_extend.py   [Sprint C skeleton]
│       ├── mode_4_elevate.py  [Sprint C skeleton]
│       └── mode_5_genesis.py  [Sprint C skeleton]
│
├── moteur_multi_judge/                                [V26.AA Sprint 2 — doctrine_judge V3.2.1]
│   ├── orchestrator.py (run_multi_judge 70/30)
│   └── judges/doctrine_judge.py
│
├── scripts/
│   ├── doctrine.py (loader racine V3.2.1 + alias lp_listicle→listicle)
│   └── _test_*.py (test runners)
│
├── skills/                                            [10 skills V26.AA + roadmap V27]
│   ├── site-capture/                                  (Audit Engine V26 + learning_layer_v29 ⭐ Sprint B)
│   ├── growth-site-generator/                         (V26.Z legacy gardé)
│   ├── cro-auditor/ [REBUMPED V26.AA Sprint A]
│   ├── gsg/ [REBUMPED V26.AA 5 modes Sprint A]
│   ├── client-context-manager/ [REBUMPED V26.AA Sprint A]
│   ├── webapp-publisher/ [NEW Sprint A]
│   ├── mode-1-launcher/ [NEW Sprint A]
│   ├── audit-bridge-to-gsg/ [NEW Sprint A]
│   ├── cro-library/ [PROMU _roadmap_v27 → actif Sprint C]
│   └── _roadmap_v27/                                  (3 vision skills isolés : notion-sync, connections-manager, dashboard-engine)
│
├── playbook/                                          [Doctrine V3.2.1 racine — 25 fichiers]
├── data/                                              [56 clients curatés V26 + cycle apprenant]
│   ├── curated_clients_v26.json [Sprint A — base officielle 56 clients]
│   ├── learning/ ⭐ Sprint B — cycle apprenant ACTIVÉ
│   │   ├── audit_based_stats.json (329 segments criterion×business)
│   │   ├── audit_based_proposals/ (69 doctrine_proposals générés)
│   │   └── audit_based_summary.md (Mathis review)
│   └── _briefs_v15/ [Sprint C — Briefs V15 produits par builder]
├── deliverables/, memory/, SCHEMA/, .claude/
│
└── _archive/                                          [legacy V13-V26X archivé, ~150 fichiers]
```

## Sprints E+F+G V26.AC — résultats clés (2026-05-04, post audit anti-oubli)

Mathis : "j'en ai marre que t'oublies tout, des semaines avec des LPs moyennes alors que AURA + perception + screenshots étaient sur disque". Réponse en 3 sprints :

### Sprint E — SYSTÈME ANTI-OUBLI ⭐
- `scripts/audit_capabilities.py` (350 LoC, auto-discovery 161 .py)
- `CAPABILITIES_REGISTRY.json` + `CAPABILITIES_SUMMARY.md` (auto-generated)
- `.claude/agents/capabilities-keeper.md` (sub-agent enforcer "use existing if available")
- `CLAUDE.md` Section "Pré-requis ANTI-OUBLI" obligatoire avant tout sprint code

Inventaire choquant : **102 fichiers .py dans `skills/site-capture/scripts/`, 86 ORPHELINS (84%)**. ~2 mois de dev cumulé jamais branché.

### Sprint F — ROUTER RACINE + multimodal + post-gates ⭐
Réponse insight Mathis : "l'accès à toutes les données se faisait à la racine, distribué intelligemment Audit/GSG selon qui appelle".

- `scripts/client_context.py` (320 LoC) — ROUTER RACINE qui charge automatiquement TOUS les artefacts client (brand_dna + AURA + screenshots + perception + recos + v143 + reality_layer + design_grammar + intent + evidence). Audit + GSG + Multi-judge consomment via `load_client_context(client, page_type)`.
- `moteur_gsg/core/pipeline_single_pass.py` : `call_sonnet_multimodal()` Anthropic vision API
- `moteur_gsg/modes/mode_1_persona_narrator.py` refactor : router + multimodal vision input + AURA tokens injectés + post-gates (AURA font blacklist + design_grammar forbidden) + HARD CONSTRAINTS (forced_language override vision bias)

### Sprint G — CSS pré-fabriqué + AURA AI-slop substitution ⭐
Audit honnête révèle : `aura_tokens.json` contient `css_custom_properties` ET `data/captures/<c>/design_grammar/tokens.css` existe (1785 chars CSS V30). On reformulait des hex en TEXTE au lieu d'injecter le CSS direct.

- `_format_aura_tokens_block()` refactor : injecte CSS DIRECT prêt à coller dans `<style>` HTML + Sonnet utilise `var(--name)` partout
- `_load_tokens_css(client)` : charge tokens.css design_grammar V30
- `_substitute_ai_slop_in_aura()` : si AURA.typography.body est Inter/Roboto/etc → SUBSTITUE par DM Sans AVANT injection prompt (Sonnet ne voit jamais "Inter" comme suggestion)
- AI_SLOP_FONTS + NON_AI_SLOP_BODY_ALTERNATIVES constants

### Test V26.AC v4 — Weglot listicle FR (résultat final)

| Critère | V26.AC v4 |
|---|---|
| Post-gates AURA + design_grammar | ✅ **0 violation** |
| Ppneuemontreal présent (display) | ✅ |
| DM Sans présent (body — substitution Inter) | ✅ |
| `var(--...)` CSS variables | **109 occurrences** ⭐ |
| Langue FR forcée | ✅ 7/8 |
| Couleurs Weglot brand | ✅ |
| 10 H2 listicle + 1 CTA | ✅ |
| Multimodal vision (Sonnet voit Weglot) | ✅ 2 screenshots fold |
| Coût | $0.141 |
| Wall | 133s |

Progression Weglot listicle : v1 0% CSS vars / v3 81 vars / v4 **109 vars** + Inter remplacé par DM Sans.

### Capacités enfin BRANCHÉES (orphelins HIGH résolus)

- ✅ `aura_compute` outputs (`data/_aura_<c>.json` + `css_custom_properties` + tokens.css)
- ✅ Screenshots desktop/mobile multimodal (Sonnet vision)
- ✅ design_grammar V30 (forbidden patterns post-gate + tokens.css)
- ✅ ROUTER RACINE distribue tous les artefacts
- ⚠️ Encore HIGH orphelins (faux positifs du registry — consommés via output JSON pas import direct) :
  - vision_spatial.py, perception_v13.py, recos_v13_final.json, evidence_ledger
  - À améliorer Sprint H : registry détecte consommation indirecte

## Sprints A+B+C V26.AA — résultats clés (2026-05-04)

### Wins ⭐
1. **Cycle apprenant ACTIVÉ** : `learning_layer_v29_audit_based.py` génère 69 doctrine_proposals depuis 56 curatés
2. **Skills écosystème aligné** : 3 rebumpés (cro-auditor, gsg, client-context-manager) + 3 nouveaux (webapp-publisher, mode-1-launcher, audit-bridge-to-gsg)
3. **5 modes GSG registrés** : Mode 1 SHIPPED (Weglot 80.5%), Mode 2 SHIPPED (+17.5pp), Modes 3-5 skeletons
4. **Bug critique fixé** : `score_hero.py` pointait sur `bloc_1_hero_DRAFT.json` (v3.0.0) au lieu de v3.2.1
5. **Base 56 clients V26** sauvée comme référence officielle (vs 105 brutes contenant audits cassés)

### Leçons empiriques ⚠️
- **Anti-pattern mega-prompt CONFIRMÉ** : design_grammar+creative_director branchés au prompt = -28pts régression. Doctrine "concision > exhaustivité" prouvée empiriquement.
- **Variance Sonnet T=0.7** : ±5-10pts entre runs → besoin best_of_N pour stats robustes
- **Mode 2 single_pass +17pp** mais pas Excellent (cible 85%) — pipeline_sequential_4_stages dédié nécessaire
