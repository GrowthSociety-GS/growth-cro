"""Mega-prompt builder for the GSG legacy LP pipeline.

Three responsibilities:

  1. ``_load_ref_section(ref_name, section_pattern)`` — extract a single
     ``##`` section from one of the markdown reference files in
     ``skills/growth-site-generator/references/`` (PAS, BAB, Headline
     formulas, Schwartz, Cialdini, biais cognitifs, CRO errors, listicle
     spec — all were dormant pre-V26.Y.7).
  2. ``PAGE_TYPE_SPECS`` + ``ANTI_AI_SLOP_DOCTRINE`` constants — the
     prescriptive doctrine blocks dropped into every mega-prompt.
  3. ``build_mega_prompt(...)`` — assembles brand_dna + design_grammar +
     creative route + AURA + golden bridge + page spec + frameworks +
     competitor BAN list + anti-AI-slop into the final string.

Optional ``creative_director`` integration is loaded once at module
import; if absent, ``render_creative_route_block`` becomes a no-op
returning ``""``.

Split from ``gsg_generate_lp.py`` (issue #8). Pulls block helpers from
``brand_blocks`` and reuses ``ROOT`` from ``data_loaders``.
"""
from __future__ import annotations

import re
from typing import Optional

from .brand_blocks import (
    render_aura_block,
    render_brand_block,
    render_brand_dna_diff_block,
    render_design_grammar_block,
)
from .data_loaders import ROOT


# V26.Z E2 : Creative Director pour génération multi-routes nommées
try:
    from creative_director import (  # type: ignore
        generate_routes as cd_generate_routes,
        select_route as cd_select_route,
        render_creative_route_block,
    )
    _CREATIVE_DIRECTOR_AVAILABLE = True
except ImportError:
    _CREATIVE_DIRECTOR_AVAILABLE = False
    cd_generate_routes = None
    cd_select_route = None

    def render_creative_route_block(*_args, **_kwargs):  # noqa: D401 — no-op fallback
        return ""


def _load_ref_section(ref_name: str, section_pattern: str, max_chars: int = 3500) -> str:
    """Extract a section from a reference file by markdown heading pattern."""
    fp = ROOT / "skills" / "growth-site-generator" / "references" / f"{ref_name}.md"
    if not fp.exists():
        return ""
    text = fp.read_text()
    # Find all top-level ## sections
    matches = list(re.finditer(r'^## ', text, re.MULTILINE))
    target_match = None
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[m.start():end]
        if section_pattern in chunk:
            target_match = chunk
            break
    if not target_match:
        return ""
    return target_match[:max_chars]


PAGE_TYPE_SPECS = {
    "listicle": """
## PAGE TYPE : LISTICLE LP A6 (sections obligatoires GSG)

Sections OBLIGATOIRES (cf page_types.md A6) :
1. **Hero listicle** — Headline CHIFFRÉ accrocheur (le chiffre est le hook).
2. **Intro pourquoi-cette-liste** — 2-3 phrases narratives en framework PAS : pourquoi ces tips importent, qui doit les savoir, ce qui se passe sinon.
3-12. **N items** numérotés (typiquement 7 à 12), chacun :
   - **H2 NARRATIF CONCRET** : tu écris UN H2 ORIGINAL pour CE produit, à partir de la doctrine GSG (cf Headline Formulas SECTION F injectée). Tu connais la marque, le ton voice_tokens, l'audience — exprime-toi.
   - **PRINCIPES de H2 CONCRET** (tu choisis ton angle parmi ceux-ci) :
     A. Image sensorielle "le temps que [scène quotidienne courte]"
     B. Scène concrète "Un [acteur] qui [action] dans [délai]"
     C. Anti-friction "Plus de [pénibilité ancienne]. [Nouveau geste simple]."
     D. Objection retournée "Le [élément] que [acteur] aurait oublié, [outil] le voit"
     E. Transformation visualisée "Un [élément FR] avec X devient un [élément étranger] avec Y"
     F. Différenciation locale "Un [acteur] qui [verbe], en [langue locale], [délai court]"
     G. Preuves brutes 3 chiffres "X marques. Y/5 sur [plateforme]. Leader Z depuis N ans."
     H. Stack technique exhaustif "[Liste vraie des intégrations], et tout le reste"
     I. Promesse opposée à la perception "[Action perçue lente] en [unité de temps surprenante]"
   - **INTERDIT** : H2 plats génériques type "Installation simple" / "SEO international" / "Détection automatique" / "Compatibilité totale" / "Support réactif" / "Preuve sociale". Ces formulations sont BANNIES — c'est précisément l'AI-slop que la doctrine combat.
   - **INTERDIT** : copier littéralement les exemples principes ci-dessus. Ce sont des principes pour ton inspiration, pas des H2 prêts à coller. Tu inventes pour CE client.
   - 100-250 mots de body narratif par item (pas bullet points safe). Une scène concrète, une analogie, un chiffre, une objection levée.
   - Si pertinent : pull quote, demo box, widget interactif (1-2 max sur tout le LP)
13. **Section Before/After (BAB framework)** — Titre du genre "Ce qui change concrètement [sur N dimensions]" : tableau ou liste avant/après en N points.
14. **CTA transition + Final CTA** mesh gradient
15. **FAQ accordéon** OBLIGATOIRE — 6-8 objections fréquentes (prix/migration/support/limites/ROI/sécurité). Format Q/R, ton conversationnel direct.
16. **Footer** minimal éditorial mono caps

Frameworks copy à utiliser :
- **PAS** (Problem-Agitate-Solution) en intro narrative obligatoire
- **Storytelling concret** sur les items (scènes mentales, pas features)
- **Voice tokens client** : utilise tone + CTA verbs + sentence_rhythm du brand_dna. Si voice_tokens.tone = ["consultant senior", "FR direct"], écris comme tel — pas un copywriter générique IA.

Niveau de conscience Schwartz : Problem/Solution Aware → Most Aware (audience B2B SaaS DTC qui hésite à choisir)

⚠️ TON DEVOIR : exprime LIBREMENT la doctrine GSG (PAS + headline formulas SECTION F + Cialdini + biais cognitifs + voice_tokens client) pour produire des H2 originaux pour CE client précis. Pas de copie d'exemples, pas de formulations safe — narration concrète, "tu" français direct si voice_tokens l'indique, scènes mentales spécifiques au business du client.
""",
    "lp_sales": """## PAGE TYPE : LP SALES — hero + USPs + proof + objections + FAQ + CTA""",
    "lp_leadgen": """## PAGE TYPE : LP LEAD GEN — hero + value prop + form inline + proof + FAQ""",
}


ANTI_AI_SLOP_DOCTRINE = """
## ANTI-AI-SLOP DOCTRINE (V22 Growth Society + design_system.md)

### Bannir absolument :
- Bento grids carrés safe (pattern Linear/Notion clone)
- Pastels safe-warm-polished (gradient mauve→rose générique)
- Plus Jakarta Sans / Space Grotesk / Inter en heading (overusé AI)
- Friendly polite copy ("✨ Welcome!" "Let's get started")
- Lottie animations génériques
- Stock business handshake photos
- Cards avec border-radius 16px + soft shadow uniforme
- Hero text-align center safe avec illustration abstraite à droite
- Buttons gradient générique (pink→purple, blue→cyan)

### Adopter à la place :
- **Asymétrie éditoriale** : sidebar TOC + main column (pas split 50/50)
- **Drop caps** géant first paragraph (5em+, italic primary)
- **Pull quotes** éditoriales (border-left 3px + italic + quote décoratif)
- **Mixed weights typography** dans même heading (350 + 500 + italic)
- **Oversized numerals** (4-7rem italic primary)
- **Type-as-decoration** (pas d'icones inutiles, lettres = visual)
- **Filets éditoriaux** verticaux entre stats (pas grid bento)
- **Grain noise overlay** SVG fractalNoise opacity 0.04-0.06
- **Mesh gradient ANIMÉ** sur final CTA (3 radial gradients qui shift slow)
- **Glass + saturation 187%** sur masthead sticky
- **Spring motion** cubic-bezier(0.34, 1.56, 0.64, 1) pas ease générique
- **Highlight surligneur** jaune sur chiffre signature (pas fond block plein)
- **Logo bar prestige** italic font-display, hover opacity (pas grayscale)
- **Stat-shock** pleine page format magazine (1 num géant + caption italic)
- **Sidebar TOC** mono caps avec active state primary border-left
- **SVG décoratif inline** (concentric circles, lines, motifs liés au business)
- **Asymmetric reveal** scroll animations (pas tous fade-up uniforme)
- **Custom scrollbar** primary couleur

### Densité éditoriale > densité SaaS :
- line-height body 1.65-1.75 (pas 1.5 SaaS)
- Paragraphes 2-3 phrases (pas bullet points partout)
- "code inline" pour références tech (pas pills colored)
- 1 image d'image direction (pas 5 illustrations abstraites)
- Vraies phrases narratives (pas "Faster. Better. Smarter." 3 mots)
"""


def build_mega_prompt(client: str, brand_dna: dict, aura: dict, golden_prompt: str,
                      page_type: str, business_context: str,
                      copy_hints: str, target_url: str,
                      reference_competitor_html: str = "",
                      design_grammar: Optional[dict] = None,
                      creative_route: Optional[dict] = None,
                      route_selection_meta: Optional[dict] = None) -> str:
    spec = PAGE_TYPE_SPECS.get(page_type, PAGE_TYPE_SPECS["listicle"])
    design_grammar = design_grammar or {}

    # V26.Y.8 : injecter les sections clés des références GSG (étaient ignorées V26.Y.7)
    # 7 872 lignes de doctrine GSG inutilisées → fix : extract sections critiques
    pas_framework = _load_ref_section("copy_frameworks", "A1. PAS", max_chars=2000)
    bab_framework = _load_ref_section("copy_frameworks", "A4. BAB", max_chars=2000)
    headline_formulas = _load_ref_section("copy_frameworks", "SECTION F", max_chars=4000)
    schwartz_levels = _load_ref_section("copy_frameworks", "SECTION C", max_chars=2500)
    cialdini = _load_ref_section("conversion_psychology", "PRINCIPES DE CIALDINI", max_chars=4500)
    cognitive_biases = _load_ref_section("conversion_psychology", "BIAIS COGNITIFS", max_chars=3500)
    cro_errors = _load_ref_section("cro_checklist", "ERREURS CLASSIQUES", max_chars=3000)
    listicle_spec = _load_ref_section("page_types", "A6. Listicle", max_chars=2000)

    competitor_block = ""
    if reference_competitor_html:
        # V26.Y.9 : ne PAS donner le HTML complet (Sonnet l'a copié iter4).
        # Au lieu de ça : extraire structure + bannir les H2 spécifiques.
        # Extract competitor H2 to BAN them (force originality)
        h2_matches = re.findall(r'<h2[^>]*>([^<]+)</h2>', reference_competitor_html)
        comp_h2_list = [h.strip() for h in h2_matches if len(h.strip()) > 5]
        competitor_block = f"""

## CONTRAINTES STRUCTURELLES (apprises d'une référence externe — TU NE LA VOIS PAS)

Une référence externe haut de gamme existe sur ce sujet. Sa structure :
- **2556 mots de copy minimum** (ton TOI doit en faire ≥ 2 600)
- **14+ H2 narratifs concrets** (pas génériques)
- Intro narrative en framework PAS (Problem-Agitate-Solution)
- 10 raisons numérotées avec H2 punchy + body 100-200 mots chacune
- Section BAB "Ce qui change concrètement, sur N dimensions" obligatoire
- Section FAQ obligatoire (6-8 questions/réponses)
- CTA final massif

## ⛔ PHRASES BANNIES (la référence externe les utilise — JAMAIS les reproduire)

Tu ne peux PAS écrire ni paraphraser proche ces formulations :
{chr(10).join('- "' + h + '"' for h in comp_h2_list[:20])}

Tu écris des H2 narratifs ORIGINAUX, avec ton angle propre. Style attendu :
- Images sensorielles ("le temps que X" / "vu depuis Y" / "qui Z avant W")
- Tutoiement français direct ("Tu installes" / "Tu cliques" / "Ton équipe")
- Scènes mentales concrètes (lieu, temps, action — pas concepts abstraits)
- Spécificité business (pas "rapide", dire "5 minutes" ; pas "compatible", dire "WordPress, Shopify, Webflow")
- Anti-jargon ("Plus de tableurs" mieux que "Workflow simplifié")

## ⚠️ CONTRAINTES STRICTES BRAND DNA (interdit de violer)

- **Palette** : utilise UNIQUEMENT les couleurs du brand_dna client (--color-primary {brand_dna.get('visual_tokens', {}).get('colors', {}).get('palette_full', [{}])[0].get('hex', '#493ce0') if isinstance(brand_dna.get('visual_tokens', {}).get('colors', {}).get('palette_full'), list) else '#493ce0'} + secondary + neutrals AURA computés). **INTERDIT** d'inventer des couleurs (genre #ffd966 highlight ou #ce9b96 sand). Si tu as besoin d'un highlight, utilise l'accent du brand_dna ou une variante alpha de --color-primary.
- **Fonts** : MAX 2 font-families totales (1 display + 1 body). Pas 3, pas 4. Le ff-accent est optionnel uniquement pour code/mono.
- **Cohérence** : tous les éléments respectent les --color-* de l'AURA tokens block.
"""

    return f"""Tu es **directeur artistique senior + COPYWRITER CRO senior + dev front senior** pour Growth Society. Tu reçois un brief BRAND DNA + AURA tokens + Golden Design intelligence + DOCTRINE COPY GSG complète et tu produis une LP **stratosphérique** : copy concret narratif punchy ET visuel anti-AI-slop top 0.001% Awwwards/FWA.

# CLIENT : {client.upper()} ({target_url})

# BUSINESS CONTEXT (audit web GrowthCRO)
{business_context}

{render_brand_block(brand_dna)}

{render_brand_dna_diff_block(brand_dna)}

{render_design_grammar_block(design_grammar)}

{render_creative_route_block(creative_route, route_selection_meta) if creative_route else ""}

{render_aura_block(aura)}

## GOLDEN DESIGN BENCHMARKS (cross-catégorie matching)
{golden_prompt}

{spec}

## DOCTRINE COPY GSG — frameworks à utiliser explicitement (était oublié V26.Y.7)

### Framework PAS (intro narrative obligatoire)
{pas_framework}

### Framework BAB (section "Ce qui change concrètement, sur N dimensions" obligatoire)
{bab_framework}

### Niveaux de conscience Schwartz (positionner copy au bon niveau)
{schwartz_levels}

### Headline formulas (utiliser pour TOUS les H2 items, JAMAIS génériques)
{headline_formulas}

### Cialdini × 6 (les 6 doivent être détectables dans la LP)
{cialdini}

### Biais cognitifs exploitables CRO (en activer ≥5)
{cognitive_biases}

### 11 erreurs classiques CRO (à éviter absolument)
{cro_errors}

### Spec exacte Listicle LP A6 (sections obligatoires)
{listicle_spec}

{competitor_block}

{ANTI_AI_SLOP_DOCTRINE}

## COPY HINTS (rough — peaufiner intelligemment)
{copy_hints}

## OUTPUT REQUIREMENTS

Tu produis UN SEUL fichier HTML auto-contenu (style + script inline) :
- DOCTYPE + html lang fr + meta viewport + meta description (SEO-aware)
- **Open Graph + Twitter Cards** : og:title, og:description, og:image (placeholder /og-image.jpg si pas dispo), twitter:card="summary_large_image", canonical URL
- **Typographie** : si la font display brand est PP Neue Montreal / Söhne / Clash Display / autre payante, importe **Geist** (Vercel font, Google Fonts) OU **Cabinet Grotesk** (Fontshare via lien CSS direct) OU **General Sans** Variable comme substitut display tight grotesque. Stack : `font-family: 'PP Neue Montreal', 'Geist', 'Cabinet Grotesk', sans-serif;`. **Sous AUCUNE circonstance** silencieusement fallback Inter pour heading.
- **Accessibility** : skip-to-main link, focus-visible custom (outline 3px primary), aria-label sur widgets/icons, contrast WCAG AA min, semantic HTML5

## ⛔ CRITICAL — RENDU PAR DÉFAUT VISIBLE (Bug-Fix V26.Z)

**Cause d'un bug MAJEUR dans les générations précédentes** : tu produis du HTML
où les chiffres sont à 0 par défaut + un JS d'animation counter — mais le `<script>`
de fin se fait tronquer ou oublier, donc l'utilisateur voit une page entièrement
en "0", visuellement morte. Les juges automatiques ne détectent pas ce bug
(ils lisent le HTML brut, pas le rendu). Pour cette raison, **règles absolues** :

### Pattern INTERDIT
```html
<!-- ❌ NEVER : chiffre à 0 par défaut qui dépend d'un JS pour s'afficher -->
<span class="stat-number" data-target="327">0</span>
<div class="stat-value" data-target="111368">0</div>
```

### Pattern OBLIGATOIRE
```html
<!-- ✅ ALWAYS : la valeur finale est DANS le HTML par défaut -->
<span class="stat-number" data-target="327">327</span>
<div class="stat-value" data-target="111368">111 368</div>
```

L'attribut `data-target` peut rester pour le JS d'animation, mais le **texte par
défaut DOIT être la valeur finale lisible**. Si tu animes le counter, tu peux
faire start FROM 0 dans le JS et terminer sur la valeur — mais avant que le JS
tourne (ou s'il plante), l'utilisateur DOIT voir le bon chiffre.

### Autres règles failsafe rendering
- **Aucun `opacity: 0` par défaut** sur du contenu textuel important sans une
  `transition` ou `@keyframes` explicite qui le fait passer à 1. Si tu fais des
  reveal animations, fais-les avec `transform: translateY(20px)` + `opacity: 0.5`
  → état final visible même sans JS.
- **Si tu inclues un `<script>` JS** : il DOIT être en fin de body, complet,
  syntaxiquement valide. Tester mentalement : "si ce script plante, est-ce que
  la page reste utilisable ?" → la réponse doit être OUI.
- **Format des chiffres > 999** : utiliser séparateurs FR avec espace fine
  (`111 368`, `1 300 000`) ou format compact (`1,3M`, `111K`). Pas de virgules
  US. Pas de chiffres bruts sans séparateur.
- **Counter animations** : même si tu animes, le CSS `text-content` du span doit
  être la valeur finale visible — JS ne fait que démarrer un loop FROM 0.

### ⛔ INTERDIT ABSOLU — Pattern reveal-class (cause de bug majeur V26.Z)

**N'utilise JAMAIS ce pattern** :
```css
/* ❌ NEVER : opacity 0 par défaut + classe reveal ajoutée par JS */
.stat-item, .listicle-item, .widget-result {{
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.6s, transform 0.6s;
}}
.stat-item.revealed, .listicle-item.revealed {{ opacity: 1; transform: translateY(0); }}
```

Pourquoi : ce pattern dépend d'un `IntersectionObserver` qui ajoute `.revealed`
au scroll. Si tu oublies le JS (ou si le JS plante), TOUTES LES SECTIONS RESTENT
INVISIBLES — la page semble vide après le hero. C'est exactement le bug qu'on
a corrigé en V26.Z. **Aucune classe nommée `.revealed` / `.show` / `.visible` /
`.in-view` / `.animated` / `.is-visible` ne doit conditionner l'apparition d'un
contenu textuel.**

**À LA PLACE, utilise des animations CSS-only auto-play** :
```css
/* ✅ ALWAYS : animation se déclenche au load, sans JS */
.stat-item {{
  opacity: 0;
  transform: translateY(20px);
  animation: revealUp 0.8s ease-out forwards;
  animation-delay: calc(var(--idx, 0) * 0.1s);  /* stagger via CSS variable */
}}
@keyframes revealUp {{
  to {{ opacity: 1; transform: translateY(0); }}
}}
```

OU **état final visible par défaut, animation purement décorative** :
```css
/* ✅ ALWAYS : visible même sans CSS animation, le animate juste polish au scroll */
.stat-item {{
  opacity: 1;
  /* Si tu veux ajouter du polish au scroll : utilise scroll-driven animations
     (CSS native) ou view() — pas de classe .revealed à ajouter via JS */
}}
@supports (animation-timeline: view()) {{
  .stat-item {{
    animation: subtle-rise linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 30%;
  }}
}}
```

Si tu veux ABSOLUMENT du reveal-on-scroll classique, INCLUS le JS COMPLET en
fin de body, et teste mentalement "si ce script plante, est-ce que tout reste
visible ?" — si non, c'est interdit.

## TECHNIQUES OBLIGATOIRES (≥20 / 42 catalogées)

Tu DOIS intégrer **au moins 20** de ces techniques avancées (pas 5-8 safe AI-default — vingt). Sois ambitieux :

### Backgrounds & Atmosphère (≥4)
1. **Gradient Mesh Animé** dans hero ou final CTA (3-4 radial gradients qui shift via @keyframes 20s+)
2. **Noise/Grain Overlay** SVG fractalNoise opacity 0.04-0.08 mix-blend-mode multiply (V22 doctrine signature)
3. **Glass / Frosted Effect** sur masthead sticky (backdrop-filter blur 12-15px + saturate 187%)
4. **Lignes Diagonales** ou **Dot Grid Pattern** ou **Geometric Gradient Pattern** ou **Radial Burst** ou **Organic Blob Background** — choisir 1-2

### Typographie avancée (≥4)
5. **Oversized Typography** hero (clamp 4-7rem italic primary)
6. **Text Gradient Clip** (background-clip:text + WebkitBackgroundClip + couleur transparente sur 1 mot-clé)
7. **Highlight / Marker Effect** (surligneur jaune skewé sur chiffre signature — pas un fond block)
8. **Drop Cap Géant** (5-6em, italic, primary, float left sur lede)

### Layout asymétrique (≥3)
9. **Asymmetric Split Hero** (60/40 ou 70/30, pas 50/50 ennuyeux)
10. **Editorial Layout** texte + image offset (sidebar TOC sticky desktop only)
11. **Alternating Section Widths** (rythme 60/40 puis 40/60)
12. **Overlap Grid** (1-2 éléments qui se chevauchent visuellement)

### Animation & Motion (≥4)
13. **Scroll Reveal avec Stagger** (IntersectionObserver, delay 0.12s entre items)
14. **Counter Animation** (compteurs 0→valeur en 2s au scroll reveal — OBLIGATOIRE sur stats bar : 111368, 400, 20, 1300000)
15. **Parallax Layer** subtil (translate3d sur 1-2 éléments décoratifs au scroll)
16. **Marquee / Infinite Scroll Text** (logo bar prestige défile en boucle horizontale lente — OBLIGATOIRE pour le logo bar)
17. **Magnetic Button Effect** (mousemove → translate du final CTA primary button vers cursor, intensity 0.2-0.3)
18. **Cursor Glow Effect** (div suit cursor avec radial-gradient violet primary, opacity 0.15 ; ou sur quelques éléments seulement)

### Interactions micro (≥3)
19. **Hover Depth on Cards** (transform translateY(-4px) + scale(1.02) + shadow renforcé)
20. **Clip-Path Reveal** (sur 1-2 sections au scroll, animation clip-path inset)
21. **Smooth Scroll** custom (CSS scroll-behavior + ancres TOC fluides)

### Décoration SVG (≥5 SVG inline distincts contextuels)
22. **5+ SVG inline décoratifs** contextuels au business (pas génériques) : motifs concentriques, lignes ondulées, icônes business-relevant, dividers ornementaux, illustrations abstraites liées au sujet (pour Weglot : globe filaire / flèches bidirectionnelles / drapeaux stylisés / curseur traduction / waveforms langues etc.)

## SECTIONS RICHESSE OBLIGATOIRES

- **Marquee logo bar** : pas un grid statique, marquee infinite continuous animation 30s linear loop avec ≥10 logos clients (texte typographique italic Fraunces ou similar) qui défilent
- **Stats animées** : 4 KPI compteurs (111368, 400%, 20%, 4.9/5) avec animation scroll reveal + count-up
- **Stat-shock pleine page** : 1 chiffre massif (1 300 000) animé compteur + caption italic + source mono
- **Pull quotes** : 2-3 éditoriales avec quote " décoratif primary opacity 0.18, italic display, border-left 3px
- **Demo box** : ≥1 (style terminal/log timestamp ou widget data viz)
- **Widget interactif** : 1 ≥ (CMS picker, calculator, etc.) — avec feedback animé post-clic
- **Mesh gradient final CTA** animé (3 radials shift 20s + noise overlay + glow effect)
- **Floating CTA sticky** apparition après scroll past hero, magnetic effect
- **Footer** minimal éditorial mono caps
- CSS custom properties basées sur AURA tokens block (utilise les --color-*, --ff-*, --fs-*)
- Pas de framework externe (pas de Tailwind/Bootstrap)
- Mobile-first responsive (breakpoints 720px desktop, 1080px wide)
- Animations JS minimal : scroll progress, reveal observer, widget interactif, floating CTA visible/hidden
- Accessibility : aria-label, focus states, contrast WCAG AA min
- Performance : lazy reveal, transform/opacity only, 60fps
- Cible 1200-1800 lignes total (HTML + CSS + JS) pour densité éditoriale ambitieuse

**JAMAIS de markdown dans la réponse.** UNIQUEMENT le HTML brut depuis <!DOCTYPE html> jusqu'à </html>. Pas de ```html fences, pas de prose explicative."""


__all__ = [
    "_load_ref_section",
    "PAGE_TYPE_SPECS",
    "ANTI_AI_SLOP_DOCTRINE",
    "build_mega_prompt",
    "render_creative_route_block",
    "cd_generate_routes",
    "cd_select_route",
    "_CREATIVE_DIRECTOR_AVAILABLE",
]
