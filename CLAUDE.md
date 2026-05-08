# CLAUDE.md — Entrypoint projet GrowthCRO

**Lire OBLIGATOIREMENT en tout début de conversation, avant toute autre action.**

---

## 🛡️ ORDRE D'INITIALISATION ABSOLU (V26.AE — RENFORCÉ)

**Mathis a explicitement demandé** (2026-05-04) : *"qui me dit que t'as pas oublié 1000 trucs ? plusieurs scripts pour le même but ? l'inutile pas archivé ? tu te souviens du système anti-oubli ?"*. Ces étapes 1-9 sont **non négociables**.

1. **Lire ce CLAUDE.md** (en entier)
2. **Lire `README.md`** — état projet V26.AE actuel (8 modules, structure post-cleanup)
3. **Re-fetcher Notion** (URLs ci-dessous) — vision produit canonique :
   - `Mathis Project x GrowthCRO Web App` : https://www.notion.so/growth-society/Mathis-Project-x-GrowthCRO-Web-App-3457148e95a58009b81efdf185f11ade
   - `Le Guide Expliqué Simplement` : https://www.notion.so/growth-society/GrowthCRO-Le-Guide-Expliqu-Simplement-3517148e95a5805ba35ee290ebf21e0d
   - **Si WebFetch retourne juste "Notion"** : Notion est SPA → utiliser `mcp__0eae5e51-...__notion-fetch` (MCP authentifié)
4. **Lire `STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`** — plan d'action ordonné Sprints F-L (refuser tout sprint hors plan)
5. **Lire le plus récent `AUDIT_TOTAL_*.md`** — diagnostic état actuel
6. **Lancer `python3 state.py`** — état disque réel (counts pipeline)
7. **Lancer `python3 scripts/audit_capabilities.py`** + lire `CAPABILITIES_SUMMARY.md` — registry honnête
8. **Skim `memory/MEMORY.md`** + `GROWTHCRO_MANIFEST.md` §12 changelog
9. **Skim `DESIGN_DOC_V26_AA.md`** — architecture cible 5 modes GSG

**Ne jamais commencer à coder/scorer/auditer sans avoir fait ces 9 étapes ET obtenu consigne explicite Mathis.**

---

## 🛡️ AVANT TOUT SPRINT CODE — Pré-requis ANTI-OUBLI RENFORCÉ V26.AE

### Erreurs récurrentes prouvées (à NE PLUS REPRODUIRE)

| # | Anti-pattern | Empirique |
|---|---|---|
| 1 | **Mega-prompt sursaturé** (>8K chars dans persona_narrator) | Sprint B+C V26.AA = -28pts régression |
| 2 | **Réinventer une grille** au lieu de doctrine V3.2.1 | V26.Z 3 grilles parallèles, abandonné |
| 3 | **Ajouter sans archiver** (Sprint G du plan) | 0% fait jusqu'à V26.AE |
| 4 | **Coder avant design doc validé** | mea culpa V26.AA Sprints C/D |
| 5 | **Ne pas relire strategic_audit** avant chaque sprint | mea culpa V26.AD/AD+ |
| 6 | **Audit sans Notion** | mea culpa V26.AE début (corrigé) |
| 7 | **Faire des "améliorations" qui ajoutent au prompt** | au lieu de gates post-process |
| 8 | **Industrialiser avant validation unitaire** | Mathis veut perfection 1er run |

### Avant tout code GSG/audit OBLIGATOIRE

1. **Run audit_capabilities** : `python3 scripts/audit_capabilities.py`
2. **Lire `CAPABILITIES_SUMMARY.md`** — section "🔴 ORPHELINS HIGH"
3. **Pour chaque capacité orpheline HIGH dans le scope** :
   - Soit BRANCHER (recommandé)
   - Soit SKIP avec **justification écrite** dans le commit
   - JAMAIS ignorer silencieusement
4. **Avant "code from scratch"** : grep le registry pour vérifier que ça n'existe pas déjà
5. **Hard limit prompt persona_narrator ≤8K chars** — au-delà = STOP, c'est anti-pattern #1
6. **Si un module cible (Reality / Multi-judge / Experiment / GEO / Learning) est mentionné dans le sprint** : vérifier état réel disque AVANT (`find skills/site-capture/scripts/<module>`)
7. **Sub-agent `capabilities-keeper`** disponible pour audit préalable formel

### Capacités déjà connues comme orphelines critiques (à brancher en priorité)

D'après `STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md` Top 10 :
1. ✅ AURA (`_aura_<client>.json`) — branché V26.AC Sprint F
2. ❌ **Reality Layer V26.C** (5 connectors codés, env vars manquent) — `skills/site-capture/scripts/reality_layer/`
3. ✅ Screenshots multimodal — branché V26.AC Sprint F
4. ✅ recos_v13_final.json — via router racine
5. ✅ v143 founder/VoC/scarcity — via router racine
6. ⚠️ **evidence_ledger comme GATE post-process** (chargé via router pas comme gate bloquant) — à convertir
7. ✅ learning_layer V29 (69 proposals générés)
8. ⚠️ **design_grammar comme POST-PROCESS GATE** (en pre-prompt actuellement = anti-pattern #1)
9. ✅ golden_dataset + golden_bridge — branché V26.AD+ Sprint AD-3
10. ❌ **score_specific_criteria.py** (listicle list_01-05) — orphelin, à brancher dans batch_rescore

---

## État actif : V26.AF — DIAGNOSTIC EMPIRIQUE BRUTAL (2026-05-04)

**Status** : V26.AF a shippé le workflow conversationnel GSG (skill réécrit + pipeline_sequential 4 stages + brief_v2_prefiller + doctrine V3.2.1 branchée + multi-judge final). MAIS le test empirique vs Sonnet vanilla chat a confirmé que **notre pipeline V26.AC/AD/AE/AF est NÉGATIF visuellement** (anti-AI-slop = anti-design).

**Premier feedback empirique pipeline V26.AF (Weglot listicle FR)** :
- Doctrine raw 61% / capped 50% (2 killers : `coh_01` + `ux_04`)
- Humanlike 75% ⭐ (vs V26.Z BESTOF 66/80 = +14% bond)
- Final 70/30 : 57.5% Moyen

**Test vanilla brutal** : Claude vanilla chat (pas de pipeline) → Mathis verdict : *"visuel BCP MIEUX, enfin des choses qu'on veut ! mais reste IA-like, copy nul on voit que c'est de l'IA"*.

**Conclusion empirique** : Linear-grade ≠ atteignable par Sonnet single-shot peu importe le pipeline. Manque vraies images + anecdotes humaines + polish humain.

**3 OPTIONS STRATÉGIQUES PROPOSÉES — DÉCISION MATHIS EN ATTENTE** :
1. **Option 1** — GSG = 80% Claude + 20% polish humain (réaliste)
2. **Option 2** ⭐ — PIVOT focus AUDIT engine = vraie IP différenciante (recommandé)
3. **Option 3** — Multi-modal ChatGPT + GPT-image (effort 2 mois ROI incertain)

**Lecture obligatoire séquentielle V26.AF** :
- `README.md` (post-V26.AE actuel)
- `AUDIT_TOTAL_V26AE_2026-05-04.md` (diagnostic complet état)
- `STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md` **section 9** (V26.AF + diagnostic empirique brutal)
- `memory/project_growthcro_v26_af.md` ⭐ (NEW — narratif V26.AF complet)

**Reste à faire (en attente décision Mathis Option 1/2/3)** :
1. **Mathis review 69 doctrine_proposals** → V3.3 (autonome, pas blocant)
2. Pre-fill audience auto via Haiku (intent.json n'a pas audience/objections/desires structurés)
3. Si Option 1 : calibration doctrine V3.2.2 (`coh_01` exclude listicle + `ux_04` amender)
4. Si Option 2 : migration webapp Next.js + Supabase + Vercel
5. Reality Layer Kaiju activation (.env vars)
6. Cross-client Japhy + 1 SaaS premium

---

## ⚠️ V26.AF Anti-pattern #2 IDENTIFIÉ — anti-AI-slop = anti-design

**Empiriquement prouvé V26.AF** : forbidden_visual_patterns trop agressif (gradient, glassmorphism, neumorphism, cards, border-left, etc.) = Sonnet code défensivement → page blanche minimaliste sans âme.

**Implication anti-pattern #2** : ne plus interdire en bloc les techniques visuelles. Distinguer :
- AI-slop évident (gradient mesh radial multi-stop, fake stars ⭐⭐⭐, FOMO countdown, lifestyle stock photos) → INTERDIT
- Techniques classy bien dosées (gradient subtil, glassmorphism nav backdrop, hairline 0.5px, drop caps colorés, shadows multi-layer, grain noise overlay, pull quotes typo) → AUTORISÉ ENCOURAGÉ

---

## Vision GrowthCRO (rappel non négociable)

**GrowthCRO** = consultant CRO senior automatisé pour les ~100 clients de l'agence **Growth Society** (media buying performance Meta/Google/TikTok). 8 modules :

1. Audit Engine (capture → vision → score → recos enrichies)
2. Brand DNA + Design Grammar (V29+V30)
3. **GSG** (génération LP, EN CRISE — 46/80 vs collègue 67/80)
4. Webapp Observatoire V26 (11 panes Deep Real Night)
5. Reality Layer V26.C (5 connectors GA4/Meta/Google/Shopify/Clarity)
6. Multi-judge V26.D
7. Experiment Engine V27
8. Learning Layer V28+V29
9. GEO Monitor V31+

**Boucle fermée** : Audit → Action → Mesure → Apprentissage → Génération → Monitoring.

**Position Mathis (verbatims non oubliables)** :
- *"Cet outil doit sortir la perfection dès le départ"* — pas industrialisation
- *"Concision > exhaustivité"* — règle de renoncement
- *"L'avant-garde, pas le best CRO B2B 2024"*
- *"Aucun concurrent agence n'a ça — c'est notre différenciateur"*
- *"Le moat est dans les data accumulées"*

---

## Tu as accès à ces ressources

- `RUNBOOK.md` → commandes exactes pour chaque scénario
- `SCHEMA/` → JSON schemas + `validate_all.py` sanity check
- `.claude/agents/` → 5 subagents (capture-worker, scorer, reco-enricher, doctrine-keeper, capabilities-keeper)
- `.claude/commands/` → 5 slash commands (/audit-client, /score-page, /pipeline-status, /full-audit, /doctrine-diff)
- Notion MCP authentifié → fetch pages produit canoniques (vs WebFetch qui voit juste la coquille SPA)

Environnement : FS natif macOS, git, pas de restrictions sandbox CoWork.

---

## Règles critiques projet (immuables)

- **No Notion auto** : ne modifier Notion que sur demande explicite Mathis
- **Qualité > vitesse** : toujours l'option la plus complète, jamais de raccourci
- **Dual-viewport obligatoire** : Desktop + Mobile séparément
- **Screenshots = proof** : DOM rendered + PNG, pas HTML statique
- **Check before assume** : grep + lire MANIFEST/AUDIT_TOTAL avant d'affirmer "on a X"
- **Git discipline** : chaque changement doctrine/scorer/reco → commit isolé. `git status` propre avant batch
- **Pas de `git reset --hard` ni autres actions git destructives** sans confirmation explicite Mathis (perte de working tree irréversible). Préférer `git stash`, `git restore --staged`, `git reset` (mode mixed par défaut), ou un nouveau commit. Couvre aussi : `git push --force`, `git checkout -- <file>`, `git clean -fd`, `git branch -D`. Règle posée 2026-05-08 après tentative reset --hard pour reconstituer historique sur ~/Developer/growth-cro (refusée → fresh history préférée).
- **Schemas = guard rails** : avant tout changement structurel, run `python3 SCHEMA/validate_all.py` baseline + post-change
- **Notion = source produit** : si conflit code vs Notion → demander clarification, ne pas drift
- **Anti-pattern #1 hard limit** : prompt persona_narrator > 8K chars = STOP

---

## Mise à jour du manifest

Quand une brique majeure change (nouveau bloc, script renommé, playbook upgrade, schéma data modifié), **éditer `GROWTHCRO_MANIFEST.md` dans la même conversation** et ajouter une ligne au changelog (§12). Sinon dérive garantie.

Commit séparé pour le manifest (`docs: manifest §12 — add YYYY-MM-DD changelog for <change>`). Ne pas amender l'ancien.

---

## Clés API

Toutes les clés vivent dans `.env` (gitignored). Template dans `.env.example`. Ne JAMAIS mettre une clé dans une wake-up note, un commit message, ou un fichier tracké. Si tu en vois une en clair → agent doctrine-keeper pour sanitize + rotate.
