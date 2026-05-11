#!/usr/bin/env python3
"""
build_doctrinal_patterns.py — V14.2 top-down completion pass.

Generates one doctrinal pattern per orphan criterion (criteria with no
validated bucket after batch 1 bottom-up). Each pattern:

- status: "doctrinal" (distinct from validated/draft/orphan)
- seed_count: 0, seed_instances: []
- expected_lift_pct: {low:null, high:null, mean:null, basis: explicit}
- seed_variance: {all null, note: explicit}
- rule.why: academic citations + playbook principle
- rule.do / rule.dont: actionable technical specs
- copy_templates: FR/EN primitives
- layout_directives: populated ONLY for MECH patterns (visual/layout criteria)
- source_refs: playbook criterion path + external literature
- business_category: "all" (universal; specialized later if bottom-up reveals)

Output: outputs_distill/batches/batch_002_doctrinal.json

Usage:
    python3 scripts/build_doctrinal_patterns.py
    python3 scripts/patterns_distill.py merge outputs_distill/batches/batch_002_doctrinal.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs_distill" / "batches" / "batch_002_doctrinal.json"


def mk(
    *,
    crit: str,
    pillar: str,
    pillar_block: str,
    name: str,
    summary: str,
    page_types: list,
    why: str,
    do: list,
    dont: list,
    copy_templates: list = None,
    layout_directives: dict = None,
    anti_patterns: list = None,
    external_refs: list = None,
    effort_hours: int = 6,
    priority: str = "P1",
    mech_or_copy: str = "COPY",
):
    """Build a doctrinal pattern dict with canonical Format A schema."""
    pattern_id = f"pat_{crit}__doctrinal__001"
    pillar_map = {
        "hero": "Hero", "per": "Persuasion", "ux": "UX",
        "coh": "Coherence", "psy": "Psychology", "tech": "Tech",
    }
    p = {
        "pattern_id": pattern_id,
        "version": "1.0.0",
        "status": "doctrinal",
        "name": name,
        "summary": summary,
        "criterion": crit,
        "pillar": pillar_map.get(pillar, pillar),
        "mech_or_copy": mech_or_copy,
        "context": {
            "criterion_id": crit,
            "criterion_pillar": pillar,
            "criterion_name": name,
            "page_type": "universal",
            "intent": "universal",
            "business_category": "all",
            "score_band": "universal",
            "applicable_to": f"playbook criterion {crit} (doctrinal pattern — no client seed grounding, sourced on playbook + academic literature)",
        },
        "applicability": {
            "page_types": page_types,
            "business_categories": ["all"],
            "skip_if": [],
        },
        "seed_count": 0,
        "seed_instances": [],
        "expected_lift_pct": {
            "low": None,
            "high": None,
            "mean": None,
            "basis": "Doctrinal pattern — no seed data. Lift to be inherited from first validated buckets of this criterion during future bottom-up pass.",
        },
        "seed_variance": {
            "jaccard": None,
            "cosine_tfidf": None,
            "mean": None,
            "computed_inline": False,
            "note": "Doctrinal pattern — no seed variance. Applicable across all business categories and contexts per playbook principle.",
        },
        "rule": {
            "why": why,
            "do": do,
            "dont": dont,
        },
        "copy_templates": copy_templates or [],
        "layout_directives": layout_directives or {},
        "anti_patterns_ref": anti_patterns or [],
        "ab_angles_ref": [],
        "related_patterns_ref": [],
        "source_refs": {
            "playbook": f"playbook/{pillar_block}#{crit}",
            "external": external_refs or [],
        },
        "effort_hours_typical": effort_hours,
        "priority_typical": priority,
    }
    return p


PATTERNS = []

# =====================================================================
# PSY (6 patterns) — Mathis-highlighted pillar
# =====================================================================

PATTERNS.append(mk(
    crit="psy_02",
    pillar="psy",
    pillar_block="bloc_5_psycho_v3.json",
    mech_or_copy="COPY",
    name="Rareté & Exclusivité authentique — perception de valeur",
    summary="Activer ≥2 leviers de valeur perçue (rareté réelle, exclusivité vérifiable, signaux de qualité supérieure) sans basculer dans la fausse urgence.",
    page_types=["home", "pdp", "lp_sales", "pricing", "collection", "bundle_standalone", "advertorial"],
    why=(
        "Cialdini (1984, 2016) Principe de Rareté : la valeur perçue d'un bien "
        "augmente avec sa rareté perçue (limited supply → higher desirability). "
        "Prospect Theory (Kahneman & Tversky 1979) : les individus sont plus "
        "motivés par la perte potentielle d'une opportunité que par le gain "
        "équivalent. Effet IKEA (Norton et al. 2012) et signalling theory "
        "(Spence 1973) : un produit présenté comme exclusif ou difficilement "
        "accessible active un heuristique 'coûteux = valeur'. La condition "
        "éthique est que la rareté soit réelle (production limitée, édition "
        "numérotée, beta fermée, cohorte nominative) — la fausse rareté détruit "
        "la confiance à long terme (Baymard 2022 : 68% des utilisateurs e-comm "
        "disent avoir déjà quitté un site après avoir détecté une fausse urgence)."
    ),
    do=[
        "Afficher au minimum 2 leviers de valeur perçue parmi : (a) rareté production/matière (édition limitée 200 ex, matière rare, artisanat), (b) exclusivité distribution (dispo uniquement ici, beta fermée sur invitation vérifiable), (c) signaux qualité supérieure (label, certification, fabrication locale tracée).",
        "Ancrer chaque mention de rareté à un chiffre ou un critère vérifiable : 'édition limitée 500 pièces', 'dernière série avant réassort fin mai', 'beta fermée 200 clients sélectionnés'.",
        "Afficher le stock réel dynamiquement si e-commerce inventaire : 'Il reste 7 en stock' sourcé DB produit, pas fake-timer. Mettre à jour côté serveur.",
        "Si exclusivité par cohorte/invitation : rendre la condition vérifiable ('entrée par parrainage', 'waitlist 2400 personnes, 50 places/mois').",
        "Positionner le signal de rareté près du CTA primaire, pas isolé dans un footer. Taille ≥14px mobile, contrast AA.",
    ],
    dont=[
        "Jamais de countdown timer qui redémarre au refresh — c'est une fausse rareté détectable et détruit la confiance.",
        "Jamais 'plus que X articles !' sur une catégorie entière ou un produit illimité (digital, SaaS abonnement).",
        "Jamais 'offre réservée aux 100 premiers' sans mécanisme réel de plafonnement (ordre d'arrivée vérifiable).",
        "Pas de message 'exclusif' sur un produit mass-market accessible partout — le mot 'exclusif' est un écoulement de crédibilité.",
        "Pas de scarcity sans ancrage : 'quantités limitées' vague = placebo inefficace (CXL 2019 : scarcity message unsourced has zero lift).",
    ],
    copy_templates=[
        {"slot": "scarcity_inventory", "template": "Il reste {count} {unit} en stock — réassort prévu {date}", "example": "Il reste 12 flacons en stock — réassort prévu 14 mai"},
        {"slot": "scarcity_edition", "template": "Édition limitée — {total} pièces numérotées", "example": "Édition limitée — 500 pièces numérotées à la main"},
        {"slot": "exclusivity_cohort", "template": "Beta fermée — {slots} places {period}", "example": "Beta fermée — 50 places par mois"},
        {"slot": "signal_quality", "template": "{certification} — {year} · {proof_link}", "example": "Label Origine France Garantie — 2024 · voir certificat"},
    ],
    anti_patterns=["scarcity_countdown_fake", "urgency_everywhere_diluted", "scarcity_unsourced_vague"],
    external_refs=[
        "Cialdini R. (2016) Influence: The Psychology of Persuasion (rev.)",
        "Kahneman D. & Tversky A. (1979) Prospect Theory",
        "Norton M., Mochon D. & Ariely D. (2012) The IKEA Effect",
        "Spence M. (1973) Job Market Signaling",
        "Baymard Institute (2022) Urgency and Scarcity on E-commerce",
        "CXL Institute (2019) Scarcity Test Library",
    ],
    effort_hours=4,
    priority="P1",
))

PATTERNS.append(mk(
    crit="psy_03",
    pillar="psy",
    pillar_block="bloc_5_psycho_v3.json",
    mech_or_copy="COPY",
    name="Ancrage prix/valeur — framing de la décision",
    summary="Structurer la présentation prix pour que le tarif affiché paraisse raisonnable face à une référence de valeur claire (prix barré vérifié, comparable marché, ROI chiffré).",
    page_types=["pdp", "pricing", "bundle_standalone", "comparison", "lp_sales", "home"],
    why=(
        "Anchoring Heuristic (Tversky & Kahneman 1974) : les individus ajustent "
        "leur estimation de valeur à partir du premier chiffre rencontré "
        "(ancre), même si celui-ci est arbitraire. Prospect Theory (Kahneman "
        "1979) : la décision d'achat dépend du framing (gain vs perte, "
        "référence vs valeur absolue). Mental Accounting (Thaler 1985) : les "
        "consommateurs comparent le prix à une 'transaction utility' = prix "
        "de référence – prix payé. Un tarif seul sans ancre de référence est "
        "jugé sur intuition, souvent biaisée. Le ROI chiffré ou la comparaison "
        "marché transforme un débat interne 'c'est cher ?' en calcul rationnel "
        "vérifiable. Condition éthique : l'ancre doit être réelle (prix barré "
        "historique réel, concurrent réel, ROI sourçable sur cas client)."
    ),
    do=[
        "Afficher un prix de référence vérifiable à côté du prix actuel : prix barré (date dernière pratique), prix catalogue vs promo, prix équivalent marché.",
        "Si bundle : décomposer le prix unitaire addition vs prix bundle ('valeur totale 120€ — bundle 79€ — vous économisez 41€').",
        "Si SaaS/abonnement : ancrer au coût évité ('remplacez 4 outils à 25€/mois = 100€/mois → notre plan 39€/mois').",
        "ROI chiffré quand pertinent B2B/SaaS : 'investissement 299€/mois — cas clients moyen +8 200€ pipe/mois = ROI 27×'.",
        "Si premium : ancrer au coût du problème non résolu ('une contrefaçon coûte 80€ à remplacer × 3/an = 240€ vs notre produit 120€ garanti à vie').",
    ],
    dont=[
        "Pas de prix barré inventé (prix jamais pratiqué) — interdiction légale (Code de la consommation, Directive Omnibus UE 2022).",
        "Pas de comparaison à un concurrent inexistant ou faussement défavorisé.",
        "Pas de 'économisez 50%' sans référence claire du prix de départ.",
        "Pas d'ancrage absurde qui casse la crédibilité ('valeur 3 000€ — aujourd'hui 49€' sans justification).",
        "Ne pas empiler 3+ ancres différentes simultanément (prix barré + comparatif + bundle + ROI) — cognitive overload, Miller 1956.",
    ],
    copy_templates=[
        {"slot": "anchor_price_strike", "template": "{striked_price} {current_price} · {discount_pct}", "example": "~~89€~~ **59€** · -34%"},
        {"slot": "anchor_bundle", "template": "Valeur totale {sum} — bundle {bundle_price} · économie {savings}", "example": "Valeur totale 120€ — bundle 79€ · économie 41€"},
        {"slot": "anchor_saas_replacement", "template": "Remplace {tools} · coût évité {saved}/mois — notre plan {our_price}/mois", "example": "Remplace Notion + Airtable + Zapier · coût évité 87€/mois — notre plan 39€/mois"},
        {"slot": "anchor_roi_b2b", "template": "{investment}/mois → {return}/mois · ROI {multiplier}×", "example": "299€/mois → 8 200€ pipe/mois · ROI 27×"},
    ],
    anti_patterns=["fake_strikethrough_price", "arbitrary_high_anchor", "savings_without_basis"],
    external_refs=[
        "Tversky A. & Kahneman D. (1974) Judgment under Uncertainty: Heuristics and Biases",
        "Kahneman D. (2011) Thinking, Fast and Slow",
        "Thaler R. (1985) Mental Accounting and Consumer Choice",
        "Ariely D. (2008) Predictably Irrational, chap. 1 The Truth About Relativity",
        "Directive (UE) 2019/2161 Omnibus — transparence des réductions de prix",
    ],
    effort_hours=5,
    priority="P0",
))

PATTERNS.append(mk(
    crit="psy_04",
    pillar="psy",
    pillar_block="bloc_5_psycho_v3.json",
    mech_or_copy="COPY",
    name="Aversion à la perte & Risk Reversal — réduction du risque perçu",
    summary="Transférer le risque de l'acheteur vers le vendeur via ≥2 leviers (garantie satisfait/remboursé, retour simple, essai gratuit, SAV rapide, clauses réassurantes).",
    page_types=["home", "pdp", "pricing", "lp_sales", "checkout", "bundle_standalone", "comparison"],
    why=(
        "Loss Aversion (Kahneman & Tversky 1979) : une perte pèse "
        "psychologiquement ~2× plus qu'un gain équivalent (coefficient λ ≈ 2.25). "
        "L'acheteur face à une décision évalue inconsciemment le risque de se "
        "tromper AVANT d'évaluer le bénéfice du choix. Commitment & Consistency "
        "(Cialdini 1.2) : engager le vendeur en premier (garantie publique) "
        "crée une obligation réciproque qui libère l'acheteur. Regret Theory "
        "(Bell 1982, Loomes & Sugden 1982) : l'acheteur anticipe le regret post-"
        "achat — la garantie éteint cette anticipation. Friction de confiance "
        "(Baymard 2023 cart-abandonment study) : 23% des abandons e-commerce "
        "liés à 'policies/returns unclear'. Chaque levier de risk reversal "
        "supprime une friction cognitive préachat. Condition éthique : la "
        "garantie doit être honorée sans conditions impossibles dans les CGV "
        "(sinon = bait-and-switch détectable)."
    ),
    do=[
        "Afficher ≥2 leviers de risk reversal parmi : garantie satisfait/remboursé chiffrée (14/30/60 jours), retour gratuit avec process simple (étiquette prépayée), essai gratuit sans CB, SAV avec délai de réponse garanti, assurance casse.",
        "Formuler la garantie au format 'engagement' : 'Nous reprenons sans poser de question' > 'Politique de retour disponible'.",
        "Placer le premier levier dans la ATF près du CTA primaire (réassurance immédiate), le second dans le bloc décision (pricing, panier, checkout).",
        "Si SaaS : essai gratuit illimité temporellement si possible, sinon ≥14 jours, sans CB requise.",
        "Framer la décision en termes de perte évitée quand pertinent : 'Ne restez pas bloqué sur un outil qui ne répond pas — testez 30 jours, arrêtez sans frais'.",
    ],
    dont=[
        "Pas de garantie affichée mais conditions impossibles en CGV (produit doit être dans emballage scellé, étiquette d'origine, etc. = manipulation).",
        "Pas de 'satisfait ou remboursé' vague sans durée — doit être chiffré.",
        "Pas d'essai gratuit avec CB obligatoire et renouvellement automatique caché.",
        "Pas de retour payant facturé >5€ sur un produit <50€ — ratio friction/valeur casse la réassurance.",
        "Ne pas multiplier les disclaimers et astérisques qui vident la promesse.",
    ],
    copy_templates=[
        {"slot": "guarantee_refund", "template": "Satisfait ou remboursé — {days} jours · retour gratuit", "example": "Satisfait ou remboursé — 30 jours · retour gratuit"},
        {"slot": "trial_saas", "template": "Essai gratuit {duration} · sans carte bancaire", "example": "Essai gratuit 14 jours · sans carte bancaire"},
        {"slot": "ship_return", "template": "Livraison {delivery} · retour {return_policy}", "example": "Livraison 48h offerte · retour prépayé 14 jours"},
        {"slot": "sav_promise", "template": "Service client {response_sla} — par {channel}", "example": "Service client répondu en <2h — par email et chat"},
        {"slot": "warranty_long", "template": "Garantie {years} — {scope}", "example": "Garantie 10 ans — pièces et main-d'œuvre"},
    ],
    anti_patterns=["hidden_return_fees", "cb_required_free_trial", "guarantee_impossible_terms"],
    external_refs=[
        "Kahneman D. & Tversky A. (1979) Prospect Theory: An Analysis of Decision Under Risk",
        "Bell D. (1982) Regret in Decision Making Under Uncertainty",
        "Cialdini R. (2016) Influence — Commitment & Consistency",
        "Baymard Institute (2023) Cart Abandonment Rate Study (2023 update)",
        "CXL (2021) Risk Reversal Copy Tests Library",
    ],
    effort_hours=5,
    priority="P0",
))

PATTERNS.append(mk(
    crit="psy_05",
    pillar="psy",
    pillar_block="bloc_5_psycho_v3.json",
    mech_or_copy="COPY",
    name="Autorité & Crédibilité — signaux d'expertise vérifiables",
    summary="Faire apparaître ≥3 signaux d'autorité différents (expert nommé, certification, media mentions, awards, partenaires institutionnels) vérifiables en <2 minutes.",
    page_types=["home", "pdp", "lp_sales", "pricing", "lp_leadgen", "vsl", "webinar", "advertorial"],
    why=(
        "Cialdini (1984) Principe d'Autorité : les individus suivent plus "
        "volontiers une recommandation émise par une figure perçue comme "
        "experte/légitime (étude Milgram 1963 sur la soumission à l'autorité). "
        "Halo Effect (Thorndike 1920) : un signal d'expertise vérifiable "
        "irradie positivement sur l'ensemble de la perception de la marque. "
        "Trust Pyramid (Baymard 2022) : 68% des acheteurs e-comm first-time "
        "cherchent au moins un signal institutionnel (media, label, expert) "
        "avant de convertir. Dual-Process Theory (Kahneman 2011) : l'autorité "
        "active le Système 1 (heuristique rapide), réduit la charge cognitive "
        "du Système 2 sur la vérification détaillée. Condition éthique : "
        "signaux vérifiables en 2 min (lien vers certification, vers article "
        "media, vers profil expert avec historique public) — faux logos "
        "media = fraude détectable (reverse-image search + fact-check)."
    ),
    do=[
        "Afficher ≥3 signaux d'autorité différents parmi : (a) expert/fondateur nommé avec titre vérifiable + lien LinkedIn ou bio publique, (b) certification/label métier avec date + numéro + lien vers organisme, (c) logos media 'As seen in' avec lien vers articles réels, (d) awards/distinctions avec date + lien vers palmares, (e) partenaires institutionnels (écoles, laboratoires, universités) avec lien vérifiable.",
        "Placer le cluster d'autorité entre Hero et Preuves (fold 2), ≥1 signal dans le Hero proche du CTA si place.",
        "Pour un fondateur : courte bio 60-80 mots (expérience + what-for-who), photo professionnelle, lien LinkedIn ou profil auteur.",
        "Pour les logos media : mettre en avant les 4-6 plus prestigieux, aligner horizontalement, taille hauteur 32-40px, grayscale ou couleurs originales sobres.",
        "Pour un laboratoire/école : logo + nom complet + 'partenaire de recherche depuis {year}'.",
    ],
    dont=[
        "Jamais de logos media 'as seen in' sans article sourçable — reverse-image search détecte la fraude en 30s.",
        "Pas de titre pompeux non vérifiable ('leader européen', '#1 du marché') sans source + méthodologie.",
        "Pas d'expert photo stock + nom inventé — LinkedIn search détecte en <1 min.",
        "Ne pas empiler 15+ logos medium pour compenser l'absence d'un signal fort.",
        "Pas de certification expirée ou de date omise — la date est un signal de fraîcheur.",
    ],
    copy_templates=[
        {"slot": "expert_founder_bio", "template": "{Name}, {Title} · {Credentials} · {Years} ans d'expérience", "example": "Dr Clara Lemoine, médecin nutritionniste · DU Nutrition Sorbonne · 15 ans d'expérience"},
        {"slot": "media_as_seen", "template": "Vu dans {Media1}, {Media2}, {Media3}", "example": "Vu dans Le Monde, Les Échos, France Inter"},
        {"slot": "certification_label", "template": "{Label} · certifié {Year} · N° {Ref}", "example": "Label Cosmos Organic · certifié 2023 · N° FR-BIO-01"},
        {"slot": "partners_inst", "template": "Partenaire de recherche · {Institution} depuis {Year}", "example": "Partenaire de recherche · Inserm depuis 2021"},
    ],
    anti_patterns=["fake_media_logos", "stock_expert_photo", "leader_market_unsourced"],
    external_refs=[
        "Cialdini R. (2016) Influence — Principle of Authority",
        "Milgram S. (1963) Behavioral Study of Obedience",
        "Thorndike E.L. (1920) A Constant Error in Psychological Ratings (Halo Effect)",
        "Baymard Institute (2022) E-commerce Trust & Credibility Study",
        "Kahneman D. (2011) Thinking, Fast and Slow — Dual Process",
        "Forrester (2022) B2B Trust Index",
    ],
    effort_hours=6,
    priority="P0",
))

PATTERNS.append(mk(
    crit="psy_06",
    pillar="psy",
    pillar_block="bloc_5_psycho_v3.json",
    mech_or_copy="COPY",
    name="Réciprocité & Micro-engagements — progression vers la conversion",
    summary="Découper le parcours en 2-3 micro-engagements progressifs (valeur gratuite reçue → mini-action → engagement principal) en exploitant la règle d'escalation.",
    page_types=["home", "lp_leadgen", "squeeze", "quiz_vsl", "pricing", "lp_sales", "webinar", "challenge"],
    why=(
        "Cialdini (1984) Principe de Réciprocité : recevoir crée une obligation "
        "de rendre. Foot-in-the-Door (Freedman & Fraser 1966) : une petite "
        "demande acceptée augmente de +47% la probabilité d'acceptation "
        "ultérieure d'une demande plus grande. Escalation of Commitment "
        "(Staw 1976) : chaque micro-action déjà faite augmente l'engagement "
        "psychologique sur la trajectoire. Fogg Behavior Model B=MAT "
        "(Fogg 2009) : Behavior = Motivation × Ability × Trigger — réduire "
        "l'Ability cost (micro-step) rend le trigger suffisant même à "
        "motivation moyenne. Endowment Effect (Thaler 1980) : dès qu'un "
        "utilisateur interagit avec un résultat personnalisé (quiz, "
        "diagnostic), il lui attribue une valeur supérieure. Le design "
        "gagnant offre une valeur gratuite réelle AVANT toute demande "
        "(contenu, diagnostic, échantillon, version gratuite) puis escalade "
        "par petites étapes. Condition éthique : la valeur gratuite doit être "
        "réelle, pas un teaser creux."
    ),
    do=[
        "Offrir ≥1 valeur gratuite réelle avant toute demande de conversion : guide téléchargeable 8+ pages, calculateur/simulateur, diagnostic personnalisé, échantillon, version freemium.",
        "Découper le parcours en 2-3 micro-engagements progressifs : (1) interaction ludique/diagnostic <2min, (2) lead magnet par email, (3) demande principale (achat/démo/souscription).",
        "Pour chaque étape, indiquer la progression : 'Étape 2/3', barre de progression, checkpoint.",
        "Pour un quiz/diagnostic : personnalisation réelle du résultat (pas 1 seul output générique).",
        "Pour un lead magnet : contenu self-sufficient (lisible sans action supplémentaire) avec lien discret vers étape suivante.",
    ],
    dont=[
        "Pas de demande finale brutale sans valeur préalable (cold CTA 'Achetez maintenant' sur landing cold traffic).",
        "Pas de lead magnet creux (pdf 1 page remanié d'un blog post existant) — le prospect perçoit la duperie et se désengage.",
        "Pas de quiz dont tous les chemins mènent au même produit — le sentiment de personnalisation disparaît et le ROI pédagogique s'effondre.",
        "Pas de 5+ micro-étapes — l'escalation devient attrition (Nielsen Norman 2022 : engagement funnel drop à partir de step 4+).",
        "Ne pas demander CB dans le micro-engagement (essai gratuit requis CB = anti-réciprocité, casse la confiance).",
    ],
    copy_templates=[
        {"slot": "free_value_guide", "template": "Téléchargez gratuitement · {guide_title} · {pages} pages", "example": "Téléchargez gratuitement · Le Guide 2026 de l'Optimisation Fiscale · 32 pages"},
        {"slot": "diagnostic_quiz", "template": "{duration} pour votre diagnostic personnalisé · {n_questions} questions", "example": "2 min pour votre diagnostic personnalisé · 8 questions"},
        {"slot": "stepper", "template": "Étape {current}/{total} — {step_name}", "example": "Étape 2/3 — Recevez votre plan"},
        {"slot": "sample_physical", "template": "Demandez votre échantillon gratuit · livré {delay}", "example": "Demandez votre échantillon gratuit · livré en 3 jours"},
    ],
    anti_patterns=["thin_lead_magnet", "quiz_same_output", "cold_cta_no_value"],
    external_refs=[
        "Cialdini R. (2016) Influence — Reciprocity",
        "Freedman J.L. & Fraser S.C. (1966) Compliance without Pressure: The Foot-in-the-Door Technique",
        "Fogg B.J. (2009) A Behavior Model for Persuasive Design",
        "Staw B.M. (1976) Knee-Deep in the Big Muddy: A Study of Escalating Commitment",
        "Thaler R. (1980) Toward a Positive Theory of Consumer Choice — Endowment Effect",
        "Nielsen Norman Group (2022) Multi-Step Form Drop-Off Research",
    ],
    effort_hours=8,
    priority="P1",
))

PATTERNS.append(mk(
    crit="psy_08",
    pillar="psy",
    pillar_block="bloc_5_psycho_v3.json",
    mech_or_copy="COPY",
    name="Voice of Customer — verbatims clients littéraux réinjectés",
    summary="Intégrer ≥3 signaux VoC réels (verbatims exacts entre guillemets, vocabulaire client non-marketing, témoignages avec contexte concret) pour activer le Message-Market Fit.",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "advertorial", "listicle", "vsl", "comparison"],
    why=(
        "Message-Market Fit (Copyhackers, Joanna Wiebe 2012-présent) : le "
        "meilleur copy n'est pas celui du copywriter, c'est celui du client — "
        "les mots exacts qu'ils utilisent pour décrire leur problème et le "
        "résultat. Voice of Customer Research Method (Jen Havice 2017) : "
        "sourcer sur reviews Amazon/G2, support tickets, sales calls, "
        "community forums. Fluency Heuristic (Reber & Schwarz 1999) : un "
        "message formulé dans le vocabulaire familier du lecteur est perçu "
        "comme plus vrai et plus crédible. Narrative Transportation (Green & "
        "Brock 2000) : un témoignage narratif avec détails concrets "
        "(nom, métier, contexte, chiffre) suspend temporairement l'esprit "
        "critique et laisse l'émotion opérer. Social Proof (Cialdini 1.4) : "
        "les prospects similaires à eux (même pain, même contexte) sont le "
        "signal le plus puissant. Condition éthique : verbatims réels "
        "(traçables), pas reformulés par le marketing. Signal de faux : "
        "tous les témoignages ont la même structure, même ton, même "
        "vocabulaire — rupture de pattern linguistique détectable."
    ),
    do=[
        "Intégrer ≥3 verbatims clients exacts entre guillemets, avec nom réel, métier/contexte, photo (si consentement), date ou durée d'utilisation.",
        "Conserver le vocabulaire client même s'il contient des tournures imparfaites — c'est le signal de vérité (Baymard 2023 : ~75% des utilisateurs distinguent un vrai review d'un faux en 6s).",
        "Structurer un témoignage narratif : (1) contexte avant ('j'ai essayé X avant'), (2) pivot ('ce qui a tout changé'), (3) résultat chiffré ou concret.",
        "Sourcer les verbatims sur : reviews produit, interviews clients 30min, support tickets avec feedback spontané, G2/Trustpilot/Google reviews, transcripts d'entretiens NPS.",
        "Réinjecter les mots exacts dans le copy principal (H1, bénéfices, FAQ) — pas seulement les témoignages. Exemple : 'Enfin un outil qui ne me demande pas un doctorat en config' > 'Interface simple et intuitive'.",
    ],
    dont=[
        "Pas de témoignages tous de la même structure grammaticale ou même longueur — révélateur de fabrication.",
        "Pas de verbatims sans nom/contexte ('J.M., satisfait') — le vague = suspect.",
        "Pas de reformulation marketing des témoignages ('le client nous a dit que…') — casse la voix, anéantit la crédibilité.",
        "Pas d'inventaire de superlatifs creux ('génial, super, incroyable') — vocabulaire copywriter, pas client.",
        "Pas de témoignages sans rapport au critère de décision principal (témoignages 'livraison rapide' sur une LP centrée efficacité produit).",
    ],
    copy_templates=[
        {"slot": "voc_testimonial_narrative", "template": "« {verbatim_quote} » — {Name}, {Role}, {Context}", "example": "« J'ai revendu mon ancien en 3 jours, celui-ci me sauve la vie en rando — j'ai jamais repensé à l'ancien. » — Pierre B., infirmier, Annecy"},
        {"slot": "voc_headline_from_review", "template": "{Exact_customer_phrase_as_H1}", "example": "« Enfin un CRM qui ne me demande pas de manuel de 200 pages »"},
        {"slot": "voc_objection_faq", "template": "« {Customer_objection} » — {factual_reply}", "example": "« Est-ce que ça marche vraiment si je suis débutant ? » — Oui, 62% de nos utilisateurs n'avaient jamais touché à la compta avant."},
        {"slot": "voc_result_specific", "template": "« J'ai {concrete_result} en {timeframe} »", "example": "« J'ai divisé mon temps de préparation de factures par 4 en 3 semaines »"},
    ],
    anti_patterns=["testimonials_template_identical", "marketing_rewritten_quote", "initials_only_no_context"],
    external_refs=[
        "Wiebe J. / Copyhackers (2012-présent) Voice of Customer research method",
        "Havice J. (2017) Finding the Right Message",
        "Reber R. & Schwarz N. (1999) Effects of Perceptual Fluency on Judgments of Truth",
        "Green M.C. & Brock T.C. (2000) The Role of Transportation in the Persuasiveness of Public Narratives",
        "Cialdini R. (2016) Influence — Social Proof",
        "Baymard Institute (2023) Trust in User-Generated Reviews",
    ],
    effort_hours=8,
    priority="P0",
))


# =====================================================================
# HERO (2 patterns)
# =====================================================================

PATTERNS.append(mk(
    crit="hero_02",
    pillar="hero",
    pillar_block="bloc_1_hero_v3.json",
    mech_or_copy="COPY",
    name="Sous-titre explicite qui complète le H1 (pour qui / comment / résultat)",
    summary="Expliciter dans un sous-titre de 12-18 mots la cible, le mécanisme et le résultat attendu — fermer l'écart entre promesse (H1) et preuve (bénéfices).",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "advertorial", "vsl", "comparison", "webinar"],
    why=(
        "5-Second Test (CXL 2019, Nielsen Norman 2020) : 62% des visiteurs "
        "qui ne comprennent pas la proposition de valeur dans les 5 premières "
        "secondes abandonnent. H1 seul = promesse, sous-titre = preuve "
        "immédiate. Story Pyramid (Minto 1987) : situation → complication → "
        "résolution en ouverture. Si le H1 porte le résultat, le sous-titre "
        "précise le chemin (pour qui, comment, quand). Dual Coding Theory "
        "(Paivio 1971) : une idée doit être formulée dans 2 registres "
        "(émotionnel + rationnel) pour être mémorisée. Le H1 active l'aspiration, "
        "le sous-titre ancre dans le concret vérifiable. Awareness Match "
        "(Schwartz 1966) : un trafic Problem-Aware a besoin d'un sous-titre "
        "qui nomme son problème avec ses mots avant d'accepter la solution."
    ),
    do=[
        "Rédiger un sous-titre de 12-18 mots qui réponde à 2 des 3 questions : POUR QUI ? COMMENT ? AVEC QUEL RÉSULTAT ?",
        "Inclure au moins un élément concret : délai ('en 7 jours'), quantité ('250 clients'), cible ('indépendants'), ou mécanisme ('via notre IA de matching').",
        "Utiliser un vocabulaire Problem-Aware du persona (pas du jargon marketing, voir psy_08 VoC).",
        "Taille typographique : 18-22px mobile, 22-28px desktop, contraste AAA sur fond hero.",
        "Espacer de 12-16px du H1 pour respiration visuelle, pas de mur de texte.",
    ],
    dont=[
        "Pas de sous-titre tautologique qui répète le H1 en d'autres mots.",
        "Pas de sous-titre >25 mots — au-delà, Nielsen Norman 2020 montre une chute de 38% de la lecture jusqu'au bout.",
        "Pas de sous-titre vague 'La meilleure solution pour votre entreprise' — zéro signal discriminant.",
        "Pas de buzzwords cumulés ('innovant, révolutionnaire, disruptif') — signal AI-generic, pas VoC.",
        "Pas de sous-titre adressé à 'tout le monde' sans cible — le persona-match échoue.",
    ],
    copy_templates=[
        {"slot": "subtitle_for_how_result", "template": "Pour {persona} qui {pain}. {mechanism} — {result_timeframe}.", "example": "Pour les avocats qui croulent sous les PV. Notre IA les classe en 60 secondes — retrouvez 4h par semaine."},
        {"slot": "subtitle_positioning", "template": "{Category_reframed} — {differenciator} · {proof}", "example": "Le CRM sans friction — build par des commerciaux, pas des ingénieurs · +8 000 équipes"},
        {"slot": "subtitle_awareness_problem", "template": "Vous {pain} ? {reframe_solution}", "example": "Vous perdez 2h par jour sur des tâches répétitives ? Automatisez sans coder."},
    ],
    anti_patterns=["subtitle_tautological", "subtitle_buzzword_stack", "subtitle_generic_everyone"],
    external_refs=[
        "CXL Institute (2019) 5-Second Test Research Library",
        "Nielsen Norman Group (2020) Writing for the Web: Subheadings",
        "Minto B. (1987) The Pyramid Principle",
        "Paivio A. (1971) Imagery and Verbal Processes — Dual Coding",
        "Schwartz E. (1966) Breakthrough Advertising — Awareness levels",
    ],
    effort_hours=4,
    priority="P0",
))

PATTERNS.append(mk(
    crit="hero_05",
    pillar="hero",
    pillar_block="bloc_1_hero_v3.json",
    mech_or_copy="COPY",
    name="Preuve sociale ou micro-réassurance dans le fold 1",
    summary="Intégrer dans le fold 1 ≥1 signal de preuve sociale chiffrée ou micro-réassurance (note moyenne, nombre d'utilisateurs, délai garantie, labels) près du CTA.",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "pricing", "advertorial", "vsl", "webinar"],
    why=(
        "Cialdini (1984) Principe de Preuve Sociale : en situation "
        "d'incertitude, les individus regardent ce que d'autres font/pensent. "
        "Plus la situation est ambiguë (first visit sur un site inconnu), "
        "plus le signal social pèse. Herd Behavior (Asch 1951) : exposure "
        "à un signal de convergence sociale augmente la probabilité de "
        "conformation même si l'évidence est contraire. Fluency Heuristic "
        "(Reber & Schwarz 1999) : un chiffre concret augmente la fluency, "
        "donc la crédibilité. Baymard (2022) : 74% des visiteurs e-comm "
        "first-time cherchent un signal social dans le fold 1 — son absence "
        "déclenche un départ vers les avis externes (Google, Trustpilot), "
        "avec risque élevé de non-retour. Conversion uplift médian Baymard "
        "rating visible ATF : +4-8% sur purchase intent. Condition éthique : "
        "chiffres réels (pas 'utilisés par des milliers'), avis sourçables."
    ),
    do=[
        "Intégrer dans le fold 1 ≥1 signal concret : (a) note moyenne chiffrée avec N ('⭐ 4.8/5 sur 2 400 avis'), (b) nombre d'utilisateurs ('+32 000 équipes utilisent X'), (c) garantie chiffrée ('Satisfait ou remboursé 30j'), (d) label/certification visible.",
        "Positionner le signal dans les 300px autour du CTA primaire (sur ou sous), taille ≥13-15px mobile.",
        "Préférer un chiffre récent à un chiffre cumulé historique peu crédible ('+450 clients cette année' > '+50 000 depuis 2012').",
        "Si plateformes d'avis (Trustpilot, Google) : afficher le widget officiel ou un badge avec lien vers la page d'avis publique.",
        "Si absence d'avis/volume : fallback sur garantie ou label ('Fabriqué en France · Certifié bio').",
    ],
    dont=[
        "Pas de 'des milliers', 'nombreux clients', 'beaucoup', vague sans chiffre — zéro lift Baymard 2022.",
        "Pas de logo de clients fictifs ou de 'nos clients' sans autorisation vérifiable.",
        "Pas d'avis moyen '5.0' sur 500+ avis — statistiquement suspect, signal de fake reviews.",
        "Pas de widget avis caché dans un footer — hors fold 1, ne compte pas pour ce critère.",
        "Pas d'accumulation de 6+ signaux qui saturent (overstuff) — 1 fort > 5 faibles.",
    ],
    copy_templates=[
        {"slot": "rating_with_n", "template": "⭐ {rating}/5 · {n_reviews} avis {source}", "example": "⭐ 4.8/5 · 2 400 avis Trustpilot vérifiés"},
        {"slot": "users_count", "template": "{n_users} {persona} nous font confiance", "example": "+32 000 équipes SaaS nous font confiance"},
        {"slot": "guarantee_microreass", "template": "{guarantee} · {delivery} · {payment}", "example": "Satisfait ou remboursé 30j · Livraison offerte dès 50€ · Paiement 3x sans frais"},
        {"slot": "label_fallback", "template": "{label_1} · {label_2}", "example": "Fabriqué en France · Certifié Cosmos Organic"},
    ],
    anti_patterns=["vague_social_proof", "fake_five_star_rating", "signals_stuffed_hero"],
    external_refs=[
        "Cialdini R. (2016) Influence — Social Proof",
        "Asch S. (1951) Effects of Group Pressure Upon the Modification and Distortion of Judgments",
        "Reber R. & Schwarz N. (1999) Effects of Perceptual Fluency on Judgments of Truth",
        "Baymard Institute (2022) Social Proof and E-commerce Trust",
        "Spiegel Research (2017) The Power of Reviews",
    ],
    effort_hours=3,
    priority="P0",
))


# =====================================================================
# COH (5 patterns) — Coherence pillar
# =====================================================================

PATTERNS.append(mk(
    crit="coh_03",
    pillar="coh",
    pillar_block="bloc_4_coherence_v3.json",
    mech_or_copy="COPY",
    name="Alignement ad → LP (scent matching)",
    summary="Préserver la continuité message/visuel/offre entre l'annonce source (ad, email, SERP) et la landing — H1 reprend la promesse de l'ad, visuel congruent, offre exactement celle annoncée.",
    page_types=["pdp", "lp_leadgen", "lp_sales", "quiz_vsl", "advertorial", "listicle", "vsl", "challenge", "squeeze"],
    why=(
        "Information Scent (Pirolli & Card 1995) : les utilisateurs suivent un "
        "sentier cognitif 'ad → landing → next step'. Chaque rupture (visuel "
        "différent, promesse reformulée, offre modifiée) déclenche une "
        "réévaluation du Système 2 (Kahneman 2011) qui brise le momentum. "
        "Message Match Score (CXL 2018) : les LP avec alignement strict "
        "copy/visuel/offre vs ad ont +21-52% de CVR par rapport aux LP "
        "génériques (étude sur 138 campaigns). Cognitive Dissonance (Festinger "
        "1957) : une landing qui ne reprend pas la promesse ad fait supposer "
        "une duperie, active le départ. Pour le trafic paid, scent = test "
        "de confiance critique : le prospect vient de cliquer sur une "
        "promesse spécifique, il doit la retrouver intacte dans les 3 "
        "premières secondes."
    ),
    do=[
        "Reprendre dans le H1 de la LP les mots exacts de la promesse ad (± synonymes proches), pas une reformulation créative.",
        "Utiliser le même visuel hero que l'ad (ou une variante évidente du même set) — pas une banque d'image différente.",
        "Afficher l'offre exacte annoncée dans l'ad (prix, promo, bonus, délai) dans le fold 1, pas derrière un scroll.",
        "Pour les ads avec persona explicite ('pour les avocats', 'pour les parents'), le nommer dans H1 ou sous-titre.",
        "Maintenir la même tonalité (informative, émotionnelle, urgente) entre ad et LP — rupture de ton = rupture de confiance.",
        "Mesurer le scent : bounce rate LP > bounce rate site global = scent cassé, à debugger.",
    ],
    dont=[
        "Pas de LP générique pour un ad promotionnel ('-30% aujourd'hui') qui ne mentionne pas la promo dans le fold 1.",
        "Pas de reformulation 'créative' du H1 qui abandonne les keywords de l'ad (ex: ad 'CRM pour indépendants' → LP 'La solution business all-in-one').",
        "Pas de visuel hero complètement différent entre ad et LP — visuel = signal de continuité #1.",
        "Pas de redirection sur la home si l'ad renvoyait à une LP spécifique.",
        "Pas de multiplication des offres (promo ad + bonus LP + upsell fold 3) — overstuff casse le focus promise.",
    ],
    copy_templates=[
        {"slot": "h1_match_ad", "template": "{Exact_ad_promise_rephrased_max_10pct_diff}", "example": "Ad: 'CRM pour indépendants — 14 jours gratuits' → LP H1: 'Le CRM pensé pour les indépendants — essai 14 jours gratuit'"},
        {"slot": "offer_match", "template": "{Exact_offer_from_ad} · {legal_terms_if_any}", "example": "-30% sur votre première commande · code AUTO appliqué au checkout"},
        {"slot": "persona_match", "template": "Pour les {persona_from_ad}.", "example": "Pour les avocats qui veulent structurer leur cabinet."},
    ],
    anti_patterns=["h1_reformulated_loses_keywords", "visual_different_from_ad", "offer_buried_fold_2"],
    external_refs=[
        "Pirolli P. & Card S. (1995) Information Foraging",
        "CXL Institute (2018) Message Match Research",
        "Festinger L. (1957) A Theory of Cognitive Dissonance",
        "Kahneman D. (2011) Thinking, Fast and Slow — Dual Process",
        "Google Ads (2022) Landing Page Experience Playbook",
    ],
    effort_hours=6,
    priority="P0",
))

PATTERNS.append(mk(
    crit="coh_04",
    pillar="coh",
    pillar_block="bloc_4_coherence_v3.json",
    mech_or_copy="COPY",
    name="Positionnement différenciant + VPC alignment (Jobs/Pains/Gains)",
    summary="Formuler le positionnement via la grille Value Proposition Canvas (Strategyzer) : jobs, pains, gains du persona alignés avec la solution, sans s'aligner sur les concurrents.",
    page_types=["home", "lp_sales", "pdp", "pricing", "comparison", "advertorial", "vsl"],
    why=(
        "Blue Ocean Strategy (Kim & Mauborgne 2005) : un positionnement qui "
        "liste les mêmes features que les concurrents condamne à la guerre "
        "des prix. Un différenciateur clair crée un espace de marché non "
        "contesté. Value Proposition Canvas (Osterwalder 2014) : le produit "
        "se justifie en adressant explicitement les Jobs (ce que le persona "
        "essaie d'accomplir), les Pains (obstacles récurrents), et les Gains "
        "(résultats désirés). Jobs To Be Done Theory (Ulwick 2005, Christensen "
        "2016) : les gens n'achètent pas des produits, ils 'embauchent' des "
        "solutions pour accomplir un progrès. Le positionnement gagnant "
        "nomme le job et le mécanisme uniquement appliqué par la marque. "
        "Anchoring bias (Tversky & Kahneman 1974) : le premier "
        "différenciateur mémorisé sert d'ancre dans toutes les évaluations "
        "ultérieures."
    ),
    do=[
        "Cartographier en interne le VPC : lister 5-7 Jobs, 5-7 Pains, 5-7 Gains du persona prioritaire. Garder uniquement les 2-3 plus élevés en frustration et fréquence.",
        "Formuler le positionnement autour du job + pain max + mécanisme propre : 'Pour les [persona] qui [job], notre [mécanisme unique] élimine [pain principal] et garantit [gain top]'.",
        "Afficher un tableau ou bloc comparatif qui nomme les solutions alternatives (catégories, pas concurrents directs si pas éthique) + le différenciateur propre sur 2-3 critères mesurables.",
        "Utiliser un vocabulaire JTBD spécifique : 'quand je [situation] je veux [motivation] pour [résultat attendu]'.",
        "Sourcer le différenciateur sur une mesure vérifiable : 'seul X a la certification Y', 'unique brevet Z', 'méthodologie publiée dans [journal]'.",
    ],
    dont=[
        "Pas de positionnement 'leader', 'meilleur', 'innovant' — zéro signal discriminant, 100% générique.",
        "Pas de liste de features identique aux concurrents — ça dit 'je suis comme les autres, mais il faut me choisir' (faible).",
        "Pas de comparaison directe avec concurrents nommés sans méthodo transparente (risque légal + faible crédibilité).",
        "Pas de positionnement qui change tous les 6 mois — accumulate positioning debt.",
        "Pas de multi-positionnement selon le canal — une seule promesse centrale, déclinée.",
    ],
    copy_templates=[
        {"slot": "positioning_vpc", "template": "Pour les {persona} qui {job}, notre {mechanism_unique} élimine {pain_max} et garantit {gain_top}.", "example": "Pour les freelances qui facturent internationalement, notre infrastructure de paiement multi-devise élimine les commissions cachées et garantit le virement en 24h ouvrées."},
        {"slot": "jtbd_story", "template": "Quand je {situation}, je veux {motivation} pour {result_expected}.", "example": "Quand je quitte le bureau à 19h, je veux savoir que mon stock sera prêt demain matin pour éviter les réclamations client."},
        {"slot": "diff_measurable", "template": "Seul {brand} {unique_fact} · {proof_link}", "example": "Seul Doctrine a indexé 100% des décisions judiciaires françaises depuis 2019 · voir méthodologie"},
    ],
    anti_patterns=["positioning_generic_leader", "features_list_same_as_competitor", "positioning_changes_too_often"],
    external_refs=[
        "Kim W.C. & Mauborgne R. (2005) Blue Ocean Strategy",
        "Osterwalder A. et al. (2014) Value Proposition Design",
        "Ulwick A. (2005) What Customers Want — Outcome-Driven Innovation",
        "Christensen C. (2016) Competing Against Luck — JTBD theory",
        "Tversky A. & Kahneman D. (1974) Judgment under Uncertainty",
    ],
    effort_hours=12,
    priority="P1",
))

PATTERNS.append(mk(
    crit="coh_05",
    pillar="coh",
    pillar_block="bloc_4_coherence_v3.json",
    mech_or_copy="COPY",
    name="Voice & Tone formalisé et cohérent (grille V&T 4 dimensions)",
    summary="Formaliser une grille Voice & Tone à 4 dimensions (Formel↔Familier, Expert↔Accessible, Sérieux↔Léger, Direct↔Nuancé) appliquée systématiquement sur H1, CTA, FAQ, emails.",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "advertorial", "blog", "email_flow"],
    why=(
        "Voice & Tone Framework (MailChimp 2015, Nielsen Norman 2022) : la "
        "voix est stable (identité de marque), le ton varie avec le contexte "
        "(objection, support, célébration). Une grille formalisée évite la "
        "dérive multi-rédacteurs et active la reconnaissance (≥3 expositions "
        "à une voix distinctive créent une empreinte mnésique — Zajonc 1968, "
        "mere exposure effect). Fluency Heuristic (Reber & Schwarz 1999) : "
        "cohérence = facilité de traitement = crédibilité. Rupture de ton "
        "(H1 corporate + CTA friendly + FAQ professoral) crée une "
        "schizophrénie perçue qui casse la confiance. Baymard (2023) sur "
        "les SaaS B2C : 31% de chute de NPS quand le ton support "
        "ne matche pas le ton marketing. Condition pratique : grille à "
        "4 axes suffit (Formel/Familier, Expert/Accessible, Sérieux/Léger, "
        "Direct/Nuancé) avec position cible (ex: 70/30 Familier, 60/40 "
        "Accessible, etc.) et exemples do/dont par contexte."
    ),
    do=[
        "Formaliser une grille V&T interne à 4 axes avec positionnement cible (ex: 70% Familier, 60% Accessible, 40% Sérieux, 75% Direct).",
        "Lister par contexte (H1, CTA, FAQ, error, success, email onboarding, email retention) 3 exemples DO et 3 DONT.",
        "Tester la cohérence : prendre 5 éléments copy au hasard sur la LP → un lecteur tiers doit identifier qu'ils viennent de la même marque.",
        "Adapter le ton au contexte sans changer la voix : FAQ peut être plus pédagogique que H1, mais le vocabulaire reste le même.",
        "Réviser la grille V&T tous les 6-12 mois après écoute customer calls ou review VoC (voir psy_08).",
    ],
    dont=[
        "Pas de mix FR/EN aléatoire ('Get started' sur LP FR) sauf si positionnement global assumé.",
        "Pas de jargon technique sur la LP si marketing est grand public — schizophrénie V&T.",
        "Pas de ton émoji-heavy sur la LP puis corporate dans les emails de facture — rupture d'identité.",
        "Pas de copy IA-generic (buzzwords) puis copy émotionnel humain sur la même page — signal de template.",
        "Pas de ton urgent ('DÉPÊCHEZ-VOUS !!!') quand la marque est premium/réfléchie — cohérence brand/tonalité.",
    ],
    copy_templates=[
        {"slot": "voice_axis_1_formal_familiar", "template": "{Example_DO_familiar} vs {Example_DONT_formal}", "example": "DO: 'On vous remet tout en place en 2 jours' · DONT: 'Nous procédons à la remise en état sous 48h'"},
        {"slot": "voice_axis_2_expert_accessible", "template": "{Example_DO_accessible} vs {Example_DONT_expert}", "example": "DO: 'Votre trésorerie respire' · DONT: 'Optimisation du BFR et du DSO'"},
        {"slot": "voice_axis_3_serieux_leger", "template": "{Balance}", "example": "Sérieux 60%, Léger 40% : ton bienveillant sans blagues forcées, métaphores concrètes autorisées"},
    ],
    anti_patterns=["voice_mixed_fr_en", "jargon_marketing_mismatch", "tone_urgency_vs_brand_premium"],
    external_refs=[
        "MailChimp (2015) Voice and Tone Style Guide",
        "Nielsen Norman Group (2022) Voice & Tone in UX Writing",
        "Zajonc R. (1968) Attitudinal Effects of Mere Exposure",
        "Reber R. & Schwarz N. (1999) Perceptual Fluency",
        "Baymard Institute (2023) SaaS Customer Tone Consistency Study",
    ],
    effort_hours=16,
    priority="P1",
))

PATTERNS.append(mk(
    crit="coh_08",
    pillar="coh",
    pillar_block="bloc_4_coherence_v3.json",
    mech_or_copy="COPY",
    name="Message Hierarchy explicite (primary / secondary / supporting)",
    summary="Hiérarchiser 3 niveaux de message par page : 1 primary (Jobs/Pain #1), 2-3 secondary (pain/gain secondaires), 4-6 supporting (preuves, features) — éviter l'overstuff.",
    page_types=["home", "lp_sales", "pdp", "lp_leadgen", "pricing", "advertorial", "vsl", "webinar"],
    why=(
        "Pyramid Principle (Minto 1987) : toute communication gagne à être "
        "structurée en pyramide — une idée principale, 2-3 idées secondaires "
        "qui la supportent, 3-5 supports par idée secondaire. Information "
        "Foraging (Pirolli & Card 1995) : les lecteurs scannent d'abord le "
        "niveau 1 (headlines, H2s) avant de décider de plonger dans le corps. "
        "Miller's Law (Miller 1956) : la working memory gère 7±2 items, 3 "
        "sont un seuil confortable. Rule of Three (rhétorique classique, "
        "Aristote) : 3 arguments sont plus persuasifs que 2 ou 4-5. "
        "Cognitive Load Theory (Sweller 1988) : hiérarchie explicite = "
        "charge intrinsèque minimale, le lecteur épargne son énergie mentale "
        "pour l'évaluation des arguments. Les pages sans hiérarchie explicite "
        "('tout est important') sont en réalité des pages où rien n'est "
        "prioritaire → le lecteur décroche."
    ),
    do=[
        "Cartographier avant rédaction : 1 message primary (≤12 mots, le Job/Pain #1), 2-3 secondary (supporting beliefs ou sub-jobs), 4-6 supporting (features, preuves, anecdotes).",
        "Réserver le fold 1 au message primary (H1 + sous-titre + CTA primaire).",
        "Consacrer les folds 2-4 chacun à un secondary (H2 + body + preuve associée).",
        "Utiliser des tailles typographiques qui matérialisent la hiérarchie : H1 > H2 > H3 en ratio ≥1.5× (type scale).",
        "Supprimer les messages qui ne s'inscrivent dans aucun des 3 niveaux — ils diluent la proposition.",
    ],
    dont=[
        "Pas de page 'tout est H1' (5+ headlines de même poids visuel).",
        "Pas de 7+ messages secondary qui saturent — après 3, attrition drastique.",
        "Pas de supporting qui contredit le primary (ex: primary 'simple', supporting 'configurable à l'infini').",
        "Pas de hiérarchie uniquement typographique sans logique narrative — la taille seule ne suffit pas.",
        "Pas de switch de message primary en cours de page — trahit l'absence de stratégie éditoriale.",
    ],
    copy_templates=[
        {"slot": "hierarchy_levels", "template": "Primary: {message_p} · Secondary: {m_s1}, {m_s2}, {m_s3} · Supporting: {m_sup1}-{m_sup6}", "example": "Primary: 'Votre compta prête en 3 clics' · Secondary: Zéro saisie / Export expert-comptable / Conforme FEC · Supporting: IA extraction / 30 templates / TVA automatique / Sauvegarde cloud / API compta / Audit en 1 clic"},
    ],
    anti_patterns=["all_h1_equal_weight", "supporting_contradicts_primary", "hierarchy_typographic_only"],
    external_refs=[
        "Minto B. (1987) The Pyramid Principle",
        "Pirolli P. & Card S. (1995) Information Foraging",
        "Miller G. (1956) The Magical Number Seven, Plus or Minus Two",
        "Sweller J. (1988) Cognitive Load During Problem Solving",
    ],
    effort_hours=8,
    priority="P1",
))

PATTERNS.append(mk(
    crit="coh_09",
    pillar="coh",
    pillar_block="bloc_4_coherence_v3.json",
    mech_or_copy="COPY",
    name="Unique Mechanism nommé (le 'comment' différenciant explicite)",
    summary="Nommer le mécanisme unique (procédé, méthode, techno propriétaire) en 2-4 mots + 1 phrase explicative — transformer une feature en différenciateur mémorisable.",
    page_types=["home", "pdp", "lp_sales", "pricing", "comparison", "advertorial", "vsl", "webinar"],
    why=(
        "Unique Mechanism (Eugene Schwartz 1966, Breakthrough Advertising) : "
        "dans un marché à forte concurrence (Sophistication 4-5), un produit "
        "gagne en nommant SON MÉCANISME propre. Le mécanisme transforme une "
        "promesse courante en promesse brevetée mentalement. Rory Sutherland "
        "(Ogilvy, 2019) : 'Don't sell the feature, sell the mechanism'. "
        "Naming magic (Robertson & Breen 2013) : un nom propre crée un "
        "conteneur cognitif mémorisable (comme 'Formule Double-Action' > "
        "'méthode combinée'). Dual Coding (Paivio 1971) : un nom propre "
        "active à la fois la voie verbale et visuelle (branding associé). "
        "CXL (2020) sur 92 LPs SaaS : LP avec mécanisme nommé = +34% "
        "de conversion médiane vs LP sans. Condition éthique : le mécanisme "
        "doit correspondre à une réalité (procédé documentable, "
        "techno propriétaire, méthode publiée, approche originale)."
    ),
    do=[
        "Identifier le mécanisme propre (ce que vous faites différemment de tous les autres) — pas la feature, le 'comment'.",
        "Lui donner un nom en 2-4 mots, idéalement en FR ou FR+EN hybrid : 'Matching IA 3-niveaux', 'Méthode Double-Impulse', 'Protocole Clear-Start'.",
        "Accompagner le nom d'une phrase explicative de 12-20 mots qui dit ce qu'il fait concrètement.",
        "Le positionner dans le fold 1 ou fold 2 (pas caché dans feature-grid). Typographie distinctive (italique, couleur brand, underline subtil).",
        "Le réutiliser systématiquement dans les preuves, témoignages, FAQ — c'est ce qui en fait un containeur mnésique.",
    ],
    dont=[
        "Pas de nom de mécanisme vague ou buzzword-only : 'Synergie Plus', 'Dynamic Engine' = zéro substance.",
        "Pas de mécanisme si le produit est réellement commoditisé — alors revenir sur le positionnement/VPC (coh_04).",
        "Pas d'utilisation occasionnelle du nom — il doit être récurrent pour devenir container mnésique.",
        "Pas de mécanisme uniquement cité sans explication fonctionnelle — opacité = méfiance.",
        "Pas de 3+ mécanismes simultanés : choisir le plus différenciant, les autres deviennent features supportantes.",
    ],
    copy_templates=[
        {"slot": "mech_named_explained", "template": "Notre {Mechanism_Name} : {what_it_does_in_12_20_words}.", "example": "Notre Matching IA 3-niveaux : nous croisons compétences techniques, soft skills et fit culturel en 30 secondes."},
        {"slot": "mech_section_title", "template": "Comment ça marche : {Mechanism_Name}", "example": "Comment ça marche : Protocole Clear-Start"},
        {"slot": "mech_repeated_in_proof", "template": "Grâce au {Mechanism_Name}, {client_result}.", "example": "Grâce au Protocole Clear-Start, nos clients économisent en moyenne 4h/semaine dès le premier mois."},
    ],
    anti_patterns=["mechanism_buzzword_empty", "mechanism_not_repeated", "too_many_mechanisms"],
    external_refs=[
        "Schwartz E. (1966) Breakthrough Advertising — Unique Mechanism chapter",
        "Sutherland R. (2019) Alchemy: The Surprising Power of Ideas That Don't Make Sense",
        "Robertson & Breen (2013) Naming Magic in Branding",
        "Paivio A. (1971) Imagery and Verbal Processes",
        "CXL Institute (2020) Unique Mechanism Performance Study (92 SaaS LP)",
    ],
    effort_hours=10,
    priority="P0",
))


# =====================================================================
# PER (4 patterns) — Persuasion pillar
# =====================================================================

PATTERNS.append(mk(
    crit="per_07",
    pillar="per",
    pillar_block="bloc_2_persuasion_v3.json",
    mech_or_copy="COPY",
    name="Ton cohérent avec la cible et la catégorie",
    summary="Caler le ton éditorial sur l'archétype de marque et l'attente du persona — le ton d'une marque premium B2B diffère de celui d'une DNVB food d'impulsion.",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "advertorial", "blog", "vsl", "webinar"],
    why=(
        "Archetypes de marque (Mark & Pearson 2001, The Hero and the Outlaw) : "
        "12 archétypes universels (Sage, Rebel, Lover, Hero, etc.) activent "
        "des schémas mentaux différents chez le lecteur. Une LP premium "
        "(Sage/Creator) avec un ton Jester (blagues) détruit la perception de "
        "valeur. Fluency Heuristic (Reber & Schwarz 1999) : ton attendu = "
        "facilité de traitement = crédibilité. Social Identity Theory "
        "(Tajfel & Turner 1981) : le lecteur cherche des signaux "
        "d'appartenance à son tribe (vocabulaire, références culturelles, "
        "niveau de langue). Category Convention Theory (Aaker 1996) : chaque "
        "catégorie a des codes dominants que les leaders respectent et que "
        "les challengers peuvent consciemment casser pour créer du signal. "
        "Mais la rupture doit être choisie, pas subie. Condition pratique : "
        "identifier l'archétype central + adapter lexique, longueur phrase, "
        "registre, rythme. Baymard (2022) : rupture de ton catégorie = "
        "+52% bounce rate en 5s."
    ),
    do=[
        "Identifier l'archétype principal du persona cible : ex. avocats = Sage/Ruler (autorité), DNVB beauté = Lover/Creator (esthétique émotionnelle), SaaS indie = Rebel/Explorer (pragmatique, direct).",
        "Aligner le lexique : B2B tech = vocabulaire pointu + abréviations métier acceptées, DNVB food = vocabulaire sensoriel.",
        "Caler la longueur et rythme des phrases : persona pressé (C-level) = phrases courtes 10-15 mots, persona réflexif (thérapeute) = phrases longues narratives.",
        "Référencer les codes culturels du persona (pas ceux du marketing generic) — argot métier si pertinent, émojis si attendus, sobriété typographique si premium.",
        "Tester avec 5 lecteurs du persona cible : 'Est-ce que c'est pour toi ?' — attention aux réponses floues.",
    ],
    dont=[
        "Pas de ton familier/Jester sur une offre premium/thérapeutique/financière — rupture de perception valeur.",
        "Pas de formel/corporate sur une marque DNVB lifestyle — rupture d'intimité.",
        "Pas de 'tutoyer tout le monde' ou 'vouvoyer tout le monde' sans décision explicite et cohérente avec l'archétype.",
        "Pas d'emprunt aux codes d'un autre persona pour 'faire plus accessible' si ça trahit l'archétype.",
        "Pas de changement de ton en cours de LP (H1 premium, bénéfices DTC 2018, FAQ corporate) — voir coh_05.",
    ],
    copy_templates=[
        {"slot": "tone_sage_b2b", "template": "{Technical_statement_with_metric} — {sourced_claim}.", "example": "Conforme RGPD, ISO 27001 et SOC 2 Type II — audités annuellement par BDO."},
        {"slot": "tone_creator_dnvb", "template": "{Sensory_opening} — {benefit_emotional}.", "example": "Enfin une texture qui fond, pas qui collent — votre peau respire, votre journée aussi."},
        {"slot": "tone_rebel_saas_indie", "template": "{Pain_named_directly} · {solution_pragmatic}.", "example": "Les CRM 'enterprise' vous font perdre 8h/semaine · nous, on vous rend ces heures en 2 clics."},
    ],
    anti_patterns=["tone_jester_on_premium", "tone_corporate_on_lifestyle", "tone_mixed_within_page"],
    external_refs=[
        "Mark M. & Pearson C.S. (2001) The Hero and the Outlaw: Building Extraordinary Brands",
        "Aaker D. (1996) Building Strong Brands — Category Conventions",
        "Tajfel H. & Turner J. (1981) Social Identity Theory of Intergroup Behavior",
        "Reber R. & Schwarz N. (1999) Perceptual Fluency",
        "Baymard Institute (2022) Tone-Category Mismatch Research",
    ],
    effort_hours=10,
    priority="P1",
))

PATTERNS.append(mk(
    crit="per_08",
    pillar="per",
    pillar_block="bloc_2_persuasion_v3.json",
    mech_or_copy="COPY",
    name="Absence de jargon creux / generic AI tone / DTC 2018 template",
    summary="Bannir les expressions creuses (innovant, révolutionnaire, leader, solution all-in-one), les tournures AI-generic, et les templates DTC 2018 (le 'Enfin un X qui...' sans spécificité).",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "advertorial", "blog", "vsl"],
    why=(
        "Semantic Bleaching (linguistique 1980+) : les mots surutilisés "
        "perdent leur charge sémantique. 'Révolutionnaire' en 2026 pèse "
        "moins que 'utile' bien placé. Fluency Heuristic (Reber & Schwarz "
        "1999) : le cerveau détecte les patterns familiers — un copy 100% "
        "buzzwords est catégorisé comme 'générique' en <3s et le lecteur "
        "cesse de lire. Pattern Matching (Gibson 1979) : un cerveau "
        "sur-exposé à des templates les reconnaît instantanément et "
        "déprécie — 'template DTC 2018' = 'enfin X qui change tout' = "
        "signal de copy fait par un junior qui a lu 5 LP de concurrents. "
        "VoC research (Wiebe 2012+) : le copy qui convertit utilise les "
        "mots exacts du client, jamais les mots du marketeur. "
        "Perplexity/Claude AI tone (2024+) : tournures 'in a world where...', "
        "'revolutionary', 'game-changing' sans spécificité = signal de "
        "contenu LLM-generated non édité, perte immédiate de crédibilité."
    ),
    do=[
        "Bannir la liste noire : 'innovant', 'révolutionnaire', 'disruptif', 'all-in-one', 'solution', 'leader', 'premium', 'game-changer', 'next-gen', 'seamless', 'state-of-the-art'.",
        "Remplacer par du concret vérifiable : au lieu de 'solution all-in-one', lister les 3 choses spécifiques que le produit fait ('factures, TVA, export FEC').",
        "Interdire les tournures DTC 2018 générique : 'Enfin un X qui...', 'Conçu pour vous qui...', 'Parce que vous méritez mieux...'.",
        "Interdire les tournures AI-generic : 'In a world where...', 'Welcome to the future of...', 'Discover a new way to...'.",
        "Pour chaque adjectif qualitatif, demander : 'Comment je peux le prouver en 1 phrase ?'. Si pas de preuve → couper.",
        "Utiliser le vocabulaire client (voir psy_08 VoC) — les mots qui viennent des reviews/calls/support tickets.",
    ],
    dont=[
        "Pas de phrases qui auraient pu être écrites pour n'importe quel concurrent de votre catégorie.",
        "Pas de 'superlatifs non sourcés' : 'la meilleure solution' sans étude, 'le plus rapide' sans benchmark.",
        "Pas de copy 'agenticy-style' copié sur les LP de Stripe/Linear sans adapter à votre réalité (vous n'êtes pas Stripe).",
        "Pas de néologisme marketing ('simplement-fication', 'experience-icing') — ça sonne forcé.",
        "Pas de copy en anglais non traduit si marché FR sans positionnement international justifié.",
    ],
    copy_templates=[
        {"slot": "replace_innovant", "template": "{Specific_fact_that_makes_it_new} · {proof}", "example": "Le 1er CRM qui auto-classe vos emails avant que vous les ouvriez · brevet FR 2024-1832"},
        {"slot": "replace_all_in_one", "template": "{Function_1}, {Function_2}, {Function_3} — dans un seul outil.", "example": "Facturation, TVA, et export expert-comptable — dans un seul outil."},
        {"slot": "replace_solution", "template": "{Specific_product_category_word}", "example": "Plateforme de recouvrement > Solution de recouvrement"},
    ],
    anti_patterns=["buzzword_revolutionary", "dtc_2018_template", "ai_generic_tone"],
    external_refs=[
        "Reber R. & Schwarz N. (1999) Perceptual Fluency",
        "Gibson J.J. (1979) The Ecological Approach to Visual Perception",
        "Wiebe J. / Copyhackers (2012+) Voice of Customer research",
        "Claude / Anthropic Prompting Docs (2024) 'Don't mention being an AI' — AI tone signals",
        "Pew Research (2024) AI-Generated Content Detection in the Wild",
    ],
    effort_hours=6,
    priority="P0",
))

PATTERNS.append(mk(
    crit="per_10",
    pillar="per",
    pillar_block="bloc_2_persuasion_v3.json",
    mech_or_copy="COPY",
    name="Structure copy identifiable — framework reconnaissable sur page",
    summary="Adopter un framework copy reconnaissable (AIDA, PAS, PASTOR, 4P, StoryBrand) adapté au page_type et à l'intent — structure > fluency creative.",
    page_types=["lp_leadgen", "lp_sales", "advertorial", "listicle", "vsl", "pdp", "challenge", "webinar", "bundle_standalone", "home"],
    why=(
        "Les frameworks copy (AIDA 1898, PAS 1970s, PASTOR Ray Edwards 2014, "
        "4P Hopkins 1923, StoryBrand Miller 2017) sont des heuristiques "
        "validés par 100+ ans de direct-response advertising. Ils optimisent "
        "la séquence émotion/raison/action pour un page_type donné. Schema "
        "Theory (Bartlett 1932, Rumelhart 1980) : le lecteur reconnaît "
        "inconsciemment la structure, économise de l'effort cognitif, "
        "progresse dans le funnel avec moins de résistance. Narrative "
        "Transport (Green & Brock 2000) : une structure narrative active "
        "la suspension d'esprit critique. Mais un mix incohérent (H1 AIDA "
        "+ body PAS + CTA StoryBrand) crée cognitive dissonance. "
        "Chaque framework matche des intents différents : AIDA = "
        "awareness→action, PAS = problem-aware traffic, PASTOR = sales page "
        "long-form, StoryBrand = brand positioning, 4P = direct response. "
        "Condition : choisir, déployer, conserver."
    ),
    do=[
        "Choisir un framework par page_type/intent : AIDA pour home, PAS pour lp_leadgen problem-aware, PASTOR pour lp_sales long-form, StoryBrand pour home B2B positioning, 4P pour advertorial direct response.",
        "Déployer systématiquement : PAS = Problem (H1+subhero) → Agitate (fold 2-3 pain amplification) → Solution (fold 4+ product) → Proof (témoignages) → CTA.",
        "Signaler explicitement les sections au lecteur : H2 clairs, visuels qui soulignent la progression.",
        "Tenir le framework jusqu'au bout : si AIDA, l'Action doit être le CTA primaire, pas un second CTA obscur.",
        "Vérifier par relecture : est-ce qu'un copywriter tiers reconnaît le framework en 60s ? Si non, il est invisible.",
    ],
    dont=[
        "Pas de mélange aléatoire de 2-3 frameworks dans la même page sans intention — cognitive dissonance.",
        "Pas de framework forcé si inapproprié au page_type (PAS sur une pricing page = grotesque).",
        "Pas de framework sans signal visuel clair — le lecteur scan d'abord, lit ensuite. Les sections doivent être visuellement distinctes.",
        "Pas de copy 'flat' (une suite de paragraphes sans structure identifiable) — pas de framework = chaos structurel.",
        "Pas de framework en surcouche cosmétique (H2s qui nomment les étapes mais body qui dit autre chose).",
    ],
    copy_templates=[
        {"slot": "framework_pas", "template": "P: {problem_headline} | A: {agitate_pain} | S: {solution_reveal} | Proof: {social_proof} | CTA: {action}", "example": "P: 'Vos factures arrivent en retard tous les mois' | A: '32% des freelances ont des impayés chroniques — stress, trésorerie en vrille' | S: 'Notre relance automatique récupère 87% des impayés' | Proof: '2400 freelances récupèrent leurs impayés avec nous' | CTA: 'Testez gratuit 14j'"},
        {"slot": "framework_aida", "template": "Attention: {hook} | Interest: {problem_reframe} | Desire: {outcome_visualization} | Action: {specific_cta}", "example": "A: 'Et si vos commerciaux signaient 2× plus de deals en 3 mois ?' | I: 'Voici ce qui bloque 73% des équipes sales...' | D: 'Imaginez votre pipeline rempli à 180%...' | A: 'Démo personnalisée 30min — créneaux cette semaine'"},
        {"slot": "framework_storybrand", "template": "Hero={customer} | Problem={pain} | Guide={brand} | Plan={3_steps} | Success={outcome} | Failure={stakes}", "example": "Hero: freelance débordé | Problem: compta prend 4h/semaine | Guide: notre app | Plan: 1) connectez banque 2) on catégorise 3) vous exportez | Success: 4h récupérées | Failure: 2000€/an perdus en erreurs"},
    ],
    anti_patterns=["frameworks_mixed_random", "framework_cosmetic_no_substance", "flat_copy_no_structure"],
    external_refs=[
        "Lewis E. (1898) AIDA framework origin",
        "Edwards R. (2014) How to Write Copy That Sells — PASTOR",
        "Miller D. (2017) Building a StoryBrand",
        "Hopkins C. (1923) Scientific Advertising",
        "Bartlett F. (1932) Remembering: A Study in Experimental and Social Psychology",
        "Green M.C. & Brock T.C. (2000) Narrative Transportation",
    ],
    effort_hours=12,
    priority="P1",
))

PATTERNS.append(mk(
    crit="per_11",
    pillar="per",
    pillar_block="bloc_2_persuasion_v3.json",
    mech_or_copy="COPY",
    name="Benefit Laddering profond (functional → emotional → identity, ≥2 niveaux)",
    summary="Remonter les bénéfices sur ≥2 niveaux de l'échelle Means-End Chain : du functional (attribut) vers emotional (ressenti) et si possible identity (qui je suis).",
    page_types=["home", "pdp", "lp_sales", "lp_leadgen", "advertorial", "vsl", "webinar"],
    why=(
        "Means-End Chain Theory (Reynolds & Gutman 1988) : les consommateurs "
        "évaluent les produits sur 3 niveaux d'abstraction — attributs "
        "(features), consequences (functional + emotional), values "
        "(identity, beliefs, self-concept). Les décisions d'achat à haute "
        "valeur sont activées par le niveau identity ('le parent qui nourrit "
        "sainement', 'l'entrepreneur qui refuse le SAAS overcomplex'). "
        "Laddering Interview Technique (Gutman 1982) : chaque attribut peut "
        "être 'monté' via 'Et alors ? Qu'est-ce que ça change pour toi ?'. "
        "Self-Concept Theory (Rosenberg 1979) : les achats cohérents avec "
        "l'identité perçue ont des taux de conversion et rétention "
        "supérieurs. Brand Love (Batra et al. 2012) : connexion "
        "identité → marque = NPS, LTV, parrainage. Condition pratique : "
        "attention aux cibles premium/conviction où identity >> functional, "
        "vs commodités où functional >> identity. Toujours au moins 2 "
        "niveaux visibles pour activer Système 1 (émotionnel) ET Système 2 "
        "(rationnel)."
    ),
    do=[
        "Pour chaque feature principale, rédiger la chaîne complète : Attribute → Functional benefit → Emotional benefit → Identity benefit.",
        "Choisir pour la LP le ou les 2 niveaux les plus puissants selon persona : B2B SaaS technique = Functional + Emotional ('gagnez 4h/semaine — enfin du temps pour votre famille'). DNVB premium = Emotional + Identity ('respecter votre peau, c'est respecter qui vous êtes').",
        "Placer le benefit identity dans le fold 1 ou fold 2 si la marque assume son positionnement identitaire.",
        "Formuler de manière à activer le self-concept du persona : pas 'devenez quelqu'un de meilleur' (manipulateur) mais 'soyez cohérent avec la personne que vous êtes déjà'.",
        "Tester laddering : demander à 3 clients existants 'Qu'est-ce que [produit] vous permet de faire ?' puis 'Et pourquoi c'est important pour vous ?'. Remonter jusqu'à atteindre un value statement.",
    ],
    dont=[
        "Pas de features-only (attribute level) — ça ne crée pas d'engagement émotionnel, rétention faible.",
        "Pas d'identity-only sans functional — 'soyez une meilleure version de vous' sans 'comment' = woo-woo, crédibilité nulle.",
        "Pas de laddering incohérent entre H1 (identity) et pricing (functional/feature) — dissonance.",
        "Pas de laddering manipulateur qui promet une transformation identitaire impossible ('devenez millionnaire') — éthique et crédibilité.",
        "Pas de saut direct attribute → identity sans passer par functional/emotional — le lecteur ne peut pas suivre le sens.",
    ],
    copy_templates=[
        {"slot": "ladder_full_chain", "template": "{attribute} → {functional_benefit} → {emotional_benefit} → {identity_benefit}", "example": "Notre IA auto-classe vos emails → vous gagnez 2h/jour → vous terminez le travail à 18h, pas 20h → vous êtes ce parent qui dîne avec ses enfants."},
        {"slot": "ladder_two_levels", "template": "{functional_benefit} · {emotional_or_identity}", "example": "Compta prête en 3 clics · retrouvez vos weekends."},
        {"slot": "ladder_identity_first", "template": "Pour les {identity_persona} qui refusent {compromise}.", "example": "Pour les parents qui refusent de choisir entre santé et simplicité."},
    ],
    anti_patterns=["features_only_no_benefit", "identity_only_no_functional", "ladder_manipulative"],
    external_refs=[
        "Reynolds T.J. & Gutman J. (1988) Laddering Theory, Method, Analysis, and Interpretation",
        "Gutman J. (1982) A Means-End Chain Model Based on Consumer Categorization Processes",
        "Rosenberg M. (1979) Conceiving the Self",
        "Batra R., Ahuvia A. & Bagozzi R. (2012) Brand Love",
        "Maslow A. (1954) Motivation and Personality — hierarchy of needs",
    ],
    effort_hours=10,
    priority="P1",
))


# =====================================================================
# UX (6 patterns) — UX pillar — MECH-heavy, requires layout_directives
# =====================================================================

PATTERNS.append(mk(
    crit="ux_01",
    pillar="ux",
    pillar_block="bloc_3_ux_v3.json",
    mech_or_copy="MECH",
    name="Hiérarchie visuelle claire (H1 unique > H2 > H3, type scale cohérente)",
    summary="Établir une hiérarchie typographique stricte (1 H1 par page, H2 ≥1.5× H3, type scale 1.25 mini) en desktop et mobile, avec contrast AA sur chaque niveau.",
    page_types=["*"],
    why=(
        "Gestalt Principles (Wertheimer 1923) : la loi de similarité et de "
        "proximité font émerger la structure dès le pré-attentive processing "
        "(<200ms). Type Scale (Robert Bringhurst 1992, The Elements of "
        "Typographic Style) : un ratio typographique ≥1.25 (idéalement "
        "1.333 Perfect Fourth ou 1.5) crée une hiérarchie perçue comme "
        "cohérente et professionnelle. Visual Hierarchy Research "
        "(Nielsen Norman 2020) : l'absence de hiérarchie visuelle force le "
        "lecteur à lire linéairement (fatigue) au lieu de scanner (efficace). "
        "Baymard (2023) : 91% des utilisateurs scannent avant de lire, une "
        "hiérarchie typographique faible augmente de +35% le temps pour "
        "trouver l'info principale. HTML Semantic (W3C ARIA) : H1 unique "
        "pour SEO et accessibilité (screen readers naviguent par headings). "
        "Cognitive Load (Sweller 1988) : charge intrinsèque minimale quand "
        "la structure est évidente."
    ),
    do=[
        "1 seul H1 par page, au niveau du hero. Tous les autres titres sont H2, H3, H4 selon l'emboîtement logique.",
        "Type scale mini 1.25 (Major Third) entre niveaux : ex. H1 48px, H2 36px, H3 28px, H4 20px, body 16px (desktop).",
        "Adapter la type scale au mobile avec facteur 0.75 : H1 36px, H2 28px, H3 22px, H4 18px, body 16px.",
        "Weight hierarchy : H1 700 (bold), H2 600 (semibold), H3 500 (medium), body 400 (regular).",
        "Contrast AA minimum sur chaque niveau (4.5:1 body, 3:1 large text ≥18px ou 14px bold).",
        "Espacement hiérarchique : margin-top H2 ≥32px, H3 ≥24px, body paragraphs ≥16px.",
    ],
    dont=[
        "Jamais 2 H1 sur une même page — casse SEO et structure a11y.",
        "Pas de H1 en dessous de 32px desktop / 28px mobile.",
        "Pas de H2 et H3 quasi-identiques en taille (écart <20%).",
        "Pas de body text <16px — en dessous, lisibilité dégradée (Nielsen Norman 2020).",
        "Pas de titres en grisé low-contrast (ex: #999 sur blanc = 2.8:1 = non-AA).",
    ],
    copy_templates=[
        {"slot": "type_scale_desktop", "template": "H1 {size_h1} · H2 {size_h2} · H3 {size_h3} · body {size_body}", "example": "H1 48px · H2 36px · H3 28px · body 16px — ratio 1.333 (Perfect Fourth)"},
        {"slot": "type_scale_mobile", "template": "H1 {size_h1_m} · H2 {size_h2_m} · H3 {size_h3_m} · body 16px", "example": "H1 36px · H2 28px · H3 22px · body 16px"},
    ],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "type_scale": {"h1": "48px", "h2": "36px", "h3": "28px", "h4": "20px", "body": "16px", "ratio": "1.333 Perfect Fourth"},
                "weights": {"h1": 700, "h2": 600, "h3": 500, "body": 400},
                "spacing": {"h2_margin_top": "48px", "h3_margin_top": "32px", "paragraph_spacing": "16px"},
                "contrast_min": "4.5:1 body, 3:1 large text",
            },
            "mobile": {
                "canvas": "390x844",
                "type_scale": {"h1": "36px", "h2": "28px", "h3": "22px", "h4": "18px", "body": "16px", "ratio": "0.75 mobile factor"},
                "weights": {"h1": 700, "h2": 600, "h3": 500, "body": 400},
                "spacing": {"h2_margin_top": "32px", "h3_margin_top": "24px", "paragraph_spacing": "16px"},
                "contrast_min": "4.5:1 body, 3:1 large text",
                "body_minimum": "16px (Apple HIG + Material)",
            },
        },
        "dom_constraints": {
            "h1_count": 1,
            "heading_levels_sequential": True,
            "semantic_html": "h1, h2, h3, h4 tags required, no <div class='h1'>",
        },
    },
    anti_patterns=["multiple_h1", "h2_h3_same_size", "low_contrast_headings"],
    external_refs=[
        "Wertheimer M. (1923) Laws of Organization in Perceptual Forms (Gestalt)",
        "Bringhurst R. (1992) The Elements of Typographic Style",
        "Nielsen Norman Group (2020) How Users Read on the Web",
        "W3C ARIA (2023) Heading Levels Guidance",
        "WCAG 2.1 (2018) Contrast Requirements",
        "Sweller J. (1988) Cognitive Load During Problem Solving",
    ],
    effort_hours=8,
    priority="P0",
))

PATTERNS.append(mk(
    crit="ux_02",
    pillar="ux",
    pillar_block="bloc_3_ux_v3.json",
    mech_or_copy="MECH",
    name="Rythme de page (alternance dense/aéré, sections délimitées)",
    summary="Alterner sections denses et aérées selon un rythme 1-2-1 (impact/développement/impact), utiliser des dividers visuels (couleur de fond, spacing) tous les 2-3 folds.",
    page_types=["*"],
    why=(
        "Gestalt Proximity Law (Wertheimer 1923) : les éléments proches sont "
        "perçus comme un groupe, ceux éloignés comme distincts. Le rythme de "
        "page exploite ce principe pour signaler les sections. Scroll "
        "Depth Research (Chartbeat 2013, mis à jour Baymard 2022) : les "
        "pages avec rythme visuel (alternance fond clair/foncé, sections "
        "distinctes) ont 2.3× plus de scroll-to-bottom que les pages plates. "
        "Cognitive Chunking (Miller 1956) : la working memory traite "
        "mieux 3-5 'gros morceaux' qu'une suite linéaire sans pause. "
        "Reading Fatigue (Nielsen Norman 2020) : les pages plates sans "
        "changement de rythme déclenchent la fatigue à 600-800px de scroll. "
        "Design System Principle (Apple HIG, Material Design) : les pages "
        "bien rythmées paraissent 'premium', celles qui sont plates "
        "paraissent 'amateur'. Condition : ne pas confondre rythme "
        "(différence entre sections) et chaos (toutes les sections "
        "différentes)."
    ),
    do=[
        "Alterner sections denses (liste de features, comparison) et aérées (témoignage avec photo grande, CTA isolé) dans un rythme 1-2-1 ou 1-1-2-1.",
        "Matérialiser chaque section par un changement visible : couleur de fond subtile (#FAFAFA ↔ #FFFFFF), spacing vertical ≥80-120px desktop / ≥48px mobile, séparateur graphique optionnel.",
        "Limiter à 5-7 sections principales par LP (au-delà, attrition + chaos).",
        "Alterner density : si la section N est text-heavy, la N+1 doit être visuelle (image, chart, quote isolée).",
        "Respecter un rythme descendant : sections les plus chargées en début de page, les plus aérées vers le bas.",
    ],
    dont=[
        "Pas de 10+ sections identiques (même layout, même density) — la page devient une bouillie visuelle.",
        "Pas de 3 sections consécutives denses (features grid × 3) sans pause visuelle.",
        "Pas d'alternance couleur de fond criardes (violet → jaune → vert) — le rythme devient migraine.",
        "Pas de spacing vertical <32px desktop entre sections — elles fusionnent.",
        "Pas de mix de templates visuels sans cohérence (section 1 Material, section 2 Tailwind default, section 3 custom) — chaos.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "section_padding_vertical": "96-128px",
                "section_max_width": "1200px centered",
                "rhythm_pattern": "1-2-1 dense/aéré/impact or 1-1-2-1",
                "background_alternation": "#FFFFFF ↔ #FAFAFA ↔ brand_soft",
                "max_sections_principales": 7,
            },
            "mobile": {
                "canvas": "390x844",
                "section_padding_vertical": "56-72px",
                "section_full_width": True,
                "rhythm_same_but_compressed": True,
                "background_alternation": "same as desktop",
                "max_sections_principales": 7,
            },
        },
        "dom_constraints": {
            "section_tag": "<section> with aria-labelledby preferred over <div>",
            "divider_visible": "CSS background-color or border-top 1px",
        },
    },
    anti_patterns=["sections_all_same_density", "chaos_template_mix", "background_alternation_garish"],
    external_refs=[
        "Wertheimer M. (1923) Gestalt Laws",
        "Chartbeat (2013) Scroll Depth Analysis (updated Baymard 2022)",
        "Nielsen Norman Group (2020) Reading Fatigue on Long Pages",
        "Apple Human Interface Guidelines (2024) Rhythm and Pacing",
        "Material Design 3 (2024) Density Guidance",
        "Miller G. (1956) Magical Number Seven",
    ],
    effort_hours=10,
    priority="P1",
))

PATTERNS.append(mk(
    crit="ux_03",
    pillar="ux",
    pillar_block="bloc_3_ux_v3.json",
    mech_or_copy="MECH",
    name="Scan-ability + pattern de lecture adapté au page_type",
    summary="Appliquer F-pattern (contenus long-form, blog, advertorial) ou Z-pattern (landing pages courtes, hero+CTA) selon le page_type, avec alignement strict des éléments critiques.",
    page_types=["*"],
    why=(
        "Eye-tracking research (Nielsen Norman Group 2006, 2017 update) : "
        "91% des users scannent au lieu de lire. Deux patterns dominants : "
        "F-Pattern (pages text-heavy, blog, advertorial) — le lecteur "
        "balaie horizontalement en haut, puis lignes plus courtes en "
        "descendant, enfin scan vertical le long du bord gauche. Z-Pattern "
        "(landing pages courtes, logos, hero+CTA) — regard en diagonale "
        "du haut gauche au bas droite. Placer les éléments critiques "
        "(H1, CTA, social proof, preuve) sur le chemin du pattern "
        "correspondant augmente la probabilité qu'ils soient vus. "
        "Saccadic Reading (Rayner 1998) : l'œil fait des sauts de 7-9 "
        "caractères, les fixations durent 200-250ms. Les éléments en "
        "dehors des points de fixation naturels sont ignorés en scan. "
        "Adapter le pattern au page_type : LP courte = Z, long-form = F, "
        "pricing = tableau F-modifié, PDP e-comm = F avec zone image "
        "gauche. Erreur courante : imposer Z à une page long-form ou "
        "F à un hero court, sans aligner les éléments critiques."
    ),
    do=[
        "Pour LP courte / hero+CTA / logos : Z-pattern. Placer H1 en haut gauche, visuel ou 2e H1 en haut droite, sous-arguments au milieu, CTA en bas droite.",
        "Pour long-form / advertorial / listicle / blog : F-pattern. H1 en haut (barre horizontale du F), H2 secondaires espacés (barres intermédiaires), barre verticale gauche (début de chaque paragraphe) doit contenir les keywords.",
        "Pour pricing : tableau F avec titres lignes à gauche, colonnes plans alignées, CTA en bas de chaque colonne.",
        "Pour e-commerce PDP : image produit à gauche (zone de fixation primaire), copy + CTA à droite, reviews en dessous.",
        "Aligner les éléments critiques (CTA, prix, social proof) sur les points de fixation du pattern : haut gauche, milieu droit, bas droite pour Z.",
    ],
    dont=[
        "Pas de F-pattern sur une LP courte (hero + 3 folds) — le pattern suppose un long texte.",
        "Pas de Z-pattern sur une page text-heavy — l'œil ne peut pas faire de Z sur 3000 mots.",
        "Pas de CTA primaire en bas gauche (dead zone dans les 2 patterns).",
        "Pas d'éléments critiques dispersés aléatoirement hors des points de fixation.",
        "Pas d'alignement centré systématique pour tout (crée un axe vertical central qui casse F et Z).",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "z_pattern": {
                    "top_left": "H1 + sous-titre",
                    "top_right": "visuel hero OR secondary H1 (e.g. logo bar)",
                    "middle_diagonal": "bénéfices/preuves distribués",
                    "bottom_right": "CTA primaire",
                },
                "f_pattern": {
                    "top_bar": "H1 + sous-titre (full width)",
                    "intermediate_bars": "H2 toutes les 300-400px vertical",
                    "left_column": "keywords/bullet starts à l'alignement gauche",
                    "cta_placement": "aligné gauche après chaque argument majeur",
                },
            },
            "mobile": {
                "canvas": "390x844",
                "pattern": "linear scroll, moins pattern-dependent",
                "critical_element_spacing": "1 critical element per 500-700px scroll",
                "cta_repetition": "sticky bottom + inline repeated every 2-3 folds",
            },
        },
        "dom_constraints": {
            "semantic_reading_order": "DOM order must match visual reading order",
            "tab_order": "tabindex natural (no positive tabindex values)",
        },
    },
    anti_patterns=["cta_in_dead_zone", "all_centered_breaks_pattern", "pattern_mismatch_page_type"],
    external_refs=[
        "Nielsen Norman Group (2006) F-Shaped Pattern for Reading Web Content",
        "Nielsen Norman Group (2017) Revisiting F-Pattern for Content",
        "Rayner K. (1998) Eye Movements in Reading and Information Processing",
        "Pernice K. (2017) Z-Pattern Reading in Web Content",
        "Sharpe W. (2015) Designing for the Eye",
    ],
    effort_hours=8,
    priority="P1",
))

PATTERNS.append(mk(
    crit="ux_06",
    pillar="ux",
    pillar_block="bloc_3_ux_v3.json",
    mech_or_copy="MECH",
    name="Navigation non-parasite sur LP (focus mono-objectif)",
    summary="Sur les LP dédiées paid traffic (lp_leadgen, lp_sales, quiz_vsl, squeeze, advertorial), supprimer ou restreindre la navigation principale — ne laisser qu'un CTA primaire.",
    page_types=["pdp", "lp_leadgen", "lp_sales", "quiz_vsl", "squeeze", "vsl", "advertorial", "listicle", "challenge", "thank_you_page", "webinar"],
    why=(
        "Attention is a Resource (Kahneman 1973) : chaque lien supplémentaire "
        "dans un menu coûte une décision cognitive. Hick's Law (Hick 1952, "
        "Hyman 1953) : le temps de décision augmente logarithmiquement avec "
        "le nombre d'options. Sur une LP orientée conversion, le menu "
        "standard (5-8 liens) est un leak funnel majeur. Unbounce (2019) "
        "étude sur 71 LP SaaS : LP avec menu complet = 22% de baisse de CVR "
        "vs LP sans menu. Google Ads Landing Page Experience (2022) : les "
        "LP 'distraction-free' scorent mieux en Quality Score. "
        "Direct-response tradition (Dan Kennedy, John Caples) : 'one page, "
        "one promise, one action'. Condition : la home et les pages de "
        "contenu (blog, PDP e-comm) peuvent et doivent conserver la nav — "
        "c'est uniquement pour les LP dédiées paid/campaign que le menu doit "
        "être supprimé ou simplifié à 1-3 liens critiques (souvent : logo "
        "non cliquable, trust badges, ou simplement logo seul)."
    ),
    do=[
        "Sur lp_leadgen, lp_sales, squeeze, quiz_vsl, advertorial, vsl : supprimer le menu standard OU le remplacer par un header minimaliste (logo + 1 CTA secondaire 'Contact' ou 'FAQ').",
        "Si logo, le laisser non-cliquable OU pointant vers la home dans un new tab (pas de back-button trap).",
        "Sur challenge / webinar : pas de nav, juste logo + countdown ou progress indicator.",
        "Sur thank_you_page : pas de nav, focus sur next-step (upsell, social share, agenda).",
        "Sur PDP e-comm : nav allégée (catégories principales + recherche + panier), pas de blog/about/carreer.",
        "Footer LP : minimal (légal + contact), pas de 'sitemap' complet qui réinjecte 30 liens.",
    ],
    dont=[
        "Jamais de menu complet (5-8 liens) sur lp_leadgen, lp_sales, squeeze — leak funnel démontré.",
        "Pas de mega-menu avec catégories produits sur une LP paid dédiée à 1 produit.",
        "Pas de footer 'copié de la home' avec newsletter signup + 40 liens — distrait du CTA primaire.",
        "Pas de 'Back to home' button visible — invite à quitter la LP.",
        "Pas d'exit-intent popup agressif qui casse le focus mono-action (sauf si c'est l'objectif ultime).",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "nav_header": {
                    "lp_dedicated": "Logo LEFT (non-clickable OR new tab) + Optional 1 CTA RIGHT (secondary, e.g. 'Parler à un expert')",
                    "home_or_pdp": "Nav standard (5-8 links max)",
                },
                "footer": {
                    "lp_dedicated": "Minimal: mentions légales, CGV, contact · no sitemap",
                    "home_or_pdp": "Full footer with links, newsletter",
                },
            },
            "mobile": {
                "canvas": "390x844",
                "nav_header": {
                    "lp_dedicated": "Logo only (centered or left), no hamburger menu on LP-dedicated",
                    "home_or_pdp": "Hamburger menu",
                },
            },
        },
        "dom_constraints": {
            "exit_intent_popup": "Allowed only if aligned with primary goal (e.g. lead capture), with clear close button",
            "back_button": "Navigate to previous page naturally (no trap)",
        },
    },
    anti_patterns=["full_menu_on_lp_dedicated", "footer_overstuffed", "exit_intent_aggressive"],
    external_refs=[
        "Kahneman D. (1973) Attention and Effort",
        "Hick W.E. (1952) On the Rate of Gain of Information",
        "Unbounce (2019) Conversion Benchmark Report — Nav Impact",
        "Google Ads (2022) Landing Page Experience Guide",
        "Kennedy D. (2006) The Ultimate Sales Letter",
        "Caples J. (1932, 1997 rev.) Tested Advertising Methods",
    ],
    effort_hours=4,
    priority="P0",
))

PATTERNS.append(mk(
    crit="ux_07",
    pillar="ux",
    pillar_block="bloc_3_ux_v3.json",
    mech_or_copy="MECH",
    name="Micro-interactions guidantes (hover states, sticky, progress, feedback)",
    summary="Activer un set cohérent de micro-interactions qui guident la lecture et rassurent sur l'état du système (hover sur CTA, sticky CTA mobile, progress bar sur quiz, feedback instant sur form).",
    page_types=["*"],
    why=(
        "Feedback Principle (Norman 1988, The Design of Everyday Things) : "
        "chaque action de l'utilisateur doit produire un feedback <100ms "
        "sinon la sensation de contrôle s'effondre. Micro-interactions "
        "(Saffer 2013) : petites interactions ciblées qui augmentent la "
        "satisfaction et la perception de qualité. Fitts's Law (Fitts 1954) : "
        "le temps pour atteindre un target dépend de sa taille et distance — "
        "les hover states agrandis / highlights facilitent le ciblage. "
        "Progress Indicator Research (Nielsen Norman 2019) : les users "
        "tolèrent 2× plus d'attente quand un progress visible existe. "
        "Form Usability (Baymard 2023) : form field feedback instant "
        "(validation inline, error immédiat) = +17% completion. "
        "Attention : micro-interactions excessives = distraction "
        "(Norman 2023 addendum). Condition : chaque interaction doit "
        "avoir un but fonctionnel, pas ornemental."
    ),
    do=[
        "Hover state sur CTA principal : background color darken 10-15%, scale 1.02-1.05, transition 150-200ms ease-out.",
        "Sticky CTA bottom-bar mobile sur LP conversion (fold 2+), avec safe-area-inset-bottom.",
        "Progress bar visible sur quiz/form multi-step (Étape 2/4) — barrière hrologique.",
        "Inline form validation : vert check dès que le champ est valide, rouge + message explicite sinon.",
        "Loading state sur CTA submit : spinner + 'En cours…' — empêche double-click et rassure.",
        "Micro-feedback sur interactions secondaires : accordion opening, tab switch, filter apply (300-400ms max).",
    ],
    dont=[
        "Pas d'animations >500ms sur interactions critiques — ralentit la perception de réactivité.",
        "Pas de parallax ou animations complexes qui coûtent en CLS/INP (Core Web Vitals).",
        "Pas de sticky CTA mobile si déjà 2 CTA visibles dans le viewport (cannibalisation).",
        "Pas de micro-interactions ornementales (bouton qui flotte sans but, fondu aléatoire) — distrait.",
        "Pas de hover state invisible/ambigu — confusion état actif vs passif.",
        "Pas d'animation au scroll sur mobile bas de gamme — perf dégradée.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "cta_hover": {"bg_darken_pct": 12, "scale": 1.03, "transition": "180ms ease-out"},
                "form_inline_validation": {"success_color": "#16a34a", "error_color": "#dc2626", "timing": "onBlur + onInput debounced 300ms"},
                "sticky_elements": "Sticky side CTA acceptable after fold 2 if not already visible",
            },
            "mobile": {
                "canvas": "390x844",
                "sticky_cta_bottom_bar": {
                    "position": "fixed bottom: 0",
                    "height": "56-64px",
                    "z_index": 9999,
                    "padding_bottom": "env(safe-area-inset-bottom)",
                    "show_after_scroll": "300-400px or 1 fold",
                    "hide_if_primary_cta_visible": True,
                },
                "progress_bar": {
                    "position": "top sticky or inline",
                    "height": "4-6px",
                    "color": "brand",
                    "animation": "width transition 400ms ease-out on step change",
                },
                "tap_feedback": "haptic if available OR visual ripple 200ms",
            },
        },
        "dom_constraints": {
            "aria_live": "polite or assertive on form validation feedback",
            "cla_impact": "avoid layout shifts >0.1 on micro-interactions",
            "inp_target": "<200ms response on interaction",
        },
    },
    anti_patterns=["animation_too_slow", "parallax_heavy_cls", "ornamental_micro_interactions"],
    external_refs=[
        "Norman D. (1988, 2013 rev.) The Design of Everyday Things",
        "Saffer D. (2013) Microinteractions: Designing with Details",
        "Fitts P.M. (1954) The Information Capacity of the Human Motor System",
        "Nielsen Norman Group (2019) Progress Indicators",
        "Baymard Institute (2023) Form Usability Benchmark",
        "Google Core Web Vitals (2024) INP/CLS Thresholds",
    ],
    effort_hours=12,
    priority="P1",
))

PATTERNS.append(mk(
    crit="ux_08",
    pillar="ux",
    pillar_block="bloc_3_ux_v3.json",
    mech_or_copy="MECH",
    name="Friction minimisée — 5 types (cognitive, émotionnelle, fonctionnelle, de confiance, technique)",
    summary="Auditer et réduire les 5 types de friction : cognitive (trop de décisions), émotionnelle (doute/peur), fonctionnelle (UX broken), de confiance (trust signals manquants), technique (perf, bugs).",
    page_types=["lp_leadgen", "checkout", "pricing", "pdp", "quiz_vsl", "squeeze", "webinar", "thank_you_page"],
    why=(
        "Friction Cost Theory (Thaler & Sunstein 2008, Nudge) : chaque "
        "friction dans un parcours de conversion réduit la probabilité de "
        "completion — les gains viennent plus d'enlever des obstacles que "
        "d'ajouter des incitations. Baymard Cart Abandonment Study (2023) : "
        "69.9% taux moyen d'abandon e-comm, cause #1 = coûts surprises "
        "(friction confiance), #2 = création compte obligatoire (friction "
        "fonctionnelle), #3 = process checkout trop long (friction "
        "cognitive). 5 types de friction (modèle étendu Nir Eyal 2019 + "
        "CXL 2022) : (1) cognitive (choix paradox, overload info), "
        "(2) émotionnelle (anxiété, doute, peur de mauvais choix), "
        "(3) fonctionnelle (form 15 champs, parcours cassé, dead-end), "
        "(4) de confiance (pas de HTTPS visible, pas de reviews, "
        "policies peu claires), (5) technique (LCP >3s, INP >200ms, "
        "layout shift). Condition : audit systématique par type, "
        "quick-wins sur technique/fonctionnelle avant d'investir en "
        "UX recherche approfondie."
    ),
    do=[
        "Cognitive : max 3 options simultanées par décision (Hick's Law), zéro choix paradoxal (trop de plans tarifaires identiques).",
        "Émotionnelle : risk reversal visible (voir psy_04), FAQ sur les objections principales (voir per_06), témoignages préalables au CTA.",
        "Fonctionnelle : formulaires ≤5 champs sur lead gen, pas d'email obligatoire avant d'avoir montré de la valeur, checkout en ≤3 étapes.",
        "De confiance : HTTPS (tech_05), trust badges discrets (paiement sécurisé, labels, reviews), mentions légales et CGV accessibles.",
        "Technique : LCP <2.5s (tech_01), INP <200ms, CLS <0.1, zéro bug bloquant, responsive sans scroll horizontal.",
    ],
    dont=[
        "Pas de formulaire à 10+ champs sur un lead magnet gratuit — friction disproportionnée.",
        "Pas de checkout 5+ étapes sans upside — Baymard montre chute à chaque étape.",
        "Pas de compte obligatoire pour un achat one-time (option guest checkout).",
        "Pas de frais cachés qui apparaissent à la dernière étape — cause #1 d'abandon.",
        "Pas de captcha agressif sur un form simple — zéro confiance + friction.",
        "Pas de redirection inattendue (ouvre un nouveau tab sans avertir) — casse le flow.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "form_field_max_count": {"lead_gen": 5, "checkout": 8, "signup_saas": 3},
                "decision_points_per_page": 3,
                "checkout_steps_max": 3,
            },
            "mobile": {
                "canvas": "390x844",
                "form_field_max_count": {"lead_gen": 4, "checkout": 7, "signup_saas": 3},
                "single_column_forms": True,
                "autocomplete_enabled": True,
                "input_type_specific": "email, tel, number, url for proper keyboard",
            },
        },
        "dom_constraints": {
            "form_validation_inline": True,
            "labels_above_inputs": True,
            "autofill_attributes": "name, email, tel, address-level1, postal-code (WHATWG spec)",
            "security_visible": "HTTPS padlock, trust badges near CTA on checkout",
        },
    },
    anti_patterns=["form_overstuffed", "hidden_fees", "account_required_for_guest_purchase", "aggressive_captcha"],
    external_refs=[
        "Thaler R. & Sunstein C. (2008) Nudge: Improving Decisions About Health, Wealth, and Happiness",
        "Baymard Institute (2023) Cart Abandonment Rate Study",
        "Eyal N. (2019) Indistractable — Friction Framework",
        "CXL Institute (2022) 5 Types of Friction Research",
        "Hick W.E. (1952) On the Rate of Gain of Information",
        "Google Core Web Vitals (2024) LCP/INP/CLS thresholds",
    ],
    effort_hours=16,
    priority="P0",
))


# =====================================================================
# TECH (5 patterns) — Tech pillar — fully MECH, core web vitals + SEO + A11y
# =====================================================================

PATTERNS.append(mk(
    crit="tech_01",
    pillar="tech",
    pillar_block="bloc_6_tech_v3.json",
    mech_or_copy="MECH",
    name="Performance — Core Web Vitals (LCP <2.5s, INP <200ms, CLS <0.1)",
    summary="Atteindre les seuils 'Good' Core Web Vitals : LCP <2.5s, INP <200ms, CLS <0.1 en P75 — condition d'indexation et de conversion (chaque 100ms LCP = -1% CVR Google).",
    page_types=["*"],
    why=(
        "Core Web Vitals (Google, 2020 → présent) : LCP (Largest Contentful "
        "Paint) mesure le temps d'affichage du plus gros élément (hero image "
        "ou H1), INP (Interaction to Next Paint, remplace FID en 2024) "
        "mesure la réactivité à l'interaction, CLS (Cumulative Layout Shift) "
        "mesure la stabilité visuelle. Google utilise CWV comme ranking "
        "signal depuis 2021. CVR Impact (Amazon 2006, Akamai 2017, Google "
        "2023) : chaque 100ms de latence LCP coûte ~1% de CVR e-commerce. "
        "Deloitte (2020) : 0.1s d'amélioration = +8% page views, +10% "
        "engagement. Condition pratique : mesurer en P75 avec real user "
        "monitoring (Chrome UX Report), pas en lab. Mobile faible connexion "
        "= worst case. Les 3 vitals sont liés : image hero mal optimisée = "
        "LCP lent ET CLS élevé (reflow). JavaScript mal chargé = INP dégradé."
    ),
    do=[
        "LCP : hero image optimisée (WebP ≤150KB, lazy sauf hero, preload sur hero, srcset responsive), minifier CSS critique inline, HTTP/2 ou /3.",
        "INP : splitter les JS bundles (route-based chunks), limiter long tasks (>50ms) dans le main thread, offload heavy compute en Web Worker.",
        "CLS : reserver space aux images (width/height attributes or aspect-ratio CSS), éviter injection contenu above-fold, fonts avec size-adjust / font-display swap.",
        "Utiliser <link rel='preconnect'> pour CDN critiques (fonts, analytics), <link rel='preload'> pour hero image/font.",
        "Mesurer en prod : Real User Monitoring (Vercel Analytics, Sentry, Google Search Console CWV report).",
    ],
    dont=[
        "Pas d'images hero non optimisées (JPEG 800KB), pas de lazy-loading sur l'image LCP.",
        "Pas de tracker analytics chargés synchronously dans <head> — bloque le LCP.",
        "Pas d'animations qui provoquent layout shift sur scroll.",
        "Pas de Google Fonts sans font-display: swap — FOIT bloque le rendering.",
        "Pas de DOM >1500 nodes sur une page simple — coûte en INP et LCP.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "lcp_target": "<2.5s",
                "inp_target": "<200ms",
                "cls_target": "<0.1",
                "hero_image_max_size": "150KB WebP",
                "preload_resources": "hero image, brand font woff2",
            },
            "mobile": {
                "canvas": "390x844",
                "lcp_target": "<2.5s on 4G Slow profile",
                "inp_target": "<200ms",
                "cls_target": "<0.1",
                "hero_image_max_size": "80KB WebP",
                "js_bundle_max_kb": "200KB initial gzipped",
            },
        },
        "dom_constraints": {
            "img_width_height": "required on all images (prevent CLS)",
            "font_display": "swap (not block, not optional)",
            "tracking_scripts": "async or defer, never sync in <head>",
            "dom_node_count": "<1500 ideal, <3000 max",
        },
    },
    anti_patterns=["hero_unoptimized_large", "sync_analytics_head", "no_font_display_swap", "layout_shift_scroll"],
    external_refs=[
        "Google Web Vitals (web.dev/vitals, 2020-présent)",
        "Amazon (2006) 100ms latency = 1% sales loss",
        "Akamai (2017) Online Retail Performance Report",
        "Google Search Central (2023) Page Experience Ranking Signals",
        "Deloitte (2020) Milliseconds Make Millions",
        "Chrome UX Report (CrUX) documentation",
    ],
    effort_hours=20,
    priority="P0",
))

PATTERNS.append(mk(
    crit="tech_02",
    pillar="tech",
    pillar_block="bloc_6_tech_v3.json",
    mech_or_copy="MECH",
    name="Accessibilité basique (sémantique HTML, contraste AA, alt, ARIA)",
    summary="Atteindre WCAG 2.1 AA minimum : sémantique HTML (h1-h6, button, nav, main), alt sur images, contraste 4.5:1 body, labels associés, navigation clavier, ARIA minimal et correct.",
    page_types=["*"],
    why=(
        "WCAG 2.1 AA (W3C, 2018) : standard international accessibilité — "
        "environ 15% de la population mondiale vit avec un handicap (OMS "
        "2022), inclusion = extension du marché + obligation légale (Europe "
        "Accessibility Act 2025, Section 508 US, RGAA FR). SEO Impact : "
        "sémantique HTML correcte = compréhension par Googlebot et LLM "
        "crawlers (Perplexity, ChatGPT Search), +15-30% de visibilité "
        "organique typique (Ahrefs 2023). Usability Impact : l'accessibilité "
        "profite à tous — caption vidéo utile en silence, alt = fallback "
        "quand image bug, structure headings = navigation rapide. Legal "
        "Impact : 4 025 procès ADA déposés en 2023 aux US (UsableNet), "
        "amendes CNIL pour non-RGAA en France. Baymard (2023) : 23% des "
        "utilisateurs ont abandonné un site à cause d'un problème "
        "d'accessibilité non-handicap (contraste faible, fonts illisibles). "
        "Mobile usability = accessibilité : touch targets 44×44px, "
        "zoom 200% sans scroll horizontal = WCAG 1.4.10."
    ),
    do=[
        "Sémantique HTML5 : <header>, <nav>, <main>, <article>, <section>, <footer>, <button>, <form>. Pas de <div onclick=''> pour un bouton.",
        "H1 unique, H2-H6 séquentiels (pas H1 → H3).",
        "alt text sur toutes les images : descriptif pour les images porteuses de sens, alt='' pour les images décoratives.",
        "Labels <label for='id'> associés à tous les inputs, ou aria-label si non visible.",
        "Contraste WCAG AA : 4.5:1 body text, 3:1 large text (≥18px ou 14px bold), 3:1 UI components.",
        "Navigation clavier : tab order logique, focus ring visible (outline: 2px solid brand), skip-to-content link.",
        "ARIA minimal : aria-label sur icônes, aria-expanded sur accordion, aria-live sur validation, aria-describedby sur form hints.",
    ],
    dont=[
        "Pas de couleur seule comme signal (ex: erreur en rouge sans icône ou texte).",
        "Pas de placeholder comme seul label (disparait au focus, utilisateur perd le contexte).",
        "Pas de outline:none sans alternative focus-visible.",
        "Pas d'aria-hidden='true' sur contenu important (caché aux AT).",
        "Pas de ARIA incorrect qui casse plus qu'il n'aide (role='button' sur un <a>, role='heading' sans level).",
        "Pas de touch targets <44×44px mobile.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {
            "desktop": {
                "canvas": "1440x900",
                "contrast_body": "4.5:1 minimum",
                "contrast_large_text": "3:1 minimum (>=18px or >=14px bold)",
                "focus_visible_ring": "2px solid brand, offset 2px",
                "skip_to_content_link": "first tab stop, visible on focus",
            },
            "mobile": {
                "canvas": "390x844",
                "touch_target_min": "44x44px (Apple HIG) or 48x48px (Material)",
                "zoom_200pct_no_h_scroll": True,
                "dynamic_text_support": "respect iOS/Android accessibility font scaling",
            },
        },
        "dom_constraints": {
            "semantic_tags": "header, nav, main, article, section, footer, button, form required",
            "h1_unique": True,
            "heading_hierarchy": "sequential no skips",
            "alt_attributes": "required on all <img> (empty for decorative)",
            "form_labels": "required for all inputs",
            "lang_attribute": "<html lang='fr'> or appropriate",
            "aria_roles": "only when HTML semantics insufficient",
        },
    },
    anti_patterns=["div_onclick_as_button", "color_only_signal", "placeholder_as_label", "outline_none_no_replacement"],
    external_refs=[
        "W3C WCAG 2.1 (2018) / 2.2 (2023)",
        "European Accessibility Act (Directive UE 2019/882)",
        "Section 508 (US Rehabilitation Act)",
        "RGAA 4.1 (France, 2024)",
        "WHO (2022) World Report on Disability update",
        "UsableNet (2023) ADA Website Lawsuit Report",
        "Apple HIG Touch Targets, Material Design Touch Targets",
    ],
    effort_hours=24,
    priority="P0",
))

PATTERNS.append(mk(
    crit="tech_03",
    pillar="tech",
    pillar_block="bloc_6_tech_v3.json",
    mech_or_copy="MECH",
    name="SEO on-page — fondations pour le trafic organique",
    summary="Implémenter les fondations SEO : balises meta (title 50-60c, description 150-160c), structure headings cohérente, URLs propres, schema.org, canonical, hreflang si multi-lang.",
    page_types=["*"],
    why=(
        "SEO on-page (Moz, Ahrefs, Google Search Central) : les signaux "
        "techniques et éditoriaux de chaque page influencent directement le "
        "classement. Title tag : le plus gros facteur de ranking intra-page. "
        "Meta description : pas de ranking direct, mais impact CTR SERP. "
        "Schema.org structured data (Product, Organization, FAQ, LocalBusiness, "
        "Article) : rich snippets augmentent CTR de +20-30% (Search Engine "
        "Land 2023). Core Web Vitals : ranking signal depuis 2021. AI "
        "Search (2024+) : Perplexity, ChatGPT, Google SGE utilisent la "
        "sémantique HTML et le schema.org pour extraire l'info. Les pages "
        "bien structurées apparaissent en citation source. E-commerce "
        "spécifique : schema Product avec price, availability, aggregateRating "
        "= éligibilité rich results Google Shopping. Canonical : évite le "
        "duplicate content. Hreflang : critique pour sites multi-pays. "
        "Condition : SEO on-page ≠ keyword stuffing, qui est contreproductif "
        "depuis Google Panda (2011)."
    ),
    do=[
        "Title tag unique par page : 50-60 caractères, keyword principal au début, marque à la fin : '[Keyword] — [Marque]'.",
        "Meta description : 150-160 caractères, value proposition + CTA implicite. Chaque page une description unique.",
        "URL propre : minuscules, tirets, pas d'accents, courts (<60c), hiérarchie logique /categorie/sous-categorie/produit.",
        "Headings hiérarchisés : 1 H1 avec keyword principal, H2 avec keywords secondaires.",
        "Schema.org : Product (e-comm), Organization (home), FAQ (pages FAQ), Article (blog), LocalBusiness (multi-site), BreadcrumbList.",
        "Canonical URL sur chaque page : <link rel='canonical' href='https://…'>.",
        "Alt images pertinents (voir tech_02), nom de fichier descriptif (kebab-case).",
        "Internal linking cohérent : 2-5 liens contextuels vers pages apparentées.",
    ],
    dont=[
        "Pas de title / description identiques sur plusieurs pages (duplicate meta).",
        "Pas de title >65c ou description >160c (coupés en SERP).",
        "Pas de keyword stuffing dans le title ou le body (>3% density = pénalité Google).",
        "Pas d'URL avec paramètres multiples (?utm=…&ref=…) en version canonical.",
        "Pas de contenu dupliqué sans canonical pointant vers version originale.",
        "Pas de H1 multiples ou H1 absent.",
        "Pas d'images hero sans alt ou avec 'image.jpg' comme nom de fichier.",
    ],
    copy_templates=[
        {"slot": "title_tag", "template": "{Primary_keyword} — {Brand}", "example": "CRM pour indépendants — Axiom (58c)"},
        {"slot": "meta_description", "template": "{Value_prop_12_15_words} · {Proof_or_CTA}.", "example": "Le CRM pensé pour les freelances qui facturent à l'international. Essai 14 jours gratuit, sans carte. (152c)"},
        {"slot": "url_pattern", "template": "/{category}/{product-kebab-case}", "example": "/crm/indie-freelance-multi-currency"},
    ],
    layout_directives={
        "viewports": {"desktop": {"canvas": "N/A — tech layer"}, "mobile": {"canvas": "N/A — tech layer"}},
        "head_requirements": {
            "title": "required, unique, 50-60c",
            "meta_description": "required, unique, 150-160c",
            "canonical": "required on every indexable page",
            "og_tags": "og:title, og:description, og:image, og:url — social preview",
            "twitter_card": "summary_large_image",
            "viewport_meta": "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "charset": "UTF-8",
            "lang": "<html lang='fr'>",
        },
        "schema_org": {
            "home_saas": "Organization + WebSite + potential Product/Service",
            "pdp_ecomm": "Product with price/availability/aggregateRating",
            "faq_page": "FAQPage with mainEntity",
            "article": "Article with headline/datePublished/author",
            "local": "LocalBusiness with address/telephone/openingHours",
        },
        "sitemap": "/sitemap.xml + reference in /robots.txt",
    },
    anti_patterns=["duplicate_meta_title", "keyword_stuffing", "url_with_params_as_canonical", "missing_canonical"],
    external_refs=[
        "Google Search Central (2024) Search Essentials & Technical SEO",
        "Moz (2024) On-Page SEO Guide",
        "Ahrefs (2023) Rich Snippets Study",
        "Search Engine Land (2023) Schema.org CTR Impact",
        "Google Panda Algorithm (2011) — quality content guidelines",
        "Schema.org (schema.org official documentation)",
    ],
    effort_hours=16,
    priority="P0",
))

PATTERNS.append(mk(
    crit="tech_04",
    pillar="tech",
    pillar_block="bloc_6_tech_v3.json",
    mech_or_copy="MECH",
    name="Tracking & Analytics — capacité de mesure et optimisation",
    summary="Installer un tracking minimum : GA4 + Google Tag Manager + pixel Meta/TikTok si paid + event tracking sur CTA principaux + consent management conforme RGPD.",
    page_types=["*"],
    why=(
        "Peter Drucker (1954) : 'What gets measured gets managed'. Sans "
        "tracking = pas d'optimisation possible, pas de A/B test, pas de "
        "boucle d'apprentissage. GA4 (Google Analytics 4, obligatoire depuis "
        "2023 remplacement UA) : standard de mesure audience, conversion, "
        "funnel. GTM (Google Tag Manager) : couche de gestion tags qui "
        "découple déploiement des tags du dev release cycle. Paid pixels "
        "(Meta Pixel, TikTok Pixel, LinkedIn Insight Tag) : critiques pour "
        "campagnes paid — sans tracking = pas d'optimisation algo, pas de "
        "remarketing. Event tracking (click CTA, scroll depth, form start/"
        "submit, purchase) : granularité nécessaire pour optimiser. "
        "RGPD / ePrivacy (UE 2018+, Google Consent Mode v2 depuis 2024) : "
        "consent management obligatoire UE, sous peine d'amende CNIL. "
        "Condition : consent-first, défensif sur données PII. Baymard "
        "(2023) : 40% des e-commerce ont un tracking cassé sur ≥1 étape "
        "du funnel — invisible mais ruineux."
    ),
    do=[
        "Installer GTM (container id GTM-XXXX) dans <head> et <body>.",
        "Configurer GA4 (Measurement ID G-XXXX) via GTM, envoyer les enhanced ecommerce events (purchase, add_to_cart, view_item, begin_checkout) selon GA4 schema.",
        "Si paid Meta : installer Meta Pixel + Conversions API (CAPI) pour iOS 14+ tracking.",
        "Si paid TikTok : TikTok Pixel + Events API.",
        "Event tracking sur : click CTA primaire, scroll 25/50/75/100%, form_start, form_submit, video_play_50pct.",
        "Consent Management Platform (CMP) conforme : Cookiebot, Didomi, Axeptio. Google Consent Mode v2 configuré.",
        "Dashboards Looker Studio ou Metabase connectés à GA4 + BigQuery export pour analyse custom.",
        "Tester en recette avec Tag Assistant et Meta Pixel Helper avant prod.",
    ],
    dont=[
        "Pas de tracking fire-before-consent UE — non-conformité RGPD, amende CNIL.",
        "Pas de Universal Analytics (UA) — arrêté juillet 2023 par Google.",
        "Pas de pixel tiers sans Consent Mode v2 ou équivalent.",
        "Pas d'event tracking custom avec des noms non-standard (ex: 'btn_click_1', 'btn_click_2') — impossible à analyser.",
        "Pas de tags scripts synchrones dans <head> — bloque le LCP (voir tech_01).",
        "Pas de tracking de PII (email, nom) en clair — hashing SHA-256 si remarketing, anonymisation sinon.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {"desktop": {"canvas": "N/A — tech layer"}, "mobile": {"canvas": "N/A — tech layer"}},
        "tracking_stack_minimum": {
            "tag_manager": "Google Tag Manager (GTM-XXXX)",
            "analytics": "GA4 (G-XXXX)",
            "consent_mode": "Google Consent Mode v2",
            "cmp": "Cookiebot | Didomi | Axeptio | custom conformant",
            "paid_pixels_if_applicable": ["Meta Pixel + CAPI", "TikTok Pixel", "LinkedIn Insight Tag", "Google Ads Conversions"],
        },
        "events_required": {
            "ecommerce": ["view_item", "add_to_cart", "begin_checkout", "purchase", "refund"],
            "lead_gen": ["form_start", "form_submit", "generate_lead", "qualified_lead"],
            "saas_trial": ["sign_up", "trial_start", "trial_convert"],
            "engagement": ["scroll_25", "scroll_50", "scroll_75", "scroll_100", "video_play", "video_complete"],
        },
        "consent_granularity": {
            "analytics_storage": "granted | denied",
            "ad_storage": "granted | denied",
            "ad_user_data": "granted | denied",
            "ad_personalization": "granted | denied",
        },
        "data_privacy": {
            "pii_hashing": "SHA-256 for emails/phones before sending to ads platforms",
            "retention": "GA4 default 14 months, configure per business need",
            "anonymize_ip": True,
        },
    },
    anti_patterns=["tracking_before_consent", "ua_still_installed", "non_standard_event_names", "sync_tracking_in_head"],
    external_refs=[
        "Google Analytics 4 Documentation (developers.google.com/analytics/devguides/collection/ga4)",
        "Google Tag Manager Documentation",
        "Meta Conversions API Documentation",
        "Google Consent Mode v2 (2024)",
        "RGPD (UE 2016/679)",
        "ePrivacy Directive 2002/58/EC",
        "CNIL (France) Guidelines cookies et traceurs 2020",
    ],
    effort_hours=16,
    priority="P0",
))

PATTERNS.append(mk(
    crit="tech_05",
    pillar="tech",
    pillar_block="bloc_6_tech_v3.json",
    mech_or_copy="MECH",
    name="Sécurité & Confiance technique — HTTPS, charset, viewport, security headers",
    summary="Déployer les fondations sécurité : HTTPS forcé (HSTS), charset UTF-8, viewport meta, CSP/X-Frame-Options/Referrer-Policy, cookies Secure+HttpOnly+SameSite.",
    page_types=["*"],
    why=(
        "HTTPS (TLS 1.3 recommandé) : Google flag les sites HTTP comme 'Non "
        "sécurisé' dans Chrome depuis 2018, ranking signal depuis 2014, "
        "obligation pour paiements (PCI-DSS). HSTS (HTTP Strict Transport "
        "Security) : empêche le downgrade HTTP. CSP (Content Security "
        "Policy) : protège contre XSS en limitant les sources autorisées "
        "JS/CSS. X-Frame-Options / frame-ancestors : empêche clickjacking. "
        "Referrer-Policy : contrôle ce qui est envoyé en referrer aux "
        "autres sites (privacy). Cookies Secure+HttpOnly+SameSite : "
        "atténuent CSRF et vol de session. Viewport meta : responsive et "
        "mobile-friendly (ranking signal mobile-first indexing). "
        "OWASP Top 10 : les vulnérabilités les plus communes sont souvent "
        "dues à l'absence de headers basiques. Mozilla Observatory / "
        "SSL Labs : outils de score publics, un mauvais score visible "
        "peut être exploité par concurrents. Impact confiance : le "
        "padlock HTTPS est vu par 92% des utilisateurs e-commerce "
        "comme un signal de confiance (Baymard 2022)."
    ),
    do=[
        "HTTPS forcé : redirection 301 http→https sur toutes les pages, certificat TLS 1.3 valide.",
        "HSTS : Strict-Transport-Security: max-age=31536000; includeSubDomains; preload (si ready for submission).",
        "Charset : <meta charset='UTF-8'> en 1er dans <head>.",
        "Viewport : <meta name='viewport' content='width=device-width, initial-scale=1'>.",
        "Content-Security-Policy : définir default-src 'self' et allowlist spécifique pour scripts/styles/images externes.",
        "X-Frame-Options: SAMEORIGIN OR CSP frame-ancestors 'self'.",
        "Referrer-Policy: strict-origin-when-cross-origin.",
        "X-Content-Type-Options: nosniff.",
        "Cookies : flags Secure + HttpOnly + SameSite=Lax (ou Strict).",
        "Vérifier score Mozilla Observatory + SSL Labs (cible A/A+).",
    ],
    dont=[
        "Pas de HTTP en 2026 — red flag sécurité immédiat dans les navigateurs.",
        "Pas de mixed content (ressource HTTP sur page HTTPS) — bloqué par Chrome.",
        "Pas de certificat self-signed ou expiré en prod.",
        "Pas de CSP unsafe-inline + unsafe-eval — annule les protections.",
        "Pas de cookies sans Secure sur HTTPS — vulnérable en MITM.",
        "Pas de X-XSS-Protection: 1 (obsolète, cause des bugs) — supprimer, utiliser CSP.",
        "Pas de Server header exposant la version (Apache/2.4.29) — signal pour exploits ciblés.",
    ],
    copy_templates=[],
    layout_directives={
        "viewports": {"desktop": {"canvas": "N/A — tech layer"}, "mobile": {"canvas": "N/A — tech layer"}},
        "http_headers_required": {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' <allowlisted-cdns>; style-src 'self' 'unsafe-inline'; img-src 'self' data: <cdns>; font-src 'self' data: <cdns>;",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",
        },
        "head_order_first_tags": [
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<title>...</title>",
            "<meta name='description' content='...'>",
            "<link rel='canonical' href='...'>",
        ],
        "cookies_flags": "Secure; HttpOnly; SameSite=Lax (auth: Strict)",
        "tls_config": "TLS 1.2 minimum, TLS 1.3 preferred, strong ciphers, no weak DH",
        "observability": {
            "mozilla_observatory_target": "A or A+",
            "ssl_labs_target": "A or A+",
            "hsts_preload_ready": "after 1 year of successful HSTS",
        },
    },
    anti_patterns=["http_still_served", "mixed_content", "unsafe_inline_csp", "server_header_exposed"],
    external_refs=[
        "Mozilla Observatory (observatory.mozilla.org)",
        "SSL Labs (www.ssllabs.com/ssltest)",
        "OWASP Top 10 (2021)",
        "Google Chrome Security Team (2018) Not Secure HTTP warning",
        "PCI-DSS 4.0 (2024) Payment Card Industry Data Security Standard",
        "Mozilla Web Security Cheat Sheet",
        "Baymard Institute (2022) E-commerce Trust Signals",
    ],
    effort_hours=12,
    priority="P0",
))


# Save intermediate (partial — will be appended in subsequent calls)
def save_all():
    out = {
        "_meta": {
            "batch_id": "batch_002_doctrinal",
            "doctrine_version": "v14.2_locked_20260416",
            "type": "top_down_completion",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "purpose": "Doctrinal patterns for orphan criteria after batch 1 bottom-up. Sourced on playbook + academic literature. NO seed grounding — will inherit lift from future bottom-up passes.",
            "coverage_goal": "47/47 criteria doctrine",
            "total_patterns": len(PATTERNS),
            "pillars_distribution": {
                p: sum(1 for pat in PATTERNS if pat["criterion"].startswith(p))
                for p in ["hero", "per", "ux", "coh", "psy", "tech"]
            },
        },
        "patterns": PATTERNS,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Wrote {len(PATTERNS)} doctrinal patterns to {OUT}")
    print("Pillar distribution:", out["_meta"]["pillars_distribution"])


if __name__ == "__main__":
    save_all()
