---
name: webapp-gsg-studio
description: Wire la route /gsg pour lister les LPs GSG livrées (deliverables/gsg_demo/*.html) avec iframe preview + métadonnées (page_type, doctrine_version, multi-judge score).
status: active
created: 2026-05-13T09:36:29Z
parent_prd: webapp-full-buildout
wave: B-extended
fr_index: FR-3
---

# PRD: webapp-gsg-studio

> Sub-PRD du master [`webapp-full-buildout`](webapp-full-buildout.md) — FR-3 (post-FR-1, S-M effort).
>
> Wirer `/gsg` aux fichiers HTML GSG livrés sur disque (`deliverables/gsg_demo/*.html`). Aucune génération nouvelle, aucune wiring Supabase — c'est un viewer iframe + métadonnées.

## Executive Summary

Mathis a livré 3 LPs GSG scaffold (Weglot listicle, Weglot advertorial, Japhy PDP) dans `deliverables/gsg_demo/`. Sans UI, c'est juste des fichiers HTML inaccessibles depuis la webapp.

FR-3 wire `/gsg` :
- Liste 1 card par LP livrée (auto-discover du dossier `deliverables/gsg_demo/`)
- Each card : iframe preview embedded + métadonnées (page_type, doctrine_version, multi-judge score si JSON dispo)
- CTA "Open in new tab" pour viewer full-screen
- API route Next.js `/api/gsg/[slug]/html` qui sert le HTML (security headers)

**Effort** : S-M, 0.5-1j wall-clock · ~2-3h agent background.
**Coût API** : $0 (file system reads).
**Bloque** : aucun (parallel-safe avec FR-2 + FR-5).

## Problem Statement

### Pourquoi maintenant

1. **3 LPs livrées invisibles** : Mathis a investi ~40h sur les 3 LPs GSG. Sans `/gsg`, aucun consultant Growth Society ne peut les voir/évaluer.
2. **Demo readiness** : preview iframe = element clé pour la demo aux consultants. Sans, FR-6 validation incomplète.
3. **Foundation Live GSG** : quand FastAPI sera deployé V2, le `/gsg` aura un bouton "Generate new LP". Wire le viewer maintenant = foundation pour V2.
4. **GSG metadata évolutive** : doctrine_version (V27.2-G), multi-judge score (70.9% Weglot listicle baseline). Affichage visuel facilite l'itération.

### Ce que FR-3 apporte

- 1 route `/gsg` qui auto-discovers les LPs livrées
- Iframe preview embeddé responsive
- Métadonnées affichées (page_type, multi-judge score si JSON dispo)
- API route sécurisée pour servir le HTML statique
- CTA "Open in new tab" + "Copy URL"

## User Stories

### US-1 — Mathis (preview LPs)
*Comme founder qui itère sur les LPs GSG, je veux `/gsg` qui liste les LPs livrées avec iframe preview, pour voir le rendu visuel sans naviguer le file system.*

**Acceptance Criteria** :
- ✓ `/gsg` HTTP 200, auto-discover `deliverables/gsg_demo/*.html`
- ✓ Each LP card : iframe preview (height: 600px, responsive)
- ✓ Iframe loaded depuis `/api/gsg/[slug]/html` (sécurisé)
- ✓ Métadonnées : filename, page_type (parsed from filename ou metadata.json sidecar), file size, last modified date
- ✓ Multi-judge score affiché si `deliverables/gsg_demo/[slug].multi_judge.json` existe (e.g., "70.9% Bon")
- ✓ CTA "Open full" → new tab vers `/api/gsg/[slug]/html`

### US-2 — Consultant (review LPs)
*Comme consultant Growth Society qui évalue la qualité GSG, je veux pouvoir scroller chaque preview iframe + voir les métadonnées techniques (doctrine_version, page_type) côte-à-côte.*

**Acceptance Criteria** :
- ✓ Grid layout : 2 cards par row desktop, 1 par row mobile
- ✓ Each iframe scrollable
- ✓ Metadata visible above iframe (badges Pill)
- ✓ Empty state gracieux si `deliverables/gsg_demo/` vide

## Functional Requirements

### Task Breakdown (3 tasks file-disjoint)

#### T001 — Lib `gsg-fs.ts` : auto-discover LPs
**Effort** : S, 30-45 min
**File** : `webapp/apps/shell/lib/gsg-fs.ts` (NEW)
**Cible** :
- `listGsgDemoFiles()` : scan `deliverables/gsg_demo/` for `*.html`
- Pour chaque HTML : parse filename for page_type (e.g., `weglot_listicle_v27_2_g.html` → `{ slug: weglot_listicle, page_type: "listicle", doctrine_version: "v27.2-g" }`)
- Read sidecar `*.multi_judge.json` if exists for score
- Return `GsgDemo[]` typed array
- Server-only (uses `node:fs`)

**Acceptance** :
- [ ] Function returns array of typed GsgDemo objects
- [ ] Handles empty dir gracefully (`return []`)
- [ ] Tolerates missing sidecar JSON (score = null)

#### T002 — API route `/api/gsg/[slug]/html`
**Effort** : XS, 15-30 min
**File** : `webapp/apps/shell/app/api/gsg/[slug]/html/route.ts` (NEW)
**Cible** :
- GET handler returns HTML content with `Content-Type: text/html`
- Security headers : `X-Frame-Options: SAMEORIGIN`, `Content-Security-Policy: default-src 'self'`
- Path traversal prevention : whitelist via `listGsgDemoFiles()` then exact match
- 404 if slug not in whitelist

**Acceptance** :
- [ ] GET `/api/gsg/weglot_listicle/html` returns 200 + HTML
- [ ] GET `/api/gsg/../../../../etc/passwd/html` returns 404 (no path traversal)
- [ ] Security headers present
- [ ] `Cache-Control: public, max-age=300` (5 min, scaffold)

#### T003 — Route `/gsg/page.tsx` + Card component
**Effort** : S-M, 45-60 min
**Files** :
- `webapp/apps/shell/app/gsg/page.tsx` (REPLACE existing scaffold from FR-1)
- `webapp/apps/shell/components/gsg/GsgLpCard.tsx` (NEW)
- `webapp/apps/shell/components/gsg/GsgEmptyState.tsx` (NEW, optional)
**Cible** :
- Server Component page : call `listGsgDemoFiles()`, render grid of cards
- Each card : Pill badges (page_type, doctrine_version, multi-judge score), iframe src=`/api/gsg/[slug]/html`, CTA "Open full"
- Empty state if no files

**Acceptance** :
- [ ] `/gsg` 200 in dev + prod
- [ ] If 3 LPs in `deliverables/gsg_demo/` → 3 cards displayed
- [ ] Iframe loads HTML successfully (no CSP block)
- [ ] Multi-judge score Pill colored : ≥70 green, 50-69 amber, <50 red

## Non-Functional Requirements

### Doctrine
- Code doctrine : `gsg-fs.ts` ≤ 800 LOC (largement OK, ~80 LOC attendu)
- Mono-concern : `gsg-fs.ts` = filesystem reader, `route.ts` = HTTP serve, `page.tsx` = render
- Anti-pattern #11 : pas de collision avec `proposals-fs.ts`, `reality-fs.ts` (3 namespacés)
- Anti-pattern : iframe needs `sandbox=""` attribute pour security ? Décision : pas de sandbox (LPs sont own content + we serve them), MAIS `X-Frame-Options: SAMEORIGIN` côté API.

### Performance
- Page load < 2s
- Iframe load < 3s (HTML files ~50-200 KB chacun)
- Bundle shell : ne doit pas augmenter > 5 KB (juste 1 page + 1-2 components)

### Sécurité
- Path traversal prevention via whitelist
- CSP `default-src 'self'` côté API route
- Pas de inline scripts injection (HTML is static, no template substitution)
- iframe `X-Frame-Options: SAMEORIGIN`

### Documentation
- MANIFEST §12 changelog post-merge
- Architecture map regen

## Success Criteria

### Routes
- [ ] `/gsg` HTTP 200 listing N LPs (N = count of `deliverables/gsg_demo/*.html`)
- [ ] `/api/gsg/[slug]/html` HTTP 200 with `Content-Type: text/html`
- [ ] Path traversal blocked (test : `/api/gsg/..%2F..%2Fetc%2Fpasswd/html` → 404)

### Gates
- [ ] Lint, parity, schemas ✓
- [ ] Typecheck + build exit 0
- [ ] Bundle First Load JS < 95 KB shared

### Runtime
- [ ] Si `deliverables/gsg_demo/weglot_listicle_v27_2_g.html` existe → card visible avec iframe preview
- [ ] Si `weglot_listicle_v27_2_g.multi_judge.json` existe avec `final_score: 70.9` → badge "70.9% Bon" green
- [ ] Empty state si dir vide ou n'existe pas

### Doctrine
- [ ] 0 régression
- [ ] 1 commit isolé
- [ ] MANIFEST §12 commit séparé

## Constraints & Assumptions

### Constraints
- **Pas de génération nouvelle LP** : c'est V2 (FastAPI deploy)
- **Pas de A/B preview** : juste single preview iframe
- **Pas de edit-in-place** : viewer only
- **`deliverables/gsg_demo/`** structure : Pour V1, on suppose `<slug>.html` + `<slug>.multi_judge.json` sidecar optional. Pour autre struct (dossier per LP), adapter dans `gsg-fs.ts`.

### Assumptions
- `deliverables/gsg_demo/*.html` lisible côté shell server (path = `path.resolve(process.cwd(), "..", "..", "..", "deliverables", "gsg_demo")` cf. `reality-fs.ts` pattern)
- Pas de credentials nécessaires (file system only)
- 3 LPs Mathis livrées valides HTML (vérifié par Playwright pendant le run #19)

## Out of Scope

### Hors scope V1
- **Live GSG trigger** : "Generate new LP" button → FastAPI V2
- **A/B preview** : multi-variant viewer
- **Edit in place** : code editor pour HTML
- **Deploy à un client** : "Push to client domain" CTA
- **Multi-judge re-run** : "Re-evaluate score" button
- **Comparison vs Weglot baseline** : split-screen diff

## Dependencies

### Externes
- Mathis ~10 min validation visuelle
- Vercel auto-deploy

### Internes
- **FR-1 SHIPPED** : route `/gsg` exists in shell (currently scaffold)
- `deliverables/gsg_demo/` directory accessible from worktree (relative path via `process.cwd()`)
- Pattern réutilisable : `reality-fs.ts` + `proposals-fs.ts` style (server-only fs reader)

### Sequencing
- T001 (gsg-fs.ts) → T002 (API route uses listGsgDemoFiles) → T003 (page uses listGsgDemoFiles) OR T001 + T002 + T003 parallel (each implements own typing)
- Prefer **T001 first** (defines types), then T002 + T003 parallel
