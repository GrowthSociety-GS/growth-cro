"""GSG Creative Director V26.Z E2 — production de 3 thèses visuelles nommées.

Réponse à la faille #3 du diagnostic post-audit (pas de creative director) :
le concept "Laboratoire Botanique Vivant" produit par aura_compute existe
déjà MAIS flotte sans validation multi-route. ChatGPT recommandait Safe
Upgrade / Premium Leap / Bold Differentiation. Le verdict humanlike Phase 1
confirme : "polish encore checklist, pas thèse" — le moteur empile sans
trancher.

E2 résout en imposant une étape AVANT le mega-prompt :
1. generate_routes() : Sonnet produit 3 thèses visuelles distinctes nommées
   (Safe / Premium / Bold) basées sur Brand DNA + design_grammar + business
   context. Chaque route est UN PARTI-PRIS, pas une accumulation.
2. select_route() :
   - mode "auto" : Sonnet arbitre laquelle matche le mieux le brief
   - mode "safe|premium|bold" : Mathis choisit explicitement
   - mode "custom" : route fournie en JSON externe (override total)
3. La route SÉLECTIONNÉE devient un bloc fort dans le mega-prompt qui
   FORCE Sonnet à se discipliner sur UNE direction au lieu d'empiler
   toutes les techniques.

Architecture d'une route :
  {
    "name": "Editorial Press Tech",  // 2-4 mots, nommable, mémorable
    "risk_level": "premium",          // safe | premium | bold
    "aesthetic_philosophy": "...",    // 1-2 phrases qui définissent l'âme
    "layout_concept": "...",          // règles structurelles spécifiques
    "typography_thesis": {...},       // choix typo cohérents avec philosophie
    "color_thesis": {...},            // ratio dominant/accent + contrastes
    "motion_thesis": "...",           // 1 profil unique (pas combo)
    "emotional_promise": "...",       // ce que le visiteur DOIT ressentir
    "signature_elements": [...],      // 3-5 éléments distinctifs nommables
    "must_not_do": [...],             // 5 patterns interdits pour CETTE route
    "fits_when": "..."                // contexte brief où cette route excelle
  }

Coût : ~$0.08 par run (1 call gen 3 routes ~3K out + 1 call arbitrage ~500 out).

Usage CLI :
    python3 skills/growth-site-generator/scripts/creative_director.py \\
        --client weglot \\
        --page-type listicle \\
        --target-url "https://www.weglot.com" \\
        [--mode auto|safe|premium|bold|custom] \\
        [--custom-route-file path.json] \\
        [--output data/_routes_<client>.json]

Usage module :
    from creative_director import generate_routes, select_route, render_creative_route_block
    routes = generate_routes(brand_dna, design_grammar, business_context, page_type)
    selected = select_route(routes, brand_dna, mode="auto")
    block = render_creative_route_block(selected)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Literal, Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
SONNET_MODEL = "claude-sonnet-4-5-20250929"

RouteMode = Literal["auto", "safe", "premium", "bold", "custom"]


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json\n"):
            text = text[5:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Étape 1 : Generate 3 routes
# ─────────────────────────────────────────────────────────────────────────────

GENERATE_ROUTES_SYSTEM = """Tu es **directeur créatif senior** (15+ ans, agences top-tier type Pentagram, Wieden+Kennedy, R/GA). Tu reçois un brief client et tu produis **EXACTEMENT 3 directions créatives distinctes nommées** pour la LP : Safe Upgrade, Premium Leap, Bold Differentiation.

## RÈGLE D'OR — Trancher, pas accumuler

Ces 3 routes ne sont pas des "options de paramétrage". Ce sont 3 **thèses visuelles complètes** qui se contredisent partiellement. Chaque route :
- A UN parti-pris fort qu'on peut nommer en 2-4 mots
- Fait des choix qui excluent les autres routes (pas un mille-feuille)
- Doit être TENABLE jusqu'au bout (pas un manifeste, un vrai design system)

## LES 3 ROUTES À PRODUIRE

### Safe Upgrade (risk_level: safe)
Améliore l'existant SANS choquer le client conservateur. Polish raffiné, codes du marché respectés, signature légèrement présente. Pour clients prudents, marques fortes, refonte light. Score plafond ~70-75/80 humanlike.

### Premium Leap (risk_level: premium)
Élève la marque au niveau "top 0.001% de sa catégorie". Ose des choix éditoriaux assumés (typo display unique, asymétrie marquée, voix tranchée). Risque modéré. Pour clients ambitieux qui veulent sortir du lot mais pas perdre la cible cœur. Score plafond ~80-85/80 humanlike.

### Bold Differentiation (risk_level: bold)
Crée un territoire visuel **mémorable et déstabilisant**. Sacrifice de patterns du secteur pour gagner une signature unique. Pour startups qui doivent émerger, lancement offre, marché saturé. Score plafond ~85-90+/80 humanlike (mais risque de rejet client +30%).

## CONTRAINTES NON-NÉGOCIABLES

Toutes les routes DOIVENT respecter :
- Brand DNA palette (les couleurs primary du brand)
- Brand DNA voice tokens (forbidden words, tone)
- Design Grammar anti_ai_patterns (interdits absolus)
- Design Grammar quality_gates (seuils chiffrés WCAG, brand_fidelity, etc.)

Une route NE PEUT PAS contredire ces contraintes — elle s'inscrit dedans en FAISANT DES CHOIX.

## OUTPUT JSON STRICT

{{
  "client": "{client}",
  "page_type": "{page_type}",
  "routes": [
    {{
      "name": "<2-4 mots, mémorable, nommable, ex: 'Editorial Press Tech', 'Quiet Luxury Data', 'Brutalist SaaS Warm', 'Heritage French Modern'>",
      "risk_level": "safe",
      "aesthetic_philosophy": "<1-2 phrases qui définissent l'âme — ce que cette route AFFIRME et REFUSE>",
      "layout_concept": "<règle structurelle distinctive — pas générique. Ex: 'Hero asymétrique 60/40 avec colonne sidebar éditoriale + main grid 12 cols sur desktop, single-col mobile avec drop caps'>",
      "typography_thesis": {{
        "display": "<font precise + weight + treatment>",
        "body": "<font + weight>",
        "scale_attitude": "<ex: 'oversized hero 96px → mid 64px → body 18px, ratio 1.5'>",
        "signature_treatment": "<ex: 'drop cap géant first paragraph italique + small caps headers' OR 'mixed weights light/black juxtaposés'>"
      }},
      "color_thesis": {{
        "dominant_role": "<bg, hero, accent>",
        "ratio": "<ex: '70% neutral / 25% brand primary / 5% accent contrast'>",
        "contrast_attitude": "<ex: 'high contrast monochrome + 1 burst couleur' OR 'warm earthy harmony'>"
      }},
      "motion_thesis": "<UN profil unique. Ex: 'Inertia lente cubic-bezier(0.23,1,0.32,1) 0.8s — pas de spring, pas de bounce' OR 'Snap brutal cubic-bezier(0.16,1,0.3,1) 0.25s — entrées sèches sans rebond'>",
      "emotional_promise": "<ce que le visiteur DOIT ressentir en 30 sec. Ex: 'Confiance instituionnelle + curiosité éditoriale' OR 'Énergie tech mais chaleur humaine'>",
      "signature_elements": [
        "<3-5 éléments distinctifs NOMMABLES — pas 'mesh gradient' générique mais 'mesh gradient bleu nuit en bas du hero seulement, fade vers neutral pour ouvrir le scroll'>",
        ...
      ],
      "must_not_do": [
        "<5 patterns interdits SPÉCIFIQUEMENT pour cette route. Ex pour Premium Editorial: 'gradients animés multi-couleurs (pas une route éditoriale)', 'icones outlined générique (sentent le SaaS template)'>"
      ],
      "fits_when": "<phrase qui décrit le contexte brief où cette route excelle. Ex: 'Marque B2B SaaS établie qui cherche premium positioning sans perdre crédibilité technique'>"
    }},
    {{ "name": ..., "risk_level": "premium", ... }},
    {{ "name": ..., "risk_level": "bold", ... }}
  ]
}}

JSON only, pas de markdown, sois TRANCHANT et SPÉCIFIQUE — pas de formules creuses type "design moderne et élégant"."""


def generate_routes(brand_dna: dict, design_grammar: dict,
                    business_context: str, page_type: str,
                    client: str, target_url: str = "",
                    model: str = SONNET_MODEL, verbose: bool = True) -> dict:
    """Génère 3 routes créatives nommées via Sonnet.

    Returns:
      {
        "client": "...",
        "page_type": "...",
        "routes": [
          {"name": "...", "risk_level": "safe", ...},
          {"name": "...", "risk_level": "premium", ...},
          {"name": "...", "risk_level": "bold", ...}
        ],
        "tokens_in": int, "tokens_out": int
      }
    """
    # Compact brand summary (palette + voice + image direction)
    vt = brand_dna.get("visual_tokens") or {}
    voice = brand_dna.get("voice_tokens") or {}
    img_dir = brand_dna.get("image_direction") or {}
    colors = vt.get("colors") or {}
    typo = vt.get("typography") or {}
    palette = colors.get("palette_full") or []

    brand_summary = f"""## Brand DNA (extrait compact)

Palette dominante: {', '.join(c.get('hex','?') for c in palette[:5])}
Typo brand: h1={typo.get('h1', {}).get('family', '?')} / body={typo.get('body', {}).get('family', '?')}
Voice tone: {', '.join((voice.get('tone') or [])[:3])}
Voice forbidden words: {', '.join((voice.get('forbidden_words') or [])[:5])}
Voice CTA verbs préférés: {', '.join((voice.get('preferred_cta_verbs') or [])[:3])}
Image direction signature: {img_dir.get('signature_visual_motif', '(non spécifié)')}
"""

    # Compact design_grammar (anti-patterns + composition)
    dg_summary = ""
    if design_grammar:
        bfp = design_grammar.get("brand_forbidden_patterns") or {}
        global_ai = bfp.get("global_anti_ai_patterns") or []
        cr = design_grammar.get("composition_rules") or {}
        asym = (cr.get("asymmetry") or {}).get("rule", "")
        density_max = (cr.get("density") or {}).get("max_elements_per_section_above_fold")
        if global_ai or asym:
            dg_summary = "## Design Grammar contraintes\n\n"
            if global_ai:
                dg_summary += "Anti-patterns brand interdits (toutes routes doivent les éviter):\n"
                for p in global_ai[:8]:
                    dg_summary += f"  - {p}\n"
            if asym:
                dg_summary += f"\nComposition rule: {asym}\n"
            if density_max:
                dg_summary += f"Densité max above-fold: {density_max} éléments\n"

    user_msg = f"""# CLIENT : {client.upper()} ({target_url})
# PAGE TYPE : {page_type}

{brand_summary}

{dg_summary}

## BUSINESS CONTEXT
{business_context[:5000] if business_context else '(brief minimal — pas de context business spécifique)'}

Produis maintenant les 3 routes créatives Safe/Premium/Bold pour cette LP. Tranche."""

    system_prompt = GENERATE_ROUTES_SYSTEM.format(client=client, page_type=page_type)

    import anthropic
    client_api = anthropic.Anthropic()
    if verbose:
        print(f"  → Sonnet creative_director generate_routes (prompt={len(user_msg)+len(system_prompt)} chars) ...", flush=True)
    msg = client_api.messages.create(
        model=model,
        max_tokens=7000,  # Up from 4500 : 3 routes JSON détaillées peuvent dépasser
        temperature=0.7,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = msg.content[0].text
    if verbose:
        print(f"  ← in={msg.usage.input_tokens} out={msg.usage.output_tokens} stop={msg.stop_reason}", flush=True)

    def _try_parse(t: str) -> Optional[dict]:
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", t)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
        return None

    text = _strip_fences(raw)
    result = _try_parse(text)
    tokens_in = msg.usage.input_tokens
    tokens_out = msg.usage.output_tokens

    # Retry if JSON tronqué (stop=max_tokens)
    if result is None:
        if verbose:
            print("  ⚠️  JSON parse failed (likely max_tokens hit), retrying with concise reminder...", flush=True)
        retry_user = user_msg + "\n\n## RAPPEL CRITIQUE : Le JSON DOIT être COMPLET et VALIDE. 3 routes max, sois CONCIS sur les descriptions (3-5 mots max par signature_element, must_not_do en 5-10 mots). Ferme TOUS les crochets et accolades."
        msg2 = client_api.messages.create(
            model=model,
            max_tokens=8000,
            temperature=0.4,
            system=system_prompt,
            messages=[{"role": "user", "content": retry_user}],
        )
        raw2 = msg2.content[0].text
        if verbose:
            print(f"  ← retry in={msg2.usage.input_tokens} out={msg2.usage.output_tokens} stop={msg2.stop_reason}", flush=True)
        text2 = _strip_fences(raw2)
        result = _try_parse(text2)
        tokens_in += msg2.usage.input_tokens
        tokens_out += msg2.usage.output_tokens
        if result is None:
            raise ValueError(f"Routes generation failed after retry. Raw first 500: {text2[:500]}")

    result["tokens_in"] = tokens_in
    result["tokens_out"] = tokens_out
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Étape 2 : Select route
# ─────────────────────────────────────────────────────────────────────────────

SELECT_ROUTE_SYSTEM = """Tu es **directeur créatif senior** + stratège brand. Tu reçois 3 routes créatives proposées + le contexte client + l'audit. Tu choisis LA route qui matche le mieux le contexte business + le potentiel de la marque, et tu justifies brièvement.

Règles de sélection :
1. La route doit servir l'OBJECTIF de la LP (audit + business context).
2. Ne pas surestimer la tolérance au risque du client. Si marque institutionnelle conservatrice → Safe. Si startup qui doit émerger → Bold OK.
3. Ne pas sous-estimer le besoin de différenciation. Si marché saturé de templates SaaS → Premium ou Bold.
4. Si le client a déjà une marque visuelle forte → Safe ou Premium (Bold risque de la trahir).
5. Si la marque est faible/générique aujourd'hui → Premium ou Bold (Safe ne change rien).

Output JSON STRICT :
{
  "selected_route_name": "<name de la route choisie verbatim depuis l'input>",
  "selected_risk_level": "safe|premium|bold",
  "selection_reason": "<2-3 phrases tranchées : pourquoi cette route et pas les 2 autres>",
  "confidence": <0.0-1.0>,
  "alternative_route_name": "<nom de la 2e route la plus pertinente, si besoin pivot>",
  "warning_if_any": "<1 phrase si la route choisie a un risque que Mathis doit valider, ou null>"
}
JSON only."""


def select_route(routes_data: dict, brand_dna: dict, business_context: str,
                 mode: RouteMode = "auto",
                 custom_route_path: Optional[pathlib.Path] = None,
                 model: str = SONNET_MODEL, verbose: bool = True) -> dict:
    """Sélectionne une route parmi les 3, ou charge une route custom.

    Modes :
      "auto"    : Sonnet arbitre
      "safe"    : prend la route risk_level=safe sans appeler Sonnet
      "premium" : idem
      "bold"    : idem
      "custom"  : charge depuis custom_route_path (override total)

    Returns :
      {
        "route": <le dict de la route sélectionnée>,
        "selection_meta": {"reason": "...", "confidence": ..., "warning": ..., "mode": "..."}
      }
    """
    if mode == "custom":
        if not custom_route_path or not custom_route_path.exists():
            raise ValueError(f"--mode custom requires --custom-route-file (got: {custom_route_path})")
        route = json.loads(custom_route_path.read_text())
        return {
            "route": route,
            "selection_meta": {
                "reason": f"Custom route loaded from {custom_route_path.name}",
                "confidence": 1.0,
                "warning": None,
                "mode": "custom",
            },
        }

    routes = routes_data.get("routes") or []
    if len(routes) < 3:
        raise ValueError(f"Expected 3 routes, got {len(routes)}")

    if mode in ("safe", "premium", "bold"):
        target = next((r for r in routes if r.get("risk_level") == mode), None)
        if not target:
            raise ValueError(f"No route with risk_level={mode} found")
        return {
            "route": target,
            "selection_meta": {
                "reason": f"Mode '{mode}' explicitement choisi",
                "confidence": 1.0,
                "warning": None,
                "mode": mode,
            },
        }

    # mode == "auto" → Sonnet arbitre
    routes_summary = "\n\n".join(
        f"### Route {i+1}: {r.get('name')} (risk={r.get('risk_level')})\n"
        f"  Philosophy: {r.get('aesthetic_philosophy', '?')}\n"
        f"  Emotional promise: {r.get('emotional_promise', '?')}\n"
        f"  Layout: {r.get('layout_concept', '?')}\n"
        f"  Fits when: {r.get('fits_when', '?')}\n"
        for i, r in enumerate(routes)
    )

    bd_summary = (
        f"Brand: {brand_dna.get('identity', {}).get('brand_name', '?')} "
        f"({brand_dna.get('identity', {}).get('category', '?')}). "
        f"Position: {brand_dna.get('identity', {}).get('market_position', '?')}"
    )

    user_msg = f"""## Contexte client
{bd_summary}

## Business context (brief de mission)
{business_context[:3000] if business_context else '(brief minimal)'}

## 3 routes proposées
{routes_summary}

Tranche : laquelle des 3 routes est la bonne pour cette LP ? Justifie brièvement."""

    import anthropic
    client_api = anthropic.Anthropic()
    if verbose:
        print(f"  → Sonnet creative_director select_route (prompt={len(user_msg)} chars) ...", flush=True)
    msg = client_api.messages.create(
        model=model,
        max_tokens=600,
        temperature=0.2,
        system=SELECT_ROUTE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = msg.content[0].text
    if verbose:
        print(f"  ← in={msg.usage.input_tokens} out={msg.usage.output_tokens}", flush=True)
    text = _strip_fences(raw)
    try:
        verdict = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError(f"Selection parse failed. Raw: {text[:500]}")
        verdict = json.loads(m.group(0))

    selected_name = verdict.get("selected_route_name", "")
    selected = next(
        (r for r in routes if r.get("name", "").strip().lower() == selected_name.strip().lower()),
        None,
    )
    if not selected:
        # Fallback : essayer par risk_level
        risk = verdict.get("selected_risk_level", "premium")
        selected = next((r for r in routes if r.get("risk_level") == risk), routes[1])

    return {
        "route": selected,
        "selection_meta": {
            "reason": verdict.get("selection_reason", ""),
            "confidence": verdict.get("confidence", 0.5),
            "warning": verdict.get("warning_if_any"),
            "alternative_route_name": verdict.get("alternative_route_name"),
            "mode": "auto",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Étape 3 : Render bloc pour mega-prompt
# ─────────────────────────────────────────────────────────────────────────────

def render_creative_route_block(route: dict, selection_meta: dict | None = None) -> str:
    """Format la route sélectionnée en bloc texte pour mega-prompt gsg_generate_lp.

    Le bloc doit être OPÉRATIONNEL et CONTRAIGNANT — Sonnet doit comprendre
    qu'il a UN parti-pris à tenir, pas une option à mixer.
    """
    if not route:
        return ""

    name = route.get("name", "(unnamed)")
    risk = route.get("risk_level", "?")
    philosophy = route.get("aesthetic_philosophy", "")
    layout = route.get("layout_concept", "")
    typo_th = route.get("typography_thesis") or {}
    color_th = route.get("color_thesis") or {}
    motion_th = route.get("motion_thesis", "")
    emo_promise = route.get("emotional_promise", "")
    sig_elements = route.get("signature_elements") or []
    must_not = route.get("must_not_do") or []

    block = f"""## CREATIVE ROUTE — "{name}" ({risk.upper()})

⚠️ TU AS UNE THÈSE, PAS UN MENU. Cette route est UN PARTI-PRIS UNIFIÉ. Tu ne mélanges pas avec d'autres routes. Tu n'empiles pas des techniques en plus.

### Philosophie
{philosophy}

### Promesse émotionnelle (ce que le visiteur DOIT ressentir en 30 sec)
{emo_promise}

### Layout concept
{layout}

### Typography thesis
- Display : {typo_th.get('display', '?')}
- Body : {typo_th.get('body', '?')}
- Scale : {typo_th.get('scale_attitude', '?')}
- Signature treatment : {typo_th.get('signature_treatment', '?')}

### Color thesis
- Dominant : {color_th.get('dominant_role', '?')}
- Ratio : {color_th.get('ratio', '?')}
- Contrast attitude : {color_th.get('contrast_attitude', '?')}

### Motion thesis (UN profil, pas un combo)
{motion_th}

### Signature elements (DOIVENT être tous présents et nommables dans le HTML final)
"""
    for el in sig_elements:
        block += f"  - {el}\n"

    block += """
### Must not do (interdit pour CETTE route — même si d'autres routes l'autorisent)
"""
    for item in must_not:
        block += f"  - {item}\n"

    if selection_meta:
        block += f"""
### Selection rationale
- Mode : {selection_meta.get('mode', '?')}
- Confidence : {selection_meta.get('confidence', '?')}
- Reason : {selection_meta.get('reason', '?')}
"""
        if selection_meta.get("warning"):
            block += f"- ⚠️  WARNING : {selection_meta['warning']}\n"

    return block


# ─────────────────────────────────────────────────────────────────────────────
# CLI standalone
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", default="listicle")
    ap.add_argument("--target-url", default="")
    ap.add_argument("--context-file", help="Path to .md/.txt with business context")
    ap.add_argument("--mode", choices=["auto", "safe", "premium", "bold", "custom"], default="auto")
    ap.add_argument("--custom-route-file", help="Path to custom route JSON (mode=custom)")
    ap.add_argument("--output", help="Path to save routes JSON (default: data/_routes_<client>.json)")
    args = ap.parse_args()

    DATA = ROOT / "data" / "captures"
    bd_fp = DATA / args.client / "brand_dna.json"
    if not bd_fp.exists():
        sys.exit(f"❌ {bd_fp} not found")
    brand_dna = json.loads(bd_fp.read_text())

    # Load design_grammar
    dg_dir = DATA / args.client / "design_grammar"
    design_grammar = {}
    if dg_dir.is_dir():
        for json_file in ("composition_rules.json", "brand_forbidden_patterns.json", "quality_gates.json"):
            fp = dg_dir / json_file
            if fp.exists():
                try:
                    design_grammar[json_file.replace(".json", "")] = json.loads(fp.read_text())
                except json.JSONDecodeError:
                    pass

    business_context = ""
    if args.context_file:
        cf = pathlib.Path(args.context_file)
        if cf.exists():
            business_context = cf.read_text()

    print(f"\n══ Creative Director — {args.client} / {args.page_type} ══\n")
    print("[1/2] Generate 3 routes (Safe + Premium + Bold)...")
    routes_data = generate_routes(brand_dna, design_grammar, business_context,
                                   args.page_type, args.client, args.target_url)
    print("\n  → 3 routes generated:")
    for r in routes_data.get("routes", []):
        print(f"    [{r.get('risk_level', '?'):8s}] {r.get('name', '?')}")
        print(f"             {r.get('aesthetic_philosophy', '?')[:100]}...")

    # Save raw routes
    out_routes_fp = pathlib.Path(args.output or (ROOT / "data" / f"_routes_{args.client}.json"))
    out_routes_fp.parent.mkdir(parents=True, exist_ok=True)
    out_routes_fp.write_text(json.dumps(routes_data, ensure_ascii=False, indent=2))
    print(f"\n  Routes saved: {out_routes_fp.relative_to(ROOT)}")

    print(f"\n[2/2] Select route (mode={args.mode})...")
    custom_path = pathlib.Path(args.custom_route_file) if args.custom_route_file else None
    selection = select_route(routes_data, brand_dna, business_context,
                              mode=args.mode, custom_route_path=custom_path)

    print("\n══ SELECTED ROUTE ══")
    r = selection["route"]
    sm = selection["selection_meta"]
    print(f"  Name : {r.get('name')}")
    print(f"  Risk : {r.get('risk_level')}")
    print(f"  Mode : {sm.get('mode')}")
    print(f"  Confidence : {sm.get('confidence')}")
    print(f"  Reason : {sm.get('reason')}")
    if sm.get("warning"):
        print(f"  ⚠️  Warning: {sm['warning']}")

    # Save selection
    sel_fp = ROOT / "data" / f"_route_selected_{args.client}.json"
    sel_fp.write_text(json.dumps(selection, ensure_ascii=False, indent=2))
    print(f"\n  Selection saved: {sel_fp.relative_to(ROOT)}")

    # Render block preview
    block = render_creative_route_block(r, sm)
    print(f"\n══ MEGA-PROMPT BLOCK PREVIEW ({len(block)} chars) ══")
    print(block[:1500] + ("..." if len(block) > 1500 else ""))


if __name__ == "__main__":
    main()
