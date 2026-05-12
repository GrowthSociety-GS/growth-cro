#!/usr/bin/env python3
"""V23.2.fr — Rewrite ciblé style FR consultant pour les recos déjà générées.

Au lieu de régénérer tout le pipeline (intelligence layer + clustering + USP), on
se contente de re-formater le texte (`why`, `after`) des recos existantes en
appliquant le STYLE_GUIDE V23.2. Conserve criterion_id, ice_score, priority, etc.

Approche : 1 prompt PAR PAGE qui rewrite toutes ses recos d'un coup
(beaucoup moins cher que 1 prompt par reco — caching system + amortisation).

Skip si déjà rewritten (`_rewritten_v23_2: true` flag).

Usage:
    python3 recos_rewrite_fr.py --client japhy --page home
    python3 recos_rewrite_fr.py --all
    python3 recos_rewrite_fr.py --all --dry-run    # estime juste le coût
"""
from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import re
import sys
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"
SCRIPTS = pathlib.Path(__file__).resolve().parent

# Reuse env loader from reco_enricher_v13_api
sys.path.insert(0, str(SCRIPTS))
from reco_enricher_v13_api import _load_dotenv_if_needed  # noqa


MODEL = "claude-haiku-4-5-20251001"

# System prompt cachable (statique inter-pages, ~3000 tokens pour franchir seuil 2048)
SYSTEM_PROMPT = """Tu es un consultant CRO senior français. Ton job : réécrire les recommandations existantes pour qu'elles sonnent CONSULTANT et pas CLAUDE-LIKE.

Tu reçois des recos déjà valides en termes de DIAGNOSTIC. Tu changes UNIQUEMENT le texte (style, ton, ancrage client). La substance technique reste identique.

═══════════════════════════════════════════════════════════════════
CE QUE TU CHANGES (SEULEMENT)
═══════════════════════════════════════════════════════════════════

Pour chaque reco, tu réécris :
1. **after** : la directive concrète. Garder l'action, traduire les anglicismes, virer le jargon.
2. **why** : la justification. CITER le nom du client + son business model + sa persona. Style consultant pédagogique. Pas de "killer rule per_04", utiliser "règle bloquante zero proof concret".

Tu CONSERVES tel quel : `before`, `criterion_id`, `priority`, `ice_score`, `effort_hours`, `expected_lift_pct`, `implementation_notes`, et tous les autres champs.

═══════════════════════════════════════════════════════════════════
RÈGLES DE STYLE
═══════════════════════════════════════════════════════════════════

## TON
- Français professionnel naturel. Phrases courtes, verbes actifs.
- **Pédagogique sans condescendance** : explique le POURQUOI psychologique avant le QUOI.
- **Direct** : pas de "il convient de", "il est nécessaire de", "il pourrait être pertinent". Tu décides, tu justifies.

## DICTIONNAIRE TERMES INTERDITS
N'écris JAMAIS dans le `after` ou `why` :

- "score" / "scoring rule" / "criterion" → utiliser "ce point", "cette règle CRO", ou nommer la règle
- "killer rule" / "killer_violations" / "killer" → "règle bloquante" ou "facteur éliminatoire"
- "fallback" → "version de secours" ou rien
- "pillar" → "pilier" (FR)
- "threshold" → "seuil"
- "override" → "remplacer" / "outrepasser"
- "applicability" → "pertinence"
- "tier" / "rank" → "niveau" / "rang"
- "amplify" / "amplification" → "renforcer" / "valoriser" / "mettre en relief"
- "lift" (verbe ou nom dans le texte) → "améliorer" / "amélioration" / "progression"
- "cap" / "capped" → "plafond" / "plafonné"

Anglicismes paresseux à virer :
- "leverager" → "exploiter"
- "drive" / "driver" → "générer", "produire"
- "matcher" → "correspondre à"
- "pusher" → "pousser" / "déployer"
- "shipper" → "livrer" / "déployer"
- "tweaker" → "ajuster"
- "brainstormer" → "réfléchir"
- "challenger" → "remettre en question"
- "rollback" → "annulation" / "rétro-pédalage"

## CITATION CLIENT OBLIGATOIRE dans `why`
Le `why` DOIT contenir, textuellement :
1. **Nom du client** (ex: "Japhy", "Spendesk", "Hellofresh") — pas "le client", "la marque", "ce site"
2. **Business model** (ex: "DTC subscription nutrition animale", "SaaS B2B finance", "marketplace e-commerce")
3. **Persona cible** (ex: "parents de chiens anxieux", "CFO scale-up", "consommateurs prix-conscients")

Format-type recommandé : *"Pour [Client], qui adresse [persona] en [business_model], cette modification déclenche [mécanisme psychologique] et corrige [problème observé]."*

═══════════════════════════════════════════════════════════════════
EXEMPLES OR (style à reproduire)
═══════════════════════════════════════════════════════════════════

### Exemple 1 — hero_03 CTA refonte (DTC Japhy)
- after AVANT: "Update CTA copy to first-person + add proof block. Tweaker la couleur si besoin pour driver le clic."
- after APRÈS: "Remplacer le texte du CTA par 'Créer le profil de mon animal — 2 min'. Conserver le lien /profile-builder/ et la couleur orange Japhy. Augmenter à 220×48px (seuil tactile 44px Apple HIG). Ajouter une micro-copy juste sous le CTA : '12 400 chiens nourris depuis 2019'."

- why AVANT: "Killer rule hero_03 violated, ratio 1:1 broken. Pillar hero score capped at 6/18. Need to leverage the USP and amplify."
- why APRÈS: "Pour Japhy, qui adresse des parents de chiens anxieux en DTC subscription nutrition canine, le passage à la 1ère personne ('mon animal' au lieu de 'son menu') active l'identification émotionnelle (Cialdini autorité + commitment). La micro-copy chiffrée transforme la friction d'engagement en preuve sociale immédiate, attaquant directement l'anxiété d'un primo-acheteur dans une catégorie premium (croquettes sur-mesure 30-50€/mois)."

### Exemple 2 — per_04 zero proof (SaaS Spendesk)
- after AVANT: "Add social proof badges + customer logos ATF to fix per_04 killer."
- after APRÈS: "Ajouter sous le H1 une bande horizontale 'Plus de 5 000 entreprises gèrent leurs dépenses avec Spendesk — Doctolib, Algolia, Aircall'. Inclure 3-4 logos client identifiables européens en grayscale 64px de hauteur."

- why AVANT: "Per_04 killer rule violated, no concrete proof detected. Score capped at 10/24 on persuasion pillar. Adds trust signal."
- why APRÈS: "Pour Spendesk, en SaaS B2B finance pour CFOs et DAFs de scale-ups, l'absence de preuve sociale au-dessus de la ligne de flottaison échoue le test des 5 secondes : le visiteur ne valide pas 'pour qui' et 'crédible' simultanément. La règle bloquante 'zéro proof concret' plafonne le pilier persuasion à 10/24 tant qu'aucune preuve concrète n'est ajoutée. Logos clients reconnaissables + chiffre agrégé adressent l'autorité (Cialdini) et le besoin de validation par les pairs."

### Exemple 3 — per_01 feature dump (SaaS Notion)
- after AVANT: "Refactor features list with benefit ladder, leverage Jobs to be Done framework, ship copy update."
- after APRÈS: "Restructurer en 4 blocs Feature → Bénéfice Émotionnel : (1) 'Centralisez tout' → 'Vos équipes arrêtent de jongler entre 8 outils' ; (2) 'Templates partagés' → '60% de temps de setup gagné par projet' ; (3) 'Mode collaboratif temps réel' → 'Décisions prises en réunion, pas après' ; (4) 'API REST' → 'Connecté à votre stack existante en 1 jour'. Garder les 8 features restantes en accordion 'Voir toutes les fonctionnalités'."

- why AVANT: "Per_01 killer violation. Feature dump without benefit translation. Score capped at 8/24. Need to leverage benefit laddering to drive engagement."
- why APRÈS: "Pour Notion, qui cible des équipes produit et ops en SaaS productivité, les listes de features bridgent rarement les bénéfices (règle bloquante 'translation feature→bénéfice <50%' — Christensen Jobs to be Done). La translation feature → bénéfice fonctionnel → bénéfice émotionnel triple le taux de mémorisation (Means-End Chain Theory). Le pourcentage chiffré '60% de temps gagné' force le visiteur à projeter le ROI immédiatement."

### Exemple 4 — funnel_04 halt step 1 (DTC AndtheGreen)
- after AVANT: "Quiz halts on step 1, fix the next button. Maybe ARIA roles. Tweaker la zone tactile if needed."
- after APRÈS: "Auditer le bouton 'Suivant' du step 1 : (1) Vérifier qu'il porte les attributs ARIA role='button' + aria-label explicite ; (2) Tester la zone tactile sur mobile 390px (cible 44×44px Apple HIG) ; (3) Standardiser l'événement à un click natif (pas un @keyup ou tap custom). Sur la page résultat finale, ajouter une CTA explicite 'Découvrir mes croquettes recommandées' (verbe action + bénéfice)."

- why AVANT: "Funnel halts at step 1 due to no_next_button heuristic failure. Vue.js custom component. Threshold doctrine 50% drop. Add accessibility ARIA. Killer on funnel_04."
- why APRÈS: "Pour AndtheGreen, en DTC subscription nutrition canine pour parents soucieux du bien-être de leur chien, un quiz qui bloque au step 1 zéro le ROI de toute la stratégie d'acquisition (16% du trafic atterrit ici). Le seuil doctrine d'abandon dépasse 50% sur les funnels custom non-accessibles. Le bouton ARIA + zone tactile 44px adresse 80% des cas selon les benchmarks WCAG 2.1, et l'ajout d'un CTA bénéfice sur la page résultat évite le drop-off post-completion."

### Exemple 5 — psy_01 urgence manquante (Marketplace TravelBase)
- after AVANT: "Add urgency signal under price. Avoid fake urgency, leverage real stock data. Don't push manipulation."
- after APRÈS: "Ajouter sous le prix une bande discrète 'Plus que 4 places à ce tarif' (mise à jour temps réel via API stock). Sur la modal de réservation, afficher 'Cette offre se termine dans 2j 14h' (countdown réel basé sur la fin de la promo). Ne PAS faire de fake urgency type 'Quelqu'un vient de réserver !' — mensonge détecté = perte de confiance."

- why AVANT: "No urgency or scarcity signal detected. Capped on psy pillar. Use Cialdini scarcity. Threshold guardrail pushy_urgency_without_risk_reversal must be respected."
- why APRÈS: "Pour TravelBase, en marketplace voyage pour familles à budget contraint, l'absence d'urgence plafonne la conversion en phase de décision (Schwartz Awareness 'product_aware'). Le levier de la rareté authentique (Cialdini scarcity, basé sur le stock RÉEL) accélère la décision sans manipulation, et respecte le garde-fou 'urgence sans réassurance contre-productive' du playbook."

═══════════════════════════════════════════════════════════════════
RAPPELS FINAUX
═══════════════════════════════════════════════════════════════════

- Tu RECEVRAS le `before` mais tu NE LE RÉÉCRIS PAS (il est factuel — citation du H1, CTA, classe DOM, etc.)
- Tu RÉÉCRIS UNIQUEMENT `after` et `why`.
- Si la reco originale est déjà bien rédigée en français consultant (sans jargon, citation client présente), tu peux la garder quasi-identique mais préserver l'output JSON propre.
- Pas de "j'ai amélioré...", "j'espère que..." — output JSON pur, point.

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════

Tu réponds UNIQUEMENT avec un objet JSON :

{
  "rewrites": [
    {
      "criterion_id": "<id de la reco>",
      "after": "<after rewritten>",
      "why": "<why rewritten>"
    },
    ...
  ]
}

L'ordre des rewrites doit matcher l'ordre des recos en input. Si tu ne peux pas rewriter une reco (ambiguë, vide), retourne le `after` et `why` ORIGINAUX inchangés (pas de skip silencieux).

Pas de markdown, pas de prose en dehors du JSON, pas de "voilà" ou "j'espère que ça aide"."""


def _client_context_block(client: str, capture_dir: pathlib.Path) -> str:
    """Build a compact CLIENT_CONTEXT for the prompt."""
    info = {
        "client_name": client,
        "business_category": None,
        "persona_hint": None,
        "page_type": capture_dir.name,
    }
    # site_audit.json is canonical for businessCategory
    site_audit = capture_dir.parent / "site_audit.json"
    if site_audit.exists():
        try:
            sa = json.load(open(site_audit))
            info["business_category"] = sa.get("businessCategory") or sa.get("business_category")
            info["persona_hint"] = sa.get("persona") or sa.get("audience")
        except Exception:
            pass
    # client_intent.json for intent
    intent_f = capture_dir.parent / "client_intent.json"
    if intent_f.exists():
        try:
            d = json.load(open(intent_f))
            info["intent"] = d.get("primary_intent")
        except Exception:
            pass
    # Vision h1/cta for grounding
    vision_d = capture_dir / "vision_desktop.json"
    if vision_d.exists():
        try:
            v = json.load(open(vision_d))
            hero = v.get("hero") or {}
            h1 = hero.get("h1")
            if isinstance(h1, dict):
                info["h1_real"] = (h1.get("text") or "")[:80]
            cta = hero.get("primary_cta")
            if isinstance(cta, dict):
                info["cta_real"] = (cta.get("text") or "")[:50]
        except Exception:
            pass

    return (
        "## CLIENT_CONTEXT\n"
        + "\n".join(f"- {k}: {v}" for k, v in info.items() if v)
    )


def _build_user_prompt(client: str, capture_dir: pathlib.Path, recos: list[dict]) -> str:
    """Build the user prompt: client context + N recos to rewrite."""
    ctx = _client_context_block(client, capture_dir)

    recos_block = []
    for i, r in enumerate(recos):
        recos_block.append(f"### RECO {i+1} — criterion_id={r.get('criterion_id') or r.get('cluster_id', '?')}")
        recos_block.append(f"- before: {(r.get('before') or '')[:600]}")
        recos_block.append(f"- after: {(r.get('after') or '')[:600]}")
        recos_block.append(f"- why: {(r.get('why') or '')[:600]}")
        recos_block.append("")

    return (
        ctx + "\n\n"
        "## RECOS À RÉÉCRIRE\n\n"
        + "\n".join(recos_block)
        + f"\n\nRéécris UNIQUEMENT `after` et `why` de chacune des {len(recos)} recos ci-dessus, en respectant le STYLE_GUIDE. "
          "Le `before` reste tel quel (il est factuel). Output JSON strict avec l'array `rewrites`."
    )


async def rewrite_page(client_api, client: str, page: str, force: bool = False, dry_run: bool = False) -> dict:
    """Rewrite all non-fallback recos on a page in one prompt batch."""
    page_dir = CAPTURES / client / page
    indiv_path = page_dir / "recos_v13_final.json"
    cluster_path = page_dir / "recos_v21_cluster_final.json"

    rewritten_count = 0
    skipped_count = 0
    errors = []
    tokens_in = tokens_out = tokens_cached_read = tokens_cached_write = 0
    loop = asyncio.get_event_loop()

    # Process individual recos
    if indiv_path.exists():
        d = json.load(open(indiv_path))
        recos = d.get("recos") or []
        # Filter: only valid recos that haven't been rewritten yet
        targets = [r for r in recos if not r.get("_fallback") and not r.get("_skipped")
                                       and not r.get("_superseded_by")
                                       and (force or not r.get("_rewritten_v23_2"))]
        if targets:
            user_prompt = _build_user_prompt(client, page_dir, targets)
            if dry_run:
                tokens_in += len(user_prompt) // 4
                tokens_out += 300 * len(targets)  # rough estimate
            else:
                try:
                    resp = await loop.run_in_executor(
                        None,
                        lambda: client_api.messages.create(
                            model=MODEL,
                            max_tokens=8192,  # need room for N×~300 token rewrites
                            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                            messages=[{"role": "user", "content": user_prompt}],
                        ),
                    )
                    text = resp.content[0].text if resp.content else ""
                    parsed = _parse_json_strict(text)
                    if parsed and isinstance(parsed.get("rewrites"), list):
                        # Map by criterion_id to apply rewrites
                        rewrites_by_id = {r.get("criterion_id"): r for r in parsed["rewrites"] if r.get("criterion_id")}
                        for r in recos:
                            if r in targets:
                                rid = r.get("criterion_id")
                                rw = rewrites_by_id.get(rid)
                                if rw:
                                    r["after"] = rw.get("after") or r.get("after")
                                    r["why"] = rw.get("why") or r.get("why")
                                    r["_rewritten_v23_2"] = True
                                    rewritten_count += 1
                                else:
                                    skipped_count += 1
                                    errors.append(f"no_match:{rid}")
                    else:
                        errors.append("individual:parse_failed")
                    tokens_in += getattr(resp.usage, "input_tokens", 0)
                    tokens_out += getattr(resp.usage, "output_tokens", 0)
                    tokens_cached_read += getattr(resp.usage, "cache_read_input_tokens", 0) or 0
                    tokens_cached_write += getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
                except Exception as e:
                    errors.append(f"individual:{type(e).__name__}:{str(e)[:120]}")

            if not dry_run and rewritten_count > 0:
                d["recos"] = recos
                d["_rewrite_v23_2_applied"] = True
                tmp = indiv_path.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
                tmp.replace(indiv_path)

    # Process cluster recos (same pattern)
    if cluster_path.exists():
        dc = json.load(open(cluster_path))
        clusters = dc.get("clusters") or []
        targets_c = [c for c in clusters if not c.get("_fallback")
                                            and (force or not c.get("_rewritten_v23_2"))]
        if targets_c:
            # Build pseudo-recos shape for the prompt (use cluster_id as criterion_id)
            pseudo = []
            for c in targets_c:
                pseudo.append({
                    "criterion_id": c.get("cluster_id"),
                    "before": c.get("before") or c.get("problem_headline", ""),
                    "after": c.get("after") or "",
                    "why": c.get("why") or "",
                })
            user_prompt = _build_user_prompt(client, page_dir, pseudo)
            if dry_run:
                tokens_in += len(user_prompt) // 4
                tokens_out += 300 * len(targets_c)
            else:
                try:
                    resp = await loop.run_in_executor(
                        None,
                        lambda: client_api.messages.create(
                            model=MODEL,
                            max_tokens=8192,
                            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                            messages=[{"role": "user", "content": user_prompt}],
                        ),
                    )
                    text = resp.content[0].text if resp.content else ""
                    parsed = _parse_json_strict(text)
                    if parsed and isinstance(parsed.get("rewrites"), list):
                        rw_by_id = {r.get("criterion_id"): r for r in parsed["rewrites"] if r.get("criterion_id")}
                        for c in clusters:
                            if c in targets_c:
                                rid = c.get("cluster_id")
                                rw = rw_by_id.get(rid)
                                if rw:
                                    c["after"] = rw.get("after") or c.get("after")
                                    c["why"] = rw.get("why") or c.get("why")
                                    c["_rewritten_v23_2"] = True
                                    rewritten_count += 1
                    tokens_in += getattr(resp.usage, "input_tokens", 0)
                    tokens_out += getattr(resp.usage, "output_tokens", 0)
                    tokens_cached_read += getattr(resp.usage, "cache_read_input_tokens", 0) or 0
                    tokens_cached_write += getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
                except Exception as e:
                    errors.append(f"cluster:{type(e).__name__}:{str(e)[:120]}")

            if not dry_run and rewritten_count > 0:
                dc["clusters"] = clusters
                dc["_rewrite_v23_2_applied"] = True
                tmp = cluster_path.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(dc, ensure_ascii=False, indent=2))
                tmp.replace(cluster_path)

    return {
        "client": client,
        "page": page,
        "rewritten": rewritten_count,
        "skipped": skipped_count,
        "errors": errors,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cache_read": tokens_cached_read,
        "cache_write": tokens_cached_write,
    }


def _parse_json_strict(text: str) -> Optional[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json\n"):
            text = text[5:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None


async def main_async(targets: list, max_concurrent: int, force: bool, dry_run: bool):
    if dry_run:
        client_api = None
    else:
        import anthropic
        client_api = anthropic.Anthropic(timeout=90.0, max_retries=3)

    sem = asyncio.Semaphore(max_concurrent)
    loop = asyncio.get_event_loop()

    async def _one(c, p):
        async with sem:
            return await loop.run_in_executor(None, lambda: asyncio.run(rewrite_page(client_api, c, p, force, dry_run)))

    # Use thread executor not asyncio rewrite
    async def _direct(c, p):
        return await rewrite_page(client_api, c, p, force, dry_run)

    tasks = [_direct(c, p) for c, p in targets]
    # Run with concurrency limit
    sem2 = asyncio.Semaphore(max_concurrent)
    async def _bound(t):
        async with sem2:
            return await t
    results = await asyncio.gather(*[_bound(t) for t in tasks])

    total_rw = sum(r["rewritten"] for r in results)
    total_in = sum(r["tokens_in"] for r in results)
    total_out = sum(r["tokens_out"] for r in results)
    total_cr = sum(r["cache_read"] for r in results)
    total_cw = sum(r["cache_write"] for r in results)
    errors = [e for r in results for e in r.get("errors", [])]

    if dry_run:
        # Estimate: input × $1/M + output × $5/M
        cost = total_in * 1 / 1_000_000 + total_out * 5 / 1_000_000
        print("\n══ DRY RUN ══")
        print(f"Pages : {len(results)}")
        print(f"Rewrites estimés : ~{total_in*4//150} recos (basé sur tokens input)")
        print(f"Input tokens estimés : {total_in:,}")
        print(f"Output tokens estimés : {total_out:,}")
        print(f"Cost estimate (no cache) : ${cost:.2f}")
        print(f"Cost with cache (-50%) : ${cost*0.5:.2f}")
    else:
        cost_real = (
            (total_in - total_cr) * 1 / 1_000_000  # uncached input
            + total_cw * 1.25 / 1_000_000          # cache write
            + total_cr * 0.1 / 1_000_000           # cache read
            + total_out * 5 / 1_000_000            # output
        )
        print("\n══ Rewrite complete ══")
        print(f"Pages : {len(results)}")
        print(f"Recos rewritten : {total_rw}")
        print(f"Tokens : {total_in:,} in / {total_out:,} out (cache: read={total_cr:,}, write={total_cw:,})")
        print(f"Cost : ${cost_real:.4f}")
        if errors:
            print(f"Errors ({len(errors)}) : {errors[:5]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-concurrent", type=int, default=10)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.all:
        for cd in sorted(CAPTURES.iterdir()):
            if not cd.is_dir() or cd.name.startswith(("_", ".")):
                continue
            for pd in sorted(cd.iterdir()):
                if pd.is_dir() and (pd / "recos_v13_final.json").exists():
                    targets.append((cd.name, pd.name))
    elif args.client and args.page:
        targets.append((args.client, args.page))
    else:
        ap.error("--client+--page OR --all")

    print(f"→ {len(targets)} pages, model={MODEL}, concurrency={args.max_concurrent}, dry-run={args.dry_run}")
    asyncio.run(main_async(targets, args.max_concurrent, args.force, args.dry_run))


if __name__ == "__main__":
    main()
