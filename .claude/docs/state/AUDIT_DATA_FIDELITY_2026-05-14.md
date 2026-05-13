# Audit A.10 — Data Fidelity (Supabase vs disk) — 2026-05-14

## TL;DR

**HYPOTHÈSE MATHIS CONFIRMÉE À 100%.** La migration `scripts/migrate_v27_to_supabase.py` lit `deliverables/growth_audit_data.js` (bundle V21 cluster pauvre, 3045 recos avec schema `{before/after/why/notes/ice_score}`) au lieu des 438 fichiers `data/captures/<client>/<page>/recos_enriched.json` (V13 enricher riche, schema `{reco_text/anti_patterns/feasibility/pillar/enricher_version/schwartz_awareness}`). Conséquence : le composant `RichRecoCard` (qui appelle `extractRichReco(content_json)`) rend une coquille vide — pills priorité/criterion_id + titre, body vide — parce que `content_json` contient `{is_cluster, ice_score, before, after, why, notes, crop, crops, evidence_ids, lifecycle}` et **AUCUN** des champs attendus (`reco_text`, `anti_patterns`, `severity`, `expected_lift_pct`, `pillar`, `enricher_version`, `feasibility.effort_days`). C'est la cause racine #1 du "écran de fumée" 2026-05-13.

## Disk truth richness

### `data/captures/<client>/<page>/recos_enriched.json` (438 fichiers, 116 dossiers clients)

Schema V3.2.0 enricher (`enricher_version: v1.1.0-p2c-2026-04-18`). Top-level wrapper :

```json
{
  "doctrine_version": "v3.2.0-draft — doctrine V13 — 2026-04-18 (overlay-aware)",
  "enricher_version": "v1.1.0-p2c-2026-04-18",
  "business_category": "saas",
  "schwartz_awareness": "problem_aware",
  "page_type": "lp",
  "v32_applicability_overlay": { ... },
  "v32_contextual_overlay": { ... },
  "summary": { "total_recos": 25, "active_count": 12, "P0": 0, "P1": 2, "P2": 0, "P3": 23, ... },
  "perception": { "available": false, ... },
  "recos": [ <25 reco objects> ]
}
```

**Per-reco fields (100% presence sur sample de 570 recos, 20 fichiers):**
- `criterion_id` (e.g. `hero_06`, `per_07`, `ux_05`)
- `reco_text` — texte long-form 100-500 mots avec line breaks + emojis (📊, 📐) + cross-page references
- `priority` — `P0|P1|P2|P3`
- `feasibility` — `{effort_days, feasibility_flag}`
- `pillar` — `hero|persuasion|ux|coherence|psycho|tech`
- `business_category`, `schwartz_awareness`
- `ice_score`, `status` (`active|deferred|suppressed`)
- `cascade`, `prerequisite_cascade`, `ab_variants`
- `enricher_version`, `enriched_at`
- `v32_weight_boost`, `v32_rescued`, `v32_rescue_rule`, `v32_rescue_delta`

**`anti_patterns` (64.6% presence)** — array of `{id, category, pattern, why_bad, instead_do, examples_good, detection_status, dom_reason, mobile_specific, regulatory_risk}`. C'est ce que le `AntiPatternSection` component (RichRecoCard L51) attend pour rendre la section "Pourquoi" / "Comment faire".

### `data/captures/<client>/<page>/score_page_type.json` (524 fichiers)

Bundle de scoring complet par page. Schema :

```json
{
  "doctrineVersion": "v3.2.0-draft — doctrine V13 — 2026-04-18 (ensemble-aware)",
  "label": "stripe",
  "pageType": "lp",
  "maxPerPageType": { "universal": 46, "specific": 3, "total": 49, "rawMax": 147, "scoreBase": 100 },
  "exclusions": { "applied": ["psy_04"], "reasons": {...}, "count": 1 },
  "universal": {
    "byPillar": {
      "hero":      { "rawTotal": 6.0,  "rawMax": 18.0, "score100": 33.3, "kept_criteria_count": 6, "kept_criteria": [...] },
      "persuasion":{ "rawTotal": 19.4, "rawMax": 33.0, "score100": 58.8, "kept_criteria": [...] },
      "ux":        { "rawTotal": 12.0, "rawMax": 24.0, "score100": 50.0, ... },
      "coherence": { "rawTotal": 18.0, "rawMax": 27.0, "score100": 66.7, ... },
      "psycho":    { "rawTotal": 15.0, "rawMax": 21.0, "score100": 71.4, ... },
      "tech":      { "rawTotal": 10.5, "rawMax": 15.0, "score100": 70.0, ... }
    },
    "rawTotal": 80.9, "rawMax": 138.0, "score100": 58.6
  },
  "specific":  { "result": {...}, "rawTotal": 1.5, "rawMax": 9, "score100": 16.7 },
  "aggregate": { "rawTotal": 82.4, "rawMax": 147.0, "score100": 56.1, "bt_weighted_score100": 58.4, "bt_weight_bias": {...} },
  "utility_banner": { "applicable": false, ... },
  "semantic_overlay":   { "applied": true, "criteria_overridden": [...18 items...] },
  "contextual_overlay": { "applied": true, "adjustments": [...], "rules_fired": [...] },
  "applicability_overlay": { "applied": false, "weighted_per_pillar": {...} }
}
```

Chaque pilier expose `kept_criteria` — array de `{id, tier, score, max, regex_score, regex_verdict, semantic_rationale, method}`. C'est la richesse "explicabilité" V3.2.

### `data/captures/<client>/<page>/score_<pillar>.json` (3656 fichiers, ~10 par page)

Un fichier par pilier élémentaire : `score_hero.json`, `score_persuasion.json`, `score_ux.json`, `score_coherence.json`, `score_psycho.json`, `score_tech.json`, `score_semantic.json`, `score_specific.json`, `score_utility_banner.json`, `score_intelligence.json` (pas tous présents partout).

Schema `score_hero.json` :
```json
{
  "label": "stripe",
  "pageType": "lp",
  "url": "https://stripe.com/payments",
  "pillar": "hero",
  "max": 15, "maxFull": 18, "rawTotal": 3, "finalTotal": 3, "score100": 20.0,
  "killerTriggered": true,
  "killerNote": "KILLER hero_06 déclenché: plafond 5/15 (raw=3)",
  "activeCriteria": 5,
  "skippedCriteria": ["hero_04"],
  "criteria": [
    {
      "id": "hero_01",
      "label": "H1 = promesse spécifique",
      "score": 0, "max": 3,
      "verdict": "critical",
      "evidence": { "h1": "Payments", "h1Count": 67, "wordCount": 1, "signals": 0, "hasTarget": false, "hasBenefit": false, "hasDifferentiator": false },
      "rationale": "H1 vague + anti-pattern SEO : 67 H1 sur la page. Le premier H1 n'exprime aucun bénéfice.",
      "applicable": true
    },
    ...
  ],
  "gridVersion": "3.0.0-draft",
  "capturedAt": "2026-04-17T16:57:06.859814+00:00",
  "_perception": { ... }
}
```

C'est le niveau "explicabilité par critère" attendu pour un drill-down V26-parity.

## `growth_audit_data.js` (legacy aggregated bundle)

`deliverables/growth_audit_data.js` — auto-généré par `build_growth_audit_data.py` le 2026-05-11. **Bundle V27 panel runtime** :

```
window.GROWTH_AUDIT_DATA = {
  "meta": { "version": "v27.0.0-panel-roles", "panel_source": ..., ... },
  "fleet": { "n_clients": 56, "n_pages": 185, "n_recos": 3045, "avg_score_pct": 54.0 },
  "module_status": {...},
  "by_panel_role": {...}, "by_business": {...}, "by_page_type": {...},
  "clients": [<56 client objects>],
  "_growth_society_dna": {...}
}
```

**Per-client fields** : `id, name, brand, url, business_type, category, panel, n_pages, n_recos_total, priority_distribution, avg_score_pct, pages, scent_trail, v26 (brand_dna), canonical_tunnel`.

**Per-page fields** : `page_type, url, score_total, score_max, score_pct, priority_distribution, pillars, overlays, semantic_zones, hero, hero_vision, screenshots, audit_quality, recos, n_recos, funnel, funnel_flow, step_recos`.

Bundle `pillars` shape : `{hero: {score: 4.5, max: 18, pct: 25.0, killer: false}, ...}` — note **`max: 0` pour 555 occurrences** (sur 185 pages × 6 piliers ≈ 1110, soit ~50% des piliers ont `max=0`). Cause probable : bug bundle generator. Le webapp tombe en fallback `DEFAULT_MAX[key]` quand `max===0` (cf. `pillar-utils.ts:79`), donc le pourcentage est cohérent mais la valeur affichée "score/max" est mensongère.

**Per-reco fields** (V21 cluster final) — schema "RICH STRUCTURED" mais avec un AUTRE vocabulaire :
| Field | Bundle | recos_enriched | Notes |
|-------|--------|----------------|-------|
| `criterion_id` | 100% | 100% | OK |
| `priority` | 100% | 100% | OK |
| `ice_score` | 100% | 100% | OK |
| `evidence_ids` | 90.1% | 100% | OK |
| `effort` | 100% | — | bundle: `int days`; disk: `null` |
| `lift` | 71.2% | — | bundle: `int 0-100`; disk: `null` |
| `why` | 100% | — | bundle key |
| `before` | 99.7% | — | bundle key |
| `after` | 74.9% | — | bundle key |
| `notes` | 99.1% | — | bundle key |
| `crops`/`crop` | 100%/49% | — | bundle key |
| `is_cluster` | 9.0% | — | bundle key |
| `cluster_id` | 9.0% | — | bundle key |
| `problem_headline` | 9.0% | — | bundle key |
| `criteria_covered` | 9.0% | — | bundle key |
| `lifecycle` | 13.4% | — | bundle key |
| `reco_text` | **0%** | **100%** | **DISK ONLY** |
| `anti_patterns` | **0%** | **64.6%** | **DISK ONLY** |
| `feasibility` | **0%** | **100%** | **DISK ONLY** |
| `pillar` | **0%** | **100%** | **DISK ONLY** |
| `business_category` | **0%** | **100%** | **DISK ONLY** |
| `schwartz_awareness` | **0%** | **100%** | **DISK ONLY** |
| `enricher_version` | **0%** | **100%** | **DISK ONLY** |
| `status` (active/deferred/...) | **0%** | **100%** | **DISK ONLY** |
| `cascade`, `prerequisite_cascade`, `ab_variants` | **0%** | **100%** | **DISK ONLY** |
| `severity` | **0%** | nested in `anti_patterns[].detection_status` | **NOWHERE** as top-level |
| `expected_lift_pct` | **0%** | **0%** | **MISSING EVERYWHERE** — only seed_supabase_test_data.py fabricates it |

### Schema delta synthétique

**Bundle V21 cluster** = "produit final" (problem/before/after/why/notes) — utile pour un consultant qui lit un audit final.
**Disk V13 enricher** = "traçabilité doctrine V3.2.0" (criterion_id + pillar + reco_text + anti_patterns + feasibility + schwartz + cascade) — utile pour le webapp UI qui expose la richesse explicabilité.

Le webapp a été conçu pour la **forme disk** (cf. SP-4 commit messages "FR-2b pivot 2026-05-13" qui parlent explicitement de `recos_enriched.json` shape) — mais la migration a chargé la **forme bundle**.

## Supabase schema (from migrations/)

### `clients` (init_schema.sql L32-L48)
- `id uuid PK`, `org_id uuid FK`, `slug text`, `name text`
- `business_category text` ← OK populated par migration (depuis `business_type || category`)
- `homepage_url text` ← OK
- `brand_dna_json jsonb` ← OK populated depuis `v26.brand_dna` (51/56 clients)
- `panel_role text`, `panel_status text` ← OK populated
- `created_at`, `updated_at timestamptz`

### `audits` (init_schema.sql L53-L68)
- `id uuid PK`, `client_id uuid FK`, `page_type text`, `page_slug text`, `page_url text`
- `doctrine_version text default 'v3.2.1'` ← hardcoded `'v3.2.1'` dans le script alors que les recos sont du v3.2.0-draft (mismatch mineur)
- `scores_json jsonb` ← contient `{pillars: page.pillars, overlays: page.overlays, audit_quality: page.audit_quality}` — note: `page.pillars` du bundle a `max:0` pour ~50% des piliers
- `total_score numeric` ← depuis `page.score_total`
- `total_score_pct numeric` ← depuis `page.score_pct`

### `recos` (init_schema.sql L73-L88)
- `id uuid PK`, `audit_id uuid FK`, `criterion_id text`
- `priority text CHECK (P0|P1|P2|P3)` — script normalise default `'P3'`
- `effort text CHECK (S|M|L)` — script bucket `effort_days: <=3→S, <=7→M, sinon L`
- `lift text CHECK (S|M|L)` — script bucket `lift|impact: 0-33→S, 34-66→M, 67+→L`
- `title text` — script tombe sur `criterion_id` en dernier recours (most bundle recos n'ont **pas** de `title`)
- `content_json jsonb default '{}'` ← **VOIR DELTA SECTION CI-DESSUS** : contient `{is_cluster, cluster_id?, criteria_covered?, ice_score, problem_headline?, before, after, why, notes, crop, crops, evidence_ids, lifecycle}` mais ZÉRO des champs UI-expected.
- `oco_anchors_json jsonb` — script l'extrait depuis `reco.oco_anchors` (jamais présent dans le bundle → 100% NULL)

### `runs`, `organizations`, `org_members` — pas pertinents pour data-fidelity.

### Brand DNA / Funnel / Vision / Perception / Spatial / Capture
**Aucune table** : tout est compressé dans `clients.brand_dna_json` (uniquement) ou perdu. Le bundle a `c.scent_trail` (scent trail end-to-end), `c.canonical_tunnel`, `p.funnel`, `p.funnel_flow`, `p.step_recos`, `p.hero_vision`, `p.semantic_zones`, `p.overlays`, `p.audit_quality` — la migration **drop tout** sauf `pillars + overlays + audit_quality` agrégés dans `scores_json`. Disk a `vision_reconciled_*.json` (582 fichiers), `spatial_v9.json` / `spatial_v10_*.json`, `perception_v13.json` — **totalement absents** de Supabase.

## Migration scripts found

| Script | Source | Cible | Notes |
|--------|--------|-------|-------|
| `scripts/migrate_v27_to_supabase.py` | `deliverables/growth_audit_data.js` (V21 cluster bundle) | `clients`, `audits`, `recos` | **Production migration** (~340 lignes). Dry-run par défaut, live si `SUPABASE_URL+SERVICE_ROLE_KEY` set. Idempotent : `delete_audits_for_clients` puis re-insert. Ne touche **pas** au disk. |
| `scripts/seed_supabase_test_data.py` | Fixtures inline (3 clients `acme-saas`/`japhy-petfood`/`doctolib-health` + 5 recos `RECOS_TEMPLATES` hardcodées) | `clients`, `audits`, `recos`, `runs` | **Test seed** — 3 clients démos + 6 audits + 30 recos avec `content_json = {summary, evidence_ids, expected_lift_pct}` (seul script qui peuple `expected_lift_pct`, mais c'est de la donnée fictive). |
| `scripts/upload_screenshots_to_supabase.py` | `data/captures/<client>/<page>/screenshots/*.png` | Supabase Storage bucket `screenshots` | OK déjà investigué (SP-11). |

**Aucun script ne lit `recos_enriched.json` ni `score_*.json` pour les pousser vers Supabase.**

## Webapp queries

### Composants UI et schemas attendus

| Composant | Fichier | Attend dans `content_json` |
|-----------|---------|--------------------------|
| `RichRecoCard` | `webapp/apps/shell/components/audits/RichRecoCard.tsx` | `reco_text` (fallback `summary`/`description`), `pillar`, `severity`, `enricher_version`, `effort_days` (top OR `feasibility.effort_days`), `ice_score`, `expected_lift_pct`, `anti_patterns[].{pattern,why_bad,instead_do,examples_good}`, `evidence_ids` |
| `AntiPatternSection` (interne) | id. | `anti_patterns[0].{pattern,why_bad,instead_do,examples_good}` |
| `extractRichReco()` | `webapp/apps/shell/components/clients/score-utils.ts` L155-L220 | Schema canonique disk V3.2.0 enricher — TOUS les fields disk ci-dessus |
| `PillarsSummary` | `webapp/apps/shell/components/audits/PillarsSummary.tsx` | `scores_json.pillars[<key>].{total|score|value, max, pct, killer}` — défensif sur 3 shapes (A=migration, B=seed flat, C=value-wrapped) |
| `AuditQualityIndicator` | `webapp/apps/shell/components/audits/AuditQualityIndicator.tsx` | derived from pillars count + recos count |
| `getAuditScores()` (legacy) | `score-utils.ts` L26-L41 | flat `{<key>: number}` ou `{<key>: {value: number}}` |
| `audits/[clientSlug]/page.tsx` `sortRecosByImpact()` | id. L46-L53 | `rankRecoImpact(priority, expectedLiftPct)` — sans `expected_lift_pct`, tous les recos ont `lift=-1` → tri uniquement par priorité (fallback OK) |

### DELTA rendered-but-empty (production actuelle)

Pour CHAQUE reco migré depuis le bundle (`growth_audit_data.js`), le UI rend :
- ✅ Pill `priority` (P0/P1/P2/P3) — OK depuis `recos.priority`
- ✅ Pill `criterion_id` — OK depuis `recos.criterion_id`
- ✅ Pill `effort S/M/L` — OK depuis `recos.effort` (bucketed S/M/L par script)
- ✅ Pill `lift S/M/L` — OK depuis `recos.lift` (bucketed S/M/L par script)
- ✅ Titre `recos.title` — généralement `criterion_id` (fallback car bundle n'a pas de `title`)
- ❌ Pill `severity` — **VIDE** (jamais populé)
- ❌ Pill `pillar` — **VIDE** (jamais populé en top-level dans content_json)
- ❌ Body `reco_text` — **VIDE** (content_json a `why`/`before`/`after`/`notes` mais pas `reco_text`)
- ❌ Section "Pourquoi" / "Comment faire" — **VIDE** (pas de `anti_patterns`)
- ❌ Pill `Lift +X%` — **VIDE** (pas de `expected_lift_pct`)
- ❌ Pill `Xj` (effort_days) — **VIDE** (pas de `feasibility.effort_days`)
- ⚠️ Debug ICE — **OK** (`ice_score` présent)
- ⚠️ Debug enricher — **VIDE** (pas de `enricher_version`)
- ⚠️ Debug evidence — **OK** (`evidence_ids` présent)

→ Body de la card s'ouvre sur **rien**. Footer affiche juste effort/lift S/M/L pills et un bouton Debug essentiellement vide. C'est le **"écran de fumée"** Mathis constate.

### Score panel side-effects

- `PillarsSummary` rend les 6 piliers OK (fallback `DEFAULT_MAX` masque le `max:0` du bundle pour ~50% des piliers).
- `audit.total_score_pct` est présent (depuis `page.score_pct`) → "Score moyen X%" badge OK.
- **MAIS** : 51 clients sur 56 ont des recos (cf. `module_status.recommendations_engine.count: 51`), donc **5 clients ont 0 recos** → message "Aucune reco générée pour cet audit." rendered (faux : ces clients ont des recos sur disk).

## P0 findings (data fidelity bugs)

1. **[P0-RACINE] Migration source pathologique** : `migrate_v27_to_supabase.py` lit `growth_audit_data.js` (V21 cluster) au lieu des 438 `recos_enriched.json` (V13 enricher). Conséquence : `content_json` n'a aucun champ que `RichRecoCard` exige. **Body vide partout.** → `RichRecoCard` rend une coquille.

2. **[P0] `reco_text` absent partout en prod Supabase** : 100% des recos disk l'ont, 0% des recos Supabase. La fallback `summary`/`description` est aussi absente (bundle n'a ni l'un ni l'autre). → Rien à afficher dans `<p className="gc-rich-reco__text">`.

3. **[P0] `anti_patterns` absent partout en prod Supabase** : 64.6% des recos disk en ont (avec `pattern, why_bad, instead_do, examples_good`), 0% des recos Supabase. → Section "Pourquoi / Comment faire" jamais rendue.

4. **[P0] `pillar`, `severity`, `enricher_version`, `feasibility.effort_days`, `business_category`, `schwartz_awareness`, `cascade`, `ab_variants`** — TOUS absents dans Supabase, TOUS présents 100% sur disk. → Pills + debug vides + impossible de filtrer par pillar/schwartz côté UI.

5. **[P0] Schema explicabilité scoring perdu** : `score_<pillar>.json` (3656 fichiers, `criteria[].{id, label, score, verdict, evidence, rationale, applicable}`) — totalement absent de Supabase. → Aucun drill-down par critère possible (V26 reference parity impossible).

6. **[P0] Schema overlays riche perdu** : `score_page_type.json.semantic_overlay.criteria_overridden[]`, `contextual_overlay.adjustments[]`, `applicability_overlay.weighted_per_pillar` — agrégés dans `audits.scores_json.overlays` SANS la richesse `kept_criteria[].{semantic_rationale, method}`. Le bundle ne porte que `{applied, version, rules_fired, by_pillar_delta}`. → Pas d'explicabilité Haiku semantic, pas de tracé "before/after rescue".

7. **[P0] Bundle `pillars.max=0` pour 555 occurrences (~50%)** : bug du bundle generator, masqué côté UI par fallback `DEFAULT_MAX`. → Pas d'impact visuel direct, mais data corrompue → médaille "écran de fumée" sous-jacente.

## P1 findings

8. **[P1] `expected_lift_pct` absent partout** : ni sur disk recos_enriched (sample 570 : 0% present), ni dans bundle, ni dans migration. Seul `seed_supabase_test_data.py` fabrique des chiffres. → Pill "Lift +X%" ne s'affichera **jamais** depuis vraie données. Soit on calcule (via `ice_score` ?), soit on retire le pill.

9. **[P1] `severity` absent partout (top-level)** : disk ne l'a pas en top-level — `anti_patterns[].detection_status` est l'équivalent mais c'est par anti-pattern. → Pill "severity" ne s'affichera jamais. Décision UX requise.

10. **[P1] `total_score` mismatch doctrine** : migration hardcode `doctrine_version: "v3.2.1"` alors que le bundle a `v3.2.0-draft — doctrine V13` ET les disk `recos_enriched.json` aussi. Le webapp affiche `v3.2.1` (faux). Soit on lit la vraie version, soit on documente que le bundle a été régénéré avec un nouveau doctrine, et on harmonise les recos.

11. **[P1] Brand DNA scope reduction** : disk `brand_dna.json` riche (visual_tokens, voice_tokens, asset_rules, method, image_direction) — bundle copie le tout dans `v26.brand_dna` ET migration l'insère dans `clients.brand_dna_json`. ✅ **OK fidèle** pour 51 clients (sur 56), mais aucune table dédiée → impossible de versionner ou de différencier `brand_dna` runs (V29/V30 evolutions).

12. **[P1] Funnel / scent_trail / canonical_tunnel / step_recos perdus** : présents dans le bundle au niveau client/page, perdus à la migration. → Pas de visualisation funnel-flow possible côté webapp.

13. **[P1] Hero / hero_vision / semantic_zones perdus** : présents dans bundle `page` shape, perdus à la migration. → Pas d'aperçu hero "annotated" côté webapp.

14. **[P1] Visions / Perceptions / Spatial perdus** : `vision_reconciled_*.json` (582 fichiers), `spatial_v9.json`, `perception_v13.json` — totalement absents de Supabase. → Aucun overlay LLM-judge ou spatial sur webapp.

## P2 findings

15. **[P2] 5 clients ont 0 recos en bundle** : 51/56 selon `module_status`. → Message "Aucune reco générée" pour ces 5 clients.

16. **[P2] Disk: 116 dossiers clients vs bundle: 56 clients** : le bundle a un panel sub-set (panel runtime). 60 clients disk ne sont pas dans Supabase. → Manque exposition fleet complète.

17. **[P2] Disk: 438 recos_enriched.json files** mais le bundle ne référence que 185 pages (3045 recos). Soit beaucoup de pages capturées non incluses dans le panel runtime, soit redondance. → Audit panel coverage requis.

18. **[P2] `audits.doctrine_version` hardcodé** : aucun lien avec `recos_enriched.json.doctrine_version`. Si on re-migre via le vrai V13 enricher, on doit lire la version par fichier.

## Re-migration plan (suggestion pour Wave C)

### Étape 1 — Nouveau script `scripts/migrate_disk_to_supabase.py`
Lire **directement** `data/captures/<client>/<page>/` :
- Pour chaque `<client>`, créer un `clients` row depuis `data/captures/<client>/brand_dna.json` + `data/captures/<client>/capture_meta.json` (url + business_category + panel_role).
- Pour chaque `<page>` (subdir non-`_*` non-`.*`), créer un `audits` row :
  - `page_type` = de `capture_meta.json` (ou du nom de dir)
  - `page_url` = de `capture_meta.json`
  - `doctrine_version` = lu depuis `score_page_type.json.doctrineVersion`
  - `total_score`, `total_score_pct` = de `score_page_type.json.aggregate.{rawTotal, score100}` (ou `bt_weighted_score100` si applicable)
  - `scores_json` = **riche** :
    ```json
    {
      "pillars": { <key>: {total, max, pct, killer, kept_criteria_count, score100} },
      "overlays": {
        "semantic": { "applied", "version", "model", "criteria_overridden": [...] },
        "contextual": { "applied", "adjustments": [...], "rules_fired": [...] },
        "applicability": { "applied", "weighted_per_pillar": {...}, "rules_matched": [...] }
      },
      "exclusions": {...},
      "utility_banner": {...},
      "specific": {...},
      "aggregate": {...}
    }
    ```
- Pour chaque reco dans `recos_enriched.json.recos[]`, créer un `recos` row avec `content_json` = **entièreté du reco** moins les fields déjà en colonnes :
  ```json
  {
    "reco_text": "...long form...",
    "pillar": "hero",
    "anti_patterns": [...],
    "feasibility": {...},
    "cascade": {...},
    "prerequisite_cascade": {...},
    "ab_variants": {...},
    "guardrails_triggered": [...],
    "business_category": "saas",
    "schwartz_awareness": "problem_aware",
    "enricher_version": "v1.1.0-p2c-2026-04-18",
    "enriched_at": "...",
    "ice_score": 0.0,
    "status": "active",
    "v32_weight_boost": 1.1,
    "v32_rescued": false
  }
  ```

### Étape 2 — Nouvelles tables (migration `20260514_0006_scores_richness.sql`)
Optionnel si on accepte de tout fourrer dans `content_json` jsonb, mais doctrine `mono-concern` suggère :
- `scores_pillars (audit_id, pillar_key, raw_total, raw_max, score100, kept_criteria_count, killer)` — index pour filter "scores ≥ 70%" rapidement
- `scores_criteria (audit_id, criterion_id, pillar_key, score, max, verdict, evidence_json, rationale, method, applicable)` — drill-down par critère
- `overlays_semantic (audit_id, criterion_id, regex_score, semantic_score, delta, verdict, rationale, method)` — exposable comme "explicabilité Haiku"
- `overlays_contextual (audit_id, target_criterion, rule_id, before_score, after_score, delta, rationale, peers_json)`
- `anti_patterns (reco_id, id, category, pattern, why_bad, instead_do, examples_good, detection_status, mobile_specific, regulatory_risk)`

### Étape 3 — Validation
- Smoke test : pour 1 client (stripe), vérifier que `RichRecoCard` rend `reco_text` long-form + section "Pourquoi/Comment faire" + tous les pills.
- Cross-check pillar scores : Supabase `audits.total_score_pct` ≈ disk `score_page_type.json.aggregate.score100` (tolérance ±0.5).
- Count parity : `SELECT count(*) FROM recos JOIN audits ON ... WHERE client.slug='stripe' AND page_type='lp'` == `recos_enriched.json.summary.total_recos`.

### Étape 4 — Cleanup
- Archive `growth_audit_data.js` (≈ 5.5M tokens) hors path actif (cf. doctrine anti-pattern #10).
- Archive `migrate_v27_to_supabase.py` après remplacement (suffix `_archive` ou move sous `scripts/_archive/`).
- Update `webapp-data-fidelity-and-skills-stratosphere-2026-05.md` PRD: cocher Wave A blocking comme résolue après re-migration validée.

### Étape 5 — Coverage extension (P2 followup)
- Ajouter les ~60 clients disk présents mais absents du bundle (panel runtime). Décision Mathis sur quel panel charger en prod.
- Pousser `vision_reconciled_*.json`, `perception_v13.json`, `spatial_*.json` vers nouvelles tables ou Supabase Storage (suivant le volume).

---

**Préparé par audit A.10 — méthode AU CARRÉ, doctrine V26.AG.**
