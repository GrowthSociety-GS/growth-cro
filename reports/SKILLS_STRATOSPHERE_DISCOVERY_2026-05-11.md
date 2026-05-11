# Skills Stratosphère Discovery — 2026-05-11

> **Mission B** : recherche profonde web pour identifier des skills/MCPs/tools manquants au stack GrowthCRO.
> **Méthodologie** : 12 web searches + WebFetch ciblés sur sources canoniques (Anthropic, Vercel labs, Trail of Bits, skills.sh, mcpservers.org, github.com/topics/claude-skill, Medium, dev.to).
> **Filtres appliqués** : compatibilité avec `SKILLS_INTEGRATION_BLUEPRINT.md`, unique value vs existant, no signaux contraires (Brand DNA per-client, GSG canonique, anti-mega-prompt V26.AF), maintenance active 2026, ROI install/usage.
> **Date sources consultées** : toutes 2026-04 à 2026-05 sauf mention.

---

## Executive Summary

| Catégorie | Count | Notes |
|---|---:|---|
| **Skills/MCPs evaluated** | 28 | issus de 12 sources Web |
| **Must install (stratosphère)** | **6** | Vercel `react-best-practices`, Vercel `web-design-guidelines`, Trail of Bits `static-analysis`, Anthropic `webapp-testing`, Anthropic `skill-creator`, Context7 MCP |
| **Interesting to test** | **5** | obra `superpowers`, `firecrawl` skill, `a11y-mcp`, GA4 MCP, `logfire`/structured-logging skill |
| **MCP servers production-ready** | **5** | Supabase MCP, Meta Ads MCP (official), Shopify MCP, Sentry MCP, PostHog MCP |
| **Excluded / False positives** | **7** | Superpowers méthodologie, Apify+Firecrawl doublon, Stripe (out of scope), Notion (déjà), Linear/Jira (CCPM remplace), Skill Creator déjà-disponible, Browser-use (web-testing remplace) |

### Top 5 stratosphère recommandées (ranked by ICE)

1. **Vercel `react-best-practices`** — ICE 9×10×10 = **900** — install command 1-liner, transformative pour Epic #6 webapp V28 (70 règles React/Next.js perf).
2. **Trail of Bits `static-analysis`** — ICE 9×10×8 = **720** — CodeQL+Semgrep, comble la lacune `bandit` → niveau professionnel.
3. **Context7 MCP** — ICE 9×10×9 = **810** — élimine hallucinations API outdated (Next.js 14/Supabase/Anthropic SDK). Sweet spot anti-régression.
4. **Vercel `web-design-guidelines`** — ICE 8×10×9 = **720** — 100+ règles a11y+perf+UX, complète Impeccable côté webapp V28.
5. **Anthropic `webapp-testing` (Playwright skill)** — ICE 8×10×9 = **720** — Playwright official Anthropic, base de QA webapp V28.

---

## Section 1 — Must install (stratosphère candidates)

### 1.1 — Vercel `react-best-practices`

- **Source** : `https://github.com/vercel-labs/agent-skills` · `https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices` (accessed 2026-05-11)
- **Category** : devops / frontend perf
- **What it does** : 70 règles encodées par Vercel sur 10 ans React/Next.js perf. 8 catégories (async patterns, bundle size, server-side caching, client-side data fetching, re-render optimization, rendering performance, JS efficiency, advanced patterns). Quand l'agent voit cascade useEffect ou heavy client imports → suggère fix automatique. Exemples : "Import directly from source files instead of barrel files to avoid loading thousands of unused modules", "Instead of awaiting data in async components before returning JSX, use Suspense boundaries".
- **Why stratosphérique for us** :
  - Cible directe Epic #6 `webapp-v28-nextjs-migration` (cf `webapp-stratosphere.md` FR-6) — 5 microfrontends Next.js 14 (`audit-app`, `reco-app`, `gsg-studio`, `reality-monitor`, `learning-lab`)
  - Le knip baseline montre déjà 12 deps Supabase "deferred wiring" — le risque de barrel-import / async-await waterfall est haut sur du Next.js scaffold récent
  - Auto-applique fixes pendant gen — zéro effort post-install
  - Performance < 2s target webapp V28 (NFR `Performance` PRD) → ce skill est l'outil naturel pour atteindre
- **Integration recommendation** : ajouter au **combo "Webapp Next.js dev"** existant (déjà 4 skills max : frontend-design + web-artifacts-builder + vercel-microfrontends + Figma). **Action** : remplacer `Figma Implement Design` (optionnel) par `vercel-react-best-practices` quand pas de design Figma, OU augmenter à 5 skills pour les sprints lourds.
- **Install command** : `npx skills add vercel-labs/agent-skills` (active aussi `web-design-guidelines`, `composition-patterns`, `react-view-transitions`).
- **Risk / open questions** : la limite Claude Code de 8 skills max nous force à choisir. Recommandation : passer `Figma Implement Design` en on-demand (chargé via `/figma-implement` ponctuellement), ajouter Vercel React BP en permanent du combo webapp.
- **ICE score** : impact **9** (touche tout le futur webapp V28) / confidence **10** (Vercel publié, 70 règles concrètes) / ease **10** (install 1-liner, auto-applique). **ICE = 900**.

### 1.2 — Vercel `web-design-guidelines`

- **Source** : `https://github.com/vercel-labs/agent-skills` · `https://skills.sh/vercel-labs/agent-skills/web-design-guidelines` (accessed 2026-05-11)
- **Category** : design / a11y / UX
- **What it does** : audite le code généré contre 100+ règles a11y + perf + UX. WCAG 2.1 AA compliance, forms, animation, interaction patterns, semantic HTML. Détecte les générateurs AI qui produisent du dark-pattern ou des inputs sans label.
- **Why stratosphérique for us** :
  - **Comble la lacune webapp V28 a11y** : on n'a pas de skill a11y dans nos 8 essentiels actuels (cf `SKILLS_INTEGRATION_BLUEPRINT.md` § Combo webapp).
  - Complémentaire à `Impeccable` (côté GSG) — celui-ci 200 anti-patterns visuels, Vercel 100+ a11y+perf+UX. **Pas de doublon** car cibles différentes (GSG vs webapp Next.js).
  - GrowthCRO consulting CRO ⇒ a11y compliance est un argument commercial pour Growth Society
  - Doctrine v3.2.1 a un pilier `Accessibility` (axe pillar dans `playbook/bloc_3_v3.json`) — ce skill alimentera la doctrine V3.3 (Epic #18 mutualisé).
- **Integration recommendation** : combo "Webapp Next.js dev" (paquet Vercel — vient gratuit avec `react-best-practices`).
- **Install command** : (inclus dans `vercel-labs/agent-skills` — déjà installé via 1.1)
- **Risk / open questions** : risque de signaux contraires avec `brand-guidelines` per-client si Vercel impose des règles design rigides. **Mitigation** : `web-design-guidelines` n'impose pas de parti pris visuel (couleurs/typos) → reste a11y/perf/UX neutre. Compatible.
- **ICE score** : impact **8** (a11y argument commercial + Doctrine V3.3) / confidence **10** / ease **9**. **ICE = 720**.

### 1.3 — Trail of Bits `static-analysis` skill suite

- **Source** : `https://github.com/trailofbits/skills` (2,439 stars, dernière maj février 2026) — accessed 2026-05-11
- **Category** : security / code audit
- **What it does** : 17 skills sécurité incl. `static-analysis` (CodeQL + Semgrep + SARIF parsing), `differential-review`, `variant-analysis`, `supply-chain-risk-auditor`, `insecure-defaults`, `fp-check` (false-positive verification), `semgrep-rule-creator`.
- **Why stratosphérique for us** :
  - Notre audit `bandit` a flag 192 issues dont 2 vrais MEDIUM (SQL injection `growthcro/reality/google_ads.py:71` + `skills/site-capture/scripts/reality_layer/google_ads.py:70`, XML untrusted `discover_pages_v25.py:125`).
  - Trail of Bits = standard industriel security research. CodeQL+Semgrep trouve des classes de vulnérabilités que bandit rate (cross-file taint analysis, custom rules per-codebase).
  - **`variant-analysis`** : trouve les patterns vulnérables identiques sur tout le codebase → utile pour absorber les 2 instances de SQL injection google_ads en une passe (vs fix manuel x 2).
  - **`supply-chain-risk-auditor`** : critique pour les 73 TS files webapp/ + dependencies Supabase/Vercel/Anthropic Python SDK.
- **Integration recommendation** : nouveau combo "Security audit" (≤ 4 skills) :
  - `static-analysis` (Trail of Bits)
  - `variant-analysis` (Trail of Bits)
  - `supply-chain-risk-auditor` (Trail of Bits)
  - éventuellement `Impeccable` côté visuel/code
  - **Activation** : avant chaque merge majeur (Epic complete) ou trimestriellement
- **Install command** : `/plugin marketplace add trailofbits/skills` puis `/plugin menu` pour sélectionner les 4 skills.
- **Risk / open questions** : CodeQL build database peut prendre 5-15min selon taille du codebase — long-running gate. Bon pour quarterly/pre-merge, pas pre-commit.
- **ICE score** : impact **9** (production security niveau pro) / confidence **10** (Trail of Bits) / ease **8** (setup CodeQL DB). **ICE = 720**.

### 1.4 — Anthropic `webapp-testing` (Playwright official skill)

- **Source** : `https://github.com/anthropics/skills/tree/main/skills/webapp-testing` · `https://mcpservers.org/agent-skills/anthropic/webapp-testing` (accessed 2026-05-11)
- **Category** : QA / browser automation
- **What it does** : toolkit Anthropic officiel pour tester des webapps locales via Playwright. Vérifie frontend, capture screenshots, debug UI, navigate forms, capture browser logs. Skill maintenu par Anthropic.
- **Why stratosphérique for us** :
  - Webapp V28 (Epic #6) aura 5 microfrontends Next.js → besoin urgent de tests E2E systématiques
  - Existant : `playwright.config.ts` déjà en place dans `webapp/` mais aucun test E2E écrit
  - Couplé à Playwright MCP (40+ tools) pour orchestration agentic
  - **Dual-viewport obligatoire** (CLAUDE.md règle immuable) + screenshots proof — ce skill est l'outil naturel
  - Compatible avec notre `tests/e2e/` actuel (Playwright déjà install)
- **Integration recommendation** : combo "Webapp Next.js dev" (ajout 5ème skill optionnel) OU nouveau combo "QA + a11y" : `webapp-testing` + `web-design-guidelines` + `a11y-mcp` + `frontend-design`.
- **Install command** : `/plugin install webapp-testing@anthropic-agent-skills` (skill officiel inclus dans le repo `anthropics/skills`).
- **Risk / open questions** : aucun connu. Anthropic-maintained, drop-in.
- **ICE score** : impact **8** / confidence **10** / ease **9**. **ICE = 720**.

### 1.5 — Anthropic `skill-creator`

- **Source** : `https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md` (accessed 2026-05-11)
- **Category** : meta / skill development
- **What it does** : 4 agents composables (Executor / Grader / Comparator / Analyzer) pour scaffolder un nouveau skill, écrire les tests, lancer les évaluations, comparer A/B des versions de skill, suggérer améliorations. Format SKILL.md officiel.
- **Why stratosphérique for us** :
  - **Note** : déjà disponible dans notre session système (`anthropic-skills:skill-creator` listé dans le bootstrap).
  - **Action** : intégrer formellement dans `SKILLS_INTEGRATION_BLUEPRINT.md` comme "meta-skill universel disponible on-demand".
  - **Use case stratégique** : créer nos propres skills internes Growth Society (ex : `cro-doctrine-v3-3-applier` qui encapsule les playbooks `bloc_*_v3.json` comme skill réutilisable cross-agent). Cela rendrait notre **moat doctrine portable** entre Claude Code / Codex / autres agents.
  - Permet de packager les 8 modules GrowthCRO en skills externalisables (vente future / réutilisation Growth Society).
- **Integration recommendation** : **déjà actif** — formaliser dans blueprint section 1 (table récapitulative) avec verdict "MÉTA — universel".
- **Install command** : déjà installé.
- **Risk / open questions** : éviter de créer trop de skills internes qui se chevauchent avec notre doctrine V3.2.1 (un skill = un usage cross-team, pas une encapsulation pour soi).
- **ICE score** : impact **9** (transformative pour le moat) / confidence **10** / ease **10** (déjà installé). **ICE = 900**.

### 1.6 — Context7 MCP (Upstash)

- **Source** : `https://github.com/upstash/context7` · `https://claude.com/plugins/context7` (accessed 2026-05-11)
- **Category** : MCP server / docs lookup
- **What it does** : injecte automatiquement la doc à jour version-spécifique des librairies utilisées (FastAPI, Next.js 14, Supabase, Anthropic SDK) dans le contexte de chaque prompt. Résout les hallucinations sur API obsolètes (training data outdated). Open-source, gratuit, Upstash-maintained.
- **Why stratosphérique for us** :
  - Notre code Python `growthcro/` utilise `anthropic>=0.40.0`, `fastapi>=0.110.0`, `playwright>=1.40.0` — toutes des libs en évolution rapide
  - Webapp V28 Next.js 14 + Supabase + Vercel microfrontends — stack tout récent où Claude hallucine fréquemment (training cutoff vs versions actuelles)
  - **Anti-régression doctrine** : élimine les bugs "Claude a généré du code Next.js 12 alors que je suis sur 14"
  - Coût : 0 (open source). Setup 1-liner.
- **Integration recommendation** : MCP server-level, activé pour **toutes** les combos. À ajouter en MCP par défaut (cf section 4 MCP servers).
- **Install command** : `claude mcp add context7 -- npx -y @upstash/context7-mcp`
- **Risk / open questions** : la doc fetch est sync sur chaque prompt — léger overhead. Acceptable.
- **ICE score** : impact **9** / confidence **10** / ease **9**. **ICE = 810**.

---

## Section 2 — Interesting to test (worth trying)

### 2.1 — obra `superpowers` (méthodologie composable)

- **Source** : `https://github.com/obra/superpowers` (40.9k stars) — accessed 2026-05-11
- **Category** : agent / méthodologie
- **What it does** : framework méthodologique en plusieurs skills chainés : `brainstorming`, `using-git-worktrees`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `test-driven-development`, `verification-before-completion`, `requesting-code-review`, `finishing-a-development-branch`.
- **Why interesting** : notre épic CCPM (`ccpm` skill) gère déjà le PRD→Epic→Issues→subagents→merge pipeline. `superpowers` est **complémentaire** sur les bouts qu'on a moins formalisés : `using-git-worktrees`, `verification-before-completion`, `test-driven-development`.
- **Why "test" plutôt que "must install"** : risque de doublon avec CCPM ; `superpowers` est généraliste, CCPM est notre spec. À tester sur 1 sprint pilote avant d'adopter.
- **ICE score** : impact **6** / confidence **7** / ease **7**. **ICE = 294**.

### 2.2 — Firecrawl skill + CLI

- **Source** : `https://www.firecrawl.dev/blog/introducing-firecrawl-skill-and-cli` · `https://github.com/firecrawl/firecrawl-claude-plugin` (Anthropic official plugin) — accessed 2026-05-11
- **Category** : data / scraping
- **What it does** : skill + CLI unifiés pour scraping / crawling / browsing / searching. Officiel Anthropic plugin (signe de qualité).
- **Why interesting** : notre `growthcro/capture/` orchestrator utilise Playwright — alternative possible via Firecrawl pour gros volumes (100 clients). Mais on a déjà BrightData + Playwright qui marchent.
- **Why "test"** : doublon potentiel avec notre stack capture. À évaluer en POC sur 5 clients pour comparer coûts/qualité.
- **ICE score** : impact **5** / confidence **8** / ease **7**. **ICE = 280**.

### 2.3 — `a11y-mcp` (MCP server axe-core)

- **Source** : `https://github.com/priyankark/a11y-mcp` — accessed 2026-05-11
- **Category** : MCP / a11y audit
- **What it does** : MCP server qui expose axe-core audits sur des URLs ou pages locales. Permet l'agentic loop "audit → fix → re-audit" automatique.
- **Why interesting** : nous fait gagner l'auto-fix a11y. Complète `webapp-testing` (Playwright) avec un audit a11y spécifique.
- **Why "test"** : redondant en partie avec Vercel `web-design-guidelines`. Tester pour voir si vrai apport au-delà.
- **ICE score** : impact **6** / confidence **8** / ease **8**. **ICE = 384**.

### 2.4 — GA4 MCP server (surendranb/google-analytics-mcp ou Cogny)

- **Source** : `https://github.com/surendranb/google-analytics-mcp` · `https://cogny.com/guides/claude-code-ga4-mcp-integration` — accessed 2026-05-11
- **Category** : MCP / data analytics
- **What it does** : connecte Claude Code à GA4 via MCP, query natural language. Cogny offre managed remote MCP avec OAuth (pas de service account local).
- **Why interesting** : Epic #23 `reality-experiment-learning-loop` (FR-8) attend les credentials GA4 sur 3 clients pilote. Ce MCP donne accès direct depuis Claude → enrichit `growthcro/reality/orchestrator.py` côté agent (vs API client uniquement).
- **Why "test"** : on a déjà l'intégration GA4 côté Python (`growthcro/reality/google_analytics.py`). Le MCP est un overlay pour exploration interactive, pas un remplacement du pipeline.
- **ICE score** : impact **7** / confidence **8** / ease **7**. **ICE = 392**.

### 2.5 — `Logfire` / `structured-logging-axiom` skills

- **Source** : `https://mcpmarket.com/tools/skills/logfire-observability` · `https://mcpmarket.com/tools/skills/structured-logging-axiom-observability` — accessed 2026-05-11
- **Category** : observability / logging
- **What it does** : skill qui guide l'intégration Pydantic Logfire (FastAPI/SQLAlchemy/HTTPX) OU stack Axiom (JSON structured logs avec correlation IDs, log levels env-driven).
- **Why interesting** : notre audit a flagué **457 `print()`** dans pipelines (action ICE 378 dans CODE_AUDIT). Ce skill cadre la migration print → logger. Logfire est Pydantic-team, Axiom est leader observability.
- **Why "test"** : avant install, décider du backend log (Logfire vs Sentry vs Axiom). Mathis trancher = pré-requis.
- **ICE score** : impact **7** / confidence **7** / ease **6**. **ICE = 294**.

---

## Section 3 — Excluded (with rationale)

### 3.1 — `Browser-use` skill (browser-use/browser-use)
**Pourquoi exclu** : doublon avec Anthropic `webapp-testing` (Playwright-based). webapp-testing est officiel Anthropic, mieux supporté pour notre Next.js stack. Browser-use mieux pour automation hors-app (forms B2B fill, scraping public).
**Action** : ne pas installer. Garder en mémoire pour cas spécifiques (form automation gros volume).

### 3.2 — `Remotion` (video generation)
**Pourquoi exclu** : hors-scope CRO core. Notre GSG produit HTML statique + animations CSS via `visual_system V27.2-G` + Emil Kowalski. Pas de video programmatique dans la roadmap 8-12 semaines.
**Action** : ne pas installer. Re-considérer en Phase 2 (post-programme) si Growth Society demande "stories" / "reels" génératives.

### 3.3 — `Valyu` skill (36+ data sources)
**Pourquoi exclu** : nos sources données sont marketing-spécifiques (GA4, Meta, Google Ads, Shopify, Clarity) — pas SEC filings / PubMed / ChEMBL. Valyu est généraliste data research, pas CRO.
**Action** : ne pas installer.

### 3.4 — `PlanetScale Database Skills`
**Pourquoi exclu** : on utilise Supabase (Postgres + auth + realtime + storage), pas PlanetScale. Stack différent.
**Action** : ne pas installer.

### 3.5 — `Shannon` (autonomous pentesting)
**Pourquoi exclu** : trop offensive-sec pour un produit interne. Trail of Bits suite couvre amplement notre besoin defensive.
**Action** : ne pas installer.

### 3.6 — `Linear` / `Jira` skills
**Pourquoi exclu** : on utilise CCPM (skill `ccpm` déjà installé) pour PRD/Epic/Issues. Doublon.
**Action** : ne pas installer. Si Growth Society finit par utiliser Linear externe, re-évaluer.

### 3.7 — `Google Workspace (GWS)` MCP
**Pourquoi exclu** : pas de workflow GWS dans la roadmap (Mathis a pas mentionné Gmail/Drive/Sheets agentic). Notion via MCP (déjà) suffit pour le doc layer.
**Action** : ne pas installer. Re-évaluer Phase 2.

---

## Section 4 — MCP servers candidates

> Les MCP servers sont des **back-ends data** (différents des skills qui sont des playbooks). À installer au niveau Claude Code config `mcp` JSON ou via `/plugin install`.

### 4.1 — Supabase MCP (official)

- **Source** : `https://supabase.com/blog/supabase-is-now-an-official-claude-connector` — official Anthropic connector depuis 2026-02-03
- **What it does** : 32 tools — execute SQL, manage schemas, deploy edge functions, manage branches, auth/storage operations
- **Why stratosphérique** : Epic #6 webapp V28 utilise Supabase EU pour auth + storage + realtime (cf PRD FR-6). Cet MCP est **must-have** dès qu'on attaque le sprint. **Safety** : Supabase doc dit explicitement "never connect to production data — dev/test only" → utiliser un projet Supabase dev pour les sessions Claude.
- **Install** : `claude mcp add --transport http supabase https://mcp.supabase.com/mcp` + OAuth
- **ICE** : 9×10×9 = **810**

### 4.2 — Meta Ads MCP (official, since 2026-04-29)

- **Source** : `https://pasqualepillitteri.it/en/news/1707/official-meta-ads-mcp-claude-29-tools-2026` · official endpoint `mcp.facebook.com/ads`
- **What it does** : 29 tools — read/write Marketing API, campaigns, catalogs, benchmarks, Pixel/CAPI diagnostics
- **Why stratosphérique** : remplace ou augmente notre wrapper `growthcro/audit_meta/` (skill `meta-ads-auditor`). Permet Claude d'explorer données live d'un client agence pendant un audit interactif.
- **Install** : `claude mcp add --transport http meta-ads https://mcp.facebook.com/ads` + OAuth
- **ICE** : 8×10×8 = **640**

### 4.3 — Shopify MCP (open-source Apr 2026)

- **Source** : `https://askphill.com/blogs/blog/shopify-just-released-an-ai-toolkit-for-claude-heres-what-it-actually-does` · open-sourced April 2026
- **What it does** : Shopify Admin API + GraphQL schemas. Create collections, dynamic pricing, product ops via natural language.
- **Why stratosphérique pour nous** : ~30% des clients agence sont Shopify (e-commerce DTC). Cet MCP permet audit live de boutique pendant un sprint CRO. Mipler Reports complémentaire pour analytics massif (10k orders/call).
- **Install** : `claude mcp add shopify` (via Shopify CLI plugin).
- **ICE** : 7×9×8 = **504**

### 4.4 — Sentry MCP

- **Source** : `https://docs.sentry.io/product/sentry-mcp/` · official remote server since April 2026 (`mcp.sentry.dev/mcp`)
- **What it does** : read issues, stack traces, group by frequency, check error status — sans quitter Claude Code
- **Why stratosphérique** : Epic #6 webapp V28 en prod (5 microfrontends) → besoin observability. Sentry official MCP via OAuth+SSE.
- **Install** : `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` + OAuth
- **ICE** : 8×9×8 = **576**

### 4.5 — PostHog MCP

- **Source** : `https://posthog.com/docs/model-context-protocol/claude-code`
- **What it does** : feature flags, funnels, A/B test results, product usage analytics
- **Why interesting (pas must)** : Epic #23 `experiment-engine` veut déclencher 5 A/B mesurés. Si Growth Society utilise PostHog (à vérifier avec Mathis), c'est un fit naturel. Sinon, alternative GA4 + Google Optimize.
- **Install** : `claude mcp add posthog` + auth
- **ICE** : 7×6×7 = **294** (confidence basse car incertain si Growth Society utilise PostHog)

---

## Section 5 — Recommended sprint structure

Si Mathis valide N installs, voici l'ordre suggéré :

### Sprint S1 — "Stratosphère Foundation" (1 install session, ~1h Mathis)

**Skills (4)** :
1. `vercel-labs/agent-skills` (apporte react-best-practices + web-design-guidelines + composition-patterns + react-view-transitions en un install)
2. `trailofbits/skills` (apporte les 17 skills security ; activer surtout static-analysis + variant-analysis + supply-chain-risk-auditor)
3. Anthropic `webapp-testing` (Playwright skill)
4. Confirmer/formaliser `skill-creator` déjà installé (juste blueprint update)

**MCPs (1)** :
5. `Context7` MCP — universel, anti-hallucination

**Combo packs à mettre à jour** :
- **Combo "Webapp Next.js dev"** (était 4 skills) → ajouter `vercel-react-best-practices` + `web-design-guidelines` (5 skills si on garde Figma optionnel, 4 si on bascule Figma en on-demand).
- **Nouveau combo "Security audit"** : `trailofbits/static-analysis` + `variant-analysis` + `supply-chain-risk-auditor` + `Impeccable`. Activé pre-merge ou trimestriel.
- **Nouveau combo "QA + a11y"** (optionnel — Epic #6) : `webapp-testing` + `web-design-guidelines` + (optionnel `a11y-mcp` MCP server).

### Sprint S2 — "Reality / Production observability" (1 install session, ~30min)

**MCPs (3)** :
6. `Supabase MCP` (Epic #6 prerequisite)
7. `Sentry MCP` (Epic #6 prerequisite)
8. `Meta Ads MCP` official (Epic #7 enhancement)
9. `Shopify MCP` (Epic #7 enhancement pour clients e-comm)

**Combo "Audit run"** étendu :
- Ajouter `Supabase MCP` + `Sentry MCP` + `Meta Ads MCP` comme MCP server-level (pas dans le compte des 8 skills/combo).
- MCPs ≠ skills → pas de limite 8 sur les MCPs.

### Sprint S3 — "POC / À tester avant adoption" (1 install session, ~1h)

**Skills/MCPs à tester en POC** :
10. obra `superpowers` (1 sprint pilote, comparer vs CCPM)
11. `a11y-mcp` MCP (POC sur 1 webapp V28 microfrontend)
12. GA4 MCP (POC sur 1 client pilote Reality Layer)
13. Logfire OR structured-logging-axiom (après décision backend obs)

**Validation pre-adoption** : 1 sprint chacun, comparer à existant, décider keep/drop.

---

## Annexes

### A.1 — Search queries used (12 total)

1. "Claude Code Skills marketplace skills.sh 2026 top CRO marketing"
2. "best Claude Code MCP servers 2026 Supabase Vercel Next.js production"
3. "Claude Code skills production agent workflow CRO conversion optimization site:medium.com OR site:dev.to 2026"
4. "Claude skills 'skills.sh' Anthropic 2026 official registry list"
5. "Playwright MCP Claude Code 2026 Supabase MCP browser automation skill"
6. "Vercel labs agent skills github React Next.js best practices 2026"
7. "Claude Code skills 'trail of bits' CodeQL Semgrep security static analysis 2026"
8. "'claude code' skill 'browser-use' OR 'obra/superpowers' OR 'firecrawl' 2026 install"
9. "'awesome-claude-code' OR 'awesome-agent-skills' github 2026 top skills CRO design webapp"
10. "'Supabase' MCP server Claude Code official 2026 install postgres auth realtime"
11. "'Sentry' OR 'PostHog' OR 'Stripe' MCP server Claude Code production observability 2026"
12. "'GA4' 'Google Analytics' MCP server Claude Code 2026 marketing analytics"

### A.2 — Sources scanned (URLs accessed 2026-05-11)

| Source | URL |
|---|---|
| GitHub Vercel labs | https://github.com/vercel-labs/agent-skills |
| GitHub Trail of Bits | https://github.com/trailofbits/skills |
| GitHub Anthropic | https://github.com/anthropics/skills |
| GitHub obra Superpowers | https://github.com/obra/superpowers |
| Firecrawl skills blog | https://www.firecrawl.dev/blog/best-claude-code-skills |
| Medium top 10 skills 2026 | https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051 |
| GitHub alirezarezvani | https://github.com/alirezarezvani/claude-skills |
| Supabase MCP official | https://supabase.com/blog/supabase-is-now-an-official-claude-connector |
| Meta Ads official MCP | https://pasqualepillitteri.it/en/news/1707/official-meta-ads-mcp-claude-29-tools-2026 |
| Shopify AI Toolkit | https://askphill.com/blogs/blog/shopify-just-released-an-ai-toolkit-for-claude-heres-what-it-actually-does |
| Context7 MCP | https://github.com/upstash/context7 |
| Sentry MCP | https://docs.sentry.io/product/sentry-mcp/ |
| PostHog MCP | https://posthog.com/docs/model-context-protocol/claude-code |
| GA4 MCP | https://github.com/surendranb/google-analytics-mcp |
| a11y-mcp | https://github.com/priyankark/a11y-mcp |
| skills.sh registry | https://skills.sh/ |
| mcpservers.org | https://mcpservers.org/ |

### A.3 — Cross-reference avec `WEBAPP_ARCHITECTURE_MAP.yaml`

Modules impactés par les Top-6 stratosphère install :

| Skill | Modules impacted |
|---|---|
| Vercel `react-best-practices` | webapp V28 (Epic #6 — `webapp/apps/audit-app`, `reco-app`, `gsg-studio`, `reality-monitor`, `learning-lab`) — toute la stack Next.js |
| Vercel `web-design-guidelines` | idem + `growthcro/scoring/specific/*.py` (alimente playbook V3.3 axe a11y) |
| Trail of Bits `static-analysis` | tout le tree Python `growthcro/`, `moteur_gsg/`, `moteur_multi_judge/`, `skills/` (audit pre-merge) |
| Anthropic `webapp-testing` | `webapp/tests/e2e/` (Playwright config existing) |
| `skill-creator` | meta — utilisé pour créer skill `cro-doctrine-v3-3-applier` (futur Epic) |
| Context7 MCP | universel — toutes les sessions Claude Code |

### A.4 — Anti-cacophonie check (vs `SKILLS_INTEGRATION_BLUEPRINT.md` § 3)

Aucune violation détectée :
- Vercel skills neutres a11y/perf — pas de parti pris visuel conflictuel avec `brand-guidelines` per-client
- Trail of Bits skills security — orthogonaux à tout combo design
- `webapp-testing` Anthropic — orthogonal à tout combo
- `skill-creator` méta — orthogonal
- Context7 MCP — purement docs lookup, aucune influence sur sortie code

### A.5 — ICE scores reference

| Action | Impact | Confidence | Ease | ICE |
|---|---:|---:|---:|---:|
| Vercel `react-best-practices` | 9 | 10 | 10 | 900 |
| Anthropic `skill-creator` (déjà) | 9 | 10 | 10 | 900 |
| Context7 MCP | 9 | 10 | 9 | 810 |
| Supabase MCP | 9 | 10 | 9 | 810 |
| Trail of Bits `static-analysis` | 9 | 10 | 8 | 720 |
| Vercel `web-design-guidelines` | 8 | 10 | 9 | 720 |
| Anthropic `webapp-testing` | 8 | 10 | 9 | 720 |
| Meta Ads MCP official | 8 | 10 | 8 | 640 |
| Sentry MCP | 8 | 9 | 8 | 576 |
| Shopify MCP | 7 | 9 | 8 | 504 |
| GA4 MCP | 7 | 8 | 7 | 392 |
| a11y-mcp MCP | 6 | 8 | 8 | 384 |
| Logfire / Axiom skill | 7 | 7 | 6 | 294 |
| obra `superpowers` | 6 | 7 | 7 | 294 |
| PostHog MCP | 7 | 6 | 7 | 294 |
| Firecrawl skill | 5 | 8 | 7 | 280 |

---

**Fin du rapport Mission B**. Tous les skills/MCPs identifiés sont compatibles avec les règles immuables `CLAUDE.md` (≤ 8 skills/session, pas de signaux contraires, doctrine V3.2.1 reste upstream).

Decision pending Mathis : (a) approuver Top-6 stratosphère + 4 MCPs sprint S1+S2, OU (b) phased rollout (skill par skill, valider chacun avant suivant), OU (c) cherry-pick le sous-ensemble qui résonne le plus.
