# GSG V15 — Doctrine Direction Artistique

## Principe fondamental

La DA d'une LP générée par GSG est le résultat d'une **fusion 3 sources** :

```
Source 1 : Brand Identity (crawl CSS réel)     → PRIME pour palette + polices
Source 2 : Archétype Jung (v143.archetype_macro) → Mood + techniques visuelles
Source 3 : Design Rules R8-R11 (V15)            → Contraintes obligatoires
```

## 1. Brand Identity (source #1 — PRIORITAIRE)

Extraite automatiquement par `site_intelligence.py` depuis le CSS du site client.

### Ce qui est extrait
- **Palette** : couleurs ordonnées par fréquence + rôle (primary/accent/background/text)
- **Polices** : heading font + body font (non-system, brand-specific)
- **Style mood** : descripteurs (organic/geometric, flat/elevated, gradient-rich, dynamic)
- **Logos** : URLs des logos détectés dans le DOM

### Règle absolue
> La palette et les polices du CLIENT priment TOUJOURS.
> Si le crawl a trouvé `geomanist` et `#f87171`, c'est ça qu'on utilise.
> L'archétype ne REMPLACE JAMAIS les couleurs/polices du crawl.

### Quand le crawl ne suffit pas
- Si `palette.primary` est null → le CSS est peut-être chargé dynamiquement. Tenter ghost_fetch.
- Si seules des system fonts sont détectées → le client utilise peut-être des web fonts chargées par JS. Vérifier les Google Fonts links.
- Si aucune couleur accent n'est trouvée → utiliser la palette de l'archétype en FALLBACK.

## 2. Archétype Jung (source #2 — MOOD + TECHNIQUES)

Défini dans `lp-front/references/design_archetypes.md` et stocké dans `v143.archetype_macro`.

### Les 12 archétypes

| # | Archétype | Mood keywords | Techniques typiques |
|---|-----------|---------------|---------------------|
| 1 | Innocent | pur, simple, honnête | formes douces, coins ronds, blanc dominant, illustrations naïves |
| 2 | Explorer | aventurier, libre, découverte | compositions asymétriques, photos grand angle, grains de texture |
| 3 | Sage | expert, fiable, analytique | grilles strictes, serif élégant, espacement généreux |
| 4 | Hero | courage, performance, dépassement | bold typo, contrastes forts, angles dynamiques, dark sections |
| 5 | Outlaw | rebelle, disruptif, audacieux | layouts cassés, typo lourde, couleurs vives, animations brutales |
| 6 | Magician | transformation, innovation, wow | gradients, glass-morphism, animations fluides, dark luxe |
| 7 | Regular | accessible, authentique, inclusif | design clean, photos vraies, tons chauds, espacement confortable |
| 8 | Lover | désir, beauté, exclusivité | serif élégant, photos studio, or/rose, animations sensuelles |
| 9 | Jester | fun, coloré, inattendu | couleurs saturées, animations ludiques, illustrations, ruptures |
| 10 | Caregiver | chaleur, protection, confiance | coins très ronds, couleurs douces, illustrations organiques |
| 11 | Creator | imagination, artisanat, originalité | typo créative, mises en page uniques, textures riches |
| 12 | Ruler | autorité, premium, excellence | serif majestueux, dark bg, or/navy, espacement luxueux |

### Archétypes composites
Les clients ont souvent 2 archétypes (ex: Caregiver × Innocent pour Japhy).
→ Prendre le mood dominant du premier, les techniques du second.

### Ce que l'archétype NE fournit PAS
- ❌ Les couleurs exactes (c'est le crawl qui décide)
- ❌ Les polices exactes (c'est le crawl qui décide)
- ❌ Les données factuelles (c'est site_intel.json qui décide)

## 3. Design Rules V15 (source #3 — OBLIGATOIRES)

Définies dans `lp-front/references/design_rules.md`, sections R8-R11.

| Règle | Nom | Obligatoire |
|-------|-----|-------------|
| R8 | Texture & profondeur | OUI — grain/noise SVG 2-5%, gradient mesh, blobs organiques, ombres longues |
| R9 | Overflow & débordement | OUI — ≥1 élément en negative margin ou absolute positioning par LP |
| R10 | Section immersive | OUI — ≥1 section dark si LP a 6+ sections |
| R11 | Séparateurs organiques | OUI — wave SVG, clip-path, arc, ou élément bridging entre sections |

## 4. Résolution DA — Algorithme

```
INPUT : brand_identity (crawl) + archetype_macro (v143) + design_rules (R8-R11)

1. PALETTE
   if brand_identity.palette.primary is not None:
       palette = brand_identity.palette  # ← CLIENT PRIME
   else:
       palette = archetype.suggested_palette  # ← fallback

2. FONTS
   if brand_identity.fonts.heading_font is not None:
       heading = brand_identity.fonts.heading_font
       body = brand_identity.fonts.body_font or heading
   else:
       heading = archetype.suggested_heading_font
       body = archetype.suggested_body_font

3. MOOD
   mood_words = brand_identity.style_mood.descriptors + archetype.mood_keywords
   → prendre les 3 plus distinctifs

4. TECHNIQUES
   techniques = archetype.techniques + R8 + R9 + R10 + R11
   → appliquer toutes

5. OUTPUT → DA brief section pour lp-front
```

## 5. Erreurs passées (à ne JAMAIS reproduire)

### Erreur V14 v1 — Japhy
- **Problème** : design plat + fondateur INVENTÉ (Axel/Pierre au lieu de Thomas)
- **Cause** : pas de crawl, données inventées, archétype utilisé pour les couleurs
- **Fix** : crawl obligatoire, palette du client prime, jamais inventer

### Erreur V15 v1 — Japhy (corrigée)
- **Problème** : LP magnifique 119/120 mais palette inventée (#1B4332 vert forêt + terracotta)
- **Cause** : archétype Caregiver×Innocent utilisé pour choisir les couleurs au lieu du crawl
- **Fix** : DA extraction module créé, palette réelle (#f87171 coral, #9bcbeb bleu) priorisée
