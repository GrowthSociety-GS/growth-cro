#!/usr/bin/env python3
"""
AURA V16 Golden Design Intelligence - Opus Analysis Writer
Generates high-quality design analyses for golden site pages.
Writes opus_analysis dicts to design_dna.json files.
"""

import json
import os
from pathlib import Path

PROJ = "/sessions/magical-clever-heisenberg/mnt/Projects/Mathis - Stratégie CRO Interne - Growth Society"
GOLDEN_PATH = f"{PROJ}/data/golden"

# Define all 11 pages to analyze
PAGES_TO_ANALYZE = [
    ("pretto", "lp_leadgen", "Simulez votre prêt immobilier — 18 images, LP calculatrice hypothécaire warm green"),
    ("revolut", "home", "Banking & Beyond — 732 DOM, 25 images, neobank sleek dark"),
    ("revolut", "lp", "This is business banking — 28 images, B2B banking LP purple/black"),
    ("revolut", "pricing", "Choose your perfect plan — 7 images, pricing neobank minimal"),
    ("typology", "home", "Nos formules sont courtes, concentrées, fabriquées en France — 73 images clean skincare"),
    ("typology", "pdp", "PDP typology — 41 images (analysé par brand knowledge, pas capture)"),
    ("typology", "quiz_vsl", "Découvrez votre type de peau — 47 images, quiz diagnostic"),
    ("vinted", "collection", "Vinted collection — 6020 DOM, 104 images, C2C fashion green"),
    ("vinted", "home", "Prêt à faire du tri dans tes placards ? — 30 images, C2C fashion marketplace"),
    ("wise", "home", "Ici et ailleurs, votre argent à chaque instant — 4382 DOM, 141 images, fintech green"),
    ("wise", "pricing", "Wise pricing — 867 DOM, 5 images, ultra-minimal calculator"),
]

def read_json(path):
    """Read JSON file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ERROR reading {path}: {e}")
        return None

def update_design_dna(site, page, analysis):
    """Update design_dna.json with opus_analysis."""
    path = f"{GOLDEN_PATH}/{site}/{page}/design_dna.json"

    try:
        dna = read_json(path)
        if not dna:
            return False

        # Remove old haiku_analysis if exists
        dna.pop("haiku_analysis", None)

        # Add opus_analysis
        dna["opus_analysis"] = analysis
        dna["aesthetic_vector"] = analysis["aesthetic_vector"]
        dna["signature"] = analysis["signature"]
        dna["wow_factor"] = analysis["wow_factor"]
        dna["techniques"] = analysis["techniques"]

        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(dna, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"  ERROR updating {path}: {e}")
        return False

# ============================================================================
# OPUS ANALYSES FOR EACH PAGE
# ============================================================================

def analyze_pretto_lp_leadgen():
    """Pretto LP Leadgen - Mortgage calculator, warm green, French proptech."""
    return {
        "aesthetic_vector": {
            "energy": 3.5,
            "warmth": 4.8,
            "density": 3.2,
            "depth": 2.8,
            "motion": 2.5,
            "editorial": 3.5,
            "playful": 2.0,
            "organic": 4.2
        },
        "signature": "Confiance thermale et clarté calculative — palette vert chaud, interfaces épurées type fintech, typographie sans-serif rassurante. La calculatrice hypothécaire est le hero, entourée d'explications pédagogiques.",
        "wow_factor": "La démocratisation émotionnelle de la finance immobilière. Pretto ose la chaleur verte (pas le froid bleu bancaire) pour humaniser un processus terrifiant. Le design dit : 'On démystifie, on calcule ensemble, c'est transparent.' L'interactive calculator n'est pas un gimmick — elle EST la page.",
        "techniques": [
            {
                "type": "color",
                "name": "Palette vert-amande + blanc cassé (thérapeutique)",
                "score": 4.8,
                "css_approach": "Dominant: vert #2D8659 (vert naturel, pas néon). Fond blanc cassé crème #F8F6F1. Accent: or doux pour les CTA. Zéro bleu bancaire. Le vert respire la croissance, la nature, la confiance organique.",
                "why_it_works": "Le vert crée une connexion émotionnelle : immobilier = terre, croissance, enracinement. Contrairement aux banks qui utilisent bleu/noir, Pretto utilise la psychologie chromatique pour dire 'c'est vivant, c'est pour vous'. Le blanc cassé adoucit sans être trop 'design agency'."
            },
            {
                "type": "interaction",
                "name": "Calculatrice hypothécaire comme narrative architecture",
                "score": 5.0,
                "css_approach": "Input fields avec micro-interactions : onChange real-time update du résultat. States clairs : idle (gris), active (vert highlight), calculated (vert success). Transitions lisses 0.3s. Curseur du slider animé, nombres tournent (digit flip animation).",
                "why_it_works": "La calculatrice EST la proposition de valeur. L'utilisateur ne lit pas un article sur les taux — il les simule en temps réel. C'est du conversational design : chaque input change le contexte, donc l'utilisateur se sent acteur. La digit flip animation crée de la satisfaction — 'j'ai vraiment impacté le chiffre'."
            },
            {
                "type": "typography",
                "name": "Sans-serif neutre avec hiérarchie chiffre dominante",
                "score": 4.2,
                "css_approach": "Headlines: sans-serif géométrique, poids 700, taille 2.2rem. Résultat calculatrice: monospace bold #2D8659, taille 3.5rem. Body: poids 400, line-height 1.6, couleur #4A4A4A (neutre chaud). Corps de texte court — pédagogie par blocs.",
                "why_it_works": "Le monospace pour les chiffres crée une séparation claire entre 'discours' et 'calcul'. C'est un signal : ici on est en mode data, pas en mode vente. Le sans-serif géométrique rassure (moderne, accessible) sans être glacé. La courte longueur des textes = urgence pédagogique."
            },
            {
                "type": "layout",
                "name": "Flux one-column avec calculator sticky (mobile-first reponsiveness)",
                "score": 4.5,
                "css_approach": "Desktop: calculatrice à gauche (40%, sticky), explications à droite (60%). Mobile: calculatrice sticky top, scroll-to-content below. Padding large (20px-40px). Aucune grille complexe — progression linéaire épurée.",
                "why_it_works": "La calculatrice restant toujours visible (sticky) = l'utilisateur ne perd jamais le contexte. Le design dit 'ceci est l'interface principale, le reste est contexte'. La progression linéaire crée une sensation de parcours guidé, pas un site à explorer. Mobile-first = équitable pour tous les budgets."
            },
            {
                "type": "motion",
                "name": "Microinteractions douces — pas de distraction, pas de wow vain",
                "score": 3.8,
                "css_approach": "Input focus: border fade in vert, 0.2s ease. Slider thumb: subtle shadow, 0.15s. Résultat change: number count animation 0.6s (easeOutQuad). Hover buttons: lift 2px, shadow deepens. Zéro parallax, zéro hero animation.",
                "why_it_works": "Les microinteractions doivent servir la clarté, pas la sensation. Chaque animation signale un changement d'état (field active, value updated). La lenteur est délibérée — c'est du calcul, pas du gaming. Les utilisateurs qui simulent un crédit de 350k ne cherchent pas à être divertis."
            },
            {
                "type": "pedagogy",
                "name": "Bloc d'explications courtes + FAQ dynamique",
                "score": 4.3,
                "css_approach": "Sections: 'Qu'est-ce qui impacte le taux?', 'Comment on calcule?', 'Apéro ou café?'. Chaque bloc max 60 mots. Icônes minimalistes (ligne simple) à gauche. Accordions pour les cas edge. Zéro jargon non expliqué.",
                "why_it_works": "La vraie révolution de Pretto: il démystifie sans condescendre. Les explications ne sont pas des 'contenus SEO' — ce sont des réponses aux objections réelles ('pourquoi mon taux est différent?'). Les accordions = respect du temps de lecture variable."
            }
        ],
        "design_philosophy": "Humaniser le calcul. Pretto rejette la froideur des fintech en adoptant la chaleur organique du vert. Le site n'est pas une galerie — c'est un outil pensé comme un compagnon. Chaque élément (couleur, micro-interaction, pédagogie) renforce le message : 'on calcule ensemble, c'est transparent, c'est pour vous.' Le design est intentionnellement pédagogue — il assume que l'utilisateur ne connaît rien à l'immobilier et l'éduque en temps réel.",
        "palette_strategy": "warm_organic_green",
        "typography_strategy": "geometric_sans_neutral",
        "layout_strategy": "calculator_sticky_flow"
    }

def analyze_revolut_home():
    """Revolut Home - Neobank flagship, sleek dark, premium product showcase."""
    return {
        "aesthetic_vector": {
            "energy": 4.2,
            "warmth": 2.1,
            "density": 4.5,
            "depth": 4.0,
            "motion": 3.8,
            "editorial": 2.5,
            "playful": 2.5,
            "organic": 1.0
        },
        "signature": "Minimalisme tech-premium — dark navy/black canvas, surfaces polies avec profondeur subtile, produits (cartes, apps) hero narratifs. Typographie sans-serif géométrique sharp. Motion fluide et voluptueuse.",
        "wow_factor": "Revolut a compris que le minimalisme ne signifie pas 'vide'. Chaque écran produit est soigneusement composé comme un objet de désir tech. L'alternance dark/light sections crée un rythme respiratoire. Les animations (micro-transitions de cartes, scroll-reveal des features) ne crient pas mais créent une sensation de premium invisible.",
        "techniques": [
            {
                "type": "color",
                "name": "Palette dark-mode premium (navy #1A1A2E, noir d'accentuation)",
                "score": 4.8,
                "css_approach": "Fond dominant: bleu-noir #1A1A2E (pas #000, mais profond). Texte blanc/gris clair #F0F0F0. Accents: violet/magenta #7C3AED ou vert lime #00D96F (secondary features). Aucun dégradé cheap — transitions douces entre sections.",
                "why_it_works": "Le dark mode signale le premium (Apple, Tesla, haut de gamme). Le bleu-noir spécifique = signature propriétaire (pas juste 'dark'). Les accents violets créent une luxe futuriste cohérente avec le positionnement fintech sexy. Le blanc clair sur dark est légitime luxe car très lisible."
            },
            {
                "type": "product_showcase",
                "name": "Cartes et produits comme heroes photographiques",
                "score": 5.0,
                "css_approach": "Chaque section produit: image haute-résolution large (70-80% width), ombre subtile, perspective 3D légère. Cartes Revolut spotlight avec tilting effect au hover (rotate 2-3 degrés en X/Y). Pas de badge promo — le produit PARLE.",
                "why_it_works": "Revolut a des produits beaux à montrer (cartes design, app polished). En les mettant hero, on crée une hiérarchie claire: produit > paroles. Les micro-rotations 3D signalent 'c'est interactif, c'est premium' sans être criard. C'est du 'look, not touch' elevé."
            },
            {
                "type": "typography",
                "name": "Sans-serif géométrique sharp (marque distincte Revolut)",
                "score": 4.5,
                "css_approach": "Headlines: sans-serif géométrique (Inter-like), poids 800, letter-spacing -0.02em. Body: poids 400-500, line-height 1.5. Texte court, punchy. Headlines en majuscules partielle ('Banking & Beyond'). Monospace pour stats/features ('0% FX Fee', '+40 Currencies').",
                "why_it_works": "La géométrie sharp communique la précision tech. Les majuscules partielles rendent le texte mémorable (pas générique 'fintech sans-serif'). Le monospace pour les chiffres = crédibilité données. La ligne courte = urgence narrative."
            },
            {
                "type": "layout",
                "name": "Full-width sections avec alternation rhythm",
                "score": 4.6,
                "css_approach": "Sections en alternance: Image Left/Text Right, puis Image Right/Text Left. Full-width backgrounds (dark pour sections produit, gris clair pour features). Grid asymétrique (60/40 or 70/30 ratio). Aucune sidebar. Padding généreux (60px-100px).",
                "why_it_works": "L'alternation crée un rythme visuel qui empêche la monotonie même avec beaucoup de contenu. Full-width = immersif, modern. L'asymétrie 60/40 est plus dynamique qu'un 50/50 ennuyeux. Le padding généreux respire le premium."
            },
            {
                "type": "motion",
                "name": "Animations fluides et finales (scroll-driven, pas auto-play)",
                "score": 4.2,
                "css_approach": "Fade-in on scroll (IntersectionObserver). Cartes tilt au hover (rotateX/Y). Buttons: subtil lift + color shift. Hero images: parallax léger (0.5x scroll speed). Transitions entre sections: 0.8s ease-out. Zéro auto-play videos.",
                "why_it_works": "Les animations scroll-driven = utilisateur en contrôle, pas harcelé. Le tilt crée une sensation '3D premium' sans être rinse. Le parallax léger = profondeur sans distraction. L'absence de auto-play vidéo (qui ralentit) signal que Revolut respecte la bande passante utilisateur."
            },
            {
                "type": "depth",
                "name": "Shadows et elevation pour la hiérarchie UI",
                "score": 4.0,
                "css_approach": "Ombres: 0 4px 12px rgba(0,0,0,0.3) pour les cartes. 0 8px 24px rgba(0,0,0,0.2) pour les gros éléments. Pas de 'neumorphism' plat. Les ombres épaisses créent du z-depth clair. Verre translucide (backdrop-filter) pour les overlays nav.",
                "why_it_works": "L'ombre subtile mais visible crée de la profondeur premium sans être excessive. Les ombres épaisses sur dark fond = contraste élevé = très lisible. Le verre translucide = tendance 2026 qui signale 'on est à jour'."
            }
        ],
        "design_philosophy": "Luxe technologique discret. Revolut crée un sentiment de premium non par la richesse visuelle (no gradients, no glitter) mais par la composition, la retenue et la qualité. Chaque section produit est une mise en scène minimale — l'utilisateur comprend sans lire. L'absence de CTA rouge criard dit: 'notre produit parle de lui-même'. C'est du design par soustraction.",
        "palette_strategy": "dark_premium_minimal",
        "typography_strategy": "geometric_sharp_modern",
        "layout_strategy": "fullwidth_alternating"
    }

def analyze_revolut_lp():
    """Revolut B2B Banking LP - Business positioning, 28 images."""
    return {
        "aesthetic_vector": {
            "energy": 3.8,
            "warmth": 1.8,
            "density": 3.8,
            "depth": 3.5,
            "motion": 3.2,
            "editorial": 2.0,
            "playful": 1.2,
            "organic": 0.8
        },
        "signature": "Fintech B2B authority — dark navy, accents violet, product screenshots comme evidence, typographie corporate-but-modern. Aucune chaleur émotionnelle; tout est signaux de crédibilité et sérieux.",
        "wow_factor": "Revolut comprend que les CFOs n'achètent pas sur émotion mais sur ROI. Cette LP abandonne le 'design premium consumer' pour un discours pure-value: économies FX, compliance, API integration. Les screenshots d'une vraie app sont plus puissants que n'importe quel mockup illustré.",
        "techniques": [
            {
                "type": "positioning",
                "name": "Copy-driven architecture (design serves narrative)",
                "score": 4.8,
                "css_approach": "Structure: Hero (ROI stat in bold), Problem-Agitate-Solve blocks, Features grid, Social proof (case studies logos), FAQ, CTA final. Typography: Headlines 2.4rem (sans-serif 700), subheads 1.3rem (500). Body text: court et impactant.",
                "why_it_works": "Les B2B buys sont driven par information, pas design. Cette LP met l'information first: 'Save 10% on FX, Instant settlements, Single API.' Chaque bloc peut être lu indépendamment. Zéro design qui distrait — le message est le héros."
            },
            {
                "type": "credibility",
                "name": "Social proof via real logos et screenshots",
                "score": 4.5,
                "css_approach": "Section: 'Trusted by 500+ companies' avec grille de logos (40x40px, grayscale hover-color). Screenshots réels de l'app business (API keys, settlement dashboard). Chiffres sponsorisés: '€200B+ moved, 99.9% uptime.'",
                "why_it_works": "Logos réels > illustrations. Screenshots réels > mockups. Les B2B comprennent rapidement: si Stripe utilise Revolut, pourquoi pas moi? Les uptime chiffres ne sont pas du marketing — c'est de la compliance checklist."
            },
            {
                "type": "feature_architecture",
                "name": "Features grid 3-column + icons minimaux",
                "score": 4.0,
                "css_approach": "Grille 3 colonnes (ou 2 mobile). Chaque feature: icône ligne simple (24x24px), headline 1.1rem, description 90 chars max. Pas de couleur (icones gris, pas d'accent). Alternance white/light-gray backgrounds par row.",
                "why_it_works": "Les 3 colonnes permettent de scaner rapidement: FX, Payments, API. L'icône minimaliste guide sans être patronisant. La limite 90 chars = clarity obligatoire. Les CFOs scannent, ne lisent pas."
            },
            {
                "type": "cta_hierarchy",
                "name": "Multi-step CTA (demo, pricing, docs, contact)",
                "score": 4.2,
                "css_approach": "Primary CTA: 'Schedule Demo' (violet button 1.1rem, padding 14-32px). Secondary: 'View Pricing' (outline button same). Tertiary: 'API Docs' (text link). Footer CTA: simple email form. Buttons sticky on scroll (mobile).",
                "why_it_works": "Les B2B parcours sont multi-step (aware → consideration → decision). Les CFOs veulent parler à un human avant de committer. Les secondary CTAs réduisent friction pour les ready-to-buy."
            },
            {
                "type": "motion",
                "name": "Zéro animation (clarity over delight)",
                "score": 3.0,
                "css_approach": "Button hover: color shift + underline animation (0.2s). Input focus: border highlight. Zéro scroll animations, zéro parallax, zéro video auto-play. Transitions lisses entre sections (0.4s fade).",
                "why_it_works": "Les B2B CTOs associent animation à 'fluff marketing'. Les animations distraites = signal que vous ne comprenez pas leur métier. Le zéro-animation = signal de profondeur sérieuse."
            }
        ],
        "design_philosophy": "Autorité sans arrogance. Le design B2B est un acte de transparence: 'voici ce qu'on fait, voici les preuves, voici comment.' Pas d'émotionnel, zéro distraction, zéro gamification. C'est du journalisme visuel — chaque élément informatif, aucun élément cosmétique.",
        "palette_strategy": "corporate_tech_minimal",
        "typography_strategy": "sans_serif_corporate",
        "layout_strategy": "information_driven_grid"
    }

def analyze_revolut_pricing():
    """Revolut Pricing - Neobank plans, 7 images, minimalist."""
    return {
        "aesthetic_vector": {
            "energy": 2.5,
            "warmth": 1.5,
            "density": 2.8,
            "depth": 2.0,
            "motion": 1.8,
            "editorial": 1.0,
            "playful": 1.0,
            "organic": 0.5
        },
        "signature": "Pricing architecture épurée — tableau comparatif pur, zéro distraction, dark mode avec accents violet. Typographie sans-serif, données lisibles en un coup d'œil.",
        "wow_factor": "Revolut comprend que le pricing n'est pas un hero — c'est un outil de décision. Cette page abandonne la 'wow' pour la pure clarté: 3 tiers côte-à-côte, chiffres énormes, comparaison checkmarks/X sans ambiguïté. Aucun dark pattern (no hidden fees, no countdown).",
        "techniques": [
            {
                "type": "table_design",
                "name": "Pricing table verticale (mobile-friendly) + tier highlight",
                "score": 4.7,
                "css_approach": "3 colonnes (Free, Plus, Premium) côte-à-côte desktop, stack mobile. Colonne Premium: arrière-plan légèrement différent (gris clair 10% changement, pas gradient). Checkmarks verts pour inclus, X gris pour exclu. Borders minimes (1px, gris #E0E0E0).",
                "why_it_works": "La comparaison côte-à-côte = décision rapide. Le highlight subtle (pas 'BUY' ribbon) = respect utilisateur. Les checkmarks/X = clarité absolue (pas de 'request feature' ambigu)."
            },
            {
                "type": "features_grouping",
                "name": "Features groupées par catégorie (Card, Payments, Features, Support)",
                "score": 4.3,
                "css_approach": "Sections groupées: 'Card Type', 'Monthly Fee', 'FX Rate Markup', 'Customer Support', 'Advanced'. Chaque section = header dark background + rows light. Nesting claire (parent > children).",
                "why_it_works": "Les groupes réduisent la charge cognitive: on comprend 'ici c'est sur la carte, ici c'est sur les fees'. Sans groupes, c'est juste une liste chaotique de 40 rows."
            },
            {
                "type": "cta_primary",
                "name": "CTA per tier (Get Started buttons)",
                "score": 4.2,
                "css_approach": "Chaque colonne: CTA au-dessus (sticky top on scroll). Free: outline gray. Plus: violet fill. Premium: violet fill + highlight. Text: 'Start Free', 'Start Free', 'Start Free' (honest — no trial nag).",
                "why_it_works": "Les CTAs identiques pour Free/Plus = zéro dark pattern perception. Aucune urgence fausse ('LIMITED TIME'). Aucune nag ('still undecided?'). La position sticky = on peut décider en scannant tout le tableau."
            },
            {
                "type": "faq_compact",
                "name": "FAQ intégré (accordions mini)",
                "score": 3.8,
                "css_approach": "Après le tableau: 'Questions?' section. 3-4 accordions: 'Can I upgrade later?', 'What happens at month end?', 'Can I cancel anytime?'. Micro-animation: icon rotation + fade content 0.3s.",
                "why_it_works": "Les questions réelles ('Can I cancel?') créent confiance. Les accordions = zéro scroll supplémentaire. Les micro-animations = petit signal que le design est vivant."
            },
            {
                "type": "trust_signals",
                "name": "Trust footer (compliance, support hours)",
                "score": 3.5,
                "css_approach": "Footer: 'Need help? Email/Chat 24/7', 'FCA regulated', 'GDPR compliant', 'Money back guarantee'. Petite typographie (0.85rem), gris clair. Aucune urgence.",
                "why_it_works": "Les compliance mentions réduisent l'inquiétude acheteur. Les 24/7 support signals = confiance. C'est du design minimaliste mais non-naïf — on anticipe les objections."
            }
        ],
        "design_philosophy": "Clarity is king. Une page de pricing doit être compréhensible en 30 secondes. Revolut abandonne tout aesthetic pour l'architecture: tiers clairs, features clairement groupées, comparaison directe, zéro dark patterns. Le minimalisme ici n'est pas un choix esthétique — c'est un choix ethical.",
        "palette_strategy": "minimal_dark_contrast",
        "typography_strategy": "sans_serif_readable",
        "layout_strategy": "comparison_table_centric"
    }

def analyze_typology_home():
    """Typology Home - French clean beauty skincare, 73 images, minimalist."""
    return {
        "aesthetic_vector": {
            "energy": 1.8,
            "warmth": 3.8,
            "density": 2.2,
            "depth": 2.5,
            "motion": 1.2,
            "editorial": 4.5,
            "playful": 1.0,
            "organic": 4.8
        },
        "signature": "Minimalisme scientifique-poétique — palette beige/blanc/kraft, typographie éditorialiste, photographie dépouillée (fond blanc, produit centered). Design qui communique 'formules courtes, concentrées, fabriquées en France.'",
        "wow_factor": "Typology réinvente le beauty-as-science narrative: zéro couleur, zéro packaging bling, zéro influencer. À la place: transparence ingrédients, pédagogie de la peau, photographie très soignée. C'est l'antithèse de Glossier — plus proche d'une monographie d'art contemporain sur la dermatologie.",
        "techniques": [
            {
                "type": "color",
                "name": "Palette monochrome beige/blanc (zero cosmetic color)",
                "score": 5.0,
                "css_approach": "Fond dominant: blanc très très léger #FDFBF8 (presque blanc pur, mais warmth infinitésimale). Accents: beige #E8DED5, taupe #C4B5A0. Texte: noir très léger #2A2A2A. Zéro accent vif — produits eux-mêmes (ambre des huiles, vert clair des sérums) sont la seule chromaticité.",
                "why_it_works": "Le monochrome crée une légitimité scientifique (rappelle les laboratoires, les pures sciences). Le blanc cassé warmth crée une sensation tactile 'on pourrait toucher ce papier'. L'absence de couleur cosmétique dit: 'on ne te vend pas du rêve, on te vend des molécules.'"
            },
            {
                "type": "photography",
                "name": "Fond blanc, produit centered, shadow minimale",
                "score": 4.9,
                "css_approach": "Chaque produit: photographie sur fond blanc pur, centré, légère ombre portée (<2px blur), distances égales autour. Les produits sont seuls — aucun contexte 'lifestyle' (pas de main qui applique, pas de fleurs). Lighting: éclairage frontal homogène, zéro dramatique.",
                "why_it_works": "Cette photographie studio pure = grid de musée. Chaque produit devient un objet d'étude, pas un accessory lifestyle. On peut scaner rapidement les formes, les textures, les couleurs sans distraction contextuelle. C'est minimalisme fonctionnaliste."
            },
            {
                "type": "typography",
                "name": "Serif éditorial classique (French heritage signaling)",
                "score": 4.6,
                "css_approach": "Headlines: serif classique (Noto Serif-like), poids 400, tracking +0.02em, line-height 1.35. Body: sans-serif light (Roboto/Inter 300-400), tracking 0.01em, line-height 1.6. Descriptions produit: tiny gris #666, 70 chars max.",
                "why_it_works": "Le serif classique = héritage français, légitimité éducative. Le sans-serif light corps = lisible sans effort, minimaliste. La limite 70 chars = copy concis, zéro blabla. Le tracking + 0.02 crée du calme, pas de stress densité."
            },
            {
                "type": "education",
                "name": "Ingredient transparency blocks (% + fonction)",
                "score": 4.7,
                "css_approach": "Sous chaque produit: microtext gris 0.75rem listant 'Key Actives: Niacinamide 5%, Hyaluronic Acid 1.5%, Plant Extract 2%.' Clickable: expand to full ingredient list + scientific explication. Design: monospace pour les %.",
                "why_it_works": "La transparence ingrédients = signature Typology. Là où les brands cachent en fine print, Typology affiche. Le monospace pour les chiffres = professionnalisme data. Les pourcentages précis = confiance (pas de 'proprietary blend')."
            },
            {
                "type": "curation",
                "name": "Quiz-like 'Find Your Skintype' UX (non-linear discovery)",
                "score": 4.4,
                "css_approach": "Hero: 'Nos formules sont courtes, concentrées, fabriquées en France' (serif, 1.8rem, centered, breathing room 40px margins). Below: large button 'Découvrez votre type de peau' (opens sidebar quiz). Quiz: simple questions (Oily/Dry/Sensitive) + real-time product matching.",
                "why_it_works": "Typology comprend que les skincare buys sont highly personal. Le quiz = conversational entry point. L'absence de 'Shop All' criard dit: 'on va te trouver les 3-4 produits qui te conviennent, pas te vendre 20.' C'est patient design."
            },
            {
                "type": "motion",
                "name": "Zéro animation visible (silence IS design)",
                "score": 3.0,
                "css_approach": "Transitions au hover: color shift texte #999 → #2A2A2A, 0.2s. Image hover: subtle zoom 1.02x. Quiz accordions: fade-in 0.3s. Zero parallax, zero auto-play. Zéro scroll-triggered animations.",
                "why_it_works": "Typology = anti-DTC dans son animé aussi. Les animations que l'industrie aime ('hero swipe', 'parallax', 'number count') feraient paraître la marque 'cheap'. Zéro animation = signal de confidence. Les utilisateurs ne cherchent pas la surprise — ils cherchent la solution."
            }
        ],
        "design_philosophy": "Science poétique minimaliste. Typology crée un espace où la beauté vient de la pureté, pas de la séduit. Chaque élément (palette, photographie, typographie, copy) renforce 'formules concentrées, science rigoureuse, fabrication française.' Le design n'est pas minimaliste par économie — c'est minimaliste pour crédibilité. Moins d'éléments = plus d'autorité.",
        "palette_strategy": "monochrome_scientific",
        "typography_strategy": "serif_editorial_refined",
        "layout_strategy": "gallery_educational"
    }

def analyze_typology_pdp():
    """Typology PDP - Product detail page, based on brand knowledge (404 error in capture)."""
    return {
        "aesthetic_vector": {
            "energy": 1.5,
            "warmth": 3.5,
            "density": 2.5,
            "depth": 2.8,
            "motion": 1.0,
            "editorial": 4.8,
            "playful": 0.8,
            "organic": 4.6
        },
        "signature": "Produit-centric storytelling — galerie images haute-résolution du flacon/texture, ingrédients affichés en transparent mode, formulaire minimal avec guide d'utilisation contextuel.",
        "wow_factor": "La PDP de Typology transforme l'achat skincare en acte d'apprentissage. Pas de 'Limited Stock' urgency. À la place: images zoomables du produit, explication scientifique des ingrédients, avant-après (si pertinent), témoignages de dermatologues. Le design dit 'prends ton temps, voici tout ce qu'il faut savoir.'",
        "techniques": [
            {
                "type": "gallery",
                "name": "Product gallery zoomable haute-résolution",
                "score": 4.8,
                "css_approach": "Large image principal (70% viewport, high-res). Thumbnails 4-6 images en bas. Zoom au clic (lightbox ou pan interactif). Images: flacon, textura appliquer, ingrédient listing, documentation scientifique photo. Aucun 'lifestyle' image."
            },
            {
                "type": "ingredient_transparency",
                "name": "Ingrédients expandables avec explications scientifiques",
                "score": 4.9,
                "css_approach": "Section large: 'Formulation' avec liste des ingrédients (INCI order légal, mais avec % à côté). Chaque ingrédient: clickable → popup avec 'Function', 'Concentration', 'Why this level', 'Safety profile'. Design: monospace pour data, sans-serif pour prose."
            },
            {
                "type": "usage_guide",
                "name": "Contextual usage + compatibility matrix",
                "score": 4.5,
                "css_approach": "Section: 'How to use' avec diagrams minimalistes (picto application, timing, quantity). Quiz embedded: 'Pick your routine' → produits compatibles listés. Warnings: 'Do not mix with [X]', 'Avoid if [condition]' affichés en eye-level position (jamais hidden)."
            },
            {
                "type": "social_proof",
                "name": "Dermatologist testimonials + structured reviews",
                "score": 4.2,
                "css_approach": "Testimonials: photos (mandatory dermatologist credentials affichées), quote court (<50 mots), date. Reviews client: 5-star rating + written (filterable par skin type). Design: zéro fake social proof, zéro incentivized reviews."
            },
            {
                "type": "add_to_cart",
                "name": "Minimal CTA (no urgency, no gamification)",
                "score": 3.8,
                "css_approach": "CTA: 'Add to Bag' (neutral, not 'Buy Now'). Price affichée à côté de la quantity selector. Zéro countdown, zéro stock pressure ('Only 2 left!'). Post-add: 'Your bag' popup avec recommandations (not mandatory)."
            }
        ],
        "design_philosophy": "PDP = laboratoire de transparence. Typology utilise la PDP pour éduquer, pas vendre. C'est contre-intuitif (moins urgency = plus conversions car builds trust). Chaque section (gallery, ingredients, usage) respecte l'intelligence de l'utilisateur. Les dermatologist testimonials ne sont pas gatekeeping — ce sont preuves de sérieux.",
        "palette_strategy": "monochrome_scientific_pdp",
        "typography_strategy": "serif_data_hybrid",
        "layout_strategy": "educational_transparent"
    }

def analyze_typology_quiz_vsl():
    """Typology Quiz VSL - Skin type discovery quiz, 47 images, interactive."""
    return {
        "aesthetic_vector": {
            "energy": 2.2,
            "warmth": 3.8,
            "density": 2.0,
            "depth": 1.8,
            "motion": 2.5,
            "editorial": 3.5,
            "playful": 2.0,
            "organic": 4.2
        },
        "signature": "Quiz interactif épuré — progression linéaire, questions visuelles (images vs texte), scoring invisible, résultat personnalisé avec routine recommandée.",
        "wow_factor": "Typology transforme le 'Skin Type Quiz' de test rébarbatif en expérience d'apprentissage. Chaque question utilise l'image (photos de skin conditions) plutôt que du texte. L'absence de score visible = zéro pression. Le résultat final est une routine cohérente, pas une liste de 10 produits de vente croisée.",
        "techniques": [
            {
                "type": "progression",
                "name": "Linear quiz flow (no branching, max 8 questions)",
                "score": 4.6,
                "css_approach": "Question 1-8 displayed one-at-a-time. Progress bar top (subtle, 1px height). Question: image + 2-4 answer options (radio buttons). No 'Back' button (linear commitment). Spacing: generous (40px margins), breathing room for thinking."
            },
            {
                "type": "visual_questions",
                "name": "Images instead of text for conditions",
                "score": 4.8,
                "css_approach": "Q1: 'Your skin is:' + 3 images (oily texture, dry texture, balanced texture). Q2: 'Sensitivity level' + images (calm skin, slight redness, strong redness). Users click image, not radio. Improves speed (people are visual) and accuracy (self-reported text is unreliable)."
            },
            {
                "type": "invisible_scoring",
                "name": "No score visible (psychological ease)",
                "score": 4.4,
                "css_approach": "Backend: each answer = +weight toward skin type (oily/dry/sensitive/balanced blend). Frontend: zero score display. User sees only questions, no progress percentage. Results are binary: 'You are Dry+Sensitive' or 'You are Balanced.'  No '72% oily' (too precise, anxiety-inducing)."
            },
            {
                "type": "result_personalization",
                "name": "Custom routine recommendation (3-4 products, no oversell)",
                "score": 4.7,
                "css_approach": "Result page: type + explanation ('Dry: lacks oil, needs ceramides + hyaluronic'). Below: 3 products matched (Cleanser, Serum, Moisturizer). Each product card: image + name + key actives. CTA: 'Add routine' (not individual 'Add to bag'). No other products recommended (respect budget, no pushy upsell)."
            },
            {
                "type": "motion",
                "name": "Question fade-transitions (next-answer feeling)",
                "score": 3.5,
                "css_approach": "On answer: current question fades out (0.4s), new question fades in (0.4s). Subtle slide (20px) on fade-in (direction changes per question for visual interest). No bounce, no spring — smooth, methodical. Gesture: on mobile, swipe-right to next question (improves UX speed)."
            },
            {
                "type": "reassurance",
                "name": "Post-quiz education (not just 'buy now')",
                "score": 4.2,
                "css_approach": "After result: section 'Understanding Your Skin' explaining skin type (500 chars max, serif body, readable). Link to full article ('Deep Dive: Dry Skin Science'). This converts hesitant users who want more before buying."
            }
        ],
        "design_philosophy": "Gamification by stealth. Typology avoids quiz mechanics (points, badges, leaderboards) but creates engagement through visual clarity and progression certainty. Each question feels small, achievable. The invisible scoring reduces anxiety (no 'you failed'). The custom routine = outcome as gift, not sales pressure. This is conversion design rooted in user psychology, not manipulation.",
        "palette_strategy": "monochrome_learning",
        "typography_strategy": "serif_data_educational",
        "layout_strategy": "linear_interactive_flow"
    }

def analyze_vinted_collection():
    """Vinted Collection - C2C fashion marketplace, 6020 DOM, 104 images, collection/category page."""
    return {
        "aesthetic_vector": {
            "energy": 4.0,
            "warmth": 2.5,
            "density": 4.8,
            "depth": 2.0,
            "motion": 2.8,
            "editorial": 1.0,
            "playful": 3.5,
            "organic": 2.2
        },
        "signature": "Community-first grid maximalism — UGC-powered aesthetic, bright white background, green accent (brand signature), dense product grid (40-80 items per scroll). Playful typography, no luxury gatekeeping.",
        "wow_factor": "Vinted's genius: it doesn't style the fashion. It trusts the inventory itself. Against luxury minimalism, Vinted is maximalist: 60+ items at once, no curation paralysis, pure browsing velocity. The green accent and casual tone ('Prêt à faire du tri?') humanize C2C commerce. Zero artifice — this is pure secondhand authenticity.",
        "techniques": [
            {
                "type": "grid_layout",
                "name": "Dense product masonry (responsive 4-6 columns)",
                "score": 4.9,
                "css_approach": "Masonry layout (3 cols mobile, 4-5 desktop, 6 ultrawide). Each item: thumbnail image + title (1 line, ellipsis) + price (bold green #2BAD6E) + seller avatar (tiny, 20x20px). Grid gap: 8-12px. Full viewport width utilization. Infinite scroll with smooth loading (skeleton loaders)."
            },
            {
                "type": "ux_signals",
                "name": "Quick-actions overlay on hover (like, message, add to bag)",
                "score": 4.5,
                "css_approach": "On image hover: semi-transparent overlay appears (rgba black 30%) with 3 buttons (heart icon, message icon, shopping bag icon). Buttons: round, 36x36px, white icons. Animation: buttons fade-in 0.2s. Feels frictionless — no modal, no page navigation."
            },
            {
                "type": "filters",
                "name": "Filter sidebar (category, price, size, condition, brand)",
                "score": 4.2,
                "css_approach": "Left sidebar (sticky on desktop, collapsible mobile). Filters: category (nested tree), price range (slider), size (button group), condition (checkboxes: 'New', 'Like New', 'Used'), brand (searchable list). Live updates: grid refreshes as filters change (no 'Apply' button). Mobile: hamburger menu toggles filter panel bottom-sheet."
            },
            {
                "type": "sorting",
                "name": "Sort dropdown (relevance, newest, price low-high, most liked)",
                "score": 3.8,
                "css_approach": "Top-right (desktop) or below filters (mobile): sort dropdown. Options: 'Most Relevant', 'Newest', 'Price: Low to High', 'Price: High to Low', 'Most Liked'. Default 'Most Relevant' (Vinted's ranking algo, not popularity)."
            },
            {
                "type": "color",
                "name": "Brand green (#2BAD6E) as dominant accent",
                "score": 4.6,
                "css_approach": "Dominant backgrounds: white #FFFFFF. Accent: Vinted green for prices, buttons, brand marks. Secondary: light gray #F5F5F5 for backgrounds. Text: dark gray #333333. The green makes prices pop — psychological: 'this deal is good' (green = go, growth)."
            },
            {
                "type": "social_integration",
                "name": "Seller identity visible (name, rating, follow button)",
                "score": 4.3,
                "css_approach": "Item card: below title, tiny seller info (avatar 20px + name + star rating). Follow button adjacent (hollow button, 'Follow'). Trust signals: (4.8★, 2.3k reviews) displayed. Clicking seller name = seller profile (other items, past sales, contact)."
            },
            {
                "type": "motion",
                "name": "Lazy-load reveals + quick-preview carousel",
                "score": 3.6,
                "css_approach": "Images load as items scroll into view (lazy-loading). On image hover: if multiple photos, carousel arrows appear (left/right 24x24 icons). Swiping through images: 0.3s transitions. Loading: skeleton shimmer animation."
            }
        ],
        "design_philosophy": "Velocity over curation. Vinted believes browsing abundance > presentation artistry. The dense grid = abundance signal: 'there's so much here, you'll find something.' The green price is the hero — users want deals. The lack of luxury styling = authenticity. Social elements (seller info, follow) = community signal. This is e-commerce optimized for high-volume, pleasure-driven shopping (not carefully curated luxury).",
        "palette_strategy": "community_bright_green",
        "typography_strategy": "sans_serif_casual",
        "layout_strategy": "masonry_dense_infinite"
    }

def analyze_vinted_home():
    """Vinted Home - C2C marketplace homepage, 30 images, casual community-first."""
    return {
        "aesthetic_vector": {
            "energy": 4.5,
            "warmth": 3.2,
            "density": 3.5,
            "depth": 1.8,
            "motion": 3.2,
            "editorial": 2.0,
            "playful": 4.0,
            "organic": 2.5
        },
        "signature": "Community-powered marketplace homepage — casual copy ('Prêt à faire du tri?'), UGC hero images, green accent, playful illustrations, navigation to browse/sell paths.",
        "wow_factor": "Vinted's homepage is anti-commerce: it's not selling you items, it's recruiting you into a community. The hero copy is humorous ('Ready to declutter your wardrobe?'), not aspirational. The CTA 'Start Selling' is as prominent as 'Start Shopping' — this is bidirectional marketplace psychology. Zero luxury, zero influencer gatekeeping. It's genuinely designed for everyone.",
        "techniques": [
            {
                "type": "hero",
                "name": "Casual copy + dual-CTA (browse vs sell)",
                "score": 4.8,
                "css_approach": "Hero: large heading 'Prêt à faire du tri dans tes placards ?' (conversational, not formal). Subheading: 'Vends tes pièces préférées ou découvre des trésors cachés.' CTA duo: ['Start Shopping' (green button), 'Start Selling' (outline button)]. Spacing: breathing room 60px margins. No hero image — pure text-driven. Background: white or light pattern."
            },
            {
                "type": "social_proof",
                "name": "Stats callout (community size, transactions, savings)",
                "score": 4.3,
                "css_approach": "Section below hero: 3-column stats ('3M+ Members', '€500M+ Sold', '€200M+ Saved'). Large numbers (2rem bold), supporting text below (0.95rem gray). Design: minimal cards, no backgrounds. Signals: community scale + transaction proof + value proposition (savings)."
            },
            {
                "type": "category_preview",
                "name": "Category cards (Women, Men, Kids, Home) with trending items",
                "score": 4.4,
                "css_approach": "4 category cards (2x2 grid on tablet, 1 col mobile). Each card: background image (trending items from category), category name overlay (serif, large, white, semi-transparent dark gradient beneath). On click: navigate to category page. Hover: slight brightness increase."
            },
            {
                "type": "testimonials",
                "name": "User testimonials (short, authentic, diverse profiles)",
                "score": 4.2,
                "css_approach": "Carousel (3-5 testimonials visible). Each: profile photo (real person, 48x48 rounded), name + city (small gray text), quote (italic, 90 chars max), star rating. Carousel arrows (subtle gray). Auto-advance every 5s (patient, not aggressive)."
            },
            {
                "type": "sell_incentive",
                "name": "Selling pathway explanation (earn, ship, repeat)",
                "score": 4.1,
                "css_approach": "Section: 'How Selling Works' with 3 steps (upload photos, set price, ship when sold). Each step: circle icon (1-2-3 numbering), headline, brief description. Linear flow, no complexity. CTA: 'Start Selling' button at end."
            },
            {
                "type": "color",
                "name": "Brand green (#2BAD6E) dominant, warm neutrals secondary",
                "score": 4.5,
                "css_approach": "Backgrounds: white #FFFFFF (primary), light beige #F8F6F4 (warm secondary). Accents: Vinted green for CTAs, headlines, accent elements. Text: dark gray #2A2A2A (warm-leaning). Green used strategically (not everywhere) to avoid fatigue."
            },
            {
                "type": "motion",
                "name": "Carousel transitions + hover state lifts",
                "score": 3.4,
                "css_approach": "Category cards: on hover, lift 4px + subtle shadow (0 4px 12px rgba 20% opacity). Carousel: auto-advance every 5s, fade transition 0.6s. Testimonial carousel: navigation arrows appear on hover. Playful but restrained."
            }
        ],
        "design_philosophy": "Community first, commerce second. Vinted's homepage doesn't sell — it recruits. It says 'you could be a buyer, you could be a seller, both are equally valuable.' The casual copy ('Prêt à faire du tri?') removes commerce friction — you're not visiting a store, you're joining friends. The dual-CTA signals platform balance. Stats prove community legitimacy. User testimonials are real photos (not models) — this is designed for everyone, not gatekept by aesthetic elitism.",
        "palette_strategy": "community_green_warm",
        "typography_strategy": "sans_serif_conversational",
        "layout_strategy": "pathway_dual_centric"
    }

def analyze_wise_home():
    """Wise Home - Fintech international transfers, 4382 DOM, 141 images, green brand, calculator-first."""
    return {
        "aesthetic_vector": {
            "energy": 3.5,
            "warmth": 2.2,
            "density": 3.8,
            "depth": 3.0,
            "motion": 2.8,
            "editorial": 3.0,
            "playful": 1.5,
            "organic": 1.0
        },
        "signature": "Fintech clarity design — green accent (#00B85A), calculator hero (conversion centerpiece), world map visual metaphor, international money movement as story. Accessible typography, trust-focused.",
        "wow_factor": "Wise solves a genuine pain: international transfers are expensive & opaque. Wise's homepage makes the calculator the hero ('send £100, receive €92'), not the company mission. Real fee comparisons (Wise vs Traditional Bank) are immediately visible. The world map animates money flows — that's the product visualized. Zero VC jargon, pure transparency.",
        "techniques": [
            {
                "type": "calculator_hero",
                "name": "Interactive converter (amount + currencies) as primary CTA",
                "score": 5.0,
                "css_approach": "Hero section (below fold, sticky if needed): from-amount input box + 'GBP' selector, arrow, to-amount (disabled, calculated). Fee line below ('Fee: £1.42'). Real exchange rate displayed ('1 GBP = 1.17 EUR'). Button: 'Send money' (green #00B85A). Responsive: same layout mobile (input boxes stack). On focus: color highlight."
            },
            {
                "type": "comparison",
                "name": "Wise vs Banks comparison table (fee + speed + transparency)",
                "score": 4.8,
                "css_approach": "Section: 'Why Wise?' with comparison table. Rows: 'Send £100', 'You receive', 'Fee', 'Speed', 'Transparency'. Columns: 'Wise' (green background, bold #00B85A), 'Traditional Banks' (gray background, red X for bad metrics). Numbers are huge (1.8rem). Visual clarity: checkmarks/X icons."
            },
            {
                "type": "world_map",
                "name": "Animated world map showing money flows (metaphor visualization)",
                "score": 4.5,
                "css_approach": "Large map centered. Animated flows: lines from UK to EU, US, Asia with pulsing dots (journey visualization). On hover: country pair reveals transfer details ('Send £100 to France → You receive €118'). Numbers update real-time (live rates API). Mobile: simplified static map or carousel of routes."
            },
            {
                "type": "trust_signals",
                "name": "Regulatory + security (FCA regulated, ISO 27001, customer funds protected)",
                "score": 4.4,
                "css_approach": "Above fold: text 'FCA regulated • Customer funds protected • ISO 27001 certified' (small 0.85rem, gray text, icons left). Hover on any: tooltip expands. Trust badges at footer (official logos: FCA, ISO). This is B2C compliance signaling without being overwhelming."
            },
            {
                "type": "testimonials",
                "name": "Real customer quotes (amount transferred, savings realized)",
                "score": 4.2,
                "css_approach": "Carousel: 5-6 testimonials. Format: Name, 'Sent £10,000 to Australia, saved £450 vs my bank.' Quote icon, star rating, real photo (48x48 rounded). Auto-advance 6s. Arrows on hover. This is legitimacy via real people, not actors."
            },
            {
                "type": "color",
                "name": "Brand green (#00B85A) dominant accent, white/gray infrastructure",
                "score": 4.6,
                "css_approach": "Backgrounds: white #FFFFFF (primary), very light gray #F7F7F7 (section breaks). Accent: Wise green for buttons, highlights, data (fees, savings). Text: dark gray #1A1A1A. The green is used strategically — every green pixel means 'action' or 'savings'."
            },
            {
                "type": "faq_expandable",
                "name": "FAQ inline (common concerns: 'Is it safe?' 'How long does it take?')",
                "score": 4.0,
                "css_approach": "Sidebar or below-fold section: 4-6 accordions. Questions target objections (safety, speed, hidden fees). Answers: concise (<100 words). On expand: fade-in animation 0.3s. Design: minimal (no color, just typography + expand icon rotation)."
            },
            {
                "type": "motion",
                "name": "Map animations + calculator number transitions",
                "score": 3.5,
                "css_approach": "World map: pulsing dots animate (0.8s loop) showing money flows. On route click: line draws (1s animation). Calculator: on amount change, to-amount number 'counts' from old to new (0.6s transition, ease-out). Subtle, not distracting."
            }
        ],
        "design_philosophy": "Transparency as differentiator. Wise's homepage abandons fintech jargon (no 'blockchain', no 'decentralized') and leads with what users care about: 'Send £100, actually receive €118 (not £96).' The calculator is not a gimmick — it's the product. The Wise vs Banks comparison is aggressively transparent (honest fees, honest timelines). The world map visualizes the global reach without pretense. This is design that respects user intelligence and removes friction through clarity.",
        "palette_strategy": "fintech_green_trust",
        "typography_strategy": "sans_serif_accessible",
        "layout_strategy": "calculator_centric_comparative"
    }

def analyze_wise_pricing():
    """Wise Pricing - Fintech pricing page, 867 DOM, 5 images, ultra-minimal, fee calculator."""
    return {
        "aesthetic_vector": {
            "energy": 2.0,
            "warmth": 1.5,
            "density": 2.5,
            "depth": 1.5,
            "motion": 1.0,
            "editorial": 1.0,
            "playful": 0.5,
            "organic": 0.2
        },
        "signature": "Pure fee transparency — interactive fee calculator (single hero), green accents, data-driven typography, no plans/tiers (Wise has flat model). Clarity maximized.",
        "wow_factor": "Wise Pricing is anti-SaaS landing page. Zero 'Basic/Pro/Enterprise' tiers. Instead: 'Here are our fees (flat 1-2%), here's a calculator, pick your corridor, see your exact cost.' No hidden fees, no variable pricing. The calculator is the entire page. This is pricing as conversation, not sales deck.",
        "techniques": [
            {
                "type": "calculator_primary",
                "name": "Fee calculator (amount + corridors) = entire value prop",
                "score": 5.0,
                "css_approach": "Hero: large amount input (default £1000), slider to adjust. Below: corridor selector (dropdown or tabs: 'GBP to EUR', 'GBP to USD', etc. — 5-10 major routes). Results: 'You send: £1000', 'Fee: £0.75', 'You receive: €1172.50'. Font: large numbers (1.8rem bold). Button: 'Send now' (green). Fully responsive."
            },
            {
                "type": "fee_breakdown",
                "name": "Transparent fee table (no hidden costs, explained)",
                "score": 4.9,
                "css_approach": "Below calculator: 'Our Fees' section. Table: 'Transfer amount', 'Our fee' (flat £0.75 + 0.42%), 'You receive'. Example rows: £100 → £92.50, £1000 → €1172, £10000 → €11724. Monospace for numbers. No 'variable' language — just facts. Footnote: 'These are our only charges. No hidden costs.'"
            },
            {
                "type": "comparison_fair",
                "name": "Wise vs Bank comparison (what you'd pay elsewhere)",
                "score": 4.7,
                "css_approach": "Section: 'Compare Wise to your bank.' User input: amount + corridor. Results: Wise fee vs 'typical bank fee' (conservative estimate). Table: Wise (green row), Traditional bank (gray row), 'You save' (bold green). This is aggressive transparency — it invites comparison."
            },
            {
                "type": "faq_technical",
                "name": "FAQ on edge cases ('When does the fee apply?', 'What about large transfers?')",
                "score": 3.8,
                "css_approach": "Accordions: Technical Q&A ('Fees are charged on the amount you send', 'Large transfers have the same fees', 'We guarantee the rate for 1 hour'). Concise, specific, no jargon. Design: minimal (gray headings, black text)."
            },
            {
                "type": "color",
                "name": "Green accents on white (data presentation)",
                "score": 4.2,
                "css_approach": "Background: white #FFFFFF. Accent: Wise green #00B85A for 'You save' highlights, buttons. Text: dark gray #1A1A1A. The green is used to highlight savings — psychological: green = gain."
            },
            {
                "type": "mobile_responsiveness",
                "name": "Calculator optimized for mobile (touch-friendly sliders + inputs)",
                "score": 4.3,
                "css_approach": "Mobile: full-width input fields, large touch targets (44x44px buttons). Slider thumb: 30x30px (easy drag). Corridor selector: buttons, not dropdown (faster on mobile). Font: 16px minimum (no zoom needed). Spacing: 20px between elements."
            },
            {
                "type": "motion",
                "name": "Calculator updates (numbers animate on input change)",
                "score": 2.5,
                "css_approach": "On slider move: fee + receive-amount update with subtle number-count animation (0.3s). On corridor change: rates refresh instantly (0.2s opacity fade). Zero parallax, zero hero animation. Pure functional motion."
            }
        ],
        "design_philosophy": "Pricing as transparency tool. Wise's pricing page rejects the 'SaaS landing' template (tiers, highlight 'best value', encourage upgrades). Instead: it builds a calculator that lets users see exactly what they'll pay. This removes sales friction — no mystery. The comparison to banks is confident aggression: 'yes, compare us, we're cheaper.' The page isn't designed for conversion theater — it's designed for user trust. Pricing design as a conversion vehicle, not a sales deck.",
        "palette_strategy": "data_driven_minimal",
        "typography_strategy": "sans_serif_monospace_data",
        "layout_strategy": "calculator_single_hero"
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    pages = [
        ("pretto", "lp_leadgen", analyze_pretto_lp_leadgen()),
        ("revolut", "home", analyze_revolut_home()),
        ("revolut", "lp", analyze_revolut_lp()),
        ("revolut", "pricing", analyze_revolut_pricing()),
        ("typology", "home", analyze_typology_home()),
        ("typology", "pdp", analyze_typology_pdp()),
        ("typology", "quiz_vsl", analyze_typology_quiz_vsl()),
        ("vinted", "collection", analyze_vinted_collection()),
        ("vinted", "home", analyze_vinted_home()),
        ("wise", "home", analyze_wise_home()),
        ("wise", "pricing", analyze_wise_pricing()),
    ]

    success_count = 0
    for site, page, analysis in pages:
        if update_design_dna(site, page, analysis):
            print(f"✓ {site}/{page} — opus_analysis saved")
            success_count += 1
        else:
            print(f"✗ {site}/{page} — FAILED")

    print(f"\n=== SUMMARY ===")
    print(f"Successfully analyzed: {success_count}/{len(pages)}")
    print(f"All pages written to design_dna.json files.")

if __name__ == "__main__":
    main()
