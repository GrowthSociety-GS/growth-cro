"""Prompt assembly entry point for Mode 1 PERSONA NARRATOR.

Single concern: take ``client``, ``page_type``, ``brief``, ``brand_dna``
(+ optional ``ctx`` from the V26.AC ROUTER RACINE) and produce
``(system_messages, user_turns_seq, philosophy_refs)`` ready for Sonnet
via the Anthropic SDK with native prompt caching.

──────────────────────────────────────────────────────────────────────
Issue #13 — V26.AG prompt architecture (2026-05-11)
──────────────────────────────────────────────────────────────────────
The legacy ``(system_prompt, user_message)`` monolithic shape — and the
quarantined ``prompt_mode='full'`` path that produced 13K+ char system
prompts (anti-pattern #1, -28pts régression V26.AA) — are GONE.

The new architecture splits the prompt across three Anthropic SDK
surfaces, all rendered into a single Sonnet call:

  1. ``system_messages`` : list of ``{type, text, cache_control}`` blocks.
     Static blocks (persona frame, doctrine, format rules) are marked
     ``cache_control: ephemeral`` so subsequent runs hit the prefix cache
     at ~1/10th input-token cost. Each block ≤ 4K chars; total ≤ 8K hard.

  2. ``user_turns_seq`` : pre-filled multi-turn dialogue (brand DNA →
     synthesis checkpoint → golden refs → synthesis checkpoint → recos
     → synthesis checkpoint). Each turn ≤ 2K chars. Sonnet's attention
     handles dialogue history better than monolithic system prompts.

  3. Final ``user`` turn (built by the caller, e.g. ``api_call``): the
     generation kickoff "Maintenant, écris cette page…".

The V26.AF 8K hard limit stays enforced defensively — each individual
text block and the cumulative ``system_messages`` are checked before
return. Empirical regression -28pts (CLAUDE.md anti-pattern #1).

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
    _format_golden_techniques_block_LITE,
    _format_intent_for_page_type,
    _format_layout_archetype_block_LITE,
    _format_recos_hint_block,
    _format_v143_citations_block,
    _load_tokens_css,
)
from .runtime_fixes import _extract_brand_font_family
from .vision_selection import ClientContext


# ─────────────────────────────────────────────────────────────────────
# Hard limits (V26.AF doctrine — defensively enforced post-refactor)
# ─────────────────────────────────────────────────────────────────────

MAX_SYSTEM_BLOCK_CHARS = 4096  # individual text block ≤ 4K (safety margin)
MAX_SYSTEM_TOTAL_CHARS = 8192  # all system blocks combined ≤ 8K (V26.AF doctrine)
MAX_USER_TURN_CHARS = 2048     # each pre-filled user/assistant turn ≤ 2K


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
        "Tu connais ton produit jusque dans la moelle parce que tu l'as conçu "
        "pour résoudre une frustration que tu vivais toi-même. Tu écris cette "
        "page comme un manifeste personnel sur ce que tu construis et pourquoi "
        "ça compte."
    )
    return persona


# ─────────────────────────────────────────────────────────────────────
# STATIC system blocks (cached via cache_control: ephemeral)
# ─────────────────────────────────────────────────────────────────────

# Block 1 — Persona frame + role + renouncement (STATIC, cached).
#   Founder persona is interpolated per-client at the top, but the rest is
#   identical across every GSG run for that client → caches per-client.
#   Total ≤ ~2K chars (well under the 4K per-block ceiling).
PERSONA_FRAME_TEMPLATE = """{founder_persona}

## TON RÔLE

Tu écris cette page comme TU l'écrirais à 3h du matin, dans ton garage, à un ami qui te demande pourquoi ton produit existe.

## RÈGLE DE RENONCEMENT (la plus importante)

Si tu n'as pas une CONVICTION PROFONDE pour justifier un mot, **NE L'ÉCRIS PAS**.

INTERDIT de mettre du creux :
- Pas de claim chiffré sans source vérifiée dans ton brand DNA
- Pas de "leader du marché", "the best", "innovant" sans preuve
- Pas de verbes vides : "découvrez", "explorez", "transformez", "boostez", "optimisez"
- Pas de testimonial inventé ("Sarah, 32 ans, marketing manager")
- Pas de chiffres ronds inventés (+50%, +127%, etc.) — seulement ceux que tu as VRAIMENT mesurés
- Pas d'icônes checkmark systématiques (✓✓✓ = AI showcase)

Si une section serait creuse → **omets-la**. Une page courte avec 100% de conviction bat une page longue avec 50% de bullshit."""


# Block 2 — Format + page-type intent (STATIC per page_type, cached).
#   Identical across every run on the same page_type. ~700 chars.
FORMAT_DOCTRINE_TEMPLATE = """## FORMAT DE CETTE PAGE — `{page_type}`

{format_intent}

## FORMAT DE SORTIE (HTML autocontenu mobile-first)

- Sortie commence par `<!DOCTYPE html>` et finit par `</html>`
- Pas de markdown wrapper, pas de commentaires hors HTML
- Sémantique correcte (`<header>`, `<main>`, `<section>`, `<footer>`)
- Mobile-first (375px) puis desktop (1440px)
- Une seule balise `<h1>`
- Aucune dépendance externe (Google Fonts via `<link>` accepté, mais pas d'images sur CDN tiers)
- Pas de stock photo lifestyle. Pas de SVG décoratif. Si tu mets un visuel, c'est un produit en usage RÉEL ou un schéma qui clarifie ta conviction."""


# ─────────────────────────────────────────────────────────────────────
# Helpers — block construction + safety enforcement
# ─────────────────────────────────────────────────────────────────────

def _system_block(text: str, *, cached: bool = True) -> dict:
    """Build a single system content block.

    Trims to MAX_SYSTEM_BLOCK_CHARS defensively and attaches
    ``cache_control: ephemeral`` when ``cached=True`` (static prefix
    content). Dynamic per-request blocks (e.g. hard language constraint)
    set ``cached=False`` and sit AFTER the last cached block in the
    rendered prefix.
    """
    text = text.strip()
    if len(text) > MAX_SYSTEM_BLOCK_CHARS:
        text = text[:MAX_SYSTEM_BLOCK_CHARS - 24] + "\n[...] (block trimmed)"
    block: dict = {"type": "text", "text": text}
    if cached:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def _user_turn(text: str) -> dict:
    """Build a pre-filled user turn (≤ MAX_USER_TURN_CHARS)."""
    text = text.strip()
    if len(text) > MAX_USER_TURN_CHARS:
        text = text[:MAX_USER_TURN_CHARS - 24] + "\n[...] (turn trimmed)"
    return {"role": "user", "content": text}


def _assistant_turn(text: str) -> dict:
    """Build a pre-filled assistant checkpoint turn (≤ MAX_USER_TURN_CHARS)."""
    text = text.strip()
    if len(text) > MAX_USER_TURN_CHARS:
        text = text[:MAX_USER_TURN_CHARS - 24] + "\n[...] (turn trimmed)"
    return {"role": "assistant", "content": text}


def _voice_synthesis(brand_dna: dict) -> str:
    """One-line synthesis the assistant 'checkpoints' after seeing brand DNA."""
    voice = brand_dna.get("voice_tokens", {}) or {}
    sig = voice.get("voice_signature_phrase") or "?"
    tone_raw = voice.get("tone")
    tone = ", ".join(tone_raw) if isinstance(tone_raw, list) else (tone_raw or "?")
    return (
        f"Compris. Signature : « {sig} ». Ton : {tone}. "
        f"J'écrirai avec cette voix, en respectant ses mots et ses interdits."
    )


def _golden_synthesis(philosophy_refs: list[dict]) -> str:
    """Assistant synthesis after seeing golden refs block."""
    if not philosophy_refs:
        return "Compris. Je m'appuierai sur ma signature visuelle propre."
    sites = ", ".join(r.get("site", "?").upper() for r in philosophy_refs[:3])
    return (
        f"Compris. Refs proches d'ADN : {sites}. J'emprunte leurs TECHNIQUES "
        f"(rythme, hairlines, drop caps, pull quotes) sans copier leurs styles."
    )


def _recos_synthesis(has_recos: bool) -> str:
    if not has_recos:
        return "Compris. Pas de backlog audit — j'écris depuis ma seule conviction."
    return (
        "Compris. Je prioriserai les gaps P0 ci-dessus dans le copy et la "
        "structure, sans les nommer explicitement comme une checklist."
    )


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
    inject_golden_techniques: bool = True,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Build (system_messages, user_turns_seq, philosophy_refs) for Mode 1 PERSONA NARRATOR.

    Issue #13 — V26.AG prompt architecture:

    Returns three values:

      * ``system_messages`` : list of ``{type, text, cache_control}`` blocks
        ready to pass as ``system=...`` to Anthropic SDK ``messages.create``.
        Static blocks (persona, format doctrine) carry
        ``cache_control: ephemeral``; dynamic per-request blocks (hard
        language / font constraints) sit AFTER the last cached block.
        Each block ≤ ``MAX_SYSTEM_BLOCK_CHARS`` (4K). Total ≤
        ``MAX_SYSTEM_TOTAL_CHARS`` (8K — V26.AF doctrine, defensively
        enforced post-refactor).

      * ``user_turns_seq`` : pre-filled multi-turn dialogue
        ``[{role, content}, ...]`` checkpointing the assistant's
        understanding between contextual chunks (brand DNA → golden refs
        → recos backlog). Pass as the leading entries of ``messages=...``;
        the caller appends the final generation kickoff turn.

      * ``philosophy_refs`` : the same shape as before (used by
        ``_select_vision_screenshots`` to add golden screenshots to the
        vision input).

    No ``prompt_mode`` parameter — the quarantined 'full' path is deleted.
    """
    # ── 1. STATIC system blocks (cached) ───────────────────────────────
    founder_persona = build_founder_persona(client, brand_dna)
    persona_block_text = PERSONA_FRAME_TEMPLATE.format(founder_persona=founder_persona)

    format_block_text = FORMAT_DOCTRINE_TEMPLATE.format(
        page_type=page_type,
        format_intent=_format_intent_for_page_type(page_type),
    )

    system_messages: list[dict] = [
        _system_block(persona_block_text, cached=True),
        _system_block(format_block_text, cached=True),
    ]

    # ── 2. DYNAMIC system constraints (NOT cached — per-request) ───────
    # These sit after the last cached block so they invalidate ONLY
    # themselves, not the static prefix.
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
            f"Utilise '{brand_font}' pour h1/h2/h3/body/CTA. "
            f"Inter/Roboto/Arial/Open Sans/Lato/Montserrat/Poppins/Helvetica interdits. "
            f"Si la font n'est pas chargeable, garde `font-family: '{brand_font}', system-ui, sans-serif`."
        )
    if hard_constraints:
        system_messages.append(_system_block("\n\n".join(hard_constraints), cached=False))

    # ── 3. Vision context block (NOT cached — depends on philosophy_refs) ─
    # We need to compute philosophy_refs first (used by both the user-turn
    # dialogue AND the vision context block).
    philosophy_refs: list[dict] = []
    user_turns_seq: list[dict] = []

    # ── 4. USER TURN 1 — Brand DNA (voice/visual/forbidden) ─────────────
    brand_voice = _format_brand_voice_block(brand_dna)
    brand_visual = _format_brand_visual_block(brand_dna)
    brand_forbid = _format_brand_forbid_block(brand_dna)
    brand_user_text = (
        f"Voici la brand DNA de {client} (extraite de son site réel — pas inventée).\n\n"
        f"### Voix\n{brand_voice}\n\n"
        f"### Couleurs (palette réelle)\n{brand_visual}\n\n"
        f"### Patterns visuels INTERDITS (anti-marque)\n{brand_forbid}"
    )
    user_turns_seq.append(_user_turn(brand_user_text))
    user_turns_seq.append(_assistant_turn(_voice_synthesis(brand_dna)))

    # ── 5. USER TURN 2 — Layout archetype + AURA design tokens + golden refs ──
    layout_block = _format_layout_archetype_block_LITE(page_type)
    aura_block = ""
    golden_block = ""
    if ctx is not None and ctx.aura_tokens:
        tokens_css = _load_tokens_css(ctx.client)
        aura_block = _format_aura_tokens_block(ctx.aura_tokens, tokens_css=tokens_css, max_chars=1400)
        if inject_golden_techniques:
            golden_block, philosophy_refs = _format_golden_techniques_block_LITE(
                ctx.aura_tokens, page_type
            )

    design_parts = [p for p in (layout_block, aura_block, golden_block) if p]
    if design_parts:
        design_user_text = (
            f"Voici les contraintes de DESIGN pour cette page ({page_type}) — "
            f"layout, design tokens et golden refs.\n\n" + "\n\n".join(design_parts)
        )
        user_turns_seq.append(_user_turn(design_user_text))
        user_turns_seq.append(_assistant_turn(_golden_synthesis(philosophy_refs)))

    # ── 6. USER TURN 3 — v143 verified citations (founder bio + VoC) ──
    if ctx is not None and ctx.has_v143_enrichment:
        v143_block = _format_v143_citations_block(ctx, max_chars=900)
        if v143_block:
            user_turns_seq.append(_user_turn(
                "Voici les citations VÉRIFIÉES (v143 — utilise UNIQUEMENT ces faits, "
                "pas d'inventions).\n\n" + v143_block
            ))
            user_turns_seq.append(_assistant_turn(
                "Compris. J'utiliserai uniquement ces faits / verbatims / preuves vérifiés. "
                "Aucune invention."
            ))

    # ── 7. USER TURN 4 — Recos backlog (gaps audit P0) ─────────────────
    has_recos = ctx is not None and bool(ctx.recos_final)
    if has_recos:
        recos_block = _format_recos_hint_block(ctx, max_chars=900)
        if recos_block:
            user_turns_seq.append(_user_turn(
                "Voici les gaps audit P0 identifiés pour ce client — "
                "à corriger en priorité dans le copy et la structure (sans les nommer "
                "explicitement comme une checklist).\n\n" + recos_block
            ))
            user_turns_seq.append(_assistant_turn(_recos_synthesis(True)))

    # ── 8. Vision input note + brief — appended as the LAST static system block
    # if vision/refs apply. Vision availability depends on ``ctx.screenshots``
    # (orchestrator passes the same ctx), so we add a generic input-hint block
    # ONLY when ctx hints we have screenshots. This block stays dynamic
    # (not cached) because philosophy_refs differ per-run.
    if ctx is not None and getattr(ctx, "screenshots", None):
        vision_block_text = (
            "## ⚠️ TU REÇOIS DES IMAGES EN INPUT VISION\n"
            "**1ère et 2ème image** : screenshots desktop + mobile de TA marque réelle.\n"
            "  → respecte la palette, la typo, le ton brand. Mais tu n'es PAS obligé de "
            "copier le LAYOUT/STRUCTURE — celui-là on veut le upgrader.\n"
        )
        if philosophy_refs:
            ref_lines = []
            for i, ref in enumerate(philosophy_refs[:2], start=3):
                site = ref.get("site", "?")
                sig = (ref.get("signature") or "")[:120]
                ref_lines.append(f"**{i}ème image** : {site.upper()} (golden ref) — {sig}")
            vision_block_text += (
                "\n" + "\n".join(ref_lines) + "\n"
                "  → ces refs définissent le NIVEAU D'EXÉCUTION VISUELLE attendu. "
                "Étudie leur rythme, leurs techniques (drop caps, marginalia, hairline "
                "rules, pull quotes, type scale, depth). Emprunte les TECHNIQUES, "
                "pas les styles. Fusionne dans ta propre signature.\n"
            )
        vision_block_text += (
            "\n**Règle d'or** : combine la palette/voix de TA marque (images 1-2) + le "
            "niveau d'exécution des golden refs (images 3+). Pas de copie. Une fusion qui crée TA signature."
        )
        system_messages.append(_system_block(vision_block_text, cached=False))

    # ── 9. FINAL user turn (mission concrète) — appended to user_turns_seq ──
    audience_default = "(toi tu sais qui c'est, tu leur as parlé 1000 fois)"
    angle_default = "(propose ton meilleur angle pour ce format)"
    objectif_default = "(à toi de définir si pas spécifié)"
    mission_text = (
        f"Mission concrète. Page : **{page_type}** pour **{client}**.\n\n"
        f"Brief client :\n"
        f"- **Objectif business** : {brief.get('objectif') or objectif_default}\n"
        f"- **Audience cible** : {brief.get('audience') or audience_default}\n"
        f"- **Hook / angle éditorial** : {brief.get('angle') or angle_default}\n\n"
        f"Maintenant, écris cette page comme TU l'écrirais. Pas de checklist mentale. "
        f"Pas de structure obligée par un template marketing. Que ce qui sort de ta conviction profonde — "
        f"au format demandé. Si tu vois des screenshots de ta marque, INSPIRE-TOI de leur signature "
        f"visuelle réelle.\n\n"
        f"Si à un moment tu sens que tu vas mettre du bullshit pour « remplir une section », "
        f"arrête-toi et trouve la conviction profonde qui justifie cette section, ou supprime-la."
    )
    user_turns_seq.append(_user_turn(mission_text))

    # ── 10. V26.AF DOCTRINE — defensive enforcement ─────────────────────
    # Each block ≤ MAX_SYSTEM_BLOCK_CHARS already trimmed by _system_block.
    # Verify cumulative system size + per-turn size before returning.
    total_system_chars = sum(len(b["text"]) for b in system_messages)
    assert total_system_chars <= MAX_SYSTEM_TOTAL_CHARS, (
        f"V26.AF doctrine — combined system_messages {total_system_chars} > "
        f"{MAX_SYSTEM_TOTAL_CHARS} chars. Empirical regression -28pts. "
        f"See .claude/epics/codebase-cleanup/follow-ups/issue-13-prompt-architecture.md"
    )
    for i, block in enumerate(system_messages):
        assert len(block["text"]) <= MAX_SYSTEM_BLOCK_CHARS, (
            f"system_messages[{i}] = {len(block['text'])} > {MAX_SYSTEM_BLOCK_CHARS} chars"
        )
    for i, turn in enumerate(user_turns_seq):
        assert len(turn["content"]) <= MAX_USER_TURN_CHARS, (
            f"user_turns_seq[{i}] ({turn['role']}) = {len(turn['content'])} > "
            f"{MAX_USER_TURN_CHARS} chars"
        )

    return system_messages, user_turns_seq, philosophy_refs


# Legacy alias — old call sites used `build_persona_prompt`. Kept for
# the shim layer; new code should import build_persona_narrator_prompt.
build_persona_prompt = build_persona_narrator_prompt


__all__ = [
    "KNOWN_FOUNDERS",
    "MAX_SYSTEM_BLOCK_CHARS",
    "MAX_SYSTEM_TOTAL_CHARS",
    "MAX_USER_TURN_CHARS",
    "PERSONA_FRAME_TEMPLATE",
    "FORMAT_DOCTRINE_TEMPLATE",
    "build_founder_persona",
    "build_persona_narrator_prompt",
    "build_persona_prompt",
]
