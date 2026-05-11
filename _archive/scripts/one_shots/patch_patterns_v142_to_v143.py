#!/usr/bin/env python3
"""
patch_patterns_v142_to_v143.py — V14.2.3 tightening pass.

Input:  skills/cro-library/references/patterns.json (v14.2.2)
Output: skills/cro-library/references/patterns.json (v14.2.3) + backup

What it does:
  1. Adds 3 cross-cutting fields to ALL patterns:
       - operator_mode.{internal_agency,saas_autonomous}
       - regulatory_flag (only on high-risk patterns)
       - expected_review_date (6 months out — 2026-10-16)
  2. Applies pattern-specific tightenings on the 11 flagged doctrinal patterns
     + a handful of the most strategic non-flagged patterns where Mathis' validation
       implies the same tightening logic (blacklists, VPC proof_type, etc).
  3. Bumps _meta.version → 14.2.3, adds harmo_history entry.

Run from project root:
  python3 scripts/patch_patterns_v142_to_v143.py
"""
from __future__ import annotations
import json, shutil, copy, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS_PATH = ROOT / "skills" / "cro-library" / "references" / "patterns.json"

REVIEW_DATE = "2026-10-16"  # 6 months after 2026-04-16 lock

# ────────────────────────────────────────────────────────────────────────
# CROSS-CUTTING ADDITIONS (apply to every pattern)
# ────────────────────────────────────────────────────────────────────────

DEFAULT_OPERATOR_MODE = {
    "internal_agency": {
        "policy": "permissive",
        "note": "opérateur GS juge nuance et vérifie manuellement les preuves côté client"
    },
    "saas_autonomous": {
        "policy": "fail_closed",
        "note": "si champ preuve manquant dans clients_database → pattern désactivé ou reformulé sans claim"
    }
}

# Patterns où l'enjeu juridique/éthique est élevé (DGCCRF, FTC, loyauté pub)
REGULATORY_RISK_PATTERN_IDS = {
    "pat_psy_02__doctrinal__001": {  # scarcity
        "dgccrf_risk": "high",
        "ftc_risk": "high",
        "legal_basis_fr": "Art L.121-1 Code Conso — pratiques commerciales trompeuses",
        "note": "Fausse scarcity = amende DGCCRF jusqu'à 300k€. Exige scarcity_proof_type vérifiable.",
    },
    "pat_psy_04__doctrinal__001": {  # loss aversion
        "dgccrf_risk": "medium",
        "ftc_risk": "medium",
        "legal_basis_fr": "Art L.121-1 + L.121-4 — exploitation vulnérabilité",
        "note": "Framing de perte interdit dans 8 secteurs (santé/fintech/psy/pharma/legal/kids/parenting/addiction).",
    },
    "pat_psy_05__doctrinal__001": {  # authority
        "dgccrf_risk": "high",
        "ftc_risk": "high",
        "legal_basis_fr": "Art L.121-4 — allégations d'appartenance/certification fausses",
        "note": "Faux signaux d'autorité détectables en <2min (reverse image, LinkedIn search). Zéro tolérance.",
    },
    "pat_psy_08__doctrinal__001": {  # VoC
        "dgccrf_risk": "medium",
        "ftc_risk": "high",
        "legal_basis_fr": "Art L.121-1 — faux témoignages",
        "note": "FTC Guides Concerning Endorsements — disclosure obligatoire si lien financier entre témoin et marque.",
    },
    "pat_coh_03__doctrinal__001": {  # scent / ad-LP truth
        "dgccrf_risk": "medium",
        "ftc_risk": "low",
        "legal_basis_fr": "Art L.121-1 — rupture promesse ad/page = tromperie potentielle",
        "note": "Si offre ad ≠ offre LP affichée, faux publicitaire au sens CPC.",
    },
    "pat_coh_04__doctrinal__001": {  # positioning claims
        "dgccrf_risk": "medium",
        "ftc_risk": "medium",
        "legal_basis_fr": "Art L.121-2 — superlatifs et comparatifs trompeurs",
        "note": "Chaque claim de différenciation requiert proof_type (certification/patent/publication/etc).",
    },
    "pat_coh_09__doctrinal__001": {  # unique mechanism
        "dgccrf_risk": "low",
        "ftc_risk": "low",
        "legal_basis_fr": "Art L.121-2 — si mécanisme invente une capacité inexistante",
        "note": "Mécanisme narratif toléré ssi container sémantique cohérent avec réalité produit.",
    },
}

# ────────────────────────────────────────────────────────────────────────
# PATTERN-SPECIFIC TIGHTENINGS
# ────────────────────────────────────────────────────────────────────────

def _as_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        return [x]
    return []

def _add_do(pattern, items):
    rule = pattern.setdefault("rule", {})
    do = _as_list(rule.get("do", []))
    for item in items:
        if item not in do:
            do.append(item)
    rule["do"] = do

def _add_dont(pattern, items):
    rule = pattern.setdefault("rule", {})
    dont = _as_list(rule.get("dont", []))
    for item in items:
        if item not in dont:
            dont.append(item)
    rule["dont"] = dont

def _set_operator_mode(pattern, internal_note=None, saas_note=None):
    om = copy.deepcopy(DEFAULT_OPERATOR_MODE)
    if internal_note:
        om["internal_agency"]["note"] = internal_note
    if saas_note:
        om["saas_autonomous"]["note"] = saas_note
    pattern["operator_mode"] = om


# ========== PSY_02 — Scarcity ==========
def patch_psy_02(p):
    _add_do(p, [
        "Champ obligatoire dans clients_database : scarcity_proof_type ∈ [inventory_db_linked | batch_fixed_documented | waitlist_public | agenda_capacity_documented | none]. En mode saas_autonomous, si none → pattern refuse toute mention de scarcity (fail-closed).",
        "Segmentation par business_category : (a) DTC physique = inventory_db_linked requis, (b) SaaS/services digitaux = waitlist_public ou cohort_public, (c) services humains = agenda_capacity_documented. Pas de scarcity sans un de ces trois.",
        "Si scarcity marketing-driven (batch 500 unités par choix délibéré) : obligatoire batch_fixed_documented avec date de production + date limite de commercialisation publiques sur la page."
    ])
    _add_dont(p, [
        "Jamais scarcity sans mécanisme de plafonnement lisible publiquement — le 'plafonnement réel' n'est crédible que s'il est vérifiable par un tiers."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur vérifie inventaire DB ou documentation batch manuellement avant publication",
        saas_note="SaaS exige scarcity_proof_type ≠ none ; si none → section scarcity supprimée automatiquement, basculer sur psy_04 (risk reversal positif)"
    )

# ========== PSY_04 — Loss aversion / Risk reversal ==========
def patch_psy_04(p):
    _add_do(p, [
        "Désactivation obligatoire du framing de perte (pas du risk reversal) dans 8 secteurs : santé, fintech, psy/mental, pharma, legal, kids/parenting, addiction (fitness extrême, détox, crypto, trading). Dans ces secteurs, UNIQUEMENT risk reversal positif.",
        "loss_framing requiert champ clients_database.loss_framing_opt_in=true explicite — défaut OFF universellement. Même en mode internal_agency, l'opt-in doit être signé par le client.",
        "Risk Reversal (garantie/retour/essai) toujours ON toutes catégories — c'est le levier positif de réduction de risque perçu, pas de déclencheur d'anxiété."
    ])
    _add_dont(p, [
        "Jamais framing de perte dans santé/fintech/psy/pharma/legal/kids/parenting/addiction — interdit même si client insiste. Éthique absolue, non négociable.",
        "Jamais framing 'vous passez à côté de X' quand X est une transformation de santé, richesse ou identité — hors cadre sectoriel blacklisté même."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur juge pertinence framing, peut l'activer si sector NOT IN blacklist ET client explicite",
        saas_note="Framing ne peut s'activer que si loss_framing_opt_in=true ET business_category NOT IN {health,fintech,mental,pharma,legal,kids,parenting,addiction}. Risk reversal toujours actif."
    )

# ========== PSY_05 — Authority ==========
def patch_psy_05(p):
    _add_do(p, [
        "Mode seuil adaptatif ≥1 signal (DTC founder-centric) autorisé SSI les 5 critères mesurables sont tous vrais dans clients_database : (1) founder_named = prénom + nom complet, (2) founder_bio_words ≥ 60, (3) founder_photo_real = true (not stock, reverse image check passed), (4) founder_linkedin_url public et actif, (5) company_age_years < 3 OR company_revenue_m_eur < 5. Sinon fallback seuil strict ≥3.",
        "Pour SaaS B2B et enterprise — seuil strict ≥3 TOUJOURS, quel que soit l'âge de la boîte. Le 'founder-centric' ne s'applique pas au B2B."
    ])
    _add_dont(p, [
        "Jamais tolérer ≥1 signal sans vérification complète des 5 critères mesurables — 'founder-centric' n'est pas un échappatoire au seuil strict.",
        "Jamais tolérer ≥1 signal pour B2B SaaS ou enterprise, même si fondateur nommé — le contexte de décision B2B exige plusieurs couches d'autorité."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur vérifie founder_photo_real par reverse image + LinkedIn search manuellement",
        saas_note="SaaS requiert les 5 champs explicites dans clients_database. Si founder_photo_real non vérifiable automatiquement → fallback ≥3."
    )

# ========== PSY_08 — Voice of Customer ==========
def patch_psy_08(p):
    _add_do(p, [
        "Règle anonymisation : autorisé 'Prénom + initiale + rôle/contexte' (ex : 'Marie L., avocate en droit social, cliente depuis 2 ans'). Interdit 'J.M., satisfait' ou initiales seules sans contexte — signal de fraude vague.",
        "Règle imperfection rate : sur ≥3 verbatims affichés, AU MOINS 1 doit contenir une tournure imparfaite intentionnellement préservée (phrase elliptique, mot argotique, syntaxe orale brute). Baymard 2023 : signal d'authenticité détectable par 75% des users en 6s.",
        "Lissage autorisé strictement limité à : correction orthographique + ponctuation pour lisibilité. Interdit toute reformulation sémantique, même mineure ('c'est ouf' reste 'c'est ouf', pas 'c'est excellent').",
        "Champ obligatoire clients_database.voc_verbatims[] : chaque entry = {source_url, capture_date, customer_consent_level ∈ [named_public|initial_only|anonymous], original_text, cleaned_text, imperfection_preserved}."
    ])
    _add_dont(p, [
        "Jamais verbatims tous en français littéraire impeccable — signal de fabrication détectable.",
        "Jamais reformulation marketing même 'pour aider le lecteur' — casse la voix = casse la crédibilité entière du bloc VoC."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur collecte verbatims depuis reviews/calls/support + valide consent client manuellement",
        saas_note="SaaS requiert voc_verbatims[] rempli par client avec source_url vérifiable et consent_level explicite. Sans source_url → rejet automatique."
    )

# ========== PER_07 — Archetypes ==========
def patch_per_07(p):
    _add_do(p, [
        "Mapping doctrinal 12 archétypes Mark & Pearson → 5 macro-buckets pour décision Oracle : (1) Sage/Ruler → B2B pro, health, legal, finance, enterprise ; (2) Hero/Outlaw → fitness, SaaS indie, startups disruptives, defi/crypto ; (3) Lover/Creator → DTC beauté, mode, food premium, décoration ; (4) Jester/Everyman → DTC mass, consumer goods, food accessible ; (5) Caregiver/Innocent → parenting, wellness doux, éducation, petite enfance.",
        "Champ clients_database.archetype_macro enum 5 valeurs [sage_ruler|hero_outlaw|lover_creator|jester_everyman|caregiver_innocent] — obligatoire pour que l'Oracle choisisse ton/lexique/rythme.",
        "Les 12 archétypes originaux restent accessibles comme métadonnée fine (archetype_fine) pour cas particuliers où la nuance compte (ex: Explorer vs Outlaw dans startup)."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur peut choisir archétype fin parmi les 12 pour nuance éditoriale",
        saas_note="SaaS restreint à 5 macro-buckets pour décision déterministe ; archetype_fine non exposé en UI client"
    )

# ========== PER_08 — Blacklist ==========
def patch_per_08(p):
    _add_do(p, [
        "Blacklist étendue par catégorie (Oracle tag chaque flag pour reco de remplacement ciblée) :",
        "• Consulting/B2B cliché : 'sur-mesure' (quand faux), 'clé en main', 'écosystème', 'valeur ajoutée', 'accompagnement personnalisé', 'à vos côtés', 'partenaire de confiance', 'expertise reconnue', 'savoir-faire unique', 'ensemble construisons', 'pensé pour vous', 'à l'écoute de vos besoins', 'solutions adaptées'.",
        "• DTC lifestyle cliché : 'curé à la main', 'notre aventure', 'passionnés', 'l'humain au cœur', 'inspirer votre quotidien', 'à taille humaine', 'fait avec amour', 'Made with love', 'home sweet home', 'nos petits plus', 'produits d'exception', 'avec soin', 'notre histoire'.",
        "• Greenwashing vague : 'engagé' (sans preuve), 'durable' (sans certif), 'éco-responsable' (sans bilan carbone), 'respectueux' (sans cadre), 'naturel' (sans composition détaillée), 'vert' (sans éco-label), 'bio-inspiré' (sans source).",
        "• AI-generic 2024-2026 : 'leverage', 'unlock potential', 'transformative', 'holistic', 'tailored', 'paradigm shift', 'cutting-edge', 'next-generation', 'in a landscape where', 'empower', 'streamline', 'seamless', 'delve into', 'navigate the complexities'.",
        "Pour chaque terme blacklisté détecté, Oracle émet reco catégorisée par 'category_risk' (consulting_cliché | dtc_cliché | greenwashing | ai_generic) + suggestion de remplacement concret-vérifiable basé sur la feature/preuve correspondante."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur peut tolérer un terme blacklisté si contexte l'exige (ex: citation directe d'un client) avec commentaire",
        saas_note="SaaS applique blacklist stricte ; si terme détecté → reco obligatoire de reformulation, pas de tolérance"
    )

# ========== PER_11 — Benefit Laddering ==========
def patch_per_11(p):
    _add_do(p, [
        "Logique Reynolds & Gutman à 4 niveaux EN INTERNE (Attribute → Functional → Emotional → Identity), mais OUTPUT restreint à 2 niveaux pour éviter dilution.",
        "Mapping Schwartz 5 Stages of Awareness → choix des 2 niveaux output : Stage 1 (unaware) = Functional + Emotional ; Stage 2 (pain-aware) = Functional + Emotional ; Stage 3 (solution-aware) = Functional + Emotional ; Stage 4 (product-aware) = Emotional + Identity ; Stage 5 (most aware) = Identity dominant + RTBs forts (ratios, awards, brevet).",
        "Champ clients_database.audience_awareness_stage enum [1,2,3,4,5] — défauts proposés : 2 pour DTC consumer, 3 pour SaaS B2B mainstream, 4 pour luxury/premium, 5 pour enterprise/niche expertise."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur peut override stage selon persona réel (ex: DTC mais audience déjà product-aware)",
        saas_note="SaaS utilise défauts par business_category sauf override explicite client"
    )

# ========== COH_03 — Scent matching ==========
def patch_coh_03(p):
    _add_do(p, [
        "Opérationnalisation mesurable (Oracle calcule automatiquement depuis ad_copy_source + hero_lp) :",
        "• keyword_overlap_ad_lp_hero ≥ 0.6 (Jaccard sur ngrams 1-3, FR stopwords retirés)",
        "• semantic_similarity_cosine ≥ 0.7 (embedding FR type sentence-camembert-large ou multilingual-mpnet)",
        "• dominant_color_cosine_ad_hero ≥ 0.7 (extraction 3 couleurs dominantes via ColorThief, cosine RGB)",
        "• offer_amount_match = true ssi promo ad chiffrée (-X% ou Xeuro) et même valeur visible dans hero_lp fold 1",
        "• persona_mention_match = true ssi ad persona-explicit ('pour les avocats') et persona cité dans h1 ou subtitle hero_lp",
        "Règle globale : si 3/5 critères OK → scent OK. Sinon → pattern émet reco de rupture + suggestion de patch (quel élément manque).",
        "Match sémantique fort tolère reformulation créative du H1 — interdiction maintenue sur perte totale des keywords de promesse ou changement de l'offre."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur peut ajuster seuils selon cas (ex: ad très visuelle vs LP très copy = dominant_color moins critique)",
        saas_note="SaaS applique les 5 seuils automatiquement, sans override. Rapport scent_score publié dans audit."
    )

# ========== COH_04 — VPC + Dunford ==========
def patch_coh_04(p):
    _add_do(p, [
        "Couche stratégique April Dunford complémentaire au VPC Osterwalder tactique :",
        "• VPC (Osterwalder) → fit produit/client : Jobs, Pains, Gains mappés sur Pain Relievers + Gain Creators",
        "• Dunford → positioning statement final à 5 composantes : (1) alternatives concrètes (pas 'faire soi-même' mais catégories ou produits comparables), (2) unique attributes (ce que vous seul avez, vérifiable), (3) value (ce que ces attributes permettent pour le client), (4) who-for (persona précis avec critères démographiques/comportementaux), (5) market frame (catégorie que vous choisissez d'habiter).",
        "Chaque claim de différenciation exige champ clients_database.differentiator_claims[].proof_type ∈ [certification | patent | publication | exclusive_contract | first_mover_date | customer_proof_doc | regulatory_approval | none]. Si proof_type = none → pattern force reformulation sans claim unique (bascule sur bénéfice fonctionnel générique)."
    ])
    _add_dont(p, [
        "Jamais affirmer différenciation sans proof_type vérifiable — signal de LP marketing-bullshit détectable par clients sophistiqués."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur peut accepter customer_proof_doc sur simple témoignage si lien explicite vérifiable",
        saas_note="SaaS requiert proof_type ≠ none pour TOUTE affirmation 'unique/seul/premier' ; sinon pattern force reformulation"
    )

# ========== COH_05 — Voice & Tone 4D ==========
def patch_coh_05(p):
    _add_do(p, [
        "Grille V&T 4 axes avec ancres verbales concrètes par position (5 positions × 4 axes = 20 ancres déterministes) :",
        "",
        "• AXE FORMEL↔FAMILIER",
        "  - 0-20% (très familier) : tutoiement systématique, argot métier toléré, phrases elliptiques, contractions autorisées",
        "  - 20-40% (familier) : tutoiement, pas d'argot, phrases complètes",
        "  - 40-60% (neutre) : mélange tu/vous selon contexte, syntaxe simple",
        "  - 60-80% (formel) : vouvoiement quasi-systématique, pas d'argot, syntaxe académique",
        "  - 80-100% (très formel) : vouvoiement strict, syntaxe académique, pas de contraction",
        "",
        "• AXE EXPERT↔ACCESSIBLE",
        "  - 0-20% (très expert) : vocabulaire métier pointu sans vulgarisation, abréviations métier",
        "  - 20-40% (expert) : termes métier avec rares explications",
        "  - 40-60% (neutre) : termes métier expliqués lors de la 1re occurrence",
        "  - 60-80% (accessible) : vocabulaire grand public avec rares termes métier contextualisés",
        "  - 80-100% (très accessible) : zero jargon, analogies du quotidien, explications imagées",
        "",
        "• AXE SÉRIEUX↔LÉGER",
        "  - 0-20% (très sérieux) : ton factuel, zéro humour, pas d'émoji, pas d'exclamation",
        "  - 20-40% (sérieux) : factuel mais chaleureux ponctuellement",
        "  - 40-60% (neutre) : sérieux chaleureux, humour léger très occasionnel",
        "  - 60-80% (léger) : humour sobre assumé, quelques émoji dans CTA/FAQ",
        "  - 80-100% (très léger) : humour décomplexé, références pop culture, émoji récurrents",
        "",
        "• AXE DIRECT↔NUANCÉ",
        "  - 0-20% (très direct) : affirmations tranchées, phrases courtes, pas de qualificateur",
        "  - 20-40% (direct) : affirmations avec preuves immédiates, peu de nuances",
        "  - 40-60% (neutre) : affirmations nuancées selon l'enjeu",
        "  - 60-80% (nuancé) : formulations prudentes, 'il est possible que', qualificateurs",
        "  - 80-100% (très nuancé) : pluralité des lectures, 'selon les cas', prudence assumée",
        "",
        "Champ clients_database.voice_tone_4d = {formel: int 0-100, expert: int 0-100, serieux: int 0-100, direct: int 0-100} — obligatoire pour que l'Oracle choisisse le registre exact de rédaction.",
        "Test cohérence : prendre 5 snippets copy LP au hasard → lecteur tiers doit identifier qu'ils viennent de la même marque avec ≤1 hésitation."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur calibre voice_tone_4d par interview brand de 30min avec client",
        saas_note="SaaS propose wizard 8 questions binaires → calcul voice_tone_4d automatique ; client peut réviser via sliders"
    )

# ========== COH_09 — Unique Mechanism ==========
def patch_coh_09(p):
    _add_do(p, [
        "Safety rail érosion narrative : si business_category = commoditized_high (cross-ref clients_database.competitive_intensity ∈ [high,very_high] ET market_saturation ∈ [saturated,hyper_saturated]), Oracle bascule prioritairement sur coh_04 (VPC + Dunford clarity) plutôt que fabriquer mécanisme narratif. Stack coh_04 + coh_09 autorisé seulement si VPC déjà solide avec proof_type vérifiable.",
        "Validation opérationnelle mécanisme : le client doit répondre EN UNE PHRASE VÉRIFIABLE à la question 'En quoi votre process produit un résultat différent de la concurrence ?'. Si réponse vague ou générique → pas de mécanisme, basculer sur coh_04.",
        "Mécanisme narratif valide (Schwartz-style) ssi : (a) container sémantique en 2-4 mots cohérent avec la réalité produit, (b) phrase explicative 12-20 mots fact-based, (c) réutilisé ≥3 fois sur la page (pas un one-shot marketing)."
    ])
    _add_dont(p, [
        "Jamais fabriquer mécanisme pour compenser absence de vrai différenciant — signal de LP creuse détectable sous copy poli.",
        "Jamais inventer capacité produit inexistante pour soutenir un nom de mécanisme (ex: 'Protocole Clear-Start' si aucun protocole réel côté produit) — passage direct en coh_04 forcé."
    ])
    _set_operator_mode(p,
        internal_note="GS opérateur juge si le mécanisme narratif est soutenable factuellement ; peut accepter narratif pur si container sémantique fort",
        saas_note="SaaS exige champ unique_mechanism_validation avec réponse client à la question test ; si vide ou vague → bascule coh_04"
    )

# ────────────────────────────────────────────────────────────────────────
# REGISTRY
# ────────────────────────────────────────────────────────────────────────

PATCH_REGISTRY = {
    "pat_psy_02__doctrinal__001": patch_psy_02,
    "pat_psy_04__doctrinal__001": patch_psy_04,
    "pat_psy_05__doctrinal__001": patch_psy_05,
    "pat_psy_08__doctrinal__001": patch_psy_08,
    "pat_per_07__doctrinal__001": patch_per_07,
    "pat_per_08__doctrinal__001": patch_per_08,
    "pat_per_11__doctrinal__001": patch_per_11,
    "pat_coh_03__doctrinal__001": patch_coh_03,
    "pat_coh_04__doctrinal__001": patch_coh_04,
    "pat_coh_05__doctrinal__001": patch_coh_05,
    "pat_coh_09__doctrinal__001": patch_coh_09,
}

# ────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────

def main():
    # 1. Load
    doc = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
    current_version = doc.get("_meta", {}).get("version")
    print(f"Loaded patterns.json v{current_version} — {len(doc['patterns'])} patterns")
    if current_version != "14.2.2":
        print(f"WARNING: expected v14.2.2, got v{current_version} — patch continues anyway")

    # 2. Backup
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_path = PATTERNS_PATH.with_suffix(f".json.pre-v143.{ts}")
    shutil.copy2(PATTERNS_PATH, backup_path)
    print(f"Backup saved : {backup_path.name}")

    # 3. Apply cross-cutting additions to all patterns
    applied_ops = 0
    applied_reg = 0
    applied_review = 0
    for p in doc["patterns"]:
        pid = p.get("pattern_id", "")
        # operator_mode (default)
        if "operator_mode" not in p:
            p["operator_mode"] = copy.deepcopy(DEFAULT_OPERATOR_MODE)
            applied_ops += 1
        # regulatory_flag (only on high-risk)
        if pid in REGULATORY_RISK_PATTERN_IDS and "regulatory_flag" not in p:
            p["regulatory_flag"] = copy.deepcopy(REGULATORY_RISK_PATTERN_IDS[pid])
            applied_reg += 1
        # expected_review_date
        if "expected_review_date" not in p:
            p["expected_review_date"] = REVIEW_DATE
            applied_review += 1

    print(f"Cross-cutting: operator_mode +{applied_ops}, regulatory_flag +{applied_reg}, expected_review_date +{applied_review}")

    # 4. Apply pattern-specific tightenings
    applied_specific = 0
    for p in doc["patterns"]:
        pid = p.get("pattern_id", "")
        if pid in PATCH_REGISTRY:
            PATCH_REGISTRY[pid](p)
            applied_specific += 1
            print(f"  tightened  {pid}  ({p.get('name','')[:60]})")

    print(f"Specific tightenings applied: {applied_specific}/11")

    # 5. Update meta
    meta = doc.setdefault("_meta", {})
    meta["version"] = "14.2.3"
    meta["last_update"] = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    meta.setdefault("harmo_history", []).append({
        "at": meta["last_update"],
        "pass": "v143_tightening_post_mathis_verdicts",
        "cross_cutting": {
            "operator_mode_added": applied_ops,
            "regulatory_flag_added": applied_reg,
            "expected_review_date_added": applied_review,
        },
        "specific_tightenings": applied_specific,
        "note": "V14.2.3 tightening : 11 doctrinal patterns renforcés (Mathis strict mode), operator_mode {internal_agency|saas_autonomous} ajouté universellement, regulatory_flag ajouté sur 7 patterns à risque DGCCRF/FTC, expected_review_date 6 mois"
    })

    # 6. Write out
    PATTERNS_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten: {PATTERNS_PATH.name} (v14.2.3)")

    # 7. Quick coverage verification
    from collections import Counter
    by_pillar = Counter()
    for p in doc["patterns"]:
        pil = p.get("context", {}).get("criterion_pillar") or p.get("pillar", "?")
        by_pillar[pil] += 1
    print(f"\nCoverage by pillar: {dict(by_pillar)}")

if __name__ == "__main__":
    main()
