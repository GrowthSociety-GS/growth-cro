---
name: FINAL_ACCEPTANCE_TEST_TODO
description: Test d'acceptance final demandé par Mathis 2026-05-15. À exécuter APRÈS la clôture de tous les sprints (Sprint 19+) — refaire le listicle Weglot from blank page avec interrogation interactive complète (LP-Creator 4 phases), pas avec un brief pré-cuit. Mathis veut valider que le pipeline est vraiment end-to-end avant d'industrialiser.
type: project
---

# 🎯 TEST D'ACCEPTANCE FINAL — Weglot listicle from blank page

**Demandé par** : Mathis 2026-05-15 (post-Sprint 18 close commit `9503106`)
**Citation** : *"à la toute fin des sprints on refera le listicle Weglot
depuis une page blanche tu me demanderas les inputs comme dans la web
app depuis le départ du pipe car je suis pas convaincu que t'aies fait
ça proprement avec toutes les itérations qu'on a fait"*

**Why** : Mathis doute légitimement que le pipeline complet (LP-Creator
4 phases → moteur_gsg canonical → multi-judge → audits runtime) ait
été testé proprement en bout-en-bout. Tous les runs V7→V11 ont utilisé
le BRIEF V2 PRÉ-CUIT `weglot-listicle-brief-v2-FROM-LP-CREATOR.json`
construit dans la session. Aucun run from blank page (qualification
brute → brief → stratégie → copy → handoff → HTML → audit) n'a été
fait avec questions/réponses interactives.

## When to run

**À la toute fin des sprints planifiés** (post-Sprint 19+). NE PAS
lancer avant que les sprints en cours soient closés. Liste des sprints
qui DOIVENT être terminés avant ce test :

- [x] Sprint 13 — `moteur_gsg` V27.2-G+ extend listicle layout (`5b1f515`)
- [x] Sprint 14 — Visual quality fixes 4 observations (`4a8de5f`)
- [x] Sprint 15 — GSG pipeline real end-to-end (`8ae6283`)
- [x] Sprint 16 — Resolve all + stratospheric hero (`223b504`)
- [x] Sprint 17 — Stratospheric final polish + honest skills audit (`a82c54c`)
- [x] Sprint 18 — Beyond Excellent : Humanlike +2.5pts (`9503106`)
- [ ] Sprint 19 — Doctrine recovery + multi-page + true Skill wiring (TBD)
- [ ] Sprint 20+ — webapp integration of audit suite (TBD)

## Test protocol — what "from blank page" means

1. **Mathis arrive avec une demande brute** : *"Je veux une LP listicle
   pour Weglot en français pour signup essai gratuit"* (ou similaire).

2. **Phase 0 LP-Creator — qualification (4 questions)** :
   - Q0 Client + URL (`Weglot` + `https://www.weglot.com/fr`)
   - Q1 Type d'offre (SaaS-abonnement)
   - Q2 Objectif conversion (Inscription essai gratuit)
   - Q3 Type LP — proposer 3-5 types, recommander `lp_listicle` avec justif
   - **STOP** — attendre réponses Mathis, **ne rien produire d'autre**

3. **Phase 1 LP-Creator — brief complet (5 blocs A/B/C/D/E)** :
   - Bloc A : contexte campagne (ad, source trafic)
   - Bloc B : audience + framework (4 déclencheurs émotionnels / JTBD /
     Persona / Hybride) — recommander, Mathis valide
   - Bloc C : offre (adapté SaaS — problème, capability, alternative,
     pricing, preuves, intégrations)
   - Bloc D : contraintes prod (CMS, charte, éléments obligatoires/interdits)
   - Bloc E : mécanisme conversion (URL signup, sans-CB, plan gratuit)
   - **STOP** — attendre TOUTES les réponses

4. **Phase 2 LP-Creator — stratégie CRO** :
   - D1 framework copy retenu + justif matrice cro_doc.md
   - D2 structure section par section mappée sur framework
   - D3 éléments preuve classés par puissance
   - D4 infos manquantes
   - D5 charte
   - **STOP** — attendre validation EXPLICITE Mathis

5. **Phase 3 LP-Creator — copy complet** :
   - Hero (eyebrow, h1, sub-h1, dek, cta, microcopy, logos line)
   - Intro problem-bridge
   - 10 reasons numérotées (heading + body + highlight)
   - Comparatif "Sans vs Avec" table
   - 3 témoignages clients (avec source_url si publique OU
     sourced_from=internal_brief)
   - FAQ 5 questions
   - CTA final + reassurance
   - Footer
   - **STOP** — attendre validation copy

6. **Handoff auto vers moteur_gsg** :
   - Sérialiser le copy validé en `.md` avec convention LP-Creator
   - Construire `BriefV2` avec `lp_creator_validated_copy_path` pointant
     vers le .md
   - Ajouter `unsplash_portrait_id` par testimonial (Polaar / Respond.io /
     L'Équipe Creative — IDs déjà curés Sprint 18)
   - Lancer `scripts/run_gsg_full_pipeline.py --brief <path>` avec
     multi-judge actif (pas `--skip-judges`)

7. **Verification gates** (acceptance) :
   - composite_score affiché + grade (Exceptionnel ≥ 85, Stratospheric ≥ 92)
   - Impeccable QA 100/100
   - CRO methodology + frontend-design + brand-guidelines +
     emil-design-eng : tous ≥ 9/10
   - Multi-judge ≥ 78% (Excellent)
   - 0 leak `home/capture.*` ou autre artefact path
   - Hero capture `/fr` (pas `/en`)
   - 3 testimonials avec portraits Unsplash
   - 3 pull-quotes éditoriaux
   - sub-h1 italique rendu
   - Logos grid HBO/Nielsen/IBM/Décathlon/Amazon
   - 10 illustrations SVG sur-mesure

8. **Playwright screenshot** desktop + mobile pour proof visuel
9. **Mathis review final** — verdict shippable ou non

## Pourquoi ce test compte

Sans ce test, on a UNIQUEMENT validé que :
- Le moteur GSG accepte un brief V2 pré-cuit et produit du HTML
- Les audits runtime PASS sur ce HTML
- Le multi-judge note l'output

On n'a PAS validé que :
- Le wizard intake LP-Creator + brief_v2 fonctionne en saisie interactive
- La conversion Mathis-dialogue → BriefV2 → .md copy → moteur_gsg est fluide
- L'expérience utilisateur "from scratch" est shippable pour les ~100 clients

## Référencement

- `MEMORY.md` index → cette mémoire listée comme priorité finale
- Sprint 19+ epic.md → ce test mentionné dans "Acceptance gate finale"
- À chaque session post-clear : lire ce fichier après CLAUDE.md init
