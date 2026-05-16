---
name: growthcro-stratosphere-p0
description: Muscler la chaîne de vérité bloquante de GrowthCRO (Verdict Gate, Evidence Ledger gate, Opportunity Layer, Skill Registry honnête, 3 skills custom, SSRF fix, doc reconciliation) après audit Pack GPT + Skills Addendum.
status: backlog
created: 2026-05-16T12:14:34Z
---

# PRD: growthcro-stratosphere-p0

> Source de vérité primaire : [`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`](../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md) — 11 sections + 4 annexes, audit read-only validé Mathis 2026-05-16.
> Ce PRD résume sans dupliquer. En cas de conflit : le dossier de décision gagne.

## Executive Summary

GrowthCRO actuel (V26.AI, 56 clients runtime, GSG canonique V27.2-F/G, Sprint 21 composite 88.6%) a **un socle métier dramatiquement plus mature** que la cible MVP du pack GPT externe. Mais il manque **la chaîne de vérité bloquante** qui transforme un "GSG bien noté" en un "GSG shippable ou pas, pas de zone grise".

Les 4 audits Explore parallèles (skills runtime / gates qualité / sécurité SSRF+secrets / contradictions docs↔code) convergent sur un diagnostic unique : **GrowthCRO a une infrastructure de gates contractuels solide (7 check_gsg_*.py + SCHEMA/validate_all.py bloquants) mais 9 audits critiques (impeccable_qa, multi-judge doctrine killer_rules, multi-judge implementation, cro_methodology_audit, frontend_design, brand_guidelines, emil_design_eng, axe-core, lighthouse) sont juste informatifs**. Un `passed=False` se solde par un `logger.info`, jamais par un `raise` ou un cap du grade composite.

P0 = combler ce gap : **Verdict Gate + Evidence & Claims Ledger gate + Opportunity Layer + Skill Registry honnête + 3 skills custom + checklist sécurité + fix SSRF crawler + archive doc obsolète**. 12 issues atomiques, ~30 fichiers, ~2000-3000 LOC, dépendances explicites, exécution séquentielle ou parallèle selon waves.

## Problem Statement

**Pourquoi maintenant ?**

1. **Le pack GPT externe (delivery_pack_v2)** propose une refonte feuille blanche qui serait une régression (MVP single-page audit vs notre 56 clients × 185 pages × 3045 recos déjà en prod). Importer la discipline méthodologique sans importer le scope reset.

2. **L'addendum Skills (skills_addendum_pack)** révèle un angle mort : sur 17 skills externes installés via `skills-lock.json`, **14 sont dormants** (Superpowers obra jamais invoqués, gstack install échouée). Sur les 3 "actifs" (impeccable, cro-methodology, emil-design-eng), aucun n'est invoqué via le Skill tool Anthropic — ce sont des **heuristiques Python locales** (`run_impeccable_qa()`, `run_cro_methodology_audit()`, `run_emil_design_eng_audit()`). On a parlé de "skills wired at runtime" en pratique on a du Python local. Il faut soit convertir, soit assumer.

3. **L'audit révèle une faille SSRF critique** : `growthcro/capture/orchestrator.py:68` `page.goto(url)` accepte n'importe quelle URL utilisateur (`localhost`, `169.254.169.254` AWS metadata, `file://`, IPs privées). Le repo est PUBLIC sur GitHub. Sans validation, c'est un vecteur d'attaque immédiat dès qu'un consultant agence utilise la pipeline sur un site client.

4. **Une contradiction docs↔code crée du drift Claude** : `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (2026-05-11) décrit microfrontends V28, alors que `PRODUCT_BOUNDARIES_V26AH §3-bis` (D1.A 2026-05-14) verrouille single shell. Vérité disque = single shell. Sans archive, chaque nouvelle session Claude peut hallucinerle V1 obsolète.

5. **Le multi-judge produit une fausse confiance** : `moteur_multi_judge/orchestrator.py:96-107` calcule `verdict_tier` (🚀 Stratosphérique ≥92%) **sans jamais consulter** `impeccable.passed` ni `killer_rules_violated`. Un GSG peut être noté 92% Exceptionnel alors qu'un gate critique a échoué.

## User Stories

### Story 1 — Mathis (operator GrowthCRO)
**En tant que** propriétaire de l'agence Growth Society opérant la pipeline GrowthCRO sur 56 clients,
**je veux** qu'un GSG noté ≥85% mais avec un gate critique en FAIL soit marqué `🔴 Non shippable` automatiquement,
**afin que** je n'envoie jamais un livrable à un client avec un claim non sourcé ou un killer rule violé.
**Acceptance** : fixture test avec `killer_rules_violated=True` + `composite=92%` → `verdict_tier = "🔴 Non shippable"`.

### Story 2 — Claude Code session (agent dev)
**En tant que** session Claude Code travaillant sur un sprint GSG/audit,
**je veux** un Skill Registry honnête qui distingue `installed_external` / `installed_custom` / `runtime_heuristic_python` / `subagent` / `mcp_server`,
**afin que** je ne prétende plus qu'`impeccable` est un "skill wired" alors que c'est `run_impeccable_qa()` Python.
**Acceptance** : `SKILLS_REGISTRY_GOVERNANCE.json` listant les 17 skills externes + 10 skills projet + 5 agents avec `type` + `invocation_proof` (grep result) + `security` audit.

### Story 3 — Sécurité (repo public attack surface)
**En tant que** propriétaire d'un repo GrowthCRO PUBLIC,
**je veux** que le crawler Playwright refuse les URLs vers IPs privées, localhost, AWS metadata, ou schemes `file://`,
**afin qu'** un fork malveillant ou un PR contributor ne puisse pas scraper les services internes ou exposer des secrets via le pipeline.
**Acceptance** : `python3 -m growthcro.cli.capture_full --url "http://localhost:9000/admin"` → `URLValidationError`.

### Story 4 — Recommendations Engine (clarté audit→action)
**En tant que** consultant CRO consommant les recos générées,
**je veux** que chaque reco soit liée à une **Opportunity structurée** (avec impact × confidence × severity / effort, hypothesis, metric_to_track),
**afin que** je puisse prioriser objectivement et tester systématiquement plutôt que de subir une longue liste de recos isolées.
**Acceptance** : Weglot home génère ≥5 opportunités structurées, chaque reco a un `linked_opportunity_id`.

### Story 5 — GSG renderer (claims provenance)
**En tant que** GSG canonique produisant des LPs avec testimonials / chiffres / logos,
**je veux** qu'aucun claim rendu dans le HTML final ne puisse exister sans un `data-evidence-id` valide pointant vers `evidence_ledger.json`,
**afin que** Growth Society puisse toujours justifier auprès du client la source de chaque preuve avancée.
**Acceptance** : HTML rendu avec testimonial sans `data-evidence-id` → `ClaimsSourceGate` raise + GSG refuse de ship.

### Story 6 — Anti-drift (méthodologie d'exécution)
**En tant que** Claude Code session lançant une issue P0,
**je veux** un skill custom `growthcro-anti-drift` qui impose le format CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS,
**afin qu'**aucune session ne dérape sur du scope hors issue ou refactor sauvage.
**Acceptance** : skill invocable via Skill tool, frontmatter conforme, référencé dans CLAUDE.md "Init obligatoire".

## Functional Requirements

### FR-1 — Verdict Gate
Agréger `impeccable.passed` + `doctrine.killer_rules_violated` + `impl_penalty > 10pp` + 7 `check_gsg_*.py` exit codes dans `moteur_multi_judge/orchestrator.py`. Si **n'importe lequel** = FAIL → `final_score_pct = 0` + `verdict = "🔴 Non shippable"`. Raise dans `mode_1_complete.py` post-multi-judge si verdict bloqué.

### FR-2 — Evidence & Claims Ledger gate
- Étendre schema `evidence_ledger.json` : `source_type` strict ∈ {vision, dom, api_external, rule_deterministic}, **jamais `llm_classifier` seul**.
- Créer `moteur_gsg/core/claims_source_gate.py` (mono-concern validation) : parse HTML rendu, extract `<span class="number">` / `<li class="proof-strip">` / `<blockquote class="testimonial">` / `<img class="logo-strip">`, valide chaque claim vs `evidence_ledger.json` via `data-evidence-id` attribute. **Bloque** (`raise ClaimsSourceError`) si claim sans source.
- Wire dans `mode_1_complete.py` post-impeccable, pre-multi-judge.

### FR-3 — Opportunity Layer
- Créer `growthcro/opportunities/` package mono-concern (8 axes CODE_DOCTRINE) : `__init__.py`, `schema.py` (Pydantic v2 strict), `persist.py`, `orchestrator.py`, `cli.py`.
- Schema `Opportunity` : `id`, `criterion_ref`, `current_score`, `target_score`, `impact 1-5`, `effort 1-5`, `confidence 1-5`, `severity`, `priority_score = (impact * confidence * severity) / effort`, `hypothesis`, `recommended_action`, `metric_to_track`, `owner`, `evidence_ids[]`.
- Orchestrator : input `score_page_type.json + score_applicability_overlay.json + brief` → output `opportunities.json` (déterministe, pas d'appel LLM).
- CLI : `python -m growthcro.opportunities.cli prepare --client <slug> --page <page_type>`.
- Wire dans `growthcro/recos/orchestrator.py` : recos consomment `opportunities.json` (champ `linked_opportunity_id` sur chaque reco), pas scores bruts.

### FR-4 — Skill Registry honnête
- Créer `growthcro/SKILLS_REGISTRY_GOVERNANCE.json` (toplevel).
- Pour chaque skill (17 externes + 10 projet + 5 agents) : `id`, `type` ∈ {installed_external_active, installed_external_dormant, installed_custom, runtime_heuristic_python, subagent, mcp_server, archived}, `location`, `invocation_proof` (grep result : file:line ou "no occurrence"), `llm_cost`, `security {shell, network, env_vars, secrets, git, filesystem}`, `audit_date`.
- Créer `scripts/audit_skills_governance.py` (greppe les invocations, fail si label drift entre registry et code).

### FR-5 — 3 skills custom
- `.claude/skills/growthcro-anti-drift/SKILL.md` : impose format CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS.
- `.claude/skills/growthcro-prd-planner/SKILL.md` : transforme idée → PRD + Epic + Issues atomiques + Dependencies + Acceptance + Tests + Out-of-scope + Stop conditions (CCPM-aware).
- `.claude/skills/growthcro-status-memory/SKILL.md` : update `docs/status/PROJECT_STATUS.md` + `NEXT_ACTIONS.md` + `CHANGELOG_AI.md` + ADR-XXX selon format WHAT CHANGED / CURRENT STATE / WHAT IS MOCKED / WHAT WORKS / KNOWN RISKS / NEXT ACTIONS / DO NOT FORGET.
- Mention dans CLAUDE.md "Init obligatoire" step #13 (nouveau).

### FR-6 — Checklist sécurité skills
- Créer `.claude/docs/reference/SKILLS_SECURITY_CHECKLIST.md` (template + 17 audits rétroactifs).
- Pour chaque skill externe : auditer shell / network / .env / secrets / git / filesystem.
- Update `SKILLS_REGISTRY_GOVERNANCE.json` avec résultats.

### FR-7 — Fix SSRF crawler
- Créer `growthcro/capture/url_validator.py` (mono-concern validation).
- Validation : reject schemes ∉ {http, https}, reject IPs privées (10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12, 127.0.0.0/8, 169.254.0.0/16), reject hostnames `localhost`/`metadata`/`metadata.google.internal`, reject ports < 80 hors {80, 443, 8080, 8443}.
- Wire dans `growthcro/capture/orchestrator.py` + `growthcro/capture/cli.py` pré-`page.goto`.
- Test fixture : 10 URLs (5 valides, 5 invalides incl. AWS metadata, file://, localhost, IP privée).

### FR-8 — Réconcilier docs
- `git mv architecture/GROWTHCRO_ARCHITECTURE_V1.md _archive/architecture_pre_d1a/` avec note "superseded by PRODUCT_BOUNDARIES_V26AH §3-bis D1.A 2026-05-14".
- Update `README.md` ligne 3 : "V27 canonical (V27.2-F route selector + V27.2-G visual layer)" au lieu de "V27.2-F" seul.
- Update `README.md` ligne 22 : remplacer mention "architecture/GROWTHCRO_ARCHITECTURE_V1.md" par "PRODUCT_BOUNDARIES_V26AH.md" comme source d'architecture vivante.
- Add manifest §12 changelog entry.

## Non-Functional Requirements

- **LOC** : max 300/file source, 50/function (cf. CODE_DOCTRINE). Issue qui dépasserait → split obligatoire.
- **Hygiene** : `python3 scripts/lint_code_hygiene.py --staged` doit exit 0 avant chaque `git add`.
- **Tests** : fixture + cas limites pour chaque nouveau module (claims_source_gate, opportunity engine, url_validator, verdict gate).
- **Pydantic** : tous les schemas (Opportunity, ClaimsSourceReport, VerdictGateReport, URLValidationResult) en Pydantic v2 strict.
- **Logging** : utiliser `growthcro.observability.logger.get_logger(__name__)`, pas `print()` (CODE_DOCTRINE §LOG).
- **Provider abstraction** : pas d'appel LLM dans l'Opportunity engine (déterministe au premier shot). Si LLM enrichment plus tard → ISSUE P1 séparée.
- **Commits** : 1 commit conventional par issue (`feat(opportunities): ...`, `feat(gates): ...`, `feat(skills): ...`, `fix(security): SSRF crawler`, `docs(architecture): archive V1`).
- **Doctrine** : pas de modification de la doctrine V3.2.1 (V3.3 = Mathis review des 69 proposals — hors scope).

## Success Criteria

1. **Verdict Gate opérationnel** : fixture test avec `killer_rules_violated=True` + `composite=92%` → `verdict_tier="🔴 Non shippable"` forcé.
2. **ClaimsSourceGate opérationnel** : HTML avec testimonial sans `data-evidence-id` → `ClaimsSourceError` raise, GSG refuse de ship.
3. **Opportunity Layer wired** : Weglot home génère ≥5 opportunités structurées, recos en aval ont `linked_opportunity_id`, taille `recos_v13_final.json` inchangée (pas de régression richesse).
4. **Skill Registry validé** : `python3 scripts/audit_skills_governance.py` exit 0, registry liste 17 + 10 + 5 entrées avec invocation_proof.
5. **3 skills custom invocables** : Skill tool reconnaît `growthcro-anti-drift`, `growthcro-prd-planner`, `growthcro-status-memory`.
6. **SSRF bloqué** : `http://localhost:9000/admin` → `URLValidationError`. 10 URLs test (5 OK, 5 reject).
7. **Doc réconcilié** : `find . -name "GROWTHCRO_ARCHITECTURE_V1.md"` retourne uniquement `_archive/`. README ligne 3 et ligne 22 à jour.
8. **Smoke test Weglot end-to-end** : capture → score → opportunities → recos → GSG → claims gate → verdict gate → multi-judge — sans régression vs baseline Sprint 21 (composite 88.6%).
9. **12 issues fermées**, 12 commits séparés conventional commit, lint_code_hygiene clean partout, manifest §12 bumped.

## Constraints & Assumptions

### Constraints
- **Repo PUBLIC** : aucun secret en clair, JWT history résiduel (rotation hors P0).
- **Pas de modification doctrine V3.2.1** (V3.3 review = Mathis, hors P0).
- **Pas d'installation skill externe nouveau** (audit P0.6 = rétroactif).
- **Pas de refactor massif** (>5 fichiers hors scope d'une issue = stop).
- **Pas de microfrontends** (D1.A acté, single shell verrouillé).
- **Pas de changement stack** (Next.js 14 + Supabase + Anthropic Sonnet 4.5).
- **Hard limit** prompt persona_narrator ≤8K chars (CLAUDE.md anti-pattern #1).
- **Anti-pattern CLAUDE.md #12** : ≤8 skills/session, combos interdits respectés.

### Assumptions
- Le baseline Sprint 21 (composite 88.6%, multi-judge 85.3%, Humanlike 88.8% sur V14b Weglot from-blank) reste reproductible.
- `evidence_ledger.json` existe pour les 56 clients curatés (à vérifier en ISSUE-002 par smoke).
- Les 7 `check_gsg_*.py` existants conservent leur contrat (exit code != 0 = FAIL).
- L'historique git contient potentiellement le JWT Supabase (rotation à planifier hors P0).
- Mathis est disponible pour trancher sur stop conditions (cf. §8 dossier de décision).

## Out of Scope

- Redesign UI webapp shell (ISSUE séparée P1+).
- Nouveau mode GSG (Mode 6, ELITE, etc.) — hors P0.
- Intégrations Reality Layer (env vars manquantes, hors P0).
- Installation skill externe nouveau (audit P0.6 = rétroactif seul).
- Refactor >5 fichiers hors scope d'une issue.
- Microfrontends (D1.A acté).
- Changement de stack.
- Modification doctrine V3.2.1 → V3.3 (= Mathis review).
- Generation LLM dans Opportunity engine (déterministe au premier shot, LLM enrichment = P1).
- Multi-page bundle test multi-judge (= P1).
- True Anthropic Skill wiring de impeccable/cro-methodology/emil-design-eng (= P1, on les clarifie en runtime_heuristic_python dans le registry).
- Slash command `/lp-creator-from-blank` (= P1, candidat CLAUDE.md Sprint 22+ qui glisse).
- BriefV2 `chosen_angle` field (= P1).
- `content_angle_freshness_check` gate (= P1).
- Promotion `axe-core` / `lighthouse` en gates bloquants (= P1, mode `--ship` strict).
- Promptfoo / DeepEval evals (= P1).
- Langfuse / Sentry AI observability (= P1).
- Provider abstraction LLM (= P1).
- Reality Layer activation Kaiju (= P2).
- Learning Layer V3.3 (= P2, Mathis review).
- GEO Monitor multi-engine (= P2, OPENAI + PERPLEXITY keys).
- Experiment Engine A/B real (= P2).
- Rotation JWT Supabase + `git-filter-repo` (= hors P0, security hardening dédié).

## Dependencies

### Internal (existing in repo)
- `moteur_gsg/core/impeccable_qa.py` — fournit `run_impeccable_qa()` + `impeccable_report.passed`.
- `moteur_multi_judge/orchestrator.py:96-107` — fournit `verdict_tier` calc + `final_score_pct`.
- `moteur_multi_judge/judges/doctrine_judge.py:240` — fournit `killer_rules_violated` flag.
- `growthcro/scoring/` (score_page_type.json + score_applicability_overlay.json) — input Opportunity engine.
- `growthcro/recos/orchestrator.py` — à modifier pour consommer opportunities.json.
- `skills/site-capture/scripts/evidence_ledger.py` — schema à étendre (P0.2).
- `growthcro/capture/orchestrator.py:68` — à modifier (SSRF fix).
- `growthcro/capture/cli.py` — à modifier (SSRF fix).
- `scripts/check_gsg_*.py` (7 scripts) — fournissent exit codes pour Verdict Gate.
- `SCHEMA/validate_all.py` — fournit exit code pour Verdict Gate.
- `scripts/lint_code_hygiene.py --staged` — hygiene gate avant chaque commit.
- `CAPABILITIES_REGISTRY.json` — référence code-only, gardé tel quel.
- `.claude/CLAUDE.md` — à modifier (mention skills custom step #13 + manifest §12).
- `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 — changelog bump.
- `.claude/docs/doctrine/CODE_DOCTRINE.md` — 8 axes mono-concern respectés.

### External (read-only, no install)
- `pbakaus/impeccable` — déjà installé, clarifier statut runtime_heuristic_python.
- `wondelai/skills/cro-methodology` — idem.
- `emilkowalski/skill/emil-design-eng` — idem.
- 14 skills `obra/superpowers` dormants — décider pin vs drop dans P0.6.
- `garrytan/gstack` — install échouée, décider drop vs reinstall dans P0.6.

### GitHub
- Remote : `https://github.com/GrowthSociety-GS/growth-cro.git`.
- Issues : 1 Epic + 12 sub-issues à créer (sync séparée, validation Mathis requise).
- Labels : `epic`, `epic:growthcro-stratosphere-p0`, `feature` (epic), `task`, `epic:growthcro-stratosphere-p0` (tasks).
- Worktree : `../epic-growthcro-stratosphere-p0` à créer post-sync.

### Notion (read-only)
- *Mathis Project x GrowthCRO Web App* — vision produit canonique.
- *Le Guide Expliqué Simplement* — boucle fermée Audit→Action→Mesure→Apprentissage→Génération→Monitoring.
- Aucune modification Notion sans demande explicite Mathis.
