"""Mode 1 PERSONA NARRATOR V26.AB Sprint D POC — excellence dès le 1er run.

PIVOT PARADIGMATIQUE post-audit ChatGPT V3 + Mathis (2026-05-04) :
le LLM ne reçoit plus une checklist. Il reçoit une POSTURE D'INCARNATION.
Tu es le founder. Tu écris ton manifeste. Pas une LP marketing.

Différences vs Mode 1 COMPLETE V26.AA :
  - Pas de doctrine 7 critères en INPUT
  - Pas de design_grammar V30 en INPUT
  - Pas de creative_director route en INPUT
  - Pas de top_critical_for_page_type en INPUT
  - Pas de killer_rules en INPUT
  - Mission : "incarne le founder, écris ton manifeste" (vs "satisfait ces critères")
  - Règle de renoncement EXPLICITE (vs implicite)
  - Prompt court (~5-6K chars total vs 10-13K Sprint 3-C)

Le seul gate de qualité (POC) : Mathis lit, est-ce mémorable ?
La doctrine V3.2.1 reste disponible en post-process gate (info only, pas blocking).
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Optional

from ..core.brand_intelligence import load_brand_dna, has_brand_dna
from ..core.pipeline_single_pass import call_sonnet, call_sonnet_multimodal, apply_runtime_fixes

ROOT = pathlib.Path(__file__).resolve().parents[2]
import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts"))
from client_context import load_client_context, ClientContext  # noqa: E402 — ROUTER RACINE V26.AC


# ─────────────────────────────────────────────────────────────────────────────
# Founders connus — hardcoded pour clients curatés V26
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_FOUNDERS = {
    "weglot": (
        "Augustin Prot, cofondateur de Weglot avec Rémy Berda en 2016. "
        "Polyglotte qui a passé des années à voir des sites SaaS souffrir de la "
        "complexité de la traduction (dev backlog, SEO multi-langue cassé, qualité "
        "humaine vs auto). 65 000+ sites servis aujourd'hui. "
        "Tu connais par cœur la peur n°1 d'un Head of Growth SaaS B2B qui veut "
        "internationaliser : « ça va exploser le dev backlog, casser le SEO, "
        "la traduction auto va donner un truc pourri ». Tu as vu cette peur "
        "65 000 fois et tu sais que ce n'est pas obligé."
    ),
    "linear": (
        "Karri Saarinen, ex-Airbnb design lead, frustré par Jira pendant 8 ans "
        "avant de cofonder Linear. Tu as la conviction profonde que la productivité "
        "dev passe par MOINS de friction visuelle, pas plus de features. "
        "Tu écris pour un dev senior qui ouvre Jira chaque matin avec un soupir."
    ),
    "japhy": (
        "Hugo Vacheron et Antoine Vacher, cofondateurs Japhy 2018. Tu as vu "
        "ton propre chien refuser ses croquettes industrielles. Ta conviction : "
        "chaque chien est unique (race, âge, poids, sensibilités) donc son "
        "alimentation doit l'être. Recalculée au gramme près, livrée chaque mois. "
        "Tu écris pour un propriétaire qui aime son chien comme un membre de famille "
        "et qui sent depuis longtemps que les croquettes mass-market ne lui vont pas."
    ),
    "stripe": (
        "Patrick et John Collison, frères qui ont écrit la première version de "
        "Stripe à coder un soir de 2010 parce qu'ils trouvaient absurde qu'il "
        "faille 6 semaines pour accepter un paiement en ligne. "
        "Tu écris pour un founder ou dev qui sait que l'argent compte mais qui "
        "déteste perdre du temps avec les banques."
    ),
    "notion": (
        "Ivan Zhao, cofondateur Notion. Tu as la conviction que les outils "
        "doivent s'adapter à l'humain, pas l'inverse. Pas de feature war, pas "
        "de roadmap surchargée. Une primitive simple (block) qui peut tout devenir."
    ),
    "duolingo": (
        "Luis von Ahn, cofondateur Duolingo. Tu as vu des millions de personnes "
        "abandonner l'apprentissage des langues parce que trop austère, trop cher, "
        "trop académique. Ta conviction : si c'est pas un jeu, ça ne marche pas. "
        "5 minutes par jour, gratuit, addictif comme TikTok mais utile."
    ),
}


def build_founder_persona(client: str, brand_dna: dict) -> str:
    """Construit la posture d'incarnation founder.

    Si client dans KNOWN_FOUNDERS → utilise founder hardcodé (le plus fort).
    Sinon → extrait depuis brand_dna (signature_phrase + tone + archetype).
    """
    if client in KNOWN_FOUNDERS:
        return KNOWN_FOUNDERS[client]

    voice = brand_dna.get("voice_tokens", {}) or {}
    signature = voice.get("voice_signature_phrase") or "?"
    tone_raw = voice.get("tone")
    tone = ", ".join(tone_raw) if isinstance(tone_raw, list) else (tone_raw or "?")

    method = brand_dna.get("method", {})
    if isinstance(method, dict):
        archetype = method.get("brand_archetype") or method.get("archetype")
    else:
        archetype = None

    persona = (
        f"Tu es le founder de {client}. "
        f"Ta voix se résume en : « {signature} ». "
        f"Ton ton est : {tone}. "
    )
    if archetype:
        persona += f"Archetype de marque : {archetype}. "
    persona += (
        f"Tu connais ton produit jusque dans la moelle parce que tu l'as conçu "
        f"pour résoudre une frustration que tu vivais toi-même. Tu écris cette "
        f"page comme un manifeste personnel sur ce que tu construis et pourquoi "
        f"ça compte."
    )
    return persona


# ─────────────────────────────────────────────────────────────────────────────
# Prompt assembly (court, mission "incarne", pas checklist)
# ─────────────────────────────────────────────────────────────────────────────

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


SYSTEM_PROMPT_TEMPLATE = """{founder_persona}

## TON RÔLE

Tu écris cette page comme TU l'écrirais à 3h du matin, dans ton garage, à un ami qui te demande pourquoi ton produit existe.

**Format spécifique de CETTE page (`{page_type}`)** :
{format_intent}

## RÈGLE DE RENONCEMENT (la plus importante)

Si tu n'as pas une CONVICTION PROFONDE pour justifier un mot, **NE L'ÉCRIS PAS**.

INTERDIT de mettre du creux :
- Pas de claim chiffré sans source vérifiée dans ton brand DNA
- Pas de "leader du marché", "the best", "innovant" sans preuve
- Pas de verbes vides : "découvrez", "explorez", "transformez", "boostez", "optimisez"
- Pas de testimonial inventé ("Sarah, 32 ans, marketing manager")
- Pas de chiffres ronds inventés (+50%, +127%, etc.) — seulement ceux que tu as VRAIMENT mesurés
- Pas d'icônes checkmark systématiques (✓✓✓ = AI showcase)

Si une section serait creuse → **omets-la**. Une page courte avec 100% de conviction bat une page longue avec 50% de bullshit.

## TA MARQUE (mots qui te définissent ou qui te trahissent)

{brand_voice_block}

## VISUEL

Tu utilises **TES couleurs** (extraites de ton site réel — pas inventées) :
{brand_visual_block}

Patterns visuels que ta marque INTERDIT (anti-toi) :
{brand_forbid_block}

## FORMAT FINAL

HTML autocontenu mobile-first.
- Sortie commence par `<!DOCTYPE html>` et finit par `</html>`
- Pas de markdown wrapper, pas de commentaires hors HTML
- Sémantique correcte (`<header>`, `<main>`, `<section>`, `<footer>`)
- Mobile-first (375px) puis desktop (1440px)
- Une seule balise `<h1>`
- Aucune dépendance externe (Google Fonts via `<link>` accepté, mais pas d'images sur CDN tiers)
- Pas de stock photo lifestyle. Pas de SVG décoratif. Si tu mets un visuel, c'est un produit en usage RÉEL ou un schéma qui clarifie ta conviction.

## TA MISSION CONCRÈTE

Page : **{page_type}** pour **{client}**

Brief client :
- **Objectif business** : {brief_objectif}
- **Audience cible** : {brief_audience}
- **Hook / angle éditorial** : {brief_angle}

Maintenant, écris ton manifeste. Si à un moment tu sens que tu vas mettre du bullshit pour "remplir une section", **arrête-toi** et trouve la conviction profonde qui justifie cette section, ou supprime-la."""


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


AI_SLOP_FONTS = {"Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat",
                 "Poppins", "Nunito", "Helvetica"}
NON_AI_SLOP_BODY_ALTERNATIVES = ["DM Sans", "IBM Plex Sans", "Spectral",
                                  "Source Sans 3", "Outfit"]


def _substitute_ai_slop_in_aura(aura: dict) -> tuple[dict, dict]:
    """Sprint G V26.AC fix — substitute AI-slop fonts dans AURA AVANT injection.

    Si AURA.typography.body est Inter/Roboto/etc → remplace par DM Sans (1ère alternative).
    Si AURA.css_custom_properties contient --font-body: Inter → idem.

    Returns: (aura_clean, substitutions_log)
    """
    import copy
    aura_clean = copy.deepcopy(aura)
    substitutions = {}

    # Substituer typography.body si AI-slop
    typo = aura_clean.get("typography", {})
    if isinstance(typo, dict):
        body = typo.get("body")
        if body and body in AI_SLOP_FONTS:
            substitutions["typography.body"] = f"{body} → DM Sans (anti-AI-slop)"
            typo["body"] = "DM Sans"
            typo["body_substituted_from"] = body

    # Substituer dans css_custom_properties
    css_props = aura_clean.get("css_custom_properties")
    if isinstance(css_props, dict):
        for key, val in list(css_props.items()):
            if "font" in key.lower() and isinstance(val, str):
                for slop in AI_SLOP_FONTS:
                    if slop in val:
                        new_val = val.replace(slop, "DM Sans")
                        css_props[key] = new_val
                        substitutions[f"css.{key}"] = f"{slop} → DM Sans"
                        break
    elif isinstance(css_props, str):
        for slop in AI_SLOP_FONTS:
            if slop in css_props:
                aura_clean["css_custom_properties"] = css_props.replace(slop, "DM Sans")
                substitutions["css_props_str"] = f"{slop} → DM Sans"
                break

    return aura_clean, substitutions


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


# ─────────────────────────────────────────────────────────────────────────────
# Sprint AD-3 V26.AD+ — Golden Design Bridge integration
# 75 golden pages × ~5-7 techniques = ~150 techniques CSS prescriptives Opus-extraites
# Branchées au prompt persona_narrator pour donner à Sonnet des refs concrètes
# (vs Sonnet improvisant sur les seuls screenshots client).
# ─────────────────────────────────────────────────────────────────────────────

_GOLDEN_BRIDGE_CACHE = None

def _get_golden_bridge():
    """Lazy-load + cache the GoldenDesignBridge (lourd à instancier : 75 profiles)."""
    global _GOLDEN_BRIDGE_CACHE
    if _GOLDEN_BRIDGE_CACHE is None:
        import importlib.util
        bridge_path = ROOT / "skills" / "growth-site-generator" / "scripts" / "golden_design_bridge.py"
        if not bridge_path.exists():
            return None
        spec = importlib.util.spec_from_file_location("golden_design_bridge", bridge_path)
        mod = importlib.util.module_from_spec(spec)
        # Silence the loader's print() since it spams stdout each load
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
            _GOLDEN_BRIDGE_CACHE = mod.GoldenDesignBridge()
    return _GOLDEN_BRIDGE_CACHE


def _extract_aesthetic_vector(aura: Optional[dict]) -> Optional[dict]:
    """Extrait le vecteur 8D (energy/warmth/density/depth/motion/editorial/playful/organic)
    depuis AURA tokens. Fallback : None si pas dispo."""
    if not aura:
        return None
    v = aura.get("vector") or aura.get("aesthetic_vector") or aura.get("vector_8d")
    if not isinstance(v, dict):
        return None
    required = ["energy", "warmth", "density", "depth", "motion", "editorial", "playful", "organic"]
    if not all(k in v for k in required):
        return None
    return {k: float(v[k]) for k in required}


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
    philosophy_refs = []
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


def _format_golden_techniques_block(
    aura: Optional[dict],
    page_type: str,
    max_chars: int = 4000,
) -> tuple[str, list[dict]]:
    """Sprint AD-3 — Version FULL (debug/explicit, anti-pattern #1 si default).

    Injecte philosophy refs + techniques par type avec css_approach Opus.
    **NE PAS UTILISER en default** — passer par _format_golden_techniques_block_LITE.
    """
    target_vector = _extract_aesthetic_vector(aura)
    if not target_vector:
        return "", []

    bridge = _get_golden_bridge()
    if not bridge:
        return "", []

    try:
        benchmark = bridge.get_design_benchmark(target_vector)
    except Exception:
        return "", []

    prompt_block = benchmark.get("prompt_block", "")
    philosophy_refs = benchmark.get("philosophy_refs", [])

    # Add a stronger framing for persona_narrator context (vs raw bridge prompt)
    framing = (
        "\n## 🎨 SIGNATURE VISUELLE DE RÉFÉRENCE — TECHNIQUES PRESCRIPTIVES (Sprint AD-3)\n"
        "\nVoici les sites dont l'ADN esthétique est PROCHE du tien (matching vector 8D), "
        "et les meilleures techniques CSS à emprunter (croisement cross-catégorie). "
        "**Tu DOIS produire un design au moins aussi mémorable que ces refs**, en empruntant "
        "leurs TECHNIQUES (pas leurs styles) et en les fusionnant pour créer ta propre signature.\n"
    )
    full_block = framing + "\n" + prompt_block

    if len(full_block) > max_chars:
        full_block = full_block[:max_chars] + "\n[...] (block tronqué)"

    return full_block, philosophy_refs


# ─────────────────────────────────────────────────────────────────────────────
# Sprint AD-5 V26.AD+ — Layout archétypes par page_type
# Chaque archétype dans data/layout_archetypes/<page_type>.json prescrit la
# structure ÉDITORIALE attendue (sections required/forbidden + typography +
# decorative techniques required/forbidden + examples_to_imitate).
# ─────────────────────────────────────────────────────────────────────────────

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


def _format_layout_archetype_block(page_type: str, max_chars: int = 4500) -> str:
    """Sprint AD-5 — Version FULL (debug/explicit, anti-pattern #1 si default).

    Donne à Sonnet une PRESCRIPTION concrète (sections required, forbidden,
    typography rules, decorative techniques) au lieu de le laisser improviser
    le layout. **NE PAS UTILISER en default** — passer par _format_layout_archetype_block_LITE.
    """
    arch = _load_layout_archetype(page_type)
    if not arch:
        return ""

    parts = [f"\n## 📐 ARCHÉTYPE DE STRUCTURE — {page_type.upper()} (FULL)"]
    parts.append(f"\n*{arch.get('philosophy', '')}*\n")

    # Sections required
    sections = arch.get("structure_required", [])
    if sections:
        parts.append("### STRUCTURE OBLIGATOIRE (dans cet ordre) :")
        for i, s in enumerate(sections, start=1):
            parts.append(f"\n{i}. **{s.get('section', '?')}**")
            if s.get("where"):
                parts.append(f"   *où :* {s['where']}")
            parts.append(f"   *quoi :* {s.get('what', '')}")
            if s.get("why"):
                parts.append(f"   *pourquoi :* {s['why']}")

    # Sections forbidden
    forbidden = arch.get("structure_forbidden", [])
    if forbidden:
        parts.append("\n\n### ⛔ STRUCTURE INTERDITE :")
        for f in forbidden:
            parts.append(f"  - {f}")

    # Typography
    typo = arch.get("typography_required", [])
    if typo:
        parts.append("\n\n### TYPOGRAPHIE OBLIGATOIRE :")
        for t in typo:
            parts.append(f"  - {t}")

    # Decorative required
    deco_req = arch.get("decorative_techniques_required", [])
    if deco_req:
        parts.append("\n\n### TECHNIQUES VISUELLES OBLIGATOIRES :")
        for d in deco_req:
            parts.append(f"  - {d}")

    # Decorative forbidden
    deco_forbid = arch.get("decorative_techniques_forbidden", [])
    if deco_forbid:
        parts.append("\n\n### ⛔ TECHNIQUES VISUELLES INTERDITES (anti-AI-slop) :")
        for d in deco_forbid:
            parts.append(f"  - {d}")

    # Color strategy
    color = arch.get("color_strategy")
    if color:
        parts.append(f"\n\n### STRATÉGIE COULEUR : {color}")

    # Examples
    examples = arch.get("examples_to_imitate", [])
    anti_examples = arch.get("anti_examples", [])
    if examples or anti_examples:
        parts.append("\n\n### RÉFÉRENCES :")
        if examples:
            parts.append("**Imiter** :")
            for e in examples[:5]:
                parts.append(f"  - {e}")
        if anti_examples:
            parts.append("\n**Éviter** :")
            for e in anti_examples[:3]:
                parts.append(f"  - {e}")

    block = "\n".join(parts)
    return block[:max_chars] if len(block) > max_chars else block


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


def _select_vision_screenshots(
    ctx: ClientContext,
    fallback_page_for_vision: Optional[str],
    max_images: int = 2,
    philosophy_refs: Optional[list[dict]] = None,  # Sprint AD-4 V26.AD+ : golden inspirations
    max_golden_inspirations: int = 2,
) -> list[pathlib.Path]:
    """Sprint F V26.AC + AD-4 V26.AD+ — sélectionne les screenshots VISION Sonnet.

    Priorité :
    1. 1-2 screenshots du client (page demandée OU fallback page) — ce que la marque EST
    2. 1-2 screenshots des golden inspirations cross-cat (philosophy_refs) — ce que la marque
       DOIT atteindre comme niveau visuel (Sprint AD-4 : Sonnet voit l'objectif, pas que le statu quo)

    On préfère `_fold` (above-the-fold, sous la limite Anthropic 8000px de hauteur)
    plutôt que `_full` (rejeté car >8000px souvent).
    """
    selected = []
    sources = ctx.screenshots
    if not sources and fallback_page_for_vision:
        fallback_ctx = load_client_context(ctx.client, fallback_page_for_vision)
        sources = fallback_ctx.screenshots

    # ── A. Screenshots client (max_images max) ──
    if sources:
        preferred_fold = ["desktop_clean_fold", "mobile_clean_fold"]
        for name in preferred_fold:
            if name in sources:
                selected.append(sources[name])
            if len(selected) >= max_images:
                break

        if len(selected) < max_images:
            for name in ["desktop_asis_fold", "mobile_asis_fold"]:
                if name in sources and sources[name] not in selected:
                    selected.append(sources[name])
                if len(selected) >= max_images:
                    break

    # ── B. Sprint AD-4 — Golden inspirations cross-cat (max_golden_inspirations) ──
    # On ajoute des screenshots de golden refs en plus du client. Sonnet voit donc
    # le client (à respecter en palette/typo) + les cibles esthétiques (à imiter en niveau).
    if philosophy_refs and max_golden_inspirations > 0:
        for ref in philosophy_refs[:max_golden_inspirations]:
            site = ref.get("site")
            page = ref.get("page", "home")
            if not site:
                continue
            golden_dir = ROOT / "data" / "golden" / site / page / "screenshots"
            if not golden_dir.exists():
                continue
            # Préférer fold desktop (sous limite 8000px)
            for fname in ["spatial_fold_desktop.png", "spatial_fold_mobile.png", "spatial_full_page.png"]:
                fp = golden_dir / fname
                if fp.exists() and fp not in selected:
                    selected.append(fp)
                    break  # un seul screenshot par golden ref

    return selected


def _check_aura_font_violations(html: str) -> list[str]:
    """Sprint F V26.AC — POST-GATE check : font blacklist AURA dans le HTML."""
    blacklist = ["Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat", "Poppins", "Nunito", "Helvetica"]
    violations = []
    html_lower = html.lower()
    for font in blacklist:
        # Cherche dans font-family / Google Fonts URL
        if f"family={font.replace(' ', '+')}".lower() in html_lower or f'"{font}"'.lower() in html_lower or f"'{font}'".lower() in html_lower or f"font-family: {font}".lower() in html_lower:
            violations.append(font)
    return violations


# ─────────────────────────────────────────────────────────────────────────────
# Sprint AD-6 V26.AD+ — Anti-AI-slop visuel renforcé
# Patterns CSS qui sont des signatures OBVIOUS d'AI-generated design dont on
# veut absolument se débarrasser. Détection regex + reporting.
# ─────────────────────────────────────────────────────────────────────────────

def _check_ai_slop_visual_patterns(html: str) -> list[dict]:
    """Sprint AD-6 — Détecte les patterns visuels AI-slop dans le HTML.

    Returns: list of {pattern, severity, count, sample}.
    """
    import re
    violations = []
    html_lower = html.lower()

    # 1. Gradient 135deg avatar (signature ChatGPT/Claude design 2024)
    pattern_135 = re.findall(r"linear-gradient\(\s*135deg[^)]+\)", html, re.IGNORECASE)
    if pattern_135:
        violations.append({
            "pattern": "gradient_135deg_avatar",
            "severity": "high",
            "count": len(pattern_135),
            "sample": pattern_135[0][:120],
            "fix": "Use a real photo, monochrome monogramme initials on white bg, or solid color circle.",
        })

    # 2. Gradient mesh / radial multi-stop background
    radial_mesh = re.findall(r"radial-gradient\([^)]+\)", html, re.IGNORECASE)
    if len(radial_mesh) >= 2:
        violations.append({
            "pattern": "gradient_mesh_background",
            "severity": "high",
            "count": len(radial_mesh),
            "sample": radial_mesh[0][:120],
            "fix": "Solid neutral background. If you need depth, use subtle hairline rules, not gradients.",
        })

    # 3. RGBA gradient box (insight-box pattern AI 2023-2024)
    rgba_gradient = re.findall(r"linear-gradient\([^)]*rgba?\s*\([^)]+\)[^)]*rgba?\s*\([^)]+\)[^)]*\)", html, re.IGNORECASE)
    if rgba_gradient:
        violations.append({
            "pattern": "rgba_gradient_box",
            "severity": "medium",
            "count": len(rgba_gradient),
            "sample": rgba_gradient[0][:120],
            "fix": "Use solid neutral background or pure white box with hairline border.",
        })

    # 4. Border-left colored callout (template blog 2018)
    border_left_callout = re.findall(r"border-left\s*:\s*\d+px\s+solid\s+var\(--[\w-]*(?:primary|accent|secondary)[\w-]*\)", html, re.IGNORECASE)
    if border_left_callout:
        violations.append({
            "pattern": "border_left_callout_blog2018",
            "severity": "medium",
            "count": len(border_left_callout),
            "sample": border_left_callout[0][:120],
            "fix": "Use marginalia (offset to side), inline stat callout (number + caption), or pull quote with italic only.",
        })

    # 5. Neumorphism shadows (2020 trend dépassée)
    neumorphism = re.findall(r"box-shadow\s*:\s*[^;]*-?\d+px\s+-?\d+px\s+\d+px[^;]+inset", html, re.IGNORECASE)
    if neumorphism:
        violations.append({
            "pattern": "neumorphism_shadow",
            "severity": "high",
            "count": len(neumorphism),
            "sample": neumorphism[0][:120],
            "fix": "Use single subtle drop shadow OR no shadow + hairline border.",
        })

    # 6. Glassmorphism (backdrop-filter blur cards)
    glassmorphism = re.findall(r"backdrop-filter\s*:\s*blur\s*\(", html, re.IGNORECASE)
    if glassmorphism:
        violations.append({
            "pattern": "glassmorphism_blur",
            "severity": "medium",
            "count": len(glassmorphism),
            "sample": glassmorphism[0][:120],
            "fix": "Use solid card or semi-transparent overlay without blur (2024 trend → out).",
        })

    # 7. Pill button radius 999px on regular CTA (= cheap signal sauf si signature brand)
    pill_buttons = re.findall(r"\.cta[^{]*\{[^}]*border-radius\s*:\s*999", html, re.IGNORECASE)
    if pill_buttons:
        violations.append({
            "pattern": "pill_button_999px",
            "severity": "low",
            "count": len(pill_buttons),
            "sample": pill_buttons[0][:80],
            "fix": "Use radius 4-8px (= signal pro éditorial) sauf si pill 999px est signature explicite de la brand.",
        })

    # 8. 3-cards grid with icons (template SaaS 2018)
    # Heuristic: ≥3 sibling .card / .feature classes
    card_count = len(re.findall(r"class=[\"'][^\"']*(?:feature-card|value-card|pricing-card)[^\"']*[\"']", html, re.IGNORECASE))
    if card_count >= 3:
        violations.append({
            "pattern": "three_cards_grid_template2018",
            "severity": "medium",
            "count": card_count,
            "sample": f"{card_count} feature-/value-/pricing-card detected",
            "fix": "Replace with prose narrative + UI screenshot alternance (Linear/Vercel pattern).",
        })

    # 9. Star rating fake ⭐ ⭐ ⭐ ⭐ ⭐ inline
    stars = re.findall(r"⭐\s*⭐\s*⭐", html)
    if stars:
        violations.append({
            "pattern": "fake_stars_inline",
            "severity": "high",
            "count": len(stars),
            "sample": "⭐⭐⭐ inline detected",
            "fix": "Use named testimonial with photo + position OR specific number (4.7/5 from 234 reviews).",
        })

    # 10. FOMO countdown timer
    countdown = re.findall(r"\b(?:countdown|timer|expires?-in|ends-in)\b[^>]*>\s*\d+\s*[hms:]", html, re.IGNORECASE)
    if countdown:
        violations.append({
            "pattern": "fomo_countdown_timer",
            "severity": "high",
            "count": len(countdown),
            "sample": countdown[0][:80],
            "fix": "Remove countdown — fake urgency = trust killer. Honest reassurance line instead.",
        })

    return violations


def _repair_ai_slop_visual_patterns(html: str, violations: list[dict]) -> tuple[str, list[str]]:
    """Sprint AD-6 — Tente d'auto-réparer certains patterns AI-slop.

    On NE répare QUE les patterns CSS sûrs (font-family déjà géré par AD-2).
    Pour les patterns structurels (3-cards grid, FOMO countdown), on flag mais
    on ne touche pas — c'est à Sonnet de les éviter en amont via les prompts.
    """
    import re
    repairs = []
    out = html

    for v in violations:
        if v["pattern"] == "gradient_135deg_avatar":
            # Replace `linear-gradient(135deg, A, B)` background sur avatar par color solid neutre
            # Heuristique : garde la couleur A, drop le gradient
            def replace_avatar_gradient(m):
                inner = m.group(0)
                # Extract first color
                color_match = re.search(r"#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)", inner)
                first_color = color_match.group(0) if color_match else "#1a1a1a"
                return first_color
            new_out = re.sub(r"linear-gradient\(\s*135deg[^)]+\)", replace_avatar_gradient, out)
            if new_out != out:
                out = new_out
                repairs.append(f"gradient_135deg_avatar: replaced {v['count']} gradient(s) by solid color")

        # rgba_gradient_box — replace by solid neutral
        if v["pattern"] == "rgba_gradient_box":
            new_out = re.sub(
                r"linear-gradient\([^)]*rgba?\s*\([^)]+\)[^)]*rgba?\s*\([^)]+\)[^)]*\)",
                "var(--color-surface, #f5f5f5)",
                out,
            )
            if new_out != out:
                out = new_out
                repairs.append(f"rgba_gradient_box: replaced {v['count']} rgba gradient(s) by solid surface var")

        # border_left_callout_blog2018 — replace by left padding only (cleaner)
        if v["pattern"] == "border_left_callout_blog2018":
            new_out = re.sub(
                r"border-left\s*:\s*\d+px\s+solid\s+var\(--[\w-]*(?:primary|accent|secondary)[\w-]*\)\s*;?",
                "padding-left: 1.5rem;",
                out,
            )
            if new_out != out:
                out = new_out
                repairs.append(f"border_left_callout: replaced colored border-left by padding-left")

    return out, repairs


_AI_SLOP_FONT_BLACKLIST = ["Inter", "Roboto", "Open Sans", "Lato", "Montserrat", "Poppins", "Nunito", "Helvetica"]


def _repair_ai_slop_fonts(
    html: str,
    *,
    target_display_font: Optional[str] = None,
    target_body_font: str = "DM Sans",
    target_body_alt_loadable: str = "DM Sans",
) -> tuple[str, list[str]]:
    """Sprint AD-2 V26.AD — garde-fou défensif post-gate : si Sonnet a dérivé
    et inclu Inter/Roboto/etc malgré le HARD CONSTRAINT, on rewrite UNIQUEMENT
    dans le CSS (font-family, --font-*, @font-face, Google Fonts URL).

    On ne touche JAMAIS au texte body (respect des "Internet", "Lateral", etc).

    Args:
      html: HTML produit par Sonnet
      target_display_font: font à utiliser pour h1/h2/h3 (ex: "Ppneuemontreal").
        Si None, fallback sur target_body_alt_loadable (DM Sans).
      target_body_font: font à utiliser pour body/p/li (ex: "DM Sans" — non-AI-slop).
      target_body_alt_loadable: fallback si target_display_font non chargeable
        depuis Google Fonts (ex: Ppneuemontreal commercial → DM Sans loaded).

    Returns: (html_repaired, list of repairs applied)
    """
    import re
    repairs = []
    out = html

    # 1. Google Fonts URLs : si family=Inter (ou autre AI-slop), substitute
    # On charge DM Sans qui est Google Fonts, garanti loadable.
    for slop in _AI_SLOP_FONT_BLACKLIST:
        slop_url = slop.replace(" ", "+")
        # match `family=Inter` or `family=Open+Sans` (with optional weight specs after `:`)
        pattern = rf"family={re.escape(slop_url)}(?=[\s\"&:'])"
        if re.search(pattern, out):
            out = re.sub(pattern, f"family={target_body_font.replace(' ', '+')}", out)
            repairs.append(f"google_fonts_url: family={slop} → family={target_body_font}")

    # 2. CSS custom properties --font-* : map AI-slop → display/body target
    # The display fonts go to --font-display, --font-heading, --font-h*
    # The body fonts go to --font-body, --font-text, --font-p
    for slop in _AI_SLOP_FONT_BLACKLIST:
        # --font-display: 'Inter' → --font-display: 'Ppneuemontreal'
        if target_display_font:
            for display_var in ["--font-display", "--font-heading", "--font-h1", "--font-h2", "--font-h3", "--font-title"]:
                pat = rf"({re.escape(display_var)}\s*:\s*['\"])({re.escape(slop)})(['\"])"
                if re.search(pat, out):
                    out = re.sub(pat, rf"\1{target_display_font}\3", out)
                    repairs.append(f"css_var: {display_var}: '{slop}' → '{target_display_font}'")
        # --font-body / --font-text → DM Sans
        for body_var in ["--font-body", "--font-text", "--font-p", "--font-base", "--font-accent"]:
            pat = rf"({re.escape(body_var)}\s*:\s*['\"])({re.escape(slop)})(['\"])"
            if re.search(pat, out):
                out = re.sub(pat, rf"\1{target_body_font}\3", out)
                repairs.append(f"css_var: {body_var}: '{slop}' → '{target_body_font}'")

    # 3. Direct font-family declarations: `font-family: 'Inter', ...` → DM Sans (body)
    # On ne sait pas si c'est display ou body, donc on prend body (safer for content)
    for slop in _AI_SLOP_FONT_BLACKLIST:
        pattern = rf"(font-family\s*:\s*['\"])({re.escape(slop)})(['\"])"
        if re.search(pattern, out):
            out = re.sub(pattern, rf"\1{target_body_font}\3", out)
            repairs.append(f"font-family: '{slop}' → '{target_body_font}'")

    # 4. @font-face url with AI-slop font (rare but possible)
    for slop in _AI_SLOP_FONT_BLACKLIST:
        pattern = rf"@font-face\s*\{{[^}}]*?font-family\s*:\s*['\"]({re.escape(slop)})['\"][^}}]*?\}}"
        if re.search(pattern, out, re.DOTALL):
            repairs.append(f"@font-face: {slop} block detected — left unchanged (safer)")

    return out, repairs


def _check_design_grammar_violations(html: str, design_grammar: Optional[dict]) -> list[str]:
    """Sprint F V26.AC — POST-GATE check : forbidden_patterns design_grammar."""
    if not design_grammar:
        return []
    forbid = design_grammar.get("forbidden") or {}
    if not forbid:
        return []
    patterns = forbid.get("patterns") or forbid.get("forbidden_patterns") or []
    violations = []
    html_lower = html.lower()
    for p in patterns[:10]:
        if isinstance(p, dict):
            rule = p.get("rule") or p.get("pattern") or ""
            check = p.get("html_check") or ""  # optional regex/keyword to detect
            if check and check.lower() in html_lower:
                violations.append(str(rule)[:100])
    return violations


def _extract_brand_font_family(brand_dna: dict) -> Optional[str]:
    """Extrait la famille typo principale du brand_dna pour injection POSITIVE."""
    typo = (brand_dna.get("visual_tokens") or {}).get("typography") or {}
    if not isinstance(typo, dict):
        return None
    h1 = typo.get("h1")
    if isinstance(h1, dict) and h1.get("family"):
        # On prend la 1ère famille (ex: "Ppneuemontreal, Arial, sans-serif" → "Ppneuemontreal")
        return h1["family"].split(",")[0].strip()
    return None


def build_persona_prompt(
    client: str,
    page_type: str,
    brief: dict,
    brand_dna: dict,
    ctx: Optional[ClientContext] = None,  # Sprint F V26.AC : ROUTER RACINE
    forced_language: Optional[str] = None,  # Sprint F.fix : "FR" / "EN" / etc — override Sonnet vision bias
    prompt_mode: str = "lite",  # V26.AE : "lite" (default, ≤8K) | "full" (debug, ≤17K)
    inject_golden_techniques: bool = True,  # Si True, ajoute le bloc golden refs (court en mode lite)
) -> tuple[str, str, list[dict]]:
    """Construit (system_prompt, user_message) pour Mode 1 Persona Narrator.

    V26.AE refactor — Anti-pattern #1 fix :
    - prompt_mode="lite" (default) : prompt ≤8K chars. Layout archetype + golden
      techniques en versions LITE (300-1200c chacun vs 4000-4500c). Détails
      structurels passés en POST-PROCESS GATES (anti-pattern #1).
    - prompt_mode="full" : versions FULL pour debug/comparaison empirique.
      Risque mega-prompt sursaturé prouvé empiriquement (-28pts régression).
    """
    founder_persona = build_founder_persona(client, brand_dna)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        founder_persona=founder_persona,
        format_intent=_format_intent_for_page_type(page_type),
        brand_voice_block=_format_brand_voice_block(brand_dna),
        brand_visual_block=_format_brand_visual_block(brand_dna),
        brand_forbid_block=_format_brand_forbid_block(brand_dna),
        client=client,
        page_type=page_type,
        brief_objectif=brief.get("objectif") or "(à toi de définir si pas spécifié)",
        brief_audience=brief.get("audience") or "(toi tu sais qui c'est, tu leur as parlé 1000 fois)",
        brief_angle=brief.get("angle") or "(propose ton meilleur angle pour ce format)",
    )

    # V26.AE : choix LITE vs FULL selon prompt_mode
    extra_blocks = []
    philosophy_refs: list[dict] = []

    # Archetype layout — LITE en default
    if prompt_mode == "lite":
        archetype_block = _format_layout_archetype_block_LITE(page_type)
    else:
        archetype_block = _format_layout_archetype_block(page_type)
    if archetype_block:
        extra_blocks.append(archetype_block)

    if ctx is not None:
        if ctx.aura_tokens:
            tokens_css = _load_tokens_css(ctx.client)  # design_grammar V30 CSS prêt
            aura_max = 1400 if prompt_mode == "lite" else 3500
            extra_blocks.append(_format_aura_tokens_block(ctx.aura_tokens, tokens_css=tokens_css, max_chars=aura_max))
            if inject_golden_techniques:
                if prompt_mode == "lite":
                    golden_block, philosophy_refs = _format_golden_techniques_block_LITE(ctx.aura_tokens, page_type)
                else:
                    golden_block, philosophy_refs = _format_golden_techniques_block(ctx.aura_tokens, page_type)
                if golden_block:
                    extra_blocks.append(golden_block)
        if ctx.has_v143_enrichment:
            v143_max = 700 if prompt_mode == "lite" else 1500
            extra_blocks.append(_format_v143_citations_block(ctx, max_chars=v143_max))
        if ctx.recos_final:
            recos_max = 500 if prompt_mode == "lite" else 1000
            extra_blocks.append(_format_recos_hint_block(ctx, max_chars=recos_max))
    extras_str = "\n".join([b for b in extra_blocks if b])
    if extras_str:
        system_prompt += "\n\n" + extras_str

    # Si screenshots disponibles → indiquer à Sonnet qu'il les voit en input.
    # Sprint AD-4 V26.AD+ : si philosophy_refs présents, expliquer que des golden refs
    # sont aussi en input vision (cross-cat inspirations niveau d'exécution).
    if ctx is not None and ctx.screenshots:
        vision_block = (
            "\n\n## ⚠️ IMPORTANT — TU REÇOIS DES IMAGES EN INPUT VISION\n"
            "**1ère et 2ème image** : screenshots desktop + mobile de TA marque réelle.\n"
            "  → respecte la palette, la typo, le ton brand. Mais tu n'es PAS obligé de copier "
            "le LAYOUT/STRUCTURE — celui-là on veut le upgrader.\n"
        )
        if philosophy_refs:
            ref_intro_lines = []
            for i, ref in enumerate(philosophy_refs[:2], start=3):
                site = ref.get("site", "?")
                sig = ref.get("signature", "")[:120]
                ref_intro_lines.append(
                    f"**{i}{'ème' if i == 3 else 'ème'} image** : {site.upper()} (golden ref) — {sig}"
                )
            vision_block += (
                "\n" + "\n".join(ref_intro_lines) + "\n"
                "  → ces refs définissent le NIVEAU D'EXÉCUTION VISUELLE attendu. Étudie leur "
                "rythme, leur signature distinctive, leurs techniques visuelles (drop caps, marginalia, "
                "hairline rules, pull quotes, type scale, depth, motion). Emprunte les TECHNIQUES, "
                "pas les styles. Fusionne dans ta propre signature.\n"
            )
        vision_block += (
            "\n**Règle d'or** : combine la palette/voix de TA marque (images 1-2) + le niveau "
            "d'exécution visuelle des golden refs (images 3+). Pas de copie. Une fusion qui crée TA signature."
        )
        system_prompt += vision_block

    # Sprint F.fix V26.AC : HARD CONSTRAINTS qui override la vision bias
    hard_constraints = []
    if forced_language:
        hard_constraints.append(
            f"## ⛔ LANGUE OBLIGATOIRE : {forced_language}\n"
            f"TOUTE la page DOIT être en {forced_language}. Tous les textes (H1, H2, body, CTA, "
            f"footer, alt texts). Si les screenshots sont dans une autre langue, IGNORE leur langue "
            f"— suis cette consigne. Le brief gagne sur ce que tu vois."
        )
    brand_font = _extract_brand_font_family(brand_dna) if brand_dna else None
    if brand_font:
        hard_constraints.append(
            f"## ⛔ TYPOGRAPHIE OBLIGATOIRE : '{brand_font}'\n"
            f"Utilise '{brand_font}' pour h1/h2/h3/body/CTA. Inter/Roboto/Arial/Open Sans/Lato/Montserrat/Poppins/Helvetica interdits. "
            f"Si la font n'est pas chargeable, garde `font-family: '{brand_font}', system-ui, sans-serif`."
        )
    if hard_constraints:
        system_prompt += "\n\n" + "\n\n".join(hard_constraints)

    user_message = (
        "Maintenant, écris cette page comme tu l'écrirais. "
        "Pas de checklist mentale. Pas de structure obligée par un template marketing. "
        "Que ce qui sort de ta conviction profonde — au format demandé ci-dessus. "
        "Si tu vois des screenshots de ta marque, INSPIRE-TOI de leur signature visuelle réelle."
    )
    return system_prompt, user_message, philosophy_refs


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Mode 1 Persona Narrator
# ─────────────────────────────────────────────────────────────────────────────

def run_mode_1_persona_narrator(
    client: str,
    page_type: str,
    brief: dict,
    *,
    fallback_page_for_vision: Optional[str] = None,  # Sprint F V26.AC : fallback screenshots si page demandée non capturée
    forced_language: Optional[str] = None,  # Sprint F.fix V26.AC : "FR"/"EN"/etc — override vision bias
    prompt_mode: str = "lite",  # V26.AE : "lite" (default ≤8K) | "full" (debug ≤17K)
    apply_fixes: bool = True,
    apply_post_gates: bool = True,  # Sprint F V26.AC : AURA font + design_grammar forbidden
    repair_visual_slop: bool = False,  # V26.AG rollback : visual gate report-only by default
    skip_judges: bool = True,
    save_html_path: str | None = None,
    save_audit_path: str | None = None,
    temperature: float = 0.85,
    max_tokens: int = 8000,
    verbose: bool = True,
) -> dict:
    """Pipeline Mode 1 Persona Narrator V26.AC Sprint F.

    PIVOT V26.AC : utilise le ROUTER RACINE `client_context` qui charge automatiquement
    TOUS les artefacts disponibles (brand_dna + AURA + screenshots + perception + recos
    + v143 + design_grammar + reality_layer + evidence). Plus jamais d'oubli.

    Args:
      client: slug
      page_type: ex "home", "lp_listicle"
      brief: dict {objectif, audience, angle}
      fallback_page_for_vision: si page_type pas capturé (ex: lp_listicle nouveau pour
        Weglot), utilise screenshots de cette page pour vision input (ex: "home").
      apply_post_gates: AURA font blacklist check + design_grammar forbidden check.
      temperature: 0.85 (vs 0.7 Mode 1 V26.AA)
      skip_judges: True default

    Returns: dict {html, gen, ctx_summary, post_gate_violations, telemetry}
    """
    if verbose:
        print(f"\n══ Mode 1 PERSONA NARRATOR V26.AC — {client} / {page_type} ══")

    grand_t0 = time.time()

    # ── 0. ROUTER RACINE — charge TOUT ce qui existe ──
    ctx = load_client_context(client, page_type)
    if not ctx.has_brand_dna:
        raise ValueError(f"❌ brand_dna manquant pour {client}")

    if verbose:
        print(f"  Router racine : {ctx.completeness_pct}% completeness ({len(ctx.available_artefacts)} artefacts)")
        print(f"    Available : {', '.join(ctx.available_artefacts[:8])}")
        if ctx.missing_artefacts:
            print(f"    Missing   : {', '.join(ctx.missing_artefacts[:6])}{' ...' if len(ctx.missing_artefacts) > 6 else ''}")

    # ── 1. Build prompt enrichi (router-aware + hard constraints + golden bridge AD-3) ──
    system_prompt, user_message, philosophy_refs = build_persona_prompt(
        client, page_type, brief, ctx.brand_dna, ctx=ctx,
        forced_language=forced_language, prompt_mode=prompt_mode,
    )
    if verbose:
        sz = len(system_prompt) + len(user_message)
        founder_used = client in KNOWN_FOUNDERS
        print(f"  Prompt : system={len(system_prompt)} user={len(user_message)} TOTAL={sz} chars [mode={prompt_mode}]")
        if sz > 8000 and prompt_mode == "lite":
            print(f"  ⚠️  ANTI-PATTERN #1 ALERT : prompt {sz} > 8K chars en mode lite (régression empirique -28pts)")
        elif sz > 12000:
            print(f"  ⚠️  Prompt {sz} chars très long — mega-prompt risque, prompt_mode={prompt_mode}")
        print(f"  Founder persona : {'hardcoded ⭐' if founder_used else 'extracted from brand_dna'}")
        if philosophy_refs:
            ref_names = [f"{r['site']}/{r['page']}" for r in philosophy_refs[:3]]
            print(f"  Golden refs (AD-3) : {len(philosophy_refs)} matches — top : {ref_names}")

    # ── 2. Sélection screenshots vision multimodal (client + AD-4 golden inspirations) ──
    vision_images = _select_vision_screenshots(
        ctx, fallback_page_for_vision, max_images=2,
        philosophy_refs=philosophy_refs, max_golden_inspirations=2,
    )
    if verbose:
        if vision_images:
            print(f"  Vision input : {len(vision_images)} screenshots — {[p.name for p in vision_images]}")
        else:
            print(f"  Vision input : ❌ aucun screenshot disponible (Sonnet code à l'aveugle)")

    # ── 3. Single-pass Sonnet MULTIMODAL ──
    if verbose:
        print(f"\n→ Sonnet single_pass MULTIMODAL (T={temperature}, max_tokens={max_tokens})...")
    if vision_images:
        gen = call_sonnet_multimodal(
            system_prompt, user_message, image_paths=vision_images,
            max_tokens=max_tokens, temperature=temperature, verbose=verbose,
        )
    else:
        gen = call_sonnet(
            system_prompt, user_message,
            max_tokens=max_tokens, temperature=temperature, verbose=verbose,
        )
    html_raw = gen["html"]

    # ── 4. fix_html_runtime auto ──
    if apply_fixes:
        html_fixed, fixes_info = apply_runtime_fixes(html_raw, verbose=verbose)
    else:
        html_fixed, fixes_info = html_raw, {"applied": False}

    # ── 4a. AUTO-REPAIR garde-fou défensif AI-slop fonts (Sprint AD-2 V26.AD) ──
    # Si Sonnet a dérivé (variance T=0.85) et a inclu Inter/Roboto/etc dans le CSS
    # malgré le HARD CONSTRAINT, on rewrite UNIQUEMENT les déclarations CSS
    # (font-family, --font-*, Google Fonts URL). Texte body intouché.
    repairs_applied: list[str] = []
    if apply_post_gates:
        target_display = _extract_brand_font_family(ctx.brand_dna) if ctx.brand_dna else None
        # Body fallback : DM Sans (loadable Google Fonts, non-AI-slop)
        html_fixed, repairs_applied = _repair_ai_slop_fonts(
            html_fixed,
            target_display_font=target_display,
            target_body_font="DM Sans",
        )
        if verbose:
            if repairs_applied:
                print(f"  🔧 AUTO-REPAIR fonts: {len(repairs_applied)} substitution(s)")
                for r in repairs_applied[:5]:
                    print(f"     - {r}")
            else:
                print(f"  ✓ AUTO-REPAIR fonts : 0 substitution nécessaire")

    # ── 4a-bis. SPRINT AD-6 — Anti-AI-slop visuel patterns ──
    # V26.AG rollback: report-only by default. The V26.AF aggressive repair path
    # removed too much depth and produced "anti-design" white pages empirically.
    visual_slop_violations: list[dict] = []
    visual_slop_repairs: list[str] = []
    if apply_post_gates:
        visual_slop_violations = _check_ai_slop_visual_patterns(html_fixed)
        if visual_slop_violations:
            if verbose:
                print(f"  ⚠️ AI-slop visual patterns détectés : {len(visual_slop_violations)}")
                for v in visual_slop_violations[:5]:
                    print(f"     - {v['pattern']} (severity={v['severity']}, count={v['count']})")
            if repair_visual_slop:
                html_fixed, visual_slop_repairs = _repair_ai_slop_visual_patterns(html_fixed, visual_slop_violations)
                if verbose and visual_slop_repairs:
                    print(f"  🔧 Auto-repaired : {len(visual_slop_repairs)} pattern(s)")
                    for r in visual_slop_repairs:
                        print(f"     - {r}")
                # Re-check post-repair
                remaining = _check_ai_slop_visual_patterns(html_fixed)
                if verbose and remaining:
                    print(f"  ⚠️ Patterns restants après repair (structurels, à refondre) : {len(remaining)}")
                    for v in remaining[:3]:
                        print(f"     - {v['pattern']} : {v['fix']}")
            elif verbose:
                print("  ↳ report-only (repair_visual_slop=True pour l'ancien repair agressif)")
        else:
            if verbose:
                print(f"  ✓ AI-slop visual patterns : 0 détection")

    # ── 4b. POST-GATES (AURA font blacklist + design_grammar forbidden) ──
    post_gate_violations = {"aura_font": [], "design_grammar": [], "ai_slop_visual": visual_slop_violations}
    if apply_post_gates:
        post_gate_violations["aura_font"] = _check_aura_font_violations(html_fixed)
        post_gate_violations["design_grammar"] = _check_design_grammar_violations(html_fixed, ctx.design_grammar)
        # ai_slop_visual already populated above (re-check post-repair)
        post_gate_violations["ai_slop_visual"] = _check_ai_slop_visual_patterns(html_fixed)
        if verbose:
            if post_gate_violations["aura_font"]:
                print(f"  ⚠️ AURA font blacklist VIOLATIONS post-repair : {post_gate_violations['aura_font']}")
            else:
                print(f"  ✓ AURA font blacklist : OK (post-repair)")
            if post_gate_violations["design_grammar"]:
                print(f"  ⚠️ design_grammar VIOLATIONS : {post_gate_violations['design_grammar']}")
            else:
                print(f"  ✓ design_grammar forbidden patterns : OK")

    # ── 4. Save HTML ──
    if save_html_path:
        out_html = pathlib.Path(save_html_path)
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html_fixed)
        if verbose:
            print(f"\n  ✓ HTML saved : {out_html.relative_to(ROOT) if out_html.is_relative_to(ROOT) else out_html}")

    # ── 5. (Optionnel) doctrine_judge en POST-PROCESS GATE info-only ──
    audit: dict = {}
    if not skip_judges:
        if verbose:
            print(f"\n→ doctrine_judge V3.2.1 GATE (info only, NE bloque PAS la livraison)...")
        from moteur_multi_judge.judges.doctrine_judge import audit_lp_doctrine
        audit = audit_lp_doctrine(html_fixed, client, page_type, verbose=verbose, parallel=True)
        if save_audit_path:
            pathlib.Path(save_audit_path).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(save_audit_path).write_text(json.dumps(audit, ensure_ascii=False, indent=2))

    grand_dt = time.time() - grand_t0

    cost = (gen["tokens_in"] / 1e6 * 3) + (gen["tokens_out"] / 1e6 * 15)
    telemetry = {
        "wall_seconds_total": round(grand_dt, 1),
        "wall_seconds_gen": gen["wall_seconds"],
        "tokens_in": gen["tokens_in"],
        "tokens_out": gen["tokens_out"],
        "cost_estimate_usd": round(cost, 3),
    }

    if verbose:
        print(f"\n══ Mode 1 PERSONA NARRATOR — DONE ══")
        print(f"  Wall total      : {telemetry['wall_seconds_total']}s")
        print(f"  Coût estimé     : ${telemetry['cost_estimate_usd']}")
        print(f"  HTML chars      : {len(html_fixed)}")
        if audit:
            t = audit.get("totals", {})
            print(f"  Doctrine score  : {t.get('total_pct','?')}% (info only — pas blocking)")

    return {
        "html": html_fixed,
        "html_raw": html_raw,
        "gen": gen,
        # API stability alias — caller can do result["audit"] across all modes (Sprint AD-1).
        "audit": audit,
        "audit_doctrine_info_only": audit,
        "fixes": fixes_info,
        "font_repairs_applied": repairs_applied,  # Sprint AD-2 V26.AD garde-fou
        "post_gate_violations": post_gate_violations,
        "ctx_summary": {
            "completeness_pct": ctx.completeness_pct,
            "n_available_artefacts": len(ctx.available_artefacts),
            "available": ctx.available_artefacts,
            "missing": ctx.missing_artefacts,
            "n_vision_images_used": gen.get("n_images", 0),
        },
        "founder_persona_used": KNOWN_FOUNDERS.get(client, "extracted_from_brand_dna"),
        "telemetry": telemetry,
        "client": client,
        "page_type": page_type,
        "brief": brief,
        "mode": "persona_narrator",
        "version": "V26.AD.sprint_ad1",
    }
