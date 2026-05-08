"""moteur_gsg.core.brief_v2_prefiller — V26.AF Sprint AF-1.B.1.

Pré-remplit un BriefV2 depuis tout ce qu'on sait déjà sur le client (router racine).
Mathis valide / édite les pré-remplis avant lancement pipeline.

API :
    from moteur_gsg.core.brief_v2_prefiller import prefill_brief_v2_from_client

    brief, sources = prefill_brief_v2_from_client(
        client_url="https://www.weglot.com",
        page_type="lp_listicle",
        target_language="FR",
        mode="complete",
    )
    # brief = BriefV2 partiellement rempli
    # sources = dict {field_name: source_string} pour transparence ("audience" ← intent.json)

Champs auto-pré-remplis (si data dispo via client_context) :
  - objective       ← intent.primary_intent + recos top P0
  - audience        ← intent.audience + v143.voc_verbatims
  - angle           ← brand_dna.signature_phrase + brand_dna.method.archetype
  - desired_signature ← AURA vector → golden bridge top match signature
  - traffic_source  ← suggéré selon page_type (cold_ad pour lp_listicle, organic_seo pour pdp, etc.)
  - visitor_mode    ← suggéré selon page_type
  - available_proofs ← v143.founder.named + v143.voc_verbatims + recos.evidence_ids
  - sourced_numbers ← v143.scarcity + v143.founder press_mentions + recos.chiffres_cités
  - founder_citations ← v143.founder bio
  - forbidden_visual_patterns ← brand_dna.diff.forbid + design_grammar.forbidden_patterns

Champs LAISSÉS VIDES (Mathis doit fournir) :
  - mode (sauf si donné en arg)
  - inspiration_urls, inspiration_screenshots
  - existing_page_url (Mode 2 spécifique)
  - concept_description (Mode 3 spécifique)
  - testimonials (anti-Sarah-32-ans : Mathis confirme noms réels)
  - product_photos_real (assets Mathis)
"""
from __future__ import annotations

import pathlib
import sys
from typing import Optional
from urllib.parse import urlparse

from .brief_v2 import BriefV2, SourcedNumber

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from client_context import load_client_context, ClientContext  # noqa: E402


def _extract_slug_from_url(url: str) -> str:
    """https://www.weglot.com → 'weglot'"""
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    return host.split(".")[0]


def _suggest_traffic_source(page_type: str) -> list[str]:
    suggestions = {
        "lp_listicle": ["cold_ad_meta", "cold_ad_google", "organic_seo"],
        "advertorial": ["cold_ad_meta", "cold_ad_google"],
        "lp_sales": ["warm_retargeting", "email_list"],
        "lp_leadgen": ["cold_ad_meta", "cold_ad_google"],
        "pdp": ["organic_seo", "cold_ad_meta"],
        "home": ["organic_seo", "direct"],
        "pricing": ["direct", "warm_retargeting"],
        "vsl": ["cold_ad_meta"],
        "quiz_vsl": ["cold_ad_meta"],
    }
    return suggestions.get(page_type, ["cold_ad_meta", "organic_seo"])


def _suggest_visitor_mode(page_type: str) -> str:
    suggestions = {
        "lp_listicle": "scan_30s",
        "advertorial": "read_5min",
        "lp_sales": "read_5min",
        "lp_leadgen": "decide_impulsive",
        "pdp": "compare_research",
        "home": "scan_30s",
        "pricing": "compare_research",
        "vsl": "read_5min",
        "quiz_vsl": "decide_impulsive",
    }
    return suggestions.get(page_type, "scan_30s")


def _extract_objective_from_intent(intent: Optional[dict], page_type: str) -> str:
    if not intent:
        return ""
    primary = intent.get("primary_intent") or intent.get("intent", "")
    if not primary:
        return ""
    intent_to_objective = {
        "purchase": "Convertir vers achat (CTA primaire = acheter / commander)",
        "signup_commit": "Convertir en signup / inscription trial",
        "contact_lead": "Capturer lead qualifié (formulaire / appel)",
        "discovery_quiz": "Engager via quiz puis convertir vers offre principale",
        "content_consume": "Engager lecture longue puis push vers CTA secondaire",
    }
    base = intent_to_objective.get(primary, f"Maximiser conversion sur intent={primary}")
    return f"{base}. Page type : {page_type}."


def _extract_audience_from_intent_v143(intent: Optional[dict], v143_voc: Optional[dict]) -> str:
    parts = []
    if intent:
        audience = intent.get("audience")
        if audience:
            parts.append(f"Audience : {audience}")
        schwartz = intent.get("schwartz_awareness") or intent.get("awareness_stage")
        if schwartz:
            parts.append(f"Schwartz awareness : {schwartz}")
        objections = intent.get("objections", [])
        if objections:
            parts.append(f"3 peurs principales : {', '.join(o[:80] for o in objections[:3])}")
        desires = intent.get("desires", [])
        if desires:
            parts.append(f"3 désirs : {', '.join(d[:80] for d in desires[:3])}")
    if v143_voc:
        verbatims = v143_voc.get("verbatims") or v143_voc.get("reviews", [])
        if verbatims:
            sample_quotes = []
            for v in verbatims[:2]:
                if isinstance(v, dict):
                    txt = v.get("text") or v.get("quote", "")
                    if txt:
                        sample_quotes.append(f'« {txt[:80]} »')
            if sample_quotes:
                parts.append(f"VoC sample : {' / '.join(sample_quotes)}")
    return ". ".join(parts) if parts else ""


def _extract_angle_from_brand_dna(brand_dna: Optional[dict], page_type: str) -> str:
    if not brand_dna:
        return ""
    voice = brand_dna.get("voice_tokens", {}) or {}
    signature = voice.get("voice_signature_phrase", "")
    method = brand_dna.get("method", {}) or {}
    archetype = method.get("brand_archetype") or method.get("archetype", "") if isinstance(method, dict) else ""

    parts = []
    if signature:
        parts.append(f"Signature voix : « {signature[:120]} »")
    if archetype:
        parts.append(f"Archetype : {archetype}")
    parts.append(f"Format {page_type} : à confirmer / éditer si besoin")
    return ". ".join(parts) if parts else ""


def _extract_proofs_from_v143_recos(
    v143_founder: Optional[dict],
    v143_voc: Optional[dict],
    v143_scarcity: Optional[dict],
    recos: Optional[dict],
) -> tuple[list[str], list[SourcedNumber]]:
    proofs = []
    sourced_numbers = []

    if v143_founder and v143_founder.get("named"):
        proofs.append("temoignages_named")
    if v143_voc and (v143_voc.get("verbatims") or v143_voc.get("reviews")):
        proofs.append("note_trustpilot_sourced")
    if v143_scarcity and v143_scarcity.get("claim_present") and not v143_scarcity.get("suspected_fake"):
        proofs.append("garantie_specifique")

    # sourced_numbers from v143
    if v143_founder:
        revenue = v143_founder.get("company_revenue_m_eur")
        age = v143_founder.get("company_age_years")
        if revenue:
            sourced_numbers.append(SourcedNumber(
                number=f"{revenue}M€", source="v143.founder.company_revenue_m_eur",
                context="Revenu annuel public"
            ))
        if age:
            sourced_numbers.append(SourcedNumber(
                number=f"{age} ans", source="v143.founder.company_age_years",
                context="Âge de l'entreprise"
            ))
    # If we have any sourced numbers, also add the proof tag
    if sourced_numbers:
        if "chiffres_internes" not in proofs:
            proofs.append("chiffres_internes")

    return proofs, sourced_numbers


def _extract_forbidden_from_brand_dna(brand_dna: Optional[dict], design_grammar: Optional[dict]) -> list[str]:
    """Pré-remplit forbidden_visual_patterns avec defaults V26.AE anti-AI-slop +
    overrides depuis brand_dna.diff.forbid + design_grammar.forbidden_patterns.
    """
    # Defaults universels anti-AI-slop
    forbidden = [
        "stock_photos",
        "gradient_mesh",
        "ai_generated_images",
        "checkmark_icons_systematic",
    ]
    # Add brand-specific forbids from brand_dna diff E1
    if brand_dna:
        diff = brand_dna.get("diff", {}) or {}
        for item in (diff.get("forbid") or [])[:5]:
            if isinstance(item, dict):
                text = item.get("item") or item.get("description")
                if text and text not in forbidden:
                    forbidden.append(str(text)[:100])
    return forbidden[:8]  # cap à 8 pour rester court


def prefill_brief_v2_from_client(
    client_url: str,
    page_type: str,
    target_language: str = "FR",
    mode: str = "complete",
    *,
    objective_override: Optional[str] = None,
    audience_override: Optional[str] = None,
    angle_override: Optional[str] = None,
) -> tuple[BriefV2, dict, ClientContext]:
    """Pré-remplit BriefV2 depuis client_context (router racine).

    Args:
      client_url: ex "https://www.weglot.com"
      page_type: ex "lp_listicle"
      target_language: "FR" / "EN" / etc.
      mode: "complete" / "replace" / "extend" / "elevate" / "genesis"
      objective_override / audience_override / angle_override: si Mathis a déjà ses idées,
        on respecte (mais le pré-fill peut remplir AUTOUR).

    Returns:
      (brief, sources, ctx)
      - brief : BriefV2 partiellement rempli
      - sources : dict {field: source_str} pour transparence vers Mathis
      - ctx : ClientContext loaded (au cas où le caller veut plus de data)
    """
    slug = _extract_slug_from_url(client_url)
    ctx = load_client_context(slug, page_type)

    sources = {}

    # — Section 1 MISSION —
    sources["mode"] = "user-provided"
    sources["page_type"] = "user-provided"
    sources["client_url"] = "user-provided"
    sources["target_language"] = "user-provided"

    # — Section 2 BUSINESS BRIEF —
    if objective_override:
        objective = objective_override
        sources["objective"] = "user-provided (override)"
    else:
        objective = _extract_objective_from_intent(ctx.intent, page_type)
        sources["objective"] = "intent.primary_intent + page_type heuristic" if objective else "VIDE — Mathis fournit"

    if audience_override:
        audience = audience_override
        sources["audience"] = "user-provided (override)"
    else:
        audience = _extract_audience_from_intent_v143(ctx.intent, ctx.v143_voc)
        sources["audience"] = "intent.audience/objections/desires + v143.voc_verbatims" if audience else "VIDE — Mathis fournit"

    if angle_override:
        angle = angle_override
        sources["angle"] = "user-provided (override)"
    else:
        angle = _extract_angle_from_brand_dna(ctx.brand_dna, page_type)
        sources["angle"] = "brand_dna.voice_signature_phrase + archetype" if angle else "VIDE — Mathis fournit"

    traffic_source = _suggest_traffic_source(page_type)
    sources["traffic_source"] = f"suggested for {page_type}"

    visitor_mode = _suggest_visitor_mode(page_type)
    sources["visitor_mode"] = f"suggested for {page_type}"

    # — Section 4 MATÉRIEL —
    proofs, sourced_numbers = _extract_proofs_from_v143_recos(
        ctx.v143_founder, ctx.v143_voc, ctx.v143_scarcity, ctx.recos_final,
    )
    sources["available_proofs"] = "v143 (founder/voc/scarcity) + recos evidences"
    sources["sourced_numbers"] = "v143.founder.* + recos.chiffres_cités"

    founder_citations = []
    if ctx.v143_founder and ctx.v143_founder.get("bio"):
        founder_citations.append(ctx.v143_founder["bio"][:300])
        sources["founder_citations"] = "v143.founder.bio"

    # — Section 5 VISUEL & DA —
    forbidden_visual = _extract_forbidden_from_brand_dna(ctx.brand_dna, ctx.design_grammar)
    sources["forbidden_visual_patterns"] = "anti-AI-slop defaults + brand_dna.diff.forbid"

    # Construct BriefV2 with all the pre-filled values
    brief = BriefV2(
        mode=mode,
        page_type=page_type,
        client_url=client_url,
        target_language=target_language,
        objective=objective,
        audience=audience,
        angle=angle,
        traffic_source=traffic_source,
        visitor_mode=visitor_mode,
        available_proofs=proofs,
        sourced_numbers=sourced_numbers,
        founder_citations=founder_citations,
        forbidden_visual_patterns=forbidden_visual,
    )

    return brief, sources, ctx


def format_brief_for_mathis_review(brief: BriefV2, sources: dict, ctx: ClientContext) -> str:
    """Formate le brief pré-rempli en markdown lisible pour validation Mathis."""
    lines = []
    lines.append(f"# Brief V2 pré-rempli — {brief.client_url} / {brief.page_type}")
    lines.append(f"\n**Router racine completeness** : {ctx.completeness_pct}% ({len(ctx.available_artefacts)} artefacts dispo)")
    lines.append(f"**Available** : {', '.join(ctx.available_artefacts[:6])}")
    if ctx.missing_artefacts:
        lines.append(f"**Missing** : {', '.join(ctx.missing_artefacts[:4])}")

    lines.append("\n## Section 1 — MISSION")
    lines.append(f"- **mode** : `{brief.mode}` ({sources.get('mode')})")
    lines.append(f"- **page_type** : `{brief.page_type}` ({sources.get('page_type')})")
    lines.append(f"- **client_url** : `{brief.client_url}`")
    lines.append(f"- **target_language** : `{brief.target_language}`")

    lines.append("\n## Section 2 — BUSINESS BRIEF")
    lines.append(f"- **objective** *(source: {sources.get('objective')})* :\n  > {brief.objective[:300]}")
    lines.append(f"- **audience** *(source: {sources.get('audience')})* :\n  > {brief.audience[:400]}")
    lines.append(f"- **angle** *(source: {sources.get('angle')})* :\n  > {brief.angle[:300]}")
    lines.append(f"- **traffic_source** : {brief.traffic_source}")
    lines.append(f"- **visitor_mode** : `{brief.visitor_mode}`")

    lines.append("\n## Section 4 — MATÉRIEL")
    lines.append(f"- **available_proofs** : {brief.available_proofs}")
    if brief.sourced_numbers:
        lines.append(f"- **sourced_numbers** ({len(brief.sourced_numbers)}) :")
        for sn in brief.sourced_numbers:
            lines.append(f"  - `{sn.number}` ← {sn.source} ({sn.context})")
    if brief.founder_citations:
        lines.append(f"- **founder_citations** : {len(brief.founder_citations)} citation(s)")

    lines.append("\n## Section 5 — VISUEL & DA")
    lines.append(f"- **forbidden_visual_patterns** : {brief.forbidden_visual_patterns}")

    # Champs vides à remplir par Mathis
    missing = []
    if not brief.objective:
        missing.append("objective")
    if not brief.audience:
        missing.append("audience")
    if not brief.angle:
        missing.append("angle")
    if missing:
        lines.append(f"\n## ⚠️ Champs VIDES — Mathis doit fournir : {missing}")

    # Validation BriefV2
    errors = brief.validate()
    if errors:
        lines.append(f"\n## ❌ Erreurs validation BriefV2 ({len(errors)}) :")
        for e in errors[:5]:
            lines.append(f"  - {e}")
    else:
        lines.append("\n## ✓ BriefV2 valide — prêt à lancer")

    return "\n".join(lines)
