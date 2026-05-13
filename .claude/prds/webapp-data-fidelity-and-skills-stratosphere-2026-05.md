---
name: webapp-data-fidelity-and-skills-stratosphere-2026-05
description: MEGA PRD — fix le vrai gap "écran de fumée" en webapp Vercel via re-migration data riche (recos_enriched.json + score_*.json) + activation 3 skills stratosphériques (skill-based-architecture + Superpowers + GStack) + 2 features natives gratuites (/review + Vercel Agent). 8 sub-PRDs sur 3 Waves. Critical reset après diagnostic franc 2026-05-13.
status: active
created: 2026-05-13T14:33:37Z
parent_prd: post-stratosphere-roadmap
wave: data-fidelity-stratosphere
priority: P0
---

# PRD: webapp-data-fidelity-and-skills-stratosphere-2026-05

> **MEGA PRD critical reset** post-diagnostic franc 2026-05-13.
>
> Le user a vu la webapp Vercel et constaté que c'est **toujours un écran de fumée** : recos minimalistes (`per_01`, `ux_07`, `tech_03`), "Pas de scores disponibles", captures bugguées (broken images). C'est PAS un bug d'affichage — c'est une **migration data sur le mauvais fichier source**.
>
> **8 sub-PRDs** organisés en **3 Waves** (Data Fidelity P0 + Skills Stratosphère P1 + Cleanup P2). Effort ~10-15h wall-clock avec agents background.

## Executive Summary

Post-diagnostic franc 2026-05-13 :

### Root cause #1 — Data migration sur mauvaise source
- **Migré (mauvais)** : `deliverables/growth_audit_data.js` = bundle V27 consolidated avec **format V21 cluster PAUVRE** (criterion_id uppercase agrégé `HERO_ENSEMBLE`, `reco_text: NULL`, `anti_patterns: 0`)
- **Devrait migrer** : `data/captures/<client>/<page>/recos_enriched.json` (438 fichiers, format V13 riche avec `reco_text` long + `anti_patterns[]` + `oco_anchors[]`)
- **Impact UI** : `RichRecoCard` ne peut PAS render le format V26 (sections Pourquoi / Comment faire) car `content_json.reco_text` est NULL.

### Root cause #2 — Scores not migrated
- `audit.scores_json.pillars` contient juste `{pillars: [...]}` du bundle, format flat
- **Devrait contenir** : data agrégée depuis `score_hero.json`, `score_persuasion.json`, `score_ux.json`, `score_coherence.json`, `score_psycho.json`, `score_tech.json` (6 per page)
- Chaque score_*.json a : `score100`, `rawTotal`, `max`, `killerTriggered`, `criteria[]` (avec id, label, score, max, verdict, evidence)
- **Impact UI** : `PillarsSummary` affiche "Pas de scores disponibles"

### Root cause #3 — Screenshots Supabase Storage redirect
- Upload terminé (1840/1840 ✓ post-WebP conversion)
- Screen utilisateur 2026-05-13 montre still broken-image icons
- **À débugger** : `NEXT_PUBLIC_SUPABASE_URL` en prod Vercel ? `screenshotPublicUrl()` returns null ? URL Supabase publique 404 ?

### Solution stratégique
Activer les **3 skills stratosphériques + 2 features natives** identifiés dans deep research 2026-05-13 (cf `SKILLS_DEEP_RESEARCH_2026-05-13.md`) AVANT de fix les root causes — pour bénéficier du multi-agent review + strategic understanding.

**Sequence optimale** :
1. Wave B (skills) installés PREMIER pour avoir Native /review qui peut auditer Wave A fixes
2. Wave A (data fidelity) avec skill-based-architecture + GStack + Superpowers actifs
3. Wave C (cleanup) closing

## Problem Statement

### Le constat user 2026-05-13 (textuel)
> *"franchement je suis allé voir, y'a rien qui va, c'est toujours un écran de fumée, y'a pas les captures, elles sont bugguées, y'a pas l'audit du html de la V26, y'a pas les problèmes évoqués, pas les recos.. ça n'a rien à voir."*

### Ce qu'on voit en prod (Japhy / collection / collection-chat)
- `Scores doctrine` : "Pas de scores disponibles"
- `Captures` : 2 broken-image icons (Desktop fold + Mobile fold)
- `Recos prioritaires · 11` : `per_01`, `ux_07`, `tech_03` (juste criterion_id rendu comme title)
- Pas de `reco_text` long
- Pas de section "Pourquoi" / "Comment faire"
- Pas d'anti_patterns affichés

### Ce qui devrait être visible (V26 HTML reference)
- 6 piliers progress bars (Hero 4.5/18, Persuasion 7.0/18, etc.) avec couleurs
- Score global + killer notes
- Captures desktop/mobile thumbnails clickables
- Recos avec full reco_text (problème + reco + pourquoi)
- Anti-patterns détaillés (pattern + why_bad + instead_do + examples_good)

### Pourquoi maintenant
1. **User patience épuisée** — "ça commence à me souler"
2. **10 sub-PRDs shipped** sans fix le data fidelity gap = travail jeté si rien ne s'affiche
3. **Session ends soon** (user va clear context) — doit documenter tout pour reprise propre
4. **Skills stratosphère identifiés** mais pas installés — opportunity cost massive

## User Stories

### US-1 — Mathis (data fidelity, urgent)
*Comme founder qui voit "Pas de scores disponibles" et `per_01`/`ux_07` minimalistes, je veux que la webapp affiche les VRAIS scores V13 (6 piliers structurés + criteria + killer notes) ET les VRAIS recos enriched (reco_text long + anti_patterns), exactement comme la V26 HTML.*

**AC** :
- ✓ `/audits/<client>/<auditId>` affiche les 6 piliers avec scores réels (ex: Hero 12/18, score100 66.7)
- ✓ Recos affichées avec `reco_text` complet (sections Pourquoi / Comment faire)
- ✓ Anti_patterns rendus (pattern + why_bad + instead_do + examples_good)
- ✓ Killer notes badges si applicable
- ✓ Min 5 clients testés (japhy, weglot, stripe, aesop, wise)

### US-2 — Mathis (captures fonctionnelles)
*Comme founder qui a uploadé 1840 WebP à Supabase Storage, je veux que les thumbnails s'affichent ENFIN sur https://growth-cro.vercel.app/audits/<client>/<auditId>.*

**AC** :
- ✓ Click un audit → panel screenshots à droite affiche desktop + mobile thumbnails WebP
- ✓ Click thumbnail → ouvre new tab avec image full
- ✓ Test 5 clients différents (japhy, weglot, stripe, aesop, wise)
- ✓ 0 broken-image icon (sauf si fichier réellement manquant Supabase Storage)

### US-3 — Mathis (strategic understanding skills)
*Comme founder solo qui doit comprendre la webapp stratégiquement comme un humain, je veux que skill-based-architecture distille toute la doctrine en `skills/growthcro/` single source of truth.*

**AC** :
- ✓ `skills/growthcro/` créé avec SKILL.md + rules/ + workflows/ + references/ + docs/
- ✓ CLAUDE.md + AGENTS.md devenus thin entry shells (≤ 20 lignes)
- ✓ Nouvelle session Claude Code : agent répond "où est définie la règle X ?" → route vers `skills/growthcro/rules/`
- ✓ Test cross-tool potentiel : `.cursor/rules/growthcro.mdc` créable plus tard sans duplication

### US-4 — Mathis (multi-agent debug review)
*Comme dev qui a shipped 10 sub-PRDs sans review humain, je veux que native /review + Vercel Agent + GStack auditent le code récent pour catch les bugs subtils encore présents.*

**AC** :
- ✓ Native /review run sur commits `fdee1af..83bad9a` (15 commits) → min 5 bugs/improvements identifiés
- ✓ Vercel Agent enabled + 1 test PR review fait
- ✓ GStack QA persona POC sur audit detail page (sample 1 audit) → feedback structured

## Functional Requirements

### Wave A — Data Fidelity (P0 critique, blocking user satisfaction)

#### SP-A1 — Re-migrate recos depuis `recos_enriched.json` (P0)
**Effort** : M, 2-3h
**Files** :
- `scripts/migrate_recos_enriched_to_supabase.py` (NEW, mimick pattern migrate_v27)
- Walk `data/captures/<client>/<page>/recos_enriched.json` (438 fichiers)
- Pour chaque reco dans `.recos[]` array :
  - DELETE existing recos pour cet (audit_id) en Supabase (clean slate)
  - INSERT nouveaux recos avec :
    - `criterion_id` lowercase (hero_01, ux_04, etc.)
    - `priority`, `effort`, `lift` (with int→S/M/L bucket conversion réutilisée)
    - `content_json` = TOUT le reco object (incl. reco_text, anti_patterns, oco_anchors, evidence, ice_score, etc.)
    - `title` = `criterion_id` (since reco.title is null dans format V13)
- Idempotent via upsert
- DRY-RUN safe

**Acceptance** :
- [ ] Script DRY-RUN OK
- [ ] Real run : 438 audits × ~25 recos = ~10000 recos updated
- [ ] Sample query Supabase : `select content_json->>'reco_text' from recos limit 1` → returns non-null long string
- [ ] `/audits/japhy/<auditId>` shows RichRecoCard with reco_text + anti_patterns rendered

#### SP-A2 — Re-migrate scores depuis `score_*.json` (P0)
**Effort** : M, 2-3h
**Files** :
- `scripts/migrate_scores_to_supabase.py` (NEW)
- Walk `data/captures/<client>/<page>/score_*.json` (6 pillars × N pages × 56 clients)
- For each (client, page) : aggregate 6 score files into 1 `scores_json` :
  ```json
  {
    "pillars": {
      "hero": { "score": 12, "max": 18, "score100": 66.7, "killer": false, "criteria": [...] },
      "persuasion": { "score": 7, "max": 18, ... },
      "ux": { ... }, "coherence": { ... }, "psycho": { ... }, "tech": { ... }
    },
    "killer_notes": [...]
  }
  ```
- UPDATE audits SET scores_json = ... WHERE client + page_type matches

**Acceptance** :
- [ ] 438 audits updated avec scores_json riches
- [ ] Sample query : `select scores_json->'pillars'->'hero'->>'score100' from audits limit 1` → returns "66.7" or similar
- [ ] `/audits/japhy/<auditId>` shows 6 piliers progress bars (Hero, Persuasion, UX, Cohérence, Psycho, Tech) avec scores réels

#### SP-A3 — Debug + fix screenshots prod (P0)
**Effort** : S, 1h
**Files** : verification only, fix selon root cause
**Steps** :
1. Verify `NEXT_PUBLIC_SUPABASE_URL` actually set in Vercel Production env :
   ```bash
   vercel env ls production | grep SUPABASE_URL
   ```
2. Test URL Supabase Storage publique manuelle :
   ```bash
   curl -I "https://xyazvwwjckhdmxnohadc.supabase.co/storage/v1/object/public/screenshots/japhy/collection/desktop_asis_fold.webp"
   ```
3. Test redirect via webapp route :
   ```bash
   curl -I "https://growth-cro.vercel.app/api/screenshots/japhy/collection/desktop_asis_fold.png"
   ```
   → Doit retourner 302 avec Location header vers Supabase
4. Si fail : check `getAppConfig().supabaseUrl` retourne la bonne valeur en prod
5. Si OK URL mais image not loading : check CSP / CORS headers

**Acceptance** :
- [ ] `/api/screenshots/japhy/collection/desktop_asis_fold.png` returns 302 OR 200 image
- [ ] Visible thumbnails dans `/audits/japhy/<auditId>` browser
- [ ] Open in new tab fonctionne (full image)

#### SP-A4 — Native `/review` + Vercel Agent (P0)
**Effort** : S, 30-60 min
**Files** :
- `.claude/docs/state/CODE_REVIEW_NATIVE_2026-05-13.md` (NEW, findings)
**Steps** :
1. Native /review : run dans Claude Code session sur commits `fdee1af..83bad9a` (15 commits récents)
2. Vercel Agent : enable in Dashboard
3. Document top 10 findings + fix top 3 quick wins

**Acceptance** :
- [ ] /review run + findings doc
- [ ] Vercel Agent enabled + tested 1 PR
- [ ] Top 3 quick wins committed (if any)

### Wave B — Skills Stratosphère (P1)

#### SP-B1 — Install `skill-based-architecture` (P1)
**Effort** : S-M, 45 min
**Files** :
- `skills/skill-based-architecture/` (NEW via git clone)
- `skills/growthcro/` (NEW via meta-skill run, structure SKILL.md + rules/ + workflows/ + references/ + docs/)
- `CLAUDE.md` reduced to thin entry shell ≤ 20 lignes (route to skills/growthcro/)
- `AGENTS.md` idem (symlink déjà CLAUDE.md, so handled)

**Steps** :
1. `git clone https://github.com/WoJiSama/skill-based-architecture.git skills/skill-based-architecture`
2. Invoke skill : `"Use skill-based-architecture to consolidate growth-cro project rules into skills/growthcro/"`
3. Verify structure produced
4. Manually edit CLAUDE.md to thin shell
5. Test new Claude Code session : agent should route to skills/growthcro/

**Acceptance** :
- [ ] `skills/growthcro/SKILL.md` exists ≤ 100 lines
- [ ] `skills/growthcro/rules/` contains hard rules
- [ ] `skills/growthcro/workflows/` contains procedures
- [ ] `skills/growthcro/references/` contains architecture + gotchas
- [ ] CLAUDE.md ≤ 30 lines (thin shell)
- [ ] Cross-session test : agent knows doctrine without reading 12 init steps

#### SP-B2 — Install + POC `Superpowers` (P1)
**Effort** : M, 1-2h
**Steps** :
1. `npx skills add obra/superpowers`
2. POC : use Superpowers to plan + execute a small task (e.g., SP-A3 fix screenshots if not done)
3. Eval report : `.claude/docs/state/SUPERPOWERS_POC_2026-05-13.md`
4. Verdict KEEP/DROP

#### SP-B3 — Install + POC `GStack` (P1)
**Effort** : M, 1-2h
**Steps** :
1. `npx skills add https://github.com/garrytan/gstack`
2. POC : use GStack QA persona to review audit detail page rendering
3. Eval report : `.claude/docs/state/GSTACK_POC_2026-05-13.md`
4. Verdict KEEP/DROP

### Wave C — Cleanup & Continuation (P2)

#### SP-C1 — Update BLUEPRINT v1.3 + MANIFEST §12 (P2)
**Effort** : S, 30 min
**Files** :
- `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` v1.2 → v1.3
- `.claude/docs/reference/GROWTHCRO_MANIFEST.md` §12 changelog
**Content** :
- Add 3 new skills + 2 natives (with KEEP/DROP verdicts post-POC)
- Add Wave A data fidelity success metrics
- Update combo packs if needed

#### SP-C2 — CONTINUATION_PLAN_2026-05-14 (P2)
**Effort** : S, 30 min
**Files** :
- `.claude/docs/state/CONTINUATION_PLAN_2026-05-14.md` (NEW post-clear reprise)
**Content** :
- Closing snapshot 2026-05-13 (master PRD + 8 sub-PRDs status)
- Wave A/B/C status
- Mathis actions humaines updated
- Next session entry point clear

## Non-Functional Requirements

### Doctrine immutables
- V26.AF immutable (vacuous post persona_narrator removal)
- V3.2.1 + V3.3 piliers intacts
- Code doctrine ≤ 800 LOC, mono-concern
- Pas de `process.env[key]` dynamic
- Anti-patterns #1-12 respectés (skill cap ≤ 8, etc.)

### Performance
- Re-migration recos (Wave A SP-A1) : ~5-10 min compute (438 fichiers)
- Re-migration scores (Wave A SP-A2) : ~5-10 min compute
- Pas de bundle size increase webapp (data layer change only)
- Page load /audits/<c>/<a> : < 2s sur 4G (Supabase EU)

### Sécurité
- Service_role JWT — Mathis doit rotater (URGENT, leak public repo)
- Pas de exposition côté client
- RLS preserved sur recos + audits + clients

### Documentation
- Eval reports POCs dans `.claude/docs/state/`
- MANIFEST §12 changelog
- BLUEPRINT v1.3 published

## Success Criteria

### Wave A (data fidelity) — BLOCKING
- [ ] SP-A1 : recos riches Supabase, `reco_text` non-null, anti_patterns rendus
- [ ] SP-A2 : scores 6 piliers per page, `PillarsSummary` shows real bars
- [ ] SP-A3 : screenshots prod visible (thumbnails clickables)
- [ ] SP-A4 : /review + Vercel Agent enabled + findings docs

### Wave B (skills) — NICE TO HAVE
- [ ] SP-B1 : `skills/growthcro/` consolidé + CLAUDE.md thin
- [ ] SP-B2 : Superpowers verdict KEEP/DROP
- [ ] SP-B3 : GStack verdict KEEP/DROP

### Wave C (cleanup)
- [ ] SP-C1 : BLUEPRINT v1.3 + MANIFEST §12
- [ ] SP-C2 : CONTINUATION_PLAN_2026-05-14 self-contained

### Mathis validation finale
- [ ] Mathis confirme "OUI ça ressemble enfin à la V26 + interactivité réelle"
- [ ] Test sur 5 clients : data riche affichée
- [ ] 0 régression V26.AF / V3.2.1 / V3.3

## Constraints & Assumptions

### Constraints
- Pas de FastAPI deploy (deferred V2)
- Pas de Reality monitor live (deferred V2)
- Pas de install nouvelle dep Node lourde (Pillow OK pour scripts Python)
- Skill cap ≤ 8/session
- Service_role JWT à rotater AVANT toute autre session sensitive

### Assumptions
- Format `recos_enriched.json` cohérent across 438 fichiers (verified sample japhy)
- Format `score_*.json` cohérent (6 pillars structured)
- Supabase Storage URLs publiques fonctionnent (à confirmer SP-A3)
- skill-based-architecture run correct sur growthcro repo
- Native /review available (Claude Code Team/Enterprise plan)
- Vercel Agent free tier suffisant

## Out of Scope

### V1 (explicitement)
- FastAPI backend deploy (trigger audit/GSG UI)
- Reality monitor connectors (GA4 + Meta + Google + Shopify + Clarity)
- GEO Monitor multi-engine
- Multi-tenant org switching
- Notion auto-sync
- Slack notifications

## Dependencies

### Externes (humaines)
- Mathis ~1h validation finale (test 5 clients post Wave A)
- Mathis OAuth Vercel Agent (already connected)
- Mathis rotation service_role JWT (URGENT 5 min)

### Externes (techniques)
- Claude Code Team/Enterprise plan (for /review)
- Vercel Free tier or Pro
- Pillow + supabase-py (already installed for scripts)
- ~50 MB disk skills installs

### Internes
- main HEAD `83bad9a` (skills research shipped)
- 438 `recos_enriched.json` + `score_*.json` files sur disque
- Supabase prod : 56 clients × 185 audits × 3045 recos (poor format actuel)
- Supabase Storage : 1840 WebP screenshots (good)

### Sequencing
```
Wave A — Data Fidelity (P0 critical, ~6-8h)
  SP-A1 re-migrate recos    ┐
  SP-A2 re-migrate scores   ├─ parallel, 2 agents background
  SP-A3 fix screenshots prod ┘
       │
       └─ SP-A4 native /review + Vercel Agent (parallel ou post)

Wave B — Skills Stratosphère (P1, ~3-5h)
  SP-B1 skill-based-architecture (foreground, ~45 min)
       │
       ├─ SP-B2 Superpowers POC ┐
       └─ SP-B3 GStack POC     ┘ parallel après SP-B1

Wave C — Cleanup (P2, ~1h)
  SP-C1 BLUEPRINT v1.3
  SP-C2 CONTINUATION_PLAN 2026-05-14
```

**Critical path** : Wave A first (data fidelity blocking) → Wave B (skills) → Wave C (cleanup).

**Total wall-clock estimé** : ~10-14h avec parallel agents.

## Skills à exploiter pour exécution

- `ccpm` (orchestration master)
- `product-management:write-spec` (sub-PRD docs)
- `Superpowers` (post SP-B2 install — pour multi-step workflows)
- `GStack` (post SP-B3 install — pour AI team review)
- Native `/review` (post SP-A4 — pour audit code)
- `skill-based-architecture` (post SP-B1 install — pour project rules consolidation)
- `frontend-design` (déjà installé)
- `vercel-react-best-practices` (déjà installé)
- `webapp-testing` (déjà installé, Playwright pour SP-A3 verify)

## Plan d'exécution session-par-session (post-clear context)

### Session 1 (reprise post-clear)
**Goal** : Wave A SP-A1 + SP-A2 + SP-A3 parallel
1. Read CLAUDE.md init steps
2. Read `.claude/docs/state/CONTINUATION_PLAN_2026-05-14.md` (will be created at end of current session by SP-C2)
3. Read this PRD + `SKILLS_DEEP_RESEARCH_2026-05-13.md`
4. Create 3 worktrees + launch 3 agents background pour SP-A1/A2/A3
5. Wait notifications, merge, push, verify prod

### Session 2 (Wave B skills)
1. SP-B1 foreground (skill-based-architecture)
2. SP-B2 + SP-B3 background parallel (Superpowers + GStack POCs)
3. Eval reports + verdicts

### Session 3 (cleanup + final)
1. SP-C1 BLUEPRINT v1.3
2. SP-C2 CONTINUATION_PLAN finalized
3. Mathis validation finale (test 5 clients)

---

## Notes critiques

1. **Le user va clear context après ce sub-PRD**. La prochaine session DOIT pouvoir reprendre depuis `.claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md` + CONTINUATION_PLAN_2026-05-14.md sans contexte session précédente.

2. **Service_role JWT à rotater AVANT toute autre action sensitive** (repo public, JWT exposé). Mathis doit faire ça en 5 min lui-même.

3. **Wave A est blocking** pour user satisfaction. Si Wave A fail, on n'avance pas sur le reste. Tout investissement skills Wave B est inutile si la data n'est pas fidèle.

4. **Strategy choice** : on installe Wave B (skills) **APRÈS** Wave A (data fix) parce que :
   - Wave A est urgent (user frustration)
   - Wave A peut être fait sans les skills stratosphère (scripts Python autonomes)
   - Wave B donnera des bénéfices durables (single source of truth) mais pas immédiatement visible

5. **Position rappel Mathis** : *"perfection dès le départ"* · *"avant-garde, pas best CRO B2B 2024"*. Ce PRD vise : (a) parité V26 réelle (data riche), (b) intégration skills 2026 stratosphériques. Both align.

---

**Première action post-clear** : créer 3 worktrees pour SP-A1/A2/A3 + lance 3 agents background. ~6-8h ETA pour Wave A complete.
