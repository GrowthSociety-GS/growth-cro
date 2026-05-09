"""GSG Generate LP — V26.Y full pipeline orchestrator.

Lit :
  - data/captures/<client>/brand_dna.json (V29 Phase 1+2)
  - aura_compute output (mode B fixé V26.Y.2)
  - golden_design_bridge output (cross-catégorie matching prompt)
  - skills/growth-site-generator/references/ (design_engine.md, swipe_library.md, etc.)
  - business audit context (insights manuels via --context)

Construit un mega-prompt structuré pour Sonnet :
  • Brand DNA token block (palette + typo + voice + image_direction + asset_rules)
  • AURA computed tokens block (vector 8D + spacing φ + motion + depth)
  • Golden Design benchmarks (3-5 sites + techniques cross-catégorie ciblées)
  • Page-type spec (listicle / sales / lead-gen) avec sections obligatoires
  • Anti-AI-slop directives (V22 doctrine + design_system.md)
  • Self-audit grid (51 critères × 153 pts) à appliquer

Sonnet génère HTML auto-contenu mobile-first.

Usage :
    python3 skills/growth-site-generator/scripts/gsg_generate_lp.py \
        --client weglot --page-type listicle \
        --energy 4 --tonality 3 --registre editorial \
        --output deliverables/weglot-listicle-V26Y-AURA.html
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "captures"
SCRIPTS = ROOT / "skills" / "growth-site-generator" / "scripts"

SONNET_MODEL = "claude-sonnet-4-5-20250929"

# Make sibling scripts importable (creative_director, etc.)
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# V26.Z E2 : Creative Director pour génération multi-routes nommées
try:
    from creative_director import (
        generate_routes as cd_generate_routes,
        select_route as cd_select_route,
        render_creative_route_block,
    )
    _CREATIVE_DIRECTOR_AVAILABLE = True
except ImportError:
    _CREATIVE_DIRECTOR_AVAILABLE = False
    def render_creative_route_block(*_args, **_kwargs):  # noqa: D401
        return ""

# V26.Z P0 : post-process automatique des bugs rendering
# Le mega-prompt (même renforcé iter3) ne suffit pas à empêcher Sonnet de
# régénérer les patterns problématiques (counter à 0, reveal-class).
# fix_html_runtime() est maintenant appelé AUTOMATIQUEMENT après chaque
# génération HTML pour garantir un rendu visible — code défensif.
try:
    from fix_html_runtime import fix_html_runtime, detect_runtime_bugs
    _RUNTIME_FIX_AVAILABLE = True
except ImportError:
    _RUNTIME_FIX_AVAILABLE = False


def auto_fix_runtime(html: str, label: str = "", verbose: bool = True) -> tuple[str, dict]:
    """V26.Z P0 — applique fix_html_runtime() automatiquement après une génération.

    Toujours injecte le JS fallback (counter + reveal) si nécessaire.
    Toujours patch CSS direct si reveal pattern détecté.

    Returns: (fixed_html, report) — report contient before/after broken_score
    pour traçabilité.
    """
    if not _RUNTIME_FIX_AVAILABLE:
        return html, {"skipped": "fix_html_runtime not importable"}

    fixed_html, report = fix_html_runtime(html, inject_js=True, fix_reveal_pattern=True)
    before = report["before"]
    after = report["after"]
    if verbose:
        if before["broken_score"] > 0.0:
            print(f"  [P0 auto-fix{f' {label}' if label else ''}] "
                  f"broken_score: {before['broken_score']} ({before['broken_severity']}) "
                  f"→ {after['broken_score']} ({after['broken_severity']})", flush=True)
            if report.get("fixed_counters"):
                print(f"    fixed counters: {report['fixed_counters']}", flush=True)
            if report.get("fixed_reveal_pairs"):
                print(f"    fixed reveal pairs: {report['fixed_reveal_pairs']}", flush=True)
            if report.get("injected_js"):
                print(f"    injected runtime JS fallback (counter + reveal)", flush=True)
        else:
            print(f"  [P0 auto-fix{f' {label}' if label else ''}] no rendering bugs detected", flush=True)
    return fixed_html, report


def load_brand_dna(client: str) -> dict:
    fp = DATA / client / "brand_dna.json"
    if not fp.exists():
        sys.exit(f"❌ {fp} not found. Run brand_dna_extractor first.")
    return json.loads(fp.read_text())


def load_design_grammar(client: str) -> dict:
    """Load les 7 fichiers prescriptifs design_grammar V30 d'un client.

    V26.Z W2 : ces fichiers étaient générés pour 51 clients mais JAMAIS lus
    par le générateur (faille découverte dans l'audit post-V26.Y). Ce loader
    + render_design_grammar_block() les injecte enfin dans le mega-prompt.

    Retourne dict vide si client n'a pas de design_grammar/ (graceful fallback).
    """
    dg_dir = DATA / client / "design_grammar"
    if not dg_dir.is_dir():
        return {}
    grammar = {}
    for json_file in ("composition_rules.json", "section_grammar.json",
                      "component_grammar.json", "brand_forbidden_patterns.json",
                      "quality_gates.json", "tokens.json"):
        fp = dg_dir / json_file
        if fp.exists():
            try:
                grammar[json_file.replace(".json", "")] = json.loads(fp.read_text())
            except json.JSONDecodeError:
                pass
    return grammar


def compute_aura_tokens(client: str, energy: float, tonality: float,
                         business: str, registre: str) -> dict:
    """Lance aura_compute en mode B fixé."""
    bd_fp = DATA / client / "brand_dna.json"
    out_fp = ROOT / "data" / f"_aura_{client}.json"
    cmd = [
        "python3", str(SCRIPTS / "aura_compute.py"),
        "--brand-dna", str(bd_fp),
        "--energy", str(energy),
        "--tonality", str(tonality),
        "--business", business,
        "--registre", registre,
        "--output", str(out_fp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(f"❌ aura_compute failed: {r.stderr}")
    return json.loads(out_fp.read_text())


def golden_bridge_prompt(vector: dict, top: int = 5) -> str:
    """Lance golden_design_bridge.py et retourne le prompt block."""
    cmd = [
        "python3", str(SCRIPTS / "golden_design_bridge.py"),
        "--vector", json.dumps(vector),
        "--top", str(top),
        "--prompt",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        return f"(golden bridge failed: {r.stderr})"
    # Strip first line "Loaded N profiles..." if present
    out = r.stdout
    lines = out.split("\n")
    return "\n".join(l for l in lines if not l.startswith("Loaded "))


def render_brand_dna_diff_block(brand_dna: dict) -> str:
    """V26.Z E1 : expose le Brand DNA Diff (preserve/amplify/fix/forbid) au mega-prompt.

    Si le client a `brand_dna.diff` (généré par brand_dna_diff_extractor V26.Z E1),
    on injecte les 4 quadrants opérationnels. Sinon on retourne string vide
    (graceful fallback : le pipeline continue avec render_brand_block seul).

    C'est la couche PRESCRIPTIVE qui dit à Sonnet "ce qu'il FAUT faire", pas
    juste "ce qui EST" (faille #2 résolue).
    """
    diff = brand_dna.get("diff")
    if not diff or diff.get("error"):
        return ""

    block = "## BRAND DNA DIFF (V26.Z E1 — couche PRESCRIPTIVE)\n\n"
    block += "Le brand_dna ci-dessus dit ce qui EST. Ce diff dit ce qu'il FAUT FAIRE pour cette LP.\n"
    summary = diff.get("summary")
    if summary:
        block += f"\n**Posture stratégique** : {summary}\n"
    block += "\n"

    # PRESERVE — forces à garder
    preserve = diff.get("preserve") or []
    if preserve:
        block += "### 🟢 PRESERVE (forces réelles à GARDER absolument)\n"
        for item in preserve[:6]:
            if isinstance(item, dict):
                block += f"  - {item.get('item','?')}"
                if item.get("evidence"):
                    block += f" *(evidence : {item['evidence'][:100]})*"
                block += "\n"
            else:
                block += f"  - {item}\n"
        block += "\n"

    # AMPLIFY — sous-exploité à pousser
    amplify = diff.get("amplify") or []
    if amplify:
        block += "### 🟡 AMPLIFY (sous-exploité à POUSSER plus loin)\n"
        for item in amplify[:6]:
            if isinstance(item, dict):
                block += f"  - {item.get('item','?')}\n"
                if item.get("how"):
                    block += f"    → comment : {item['how'][:160]}\n"
            else:
                block += f"  - {item}\n"
        block += "\n"

    # FIX — faiblesses à corriger (LE QUADRANT MANQUANT V26.Y)
    fix = diff.get("fix") or []
    if fix:
        block += "### 🔴 FIX (faiblesses CONCRÈTES à CORRIGER — priorité absolue)\n"
        # Sort by priority high → medium → low
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        sorted_fix = sorted(fix, key=lambda x: priority_rank.get(
            x.get("priority", "low") if isinstance(x, dict) else "low", 2))
        for item in sorted_fix[:8]:
            if isinstance(item, dict):
                pri = item.get("priority", "?")
                block += f"  - **[{pri}]** {item.get('item','?')}\n"
                if item.get("fix_directive"):
                    block += f"    → directive : {item['fix_directive'][:200]}\n"
            else:
                block += f"  - {item}\n"
        block += "\n"

    # FORBID — anti-patterns
    forbid = diff.get("forbid") or []
    if forbid:
        block += "### ⛔ FORBID (anti-patterns INTERDITS pour cette marque)\n"
        for item in forbid[:8]:
            if isinstance(item, dict):
                block += f"  - {item.get('item','?')}\n"
            else:
                block += f"  - {item}\n"

    return block


def render_brand_block(brand_dna: dict) -> str:
    """Format brand_dna pour prompt LLM — compact, lisible."""
    vt = brand_dna.get("visual_tokens") or {}
    voice = brand_dna.get("voice_tokens") or {}
    img_dir = brand_dna.get("image_direction") or {}
    assets = brand_dna.get("asset_rules") or {}

    colors = vt.get("colors") or {}
    typo = vt.get("typography") or {}

    block = "## BRAND DNA (V29 Phase 1+2 extracted) — RESPECTER À 100%\n\n"
    block += "### Couleurs\n"
    if colors.get("palette_full"):
        for c in colors["palette_full"][:6]:
            block += f"  - {c.get('hex')} (coverage {c.get('coverage_pct', 0)*100:.1f}%)\n"
    block += "\n### Typographie (préserver familles)\n"
    for key in ("h1", "h2", "h3", "body", "button"):
        t = typo.get(key) or {}
        if t.get("family"):
            block += f"  - {key}: {t.get('family')} {t.get('weight','')} {t.get('size_px','?')}px lh={t.get('line_height','?')}\n"

    if voice.get("tone"):
        block += "\n### Voice tokens (ton + forbidden + CTA)\n"
        block += f"  - tone: {', '.join(voice.get('tone') or [])}\n"
        if voice.get("forbidden_words"):
            block += f"  - FORBIDDEN: {', '.join(voice['forbidden_words'])}\n"
        if voice.get("preferred_cta_verbs"):
            block += f"  - CTA verbs préférés: {', '.join(voice['preferred_cta_verbs'])}\n"
        if voice.get("voice_signature_phrase"):
            block += f"  - Signature: \"{voice['voice_signature_phrase']}\"\n"

    if img_dir.get("photo_style"):
        block += "\n### Image direction (LLM Vision)\n"
        for k in ("photo_style", "lighting", "composition", "color_treatment", "subject_focus", "image_to_text_ratio"):
            if img_dir.get(k):
                block += f"  - {k}: {img_dir[k]}\n"
        if img_dir.get("do_not_use"):
            block += f"  - DO NOT USE: {', '.join(img_dir['do_not_use'])}\n"
        if img_dir.get("signature_visual_motif"):
            block += f"  - signature motif: {img_dir['signature_visual_motif']}\n"

    if assets.get("approved_techniques"):
        block += "\n### Asset rules (techniques approuvées)\n"
        for t in (assets.get("approved_techniques") or [])[:6]:
            block += f"  - {t}\n"
        if assets.get("do_not"):
            block += "\n  DO NOT:\n"
            for t in (assets.get("do_not") or [])[:6]:
                block += f"  - {t}\n"

    return block


def render_design_grammar_block(grammar: dict) -> str:
    """Format design_grammar V30 prescriptif pour mega-prompt.

    V26.Z W2 : couche prescriptive (preserve/amplify/forbid + thresholds chiffrés).
    Le brand_dna dit "ce qui EST". Le design_grammar dit "ce qu'il FAUT FAIRE et
    NE PAS FAIRE" pour cette marque. Cette couche était fossilisée jusqu'à W2.

    Si grammar est vide (client sans design_grammar/), retourne string vide.
    Le bloc est concentré (~500-1500 chars) pour ne pas saturer le mega-prompt
    déjà à ~30-50KB.
    """
    if not grammar:
        return ""

    block = "## DESIGN GRAMMAR V30 (couche prescriptive — RESPECTER, ne pas paraphraser)\n\n"

    # 1. Composition rules (asymétrie, density, rythme — règles structurelles)
    cr = grammar.get("composition_rules") or {}
    if cr:
        asym = cr.get("asymmetry") or {}
        density = cr.get("density") or {}
        rhythm = cr.get("rhythm") or {}
        ns = cr.get("negative_space") or {}
        do_not_cr = cr.get("do_not") or []
        block += "### Composition (règles structurelles)\n"
        if asym.get("rule"):
            block += f"  - asymétrie: {asym['rule']}\n"
        if density.get("max_elements_per_section_above_fold"):
            block += f"  - densité max above-fold: {density['max_elements_per_section_above_fold']} éléments / section\n"
        if rhythm.get("alternate_bg"):
            block += f"  - alternance bg sections: {rhythm['alternate_bg']}\n"
        if ns.get("rule"):
            block += f"  - négative space: {ns['rule']}\n"
        if do_not_cr:
            block += "  - DO NOT (composition):\n"
            for item in do_not_cr[:5]:
                block += f"      • {item}\n"
        block += "\n"

    # 2. Anti-patterns globaux (les plus opérationnels — ce qui sent le LLM)
    bfp = grammar.get("brand_forbidden_patterns") or {}
    global_ai = bfp.get("global_anti_ai_patterns") or []
    if global_ai:
        block += "### ANTI-PATTERNS AI/SLOP (interdits absolus pour cette marque)\n"
        for pattern in global_ai[:10]:
            block += f"  - {pattern}\n"
        block += "\n"

    # 3. Quality gates (seuils chiffrés à respecter — guard rails)
    qg = grammar.get("quality_gates") or {}
    thresholds = qg.get("thresholds") or {}
    if thresholds:
        block += "### Quality gates (seuils chiffrés — page rejetée si non respectés)\n"
        for key, label in [
            ("brand_fidelity_score_min", "fidélité brand min"),
            ("anti_ai_like_score_max", "AI-like score MAX"),
            ("wcag_contrast_min", "WCAG contrast min"),
            ("performance_lcp_max_s", "LCP max (s)"),
            ("accessibility_score_min", "a11y score min"),
        ]:
            if key in thresholds:
                block += f"  - {label}: {thresholds[key]}\n"
        block += "\n"

    # 4. Section grammar — anti-patterns par section (concis : juste hero pour ne pas surcharger)
    sg = grammar.get("section_grammar") or {}
    sg_sections = sg.get("sections") or {}
    hero = sg_sections.get("hero") or {}
    hero_avoid = hero.get("avoid") or []
    if hero_avoid:
        block += "### Hero section — patterns à éviter (cf section_grammar)\n"
        for item in hero_avoid[:5]:
            block += f"  - {item}\n"
        block += "\n"

    return block


def render_aura_block(aura: dict) -> str:
    """Format AURA tokens pour prompt LLM."""
    block = "## AURA COMPUTED TOKENS (V16) — utiliser tels quels en CSS\n\n"
    p = aura.get("palette") or {}
    block += f"### Palette (mathématiquement dérivée du brand DNA)\n"
    for k, v in p.items():
        if k.endswith("_rgb") or k == "is_dark_mode":
            continue
        block += f"  --color-{k.replace('_', '-')}: {v};\n"
    t = aura.get("typography") or {}
    block += f"\n### Typography\n"
    block += f"  --ff-display: '{t.get('display')}';\n"
    block += f"  --ff-body: '{t.get('body')}';\n"
    block += f"  --ff-accent: '{t.get('accent')}';\n"
    ts = aura.get("type_scale") or {}
    block += f"\n### Type scale (φ-derived)\n"
    for k, v in ts.items():
        block += f"  --fs-{k}: {v};\n"
    m = aura.get("motion") or {}
    block += f"\n### Motion (vector-derived)\n"
    block += f"  curve: {m.get('curve')}  ({m.get('name')})\n"
    block += f"  duration_base: {m.get('duration_base')}\n"
    block += f"  hover_scale: {m.get('hover_scale')}\n"
    d = aura.get("depth") or {}
    block += f"\n### Depth (shadows + radius vector-derived)\n"
    block += f"  glass enabled: {d.get('glass_enabled')} blur={d.get('glass_blur')} sat={d.get('glass_saturation')}\n"
    block += f"  noise_opacity: {d.get('noise_opacity')}\n"
    return block


def _load_ref_section(ref_name: str, section_pattern: str, max_chars: int = 3500) -> str:
    """Extract a section from a reference file by markdown heading pattern."""
    fp = ROOT / "skills" / "growth-site-generator" / "references" / f"{ref_name}.md"
    if not fp.exists():
        return ""
    text = fp.read_text()
    import re
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
                      design_grammar: dict | None = None,
                      creative_route: dict | None = None,
                      route_selection_meta: dict | None = None) -> str:
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
        import re as _re
        # Extract competitor H2 to BAN them (force originality)
        h2_matches = _re.findall(r'<h2[^>]*>([^<]+)</h2>', reference_competitor_html)
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


def call_sonnet(prompt: str, max_tokens: int = 16000) -> str:
    """Appelle Sonnet pour générer le HTML. Streaming si max_tokens > 16K."""
    import anthropic
    client = anthropic.Anthropic()
    print(f"  → Sonnet call (max_tokens={max_tokens}, prompt={len(prompt)} chars, streaming={max_tokens > 16000}) ...", flush=True)
    if max_tokens > 16000:
        # Streaming mandatory pour > 16K tokens
        text_chunks = []
        in_tokens = out_tokens = 0
        stop_reason = None
        with client.messages.stream(
            model=SONNET_MODEL,
            max_tokens=max_tokens,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for chunk in stream.text_stream:
                text_chunks.append(chunk)
            final = stream.get_final_message()
            in_tokens = final.usage.input_tokens
            out_tokens = final.usage.output_tokens
            stop_reason = final.stop_reason
        raw = "".join(text_chunks)
        print(f"  ← Sonnet streaming: in={in_tokens} out={out_tokens} stop_reason={stop_reason}", flush=True)
    else:
        msg = client.messages.create(
            model=SONNET_MODEL,
            max_tokens=max_tokens,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        print(f"  ← Sonnet response: in={msg.usage.input_tokens} out={msg.usage.output_tokens}"
              f" stop_reason={msg.stop_reason}", flush=True)
    # Strip markdown fences if any
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("html\n"): text = text[5:]
        if text.endswith("```"): text = text[:-3]
        text = text.strip()
    return text


def build_repair_prompt(current_html: str, client: str,
                         multi_judge_result: dict,
                         brand_dna: dict, design_grammar: dict,
                         original_mega_prompt_summary: str = "") -> str:
    """V26.Z W3 : prompt de repair ciblé qui consomme les verdicts multi-judge.

    Stratégie : ne PAS régénérer from scratch — corriger SPÉCIFIQUEMENT les
    weaknesses identifiées par le humanlike + les ai_default_patterns détectés.
    Le mega-prompt initial est référencé via summary, pas copié intégralement
    (économie tokens + force le focus sur les corrections).
    """
    judges = multi_judge_result.get("judges") or {}
    humanlike = judges.get("humanlike") or {}
    arbitrage = judges.get("arbitrage") or {}
    agreement = multi_judge_result.get("agreement") or {}

    weaknesses = humanlike.get("humanlike_weaknesses") or []
    ai_patterns = humanlike.get("ai_default_patterns_detected") or []
    sig_nommable = humanlike.get("signature_nommable")
    humanlike_verdict = humanlike.get("verdict_paragraph", "")
    arbitrage_verdict = arbitrage.get("final_verdict_short", "")
    final_pct = multi_judge_result.get("final_score_pct", "?")

    weaknesses_md = "\n".join(f"  - {w}" for w in weaknesses) if weaknesses else "  (aucune)"
    ai_patterns_md = "\n".join(f"  - {p}" for p in ai_patterns) if ai_patterns else "  (aucun)"

    # Compact brand reminder
    bd_summary = ""
    vt = brand_dna.get("visual_tokens") or {}
    voice = brand_dna.get("voice_tokens") or {}
    colors = vt.get("colors") or {}
    palette = colors.get("palette_full") or []
    bd_summary = f"Palette obligatoire: {', '.join(c.get('hex','?') for c in palette[:4])}"
    if voice.get("tone"):
        bd_summary += f" | Tone: {', '.join(voice['tone'][:3])}"
    if voice.get("forbidden_words"):
        bd_summary += f" | Forbidden words: {', '.join(voice['forbidden_words'][:5])}"

    # Compact design_grammar reminder (anti-patterns + composition rule)
    dg_summary = ""
    if design_grammar:
        bfp = (design_grammar.get("brand_forbidden_patterns") or {})
        global_ai = bfp.get("global_anti_ai_patterns") or []
        cr = (design_grammar.get("composition_rules") or {})
        asym = (cr.get("asymmetry") or {}).get("rule", "")
        if global_ai:
            dg_summary += "Anti-patterns brand interdits:\n" + "\n".join(f"  - {p}" for p in global_ai[:8])
        if asym:
            dg_summary += f"\n  - Composition: {asym}"

    return f"""Tu es directeur artistique senior + dev front senior. La LP que tu as générée pour {client.upper()} a été auditée par un multi-judge 3-way. **Score final : {final_pct}%** (en dessous du seuil de qualité).

Le défenseur (audit mécanique) donnait ~95%, mais le directeur créatif senior (humanlike, grille humaine 8 dimensions) a donné {agreement.get('judges_pct', {}).get('humanlike', {}).get('pct', '?')}% en pointant des défauts structurels. L'arbitre a tranché en sa faveur.

**Tu ne régénères PAS from scratch.** Tu corriges SPÉCIFIQUEMENT les défauts identifiés. Le code existant a des forces — garde-les.

## VERDICT DU DA SENIOR (humanlike)
{humanlike_verdict}

## VERDICT FINAL ARBITRE
{arbitrage_verdict}

## SIGNATURE VISUELLE NOMMABLE
{f'Actuelle: "{sig_nommable}"' if sig_nommable else '⚠️ AUCUNE — DOIT être créée. Une signature nommable en 3-5 mots ("Editorial Press SaaS", "Brutalist Tech Warm") doit émerger de cette LP. Pas un kitchen-sink de techniques.'}

## FAIBLESSES À CORRIGER (priorité haute)
{weaknesses_md}

## AI-DEFAULT PATTERNS À ÉLIMINER (interdits absolus dans la version repair)
{ai_patterns_md}

## RAPPELS BRAND (à ne pas violer)
{bd_summary}

## DESIGN GRAMMAR (couche prescriptive — RESPECTER)
{dg_summary}

## HTML ACTUEL À CORRIGER
```html
{current_html[:55000] if len(current_html) > 55000 else current_html}
```

## TON OUTPUT

Régénère le HTML COMPLET en appliquant les corrections ci-dessus. Tu peux :
- Modifier la composition globale (ex: changer asymétrie hero, repenser hiérarchie)
- Remplacer des patterns AI-default par des éléments distinctifs
- Resserrer la voix pour qu'elle soit reconnaissable comme {client.upper()}
- Ajouter une signature visuelle nommable cohérente (UN parti-pris, pas un empilement)
- Activer les principes Cialdini manquants si pointé en weakness
- Éliminer les patterns AI listés ci-dessus

Tu DOIS garder les forces du HTML actuel (les éléments concrets, les chiffres, la structure narrative qui fonctionne) — mais corriger ce que le DA senior a pointé.

Le HTML final doit être auto-contenu, mobile-first, accessible. Pas de markdown, juste le HTML pur.
"""


def run_repair_loop(initial_html: str, args, brand_dna: dict, design_grammar: dict,
                     output_path: pathlib.Path) -> tuple[str, list[dict]]:
    """V26.Z W3 : boucle automatique génération → multi_judge → repair si <threshold.

    Returns:
      (final_html, iterations_log)
      iterations_log = [{iter, score_pct, source, html_size, tokens}, ...]
    """
    # Lazy import to avoid circular dependency at module level
    sys.path.insert(0, str(SCRIPTS))
    from gsg_multi_judge import run_multi_judge  # noqa: E402

    iterations_log = []
    current_html = initial_html

    for it in range(args.max_repairs + 1):
        # Save current iteration HTML to disk for multi_judge to read
        iter_fp = output_path.with_name(output_path.stem + (f".iter{it}" if it > 0 else "") + output_path.suffix)
        iter_fp.parent.mkdir(parents=True, exist_ok=True)
        iter_fp.write_text(current_html)

        print(f"\n══ Repair loop iteration {it} ({iter_fp.name}) ══")

        # Run multi-judge
        mj_result = run_multi_judge(
            iter_fp, args.client,
            threshold=0.7,  # spread threshold for arbitrage trigger (independent of repair threshold)
            verbose=True,
        )
        score_pct = mj_result.get("final_score_pct", 0.0)
        iterations_log.append({
            "iter": it,
            "html_path": str(iter_fp.relative_to(ROOT)) if iter_fp.is_relative_to(ROOT) else str(iter_fp),
            "score_pct": score_pct,
            "source": mj_result.get("final_score_source", "?"),
            "html_size": len(current_html),
            "tokens": mj_result.get("tokens_total", 0),
        })

        # Save multi-judge result for this iteration
        mj_fp = ROOT / "data" / f"_audit_{args.client}_multi_iter{it}.json"
        mj_fp.write_text(json.dumps(mj_result, ensure_ascii=False, indent=2))

        if score_pct >= args.repair_threshold:
            print(f"\n✓ Score {score_pct}% ≥ threshold {args.repair_threshold}% → repair loop done at iter {it}")
            break

        if it >= args.max_repairs:
            print(f"\n⚠️  Max repairs ({args.max_repairs}) atteint — score final {score_pct}% < threshold {args.repair_threshold}%")
            break

        print(f"\n→ Score {score_pct}% < threshold {args.repair_threshold}% — repair iteration {it+1}/{args.max_repairs}")
        repair_prompt = build_repair_prompt(
            current_html=current_html,
            client=args.client,
            multi_judge_result=mj_result,
            brand_dna=brand_dna,
            design_grammar=design_grammar,
        )
        # Save repair prompt for debug
        debug_fp = ROOT / "data" / f"_gsg_repair_prompt_{args.client}_iter{it+1}.md"
        debug_fp.write_text(repair_prompt)
        print(f"  → repair prompt saved : {debug_fp.relative_to(ROOT)} ({len(repair_prompt)} chars)")

        current_html = call_sonnet(repair_prompt, max_tokens=args.max_tokens)
        print(f"✓ Iter {it+1} HTML regenerated ({len(current_html)} chars)")
        # V26.Z P0 : post-process auto également sur chaque iteration repair
        current_html, _ = auto_fix_runtime(current_html, label=f"iter{it+1}")

    return current_html, iterations_log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-legacy-lab", action="store_true",
                    help="Required acknowledgement: this V26.Z mega-prompt script is frozen legacy lab. Use moteur_gsg/orchestrator.py for canonical GSG.")
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", default="listicle")
    ap.add_argument("--energy", type=float, default=4.0)
    ap.add_argument("--tonality", type=float, default=3.0)
    ap.add_argument("--business", default="saas")
    ap.add_argument("--registre", default="editorial")
    ap.add_argument("--target-url", default="")
    ap.add_argument("--context-file", help="Path to .md/.txt with business audit context")
    ap.add_argument("--copy-hints-file", help="Path to .md with copy hints (10 raisons brief, etc.)")
    ap.add_argument("--reference-html", help="Path to HTML reference (e.g. concurrent version) à dépasser")
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-tokens", type=int, default=16000)
    # V26.Z W3 : auto-repair flags (opt-in, default off pour rétrocompat)
    ap.add_argument("--auto-repair", action="store_true",
                    help="V26.Z W3 : si activé, lance multi_judge après génération et "
                         "re-génère jusqu'à --repair-threshold ou --max-repairs.")
    ap.add_argument("--repair-threshold", type=float, default=70.0,
                    help="Score pct multi-judge final en dessous duquel on déclenche un repair (default 70)")
    ap.add_argument("--max-repairs", type=int, default=2,
                    help="Nombre max d'itérations de repair (default 2 → 3 calls Sonnet max au pire)")
    # V26.Z E2 : Creative Director multi-routes (opt-in, force une thèse visuelle nommable)
    ap.add_argument("--creative-mode", choices=["off", "auto", "safe", "premium", "bold", "custom"],
                    default="off",
                    help="V26.Z E2 : génère 3 routes nommées + sélectionne avant le mega-prompt. "
                         "off=skip (legacy V26.Z W2 sans creative director). "
                         "auto=Sonnet arbitre. safe/premium/bold=Mathis choisit explicitement. "
                         "custom=charge route depuis --custom-route-file.")
    ap.add_argument("--custom-route-file",
                    help="Path JSON pour route custom (mode=custom uniquement)")
    # V26.Z P1 : Sequential pipeline (4 stages chaînés vs mega-prompt one-shot)
    ap.add_argument("--sequential", action="store_true",
                    help="V26.Z P1 : utilise le pipeline 4 stages (Strategy → Copy → "
                         "Composer → Polish) au lieu du mega-prompt one-shot. Chaque stage "
                         "produit un artefact validable. Coût similaire ~$0.30 mais plus "
                         "diciplinaire.")
    args = ap.parse_args()

    if not args.allow_legacy_lab:
        sys.exit(
            "❌ FROZEN LEGACY LAB: gsg_generate_lp.py is no longer a public GSG entrypoint.\n"
            "Use `moteur_gsg.orchestrator.generate_lp()` or `scripts/run_gsg_full_pipeline.py --generation-path minimal`.\n"
            "For forensic reproduction only, re-run with `--allow-legacy-lab`."
        )

    print(f"\n══ GSG Generate LP — {args.client} / {args.page_type} ══\n")
    brand_dna = load_brand_dna(args.client)
    print("✓ Brand DNA loaded")

    design_grammar = load_design_grammar(args.client)
    if design_grammar:
        print(f"✓ Design Grammar V30 loaded ({len(design_grammar)} prescriptive files: {', '.join(design_grammar.keys())})")
    else:
        print(f"⚠️  No design_grammar/ found for {args.client} — degraded mode (brand_dna only)")

    aura = compute_aura_tokens(args.client, args.energy, args.tonality, args.business, args.registre)
    print(f"✓ AURA computed (vector + palette + typo + motion)")

    golden = golden_bridge_prompt(aura["vector"], top=5)
    print(f"✓ Golden Design Bridge ({len(golden)} chars)")

    business_context = ""
    if args.context_file and pathlib.Path(args.context_file).exists():
        business_context = pathlib.Path(args.context_file).read_text()
    copy_hints = ""
    if args.copy_hints_file and pathlib.Path(args.copy_hints_file).exists():
        copy_hints = pathlib.Path(args.copy_hints_file).read_text()
    reference_html = ""
    if args.reference_html and pathlib.Path(args.reference_html).exists():
        reference_html = pathlib.Path(args.reference_html).read_text()
        print(f"✓ Reference HTML loaded ({len(reference_html)} chars) — Sonnet doit le surpasser")

    # V26.Z E2 : Creative Director — génère 3 routes nommées + sélectionne
    creative_route = None
    route_selection_meta = None
    if args.creative_mode != "off":
        if not _CREATIVE_DIRECTOR_AVAILABLE:
            print("⚠️  --creative-mode demandé mais creative_director.py introuvable — skipping")
        else:
            print(f"\n══ Creative Director (mode={args.creative_mode}) ══")
            if args.creative_mode == "custom":
                custom_path = pathlib.Path(args.custom_route_file) if args.custom_route_file else None
                if not custom_path or not custom_path.exists():
                    sys.exit(f"❌ --creative-mode custom requires --custom-route-file (got: {custom_path})")
                custom_route = json.loads(custom_path.read_text())
                creative_route = custom_route
                route_selection_meta = {
                    "mode": "custom", "confidence": 1.0,
                    "reason": f"Custom route loaded from {custom_path.name}",
                    "warning": None,
                }
                print(f"✓ Custom route loaded: {creative_route.get('name', '?')}")
            else:
                # Generate 3 routes (Safe + Premium + Bold)
                print("[1/2] Generate 3 routes...")
                routes_data = cd_generate_routes(
                    brand_dna, design_grammar, business_context,
                    args.page_type, args.client, args.target_url
                )
                routes_fp = ROOT / "data" / f"_routes_{args.client}.json"
                routes_fp.write_text(json.dumps(routes_data, ensure_ascii=False, indent=2))
                print(f"  ✓ 3 routes generated, saved to {routes_fp.relative_to(ROOT)}")
                for r in routes_data.get("routes", []):
                    print(f"    [{r.get('risk_level', '?'):8s}] {r.get('name', '?')}")

                # Select route (auto Sonnet, ou explicit safe/premium/bold)
                print(f"\n[2/2] Select route (mode={args.creative_mode})...")
                selection = cd_select_route(
                    routes_data, brand_dna, business_context,
                    mode=args.creative_mode,
                )
                creative_route = selection["route"]
                route_selection_meta = selection["selection_meta"]
                sel_fp = ROOT / "data" / f"_route_selected_{args.client}.json"
                sel_fp.write_text(json.dumps(selection, ensure_ascii=False, indent=2))
                print(f"  ✓ Selected: \"{creative_route.get('name')}\" (risk={creative_route.get('risk_level')})")
                print(f"    Confidence: {route_selection_meta.get('confidence')}")
                print(f"    Reason: {route_selection_meta.get('reason')[:200]}")
                if route_selection_meta.get("warning"):
                    print(f"    ⚠️  {route_selection_meta['warning']}")

    # V26.Z P1 — Sequential pipeline (option) vs mega-prompt one-shot (legacy)
    if args.sequential:
        try:
            from gsg_pipeline_sequential import run_sequential_pipeline
        except ImportError as e:
            sys.exit(f"❌ --sequential requires gsg_pipeline_sequential.py : {e}")
        print(f"\n══ Sequential pipeline (P1, 4 stages) ══")
        seq_result = run_sequential_pipeline(
            client=args.client, brand_dna=brand_dna, design_grammar=design_grammar,
            aura=aura, creative_route=creative_route,
            business_context=business_context, copy_hints=copy_hints,
            page_type=args.page_type, target_url=args.target_url or "",
            verbose=True,
        )
        html = seq_result["html_final"]
        # Save telemetry
        telem_fp = ROOT / "data" / f"_pipeline_{args.client}_telemetry.json"
        telem_fp.write_text(json.dumps(seq_result["telemetry"], ensure_ascii=False, indent=2))
        print(f"\n✓ Sequential pipeline complete : tokens_total={seq_result['telemetry']['tokens_total']}")
        print(f"  → telemetry saved : {telem_fp.relative_to(ROOT)}")
    else:
        # Mega-prompt one-shot (legacy)
        prompt = build_mega_prompt(
            client=args.client, brand_dna=brand_dna, aura=aura, golden_prompt=golden,
            page_type=args.page_type, business_context=business_context,
            copy_hints=copy_hints, target_url=args.target_url or "",
            reference_competitor_html=reference_html,
            design_grammar=design_grammar,
            creative_route=creative_route,
            route_selection_meta=route_selection_meta,
        )
        print(f"✓ Mega-prompt assembled ({len(prompt)} chars)")
        # Save prompt for debug
        debug_fp = ROOT / "data" / f"_gsg_prompt_{args.client}.md"
        debug_fp.write_text(prompt)
        print(f"  → debug prompt saved : {debug_fp.relative_to(ROOT)}")

        html = call_sonnet(prompt, max_tokens=args.max_tokens)

    print(f"✓ HTML generated ({len(html)} chars · {html.count(chr(10))+1} lines)")

    # V26.Z P0 : post-process auto rendering bugs (counter à 0, reveal-class, opacity 0)
    # → garantit un rendu visible peu importe ce que Sonnet a généré.
    html, fix_report = auto_fix_runtime(html, label="iter0")

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    # V26.Z W3 : si --auto-repair, on entre dans la boucle multi_judge → repair → ...
    if args.auto_repair:
        print(f"\n══ Auto-repair activé (threshold={args.repair_threshold}%, max_repairs={args.max_repairs}) ══")
        final_html, iter_log = run_repair_loop(html, args, brand_dna, design_grammar, out)
        out.write_text(final_html)
        # Save iterations log
        log_fp = ROOT / "data" / f"_gsg_iter_log_{args.client}.json"
        log_fp.write_text(json.dumps({
            "client": args.client,
            "page_type": args.page_type,
            "iterations": iter_log,
            "best_iter": max(range(len(iter_log)), key=lambda i: iter_log[i]["score_pct"]),
            "final_iter": len(iter_log) - 1,
            "threshold": args.repair_threshold,
        }, ensure_ascii=False, indent=2))
        print(f"\n══ Repair loop summary ══")
        for entry in iter_log:
            mark = "✓" if entry["score_pct"] >= args.repair_threshold else "✗"
            print(f"  {mark} iter {entry['iter']}: {entry['score_pct']}% ({entry['html_size']} chars, {entry['tokens']} tokens)")
        print(f"\n  Iter log saved: {log_fp.relative_to(ROOT)}")
    else:
        out.write_text(html)

    print(f"\n✓ Saved : {out}")
    print(f"  Open : open {out}")


if __name__ == "__main__":
    main()
