# Design System Reference — Growth Site Generator

## Contexte & Philosophie

Le **Design System GSG** combine deux piliers fondamentaux :

1. **Anti-AI-Slop** : Rejet systématique du générique, du templat, du "vu mille fois"
2. **CRO-Centric** : Chaque décision design sert la conversion et l'intention utilisateur

Ce document est une Bible de Design pour l'IA. Elle doit générer des sites DISTINCTIFS, INTENTIONNELS, et CONVERTISSANTS — jamais de sites "template" qui pourraient avoir été générés par n'importe quel outil.

---

## 1. PHILOSOPHIE ANTI-AI-SLOP

### Qu'est-ce que le "AI Slop" en design ?

Le AI slop est le pattern générique, inoffensif, et mémorable par son absence : des sites générés sans âme, qui semblent flottants dans un non-univers design. Caractéristiques :

- **Compositions symétriques parfaites** : tout centré, tout équilibré, manque de tension
- **Gradients dégradés** (au sens propre) : bleu → violet sur blanc, aka "le gradient de startup"
- **Icons génériques** : des silhouettes plates, inexpressives, du stock SVG standardisé
- **Copy en anglais ou français générique** : "bienvenue", "découvrez", "solutions innovantes"
- **Grilles uniformes** : cartes de même taille, espaces identiques, zéro surprise
- **Animations basiques** : fade-in au scroll, slide in depuis le bas, rien qui fait penser
- **Palette plate** : 3 couleurs max, pas de nuance, pas d'acidité
- **Images de stock homogénéisées** : femme souriante devant laptop, mains qui se serrent, équipe diversifiée en réunion

### Les 7 Péchés Mortels du Design AI-Généré

#### 1. **Fonts Interdites (Blacklist)**

| Font | Raison | Remplacement |
|------|--------|--------------|
| **Inter** | Neutre à l'extrême, tout le web en 2023-2024 | Clash Display, Satoshi, General Sans |
| **Roboto** | Material Design legacy, Android par défaut | Outfit, Manrope, Plus Jakarta Sans |
| **Arial/Helvetica** | Années 2000, Windows defaults | Cabinet Grotesk, Syne |
| **Open Sans** | Google Font "safe", utilisée par 40% du web | Satoshi, DM Sans |
| **Lato** | Overly friendly, dilue la personnalité | Cormorant (serif), Unbounded (display) |
| **Montserrat** | Géométrique génériquement | Clash Display, Fraunces |
| **system-ui** | Zéro personnalité, zéro effort | Toute font web custom |

**Règle d'Or** : Si une font apparaît dans "Google Fonts Popular", elle est probablement trop utilisée. Préférer les fondries spécialisées (TypeTogether, Dalton Maag, David Jonathan Ross, etc.).

#### 2. **Patterns de Layout Interdits**

- ❌ **Hero symétrique** : texte centré, image centrée, tout aligned à la perfection
  - ✅ Remplacer par : asymétrie intentionnelle, texte à gauche + image décalée, overlap, angle

- ❌ **Grille de cartes 3×3** : même hauteur, même largeur, espace régulier
  - ✅ Remplacer par : grille asymétrique, cartes de tailles variables, masonry, alternance dense/airy

- ❌ **Section CTA centrée** : "Êtes-vous prêt?" avec bouton centré
  - ✅ Remplacer par : CTA positionné stratégiquement, peut être hors-écran, flotant, ou intégré dans un flux

- ❌ **Bootstrap Default** : container gris clair, card blanche avec ombre légère, spacing régulier
  - ✅ Remplacer par : custom spacing logic, pas d'ombre (ou shadows audacieuses), texture et depth

- ❌ **Grille 100% symétrique avec padding identique** : "spacieux" mais figé
  - ✅ Remplacer par : espaces variables, sections full-bleed alternées, micro-rythmes

#### 3. **Gradients Interdits**

- ❌ `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` — le gradient violet/bleu de 2019
- ❌ `radial-gradient(circle, #FF6B6B, #FFE66D)` — trop "fun", pas de sophistication
- ❌ Gradients trop lisses, sans tension : `#FFF → #F0F0F0`

**À la place** :
- Gradients complexes : 3-4 stops avec angles asymétriques
- Mesh gradients : `radial-gradient()` imbriqué pour créer du mouvement
- Gradients avec texture superposée (voir section Textures)
- Gradients stops non-linéaires : 0%, 5%, 85%, 100% (crée du drama)

#### 4. **Copy Patterns Interdits**

En français, ces phrases condemn un site à l'oubli :

- ❌ "Bienvenue sur [Brand]"
- ❌ "Découvrez nos solutions innovantes"
- ❌ "Nous sommes passionnés par..."
- ❌ "Prêt à transformer votre [domaine]?"
- ❌ "Solutions de [sector] pour les [audience]"
- ❌ "Rejoignez les milliers de clients satisfaits"
- ❌ "L'avenir est maintenant"
- ❌ "Créé avec amour par notre équipe"

**La Règle** : Chaque copie doit être **SPÉCIFIQUE au client**. Jamais de template copy. Préférer :
- Chiffres concrets au lieu de promesses vagues
- Voice distinctif : plutôt brut, plutôt poétique, plutôt humoristique — mais DISTINCTIF
- Bénéfice direct au lieu de feature énumération

### L'Antidote : INTENTIONNALITÉ

Chaque élément de design doit répondre à une question :
- **Pourquoi cette couleur ici ?** (pas "parce que c'est joli", mais "pour attirer l'attention" ou "pour créer du repos")
- **Pourquoi cette font ?** (sa personnalité doit matcher le tone de la marque)
- **Pourquoi cet espace ?** (pour respirer, ou pour créer de la tension?)
- **Pourquoi cette animation ?** (pour guider l'attention ou créer du delight?)

Si tu ne peux pas répondre : **supprime-le**.

---

## 2. TYPOGRAPHIE

La typographie est l'armature invisible du design. Elle porte la voix de la marque.

### 2.1 Catégories de Fonts Recommandées

#### **SERIF** (tradition, luxe, credibilité)

1. **Playfair Display** — Élégant, haut contraste, parfait pour h1/hero
2. **DM Serif Display** — Moderne serif, moins posh que Playfair, plus accessible
3. **Fraunces** — Serif variable, joueur, peut être très lourd ou très léger
4. **Libre Baskerville** — Classique, lisible en corps texte, très français
5. **Cormorant** — Ultra-élégant, très haut contraste, luxe pur
6. **Recoleta** — Contemporain serif, béton + fine, tendance 2024
7. **Caslon** — Historique serif, web pour les marques heritage
8. **Lora** — Serif + chaleur, lisible en body, Google Fonts mais pas generic

#### **SANS-SERIF GÉOMÉTRIQUE & MODERNE** (tech, SaaS, épuré)

1. **Clash Display** — Géométrique audacieux, personality très marquée
2. **Satoshi** — Roundness douce, tech-friendly, très lisible
3. **General Sans** — Minimaliste, utilité pure, design suisse
4. **Cabinet Grotesk** — Historique grotesk, nerveux, distinctif
5. **Outfit** — Géométrique soft, tech+humaniste
6. **Syne** — Caractère fort, playful sans être childish
7. **Plus Jakarta Sans** — Géométrique chaud, accent indonésien
8. **Manrope** — Soft geometric, très lisible, friendly
9. **Maude** — Geometric bold, très distinctif
10. **Neue Montreal** — Grotesk montréalais, minimaliste + personality

#### **MONOSPACE** (code, technical credibility, éditorial)

1. **Space Mono** — Historique monospace, personality distincte
2. **JetBrains Mono** — Professionnel, très lisible en petit
3. **Fira Code** — Tech font avec ligatures, crédibilité dev
4. **IBM Plex Mono** — Entreprise grade, excellent accessibility
5. **DM Mono** — Designer's monospace, plus chaud que technique
6. **Courier Prime** — Typewriter vibes, vintage-tech blend

#### **DISPLAY & EXPERIMENTAL** (headlines, personality)

1. **Unbounded** — Variable font joueur, peut être très loose ou très tight
2. **Instrument Serif** — Serif moderne déstructuré, éditorial
3. **Bricolage Grotesque** — Organic grotesk, très personality
4. **Hanken Grotesk** — Géométrique warm, humaniste
5. **Arvo** — Serif slab, brutalist, très distinctive
6. **Soho Gothic** — Grotesk avec character, rétro-futuriste
7. **Rooney Sans** — Humaniste playful, branding fort

### 2.2 Stratégie de Pairing

**La Règle d'Or** : Contraste CLAIR entre display et body.

#### Pairings Éprouvés

```
Luxury E-commerce:
- H1/H2: Playfair Display (serif elegant)
- Body: Satoshi (sans-serif moderne)
→ Contraste: serif traditionnel + sans contemporain = sophistication

SaaS B2B:
- H1/H2: Clash Display (bold geometric)
- Body: General Sans (minimal sans)
→ Contraste: audacieux + épuré = confiance tech

Agence créative:
- H1/H2: Bricolage Grotesque (organic)
- Body: Plus Jakarta Sans (warm geometric)
→ Contraste: personality + accessibility

Fashion/Mode:
- H1/H2: Fraunces (serif variable)
- Body: Outfit (soft geometric)
→ Contraste: haute couture + contemporain

Food & Beverage:
- H1/H2: Unbounded (playful variable)
- Body: Manrope (soft sans)
→ Contraste: fun + lisible

Finance/Fintech:
- H1/H2: Cormorant (ultra elegant serif)
- Body: IBM Plex Sans (professional sans)
→ Contraste: tradition + neutre = trustworthy
```

**Anti-pairing** (à ÉVITER) :
- ❌ Deux fonts sans distincte (Inter + Open Sans = invisibilité)
- ❌ Deux fonts display (trop bruyant)
- ❌ Deux fonts serif (combat d'élégance)
- ❌ Font display + font serif body (lisibilité compromise)

### 2.3 Système d'Échelle Typographique

**Ratio multiplicateur** : 1.25 (golden ratio-like, sans être trop agressif)

```css
:root {
  /* FONT FAMILY */
  --font-display: 'Clash Display', sans-serif; /* H1, H2, labels branding */
  --font-body: 'Satoshi', sans-serif;          /* p, li, body copy */
  --font-mono: 'Space Mono', monospace;        /* code, technical */

  /* SCALE — rem values for fluid scaling */
  /* Base: 16px = 1rem */

  /* Display/Hero */
  --fs-h1: 3.5rem;    /* 56px — main hero headline */
  --fs-h2: 2.75rem;   /* 44px — section headlines */
  --fs-h3: 2.125rem;  /* 34px — sub-headlines */

  /* Body */
  --fs-body: 1rem;    /* 16px — default body copy */
  --fs-lead: 1.25rem; /* 20px — intro paragraph, emphasis */

  /* Small */
  --fs-small: 0.875rem;  /* 14px — secondary text, labels */
  --fs-caption: 0.75rem; /* 12px — captions, micro-copy */

  /* LINE HEIGHT */
  --lh-display: 1.1;   /* tight for h1/h2 */
  --lh-body: 1.6;      /* comfortable for reading */
  --lh-compact: 1.4;   /* labels, secondary */

  /* LETTER SPACING */
  --ls-display: -0.02em;   /* slightly negative for h1 */
  --ls-body: 0;
  --ls-caps: 0.08em;       /* if using text-transform: uppercase */
}

/* Mobile */
@media (max-width: 768px) {
  :root {
    --fs-h1: 2.25rem;    /* 36px */
    --fs-h2: 1.875rem;   /* 30px */
    --fs-h3: 1.5rem;     /* 24px */
    --fs-lead: 1.125rem; /* 18px */
  }
}

/* H1/H2 */
h1 {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  font-weight: 700;
}

h2 {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-display);
  font-weight: 600;
}

h3 {
  font-family: var(--font-body);
  font-size: var(--fs-h3);
  line-height: var(--lh-body);
  font-weight: 600;
}

/* Body copy */
p, li {
  font-family: var(--font-body);
  font-size: var(--fs-body);
  line-height: var(--lh-body);
}

/* Lead paragraph (intro) */
.lead {
  font-size: var(--fs-lead);
  line-height: var(--lh-body);
  font-weight: 500;
}

/* Small/secondary text */
small, .caption {
  font-size: var(--fs-small);
  line-height: var(--lh-compact);
  color: var(--color-muted);
}
```

### 2.4 Font Loading Strategy

**Objectif** : zéro Cumulative Layout Shift (CLS), zéro "flash of unstyled text" visible.

```html
<!-- Dans <head>, AVANT tout CSS custom -->

<!-- Précharge des fonts depuis Google Fonts ou Fontshare -->
<link rel="preload" as="font" href="https://fonts.googleapis.com/css2?family=Clash+Display:wght@400;600;700&display=swap" crossorigin>
<link rel="preload" as="font" href="https://fonts.googleapis.com/css2?family=Satoshi:wght@400;500;700&display=swap" crossorigin>

<!-- Ou si using fondries payantes (Adobe Fonts, Monotype, etc.) -->
<link rel="preload" as="font" href="/fonts/ClashDisplay-Bold.woff2" type="font/woff2" crossorigin>
```

```css
/* Font-display: swap = montre fallback IMMÉDIATEMENT, puis remplace font custom */
@font-face {
  font-family: 'Clash Display';
  src: url('/fonts/ClashDisplay-Bold.woff2') format('woff2'),
       url('/fonts/ClashDisplay-Bold.woff') format('woff');
  font-weight: 700;
  font-display: swap;  /* CRITICAL: jamais "block" ou "auto" */
}

@font-face {
  font-family: 'Satoshi';
  src: url('/fonts/Satoshi-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}

/* Fallback stack - essayer locale, puis fonts Google, puis système */
h1, h2 {
  font-family: 'Clash Display', 'Futura', 'Trebuchet MS', sans-serif;
}

body, p, li {
  font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

**Performance Notes** :
- Variable fonts (Fraunces, Unbounded) = moins de fichiers mais un seul .woff2 plus gros
- Fixed weights (Clash Display Bold 700 uniquement) = fichier smaller mais moins flexible
- Stratégie habituelle : 1 variable font body + 1-2 files display fixes

### 2.5 Adaptation Typographique par Secteur

Voir section "Direction Artistique par Secteur" pour pairings complets.

**Règle rapide** :
- **Luxury** = serif traditionnel (Playfair, Cormorant) + sans modern minimale (General Sans)
- **Tech** = sans geometric (Clash, Satoshi) + mono (JetBrains) pour credibilité dev
- **Créative** = display experimental (Unbounded, Bricolage) + sans warm (Manrope, Plus Jakarta)
- **Corporate** = sans professional (IBM Plex, Manrope) + serif pour warmth (Lora, Recoleta)

---

## 3. COULEUR & PALETTE

La couleur est une **arme de conversion**. Elle crée hiérarchie, émotion, et urgence.

### 3.1 Structure CSS Custom Properties

```css
:root {
  /* PRIMARY BRAND COLOR */
  --color-primary: #2563eb;        /* Brand lead color - CTA, highlights */
  --color-primary-dark: #1e40af;
  --color-primary-light: #3b82f6;
  --color-primary-muted: #dbeafe;  /* subtle bg, barely visible */

  /* ACCENT / SECONDARY */
  --color-accent: #ec4899;         /* Complementary for contrast */
  --color-accent-dark: #be185d;
  --color-accent-light: #f472b6;

  /* BACKGROUND & TEXT */
  --color-bg: #ffffff;
  --color-bg-alt: #f9fafb;         /* Slightly off-white for sections */
  --color-bg-muted: #f3f4f6;       /* For cards, containers */

  --color-text: #111827;           /* Primary text - H1, p, labels */
  --color-text-secondary: #4b5563; /* Slightly lighter - meta, secondary */
  --color-text-muted: #9ca3af;     /* Very light - captions, disabled */

  /* SEMANTIC */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #0ea5e9;

  /* NEUTRAL SCALE (for depth) */
  --color-neutral-50: #f9fafb;
  --color-neutral-100: #f3f4f6;
  --color-neutral-200: #e5e7eb;
  --color-neutral-300: #d1d5db;
  --color-neutral-400: #9ca3af;
  --color-neutral-500: #6b7280;
  --color-neutral-600: #4b5563;
  --color-neutral-700: #374151;
  --color-neutral-800: #1f2937;
  --color-neutral-900: #111827;

  /* BORDERS & DIVIDERS */
  --color-border: #e5e7eb;
  --color-border-dark: #d1d5db;

  /* SHADOWS */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

/* DARK MODE */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0f172a;
    --color-bg-alt: #1e293b;
    --color-bg-muted: #334155;

    --color-text: #f1f5f9;
    --color-text-secondary: #cbd5e1;
    --color-text-muted: #94a3b8;

    --color-border: #475569;
    --color-border-dark: #64748b;
  }
}
```

### 3.2 Comment Construire une Palette à Partir d'une Couleur Primaire

**Étape 1 : Choisir la couleur primaire** (la "hero color" de la marque)
- Exemple : #2563eb (bleu électrique)

**Étape 2 : Générer variations** (via Tailwind, Coolors, ou Huetone)
- Dark (saturation +10%, lightness -20%) : #1e40af
- Light (saturation -5%, lightness +15%) : #3b82f6
- Muted (saturation -60%, lightness +40%) : #dbeafe

**Étape 3 : Choisir l'accent** (complémentaire ou triad)
- Complémentaire (180°) : orange, pink, ou teal
- Triad (120° intervals) : plus harmonieux si couleur primaire froide
- Recommendation : prendre couleur chaude (rose, orange) si primaire est froide (bleu, vert)

**Étape 4 : Construire le neutre** (grays)
- Pas d'utiliser #999 ou #ccc (trop "web 2000")
- Créer scale de 9 grays avec subtilité : du très clair au charbon
- Assurer chaque step a une utilité : labels, borders, disabled, text secondary, etc.

**Étape 5 : Tester le contraste** (WCAG AA minimum)

### 3.3 Contraste & Accessibilité

**WCAG AA Standards** (minimum acceptable) :
- **Normal text (14px+)** : 4.5:1 contrast ratio
- **Large text (18px+ ou 14px bold)** : 3:1 contrast ratio
- **Non-text contrast (borders, icons)** : 3:1 contrast ratio

```css
/* ✅ PASS: #111827 text on #ffffff bg */
/* Ratio: 18:1 — excellent */

/* ⚠️ WARNING: #6b7280 text on #f3f4f6 bg */
/* Ratio: 2.5:1 — FAIL, only for disabled state */

/* ✅ PASS: #374151 text on #f9fafb bg */
/* Ratio: 8.5:1 — good for secondary text */
```

**Tool Check** :
- WebAIM Contrast Checker (webaim.org/resources/contrastchecker)
- Polypane contrast checker
- Chrome DevTools Lighthouse

### 3.4 Couleur comme Outil de Conversion

#### Primary CTA Button
```css
.btn-primary {
  background-color: var(--color-primary);
  color: #ffffff;
  /* Shadow pour lift, border-radius subtle pour moderne */
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
  border-radius: 6px;
  font-weight: 600;
  padding: 12px 24px;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
  transform: translateY(-2px); /* subtle lift */
}
```

**Règle CRO** :
- CTA ne doit JAMAIS être la couleur neutre (gris, blanc)
- CTA contraste fort avec contexte (si fond blanc → couleur vive; si fond coloré → blanc ou noir)
- Ordre de hierarchy : Primary CTA (color bold) → Secondary CTA (outline) → Tertiary (text link)

#### Visual Hierarchy par Couleur
```css
/* H1 — text primary, emphasis via taille + weight */
h1 { color: var(--color-text); font-weight: 700; }

/* Accent highlight — utiliser sparingly pour guide attention */
.highlight {
  color: var(--color-accent);
  font-weight: 600;
}

/* Meta text — secondary color, lighter weight */
.meta {
  color: var(--color-text-secondary);
  font-size: var(--fs-small);
}

/* Disabled state — very muted */
.disabled {
  color: var(--color-text-muted);
  opacity: 0.5;
}
```

### 3.5 Dark Mode vs Light Mode

**Quand utiliser Dark Mode** :
- ✅ SaaS tools, dashboards (les utilisateurs passent des heures)
- ✅ Creative agencies, portfolios (wow factor)
- ✅ Tech products (developer credibility)
- ❌ E-commerce de luxe (préférer light pour commodity)
- ❌ Food & Beverage (couleurs trop murky en dark)
- ❌ Finance (trop "gaming", pas assez trustworthy)

**Stratégie** : offrir toggle au user, sauvegarder preference dans localStorage

```javascript
// Check user preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const userSetting = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');

document.documentElement.setAttribute('data-theme', userSetting);

// Toggle function
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}
```

```css
:root[data-theme="light"] {
  --color-bg: #ffffff;
  --color-text: #111827;
  /* ...etc */
}

:root[data-theme="dark"] {
  --color-bg: #0f172a;
  --color-text: #f1f5f9;
  /* ...etc */
}
```

### 3.6 Associations Couleur par Industrie

| Industrie | Couleur Primaire | Accent | Rationale | Tone |
|-----------|------------------|--------|-----------|------|
| **Finance/Fintech** | Navy (#001a4d), Dark Blue (#003d82) | Gold (#d4af37), Emerald (#27ae60) | Trustworthiness, security | Conservative mais modern |
| **Tech/SaaS** | Electric Blue (#2563eb), Purple (#7c3aed) | Cyan (#06b6d4), Neon Pink (#ec4899) | Innovation, speed | Playful but professional |
| **Luxury** | Black (#000000), Deep Plum (#2d1b4e) | Gold (#fbbf24), Pearl White (#faf9f6) | Exclusivity, heritage | Minimal, refined |
| **Health/Wellness** | Green (#10b981), Sage (#6b8e7f) | Warm Orange (#f59e0b), Blush (#f9a8d4) | Trust, healing, natural | Calm, approachable |
| **Food & Beverage** | Warm Brown (#92400e), Burgundy (#7f2d2d) | Terracotta (#ea8b5b), Sage Green (#84a59d) | Appetite, warmth, naturalness | Inviting, comfortable |
| **E-commerce DTC** | Bold Magenta (#d946ef), Vibrant Orange (#f97316) | Bright Cyan (#06b6d4), Lime (#84cc16) | Energy, attention-grabbing | Bold, youthful |
| **Fashion/Mode** | Black (#000000), Charcoal (#36454f) | Rose Gold (#b76e79), Sage (#9dad9f) | Sophistication, trend | Elegant, aspirational |
| **Education** | Royal Blue (#1e40af), Teal (#0d9488) | Warm Yellow (#fbbf24), Purple (#a855f7) | Knowledge, growth | Friendly, inspiring |
| **Real Estate** | Slate Blue (#64748b), Warm Gray (#a1957a) | Terracotta (#ea8b5b), Forest Green (#15803d) | Stability, value | Trustworthy, aspirational |

---

## 4. LAYOUT & COMPOSITION SPATIALE

Le layout crée le rythme. C'est le squelette dont émerge le design.

### 4.1 Systèmes de Grille

#### **12-Column Grid** (standard, responsive)
```css
.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1.5rem; /* 24px */
}

/* Mobile (1 col) */
@media (max-width: 640px) {
  .grid-12 { grid-template-columns: 1fr; }
}

/* Tablet (2 col) */
@media (min-width: 641px) and (max-width: 1024px) {
  .grid-12 { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop (full 12) */
@media (min-width: 1025px) {
  .grid-12 { grid-template-columns: repeat(12, 1fr); }
}

/* Usage */
.grid-12 > .item:nth-child(1) { grid-column: span 8; }  /* 2/3 width */
.grid-12 > .item:nth-child(2) { grid-column: span 4; }  /* 1/3 width */
```

#### **Asymmetric Grid** (plus intéressant visuellement)
```css
.grid-asymmetric {
  display: grid;
  grid-template-columns: 1fr 0.6fr 1.2fr;
  gap: 2rem;
}

/* Crée rhythm via non-uniformité */
```

#### **Masonry Layout** (imagesories, portfolios)
```css
.masonry {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

/* Ou via Masonry CSS (support limité) */
.masonry {
  column-count: 3;
  column-gap: 1.5rem;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .masonry { column-count: 1; }
}
```

### 4.2 Breaking the Grid: Techniques d'Asymétrie

#### **Overlap & Layering**
```css
.hero-with-overlap {
  position: relative;
  padding: 80px 40px;
}

.hero-image {
  position: absolute;
  right: -60px;
  top: -40px;
  z-index: 1;
  max-width: 600px;
}

.hero-text {
  position: relative;
  z-index: 2;
  max-width: 500px;
}

/* Image overlaps text, creates tension */
```

#### **Diagonal Flow**
```css
.section-diagonal {
  position: relative;
  overflow: hidden;
}

.diagonal-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--color-primary);
  clip-path: polygon(0 0, 100% 0, 100% 75%, 0 100%);
  z-index: -1;
}

/* Content floats over diagonal shape */
```

#### **Z-Pattern Layout** (guides eye naturally)
```css
/* Eye naturally follows Z:
   1. Top-left
   2. Top-right
   3. Bottom-left
   4. Bottom-right
*/

.z-pattern {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
}

.z-pattern > :nth-child(1) { grid-column: 1; grid-row: 1; }  /* TL */
.z-pattern > :nth-child(2) { grid-column: 2; grid-row: 1; }  /* TR */
.z-pattern > :nth-child(3) { grid-column: 1; grid-row: 2; }  /* BL */
.z-pattern > :nth-child(4) { grid-column: 2; grid-row: 2; }  /* BR */

/* Alternate pattern: odd items left, even items right */
```

#### **F-Pattern Layout** (natural reading flow)
```css
/* Eye follows F when scanning:
   1. Top horizontal
   2. Middle horizontal (shorter)
   3. Vertical down left
*/

.f-pattern {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.f-header { width: 100%; }
.f-feature { width: 70%; }
.f-list { width: 100%; display: grid; grid-template-columns: repeat(3, 1fr); }
```

### 4.3 Negative Space comme Outil Design

Negative space n'est pas "vide" — c'est **respiration**.

```css
/* Minimal, spacious design */
.feature {
  padding: 60px 40px;          /* ample padding */
  max-width: 1000px;
  margin: 0 auto;
}

.feature-title {
  margin-bottom: 2rem;         /* space between headline + copy */
}

.feature-copy {
  max-width: 600px;            /* constrains line-length for readability */
  margin-bottom: 3rem;         /* space before CTA */
  line-height: 1.8;            /* loose for breathing */
}

/* Rule: Negative space = emotional breathing */
```

### 4.4 Breakpoints Responsif (Mobile-First)

```css
/* Base = mobile (< 640px) */
.container {
  width: 100%;
  padding: 1rem;
  font-size: 14px;
}

/* Small tablets */
@media (min-width: 640px) {
  .container {
    padding: 1.5rem;
    font-size: 15px;
  }
}

/* Tablets */
@media (min-width: 768px) {
  .container {
    width: 750px;
    margin: 0 auto;
    padding: 2rem;
    font-size: 16px;
  }
}

/* Small desktop */
@media (min-width: 1024px) {
  .container {
    width: 960px;
    padding: 2.5rem;
  }
}

/* Full desktop */
@media (min-width: 1280px) {
  .container {
    width: 1200px;
    padding: 3rem;
  }
}

/* Ultra-wide */
@media (min-width: 1536px) {
  .container {
    width: 1400px;
  }
}

/* Orientation mobile landscape */
@media (max-width: 1024px) and (orientation: landscape) {
  /* Adjust for tall-thin screens */
}
```

### 4.5 Section Rhythm: Alternance Dense/Airy

Pattern que crée du flow visuel :

```css
/* Dense section — packed avec info */
.section-dense {
  padding: 40px;
  background: var(--color-bg-muted);
}

.section-dense-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;  /* tight spacing */
}

/* Airy section — spacieux, breathing */
.section-airy {
  padding: 120px 60px;  /* ample padding */
  background: var(--color-bg);
}

.section-airy-content {
  max-width: 800px;
  margin: 0 auto;
}

/* Rhythm: Airy → Dense → Airy → Dense */
/* Crée dynamique, prévient monotonie */
```

### 4.6 Max-Width Containers

```css
/* Content container — readable line-length */
.container-content {
  max-width: 800px;  /* ~65-70 chars per line */
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Full-bleed sections — hero, image showcase */
.section-fullbleed {
  width: 100vw;
  margin-left: calc(-50vw + 50%);
}

/* Safe container — avec breathing */
.container-safe {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;  /* margin qui scale avec viewport */
}

/* Ultra-wide — pour immersive designs */
.container-ultra {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 3rem;
}

@media (max-width: 768px) {
  .container-safe,
  .container-ultra {
    max-width: 100%;
    padding: 0 1rem;
  }
}
```

---

## 5. MOTION & ANIMATION

Animation donne la vie. Elle guide l'attention, crée delight, et renforce hiérarchie.

### 5.1 Page Load: Staggered Reveals

```css
/* Base — tous les items starts invisible */
.item {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeUpReveal 0.6s ease-out forwards;
}

/* Stagger chaque item avec délai croissant */
.item:nth-child(1) { animation-delay: 0s; }
.item:nth-child(2) { animation-delay: 0.1s; }
.item:nth-child(3) { animation-delay: 0.2s; }
.item:nth-child(4) { animation-delay: 0.3s; }

@keyframes fadeUpReveal {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Automated stagger via CSS */
.item {
  animation-delay: calc(var(--index) * 0.1s);
}
```

### 5.2 Scroll Animations: IntersectionObserver

```javascript
// Observe when elements enter viewport
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in-view');
      // Option: observer.unobserve(entry.target) si animation une seule fois
    }
  });
}, {
  threshold: 0.1,  // Trigger when 10% visible
});

document.querySelectorAll('[data-scroll-animate]').forEach((el) => {
  observer.observe(el);
});
```

```css
/* Element starts hidden */
[data-scroll-animate] {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}

/* Triggered by .in-view class */
[data-scroll-animate].in-view {
  opacity: 1;
  transform: translateY(0);
}

/* Different animation types */
[data-scroll-animate="fade"] {
  opacity: 0;
  transform: none;
}

[data-scroll-animate="slide-left"] {
  opacity: 0;
  transform: translateX(-50px);
}

[data-scroll-animate="slide-right"] {
  opacity: 0;
  transform: translateX(50px);
}

[data-scroll-animate="scale"] {
  opacity: 0;
  transform: scale(0.95);
}

[data-scroll-animate="clip-reveal"] {
  clip-path: inset(0 100% 0 0);
}

[data-scroll-animate].in-view[data-scroll-animate="clip-reveal"] {
  clip-path: inset(0 0 0 0);
  transition: clip-path 0.8s ease-out;
}
```

### 5.3 Hover States: Subtle Transforms

```css
/* Link hover */
a {
  transition: color 0.3s ease, text-decoration 0.3s ease;
}

a:hover {
  color: var(--color-primary);
  text-decoration: underline;
}

/* Button hover — lift + shadow */
.btn {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.btn:active {
  transform: translateY(0);
}

/* Card hover — subtle scale + shadow */
.card {
  transition: all 0.3s ease;
  transform: scale(1);
  box-shadow: var(--shadow-md);
}

.card:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-lg);
}

/* Image hover — slight zoom */
.image-hover {
  overflow: hidden;
  border-radius: 8px;
}

.image-hover img {
  transition: transform 0.4s ease;
  transform: scale(1);
}

.image-hover:hover img {
  transform: scale(1.05);
}
```

### 5.4 CTA Animations: Pulse, Glow, Micro-Bounce

```css
/* Pulse animation — subtle grow/shrink */
@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.7);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(37, 99, 235, 0);
  }
}

.btn-pulse {
  animation: pulse 2s infinite;
}

/* Glow animation — bright halo */
@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(37, 99, 235, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(37, 99, 235, 1);
  }
}

.btn-glow {
  animation: glow 2s ease-in-out infinite;
}

/* Micro-bounce — playful CTA */
@keyframes microBounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

.btn-bounce {
  animation: microBounce 1.5s ease-in-out infinite;
}

/* Arrow wiggle — "scroll down" hint */
@keyframes wiggle {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-3px);
  }
  75% {
    transform: translateX(3px);
  }
}

.scroll-hint {
  animation: wiggle 1s ease-in-out infinite;
}
```

### 5.5 Performance Rules

```css
/* ✅ Use transform & opacity — GPU accelerated */
.good {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

/* ❌ Avoid animating width, height, position — causes reflow */
.bad {
  transition: width 0.3s ease;
}

/* Use will-change sparingly — helps browser optimize */
.animated-element {
  will-change: transform;
}

/* Remove will-change when animation ends */

/* Respect user preference for reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 5.6 Code Snippets: Common Patterns

```css
/* Shimmer Loading Animation */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
}

/* Text Reveal Animation */
@keyframes textReveal {
  0% {
    clip-path: inset(0 100% 0 0);
  }
  100% {
    clip-path: inset(0 0 0 0);
  }
}

.reveal-text {
  animation: textReveal 0.8s ease-out forwards;
}

/* Counter Animation (with JavaScript) */
.counter {
  font-weight: 700;
  font-size: 2.5rem;
}

/* In JS: setInterval with counter updates */

/* Gradient Shift Animation */
@keyframes gradientShift {
  0% {
    background-position: 0% center;
  }
  100% {
    background-position: 100% center;
  }
}

.gradient-animated {
  background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
  background-size: 200% 100%;
  animation: gradientShift 4s ease infinite;
}
```

---

## 6. BACKGROUNDS & TEXTURES

Textures ajoutent profondeur, sophistication, et personnalité.

### 6.1 Gradient Meshes (Backgrounds Complexes)

```css
/* Mesh gradient — multiple radial overlaps */
.mesh-gradient {
  background:
    radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.4) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(240, 46, 170, 0.4) 0%, transparent 50%),
    radial-gradient(circle at 40% 0%, rgba(64, 224, 208, 0.3) 0%, transparent 50%);
  background-color: #ffffff;
}

/* Smooth, flowing feel */

/* Animated mesh */
.mesh-animated {
  background:
    radial-gradient(circle at var(--x, 50%) var(--y, 50%), rgba(102, 126, 234, 0.4) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(240, 46, 170, 0.4) 0%, transparent 50%);
  background-color: #ffffff;
  animation: meshShift 8s ease-in-out infinite;
}

@keyframes meshShift {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 100%; }
}
```

### 6.2 Noise/Grain Overlays

```css
/* Grain texture via SVG filter */
.grain-bg {
  background-color: var(--color-bg);
  position: relative;
}

.grain-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIj4KICA8ZmlsdGVyIGlkPSJub2lzZSI+CiAgICA8ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iMC45IiBudW1PY3RhdmVzPSI0IiByZXN1bHQ9Im5vaXNlIiAvPgogICAgPGZlQ29sb3JNYXRyaXggaW49Im5vaXNlIiB0eXBlPSJzYXR1cmF0ZSIgdmFsdWVzPSIwIiAvPgogIDwvZmlsdGVyPgogIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiBmaWx0ZXI9InVybCgjbm9pc2UpIiBvcGFjaXR5PSIwLjAyIiAvPgo8L3N2Zz4=');
  background-size: 400px 400px;
  pointer-events: none;
  z-index: 1;
  opacity: 0.3;
}

.grain-bg > * {
  position: relative;
  z-index: 2;
}
```

### 6.3 Geometric Patterns

```css
/* Repeating SVG pattern — dots */
.pattern-dots {
  background-image: radial-gradient(circle, var(--color-primary) 1px, transparent 1px);
  background-size: 20px 20px;
  background-position: 0 0, 10px 10px;
}

/* Repeating SVG pattern — stripes */
.pattern-stripes {
  background-image: repeating-linear-gradient(
    45deg,
    var(--color-primary),
    var(--color-primary) 10px,
    transparent 10px,
    transparent 20px
  );
}

/* Grid pattern */
.pattern-grid {
  background-image:
    linear-gradient(0deg, transparent 24%, rgba(0, 0, 0, 0.05) 25%, rgba(0, 0, 0, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 0, 0, 0.05) 75%, rgba(0, 0, 0, 0.05) 76%, transparent 77%, transparent),
    linear-gradient(90deg, transparent 24%, rgba(0, 0, 0, 0.05) 25%, rgba(0, 0, 0, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 0, 0, 0.05) 75%, rgba(0, 0, 0, 0.05) 76%, transparent 77%, transparent);
  background-size: 50px 50px;
}
```

### 6.4 Blur & Glass Effects

```css
/* Glass morphism — modern, trendy */
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
}

/* Darkened glass */
.glass-dark {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Blur backdrop for modals */
.modal-backdrop {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

/* Note: backdrop-filter not supported in all browsers, provide fallback */
@supports not (backdrop-filter: blur(10px)) {
  .glass {
    background: rgba(255, 255, 255, 0.9);
  }
}
```

### 6.5 Quand Utiliser Quoi

```css
/* Luxury brand → Subtle gradient + grain */
.luxury-section {
  background: linear-gradient(135deg, #f5f5f0 0%, #ffffff 100%);
  position: relative;
}
.luxury-section::before {
  /* fine grain overlay */
  opacity: 0.02;
}

/* Tech product → Mesh gradient + glass elements */
.tech-section {
  background: radial-gradient(circle at 30% 60%, #667eea, #transparent);
  color: #ffffff;
}

/* Creative agency → Bold gradient + pattern */
.creative-section {
  background: linear-gradient(45deg, #667eea, #764ba2);
  background-image: url('pattern.svg');
}

/* Food & Beverage → Warm color + subtle texture */
.food-section {
  background: linear-gradient(135deg, #f0e4d7, #f9e8d1);
  background-image: url('noise.svg');
}
```

---

## 7. ÉLÉMENTS SIGNATURE

Un site mémorable a au minimum **1 élément "wow"** par page. C'est ce qui crée l'association mentale avec la marque.

### 7.1 Catégories d'Éléments Signature

#### **Custom Cursor Effects**
```javascript
// Move cursor-following element
document.addEventListener('mousemove', (e) => {
  const cursor = document.querySelector('.custom-cursor');
  cursor.style.left = e.clientX + 'px';
  cursor.style.top = e.clientY + 'px';
});
```

```css
.custom-cursor {
  position: fixed;
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-primary);
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  transition: transform 0.1s ease-out;
}

.custom-cursor.active {
  transform: scale(1.5);
  background: var(--color-primary);
}
```

#### **Parallax Sections**
```javascript
window.addEventListener('scroll', () => {
  const parallaxElements = document.querySelectorAll('[data-parallax]');
  parallaxElements.forEach((el) => {
    const offset = el.dataset.parallax;
    el.style.transform = `translateY(${window.scrollY * offset}px)`;
  });
});
```

#### **Text Reveal Animations**
```css
.reveal-text {
  position: relative;
  overflow: hidden;
}

.reveal-text::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: var(--color-primary);
  animation: revealMask 0.8s ease-out forwards;
}

@keyframes revealMask {
  0% { width: 100%; }
  100% { width: 0%; }
}
```

#### **Morphing Shapes (SVG)**
```html
<svg viewBox="0 0 200 200">
  <defs>
    <filter id="gooey">
      <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="coloredBlur" />
      <feMerge>
        <feMergeNode in="coloredBlur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <circle cx="100" cy="100" r="50" fill="var(--color-primary)" filter="url(#gooey)">
    <animate attributeName="r" values="50;60;50" dur="2s" repeatCount="indefinite" />
  </circle>
</svg>
```

#### **Interactive Hover Galleries**
```javascript
const gallery = document.querySelector('.gallery');
const images = gallery.querySelectorAll('img');

gallery.addEventListener('mousemove', (e) => {
  const x = e.clientX - gallery.getBoundingClientRect().left;
  const percentage = (x / gallery.offsetWidth) * 100;

  images.forEach((img, idx) => {
    const imgStart = (idx / images.length) * 100;
    const imgEnd = ((idx + 1) / images.length) * 100;

    if (percentage >= imgStart && percentage <= imgEnd) {
      img.style.opacity = 1;
    } else {
      img.style.opacity = 0;
    }
  });
});
```

#### **Animated SVG Illustrations**
```html
<svg class="animated-icon" viewBox="0 0 100 100">
  <path class="path" d="M 10 50 Q 50 10, 90 50" stroke-width="2" fill="none" />
</svg>
```

```css
.path {
  stroke: var(--color-primary);
  stroke-linecap: round;
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  animation: drawPath 1.5s ease-in-out forwards;
}

@keyframes drawPath {
  to { stroke-dashoffset: 0; }
}
```

#### **Scroll-Triggered Counters**
```javascript
function animateCounter(element, target, duration = 1000) {
  let current = 0;
  const increment = target / (duration / 16);

  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = target;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 16);
}

// Trigger when element enters viewport
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      const target = entry.target.dataset.count;
      animateCounter(entry.target, parseInt(target));
      observer.unobserve(entry.target);
    }
  });
});

document.querySelectorAll('[data-count]').forEach((el) => observer.observe(el));
```

#### **Dynamic Gradients (Animé)**
```css
.gradient-dynamic {
  background: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #4facfe);
  background-size: 400% 400%;
  animation: gradientFlow 15s ease infinite;
}

@keyframes gradientFlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

### 7.2 Critère de Sélection

**L'élément signature doit SERVIR la message**, pas juste regarder cool.

```
Règles:
- ✅ Renforce l'identité de la marque
- ✅ Guide l'utilisateur vers l'action clé
- ✅ N'interfère pas avec accessibility
- ❌ N'est pas une distraction gratuite
- ❌ Ne ralentit pas le site (performance critical)
```

---

## 8. DIRECTION ARTISTIQUE PAR SECTEUR

Chaque secteur a des conventions de design. Le GSG doit les connaître ET les briser intelligemment.

### Matrice Complète: 13 Secteurs

| **Secteur** | **DA Angle** | **Font Pairing** | **Palette Primaire** | **Layout Style** | **Signature Element** | **CRO Focus** |
|---|---|---|---|---|---|---|
| **E-commerce DTC** | Bold, energetic, youth-focused | Unbounded (h1) + Manrope (body) | Magenta + Cyan + Black | Asymmetric grid, full-bleed hero | Hover product galleries, animated counters (stock, reviews) | "Add to Cart" prominence, trust badges, social proof |
| **E-commerce Luxe** | Minimal, refined, heritage | Playfair Display + General Sans | Black + Gold + Cream | Spacious, editorial rhythm | Parallax imagery, smooth scroll reveals | Product storytelling, exclusivity messaging, high-res imagery |
| **SaaS B2B** | Professional, trustworthy, technical | Clash Display + IBM Plex Sans | Navy + Electric Blue + Neutral | 12-col grid, dense feature sections | Animated SVG product demos, screenshot carousels | Feature benefits, pricing transparency, free trial CTA |
| **SaaS B2C** | Approachable, playful, accessible | Syne + Satoshi | Teal + Orange + White | Asymmetric, varied section heights | Microinteractions on buttons, animated onboarding flow | Simplicity of use, social proof, quick signup |
| **Agence Créative** | Artistic, experimental, bold | Bricolage Grotesque + Plus Jakarta Sans | Charcoal + Accent (brand-specific) + Texture | Editorial, z-pattern, broken grid | Custom cursor, scroll-driven animations, morphing shapes | Portfolio impact, client case studies, contact CTA |
| **Service B2B (Consulting)** | Corporate, expertise-driven, minimalist | Cormorant + Satoshi | Navy + Slate + Warm Gray | Conservative grid, plenty of white space | Team bios with hover animations, statistic counters | Experience, testimonials, consultation booking |
| **Startup Tech** | Disruptive, future-forward, energetic | Clash Display + General Sans | Neon (accent) + Dark background | Full-bleed sections, asymmetric | Animated SVG illustrations, scrolljacking reveal, animated counter | Funding stage, product vision, investor deck link |
| **Food & Beverage** | Warm, inviting, sensory | Unbounded + Manrope | Warm Brown + Terracotta + Sage Green | Circular/organic layouts, high-res food imagery | Parallax food galleries, recipe animations, ingredient reveals | Menu clarity, online ordering CTA, delivery options |
| **Santé & Wellness** | Calm, trustworthy, natural | Lora + Manrope | Green + Warm White + Accent soft | Clean, airy sections, cardio imagery | Scroll-triggered wellness stat counters, guided breathe animation | Doctor credentials, patient testimonials, appointment booking |
| **Finance & Fintech** | Serious, secure, transparent | Cormorant + IBM Plex Sans | Dark Navy + Gold + Neutral | Conservative grid, data visualization focus | Chart animations, ticker tapes, security badge | Risk transparency, fee breakdown, account setup simplicity |
| **Éducation** | Inspiring, growth-focused, accessible | General Sans + Playfair Display | Teal + Warm Yellow + Navy | Modular grid, course cards | Animated progress indicators, course preview videos | Student testimonials, free trial, enrollment CTA |
| **Fashion & Mode** | Elegant, aspirational, trend-forward | Fraunces + Outfit | Black + Rose Gold + Sage | Editorial, asymmetric, full-bleed images | Hover product zooms, animated lookbooks, style guides | Seasonal collections, size guides, styling tips |
| **Immobilier** | Trustworthy, aspirational, showcase-focused | Recoleta + Satoshi | Warm Gray + Slate + Terracotta | Grid of property cards, 3D visualization, maps | Property image carousels, 360° tours, mortgage calculator | Virtual tours, agent bios, financing options |

### Détails par Secteur

#### **E-commerce DTC** (Direct-to-Consumer: mode, beauty, gadgets)

**Direction Artistique** : Bold color, youth energy, social-first mindset

```css
.dtc-hero {
  background: linear-gradient(135deg, #d946ef 0%, #2563eb 100%);
  color: white;
  padding: 120px 40px;
  text-align: center;
}

.dtc-hero h1 {
  font-family: 'Unbounded', sans-serif;
  font-size: 3.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dtc-product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.dtc-product-card {
  position: relative;
  overflow: hidden;
  aspect-ratio: 1;
}

.dtc-product-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.dtc-product-card:hover img {
  transform: scale(1.1) rotate(2deg);
}

.dtc-product-card-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 1rem;
  transform: translateY(100%);
  transition: transform 0.3s ease;
}

.dtc-product-card:hover .dtc-product-card-info {
  transform: translateY(0);
}
```

**CRO Points** :
- Couleur CTA doit CONTRASTER fortement (blanc sur fond coloré, ou couleur accent sur fond blanc)
- Social proof via avis clients, count de reviews visibles
- Stock indicator ("Seulement 3 restant")
- Easy "Add to Bag" sans friction

#### **E-commerce Luxe** (Hermès, Yves Saint Laurent, artisanal)

**Direction Artistique** : Minimal, editorial, heritage-focused

```css
.luxury-hero {
  width: 100%;
  aspect-ratio: 16 / 9;
  background-image: url('hero-image.jpg');
  background-size: cover;
  background-position: center;
  position: relative;
}

.luxury-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to right, rgba(0,0,0,0.3), transparent);
}

.luxury-hero-content {
  position: absolute;
  bottom: 60px;
  left: 60px;
  max-width: 500px;
  color: white;
  z-index: 2;
}

.luxury-hero-content h1 {
  font-family: 'Playfair Display', serif;
  font-size: 3rem;
  font-weight: 400;
  line-height: 1.2;
  margin-bottom: 2rem;
  letter-spacing: 0.08em;
}

.luxury-feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  padding: 100px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.luxury-feature-grid > :nth-child(odd) {
  padding-right: 40px;
}

.luxury-feature-image {
  aspect-ratio: 3 / 4;
  background: var(--color-bg-muted);
  border-radius: 2px;
}
```

**CRO Points** :
- Storytelling avant tout (heritage, craftsmanship, provenance)
- Haute-res imagery (4K minimum)
- Detailed product specs: matériaux, dimensions, origin
- Personal shopping CTA over "Add to Cart"

#### **SaaS B2B** (Salesforce, HubSpot, Notion-like)

**Direction Artistique** : Professional, dashboard-like, feature-rich

```css
.saas-nav {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 1rem 2rem;
}

.saas-feature-section {
  padding: 80px 40px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  max-width: 1400px;
  margin: 0 auto;
  align-items: center;
}

.saas-feature-image {
  border-radius: 12px;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.saas-benefits-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  padding: 80px 40px;
}

.saas-benefit-card {
  padding: 2rem;
  border-radius: 8px;
  background: var(--color-bg-muted);
  border: 1px solid var(--color-border);
}

.saas-benefit-card-icon {
  width: 48px;
  height: 48px;
  background: var(--color-primary);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.saas-pricing {
  padding: 100px 40px;
  text-align: center;
}

.saas-pricing-table {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  max-width: 1200px;
  margin: 3rem auto 0;
}

.saas-pricing-card {
  border: 2px solid var(--color-border);
  border-radius: 12px;
  padding: 2rem;
  transition: all 0.3s ease;
}

.saas-pricing-card.featured {
  border-color: var(--color-primary);
  background: var(--color-primary-muted);
  transform: scale(1.05);
}

.saas-pricing-card:hover {
  box-shadow: var(--shadow-lg);
}
```

**CRO Points** :
- Feature comparison table, side-by-side clarity
- Free trial CTA prédominant
- Customer logos / testimonials early
- Pricing transparency, no hidden fees messaging
- Security badges (SOC 2, ISO, GDPR compliant)

#### **SaaS B2C** (Notion, Slack, Figma pour consumer)

**Direction Artistique** : Friendly, playful, low-friction

```css
.b2c-onboarding-flow {
  padding: 60px 40px;
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.b2c-step {
  margin-bottom: 4rem;
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp 0.6s ease-out forwards;
}

.b2c-step:nth-child(1) { animation-delay: 0s; }
.b2c-step:nth-child(2) { animation-delay: 0.1s; }
.b2c-step:nth-child(3) { animation-delay: 0.2s; }

.b2c-step-number {
  display: inline-block;
  width: 48px;
  height: 48px;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.b2c-signup-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
  border-radius: 12px;
  background: var(--color-bg-muted);
}

.b2c-form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 1rem;
  margin-bottom: 1rem;
  font-family: var(--font-body);
  transition: border-color 0.3s ease;
}

.b2c-form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.b2c-form-submit {
  width: 100%;
  padding: 12px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.b2c-form-submit:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
```

**CRO Points** :
- Minimal signup friction (email + password, ou Google OAuth)
- Demo video or animated walkthrough early
- "Start free" vs "Get started" (free perception important)
- Social proof: user count, satisfaction score

#### **Agence Créative**

**Direction Artistique** : Artistic, experimental, show portfolio strength

```css
.creative-portfolio-hero {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.creative-portfolio-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  z-index: 1;
}

.creative-portfolio-content {
  position: relative;
  z-index: 2;
  text-align: center;
  color: white;
}

.creative-portfolio-content h1 {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-size: 4rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.creative-work-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  padding: 60px 40px;
}

.creative-work-item {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border-radius: 12px;
  cursor: pointer;
}

.creative-work-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.creative-work-item:hover img {
  transform: scale(1.1);
}

.creative-work-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s ease;
}

.creative-work-item:hover .creative-work-overlay {
  background: rgba(0, 0, 0, 0.6);
}

.creative-work-overlay-content {
  color: white;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.creative-work-item:hover .creative-work-overlay-content {
  opacity: 1;
}
```

**CRO Points** :
- Portfolio case studies avec context, challenge, solution
- Client testimonials with photos
- "Let's work together" CTA, clear contact form
- Instagram/LinkedIn integration pour social proof

#### **Service B2B (Consulting)**

**Direction Artistique** : Conservative, expertise-driven, minimal

```css
.consulting-hero {
  padding: 100px 60px;
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.consulting-expertise-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3rem;
  padding: 80px 60px;
}

.consulting-expertise-card {
  padding: 2rem;
}

.consulting-expertise-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.consulting-expertise-label {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.consulting-team-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  padding: 80px 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.consulting-team-card {
  text-align: center;
}

.consulting-team-image {
  width: 100%;
  aspect-ratio: 1;
  background: var(--color-bg-muted);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.consulting-team-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.consulting-team-name {
  font-weight: 600;
  font-size: 1.125rem;
  margin-bottom: 0.25rem;
}

.consulting-team-role {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}
```

**CRO Points** :
- Years in business / expertise credibility prominent
- Client case studies avec results metrics
- Testimonials from C-level executives
- "Schedule consultation" CTA
- Free whitepaper / resource download

#### **Startup Tech**

**Direction Artistique** : Disruptive, future-forward, high energy

```css
.startup-hero {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  color: white;
  padding: 120px 40px;
  position: relative;
  overflow: hidden;
}

.startup-hero::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.3), transparent);
  border-radius: 50%;
}

.startup-hero-content {
  position: relative;
  z-index: 2;
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.startup-hero h1 {
  font-family: 'Clash Display', sans-serif;
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.startup-problem-solution {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  padding: 80px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.startup-feature-showcase {
  padding: 100px 40px;
  background: var(--color-bg);
}

.startup-feature-showcase h2 {
  text-align: center;
  margin-bottom: 3rem;
}

.startup-feature-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 800px;
  margin: 0 auto;
}

.startup-feature-item {
  padding: 1.5rem;
  border-left: 4px solid var(--color-primary);
  padding-left: 2rem;
}

.startup-cta-section {
  text-align: center;
  padding: 60px 40px;
  background: var(--color-primary);
  color: white;
}

.startup-cta-button {
  display: inline-block;
  padding: 12px 32px;
  background: white;
  color: var(--color-primary);
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.startup-cta-button:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}
```

**CRO Points** :
- Funding stage / investor credibility visible
- Product demo video prominent
- Waitlist signup if pre-launch
- "Join the revolution" energy

#### **Finance & Fintech**

**Direction Artistique** : Serious, transparent, security-focused

```css
.finance-hero {
  background: var(--color-bg);
  padding: 80px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.finance-chart-section {
  padding: 80px 40px;
  background: var(--color-bg-alt);
}

.finance-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.finance-chart-item {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  border: 1px solid var(--color-border);
}

.finance-security-badges {
  display: flex;
  justify-content: center;
  gap: 2rem;
  padding: 3rem 40px;
  flex-wrap: wrap;
}

.finance-security-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.finance-security-badge-icon {
  width: 60px;
  height: 60px;
  background: var(--color-primary-muted);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.finance-pricing-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 2rem;
}

.finance-pricing-table th,
.finance-pricing-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.finance-pricing-table th {
  background: var(--color-bg-muted);
  font-weight: 600;
}
```

**CRO Points** :
- Transparency sur les fees (pas de frais cachés messaging)
- Security certifications prominentes
- Risk disclosure clair mais accessible
- "Open an account" CTA clear et simple

#### **Food & Beverage**

**Direction Artistique** : Warm, sensory, appetite-appealing

```css
.f-b-hero {
  background: linear-gradient(135deg, #f0e4d7 0%, #faf3e8 100%);
  padding: 80px 40px;
  text-align: center;
}

.f-b-hero-image {
  max-width: 600px;
  margin: 2rem auto 0;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.f-b-menu-section {
  padding: 80px 40px;
}

.f-b-menu-category {
  margin-bottom: 4rem;
}

.f-b-menu-category-title {
  font-family: 'Unbounded', sans-serif;
  font-size: 2rem;
  margin-bottom: 2rem;
  color: var(--color-text);
}

.f-b-menu-items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.f-b-menu-item {
  padding: 1.5rem;
  border-radius: 12px;
  background: white;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.f-b-menu-item:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.f-b-menu-item-title {
  font-weight: 600;
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
}

.f-b-menu-item-description {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.f-b-menu-item-price {
  font-weight: 700;
  color: var(--color-primary);
}

.f-b-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 80px 40px;
}

.f-b-gallery-item {
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 12px;
  cursor: pointer;
  position: relative;
}

.f-b-gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.f-b-gallery-item:hover img {
  transform: scale(1.1);
}

.f-b-order-cta {
  position: sticky;
  bottom: 0;
  background: var(--color-primary);
  color: white;
  padding: 1.5rem;
  text-align: center;
  font-weight: 600;
}
```

**CRO Points** :
- Menu clarity (prix, descriptions clairs)
- Online ordering intégré ou obvious link
- Delivery options prominentes
- Food photography haute-qualité, styled

#### **Santé & Wellness**

**Direction Artistique** : Calm, trustworthy, natural

```css
.wellness-hero {
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
  padding: 100px 40px;
  text-align: center;
}

.wellness-feature-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  padding: 80px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.wellness-feature-card {
  padding: 2rem;
  border-radius: 16px;
  background: white;
  border: 1px solid var(--color-border);
  text-align: center;
  transition: all 0.3s ease;
}

.wellness-feature-card:hover {
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.wellness-feature-icon {
  width: 80px;
  height: 80px;
  background: var(--color-primary-muted);
  border-radius: 50%;
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wellness-breathing-animation {
  width: 80px;
  height: 80px;
  border: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: breathe 4s ease-in-out infinite;
  margin: 2rem auto;
}

@keyframes breathe {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.3);
  }
}

.wellness-doctor-bios {
  padding: 80px 40px;
  background: var(--color-bg-alt);
}

.wellness-doctor-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.wellness-doctor-card {
  text-align: center;
}

.wellness-doctor-image {
  width: 100%;
  aspect-ratio: 1;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.wellness-doctor-credentials {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.wellness-appointment-cta {
  text-align: center;
  padding: 60px 40px;
}

.wellness-appointment-button {
  display: inline-block;
  padding: 12px 32px;
  background: var(--color-primary);
  color: white;
  border-radius: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
}

.wellness-appointment-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}
```

**CRO Points** :
- Doctor credentials prominentes
- Patient testimonials + before/after
- Transparent pricing et insurance info
- Appointment booking simple et accessible

#### **Fashion & Mode**

**Direction Artistique** : Elegant, trend-forward, aspirational

```css
.fashion-hero {
  background: black;
  color: white;
  padding: 120px 40px;
  text-align: center;
}

.fashion-hero-image {
  max-width: 600px;
  margin: 2rem auto;
  aspect-ratio: 3 / 4;
  background: var(--color-bg);
  border-radius: 12px;
  overflow: hidden;
}

.fashion-lookbook-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 80px 40px;
}

.fashion-lookbook-item {
  position: relative;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  border-radius: 12px;
  cursor: pointer;
}

.fashion-lookbook-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.fashion-lookbook-item:hover img {
  transform: scale(1.08);
}

.fashion-lookbook-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
  padding: 1.5rem;
  color: white;
  transform: translateY(100%);
  transition: transform 0.3s ease;
}

.fashion-lookbook-item:hover .fashion-lookbook-overlay {
  transform: translateY(0);
}

.fashion-collection-hero {
  padding: 80px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.fashion-collection-title {
  font-family: 'Fraunces', serif;
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.fashion-size-guide {
  margin-top: 3rem;
}

.fashion-size-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.fashion-size-table th,
.fashion-size-table td {
  padding: 1rem;
  text-align: center;
  border-bottom: 1px solid var(--color-border);
}

.fashion-size-table th {
  background: var(--color-bg-muted);
  font-weight: 600;
}
```

**CRO Points** :
- Lookbook avec clear styling inspiration
- Size guides detailed
- Color/style variants visible pour chaque item
- "Shop now" obvious per piece

#### **Immobilier**

**Direction Artistique** : Trustworthy, showcase-focused, aspirational

```css
.real-estate-hero {
  height: 100vh;
  background-image: url('flagship-property.jpg');
  background-size: cover;
  background-position: center;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  text-align: center;
}

.real-estate-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
}

.real-estate-hero-content {
  position: relative;
  z-index: 2;
}

.real-estate-properties-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
  padding: 80px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.real-estate-property-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.real-estate-property-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.real-estate-property-image {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-bg-muted);
}

.real-estate-property-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.real-estate-property-card:hover .real-estate-property-image img {
  transform: scale(1.05);
}

.real-estate-property-info {
  padding: 1.5rem;
}

.real-estate-property-price {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.real-estate-property-address {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.real-estate-property-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin: 1rem 0;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  font-size: 0.875rem;
}

.real-estate-property-detail-item {
  text-align: center;
}

.real-estate-property-detail-label {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
}

.real-estate-property-detail-value {
  font-weight: 600;
}

.real-estate-property-cta {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease;
  margin-top: 1rem;
}

.real-estate-property-cta:hover {
  background: var(--color-primary-dark);
}

.real-estate-map-section {
  padding: 80px 40px;
  background: var(--color-bg-alt);
}

.real-estate-map {
  width: 100%;
  height: 500px;
  border-radius: 12px;
  overflow: hidden;
}

.real-estate-financing {
  padding: 80px 40px;
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.real-estate-financing-calculator {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  background: var(--color-bg-muted);
  border-radius: 12px;
}

.real-estate-financing-input {
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-family: var(--font-body);
}

.real-estate-financing-result {
  margin-top: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.real-estate-financing-result-label {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.real-estate-financing-result-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-primary);
}
```

**CRO Points** :
- Property galleries with high-res imagery
- Virtual tours 360° if available
- Mortgage calculator for financing clarity
- Agent bios + photo gallery
- Schedule showing CTA prominent

---

## RÉSUMÉ: CHECKLIST ANTI-SLOP

Avant de finaliser un site, vérifier:

- [ ] **Fonts** : Pas de Inter, Roboto, Arial, Open Sans, Lato, Montserrat, system-ui
- [ ] **Layout** : Pas de grilles parfaitement symétriques; asymétrie intentionnelle + negative space
- [ ] **Gradients** : Pas de violet/bleu fade sur blanc; gradients mesh complexes OU minimalistes épurés
- [ ] **Copy** : Pas de "bienvenue", "découvrez", "nous sommes passionnés"; voice distinctif par client
- [ ] **Animations** : Pas juste fade-in fade-out; scroll animations + hover states + signature element
- [ ] **Palette** : Pas de 3 couleurs plat; structure CSS custom properties, contraste WCAG AA min
- [ ] **Éléments Signature** : Au minimum 1 élément "wow" qui serve la message
- [ ] **Direction Artistique** : Alignée avec secteur d'activité ET distincte (pas template)
- [ ] **Performance** : Animations GPU-accelerated (transform/opacity), no layout thrashing
- [ ] **Accessibilité** : Contraste texte, reduced-motion respect, navigation keyboard
- [ ] **CRO** : CTA clair, couleur contraste, copy spécifique au client, social proof intégré

**SI tu passes cette checklist**, tu as un site distinctif, INTENTIONNEL, et anti-AI-slop.

---

## FIN

Ce Design System est l'armature du GSG. Elle doit piloter chaque décision design de l'IA — jamais de déviations vers le générique.

**L'objectif final** : générer des sites qui pourraient être reconnus comme "produit d'excellence intentionnelle" plutôt que "généré par IA".
