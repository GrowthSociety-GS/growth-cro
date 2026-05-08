#!/usr/bin/env python3
"""
score_persuasion.py — Scorer Bloc 2 Persuasion V3 pour GrowthCRO Playbook.

Usage:
    python score_persuasion.py <label> [pageType]
Reads:  data/captures/<label>/capture.json + page.html
Writes: data/captures/<label>/score_persuasion.json

Applique les 8 critères per_01→per_08 de playbook/bloc_2_persuasion_v3.json
en lisant capture.json (structured) + page.html (regex fallback).

Cohérent avec le baseline manuel data/bloc_2_baseline_japhy_v3.json (15.5/24).
"""
import json, sys, re, pathlib
from datetime import datetime, timezone
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
    print("Usage: score_persuasion.py <label> [pageType]", file=sys.stderr); sys.exit(1)
LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else "home"

ROOT = pathlib.Path(__file__).resolve().parents[3]
# Support both old (flat) and new (multi-page) storage layouts
if (ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json").exists():
    CAP = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json"
    HTML = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "page.html"
    OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "score_persuasion.json"
else:
    CAP = ROOT / "data" / "captures" / LABEL / "capture.json"
    HTML = ROOT / "data" / "captures" / LABEL / "page.html"
    OUT = ROOT / "data" / "captures" / LABEL / "score_persuasion.json"
GRID = ROOT / "playbook" / "bloc_2_persuasion_v3.json"

if not CAP.exists():
    print(f"capture.json missing: {CAP}", file=sys.stderr); sys.exit(2)

# ─── Filtrage par pageType ───────────────────────────────────
# Chaque critère déclare pour quels pageTypes il est applicable.
CRITERIA_PAGE_TYPES = {
    "per_01": "*",                                                    # Bénéfices > features — universel
    "per_02": ["home", "lp_sales", "pdp", "quiz_vsl", "blog"],       # Storytelling
    "per_03": "*",                                                    # Objections levées — universel
    "per_04": "*",                                                    # Preuves concrètes — universel
    "per_05": "*",                                                    # Témoignages — universel
    "per_06": ["pdp", "pricing", "lp_sales", "lp_leadgen", "home"],  # FAQ ciblée
    "per_07": "*",                                                    # Ton cohérent — universel
    "per_08": "*",                                                    # Jargon creux — universel
}

def is_criterion_applicable(criterion_id: str, page_type: str) -> bool:
    pt = CRITERIA_PAGE_TYPES.get(criterion_id, "*")
    if pt == "*":
        return True
    return page_type in pt

cap = json.loads(CAP.read_text())
grid = json.loads(GRID.read_text())
html_raw = HTML.read_text(errors="ignore") if HTML.exists() else ""

# ── Normalize body text from html ──────────────────────────────
_body = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
_body = re.sub(r"<style[^>]*>.*?</style>", " ", _body, flags=re.DOTALL | re.I)
_body = re.sub(r"<[^>]+>", " ", _body)
BODY = re.sub(r"\s+", " ", _body)
BODY_L = BODY.lower()

hero = cap.get("hero", {}) or {}
social = cap.get("socialProof", {}) or {}
structure = cap.get("structure", {}) or {}
meta = cap.get("meta", {}) or {}
tech = cap.get("technical", {}) or {}

headings = structure.get("headings", []) or []
testimonials = social.get("testimonials", []) or []
trust_widgets = social.get("trustWidgets", []) or []


def _scored_at() -> str:
    return meta.get("capturedAt") or cap.get("capturedAt") or datetime.now(timezone.utc).isoformat()

# ── FALLBACK H1/headings depuis page.html si capture.json vide ──
if html_raw and not (hero.get("h1") or "").strip():
    _fb = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
    _fb = re.sub(r"<style[^>]*>.*?</style>", " ", _fb, flags=re.DOTALL | re.I)
    h1m = re.findall(r'<h1\b[^>]*>(.*?)</h1>', _fb, re.DOTALL | re.I)
    if h1m:
        h1t = re.sub(r'<[^>]+>', '', h1m[0]).strip()
        if h1t:
            hero["h1"] = h1t
            hero["h1Count"] = len(h1m)
            print(f"  [FALLBACK] H1 récupéré depuis page.html: '{h1t[:60]}'")

if html_raw and not headings:
    _fb = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
    _fb = re.sub(r"<style[^>]*>.*?</style>", " ", _fb, flags=re.DOTALL | re.I)
    html_h = re.findall(r'<(h[1-4])\b[^>]*>(.*?)</\1>', _fb, re.DOTALL | re.I)
    if html_h:
        headings = []
        for idx, (tag, text) in enumerate(html_h):
            clean = re.sub(r'<[^>]+>', '', text).strip()
            if clean:
                headings.append({"level": int(tag[1]), "text": clean, "order": idx + 1})
        if headings:
            print(f"  [FALLBACK] {len(headings)} headings trouvés dans page.html")

# ── Spatial V9 enrichment ──────────────────────────────────────
_spatial_data = load_spatial(LABEL, PAGE_TYPE) if _HAS_SPATIAL else None
_sp_pers = get_spatial_evidence("persuasion", _spatial_data) if _spatial_data else {}
if _sp_pers:
    print(f"  [SPATIAL] Persuasion enrichi avec {len(_sp_pers)} clés spatiales")

results = []

def entry(cid, label, pts, verdict, evidence, rationale):
    if _sp_pers:
        evidence = {**evidence, **_sp_pers}
    return {"id": cid, "label": label, "score": pts, "max": 3,
            "verdict": verdict, "evidence": evidence, "rationale": rationale}

# ══════════════════════════════════════════════════════════════
# per_01 — Bénéfices > features
# ══════════════════════════════════════════════════════════════
# Heuristique : on cherche dans les H2/H3 et hero subtitle les motifs
#   FEATURE  = unités mesurées, specs, "sans X", "contient X", "composé de"
#   OUTCOME  = verbes de bénéfice pour l'utilisateur ("gagnez", "digère mieux",
#              "économisez", "évitez", "retrouvez", "transformez", "change la vie")
FEATURE_PAT = re.compile(
    r"\b(contient|compos[ée]|sans\s+\w+|\d+\s*(mg|g|kg|ml|cl|l|%|cm|mm)\b|ingr[ée]dients?|"
    r"fabriqu[ée]|origine|compatibilit[ée]|formule|fibre|prot[ée]ines?|vitamin)",
    re.I,
)
OUTCOME_PAT = re.compile(
    r"\b(gagn(?:e|ez)|[ée]conomis|[ée]vit|r[ée]duir|am[ée]lior|transform|retrouv|"
    r"ne\s+plus|sans\s+stress|sans\s+effort|digest|dormez|dormir\s+mieux|"
    r"change\s+la\s+vie|plus\s+(jamais|besoin)|en\s+\d+\s*(jours|semaines|minutes))",
    re.I,
)
# Cherche dans les 20 premiers headings + hero subtitle + h1
corpus_01 = " ".join([hero.get("h1", "") or "", hero.get("subtitle", "") or ""] +
                     [h.get("text", "") for h in headings[:30]])
feat_hits = len(FEATURE_PAT.findall(corpus_01))
out_hits = len(OUTCOME_PAT.findall(corpus_01))
# Body wide outcome ratio comme backup
body_out = len(OUTCOME_PAT.findall(BODY[:20000]))
body_feat = len(FEATURE_PAT.findall(BODY[:20000]))

if feat_hits + out_hits == 0:
    # Pas assez de signal dans headings, on regarde le body
    ratio = body_out / max(body_feat + body_out, 1)
else:
    ratio = out_hits / max(feat_hits + out_hits, 1)

total_outcomes_all = out_hits + body_out
total_features_all = feat_hits + body_feat
if out_hits >= 3 and ratio >= 0.55:
    pts = 3; v = "top"
elif out_hits >= 1 or ratio >= 0.30 or total_outcomes_all >= 3:
    pts = 2; v = "ok"
elif total_outcomes_all >= 1:
    pts = 1; v = "weak"
else:
    # Killer seulement si on a VRAIMENT 0 outcome sur tout le corpus ET ≥5 features
    # (pages 100% features, pas juste heading pauvres en verbes)
    if total_features_all >= 5:
        pts = 0; v = "critical"  # killer trigger
    else:
        pts = 1; v = "weak"  # page vide/atypique, pas killer

results.append(entry(
    "per_01", "Bénéfices > features", pts, v,
    {"outcome_hits_headings": out_hits, "feature_hits_headings": feat_hits,
     "body_outcome": body_out, "body_feature": body_feat, "outcome_ratio": round(ratio, 2)},
    f"Outcome hits dans H1/subtitle/headings={out_hits} vs features={feat_hits}. "
    f"Ratio outcome/(outcome+feature)={ratio:.2f}. Top>=0.55+out>=3, OK>=0.30, critical<0.30."
))

# ══════════════════════════════════════════════════════════════
# per_02 — Storytelling / angle narratif
# ══════════════════════════════════════════════════════════════
story_patterns = {
    "notre_histoire": r"notre\s+histoire",
    "fonde_en": r"fond[ée]s?\s+en\s+\d{4}",
    "pourquoi_nous": r"pourquoi\s+(nous|japhy|" + re.escape(LABEL) + r")",
    "il_etait_une_fois": r"il\s+[ée]tait\s+une\s+fois",
    "notre_mission": r"notre\s+mission",
    "nous_sommes_nes": r"(nous\s+sommes\s+n[ée]s?|est\s+n[ée]e?\s+(de|d['’])\s+)",
    "tout_a_commence": r"tout\s+a\s+commenc[ée]",
    "frustrated_founder": r"(frustr[ée]|en\s+a(?:i|vait)\s+marre|lass[ée])",
    "cofounder_story": r"cofondat(?:rice|eur)|fondat(?:rice|eur)",
}
story_hits = {k: len(re.findall(p, BODY_L)) for k, p in story_patterns.items()}
story_total = sum(1 for v in story_hits.values() if v > 0)
# Vrai arc narratif : au moins 3 signaux différents, incluant pourquoi/mission OU déclencheur
has_trigger = story_hits["frustrated_founder"] + story_hits["nous_sommes_nes"] + story_hits["tout_a_commence"] > 0
has_mission = story_hits["notre_mission"] + story_hits["pourquoi_nous"] > 0
has_origin = story_hits["notre_histoire"] + story_hits["fonde_en"] + story_hits["cofounder_story"] > 0

if story_total >= 3 and has_trigger and (has_mission or has_origin):
    pts = 3; v = "top"
elif story_total >= 1:
    pts = 1; v = "weak"
else:
    pts = 0; v = "critical"
# Override : si has_origin + has_mission + 2 signaux → OK 2
if story_total >= 2 and has_origin and has_mission and not has_trigger:
    pts = 2; v = "ok"

results.append(entry(
    "per_02", "Storytelling fondateur", pts, v,
    {"signals": {k: v for k, v in story_hits.items() if v > 0}, "total_distinct": story_total,
     "has_trigger": has_trigger, "has_mission": has_mission, "has_origin": has_origin},
    "Top: ≥3 signaux distincts + déclencheur + (mission OR origine). "
    "OK: origine + mission sans déclencheur. Weak: ≥1 signal isolé. Critical: 0."
))

# ══════════════════════════════════════════════════════════════
# per_03 — Objections principales levées (FAQ + comparaison + garantie)
# ══════════════════════════════════════════════════════════════
# On détecte la présence d'une FAQ (count) + mention garantie/remboursement + comparaison Eux vs Nous
objection_markers = {
    "garantie": r"garanti(?:e|r)|satisfait\s+ou\s+rembours|remboursement",
    "livraison": r"(livraison|exp[ée]dition).{0,50}(gratuit|24h|48h|rapide|\d+\s*jours)",
    "retour": r"retour\s+gratuit|sans\s+frais\s+de\s+retour|\d+\s*jours?\s+pour\s+(changer|rendre)",
    "prix_comparatif": r"(vs|contre|compar[ée]\s+[àa])\s+.{0,40}(prix|autres|concurrent)",
    "engagement": r"sans\s+engagement|r[ée]siliation\s+(?:libre|simple|\d+\s*clic)",
    "securite_rgpd": r"(rgpd|ssl|donn[ée]es?\s+(?:s[ée]curis|prot[ée]g))",
    "essai_gratuit": r"(essai|offre\s+d[ée]couverte|gratuit\s+pendant)",
}
obj_hits = {k: len(re.findall(p, BODY_L)) for k, p in objection_markers.items()}
obj_covered = sum(1 for v in obj_hits.values() if v > 0)
# FAQ count (heuristique page.html + structure)
faq_q_pat = re.compile(
    r"(?:Combien|Comment|Pourquoi|Puis-?je|Est-?ce|Quels?|Quelles?|Quand|O[uù]|Que\s+(?:se\s+passe|faire))"
    r"[^?<>{}]{5,200}\?",
    re.I,
)
faq_qs = faq_q_pat.findall(BODY)
# Dedup + filter
seen = set(); faq_uniq = []
for q in faq_qs:
    qc = re.sub(r"\s+", " ", q).strip()
    if qc not in seen and len(qc) < 250:
        seen.add(qc); faq_uniq.append(qc)
faq_count = len(faq_uniq)

if obj_covered >= 4 and faq_count >= 5:
    pts = 3; v = "top"
elif obj_covered >= 2 or faq_count >= 4:
    pts = 2; v = "ok"
elif obj_covered >= 1 or faq_count >= 2:
    pts = 1; v = "weak"
else:
    pts = 0; v = "critical"

results.append(entry(
    "per_03", "Objections levées", pts, v,
    {"objection_markers_hit": {k: v for k, v in obj_hits.items() if v > 0},
     "distinct_objections_covered": obj_covered, "faq_question_count": faq_count},
    "Top: ≥4 objections distinctes + FAQ ≥5 Q. OK: ≥2 objections ou FAQ ≥4 Q. Weak: ≥1. Critical: 0."
))

# ══════════════════════════════════════════════════════════════
# per_04 — Preuves concrètes (chiffres, stats, études, before/after)
# ══════════════════════════════════════════════════════════════
# Compte les % sourcés, les grands nombres (clients, années, repas), études, avant/après
percent_mentions = len(re.findall(r"\b\d{1,3}\s*%", BODY))
big_numbers = len(re.findall(r"\b\d{1,3}(?:[\s\u00a0.]\d{3}){1,3}\b", BODY))  # 10 000 / 45 000 000
year_exp = len(re.findall(r"\b(depuis|fond[ée])\s+\w*\s*\d{4}", BODY_L))
study_mentions = len(re.findall(r"[ée]tude\s+(clinique|scientifique|men[ée]e|r[ée]alis[ée]e)", BODY_L))
before_after = len(re.findall(r"(avant\s*/\s*apr[èe]s|before[- ]after|avant\s+et\s+apr[èe]s)", BODY_L))
press_logos = len(re.findall(r"(vu\s+dans|parl[ée]\s+de\s+nous|ils\s+parlent\s+de\s+nous|as\s+seen\s+in)", BODY_L))

proof_types = 0
if percent_mentions >= 2: proof_types += 1
if big_numbers >= 1: proof_types += 1
if study_mentions >= 1: proof_types += 1
if before_after >= 1: proof_types += 1
if len(trust_widgets) >= 1: proof_types += 1
if press_logos >= 1: proof_types += 1

if proof_types >= 4 and (percent_mentions >= 3 or study_mentions >= 1):
    pts = 3; v = "top"
elif proof_types >= 2:
    pts = 2; v = "ok"
elif proof_types >= 1:
    pts = 1; v = "weak"
else:
    pts = 0; v = "critical"  # killer trigger

results.append(entry(
    "per_04", "Preuves concrètes", pts, v,
    {"percent_mentions": percent_mentions, "big_numbers": big_numbers,
     "year_experience": year_exp, "study_mentions": study_mentions,
     "before_after": before_after, "trust_widgets": len(trust_widgets),
     "press_logos": press_logos, "proof_types_distinct": proof_types},
    "Top: ≥4 types de preuves + (3+ % OU étude). OK: ≥2 types. Weak: 1 type. Critical: 0."
))

# ══════════════════════════════════════════════════════════════
# per_05 — Témoignages nommés + photo/vidéo
# ══════════════════════════════════════════════════════════════
n_testim = len(testimonials)
has_photo = any(t.get("hasPhoto") for t in testimonials)
has_widget_vrfd = any(
    (w.get("type") or "").lower() in {"trustpilot", "google", "judgeme", "avis-verifies", "yotpo"}
    for w in trust_widgets
)
# Détection vidéo testimoniale (rare mais on la cherche dans html)
video_testim = len(re.findall(r"(t[ée]moignage[s]?\s+vid[ée]o|client[s]?\s+parle|" \
                              r"<video[^>]*testimonial|youtube.*testim)", BODY_L))
# Noms propres dans testimonials (prénom + détail)
named_count = 0
for t in testimonials:
    txt = t.get("text", "") or ""
    if re.search(r"\b[A-Z][a-zéèêà]{2,}(?:\s+et\s+[A-Z][a-zéèêà]{2,})?\b", txt):
        if len(txt) > 20:
            named_count += 1

if (video_testim >= 1 or has_widget_vrfd) and named_count >= 2 and has_photo:
    pts = 3; v = "top"
elif named_count >= 2 or has_widget_vrfd:
    pts = 2; v = "ok"
elif n_testim >= 1:
    pts = 1; v = "weak"
else:
    pts = 0; v = "critical"

results.append(entry(
    "per_05", "Témoignages nommés + photo/vidéo", pts, v,
    {"testimonial_count": n_testim, "named_count": named_count, "has_photo": has_photo,
     "has_verified_widget": has_widget_vrfd, "video_testimonial_hits": video_testim},
    "Top: (vidéo OU widget vérifié) + ≥2 nommés + photo. OK: ≥2 nommés OU widget. Weak: ≥1 témoignage. Critical: 0."
))

# ══════════════════════════════════════════════════════════════
# per_06 — FAQ ciblée sur objections réelles
# ══════════════════════════════════════════════════════════════
# Réutilise faq_uniq de per_03
def classify_faq_q(q):
    ql = q.lower()
    if re.search(r"(qui\s+sommes|histoire\s+de\s+la\s+marque|fondateur|valeurs)", ql):
        return "hors_sujet"
    if re.search(r"(prix|co[uû]te|tarif|paiement|abonnement|engagement)", ql):
        return "financier"
    if re.search(r"(livraison|exp[ée]dition|d[ée]lai|re[cç]ois|exp[ée]di)", ql):
        return "logistique"
    if re.search(r"(efficac|r[ée]sultat|marche|fonctionn|transition|convenir|convient)", ql):
        return "efficacite"
    if re.search(r"(retour|rembours|garantie|chang|rendre|modifier)", ql):
        return "garantie"
    if re.search(r"(compatible|compatibil|adapt|convient)", ql):
        return "compatibilite"
    if re.search(r"(support|contact|aide|probl[èe]me)", ql):
        return "support"
    return "autre"

faq_cats = [classify_faq_q(q) for q in faq_uniq]
business_q = sum(1 for c in faq_cats if c not in {"hors_sujet", "autre"})
cat_distinct = len(set(c for c in faq_cats if c not in {"hors_sujet", "autre"}))

if faq_count >= 5 and business_q >= 5 and cat_distinct >= 3:
    pts = 3; v = "top"
elif faq_count >= 4 and business_q >= 3:
    pts = 2; v = "ok"
elif faq_count >= 2:
    pts = 1; v = "weak"
else:
    pts = 0; v = "critical"
# Tolérance : jusqu'à 10 Q acceptable si ≥80 % business
if faq_count > 10 and business_q / max(faq_count, 1) < 0.7:
    pts = min(pts, 2)

results.append(entry(
    "per_06", "FAQ ciblée objections", pts, v,
    {"faq_count": faq_count, "business_q": business_q, "categories_distinct": cat_distinct,
     "categories": faq_cats[:15], "sample_questions": faq_uniq[:8]},
    "Top: ≥5 Q + ≥5 business + ≥3 catégories. OK: ≥4 Q + ≥3 business. Weak: ≥2 Q. Critical: <2 Q."
))

# ══════════════════════════════════════════════════════════════
# per_07 — Ton cohérent avec la cible
# ══════════════════════════════════════════════════════════════
tu_hits = len(re.findall(r"\b(tu|ton|tes|toi)\b", BODY_L[:15000]))
vous_hits = len(re.findall(r"\b(vous|votre|vos)\b", BODY_L[:15000]))
mix_ratio = min(tu_hits, vous_hits) / max(max(tu_hits, vous_hits), 1)
# Signature markers : punchlines / interjections / formules de marque
punch_hits = len(re.findall(
    r"(arr[êe]te\s+de|fini(?:e)?s?\s+les|enfin|bravo|\\bwow\\b|on\s+sait\s+que|"
    r"parce\s+qu(?:e|')|soyons\s+honn[êe]tes?|spoiler)",
    BODY_L[:15000]
))

# Incohérence si mix tutoiement/vouvoiement fort (>20%)
if mix_ratio > 0.2:
    pts = 1; v = "weak"  # ton incohérent
elif punch_hits >= 3:
    pts = 3; v = "top"
elif tu_hits + vous_hits >= 20:
    pts = 2; v = "ok"
else:
    pts = 1; v = "weak"

results.append(entry(
    "per_07", "Ton cohérent", pts, v,
    {"tu_hits": tu_hits, "vous_hits": vous_hits, "mix_ratio": round(mix_ratio, 2),
     "punchline_hits": punch_hits},
    "Top: adresse stable + ≥3 punchlines. OK: adresse stable volume ≥20. Weak: mix ou faible volume."
))

# ══════════════════════════════════════════════════════════════
# per_08 — Absence de jargon creux
# ══════════════════════════════════════════════════════════════
JARGON = {
    "cree_avec_soin": r"cr[ée]{1,3}e?s?\s+avec\s+soin",
    "avec_passion": r"avec\s+passion",
    "haut_niveau_exigence": r"haut\s+niveau\s+d[''’]exigence",
    "point_dhonneur": r"point\s+d[''’]honneur",
    "plusieurs_dizaines_de": r"plusieurs\s+(dizaines|centaines|milliers)\s+de",
    "solution_innovante": r"solution\s+innovante",
    "expertise_reconnue": r"(expertise|savoir[- ]faire)\s+reconnue?s?",
    "leader_marche": r"leader\s+(du|sur\s+le)\s+march[ée]",
    "qualite_premium": r"qualit[ée]\s+(irr[ée]prochable|premium|sup[ée]rieure)",
    "equipe_passionnee": r"[ée]quipe\s+passionn[ée]e?",
    "haut_de_gamme": r"haut\s+de\s+gamme",
    "engagement_qualite": r"engagement\s+qualit[ée]",
    "savoir_faire_unique": r"savoir[- ]faire\s+unique",
    "innovation_continue": r"innovation\s+continue",
}
jargon_hits = {k: len(re.findall(p, BODY_L)) for k, p in JARGON.items()}
jargon_total = sum(jargon_hits.values())
distinct_jargon = sum(1 for v in jargon_hits.values() if v > 0)

if jargon_total == 0:
    pts = 3; v = "top"
elif jargon_total <= 4:
    pts = 2; v = "ok"
elif jargon_total <= 7:
    pts = 1; v = "weak"
else:
    pts = 0; v = "critical"  # killer penalty

results.append(entry(
    "per_08", "Absence de jargon creux", pts, v,
    {"jargon_hits": {k: v for k, v in jargon_hits.items() if v > 0},
     "jargon_total": jargon_total, "distinct_jargon_patterns": distinct_jargon},
    "Top: 0 hit. OK: 1-4 hits. Weak: 5-7 hits. Critical: ≥8 hits → cap 20/24."
))

# ══════════════════════════════════════════════════════════════
# Filtrage par pageType + Pondération + renormalisation
# ══════════════════════════════════════════════════════════════
active_results = []
skipped_results = []
for r in results:
    if is_criterion_applicable(r["id"], PAGE_TYPE):
        r["applicable"] = True
        active_results.append(r)
    else:
        r["applicable"] = False
        r["score"] = 0
        r["verdict"] = "skipped"
        r["rationale"] = f"Critère non applicable pour pageType={PAGE_TYPE}"
        skipped_results.append(r)

weights = grid.get("pageTypeWeights", {})
raw_total = sum(r["score"] for r in active_results)
active_count = len(active_results)
active_max_raw = active_count * 3

weighted_sum = 0.0
weighted_max = 0.0
for r in active_results:
    w = weights.get(r["id"], {}).get(PAGE_TYPE, 1.0)
    weighted_sum += r["score"] * w
    weighted_max += 3 * w
    r["weight"] = w
    r["weightedScore"] = round(r["score"] * w, 2)

# Marquer les skipped avec weight=0
for r in skipped_results:
    r["weight"] = 0
    r["weightedScore"] = 0

final_normalized = (weighted_sum / weighted_max) * active_max_raw if weighted_max else 0

# ══════════════════════════════════════════════════════════════
# Killers & caps (seulement sur les critères actifs)
# ══════════════════════════════════════════════════════════════
caps_applied = []
active_ids = {r["id"] for r in active_results}

per01 = next((r for r in active_results if r["id"] == "per_01"), None)
per04 = next((r for r in active_results if r["id"] == "per_04"), None)
per08 = next((r for r in active_results if r["id"] == "per_08"), None)

final_capped = final_normalized
# Caps proportionnels au max actif (pas au 24 fixe)
cap_third = round(active_max_raw / 3)
cap_half = round(active_max_raw / 2.4)
cap_high = round(active_max_raw * 0.83)

if per01 and per01["score"] == 0:
    final_capped = min(final_capped, cap_third)
    caps_applied.append(f"per_01_critical cap {cap_third}/{active_max_raw}")
if per04 and per04["score"] == 0:
    final_capped = min(final_capped, cap_half)
    caps_applied.append(f"per_04_critical cap {cap_half}/{active_max_raw}")
if per08 and per08["score"] == 0:
    final_capped = min(final_capped, cap_high)
    caps_applied.append(f"per_08_critical cap {cap_high}/{active_max_raw}")

# Rounded to nearest .5
final_rounded = round(final_capped * 2) / 2

# Score normalisé /100
score_100 = round((final_rounded / active_max_raw) * 100, 1) if active_max_raw > 0 else 0

# ─── Perception Layer 2 : evidence + hints Persuasion ───
_perception_block = {"available": False}
if _HAS_PERCEPTION:
    _p = load_perception(LABEL, PAGE_TYPE, ROOT)
    _sig = perception_signals(_p)
    _perception_block = {"available": _sig.get("pc_available", False), "signals": _sig}
    if _sig.get("pc_available"):
        for r in results:
            # per_01 (preuve sociale concentrée) : logos presse + testimonials
            if r["id"] == "per_01":
                r.setdefault("perception_has_social_proof", _sig.get("pc_has_social_proof", False))
            # per_04 (preuve sociale diversifiée)
            if r["id"] == "per_04":
                r.setdefault("perception_social_proof_count",
                             count_component(_p, "testimonial_block") + count_component(_p, "social_proof_logos"))
            # per_05 (CTA multiples diluant la conversion) : critique si >5 cta_band
            if r["id"] == "per_05":
                r.setdefault("perception_cta_bands_count", _sig.get("pc_num_cta_bands", 0))

output = {
    "client": LABEL,
    "url": meta.get("url") or meta.get("finalUrl"),
    "pageType": PAGE_TYPE,
    "scoredBy": "score_persuasion.py v2.0",
    "scoredAt": _scored_at(),
    "gridVersion": grid.get("version"),
    "criteria": results,
    "activeCriteria": active_count,
    "skippedCriteria": [r["id"] for r in skipped_results],
    "rawTotal": raw_total,
    "rawMax": active_max_raw,
    "weightedSum": round(weighted_sum, 2),
    "weightedMax": round(weighted_max, 2),
    "finalNormalized": round(final_normalized, 2),
    "finalCapped": round(final_capped, 2),
    "finalRounded": final_rounded,
    "finalMax": active_max_raw,
    "score100": score_100,
    "capsApplied": caps_applied,
    "verdict": (
        "Killer triggered" if caps_applied else
        ("TOP" if score_100 >= 80 else
         "SOLIDE" if score_100 >= 60 else
         "MOYEN" if score_100 >= 40 else
         "FAIBLE")
    ),
    "_perception": _perception_block,
}

OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
print(f"[{LABEL}] [{PAGE_TYPE}] persuasion = {final_rounded}/{active_max_raw} ({score_100}/100)"
      f"  (raw {raw_total}/{active_max_raw}, weighted {round(weighted_sum,1)}/{round(weighted_max,1)})"
      + (f" — CAPS: {', '.join(caps_applied)}" if caps_applied else ""))
for r in results:
    skip = " [SKIP]" if not r.get("applicable", True) else ""
    w = r.get('weight', 0)
    print(f"  {r['id']:6s} {r['score']}/3 [{r['verdict']:8s}] (w={w})  {r['label']}{skip}")
if skipped_results:
    print(f"  Critères exclus ({PAGE_TYPE}): {', '.join(r['id'] for r in skipped_results)}")
