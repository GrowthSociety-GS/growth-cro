# Wave A — AUDIT SUMMARY (master canonical) — 2026-05-14

> Synthèse des 12 audits du MEGA PRD AUDIT-FIRST `webapp-data-fidelity-and-skills-stratosphere-2026-05`. Source de vérité pour Wave B synthesis + Wave C execution.

## 0. TL;DR brutal

**Mathis avait raison sur le diagnostic root**. La webapp est un **écran de fumée légitime** parce que :

> 🎯 **Root cause confirmé (A.10) : `scripts/migrate_v27_to_supabase.py` lit `deliverables/growth_audit_data.js` (V21 bundle pauvre) au lieu des 438 `data/captures/<c>/<p>/recos_enriched.json` (V13 enricher riche).**
>
> Conséquence : Supabase `recos.content_json` a **0%** des champs UI-attendus (`reco_text`, `anti_patterns`, `feasibility`, `pillar`, `severity`, `enricher_version`, `business_category`, `schwartz_awareness`). `RichRecoCard.tsx` → `extractRichReco()` renvoie des defaults vides → seuls les pills priority/criterion_id/effort/lift s'affichent → titre fallback à `criterion_id` → section "Pourquoi / Comment faire" jamais rendue.

**Bonne nouvelle** : l'architecture est saine. Pas de réécriture nécessaire.
- Code RSC-first propre (A.8) — Lighthouse 72-85 → 88-95 avec 5 fixes
- 31 findings React surface (A.7) — bones structurales solides
- Security posture **healthy** (A.11) — RLS solide, service_role server-only confined
- A11y foundation présent (A.6) — skip link, focus-visible, prefers-reduced-motion ; mais contrast pervasive FAIL

## 1. Stats globales

| Audit | Status | P0 | P1 | P2 | P3 | Verdict 1-line |
|---|---|---|---|---|---|---|
| A.1 Code review | ✅ | 3 | 9 | 11 | 4 | `/api/learning/proposals/review` POST sans auth (security hole) |
| A.2 Vercel Agent | 🟡 doc | – | – | – | – | Bloqué OAuth Mathis-side |
| A.3 vercel:verification | 🟡 doc | – | – | – | – | Bloqué dev server live, plan prêt |
| A.4 Playwright E2E | ✅ spec | – | – | – | – | 23 tests écrits dans `wave-a-2026-05-14.spec.ts`, run next session |
| A.5 Design critique | ✅ | 3 | 4 | 5 | – | Premium 5.2/10 + Inter font fiction + pill ambigu |
| A.6 A11y WCAG AA | ✅ | 6 | 11 | 9 | – | **FAIL** — contrast `--gc-muted` 4.13:1 + Modal pas focus trap |
| A.7 React best-practices | ✅ | 3 | 8 | 11 | 6 | Index-as-key + router.refresh manquant + silent auth fail |
| A.8 Lighthouse / perf | ✅ | 0 | 5 | 7 | – | Surprisingly clean ; 5 fixes surgicaux |
| A.9 GStack | 🟡 doc | – | – | – | – | Bloqué install (auto-classifier) |
| A.10 Data fidelity | ✅ | 7 | 7 | 4 | – | **🔴 ROOT CAUSE — wrong migration source** |
| A.11 Security | ✅ | 3 | 5 | 6 | – | Open redirect + Anthropic key history + JWT rotation pending |
| A.12 Mobile responsive | ✅ | 5 | 10 | 8 | – | ~60% ready ; Modal width inline override + grid overrides |
| **TOTAL exécutable** | **9/12** | **30** | **59** | **61** | **10** | **160 findings** |

3 audits différés (A.2 OAuth, A.3 dev server, A.9 install bloqué) ont des plans `.claude/docs/state/AUDIT_*_2026-05-14.md` rédigés et activables next session.

## 2. P0 canonical list (à fixer Wave C P0)

### P0.A — DATA FIDELITY (root cause user-visible)
1. **A.10** — Migration script lit mauvais bundle. `scripts/migrate_v27_to_supabase.py` → archive ; **créer `scripts/migrate_disk_to_supabase.py`** qui walks `data/captures/<c>/<p>/` (recos_enriched.json + score_page_type.json + score_<pillar>.json + brand_dna + design_grammar).
2. **A.10** — 6 champs critiques absents Supabase : reco_text, anti_patterns, feasibility, pillar, severity, schwartz_awareness.
3. **A.10** — Tables Supabase à étendre : `scores_pillars`, `scores_criteria`, `anti_patterns`, `overlays_semantic`, `overlays_contextual` (split optionnel pour queryability).
4. **A.10** — 5 clients zero-reco à investiguer post-migration.

### P0.B — SECURITY (rotate + patch avant deploy suivant)
5. **A.11** — Open redirect dans `webapp/apps/shell/app/auth/callback/route.ts:17` + `app/login/page.tsx:22+40` — valider `redirect.startsWith('/') && !startsWith('//')`. ⏱ ~5 min.
6. **A.11 + A.1 convergence** — `webapp/apps/shell/app/api/learning/proposals/review/route.ts:1-78` POST sans `requireAdmin()` + accepts user-supplied `reviewed_by`. ⏱ ~10 min.
7. **A.11** — Anthropic API key historiquement leaked (refs dans WAKE_UP_NOTE_2026-04-19 + memory/HISTORY) — confirmer si commitée historiquement ou rotater.
8. **W0.1 (PRD)** — service_role JWT Supabase rotation (Mathis-side, BLOCKING).

### P0.C — A11Y WCAG (FAIL → AA)
9. **A.6** — `var(--gc-muted) = #98a2b3` sur `var(--gc-bg) = #0c1018` = 4.13:1 (fails 4.5:1). Fix 1 ligne CSS → bump `--gc-muted` à un shade plus clair (#a6b0c0 ou similaire). ⏱ ~5 min.
10. **A.6** — Pill borders `rgba(*, 0.45)` sur `#0c1018` = 2.3-2.6:1 (fails 3:1 UI). Bump opacity → 0.6+. ⏱ ~10 min.
11. **A.6** — `packages/ui/src/components/Modal.tsx:32-37` — pas de focus trap, pas de restore-focus on close. ⏱ ~30 LOC focus-trap helper.
12. **A.6** — `<a aria-disabled>` / `<span aria-disabled>` comme fake-disabled controls (GSG Open preview, Export PDF pill, pagination). Remplacer par `<button disabled>` ou `<a aria-disabled tabIndex={-1} onClick={e => e.preventDefault()}>`. ⏱ ~20 min.

### P0.D — REACT/UX BROKEN
13. **A.7** — Index-as-key in user lists (RichRecoCard:L73 examples_good, JudgeScoreCard:L88 remarks). ⏱ ~10 min.
14. **A.7** — Missing `router.refresh()` after vote in `ProposalQueue` — KPI stays stale. ⏱ ~5 min.
15. **A.7 + A.1 convergence** — `getCurrentRole().catch(() => null)` silently masks auth failures in `audits/[c]/[a]/page.tsx:36` + `clients/[slug]/page.tsx:31`. Surface l'erreur avec `<ErrorFallback>` ou redirect.

### P0.E — MOBILE BROKEN (360px)
16. **A.12** — `webapp/apps/shell/components/settings/UsageTab.tsx:24` — inline `gridTemplateColumns: repeat(4, ...)` force 4 cols à 360px. Replace par responsive grid. ⏱ ~5 min.
17. **A.12** — `webapp/apps/shell/components/learning/ProposalList.tsx:80-85` — inline `"1fr auto auto auto"` overflow 360px. ⏱ ~10 min.
18. **A.12** — `webapp/packages/ui/src/components/Modal.tsx:49` — inline `width: "560px"` etc override le `min(640px, 100%)` clamp → horizontal overflow 360px. Fix : `width: min(${width}, calc(100vw - 32px))`. ⏱ ~3 min ROOT FIX.

### P0.F — DESIGN INFRA (pre-condition all UI fixes)
19. **A.5** — **Inter font jamais chargé** (referenced dans tokens.ts + CSS mais pas de `next/font` import). User voit SF Pro/Segoe/fallback. Ajouter `import { Inter } from 'next/font/google'` dans `app/layout.tsx`. ⏱ ~5 min.
20. **A.5** — Pill `.gc-pill` utilisé 3 rôles différents (data badge, primary CTA, reset button). Séparer en `.gc-badge`, `.gc-button`, `.gc-pill-reset`. ⏱ ~1h refactor.
21. **A.5** — 339 occurrences `style={{}}` inline override CSS. Top offender: `audits/[c]/[a]/page.tsx:50` (H1 contient styled `<span>` subtitle). Audit + migrer vers utility classes. ⏱ Wave-C-long.

### P0.G — TESTS (validation Wave D)
22. **A.4** — Run `webapp/tests/e2e/wave-a-2026-05-14.spec.ts` en local + prod. Setup storage state auth. ⏱ ~20 min.

**Total P0 unique = 22 items**. Est. effort cumulé Wave C P0 : ~6-8h (dont 4-5h sur A.10 re-migration script + validation).

## 3. P1 priorités (post-P0)

Voir détails individuels dans chaque `AUDIT_*_2026-05-14.md`. Patterns récurrents :

- **A.1 + A.7** — `force-dynamic` sur chaque Server Component (defeats ISR + cost $)
- **A.1 + A.7** — Optimistic UI sans rollback
- **A.5 + A.7** — 15+ inline `style={{}}` avec hardcoded hex bypass tokens CSS
- **A.7** — 12+ `<a href>` internes au lieu de `next/link` (defeat prefetching)
- **A.7** — `audit.scores_json as Record<string, unknown>` casts (missing upstream type)
- **A.8** — Middleware runs on `/api/screenshots/*` (1s perte sur audit detail)
- **A.8** — No `next/image` for Supabase screenshots (80-300KB vs 15KB)
- **A.8** — Home `loadOverview()` 3 sequential awaits → `Promise.allSettled`
- **A.11** — `runs` table RLS allows `org_id IS NULL` rows (backdoor)
- **A.11** — RLS write policies use `is_org_member` not `is_org_admin` (viewer can bypass)
- **A.11** — No global CSP/X-Frame-Options/nosniff headers
- **A.12** — No explicit `<meta viewport>` ni Next.js `viewport` export

## 4. Cross-validation (convergences entre audits)

| Finding | Audits qui l'ont flag | Confiance |
|---|---|---|
| `/api/learning/proposals/review` sans auth | A.1 + A.11 | 🔴 P0 confirmé |
| Inline `style={{}}` sprawl | A.5 (339 occ) + A.7 (15+) | 🔴 P0 design infra |
| Auth role silent fail | A.1 + A.7 | 🔴 P0 UX |
| Modal width hardcoded breaks 360px | A.6 (a11y modal) + A.12 (mobile) | 🔴 P0 mobile-a11y |
| Migration source mismatch | A.10 (root) + A.7 (`scores_json` cast) | 🔴 ROOT CAUSE |
| Service_role JWT in history | A.11 + W0.1 PRD | 🔴 Mathis urgent |

## 5. Bonnes nouvelles (foundation solide)

- **Architecture RSC-first propre** (A.8) — 55 `"use client"` files only, heavy charts pure server-side SVG, 3 third-party libs (clsx + 2 Supabase), pas de lodash/moment/date-fns/chart libs
- **Largest JS chunk 180KB unminified** (A.8)
- **Security gates correctement appliqués** SP-7 sur recos/audits/clients (A.1, A.11)
- **captures-fs path-traversal defense thorough** (A.1)
- **A11y foundation présent** : skip link, `:focus-visible` global ring, `prefers-reduced-motion`, form labels via `FormRow`, modals `role="dialog"` + `aria-modal` + ESC + scroll lock, breadcrumb `<nav>/<ol>` + `aria-current`, NavItem `aria-current`, native `<button type="button">` mostly (A.6)
- **Doctrine-aligned `"use client"` thin-island triggers** (A.7)
- **Defensive parsers** (`parseCapturedFunnel`, `parseJudgesPayload`, `extractRichReco`) returning null on bad shape (A.7)
- **Reusable error.tsx + loading.tsx + ErrorFallback + PageSkeleton pattern** (A.7)
- **V26 foundation CSS** ships solid media queries `@media (max-width: 1180/980/720/640/480px)` — mais bypassed par inline overrides (A.12)

## 6. Wave B/C/D/E plan (next sessions)

### Wave B — SYNTHESIS (~30 min next session) — déjà fait ici partiellement
- ✅ Aggregate findings (ce fichier)
- ⏳ Master bug list canonical (= section 2 ci-dessus, à éventuellement raffiner)
- ⏳ Impact × effort prioritization formelle si Mathis veut autre ordre

### Wave C — EXECUTION FIXES (sequencing recommandé)

**Sprint C.0 — Pre-Wave C blockers (Mathis side, ~10 min)**
- W0.1 : rotater service_role JWT
- W0.4 : enable Vercel Agent
- Débloquer GStack install
- Optionnel : rotater Anthropic key si confirmée historiquement leaked

**Sprint C.1 — Data fidelity (~4-5h, P0.A)**
- Sub-PRD `fix-data-fidelity-migration` :
  - Code `scripts/migrate_disk_to_supabase.py` mono-concern, ≤800 LOC
  - Walks `data/captures/<c>/<p>/` → `recos_enriched.json` + scores
  - Tables étendues : ajout migrations `supabase/migrations/2026-05-14_*_*.sql`
  - Re-run migration → validate sample audit detail page
  - Archive `scripts/migrate_v27_to_supabase.py` + `growth_audit_data.js`

**Sprint C.2 — Security patches (~30 min, P0.B)**
- Open redirect fix (5 min)
- requireAdmin sur learning endpoint (10 min)
- Anthropic key audit + rotation if needed (5 min)
- Confirm RLS hardening pour `runs` table (10 min)

**Sprint C.3 — A11y + mobile P0s (~2h, P0.C + P0.E + P0.F design infra)**
- Bump `--gc-muted` à shade lighter (1 ligne CSS)
- Modal width clamp fix (3 min code, root fix for mobile + a11y)
- Modal focus trap + restore (~30 LOC helper)
- `<a aria-disabled>` → `<button disabled>` ou tabindex pattern
- Inline grid overrides → responsive grid
- Inter font `next/font/google` import (5 min)

**Sprint C.4 — React polish (~2h, P0.D)**
- Index-as-key fixes
- router.refresh after mutations
- Surface silent auth failures
- 12+ `<a>` → `<Link>` (prefetch)
- Shared TRACK_TONE/DECISION_TONE module

**Sprint C.5 — Perf wins (~1h, A.8 P1)**
- Middleware matcher exclude `/api/screenshots/*`
- Migrate AuditScreenshotsPanel to `next/image`
- `Promise.allSettled` on home `loadOverview()`

**Sprint C.6 — Wave A delta audits (~1h)**
- A.2 Vercel Agent : trigger PR + capture findings
- A.3 vercel:verification : run 3 routes with dev server
- A.9 GStack : run 3 personas

### Wave D — VALIDATION (~2h)
- Run `wave-a-2026-05-14.spec.ts` desktop + mobile
- Re-run Wave A audits sur fixed code (regression check)
- Mathis manual validation 10 routes principales
- Lighthouse en réel sur 5 main routes (target ≥90)

### Wave E — CLOSE (~1h)
- BLUEPRINT v1.3 update (skills new)
- MANIFEST §12 changelog 2026-05-14
- CONTINUATION_PLAN_2026-05-15.md

## 7. Mathis-side actions (recap, blocking Wave C)

| # | Action | Effort | Urgency | Doc |
|---|---|---|---|---|
| 1 | 🔴 Rotater service_role JWT Supabase | 5 min | URGENT | [WAVE_0_STATUS](WAVE_0_STATUS_2026-05-14.md) §Action 1 |
| 2 | 🟡 Enable Vercel Agent (Dashboard) | 5 min | P0 Wave A.2 | [AUDIT_VERCEL_AGENT](AUDIT_VERCEL_AGENT_2026-05-14.md) |
| 3 | 🟢 Débloquer GStack install (permission rule ou manuel) | 2 min | P1 Wave A.9 | [AUDIT_GSTACK](AUDIT_GSTACK_2026-05-14.md) |
| 4 | 🟡 Confirmer Anthropic key rotation historique | 5 min | P0 Wave C.2 | [AUDIT_SECURITY](AUDIT_SECURITY_2026-05-14.md) P0.2 |
| 5 | 🟢 Validation manuelle 10 routes post-Wave C | 1-2h | P0 Wave D | (à venir) |

## 8. Next session trigger phrase

```
Reprise Wave A → B → C.
Lis CLAUDE.md init steps + .claude/docs/state/AUDIT_SUMMARY_2026-05-14.md (source canonique).
Confirme Mathis actions §7 (JWT + Vercel Agent + GStack).
Lance Wave C.1 : sub-PRD fix-data-fidelity-migration via /ccpm. Superpowers TDD enforcement.
```

## 9. Doctrine respected (anti-velocity gates)

- ✅ Audit-first méthodo (12 dimensions cross-validated)
- ✅ Cross-validation : 6 convergences entre audits indépendants
- ✅ Findings écrits dans fichiers .md (pas dans le chat — Wave B/C reading material)
- ✅ Mathis-side blockers documentés sans push
- ✅ Pas de fix shipped Wave A — pure diagnostic
- ⏳ Test visuel Playwright reporté Wave D (spec écrite Wave A)
- ⏳ Mathis-in-loop validation Wave D

## 10. Cross-references

- Master PRD : [`webapp-data-fidelity-and-skills-stratosphere-2026-05`](../../prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md)
- Continuation plan : [`CONTINUATION_PLAN_2026-05-14`](CONTINUATION_PLAN_2026-05-14.md)
- Wave 0 status : [`WAVE_0_STATUS_2026-05-14`](WAVE_0_STATUS_2026-05-14.md)
- Skills research : [`SKILLS_DEEP_RESEARCH_2026-05-13`](SKILLS_DEEP_RESEARCH_2026-05-13.md)
- 12 audit reports : `AUDIT_*_2026-05-14.md` ce dossier

---

**État final Wave A** : 9 audits exécutés + 3 plans activables Mathis-side. 160 findings catalogués, **root cause confirmé empiriquement**, plan Wave C ordonné. **AU CARRÉ.**
