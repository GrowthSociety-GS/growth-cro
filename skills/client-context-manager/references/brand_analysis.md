# Brand Analysis — Processus d'extraction automatique de marque

## Objectif

Quand une URL client est fournie, extraire automatiquement toutes les données de marque exploitables pour alimenter le Brand Context et le Design Engine du GSG.

---

## Pipeline d'extraction

### Étape 1 — Fetch & Parse

**Actions :**
1. Récupérer le HTML de la page d'accueil
2. Récupérer les CSS (inline + external stylesheets)
3. Identifier le framework/CMS (WordPress, Shopify, Webflow, custom...)
4. Extraire la structure de la page

**Données extraites :**
- Balises meta (title, description, og:image)
- Structure headings (H1, H2, H3)
- Texte complet (copy visible)
- Images (logos, hero, produits)
- Liens navigation
- Footer (mentions légales, social links)

### Étape 2 — Extraction de palette

**Méthode :**
1. Parser les CSS pour les propriétés `color`, `background-color`, `border-color`
2. Identifier les CSS custom properties (`--primary`, `--brand-color`, etc.)
3. Analyser les couleurs inline dans le HTML
4. Extraire les couleurs dominantes des images (logo, hero) si possible

**Classification :**
```
Primaire     → La couleur la plus utilisée dans les CTAs + éléments d'accent
Secondaire   → La seconde couleur d'accent la plus fréquente
Background   → La couleur de fond principale du body
Text         → La couleur de texte principale
CTA          → La couleur du bouton d'action principal (peut = primaire)
Accent(s)    → Couleurs complémentaires utilisées ponctuellement
```

**Validation :**
- Vérifier le contraste WCAG AA entre texte et fond
- Identifier si la palette est cohérente ou désordonnée
- Détecter les couleurs "parasites" (non intentionnelles)

### Étape 3 — Extraction typographique

**Méthode :**
1. Parser `font-family` dans les CSS
2. Identifier Google Fonts (link tags ou @import)
3. Identifier Adobe Fonts (Typekit)
4. Identifier les fonts custom (@font-face)

**Classification :**
```
Display      → Font utilisée dans les H1/H2 (titres)
Body         → Font utilisée dans les paragraphes
UI/Accent    → Font utilisée dans les boutons/labels (si différente)
```

**Anti-patterns à signaler :**
- Plus de 3 familles de fonts = incohérence
- System fonts uniquement = pas de personnalité
- Fonts AI-slop blacklistées (Inter, Roboto, Arial) = recommander un upgrade

### Étape 4 — Analyse du ton de voix

**Méthode :**
Analyser le copy extrait pour déterminer les 5 axes :

1. **Formel ↔ Casual** (1-10)
   - Indices formels : vouvoiement, phrases longues, jargon technique, pas de contractions
   - Indices casual : tutoiement, phrases courtes, humour, émojis, exclamations

2. **Technique ↔ Accessible** (1-10)
   - Indices techniques : termes spécialisés, specs, données chiffrées complexes
   - Indices accessibles : analogies, "en clair", simplification

3. **Premium ↔ Populaire** (1-10)
   - Indices premium : vocabulaire rare, sous-texte, minimalisme verbal
   - Indices populaire : superlatifs, promo, urgence, langage direct

4. **Sérieux ↔ Playful** (1-10)
   - Indices sérieux : factuel, sobre, pas d'émojis, pas de jeux de mots
   - Indices playful : émojis, jeux de mots, ton léger, interpellation directe

5. **Corporate ↔ Human** (1-10)
   - Indices corporate : "nous", 3ème personne, langage institutionnel
   - Indices human : "je/on", storytelling personnel, vulnérabilité assumée

### Étape 5 — Registre d'ambiance

Mapper le résultat de l'analyse (palette + typo + ton + layout) vers l'un des 8 registres du Design Engine v2.0 :

| Registre | Signaux |
|----------|---------|
| Luxe Raffiné | Palette sombre ou neutre, serif élégant, beaucoup d'espace, photos full-bleed |
| Organique Naturel | Verts/terreux, formes organiques, photos nature, tons chaleureux |
| Tech Sharp | Bleus/gris, sans-serif géométrique, grids stricts, angles nets |
| Playful Accessible | Couleurs vives, formes arrondies, illustrations, ton léger |
| Brutalist Raw | Contrastes forts, typo bold, layout cassé, pas de décoration |
| Minimal Suisse | Beaucoup de blanc, grille stricte, typo neutre mais soignée, pas d'effets |
| Éditorial Magazine | Hiérarchie typo forte, colonnes, grandes images, chapô |
| Dark Premium | Fond sombre, accents lumineux, effets glow/blur, atmosphère immersive |

**Si aucun registre ne correspond** → Créer une description custom du style visuel.

### Étape 6 — Synthèse Brand Context

Compiler toutes les extractions en un objet `brand` structuré (format défini dans context_schema.md).

---

## Cas spéciaux

### Client sans site web (pré-lancement)
- Pas d'extraction automatique possible
- Poser les questions d'enrichissement manuellement
- Proposer un registre d'ambiance basé sur le secteur + la description verbale

### Client avec site web de mauvaise qualité
- Extraire quand même mais signaler les incohérences
- Proposer des améliorations de brand dans le contexte
- Ne PAS reproduire les défauts dans les générations GSG

### Client avec charte graphique fournie
- La charte fournie PRIME sur l'extraction automatique
- L'extraction sert de validation / complément
- Signaler les écarts entre la charte et l'implémentation actuelle du site

---

## Qualité de l'extraction

### Scoring de confiance

Chaque donnée extraite reçoit un score de confiance :
- **High** (90%+) : Donnée explicitement présente (couleur CSS, font-family déclarée)
- **Medium** (60-89%) : Donnée inférée avec bonne confiance (ton de voix, registre d'ambiance)
- **Low** (< 60%) : Donnée devinée, à valider absolument (concurrents, persona)

### Affichage
Toujours indiquer le niveau de confiance à l'utilisateur :
- High → Présenté comme fait
- Medium → "J'ai détecté..." (présentation assurée mais modifiable)
- Low → "Il me semble que..." (demande explicite de validation)
