# GrowthCRO V9 — Perception Tree Schema

## Philosophie

Le visiteur ne voit pas du HTML. Il voit des **zones visuelles**, des **contrastes**, un **rythme** de sections, et il **scroll**. Le schéma V9 capture la page telle que l'oeil humain la perçoit, pas telle que le DOM la structure.

## Différences V8 → V9

| V8 (actuel) | V9 (Oracle) |
|-------------|-------------|
| H1 texte → regex "has benefit" | H1 texte + position + taille font + contraste fond |
| CTA label → regex "action verb" | CTA label + bbox + area + isolation score + contraste |
| Images count | Images bbox + ratio zone, position relative au H1 |
| "Social proof fold" binaire | Social proof bbox + distance au CTA + visibilité réelle |
| Sections = H2 count | Sections = zones découpées + ordre + hauteur + density |
| Formulaire = field count | Formulaire bbox + champs visibles + friction calculée |

## Schéma capture_v9.json

```json
{
  "meta": {
    "url": "string",
    "label": "string",
    "pageType": "home|pdp|collection|lp_leadgen|pricing|blog|quiz_vsl|checkout",
    "capturedAt": "ISO8601",
    "viewport": { "width": 1440, "height": 900 },
    "viewportMobile": { "width": 390, "height": 844 },
    "totalHeight": 4200,
    "captureLevel": "spatial",
    "engine": "playwright|apify-puppeteer"
  },

  "fold": {
    "desktop": 900,
    "mobile": 844,
    "elementsAboveFold": 12,
    "foldScreenshot": "screenshots/fold_desktop.png"
  },

  "sections": [
    {
      "id": "section_0",
      "type": "hero",
      "bbox": { "x": 0, "y": 0, "w": 1440, "h": 680 },
      "aboveFold": true,
      "elements": [
        {
          "type": "heading",
          "tag": "h1",
          "text": "L'alimentation experte qui change la vie de nos chiens et chats",
          "bbox": { "x": 120, "y": 220, "w": 700, "h": 60 },
          "computedStyle": {
            "fontSize": "48px",
            "fontWeight": "700",
            "lineHeight": "56px",
            "color": "#1a1a2e",
            "backgroundColor": "#ffffff",
            "contrastRatio": 14.2
          }
        },
        {
          "type": "text",
          "tag": "p",
          "subtype": "subtitle",
          "text": "Fabriquée en France. Adaptée selon son profil.",
          "bbox": { "x": 120, "y": 290, "w": 600, "h": 40 },
          "computedStyle": {
            "fontSize": "18px",
            "fontWeight": "400",
            "lineHeight": "28px",
            "color": "#4a4a5a",
            "contrastRatio": 7.1
          }
        },
        {
          "type": "cta",
          "tag": "a",
          "text": "Je découvre",
          "href": "/profile-builder/",
          "bbox": { "x": 120, "y": 350, "w": 220, "h": 52 },
          "area": 11440,
          "computedStyle": {
            "fontSize": "16px",
            "fontWeight": "600",
            "color": "#ffffff",
            "backgroundColor": "#2d5f3d",
            "contrastRatio": 6.8,
            "borderRadius": "8px"
          },
          "isolationScore": 0.35,
          "distanceToNearestCompetitor": 80,
          "isStickyOrFixed": false
        },
        {
          "type": "image",
          "src": "/images/hero-dog.webp",
          "alt": "Chien heureux avec sa gamelle Japhy",
          "bbox": { "x": 800, "y": 100, "w": 540, "h": 500 },
          "naturalWidth": 1200,
          "naturalHeight": 900,
          "format": "webp",
          "ratio": 0.375
        },
        {
          "type": "social_proof",
          "subtype": "trustpilot_widget",
          "text": "★★★★★ 4.7/5 (2000+ avis)",
          "bbox": { "x": 120, "y": 420, "w": 250, "h": 30 },
          "distanceToCta": 70,
          "verified": true
        }
      ],
      "density": {
        "textRatio": 0.25,
        "imageRatio": 0.40,
        "whitespaceRatio": 0.35,
        "elementCount": 5
      },
      "screenshot": "screenshots/section_0_hero.png"
    },
    {
      "id": "section_1",
      "type": "value_proposition",
      "bbox": { "x": 0, "y": 680, "w": 1440, "h": 520 },
      "aboveFold": false,
      "scrollDepthPct": 16.2,
      "elements": ["..."],
      "density": { "textRatio": 0.45, "imageRatio": 0.20, "whitespaceRatio": 0.35, "elementCount": 8 }
    }
  ],

  "spatial_analysis": {
    "heroHeight": 680,
    "heroRatio": 0.162,
    "ctaFoldDistance": -550,
    "firstSocialProofY": 420,
    "firstTestimonialY": 2100,
    "faqY": 3400,
    "lastCtaY": 3800,
    "totalCtaCount": 5,
    "ctaPositions": [350, 1200, 2100, 3000, 3800],
    "ctaSpacing": [850, 900, 900, 800],
    "sectionOrder": ["hero", "value_proposition", "features", "testimonials", "faq", "cta_final"],
    "arcNarrative": {
      "hook": "hero",
      "proof_first": 2100,
      "proof_position": "late",
      "cta_frequency": "adequate",
      "urgency_position": null,
      "closing_strength": "weak"
    },
    "attentionMap": {
      "aboveFold": { "cta_area_pct": 1.7, "noise_count": 2, "focus_score": 0.72 },
      "fullPage": { "avg_section_height": 700, "rhythm_score": 0.65, "density_variance": 0.18 }
    }
  },

  "motion_media": {
    "videos": [
      { "type": "autoplay", "bbox": { "x": 0, "y": 0, "w": 1440, "h": 680 }, "src": "...", "hasAudio": false }
    ],
    "animations": {
      "cssAnimations": 3,
      "jsAnimations": 2,
      "scrollTriggered": 1,
      "totalMotionElements": 6
    },
    "stickyElements": [
      { "type": "header", "bbox": { "x": 0, "y": 0, "w": 1440, "h": 64 }, "containsCta": true },
      { "type": "cta_bar", "bbox": { "x": 0, "y": 836, "w": 390, "h": 64 }, "viewport": "mobile" }
    ]
  },

  "forms": [
    {
      "id": "form_0",
      "action": "/subscribe",
      "method": "POST",
      "bbox": { "x": 200, "y": 3600, "w": 600, "h": 300 },
      "fields": [
        { "type": "email", "label": "Votre email", "required": true, "bbox": { "x": 220, "y": 3650, "w": 400, "h": 44 } },
        { "type": "submit", "label": "S'inscrire", "bbox": { "x": 640, "y": 3650, "w": 140, "h": 44 } }
      ],
      "visibleFieldCount": 1,
      "totalFieldCount": 1,
      "frictionScore": 0.15
    }
  ],

  "navigation": {
    "headerLinks": 7,
    "footerLinks": 15,
    "inlineExitLinks": 3,
    "totalExitLinks": 25,
    "headerHeight": 64,
    "headerIsSticky": true,
    "headerContainsCta": true,
    "attentionRatio": 5.0,
    "primaryCtaInHeader": { "text": "Je découvre", "href": "/profile-builder/" }
  },

  "accessibility": {
    "imgNoAlt": 2,
    "ariaLandmarks": 3,
    "skipLink": true,
    "touchTargetsBelow44": 1,
    "colorContrastFails": [ { "element": ".subtitle", "ratio": 3.2, "required": 4.5 } ],
    "focusIndicatorPresent": true
  },

  "seo": {
    "title": "Japhy – Alimentation saine et naturelle pour chiens et chats",
    "titleLength": 56,
    "metaDesc": "Livraison de croquettes sur-mesure pour chiens et chats",
    "metaDescLength": 54,
    "canonical": "https://japhy.fr/",
    "hasSchema": true,
    "schemaTypes": ["Organization", "Product"],
    "ogTitle": "Japhy – Alimentation saine",
    "ogImage": "/images/og.jpg",
    "h1Count": 1,
    "hreflang": null
  },

  "tracking": {
    "ga4": true,
    "gtm": true,
    "metaPixel": true,
    "tiktokPixel": false,
    "hotjar": false,
    "consent": {
      "cmp": "didomi",
      "blocksCta": false,
      "coverageHeroPct": 15
    }
  },

  "performance": {
    "htmlSizeKb": 142,
    "domNodes": 1847,
    "scriptsCount": 12,
    "imagesCount": 18,
    "lazyLoadedImages": 14,
    "webpAvifUsed": true,
    "criticalCssInlined": false
  },

  "screenshots": {
    "fold_desktop": "screenshots/fold_desktop.png",
    "fold_mobile": "screenshots/fold_mobile.png",
    "full_page": "screenshots/full_page.png",
    "sections": ["screenshots/section_0.png", "screenshots/section_1.png"]
  }
}
```

## Section Detection Algorithm

1. Identifier les "section boundaries" via :
   - Tags sémantiques : `<section>`, `<article>`, `<aside>`, `<main>`
   - Headings H2/H3 qui créent une nouvelle section logique
   - Espacement vertical > 60px entre éléments consécutifs
   - Changement de background-color

2. Pour chaque section :
   - Screenshot de la section
   - Bounding box de tous les éléments enfants pertinents
   - Computed styles du premier heading et du premier CTA
   - Density calculation (text/image/whitespace ratio)
   - Classification automatique : hero, value_proposition, features, testimonials, social_proof, faq, pricing, cta_final, footer

3. Classification hierarchy :
   - Section 0 (y=0 → first section break) = always "hero"
   - Section with FAQ accordion/toggle = "faq"
   - Section with testimonial/review patterns = "testimonials"
   - Section with pricing table/cards = "pricing"
   - Section with only CTA = "cta_final"
   - Everything else = "features" or "value_proposition"

## Arc Narratif Analysis

L'ordre des sections détermine la "story" de la page. L'algorithme vérifie :

| Pattern optimal | Description |
|----------------|-------------|
| Hero → Proof → Features → Testimonials → FAQ → CTA | E-commerce classique |
| Hero → Demo → Features → Pricing → Testimonials → CTA | SaaS |
| Hero → Problem → Solution → Proof → Objections → CTA | Lead gen |

Scoring de l'arc :
- `proof_position`: "early" (before 30% scroll) = +2, "late" (after 50%) = -1
- `cta_frequency`: "adequate" (every 800-1200px) = +2, "sparse" (>1500px gap) = -1
- `closing_strength`: CTA final + urgence + garantie dans les 500px finaux = "strong"

## Isolation Score (pour CTAs)

L'isolation score mesure à quel point un CTA est visuellement isolé :

```
isolation = 1 - (noise_elements_within_200px / total_elements_in_section)
```

- `noise_elements` = liens, boutons secondaires, images distrayantes dans un rayon de 200px
- Score 1.0 = CTA totalement isolé (parfait)
- Score < 0.3 = CTA noyé (critique)

## Migration depuis V8

Le V9 est **rétrocompatible**. Les champs V8 existent toujours dans les sections et éléments. Le scoring V8 fonctionne sur un V9 capture. Le scoring V9 **enrichit** en exploitant les données spatiales quand elles existent (graceful degradation).
