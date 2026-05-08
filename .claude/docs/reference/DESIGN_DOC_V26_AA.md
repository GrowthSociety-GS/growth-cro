# DESIGN DOC V26.AA — Architecture cible GrowthCRO post-pivot doctrine racine

> **Statut** : DRAFT à valider par Mathis avant tout code en next session.
> **Date** : 2026-05-03
> **Auteur** : Claude Opus 4.7 (co-créateur)
> **Trigger** : insight Mathis "doctrine V3.2 doit être racine partagée Audit + GSG"

---

## 1. Pourquoi ce design (problème à résoudre)

### Faille architecturale identifiée

V26.Z avait 3 systèmes de qualité parallèles qui ne se parlaient pas :
- **Audit Engine** consomme `playbook/bloc_*_v3.json` (54 critères V3.2 — notre IP depuis V13)
- **GSG Defender** consomme `eval_grid.md` /135 (grille inventée pour gsg_self_audit)
- **GSG Humanlike** consomme 8 dimensions humaines (encore une grille inventée)

→ 3 ré-inventions parallèles. La doctrine V3.2 (54 critères + 6 killer_rules + thresholds + frameworks) — accumulation de 6 mois de travail CRO — était **sous-utilisée par 50%** côté GSG.

### Test empirique du 2026-05-03

| Approche | Humanlike | Coût |
|---|---|---|
| V26.Z BESTOF Premium (4 stages, 3500 LoC) | 66/80 | $1.50 |
| **gsg_minimal v1** (1 prompt 3K + règle renoncement) | **70/80** ⭐ | $0.02 |
| ChatGPT GlobalFlow (1 prompt manuel) | 53/80 | manuel |

→ **Le pipeline complexe V26.Z a été battu par 1 prompt court avec doctrine de renoncement.** La complexité architecturale ≠ la qualité.

### Insight Mathis (le pivot)

La doctrine V3.2 doit être à la **racine partagée**. Audit consomme pour critiquer, GSG consomme pour CRÉER, multi-judge consomme pour SCORER — **avec les MÊMES règles**.

Et Mathis n'accepte pas l'industrialisation de masse : *« cet outil doit sortir la perfection dès le départ »*. Critère gate = **perfection unitaire**, pas moyenne fleet.

---

## 2. Architecture cible (validée par Mathis)

```
GrowthCRO ROOT
│
├── doctrine/  (DÉJÀ : scripts/doctrine.py + playbook/)
│   ├── playbook/
│   │   ├── bloc_1_hero_v3.json (6 critères)
│   │   ├── bloc_2_persuasion_v3.json (11 critères)
│   │   ├── bloc_3_ux_v3.json (8 critères)
│   │   ├── bloc_4_coherence_v3.json (9 critères)
│   │   ├── bloc_5_psycho_v3.json (8 critères)
│   │   ├── bloc_6_tech_v3.json (5 critères)
│   │   ├── bloc_utility_elements_v3.json (7 critères)
│   │   ├── killer_rules.json (6 règles absolues)
│   │   ├── anti_patterns.json
│   │   ├── thresholds_benchmarks.json
│   │   ├── page_type_criteria.json
│   │   └── guardrails.json
│   └── doctrine.py (loader exposant top_critical_for_page_type, render_doctrine_for_gsg, etc.)
│
├── moteur_audit/  (V26 existant, INCHANGÉ — consume doctrine déjà)
│   ├── capture (Playwright dual-pass)
│   ├── perception (DBSCAN clusters)
│   ├── score_<bloc>.py × 6 + score_page_type.py
│   ├── reco_clustering + reco_enricher_v13_api
│   └── evidence_ledger + reco_lifecycle (V26.A+B)
│
├── moteur_gsg/  (À CRÉER PROPREMENT)
│   │
│   ├── core/
│   │   ├── brand_intelligence/
│   │   │   ├── brand_dna_extractor.py (V29 réutilisé, GARDÉ)
│   │   │   ├── brand_dna_diff_extractor.py (E1 réutilisé, GARDÉ)
│   │   │   └── creative_director.py (3 routes, GARDÉ optionnel selon mode)
│   │   │
│   │   ├── prompt_assembly/
│   │   │   ├── doctrine_block_builder.py (consume doctrine.render_doctrine_for_gsg)
│   │   │   ├── brand_block_builder.py (consume brand_dna + diff)
│   │   │   └── mode_aware_assembly.py (orchestre le tout selon mode)
│   │   │
│   │   └── pipeline/
│   │       ├── single_pass.py (1 prompt court — equivalent gsg_minimal v1, default)
│   │       ├── sequential.py (4 stages, GARDÉ optionnel — Mode 2 refonte profonde)
│   │       └── best_of_n.py (3 routes parallel, GARDÉ + recâblé)
│   │
│   ├── modes/  (les 5 situations type)
│   │   ├── mode_1_complete.py     (URL site + nouvelle LP type X)
│   │   ├── mode_2_replace.py      (URL site + URL page à refondre)
│   │   ├── mode_3_extend.py       (URL site + concept nouveau)
│   │   ├── mode_4_elevate.py      (URL site + URLs inspirations)
│   │   └── mode_5_genesis.py      (brief seul, pas d'URL)
│   │
│   └── orchestrator.py  (API unifiée : generate_lp(mode, client, page_type, ...))
│
├── moteur_multi_judge/  (À UNIFIER sur doctrine V3.2)
│   ├── judges/
│   │   ├── doctrine_judge.py (NEW — utilise les 54 critères V3.2, /117 max)
│   │   ├── humanlike_judge.py (V26.Z gardé, en complément sensoriel)
│   │   └── implementation_check.py (V26.Z bug-fix gardé universel)
│   └── orchestrator.py (run_multi_judge avec doctrine + humanlike + impl_check)
│
└── moteur_reality/  (V26.C activable post-MVP, Mathis env vars Catchr/Meta/GA/Shopify/Clarity)
```

---

## 3. Spec détaillée des 5 modes GSG

### Mode 1 — COMPLETE (default UX webapp, ~30-40% des cas)
**Use case** : Client a un site existant. Veut une nouvelle LP type X (PDP, listicle, advertorial...) qui n'existe pas encore dans son écosystème.

**Inputs** :
- `client_url` (obligatoire)
- `page_type` (obligatoire — `lp_listicle`, `pdp`, `lp_sales`, ...)
- `brief` (3 questions courtes : objectif / audience / angle)

**Pipeline interne** :
1. `brand_dna_extractor(client_url)` → brand DNA + diff (Phase 3 Fix)
2. `doctrine.top_critical_for_page_type(page_type, n=7)` → top critères
3. Optionnel : `creative_director(brand_dna, page_type)` → 1 route choisie
4. `prompt_assembly` → prompt court ~7-10K chars (brand + diff + doctrine principles + creative route + brief)
5. `pipeline.single_pass()` → 1 call Sonnet → HTML
6. `auto_fix_runtime(html)` → patch rendering bugs
7. `multi_judge(html, page_type)` → doctrine_judge + humanlike + impl_check
8. Si score < threshold → `pipeline.best_of_n()` (3 variantes parallel) ou `repair_loop`

**Output** :
- HTML LP livrable
- Audit JSON (doctrine_judge V3.2 par critère + humanlike + impl_check)
- Telemetry (tokens, coût, temps)

**Coût attendu** : ~$0.10-0.15 (single_pass), ~$1.00-1.50 (best_of_n si triggered)

### Mode 2 — REPLACE (~25-30%)
**Use case** : Refonte d'une page existante (alternative meilleure).

**Inputs** :
- `client_url`
- `page_to_replace_url` (obligatoire — la page à refondre)
- `page_type`
- `brief` court

**Pipeline interne** :
1. `brand_dna_extractor(client_url)` → brand DNA + diff
2. `audit_engine(page_to_replace_url)` → score actuel + recos V3.2
3. `doctrine.top_critical_for_page_type(page_type, n=7)` → top critères
4. Optionnel : `creative_director` (route Premium ou Bold pour upgrade)
5. `prompt_assembly` enrichi avec **gaps audit** comme contraintes ("hero_01 actuellement à 1.5/3 — la nouvelle version DOIT atteindre 3/3 en faisant X")
6. `pipeline.sequential()` (4 stages — pour cas complexes type refonte) OU `single_pass`
7. `auto_fix + multi_judge`

**Output** : HTML + audit comparatif (avant/après) + delta scores doctrine V3.2

### Mode 3 — EXTEND (~15-20%)
**Use case** : Site existant, mais on crée un concept NOUVEAU pas dans l'existant (ex: advertorial alors que site n'en a pas).

**Inputs** :
- `client_url`
- `concept` (ex: "advertorial Editorial Magazine")
- `brief`

**Pipeline interne** : Identique Mode 1 mais avec `concept` qui guide creative_director vers une route adaptée au concept (vs cohérence stricte avec site existant).

### Mode 4 — ELEVATE (~5-10%)
**Use case** : Challenger la DNA actuelle. Créer une alternative encore plus quali en proposant URLs d'inspirations supplémentaires.

**Inputs** :
- `client_url` (brand actuel)
- `inspiration_urls` (1-5 URLs de marques de référence)
- `page_type`
- `brief`

**Pipeline interne** :
1. `brand_dna_extractor(client_url)` → brand DNA actuel
2. `brand_dna_extractor(inspiration_urls)` → brand DNA cible évolué
3. `creative_director` reçoit BOTH (current + target) → route qui fait le pont
4. `prompt_assembly` injecte gap actuel→cible
5. `pipeline.sequential` ou `best_of_n` (cas le plus créatif, mérite 3 variantes)

### Mode 5 — GENESIS (<5%)
**Use case** : Rien n'existe (nouvelle brand). Brief seul, pas d'URL.

**Inputs** :
- 8-12 questions structurées (brand_name, category, audience, offer, CTA, proofs, niveau visuel, contraintes, voice, palette préférence, références)
- Optionnel : uploads assets (logo, photos, etc.)

**Pipeline interne** :
1. `creative_director` Mode Bold (puisque rien à respecter, on peut oser)
2. `doctrine.top_critical_for_page_type(page_type, n=7)`
3. `prompt_assembly` minimal
4. `single_pass` ou `best_of_n` (sans contraintes brand existant, on peut explorer)

---

## 4. Spec multi-judge unifié sur doctrine V3.2

### `doctrine_judge.py` (NEW V26.AA)

**Remplace** : Defender + Skeptic (eval_grid /135 inventé).

**Input** : HTML + client + page_type
**Output** : audit JSON par critère V3.2 (54 critères, scores ternaires 0/1.5/3)

**Logique** :
1. Charger les 54 critères via `doctrine.load_all_criteria()`
2. Filtrer par page_type via `_criterion_applies_to_page_type()`
3. Pour chaque critère applicable :
   - Construire prompt avec `criterion_to_audit_prompt(criterion_id)`
   - Score Sonnet (0/1.5/3)
   - Capturer evidence (extrait HTML) + rationale
4. Calculer total + total_max + tier (Exceptionnel ≥85%, Excellent 75-84%, Bon 65-74%, Insuffisant <65%)
5. Détecter killer_rules violées → cap automatique
6. Output structuré identique à eval_grid mais sur grille V3.2

**Coût attendu** : ~$0.15-0.20 par audit (54 critères × Sonnet, possible parallélisation par bloc).

### `humanlike_judge.py` (V26.Z gardé en complément)

Inchangé. Reste comme dimension complémentaire (8 dimensions humaines /80 — concrétude H2, signature nommable, AI patterns détectés).

### `implementation_check.py` (V26.Z gardé)

Inchangé. Sanity check Python (counter à 0, reveal-pattern, opacity 0).

### Orchestrator multi-judge V26.AA

```python
def run_multi_judge(html_path, client, page_type):
    impl = implementation_check(html)  # Étape 0 — pénalité auto si critical

    doctrine_audit = doctrine_judge(html, client, page_type)  # 54 critères V3.2
    humanlike_audit = humanlike_judge(html, client)  # complémentaire

    # Final score : pondération
    final = 0.7 * doctrine_audit["total_pct"] + 0.3 * humanlike_audit["total_pct"]
    final -= impl_penalty  # -25pct si critical

    return {
        "final_score_pct": final,
        "doctrine": doctrine_audit,
        "humanlike": humanlike_audit,
        "implementation": impl,
        "verdict": tier(final),
    }
```

---

## 5. Mapping ancien → nouveau (migration progressive)

| V26.Z avant | V26.AA après | Action |
|---|---|---|
| `gsg_generate_lp.py` (mega-prompt 53K) | `moteur_gsg/orchestrator.py` | REFACTOR (décomposer build_mega_prompt) |
| `build_mega_prompt()` | `modes/mode_<X>/prompt_assembly()` | RÉ-ARCHITECTURE par mode |
| `--auto-repair` flag | `pipelines/with_repair.py` | EXTRACT |
| `--sequential` flag | `pipelines/sequential.py` | EXTRACT (Mode 2/4 only) |
| `--creative-mode` flag | intégré par mode | INTÉGRER |
| `gsg_self_audit.py` (eval_grid /135) | **[ARCHIVÉ]** | DELETE après migration |
| `gsg_multi_judge.py` Defender + Skeptic | `doctrine_judge.py` | REPLACE |
| `gsg_multi_judge.py` orchestrateur | `moteur_multi_judge/orchestrator.py` | REFACTOR |
| `gsg_humanlike_audit.py` | `moteur_multi_judge/judges/humanlike.py` | MOVE |
| `fix_html_runtime.py` | `moteur_multi_judge/judges/implementation.py` | MOVE |
| `gsg_minimal v1/v2` | **[ARCHIVÉS]** | DELETE (tests historiques utiles, plus utiles maintenant) |

---

## 6. Plan d'exécution séquentiel (7 étapes)

| Étape | Description | Estimation | Dépendance |
|---|---|---|---|
| **1** | **Design doc validé Mathis** | 1-2h | Cette doc — à valider avant tout code |
| 2 | `doctrine_judge.py` (54 critères V3.2 par bloc, parallélisable) | 2-3h, ~$0.10 | doctrine.py (Sprint 1 OK) |
| 3 | `moteur_gsg/orchestrator.py` + `mode_1_complete.py` (premier mode) | 1 jour, ~$0.50 | étape 2 |
| 4 | `mode_2_replace.py` + `mode_3_extend.py` + `mode_4_elevate.py` | 1-2 jours, ~$2 | étape 3 |
| 5 | `mode_5_genesis.py` | 0.5 jour, ~$0.30 | étape 4 |
| 6 | Validation cross-client (Weglot + Japhy + 1 SaaS premium) | 1 jour, ~$5 | étape 5 |
| 7 | Archive `gsg_minimal v1/v2`, `gsg_self_audit.py`, `eval_grid.md` + commit propre | 1h | étape 6 |

**Total estimé** : 5-7 jours dev + ~$8-10 API.

---

## 7. Critères de validation (gates)

### Gate après étape 2 (doctrine_judge)
- [ ] Score les 4 LPs existantes (V26.Z BESTOF / minimal v1 / minimal v2 / ChatGPT GlobalFlow)
- [ ] Cohérence avec humanlike actuel (corrélation > 0.6)
- [ ] Détecte killer_rules violations correctement
- [ ] Coût < $0.25 par audit

### Gate après étape 3 (Mode 1 fonctionnel)
- [ ] Mode 1 génère LP Weglot avec doctrine V3.2 injectée
- [ ] doctrine_judge sur output Mode 1 ≥ 70% sur les 7 top critères du page_type
- [ ] Implementation Check ok
- [ ] Coût < $0.20 par run single_pass

### Gate finale après étape 6 (cross-client)
- [ ] Mode 1 marche sur 3 clients distincts (Weglot SaaS + Japhy DTC + 1 premium)
- [ ] doctrine_judge moyenne ≥ 75% sur les 3
- [ ] **Critère Mathis** : "perfection unitaire dès le 1er run" — Mathis valide visuellement les 3 LPs
- [ ] Si OK → archive l'ancien (étape 7) et release V26.AA

---

## 8. Ce qu'on ÉVITE explicitement (anti-patterns identifiés)

### Anti-pattern 1 : retomber dans le mega-prompt sursaturé
**Symptôme** : prompt > 15K chars, Sonnet coche les cases au lieu de créer.
**Garde-fou** : limite stricte 10K chars max par prompt unique. Sinon découper en pipeline.

### Anti-pattern 2 : ré-inventer une grille de qualité différente de V3.2
**Symptôme** : "j'ai créé une grille X de 45 critères pour Y..."
**Garde-fou** : tout juge consomme `doctrine.py`. Pas de eval_grid.md.

### Anti-pattern 3 : industrialiser sur 51 clients avant validation unitaire
**Position Mathis explicite** : *« cet outil doit sortir la perfection dès le départ »*.
**Garde-fou** : Phase 4 validation = 3 clients distincts qualité absolue, pas batch.

### Anti-pattern 4 : oublier le humanlike judge ou le supprimer
**Risque** : tomber dans la complaisance grille audit (V26.Z avait ce piège côté Defender).
**Garde-fou** : humanlike garde son poids 30% dans final_score, comme contre-poids sensoriel.

### Anti-pattern 5 : ajouter des micro-règles sans test empirique
**Position Mathis explicite** : *« arrêter d'ajouter des micro-règles, recentrer sur création »*.
**Garde-fou** : avant tout ajout de règle, lancer un test mesurant le delta humanlike. Si pas de gain → pas d'ajout.

### Anti-pattern 6 : coder avant design doc
**3 mea culpa session 2026-05-03** : à chaque fois j'ai recommencé à coder vite.
**Garde-fou** : ce design doc validé Mathis = précondition tout sprint code suivant.

---

## 9. Questions ouvertes (à résoudre avec Mathis)

### Q1 — Pondération doctrine vs humanlike dans final_score
Ma proposition : 70% doctrine + 30% humanlike. Mathis valide ?

### Q2 — Killer_rules cap : automatique ou warning ?
Si killer rule violée → cap score automatique (V26.Z faisait ça côté audit). Garder pour GSG ?

### Q3 — Best-of-N par défaut ou opt-in ?
Mode 1 default : single_pass uniquement. Best-of-N opt-in si client demande premium ($1.50 vs $0.15).

### Q4 — UX webapp : dropdown 5 modes ou wizard ?
Pour un futur SaaS : dropdown clair sur 5 modes ou wizard "réponds à ces questions, on choisit pour toi" ?

### Q5 — Mode 2 (REPLACE) : on génère 1 alternative ou 3 ?
Mode REPLACE = refonte. Plus de risque de rejet client. Best-of-N par défaut ici ? Ou laisser au client de choisir ?

### Q6 — Reality Layer integration timing
Phase 6 dans plan V26.Z. À garder ? Activer après Mode 1 fonctionnel pour mesurer outcome réel ?

---

## 10. Demande explicite à Mathis

**Avant tout code en next session :**
1. Lis ce design doc complet
2. Réponds aux 9 questions ouvertes (au moins Q1-Q5)
3. Valide ou challenge l'architecture cible
4. Valide le mapping ancien → nouveau
5. Valide le plan d'exécution 7 étapes

**Une fois validé, je code étape 2 (doctrine_judge) en premier.**

---

**FIN DU DESIGN DOC — V26.AA est en attente de validation Mathis pour démarrer.**
