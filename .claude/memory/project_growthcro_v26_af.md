---
name: project_growthcro_v26_af
description: V26.AF (2026-05-04) — GSG workflow conversationnel + doctrine V3.2.1 branchée + multi-judge final + DIAGNOSTIC EMPIRIQUE BRUTAL test vanilla vs pipeline. Verdict Mathis : pipeline NÉGATIF visuellement, vanilla mieux mais IA-like, copy IA-like. Linear-grade ≠ Sonnet single-shot. 3 options stratégiques proposées en attente décision.
type: project
---

# V26.AF — GSG workflow conversationnel + Diagnostic empirique brutal (2026-05-04)

## Contexte

Post-V26.AE Cleanup massif (~80 fichiers archivés, README réécrit, CLAUDE.md renforcé), Mathis a invoqué le GSG en attendant un workflow conversationnel ("je l'invoque, tu poses les questions, tu pré-remplis ce que tu sais, je valide, hop ça génère"). Le skill GSG existait mais c'était une doc technique pas un vrai workflow.

## Ce qui a été shippé (Phase 1 — Sprint AF-1.B)

### `moteur_gsg/core/brief_v2_prefiller.py`
Pré-remplit BriefV2 depuis router racine (intent + brand_dna + v143 + recos + design_grammar) :
- objective ← intent.primary_intent + heuristic page_type
- audience ← intent.audience + objections + desires + v143.voc (LIMIT : intent.json Weglot n'a pas ces champs structurés → audience reste vide, demande Mathis)
- angle ← brand_dna.voice_signature_phrase + archetype
- traffic_source + visitor_mode ← suggested per page_type
- available_proofs + sourced_numbers ← v143
- forbidden_visual_patterns ← anti-AI-slop defaults + brand_dna.diff.forbid

### `moteur_gsg/core/pipeline_sequential.py`
4 stages séquentiels (anti-pattern #1 mega-prompt évité par construction) :
- **Stage 1 STRATEGY** (T=0.4) : décide structure → JSON {layout_plan, sections, key_proofs, hook}
- **Stage 2 COPY** (T=0.7) : persona narrator écrit contenu → JSON {h1, dek, intro, reasons, pull_quotes, stat_callouts, cta}
- **Stage 3 COMPOSER** (T=0.6, multimodal) : compose HTML avec AURA CSS injecté
- **Stage 4 POLISH** (T=0.3) : raffine (typo, langue, anti-slop)

### `scripts/run_gsg_full_pipeline.py`
Orchestrateur conversationnel : URL → pre-fill → validation → pipeline → multi-judge final.

### `skills/gsg/SKILL.md` réécrit en workflow conversationnel
"je pose les questions, je pré-remplis, tu valides, je génère" + 5 modes différenciés + interdits anti-patterns + exemple session complet.

## Phase 2 — Mathis pointe 3 trous critiques

Après run V26.AF initial sans doctrine ni judges, Mathis a explicitement noté :
1. **GSG pas connecté à la doctrine !** — Pivot V26.AA "doctrine racine partagée Audit + GSG" oublié dans MA propre refonte sequential
2. **Tu notes plus la LP générée** — `skip_judges=True` par défaut, 0 feedback empirique
3. **Tu as bypass ton skill GSG** — overrides CLI au lieu du workflow conversationnel pose-questions

→ Mea culpa direct, fixes immédiats.

## Phase 3 — FIX 1+2 : doctrine branchée + multi-judge final

### Fix 1 — pipeline_sequential.py
- Import `scripts.doctrine` : top_critical_for_page_type, killer_rules_for_page_type, render_doctrine_for_gsg
- Stage 1 STRATEGY consume doctrine_block (n=7 critères ≤2.5K chars) + killer_rules_block (≤800c)
- Stage 2 COPY consume doctrine_block court (n=5, ≤1.5K chars)

### Fix 2 — run_gsg_full_pipeline.py
- Étape 8 : multi-judge final (doctrine V3.2.1 + humanlike + impl_check)
- Save audit_multi_judge.json
- Affichage note finale (doctrine % / humanlike % / final 70-30)

## Premier feedback empirique pipeline V26.AF (Weglot listicle FR)

| Métrique | Score |
|---|---|
| Doctrine raw | **61%** |
| Doctrine capped | **50%** (2 killers) |
| Humanlike | **75%** ⭐ (vs V26.Z BESTOF 66/80, +14%) |
| Final 70/30 | 57.5% (Moyen) |
| Cost | $0.62 ($0.28 pipeline + $0.34 judges) |
| Wall | 6.5 min |

**Killer rules diagnostiqués** :
- `coh_01` : H1 listicle = hook éditorial mais manque promesse claire (Quoi/Pour qui/Pourquoi)
- `ux_04` : 1 CTA final seulement vs ≥3 distribués
- → CONFLIT entre archétype lp_listicle ("single_cta_final") et doctrine ("≥3 CTAs")

**Insight** : COPY (Stage 2 + persona narrator + doctrine) = bon (humanlike 75%). Le sujet = HERO + CTAs distribution.

## Phase 4 — TEST EMPIRIQUE BRUTAL : pipeline V26.AF vs Sonnet vanilla

### Mathis verdict V26.AF visuel
> *"toujours aussi nul ! page blanche, aucun effet, aucune texture, aucun motion, aucune image. Même Claude vanilla en chat ferait mieux. ChatGPT fait mieux en 30s."*

### Test : Claude Sonnet (moi) écrit DIRECTEMENT dans le chat
HTML Weglot listicle, **sans pipeline, sans contraintes anti-AI-slop**, avec autorisation totale (gradients, motion, schémas SVG inline, animations IntersectionObserver, depth + blur, textures grain noise, drop caps massifs colorés, sticky progress sidebar, marginalia card violet, takeaway dark avec radial gradient blur).

→ Output : `deliverables/weglot-VANILLA-CLAUDE-CHAT.html`

### Mathis verdict vanilla
- ✅ **Visuel BCP MIEUX** : *"enfin des choses qu'on veut !"*
- ❌ Mais **reste IA-like** visuellement
- ❌ **Copy nul** : *"on voit que c'est de l'IA"*

## Diagnostic empirique CONFIRMÉ

1. **Notre pipeline V26.AC/AD/AE/AF est NÉGATIF visuellement.** Anti-AI-slop = anti-design tout court. Confirmé par Mathis empiriquement.

2. **Sonnet single-shot a un plafond visuel.** Même libéré de toutes les contraintes, reste reconnaissable comme IA.

3. **Linear-grade ≠ atteignable par Sonnet/LLM seul.** Ce qui sépare 75/80 du 95/80 :
   - **Vraies images** (photos founder, screenshots produit, stats live) — Sonnet ne peut pas les générer
   - **Anecdotes humaines ultra-spécifiques** (date précise, nom employé réel, conversation Slack, commit hash) — incarnation humaine requise
   - **Prises de position polémiques** — Sonnet n'oserait pas
   - **Polish humain 20-30 min final** (ajustements typo, micro-copy, choix de mot)

## 3 Options stratégiques honnêtes proposées

### Option 1 — GSG = 80% Claude + 20% polish humain
- Pipeline V26.AF garde l'audit/scoring + brand_dna + doctrine
- Mathis polit 30 min après chaque run
- GSG = accélérateur pas magicien
- Réaliste, scalable, vendable

### Option 2 ⭐ — PIVOT stratégique : focus AUDIT engine (vraie IP)
- **L'IP différenciante = AUDIT + closed-loop**, PAS génération LP automatique
- 56 clients audités, 3186 recos LP + 170 step, 8347 evidences, doctrine V3.2.1
- Migration webapp Next.js + Supabase + Vercel pour vendre AUDIT au client agence
- C'est ÇA qu'aucun concurrent agence n'a
- Recommandation Claude

### Option 3 — Multi-modal ChatGPT + GPT-image
- ChatGPT GPT-5 + DALL-E pour vrais assets visuels
- Notre backend (audit / brand_dna / doctrine) reste utile en input
- ~$5/run, espoir 85/80 mais 2 mois dev sans garantie

## Files créés/modifiés V26.AF

```
NEW :
  moteur_gsg/core/brief_v2_prefiller.py    (305 LoC — pre-fill from router racine)
  moteur_gsg/core/pipeline_sequential.py    (470 LoC — 4 stages + doctrine branché)
  scripts/run_gsg_full_pipeline.py          (220 LoC — orchestrateur conversationnel)
  scripts/_test_weglot_listicle_V26AE.py    (test V26.AE référence)
  deliverables/weglot-lp_listicle-V26AF-FULLPIPE.html       (output sans doctrine)
  deliverables/weglot-lp_listicle-V26AF-DOCTRINE-JUDGED.html  (output avec doctrine + judges)
  deliverables/weglot-VANILLA-CLAUDE-CHAT.html              (output vanilla SANS pipeline — référence empirique)
  data/_pipeline_runs/weglot_lp_listicle_*/  (intermediates Stage 1-5 + audit JSON)

MODIFIED :
  skills/gsg/SKILL.md (réécrit workflow conversationnel)
  scripts/run_gsg_full_pipeline.py (+ multi-judge final)
  moteur_gsg/core/pipeline_sequential.py (+ doctrine helpers + Stage 1+2 consume doctrine)
```

## Position Mathis post-V26.AF

> *"Bah à toi aussi de juger ! mais mon retour c'est que le visuel est bcp mieux, enfin des choses qu'on veut !! mais il est juste IA-like quoi. Par contre le copy est nul, on voit que c'est de l'IA. bref ça nous avance pas bcp."*

→ Décision stratégique en attente Mathis : Option 1, 2, ou 3.

## Insight stratégique majeur

**On a passé 2 mois sur le GSG visuel à la perfection.** Empirique : on n'arrivera pas à Linear-grade en 1 run avec Sonnet seul, même avec pipeline parfait. La vraie IP différenciante de Growth Society = AUDIT + closed-loop (Reality + Lifecycle + Learning + Multi-judge), pas la génération LP.

**Recommandation Claude** : Option 2 (pivot AUDIT engine + webapp Next.js+Supabase+Vercel). C'est probablement le bon move.
