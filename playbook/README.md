# GrowthCRO — Playbook V3 unifié

**Objectif :** un seul socle de vérité CRO qui fusionne les 4 couches de savoir existantes (Notion Checklist CRO, skill cro-auditor, cro_criteria_v2, architecture + audits validés) en une grille /117 exhaustive, contextualisée, falsifiable, apprenable, et capable d'auditer n'importe quel type de client / page / business.

Démarré : 2026-04-08.
Pilote : Mathis (Growth Society).

---

## Architecture — 3 couches empilées

### Couche 1 — Axiomes
Les 6 règles non-négociables. Voir [AXIOMES.md](./AXIOMES.md).

1. Falsifiabilité
2. Discrétisation ternaire (Top 3 / OK 1.5 / Critique 0)
3. Contextualité (page-type + business-category obligatoires)
4. Priorisation ROI (Impact × (6-Effort))
5. Livrable actionnable (rewrite obligatoire pour chaque Critique)
6. Double boucle d'apprentissage (validated + corrections)

### Couche 2 — Grille V3 /117
Fichier cible : `data/cro_criteria_v3.json` (à construire bloc par bloc).

- **6 piliers** : Cohérence /18, Hero /18, Persuasion /24, UX /24, Tech /15, Psycho /18
- **~60 critères** (vs 39 en V2) — granularité enrichie depuis Notion
- Schema critère :
  ```json
  {
    "id": "hero_01",
    "pillar": "hero",
    "label": "Proposition de valeur claire en H1",
    "pageTypes": ["home", "lp_leadgen", "lp_sales", "pdp"],
    "businessCategories": ["*"],
    "weight": 3,
    "scoring": {
      "top": "H1 contient: [bénéfice utilisateur] + [proof point|différenciateur|audience]",
      "ok": "H1 contient un bénéfice mais sans proof point ni différenciateur",
      "critical": "H1 générique (nom de marque, tagline vague, feature-only)"
    },
    "checkMethod": "textual",
    "examples": ["..."],
    "antiPatterns": ["..."],
    "killer": false,
    "notionRefId": "3207148e-95a5-81ac-a349-d87342dec780",
    "principleRefs": ["scent_trail", "test_5_sec"],
    "version": "3.0.0",
    "updatedAt": "2026-04-08"
  }
  ```
- Ajout `businessCategoryWeighting` (manquant en V2).
- Mécanisme `killer` (critère bloquant qui plafonne le score global).

### Couche 3 — Moteur reco + apprentissage
Fichiers cibles :
- `data/reco_templates_v3.json` (~50 templates, 1:1 avec les critères V3)
- `memory/memory_validated.md` (audits validés)
- `memory/memory_corrections.md` (erreurs apprises, avec **Why** + **How to apply**)
- `scripts/syncNotionChecklist.ts` (pont Notion ↔ GrowthCRO, à créer plus tard)

Priorisation : P0 / P1 / P2 (harmonisation SPECS.md — on abandonne le P1/P2/P3 du reco_engine legacy).

---

## Plan d'attaque bloc par bloc

On construit la grille V3 un pilier à la fois. Chaque bloc = 4 étapes + validation humaine obligatoire avant le suivant.

### Les 4 étapes d'un bloc
1. **Extraction brute** — lister tous les critères qui touchent au pilier depuis : Notion Checklist CRO, `audit_criteria.md` V1, `cro_principles.md`, `cro_criteria_v2.json`.
2. **Formalisation V3** — dédoubler / fusionner / réécrire en critères V3 structurés (scoring ternaire falsifiable, pageTypes, businessCategories, antiPatterns).
3. **Validation Mathis** — présentation critère par critère, Mathis valide ou recadre.
4. **Application double** — scorer 2 cas réels (Japhy + 1 autre : Travelbase ou &TheGreen) et comparer au scoring humain pour calibrer.

### Ordre des blocs

| # | Pilier | Points | Pourquoi dans cet ordre |
|---|---|---|---|
| 1 | **Hero** | /18 | Le plus impactant (×1.2 sur home), le mieux documenté, meilleur terrain d'entraînement |
| 2 | Persuasion | /24 | Le plus gros volume, hérite directement des learnings Hero |
| 3 | UX | /24 | Granularité Notion la plus riche (menus, filtres, checkout, etc.) |
| 4 | Cohérence | /18 | Transverse, plus facile une fois les 3 précédents posés |
| 5 | **Psycho** | /18 | Le plus faible (6 critères non formalisés en V2) — nécessite le plus de travail |
| 6 | Tech | /15 | Le plus cadré (mesurable PageSpeed/DOM), se fera rapidement |

---

## État actuel — 2026-04-08

- ✅ Étape 0 inventaire terminée (cf. HISTORY.md Phase 8)
- ✅ AXIOMES.md rédigé
- ✅ README.md (ce fichier) rédigé
- 🔄 **Bloc 1 Hero /18 en cours** — extraction brute en démarrage
- ⏳ Blocs 2-6 en attente

---

## Livrables attendus au terme du playbook

- `data/cro_criteria_v3.json` — grille complète /117, ~60 critères
- `data/reco_templates_v3.json` — ~50 templates de recos
- `memory/memory_validated.md` — audits validés avec patterns gagnants
- `memory/memory_corrections.md` — erreurs apprises avec Why + How to apply
- Adapter JS dans le prototype V5.x pour lire la grille V3
- Mise à jour `skills/cro-auditor/SKILL.md` pour pointer vers V3
- Migration Supabase (phase ultérieure, après figeage V3)
