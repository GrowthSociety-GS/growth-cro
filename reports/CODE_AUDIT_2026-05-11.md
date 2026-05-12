# Code Audit Report — 2026-05-11

> **Scope** : Audit complet (Mission A) sur la codebase GrowthCRO post-cleanup epic. Read-only. Worktree `task-code-audit` sur branche `task/code-audit-and-discovery`.
> **Tooling** : ruff 0.15.12, mypy 2.0.0, bandit 1.9.4, vulture 2.16, eslint 8.57 (next/core-web-vitals), tsc 5.4, knip (latest), `scripts/lint_code_hygiene.py` (stdlib custom), `scripts/audit_capabilities.py`.
> **Périmètre Python** : `growthcro/`, `moteur_gsg/`, `moteur_multi_judge/`, `skills/`, `scripts/` (excluant `_archive/`, `__pycache__/`). 242 fichiers `.py` actifs, ~54 849 LOC scannées par bandit.
> **Périmètre TypeScript** : `webapp/apps/*`, `webapp/packages/*` (6 microfrontends + 3 packages partagés). 73 fichiers `.ts`/`.tsx`.

---

## Executive Summary

| Tool / Check | Findings | Severity breakdown |
|---|---:|---|
| ruff (Python lint) | 655 | majoritairement style (F541 f-string vides 202, F401 unused-imports 133, E701/E702 statements 200), 4 bare-except |
| mypy (types) | 88 | 39 union-attr, 20 assignment, 9 arg-type — concentrés 25 fichiers |
| bandit (security) | 192 | 4 HIGH, 15 MEDIUM, 173 LOW |
| vulture (dead code) | 18 | high-confidence unused imports + 4 unused variables |
| eslint (webapp) | 0 | propre |
| tsc per-app (webapp) | 0 | propre sur 6 apps |
| knip (webapp dead) | 23 | 1 fichier inutilisé + 12 deps unused (Supabase stubs) + 6 exports/types |
| TODO/FIXME debt | 16 | 7 `_TODO_sprint_c` brief_v15 + 5 BrightData env example strings + 4 autres |
| `os.environ` outside config | **0** | **doctrine 100% compliant** |
| Bare `except:` | 4 | tous dans `skills/` legacy |
| Hardcoded secrets | **0** | sk-/ghp_/AKIA/TOKEN scans propres |
| print() in pipelines | 457 | déjà tracé INFO par linter custom |
| Orphans (capabilities) | **0** | confirmé par `audit_capabilities.py` |
| Legacy in active use | 5 | tous contenus dans îlot `growthcro/gsg_lp/` + `brief_v15_builder` |

### Critical clusters (top 3 modules)
1. **`moteur_gsg/core/visual_intelligence.py`** : 13 erreurs mypy (union-attr × 7, assignment × 3, var-annotated × 3) — typage faible sur structures dict imbriquées.
2. **`growthcro/recos/orchestrator.py`** : 10 erreurs mypy, 6 bandit, 1 ruff. Carrefour orchestration recos. Probable manque de pydantic models pour les contrats internes.
3. **`growthcro/capture/orchestrator.py`** : 11 bandit MEDIUM (B603 subprocess), 34 print() (top offender), un des entrypoints orchestration les plus chargés.

### Recommended actions (top 5 by ICE — Impact × Confidence × Ease)
1. **Auto-fix ruff `--fix`** : 339 fixes mécaniques disponibles (unused imports F401, multiple-statements). **ICE = 8×10×10 = 800**. Zéro risque sémantique. Faire un commit isolé `chore: ruff --fix on Python tree`.
2. **Tag bandit weak-hash findings comme `usedforsecurity=False`** : 4 HIGH severity findings sont tous des cache-keys non-cryptographiques (faux positifs). **ICE = 5×10×10 = 500**. Réduit le bruit security à 0 HIGH.
3. **Remplacer les 4 bare `except:`** par `except Exception:` minimum, idéalement `except (KnownError1, KnownError2)`. Tous dans `skills/` — bug latent qui masque des erreurs système (Ctrl-C). **ICE = 7×10×7 = 490**.
4. **Pydantic-iser les contrats internes** (`copy_doc`, `plan`, `brand_dna`, `recos_payload`) pour faire disparaître les 39 mypy `union-attr` errors. **ICE = 9×8×5 = 360** — gros impact qualité, gros effort (≥1 sprint).
5. **Migrer print() → logging** dans les top-10 pipelines (`capture_full.py` 75, `capture/orchestrator.py` 34, `mode_1/orchestrator.py` 33, `gsg_lp/lp_orchestrator.py` 33). **ICE = 7×9×6 = 378**. Permettra de promouvoir la règle INFO → WARN dans le linter custom.

---

## Section 1 — Python audit (ruff / mypy / bandit / vulture)

### 1.1 — Ruff (655 errors, 339 auto-fixable)

**Categories** :
| Code | Count | Description |
|---|---:|---|
| F541 | 202 | f-string without placeholder (auto-fix) |
| F401 | 133 | unused-import (auto-fix) |
| E701 | 107 | multiple-statements-on-one-line (colon) |
| E702 | 93 | multiple-statements-on-one-line (semicolon) |
| E402 | 43 | module-import-not-at-top-of-file |
| F841 | 31 | unused-variable |
| E741 | 22 | ambiguous-variable-name |
| E401 | 18 | multiple-imports-on-one-line (auto-fix) |
| E722 | **4** | **bare-except (real bug latent)** |
| invalid-syntax | 1 | encoding/parse error (1 file) |
| F811 | 1 | redefined-while-unused |

**Top 10 files by ruff findings** :
```
46  skills/site-capture/scripts/score_persuasion.py
31  skills/site-capture/scripts/score_coherence.py
23  scripts/run_gsg_full_pipeline.py
20  skills/growth-site-generator/scripts/aura_extract.py
20  skills/site-capture/scripts/capture_site.py
18  skills/growth-site-generator/scripts/aura_compute.py
18  skills/site-capture/scripts/geo_audit.py
16  growthcro/cli/capture_full.py
16  skills/site-capture/scripts/discover_pages_v25.py
13  moteur_multi_judge/orchestrator.py
```

**Cluster observation** : 70% des findings concentrés sur `skills/site-capture/scripts/` (pre-existing legacy debt — déjà mentionné dans `CODE_DOCTRINE.md` §debt). 30% sur `moteur_gsg/`, `moteur_multi_judge/`, `growthcro/`.

**Action recommandée** : exécuter `ruff check --fix growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/` pour absorber les 339 auto-fixes. Reste 316 violations dont 4 bare-except à traiter à la main.

### 1.2 — Mypy (88 errors in 25 files, 138 sources checked)

**Top error categories** :
| Category | Count |
|---|---:|
| union-attr | 39 |
| assignment | 20 |
| arg-type | 9 |
| var-annotated | 7 |
| misc | 4 |
| index | 3 |
| operator | 3 |
| attr-defined | 2 |
| dict-item | 1 |

**Top files by mypy errors** :
```
13  moteur_gsg/core/visual_intelligence.py
10  moteur_gsg/core/context_pack.py
10  growthcro/recos/orchestrator.py
 8  growthcro/scoring/ux.py
 6  growthcro/recos/schema.py
 6  moteur_gsg/core/design_tokens.py
 5  moteur_gsg/core/creative_route_selector.py
 3  growthcro/cli/enrich_client.py
 3  moteur_gsg/core/copy_writer.py
 3  growthcro/reality/orchestrator.py
 3  moteur_gsg/modes/mode_1_complete.py
```

**Pattern dominant** : 39 `union-attr` errors viennent de `dict[Any, Any] | None` non-narrowés (`.get()` appelé sans guard `if x is not None`). Indicatif que les contrats inter-modules sont structurés en dict-pythonic (pas Pydantic / TypedDict).

**Action recommandée** : étape 1 — corriger les 7 `var-annotated` (annotations manquantes, mécanique). Étape 2 — typer les contrats internes via Pydantic / TypedDict ; viser `moteur_gsg/core/visual_intelligence` + `context_pack` + `growthcro/recos/orchestrator` (top 3, 33 erreurs = 37% du total).

### 1.3 — Bandit (192 issues : 4 HIGH + 15 MEDIUM + 173 LOW)

#### HIGH severity (4) — TOUS faux positifs

Tous des hash weak (MD5/SHA1) utilisés comme **cache keys**, jamais en contexte sécurité :
- `skills/site-capture/scripts/geo_readiness_monitor.py:285` — `_cache_key(query, engine_name)` MD5
- `skills/site-capture/scripts/page_cleaner.py:171` — `_section_signature(sec)` SHA1 (dédup)
- `skills/site-capture/scripts/project_snapshot.py:286` — SHA1 file digest
- `skills/site-capture/scripts/vision_spatial.py:231` — `_vision_cache_key(image_b64)` MD5

**Action recommandée** : ajouter `usedforsecurity=False` à chaque `hashlib.md5()`/`hashlib.sha1()` ou un `# nosec B324` ciblé. Ramène les 4 HIGH à 0.

#### MEDIUM severity (15)

| File:Line | Test | Description | Triage |
|---|---|---|---|
| `growthcro/api/server.py:319` | B104 | bind 0.0.0.0 | Dev-only (`uvicorn.run`) — OK en prod-Vercel. À documenter. |
| `growthcro/reality/google_ads.py:71` | B608 | SQL injection (f-string GAQL) | RÉEL : `page_url` et `period_*` proviennent du client. À paramétrer ou whitelist. |
| `skills/site-capture/scripts/reality_layer/google_ads.py:70` | B608 | idem | RÉEL — doublon legacy. |
| `growthcro/capture/scorer.py:95` | B310 | `urllib.urlopen` custom scheme | Internal-only. À ajouter assert `url.startswith("https://")`. |
| `growthcro/cli/enrich_client.py:198` | B310 | idem | idem |
| `scripts/migrate_v27_to_supabase.py:174` | B310 | idem | idem |
| `skills/site-capture/scripts/eclaireur_llm.py:84` | B310 | idem | idem |
| `skills/site-capture/scripts/run_capture.py:94` | B310 | idem | idem |
| `skills/site-capture/scripts/run_discover.py:150` | B310 | idem | idem |
| `skills/site-capture/scripts/run_spatial_capture.py:176` | B310 | idem | idem |
| `skills/site-capture/scripts/web_vitals_adapter.py:90` | B310 | idem | idem |
| `skills/site-capture/scripts/web_vitals_adapter.py:105` | B310 | idem | idem |
| `growthcro/research/cli.py:34` | B108 | insecure temp file | `/tmp/gc_research_*` — mineur. |
| `moteur_gsg/core/pipeline_single_pass.py:370` | B108 | idem | idem |
| `skills/site-capture/scripts/discover_pages_v25.py:125` | B314 | XML untrusted | sitemap.xml parsing — passer à `defusedxml`. |

**Top 5 files by bandit findings** :
```
11  growthcro/capture/orchestrator.py
10  skills/site-capture/scripts/discover_pages_v25.py
 9  skills/site-capture/scripts/build_growth_audit_data.py
 9  skills/site-capture/scripts/capture_site.py
 7  skills/growth-site-generator/scripts/aura_compute.py
```

**Action recommandée P1** : corriger les 2 SQL injection B608 dans Google Ads (paramétrer `period_start/period_end`, whitelist `page_url`). **P2** : ajouter `defusedxml` pour le sitemap parsing. **P3** : tag `usedforsecurity=False` sur les 4 HIGH.

### 1.4 — Vulture (18 dead-code candidates, confidence ≥70%)

```
growthcro/api/server.py:38           unused import 'JSONResponse'
growthcro/api/server.py:39           unused import 'HttpUrl'
growthcro/gsg_lp/repair_loop.py:31   unused variable 'original_mega_prompt_summary'
growthcro/research/brand_identity.py:105  unused variable 'all_colors'
moteur_gsg/modes/mode_1/runtime_fixes.py:140  unused variable 'target_body_alt_loadable'
skills/growth-site-generator/scripts/gsg_multi_judge.py:69  unused import '_ensure_api_key'
skills/site-capture/scripts/brand_dna_extractor.py:644  unused import '_load_dotenv_if_needed'
skills/site-capture/scripts/enrich_scores_with_evidence.py:33  unused imports x2
skills/site-capture/scripts/golden_calibration_check.py:299  redundant if-condition
skills/site-capture/scripts/project_snapshot.py:33    unused import 'OrderedDict'
skills/site-capture/scripts/score_coherence.py:21     unused import 'get_verdict'
skills/site-capture/scripts/score_hero.py:27          unused import 'get_verdict'
skills/site-capture/scripts/score_persuasion.py:23    unused import 'get_verdict'
skills/site-capture/scripts/score_psycho.py:32        unused import 'get_verdict'
skills/site-capture/scripts/score_tech.py:32          unused import 'get_verdict'
skills/site-capture/scripts/spatial_bridge.py:31      unused import 'is_v9_capture'
skills/site-capture/scripts/web_vitals_adapter.py:121 unused variable 'dom_hints'
```

**Pattern** : 5 scorers importent `get_verdict` sans l'utiliser — copier-coller historique. **Action recommandée** : `ruff --fix` les attrape via F401 sauf si protégés par `if False:`. Vérifier après auto-fix.

---

## Section 2 — TypeScript audit (eslint / tsc / knip)

### 2.1 — Per-app results

| App | tsc errors | eslint errors |
|---|---:|---:|
| audit-app | 0 | 0 |
| gsg-studio | 0 | 0 |
| learning-lab | 0 | 0 |
| reality-monitor | 0 | 0 |
| reco-app | 0 | 0 |
| shell | 0 | 0 |

**Observation** : tsc contre `tsconfig.base.json` (racine) montre 23 erreurs `Cannot find module '@/lib/...'` car les paths `@/*` sont définis **per-app** dans `apps/*/tsconfig.json`, pas dans base. C'est attendu. `tsc --noEmit` lancé dans chaque app passe à 0 erreur.

### 2.2 — Knip (dead-code / unused deps)

**Findings** (23 total) :
- 1 unused file : `apps/learning-lab/lib/supabase-server.ts`
- 12 unused dependencies : `@supabase/ssr` × 5 + `@supabase/supabase-js` × 5 + `@growthcro/config` + `@growthcro/data` (apps Supabase stubs, deferred wiring)
- 4 unused devDependencies racine : `@types/react-dom`, `eslint`, `eslint-config-next`, `prettier` (utilisés par sous-projets, faux positif)
- 3 unused exports : `proposalFilterDomains` (learning-lab), `listAllSnapshots` + `snapshotsByClient` (reality-monitor)
- 3 unused exported types : `ConnectorStatusView`, `ConnectorStatus`, `Tokens`

**Triage** : webapp est un fresh scaffold Next.js 14 (V28 target, Epic #21 récent). Les deps Supabase et les exports `*-fs.ts` sont des **stubs** pour wiring futur. Les knip findings sont attendus mais à reviewer post-Epic #6 (webapp V28 migration complète).

**Action recommandée** : créer ticket `KNIP_FALSE_POSITIVE_TRIAGE.md` post-Epic #6 pour distinguer dead-code réel des stubs deferred.

### 2.3 — Axe a11y

Non installé par défaut. À ajouter dans une passe future quand des pages live tournent (V28 deployment).

---

## Section 3 — Cross-cutting

### 3.1 — TODO / FIXME / HACK / XXX debt

**16 occurrences** réparties :
- 5 strings d'exemple BrightData env (pas vraie debt)
- 7 `_TODO_sprint_c` dans `moteur_gsg/core/brief_v15_builder.py` (legacy, déjà flaggé `status=legacy` dans architecture map)
- 1 `TODO P11.9` migration cloud capture
- 2 `TODO : from ocr_diff.json when available` dans `build_growth_audit_data.py`
- 1 `TODO (depends on issue #6 merging)` dans `mode_1/api_call.py`

**Verdict** : debt minimal, déjà tracée dans roadmap (issues GitHub + status=legacy).

### 3.2 — Env reads outside `growthcro/config.py`

**0 violations** (excluant 2 références dans `scripts/lint_code_hygiene.py` lui-même qui contient les strings de check). Conformité doctrine 100%.

### 3.3 — Bare except clauses

**4 occurrences** :
```
skills/growth-site-generator/scripts/aura_extract.py:597
skills/growth-site-generator/scripts/aura_extract.py:702
skills/site-capture/scripts/batch_site.py:113
skills/site-capture/scripts/discover_pages_v25.py:648
```

Tous dans `skills/` legacy paths. **Risque** : masque `KeyboardInterrupt`, `SystemExit`, et autres exceptions internes Python. **Action P1** : remplacer par `except Exception:` minimum.

### 3.4 — Hardcoded credentials / secrets

**0 occurrences** détectées (regex `sk-[a-zA-Z0-9]{20,}|xoxb-|ghp_|AKIA|API_KEY=['\"][^'\"]{20,}|TOKEN=['\"]`). Lecture des `.env` strictement passe par `growthcro/config.py`.

### 3.5 — print() dans pipelines

**457 occurrences** dans `growthcro/`, `moteur_gsg/`, `moteur_multi_judge/` (hors CLIs). Top files :
```
75  growthcro/cli/capture_full.py     (CLI — exception OK)
34  growthcro/capture/orchestrator.py (pipeline — NON-OK)
33  moteur_gsg/modes/mode_1/orchestrator.py
33  growthcro/gsg_lp/lp_orchestrator.py (legacy)
26  growthcro/capture/scorer.py
20  moteur_gsg/modes/mode_1_complete.py
19  moteur_gsg/core/pipeline_sequential.py
17  moteur_gsg/core/pipeline_single_pass.py
17  growthcro/cli/enrich_client.py    (CLI — exception OK)
16  moteur_multi_judge/orchestrator.py
```

Déjà tracé via la règle `INFO[print-in-pipeline]` du linter custom (34 fichiers dépassent le seuil). **Action future** : canoniser un module `growthcro/observability/logger.py` puis migrer top-10 — promouvoir la règle INFO → WARN.

### 3.6 — Duplication code

Pas de `pylint --duplicate-code` exécuté (lourd). Indicateurs indirects via vulture (5 scorers importent `get_verdict` sans l'utiliser → copier-coller depuis un template scorer). Recommandé à refaire en sprint dédié si Mathis veut chiffrer la duplication.

---

## Section 4 — Architecture-level

### 4.1 — Orphans (modules sans `imported_by` et non-entrypoint)

`audit_capabilities.py` (heuristique robuste) → **0 orphans HIGH**, **0 partial wired**, **0 potentially orph**.

Analyse YAML brute (`WEBAPP_ARCHITECTURE_MAP.yaml`) montre 88 "candidat orphans" mais une inspection révèle :
- ~40 fichiers `skills/site-capture/scripts/_archive_deprecated_*` qui devraient être déplacés vers `_archive/` racine (anti-pattern #10) — **à fixer hors-scope audit**
- ~30 scripts dans `scripts/` (test/check/migration utilitaires, run-via-shell)
- ~15 CLIs / orchestrators (run via `python -m` ou subprocess)
- ~3 modes GSG `mode_2_replace`, `mode_3_extend`, `mode_4_elevate`, `mode_5_genesis` (run-only via `moteur_gsg/orchestrator`)

**Note** : `growthcro/recos/orchestrator.py` apparaît comme "orphan" YAML mais est en fait l'entrypoint principal du combo "Audit run" — donc faux positif du YAML scan, pas un vrai orphan.

### 4.2 — High-coupling modules

| Module | depends_on | Concern |
|---|---:|---|
| `moteur_gsg/modes/mode_1_complete` | 15 | Orchestrator principal — 15 deps normales pour un orchestrator AD-1 axe #4. **OK**. |
| `growthcro/reality` (package) | 9 | `__init__.py` qui ré-exporte — pas un fichier de logique. **OK**. |
| `moteur_gsg/core/copy_writer` | 9 | Prompt assembly + LLM call — devrait split en `prompt_assembly.py` + `llm_call.py` (axes #1+#2 mélangés). **Action P3**. |
| `moteur_gsg/core/page_renderer_orchestrator` | 9 | Orchestrator HTML render — 137 LOC, contenu OK. **OK**. |
| `growthcro/reality/orchestrator` | 8 | Orchestrator Reality Layer — normal. **OK**. |
| `moteur_gsg/core/section_renderer` | 8 | Rendering composition — normal. **OK**. |
| `scripts/run_gsg_full_pipeline` | 8 | Script lanceur top-level — normal. **OK**. |

Seul `copy_writer.py` mérite un split mono-concern post-audit.

### 4.3 — Legacy status modules still imported

5 modules `status=legacy` ont `imported_by` non-vide. Tous contenus dans **2 îlots** :

**Îlot 1 — `growthcro/gsg_lp/` (V25.2 pipeline pre-V27)** :
- `brand_blocks` ← imported by `mega_prompt_builder`
- `data_loaders` ← imported by `lp_orchestrator`, `mega_prompt_builder`, `repair_loop`
- `lp_orchestrator` ← imported by NONE (orphan)
- `mega_prompt_builder` ← imported by `lp_orchestrator`
- `repair_loop` ← imported by `lp_orchestrator`

**Analyse** : cycle d'imports internes au package legacy `gsg_lp/`. Aucun importer externe au package. C'est un îlot scellé qui peut être déplacé vers `_archive/` à la prochaine fenêtre.

**Îlot 2 — `moteur_gsg/core/brief_v15_builder`** :
- imported by `moteur_gsg/modes/mode_2_replace` (un seul importer)

**Action P2** : migrer `mode_2_replace` vers le brief V2 canon (épic dédié) puis archiver `brief_v15_builder.py`.

### 4.4 — Empty-stage pipelines

3 pipelines dans `WEBAPP_ARCHITECTURE_MAP.yaml` ont 0 stages :
- `webapp` (generic placeholder)
- `webapp_v27` (V27 HTML statique — pipeline absent par design)
- `webapp_v28` (V28 Next.js — pipeline à définir post-Epic #6)

**Action** : ajouter stages à `webapp_v28` quand Epic #6 démarre. `webapp_v27` peut être marqué `status: legacy` dans le YAML pour clarifier.

---

## Section 5 — Skills `simplify` + `security-review` outputs

### 5.1 — `simplify` skill (manual run — skill nécessite un git diff)

Le skill `simplify` attend des changements via `git diff`. Cet audit étant read-only, j'ai fait l'inspection manuelle des 3 modules high-coupling :

**`moteur_gsg/modes/mode_1_complete.py` (556 LOC, 15 deps)** :
- Single concern : orchestration AD-1 axe #4 — légitime
- 4 functions, dont `run_mode_1_complete()` ~370 LOC (très longue mais cohérente)
- Aucun copy-paste flag, pas de stringly-typed code, pas de leaky abstractions évidentes
- 1 occurrence de `os` import (ligne 45) potentiellement inutile si non-utilisé — à vérifier
- **Verdict** : peut rester tel quel jusqu'à split formel via doctrine update

**`moteur_gsg/core/copy_writer.py` (376 LOC, 9 deps)** :
- **2 axes mélangés** : `build_copy_prompt` (axe #1 prompt assembly) + `call_copy_llm` (axe #2 API client) + `normalize_copy_doc` (axe #8 serialization)
- **Recommandation simplify** : split en 3 fichiers — `prompt_assembly.py` (build + fallback), `llm_call.py` (call_copy_llm), `serializers.py` (normalize_copy_doc, _strip_json_fences, _parse_json)
- Effort : ~2h. Impact : clean mono-concern.

**`moteur_gsg/core/page_renderer_orchestrator.py` (137 LOC, 9 deps)** :
- Single concern : orchestration rendu HTML — légitime
- 1 fonction `render_controlled_page()` simple
- Pas de simplify flag

### 5.2 — `security-review` skill (manual run — skill nécessite git diff)

Inspection manuelle basée sur bandit findings :

**HIGH severity — 4 false positives** : tous des cache-keys MD5/SHA1, non-crypto. Solution : `hashlib.md5(..., usedforsecurity=False)` (Python ≥3.9).

**MEDIUM severity — 2 vrais risques** :
1. **B608 SQL injection** dans `growthcro/reality/google_ads.py:71` et duplicate dans `skills/site-capture/scripts/reality_layer/google_ads.py:70` (legacy). Le `page_url` et `period_start/end` sont interpolés via f-string dans GAQL. Bien que l'input vienne d'audit interne, c'est un risque latent si l'orchestrator ouvre un endpoint API. **Recommandation** : whitelist `page_url` (URL validation regex), valider `period_*` comme dates ISO via Pydantic.

2. **B314 XML untrusted** dans `discover_pages_v25.py:125` — sitemap.xml de sites tiers parsés via `xml.etree.ElementTree.fromstring`. **Recommandation** : remplacer par `defusedxml.ElementTree.fromstring` (drop-in, secure-by-default).

**LOW severity (173)** : majoritairement B603 (subprocess sans `shell=True` — OK), B311 (random non-crypto — OK pour shuffling de prompts), B110 (try-except-pass — code defensive justifié dans 77 occurrences). À tagger en batch via `# nosec` ciblé si Mathis veut une review bandit propre.

**Verdict global security** :
- 0 hardcoded secrets
- 0 SQL injection critique (interne)
- 0 XSS (pas de templating user-input direct vers HTML — passe via `render_controlled_page` controlled)
- 4 HIGH bandit = 0 vrai HIGH après triage
- 2 vrais MEDIUM (SQL + XML) à corriger

---

## Section 6 — Recommended action plan (prioritized, ICE-scored)

| # | Action | Impact | Confidence | Ease | ICE | Effort |
|---|---|---:|---:|---:|---:|---|
| 1 | `ruff check --fix` sur tout l'arbre Python (339 fixes mécaniques) | 8 | 10 | 10 | **800** | 5min |
| 2 | Fix 2 B608 SQL injection (`google_ads.py` × 2) — paramétrer GAQL | 9 | 10 | 7 | **630** | 1h |
| 3 | Tag 4 HIGH bandit hash findings `usedforsecurity=False` | 5 | 10 | 10 | **500** | 15min |
| 4 | Remplacer 4 bare `except:` par `except Exception:` | 7 | 10 | 7 | **490** | 30min |
| 5 | Migrer `discover_pages_v25.py` XML → `defusedxml` | 7 | 10 | 7 | **490** | 30min |
| 6 | Canoniser `growthcro/observability/logger.py` + migrer top-3 pipelines | 7 | 9 | 6 | **378** | 1 sprint |
| 7 | Pydantic-iser contrats `moteur_gsg/core/visual_intelligence` (-13 mypy) | 9 | 8 | 5 | **360** | 1 sprint |
| 8 | Split `moteur_gsg/core/copy_writer.py` (3 fichiers mono-concern) | 6 | 9 | 6 | **324** | 2h |
| 9 | Archive `growthcro/gsg_lp/` legacy island (vers `_archive/`) | 6 | 9 | 6 | **324** | 1h |
| 10 | Déplacer `skills/site-capture/scripts/_archive_deprecated_*/` vers `_archive/` racine (anti-pattern #10) | 5 | 10 | 6 | **300** | 30min |

### Suggested sprint structure

**Sprint 1 — Hygiene quick-wins (~3h)** : actions #1, #3, #4, #5, #10. Net effect : ruff/bandit/anti-pattern findings divisés par ~2.

**Sprint 2 — Security fixes (~2h)** : actions #2 + tagger les 173 LOW en `# nosec` ciblés.

**Sprint 3 — Logging refactor (~1 sprint)** : action #6 + promouvoir `INFO[print-in-pipeline]` → `WARN`.

**Sprint 4 — Typage strict (~1 sprint)** : action #7 + viser `mypy --strict` sur 3 top fichiers, puis étendre.

**Sprint 5 — Mono-concern split (~3h)** : action #8 + archive #9.

---

## Annexes — Raw outputs

Tous les raw outputs sont dans `reports/raw/` :
- `ruff_full.txt` (658 lignes)
- `ruff_stats.txt` (11 lignes)
- `mypy_full.txt` (104 lignes)
- `bandit_full.json` (machine-readable, 192 issues)
- `bandit_summary.txt`
- `vulture_full.txt` (18 lignes)
- `eslint_per_app.txt` (vide = clean)
- `tsc_per_app.txt` (vide = clean)
- `tsc.txt` (23 path-resolution errors — faux positifs base config)
- `knip.txt` (28 lignes)
- `debt_todo_fixme.txt` (16 lignes)
- `env_reads_outside_config.txt` (2 lignes, tous dans le linter lui-même)
- `bare_except.txt` (4 lignes)
- `secrets_scan.txt` (vide)
- `print_in_pipeline.txt` (457 lignes)
- `architecture_audit.txt` (analyse YAML)
- `capabilities_audit.txt` (output `audit_capabilities.py` — 0 orphans)
- `lint_hygiene_baseline.txt` (output `lint_code_hygiene.py`)

### Tool versions
```
ruff      0.15.12
mypy      2.0.0
bandit    1.9.4
vulture   2.16
eslint    8.57.0 (next/core-web-vitals)
tsc       5.4.x
knip      latest (via npx --yes)
Python    3.13.1
Node      v25.9.0
```

### Out of scope (for separate sprints)
- `pylint --duplicate-code` deep dup analysis (heavy run, ~10min)
- `@axe-core/cli` accessibility check on V27/V28 webapp (waiting for live pages)
- `eslint-plugin-import-no-cycle` to detect import cycles (would catch `gsg_lp/` island)
- `madge` for visualizing dependency graph webapp side
- `pip-audit` for runtime deps CVE scan

---

**Fin du rapport. 13 commits incrémentaux dans la branche `task/code-audit-and-discovery` documentent chaque étape.**
