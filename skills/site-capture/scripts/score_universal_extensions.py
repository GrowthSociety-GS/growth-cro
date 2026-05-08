#!/usr/bin/env python3
"""
score_universal_extensions.py — Scorers pour les 8 critères universels ajoutés en doctrine v3.1.0.

Critères introduits par V12 NON ENCORE implémentés dans les bloc scorers historiques :
  - Persuasion  : per_09 (Schwartz awareness), per_10 (framework copy), per_11 (Benefit Laddering)
  - Cohérence   : coh_07 (Positioning Statement Moore), coh_08 (Message Hierarchy), coh_09 (Unique Mechanism)
  - Psycho      : psy_07 (4 déclencheurs émotionnels), psy_08 (Voice of Customer)

Approche : détection heuristique où possible, flag `requires_llm_evaluation: true` sinon.
L'orchestrateur `score_page_type.py` appelle `score_extensions(cap, html, page_type)` et
concatène les résultats aux `criteria` du bloc correspondant avant aggregation.

Philosophy v12 : transparent (proof documentée), falsifiable (ternaire Top/OK/Critical),
honnête (review_required explicite quand détection impossible sans LLM/screenshot).
"""
from __future__ import annotations

import json
import re
import pathlib
from typing import Callable

TERNARY = {"top": 3.0, "ok": 1.5, "critical": 0.0}
ROOT = pathlib.Path(__file__).resolve().parents[3]


def _mk(tier: str, signal: str, **proof) -> dict:
    return {
        "tier": tier,
        "score": TERNARY[tier],
        "signal": signal,
        "proof": {k: v for k, v in proof.items() if v is not None},
        "confidence": "high" if tier in ("top", "critical") else "medium",
    }


def _text(html: str) -> str:
    t = re.sub(r"<script[^>]*>.*?</script>", " ", html or "", flags=re.DOTALL | re.I)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.DOTALL | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).lower()


def _h1(cap: dict, html: str) -> str:
    h = (cap.get("hero") or {}).get("h1") or ""
    if h.strip():
        return h
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", html or "", re.I | re.DOTALL)
    return re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else ""


def _h2s(html: str) -> list[str]:
    return [re.sub(r"<[^>]+>", " ", m).strip()
            for m in re.findall(r"<h2\b[^>]*>(.*?)</h2>", html or "", re.I | re.DOTALL)]


# ════════════════════════════════════════════════════════════════════════════
# PERSUASION EXTENSIONS
# ════════════════════════════════════════════════════════════════════════════

def score_per_09(cap: dict, html: str, page_type: str) -> dict:
    """Awareness match Schwartz (Unaware / Problem Aware / Solution Aware / Product Aware / Most Aware).

    Heuristique : détection du niveau de discours H1+H2 et correspondance avec page_type default.
    """
    h1 = _h1(cap, html).lower()
    h2s = " ".join(_h2s(html)).lower()
    text = f"{h1} {h2s}"

    # Default awareness expected per page type (doctrine decision Mathis 2026-04-13)
    defaults = {
        "home": "solution_aware",
        "pdp": "product_aware",
        "collection": "solution_aware",
        "lp_leadgen": "problem_aware",
        "lp_sales": "solution_aware",
        "blog": "problem_aware",
        "quiz_vsl": "unaware_or_problem_aware",
        "pricing": "most_aware",
        "checkout": "most_aware",
        "listicle": "problem_aware",
        "advertorial": "unaware_or_problem_aware",
        "comparison": "product_aware",
        "vsl": "problem_aware",
        "challenge": "solution_aware",
        "thank_you_page": "most_aware",
        "bundle_standalone": "product_aware",
        "squeeze": "problem_aware",
        "webinar": "problem_aware",
    }
    expected = defaults.get(page_type, "solution_aware")

    # Schwartz markers (crude)
    problem_markers = ["problème", "problem", "issue", "struggle", "pain", "fatigue",
                       "difficile", "challenge (personal)", "souffrir", "ras-le-bol"]
    solution_markers = ["solution", "comment", "how to", "méthode", "method", "way to", "approach"]
    product_markers = ["notre produit", "our product", "découvrez", "meet", "introducing",
                       "fonctionnalité", "feature"]
    most_aware_markers = ["buy now", "acheter", "commander", "subscribe", "s'abonner",
                          "checkout", "add to cart", "ajouter au panier", "essayer gratuitement"]

    p_score = sum(1 for m in problem_markers if m in text)
    s_score = sum(1 for m in solution_markers if m in text)
    pr_score = sum(1 for m in product_markers if m in text)
    ma_score = sum(1 for m in most_aware_markers if m in text)

    detected = max(
        [("unaware_or_problem_aware", p_score),
         ("problem_aware", p_score),
         ("solution_aware", s_score),
         ("product_aware", pr_score),
         ("most_aware", ma_score)],
        key=lambda x: x[1],
    )[0] if any([p_score, s_score, pr_score, ma_score]) else "indeterminate"

    match = detected == expected or (expected == "unaware_or_problem_aware" and detected in ("problem_aware", "unaware_or_problem_aware"))
    if match:
        return _mk("top", f"Awareness détecté '{detected}' match default pageType '{expected}'",
                   expected=expected, detected=detected)
    if detected != "indeterminate":
        return _mk("ok", f"Awareness détecté '{detected}' diffère de default '{expected}' — peut être volontaire (UTM/brief)",
                   expected=expected, detected=detected, requires_llm_evaluation=True)
    return _mk("critical", "Niveau d'awareness indéterminable — copy trop générique", expected=expected)


def score_per_10(cap: dict, html: str, page_type: str) -> dict:
    """Structure copy identifiable via framework (PAS/PASTOR/AIDA/BAB/FAB/SB7/4P/SSS/Slippery/CAP)."""
    h2s = _h2s(html)
    t = _text(html)

    # PAS signature: Problème → Agitation → Solution
    pas_hits = sum(1 for kw in ["problème", "problem"] if kw in t) + \
               sum(1 for kw in ["imaginez", "pire", "agitation", "what if", "consequence"] if kw in t) + \
               sum(1 for kw in ["solution", "découvrez", "discover"] if kw in t)

    # AIDA: Attention Interest Desire Action
    aida_hits = sum(1 for kw in ["attention", "attention-grabbing"] if kw in t) + \
                sum(1 for kw in ["interest", "intéressant", "curious"] if kw in t) + \
                sum(1 for kw in ["desire", "envie", "rêve", "dream"] if kw in t) + \
                sum(1 for kw in ["action", "cta", "get started", "commencer"] if kw in t)

    # BAB: Before After Bridge
    bab_hits = sum(1 for kw in ["avant", "before"] if kw in t) + \
               sum(1 for kw in ["après", "after"] if kw in t) + \
               sum(1 for kw in ["bridge", "comment", "how"] if kw in t)

    # Presence of structured H2s (>=4 = narrative arc likely)
    structure_depth = len(h2s)

    max_framework = max([("PAS", pas_hits), ("AIDA", aida_hits), ("BAB", bab_hits)], key=lambda x: x[1])

    if structure_depth >= 4 and max_framework[1] >= 2:
        return _mk("top", f"Structure narrative {max_framework[0]} identifiable ({structure_depth} H2)",
                   framework=max_framework[0], h2_count=structure_depth)
    if structure_depth >= 3:
        return _mk("ok", f"Structure présente ({structure_depth} H2) mais framework peu lisible",
                   h2_count=structure_depth, requires_llm_evaluation=True)
    return _mk("critical", f"Structure narrative absente ({structure_depth} H2 seulement)",
               h2_count=structure_depth)


def score_per_11(cap: dict, html: str, page_type: str) -> dict:
    """Benefit Laddering profond : feature → functional → emotional → identity."""
    t = _text(html)
    # Emotional keywords — signal du passage feature→emotional
    emotional = ["confiance", "confidence", "fier", "proud", "serein", "peace of mind",
                 "libéré", "freedom", "soulagé", "relieved", "happy", "heureux"]
    identity = ["qui vous êtes", "who you are", "devenir", "become", "votre vie",
                "your life", "cette personne", "this kind of person"]
    e_hits = sum(1 for kw in emotional if kw in t)
    i_hits = sum(1 for kw in identity if kw in t)

    if e_hits >= 2 and i_hits >= 1:
        return _mk("top", f"Laddering profond : {e_hits} émotionnels + {i_hits} identitaires",
                   emotional_count=e_hits, identity_count=i_hits)
    if e_hits >= 1 or i_hits >= 1:
        return _mk("ok", f"Laddering partiel (e={e_hits}, i={i_hits})", requires_llm_evaluation=True)
    return _mk("critical", "Copy reste au niveau feature/fonctionnel — pas de laddering émotionnel",
               emotional_count=e_hits)


# ════════════════════════════════════════════════════════════════════════════
# COHERENCE EXTENSIONS
# ════════════════════════════════════════════════════════════════════════════

def score_coh_07(cap: dict, html: str, page_type: str) -> dict:
    """Positioning Statement Moore : 'For X who Y, our Z is the W that [differentiator]'."""
    # Rare on homepages in raw template form; look for pattern markers
    t = _text(html)
    patterns = [
        r"pour\s+(?:les|le|la|l')\s+\w+\s+qui\s+\w+",  # "Pour les X qui Y"
        r"for\s+\w+\s+who\s+\w+",
        r"nous (aidons|permettons|accompagnons)\s+\w+",  # "Nous aidons X"
        r"we help\s+\w+\s+(?:to|achieve|get)",
    ]
    hits = [p for p in patterns if re.search(p, t, re.I)]
    if hits:
        return _mk("top", f"Positioning statement détecté ({len(hits)} patterns)", patterns=hits)
    # Fallback: check for "for / pour" + audience mention in hero h1+h2
    h1 = _h1(cap, html).lower()
    if any(w in h1 for w in ["pour ", "for ", "aux ", "dédié", "dedicated to"]):
        return _mk("ok", "Audience mentionnée dans hero mais pattern Moore incomplet",
                   requires_llm_evaluation=True)
    return _mk("critical", "Pas de positioning statement explicite (audience × différenciation)")


def score_coh_08(cap: dict, html: str, page_type: str) -> dict:
    """Message Hierarchy : primary (H1), secondary (sous-titre), supporting (H2+) explicites."""
    h1 = _h1(cap, html)
    sub = (cap.get("hero") or {}).get("subtitle") or ""
    # Fallback subtitle from HTML
    if not sub:
        m = re.search(r"<h1[^>]*>.*?</h1>\s*<(?:p|h2)[^>]*>(.*?)</(?:p|h2)>",
                      html or "", re.I | re.DOTALL)
        sub = re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else ""
    h2s = _h2s(html)

    levels = sum([bool(h1.strip()), bool(sub.strip()), len(h2s) >= 2])
    if levels == 3:
        return _mk("top", "3 niveaux hiérarchie présents (H1 / sous-titre / H2+)",
                   h1_present=bool(h1), sub_present=bool(sub), h2_count=len(h2s))
    if levels == 2:
        return _mk("ok", f"{levels}/3 niveaux présents",
                   h1_present=bool(h1), sub_present=bool(sub), h2_count=len(h2s))
    return _mk("critical", f"Hiérarchie plate ({levels}/3 niveaux)")


def score_coh_09(cap: dict, html: str, page_type: str) -> dict:
    """Unique Mechanism (Schwartz/Georgi) : le 'comment' différenciant explicitement nommé."""
    t = _text(html)
    # Named mechanism markers: "méthode X", "système Y", "notre approche Z", branded terms
    method_patterns = [
        r"(?:notre|our)\s+(?:méthode|method|système|system|approche|approach|process|processus|formule|formula)\s+\w+",
        r"\b(?:patent(?:ed)?|breveté|exclusive|exclusif|proprietary|propriétaire)\b",
        r"(?:thanks to|grâce à)\s+(?:notre|our)\s+\w+",
        r"™|®",  # Trademark symbols = named mechanism
    ]
    hits = []
    for p in method_patterns:
        m = re.search(p, t, re.I)
        if m:
            hits.append(m.group(0)[:50])
    # Trademark symbols count
    trademarks = len(re.findall(r"™|®", html or ""))
    if trademarks:
        hits.append(f"{trademarks} trademark symbols")

    if len(hits) >= 2:
        return _mk("top", "Unique mechanism nommé + étayé", hits=hits[:5])
    if hits:
        return _mk("ok", "Mention de mécanisme mais peu détaillée", hits=hits)
    return _mk("critical", "Aucun unique mechanism nommé — différenciation floue")


# ════════════════════════════════════════════════════════════════════════════
# PSYCHO EXTENSIONS
# ════════════════════════════════════════════════════════════════════════════

def score_psy_07(cap: dict, html: str, page_type: str) -> dict:
    """4 déclencheurs émotionnels : peur / désir / aspiration / appartenance."""
    t = _text(html)
    triggers = {
        "peur": ["risque", "perdre", "manquer", "avant qu'il ne soit trop tard", "miss out",
                 "fear", "danger", "warning", "attention", "éviter"],
        "désir": ["envie", "want", "craving", "désir", "longing", "obtenir", "get",
                  "acquérir", "posséder"],
        "aspiration": ["devenir", "become", "transform", "atteindre", "achieve",
                       "rêve", "dream", "potential", "meilleure version"],
        "appartenance": ["rejoindre", "join", "communauté", "community", "ensemble",
                         "together", "club", "membres", "members", "tribe"],
    }
    detected = {name: sum(1 for kw in kws if kw in t) for name, kws in triggers.items()}
    active = [n for n, c in detected.items() if c > 0]
    if len(active) >= 3:
        return _mk("top", f"{len(active)}/4 déclencheurs émotionnels actifs",
                   triggers=active, counts=detected)
    if len(active) >= 1:
        return _mk("ok", f"{len(active)}/4 déclencheurs (couverture partielle)",
                   triggers=active, counts=detected)
    return _mk("critical", "Aucun déclencheur émotionnel détecté — copy purement rationnel",
               counts=detected)


def score_psy_08(cap: dict, html: str, page_type: str) -> dict:
    """Voice of Customer : verbatims client réinjectés dans le copy."""
    t = _text(html)
    # Markers of VoC: quoted phrases, testimonials with names, specific personal expressions
    quoted = len(re.findall(r'["«][^"»]{20,200}["»]', html or ""))
    testimonial_names = len(re.findall(r'(?:—|—|–|-)\s*[A-Z][a-zéèêîôûç]+\s+[A-Z]\.?', html or ""))
    # Marketer-speak red flags (anti-signal)
    marketer_speak = ["best-in-class", "world-class", "cutting-edge", "révolutionnaire",
                      "disruptive", "game-changer", "innovative", "premium"]
    anti_count = sum(1 for kw in marketer_speak if kw in t)

    if quoted >= 3 and testimonial_names >= 2 and anti_count <= 1:
        return _mk("top", f"VoC présente : {quoted} citations, {testimonial_names} témoins nommés",
                   quotes=quoted, testimonials=testimonial_names, marketer_speak=anti_count)
    if quoted >= 1 or testimonial_names >= 1:
        return _mk("ok", f"VoC partielle (quotes={quoted}, témoins={testimonial_names})",
                   quotes=quoted, testimonials=testimonial_names, marketer_speak=anti_count)
    if anti_count >= 3:
        return _mk("critical", f"Copy sature de marketer-speak ({anti_count} termes creux) — VoC absente",
                   marketer_speak_examples=[kw for kw in marketer_speak if kw in t])
    return _mk("critical", "Aucun verbatim client / voice of customer détecté")


# ════════════════════════════════════════════════════════════════════════════
# REGISTRY + API
# ════════════════════════════════════════════════════════════════════════════

EXTENSIONS: dict[str, tuple[str, Callable]] = {
    # (pillar, detector)
    "per_09": ("persuasion", score_per_09),
    "per_10": ("persuasion", score_per_10),
    "per_11": ("persuasion", score_per_11),
    "coh_07": ("coherence", score_coh_07),
    "coh_08": ("coherence", score_coh_08),
    "coh_09": ("coherence", score_coh_09),
    "psy_07": ("psycho", score_psy_07),
    "psy_08": ("psycho", score_psy_08),
}


# Labels (sync with playbook JSON amendments)
LABELS = {
    "per_09": "Awareness match Schwartz (Unaware → Most Aware) × pageType default",
    "per_10": "Structure copy identifiable (PAS/PASTOR/AIDA/BAB/FAB/SB7/4P/SSS/Slippery/CAP)",
    "per_11": "Benefit Laddering profond (feature → functional → emotional → identity)",
    "coh_07": "Positioning Statement clair (For X who Y, our Z is the W that...) — Moore template",
    "coh_08": "Message Hierarchy explicite (primary / secondary / supporting)",
    "coh_09": "Unique Mechanism nommé (le 'comment' différenciant — Schwartz/Georgi)",
    "psy_07": "4 déclencheurs émotionnels actifs (peur / désir / aspiration / appartenance)",
    "psy_08": "Voice of Customer (verbatims client réinjectés, pas marketer-speak)",
}


def score_extensions(cap: dict, html: str, page_type: str,
                     applicable_ids: list[str] | None = None) -> dict:
    """Score all v3.1.0 universal extensions, grouped by pillar.

    Args:
        applicable_ids: if provided, only score these IDs (post-exclusion filter).

    Returns:
        {
          "byPillar": {"persuasion": {"criteria": [...], "rawTotal": N, "rawMax": M}, ...},
          "rawTotal": ..., "rawMax": ...,
          "doctrineVersion": "v3.1.0",
        }
    """
    ids_to_score = applicable_ids if applicable_ids is not None else list(EXTENSIONS.keys())
    by_pillar: dict[str, dict] = {}

    for cid in ids_to_score:
        if cid not in EXTENSIONS:
            continue
        pillar, detector = EXTENSIONS[cid]
        try:
            res = detector(cap, html, page_type)
        except Exception as e:
            res = {
                "tier": "ok", "score": TERNARY["ok"],
                "signal": f"detector_error: {type(e).__name__}: {e}",
                "proof": {}, "confidence": "low",
                "requires_llm_evaluation": True,
            }
        entry = {"id": cid, "label": LABELS.get(cid), **res, "max": 3}
        by_pillar.setdefault(pillar, {"criteria": [], "rawTotal": 0.0, "rawMax": 0.0})
        by_pillar[pillar]["criteria"].append(entry)
        by_pillar[pillar]["rawTotal"] += res["score"]
        by_pillar[pillar]["rawMax"] += 3

    # Compute score100 per pillar
    for p in by_pillar.values():
        p["score100"] = round(p["rawTotal"] / p["rawMax"] * 100, 1) if p["rawMax"] else 0.0

    total = sum(p["rawTotal"] for p in by_pillar.values())
    total_max = sum(p["rawMax"] for p in by_pillar.values())
    return {
        "byPillar": by_pillar,
        "rawTotal": round(total, 2),
        "rawMax": round(total_max, 2),
        "score100": round(total / total_max * 100, 1) if total_max else 0.0,
        "doctrineVersion": "v3.1.0 — doctrine V12 — 2026-04-13",
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: score_universal_extensions.py <label> [pageType]")
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    base = ROOT / "data" / "captures" / label
    cap_path = base / page_type / "capture.json"
    if not cap_path.exists():
        cap_path = base / "capture.json"
    cap = json.loads(cap_path.read_text())
    html_path = cap_path.parent / "page.html"
    html = html_path.read_text(errors="ignore") if html_path.exists() else ""
    result = score_extensions(cap, html, page_type)
    print(json.dumps(result, indent=2, ensure_ascii=False))
