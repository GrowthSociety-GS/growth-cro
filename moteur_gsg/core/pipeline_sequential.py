"""moteur_gsg.core.pipeline_sequential — V26.AF Sprint AF-1.B.2.

Pipeline 4 stages séquentiels (Strategy → Copy → Composer → Polish) qui remplace
le single_pass V26.AC/AD/AE plafonnant à 46/80 humanlike sur Weglot.

Approche : chaque stage = 1 prompt court (~2-3K chars) avec UN focus.
Anti-pattern #1 (mega-prompt sursaturé) évité par construction.

Stages :
  1. STRATEGY  — décide structure de page depuis archetype + brief + brand_dna
                 → output JSON {layout_plan, sections, key_proofs, hook}
  2. COPY      — persona narrator V26.AC incarne founder, écrit le contenu
                 → output JSON {h1, dek, intro, reasons[], cta_final, byline, pull_quotes}
  3. COMPOSER  — compose HTML structuré avec AURA CSS injecté + golden techniques
                 → output HTML brut
  4. POLISH    — raffine le HTML (typo strict, hard constraints langue/font, anti-slop visuel)
                 → output HTML final + post-gates

Coût attendu : ~$0.50-0.80 (4 calls Sonnet × ~10K input + 2K output / call).
Wall : ~3-5 min (séquentiel, vs 2 min single_pass mais qualité mieux).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from client_context import ClientContext  # noqa: E402
from doctrine import (  # noqa: E402 — V26.AF FIX 1 : brancher doctrine V3.2.1 racine partagée
    top_critical_for_page_type,
    killer_rules_for_page_type,
    render_doctrine_for_gsg,
    criterion_to_gsg_principle,
)

from .brief_v2 import BriefV2
from .pipeline_single_pass import call_sonnet, call_sonnet_multimodal, apply_runtime_fixes


def _format_doctrine_block(page_type: str, n_critical: int = 7, max_chars: int = 2500) -> str:
    """V26.AF FIX 1 — Charge doctrine V3.2.1 (top critères + killer rules) pour ce page_type.

    Renvoie un block prescriptif court (≤2.5K chars) à injecter dans Stage 1 STRATEGY
    + Stage 2 COPY. Format : principes constructifs (pas checklist).
    """
    try:
        block = render_doctrine_for_gsg(page_type, n_critical=n_critical)
        return block[:max_chars] if len(block) > max_chars else block
    except Exception as e:
        return f"(doctrine load error: {e})"


def _format_killer_rules_block(page_type: str, max_chars: int = 800) -> str:
    """V26.AF FIX 1 — Killer rules absolues pour ce page_type (caps score si violé)."""
    try:
        killers = killer_rules_for_page_type(page_type)
        if not killers:
            return ""
        parts = ["## ⛔ KILLER RULES (absolues — violer = LP refusée)"]
        for k in killers[:6]:
            parts.append(f"  - **{k.get('id', '?')}** : {k.get('rule', k.get('description', '?'))[:200]}")
        return "\n".join(parts)[:max_chars]
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — STRATEGY (planning structure)
# ─────────────────────────────────────────────────────────────────────────────

STRATEGY_PROMPT_TEMPLATE = """Tu es Strategy Director pour une LP haute-performance.

## Mission
Décide la STRUCTURE de la page (sections + ordre + proofs prioritaires) avant qu'on écrive le copy.

## Inputs

**Page type** : {page_type}
**Format intent** : {format_intent}

**Brief client** :
- Objectif business : {brief_objective}
- Audience : {brief_audience}
- Angle éditorial : {brief_angle}
- Traffic source : {traffic_source} / Visitor mode : {visitor_mode}

**Brand context** :
- Signature voix : « {brand_signature} »
- Archetype : {brand_archetype}

**Layout archétype prescrit** ({page_type}) :
{archetype_summary}

**Proofs disponibles** :
{available_proofs}

**Sourced numbers (anti-invention)** :
{sourced_numbers}

{doctrine_block}

{killer_rules_block}

## Tâche

Produis UN JSON strict (rien d'autre) :
```json
{{
  "layout_plan": "1 phrase qui résume la stratégie de page",
  "sections": [
    {{"name": "byline", "purpose": "...", "max_words": 30}},
    {{"name": "hero", "purpose": "...", "max_words": 80}},
    ...
  ],
  "key_proofs_to_use": ["sourced number 1", "verbatim 2", ...],
  "hook_concept": "1 phrase — la promesse / accroche éditoriale unique"
}}
```

Règles :
- 5-10 sections max (qualité > exhaustivité)
- Chaque section a un PURPOSE clair (pas "feature card 1")
- Sections respectent l'archétype prescrit (pas de cards 3-cols si archétype dit "éditorial")
- key_proofs_to_use : MAX 3-5 — les plus crédibles
- hook_concept : 1 phrase qui peut servir de pitch elevator interne
"""


def stage_1_strategy(
    brief: BriefV2,
    ctx: ClientContext,
    archetype_summary: str,
    format_intent: str,
    *,
    temperature: float = 0.4,
    verbose: bool = True,
) -> tuple[dict, dict]:
    """Stage 1 : décide structure. Retourne (strategy_json, gen_meta).

    T=0.4 (vs 0.85) car on veut décision déterministe pas créativité.
    """
    voice = (ctx.brand_dna or {}).get("voice_tokens", {}) or {}
    method = (ctx.brand_dna or {}).get("method", {}) or {}
    archetype = method.get("brand_archetype") or method.get("archetype", "?") if isinstance(method, dict) else "?"

    proofs_str = ", ".join(brief.available_proofs) if brief.available_proofs else "(aucun preuve déclarée)"
    sn_lines = [f"  - {sn.number} ({sn.source}, {sn.context})" for sn in brief.sourced_numbers[:5]]
    sn_str = "\n".join(sn_lines) if sn_lines else "(aucun chiffre sourcé fourni)"

    # V26.AF FIX 1 : doctrine V3.2.1 racine partagée
    doctrine_block = _format_doctrine_block(brief.page_type, n_critical=7, max_chars=2500)
    killer_rules_block = _format_killer_rules_block(brief.page_type, max_chars=800)

    prompt = STRATEGY_PROMPT_TEMPLATE.format(
        page_type=brief.page_type,
        format_intent=format_intent,
        brief_objective=brief.objective,
        brief_audience=brief.audience,
        brief_angle=brief.angle,
        traffic_source=", ".join(brief.traffic_source),
        visitor_mode=brief.visitor_mode,
        brand_signature=voice.get("voice_signature_phrase", "?")[:120],
        brand_archetype=archetype,
        archetype_summary=archetype_summary[:1200],
        available_proofs=proofs_str,
        sourced_numbers=sn_str,
        doctrine_block=doctrine_block,
        killer_rules_block=killer_rules_block,
    )

    if verbose:
        print(f"\n→ Stage 1 STRATEGY (T={temperature}, prompt={len(prompt)} chars)...")

    user_msg = "Produis le JSON strategy maintenant. Pas d'autre texte."

    gen = call_sonnet(prompt, user_msg, max_tokens=2000, temperature=temperature, verbose=False)
    raw_text = gen.get("html", "") or gen.get("text", "")

    # Extract JSON
    m = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not m:
        if verbose:
            print(f"  ⚠️ No JSON found in Stage 1 output. Raw[:200]: {raw_text[:200]}")
        return {}, gen

    try:
        strategy = json.loads(m.group(0))
    except Exception as e:
        if verbose:
            print(f"  ⚠️ JSON parse failed: {e}. Raw[:200]: {m.group(0)[:200]}")
        return {}, gen

    if verbose:
        n_sections = len(strategy.get("sections", []))
        n_proofs = len(strategy.get("key_proofs_to_use", []))
        print(f"  ✓ Stage 1 done — {n_sections} sections planned, {n_proofs} key proofs")
        print(f"  Hook : « {strategy.get('hook_concept', '?')[:120]} »")

    return strategy, gen


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — COPY (persona narrator)
# ─────────────────────────────────────────────────────────────────────────────

COPY_PROMPT_TEMPLATE = """{founder_persona}

## Mission Stage 2 COPY

Tu écris LE CONTENU TEXTUEL de la page (pas le HTML). Le strategy a déjà décidé la structure.

## Strategy validé (Stage 1)

{strategy_summary}

## Brief original (résumé)
- Objectif : {brief_objective}
- Audience : {brief_audience}
- Angle : {brief_angle}

## Règle de renoncement (CRITIQUE)

Si tu n'as pas une CONVICTION PROFONDE pour justifier un mot, **NE L'ÉCRIS PAS**.
- Pas de claim chiffré sans source vérifiée
- Pas de verbe vide ("découvrez", "boostez", "explorez", "transformez")
- Pas de testimonial inventé
- Pas d'urgence fake

Si une section serait creuse → omets-la. Une page courte 100% conviction > une longue 50% bullshit.

## Sourced numbers OBLIGATOIRE (anti-invention)

Tu ne peux citer QUE ces chiffres :
{sourced_numbers}

Si tu cites un autre chiffre → INVENTÉ → INTERDIT.

## Voice & tone

- Signature : « {brand_signature} »
- Ton : {brand_tone}
- Verbes CTA naturels : {cta_verbs}
- Mots INTERDITS (anti-marque) : {forbidden_words}

{doctrine_block}

## Format de sortie

Produis UN JSON strict (rien d'autre) avec UNE clé par section déclarée par strategy :
```json
{{
  "byline": "...",
  "h1": "...",
  "dek": "...",
  "intro": "...",
  "reasons": [
    {{"number": 1, "h2": "...", "body": "..."}},
    ...
  ],
  "pull_quotes": ["...", "..."],
  "stat_callouts": [{{"number": "...", "caption": "..."}}, ...],
  "cta_final": {{"headline": "...", "button": "...", "reassurance": "..."}}
}}
```

Langue obligatoire : {target_language}. Tous les textes dans cette langue, sans exception.
"""


def stage_2_copy(
    brief: BriefV2,
    ctx: ClientContext,
    strategy: dict,
    founder_persona: str,
    *,
    temperature: float = 0.7,
    verbose: bool = True,
) -> tuple[dict, dict]:
    """Stage 2 : persona narrator écrit le copy depuis strategy. Retourne (copy_json, gen_meta).

    T=0.7 (créatif mais pas erratique).
    """
    voice = (ctx.brand_dna or {}).get("voice_tokens", {}) or {}

    sn_lines = [f"  - {sn.number} ({sn.source})" for sn in brief.sourced_numbers[:5]]
    sn_str = "\n".join(sn_lines) if sn_lines else "(aucun — n'invente AUCUN chiffre)"

    tone = voice.get("tone", "expert")
    if isinstance(tone, list):
        tone = ", ".join(tone)
    forbidden_words = voice.get("forbidden_words", [])
    cta_verbs = voice.get("preferred_cta_verbs", [])

    strategy_summary = json.dumps(strategy, ensure_ascii=False, indent=2)[:2500]

    # V26.AF FIX 1 : doctrine plus courte pour Stage 2 (focus copy = persuasion criteria)
    doctrine_block_copy = _format_doctrine_block(brief.page_type, n_critical=5, max_chars=1500)

    prompt = COPY_PROMPT_TEMPLATE.format(
        founder_persona=founder_persona[:800],
        strategy_summary=strategy_summary,
        brief_objective=brief.objective[:200],
        brief_audience=brief.audience[:300],
        brief_angle=brief.angle[:200],
        sourced_numbers=sn_str,
        brand_signature=voice.get("voice_signature_phrase", "?")[:120],
        brand_tone=tone,
        cta_verbs=", ".join(cta_verbs[:5]) if cta_verbs else "?",
        forbidden_words=", ".join(forbidden_words[:8]) if forbidden_words else "(none)",
        target_language=brief.target_language,
        doctrine_block=doctrine_block_copy,
    )

    if verbose:
        print(f"\n→ Stage 2 COPY (T={temperature}, prompt={len(prompt)} chars)...")

    user_msg = f"Écris le copy en {brief.target_language}, JSON strict, suis le strategy ci-dessus."

    gen = call_sonnet(prompt, user_msg, max_tokens=4000, temperature=temperature, verbose=False)
    raw_text = gen.get("html", "") or gen.get("text", "")

    m = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not m:
        if verbose:
            print(f"  ⚠️ No JSON in Stage 2. Raw[:200]: {raw_text[:200]}")
        return {}, gen

    try:
        copy = json.loads(m.group(0))
    except Exception as e:
        if verbose:
            print(f"  ⚠️ JSON parse failed: {e}")
        return {}, gen

    if verbose:
        n_reasons = len(copy.get("reasons", []))
        n_pull = len(copy.get("pull_quotes", []))
        n_stats = len(copy.get("stat_callouts", []))
        print(f"  ✓ Stage 2 done — h1='{copy.get('h1', '?')[:60]}...', {n_reasons} reasons, {n_pull} pull_quotes, {n_stats} stat_callouts")

    return copy, gen


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 — COMPOSER (HTML structured)
# ─────────────────────────────────────────────────────────────────────────────

COMPOSER_PROMPT_TEMPLATE = """Tu es Composer HTML expert pour LPs éditoriales premium.

## Mission Stage 3 COMPOSER

Compose UN HTML auto-contenu (DOCTYPE → /html) à partir du copy déjà écrit Stage 2.
Le copy est FIGÉ — n'invente rien, ne réécris pas. Tu COMPOSES le HTML autour.

## Copy figé (Stage 2)

{copy_summary}

## Strategy (Stage 1, sections + layout)

{strategy_summary}

## AURA Design Tokens (CSS prêt à coller)

{aura_css_block}

## Layout archetype prescrit

{archetype_summary}

## Format de sortie

HTML autocontenu :
- Commence par `<!DOCTYPE html>`, finit par `</html>`
- Mobile-first (375px) puis desktop (1440px+)
- Typo : utilise `var(--font-display)` pour h1/h2/h3, `var(--font-body)` pour body
- Couleurs : utilise `var(--color-*)` partout, JAMAIS de hex en dur
- Pas de framework JS (vanilla seulement)
- Pas de stock photos lifestyle génériques
- SVG inline autorisés s'ils clarifient un concept, une donnée ou une métaphore produit
- Drop caps massifs pour numéros de section (clamp 4rem-6rem, opacity 0.15)
- Hairline rules 0.5px entre sections (pas border-radius cards)
- Pull quotes italique sans border-left coloré
- Stat callouts inline énormes (chiffre 3-5x body, caption petit)
- Avatar/byline : monogramme sobre ou portrait réel si fourni

## Anti-slop visuel

Interdit : les clichés visibles d'IA générative sans intention, comme fake stars,
FOMO countdown, lifestyle stock photo, 3 cards SaaS génériques, gradients multi-orbes
posés au hasard, neumorphism.

Autorisé et encouragé quand c'est maîtrisé : gradient subtil, backdrop nav discret,
grain/noise léger, ombres multi-layer, hairlines, marginalia, schémas SVG utiles,
drop caps colorés, pull quotes typographiques. Ne te défends pas en produisant une
page blanche : choisis 2-4 gestes visuels forts, cohérents avec la thèse.

## Langue obligatoire

{target_language} pour TOUS les textes (h1, h2, body, alt, footer).
"""


def stage_3_composer(
    brief: BriefV2,
    ctx: ClientContext,
    strategy: dict,
    copy: dict,
    aura_css_block: str,
    archetype_summary: str,
    vision_images: Optional[list[pathlib.Path]] = None,
    *,
    temperature: float = 0.6,
    max_tokens: int = 8000,
    verbose: bool = True,
) -> tuple[str, dict]:
    """Stage 3 : compose HTML. Retourne (html, gen_meta).

    T=0.6 (équilibre entre fidélité copy et créativité visuelle).
    Optionnel : multimodal vision (screenshots client + golden refs).
    """
    copy_summary = json.dumps(copy, ensure_ascii=False, indent=2)[:3500]
    strategy_summary = json.dumps(strategy, ensure_ascii=False, indent=2)[:1500]

    prompt = COMPOSER_PROMPT_TEMPLATE.format(
        copy_summary=copy_summary,
        strategy_summary=strategy_summary,
        aura_css_block=aura_css_block[:3500] if aura_css_block else "(no AURA tokens — fallback safe)",
        archetype_summary=archetype_summary[:1200],
        target_language=brief.target_language,
    )

    if verbose:
        sz = len(prompt)
        print(f"\n→ Stage 3 COMPOSER (T={temperature}, prompt={sz} chars, vision_images={len(vision_images) if vision_images else 0})...")

    user_msg = "Compose le HTML maintenant. Sortie : HTML pur, commence par <!DOCTYPE html>."

    if vision_images:
        gen = call_sonnet_multimodal(
            prompt, user_msg, image_paths=vision_images,
            max_tokens=max_tokens, temperature=temperature, verbose=False,
        )
    else:
        gen = call_sonnet(prompt, user_msg, max_tokens=max_tokens, temperature=temperature, verbose=False)

    html = gen.get("html", "")

    if verbose:
        print(f"  ✓ Stage 3 done — HTML {len(html)} chars")

    return html, gen


# ─────────────────────────────────────────────────────────────────────────────
# Stage 4 — POLISH (refine HTML)
# ─────────────────────────────────────────────────────────────────────────────

POLISH_PROMPT_TEMPLATE = """Tu es Polish Editor expert. Le HTML produit Stage 3 est BON mais peut être raffiné.

## Mission Stage 4 POLISH

Tu reçois le HTML composé. Tu peux EDITER (pas réécrire) pour corriger :
1. Langue : si un mot n'est pas en {target_language}, traduis-le
2. Typo : remplace toute font Inter/Roboto/Arial/Open Sans/Lato/Montserrat par var(--font-display) ou var(--font-body)
3. Anti-slop visuel : retire uniquement les clichés sans intention (fake stars, FOMO countdown, stock lifestyle, 3-cards génériques, gradient-orbs gratuits)
4. Hard constraints : si typo principale doit être '{forced_font}', impose-la dans CSS
5. Hairlines : remplace `border: 1px solid` lourds par `border-bottom: 0.5px solid`
6. Drop caps : si raisons numérotées sans drop cap massif, ajoute (clamp 4rem-6rem, opacity 0.15)

## INTERDITS de POLISH

- N'invente PAS de nouveau contenu (texte, sections)
- Ne change PAS la palette (--color-*) ni le layout général
- Ne retire PAS la profondeur visuelle juste pour "faire propre" : si un gradient,
  une ombre, un blur ou un SVG sert la thèse, garde-le et raffine-le.

## Output

HTML autocontenu raffiné. DOCTYPE → /html.
"""


def stage_4_polish(
    html_in: str,
    brief: BriefV2,
    *,
    forced_font: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 8000,
    verbose: bool = True,
) -> tuple[str, dict]:
    """Stage 4 : raffine HTML. Retourne (html_polished, gen_meta).

    T=0.3 (édition stricte, pas créativité).
    """
    prompt = POLISH_PROMPT_TEMPLATE.format(
        target_language=brief.target_language,
        forced_font=forced_font or "(brand font)",
    )

    if verbose:
        print(f"\n→ Stage 4 POLISH (T={temperature}, html_in={len(html_in)} chars)...")

    user_msg = f"HTML à raffiner (édite, ne réécris pas) :\n\n{html_in}"

    gen = call_sonnet(prompt, user_msg, max_tokens=max_tokens, temperature=temperature, verbose=False)
    html_out = gen.get("html", "")

    if verbose:
        print(f"  ✓ Stage 4 done — HTML {len(html_out)} chars")

    return html_out, gen


def _count_action_controls(html: str) -> int:
    """Count obvious action controls in generated HTML."""
    return len(re.findall(r"<(?:a|button)\b", html or "", re.IGNORECASE))


def _html_looks_complete(html: str) -> bool:
    """Cheap guard against Stage 4 truncating or breaking the document."""
    if not html:
        return False
    html_lower = html.lower()
    if "</html>" not in html_lower or "</body>" not in html_lower:
        return False
    if re.search(r"<p\b[^>]*>(?:(?!</p>).)*$", html, re.IGNORECASE | re.DOTALL):
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline_sequential_4_stages(
    brief: BriefV2,
    ctx: ClientContext,
    *,
    founder_persona: str = "",
    archetype_summary: str = "",
    format_intent: str = "",
    aura_css_block: str = "",
    vision_images: Optional[list[pathlib.Path]] = None,
    forced_font: Optional[str] = None,
    save_intermediates: bool = True,
    save_dir: Optional[pathlib.Path] = None,
    verbose: bool = True,
) -> dict:
    """Pipeline 4 stages séquentiels (Strategy → Copy → Composer → Polish).

    Returns: dict {
      html_final, html_composed, html_polished,
      strategy, copy,
      stages_meta: [{stage, tokens_in, tokens_out, wall_seconds}, ...],
      total_cost_usd, total_wall_seconds,
    }
    """
    grand_t0 = time.time()
    stages_meta = []

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)

    # ── Stage 1 STRATEGY ──
    t0 = time.time()
    strategy, s1_gen = stage_1_strategy(
        brief, ctx, archetype_summary, format_intent,
        verbose=verbose,
    )
    s1_wall = time.time() - t0
    stages_meta.append({
        "stage": "1_strategy",
        "tokens_in": s1_gen.get("tokens_in", 0),
        "tokens_out": s1_gen.get("tokens_out", 0),
        "wall_seconds": round(s1_wall, 1),
    })
    if save_intermediates and save_dir:
        (save_dir / "stage_1_strategy.json").write_text(json.dumps(strategy, ensure_ascii=False, indent=2))

    if not strategy:
        return {"error": "Stage 1 STRATEGY failed", "stages_meta": stages_meta}

    # ── Stage 2 COPY ──
    t0 = time.time()
    copy, s2_gen = stage_2_copy(brief, ctx, strategy, founder_persona, verbose=verbose)
    s2_wall = time.time() - t0
    stages_meta.append({
        "stage": "2_copy",
        "tokens_in": s2_gen.get("tokens_in", 0),
        "tokens_out": s2_gen.get("tokens_out", 0),
        "wall_seconds": round(s2_wall, 1),
    })
    if save_intermediates and save_dir:
        (save_dir / "stage_2_copy.json").write_text(json.dumps(copy, ensure_ascii=False, indent=2))

    if not copy:
        return {"error": "Stage 2 COPY failed", "strategy": strategy, "stages_meta": stages_meta}

    # ── Stage 3 COMPOSER ──
    t0 = time.time()
    html_composed, s3_gen = stage_3_composer(
        brief, ctx, strategy, copy, aura_css_block, archetype_summary,
        vision_images=vision_images, verbose=verbose,
    )
    s3_wall = time.time() - t0
    stages_meta.append({
        "stage": "3_composer",
        "tokens_in": s3_gen.get("tokens_in", 0),
        "tokens_out": s3_gen.get("tokens_out", 0),
        "wall_seconds": round(s3_wall, 1),
    })
    if save_intermediates and save_dir:
        (save_dir / "stage_3_composer.html").write_text(html_composed)

    if not html_composed:
        return {"error": "Stage 3 COMPOSER failed", "strategy": strategy, "copy": copy, "stages_meta": stages_meta}

    # ── Stage 4 POLISH ──
    t0 = time.time()
    html_polished, s4_gen = stage_4_polish(
        html_composed, brief, forced_font=forced_font, verbose=verbose,
    )
    s4_wall = time.time() - t0
    stages_meta.append({
        "stage": "4_polish",
        "tokens_in": s4_gen.get("tokens_in", 0),
        "tokens_out": s4_gen.get("tokens_out", 0),
        "wall_seconds": round(s4_wall, 1),
    })

    polish_fallback_reason = ""
    if not _html_looks_complete(html_polished):
        polish_fallback_reason = "stage4_incomplete_html"
    elif _count_action_controls(html_composed) > 0 and _count_action_controls(html_polished) == 0:
        polish_fallback_reason = "stage4_lost_all_action_controls"

    if polish_fallback_reason:
        if verbose:
            print(f"  ⚠️ Stage 4 fallback → using Stage 3 HTML ({polish_fallback_reason})")
        html_polished = html_composed
        stages_meta[-1]["fallback_to_stage3"] = polish_fallback_reason

    # Apply runtime fixes (counter, reveal, opacity bugs)
    html_final, fixes_info = apply_runtime_fixes(html_polished, verbose=False)
    if save_intermediates and save_dir:
        (save_dir / "stage_4_polished.html").write_text(html_polished)
        (save_dir / "stage_5_final.html").write_text(html_final)

    grand_dt = time.time() - grand_t0
    total_in = sum(s["tokens_in"] for s in stages_meta)
    total_out = sum(s["tokens_out"] for s in stages_meta)
    total_cost = (total_in / 1e6 * 3) + (total_out / 1e6 * 15)

    if verbose:
        print(f"\n══ Pipeline 4 stages DONE ══")
        print(f"  Total wall : {grand_dt:.1f}s")
        print(f"  Total tokens : in={total_in} out={total_out}")
        print(f"  Total cost : ${total_cost:.3f}")
        print(f"  Final HTML : {len(html_final)} chars")

    return {
        "html_final": html_final,
        "html_polished": html_polished,
        "html_composed": html_composed,
        "strategy": strategy,
        "copy": copy,
        "stages_meta": stages_meta,
        "fixes_runtime": fixes_info,
        "total_tokens_in": total_in,
        "total_tokens_out": total_out,
        "total_cost_usd": round(total_cost, 3),
        "total_wall_seconds": round(grand_dt, 1),
    }
