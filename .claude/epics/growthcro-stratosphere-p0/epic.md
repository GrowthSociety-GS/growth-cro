---
name: growthcro-stratosphere-p0
status: backlog
created: 2026-05-16T12:14:34Z
updated: 2026-05-16T12:14:34Z
progress: 0%
prd: .claude/prds/growthcro-stratosphere-p0.md
github: (will be set on sync)
---

# Epic: growthcro-stratosphere-p0

> Source de vérité primaire : [`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`](../../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md). PRD : [`.claude/prds/growthcro-stratosphere-p0.md`](../../prds/growthcro-stratosphere-p0.md).

## Overview

Muscler la **chaîne de vérité bloquante** de GrowthCRO en 12 issues atomiques. Trois lignes de force :

1. **Gates qui bloquent vraiment** — `Verdict Gate` qui consume `impeccable.passed + killer_rules_violated + impl_penalty + 7 check_gsg_*.py exit codes` et force `🔴 Non shippable` si ANY = FAIL. `ClaimsSourceGate` qui refuse tout HTML rendant un claim sans `data-evidence-id`.

2. **Opportunity Layer manquant** — couche déterministe entre `scoring/` et `recos/` qui produit des `Opportunity(impact, effort, confidence, severity, priority_score, hypothesis, metric_to_track, evidence_ids[])` consommées en aval par les recos.

3. **Gouvernance agentique honnête** — `SKILLS_REGISTRY_GOVERNANCE.json` distinguant `installed_external_active/dormant` vs `runtime_heuristic_python` vs `installed_custom` vs `subagent` vs `mcp_server`. 3 skills custom créés (`growthcro-anti-drift`, `growthcro-prd-planner`, `growthcro-status-memory`). Checklist sécurité rétroactive sur les 17 skills externes.

Plus : **fix SSRF crawler** (critique, repo PUBLIC) et **archive doc obsolète** (`architecture/GROWTHCRO_ARCHITECTURE_V1.md` qui contredit `PRODUCT_BOUNDARIES_V26AH §3-bis` D1.A single shell).

## Architecture Decisions

| Décision | Rationale |
|---|---|
| **Pas de refonte feuille blanche** | GrowthCRO V26.AI (56 clients, 185 pages, 3045 recos) >>> pack GPT MVP single-page. On importe la discipline, pas le scope reset. |
| **Opportunity engine déterministe au premier shot** | Pas d'appel LLM (déterministe = reproductible = testable). LLM enrichment = ISSUE P1 séparée. |
| **Verdict Gate dans `moteur_multi_judge/orchestrator.py`** | Là où `verdict_tier` est déjà calculé (ligne 96-107). Pas un nouveau module wrapper, une extension du composite. |
| **ClaimsSourceGate dans `moteur_gsg/core/`** | Wire post-impeccable, pre-multi-judge dans `mode_1_complete.py`. Parser HTML rendu, pas l'output LLM brut. |
| **`growthcro/opportunities/` package mono-concern (8 axes CODE_DOCTRINE)** | `schema.py` (Pydantic v2) + `persist.py` + `orchestrator.py` + `cli.py`. Pas de god-file. |
| **Skill Registry séparé de `CAPABILITIES_REGISTRY.json`** | `CAPABILITIES_REGISTRY.json` reste code-only (fichiers Python actifs). `SKILLS_REGISTRY_GOVERNANCE.json` est doctrine-gouvernance (skill type + invocation_proof + security audit). |
| **3 skills custom dans `.claude/skills/` racine projet** | Pas dans `~/.claude/skills/` user global. Skills projet committed dans repo pour traçabilité (l'addendum dit "committer les skills projet pour traçabilité"). |
| **URL validator mono-concern `growthcro/capture/url_validator.py`** | Pas dans `orchestrator.py` (multi-concern interdit). 1 module, 1 axe (validation). |
| **Pas de modification de doctrine V3.2.1** | V3.3 = Mathis review des 69 proposals. Hors P0. |
| **Conventional commit + 1 commit par issue** | Traceability + rollback granulaire. |

## Technical Approach

### Backend Services / Python modules

**Nouveaux modules (mono-concern, 8 axes CODE_DOCTRINE)** :

- `growthcro/opportunities/__init__.py` (package marker)
- `growthcro/opportunities/schema.py` (Pydantic v2 — axe `validation`)
- `growthcro/opportunities/persist.py` (read/write `data/captures/.../opportunities.json` — axe `persistence`)
- `growthcro/opportunities/orchestrator.py` (sequence scoring → opps — axe `orchestration`)
- `growthcro/opportunities/cli.py` (argparse entrypoint — axe `CLI`)
- `moteur_gsg/core/claims_source_gate.py` (validate HTML claims vs evidence ledger — axe `validation`)
- `moteur_multi_judge/judges/blocking_gates.py` (aggregate blocking signals — axe `validation`)
- `growthcro/capture/url_validator.py` (validate input URLs — axe `validation`)

**Modifications ciblées (1-2 axes touchés max par fichier)** :

- `moteur_multi_judge/orchestrator.py` : ajouter `compute_verdict_with_blocking_gates()` consuming `blocking_gates.py`.
- `moteur_gsg/modes/mode_1_complete.py` : wire `claims_source_gate` post-impeccable, raise si fail.
- `growthcro/capture/orchestrator.py:68` : appeler `url_validator.validate_url(url)` pré-`page.goto`.
- `growthcro/capture/cli.py` : appel `url_validator` au parsing args.
- `growthcro/recos/orchestrator.py` : consommer `opportunities.json`, ajouter `linked_opportunity_id` aux recos.
- `skills/site-capture/scripts/evidence_ledger.py` : strict schema `source_type` enum.

### Skills (`.claude/skills/` racine projet)

- `.claude/skills/growthcro-anti-drift/SKILL.md` (frontmatter `name`+`description` conforme Anthropic Skill spec)
- `.claude/skills/growthcro-prd-planner/SKILL.md` (+ templates PRD/Epic/Issue dans subdir si besoin)
- `.claude/skills/growthcro-status-memory/SKILL.md`

### Doctrine / Documentation

- `growthcro/SKILLS_REGISTRY_GOVERNANCE.json` (toplevel registry)
- `scripts/audit_skills_governance.py` (audit script, exit code != 0 si label drift)
- `.claude/docs/reference/SKILLS_SECURITY_CHECKLIST.md` (template + 17 audits rétroactifs)
- `.claude/CLAUDE.md` : ajouter step #13 "Lire `SKILLS_REGISTRY_GOVERNANCE.json` + `SKILLS_SECURITY_CHECKLIST.md`"
- `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 : changelog entry 2026-05-16 (ce sprint)
- `README.md` : ligne 3 et ligne 22 update (V27.2-F/G + retrait référence V1)
- `git mv architecture/GROWTHCRO_ARCHITECTURE_V1.md _archive/architecture_pre_d1a/` (avec note de superseding)

### Infrastructure

- **Pas de modif infra** (Next.js shell, Supabase, Fly.io backend FastAPI) — hors P0.
- **GitHub** : 1 Epic issue + 12 task issues sur `GrowthSociety-GS/growth-cro`.
- **Worktree** : `../epic-growthcro-stratosphere-p0` post-sync.
- **Tests** : pytest pour Pydantic schemas + integration smoke Weglot end-to-end.

## Implementation Strategy

### Waves de parallélisation (max 5 concurrent)

**Wave 1 — Fondations indépendantes (6 issues en parallèle possible)** :
- ISSUE-001 : Fix SSRF crawler (P0-11) — fast, critique sécurité
- ISSUE-002 : Archive doc V1 obsolète (P0-12) — fast, déverrouille drift Claude
- ISSUE-003 : Skill custom `growthcro-anti-drift` (P0-07)
- ISSUE-004 : Skill custom `growthcro-prd-planner` (P0-08)
- ISSUE-005 : Skill custom `growthcro-status-memory` (P0-09)
- ISSUE-008 : Opportunity schema (P0-03 étape 1/3)

**Wave 2 — Consommateurs de wave 1 (3 issues parallèles)** :
- ISSUE-006 : Skill Registry Governance (P0-04) — dépend 003+004+005
- ISSUE-009 : Opportunity engine orchestrator (P0-03 étape 2/3) — dépend 008
- ISSUE-012 : ClaimsSourceGate (P0-02) — peut commencer indép. mais smoke-test évidence_ledger.json shape sur Weglot first

**Wave 3 — Wrap-up (3 issues, séquentielles ou parallèles)** :
- ISSUE-007 : Checklist sécurité skills + audit rétroactif 17 (P0-06) — dépend 006
- ISSUE-010 : Opportunity CLI + wiring recos (P0-03 étape 3/3) — dépend 009
- ISSUE-011 : Verdict Gate agrégateur (P0-01) — indép. mais logique en dernier

### Tooling parallèle

- **Subagents existants à invoquer** : `capabilities-keeper` (avant tout sprint code GSG/audit), `doctrine-keeper` (si touche playbook — théoriquement non), `scorer` (smoke Weglot), `reco-enricher` (smoke Weglot).
- **Skill custom `growthcro-anti-drift` invoqué dès qu'il existe** (à partir de wave 2).
- **Worktree par epic** : tout le travail dans `../epic-growthcro-stratosphere-p0`.
- **1 commit conventional par issue** : `feat(security): fix SSRF crawler validation [#001]`, etc.

### Stop conditions

13 conditions formelles cf. dossier de décision §8. Les plus probables ici :
- Régression Weglot baseline (composite Sprint 21 = 88.6%) → stop + ADR.
- `python3 scripts/lint_code_hygiene.py --staged` exit != 0 → fix avant proceed.
- Découverte secret en clair pendant édition → stop + Mathis.
- Sortie LLM critique non validée par Pydantic → stop + schema avant code.
- Toucher fichier hors scope d'une issue → ouvrir issue séparée, ne pas drift.

## Task Breakdown Preview

12 tasks, ordonnées par wave et dépendances. Effort total : ~80-120h dev.

| Task | Title | Wave | Parallel | Depends on | Effort |
|---|---|---|---|---|---|
| 001 | Fix SSRF crawler validation | 1 | yes | — | S (4h) |
| 002 | Archive obsolete architecture V1 doc | 1 | yes | — | XS (1h) |
| 003 | Create skill `growthcro-anti-drift` | 1 | yes | — | S (3h) |
| 004 | Create skill `growthcro-prd-planner` | 1 | yes | — | S (4h) |
| 005 | Create skill `growthcro-status-memory` | 1 | yes | — | S (3h) |
| 006 | Create `SKILLS_REGISTRY_GOVERNANCE.json` + audit script | 2 | partial | 003,004,005 | M (8h) |
| 007 | Skills security checklist + retroactive audit 17 externals | 3 | yes | 006 | M (6h) |
| 008 | `Opportunity` Pydantic schema + persistence | 1 | yes | — | M (6h) |
| 009 | Opportunity engine orchestrator (deterministic) | 2 | partial | 008 | L (12h) |
| 010 | Opportunity CLI + wire recos orchestrator | 3 | yes | 009 | M (8h) |
| 011 | Verdict Gate aggregator in multi-judge | 3 | yes | — | M (8h) |
| 012 | ClaimsSourceGate HTML parser + wire mode_1 | 2/3 | yes | — | L (12h) |

Total estimated : ~75h (low end if minimal acceptance) → ~120h (high end if extensive fixtures + smoke).

## Dependencies

### Internal (in repo, no external install)
- `moteur_gsg/core/impeccable_qa.py` (input Verdict Gate)
- `moteur_multi_judge/orchestrator.py:96-107` (modify Verdict Gate)
- `moteur_multi_judge/judges/doctrine_judge.py:240` (read killer_rules)
- `growthcro/scoring/*` (input Opportunity engine)
- `growthcro/recos/orchestrator.py` (wire opportunities consumer)
- `growthcro/capture/orchestrator.py:68` + `cli.py` (SSRF fix wire)
- `scripts/check_gsg_*.py` (7 scripts, input Verdict Gate exit codes)
- `SCHEMA/validate_all.py` (input Verdict Gate exit code)
- `skills/site-capture/scripts/evidence_ledger.py` (extend schema P0.2)
- `scripts/lint_code_hygiene.py` (gate avant chaque commit)
- `.claude/CLAUDE.md`, `.claude/docs/reference/GROWTHCRO_MANIFEST.md`, `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`, `README.md` (doc updates)

### External (read-only audits)
- 17 skills externes via `skills-lock.json` (audit P0.6 rétroactif)
- 10 skills projet sous `skills/` (audit P0.6)
- 5 agents `.claude/agents/*.md` (audit P0.6)

### GitHub
- Remote `https://github.com/GrowthSociety-GS/growth-cro.git`
- 1 Epic issue + 12 task issues à créer post-validation Mathis
- Worktree `../epic-growthcro-stratosphere-p0`

### Notion (read-only, no modification)
- *Mathis Project x GrowthCRO Web App*
- *Le Guide Expliqué Simplement*

## Success Criteria (Technical)

1. **Smoke test Weglot end-to-end PASS** : capture → score → opportunities → recos → GSG → claims_source_gate → verdict_gate → multi-judge. Composite Sprint 21 baseline (88.6%) reproductible, pas de régression.
2. **Verdict Gate** : fixture `killer_rules_violated=True` + `composite=92%` → `verdict_tier="🔴 Non shippable"`.
3. **ClaimsSourceGate** : fixture HTML avec testimonial sans `data-evidence-id` → `ClaimsSourceError` raise + GSG refuse de ship.
4. **Opportunity Layer** : Weglot home → ≥5 opportunités structurées avec evidence+hypothesis+metric, recos en aval ont `linked_opportunity_id` populated.
5. **SKILLS_REGISTRY_GOVERNANCE.json** : 17 + 10 + 5 entrées avec type + invocation_proof + security audit, `python3 scripts/audit_skills_governance.py` exit 0.
6. **3 skills custom** : invocables via Skill tool, frontmatter conforme, mentionnés CLAUDE.md step #13.
7. **SSRF** : `http://localhost:9000/admin` → `URLValidationError`. 10 URLs test (5 valides, 5 reject) couverts.
8. **Docs réconciliés** : `find . -name "GROWTHCRO_ARCHITECTURE_V1.md"` → uniquement `_archive/`. README ligne 3+22 OK. Manifest §12 bumped.
9. **Hygiene** : `python3 scripts/lint_code_hygiene.py` exit 0 partout.
10. **Tests** : pytest pour Opportunity schema, claims_source_gate, url_validator, verdict_gate. Couverture par fixtures.
11. **12 issues GitHub fermées**, 12 commits conventional, epic GitHub fermé, worktree merged.

## Estimated Effort

- **Total** : ~80-120h dev (3-4 semaines à 1 dev temps plein, ou 1-2 semaines parallélisé avec 3-5 agents).
- **Critical path** : SSRF fix (4h) → Opportunity engine path (008→009→010 = 26h séquentiel) → Verdict Gate + Claims Gate wire (8+12h) = ~50h minimum sur le path long.
- **Parallel headroom** : 6 issues wave 1 indépendantes → grosse partie peut être parallélisée si 3-5 agents simultanés.
- **Recommandation** : exécuter wave 1 en parallèle (gain 30-50% temps), puis wave 2 séquentiel par dépendance, puis wave 3 parallèle pour wrap-up.

## Tasks Created

- [ ] 001.md - Fix SSRF crawler validation (parallel: true)
- [ ] 002.md - Archive obsolete architecture V1 doc (parallel: true)
- [ ] 003.md - Create skill `growthcro-anti-drift` (parallel: true)
- [ ] 004.md - Create skill `growthcro-prd-planner` (parallel: true)
- [ ] 005.md - Create skill `growthcro-status-memory` (parallel: true)
- [ ] 006.md - Create `SKILLS_REGISTRY_GOVERNANCE.json` + audit script (parallel: partial, depends 003-005)
- [ ] 007.md - Skills security checklist + retroactive audit 17 externals (parallel: true, depends 006)
- [ ] 008.md - `Opportunity` Pydantic schema + persistence (parallel: true)
- [ ] 009.md - Opportunity engine orchestrator deterministic (parallel: partial, depends 008)
- [ ] 010.md - Opportunity CLI + wire recos orchestrator (parallel: true, depends 009)
- [ ] 011.md - Verdict Gate aggregator in multi-judge (parallel: true)
- [ ] 012.md - ClaimsSourceGate HTML parser + wire mode_1 (parallel: true)

Total tasks: 12
Parallel tasks (wave 1): 6 — 001, 002, 003, 004, 005, 008
Sequential tasks (waves 2-3): 6 — 006, 007, 009, 010, 011, 012
Estimated total effort: 75-120h
