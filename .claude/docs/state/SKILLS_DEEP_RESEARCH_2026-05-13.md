# Skills Deep Research — 2026-05-13 (post-Wave-P2 final report)

> **Réponse à Mathis 2026-05-13** : "il y a quelques jours je t'ai demandé un deep search sur internet (Reddit, Medium etc) + tes connaissances sur les derniers skills les plus récents qui existent et pourraient être stratosphériques, tant pour ma webapp en termes de features et de design, code, règles, analyse etc, mais aussi comme skill d'analyse et compréhension stratégique de ma webapp, des process, (tel un humain), des interactions, des fonctions, des connexions, de l'architecture et du code."
>
> **Status** : Recherche menée via WebSearch + WebFetch (Firecrawl, GitHub, Medium, dev.to). Existing blueprint `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` v1.2 cross-checké pour éviter doublons.

## 🌟 TIER 1 — Stratosphériques (à installer immédiatement)

### 1. `skill-based-architecture` (WoJiSama) — **PARFAIT pour le besoin user**

Meta-skill qui transforme la doctrine éparpillée en single source of truth.

**Ce que ça fait** :
- Lit `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `README.md`, workflow docs
- Distille en `skills/<project>/` :
  - `SKILL.md` (router, ≤100 lignes)
  - `rules/` (constraints stables)
  - `workflows/` (procédures répétables)
  - `references/` (architecture notes + gotchas)
  - `docs/` (rapports + prompts)
- Crée des **thin entry shells** dans CLAUDE.md/AGENTS.md/.cursor/rules/ qui routent vers le central skill (pas de duplication)
- Compatible **cross-tool** : Claude Code + Cursor + Windsurf + Codex + Gemini consultent le même skill

**Pourquoi c'est exactement ce que Mathis demande** :
- "Compréhension stratégique de ma webapp" → ce skill lit ET structure TOUT le contexte projet
- "Process, interactions, fonctions, connexions" → distillés dans workflows/ + references/
- "Tel un humain" → single source of truth = comportement consistent cross-session
- "Architecture et code" → references/ contient l'architecture map distillée

**Install** :
```bash
git clone https://github.com/WoJiSama/skill-based-architecture.git \
  skills/skill-based-architecture
```

**Use case** :
```
Mathis: "Use skill-based-architecture to refactor the project rules."
Claude: <reads CLAUDE.md + AGENTS.md + memory/ + docs/ + creates skills/growthcro/>
```

### 2. `Superpowers` (obra/superpowers) — Multi-step development workflow

Structure les développements en plans + subagents + TDD enforcement.

**Ce que ça fait** :
- Force un plan structuré avant exécution
- Délègue à des subagents parallèles
- Test-Driven Development par défaut (red → green → refactor)
- Pattern proven pour features complexes multi-file

**Pourquoi c'est utile** :
- Mathis a noté à plusieurs reprises "industrialiser avant validation unitaire" comme anti-pattern. Superpowers force la validation unitaire dès le départ.
- Combo idéal avec ccpm pour le sprint planning.

**Install** : `npx skills add obra/superpowers`

**Status existing blueprint** : déjà listé comme "POC à tester" (Wave A Epic 5 a). 2026-05 → time to actually install + evaluate.

### 3. `GStack` (garrytan/gstack) — Full AI engineering team

Provides "office hours", design, QA, testing personas as a coherent team.

**Ce que ça fait** :
- Multiple agents personas en un seul skill
- Office hours = "junior dev quick questions" mode
- Design persona = critique de mockups
- QA persona = test scenarios + edge cases
- Testing = unit/integration tests

**Pourquoi c'est utile** :
- Mathis travaille solo, GStack simule une équipe (debug + design + QA + tests simultanés)
- Combo idéal pour debugging complexe (Server Component crash récent par exemple)

**Install** : `npx skills add https://github.com/garrytan/gstack`

## 🌟 TIER 2 — Code review & investigations (natifs Claude Code, GRATUITS)

### 4. **Native Code Review Agent** (Anthropic, 2026-04 GA)

Multi-agent PR review built into Claude Code Team/Enterprise.

**Comment l'invoquer** :
```
/review                    # full PR review
/security-review           # security focus only (déjà dispo dans skills list)
```

→ Lance **9 parallel subagents** sur PR : Linter, Code Reviewer, Security, Quality+Style, et 5 autres.

**Activation** : Déjà dispo si Claude Code Team/Enterprise. À tester sur dernière PR.

### 5. **`Vercel Agent`** (Vercel native, GA depuis 2026-Q1)

AI code reviews + production investigations.

**Capabilities** :
- Auto-review every PR Vercel
- Production investigations (anomaly detection sur logs + metrics)
- Integration GitHub native

**Activation** : Vercel Dashboard → Agent → Enable. Free tier disponible.

## 🌟 TIER 3 — Spécialisés on-demand

### 6. `Firecrawl Skill + CLI`

Web scraping + browser automation pour benchmark UX agences concurrentes + capture.

**Pourquoi utile pour GrowthCRO** :
- Benchmark UI/UX d'agences CRO concurrentes (analyze Conversion Rate Experts, Cro Metrics, etc.)
- Future : pourrait remplacer notre Playwright + BrightData stack (eval Wave A Epic 5 b POC)

**Install** : `npx -y firecrawl-cli@latest init --all --browser`

### 7. `wshobson/agents` — Multi-agent orchestration

Intelligent automation + multi-agent orchestration pour Claude Code.

**Status** : à évaluer. Peut être un compétiteur ou complément à ccpm.

### 8. `Context7 MCP` (already in Wave A Epic 5)

Real-time docs + library integration. **Anti-hallucination universel**.

**Status** : Action Mathis #1 still pending. À installer (1 min) :
```bash
claude mcp add context7 npx @upstash/context7-mcp
```

## 📊 Comparison Claude Code vs Cursor vs Windsurf (key insight 2026)

D'après research dev.to + Medium :

| Tool | Strength | Weakness | Best for |
|---|---|---|---|
| **Claude Code** | 200K context, architecture quality best | Slow vs Cursor | Complex multi-file architectural work |
| **Cursor** | Fast, embedding-based code search | ~120K effective context (incl chat), limits on large codebases | Medium-scope focused tasks |
| **Windsurf** | On-demand file reads, Memories/Skills system | Less mature than Cursor | Iterative collaborative building, massive enterprise codebases |

**Verdict** : pour GrowthCRO (architecture-heavy + multi-file refactors), Claude Code reste le bon choix. **Mais** `skill-based-architecture` rend le code accessible aux 3 outils, donc pas besoin de choisir.

## 🔍 Trouvaille bonus : "Designing CLAUDE.md correctly" (obviousworks.ch 2026)

Architecture 2026 recommended :
- **5 scopes** : `~/.claude/` (user) → `<project>/.claude/CLAUDE.md` (project) → `<dir>/CLAUDE.md` (sub-dir) → frontmatter skill (skill) → conversation (session)
- **WHAT/WHY/HOW** framework
- **7 core rules** : run /init first, stay under 200 lines, use hooks for 100% enforcement, etc.
- CLAUDE.md is advisory (~70% followed), **hooks are deterministic** for lint/test/security

**Action GrowthCRO** : notre CLAUDE.md = 99 lignes ✓ (under 200). Init step ✓ (12 obligatoires). On respect déjà la doctrine 2026. **Mais** : on n'utilise PAS de hooks deterministic. Skill bonus : ajouter `.claude/hooks/pre-commit.sh` pour enforce lint + typecheck pre-commit.

## ⚠️ Anti-pattern important découvert

**`Cursor vs Claude Code architecture`** : Claude Code génère la meilleure architecture mais est plus lent. **Pour des fixes rapides** (typo, single-file edit), Cursor est plus efficace. → Use Claude Code pour les architectures changes, Cursor pour les tweaks. Hybrid workflow.

→ Pour GrowthCRO V1 (architecture en construction), Claude Code stay. Quand stabilisé (post-V1), envisager Cursor pour daily edits.

## 📦 Recommendations finales — 3 actions concrètes

### Action 1 (P0, ~10 min) : Install `skill-based-architecture`
**Bénéfice immédiat** : single source of truth, future-proof cross-tool.

```bash
cd /Users/mathisfronty/Developer/growth-cro
git clone https://github.com/WoJiSama/skill-based-architecture.git \
  skills/skill-based-architecture
```

Puis invoke :
```
"Use skill-based-architecture to consolidate growth-cro project rules into skills/growthcro/"
```

### Action 2 (P0, ~5 min) : Use native `/review` command sur dernière PR
**Bénéfice** : 9 parallel subagents debug le code récent (10 sub-PRDs shipped).

Dans une session Claude Code : taper `/review` sur la branche main → automatic multi-agent review.

### Action 3 (P1, ~10 min) : Install `Superpowers` + `GStack` pour evaluation
**Bénéfice** : multi-step planning + AI team simulation.

```bash
npx skills add obra/superpowers
npx skills add https://github.com/garrytan/gstack
```

Run un POC sur le prochain bug fix pour évaluer KEEP/DROP (cf Wave A Epic 5 a).

## 🔄 Update SKILLS_INTEGRATION_BLUEPRINT à faire

Post-installs, bumper le blueprint à **v1.3** avec :
- 3 new skills Tier 1 (skill-based-architecture, Superpowers, GStack)
- Native /review Claude Code documented
- Vercel Agent integration documented
- Combo "Production debugging" (Sentry MCP + Claude Code /review + Vercel Agent)

## Sources consultées

- [Best Claude Code Skills 2026 — Firecrawl](https://www.firecrawl.dev/blog/best-claude-code-skills)
- [skill-based-architecture — WoJiSama](https://github.com/WoJiSama/skill-based-architecture)
- [Anthropic Code Review (InfoQ)](https://www.infoq.com/news/2026/04/claude-code-review/)
- [Vercel Code Review Agent](https://vercel.com/docs/agent/pr-review)
- [Cursor vs Windsurf vs Claude Code 2026 — dev.to](https://dev.to/pockit_tools/cursor-vs-windsurf-vs-claude-code-in-2026-the-honest-comparison-after-using-all-three-3gof)
- [Designing CLAUDE.md 2026 — obviousworks](https://www.obviousworks.ch/en/designing-claude-md-right-the-2026-architecture-that-finally-makes-claude-code-work/)
- [9 Parallel AI Agents Code Review — hamy.xyz](https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents)
- [Claude Code Sub-Agents Guide 2026 — vibecodingacademy](https://www.vibecodingacademy.ai/blog/claude-code-subagents-complete-guide)
