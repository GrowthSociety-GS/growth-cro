#!/usr/bin/env python3
"""
perception_v13.py — Couche 1 Oracle Perception V13

Post-processe spatial_v9_clean.json + capture.json et produit perception_v13.json
qui contient :
  - elements[] enrichis avec noise_score (0-100) et cluster_id
  - clusters[] : regroupements DBSCAN adaptatifs
  - roles[] : rôles fonctionnels (UTILITY_BANNER, HERO, VALUE_PROPS, SOCIAL_PROOF,
              PRICING, FAQ, FINAL_CTA, FOOTER, NAV)

Pourquoi V13 vs V12 ?
  - V12 détecte les sections par "gap vertical > 60px" → tout est empaqueté en une
    seule "hero section" (ex: Japhy home = section_0 fait 10825px et contient 125
    éléments). Inutilisable pour scorer le vrai hero.
  - V13 : ignore les sections buggées, travaille directement sur les éléments,
    reconstruit les clusters via DBSCAN adaptatif sur (y_center, x_center) avec
    eps auto-calibré à la densité de la page.

Usage :
    python3 perception_v13.py --client japhy --page home
    python3 perception_v13.py --all   # tous les clients × pages
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────
# CONSTANTES
# ────────────────────────────────────────────────────────────────

VIEWPORT_W = 1440
FOLD_Y = 900  # hauteur du fold desktop

# Keywords qui signalent du "noise" (promo, banner, dismiss, cookie)
NOISE_KEYWORDS = re.compile(
    r"(livraison offerte|offre|promo|réduction|remise|-\d+\s?%|\d+\s?%\s?(off|de réduction)|"
    r"black\s?friday|solde|code promo|gratuit pendant|essai gratuit|"
    r"cookie|consent|rgpd|gdpr|accepter|politique de confidentialit|"
    r"newsletter|inscription|abonne|suivez.nous|"
    r"nous contacter$|mentions légales|cgv|cgu)",
    re.IGNORECASE,
)

# Tags de navigation secondaire
NAV_KEYWORDS = re.compile(
    r"(menu|nav|connexion|se connecter|mon compte|panier|rechercher|search|"
    r"langue|français|english|\bfr\b|\ben\b)",
    re.IGNORECASE,
)

# Patterns CTA principaux (forte affordance)
CTA_PRIMARY_KEYWORDS = re.compile(
    r"(commencer|démarrer|découvrir|essayer|tester|commander|acheter|"
    r"faire.le.quiz|faire.le.test|diagnostic|trouver|créer|obtenir|"
    r"start|try|get started|sign up|get|find|discover)",
    re.IGNORECASE,
)

# Footer keywords
FOOTER_KEYWORDS = re.compile(
    r"(©|copyright|tous droits réservés|mentions légales|"
    r"rejoignez.nous|suivez.nous|contactez.nous|siret|siège social)",
    re.IGNORECASE,
)

# Role priorities (le plus fort gagne si multi-match)
ROLE_PRIORITY = {
    "FOOTER": 10,
    "MODAL": 9.5,
    "UTILITY_BANNER": 9,
    "NAV": 8,
    "HERO": 7,
    "FINAL_CTA": 6,
    "PRICING": 5,
    "FAQ": 5,
    "SOCIAL_PROOF": 4,
    "VALUE_PROPS": 3,
    "CONTENT": 1,
}


# ────────────────────────────────────────────────────────────────
# UTILITIES
# ────────────────────────────────────────────────────────────────

def bbox_center(bbox: dict) -> tuple[float, float]:
    return (
        bbox.get("x", 0) + bbox.get("w", 0) / 2,
        bbox.get("y", 0) + bbox.get("h", 0) / 2,
    )


def bbox_area(bbox: dict) -> float:
    return max(0, bbox.get("w", 0)) * max(0, bbox.get("h", 0))


def parse_font_size(css_fs: str) -> float:
    if not css_fs:
        return 0.0
    m = re.match(r"([\d.]+)px", css_fs)
    return float(m.group(1)) if m else 0.0


# ────────────────────────────────────────────────────────────────
# NOISE SCORE (0-100)
# ────────────────────────────────────────────────────────────────

def compute_noise_score(el: dict, page_context: dict) -> dict:
    """
    Score 0-100 : plus c'est haut, plus l'élément est du bruit (promo, banner,
    cookie, nav secondaire, footer utilitaire…).

    Signaux combinés :
      - Text pattern (promo/consent/footer): +40
      - Position sticky/fixed hors fold: +20
      - Taille micro (<30px de haut, texte court): +15
      - Z-index > 1000: +15
      - Font-size très petit (<12px): +10
      - Tag de nav (link dans header): +10
    """
    score = 0
    reasons = []

    text = (el.get("text") or "").strip()
    bbox = el.get("bbox") or {}
    cs = el.get("computedStyle") or {}

    # 1. Text pattern promo / consent / footer
    if text and NOISE_KEYWORDS.search(text):
        score += 40
        reasons.append("noise_keyword_text")

    if text and FOOTER_KEYWORDS.search(text):
        score += 30
        reasons.append("footer_keyword")

    if text and NAV_KEYWORDS.search(text) and len(text) < 30:
        score += 15
        reasons.append("nav_keyword")

    # 2. Micro-taille (bandeau fin) — top promo banner typically 40-60px tall
    h = bbox.get("h", 0)
    w = bbox.get("w", 0)
    if 0 < h < 60 and w > 800:
        score += 20
        reasons.append("banner_thin_wide")

    # 2b. Emojis promo (⚡🔥⭐💥🎁) signalent quasi-toujours une bannière promo
    if text and re.search(r"[⚡🔥⭐💥🎁✨]", text):
        score += 15
        reasons.append("promo_emoji")

    # 3. Font tiny
    fs = parse_font_size(cs.get("fontSize", ""))
    if 0 < fs < 12:
        score += 10
        reasons.append(f"tiny_font_{fs}")

    # 4. Texte très court ou vide
    if el.get("type") == "heading" and len(text) < 3:
        score += 20
        reasons.append("empty_heading")

    # 5. Y très bas = footer probable
    page_max_y = page_context.get("max_y", 1)
    y = bbox.get("y", 0)
    if y > page_max_y * 0.92:
        score += 15
        reasons.append("near_bottom")

    # 6. Top banner fin (<80px de haut, y<100)
    if y < 100 and h < 80:
        # Signal faible seul, mais avec keyword noise → bandeau promo
        if text and (NOISE_KEYWORDS.search(text) or re.search(r"livraison|offert", text, re.I)):
            score += 20
            reasons.append("top_thin_banner_promo")

    return {
        "noise_score": min(100, score),
        "noise_reasons": reasons,
    }


# ────────────────────────────────────────────────────────────────
# DBSCAN ADAPTATIF
# ────────────────────────────────────────────────────────────────

def compute_adaptive_eps(points: list[tuple[float, float]]) -> float:
    """
    Eps auto-calibré : médiane des distances au plus proche voisin × 1.5
    Minimum 120, maximum 400.
    """
    if len(points) < 2:
        return 200.0

    neighbor_dists = []
    for i, p in enumerate(points):
        dmin = float("inf")
        for j, q in enumerate(points):
            if i == j:
                continue
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            if d < dmin:
                dmin = d
        if dmin != float("inf"):
            neighbor_dists.append(dmin)

    if not neighbor_dists:
        return 200.0
    neighbor_dists.sort()
    median = neighbor_dists[len(neighbor_dists) // 2]
    eps = median * 1.5
    return max(120.0, min(400.0, eps))


def dbscan_1d_vertical(elements: list[dict], eps: float, min_samples: int = 2) -> list[int]:
    """
    DBSCAN simplifié sur axe vertical (y_center).
    On cluster majoritairement par Y : 2 éléments sont voisins s'ils sont espacés
    de moins de eps verticalement, peu importe leur X (c'est la logique d'un
    "bloc" sur une LP).

    Returns: list de cluster_id (-1 = bruit) de même longueur qu'elements.
    """
    n = len(elements)
    if n == 0:
        return []

    labels = [-1] * n
    cluster_id = 0

    # Trier par y_center
    indexed = sorted(enumerate(elements), key=lambda t: bbox_center(t[1].get("bbox", {}))[1])

    visited = [False] * n
    for idx_in_sorted, (orig_i, el) in enumerate(indexed):
        if visited[orig_i]:
            continue
        visited[orig_i] = True

        # Trouver les voisins (dans eps vertical)
        y_i = bbox_center(el.get("bbox", {}))[1]
        neighbors = []
        for idx_j, (orig_j, el_j) in enumerate(indexed):
            if orig_j == orig_i:
                continue
            y_j = bbox_center(el_j.get("bbox", {}))[1]
            if abs(y_j - y_i) <= eps:
                neighbors.append(orig_j)

        if len(neighbors) + 1 < min_samples:
            continue  # reste -1 (bruit)

        # Nouveau cluster
        labels[orig_i] = cluster_id
        stack = list(neighbors)
        while stack:
            q = stack.pop()
            if not visited[q]:
                visited[q] = True
                y_q = bbox_center(elements[q].get("bbox", {}))[1]
                sub_neighbors = []
                for idx_k, (orig_k, el_k) in enumerate(indexed):
                    if orig_k == q:
                        continue
                    y_k = bbox_center(el_k.get("bbox", {}))[1]
                    if abs(y_k - y_q) <= eps:
                        sub_neighbors.append(orig_k)
                if len(sub_neighbors) + 1 >= min_samples:
                    stack.extend([x for x in sub_neighbors if labels[x] == -1])
            if labels[q] == -1:
                labels[q] = cluster_id

        cluster_id += 1

    return labels


def refine_clusters_by_y_gap(elements: list[dict], labels: list[int], gap_threshold: float = 150.0) -> list[int]:
    """
    Post-traitement : si un "cluster" contient plusieurs îlots d'éléments
    séparés par plus de gap_threshold pixels de vide, on le découpe.

    Ex: DBSCAN peut rassembler deux blocs par chaîne transitive ; ce gap-split
    casse les chaînes artificielles.
    """
    new_labels = labels.copy()
    unique_clusters = set(l for l in labels if l != -1)
    max_label = max(unique_clusters) if unique_clusters else -1

    for cid in unique_clusters:
        indices = [i for i, l in enumerate(labels) if l == cid]
        if len(indices) < 2:
            continue
        indices.sort(key=lambda i: bbox_center(elements[i].get("bbox", {}))[1])

        current_sub = [indices[0]]
        subclusters = [current_sub]
        for i in range(1, len(indices)):
            y_prev = bbox_center(elements[indices[i - 1]].get("bbox", {}))[1]
            y_curr = bbox_center(elements[indices[i]].get("bbox", {}))[1]
            if y_curr - y_prev > gap_threshold:
                current_sub = [indices[i]]
                subclusters.append(current_sub)
            else:
                current_sub.append(indices[i])

        if len(subclusters) > 1:
            for sub in subclusters[1:]:
                max_label += 1
                for idx in sub:
                    new_labels[idx] = max_label

    return new_labels


# ────────────────────────────────────────────────────────────────
# ROLE ASSIGNMENT PAR CLUSTER
# ────────────────────────────────────────────────────────────────

def assign_cluster_role(cluster_elements: list[dict], page_context: dict) -> dict:
    """
    Chaque cluster reçoit un rôle fonctionnel unique basé sur :
      - Position Y (fold / post-fold / bottom)
      - Composition : tags présents (h1/h2/cta/img/form)
      - Patterns de texte (prix, avis, faq, value props)
      - Taille visuelle (surface)
    """
    if not cluster_elements:
        return {"role": "NOISE", "confidence": 0}

    # Stats
    ys = [bbox_center(e.get("bbox", {}))[1] for e in cluster_elements]
    y_min = min(ys)
    y_max = max(ys)
    y_mean = sum(ys) / len(ys)
    page_max_y = page_context.get("max_y", 1)
    rel_y_min = y_min / page_max_y
    rel_y_max = y_max / page_max_y

    texts = [(e.get("text") or "").strip() for e in cluster_elements]
    joined_text = " ".join(texts).lower()

    tags = [e.get("tag") for e in cluster_elements]
    types = [e.get("type") for e in cluster_elements]

    has_h1 = "h1" in tags
    has_h2 = "h2" in tags
    has_big_heading = any(
        parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 32
        for e in cluster_elements
        if e.get("type") == "heading"
    )
    has_cta = "cta" in types
    has_form = "form" in types
    has_img = "image" in types
    avg_noise = sum(e.get("noise_score", 0) for e in cluster_elements) / len(cluster_elements)
    total_area = sum(bbox_area(e.get("bbox", {})) for e in cluster_elements)

    # Scoring par rôle (plusieurs peuvent matcher, on garde le plus fort)
    role_scores = {}
    fold_y = page_context.get("fold_y", 900)

    # UTILITY_BANNER : top de la page + keywords noise + petite surface + noise_score élevé
    # Height-gate (Étape 1a 2026-04-15) : un vrai bandeau fait <400px. Au-delà, probable MODAL
    # (ex: Seoni cluster 835px mal clusterisé comme utility banner).
    cluster_height = y_max - y_min
    if cluster_height <= 400:
        if y_min < 100 and avg_noise > 30:
            role_scores["UTILITY_BANNER"] = 80
        elif y_min < 120 and re.search(r"livraison|offert|promo|\-\d+%", joined_text):
            role_scores["UTILITY_BANNER"] = 70
    else:
        # Cluster haut mais au top de la page + keywords promo → MODAL (popup)
        if y_min < 100 and (avg_noise > 30 or re.search(r"livraison|offert|promo|\-\d+%|newsletter|inscri", joined_text)):
            role_scores["MODAL"] = 70

    # NAV : top (<200) + pas de h1/h2 grand + liens courts
    # Enrichi : presence de patterns menu sans h1 + tout le cluster dans la zone nav (y<200)
    short_link_count = sum(1 for t in texts if 0 < len(t) < 25)
    if y_max < 200 and not has_big_heading and short_link_count >= 3:
        role_scores["NAV"] = 75
    elif y_min < 150 and short_link_count >= 3 and NAV_KEYWORDS.search(joined_text):
        role_scores["NAV"] = 70

    # HERO : le cluster DOIT être au fold (pas "premiers 25% de la page" qui sur une
    # page de 10000px donnerait 2500px, absurde). Utilise le fold absolu.
    # Le cluster est considéré hero s'il commence dans le premier tiers du fold
    # ET se termine avant 1.5× le fold (donc vraiment au premier écran).
    if y_min < fold_y * 0.8 and y_max < fold_y * 1.5 and (has_h1 or has_big_heading) and has_cta:
        hero_score = 60
        if y_min < fold_y * 0.2:
            hero_score += 20
        if has_h1:
            hero_score += 15
        if has_img:
            hero_score += 5
        role_scores["HERO"] = hero_score

    # PRICING : keywords prix + plans (élargi)
    # Inclut : "39€/mois", "39 € / mois", "$39/month", "€39.99", "gratuit 14 jours",
    # "essai gratuit", "pricing", "tarifs", "plan", "abonnement", "premium/basic/pro tier"
    pricing_patterns = [
        r"\d+[.,]?\d*\s*(€|\$|£|eur|euro|usd)\s*(/\s*(mois|an|year|month|jour))?",
        r"(€|\$|£)\s*\d+[.,]?\d*",
        r"pricing|tarif|abonnement",
        r"\b(plan|forfait|offre|pack)\b",
        r"essai\s+(gratuit|free)",
        r"(gratuit|free)\s+\d+\s*(jours?|days?)",
        r"\b(basic|standard|premium|pro|enterprise|starter|business)\b.{0,20}(\d+[€\$]|gratuit|free)",
    ]
    if any(re.search(p, joined_text) for p in pricing_patterns):
        role_scores["PRICING"] = 75

    # FAQ : patterns question/réponse + accordion tags
    if re.search(r"\bfaq\b|questions fréquentes|vos questions", joined_text):
        role_scores["FAQ"] = 75
    elif sum(1 for t in texts if t.endswith("?")) >= 2:
        role_scores["FAQ"] = 65

    # SOCIAL_PROOF : témoignages, avis, étoiles, stats clients, logos
    if re.search(r"\bavis\b|témoignage|trustpilot|(\d[.,]\d)\s*/\s*5|\d+\s*étoiles|clients satisfaits|vétérinaire", joined_text):
        role_scores["SOCIAL_PROOF"] = 70
    elif has_img and len([e for e in cluster_elements if e.get("type") == "image"]) >= 3 and total_area < 200000:
        # Logos clients (plusieurs petites images alignées)
        role_scores["SOCIAL_PROOF"] = 60

    # FINAL_CTA : CTA fort en bas de page, juste avant footer
    if has_cta and rel_y_min > 0.7 and rel_y_max < 0.95:
        if any(CTA_PRIMARY_KEYWORDS.search(t) for t in texts if t):
            role_scores["FINAL_CTA"] = 70

    # FOOTER : y très bas ET keywords (AND, pas OR : éviter que "Contactez-nous"
    # dans un NAV top-page soit labellé FOOTER. Un footer est toujours spatial).
    # Cas 1 : rel_y_min > 0.9 suffit (footer positionnel)
    # Cas 2 : rel_y_min > 0.6 + keywords footer (copyright, mentions légales, etc.)
    if rel_y_min > 0.9:
        role_scores["FOOTER"] = 85
    elif rel_y_min > 0.6 and FOOTER_KEYWORDS.search(joined_text):
        role_scores["FOOTER"] = 75

    # VALUE_PROPS : blocs milieu de page, plusieurs titres de même niveau, pas de pricing/faq
    if 0.15 < rel_y_min < 0.7 and has_h2 and len(cluster_elements) >= 3 and "PRICING" not in role_scores and "FAQ" not in role_scores:
        role_scores["VALUE_PROPS"] = 55

    # CONTENT (fallback)
    if not role_scores:
        role_scores["CONTENT"] = 30

    # Pick highest by (score × priority tie-break)
    best_role = max(
        role_scores.items(),
        key=lambda kv: (kv[1], ROLE_PRIORITY.get(kv[0], 0)),
    )

    return {
        "role": best_role[0],
        "confidence": best_role[1],
        "alt_roles": [(r, s) for r, s in sorted(role_scores.items(), key=lambda x: -x[1])][1:4],
        "y_min": y_min,
        "y_max": y_max,
        "rel_y": (round(rel_y_min, 3), round(rel_y_max, 3)),
        "has_h1": has_h1,
        "has_cta": has_cta,
        "element_count": len(cluster_elements),
    }


# ────────────────────────────────────────────────────────────────
# MAIN PROCESSING
# ────────────────────────────────────────────────────────────────

def process_page(spatial_path: Path, capture_path: Path, out_path: Path) -> dict:
    """
    Traite une page : flatten elements → noise_score → cluster → roles → write perception_v13.json.
    Retourne un résumé pour logging.
    """
    with open(spatial_path) as f:
        spatial = json.load(f)
    capture = {}
    if capture_path.exists():
        with open(capture_path) as f:
            capture = json.load(f)

    # Flatten elements (ignorer les sections buggées de V12)
    raw_els = []
    for sec in spatial.get("sections", []):
        for el in sec.get("elements", []):
            el_copy = dict(el)
            el_copy["_src_section_id"] = sec.get("id")
            el_copy["_src_section_type"] = sec.get("type")
            raw_els.append(el_copy)

    # Dédup : la capture V12 double quasi systématiquement les éléments.
    # Clé de dédup : (tag, text, bbox exact).
    seen = {}
    all_els = []
    for el in raw_els:
        bbox = el.get("bbox") or {}
        key = (
            el.get("tag"),
            el.get("type"),
            (el.get("text") or "").strip(),
            bbox.get("x"),
            bbox.get("y"),
            bbox.get("w"),
            bbox.get("h"),
        )
        if key in seen:
            continue
        seen[key] = True
        all_els.append(el)

    dedup_dropped = len(raw_els) - len(all_els)
    if dedup_dropped > 0:
        print(f"  ℹ️  dédup: {len(raw_els)} → {len(all_els)} (-{dedup_dropped} duplicates)")

    if not all_els:
        print(f"  ⚠️  {spatial_path} : aucun élément, skip.")
        return {"status": "empty"}

    # Page context
    max_y = max(
        (el.get("bbox", {}).get("y", 0) + el.get("bbox", {}).get("h", 0) for el in all_els),
        default=1,
    )
    page_context = {"max_y": max_y, "viewport_w": VIEWPORT_W, "fold_y": FOLD_Y}

    # 1. Noise scoring
    for el in all_els:
        ns = compute_noise_score(el, page_context)
        el["noise_score"] = ns["noise_score"]
        el["noise_reasons"] = ns["noise_reasons"]

    # 2. Filtrer les vrais noise (>=60) du clustering
    # Mais on les garde dans la sortie marqués NOISE
    NOISE_THRESHOLD = 60
    non_noise_els = [el for el in all_els if el.get("noise_score", 0) < NOISE_THRESHOLD]
    noise_els = [el for el in all_els if el.get("noise_score", 0) >= NOISE_THRESHOLD]

    # 3a. Pré-extraire la zone NAV (y<100, tags a|button, textes courts) pour
    # éviter que DBSCAN fusionne la nav avec le hero.
    NAV_ZONE_Y = 100
    nav_els = []
    rest_els = []
    for el in non_noise_els:
        y = el.get("bbox", {}).get("y", 999999)
        h = el.get("bbox", {}).get("h", 0)
        txt = (el.get("text") or "").strip()
        is_nav = (
            y < NAV_ZONE_Y
            and (y + h) < NAV_ZONE_Y + 50  # tout tient dans la nav zone
            and el.get("type") in ("cta", "heading")
            and 0 < len(txt) < 30  # libellé court
            and not re.search(r"^(commencer|démarrer|faire.le.quiz|start)", txt, re.I)  # CTA primaire hero-like
        )
        if is_nav:
            nav_els.append(el)
        else:
            rest_els.append(el)

    # 3b. Clustering DBSCAN adaptatif sur le reste (hors nav)
    if len(rest_els) >= 2:
        centers = [bbox_center(el.get("bbox", {})) for el in rest_els]
        eps = compute_adaptive_eps(centers)
        labels = dbscan_1d_vertical(rest_els, eps=eps, min_samples=2)
        labels = refine_clusters_by_y_gap(rest_els, labels, gap_threshold=eps * 1.2)
    else:
        eps = 200.0
        labels = [-1] * len(rest_els)

    for el, lab in zip(rest_els, labels):
        el["cluster_id"] = int(lab) if lab >= 0 else None

    # La nav forme un cluster dédié si ≥2 éléments
    if len(nav_els) >= 2:
        nav_cluster_id = (max((l for l in labels if l is not None and l >= 0), default=-1) + 1)
        for el in nav_els:
            el["cluster_id"] = nav_cluster_id
            el["_is_nav_prezone"] = True
    else:
        # Trop peu pour un cluster, on remet les éléments dans le flow normal
        for el in nav_els:
            el["cluster_id"] = None
            rest_els.append(el)

    for el in noise_els:
        el["cluster_id"] = None  # NOISE explicite

    # Fusionner la liste non_noise_els = rest_els + nav_els (pour la suite)
    non_noise_els = rest_els + (nav_els if len(nav_els) >= 2 else [])

    # 4. Build clusters dict
    clusters_map: dict[int, list[dict]] = {}
    for el in non_noise_els:
        cid = el.get("cluster_id")
        if cid is None:
            continue
        clusters_map.setdefault(cid, []).append(el)

    clusters_out = []
    for cid, cluster_els in sorted(clusters_map.items()):
        role_info = assign_cluster_role(cluster_els, page_context)
        # Bbox agrégée
        xs = [e.get("bbox", {}).get("x", 0) for e in cluster_els]
        ys = [e.get("bbox", {}).get("y", 0) for e in cluster_els]
        xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in cluster_els]
        yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in cluster_els]
        bbox = {
            "x": min(xs) if xs else 0,
            "y": min(ys) if ys else 0,
            "w": (max(xws) - min(xs)) if xs else 0,
            "h": (max(yhs) - min(ys)) if ys else 0,
        }
        clusters_out.append(
            {
                "cluster_id": cid,
                "role": role_info["role"],
                "confidence": role_info["confidence"],
                "alt_roles": role_info["alt_roles"],
                "bbox": bbox,
                "element_count": len(cluster_els),
                "has_h1": role_info["has_h1"],
                "has_cta": role_info["has_cta"],
                "rel_y": role_info["rel_y"],
                "element_indices": [all_els.index(e) for e in cluster_els],
            }
        )

    # 5. Sort clusters by y
    clusters_out.sort(key=lambda c: c["bbox"]["y"])

    # 5b. Merge fold clusters into HERO
    #
    # Problème DBSCAN 1D : sur Japhy le H1 est à y=170 mais les CTAs hero sont à
    # y=610. Le gap de ~440px les sépare en 2+ clusters distincts. Résultat :
    # cluster H1-only et cluster CTA-only → aucun ne match HERO (qui exige h1+cta).
    #
    # Fix : on identifie tous les clusters strictement au-dessus du fold (y_max <
    # fold_y + marge) qui ensemble contiennent ≥1 h1/big_heading ET ≥1 cta, on les
    # fusionne en un seul cluster HERO.
    fold_cut = FOLD_Y + 100  # petite marge tolérée (ex: CTA légèrement sous le fold)
    fold_candidates = [c for c in clusters_out if c["bbox"]["y"] + c["bbox"]["h"] <= fold_cut]
    # Exclure les clusters déjà identifiés comme NAV ou UTILITY_BANNER (top-top)
    fold_heros = [c for c in fold_candidates if c["role"] not in ("NAV", "UTILITY_BANNER", "FOOTER")]

    merged_hero_done = False
    if fold_heros and len(fold_heros) >= 2:
        has_h1_anywhere = any(c["has_h1"] for c in fold_heros)
        has_cta_anywhere = any(c["has_cta"] for c in fold_heros)
        has_big_heading_anywhere = False
        for c in fold_heros:
            for idx in c["element_indices"]:
                e = all_els[idx]
                if e.get("type") == "heading":
                    if parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 32:
                        has_big_heading_anywhere = True
                        break
            if has_big_heading_anywhere:
                break

        if (has_h1_anywhere or has_big_heading_anywhere) and has_cta_anywhere:
            # On garde le cluster du H1 comme "base" (cluster_id le plus petit y),
            # on réassigne role=HERO, et on fusionne les element_indices.
            merged = sorted(fold_heros, key=lambda c: c["bbox"]["y"])
            base = merged[0]
            all_indices = []
            for c in merged:
                all_indices.extend(c["element_indices"])
            all_indices = sorted(set(all_indices))

            # Recompute bbox
            base_elems = [all_els[i] for i in all_indices]
            xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
            ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
            xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
            yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
            merged_bbox = {
                "x": min(xs),
                "y": min(ys),
                "w": max(xws) - min(xs),
                "h": max(yhs) - min(ys),
            }
            has_h1_merged = any(e.get("tag") == "h1" for e in base_elems)
            has_cta_merged = any(e.get("type") == "cta" for e in base_elems)

            hero_cluster = {
                "cluster_id": base["cluster_id"],
                "role": "HERO",
                "confidence": 90,
                "alt_roles": [],
                "bbox": merged_bbox,
                "element_count": len(all_indices),
                "has_h1": has_h1_merged,
                "has_cta": has_cta_merged,
                "rel_y": (round(merged_bbox["y"] / max_y, 3), round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                "element_indices": all_indices,
                "_merged_from": [c["cluster_id"] for c in merged],
            }

            # Réassigner les cluster_id des éléments mergés
            for i in all_indices:
                all_els[i]["cluster_id"] = hero_cluster["cluster_id"]

            # Remplacer dans clusters_out : retirer les clusters mergés, insérer HERO
            clusters_out = [c for c in clusters_out if c["cluster_id"] not in hero_cluster["_merged_from"]]
            clusters_out.append(hero_cluster)
            clusters_out.sort(key=lambda c: c["bbox"]["y"])
            merged_hero_done = True

    if not merged_hero_done:
        # Dernier recours : si aucun cluster n'a le rôle HERO mais qu'il existe un
        # cluster fold avec un h1, on le promeut HERO d'office (single-cluster case).
        hero_exists = any(c["role"] == "HERO" for c in clusters_out)
        if not hero_exists:
            for c in clusters_out:
                if c["bbox"]["y"] < fold_cut and c["has_h1"]:
                    c["role"] = "HERO"
                    c["confidence"] = 70
                    break

    # 5c. ORPHAN HERO RESCUE
    # Bug : sur certaines pages le H1 hero est trop éloigné verticalement de ses
    # voisins (titre à y=200, sous-titre à y=500, CTA à y=700) et DBSCAN
    # avec eps capped à 400px le laisse orphelin (cluster_id=None). Résultat :
    # aucun cluster ne contient le H1, donc le fallback HERO échoue.
    #
    # Fix : après tout le clustering, si aucun HERO n'a été détecté, on construit
    # un cluster synthétique HERO depuis les éléments orphelins du fold (les
    # non_noise_els avec cluster_id=None et y < rescue_fold_cut), à condition qu'il
    # contienne ≥1 h1/big_heading.
    #
    # NOTE : le fold_cut normal est FOLD_Y+100 (1000px). Pour le RESCUE, on étend
    # jusqu'à FOLD_Y*2 (1800px) car certaines pages (ex: oma_me/home) ont un H1
    # hero à y=1316 à cause d'un gros header/banner (utility + nav + announcement).
    rescue_fold_cut = FOLD_Y * 2  # 1800px
    hero_exists_now = any(c["role"] == "HERO" for c in clusters_out)
    if not hero_exists_now:
        fold_orphans = [
            el for el in non_noise_els
            if el.get("cluster_id") is None
            and el.get("bbox", {}).get("y", 999999) < rescue_fold_cut
        ]
        # On inclut aussi les éléments du fold déjà clusterisés SAUF ceux
        # dans NAV/UTILITY_BANNER/FOOTER (pour ne pas casser la nav).
        excluded_cids = {c["cluster_id"] for c in clusters_out
                         if c["role"] in ("NAV", "UTILITY_BANNER", "FOOTER")}
        fold_extra = [
            el for el in non_noise_els
            if el.get("cluster_id") is not None
            and el.get("cluster_id") not in excluded_cids
            and el.get("bbox", {}).get("y", 999999) < rescue_fold_cut
        ]
        hero_pool = fold_orphans + fold_extra
        if hero_pool:
            has_h1_pool = any(e.get("tag") == "h1" for e in hero_pool)
            has_big_heading_pool = any(
                e.get("type") == "heading"
                and parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 32
                for e in hero_pool
            )
            has_cta_pool = any(e.get("type") == "cta" for e in hero_pool)

            if (has_h1_pool or has_big_heading_pool) and has_cta_pool:
                # Construire un cluster HERO synthétique
                all_indices = sorted(set(all_els.index(e) for e in hero_pool))
                base_elems = [all_els[i] for i in all_indices]
                xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
                ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
                xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
                yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
                merged_bbox = {
                    "x": min(xs), "y": min(ys),
                    "w": max(xws) - min(xs), "h": max(yhs) - min(ys),
                }
                hero_cid = max((c["cluster_id"] for c in clusters_out), default=-1) + 1
                hero_cluster = {
                    "cluster_id": hero_cid,
                    "role": "HERO",
                    "confidence": 75,  # reconstitué, moins haut que le merge normal
                    "alt_roles": [],
                    "bbox": merged_bbox,
                    "element_count": len(all_indices),
                    "has_h1": any(e.get("tag") == "h1" for e in base_elems),
                    "has_cta": any(e.get("type") == "cta" for e in base_elems),
                    "rel_y": (round(merged_bbox["y"] / max_y, 3),
                              round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                    "element_indices": all_indices,
                    "_reconstituted_from_orphans": True,
                }
                # Réassigner les cluster_id des éléments absorbés
                for i in all_indices:
                    all_els[i]["cluster_id"] = hero_cid
                # Retirer les clusters absorbés (ceux dans fold_extra)
                absorbed_cids = {e.get("cluster_id") for e in fold_extra if e.get("cluster_id") is not None}
                absorbed_cids.discard(hero_cid)
                clusters_out = [c for c in clusters_out if c["cluster_id"] not in absorbed_cids]
                clusters_out.append(hero_cluster)
                clusters_out.sort(key=lambda c: c["bbox"]["y"])

            elif has_h1_pool or has_big_heading_pool:
                # Pas de CTA mais h1 présent : HERO "statement only" — encore valide,
                # certaines homepages ont leur CTA en NAV (Get Started header) et h1 seul dans fold.
                all_indices = sorted(set(all_els.index(e) for e in hero_pool
                                         if e.get("tag") in ("h1", "h2") or e.get("type") == "heading"))
                if all_indices:
                    base_elems = [all_els[i] for i in all_indices]
                    xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
                    ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
                    xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
                    yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
                    merged_bbox = {
                        "x": min(xs), "y": min(ys),
                        "w": max(xws) - min(xs), "h": max(yhs) - min(ys),
                    }
                    hero_cid = max((c["cluster_id"] for c in clusters_out), default=-1) + 1
                    hero_cluster = {
                        "cluster_id": hero_cid,
                        "role": "HERO",
                        "confidence": 60,  # hero sans CTA interne = moins fiable
                        "alt_roles": [],
                        "bbox": merged_bbox,
                        "element_count": len(all_indices),
                        "has_h1": any(e.get("tag") == "h1" for e in base_elems),
                        "has_cta": False,
                        "rel_y": (round(merged_bbox["y"] / max_y, 3),
                                  round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                        "element_indices": all_indices,
                        "_reconstituted_from_orphans": True,
                        "_hero_without_cta": True,
                    }
                    for i in all_indices:
                        all_els[i]["cluster_id"] = hero_cid
                    clusters_out.append(hero_cluster)
                    clusters_out.sort(key=lambda c: c["bbox"]["y"])

    # 5c-tier3. HERO FALLBACK ULTIME (pas de h1 ET pas de big_heading ≥32px)
    # Cas réel : seoni/home (h2 21px + CTA), reverso/home, georide/pdp.
    # Certaines pages DTC modernes ont leur "titre" en h2/p 20-28px pour le design,
    # avec le vrai H1 invisible (aria-label) ou absent. On doit quand même avoir
    # un HERO pour pouvoir scorer correctement.
    #
    # Règle : si toujours pas de HERO après tier1+tier2, on promeut le 1er cluster
    # (non-NAV/UTILITY/FOOTER) dans le rescue_fold qui contient au moins un CTA
    # OU au moins un heading (h1/h2/h3 ou type=heading) de ≥18px. Confidence=50.
    hero_exists_now = any(c["role"] == "HERO" for c in clusters_out)
    if not hero_exists_now:
        # Chercher d'abord parmi les clusters existants (fold_cut étendu à rescue_fold_cut)
        candidate = None
        for c in sorted(clusters_out, key=lambda x: x["bbox"]["y"]):
            if c["role"] in ("NAV", "UTILITY_BANNER", "FOOTER"):
                continue
            if c["bbox"]["y"] >= rescue_fold_cut:
                continue
            c_elems = [all_els[i] for i in c.get("element_indices", [])]
            has_cta_c = any(e.get("type") == "cta" for e in c_elems)
            has_heading_c = any(
                (e.get("tag") in ("h1", "h2", "h3") or e.get("type") == "heading")
                and parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 18
                for e in c_elems
            )
            if has_cta_c or has_heading_c:
                candidate = c
                break
        if candidate is not None:
            candidate["role"] = "HERO"
            candidate["confidence"] = 50
            candidate["_hero_tier3_fallback"] = True
        else:
            # Vraiment aucun cluster exploitable : on construit un pseudo-HERO depuis
            # les premiers éléments significatifs (heading OU cta) sous le fold étendu.
            pool = [
                el for el in non_noise_els
                if el.get("bbox", {}).get("y", 999999) < rescue_fold_cut
                and (el.get("type") in ("heading", "cta") or el.get("tag") in ("h1", "h2", "h3"))
            ]
            if pool:
                pool.sort(key=lambda e: e.get("bbox", {}).get("y", 0))
                top_pool = pool[:6]
                all_indices = sorted(set(all_els.index(e) for e in top_pool))
                base_elems = [all_els[i] for i in all_indices]
                xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
                ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
                xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
                yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
                merged_bbox = {
                    "x": min(xs), "y": min(ys),
                    "w": max(xws) - min(xs), "h": max(yhs) - min(ys),
                }
                hero_cid = max((c["cluster_id"] for c in clusters_out), default=-1) + 1
                hero_cluster = {
                    "cluster_id": hero_cid,
                    "role": "HERO",
                    "confidence": 45,
                    "alt_roles": [],
                    "bbox": merged_bbox,
                    "element_count": len(all_indices),
                    "has_h1": any(e.get("tag") == "h1" for e in base_elems),
                    "has_cta": any(e.get("type") == "cta" for e in base_elems),
                    "rel_y": (round(merged_bbox["y"] / max_y, 3),
                              round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                    "element_indices": all_indices,
                    "_reconstituted_from_orphans": True,
                    "_hero_tier3_fallback": True,
                }
                for i in all_indices:
                    all_els[i]["cluster_id"] = hero_cid
                clusters_out.append(hero_cluster)
                clusters_out.sort(key=lambda c: c["bbox"]["y"])

    # 5d. PRICING RESCUE (page-type aware)
    # Bug : sur les pages pricing, la règle PRICING (regex prix) a parfois perdu
    # face à HERO (h1+cta) alors que le cluster CONTIENT bien des prix.
    # Fix : si la page est pricing/tarif et qu'aucun cluster n'a role PRICING mais
    # qu'au moins un a "PRICING" dans ses alt_roles, on le promeut PRICING (sauf
    # le HERO et la NAV — on garde leur rôle primaire).
    # Additionnellement, on scanne les clusters avec du texte prix pour les
    # promouvoir si pas déjà typés PRICING/HERO/NAV/FOOTER.
    # Résoudre page_type_guess en écartant "unknown"/"" des sources primaires,
    # sinon on manque les pages dont meta.pageType est "unknown" alors que le
    # nom du dossier est explicite (ex: "pricing", "pdp"…).
    _pt_candidates = [
        spatial.get("meta", {}).get("pageType"),
        (capture.get("meta", {}) or {}).get("pageType"),
        spatial_path.parent.name,
    ]
    page_type_guess = ""
    for _pt in _pt_candidates:
        if _pt and str(_pt).strip().lower() not in ("unknown", "none", ""):
            page_type_guess = str(_pt)
            break
    if not page_type_guess:
        page_type_guess = spatial_path.parent.name or ""
    is_pricing_page = bool(re.search(r"pricing|tarif|abonnement|plan", page_type_guess.lower()))

    if is_pricing_page:
        has_pricing_role = any(c["role"] == "PRICING" for c in clusters_out)
        price_re = re.compile(
            r"\d+[\s,.]*\d*\s*(€|\$|eur|euro)(\s*/\s*(mois|an|year|month))?"
            r"|\d+[.,]\d{2}\s*(€|\$)"
            r"|gratuit(?:ement)?|free(?: forever)?|\bessai\b",
            re.I,
        )
        if not has_pricing_role:
            # Priorité 1 : promouvoir un cluster qui a PRICING en alt_roles
            for c in clusters_out:
                if c["role"] in ("HERO", "NAV", "UTILITY_BANNER", "FOOTER"):
                    continue
                alt = [r for r, s in (c.get("alt_roles") or [])]
                if "PRICING" in alt:
                    c["role"] = "PRICING"
                    c["confidence"] = max(c.get("confidence", 0), 75)
                    has_pricing_role = True
                    break
            # Priorité 2 : scanner le texte agrégé des clusters mid-page
            if not has_pricing_role:
                for c in clusters_out:
                    if c["role"] in ("HERO", "NAV", "UTILITY_BANNER", "FOOTER", "PRICING"):
                        continue
                    cluster_text = " ".join(
                        (all_els[i].get("text") or "") for i in c.get("element_indices", [])
                    )
                    if price_re.search(cluster_text):
                        c["role"] = "PRICING"
                        c["confidence"] = 70
                        c["_pricing_rescued"] = True
                        has_pricing_role = True
                        break

        # Priorité 3 : HERO/FINAL_CTA/VALUE_PROPS dual-label
        # Sur pages pricing minimalistes (ex: poppins_mila_learn/pricing avec
        # "39€/mois" dans le hero et rien d'autre), le cluster PRICING est le
        # HERO lui-même. On ne vole pas son rôle primaire (HERO) mais on ajoute
        # PRICING en alt_role dominant pour que les scorers puissent l'utiliser.
        if not has_pricing_role:
            for c in clusters_out:
                if c["role"] in ("NAV", "UTILITY_BANNER", "FOOTER"):
                    continue
                cluster_text = " ".join(
                    (all_els[i].get("text") or "") for i in c.get("element_indices", [])
                )
                if price_re.search(cluster_text):
                    # Injecter PRICING en tête des alt_roles avec score 75
                    existing_alt = list(c.get("alt_roles") or [])
                    # Retirer un éventuel ("PRICING", ...) puis ajouter en tête
                    existing_alt = [(r, s) for (r, s) in existing_alt if r != "PRICING"]
                    c["alt_roles"] = [("PRICING", 75)] + existing_alt
                    c["_pricing_dual_label"] = True
                    # Pour la suite du pipeline : si c'est un cluster non-HERO,
                    # on change quand même le rôle primaire pour refléter la
                    # page (seul le HERO garde son rôle).
                    if c["role"] != "HERO":
                        c["role"] = "PRICING"
                        c["confidence"] = max(c.get("confidence", 0), 65)
                    has_pricing_role = True
                    break

    # 6. Page-level summary
    role_counter: dict[str, int] = {}
    for c in clusters_out:
        role_counter[c["role"]] = role_counter.get(c["role"], 0) + 1

    # 7. Primary CTA (dans le HERO cluster, sinon dans n'importe quel cluster fold)
    primary_cta = None
    hero_clusters = [c for c in clusters_out if c["role"] == "HERO"]
    for c in hero_clusters:
        for idx in c["element_indices"]:
            el = all_els[idx]
            if el.get("type") == "cta" and el.get("text"):
                if not primary_cta or bbox_area(el.get("bbox", {})) > bbox_area(primary_cta.get("bbox", {})):
                    primary_cta = {
                        "text": el.get("text"),
                        "href": el.get("href"),
                        "bbox": el.get("bbox"),
                        "cluster_id": c["cluster_id"],
                    }

    output = {
        "version": "v13.0.0-perception",
        "meta": {
            "source_spatial": str(spatial_path),
            "source_capture": str(capture_path) if capture_path.exists() else None,
            "url": spatial.get("meta", {}).get("url") or (capture.get("meta", {}) or {}).get("url"),
            # Le pageType de spatial_v9 est souvent "unknown" — on préfère le nom de dossier
            # sauf si spatial_v9/capture en donne un non-trivial.
            "page_type": (
                (lambda v: v if v and v != "unknown" else None)(spatial.get("meta", {}).get("pageType"))
                or (lambda v: v if v and v != "unknown" else None)((capture.get("meta", {}) or {}).get("pageType"))
                or (lambda v: v if v and v != "unknown" else None)((capture.get("meta", {}) or {}).get("page_type"))
                or spatial_path.parent.name
            ),
            "page_max_y": max_y,
            "eps_used": round(eps, 1) if len(non_noise_els) >= 2 else None,
        },
        "stats": {
            "total_elements": len(all_els),
            "noise_filtered": len(noise_els),
            "clusters": len(clusters_out),
            "roles": role_counter,
        },
        "elements": [
            {
                **e,
                # Remove _section fields pour alléger
                "_src_section_id": e.get("_src_section_id"),
                "_src_section_type": e.get("_src_section_type"),
            }
            for e in all_els
        ],
        "clusters": clusters_out,
        "primary_cta": primary_cta,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"  ✓ {spatial_path.parent.name}: "
        f"{len(all_els)}el / {len(noise_els)}noise / {len(clusters_out)}clusters / "
        f"roles={role_counter}"
    )
    return {"status": "ok", "clusters": len(clusters_out), "roles": role_counter}


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="Label client (ex: japhy)")
    ap.add_argument("--page", help="Page type (ex: home)")
    ap.add_argument("--data-dir", default="data/captures", help="Base data dir")
    ap.add_argument("--all", action="store_true", help="Processer tous les clients/pages")
    args = ap.parse_args()

    base = Path(args.data_dir)
    if not base.exists():
        print(f"❌ {base} n'existe pas", file=sys.stderr)
        sys.exit(1)

    targets: list[tuple[Path, Path, Path]] = []
    if args.all:
        for client_dir in sorted(base.iterdir()):
            if not client_dir.is_dir():
                continue
            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir():
                    continue
                sp = page_dir / "spatial_v9_clean.json"
                if not sp.exists():
                    sp = page_dir / "spatial_v9.json"
                if sp.exists():
                    cp = page_dir / "capture.json"
                    out = page_dir / "perception_v13.json"
                    targets.append((sp, cp, out))
    else:
        if not args.client or not args.page:
            print("❌ --client et --page requis (ou --all)", file=sys.stderr)
            sys.exit(1)
        page_dir = base / args.client / args.page
        sp = page_dir / "spatial_v9_clean.json"
        if not sp.exists():
            sp = page_dir / "spatial_v9.json"
        if not sp.exists():
            print(f"❌ pas de spatial_v9 dans {page_dir}", file=sys.stderr)
            sys.exit(1)
        cp = page_dir / "capture.json"
        out = page_dir / "perception_v13.json"
        targets.append((sp, cp, out))

    print(f"→ {len(targets)} page(s) à traiter")
    ok = 0
    for sp, cp, out in targets:
        try:
            res = process_page(sp, cp, out)
            if res.get("status") == "ok":
                ok += 1
        except Exception as e:
            print(f"  ❌ {sp}: {e}")

    print(f"\n✓ {ok}/{len(targets)} pages processées")


if __name__ == "__main__":
    main()
