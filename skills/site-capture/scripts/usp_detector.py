#!/usr/bin/env python3
"""V21.F.2 — USP detector

Scanne perception_v13.json + vision_{desktop,mobile}.json + client_intent.json
pour détecter les éléments distinctifs (USP) qui doivent être PRÉSERVÉS par
les recos LLM. Output: usp_signals.json par page.

Patterns détectés (cf playbook/usp_preservation.json):
  - specific_duration_promise (en X min/jours/heures)
  - named_target_audience (pour chien, pour développeurs, ...)
  - quantified_outcome_claim (X% de Y, +N clients, ...)
  - proprietary_method_or_term (catégorie créée)
  - distinctive_cta_verb (CTA non-générique)
  - vertical_terminology (jargon insider du business_category)
  - founder_voice (lettre fondateur, photo, signature)

Usage:
  python3 usp_detector.py --client japhy --page home
  python3 usp_detector.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "captures"

# ────────────────────────────────────────────────────────────────────────
# DICTIONNAIRES de référence
# ────────────────────────────────────────────────────────────────────────

GENERIC_CTAS = {
    "acheter", "buy", "buy now", "shop now",
    "découvrir", "decouvrir", "discover",
    "en savoir plus", "learn more", "more",
    "voir", "see", "view",
    "suivant", "next",
    "cliquer", "cliquer ici", "click", "click here",
    "go", "ok", "submit",
    "envoyer", "send",
    "réserver", "reserver", "book",
    "commencer", "start", "get started",
    "inscription", "sign up", "signup",
    "connexion", "login", "log in",
    "contact", "contactez-nous", "contact us",
    "essai gratuit", "free trial", "try free",
    "demander une démo", "demo", "book a demo",
    "télécharger", "telecharger", "download",
}

GENERIC_AUDIENCE_WORDS = {"client", "clients", "user", "users", "everyone", "tous", "tout le monde"}

# Verticals → mots de jargon insider (signal d'expertise)
VERTICAL_JARGON = {
    "saas_b2b": {"api", "sdk", "webhooks", "integration", "uptime", "sso", "rbac", "audit log", "saml"},
    "saas_b2c": {"sync", "offline", "real-time", "collaboration"},
    "ecommerce": {"panier", "checkout", "livraison", "retour", "garantie"},
    "dtc_subscription": {"abonnement", "récurrent", "résiliation", "menu", "ration", "cure"},
    "fintech": {"iban", "swift", "kyc", "aml", "sepa", "wire", "compliance"},
    "edu": {"cohorte", "cohort", "module", "certificat", "diplôme", "accreditation"},
    "luxe": {"héritage", "savoir-faire", "atelier", "édition limitée", "numéroté"},
    "health": {"clinique", "validé", "essai clinique", "agréé", "homologué"},
    "lead_gen": {"diagnostic", "audit", "simulation", "estimation", "devis"},
}

FOUNDER_PATTERNS = re.compile(
    r"\b(ceo|founder|fondateur|fondatrice|co-?fondateur|co-?fondatrice|président|présidente|directeur|directrice général)\s+[A-Z][a-zà-ÿ]+",
    re.IGNORECASE,
)

DURATION_PATTERN = re.compile(
    r"\b(en|in)\s+(\d+(?:\.,\d+)?)\s*(min|minutes?|sec|secondes?|h|heures?|hr|jour|jours?|day|days?|semaines?|weeks?|mois|months?)\b",
    re.IGNORECASE,
)

QUANTIFIED_PATTERN = re.compile(
    r"(\d{1,3}(?:[ ,]\d{3})*(?:[\.,]\d+)?)\s*(%|x|×|fois|€|\$|£|pts|points|clients?|users?|utilisateurs?|avis|reviews?|chiens?|chats?|pays|countries|téléchargements?|downloads?)\b",
    re.IGNORECASE,
)

NAMED_AUDIENCE_PATTERN = re.compile(
    r"\b(pour|for|built for|designed for|spécialement pour|conçu pour|destiné aux?)\s+(les?|the|votre|vos|son|sa|ses)?\s*([a-zà-ÿ]+(?:\s+[a-zà-ÿ]+){0,3})",
    re.IGNORECASE,
)

PROPRIETARY_METHOD_PATTERN = re.compile(
    r"\b(notre|our|le|la)\s+(\w+)\s+(unique|propriétaire|proprietary|exclusif|exclusive|breveté|patented|signature)",
    re.IGNORECASE,
)


# ────────────────────────────────────────────────────────────────────────
# DETECTORS
# ────────────────────────────────────────────────────────────────────────

def _strip_text(t: str | None) -> str:
    if not t:
        return ""
    return re.sub(r"\s+", " ", t).strip()


def detect_duration_promise(text: str) -> dict | None:
    m = DURATION_PATTERN.search(text)
    if not m:
        return None
    return {
        "match": m.group(0),
        "duration_value": m.group(2),
        "duration_unit": m.group(3),
        "score": 0.85,
    }


def detect_quantified_outcome(text: str) -> dict | None:
    m = QUANTIFIED_PATTERN.search(text)
    if not m:
        return None
    return {
        "match": m.group(0),
        "quantity": m.group(1),
        "unit": m.group(2),
        "score": 0.8,
    }


def detect_named_audience(text: str) -> dict | None:
    m = NAMED_AUDIENCE_PATTERN.search(text)
    if not m:
        return None
    audience = (m.group(3) or "").strip().lower()
    if not audience or audience in GENERIC_AUDIENCE_WORDS:
        return None
    return {
        "match": m.group(0),
        "audience_term": audience,
        "score": 0.75 if len(audience.split()) <= 2 else 0.7,
    }


def detect_proprietary_method(text: str) -> dict | None:
    m = PROPRIETARY_METHOD_PATTERN.search(text)
    if not m:
        return None
    return {
        "match": m.group(0),
        "method_term": m.group(2),
        "modifier": m.group(3),
        "score": 0.9,
    }


def detect_distinctive_cta(cta_text: str) -> dict | None:
    if not cta_text:
        return None
    norm = cta_text.lower().strip().rstrip("!.→›>")
    if norm in GENERIC_CTAS:
        return None
    # Distinctive CTA: not in generic list, has more than 1 verb-like word OR has specificity
    if len(norm.split()) >= 2:
        # Check if it has any distinctive non-generic word
        words = set(norm.split())
        generic_words = {"le", "la", "les", "the", "a", "an", "un", "une", "de", "du", "des", "for", "pour", "et", "and"}
        meaningful = words - generic_words
        if not (meaningful & {w.lower() for cta in GENERIC_CTAS for w in cta.split()}):
            return {
                "match": cta_text,
                "score": 0.7,
                "reason": "distinctive_cta_not_in_generic_dict",
            }
    return None


def detect_vertical_jargon(text: str, business_category: str | None) -> list[dict]:
    if not text or not business_category:
        return []
    jargon_set = VERTICAL_JARGON.get(business_category, set())
    text_lower = text.lower()
    found = []
    for term in jargon_set:
        if term in text_lower:
            found.append({
                "match": term,
                "category": business_category,
                "score": 0.65,
            })
    return found


def detect_founder_voice(text: str) -> dict | None:
    m = FOUNDER_PATTERNS.search(text)
    if not m:
        return None
    return {
        "match": m.group(0),
        "score": 0.7,
    }


# ────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ────────────────────────────────────────────────────────────────────────

def extract_vocab_canonical(hero: dict) -> dict:
    """Extrait le vocabulaire canonique (verbe action + objet) du CTA primaire / H1."""
    cta_raw = hero.get("primary_cta")
    if isinstance(cta_raw, list) and cta_raw:
        cta_raw = cta_raw[0]
    cta_text = _strip_text(cta_raw.get("text") if isinstance(cta_raw, dict) else None)
    h1_raw = hero.get("h1")
    h1_text = _strip_text(h1_raw.get("text") if isinstance(h1_raw, dict) else None)

    # Verb extraction depuis CTA (1er mot infinitif)
    verb = None
    obj = None
    if cta_text:
        words = cta_text.split()
        if words:
            verb_candidate = words[0].lower().rstrip(",.")
            # Vérifier que c'est un verbe d'action (heuristique: termine par -er, -ir, -re en français OU est commun en anglais)
            if re.match(r".+(er|ir|re|ez|ons|e)$", verb_candidate) or verb_candidate in {"get", "start", "create", "build", "join", "try", "shop", "buy"}:
                verb = verb_candidate
                obj = " ".join(words[1:]) if len(words) > 1 else None

    # Detecter promesse temporelle
    duration = None
    sub_raw = hero.get("subtitle")
    sub_text = _strip_text(sub_raw.get("text") if isinstance(sub_raw, dict) else None)
    full_hero_text = " ".join(filter(None, [h1_text, sub_text, cta_text]))
    dp = detect_duration_promise(full_hero_text)
    if dp:
        duration = dp["match"]

    # Audience
    audience = None
    a = detect_named_audience(h1_text + " " + (sub_text or ""))
    if a:
        audience = a["audience_term"]

    return {
        "action_verb": verb,
        "action_object": obj,
        "duration_promise": duration,
        "audience": audience,
        "cta_canonical": cta_text or None,
        "h1_canonical": h1_text or None,
    }


def detect_usp_signals(client: str, page: str, page_dir: Path, business_category: str | None = None) -> dict:
    """Detect all USP signals on a given page."""
    # Load Vision (priority over perception for hero ground truth)
    vision_desktop_path = page_dir / "vision_desktop.json"
    vision_mobile_path = page_dir / "vision_mobile.json"
    perception_path = page_dir / "perception_v13.json"

    vision_desktop = json.load(open(vision_desktop_path)) if vision_desktop_path.exists() else {}
    vision_mobile = json.load(open(vision_mobile_path)) if vision_mobile_path.exists() else {}
    perception = json.load(open(perception_path)) if perception_path.exists() else {}

    raw_d_hero = vision_desktop.get("hero") or {}
    raw_m_hero = vision_mobile.get("hero") or {}
    desktop_hero = raw_d_hero if isinstance(raw_d_hero, dict) else {}
    mobile_hero = raw_m_hero if isinstance(raw_m_hero, dict) else {}

    # Aggregate texts to scan
    sources = []

    def _add(loc: str, text: str | None):
        if text:
            sources.append({"location": loc, "text": _strip_text(text)})

    # Desktop hero
    _add("hero.h1", (desktop_hero.get("h1") or {}).get("text") if isinstance(desktop_hero.get("h1"), dict) else None)
    _add("hero.subtitle", (desktop_hero.get("subtitle") or {}).get("text") if isinstance(desktop_hero.get("subtitle"), dict) else None)
    primary_cta_raw = desktop_hero.get("primary_cta")
    if isinstance(primary_cta_raw, list) and primary_cta_raw:
        primary_cta_raw = primary_cta_raw[0]
    if isinstance(primary_cta_raw, dict):
        _add("hero.cta_primary", primary_cta_raw.get("text"))
    sp = desktop_hero.get("social_proof_in_fold") or {}
    if isinstance(sp, dict) and sp.get("snippet"):
        _add("hero.social_proof", sp.get("snippet"))

    # Below fold sections (headlines)
    for s in (vision_desktop.get("below_fold_sections") or [])[:6]:
        if isinstance(s, dict) and s.get("headline"):
            _add(f"below_fold.{s.get('type', 'section')}", s["headline"])

    # Utility banner
    ub = vision_desktop.get("utility_banner") or {}
    if isinstance(ub, dict) and ub.get("text"):
        _add("utility_banner", ub["text"])

    # Detect signals
    signals = []
    for src in sources:
        text = src["text"]
        loc = src["location"]

        # Duration
        dp = detect_duration_promise(text)
        if dp:
            signals.append({
                "type": "specific_duration_promise",
                "text_canonical": text,
                "match": dp["match"],
                "score": dp["score"],
                "location": loc,
                "amplify_strategy": "Garder la promesse temporelle + ajouter une preuve sociale chiffrée",
            })

        # Quantified outcome
        qo = detect_quantified_outcome(text)
        if qo:
            signals.append({
                "type": "quantified_outcome_claim",
                "text_canonical": text,
                "match": qo["match"],
                "score": qo["score"],
                "location": loc,
                "amplify_strategy": "Garder le chiffre + ajouter source/date/méthodologie",
            })

        # Named audience (only on H1/subtitle, not CTA)
        if loc.startswith("hero.h1") or loc.startswith("hero.subtitle") or loc.startswith("below_fold"):
            na = detect_named_audience(text)
            if na:
                signals.append({
                    "type": "named_target_audience",
                    "text_canonical": text,
                    "match": na["match"],
                    "audience_term": na["audience_term"],
                    "score": na["score"],
                    "location": loc,
                    "amplify_strategy": "Garder l'audience nommée + ajouter un proof point spécifique",
                })

        # Proprietary method
        pm = detect_proprietary_method(text)
        if pm:
            signals.append({
                "type": "method_or_process_proprietary",
                "text_canonical": text,
                "match": pm["match"],
                "score": pm["score"],
                "location": loc,
                "amplify_strategy": "Renforcer la méthode + ajouter étape ou détail concret",
            })

        # Founder voice
        fv = detect_founder_voice(text)
        if fv:
            signals.append({
                "type": "named_founder_voice",
                "text_canonical": text,
                "match": fv["match"],
                "score": fv["score"],
                "location": loc,
                "amplify_strategy": "Garder voix fondateur + ajouter contexte personnel/mission",
            })

        # Vertical jargon
        if business_category:
            vj_list = detect_vertical_jargon(text, business_category)
            for vj in vj_list:
                signals.append({
                    "type": "vertical_specific_terminology",
                    "text_canonical": text,
                    "match": vj["match"],
                    "category": vj["category"],
                    "score": vj["score"],
                    "location": loc,
                    "amplify_strategy": "Garder le jargon (signal expertise) + ajouter mini-définition",
                })

    # Distinctive CTA (only one — the primary CTA)
    cta_raw = desktop_hero.get("primary_cta")
    if isinstance(cta_raw, list) and cta_raw:
        cta_raw = cta_raw[0]
    cta_text = cta_raw.get("text") if isinstance(cta_raw, dict) else None
    if cta_text:
        dc = detect_distinctive_cta(cta_text)
        if dc:
            # Skip if cta already covered by another signal type
            covered = any(s.get("location") == "hero.cta_primary" for s in signals)
            if not covered:
                signals.append({
                    "type": "distinctive_cta_verb",
                    "text_canonical": _strip_text(cta_text),
                    "match": dc["match"],
                    "score": dc["score"],
                    "location": "hero.cta_primary",
                    "amplify_strategy": "Garder texte CTA distinctif + ajouter preuve/spécificité sous-CTA",
                })

    # Vocab canonical (always extracted)
    vocab_canonical = extract_vocab_canonical(desktop_hero)

    # Sort signals by score desc
    signals.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Determine highest score (drives preservation directive)
    max_score = max((s.get("score", 0) for s in signals), default=0.0)
    if max_score >= 0.85:
        directive = "PRESERVE STRICTLY — only add proof/specificity, never modify text"
    elif max_score >= 0.65:
        directive = "PRESERVE WITH POLISH — minor wording tweaks OK if they ENHANCE specificity"
    elif max_score >= 0.40:
        directive = "OPTIMIZE — keep core idea, may rewrite if score < 60% on linked criterion"
    else:
        directive = "FREE TO REWRITE — text is generic, not USP"

    return {
        "version": "V21.F.2",
        "client": client,
        "page": page,
        "business_category": business_category,
        "n_signals": len(signals),
        "max_score": max_score,
        "preservation_directive": directive,
        "vocab_canonical": vocab_canonical,
        "usp_signals": signals,
    }


def process_page(client: str, page: str, data_dir: Path = DATA_DIR, force: bool = False) -> Path | None:
    page_dir = data_dir / client / page
    if not page_dir.exists():
        return None

    out_path = page_dir / "usp_signals.json"
    if out_path.exists() and not force:
        return out_path

    # Load business_category from intent
    intent_path = data_dir / client / "client_intent.json"
    business_category = None
    if intent_path.exists():
        try:
            intent = json.load(open(intent_path))
            business_category = intent.get("category") or intent.get("business_category")
        except Exception:
            pass

    # Fallback: try client_meta or capture
    if not business_category:
        capture_path = page_dir / "capture.json"
        if capture_path.exists():
            try:
                cap = json.load(open(capture_path))
                business_category = cap.get("businessCategory")
            except Exception:
                pass

    result = detect_usp_signals(client, page, page_dir, business_category)

    with open(out_path, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return out_path


def process_all(data_dir: Path = DATA_DIR, force: bool = False) -> list[tuple[str, str]]:
    processed = []
    for client_dir in sorted(data_dir.iterdir()):
        if not client_dir.is_dir():
            continue
        client = client_dir.name
        if client.startswith("_") or client.startswith("."):
            continue
        for page_dir in sorted(client_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            page = page_dir.name
            if page.startswith("_") or page.startswith("."):
                continue
            # Need at least vision_desktop OR perception
            if not (page_dir / "vision_desktop.json").exists() and not (page_dir / "perception_v13.json").exists():
                continue
            try:
                out = process_page(client, page, data_dir, force=force)
                if out:
                    processed.append((client, page))
            except Exception as e:
                print(f"  ⚠️  {client}/{page}: {e}", file=sys.stderr)
    return processed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", help="Slug client (e.g. japhy)")
    parser.add_argument("--page", help="Page name (e.g. home)")
    parser.add_argument("--all", action="store_true", help="Process all clients/pages")
    parser.add_argument("--force", action="store_true", help="Re-run even if usp_signals.json exists")
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    if args.all:
        results = process_all(data_dir, force=args.force)
        print(f"✓ {len(results)} pages processed")
        # Quick stats
        n_with_usp = 0
        for c, p in results:
            sig_path = data_dir / c / p / "usp_signals.json"
            if sig_path.exists():
                d = json.load(open(sig_path))
                if d.get("n_signals", 0) > 0:
                    n_with_usp += 1
        print(f"   {n_with_usp} pages avec ≥1 USP signal détecté ({100*n_with_usp/max(len(results),1):.1f}%)")
        return

    if not args.client or not args.page:
        parser.error("Either --all OR (--client + --page)")

    out = process_page(args.client, args.page, data_dir, force=args.force)
    if out:
        d = json.load(open(out))
        print(f"✓ {out}")
        print(f"  n_signals = {d['n_signals']}, max_score = {d['max_score']}")
        print(f"  directive: {d['preservation_directive']}")
        for s in d["usp_signals"][:5]:
            print(f"  - [{s['type']}] {s['location']} score={s['score']} match={s.get('match', '')[:80]!r}")
    else:
        print(f"✗ {args.client}/{args.page} introuvable")
        sys.exit(1)


if __name__ == "__main__":
    main()
