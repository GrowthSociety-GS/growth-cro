---
name: skill-stratosphere-2026-05-integration
description: Intégration des 3 skills stratosphériques 2026 identifiés post-deep-research (skill-based-architecture + Superpowers + GStack) + activation native /review Claude Code + Vercel Agent. Réponse au besoin user 2026-05-13 "skill d'analyse et compréhension stratégique tel un humain".
status: active
created: 2026-05-13T14:25:00Z
parent_prd: post-stratosphere-roadmap
wave: stratosphere-skills
---

# PRD: skill-stratosphere-2026-05-integration

> Sub-PRD ad-hoc en réaction au besoin user 2026-05-13 : *"skill d'analyse et compréhension stratégique de ma webapp, des process, (tel un humain), des interactions, des fonctions, des connexions, de l'architecture et du code"*.
>
> Document de recherche complet : `.claude/docs/state/SKILLS_DEEP_RESEARCH_2026-05-13.md`. Master blueprint actif : `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` v1.2 → cible v1.3 post-intégration.

## Executive Summary

Post-Wave-P0/P1/P2 (10 sub-PRDs shipped) + diagnostic webapp Vercel, le user a demandé un **deep search** des skills 2026 les plus récents pour combler le gap entre la webapp actuelle et la vision "vraiment fonctionnelle + stratégiquement comprise par l'IA".

Le research a identifié **3 skills stratosphériques** + **2 features natives gratuites** qui répondent au besoin :

1. **`skill-based-architecture`** (WoJiSama) — META-skill cross-tool qui distille toute la doctrine en `skills/<project>/` (SKILL.md + rules/ + workflows/ + references/). **C'est exactement la réponse au besoin user**.
2. **`Superpowers`** (obra) — Multi-step plans + TDD enforcement (déjà flaggé Wave A Epic 5 POC).
3. **`GStack`** (garrytan) — AI team personas (debug + design + QA + tests).
4. **Native `/review`** Claude Code (Anthropic 2026-04 GA) — 9 parallel subagents debug.
5. **Vercel Agent** (Vercel 2026 GA) — AI PR review + production investigation.

**Effort** : 4-6 heures wall-clock cumulé (4 tasks).
**Coût API** : ~$5-10 (POC runs).
**ROI attendu** : durable — single source of truth = -50% drift docs, +30% qualité code.

## Problem Statement

### Le besoin user textuel (2026-05-13)

> *"il y a quelques jours je t'ai demandé un deep search sur internet (reddit, medium etc) + tes connaissances sur les derniers skills les plus récents qui existent et pourraient être stratosphériques, tant pour ma webapp en termes de features et de design, code, règles, analyse etc, mais aussi comme skill d'analyse et compréhension stratégique de ma webapp, des process, (tel un humain), des interactions, des fonctions, des connexions, de l'architecture et du code. Et qui pourrait servir pour nous sortir de cette galère et tout débugguer, améliorer, et nous remettre sur le bon rail."*

### Pourquoi maintenant

1. **10 sub-PRDs shipped en 1 journée** (Wave P0/P1/P2 + rich-ux + SP-11) → beaucoup de code, complexité accrue. Besoin d'une vue d'ensemble strategic.
2. **Crash récent `/audits/[c]/[a]`** (RSC serialization bug fixé en `60f62a7`) montre que des bugs subtils peuvent ship sans un review multi-agent.
3. **Drift potentiel** entre `CLAUDE.md`, `AGENTS.md`, `.claude/docs/*`, `memory/`. `skill-based-architecture` consolide ce drift en single source.
4. **Solo dev** : Mathis n'a pas une équipe. GStack simule via personas. Superpowers force TDD multi-step (anti-pattern #7 "industrialiser avant validation unitaire" évité).
5. **Native features GRATUITES** non activées : `/review` Claude Code + Vercel Agent. Free money sur la table.

### Ce que ce PRD apporte

- **Compréhension stratégique IA** : single source of truth = même comportement cross-tool (Claude/Cursor/Windsurf)
- **Multi-agent review** : 9 parallel subagents debug + Vercel Agent PR review = catch des bugs subtils avant prod
- **AI team simulation** : GStack offre debug + design + QA personas pour solo dev
- **Méthodologie multi-step** : Superpowers force plans + tests + parallelism

## User Stories

### US-1 — Mathis (founder solo, "tel un humain")
*Comme founder solo qui doit comprendre l'état stratégique de sa webapp en 5 min sans relire 14 fichiers de doctrine, je veux que tout agent AI consulte un seul `skills/growthcro/` qui contient les rules + workflows + références + gotchas distillés.*

**Acceptance** :
- ✓ `skills/growthcro/` créé via skill-based-architecture
- ✓ `SKILL.md` router ≤ 100 lignes routes vers files spécifiques
- ✓ `rules/` contient les hard-rules (mono-concern, ≤800 LOC, etc.)
- ✓ `workflows/` contient les procédures (audit run, GSG run, deploy)
- ✓ `references/` contient l'architecture + gotchas
- ✓ `CLAUDE.md` + `AGENTS.md` devenus des thin entry shells (5-15 lignes) qui pointent vers `skills/growthcro/`

### US-2 — Future Mathis (cross-tool team)
*Si demain je ajoute un consultant Growth Society qui utilise Cursor (pas Claude Code), je veux que son agent IA consulte le même skill source-of-truth que mon Claude Code, sans redondance.*

**Acceptance** :
- ✓ `.cursor/rules/growthcro.mdc` créé en thin shell pointant vers `skills/growthcro/`
- ✓ Tested : Cursor agent répond cohérent avec mon Claude Code session
- ✓ Update doctrine dans `skills/growthcro/` propagée instantanément aux deux agents

### US-3 — Mathis (debug strategic comme une équipe)
*Comme dev solo qui ship 10 sub-PRDs/jour, je veux un AI team (debug + design + QA) qui review le code récent pour catcher les bugs subtils avant production.*

**Acceptance** :
- ✓ Native `/review` Claude Code launched sur les commits récents `fdee1af..60f62a7`
- ✓ 9 parallel subagents report (Linter, Code Reviewer, Security, Quality+Style, etc.)
- ✓ Min 3 bugs/improvements identifiés (au-delà du RSC crash déjà fixé)
- ✓ Vercel Agent activated → review auto futures PRs

### US-4 — Mathis (multi-step plan TDD)
*Comme dev qui veut éviter "industrialiser avant validation unitaire" (anti-pattern #7), je veux que Superpowers force un plan + tests + parallelism avant chaque feature.*

**Acceptance** :
- ✓ Superpowers installed
- ✓ POC : nouvelle feature développée via Superpowers (plan → tests → impl → parallelism)
- ✓ Comparaison qualitative vs développement direct sans Superpowers
- ✓ Verdict KEEP/DROP documenté

## Functional Requirements

### Task Breakdown (4 tasks)

#### T001 — Install + Run `skill-based-architecture` (P0)
**Effort** : S, 30-45 min
**Files** :
- `skills/skill-based-architecture/` (NEW via `git clone`)
- `skills/growthcro/` (NEW via meta-skill run) :
  - `SKILL.md` router ≤ 100 lignes
  - `rules/` (hard rules from CLAUDE.md + memory + doctrine)
  - `workflows/` (audit run, GSG run, deploy, dev local)
  - `references/` (architecture map + gotchas + V26.AF anti-patterns)
  - `docs/` (rapports + prompts)
- Refactor `CLAUDE.md` + `AGENTS.md` en thin entry shells (5-15 lignes routing vers `skills/growthcro/`)
- (Optional) `.cursor/rules/growthcro.mdc` thin shell (V2 si Mathis ajoute Cursor)

**Steps** :
1. `git clone https://github.com/WoJiSama/skill-based-architecture.git skills/skill-based-architecture`
2. Invoke skill : `"Use skill-based-architecture to consolidate growth-cro project rules into skills/growthcro/"`
3. Verify structure créée
4. Manually edit `CLAUDE.md` to thin shell pointing to `skills/growthcro/`
5. Test : ouvrir une nouvelle session Claude Code, demander une question sur l'architecture → vérifier qu'il route vers `skills/growthcro/`

**Acceptance** :
- [ ] `skills/growthcro/` créé avec SKILL.md + 4 sub-dirs
- [ ] CLAUDE.md ≤ 30 lignes (thin shell)
- [ ] Cohérence : ce qui était dans memory/docs/reference/state est tout référencé dans skills/growthcro/
- [ ] 0 duplication de règles (pas la même règle dans 2 endroits)
- [ ] Test nouvelle session : agent connaît la doctrine sans lire les 12 init steps explicites

#### T002 — Install + POC `Superpowers` (P1)
**Effort** : M, 1-2h
**Files** :
- `~/.claude/skills/obra-superpowers/` (NEW via `npx skills add`)
- `.claude/docs/state/SUPERPOWERS_POC_2026-05-13.md` (NEW, eval report)

**Steps** :
1. `npx skills add obra/superpowers`
2. Choose POC scope : un sub-PRD futur small (e.g., `webapp-clients-edit-quick-fix`)
3. Invoke : `"Use Superpowers to plan + execute <scope>"`
4. Measure :
   - Plan quality (présence d'objectifs + AC + tests upfront)
   - TDD adherence (tests écrits AVANT implémentation)
   - Parallelism efficiency (subagents utilisés correctement)
5. Compare vs développement direct (subjective)
6. Verdict KEEP/DROP

**Acceptance** :
- [ ] Superpowers installed
- [ ] 1 POC sub-PRD exécuté avec Superpowers
- [ ] Eval report écrit (≥ 300 mots)
- [ ] Verdict explicite (KEEP / DROP / KEEP-WITH-CAVEATS)

#### T003 — Install + POC `GStack` (P1)
**Effort** : M, 1-2h
**Files** :
- `~/.claude/skills/gstack/` (NEW via `npx skills add`)
- `.claude/docs/state/GSTACK_POC_2026-05-13.md` (NEW, eval report)

**Steps** :
1. `npx skills add https://github.com/garrytan/gstack`
2. Choose POC : "Use GStack QA persona to review the recent FR-1..SP-11 PRs"
3. Measure :
   - Bugs found vs single-agent review
   - Design feedback quality
   - Testing scenarios proposés
4. Compare vs native /review Claude Code (T004)
5. Verdict KEEP/DROP

**Acceptance** :
- [ ] GStack installed
- [ ] 1 POC review exécuté sur PRs récents
- [ ] Eval report écrit
- [ ] Verdict explicite

#### T004 — Native `/review` + Vercel Agent activation (P0)
**Effort** : S-M, 30-60 min
**Files** :
- `.claude/docs/state/CODE_REVIEW_NATIVE_2026-05-13.md` (NEW, findings + fixes)
- (Vercel Dashboard, no local file) : Vercel Agent enabled

**Steps** :
1. Native `/review` :
   - Run `/review` dans Claude Code session sur les commits `fdee1af..60f62a7` (Wave P2 + SP-11 + RSC fix)
   - 9 parallel subagents : Linter, Code Reviewer, Security, Quality+Style, etc.
   - Document findings : top 10 issues/improvements identified
   - Fix top 3 si quick wins (sinon flag pour follow-up)
2. Vercel Agent :
   - Go to https://vercel.com/tech-4696s-projects/growth-cro → Agent tab
   - Enable "AI PR Review" + "Production Investigation"
   - Configure trigger : every PR + production anomaly
   - Test : open a test PR or simulate anomaly
3. Document Vercel Agent activation in CONTINUATION_PLAN_2026-05-14

**Acceptance** :
- [ ] `/review` run + 10 findings documented
- [ ] Top 3 quick wins fixed (commits separated)
- [ ] Vercel Agent enabled + tested
- [ ] Update SKILLS_INTEGRATION_BLUEPRINT.md to v1.3 with both natives documented

## Non-Functional Requirements

### Doctrine
- Skill cap respect : skill-based-architecture = META (hors compte), Superpowers + GStack on-demand
- Combo packs blueprint v1.2 préservés (Audit run, GSG generation, Webapp Next.js dev, Security audit, QA+a11y)
- Code doctrine inchangé (≤ 800 LOC, mono-concern, 8 axes)
- Hard rules immuables (V26.AF persona_narrator ≤ 8K chars, V3.2.1, etc.)

### Performance
- skill-based-architecture run : ≤ 5 min wall-clock (lit ~14 fichiers doctrine + génère structure)
- Native /review : ≤ 3 min pour les 10-15 commits récents
- Vercel Agent : 0 overhead (cloud-side)

### Sécurité
- skill-based-architecture clone : depuis GitHub public (low risk, code-read)
- Superpowers + GStack : `npx skills add` = sandboxed
- Native /review : utilise Claude Code identity (déjà autorisé)
- Vercel Agent : OAuth Vercel (déjà connecté)

### Documentation
- Eval reports T001/T002/T003/T004 dans `.claude/docs/state/`
- BLUEPRINT v1.3 update post-intégration
- MANIFEST §12 changelog 2026-05-13

## Success Criteria

### Globaux
- [ ] T001 : `skills/growthcro/` produit + CLAUDE.md devient thin shell + test cross-session passé
- [ ] T002 : Superpowers verdict KEEP/DROP avec eval report
- [ ] T003 : GStack verdict KEEP/DROP avec eval report
- [ ] T004 : /review run + 3+ improvements appliqués + Vercel Agent enabled
- [ ] BLUEPRINT.md v1.3 published

### Métriques qualitatives
- [ ] Nouvelle session Claude Code : agent répond "what's the doctrine for X?" sans devoir relire les 12 init steps
- [ ] Drift CLAUDE.md ↔ AGENTS.md ↔ docs/ supprimé (single source via skills/growthcro/)
- [ ] Au moins 3 bugs détectés par /review + Vercel Agent (au-delà des erreurs visibles)

### Mathis validation
- [ ] Mathis confirme "skill-based-architecture = oui c'est ça que je voulais"
- [ ] Mathis review les 3 eval reports POC (Superpowers, GStack, /review)
- [ ] Décision finale install KEEP/DROP par skill

## Constraints & Assumptions

### Constraints
- Pas de install lourd (>500 MB) — tous les 3 skills sont des markdown + scripts légers
- Pas de modification de skills déjà installés (frontend-design, vercel-react-best-practices, etc.)
- Pas de break des combo packs v1.2
- skill-based-architecture est META — ne consomme PAS un slot dans les 8 skills/session
- Pas de modification de la doctrine V3.2.1 / V3.3 / V26.AF

### Assumptions
- skill-based-architecture run correct sur growth-cro repo (peut nécessiter ajustement format CLAUDE.md)
- Native /review Claude Code disponible (Team/Enterprise plan ; sinon downgrade gracieux)
- Vercel Agent disponible sur free tier OR Pro plan (à confirmer pricing)
- Mathis disponible ~30 min pour validation finale (T001 verification + verdicts)

## Out of Scope

### V1
- Pas de Cursor / Windsurf install (Claude Code reste primary tool)
- Pas de migration vers `wshobson/agents` (eval séparée si besoin V2)
- Pas de retrait des skills installés v1.2 (sauf si clear overlap découvert)
- Pas de hooks deterministic (CLAUDE.md doctrine fix V2 si needed)
- Pas de Firecrawl install (on-demand, hors scope skills strategic)

### V2+
- Cross-tool deployment (`.cursor/rules/growthcro.mdc` thin shell) — quand Mathis ajoute Cursor
- Hooks deterministic (`.claude/hooks/pre-commit.sh`) pour lint + typecheck pre-commit
- Skill packaging de growth-cro pipelines en skill externalisable (use case skill-creator)

## Dependencies

### Externes (humaines)
- Mathis ~30 min validation finale (T001 cross-session test + 3 verdicts)
- Mathis OAuth Vercel Agent (déjà connecté)

### Externes (techniques)
- Claude Code Team/Enterprise (pour native /review)
- Vercel Free tier ou Pro (pour Vercel Agent — to confirm)
- Node.js + npx (pour skills add)
- Git (pour clone meta-skill)
- ~50 MB disk space cumul

### Internes
- main HEAD `60f62a7` (RSC fix shipped)
- `.claude/docs/state/SKILLS_DEEP_RESEARCH_2026-05-13.md` (référence)
- `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` v1.2 (existing)
- Tous les CLAUDE.md / memory / docs / reference (input meta-skill)

### Sequencing
- T001 (skill-based-architecture) blocking pour T002 + T003 ? Non — indépendants
- T004 (/review + Vercel Agent) parallelable avec tous
- Ordre recommandé : T001 → T004 (en parallel) → T002 → T003 (parallel)

```
P0 critical path :
  T001 skill-based-architecture (30-45 min)  ┐
  T004 native /review + Vercel Agent (30-60 min)  ┘ parallel

P1 evaluation :
  T002 Superpowers POC (1-2h)  ┐
  T003 GStack POC (1-2h)       ┘ parallel après P0

Total wall-clock : ~3-4h avec parallel
```

---

## Plan d'exécution session-par-session

### Session 1 — Foundation (T001 + T004 parallel)
- 1 agent foreground T001 (skill-based-architecture, ~45 min)
- En parallel : Mathis enable Vercel Agent dashboard (5 min) + run /review Claude Code session (30 min)
- Commit isolé `feat(skills): integrate skill-based-architecture + native /review findings (stratosphere 2026-05)`

### **GATE A — Mathis verification T001**
- Cross-session test : ouvrir nouveau Claude Code, demander question doctrine → check si agent route vers `skills/growthcro/`
- ✅ ship Session 2 OR 🔁 fix gaps

### Session 2 — Evaluation (T002 + T003 parallel)
- 2 agents background : Superpowers POC + GStack POC
- 2 eval reports
- Verdicts KEEP/DROP

### Session 3 — Update BLUEPRINT + Continuation Plan
- Bump BLUEPRINT.md v1.2 → v1.3
- Update CONTINUATION_PLAN_2026-05-14 avec recos finales
- Commit `chore(blueprint): v1.3 + skills stratosphere integration done`

---

## Notes finales

Ce sub-PRD est la réponse directe au besoin user 2026-05-13 sur le deep search skills stratosphériques. Le research était attendu "depuis quelques jours" — on le fait maintenant + on l'exécute.

**Bénéfice attendu** :
1. **Strategic understanding** (skill-based-architecture) — single source of truth cross-tool
2. **Automated debugging** (/review + Vercel Agent) — bugs catch avant prod
3. **AI team simulation** (GStack) — debug + design + QA en personas
4. **Multi-step planning** (Superpowers) — TDD enforcement, anti anti-pattern #7

**Position rappel Mathis** : *"perfection dès le départ"* · *"concision > exhaustivité"* · *"avant-garde, pas best CRO B2B 2024"*. Ces 3 skills s'alignent : avant-garde 2026, single source = concision, automated review = perfection.
