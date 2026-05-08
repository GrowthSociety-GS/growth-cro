#!/usr/bin/env python3
"""
score_coherence.py — Scorer Bloc 4 Cohérence V3 pour GrowthCRO Playbook.

Usage:
    python score_coherence.py <label> [pageType]
Reads:  data/captures/<label>/<pageType>/capture.json + page.html
Writes: data/captures/<label>/<pageType>/score_coherence.json

Applique les 6 critères coh_01→coh_06 de playbook/bloc_4_coherence_v3.json.
"""
import json, sys, re, pathlib
from collections import Counter
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
    print("Usage: score_coherence.py <label> [pageType]", file=sys.stderr); sys.exit(1)
LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else "home"

ROOT = pathlib.Path(__file__).resolve().parents[3]
if (ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json").exists():
    CAP = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json"
    HTML = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "page.html"
    OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "score_coherence.json"
else:
    CAP = ROOT / "data" / "captures" / LABEL / "capture.json"
    HTML = ROOT / "data" / "captures" / LABEL / "page.html"
    OUT = ROOT / "data" / "captures" / LABEL / "score_coherence.json"
GRID = ROOT / "playbook" / "bloc_4_coherence_v3.json"

if not CAP.exists():
    print(f"capture.json missing: {CAP}", file=sys.stderr); sys.exit(2)

cap = json.loads(CAP.read_text())
grid = json.loads(GRID.read_text())
html_raw = HTML.read_text(errors="ignore") if HTML.exists() else ""

_body = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
_body = re.sub(r"<style[^>]*>.*?</style>", " ", _body, flags=re.DOTALL | re.I)
_body_clean = re.sub(r"<[^>]+>", " ", _body)
BODY = re.sub(r"\s+", " ", _body_clean)
BODY_L = BODY.lower()

hero = cap.get("hero", {}) or {}
structure = cap.get("structure", {}) or {}
meta = cap.get("meta", {}) or {}
tech = cap.get("technical", {}) or {}
social = cap.get("socialProof", {}) or {}

headings = structure.get("headings", []) or []
all_ctas = structure.get("ctas", []) or []


def _scored_at() -> str:
    return meta.get("capturedAt") or cap.get("capturedAt") or datetime.now(timezone.utc).isoformat()

# ── FALLBACK H1/headings depuis page.html si capture.json vide ──
if html_raw and not (hero.get("h1") or "").strip():
    _body_tags = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
    _body_tags = re.sub(r"<style[^>]*>.*?</style>", " ", _body_tags, flags=re.DOTALL | re.I)
    h1_matches = re.findall(r'<h1\b[^>]*>(.*?)</h1>', _body_tags, re.DOTALL | re.I)
    if h1_matches:
        h1_text = re.sub(r'<[^>]+>', '', h1_matches[0]).strip()
        if h1_text:
            hero["h1"] = h1_text
            hero["h1Count"] = len(h1_matches)
            print(f"  [FALLBACK] H1 récupéré depuis page.html: '{h1_text[:60]}'")

if html_raw and not headings:
    _body_tags = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
    _body_tags = re.sub(r"<style[^>]*>.*?</style>", " ", _body_tags, flags=re.DOTALL | re.I)
    html_h = re.findall(r'<(h[1-4])\b[^>]*>(.*?)</\1>', _body_tags, re.DOTALL | re.I)
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
_sp_coh = get_spatial_evidence("coherence", _spatial_data) if _spatial_data else {}
if _sp_coh:
    print(f"  [SPATIAL] Cohérence enrichi avec {len(_sp_coh)} clés spatiales")

results = []

# ─── Filtrage par pageType ───────────────────────────────────
CRITERIA_PAGE_TYPES = {
    "coh_01": "*",
    "coh_02": "*",
    "coh_03": ["pdp", "lp_leadgen", "lp_sales", "quiz_vsl"],
    "coh_04": "*",
    "coh_05": "*",
    "coh_06": "*",
}

def is_applicable(cid, pt):
    p = CRITERIA_PAGE_TYPES.get(cid, "*")
    if p == "*": return True
    return pt in p

def entry(cid, label, pts, verdict, evidence, rationale):
    if _sp_coh:
        evidence = {**evidence, **_sp_coh}
    return {"id": cid, "label": label, "score": pts, "max": 3,
            "verdict": verdict, "evidence": evidence, "rationale": rationale}


# ══════════════════════════════════════════════════════════════
# coh_01 — Promesse principale claire en 5 sec
# ══════════════════════════════════════════════════════════════
h1 = (hero.get("h1") or "").strip()
subtitle = (hero.get("subtitle") or "").strip()
fold_text = f"{h1} {subtitle}".lower()

# 3 questions : Quoi? Pour qui? Pourquoi?
# Quoi : mot tangible (pas "Solution", "Bienvenue")
quoi_patterns = [
    r"\b(croquettes|alimentation|logiciel|app|plateforme|outil|service|formation|programme|recette|produit|offre|assurance|livraison|box)\b",
    r"\b(coaching|conseil|agence|studio|freelance|marketplace|boutique|solution)\b",
]
has_quoi = any(re.search(p, fold_text) for p in quoi_patterns)

# Pour qui : persona
pour_qui_patterns = [
    r"\bpour (les |mon |votre |ses |son |ton )?\w+",
    r"\bchiens?\b", r"\bchats?\b", r"\bfreelances?\b", r"\béquipes?\b",
    r"\bentrepreneurs?\b", r"\bstartups?\b", r"\bmarques?\b",
    r"\bparticuliers?\b", r"\bprofessionnels?\b", r"\bparents?\b",
    r"\bvous qui\b", r"\btoi qui\b", r"\bsi (tu|vous)\b",
]
has_pour_qui = any(re.search(p, fold_text) for p in pour_qui_patterns)

# Pourquoi : bénéfice / outcome
pourquoi_patterns = [
    r"\bchange\b", r"\btransforme", r"\bgagn", r"\béconomis",
    r"\bpersonnalis", r"\bsur[- ]mesure", r"\bexpert",
    r"\baméliore", r"\bsimplifie", r"\bréduit", r"\bprotège",
    r"\b\d+\s*%", r"\bx\d+", r"\bgaranti",
]
has_pourquoi = any(re.search(p, fold_text) for p in pourquoi_patterns)

questions = sum([has_quoi, has_pour_qui, has_pourquoi])

# Longueur H1
h1_wc = len(h1.split())
# "Bienvenue" / slogan vague
is_slogan_vague = bool(re.match(r"^(bienvenue|welcome|hello|accueil|découvrez)\b", h1.lower()))

if is_slogan_vague or not h1:
    pts = 0; v = "critical"
    rationale = f"H1 vague/absent: '{h1[:50]}'. Slogan={is_slogan_vague}."
elif questions >= 3 and 4 <= h1_wc <= 15:
    pts = 3; v = "top"
    rationale = f"3/3 questions (quoi={has_quoi}, pour_qui={has_pour_qui}, pourquoi={has_pourquoi}). H1 {h1_wc} mots."
elif questions >= 2:
    pts = 1.5; v = "ok"
    rationale = f"{questions}/3 questions (quoi={has_quoi}, pour_qui={has_pour_qui}, pourquoi={has_pourquoi})."
else:
    pts = 0; v = "critical"
    rationale = f"Seulement {questions}/3 questions répondues dans le fold."

results.append(entry("coh_01", "Promesse claire 5 sec", pts, v,
    {"h1": h1[:100], "subtitle": subtitle[:100], "questions": questions,
     "has_quoi": has_quoi, "has_pour_qui": has_pour_qui, "has_pourquoi": has_pourquoi,
     "h1_wordcount": h1_wc, "is_slogan_vague": is_slogan_vague}, rationale))


# ══════════════════════════════════════════════════════════════
# coh_02 — Cible identifiable
# ══════════════════════════════════════════════════════════════
# Scan fold + first 5 headings for persona
persona_patterns = [
    r"\bpour (les |votre |mon |ton )?\w+",
    r"\bchiens?\b", r"\bchats?\b", r"\bfreelances?\b", r"\béquipes?\b",
    r"\bmanagers?\b", r"\bdéveloppeurs?\b", r"\bentrepreneurs?\b",
    r"\bparents?\b", r"\bfemmes?\b", r"\bhommes?\b", r"\bétudiants?\b",
    r"\bpropriétaires?\b", r"\bcommerçants?\b", r"\bartisans?\b",
    r"\bvous qui\b", r"\btoi qui\b", r"\bsi (tu|vous) (êtes|es|avez|as|cherch)\b",
]

# In fold (H1 + subtitle)
persona_fold = sum(1 for p in persona_patterns if re.search(p, fold_text))
# In headings (H2/H3)
headings_text = " ".join(h.get("text", "").lower() for h in headings[:15])
persona_headings = sum(1 for p in persona_patterns if re.search(p, headings_text))
# In body (first 5000 chars)
persona_body = sum(1 for p in persona_patterns if re.search(p, BODY_L[:5000]))

# Contexte défi / besoin
defi_patterns = [
    r"\bfatigué|marre|assez|ras.le.bol|frustré",
    r"\bproblème|difficulté|galère|challenge|défi",
    r"\bbesoin de|envie de|cherchez|cherche[sz]? à",
]
has_defi = any(re.search(p, BODY_L[:5000]) for p in defi_patterns)

if persona_fold >= 2 and has_defi:
    pts = 3; v = "top"
    rationale = f"Persona explicite dans le fold ({persona_fold} signaux) + contexte défi détecté."
elif persona_fold >= 1 or (persona_headings >= 2 and persona_body >= 3):
    pts = 1.5; v = "ok"
    rationale = f"Persona détecté (fold={persona_fold}, headings={persona_headings}, body={persona_body}). Défi={has_defi}."
else:
    pts = 0; v = "critical"
    rationale = f"Aucune cible identifiable (fold={persona_fold}, headings={persona_headings})."

results.append(entry("coh_02", "Cible identifiable", pts, v,
    {"persona_fold_signals": persona_fold, "persona_headings": persona_headings,
     "persona_body": persona_body, "has_defi": has_defi}, rationale))


# ══════════════════════════════════════════════════════════════
# coh_03 — Alignement ad → LP (scent matching)
# ══════════════════════════════════════════════════════════════
# Sans accès à l'ad source, on évalue la cohérence interne :
# H1 vs meta title vs CTA vs offer
meta_title = (tech.get("title") or meta.get("title") or "").lower()
meta_desc = (tech.get("metaDescription") or meta.get("metaDescription") or "").lower()
cta_label = ((hero.get("primaryCta") or {}).get("label") or "").lower()

# Overlap H1 ↔ meta title (mots communs)
h1_words = set(re.findall(r"\w{3,}", h1.lower()))
title_words = set(re.findall(r"\w{3,}", meta_title))
desc_words = set(re.findall(r"\w{3,}", meta_desc))

title_overlap = len(h1_words & title_words) / max(len(h1_words), 1)
desc_overlap = len(h1_words & desc_words) / max(len(h1_words), 1)

# CTA cohérence avec H1 (le CTA fait référence à l'offre mentionnée en H1)
cta_words = set(re.findall(r"\w{3,}", cta_label))
cta_h1_overlap = len(cta_words & h1_words) / max(len(cta_words), 1)

# Offer consistency (prix/offre mentionné en H1 retrouvé dans le body)
offer_patterns = re.findall(r"(-?\d+\s*[%€$]|\d+[.,]\d+\s*€|gratuit|offre|promo|essai|démo)", fold_text)
offer_in_body = sum(1 for o in offer_patterns if o.lower() in BODY_L[:3000])

coherence_score = 0
if title_overlap >= 0.4: coherence_score += 1
if desc_overlap >= 0.3: coherence_score += 1
if cta_label and len(cta_label) > 3: coherence_score += 1  # CTA exists and is meaningful
if len(offer_patterns) > 0: coherence_score += 1

if coherence_score >= 3:
    pts = 3; v = "top"
    rationale = f"Forte cohérence interne: title_overlap={title_overlap:.0%}, desc_overlap={desc_overlap:.0%}, CTA='{cta_label[:30]}', offres={len(offer_patterns)}."
elif coherence_score >= 2:
    pts = 1.5; v = "ok"
    rationale = f"Cohérence partielle: {coherence_score}/4 signaux."
else:
    pts = 0; v = "critical"
    rationale = f"Faible cohérence: {coherence_score}/4. H1 vs title overlap={title_overlap:.0%}."

results.append(entry("coh_03", "Alignement ad → LP", pts, v,
    {"title_overlap": round(title_overlap, 2), "desc_overlap": round(desc_overlap, 2),
     "cta_label": cta_label[:50], "offer_patterns_found": offer_patterns[:5],
     "coherence_score": coherence_score}, rationale))


# ══════════════════════════════════════════════════════════════
# coh_04 — Positionnement différenciant
# ══════════════════════════════════════════════════════════════
# Red flags : patterns génériques sans substance
GENERIC_PATTERNS = [
    r"solution\s+(complète|innovante|unique)",
    r"(meilleur|leader)\s+(du|sur)\s+(le\s+)?march[ée]",
    r"partenaire\s+de\s+confiance",
    r"qualit[ée]\s+(irr[ée]prochable|premium|sup[ée]rieure)",
    r"[ée]quipe\s+passionn[ée]e",
    r"expertise\s+reconnue",
    r"innovation\s+continue",
    r"haut\s+de\s+gamme",
]
generic_hits = sum(len(re.findall(p, BODY_L)) for p in GENERIC_PATTERNS)

# Differentiation signals
DIFF_PATTERNS = {
    "proprietary_method": r"(méthode|process|recette|algorithme|technologie)\s+\w*\s*(propri[ée]taire|brevet[ée]e?|exclusive?|unique)",
    "certification": r"(certifi[ée]|label|norme\s+\w+|bio|iso|haccp|vétérinaire)",
    "origin": r"(fabriqu[ée]\s+en|made\s+in|fran[çc]ais|local|artisan)",
    "named_expert": r"(cr[ée]{1,2}[ée]\s+par|fond[ée]\s+par|con[çc]u\s+par|formul[ée]\s+par)",
    "vs_competitor": r"(vs\s+|contre\s+|compar[ée]\s+[àa]|à\s+la\s+différence\s+de)",
    "unique_claim": r"\b(seul[es]?|premier|unique|exclusi[fv])\b",
    "specific_ingredient": r"(poulet|saumon|agneau|riz|patate|prot[ée]ines?\s+\w+|sans\s+(gluten|c[ée]r[ée]ales|additif))",
}
diff_hits = {k: len(re.findall(p, BODY_L)) for k, p in DIFF_PATTERNS.items()}
diff_count = sum(1 for v in diff_hits.values() if v > 0)

if diff_count >= 3 and generic_hits <= 2:
    pts = 3; v = "top"
    rationale = f"{diff_count} signaux différenciation, {generic_hits} patterns génériques."
elif diff_count >= 1 and generic_hits <= 4:
    pts = 1.5; v = "ok"
    rationale = f"{diff_count} différenciation mais {generic_hits} patterns génériques."
else:
    pts = 0; v = "critical"
    rationale = f"0 différenciation détectée, {generic_hits} patterns génériques."

results.append(entry("coh_04", "Positionnement différenciant", pts, v,
    {"diff_signals": {k: v for k, v in diff_hits.items() if v > 0},
     "diff_count": diff_count, "generic_hits": generic_hits}, rationale))


# ══════════════════════════════════════════════════════════════
# coh_05 — Ton de marque reconnaissable
# ══════════════════════════════════════════════════════════════
# Tutoiement vs vouvoiement
tu_hits = len(re.findall(r"\b(tu|ton|tes|toi)\b", BODY_L[:15000]))
vous_hits = len(re.findall(r"\b(vous|votre|vos)\b", BODY_L[:15000]))
mix_ratio = min(tu_hits, vous_hits) / max(max(tu_hits, vous_hits), 1)

# Tone markers : punchlines, interjections, informal
punch_patterns = [
    r"(arr[êe]te\s+de|fini(?:e)?s?\s+les|enfin|bravo|wow|on\s+sait\s+que|"
    r"parce\s+qu(?:e|')|soyons\s+honn[êe]tes?|spoiler|et\s+boom|bam|tadaaa)",
]
punch_hits = sum(len(re.findall(p, BODY_L[:15000])) for p in punch_patterns)

# AI slop patterns
AI_SLOP = [
    r"dans\s+un\s+monde\s+en\s+constante\s+[ée]volution",
    r"il\s+est\s+(essentiel|crucial|important)\s+de",
    r"n['']h[ée]sitez\s+pas\s+[àa]",
    r"afin\s+de\s+vous\s+offrir",
    r"notre\s+engagement\s+envers",
    r"au\s+sein\s+de\s+notre",
    r"force\s+est\s+de\s+constater",
]
ai_slop_hits = sum(len(re.findall(p, BODY_L[:15000])) for p in AI_SLOP)

tone_inconsistent = mix_ratio > 0.2

if not tone_inconsistent and punch_hits >= 3 and ai_slop_hits == 0:
    pts = 3; v = "top"
    rationale = f"Ton signature: {punch_hits} punchlines, 0 AI slop, tu/vous stable (mix={mix_ratio:.0%})."
elif not tone_inconsistent and ai_slop_hits <= 2:
    pts = 1.5; v = "ok"
    rationale = f"Ton identifiable: punch={punch_hits}, AI slop={ai_slop_hits}, mix={mix_ratio:.0%}."
else:
    pts = 0; v = "critical"
    rationale = f"Ton problématique: inconsistant={tone_inconsistent}, AI slop={ai_slop_hits}, punch={punch_hits}."

results.append(entry("coh_05", "Ton de marque", pts, v,
    {"tu_hits": tu_hits, "vous_hits": vous_hits, "mix_ratio": round(mix_ratio, 2),
     "punchline_hits": punch_hits, "ai_slop_hits": ai_slop_hits,
     "tone_inconsistent": tone_inconsistent}, rationale))


# ══════════════════════════════════════════════════════════════
# coh_06 — Un seul objectif prioritaire par page
# ══════════════════════════════════════════════════════════════
# URL normalization helper (strip www, protocol, trailing slash)
def _norm_url_coh(href):
    if not href: return ""
    href = href.strip().rstrip("/")
    try:
        from urllib.parse import urlparse
        p = urlparse(href)
        host = p.netloc.lower().replace("www.", "")
        path = p.path.rstrip("/") or "/"
        return f"{host}{path}"
    except Exception:
        return href.lower().replace("www.", "")

# Use perceived global CTA data if available
perceived_primary_count = hero.get("primary_action_count", 0)
perceived_competing = hero.get("competing_ctas", 0)
perceived_unique = hero.get("unique_action_destinations", 0)

# Dédupliquer CTAs par href normalisé
href_counts = Counter(_norm_url_coh(c.get("href", "")) for c in all_ctas if c.get("href"))
href_counts.pop("", None)  # Remove empty
unique_destinations = perceived_unique if perceived_unique > 0 else len(href_counts)

# Primary CTA
primary = hero.get("primaryCta")
primary_href = (primary or {}).get("href", "")
norm_primary = _norm_url_coh(primary_href)
primary_count = perceived_primary_count if perceived_primary_count > 0 else (href_counts.get(norm_primary, 0) if norm_primary else 0)

# Competing CTAs : ceux qui ne sont pas le primary et ont un volume significatif
competing = []
for href_norm, count in href_counts.items():
    if href_norm != norm_primary and count >= 1:
        competing.append({"href": href_norm[:60], "count": count})

# Ratio d'attention : primary_count / total unique destinations
attention_ratio = primary_count / max(unique_destinations, 1)

# Navigation links (header + footer = sorties non-CTA)
nav_exit_links = sum(1 for c in all_ctas
    if c.get("tag") in ("a",) and c.get("href")
    and not c.get("href", "").startswith(("javascript:", "#", "mailto:")))

if primary_count >= 3 and unique_destinations <= 5 and attention_ratio >= 0.3:
    pts = 3; v = "top"
    rationale = f"Focus clair: CTA primaire {primary_count}× sur {unique_destinations} destinations. Ratio {attention_ratio:.0%}."
elif primary_count >= 2 and unique_destinations <= 10:
    pts = 1.5; v = "ok"
    rationale = f"Objectif identifiable: primaire {primary_count}×, {unique_destinations} destinations, {len(competing)} concurrents."
else:
    pts = 0; v = "critical"
    rationale = f"Objectif flou: primaire {primary_count}×, {unique_destinations} destinations, ratio {attention_ratio:.0%}."

results.append(entry("coh_06", "Mono-objectif par page", pts, v,
    {"primary_href": primary_href[:60] if primary_href else None,
     "primary_count": primary_count,
     "unique_destinations": unique_destinations,
     "attention_ratio": round(attention_ratio, 2),
     "competing_ctas": competing[:5],
     "total_links": nav_exit_links}, rationale))


# ══════════════════════════════════════════════════════════════
# Filtrage pageType + Pondération + Totaux
# ══════════════════════════════════════════════════════════════
active_results = []
skipped_results = []
for r in results:
    if is_applicable(r["id"], PAGE_TYPE):
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

for r in skipped_results:
    r["weight"] = 0
    r["weightedScore"] = 0

final_normalized = (weighted_sum / weighted_max) * active_max_raw if weighted_max else 0
final_rounded = round(final_normalized * 2) / 2

# ─── KILLERS Cohérence (V12 — P0.3 enrichi 2026-04-14) ───
# Caps nuancés (alignés sur pattern bloc_2_persuasion) :
#   - coh_01_critical (promesse 5s manquante)       → cap 1/3  (éliminatoire, LE killer base)
#   - coh_06_critical (multi-objectifs diluant)      → cap 1/2  (éliminatoire, focus = conversion)
#   - coh_03_critical (scent mismatch ad→LP, paid)   → cap 1/2  (éliminatoire, paid-only)
#   - coh_04_critical_penalty (0 différenciation)    → cap 5/6  (pénalité non éliminatoire, DTC template)
PAID_PAGE_TYPES = {"lp_leadgen", "lp_sales", "advertorial", "vsl"}
killers_fired = []  # liste de tuples (id, description, cap_ratio)
for r in active_results:
    is_critical = r.get("verdict") == "critical" or r.get("score", 0) == 0
    if not is_critical:
        continue
    cid = r["id"]
    if cid == "coh_01":
        killers_fired.append((cid, "coh_01 (promesse 5s manquante)", 1/3))
    elif cid == "coh_06":
        killers_fired.append((cid, "coh_06 (multi-objectifs diluant le focus)", 1/2))
    elif cid == "coh_03" and PAGE_TYPE in PAID_PAGE_TYPES:
        killers_fired.append((cid, f"coh_03 (scent mismatch ad→LP sur {PAGE_TYPE})", 1/2))
    elif cid == "coh_04":
        killers_fired.append((cid, "coh_04 (0 différenciation — DTC template)", 5/6))

if killers_fired:
    # Appliquer le cap le plus sévère (ratio minimal)
    strictest = min(killers_fired, key=lambda k: k[2])
    killer_cap = active_max_raw * strictest[2]
    descs = "; ".join(k[1] for k in killers_fired)
    if final_rounded > killer_cap:
        killer_note = (
            f"KILLERS {descs} — cap appliqué {killer_cap:.1f}/{active_max_raw} "
            f"(strictest={strictest[0]} ratio={strictest[2]:.2f}, raw={final_rounded})"
        )
        final_rounded = round(killer_cap * 2) / 2
    else:
        killer_note = f"KILLERS déclenchés {descs} mais score déjà sous cap {killer_cap:.1f}"
else:
    killer_note = None

score_100 = round((final_rounded / active_max_raw) * 100, 1) if active_max_raw > 0 else 0

# ─── Perception Layer 2 : evidence + hints Cohérence ───
_perception_block = {"available": False}
if _HAS_PERCEPTION:
    _p = load_perception(LABEL, PAGE_TYPE, ROOT)
    _sig = perception_signals(_p)
    _perception_block = {"available": _sig.get("pc_available", False), "signals": _sig}
    if _sig.get("pc_available"):
        for r in results:
            # coh_01 (CTA unifié) : si >5 cta_band = dilution
            if r["id"] == "coh_01":
                r.setdefault("perception_cta_bands_count", _sig.get("pc_num_cta_bands", 0))
                if _sig.get("pc_num_cta_bands", 0) > 5:
                    r.setdefault("perception_note", "Perception Layer 2 détecte >5 cta_band — dilution probable du focus")
            # coh_02 (cohérence promesse→preuve→CTA)
            if r["id"] == "coh_02":
                r.setdefault("perception_has_hero", _sig.get("pc_has_hero", False))
                r.setdefault("perception_has_social_proof", _sig.get("pc_has_social_proof", False))

output = {
    "client": LABEL,
    "url": meta.get("url") or meta.get("finalUrl"),
    "pageType": PAGE_TYPE,
    "scoredBy": "score_coherence.py v1.0",
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
    "finalRounded": final_rounded,
    "finalMax": active_max_raw,
    "score100": score_100,
    "capsApplied": [],
    "killersTriggered": [
        {"id": k[0], "description": k[1], "capRatio": round(k[2], 3)}
        for k in killers_fired
    ],
    "killerNote": killer_note,
    "verdict": (
        "TOP" if score_100 >= 80 else
        "SOLIDE" if score_100 >= 60 else
        "MOYEN" if score_100 >= 40 else
        "FAIBLE"
    ),
    "_perception": _perception_block,
}

OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
print(f"[{LABEL}] [{PAGE_TYPE}] coherence = {final_rounded}/{active_max_raw} ({score_100}/100)"
      f"  (raw {raw_total}/{active_max_raw}, weighted {round(weighted_sum,1)}/{round(weighted_max,1)})")
for r in results:
    skip = " [SKIP]" if not r.get("applicable", True) else ""
    w = r.get('weight', 0)
    print(f"  {r['id']:6s} {r['score']}/3 [{r['verdict']:8s}] (w={w})  {r['label']}{skip}")
if skipped_results:
    print(f"  Critères exclus ({PAGE_TYPE}): {', '.join(r['id'] for r in skipped_results)}")
