# MODULE AURA V16 — Aesthetic Universal Reasoning Architecture

> Source de vérité pour le moteur DA computationnel du GSG.
> AURA ne choisit pas un style — il CALCULE une esthétique.

---

## 0. Philosophie

AURA est un **compilateur d'esthétique**. Il prend des inputs (URL client, inspirations, brief minimal) et produit des design tokens mathématiquement cohérents, informés par les meilleurs sites au monde, sans jamais copier ni se répéter.

**Trois principes fondateurs :**

1. **L'esthétique se calcule, elle ne se choisit pas.** Chaque valeur CSS (padding, color, shadow, animation-timing) est dérivée d'un système mathématique (nombre d'or, théorie des couleurs, physique du mouvement), pas piochée dans une liste.

2. **L'inspiration traverse les catégories.** Un site de croquettes peut emprunter la profondeur de Stripe et la chaleur d'Aesop. Le matching se fait par intention esthétique, jamais par secteur business.

3. **Chaque output est unique.** Le système anti-répétition garantit que deux clients similaires ne recevront jamais le même design. L'authenticité naît de la combinaison unique d'ingrédients, pas d'un template customisé.

---

## 1. Les 3 Modes d'Entrée

Tous les modes convergent vers le même pipeline AURA. La différence est la source des inputs.

### Mode A — Client Existant (URL du site)

```
Input  : URL du site client (+ optionnel: URL plateforme Ads Society)
Process: ghost_capture → JS Design Extractor → Haiku DA Analysis
Output : brand_dna.json (ADN de la marque existante)
Rôle   : AURA AUGMENTE l'ADN sans le trahir
```

Le client a déjà une identité. AURA l'extrait, la comprend, et la pousse vers son meilleur potentiel. Les couleurs du client sont sacrées (sauf si objectivement problématiques — contraste WCAG insuffisant). Les fonts peuvent être upgradées si elles sont génériques. Le spacing, la profondeur, le motion sont recalculés.

**Plus tard** : connexion à Ads Society pour récupérer la charte graphique complète (palette officielle, fonts, guidelines). L'URL client + Ads Society = double source de vérité qui se valident mutuellement.

### Mode B — Création Pure (from scratch)

```
Input  : Smart Intake (3-5 questions) + optionnel: jusqu'à 3 URLs d'inspiration
Process: Intake → Vecteur esthétique → AURA Compute (+ extraction inspis si fournies)
Output : aura_tokens.json (design system complet généré de zéro)
Rôle   : AURA INVENTE une identité à partir du contexte
```

Pas de site existant. Le client peut fournir :
- **URL Tone of Voice** : un site dont il aime le TON (pas forcément le visuel)
- **URL Visual/Charte** : un site dont il aime le STYLE VISUEL
- **URL Produit/Business** : un site dans le même domaine pour le contexte

Chaque URL est taggée avec l'aspect à extraire. AURA ne prend de chaque inspiration QUE l'aspect demandé et ignore le reste.

Sans inspiration, AURA génère l'esthétique entièrement depuis le vecteur d'intention (Smart Intake + archétype détecté).

### Mode C — Hybride (client + inspirations)

```
Input  : URL client + URLs d'inspiration + Smart Intake
Process: Extraction ADN client + Extraction aspects inspis → Fusion intelligente
Output : aura_tokens.json (ADN client augmenté par les inspirations)
Rôle   : AURA FUSIONNE en résolvant les conflits
```

Règles de fusion :
- **Couleurs** : le client gagne (sauf override explicite)
- **Fonts** : l'inspiration gagne si le client a des fonts génériques (Arial, Roboto...)
- **Layout/Motion/Profondeur** : l'inspiration gagne (c'est généralement ce que le client veut améliorer)
- **Texture/Signature** : synthèse créative (ni l'un ni l'autre — quelque chose de nouveau)

---

## 2. Smart Intake — Le Brief en 5 Questions

Remplace les 15+ questions du brief actuel. Chaque réponse alimente directement le vecteur esthétique.

### Questions Core (obligatoires)

**Q1. Type de page** (1 choix)
```
LP (Landing Page) | Home | PDP (Page Produit) | Pricing | Multi-page | Blog | About
```
→ Impacte : structure sections, densité, longueur

**Q2. Business** (1 choix)
```
E-commerce | SaaS | Service/Agence | Lead Gen | App Mobile | Formation | Autre
```
→ Impacte : CRO patterns, séquence de persuasion, motion profile par défaut

**Q3. Énergie** (échelle 1-5)
```
1 ●○○○○ Calme & Posé    ←→    Dynamique & Audacieux ○○○○● 5
```
→ Impacte : saturation palette, amplitude motion, densité layout, taille typo

**Q4. Tonalité** (échelle 1-5)
```
1 ●○○○○ Premium & Expert  ←→   Accessible & Fun ○○○○● 5
```
→ Impacte : warmth palette, border-radius, font personality, copy register

### Question Optionnelle (recommandée)

**Q5. Registre express** (1 choix ou skip)
```
Minimal | Éditorial | Organique | Tech | Brutalist | Dark | Coloré | Luxe | Skip (AURA décide)
```
→ Impacte : override direct du registre si le client sait ce qu'il veut. Si skip, AURA calcule le registre optimal depuis Q3+Q4.

### Inférences automatiques depuis le Smart Intake

| Input | Inférence |
|-------|-----------|
| E-com + Énergie 4 + Tonalité 4 | Playful DTC → rebonds, couleurs vives, arrondis |
| SaaS + Énergie 2 + Tonalité 1 | Tech Premium → dark possible, grid sharp, glass |
| Service + Énergie 1 + Tonalité 1 | Luxe Corporate → serif, spacing massif, inertie |
| Lead Gen + Énergie 3 + Tonalité 3 | Équilibré → moderne, accessible, efficace |
| E-com + Énergie 1 + Tonalité 2 | Luxe E-com → éditorial, images larges, slow motion |

---

## 3. Le Vecteur Esthétique — L'ADN Numérique d'un Design

Chaque design (qu'il soit un golden site, un rendu validé, ou une intention client) est encodé en un vecteur à 8 dimensions. C'est ça qui permet le matching cross-catégorie.

### Les 8 Dimensions

```python
AESTHETIC_VECTOR = {
    "energy":     float,  # 1-5 : Calme ↔ Dynamique
    "warmth":     float,  # 1-5 : Froid/Technique ↔ Chaud/Humain
    "density":    float,  # 1-5 : Aéré/Minimal ↔ Dense/Riche
    "depth":      float,  # 1-5 : Plat/2D ↔ Profond/Multicouche
    "motion":     float,  # 1-5 : Statique ↔ Très animé
    "editorial":  float,  # 1-5 : Fonctionnel ↔ Éditorial/Magazine
    "playful":    float,  # 1-5 : Sérieux ↔ Ludique/Fun
    "organic":    float,  # 1-5 : Géométrique/Sharp ↔ Organique/Courbes
}
```

### Calcul depuis le Smart Intake

```python
def intake_to_vector(energy, tonality, business, registre=None):
    """Convertit les réponses du Smart Intake en vecteur esthétique."""
    
    # Base depuis les sliders
    v = {
        "energy": energy,
        "warmth": tonality * 0.7 + (1 if business in ["ecom", "food"] else 0),
        "density": 3.0,  # neutre par défaut
        "depth": 3.0,
        "motion": energy * 0.8,
        "editorial": max(1, 5 - energy),  # inverse de l'énergie
        "playful": tonality * 0.6,
        "organic": tonality * 0.5 + (1 if business in ["wellness", "food"] else 0),
    }
    
    # Modifiers par business type
    BUSINESS_MODIFIERS = {
        "saas":      {"depth": +1.0, "density": +0.5, "organic": -1.0},
        "ecom":      {"density": +1.0, "motion": +0.5},
        "luxury":    {"density": -1.5, "editorial": +1.5, "depth": +1.0, "motion": -0.5},
        "leadgen":   {"density": -0.5, "editorial": +0.5},
        "app":       {"playful": +0.5, "motion": +0.5, "organic": +0.5},
        "formation": {"warmth": +0.5, "editorial": +0.5},
    }
    
    # Override direct si registre choisi
    REGISTRE_OVERRIDES = {
        "minimal":   {"density": 1.5, "depth": 2.0, "motion": 2.0, "editorial": 3.5},
        "editorial": {"editorial": 5.0, "density": 2.0, "depth": 3.5},
        "organique": {"organic": 5.0, "warmth": 4.0, "depth": 3.5},
        "tech":      {"organic": 1.0, "depth": 4.5, "warmth": 1.5},
        "brutalist": {"organic": 1.0, "playful": 1.0, "depth": 1.5, "editorial": 4.5, "energy": 4.0},
        "dark":      {"depth": 4.5, "warmth": 1.5, "energy": 3.5},
        "colore":    {"playful": 4.5, "warmth": 4.0, "energy": 4.0},
        "luxe":      {"density": 1.0, "depth": 4.0, "editorial": 4.5, "motion": 2.0, "warmth": 2.5},
    }
    
    # Appliquer modifiers et clamp [1, 5]
    # ... (voir aura_compute.py pour l'implémentation complète)
    
    return v
```

### Calcul depuis un Site Capturé (golden ou client)

```python
def site_to_vector(design_dna: dict) -> dict:
    """Convertit un design_dna.json en vecteur esthétique."""
    
    # Analyse des couleurs → warmth
    warmth = color_temperature(design_dna["palette"]["dominant_colors"])
    
    # Analyse du spacing → density
    density = spacing_density(design_dna["spacing"]["avg_section_padding"])
    
    # Analyse des shadows → depth
    depth = shadow_depth(design_dna["shadows"]["layers_count"], design_dna["shadows"]["max_blur"])
    
    # Analyse des animations → motion
    motion = animation_intensity(design_dna["animations"]["count"], design_dna["animations"]["avg_duration"])
    
    # Analyse du layout → editorial
    editorial = layout_asymmetry(design_dna["layout"]["grid_type"], design_dna["layout"]["overlap_count"])
    
    # Analyse des border-radius → organic
    organic = radius_organicity(design_dna["radii"]["avg"], design_dna["radii"]["max"])
    
    # Analyse des fonts → playful vs serious
    playful = font_personality(design_dna["typography"]["display_font"], design_dna["typography"]["body_font"])
    
    # Analyse globale → energy
    energy = composite_energy(motion, density, design_dna["palette"]["saturation_avg"])
    
    return {
        "energy": energy, "warmth": warmth, "density": density, "depth": depth,
        "motion": motion, "editorial": editorial, "playful": playful, "organic": organic,
    }
```

### Distance entre deux vecteurs

```python
def aesthetic_distance(v1: dict, v2: dict) -> float:
    """Distance euclidienne pondérée entre deux vecteurs esthétiques."""
    WEIGHTS = {
        "energy": 1.0, "warmth": 1.2, "density": 0.8, "depth": 1.0,
        "motion": 0.7, "editorial": 1.0, "playful": 1.1, "organic": 0.9,
    }
    return math.sqrt(sum(
        WEIGHTS[k] * (v1[k] - v2[k])**2 for k in WEIGHTS
    ))
```

---

## 4. AURA Compute — Le Calculateur de Design Tokens

### 4.1 Échelle Modulaire φ (Nombre d'Or)

Tous les spacings et font sizes dérivent du nombre d'or (φ ≈ 1.618).

```python
PHI = 1.618033988749895
BASE_UNIT = 8  # px

def phi_scale(base=BASE_UNIT, steps=8):
    """Génère une échelle modulaire basée sur φ."""
    scale = []
    for i in range(-2, steps):
        scale.append(round(base * (PHI ** i)))
    return scale
    # Exemple: [3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

def spacing_tokens(base=BASE_UNIT):
    """Génère les tokens de spacing."""
    s = phi_scale(base, 8)
    return {
        "3xs": f"{s[0]}px",   # ~3px
        "2xs": f"{s[1]}px",   # ~5px
        "xs":  f"{s[2]}px",   # ~8px
        "sm":  f"{s[3]}px",   # ~13px
        "md":  f"{s[4]}px",   # ~21px
        "lg":  f"{s[5]}px",   # ~34px
        "xl":  f"{s[6]}px",   # ~55px
        "2xl": f"{s[7]}px",   # ~89px
        "3xl": f"{s[8]}px",   # ~144px
        "4xl": f"{s[9]}px",   # ~233px
    }

def type_scale(base_rem=1.0):
    """Génère l'échelle typographique basée sur φ."""
    return {
        "xs":       f"{base_rem / PHI / PHI:.3f}rem",   # ~0.382rem
        "sm":       f"{base_rem / PHI:.3f}rem",          # ~0.618rem
        "base":     f"{base_rem:.3f}rem",                 # 1rem
        "md":       f"{base_rem * 1.125:.3f}rem",         # 1.125rem
        "lg":       f"{base_rem * PHI * 0.75:.3f}rem",    # ~1.214rem
        "xl":       f"{base_rem * PHI:.3f}rem",            # ~1.618rem
        "2xl":      f"{base_rem * PHI * PHI * 0.6:.3f}rem",# ~1.571rem
        "3xl":      f"{base_rem * PHI * PHI:.3f}rem",     # ~2.618rem
        "display":  f"{base_rem * PHI * PHI * PHI * 0.7:.3f}rem", # ~2.962rem
        "hero":     f"clamp(2.5rem, 8vw, {base_rem * PHI**3:.1f}rem)", # responsive
    }
```

### 4.2 Chromatisme Psychologique

La palette n'est pas choisie — elle est DÉRIVÉE de la couleur primaire + le vecteur esthétique.

```python
def compute_palette(primary_hex: str, vector: dict) -> dict:
    """Calcule une palette complète depuis la couleur primaire et le vecteur."""
    
    primary_hsl = hex_to_hsl(primary_hex)
    h, s, l = primary_hsl
    
    warmth = vector["warmth"]
    energy = vector["energy"]
    depth = vector["depth"]
    
    # Secondary : analogique chaud ou froid selon warmth
    if warmth > 3:
        secondary_h = (h + 30) % 360   # analogique chaud
    else:
        secondary_h = (h - 30) % 360   # analogique froid
    secondary_s = s * (0.7 + energy * 0.06)  # saturation liée à l'énergie
    
    # Accent : complémentaire split (tension visuelle)
    accent_h = (h + 150 + random.uniform(-15, 15)) % 360  # split-complémentaire avec variation
    accent_s = min(100, s * 1.2)  # plus saturé que primary
    accent_l = 50 + (energy - 3) * 5  # plus lumineux si énergique
    
    # Background : dérivé de la primary (pas un blanc pur)
    if depth > 3.5:  # site "profond" → peut être dark
        bg_l = 8 + (5 - depth) * 3
        bg_s = s * 0.15
        text_l = 92
    else:
        bg_l = 97 - warmth * 1.5  # légèrement teinté
        bg_s = s * 0.08
        text_l = 12 + warmth * 2  # jamais #000, toujours dérivé de la primary
    
    # Text : JAMAIS #000000 — toujours une "encre profonde" dérivée
    text_h = h
    text_s = s * 0.2
    
    # Muted : version désaturée de la secondary
    muted_s = secondary_s * 0.3
    muted_l = 60
    
    # Proprietary : couleur unique dérivée par triadic
    prop_h = (h + 120) % 360
    prop_s = s * 0.6
    prop_l = 70
    
    return {
        "primary": hsl_to_hex(h, s, l),
        "primary_rgb": hsl_to_rgb_str(h, s, l),
        "secondary": hsl_to_hex(secondary_h, secondary_s, l),
        "accent": hsl_to_hex(accent_h, accent_s, accent_l),
        "bg": hsl_to_hex(h, bg_s, bg_l),
        "bg_alt": hsl_to_hex(h, bg_s, bg_l - 3),
        "text": hsl_to_hex(text_h, text_s, text_l),
        "muted": hsl_to_hex(h, muted_s, muted_l),
        "success": hsl_to_hex(140, 50, 45),
        "proprietary": hsl_to_hex(prop_h, prop_s, prop_l),
        "shadow_tint": f"rgba({hsl_to_rgb_str(h, s * 0.3, 20)}, 0.12)",
    }
```

### 4.3 Physique du Mouvement

Les animations ne sont pas des valeurs CSS arbitraires — elles sont des PROFILS PHYSIQUES.

```python
MOTION_PROFILES = {
    "inertia": {
        # Luxe, calm, silk-like. Slow start, infinitely smooth end.
        "name": "Inertia (Soie)",
        "curve": "cubic-bezier(0.23, 1, 0.32, 1)",
        "duration_base": "0.8s",
        "stagger_delay": "100ms",
        "hover_scale": 1.015,
        "hover_translate_y": "-2px",
        "scroll_reveal": "fade-up",
        "scroll_duration": "1s",
        "best_for_energy": (1, 2.5),
    },
    "smooth": {
        # DTC, wellness, organic. Ample, easy, breathing.
        "name": "Smooth (Respiration)",
        "curve": "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        "duration_base": "0.6s",
        "stagger_delay": "80ms",
        "hover_scale": 1.03,
        "hover_translate_y": "-4px",
        "scroll_reveal": "fade-up",
        "scroll_duration": "0.8s",
        "best_for_energy": (2, 3.5),
    },
    "spring": {
        # SaaS, tech, tools. Fast, precise, slight overshoot.
        "name": "Spring (Précision)",
        "curve": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "duration_base": "0.35s",
        "stagger_delay": "50ms",
        "hover_scale": 1.05,
        "hover_translate_y": "-3px",
        "scroll_reveal": "slide-up",
        "scroll_duration": "0.5s",
        "best_for_energy": (3, 4.5),
    },
    "bounce": {
        # Fun, playful, kids, games. Elastic, joyful.
        "name": "Bounce (Élastique)",
        "curve": "cubic-bezier(0.68, -0.55, 0.27, 1.55)",
        "duration_base": "0.5s",
        "stagger_delay": "60ms",
        "hover_scale": 1.08,
        "hover_translate_y": "-6px",
        "scroll_reveal": "pop-in",
        "scroll_duration": "0.6s",
        "best_for_energy": (4, 5),
    },
    "snap": {
        # Brutalist, editorial, minimal. Sharp, no ease, immediate.
        "name": "Snap (Impact)",
        "curve": "cubic-bezier(0.16, 1, 0.3, 1)",
        "duration_base": "0.25s",
        "stagger_delay": "30ms",
        "hover_scale": 1.0,
        "hover_translate_y": "0px",
        "scroll_reveal": "clip-reveal",
        "scroll_duration": "0.4s",
        "best_for_energy": (3.5, 5),
    },
}

def select_motion_profile(vector: dict) -> dict:
    """Sélectionne le profil motion optimal depuis le vecteur esthétique."""
    energy = vector["energy"]
    playful = vector["playful"]
    editorial = vector["editorial"]
    organic = vector["organic"]
    
    # Score chaque profil
    scores = {}
    for name, profile in MOTION_PROFILES.items():
        lo, hi = profile["best_for_energy"]
        # Distance au range optimal
        if lo <= energy <= hi:
            e_score = 1.0
        else:
            e_score = max(0, 1 - abs(energy - (lo + hi) / 2) * 0.3)
        
        # Bonus contextuels
        bonus = 0
        if name == "bounce" and playful > 3.5: bonus += 0.3
        if name == "inertia" and editorial > 3.5: bonus += 0.3
        if name == "smooth" and organic > 3.5: bonus += 0.3
        if name == "snap" and editorial > 4: bonus += 0.2
        if name == "spring" and organic < 2: bonus += 0.2
        
        scores[name] = e_score + bonus
    
    best = max(scores, key=scores.get)
    return MOTION_PROFILES[best]
```

### 4.4 Profondeur & Texture

```python
def compute_depth_tokens(vector: dict, palette: dict) -> dict:
    """Calcule les tokens de profondeur depuis le vecteur."""
    depth = vector["depth"]
    organic = vector["organic"]
    
    # Border-radius : ratio de courbure, pas valeur fixe
    if organic > 3.5:
        radius_scale = [8, 12, 16, 24, 999]  # arrondi → full pill
    elif organic < 2:
        radius_scale = [0, 2, 4, 6, 8]  # sharp
    else:
        radius_scale = [4, 6, 8, 12, 16]  # modéré
    
    # Shadows : multicouches proportionnelles à depth
    shadow_layers = max(1, round(depth))
    shadows = {
        "sm": _compute_shadow(shadow_layers, 4, palette["shadow_tint"]),
        "md": _compute_shadow(shadow_layers, 12, palette["shadow_tint"]),
        "lg": _compute_shadow(shadow_layers, 24, palette["shadow_tint"]),
        "xl": _compute_shadow(shadow_layers, 48, palette["shadow_tint"]),
    }
    
    # Noise/grain : opacité liée à la profondeur
    noise_opacity = 0.01 + depth * 0.008  # 0.018 → 0.05
    
    # Glass : activé si depth > 3
    glass_enabled = depth > 3
    glass_blur = round(8 + depth * 2)
    
    return {
        "radius": {f"r{i+1}": f"{r}px" for i, r in enumerate(radius_scale)},
        "shadows": shadows,
        "noise_opacity": round(noise_opacity, 3),
        "glass_enabled": glass_enabled,
        "glass_blur": f"{glass_blur}px",
        "glass_saturation": f"{150 + round(depth * 10)}%",
    }

def _compute_shadow(layers: int, base_blur: int, tint: str) -> str:
    """Génère une ombre multicouche."""
    parts = []
    for i in range(layers):
        factor = (i + 1) / layers
        blur = round(base_blur * factor)
        spread = round(-base_blur * 0.1 * (1 - factor))
        y = round(blur * 0.5)
        opacity = 0.04 + (0.08 / layers) * (layers - i)
        parts.append(f"0 {y}px {blur}px {spread}px {tint.replace('0.12', str(round(opacity, 3)))}")
    return ", ".join(parts)
```

### 4.5 Sélection Typographique Intelligente

```python
# Pools de fonts par personnalité — jamais de fonts "AI-slop"
FONT_POOLS = {
    "display_serif_elegant": [
        "Playfair Display", "Fraunces", "DM Serif Display", "Cormorant",
        "Lora", "Recoleta", "Erode", "Zodiak",
    ],
    "display_sans_bold": [
        "Clash Display", "Syne", "Unbounded", "Space Grotesk",
        "Bricolage Grotesque", "Cabinet Grotesk", "Switzer",
    ],
    "display_sans_clean": [
        "General Sans", "Satoshi", "Outfit", "Plus Jakarta Sans",
        "Manrope", "Geist",
    ],
    "display_mono": [
        "Space Mono", "JetBrains Mono", "IBM Plex Mono", "Fira Code",
    ],
    "body_readable": [
        "Plus Jakarta Sans", "Satoshi", "General Sans", "Outfit",
        "Manrope", "Geist", "IBM Plex Sans",
    ],
    "body_serif": [
        "Source Serif 4", "Literata", "Newsreader", "Charter",
    ],
}

# Blacklist absolue — fonts AI-slop
FONT_BLACKLIST = {"Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat", "Poppins", "Nunito"}

def select_typography(vector: dict, memory_recent_fonts: list = None) -> dict:
    """Sélectionne un pairing typographique depuis le vecteur esthétique."""
    
    editorial = vector["editorial"]
    playful = vector["playful"]
    organic = vector["organic"]
    warmth = vector["warmth"]
    energy = vector["energy"]
    
    # Déterminer le pool display
    if editorial > 3.5 and organic > 3:
        pool_key = "display_serif_elegant"
    elif energy > 3.5 and playful > 3:
        pool_key = "display_sans_bold"
    elif organic < 2 and editorial > 3:
        pool_key = "display_mono"
    else:
        pool_key = "display_sans_clean"
    
    # Filtrer les fonts récemment utilisées (anti-répétition)
    available = [f for f in FONT_POOLS[pool_key] if f not in (memory_recent_fonts or [])]
    if not available:
        available = FONT_POOLS[pool_key]  # fallback si toutes utilisées
    
    display_font = random.choice(available)
    
    # Body : toujours lisible, complémentaire au display
    if pool_key.startswith("display_serif"):
        body_pool = "body_readable"  # serif display → sans body
    elif pool_key == "display_mono":
        body_pool = "body_readable"
    else:
        # Sans display → peut aller avec sans body OU serif body
        body_pool = "body_serif" if editorial > 4 else "body_readable"
    
    body_font = random.choice([f for f in FONT_POOLS[body_pool] if f != display_font])
    
    return {
        "display": display_font,
        "body": body_font,
        "accent": "JetBrains Mono" if organic < 2.5 else display_font,
        "letter_spacing_display": "-0.02em" if editorial > 3 else "0em",
        "letter_spacing_body": "0em",
        "letter_spacing_caps": "0.1em",
        "line_height_display": "1.1" if editorial > 3.5 else "1.2",
        "line_height_body": "1.65" if editorial > 3 else "1.6",
    }
```

---

## 5. Golden Design Intelligence — L'Apprentissage par les Meilleurs

### 5.1 Golden Design Profiles

Chaque golden site est profilé avec :
- Son `design_dna.json` (extraction technique depuis le HTML)
- Son `aesthetic_vector` (8 dimensions calculées)
- Ses `techniques[]` (patterns design identifiés avec score)

Stockage : `data/golden/<label>/<page>/design_dna.json`

### 5.2 Matching par Intention Esthétique (pas par catégorie business)

```python
class GoldenDesignBridge:
    """Match un client aux golden sites par proximité esthétique, pas business."""
    
    def __init__(self, golden_dir):
        self.profiles = self._load_all_profiles(golden_dir)
    
    def find_closest(self, target_vector: dict, top_n: int = 5) -> list:
        """Retourne les N golden sites dont le vecteur est le plus proche."""
        distances = []
        for profile in self.profiles:
            dist = aesthetic_distance(target_vector, profile["vector"])
            distances.append((profile, dist))
        distances.sort(key=lambda x: x[1])
        return distances[:top_n]
    
    def find_best_techniques(self, technique_type: str, top_n: int = 3) -> list:
        """Retourne les N meilleures exécutions d'un type de technique, tous sites confondus."""
        all_techniques = []
        for profile in self.profiles:
            for tech in profile.get("techniques", []):
                if tech["type"] == technique_type:
                    all_techniques.append({
                        "site": profile["label"],
                        "page": profile["page"],
                        "category": profile["category"],
                        **tech
                    })
        all_techniques.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_techniques[:top_n]
    
    def get_design_benchmark(self, target_vector: dict) -> dict:
        """Produit le bloc de benchmark pour injection dans le prompt de génération."""
        
        # Match global : les 3 sites les plus proches en intention esthétique
        closest = self.find_closest(target_vector, top_n=3)
        
        # Match technique : les meilleures exécutions par type
        technique_types = ["background", "typography", "depth", "motion", "layout", "texture", "color"]
        best_techniques = {}
        for tt in technique_types:
            best = self.find_best_techniques(tt, top_n=2)
            if best:
                best_techniques[tt] = best
        
        return {
            "philosophy_refs": [
                {
                    "site": p["label"],
                    "category": p["category"],
                    "distance": round(d, 2),
                    "vector": p["vector"],
                    "signature": p.get("signature", ""),
                    "why_matched": _explain_match(target_vector, p["vector"]),
                }
                for p, d in closest
            ],
            "technique_refs": best_techniques,
            "prompt_block": _format_benchmark_prompt(closest, best_techniques),
        }
```

### 5.3 Le Prompt Block Injecté

```python
def _format_benchmark_prompt(closest, techniques):
    """Formate le bloc de benchmark pour injection dans le prompt GSG."""
    lines = ["## GOLDEN DESIGN BENCHMARK (intelligence esthétique cross-catégorie)\n"]
    
    lines.append("### PHILOSOPHIE DA — Sites dont l'ADN esthétique est le plus proche :\n")
    for ref, dist in closest:
        lines.append(f"**{ref['label'].upper()}** ({ref['category']}) — distance esthétique: {dist:.1f}")
        lines.append(f"  Signature : {ref.get('signature', 'N/A')}")
        lines.append(f"  Ce qui fait \"wow\" : {ref.get('wow_factor', 'N/A')}")
        lines.append(f"  Vecteur : energy={ref['vector']['energy']:.1f}, "
                      f"warmth={ref['vector']['warmth']:.1f}, "
                      f"depth={ref['vector']['depth']:.1f}")
        lines.append("")
    
    lines.append("### TECHNIQUES À EMPRUNTER (cross-catégorie, meilleures exécutions) :\n")
    for tt, techs in techniques.items():
        best = techs[0]
        lines.append(f"**{tt.upper()}** → {best['name']} (source: {best['site']}, score: {best['score']}/5)")
        lines.append(f"  Approche CSS : {best.get('css_approach', 'N/A')}")
        lines.append(f"  Pourquoi ça marche : {best.get('why_it_works', 'N/A')}")
        lines.append("")
    
    lines.append("### CONSIGNES :")
    lines.append("- Inspire-toi des TECHNIQUES ci-dessus, pas des STYLES.")
    lines.append("- Ton output doit être aussi impressionnant mais visuellement DIFFÉRENT.")
    lines.append("- Ne copie jamais un layout — invente le tien avec le même niveau d'exécution.")
    lines.append("- Fusionne des techniques de sites DIFFÉRENTS pour créer quelque chose d'inédit.")
    
    return "\n".join(lines)
```

---

## 6. Technique Library — Bibliothèque Vivante Cross-Catégorie

### 6.1 Structure

```json
{
  "version": "1.0.0",
  "updated": "2026-04-18",
  "techniques": [
    {
      "id": "bg_mesh_gradient_01",
      "name": "Animated Mesh Gradient",
      "type": "background",
      "source": {"site": "stripe", "page": "home", "category": "devtools_b2b"},
      "score": 4.5,
      "aesthetic_affinity": {
        "best_when": {"depth": ">3.5", "energy": "<4"},
        "avoid_when": {"density": ">4", "editorial": ">4.5"}
      },
      "css_snippet": "/* ... code CSS complet ... */",
      "why_it_works": "Crée une atmosphère vivante sans distraire. Le mouvement lent suggère la profondeur.",
      "usage_count": 0,
      "last_used": null,
      "compatible_with": ["bg_noise_overlay_01", "depth_glass_card_01"],
      "conflicts_with": ["bg_solid_color_01"]
    }
  ]
}
```

### 6.2 Types de Techniques

| Type | Exemples |
|------|----------|
| `background` | Mesh gradient, noise overlay, dot grid, organic blobs, diagonal lines, geometric patterns |
| `typography` | Gradient text, split reveal, oversized, highlight marker, variable spacing |
| `layout` | Asymmetric split, overlap grid, bento, editorial offset, alternating widths |
| `depth` | Multi-shadow, glass/frost, elevated cards, inner glow, border glow |
| `motion` | Staggered reveal, parallax, magnetic hover, clip-path reveal, counter-scroll |
| `texture` | Perlin noise, grain overlay, paper texture, halftone, mesh distortion |
| `color` | Psychological tinting, shadow coloring, gradient accents, luminance contrast |
| `signature` | Custom cursor, scroll-driven transforms, morphing shapes, interactive particles |

### 6.3 Sélection Intelligente

```python
def select_techniques(vector: dict, technique_library: list, memory_recent: list = None) -> dict:
    """Sélectionne les techniques optimales pour chaque type depuis la library."""
    
    selected = {}
    for tech_type in ["background", "typography", "layout", "depth", "motion", "texture", "color", "signature"]:
        candidates = [t for t in technique_library if t["type"] == tech_type]
        
        # Scorer chaque candidat
        scored = []
        for t in candidates:
            score = t["score"]  # base: qualité intrinsèque
            
            # Bonus : affinité esthétique
            affinity = t.get("aesthetic_affinity", {})
            for cond_key, cond_val in affinity.get("best_when", {}).items():
                op = cond_val[0]  # ">" ou "<"
                threshold = float(cond_val[1:])
                actual = vector.get(cond_key, 3.0)
                if (op == ">" and actual > threshold) or (op == "<" and actual < threshold):
                    score += 0.5
            
            # Malus : anti-affinité
            for cond_key, cond_val in affinity.get("avoid_when", {}).items():
                op = cond_val[0]
                threshold = float(cond_val[1:])
                actual = vector.get(cond_key, 3.0)
                if (op == ">" and actual > threshold) or (op == "<" and actual < threshold):
                    score -= 1.0
            
            # Malus : récemment utilisé (anti-répétition)
            if memory_recent and t["id"] in memory_recent:
                score -= 1.5
            
            scored.append((t, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored:
            selected[tech_type] = scored[0][0]
    
    return selected
```

---

## 7. Self-Learning Loop

### 7.1 Ce qui est appris après chaque génération validée

```json
{
  "id": "render_2026_04_18_001",
  "date": "2026-04-18",
  "client": "japhy",
  "page_type": "home",
  "business": "ecom_dtc",
  
  "input_vector": {"energy": 2.5, "warmth": 4.0, "...": "..."},
  "computed_tokens": {"palette": {"primary": "#2D5A3D"}, "...": "..."},
  
  "decisions": {
    "display_font": "Fraunces",
    "body_font": "Plus Jakarta Sans",
    "motion_profile": "smooth",
    "signature": "gradient mesh botanique + parallax images",
    "techniques_used": ["bg_mesh_gradient_01", "typo_serif_oversized_02", "depth_glass_card_01"],
    "golden_refs_used": ["aesop/home", "glossier/home", "stripe/home"]
  },
  
  "score": {
    "cro": 82, "design": 42, "psycho": 16, "total": 140
  },
  
  "feedback": "client a adoré le calme botanique, a demandé plus de mouvement sur le hero",
  "lessons": ["Pour DTC wellness: le parallax images marche très bien", "Fraunces + Plus Jakarta = combo validé premium organique"]
}
```

### 7.2 Comment la mémoire influence les futures générations

1. **Font rotation** : Les 5 dernières display fonts utilisées sont déprioritisées (pas blacklistées — juste -1.5 score). Force la diversité.

2. **Technique rotation** : Même logique. Si "mesh gradient" a été utilisé 3 fois récemment, les alternatives montent en score.

3. **Pattern reinforcement** : Si un combo (vector proche + technique X) a scoré >135/153, ce combo gagne un bonus pour les futurs vecteurs similaires.

4. **Feedback integration** : Les retours clients sont parsés pour extraire des règles. "Plus de mouvement" → le vecteur motion s'ajuste à +0.5 pour les futurs clients dans un contexte similaire.

5. **Diversity scoring** : Avant de livrer, AURA calcule la distance esthétique entre le nouveau design et les 5 derniers rendus. Si distance < 3.0, il force une variation (change la signature, le motion profile, ou les techniques).

### 7.3 Enrichissement de la Technique Library

Deux sources :

1. **Golden sites** : Chaque nouveau golden site ajouté au registry est profilé et ses techniques extraites → enrichissent la library.

2. **Renders validés** : Quand un render score >130/153 ET le client valide, les techniques utilisées dans ce render sont ajoutées à la library avec tag `source: "own_render"`. Le GSG apprend de ses propres créations réussies.

---

## 8. Output Final — aura_tokens.json

Le résultat de tout le pipeline AURA est un fichier JSON qui contient TOUT ce dont la Phase 3 (Production) a besoin :

```json
{
  "version": "16.0.0",
  "generated_at": "2026-04-18T14:30:00Z",
  "mode": "A",
  
  "concept": "Laboratoire Botanique Vivant",
  "archetype": "caregiver",
  
  "vector": {
    "energy": 2.5, "warmth": 4.0, "density": 2.0, "depth": 4.0,
    "motion": 3.0, "editorial": 3.5, "playful": 2.0, "organic": 4.5
  },
  
  "palette": {
    "primary": "#2D5A3D", "primary_rgb": "45,90,61",
    "secondary": "#D4A76A", "accent": "#E85D3A",
    "bg": "#FAFAF7", "bg_alt": "#F0EDE6",
    "text": "#1A2E1F", "muted": "#8B9A8E",
    "success": "#3D7A4F", "proprietary": "#C9E4D1",
    "shadow_tint": "rgba(45,90,61,0.12)"
  },
  
  "typography": {
    "display": "Fraunces", "body": "Plus Jakarta Sans", "accent": "JetBrains Mono",
    "scale": {"xs": "0.382rem", "sm": "0.618rem", "base": "1rem", "lg": "1.214rem", "xl": "1.618rem", "2xl": "2.618rem", "hero": "clamp(2.5rem, 8vw, 4.2rem)"},
    "letter_spacing_display": "-0.02em", "line_height_display": "1.1",
    "letter_spacing_body": "0em", "line_height_body": "1.65"
  },
  
  "spacing": {
    "3xs": "3px", "2xs": "5px", "xs": "8px", "sm": "13px", "md": "21px",
    "lg": "34px", "xl": "55px", "2xl": "89px", "3xl": "144px"
  },
  
  "motion": {
    "profile": "smooth",
    "curve": "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    "duration_base": "0.6s", "stagger_delay": "80ms",
    "hover_scale": 1.03, "hover_translate_y": "-4px",
    "scroll_reveal": "fade-up", "scroll_duration": "0.8s"
  },
  
  "depth": {
    "radius": {"r1": "8px", "r2": "12px", "r3": "16px", "r4": "24px", "r5": "999px"},
    "shadows": {
      "sm": "0 2px 4px -1px rgba(45,90,61,0.08)",
      "md": "0 4px 8px -2px rgba(45,90,61,0.06), 0 8px 16px -4px rgba(45,90,61,0.04)",
      "lg": "0 6px 12px -3px rgba(45,90,61,0.05), 0 12px 24px -6px rgba(45,90,61,0.04), 0 24px 48px -12px rgba(45,90,61,0.03)"
    },
    "noise_opacity": 0.035,
    "glass_enabled": true, "glass_blur": "16px", "glass_saturation": "190%"
  },
  
  "techniques_selected": {
    "background": "bg_mesh_gradient_organic_01",
    "typography": "typo_serif_oversized_02",
    "layout": "layout_editorial_offset_01",
    "depth": "depth_glass_card_nature_01",
    "motion": "motion_staggered_fade_01",
    "texture": "texture_perlin_warm_01",
    "color": "color_warm_shadow_tint_01",
    "signature": "sig_parallax_botanical_01"
  },
  
  "golden_benchmark": {
    "philosophy_refs": ["aesop/home", "headspace/home"],
    "technique_refs": {"depth": "stripe/home", "texture": "glossier/home", "typography": "sezane/home"}
  },
  
  "css_custom_properties": "/* ... generated CSS variables ... */"
}
```

### CSS Custom Properties (auto-générées)

```css
:root {
  /* Palette */
  --primary: #2D5A3D;
  --primary-rgb: 45,90,61;
  --secondary: #D4A76A;
  --accent: #E85D3A;
  --bg: #FAFAF7;
  --bg-alt: #F0EDE6;
  --text: #1A2E1F;
  --muted: #8B9A8E;
  --success: #3D7A4F;
  
  /* Typography */
  --font-display: 'Fraunces', serif;
  --font-body: 'Plus Jakarta Sans', sans-serif;
  --font-accent: 'JetBrains Mono', monospace;
  --fs-xs: 0.382rem; --fs-sm: 0.618rem; --fs-base: 1rem;
  --fs-lg: 1.214rem; --fs-xl: 1.618rem; --fs-2xl: 2.618rem;
  --fs-hero: clamp(2.5rem, 8vw, 4.2rem);
  --ls-display: -0.02em; --lh-display: 1.1;
  --ls-body: 0em; --lh-body: 1.65;
  
  /* Spacing (φ scale) */
  --sp-3xs: 3px; --sp-2xs: 5px; --sp-xs: 8px; --sp-sm: 13px;
  --sp-md: 21px; --sp-lg: 34px; --sp-xl: 55px; --sp-2xl: 89px; --sp-3xl: 144px;
  
  /* Motion */
  --ease: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --duration: 0.6s;
  --stagger: 80ms;
  
  /* Depth */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-xl: 24px; --radius-full: 999px;
  --shadow-sm: 0 2px 4px -1px rgba(45,90,61,0.08);
  --shadow-md: 0 4px 8px -2px rgba(45,90,61,0.06), 0 8px 16px -4px rgba(45,90,61,0.04);
  --shadow-lg: 0 6px 12px -3px rgba(45,90,61,0.05), 0 12px 24px -6px rgba(45,90,61,0.04), 0 24px 48px -12px rgba(45,90,61,0.03);
  --noise-opacity: 0.035;
  --glass-blur: 16px;
  --glass-saturation: 190%;
}
```

---

## 9. Intégration dans le Pipeline GSG

### Avant (V15)

```
Phase 0 (15 questions) → Phase 1 (brief) → Phase 2 (choix registre manuel + DA) → Phase 3 (code) → Phase 3.5 (eval)
```

### Après (V16 AURA)

```
Smart Intake (3-5 questions) → AURA Extract (si URL) → AURA Compute (tokens) → Golden Design Bridge (benchmark) → Phase 2 (stratégie CRO — le copy est toujours fait ici) → Phase 3 (code guidé par aura_tokens.json) → Phase 3.5 (eval) → Phase 4 (learning)
```

La DA n'est plus "décidée" en Phase 2 — elle est CALCULÉE par AURA avant même que le copy ne commence. Phase 2 se concentre sur la stratégie CRO et le copy, avec la DA déjà prête.

---

## 10. Fichiers du Module AURA

```
skills/growth-site-generator/
├── AURA_ARCHITECTURE.md          ← CE FICHIER (source de vérité)
├── scripts/
│   ├── aura_extract.py           ← Extraction DA depuis URL
│   ├── aura_compute.py           ← Calcul des design tokens
│   ├── golden_design_bridge.py   ← Matching esthétique cross-catégorie
│   └── aura_css_generator.py     ← Tokens → CSS custom properties
├── data/
│   └── technique_library.json    ← Bibliothèque vivante de techniques
├── references/
│   ├── design_engine.md          ← MIS À JOUR avec intégration AURA
│   ├── design_system.md          ← Inchangé (règles anti-slop toujours valides)
│   └── memory.md                 ← MIS À JOUR avec format pattern-based
└── evals/
    └── eval_grid.md              ← Inchangé
```

Golden design profiles :
```
data/golden/<label>/<page>/
├── design_dna.json               ← Extraction technique (couleurs, fonts, shadows, etc.)
├── design_patterns.json          ← Techniques identifiées + scores + vecteur esthétique
└── ... (fichiers existants: capture.json, perception_v13.json, etc.)
```

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-04-18 | 16.0.0 | Architecture AURA V16 initiale |
