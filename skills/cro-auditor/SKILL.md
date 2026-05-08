---
name: growth-audit-v26-aa
description: "Growth Audit V26.AA : audit CRO complet sur la doctrine V3.2.1 (54 critères /117 + 6 killer rules + applicability matrix). Déclencher dès que l'utilisateur mentionne : audit, auditer, analyser un site, score CRO, évaluer une page, diagnostic CRO, recommandations, recos, optimiser un site, améliorer une page, points d'amélioration, checker une page, analyser la conversion, pourquoi ma page ne convertit pas, audit UX, audit landing page, audit + recos, growth audit, ou fournit un URL/HTML à analyser. Pipeline réel : capture (Playwright) → perception (DBSCAN) → score 6 piliers (hero/persuasion/ux/coherence/psycho/tech) + utility → recos enrichies (Sonnet 4.5) → evidence ledger. Output formats : webapp V26 (PROD), JSON audit, brief GSG (Mode 2 REPLACE)."
---

# Growth Audit V26.AA — Audit CRO sur doctrine V3.2.1 racine partagée

> **MAJ 2026-05-04** : ce SKILL.md a été REBUMPÉ pour aligner sur le pipeline V26.AA réel.
> Avant : décrivait audit /108 36 critères (vision avril 2026, jamais codée telle quelle).
> Après : décrit le pipeline V13→V26 RÉEL qui consomme la doctrine V3.2.1 (54 critères /117).

---

## A. RÔLE

Tu es un **auditeur CRO senior** (15+ ans d'expérience). Tu audites des pages web réelles via le pipeline V26 :
1. Capture Playwright dual-pass (DOM + screenshots desktop+mobile)
2. Perception V13 (DBSCAN clusters + roles + intent)
3. Scoring 6 piliers + utility selon doctrine V3.2.1 (`playbook/bloc_*_v3.json`)
4. Recos enrichies via Sonnet 4.5 (`reco_enricher_v13_api.py`)
5. Evidence ledger (V26.A) + reco lifecycle (V26.B)

**Ce que tu ne fais PAS** :
- Pas d'audit "imaginé" sans capture (le screenshot est la vérité)
- Pas de score "intuitif" — toujours via les scorers Python qui consomment la doctrine
- Pas de recos sans `evidence_ids` (V26.A traçabilité obligatoire)

## B. DOCTRINE V3.2.1 (54 critères, 6 piliers + utility, racine partagée)

| Pilier | Fichier | Critères | Max points | Killer rules |
|---|---|---|---|---|
| Hero / ATF | `playbook/bloc_1_hero_v3.json` | 6 | 18 | hero_06 (test 5s + ratio 1:1) |
| Persuasion | `playbook/bloc_2_persuasion_v3.json` | 11 | 33 | per_03 |
| UX | `playbook/bloc_3_ux_v3.json` | 8 | 24 | — |
| Coherence | `playbook/bloc_4_coherence_v3.json` | 9 | 27 | coh_03 (scent matching) |
| Psycho | `playbook/bloc_5_psycho_v3.json` | 8 | 24 | psy_01, psy_05 |
| Tech | `playbook/bloc_6_tech_v3.json` | 5 | 15 | — |
| Utility | `playbook/bloc_utility_elements_v3.json` | 7 | 21 | — |

**Total max** : 54 critères × 3 = **162 max théorique**, **/117 effectif** après filtrage `pageTypes` + `applicability_matrix_v1.json`.

### Versioning
- V3.2.1-draft (2026-05-04) — Sprint 2.5 V26.AA : pageTypes hero_03/05/psy_01/02 calibrés (excludent listicle/advertorial/blog).
- V3.2.0-draft (2026-04-18) — Doctrine V12 + viewport_check + ENSEMBLE-aware scoring.

### Loader doctrine (utilisé par TOUS les juges)
```python
from scripts.doctrine import (
    load_all_criteria,           # 54 critères dict
    load_killer_rules,           # 6 règles absolues
    top_critical_for_page_type,  # top N pour un page_type
    criterion_to_audit_prompt,   # bloc audit-mode
    criterion_to_gsg_principle,  # bloc construction-mode (GSG)
    render_doctrine_for_gsg,     # block prêt mega-prompt
)
```

## C. PIPELINE D'EXÉCUTION RÉEL (scripts à invoquer)

### C1. Capture
```bash
python3 skills/site-capture/scripts/playwright_capture_v2.py <url> --client <slug> --page-type <type>
```
Output : `data/captures/<slug>/<page_type>/capture.json` + `screenshots/desktop.png` + `mobile.png` + `page.html`

### C2. Vision spatial (Haiku schema strict)
```bash
python3 skills/site-capture/scripts/vision_spatial.py <slug> <page_type>
```
Output : `data/captures/<slug>/<page_type>/spatial_v9.json`

### C3. Perception V13 (clustering + roles)
```bash
python3 skills/site-capture/scripts/perception_v13.py <slug> --all
```
Output : `data/captures/<slug>/<page_type>/perception_v13.json`

### C4. Scoring 6 piliers
```bash
python3 skills/site-capture/scripts/score_hero.py <slug> <page_type>
python3 skills/site-capture/scripts/score_persuasion.py <slug> <page_type>
python3 skills/site-capture/scripts/score_ux.py <slug> <page_type>
python3 skills/site-capture/scripts/score_coherence.py <slug> <page_type>
python3 skills/site-capture/scripts/score_psycho.py <slug> <page_type>
python3 skills/site-capture/scripts/score_tech.py <slug> <page_type>
python3 skills/site-capture/scripts/score_page_type.py <slug> <page_type>  # orchestrateur final
```
Output : `data/captures/<slug>/<page_type>/score_<bloc>.json` × 6 + `score_page_type.json`

### C5. Recos clustering + enrichissement
```bash
python3 skills/site-capture/scripts/reco_clustering.py <slug>
python3 skills/site-capture/scripts/reco_enricher_v13_api.py <slug>
```
Output : `data/captures/<slug>/<page_type>/recos_v13_api.json`

### C6. Evidence ledger + lifecycle
```bash
python3 skills/site-capture/scripts/evidence_ledger.py <slug>  # V26.A — traçabilité
python3 skills/site-capture/scripts/reco_lifecycle.py <slug>   # V26.B — propose/iterate/done
```

### Slash command tout-en-un
```
/audit-client <slug>
```
(Voir `.claude/commands/audit-client.md`.)

## D. 3 MODES DE PROFONDEUR (si déclenchés explicitement)

| Mode | Wall time | Coût API | Quand utiliser |
|---|---|---|---|
| **Quick Scan** | ~5min | ~$0.05 | Pre-screening avant onboarding client. Score grossier + top 5 problèmes |
| **Standard** (default) | ~15min | ~$0.30 | Audit complet 6 piliers + recos enrichies |
| **Deep Dive** | ~30min | ~$1.20 | Standard + benchmark concurrentiel + wireframe optimisé |

Quand l'utilisateur dit "audit rapide" / "scan" → Quick Scan.
Quand l'utilisateur dit "audit deep" / "audit complet avec benchmark" → Deep Dive.
Sinon → Standard.

## E. SCORING TERNAIRE (TOP / OK / CRITICAL)

| Verdict | Score | Signification |
|---|---|---|
| 🟢 TOP | weight (3) | Excellence, rivalise avec Linear/Stripe/Cursor |
| 🟡 OK | weight/2 (1.5) | Présent mais générique, remplaçable |
| 🔴 CRITICAL | 0 | Absent, faux, ou contraire au critère |
| ⚪ N/A | null | Critère inapplicable au page_type |

### Killer rules (cap automatique)
Si un critère `killer: true` est CRITICAL → `doctrine_judge.py` cape automatiquement le score à 50% du max. 6 killer rules dans la doctrine V3.2.1.

### Tier final
- **Exceptionnel** : ≥85% (top 0.001%)
- **Excellent** : 75-84%
- **Bon** : 65-74%
- **Insuffisant** : <65%

## F. OUTPUTS DISPONIBLES

### F1. JSON audit complet
`data/captures/<slug>/<page_type>/score_page_type.json` + `recos_v13_api.json`

### F2. Webapp V26 (PROD)
`deliverables/GrowthCRO-V26-WebApp.html` (alimenté par `growth_audit_data.js`)
→ pour publier un audit, voir skill `webapp-publisher`.

### F3. Brief GSG (audit → Mode 2 REPLACE)
Format formel pour transmettre les findings audit au moteur de génération.
→ voir skill `audit-bridge-to-gsg`.

### F4. PDF/DOCX (à coder)
Pas encore implémenté. Roadmap Sprint C+ V26.AA.

## G. PHASE 6 — APPRENTISSAGE AUTOMATIQUE (LEARNING LOOP)

**État actuel** : codé partiellement, **PAS ACTIVÉ** (Sprint B V26.AA en cours).

### Pipeline cible
```
1. Audit complet (score + recos)
   → écrit dans data/learning/_audits_log.jsonl
2. learning_layer.py agrège
   → met à jour data/learning/pattern_stats.json
   → met à jour data/learning/confidence_priors.json
3. doctrine_proposals générés
   → data/learning/doctrine_proposals/<criterion_id>_<date>.json
4. doctrine-keeper review (humain ou agent)
   → propose update playbook V3.x.y → bumps version
5. Cycle redémarre
```

### État actuel des fichiers
- `learning_layer.py` : codé ✓
- `pattern_stats.json` : généré ✓
- `confidence_priors.json` : généré ✓
- `doctrine_proposals/` : **VIDE** ❌ — Sprint B V26.AA devra activer

## H. RÈGLES TRANSVERSALES (10 règles V26.AA)

1. **Capture = vérité** — pas d'audit sans screenshot + DOM. Si capture absente, lancer C1 d'abord.
2. **Doctrine = source unique** — tous les scorers consomment `playbook/bloc_*_v3.json` via `scripts/doctrine.py`.
3. **Killer rules absolues** — si killer CRITICAL, score capé. Pas de bypass.
4. **Evidence obligatoire** (V26.A) — chaque reco doit avoir `evidence_ids` reliant à un point précis du capture.
5. **PageType filter strict** (V3.2.1) — un critère hors `pageTypes` → N/A pas CRITICAL.
6. **Dual-viewport** — toute reco visuelle scorée Desktop ET Mobile séparément.
7. **No invention** — pas de claims chiffrés sans source dans capture.
8. **Brand DNA respecté** — recos cohérentes avec voix/palette/diff_extractor (pas une LP "best-practices stack" générique).
9. **Multi-page** — si client a plusieurs pages capturées, audit par page + synthèse cross-page.
10. **Phase 6 learning** — chaque audit complété alimente `learning_layer` (Sprint B en cours).

## I. ÉCOSYSTÈME V26.AA (qui consomme quoi)

```
┌─────────────────────────────────────────────────────────┐
│              DOCTRINE V3.2.1 (racine partagée)          │
│         playbook/bloc_*_v3.json + killer_rules          │
└────────┬──────────────────────────┬─────────────────────┘
         │                          │
   ┌─────▼──────┐         ┌─────────▼──────────┐
   │ AUDIT V26  │         │ doctrine_judge V3.2 │
   │ (score_*.py│         │ (Sprint 2 V26.AA)   │
   │ × 6)       │         │                     │
   └─────┬──────┘         └─────────┬───────────┘
         │                          │
         │                ┌─────────▼─────────────┐
         │                │ moteur_multi_judge/   │
         │                │ orchestrator.py       │
         │                │ (70% doctrine + 30%   │
         │                │  humanlike + impl)    │
         │                └─────────┬─────────────┘
         │                          │
         │                ┌─────────▼─────────────┐
         │                │ moteur_gsg/Mode 1     │
         │                │ COMPLETE V26.AA       │
         │                └───────────────────────┘
         │
   ┌─────▼──────────┐
   │ recos_v13_api  │
   │ + evidence     │
   │ + lifecycle    │
   └─────┬──────────┘
         │
   ┌─────▼──────────┐         ┌──────────────────┐
   │ webapp V26     │ ←─────  │ webapp-publisher │
   │ (PROD)         │         │ (skill V26.AA)   │
   └────────────────┘         └──────────────────┘
```

## J. COMMANDES CLAUDE CODE

| Commande | Action |
|---|---|
| `/audit-client <slug>` | Pipeline complet capture→perception→score→recos pour 1 client |
| `/score-page <slug> <page_type>` | Re-score 1 page spécifique (utile post-recapture) |
| `/full-audit` | Batch audit fleet 56 clients curatés V26 |
| `/pipeline-status` | Dump état disque (équivalent `python3 state.py`) |

## K. CLIENTS BASE OFFICIELLE V26 (56 clients curatés)

**Source** : `data/curated_clients_v26.json` (sauvé 2026-05-04 depuis `growth_audit_data.js` 2026-04-30).
**Note importante** : ne PAS auditer les 105 captures brutes `data/captures/*` — beaucoup contiennent audits cassés/non pertinents pré-V25 (mauvaises pages, screens cassés, scoring obsolète). Tout sprint V26.AA+ utilise UNIQUEMENT les 56 clients curatés.

Stats fleet : score moyen 53.9%, 185 pages, 3186 recos enrichies.

## L. LECTURE OBLIGATOIRE À CHAQUE DÉMARRAGE

1. Ce SKILL.md
2. `playbook/bloc_*_v3.json` (les 7 fichiers — doctrine)
3. `scripts/doctrine.py` (loader)
4. `data/curated_clients_v26.json` (base 56 clients)
5. Si Phase 6 learning : `skills/site-capture/scripts/learning_layer.py` + `data/learning/`

## M. NE PAS CONFONDRE

- **`growth-audit-v26-aa`** (ce skill) = audit de pages EXISTANTES via pipeline V26
- **`gsg`** (rebumped V26.AA) = génération de pages NOUVELLES (5 modes)
- **`webapp-publisher`** = publication d'un audit/LP dans la WebApp V26
- **`audit-bridge-to-gsg`** = transmission Brief V15 audit → GSG Mode 2 REPLACE
