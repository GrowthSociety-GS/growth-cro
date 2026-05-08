# CRO Checklist Reference — Growth Site Generator

Consolidation des connaissances CRO critiques. Reference dense et actionnable pour optimisation de landing pages.

---

## 1. LES 11 ERREURS CLASSIQUES

### 1.1 Pas de proposition de valeur claire

**Impact:** 🔴 **Critique**

Visiteur ne comprend pas en < 5 secondes ce que vous proposez. Absence de headline distinctif ou proposition générique ("La meilleure solution du marché").

**Vérification:**
- [ ] Headline = bénéfice principal, pas feature
- [ ] Sous-titre clarifie immédiatement le "pour qui"
- [ ] Test des 5 secondes : visiteur peut expliquer votre offre sans lire

**Fix:**
- Réécrire headline : "Avant → Après" plutôt que "Solution XYZ"
- Ajouter subtitle spécifique au segment (ex: "Pour agences créatives qui facturent < 10k€/mois")
- Tester avec 5-10 personnes externes

---

### 1.2 CTA absent / invisible / confus

**Impact:** 🔴 **Critique**

Pas de bouton visible above the fold, ou CTA texte ambigu ("Cliquez ici" vs "Démarrer mon audit gratuit").

**Vérification:**
- [ ] CTA visible et clickable sur mobile
- [ ] CTA principal unique et dominant (contraste couleur)
- [ ] Texte CTA précise action + bénéfice ("Obtenir mon plan d'action gratuit" pas "Submit")
- [ ] CTA répété toutes les 300-400 mots

**Fix:**
- Augmenter taille/contraste du bouton
- Texte CTA spécifique : action + résultat
- Multiplier CTA stratégiquement (hero, section bénéfices, FAQ, footer)

---

### 1.3 Trop de distractions / liens sortants

**Impact:** 🔴 **Critique**

Trop de CTA secondaires, liens internes (blog, pricing d'autres services), ou navigation principal. Visiteur confus sur action prioritaire.

**Vérification:**
- [ ] Un CTA principal visible (ratio 1:1)
- [ ] Zéro liens vers d'autres pages except formulaire
- [ ] Navigation minimale ou cachée (offcanvas)
- [ ] Social icons en footer uniquement

**Fix:**
- Supprimer navigation standard, garder logo (non-cliquable ou vers anchor hero)
- Éliminer tous liens internes, CTA secondaires
- Cacher formulaires ou CTA alternatives jusqu'à section objections

---

### 1.4 Pas de social proof

**Impact:** 🟡 **Modéré**

Zéro témoignage, avis, logo client, ou chiffre social. Visiteur ne sait pas si d'autres ont converti.

**Vérification:**
- [ ] Témoignage spécifique + photo (ou vidéo) visible above the fold ou près du CTA
- [ ] Au minimum 3 avis texte avec photo + étoiles
- [ ] Chiffre social si disponible ("500+ clients" pas juste "beaucoup")
- [ ] Hiérarchie prouvée : video > texte+photo > étoiles > logos

**Fix:**
- Collecter 5-10 témoignages clients (bref, spécifique, avec métier)
- Ajouter photos LinkedIn ou testimonials vidéo (boost de 15-25% conversion)
- Placer près du CTA principal, pas seulement en bas de page

---

### 1.5 Mauvaise hiérarchie visuelle

**Impact:** 🟡 **Modéré**

Éléments importants ont même poids que détails. Visiteur ne sait pas où regarder. Tailles, couleurs, espacements incohérents.

**Vérification:**
- [ ] Headline > Subtitle > Body copy (tailles décroissantes)
- [ ] CTA principal bcp plus visible que boutons secondaires
- [ ] Images/vidéos placées côté CTA (droite souvent)
- [ ] Whitespace autour éléments critiques

**Fix:**
- Aumentar headline à 48-64px minimum
- Contraste CTA 120+ WCAG (bleu vif / orange sur fond clair)
- Reduce taille body copy à 16-18px (lisibilité mobile)

---

### 1.6 Pas de réponse aux objections

**Impact:** 🟡 **Modéré**

Visiteur a doutes (prix, complexité, commitment) et page n'adresse rien. Abandon près du CTA.

**Vérification:**
- [ ] Section FAQ avec top 5-7 objections
- [ ] Risk reversal visible (garant, essai 30j, remboursement)
- [ ] Timeline clair ("résultats en X jours")
- [ ] Comparaison vs alternative (implicite ou explicite)

**Fix:**
- Ajouter FAQ section avec schéma accordéon
- Mettre garantie/essai gratuit sous CTA
- Ajouter section "Pourquoi maintenant" + urgence douce

---

### 1.7 Mobile non optimisé

**Impact:** 🔴 **Critique**

Desktop parfait, mobile brisé : texte minuscule, CTA non-cliquable, image écrasée, formulaire insoutenable.

**Vérification:**
- [ ] CTA cliquable sur mobile (> 44x44px), visible above fold
- [ ] Texte ≥ 16px mobile, headings 28-36px
- [ ] Stack vertical (pas colonnes multiples)
- [ ] Formulaire max 3-5 champs, labels clairs
- [ ] Tester sur Chrome mobile + Safari iOS

**Fix:**
- Réduire formulaire mobile (max 3 champs, cacher optionnels)
- Stack 100% largeur, padding 16px sides
- Agrandir CTA à 48-56px height
- Test sur vrai devices (pas juste DevTools)

---

### 1.8 Incohérence ad → landing page (scent trail brisé)

**Impact:** 🟡 **Modéré**

Annonce promise X, page affiche Y. Visiteur confus, abandon immédiat. Couleurs, headline, tonalité différentes.

**Vérification:**
- [ ] Headline LP = (ou reprend) headline ad
- [ ] Couleurs primaires ad = LP hero
- [ ] Tonalité, audience cible identiques
- [ ] Image/vidéo hero continue la promesse ad
- [ ] Offre = offre (pas changement de prix/format)

**Fix:**
- Template LP reprend design ad : couleurs, typo, copy style
- Tester multiples ad copy → dedicated LP per variation
- Quality Score de l'ad impacte historiquement CTR LP

---

### 1.9 Above the fold mal exploité

**Impact:** 🔴 **Critique**

Hero section faible : pas d'image, texte confus, CTA absent, ou blanc excessif. Pire : auto-scroll qui cache le CTA.

**Vérification:**
- [ ] Image/vidéo héroïque impactante et pertinente
- [ ] Headline + subtitle claire en 2 lignes max mobile
- [ ] CTA principal en place, contrasté
- [ ] Bandeau réassurance (3-5 éléments) ou directement trust signals
- [ ] Zéro auto-play vidéo, zéro pop-up

**Fix:**
- Ajouter image hero spécifique au produit (pas generic stock)
- Simplifier headline à une seule promesse
- Déplacer CTA en bas de hero pour click (pas besoin de scroll pour action)

---

### 1.10 Temps de chargement > 3 secondes

**Impact:** 🟡 **Modéré**

Chaque 100ms ajoute = -1% conversion. 3s+ = abandon critique, surtout mobile.

**Vérification:**
- [ ] PageSpeed Insights > 85 sur mobile
- [ ] LCP (Largest Contentful Paint) < 2.5s
- [ ] CLS (Cumulative Layout Shift) < 0.1 (pas de sauts éléments)
- [ ] FCP (First Contentful Paint) < 1.8s

**Fix:**
- Compresser images (WebP, lazy loading)
- Minify JS/CSS, defer non-critical JS
- Utiliser CDN pour assets statiques
- Limiter external scripts (analytics, ads)

---

### 1.11 Absence d'urgence ou de rareté

**Impact:** 🟡 **Modéré**

Visiteur pense "je vais revenir plus tard" → jamais revient. Manque de trigger de scarcité ou urgence.

**Vérification:**
- [ ] Scarcité implicite ou explicite : places limitées, deadline, stock
- [ ] Urgence douce visible : "Audit gratuit valide cette semaine" ou "Démarrer avant..."
- [ ] Countdown timer (si vraiment limité) ou badge "Limité"
- [ ] Copy : "avant" trigger, pas "après"

**Fix:**
- Ajouter text-based urgency sous CTA ("Valable ce mois" ou "2 places restantes")
- Timer countdown si offre réellement limitée (sinon crédibilité baisse)
- Email follow-up : "Vous aviez visité notre page..."

---

## 2. PRINCIPES CRO FONDAMENTAUX

### 2.1 Ratio d'attention 1:1

**Principe:** Un objectif de conversion = un CTA dominant visible.

**Explicitation:**
- Visiteur devrait avoir 1 chemin clair vers conversion (hero CTA)
- Tous autres éléments soutiennent ce chemin, ne le distraient pas
- Multi-CTA = confusion cognitif = baisse conversion

**Implémentation:**
- Primary CTA (couleur dominante, > 50px height)
- Secondary CTA (texte, liens d'ancre) uniquement à la fin (FAQ, social proof)
- Test A/B : single vs dual CTA buttons = single gagne souvent +15-30%

---

### 2.2 Test des 5 secondes

**Principe:** Visiteur doit comprendre votre offre en < 5 secondes.

**Explicitation:**
- Ouvrir page, timer 5 sec, fermer. Visiteur peut-il dire : "C'est quoi l'offre? Pour qui? Pourquoi j'en ai besoin?"
- Si non, page a fail

**Implémentation:**
- Tester avec 5-10 utilisateurs externes (pas équipe)
- Headline doit être "hooks" : spécific pain point + solution
- Ajouter sub-copy directement sous headline qui précise le "pour qui"

---

### 2.3 Scent Trail (Cohérence ad → page → conversion)

**Principe:** Chaque touchpoint (ad, email, page) reprend cohérente les mêmes signaux visuels et messaging.

**Explicitation:**
- Annonce Google/Facebook X → LP doit affirmer X (pas Y)
- Copy, couleurs, imagery, tonalité = continuité
- Rupture de "scent" = visiteur pense être arrivé à la mauvaise page

**Implémentation:**
- Créer 3-5 variantes ad → créer 3-5 variantes LP (landing page dédiée par ad)
- Headline LP reprend mot-clé de l'ad
- Couleur CTA = couleur ad
- Test multi-ad, multi-lp pour identifier meilleure combo

---

### 2.4 Hiérarchie de la preuve sociale

**Principe:** Différentes preuves ont différents poids. Hiérarchie prouvée par tests A/B.

**Ordre de force (descendant):**
1. Témoignage vidéo (authentique, face visible) → +25-40% lift
2. Témoignage texte + photo + logo client
3. Avis étoilés (Google, Trustpilot, TrustRadius)
4. Logos clients (cohort recognition)
5. Chiffres sociaux ("10,000+ utilisateurs")

**Implémentation:**
- Priorité : vidéo testimonials (même 30-60 sec)
- Si vidéo trop coûteux : photo LinkedIn + quote + role
- Mettre une preuve social "haute valeur" immédiatement après headline (section ou sidebar)
- Éviter mélanger dans un carousel, mettre en 2-3 éléments distincts

---

### 2.5 Les 5 types de friction

**Principe:** Friction = barrière à conversion. Chaque type demande fix différent.

**Types:**

1. **Friction cognitive** : visiteur doit penser trop
   - Fix: Headline clair, navigation simple, pas trop de choix

2. **Friction émotionnelle** : doute, peur, incertitude
   - Fix: Social proof, testimonials, risk reversal (garantie), FAQs

3. **Friction d'interaction** : formulaire trop long, CTA difficile à cliquer
   - Fix: Reduce champs (min viable), mobile-friendly, CTA 44x44px+

4. **Friction visuelle** : design confus, trop d'éléments, hiérarchie inexistante
   - Fix: Whitespace, 1-2 couleurs primaire, hiérarchie taille/contrast

5. **Friction technique** : page lente, ne charge pas, formulaire brisé
   - Fix: PageSpeed > 85, test multi-device, test formulaire live

**Implémentation:**
- Audit page : identifier 1-2 frictions principales
- Priorité fix : cognitif + émotionnel d'abord
- A/B tester chaque fix

---

### 2.6 F-pattern et Z-pattern de lecture

**Principe:** Œil suit naturally un chemin en forme de F ou Z. Design doit aligner éléments clés sur ce chemin.

**F-pattern (contenu lourd):**
```
Headline ————————————
Sub       ————————————

Body      ————
Body      ————
Body      ————
```
- Vertical gauche, puis horizontal bas
- Adapté pour pages texte/blog
- Align headline, sous-titre à gauche; CTA en bas left

**Z-pattern (minimal):**
```
Logo ——————— CTA
     \
      \
Body  ————— Image/CTA
```
- Diagonal top-left → bottom-right
- Adapté pour hero pages simples
- Image à droite, CTA droite

**Implémentation:**
- Landing pages : Z-pattern (simple, conversion-focused)
- Blogs/long-form : F-pattern
- Place CTA à intersection "Z" (bas-right zone)

---

### 2.7 Paradoxe du choix (Schwartz)

**Principe:** Trop de choix = paralysie = no choice. 3-7 options = optimal.

**Explicitation:**
- 2 options (on/off) : pas assez, visiteur hésitant
- 3-7 options : sweet spot, visiteur engage
- 10+ options : paralysie, abandon, très basse conversion

**Implémentation:**
- Max 3-5 pricing tiers (pas 10 plans)
- Max 6 bénéfices clés (pas 15 features)
- Max 3 CTA distinct strategies (hero, FAQ, final)
- Test : 3 plan vs 5 plan = généralement 5 plan gagne (choix)

---

### 2.8 Ancrage de prix

**Principe:** Premier prix vu = anchor. Suivants se comparent à lui. Anchor haut = autres semblent meilleur marché.

**Explicitation:**
- Montrer plan premium en premier → plan "pro" semble reasonable
- Montrer plan cheap en premier → tout semble trop cher

**Implémentation:**
- Afficher prix du haut en premier (premium/pro)
- Highlight la plan "recommandée" (pas la plus chère, ni la moins)
- Si prix unique : montrer "prix normal" barré + prix promos
- Comparer vs alternative coûteuse ("vs hiring FT employee = X par an")

---

### 2.9 Effet de dotation (Endowment Effect)

**Principe:** Visiteur valorise plus ce qu'il possède déjà (essai gratuit, accès temporaire). Dès qu'il a essai = + probable conversion.

**Explicitation:**
- 7 jours accès gratuit = visiteur se sent possesseur → plus probable d'acheter
- Vs. "acheter en aveugle" = friction haute

**Implémentation:**
- Offrir free trial (7-14 jours selon product weight)
- Orientation email post-signup : montrer valeur générée déjà
- Risk reversal : "Si pas satisfait en 30j, 100% remboursé"

---

### 2.10 Biais de confirmation

**Principe:** Visiteur cherche preuves qui confirment son choix, pas preuves qui le contredisent.

**Explicitation:**
- Visiteur déjà "vendu" mentalement cherche justification
- Montrer preuves qui confirment son instinct = conversion
- Montrer objections head-on = activation of bias contre-productif

**Implémentation:**
- FAQ déguisée : "Pourquoi 1000+ entreprises choisissent notre solution"
- Testimonials : chercher celui qui reprend le pain point visiteur exprimé dans ad
- Pas de "mais attendez, considérez ceci" (contradiction active)

---

### 2.11 Réciprocité (donner avant de demander)

**Principe:** Donner valeur gratuite upfront → visiteur se sent obligation de rendre (conversion). Inversement, demander input d'abord = friction.

**Explicitation:**
- Gratuit guide → email + conversion
- Email directement → très basse conversion
- Free trial → + probable payer que demo seul

**Implémentation:**
- Lead magnet (guide, checklist, template) = value offer AVANT formulaire
- Post-formulaire : accès immédiat au lead magnet
- Multi-step : step 1 = offer value, step 2 = request contact
- Email sequence post-signup : donner tips, case studies AVANT sales pitch

---

## 3. SECTIONS D'UNE PAGE — BEST PRACTICES CRO

### 3.1 Hero / Buy Box

**CRO Rule #1 : Above-the-fold critical zone**

**Must-haves (non-negotiables):**
- [ ] Headline visible (28-48px mobile, 48-72px desktop), conveying key benefit
- [ ] Sub-headline or subtitle clarifying "for whom" or "what happens next"
- [ ] Primary CTA visible, clickable (44x44px+ mobile, 48x56px desktop)
- [ ] Hero image/video aligned right (Z-pattern), product-specific
- [ ] No scroll needed to see CTA (or minimal scroll)

**Réassurance immédiate (trust signals):**
- [ ] Optionnel : 1 small testimonial quote / avatar avec 5 étoiles
- [ ] Optionnel : "1,000+ companies trust us" ou chiffre pertinent
- [ ] Pas de pop-ups, no auto-play video (mute × close button)

**CRO Rules d'optimisation :**
- Tester headline variations : "Problem Focused" vs "Solution Focused" vs "Outcome Focused"
- CTA button : contrasté 120+  WCAG (ex: #FF6B35 sur blanc)
- Test 2-column hero vs 1-column centered (1-col souvent meilleur mobile)

---

### 3.2 Bandeau de réassurance

**CRO Rule : Trust signals doivent être pertinents et spécifiques, max 3-6 éléments**

**Format standard :**
```
[Icon] Headline ≤ 4 words
[Icon] Headline ≤ 4 words
[Icon] Headline ≤ 4 words
...max 6
```

**Positionnement :**
- Immédiatement après hero CTA
- Ou en bas du hero (above the fold mobile)
- Ou avant section bénéfices

**Éléments pertinents (exemples) :**
- 🏆 "Award-winning" (si relevant, ex: G2, Capterra)
- 🔒 "GDPR Compliant" ou "SOC 2 Certified" (si B2B/data)
- ⚡ "5 min setup" ou "No CC required"
- 👥 "10K+ active users" (spécifique, vérifiable)
- 💰 "Money-back guarantee"
- 📈 "Used by [Cohort]" (ex: "500+ agencies")

**CRO Rules d'optimisation :**
- Icones : style consistent, couleur brand
- Texte : sans sérif, 14-16px, centered ou left-aligned
- A/B test : présence vs absence (généralement +5-15% si bien ciblé)
- Tester position : après hero vs après bénéfices

---

### 3.3 Section Bénéfices

**CRO Rule : Toujours vendre bénéfices, jamais features. Max 6 bénéfices par section.**

**Format standard :**
```
[Icon] Bénéfice headline (1 ligne)
Description (2-3 lignes, outcome-focused)
```

**Bénéfice vs Feature :**
- Feature : "Intégration Stripe" → Bénéfice : "Encaissez paiements clients en < 30 sec"
- Feature : "AI-powered" → Bénéfice : "Économisez 10 heures/semaine sur tâches répétitives"
- Feature : "Mobile app" → Bénéfice : "Gérez votre business n'importe où"

**Structure :**
- 3-6 bénéfices (pas plus, paradoxe du choix)
- 1 icone par bénéfice (spécifique, brand color)
- Headline 18-24px, strong/bold
- Description 14-16px, contraste réduit (gris-700)
- Stack vertical sur mobile, 2-3 colonnes sur desktop

**CRO Rules d'optimisation :**
- Tester ordre : most impactful benefit en premier vs. "engagement hook" en premier
- Tester headline length : 4 mots vs 8 mots
- Test format : icon-left vs. icon-top (icon-top souvent meilleur mobile)
- Video/GIF > statique icon

---

### 3.4 Social Proof

**CRO Rule : Spécificité > quantité. Hiérarchie prouvée par test.**

**Hiérarchie de force (descendant) :**

1. **Testimonial vidéo** (30-60sec, face visible)
   - Gain: +25-40% conversion lift
   - Format : job title, company, quote, face
   - Placement : après headline ou après objection-heavy section

2. **Testimonial texte + photo + logo**
   - Gain: +15-25% conversion lift
   - Format : 2-3 lignes quote, photo 60x60px, job title
   - Carousel ou single rotation

3. **Avis étoilés + avatar**
   - Gain: +10-15% conversion lift
   - Format : 5-stars, 1-2 lignes, source (Google, Capterra, etc.)
   - Placement : carousel sous prix ou près CTA

4. **Logos clients / Cohort Recognition**
   - Gain: +5-10% conversion lift
   - Format : 40x40px grayscale logos, 8-12 logos max
   - Placement : bandeau section réassurance ou bénéfices

5. **Chiffres sociaux**
   - Gain: +5% conversion lift
   - Format : "10,000+ customers in 50+ countries" (spécifique)
   - Placement : fin page ou FAQ

**CRO Rules d'optimisation :**
- Tester placement : après headline vs. près CTA vs. fin page
- Tester nombre : 1 big testimonial vs. 3 small vs. carousel
- Tester type : vidéo vs. photo+text (vidéo gagne souvent)
- Chercher testimonials qui reprennent pain point spécifique du segment

---

### 3.5 Section Problème / Agitation

**CRO Rule : Agiter suffisamment pour créer urgence, pas assez pour créer anxiété.**

**Techniques d'agitation (choisir 1-2) :**

1. **Statistics** : "72% de X expérience Y" (si sourçable, précis)
2. **Stories** : mini-case study "Avant, Jean était coincé avec X... Après..."
3. **Scenarios** : "Imagine: sans solution, dans 6 mois, tu auras Y conséquence"

**Formule agitation efficace :**
```
Problème specifique + Conséquence négative + Emotion
"Les freelances dépensent 15h/mois sur invoicing
(conséquence: perte $3k/an)
ce qui crée stress et perte focus sur clients"
```

**CRO Rules d'optimisation :**
- Pas trop agiter : anxiety → abandon. Ratio optimal = 40% agitation, 60% solution
- Tester agitation légère vs. strong : généralement modéré gagne
- Placement : avant section solution (problème → solution flow)
- Tester texte vs. image vs. stat box : test A/B placement

---

### 3.6 Section Solution

**CRO Rule : Bridge problème → produit. Communiquer "unique mechanism".**

**Structure :**
```
Problème spécifique (1-2 lignes)
↓
Unique Mechanism (comment tu résous ≠ compétition)
↓
Résultat client (outcome spécifique)
```

**Unique Mechanism = "why different":**
- Pas : "We're the best"
- Oui : "Our AI analyzes buyer signals in real-time, giving you 48h advance warning of churn"

**Format :**
- Headline 24-36px : reprend douleur + solution
- Description : 3-4 lignes expliquant mechanism
- Image/diagram : illustrant le processus (3 étapes max)
- CTA secondaire : "See how it works" ou "Watch demo"

**CRO Rules d'optimisation :**
- Tester mechanism visibility : explicit vs. implicit (implicite souvent gagne si produit complex)
- Tester copy length : 50 words vs. 150 words (court gagne si audience impatient)
- Vidéo demo 1-2 min : très efficace pour complex products

---

### 3.7 FAQ / Objections

**CRO Rule : Top 5-7 objections déguisées en FAQ. Schema.org markup. Accordéon mobile-friendly.**

**Sourcing objections :**
- Analyser support tickets (quels questions reviennent?)
- Analyser ad comments (quels critiques?)
- Analyser GA drop-off (où quitten les visiteurs?)
- Interviews clients : "Pourquoi tu as hésité avant d'acheter?"

**Format standard :**
```
Q: Objection déguisée en question
A: 2-3 lignes max, directe, preuve (si applicable)

Q: Can I cancel anytime?
A: Yes, cancel anytime with 1 click.
No contracts, no support calls needed.
```

**Accordéon implémentation (mobile-friendly) :**
- Max 7 FAQ items (pas plus)
- Click pour expand, collapse autres
- All text visible on mobile (pas besoin scroll après expand)

**Schema.org FAQPage markup** (SEO bonus) :
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Can I cancel anytime?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, cancel anytime with 1 click..."
      }
    }
  ]
}
```

**CRO Rules d'optimisation :**
- Tester placement : après social proof vs. fin page (fin page généralement)
- Tester format : accordéon vs. expanded (accordéon mobile)
- Tester nombre : 5 vs. 7 vs. 10 (7 optimal)
- Ajouter "Not answered? Contact us" CTA en bas

---

### 3.8 Pricing

**CRO Rule : Ancrage prix haut, highlight plan recommandé (pas plus cher), eliminate price friction.**

**Ancrage technique :**
- Afficher plan premium en premier
- Highlight plan "Pro" ou "Popular" (middle option, généralement recommandé)
- Texte "Recommandé" ou "Most Popular" sur plan recommandé

**Structure de pricing :**
- Max 3-5 plans (paradoxe du choix)
- Comparison table : features par plan (simple, 4-6 features max)
- Highlight différences : ce qui change entre plans

**Éliminer friction prix :**
- Afficher prix annuel + mensuel switcher (annual = discount visible)
- Ajouter paiement fractionné : "X/mois ou payer semestrement" (-10% discount)
- Ajouter essai gratuit : "7 jours essai, pas CC requis"
- Ajouter garantie : "30j remboursé 100%" ou "Money-back guarantee"

**Format visuel :**
```
[Pro Plan]      [Popular: Pro Plan]      [Enterprise]
$29/mo          $79/mo                   Custom
Feature 1       Feature 1 ✓              Feature 1 ✓
Feature 2       Feature 2 ✓              Feature 2 ✓
---             Feature 3 ✓              Feature 3 ✓
[CTA]           [CTA - Bold]             [CTA - Contact]
```

**CRO Rules d'optimisation :**
- Tester prix anchor : High → Middle vs. Middle → Low
- Tester plan highlight : Middle vs. Top vs. None (middle gagne)
- Tester "Popular" label vs. aucun label
- Tester annual discount : 10% vs. 20% vs. 30% (20% optimal)

---

### 3.9 CTA Final

**CRO Rule : Résumé valeur + risk reversal + urgence douce = conversion final push.**

**Structure :**
```
Headline : Résumé bénéfice clé (1 ligne)
Description : Valeur clé, délivérables, timeline
[Risk Reversal] : Garantie, essai gratuit, remboursement
[Urgence douce] : "Offer valid until [date]" ou "Only X spots left"
[CTA Final - prominent]
```

**Exemple :**
```
Everything Included + Zero Risk

You get:
- Audit personnalisé (valeur $2k)
- 3 sessions coaching (valeur $1.5k)
- Access à templates (valeur $500)

100% Money-Back Guarantee
If you're not happy in 30 days, full refund. No questions.

Offer valid until Friday
[CTA: Claim Your Audit Now]
```

**CRO Rules d'optimisation :**
- Tester sans vs. avec risk reversal (risque reversal gagne ~20-30%)
- Tester urgence : aucune vs. douce (douce gagne ~10-15%)
- Tester CTA copy : "Claim" vs. "Get" vs. "Start" (test avec audience)
- Tester summary value : brief vs. détaillé (détaillé si audience hésitant)

---

### 3.10 Formulaire

**CRO Rule : Min viable champs. Labels au-dessus. Multi-step = progression visuelle claire.**

**Règle des champs :**
- Objectif : conversion rapide → max 3 champs (name, email, goal)
- Objectif : lead qualification → max 5-7 champs
- Ajouter champs optionnels post-formulaire (step 2)

**Design d'input :**
- [ ] Labels AU-DESSUS input (pas placeholder-only)
- [ ] Input largeur 100% sur mobile (sauf name = 50% col)
- [ ] Focus state visible (border color, shadow, outline)
- [ ] Réel input type : email, tel, date (aide mobile keyboards)
- [ ] Placeholder grey, dimmed (label noir, bold)

**Multi-step (si > 5 champs) :**
- Progression visuelle (step 1/3 indicator, progress bar)
- Validation immédiate par field (pas attendre submit final)
- Sauvegarder auto chaque step (si disconnect = continuer)
- Step 2 = optionnels + message "Presqu'arrivé"

**Message de succès :**
- Pas juste "Success" message
- Actionable : "Check your inbox for your audit report. Didn't get it? Check spam."
- Link ou button : "Explore your results" ou "Return to dashboard"
- Email automatique confirming + next steps

**CRO Rules d'optimisation :**
- Tester 3 champs vs. 5 champs : 3 généralement gagne (+25-40%)
- Tester single-step vs. multi-step (multi gagne si > 5 champs)
- Tester obligatoire vs. optional fields : moins obligatoires gagnent
- Tester email confirmation vs. directement accès

---

## 4. BENCHMARKS CRO PAR INDUSTRIE

| Industrie | Taux conversion moyen | Bon | Excellent | Bounce rate moyen |
|---|---|---|---|---|
| **E-commerce général** | 2.0-2.5% | 3-4% | 5%+ | 45-50% |
| **E-commerce DTC** | 1.5-2.5% | 3-5% | 6%+ | 40-45% |
| **SaaS (Free Trial)** | 3-5% | 7-10% | 15%+ | 35-45% |
| **SaaS (Enterprise)** | 0.5-2% | 3-5% | 8%+ | 50-60% |
| **Lead Gen B2B** | 3-7% | 10-15% | 20%+ | 40-50% |
| **Lead Gen B2C** | 1-3% | 5-8% | 12%+ | 50-60% |
| **Santé / Wellness** | 1-2% | 3-5% | 8%+ | 55-65% |
| **Finance** | 0.5-1% | 2-3% | 5%+ | 60-70% |
| **Education** | 2-3% | 5-7% | 10%+ | 50-55% |
| **Food & Beverage** | 0.5-1.5% | 2-4% | 6%+ | 55-65% |

**Notes :**
- SaaS gratuit = souvent conversion plus haute (lower barrier)
- B2B Enterprise = conversion basse (long consideration, multi-stakeholder)
- Bounce rate haut = traffic quality problème ou traffic non-qualified
- Références : Unbounce, Invespcro, CXL data

---

## 5. CHECKLIST RAPIDE PRÉ-LIVRAISON

**Avant livrer any LP, valider ces 20 points (yes/no):**

- [ ] **Headline visible above-fold**, spécifique à segment cible
- [ ] **CTA principal visible above-fold mobile** (44x44px+, cliquable)
- [ ] **CTA texte spécifique** : action + bénéfice ("Get free audit" pas "Submit")
- [ ] **Ratio 1:1 : un CTA principal** dominant, autres CTA secondaire
- [ ] **Social proof présent + spécifique** : témoignage ou logo ou chiffre
- [ ] **Mobile optimisé** : texte ≥16px, stack vertical, CTA >= 48px height
- [ ] **Scent trail cohérent** : ad copy = LP headline, même couleurs/tonalité
- [ ] **Formulaire ≤ 5 champs max** (3 idéal), labels au-dessus input
- [ ] **Hiérarchie visuelle claire** : headline > subtitle > body, contraste button 120+ WCAG
- [ ] **Pas de distractions** : zéro navigation standard, zéro liens externe (sauf footer)
- [ ] **FAQ ou objections adressées** : top 5-7 objections présentes
- [ ] **Risk reversal présent** : garantie, essai gratuit, ou remboursement
- [ ] **Urgence ou rareté soft** : "offer valid until", "X spots left", ou similar
- [ ] **Image hero spécifique + impactante** : pas stock generic (ou vidéo)
- [ ] **Temps chargement < 3 secondes** : PageSpeed > 85 (mobile)
- [ ] **Zéro auto-play vidéo** : si vidéo, mute + close button visible
- [ ] **Réassurance bandeau** (3-6 éléments max) : pertinent au segment
- [ ] **Bénéfices section** : 3-6 bénéfices, format icon + headline + desc
- [ ] **CTA répété** : minimum 2x (hero + fin page)
- [ ] **Formulaire testé** : soumission réelle + vérifier email reçu

**Score:** 19-20 = Ready, 17-18 = Minor fixes, <17 = Rework.

---

## NOTES D'IMPLÉMENTATION

**Processus recommandé par section :**

1. **Hero** : Fixer headline (problem/benefit focused), ajouter CTA, image/video
2. **Réassurance** : 3-5 trust signals pertinents
3. **Bénéfices** : 4-6 bénéfices max, icon + headline + 2-3 lignes desc
4. **Social proof** : Collecte testimonials (objectif: 5-10 clients pour vidéo/photo)
5. **Problem + Solution** : Agitation modérée + unique mechanism
6. **Pricing** (si applicable) : Ancrage, highlight plan, friction removal
7. **FAQ** : Top 5-7 objections sourçées de support/ads/interviews
8. **CTA Final** : Résumé valeur + risk reversal + soft urgency
9. **Formulaire** : Min viable, labels clairs, validation immédiate
10. **Test & Optimize** : A/B test headline, CTA, social proof placement, urgency

**Priorités A/B test (ordre impact):**
1. Headlines variation (problem vs. solution vs. outcome)
2. Social proof presence + type (vidéo vs. photo vs. text)
3. CTA text (action-oriented vs. benefit-oriented)
4. Pricing anchor (high-first vs. middle-first)
5. Urgency presence (aucune vs. soft deadline)
6. Risk reversal presence (avec vs. sans)
7. Formulaire champs (3 vs. 5)
8. Image/video hero (spécific vs. generic)

**Red flags à corriger immédiatement :**
- CTA non visible mobile = instant fix
- Formulaire > 7 champs = reduce avant test
- Page charge > 4 sec = optimize images
- Headline générique ("Best solution") = rewrite
- Zéro social proof = ajouter même 1 testimonial
- Navigation/liens multiples = simplify
