"""Mega-prompt block renderers for brand DNA + design grammar + AURA.

Four ``render_*_block(...)`` helpers produce ready-to-concatenate
markdown sections used by ``mega_prompt_builder.build_mega_prompt``:

  * ``render_brand_dna_diff_block`` — V26.Z E1 prescriptive layer
    (preserve / amplify / fix / forbid quadrants).
  * ``render_brand_block``          — visual + voice + image direction
    + asset rules from brand_dna V29 Phase 1+2.
  * ``render_design_grammar_block`` — V26.Z W2 design_grammar V30
    (composition rules + anti-patterns + quality gates + section grammar).
  * ``render_aura_block``           — V16 AURA computed tokens (palette,
    typography, type scale, motion, depth).

Pure formatting — no I/O, no subprocess. Split from
``gsg_generate_lp.py`` (issue #8).
"""
from __future__ import annotations


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
    block += "### Palette (mathématiquement dérivée du brand DNA)\n"
    for k, v in p.items():
        if k.endswith("_rgb") or k == "is_dark_mode":
            continue
        block += f"  --color-{k.replace('_', '-')}: {v};\n"
    t = aura.get("typography") or {}
    block += "\n### Typography\n"
    block += f"  --ff-display: '{t.get('display')}';\n"
    block += f"  --ff-body: '{t.get('body')}';\n"
    block += f"  --ff-accent: '{t.get('accent')}';\n"
    ts = aura.get("type_scale") or {}
    block += "\n### Type scale (φ-derived)\n"
    for k, v in ts.items():
        block += f"  --fs-{k}: {v};\n"
    m = aura.get("motion") or {}
    block += "\n### Motion (vector-derived)\n"
    block += f"  curve: {m.get('curve')}  ({m.get('name')})\n"
    block += f"  duration_base: {m.get('duration_base')}\n"
    block += f"  hover_scale: {m.get('hover_scale')}\n"
    d = aura.get("depth") or {}
    block += "\n### Depth (shadows + radius vector-derived)\n"
    block += f"  glass enabled: {d.get('glass_enabled')} blur={d.get('glass_blur')} sat={d.get('glass_saturation')}\n"
    block += f"  noise_opacity: {d.get('noise_opacity')}\n"
    return block


__all__ = [
    "render_brand_dna_diff_block",
    "render_brand_block",
    "render_design_grammar_block",
    "render_aura_block",
]
