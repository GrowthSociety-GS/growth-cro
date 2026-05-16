# GitHub Issue Mapping — growthcro-stratosphere-p0

**Repo** : https://github.com/GrowthSociety-GS/growth-cro
**Epic issue** : [#39 - Epic: growthcro-stratosphere-p0](https://github.com/GrowthSociety-GS/growth-cro/issues/39)
**Synced** : 2026-05-16T12:43:15Z
**PRD** : [`.claude/prds/growthcro-stratosphere-p0.md`](../../prds/growthcro-stratosphere-p0.md)
**Source dossier** : [`.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md`](../../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md)

## Issue mapping (local → GitHub)

| Local file | GitHub # | Title | Wave | Parallel | Depends on | Conflicts with |
|---|---|---|---|---|---|---|
| 001.md → 40.md | [#40](https://github.com/GrowthSociety-GS/growth-cro/issues/40) | Fix SSRF crawler validation | 1 | true | — | — |
| 002.md → 41.md | [#41](https://github.com/GrowthSociety-GS/growth-cro/issues/41) | Archive obsolete architecture V1 doc | 1 | true | — | — |
| 003.md → 42.md | [#42](https://github.com/GrowthSociety-GS/growth-cro/issues/42) | Create skill `growthcro-anti-drift` | 1 | true | — | — |
| 004.md → 43.md | [#43](https://github.com/GrowthSociety-GS/growth-cro/issues/43) | Create skill `growthcro-prd-planner` | 1 | true | — | — |
| 005.md → 44.md | [#44](https://github.com/GrowthSociety-GS/growth-cro/issues/44) | Create skill `growthcro-status-memory` | 1 | true | — | — |
| 006.md → 45.md | [#45](https://github.com/GrowthSociety-GS/growth-cro/issues/45) | Create `SKILLS_REGISTRY_GOVERNANCE.json` + audit script | 2 | partial | 42, 43, 44 | — |
| 007.md → 46.md | [#46](https://github.com/GrowthSociety-GS/growth-cro/issues/46) | Skills security checklist + retroactive audit 17 externals | 3 | true | 45 | — |
| 008.md → 47.md | [#47](https://github.com/GrowthSociety-GS/growth-cro/issues/47) | `Opportunity` Pydantic schema + persistence | 1 | true | — | — |
| 009.md → 48.md | [#48](https://github.com/GrowthSociety-GS/growth-cro/issues/48) | Opportunity engine orchestrator (deterministic) | 2 | false | 47 | — |
| 010.md → 49.md | [#49](https://github.com/GrowthSociety-GS/growth-cro/issues/49) | Opportunity CLI + wire recos orchestrator | 3 | true | 48 | — |
| 011.md → 50.md | [#50](https://github.com/GrowthSociety-GS/growth-cro/issues/50) | Verdict Gate aggregator in multi-judge | 2/3 | true | — | 51 |
| 012.md → 51.md | [#51](https://github.com/GrowthSociety-GS/growth-cro/issues/51) | ClaimsSourceGate HTML parser + wire mode_1 | 2/3 | true | — | 50 |

## Waves de parallélisation

### Wave 1 — 6 issues parallèles indépendantes (start ASAP)
- #40 Fix SSRF crawler validation (S — 4h)
- #41 Archive obsolete architecture V1 doc (XS — 1h)
- #42 Create skill `growthcro-anti-drift` (S — 3h)
- #43 Create skill `growthcro-prd-planner` (S — 4h)
- #44 Create skill `growthcro-status-memory` (S — 3h)
- #47 `Opportunity` Pydantic schema + persistence (M — 6h)

### Wave 2 — 3 issues partiellement bloquées
- #45 SKILLS_REGISTRY_GOVERNANCE.json (M — 8h) — depends 42+43+44
- #48 Opportunity engine orchestrator (L — 12h) — depends 47
- #51 ClaimsSourceGate (L — 12h) — peut start indép. mais smoke evidence_ledger.json shape sur Weglot first

### Wave 3 — 3 issues wrap-up
- #46 Skills security checklist + retro audit 17 (M — 6h) — depends 45
- #49 Opportunity CLI + wire recos (M — 8h) — depends 48
- #50 Verdict Gate aggregator (M — 8h) — peut start indép. mais conflict #51 sur `mode_1_complete.py` → merge ordonné

## Conflits ordonnancement

- **#50 et #51** modifient tous deux `moteur_gsg/modes/mode_1_complete.py` :
  - #51 wire `ClaimsSourceGate` POST-impeccable, PRE-multi-judge (vers ligne ~340)
  - #50 wire `VerdictGate` POST-multi-judge (vers ligne ~400)
  - Merge séquentiel obligatoire (l'un APRES l'autre, pas en parallèle simultanée)

## Stop conditions formelles (13)

Cf. [`AUDIT_DECISION_DOSSIER_2026-05-16` §8](../../docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md#8-stop-conditions-à-respecter-pendant-limplémentation-p0).

Pendant l'exécution, **stop + demande Mathis** si :
1. Migration destructive nécessaire
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
13. Manifest §12 à bumper (commit séparé)

## Worktree

```bash
git worktree add ../epic-growthcro-stratosphere-p0 -b epic/growthcro-stratosphere-p0
```

Tout le travail des 12 issues se fait dans `../epic-growthcro-stratosphere-p0/`. Commits format : `feat(<scope>): <description> [#<github-num>]`.

## Next steps

1. Wave 1 — lancer 6 issues en parallèle via subagent-driven-development.
2. Coordination merge #50 ↔ #51 quand wave 2/3 arrive.
3. Smoke test Weglot baseline (composite Sprint 21 = 88.6%) à chaque fin de wave pour vérifier non-régression.
