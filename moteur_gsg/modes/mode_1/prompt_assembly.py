"""Prompt assembly entry point for Mode 1 PERSONA NARRATOR.

Single concern: take ``client``, ``page_type``, ``brief``, ``brand_dna``
(+ optional ``ctx`` from the V26.AC ROUTER RACINE) and produce
``(system_prompt, user_message, philosophy_refs)`` ready for Sonnet.

**V26.AF non-negotiable**: the assembled ``system_prompt`` is asserted
``≤ 8 192 chars`` before return. The legacy ``prompt_mode='full'``
path stays in code (so the empirical comparison artefact is preserved
for issue #13's prompt-architecture spec) but **fails the assert at
runtime** — regression -28pts on persona_narrator quality (CLAUDE.md
anti-pattern #1).

The ``KNOWN_FOUNDERS`` registry is intentionally hardcoded here for the
6 curated V26 clients (Mathis decision 2026-05-10 — migrate to
``data/persona/founders.json`` once we cross 10+ founders).
"""
from __future__ import annotations

from typing import Optional

from .prompt_blocks import (
    _format_aura_tokens_block,
    _format_brand_forbid_block,
    _format_brand_visual_block,
    _format_brand_voice_block,
    _format_golden_techniques_block,
    _format_golden_techniques_block_LITE,
    _format_intent_for_page_type,
    _format_layout_archetype_block,
    _format_layout_archetype_block_LITE,
    _format_recos_hint_block,
    _format_v143_citations_block,
    _load_tokens_css,
)
from .runtime_fixes import _extract_brand_font_family
from .vision_selection import ClientContext


# ─────────────────────────────────────────────────────────────────────
# Founders connus — hardcoded pour clients curatés V26
# ─────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────
# Prompt template (court, mission "incarne", pas checklist)
# ─────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────
# Public assembly entrypoint
# ─────────────────────────────────────────────────────────────────────

def build_persona_narrator_prompt(
    client: str,
    page_type: str,
    brief: dict,
    brand_dna: dict,
    ctx: Optional[ClientContext] = None,  # Sprint F V26.AC : ROUTER RACINE
    forced_language: Optional[str] = None,  # Sprint F.fix : "FR" / "EN" / etc — override Sonnet vision bias
    prompt_mode: str = "lite",  # V26.AE : "lite" (default, ≤8K) | "full" (debug, ≤17K)
    inject_golden_techniques: bool = True,  # Si True, ajoute le bloc golden refs (court en mode lite)
) -> tuple[str, str, list[dict]]:
    """Construit (system_prompt, user_message, philosophy_refs) pour Mode 1 PERSONA NARRATOR.

    V26.AE refactor — Anti-pattern #1 fix :
    - prompt_mode="lite" (default) : prompt ≤ 8 192 chars. Layout archetype + golden
      techniques en versions LITE (300-1200c chacun vs 4000-4500c). Détails
      structurels passés en POST-PROCESS GATES (anti-pattern #1).
    - prompt_mode="full" : versions FULL pour debug/comparaison empirique.
      ⚠️ V26.AF QUARANTAINE — fait crasher l'assert ci-dessous (régression
      empirique -28pts prouvée). Le path reste dans le code pour préserver
      l'intent (issue #13 traitera la vraie solution prompt-caching +
      user-turns structurés). NE PAS APPELER en prod.
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
    extra_blocks: list[str] = []
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
    hard_constraints: list[str] = []
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

    # ─────────────────────────────────────────────────────────────────
    # V26.AF DOCTRINE — non-negotiable hard limit
    # ─────────────────────────────────────────────────────────────────
    # Anti-pattern #1 prouvé empiriquement (-28 pts régression V26.AA).
    # Le path prompt_mode='full' produit ~13 K chars et viole ce gate par
    # design — c'est une QUARANTAINE volontaire (Mathis decision
    # 2026-05-10), pas un kill, pour préserver l'artefact de comparaison
    # côté issue #13 (vraie solution = prompt caching + user-turns
    # structurés).
    assert len(system_prompt) <= 8192, (
        f"V26.AF doctrine — persona_narrator prompt {len(system_prompt)} > 8192 chars. "
        f"Empirical regression -28pts. See .claude/epics/codebase-cleanup/follow-ups/issue-13-prompt-architecture.md"
    )
    return system_prompt, user_message, philosophy_refs


# Legacy alias — old call sites used `build_persona_prompt`. Kept for
# the shim layer; new code should import build_persona_narrator_prompt.
build_persona_prompt = build_persona_narrator_prompt


__all__ = [
    "KNOWN_FOUNDERS",
    "SYSTEM_PROMPT_TEMPLATE",
    "build_founder_persona",
    "build_persona_narrator_prompt",
    "build_persona_prompt",
]
