#!/usr/bin/env python3
"""
score_psycho.py — Scorer Psycho V3 pour GrowthCRO Playbook.

Usage:
    python score_psycho.py <label> [pageType]
Reads:  data/captures/<label>/<pageType>/capture.json
        data/captures/<label>/<pageType>/page.html (fallback)
Writes: data/captures/<label>/<pageType>/score_psycho.json

Applique les 6 critères du bloc 5 Psycho V3 depuis playbook/bloc_5_psycho_v3.json.
Évalue les leviers psychologiques comportementaux (Cialdini, biais cognitifs) :
  psy_01 : Urgence & Rareté — crédibilité et calibration
  psy_02 : Rareté & Exclusivité — perception de valeur
  psy_03 : Ancrage prix/valeur — framing de la décision
  psy_04 : Aversion à la perte & Risk Reversal
  psy_05 : Autorité & Crédibilité — signaux d'expertise
  psy_06 : Réciprocité & Micro-engagements

Consomme principalement capture.json.psychoSignals (extrait par native_capture.py).
100% textual+heuristic — aucun besoin Apify.

v1.0 — 2026-04-10
"""
import json
import sys
import re
import pathlib
try:
    from spatial_bridge import load_spatial, get_spatial_evidence
    _HAS_SPATIAL = True
except ImportError:
    _HAS_SPATIAL = False
try:
    from perception_bridge import (
        load_perception, has_component, count_component,
        get_verdict, perception_signals,
    )
    _HAS_PERCEPTION = True
except ImportError:
    _HAS_PERCEPTION = False

if len(sys.argv) < 2:
    print("Usage: score_psycho.py <label> [pageType]", file=sys.stderr)
    sys.exit(1)

LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else None

ROOT = pathlib.Path(__file__).resolve().parents[3]

# Support both old (flat) and new (multi-page) storage layouts
if PAGE_TYPE:
    CAP = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "score_psycho.json"
elif (ROOT / "data" / "captures" / LABEL / "home" / "capture.json").exists():
    CAP = ROOT / "data" / "captures" / LABEL / "home" / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / "home" / "score_psycho.json"
    PAGE_TYPE = "home"
else:
    CAP = ROOT / "data" / "captures" / LABEL / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / "score_psycho.json"
    PAGE_TYPE = PAGE_TYPE or "home"

GRID = ROOT / "playbook" / "bloc_5_psycho_v3.json"

if not CAP.exists():
    print(f"ERROR: {CAP} not found", file=sys.stderr)
    sys.exit(1)

cap = json.loads(CAP.read_text())
grid = json.loads(GRID.read_text())

# Load page.html for deeper regex when psychoSignals incomplete
HTML_PATH = CAP.parent / "page.html"
html_raw = HTML_PATH.read_text(errors="ignore") if HTML_PATH.exists() else ""
HTML_L = html_raw.lower() if html_raw else ""  # Full HTML (for tag-level checks like <s>, <del>)

# VISIBLE_TEXT: strip scripts, styles, tags → only user-visible text
# This prevents matching CSS classes, URLs, attributes, JS code
def extract_visible_text(html_str):
    """Extract only visible text from HTML, stripping scripts/styles/tags."""
    if not html_str:
        return ""
    t = re.sub(r"<script[^>]*>.*?</script>", " ", html_str, flags=re.DOTALL | re.I)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.DOTALL | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.DOTALL)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.lower().strip()

BODY_L = extract_visible_text(html_raw)  # Visible text only (for content matching)

meta = cap.get("meta", {})
psycho = cap.get("psychoSignals", {})
hero = cap.get("hero", {})
structure = cap.get("structure", {})
social = cap.get("socialProof", {})
page_specific = cap.get("pageSpecific", {})

# ── FALLBACK : recalculer psychoSignals si absent (vieilles captures Apify) ──
if not psycho and html_raw:
    psycho = {}
    psycho["urgency_words"] = len(re.findall(
        r"\b(urgent|limité|dernière?\s+chance|plus\s+que|expire|se\s+termine|countdown|timer|"
        r"offre\s+flash|derniers?\s+jours?|ne\s+manquez\s+pas|dépêchez|maintenant|today\s+only|"
        r"limited\s+time|hurry|last\s+chance|ends?\s+(?:today|soon|tonight))\b",
        BODY_L))
    psycho["has_countdown"] = bool(re.search(r"countdown|timer|chrono|compte.?à.?rebours", HTML_L))
    psycho["has_deadline"] = bool(re.search(r"jusqu.?au|before|avant\s+le|deadline|date\s+limite", BODY_L))
    psycho["scarcity_words"] = len(re.findall(
        r"\b(stock\s+limité|épuisé|plus\s+que\s+\d|reste\s+\d|exclusive?|rare|edition\s+limitée|"
        r"sold\s+out|out\s+of\s+stock|limited\s+edition|only\s+\d+\s+left|few\s+remaining)\b",
        BODY_L))
    psycho["has_stock_indicator"] = bool(re.search(r"stock|disponib|en\s+stock|rupture|qty|quantity", BODY_L))
    psycho["user_count_mentions"] = len(re.findall(r"\d[\d\s.,]*\+?\s*(?:clients?|users?|utilisateurs?|membres?|inscrits?)", BODY_L))
    psycho["media_mentions"] = len(re.findall(r"vu\s+(?:dans|sur|à)|as\s+seen|featured\s+in|partenaires?\s+média", BODY_L))
    psycho["award_mentions"] = len(re.findall(r"prix|award|récompens|lauréat|winner|élu|best\s+of|top\s+\d", BODY_L))
    psycho["certification_mentions"] = len(re.findall(r"certifi|label|agré|homologu|norme|iso\s*\d|bio|organic|vegan", BODY_L))
    psycho["has_crossed_price"] = bool(re.search(r"<(?:s|del|strike)\b|text-decoration\s*:\s*line-through", HTML_L) or re.search(r"barré|ancien\s+prix", BODY_L))
    psycho["has_discount_badge"] = bool(re.search(r"promo|réduction|remise|-\d+%|save\s+\d|économi|discount", BODY_L))
    psycho["has_free_offer"] = bool(re.search(r"gratuit|offert|cadeau|free\s+(?:trial|shipping)|livraison\s+gratuite|essai\s+gratuit", BODY_L))
    psycho["has_guarantee"] = bool(re.search(r"garantie?|garanti|satisfait|remboursé|money.back|risk.free|sans\s+engagement|sans\s+risque", BODY_L))
    psycho["loss_framing"] = len(re.findall(
        r"\b(ne\s+(?:ratez|manquez|perdez)|risque|danger|erreur|éviter?|sans\s+(?:risque|engagement)|"
        r"don.t\s+miss|avoid|risk|mistake|stop\s+(?:losing|wasting))\b",
        BODY_L))
    psycho["expert_mentions"] = len(re.findall(r"expert|spécialiste|docteur|dr\.?\s|professeur|vétérinaire|nutritionniste|ingénieur|scientifique", BODY_L))
    psycho["has_press_logos"] = bool(re.search(r"press|presse|médias?|as\s+seen|vu\s+dans", BODY_L) or re.search(r"logo.*(?:press|media)", HTML_L))
    print("  [FALLBACK] psychoSignals recalculés depuis page.html")


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
# ── Spatial V9 enrichment ──────────────────────────────────────
_spatial_data = load_spatial(LABEL, PAGE_TYPE) if _HAS_SPATIAL else None
_sp_psy = get_spatial_evidence("psycho", _spatial_data) if _spatial_data else {}
if _sp_psy:
    print(f"  [SPATIAL] Psycho enrichi avec {len(_sp_psy)} clés spatiales")

results = []

def score_entry(cid, label, pts, verdict, evidence, rationale):
    if _sp_psy:
        evidence = {**evidence, **_sp_psy}
    return {
        "id": cid, "label": label, "score": pts, "max": 3,
        "verdict": verdict, "evidence": evidence, "rationale": rationale,
        "applicable": True,
    }

# Page type weighting
def get_weight(criterion_id):
    """Get pageType weight for criterion, default 1.0."""
    weights = grid.get("pageTypeWeights", {}).get(criterion_id, {})
    return weights.get(PAGE_TYPE, 1.0)


# ══════════════════════════════════════════════════════════════
# PSY_01 — Urgence & Rareté — crédibilité et calibration
# ══════════════════════════════════════════════════════════════
urgency_words = psycho.get("urgency_words", 0)
has_countdown = psycho.get("has_countdown", False)
has_deadline = psycho.get("has_deadline", False)
scarcity_words = psycho.get("scarcity_words", 0)
has_stock = psycho.get("has_stock_indicator", False)

urgency_signals = urgency_words + (2 if has_countdown else 0) + (1 if has_deadline else 0)
scarcity_signals = scarcity_words + (1 if has_stock else 0)
total_urgency_scarcity = urgency_signals + scarcity_signals

# Fake detection heuristics
# Countdown without real deadline = suspect
fake_indicators = 0
fake_notes = []
if has_countdown and not has_deadline:
    fake_indicators += 1
    fake_notes.append("countdown_sans_deadline")
# Over-solicitation: too many urgency words = aggressive
if urgency_words >= 5:
    fake_indicators += 1
    fake_notes.append(f"urgency_over_solicitation({urgency_words})")
# Scarcity words but no real stock mechanism
if scarcity_words >= 3 and not has_stock:
    fake_indicators += 1
    fake_notes.append(f"scarcity_sans_stock_indicator({scarcity_words})")

# Killer check: fake urgency detected
killer_psy01 = fake_indicators >= 2

if killer_psy01:
    pts, verdict = 0, "critical"
    rationale = f"Urgence potentiellement fake: {', '.join(fake_notes)}. KILLER déclenché."
elif total_urgency_scarcity >= 2 and fake_indicators == 0:
    pts, verdict = 3, "top"
    rationale = f"Urgence/rareté crédible: urgency={urgency_signals}, scarcity={scarcity_signals}, deadline={has_deadline}, zéro indicateur fake."
elif total_urgency_scarcity >= 1:
    pts, verdict = 1.5, "ok"
    rationale = f"Urgence/rareté présente mais limitée ou légèrement suspecte: urgency={urgency_signals}, scarcity={scarcity_signals}."
else:
    # Absence = OK (opportunité manquée, pas un défaut)
    pts, verdict = 1.5, "ok"
    rationale = "Pas d'urgence/rareté détectée. Opportunité manquée mais pas un défaut."

results.append(score_entry("psy_01", "Urgence & Rareté — crédibilité", pts, verdict,
    {"urgency_words": urgency_words, "has_countdown": has_countdown, "has_deadline": has_deadline,
     "scarcity_words": scarcity_words, "has_stock": has_stock,
     "fake_indicators": fake_notes, "killerTriggered": killer_psy01}, rationale))


# ══════════════════════════════════════════════════════════════
# PSY_02 — Rareté & Exclusivité — perception de valeur
# ══════════════════════════════════════════════════════════════
levers_02 = 0
lever_notes_02 = []

# (a) Rareté produit
if scarcity_words >= 1 or has_stock:
    levers_02 += 1
    lever_notes_02.append("rarete_produit")

# (b) Exclusivité d'accès — detect membership, waitlist, invitation
exclu_patterns = re.findall(
    r"\b(réservé\s+aux|exclusi\w+|early\s+access|liste\s+d.attente|waitlist|sur\s+invitation|"
    r"accès\s+(?:vip|premium|prioritaire)|beta\s+(?:privée?|fermée?)|nombre\s+limité\s+de\s+places)\b",
    BODY_L)
if exclu_patterns:
    levers_02 += 1
    lever_notes_02.append(f"exclusivite({len(exclu_patterns)})")

# (c) Personnalisation / sur-mesure / quiz / configurateur
perso_patterns = re.findall(
    r"(sur.mesure|personnal|custom|configurateur|quiz|votre\s+(?:formule|profil|recette|plan)|"
    r"adapté\s+à\s+(?:vous|ton|votre|toi)|unique|spécifique\s+à)",
    BODY_L)
if perso_patterns:
    levers_02 += 1
    lever_notes_02.append(f"personnalisation({len(perso_patterns)})")

# (d) Ancrage comparatif implicite (vs alternative)
compare_patterns = re.findall(
    r"(contrairement|vs\s|versus|par\s+rapport|comparé|à\s+la\s+différence|plutôt\s+que|"
    r"whereas|unlike|instead\s+of|compared\s+to)",
    BODY_L)
if compare_patterns:
    levers_02 += 1
    lever_notes_02.append(f"ancrage_comparatif({len(compare_patterns)})")

if levers_02 >= 2:
    pts, verdict = 3, "top"
    rationale = f"{levers_02} leviers de valeur perçue actifs: {', '.join(lever_notes_02)}."
elif levers_02 == 1:
    pts, verdict = 1.5, "ok"
    rationale = f"1 seul levier de valeur perçue: {', '.join(lever_notes_02)}."
else:
    pts, verdict = 0, "critical"
    rationale = "Zéro levier de valeur perçue (ni rareté, ni exclusivité, ni personnalisation, ni comparaison)."

results.append(score_entry("psy_02", "Rareté & Exclusivité — valeur perçue", pts, verdict,
    {"levers_count": levers_02, "levers_detail": lever_notes_02,
     "scarcity_words": scarcity_words, "has_stock": has_stock,
     "exclusivity_matches": len(exclu_patterns) if exclu_patterns else 0,
     "personalization_matches": len(perso_patterns) if perso_patterns else 0}, rationale))


# ══════════════════════════════════════════════════════════════
# PSY_03 — Ancrage prix/valeur — framing de la décision
# ══════════════════════════════════════════════════════════════
anchoring_levers = 0
anchor_notes = []

has_crossed = psycho.get("has_crossed_price", False)
has_discount = psycho.get("has_discount_badge", False)
has_free = psycho.get("has_free_offer", False)
has_guarantee = psycho.get("has_guarantee", False)
loss_framing = psycho.get("loss_framing", 0)

# (a) Prix barré / ancien prix
if has_crossed:
    anchoring_levers += 1
    anchor_notes.append("prix_barre")

# (b) Badge promo / réduction
if has_discount:
    anchoring_levers += 1
    anchor_notes.append("badge_promo")

# (c) Comparaison coût quotidien (X€/jour, X€/mois)
daily_cost = re.findall(r"\d+[.,]?\d*\s*€?\s*/\s*(?:jour|day|mois|month|semaine|week)", BODY_L)
if daily_cost:
    anchoring_levers += 1
    anchor_notes.append(f"cout_quotidien({len(daily_cost)})")

# (d) Coût de l'inaction (loss framing)
if loss_framing >= 1:
    anchoring_levers += 1
    anchor_notes.append(f"loss_framing({loss_framing})")

# (e) Garantie / risk reversal (as anchoring of zero risk)
if has_guarantee:
    anchoring_levers += 1
    anchor_notes.append("garantie")

# (f) Free offer / essai gratuit
if has_free:
    anchoring_levers += 1
    anchor_notes.append("offre_gratuite")

# (g) Pricing tiers (detect multiple price points)
pricing_amounts = re.findall(r"\d+[.,]?\d*\s*€", BODY_L)
if len(pricing_amounts) >= 3:
    anchoring_levers += 1
    anchor_notes.append(f"multi_prix({len(pricing_amounts)})")

if anchoring_levers >= 2:
    pts, verdict = 3, "top"
    rationale = f"{anchoring_levers} techniques d'ancrage actives: {', '.join(anchor_notes)}."
elif anchoring_levers == 1:
    pts, verdict = 1.5, "ok"
    rationale = f"1 seule technique d'ancrage: {', '.join(anchor_notes)}."
else:
    pts, verdict = 0, "critical"
    rationale = "Zéro ancrage prix/valeur. Le prix est affiché sans contexte ni comparaison."

results.append(score_entry("psy_03", "Ancrage prix/valeur — framing", pts, verdict,
    {"anchoring_levers": anchoring_levers, "detail": anchor_notes,
     "has_crossed_price": has_crossed, "has_discount": has_discount,
     "has_free": has_free, "has_guarantee": has_guarantee,
     "loss_framing": loss_framing}, rationale))


# ══════════════════════════════════════════════════════════════
# PSY_04 — Aversion à la perte & Risk Reversal
# ══════════════════════════════════════════════════════════════
risk_levers = 0
risk_notes = []

# (a) Garantie explicite
if has_guarantee:
    risk_levers += 1
    risk_notes.append("garantie")

# (b) Loss framing in copy
if loss_framing >= 1:
    risk_levers += 1
    risk_notes.append(f"loss_framing({loss_framing})")

# (c) Free trial / sans CB / sans engagement
free_trial_patterns = re.findall(
    r"\b(essai\s+gratuit|offre\s+d.essai|free\s+trial|sans\s+(?:cb|carte|engagement|frais)|try\s+free|"
    r"no\s+(?:credit\s+card|commitment)|période\s+d.essai|faites?\s+tester|offre\s+découverte)\b",
    BODY_L)
if free_trial_patterns:
    risk_levers += 1
    risk_notes.append(f"essai_gratuit({len(free_trial_patterns)})")

# (d) Return/exchange policy
return_patterns = re.findall(
    r"(retour\s+gratuit|échange|remboursement|retour\s+facile|free\s+return|"
    r"money.back|satisfait\s+ou\s+remboursé|30\s+jours?|return\s+policy)",
    BODY_L)
if return_patterns:
    risk_levers += 1
    risk_notes.append(f"retour_echange({len(return_patterns)})")

# (e) Micro-reassurance near CTA (security badges, padlock, SSL)
reassurance = cap.get("hero", {}).get("microReassurance", [])
if isinstance(reassurance, list) and reassurance:
    risk_levers += 1
    risk_notes.append(f"micro_reassurance_hero({len(reassurance)})")
# Also check in HTML for security mentions
security_patterns = re.findall(
    r"(paiement\s+sécurisé|cadenas|données\s+protégées|secure\s+payment|"
    r"256.bit|chiffré|encrypted|confidentiel|rgpd|gdpr|paiement\s+100)",
    BODY_L)
if security_patterns:
    risk_levers += 1
    risk_notes.append(f"securite({len(security_patterns)})")

if risk_levers >= 2:
    pts, verdict = 3, "top"
    rationale = f"{risk_levers} leviers de risk reversal: {', '.join(risk_notes)}."
elif risk_levers == 1:
    pts, verdict = 1.5, "ok"
    rationale = f"1 seul levier de risk reversal: {', '.join(risk_notes)}."
else:
    pts, verdict = 0, "critical"
    rationale = "Zéro risk reversal. Le visiteur supporte 100% du risque perçu."

results.append(score_entry("psy_04", "Aversion perte & Risk Reversal", pts, verdict,
    {"risk_levers": risk_levers, "detail": risk_notes,
     "has_guarantee": has_guarantee, "loss_framing": loss_framing,
     "free_trial_matches": len(free_trial_patterns) if free_trial_patterns else 0,
     "return_matches": len(return_patterns) if return_patterns else 0,
     "security_matches": len(security_patterns) if security_patterns else 0}, rationale))


# ══════════════════════════════════════════════════════════════
# PSY_05 — Autorité & Crédibilité — signaux d'expertise
# ══════════════════════════════════════════════════════════════
auth_signals = 0
auth_notes = []

expert = psycho.get("expert_mentions", 0)
certifications = psycho.get("certification_mentions", 0)
media = psycho.get("media_mentions", 0)
awards = psycho.get("award_mentions", 0)
press_logos = psycho.get("has_press_logos", False)
user_counts = psycho.get("user_count_mentions", 0)

# (a) Expert mentions
if expert >= 1:
    auth_signals += 1
    auth_notes.append(f"experts({expert})")

# (b) Certifications/labels
if certifications >= 1:
    auth_signals += 1
    auth_notes.append(f"certifications({certifications})")

# (c) Media/press mentions
if media >= 1 or press_logos:
    auth_signals += 1
    auth_notes.append(f"media({media},logos={press_logos})")

# (d) Awards
if awards >= 1:
    auth_signals += 1
    auth_notes.append(f"awards({awards})")

# (e) User count / experience chiffrée
if user_counts >= 1:
    auth_signals += 1
    auth_notes.append(f"user_counts({user_counts})")

# (f) Experience years or number of clients/projects
exp_patterns = re.findall(
    r"(\d+\s*(?:ans?|years?)\s*(?:d.expérience|of\s+experience|d.expertise)|\d+\+?\s*(?:projets?|projects?|clients?|audits?))",
    BODY_L)
if exp_patterns:
    auth_signals += 1
    auth_notes.append(f"experience({len(exp_patterns)})")

# (g) Made in France / local manufacturing
local_patterns = re.findall(r"(fabriqué\s+en|made\s+in|produit\s+en|assemblé\s+en|conçu\s+en)", BODY_L)
if local_patterns:
    auth_signals += 1
    auth_notes.append(f"fabrication_locale({len(local_patterns)})")

# Killer check: zero authority on primary/mandatory page
killer_psy05 = (auth_signals == 0 and PAGE_TYPE in ("home", "pdp", "lp_sales", "lp_leadgen", "lp_saas", "pricing"))

if auth_signals >= 3:
    pts, verdict = 3, "top"
    rationale = f"{auth_signals} signaux d'autorité différents: {', '.join(auth_notes)}."
elif auth_signals >= 1:
    pts, verdict = 1.5, "ok"
    rationale = f"{auth_signals} signal(s) d'autorité (< 3): {', '.join(auth_notes)}."
else:
    pts, verdict = 0, "critical"
    rationale = "Zéro signal d'autorité détecté."
    if killer_psy05:
        rationale += " KILLER psy_05 déclenché (page primary/mandatory)."

results.append(score_entry("psy_05", "Autorité & Crédibilité", pts, verdict,
    {"auth_signals": auth_signals, "detail": auth_notes,
     "expert_mentions": expert, "certifications": certifications,
     "media_mentions": media, "awards": awards, "press_logos": press_logos,
     "user_counts": user_counts, "killerTriggered": killer_psy05}, rationale))


# ══════════════════════════════════════════════════════════════
# PSY_06 — Réciprocité & Micro-engagements
# ══════════════════════════════════════════════════════════════
recip_levers = 0
recip_notes = []

# (a) Free value before ask
if has_free:
    recip_levers += 1
    recip_notes.append("offre_gratuite")

# Lead magnet detection
lead_magnet = re.findall(
    r"\b(télécharge[rz]|guide\s+gratuit|ebook|e-book|checklist|calculateur|calculatrice|"
    r"audit\s+gratuit|livre\s+blanc|white\s*paper|webinaire?\s+gratuit|mini.cours|"
    r"free\s+(?:guide|ebook|tool|audit)|ressource\s+gratuite)\b",
    BODY_L)
if lead_magnet:
    recip_levers += 1
    recip_notes.append(f"lead_magnet({len(lead_magnet)})")

# (b) Multi-step engagement (quiz, configurateur, steps)
quiz_config = re.findall(
    r"\b(quiz|questionnaire|configurateur|étape\s+\d|step\s+\d|profil.builder|"
    r"diagnostic\s+gratuit|bilan\s+gratuit|faites?\s+le\s+test|évaluation\s+gratuite|"
    r"assessment|découvr\w+\s+votre\s+profil|cré\w+\s+(?:le\s+)?profil|votre\s+profil\s+(?:en|sur))\b",
    BODY_L)
if quiz_config:
    recip_levers += 1
    recip_notes.append(f"quiz_configurateur({len(quiz_config)})")

# (c) Progressive disclosure (chunked forms, multi-step forms)
forms = structure.get("forms", [])
if isinstance(forms, list):
    for f in forms:
        fields = f.get("fields", [])
        n_fields = fields if isinstance(fields, int) else len(fields)
        # Multi-step indicator: presence of step/étape in form context
        if n_fields >= 2:
            recip_levers += 1
            recip_notes.append(f"formulaire({n_fields}_champs)")
            break

# (d) Free trial / freemium
freemium = re.findall(
    r"(freemium|plan\s+gratuit|free\s+plan|version\s+gratuite|free\s+tier|"
    r"démarrer\s+gratuitement|start\s+free|gratuit\s+à\s+vie|free\s+forever)",
    BODY_L)
if freemium:
    recip_levers += 1
    recip_notes.append(f"freemium({len(freemium)})")

# (e) Demo / sample
demo = re.findall(
    r"(démo|demo|échantillon|sample|essayer|try\s+it|tester\s+gratuitement|"
    r"voir\s+en\s+action|see\s+it\s+in\s+action|playground)",
    BODY_L)
if demo:
    recip_levers += 1
    recip_notes.append(f"demo_sample({len(demo)})")

if recip_levers >= 2:
    pts, verdict = 3, "top"
    rationale = f"{recip_levers} leviers de réciprocité/engagement: {', '.join(recip_notes)}."
elif recip_levers == 1:
    pts, verdict = 1.5, "ok"
    rationale = f"1 seul levier de réciprocité: {', '.join(recip_notes)}."
else:
    pts, verdict = 0, "critical"
    rationale = "Zéro réciprocité / micro-engagement. La page demande l'action sans rien donner."

results.append(score_entry("psy_06", "Réciprocité & Micro-engagements", pts, verdict,
    {"recip_levers": recip_levers, "detail": recip_notes,
     "has_free": has_free, "lead_magnets": len(lead_magnet) if lead_magnet else 0,
     "quiz_config": len(quiz_config) if quiz_config else 0,
     "forms_count": len(forms) if isinstance(forms, list) else 0}, rationale))


# ══════════════════════════════════════════════════════════════
# TOTAUX + KILLERS
# ══════════════════════════════════════════════════════════════
raw_total = sum(r["score"] for r in results)
active_max = len(results) * 3  # 6 × 3 = 18

# Apply killers
killer_triggered = False
killer_note = None
final_total = raw_total

if killer_psy01:
    killer_triggered = True
    cap_value = 6
    final_total = min(final_total, cap_value)
    killer_note = f"KILLER psy_01_fake_urgency: cap {cap_value}/{active_max} (raw={raw_total})"

if killer_psy05:
    killer_triggered = True
    cap_value = 10
    if killer_note:
        # Both killers: take the stricter one
        final_total = min(final_total, cap_value)
        killer_note += f" + KILLER psy_05_zero_authority: cap {cap_value}/{active_max}"
    else:
        final_total = min(final_total, cap_value)
        killer_note = f"KILLER psy_05_zero_authority: cap {cap_value}/{active_max} (raw={raw_total})"

# Score normalisé /100
score_100 = round((final_total / active_max) * 100, 1) if active_max > 0 else 0

# ─── Perception Layer 2 : evidence + hints Psycho ───
_perception_block = {"available": False}
if _HAS_PERCEPTION:
    _p = load_perception(LABEL, PAGE_TYPE, ROOT)
    _sig = perception_signals(_p)
    _perception_block = {"available": _sig.get("pc_available", False), "signals": _sig}
    if _sig.get("pc_available"):
        for r in results:
            # psy_05 (autorité/crédibilité) : presence logos + testimonials
            if r["id"] == "psy_05":
                r.setdefault("perception_has_social_proof", _sig.get("pc_has_social_proof", False))
            # psy_07 (friction cognitive) : trop de blocs = overload
            if r["id"] == "psy_07":
                r.setdefault("perception_num_components", _sig.get("pc_num_components", 0))

output = {
    "label": LABEL,
    "pageType": PAGE_TYPE,
    "url": meta.get("url"),
    "pillar": "psycho",
    "max": active_max,
    "maxFull": 18,
    "rawTotal": raw_total,
    "finalTotal": final_total,
    "score100": score_100,
    "killerTriggered": killer_triggered,
    "killerNote": killer_note,
    "activeCriteria": len(results),
    "skippedCriteria": [],
    "criteria": results,
    "gridVersion": grid.get("version"),
    "capturedAt": meta.get("capturedAt"),
    "_perception": _perception_block,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))

# ─────────────────────────────────────────────────────────────
# Console summary
# ─────────────────────────────────────────────────────────────
print(f"\n━━━ Psycho V3 Scoring — {LABEL} [{PAGE_TYPE}] ━━━")
print(f"URL: {meta.get('url')}")
print(f"{'Critère':<12} {'Score':>8}  Verdict")
print("─" * 60)
for r in results:
    print(f"{r['id']:<12} {r['score']:>3}/{r['max']}   {r['verdict']:<9}  {r['label'][:40]}")
    print(f"             → {r['rationale'][:90]}")
print("─" * 60)
print(f"{'TOTAL':<12} {final_total:>3}/{active_max}   ({score_100}/100)  (raw={raw_total}{', KILLER' if killer_triggered else ''})")
if killer_note:
    print(f"  {killer_note}")
print(f"\nOutput: {OUT}")
