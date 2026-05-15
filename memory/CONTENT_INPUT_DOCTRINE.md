---
name: CONTENT_INPUT_DOCTRINE
description: Doctrine "content-input-from-blank" — règle obligatoire pour tous les GSGs (tous clients, tous types de LP). Avant toute Phase 1 brief, l'agent DOIT fetcher 6 catégories de sources Weglot-equivalent (homepage / pricing / customers index + 2-3 case studies individuelles / about / blog index + top 5 articles / features OR integrations), synthétiser des insights frais, et PROPOSER 3 ANGLES DISTINCTS au user qui choisit avant pré-remplissage. Bloque le drift "réutilise le copy existant sans questionner".
type: project
---

# Doctrine "content-input-from-blank" — règle pipeline GSG

**Demandé par** : Mathis 2026-05-15 (post-test acceptance Weglot, après avoir constaté que j'avais recyclé l'angle Sprint 13 sans questionnement).

**Citation** : *"on est d'accord que t'es reparti de quelque chose d'existant au final pour le contenu choisi ?... va falloir pour tous les GSGs, clients et types de LP inclure cette méthodo dans le pipe, il faut absolument pouvoir donner des inputs sur le contenu en plus du reste"*

## Pourquoi cette doctrine existe

Sans cette règle, l'agent (moi) tombe dans le réflexe **"si un copy validé existe déjà pour ce client/type LP, je le réutilise"** — qui marche pour itérer mais qui **étouffe la diversité éditoriale** et empêche d'explorer des angles vraiment frais. Quand un user lance un from-blank pour la 2e fois sur le même client, il s'attend à **un nouvel angle**, pas le copy précédent verbatim.

## Règle obligatoire (HARD GATE)

À **toute Phase 1 brief from-blank**, l'agent DOIT :

### Step 1 — Research fetch (6 catégories minimum)

Fetcher en parallèle les 6 catégories de sources publiques (10-15 minutes wall) :

| Catégorie | URL pattern | Pourquoi |
|----|----|----|
| Homepage | `/`, `/<lang>/` | Voice signature, hero pattern, CTAs, logos tier-1, ratings ATF |
| Pricing | `/pricing`, `/plans`, `/tarifs` | Modèle tarifaire exact, tiers, free trial, contraintes |
| Customers index | `/customers`, `/case-studies`, `/clients` | Liste named cases + résultats agrégés |
| **Case studies individuelles** | `/customers/<name>` × **2-3 minimum** | Quotes verbatim, stats spécifiques avec timeframe, contexte business AVANT/APRÈS, raison du choix vs alternatives |
| About | `/about`, `/company`, `/team` | Fondateurs, année, funding, mission, team size — anti-AI-slop = ancres réelles |
| **Blog / Resources** | `/blog`, `/resources`, `/guides` | **Critical** : extraire 5-8 article titles pour identifier les angles éditoriaux que le client lui-même développe — c'est la voice de la marque en action |

Optionnel mais recommandé :
- `/features` (descriptifs détaillés capabilities)
- `/integrations` (stack-fit objection killer)
- `/security` / `/compliance` (si entreprise)
- Twitter / LinkedIn officiel (si voice marketing actuelle)

### Step 2 — Synthèse des fresh insights

Avant de pré-remplir le brief, l'agent compile :
- **Stats fresh** par case study (timeframe + context — pas juste le chiffre)
- **Quotes verbatim** des testimonials avec nom + role réel
- **Recurring themes** du blog (ce que le client lui-même éditorialise)
- **Anti-patterns** (ce que le brand_dna interdit + ce qui pourrait être confondu avec le client)

### Step 3 — Proposer **3 ANGLES DISTINCTS** au user

L'agent DOIT proposer **au moins 3 angles éditoriaux distincts** pour le même brief :

Pattern recommandé :
- **Angle A — Listicle pure** ("N raisons", "N erreurs à éviter", "N outils") — scanner 30s persona
- **Angle B — Case studies décodés** (story-driven, 3-5 cases zoomés) — reader 5min persona
- **Angle C — Méthode/playbook** ("Le guide en N étapes pour…") — solution-seeker persona

OU des variations selon le type de LP :
- **pdp** : Bénéfice principal / Lifestyle showroom / Comparison battlefield
- **lp_sales** : VSL pure / Story du founder / Investigation
- **advertorial** : Native article / Expert interview / Data deep dive
- **etc.**

### Step 4 — Attendre choix utilisateur EXPLICITE

L'agent NE peut PAS pré-remplir le brief AVANT que le user ait choisi entre les 3 angles. Le user peut aussi répondre **"angle D — je veux X"** pour proposer un 4e angle non-anticipé.

### Step 5 — Pré-remplir le brief sur l'angle CHOISI uniquement

Une fois l'angle choisi, l'agent pré-remplit le brief en partant **des fresh insights step 2**, pas du cache mental du copy précédent.

### Step 6 — Rédiger le copy from-scratch sur cet angle

Phase 3 copy ne peut PAS recopier verbatim un copy.md existant. Chaque reason / section doit être ré-rédigée depuis les fresh insights, ses verbatim quotes, ses stats avec timeframe.

## Implémentation pipeline (à wirer dans Sprint 21+)

Cette doctrine sera implémentée comme :

1. **Slash command `/lp-creator-from-blank <client> <page_type>`** qui :
   - Lance les 6 fetchs en parallèle (Step 1)
   - Synthétise les fresh insights (Step 2)
   - Présente les 3 angles distincts au user (Step 3)
   - Attend choix puis enchaîne Phase 1 → 3 → handoff moteur_gsg

2. **BriefV2 schema field** : `chosen_angle: str` (mandatory) — captures le choix step 4 + horodatage + rationale

3. **Audit gate `content_angle_freshness_check`** dans `cro_methodology_audit` :
   - Si le `chosen_angle` matche un angle déjà utilisé pour ce client+page_type dans `data/_briefs_v2/` archive → warning "angle recyclé"
   - Le user peut override mais doit le confirmer explicitement

4. **Webapp wizard étape "Choisir un angle"** entre brief et stratégie CRO

## Référencement

- `MEMORY.md` index → cette doctrine listée
- `CODE_DOCTRINE.md` → règle hard ajoutée
- `FINAL_ACCEPTANCE_TEST_TODO.md` (déjà existant) → mis à jour pour intégrer Step 1-6 dans le protocole "from blank"
- Sprint 21+ epic → implémentation slash command + schema + audit gate
