# Execution Plan — Wave 1 (6 issues parallèles)

> **Quand reprendre cette session** : nouvelle conversation Claude Code, démarrée DEPUIS ce worktree (`/Users/mathisfronty/Developer/epic-growthcro-stratosphere-p0/`).
>
> **NE PAS** lancer Wave 1 depuis le main worktree (`/Users/mathisfronty/Developer/growth-cro/`) — tu écraserais l'état main.

## Where you are

```
Worktree    : /Users/mathisfronty/Developer/epic-growthcro-stratosphere-p0/
Branch      : epic/growthcro-stratosphere-p0
Base commit : 6ad22de (sync GitHub URLs back to local frontmatter)
PRD         : .claude/prds/growthcro-stratosphere-p0.md
Epic        : .claude/epics/growthcro-stratosphere-p0/epic.md
Tasks       : .claude/epics/growthcro-stratosphere-p0/40-51.md
Mapping     : .claude/epics/growthcro-stratosphere-p0/github-mapping.md
Dossier     : .claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md
GitHub Epic : https://github.com/GrowthSociety-GS/growth-cro/issues/39
```

## Init obligatoire (à chaque nouvelle session)

Cf. `.claude/CLAUDE.md` "Init obligatoire" (12 étapes + step #13 si skill `growthcro-anti-drift` créé après Wave 1).

Lecture minimale pour Wave 1 :
1. Ce fichier (EXECUTION_PLAN_WAVE_1.md)
2. `.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md` §6 P0 + §8 Stop conditions + §9 Prompt impl
3. `.claude/epics/growthcro-stratosphere-p0/epic.md`
4. `.claude/epics/growthcro-stratosphere-p0/github-mapping.md`
5. `.claude/docs/doctrine/CODE_DOCTRINE.md` (8 axes, hard rules)
6. Le task file de l'issue qu'on attaque (40.md, 41.md, etc.)

## Wave 1 — 6 issues à coder en parallèle

| # | File | Title | Effort | Scope (1 ligne) |
|---|---|---|---|---|
| **#40** | `40.md` | Fix SSRF crawler validation | 4h | Nouveau module `growthcro/capture/url_validator.py` + wire dans orchestrator + cli + tests pytest 10 URLs |
| **#41** | `41.md` | Archive obsolete architecture V1 doc | 1h | `git mv architecture/GROWTHCRO_ARCHITECTURE_V1.md _archive/architecture_pre_d1a/` + update README ligne 3 + 22 + manifest §12 |
| **#42** | `42.md` | Create skill `growthcro-anti-drift` | 3h | `.claude/skills/growthcro-anti-drift/SKILL.md` avec format CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS |
| **#43** | `43.md` | Create skill `growthcro-prd-planner` | 4h | `.claude/skills/growthcro-prd-planner/SKILL.md` + 4 templates (PRD/Epic/Issue/Out-of-scope) CCPM-aware + GrowthCRO opinionated |
| **#44** | `44.md` | Create skill `growthcro-status-memory` | 3h | `.claude/skills/growthcro-status-memory/SKILL.md` updates PROJECT_STATUS + NEXT_ACTIONS + CHANGELOG_AI + ADR + manifest §12 + SPRINT_LESSONS |
| **#47** | `47.md` | `Opportunity` Pydantic schema + persistence | 6h | `growthcro/opportunities/` package mono-concern + `growthcro/models/opportunity_models.py` + tests pytest |

**Total Wave 1** : ~21h dev solo / ~5-7h parallélisé 3 agents.

**Aucune dépendance entre ces 6** → peuvent être codées strictement en parallèle.

## Modes d'exécution

### Mode A — Subagent-driven-development (1 session, 3 agents Task parallèles)

Dans une nouvelle session Claude Code lancée depuis ce worktree :

```
/subagent-driven-development

Worktree: ../epic-growthcro-stratosphere-p0 (current)
Branch: epic/growthcro-stratosphere-p0

Dispatch 3 agents en parallèle (max 5 concurrent CCPM recommandation) :
- Agent 1 (general-purpose, fast) : issues #40 + #41 (security + archive = scope sécurité/docs)
- Agent 2 (general-purpose) : issues #42 + #43 + #44 (3 skills custom = scope gouvernance)
- Agent 3 (general-purpose) : issue #47 (Opportunity schema = scope code)

Pour chaque agent :
- Read its assigned task file (40.md, 41.md, etc.)
- Apply anti-drift protocol (CURRENT ISSUE / IN SCOPE / etc. — see growthcro-anti-drift skill, or use checklist from .claude/CLAUDE.md)
- Code + tests
- python3 scripts/lint_code_hygiene.py --staged exit 0 obligatoire
- Commit conventional `feat/fix/docs(<scope>): ... [#<num>]`
- Push to epic/growthcro-stratosphere-p0
- Update local task file frontmatter : status: closed
- Post comment on GitHub issue : "Closed: <commit SHA>"
```

### Mode B — CCPM /epic-start (1 session, séquentiel)

```
/ccpm

Start working on epic growthcro-stratosphere-p0 from worktree.
Issues in order : 40 → 41 → 42 → 43 → 44 → 47 (Wave 1 sequential).
For each issue : analyze, code, test, commit, close, next.
```

### Mode C — Manuel 1 issue à la fois

```
cd /Users/mathisfronty/Developer/epic-growthcro-stratosphere-p0
# Read task file
cat .claude/epics/growthcro-stratosphere-p0/40.md
# Code + test + commit
# git push origin epic/growthcro-stratosphere-p0
# gh issue close 40 -c "Closed: <commit SHA>"
```

## Stop conditions (13)

À chaque issue, l'agent doit s'arrêter et demander Mathis si :

1. Migration destructive (DB schema change, `git mv` massif hors scope)
2. Secret détecté en clair (commit, log, comment)
3. Contradiction produit non tranchée
4. Skill externe requis (audit P0.6 = rétroactif seul)
5. Sortie LLM critique non validée Pydantic v2
6. Claim rendable sans preuve
7. Fichier hors scope de l'issue à toucher
8. LOC dépassé (>300 fichier signal, >800 fail)
9. Gate critique échoue (régression Weglot baseline)
10. `lint_code_hygiene.py --staged` exit != 0
11. Anti-pattern CLAUDE.md #1-12 triggered
12. Doctrine V3.2.1 à modifier (= Mathis review V3.3)
13. Manifest §12 à bumper (commit séparé `docs: manifest §12 — ...`)

## Smoke test après Wave 1

Avant de passer à Wave 2 :

```bash
# Lint global
python3 scripts/lint_code_hygiene.py
# Should exit 0

# Schemas
python3 SCHEMA/validate_all.py
# Should exit 0

# Tests Wave 1
pytest tests/capture/test_url_validator.py -v
pytest tests/opportunities/ -v
# Should all pass

# Smoke pipeline existing (no regression)
python3 -m growthcro.cli.capture_full https://www.weglot.com weglot saas --page-type home
# Should succeed (Weglot baseline)

# Audit capabilities to make sure we didn't drift
python3 scripts/audit_capabilities.py
cat .claude/docs/state/CAPABILITIES_SUMMARY.md
# Should show new modules wired

# Skills custom test
# In new Claude Code session, type "/growthcro-anti-drift" — skill should be detected
```

## Acceptance Wave 1 (DoD)

- [ ] 6 issues GitHub fermées (#40, #41, #42, #43, #44, #47)
- [ ] 6 commits conventional dans `epic/growthcro-stratosphere-p0`
- [ ] Local task files marked `status: closed`
- [ ] `python3 scripts/lint_code_hygiene.py` exit 0
- [ ] `python3 SCHEMA/validate_all.py` exit 0
- [ ] Smoke Weglot pipeline OK (pas de régression baseline 88.6%)
- [ ] Skills custom invocables (test taper `/growthcro-anti-drift` en nouvelle session)
- [ ] README ligne 3 + 22 updates committed
- [ ] `architecture/GROWTHCRO_ARCHITECTURE_V1.md` archivé sous `_archive/architecture_pre_d1a/`
- [ ] Manifest §12 bumped (commit séparé)

## Next after Wave 1

→ `EXECUTION_PLAN_WAVE_2.md` (à créer post Wave 1 succès)

Wave 2 = 3 issues : #45 Skill Registry Governance (depends #42+#43+#44), #48 Opp engine (depends #47), #51 ClaimsSourceGate (indép. mais conflicts #50).

Effort : ~32h dev solo.
