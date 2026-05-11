"""Prompt block formatters for Mode 1 PERSONA NARRATOR.

Every ``_format_*_block(...)`` helper takes structured data (brand_dna,
AURA tokens, ClientContext, …) and returns a ready-to-concatenate
markdown chunk. Each accepts a ``max_chars`` cap; the new V26.AG
architecture (issue #13) splits content across cached system blocks
(≤4K each, ≤8K total) and pre-filled user-turn dialogue (≤2K each),
so callers pass small per-block budgets rather than the historical 4K+.

The legacy ``_format_*_block`` (FULL) variants have been DELETED with
issue #13: the empirical-regression artefact they preserved (anti-pattern
#1, -28pts on persona_narrator) is now obsolete because the new
architecture uses prompt caching + user-turn dialogue to deliver MORE
context to Sonnet without ever exceeding 8K in the system prefix.

Helpers exposed:

  * ``_format_brand_voice_block``     — voice tokens (signature, tone,
                                        forbidden words, CTA verbs).
  * ``_format_brand_visual_block``    — primary / secondary palette + h1
                                        family.
  * ``_format_brand_forbid_block``    — brand_dna.diff.forbid items.
  * ``_format_aura_tokens_block``     — :root CSS custom properties +
                                        typography mapping (after AI-slop
                                        substitution).
  * ``_load_tokens_css``              — design_grammar V30 tokens.css
                                        loader.
  * ``_format_v143_citations_block``  — founder bio / VoC / scarcity
                                        verified citations.
  * ``_format_golden_techniques_block_LITE`` — 3 refs, 1-line each, full
                                        content via vision input.
  * ``_format_layout_archetype_block_LITE`` — top sections / forbidden
                                        / examples.
  * ``_format_recos_hint_block``      — top-5 P0 recos from
                                        ``ctx.recos_final``.
  * ``_format_intent_for_page_type``  — page-type intent line for the
                                        FORMAT_DOCTRINE_TEMPLATE.
"""
from __future__ import annotations

import json
from typing import Optional

from .philosophy_bridge import (
    ROOT,
    _extract_aesthetic_vector,
    _get_golden_bridge,
)
from .runtime_fixes import _substitute_ai_slop_in_aura
from .vision_selection import ClientContext


# ─────────────────────────────────────────────────────────────────────
# Page-type intent strings (used by SYSTEM_PROMPT_TEMPLATE.format)
# ─────────────────────────────────────────────────────────────────────

FORMAT_INTENT_BY_PAGE_TYPE = {
    "home": (
        "Comme un **manifeste personnel** sur ce que tu construis et pourquoi ça compte. "
        "Pas un livrable marketing. Pas une LP CRO checklist. Un manifeste qu'on lirait sur ton blog perso."
    ),
    "lp_listicle": (
        "Comme un **essai éditorial signé** de toi. C'est un listicle de raisons concrètes (X raisons "
        "pour lesquelles [audience] [action]) — mais écrit comme un journaliste ferait son métier "
        "(toi, le founder, en train de partager ton analyse de l'industrie depuis ton expérience "
        "directe). Pas une LP marketing. Pas un advertorial. Un essai éditorial avec ta voix."
    ),
    "listicle": (
        "Comme un **essai éditorial signé** de toi. C'est un listicle de raisons concrètes (X raisons "
        "pour lesquelles [audience] [action]) — mais écrit comme un journaliste ferait son métier "
        "(toi, le founder, partageant ton analyse de l'industrie). Pas une LP marketing."
    ),
    "advertorial": (
        "Comme un **article éditorial sponsorisé** mais authentique. Ton style natif media, "
        "pas marketing. C'est toi qui partages une perspective d'expert dans la presse spécialisée."
    ),
    "lp_sales": (
        "Comme une **lettre commerciale honnête** : tu expliques à un prospect intéressé exactement "
        "pourquoi ce produit existe, qui il sert, qui il ne sert pas. Aucun bullshit sales."
    ),
    "lp_leadgen": (
        "Comme une **invitation personnelle** à rejoindre quelque chose qui compte. Pas un formulaire "
        "qui aspire un email. Une raison authentique pour laquelle tu offres ce lead magnet."
    ),
    "pdp": (
        "Comme une **présentation produit personnelle** : tu montres ton produit comme tu le ferais "
        "à un ami curieux. Détails techniques honnêtes, sensorialité réelle, défauts assumés."
    ),
    "pricing": (
        "Comme une **conversation transparente sur ton pricing** : tu expliques ce que chaque plan "
        "coûte vraiment et pourquoi. Pas de FOMO, pas de fake urgency. Tu défends tes prix."
    ),
}


def _format_intent_for_page_type(page_type: str) -> str:
    return FORMAT_INTENT_BY_PAGE_TYPE.get(page_type, FORMAT_INTENT_BY_PAGE_TYPE["home"])


# ─────────────────────────────────────────────────────────────────────
# Brand voice / visual / forbid blocks
# ─────────────────────────────────────────────────────────────────────

def _format_brand_voice_block(brand_dna: dict) -> str:
    voice = brand_dna.get("voice_tokens", {}) or {}
    parts = []
    sig = voice.get("voice_signature_phrase")
    if sig:
        parts.append(f"- Signature : « {sig} »")
    tone = voice.get("tone")
    if tone:
        if isinstance(tone, list):
            parts.append(f"- Ton : {', '.join(tone)}")
        else:
            parts.append(f"- Ton : {tone}")
    forbidden = voice.get("forbidden_words")
    if forbidden:
        parts.append(f"- Mots INTERDITS (anti-marque) : {', '.join(forbidden[:10])}")
    cta_verbs = voice.get("preferred_cta_verbs")
    if cta_verbs:
        parts.append(f"- Verbes CTA naturels chez toi : {', '.join(cta_verbs[:6])}")
    rhythm = voice.get("sentence_rhythm")
    if rhythm:
        parts.append(f"- Rythme phrase : {rhythm}")
    return "\n".join(parts) if parts else "(brand voice non extraite — incarne ce que tu sais du client)"


def _format_brand_visual_block(brand_dna: dict) -> str:
    visual = brand_dna.get("visual_tokens", {}) or {}
    colors = visual.get("colors", {}) or {}
    parts = []
    primary = colors.get("primary")
    if isinstance(primary, dict):
        parts.append(f"- Primary : {primary.get('hex','?')} ({primary.get('usage_hint','')})")
    elif primary:
        parts.append(f"- Primary : {primary}")
    secondary = colors.get("secondary")
    if isinstance(secondary, list):
        for item in secondary[:2]:
            if isinstance(item, dict):
                parts.append(f"- Secondary : {item.get('hex','?')}")
    typo = visual.get("typography", {}) or {}
    if isinstance(typo, dict):
        h1 = typo.get("h1")
        if isinstance(h1, dict) and h1.get("family"):
            family = h1["family"].split(",")[0].strip()
            parts.append(f"- Typographie : {family}")
    return "\n".join(parts) if parts else "(palette/typo non extraites)"


def _format_brand_forbid_block(brand_dna: dict) -> str:
    diff = brand_dna.get("diff", {}) or {}
    forbid = diff.get("forbid", []) or []
    if not forbid:
        return "(aucun pattern explicitement interdit — utilise ton jugement de founder)"
    items = []
    for it in forbid[:5]:
        if isinstance(it, dict):
            text = it.get("item") or it.get("description") or it.get("text")
            if text:
                items.append(str(text)[:120])
        else:
            items.append(str(it)[:120])
    return "\n".join(f"- {x}" for x in items) if items else "(forbidden patterns non extraits)"


# ─────────────────────────────────────────────────────────────────────
# AURA tokens (CSS custom props) + design_grammar tokens.css loader
# ─────────────────────────────────────────────────────────────────────

def _format_aura_tokens_block(aura: Optional[dict], tokens_css: Optional[str] = None, max_chars: int = 3500) -> str:
    """Sprint G V26.AC — injecte AURA tokens + CSS pré-fabriqué (tokens.css design_grammar V30).

    Au lieu de reformuler en texte, on donne à Sonnet le CSS DIRECT prêt à coller
    dans son `<style>`. Sonnet utilise var(--color-primary), var(--font-display) etc.
    C'est le pattern "Hard system → structure" de l'audit ChatGPT V3.

    Sprint G fix : substitute AI-slop fonts (Inter/Roboto/etc) AVANT injection.
    """
    if aura:
        aura, substitutions = _substitute_ai_slop_in_aura(aura)
    if not aura and not tokens_css:
        return ""

    parts = ["\n## 🎨 DESIGN TOKENS — CSS PRÊT À L'EMPLOI (à inclure dans ton <style>)"]
    parts.append("")
    parts.append("Tu DOIS inclure les CSS custom properties ci-dessous dans ton `<style>` HTML")
    parts.append("et utiliser EXCLUSIVEMENT `var(--name)` partout au lieu de hardcoder des valeurs.")
    parts.append("")

    # 1. CSS pré-fabriqué AURA (si dispo) — c'est le bloc le plus important
    if aura:
        css_props = aura.get("css_custom_properties") or aura.get("css") or ""
        if css_props:
            parts.append("```css")
            parts.append(":root {")
            if isinstance(css_props, dict):
                for k, v in css_props.items():
                    parts.append(f"  --{k}: {v};")
            elif isinstance(css_props, str):
                parts.append(css_props.strip())
            parts.append("}")
            parts.append("```")

    # 2. design_grammar/tokens.css (V30) — encore plus prescriptif (radius, spacing, motion)
    if tokens_css and tokens_css.strip():
        parts.append("\n## CSS TOKENS V30 design_grammar (AJOUTE aussi ces variables)")
        parts.append("```css")
        parts.append(tokens_css.strip()[:1500])
        parts.append("```")

    # 3. Typography mapping explicite (display vs body — leçon Sprint F.fix v2 où Sonnet
    #    a tout mis en Inter alors qu'AURA dit display=Ppneuemontreal/body=Inter)
    if aura:
        typo = aura.get("typography") or {}
        if isinstance(typo, dict):
            display = typo.get("display") or typo.get("heading")
            body = typo.get("body")
            if display or body:
                parts.append("\n## ⛔ TYPOGRAPHIE STRICT MAPPING")
                if display:
                    parts.append(f"  - **h1, h2, h3, h4** : `font-family: '{display}', Georgia, serif;`")
                if body:
                    # Si body est dans la blacklist anti-AI-slop, propose alternative
                    AI_SLOP = {"Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat",
                               "Poppins", "Nunito", "Helvetica"}
                    if body in AI_SLOP:
                        parts.append(f"  - ⚠️ AURA assigne body='{body}' (AI-slop blacklist) — SUBSTITUE par 'IBM Plex Sans' OU 'DM Sans' OU 'Spectral' (non-AI-slop, dispos Google Fonts).")
                    else:
                        parts.append(f"  - **body, p, li, span** : `font-family: '{body}', system-ui, sans-serif;`")
                parts.append(f"  - INTERDIT body en Inter/Roboto/Arial/Open Sans/Lato/Montserrat/Poppins/Nunito/Helvetica.")
                parts.append(f"  - Charge les fonts via `<link href=\"https://fonts.googleapis.com/css2?family=...\">` dans `<head>`.")

    block = "\n".join(parts)
    return block[:max_chars] if len(block) > max_chars else block


def _load_tokens_css(client: str) -> Optional[str]:
    """Charge le CSS pré-fabriqué design_grammar V30."""
    p = ROOT / "data" / "captures" / client / "design_grammar" / "tokens.css"
    if p.exists():
        try:
            return p.read_text()
        except Exception:
            return None
    return None


# ─────────────────────────────────────────────────────────────────────
# v143 enrichment block (founder + VoC + scarcity)
# ─────────────────────────────────────────────────────────────────────

def _format_v143_citations_block(ctx: ClientContext, max_chars: int = 1500) -> str:
    """Sprint F V26.AC — injecte v143 founder + VoC + scarcity (citations vérifiées vs inventées)."""
    if not ctx.has_v143_enrichment:
        return ""
    parts = ["\n## CITATIONS VÉRIFIÉES (v143 — utilise UNIQUEMENT ces faits/quotes)"]
    if ctx.v143_founder:
        f = ctx.v143_founder
        bio = f.get("bio") or f.get("about") or ""
        if bio:
            parts.append(f"\n### Founder bio (extrait About + LinkedIn vérifié)")
            parts.append(f"  {str(bio)[:300]}")
    if ctx.v143_voc:
        v = ctx.v143_voc
        verbatims = v.get("verbatims") or v.get("reviews") or []
        if verbatims:
            parts.append(f"\n### Voice of Customer (Trustpilot/G2 verbatims réels)")
            for q in verbatims[:3]:
                if isinstance(q, dict):
                    txt = q.get("text") or q.get("quote", "")
                    auth = q.get("author") or q.get("name", "")
                    parts.append(f'  - « {str(txt)[:150]} » — {auth}')
                else:
                    parts.append(f"  - « {str(q)[:150]} »")
    if ctx.v143_scarcity:
        s = ctx.v143_scarcity
        if s:
            parts.append(f"\n### Scarcity réelle (anti-fake)")
            for k, v in (s.items() if isinstance(s, dict) else []):
                parts.append(f"  - {k}: {v}")
    block = "\n".join(parts)
    return block[:max_chars] if len(block) > max_chars else block


# ─────────────────────────────────────────────────────────────────────
# Golden Design Bridge integration (Sprint AD-3) — LITE + FULL
# ─────────────────────────────────────────────────────────────────────

def _format_golden_techniques_block_LITE(
    aura: Optional[dict],
    page_type: str,
    max_chars: int = 800,
) -> tuple[str, list[dict]]:
    """V26.AE — Version LITE du golden techniques block (default).

    Format court : 3 sites refs avec signature 1 ligne chacun. Les techniques
    techniques détaillées (css_approach Opus) NE sont PAS injectées dans le prompt
    — Sonnet voit les screenshots golden refs en VISION input et déduit visuellement.

    Returns: (prompt_block, philosophy_refs) où philosophy_refs est utilisé
    par _select_vision_screenshots() pour ajouter les golden screenshots.
    """
    target_vector = _extract_aesthetic_vector(aura)
    if not target_vector:
        return "", []

    bridge = _get_golden_bridge()
    if not bridge:
        return "", []

    try:
        closest = bridge.find_closest(target_vector, top_n=3)
    except Exception:
        return "", []

    parts = ["\n## 🎨 RÉFÉRENCES VISUELLES — Sites dont l'ADN esthétique est proche du tien"]
    philosophy_refs: list[dict] = []
    for profile, dist in closest:
        sig = (profile.get("signature") or "")[:130]
        parts.append(f"  - **{profile['label'].upper()}/{profile['page']}** : {sig}")
        philosophy_refs.append({
            "site": profile["label"],
            "page": profile["page"],
            "category": profile.get("category"),
            "distance": round(dist, 2),
            "vector": profile["vector"],
            "signature": profile.get("signature", ""),
        })
    parts.append("\nTu vois 2 de ces refs en INPUT VISION (images 3-4) — étudie leur niveau d'exécution visuelle (drop caps, marginalia, hairlines, pull quotes). Emprunte les TECHNIQUES, fusionne dans TA signature.")

    block = "\n".join(parts)
    return block[:max_chars] if len(block) > max_chars else block, philosophy_refs


# ─────────────────────────────────────────────────────────────────────
# Layout archétype loader + formatter (Sprint AD-5) — LITE + FULL
# ─────────────────────────────────────────────────────────────────────

def _load_layout_archetype(page_type: str) -> Optional[dict]:
    """Charge l'archétype de structure pour ce page_type. Fallback : None."""
    p = ROOT / "data" / "layout_archetypes" / f"{page_type}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _format_layout_archetype_block_LITE(page_type: str, max_chars: int = 1200) -> str:
    """V26.AE — Version LITE de l'archetype block (default).

    Format court : philosophie + 3 sections required (titre seul) + 3 forbidden patterns.
    Le check de structure complète passe en POST-PROCESS GATE (pas dans le prompt).
    """
    arch = _load_layout_archetype(page_type)
    if not arch:
        return ""

    parts = [f"\n## 📐 LAYOUT — {page_type.upper()}"]
    parts.append(f"*{arch.get('philosophy', '')[:200]}*\n")

    # Top 3 sections required (titre seul, pas 'where/what/why' détaillé)
    sections = arch.get("structure_required", [])[:5]
    if sections:
        parts.append("**Structure obligatoire** :")
        for i, s in enumerate(sections, 1):
            parts.append(f"  {i}. {s.get('section', '?')}")
    # Top 3 forbidden patterns
    forbidden = arch.get("structure_forbidden", [])[:3]
    if forbidden:
        parts.append("\n**INTERDIT (structure)** :")
        for f in forbidden:
            parts.append(f"  - {f[:100]}")
    # Examples to imitate (1 ligne chacun)
    examples = arch.get("examples_to_imitate", [])[:3]
    if examples:
        parts.append("\n**Réfs à imiter** : " + ", ".join(e[:50] for e in examples))

    block = "\n".join(parts)
    return block[:max_chars] if len(block) > max_chars else block


# ─────────────────────────────────────────────────────────────────────
# Recos hint block (Mode 2 REPLACE refonte)
# ─────────────────────────────────────────────────────────────────────

def _format_recos_hint_block(ctx: ClientContext, max_chars: int = 1000) -> str:
    """Sprint F V26.AC — injecte hints depuis recos_v13_final (Mode 2 REPLACE refonte)."""
    if not ctx.recos_final:
        return ""
    recos = ctx.recos_final.get("recos") or ctx.recos_final.get("recommendations") or []
    if not recos:
        return ""
    parts = [f"\n## GAPS AUDIT IDENTIFIÉS pour cette page (top 5 — à corriger en priorité)"]
    p0_recos = [r for r in recos if (r.get("priority") == "P0" or r.get("priority_level") == "P0")]
    top = p0_recos[:5] if p0_recos else recos[:5]
    for r in top:
        crit = r.get("criterion_id") or r.get("criterion", "?")
        action = r.get("action") or r.get("recommendation") or r.get("fix", "")
        parts.append(f"  - **{crit}** : {str(action)[:200]}")
    block = "\n".join(parts)
    return block[:max_chars] if len(block) > max_chars else block


__all__ = [
    "FORMAT_INTENT_BY_PAGE_TYPE",
    "_format_intent_for_page_type",
    "_format_brand_voice_block",
    "_format_brand_visual_block",
    "_format_brand_forbid_block",
    "_format_aura_tokens_block",
    "_load_tokens_css",
    "_format_v143_citations_block",
    "_format_golden_techniques_block_LITE",
    "_load_layout_archetype",
    "_format_layout_archetype_block_LITE",
    "_format_recos_hint_block",
]
