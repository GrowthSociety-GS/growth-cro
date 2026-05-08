#!/usr/bin/env python3
"""
score_utility_banner.py — Scorer Bloc 7 Utility Elements (UTILITY_BANNER) V3.

Usage:
    python score_utility_banner.py <label> [pageType]

Reads:
  data/captures/<label>/<pageType>/perception_v13.json  (source of truth — cluster role)
  data/captures/<label>/<pageType>/capture.json         (raw HTML/overlays for CSS checks)
  data/captures/<label>/<pageType>/spatial_v9.json      (optional, for contrast/dims)

Writes:
  data/captures/<label>/<pageType>/score_utility_banner.json

Logique (Étape 1a, 2026-04-15) :
  1. Charge perception_v13.json. Si AUCUN cluster role=UTILITY_BANNER → skip propre
     ({"applicable": false, "reason": "no UTILITY_BANNER cluster"}).
  2. Détecte variant (PROMO / REASSURANCE / UNKNOWN) via regex sur le texte cluster.
  3. Évalue les 7 critères ut_01 → ut_07 (certains skip si variant≠PROMO).
  4. Applique killers (ut_01_critical, ut_02_critical_promo).
  5. Renvoie total normalisé /21 + rationale par critère.

Contribution au score page : cf score_page_type.py (pondération 5-10%).
"""
import json
import re
import sys
import pathlib
from typing import Any

# ────────────────────────────────────────────────────────────────
# CLI + PATHS
# ────────────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    print("Usage: score_utility_banner.py <label> [pageType]", file=sys.stderr)
    sys.exit(1)

LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else None

ROOT = pathlib.Path(__file__).resolve().parents[3]
if PAGE_TYPE:
    BASE = ROOT / "data" / "captures" / LABEL / PAGE_TYPE
elif (ROOT / "data" / "captures" / LABEL / "home").exists():
    BASE = ROOT / "data" / "captures" / LABEL / "home"
    PAGE_TYPE = "home"
else:
    BASE = ROOT / "data" / "captures" / LABEL
    PAGE_TYPE = PAGE_TYPE or "home"

PERC_PATH = BASE / "perception_v13.json"
CAP_PATH = BASE / "capture.json"
SPATIAL_PATH = BASE / "spatial_v9.json"
OUT_PATH = BASE / "score_utility_banner.json"
PLAYBOOK = ROOT / "playbook" / "bloc_utility_elements_v3.json"

# ────────────────────────────────────────────────────────────────
# REGEX PATTERNS (variant detection + criteria)
# ────────────────────────────────────────────────────────────────
PROMO_REGEX = re.compile(
    r"(-\s?\d+\s?%|\b\d+\s?%\s?(off|de réduction)\b|code\s*promo|soldes?|"
    r"black\s?friday|cyber\s?(monday|week)?|flash|exclu|fin de stock|"
    r"24\s?h\b|offre\s+(spéciale|limitée|exceptionnelle)|promo)",
    re.IGNORECASE,
)
REASSURANCE_REGEX = re.compile(
    r"(livraison\s+(offerte|gratuite)|retour\s+(offert|gratuit)|garantie|"
    r"paiement\s+sécurisé|made\s+in\s+france|avis\s+vérifiés|satisfait\s+ou\s+remboursé|"
    r"fabriqué\s+en|expédi[eé])",
    re.IGNORECASE,
)
TIMEFRAME_REGEX = re.compile(
    r"\b(jusqu'au|until|aujourd'hui|ce soir|fin\s+(de|du)|expir|plus que|"
    r"\d+\s*h\b|\d+\s*j\b|countdown|timer|\d{1,2}/\d{1,2})\b",
    re.IGNORECASE,
)
REASON_REGEX = re.compile(
    r"\b(black\s?friday|cyber|soldes?|noël|noel|saint[- ]valentin|anniv|"
    r"premier\s+achat|nouveau\s+client|bienvenue|exclu|stock|halloween|printemps)\b",
    re.IGNORECASE,
)
AGGRESSIVE_MARKERS = ["!!!", "FLASH", "ALERTE", "DERNIÈRE CHANCE", "🔥", "⚡", "-70", "-80"]
PREMIUM_MARKERS = ["artisan", "savoir-faire", "luxe", "exclusif", "maison", "héritage", "couture", "premium", "signature"]


# ────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────
def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def find_utility_banner(perception: dict) -> dict | None:
    """Retourne le cluster role=UTILITY_BANNER (ou None)."""
    for c in perception.get("clusters", []) or []:
        if c.get("role") == "UTILITY_BANNER":
            return c
    return None


def detect_variant(text: str) -> str:
    has_promo = bool(PROMO_REGEX.search(text))
    has_reassurance = bool(REASSURANCE_REGEX.search(text))
    if has_promo and not has_reassurance:
        return "PROMO"
    if has_reassurance and not has_promo:
        return "REASSURANCE"
    if has_promo and has_reassurance:
        # Mixte : on garde PROMO (plus contraignant, killers actifs)
        return "PROMO"
    return "UNKNOWN"


def cluster_text(cluster: dict) -> str:
    elems = cluster.get("elements") or []
    parts = []
    for e in elems:
        t = (e.get("text") or "").strip()
        if t:
            parts.append(t)
    return " ".join(parts)


def cluster_bbox(cluster: dict) -> dict:
    bbox = cluster.get("bbox") or {}
    return {
        "x": bbox.get("x", 0),
        "y": bbox.get("y", 0),
        "w": bbox.get("w", 0) or bbox.get("width", 0),
        "h": bbox.get("h", 0) or bbox.get("height", 0),
    }


def viewport_height(perception: dict, default: int = 900) -> int:
    vp = perception.get("viewport") or {}
    return int(vp.get("h") or vp.get("height") or default)


# ────────────────────────────────────────────────────────────────
# CRITERIA SCORERS
# ────────────────────────────────────────────────────────────────
def score_ut_01(cluster: dict, perception: dict) -> dict:
    """Proportion du fold occupée."""
    bbox = cluster_bbox(cluster)
    h = bbox["h"]
    fold = viewport_height(perception, 900)
    ratio = (h / fold) if fold else 0
    evidence = {"banner_height_px": round(h, 1), "fold_height_px": fold, "ratio_fold": round(ratio, 3)}
    if ratio < 0.05:
        return {"id": "ut_01", "label": "Proportion du fold occupée", "score": 3, "max": 3,
                "verdict": "top", "evidence": evidence,
                "rationale": f"Bandeau {round(h,0)}px ({ratio*100:.1f}% du fold) — n'étouffe pas la value prop."}
    if ratio <= 0.12:
        return {"id": "ut_01", "label": "Proportion du fold occupée", "score": 2, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": f"Bandeau {round(h,0)}px ({ratio*100:.1f}% du fold) — acceptable."}
    return {"id": "ut_01", "label": "Proportion du fold occupée", "score": 0, "max": 3,
            "verdict": "critical", "evidence": evidence,
            "rationale": f"Bandeau {round(h,0)}px ({ratio*100:.1f}% du fold) > 12% — étouffe la value prop. Killer actif."}


def score_ut_02(text: str, variant: str) -> dict | None:
    """Crédibilité du mécanisme (PROMO uniquement)."""
    if variant != "PROMO":
        return None
    has_time = bool(TIMEFRAME_REGEX.search(text))
    has_reason = bool(REASON_REGEX.search(text))
    evidence = {"has_timeframe": has_time, "has_reason": has_reason, "text_sample": text[:200]}
    if has_time and has_reason:
        return {"id": "ut_02", "label": "Crédibilité mécanisme promo", "score": 3, "max": 3,
                "verdict": "top", "evidence": evidence,
                "rationale": "Cadre temporel ET raison présents — promo crédible."}
    if has_time or has_reason:
        return {"id": "ut_02", "label": "Crédibilité mécanisme promo", "score": 2, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": f"{'Cadre temporel' if has_time else 'Raison'} présent, l'autre manque."}
    return {"id": "ut_02", "label": "Crédibilité mécanisme promo", "score": 0, "max": 3,
            "verdict": "critical", "evidence": evidence,
            "rationale": "Ni cadre temporel ni raison — promo perçue comme permanente / prix barré artificiel. Killer actif."}


def score_ut_03(text: str, perception: dict) -> dict:
    """Cohérence offre × produit-hero."""
    hero_text = ""
    for c in perception.get("clusters", []) or []:
        if c.get("role") == "HERO":
            hero_text = cluster_text(c)
            break
    # Naïf : overlap de tokens significatifs (>4 chars, non-stopwords)
    STOP = {"pour", "avec", "dans", "votre", "vous", "nous", "cette", "tout", "tous", "toutes"}
    def toks(s: str) -> set:
        return {w.lower() for w in re.findall(r"\b[\wÀ-ÿ]{4,}\b", s) if w.lower() not in STOP}
    banner_toks = toks(text)
    hero_toks = toks(hero_text)
    overlap = banner_toks & hero_toks
    evidence = {"banner_tokens": sorted(banner_toks)[:20], "hero_tokens": sorted(hero_toks)[:20],
                "overlap": sorted(overlap)}
    # Universelle réassurance (livraison / paiement / retour) = OK par défaut même sans overlap
    is_universal = bool(REASSURANCE_REGEX.search(text))
    if len(overlap) >= 2 or is_universal:
        return {"id": "ut_03", "label": "Cohérence offre × produit-hero", "score": 3, "max": 3,
                "verdict": "top", "evidence": evidence,
                "rationale": f"Cohérence sémantique {'(réassurance universelle)' if is_universal else '(overlap '+str(len(overlap))+')'}."}
    if len(overlap) == 1:
        return {"id": "ut_03", "label": "Cohérence offre × produit-hero", "score": 2, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": "Cohérence partielle (1 token commun)."}
    return {"id": "ut_03", "label": "Cohérence offre × produit-hero", "score": 0, "max": 3,
            "verdict": "critical", "evidence": evidence,
            "rationale": "Aucun overlap sémantique banner↔hero — friction cognitive possible."}


def score_ut_04(text: str, variant: str, capture: dict) -> dict | None:
    """Scent trail paid match (PROMO uniquement)."""
    if variant != "PROMO":
        return None
    utms = {}
    url = (capture.get("meta") or {}).get("url") or capture.get("url") or ""
    for m in re.finditer(r"utm_(\w+)=([^&]+)", url):
        utms[m.group(1)] = m.group(2)
    evidence = {"utms_captured": utms, "banner_text_sample": text[:200]}
    # Fallback : en l'absence d'UTM, tag 'ok' par défaut si promo cohérente (pas d'agressivité contradictoire)
    if not utms:
        return {"id": "ut_04", "label": "Scent trail paid match", "score": 2, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": "Pas d'UTM capturés — fallback sur cohérence contextuelle (no contradiction flag)."}
    # Si UTM campagne contient un %age, vérifier qu'il matche
    campaign = (utms.get("campaign") or "").lower()
    m = re.search(r"-?(\d+)\s*%?", campaign)
    if m:
        promised = int(m.group(1))
        banner_m = re.search(r"-?(\d+)\s*%", text)
        if banner_m and abs(int(banner_m.group(1)) - promised) <= 5:
            return {"id": "ut_04", "label": "Scent trail paid match", "score": 3, "max": 3,
                    "verdict": "top", "evidence": evidence,
                    "rationale": "UTM campagne matche la promesse bandeau."}
        if banner_m:
            return {"id": "ut_04", "label": "Scent trail paid match", "score": 0, "max": 3,
                    "verdict": "critical", "evidence": evidence,
                    "rationale": f"UTM annonce -{promised}% mais bandeau annonce -{banner_m.group(1)}% — contradiction."}
    return {"id": "ut_04", "label": "Scent trail paid match", "score": 2, "max": 3,
            "verdict": "ok", "evidence": evidence,
            "rationale": "UTM présent, pas de contradiction détectée."}


def score_ut_05(cluster: dict, spatial: dict) -> dict:
    """Contraste & lisibilité."""
    elem_ids = {(e.get("id") or i) for i, e in enumerate(cluster.get("elements") or [])}
    # Fallback : utilise les elements du cluster directement (spatial_v9 fusion non triviale sans IDs)
    sizes = []
    texts = []
    for e in cluster.get("elements") or []:
        fs = (e.get("computedStyle") or {}).get("fontSize", "")
        m = re.match(r"([\d.]+)", fs or "")
        if m:
            sizes.append(float(m.group(1)))
        t = (e.get("text") or "").strip()
        if t:
            texts.append(t)
    min_size = min(sizes) if sizes else None
    evidence = {"font_sizes_px": sizes[:10], "min_font_size": min_size,
                "text_samples": texts[:3]}
    if min_size is None:
        return {"id": "ut_05", "label": "Contraste & lisibilité", "score": 1, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": "Pas de font-size détecté — fallback neutre (à valider manuellement)."}
    if min_size >= 14:
        return {"id": "ut_05", "label": "Contraste & lisibilité", "score": 3, "max": 3,
                "verdict": "top", "evidence": evidence,
                "rationale": f"Font-size min {min_size}px ≥ 14 — lisible."}
    if min_size >= 12:
        return {"id": "ut_05", "label": "Contraste & lisibilité", "score": 2, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": f"Font-size min {min_size}px — WCAG AA acceptable."}
    return {"id": "ut_05", "label": "Contraste & lisibilité", "score": 0, "max": 3,
            "verdict": "critical", "evidence": evidence,
            "rationale": f"Font-size min {min_size}px < 12 — illisible."}


def score_ut_06(cluster: dict, capture: dict) -> dict:
    """Dismissibility & persistance."""
    has_dismiss = False
    for e in cluster.get("elements") or []:
        text = (e.get("text") or "").strip().lower()
        if e.get("type") in ("button", "cta") and (text in ("×", "x", "fermer", "close") or "fermer" in text):
            has_dismiss = True
            break
    # fallback : chercher "×" dans les textes du cluster
    if not has_dismiss:
        for e in cluster.get("elements") or []:
            if (e.get("text") or "").strip() in ("×", "✕", "✖"):
                has_dismiss = True
                break
    bbox = cluster_bbox(cluster)
    h = bbox["h"]
    # Sticky inference : capture.js ne capture pas toujours position:sticky.
    # Heuristique : si cluster tout en haut (y<50) et h raisonnable, supposé non-sticky.
    is_top = bbox["y"] < 50
    evidence = {"has_dismiss": has_dismiss, "banner_height_px": round(h, 1), "y_top": round(bbox["y"], 1)}
    if has_dismiss:
        return {"id": "ut_06", "label": "Dismissibility & persistance", "score": 3, "max": 3,
                "verdict": "top", "evidence": evidence,
                "rationale": "Bouton de fermeture détecté."}
    if h <= 50:
        return {"id": "ut_06", "label": "Dismissibility & persistance", "score": 2, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": f"Pas de dismiss mais empreinte limitée ({round(h,0)}px ≤ 50)."}
    return {"id": "ut_06", "label": "Dismissibility & persistance", "score": 0, "max": 3,
            "verdict": "critical", "evidence": evidence,
            "rationale": f"Pas de dismiss + {round(h,0)}px > 50 — agression UX permanente."}


def score_ut_07(text: str, perception: dict, business_category: str = "") -> dict:
    """Cohérence tonale avec la marque."""
    text_upper = text.upper()
    aggressive = sum(1 for m in AGGRESSIVE_MARKERS if m in text_upper)
    # Premium markers sur le hero
    hero_text = ""
    for c in perception.get("clusters", []) or []:
        if c.get("role") == "HERO":
            hero_text = cluster_text(c).lower()
            break
    is_premium = any(m in hero_text for m in PREMIUM_MARKERS) or business_category in ("luxury", "premium")
    evidence = {"aggressive_markers_count": aggressive, "hero_premium_signals": is_premium}
    if aggressive == 0:
        return {"id": "ut_07", "label": "Cohérence tonale marque", "score": 3, "max": 3,
                "verdict": "top", "evidence": evidence,
                "rationale": "Ton bandeau sobre, aligné avec la marque."}
    if aggressive >= 2 and is_premium:
        return {"id": "ut_07", "label": "Cohérence tonale marque", "score": 0, "max": 3,
                "verdict": "critical", "evidence": evidence,
                "rationale": f"{aggressive} marqueurs agressifs sur marque premium — dégrade la perception qualité."}
    if aggressive >= 2:
        return {"id": "ut_07", "label": "Cohérence tonale marque", "score": 1, "max": 3,
                "verdict": "ok", "evidence": evidence,
                "rationale": f"{aggressive} marqueurs agressifs (acceptable sur marque mass-market)."}
    return {"id": "ut_07", "label": "Cohérence tonale marque", "score": 2, "max": 3,
            "verdict": "ok", "evidence": evidence,
            "rationale": "Léger décalage tonal, acceptable."}


# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────
def main():
    perception = load_json(PERC_PATH)
    capture = load_json(CAP_PATH)
    spatial = load_json(SPATIAL_PATH)

    if not perception:
        OUT_PATH.write_text(json.dumps({
            "applicable": False, "reason": "perception_v13.json missing",
            "label": LABEL, "pageType": PAGE_TYPE
        }, ensure_ascii=False, indent=2))
        print(f"[skip] no perception_v13 for {LABEL}/{PAGE_TYPE}")
        return

    cluster = find_utility_banner(perception)
    if cluster is None:
        OUT_PATH.write_text(json.dumps({
            "applicable": False, "reason": "no UTILITY_BANNER cluster detected",
            "label": LABEL, "pageType": PAGE_TYPE,
            "total": 0, "max": 21, "contribution_page_score": 0
        }, ensure_ascii=False, indent=2))
        print(f"[skip] no UTILITY_BANNER for {LABEL}/{PAGE_TYPE}")
        return

    text = cluster_text(cluster)
    variant = detect_variant(text)
    business_category = (capture.get("business") or {}).get("category", "")

    # Score les 7 critères
    results = []
    r = score_ut_01(cluster, perception); results.append(r)
    r = score_ut_02(text, variant)
    if r: results.append(r)
    r = score_ut_03(text, perception); results.append(r)
    r = score_ut_04(text, variant, capture)
    if r: results.append(r)
    r = score_ut_05(cluster, spatial); results.append(r)
    r = score_ut_06(cluster, capture); results.append(r)
    r = score_ut_07(text, perception, business_category); results.append(r)

    total_raw = sum(r["score"] for r in results)
    max_raw = sum(r["max"] for r in results)

    # Killers
    killers_fired = []
    ut_01 = next((r for r in results if r["id"] == "ut_01"), None)
    ut_02 = next((r for r in results if r["id"] == "ut_02"), None)
    cap_total_21 = None
    if ut_01 and ut_01["verdict"] == "critical":
        cap_total_21 = min(cap_total_21 or 21, 7)
        killers_fired.append("ut_01_critical")
    if ut_02 and ut_02["verdict"] == "critical" and variant == "PROMO":
        cap_total_21 = min(cap_total_21 or 21, 10)
        killers_fired.append("ut_02_critical_promo")

    # Normalisation sur /21 (si certains critères skip, renormaliser)
    if max_raw > 0:
        total_21 = round((total_raw / max_raw) * 21, 2)
    else:
        total_21 = 0
    if cap_total_21 is not None:
        total_21 = min(total_21, cap_total_21)

    # Contribution au score page : 7.5% par défaut, passé à 10% si variant=PROMO sur home/pdp
    contribution_pct = 7.5
    if variant == "PROMO" and PAGE_TYPE in ("home", "pdp"):
        contribution_pct = 10.0
    elif PAGE_TYPE in ("blog", "pricing"):
        contribution_pct = 5.0

    payload = {
        "applicable": True,
        "label": LABEL,
        "pageType": PAGE_TYPE,
        "variant": variant,
        "cluster_bbox": cluster_bbox(cluster),
        "cluster_text_sample": text[:300],
        "total_raw": total_raw,
        "max_raw": max_raw,
        "total_21": total_21,
        "max": 21,
        "killers_fired": killers_fired,
        "cap_from_killers": cap_total_21,
        "contribution_page_score_pct": contribution_pct,
        "business_category": business_category,
        "criteria": results,
        "playbook_version": "3.0.0",
    }

    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[ok] {LABEL}/{PAGE_TYPE} — variant={variant} — score {total_21}/21 "
          f"(raw {total_raw}/{max_raw}) — contribution {contribution_pct}% — killers={killers_fired or 'none'}")


if __name__ == "__main__":
    main()
