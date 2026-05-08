# Rescue Decision V26.AH — 2026-05-04

> Day 7 du plan de sauvetage. But : décider si le rollback suffit, ce qui reste gelé, et comment reprendre sans repartir dans une usine à prompts.

## 0. Décision

Baseline stable retrouvée : oui, techniquement.

Baseline product-grade : non.

Donc la décision est :

1. Ne pas rollback plus ancien par défaut.
2. Garder V26.AH comme baseline de survie GSG.
3. Ne pas reconstruire le GSG sur le pipeline V26.AF/AG séquentiel.
4. Reprendre la roadmap par séparation produit : Audit/Reco d'abord, Webapp honnête ensuite, GSG propre séparé.

## 1. Bilan des 7 Jours

| Jour | Objectif | Résultat |
|---|---|---|
| 1 | Scoring resurrection | OK : dépendances archivées restaurées, Weglot `batch_rescore.py --only weglot` OK |
| 2 | Recos Engine | OK : Weglot 5 pages, 106 recos OK, quality audit durci |
| 3 | Webapp statique honnête | OK : panel officiel 56 clients, statuts modules actifs/inactifs/frozen |
| 4 | GSG rollback | OK : `complete` route vers Mode 1 V26.AA restauré, sequential expérimental |
| 5 | GSG minimal fonctionnel | OK : `minimal_guards.py`, CTA/langue/fonts/preuves déterministes, Weglot PASS |
| 6 | Séparation architecture | OK : `architecture/PRODUCT_BOUNDARIES_V26AH.md` |
| 7 | Décision finale | OK : ce document |

## 2. Commits de Référence

| Commit | Rôle |
|---|---|
| `828a752` | Restore scoring dependencies |
| `777bffe` | Harden recos quality audit |
| `deaffcb` | Static webapp from curated panel |
| `60642f2` | Restore Mode 1 rollback default |
| `83270c8` | Add deterministic minimal GSG gates |
| `f972677` | Manifest Day 5 changelog |

## 3. Rollback Minimal

### Niveau 0 — Garder V26.AH

Décision recommandée. Le runtime minimal passe :

```bash
python3 -B -m py_compile \
  moteur_gsg/core/minimal_guards.py \
  moteur_gsg/core/prompt_assembly.py \
  moteur_gsg/modes/mode_1_complete.py \
  moteur_gsg/orchestrator.py
```

Gate de preuve :

```bash
python3 -B - <<'PY'
from pathlib import Path
from pprint import pprint
from scripts._test_weglot_listicle_V26AE import WEGLOT_BRIEF_V2
from moteur_gsg.core.brief_v2_validator import parse_brief_v2_from_dict
from moteur_gsg.core.minimal_guards import audit_minimal_html, build_minimal_constraints
from moteur_gsg.core.brand_intelligence import load_brand_dna

brief = parse_brief_v2_from_dict(WEGLOT_BRIEF_V2).to_legacy_brief()
html = Path('deliverables/weglot-lp_listicle-V26AH-MINIMAL.html').read_text()
constraints = build_minimal_constraints('weglot', 'lp_listicle', brief, load_brand_dna('weglot'), target_language='FR')
pprint(audit_minimal_html(html, constraints))
PY
```

Attendu : `pass: True`.

### Niveau 1 — Revenir au Day 4 V26.AG

Seulement si `minimal_guards.py` bloque trop agressivement une génération validée.

```bash
git checkout 60642f2 -- \
  moteur_gsg/core/prompt_assembly.py \
  moteur_gsg/modes/mode_1_complete.py \
  moteur_gsg/orchestrator.py \
  skills/gsg/SKILL.md
```

Puis générer :

```bash
python3 -m moteur_gsg.orchestrator \
  --mode complete \
  --client weglot \
  --page-type lp_listicle \
  --objectif "Convertir trial gratuit" \
  --audience "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p..." \
  --angle "Listicle founder-led Weglot" \
  --skip-judges \
  --save-html deliverables/weglot-lp_listicle-V26AG-MODE1-ROLLBACK.html
```

Risque connu : CTA anglais, fonts slop, chiffres pseudo-sourcés.

### Niveau 2 — Revenir au fichier archivé V26.AA

Seulement si le runtime actuel casse complètement.

```bash
cp _archive/legacy_pre_v26ae_2026-05-04/moteur_gsg_legacy/mode_1_complete.py \
  moteur_gsg/modes/mode_1_complete.py
```

Puis réappliquer manuellement le routing `complete` dans `moteur_gsg/orchestrator.py`.

Risque connu : baseline plus vivante mais moins contrôlée, aucune preuve déterministe.

## 4. Ce Qui Reste Gelé

1. `pipeline_sequential.py` comme default.
2. `mode_1_persona_narrator.py` comme default.
3. GSG avec mega-prompt > 8K dans persona narrator.
4. GSG qui ingère tout `design_grammar` en texte.
5. AURA comme gros bloc prompt.
6. Multi-judge comme gate bloquant pendant génération.
7. Learning Layer qui modifie doctrine automatiquement.
8. Reality Layer qui pondère score sans outputs réels validés.
9. Webapp qui présente modules inactifs comme actifs.
10. Batch GSG multi-clients.

## 5. Ce Qui Peut Continuer

1. Audit Engine sur panel officiel 56 clients.
2. Recos Engine avec quality audit durci.
3. Webapp statique honnête.
4. GSG minimal V26.AH pour smoke tests unitaires.
5. Multi-judge en audit post-run.
6. Learning proposals en lecture/review.
7. Reality Layer sur 1 client pilote.
8. GEO en pilote dès que clés dispo.
9. Brand DNA + Design Grammar en lecture, pas en méga-prompt.
10. Golden sites comme pattern library, pas comme prompt dump.

## 6. Plan Exécutable Après Sauvetage

### Semaine 1

1. Schema global vert : fait post-rescue (`SCHEMA/validate_all.py` = 3325 files all passing).
2. `score_site.py` modernisé : fait post-rescue, agrégation depuis `score_page_type.json` avec fallback legacy.
3. Recos quality audit 3 clients : fait post-rescue (`weglot`, `seazon`, `captain_contrat`) ; seul Captain Contrat nécessite correction grounding ciblée.
4. Créer un protocole Reality Layer Kaiju avec env vars et outputs attendus.
5. Construire un mini-spec GSG planner déterministe : sections, proofs, CTA, visual tokens.

### Mois 1

1. Webapp cible : décider si Next/Supabase démarre maintenant ou après Reality pilote.
2. GSG propre : séparer planner, copy LLM, renderer, audit post-run.
3. Learning : review humaine des 69 proposals, puis doctrine V3.3 en commit isolé.
4. Reality : au moins 1 client avec `reality_layer.json` page-level.
5. Experiment : convertir 5 recos P0 en specs testables.

## 7. Go / No-Go

Go pour reprendre le produit réel :

- Audit/Reco/Webapp : oui.
- GSG minimal smoke : oui.
- GSG reconstruction : oui, mais uniquement après mini design doc validé.
- GSG "amélioration prompt" : non.
- Batch GSG : non.
- Learning auto doctrine : non.

## 8. Phrase à Garder

Le sauvetage a réparé le runtime, pas inventé une stratégie magique.

La suite gagnante : un système qui décide la structure, les preuves et le rendu ; le LLM écrit seulement ce qu'il est bon à écrire.
