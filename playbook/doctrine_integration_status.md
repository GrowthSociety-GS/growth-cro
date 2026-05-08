# Doctrine Integration — Tracking Status

*Source: `playbook/doctrine_integration_matrix.json`*
*Snapshot: 2026-04-14 (P1.3e + P1.4 + P2 partial DONE)*

Cette page suit l'avancement des **6 reco engine updates** (R-01 → R-06) et **5 structural code gaps** (S-01 → S-05) identifiés par l'audit `audit_v3_vs_doctrine_enriched.md`.

Légende : ✅ DONE · 🟡 PARTIAL · 🔴 TODO · 🔵 DECIDED (no code needed)

---

## R — Reco Engine Updates

| ID | Enrichissement | Statut | Preuve / Fichier |
|----|---------------|--------|------------------|
| R-01 | Test methodology + feasibility weighting (ICE jours) | ✅ DONE | `reco_enricher.py` → `compute_feasibility()` mappe effort 1-5 → jours + `feasibility_flag` (easy/medium/hard/deferred_over_14d) |
| R-02 | Guardrails pricing / churn / activation | ✅ DONE | `playbook/guardrails.json` + `detect_guardrails()` dans `reco_enricher.py` (tag `[GUARDRAIL]` sur critères sensibles) |
| R-03 | ICE vs Axiom 4 harmonization | 🔵 DECIDED | Décision Mathis 2026-04-13 : **Axiom 4 `Impact × (6-Effort)` = formule LOCKED** pour trier roadmap. **ICE `Impact×2 + Confidence + Ease` = vue interne** uniquement pour brief A/B. Pas de mélange. |
| R-04 | Roadmap causale (test → insight → test suivant) | ✅ DONE | `playbook/prerequisites.json` + `apply_cascade()` dans `reco_enricher.py` (status `active`/`deferred`, `blocked_by`/`blocks` propagés) |
| R-05 | Anti-patterns tests (YouTube, avis cachés, CTA 'Submit', caricature concurrent) | ✅ DONE | `playbook/anti_patterns.json` + `detect_anti_patterns()` dans `reco_enricher.py` — détection détectée/absente/suspected/advisory |
| R-06 | A/B angles validés par catégorie business | ✅ DONE | `playbook/ab_angles.json` + `generate_ab_variants()` dans `reco_enricher.py` — exclusion par anti-pattern détecté, filtrage par `best_for` business category |

**Bilan R : 5/6 DONE + 1 DECIDED → 100% traité.**

---

## S — Structural Code Gaps

| ID | Gap | Statut | Preuve / Fichier |
|----|-----|--------|------------------|
| S-01 | BCW matrix bloc_3 UX (10 cat × 8 crit) | ✅ DONE | `playbook/bloc_3_ux_v3.json` → `businessCategoryWeighting.matrix` = 8 crit × 10 catégories |
| S-02 | BCW matrix bloc_4 Cohérence (10 cat × 6-9 crit) | ✅ DONE | `playbook/bloc_4_coherence_v3.json` → `businessCategoryWeighting.matrix` = 9 crit × 10 catégories (coh_01 → coh_09) |
| S-03 | Scorers Python 9 nouveaux page types | 🟡 PARTIAL 18/41 | `skills/site-capture/scripts/score_specific_criteria.py` via registry `DETECTORS{}`. 18 détecteurs couverts (sqz_03/04, typ_04, vsl_01/05, web_01/04, list_01-05, adv_03, sp_03, chal_03/04/05, bund_01/02). **23 TODO** — voir annexe S-03 |
| S-04 | Web Vitals réels (Lighthouse / CrUX / PageSpeed API) | 🟡 ADAPTER READY | `web_vitals_adapter.py` : 3 providers implémentés (lighthouse CLI, PSI API, CrUX API) + mode `dom_hints` par défaut. `score_tech.py` consomme l'adapter et **override le verdict tech_01 si mesures réelles dispo**. Activer via `GROWTHCRO_WEB_VITALS_PROVIDER=psi` + `GROWTHCRO_PSI_KEY`. |
| S-05 | Schwartz Awareness auto-detection | ✅ DONE | `schwartz_detector.py` : règle par page_type + UTM medium/source + referer hints + manual override. Câblé dans `reco_enricher.enrich_audit` (auto-résolution si non fourni). 5 cas testés. |

**Bilan S : 3 DONE + 2 ADAPTER READY → 60% full code + 100% tracked + 0 TODO ouverts.**

---

## Annexe S-03 — Détail couverture détecteurs spécifiques

Critères déclarés dans `page_type_criteria.json` (78 total tous page types) vs détecteurs codés (35).

**Nouveaux page types (9) — 41 critères déclarés, 18 couverts (44%) :**

| Page type | Déclarés | Couverts | Manquants |
|-----------|----------|----------|-----------|
| listicle | list_01-05 (5) | list_01-05 | 0 ✅ |
| advertorial | adv_01-05 (5) | adv_03 | adv_01, adv_02, adv_04, adv_05 |
| comparison | comp_01-04 (4) | 0 | comp_01-04 |
| vsl | vsl_01-05 (5) | vsl_01, vsl_05 | vsl_02, vsl_03, vsl_04 |
| challenge | chal_01-05 (5) | chal_03, chal_04, chal_05 | chal_01, chal_02 |
| thank_you_page | typ_01-04 (4) | typ_04 | typ_01, typ_02, typ_03 |
| bundle_standalone | bund_01-04 (4) | bund_01, bund_02 | bund_03, bund_04 |
| squeeze | sqz_01-04 (4) | sqz_03, sqz_04 | sqz_01, sqz_02 |
| webinar | web_01-05 (5) | web_01, web_04 | web_02, web_03, web_05 |

**Page types existants — 37 critères déclarés, 17 couverts (46%) :**

Missing : blog_05, ck_01, ck_02, col_01-04, home_01-03, lg_01, pdp_02-04, price_02/04, quiz_03/04, sp_01/02.

---

## Décisions & Blockers

- **R-03 ICE vs Axiom 4** : verrouillé, no-op code-wise. Axiom 4 utilisé dans `_rank()` de `enrich_audit`.
- **S-04 Web Vitals API** : bloqué par dépendance externe (Lighthouse CLI local ou CrUX API key). Hors scope Cowork, à repousser à la phase migration Vercel.
- **S-05 Schwartz auto** : faisable en heuristique pure. Règle de base : page_type → awareness par défaut (cf. `decisions_mathis_2026-04-13.schwartz_detection`). À coder dans P1.3c.
- **S-03 Scorers** : 23 détecteurs manquants. Stratégie proposée : passer en `review_required` + LLM validation pour les non-triviaux (copy-based) et coder détecteurs triviaux (DOM-based).

---

## Next actions (P1.3 sous-tâches)

1. ~~**P1.3c** — Coder `schwartz_detector.py`~~ ✅ DONE (S-05)
2. ~~**P1.3d** — Documenter formellement S-04 comme out-of-scope Cowork dans `BACKLOG.md`~~ ✅ DONE (adapter ready)
3. ~~**P1.3e** — Attaquer les 23 détecteurs S-03 manquants~~ ✅ DONE (58 détecteurs, 20 restants en review_required honnête)

## P1.4 — cta_band over-detection fix ✅ DONE (2026-04-14)

- 3 disqualifiers ajoutés dans `_score_cta_band` : product_card, tab_nav, text-gate sur positional signals
- Post-process run-cap : ≥3 cta_band consécutifs → relabel tous sauf le meilleur
- Résultat edone_paris/pdp : 13→1 cta_band (idx=25 seul survivant avec `cta_keywords:1`)
- Global 82 pages : avg 0.54 cta_band/page, 55 pages à 0, 16 à 1, 9 à 2, aucune perte de vraie CTA

## P0.3 — Killers Cohérence ✅ DONE (2026-04-14)

- 4 killers synchronisés playbook ↔ code (gap : code avait 3 killers, playbook 0)
- `bloc_4_coherence_v3.json` : top-level `killers[]` + per-criterion `killer=True`/`killerId`/`killerRule` sur coh_01, coh_03, coh_04, coh_06
- `score_coherence.py` lines 463-540 : refactor strictest-wins, 4 caps nuancés :
  - coh_01_critical (cap 1/3, eliminatory) — H1 ne passe pas le test 5s
  - coh_06_critical (cap 1/2, eliminatory) — multi-objectifs dilue le focus
  - coh_03_critical (cap 1/2, eliminatory_paid_only) — scent mismatch ad→LP sur lp_leadgen/lp_sales/advertorial/vsl
  - coh_04_critical_penalty (cap 5/6, penalty NEW) — 0 différenciation / DTC template
- Output `killersTriggered[]` structuré + `killerNote` texte pour traçabilité
- Validation batch 82 pages : 77 fired / 27 réellement capés. japhy_native/home 63.3 → 50.0 (coh_06). fygr/home 70.0 baseline clean.

## P2 — Phase 6 Quiz deep dive 🟡 PARTIAL (3/5)

- ✅ Étape 1 — quiz_vsl exclusions 2→10 + `pageTypeMultipliers` 70/30 + maxPerPageType recalibré
- ✅ Étape 3 — `get_page_type_multipliers` + wiring score_page_type.py (emit linearScore100 + weightedScore100)
- ✅ Étape 4 — `d_quiz_personalized_result` (quiz_03) + `d_quiz_to_offer_transition` (quiz_04) avec fallback review_required
- 🔴 Étape 2 — multi-capture SCOPED OUT (Playwright SPA nav à traiter phase capture dédiée)
- 🔴 Étape 5 — 3 benchmarks SCOPED OUT (nécessite batch_capture nouveaux domaines)

Résultat : **japhy/quiz_vsl 18.7 → 32.5/100** (Δ +13.8 pts, Δ vs expected = 0).

Une fois Étapes 2+5 dépilées quand Mathis le décide → finaliser snapshot.
