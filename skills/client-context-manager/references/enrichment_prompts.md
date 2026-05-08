# Enrichment Prompts — Questions par secteur et business model

## Principes d'enrichissement

### Règle du "Never ask what you can infer"
Si l'URL est fournie, ne JAMAIS demander ce que l'IA peut déduire seule :
- ❌ "Quelle est votre couleur primaire ?" → ✅ Extraire depuis le site
- ❌ "Quel est votre secteur ?" → ✅ Détecter depuis le contenu
- ❌ "Quels sont vos concurrents ?" → ✅ Chercher et proposer

### Ordre des questions (quand on en a besoin)
1. Questions qui débloquent le plus de contexte en premier
2. Questions fermées avant questions ouvertes
3. Questions avec exemples/suggestions plutôt que champs vides
4. Max 5 questions par tour de conversation

---

## Questions universelles (tous secteurs)

### Tier 1 — Les indispensables (si pas déductibles)
1. "Quel est l'objectif #1 de ce projet ? (plus de leads / plus de ventes / lancement produit / refonte / autre)"
2. "Qui est votre client idéal en une phrase ?"
3. "Quelle est LA raison principale pour laquelle vos clients vous choisissent plutôt qu'un concurrent ?"

### Tier 2 — Enrichissement stratégique
4. "Quels sont les 3 arguments qui reviennent le plus dans vos avis clients ?"
5. "Quelle est l'objection #1 que vos prospects formulent avant d'acheter ?"
6. "Si vous deviez résumer votre différence en une phrase que même votre grand-mère comprendrait ?"

### Tier 3 — Contexte opérationnel
7. "D'où vient principalement votre trafic ? (Ads Meta / Google Ads / SEO / Email / Social / Autre)"
8. "Quel est votre budget ads mensuel approximatif ?"
9. "Y a-t-il des éléments de design / marque à respecter absolument ? (charte, fonts, couleurs imposées)"

---

## Questions par secteur

### E-commerce / D2C

**Questions prioritaires :**
- "Quel est votre produit best-seller et à quel prix ?"
- "Votre panier moyen ?"
- "Offrez-vous la livraison gratuite ? À partir de quel montant ?"
- "Quelle est votre politique de retour ?"
- "Avez-vous de la rareté naturelle (stock limité, éditions limitées) ?"

**Enrichissement IA automatique :**
- Analyser les pages produit pour détecter le pricing
- Extraire les avis clients visibles
- Identifier la stratégie de social proof utilisée
- Détecter les mécanismes d'urgence existants

### SaaS / B2B

**Questions prioritaires :**
- "Quel est votre modèle de pricing ? (freemium / trial / demo / sur devis)"
- "Cycle de vente typique : combien de temps entre le premier contact et la signature ?"
- "Les 3 features qui déclenchent le 'aha moment' chez vos utilisateurs ?"
- "Vos principaux intégrations/partenaires tech ?"
- "Qui est le decision-maker dans le processus d'achat ? (l'utilisateur final ou quelqu'un d'autre)"

**Enrichissement IA automatique :**
- Analyser la page pricing (tiers, features, CTA)
- Détecter le modèle d'acquisition (self-serve vs sales-led)
- Extraire les logos clients / case studies
- Identifier les intégrations listées

### Lead Gen / Services

**Questions prioritaires :**
- "Quel type de lead générez-vous ? (formulaire / appel / devis / RDV)"
- "Combien de champs dans votre formulaire actuel ?"
- "Avez-vous un lead magnet ou une offre d'appel ? (audit gratuit, consultation, guide...)"
- "Quel est le délai moyen de conversion lead → client ?"
- "Quel est la lifetime value d'un client ?"

**Enrichissement IA automatique :**
- Analyser le formulaire existant (nombre de champs, types)
- Détecter l'offre d'appel
- Évaluer la friction du processus de conversion
- Identifier les éléments de réassurance

### InsurTech / FinTech

**Questions prioritaires :**
- "Quels produits d'assurance/finance proposez-vous ?"
- "Combien d'étapes dans le processus de souscription ?"
- "Quels agréments/certifications devez-vous afficher ?"
- "La souscription est-elle 100% en ligne ou il y a une étape humaine ?"
- "Quel est le taux de complétion de votre funnel de souscription ?"

**Enrichissement IA automatique :**
- Détecter les mentions légales et agréments
- Analyser le funnel de souscription
- Extraire les éléments de réassurance (garanties, certifications)
- Identifier les partenaires (assureurs, banques)

### Health / Wellness / Beauty

**Questions prioritaires :**
- "Vos produits ont-ils des certifications ou labels ? (bio, vegan, cruelty-free...)"
- "Y a-t-il des ingrédients ou un processus distinctif à mettre en avant ?"
- "Des preuves cliniques ou études à mentionner ?"
- "Des contre-indications ou disclaimers obligatoires ?"
- "Quel est le rituel/routine d'utilisation ?"

**Enrichissement IA automatique :**
- Détecter les certifications/labels affichés
- Analyser les listes d'ingrédients
- Identifier le storytelling marque (origine, fondateur, mission)
- Extraire les témoignages/avant-après

---

## Questions par type de projet

### Projet "Nouvelle Landing Page Paid"
1. "Pour quelle plateforme publicitaire ? (Meta / Google / TikTok / LinkedIn)"
2. "Quelle est l'accroche de votre ad ? (pour assurer la cohérence message)"
3. "Objectif de la LP : formulaire / achat / inscription / téléchargement ?"
4. "Budget prévu pour cette campagne ?"
5. "Y a-t-il une urgence ou une offre limitée dans le temps ?"

### Projet "Refonte de page existante"
1. "URL de la page actuelle ?"
2. "Qu'est-ce qui ne fonctionne pas selon vous ?"
3. "Le taux de conversion actuel de cette page ?"
4. "Avez-vous déjà testé des variantes ?"
5. "Y a-t-il des éléments à garder absolument ?"

### Projet "Audit CRO"
1. "URL(s) à auditer ?"
2. "Objectif principal de la/les page(s) ?"
3. "Source de trafic principale ?"
4. "Données de performance disponibles ?"
5. "Budget/deadline pour implémenter les recos ?"

---

## Exemples de propositions d'enrichissement

Quand l'IA enrichit automatiquement, elle PROPOSE toujours :

**Format de proposition :**
```
🔍 Enrichissement automatique basé sur l'analyse de [URL]

Voici ce que j'ai détecté — corrige ou complète si besoin :

• Secteur détecté : InsurTech (assurance habitation)
• Proposition de valeur : "Assurance habitation 100% digitale, remboursement en 2h"
• Ton : Moderne, accessible, rassurant (pas corporate)
• Palette : #1B4D89 (bleu principal) + #FF6B35 (accent orange)
• Concurrents probables : Lemonade, Lovys, Alan
• Audience probable : 25-40 ans, propriétaires urbains, digital-native
• Awareness level : Solution-aware (ils comparent les options)

✅ Ça te semble juste ? Corrige ce qui ne colle pas.
```
