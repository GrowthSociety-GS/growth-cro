# Task #26 — Skills Stratosphère S1 Install — Stream A report

**Date** : 2026-05-12
**Branch** : `task/26-skills-s1`
**Worktree** : `/Users/mathisfronty/Developer/task-26-skills-s1`
**Agent** : Claude Opus 4.7 (1M context)

---

## 1. Install status

### Skills (all PASS via `npx skills add` programmatic — sandbox NOT blocked)

| Skill bundle | Command | Status | Skills added |
|---|---|---|---|
| **Vercel `vercel-labs/agent-skills`** | `npx --yes skills add vercel-labs/agent-skills` | **PASS** | 7 skills : `vercel-react-best-practices`, `web-design-guidelines`, `vercel-composition-patterns`, `vercel-react-view-transitions`, `deploy-to-vercel`, `vercel-cli-with-tokens`, `vercel-react-native-skills` |
| **Trail of Bits `trailofbits/skills`** | `npx --yes skills add trailofbits/skills` | **PASS** | 74 skills (full suite). Essentiels actifs combo Security audit : `codeql`, `semgrep`, `variant-analysis`, `supply-chain-risk-auditor`. Note : suite split = `codeql` + `semgrep` + `semgrep-rule-creator` (pas un seul "static-analysis" skill — la suite est plus granulaire que le rapport SKILLS_STRATOSPHERE annonçait) |
| **Anthropic `webapp-testing`** | `npx --yes skills add anthropics/skills/skills/webapp-testing` | **PASS** | 1 skill : `webapp-testing` (Playwright official) |
| **`skill-creator`** (formalize) | déjà actif (`anthropic-skills:skill-creator`) | **PASS — pre-existing** | Formalisé dans BLUEPRINT.md ligne 17 table récap, verdict "MÉTA universel on-demand" |

### MCPs

| MCP | Command | Status |
|---|---|---|
| **Context7 MCP (Upstash)** | `claude mcp add context7 -- npx -y @upstash/context7-mcp` | **TO INSTALL MANUALLY BY MATHIS** — agent sandbox n'a pas la CLI `claude` (vérifié : `which claude` → not found). Aucun OAuth requis (open-source). Smoke test post-install : demander Next.js 14 + Supabase v2 → vérifier que Claude ne mentionne PAS Next.js 12 / Supabase v1. |

### Notes d'install

- Les skills sont installés via `.agents/skills/` (Codex mirror, gitignored) + `.claude/skills/` (Claude Code symlinks, **ajouté à .gitignore** dans ce sprint) + `skills-lock.json` à la racine du projet (**ajouté à .gitignore**).
- Aucune install programmatique n'a échoué — sandbox **permissive** pour `npx skills add` (≠ Task #17 où c'était bloqué).
- 74 skills Trail of Bits installés mais seuls 4 sont activés dans le combo Security audit ; les 70 autres sont disponibles **on-demand** (notamment `semgrep-rule-creator`, `differential-review`, `insecure-defaults`, `fp-check`, `sarif-parsing`, `modern-python`, `git-cleanup`, `gh-cli`).
- 7 skills Vercel installés ; 4 essentiels (cf table BLUEPRINT.md lignes 8-11) + 3 disponibles on-demand (`deploy-to-vercel`, `vercel-cli-with-tokens`, `vercel-react-native-skills`).

### Smoke tests effectués

- `ls .agents/skills/ | wc -l` → 82 skills installés (74 ToB + 7 Vercel + 1 Anthropic).
- Présence vérifiée des skills clés : `vercel-react-best-practices`, `web-design-guidelines`, `codeql`, `semgrep`, `variant-analysis`, `supply-chain-risk-auditor`, `webapp-testing`. **OK**.
- Smoke fonctionnel (invocation) hors-scope agent (nécessite session interactive avec Claude Code chargeant les skills). **À tester par Mathis** dans une nouvelle session Claude Code post-merge.

---

## 2. BLUEPRINT.md updates

### Section 1 — table récap

- **6 nouvelles entries skills installés** (lignes 8-16) : 4 Vercel + 4 Trail of Bits (sélection essentielle parmi 74) + 1 Anthropic webapp-testing.
- **1 entry méta** (ligne 17) : `skill-creator` formalisé "MÉTA universel on-demand".
- **1 démotion** (ligne 18) : `Figma Implement Design` → ON-DEMAND (slash `/figma-implement` ponctuel, retiré du combo permanent webapp_nextjs).
- Renumérotation des autres lignes (on-demand 20-24, exclus 25-29).
- 2 notes ajoutées sous la table : bundle Vercel (7 installés, 4 essentiels) et bundle Trail of Bits (74 installés, 4 essentiels).

### Section 2 — Combo packs

- **`Webapp Next.js dev`** : 4 → 5 skills max. Skills actifs : `frontend-design` + `web-artifacts-builder` + `vercel-microfrontends` + `vercel-react-best-practices` + `web-design-guidelines`. Trade-off décidé : 5 permanents + `Figma Implement Design` en on-demand. Rationale documentée (auto-fix Vercel pendant gen = zero effort post-install).
- **`Security audit`** (NEW) : 4 skills, activation pre-merge / quarterly. Skills : `codeql` + `semgrep` + `variant-analysis` + `supply-chain-risk-auditor`. Cost/latence documenté (CodeQL 5-15min). Anti-cacophonie : ne JAMAIS tourner en parallèle GSG generation ou Audit run.
- **`QA + a11y`** (NEW) : 2 skills, activation sprint QA E2E pre-deploy V28. Skills : `webapp-testing` + `web-design-guidelines`. Peut tourner en parallèle avec webapp_nextjs → total 7 ≤ 8 hard limit.

### Section 4bis (NEW) — MCPs server-level

- AD-4 documenté : MCPs ≠ Skills (JSON-RPC servers, hors compte 8 skills/session).
- 4bis.1 Context7 MCP (universel anti-hallucination, ICE 810, à installer manuellement par Mathis).
- 4bis.2 MCPs production futurs (Task #27) : Supabase, Sentry, Meta Ads, Shopify — install commands + ICE + OAuth requirements documentés.
- 4bis.3 Anti-pattern AD-5 explicite : Supabase MCP = dev only, NEVER prod.

### Section 5 — Installation procedure

- Étape 2 restructurée en 3 tiers :
  - Tier 1 — Stratosphère S1 (Task #26, installés 2026-05-12 par agent)
  - Tier 2 — Original essentiels (Task #17, à installer par Mathis si pas déjà faits)
  - Tier 3 — MCPs server-level (Task #26 partial → Task #27 complet)
- Notes critiques ajoutées : `.claude/skills/` + `skills-lock.json` gitignored, source-of-truth = ce blueprint + YAML.

---

## 3. CLAUDE.md update

Anti-pattern #12 mis à jour :
- Combo packs étendus : Audit run (≤4) · GSG generation (≤4) · Webapp Next.js dev (≤5, was ≤4) · Security audit (≤4, NEW) · QA + a11y (≤2, NEW).
- Clarification ajoutée : "**MCPs server-level (Context7, futurs Supabase/Sentry/Meta/Shopify Task #27) sont hors compte des 8 skills/session** — ils tournent en serveurs JSON-RPC au niveau Claude Code config, pas en skills."

---

## 4. WEBAPP_ARCHITECTURE_MAP.yaml update

Section `skills_integration` enrichie :
- `meta.version` : `'1.0'` → `'1.1'`, `last_updated` : `'2026-05-11'` → `'2026-05-12'`, `task_ref` updated.
- `combo_packs.webapp_nextjs` : 4 → 5 skills, ajout `vercel-react-best-practices` + `web-design-guidelines`, modules_impacted enrichis (5 microfrontends listés), trade_off_decided documenté.
- **NEW** `combo_packs.security_audit` : 4 skills, activation pre-merge/quarterly, modules_impacted listés, cost_latency + anti_cacophonie documentés.
- **NEW** `combo_packs.qa_a11y` : 2 skills, activation sprint QA E2E, combos_compatible documenté.
- `essentials` : **9 nouvelles entries** ajoutées (vercel-react-best-practices, web-design-guidelines, vercel-composition-patterns, vercel-react-view-transitions, codeql, semgrep, variant-analysis, supply-chain-risk-auditor, webapp-testing, skill-creator) avec `installed: true`, `installed_date: '2026-05-12'`, `combo`, `ice_score`, `notes`.
- `Figma Implement Design` : combo passé de `webapp_nextjs` à `'ON-DEMAND (demoted 2026-05-12, was webapp_nextjs permanent)'`.
- `anti_cacophonie_rules` : 2 règles ajoutées (security_audit isolation + MCPs hors compte).
- **NEW** `mcps_server_level` section : meta (AD-4 ref), installed[context7], pending_task_27[supabase, sentry, meta-ads, shopify].

Idempotency : `python3 scripts/update_architecture_map.py` exit 0. Re-run identique (diff stable). Section `skills_integration` 100% préservée.

---

## 5. Gates results

| Gate | Result |
|---|---|
| `python3 scripts/lint_code_hygiene.py` | **EXIT 0** · FAIL = 0 · WARN = 12 (mixed-concern signals legacy — inchangé) · 12 INFO files (pre-existing, hors-scope Task #26) · 34 INFO print-in-pipeline (Task #28 cible) |
| `python3 scripts/audit_capabilities.py` | **EXIT 0** · 231 files scanned · Orphans HIGH = **0** · Partial wired = 0 |
| `python3 SCHEMA/validate_all.py` | **EXIT 0** · 15 files validated, all passing |
| `bash scripts/parity_check.sh weglot` | **EXIT 0** (hash listing OK) |
| `bash scripts/agent_smoke_test.sh` | **EXIT 0** (pre-existing warning `score_page_type.py usage missing` legacy, hors-scope) |
| `python3 scripts/update_architecture_map.py` | **EXIT 0** · idempotent · skills_integration human-curated section préservée |

**Verdict** : tous gates verts, aucune régression. .gitignore enrichi pour gérer les artefacts locaux d'install skills.

---

## 6. Files modified

- `.claude/CLAUDE.md` (anti-pattern #12 updated)
- `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` (sections 1+2+4bis NEW+5 — v1.0 → v1.1)
- `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` (skills_integration v1.0 → v1.1 + script idempotency-induced reformat)
- `.gitignore` (added `.claude/skills/` + `skills-lock.json`)
- `.claude/epics/hardening-and-skills-uplift/updates/26/stream-A.md` (this report)

---

## 7. Pending Mathis actions

1. **Install Context7 MCP** (universel) :
   ```bash
   claude mcp add context7 -- npx -y @upstash/context7-mcp
   ```
2. **Smoke test Context7** post-install :
   - Open new Claude Code session
   - Prompt : "Generate Next.js 14 App Router server actions with Supabase v2 auth using cookies()"
   - Vérifier que Claude utilise correctement `server actions`, `createServerClient`, `cookies()` (pas Next.js 12 / Supabase v1).
3. **Smoke tests skills installés** post-merge :
   - Open new Claude Code session
   - Vérifier dans liste "Available skills" du system prompt : `vercel-react-best-practices`, `web-design-guidelines`, `codeql`, `semgrep`, `variant-analysis`, `supply-chain-risk-auditor`, `webapp-testing`, `skill-creator`.
4. **Task #27 (futur sprint)** : Supabase + Sentry + Meta Ads + Shopify MCPs (~30min OAuth flows total).

---

## 8. Commits planned

1. `chore: gitignore .claude/skills/ + skills-lock.json (Task #26 install artefacts)`
2. `docs: BLUEPRINT.md v1.0 -> v1.1 — Task #26 Stratosphère S1 install (3 new combo packs + Context7 MCP)`
3. `docs: CLAUDE.md anti-pattern #12 updated — combo packs étendus + MCPs hors compte`
4. `docs: WEBAPP_ARCHITECTURE_MAP.yaml skills_integration v1.0 -> v1.1 — Task #26 install`
5. `docs: stream-A.md report Task #26`
6. `docs: manifest §12 — add 2026-05-12 changelog for #26 skills stratosphère S1 install` (séparé, per CLAUDE.md rule)

---

**Fin du rapport Stream A Task #26**.
