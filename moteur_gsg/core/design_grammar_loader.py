"""Design Grammar Loader V26.AA Sprint B — branche design_grammar V30 au Mode 1.

Trou architectural identifié 2026-05-04 : `skills/site-capture/scripts/design_grammar.py`
(V30) génère 7 fichiers prescriptifs/client mais Mode 1 V26.AA ne les consomme pas.

Ce module :
1. Charge `data/captures/<client>/design_grammar/` (7 fichiers)
2. Format un bloc texte court (≤2K chars) injectable dans prompt_assembly Mode 1
3. Expose les forbidden_patterns + section_grammar + tokens essentiels
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def has_design_grammar(client: str) -> bool:
    return (ROOT / "data" / "captures" / client / "design_grammar" / "tokens.json").exists()


def load_design_grammar(client: str) -> dict:
    """Charge les 7 fichiers design_grammar/ pour un client.

    Returns: dict avec keys tokens, components, sections, composition, forbidden, gates.
    Vide ({}) si design_grammar/ absent.
    """
    dgd = ROOT / "data" / "captures" / client / "design_grammar"
    if not dgd.exists():
        return {}

    def _load(name):
        fp = dgd / name
        if not fp.exists():
            return None
        try:
            return json.loads(fp.read_text())
        except Exception:
            return None

    return {
        "tokens": _load("tokens.json"),
        "components": _load("component_grammar.json"),
        "sections": _load("section_grammar.json"),
        "composition": _load("composition_rules.json"),
        "forbidden": _load("brand_forbidden_patterns.json"),
        "gates": _load("quality_gates.json"),
    }


def format_design_grammar_block(grammar: dict, max_chars: int = 2200) -> str:
    """Format design grammar en bloc texte court pour injection prompt Mode 1.

    Priorise (par ordre d'importance création) :
    1. Forbidden patterns (ce qu'il NE faut JAMAIS faire — anti-AI-slop)
    2. Composition rules (rythme, densité, asymétrie)
    3. Section hero rules (le plus critique CRO)
    4. Component grammar buttons + cards (CTA + sections)
    5. Tokens essentiels (radius, motion)
    """
    if not grammar or not any(grammar.values()):
        return ""

    parts = ["## DESIGN GRAMMAR (V30 prescriptif client — RÈGLES VISUELLES NON NÉGOCIABLES)"]

    # 1. Forbidden patterns (PRIORITÉ — anti-AI-slop)
    forbid = grammar.get("forbidden") or {}
    if forbid:
        patterns = forbid.get("patterns") or forbid.get("forbidden_patterns") or []
        if patterns:
            parts.append("\n### ⛔ INTERDIT (jamais utiliser)")
            for p in patterns[:8]:
                if isinstance(p, dict):
                    rule = p.get("rule") or p.get("pattern") or p.get("description")
                    reason = p.get("reason") or p.get("why")
                    if rule:
                        line = f"  - {str(rule)[:130]}"
                        if reason:
                            line += f" (why: {str(reason)[:80]})"
                        parts.append(line)
                else:
                    parts.append(f"  - {str(p)[:150]}")

    # 2. Composition rules
    comp = grammar.get("composition") or {}
    if comp:
        parts.append("\n### COMPOSITION")
        for key in ("grid", "density", "rhythm", "negative_space", "asymmetry"):
            v = comp.get(key)
            if v:
                if isinstance(v, dict):
                    summary = v.get("rule") or v.get("description") or json.dumps(v, ensure_ascii=False)[:100]
                else:
                    summary = str(v)[:100]
                parts.append(f"  - **{key}** : {summary}")

    # 3. Sections (hero priorité)
    sections = grammar.get("sections") or {}
    if isinstance(sections, dict):
        hero = sections.get("hero") or sections.get("byType", {}).get("hero")
        if hero:
            parts.append("\n### HERO RULES (le plus critique CRO)")
            if isinstance(hero, dict):
                for key in ("layout", "ratio", "must_have", "must_avoid"):
                    v = hero.get(key)
                    if v:
                        if isinstance(v, list):
                            parts.append(f"  - **{key}** : {', '.join(str(x)[:60] for x in v[:3])}")
                        else:
                            parts.append(f"  - **{key}** : {str(v)[:120]}")

    # 4. Component grammar buttons (CTAs)
    components = grammar.get("components") or {}
    btn = (components.get("buttons") or components.get("byType", {}).get("buttons")) if isinstance(components, dict) else None
    if btn and isinstance(btn, dict):
        parts.append("\n### BUTTONS / CTA")
        primary = btn.get("primary") or btn.get("primary_button")
        if isinstance(primary, dict):
            for key in ("style", "radius", "height", "padding", "font_size", "font_weight", "must_avoid"):
                v = primary.get(key)
                if v:
                    parts.append(f"  - **primary.{key}** : {str(v)[:80]}")

    # 5. Tokens essentiels (motion + radius)
    tokens = grammar.get("tokens") or {}
    if isinstance(tokens, dict):
        motion = tokens.get("motion") or {}
        shape = tokens.get("shape") or {}
        essentials = []
        if motion.get("style"): essentials.append(f"motion={motion['style']}")
        if shape.get("border_radius"): essentials.append(f"radius={shape['border_radius']}")
        if essentials:
            parts.append(f"\n### TOKENS : {' | '.join(essentials)}")

    block = "\n".join(parts)
    if len(block) > max_chars:
        block = block[:max_chars - 30] + "\n[... tronqué design_grammar]"
    return block


if __name__ == "__main__":
    import sys
    client = sys.argv[1] if len(sys.argv) > 1 else "weglot"
    g = load_design_grammar(client)
    if not g or not any(g.values()):
        print(f"❌ design_grammar/ absent pour {client}")
        sys.exit(1)
    block = format_design_grammar_block(g)
    print(f"\n══ Design Grammar block — {client} ══")
    print(f"Block size: {len(block)} chars\n")
    print(block)
