"""Brand Intelligence — V26.AA Sprint 3.

Wrapper qui :
  1. Charge `data/captures/<client>/brand_dna.json` (V29 produit par brand_dna_extractor)
  2. Charge `brand_dna.diff` (V26.Z E1 brand_dna_diff_extractor — quadrant preserve/amplify/fix/forbid)
  3. Format en bloc texte court (~2-3K chars max) injectable dans prompt

Le brand_dna est l'input principal du Mode 1 COMPLETE (Mathis : "URL→extraction auto, pas brief 8 questions").

Structure brand_dna V29 (vérifiée sur weglot) :
  visual_tokens: colors, typography, spacing, shape, depth, motion
  voice_tokens : tone, forbidden_words, preferred_cta_verbs, sentence_rhythm, voice_signature_phrase
  asset_rules  : règles d'usage des assets
  method       : classification persona / archetype / niveau Schwartz
  image_direction: art direction images (textures, lumière, etc.)
  diff         : preserve / amplify / fix / forbid (E1, prescriptif)
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_brand_dna(client: str) -> dict:
    """Charge brand_dna.json depuis data/captures/<client>/.

    Returns: brand_dna dict, OU {} si absent (à signaler à l'appelant).
    """
    fp = ROOT / "data" / "captures" / client / "brand_dna.json"
    if not fp.exists():
        return {}
    return json.loads(fp.read_text())


def has_brand_dna(client: str) -> bool:
    return (ROOT / "data" / "captures" / client / "brand_dna.json").exists()


def _extract_diff(brand_dna: dict) -> dict:
    """Brand DNA V29 packs le diff (E1) inline dans la clé 'diff'. Sépare proprement."""
    return brand_dna.get("diff", {}) if isinstance(brand_dna.get("diff"), dict) else {}


def format_brand_block(brand_dna: dict, max_chars: int = 3500) -> str:
    """Format le brand_dna en bloc texte court pour injection dans prompt.

    Priorise les leviers les plus actionnables :
      - voice_signature_phrase + tone + forbidden_words + preferred_cta_verbs
      - palette couleurs (3-5 hex)
      - typography family + weights
      - diff prescriptif : preserve/amplify/fix/forbid (le plus exploitable côté création)

    Si max_chars dépassé : tronque les sections moins critiques (image_direction, motion).
    """
    if not brand_dna:
        return "## BRAND DNA\n(Brand DNA non disponible — invente une signature visuelle cohérente avec le brief.)\n"

    visual = brand_dna.get("visual_tokens", {}) or {}
    voice = brand_dna.get("voice_tokens", {}) or {}
    diff = _extract_diff(brand_dna)
    method = brand_dna.get("method", {}) or {}

    parts: list[str] = []
    parts.append(f"## BRAND DNA — {brand_dna.get('client', '?')}")
    if brand_dna.get("home_url"):
        parts.append(f"Source : {brand_dna['home_url']}")

    # ── Voice ──────────────────────────────────────────────────
    parts.append("\n### VOIX (à respecter strictement)")
    if voice.get("voice_signature_phrase"):
        parts.append(f"- Signature : « {voice['voice_signature_phrase']} »")
    if voice.get("tone"):
        tones = voice["tone"] if isinstance(voice["tone"], list) else [voice["tone"]]
        parts.append(f"- Ton : {', '.join(tones)}")
    if voice.get("sentence_rhythm"):
        parts.append(f"- Rythme phrase : {voice['sentence_rhythm']}")
    if voice.get("preferred_cta_verbs"):
        verbs = voice["preferred_cta_verbs"][:6]
        parts.append(f"- Verbes CTA préférés : {', '.join(verbs)}")
    if voice.get("forbidden_words"):
        forbid = voice["forbidden_words"][:8]
        parts.append(f"- Mots INTERDITS : {', '.join(forbid)}")

    # ── Visual tokens ──────────────────────────────────────────
    parts.append("\n### VISUEL")
    colors = visual.get("colors", {}) or {}
    color_lines: list[str] = []
    if isinstance(colors, dict):
        # primary peut être {hex, coverage_pct, usage_hint} OU directement un hex string
        primary = colors.get("primary")
        if isinstance(primary, dict):
            hint = primary.get("usage_hint", "")
            color_lines.append(f"primary={primary.get('hex','?')} ({hint})")
        elif primary:
            color_lines.append(f"primary={primary}")
        # secondary peut être list[dict] ou single value
        secondary = colors.get("secondary")
        if isinstance(secondary, list) and secondary:
            for item in secondary[:3]:
                if isinstance(item, dict):
                    color_lines.append(f"sec={item.get('hex','?')}")
                else:
                    color_lines.append(f"sec={item}")
        elif secondary:
            color_lines.append(f"secondary={secondary}")
        # accent / background / text si présents
        for key in ("accent", "background", "text"):
            v = colors.get(key)
            if isinstance(v, dict):
                color_lines.append(f"{key}={v.get('hex','?')}")
            elif v:
                color_lines.append(f"{key}={v}")
    if color_lines:
        parts.append(f"- Palette : {', '.join(color_lines[:6])}")

    # Typography : peut avoir {h1,h2,...} où chaque entrée a family/size/weight
    typo = visual.get("typography", {}) or {}
    if isinstance(typo, dict):
        # Cherche family commune (souvent shared entre h1/h2/body)
        families = set()
        for key in ("h1", "h2", "h3", "body", "button"):
            entry = typo.get(key)
            if isinstance(entry, dict) and entry.get("family"):
                families.add(entry["family"].split(",")[0].strip())  # take first font in stack
        if families:
            parts.append(f"- Typographie : {', '.join(sorted(families))}")
        h1 = typo.get("h1")
        if isinstance(h1, dict) and h1.get("size_px"):
            weight = h1.get("weight", "")
            parts.append(f"- H1 style : {h1['size_px']}px {weight}".rstrip())

    shape = visual.get("shape", {})
    if isinstance(shape, dict) and shape.get("border_radius"):
        parts.append(f"- Border-radius : {shape['border_radius']}")
    motion = visual.get("motion", {})
    if isinstance(motion, dict) and motion.get("style"):
        parts.append(f"- Motion : {motion['style']}")

    # ── Method (persona / archetype / Schwartz) ───────────────
    # method peut être un str ("python_phase1+llm_phase2_hybrid") ou un dict
    if isinstance(method, dict):
        archetype = method.get("brand_archetype") or method.get("archetype")
        persona = method.get("persona")
        schwartz = method.get("schwartz_awareness_level") or method.get("schwartz")
        if archetype:
            parts.append(f"\n### ARCHETYPE / PERSONA\n- Archetype : {archetype}")
            if persona:
                parts.append(f"- Persona : {str(persona)[:200]}")
            if schwartz:
                parts.append(f"- Schwartz awareness : {schwartz}")

    # ── Diff prescriptif (E1) ─────────────────────────────────
    if diff:
        parts.append("\n### DIFF PRESCRIPTIF (V26.Z E1 — preserve / amplify / fix / forbid)")
        for quadrant in ("preserve", "amplify", "fix", "forbid"):
            items = diff.get(quadrant)
            if not items:
                continue
            label = quadrant.upper()
            parts.append(f"\n**{label}** :")
            if isinstance(items, list):
                for it in items[:4]:
                    if isinstance(it, dict):
                        # Brand DNA E1 schema : {item, evidence, reason}
                        item_text = it.get("item") or it.get("text") or it.get("description")
                        if item_text:
                            parts.append(f"  - {str(item_text)[:160]}")
                    else:
                        parts.append(f"  - {str(it)[:160]}")
            else:
                parts.append(f"  - {str(items)[:300]}")
        if diff.get("summary"):
            parts.append(f"\n**Synthèse diff** : {str(diff['summary'])[:300]}")

    block = "\n".join(parts)
    if len(block) > max_chars:
        block = block[:max_chars - 20] + "\n[...tronqué]"
    return block


def get_brand_summary(client: str) -> dict:
    """Helper qui retourne un résumé bref pour l'affichage CLI."""
    bd = load_brand_dna(client)
    if not bd:
        return {"client": client, "available": False}
    voice = bd.get("voice_tokens", {})
    visual = bd.get("visual_tokens", {})
    typo = (visual.get("typography") or {})
    # h1.family est où la family vit (pas typography.family direct)
    typo_family = None
    h1 = typo.get("h1")
    if isinstance(h1, dict):
        typo_family = h1.get("family")
    return {
        "client": client,
        "available": True,
        "signature_phrase": voice.get("voice_signature_phrase"),
        "tone": voice.get("tone"),
        "primary_color": (visual.get("colors") or {}).get("primary"),
        "typo": typo_family,
        "has_diff": bool(_extract_diff(bd)),
    }


if __name__ == "__main__":
    # Smoke test
    import sys
    client = sys.argv[1] if len(sys.argv) > 1 else "weglot"
    print(f"\n═══ Brand Intelligence smoke test — {client} ═══\n")
    summary = get_brand_summary(client)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n--- Format brand_block ---\n")
    bd = load_brand_dna(client)
    block = format_brand_block(bd)
    print(f"Block size: {len(block)} chars")
    print(block)
