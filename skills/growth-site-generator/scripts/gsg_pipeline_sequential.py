"""GSG Pipeline Sequential V26.Z P1 — découpage du mega-prompt en 4 stages chaînés.

Réponse à la faille structurelle confirmée par le FINAL benchmark : le
mega-prompt one-shot (53-67K chars) sature Sonnet qui empile les techniques
sans thèse, ignore les règles INTERDIT, hallucine des témoignages, et le
repair loop régresse au lieu d'améliorer.

Cette pipeline découpe la génération en 4 stages, chaque stage produit un
artefact JSON/HTML validable séparément. Si le Stage 1 (stratégie) dévie,
on le détecte avant de gaspiller Stage 3+4.

ARCHITECTURE
============

Stage 1 — Strategy & Wireframe Narratif
  Input  : brand_dna + diff + design_grammar + creative_route + business_context
  Output : strategy.json
    {
      "page_thesis": "<1-2 phrases qui tient toute la LP>",
      "narrative_arc": ["hook", "tension", "resolution", "cta"],
      "sections": [
        {
          "id": "hero", "name": "Hero", "narrative_role": "hook",
          "psych_principle": ["loss_aversion", "specificity"],
          "design_cues": ["asymmetric_60_40", "stat_callout_visible"],
          "cta_priority": "primary",
          "key_message": "<1 phrase>",
          "must_include": ["stat 327%", "stat callout"],
          "must_not_include": ["lifestyle photo", "logos carousel"]
        },
        ...
      ],
      "cta_strategy": {
        "primary_label": "Tester gratuitement",
        "placement_count": 3,
        "placement_sections": ["hero", "after_section_4", "final"]
      }
    }

Stage 2 — Copy Writer
  Input  : wireframe + brand_dna.voice + creative_route.emotional_promise + frameworks (PAS, Cialdini)
  Output : copy.json
    {
      "hero": {"h1": "...", "subtitle": "...", "cta_label": "..."},
      "sections": [
        {
          "id": "section_1", "h2": "...", "body_paragraphs": ["...", "..."],
          "evidence": "<chiffre/témoignage>", "cta_micro": null
        },
        ...
      ],
      "faq": [{"q": "...", "a": "..."}],
      "footer": "..."
    }

Stage 3 — HTML Composer (sémantique sans empilement)
  Input  : wireframe + copy + design_tokens (aura palette + typo)
  Output : HTML structure complète, CSS minimal cohérent
    - PAS de "technique stacking" (pas 20 techniques imposées par quota)
    - Sémantique HTML5 propre
    - États finaux visibles par défaut (rendering safe by default)
    - Mobile-first responsive

Stage 4 — HTML Polish
  Input  : HTML composer + creative_route.signature_elements + technique_choice
  Output : HTML final avec 3-5 polish elements ciblés (pas 20)
    - Polish dérivé de creative_route.signature_elements
    - Animations CSS-only auto-play (pas de reveal-class)
    - Counter avec valeurs visibles par défaut

Coût estimé : ~$0.30 par run (4 calls Sonnet, ~2-5K tokens out chacun).
Vs mega-prompt one-shot : ~$0.40, similaire mais 4 artefacts validables.

Usage CLI : appelé via gsg_generate_lp.py --sequential

Usage module :
    from gsg_pipeline_sequential import run_sequential_pipeline
    html = run_sequential_pipeline(
        client="weglot", brand_dna={...}, design_grammar={...},
        creative_route={...}, business_context="...", ...
    )
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
SONNET_MODEL = "claude-sonnet-4-5-20250929"


def _strip_fences(raw: str, lang: str = "json") -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith(f"{lang}\n"):
            text = text[len(lang) + 1:]
        elif text.startswith("\n"):
            text = text[1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _parse_json_safe(raw: str) -> dict:
    text = _strip_fences(raw, "json")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"JSON parse failed. Raw first 500: {text[:500]}")


def _call_sonnet(system: str, user: str, max_tokens: int = 4000,
                 temperature: float = 0.5, label: str = "stage",
                 verbose: bool = True) -> tuple[str, int, int]:
    """Call Sonnet with system + user message. Returns (text, tokens_in, tokens_out)."""
    import anthropic
    client_api = anthropic.Anthropic()
    if verbose:
        print(f"  → [{label}] Sonnet call (system={len(system)}, user={len(user)} chars, max_tokens={max_tokens}, temp={temperature}) ...", flush=True)
    msg = client_api.messages.create(
        model=SONNET_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = msg.content[0].text
    if verbose:
        print(f"  ← [{label}] in={msg.usage.input_tokens} out={msg.usage.output_tokens} stop={msg.stop_reason}", flush=True)
    return raw, msg.usage.input_tokens, msg.usage.output_tokens


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — Strategy & Wireframe Narratif
# ─────────────────────────────────────────────────────────────────────────────

STRATEGY_SYSTEM = """Tu es **stratège senior CRO + directeur créatif** (15+ ans agences top-tier). Tu reçois le brief client + brand DNA + creative route choisie. Tu produis UN SEUL artefact : le wireframe narratif structuré JSON qui guidera la génération de la LP.

## RÈGLES D'OR

1. **UNE THÈSE TIENT TOUTE LA LP** — pas un kitchen-sink, pas 20 idées juxtaposées.
2. **Chaque section sert le narrative arc** — hook → tension → resolution → cta. Pas de section décorative.
3. **Spécificité business** — pas de "section preuve sociale" générique, mais "section preuve sociale avec chiffre 327% + 2 témoignages cardinaux + comparison table".
4. **Anti-empilement** — chaque section a 1-2 design_cues max, pas 5. Le polish vient en Stage 4, pas ici.
5. **CTA strategy explicite** — placement réfléchi (typiquement 2-3 instances), pas un CTA toutes les sections.

## STRUCTURE OUTPUT (JSON STRICT)

{
  "page_thesis": "<1-2 phrases qui tiennent TOUTE la LP — c'est la promesse + le parti-pris>",
  "narrative_arc": ["hook", "tension", "resolution", "validation", "cta"],
  "sections": [
    {
      "id": "hero",
      "name": "<nom court humain>",
      "narrative_role": "hook|tension|resolution|validation|cta_setup|cta_final",
      "psych_principle": ["loss_aversion"|"social_proof"|"authority"|"scarcity"|"specificity"|"reciprocity"],
      "design_cues": ["<2 cues max, type 'asymmetric_60_40' ou 'stat_callout_dominant'>"],
      "cta_priority": "primary|secondary|none",
      "key_message": "<1 phrase qui résume CE QUE LE LECTEUR DOIT COMPRENDRE>",
      "must_include": ["<éléments concrets obligatoires, ex: 'stat 327%' ou 'logo bar HBO/IBM'>"],
      "must_not_include": ["<patterns à éviter spécifiquement pour cette section>"]
    }
  ],
  "cta_strategy": {
    "primary_label": "<verbe actif ancré dans voice_tokens client>",
    "primary_action": "<URL ou anchor>",
    "placement_count": <int 2-4>,
    "placement_sections": ["<liste section ids>"]
  },
  "must_avoid_globally": [
    "<3-5 patterns à éviter au niveau page entière, ex: 'reveal-class JS-dependent', 'symmetric centered hero'>"
  ]
}

JSON only, pas de markdown. Sois TRANCHANT — chaque section doit JUSTIFIER son existence."""


def stage1_strategy_wireframe(brand_dna: dict, design_grammar: dict,
                               creative_route: dict, business_context: str,
                               page_type: str, client: str,
                               verbose: bool = True) -> tuple[dict, dict]:
    """Stage 1 : génère wireframe narratif JSON.

    Returns: (strategy_json, telemetry_dict)
    """
    # Compact brand summary
    vt = brand_dna.get("visual_tokens") or {}
    voice = brand_dna.get("voice_tokens") or {}
    img_dir = brand_dna.get("image_direction") or {}
    diff = brand_dna.get("diff") or {}

    brand_compact = {
        "identity": brand_dna.get("identity", {}),
        "voice_tone": (voice.get("tone") or [])[:5],
        "voice_forbidden_words": (voice.get("forbidden_words") or [])[:8],
        "preferred_cta_verbs": (voice.get("preferred_cta_verbs") or [])[:5],
        "signature_visual_motif": img_dir.get("signature_visual_motif"),
        "diff_summary": diff.get("summary"),
        "diff_fix_priorities": [
            f for f in (diff.get("fix") or []) if isinstance(f, dict) and f.get("priority") == "high"
        ][:5],
    }

    cr_compact = {
        "name": creative_route.get("name"),
        "risk_level": creative_route.get("risk_level"),
        "philosophy": creative_route.get("aesthetic_philosophy"),
        "emotional_promise": creative_route.get("emotional_promise"),
        "signature_elements": creative_route.get("signature_elements"),
        "must_not_do": creative_route.get("must_not_do"),
    } if creative_route else None

    dg_anti_patterns = ((design_grammar or {}).get("brand_forbidden_patterns") or {}).get("global_anti_ai_patterns", [])[:8]

    user_msg = f"""# CLIENT : {client.upper()}
# PAGE TYPE : {page_type}

## Brand DNA (compact)
```json
{json.dumps(brand_compact, ensure_ascii=False, indent=2)}
```

## Creative Route choisie
```json
{json.dumps(cr_compact, ensure_ascii=False, indent=2) if cr_compact else "(aucune — mode legacy)"}
```

## Design Grammar — anti-patterns brand
{chr(10).join(f"  - {p}" for p in dg_anti_patterns) if dg_anti_patterns else "(aucun)"}

## Business context
{business_context[:5000] if business_context else '(brief minimal)'}

Produis le wireframe narratif JSON pour cette LP. Pas plus de 8-10 sections totales (intro+items+bab+faq+footer). Tranche."""

    raw, t_in, t_out = _call_sonnet(
        system=STRATEGY_SYSTEM, user=user_msg,
        max_tokens=5000, temperature=0.4, label="Stage 1 — Strategy",
        verbose=verbose,
    )
    try:
        strategy = _parse_json_safe(raw)
    except (ValueError, json.JSONDecodeError) as e:
        # Retry once with prompt reminder to be concise
        if verbose:
            print(f"  ⚠️  Stage 1 parse failed ({e}), retrying with concise reminder...", flush=True)
        retry_user = user_msg + "\n\n## RAPPEL : Le JSON DOIT être complet et valide. Sois concis. Pas plus de 8 sections totales. Termine TOUJOURS par la fermeture des crochets."
        raw, t_in2, t_out2 = _call_sonnet(
            system=STRATEGY_SYSTEM, user=retry_user,
            max_tokens=6000, temperature=0.3, label="Stage 1 — Strategy (retry)",
            verbose=verbose,
        )
        strategy = _parse_json_safe(raw)
        t_in += t_in2
        t_out += t_out2
    return strategy, {"tokens_in": t_in, "tokens_out": t_out}


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — Copy Writer
# ─────────────────────────────────────────────────────────────────────────────

COPY_SYSTEM = """Tu es **copywriter senior CRO** (15+ ans). Tu reçois le wireframe narratif d'une LP + le brand voice. Tu produis le copy section par section, EN STRICT RESPECT du wireframe.

## RÈGLES D'OR

1. **Tu ne changes PAS la structure** — le wireframe est la vérité, tu remplis le copy.
2. **Voice tokens client** — tone, forbidden_words, sentence_rhythm. Si voice = "consultant senior FR direct", écris comme tel. Pas de copywriter générique IA.
3. **Concrétude obligatoire** — chiffres précis, scènes mentales, pas d'abstractions ("rapide" → "5 minutes" ; "compatible" → "WordPress, Shopify, Webflow").
4. **Frameworks copy orchestrés** — si le wireframe dit "psych_principle: loss_aversion", le copy DOIT activer ce principe par des mots concrets ("perdez", "manquez", "invisibles").
5. **H2 narratifs concrets** — pas "Notre solution" mais "Le widget Klaviyo que tu as oublié, on le voit". Voir principes A-I dans Headline Formulas.
6. **Pas d'hallucination** — pas de témoignages CEO Weglot citant Weglot. Pas de chiffre inventé. Si tu n'as pas le fait, tu ne l'inventes pas.

## STRUCTURE OUTPUT (JSON STRICT)

{
  "hero": {
    "eyebrow": "<optionnel — 'Édition Growth Society · Dossier X' ou similaire>",
    "h1": "<headline conforme au key_message du wireframe>",
    "subtitle": "<1-2 phrases qui prolongent>",
    "cta_label": "<conforme à cta_strategy.primary_label>",
    "cta_micro_reassurance": "<optionnel — 'Sans CB · 10 jours' ou similaire>"
  },
  "stat_shock": {
    "primary_number": "<chiffre principal hero ou shock section>",
    "label": "<courte description>",
    "context": "<source du chiffre — 'Étude Weglot 1.3M citations 2025'>"
  },
  "sections": [
    {
      "id": "<copie de wireframe.sections[i].id>",
      "h2": "<headline narrative concret, principe A-I>",
      "body_paragraphs": ["<paragraphe 1>", "<paragraphe 2>"],
      "evidence": "<chiffre, témoignage, ou null>",
      "cta_micro": "<optionnel si cta_priority=secondary>"
    }
  ],
  "faq": [
    {"q": "<question fréquente>", "a": "<réponse 2-3 phrases>"}
  ],
  "comparison_table": {
    "rows": [
      {"feature": "<critère>", "us": "<notre value>", "competitor": "<value concurrent>"}
    ]
  } | null,
  "footer_text": "<phrase courte mention édition>"
}

JSON only. Sois SPÉCIFIQUE et ANCRÉ — chaque phrase doit pouvoir être prouvée."""


def stage2_copy(strategy: dict, brand_dna: dict, creative_route: dict,
                 business_context: str, copy_hints: str = "",
                 verbose: bool = True) -> tuple[dict, dict]:
    """Stage 2 : génère le copy structuré par section."""
    voice = brand_dna.get("voice_tokens") or {}
    voice_compact = {
        "tone": (voice.get("tone") or [])[:5],
        "forbidden_words": (voice.get("forbidden_words") or [])[:10],
        "preferred_cta_verbs": (voice.get("preferred_cta_verbs") or [])[:5],
        "sentence_rhythm": voice.get("sentence_rhythm"),
        "voice_signature_phrase": voice.get("voice_signature_phrase"),
    }

    user_msg = f"""## Wireframe narratif (à respecter strict)
```json
{json.dumps(strategy, ensure_ascii=False, indent=2)[:6000]}
```

## Brand voice
```json
{json.dumps(voice_compact, ensure_ascii=False, indent=2)}
```

## Creative emotional promise
{creative_route.get('emotional_promise', '(none)') if creative_route else '(none)'}

## Business context
{business_context[:4000] if business_context else '(none)'}

## Copy hints (rough)
{copy_hints[:1500] if copy_hints else '(none)'}

Produis le copy JSON pour cette LP, section par section, en respectant strict le wireframe et le voice."""

    raw, t_in, t_out = _call_sonnet(
        system=COPY_SYSTEM, user=user_msg,
        max_tokens=5000, temperature=0.6, label="Stage 2 — Copy",
        verbose=verbose,
    )
    copy_data = _parse_json_safe(raw)
    return copy_data, {"tokens_in": t_in, "tokens_out": t_out}


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — HTML Composer (structure sémantique)
# ─────────────────────────────────────────────────────────────────────────────

COMPOSER_SYSTEM = """Tu es **développeur front-end senior** (15+ ans). Tu reçois un wireframe + un copy structuré + des design tokens (palette, typo, spacing). Tu produis le HTML COMPLET sémantique avec CSS minimal cohérent.

## RÈGLES D'OR

1. **Sémantique HTML5** — header, main, section, article, footer, h1-h3, p. Pas tout en div.
2. **CSS minimal** — variables CSS pour palette/typo/spacing, classes contextuelles, pas d'inline styles.
3. **Mobile-first** — single column 375px par défaut, breakpoints @media min-width.
4. **Rendering safe by default** — TOUS les états finaux visibles par défaut. PAS de opacity:0 par défaut, PAS de classes reveal qui dépendent de JS.
5. **Composition cohérente** — les design_cues du wireframe (asymmetric_60_40, stat_callout) doivent être implémentées en CSS.
6. **Pas d'empilement de techniques** — TU NE CRÉES PAS de mesh gradient + grain + glass + cursor glow + drop caps tous ensemble. Le polish vient en Stage 4. Ici, structure + typo + palette + 1 motif signature, c'est tout.
7. **Counter values visibles** — si stat 327%, écris `<span data-target="327">327</span>` (pas `>0<`).
8. **Animations CSS-only** — si tu veux du motion, utilise `animation: <name> Xs Y forwards` qui se déclenche au load. PAS de classes reveal JS-dependent.

## STRUCTURE OUTPUT

HTML complet, auto-contenu (style inline dans `<style>`), commencer par `<!DOCTYPE html>`, finir par `</html>`. Aucun JS pour l'instant (Stage 4 ajoutera le polish JS si nécessaire).

Pas de markdown, pas d'explication — juste le HTML pur."""


def stage3_composer(strategy: dict, copy_data: dict, brand_dna: dict,
                    aura: dict, design_grammar: dict, target_url: str = "",
                    verbose: bool = True) -> tuple[str, dict]:
    """Stage 3 : compose HTML sémantique structure."""
    vt = brand_dna.get("visual_tokens") or {}
    colors = vt.get("colors") or {}
    typo = vt.get("typography") or {}
    palette = colors.get("palette_full") or []

    palette_compact = {
        "primary": palette[0].get("hex") if palette else "#000",
        "secondary": [p.get("hex") for p in palette[1:5] if p.get("hex")],
    }
    typo_compact = {
        "h1": (typo.get("h1") or {}).get("family", "system-ui"),
        "body": (typo.get("body") or {}).get("family", "system-ui"),
    }

    aura_palette = aura.get("palette") or {}
    aura_typo = aura.get("typography") or {}

    user_msg = f"""## Wireframe (structure)
```json
{json.dumps(strategy, ensure_ascii=False, indent=2)[:5000]}
```

## Copy (contenu)
```json
{json.dumps(copy_data, ensure_ascii=False, indent=2)[:8000]}
```

## Design tokens
- Palette brand : {json.dumps(palette_compact)}
- Typo brand : {json.dumps(typo_compact)}
- AURA palette dérivée : {json.dumps({k: v for k, v in aura_palette.items() if not k.endswith('_rgb')})[:600]}
- AURA typo : {json.dumps(aura_typo)[:300]}

## URL cible : {target_url or '(none)'}

Compose le HTML complet sémantique. Mobile-first. Rendering safe by default. Pas de polish JS-dependent."""

    raw, t_in, t_out = _call_sonnet(
        system=COMPOSER_SYSTEM, user=user_msg,
        max_tokens=10000, temperature=0.4, label="Stage 3 — Composer",
        verbose=verbose,
    )
    # Strip code fences if present
    html = raw.strip()
    if html.startswith("```"):
        html = html.lstrip("`")
        if html.startswith("html\n"):
            html = html[5:]
        elif html.startswith("\n"):
            html = html[1:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()
    return html, {"tokens_in": t_in, "tokens_out": t_out}


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — HTML Polish (techniques ciblées par intention)
# ─────────────────────────────────────────────────────────────────────────────

POLISH_SYSTEM = """Tu es **directeur artistique senior + dev front senior**. Tu reçois un HTML composé propre + une creative_route + ses signature_elements. Tu ajoutes du polish CIBLÉ — pas un kitchen-sink.

## RÈGLES D'OR

1. **Polish ciblé, pas empilé** — tu ajoutes UNIQUEMENT 3-5 signature_elements de la creative_route. PAS 20 techniques.
2. **Cohérence avec la thèse visuelle** — chaque élément ajouté doit renforcer la "name" + "philosophy" de la creative_route. Si elle dit "Editorial Press Tech", tu n'ajoutes pas "cursor glow" (c'est SaaS générique).
3. **Animations CSS-only auto-play UNIQUEMENT** — `animation: <name> Xs Y forwards` ou `@supports (animation-timeline: view())`. PAS de classes reveal JS-dependent.
4. **JS optionnel** — si tu ajoutes un counter animation ou une interaction, le HTML par défaut DOIT être utilisable sans JS. Le JS = polish.
5. **Conserve la structure HTML existante** — tu ne réorganises pas, tu polish.
6. **Tu retournes le HTML complet final** (pas un diff).

## STRUCTURE OUTPUT

HTML complet final, auto-contenu, commencer par `<!DOCTYPE html>`, finir par `</html>`. Pas de markdown, pas d'explication."""


def stage4_polish(html_composer: str, creative_route: dict,
                   verbose: bool = True) -> tuple[str, dict]:
    """Stage 4 : applique polish ciblé via creative_route."""
    if not creative_route:
        # No creative route → no polish, return as-is
        return html_composer, {"tokens_in": 0, "tokens_out": 0, "skipped": True}

    cr_compact = {
        "name": creative_route.get("name"),
        "philosophy": creative_route.get("aesthetic_philosophy"),
        "signature_elements": creative_route.get("signature_elements"),
        "motion_thesis": creative_route.get("motion_thesis"),
        "must_not_do": creative_route.get("must_not_do"),
    }

    # Truncate HTML if huge
    html_for_prompt = html_composer if len(html_composer) < 40000 else html_composer[:40000] + "\n... [truncated]"

    user_msg = f"""## Creative Route — La thèse visuelle à servir
```json
{json.dumps(cr_compact, ensure_ascii=False, indent=2)}
```

## HTML composé (Stage 3) à enrichir avec polish ciblé
```html
{html_for_prompt}
```

Ajoute UNIQUEMENT les 3-5 signature_elements de la creative_route, en CSS-only auto-play. Pas d'empilement. Retourne le HTML complet final."""

    raw, t_in, t_out = _call_sonnet(
        system=POLISH_SYSTEM, user=user_msg,
        max_tokens=12000, temperature=0.5, label="Stage 4 — Polish",
        verbose=verbose,
    )
    html = raw.strip()
    if html.startswith("```"):
        html = html.lstrip("`")
        if html.startswith("html\n"):
            html = html[5:]
        elif html.startswith("\n"):
            html = html[1:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()
    return html, {"tokens_in": t_in, "tokens_out": t_out}


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def run_sequential_pipeline(client: str, brand_dna: dict, design_grammar: dict,
                             aura: dict, creative_route: Optional[dict],
                             business_context: str, copy_hints: str = "",
                             page_type: str = "listicle", target_url: str = "",
                             verbose: bool = True) -> dict:
    """Orchestre les 4 stages chaînés. Sauvegarde chaque artefact intermédiaire
    dans data/_pipeline_<client>_stage<N>.{json|html}.

    Returns:
      {
        "html_final": str,
        "strategy": dict,
        "copy": dict,
        "html_composer": str,
        "telemetry": {"stage1": {...}, "stage2": {...}, "stage3": {...}, "stage4": {...}, "tokens_total": int}
      }
    """
    if verbose:
        print(f"\n══ Sequential Pipeline V26.Z P1 — {client} / {page_type} ══")

    # Stage 1
    if verbose:
        print(f"\n[Stage 1/4] Strategy & Wireframe Narratif")
    strategy, t1 = stage1_strategy_wireframe(
        brand_dna, design_grammar, creative_route or {},
        business_context, page_type, client, verbose=verbose,
    )
    s1_fp = ROOT / "data" / f"_pipeline_{client}_stage1_strategy.json"
    s1_fp.write_text(json.dumps(strategy, ensure_ascii=False, indent=2))
    if verbose:
        print(f"  ✓ Strategy : page_thesis = \"{strategy.get('page_thesis', '?')[:120]}\"")
        print(f"  ✓ Sections : {len(strategy.get('sections', []))}")
        print(f"  ✓ saved → {s1_fp.relative_to(ROOT)}")

    # Stage 2
    if verbose:
        print(f"\n[Stage 2/4] Copy Writer")
    copy_data, t2 = stage2_copy(
        strategy, brand_dna, creative_route or {},
        business_context, copy_hints, verbose=verbose,
    )
    s2_fp = ROOT / "data" / f"_pipeline_{client}_stage2_copy.json"
    s2_fp.write_text(json.dumps(copy_data, ensure_ascii=False, indent=2))
    if verbose:
        n_sections = len(copy_data.get("sections", []))
        n_faq = len(copy_data.get("faq", []))
        print(f"  ✓ Hero h1 : \"{copy_data.get('hero', {}).get('h1', '?')[:80]}\"")
        print(f"  ✓ Sections : {n_sections}, FAQ : {n_faq}")
        print(f"  ✓ saved → {s2_fp.relative_to(ROOT)}")

    # Stage 3
    if verbose:
        print(f"\n[Stage 3/4] HTML Composer")
    html_composer, t3 = stage3_composer(
        strategy, copy_data, brand_dna, aura, design_grammar,
        target_url=target_url, verbose=verbose,
    )
    s3_fp = ROOT / "data" / f"_pipeline_{client}_stage3_composer.html"
    s3_fp.write_text(html_composer)
    if verbose:
        print(f"  ✓ HTML composer : {len(html_composer)} chars · {html_composer.count(chr(10))+1} lines")
        print(f"  ✓ saved → {s3_fp.relative_to(ROOT)}")

    # Stage 4
    if verbose:
        print(f"\n[Stage 4/4] HTML Polish (creative_route signature_elements)")
    html_final, t4 = stage4_polish(html_composer, creative_route, verbose=verbose)
    s4_fp = ROOT / "data" / f"_pipeline_{client}_stage4_final.html"
    s4_fp.write_text(html_final)
    if verbose:
        print(f"  ✓ HTML final : {len(html_final)} chars · {html_final.count(chr(10))+1} lines")
        print(f"  ✓ saved → {s4_fp.relative_to(ROOT)}")

    tokens_total = sum(t.get("tokens_in", 0) + t.get("tokens_out", 0)
                       for t in (t1, t2, t3, t4))

    return {
        "html_final": html_final,
        "strategy": strategy,
        "copy": copy_data,
        "html_composer": html_composer,
        "telemetry": {
            "stage1": t1, "stage2": t2, "stage3": t3, "stage4": t4,
            "tokens_total": tokens_total,
        },
    }


if __name__ == "__main__":
    print("This module is meant to be called from gsg_generate_lp.py --sequential")
    print("Or imported as: from gsg_pipeline_sequential import run_sequential_pipeline")
