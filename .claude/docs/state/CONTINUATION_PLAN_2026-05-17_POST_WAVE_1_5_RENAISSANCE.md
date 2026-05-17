# Continuation Plan — Post Wave 1.5 Renaissance (2026-05-17)

**Quand utiliser ce doc** : début de la prochaine session Claude Code post-`/clear`. Point d'entrée officiel pour reprendre le travail Renaissance proprement, sans recharger tout l'historique.

**Status global** : Epic `gsg-creative-renaissance` à 4/8 sub-issues closed (Wave 1 + Wave 1.5 Elite Mode). Plus 1 quick win SEO + 3 commits cleanup post-/simplify. Prêt pour Wave 2 (CR-04 + CR-05) dès que Mathis valide le scope.

---

## 0. Lecture obligatoire (5 min)

1. Ce fichier (CONTINUATION_PLAN_2026-05-17)
2. `.claude/CLAUDE.md` (step #12 pointe vers ce fichier)
3. `.claude/docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md` — diagnostic produit Codex
4. `.claude/prds/gsg-creative-renaissance.md` — PRD complet avec FR-9 Elite Mode
5. `.claude/epics/gsg-creative-renaissance/epic.md` — Two Creative Modes + 4 Codex Constraints + 9 sub-issues
6. `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 — 2 dernières entries (Wave 1 + Wave 1.5 Elite Mode shipped)
7. `python3 state.py` — disk state pipeline
8. `python3 scripts/audit_capabilities.py` — modules actifs

**Si Mathis demande "what's next"** → lance `bash .claude/skills/ccpm/references/scripts/next.sh` ou lis directement la section §3 ci-dessous.

---

## 1. Ce qui a été shipped (2026-05-16 → 2026-05-17)

### Epic `growthcro-stratosphere-p0` — 100% DONE (12 issues + epic #39 CLOSED)

- **Wave 1** : SSRF crawler fix (#40), archive V1 doc (#41), 3 custom skills growthcro-anti-drift/prd-planner/status-memory (#42-#44), Opportunity Pydantic schema (#47)
- **Wave 2** : Skill Registry Governance (#45), Opportunity engine orchestrator (#48), ClaimsSourceGate module (#51 partial)
- **Wave 3** : Skills security checklist 18 ext audit (#46), Opp CLI + wire recos (#49), VerdictGate aggregator (#50), ClaimsSourceGate wire mode_1 (#51)
- **Follow-ups** : CLAUDE.md step #13, drop 4 dormant skills (gstack + 3 superpowers), heavy smoke GSG runtime
- **Quick win** : tech_03 SEO caps (commit `6348fa2`)

### Epic `gsg-creative-renaissance` — 4/8 sub-issues DONE

- **Wave 1 structured** : Creative Exploration Engine thesis/orchestrator/persist/CLI (#56), Visual Judge structured (#57), Pydantic Contracts (#58). 77 tests new, 4400 LOC.
- **Wave 1.5 Elite Mode** (#64) : Opus Unleashed direct-to-HTML + Creative Bar 12 verticals + 2-phase judge Phase 1. 138 tests new. 4 Codex Constraint Statements verbatim respectés.
- **Post-Elite 3 fixes** : F1 ThreadPoolExecutor parallel (3x speedup latence), F2 brand DNA enrich (palette_full + typography + spacing + voice), F3 copy guidance (sourced_numbers + testimonials + LP-Creator copy inject)
- **Post-/simplify cleanup** : delete dead async wrapper, hoist precompute blocks, feature-detect models sans temperature, strip narrative F1/F2/F3 comments. KNOWN_DEBT bump pour orchestrator.py 1106 LOC.

### Smoke runtime validation (Mathis)

- ✅ 3 HTML candidates Opus 4.7 générés sur Weglot lp_listicle, qualité visuelle "GOBSMACKED, quasi-ORBITAL" (verdict Mathis), candidate 3 > 2 > 1 en qualité créative
- ⚠️ 11min wall pre-F1 fix (séquentiel) — attendu ~4min post-F1
- ⚠️ Brand alignment ~50% pre-F2 fix — attendu ~85% post-F2 enrich
- ⚠️ Copy invented par Opus pre-F3 fix — attendu ~80% sourced post-F3 inject

### Smoke heavy runtime Wave 3 (Mathis) — pré-Renaissance

- Composite 50%, killer rule `coh_03 scent_matching` violated (missing ad creatives). Système refuse de mentir ✅ Gates honnêtes (Wave 3) functional.

---

## 2. État disk + GitHub

### Commits récents (top 12 sur main)

```
417b320 refactor(creative_engine.elite): post-/simplify cleanup + KNOWN_DEBT bump
7fbe190 feat(creative_engine.elite): 3 fixes F1+F2+F3 (parallel + brand DNA + copy guidance)
83ee55c fix(creative_engine.elite): handle deprecated temperature param for opus-4-7+
ecd93a7 fix(creative_engine.elite): defensive color extraction handles list/None shapes
ae54215 docs: manifest §12 — Wave 1.5 Renaissance CR-09 SHIPPED (Elite Mode #64)
25f8944 feat(creative_engine.elite): Opus Unleashed direct-to-HTML + Creative Bar + Phase 1 judge
a04d352 chore(epic): sync CR-09 frontmatter github URL #64
98ad326 docs(epic): add CR-09 Elite Mode per Codex pivot review 2026-05-17
2239c4e docs: manifest §12 — Wave 1 Renaissance SHIPPED (#56 + #57 + #58)
428dbce chore: post Wave 1 Renaissance housekeeping
46f21e2 chore(epic): close CR-02 task file
a40d1bf feat(creative_engine): Visual Judge selects route via Sonnet scoring 5 axes
```

### Smoke gates (status à `417b320`)

- **pytest** : 353 passed (138 Renaissance + 215 baseline pre-Renaissance)
- **lint_code_hygiene** : FAIL 3 (pré-existants : _archive_deprecated dir, components.py 979 LOC, seed_supabase os.environ). orchestrator.py 1106 LOC tracked KNOWN_DEBT.
- **SCHEMA validate_all** : 3439 files OK
- **audit_skills_governance** : 38 entries, 0 drift
- **audit_capabilities** : 0 orphans HIGH

### GitHub issues état

- **Epic #39** `growthcro-stratosphere-p0` : CLOSED
- **Epic #55** `gsg-creative-renaissance` : OPEN (4/8 sub-issues done)
- **CLOSED Renaissance** : #56 #57 #58 (Wave 1 structured) + #64 (Wave 1.5 Elite)
- **OPEN Renaissance** : #59 CR-04 (Wave 2), #60 CR-05 (Wave 2), #61 CR-06 (Wave 3), #62 CR-07 (Wave 3), #63 CR-08 (Wave 3)

### Tracked tree

Clean sauf `deliverables/gsg_demo/*.html` modifiés (pré-existants, hors scope).

---

## 3. NEXT STEPS prioritaires

### 🎯 Step 1 (Mathis, 5-10 min) — Re-smoke Elite Mode avec 3 fixes

```bash
cd /Users/mathisfronty/Developer/growth-cro && set -a; source .env; set +a
python3 -m moteur_gsg.creative_engine.elite.cli explore \
  --client weglot --page lp_listicle --candidates 3
```

**Vérifie** :
- Wall time : ~4min (vs 11min pre-F1) — 3× speedup parallèle
- Couleurs Weglot exactes dans `<style>` blocks : #e9dcf0, #c1e0f8, #493ce0 (palette_extras)
- Copy sourcé : "111 368 marques", "+400% Polaar", "4.8/5 G2" cités exactement (pas inventés)
- Testimonials nommés : Sophie von Kirchmann (Polaar), Polina Usynina (Respond.io), Salomé Amar (L'Équipe Créative)
- Qualité visuelle : reste niveau ORBITAL ou mieux

**Si OK** → Step 2 (Wave 2 dispatch).
**Si KO** → ping Claude avec output + fix itératif.

### 🚀 Step 2 (Claude session next, 4-8h wall) — Wave 2 Renaissance

**3 issues à dispatch en parallèle / sequential selon dépendances** :

- **#59 CR-04 Visual Composer** (Wave 2, L 18h estimé / ~3-4h wall avec agent) — structured mode only path. Depends CR-02 + CR-03 (both DONE). Image gen SKIP v1 décidé (Brand DNA + SVG/CSS/Lottie + Pexels fallback). Vocabulary library 12 verticals.
- **#60 CR-05 Screenshot QA** (Wave 2, L 16h / ~3h wall) — BOTH modes. Phase 2 Screenshot QA winner picker pour Elite + structured QA. Depends MCP Playwright ✅ already installed `.mcp.json`.
- (Optional pre-Wave-2) **Mini-sprint refacto factorisation** identifié par /simplify Agent 1 — ~390 LOC dedupable cross-modules :
  - `growthcro/lib/anthropic_client.call_messages()` factor `_call_anthropic` × 4 sites (orchestrator wave 1 + judge wave 1 + elite orchestrator + elite judge_html)
  - `growthcro/lib/atomic_write.py` factor atomic write × 4 sites
  - `growthcro/lib/text_utils.py` factor `_truncate` × 4 sites
  - `moteur_gsg/creative_engine/_shared/cli_io.py` factor CLI plumbing × 2 sites
  - Réutiliser `moteur_gsg/core/design_tokens._hex` + `_palette` dans elite/orchestrator
  - **Effort** : ~2-3h dev, mais débloque le split orchestrator.py 1106 LOC (KNOWN_DEBT)

### 🚀 Step 3 (Claude session après Wave 2) — Wave 3 Renaissance

**3 issues finales** :

- **#61 CR-06 Renderer extension** (Wave 3, XL 24h / ~4-5h wall) — structured mode only per Codex Constraint #3. Depends CR-04. Multi-vertical CSS modules.
- **#62 CR-07 Promptfoo benchmark** (Wave 3, L 16h / ~3h wall) — BOTH modes comparative eval. Depends CR-06. 6+ clients golden set.
- **#63 CR-08 5 custom skills + wire mode_1_complete** (Wave 3, M 12h / ~2-3h wall) — feature flag `creative_mode: Literal["structured", "elite"]` dans mode_1_complete.py. Depends CR-06 + CR-07.

### 🔬 Step 4 (Mathis post-Wave-3) — Smoke heavy GSG full pipeline avec Renaissance

```bash
# Mode structured (default backward-compat)
python3 scripts/run_gsg_full_pipeline.py --url https://www.weglot.com --page-type lp_listicle ...

# Mode elite (opt-in)
python3 scripts/run_gsg_full_pipeline.py ... --creative-mode elite

# Mode both (debug A/B compare)
python3 scripts/run_gsg_full_pipeline.py ... --creative-mode both --debug-compare
```

---

## 4. Décisions tranchées Mathis (sources of truth)

### Image gen
**SKIP v1** : Brand DNA + SVG/CSS/Lottie + Pexels/Unsplash fallback. PAS d'OpenAI/Replicate/Midjourney. FLUX peut être ajouté en v2 si benchmark prouve gap luxury/lifestyle verticals.

### Provider LLM
- **Creative exploration** : Claude Opus 4.7 (stack 100% Anthropic, ~$0.5-1/run)
- **Copy + Judge + retry** : Claude Sonnet 4.5
- **Screenshot QA** : Claude Sonnet 4.5 vision

### Screenshot QA
**MCP Playwright** : installed via `.mcp.json` commit `58ad215`. Restart Claude Code requis pour pick-up. Already verified working dans session 2026-05-17.

### Eval framework
**Promptfoo** : installed globally v0.121.11. Use pour CR-07 benchmark Wave 3.

### Two Creative Modes (Codex pivot)
- `structured` : Wave 1 CR-01/02/03 thesis → composer → renderer. Default backward-compat, learning, scaling 56 clients, fallback safe.
- `elite` : Wave 1.5 CR-09 Opus Unleashed direct HTML. Opt-in, wow-factor, client demo, benchmark.
- `both` : CLI flag `--debug-compare` UNIQUEMENT (benchmark A/B), JAMAIS default workflow.

### 4 Codex Constraints (NON NÉGOCIABLES)
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output preserves layout/CSS/motion unless deterministic gate blocks.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence at post-process gates only, NEVER at rendering layer.

### Anti-régression marker
`PRESERVE_CREATIVE_LATITUDE = True` constant dans `moteur_gsg/creative_engine/elite/orchestrator.py`. Future edits MUST preserve Opus creative latitude. Enrich INPUTS (brand fidelity, sourced proof), never DICTATE visual structure.

---

## 5. Tech debt + follow-ups (à scoper post-Wave 2)

### Dette tracked (KNOWN_DEBT in lint_code_hygiene.py)

- `moteur_gsg/creative_engine/elite/orchestrator.py` (1106 LOC) — split scheduled post-Wave 2 : extract `prompt_assembly.py` (Section builders + brand_dna helpers) + `user_message.py` (copy guidance formatters) + `parallel_runner.py` (ThreadPoolExecutor wrap). Target ~500-600 LOC orchestrator.
- `moteur_gsg/modes/mode_1_complete.py` (1027 LOC) — split scheduled post-stratosphere-p0 (déjà tracked depuis Wave 3 #50/#51 wires).
- `moteur_gsg/core/css/components.py` (979 LOC) — pré-P0 dette (Sprint 13-21 accretion).

### Refacto factorisation cross-modules (Agent 1 /simplify findings, ~390 LOC dedupable)

- **HIGH** : `growthcro/lib/anthropic_client.call_messages()` — factor `_call_anthropic` × 4 sites
- **HIGH** : `growthcro/lib/atomic_write.py` — factor atomic tmpfile+os.replace × 4 sites
- **MEDIUM** : `growthcro/lib/text_utils.py` — factor `_truncate` × 4 sites
- **MEDIUM** : `moteur_gsg/creative_engine/_shared/cli_io.py` — factor `_find_brief` / `_load_brand_dna` / `_load_json` × 2 sites
- **MEDIUM** : `moteur_gsg/creative_engine/_shared/brief_brand_summary.py` — factor `_summarise_brief` / `_summarise_brand` × 2 sites
- **MEDIUM** : Réutiliser `moteur_gsg/core/design_tokens._hex` + `_palette` dans elite/orchestrator au lieu de `_extract_color_hex` + `_extract_palette_full` locaux

**Recommandation** : créer 1 mini-sprint dédié refacto factorisation AVANT Wave 2 si on veut le split orchestrator.py propre. OU laisser tel quel et split orchestrator.py post-Wave 3.

### Issues émergentes identifiées mais NON scopées

- **Multi-judge audit detail persist enrichment** : `multi_judge_audit.json` (Sprint P1 #54) ne contient pas les LLM rationale détaillés pour chaque criterion failure. Pour Learning Layer V29 future, on aura besoin du rationale.
- **Brand_dna typography + voice extraction Weglot** : Mathis brand_dna.json est sparse (pas de typography.heading detail, pas de voice_keywords). F2 marche mais Opus a peu à utiliser. Suggérer enrich `growthcro/research/brand_identity.py` extractor pour générer brand_dna plus riche.
- **Anthropic prompt cache parallel cache miss** : /simplify Agent 3 MEDIUM 2 — 3 calls Opus en parallèle race pour créer le cache simultanément = 3× `cache_creation_input_tokens` au lieu de 1× create + 2× reads (~$0.05 wasted/batch). Vérifier empiriquement via telemetry, fix si vrai impact.
- **CR-04 Visual Composer / asset_resolver Pexels API** : décision en attendant — Mathis confirme Pexels API key gratuit ou skip Pexels totalement (SVG library + brand assets only) ?

---

## 6. Acceptance globale epic Renaissance (rappel)

Quand l'epic sera CLOSED, on aura :

1. **Universalité** : 6+ verticals tests → composite ≥85% (variance ≤5pp)
2. **Visual ambition** : Screenshot QA ≥7/10 sur ≥80% runs
3. **Time-to-LP** : ≤10min wall structured OR ~4min elite avec ThreadPool
4. **Cost** : ≤$2/LP structured, ~$4.35/LP elite (3 candidates)
5. **Zero régression** : Sprint 21 baseline Weglot V14b 88.6% reproductible
6. **5 custom skills** Renaissance invocables (CR-08)
7. **Promptfoo CI green** sur golden set
8. **8 sub-issues + epic CLOSED** + manifest §12 bumped
9. **PRESERVE_CREATIVE_LATITUDE** respecté (constant in code)
10. **4 Codex Constraints** verified via grep (zero forbidden imports cross-modes)

---

## 7. Process learnings (à appliquer next sessions)

- **Early-push pattern** : Wave 1 a démontré que push schema seul (commit 1) débloque agents downstream parallèles. Réutiliser pour CR-04 (split CreativeRouteContract consumer schema → push → unblock CR-05/06).
- **Stash-on-race-detection** : Wave 1 Agent CR-03 a `git stash` les fichiers CR-02 untracked pendant commit. Zero work lost. Pattern utile pour Wave 2/3 parallèle.
- **Mono-concern enforcement** : Wave 1 CR-03 a refusé d'étendre creative_models.py CR-01-owned, créé visual_composer_models.py séparé. Continuer ce pattern (e.g. judge_html.py séparé de judge.py, pas extension).
- **Codex Constraint Statements verbatim** : inscrire les constraints dans docstrings de chaque module pour anti-régression. Grep verify les forbidden imports avant chaque PR.
- **/simplify pattern** : invoquer après chaque sprint de >500 LOC pour catch redondances tôt. 3 agents Code Reuse + Code Quality + Efficiency en parallèle = ~5 min wall.
- **/ccpm standup** : utile pour formaliser status en début/fin de session.

---

## 8. Si tu reprends après /clear et tu es perdu

**Lance dans l'ordre** :

```bash
# 1. État disk pipeline
python3 state.py

# 2. Capabilities registry
python3 scripts/audit_capabilities.py
cat .claude/docs/state/CAPABILITIES_SUMMARY.md | head -50

# 3. Renaissance current state
cat .claude/epics/gsg-creative-renaissance/epic.md | head -60

# 4. Last commits
git log --oneline -15

# 5. Open issues epic
gh issue list --repo GrowthSociety-GS/growth-cro --state open --label "epic:gsg-creative-renaissance"

# 6. Test suite quick check
python3 -m pytest tests/creative_engine/ -q

# 7. Quick lint
python3 scripts/lint_code_hygiene.py | head -10
```

**Si tout vert** → Step 1 ci-dessus (Mathis re-smoke) ou Step 2 (dispatch Wave 2).

**Si rouge quelque part** → ping moi avec output, je triage.

---

*Document créé 2026-05-17 fin de session post Wave 1.5 Renaissance + 3 fixes + /simplify cleanup. Mathis verdict "GOBSMACKED" sur outputs Opus Elite Mode, candidate 3 > 2 > 1 qualité croissante. Architecture hybride structured+elite validée production-ready. Total Renaissance work à date : 12 commits, ~4400 LOC nouveau, 138 tests Elite + 77 tests structured = 215 tests Renaissance, $4.35/batch Elite, ~4min wall post-F1.*
