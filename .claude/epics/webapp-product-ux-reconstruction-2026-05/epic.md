---
name: webapp-product-ux-reconstruction-2026-05
status: backlog
created: 2026-05-17T15:00:00Z
updated: 2026-05-17T15:00:00Z
progress: 0%
prd: .claude/prds/webapp-product-ux-reconstruction-2026-05.md
github: https://github.com/GrowthSociety-GS/growth-cro/issues/65
---

# Epic: webapp-product-ux-reconstruction-2026-05

> Source de vérité primaire : [`.claude/docs/state/WEBAPP_PRODUCT_AUDIT_2026-05-17.md`](../../docs/state/WEBAPP_PRODUCT_AUDIT_2026-05-17.md). PRD : [`.claude/prds/webapp-product-ux-reconstruction-2026-05.md`](../../prds/webapp-product-ux-reconstruction-2026-05.md).

## Overview

Refonte UX/produit totale de la webapp GrowthCRO V28 au-dessus du socle technique préservé. **Pas de réécriture backend.** L'epic est découpé en **10 phases (A→J)** organisées en **vagues parallélisables** quand les dépendances le permettent.

Trois lignes de force :
1. **Vérité produit** — auditer route-par-route, définir IA cible, Module Maturity Model, archiver dead code (Phase A + J0).
2. **Plateforme** — shell uniforme, états canoniques, worker liveness, edit/save pattern global (Phases B/C/D/E).
3. **Espaces métier** — Command Center actionnable, Client workspace progressive disclosure, Audit/Reco orchestré, GSG Studio E2E, Advanced Intelligence honnête (Phases C/D/E/F/G).
4. **Hardening** — design system productif calme, perf budgets, Playwright smoke suite, docs cohérentes (Phases H/I/J).

Ce qui **ne sera pas touché** : moteurs Python (`moteur_gsg/`, `moteur_multi_judge/`, `growthcro/` Python sauf worker handler `audit_full` + heartbeat), doctrine V3.2.1, PRESERVE_CREATIVE_LATITUDE Elite Mode, Brand DNA, AURA, Opportunity Layer, Gates (ClaimsSourceGate, VerdictGate), schémas SCHEMA/, structure D1.A single shell.

## Architecture Decisions

| Décision | Rationale |
|----------|-----------|
| **Mono-concern 8-axes** pour tout nouveau module Python (worker handler `audit_full`, system_health migration) | Per CODE_DOCTRINE.md. Validation / persistence / orchestration / CLI / prompt / API / scoring / capture. |
| **Conventional commits, 1 issue per commit** | Traceability + rollback granulaire. `<type>(<scope>): <subject> [#<issue>]`. |
| **No doctrine V3.2.1 modification** | Frozen pour cet epic. V3.3 = PRD séparé via doctrine-keeper. |
| **Manifest §12 bump as SEPARATE commit** | Per CLAUDE.md. Never bundled with implementation. |
| **D1.A single shell preserved** | Locked 2026-05-14. Pas de re-fédération microfrontends. |
| **PRESERVE_CREATIVE_LATITUDE intact** | Webapp ne modifie jamais `moteur_gsg/creative_engine/elite/*`. |
| **Renaissance Wave 2/3 paused** | CR-04..CR-08 reprise post-acceptance epic. |
| **Feature flags per phase** | `FEATURE_NEW_UX_<phase>` env var pour rollback rapide en preview/prod. |
| **Module Maturity Model honest** | Aucun fake interactivity, aucune fake data, statuts toujours visibles. |
| **Reality/Learning research spikes first** | Pas de UI build sans research/decision tranchée. |

## Technical Approach

### Frontend (Next.js shell)

**Nouveaux composants `apps/shell/components/`** :
- `states/` : `EmptyState`, `LoadingSkeleton`, `BlockedState`, `WorkerOfflineState`, `ErrorBoundary` canoniques (FR-6)
- `feedback/ActionButton` : pending/success/failure + next_step + retry/cancel (FR-7)
- `maturity/ModuleHeader` : affiche status + reason + next_step CTA (FR-5)
- `feedback/WorkerHealthBadge` : topbar global (FR-3)
- `data-table/DataTable` : sort/filter/pagination/empty/loading générique (FR-20)
- `command-center/`: refonte 4 zones (FR-8)
- `gsg/BriefWizard/*` : wizard 6-8 étapes produisant BriefV2 (FR-10)
- `gsg/Preview/*` : iframe + QA status + export (FR-12)
- `recos/RecoEditor` : pattern useEdit (FR-13)
- `opportunities/Board` : Promote reco → opportunity (FR-15)

**Nouvelles routes `apps/shell/app/`** :
- `gsg/studio/page.tsx` (FR-10) — entrée Studio
- `gsg/runs/page.tsx` (FR-10) — history
- `gsg/runs/[id]/page.tsx` (FR-10/11/12) — detail + preview
- `gsg/design-grammar/[client]/page.tsx` (FR-10) — viewer dédié
- `gsg/page.tsx` — redirect → `/gsg/studio` (FR-10)
- `opportunities/page.tsx` ou tab dans /recos (FR-15)

**Routes refondues** :
- `app/page.tsx` (home Command Center FR-8)
- `app/clients/[slug]/page.tsx` (progressive disclosure FR-2 stories)
- `app/audits/[clientSlug]/[auditId]/page.tsx` (workflow refondu FR-9)
- `app/learning/page.tsx` (post research spike Q2)
- `app/reality/*` (UX honest activation FR-16, no backend wire)
- `app/geo/*` (UX honest activation FR-17)

**Routes archivées / cachées** :
- `app/audit-gads`, `app/audit-meta` cachées de la nav (FR-25)
- `app/funnel` ghost route supprimée (FR-24)
- Composants `CommandCenterTopbar`, `ViewToolbar` legacy supprimés (FR-24)

**Hooks/lib `apps/shell/lib/`** :
- `lib/useEdit.ts` (FR-13)
- `lib/maturity.ts` (FR-5)
- `lib/cmdk-items.ts` resync avec nouvelle IA (Phase B1)

### Backend (minimal additions)

**Worker (`growthcro/worker/`)** :
- Ajout `dispatcher.py` handler `audit_full` : nouveau kind qui chaîne capture → score → recos dans une seule run row, mais expose progress_pct par sub-step via metadata_json (FR-9)
- Ajout `daemon.py` heartbeat : PATCH `system_health` row toutes 30s (FR-3)
- Decision spike Phase G4 : implement OR remove `experiment` dispatcher (FR-19)

**Supabase migrations (`supabase/migrations/`)** :
- `20260518_0001_system_health.sql` : table `system_health(component, last_seen_at, version, status, error_message)` + RLS (FR-4)
- Decision Phase G4 : éventuellement DROP table `experiments` si archive option choisie

**API routes (`apps/shell/app/api/`)** :
- `GET /api/worker/health` : retourne dernier heartbeat + status active/lagging/offline (FR-3)
- `POST /api/audits/[id]/run` (ou extend `/api/runs` schema) : déclenche run `audit_full` (FR-9)
- Eventuel merge `/api/recos/[id]` + `/lifecycle` selon décision Phase E2 (FR-14)

**Pas de modification** :
- `moteur_gsg/`, `moteur_multi_judge/`, `growthcro/` Python (sauf worker)
- `playbook/`, `data/`, `SCHEMA/`
- Doctrine V3.2.1 / V3.3

### Infrastructure

- **Env vars** : aucune nouvelle requise pour V1 webapp UX. Reality/GEO env vars deferred (Mathis decision).
- **Vercel** : pas de change `vercel.json`. Cron `reality-poll` deferred pending Mathis decision.
- **Feature flags** : `FEATURE_NEW_UX_HOME`, `FEATURE_NEW_UX_GSG`, `FEATURE_NEW_UX_AUDIT`, ... (default false en prod, true preview)
- **Playwright** : extension `webapp/tests/e2e/` suite (FR-23)

## Implementation Strategy

### Vagues

**Wave 0 (immediate, 1j)** — Quick wins parallèles à Phase A :
- J0-1 : webapp/README microfrontends → single shell (déjà appliqué dans ce PR)
- J0-2 : Clarify epic master hierarchy
- J0-3 : Consolidate CONTINUATION_PLAN cascade

**Wave 1 (~3-5j)** — Phase A audit-only, vérité produit :
- A1 : Route/product audit final
- A2 : Target Information Architecture (5 espaces)
- A3 : Module Maturity Model definition

**Wave 2 (~5-7j)** — Phase B shell foundation :
- B1 : App shell simplifié (sidebar/header/breadcrumbs/cmd-k)
- B2 : Global loading/empty/error/blocked/worker-offline states
- B3 : Action Feedback System + Worker Health Badge + system_health migration

**Wave 3 (~3-4j)** — Phase C Command Center :
- C1 : Rebuild home as Command Center (4 zones)
- C2 : Performance pass home

**Wave 4 (parallel ~5-7j chacune, peut overlap)** — Phases D/E :
- D1/D2/D3 : Client workspace + orchestrated audit_full + progressive disclosure
- E1/E2/E3 : Audit workflow + reco editing + Opportunities board

**Wave 5 (~7-10j)** — Phase F GSG Studio :
- F1 : Studio product spec
- F2 : Intake wizard E2E
- F3 : Run wiring (auto-preview)
- F4 : Preview/export UX
- F5 : Design Grammar placement

**Wave 6 (parallel ~3-5j)** — Phase G Advanced Intelligence :
- G1 : Reality UX honest (no backend wire)
- G2 : GEO UX honest
- G3 : Learning Layer **research spike** → decision doc
- G4 : Experiments **decision spike** → implement OR archive

**Wave 7 (continuous, ~3-5j cumulés)** — Phase H design system :
- H1 : Visual simplification
- H2 : Component standards
- H3 : Mobile/tablet sanity

**Wave 8 (~3-5j)** — Phase I hardening :
- I1 : Query audit + lazy boundaries
- I2 : Worker/run reliability UX
- I3 : Vercel prod Playwright smoke suite

**Wave 9 (~1-2j)** — Phase J docs/memory final :
- J1 : Docs source-of-truth final cleanup
- J2 : Status memory update via growthcro-status-memory

### Risk mitigation

- **Anti-drift** : `growthcro-anti-drift` skill invoqué AVANT chaque issue. Pre-flight imprimé (CURRENT ISSUE / IN SCOPE / OUT OF SCOPE / EXPECTED FILES / DRIFT RISK / STOP CONDITIONS / FILES_ALLOWED / FILES_FORBIDDEN).
- **Per-issue scope** : 1-6 fichiers touchés max, 50-300 LOC ajoutées max. Si dépasse → STOP, split.
- **Per-phase rollback** : feature flag env var, redéploiement Vercel preview, `git revert` si urgence.
- **Regression fixtures** : `pytest tests/` reste vert. `python3 SCHEMA/validate_all.py` exit 0. `python3 scripts/lint_code_hygiene.py --staged` exit 0.
- **Anti-régression Renaissance** : 215 tests Renaissance verts. `PRESERVE_CREATIVE_LATITUDE` constant inchangé.

### Testing approach

- TDD par `test-driven-development` skill pour worker handler `audit_full` (1 fixture E2E) et migration `system_health` (RLS test)
- Playwright E2E par phase B/C/D/E/F (mock backend si nécessaire)
- Playwright smoke suite Phase I3 sur prod URL (9 parcours)
- Visual regression : screenshots dual-viewport before/after par phase, attached to issue close

## Task Breakdown Preview

Phases A et J0 atomiques détaillées (6 issues sur 33 totales). Phases B-J seront fichées au moment du dispatch (per Mathis choice 2026-05-17 : "Créer Phase A + J0 maintenant, le reste au moment de lancer").

| # | Slug | Title | Size | Hours | Parallel? | Depends on |
|---|------|-------|------|-------|-----------|------------|
| 66 | A1 | Auditer routes produit + classifier garder/fusionner/cacher | M | 6 | yes | — |
| 67 | A2 | Définir Target Information Architecture 5 espaces | M | 5 | no | #66 |
| 68 | A3 | Définir Module Maturity Model + matrix initiale | S | 3 | yes | #66 |
| 69 | J0-1 | Corriger webapp/README microfrontends → single shell | S | 1 | yes | — |
| 70 | J0-2 | Clarifier epic master hierarchy (webapp-stratosphere vs reconstruction-2026-05 + 4 GSG orphelines) | S | 2 | yes | — |
| 71 | J0-3 | Consolider CONTINUATION_PLAN cascade en 1 doc current | S | 1 | yes | — |
| TBD | B1 | Refondre app shell (sidebar uniforme + header + breadcrumbs + cmd-k) | L | 10 | no | #66 |
| TBD | B2 | Implémenter 5 canonical states components | M | 6 | no | #67, B1 |
| TBD | B3 | Worker Health endpoint + system_health migration + topbar badge | L | 10 | no | B1 |
| TBD | C1 | Rebuild home as Command Center (4 zones) | L | 10 | no | A2, B1, B2 |
| TBD | C2 | Performance pass home + lazy boundaries | M | 6 | no | C1 |
| TBD | D1 | Client overview redesign | M | 7 | yes (vs E*) | A2, B |
| TBD | D2 | Client actions E2E (worker handler audit_full + orchestrated capture→score→recos) | L | 12 | no | B3, D1 |
| TBD | D3 | Client detail progressive disclosure | M | 6 | no | D1 |
| TBD | E1 | Audit workflow redesign | M | 8 | yes (vs D*) | A2, B |
| TBD | E2 | Reco editing/saving global pattern (useEdit + lifecycle pill) | M | 7 | no | B, E1 |
| TBD | E3 | Opportunities board (lire Opportunity Layer module) | M | 6 | no | E2 |
| TBD | F1 | GSG Studio product spec doc | S | 3 | yes | A2 |
| TBD | F2 | GSG intake wizard E2E (BriefV2 complet) | XL | 16 | no | F1, B |
| TBD | F3 | GSG run wiring (auto-preview, no UUID paste) | M | 6 | no | F2, B3 |
| TBD | F4 | GSG preview/export UX | L | 10 | no | F3 |
| TBD | F5 | Design Grammar route split + redirect | S | 3 | yes | F1 |
| TBD | G1 | Reality UX honest activation (no backend wire) | M | 6 | yes | A3, B |
| TBD | G2 | GEO UX honest activation | S | 4 | yes | A3, B |
| TBD | G3 | Learning Layer research spike → decision doc | M | 8 | yes | A3 |
| TBD | G4 | Experiments decision spike (implement OR archive) | S | 4 | yes | A3 |
| TBD | H1 | Visual simplification pass | M | 6 | yes | B, C |
| TBD | H2 | Component standards canonical | M | 8 | no | H1 |
| TBD | H3 | Mobile/tablet sanity | M | 6 | no | H2 |
| TBD | I1 | Query audit + lazy boundaries + perf budget | M | 6 | no | C, D, E |
| TBD | I2 | Worker/run reliability UX (stuck pending, retry, cancel) | M | 6 | no | B3 |
| TBD | I3 | Vercel prod Playwright smoke suite (9 parcours desktop+mobile) | L | 10 | no | I1, I2 |
| TBD | J1 | Docs source-of-truth final cleanup + manifest §12 | S | 3 | no | tout |
| TBD | J2 | Status memory update via growthcro-status-memory | S | 2 | no | J1 |

**Total estimate** : ~210 heures dev = 5-7 semaines solo dev temps plein, 8-10 semaines avec interruptions + reviews Mathis.

## Dependencies

```
DEPENDENCIES GRAPH (issues nommées par leur slug local):

  Wave 0 (parallel, immediate):
    J0-1, J0-2, J0-3 (no deps)

  Wave 1:
    A1 (no deps)
    A1 → A2
    A1 → A3 (parallel to A2)

  Wave 2:
    A2 + A3 → B1
    A3 → B2
    B1 → B2
    B1 → B3 (parallel to B2 if disjoint files — they are: states/ vs feedback/)

  Wave 3:
    A2 + B1 + B2 → C1
    C1 → C2

  Wave 4 (parallel within wave):
    A2 + B → D1, E1 (parallel, disjoint files)
    B3 + D1 → D2
    D1 → D3
    B + E1 → E2
    E2 → E3

  Wave 5 (GSG Studio):
    A2 → F1
    F1 + B → F2
    F2 + B3 → F3
    F3 → F4
    F1 → F5 (parallel to F2)

  Wave 6 (parallel):
    A3 + B → G1, G2, G3, G4 (all parallel, disjoint files)

  Wave 7 (parallel/continuous):
    B + C → H1
    H1 → H2 → H3

  Wave 8:
    C + D + E → I1
    B3 → I2
    I1 + I2 → I3

  Wave 9:
    tout → J1 → J2

PARALLELIZATION WAVES:
  Wave 0 (parallel): J0-1, J0-2, J0-3
  Wave 1 (sequential A1 then parallel A2/A3): A1 → {A2, A3}
  Wave 2 (sequential B1 then parallel B2/B3): B1 → {B2, B3}
  Wave 3 (sequential): C1 → C2
  Wave 4 (parallel D and E): {D1, E1} → ...
  Wave 5 (mostly sequential, F5 parallel to F2): F1 → {F2, F5} → F3 → F4
  Wave 6 (parallel): {G1, G2, G3, G4}
  Wave 7 (continuous): H1 → H2 → H3
  Wave 8 (sequential): I1 → I2 → I3
  Wave 9 (sequential): J1 → J2
```

## Success Criteria

- All 27 FRs from PRD map to ≥1 acceptance criterion in ≥1 task.
- 13 PRD Success Criteria all met before epic close.
- All regression fixtures green (`pytest`, `python3 SCHEMA/validate_all.py`, `python3 scripts/lint_code_hygiene.py --staged`).
- 215 tests Renaissance restent verts.
- 0 new file >300 LOC sans single-concern reviewer affirmation.
- 0 anti-pattern CLAUDE.md re-introduced.
- 9 Playwright smoke E2E green sur prod Vercel.
- TTFB home p50 <500ms sur Vercel prod.
- Heuristique <30s validée sur 3 personnes externes (test post Phase E).

## Estimated Effort

- **Total hours** : ~210h dev
- **Critical path** : A1 → A2 → B1 → B3 → D2 (worker handler) → C1 → I3 = ~70h sur le critical path
- **Calendar** :
  - 1 agent solo séquentiel : 8-10 semaines
  - Avec parallelization Wave 4 + 6 : 6-8 semaines
- **Mathis validations** : 6 milestones (end of A, B, C, D+E, F, I3)

## Tasks Created (Wave 0 + Wave 1)

> Wave 0 + Wave 1 atomic tasks created now per Mathis decision 2026-05-17 ("Créer Phase A + J0 maintenant, le reste au moment de lancer"). Waves 2-9 fichées au moment du dispatch.

- [ ] [#66](https://github.com/GrowthSociety-GS/growth-cro/issues/66) — A1 — Auditer routes produit + classifier garder/fusionner/cacher — `A1.md`
- [ ] [#67](https://github.com/GrowthSociety-GS/growth-cro/issues/67) — A2 — Définir Target Information Architecture 5 espaces — `A2.md`
- [ ] [#68](https://github.com/GrowthSociety-GS/growth-cro/issues/68) — A3 — Définir Module Maturity Model + matrix initiale — `A3.md`
- [ ] [#69](https://github.com/GrowthSociety-GS/growth-cro/issues/69) — J0-1 — Corriger webapp/README microfrontends → single shell — `J0-1.md` (work already bundled in commit e42a36a)
- [ ] [#70](https://github.com/GrowthSociety-GS/growth-cro/issues/70) — J0-2 — Clarifier epic master hierarchy — `J0-2.md`
- [ ] [#71](https://github.com/GrowthSociety-GS/growth-cro/issues/71) — J0-3 — Consolider CONTINUATION_PLAN cascade en 1 doc current — `J0-3.md`

Epic GitHub : [#65](https://github.com/GrowthSociety-GS/growth-cro/issues/65). Waves 2-9 issues fichées au moment du dispatch (per Mathis decision 2026-05-17).
