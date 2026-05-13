---
name: webapp-data-fidelity-and-skills-stratosphere-2026-05
description: MEGA PRD AUDIT-FIRST — install ALL skills stratosphère 2026 d'abord, puis multi-agent audit exhaustif (data + UI/UX + interactions + sécurité + perf + a11y), puis prioritized fix list, puis execution, puis validation Playwright. Plan AU CARRÉ post-frustration user 2026-05-13.
status: active
created: 2026-05-13T15:00:00Z
parent_prd: post-stratosphere-roadmap
wave: audit-first-stratosphere
priority: P0-critical-reset
---

# PRD: webapp-data-fidelity-and-skills-stratosphere-2026-05

> **MEGA PRD AUDIT-FIRST critical reset** post-frustration légitime user 2026-05-13.
>
> User a constaté : "y'a des erreurs de PARTOUT, sur la donnée, les règles, les critères, les images, l'UI/UX de l'app elle même... c'est quoi ce bordel ?"
>
> Cause root du désastre 2026-05-13 : **velocity > validation**. 10+ sub-PRDs shipped sans vérification end-to-end visuelle. Migration data sur mauvais bundle. Agents background trusted sans validation que data input correspondait au UI rendering.
>
> **Stratégie 2026-05-14 inversée** : AUDIT EXHAUSTIF AVANT TOUTE ACTION, avec ALL skills stratosphère + natives gratuits. Puis fix prioritized list. Puis validation Playwright.

## Executive Summary

### Le problème (constat user textuel 2026-05-13)
> *"y'a des erreurs de PARTOUT, sur la donnée, les règles, les critères, les images, l'UI/UX de l'app elle même... c'est quoi ce bordel ?"*

### Cause du désastre (méta-analyse honnête)
1. **Velocity > validation** : 10 sub-PRDs shipped sans browser-load test
2. **Migration data sur mauvais bundle** : `growth_audit_data.js` (V21 cluster pauvre) au lieu de `recos_enriched.json` (V13 riche)
3. **Trust agents sans cross-check data** : RichRecoCard parfait, mais recos input vides
4. **Skills disponibles non-utilisés** : `vercel:verification`, `webapp-testing`, `design:design-critique`, native `/review`, `Vercel Agent`
5. **Sub-PRDs top-down features** : visaient le rendu UI sans vérifier la data underlying

### Bugs probables non-encore visibles
- `brand_dna_json` NULL → 56/56 clients empty state
- `judges_json` NULL → 185/185 audits empty state
- `funnel_json` NULL → fallback derived weird
- doctrine_proposals empty Supabase
- CRUD modals (edit reco / create audit) jamais testés réellement
- Mobile responsive jamais testé à 360px/768px/1024px
- A11y skip link jamais testé au focus clavier
- Search/filter avec 56 vrais clients jamais testé
- Settings tabs (Account password change, Team invite) jamais testés
- Doctrine, Learning, Reality routes jamais ouvertes
- Error boundaries jamais déclenchés (donc jamais validés)
- Toutes les routes secondary

### Stratégie AUDIT-FIRST
1. **Wave 0 PREP** : install skills stratosphère + activate natives + rotate JWT
2. **Wave A AUDIT** : 10+ parallel multi-agent audits (data + UI + interactions + perf + a11y + security)
3. **Wave B SYNTHESIS** : prioritized bug list with severity ranking
4. **Wave C FIX** : execute fixes by priority (critical → important → nice-to-have)
5. **Wave D VALIDATE** : Playwright E2E + Lighthouse + Mathis manual validation
6. **Wave E CLOSE** : BLUEPRINT v1.3 + CONTINUATION_PLAN

## Problem Statement

### Pourquoi le plan précédent a échoué (méta-analyse)

| Erreur méthodologique | Conséquence |
|---|---|
| Velocity-mode 10 sub-PRDs/jour | 0 test end-to-end visuel |
| Trust HTTP codes (200/307/404) = "ça marche" | Bugs visuels invisibles passent en prod |
| Skills installed pas utilisés | Audit exhaustif jamais run |
| Migration sur premier bundle plausible | Mauvais format data en Supabase |
| Pas de Mathis dans la boucle de validation | Drift attente vs réalité |
| Plan top-down features (Wave P0/P1/P2) | Pas validé que data underlying matchait |
| Sub-PRDs ambitious (avant V26 parity reached) | Beyond V26 features avec data vide |

### Ce que ce PRD remet AU CARRÉ

- **Audit AVANT execution** : on découvre TOUT le bordel avant de fix
- **Skills stratosphère intégrés** : skill-based-architecture + Superpowers + GStack + /review + Vercel Agent + vercel:verification + webapp-testing + design-critique + accessibility-review + react-best-practices + performance-optimizer
- **Cross-validation par 5+ agents indépendants** : eliminate single-point-of-failure
- **Test visuel obligatoire** : Playwright E2E + screenshots browser réel + Mathis validation
- **Sub-PRDs créés POST-audit** : prioritized par severity, pas par feature top-down
- **Continuation Plan rigoureux** : self-contained, user peut reprendre sans contexte session précédente

## User Stories

### US-1 — Mathis (sortir du bordel maintenant et pour toujours)
*Comme founder qui a vu un écran de fumée pendant 12h de coding, je veux que la prochaine session commence par un audit exhaustif multi-agent qui identifie TOUS les bugs (data + UI + interactions + sécurité + perf + a11y) AVANT de toucher au code.*

**AC** :
- ✓ ≥10 audit reports parallel agents (1 par dimension)
- ✓ Master bug list with severity ranking (P0/P1/P2/P3)
- ✓ Min 30 bugs/improvements identifiés (réaliste pour 10 sub-PRDs shipped sans validation)
- ✓ Roadmap fix ordered by impact × effort

### US-2 — Mathis (parité V26 réelle, vérifiable)
*Comme user qui attendait la parité V26 et a eu un écran de fumée, je veux que chaque promise du master PRD `webapp-v26-parity-and-beyond` soit VÉRIFIÉE en browser réel avec Playwright + screenshots avant de claim "shipped".*

**AC** :
- ✓ Playwright E2E suite : 1 test par route critique (10+ tests)
- ✓ Each test : load route + verify data displayed + interaction (if applicable) + screenshot
- ✓ All passing avant claim "V26 parity reached"

### US-3 — Mathis (skills stratosphère exploités)
*Comme founder qui a investi du temps à identifier 3 skills stratosphère + 2 natives, je veux qu'ils soient TOUS utilisés dans cette opération, pas juste mentionnés.*

**AC** :
- ✓ `skill-based-architecture` installé + run → `skills/growthcro/` consolidé
- ✓ `Superpowers` installé + utilisé pour le sprint multi-step
- ✓ `GStack` installé + utilisé pour audit QA persona
- ✓ Native `/review` Claude Code run sur commits récents (15+)
- ✓ Vercel Agent enabled + au moins 1 PR review automatique
- ✓ `vercel:verification` invoked sur ≥3 routes critiques
- ✓ `webapp-testing` (Playwright) E2E suite written
- ✓ `design:design-critique` invoked sur audit detail page
- ✓ `design:accessibility-review` WCAG AA audit complet
- ✓ `vercel:react-best-practices` audit sur TSX components récents
- ✓ `vercel:performance-optimizer` Lighthouse audit

## Functional Requirements

### Wave 0 — PREP (P0 absolu, AVANT TOUT)

#### W0.1 — 🔴 URGENT Rotate service_role JWT (Mathis, 5 min)
**Steps** :
1. https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc/settings/api → Reset service_role
2. Copier new clé
3. Vercel Dashboard env vars → update `SUPABASE_SERVICE_ROLE_KEY` (Production + Preview)
4. `.env.local` local update
5. Document new key in personal password manager

**Acceptance** : new JWT works (test 1 query), old JWT invalidated

#### W0.2 — Install skill-based-architecture (P0, ~45 min)
**Steps** :
1. `git clone https://github.com/WoJiSama/skill-based-architecture.git skills/skill-based-architecture`
2. Invoke skill : `"Use skill-based-architecture to consolidate growthcro project rules into skills/growthcro/"`
3. Verify structure : SKILL.md + rules/ + workflows/ + references/ + docs/
4. Edit CLAUDE.md → thin entry shell (≤20 lignes routing vers skills/growthcro/)
5. Test : new Claude Code session répond doctrine sans lire 12 init steps

#### W0.3 — Install Superpowers + GStack (P0, ~30 min)
**Steps** :
1. `npx skills add obra/superpowers`
2. `npx skills add https://github.com/garrytan/gstack`
3. Verify installs via `claude skill list`

#### W0.4 — Activate Vercel Agent + native /review prep (P0, ~15 min)
**Steps** :
1. Vercel Dashboard → Agent → enable AI PR Review + Production Investigation
2. Configure : auto-trigger on every PR
3. Verify in Vercel project settings

### Wave A — AUDIT EXHAUSTIF (P0, ~3-4h)

**Stratégie** : lancer 10-12 agents/skills audits en PARALLEL pour cross-validation. Chacun produit un rapport `.claude/docs/state/AUDIT_<dimension>_2026-05-14.md`.

#### W A.1 — Native `/review` Claude Code (1 invocation)
**Run** : `/review` dans Claude Code session sur commits `fdee1af..3e648c6` (15+ commits Wave P0/P1/P2/SP-11 + RSC fix)
**Output** : 9 parallel subagents reports : Linter, Code Reviewer, Security, Quality+Style, Performance, etc.
**Document** : `.claude/docs/state/AUDIT_NATIVE_REVIEW_2026-05-14.md`

#### W A.2 — Vercel Agent PR Review
**Run** : Vercel Agent enabled → auto-review next PR (create a small no-op PR to trigger)
**Output** : Vercel Agent report findings
**Document** : `.claude/docs/state/AUDIT_VERCEL_AGENT_2026-05-14.md`

#### W A.3 — `vercel:verification` Full-Story Test (3 routes critiques)
**Run** : invoke skill on `/`, `/audits/japhy/<auditId>`, `/clients/aesop/dna`
**Output** : browser → API → data → response trace per route
**Document** : `.claude/docs/state/AUDIT_FULL_STORY_2026-05-14.md`

#### W A.4 — `webapp-testing` Playwright E2E Suite (10+ tests)
**Run** : write Playwright tests for :
1. Login flow + dashboard load
2. /clients list + filter + sort + pagination
3. /clients/[slug] detail + tabs switch
4. /clients/[slug]/dna Brand DNA viewer
5. /audits/[c] page-tabs + drill-down
6. /audits/[c]/[a] detail + screenshots load + reco edit modal
7. /gsg 5 modes selector + copy brief
8. /funnel/[c] viz + drop-off chart
9. /learning vote queue
10. /settings 4 tabs + password change attempt
11. Mobile 360px + 768px responsive (visual diff)
**Output** : E2E test suite + run report
**Document** : `.claude/docs/state/AUDIT_PLAYWRIGHT_E2E_2026-05-14.md`

#### W A.5 — `design:design-critique` Visual Critique
**Run** : invoke skill on 5 main routes (`/`, `/clients`, `/audits/[c]`, `/audits/[c]/[a]`, `/gsg`)
**Output** : usability + hierarchy + cohesion feedback per route
**Document** : `.claude/docs/state/AUDIT_DESIGN_CRITIQUE_2026-05-14.md`

#### W A.6 — `design:accessibility-review` WCAG 2.1 AA
**Run** : audit color contrast, keyboard nav, touch targets, screen reader on 5 routes
**Output** : WCAG AA compliance report + violations
**Document** : `.claude/docs/state/AUDIT_A11Y_WCAG_2026-05-14.md`

#### W A.7 — `vercel:react-best-practices` TSX Quality Review
**Run** : skill audit on tous TSX shippés Wave P0/P1/P2 (27+ files)
**Output** : 57 perf optimization rules compliance + violations
**Document** : `.claude/docs/state/AUDIT_REACT_BEST_PRACTICES_2026-05-14.md`

#### W A.8 — `vercel:performance-optimizer` Lighthouse + Core Web Vitals
**Run** : Lighthouse audit on 5 main routes (Performance + Best Practices + SEO)
**Output** : scores + opportunities
**Document** : `.claude/docs/state/AUDIT_LIGHTHOUSE_2026-05-14.md`

#### W A.9 — `GStack` AI Team Review (post-install W0.3)
**Run** : invoke QA persona on audit detail page + design persona on Brand DNA viewer
**Output** : structured team feedback
**Document** : `.claude/docs/state/AUDIT_GSTACK_2026-05-14.md`

#### W A.10 — Data Fidelity Audit (Supabase queries vs disk truth)
**Run** : custom Python script that compares Supabase data vs `data/captures/<client>/<page>/recos_enriched.json` + `score_*.json`
**Output** : per-table fidelity report (% match, NULL fields, format mismatches)
**Document** : `.claude/docs/state/AUDIT_DATA_FIDELITY_2026-05-14.md`

#### W A.11 — Security Audit (Trail of Bits skills already installed)
**Run** : `codeql` + `semgrep` + `variant-analysis` + `supply-chain-risk-auditor` on shell + scripts
**Output** : HIGH/MEDIUM vulnerabilities
**Document** : `.claude/docs/state/AUDIT_SECURITY_2026-05-14.md`

#### W A.12 — Mobile Responsive Audit (manual + Playwright)
**Run** : Playwright headless at 360px, 768px, 1024px, 1440px on 5 routes + screenshot diff
**Output** : visual regression report
**Document** : `.claude/docs/state/AUDIT_MOBILE_RESPONSIVE_2026-05-14.md`

### Wave B — SYNTHESIS (P0, ~1h)

#### W B.1 — Master Bug List
**Steps** :
1. Aggregate findings from 12 audit reports
2. Categorize : Data fidelity / UI rendering / Interactions / Performance / A11y / Security / Mobile / Code quality
3. Severity ranking : P0 (broken), P1 (degraded UX), P2 (improvement), P3 (nice-to-have)
4. Effort estimate per bug : XS / S / M / L
5. Impact × effort priorization

**Output** : `.claude/docs/state/MASTER_BUG_LIST_2026-05-14.md` (the canonical source)

### Wave C — EXECUTION FIXES (P0 → P3, ~8-12h)

**Approach** : créer des sub-PRDs POST-audit basés sur les vrais bugs trouvés, PAS basés sur features top-down imaginées.

#### W C.1 — P0 Critical Fixes (~3-5h)
**Sub-PRDs créés via /ccpm post-audit** :
- (probable) `fix-data-fidelity-recos` : re-migrate depuis recos_enriched.json
- (probable) `fix-data-fidelity-scores` : re-migrate depuis score_*.json
- (probable) `fix-screenshots-prod-redirect`
- (probable) `fix-N-server-component-crashes` (autres RSC bugs trouvés par /review)
- (probable) `fix-rls-supabase-leaks`
- ... selon audit findings

**Pattern d'exécution** : utiliser Superpowers pour multi-step plan + TDD enforcement par fix

#### W C.2 — P1 Important Fixes (~2-4h)
**Sub-PRDs** :
- (probable) UX rendering bugs (empty states, loading skeletons not triggered)
- (probable) CRUD interactions bugs
- (probable) Mobile responsive fixes
- ... selon audit

#### W C.3 — P2 Improvements (~2-3h)
**Sub-PRDs** :
- (probable) A11y improvements (focus management, aria-labels)
- (probable) Performance optimizations (lazy loading, caching)
- (probable) Code quality improvements (react-best-practices violations)

### Wave D — VALIDATION (P0, ~2h)

#### W D.1 — Re-run /review post-fixes
**Goal** : verify P0 + P1 fixes don't introduce regressions

#### W D.2 — Re-run Playwright E2E
**Goal** : all 10+ tests passing post-fixes

#### W D.3 — Mathis Manual Validation
**Steps** :
1. Login webapp
2. Navigate les 10 routes principales
3. Test interactions (filter clients, edit reco, create audit)
4. Test mobile (DevTools 360px / 768px)
5. Verify screenshots load
6. Verify scores affichés
7. Verify recos riches (reco_text + anti_patterns)

**Acceptance** : Mathis confirme "OK ça ressemble enfin à ce que je voulais"

### Wave E — CLOSE (P2, ~1h)

#### W E.1 — BLUEPRINT v1.3 update
- New skills documented (skill-based-architecture, Superpowers, GStack, /review, Vercel Agent)
- Combo packs updated

#### W E.2 — MANIFEST §12 changelog 2026-05-14

#### W E.3 — CONTINUATION_PLAN_2026-05-15.md (next session)

## Non-Functional Requirements

### Doctrine immutables
- V26.AF, V3.2.1, V3.3 intacts
- Code doctrine ≤ 800 LOC, mono-concern, 8 axes
- Anti-patterns #1-12 respectés
- Skill cap ≤ 8/session (skill-based-architecture = META hors compte)

### Méthodologie nouvelle (anti-velocity)
- **AUDIT-FIRST** avant toute fix
- **CROSS-VALIDATION** : 5+ skills audit pour chaque dimension
- **TEST VISUEL OBLIGATOIRE** : Playwright E2E + screenshots before claim "shipped"
- **MATHIS-IN-LOOP** : validation manuelle obligatoire pré-merge
- **PRIORITIZED FIXES** : impact × effort, pas top-down feature list

### Performance
- Wave A audit cumul : ~3-4h wall-clock avec parallel agents
- Wave B synthesis : ~1h (LLM aggregation)
- Wave C execution : ~8-12h (par priority)
- Wave D validation : ~2h
- Wave E close : ~1h
- **TOTAL** : ~15-20h sur 2-3 sessions

### Sécurité
- Service_role JWT rotated AVANT toute autre action
- Trail of Bits skills run (codeql + semgrep + variant-analysis)
- Pas de leaked secrets in git history (rotation comprehensive)

### Documentation
- 12 audit reports dans `.claude/docs/state/AUDIT_*_2026-05-14.md`
- Master bug list canonical
- Eval reports skills POCs
- BLUEPRINT v1.3
- CONTINUATION_PLAN 2026-05-15

## Success Criteria

### Wave 0 — PREP
- [ ] JWT rotated
- [ ] skill-based-architecture installed + `skills/growthcro/` created + CLAUDE.md thin
- [ ] Superpowers + GStack installed
- [ ] Vercel Agent enabled

### Wave A — AUDIT (12 reports)
- [ ] Native /review report
- [ ] Vercel Agent report
- [ ] vercel:verification report (3 routes)
- [ ] Playwright E2E suite written (10+ tests)
- [ ] design:design-critique report (5 routes)
- [ ] design:accessibility-review WCAG AA report
- [ ] vercel:react-best-practices TSX review
- [ ] vercel:performance-optimizer Lighthouse report
- [ ] GStack AI team review
- [ ] Data fidelity audit (Supabase vs disk)
- [ ] Security audit (Trail of Bits)
- [ ] Mobile responsive audit

### Wave B — SYNTHESIS
- [ ] Master bug list ≥30 bugs identifiés
- [ ] Severity ranking P0/P1/P2/P3
- [ ] Effort estimates XS/S/M/L
- [ ] Impact × effort priorization

### Wave C — FIX
- [ ] All P0 critical bugs fixed
- [ ] All P1 important bugs fixed
- [ ] ≥50% P2 improvements addressed
- [ ] Per-fix : commit isolé + gate-vert
- [ ] Per-fix : Superpowers used for multi-step (TDD enforcement)

### Wave D — VALIDATION
- [ ] /review re-run : 0 P0 regression
- [ ] Playwright E2E : 10+/10+ passing
- [ ] Mathis validation manuelle : "OUI ça ressemble enfin à V26+"
- [ ] Lighthouse > 90 sur 5 main routes
- [ ] WCAG AA compliant

### Wave E — CLOSE
- [ ] BLUEPRINT v1.3
- [ ] MANIFEST §12 2026-05-14
- [ ] CONTINUATION_PLAN_2026-05-15

## Constraints & Assumptions

### Constraints
- Pas de FastAPI deploy (deferred V2)
- Pas de Reality monitor live (deferred V2)
- Pas de install lourde dep
- Service_role JWT rotate AVANT toute autre action sensitive
- Velocity DOWN — priority ON validation

### Assumptions
- Native /review available (Claude Code Team/Enterprise)
- Vercel Agent available (free tier or Pro)
- Playwright installed (skill webapp-testing déjà installé)
- All 12 audit skills run successful (sinon fallback documented)
- Mathis disponible ~2-3h pour validation manuelle (Wave D)

## Out of Scope

### V1 (explicit)
- FastAPI backend deploy
- Reality monitor live connectors
- GEO Monitor multi-engine
- Multi-tenant org switching
- New skills install au-delà des 3 stratosphère + 2 natives

## Dependencies

### Externes (humaines)
- Mathis ~3-4h cumulé (rotation JWT + Vercel Agent OAuth + validation manuelle finale)
- Consultant Growth Society 30 min (optional final feedback)

### Externes (techniques)
- Claude Code Team/Enterprise (native /review)
- Vercel Free/Pro (Vercel Agent)
- Pillow + supabase-py + Playwright (déjà installés)
- Disk ~100 MB skills installs

### Internes
- main HEAD `3e648c6` (master PRD shipped pre-clear)
- 438 `recos_enriched.json` + score_*.json files
- Supabase prod 56×185×3045 (poor format) + 1840 WebP screenshots
- CLAUDE.md + memory/ + docs/ (input skill-based-architecture)

### Sequencing
```
Wave 0 — PREP (~1.5h) [foreground sequential]
  W0.1 JWT rotate (Mathis)
  W0.2 skill-based-architecture install + run
  W0.3 Superpowers + GStack install
  W0.4 Vercel Agent enable

Wave A — AUDIT (~3-4h) [12 parallel agents background]
  W A.1-A.12 lance en parallel (skill cap = 8 active, donc batch 2)
       │
Wave B — SYNTHESIS (~1h) [foreground]
  W B.1 Master bug list
       │
Wave C — FIX (~8-12h) [agents background par priority]
  C.1 P0 critical (5h)
  C.2 P1 important (3h)
  C.3 P2 improvements (2h)
       │
Wave D — VALIDATION (~2h) [foreground + Mathis]
  D.1 /review re-run
  D.2 Playwright E2E
  D.3 Mathis manual
       │
Wave E — CLOSE (~1h)
  E.1 BLUEPRINT v1.3
  E.2 MANIFEST §12
  E.3 CONTINUATION_PLAN 2026-05-15
```

**Total wall-clock** : ~15-20h sur 2-3 sessions Claude Code.

## Skills à exploiter — chaque skill explicitement intégré dans le plan

| Skill | Wave où utilisé | Output attendu |
|---|---|---|
| `skill-based-architecture` | W0.2 (install + run) | `skills/growthcro/` consolidé, CLAUDE.md thin |
| `Superpowers` | W0.3 + Wave C (per-fix TDD) | Multi-step plans + tests per fix |
| `GStack` | W0.3 + Wave A.9 | AI team review (QA + design personas) |
| Native `/review` | Wave A.1 + Wave D.1 | 9 parallel subagents reports |
| Vercel Agent | W0.4 + Wave A.2 | AI PR Review + production investigation |
| `vercel:verification` | Wave A.3 | Full-story 3 routes critiques |
| `webapp-testing` | Wave A.4 + Wave D.2 | Playwright E2E suite |
| `design:design-critique` | Wave A.5 | Usability + hierarchy + cohesion |
| `design:accessibility-review` | Wave A.6 | WCAG 2.1 AA compliance |
| `vercel:react-best-practices` | Wave A.7 | 57 perf rules audit |
| `vercel:performance-optimizer` | Wave A.8 | Lighthouse + Core Web Vitals |
| Trail of Bits (codeql, semgrep, etc.) | Wave A.11 | Security HIGH/MEDIUM |
| `frontend-design` | Wave C (fixes UI) | Premium frontend per-fix |
| `vercel:nextjs` | Wave C (fixes RSC) | Next.js App Router expert |
| `vercel:env-vars` | Wave A.3 + W C debug | Env management |
| `data:write-query` | Wave A.10 + Wave C.1 | SQL pour data fidelity check + re-migration |
| `data:explore-data` | Wave A.10 | Profile Supabase data quality |
| `data:validate-data` | Wave B.1 | QA validation accuracy |
| `ccpm` | Toutes Waves | PRD → tasks → agents orchestration |
| `product-management:write-spec` | Wave C (post-audit sub-PRDs) | Sub-PRDs basés audit findings |
| `product-management:sprint-planning` | Pre-Wave C | Plan sprint capacity |
| `product-management:product-brainstorming` | Wave B.1 | Brainstorm fix approaches |
| `simplify` | Per-fix post-commit | Review fixes quality |

## Plan d'exécution session-par-session (post-clear)

### Session 1 — PREP + AUDIT (Wave 0 + Wave A, ~5-6h)
1. Read CLAUDE.md init steps (12 obligatoires)
2. Read CONTINUATION_PLAN_2026-05-14.md + this PRD + SKILLS_DEEP_RESEARCH
3. Mathis : rotate JWT (5 min)
4. Install skill-based-architecture + Superpowers + GStack
5. Enable Vercel Agent
6. Run Wave A : 12 audit reports in parallel (batch 2-3 à la fois pour skill cap)
7. Commit audit reports

### Session 2 — SYNTHESIS + FIX P0 (Wave B + C.1, ~6-7h)
1. Master bug list aggregation
2. Sub-PRDs P0 critical via /ccpm
3. Launch agents background P0 fixes
4. Merge + push
5. Re-test /review + Playwright

### Session 3 — FIX P1/P2 + VALIDATION + CLOSE (Wave C.2-3 + D + E, ~5-7h)
1. P1 + P2 fixes background agents
2. Wave D validation : /review re-run + Playwright + Mathis manual
3. Wave E close : BLUEPRINT v1.3 + MANIFEST + CONTINUATION_PLAN

## Trigger phrase post-clear

```
Lis CLAUDE.md init steps. Puis :
1. .claude/docs/state/CONTINUATION_PLAN_2026-05-14.md
2. .claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md (MEGA PRD)
3. .claude/docs/state/SKILLS_DEEP_RESEARCH_2026-05-13.md

Lance Wave 0 PREP : install skill-based-architecture + Superpowers + GStack, enable Vercel Agent. Puis Wave A AUDIT : 12 parallel audit reports.
```

---

## Notes critiques

1. **Méthodo inversée vs hier** : audit-first, pas velocity-first
2. **Skills stratosphère TOUS utilisés** : 22+ skills mentionnés ont chacun un rôle explicite dans le plan
3. **Cross-validation 12 dimensions** : éliminer single-point-of-failure du diagnostic
4. **Mathis-in-loop validation manuelle** : pré-merge obligatoire Wave D.3
5. **Sub-PRDs créés POST-audit** : prioritized par severity, pas par feature
6. **Pas de hubris velocity** : 0 commit Wave C sans gate-vert + Playwright test
7. **Self-contained reprise** : CONTINUATION_PLAN_2026-05-14 + ce PRD suffisent

### Position rappel Mathis
*"perfection dès le départ"* · *"avant-garde, pas best CRO B2B 2024"* · *"je veux comprendre comme un humain"* · *"AU CARRÉ"*.

Ce plan = méthodologie 2026 anti-velocity, audit-first, multi-agent cross-validation, mathis-in-loop. **AU CARRÉ**.

---

**Première action post-clear** : trigger phrase ci-dessus. Wave 0 + Wave A en 1 session si energy permits.
