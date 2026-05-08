"""V30 — GSG Design Grammar : transformation Brand DNA → grammaire de génération.

Réponse à la roadmap ChatGPT §11 (V31 GSG Design Grammar) + §7.3 :
"Le Design Grammar Engine est la brique qui évite le rendu IA-like.
Il transforme le Brand DNA en contraintes de génération. Il ne dit pas
seulement 'utilise cette couleur'. Il dit : 'les boutons principaux
sont pleins, radius 999, hauteur 52, texte 15/600, CTA jamais en
gradient, hover translateY(-1), section hero utilise image 45% right,
cards ont radius 20, pas de glassmorphism, pas de purple gradient.'"

Inputs : data/captures/<client>/brand_dna.json (V29 full)
Outputs : data/captures/<client>/design_grammar/
  - tokens.css                    : variables CSS for radius/colors/typo/spacing/shadows/motion
  - tokens.json                   : same as JSON (machine-readable)
  - component_grammar.json        : rules per component (buttons, cards, nav, forms, testimonials)
  - section_grammar.json          : rules per section (hero, proof, benefits, pricing, FAQ, CTA)
  - composition_rules.json        : grid, asymmetry, negative_space, density, rhythm
  - brand_forbidden_patterns.json : ce que la marque ne doit JAMAIS produire
  - quality_gates.json            : seuils min (brand_fidelity, CRO, UX, a11y, visual_taste)

Pas d'API call (transformation déterministe depuis brand_dna).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"


# ────────────────────────────────────────────────────────────────
# Tokens.css generation
# ────────────────────────────────────────────────────────────────

def build_tokens_css(brand_dna: dict) -> str:
    """Generate CSS variables from brand_dna visual_tokens."""
    vt = brand_dna.get("visual_tokens", {}) or {}
    colors = vt.get("colors", {}) or {}
    typo = vt.get("typography", {}) or {}
    spacing = vt.get("spacing", {}) or {}
    shape = vt.get("shape", {}) or {}
    depth = vt.get("depth", {}) or {}
    motion = vt.get("motion", {}) or {}

    primary_hex = (colors.get("primary") or {}).get("hex") or "#000000"
    secondary = colors.get("secondary") or []
    sec_1 = secondary[0]["hex"] if len(secondary) > 0 else "#888888"
    sec_2 = secondary[1]["hex"] if len(secondary) > 1 else "#cccccc"
    neutrals = colors.get("neutrals") or ["#ffffff", "#f5f5f5", "#1a1a1a"]

    # Typography
    body = typo.get("body") or {}
    h1 = typo.get("h1") or {}
    body_size = body.get("size_px") or 16
    h1_size = (h1.get("size_px") or body_size * 2.5)
    body_family = body.get("family") or "system-ui, sans-serif"
    h1_family = (h1.get("family") or body_family)

    # Shape
    radius_dom = shape.get("radius_dominant") or 8
    edge = shape.get("edge_language") or "soft"

    # Depth
    shadow_style = depth.get("shadow_style") or "soft"

    css = f"""/* GrowthCRO V30 — Design Grammar Tokens for {brand_dna.get('client', 'unknown')} */
/* Generated from brand_dna.json. DO NOT edit manually. */

:root {{
  /* ── Colors ── */
  --color-primary: {primary_hex};
  --color-primary-hover: color-mix(in srgb, {primary_hex} 88%, black);
  --color-secondary-1: {sec_1};
  --color-secondary-2: {sec_2};
  --color-bg: {neutrals[0] if len(neutrals) > 0 else "#ffffff"};
  --color-surface: {neutrals[1] if len(neutrals) > 1 else "#f5f5f5"};
  --color-text: {neutrals[2] if len(neutrals) > 2 else "#1a1a1a"};
  --color-text-muted: color-mix(in srgb, var(--color-text) 65%, transparent);
  --color-border: color-mix(in srgb, var(--color-text) 12%, transparent);

  /* ── Typography ── */
  --font-heading: {h1_family};
  --font-body: {body_family};
  --fs-h1: {int(h1_size)}px;
  --fs-h2: {int(h1_size * 0.7)}px;
  --fs-h3: {int(h1_size * 0.5)}px;
  --fs-body: {body_size}px;
  --fs-small: {max(12, body_size - 2)}px;
  --lh-heading: 1.1;
  --lh-body: 1.55;
  --fw-body: {body.get('weight') or '400'};
  --fw-heading: {h1.get('weight') or '700'};

  /* ── Spacing ── */
  --container-max: {spacing.get('container_max') or 1200}px;
  --gap-xs: 8px;
  --gap-sm: 16px;
  --gap-md: 24px;
  --gap-lg: 48px;
  --gap-xl: 96px;
  --section-py: 96px;

  /* ── Shape ── */
  --radius-sharp: 0;
  --radius-subtle: 4px;
  --radius-soft: {radius_dom}px;
  --radius-round: 999px;
  --radius-default: {radius_dom}px;
  --edge-language: "{edge}";

  /* ── Depth (shadows) ── */
  --shadow-none: none;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.08);
  --shadow-default: var(--shadow-{shadow_style if shadow_style in ('none', 'sm', 'md', 'lg') else 'md'});

  /* ── Motion ── */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
}}

/* Dark mode override (optional, used if brand_dna voice indicates premium dark) */
[data-theme="dark"] {{
  --color-bg: {neutrals[2] if len(neutrals) > 2 else "#0a0a0a"};
  --color-surface: color-mix(in srgb, {neutrals[2] if len(neutrals) > 2 else "#0a0a0a"} 92%, white);
  --color-text: {neutrals[0] if len(neutrals) > 0 else "#ffffff"};
}}
"""
    return css


# ────────────────────────────────────────────────────────────────
# Component grammar
# ────────────────────────────────────────────────────────────────

def build_component_grammar(brand_dna: dict) -> dict:
    """Component rules : buttons, cards, nav, forms, testimonials."""
    vt = brand_dna.get("visual_tokens", {}) or {}
    shape = vt.get("shape", {}) or {}
    edge = shape.get("edge_language") or "soft"
    radius_dom = shape.get("radius_dominant") or 8

    # Map edge_language → button shape
    button_radius = {
        "sharp": "var(--radius-sharp)",
        "subtle": "var(--radius-subtle)",
        "soft": "var(--radius-soft)",
        "pill": "var(--radius-round)",
    }.get(edge, "var(--radius-soft)")

    return {
        "version": "v30.1.0",
        "client": brand_dna.get("client"),
        "buttons": {
            "primary": {
                "background": "var(--color-primary)",
                "color": "var(--color-bg)",
                "border": "none",
                "border_radius": button_radius,
                "padding": "14px 28px",
                "font_size": "var(--fs-body)",
                "font_weight": "600",
                "text_transform": "none",
                "transition": "var(--transition-base)",
                "hover": "transform: translateY(-1px); background: var(--color-primary-hover);",
                "do_not": ["gradient backgrounds", "drop shadows on hover", "uppercase only"],
            },
            "secondary": {
                "background": "transparent",
                "color": "var(--color-text)",
                "border": "1px solid var(--color-border)",
                "border_radius": button_radius,
                "padding": "13px 27px",
                "do_not": ["faux-3D effects", "gradient borders"],
            },
            "ghost": {
                "background": "transparent",
                "color": "var(--color-primary)",
                "border": "none",
                "padding": "8px 12px",
                "do_not": ["icon-only without label"],
            },
        },
        "cards": {
            "default": {
                "background": "var(--color-surface)",
                "border": "1px solid var(--color-border)",
                "border_radius": "var(--radius-default)",
                "padding": "var(--gap-md)",
                "shadow": "var(--shadow-default)",
                "do_not": ["glassmorphism", "neon glow", "tilt 3D"],
            },
            "product": {
                "background": "var(--color-bg)",
                "border": "1px solid var(--color-border)",
                "border_radius": "var(--radius-default)",
                "image_aspect_ratio": "1/1 or 4/5",
                "image_position": "top",
                "do_not": ["overlay text on image", "rotated images"],
            },
        },
        "nav": {
            "header": {
                "padding": "var(--gap-sm) var(--gap-md)",
                "border_bottom": "1px solid var(--color-border)",
                "logo_height": "32px",
                "items": "horizontal flex, var(--gap-md) gap",
                "sticky": True,
                "do_not": ["transparent over hero (à moins que hero ait dark overlay)", "mega-menus on B2C"],
            },
        },
        "forms": {
            "input": {
                "border": "1px solid var(--color-border)",
                "border_radius": "var(--radius-subtle)",
                "padding": "12px 16px",
                "font_size": "var(--fs-body)",
                "min_height": "44px",
                "focus": "border-color: var(--color-primary); outline: 2px solid color-mix(in srgb, var(--color-primary) 20%, transparent);",
                "do_not": ["floating labels avec animations complexes", "border-bottom only", "placeholder as label"],
            },
            "field_count_max": 5,  # Baymard rule
        },
        "testimonials": {
            "card_style": "minimal_card",
            "include_photo": True,
            "include_role": True,
            "do_not": ["stock photos", "fake names", "5-star ratings without reviewer name"],
        },
    }


# ────────────────────────────────────────────────────────────────
# Section grammar
# ────────────────────────────────────────────────────────────────

def build_section_grammar(brand_dna: dict) -> dict:
    """Rules per landing-page section type."""
    return {
        "version": "v30.1.0",
        "client": brand_dna.get("client"),
        "hero": {
            "structure": "h1 → subtitle → primary_cta → social_proof_inline",
            "h1_max_words": 12,
            "h1_pattern": "<benefit> <pour qui> <différenciateur>",
            "subtitle_max_chars": 160,
            "primary_cta_position": "above_fold",
            "social_proof_required": True,
            "image_to_text_ratio": "60_40 or 50_50",
            "do_not": ["stock smiley faces", "purple gradient bg", "centered everything", "AI-like badges"],
        },
        "social_proof": {
            "position": "after_hero",
            "types_allowed": ["client_logos", "review_card", "press_quote", "stat_number"],
            "min_proofs": 3,
            "do_not": ["fake reviews", "generic '5 stars' badges", "stock business photos"],
        },
        "benefits": {
            "structure": "3-4 benefits in grid, icon + h3 + body",
            "icons_style": "outline_consistent",  # follows brand_dna asset_rules
            "max_benefits": 4,
            "do_not": ["lorem ipsum-tier copy", "icons stock", "glow effects"],
        },
        "pricing": {
            "show_price": True,  # except luxury/enterprise (override via brand_dna market_position)
            "tiers_max": 3,
            "highlight_recommended": True,
            "include_money_back_guarantee": True,
            "do_not": ["hidden pricing on B2C", "price comparison without source", "fake countdown"],
        },
        "faq": {
            "structure": "accordion, 5-10 items",
            "include_schema_org": True,  # FAQPage JSON-LD (V24.4 GEO)
            "do_not": ["promotional Q&A", "made-up authority"],
        },
        "final_cta": {
            "structure": "h2 → reassurance → primary_cta → secondary_link",
            "background": "var(--color-primary) ou var(--color-surface)",
            "do_not": ["urgency artificielle ('Plus que 3 places')", "popups exit-intent intrusifs"],
        },
    }


# ────────────────────────────────────────────────────────────────
# Composition rules
# ────────────────────────────────────────────────────────────────

def build_composition_rules(brand_dna: dict) -> dict:
    img_dir = brand_dna.get("image_direction", {}) or {}
    composition = img_dir.get("composition", "asymmetric")
    return {
        "version": "v30.1.0",
        "client": brand_dna.get("client"),
        "grid": {
            "max_columns": 12,
            "gap_default": "var(--gap-md)",
            "container_max": "var(--container-max)",
        },
        "asymmetry": {
            "preferred": composition == "asymmetric",
            "rule": "Hero : image 45% right + text 55% left (or inverse). Avoid 50/50 centered.",
        },
        "negative_space": {
            "min_section_padding_y": "var(--gap-xl)",
            "rule": "Min 96px padding top/bottom per section. Min 24px gap between siblings.",
        },
        "density": {
            "preferred": "balanced",  # could derive from brand_dna voice or asset_rules
            "max_elements_per_section_above_fold": 8,
        },
        "rhythm": {
            "alternate_bg": True,  # alternate var(--color-bg) and var(--color-surface)
            "section_height_min": "60vh for hero, auto for others",
        },
        "do_not": [
            "all sections same bg color (loss of rhythm)",
            "all sections center-aligned (boring)",
            "more than 2 columns on mobile",
            "horizontal scroll on body",
        ],
    }


# ────────────────────────────────────────────────────────────────
# Brand forbidden patterns
# ────────────────────────────────────────────────────────────────

def build_forbidden_patterns(brand_dna: dict) -> dict:
    """Aggregate do_not rules from voice_tokens + image_direction + asset_rules."""
    voice = brand_dna.get("voice_tokens", {}) or {}
    img_dir = brand_dna.get("image_direction", {}) or {}
    asset = brand_dna.get("asset_rules", {}) or {}

    forbidden = {
        "version": "v30.1.0",
        "client": brand_dna.get("client"),
        "voice": {
            "forbidden_words": voice.get("forbidden_words") or [],
        },
        "visual": {
            "forbidden_styles": img_dir.get("do_not_use") or [],
            "forbidden_techniques": (asset.get("do_not") if isinstance(asset, dict) else None) or [],
        },
        "global_anti_ai_patterns": [
            "generic SaaS hero with mockup centered",
            "purple-pink gradients",
            "icon library outlined identical pour toutes les sections",
            "stock smiling diverse team photo",
            "lorem-feeling testimonials",
            "5-star ratings without source",
            "glassmorphism partout",
            "hover translateY(-2) + scale(1.05) sur tous les cards",
            "section avec gradient mesh psychedelic",
            "CTA 'Get Started Free' identique pour toute page",
        ],
    }
    return forbidden


# ────────────────────────────────────────────────────────────────
# Quality gates
# ────────────────────────────────────────────────────────────────

def build_quality_gates(brand_dna: dict) -> dict:
    """Min thresholds for client-ready output (cf ChatGPT §13.3 + §13.4)."""
    return {
        "version": "v30.1.0",
        "client": brand_dna.get("client"),
        "thresholds": {
            "brand_fidelity_score_min": 0.88,
            "anti_ai_like_score_max": 0.20,  # lower = less AI-like
            "cro_critic_score_min": 0.80,
            "wcag_contrast_min": 4.5,
            "performance_lcp_max_s": 2.5,
            "performance_cls_max": 0.10,
            "mobile_qa_pass_required": True,
            "page_load_time_max_s": 3.0,
            "accessibility_score_min": 0.85,
        },
        "blocking_critics": [
            "brand_fidelity",
            "anti_ai_like",
            "cro",
            "a11y",
            "performance",
        ],
        "informational_critics": [
            "visual_taste",
            "evidence_critic",
            "implementation_critic",
        ],
    }


# ────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────

def generate_design_grammar(client: str) -> dict:
    """Read brand_dna.json, write all grammar files. Return manifest."""
    client_dir = CAPTURES / client
    bdna_path = client_dir / "brand_dna.json"
    if not bdna_path.exists():
        return {"error": "brand_dna.json missing — run brand_dna_extractor.py first"}

    brand_dna = json.loads(bdna_path.read_text())
    out_dir = client_dir / "design_grammar"
    out_dir.mkdir(exist_ok=True)

    # Generate
    css = build_tokens_css(brand_dna)
    tokens_json = brand_dna.get("visual_tokens", {})
    component = build_component_grammar(brand_dna)
    section = build_section_grammar(brand_dna)
    composition = build_composition_rules(brand_dna)
    forbidden = build_forbidden_patterns(brand_dna)
    gates = build_quality_gates(brand_dna)

    files = {
        "tokens.css": css,
        "tokens.json": json.dumps(tokens_json, ensure_ascii=False, indent=2),
        "component_grammar.json": json.dumps(component, ensure_ascii=False, indent=2),
        "section_grammar.json": json.dumps(section, ensure_ascii=False, indent=2),
        "composition_rules.json": json.dumps(composition, ensure_ascii=False, indent=2),
        "brand_forbidden_patterns.json": json.dumps(forbidden, ensure_ascii=False, indent=2),
        "quality_gates.json": json.dumps(gates, ensure_ascii=False, indent=2),
    }

    written = []
    for fname, content in files.items():
        f = out_dir / fname
        tmp = f.with_suffix(f.suffix + ".tmp")
        tmp.write_text(content)
        tmp.replace(f)
        written.append(fname)

    return {
        "client": client,
        "design_grammar_dir": str(out_dir),
        "files_written": written,
        "n_files": len(written),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        n = 0
        for cd in sorted(CAPTURES.iterdir()):
            if not cd.is_dir() or cd.name.startswith(("_", ".")):
                continue
            if not (cd / "brand_dna.json").exists():
                continue
            res = generate_design_grammar(cd.name)
            if "error" not in res:
                n += 1
                sys.stderr.write(".")
                sys.stderr.flush()
        sys.stderr.write("\n")
        print(f"✓ Generated design_grammar/ for {n} clients")
    elif args.client:
        res = generate_design_grammar(args.client)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("❌ --client or --all required", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
