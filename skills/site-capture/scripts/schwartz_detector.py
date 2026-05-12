#!/usr/bin/env python3
"""
schwartz_detector.py — GrowthCRO V12 S-05 : Schwartz Awareness Scale auto-detection.

Doctrine Mathis 2026-04-13 :
  1. Règle par défaut selon page_type (fallback universel)
  2. Override UTM/referer si dispo (paid → unaware/problem_aware, email → product_aware, etc.)
  3. Override manuel brief audit (clé `schwartz_override` dans run_audit.py)

5 niveaux Schwartz (Eugene M. Schwartz, Breakthrough Advertising 1966) :
  - unaware        : ne connaît ni le problème ni la solution (cold traffic, broad ads)
  - problem_aware  : ressent le problème, cherche comprendre (content marketing, SEO informational)
  - solution_aware : connaît les solutions génériques, compare (retarget, SEO transactional)
  - product_aware  : connaît notre produit, hésite à acheter (PDP, comparison, review)
  - most_aware     : prêt à acheter, juste besoin d'un trigger (pricing, checkout, upsell)

Usage programmatique :
    from schwartz_detector import detect_awareness
    level = detect_awareness(page_type="lp_leadgen", utm_medium="cpc", utm_source="facebook")
    # → "problem_aware"

Usage CLI :
    python schwartz_detector.py <page_type> [--utm-medium X] [--utm-source Y] [--referer Z]
"""
from __future__ import annotations

from typing import Literal

AwarenessLevel = Literal["unaware", "problem_aware", "solution_aware", "product_aware", "most_aware"]


# ─────────────────────────── Règle 1 : page_type → default ───────────────────
# Source : doctrine_integration_matrix.json decisions_mathis_2026-04-13.schwartz_detection
PAGE_TYPE_DEFAULTS: dict[str, AwarenessLevel] = {
    # Homepage / collection = "pont" problem ↔ solution (on prend le plus défensif : problem_aware)
    "home": "problem_aware",
    "collection": "solution_aware",

    # PDP = utilisateur a cliqué sur un produit précis → product_aware
    "pdp": "product_aware",

    # Landing pages paid
    "lp_leadgen": "problem_aware",
    "lp_sales": "solution_aware",  # transitionne vers product_aware au scroll

    # Content marketing = cold/mid-funnel
    "advertorial": "problem_aware",  # part d'un angle éditorial → éducation
    "listicle": "problem_aware",
    "blog": "problem_aware",

    # Funnel late-stage
    "checkout": "most_aware",
    "pricing": "product_aware",      # user en comparaison, pas encore signé
    "thank_you_page": "most_aware",

    # Quiz / VSL / Challenge = éducatif long-form
    "quiz_vsl": "unaware",           # quiz cold = ne sait pas encore
    "quiz": "unaware",
    "vsl": "problem_aware",          # VSL commence douleur puis monte
    "challenge": "problem_aware",

    # Bundle / Squeeze / Webinar
    "bundle_standalone": "product_aware",
    "squeeze": "unaware",            # squeeze = capture email cold
    "webinar": "problem_aware",

    # Comparison = utilisateur compare déjà → product_aware
    "comparison": "product_aware",
}


# ─────────────────────────── Règle 2 : UTM / referer overrides ────────────────
UTM_MEDIUM_MAP: dict[str, AwarenessLevel] = {
    "cpc": "unaware",                # Google Ads broad, Meta Ads cold → cold traffic
    "paid_social": "unaware",
    "paidsocial": "unaware",
    "display": "unaware",
    "retargeting": "solution_aware",  # retarget = a déjà vu le site
    "retarget": "solution_aware",
    "email": "product_aware",        # liste email = connaît la marque
    "newsletter": "product_aware",
    "sms": "most_aware",             # SMS opt-in = forte intent
    "organic": "problem_aware",      # SEO = cherche info
    "referral": "solution_aware",
    "affiliate": "solution_aware",
    "influencer": "problem_aware",
}

UTM_SOURCE_MAP: dict[str, AwarenessLevel] = {
    # Cold platforms
    "facebook": "unaware",
    "instagram": "unaware",
    "tiktok": "unaware",
    "youtube": "unaware",
    # Search = intent élevée mais variable
    "google": "problem_aware",
    "bing": "problem_aware",
    # B2B / professional
    "linkedin": "solution_aware",
    # Warm list
    "klaviyo": "product_aware",
    "mailchimp": "product_aware",
    "brevo": "product_aware",
    "sendinblue": "product_aware",
    "activecampaign": "product_aware",
}

REFERER_HINTS: dict[str, AwarenessLevel] = {
    "ads.google.com": "unaware",
    "facebook.com": "unaware",
    "instagram.com": "unaware",
    "tiktok.com": "unaware",
    "linkedin.com": "solution_aware",
    "twitter.com": "problem_aware",
    "x.com": "problem_aware",
}


# ─────────────────────────── Hiérarchie de confiance ──────────────────────────
# Plus spécifique = plus fort. Order of precedence :
#   1. Manual override (from brief) — trumps everything
#   2. UTM medium + source combination
#   3. UTM medium alone
#   4. UTM source alone
#   5. Referer heuristic
#   6. page_type default
#   7. Fallback : problem_aware (milieu le plus défensif)

def _combine_utm(medium: str | None, source: str | None) -> AwarenessLevel | None:
    """Rules for specific medium+source pairs that override the simple map."""
    m = (medium or "").lower().strip()
    s = (source or "").lower().strip()

    # Paid social + cold platforms = definitely unaware
    if m in {"cpc", "paid_social", "paidsocial"} and s in {"facebook", "instagram", "tiktok", "youtube"}:
        return "unaware"
    # Email + known ESP = product_aware warm list
    if m in {"email", "newsletter"} and s in {"klaviyo", "mailchimp", "brevo", "activecampaign"}:
        return "product_aware"
    # Organic + google = problem_aware (info intent)
    if m == "organic" and s in {"google", "bing"}:
        return "problem_aware"
    return None


def detect_awareness(
    page_type: str | None,
    utm_medium: str | None = None,
    utm_source: str | None = None,
    referer: str | None = None,
    manual_override: str | None = None,
) -> dict:
    """Detect Schwartz Awareness level with provenance & confidence.

    Returns : {
        "level": AwarenessLevel,
        "source": "override" | "utm_combo" | "utm_medium" | "utm_source" | "referer" | "page_type_default" | "fallback",
        "confidence": "high" | "medium" | "low",
        "trace": [str, ...]    # reasoning trail
    }
    """
    trace: list[str] = []

    # 1. Manual override — highest confidence
    if manual_override:
        mo = manual_override.lower().strip().replace("-", "_")
        if mo in {"unaware", "problem_aware", "solution_aware", "product_aware", "most_aware"}:
            return {
                "level": mo,
                "source": "override",
                "confidence": "high",
                "trace": [f"Manual override from brief: {mo}"],
            }
        trace.append(f"Manual override '{manual_override}' invalid — falling back")

    # 2. UTM medium + source combo
    combo = _combine_utm(utm_medium, utm_source)
    if combo:
        trace.append(f"UTM combo medium={utm_medium}+source={utm_source} → {combo}")
        return {
            "level": combo,
            "source": "utm_combo",
            "confidence": "high",
            "trace": trace,
        }

    # 3. UTM medium alone
    if utm_medium:
        m = utm_medium.lower().strip()
        if m in UTM_MEDIUM_MAP:
            lvl = UTM_MEDIUM_MAP[m]
            trace.append(f"UTM medium={m} → {lvl}")
            return {
                "level": lvl,
                "source": "utm_medium",
                "confidence": "medium",
                "trace": trace,
            }

    # 4. UTM source alone
    if utm_source:
        s = utm_source.lower().strip()
        if s in UTM_SOURCE_MAP:
            lvl = UTM_SOURCE_MAP[s]
            trace.append(f"UTM source={s} → {lvl}")
            return {
                "level": lvl,
                "source": "utm_source",
                "confidence": "medium",
                "trace": trace,
            }

    # 5. Referer heuristic
    if referer:
        r = referer.lower()
        for host, lvl in REFERER_HINTS.items():
            if host in r:
                trace.append(f"Referer host matched '{host}' → {lvl}")
                return {
                    "level": lvl,
                    "source": "referer",
                    "confidence": "medium",
                    "trace": trace,
                }

    # 6. page_type default
    if page_type:
        pt = page_type.lower().strip()
        if pt in PAGE_TYPE_DEFAULTS:
            lvl = PAGE_TYPE_DEFAULTS[pt]
            trace.append(f"page_type={pt} → default {lvl}")
            return {
                "level": lvl,
                "source": "page_type_default",
                "confidence": "low",
                "trace": trace,
            }
        trace.append(f"page_type='{pt}' unknown")

    # 7. Fallback
    trace.append("No signal available → fallback problem_aware")
    return {
        "level": "problem_aware",
        "source": "fallback",
        "confidence": "low",
        "trace": trace,
    }


# ─────────────────────────── CLI ────────────────────────────────────────────

def main():
    import argparse
    p = argparse.ArgumentParser(description="Detect Schwartz Awareness level from context signals.")
    p.add_argument("page_type", nargs="?", default=None)
    p.add_argument("--utm-medium", default=None)
    p.add_argument("--utm-source", default=None)
    p.add_argument("--referer", default=None)
    p.add_argument("--override", default=None, help="Manual override (unaware|problem_aware|solution_aware|product_aware|most_aware)")
    p.add_argument("--json", action="store_true", help="Output JSON")
    args = p.parse_args()

    r = detect_awareness(
        page_type=args.page_type,
        utm_medium=args.utm_medium,
        utm_source=args.utm_source,
        referer=args.referer,
        manual_override=args.override,
    )
    if args.json:
        import json
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(f"Level     : {r['level']}")
        print(f"Source    : {r['source']}")
        print(f"Confidence: {r['confidence']}")
        print("Trace     :")
        for t in r["trace"]:
            print(f"  - {t}")


if __name__ == "__main__":
    main()
