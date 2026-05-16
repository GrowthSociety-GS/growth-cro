# Dossier de décision — GrowthCRO × Pack GPT × Skills Addendum

**Date** : 2026-05-16
**Mode** : Audit read-only, zéro modification code, zéro installation skill
**Inputs lus** :
- `PLAN_GrowthCRO_Challenge_Codex_GPT.md` (Mathis, 2026-05-15)
- `README.md` racine (V26.AI)
- `.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md` (D1.A 2026-05-14)
- `skills-lock.json` (17 skills externes installés)
- `growthcro/architecture_webapp_agentic_growthcro.md` (l'agentic — feuille blanche, 2643 lignes)
- `growthcro/growthcro_delivery_pack_v2.zip` (CLAUDE.md template + MVP_SCOPE + 10 PRDs + 8 EPICs + 28 ISSUES)
- `growthcro/growthcro_skills_addendum_pack.zip` (`SKILLS_AND_AGENT_STACK_ADDENDUM.md`)
- `.claude/CLAUDE.md` + `.claude/docs/doctrine/CODE_DOCTRINE.md` + `.claude/docs/state/CAPABILITIES_SUMMARY.md` + `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (2026-05-11, désormais obsolète)
- 5 agents `.claude/agents/*.md`
- 4 audits Explore parallèles (skills runtime / gates qualité / sécurité / contradictions docs↔code)

**Décisions Mathis préalables** : Prompt 1 (audit read-only) → P0 du nouveau plan → 3 skills custom (anti-drift / prd-planner / status-memory)

---

## 1. Verdict brutal

**Ne pas repartir de zéro.** GrowthCRO actuel (V26.AI, 56 clients, 185 pages, GSG canonique V27.2-F/G, Sprint 21 composite 88.6%) est **substantiellement plus riche** que la cible MVP du pack GPT (single-page audit + 10 scores + 5 opps + 3 hero variants). Adopter feuille blanche serait une **régression irréversible**.

**Ne pas ignorer le pack GPT.** Il apporte une **discipline méthodologique** qui manque : PRD→Epic→Issue→Branch→PR, schemas Zod validés, anti-drift protocol formel, LOC constraints mécaniques, MockProvider first / real LLM after, distinction observed/inferred/declared/measured.

**L'addendum Skills change la doctrine d'exécution.** Il introduit la **gouvernance agentique** : *installer peu de skills externes, créer ses propres skills custom, auditer avant install, traiter les skills comme des dépendances logicielles*. Cela colle aux anti-patterns CLAUDE.md (#12 sur la cacophonie ≥8 skills).

**Le vrai problème n'est pas créatif, c'est probatoire.** Les 4 audits convergent sur le même diagnostic — GrowthCRO a une **infrastructure de gates contractuels solide** (7 check_gsg_*.py + SCHEMA/validate_all.py bloquants), mais **aucune chaîne de vérité bloquante** :

- **9 audits critiques sont juste informatifs** (impeccable_qa, multi-judge doctrine, cro_methodology_audit, frontend_design, brand_guidelines, emil_design_eng, axe-core, lighthouse, evidence_ledger). Un `passed=False` se solde par un `logger.info`, pas par un `raise` ou un cap du grade composite.
- **Aucun Verdict Gate** : `multi_judge/orchestrator.py:96-107` calcule `verdict_tier` (🚀 Stratosphérique ≥92%) **sans jamais consulter `impeccable.passed` ni `killer_rules_violated`**.
- **Pas d'Opportunity Layer** : zéro occurrence du concept dans le code. Recos sortent directement des scores.
- **Skill Registry code-only** : `CAPABILITIES_REGISTRY.json` (246 fichiers) ne distingue pas installed/custom/runtime_heuristic/subagent/MCP.
- **3 skills externes prétendument "actifs"** (impeccable, cro-methodology, emil-design-eng) sont en réalité **des heuristiques Python locales** (`run_impeccable_qa()`, `run_cro_methodology_audit()`, `run_emil_design_eng_audit()`) — **PAS** des skills invoqués via le Skill tool Anthropic. 14 autres skills installés via `skills-lock.json` sont **dormants** (jamais grep, jamais référencés).

**Verdict final** : le P0 du nouveau plan (Verdict Gate + Evidence & Claims Ledger gate + Opportunity Layer + Skill Registry honnête + 3 skills custom + checklist sécurité) est exactement le bon socle à muscler. C'est ce qui transforme un "GSG bien noté" en un "GSG vraiment shippable".

---

## 2. Ce que GrowthCRO actuel fait mieux que le pack GPT

| Capacité | GrowthCRO actuel | Pack GPT |
|---|---|---|
| **Échelle** | 56 clients runtime, 185 pages auditées, 3045 recos LP-level, 8347 evidence items | MVP single-page, 1 client mock |
| **Doctrine CRO propriétaire** | V3.2.1 : 6 piliers × 54 critères + 6 killer_rules + applicability overlay + thresholds | 20 dimensions sans pondération validée empiriquement |
| **GSG canonique** | Mode 1-5 (COMPLETE/REPLACE/EXTEND/ELEVATE/GENESIS) + intake wizard + context pack + doctrine planner + visual intelligence + creative route selector + premium visual layer V27.2-G | Generator hypothétique post-MVP |
| **Brand DNA + Design Grammar** | 51/56 fleet (91%), AURA tokens, design_tokens, brand_intelligence | "Brand Profile" abstrait |
| **Multi-judge** | doctrine + humanlike + implementation parallélisé, composite Sprint 21 = 88.6% Exceptionnel | QA Agent générique |
| **Evidence ledger existant** | `evidence_ledger.json` per page (source_type, dom_selector, bbox, screenshot_crop, model, confidence) | "Evidence" champ libre dans schéma Zod |
| **Reality Layer** (dormant) | 5 connecteurs GA4/Meta/Google/Shopify/Clarity scaffoldés | Promesse "future integrations" |
| **Learning Layer** | V29 audit-based, 69 doctrine proposals en review | "Learning engine later" |
| **Pipeline disque** | 8 stages avec persistence canonique, capture dual-viewport, perception_v13, spatial_v9, screenshots | Job queue théorique |
| **Sub-agents existants** | capabilities-keeper, doctrine-keeper, scorer, reco-enricher, capture-worker — chacun avec Refus/Refuse-to-emit attaché à CODE_DOCTRINE | 18 agents proposés mais inexistants |
| **Hygiène code** | `scripts/lint_code_hygiene.py` enforced, 8 axes mono-concern, hard rules mécaniques | LOC constraints en doctrine texte |
| **Anti-pattern memory** | 12 anti-patterns prouvés empiriquement (V26.AA -28pts, V26.AF page blanche, etc.) | Anti-patterns théoriques |
| **Notion canonical** | Mathis Project x GrowthCRO Web App + Le Guide Expliqué Simplement = source produit | (Absent) |
| **Logger structuré** | `growthcro.observability.logger` JSON-line, drop-in Logfire/Axiom/Sentry | (Absent) |
| **Pydantic models à frontière** | `growthcro/models/*` validators stricts, mypy strict sur top-3 | Zod côté TS, jamais wiré au Python |

**Verdict §2** : GrowthCRO a un socle métier **dramatiquement plus mature**. Le pack GPT le réduirait à une démo single-page.

---

## 3. Ce que le pack GPT fait mieux

| Discipline | Pack GPT | GrowthCRO actuel |
|---|---|---|
| **PRD → Epic → Issue → Branch → PR** | 10 PRDs + 8 EPICs + 28 ISSUES atomiques, templates formels (`docs/prds/PRD-XXX.md`, `docs/issues/V1_ISSUE_BACKLOG.md`) | Sprints linéaires, peu de PRDs formels, plutôt continuous |
| **Anti-drift protocol formel** | CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS systématiquement | Présent en doctrine, jamais imposé par tooling |
| **LOC constraints mécaniques** | Max 300/file, 150/component, 50/function, 200/agent, doctrine de split | `lint_code_hygiene.py` hard fail à 800 LOC, warn à 300 (signal seulement) |
| **Schemas Zod validés systématiques** | Tout output LLM critique → Zod parse → reject si invalid | Pydantic v2 top-3, le reste en dict |
| **MockProvider first, real LLM after** | Pattern obligatoire : `MockProvider` pour tests, real LLM seulement après mock validé | Direct calls dans la plupart des cas |
| **LLM provider abstraction** | `interface LLMProvider { generateStructured<T>(StructuredPrompt<T>): Promise<T> }` | Anthropic-only, lié à Sonnet 4.5 |
| **4 types de vérité** | Observed / Inferred / Declared / Measured taggé sur chaque conclusion | Concept présent mais pas systématique |
| **Definition of Done globale** | Checklist explicite : acceptance + tests + no scope creep + docs status updated + files listed + next step identifié | Implicite, par sprint |
| **Templates partout** | PRD-TEMPLATE.md, EPIC-TEMPLATE.md, ISSUE-TEMPLATE.md, ADR-000-template.md | Templates manquants |
| **Anti-extrapolation + anti-refactor sauvage** | Règle dure : utile mais hors scope → `NEXT_ACTIONS.md`, jamais code | CLAUDE.md le dit, pas enforced |
| **Checkpoints obligatoires** | Après chaque epic, avant migration DB, avant branchement LLM réel, avant prod | AUDIT_TOTAL_*.md ponctuels |
| **PR template + commit style** | Conventions strictes (feat/fix/test/docs scope) | Présent mais pas templated PR |

**Verdict §3** : Le pack GPT est **moins riche métier**, mais **plus discipliné méthodologiquement**. Importer la discipline (templates PRD/Epic/Issue, anti-drift, LOC, Zod schemas, MockProvider, definition of done) **sans importer la régression scope**.

---

## 4. Ce que l'addendum Skills change

**Apport central** : il transforme "installer un skill" en "ajouter une dépendance logicielle" — donc soumis à audit sécurité, traçabilité, gouvernance.

| Règle addendum | Impact sur GrowthCRO |
|---|---|
| **Installer peu de skills externes** | Le repo a 17 skills externes installés via `skills-lock.json`. **14 sont dormants** (Superpowers obra jamais invoqués). Décision implicite : désinstaller ou pin avec rationale. |
| **Créer 9 skills custom GrowthCRO** | `growthcro-anti-drift` / `growthcro-prd-planner` / `growthcro-status-memory` / `growthcro-cro-audit` / `growthcro-opportunity-engine` / `growthcro-recommendation-engine` / `growthcro-generator-qa` / `growthcro-frontend-quality` / `growthcro-security-review` |
| **8 subagents spécialisés** | product-architect / prd-manager / backend-architect / frontend-quality-reviewer / cro-audit-specialist / security-reviewer / test-qa-engineer / devops-deployment. **Doublons potentiels** : `cro-audit-specialist` vs `scorer` existant + `reco-enricher` existant + `doctrine-keeper` existant. À fusionner, pas à dupliquer. |
| **Skills custom > skills externes** | Doctrine GrowthCRO devient portable sous forme de skill invocable plutôt que de Python heuristique enfouie dans `moteur_gsg/core/`. Maxi-priorité car nos "3 skills runtime actifs" (impeccable, cro-methodology, emil-design-eng) sont en réalité du Python local. |
| **Security checklist avant install** | shell / network / .env / secrets / git / filesystem. **Pas de `curl \| bash` non audité**. Critique vu repo PUBLIC. |
| **MCP > skill quand server-level** | Playwright MCP, GitHub MCP, Supabase MCP, Vercel CLI — hors compte des 8 skills/session (CLAUDE.md anti-pattern #12 le dit déjà). |
| **CCPM colonne vertébrale** | PRD/Epic/Issue/GitHub natif. Possiblement remplacé par notre propre `growthcro-prd-planner` + GitHub API directe. |

**Verdict §4** : l'addendum corrige un **angle mort GrowthCRO** : on a parlé de "skills wired at runtime" en pratique on a du Python local. Il faut soit (a) **convertir** les 3 heuristiques actives en vrais skills Anthropic invocables, soit (b) **assumer** que ce sont des modules Python et arrêter de prétendre que ce sont des skills.

---

## 5. Skills et agents : garder / fusionner / créer / éviter

### 5.1 Tableau skills externes installés (preuve grep)

| Skill | Source | Invocation observée | Décision P0 |
|---|---|---|---|
| `impeccable` | pbakaus/impeccable | ✅ `moteur_gsg/core/impeccable_qa.py:60` `run_impeccable_qa(html=...)` — **Python direct, pas Skill tool** | **GARDER** (mais clarifier statut "runtime heuristic", pas "skill invoqué") |
| `cro-methodology` | wondelai/skills | ✅ `moteur_gsg/modes/mode_1_complete.py:92` `run_cro_methodology_audit()` — **Python direct** | **GARDER** (idem) |
| `emil-design-eng` | emilkowalski/skill | ✅ `moteur_gsg/core/emil_design_eng_audit.py` + `animations.py` — **Python direct** | **GARDER** (idem) |
| `brainstorming` / `executing-plans` / `finishing-a-development-branch` / `dispatching-parallel-agents` / `receiving-code-review` / `requesting-code-review` / `subagent-driven-development` / `systematic-debugging` / `test-driven-development` / `using-git-worktrees` / `using-superpowers` / `verification-before-completion` / `writing-plans` / `writing-skills` | obra/superpowers | ❌ Aucun grep, **dormants** | **PIN ou DROP** — décider pack par pack, ne pas auto-charger en session |
| `gstack` | garrytan/gstack | ❌ Install échoué doc 2026-05-14, dormant | **DROP** ou **REINSTALL avec audit** |

### 5.2 Tableau skills "projet" sous `skills/`

| Path | SKILL.md valide | Statut réel | Décision P0 |
|---|---|---|---|
| `skills/site-capture/` | ✅ | LOCKED v1.0.0, production | **GARDER** |
| `skills/gsg/` | ✅ | ACTIF, invoqué par `moteur_gsg/orchestrator.py` | **GARDER** |
| `skills/cro-auditor/` | ✅ | ACTIF, 54 critères | **GARDER** |
| `skills/client-context-manager/` | ✅ | ACTIF, hub client | **GARDER** |
| `skills/webapp-publisher/` | ✅ | ACTIF, publie audits/recos/LPs V26 | **GARDER** |
| `skills/audit-bridge-to-gsg/` | ✅ | ACTIF, bridge audit→Brief Mode 2 | **GARDER** |
| `skills/cro-library/` | ✅ | ACTIF, pattern library 56 clients | **GARDER** |
| `skills/growthcro-strategist/` | ✅ | ACTIF, diagnostic stratégique on-demand | **GARDER** |
| `skills/skill-based-architecture/` | ✅ | ACTIF (meta-skill) | **GARDER** |
| `skills/growth-site-generator/` | ❌ | Lab legacy, heuristiques Python | **ARCHIVER** sous `_archive/skills_legacy/` |
| `skills/mode-1-launcher/` | ✅ | FROZEN/DEPRECATED, remplacé par `skills/gsg/` | **ARCHIVER** sous `_archive/skills_legacy/` |
| `skills/_roadmap_v27/` | (placeholders) | notion-sync / connections-manager / dashboard-engine | **GARDER** (roadmap V27) |

### 5.3 Tableau agents `.claude/agents/`

| Agent | Skills externes mentionnés | Décision P0 |
|---|---|---|
| `capabilities-keeper.md` | Aucun | **GARDER** |
| `doctrine-keeper.md` | `cro-methodology` (post-process, jamais invoqué via Skill tool) | **GARDER** |
| `scorer.md` | Aucun | **GARDER** |
| `reco-enricher.md` | `cro-methodology`, `/page-cro`, `/form-cro`, `/signup-flow-cro`, `/onboarding-cro`, `/paywall-upgrade-cro`, `/popup-cro` (post-process, jamais invoqué via Skill tool) | **GARDER** |
| `capture-worker.md` | Aucun | **GARDER** |

### 5.4 Skills custom à créer en P0 (validé Mathis)

| Skill custom | Mission | Priorité |
|---|---|---|
| **`growthcro-anti-drift`** | Avant chaque issue : CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS imposé. Format du protocole. | **P0** |
| **`growthcro-prd-planner`** | Transforme idée/module → PRD + Epic + Issues atomiques + Dependencies + Acceptance + Tests + Out-of-scope + Stop conditions | **P0** |
| **`growthcro-status-memory`** | Update `docs/status/PROJECT_STATUS.md` + `NEXT_ACTIONS.md` + `CHANGELOG_AI.md` + `ADR-XXX.md` après chaque epic | **P0** |

### 5.5 Skills custom à créer en P1 (après P0 validé)

| Skill custom | Mission | Priorité | Justification report P1 |
|---|---|---|---|
| `growthcro-cro-audit` | Encapsuler méthodo CRO actuelle (V3.2.1, 54 critères, evidence/rationale/confidence) | P1 | Doctrine déjà codée en Python (`growthcro/scoring/`) — convertir en skill invocable plus tard |
| `growthcro-recommendation-engine` | Encapsuler discipline recos (evidence/hypothesis/action/metric) | P1 | Déjà en code (`growthcro/recos/`) — convertir en skill invocable plus tard |
| `growthcro-opportunity-engine` | NOUVELLE couche audit→opportunities priorisées (impact × confidence × severity / effort) | **P0 partiel** | Le concept manque (zéro occurrence "Opportunity" dans code) — coder le module Python d'abord, puis l'envelopper en skill |
| `growthcro-generator-qa` | Quality gate variantes générées (tied to opportunity / hypothesis / problem / brand / non-générique) | P1 | Impeccable QA fait une partie — étendre |
| `growthcro-frontend-quality` | Review UI density / a11y / loading states / shadcn consistency anti-AI-slop | P1 | Webapp single shell est encore fraîche, pas urgent |
| `growthcro-security-review` | SSRF / prompt injection / secrets / RLS / HTML untrusted | **P0 partiel** | Le SSRF crawler est CRITIQUE — coder le validator d'abord, l'envelopper en skill plus tard |

### 5.6 Subagents à créer / fusionner

L'addendum propose 8 subagents. Plusieurs **doublonnent** ceux existants :

| Subagent proposé addendum | Doublon avec existant ? | Décision |
|---|---|---|
| `product-architect` | (Aucun) | **CRÉER** (cohérence MVP scope, anti-gas factory) |
| `prd-manager` | Couvert par `growthcro-prd-planner` (skill) | **NE PAS CRÉER** subagent, utiliser le skill |
| `backend-architect` | (Aucun) | **DIFFÉRÉ P2** (webapp encore mature) |
| `frontend-quality-reviewer` | Couvert par `growthcro-frontend-quality` (skill P1) | **NE PAS CRÉER** subagent |
| `cro-audit-specialist` | **DOUBLON** avec `scorer` + `doctrine-keeper` existants | **NE PAS CRÉER**, utiliser existants |
| `security-reviewer` | (Aucun) | **CRÉER P0** vu SSRF critique |
| `test-qa-engineer` | (Aucun) | **DIFFÉRÉ P1** |
| `devops-deployment` | (Aucun) | **DIFFÉRÉ P2** (EPIC-008 webapp) |

### 5.7 À éviter maintenant (anti-patterns CLAUDE.md #12)

- **Charger >8 skills simultanés** en session.
- **Combinaisons interdites** : `Taste Skill` + `brand-guidelines` per-client, `lp-creator` + `moteur_gsg`, `theme-factory` + Brand DNA.
- **Réinstaller `gstack`** sans audit sécurité.
- **Créer un subagent qui doublonne `scorer`/`doctrine-keeper`/`reco-enricher`**.
- **Prétendre qu'une heuristique Python est un skill** (3 cas actuels : impeccable, cro-methodology, emil-design-eng — clarifier statut).

---

## 6. Roadmap P0 / P1 / P2

### P0 — Vérité, Gates, Gouvernance (chantier stratosphérique)

**Objectif** : transformer un GSG "bien noté" en un GSG "shippable ou pas, pas de zone grise".

| # | Chantier | Effort | Acceptance |
|---|---|---|---|
| **P0.1** | **Verdict Gate** dans `moteur_multi_judge/orchestrator.py` — agréger `impeccable.passed` + `doctrine.killer_rules_violated` + `impl_penalty > 10pp` + 7 check_gsg_*.py exit codes. Si ANY = FAIL → `final_score_pct = 0` + `verdict = "🔴 Non shippable"` + raise dans `mode_1_complete.py` | M | Test fixture : 1 page avec killer rule fired → verdict forcé "Non shippable" même si composite ≥85% |
| **P0.2** | **Evidence & Claims Ledger gate** — étendre `evidence_ledger.json` schema (`source_type` enforced ∈ {vision, dom, api_external, rule_deterministic}, jamais `llm_classifier` seul). Créer `ClaimsSourceGate` dans `moteur_gsg/core/claims_source_gate.py` qui parse HTML rendu, extract claims (`<span class="number">`, `<li class="proof">`, `<blockquote class="testimonial">`, logos), valide chaque claim vs `evidence_ledger.json`, **bloque** si claim sans source | L | Test fixture : HTML avec testimonial sans `data-evidence-id` → exit 1 + reason |
| **P0.3** | **Opportunity Layer** — créer `growthcro/opportunities/` package mono-concern (orchestrator + schema + persist + cli). Schema : `Opportunity(id, criterion_ref, current_score, target_score, impact, effort, confidence, severity, priority_score, hypothesis, recommended_action, metric_to_track, owner, evidence_ids[])`. Insérer entre `scoring/` et `recos/`. Recos consomment opportunities, pas scores bruts. | XL | 1 client (weglot) génère ≥5 opportunités structurées avec evidence, hypothesis, metric — recos en aval inchangées en richesse |
| **P0.4** | **Skill Registry honnête** — créer `growthcro/SKILLS_REGISTRY_GOVERNANCE.json` distinguant : `installed_external` / `installed_custom` / `runtime_heuristic_python` / `subagent` / `mcp_server`. Pour chacun : `id`, `type`, `location`, `invocation_proof` (grep), `llm_cost`, `security {shell, network, env_vars, secrets, git, filesystem}`, `audit_date`. Clarifier statut impeccable/cro-methodology/emil-design-eng en `runtime_heuristic_python`. | M | Registry validé par script `scripts/audit_skills_governance.py` (greppe les invocations, fail si label drift) |
| **P0.5** | **3 skills custom** : `growthcro-anti-drift`, `growthcro-prd-planner`, `growthcro-status-memory` créés dans `.claude/skills/` avec `SKILL.md` frontmatter conforme | M | Skills appelables via Skill tool, mentionnés dans CLAUDE.md "Init obligatoire" |
| **P0.6** | **Checklist sécurité skills** (`docs/reference/SKILLS_SECURITY_CHECKLIST.md`) : shell / network / .env / secrets / git / filesystem — appliquée AUX 17 skills externes existants en rétroactif | S | 17 entrées dans `SKILLS_REGISTRY_GOVERNANCE.json` avec audit complété |
| **P0.7** | **Fix SSRF critique crawler** — `growthcro/capture/orchestrator.py` ajouter `validate_url(url)` : reject schemes ∉ {http, https}, reject IPs privées (10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12, 127.0.0.0/8, 169.254.0.0/16), reject `localhost`/`metadata` hostnames, reject ports < 80 hors {80, 443, 8080, 8443} | S | Test fixture : `http://localhost:9000/admin` → reject avec ValidationError |
| **P0.8** | **Réconcilier docs** — archiver `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (2026-05-11, dit microfrontends V28) sous `_archive/architecture_pre_d1a/` avec note "superseded by PRODUCT_BOUNDARIES_V26AH §3-bis D1.A 2026-05-14". Update README ligne 3 : "V27 canonical (V27.2-F route selector + V27.2-G visual layer)". | S | `ls webapp/apps/` montre uniquement `shell/`, aucun doc actif ne mentionne `microfrontends.json` |

### P1 — Qualité produit (après P0 validé)

| Chantier | Justification |
|---|---|
| `growthcro-cro-audit` skill custom | Doctrine V3.2.1 portable, invocable par Skill tool (pas juste Python heuristique) |
| `growthcro-recommendation-engine` skill custom | Idem pour les recos |
| `growthcro-generator-qa` skill custom | Étendre impeccable_qa en gate dur lié aux opportunities |
| Playwright MCP wired (E2E webapp shell) | Tester le wizard contexte, le flow capture, le report export |
| axe-core / Lighthouse en gates bloquants (pas avertissements) | Cf. `moteur_gsg/core/external_audits.py` — convertir fallback défensif en gate strict en mode `--ship` |
| Promptfoo / DeepEval pour LLM evals | Evals systématiques GSG output (golden set Weglot + 5 autres clients) |
| Langfuse ou Sentry AI Performance | Observabilité LLM (latency, cost, prompt drift) |
| Benchmark GSG multi-clients × multi-page-types | Sortir de l'overfit Weglot/lp_listicle |
| LLM provider abstraction | Découpler Anthropic Sonnet 4.5 (cf. agentic doc §38) |
| Slash command `/lp-creator-from-blank` | Codifier `memory/CONTENT_INPUT_DOCTRINE.md` en workflow exécutable (était P0 CLAUDE.md, devient P1 après nouveau P0 structural) |
| BriefV2 `chosen_angle` field + `content_angle_freshness_check` gate | Idem (continuité Sprint 21) |

### P2 — Moat (après P1 stable)

| Chantier | Justification |
|---|---|
| Reality Layer activation (1 client pilote Kaiju) | Quand env vars Catchr/Meta/GA/Shopify/Clarity dispo |
| Learning Layer validation humaine 69 proposals → V3.3 | Mathis review, bump doctrine |
| Doctrine GrowthCRO portable sous skills custom | `growthcro-doctrine-v33` skill |
| Skills externes seulement si audit + utilité prouvée | Pas de `curl \| bash` réflexe |
| MCP Supabase/Sentry/GitHub avec env dev + permissions cadrées | Pas en prod sans review |
| `growthcro-frontend-quality` skill custom | Quand webapp shell mature |
| GEO Monitor multi-engine | OPENAI + PERPLEXITY keys |
| Experiment Engine A/B real | Calculator OK, manque déclencheurs |

---

## 7. Issues prêtes à coder (P0)

Format compact : 1 issue = 1 comportement / artefact technique clair, 1-6 fichiers touchés, 50-300 LOC.

### ISSUE-P0-01 — `Verdict Gate` agrégateur dans multi-judge
- **Linked** : P0.1
- **In scope** : `moteur_multi_judge/orchestrator.py` (ajouter `compute_verdict_with_blocking_gates()`), `moteur_multi_judge/judges/blocking_gates.py` (nouveau, charge `impeccable.passed`, `killer_rules_violated`, `impl_penalty`, 7 check_gsg_*.py exit codes via subprocess), 1 fixture test
- **Out of scope** : modifier le scoring composite lui-même
- **Acceptance** : fixture avec `killer_rules_violated=True` → `verdict_tier="🔴 Non shippable"` même si `composite=92%`
- **Stop conditions** : modif du calcul composite, modif des sub-judges
- **Files** : 3 (orchestrator.py + blocking_gates.py + test fixture)

### ISSUE-P0-02 — `ClaimsSourceGate` parsing HTML rendu
- **Linked** : P0.2
- **In scope** : `moteur_gsg/core/claims_source_gate.py` (nouveau, mono-concern validation), pattern recognition pour `<span class="number">`, `<li class="proof-strip">`, `<blockquote class="testimonial">`, `<img class="logo-strip">`. Wire dans `mode_1_complete.py` post-impeccable, avant multi-judge
- **Out of scope** : modifier le HTML rendering du renderer contrôlé
- **Acceptance** : HTML avec testimonial sans `data-evidence-id` → raise `ClaimsSourceError` avec reason
- **Stop conditions** : modifier `evidence_ledger.json` schema sans ADR
- **Files** : 2 (claims_source_gate.py + test fixture HTML)

### ISSUE-P0-03 — Schema `Opportunity` + persistence
- **Linked** : P0.3 (étape 1/3)
- **In scope** : `growthcro/opportunities/__init__.py`, `growthcro/opportunities/schema.py` (Pydantic v2 strict), `growthcro/opportunities/persist.py` (write `data/captures/<client>/<page>/opportunities.json`)
- **Out of scope** : générer les opportunities depuis l'audit (= ISSUE-P0-04)
- **Acceptance** : Pydantic schema rejette opp sans evidence_ids, hypothesis ou metric. Persist round-trip OK.
- **Stop conditions** : toucher `growthcro/recos/`
- **Files** : 3 (schema.py + persist.py + test)

### ISSUE-P0-04 — Opportunity engine (orchestrator)
- **Linked** : P0.3 (étape 2/3)
- **In scope** : `growthcro/opportunities/orchestrator.py` — prend `score_page_type.json + score_applicability_overlay.json + brief` en input, produit `opportunities.json` (priorité par formule `priority_score = (impact * confidence * severity) / effort`)
- **Out of scope** : modifier le scoring
- **Acceptance** : Weglot home → ≥5 opportunités structurées avec hypothesis + metric
- **Stop conditions** : appel LLM (l'engine doit être déterministe au premier shot, LLM enrichment = ISSUE-P1)
- **Files** : 2 (orchestrator.py + test fixture weglot)

### ISSUE-P0-05 — CLI opportunities + wiring recos
- **Linked** : P0.3 (étape 3/3)
- **In scope** : `growthcro/opportunities/cli.py` (`python -m growthcro.opportunities.cli prepare --client weglot --page home`), modif `growthcro/recos/orchestrator.py` pour consommer `opportunities.json` au lieu de scores bruts
- **Out of scope** : modifier le prompt assembly des recos
- **Acceptance** : pipeline weglot/home end-to-end produit recos liées aux opportunities (champ `linked_opportunity_id`)
- **Stop conditions** : régression sur richesse recos (compter taille `recos_v13_final.json` avant/après)
- **Files** : 2 (cli.py + orchestrator.py modif)

### ISSUE-P0-06 — `SKILLS_REGISTRY_GOVERNANCE.json` + script audit
- **Linked** : P0.4
- **In scope** : `growthcro/SKILLS_REGISTRY_GOVERNANCE.json` (toplevel), `scripts/audit_skills_governance.py` (greppe les invocations, fail si label drift, distingue runtime_heuristic_python de skill réel)
- **Out of scope** : changer les invocations existantes
- **Acceptance** : 17 skills externes + 10 skills projet + 5 agents listés avec type + invocation_proof + security audit
- **Stop conditions** : modifier `CAPABILITIES_REGISTRY.json` (lui est code-only, on garde)
- **Files** : 2 (registry json + audit script)

### ISSUE-P0-07 — Skill custom `growthcro-anti-drift`
- **Linked** : P0.5 (skill 1/3)
- **In scope** : `.claude/skills/growthcro-anti-drift/SKILL.md` + sous-fichiers de référence si besoin
- **Out of scope** : modifier les agents existants
- **Acceptance** : skill invocable via Skill tool, frontmatter conforme, impose le format CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS
- **Stop conditions** : créer le contenu en doublonnant CLAUDE.md (référer-le, ne pas dupliquer)
- **Files** : 1 (SKILL.md)

### ISSUE-P0-08 — Skill custom `growthcro-prd-planner`
- **Linked** : P0.5 (skill 2/3)
- **In scope** : `.claude/skills/growthcro-prd-planner/SKILL.md` + templates de PRD/Epic/Issue
- **Out of scope** : modifier les PRDs existants
- **Acceptance** : skill invocable, génère PRD + Epic + Issues atomiques avec acceptance + tests + out-of-scope + stop conditions
- **Files** : 2 (SKILL.md + templates/)

### ISSUE-P0-09 — Skill custom `growthcro-status-memory`
- **Linked** : P0.5 (skill 3/3)
- **In scope** : `.claude/skills/growthcro-status-memory/SKILL.md`
- **Out of scope** : modifier `memory/MEMORY.md` schema
- **Acceptance** : skill invocable, update `docs/status/PROJECT_STATUS.md` + `NEXT_ACTIONS.md` + `CHANGELOG_AI.md` + `ADR-XXX.md` selon format WHAT CHANGED / CURRENT STATE / WHAT IS MOCKED / WHAT WORKS / KNOWN RISKS / NEXT ACTIONS / DO NOT FORGET
- **Files** : 1 (SKILL.md)

### ISSUE-P0-10 — Checklist sécurité skills + audit rétroactif
- **Linked** : P0.6
- **In scope** : `.claude/docs/reference/SKILLS_SECURITY_CHECKLIST.md`, audit rétro des 17 skills externes (shell / network / .env / secrets / git / filesystem)
- **Out of scope** : désinstaller des skills
- **Acceptance** : 17 entrées audit dans `SKILLS_REGISTRY_GOVERNANCE.json`
- **Files** : 1 doc + update json registry

### ISSUE-P0-11 — Fix SSRF crawler (validation URL)
- **Linked** : P0.7
- **In scope** : `growthcro/capture/url_validator.py` (nouveau, mono-concern), wire dans `growthcro/capture/orchestrator.py` et `growthcro/capture/cli.py` pré-`page.goto`
- **Out of scope** : modifier Playwright config
- **Acceptance** : `http://localhost:9000/admin` → `URLValidationError`. Test fixture avec 10 URLs (5 valides, 5 invalides incl. AWS metadata, file://, localhost, IP privée)
- **Stop conditions** : casser les captures existantes (run smoke sur 3 clients après merge)
- **Files** : 2 (url_validator.py + orchestrator.py modif + test)

### ISSUE-P0-12 — Archiver doc obsolète + update README
- **Linked** : P0.8
- **In scope** : `git mv architecture/GROWTHCRO_ARCHITECTURE_V1.md _archive/architecture_pre_d1a/`, update README ligne 3 + ligne 22 (Architecture cible) pour refléter D1.A single shell, add changelog manifest §12
- **Out of scope** : modifier `PRODUCT_BOUNDARIES_V26AH.md`
- **Acceptance** : `find . -name "GROWTHCRO_ARCHITECTURE_V1.md"` retourne seulement `_archive/`
- **Files** : 2 (mv + README + manifest)

**Total P0** : 12 issues, ~30 fichiers touchés, ~2000-3000 LOC ajoutées.

---

## 8. Stop conditions (à respecter pendant l'implémentation P0)

L'agent d'implémentation **doit s'arrêter et demander validation Mathis** si :

1. Une **migration destructive** est nécessaire (DB schema change, `git mv` massif).
2. Un **secret** est détecté en clair (commit en cours, log, comment).
3. Une **contradiction produit** non tranchée apparaît (ex: scope opportunity vs scope reco).
4. Un **skill externe** est requis pour avancer (audit sécurité préalable + accord).
5. Une **sortie LLM critique** n'est pas validée par schema (Pydantic v2 strict).
6. Un **claim** est rendu sans preuve dans le HTML test.
7. Un **fichier hors scope** doit être touché (l'agent propose une issue séparée, ne touche pas).
8. **LOC** dépasse les limites : >800 source file → hard FAIL, >300 → split obligatoire avant ajout.
9. Un **gate critique échoue** sur les tests existants (régression Weglot).
10. Le **lint_code_hygiene.py --staged** retourne `fail > 0`.
11. Un **anti-pattern CLAUDE.md** se manifesterait (mega-prompt >8K, archive dans path actif, basename duplicate hors allow-list, env read hors config.py, >8 skills simultanés, combo interdit).
12. La **doctrine** doit changer (V3.2.1 → V3.3 : passer par `doctrine-keeper` agent).
13. Le **manifest §12** doit être bumped (commit séparé `docs: manifest §12 — ...`).

---

## 9. Prompt futur d'implémentation P0 (à utiliser seulement après validation humaine)

**À ne lancer qu'après ton OK explicite Mathis sur le présent dossier.**

```text
Tu vas implémenter uniquement P0 du dossier de décision
`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`.

Init obligatoire (avant tout code) :
1. Lire `.claude/CLAUDE.md` + `.claude/README.md` + ce dossier de décision
2. Lire `.claude/docs/doctrine/CODE_DOCTRINE.md` — 8 axes, hard rules
3. `python3 state.py` — état disque
4. `python3 scripts/audit_capabilities.py` + lire `CAPABILITIES_SUMMARY.md`
5. `python3 scripts/lint_code_hygiene.py` — baseline hygiène
6. Lire les 5 agents `.claude/agents/*.md`

Scope (12 issues, P0 strict) :
- ISSUE-P0-01 : Verdict Gate agrégateur dans multi-judge
- ISSUE-P0-02 : ClaimsSourceGate parsing HTML rendu
- ISSUE-P0-03 : Schema Opportunity + persistence
- ISSUE-P0-04 : Opportunity engine orchestrator
- ISSUE-P0-05 : CLI opportunities + wiring recos
- ISSUE-P0-06 : SKILLS_REGISTRY_GOVERNANCE.json + audit script
- ISSUE-P0-07 : Skill custom growthcro-anti-drift
- ISSUE-P0-08 : Skill custom growthcro-prd-planner
- ISSUE-P0-09 : Skill custom growthcro-status-memory
- ISSUE-P0-10 : Checklist sécurité skills + audit rétroactif 17 skills
- ISSUE-P0-11 : Fix SSRF crawler (validation URL)
- ISSUE-P0-12 : Archiver doc obsolète + update README + manifest §12

Out of scope (P1/P2 — interdit de toucher) :
- redesign UI webapp shell
- nouveau GSG créatif / Mode 6
- nouvelles intégrations Reality Layer
- installation de skills externes (audit dans P0.10 = rétroactif, pas install)
- refactor massif (>5 fichiers hors scope d'une issue)
- microfrontends (D1.A acté, single shell verrouillé)
- changement de stack (Next.js 14 + Supabase + Anthropic Sonnet 4.5)
- modifier la doctrine V3.2.1 (V3.3 = Mathis review des 69 proposals)
- générer du copy LLM dans Opportunity engine (déterministe au premier shot)

Workflow obligatoire par issue :
1. Avant de commencer : remplir le format anti-drift formel (CURRENT ISSUE / LINKED P0 / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS / FILES_ALLOWED / FILES_FORBIDDEN)
2. Coder l'issue (1-6 fichiers touchés, 50-300 LOC ajoutées max)
3. Tests : fixture + cas limites
4. `python3 scripts/lint_code_hygiene.py --staged` → DOIT exit 0
5. `python3 SCHEMA/validate_all.py` si schemas touchés → DOIT exit 0
6. Commit séparé par issue, message conventional commit (`feat(opportunities): ...`, `feat(gates): ...`, `feat(skills): ...`, `fix(security): SSRF crawler`, `docs(architecture): archive V1`)
7. Update `docs/status/PROJECT_STATUS.md` + `docs/status/CHANGELOG_AI.md` (skill growthcro-status-memory une fois créé)
8. Rapport fin d'issue : DONE / FILES CHANGED / TESTS RUN / DOCS UPDATED / RISKS / NEXT ISSUE

Stop conditions (cf. dossier §8) :
- migration destructive
- secret détecté en clair
- contradiction produit non tranchée
- skill externe requis
- sortie LLM non validée par schema
- claim rendable sans preuve
- fichier hors scope
- LOC limit dépassé
- gate critique échoue
- lint_code_hygiene --staged fail
- anti-pattern CLAUDE.md
- doctrine doit changer
- manifest §12 doit être bumped

Ordre d'implémentation recommandé (dépendances) :
1. ISSUE-P0-11 (SSRF fix) — bloquant sécurité, fast
2. ISSUE-P0-12 (archive doc obsolète) — fast, déverrouille
3. ISSUE-P0-07/08/09 (3 skills custom) — fondation gouvernance, en parallèle
4. ISSUE-P0-06 (Skill Registry Governance) — consume les 3 skills
5. ISSUE-P0-10 (Checklist sécu skills) — consume le registry
6. ISSUE-P0-03 (Opportunity schema) — fondation P0.3
7. ISSUE-P0-04 (Opportunity engine) — dépend de P0-03
8. ISSUE-P0-05 (CLI + wiring recos) — dépend de P0-04
9. ISSUE-P0-01 (Verdict Gate) — consume gates existants
10. ISSUE-P0-02 (ClaimsSourceGate) — dépend de evidence_ledger schema (peut être avant P0-01)

Acceptance globale P0 :
- 12 issues fermées, 12 commits séparés
- Test smoke Weglot end-to-end : capture → score → opportunities → recos → GSG → verdict gate → multi-judge
- Si killer_rules_violated=True sur fixture test, verdict "🔴 Non shippable" forcé même composite 92%
- Si HTML rendered claim sans data-evidence-id, ClaimsSourceGate raise + GSG refuse de ship
- SSRF localhost/IP privée → URLValidationError
- 3 skills custom appelables via Skill tool
- SKILLS_REGISTRY_GOVERNANCE.json complet, audit 17 skills externes documenté
- README ligne 3 et 22 actualisés, doc V1 archivée, manifest §12 bumped

Ne fais rien hors scope. Demande validation Mathis sur chaque stop condition.
```

---

## 10. Annexes

### 10.1 Top 5 risques sécurité (de l'audit 3)

| Rang | Risque | Sévérité | Preuve | Fix |
|---|---|---|---|---|
| 1 | **SSRF Crawler** — accepte URLs arbitraires | 🔴 CRITIQUE | `growthcro/capture/orchestrator.py:68` `page.goto(url)` direct | ISSUE-P0-11 |
| 2 | **JWT in git history** — repo public + 17 commits référencent `SUPABASE_SERVICE_ROLE_KEY` | 🟠 HAUT | `git log -S "SUPABASE_SERVICE_ROLE_KEY"` | Rotation immédiate + `git-filter-repo` si redeploy critique (hors P0) |
| 3 | **HTML scraped untrusted** — stocké Supabase Storage, future XSS si rendered | 🟡 MOYEN | `data/captures/*/html_snapshot/*.html` non sanitized | CSP header webapp + DOMPurify si rendering futur (P1) |
| 4 | **`os.environ` hors config.py** — surface drift | 🟡 MOYEN | Audit linter en place, status unknown sur tout le repo | `python3 scripts/lint_code_hygiene.py` baseline (déjà gated en pre-commit) |
| 5 | **Service_role JWT en exemples docs** | 🟢 FAIBLE | `scripts/upload_screenshots_to_supabase.py:13` exemple | Remplacer par `<ask-ops>` placeholder (hors P0) |

### 10.2 Tableau gates (de l'audit 2)

| Gate | Type | Bloquant aujourd'hui | Doit l'être après P0 |
|---|---|---|---|
| SCHEMA/validate_all.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| check_gsg_canonical.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| check_gsg_controlled_renderer.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| check_gsg_creative_route_selector.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| check_gsg_intake_wizard.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| check_gsg_component_planner.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| check_gsg_visual_renderer.py | Validator | ✅ Oui | ✅ Oui (inchangé) |
| impeccable_qa | Heuristic | ❌ Non | **✅ Oui via Verdict Gate** (P0.1) |
| multi_judge doctrine (killer_rules) | LLM audit | ❌ Non | **✅ Oui via Verdict Gate** (P0.1) |
| multi_judge implementation (impl_penalty) | LLM audit | ❌ Non | **✅ Oui via Verdict Gate** si >10pp (P0.1) |
| cro_methodology_audit | Heuristic | ❌ Non | ⚠️ Reste informatif (P1 promo) |
| frontend_design_audit | Heuristic | ❌ Non | ⚠️ Reste informatif (P1) |
| brand_guidelines_audit | Heuristic | ❌ Non | ⚠️ Reste informatif (P1) |
| emil_design_eng_audit | Heuristic | ❌ Non | ⚠️ Reste informatif (P1) |
| axe-core (a11y) | Subprocess | ❌ Non (fallback défensif) | ⚠️ P1 (mode `--ship` strict) |
| Lighthouse (perf) | Subprocess | ❌ Non (fallback défensif) | ⚠️ P1 (mode `--ship` strict) |
| evidence_ledger | Tracer (append-only) | ❌ Non | **✅ Oui via ClaimsSourceGate** (P0.2) |
| **Opportunity → Reco link** | (n'existe pas) | ❌ N/A | **✅ Oui via Opportunity Layer** (P0.3) |

### 10.3 Tableau skills externes (de l'audit 1)

| Skill | Source | Invocation observée | Type réel | Décision P0 |
|---|---|---|---|---|
| impeccable | pbakaus/impeccable | `moteur_gsg/core/impeccable_qa.py:60` Python direct | runtime_heuristic_python | Garder + clarifier statut |
| cro-methodology | wondelai/skills | `mode_1_complete.py:92` Python direct | runtime_heuristic_python | Garder + clarifier statut |
| emil-design-eng | emilkowalski/skill | `emil_design_eng_audit.py` + `animations.py` Python direct | runtime_heuristic_python | Garder + clarifier statut |
| brainstorming | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| executing-plans | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| finishing-a-development-branch | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| dispatching-parallel-agents | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| receiving-code-review | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| requesting-code-review | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| subagent-driven-development | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| systematic-debugging | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| test-driven-development | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| using-git-worktrees | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| using-superpowers | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| verification-before-completion | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| writing-plans | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| writing-skills | obra/superpowers | (aucune) | installed_external_dormant | Pin ou drop (P0.6) |
| gstack | garrytan/gstack | (install échoué) | installed_external_failed | Drop ou reinstall avec audit (P0.6) |

### 10.4 Tableau contradictions docs↔code (de l'audit 4)

| Tension | Doc A | Doc B | Vérité disque | Action |
|---|---|---|---|---|
| Microfrontends | `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (2026-05-11) : 6 µfrontends | `PRODUCT_BOUNDARIES_V26AH §3-bis` (2026-05-14) : single shell D1.A | Single shell (`webapp/apps/shell/` uniquement, `_archive/webapp_microfrontends_2026-05-12/`) | **ARCHIVER doc A** (P0.8) |
| GSG version | README ligne 3 : V27.2-F | SPRINT_LESSONS : V27.2-G | Les deux coexistent (F = route selector, G = visual layer) | Update README pour mentionner les deux (P0.8) |
| Webapp HTML/Next | README : V26-WebApp.html + V27 Command Center | ARCHITECTURE_V1 : V28 Next.js production | V26/V27 HTML en prod, V28 shell exists pas encore live | Pas de contradiction effective, clarifier dans README |
| Skills count | CLAUDE.md anti-pattern #12 : ≤8/session | skills-lock.json : 17 | Limite par session, pas global. Combo packs respectent. | Pas de contradiction |
| Reality Layer | README : "Orchestrator corrigé V26.AI, dry-run OK" | PRODUCT_BOUNDARIES : "INACTIVE" | INACTIVE confirmé (pas de dir, pas de json, env vars manquent) | Pas de contradiction (sémantique : "dry-run OK" ≠ "actif") |
| Versionning | V26.AI / V27.2-F / V28 | (idem) | Schéma progressif clair | Pas de contradiction |

---

## 11. Synthèse exécutive

**Le plan PLAN_GrowthCRO_Challenge_Codex_GPT.md est validé** :
- Verdict §1 confirmé : ne pas repartir de zéro, importer la discipline du pack GPT + la gouvernance de l'addendum.
- P0 §7 confirmé : Verdict Gate + Evidence & Claims Ledger gate + Opportunity Layer + Skill Registry honnête + 3 skills custom + checklist sécurité = exactement le socle manquant.

**Ce qui n'était pas dans le plan mais qui ressort des audits** :
- **SSRF critique** dans le crawler (`page.goto(url)` sans validation) — à fixer dans P0.7 (ISSUE-P0-11), sinon le repo public est un vecteur d'attaque dès qu'un client utilise l'API.
- **Archive doc obsolète** : `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (microfrontends V28) contredit `PRODUCT_BOUNDARIES_V26AH §3-bis` (single shell D1.A) — à archiver pour éviter futur drift Claude.

**Ce qui change vs CLAUDE.md Sprint 22+ candidates** :
- Les candidats P0 du CLAUDE.md (`/lp-creator-from-blank`, BriefV2 `chosen_angle`, `content_angle_freshness_check`) glissent en **P1** — ils consommeront ensuite la nouvelle chaîne (Verdict Gate + Evidence Ledger + Opportunity Layer) plutôt que d'être ajoutés à une chaîne qui laisse passer des outputs douteux.

**Volumétrie P0** : 12 issues, ~30 fichiers touchés, ~2000-3000 LOC ajoutées, 12 commits conventional commit, ordre d'implémentation explicite (SSRF + doc archive d'abord, fondations skills ensuite, Opportunity Layer en dernier).

**Stop conditions formelles** : 13 conditions explicites (cf. §8).

**Prompt d'implémentation** : prêt §9, à utiliser SEULEMENT après validation explicite Mathis.

---

*Dossier produit en mode read-only le 2026-05-16. Aucun fichier source modifié, aucun skill installé, aucune commande destructive lancée. Inputs : PLAN principal + 3 fichiers sources + l'agentic + delivery_pack_v2 + skills_addendum_pack + doctrine projet + 4 audits Explore parallèles.*
