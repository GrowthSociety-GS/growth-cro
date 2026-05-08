# Moteur de Recommandations CRO - Reco Engine

**Version:** 1.0
**Dernière mise à jour:** 2026-04-04
**Objectif:** Transformer les diagnostics audit en recommandations CRO actionnables, priorisées et structurées.

---

## 1. LOGIQUE DE PRIORISATION DES RECOMMANDATIONS

### 1.1 Matrice Impact × Effort

Chaque recommandation est scorée selon deux axes : **Impact** (1-5) et **Effort** (1-5). La combinaison détermine la priorité.

#### Impact (1-5) — Potentiel de gain de conversion

**Impact 5 - Critique (affecte directement CVR)**
- Position : ATF, headline, hero visuel, CTA principal, formulaire
- Corrélation conversion : forte (data-backed ou pattern reconnu)
- Exemple : Réécrire headline, repositionner CTA above-the-fold, simplifier formulaire

**Impact 4 - Haut (affecte engagement et rétention)**
- Position : sections benefits, social proof, testimonials, structure generale
- Corrélation conversion : indirecte mais mesurable (améliore scroll depth, engagement, trust)
- Exemple : Ajouter testimonials vidéos, restructurer hiérarchie, ajouter garantie

**Impact 3 - Moyen (affecte perception/confiance)**
- Position : body sections, copy secondary, design refinements
- Corrélation conversion : légère (améliore perception de qualité/crédibilité)
- Exemple : Améliorer qualité image produit, affiner typography, ajouter micro-copy rassurance

**Impact 2 - Bas (affecte expérience)**
- Position : footer, navigation secondaire, sections informationnelles
- Corrélation conversion : très indirecte (UX/accessibilité)
- Exemple : Footer optimization, menu reorganization, internal link refinement

**Impact 1 - Minimal (cosmétique ou technique mineur)**
- Position : anywhere
- Corrélation conversion : nulle
- Exemple : Spelling fix, color refinement, icon update

#### Effort (1-5) — Ressources nécessaires pour implémenter

**Effort 1 - Trivial (< 30 min)**
- Discipline : Copy only
- Qui : Marketer solo
- Exemple : Changer headline, ajouter micro-copy, éditer sous-titre

**Effort 2 - Léger (< 2h)**
- Discipline : Design tweak + minor HTML/CSS
- Qui : Designer ou dev junior
- Exemple : Bouton CTA color change, image swap, spacing adjustment

**Effort 3 - Modéré (1 journée)**
- Discipline : Section restructure
- Qui : Designer + Dev junior
- Exemple : Réarranger hero, ajouter/retirer section, intégrer formulaire différent

**Effort 4 - Substantiel (2-3 jours)**
- Discipline : Page restructure
- Qui : Designer + Dev + Copy
- Exemple : Refonte page layout, intégration nouvel outil (chat, vidéo auto-play), tunnel multi-step

**Effort 5 - Majeur (1+ semaine)**
- Discipline : Full page rebuild
- Qui : Full team (Design, Dev, Product, Copy)
- Exemple : Migration de plateforme, redesign complet, intégration CRM/API

#### Score de Priorité (P1, P2, P3)

**Formule:** `Score = Impact × (6 - Effort)`

| Impact | Effort 1 | Effort 2 | Effort 3 | Effort 4 | Effort 5 |
|--------|----------|----------|----------|----------|----------|
| **5**  | 25       | 20       | 15       | 10       | 5        |
| **4**  | 20       | 16       | 12       | 8        | 4        |
| **3**  | 15       | 12       | 9        | 6        | 3        |
| **2**  | 10       | 8        | 6        | 4        | 2        |
| **1**  | 5        | 4        | 3        | 2        | 1        |

**Seuils de Priorité:**
- **P1 (Quick Wins + High Impact)** : Score ≥ 15
- **P2 (Incremental Improvements)** : Score 8-14
- **P3 (Nice-to-have)** : Score ≤ 7

### 1.2 Ordre de Présentation des Recos

Présenter au client dans cet ordre pour maximiser impact perçu et probabilité d'exécution :

1. **Quick Wins (P1, Effort ≤ 2)** — Faire immédiatement (< 2h)
   - Changements de copy simples
   - Swap visuels
   - Modifications CTA/placement

2. **High-Impact Projects (P1, Effort > 2)** — Planifier sprint suivant
   - Restructures majeures
   - Ajout de sections de social proof
   - Refonte hero/CTA

3. **Incremental Improvements (P2)** — Backlog court terme
   - Optimisations secondaires
   - Tests A/B candidates
   - Améliorations UX/copy

4. **Nice-to-have (P3)** — Considérer long terme
   - Polish cosmétiques
   - Optimisations micro

### 1.3 Mapping Critère Audit → Type de Reco

Chaque critère de la grille d'audit (36 critères × 6 catégories) mappe directement à un type de recommandation :

#### Catégorie 1 : Cohérence Stratégique (Critères 1.1-1.6)
- **1.1 Scent trail** → Reco type : "Alignement Ad → Page"
- **1.2 Objectif clair** → Reco type : "Clarifier l'objectif primaire"
- **1.3 Proposition de valeur** → Reco type : "Affiner proposition de valeur"
- **1.4 Audience identifiable** → Reco type : "Affiner ciblage et persona"
- **1.5 Bénéfices vs Features** → Reco type : "Recentrer sur bénéfices"
- **1.6 Cohérence message** → Reco type : "Structurer narration logique"

#### Catégorie 2 : Hero / Above The Fold (Critères 2.1-2.5)
- **2.1 Promesse claire** → Reco type : "Réécrire headline/promesse"
- **2.2 CTA visible ATF** → Reco type : "Repositionner CTA"
- **2.3 Urgence/pertinence** → Reco type : "Ajouter urgence/relevance"
- **2.4 Hero visuel** → Reco type : "Optimiser visuel hero"
- **2.5 Micro-réassurance ATF** → Reco type : "Ajouter micro-copy rassurance"

#### Catégorie 3 : Persuasion & Copy (Critères 3.1-3.7)
- **3.1 Bénéfices clairs** → Reco type : "Réécrire sections bénéfices"
- **3.2 Social proof forte** → Reco type : "Ajouter/améliorer social proof"
- **3.3 Scarcité/urgence** → Reco type : "Intégrer scarcité/urgence"
- **3.4 Guarantees/reassurance** → Reco type : "Ajouter garanties"
- **3.5 Objections handling** → Reco type : "Ajouter FAQ/objection handling"
- **3.6 Call-to-action copy** → Reco type : "Optimiser CTA wording"
- **3.7 Copy tone/voice** → Reco type : "Aligner tone et voice"

#### Catégorie 4 : Structure & UX (Critères 4.1-4.7)
- **4.1 Hiérarchie visuelle** → Reco type : "Restructurer hiérarchie"
- **4.2 Whitespace** → Reco type : "Améliorer whitespace"
- **4.3 Scannabilité** → Reco type : "Optimiser scannabilité"
- **4.4 Mobile-first UX** → Reco type : "Optimiser mobile UX"
- **4.5 Formulaires** → Reco type : "Simplifier formulaire"
- **4.6 Flow et progression** → Reco type : "Améliorer flow page"
- **4.7 Liens de sortie** → Reco type : "Réduire distractions"

#### Catégorie 5 : Qualité Technique (Critères 5.1-5.5)
- **5.1 Performance page** → Reco type : "Optimiser performance"
- **5.2 Cross-browser** → Reco type : "Tester/fixer bugs cross-browser"
- **5.3 Mobile responsivity** → Reco type : "Corriger responsive design"
- **5.4 Formulaires fonctionnels** → Reco type : "Déboguer formulaires"
- **5.5 Analytics/tracking** → Reco type : "Implémenter tracking"

#### Catégorie 6 : Psychologie de Conversion (Critères 6.1-6.6)
- **6.1 Cognitive ease** → Reco type : "Simplifier compréhension"
- **6.2 Social proof anchoring** → Reco type : "Ancrer avec social proof"
- **6.3 Anchoring/prix** → Reco type : "Utiliser anchoring effet"
- **6.4 Loss aversion** → Reco type : "Framer losses"
- **6.5 FOMO/urgence** → Reco type : "Activer FOMO"
- **6.6 Trust markers** → Reco type : "Ajouter trust markers"

---

## 2. TEMPLATES DE RECOMMANDATIONS PAR CATÉGORIE

### 2.1 Templates Cohérence Stratégique (Critères 1.1-1.6)

#### Critère 1.1 - Scent Trail Ad → Page

**RECO TYPE:** Alignement Ad → Page
**IMPACT:** 5 | **EFFORT:** 1-2 | **SCORE P1:** 20-25

**PROBLÈME TYPE:**
Le message/visuel/offre de la page ne correspond pas à l'annonce source. Rupture d'expectation → bounce rate +20-40%.

**SOLUTIONS (du plus simple au plus complexe):**

1. **[Effort 1]** Modifier le headline pour reprendre le wording exact de l'ad
   - Chercher le headline ad source
   - Le copier mot-pour-mot en H1 page
   - Tester en 5 sec : reconnaître scent?

2. **[Effort 1]** Ajouter un "hero tagline" qui reprend la promesse ad
   - Sous-headline : "Comme promis dans l'annonce : [offre exacte]"
   - Renforce scent trail psychologiquement

3. **[Effort 2]** Aligner les couleurs hero avec l'ad
   - Extraire couleur primaire de l'ad
   - L'utiliser en hero background ou accents
   - Ajouter même offre/urgence en header

4. **[Effort 2-3]** Créer variantes de page par ad group
   - Si 3 ads différentes → 3 pages différentes
   - Headline = ad headline
   - Visuel = ad visuel style
   - Offre = ad offer

**COPY SUGGESTIONS:**

- Reprendre mot pour mot le hook de l'ad dans le headline
- Ajouter sous-titre: "Vous êtes ici parce que [promesse ad]. Voilà comment ça marche."
- Ajouter micro-copy: "Sans engagement, comme vous l'avez vu dans l'annonce"

**EXEMPLES CONCRETS:**

Ad: "Doublez votre productivité en 30 jours (gratuit)"
Page décente: "Augmentez votre productivité"
Page optimisée: "Doublez votre productivité en 30 jours - Commencez gratuitement"

**PSYCHOLOGIE:** Consistency (Cialdini), Cognitive Ease (réduction dissonance cognitive)

---

#### Critère 1.2 - Objectif de Conversion Clair et Unique

**RECO TYPE:** Clarifier l'objectif primaire
**IMPACT:** 5 | **EFFORT:** 1-3 | **SCORE P1:** 15-25

**PROBLÈME TYPE:**
Plusieurs objectifs en compétition (Acheter + Newsletter + Chat + Démo request). Visiteur hésite → abandonne.

**SOLUTIONS:**

1. **[Effort 1]** Masquer/réduire les CTA secondaires
   - Garder VISIBLE : CTA principal unique
   - CACHÉ/TAILLE RÉDUITE : CTAs secondaires (chat, newsletter)
   - Ratio d'attention: 1 principal : 0.2 secondaires

2. **[Effort 1]** Réécrire les CTA pour clarifier la hiérarchie
   - CTA principal: "Acheter maintenant" (gros bouton, couleur primaire)
   - CTA secondaire: "Voir la démo" (petit lien, gris)

3. **[Effort 2]** Masquer le footer (ou le rendre minimal)
   - Footer = grosse source de distractions
   - Alternative: footer ultra-simple (contact + legal)

4. **[Effort 2-3]** Créer 2-3 variantes de page par segment
   - Page 1 (Acheteurs) : CTA = "Acheter"
   - Page 2 (Leads froids) : CTA = "Voir la démo"
   - Page 3 (Newsletter) : CTA = "Recevoir la newsletter"

**COPY SUGGESTIONS:**

CTA Principal:
- "Acheter maintenant" → "Commencer ma croissance aujourd'hui"
- "S'inscrire" → "Créer mon compte gratuit"
- Éviter: "Envoyer", "Soumettre", "Continuer" (neutres)

**PSYCHOLOGIE:** Choice Overload (paradox Jam), Goal Priming

---

#### Critère 1.3 - Proposition de Valeur Explicite (5 sec)

**RECO TYPE:** Affiner proposition de valeur
**IMPACT:** 5 | **EFFORT:** 1 | **SCORE P1:** 25

**PROBLÈME TYPE:**
Visiteur ne comprend pas "quoi, pour qui, pourquoi maintenant" après 5 secondes. Bounce rate élevé.

**SOLUTIONS:**

1. **[Effort 1]** Réécrire headline avec structure : [Bénéfice] + [Pour qui] + [Pourquoi]
   - Mauvais: "Solution innovante"
   - Bon: "Gagnez 5 heures/semaine — Sans apprendre à coder"
   - Test: "So what?" appliqué 3x → chaque réponse = partie headline

2. **[Effort 1]** Ajouter sous-titre qui répond au "comment"
   - Headline = "Quoi" + "Pourquoi"
   - Sous-titre = "Pour qui" + "Comment"
   - Exemple :
     - H1: "Gagnez 5h/semaine sur les réunions"
     - H2: "Avec notre IA de scheduling — Aucune formation requise"

3. **[Effort 1]** Tester proposition avec "elevator pitch" (30 sec)
   - Proposer à 3 personnes
   - Elles comprennent-elles la valeur en 5 sec?
   - Sinon: revenir au drawing board

**COPY SUGGESTIONS:**

Structure gagante pour headlines:
- "[Résultat chiffré] en [temps] sans [obstacle]"
  - "Doublez votre revenu en 90 jours sans créer un produit"

- "Oublie [pain point]. Voici [solution]"
  - "Oublie les réunions qui n'avancent rien. Voici le meeting planner IA"

- "[Action] pour [audience] → [résultat]"
  - "Lancez votre e-shop pour les créateurs → 10k€ le mois 1"

**PSYCHOLOGIE:** Clarity, Cognitive Load Reduction

---

#### Critère 1.4 - Audience Cible Identifiable

**RECO TYPE:** Affiner ciblage et persona
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Page parle au "tout le monde" → personne ne se reconnaît → bounce.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter "persona anchor" dès le hero
   - "Vous êtes manager en startup"
   - "Si vous lancez une marque D2C"
   - "Freelances : vous fatigués de chasser les clients?"

2. **[Effort 1]** Réécrire sections clés avec "vous" spécifique
   - Identifier le pain point spécifique du persona
   - Parler directement à lui
   - Exemple: "Comme vous, 82% des founders perdent 15h/semaine en admin"

3. **[Effort 1]** Ajouter micro-copy de reconnaissance
   - Sous CTA: "Pour solopreneurs qui veulent scaler"
   - En hero: "Si tu gères seul, tu reconnaitras ce problème..."

4. **[Effort 2]** Créer landing pages segmentées
   - Page 1: "Pour les Agences"
   - Page 2: "Pour les Freelances"
   - Chaque page adapte headline, examples, pricing

**COPY SUGGESTIONS:**

Persona Anchors puissants:
- "Freelances qui facturent en dessous de votre valeur"
- "Founders qui ont fermé leur série A"
- "Marketeers qui se demandent si le CRO ça existe vraiment"

**PSYCHOLOGIE:** In-group/Out-group bias, Social Identity Theory

---

#### Critère 1.5 - Bénéfices vs Features (Ratio ≥ 2:1)

**RECO TYPE:** Recentrer sur bénéfices
**IMPACT:** 4 | **EFFORT:** 1 | **SCORE P1:** 20

**PROBLÈME TYPE:**
Page liste les features (API, modèles, stockage) sans traduire en bénéfices client → peu compréhensible.

**SOLUTIONS:**

1. **[Effort 1]** Appliquer le test "Donc pour toi ça veut dire que..."
   - Feature: "API intégrée Slack"
   - Test: "Donc pour toi ça veut dire que... tu reçois notifications direct?"
   - Bénéfice: "Reçois tes notifications où tu travailles déjà"

2. **[Effort 1]** Réécrire chaque bullet point
   - De: "250 modèles templates"
   - Vers: "Lance ta page en 5 min (sans coding, sans design)"

3. **[Effort 1]** Ajouter "impact stémérique"
   - Feature: "Stockage illimité"
   - Bénéfice: "Stocker tous tes fichiers — jamais de perte, jamais de coût additionnel"

4. **[Effort 2]** Réstructurer section avantages
   - Colonne 1 (35%): Icon + Bénéfice (gros texte)
   - Colonne 2 (65%): Feature (petit texte)
   - L'oeil voit le bénéfice d'abord

**STRUCTURE COPY GAGANTE:**

```
[ICON] Gagnez 5 heures/semaine
Avec notre IA qui automatise vos rapports (API + Dashboard auto-refresh)
```

**PSYCHOLOGIE:** Benefits Vs Features, Outcome Focus

---

#### Critère 1.6 - Cohérence Globale du Message

**RECO TYPE:** Structurer narration logique
**IMPACT:** 4 | **EFFORT:** 2-3 | **SCORE P1:** 8-16

**PROBLÈME TYPE:**
Sections indépendantes, pas de fil conducteur → visiteur perd compréhension → abandonne.

**SOLUTIONS:**

1. **[Effort 1]** Appliquer le "titres seuls" test
   - Enlever tout le body text
   - Lire juste les H2 de haut en bas
   - Ça raconte une histoire cohérente?
   - Si non : reorder sections ou réécrire titres

2. **[Effort 1]** Vérifier zéro contradiction
   - Relire toutes les sections
   - Y a-t-il une contradiction? (ex: "rapide" vs "complet, prend du temps")
   - Corriger immédiatement

3. **[Effort 2]** Réarranger sections pour "Problem → Solution → Proof → CTA"
   - Section 1: Identifie le pain point
   - Section 2: Présente la solution
   - Section 3: Fournit la preuve (testimonial, case study)
   - Section 4: CTA conversion

4. **[Effort 2-3]** Ajouter transitions explicites
   - Entre chaque section, ajouter 1-2 phrases de transition
   - "Maintenant que tu sais le problème, voici la solution..."
   - "Les faits le prouvent. Regarde ces résultats:"

**COPY SUGGESTIONS:**

Formule narrative gagnante:
```
Hero: "Voici votre problème" [Identifier pain point]
↓
Section 1: "Vous n'êtes pas seul(e)" [Normaliser]
↓
Section 2: "Voici comment on le résout" [Présenter solution]
↓
Section 3: "Regardez les résultats" [Fournir preuve]
↓
Section 4: "Passez à l'action aujourd'hui" [CTA]
```

**PSYCHOLOGIE:** Narrative Arc, Story Structure (Hero's Journey)

---

### 2.2 Templates Hero / Above The Fold (Critères 2.1-2.5)

#### Critère 2.1 - Promesse Claire Visible Immédiatement

**RECO TYPE:** Réécrire headline/promesse
**IMPACT:** 5 | **EFFORT:** 1 | **SCORE P1:** 25

**PROBLÈME TYPE:**
Headline vague ("Bienvenue", "Solution innovante") → visiteur ne sait pas pourquoi rester → bounce.

**SOLUTIONS:**

1. **[Effort 1]** Appliquer structure headline de promesse
   - Structure: "[Résultat] en [temps] sans [effort]"
   - Mauvais: "Logiciel de gestion"
   - Bon: "Gagnez 5h/semaine — Automatisez votre admin"

2. **[Effort 1]** Utiliser le "3 questions test"
   - Quoi? (Produit/service)
   - Pour qui? (Audience)
   - Pourquoi maintenant? (Urgence/pertinence)
   - Headline doit répondre aux 3 → sinon rewrite

3. **[Effort 1]** Tester lisibilité (5 sec + distance)
   - Montrer le hero 5 secondes seulement
   - Demander: "Quelle est la promesse?"
   - Si réponse floue → rewrite

4. **[Effort 1]** Rendre headline unique
   - Comparer avec 5 concurrents
   - Si headline = générique pour l'industrie → trop vague
   - Ajouter spécificité (chiffres, délais, personas)

**BIBLIOTHÈQUE FORMULES HEADLINES (10+ options):**

1. **Promesse de Résultat**
   - "Obtenez [résultat] en [temps] sans [obstacle]"
   - Exemple: "Gagnez 5h/semaine sans apprendre à coder"

2. **Curiosité / Intérêt**
   - "Le secret que [audience] utilisent pour [résultat]"
   - Exemple: "Le secret que 2,847 e-commerçants utilisent pour doubler leur taux de conversion"

3. **Social Proof / Validation**
   - "[Nombre] [audience] ont déjà [résultat]. Et toi?"
   - Exemple: "14,000 freelances gagnent maintenant 6-7 figures — Tu pourrais être le suivant"

4. **Question Rhétorique**
   - "Et si [pain point] n'était plus un problème?"
   - Exemple: "Et si les réunions vous prenaient 0 heure par semaine?"

5. **Contre-intuition / Révélation**
   - "Pourquoi [croyance commune] est faux (et comment [résultat])"
   - Exemple: "Pourquoi le CRO traditionnel échoue (et comment notre approche génère +45% de conversions)"

6. **Urgence / Limitation**
   - "[Offre] disponible jusqu'au [date] — [bénéfice]"
   - Exemple: "Formation au prix de lancement - 50% jusqu'au 15 mai - Valeur réelle 1,997€"

7. **Comparaison**
   - "[Approche A] vs [Approche B] : [différence]"
   - Exemple: "E-mail marketing vs SMS marketing : [Lequel génère 5x plus de conversions?]"

8. **Transformation**
   - "De [état A] à [état B] en [temps]"
   - Exemple: "De galère à 100k€/mois en 6 mois avec cette stratégie"

9. **Spécificité / Détail**
   - "[Chiffre exact] [audience] ont augmenté [métrique] de [%] en [temps]"
   - Exemple: "873 managers ont augmenté leur productivité de 37% en 30 jours"

10. **Negative / Avoidance**
    - "[Nombre] erreurs qui tuent votre [métrique] (et comment les corriger)"
    - Exemple: "7 erreurs qui tuent votre taux de conversion (et comment les corriger en 48h)"

**COPY SUGGESTIONS:**

- Max 12 mots (benchmark haute conversion)
- Bénéfice first, spécificité second
- Éviter: Jargon, buzzwords (innovant, solution, leader)
- Tester: 3 variantes de headlines, garder la meilleure

**PSYCHOLOGIE:** Clarity, Curiosity, Result Orientation

---

#### Critère 2.2 - CTA Visible Above The Fold

**RECO TYPE:** Repositionner CTA
**IMPACT:** 5 | **EFFORT:** 1-3 | **SCORE P1:** 15-25

**PROBLÈME TYPE:**
CTA principal invisible sans scroll (mobile: visible à 25% du viewport seulement).

**SOLUTIONS:**

1. **[Effort 1]** Ajouter CTA "sticky" en haut page (mobile)
   - Header sticky avec CTA fixe
   - Visible même après scroll
   - Améliore conversion mobile de 12-25%

2. **[Effort 1]** Ajouter CTA sticky en bas (mobile)
   - Barre de bas de page avec CTA
   - Accessible au pouce (thumb zone)
   - À la place ou en complément du header

3. **[Effort 2]** Repositionner hero pour faire de la place au CTA
   - Si hero hero trop haut : le descendre légèrement
   - Assurer CTA visible à 90% sur mobile 375px
   - Tester sur vrais devices

4. **[Effort 2]** Augmenter taille du CTA button
   - Min: 44×44px (iOS), idéal: 48×56px
   - Faire le bouton "prioritaire visuellement"
   - Couleur contrastante (pas de couleur "safe")

5. **[Effort 3]** Restructurer hero si needed
   - Si ATF trop serré : enlever section secondaire
   - Focus sur headline + image + CTA uniquement
   - Replacer info secondaire plus bas

**CHECKLIST ATOF VISIBILITY:**

- [ ] Visible sans scroll sur 375px viewport (mobile)
- [ ] Visible sans scroll sur 768px viewport (tablet)
- [ ] Visible sans scroll sur 1440px viewport (desktop)
- [ ] Entièrement visible (pas coupé par footer ou autres)
- [ ] Taille min 44×44px
- [ ] Couleur contrastante (≥ 4.5:1 ratio)
- [ ] Alt: CTA sticky si ATF vraiment trop serré

**PSYCHOLOGIE:** Prominence, Accessibility (Thumb Zone)

---

#### Critère 2.3 - Urgence/Pertinence Immédiate

**RECO TYPE:** Ajouter urgence/relevance
**IMPACT:** 4 | **EFFORT:** 1 | **SCORE P1:** 20

**PROBLÈME TYPE:**
Pas de "raison d'agir maintenant" → visiteur bookmarke et part → jamais revient.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter "urgence structurelle"
   - Limitation quantitative: "50 places disponibles"
   - Deadline claire: "Offer valide jusqu'au 15 mai"
   - Scarcité sociale: "1,247 personnes se sont inscrites ce mois"

2. **[Effort 1]** Ajouter micro-copy urgence sous CTA
   - "Lancer maintenant — Essai gratuit, sans engagement"
   - "Commencer aujourd'hui — Accès instant"
   - "Rejoins-nous — Les places se remplissent vite"

3. **[Effort 1]** Ajouter countdown timer (si applicable)
   - Flash sale? Ajouter timer visible
   - Crée urgence psychologique (FOMO)
   - Améliore conversion de 7-15%

4. **[Effort 1]** Ajouter "relevance statement"
   - "Spécial pour les [persona] qui [problème]"
   - "Parfait pour toi si tu [condition]"
   - Crée sentiment d'être ciblé

**COPY SUGGESTIONS:**

Phrases urgence :
- "Les 100 premières personnes obtiennent [bonus]"
- "Cette offre se termine le [date] — Sécurise ta place maintenant"
- "Rejoins les [nombre] [audience] qui ont déjà [résultat]"

Micro-copy relevance:
- "Conçu spécialement pour les [persona]"
- "Si tu [pain point], tu reconnaitras ce problème..."

**PSYCHOLOGIE:** FOMO, Scarcity, Loss Aversion

---

#### Critère 2.4 - Hero Visuel Optimisé

**RECO TYPE:** Optimiser visuel hero
**IMPACT:** 4 | **EFFORT:** 1-3 | **SCORE P1:** 8-20

**PROBLÈME TYPE:**
Visuel hero générique ou mal aligné avec le message → pas complémentaire → confusion.

**SOLUTIONS:**

1. **[Effort 1]** Changer l'image hero (si source disponible)
   - Chercher image que mieux représente la promesse
   - Teste: audience reconnaît-elle la valeur en 5 sec?
   - Éviter: images génériques, bancales, non-pertinentes

2. **[Effort 1]** Ajouter overlay text sur image
   - Si image trop "busy", ajouter overlay semi-transparent
   - Assure lisibilité du texte par-dessus
   - Maintient impact visuel

3. **[Effort 2]** Remplacer image statique par démo/video
   - Si produit SaaS: afficher screenshot du produit (pas image vague)
   - Si service: vidéo court (10-15s) montrant résultat
   - Vidéo auto-play (sans son) améliore engagement +30%

4. **[Effort 2]** Utiliser "hero image grid" au lieu d'une grosse image
   - 4-6 petites images montrant différents angles
   - Chaque image = un bénéfice
   - Plus visuel, plus informatif

5. **[Effort 3]** Créer custom illustration/visuel
   - Si image de stock inefficace
   - Commission illustration custom alignée avec brand
   - Unique → Meilleure conversion

**CHECKLIST HERO VISUAL:**

- [ ] Image/vidéo répond à la promesse headline
- [ ] Pas de coupure d'image sur mobile (responsive)
- [ ] Texte lisible par-dessus (contraste ≥ 4.5:1)
- [ ] Image optimisée pour web (< 300KB)
- [ ] Aucun branding concurrent visible
- [ ] Représente audience target (non-generic)

**PSYCHOLOGIE:** Visual Relevance, Coherence Bias

---

#### Critère 2.5 - Micro-Réassurance ATF

**RECO TYPE:** Ajouter micro-copy rassurance
**IMPACT:** 4 | **EFFORT:** 1 | **SCORE P1:** 20

**PROBLÈME TYPE:**
Visiteur hésite avant premier CTA → micro-copy rassurance supprime frictions.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter micro-copy sous CTA principal
   - "Sans engagement"
   - "Essai gratuit, aucune CB requise"
   - "Accès instant"
   - "Résultats en 48h"
   - Supprime les objections implicites

2. **[Effort 1]** Ajouter garantie visible
   - "Garantie 30j remboursé" (si applicable)
   - "Si pas satisfait, on te rembourse"
   - Réduit perception de risque

3. **[Effort 1]** Ajouter trust marker simple
   - Logo badge ("Certifié", "Sécurisé par Stripe", etc.)
   - Stat social proof: "15,000+ clients satisfaits"
   - Avis rapidement: "★★★★★ 4.9/5 (2,847 avis)"

4. **[Effort 1]** Ajouter directive de réassurance
   - "Joue plus de vidéo de démo → [lien]"
   - "Pas prêt? Lire notre guide → [lien]"
   - Donne option de retraite (améliore conversion)

5. **[Effort 2]** Ajouter formulaire mini (si lead gen)
   - Au lieu de gros formulaire, commencer par "Email seulement"
   - "Puis on continuera avec les infos restantes"
   - Progessive disclosure réduit friction

**MICRO-COPY RASSURANCE TEMPLATES:**

- "[Nombre] clients satisfaits"
- "Garantie [délai] ou remboursé"
- "Aucune donnée partagée avec des tiers"
- "Accès aux [X] bonus exclusifs"
- "Pas d'engagement, cancel quand tu veux"
- "Résultats visibles en [time] ou nous le savons"

**PSYCHOLOGIE:** Risk Reduction, Trust Signaling

---

### 2.3 Templates Persuasion & Copy (Critères 3.1-3.7)

#### Critère 3.1 - Bénéfices Clairs dans Sections

**RECO TYPE:** Réécrire sections bénéfices
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Sections avantages listent features en vrac → visiteur ne comprend pas "pourquoi j'en ai besoin".

**SOLUTIONS:**

1. **[Effort 1]** Réécrire chaque "avantage" avec structure: Bénéfice + Feature
   - Mauvais: "API intégrée Slack"
   - Bon: "Reçois notifications instantanées là où tu travailles (API Slack native)"

2. **[Effort 1]** Appliquer le test "Donc pour toi ça veut dire..."
   - Feature: "250 modèles"
   - Test: "Donc pour toi ça veut dire que... quoi?"
   - Réponse: "Je peux créer une page en 5 min"
   - Bénéfice: "Créez une page en 5 min, sans design"

3. **[Effort 2]** Réstructurer layout : Bénéfice GRAND, Feature petit
   - Colonne 1: Icon + Bénéfice (gros texte, 32px+)
   - Colonne 2: Feature expliquant le "comment" (petit, 14px)
   - L'œil capture bénéfice d'abord

4. **[Effort 2]** Ajouter outcome chiffré à chaque bénéfice
   - "Gagnez 5h/semaine"
   - "Réduisez vos coûts de 30%"
   - "Augmentez conversion de +25%"
   - Spécificité = crédibilité

**STRUCTURE COPY SECTIONS:**

```
[ICON] Gagnez 5 heures/semaine
À automatiser vos rapports (avec notre IA + intégration native à Google Sheets)

[ICON] Réduisez vos erreurs de 98%
Avec validation automatique (vérifiez 50 points de données en 3 sec, 0 erreur)

[ICON] Continuez comme avant
Aucune formation requise (plug & play, compatible avec votre stack)
```

**PSYCHOLOGIE:** Benefit Focus, Outcome Orientation

---

#### Critère 3.2 - Social Proof Forte

**RECO TYPE:** Ajouter/améliorer social proof
**IMPACT:** 5 | **EFFORT:** 2-4 | **SCORE P1:** 8-20

**PROBLÈME TYPE:**
Absence ou social proof faible (logos seulement) → pas de confiance → conversion basse.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter testimonials vérifiés simples
   - Citation + Nom + Titre + Photo
   - Idéal: Vidéo court (15-30s) du client
   - Alternative: Screenshot d'avis Google/Trustpilot vérifiés

2. **[Effort 2]** Créer "testimonial section" dédiée
   - 3-5 testimonials authentiques
   - Varié: différents types de clients
   - Chacun adresse une objection différente

3. **[Effort 2]** Ajouter case study chiffré
   - Client [nom] : A obtenu [résultat] en [temps] avec [approche]
   - Photo + chiffres = crédibilité
   - Exemple: "SaaS XYZ a augmenté ses MRR de 47% en 3 mois"

4. **[Effort 2-3]** Intégrer vidéo testimonial
   - 1-3 vidéos clients courts (30-60s)
   - Authentique (pas de script rigide)
   - Placement: haut de page ou fin
   - Améliore conversion de 15-30%

5. **[Effort 1]** Ajouter badge/chiffre de validation
   - "[X] clients satisfaits"
   - "[X]% de satisfaction"
   - "Évaluation [★★★★★] sur [Y] avis"
   - "Certifié par [Organisme]"

**HIÉRARCHIE DE PREUVES (efficacité décroissante):**

1. Vidéos testimoniales authentiques (client parle)
2. Avis vérifiés tiers (Google, Trustpilot, etc.)
3. Screenshots d'avis/messages clients
4. Case studies chiffrés (résultats concrets)
5. Logos clients/partenaires
6. Badges certification/trust
7. Chiffres: "X clients", "Y% satisfaction"

**COPY SUGGESTIONS TESTIMONIALS:**

Bons templates:
- "[Client] a obtenu [résultat] en [temps]. Voici comment."
- "Depuis utilisation de [produit], mon [métrique] a augmenté de [%]. [Client]"
- "[Client] dépensait [coût ancien], maintenant [coût nouveau]. Économie: [€]. Il dit..."

**PSYCHOLOGIE:** Social Proof, Authority, Likeness

---

#### Critère 3.3 - Scarcité/Urgence Intégrée

**RECO TYPE:** Intégrer scarcité/urgence
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Pas de "raison d'agir aujourd'hui" → visiteur procrastine → jamais revient.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter urgence de prix
   - "Prix de lancement : 99€ (Prix normal 297€) jusqu'au 30 avril"
   - Crée comportement de "saisir l'opportunité"
   - Améliore conversion de 7-15%

2. **[Effort 1]** Ajouter scarcité quantité
   - "50 places disponibles seulement"
   - "100 spots limités pour cette cohorte"
   - Psychological scarcity

3. **[Effort 1]** Ajouter scarcité temps
   - Countdown timer visible
   - "Offer valide jusqu'au 15 mai"
   - Auto-refresh si deadline approche

4. **[Effort 1]** Ajouter scarcité social (FOMO)
   - "1,847 personnes se sont inscrites cette semaine"
   - "[X]% de places remplies (Y/Z spots left)"
   - Ajoute momentum

5. **[Effort 2]** Structurer scarcité dans formulaire
   - Afficher: "Seulement [N] places restantes"
   - Meter visuel de remplissage
   - "À ce rythme, complet dans [X] jours"

**COPY SCARCITÉ TEMPLATES:**

- "Prix de lancement — $99 (valeur $297) — Offer expire 15 mai"
- "100 places seulement — [X] réservées, [Y] disponibles"
- "[X] personnes se sont inscrites cette semaine — Rejoins-toi?"
- "Si tu attends, tu paies 3x plus cher"

**PSYCHOLOGIE:** Scarcity Principle (Cialdini), Loss Aversion, FOMO

---

#### Critère 3.4 - Guarantees/Reassurance

**RECO TYPE:** Ajouter garanties
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Visiteur percoit risque → hésite à convertir → besoin de réassurance explicite.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter garantie de remboursement claire
   - "30 jours satisfait ou remboursé, 0 questions"
   - Visible près du CTA
   - Réduit perception de risque de 30-40%

2. **[Effort 1]** Ajouter "essai gratuit" micro-copy
   - "Essai gratuit 14 jours, aucune CB requise"
   - Permet au visiteur de "tester sans risque"
   - Augmente conversion de 15-25%

3. **[Effort 1]** Ajouter garantie de résultat
   - "Si tu n'as pas [résultat] en [temps], on te rembourse"
   - "Basé sur [X] cas de succès"
   - Basé sur data réelle

4. **[Effort 1]** Ajouter certification/trust badge
   - Logo SSL/sécurisé
   - "Données encryptées 256-bit"
   - "Traité par Stripe (leader paiements)"
   - "Certifié RGPD"

5. **[Effort 2]** Créer "satisfaction guarantee" section
   - Dédiée aux objections
   - "Voici pourquoi on peut te donner cette garantie..."
   - Explique confiance dans le produit

**GUARANTEE TEMPLATES:**

- "30 jours satisfait ou remboursé — Zéro questions posées"
- "Essai gratuit [X] jours — Aucune carte de crédit requise"
- "Si ton [résultat] n'a pas augmenté de [%], on te rembourse 100%"
- "Protégé par Stripe — Tes données sont sécurisées"
- "Rejoins [X]+ clients qui nous font confiance depuis [Y] ans"

**PSYCHOLOGIE:** Risk Reduction, Trust Signal, Loss Aversion

---

#### Critère 3.5 - Objection Handling (FAQ/Reassurance)

**RECO TYPE:** Ajouter FAQ/objection handling
**IMPACT:** 3 | **EFFORT:** 1-2 | **SCORE P1:** 12-16

**PROBLÈME TYPE:**
Visiteur a des questions en tête → pas de réponses visibles → quitte la page.

**SOLUTIONS:**

1. **[Effort 1]** Créer FAQ section (5-10 Q)
   - Identifier top objections (basé sur support tickets)
   - Répondre clairement et brièvement
   - Placer avant CTA final

2. **[Effort 1]** Ajouter "anticipatory reassurance"
   - Objection implicite: "Will this work for me?"
   - Réassurance: "Works for [types of customers]"
   - Placement: subheading sous headline

3. **[Effort 1]** Créer "objection killer" mini-copy
   - Sous CTA: "Still unsure? [Link to demo/case study]"
   - Objection: "Je ne suis pas sûr"
   - Réponse: "Regarde la démo (5 min)"

4. **[Effort 2]** Intégrer FAQ interactif
   - Accordion style (click to expand)
   - Organiser par catégorie (Pricing, Features, Support, etc.)
   - Améliore UX et réassurance

5. **[Effort 1]** Ajouter "common concerns" section
   - Afficher les top 3 objections
   - Répondre avec stat/cas concret
   - Exemple:
     - "Pas assez de support?" → "Support 24/7 en [langage]"
     - "Ça prendra trop de temps?" → "Setup 5 min, résultats jour 1"

**TOP OBJECTIONS À COUVRIR:**

- "Will this work for me / my company type?"
- "How long until I see results?"
- "What if I'm not satisfied?"
- "Is this secure / trustworthy?"
- "How much does it actually cost?"
- "Can I cancel anytime?"
- "Do I need technical skills?"

**PSYCHOLOGY:** Anticipated Regret, Uncertainty Reduction

---

#### Critère 3.6 - Call-to-Action Copy Optimisée

**RECO TYPE:** Optimiser CTA wording
**IMPACT:** 5 | **EFFORT:** 1 | **SCORE P1:** 25

**PROBLÈME TYPE:**
CTA wording générique ("Envoyer", "Soumettre") → peu motivant → lower conversion.

**SOLUTIONS:**

1. **[Effort 1]** Remplacer CTA neutre par CTA bénéfice
   - Mauvais: "Envoyer", "Soumettre", "Continuer", "Cliquer ici"
   - Bon: "Recevoir mon devis", "Commencer ma croissance", "Accéder au cours"

2. **[Effort 1]** Ajouter urgence/pertinence au CTA
   - "Commencer mon essai gratuit (14 jours)"
   - "Obtenir mon analyse gratuite"
   - "Réserver ma place maintenant"

3. **[Effort 1]** Utiliser micro-copy CTA
   - CTA bouton: "Télécharger le guide"
   - Micro-copy: "PDF gratuit, 5 min de lecture"

4. **[Effort 1]** Tester variantes CTA
   - A: "Acheter maintenant" vs B: "Acceder maintenant"
   - A: "S'inscrire" vs B: "Créer mon compte"
   - Tracker performance, garder le meilleur

5. **[Effort 1]** Personnaliser CTA par segment (si possible)
   - Segment A (leads): "Réserver une démo"
   - Segment B (ready): "Acheter maintenant"
   - Améliore relevance et conversion

**BIBLIOTHÈQUE TEMPLATES CTA:**

**Par objectif:**

*Vente:*
- "Acheter maintenant"
- "Obtenir mon accès immédiat"
- "Finaliser ma commande"

*Lead Gen:*
- "Réserver ma démo"
- "Recevoir mon devis"
- "Planifier un appel"

*Inscription:*
- "Créer mon compte gratuit"
- "S'inscrire gratuitement"
- "Commencer mon essai"

*Téléchargement:*
- "Télécharger mon guide"
- "Accéder au webinaire"
- "Recevoir la ressource"

*Consultation:*
- "Prendre un RDV"
- "Parler à un expert"
- "Obtenir une consultation"

**Micro-copy CTA (sous le bouton):**
- "Essai gratuit, sans engagement"
- "Accès instant, aucune CB"
- "Résultats en 48h"
- "Garantie 30j remboursé"

**PSYCHOLOGIE:** Outcome Focus, Urgency, Clarity

---

#### Critère 3.7 - Copy Tone/Voice Alignée

**RECO TYPE:** Aligner tone et voice
**IMPACT:** 3 | **EFFORT:** 1-2 | **SCORE P1:** 12-16

**PROBLÈME TYPE:**
Tone incohérent entre sections (formel vs. fun, sérieux vs. playful) → confus.

**SOLUTIONS:**

1. **[Effort 1]** Définir tone cible
   - Formel? Fun? Urgent? Rassurant?
   - Basé sur audience (B2B vs B2C), industrie, brand
   - Document tone guide (1 page suffit)

2. **[Effort 1]** Auditez toute la copy
   - Vérifier cohérence d'une section à l'autre
   - Identifier inconsistencies (une section fun, suivante formelle)
   - Corriger pour uniformité

3. **[Effort 1]** Adapter tone à chaque audience
   - B2B (formé, confiant): Tone factuel, respectueux, expert
   - B2C (débutant): Tone simple, conversationnel, bienveillant
   - Startup (ambitieux): Tone énergique, disruptif, forward-thinking

4. **[Effort 1]** Créer "tone template"
   - Exemple phrase dans chaque tone
   - Utiliser pour guider réécriture
   - Exemple:
     - Formel: "Nos solutions augmentent votre productivité de manière significative"
     - Conversationnel: "On te fait gagner 5h par semaine — c'est fou"

5. **[Effort 2]** Mettre à jour voice/brand elements
   - Catchphrases cohérentes
   - Vocabulaire récurrent
   - Style ponctuation (ex: listes avec tirets vs. numéros)

**TONE GUIDELINES TEMPLATE:**

```
Tone: [Formel / Conversationnel / Enjoué / Urgent]
Voice: [Brand personality]

DO:
- Utilise [style]
- Parle de [bénéfice]
- Adresse [audience]

DON'T:
- Évite [style]
- N'utilise pas [jargon]
- Pas trop [attitude]

Exemple bon: "[Phrase exemple]"
Exemple mauvais: "[Phrase à éviter]"
```

**PSYCHOLOGIE:** Audience Alignment, Brand Consistency

---

### 2.4 Templates Structure & UX (Critères 4.1-4.7)

#### Critère 4.1 - Hiérarchie Visuelle

**RECO TYPE:** Restructurer hiérarchie
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Tous les éléments au même niveau visuel → difficile de scanner → compréhension basse.

**SOLUTIONS:**

1. **[Effort 1]** Appliquer "F-Pattern" ou "Z-Pattern"
   - F-Pattern: top-left → droite → scan vertical (articles/blogs)
   - Z-Pattern: top-left → top-right → diagonal → bas-droit (landing pages)
   - Organiser éléments selon le pattern

2. **[Effort 1]** Établir hiérarchie de tailles
   - H1 (Headline): 48px+
   - H2 (Section titles): 32px+
   - H3 (Subheadings): 24px+
   - Body: 16px
   - Small: 14px
   - Chaque niveau visuellement distinct

3. **[Effort 1]** Utiliser couleur pour créer hiérarchie
   - Headline: Couleur primaire (ou noir fort)
   - Section titles: Couleur secondaire ou gris foncé
   - Body text: Gris moyen
   - CTA button: Couleur primaire + bold

4. **[Effort 2]** Réarranger sections pour améliorer scan
   - Mettre éléments importants en haut
   - Laisser whitespace entre sections
   - Tester: lire juste les titres → ça raconte l'histoire?

5. **[Effort 2]** Ajouter visuels (icons, images) pour hiérarchie
   - Chaque section = icon distinct
   - Aide le scan (visual anchor)
   - Crée variation visuelle

**CHECKLIST HIÉRARCHIE:**

- [ ] Headline clairement plus grand que sous-titres
- [ ] Contraste texte/fond adéquat (≥ 4.5:1)
- [ ] Couleur utilisée pour créer priorité (not just for fun)
- [ ] Un message majeur par section
- [ ] Whitespace entre sections
- [ ] Tester: lire juste les titres = histoire cohérente?

**PSYCHOLOGY:** Visual Hierarchy, Cognitive Load

---

#### Critère 4.2 - Whitespace

**RECO TYPE:** Améliorer whitespace
**IMPACT:** 3 | **EFFORT:** 1-2 | **SCORE P1:** 12-16

**PROBLÈME TYPE:**
Page trop serrée (pas de whitespace) → confuse → difficile à lire.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter padding/margin entre sections
   - Min: 32px top/bottom par section
   - Idéal: 48-64px
   - Crée breathing room

2. **[Effort 1]** Ajouter whitespace vertical entre éléments
   - Entre headline et body: 16px
   - Entre body et CTA: 24px
   - Entre sections: 48px+

3. **[Effort 1]** Réduire # éléments par section
   - Mauvais: 10 bullet points crammed
   - Bon: 3-5 bullet points avec whitespace
   - Plus aéré = plus lisible

4. **[Effort 2]** Utiliser layout columns
   - Single column (mobile): plus d'espace vertical
   - Two column (desktop): whitespace horizontal
   - Créé aération visuelle

5. **[Effort 1]** Tester "squint test"
   - Squint à l'écran (ou flouter)
   - Ça devrait être scannable en 5 sec
   - Si trop fouilli → ajouter whitespace

**WHITESPACE GUIDELINES:**

- Header/Logo space: 16-24px
- Section top margin: 32-64px
- Section bottom margin: 32-64px
- Padding dentro de sections: 24-32px
- Between text lines: 1.5-1.8 line-height

**PSYCHOLOGY:** Cognitive Ease, Information Processing

---

#### Critère 4.3 - Scannabilité

**RECO TYPE:** Optimiser scannabilité
**IMPACT:** 4 | **EFFORT:** 1 | **SCORE P1:** 20

**PROBLÈME TYPE:**
Visiteur scanne page en 5 sec, pas de structure claire → quitte.

**SOLUTIONS:**

1. **[Effort 1]** Utiliser bullet points + listes
   - Mauvais: "Les clients peuvent utiliser notre logiciel de plusieurs façons. Ils peuvent créer des documents..."
   - Bon:
     - "Créez des documents en 5 min"
     - "Collaborez en temps réel"
     - "Exportez en PDF, Word, Google Docs"

2. **[Effort 1]** Ajouter bold/couleur aux mots-clés
   - Highlight 1-3 mots par phrase
   - L'oeil capture les words clés en scanning
   - Améliore compréhension rapide

3. **[Effort 1]** Créer "headline-only" version
   - Enlever tout body text
   - Lire juste les H2 de la page
   - Ça doit raconter une histoire
   - Si non → rewriter/reorganize

4. **[Effort 1]** Utiliser short paragraphs
   - Max 3-4 phrases par paragraphe
   - Max 2 paragraphes par section
   - Sinon break en bullet points

5. **[Effort 2]** Ajouter infographics/visuels
   - Comparaison tableau (Our vs. Competitor)
   - Process step-by-step
   - Data visualization
   - Aide au scanning

**SCANNABLE STRUCTURE:**

```
HERO SECTION
[Big Headline] - 5-8 words, benefit
[Sub-headline] - Who, what, how
[CTA Button]

SECTION 2
[H2] - Clear benefit
- Bullet point 1
- Bullet point 2
- Bullet point 3
[Optional: Small image/icon]

SECTION 3
[H2]
[Body paragraph 1]
[Body paragraph 2 max]
(Or break into bullets)
```

**PSYCHOLOGY:** Cognitive Load, Information Scannability

---

#### Critère 4.4 - Mobile-First UX

**RECO TYPE:** Optimiser mobile UX
**IMPACT:** 5 | **EFFORT:** 2-3 | **SCORE P1:** 8-20

**PROBLÈME TYPE:**
Page optimisée desktop mais cassée mobile (85-95% du trafic). Mauvaise UX mobile = abandon.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter CTA sticky header + footer (mobile)
   - Header: CTA fixe en haut
   - Footer: CTA fixe en bas
   - Toujours visible, accessible au pouce

2. **[Effort 1]** Élargir zones cliquables
   - Min: 44×44px (iOS), idéal 48×56px
   - Padding entre buttons (minimum 8px)
   - Surtout sur mobile (petits doigts)

3. **[Effort 2]** Vérifier thumb zone (bottom 20% accessible)
   - CTA importants en bas ou header sticky
   - Menus hamburger en haut
   - Éviter CTA dans "unreachable zone" (top-right)

4. **[Effort 2]** Adapter images mobile
   - Portfolio format (vertical), pas paysage
   - Lazy loading (charge au scroll)
   - Compresser pour mobile (< 100KB)

5. **[Effort 2]** Simplifier formulaires mobile
   - Une colonne
   - Un champ par "row"
   - Padding vertical entre champs (20px+)
   - Auto-focus sur champ premier

6. **[Effort 2]** Tester sur vrais devices
   - iPhone 12, 14, etc.
   - Samsung Galaxy
   - Tablet (iPad)
   - Pas juste "resize browser"

**MOBILE UX CHECKLIST:**

- [ ] CTA visible top + bottom
- [ ] Tous les boutons ≥ 44×44px
- [ ] Padding entre clickables ≥ 8px
- [ ] Pas de pop-ups bloquantes non-closable
- [ ] Pas d'autoplay vidéo + son
- [ ] Images responsive (portrait-optimized)
- [ ] Formulaires un champ par row
- [ ] Menu hamburger, pas full nav

**PSYCHOLOGY:** Accessibility, Thumb Zone Psychology

---

#### Critère 4.5 - Formulaires Optimisés

**RECO TYPE:** Simplifier formulaire
**IMPACT:** 5 | **EFFORT:** 2-3 | **SCORE P1:** 8-20

**PROBLÈME TYPE:**
Formulaire trop long ou mal organisé → abandons, drop-off élevé.

**SOLUTIONS:**

1. **[Effort 1]** Réduire # champs
   - Start: max 5 champs (pour lead gen)
   - Vente: max 3 champs (email, nom, tel)
   - Chat: email seulement
   - Progressif: demander info additionnelle après

2. **[Effort 1]** Utiliser progressive disclosure
   - Afficher 3 champs initiaux
   - "Cliquez suivant pour continuer"
   - Puis 2-3 champs additionnels
   - Réduit cognitive load

3. **[Effort 2]** Améliorer layout formulaire
   - Une colonne (pas side-by-side)
   - Padding vertical entre champs (20px+)
   - Labels clairs et concis
   - Placeholder text pas trop pâle

4. **[Effort 2]** Ajouter validation temps réel
   - Feedback immédiat (email format OK, etc.)
   - Erreurs claires (pas "invalid input")
   - Help text sous champs confus

5. **[Effort 2]** Ajouter micro-copy rassurance
   - Sous le formulaire: "Nous ne partagerons jamais tes données"
   - Sous submit: "Essai gratuit, sans engagement"
   - Icons confiance (SSL, GDPR, etc.)

**FORMULAIRE TEMPLATE:**

```
[Label] Email
[Input field]
Help text: "Où tu travailles"

[Label] Nom complet
[Input field]

[Label] Entreprise
[Input field]
Help text: "Pour une expérience tailored"

[CTA Button] Créer mon compte gratuit
Micro-copy: "Essai 14j, aucune CB"
```

**PSYCHOLOGY:** Cognitive Load, Progressive Disclosure

---

#### Critère 4.6 - Flow et Progression

**RECO TYPE:** Améliorer flow page
**IMPACT:** 3 | **EFFORT:** 2 | **SCORE P1:** 9-12

**PROBLÈME TYPE:**
Sections jumbled, pas de progression logique → visiteur perd fil rouge → bounce.

**SOLUTIONS:**

1. **[Effort 2]** Créer "customer journey map"
   - Unaware → Problem Aware → Solution Aware → Product Aware → Most Aware
   - Reorder sections selon ce journey
   - Chaque section adresse une étape

2. **[Effort 2]** Appliquer "Problem → Solution → Proof → CTA"
   - Section 1: Identifie le pain point (visiteur se reconnaît)
   - Section 2: Présente la solution
   - Section 3: Fournit preuve (testimonial, case study)
   - Section 4: CTA finale

3. **[Effort 1]** Ajouter transitions/bridging text
   - Entre sections, ajouter 1-2 phrases de transition
   - "Maintenant que tu comprends le problème, voici la solution..."
   - Crée continuité narrative

4. **[Effort 2]** Utiliser "nested structure"
   - Chaque section a: (Intro) → (Body) → (Bridge to next)
   - Crée flow naturel
   - Visiteur flow logiquement

**PROGRESSION TEMPLATE:**

```
SECTION 1: PROBLEM
[Headline: Identify pain point]
[Body: Normal the problem]
[Bridge: "So how do we solve this?"]

SECTION 2: SOLUTION
[Headline: Introduce solution]
[Body: Explain how it works]
[Bridge: "Proof? Here's what happens..."]

SECTION 3: PROOF
[Testimonials, Case studies, Stats]
[Bridge: "Ready to get started?"]

SECTION 4: CTA
[Final call to action]
[Micro-reassurance]
```

**PSYCHOLOGY:** Narrative Arc, Coherence

---

#### Critère 4.7 - Réduire Distractions (Liens de Sortie)

**RECO TYPE:** Réduire distractions
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Menu/footer chargés, trop de liens de sortie → visiteur distrait → abandonne la page.

**SOLUTIONS:**

1. **[Effort 1]** Masquer/minimiser menu navigation
   - Desktop: Menu hamburger (hidden par défaut)
   - Mobile: Hamburger menu obligatoire
   - Réduit visibilité distractions

2. **[Effort 1]** Réduire footer
   - Pas d'arborescence large
   - Max 3-4 catégories de liens
   - Ou footer minimal (contact + legal uniquement)

3. **[Effort 1]** Réduire liens internes
   - Enlever liens vers "autres produits"
   - Enlever liens vers "blog"
   - Garder max 1-2 liens alternatifs (FAQ, contact)

4. **[Effort 1]** Déplacer liens externes
   - Si article/case study cités, placer sous le fold
   - Pas de liens qui sortent de la page
   - Alternative: "Lire le full case study [après conversio]"

5. **[Effort 2]** Utiliser "ratio d'attention 1:1"
   - Par CTA principal, max 1 lien alternatif
   - Si 1 CTA de vente, max 1 lien de sortie (FAQ, démo)
   - Réduire compétition pour l'attention

**DISTRACTION AUDIT:**

- [ ] Compter # links hors CTA principal
- [ ] Vérifier si menu visible (distrait?)
- [ ] Analyser footer (trop de liens?)
- [ ] Identifier liens "siphon attention" (blog, produits autres)
- [ ] Réduire à ratio 1:1

**PSYCHOLOGY:** Attention Economics, Goal Priming

---

### 2.5 Templates Qualité Technique (Critères 5.1-5.5)

#### Critère 5.1 - Performance Page

**RECO TYPE:** Optimiser performance
**IMPACT:** 3 | **EFFORT:** 2-3 | **SCORE P1:** 6-12

**PROBLÈME TYPE:**
Page lente (LCP > 2.5s, FID > 100ms, CLS > 0.1) → abandons mobiles → perte conversion.

**SOLUTIONS:**

1. **[Effort 1]** Vérifier Core Web Vitals
   - LCP (Largest Contentful Paint): < 2.5s
   - FID (First Input Delay): < 100ms
   - CLS (Cumulative Layout Shift): < 0.1
   - Tool: Google PageSpeed Insights, GTmetrix

2. **[Effort 2]** Compresser images
   - Utiliser format WebP
   - Lazy loading (charger au scroll)
   - Responsive images (tailored par viewport)
   - Target: < 100KB per image

3. **[Effort 2]** Optimiser CSS/JS
   - Minify CSS/JS
   - Defer JS non-critical
   - Code split pour réduire bundle
   - Lazy load scripts (chat, analytics)

4. **[Effort 2]** Implémenter caching
   - Browser caching (images, CSS, JS)
   - CDN pour assets statiques
   - Cache 304 responses

5. **[Effort 1]** Tester sur 4G lent
   - Chrome DevTools: throttle à "Fast 4G"
   - Vérifier que page reste usable
   - Mobile users = priorité

**PERFORMANCE CHECKLIST:**

- [ ] LCP < 2.5s (Google target)
- [ ] FID < 100ms
- [ ] CLS < 0.1
- [ ] Images < 100KB each
- [ ] CSS minified
- [ ] JS deferred
- [ ] Tested on 4G throttle

**PSYCHOLOGY:** Speed = Friction Reduction

---

#### Critère 5.2 - Cross-Browser Compatibility

**RECO TYPE:** Tester/fixer bugs cross-browser
**IMPACT:** 2 | **EFFORT:** 1-3 | **SCORE P1:** 4-12

**PROBLÈME TYPE:**
Page OK sur Chrome, cassée sur Safari/Firefox → perte de visiteurs.

**SOLUTIONS:**

1. **[Effort 1]** Tester sur 4 navigateurs majeurs
   - Chrome (+ Android via Chrome mobile)
   - Safari (+ iOS via Safari mobile)
   - Firefox
   - Edge
   - Tools: BrowserStack, LambdaTest

2. **[Effort 2]** Corriger CSS issues
   - Flexbox comportement différent (Safari)
   - Gradients pas supportés (IE)
   - Border-radius, box-shadow variations
   - Use vendor prefixes (-webkit-, -moz-)

3. **[Effort 2]** Corriger JS issues
   - Promise support (IE11)
   - Array methods (IE)
   - fetch API (IE)
   - Use polyfills ou feature detection

4. **[Effort 2]** Tester form submission
   - Envoyer test form sur chaque navigateur
   - Vérifier email de confirmation reçu
   - Vérifier redirects post-submit

5. **[Effort 1]** Utiliser caniuse.com
   - Avant d'utiliser CSS/JS feature
   - Vérifier compatibilité
   - Plan fallback si needed

**BROWSER TEST CHECKLIST:**

- [ ] Chrome (desktop + mobile)
- [ ] Safari (desktop + iOS)
- [ ] Firefox (desktop + mobile)
- [ ] Edge
- [ ] Forms submit successfully
- [ ] No visual glitches
- [ ] Links work
- [ ] Videos play

**PSYCHOLOGY:** Trust = no bugs visible

---

#### Critère 5.3 - Mobile Responsivity

**RECO TYPE:** Corriger responsive design
**IMPACT:** 4 | **EFFORT:** 2-3 | **SCORE P1:** 8-16

**PROBLÈME TYPE:**
Responsive CSS broken (éléments chevauchés, trop petits, pas alignés mobile).

**SOLUTIONS:**

1. **[Effort 1]** Tester viewports clés
   - 375px (iPhone SE)
   - 768px (iPad)
   - 1440px (Desktop)
   - DevTools resize, pas manual scroll

2. **[Effort 2]** Corriger layout
   - Single column mobile
   - 2-column tablet
   - 3+ column desktop
   - Media queries pour breakpoints

3. **[Effort 2]** Corriger font sizes
   - Mobile: 16px min (avoid zoom)
   - Tablet: 18px
   - Desktop: 16-20px
   - Utiliser vw/relative units si possible

4. **[Effort 2]** Corriger images
   - Aspect ratio locked (prevent CLS)
   - Responsive src (srcset)
   - Mobile-optimized crops (portrait)

5. **[Effort 1]** Tester sur vrais devices
   - iPhone 12, 14
   - iPad
   - Android phone (Samsung)
   - Chrome DevTools ne suffit pas

**RESPONSIVE BREAKPOINTS:**

```css
Mobile: 320px - 480px
Tablet: 481px - 768px
Desktop: 769px+
```

**PSYCHOLOGY:** Accessibility, Usability

---

#### Critère 5.4 - Formulaires Fonctionnels

**RECO TYPE:** Déboguer formulaires
**IMPACT:** 5 | **EFFORT:** 1-2 | **SCORE P1:** 20-25

**PROBLÈME TYPE:**
Formulaire ne se soumet pas / emails pas reçus / erreurs non-claires.

**SOLUTIONS:**

1. **[Effort 1]** Soumettre test form
   - Remplir tous les champs
   - Cliquer submit
   - Email de confirmation reçu dans inbox?
   - Si non: déboguer immédiatement

2. **[Effort 1]** Vérifier error messages
   - Essayer submit avec email vide
   - Message d'erreur clear?
   - Highlight le champ erroné?

3. **[Effort 1]** Vérifier validation
   - Email format: rejette "test"?
   - Required fields: rejet si vide?
   - Field-level feedback?

4. **[Effort 2]** Configurer email confirmation
   - Utilisateur reçoit email post-submit?
   - Email contient les infos soumises?
   - Business reçoit notification aussi?

5. **[Effort 1]** Tester cross-browser form
   - Chrome, Safari, Firefox
   - Chacun: submit test
   - Vérifier email reçu

**FORM QA CHECKLIST:**

- [ ] Submit test form → email reçu?
- [ ] Error messages clairs
- [ ] Required fields validated
- [ ] Email format validated
- [ ] Phone number accepted (diverse formats?)
- [ ] Dropdown options working
- [ ] Checkbox/radio buttons functional
- [ ] Confirmation email sent
- [ ] Cross-browser tested

**PSYCHOLOGY:** Trust = everything works

---

#### Critère 5.5 - Analytics/Tracking Implémenté

**RECO TYPE:** Implémenter tracking
**IMPACT:** 2 | **EFFORT:** 2 | **SCORE P1:** 4-8

**PROBLÈME TYPE:**
Pas de tracking ou tracking incomplet → data aveugle pour optimiser.

**SOLUTIONS:**

1. **[Effort 1]** Implémenter GA4
   - Google Analytics 4 (GA4)
   - Page view tracking
   - Scroll depth tracking
   - Event tracking pour CTA clicks

2. **[Effort 1]** Implémenter conversion tracking
   - Facebook Pixel (pour Meta ads)
   - Google Ads Conversion (pour Google ads)
   - Tracking form submissions
   - Tracking purchases (si ecommerce)

3. **[Effort 1]** Implémenter event tracking
   - CTA clicks (track which button)
   - Form starts (incomplete funnel)
   - Video plays (engagement)
   - Download clicks
   - External link clicks

4. **[Effort 2]** Implémenter heatmaps
   - Hotjar ou Crazy Egg
   - Voir où cliquent les visiteurs
   - Scroll depth visualization
   - Session recordings (debugging)

5. **[Effort 1]** Vérifier tracking works
   - Trigger test event
   - Check GA4 real-time
   - Pixel firing?
   - Revenue tracked (si applicable)?

**TRACKING SETUP CHECKLIST:**

- [ ] GA4 implemented
- [ ] Pageviews tracked
- [ ] CTA clicks tracked as events
- [ ] Form submissions tracked
- [ ] Conversion pixels (Meta, Google)
- [ ] Heatmaps (optional but useful)
- [ ] Verify in real-time reports

**PSYCHOLOGY:** Data-driven = confident decisions

---

### 2.6 Templates Psychologie de Conversion (Critères 6.1-6.6)

#### Critère 6.1 - Cognitive Ease

**RECO TYPE:** Simplifier compréhension
**IMPACT:** 4 | **EFFORT:** 1 | **SCORE P1:** 20

**PROBLÈME TYPE:**
Page demande trop d'effort cognitif → visiteur abandonne → recherche concurrents.

**SOLUTIONS:**

1. **[Effort 1]** Simplifier copy
   - Max 12 mots par headline
   - Max 25 mots par sous-titre
   - Courtes phrases (10-15 mots max)
   - Éviter jargon/acronymes

2. **[Effort 1]** Utiliser common vocabulary
   - Remplacer "facilitate" par "help"
   - Remplacer "utilize" par "use"
   - Remplacer "paradigm shift" par "change"
   - Plus facile = plus rapide à comprendre

3. **[Effort 1]** Utiliser familiar patterns
   - Hero + Benefits + Social Proof + CTA (pattern reconnu)
   - Visiteur comprend avant même de lire
   - Réduit cognitive load

4. **[Effort 1]** Utiliser transitions claires
   - "Voici le problème... Voici la solution... Voici la preuve... Action:"
   - Visiteur sait où il est dans la narrative
   - Réduit confusion

5. **[Effort 1]** Ajouter whitespace + breathing room
   - Pas de fouillis
   - Un concept par section
   - Section = une idée max

**COPY SIMPLIFICATION:**

- Complexe: "Our innovative solution leverages AI to optimize operational efficiency metrics"
- Simple: "Our AI saves you 5 hours/week"

**PSYCHOLOGY:** Cognitive Ease (Kahneman), Fluency Effect

---

#### Critère 6.2 - Social Proof Anchoring

**RECO TYPE:** Ancrer avec social proof
**IMPACT:** 4 | **EFFORT:** 2 | **SCORE P1:** 8-16

**PROBLÈME TYPE:**
Visiteur hésite → pas de "preuve que ça marche" → abandonne.

**SOLUTIONS:**

1. **[Effort 1]** Placer social proof au bon moment
   - ATF: small stat ("15,000+ clients")
   - Mid-page: testimonials (adresse objection)
   - Near CTA: guarantee ("30j remboursé")

2. **[Effort 1]** Ajouter "anchor stat"
   - Nombre clients: "[X] clients"
   - Résultats: "[Y]% augmentation de conversion"
   - Satisfaction: "[Z]★ (N avis)"
   - Établit crédibilité

3. **[Effort 2]** Intégrer testimonials vidéo
   - Client parle (authentic)
   - 30-60 secondes max
   - Placement: hero ou mid-page
   - Améliore conversion de 15-30%

4. **[Effort 2]** Créer case study chiffré
   - Company [X], Résultat [Y], Time [Z]
   - Détail concret
   - Crée confiance

5. **[Effort 1]** Ajouter "social proof element" répété
   - "5,000 freelances gagnent maintenant 6-7 figures"
   - Utiliser dans hero + social proof section + CTA
   - Répétition = ancrage psychologique

**SOCIAL PROOF ANCHORING FORMULA:**

```
STAT TO ANCHOR WITH:
"[X] [audience] achieve [result] using our [product]"

Examples:
- "14,000 freelances earn $100k+ annually with our system"
- "2,847 e-com stores doubled their CVR in 90 days"
- "Rated 4.9★ by 5,000+ users on Trustpilot"
```

**PSYCHOLOGY:** Social Proof, Anchoring Effect, Authority

---

#### Critère 6.3 - Anchoring de Prix

**RECO TYPE:** Utiliser anchoring effet
**IMPACT:** 3 | **EFFORT:** 1 | **SCORE P1:** 15

**PROBLÈME TYPE:**
Pas de point de référence pour le prix → visiteur pense "cher" → quitte.

**SOLUTIONS:**

1. **[Effort 1]** Afficher "prix avant" vs "prix maintenant"
   - "Régulièrement $297, Maintenant $99"
   - Anchore prix régulier = référence
   - Améliore perception valeur de 15-25%

2. **[Effort 1]** Comparer avec équivalent
   - "Coûte moins qu'une tasse de café par jour ($0.33/j)"
   - Rend prix relatable
   - Réduit perceived cost

3. **[Effort 1]** Utiliser "price anchoring" avec tiers
   - Basic: $99
   - Pro: $199 (anchor moyen)
   - Premium: $399 (makes Pro look valuable)
   - Pro devient "sweet spot"

4. **[Effort 1]** Ajouter valeur déclarée
   - "Valeur réelle du cours: $1,997"
   - "Prix de lancement: $99"
   - "Économie: $1,898"
   - Crée perception de deal

5. **[Effort 2]** Créer "alternative pricing"
   - "Payez $199/mois (cancel anytime) OU $99 (lifetime)"
   - Lifetime pricing anchore plus bas
   - Améliore conversions

**PRICING ANCHOR EXAMPLES:**

- Régularly $497, Now $147 (70% off)
- Worth $10,000 in value, Yours for $397
- Costs less than 1 hour of consultant time (normally $250/h)

**PSYCHOLOGY:** Anchoring Effect, Price Perception, Comparative Thinking

---

#### Critère 6.4 - Loss Aversion Framing

**RECO TYPE:** Framer losses
**IMPACT:** 3 | **EFFORT:** 1 | **SCORE P1:** 15

**PROBLÈME TYPE:**
Page focus sur gains, pas sur "what you're missing" → moins motivant.

**SOLUTIONS:**

1. **[Effort 1]** Réécrire bénéfices en termes de LOSS AVOIDANCE
   - Gain frame: "Gagnez 5h/semaine"
   - Loss frame: "Arrêtez de perdre 5h/semaine"
   - Loss frame = plus motivant

2. **[Effort 1]** Ajouter "problem cost" section
   - "Si tu continues comme ça, tu perds..."
   - "Chaque jour sans [solution], c'est $X en perte"
   - Crée urgency

3. **[Effort 1]** Utiliser "fear-based" messaging (subtle)
   - "Sais-tu que 73% des [audience] font cette erreur?"
   - "Les [competitors] gagnent déjà [resultat], toi?"
   - Motivé par loss aversion

4. **[Effort 1]** Ajouter "FOMO angle"
   - "Dans 6 mois, tu auras économisé [X] heures ou perdu [X] heures"
   - Visiteur se voit dans le futur
   - Motiv par desire d'avoid regret

5. **[Effort 1]** Créer "cost of inaction"
   - Calculer coût monthly de ne rien faire
   - "Inaction te coûte $500/mois"
   - Comparé au prix produit ($99)
   - ROI évident

**LOSS FRAME EXAMPLES:**

- Gain: "Save 5 hours/week"
  Loss: "Stop wasting 5 hours/week"

- Gain: "Increase conversion by 25%"
  Loss: "Prevent losing $10,000/month in missed sales"

**PSYCHOLOGY:** Loss Aversion (Kahneman), Prospect Theory

---

#### Critère 6.5 - FOMO/Urgence Activation

**RECO TYPE:** Activer FOMO
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Pas d'urgence → visiteur bookmarke et part → jamais revient.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter deadline clair
   - "Offer available until May 15"
   - Countdown timer (psychology FOMO)
   - Afficher: "[X] days left"

2. **[Effort 1]** Ajouter scarcité quantité
   - "100 spots limited"
   - Meter de remplissage visible
   - "[X]/100 spots taken, [Y] available"

3. **[Effort 1]** Ajouter scarcité sociale
   - "[X] people registered this week"
   - "At this rate, full in [X] days"
   - "Join the [X] founders who already..."

4. **[Effort 1]** Ajouter bonus temporaire
   - "Sign up before May 15 → bonus access to [resource]"
   - Bonus disponible que pour early adopters
   - Crée FOMO

5. **[Effort 2]** Créer "limited time offer" section
   - Dédié à l'urgence
   - Countdown timer
   - Bonus + Deadline + Scarcité
   - Placement: attention-grabbing

**FOMO ACTIVATION FORMULA:**

```
[DEADLINE] + [SCARCITY] + [BONUS] = FOMO

Example:
"Price increases to $297 on May 15"
+ "100 spots available (47 taken)"
+ "Early bird bonus: $500 lifetime access to updates"
= FOMO activated
```

**PSYCHOLOGY:** FOMO, Scarcity Principle, Loss Aversion

---

#### Critère 6.6 - Trust Markers Visibles

**RECO TYPE:** Ajouter trust markers
**IMPACT:** 4 | **EFFORT:** 1-2 | **SCORE P1:** 16-20

**PROBLÈME TYPE:**
Visiteur hésite (est-ce vraiment sûr?) → manque trust markers → bounce.

**SOLUTIONS:**

1. **[Effort 1]** Ajouter security badges
   - SSL/HTTPS badge ("Sécurisé par...")
   - Stripe/PayPal badge (si paiement)
   - GDPR compliant label (si EU)
   - Placement: Near CTA ou footer

2. **[Effort 1]** Ajouter certification badges
   - "Certified [Organisme]"
   - "Award: [Prix]"
   - "Featured in [Publication]"
   - Établit crédibilité

3. **[Effort 1]** Ajouter company credibility
   - Fondée [année]
   - "[X] clients served"
   - "$[X]M raised" (si relevant)
   - "Trusted by [Industry leaders]"

4. **[Effort 2]** Ajouter team photos
   - Vrai team members
   - Humanize la company
   - Crée trustworthiness
   - Placement: About section

5. **[Effort 1]** Ajouter privacy/terms clarity
   - "Your data is safe" + link to privacy policy
   - "No spam, ever" (si newsletter)
   - "Cancel anytime, no questions asked"
   - Réduit crainte

**TRUST MARKER CHECKLIST:**

- [ ] SSL/Security badge visible
- [ ] Certifications/Awards displayed
- [ ] Social proof numbers (clients, avis)
- [ ] Contact info clear (email, phone, address)
- [ ] Privacy policy + Terms linked
- [ ] Team photos (si B2B/premium)
- [ ] Company founding year/history
- [ ] Logos partenaires/clients

**PSYCHOLOGY:** Trust Signals, Credibility, Social Proof

---

## 3. COPY REWRITE ENGINE

### 3.1 Framework de Réécriture

Pour chaque reco touchant du copy, le process est :

1. **Identifier le texte actuel et son intention**
   - Quoi dit le texte maintenant?
   - Quelle était l'intention originale?
   - Pourquoi ça ne marche pas?

2. **Identifier le framework copy le plus adapté**
   - PAS (Problem, Agitate, Solution)
   - AIDA (Attention, Interest, Desire, Action)
   - BAB (Before, After, Bridge)
   - FAB (Feature, Advantage, Benefit)
   - PASTOR (Problem, Amplify, Story, Transformation, Objection, Response)
   - StoryBrand (Hook, Problem, Guide, Plan, Call, Failure, Success)
   - 4P (Promise, Picture, Proof, Push)
   - CAP (Consequence, Action, Payoff)

3. **Identifier le niveau Schwartz de l'audience**
   - Unaware (don't know problem exists)
   - Problem-aware (know problem, not solution)
   - Solution-aware (know solution, not product)
   - Product-aware (know product, not convinced)
   - Most-aware (convinced, ready to buy)

4. **Générer 3 alternatives avec justification**
   - Alt A: Framework X
   - Alt B: Framework Y
   - Alt C: Framework Z
   - Justification pour chacun

### 3.2 Règles de Réécriture par Élément

#### Headlines

**Règles:**
- Max 12 mots (benchmark haute conversion)
- Structure: Bénéfice + Spécificité
- Test "So what?" appliqué 3x → pas de genericité
- Éviter: Buzzwords (innovant, solution, leader), jargon, genericité

**Process:**
1. Extraire le bénéfice core
2. Ajouter spécificité (chiffre, délai, audience)
3. Vérifier "So what?" test → chaque mot ajoute valeur?

**Exemples:**

Mauvais: "Solution innovante"
Bon: "Gagnez 5h/semaine sans apprendre à coder"

Mauvais: "Bienvenue sur notre site"
Bon: "Doublez votre productivité en 30 jours (gratuit)"

#### Sous-titres

**Règles:**
- Max 25 mots
- Complémente headline (ne répète pas)
- Ajoute le "comment" ou le "pour qui"

**Process:**
1. Lire le headline
2. Écrire sous-titre qui répond: "Comment?" ou "Pour qui?"
3. Vérifier: sans sous-titre, headline fait sens? Si oui, trop redondant.

**Exemples:**

H1: "Gagnez 5h/semaine"
H2 (mauvais): "Notre logiciel te fait gagner 5h/semaine"
H2 (bon): "Avec notre IA de scheduling — Aucune formation requise"

#### CTAs

**Règles:**
- Verbe d'action + bénéfice
- Éviter: "Envoyer", "Soumettre", "Continuer"
- Max 5 mots

**Process:**
1. Identifier l'action (Acheter, S'inscrire, Réserver, etc.)
2. Identifier le bénéfice (gratuit, immédiat, démo, etc.)
3. Combiner: "[Verbe] mon [bénéfice]"

**Exemples:**

Mauvais: "Envoyer"
Bon: "Recevoir mon devis"

Mauvais: "Cliquer ici"
Bon: "Commencer mon essai gratuit"

#### Micro-copy

**Règles:**
- Réassurance
- Objection killer
- Max 8 mots
- Placement: sous CTA ou dans formulaire

**Process:**
1. Identifier l'objection implicite
2. Écrire reassurance qui l'adresse
3. Placer directement sous élément créant objection

**Exemples:**

Objection: "Will this cost me?"
Micro-copy: "Essai gratuit, sans engagement"

Objection: "Is this secure?"
Micro-copy: "Sécurisé par Stripe (encryption 256-bit)"

#### Social Proof Titres

**Règles:**
- Spécificité
- Chiffres concrets
- Éviter: "Ils nous font confiance"

**Exemples:**

Mauvais: "Ils nous font confiance"
Bon: "Rejoignez 2,847 e-commerçants qui ont doublé leur taux de conversion"

#### Bullet Points

**Règles:**
- Bénéfice first, feature second
- Format: "[Bénéfice] ([Feature])"
- Max 10 mots par point

**Exemples:**

Mauvais: "API intégrée avec Slack"
Bon: "Reçois notifications où tu travailles (Slack intégré)"

### 3.3 Bibliothèque de Formules par Intention

#### Promesse de Résultat

"Obtenez [résultat] en [temps] sans [obstacle]"

Exemples:
- "Gagnez 5h/semaine sans apprendre à coder"
- "Doublez votre revenu en 90 jours sans créer un produit"
- "Augmentez votre CVR de 25% sans changer votre design"

#### Curiosité

"Le secret que [audience] utilisent pour [résultat]"

Exemples:
- "Le secret que 2,847 e-commerçants utilisent pour doubler leur CVR"
- "Le truc que les top 1% des founders utilisent pour scaler vite"

#### Social Proof

"[Nombre] [audience] ont déjà [résultat]. Et toi?"

Exemples:
- "14,000 freelances gagnent maintenant 6-7 figures — Tu pourrais être le suivant"
- "2,500+ startups ont levé leurs séries A avec notre help"

#### Question Rhétorique

"Et si [pain point] n'était plus un problème?"

Exemples:
- "Et si tu ne passais 0 heures en réunions improductives?"
- "Et si lancer ton produit prenait 48 heures, pas 6 mois?"

#### Contre-intuition

"Pourquoi [croyance commune] est faux (et comment [résultat])"

Exemples:
- "Pourquoi le CRO traditionnel échoue (et notre approche génère +45% CVR)"
- "Pourquoi vous gaspillez 80% du budget ads (et comment l'optimiser)"

#### Urgence

"[Offre] disponible jusqu'au [date] — [bénéfice]"

Exemples:
- "Prix de lancement 50% jusqu'au 15 mai — Valeur réelle 1,997€"
- "100 spots disponibles — À ce rythme, complet dans 3 jours"

#### Comparaison

"[Approche A] vs [Approche B] : [différence mesurable]"

Exemples:
- "E-mail marketing vs SMS marketing: [SMS génère 5x plus de conversions]"
- "Hiring experts vs notre AI: [AI fait 10x plus, 100x moins cher]"

#### Transformation

"De [état A] à [état B] en [temps]"

Exemples:
- "De galère à 100k€/mois en 6 mois avec cette stratégie"
- "De founder solo à managing 50-person team (notre framework)"

#### Spécificité

"[Chiffre exact] [audience] ont augmenté [métrique] de [%] en [temps]"

Exemples:
- "873 managers ont augmenté leur productivité de 37% en 30 jours"
- "1,247 freelances ont augmenté leur taux horaire de 52% en 12 semaines"

#### Négatif

"[Nombre] erreurs qui tuent votre [métrique] (et comment les corriger)"

Exemples:
- "7 erreurs qui tuent votre taux de conversion (et comment les corriger en 48h)"
- "5 mistakes that cost you $100k/year in lost revenue"

---

## 4. MATRICE RECO × SECTION DE PAGE

| Section | Copy Issue | Design Issue | UX Issue | Technique | Psychologie |
|---------|-----------|-------------|----------|-----------|------------|
| **Header** | CTA wording optimization | Logo/nav visual hierarchy | Menu confusion, distraction | Sticky performance | Trust signals |
| **Hero** | Headline rewrite | Visual optimization | ATF visibility | Image optimization | Urgency framing |
| **Benefits** | Feature to benefit | Section layout hierarchy | Scannability | Performance | Social proof anchoring |
| **Social Proof** | Testimonial copy | Design grid layout | Placement clarity | Video performance | Trust markers |
| **How It Works** | Process clarity | Step visualization | Flow understanding | Animation performance | Cognitive ease |
| **Pricing** | Price framing, discount copy | Tier comparison visual | Option paralysis | Pricing table rendering | Anchoring effect |
| **FAQ** | Answer clarity, objection copy | Accordion design | Progressive disclosure | Searchability | Uncertainty reduction |
| **CTA Final** | Button text optimization | Button visual prominence | Click friction | Button functionality | FOMO activation |
| **Footer** | Legal/trust copy | Footer layout | Link distraction reduction | Footer loading | Privacy reassurance |

---

## 5. SCORING PRÉDICTIF DES RECOS

### 5.1 Estimation du Gain de Score

Pour chaque reco, estimer le gain de points si la reco est appliquée :

- **🔴 → 🟢 = +3 points** (optimiste, reco transformative)
  - Exemple: Réécrire headline + ajouter CTA sticky = transformation hero complète

- **🔴 → 🟡 = +1.5 points** (réaliste, amélioration partielle)
  - Exemple: Ajouter micro-copy rassurance = amélioration partielle du hero

- **🟡 → 🟢 = +1.5 points** (fine-tuning)
  - Exemple: Remplacer image hero par vidéo démo = fine-tuning du hero existant

### 5.2 Score Post-Reco Estimé

Calculer le score estimé après application des recos :

```
Score actuel: XX/108

Top P1 Recos (if applied):
- Reco 1: +3 points (reco transformative)
- Reco 2: +1.5 points
- Reco 3: +1.5 points
Total P1 gain: +6 points
→ Score estimé (P1 only): XX+6 = YY/108

Ajout P2 Recos:
- Reco 4: +1.5 points
- Reco 5: +1 point
Total P2 gain: +2.5 points
→ Score estimé (P1+P2): YY+2.5 = ZZ/108

Ajout P3 Recos:
- Reco 6: +0.5 points
Total P3 gain: +0.5 points
→ Score estimé (Full): ZZ+0.5 = WW/108
```

---

## 6. CONNEXION ÉCOSYSTÈME

### 6.1 Vers GSG (Growth Strategic Guide)

Le brief GSG est auto-généré à partir des recos :

**Format du brief:**
1. Résumé audit (score, top 3 problèmes)
2. Top 5 recos P1 (avec impact/effort)
3. Copy rewrites (3 variantes de headlines, CTAs)
4. Wireframe recommandé (layout optimisé)
5. Timeline d'exécution
6. Expected ROI (score estimé post-recos)

**Auto-mapping:**
- Recos de type "Copy" → Input "Rewrite Brief"
- Recos de type "Design" → Input "Design Spec"
- Recos de type "UX" → Input "Wireframe"

### 6.2 Depuis la Bibliothèque Concurrentielle

Pour chaque reco, chercher dans la bibliothèque des exemples de concurrents qui font bien ce critère :

**Format citation:**
"[Concurrent X] utilise cette approche avec succès : [description]. Benchmark: [chiffre de performance si disponible]"

**Exemple:**
"Unbounce utilise une promesse spécifique (Reco: Réécrire headline) avec succès : 'Create high-converting landing pages in minutes without a designer or developer.' Benchmark: 30% higher CTR que industrie."

### 6.3 Depuis le Swipe Library

Pour chaque reco de type section, proposer un pattern du Swipe Library comme référence :

**Format citation:**
"Pattern recommandé : [CAT-XX] [Nom du pattern] — Score: X/9"

**Exemple:**
"Pour reco 'Ajouter video testimonial', pattern recommandé : CAT-SP-47 'Customer Testimonial Video Grid' — Score: 8.5/9 (haute conversion)"

---

**END OF RECO ENGINE**

Version: 1.0 | Date: 2026-04-04 | Maintenu par: CRO Auditor Skill
