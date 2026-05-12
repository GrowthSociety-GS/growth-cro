#!/usr/bin/env python3
"""
golden_differential.py — P11.2 Golden Differential Engine (online helper)

Lit data/golden/percentiles_v1.json (produit par golden_percentiles.py) et
compare les métriques d'un client vs les percentiles du segment golden
(pageType × business_type).

Produit des directives chiffrées injectables dans le prompt reco :
  - "Ton H1 fait 18 mots, p50 golden = 8. Coupe ~55% pour atteindre le p50."
  - "Ton CTA principal est passif (verb_rank=-1), p50 golden = +1 action.
     Reformule avec un verbe d'engagement."

Usage depuis reco_enricher_v13.py :
    from golden_differential import compute_differential_block
    block = compute_differential_block(capture, spatial, page_type, business_type)
    # → string Markdown à injecter dans user_prompt, ou "" si pas de données.
"""
from __future__ import annotations

import json
import pathlib

# Import local metrics extractor (évite duplication)
try:
    from golden_percentiles import page_metrics, segment_key
except ImportError:
    # Fallback pour import depuis scripts parent : sys.path
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from golden_percentiles import page_metrics, segment_key  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_PERCENTILES = ROOT / "data" / "golden" / "percentiles_v1.json"


# ────────────────────────────────────────────────────────────────
# LOAD / CACHE
# ────────────────────────────────────────────────────────────────

_cache: dict | None = None


def load_percentiles(path: pathlib.Path | None = None) -> dict:
    global _cache
    if _cache is not None and path is None:
        return _cache
    p = path or DEFAULT_PERCENTILES
    if not p.exists():
        return {"segments": {}, "n_pages": 0}
    try:
        data = json.load(open(p))
    except Exception:
        return {"segments": {}, "n_pages": 0}
    if path is None:
        _cache = data
    return data


def reset_cache() -> None:
    """Pour tests / refresh après rerun de golden_percentiles.py."""
    global _cache
    _cache = None


# ────────────────────────────────────────────────────────────────
# DIRECTIVE GENERATION PER METRIC
# ────────────────────────────────────────────────────────────────

# Seuils : quand la métrique client dépasse ou est sous ces quantiles, on émet une directive.
# Format : (client < p25 = trop faible) / (client > p75 = trop haut) → directive correctrice.
METRIC_DIRECTIVES = {
    "hero_h1_word_count": {
        "dir": "bidirectional",
        "low": "H1 à {client} mots, p25 golden = {p25}. Golden avg {p50} mots — enrichis pour clarifier la promesse.",
        "high": "H1 à {client} mots, p50 golden = {p50} (p75 = {p75}). Coupe d'environ {cut_pct}% pour atteindre le median golden.",
    },
    "hero_subtitle_word_count": {
        "dir": "high",
        "high": "Sous-titre à {client} mots, p50 golden = {p50}. Trop verbeux : vise {p50} mots max.",
    },
    "hero_copy_chars": {
        "dir": "high",
        "high": "Copy hero total = {client} chars, p50 golden = {p50}. Réduis d'environ {cut_pct}% pour atteindre la densité cible.",
    },
    "cta_count_in_fold": {
        "dir": "high",
        "high": "{client} CTAs ATF, p50 golden = {p50}. Trop de choix dilue la conversion — vise 1-{p50_int} CTA principal.",
    },
    "cta_primary_verb_rank": {
        "dir": "low",
        "low": "CTA primaire passif ou browsing (rank={client}), p50 golden = {p50} (action verb). Reformule avec un verbe d'engagement.",
    },
    "social_proof_signals": {
        "dir": "low",
        "low": "{client} signaux de preuve sociale, p50 golden = {p50}. Ajoute des widgets / chiffres / testimonials.",
    },
    "h1_count": {
        "dir": "high",
        "high": "{client} H1 sur la page (anti-pattern SEO), p50 golden = 1. Réduis à 1 H1 unique.",
    },
    "hero_image_area_px": {
        "dir": "low",
        "low": "Visuel hero {client}px², p50 golden = {p50}px². Visuel sous-dimensionné — agrandis pour dominance fold.",
    },
}


def _cut_pct(client_v: float, target_v: float) -> int:
    """Retourne le pourcentage de coupe pour passer de client_v à target_v (vers le bas)."""
    if client_v <= 0 or target_v <= 0 or client_v <= target_v:
        return 0
    return max(0, min(90, round((1 - target_v / client_v) * 100)))


# ────────────────────────────────────────────────────────────────
# P11.16 (V19) — Doctrine-first arbitrage : la doctrine prime sur le golden
# ────────────────────────────────────────────────────────────────
# Si un golden "fautif" suggère d'aller dans une direction que la doctrine
# CRO Growth Society sanctionne, on IGNORE la directive golden sur ce point.
# Exemple : Golden avec urgency artificielle + pas de risk reversal.
# Notre règle R5_MANIPULATION_FLAG dit "pénalité". Donc on ne doit pas
# recommander de copier cette urgency.
#
# Format : {metric_name: {floor_min, ceiling_max, veto_if_true, doctrine_note}}
DOCTRINE_FLOORS_CEILINGS = {
    "hero_h1_word_count": {
        "floor_min": 4,   # hero_01 doctrine : < 4 mots = trop court pour porter les 3 signals target/benefit/diff
        "ceiling_max": 14,  # > 14 mots = trop long quelle que soit la référence golden
        "doctrine_note": "hero_01 exige 3 signals (target + benefit + diff). Ne jamais descendre sous 4 mots.",
    },
    "hero_subtitle_word_count": {
        "ceiling_max": 30,  # hero_02 : max 30 mots, peu importe le golden
        "doctrine_note": "hero_02 : subtitle > 30 mots = dilution. Jamais pousser au-delà même si golden le fait.",
    },
    "cta_count_in_fold": {
        "floor_min": 1,  # Toujours au moins 1 CTA, même si golden en a 0 (ce qui serait absurde)
        "ceiling_max": 4,  # hero_06 : focus = 1 CTA primaire. Pousser au-delà de 4 = chaos.
        "doctrine_note": "hero_06 focus : 1 CTA primaire + max 3 secondaires. Jamais plus.",
    },
    "cta_primary_verb_rank": {
        "floor_min": 0,  # 0 = browsing (Découvrir/Voir) accepté mais -1 (passif) veto
        "doctrine_note": "hero_03 : CTA avec verbe d'action ou de projection. Jamais passif (rank=-1).",
    },
    "social_proof_signals": {
        "floor_min": 1,  # per_04 REQUIRED en ecommerce PDP/checkout (applicability_matrix)
        "doctrine_note": "per_04 REQUIRED sur ecommerce PDP. Jamais 0 sur ces pages.",
    },
    "h1_count": {
        "ceiling_max": 1,  # SEO hard rule : 1 seul H1 par page
        "doctrine_note": "tech SEO : 1 seul H1. Jamais plus même si golden en a 2+.",
    },
}

# Métriques pour lesquelles la doctrine VETO systématiquement certaines directives golden,
# même si le delta mathématique existe. Ex: manipulation flag.
DOCTRINE_VETO_RULES = [
    {
        "name": "urgency_without_risk_reversal",
        "applies_to_metric": None,  # méta-règle pas attachée à une métrique unique
        "note": "R5_MANIPULATION_FLAG : si urgence golden est forte ET risk reversal absent, ne pas inciter à copier.",
    },
]


def _apply_doctrine_arbitrage(metric: str, directive: str, client_v: float, target_v: float) -> tuple[str, str | None]:
    """Filtre la directive golden à travers les floors/ceilings doctrinaux.

    Retourne (directive_finale, doctrine_note | None). Si la directive viole un
    floor/ceiling, on la clampe et on append une doctrine_note.
    """
    rule = DOCTRINE_FLOORS_CEILINGS.get(metric)
    if not rule:
        return directive, None

    floor = rule.get("floor_min")
    ceiling = rule.get("ceiling_max")
    note = rule.get("doctrine_note")

    # Clamp la cible (target_v) aux bornes doctrinales
    if floor is not None and target_v < floor:
        # Le golden veut descendre sous le floor → clamp au floor
        adjusted_dir = f"{directive}\n⚠️ DOCTRINE OVERRIDE : target clampé à {floor} ({note})"
        return adjusted_dir, note
    if ceiling is not None and target_v > ceiling:
        adjusted_dir = f"{directive}\n⚠️ DOCTRINE OVERRIDE : target clampé à {ceiling} ({note})"
        return adjusted_dir, note
    # Directive passe la doctrine telle quelle
    return directive, None


def _generate_directive(metric: str, client_v: float, pcts: dict) -> str | None:
    """Retourne une string directive, ou None si pas de déviation significative."""
    cfg = METRIC_DIRECTIVES.get(metric)
    if not cfg:
        return None
    p25 = pcts.get("p25")
    p50 = pcts.get("p50")
    p75 = pcts.get("p75")
    if p50 is None:
        return None

    direction = cfg["dir"]
    # "high" = client trop au-dessus du golden
    # "low" = client trop en-dessous
    if direction in ("high", "bidirectional") and p75 is not None and client_v > p75 and "high" in cfg:
        tpl = cfg["high"]
        return tpl.format(
            client=round(client_v, 2),
            p25=p25,
            p50=p50,
            p75=p75,
            p50_int=int(p50) if p50 else 1,
            cut_pct=_cut_pct(client_v, p50),
        )
    if direction in ("low", "bidirectional") and p25 is not None and client_v < p25 and "low" in cfg:
        tpl = cfg["low"]
        return tpl.format(
            client=round(client_v, 2),
            p25=p25,
            p50=p50,
            p75=p75,
            p50_int=int(p50) if p50 else 1,
            cut_pct=0,
        )
    return None


# ────────────────────────────────────────────────────────────────
# MAIN API
# ────────────────────────────────────────────────────────────────

def compute_differentials(
    capture: dict,
    spatial: dict | None,
    page_type: str,
    business_type: str,
) -> list[dict]:
    """Retourne la liste des directives chiffrées pour ce client.

    Chaque directive = {metric, client_value, p50_golden, directive_text, severity}.
    """
    pctls = load_percentiles()
    segments = pctls.get("segments") or {}
    if not segments:
        return []

    # Segment match : pageType × businessType, fallback pageType only
    client_metrics = page_metrics(capture, spatial)
    seg_key = segment_key(page_type, business_type)

    seg_data = segments.get(seg_key)
    fallback_note = ""
    if not seg_data:
        # Fallback : agréger tous les segments avec le même pageType
        all_metrics: dict[str, list[float]] = {}
        n_pages = 0
        for k, v in segments.items():
            if k.startswith(f"{page_type}__"):
                n_pages += v.get("n_pages", 0)
                for mname, mpcts in (v.get("metrics") or {}).items():
                    # Approx : on reprend les p50 existants comme samples
                    all_metrics.setdefault(mname, [])
                    for _, pv in mpcts.items():
                        if pv is not None:
                            all_metrics[mname].append(pv)
        if not all_metrics:
            return []
        # Estime p50 approximatif par mean des p50 agrégés
        seg_data = {
            "n_pages": n_pages,
            "metrics": {
                k: {
                    "p25": min(v) if v else None,
                    "p50": sum(v) / len(v) if v else None,
                    "p75": max(v) if v else None,
                    "p90": max(v) if v else None,
                }
                for k, v in all_metrics.items()
            },
        }
        fallback_note = f" (fallback : pageType-only, {n_pages} golden pages)"

    directives = []
    for metric, pcts in (seg_data.get("metrics") or {}).items():
        client_v = client_metrics.get(metric)
        if client_v is None:
            continue
        text = _generate_directive(metric, client_v, pcts)
        if text:
            # P11.16 — arbitrage doctrine-first avant d'émettre la directive
            p50 = pcts.get("p50") or 0
            final_text, doctrine_note = _apply_doctrine_arbitrage(metric, text, client_v, p50)
            directives.append({
                "metric": metric,
                "client_value": round(client_v, 2),
                "p25": pcts.get("p25"),
                "p50": pcts.get("p50"),
                "p75": pcts.get("p75"),
                "directive": final_text + fallback_note,
                "doctrine_override": doctrine_note,  # None si directive golden respectée telle quelle
            })
    return directives


def compute_differential_block(
    capture: dict,
    spatial: dict | None,
    page_type: str,
    business_type: str,
    limit: int = 5,
) -> str:
    """Retourne un bloc Markdown à injecter dans le prompt reco, ou "" si rien.

    Limit = nombre max de directives affichées (triées par priorité implicite).
    """
    directives = compute_differentials(capture, spatial, page_type, business_type)
    if not directives:
        return ""
    lines = [
        "## DIFFÉRENTIEL GOLDEN (directives chiffrées vs best-in-class)",
        "> Ces chiffres viennent de la comparaison de ce client contre les percentiles golden "
        f"du segment ({page_type} × {business_type}).",
        "> Si une directive est présente, elle est PLUS SPÉCIFIQUE que le golden benchmark textuel.",
        "> Ta reco DOIT adresser en priorité ces écarts chiffrés.",
        "",
    ]
    for d in directives[:limit]:
        lines.append(f"- **{d['metric']}** : {d['directive']}")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────
# CLI (smoke test)
# ────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--page", required=True)
    ap.add_argument("--page-type", default=None, help="Override page_type (else derived from dir)")
    ap.add_argument("--business-type", default=None, help="Override business_type (else 'unknown')")
    args = ap.parse_args()

    cap_path = ROOT / "data" / "captures" / args.client / args.page / "capture.json"
    spa_path = ROOT / "data" / "captures" / args.client / args.page / "spatial_v9.json"
    if not cap_path.exists():
        print(f"❌ {cap_path} introuvable")
        return
    capture = json.load(open(cap_path))
    spatial = json.load(open(spa_path)) if spa_path.exists() else None

    pt = args.page_type or args.page
    bt = args.business_type or "unknown"

    # Lookup business type from clients_database if not provided
    if not args.business_type:
        db_path = ROOT / "data" / "clients_database.json"
        if db_path.exists():
            try:
                db = json.load(open(db_path))
                clients = db.get("clients") or db
                if isinstance(clients, dict):
                    c = clients.get(args.client) or {}
                else:
                    c = next((x for x in clients if x.get("label") == args.client), {}) or {}
                bt = (c.get("identity") or {}).get("businessType") or c.get("business_type") or "unknown"
            except Exception:
                pass

    print(f"→ {args.client}/{args.page} [pt={pt}, bt={bt}]")
    directives = compute_differentials(capture, spatial, pt, bt)
    if not directives:
        print("  (aucune directive — soit conforme aux golden, soit pas de percentiles)")
        return
    for d in directives:
        print(f"  • {d['metric']} client={d['client_value']} p50_golden={d['p50']}")
        print(f"    → {d['directive']}")


if __name__ == "__main__":
    main()
