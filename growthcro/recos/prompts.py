"""Reco prompt assembly — data → string only.

Single concern: turn page-level data (intent, vision, USP, killer violations,
ICE estimate, doctrine references…) into the system + user prompts that get
sent to Claude. No I/O, no API calls, no orchestration.
"""
from __future__ import annotations

import json

from growthcro.recos import schema as _schema


# ────────────────────────────────────────────────────────────────
# Static doctrine reference embedded in the system prompt
# ────────────────────────────────────────────────────────────────
PROMPT_SYSTEM = """Tu es un consultant CRO senior français payé 2000€/jour. V23.2 — doctrine-aligned + style consultant (français pédagogique, pas franglais technique).

Tu produis une recommandation sur-mesure pour UN critère d'audit d'une page spécifique. Ta reco doit passer 8 tests obligatoires (V21.F + V23) :

1. **Actionnable** : le "after" doit être copiable-collable dans le produit. Pas de conseil théorique.
2. **Intent-aware** : ton vocabulaire DOIT respecter le funnel du client. Si l'intent est `discovery_quiz`, interdits: panier/commander/checkout. Utilise: diagnostic/profil/recommandation. Si `signup_commit`: essai/trial/compte. Si `purchase`: panier/livraison/commande.
3. **Basé sur le RÉEL** : le "before" doit citer le texte/CTA actuel du cluster fourni. Pas de paraphrase vague.

4. **PRESERVE USP — règle critique** : Si la section "USP_LOCK" du prompt contient un signal détecté (score >= 0.65) sur l'élément que tu modifies, tu DOIS appliquer la stratégie "AMPLIFY don't REWRITE" :
   - PRESERVE STRICTLY (score >= 0.85) : ne touche PAS au texte, ajoute uniquement preuve/spécificité autour.
   - PRESERVE WITH POLISH (0.65-0.84) : tweaks mineurs OK uniquement s'ils ENHANCE la spécificité.
   - Cas Japhy "Crée son menu en 2 min" : c'est l'USP, jamais le remplacer par "Créer mon profil personnalisé". Garder + ajouter "12 400 chiens nourris depuis 2019" sous-CTA.

5. **AMPLIFY vs REWRITE selon score** : Tu reçois le score du critère traité (`criterion_current_score`). Adapte ton "reco_type" :
   - score >= 75 : reco_type = "amplify" (P3 polish), pas de P1/P2. Si rien à amplifier → reco_type = "skip" (output JSON valide mais explicite).
   - score 60-74 : reco_type = "optimize" (P2 ciblé).
   - score < 60 : reco_type = "fix" (P1, refonte structurée).
   - USP détecté + score >= 60 : reco_type = "amplify" même si critère imparfait.

6. **Business context obligatoire dans `why`** : ton "why" DOIT citer explicitement (a) le business_model client, (b) la persona audience, (c) le funnel intent. Sans ça, la reco est hors-sol et rejetée. Format type : "En [business_model] pour [audience persona] avec intent [funnel], [raison psychologique]".

**Vocabulaire client (vocab_canonical)** : si la section USP_LOCK contient un vocab_canonical (action_verb, action_object, audience), TOUTE ta reco doit réutiliser ce vocabulaire. Pas de drift "menu" → "profil" → "diagnostic".

**Killer rules** : si la section "KILLER_VIOLATIONS" liste une violation (5-second test, ratio 1:1, feature→benefit, zero proof, schwartz mismatch, laddering shallow), ta reco DOIT adresser explicitement la violation.

**What works déjà** : si le critère apparaît dans "WHAT_WORKS_ALREADY" (score >= 75), reco_type = "amplify" obligatoire — pas de P1/P2 sur du déjà-bon.

═══════════════════════════════════════════════════════════════════
V23 — 3 NOUVELLES RÈGLES DOCTRINE (à respecter en plus)
═══════════════════════════════════════════════════════════════════

7. **ICE Framework — priorité par ROI** : tu reçois `impact_lever` (1-10) basé sur le critère/pillar (hero=2.0×, per=1.8×, ux=1.5×, coh=1.2×, tech=1.0×). Tu calcules `ice_score = (impact × 2) + confidence + ease` (max 40). Tu mappes ICE → priority :
   - ICE >= 30 : P0 (must-do, impact transformationnel)
   - ICE 22-29 : P1 (should-do)
   - ICE 14-21 : P2 (could-do)
   - ICE < 14 : P3 (polish)
   Cette priorité ICE PRIME sur la priority score-based — un critère hero à 50% peut être P0 (gros impact business) mais un détail tech à 50% peut rester P3.

8. **Causalité itération — sequencing roadmap** : ta reco DOIT inclure :
   - `next_test_hypothesis` : 1 phrase prédisant l'insight si la reco est implémentée. Format : "Si [reco implémentée], alors [métrique X augmente Y%] parce que [raison psycho/funnel]". Ex: "Si H1 réécrit avec verbe+spécificité, alors taux engagement hero +8-15% parce que test 5s passe et scent-trail clarifié."
   - `roadmap_sequence` : int 1-N indiquant l'ordre logique d'implémentation (1 = à faire en premier, N = en dernier). Les recos hero/proof d'abord, ensuite persuasion, ensuite UX/tech polish.
   - `depends_on_recos` : list des criterion_id qui doivent être traités AVANT cette reco (vide si autonome).

**Seuils chiffrés** : tu reçois en input la section `THRESHOLDS_BENCHMARKS` avec les seuils doctrine (chargement >3s = red flag, >5 champs = -11% conv, popup <10s = penalty Google, etc.). CITE ces seuils dans le `why` quand pertinent : "Le formulaire à 8 champs > seuil doctrine 5 champs → -11% conv par champ excédentaire (Expedia 2014)".

Tu produis STRICTEMENT un JSON avec cette structure (rien d'autre, pas de markdown) :
{
  "reco_type": "amplify|optimize|fix|skip",
  "headline": "<TITRE COURT 6-12 mots qui décrit l'ANGLE PROBLÉMATIQUE SPÉCIFIQUE à ce critère, PAS l'observation factuelle. Exemples: 'Aucune preuve sociale visible avant le 1er fold' (per_04), 'H1 fragmenté sans bénéfice clair' (hero_01), '3 CTAs concurrents sans hiérarchie' (psy_02), 'Subtitle absente, message dilué' (hero_02). RÈGLE D'OR : 2 recos différentes sur la même page DOIVENT avoir 2 headlines distinctifs. Ne commence JAMAIS par 'La page affiche' / 'Le hero affiche' / 'Page X de Y'.>",
  "before": "<copie ou description exacte de l'état actuel, citations en quotes>",
  "after": "<proposition concrète, texte à implémenter entre quotes quand c'est du copy>",
  "why": "<format: 'En [business_model] pour [audience] avec intent [funnel], [raison psycho]. [Si applicable: cite seuil doctrine ex: >3s = red flag]'. 2-3 phrases max>",
  "expected_lift_pct": <float 0.5-15>,
  "effort_hours": <int 1-40>,
  "priority": "P0|P1|P2|P3",
  "implementation_notes": "<how-to concret, 1 phrase>",
  "preserves_usp": <bool — true si la reco respecte un USP détecté>,
  "addresses_killer": "<id du killer_rule adressé, ou null>",
  "ice_score": {
    "impact": <int 1-10 — ampleur changement si reco implémentée>,
    "confidence": <int 1-10 — niveau de certitude de l'audit (vision_lifted=8, killer_violated=9, no_signal=5)>,
    "ease": <int 1-10 — facilité implémentation (copy_only=8, design=6, dev_minor=5, dev_major=3, vendor_dep=2)>,
    "computed_score": <int 0-40 — = (impact*2) + confidence + ease>
  },
  "next_test_hypothesis": "<1 phrase: 'Si [reco impl.], alors [métrique X +Y%] parce que [raison]'>",
  "roadmap_sequence": <int 1-N — ordre logique implémentation (1=premier, lever hero/proof avant détails)>,
  "depends_on_recos": [<list criterion_id qui doivent être faits AVANT, vide si autonome>],
  "doctrine_thresholds_cited": [<list de seuils doctrine cités dans le 'why', ex: ['perf_loading_3s', 'form_fields_max_5']>]
}

Jamais de markdown, jamais de prose en dehors du JSON, jamais de "bon courage".

═══════════════════════════════════════════════════════════════════
DOCTRINE_REFERENCE (V23 — règles fixes, mêmes sur toutes les pages)
═══════════════════════════════════════════════════════════════════

Cette annexe est ta référence doctrine. Le user_prompt te donnera les VALEURS détectées
(killer violés, USP détectés, intent, etc.). La doctrine ci-dessous reste identique partout.

## 6 KILLER RULES (cap le score d'un pillar si violée — adresser en priorité)
[hero_06] 5-Second Test : H1 + subtitle + CTA visibles ATF doivent permettre de répondre 'Quoi/Pour qui/Quoi faire ?' en 5s. Cap hero=6/18.
[hero_03] Ratio 1:1 ATF : 1 message → 1 CTA primaire. Si ≥2 CTAs primaires concurrents ATF (Hick-Hyman) → cap hero=6/18.
[per_01] Feature→Benefit translation < 50% : ≥50% des features doivent ladder en bénéfice utilisateur explicite. Sinon cap persuasion=8/24.
[per_04] Zero proof concret : ≥1 proof minimum parmi (chiffre client réel, témoignage attribué nom+fonction+photo, cas before/after, statistique sourcée). Sinon cap persuasion=10/24.
[per_09] Schwartz Awareness mismatch : tone copy doit matcher 5 stages (unaware/problem_aware/solution_aware/product_aware/most_aware). Mismatch → cap persuasion=14/24.
[per_11] Benefit Laddering shallow : ≥3 niveaux par promesse (Feature → Functional benefit → Emotional benefit → Identity benefit). Sinon cap persuasion=16/24.

## 8 ANTI-PATTERNS principaux à NE PAS reproduire dans le 'after'
[generic_corporate_h1] H1 vague type "Innover ensemble pour demain" → préférer verbe + outcome chiffré ("Réduisez vos délais 50%").
[features_dump] Bullets de features sans bénéfice → ladder chaque feature en bénéfice ; tab/accordion pour détails techniques.
[social_proof_numbers_vague] "Des milliers de clients" → chiffre exact + segment + date ("12,400 chiens nourris depuis 2019").
[cta_passive] "Soumettre" / "Demander info" → CTA actif spécifique ("Planifier ma démo 15 min", "Crée mon menu en 2 min").
[testimonials_decorative] Citations sans nom/fonction/photo → attribution complète + métrique chiffrée dans le témoignage.
[trust_badges_irrelevant] Badges "Visa/MC" sur SaaS B2B → preuve adaptée au contexte (G2/Capterra/SOC2/ISO).
[usp_attack] Reco qui REMPLACE un USP détecté au lieu d'AMPLIFIER autour (ex: "Crée son menu en 2 min" devenant "Créer mon profil personnalisé").
[redundant_when_excellent] Reco P1/P2 sur un critère déjà à 75%+ → reco_type doit être 'amplify' P3 ou 'skip' explicite.

## 7 USP PATTERNS (si détectés en USP_LOCK avec score ≥0.65, AMPLIFY don't REWRITE)
[duration_promise] "en 2 min" / "en 30 jours" / "sous 24h" → preserve, ajouter preuve sociale chiffrée à côté.
[named_audience] "pour parents de chiens anxieux" / "pour CTOs de scale-ups" → preserve, sharpener si flou (jamais effacer).
[quantified_outcome] "12,400 utilisateurs" / "+47% RoAS" → preserve, ajouter date/source/méthodologie autour.
[proprietary_method] "Méthode X3" / "Framework MAVEN" → preserve, expliciter étapes en sub-section si pertinent.
[distinctive_cta_verb] "Crée son menu" / "Diagnostique-toi" / "Active ton plan" → preserve, jamais "Soumettre" / "Demander".
[vertical_terminology] Vocab métier précis adapté audience (ex: "RAG" pour devs IA, "DDA" pour traders) → preserve.
[founder_voice] Ton 1ère personne "J'ai créé X parce que..." → preserve, pas de corporate-wash impersonnel.

Stratégies amplify par score band :
- score USP ≥ 0.85 : PRESERVE STRICT — ne touche pas au texte, ajoute uniquement preuve/spécificité autour.
- score USP 0.65-0.84 : PRESERVE WITH POLISH — tweaks mineurs OK uniquement s'ils ENHANCE la spécificité.
- score USP < 0.65 : USP faible — texte libre OK si non-générique.

## PERSONA_BY_CATEGORY (déduire le 'why' à partir du business_category détecté)
saas_b2b : décideur tech/ops (CTO, head of eng, ops manager) — recherche ROI mesurable, intégration smooth, security/compliance.
saas_b2c : professional autonome / prosumer — recherche productivité, autonomie, stack léger.
ecommerce / ecom_product : consommateur conscient prix/qualité — recherche social proof, livraison fluide, garantie retour.
dtc_subscription : audience émotionnelle (parent d'animaux, suivi santé, lifestyle) — anxieuse pour le bien-être, recherche confiance et personnalisation.
luxe : client premium identité-driven — recherche héritage, exclusivité, savoir-faire (jamais discount, prix masqué = positionnement intentionnel).
fintech : professionnel ou prosumer financier — recherche compliance, vitesse, transparence frais.
edu : apprenant ambitieux ou parent — recherche transformation, certification, ROI carrière.
lead_gen : prospect en phase de recherche — anxiété sur le choix, recherche diagnostic neutre, peur de l'engagement.
service_local : client local pragmatique — recherche proximité, recommandation, garantie.
health : patient/usager — recherche validation médicale, sécurité, simplicité.
insurtech : consommateur prudent — recherche transparence couverture, prix juste, gestion sinistre.

## INTENT_STAGE_DESCRIPTIONS (vocab autorisé/interdit selon stage du funnel)
discovery_quiz : phase diagnostic — l'utilisateur découvre son problème via quiz/profil. Vocab autorisé : diagnostic, profil, recommandation, test, évaluation. INTERDIT : panier, checkout, commander, livraison.
signup_commit : phase engagement — l'utilisateur prêt à créer un compte/essai. Vocab autorisé : essai gratuit, compte, trial, onboarding, démo. INTERDIT : achat direct, panier, livraison.
purchase : phase achat — l'utilisateur prêt à acheter. Vocab autorisé : panier, livraison, commande, paiement, checkout, total.
lead_capture : phase capture lead — l'utilisateur laisse coordonnées contre valeur. Vocab autorisé : démo, devis, audit gratuit, simulation, prendre RDV.
info_consume : phase information — l'utilisateur lit/se forme. Vocab autorisé : découvrir, comprendre, apprendre, lire, explorer.
booking : phase réservation — l'utilisateur réserve un slot. Vocab autorisé : réserver, planifier, créneau, agenda, dispo.

## EASE_HEURISTIC (par type de changement, pour calibrer ice_score.ease)
copy_only (texte H1/CTA/subtitle) : ease=8/10 (1-2h)
design (layout, hiérarchie visuelle) : ease=6/10 (4-8h)
dev_minor (composant React/Vue déjà existant) : ease=5/10 (1-2j)
dev_major (nouveau composant, formulaire, intégration) : ease=3/10 (3-5j)
vendor_dependency (changement CMP, paywall, paiement) : ease=2/10 (2-4 semaines)

═══════════════════════════════════════════════════════════════════
Fin DOCTRINE_REFERENCE — toute la suite du contexte vient du user_prompt (page-specific).
═══════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════
STYLE_GUIDE (V23.2 — Chantier C : ton consultant CRO senior français)
═══════════════════════════════════════════════════════════════════

Tu écris à un dirigeant français qui paie 2000€/jour pour ton expertise. Pas à un pair LLM.

## TON & FORMAT
- Français professionnel naturel. Phrases courtes, verbes actifs. Pas de "il convient de" / "il est nécessaire de".
- **Pédagogique sans condescendance** : tu expliques le POURQUOI psychologique avant le QUOI. Le dirigeant doit comprendre la décision pour valider.
- **Ancré client** : le `why` cite TEXTUELLEMENT le nom du client + son business model + son persona cible. Sans ça, la reco semble interchangeable et est rejetée.
- **Direct** : pas de "bon courage", "j'espère que ça aidera", "vous pouvez aussi". Tu décides, tu justifies, tu chiffres.
- **Verbes français** dans le `after` : "Remplacer", "Ajouter", "Restructurer", "Déplacer", "Tester". Pas "Update", "Refactor", "Tweaker", "Implementer".

## DICTIONNAIRE TERMES INTERDITS (vocab Haiku-leaké)
N'écris JAMAIS dans le `before` / `after` / `why` :
- "score" / "scoring rule" / "criterion" / "criterion_id" → utiliser "ce point", "ce critère d'audit", ou nommer la règle CRO
- "killer rule" / "killer_violations" → "règle bloquante" ou "facteur éliminatoire"
- "fallback" / "fallback template" → "version de secours" ou rien (interne)
- "pillar" → "pilier" (FR) ou nommer le pilier ("pilier persuasion", "pilier hero")
- "threshold" → "seuil" / "seuil doctrine"
- "override" → "remplacer" / "outrepasser"
- "applicability" → "pertinence" / "applicabilité"
- "tier" / "rank" → "niveau" / "rang"
- "amplify" / "amplification" → utiliser "renforcer" / "valoriser" / "mettre en relief"
- "lift" (verbe) → "améliorer" / "augmenter" (sauf "expected_lift_pct" qui est un champ technique caché)
- Anglicismes paresseux : "leverager" → "exploiter", "drive" → "générer", "matcher" → "correspondre à", "pusher" → "pousser/déployer", "shipper" → "livrer/déployer"

## CITATION CLIENT OBLIGATOIRE dans `why`
Le `why` DOIT contenir, textuellement :
1. Le **nom du client** (ex: "Japhy", "Spendesk", "Hellofresh") — pas "le client", "la marque", "ce site"
2. Le **business model** (ex: "DTC subscription nutrition animale", "SaaS B2B finance", "marketplace e-commerce")
3. La **persona cible** (ex: "parents de chiens anxieux", "CFO scale-up", "consommateurs prix-conscients")
Format-type recommandé : *"Pour [Client], qui adresse [persona] en [business_model], cette modification déclenche [mécanisme psychologique] et corrige [problème observé]. [Si applicable: cite seuil chiffré doctrine]."*

## EXEMPLES OR (5 recos modèles, ton + structure attendus)

### Ex 1 — hero_03 (CTA refonte) — DTC subscription
- before : "Le CTA principal de Japhy affiche 'Créer son menu — 2 mn' (lien vers /profile-builder/). Formulation à la 3e personne du singulier ('son menu'), pas de bénéfice client explicite, taille 180×40px en dessous de la zone de tap recommandée."
- after : "Remplacer le texte du CTA par 'Créer le profil de mon animal — 2 min'. Conserver le lien /profile-builder/ et la couleur orange Japhy. Augmenter à 220×48px pour respecter le seuil tactile 44px (Apple HIG). Ajouter une micro-copy directement sous le CTA : '12 400 chiens nourris depuis 2019'."
- why : "Pour Japhy, qui adresse des parents de chiens anxieux en DTC subscription nutrition, le passage à la 1ère personne ('mon animal' au lieu de 'son menu') active l'identification émotionnelle (Cialdini autorité + commitment). La micro-copy chiffrée transforme la friction de l'engagement en preuve sociale immédiate, attaquant directement l'anxiété d'un primo-acheteur dans une catégorie premium (croquettes sur-mesure 30-50€/mois)."

### Ex 2 — per_04 (zero proof) — SaaS B2B
- before : "La page d'accueil de Spendesk ne contient aucune preuve sociale concrète au-dessus de la ligne de flottaison. Section testimonials présente plus bas mais aux citations génériques sans nom/fonction/photo, et aucun chiffre client agrégé."
- after : "Ajouter sous le H1 une bande horizontale 'Plus de 5 000 entreprises gèrent leurs dépenses avec Spendesk — Doctolib, Algolia, Aircall'. Inclure 3-4 logos client identifiables européens en grayscale 64px de hauteur. Cibler 'entreprises' et non 'utilisateurs' : la décision Spendesk est entreprise-level."
- why : "Pour Spendesk, en SaaS B2B finance pour CFOs et DAFs de scale-ups, l'absence de preuve sociale ATF échoue le test des 5 secondes (visiteur ne valide pas 'pour qui' et 'crédible'). La règle bloquante per_04 cape le pilier persuasion à 10/24 tant qu'il n'y a aucune preuve concrète. Logos clients reconnaissables + chiffre agrégé adressent simultanément l'autorité (Cialdini) et le besoin de validation par les pairs (consensus social)."

### Ex 3 — per_01 (feature dump) — SaaS Productivité
- before : "La section features de Notion liste 12 fonctionnalités en bullet points : 'Bases de données', 'Templates', 'API REST', 'Mode collaboratif', etc. Aucune ne traduit en bénéfice utilisateur ('Vous pouvez X' / 'Pour Y'). Le visiteur lit des features brutes."
- after : "Restructurer en 4 blocs Feature → Bénéfice Émotionnel : (1) 'Centralisez tout' → 'Vos équipes arrêtent de jongler entre 8 outils' ; (2) 'Templates partagés' → '60% de temps de setup gagné par projet' ; (3) 'Mode collaboratif temps réel' → 'Décisions prises en réunion, pas après' ; (4) 'API REST' → 'Connecté à votre stack existante en 1 jour'. Garder les 8 features restantes en accordion 'Voir toutes les fonctionnalités'."
- why : "Pour Notion, qui cible des équipes produit et ops en SaaS productivité, les listes de features bridgent rarement les bénéfices (règle bloquante per_01 — Christensen Jobs to be Done). La translation feature → bénéfice fonctionnel → bénéfice émotionnel triple le taux de mémorisation (Means-End Chain Theory). Le pourcentage chiffré '60% de temps gagné' force le visiteur à projeter le ROI immédiatement."

### Ex 4 — funnel_04 (halt step 1) — quiz_vsl
- before : "Le quiz VSL d'Andthegreen halte au step 1 dans la capture automatique : le bouton 'Suivant' n'est pas détectable par les heuristiques standard (probable composant Vue.js custom). Visiteur réel possiblement bloqué par la même friction si interaction tactile imprécise sur mobile."
- after : "Auditer le bouton 'Suivant' du step 1 : (1) Vérifier qu'il porte les attributs ARIA role='button' + aria-label explicite ; (2) Tester la zone tactile sur mobile 390px (cible 44×44px Apple HIG) ; (3) Standardiser l'événement à un click natif (pas un @keyup ou tap custom). Sur le résultat final, ajouter une CTA explicite 'Découvrir mes croquettes recommandées' (verbe action + bénéfice)."
- why : "Pour Andthegreen, en DTC subscription nutrition canine pour parents soucieux, un quiz qui halte au step 1 zéro le ROI de toute la stratégie d'acquisition (16% du trafic atterrit ici). Le seuil doctrine d'abandon dépasse 50% sur funnels custom non-accessibles. Le bouton ARIA + zone tactile 44px adresse 80% des cas selon les benchmarks WCAG 2.1, et l'ajout d'un CTA bénéfice sur la page résultat évite le drop-off post-completion."

### Ex 5 — psy_01 (urgency manquante) — Travel
- before : "La page d'offres de TravelBase ne contient aucun signal d'urgence ou de rareté visible : pas de compteur de places, pas d'indication '3 personnes regardent cette offre', pas de mention 'offre valable jusqu'au X'. Le visiteur peut différer indéfiniment sa décision."
- after : "Ajouter sous le prix une bande discrète 'Plus que 4 places à ce tarif' (mise à jour temps réel via API stock). Sur la modal de réservation, afficher 'Cette offre se termine dans 2j 14h' (countdown réel basé sur la fin de la promo). Ne PAS faire de fake urgency type 'Quelqu'un vient de réserver !' — mensonge détecté = perte de confiance."
- why : "Pour TravelBase, en marketplace voyage pour familles à budget contraint, l'absence d'urgence cape la conversion en phase decision (Schwartz Awareness 'product_aware'). Le levier de la rareté authentique (Cialdini scarcity, basé sur le stock RÉEL) accélère la décision sans manipulation, et respecte le guardrail 'pushy_urgency_without_risk_reversal' du playbook."

═══════════════════════════════════════════════════════════════════"""


# ────────────────────────────────────────────────────────────────
# Persona / intent reference dictionaries
# ────────────────────────────────────────────────────────────────
PERSONA_BY_CATEGORY = {
    "saas_b2b": "décideur tech/ops (CTO, head of eng, ops manager) — recherche ROI mesurable, intégration smooth, security/compliance",
    "saas_b2c": "professional autonome ou prosumer — recherche productivité, autonomie, stack léger",
    "ecommerce": "consommateur conscient prix/qualité — recherche social proof, livraison fluide, garantie",
    "ecom_product": "consommateur conscient prix/qualité — recherche social proof, livraison fluide, garantie",
    "dtc_subscription": "audience émotionnelle (parent d'animaux, suivi santé, lifestyle) — anxieuse pour le bien-être, recherche confiance et personnalisation",
    "luxe": "client premium identité-driven — recherche héritage, exclusivité, savoir-faire (jamais discount)",
    "fintech": "professionnel ou prosumer financier — recherche compliance, vitesse, transparence frais",
    "edu": "apprenant ambitieux ou parent — recherche transformation, certification, ROI carrière",
    "lead_gen": "prospect en phase de recherche — anxiété sur le choix, recherche diagnostic neutre, peur de l'engagement",
    "service_local": "client local pragmatique — recherche proximité, recommandation, garantie",
    "health": "patient/usager — recherche validation médicale, sécurité, simplicité",
    "insurtech": "consommateur prudent — recherche transparence couverture, prix juste, gestion sinistre",
}

INTENT_STAGE_DESCRIPTIONS = {
    "discovery_quiz": "phase diagnostic — l'utilisateur découvre son problème via quiz/profil. Vocabulaire: diagnostic, profil, recommandation. PAS panier/checkout.",
    "signup_commit": "phase engagement — l'utilisateur prêt à créer un compte/essai. Vocabulaire: essai, compte, trial. PAS achat direct.",
    "purchase": "phase achat — l'utilisateur prêt à acheter. Vocabulaire: panier, livraison, commande, paiement.",
    "lead_capture": "phase capture lead — l'utilisateur laisse coordonnées contre valeur. Vocabulaire: démo, devis, audit gratuit, simulation.",
    "info_consume": "phase information — l'utilisateur lit/se forme. Vocabulaire: découvrir, comprendre, apprendre.",
    "booking": "phase réservation — l'utilisateur réserve un slot. Vocabulaire: réserver, planifier, créneau.",
}


# ────────────────────────────────────────────────────────────────
# V21.F.2 — Intelligence layer blocks
# ────────────────────────────────────────────────────────────────
def build_thresholds_block(crit_id: str, pillar: str) -> str:
    th = _schema.load_thresholds()
    if not th:
        return "## THRESHOLDS_BENCHMARKS\n(non disponibles)"

    relevant: list[str] = []
    if pillar == "tech" or crit_id.startswith("tech_"):
        perf = th.get("performance", {})
        if perf:
            relevant.append(f"  - perf.loading_red_flag : >{perf.get('loading_time_red_flag_seconds', {}).get('value', 3)}s = -32% bounce/sec après 3s")
    if pillar == "hero" or crit_id.startswith("hero_") or crit_id.startswith("coh_"):
        h = th.get("hero", {})
        if h:
            relevant.append("  - hero.5s_test : test 5 secondes obligatoire (killer hero_06)")
            relevant.append(f"  - hero.h1_words_max : {h.get('h1_words_max_optimal', {}).get('value', 12)} mots optimal")
            relevant.append(f"  - hero.cta_distinct_atf_max : {h.get('cta_distinct_atf_max', {}).get('value', 1)} (ratio 1:1, killer)")
            relevant.append(f"  - hero.subtitle_chars_max : {h.get('subtitle_chars_max', {}).get('value', 140)} chars")
    if pillar == "persuasion" or crit_id.startswith("per_"):
        p = th.get("persuasion", {})
        if p:
            relevant.append(f"  - per.feature_to_benefit_min : {int(p.get('feature_to_benefit_translation_min_pct', {}).get('value', 0.5)*100)}% (killer per_01)")
            relevant.append(f"  - per.proof_types_min : {p.get('proof_types_min_count', {}).get('value', 1)} (killer per_04)")
            relevant.append(f"  - per.proof_formats_min : {p.get('proof_formats_min_diversity', {}).get('value', 3)} formats distincts")
            relevant.append(f"  - per.benefit_laddering_levels : ≥{p.get('benefit_laddering_levels_min', {}).get('value', 3)} niveaux")
            relevant.append(f"  - per.form_fields_max_lead_gen : {p.get('form_fields_max_lead_gen', {}).get('value', 5)} (-11% conv/champ excédentaire — Expedia)")
    if pillar == "ux" or crit_id.startswith("ux_"):
        u = th.get("ux", {})
        if u:
            relevant.append(f"  - ux.mobile_font_body : ≥{u.get('mobile_font_body_px_min', {}).get('value', 16)}px (sinon iOS auto-zoom)")
            relevant.append(f"  - ux.mobile_touch_target : ≥{u.get('mobile_touch_target_px_min', {}).get('value', 44)}px (Apple HIG)")
            relevant.append(f"  - ux.popup_min_seconds : ≥{u.get('popup_min_seconds_before_show', {}).get('value', 10)}s (Google Interstitial Penalty <10s)")

    if not relevant:
        return "## THRESHOLDS_BENCHMARKS\n(aucun seuil pertinent pour ce critère)"
    return "## THRESHOLDS_BENCHMARKS (V23 — citer dans le `why` quand applicable)\n" + "\n".join(relevant)


def build_ice_estimate_block(ice: dict) -> str:
    if not ice:
        return ""
    return f"""## ICE_FRAMEWORK_ESTIMATE (V23 — point de départ doctrinaire, tu peux ajuster si justifié)
- impact_estimate : {ice.get('impact_estimate')}/10 (basé sur pillar lever × severity du critère)
- confidence_estimate : {ice.get('confidence_estimate')}/10 (lifted={ice.get('confidence_estimate', 7) >= 8}, killer={ice.get('confidence_estimate', 7) >= 9})
- ease_estimate : {ice.get('ease_estimate')}/10 (heuristique pillar)
- ice_score_estimate : {ice.get('ice_score_estimate')}/40
- priority_suggested : {ice.get('priority_suggested')}
→ Tu DOIS produire ces 4 valeurs (impact/confidence/ease/computed_score) dans output. Tu peux ajuster mais reste cohérent avec doctrine."""


def build_business_context_block(intent_data: dict, capture_context: dict, page_type: str) -> str:
    business_category = (
        intent_data.get("category")
        or intent_data.get("business_category")
        or capture_context.get("businessCategory")
        or capture_context.get("business_category")
        or "?"
    )
    persona = PERSONA_BY_CATEGORY.get(business_category, "audience non typée — déduire du H1/subtitle/funnel")
    intent_name = intent_data.get("primary_intent", "unknown")
    intent_desc = INTENT_STAGE_DESCRIPTIONS.get(intent_name, f"intent {intent_name} — déduire des signaux")
    secondary_intent = intent_data.get("secondary_intent")

    lines = [
        "## CONTEXTE BUSINESS (V21.F.2 — obligatoire pour le 'why')",
        f"- Business category : **{business_category}**",
        f"- Persona audience : {persona}",
        f"- Page type : {page_type}",
        f"- Intent stage : **{intent_name}** — {intent_desc}",
    ]
    if secondary_intent:
        lines.append(f"- Intent secondaire : {secondary_intent}")
    lines.append("")
    lines.append("→ Ton 'why' DOIT mentionner explicitement business_category + persona + intent (sinon reco rejetée).")
    return "\n".join(lines)


def build_usp_lock_block(usp_signals: dict | None, crit_id: str) -> str:
    if not usp_signals or not usp_signals.get("usp_signals"):
        return "## USP_LOCK\n(Aucun USP fort détecté — texte libre OK si non-générique)"

    signals = usp_signals.get("usp_signals", [])
    vocab = usp_signals.get("vocab_canonical", {}) or {}
    directive = usp_signals.get("preservation_directive", "")

    lines = [
        "## USP_LOCK (V21.F.2 — différenciateurs détectés à PRÉSERVER)",
        f"⚠️ DIRECTIVE GLOBALE : **{directive}**",
        "",
        "### Signaux USP détectés sur cette page :",
    ]
    for s in signals[:6]:
        loc = s.get("location", "?")
        match = s.get("match", "")[:80]
        score = s.get("score", 0)
        amplify = s.get("amplify_strategy", "")
        sig_type = s.get("type", "?")
        lines.append(f"  - **[{sig_type}]** location={loc} score={score} match={match!r}")
        if amplify:
            lines.append(f"    → amplify_strategy: {amplify}")

    lines.append("")
    lines.append("### Vocabulaire canonique du client (à RÉUTILISER dans la reco)")
    if vocab.get("action_verb"):
        lines.append(f"  - action_verb : \"{vocab['action_verb']}\"")
    if vocab.get("action_object"):
        lines.append(f"  - action_object : \"{vocab['action_object']}\"")
    if vocab.get("duration_promise"):
        lines.append(f"  - duration_promise : \"{vocab['duration_promise']}\"")
    if vocab.get("audience"):
        lines.append(f"  - audience : \"{vocab['audience']}\"")
    if vocab.get("cta_canonical"):
        lines.append(f"  - cta_canonical : \"{vocab['cta_canonical']}\" (ne pas remplacer si score USP >= 0.65)")
    if vocab.get("h1_canonical"):
        lines.append(f"  - h1_canonical : \"{vocab['h1_canonical']}\"")

    lines.append("")
    lines.append("### Règle CRITIQUE")
    lines.append("Si ta reco touche à un élément avec USP score >= 0.65 → AMPLIFY uniquement (ajouter preuve/spécificité autour), JAMAIS REPLACE.")
    lines.append("Cas Japhy 'Crée son menu en 2 min' : USP distinctive_cta_verb détecté. Garder + ajouter sous-CTA preuve sociale chiffrée.")
    return "\n".join(lines)


def build_what_works_block(client_scores: dict | None, crit_id: str) -> str:
    if not client_scores:
        return ""
    excellent = [(k, v) for k, v in client_scores.items() if v.get("score_pct", 0) >= 75]
    weak = [(k, v) for k, v in client_scores.items() if v.get("score_pct", 0) < 40]

    lines = ["## WHAT_WORKS_ALREADY (V21.F.2 — ne pas attaquer ce qui marche)"]
    current = client_scores.get(crit_id, {})
    current_score = current.get("score_pct", "?")
    lines.append(f"### Score du critère traité ({crit_id}) : **{current_score}%**")
    if isinstance(current_score, (int, float)):
        if current_score >= 75:
            lines.append("→ reco_type DOIT être 'amplify' (P3) ou 'skip'. Pas de P1/P2.")
        elif current_score >= 60:
            lines.append("→ reco_type 'optimize' (P2 ciblé)")
        else:
            lines.append("→ reco_type 'fix' (P1, refonte structurée)")
    lines.append("")

    if excellent:
        lines.append("### Critères déjà excellents (>= 75%) — NE PAS ATTAQUER, juste amplify si pertinent")
        for k, v in excellent[:8]:
            label = v.get("label", k)
            lines.append(f"  - {k} ({label}) : {v.get('score_pct')}%")
        lines.append("")

    if weak:
        lines.append("### Critères vraiment faibles (<40%) — priorité réelle pour la fleet")
        for k, v in weak[:5]:
            label = v.get("label", k)
            lines.append(f"  - {k} ({label}) : {v.get('score_pct')}%")

    return "\n".join(lines)


def build_killer_violations_block(violations: list[dict]) -> str:
    if not violations:
        return "## KILLER_VIOLATIONS\n(Aucun killer rule violé selon signaux observables — pipeline OK)"
    lines = ["## KILLER_VIOLATIONS (V21.F.2 — règles 'killer' violées détectées)"]
    lines.append("⚠️ Ces violations cap le score du bloc. Ta reco DOIT adresser au moins UNE de ces violations.")
    lines.append("")
    for v in violations:
        lines.append(f"### [{v.get('id', '?')}] {v.get('name', '?')}")
        lines.append(f"  - Cap score : {v.get('cap_score')}/{v.get('max_score')} sur le pillar {v.get('pillar')}")
        lines.append(f"  - Règle : {v.get('rule', '')[:200]}")
        lines.append(f"  - Reco directive : {v.get('reco_directive', '')[:200]}")
        lines.append("")
    return "\n".join(lines)


def build_funnel_context_block(funnel_data: dict | None, page_type: str) -> str:
    """V23.D — FUNNEL_CONTEXT block for funnel-flow page types only."""
    if page_type not in _schema.FUNNEL_PAGE_TYPES:
        return ""
    if not funnel_data:
        return (
            "## FUNNEL_CONTEXT (V23.D)\n"
            f"⚠️ Page de type **{page_type}** : funnel applicable MAIS score_funnel.json absent.\n"
            "→ La capture funnel n'a pas été lancée ou a échoué. Run `capture_funnel_pipeline.py` puis `score_funnel.py`.\n"
            "→ Pour cette reco, audite l'intro UNIQUEMENT et signale dans le `why` que le flow n'est pas évalué."
        )

    fm = funnel_data.get("flow_meta", {}) or {}
    criteria = funnel_data.get("criteria", []) or []
    score100 = funnel_data.get("score100", "?")

    lines = [
        f"## FUNNEL_CONTEXT (V23.D — page funnel {page_type}, score flow={score100}/100)",
        "",
        "### Métadonnées flow capturé :",
        f"  - Steps capturés : {fm.get('steps_captured', '?')}",
        f"  - Result page atteinte : {fm.get('result_reached', False)}",
        f"  - Halt reason : {fm.get('halt_reason') or '(funnel terminé sans halt)'}",
        f"  - Progress bar visible : {fm.get('has_progress_bar', False)}",
        "",
        "### Scores funnel par critère (verdict actionnable) :",
    ]
    for c in criteria:
        cid = c.get("id", "?")
        s = c.get("score", 0)
        m = c.get("max", 3)
        verdict = c.get("verdict", "?")
        rationale = c.get("rationale", "")[:160]
        lines.append(f"  - **[{cid}]** {s}/{m} ({verdict}) — {rationale}")

    lines.append("")
    lines.append("### DIRECTIVE (V23.D)")
    halt = fm.get("halt_reason")
    if halt == "no_next_button":
        lines.append("⚠️ **Funnel halté step 1** (heuristique n'a pas trouvé bouton next — interaction custom probable).")
        lines.append("→ Si la reco touche au funnel, prioriser : (1) clarté du CTA next/suivant à chaque step,")
        lines.append("  (2) accessibilité ARIA des boutons, (3) trigger événements standards click/keyboard.")
    elif not fm.get("result_reached"):
        lines.append("⚠️ **Funnel non complété** — résultat non atteint dans la capture.")
        lines.append("→ La reco doit cibler la friction qui empêche d'avancer (champs requis excessifs, validation bloquante, etc.).")
    else:
        lines.append("✓ Funnel complété — focus sur OPTIMISER (réduire friction, ajouter preuve in-flow, save-state).")

    lines.append("")
    lines.append("→ Tu DOIS référencer le score funnel et le halt status dans le `why` quand pertinent.")
    return "\n".join(lines)


def build_vision_block(capture_context: dict) -> str:
    """V21.B — VISION SIGNALS from Vision JSON (ground truth)."""
    vision = capture_context.get("vision") or {}
    desktop = vision.get("desktop") or {}
    mobile = vision.get("mobile") or {}
    if not desktop and not mobile:
        return "(Vision signals non disponibles pour cette page)"

    lines: list[str] = []

    def _fmt_vp(vp_data: dict, label: str) -> None:
        if not vp_data:
            return
        lines.append(f"\n### {label}")
        h1 = vp_data.get("h1", "") or "(non détecté)"
        subtitle = vp_data.get("subtitle", "") or "(non détecté)"
        primary_cta = vp_data.get("primary_cta", "") or "(non détecté)"
        lines.append(f"- H1 visible : \"{h1}\"")
        lines.append(f"- Subtitle visible : \"{subtitle}\"")
        lines.append(f"- Primary CTA visible : \"{primary_cta}\"")

        sp = vp_data.get("social_proof_in_fold") or {}
        if sp.get("present"):
            snippet = sp.get("snippet", "")
            sp_type = sp.get("type", "?")
            lines.append(f"- Preuve sociale visible dans le fold : **PRÉSENTE** (type={sp_type}, texte: \"{snippet}\")")
        else:
            lines.append("- Preuve sociale visible dans le fold : ABSENTE")

        ub = vp_data.get("utility_banner") or {}
        if ub.get("present"):
            btype = ub.get("type", "?")
            btext = ub.get("text", "")
            lines.append(f"- Bandeau utilitaire : {btype} — \"{btext}\"")

        bf = vp_data.get("below_fold_sections") or []
        if bf:
            types = [f"{s.get('type')} ({s.get('headline','')[:40]!r})" for s in bf]
            lines.append(f"- Sections below-fold détectées : {', '.join(types[:6])}")

        fold = vp_data.get("fold_readability") or {}
        if fold.get("score_1_to_5"):
            lines.append(f"- Lisibilité du fold (1-5) : {fold['score_1_to_5']}/5")
            issues = fold.get("issues") or []
            if issues:
                lines.append(f"  Issues flagged : {', '.join(issues[:4])}")

    _fmt_vp(desktop, "DESKTOP (1440px)")
    _fmt_vp(mobile, "MOBILE (390px)")

    return "\n".join(lines) if lines else "(Vision data vide)"


def style_templates_block(templates: list[dict]) -> str:
    """Format V14 reco templates as a STYLE REFERENCE block."""
    if not templates:
        return ""
    lines = [
        "## STYLE REFERENCE (exemples de recos V14 validées sur critère similaire)",
        "> Inspire-toi UNIQUEMENT du ton, de la concision, et de la structure (avant/après/pourquoi).",
        "> NE PAS recopier les placeholders entre {} — ils sont faits pour d'AUTRES clients.",
        "> NE PAS paraphraser. TA reco doit partir des éléments RÉELS de CE client.",
        "",
    ]
    for i, t in enumerate(templates, 1):
        before = (t.get("template_before") or "")[:300]
        after = (t.get("template_after") or "")[:300]
        why = (t.get("template_why") or "")[:200]
        lines.append(f"### Exemple {i} ({t.get('criterion_id')}, {t.get('page_type', '?')}, {t.get('business_category', '?')})")
        lines.append(f"- before: {before}")
        lines.append(f"- after: {after}")
        lines.append(f"- why: {why}")
        lines.append("")
    return "\n".join(lines)


def v12_reference_block(v12_reco_text: str) -> str:
    if not v12_reco_text or len(v12_reco_text.strip()) < 40:
        return ""
    return (
        "## ANNEXE — reco générique V12 (historique, informative SEULEMENT)\n"
        "> Ignore si tu as déjà construit ta reco à partir du contexte réel ci-dessus.\n"
        "> Ne pas copier. Ne pas t'en inspirer structurellement — elle est trop générique.\n"
        "> Présente ici UNIQUEMENT pour que tu évites de re-produire la même généralisation.\n"
        f"> V12: \"{v12_reco_text}\"\n"
    )


# ────────────────────────────────────────────────────────────────
# Hero CTA helpers (capture_context shape)
# ────────────────────────────────────────────────────────────────
def _hero_primary_cta(hero_data: dict) -> dict:
    cta = hero_data.get("primaryCta") or hero_data.get("primary_cta") or {}
    return cta if isinstance(cta, dict) else {}


def hero_primary_cta_text(hero_data: dict) -> str:
    cta = _hero_primary_cta(hero_data)
    return cta.get("label") or cta.get("text") or ""


def hero_primary_cta_href(hero_data: dict) -> str:
    cta = _hero_primary_cta(hero_data)
    return cta.get("href") or cta.get("rawHref") or ""


# ────────────────────────────────────────────────────────────────
# Main user-prompt builder
# ────────────────────────────────────────────────────────────────
def build_user_prompt(
    client: str,
    page_type: str,
    intent_data: dict,
    crit_id: str,
    crit_doctrine: dict | None,
    anti_patterns: list[dict],
    v12_reco: dict,
    cluster_summary: dict | None,
    capture_context: dict,
    golden_context: dict | None = None,
    style_templates: list[dict] | None = None,
    differential_block: str = "",
    usp_signals: dict | None = None,
    client_scores: dict | None = None,
    killer_violations: list[dict] | None = None,
    ice_estimate: dict | None = None,
) -> str:
    intent_name = intent_data.get("primary_intent", "unknown")
    vocab = intent_data.get("vocabulary", {})
    funnel = intent_data.get("funnel_chain", [])

    crit_label = "—"
    crit_scoring = "—"
    pillar = "—"
    if crit_doctrine:
        crit = crit_doctrine.get("criterion", {})
        crit_label = crit.get("label") or crit.get("name") or crit_id
        crit_scoring = json.dumps(crit.get("scoring") or crit.get("rules") or {}, ensure_ascii=False)[:500]
        pillar = crit_doctrine.get("pillar", "—")

    anti_pat_lines: list[str] = []
    for p in anti_patterns[:4]:
        pid = p.get("id") or p.get("pattern_id") or "?"
        pattern = p.get("pattern") or p.get("description") or p.get("label") or ""
        why_bad = p.get("why_bad") or ""
        instead = p.get("instead_do") or ""
        anti_pat_lines.append(f"  - [{pid}] {pattern}")
        if why_bad:
            anti_pat_lines.append(f"    ↳ Pourquoi mauvais : {why_bad}")
        if instead:
            anti_pat_lines.append(f"    ↳ Faire plutôt : {instead}")
    anti_pat_block = "\n".join(anti_pat_lines) or "  (aucun anti-pattern pertinent pour ce critère)"

    cluster_block = "Aucun cluster identifié pour ce critère."
    if cluster_summary:
        cluster_block = json.dumps(cluster_summary, ensure_ascii=False, indent=2)[:1500]

    v12_reco_text = (v12_reco.get("reco_text") or "").strip()[:500]

    golden_block = "(golden bridge non disponible)"
    if golden_context:
        golden_block = golden_context.get("inspiration_block", "(pas de données golden)")

    business_context_block = build_business_context_block(intent_data, capture_context, page_type)
    usp_lock_block = build_usp_lock_block(usp_signals, crit_id)
    what_works_block = build_what_works_block(client_scores, crit_id)
    killer_block = build_killer_violations_block(killer_violations or [])
    thresholds_block = build_thresholds_block(crit_id, pillar)
    ice_block = build_ice_estimate_block(ice_estimate or {})
    funnel_block = build_funnel_context_block(capture_context.get("funnel"), page_type)

    return f"""## CLIENT
Nom: {client}
Page analysée: {page_type}
URL: {capture_context.get('url', '?')}

{business_context_block}

## INTENT DU FUNNEL (détecté V13)
Intent primaire: **{intent_name}** (confidence {intent_data.get('confidence', 0)})
Vocabulaire autorisé: {vocab.get('use_words', [])}
Vocabulaire INTERDIT: {vocab.get('avoid_words', [])}
Tone attendu: {vocab.get('cta_tone', '—')}
Proofs prioritaires: {vocab.get('proof_priority', [])}

Chaîne du funnel (statuts détectés):
{json.dumps(funnel, ensure_ascii=False, indent=2)[:600]}

{usp_lock_block}

{what_works_block}

{killer_block}

{thresholds_block}

{ice_block}

{funnel_block}

## CRITÈRE À TRAITER
criterion_id: {crit_id}
pillar: {pillar}
label: {crit_label}
scoring rules (extrait): {crit_scoring[:400]}

## ANTI-PATTERNS DÉTECTÉS sur cette page (playbook)
{anti_pat_block}

## CLUSTER PERCEPTUEL CONCERNÉ (état RÉEL de la page)
{cluster_block}

## HERO CAPTURE CONTEXT
H1 page: "{capture_context.get('h1', '')}"
Subtitle: "{capture_context.get('subtitle', '')}"
Primary CTA: "{capture_context.get('primary_cta_text', '')}" → {capture_context.get('primary_cta_href', '')}

## VISION SIGNALS (ground truth visuelle — Claude Vision 4.5 sur le screenshot)
⚠️ CES SIGNAUX SONT LA VÉRITÉ VISUELLE. Ils priment sur les signaux cluster/DOM qui peuvent être bugués
(ex: "No items found. Trustpilot Trustpilot Trustpilot" = texte DOM poubelle, tu dois te fier à Vision).
Si Vision dit qu'un élément est présent, il EST visible à l'écran. Si Vision l'a pas vu, il n'est pas visible.
{build_vision_block(capture_context)}

## GOLDEN BENCHMARK (sites best-in-class de référence)
{golden_block}

{differential_block}

---

CONSIGNES GOLDEN :
- Si le signal d'annihilation (⚠️) est actif, tu DOIS rétrograder cette reco en P3 ou l'annuler si l'écart client/golden est < 0.5 point. Justifie dans "why".
- Si un signal fort (🎯) est actif, inspire-toi des patterns golden pour le "after". Cite le golden site qui fait le mieux.
- Le "after" doit être MEILLEUR que ce que font les golden, pas une copie.

{style_templates_block(style_templates or [])}
{v12_reference_block(v12_reco_text)}

Produis ta reco sur-mesure V13. JSON strict uniquement."""
