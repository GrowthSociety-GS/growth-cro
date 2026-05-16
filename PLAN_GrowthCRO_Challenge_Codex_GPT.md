# Dossier GrowthCRO — Audit + Prompt Claude Code Ajusté Avec Skills Addendum

## 1. Verdict Brutal

Le nouvel addendum ne change pas la stratégie de fond : **il ne faut pas repartir de zéro**. GrowthCRO actuel est plus riche que le plan GPT feuille blanche. Le plan GPT est plus propre méthodologiquement. L’addendum skills ajoute la bonne couche manquante : **gouvernance agentique, anti-drift, sécurité des skills, mémoire et workflow**.

Donc la voie correcte est :

```text
GrowthCRO actuel = socle réel
Pack GPT = discipline produit
Skills Addendum = système d’exploitation agentique
```

Le problème principal aujourd’hui n’est pas “il manque un skill magique”. Le problème principal est que GrowthCRO a beaucoup de puissance, mais pas encore assez de **chaîne de vérité bloquante**.

## 2. Ce Qui Est Meilleur Dans GrowthCRO Actuel

GrowthCRO réel a déjà des choses que le pack GPT n’a pas :

- Un vrai historique de runs, erreurs, corrections et sprints GSG.
- Un moteur audit/reco déjà exploité sur des clients réels.
- Une doctrine CRO propriétaire.
- Un GSG canonique avec renderer contrôlé.
- Une webapp Next.js/Supabase déjà avancée.
- Des modules Reality, Experiment, Learning, GEO déjà amorcés.
- Des agents existants utiles : `capabilities-keeper`, `doctrine-keeper`, `scorer`, `reco-enricher`, `capture-worker`.
- Des skills déjà installés : Superpowers, GStack, cro-methodology, impeccable, emil-design-eng.
- Une vraie mémoire projet, même si elle est devenue lourde.

Source principale : [README.md](/Users/mathisfronty/Developer/growth-cro/README.md), [PRODUCT_BOUNDARIES_V26AH.md](/Users/mathisfronty/Developer/growth-cro/.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md), [skills-lock.json](/Users/mathisfronty/Developer/growth-cro/skills-lock.json).

## 3. Ce Qui Est Meilleur Dans Le Pack GPT

Le pack GPT est meilleur sur la structure théorique :

- V1 étroite.
- Pas de génération avant diagnostic.
- Outputs IA validés par schema.
- Distinction claire entre contexte, audit, opportunité, recommandation, variante, expérimentation, apprentissage.
- Recommandations invalides si elles n’ont pas preuve, hypothèse, action et métrique.
- Architecture plus lisible pour un agent externe.

Mais il est moins “réel” : il ne connaît pas toute la dette, les artefacts, les décisions et les régressions historiques de GrowthCRO.

Source : [architecture_webapp_agentic_growthcro.md](/Users/mathisfronty/Developer/growth-cro/growthcro/architecture_webapp_agentic_growthcro.md), [growthcro_delivery_pack_v2.zip](/Users/mathisfronty/Developer/growth-cro/growthcro/growthcro_delivery_pack_v2.zip).

## 4. Ce Que L’Addendum Skills Change

L’addendum apporte une correction importante : il dit explicitement de **ne pas installer aveuglément des skills externes**.

Le bon ordre devient :

1. Auditer les skills déjà présents.
2. Créer des skills custom GrowthCRO.
3. Installer très peu d’externes, seulement après audit sécurité.
4. Garder CCPM / PRD / epic / issue comme colonne vertébrale.
5. Utiliser les subagents pour spécialiser, pas pour multiplier le chaos.

Point important observé : `.claude/skills/` est vide, mais `skills/skill-based-architecture/` existe déjà, et `skills-lock.json` montre Superpowers + GStack déjà installés. Donc l’étape suivante n’est pas “installer”, c’est **consolider et gouverner**.

Source : [growthcro_skills_addendum_pack.zip](/Users/mathisfronty/Developer/growth-cro/growthcro/growthcro_skills_addendum_pack.zip).

## 5. Le Vrai Noyau À Construire

La chaîne canonique doit devenir :

```text
Business Context
→ Capture / Page Understanding
→ CRO Audit
→ Evidence & Claims Ledger
→ Opportunity Engine
→ Recommendation Engine
→ Variant / GSG
→ QA Gates
→ Reality Layer
→ Learning Layer
```

Aujourd’hui, GrowthCRO a déjà beaucoup de briques, mais la couche **Evidence → Opportunity → Recommendation → Variant** doit devenir beaucoup plus stricte.

## 6. Pourquoi GSG Et Recos Ne Sont Pas Encore Au Niveau “Top Mondial”

- Un output peut encore être bien noté alors que des gates échouent.
- Les juges internes peuvent produire une fausse confiance.
- Les skills runtime sont souvent des heuristiques Python, pas des skills réellement invoqués.
- Les recos sont parfois fortes, mais pas encore systématiquement reliées à une opportunité mesurable.
- Le GSG a beaucoup travaillé sur Weglot/listicle ; il faut éviter l’overfit.
- La preuve business réelle reste faible tant que Reality/Experiment/Learning ne ferment pas la boucle.
- Le design “stratosphérique” ne peut pas compenser des claims fragiles ou non sourcés.

Le problème n’est donc pas la créativité. C’est la **preuve**.

## 7. Roadmap Décisionnelle

### P0 — Vérité, Gates, Gouvernance

- Créer un `Verdict Gate` : si un gate critique échoue, grade maximum = `Non shippable`.
- Créer un `Evidence & Claims Ledger` : aucun chiffre, logo, testimonial, proof ou claim ne peut être rendu sans source.
- Créer un `Opportunity Layer` entre audit et recos.
- Créer un `Skill Registry` : installed skill, custom skill, runtime heuristic, subagent, MCP.
- Créer seulement 3 custom skills au départ :
  - `growthcro-anti-drift`
  - `growthcro-prd-planner`
  - `growthcro-status-memory`
- Ajouter une checklist sécurité skills : shell, network, `.env`, secrets, git, filesystem.
- Réconcilier les docs : single shell Next.js actuel, pas microfrontends.

### P1 — Qualité Produit

- Ajouter Playwright desktop/mobile sur les flows critiques.
- Ajouter axe-core / Lighthouse sur les pages webapp principales.
- Ajouter evals LLM avec Promptfoo ou DeepEval.
- Ajouter observabilité LLM avec Langfuse ou Sentry AI Performance.
- Créer benchmark GSG multi-clients et multi-page-types.
- Valider les recos avec critères : evidence, hypothesis, metric, owner, action concrète.

### P2 — Moat

- Reality Layer manual-first.
- Learning Layer validé humainement.
- Doctrine GrowthCRO portable sous forme de skills custom.
- Skills externes seulement si audit + utilité prouvée.
- MCP Supabase/Sentry/GitHub seulement avec environnement dev et permissions cadrées.

## 8. Skills Et Agents : Garder / Fusionner / Créer

À garder :

- `capabilities-keeper`
- `doctrine-keeper`
- `scorer`
- `reco-enricher`
- `capture-worker`
- `cro-methodology`
- `impeccable`
- `emil-design-eng`
- Superpowers
- GStack
- skill-based-architecture

À créer en premier :

- `growthcro-anti-drift`
- `growthcro-prd-planner`
- `growthcro-status-memory`

À créer ensuite :

- `growthcro-cro-audit`
- `growthcro-opportunity-engine`
- `growthcro-recommendation-engine`
- `growthcro-generator-qa`
- `growthcro-security-review`
- `growthcro-frontend-quality`

À éviter maintenant :

- Installer encore des skills externes sans audit.
- Créer 8 nouveaux subagents qui doublonnent ceux existants.
- Charger trop de skills dans une même session.
- Laisser des heuristiques Python se présenter comme “skills réellement invoqués”.

## 9. Prompt Claude Code — Audit Read-Only

```text
Tu travailles sur GrowthCRO.

Mission : produire un audit formel read-only + dossier de décision. Ne modifie, ne crée, ne supprime aucun fichier. N’installe aucun skill. Ne lance aucune commande destructive.

Lis d’abord :
1. CLAUDE.md
2. README.md
3. architecture/GROWTHCRO_ARCHITECTURE_V1.md
4. .claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md
5. docs/state/SKILLS_HONEST_AUDIT_2026-05-15.md
6. growthcro/architecture_webapp_agentic_growthcro.md
7. growthcro/growthcro_delivery_pack_v2.zip
8. growthcro/growthcro_skills_addendum_pack.zip
9. skills-lock.json
10. .claude/agents/*

Objectif :
Comparer GrowthCRO réel avec GrowthCRO OS + Skills Addendum, puis produire un dossier de décision.

Analyse obligatoirement :
- architecture produit actuelle ;
- architecture technique actuelle ;
- webapp Next.js/Supabase ;
- audit engine ;
- recommendation engine ;
- GSG ;
- reality layer ;
- experiment layer ;
- learning layer ;
- GEO ;
- skills installés vs skills réellement utilisés ;
- skills custom manquants ;
- agents existants vs agents proposés ;
- contradictions docs/code ;
- gates qualité ;
- inputs/outputs ;
- sécurité : SSRF, prompt injection, secrets, RLS, storage, HTML untrusted ;
- pourquoi GSG et recos ne sont pas encore top mondial.

Règles :
- zéro modification ;
- zéro installation ;
- zéro bullshit ;
- cite les fichiers lus ;
- distingue preuve, inférence et opinion ;
- ne prétends pas qu’un skill est utilisé si c’est seulement une heuristique Python ;
- si un gate critique échoue, considère l’output non shippable ;
- ne recommande pas de repartir de zéro sauf preuve forte.

Livrable attendu :
1. verdict brutal ;
2. ce que GrowthCRO actuel fait mieux que le pack GPT ;
3. ce que le pack GPT fait mieux ;
4. ce que l’addendum skills change ;
5. skills/agents à garder, fusionner, créer, éviter ;
6. roadmap P0/P1/P2 ;
7. issues prêtes à coder ;
8. stop conditions ;
9. prompt futur d’implémentation P0, séparé, à utiliser seulement après validation humaine.
```

## 10. Prompt Futur Si Tu Veux Faire Coder Plus Tard

```text
Tu vas implémenter uniquement P0. Ne fais rien hors scope.

Scope :
1. Skill Registry honnête.
2. Trois custom skills initiaux :
   - growthcro-anti-drift
   - growthcro-prd-planner
   - growthcro-status-memory
3. Verdict Gate.
4. Evidence & Claims Ledger.
5. Opportunity Layer.
6. Security checklist P0.
7. Tests unitaires/fixtures liés.

Out of scope :
- redesign UI ;
- nouveau GSG créatif ;
- nouvelles intégrations ;
- installation de skills externes ;
- refactor massif ;
- microfrontends ;
- changement de stack.

Stop si :
- migration destructive ;
- secret détecté ;
- contradiction produit non tranchée ;
- skill externe requis ;
- sortie LLM critique non validée ;
- claim rendable sans preuve ;
- fichier touché hors scope.
```

## 11. Assumptions

- On ne code rien maintenant.
- On ne crée aucun fichier maintenant.
- On ne demande pas à Claude Code de coder dans le premier prompt.
- GrowthCRO actuel reste le socle.
- Le pack GPT sert de discipline.
- L’addendum skills sert de gouvernance.
- Les prompts ci-dessus sont prêts à coller.
