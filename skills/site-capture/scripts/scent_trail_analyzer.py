#!/usr/bin/env python3
"""
scent_trail_analyzer.py — P11.15 (V19) : mesure cross-page scent trail CRO.

Le scent trail (continuité ad → LP → PDP → checkout) est la killer feature CRO
différenciante. GrowthCRO V17 ne mesure QUE page par page. Cette analyse mesure
les transitions entre pages d'un même client :

- **Vocabulaire** : Jaccard sur mots-clés (hero H1 + subtitle + CTAs)
- **Offre** : présence constante des benefits/prix/promo promis
- **Persona** : mention constante du target (cible)
- **Visuel** : (futur, nécessite CLIP embedding) — V1 skip

Output : `<client>/scent_trail.json`
{
  "client": "japhy",
  "analyzed_pages": ["home", "pdp", "checkout"],
  "transitions": [
    {
      "from": "home",
      "to": "pdp",
      "vocabulary_jaccard": 0.35,
      "offer_continuity": 0.8,
      "persona_continuity": 1.0,
      "score_overall": 0.65,
      "breaks": ["price_not_mentioned_on_home"],
      "verdict": "partial"
    },
    ...
  ],
  "overall_scent_score": 0.58,
  "verdict": "partial_breaks",
  "top_recommendations": [
    "Aligner le CTA 'Commander' sur la home avec le bouton 'Ajouter au panier' PDP...",
    ...
  ]
}

Usage :
    python3 scent_trail_analyzer.py --client japhy
    python3 scent_trail_analyzer.py --client japhy --sequence home,pdp,checkout
    python3 scent_trail_analyzer.py --all
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"


# ────────────────────────────────────────────────────────────────
# Keyword extraction
# ────────────────────────────────────────────────────────────────

_STOPWORDS_FR = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "à", "au", "aux",
    "pour", "sur", "dans", "avec", "sans", "par", "en", "ce", "ces", "son", "sa",
    "ses", "notre", "votre", "vos", "mon", "ma", "mes", "ton", "ta", "tes", "il",
    "elle", "ils", "elles", "je", "tu", "nous", "vous", "qui", "que", "quoi", "dont",
    "est", "sont", "être", "avoir", "a", "ont", "plus", "moins", "très", "tout",
    "tous", "toutes", "toute", "aussi", "encore", "déjà", "mais", "donc", "car",
    "si", "non", "oui", "pas", "ne", "ni", "vraiment", "bien", "mal", "faire",
    "fait", "dire", "dit", "voir", "vu", "aller", "va", "venir",
}
_STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "from", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should", "could",
    "this", "that", "these", "those", "it", "its", "we", "you", "he", "she", "they",
    "me", "my", "your", "our", "their", "his", "her",
}
STOPWORDS = _STOPWORDS_FR | _STOPWORDS_EN

_WORD_RE = re.compile(r"\b[\w'’\-]{3,}\b", re.UNICODE)


def tokenize_clean(text: str) -> set[str]:
    """Extract content words (len≥3, pas stopword) en lowercase."""
    words = {m.group(0).lower() for m in _WORD_RE.finditer(text or "")}
    return {w for w in words if w not in STOPWORDS}


def extract_page_keywords(capture_json: dict) -> dict:
    """Extract les signaux clés par page : vocabulaire, CTAs, offres, persona."""
    hero = capture_json.get("hero") or {}
    social = capture_json.get("socialProof") or {}
    overlays = capture_json.get("overlays") or {}

    # Vocabulaire principal (H1 + subtitle + top CTAs labels)
    primary_text = " ".join(filter(None, [
        hero.get("h1", ""),
        hero.get("subtitle", ""),
    ]))
    cta_labels = " ".join(
        (c.get("label") or "") for c in (hero.get("ctas") or [])[:5] if isinstance(c, dict)
    )
    vocabulary = tokenize_clean(primary_text + " " + cta_labels)

    # CTAs actionnables
    cta_texts = [
        (c.get("label") or "").strip()
        for c in (hero.get("ctas") or [])
        if isinstance(c, dict) and c.get("label")
    ][:10]

    # Offres détectées (chiffres %, €, gratuit, offert, essai, etc.)
    offer_markers = set()
    for text_src in [primary_text, cta_labels]:
        for pattern in [
            r"\b(\d+)\s*%",           # pourcentages
            r"(\d+)\s*€",             # prix EUR
            r"\b(gratuit|offert|offerte|free)\b",
            r"\b(essai|essayer|trial)\b",
            r"\b(livraison|shipping)\b",
            r"\b(garantie|guaranteed|sans engagement)\b",
            r"\b(rembours\w+)\b",
        ]:
            for m in re.finditer(pattern, text_src.lower()):
                offer_markers.add(m.group(0))

    # Persona/target mentions (pour, les, ma, mon, etc. + noms communs cible)
    target_patterns = [
        r"\bpour (les |mon |votre |ses |son |ton )?(\w+)",
        r"\b(chiens?|chats?|freelances?|équipes?|entrepreneurs?|startups?)",
        r"\b(parents?|femmes?|hommes?|étudiants?|designers?|developers?)",
    ]
    target_mentions = set()
    for p in target_patterns:
        for m in re.finditer(p, primary_text.lower()):
            target_mentions.add(m.group(0))

    return {
        "vocabulary": vocabulary,
        "cta_texts": cta_texts,
        "offer_markers": sorted(list(offer_markers)),
        "target_mentions": sorted(list(target_mentions)),
        "h1": hero.get("h1", ""),
        "subtitle": hero.get("subtitle", ""),
    }


# ────────────────────────────────────────────────────────────────
# Transition scoring
# ────────────────────────────────────────────────────────────────

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_transition(page_a: dict, page_b: dict) -> dict:
    """Score la cohérence entre page_a (upstream) et page_b (downstream dans funnel)."""
    voc_jaccard = jaccard(page_a["vocabulary"], page_b["vocabulary"])

    # Offer continuity : est-ce que les offres promises A sont présentes B ?
    set_a_offers = set(page_a["offer_markers"])
    set_b_offers = set(page_b["offer_markers"])
    if not set_a_offers and not set_b_offers:
        offer_continuity = 1.0
    elif not set_a_offers:
        offer_continuity = 1.0  # rien promis upstream = rien à honorer
    else:
        offer_continuity = len(set_a_offers & set_b_offers) / len(set_a_offers)

    # Persona continuity
    persona_a = set(page_a["target_mentions"])
    persona_b = set(page_b["target_mentions"])
    if not persona_a and not persona_b:
        persona_continuity = 1.0
    elif not persona_a:
        persona_continuity = 1.0
    else:
        persona_continuity = len(persona_a & persona_b) / len(persona_a)

    # Score global pondéré
    score_overall = round(
        0.5 * voc_jaccard + 0.3 * offer_continuity + 0.2 * persona_continuity, 3
    )

    # Breaks explicites (pour diagnostic)
    breaks = []
    if voc_jaccard < 0.2:
        breaks.append(f"vocabulary_rupture (jaccard={voc_jaccard:.2f})")
    missing_offers = set_a_offers - set_b_offers
    if missing_offers:
        breaks.append(f"offers_not_honored: {sorted(missing_offers)[:3]}")
    if persona_a and not persona_b:
        breaks.append("persona_vanished")

    # Verdict
    if score_overall >= 0.7:
        verdict = "strong"
    elif score_overall >= 0.4:
        verdict = "partial"
    else:
        verdict = "broken"

    return {
        "vocabulary_jaccard": round(voc_jaccard, 3),
        "offer_continuity": round(offer_continuity, 3),
        "persona_continuity": round(persona_continuity, 3),
        "score_overall": score_overall,
        "breaks": breaks,
        "verdict": verdict,
    }


# ────────────────────────────────────────────────────────────────
# Main analysis
# ────────────────────────────────────────────────────────────────

DEFAULT_SEQUENCES = {
    "ecommerce": ["home", "collection", "pdp", "checkout"],
    "saas": ["home", "pricing", "checkout"],
    "lead_gen": ["home", "pricing", "lp_leadgen"],
    "fintech": ["home", "pricing"],
    "app": ["home", "pricing"],
    "content": ["home", "blog"],
}


def analyze_client(client: str, sequence: Optional[list[str]] = None) -> Optional[dict]:
    client_dir = CAPTURES / client
    if not client_dir.exists():
        print(f"❌ {client_dir} introuvable")
        return None

    # Identifie les pages disponibles
    available_pages = sorted([p.name for p in client_dir.iterdir() if p.is_dir()])
    if not available_pages:
        print(f"❌ Aucune page dans {client_dir}")
        return None

    # Sequence : user-provided ou inférée (ordre logique)
    if sequence:
        pages_to_analyze = [p for p in sequence if p in available_pages]
    else:
        # Heuristique : trier par importance funnel
        funnel_order = ["home", "lp_leadgen", "lp_sales", "quiz_vsl", "collection", "pdp", "pricing", "checkout", "blog"]
        pages_to_analyze = [p for p in funnel_order if p in available_pages]

    if len(pages_to_analyze) < 2:
        print(f"⚠ {client}: besoin d'au moins 2 pages pour analyser un scent trail")
        return None

    print(f"→ Scent trail {client}: {' → '.join(pages_to_analyze)}")

    # Extract keywords par page
    page_data: dict[str, dict] = {}
    for page in pages_to_analyze:
        cap = client_dir / page / "capture.json"
        if not cap.exists():
            continue
        try:
            data = json.loads(cap.read_text())
            page_data[page] = extract_page_keywords(data)
        except Exception as e:
            print(f"  ⚠ {page}: {e}")

    if len(page_data) < 2:
        return None

    # Score chaque transition
    transitions = []
    pages_ordered = [p for p in pages_to_analyze if p in page_data]
    for i in range(len(pages_ordered) - 1):
        p_from = pages_ordered[i]
        p_to = pages_ordered[i + 1]
        t = score_transition(page_data[p_from], page_data[p_to])
        t["from"] = p_from
        t["to"] = p_to
        transitions.append(t)
        print(f"  {p_from} → {p_to}: score={t['score_overall']} ({t['verdict']})")

    # Overall score
    if transitions:
        overall = sum(t["score_overall"] for t in transitions) / len(transitions)
    else:
        overall = 0.0

    if overall >= 0.7:
        verdict = "strong_continuity"
    elif overall >= 0.4:
        verdict = "partial_breaks"
    else:
        verdict = "severe_breaks"

    # Top recommendations basées sur les breaks détectés
    recos = []
    all_breaks = []
    for t in transitions:
        for b in t["breaks"]:
            all_breaks.append(f"{t['from']}→{t['to']}: {b}")
    for b in all_breaks[:5]:
        recos.append(b)

    result = {
        "client": client,
        "analyzed_pages": pages_ordered,
        "transitions": transitions,
        "overall_scent_score": round(overall, 3),
        "verdict": verdict,
        "top_recommendations": recos,
    }

    out = client_dir / "scent_trail.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"✓ overall={overall:.2f} ({verdict}) → {out}")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="Un client specifique")
    ap.add_argument("--sequence", help="Séquence custom ex 'home,pdp,checkout'")
    ap.add_argument("--all", action="store_true", help="Analyser tous les clients")
    args = ap.parse_args()

    if args.all:
        total, strong, partial, broken = 0, 0, 0, 0
        for cd in sorted(CAPTURES.iterdir()):
            if not cd.is_dir() or cd.name.startswith("_"):
                continue
            r = analyze_client(cd.name)
            if r:
                total += 1
                v = r["verdict"]
                if v == "strong_continuity":
                    strong += 1
                elif v == "partial_breaks":
                    partial += 1
                else:
                    broken += 1
        print("\n=== FLEET SCENT TRAIL ===")
        print(f"Total analysés : {total}")
        print(f"Strong : {strong}  Partial : {partial}  Broken : {broken}")
        return

    if not args.client:
        print("❌ --client ou --all requis")
        return

    seq = None
    if args.sequence:
        seq = [s.strip() for s in args.sequence.split(",")]
    analyze_client(args.client, seq)


if __name__ == "__main__":
    main()
