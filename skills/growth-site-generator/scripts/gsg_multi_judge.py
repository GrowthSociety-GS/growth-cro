"""GSG Multi-Judge — Orchestrateur 2 juges + arbitrage Sonnet (V26.Z W1).

Réponse à la faille #1 ("Self-audit complaisant") du diagnostic ChatGPT
+ découverte interne : sur Weglot iter8, le self-audit Sonnet seul donnait
132/135 alors qu'une éval humaine externe donnait 46/80. La boucle qualité
mentait par biais de juge unique (le même modèle Sonnet juge ses propres
outputs Sonnet).

ARCHITECTURE
============

Étape 1 — Defender (Sonnet bienveillant, posture historique)
  - Réutilise gsg_self_audit.audit_lp(persona="defender")
  - Score sur 135 pts (eval_grid 45 critères ternaire)

Étape 2 — Skeptic (Sonnet critique impitoyable, anti-biais)
  - Réutilise gsg_self_audit.audit_lp(persona="skeptic")
  - Même grille, posture opposée. Doute par défaut.
  - Le score skeptic est l'estimation pessimiste qui aurait dû exister
    depuis le début pour casser l'auto-validation.

Étape 3 — Compute agreement
  - Sur les TOTAUX (cro_score / design_score / total)
  - Sur les 10 sous-catégories (5 CRO + 5 Design)
  - agreement = 1 - mean(normalized_pairwise_distance)
  - Below threshold (default 0.7) → désaccord matériel → arbitrage

Étape 4 — Arbitrage Sonnet (3e juge avec contexte)
  - Prompt explicite : "Voici 2 juges en désaccord. Tranche."
  - Le Sonnet arbitre VOIT les 2 verdicts + leurs justifications
  - Output : score arbitré + raison + winner (defender / skeptic / own_judgment)
  - Coût additionnel ~$0.05

Étape 5 — Output
  - Sauvegarde dans data/_audit_<client>_multi.json
  - Structure complète : 2-3 verdicts + agreement + delta_analysis
  - Compatible avec disagreement_log.json de multi_judge.py (V26.D)
    pour future intégration au Learning Layer V28

USAGE
=====
CLI :
    python3 skills/growth-site-generator/scripts/gsg_multi_judge.py \\
        --html deliverables/weglot-listicle-V26Y-AURA.html \\
        --client weglot \\
        [--threshold 0.7] [--no-arbitrage]

Module :
    from gsg_multi_judge import run_multi_judge
    result = run_multi_judge(html_path, client="weglot")
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from typing import Optional

# Make sure we can import gsg_self_audit
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

_LEGACY_IMPORT_ERROR: Exception | None = None
try:
    from gsg_self_audit import audit_lp, print_audit_summary, _ensure_api_key, _strip_fences  # noqa: E402
    from gsg_humanlike_audit import audit_lp_humanlike, print_humanlike_summary  # noqa: E402
    from fix_html_runtime import detect_runtime_bugs  # noqa: E402  V26.Z bug-fix : sanity check
except Exception as exc:  # legacy lab may be partially archived
    _LEGACY_IMPORT_ERROR = exc
    audit_lp = print_audit_summary = _ensure_api_key = _strip_fences = None  # type: ignore
    audit_lp_humanlike = print_humanlike_summary = detect_runtime_bugs = None  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[3]
SONNET_MODEL = "claude-sonnet-4-5-20250929"

# Threshold below which we trigger arbitrage. Calibration empirique :
# - 0.5 = trop permissif (accepte ~50% delta entre juges sans alerter)
# - 0.7 = sweet spot (déclenche arbitrage si delta total > ~30%)
# - 0.85 = trop strict (arbitrage trop souvent)
# Pour le 3-way (defender + skeptic + humanlike), on compare les 3 sur leurs
# pct normalisés. spread = max(pct) - min(pct).
# spread < 0.15 (15pts d'écart sur 100) = accord, sinon arbitrage.
DEFAULT_AGREEMENT_THRESHOLD = 0.7
DEFAULT_SPREAD_THRESHOLD = 0.15  # 15% d'écart entre juges sur les pct normalisés


# ─────────────────────────────────────────────────────────────────────────────
# Agreement computation
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return max(0.0, min(1.0, score / max_score))


def _category_pairs(audit: dict) -> dict[str, tuple[float, float]]:
    """Extrait (sum_score, sum_max) par sous-catégorie pour comparaison."""
    out: dict[str, tuple[float, float]] = {}
    scores = audit.get("scores") or {}
    for block_name, block in scores.items():  # cro / design
        if not isinstance(block, dict):
            continue
        for cat_name, criteria in block.items():
            if not isinstance(criteria, list):
                continue
            s_sum = 0.0
            m_sum = 0.0
            for c in criteria:
                try:
                    s_sum += float(c.get("score", 0) or 0)
                    # Each criterion scored on 3 pts
                    m_sum += 3.0
                except (TypeError, ValueError):
                    continue
            key = f"{block_name}.{cat_name}"
            out[key] = (s_sum, m_sum)
    return out


def _judge_total_pct(audit: dict) -> tuple[float, float, float]:
    """Returns (score, max, pct) from a judge audit total."""
    t = audit.get("totals") or {}
    score = float(t.get("total", 0) or 0)
    max_v = float(t.get("total_max", 0) or 0)
    pct = (score / max_v * 100) if max_v > 0 else 0.0
    return score, max_v, round(pct, 1)


def compute_agreement(defender: dict, skeptic: dict,
                       humanlike: dict | None = None) -> dict:
    """Calcule l'agreement entre 2 ou 3 audits sur des grilles potentiellement différentes.

    Le defender + skeptic partagent eval_grid 135 pts.
    Le humanlike (optionnel) score sur grille 80 pts (8 dimensions humaines).
    On compare les 3 sources NORMALISÉES EN POURCENTAGE pour permettre la
    comparaison de grilles différentes.

    Retourne :
      {
        "overall": 0.42,                # 1 - max_pairwise_distance des pct normalisés
        "spread_pct": 58.0,             # max(pct) - min(pct) sur les juges
        "judges_pct": {                 # pct normalisé par juge
          "defender":  {"score": 135.0, "max": 135.0, "pct": 100.0},
          "skeptic":   {"score": 135.0, "max": 135.0, "pct": 100.0},
          "humanlike": {"score": 32.0,  "max": 80.0,  "pct": 40.0}
        },
        "per_total": {                  # legacy, sur la grille eval_grid (compat skeptic)
          "cro": {...}, "design": {...}, "total": {...}
        },
        "per_category": [...],          # désaccords par sous-catégorie eval_grid (defender vs skeptic)
        "max_category_delta_pts": 9.0,
        "humanlike_signature_nommable": "Editorial Press SaaS" | null,
        "humanlike_ai_patterns": [...]
      }
    """
    judges_pct: dict[str, dict] = {}
    for label, audit in [("defender", defender), ("skeptic", skeptic),
                         ("humanlike", humanlike)]:
        if audit is None:
            continue
        score, max_v, pct = _judge_total_pct(audit)
        judges_pct[label] = {"score": score, "max": max_v, "pct": pct}

    pcts = [j["pct"] for j in judges_pct.values()]
    spread_pct = round(max(pcts) - min(pcts), 1) if pcts else 0.0
    # overall = 1 - spread normalisé sur 100. Si tous d'accord à 100% pct → overall=1.0.
    overall = round(1.0 - (spread_pct / 100.0), 3)

    # Legacy per_total (defender vs skeptic on eval_grid)
    d_t = defender.get("totals") or {}
    s_t = skeptic.get("totals") or {}
    per_total = {}
    for key, max_key in [("cro", "cro_max"), ("design", "design_max"), ("total", "total_max")]:
        if key == "total":
            d_score = float(d_t.get("total", 0) or 0)
            s_score = float(s_t.get("total", 0) or 0)
        else:
            d_score = float(d_t.get(f"{key}_score", 0) or 0)
            s_score = float(s_t.get(f"{key}_score", 0) or 0)
        max_score = float(d_t.get(max_key, s_t.get(max_key, 0)) or 0)
        delta_pts = abs(d_score - s_score)
        per_total[key] = {
            "defender": d_score,
            "skeptic": s_score,
            "max": max_score,
            "delta_pts": delta_pts,
            "delta_pct": round((delta_pts / max_score * 100) if max_score > 0 else 0, 1),
        }

    # Per-category (defender vs skeptic eval_grid breakdown — utile pour debug ciblé)
    d_cats = _category_pairs(defender)
    s_cats = _category_pairs(skeptic)
    per_category = []
    for cat in sorted(set(d_cats.keys()) | set(s_cats.keys())):
        d_s, d_m = d_cats.get(cat, (0.0, 0.0))
        s_s, s_m = s_cats.get(cat, (0.0, 0.0))
        max_v = max(d_m, s_m)
        delta = abs(d_s - s_s)
        per_category.append({
            "category": cat,
            "defender": d_s,
            "skeptic": s_s,
            "max": max_v,
            "delta_pts": delta,
            "delta_pct": round((delta / max_v * 100) if max_v > 0 else 0, 1),
        })
    per_category.sort(key=lambda x: x["delta_pts"], reverse=True)
    max_cat_delta = per_category[0]["delta_pts"] if per_category else 0.0

    out = {
        "overall": overall,
        "spread_pct": spread_pct,
        "judges_pct": judges_pct,
        "per_total": per_total,
        "per_category": per_category,
        "max_category_delta_pts": max_cat_delta,
    }

    if humanlike is not None:
        out["humanlike_signature_nommable"] = humanlike.get("signature_nommable")
        out["humanlike_ai_patterns"] = humanlike.get("ai_default_patterns_detected") or []

    return out


# ─────────────────────────────────────────────────────────────────────────────
# Arbitrage Sonnet
# ─────────────────────────────────────────────────────────────────────────────

ARBITRAGE_SYSTEM = """Tu es un juge senior CRO + Design GSG, en posture d'ARBITRAGE FINAL.

Trois juges ont évalué la même LP HTML sur DES GRILLES DIFFÉRENTES :

1. **Defender** (Sonnet posture bienveillante, eval_grid /135) : audit officiel mécanique
   sur 45 critères ternaires (présence/absence de headline, social proof, anti-slop bool×8, etc.)
2. **Skeptic** (Sonnet posture critique, MÊME eval_grid /135) : même grille, posture inverse
3. **Humanlike** (Sonnet directeur créatif senior, grille humaine /80 sur 8 dimensions) :
   concrétude H2, densité narrative, Cialdini activé, biais cognitifs, frameworks copy
   orchestrés, polish anti-AI-slop "réel" (pas juste pattern présent), brand DNA respect
   "réel", architecture émotionnelle. 10/10 = top 0.001% Linear/Stripe/Aesop.

DIFFÉRENCE CRITIQUE : la grille humanlike capture ce que les humains experts pénalisent
(originalité non-IA, signature visuelle nommable, tension narrative, copy spécifique vs
"AI default") — qui est SOUS-représenté dans eval_grid. Si humanlike donne <60/80 pendant
que defender/skeptic donnent ~130/135, le PRIX humanlike est plus proche de la vérité
externe — c'est le signal "self-audit complaisant" pointé par Mathis.

Règles d'arbitrage :
1. Ne pas faire la moyenne par paresse. Trancher avec position.
2. Si humanlike pénalise sur "signature non nommable" / "AI default patterns" / "brand DNA
   reproduit pas amplifié" → ces critiques sont prioritaires (pas dans eval_grid).
3. Si defender+skeptic alignent sur 95-100% pct mais humanlike donne <70%, l'arbitre PRIVILÉGIE
   humanlike pour le score final (il regarde ce qui compte vraiment côté lecteur humain).
4. Si humanlike donne >85% ET defender/skeptic alignent ~95% → vraie excellence, score haut OK.
5. Privilégier les éléments AUDITABLES (patterns concrets dans le HTML) plutôt que les verdicts
   narratifs.
6. Pénaliser explicitement si l'humanlike signale "signature_nommable: null" ou plus de 3
   "ai_default_patterns_detected".

Output JSON STRICT :
{
  "arbitrated_total_score_pct": <0-100>,
  "winner_overall": "defender|skeptic|humanlike|own_judgment",
  "key_disagreements_resolved": [
    {
      "topic": "...",
      "defender_said": "...",
      "skeptic_said": "...",
      "humanlike_said": "...",
      "arbiter_says": "...",
      "evidence_in_html": "..."
    }
  ],
  "arbitrage_reason": "<4-5 phrases ancrées, explique POURQUOI on penche vers humanlike ou eval_grid>",
  "confidence": <0.0-1.0>,
  "final_verdict_short": "<1 phrase finale tranchante : la LP est-elle livrable, et au prix de quoi>"
}
JSON only, pas de markdown autour."""


def call_arbitrage_sonnet(html: str, defender: dict, skeptic: dict,
                          agreement: dict, humanlike: dict | None = None,
                          model: str = SONNET_MODEL,
                          verbose: bool = True) -> Optional[dict]:
    """Appelle Sonnet en arbitre 3-way. Voit les 3 verdicts + le HTML pour ancrer.

    Si humanlike est None, retombe sur l'arbitrage 2-way (defender vs skeptic) historique.
    """
    _ensure_api_key()
    import anthropic
    client_api = anthropic.Anthropic()

    html_for_prompt = html if len(html) < 30000 else html[:30000] + "\n... [truncated]"

    judges_pct = agreement.get("judges_pct", {})
    pct_table_lines = []
    for label in ["defender", "skeptic", "humanlike"]:
        if label in judges_pct:
            j = judges_pct[label]
            pct_table_lines.append(f"| {label.capitalize()} | {j['score']}/{j['max']} | {j['pct']}% |")
    pct_table = "\n".join(pct_table_lines)

    sig_nommable = agreement.get("humanlike_signature_nommable")
    ai_patterns = agreement.get("humanlike_ai_patterns") or []
    humanlike_section = ""
    if humanlike is not None:
        ai_patterns_md = "\n".join(f"  - {p}" for p in ai_patterns) if ai_patterns else "  (aucun détecté)"
        humanlike_section = f"""
### Verdict Humanlike (DA senior, grille 8 dimensions /80)
{humanlike.get('verdict_paragraph', '?')[:500]}

Signature visuelle nommable : {sig_nommable if sig_nommable else "❌ AUCUNE (alarme)"}

Patterns AI default détectés ({len(ai_patterns)}) :
{ai_patterns_md}

Forces vues par humanlike :
""" + "\n".join(f"  + {s}" for s in humanlike.get("humanlike_strengths", [])[:3]) + """

Faiblesses vues par humanlike :
""" + "\n".join(f"  - {w}" for w in humanlike.get("humanlike_weaknesses", [])[:3])

    user_msg = f"""## Trois verdicts sur la même LP HTML, grilles différentes

### Scores normalisés en %
| Juge | Score | Pct |
|---|---|---|
{pct_table}

Spread (max-min des pct) : {agreement.get('spread_pct', '?')}%
Agreement global : {agreement.get('overall', '?')} (1.0 = parfait, <0.85 = désaccord matériel)

### Verdict Defender (extrait, eval_grid 135 pts)
{defender.get('verdict_paragraph', '?')[:500]}

### Verdict Skeptic (extrait, eval_grid 135 pts)
{skeptic.get('verdict_paragraph', '?')[:500]}
{humanlike_section}

### HTML à arbitrer
```html
{html_for_prompt}
```

Tranche."""

    if verbose:
        print(f"  → Sonnet arbitrage call (3-way, prompt={len(user_msg)} chars) ...", flush=True)
    msg = client_api.messages.create(
        model=model,
        max_tokens=2500,
        temperature=0,
        system=ARBITRAGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = msg.content[0].text
    if verbose:
        print(f"  ← in={msg.usage.input_tokens} out={msg.usage.output_tokens}", flush=True)
    text = _strip_fences(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"error": "arbitrage_parse_failed", "raw_first_500": text[:500]}


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def run_multi_judge(html_path: pathlib.Path, client: str,
                    threshold: float = DEFAULT_AGREEMENT_THRESHOLD,
                    skip_arbitrage: bool = False,
                    skip_humanlike: bool = False,
                    verbose: bool = True) -> dict:
    """Orchestre le multi-judge complet 3-way :
    defender → skeptic → humanlike → agreement → arbitrage si désaccord.

    Args:
      threshold: agreement threshold below which arbitrage triggers (1.0 - spread_pct/100)
      skip_humanlike: si True, retombe sur 2-way historique (defender + skeptic)
      skip_arbitrage: si True, pas d'arbitrage même en cas de désaccord
    """
    if _LEGACY_IMPORT_ERROR is not None:
        raise RuntimeError(
            "FROZEN LEGACY LAB gsg_multi_judge.py is incomplete in the active tree. "
            "Use moteur_multi_judge.orchestrator.run_multi_judge() for canonical judging. "
            f"Legacy import error: {_LEGACY_IMPORT_ERROR}"
        )

    html = html_path.read_text()
    n_judges = 2 if skip_humanlike else 3

    if verbose:
        print(f"\n══ GSG Multi-Judge — {client} / {html_path.name} ══\n")

    # ÉTAPE 0 : Implementation Check (V26.Z bug-fix Phase 1)
    # Sanity check Python AVANT les juges Sonnet (qui lisent le HTML brut et
    # ratent les bugs de rendering). Détecte counters à 0, opacity 0 sans
    # animation, scripts manquants. Pénalise le score final si critical.
    if verbose:
        print(f"[0/{n_judges + (0 if skip_arbitrage else 1)}] Implementation check (Python sanity, AVANT Sonnet juges)...")
    impl_report = detect_runtime_bugs(html)
    impl_severity = impl_report.get("broken_severity", "ok")
    impl_penalty_pct = 0.0
    if impl_severity == "critical":
        impl_penalty_pct = 25.0  # pénalité forte sur le score final
    elif impl_severity == "warning":
        impl_penalty_pct = 10.0
    if verbose:
        print(f"  Counters with 0 default : {impl_report['counters_with_zero_default']}/{impl_report['counters_total']}")
        print(f"  Has counter JS          : {impl_report['has_counter_js']}")
        print(f"  Opacity:0 no animation  : {impl_report['opacity_zero_no_animation']}")
        print(f"  Broken score            : {impl_report['broken_score']} ({impl_severity})")
        if impl_penalty_pct > 0:
            print(f"  ⚠️  Penalty applied to final score : -{impl_penalty_pct}pts")

    # Étape 1 : Defender (eval_grid 135)
    if verbose:
        print(f"\n[1/{n_judges + (0 if skip_arbitrage else 1)}] Defender judging (eval_grid 135 pts)...")
    defender = audit_lp(html, client, persona="defender", verbose=verbose)
    if verbose:
        print_audit_summary(defender, label="DEFENDER")

    # Étape 2 : Skeptic (eval_grid 135, posture critique)
    if verbose:
        print(f"\n[2/{n_judges + (0 if skip_arbitrage else 1)}] Skeptic judging (eval_grid 135 pts, posture critique)...")
    skeptic = audit_lp(html, client, persona="skeptic", verbose=verbose)
    if verbose:
        print_audit_summary(skeptic, label="SKEPTIC")

    # Étape 3 : Humanlike (8 dimensions humaines /80) — la VRAIE rupture de grille
    humanlike = None
    if not skip_humanlike:
        if verbose:
            print(f"\n[3/{n_judges + (0 if skip_arbitrage else 1)}] Humanlike judging (DA senior, 8 dimensions /80)...")
        humanlike = audit_lp_humanlike(html, client, verbose=verbose)
        if verbose:
            print_humanlike_summary(humanlike, label="HUMANLIKE")

    # Étape 4 : agreement 3-way (ou 2-way si skip_humanlike)
    agreement = compute_agreement(defender, skeptic, humanlike)
    needs_arb = agreement["overall"] < threshold

    if verbose:
        print(f"\n══ AGREEMENT ANALYSIS ══")
        print(f"  Overall agreement : {agreement['overall']}  (threshold={threshold})")
        print(f"  Spread pct        : {agreement['spread_pct']}%")
        print(f"  Per judge :")
        for label, j in agreement["judges_pct"].items():
            print(f"    {label:10s}: {j['score']}/{j['max']} ({j['pct']}%)")
        print(f"  Needs arbitrage   : {needs_arb}")
        if humanlike is not None:
            sig = agreement.get("humanlike_signature_nommable")
            print(f"  Signature nommable (humanlike) : {sig if sig else '❌ aucune'}")
            ai_patterns = agreement.get("humanlike_ai_patterns") or []
            if ai_patterns:
                print(f"  Patterns IA détectés ({len(ai_patterns)}) :")
                for p in ai_patterns[:5]:
                    print(f"    • {p}")

    # Étape 5 : arbitrage si désaccord
    arbitrage = None
    if needs_arb and not skip_arbitrage:
        step_n = n_judges + 1
        if verbose:
            print(f"\n[{step_n}/{step_n}] Désaccord matériel → arbitrage Sonnet 3-way...")
        arbitrage = call_arbitrage_sonnet(html, defender, skeptic, agreement,
                                           humanlike=humanlike, verbose=verbose)
        if verbose and arbitrage and "arbitrated_total_score_pct" in arbitrage:
            print(f"\n══ ARBITRAGE VERDICT ══")
            print(f"  Final pct      : {arbitrage.get('arbitrated_total_score_pct')}%")
            print(f"  Winner overall : {arbitrage.get('winner_overall')}")
            print(f"  Confidence     : {arbitrage.get('confidence')}")
            print(f"  Reason         : {arbitrage.get('arbitrage_reason')}")
            print(f"  Final verdict  : {arbitrage.get('final_verdict_short')}")

    # Étape 6 : final score (en pct pour comparabilité grilles différentes)
    judges_pcts = [j["pct"] for j in agreement["judges_pct"].values()]
    if arbitrage and isinstance(arbitrage.get("arbitrated_total_score_pct"), (int, float)):
        final_pct = float(arbitrage["arbitrated_total_score_pct"])
        final_source = "arbitrage_3way"
    elif needs_arb:
        # Pas d'arbitrage demandé mais désaccord : weighted lean vers le pct le plus bas
        # (philosophie : en cas de doute, mieux sous-estimer que sur-estimer — surtout si
        # humanlike est dans le panel et donne un signal de gap)
        sorted_pcts = sorted(judges_pcts)
        # Min count 0.4 + median 0.4 + max 0.2
        if len(sorted_pcts) >= 3:
            final_pct = round(0.4 * sorted_pcts[0] + 0.4 * sorted_pcts[1] + 0.2 * sorted_pcts[2], 1)
        else:
            final_pct = round(0.6 * min(judges_pcts) + 0.4 * max(judges_pcts), 1)
        final_source = "weighted_pessimist_lean"
    else:
        final_pct = round(sum(judges_pcts) / len(judges_pcts), 1) if judges_pcts else 0.0
        final_source = "average_agreed"

    # V26.Z bug-fix : appliquer la pénalité Implementation Check
    if impl_penalty_pct > 0:
        final_pct = max(0.0, round(final_pct - impl_penalty_pct, 1))
        final_source = f"{final_source}_minus_impl_penalty_{impl_penalty_pct}"
        if verbose:
            print(f"\n  ⚠️  Implementation penalty applied : final {final_pct}% (severity={impl_severity})")

    tokens_total = (
        (defender.get("tokens_in", 0) + defender.get("tokens_out", 0))
        + (skeptic.get("tokens_in", 0) + skeptic.get("tokens_out", 0))
    )
    if humanlike is not None:
        tokens_total += humanlike.get("tokens_in", 0) + humanlike.get("tokens_out", 0)

    return {
        "version": "v26.Z.W1.c",  # bumped : added Implementation Check (Étape 0)
        "client": client,
        "html_path": str(html_path.relative_to(ROOT)) if html_path.is_relative_to(ROOT) else str(html_path),
        "judged_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "threshold": threshold,
        "n_judges": n_judges,
        "implementation_check": impl_report,
        "implementation_penalty_pct": impl_penalty_pct,
        "judges": {
            "defender": defender,
            "skeptic": skeptic,
            "humanlike": humanlike,
            "arbitrage": arbitrage,
        },
        "agreement": agreement,
        "needs_arbitrage": needs_arb,
        "final_score_pct": final_pct,
        "final_score_source": final_source,
        "tokens_total": tokens_total,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-legacy-lab", action="store_true",
                    help="Required acknowledgement: legacy eval_grid /135 judge. Use moteur_multi_judge/orchestrator.py for canonical post-run judging.")
    ap.add_argument("--html", required=True)
    ap.add_argument("--client", required=True)
    ap.add_argument("--threshold", type=float, default=DEFAULT_AGREEMENT_THRESHOLD,
                    help=f"Agreement threshold below which arbitrage triggers (default: {DEFAULT_AGREEMENT_THRESHOLD})")
    ap.add_argument("--no-arbitrage", action="store_true",
                    help="Skip Sonnet arbitrage (cheaper, just defender + skeptic [+ humanlike])")
    ap.add_argument("--no-humanlike", action="store_true",
                    help="Skip humanlike judge (faster, falls back to 2-way defender vs skeptic)")
    ap.add_argument("--output", help="Path to save multi-judge JSON (default: data/_audit_<client>_multi.json)")
    args = ap.parse_args()

    if not args.allow_legacy_lab:
        sys.exit(
            "❌ FROZEN LEGACY LAB: gsg_multi_judge.py uses the abandoned eval_grid /135.\n"
            "Use `moteur_multi_judge.orchestrator.run_multi_judge()` instead.\n"
            "For forensic reproduction only, re-run with `--allow-legacy-lab`."
        )

    html_fp = pathlib.Path(args.html)
    if not html_fp.exists():
        sys.exit(f"❌ {html_fp} not found")

    result = run_multi_judge(
        html_fp, args.client,
        threshold=args.threshold,
        skip_arbitrage=args.no_arbitrage,
        skip_humanlike=args.no_humanlike,
    )

    out_fp = pathlib.Path(args.output or (ROOT / "data" / f"_audit_{args.client}_multi.json"))
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"\n══ FINAL ══")
    print(f"  Final pct      : {result['final_score_pct']}%  (source: {result['final_score_source']})")
    for label, j in result["agreement"]["judges_pct"].items():
        print(f"  {label.capitalize():10s}: {j['score']}/{j['max']} ({j['pct']}%)")
    arb = (result.get("judges") or {}).get("arbitrage") or {}
    if isinstance(arb, dict) and arb.get("arbitrated_total_score_pct") is not None:
        print(f"  Arbiter pct    : {arb['arbitrated_total_score_pct']}%  ({arb.get('winner_overall', '?')})")
    print(f"  Agreement      : {result['agreement']['overall']}  (spread {result['agreement']['spread_pct']}%)")
    print(f"  Tokens total   : {result['tokens_total']}  (~${result['tokens_total'] * 3 / 1e6:.3f})")
    print(f"\n  Multi-judge saved: {out_fp.relative_to(ROOT) if out_fp.is_relative_to(ROOT) else out_fp}")


if __name__ == "__main__":
    main()
