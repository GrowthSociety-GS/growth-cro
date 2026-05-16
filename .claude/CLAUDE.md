# CLAUDE.md — GrowthCRO entrypoint (V26.AG)

**Lire OBLIGATOIREMENT en début de conversation.** Détail complet : [`.claude/README.md`](README.md).

## Init obligatoire (avant toute action)

1. Lire ce fichier intégralement
2. Lire [`.claude/README.md`](README.md) — index de la doctrine projet
3. Lire `README.md` racine — état actuel V26.AF/AG
4. Notion produit canonique via MCP `notion-fetch` (PAS WebFetch — Notion est une SPA) :
   - *Mathis Project x GrowthCRO Web App*
   - *Le Guide Expliqué Simplement*
5. Lire [`docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`](docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md) — plan ordonné Sprints F-L
6. Lire le plus récent `docs/state/AUDIT_TOTAL_*.md` — diagnostic
7. `python3 state.py` — état disque pipeline
8. `python3 scripts/audit_capabilities.py` + lire [`docs/state/CAPABILITIES_SUMMARY.md`](docs/state/CAPABILITIES_SUMMARY.md)
9. Skim [`memory/MEMORY.md`](memory/MEMORY.md) + [`docs/reference/GROWTHCRO_MANIFEST.md`](docs/reference/GROWTHCRO_MANIFEST.md) §12 changelog
10. Lire [`docs/doctrine/CODE_DOCTRINE.md`](docs/doctrine/CODE_DOCTRINE.md) — doctrine code projet (mono-concern, 8 axes, hard rules)
11. Lire [`docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`](docs/state/WEBAPP_ARCHITECTURE_MAP.yaml) — source-of-truth machine-readable de l'architecture webapp post-cleanup (modules + data_artefacts + pipelines). Vue humaine Mermaid : [`docs/state/WEBAPP_ARCHITECTURE_MAP.md`](docs/state/WEBAPP_ARCHITECTURE_MAP.md). Mis à jour automatiquement à chaque epic terminé via `scripts/update_architecture_map.py` (idempotent, préserve les champs human-curated).
12. **Point d'entrée prochaine session** (post-clear 2026-05-15 post Sprint 21) : Lire **[`docs/state/CONTINUATION_PLAN_2026-05-15_POST_SPRINT_21.md`](docs/state/CONTINUATION_PLAN_2026-05-15_POST_SPRINT_21.md)** EN PREMIER — récap 9 sprints 13→21 (composite final 88.6% Exceptionnel, multi-judge 85.3% 🏆, Humanlike 88.8% 🏆 sur V14b Weglot from-blank, 8 audits runtime wirés). Puis lire les 3 memory files pinned : `memory/CONTENT_INPUT_DOCTRINE.md` (hard gate fetch 6 catégories + 3 angles distincts pour tous GSGs) + `memory/FINAL_ACCEPTANCE_TEST_TODO.md` (COMPLETED 2026-05-15) + `memory/SPRINT_LESSONS.md` (24+ règles distillées). Sprint 22+ scope à confirmer avec Mathis : *"on va attaquer un énorme chantier après"*. Candidats P0 : slash command `/lp-creator-from-blank` (codifier `CONTENT_INPUT_DOCTRINE.md` en workflow exécutable) + BriefV2 `chosen_angle` field + audit gate `content_angle_freshness_check`. Candidats P1 : multi-page bundle test multi-judge / true Anthropic Skill wiring / multi-judge noise reduction (vote 3-runs). Référence historique webapp-data-fidelity ci-dessous (Wave A/B pending si Mathis veut y revenir).
    - Historique : master PRD ACTIVE [`.claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md`](../prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md) — Wave A blocking : re-migrate depuis `recos_enriched.json` (438 files, V13 riche) + `score_*.json` + debug screenshots prod ; Wave B : skill-based-architecture + Superpowers + GStack + native /review + Vercel Agent. 🔴 URGENT : rotater service_role JWT Supabase si re-déploiement (repo PUBLIC + JWT in git history).
13. **Gouvernance skills + sécurité agentique** (post epic `growthcro-stratosphere-p0` 2026-05-16) : Lire [`growthcro/SKILLS_REGISTRY_GOVERNANCE.json`](../../growthcro/SKILLS_REGISTRY_GOVERNANCE.json) (38 entries — 18 ext + 13 custom + 5 subagents + 4 runtime_heuristic + 1 archived ; chaque entrée : `type`, `invocation_proof`, `security{shell,network,env_vars,secrets,git,filesystem}`, `audit_date`, `mathis_decision_proposed`) + [`docs/reference/SKILLS_SECURITY_CHECKLIST.md`](docs/reference/SKILLS_SECURITY_CHECKLIST.md) (template + 18 audits rétroactifs). Avant tout install de skill externe nouveau : run la checklist + entrée registry + Mathis valide DROP/PIN/KEEP. **3 skills custom GrowthCRO** disponibles via Skill tool : [`growthcro-anti-drift`](skills/growthcro-anti-drift/SKILL.md) (impose CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS avant chaque issue P0/P1/P2), [`growthcro-prd-planner`](skills/growthcro-prd-planner/SKILL.md) (transforme idée → PRD + Epic + Issues atomiques avec templates), [`growthcro-status-memory`](skills/growthcro-status-memory/SKILL.md) (update docs/status/PROJECT_STATUS + NEXT_ACTIONS + CHANGELOG_AI + ADR + manifest §12 + SPRINT_LESSONS après chaque epic/sprint significatif). **Gates bloquants ajoutés** : `ClaimsSourceGate` (refuse HTML rendu avec claim sans `data-evidence-id`) + `VerdictGate` (force `🔴 Non shippable` si impeccable.passed=False OR killer_rules_violated OR impl_penalty>10pp OR n'importe quel check_gsg_*.py / SCHEMA validate exit≠0) — wirés dans `moteur_gsg/modes/mode_1_complete.py` post-impeccable et post-multi-judge. Mode `--ship-strict` raise `ClaimsSourceError` / `VerdictGateError`, mode normal logger.warning + tag dans output.

**Ne jamais coder/scorer/auditer sans ces 13 étapes ET consigne explicite Mathis.**

## Anti-patterns prouvés (à NE PLUS reproduire)

1. Mega-prompt persona_narrator >8K chars → STOP (-28pts régression V26.AA)
2. Anti-AI-slop trop agressif → page blanche défensive (V26.AF)
3. Réinventer une grille au lieu de doctrine V3.2.1
4. Ajouter sans archiver
5. Coder avant design doc validé
6. Audit sans Notion fetch
7. Industrialiser avant validation unitaire (Mathis veut perfection 1er run)
8. Fichier multi-concern (mélange prompt + API + persistence + orchestration) — split en modules mono-concern (8 axes, cf. `docs/doctrine/CODE_DOCTRINE.md`)
9. `os.environ` / `os.getenv` hors `growthcro/config.py` — toute lecture env passe par le module config
10. Archive (`_archive*`, `_obsolete*`, `*deprecated*`, `*backup*`) à l'intérieur d'un path actif — déplacer sous `_archive/` racine
11. Basename dupliqué dans des paths actifs (hors `__init__.py`, `cli.py`, et les noms canoniques AD-1 `base/orchestrator/persist/prompt_assembly`)
12. Charger >8 skills simultanés OU skills à signaux contraires (ex: `Taste Skill` + `brand-guidelines` per-client, `lp-creator` + `moteur_gsg`, `theme-factory` + Brand DNA) → cacophonie + dépassement limite Claude Code. Respecter les combo packs par contexte définis dans [`docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`](docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md) : Audit run (≤4) · GSG generation (≤4) · Webapp Next.js dev (≤5) · Security audit (≤4) · QA + a11y (≤2). **MCPs server-level (Context7, futurs Supabase/Sentry/Meta/Shopify Task #27) sont hors compte des 8 skills/session** — ils tournent en serveurs JSON-RPC au niveau Claude Code config, pas en skills.

## Règles immuables

- Qualité > vitesse, jamais de raccourci
- Dual-viewport obligatoire (Desktop + Mobile)
- Screenshots = proof (DOM rendered + PNG)
- Check before assume (grep avant d'affirmer)
- Git discipline : 1 commit isolé par changement doctrine/scorer/reco, `git status` propre avant batch
- **Pas de `git reset --hard`, `push --force`, `clean -fd`, `branch -D`, `checkout -- <file>` sans accord explicite Mathis** (perte irréversible). Préférer `git stash`, `git restore --staged`, `git reset` (mixed)
- Schemas guard-rails : `python3 SCHEMA/validate_all.py` avant/après modifs structurelles
- **Code hygiene gate** : avant tout `git add` d'un fichier source, `python3 scripts/lint_code_hygiene.py --staged` doit exit 0. Doctrine complète : [`docs/doctrine/CODE_DOCTRINE.md`](docs/doctrine/CODE_DOCTRINE.md)
- Notion = source produit (conflit code vs Notion → demander clarification, pas drift)
- Hard limit prompt persona_narrator ≤8K chars
- Pas de modif Notion sans demande explicite Mathis
- Clés API dans `.env` (gitignored), jamais en clair dans commit/note/wake-up

## Vision GrowthCRO (rappel non négociable)

Consultant CRO senior automatisé pour ~100 clients de l'agence **Growth Society** (media buying performance Meta/Google/TikTok). 8 modules : Audit Engine · Brand DNA + Design Grammar (V29+V30) · GSG (en crise V26.AF) · Webapp Observatoire V26 · Reality Layer V26.C · Multi-judge V26.D · Experiment Engine V27 · Learning Layer V28+V29 · GEO Monitor V31+.

Boucle fermée : Audit → Action → Mesure → Apprentissage → Génération → Monitoring.

Position Mathis : *"perfection dès le départ"* · *"concision > exhaustivité"* · *"avant-garde, pas best CRO B2B 2024"* · *"moat dans les data accumulées"* · *"aucun concurrent agence n'a ça"*.

## Mise à jour du manifest

Brique majeure modifiée → éditer [`docs/reference/GROWTHCRO_MANIFEST.md`](docs/reference/GROWTHCRO_MANIFEST.md) §12 dans la même conv. Commit séparé : `docs: manifest §12 — add YYYY-MM-DD changelog for <change>`.
