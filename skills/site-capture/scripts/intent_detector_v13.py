#!/usr/bin/env python3
"""
intent_detector_v13.py — Couche 2 Oracle Perception V13

Détecte l'intention primaire d'un client (funnel_intent) à partir des
perception_v13.json de ses pages.

Sorties :
  - data/captures/{client}/client_intent.json

Taxonomie intent (5 types) :
  - discovery_quiz       : CTA principal mène vers un quiz/diagnostic
                           (japhy, skarlett, edone_paris, andthegreen…)
  - signup_commit        : CTA mène vers un signup SaaS / trial
                           (fygr, matera, weglot, georide, seoni, kaiju…)
  - purchase             : CTA mène direct en achat/panier
                           (voggt, jomarine, captaincause…)
  - contact_lead         : CTA formulaire contact ou demande devis
                           (poppins_mila_learn, massena_formation, ocni_factory…)
  - content_consume      : CTA "lire/voir", contenu gratuit
                           (blog-first, très rare en commerce)

La détection combine 3 signaux :
  1. URL/href path pattern du primary CTA
  2. Texte du primary CTA (regex keyword)
  3. Contexte de la page (présence de pricing, quiz flow, cart…)

L'intent pilote ensuite :
  - Le vocabulaire LLM des recos (Couche 3) :
      quiz → "Diagnostic / Profil / Résultat"
      signup → "Essai / Compte / Onboarding"
      purchase → "Panier / Commande / Livraison"
  - La pondération des critères (ex: quiz_flow activé si quiz)
  - Les benchmarks (ce client vs top quartile de son intent_cluster)

Usage :
    python3 intent_detector_v13.py --client japhy
    python3 intent_detector_v13.py --all
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────
# SIGNATURES D'INTENT (path + label)
# ────────────────────────────────────────────────────────────────

INTENT_SIGNATURES = {
    "discovery_quiz": {
        "href_patterns": [
            r"/quiz\b", r"/diagnostic\b", r"/profile-?builder\b", r"/profil\b",
            r"/configurateur\b", r"/personnaliser\b", r"/test\b",
            r"/onboarding/start\b", r"/get-started\b", r"/discover\b",
            r"/trouver-ma-formule\b", r"/find-?my\b", r"/match\b",
        ],
        "label_patterns": [
            r"\bfaire.le.quiz\b", r"\bfaire.le.test\b", r"\bdiagnostic\b",
            r"\bcr[ée]er.(son|mon|le).menu\b", r"\bcr[ée]er.(son|mon|le).profil\b",
            r"\bconfigurer\b", r"\bpersonnaliser\b", r"\btrouver.ma.formule\b",
            r"\bfind.?my\b", r"\bmatch.?me\b", r"\btake.the.quiz\b",
            r"\bstart.(the.)?quiz\b", r"\b2.?mn\b", r"\b30.?sec",
        ],
        "weight": 1.0,
    },
    "signup_commit": {
        "href_patterns": [
            r"/signup\b", r"/sign-?up\b", r"/register\b", r"/inscription\b",
            r"/trial\b", r"/essai\b", r"/essayer\b", r"/demo\b", r"/try\b", r"/start-?free\b",
            r"/get-?started\b", r"/create-?account\b", r"/creer-?compte\b",
            r"app\..+\.(com|fr|io)/", r"/login\b", r"/connexion\b",
            r"dashboard\.", r"/onboard(ing)?\b",
        ],
        "label_patterns": [
            r"\bessai(.|\W).?gratuit\b", r"\bcommencer.gratuitement\b",
            r"\bs.?inscrire\b", r"\bcr[ée]er.un.compte\b",
            r"\bessayer.(maintenant|gratuit)\b", r"\bessayez.gratuitement\b",
            r"\bstart.(free|for.free)\b", r"\btry.(it.)?free\b", r"\bsign.?up\b",
            r"\bget.started\b", r"\bfree.trial\b", r"\bd[ée]mo\b",
            r"\btester.(14.?jours|pendant)\b",
            r"\bd[ée]couvrir.gratuitement\b", r"\bcommencer\b", r"\bstart.free\b",
            r"\bcontinue\b",  # onboarding flow step
            r"\bcr[ée]er.(ma|mon|une|un).(cagnotte|collecte|campagne|espace|profil)\b",
            r"\blancer.(ma|ta|une|mon).(cagnotte|collecte|campagne)\b",
            r"\bopen.(an.)?account\b",
        ],
        "weight": 1.0,
    },
    "purchase": {
        "href_patterns": [
            r"/cart\b", r"/panier\b", r"/checkout\b", r"/shop\b", r"/store\b",
            r"/boutique\b", r"/products?/", r"/produits?/",
            r"/collections?/", r"/acheter\b", r"/buy\b",
            r"/fidelite\b", r"/recettes?\b", r"/distributeurs?\b",  # m-martin
        ],
        "label_patterns": [
            r"\bajouter.au.panier\b", r"\bcommander\b", r"\bacheter\b",
            r"\bje.commande\b", r"\bvoir.(les.)?produits\b",
            r"\badd.to.cart\b", r"\bbuy.(now|it)\b", r"\bshop.now\b",
            r"\border.now\b",
            r"\bshop\b", r"\bd[ée]couvrir\b", r"\bnos.produits\b",
            r"\bcollections?\b", r"\bparcourir\b",
        ],
        "weight": 1.0,
    },
    "contact_lead": {
        "href_patterns": [
            r"/contact\b", r"/contactez\b", r"/demande-?devis\b",
            r"/devis\b", r"/rdv\b", r"/rendez-?vous\b", r"/booking\b",
            r"/reservation\b", r"calendly\.", r"cal\.com", r"tally\.so",
            r"/conseiller\b", r"/reserver-?une-?demonstration\b",
            r"/reserver\b",
        ],
        "label_patterns": [
            r"\bcontactez.nous\b", r"\bnous.contacter\b",
            r"\bdemander.un.devis\b", r"\bdemande.de.devis\b",
            r"\bprendre.rendez.vous\b", r"\bprendre.rdv\b",
            r"\br[ée]server\b", r"\bbook.a.(call|demo)\b",
            r"\btalk.to.(sales|us)\b",
            r"\bparler.(à|a).un.(conseiller|expert|commercial)\b",
            r"\bdemander.une.d[ée]mo\b", r"\bprendre.contact\b",
            r"\brecevoir.(mon|le|un).rapport\b",
            r"\bcontact.us\b", r"\bget.in.touch\b",
        ],
        "weight": 1.0,
    },
    "content_consume": {
        "href_patterns": [
            r"/blog/?$", r"/articles?/", r"/guide/", r"/resources?/",
            r"/ressources?/",
        ],
        "label_patterns": [
            r"\blire.(l.article|le.guide)\b", r"\bd[ée]couvrir.l.article\b",
            r"\bregarder.(la.vid[ée]o|le.replay)\b",
            r"\bread.(more|the.article)\b", r"\bwatch.(the.)?(video|replay)\b",
        ],
        "weight": 0.7,
    },
}


# Micro-secondary signals (boost d'intent via contexte page)
# v13.1 : HERO n'est PLUS un signal discriminant (présent sur toutes les pages).
# Les boosts doivent refléter des corrélations réelles entre type de business et
# structure des pages découvertes.
CONTEXT_BOOSTS = {
    "discovery_quiz": {
        # Signal fort : la page quiz_vsl a été découverte ET capturée
        "page_has": ["quiz_vsl"],
        "role_has": [],
        "boost": 0.4,
    },
    "signup_commit": {
        # Signal fort : page pricing découverte ET cluster PRICING détecté
        "page_has": ["pricing"],
        "role_has": ["PRICING"],
        "boost": 0.25,
        "require_both": True,  # AND au lieu de OR
    },
    "purchase": {
        # Signal fort : pdp + collection (catalogue e-com)
        "page_has": ["pdp", "collection"],
        "role_has": [],
        "boost": 0.35,
        "require_both": True,
    },
    "contact_lead": {
        # Signal : présence d'une page lp_leadgen
        "page_has": ["lp_leadgen", "contact"],
        "role_has": [],
        "boost": 0.3,
    },
    "content_consume": {
        # Signal : blog est présent MAIS sans pricing ni collection ni pdp
        "page_has": ["blog"],
        "role_has": [],
        "boost": 0.15,  # faible : blog existe dans 90% des business
    },
}


# ────────────────────────────────────────────────────────────────
# CORE DETECTION
# ────────────────────────────────────────────────────────────────

def score_cta_intent(text: str, href: str) -> dict:
    """
    Scoring d'un CTA sur les 5 intents. Retourne {intent: score, ...}.
    """
    text_low = (text or "").lower()
    href_low = (href or "").lower()
    scores = {k: 0.0 for k in INTENT_SIGNATURES}

    for intent, sig in INTENT_SIGNATURES.items():
        matches = []
        for pat in sig["href_patterns"]:
            if re.search(pat, href_low):
                matches.append(("href", pat))
                scores[intent] += 2.0  # href = signal fort
        for pat in sig["label_patterns"]:
            if re.search(pat, text_low):
                matches.append(("label", pat))
                scores[intent] += 1.5  # label = signal moyen-fort

    return scores


def detect_client_intent(client_dir: Path) -> dict:
    """
    Agrège les signaux de toutes les pages perception_v13 d'un client et
    produit un client_intent dict.
    """
    page_files = sorted(client_dir.glob("*/perception_v13.json"))
    if not page_files:
        return {"error": "no perception_v13.json found"}

    pages_data = []
    intent_votes = Counter()
    intent_scores_sum: dict[str, float] = {k: 0.0 for k in INTENT_SIGNATURES}

    # Primary CTA analysis par page (poids dépend du page_type)
    page_type_weight = {
        "home": 2.0,
        "pdp": 1.2,
        "collection": 0.8,
        "pricing": 1.5,
        "lp_leadgen": 1.8,
        "lp_ecom": 1.8,
        "quiz_vsl": 0.3,  # c'est l'intérieur du funnel, pas la source de vérité de l'intent
        "blog": 0.2,
    }

    role_presence = Counter()
    page_types_available = set()

    for pf in page_files:
        try:
            d = json.load(open(pf))
        except Exception:
            continue
        page_type = d.get("meta", {}).get("page_type") or pf.parent.name
        page_types_available.add(page_type)
        weight = page_type_weight.get(page_type, 0.5)

        # Primary CTA
        primary_cta = d.get("primary_cta") or {}
        cta_text = primary_cta.get("text", "")
        cta_href = primary_cta.get("href", "")

        # CTAs fallback : tous les CTAs des clusters HERO/FINAL_CTA si primary manque
        ctas_to_score = []
        if cta_text or cta_href:
            ctas_to_score.append((cta_text, cta_href, 1.0))

        # Secondary : tous les CTAs de clusters HERO + FINAL_CTA (poids réduit)
        for c in d.get("clusters", []):
            if c.get("role") in ("HERO", "FINAL_CTA"):
                for idx in c.get("element_indices", []):
                    if idx >= len(d["elements"]):
                        continue
                    el = d["elements"][idx]
                    if el.get("type") == "cta":
                        t = el.get("text") or ""
                        h = el.get("href") or ""
                        if t and (t, h, 0.4) not in ctas_to_score:
                            ctas_to_score.append((t, h, 0.4))

        # Score all CTAs
        page_scores: dict[str, float] = {k: 0.0 for k in INTENT_SIGNATURES}
        for t, h, w in ctas_to_score:
            cta_scores = score_cta_intent(t, h)
            for intent, s in cta_scores.items():
                # v13.1 : les CTAs pointant vers /article|/blog sur une page
                # pdp/pricing/home sont des liens de "nourriture" (lecture de
                # contenu connexe), pas le signal d'intent primaire.
                # On ignore le content_consume signal pour les pages non-blog.
                if intent == "content_consume" and page_type not in ("blog",):
                    continue
                page_scores[intent] += s * w

        # Role presence
        for c in d.get("clusters", []):
            role_presence[c.get("role", "")] += 1

        # Aggregate
        top_intent_page = None
        if page_scores and max(page_scores.values()) > 0:
            top_intent_page = max(page_scores.items(), key=lambda kv: kv[1])[0]
            intent_votes[top_intent_page] += weight
            for intent, s in page_scores.items():
                intent_scores_sum[intent] += s * weight

        pages_data.append(
            {
                "page_type": page_type,
                "primary_cta_text": cta_text,
                "primary_cta_href": cta_href,
                "page_intent_scores": {k: round(v, 2) for k, v in page_scores.items()},
                "top_intent": top_intent_page,
            }
        )

    # Boost par contexte (présence de page types / roles)
    # v13.1 : support require_both=True (AND au lieu de OR)
    for intent, boost in CONTEXT_BOOSTS.items():
        page_has_list = boost.get("page_has", [])
        role_has_list = boost.get("role_has", [])
        require_both = boost.get("require_both", False)
        if require_both:
            has_page = all(pt in page_types_available for pt in page_has_list) if page_has_list else True
            has_role = all(role_presence.get(r, 0) > 0 for r in role_has_list) if role_has_list else True
            ok = has_page and has_role
        else:
            has_page = any(pt in page_types_available for pt in page_has_list)
            has_role = any(role_presence.get(r, 0) > 0 for r in role_has_list)
            ok = has_page or has_role
        if ok:
            intent_scores_sum[intent] += boost["boost"] * 5

    # Snapshot des scores AVANT fallbacks pour déterminer la qualité du signal
    scores_before_fallback = dict(intent_scores_sum)
    max_cta_signal = max(scores_before_fallback.values())

    # v13.1 — FALLBACK de dernier recours : dériver intent depuis la structure
    # de pages si tous les scores sont ≤ threshold (ex : oma_me avec que des
    # NAV-links comme CTAs, pas de href "/cart").
    # Heuristique "page structure → intent" :
    PAGE_STRUCTURE_FALLBACK = {
        ("collection", "pdp"): ("purchase", 3.0),
        ("quiz_vsl",): ("discovery_quiz", 3.0),
        ("pricing",): ("signup_commit", 2.0),
        ("lp_leadgen", "contact"): ("contact_lead", 2.5),
    }
    if max(intent_scores_sum.values()) < 3.0:
        for pages_needed, (intent_fb, boost_fb) in PAGE_STRUCTURE_FALLBACK.items():
            if all(p in page_types_available for p in pages_needed):
                intent_scores_sum[intent_fb] += boost_fb

    # v13.1 — FALLBACK par ROLE si pas de CTA exploitable et pas de page-type
    # discriminante (ex : nobo, one-pager avec PRICING role sur home mais CTAs vides).
    # Règle : si aucun intent > 2.0 mais la home a PRICING role → signup/purchase léger.
    if max(intent_scores_sum.values()) < 2.0:
        if role_presence.get("PRICING", 0) > 0:
            # PRICING role présent → soit signup (SaaS), soit purchase (e-com).
            # Si collection ou pdp existent → purchase, sinon signup.
            if "collection" in page_types_available or "pdp" in page_types_available:
                intent_scores_sum["purchase"] += 2.5
            else:
                intent_scores_sum["signup_commit"] += 2.5
        elif "home" in page_types_available and role_presence.get("HERO", 0) > 0:
            # Page marketing minimale (just home + HERO) mais sans signal clair.
            # Default "unknown_but_marketing" → on tag "signup_commit" faible
            # comme le moins risqué (majorité des SaaS/services français vont
            # vers un signup/trial). C'est meilleur qu'unknown pour Couche 3.
            intent_scores_sum["signup_commit"] += 1.2

    # Determine primary + secondary intent
    is_multi_intent = False
    intent_source = "none"
    if not any(v > 0 for v in intent_scores_sum.values()):
        primary_intent = "unknown"
        confidence = 0
        secondary_intent = None
    else:
        ranked = sorted(intent_scores_sum.items(), key=lambda kv: -kv[1])
        primary_intent = ranked[0][0]
        top_score = ranked[0][1]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        secondary_intent = ranked[1][0] if len(ranked) > 1 and second_score > 0 else None
        total = sum(v for _, v in ranked) or 1

        # v13.1 — Confidence formula revue :
        #   - Si top_score ≥ 2× second_score ET top_score ≥ 3.0 → signal fort ≥0.7
        #   - Sinon : share * 0.5 + separation * 0.5, bumpé si top_score > 5
        share = top_score / total
        separation = (top_score - second_score) / max(top_score, 1)

        if top_score >= max(2.0 * second_score, 3.0):
            # Signal dominant clair
            confidence = round(min(1.0, 0.6 + separation * 0.4), 3)
        else:
            base = share * 0.5 + separation * 0.5
            # Bump si scores absolus élevés (>5 = signaux multiples convergents)
            if top_score >= 5.0:
                base = min(1.0, base + 0.15)
            elif top_score >= 3.0:
                base = min(1.0, base + 0.10)
            confidence = round(min(1.0, base), 3)

        # Garde-fou 1 : séparation forte
        if confidence < 0.5 and top_score >= 2.0 and separation >= 0.4:
            confidence = 0.5

        # Garde-fou 2 (v13.1.1) : score absolu fort ≥ 4.0, on a au moins UN
        # signal CTA clair même si secondaire proche (ex seoni/sunday : SaaS
        # multi-persona mais intent primaire identifiable).
        # Dans ce cas on expose is_multi_intent=True et on plancher à 0.5.
        if confidence < 0.5 and top_score >= 4.0:
            confidence = 0.5
            is_multi_intent = True

        # Garde-fou 3 : si top+second sont les 2 seuls intents actifs et que
        # leur somme >= 3.0, plancher à 0.5 (signaux convergents sur 2 intents).
        if confidence < 0.5 and second_score > 0 and (top_score + second_score) >= 3.0:
            active_intents = sum(1 for v in intent_scores_sum.values() if v > 0)
            if active_intents <= 2:
                confidence = 0.5
                is_multi_intent = True

        # Cap CRITIQUE : si max CTA signal avant fallback était très faible
        # (<1.0), on ne doit PAS sortir une confidence de 1.0 sur du vide.
        # Le fallback par structure/role peut proposer un intent, mais la
        # confidence doit refléter le manque d'évidence primaire.
        if max_cta_signal < 1.0:
            # Pas de signal CTA exploitable → confidence figée à 0.5 (fallback only)
            # Floor à 0.5 aussi car un intent proposé par fallback structure/role
            # mérite au minimum la confidence minimale de "signal présent mais faible".
            confidence = 0.5
            intent_source = "fallback_only"
        elif max_cta_signal < 2.0:
            # Signal faible (1 pattern match isolé)
            confidence = min(confidence, 0.7)
            intent_source = "weak_cta"
        else:
            intent_source = "cta_signals"

    # Funnel chain (intent_chain awareness → action)
    funnel_chain = build_funnel_chain(primary_intent, page_types_available, role_presence)

    # Vocabulary lexicon (pour piloter Couche 3 LLM)
    vocabulary = build_vocabulary(primary_intent)

    return {
        "version": "v13.1.0-intent",
        "client": client_dir.name,
        "primary_intent": primary_intent,
        "secondary_intent": secondary_intent,
        "is_multi_intent": is_multi_intent,
        "confidence": confidence,
        "intent_source": intent_source,
        "max_cta_signal": round(max_cta_signal, 2),
        "intent_scores": {k: round(v, 2) for k, v in intent_scores_sum.items()},
        "intent_votes": dict(intent_votes),
        "page_types_available": sorted(page_types_available),
        "role_presence": dict(role_presence),
        "funnel_chain": funnel_chain,
        "vocabulary": vocabulary,
        "pages": pages_data,
    }


def build_funnel_chain(primary_intent: str, page_types: set, role_presence: Counter) -> list[dict]:
    """
    Chaîne cognitive typique selon l'intent détecté.
    Chaque étape contient : stage, required_pages, required_roles, status.
    """
    templates = {
        "discovery_quiz": [
            ("awareness", ["home"], ["HERO"]),
            ("engagement", ["home", "quiz_vsl"], ["HERO", "FINAL_CTA"]),
            ("diagnostic", ["quiz_vsl"], []),
            ("personalization", ["pdp"], ["PRICING"]),
            ("commit", ["pricing", "pdp"], ["PRICING", "FINAL_CTA"]),
        ],
        "signup_commit": [
            ("awareness", ["home"], ["HERO"]),
            ("evaluation", ["pricing"], ["PRICING", "SOCIAL_PROOF"]),
            ("trust", ["home"], ["SOCIAL_PROOF", "FAQ"]),
            ("commit", ["pricing", "home"], ["FINAL_CTA"]),
            ("onboarding", [], []),
        ],
        "purchase": [
            ("awareness", ["home"], ["HERO"]),
            ("browse", ["collection"], []),
            ("consideration", ["pdp"], ["PRICING", "SOCIAL_PROOF"]),
            ("add_to_cart", ["pdp"], ["FINAL_CTA"]),
            ("checkout", ["cart", "checkout"], []),
        ],
        "contact_lead": [
            ("awareness", ["home"], ["HERO"]),
            ("trust", ["home", "about"], ["SOCIAL_PROOF"]),
            ("qualification", ["home", "lp_leadgen"], ["FAQ"]),
            ("contact", ["contact", "lp_leadgen"], ["FINAL_CTA"]),
        ],
        "content_consume": [
            ("discovery", ["blog"], []),
            ("engagement", ["blog"], []),
            ("subscribe", ["home"], ["FINAL_CTA"]),
        ],
    }
    steps = templates.get(primary_intent, [])
    out = []
    for stage, req_pages, req_roles in steps:
        has_pages = all(p in page_types for p in req_pages)
        has_roles = all(role_presence.get(r, 0) > 0 for r in req_roles)
        status = "complete" if (has_pages and has_roles) else ("partial" if (has_pages or has_roles) else "missing")
        out.append(
            {
                "stage": stage,
                "required_pages": req_pages,
                "required_roles": req_roles,
                "status": status,
            }
        )
    return out


def build_vocabulary(primary_intent: str) -> dict:
    """
    Lexique autorisé / interdit selon intent. Utilisé par Couche 3 pour forcer
    le LLM à parler le langage du funnel client (ex: "panier" interdit si quiz).
    """
    base = {
        "discovery_quiz": {
            "use_words": ["diagnostic", "profil", "résultat", "recommandation", "profil personnalisé", "sur-mesure"],
            "avoid_words": ["panier", "ajouter au panier", "commander maintenant", "checkout"],
            "cta_tone": "invite à découvrir / créer son profil",
            "proof_priority": ["expert endorsement", "personalization demo", "before/after results"],
        },
        "signup_commit": {
            "use_words": ["essai gratuit", "compte", "trial", "onboarding", "setup", "démo"],
            "avoid_words": ["panier", "livraison", "commander"],
            "cta_tone": "réduction de friction + preuve de valeur rapide",
            "proof_priority": ["logos clients", "ROI metrics", "integrations", "expert reviews"],
        },
        "purchase": {
            "use_words": ["panier", "commande", "livraison", "retour", "paiement sécurisé", "frais de port"],
            "avoid_words": ["diagnostic", "compte", "inscription"],
            "cta_tone": "urgency + social proof + friction checkout minimale",
            "proof_priority": ["avis produit", "photos client", "delivery proof", "return policy"],
        },
        "contact_lead": {
            "use_words": ["devis", "rendez-vous", "audit gratuit", "expert", "interlocuteur"],
            "avoid_words": ["panier", "inscription automatique"],
            "cta_tone": "qualification douce + promesse de retour rapide",
            "proof_priority": ["études de cas", "logos clients B2B", "témoignages directeurs"],
        },
        "content_consume": {
            "use_words": ["lire", "guide", "ressource", "newsletter", "gratuit"],
            "avoid_words": ["acheter", "commander"],
            "cta_tone": "curiosité / valeur immédiate",
            "proof_priority": ["auteurs expertise", "reach/stats audience"],
        },
        "unknown": {
            "use_words": [],
            "avoid_words": [],
            "cta_tone": "neutral",
            "proof_priority": [],
        },
    }
    return base.get(primary_intent, base["unknown"])


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="Client label (ex: japhy)")
    ap.add_argument("--data-dir", default="data/captures", help="Base dir")
    ap.add_argument("--all", action="store_true", help="Tous les clients")
    args = ap.parse_args()

    base = Path(args.data_dir)
    if not base.exists():
        print(f"❌ {base} n'existe pas", file=sys.stderr)
        sys.exit(1)

    targets: list[Path] = []
    if args.all:
        for client_dir in sorted(base.iterdir()):
            if client_dir.is_dir():
                targets.append(client_dir)
    else:
        if not args.client:
            print("❌ --client requis (ou --all)", file=sys.stderr)
            sys.exit(1)
        targets.append(base / args.client)

    for client_dir in targets:
        if not client_dir.exists() or not client_dir.is_dir():
            continue
        result = detect_client_intent(client_dir)
        out_path = client_dir / "client_intent.json"
        with open(out_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        primary = result.get("primary_intent", "?")
        conf = result.get("confidence", 0)
        pages = len(result.get("pages", []))
        print(f"  ✓ {client_dir.name}: intent={primary} (conf={conf}) · {pages} pages")

    print(f"\n✓ {len(targets)} client(s) processés")


if __name__ == "__main__":
    main()
