# Module Maturity Model — 2026-05

> Document canonique du Module Maturity Model GrowthCRO Webapp. Source de vérité pour B2 (canonical states components : `<ModuleHeader>`, `<BlockedState>`, `<WorkerOfflineState>`, `<EmptyState>`, `<ModuleMaturityBadge>`), G1/G2/G3/G4 (Advanced Intelligence honest), et tous loaders Server Component qui veulent afficher un statut honnête.
>
> Issue [#68](https://github.com/GrowthSociety-GS/growth-cro/issues/68) (A3). Ancre le PRD [`webapp-product-ux-reconstruction-2026-05`](../../prds/webapp-product-ux-reconstruction-2026-05.md) §FR-5.
>
> Étend [`WEBAPP_PRODUCT_AUDIT_2026-05-17.md`](WEBAPP_PRODUCT_AUDIT_2026-05-17.md) §4 (proposition initiale) en raffinant la sémantique, la matrix exhaustive, le contract TypeScript, et les règles d'affichage. Pure documentation + 1 fichier interface TS — aucune modification de code applicatif.

**Auteur** : Claude Code (Opus 4.7 1M-ctx).
**Date** : 2026-05-17.
**Périmètre** : `webapp/apps/shell/app/**` (25 routes utilisateur), `webapp/apps/shell/lib/**` (loaders existants), `growthcro/worker/dispatcher.py`, `supabase/migrations/**`.

---

## 0. Pourquoi un Module Maturity Model

L'audit produit 2026-05-17 a révélé un mode d'échec systématique de l'UX : **plusieurs modules avancés (Reality, GEO, Scent, Experiments, AURA, Learning) affichent un skeleton "0/N configured" ou un empty state "Aucun X" sans distinguer plusieurs causes radicalement différentes** :

1. *Le code n'est pas wiré* (donc rien à attendre).
2. *Les credentials manquent* (OAuth pas connecté, env vars manquants).
3. *Le pipeline n'a jamais run* (mais tout est prêt).
4. *Une dépendance runtime est down* (worker daemon offline, migration KO).
5. *Le module n'a aucun effet réel* (schéma DB existe, dispatcher noop).
6. *Le module est en voie d'archivage* (legacy, dead code, route cachée).

Aujourd'hui un utilisateur ne sait pas s'il regarde un module **cassé**, un module **en attente d'activation**, ou un module **désaffecté**. Conséquence : perte de confiance produit, support burden, fake-feature accusation.

**Solution** : 6 statuts canoniques affichés honnêtement via un contract TypeScript unique (`Maturity`), consommé par chaque loader Server Component et matérialisé par un `<ModuleHeader>` standardisé. Plus de skeleton ambigu.

**Principe directeur** : *aucune fake data, aucune fake interactivity*. Si un module ne marche pas, il dit pourquoi et ce que l'utilisateur peut faire — ou pas.

---

## 1. Définition des 6 statuts

### 1.1 `active`

**Sémantique** : E2E fonctionnel. Backend wiré + frontend wiré + dépendances runtime OK + runs en succès récents (≤7j).

**Quand l'utiliser** : tout le pipeline fonctionne réellement. L'utilisateur peut interagir et obtenir un effet observable.

**Affichage** : pas de badge spécial par défaut (silence = succès). Si l'on souhaite signaler explicitement, badge vert sobre "Active" — utile dans une fleet view pour distinguer modules opérables.

**Règle d'or** : ne JAMAIS marquer `active` si le worker handler associé est noop ou si la dernière run effective date de >30j (auquel cas → `no_data` ou `blocked`).

**Exemples actuels** (cf. §4 matrix) :
- Audit capture/score/recos (worker handlers E2E)
- Recos editor (PATCH `/api/recos/[id]`)
- Doctrine viewer (`/doctrine`, stateless)
- Settings (`/settings`, 4 tabs role-gated)
- Learning vote queue (UI E2E ; approche fondamentale en research spike G3 — voir §1.5 note)

### 1.2 `ready_to_configure`

**Sémantique** : Worker prêt, code applicatif wiré, mais **credentials / env vars / OAuth manquants** côté config. Le module ne peut pas tourner tant que l'utilisateur n'a pas fourni la pièce manquante.

**Quand l'utiliser** :
- OAuth provider attend un Connect (Catchr, Meta Ads, Google Ads, Shopify, Clarity).
- API key absente (`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`).
- Compte/tenant ID nécessaire côté config (ex: GA4 measurement ID).

**Affichage** : badge orange "À configurer" + CTA explicit `next_step` ("Connect Catchr", "Set OPENAI_API_KEY"). Le module est lisible (skeleton non vide ; on peut décrire ce qui va arriver) mais inactif.

**RÈGLE D'OR** : **AUCUNE fake data, AUCUNE fake interactivity.** Pas de chiffres fictifs, pas de graphes en pointillés mensongers, pas de bouton "Run" qui ne fait rien. Le module montre exactement ce qu'il faut faire pour l'activer.

**Exemples actuels** :
- Reality connectors (Catchr, Meta Ads, Google Ads, Shopify, Clarity).
- Reality connectors mentionnés Mathis 2026-05-17 mais non encore wirés backend (GA4, TikTok) — même statut + reason "Not implemented yet".
- GEO engines OpenAI et Perplexity (clés manquantes).
- AURA pipeline V2 sur `/clients/[slug]?tab=brand-dna` (bouton "Run AURA" disabled aujourd'hui).

### 1.3 `no_data`

**Sémantique** : Worker prêt, credentials OK, code wiré, **mais aucun run encore exécuté**. État transitoire normal d'un module qui vient d'être activé OU pipeline batch non encore lancé.

**Quand l'utiliser** :
- Module fraîchement configuré : tout est OK mais l'utilisateur n'a pas encore lancé son premier run.
- Pipeline cross-channel pas batché en prod (Scent : code disponible, mais pas de captures batch en agence).
- Premier poll post-OAuth pas encore arrivé (Reality post-Connect en attente du prochain cron).

**Affichage** : empty state explicite "Aucun run encore — lancez votre premier <action>" + CTA action principale. Le badge `no_data` est gris/sobre — c'est un état neutre, pas une erreur.

**Différence avec `ready_to_configure`** : `ready_to_configure` = il manque une config user ; `no_data` = tout est configuré mais rien n'a tourné. Ces deux statuts sont **disjoints**.

**Exemples actuels** :
- Scent (`/scent`) : code lit `data/captures/<client>/scent_trail.json` mais pipeline cross-channel pas batch-run en agence.
- Reality post-OAuth si premier poll pas encore reçu.
- Tout module fraîchement débloqué entre première activation et premier run.

### 1.4 `blocked`

**Sémantique** : Dépendance critique runtime manquante. Pas un statut config-time (= `ready_to_configure`), un statut **runtime**.

**Quand l'utiliser** :
- Worker daemon offline depuis >5min (heartbeat lapsed — FR-3/FR-4).
- Table Supabase critique inexistante (migration KO ou drop accidentel).
- API tierce en outage prolongée (≥5min consecutive failures).
- Module dépend d'un autre module en panne (cascade — rare, à éviter).

**Affichage** : badge rouge "Bloqué" + explication détaillée + lien debug (vers logs ou doc remediation). C'est le SEUL statut où l'on doit utiliser un ton "alerte" rouge.

**Distinction critique** : un module en `blocked` est temporairement KO, pas désaffecté. Si la dépendance revient, le statut redevient `active` automatiquement à la prochaine refresh du loader.

**Exemples potentiels** :
- N'importe quel module qui dépend du worker, **si le worker daemon est offline >5min**. Le badge global topbar B3 (`/api/worker/health`) expose cette information centralement.
- Reality si table `reality_snapshots` inexistante (migration regressed).
- GEO si table `geo_audits` inexistante.

### 1.5 `experimental`

**Sémantique** : Schéma DB + code stub présents, **pas d'effet réel** côté prod. C'est le statut explicite "tu peux voir l'UI mais cliquer ne fait rien".

**Quand l'utiliser** :
- Table relationnelle créée mais zéro mutation prod (`experiments`).
- Worker dispatcher = `print("not implemented")` (cf. `growthcro/worker/dispatcher.py:46`).
- Feature flag off + UI build derrière le flag.
- UI prototype en cours d'évaluation produit (decision spike pending).

**Affichage** : badge violet/gold "Expérimental" + warning explicite "Cette feature n'a pas d'effet réel — voir [decision spike X]". Sur-communication >> sous-communication ici, parce que l'utilisateur risque de penser "c'est cassé".

**Politique** : un module en `experimental` ne doit JAMAIS persister >2 sprints sans **decision spike** tranché. Soit on l'implémente (→ `ready_to_configure` ou `active`), soit on l'archive (→ `archived`).

**Exemples actuels** :
- Experiments (`/experiments`) : table créée, UI lit la table, mais dispatcher noop → run "completed" sans effet. Decision spike G4 pending (FR-19).

### 1.6 `archived`

**Sémantique** : Code / route à retirer. Maintenu temporairement pour backward compat ou en attente de cleanup formel.

**Quand l'utiliser** :
- Route obsolète (`/funnel/[clientSlug]` — décision Mathis A1 §11.1 SUPPRIMER).
- Composant legacy remplacé (`CommandCenterTopbar` → `StickyHeader`).
- Route fonctionnelle mais retirée de la nav (post-MVP, en attente skill wiring : `/audit-gads`, `/audit-meta`).
- Vue agrégée retirée au profit d'une vue intégrée (vue cross-client `/recos` → tab `?tab=recos`).

**Affichage** :
- Si l'URL reste accessible directement (cas `/audit-gads`, `/audit-meta`) : bandeau gris en tête "Cette page est archivée — voir [alternative]" + badge "Archived".
- Si la route est retirée : 410 Gone OU redirect 301 vers la cible canonique (voir §5 transitions).

**Politique** : un module en `archived` doit avoir une **deadline de suppression** (next phase D/E/F/J cleanup). Le statut n'est PAS un état long-terme.

**Exemples actuels** :
- `/audit-gads` (caché de nav FR-25, URL toujours accessible).
- `/audit-meta` (caché de nav FR-25).
- `/funnel/[clientSlug]` (SUPPRIMER décision Mathis A1 §11.1).
- `/recos` cross-client (FUSIONNER en tab — décision Mathis A1 §11.3).
- `/recos/[clientSlug]` (FUSIONNER en tab).
- `CommandCenterTopbar` (B1 cleanup).
- `ViewToolbar` + `Breadcrumbs` shim (B1 cleanup).

---

## 2. Contract TypeScript

Source de vérité : `webapp/apps/shell/lib/maturity.ts` (interface only, créé en même temps que ce doc).

```ts
// apps/shell/lib/maturity.ts — INTERFACE ONLY (A3 scope, no logic, no wire).

export type MaturityStatus =
  | "active"
  | "ready_to_configure"
  | "no_data"
  | "blocked"
  | "experimental"
  | "archived";

export interface Maturity {
  status: MaturityStatus;
  reason?: string;
  next_step?: {
    label: string;
    href: string;
  };
  last_updated?: string;
  blocking_dependency?:
    | "worker_daemon"
    | "supabase_migration"
    | "external_api"
    | "credentials"
    | "data_pipeline";
}

export const MATURITY_LABELS: Record<MaturityStatus, string> = {
  active: "Active",
  ready_to_configure: "À configurer",
  no_data: "Aucun run",
  blocked: "Bloqué",
  experimental: "Expérimental",
  archived: "Archivé",
};

export const MATURITY_COLORS: Record<MaturityStatus, string> = {
  active: "var(--gc-success, #2dd4bf)",
  ready_to_configure: "var(--gc-warning, #f59e0b)",
  no_data: "var(--gc-muted, #94a3b8)",
  blocked: "var(--gc-error, #ef4444)",
  experimental: "var(--gc-info, #a855f7)",
  archived: "var(--gc-archive, #6b7280)",
};

export const MATURITY_PILL_TONE: Record<MaturityStatus, /* tones */> = {
  active: "green",
  ready_to_configure: "amber",
  no_data: "soft",
  blocked: "red",
  experimental: "gold",
  archived: "soft",
};
```

**Décisions de design** :

1. **`reason` optional** au niveau type, mais **obligatoire par convention** pour `ready_to_configure` / `blocked` / `experimental` / `archived` (cf. §3 règles d'affichage). On ne hard-fail pas via type pour rester souple aux loaders progressifs ; B2 lint runtime peut renforcer.
2. **`next_step` optional** mais **mandatory** pour `ready_to_configure` (sinon comment l'utilisateur agit ?) et **strongly recommended** pour `archived` (où aller maintenant ?).
3. **`blocking_dependency` enum fermé** — évite la créativité au runtime. 5 valeurs canoniques couvrent les cas observés. À étendre prudemment si nouveau cas réel apparaît.
4. **`last_updated` ISO** — utile pour distinguer un statut frais vs un statut cached. Phase B2 affichera "Mis à jour il y a Xmin" sur le ModuleHeader.
5. **Pas de transition automatique** dans ce module. Les transitions sont décrites en §5 et calculées par chaque loader.

---

## 3. Règles d'affichage par status

Pour chaque status, ce que l'UI **doit** afficher et **ne doit jamais** afficher.

### 3.1 `active`

**MUST** :
- Présentation normale : data réelle, charts vivants, CTAs actifs.
- Optionnel : badge vert sobre "Active" (à activer dans fleet views).

**NEVER** :
- Marquer `active` si le dernier run effectif date de >30j → utiliser `no_data` ou `blocked`.
- Marquer `active` si le worker handler est noop → utiliser `experimental`.

### 3.2 `ready_to_configure`

**MUST** :
- Badge orange "À configurer".
- `reason` court et précis ("OAuth Catchr non configuré", "OPENAI_API_KEY manquante").
- `next_step` CTA visible et explicit ("Connecter Catchr", "Définir la clé API").
- Skeleton non interactif (= visuellement clair que les valeurs montrées sont des labels, pas des chiffres).

**NEVER** :
- Pas de graphes avec données fictives, même en gris.
- Pas de boutons "Run" actifs (le run échouera côté worker ou silently noop).
- Pas de chiffres dans des KpiCards (utiliser "—" partout).
- Pas de "Coming soon" vague — toujours dire **ce qui** manque et **où** le configurer.

### 3.3 `no_data`

**MUST** :
- Empty state explicite : "Aucun run encore — lancez votre premier <action>".
- CTA action principale (`<TriggerRunButton>` ou équivalent) visible et fonctionnel.
- Badge sobre "Aucun run".

**NEVER** :
- Pas de message ambigu ("En attente…") sans préciser de quoi.
- Pas de skeleton vide infini — toujours surfaces une action.

### 3.4 `blocked`

**MUST** :
- Badge rouge "Bloqué".
- `reason` détaillé avec timestamp si possible ("Worker daemon offline depuis 12:34 UTC").
- `next_step` avec URL debug / docs / link logs.
- `blocking_dependency` explicit pour télémétrie (cf. §7).

**NEVER** :
- Pas d'auto-retry silencieux côté UI (l'utilisateur doit voir la panne).
- Pas de masquage : un module bloqué ne disparaît PAS de la nav, son statut est rouge dans la sidebar.
- Pas de fake data pendant le blocage (mieux vaut empty state explicite).

### 3.5 `experimental`

**MUST** :
- Badge violet/gold "Expérimental".
- Banner inline visible ("Cette feature n'a pas d'effet réel — decision spike pending").
- `reason` lien vers le decision spike (G3/G4 issues GitHub).
- Si UI inclut des mutations, ces mutations doivent être **désactivées** OU réellement implémentées (pas de mensonge UX).

**NEVER** :
- Pas de promesse implicite que la feature fonctionne.
- Pas de A/B test live en arrière-plan (rappel : un module `experimental` n'a aucun effet réel par définition).

### 3.6 `archived`

**MUST** :
- Si URL accessible : bandeau gris en tête "Cette page est archivée" + lien vers alternative.
- Si URL retirée : redirect 301 vers cible canonique OU 410 Gone (si pas de cible).
- Retrait de la nav (`lib/cmdk-items.ts`).

**NEVER** :
- Pas de redirect silencieux sans bandeau (l'utilisateur doit comprendre le changement).
- Pas de garder un module `archived` >2 sprints sans suppression formelle.

---

## 4. Matrix initiale module-par-module

Source : audit Phase A signed-off (cf. `WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md` §11) + lecture code 2026-05-17 (worker dispatcher, loaders, migrations).

Décisions Mathis A1 §11 intégrées : `/funnel` → archived (SUPPRIMER), `/audits` landing → active (GARDER picker), `/recos` cross-client → archived (FUSIONNER en tab), `experiments` → experimental (G4 decision spike), `screenshots` = bucket Storage actif **hors matrix** (c'est un bucket, pas un module produit).

### 4.1 Audit pipeline

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| Audit capture (worker `capture`) | active | — | — | E2E `growthcro.capture.cli`. Dispatcher line 37. |
| Audit score (worker `score`) | active | "Capture → score → recos pas chained (FR-9 pending)" | "Wait E1 `audit_full` handler" | E2E mais 3 POST manuels côté UI |
| Audit recos enrich (worker `recos`) | active | idem (chainage manquant) | idem | E2E `growthcro.recos.cli enrich` |
| `/audits` landing (picker) | active | — | — | Décision Mathis A1 §11.2 : GARDER |
| `/audits/[clientSlug]` (per-client list) | active | — | — | Pattern groupage par page_type solide |
| `/audits/[clientSlug]/[auditId]` (drill-down) | active | — | — | Pattern E2E excellent |
| `/audits/[clientSlug]/[auditId]/judges` (multi-judge) | active | — | — | Empty state honnête déjà présent |

### 4.2 Recos

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| Recos editor (PATCH `/api/recos/[id]`) | active | "Two-endpoint pattern (`/api/recos/[id]` + `/api/recos/[id]/lifecycle`) à unifier — FR-13/FR-14" | "Wait E2" | Fonctionne ; pattern global `useEdit` pending |
| Recos lifecycle (PATCH `/api/recos/[id]/lifecycle`) | active | idem | idem | — |
| `/recos` (cross-client agg) | archived | "Décision Mathis A1 §11.3 — FUSIONNER en tab `/clients/[slug]?tab=recos`. Drop vue cross-fleet." | "Redirect 301 `/recos` → `/clients`" | À traiter D/E |
| `/recos/[clientSlug]` | archived | "Idem §11.3 — FUSIONNER en tab" | "Redirect 301 `/recos/[c]` → `/clients/[c]?tab=recos`" | idem |

### 4.3 Clients & Brand DNA

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/clients` (fleet list) | active | — | — | Pattern URL state propre |
| `/clients/[slug]` (workspace) | active | "Densité à rebalancer — D1 progressive disclosure" | "Wait D1" | Workspace canonical cible |
| `/clients/[slug]/dna` (Brand DNA viewer) | active | "À fusionner en tab `?tab=brand-dna` — D1" | "Wait D1" | Viewer V29 solide |
| AURA pipeline V2 (bouton "Run AURA pipeline") | ready_to_configure | "Pipeline V2 jamais run pour ce client (artefact `_pipeline_runs/aura/...` absent)" | "Wait AURA backend wire (deferred V2)" | Bouton aujourd'hui disabled (`clients/[slug]/dna/page.tsx:312`) |

### 4.4 GSG

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/gsg` (Design Grammar viewer) | active | "Mal placé — pas le Studio. Refonte F5 RENOMMER en `/gsg/design-grammar/[client]`" | "Wait F5" | Viewer V30 solide, label "GSG Studio" trompeur |
| `/gsg/handoff` (Brief Wizard) | active | "Wizard fragile : output_path race + UUID paste seam — refonte F2/F3/F4" | "Wait F2/F3/F4" | Pattern brief wizard OK, plumbing en refonte |
| `/gsg/studio` (cible F-phase) | n/a | "Pas encore créée" | "Wait F2" | Future canonical Studio |
| `/gsg/runs/[id]` (cible F-phase) | n/a | "Pas encore créée" | "Wait F2/F3" | Future preview page |
| GSG worker handler (`moteur_gsg.orchestrator`) | active | — | — | E2E ; payload complet wizard → CLI |
| Multi-judge worker (`moteur_multi_judge.orchestrator`) | active | — | — | Dispatcher line 41 |

### 4.5 Learning

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/learning` (vote queue + lifecycle bars) | active | "Underlying Bayesian approach under review — see G3 research spike `LEARNING_LAYER_APPROACH_DECISION.md`" | "View G3 spike doc when shipped" | UI fonctionnel + sidecar `<id>.review.json` ; **NE PAS REFONDRE UI avant spike** |
| `/learning/[proposalId]` | active | idem (bloqué par G3 spike pour évolution) | idem | Detail + form vote E2E |
| Learning sidecar persistence (POST `/api/learning/proposals/review`) | active | — | — | Écrit `<id>.review.json` |

**Question ouverte Mathis** (cf. §8 sign-off) : doit-on plutôt marquer Learning en `experimental` pendant que la spike G3 est en cours ? Argument *pour* : honnête côté utilisateur ("approche fondamentale en évaluation"). Argument *contre* : la vote queue fonctionne et capture des données réelles utilisées en doctrine update — c'est du `active` avec une note. **Proposition par défaut : `active` + note**. À confirmer.

### 4.6 Doctrine & Settings

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/doctrine` (V3.2.1 viewer pédagogique) | active | — | — | Stateless reference, hardcoded PILIERS |
| `/settings` (4 tabs role-gated) | active | — | — | E2E fonctionnel |

### 4.7 Reality Layer (Advanced Intelligence — espace 5)

Backend wiring deferred (cf. PRD §6 Q1 + Constraints §Reality). UX/architecture/maturity only.

| Sub-module / connector | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/reality` (fleet root) | ready_to_configure | "5 OAuth connectors not configured (Catchr, Meta Ads, Google Ads, Shopify, Clarity). Heat map vide sans data." | "Configure at least one connector below" | `<ModuleHeader status="ready_to_configure">` (G1) |
| `/reality/[clientSlug]` (per-client) | ready_to_configure | idem | idem | CredentialsGateGrid déjà rendu skeleton honnête |
| Reality connector — Catchr | ready_to_configure | "OAuth Catchr non configuré" | "Connect Catchr" → `/api/auth/catchr/start` | Callback route déjà LIVE |
| Reality connector — Meta Ads | ready_to_configure | "OAuth Meta Ads non configuré" | "Connect Meta Ads" → `/api/auth/meta-ads/start` | idem |
| Reality connector — Google Ads | ready_to_configure | "OAuth Google Ads non configuré" | "Connect Google Ads" → `/api/auth/google-ads/start` | idem |
| Reality connector — Shopify | ready_to_configure | "OAuth Shopify non configuré" | "Connect Shopify" → `/api/auth/shopify/start` | idem |
| Reality connector — Clarity | ready_to_configure | "OAuth Microsoft Clarity non configuré" | "Connect Clarity" → `/api/auth/clarity/start` | idem |
| Reality connector — GA4 | ready_to_configure | "Not implemented yet (mentionné par Mathis 2026-05-17 — backend wire deferred)" | "Wait backend wire G1+" | **À inclure visuellement mais marquer 'Not implemented yet'** |
| Reality connector — TikTok | ready_to_configure | "Not implemented yet (mentionné par Mathis 2026-05-17 — backend wire deferred)" | "Wait backend wire G1+" | idem GA4 |
| Reality worker (`reality.poller`) | active | "Backend E2E mais sans creds aucun poll ne réussit" | — | Dispatcher line 42 fonctionnel |
| `/api/cron/reality-poll` | ready_to_configure | "External Vercel cron config requise" | "Configure Vercel cron job" | Untested |

**Question ouverte Mathis** (cf. §8 sign-off) : inclure GA4 + TikTok dans la matrix initiale en `ready_to_configure` "Not implemented yet" est-il préférable à les omettre jusqu'à wire backend réel ? Argument *pour* l'inclusion : roadmap visible côté Mathis 2026-05-17. Argument *contre* : sur-promet quelque chose qui n'a pas de code wired. **Proposition par défaut : inclure avec reason explicit "Not implemented yet" + next_step "Wait backend wire G1+"**. À confirmer.

### 4.8 GEO Layer (Advanced Intelligence)

| Sub-module / engine | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/geo` (fleet root) | ready_to_configure | "OpenAI + Perplexity keys missing ; Anthropic active sur 4/56 clients" | "Configure missing engine keys" | `<ModuleHeader>` G2 |
| `/geo/[clientSlug]` (per-client drilldown) | ready_to_configure | idem | idem | — |
| GEO engine — Anthropic (Claude) | active | "Active sur 4/56 clients" | — | `ANTHROPIC_API_KEY` provisionnée |
| GEO engine — OpenAI (ChatGPT) | ready_to_configure | "OPENAI_API_KEY manquante" | "Set OPENAI_API_KEY in env" | — |
| GEO engine — Perplexity | ready_to_configure | "PERPLEXITY_API_KEY manquante" | "Set PERPLEXITY_API_KEY in env" | — |
| GEO worker (`growthcro.geo`) | active | "Anthropic-only en pratique" | — | Dispatcher line 43 |

### 4.9 Scent (Advanced Intelligence)

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/scent` (fleet trail) | no_data | "Pipeline cross-channel pas batch-run en agence — `scent_trail.json` absent sur 95% des installs" | "Configure batch captures runs (deferred — pas de prio backend planifiée)" | Empty state honnête déjà présent |

### 4.10 Experiments (Advanced Intelligence)

| Sub-module / route | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/experiments` (UI page) | experimental | "Worker dispatcher = `print('experiment dispatcher not implemented')` (dispatcher.py:46). Table `experiments` créée + lue par UI (`lib/experiments-data.ts:47`) mais zéro mutation prod. G4 decision spike pending." | "Wait G4 decision: implement OR archive" | Calculator + Ramp-up Matrix = client-side OK, dispatcher = mensonge UX |
| Experiments worker handler | experimental | idem | idem | Dispatcher mark "completed" sans rien faire |
| Supabase table `experiments` | experimental | idem (migration 20260514_0021 créée, lue, jamais writée) | "Wait G4" | RLS policies définies |

### 4.11 Routes archivées / dead UI

| Route / composant | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| `/audit-gads` | archived | "CTA disabled post-MVP — caché de nav FR-25" | "Wait form UI + skill wiring (post-MVP)" | URL accessible directement |
| `/audit-meta` | archived | "Idem `/audit-gads` — caché de nav FR-25" | "Wait form UI + skill wiring" | idem |
| `/funnel/[slug]` | archived | "Décision Mathis A1 §11.1 — SUPPRIMER (pas de capture funnel pipeline, source data fragile `brand_dna_json.funnel` hors schema)" | "Delete file en phase D ou J1 cleanup" | Drop link source `clients/[slug]/page.tsx:80` |
| `components/command-center/CommandCenterTopbar.tsx` | archived | "Replaced by StickyHeader — legacy coexistant `app/page.tsx:224`" | "Delete in B1 cleanup" | Commentaire `page.tsx:218` admet "legacy still in place" |
| `components/ViewToolbar.tsx` | archived | "Single-caller `/doctrine`, redundant avec `gc-topbar` pattern inline" | "Refactor `/doctrine` inline + delete in B1" | — |
| `components/Breadcrumbs.tsx` (shim) | archived | "Deprecated shim re-export DynamicBreadcrumbs (10 LOC), single-caller ViewToolbar" | "Delete post ViewToolbar cleanup B1" | — |
| Input "Subscribe to a run UUID manually (smoke test)" `HandoffBriefSection.tsx:75-100` | archived | "Seam de dev exposé en prod" | "Delete in F2 refonte Studio" | Wizard submit → redirect direct au lieu de paste UUID |
| Link "Open V26 archive" `CommandCenterTopbar.tsx:17` | archived | "Pointe vers HTML statique pré-launch sans valeur produit" | "Drop avec CommandCenterTopbar" | — |

### 4.12 Worker daemon liveness (transverse)

| Sub-module | Status | Reason | Next step | Notes |
|---|---|---|---|---|
| Worker daemon `/api/worker/health` | active OR blocked (computed runtime) | "Heartbeat lapsed >5min ⇒ blocked" | "Restart `growthcro/worker/daemon.py` OR check logs" | À créer B3 (FR-3/FR-4) — table `system_health` + endpoint |

Note : le worker daemon est une dépendance transverse, pas un module produit en soi. Son statut bascule entre `active` (heartbeat <60s) et `blocked` (>5min). Il propage `blocked` vers tous les modules qui en dépendent (Reality, GEO, GSG, Audit, multi-judge) **uniquement si une run effective est en pending depuis >5min** — pas par défaut (sinon tout l'app rougit dès qu'aucune run n'est en file). Cette logique de cascade reste de la responsabilité de chaque loader.

---

## 5. Process de transition status → status

Pour éviter du flicker UI, chaque transition doit être **idempotente** côté loader (= un refresh page recalcule le statut sans état persistant).

### Transitions canoniques

| De | Vers | Déclencheur | Côté |
|---|---|---|---|
| `ready_to_configure` | `no_data` | OAuth callback success OR env var détectée OR token valide en base | Loader détecte creds présentes |
| `no_data` | `active` | Premier run effectif terminé en succès (`runs.status = 'completed'` + artefact produit) | Loader détecte ≥1 run récent |
| `active` | `no_data` | Aucune run effective depuis >30j (module idle, pas idéal mais honnête) | Loader date-based (rare) |
| `active` | `blocked` | Worker heartbeat lapsed >5min ET run pending >5min sur ce module | Loader + `/api/worker/health` |
| `blocked` | `active` | Worker heartbeat reprise + dernière run resucceedée | Auto au prochain refresh |
| `experimental` | `ready_to_configure` | Decision spike → implement (worker handler wiré, mais creds peuvent encore manquer) | Issue G4 closed avec décision "implement" |
| `experimental` | `archived` | Decision spike → archive | Issue G4 closed avec décision "archive" |
| `*` | `archived` | Décision produit Mathis explicit (cf. A1 §11) | Manuel, sprint cleanup |
| `archived` | (delete) | Suppression effective code + route + migrations associées | Phase J cleanup ou follow-up issue |

### Hors transitions

- Pas de transition automatique entre `ready_to_configure` et `blocked`. Si la creds manque, c'est `ready_to_configure` (config-time). Si la creds est OK mais le service tiers est down, c'est `blocked` (runtime).
- Pas de transition entre `archived` et `active`. Re-activer un module archived = créer une nouvelle route avec un nouveau statut.

### Calcul du status par un loader (pattern type)

```ts
// Pattern simplifié à wirer en G1/G2/G3/G4 (PAS dans A3 scope) :
async function loadModuleMaturity(client: Client): Promise<Maturity> {
  // 1. Check creds present ?
  if (!hasCredsForConnector(client, "catchr")) {
    return {
      status: "ready_to_configure",
      reason: "OAuth Catchr non configuré",
      next_step: { label: "Connecter Catchr", href: oauthStartHref("catchr", client.id) },
      blocking_dependency: "credentials",
    };
  }
  // 2. Check at least one effective run ?
  const lastRun = await getLastSuccessfulRun(client.id, "reality");
  if (!lastRun) {
    return {
      status: "no_data",
      reason: "Aucun snapshot encore",
      next_step: { label: "Lancer le premier poll", href: triggerRunHref("reality", client.slug) },
    };
  }
  // 3. Check worker health ?
  const workerHealth = await fetchWorkerHealth();
  if (workerHealth.lapsed && pendingRunCountForModule(client.id, "reality") > 0) {
    return {
      status: "blocked",
      reason: `Worker daemon offline (heartbeat ${workerHealth.lastSeenAt})`,
      next_step: { label: "Voir logs worker", href: "/settings#worker" },
      blocking_dependency: "worker_daemon",
    };
  }
  // 4. Default : active.
  return { status: "active", last_updated: lastRun.completed_at };
}
```

---

## 6. UI primitives consommatrices (Phase B2)

Les composants suivants doivent consommer le contract `Maturity`. Implémentation = B2, hors scope A3.

| Composant | Consomme `Maturity` | Description |
|---|---|---|
| `<ModuleHeader>` | oui (props) | Header standardisé fleet root : titre module + badge status + reason + next_step CTA. Remplace les `<div className="gc-topbar">` ad-hoc sur Reality/GEO/Scent/Experiments/Learning. |
| `<ModuleMaturityBadge>` | oui (props) | Badge inline réutilisable (sidebar nav, fleet table cells, drill-down headers). Utilise `MATURITY_PILL_TONE`. |
| `<BlockedState>` | oui (props) | Full-page state pour `blocked` runtime. Style alarm + remediation steps. |
| `<WorkerOfflineState>` | oui (composable avec `blocked`) | Spécialisation de `<BlockedState>` pour `blocking_dependency === "worker_daemon"`. Affiche dernier heartbeat. |
| `<EmptyStateWithMaturity>` | oui (props) | Extension de `EmptyState` existant qui accepte `status === "no_data"` ou `"ready_to_configure"` et rend le CTA next_step approprié. |
| `<ConnectorCard>` | oui (per-connector) | Card par OAuth provider (Reality). Affiche son propre `Maturity`. |

Les primitives `Card` / `KpiCard` / `Pill` / `Button` / `Modal` (cf. `@growthcro/ui`) restent inchangées.

---

## 7. Telemetry

À mettre en place en B3 + G1 (hors A3 scope).

- **Log structuré côté loader** : chaque évaluation de `Maturity` log JSON-ligne `{client_id, module, status, reason, blocking_dependency, computed_at}`. Permet de track la distribution des statuts (combien de clients en `ready_to_configure` Catchr, etc.).
- **Topbar badge global** (B3 / FR-3) : worker daemon health (`active` / `lagging` / `offline`). Lit `/api/worker/health` toutes les 30s.
- **Sidebar dots** (B2) : chaque entrée nav peut afficher un point coloré reflétant le statut max-sévérité du module (`blocked` > `ready_to_configure` > `no_data` > `active` > `experimental` > `archived`).
- **Daily report** (optionnel, J-phase) : sur tous les clients, distribution des statuts par module → repère drift (ex : 50% des clients en `blocked` = signal worker daemon prod en panne).

---

## 8. Sign-off

**Validé par Mathis 2026-05-17** (décisions formalisées + Claude defaults pour Q3-Q5 non-bloquantes).

- [x] **6 statuts** (sémantique + couleurs + labels FR) ✅
- [x] **Règles d'affichage §3** (notamment "aucune fake data, aucune fake interactivity" pour `ready_to_configure`) ✅
- [x] **Contract TypeScript §2** (en particulier l'enum `blocking_dependency`) ✅
- [x] **Matrix initiale §4** (status par module) ✅
- [x] **Transitions §5** (notamment la condition `blocked` = "worker offline ET run pending >5min sur ce module", pas tout l'app rougit par défaut) ✅
- [x] **Q1 Learning status** → `active` + note "Underlying Bayesian approach under review — see G3 spike" (décision Mathis 2026-05-17). Vote queue UI fonctionne et capture signal réel ; l'approche fondamentale est questionnée mais le module reste actif.
- [x] **Q2 Reality connectors GA4 + TikTok** → INCLUS dans matrix initiale en `ready_to_configure` "Not implemented yet — see G1 backend wiring" (décision Mathis 2026-05-17, cohérent avec mention 2026-05-17 sur les connectors prévus).
- [x] **Q3 AURA pipeline V2 status** → `ready_to_configure` "Pipeline V2 jamais run" (Claude default appliqué, sensible avec bouton disabled actuel). Mathis peut override en `experimental` si la V2 doit signaler "non implémenté du tout".
- [x] **Q4 Deadline cleanup `archived`** → Claude default appliqué :
  - `/funnel/[slug]` SUPPRIMÉ en Phase D1 (refonte client workspace, link source dans `clients/[slug]/page.tsx:80` retiré)
  - `/recos` cross-client + `/recos/[clientSlug]` SUPPRIMÉS en Phase D1/E2 (fusion en tab `?tab=recos`)
  - `/clients/[slug]/dna` SUPPRIMÉE en Phase D1 (fusion en tab `?tab=brand-dna`)
  - `CommandCenterTopbar` legacy + `ViewToolbar` + `Breadcrumbs` shim SUPPRIMÉS en Phase B1 (cleanup app shell)
  - `/audit-gads` + `/audit-meta` routes : **PAS supprimées** dans cet epic — cachées de nav (FR-25) en Phase B1, suppression post-MVP quand form UI shippé
- [x] **Q5 Worker daemon** → dépendance transverse, **PAS** module dédié sidebar (Claude default). Pattern : badge global topbar B3 (`<WorkerHealthBadge>`) + cascade `blocking_dependency: 'worker_daemon'` vers modules dépendants. Cohérent avec FR-3 PRD.

### Process post-validation

Une fois validé par Mathis :
1. Commit conventional : `docs(state): add MODULE_MATURITY_MODEL + lib/maturity draft [#68]`.
2. Issue [#68](https://github.com/GrowthSociety-GS/growth-cro/issues/68) closed.
3. B2 (canonical states components) + G1 (Reality UX honest) + G2 (GEO UX honest) + G3 (Learning research spike) + G4 (Experiments decision spike) peuvent démarrer en parallel.
4. Chaque loader Server Component touché en G* doit retourner un `Maturity` au composant chrome (`<ModuleHeader>`) — pas de status hardcodé en UI.

---

## Annexe — Liens

- Source audit produit : [`WEBAPP_PRODUCT_AUDIT_2026-05-17.md`](WEBAPP_PRODUCT_AUDIT_2026-05-17.md) §4.
- Source décisions Mathis A1 : [`WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md`](WEBAPP_PRODUCT_ROUTE_AUDIT_2026-05.md) §11.
- PRD ancré : [`webapp-product-ux-reconstruction-2026-05`](../../prds/webapp-product-ux-reconstruction-2026-05.md) §FR-5, Story 5.
- Epic : [`webapp-product-ux-reconstruction-2026-05`](../../epics/webapp-product-ux-reconstruction-2026-05/epic.md), issue A3 = #68.
- Worker dispatcher : `growthcro/worker/dispatcher.py:36-47`.
- Reality types : `webapp/apps/shell/lib/reality-types.ts` (5 connectors aujourd'hui ; GA4 + TikTok mentionnés Mathis 2026-05-17 hors code).
- Experiments table : `supabase/migrations/20260514_0021_experiments.sql`.

---

**Document créé 2026-05-17 par Claude Code (Opus 4.7 1M-ctx) pour l'issue #68 (A3). Pure documentation + 1 fichier interface TS. Aucune modification de code applicatif existant. À signer-off par Mathis avant que B2 démarre.**
