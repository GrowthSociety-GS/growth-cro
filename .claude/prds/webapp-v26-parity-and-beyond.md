---
name: webapp-v26-parity-and-beyond
description: Méga-programme pour amener la webapp V28 Next.js à la parité du V26 HTML reference + ajouter interactivité réelle (CRUD) + features beyond V26. 10 sub-PRDs organisés en 3 Waves. Réponse au feedback critique Mathis 2026-05-13 "webapp Vercel ne ressemble pas au html V26".
status: active
created: 2026-05-13T11:11:07Z
parent_prd: post-stratosphere-roadmap
wave: parity-v26
---

# PRD: webapp-v26-parity-and-beyond

> **Méga-programme multi-Wave (P0/P1/P2)** pour amener la webapp V28 Next.js (https://growth-cro.vercel.app) à la **parité du V26 HTML reference** (`deliverables/GrowthCRO-V26-WebApp.html`, 216 KB / 3666 lignes) + **interactivité réelle** (CRUD via Supabase) + **features beyond V26**.
>
> Réponse directe au feedback Mathis 2026-05-13 : *"webapp Vercel ne ressemble pas au html V26, c'est presque comme si on était revenu à zéro"*.
>
> Décliné en **10 sub-PRDs** parallélisables, exécutables en ~8-12 jours wall-clock avec agents background + skills frontend-design.

## Executive Summary

Le programme webapp-full-buildout (Phase 1 + Phase 2 + rich-ux pivot, shipped 2026-05-13) a livré une **fondation architecturale propre** : shell consolidé, auth Supabase, 4 features wired scaffold, migration data 56 clients. Mais le user a signalé que le résultat est **inférieur en UX/features/design** au V26 HTML qui existait avant (généré statiquement par les pipelines Python).

Ce master PRD encadre le **chemin de remontée** : 10 sub-PRDs ordonnés en 3 Waves (Parité V26 P0 → Interactivité P1 → Polish + Beyond P2). Chaque sub-PRD est self-contained, file-disjoint quand possible, et exploite les skills frontend-design + design-system pour atteindre un niveau **studio de design** (cf doctrine Mathis *"perfection dès le départ"* + *"avant-garde, pas best CRO B2B 2024"*).

**Effort total** : ~8-12 jours wall-clock avec 3-4 agents parallèles + skills externes.
**Coût API** : ~$15-30.
**Critical path** : Wave Parité V26 (P0) bloque user satisfaction → Wave Interactivité (P1) + Beyond (P2) en parallèle après.

## Problem Statement

### Pourquoi maintenant

1. **Feedback user critique 2026-05-13** : *"RIEN A VOIR avec le html V26 interactif, avec les screens les infos, l'ux/Ui travaillée"*. Le user demande **minimum parité V26**.
2. **Foundation existe** : shell Next.js + auth Supabase + data layer + 20 routes scaffold + rich UX recos shipped. Le terrain est prêt pour l'upgrade UX.
3. **Skills frontend-design disponibles** : `anthropic-skills:frontend-design`, `design:design-system`, `design:design-critique`, `design:design-handoff` permettent un niveau studio sans repartir de zéro.
4. **Data réelle migrée** : 56 clients × 185 audits × 3045 recos en Supabase prod, donc les vues riches AURONT du contenu réel à render.
5. **CRUD impossible aujourd'hui** : la webapp V28 est read-only. Pas d'edit reco, pas de create audit, pas de save brief GSG. Le user veut **interactivité**.

### Ce que ce master PRD apporte

- **Parité V26 HTML** atteinte (UX/DA/features) en P0
- **Interactivité réelle** ajoutée (CRUD Supabase) en P1
- **Features beyond V26** (multi-judge UI, learning lab, funnel viz) en P2
- **Roadmap claire** : 10 sub-PRDs ordonnés par Wave + dépendances explicites
- **Réutilisation** des skills frontend-design + design-system pour qualité studio

## User Stories

### US-1 — Mathis (founder, position "perfection dès le départ")
*Comme founder qui a investi sur le V26 HTML, je veux que la webapp V28 sur Vercel soit AU MINIMUM aussi belle et fonctionnelle que le V26 HTML, pour ne pas avoir l'impression d'avoir régressé.*

**AC** :
- Visuel parité : grain texture, panel shadows, pills colorées, score bars colorées, reco cards left-border priority
- Features parité : Brand DNA viewer, Doctrine blocs, Funnel viz, Modals system, Tabs page-types, GSG 5 modes
- Navigation parité : sidebar 4-5 vues + URL state + breadcrumbs

### US-2 — Consultant Growth Society (cible business)
*Comme consultant qui présente un audit à un client, je veux pouvoir EDITER une reco (ajuster reco_text, changer priority, ajouter des notes), SAUVEGARDER, et CRÉER de nouveaux audits depuis la webapp, pour avoir un outil de travail réel et pas juste un viewer statique.*

**AC** :
- Modal "Edit reco" avec form-row pour tous les fields
- Modal "Create audit" avec form-row + page_type select
- Save persiste via Supabase REST + service_role (RLS enforced)
- Optimistic UI updates + rollback on error
- Audit log "qui a modifié quoi quand" (V2, scaffold V1)

### US-3 — Consultant (drill-down audit)
*Comme consultant qui audite 1 client avec 4 pages (home, pdp, collection, checkout), je veux pouvoir tabber entre les page-types et voir les 6 piliers V3.2.1 + recos prioritaires per page-type, pour comprendre où sont les problèmes.*

**AC** :
- Tabs page-types (home/pdp/collection/checkout/...) avec converged notice si nécessaire
- 6 piliers progress bars per page (hero/persuasion/ux/coherence/psycho/tech)
- Score total per page + score moyen client
- Drill-down "Voir toutes les recos" → filtered list

### US-4 — Mathis (GSG handoff workflow)
*Comme founder qui prépare un brief GSG pour le pipeline Python, je veux pouvoir choisir un mode (Complete/Replace/Extend/Elevate/Genesis), voir le brief JSON deterministic généré, prévisualiser le rendu attendu, copier le brief en clipboard, pour pouvoir le passer au pipeline `moteur_gsg`.*

**AC** :
- Sidebar GSG modes (5 buttons avec descriptions)
- Brief JSON viewer avec syntax highlighting (mono font, max-height + scroll)
- Controlled Preview iframe rendering placeholder LP
- Copy brief button → clipboard + toast feedback
- (V2) Bouton "Trigger run" → POST FastAPI backend (deferred)

### US-5 — Consultant Growth Society (Brand DNA discovery)
*Comme consultant qui découvre un nouveau client, je veux voir son Brand DNA (palette colors, typography, voice, persona) en 1 vue visuelle, pour me caler immédiatement sur sa direction artistique.*

**AC** :
- `/clients/[slug]/dna` ou tab `Brand DNA` dans `/clients/[slug]`
- Render `client.brand_dna_json` (V29 schema) en visuel :
  - Palette colors swatches (hex + name)
  - Typography preview (font name + sample text)
  - Voice description (tone, vocabulary, examples)
  - Persona narrative (Schwartz awareness level)
- Fallback gracieux si brand_dna_json null (3 clients seed n'en ont pas)

## Functional Requirements

Le programme est décomposé en **10 sub-PRDs** organisés en 3 Waves :

### 🔴 Wave Parité V26 (P0 — bloque user satisfaction)

#### SP-1 — `webapp-visual-design-system-v26`
- **Effort** : M, 1-2j
- **Cible** : Match exact CSS tokens + components du V26 HTML
- **Files** : `webapp/apps/shell/app/globals.css`, `webapp/packages/ui/src/components/*.tsx`
- **Acceptance** :
  - CSS variables `--bg`, `--panel`, `--gold`, `--cyan`, `--green`, `--red`, `--amber`, `--blue`, `--shadow` identiques V26
  - Grain texture background (CSS pattern OR SVG noise)
  - Panel shadow (`0 18px 54px rgba(0,0,0,.28)`)
  - 5 variants Pill (red/amber/green/gold/cyan)
  - Score bars composant (`.bar-track` + `.bar-fill` colored)
  - Reco card avec `left-border` colorée par priority
  - KpiCard 5-col grid responsive

#### SP-2 — `webapp-command-center-view`
- **Effort** : M, 1-2j
- **Cible** : Refactor `/` dashboard pour matcher V26 Command Center
- **Files** : `webapp/apps/shell/app/page.tsx`, NEW `components/command-center/*`
- **Acceptance** :
  - Topbar : titre + subtitle + 2 boutons (Open V26 archive + Copy GSG brief)
  - Grid KPI 5-col (Fleet count, P0 recos, Avg score, Recent runs, Active audits)
  - Layout 2-col : Fleet sidebar (clients list scrollable) + Client hero detail
  - Filtres globaux : roleFilter + search + sort
  - Client-row : name + score + role pill (`business_client`, `golden_reference`, `mathis_pick`, etc.)

#### SP-3 — `webapp-brand-dna-viewer`
- **Effort** : S-M, 1j
- **Cible** : `client.brand_dna_json` (V29 schema) rendered as visual page
- **Files** : NEW `webapp/apps/shell/app/clients/[slug]/dna/page.tsx` + components
- **Acceptance** :
  - Palette colors swatches grid + hex codes
  - Typography preview (font face load + sample H1/H2/p)
  - Voice description + Schwartz awareness pill
  - Persona narrative + sample copy snippets
  - Fallback "Pending Brand DNA" si null

#### SP-4 — `webapp-audit-pillars-rich-view`
- **Effort** : M, 1-2j
- **Cible** : 6 piliers V3.2.1 avec drill-down per page-type + tabs
- **Files** : Refactor `webapp/apps/shell/app/audits/[clientSlug]/page.tsx` + `[auditId]/page.tsx`
- **Acceptance** :
  - Tabs page-types (home/pdp/collection/checkout/article/quiz/lp_*) avec auto-discover des audits du client
  - "Converged notice" si plusieurs audits convergent sur même page_type
  - 6 piliers progress bars per page (hero/persuasion/ux/coherence/psycho/tech)
  - Score total per page + score moyen client visible
  - Audit quality indicator (full vs partial)

#### SP-5 — `webapp-gsg-handoff-view`
- **Effort** : M, 1-2j
- **Cible** : `/gsg` étendu avec 5 modes selector + brief JSON viewer + Controlled Preview iframe
- **Files** : Refactor `webapp/apps/shell/app/gsg/page.tsx` + new components
- **Acceptance** :
  - Sidebar GSG modes (Complete/Replace/Extend/Elevate/Genesis) avec descriptions
  - Brief JSON viewer mono font, syntax highlighting (Prism.js OR home-made)
  - Controlled Preview iframe rendering current LP du mode sélectionné
  - "Copy GSG brief" button → clipboard JSON + toast feedback
  - "Open in new tab" pour preview full
  - End-to-end Demo flow : Audit → Reco → Brief → Preview chain visualization

#### SP-6 — `webapp-navigation-multi-view`
- **Effort** : S-M, 1j
- **Cible** : Sidebar nav 4-5 vues principales + URL state + breadcrumbs
- **Files** : Refactor `webapp/apps/shell/components/Sidebar.tsx` + layout
- **Acceptance** :
  - Sidebar : Command Center, Audit & Recos, GSG Handoff, Brand DNA, Doctrine
  - URL state : `?view=audit&client=weglot&page=home` (shareable links)
  - Breadcrumbs : Home > Client > Audit > Page-type
  - Active state visual sur nav button
  - Mobile collapse + drawer

### 🟡 Wave Interactivité (P1 — adds real value vs V26)

#### SP-7 — `webapp-modals-and-crud`
- **Effort** : L, 2-3j
- **Cible** : Modal pattern + CRUD via Supabase RLS pour recos/audits/clients
- **Files** : NEW `webapp/packages/ui/src/components/Modal.tsx`, NEW `app/api/recos/[id]/route.ts`, NEW `app/api/audits/route.ts`, etc.
- **Acceptance** :
  - Modal component réutilisable (backdrop + ESC close + click-outside close + focus trap)
  - Edit reco modal : form fields (reco_text, priority, severity, effort, lift) + Save → Supabase UPDATE
  - Create audit modal : page_type select + page_url input + auto-generate audit_id + Save
  - Delete confirmation modal pour clients/audits/recos
  - Optimistic UI updates + rollback on error
  - RLS enforced : seul org owner peut edit/delete

#### SP-8 — `webapp-search-filter-sort-patterns`
- **Effort** : M, 1j
- **Cible** : Reusable hooks + URL state + scalable to 100+ clients
- **Files** : NEW `webapp/apps/shell/lib/use-url-state.ts`, refactor existing pages
- **Acceptance** :
  - `useUrlState()` hook : sync state ↔ URL searchParams (debounced 300ms for input)
  - Filters reusable : priority, effort, lift, criterion_id, business_category, role
  - Server-side filtering pour scale 100+ clients (utilise Supabase `.eq()` `.gte()`)
  - URL state persistent post-refresh + shareable
  - Reset all filters button

### 🟢 Wave Polish + Beyond V26 (P2 — quality + nice-to-have)

#### SP-9 — `webapp-polish-perf-a11y`
- **Effort** : M, 1-2j
- **Cible** : Loading states + error boundaries + mobile + Lighthouse > 90 + WCAG AA
- **Files** : Various components + add `loading.tsx` + `error.tsx` per route
- **Acceptance** :
  - Loading skeletons sur toutes les pages (sub-200ms perception)
  - Error boundaries Next.js 14 `error.tsx` per route
  - Empty states gracieux (no clients, no audits, no recos)
  - Mobile-first responsive (test breakpoints 360px, 768px, 1024px, 1440px)
  - Lighthouse score > 90 (Performance + Accessibility + Best Practices)
  - WCAG AA : color contrast, keyboard nav, screen reader (NVDA + VoiceOver)
  - axe-core 0 violations sur audit pages principales

#### SP-10 — `webapp-funnel-multi-judge-learning`
- **Effort** : L, 2-3j (conditional, étalable)
- **Cible** : Funnel viz + Multi-judge UI + Learning lab proposals (Wave C originelle)
- **Files** : NEW routes + components
- **Acceptance** :
  - **Funnel viz** : `/funnel/[clientSlug]` rendering funnel-steps (visitors → click → engaged → CTA → conversion). Source : `client.funnel_json` (V2 schema) OR derived from audit data.
  - **Multi-judge UI** : `/audits/[clientSlug]/[auditId]/judges` rendering 4 juges (Sonnet/Haiku/Opus/Doctrine) consensus + per-judge scores. Source : `audits.judges_json` (V26.D schema).
  - **Learning lab** : `/learning` rendering doctrine_proposals avec vote 4 buttons (accept/reject/refine/defer). Persistance via service_role REST (deferred FR-4 si Mathis review faite).

## Non-Functional Requirements

### Doctrine immuables
- V26.AF immutable (vacuous, persona_narrator gone)
- V3.2.1 + V3.3 piliers respectés (radial chart affiche les 6 piliers)
- Code doctrine : ≤ 800 LOC, mono-concern, 8 axes
- Pas de `process.env[key]` dynamic
- Anti-pattern #10 : archive sous `_archive/` racine
- Anti-pattern #11 : pas de basename duplication non-canonique

### Performance
- Page load < 2s sur 4G (Vercel CDN + RSC streaming)
- Supabase queries < 200ms (EU region, RLS enforced)
- Bundle size shell : ne doit pas augmenter > 50% vs baseline 87.3 KB (cible < 130 KB)
- Mobile FCP < 1.5s, LCP < 2.5s, CLS < 0.1

### Sécurité
- Service_role JWT server-only (jamais client-side)
- RLS Supabase enforced sur toutes les mutations
- CSRF protection (Next.js default same-origin)
- Modal forms validate côté server avant insert/update
- Path traversal blocked sur API routes (whitelist pattern)

### Documentation
- MANIFEST §12 changelog par sub-PRD merge
- Architecture map regen post-merge
- Capabilities-keeper invocation pre-each sub-PRD
- Sub-PRD spec dans `.claude/prds/` avant exécution agent
- Progress.md updates dans `.claude/epics/<name>/updates/<task>/`

### Design system
- CSS tokens centralisés (`--bg`, `--panel`, etc.) dans `webapp/apps/shell/app/globals.css`
- Components dans `webapp/packages/ui/src/` (Card, Pill, KpiCard, ScoreBar, Modal, Tabs, NavItem)
- Pas de Tailwind utility-soup dans les pages (préférer classes sémantiques via globals.css)
- Inter font (system stack fallback)

## Success Criteria

### Globaux V1 (parité V26 atteinte)
- [ ] SP-1 done : tokens + components V26 match
- [ ] SP-2 done : Command Center view = V26 layout
- [ ] SP-3 done : Brand DNA viewer fonctionnel
- [ ] SP-4 done : 6 piliers V3.2.1 + tabs page-types
- [ ] SP-5 done : GSG 5 modes + brief JSON + preview
- [ ] SP-6 done : Sidebar 5 vues + URL state + breadcrumbs

### Globaux V2 (interactivité ajoutée)
- [ ] SP-7 done : Modals + CRUD recos/audits/clients
- [ ] SP-8 done : Search/Filter/Sort reusable patterns

### Globaux V3 (polish + beyond)
- [ ] SP-9 done : Lighthouse > 90, WCAG AA, mobile responsive
- [ ] SP-10 done (optionnel) : Funnel + Multi-judge + Learning lab

### Mathis validation
- [ ] Mathis confirme "**parité V26 atteinte**" via review visuelle directe
- [ ] Mathis confirme "**interactivité utile**" via test CRUD réel
- [ ] 0 régression V26.AF / V3.2.1 / V3.3

### Métriques techniques
- [ ] 0 fichier > 800 LOC introduit
- [ ] 0 new dep lourde (Material-UI, Mantine, recharts, etc.)
- [ ] Bundle First Load shared < 130 KB
- [ ] Lighthouse Performance > 90 sur `/`, `/clients`, `/audits/[c]/[a]`
- [ ] axe-core 0 violations sur 5 pages principales
- [ ] Mobile responsive : tests passing à 360px, 768px, 1024px, 1440px

## Constraints & Assumptions

### Constraints
- **Pas de nouvelle dep UI lourde** : pas de Material-UI, Mantine, Chakra, recharts, victory. Réutiliser `@growthcro/ui` custom + SVG/CSS plain.
- **Pas de refactor doctrine** V3.2.1/V3.3/V26.AF
- **Pas de modif Supabase schema** sans migration explicite documentée
- **Pas de FastAPI deploy** (deferred V2)
- **Pas de Reality monitor live** (deferred V2, credentials pending)
- **Skill cap** : ≤ 8 skills simultanés/session (cf CLAUDE.md anti-pattern #12)
- **Combo packs respectés** : Webapp Next.js dev (≤ 5 skills) — frontend-design + nextjs + design-system + react-best-practices + (vercel-cli OR shadcn OR ux-copy)

### Assumptions
- Migration data V27→Supabase déjà effectuée (56 clients en prod, cf 2026-05-13)
- Rich UX recos shipped (RichRecoCard + AuditScreenshotsPanel, cf 2026-05-13)
- Mathis disponible ~2-4h validation finale post-Wave Parité V26
- Skills frontend-design + design-system maintenus 2026
- Vercel free tier suffisant (mesure post-SP-9 polish)
- Service_role JWT rotaté (cf rotation urgente post-session 2026-05-13)

## Out of Scope

### V1 (explicitement)
- **FastAPI backend deploy** (Fly.io/Railway) → decision gate distinct
- **Trigger audit/GSG depuis UI** (button "Generate new LP") → besoin FastAPI
- **Reality monitor live connectors** (GA4 + Meta + Google + Shopify + Clarity) → V2
- **GEO Monitor multi-engine** (ChatGPT/Perplexity/Claude) → V3
- **Multi-tenant org switching** → V2 (1 user = 1 org pour V1)
- **Notion auto-sync** → V2
- **Slack/Email notifications** → V2

### V2+ (post-parité V26)
- FastAPI deploy + trigger UI
- Reality monitor live
- GEO Monitor
- Multi-tenant
- Notion sync
- Notifications

## Dependencies

### Externes (humaines)
- Mathis ~2-4h validation post-Wave Parité V26 (review visuelle directe + test CRUD)
- Mathis ~30min validation par sub-PRD (5 sub-PRDs Wave P0)
- Consultant Growth Society 30min feedback session (post SP-7 CRUD)

### Externes (techniques)
- Vercel auto-deploy GitHub (active)
- Supabase EU + RLS (active, 56 clients × 185 audits × 3045 recos)
- Skills frontend-design + design-system (maintained 2026)
- Skill cap 8/session respecté

### Internes (code/data)
- main HEAD `0dbac2d` (rich-ux merged)
- `webapp/packages/{config,data,ui}` stables
- `data/captures/<client>/<page>/screenshots/` 4831 PNG (servi via `/api/screenshots`)
- `data/_aura_<client>.json` brand DNA computed (à exploiter SP-3)
- Doctrine V3.2.1 + V3.3 schemas

### Sequencing
- **SP-1** foundation : blocking pour SP-2/3/4/5/6 (tokens + components réutilisés partout)
- **SP-2/3/4/5/6** : parallèles après SP-1 (Wave Parité V26)
- **SP-7/8** : parallèles après Wave Parité (touchent les pages déjà refactorisées)
- **SP-9/10** : post Wave Interactivité (polish + extensions)

```
Wave Parité V26 (P0, ~4-6 jours wall-clock)
  SP-1 design-system-v26 (M, 1-2j) ← blocking
       │
       ├─ SP-2 command-center (M, 1-2j)    ┐
       ├─ SP-3 brand-dna (S-M, 1j)         │  parallèles 3-4 agents
       ├─ SP-4 audit-pillars (M, 1-2j)     │  ~2-3j max wall-clock
       ├─ SP-5 gsg-handoff (M, 1-2j)       │
       └─ SP-6 navigation (S-M, 1j)        ┘

Wave Interactivité (P1, ~2-3 jours wall-clock, post Wave P0)
  ├─ SP-7 modals-crud (L, 2-3j)    ┐
  └─ SP-8 search-filter (M, 1j)    ┘ parallèles 2 agents

Wave Polish + Beyond (P2, ~2-3 jours)
  ├─ SP-9 polish-perf-a11y (M, 1-2j)
  └─ SP-10 funnel-multi-judge-learning (L, 2-3j, conditional)
```

**Critical path** : SP-1 (1-2j) → max(SP-2..SP-6) (2-3j) → max(SP-7, SP-8) (2-3j) → max(SP-9, SP-10) (2-3j) = **~8-12 jours wall-clock** avec parallélisation max.

---

## Programme — Plan d'exécution session-par-session

### Session 1 — Foundation (SP-1)
- Setup design-system + tokens V26 + base components (Pill, ScoreBar, KpiCard variants, Modal stub)
- Pattern doctrine fix : tous les classes V26 mappées en composants `@growthcro/ui`
- 1 commit isolé `feat(ui): visual design system v26-parity foundation`
- Skills : `frontend-design` + `design-system` + `react-best-practices`

### Session 2 — Vue parité (SP-2 + SP-3 + SP-4 parallèles)
- 3 agents background sur 3 worktrees disjoints
- SP-2 = `/` Command Center refactor
- SP-3 = `/clients/[slug]/dna` Brand DNA viewer
- SP-4 = `/audits/[c]/[a]` 6 piliers + tabs page-types
- Skills par agent : `frontend-design` + `nextjs` + `design-handoff`
- 3 commits isolés + 3 merges

### Session 3 — GSG + Nav (SP-5 + SP-6 parallèles)
- 2 agents background
- SP-5 = `/gsg` 5 modes + brief + preview
- SP-6 = Sidebar 5 vues + URL state + breadcrumbs
- Skills : `frontend-design` + `nextjs` + `ux-copy`
- 2 commits isolés + 2 merges

### **GATE A — Mathis validation Wave Parité V26**
- Visual review parité V26 → ✅ ship Wave Interactivité OR 🔁 fix gaps

### Session 4 — Interactivité (SP-7 + SP-8 parallèles)
- 2 agents background
- SP-7 = Modals + CRUD recos/audits/clients
- SP-8 = Search/Filter/Sort reusable hooks
- Skills : `nextjs` + `react-best-practices` + `vercel-functions`
- 2 commits isolés + 2 merges

### **GATE B — Mathis validation interactivité**
- Test CRUD réel (edit reco, create audit) → ✅ ship Polish OR 🔁 fix gaps

### Session 5 — Polish (SP-9)
- 1 agent background
- Loading states + error boundaries + mobile responsive + Lighthouse > 90 + WCAG AA
- Skills : `performance-optimizer` + `accessibility-review` + `ux-copy`
- 1 commit isolé + merge

### Session 6 — Beyond V26 (SP-10, optionnel)
- 1 agent background si Mathis valide la priorité
- Funnel viz + Multi-judge UI + Learning lab
- Skills : `frontend-design` + `data:data-visualization`
- 1 commit isolé + merge

---

## Notes finales

Ce master PRD est intentionnellement **scope-ambitieux** parce que Mathis attend un niveau studio. La parité V26 (P0) est non-négociable. L'interactivité (P1) ajoute la vraie valeur business vs V26 static. Le polish (P2) finalise. Beyond V26 (SP-10) est conditional.

**Première action** : créer SP-1 sub-PRD `webapp-visual-design-system-v26.md` via /ccpm prd-new, decompose en 4-5 tasks, lance agent foreground (foundation critique pour le reste).

**Position Mathis rappel** : *"perfection dès le départ"* · *"concision > exhaustivité"* · *"avant-garde, pas best CRO B2B 2024"* · *"moat dans les data accumulées"*.

Ce master PRD est notre roadmap pour les ~2 prochaines semaines de webapp work.
