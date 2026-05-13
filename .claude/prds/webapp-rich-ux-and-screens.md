---
name: webapp-rich-ux-and-screens
description: Combler le gap V27 HTML vs V28 Next.js sur le rendering riche des recos + servir les 4831 screenshots existants sur disque. Sprint pivot post-diagnostic 2026-05-13.
status: active
created: 2026-05-13T10:19:20Z
parent_prd: webapp-full-buildout
wave: B-extended
fr_index: FR-2b (pivot)
---

# PRD: webapp-rich-ux-and-screens

> Sprint pivot post-diagnostic 2026-05-13. Le user a signalé que la V28 actuelle est "comme si on était revenu à zéro" comparé à la V27 HTML. Diagnostic confirme :
> - 4831 screenshots PNG sur disque, 0 servis
> - 438 fichiers `recos_enriched.json` avec format riche (reco_text long, anti_patterns, oco_anchors, etc.)
> - `AuditDetailFull.tsx` (150 LOC) render minimaliste : juste title + lift_pct
>
> Ce sub-PRD comble ce gap UX sans toucher au backend FastAPI (deferred V2).

## Executive Summary

Refactor `AuditDetailFull.tsx` pour render le format riche des recos (problème → reco → pourquoi → evidence visuelles + anti-patterns + counter-objections). Ajouter API route `/api/screenshots/[client]/[page]/[filename]` pour servir les PNG depuis `data/captures/<client>/<page>/screenshots/`.

**Hypothèse data** : la migration `migrate_v27_to_supabase.py` aura été exécutée → Supabase contient les vrais `content_json` riches per reco. Si pas encore exécuté, seed data fallback (3 clients minimalistes) reste affichée mais correctement formattée.

**Effort** : M, 2-3h wall-clock · 1 agent background.
**Coût API** : $0.
**Débloque** : Mathis valide enfin "voir des données réelles + UX riche en prod".

## Problem Statement

### Pourquoi maintenant (post-diagnostic)

Le user a signalé textuellement :
- "GSG est buggué complet. C'est même pas interactif on peut même pas lancer une génération de LP"
- "on voit aucun audit, l'UI/UX de l'audit et des recos n'a rien à voir avec ce qu'on avait mis en place"
- "On a pas les screens, on a pas les 'problème' → 'reco' et le 'pourquoi il faut le faire' comme avant"
- "Presque comme si on était revenu à zéro"

Le gap est REAL. Le master PRD a programmé une migration data qui n'a pas eu lieu, ET un rendering minimaliste vs V27 HTML.

### Ce que ce PRD apporte

- 4831 screenshots accessibles via API route sécurisée
- AuditDetailFull refactor : render reco_text long-form + anti_patterns + oco_anchors + criterion description
- Pattern doctrine pour FR-4/6/futures : 1 reco = 1 card riche expandable

## User Stories

### US-1 — Mathis (voir les screens audit)
*Comme founder qui audit ses clients, je veux que les 4831 screenshots existants soient affichés à côté des recos pour avoir le contexte visuel.*

**Acceptance Criteria** :
- ✓ API route `/api/screenshots/[client]/[page]/[filename]` HTTP 200 sert PNG depuis `data/captures/<client>/<page>/screenshots/<filename>`
- ✓ Security : whitelist via inventory + path traversal blocked + cache-control 1h
- ✓ AuditDetailFull affiche desktop + mobile screenshots fold en thumbnails cliquables (lightbox OR open new tab)
- ✓ 404 gracieux si screenshot manquant

### US-2 — Consultant (UX riche recos)
*Comme consultant qui présente un audit, je veux que chaque reco affiche : problème détecté + solution + pourquoi (anti-pattern) + comment faire (examples_good), pour avoir un discours structuré.*

**Acceptance Criteria** :
- ✓ Each RecoCard riche affiche :
  - Header : `criterion_id` + `priority` badge + `severity` badge + `pillar` badge
  - Body : `reco_text` (parsé : si contient "⚠️ Problème" ou similaire, split en sections)
  - Section "Pourquoi" : `anti_patterns[0].why_bad` + `pattern`
  - Section "Comment faire" : `anti_patterns[0].instead_do` + `examples_good`
  - Footer : `effort_days`, `ice_score`, `enricher_version` (collapsible debug)
- ✓ Top 5 expanded par défaut, autres collapsibles
- ✓ Si content_json minimaliste (seed data) : fallback gracieux (juste title + priority)

### US-3 — Consultant (evidence visuelles)
*Comme consultant, je veux voir les screenshots desktop + mobile fold de la page auditée à côté des recos, pour pouvoir pointer "regardez ce visual ici".*

**Acceptance Criteria** :
- ✓ AuditDetailFull layout : column left = recos, column right = screenshots panel
- ✓ Screenshots panel : 2 thumbnails (desktop fold + mobile fold) cliquables
- ✓ Click → open full image new tab OR lightbox modal
- ✓ Fallback si pas de screenshots disponibles : "Pas de captures pour cette page" gracieux

## Functional Requirements

### Task Breakdown (3 tasks séquentielles)

#### T001 — API route `/api/screenshots/[client]/[page]/[filename]`
**Effort** : S, 30-45 min
**File** : `webapp/apps/shell/app/api/screenshots/[client]/[page]/[filename]/route.ts` (NEW)
**Pattern existing** : `/api/gsg/[slug]/html/route.ts` (FR-3) — copy security pattern
**Cible** :
- GET handler, lit `data/captures/<client>/<page>/screenshots/<filename>` from disk
- Whitelist via `lib/captures-fs.ts` (NEW lib) : `listScreenshotsForPage(client, page)`
- Path traversal prevention : strict slug regex + exact filename match
- Security headers : `Cache-Control: public, max-age=3600`, `Content-Type: image/png`
- 404 if not in whitelist OR file missing

**Acceptance** :
- [ ] `GET /api/screenshots/aesop/home/desktop_fold.png` → 200 + PNG bytes
- [ ] `GET /api/screenshots/..%2F..%2Fetc%2Fpasswd/x/y` → 404 (path traversal blocked)
- [ ] `GET /api/screenshots/aesop/home/nonexistent.png` → 404
- [ ] `Cache-Control: public, max-age=3600` header present

#### T002 — Lib `captures-fs.ts` (server-only file system reader)
**Effort** : XS-S, 15-30 min
**File** : `webapp/apps/shell/lib/captures-fs.ts` (NEW)
**Pattern existing** : `lib/reality-fs.ts`, `lib/proposals-fs.ts`, `lib/gsg-fs.ts`
**Cible** :
- `listCaptureClients()` : scan `data/captures/*/`, exclude `_*`, return slug list
- `listPagesForClient(client)` : scan `data/captures/<client>/*/`, exclude `_*`
- `listScreenshotsForPage(client, page)` : scan `.../screenshots/*.png`, return filenames whitelist
- `screenshotPath(client, page, filename)` : returns absolute path OR null if not in whitelist
- Server-only via `import fs from "node:fs"`

**Acceptance** :
- [ ] Functions return correct lists
- [ ] Handles missing dirs gracefully
- [ ] Returns null for non-whitelisted filenames (no path traversal possible)

#### T003 — Refactor `AuditDetailFull.tsx` for rich UX
**Effort** : M, 1.5-2h
**Files** :
- Refactor `webapp/apps/shell/components/audits/AuditDetailFull.tsx`
- NEW `webapp/apps/shell/components/audits/RichRecoCard.tsx` (rich reco rendering)
- NEW `webapp/apps/shell/components/audits/AuditScreenshotsPanel.tsx`
- Optional: extend `webapp/apps/shell/components/clients/score-utils.ts` for parsing helpers (e.g., `parseRecoText`, `extractAntiPattern`)

**Cible** :
- Layout 2 columns : recos (left) + screenshots panel (right)
- Recos top-5 expanded by default, others click-to-expand
- Each card : header (criterion_id + badges) + reco_text + sections "Pourquoi" + "Comment faire" + debug collapsible footer
- Fallback gracieux si content_json minimaliste

**Acceptance** :
- [ ] Layout 2 cols desktop, stacked mobile
- [ ] Top 5 recos expanded
- [ ] reco_text rendered (line-breaks preserved, emojis preserved e.g. ⚠️)
- [ ] anti_patterns.why_bad + instead_do + examples_good rendered if present
- [ ] Screenshots thumbnails clicables → new tab full size
- [ ] Fallback graceful pour seed data minimaliste

## Non-Functional Requirements

### Doctrine
- ≤ 800 LOC par fichier (AuditDetailFull devient ~250 LOC, RichRecoCard ~150 LOC OK)
- Mono-concern : RichRecoCard = render 1 reco, AuditScreenshotsPanel = render screenshots, AuditDetailFull = layout
- Anti-pattern #11 : `captures-fs.ts` distinct des autres `*-fs.ts` (namespaced par feature)
- Pas de `process.env[key]` dynamic
- Pas de service_role exposé client-side (API route server-only)

### Performance
- Page load < 2s
- Screenshots lazy-load (`loading="lazy"` attribute)
- Cache 1h sur screenshots (immutable per audit)
- Bundle shell : ne doit pas augmenter > 10 KB

### Sécurité
- Path traversal blocked (test : `/api/screenshots/..%2F..%2Fetc%2Fpasswd/x/y` → 404)
- Whitelist strict via `listScreenshotsForPage()`
- Pas de symlink follow (Node fs default OK)

### Documentation
- MANIFEST §12 changelog post-merge
- Architecture map regen

## Success Criteria

### Routes
- [ ] `/api/screenshots/[client]/[page]/[filename]` HTTP 200 sur fichier existant, 404 sinon
- [ ] Path traversal blocked

### UX
- [ ] `/audits/[clientSlug]/[auditId]` affiche reco_text long + anti_patterns + screenshots
- [ ] Top 5 recos expanded, autres collapsibles
- [ ] Screenshots thumbnails clicables

### Gates
- [ ] Lint, parity, schemas ✓
- [ ] Typecheck + build exit 0
- [ ] Bundle < 100 KB shared

### Doctrine
- [ ] 0 régression
- [ ] 1 commit isolé
- [ ] MANIFEST §12 commit séparé

## Constraints & Assumptions

### Constraints
- **Pas de modif schema Supabase** (utiliser content_json existant)
- **Pas de FastAPI deploy** (deferred V2)
- **Pas de génération nouvelle reco** (read-only viewer)
- **Pas de cropping/resizing PNG** (sert tel quel, browser scale via CSS)

### Assumptions
- `data/captures/<client>/<page>/screenshots/*.png` accessible depuis worktree (relative path via `process.cwd()`)
- Migration `migrate_v27_to_supabase.py` aura été exécutée OR seed data minimaliste reste (les 2 cas doivent être gérés gracieusement)
- Format `reco.content_json` cohérent avec `recos_enriched.json` format (cf sample dans `data/captures/aesop/home/recos_enriched.json`)

## Out of Scope

### Hors scope V1 (ce sub-PRD)
- **Génération reco nouvelle** : FastAPI V2
- **Trigger audit depuis UI** : FastAPI V2
- **Crop/resize screenshots** : optimization V2
- **Lightbox modal** : optionnel, fallback = open new tab
- **PDF export audit** : V2

## Dependencies

### Externes
- Mathis ~15 min validation visuelle post-deploy
- Migration data effectuée par Mathis (cf instructions chat)

### Internes
- **FR-1 + FR-2 SHIPPED** : routes `/audits/[clientSlug]/[auditId]` existent
- Pattern `lib/*-fs.ts` réutilisable
- `@growthcro/ui` Card + Pill components

### Sequencing
- T001 ← T002 (API uses listScreenshotsForPage)
- T003 ← T001 (screenshots panel uses API URL)
- ORDRE : T002 → T001 → T003

## Notes finales

Ce sub-PRD est en réaction directe au feedback Mathis 2026-05-13 sur le gap V27 HTML vs V28 Next.js. Il ne **remplace pas** FR-4 webapp-learning-lab (conditional) ni FR-6 webapp-polish-validation (polish générique) — il les **précède** logiquement car comble le gap user-visible avant le polish.
