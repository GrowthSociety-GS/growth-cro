# Webapp Product Audit — 2026-05-17

> Document canonique d'audit produit/UX de la webapp GrowthCRO. Anchore le PRD [`webapp-product-ux-reconstruction-2026-05`](../../prds/webapp-product-ux-reconstruction-2026-05.md) et l'epic associé.

**Auteurs** : Codex (audit Vercel deployed) + Claude Code (audit read-only des sources `webapp/`, `supabase/`, `growthcro/worker/`, `.claude/docs/**`).
**Date** : 2026-05-17.
**Périmètre** : `webapp/apps/shell/**`, `webapp/packages/**`, `supabase/migrations/**`, `growthcro/worker/**`, `.claude/docs/architecture/**`, `.claude/docs/state/**`, `.claude/prds/**`, `.claude/epics/**`.
**Méthode** : 4 sub-audits parallèles read-only (routes/UI, backend/data, docs contradictions, workflows E2E) consolidés.

---

## 0. Verdict global

**La webapp n'est PAS un lab déguisé en produit. C'est un produit core viable (≈60%) entouré de skeleton honnêtes (≈25%) et de dead UI (≈15%).**

Le socle technique est sain et réutilisable :
- Next.js 14 App Router single shell (D1.A locked 2026-05-14)
- 20 routes, 122 composants (68 client islands), 19 API routes
- Supabase EU avec RLS actif, helpers `is_org_member()` / `is_org_admin()`
- Worker daemon Python qui polle `runs` toutes 30s, atomic claim, 9 types supportés
- 19 API routes admin-gated avec sanitization metadata jsonb
- Primitives design propres : `Card`, `KpiCard`, `Pill`, `TriggerRunButton`, Sidebar+CmdK

**Ce qui ne va pas, c'est l'expérience produit posée par-dessus** :
- navigation orientée architecture interne (modules), pas workflows utilisateur
- home en mur de KPIs/charts/panels sans hiérarchie actionnable
- workflows qui s'arrêtent en chemin sans le dire (capture déclenchée, score/recos pas chaînés)
- worker liveness invisible → runs stagnent en `pending` sans feedback
- modules avancés affichés comme actifs alors qu'ils tournent à vide (Reality, GEO, Scent)
- 2 routes décoratives (`/audit-gads`, `/audit-meta`) avec boutons disabled "post-MVP"
- docs qui se contredisent (webapp/README dit 5 microfrontends, code est single shell)

**Décision stratégique** : ne pas réécrire le socle. Refondre l'expérience produit/UX au-dessus.

---

## 1. Routes — état honnête route-par-route

### 1.1 Routes vert (E2E fonctionnel, à garder)

| Route | Pourquoi solide |
|---|---|
| `/` (home) | 9 queries Supabase parallèles, RSC orchestration propre, FleetPanel + ClientHeroDetail client islands interactives, graceful fallback Supabase error. **Mais trop dense — refonte UX requise (C1).** |
| `/clients` | Server-fetch + filters/sort/pagination client URL-driven (`useUrlState`). Pattern réutilisable. |
| `/clients/[slug]` | Fiche client server-rendered avec stats + recos + audits + GSG handoff link. **Densité à rebalancer.** |
| `/audits` | ClientPicker minimal mais fonctionnel. |
| `/audits/[clientSlug]/[auditId]` | 4 queries parallèles propres : client + audit + recos + audits siblings. Multi-judges nav. TriggerRunButton re-run. AuditEditTrigger modal. |
| `/recos` | Cross-client reco aggregator, same pattern que /clients. Lift-based sort logique. |
| `/learning` | Vote queue optimistic UI (4 boutons accept/reject/refine/defer), proposals depuis FS + Supabase lifecycle counts. |
| `/experiments` | SampleSizeCalculator interactif + RampUpMatrix + KillSwitchesMatrix + ActiveExperimentsList. Cohabitation server + client islands propre. |
| `/doctrine` | Stateless, PILIERS[] hardcoded inline, PillierBrowser + CritereDetail + ClosedLoopDiagram SVG. Pédagogique solide. |
| `/settings` | 3 tabs (profile, team, usage), role-gated via `getCurrentRole()`, server actions. |
| `/privacy`, `/terms` | Public, lecture seule, OK. |
| `/auth/*`, `/login` | OAuth callbacks Supabase, fonctionnel. |

### 1.2 Routes orange (partielles, à repenser)

| Route | Problème |
|---|---|
| `/gsg` | Design Grammar **viewer** uniquement. Le brief/run/preview vit ailleurs (`/gsg/handoff`). Aucun CTA croisé. Le user atterrit dessus et croit que c'est le studio. |
| `/gsg/handoff` | Wizard existe, payload solide passé au worker, mais `output_path` écrit par worker **après** status=`completed`. Race possible → preview vide avec message "worker doit être patché". Pas de validation post-completion. |
| `/reality` | Heat map + per-client drill. Skeleton honnête (graceful "0/5 configured"). **Module Maturity Model absent** → l'utilisateur ne sait pas si c'est cassé ou pas configuré. |
| `/reality/[clientSlug]` | Skeleton parental, OAuth dance post-MVP. |
| `/geo` | EnginePresenceCards + QueryBankViewer read-only. Pas de clés API provisionnées. Idem maturity model manquant. |
| `/scent` | Disk walk pour `scent_trail.json`. Affiche "Aucun scent trail" sur 95% des installs (captures cross-channel deferred). |

### 1.3 Routes rouge (décoratives ou cassées, à archiver / cacher)

| Route | Statut |
|---|---|
| `/audit-gads` | Bouton "New audit (CSV)" **disabled** avec title="Form UI post-MVP". Instructions CLI uniquement. Pas de form, pas de mutation. **À cacher de la nav.** |
| `/audit-meta` | Idem `/audit-gads`. |
| `/funnel` | Route mentionnée dans nav config mais **pas de `page.tsx`**. Ghost route. |

### 1.4 Composants dead code à supprimer

| Composant | État |
|---|---|
| `components/command-center/CommandCenterTopbar.tsx` | Remplacé par `StickyHeader`, mais coexiste encore dans `app/page.tsx:224`. Legacy import. |
| `components/.../ViewToolbar.tsx` | Utilisé uniquement sur `/doctrine`. Redondant avec gc-topbar pattern partout ailleurs. |

---

## 2. Backend honesty check

### 2.1 Tables Supabase fantômes (créées mais jamais utilisées)

| Table | Migration | État |
|---|---|---|
| `screenshots` | `20260513_0005` | CREATE TABLE jamais writée. Route `/api/screenshots/[client]/[page]/[filename]` sert depuis FS ou Storage redirect. **Table morte.** |
| `experiments` | `20260514_0021` | CREATE TABLE + RLS policies définies. Zéro routes API, zéro mutations, zéro worker dispatch (dispatcher = `print("not implemented")`). **Table morte.** |

### 2.2 Dispatchers worker honnêtes vs mensongers

Source : `growthcro/worker/dispatcher.py:36-47`

| Type | CLI | Statut | Artefact |
|---|---|---|---|
| `capture` | `growthcro.capture.cli` | ✅ E2E | PNG + metadata JSON → `data/captures/<client>/<page>/` |
| `score` | `growthcro.scoring.cli specific <label> <page>` | ✅ E2E | scores merged into `audits` row |
| `recos` | `growthcro.recos.cli enrich --client X --page Y` | ✅ E2E | rows insérées dans `recos` |
| `gsg` | `moteur_gsg.orchestrator --mode <mode> --client X --page-type Z ...` | ✅ E2E | HTML file → `deliverables/gsg/<client>/<mode>/<run_id>.html` |
| `multi_judge` | `moteur_multi_judge.orchestrator --client X --page Y` | ✅ E2E | JSON matrix → `data/` |
| `reality` | `growthcro.reality.poller --client X --engine <engine>` | ✅ E2E backend / ⚠️ credentials manquent | rows dans `reality_snapshots` |
| `geo` | `growthcro.geo --client X --engines <str> --limit N --brand X --keywords CSV` | ✅ E2E backend / ⚠️ keys OPENAI/PERPLEXITY manquent | rows dans `geo_audits` |
| `audit` | alias de `capture` (legacy) | ✅ E2E (deprecated alias) | idem capture |
| `experiment` | **`print("not implemented")`** | 🔴 **NOOP — returncode=0 → run marked "completed" sans rien faire. Mensonge UX.** | none |

### 2.3 API routes

19 routes total, toutes admin-gated via `requireAdmin()` ou RLS-bound :
- 9 routes `/api/runs*` et `/api/audits*` et `/api/recos*` : 🟢 LIVE
- 5 OAuth callbacks (catchr, meta-ads, google-ads, shopify, clarity) : 🟢 LIVE (token store)
- `/api/cron/reality-poll` : ⚠️ UNTESTED (external cron job assumé — si pas configuré, zéro data reality)
- `/api/screenshots/*`, `/api/design-grammar/*`, `/api/gsg/[slug]/html` : 🟢 LIVE (FS/Storage serve)

**Trou critique** : `/api/audits` POST crée la row `audits` mais **ne déclenche aucun run**. Il faut un POST séparé `/api/runs` `type=capture` puis encore deux pour `score` et `recos`. **Aucune orchestration chained.** L'UI doit faire 3 POSTs séquentiels, et ne le fait pas aujourd'hui.

### 2.4 Worker liveness

- Worker daemon poll 30s, atomic claim, stdout/stderr tail dans `metadata_json` (2KB max chacun)
- **Aucun health check exposé** : pas de table `system_health`, pas de route `/api/worker/health`, pas de heartbeat
- Si daemon crash ou pas lancé : rows `runs` stagnent en `pending` indéfiniment
- L'UI affiche `RunStatusPill` amber "en attente" indéfiniment → confusant
- **Suggestion** : ajouter `system_health` table avec `last_seen_at`, heartbeat 30s depuis daemon, endpoint `/api/worker/health`, badge global dans topbar

---

## 3. Workflows E2E — reality check

### W1 — Create client : 🟢 VERT

UI form → POST `/api/clients` validate (slug regex, URL http/https, business_category, panel_role enum) → `createClientRow()` → INSERT clients → `router.push(/clients/<slug>)` + `router.refresh()`.
Feedback : toast inline OK / erreur. Redirect immédiat.

### W2 — Audit run (capture → score → recos) : 🟠 ORANGE

UI bouton `<TriggerRunButton type="capture">` → POST `/api/runs` `type=capture` → worker → `growthcro.capture.cli` → PNG + metadata.

**Problèmes** :
- ❌ Score et recos **pas chaînés** automatiquement après capture. Il faut deux POSTs séparés `type=score` puis `type=recos`. L'UI n'orchestre rien.
- ❌ Pas de refresh auto UI quand run complète. `RunStatusPill` passe au vert via Realtime channel `public:runs`, mais les recos remontées ne réappa raissent qu'au refresh manuel.
- ❌ Pas de progress visible entre capture/score/recos.

### W3 — Edit reco : 🟢 VERT

PATCH `/api/recos/[id]` validation (title 2-500c, priority P0-P3, effort/lift S/M/L, severity) → fetch existing content_json → merge → UPDATE → 200 + toast.

**Gap** : `lifecycle_status` (draft/validated/shipped) géré via **endpoint séparé** `/api/recos/[id]/lifecycle`. Deux chemins pour deux updates = confusion UX. Pattern global d'édition manquant.

### W4 — GSG generation : 🟠 ORANGE

`/gsg/handoff` → `<GsgModesSelector>` (5 modes complete/replace/extend/elevate/genesis) → `<BriefWizard>` collecte client, objectif, audience, angle, CTA → `<TriggerRunButton type="gsg">` → POST `/api/runs` avec payload complet → worker → `moteur_gsg.orchestrator --mode <mode> --client <slug> --objectif --audience --angle ...`.

**Bons points** :
- ✅ Payload complet passé au CLI (mode, objectif, audience, angle).
- ✅ Wizard déterministe, pas de mega-prompt.
- ✅ Iframe preview via `/api/gsg/[slug]/html` avec CSP strict.

**Problèmes** :
- ❌ `output_path` écrit par worker **après** status=`completed`. Race possible → preview affiche "worker doit être patché".
- ❌ Pas de validation post-completion que HTML existe.
- ❌ Wizard pas exposé comme **Studio** (route `/gsg` = viewer, pas le studio).
- ❌ Plus profond : pas de paste UUID dans la doc, mais le flow d'attache automatique du `runId` à la preview est fragile (URL state pas garanti).

### W5 — Reality / GEO / Learning runs

- **Reality** : 🟠 backend OK, mais credentials env vars manquent (Catchr, Meta, Google, Shopify, Clarity). Cron `/api/cron/reality-poll` external-dependent.
- **GEO** : 🟠 backend OK, mais OPENAI_API_KEY + PERPLEXITY_API_KEY manquent. Anthropic seul actif sur 4/56 clients.
- **Learning** : 🟢 vote queue UI fonctionnelle, proposals lifecycle visible. Mais le pattern d'apprentissage lui-même (proposals JSON → Bayesian update doctrine) **est questionné par Mathis** (voir §6 OPEN QUESTIONS).
- **Experiments** : 🔴 dispatcher = `print("not implemented")`. UI peut envoyer un run, marque "completed" sans rien faire. Mensonge UX.

### Worker liveness UX : 🔴 ROUGE (trou critique)

- Zéro signal visuel si daemon down.
- Aucune route `/api/worker/health`.
- Pas de badge "worker online/offline" dans la topbar.
- Runs `pending` stagnent indéfiniment → user croit que c'est cassé.

---

## 4. Module Maturity Model (proposé)

Six statuts pour gouverner l'affichage UI, à wirer dans chaque loader server :

```ts
type Maturity = {
  status:
    | 'active'              // E2E fonctionnel, données réelles
    | 'ready_to_configure'  // Worker prêt, credentials/env manquants
    | 'no_data'             // Worker prêt, credentials OK, pas encore de run
    | 'blocked'             // Dépendance critique manquante (worker offline, etc.)
    | 'experimental'        // Schéma DB + code stub, pas d'effet réel
    | 'archived'            // Code/route à retirer
  reason?: string           // "Catchr OAuth not configured"
  next_step?: { label: string, href: string }
}
```

Matrix initiale par module :

| Module | Status proposé | Reason | Next step |
|---|---|---|---|
| Audit (capture) | active | — | — |
| Audit (score, recos) | active mais orchestration manquante | "Capture → score → recos not chained" | Fix via E1-E2 issues |
| Recos editor | active | — | — |
| Recos lifecycle | active | "Two-endpoint pattern unifying needed" | Fix via E2 |
| Learning vote queue | active | "Underlying approach under review" | OPEN QUESTION §6 |
| Doctrine viewer | active | — | — |
| Settings | active | — | — |
| GSG viewer (/gsg) | active mais mal placé | "Not the studio" | Refonte F5 |
| GSG handoff (wizard) | active mais fragile | "output_path race, no validation post-completion" | Refonte F2/F3/F4 |
| Reality (Meta/Google/GA4/TikTok/Shopify/Clarity) | ready_to_configure | "OAuth credentials missing" | UX design only (Mathis decision deferred) |
| GEO | ready_to_configure | "OPENAI + PERPLEXITY keys missing" | UX design only |
| Scent | no_data | "Cross-channel captures deferred" | UX honest empty state |
| Experiments | experimental | "Dispatcher = print(not implemented)" | Decision G4: implement or archive |
| audit-gads | archived | "Disabled CTA, post-MVP" | Hide from nav |
| audit-meta | archived | "Disabled CTA, post-MVP" | Hide from nav |
| screenshots table | archived | "Never written or read" | Drop migration / unused |

L'UI doit **toujours afficher** ce statut. Aujourd'hui elle ne le fait pas.

---

## 5. Docs contradictions critiques

### 5.1 webapp/README.md ↔ D1.A

| Doc | Disait |
|---|---|
| `webapp/README.md` (avant 2026-05-17) | "5 microfrontends: shell:3000, audit-app:3001, reco-app:3002, gsg-studio:3003, reality-monitor:3004" |
| `MICROFRONTENDS_DECISION_2026-05-14.md` (D1.A locked) | "Single Next.js 14 App Router. No microfrontends.json. All product surfaces are routes inside the shell." |
| `README.md` racine | "single shell D1.A verrouillé (2026-05-14)" |

→ **`webapp/README.md` corrigé par J0.1 dans le même PR/commit** que ce dossier d'audit.

### 5.2 Epics master concurrentes

| Epic | Status |
|---|---|
| `webapp-stratosphere` | "completed" 100% (May 11) |
| `webapp-stratospheric-reconstruction-2026-05` | "closed" (May 13) — supersede l'autre ? |

→ Hiérarchie unclear. À clarifier (J0.2).

### 5.3 Epics GSG orphelines (sans GitHub mapping)

- `gsg-beyond-excellent-2026-05`
- `gsg-push-to-stratospheric-2026-05`
- `gsg-quality-completeness-2026-05`
- `gsg-stratospheric-final-polish-2026-05`

→ À archiver ou mapper formellement (J0.2).

### 5.4 Cascade CONTINUATION_PLAN

4+ versions du 15→17 mai créent confusion. CLAUDE.md step #12 pointe le plus récent (`2026-05-17_POST_WAVE_1_5_RENAISSANCE`), mais les autres ne sont pas marqués "superseded".

→ Consolider (J0.3).

---

## 6. OPEN QUESTIONS stratégiques

### Q1 — Reality Layer (Meta/Google/TikTok/GA4/Shopify/Clarity) : on déploie quand ?

Position Mathis 2026-05-17 : *"on peut préparer l'architecture le workflow l'UI UX mais c'est tout, on y est pas encore du tout"*.

Décision PRD : Phase G1 = **UX/architecture preparation only**. Backend wiring (OAuth completion, polling reliability, error recovery, observability) deferred jusqu'à signal explicite Mathis basé sur :
- coût (provider costs ad APIs)
- value (uplift mesurable client par client)
- risk (token rotation, data privacy)

### Q2 — Learning Layer : c'est la bonne approche ?

Position Mathis 2026-05-17 : *"j'aimerai questionner son intérêt.. est-ce que c'est la meilleure façon pour l'IA et l'app sur vercel d'apprendre en continu et de se nourrir intelligemment.. pas sur !"*

État actuel : `data/learning/audit_based_proposals/` contient 69 propositions V29 + V30. Pattern : LLM génère proposal à partir d'audit failure → Mathis vote (accept/reject/refine/defer) → Bayesian update doctrine V3.2.1.

**Alternatives à explorer** (research spike Phase G3 avant tout UI build) :

1. **Static doctrine + LLM-as-judge** — doctrine V3.2.1 frozen. Juger chaque LP avec LLM + few-shot examples curated par Mathis (en Notion ou en JSON repo). Simple, pas de Bayesian, pas de queue.
2. **RAG outcome-driven** — au scoring, retrieve pages similaires + leurs résultats A/B mesurés. Doctrine = anchor + evidence retrouvée.
3. **Skills evolutifs** — encoder les patterns appris comme skills Claude Code (`.md` per pattern). Version-controlled, lisibles, partageables.
4. **Memory files** — pattern Claude Code memory : snippets Mathis-validated injectés en contexte sur certains scoring.
5. **Status quo amélioré** — garder pattern Bayesian mais améliorer UX (queue tri, filtres, batch review).

**Critère de décision** : laquelle des 5 approches **scale avec 100 clients × N pages × M experiments** sans devenir une dette de maintenance ?

Phase G3 issue = **research spike** qui produit un doc decision `LEARNING_LAYER_APPROACH_DECISION.md`. Build UI seulement après tranche.

### Q3 — Experiments : implement or archive ?

Dispatcher `experiment` = noop. Table créée. UI a une calculator sample size. Mais aucun A/B effectivement runé.

Options :
- (a) implement dispatcher correctement (run A/B contre Reality Layer ou outil tiers type GrowthBook)
- (b) archive le type, retirer table, retirer route (déclarer hors-scope V28)
- (c) garder calculator standalone, retirer dispatcher

→ Décision Phase G4 (issue type "decision spike").

---

## 7. Implications pour la refonte

### Ce qu'on garde tel quel
- Architecture Next.js single shell + Supabase EU + worker daemon polling
- Doctrine V3.2.1 (V3.3 reste P1 séparé)
- Tous les moteurs Python (Audit, Reco, GSG, multi-judge, Reality, GEO)
- Brand DNA + AURA + Opportunity Layer + Gates (ClaimsSourceGate, VerdictGate)
- PRESERVE_CREATIVE_LATITUDE constant dans Elite Mode

### Ce qu'on reconstruit
- **Information architecture** : 5 espaces (Command Center, Clients, Audits & Recos, GSG Studio, Advanced Intelligence) au lieu de 20 routes plates
- **Navigation** : sidebar uniforme workflow-first
- **Home Command Center** : 4 zones max au lieu d'un mur
- **GSG Studio E2E** : `/gsg/studio` = vrai studio, `/gsg/runs` history, `/gsg/design-grammar/[client]` viewer
- **Client workspace** : progressive disclosure
- **Audit/Reco workspace** : capture → score → recos orchestrés (chainage automatique via nouveau worker handler `audit_full`)
- **Worker liveness** : table `system_health`, heartbeat, badge global UI
- **Edit/save global pattern** : `useEdit` hook, save explicit, lifecycle pill séparé
- **Module Maturity Model** : 6 statuts affichés honnêtement
- **Design system productif** : calm premium, density, no card-in-card, primitives canoniques
- **Quick wins docs** : webapp/README fix, epic hierarchy clarification, CONTINUATION_PLAN consolidation

### Ce qu'on défère
- Reality Layer backend wiring (Mathis decision pending — coût/value)
- Learning Layer architecture decision (research spike avant tout build)
- Experiments dispatcher (implement vs archive — decision spike)
- audit-gads / audit-meta routes (cachées de la nav jusqu'à form UI + skill wiring)

---

## 8. Sources

- 4 audits parallèles read-only Claude Code 2026-05-17 (routes/UI, backend/data, docs contradictions, workflows E2E)
- Codex audit produit (transmis par Mathis 2026-05-17)
- `webapp/apps/shell/**` source code
- `growthcro/worker/dispatcher.py`, `daemon.py`
- `supabase/migrations/**`
- `.claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md`
- `.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md`
- `.claude/docs/state/CONTINUATION_PLAN_2026-05-17_POST_WAVE_1_5_RENAISSANCE.md`

---

**Document créé 2026-05-17. Source de vérité primaire pour le PRD [`webapp-product-ux-reconstruction-2026-05`](../../prds/webapp-product-ux-reconstruction-2026-05.md). Mise à jour : à chaque clôture de phase, ajouter une section "Post-Phase X delta" listant ce qui a changé.**
