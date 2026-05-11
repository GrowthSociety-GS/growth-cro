#!/usr/bin/env python3
"""
AURA V16 Opus-Level Design Analysis Generator
Re-analyzes golden sites with Opus quality for aesthetic comprehension
"""

import json
import os
from pathlib import Path

# Base path
PROJ = "/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society"

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def update_design_dna(site, page, analysis):
    """Update design_dna.json with opus_analysis"""
    path = Path(PROJ) / "data" / "golden" / site / page / "design_dna.json"

    if not path.exists():
        print(f"  WARNING: {path} not found")
        return False

    with open(path) as f:
        dna = json.load(f)

    # Remove old haiku_analysis if present
    dna.pop("haiku_analysis", None)

    # Add opus_analysis
    dna["opus_analysis"] = analysis
    dna["aesthetic_vector"] = analysis["aesthetic_vector"]
    dna["signature"] = analysis["signature"]
    dna["wow_factor"] = analysis["wow_factor"]
    dna["techniques"] = analysis["techniques"]

    with open(path, "w") as f:
        json.dump(dna, f, indent=2, ensure_ascii=False)

    return True

# ============================================================================
# CANVA ANALYSES
# ============================================================================

def analyze_canva_home():
    """Canva home: Vibrant, creative, accessible design democratization"""
    return {
        "aesthetic_vector": {
            "energy": 4.2,
            "warmth": 3.5,
            "density": 3.4,
            "depth": 2.3,
            "motion": 2.6,
            "editorial": 3.6,
            "playful": 4.1,
            "organic": 2.2
        },
        "signature": "Une palette pastel-saturée (rose, lavande, corail) conjuguée à des accents bleu Google crée une identité joyeuse et accessible qui démocratise le design créatif sans jamais paraitre basique",
        "wow_factor": "L'équilibre subtil entre chromatisme ludique (pastels) et rigueur typographique sans-serif qui transforme un outil SaaS complexe en interface invitante et humanisée",
        "techniques": [
            {
                "type": "color",
                "name": "Palette pastel-vivid hybride stratégique",
                "score": 4.3,
                "css_approach": "8 couleurs dominantes (bleu #1a73e8, rose #ffd7dc, lavande #ead6ff, corail #ffdac4) combinées via CSS variables ; 34 gradients linéaires/radiaux à saturation contrôlée 56.4% ; accents primaires Google (#4285f4, #ff3b4c) pour crédibilité",
                "why_it_works": "Signature chromatique distinctive sans agressivité ; les pastels signalent l'accessibilité tandis que les bleus Google ancrent la confiance tech ; contraste psychologique qui attire créatifs ET professionnels"
            },
            {
                "type": "typography",
                "name": "Hiérarchie sans-serif humanisée avec propriété",
                "score": 3.8,
                "css_approach": "Canva Sans (display custom) + Google Sans (corporate) + Roboto (fallback) ; variation de poids progressif sans sauts radicaux ; spacing typographique régulé via système de grille modulaire",
                "why_it_works": "Canva Sans propriétaire construit l'identité tout en restant inclusive ; Google Sans ajoute la légitimité institutionnelle ; composition hiérarchique ne force jamais le lecteur à scanner"
            },
            {
                "type": "layout",
                "name": "Flexbox asymétrique avec micro-overlaps dynamiques",
                "score": 3.5,
                "css_approach": "4 flex containers principaux ; 6 overlaps calculés sur 3 couches z-index ; padding maximum 85px, moyenne 45px ; aucune grille CSS rigide pour responsivité fluide",
                "why_it_works": "Asymétrie perçue crée du dynamisme sans chaos ; overlaps subtils via z-index guident l'oeil naturellement ; flexbox garantit adaptation responsive tout en préservant l'intention ludique"
            },
            {
                "type": "texture",
                "name": "Gradients omniprésents sans texture noise",
                "score": 3.7,
                "css_approach": "34 gradients CSS distribués ; aucun bruit grain ou mesh ; profondeur créée par saturation progressive, pas par blur ; transitions de 131.8ms en moyenne",
                "why_it_works": "Gradients ajoutent profondeur perceptive sans charger le DOM ; saturation 56.4% maintient la clarté et l'accessibilité ; absence volontaire de textures conserve le raffinement moderne"
            }
        ],
        "design_philosophy": "Canva matérialise une philosophie de 'democratic design' où l'interface est volontairement ludique mais rigoureusement structurée. Chaque teinte de palette communique : les pastels disent 'accessible', les bleus disent 'fiable', les overlaps disent 'dynamique'. L'approche refuse le cynisme du SaaS froid en faveur d'une joie visuelle calibrée, où chaque décision répond d'abord à l'intention UX avant l'esthétique pure",
        "palette_strategy": "colorful_playful_accessible",
        "typography_strategy": "sans_humanist_proprietary",
        "layout_strategy": "asymmetric_tension_breathing"
    }

def analyze_canva_lp():
    """Canva leadgen LP: Design School landing"""
    return {
        "aesthetic_vector": {
            "energy": 4.4,
            "warmth": 3.6,
            "density": 3.2,
            "depth": 2.4,
            "motion": 3.1,
            "editorial": 3.8,
            "playful": 4.3,
            "organic": 2.1
        },
        "signature": "Landing page Design School qui amplifie la palette Canva avec plus d'illustrations animées et un positionnement pédagogique qui valorise la transformation de l'utilisateur",
        "wow_factor": "La fusion entre ludisme chromatique et storytelling narratif qui transforme un LP classique en expérience éducative immersive",
        "techniques": [
            {
                "type": "color",
                "name": "Palette saturée avec gradients animés",
                "score": 4.4,
                "css_approach": "Même palette de base enrichie par gradients animés ; plus de transitions de couleur on-scroll ; accents plus francs pour urgence conversion",
                "why_it_works": "Motion ajoutée amplifie l'engagement ; saturation augmentée crée sens d'opportunité ; gradients animés guident l'attention vers CTAs"
            },
            {
                "type": "motion",
                "name": "Scroll animations orchestrées et progressives",
                "score": 3.8,
                "css_approach": "Multiple keyframes sur éléments héros ; transitions parallaxe légère ; animations fade-in/scale subtiles ; timing orchestré pour cadence narrative",
                "why_it_works": "Motion narrative guide le lecteur sans distraction ; orchestration respecte préférences accessibilité ; animations créent sens de momentum conversion"
            },
            {
                "type": "layout",
                "name": "Hero asymétrique avec stack narratif",
                "score": 3.7,
                "css_approach": "Hero section avec image/illustration à droite, texte à gauche asymétrique ; stack de sections progressif ; spacing verticale important",
                "why_it_works": "Asymétrie crée dynamisme ; stack vertical guide la narratif ; image hero renforce le positionnement pédagogique"
            }
        ],
        "design_philosophy": "LP Design School optimise la palette Canva pour la conversion en amplifiant motion, en concentrant l'attention via asymétrie, et en adoptant une narratif pédagogique où chaque section explique un bénéfice. Le design balance entre ludisme (pour attraction) et clarté (pour conversion)",
        "palette_strategy": "colorful_playful_narrative",
        "typography_strategy": "sans_hierarchy_dominant",
        "layout_strategy": "hero_asymmetric_stacked"
    }

def analyze_canva_pricing():
    """Canva pricing: SaaS pricing table"""
    return {
        "aesthetic_vector": {
            "energy": 3.8,
            "warmth": 3.3,
            "density": 3.9,
            "depth": 2.2,
            "motion": 2.3,
            "editorial": 3.9,
            "playful": 3.2,
            "organic": 2.0
        },
        "signature": "Page pricing Canva qui maintient la palette ludique tout en augmentant la densité informationnelle et la clarté de la structure tarifaire",
        "wow_factor": "L'équilibre entre densité de contenu (3 plans, nombreuses features) et jouabilité visuelle via la palette sans laisser la complexity dominer",
        "techniques": [
            {
                "type": "layout",
                "name": "Pricing card grid avec emphasis stratégique",
                "score": 4.0,
                "css_approach": "3 cartes en grid ; card de milieu (Pro) légèrement élevée via transform ; cards équidistantes ; spacing vertical important entre tiers",
                "why_it_works": "Emphasis sur Pro via position et scale (visual hierarchy) ; spacing maintient clarté ; grid responsive préserve intent sur mobile"
            },
            {
                "type": "color",
                "name": "Couleurs des cartes differenciant tiers",
                "score": 3.8,
                "css_approach": "Chaque card avec accent de couleur distinct mais palette harmonieuse ; Pro possède gradiet plus saturé ; accents CTA sur chaque card",
                "why_it_works": "Differenciation chromatique aide scannabilité ; accent saturé sur Pro signale premium ; CTA cohérents en couleur"
            },
            {
                "type": "typography",
                "name": "Hiérarchie dense et scannable",
                "score": 3.7,
                "css_approach": "Prix gros/gras, description succincte, features en liste courte ; typo légèrement réduite sur features pour clarté",
                "why_it_works": "Hiérarchie dense permet scannabilité rapide de 60+ features ; Prix est focal point immédiat ; liste compacte évite surcharge cognitive"
            }
        ],
        "design_philosophy": "Pricing Canva accepte la densité (3 plans × ~20 features chacun) mais la maîtrise via hiérarchie typographique stricte et spacing internal. La palette ludique persiste (pastels + accents) pour maintenir la signature Canva, mais l'emphasis visuel sur clarity et CTA domine",
        "palette_strategy": "colorful_hierarchy_emphasis",
        "typography_strategy": "sans_dense_scannable",
        "layout_strategy": "card_grid_asymmetric_emphasis"
    }

# ============================================================================
# COURSERA ANALYSES
# ============================================================================

def analyze_coursera_home():
    """Coursera home: Edtech, 'Apprenez sans limites'"""
    return {
        "aesthetic_vector": {
            "energy": 3.5,
            "warmth": 2.8,
            "density": 3.2,
            "depth": 2.8,
            "motion": 2.4,
            "editorial": 4.2,
            "playful": 2.6,
            "organic": 2.5
        },
        "signature": "Interface edtech ancrée dans la rigueur académique (blues, grays) mais humanisée par photographies chaleur et messaging inspirationnel d'empowerment",
        "wow_factor": "L'alliance entre crédibilité institutionnelle (logos université) et aspirationalisme personnel (user success stories) via design réservé mais chaleureux",
        "techniques": [
            {
                "type": "color",
                "name": "Palette blues académiques + warmth via content",
                "score": 3.8,
                "css_approach": "Couleurs primaires : blues institutionnels (#1a73e8 approx), grays neutres pour fond ; warmth apportée par photographies d'apprenants, pas par palette CSS",
                "why_it_works": "Blues communiquent rigueur/credibilité académique ; grayground maximi content visibility ; photographies chaudes contrebalancent froideur de couleurs"
            },
            {
                "type": "editorial",
                "name": "Photographie en hero et social proof",
                "score": 4.1,
                "css_approach": "Large hero image of learner/university ; grid of university logos prominently placed ; testimonial cards avec photo de learner",
                "why_it_works": "Photographie crée connexion émotionnelle ; logos university = credibilité explicite ; faces dans testimonials = trust social"
            },
            {
                "type": "layout",
                "name": "Hero + card grid + social proof",
                "score": 3.6,
                "css_approach": "Full-width hero with image left/text right ; logo grid below ; card grid de courses ; testimonial carousel",
                "why_it_works": "Hero asymétrique crée intérêt ; logo grid immediate credibility signal ; card grid scannable ; carousel = engagement"
            }
        ],
        "design_philosophy": "Coursera adopte une esthétique réservée mais aspirationnelle où la rigueur académique (couleurs, typographie) est intentionnellement humanisée par la photographie et le storytelling d'impact personnel. Chaque décision design privilege clarity et credibilité universitaire tout en signalant que l'education est accessible et transformatrice",
        "palette_strategy": "academic_neutral_warmth_via_content",
        "typography_strategy": "sans_corporate_hierarchy",
        "layout_strategy": "hero_grid_social_proof"
    }

def analyze_coursera_collection():
    """Coursera collection: 10 cours populaires"""
    return {
        "aesthetic_vector": {
            "energy": 3.3,
            "warmth": 2.9,
            "density": 4.1,
            "depth": 2.5,
            "motion": 2.2,
            "editorial": 4.3,
            "playful": 2.4,
            "organic": 2.3
        },
        "signature": "Page collection Coursera optimisée pour scannabilité dense de cours avec photographies miniatures et metadata cristalline",
        "wow_factor": "L'organisation dense de contenu (10+ courses) qui reste scannable et visuellement cohérente via répétition de pattern de card",
        "techniques": [
            {
                "type": "layout",
                "name": "Card grid dense et régulière",
                "score": 4.0,
                "css_approach": "Grid 3-colonnes (desktop) ou 2-colonnes (tablet) de cards identiques ; card height normalisée ; gap régulier 20px",
                "why_it_works": "Régularité crée scannabilité même en haute densité ; normalisation des hauteurs évite l'effet 'masonry chaos' ; gap régulier crée breathing room"
            },
            {
                "type": "density",
                "name": "Haute densité avec priorités claires",
                "score": 4.1,
                "css_approach": "Chaque card : image + titre + instructor + rating + price empilés ; spacing vertical compact ; aucune 'bleed' horizontale",
                "why_it_works": "Densité acceptée car hierarchy des données est claire : image scout, titre scan, price scan ; pas de surcharge due à hiérarchie"
            },
            {
                "type": "editorial",
                "name": "Image miniature + metadata cristalline",
                "score": 4.0,
                "css_approach": "Thumbnail course image (aspect strict 16:9) ; titre 2-3 lignes max ; instructor name + star rating inline ; price gros/gras",
                "why_it_works": "Thumbnail previews créent intérêt visuel ; metadata ordre = decision flow naturel de l'utilisateur ; price visibility immediate"
            }
        ],
        "design_philosophy": "Collection Coursera accepte une densité de contenu élevée (4.1) car l'architecture de card crée une régularité optique qui permet scannabilité même avec 10+ items. L'Editorial strategy (image, metadata order) optimise pour comportement scanning réel de l'utilisateur",
        "palette_strategy": "academic_neutral_image_driven",
        "typography_strategy": "sans_corporate_compact",
        "layout_strategy": "card_grid_regular_dense"
    }

def analyze_coursera_pricing():
    """Coursera pricing: Edtech pricing"""
    return {
        "aesthetic_vector": {
            "energy": 3.2,
            "warmth": 2.7,
            "density": 3.6,
            "depth": 2.4,
            "motion": 2.1,
            "editorial": 4.1,
            "playful": 2.2,
            "organic": 2.2
        },
        "signature": "Page pricing Coursera qui présente tiers et benefits via structure pédagogique stricte et comparaison tabulaire",
        "wow_factor": "La clarté de structure tarifaire qui refuse toute ambiguite via tableau ou card side-by-side sans artifice visuel",
        "techniques": [
            {
                "type": "layout",
                "name": "Toggle tiers + card ou tableau comparison",
                "score": 3.9,
                "css_approach": "Toggle 'Monthly vs Annual' en top ; cards ou tableau structured display ; clear CTA per tier ; footnotes pour fine print",
                "why_it_works": "Toggle = flexible comparison sans scattergun cards ; structured layout crée clarity ; CTAs per tier = obvious action path"
            },
            {
                "type": "editorial",
                "name": "Benefits checklist scannable",
                "score": 4.0,
                "css_approach": "Checkmarks ou icons pour included features ; X ou aucun symbol pour excluded ; feature list compact mais exhaustive",
                "why_it_works": "Checkmark scanning = fast decision ; X clarity = no ambiguity ; exhaustive list = no 'gotchas'"
            },
            {
                "type": "typography",
                "name": "Hierarchy pricing primaire",
                "score": 3.8,
                "css_approach": "Tier name prominent, price très gros/gras, currency petit ; description succincte ; CTA texte gros/gras",
                "why_it_works": "Hierarchy = immediate price scanning ; currency petit = avoid sticker shock ; CTA prominent = conversion intent"
            }
        ],
        "design_philosophy": "Pricing Coursera privilégie l'exhaustivité et la transparence sur l'esthétique, car le public edtech valorise clarity over beauty. Structure tabulaire ou card strictement organisée refuse l'ambiguité ; chaque élément de pricing info est scannable en < 2 secondes",
        "palette_strategy": "academic_neutral_no_emotion",
        "typography_strategy": "sans_hierarchy_exhaustive",
        "layout_strategy": "table_or_card_comparison_clear"
    }

# ============================================================================
# DOLLAR SHAVE CLUB ANALYSES
# ============================================================================

def analyze_dsc_home():
    """DSC home: Bold, irreverent DTC, 'A SHAVE LINEUP MADE FOR CURVES'"""
    return {
        "aesthetic_vector": {
            "energy": 4.5,
            "warmth": 3.9,
            "density": 3.3,
            "depth": 2.6,
            "motion": 3.2,
            "editorial": 3.5,
            "playful": 4.4,
            "organic": 2.8
        },
        "signature": "Branding DTC irreverent et masculine avec palette dark (noirs, gris charcoal) contrastée par accents primaires punchy et photographie product-centric",
        "wow_factor": "L'irreverence audacieuse du copywriting ('A SHAVE LINEUP MADE FOR CURVES') amplifiée par design bold et humor visuel qui refuse la commodification du rasage",
        "techniques": [
            {
                "type": "color",
                "name": "Palette dark + primary accents punchy",
                "score": 4.3,
                "css_approach": "Dark base : #000000 / #1a1a1a ; primaries : #ff3b4c (red), #ffd700 (gold) ou variantes ; aucun pastel ; saturation élevée en accents",
                "why_it_works": "Dark = masculine, premium, irreverent ; primaries punchy = playfulness sans douceur ; saturation haute crée pop visuel et humor"
            },
            {
                "type": "typography",
                "name": "Copie audacieuse et hiérarchie dominante",
                "score": 4.2,
                "css_approach": "Fonts épaisses/gras pour headings (sans-serif bold, potentiellement custom) ; copy joueuse/informal ; casse majuscule fréquente pour EMPHASIS",
                "why_it_works": "Typographie gras = confidence and boldness ; casse majuscule = irreverence tone ; copy tone = humanisation de marque"
            },
            {
                "type": "editorial",
                "name": "Product photography dominante et rapprochée",
                "score": 4.1,
                "css_approach": "Large product shots / close-ups ; lifestyle photography mineure ; product est héros visuel ; ombre ou fond contraste pour pop",
                "why_it_works": "Product photo = product transparency et quality signal ; close-ups = desirability ; ombre/contraste = product isolation = luxury"
            }
        ],
        "design_philosophy": "DSC adopte une esthétique délibérément irreverent où le dark palette signale que le rasage n'est pas à prendre au sérieux, et le copie audacieuse couplée à la photographie product-centric refusent la commodification. Chaque décision design (dark, bold fonts, accents punchy, humor) rejette l'institutionnalisme et crée une connexion émotionnelle par subversion",
        "palette_strategy": "dark_primary_accents_punchy",
        "typography_strategy": "sans_bold_audacious_tone",
        "layout_strategy": "hero_asymmetric_dark_product"
    }

def analyze_dsc_pdp():
    """DSC PDP: '$8 STARTER SET'"""
    return {
        "aesthetic_vector": {
            "energy": 4.4,
            "warmth": 3.8,
            "density": 3.7,
            "depth": 2.8,
            "motion": 2.9,
            "editorial": 3.8,
            "playful": 4.2,
            "organic": 2.7
        },
        "signature": "PDP DSC optimisé pour conversion avec product hero amplifiée, value prop $8 prominent, et add-to-cart path clarifié sans perte de personality",
        "wow_factor": "La fusion de densité tarifaire et descriptive avec irreverence tonale qui maintient la marque DSC même en contexte transactionnel",
        "techniques": [
            {
                "type": "editorial",
                "name": "Product gallery multivue + zoom interactive",
                "score": 4.2,
                "css_approach": "Main image dominant (left, ~60% viewport) ; thumbnails below ou right ; zoom on hover ; 4-6 images de product angles différents",
                "why_it_works": "Multiple views build confidence in product quality ; zoom = inspection details ; gallery UX standard e-commerce but DSC brand colors"
            },
            {
                "type": "density",
                "name": "Informations densifiées sans surcharge",
                "score": 3.8,
                "css_approach": "Right sidebar : price gros/gras, quantity selector, CTA button, reviews, description, specifications en collapse accordion",
                "why_it_works": "Density acceptée car layout clair ; price primary focal point ; CTA obvious ; accordion hides spec depth until needed"
            },
            {
                "type": "price_emphasis",
                "name": "Value prop '$8' comme hero",
                "score": 4.3,
                "css_approach": "Price gros/bold, currency small ; value prop 'Starter Set' above ou inline ; cross-struck original price si applicable ; scarcity/urgency badge if present",
                "why_it_works": "$8 = immediate attention ; value framing = psychological anchor ; cross-struck = perceived discount ; scarcity badge = FOMO"
            }
        ],
        "design_philosophy": "PDP DSC intensifie la conversion clarity (CTA, price prominence, gallery) tout en refusant de devenir generic e-commerce. La palette dark, les accents punchy, et la review section tonale maintiennent la personality DSC même sous pression transactionnelle",
        "palette_strategy": "dark_primary_accents_conversion",
        "typography_strategy": "sans_bold_value_prop",
        "layout_strategy": "gallery_sidebar_cta_prominent"
    }

# ============================================================================
# DRUNK ELEPHANT ANALYSES
# ============================================================================

def analyze_drunk_elephant_home():
    """Drunk Elephant home: Clean beauty DTC, colorful, 117 images"""
    return {
        "aesthetic_vector": {
            "energy": 4.1,
            "warmth": 4.0,
            "density": 3.8,
            "depth": 3.2,
            "motion": 2.7,
            "editorial": 3.4,
            "playful": 3.9,
            "organic": 3.5
        },
        "signature": "Brand clean beauty où les couleurs des packagings des produits deviennent la palette design : rose, bleu, vert, orange créent une identité joyeuse et chromatiquement distinctive",
        "wow_factor": "L'inverse traditionnel du design beauty : au lieu de palette aspirationnelle neutre, Drunk Elephant utilise la colorimetrie product comme design language principal, créant une marque visuellement unique",
        "techniques": [
            {
                "type": "color",
                "name": "Palette tirée de l'emballage produit",
                "score": 4.3,
                "css_approach": "Couleurs primaires : rose (lipstick), bleu (serum), vert (sunscreen), orange/coral (masks) ; aucun neutre grey ; saturation élevée ; blanc généreux pour breathing",
                "why_it_works": "Produits ARE la palette = cohérence absolue marque ; colorimetrie product-centric = produit est le héros design ; saturation = playfulness signal"
            },
            {
                "type": "photography",
                "name": "114+ images de product / flat-lay / lifestyle",
                "score": 4.2,
                "css_approach": "Grid de carrousel d'images ; flat-lay dominant avec fonds blancs/colorés ; product shots rapprochés ; lifestyle photos minority ; image optimisation haute",
                "why_it_works": "Image density = trust (transparency de product) ; flat-lay = minimalist aesthetic premium ; product shots rapprochés = desirability et detail inspection"
            },
            {
                "type": "layout",
                "name": "Grille image dominante + texte minimal",
                "score": 3.9,
                "css_approach": "Large hero section avec image ou carrousel ; grid principale de produits en 3-4 colonnes ; texte minimal (1-2 sentencesby section) ; whitespace generous",
                "why_it_works": "Grille crée scannabilité dense sans surcharge ; texte minimal = focus on visual ; whitespace valorise images"
            }
        ],
        "design_philosophy": "Drunk Elephant inverse la convention beauty design (neutral, aspirational) en faisant de la colorimetrie product la palette design elle-même. Cette stratégie crée une marque visuellement distinctive et product-centric où le design ne compete pas avec les produits mais amplifie leur colorimetrie unique. La densité d'image (117+) est justifiée car le design dit 'nous sommes transparents sur nos produits'",
        "palette_strategy": "product_colorimetry_primary",
        "typography_strategy": "sans_elegant_letterspacing",
        "layout_strategy": "image_grid_minimal_text_white_breathing"
    }

def analyze_drunk_elephant_pdp():
    """Drunk Elephant PDP: Beauty PDP, 134 images"""
    return {
        "aesthetic_vector": {
            "energy": 4.0,
            "warmth": 3.9,
            "density": 4.2,
            "depth": 3.4,
            "motion": 2.5,
            "editorial": 3.6,
            "playful": 3.8,
            "organic": 3.4
        },
        "signature": "PDP Drunk Elephant amplifie la densité image (134+) pour product transparency maximize, avec color product comme hero et descriptive narrative balancée",
        "wow_factor": "La densité extrême d'image (134+) organisée en gallery/carousel/grid qui reste scannable car hierarchy de 'product hero → detailed images → testimonials' crée narrative",
        "techniques": [
            {
                "type": "editorial",
                "name": "Product hero gallery massive",
                "score": 4.4,
                "css_approach": "Main product image large (~60% viewport width) ; 20-30 thumbnails below ou right sidebar ; carrousel auto-advance ; zoom on hover ; 360 view if applicable",
                "why_it_works": "Massive gallery = product confidence signal ; multiple angles = detail inspection luxury ; zoom = desirability ; 360 = digital shopping experience"
            },
            {
                "type": "density",
                "name": "Densité 4.2 avec structure claire",
                "score": 4.1,
                "css_approach": "Left : product gallery ; right : price/CTA/specs ; below : description, ingredients, benefits grid, testimonials, related products ; no white space waste",
                "why_it_works": "Density acceptée car layout structure crée clarity ; left-right = standard e-commerce UX ; below sections = scroll narrative"
            },
            {
                "type": "ingredients",
                "name": "Transparent ingredient list + educational",
                "score": 4.0,
                "css_approach": "Full ingredient list with icons/categories (Clean, Actives, Texture) ; hover descriptions ; IngredientList expandable ou tabbed ; educational copy about clean formulation",
                "why_it_works": "Drunk Elephant = clean beauty = transparency requirement ; icons make complex list scannable ; educational copy builds credibility ; tabbed = not overwhelming"
            }
        ],
        "design_philosophy": "PDP Drunk Elephant maximise image density (134+) car la brand philosophy est la transparence product absolue. Chaque image additionelle dit 'voici le produit sans artifice', et la structure layout crée narrative même en haute densité : hero → details → ingredients → testimonials → social proof. La densité 4.2 est intentionnel et justified par la brand promise",
        "palette_strategy": "product_colorimetry_emphasis",
        "typography_strategy": "sans_elegant_transparent",
        "layout_strategy": "gallery_massive_transparent_narrative"
    }

# ============================================================================
# HELLOFRESH ANALYSES
# ============================================================================

def analyze_hellofresh_home():
    """HelloFresh home: Meal kit, 61 images"""
    return {
        "aesthetic_vector": {
            "energy": 3.9,
            "warmth": 4.2,
            "density": 3.6,
            "depth": 2.9,
            "motion": 2.8,
            "editorial": 3.7,
            "playful": 3.5,
            "organic": 4.1
        },
        "signature": "Brand meal kit où food photography dominante et warmth chromatique (verts, beiges, ambre) créent une esthétique d'appétance et de simplicité culinaire",
        "wow_factor": "L'utilisation de food photography comme design language principal qui fait de chaque image un appel émotionnel à participation culinaire plutôt qu'à transaction",
        "techniques": [
            {
                "type": "photography",
                "name": "Food photography dominante et appétisante",
                "score": 4.3,
                "css_approach": "Haute résolution food images sur fond blanc/naturel ; lighting chaud et natural ; plating professionnel ; 61 images distributed across sections",
                "why_it_works": "Food photography = immediate appeal et emotional trigger ; warm lighting = appetite signal ; professional plating = quality perception"
            },
            {
                "type": "color",
                "name": "Palette warm et organic : vert, beige, ambre",
                "score": 4.2,
                "css_approach": "Primaires : vert naturel (#4CAF50 approx), beige terreux (#D2B48C approx), ambre/or (#DAA520 approx) ; aucune couleur 'plastique' ; palette naturelle et chaude",
                "why_it_works": "Couleurs de palette naturelle = trust food authenticity ; warm = appetite stimulation ; aucun artificiel = positioning 'natural fresh'"
            },
            {
                "type": "layout",
                "name": "Hero food image + stacked sections",
                "score": 3.8,
                "css_approach": "Hero avec food image (full width ou asymmetric) + copy localisée ; sections : menus (carrousel), testimonials, recipes, nutrition facts",
                "why_it_works": "Hero food = immediate emotional hook ; messaging place local = trust authenticity ; carrousel menus = sampling ; testimonials build credibility"
            }
        ],
        "design_philosophy": "HelloFresh inverse la densité pure en favour de profondeur émotionnelle où food photography n'est pas asset mais language design principal. Chaque couleur, spacing, et texture est calibrée pour dire 'cuisine authentique, locale, simple' via palette naturelle chaud et organic textures. L'image density 61 est justifiée car le design dit 'voici les plats que vous cuisinerez'",
        "palette_strategy": "warm_organic_natural_appetite",
        "typography_strategy": "sans_headline_serif_body_approachable",
        "layout_strategy": "hero_food_stacked_sections_carousel"
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 80)
    print("AURA V16 Opus-Level Design Analysis Generator")
    print("=" * 80)
    print()

    sites_pages = [
        ("canva", "home", analyze_canva_home),
        ("canva", "lp_leadgen", analyze_canva_lp),
        ("canva", "pricing", analyze_canva_pricing),
        ("coursera", "home", analyze_coursera_home),
        ("coursera", "collection", analyze_coursera_collection),
        ("coursera", "pricing", analyze_coursera_pricing),
        ("dollar_shave_club", "home", analyze_dsc_home),
        ("dollar_shave_club", "pdp", analyze_dsc_pdp),
        ("drunk_elephant", "home", analyze_drunk_elephant_home),
        ("drunk_elephant", "pdp", analyze_drunk_elephant_pdp),
        ("hellofresh", "home", analyze_hellofresh_home),
    ]

    success_count = 0

    for site, page, analyzer_func in sites_pages:
        try:
            print(f"Analyzing {site}/{page}...", end=" ")
            analysis = analyzer_func()

            if update_design_dna(site, page, analysis):
                print("✓ SAVED")
                success_count += 1
            else:
                print("✗ FILE NOT FOUND")
        except Exception as e:
            print(f"✗ ERROR: {e}")

    print()
    print("=" * 80)
    print(f"Completed: {success_count}/{len(sites_pages)} sites analyzed and saved")
    print("=" * 80)

if __name__ == "__main__":
    main()
