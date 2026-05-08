#!/usr/bin/env python3
"""
score_hero.py — Scorer Hero V3 pour GrowthCRO Playbook.

Usage:
    python score_hero.py <label>
Reads:  data/captures/<label>/capture.json
Writes: data/captures/<label>/score_hero.json

Applique les 6 critères du bloc 1 Hero V3.2.1 depuis playbook/bloc_1_hero_v3.json,
en lisant UNIQUEMENT les données structurées du SiteCapture (pas de regard aux PNG).
C'est le test de non-régression vs le scoring visuel baseline (Japhy = 15/18).

V3.2.1 (Sprint 2.5 V26.AA, 2026-05-03) : pageTypes hero_03/05 resserrés
(exclus listicle/advertorial/blog/vsl/thank_you_page/quiz_vsl).
GRID pointait sur bloc_1_hero_DRAFT.json (v3.0.0) jusqu'à 2026-05-04 — bug
silencieux découvert lors du cleanup V26.AA Phase B + corrigé en pointant
sur bloc_1_hero_v3.json (v3.2.1).
"""
import json, sys, re, pathlib
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
    print("Usage: score_hero.py <label> [pageType]  (e.g., japhy home)", file=sys.stderr); sys.exit(1)
LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else None

ROOT = pathlib.Path(__file__).resolve().parents[3]
# Support both old (flat) and new (multi-page) storage layouts
if PAGE_TYPE:
    CAP = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "score_hero.json"
elif (ROOT / "data" / "captures" / LABEL / "home" / "capture.json").exists():
    CAP = ROOT / "data" / "captures" / LABEL / "home" / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / "home" / "score_hero.json"
    PAGE_TYPE = "home"
else:
    CAP = ROOT / "data" / "captures" / LABEL / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / "score_hero.json"
    PAGE_TYPE = PAGE_TYPE or "home"
GRID = ROOT / "playbook" / "bloc_1_hero_v3.json"  # V3.2.1 — était DRAFT v3.0.0 jusqu'à 2026-05-04 (bug silencieux corrigé Phase B V26.AA cleanup)

# ─── Filtrage par pageType ───────────────────────────────────
# Chaque critère du scorer déclare pour quels pageTypes il est applicable.
# Si le pageType courant n'est pas dans la liste, le critère est SKIPPÉ.
# Format : {"scorer_id": "*" | ["home", "pdp", ...]}
# Basé sur cro_criteria_v2.json mais avec les IDs scorer (pas V2)
CRITERIA_PAGE_TYPES = {
    "hero_01": "*",                                           # H1 promesse — universel
    "hero_02": "*",                                           # Sous-titre — universel
    # V3.2.1 (Sprint 2.5 V26.AA) : exclus listicle/advertorial/blog/vsl/thank_you_page/quiz_vsl
    # Listicles éditoriaux (Weglot/Linear/Stripe blog) n'ont jamais de CTA hero ATF.
    # ALIGNÉ avec playbook/bloc_1_hero_v3.json hero_03.pageTypes (rétrocompat).
    "hero_03": ["home", "pdp", "lp_sales", "collection", "lp_leadgen", "challenge",
                "bundle_standalone", "squeeze", "webinar", "pricing", "comparison"],
    "hero_04": ["home", "pdp", "lp_sales", "collection", "lp_leadgen"],  # Visuel hero = produit en usage
    # V3.2.1 idem : preuve sociale fold 1 N/A en éditorial (place dans le contenu narratif).
    "hero_05": ["home", "pdp", "lp_sales", "collection", "lp_leadgen", "challenge",
                "bundle_standalone", "squeeze", "webinar", "pricing", "comparison"],
    "hero_06": "*",                                           # Test 5s — universel
}

def is_criterion_applicable(criterion_id: str, page_type: str) -> bool:
    """Vérifie si un critère s'applique au pageType courant."""
    pt = CRITERIA_PAGE_TYPES.get(criterion_id, "*")
    if pt == "*":
        return True
    return page_type in pt

cap = json.loads(CAP.read_text())
grid = json.loads(GRID.read_text())

# Load page.html for fallback heading extraction
HTML_PATH = CAP.parent / "page.html"
html_raw = HTML_PATH.read_text(errors="ignore") if HTML_PATH.exists() else ""

hero = cap.get("hero", {})
social = cap.get("socialProof", {})
overlays = cap.get("overlays", {})
tech = cap.get("technical", {})
structure = cap.get("structure", {})

# ── FALLBACK H1 : si capture.json dit h1="" mais page.html contient un <h1> ──
if html_raw and not (hero.get("h1") or "").strip():
    _body_no_script = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
    _body_no_style = re.sub(r"<style[^>]*>.*?</style>", " ", _body_no_script, flags=re.DOTALL | re.I)
    h1_matches = re.findall(r'<h1\b[^>]*>(.*?)</h1>', _body_no_style, re.DOTALL | re.I)
    if h1_matches:
        h1_text = re.sub(r'<[^>]+>', '', h1_matches[0]).strip()
        if h1_text:
            hero["h1"] = h1_text
            hero["h1Count"] = len(h1_matches)
            print(f"  [FALLBACK] H1 récupéré depuis page.html: '{h1_text[:60]}'")
            print(f"  [FALLBACK] {len(h1_matches)} H1 trouvé(s) dans le HTML")
meta = cap.get("meta", {})

# ── Spatial V9 enrichment (graceful degradation) ──────────────
_spatial_data = load_spatial(LABEL, PAGE_TYPE) if _HAS_SPATIAL else None
_sp_hero = get_spatial_evidence("hero", _spatial_data) if _spatial_data else {}
if _sp_hero:
    print(f"  [SPATIAL] Hero enrichi avec {len(_sp_hero)} clés spatiales")

results = []

# FIX V15.2: evidence ciblée par critère au lieu de broadcaster tout
_CRIT_SPATIAL_KEYS = {
    "hero_01": ["sp_h1_font_size", "sp_h1_contrast", "sp_h1_position"],
    "hero_02": [],  # subtitle n'a pas de clés spatiales spécifiques
    "hero_03": ["sp_cta_bbox", "sp_cta_area", "sp_cta_above_fold", "sp_cta_fold_distance",
                "sp_cta_isolation_score", "sp_cta_contrast", "sp_cta_min_dimension", "sp_cta_touch_target_ok"],
    "hero_04": ["sp_hero_image_bbox", "sp_hero_image_ratio", "sp_hero_height", "sp_hero_ratio"],
    "hero_05": ["sp_social_proof_in_fold"],
    "hero_06": ["sp_five_second_spatial_score", "sp_hero_whitespace_ratio",
                "sp_hero_element_count", "sp_hero_distraction_count"],
}

def score_entry(cid, label, pts, verdict, evidence, rationale):
    # Merge ONLY relevant spatial evidence for this criterion
    if _sp_hero:
        allowed = _CRIT_SPATIAL_KEYS.get(cid, [])
        filtered_sp = {k: v for k, v in _sp_hero.items() if k in allowed}
        evidence = {**evidence, **filtered_sp}
    return {
        "id": cid, "label": label, "score": pts, "max": 3,
        "verdict": verdict, "evidence": evidence, "rationale": rationale
    }

# ─────────────────────────────────────────────────────────────
# hero_01 — H1 = promesse spécifique (bénéfice + cible + différenciateur)
# ─────────────────────────────────────────────────────────────
h1 = (hero.get("h1") or "").strip()
h1_count = hero.get("h1Count", 0)
h1_lower = h1.lower()
words = [w for w in re.split(r"\s+", h1) if w]
wc = len(words)

# Cible : "pour <cible>", mention "chiens/chats/freelances/équipes/entrepreneurs/…"
target_patterns = [
    r"\bpour (les |mon |votre |ses |son |ton )?\w+",
    r"\bchiens?\b", r"\bchats?\b", r"\bfreelances?\b", r"\béquipes?\b",
    r"\bentrepreneurs?\b", r"\bstartups?\b", r"\bmarques?\b",
    r"\bparticuliers?\b", r"\bprofessionnels?\b", r"\bparents?\b", r"\bfemmes?\b", r"\bhommes?\b",
    r"\bdevelopers?\b", r"\bdesigners?\b", r"\bétudiants?\b",
]
has_target = any(re.search(p, h1_lower) for p in target_patterns)

# Bénéfice : verbe de transformation OU valeur tangible
benefit_patterns = [
    r"change\s+la\s+vie", r"\btransforme", r"\bgagn", r"\béconomis",
    r"sur[- ]mesure", r"personnalis", r"\bexpert", r"\boptimis",
    r"\baugment", r"\bboost", r"\baméliore", r"\baccélère", r"\bsimplifie",
    r"\bfait\s+gagner", r"\bréduit", r"-?\d+\s*%", r"\bx\d+",
    r"\ben \d+\s*(min|jour|semaine|mois)",
]
has_benefit = any(re.search(p, h1_lower) for p in benefit_patterns)

# Différenciateur : "seul(e)", "only", "sans X", "grâce à", "recommandé par", adjectif singulier ("experte", "vraie")
differentiator_patterns = [
    r"\bla seule\b", r"\ble seul\b", r"\bseule?s?\b",
    r"\bsans\b", r"\bgrâce à\b", r"\brecommandé", r"\bvéritable",
    r"\bexperte?s?\b", r"\bvraie?s?\b", r"\bunique", r"\bofficial", r"\bcertifié",
    r"\bchef\b", r"\bnumber one\b", r"\bn°\s*1",
]
has_diff = any(re.search(p, h1_lower) for p in differentiator_patterns)

signals = sum([has_target, has_benefit, has_diff])

if not h1:
    pts, verdict = 0, "critical"
    rationale = "Pas de H1 détecté dans le fold."
elif h1_count > 1 and signals == 0:
    # H1 multiples ET premier H1 vague = double pénalité
    pts, verdict = 0, "critical"
    rationale = f"H1 vague + anti-pattern SEO : {h1_count} H1 sur la page. Le premier H1 n'exprime aucun bénéfice."
elif h1_count > 1 and signals >= 2:
    # FIX V15.2: H1 multiples mais le premier est bon → noter en avertissement seulement
    pts, verdict = 1.5, "ok"
    rationale = f"H1 bien rédigé ({signals}/3 éléments) mais {h1_count} H1 sur la page — anti-pattern SEO à corriger (note tech séparée)."
elif h1_count > 1:
    pts, verdict = 1.5, "ok"
    rationale = f"H1 passable ({signals}/3 éléments) + {h1_count} H1 sur la page. Double faiblesse : message et structure."
elif signals >= 2 and 4 <= wc <= 14:
    pts, verdict = 3, "top"
    rationale = f"H1 contient {signals}/3 éléments (target={has_target}, benefit={has_benefit}, diff={has_diff}). Longueur {wc} mots."
elif signals >= 1:
    pts, verdict = 1.5, "ok"
    rationale = f"H1 contient {signals}/3 éléments (target={has_target}, benefit={has_benefit}, diff={has_diff}). Générique, remplaçable."
else:
    pts, verdict = 0, "critical"
    rationale = f"H1 vague, 0 élément détecté. Répond à 0-1 question sur 3."

results.append(score_entry("hero_01", "H1 = promesse spécifique", pts, verdict,
    {"h1": h1, "h1Count": h1_count, "wordCount": wc, "signals": signals,
     "hasTarget": has_target, "hasBenefit": has_benefit, "hasDifferentiator": has_diff}, rationale))

# ─────────────────────────────────────────────────────────────
# hero_02 — Sous-titre explicite qui complète le H1
# ─────────────────────────────────────────────────────────────
subtitle = (hero.get("subtitle") or "").strip()
sub_wc = len([w for w in re.split(r"\s+", subtitle) if w])

# Le subtitle est top si : <25 mots, contient au moins un de : méthode/cible/résultat/diff
adds_info_patterns = [
    r"en \d+\s*(min|jour|semaine|mois)",  # méthode
    r"\bpour les?\b", r"\bpour votre\b", r"\bpour mon\b",  # cible
    r"-?\d+\s*%", r"\bx\d+", r"\b\+?\d+\s*(x|fois)",  # résultat
    r"\bsans\b", r"\bgrâce à\b",  # différenciateur
    r"\brecommandé", r"\bvétérinaire", r"\bfabriqué", r"\bpersonnalis", r"\bsur[- ]mesure",
    r"\badapté", r"\bcréé avec",
]
adds_info = any(re.search(p, subtitle.lower()) for p in adds_info_patterns)
# Liste à puces détectée (le subtitle contient \n ou plusieurs infos)
has_puces = "\n" in subtitle or len(subtitle.split(".")) >= 3

# FIX V15.2: détecter quand le "subtitle" est en fait une barre de navigation
_sub_lines = [l.strip() for l in subtitle.split("\n") if l.strip()]
_nav_words = ["fermer", "découvrir", "voir tout", "tout voir", "e-shop", "shop",
              "newsletter", "collection", "blog", "contact", "panier", "cart", "menu"]
_is_nav_subtitle = (len(_sub_lines) >= 3 and
    all(len(l.split()) <= 4 for l in _sub_lines) and
    any(any(nw in l.lower() for nw in _nav_words) for l in _sub_lines))
_has_html_entities = "&#" in subtitle or "&nbsp;" in subtitle

if not subtitle:
    pts, verdict = 0, "critical"
    rationale = "Pas de sous-titre détecté."
elif _is_nav_subtitle or _has_html_entities:
    pts, verdict = 0, "critical"
    rationale = f"Le sous-titre détecté est une barre de navigation, pas un vrai sous-titre : '{subtitle[:60]}'."
elif sub_wc > 30:
    pts, verdict = 1.5, "ok"
    rationale = f"Sous-titre présent mais long ({sub_wc} mots, max recommandé 25)."
elif adds_info or has_puces:
    pts, verdict = 3, "top"
    rationale = f"Sous-titre ajoute de l'info ({sub_wc} mots). Puces={has_puces}, adds_info={adds_info}."
else:
    # Reformulation ou trop vague
    h1_words = set(h1_lower.split())
    sub_words = set(subtitle.lower().split())
    overlap = len(h1_words & sub_words) / max(1, len(sub_words))
    if overlap > 0.4:
        pts, verdict = 1.5, "ok"
        rationale = f"Sous-titre reformule le H1 (overlap {int(overlap*100)}%)."
    else:
        pts, verdict = 1.5, "ok"
        rationale = "Sous-titre présent mais trop vague, n'ajoute pas d'info claire."

results.append(score_entry("hero_02", "Sous-titre explicite", pts, verdict,
    {"subtitle": subtitle[:200], "wordCount": sub_wc, "hasBulletList": has_puces, "addsInfo": adds_info}, rationale))

# ─────────────────────────────────────────────────────────────
# hero_03 — CTA principal visible ATF (action + bénéfice)
# FIX V15.2: filtrer CTA fantômes avant scoring
# ─────────────────────────────────────────────────────────────
# Blacklist de textes CTA qui sont des artefacts de capture (cookie, nav, skip, etc.)
_CTA_BLACKLIST = [
    "fermer", "close", "aller au contenu", "aller au contenu principal",
    "skip to content", "skip to main", "accepter", "accept", "refuser",
    "en savoir plus sur l'utilisation des données", "cookie", "rgpd",
    "newsletter", "&nbsp;", "menu", "rechercher", "search", "panier", "cart",
    "se connecter", "me connecter", "mon compte", "log in", "sign in", "sign up",
]
def _is_phantom_cta(cta_dict):
    """Retourne True si le CTA est un artefact (cookie, nav, skip, 0x0)."""
    if not isinstance(cta_dict, dict):
        return True
    label = (cta_dict.get("label") or cta_dict.get("text") or "").strip().lower()
    # Texte blacklisté
    for bl in _CTA_BLACKLIST:
        if bl in label:
            return True
    # Href invalide
    href = (cta_dict.get("href") or "")
    if not href or href in ("#", "javascript:void(0)", "javascript:;"):
        # Exception: un bouton sans href peut être un JS handler valide
        # On le garde s'il a un label d'action valide
        action_words = ["découvr", "commenc", "essai", "commander", "acheter", "obtenir", "voir", "créer", "profiter"]
        if not any(w in label for w in action_words):
            return True
    return False

primary = hero.get("primaryCta")
# Si le primary est un fantôme, chercher le meilleur CTA dans la liste fold
if _is_phantom_cta(primary):
    _all_ctas = hero.get("ctas") or []
    _valid_ctas = [c for c in _all_ctas if not _is_phantom_cta(c)]
    if _valid_ctas:
        # Prendre celui avec le meilleur primaryScore
        _valid_ctas.sort(key=lambda c: c.get("primaryScore", 0) or 0, reverse=True)
        primary = _valid_ctas[0]
        print(f"  [FIX] CTA fantôme filtré, remplacé par: '{(primary.get('label') or '')[:50]}'")
    else:
        primary = None  # Aucun CTA valide trouvé

# Fix 2026-04-14 (audit Japhy+Oma Bug B) : Perception Layer 2 a réécrit `primaryCta`
# depuis component_perception sans reporter `primaryScore`/`primaryScoreReasons`.
# On enrichit depuis hero.ctas[] (native capture) en matchant par normalized_href.
def _enrich_primary_with_score(p, ctas):
    if not isinstance(p, dict) or not ctas:
        return p
    if p.get("primaryScore") is not None:
        return p
    p_href = p.get("normalized_href") or p.get("href")
    p_label = (p.get("label") or "").strip()
    if not p_href and not p_label:
        return p
    best = None
    for c in ctas:
        c_href = c.get("normalized_href") or c.get("href")
        c_label = (c.get("label") or "").strip()
        match = (p_href and c_href == p_href) or (p_label and c_label == p_label)
        if match and c.get("primaryScore") is not None:
            if best is None or c.get("primaryScore", 0) > best.get("primaryScore", 0):
                best = c
    if best:
        p = dict(p)  # don't mutate original
        p["primaryScore"] = best.get("primaryScore")
        p["primaryScoreReasons"] = best.get("primaryScoreReasons") or []
        # width/height from native bbox if missing
        if not p.get("width") and p.get("bbox"):
            p["width"] = p["bbox"].get("w", 0)
            p["height"] = p["bbox"].get("h", 0)
        p["contrastText"] = best.get("contrastText", p.get("contrastText", 1))
    return p

primary = _enrich_primary_with_score(primary, hero.get("ctas") or [])

if not primary:
    pts, verdict = 0, "critical"
    rationale = "Aucun CTA primaire détecté dans le fold."
else:
    label_cta = (primary.get("label") or "").strip()
    cta_wc = len([w for w in re.split(r"\s+", label_cta) if w])
    contrast_text = primary.get("contrastText", 1)
    primary_score = primary.get("primaryScore", 0)
    width = primary.get("width", 0)
    height = primary.get("height", 0)
    weak = re.match(r"^(en savoir plus|lire|learn more|read more|ok|submit|envoyer|valider|cliquez|cliquer|continuer)$", label_cta.lower())
    generic = re.match(r"^(continuer|continue|suivant|next)$", label_cta.lower())
    action_verb_match = "actionVerb+20" in (primary.get("primaryScoreReasons") or [])

    # Touch target
    touch_ok = width >= 44 and height >= 44
    # Contraste : on utilise contrastText (bouton vs son propre texte) comme proxy du "bouton coloré"
    # car contrastVsPage est cassé quand le parent est transparent
    contrast_ok = contrast_text >= 4.5

    if weak or generic:
        pts, verdict = 0, "critical"
        rationale = f"CTA texte creux: '{label_cta}'."
    elif cta_wc > 5:
        pts, verdict = 1.5, "ok"
        rationale = f"CTA trop long: '{label_cta}' ({cta_wc} mots, max 4)."
    elif action_verb_match and touch_ok and contrast_ok and cta_wc <= 4:
        pts, verdict = 3, "top"
        rationale = f"CTA '{label_cta}': verbe action + touch target OK ({width}×{height}) + contraste {contrast_text} + {cta_wc} mots."
    elif action_verb_match and touch_ok:
        pts, verdict = 3, "top"
        rationale = f"CTA '{label_cta}': verbe action + touch target OK ({width}×{height}). Contraste texte {contrast_text}."
    elif action_verb_match:
        pts, verdict = 1.5, "ok"
        rationale = f"CTA '{label_cta}': verbe action OK mais taille {width}×{height} sous 44px."
    else:
        pts, verdict = 1.5, "ok"
        rationale = f"CTA '{label_cta}': pas de verbe d'action clair."

results.append(score_entry("hero_03", "CTA principal visible ATF", pts, verdict,
    {"label": primary.get("label") if primary else None,
     "href": primary.get("href") if primary else None,
     "wordCount": cta_wc if primary else 0,
     "width": primary.get("width") if primary else 0,
     "height": primary.get("height") if primary else 0,
     "contrastText": primary.get("contrastText") if primary else 0,
     "primaryScore": primary.get("primaryScore") if primary else 0,
     "reasons": primary.get("primaryScoreReasons") if primary else []}, rationale))

# ─────────────────────────────────────────────────────────────
# hero_04 — Visuel hero pertinent (produit en usage)
# FIX V15.2: fallback sur spatial bbox si DOM <img> vide
# ─────────────────────────────────────────────────────────────
hero_imgs = hero.get("heroImages") or []
valid_imgs = [i for i in hero_imgs if i.get("width", 0) >= 400 and i.get("height", 0) >= 200]

# SPATIAL FALLBACK: si le DOM ne voit pas d'images mais le spatial détecte
# un hero_image_bbox significatif (>=80.000px²), un visuel existe
# (background-image CSS, video, canvas, lazy-loaded).
_sp_img_bbox = _sp_hero.get("sp_hero_image_bbox", {}) if _sp_hero else {}
_sp_img_ratio = _sp_hero.get("sp_hero_image_ratio", 0) if _sp_hero else 0
_sp_img_area = (_sp_img_bbox.get("w", 0) * _sp_img_bbox.get("h", 0)) if isinstance(_sp_img_bbox, dict) else 0
_visual_via_spatial = _sp_img_area >= 80000 or (isinstance(_sp_img_ratio, (int,float)) and _sp_img_ratio >= 0.10)

if valid_imgs:
    big = valid_imgs[0]
    alt = (big.get("alt") or "").lower()
    dim_ok = big.get("width", 0) >= 800
    alt_ok = len(alt) >= 10
    in_use_patterns = [r"\bmang", r"\butilis", r"\bporte", r"\bouvre", r"\bpréparation",
                       r"\bdans\b", r"\bsur\b", r"\btient", r"\bapplique", r"\bjoue",
                       r"\bécran", r"\binterface", r"\ben action"]
    in_use = any(re.search(p, alt) for p in in_use_patterns)
    product = bool(re.search(r"\b(produit|pack|bouteille|flacon|écran|croquette|tasse|vêtement|chat|chien)\b", alt))

    if in_use and product and dim_ok:
        pts, verdict = 3, "top"
        rationale = f"Visuel {big.get('width')}×{big.get('height')}, alt descriptif en usage: '{alt[:80]}'."
    elif (in_use or product) and dim_ok and alt_ok:
        pts, verdict = 3, "top"
        rationale = f"Visuel {big.get('width')}×{big.get('height')}, alt: '{alt[:80]}'. Produit ou contexte présent."
    elif dim_ok and alt_ok:
        pts, verdict = 1.5, "ok"
        rationale = f"Visuel présent {big.get('width')}×{big.get('height')} mais alt générique."
    else:
        pts, verdict = 1.5, "ok"
        rationale = f"Visuel {big.get('width')}×{big.get('height')}, alt: '{alt[:60]}'."
elif _visual_via_spatial:
    # Visuel détecté par screenshot spatial mais pas par DOM (background-image CSS, video, etc.)
    _w = _sp_img_bbox.get("w", 0) if isinstance(_sp_img_bbox, dict) else 0
    _h = _sp_img_bbox.get("h", 0) if isinstance(_sp_img_bbox, dict) else 0
    if _sp_img_ratio >= 0.30:
        pts, verdict = 1.5, "ok"
        rationale = f"Visuel détecté visuellement ({_w}×{_h}, ratio {_sp_img_ratio:.0%} de l'écran) mais pas en balise <img> — probablement CSS background-image. Qualité/pertinence non vérifiable sans alt-text."
    else:
        pts, verdict = 1.5, "ok"
        rationale = f"Visuel présent en arrière-plan ({_w}×{_h}, {_sp_img_area:,}px²) mais petit ou secondaire. Pas de balise <img> accessible."
else:
    pts, verdict = 0, "critical"
    rationale = "Aucun visuel hero détecté — ni en balise <img>, ni dans le screenshot spatial."

results.append(score_entry("hero_04", "Visuel hero pertinent", pts, verdict,
    {"heroImagesCount": len(hero_imgs), "validImagesCount": len(valid_imgs),
     "mainImage": valid_imgs[0] if valid_imgs else None,
     "spatialVisualDetected": _visual_via_spatial,
     "spatialImgArea": _sp_img_area,
     "spatialImgRatio": _sp_img_ratio}, rationale))

# ─────────────────────────────────────────────────────────────
# hero_05 — Preuve sociale dans le fold 1
# FIX V15.2: cross-check avec sp_social_proof_in_fold
# ─────────────────────────────────────────────────────────────
sp = hero.get("socialProofInFold", {}) or {}
trust_widgets = (social or {}).get("trustWidgets") or []
review_counts = (social or {}).get("reviewCounts") or []

present = sp.get("present", False)
sp_type = sp.get("type")
snippet = sp.get("snippet", "")

# Crédibilité : si on a des chiffres réels ET un widget identifié
has_widget = len(trust_widgets) > 0 or sp_type in ("trustpilot_widget", "judgeme_widget")
has_numbers = bool(review_counts) or bool(re.search(r"\d[\d\s]{2,}", snippet)) or bool(re.search(r"\d[.,]\d\s*/\s*5", snippet))

# SPATIAL CROSS-CHECK: le spatial sait si la preuve sociale est réellement
# visible au-dessus du fold (screenshot analysis). Si sp_social_proof_in_fold=False,
# la preuve existe peut-être dans le DOM mais pas dans le fold visible.
_sp_in_fold = _sp_hero.get("sp_social_proof_in_fold", None) if _sp_hero else None
_actually_in_fold = _sp_in_fold is True or _sp_in_fold is None  # None = pas de data spatial, on fait confiance au DOM

if present and has_widget and has_numbers and _actually_in_fold:
    pts, verdict = 3, "top"
    rc_texts = [r.get("text", str(r)) if isinstance(r, dict) else str(r) for r in review_counts[:2]]
    rationale = f"Preuve sociale crédible visible sans scroller : {sp_type} + chiffres ({', '.join(rc_texts) if rc_texts else snippet})."
elif present and (has_widget or has_numbers) and _actually_in_fold:
    pts, verdict = 3, "top"
    rationale = f"Preuve sociale visible : type={sp_type}, widgets={len(trust_widgets)}, chiffres={review_counts[:2]}."
elif present and (has_widget or has_numbers) and not _actually_in_fold:
    # Preuve existe mais PAS dans le fold visible — score réduit
    pts, verdict = 1.5, "ok"
    rc_texts = [r.get("text", str(r)) if isinstance(r, dict) else str(r) for r in review_counts[:2]]
    rationale = f"Preuve sociale détectée ({sp_type}, {', '.join(rc_texts)}) mais NON visible sans scroller — le visiteur ne la voit pas au premier regard."
elif present and not _actually_in_fold:
    pts, verdict = 0, "critical"
    rationale = f"Signal de preuve sociale ({sp_type or 'mention vague'}) enfoui sous le fold. Non visible au chargement."
elif present:
    pts, verdict = 1.5, "ok"
    rationale = f"Signal faible: {sp_type or 'mention vague'}, sans widget ni chiffre vérifiable."
else:
    pts, verdict = 0, "critical"
    rationale = "Aucune preuve sociale détectée dans le fold."

results.append(score_entry("hero_05", "Preuve sociale ATF", pts, verdict,
    {"present": present, "type": sp_type, "snippet": snippet,
     "trustWidgets": trust_widgets, "reviewCounts": review_counts,
     "spatialInFold": _sp_in_fold}, rationale))

# ─────────────────────────────────────────────────────────────
# hero_06 — Test 5s + ratio 1:1 (KILLER)
# ─────────────────────────────────────────────────────────────
# 3 questions: Quoi (H1) / Pour qui (H1 ou subtitle target) / Quoi faire (CTA)
q_quoi = bool(h1 and len(h1) > 4)
q_pour_qui = has_target or any(re.search(p, (subtitle or "").lower()) for p in target_patterns)
q_action = bool(primary and primary.get("label"))
questions_answered = sum([q_quoi, q_pour_qui, q_action])

# Ratio 1:1 : le primaire doit avoir un score très supérieur au secondaire
fold_ctas = hero.get("ctas") or []
# Fix 2026-04-14 Bug B : force int, None→0 (primaryCta peut venir de Perception sans primaryScore)
primary_score = (primary or {}).get("primaryScore") if primary else 0
primary_score = primary_score if isinstance(primary_score, (int, float)) else 0
# Dédupliquer par href : un même CTA répété (sticky header + hero) n'est pas un conflit
primary_href = (primary or {}).get("href")
deduped = []
seen_hrefs = set()
if primary_href:
    seen_hrefs.add(primary_href)
for c in fold_ctas:
    h = c.get("href")
    if h and h in seen_hrefs:
        continue
    if h:
        seen_hrefs.add(h)
    deduped.append(c)
secondary = deduped[0] if deduped else None
secondary_score = (secondary or {}).get("primaryScore") if secondary else 0
secondary_score = secondary_score if isinstance(secondary_score, (int, float)) else 0
# Si deux CTAs ont ≥ 40 et la diff < 15, c'est un conflit
has_focus = primary_score >= 40 and (secondary_score == 0 or (primary_score - secondary_score) >= 15)

# Distractions : cookie banner covers hero, chat widgets, promo banner
cookie = overlays.get("cookieBanner") or {}
distractions = 0
dist_notes = []
if cookie.get("present") and cookie.get("coversHero"):
    distractions += 1; dist_notes.append("cookie_covers_hero")
if cookie.get("present") and cookie.get("coveragePct", 0) > 20:
    distractions += 1; dist_notes.append(f"cookie_coverage_{cookie.get('coveragePct')}%")
if cookie.get("present") and cookie.get("competingCtas") and len(cookie.get("competingCtas", [])) >= 2:
    distractions += 1; dist_notes.append("cookie_adds_competing_ctas")
if len(overlays.get("chatWidgets", [])) > 0:
    dist_notes.append("chat_widget")  # pas comptant comme distraction si juste launcher
# Bannière promo dans le fold (détectée comme CTA fullWidth avec promo)
for c in fold_ctas[:3]:
    reasons = c.get("primaryScoreReasons") or []
    if "promo×0.3" in reasons and c.get("width", 0) > 800:
        distractions += 1; dist_notes.append("promo_banner_fullwidth")
        break

# FIX V15.2: reconcilier avec le score spatial 5 secondes
_sp_5s = _sp_hero.get("sp_five_second_spatial_score", None) if _sp_hero else None
_sp_5s_boost = isinstance(_sp_5s, (int, float)) and _sp_5s >= 0.8  # spatial dit "page claire en 5s"

if questions_answered == 3 and has_focus and distractions == 0:
    pts, verdict = 3, "top"
    rationale = "3/3 questions répondues, CTA focus clair, 0 distraction."
elif questions_answered == 3 and has_focus and distractions <= 1:
    pts, verdict = 1.5, "ok"
    rationale = f"3/3 questions + focus OK mais {distractions} distraction mineure: {dist_notes}."
elif questions_answered >= 2 and has_focus and distractions <= 2:
    pts, verdict = 1.5, "ok"
    rationale = f"{questions_answered}/3 questions, focus OK, {distractions} distraction(s): {dist_notes}."
elif _sp_5s_boost and questions_answered >= 2:
    # FIX: le spatial dit la page est claire, le textuel n'est pas loin → 1.5 minimum
    pts, verdict = 1.5, "ok"
    rationale = f"Score spatial 5s élevé ({_sp_5s:.2f}) et {questions_answered}/3 questions. Page visuellement claire malgré focus CTA imparfait."
elif _sp_5s_boost:
    # Spatial clair mais texte trop faible → 1.5 (pas 0)
    pts, verdict = 1.5, "ok"
    rationale = f"Score spatial 5s élevé ({_sp_5s:.2f}) : la page est visuellement claire au chargement, mais seulement {questions_answered}/3 questions textuelles détectées."
else:
    pts, verdict = 0, "critical"
    rationale = f"Test 5s échoué : {questions_answered}/3 questions, focus CTA={has_focus}, distractions={dist_notes}."

# KILLER: si test 5s échoué (< 2) ET ratio cassé, plafond 6/18
killer_triggered = (questions_answered < 2) and (not has_focus)

results.append(score_entry("hero_06", "Test 5s + ratio 1:1", pts, verdict,
    {"questionsAnswered": questions_answered,
     "q_quoi": q_quoi, "q_pour_qui": q_pour_qui, "q_action": q_action,
     "hasFocus": has_focus,
     "primaryScore": primary_score, "secondaryScore": secondary_score,
     "distractions": dist_notes,
     "killerTriggered": killer_triggered}, rationale))

# ─────────────────────────────────────────────────────────────
# Filtrage par pageType + Totaux
# ─────────────────────────────────────────────────────────────
# Séparer critères actifs et exclus
active_results = []
skipped_results = []
for r in results:
    if is_criterion_applicable(r["id"], PAGE_TYPE):
        r["applicable"] = True
        active_results.append(r)
    else:
        r["applicable"] = False
        r["score"] = 0  # pas compté
        r["verdict"] = "skipped"
        r["rationale"] = f"Critère non applicable pour pageType={PAGE_TYPE}"
        skipped_results.append(r)

raw_total = sum(r["score"] for r in active_results)
active_max = len(active_results) * 3  # max dynamique

if killer_triggered and "hero_06" in [r["id"] for r in active_results]:
    killer_cap = int(active_max / 3)  # plafond = 1/3 du max actif
    final_total = min(raw_total, killer_cap)
    killer_note = f"KILLER hero_06 déclenché: plafond {killer_cap}/{active_max} (raw={raw_total})"
elif killer_triggered:
    final_total = raw_total  # hero_06 n'est pas actif, pas de killer
    killer_triggered = False
    killer_note = None
else:
    final_total = raw_total
    killer_note = None

# Score normalisé /100
score_100 = round((final_total / active_max) * 100, 1) if active_max > 0 else 0

# ─── Perception Layer 2 : évidence + override hero_01 si pas de hero détecté ───
_perception_block = {"available": False}
if _HAS_PERCEPTION:
    _p = load_perception(LABEL, PAGE_TYPE, ROOT)
    _sig = perception_signals(_p)
    _perception_block = {
        "available": _sig.get("pc_available", False),
        "signals": _sig,
    }
    # Doctrine : hero_01 (H1 promesse) doit avoir un hero_band visible.
    # Si aucun hero_band détecté → note d'alerte (pas d'override destructif).
    if _sig.get("pc_available") and not _sig.get("pc_has_hero"):
        for r in results:
            if r["id"] == "hero_01" and r.get("verdict") not in ("skipped",):
                r.setdefault("perception_note", "Aucun hero_band détecté par Layer 2 Perception — à challenger visuellement")
    # Bonus evidence : hero_05 (preuve sociale) enrichi si social_proof_logos détecté
    for r in results:
        if r["id"] == "hero_05":
            r.setdefault("perception_has_social_proof", _sig.get("pc_has_social_proof", False))

output = {
    "label": LABEL,
    "pageType": PAGE_TYPE,
    "url": meta.get("url"),
    "pillar": "hero",
    "max": active_max,
    "maxFull": 18,
    "rawTotal": raw_total,
    "finalTotal": final_total,
    "score100": score_100,
    "killerTriggered": killer_triggered,
    "killerNote": killer_note,
    "activeCriteria": len(active_results),
    "skippedCriteria": [r["id"] for r in skipped_results],
    "criteria": results,
    "gridVersion": grid.get("version"),
    "capturedAt": meta.get("capturedAt"),
    "_perception": _perception_block,
}
OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))

# ─────────────────────────────────────────────────────────────
# Console summary
# ─────────────────────────────────────────────────────────────
print(f"\n━━━ Hero V3 Scoring — {LABEL} [{PAGE_TYPE}] ━━━")
print(f"URL: {meta.get('url')}")
print(f"{'Critère':<12} {'Score':>8}  Verdict")
print("─" * 60)
for r in results:
    status = " [SKIP]" if not r.get("applicable", True) else ""
    print(f"{r['id']:<12} {r['score']:>3}/{r['max']}   {r['verdict']:<9}  {r['label'][:40]}{status}")
    if r.get("applicable", True):
        print(f"             → {r['rationale'][:90]}")
print("─" * 60)
print(f"{'TOTAL':<12} {final_total:>3}/{active_max}   ({score_100}/100)  (raw={raw_total}{', KILLER' if killer_triggered else ''})")
if skipped_results:
    print(f"  Critères exclus ({PAGE_TYPE}): {', '.join(r['id'] for r in skipped_results)}")
print(f"\nOutput: {OUT}")
