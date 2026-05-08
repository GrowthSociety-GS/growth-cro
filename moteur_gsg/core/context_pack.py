"""Generation context pack for the canonical GSG.

The client context router already knows how to load GrowthCRO artefacts. This
module turns that rich, heterogeneous state into a compact contract for GSG
planning: what we know, what we can prove, what assets exist, and where the
current generation mode is allowed to depend on Audit/Reco.
"""
from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from client_context import ClientContext, load_client_context  # noqa: E402


MODE_AUDIT_DEPENDENCY = {
    "complete": "read_context_only",
    "replace": "requires_audit_reco",
    "extend": "read_context_only",
    "elevate": "read_context_only",
    "genesis": "no_client_context_required",
}


@dataclass
class EvidenceFact:
    label: str
    value: str
    source: str
    context: str = ""


@dataclass
class GenerationContextPack:
    version: str
    mode: str
    client: str
    page_type: str
    target_language: str
    audit_dependency_policy: str
    artefacts: dict[str, Any]
    brand: dict[str, Any]
    business: dict[str, Any]
    audience: dict[str, Any]
    proof_inventory: list[EvidenceFact] = field(default_factory=list)
    scent_contract: dict[str, Any] = field(default_factory=dict)
    visual_assets: dict[str, str] = field(default_factory=dict)
    design_sources: dict[str, Any] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _compact_text(value: Any, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:max_chars]


def _brief_text(brief: dict[str, Any]) -> str:
    return " ".join(
        str(v)
        for v in (brief or {}).values()
        if isinstance(v, (str, int, float, list, tuple))
    ).lower()


def infer_business_category_from_context(ctx: ClientContext, brief: dict[str, Any]) -> str:
    """Infer a broad business category from brief + existing context."""
    text_parts = [_brief_text(brief)]
    for source in (ctx.intent, ctx.brand_dna, ctx.site_audit):
        if isinstance(source, dict):
            text_parts.append(_compact_text(source, max_chars=1600).lower())
    text = " ".join(text_parts)
    if re.search(r"\b(saas|software|app|api|trial|demo|product-led|product led|signup|b2b)\b", text):
        return "saas"
    if re.search(r"\b(ecommerce|e-commerce|dtc|shopify|panier|checkout|pdp|commande|achat)\b", text):
        return "ecommerce"
    if re.search(r"\b(devis|rdv|rendez-vous|lead|formulaire|consultation|audit gratuit)\b", text):
        return "lead_gen"
    if re.search(r"\b(mobile app|application mobile|ios|android|install)\b", text):
        return "app"
    if re.search(r"\b(luxe|premium|maison|atelier|bijou|montre|parfum)\b", text):
        return "luxury"
    if re.search(r"\b(course|formation|coaching|programme|webinar|challenge)\b", text):
        return "education"
    return "generic_cro"


def _brand_summary(ctx: ClientContext) -> dict[str, Any]:
    brand = ctx.brand_dna or {}
    diff = brand.get("diff") if isinstance(brand.get("diff"), dict) else {}
    visual = brand.get("visual_tokens") if isinstance(brand.get("visual_tokens"), dict) else {}
    voice = brand.get("voice_tokens") if isinstance(brand.get("voice_tokens"), dict) else {}
    colors = visual.get("colors") if isinstance(visual.get("colors"), dict) else {}
    typography = visual.get("typography") if isinstance(visual.get("typography"), dict) else {}

    return {
        "client_name": brand.get("client") or diff.get("client") or ctx.client,
        "home_url": brand.get("home_url"),
        "signature": (
            brand.get("voice_signature_phrase")
            or voice.get("signature_phrase")
            or _compact_text(diff.get("preserve"), 180)
        ),
        "preserve_count": len(diff.get("preserve") or []),
        "amplify_count": len(diff.get("amplify") or []),
        "fix_count": len(diff.get("fix") or []),
        "forbid_count": len(diff.get("forbid") or []),
        "palette": [
            item.get("hex")
            for item in (colors.get("palette_full") or [])
            if isinstance(item, dict) and item.get("hex")
        ][:8],
        "display_font": ((typography.get("h1") or {}).get("family") if isinstance(typography, dict) else None),
        "body_font": ((typography.get("body") or {}).get("family") if isinstance(typography, dict) else None),
    }


def _audience_summary(ctx: ClientContext, brief: dict[str, Any]) -> dict[str, Any]:
    intent = ctx.intent or {}
    return {
        "brief_audience": _compact_text(brief.get("audience"), 520),
        "objective": _compact_text(brief.get("objectif") or brief.get("objective"), 220),
        "angle": _compact_text(brief.get("angle"), 360),
        "intent_summary": _compact_text(intent.get("primary_intent") or intent.get("intent"), 220),
        "objections": intent.get("objections") if isinstance(intent.get("objections"), list) else [],
        "desires": intent.get("desires") if isinstance(intent.get("desires"), list) else [],
    }


def _add_fact(out: list[EvidenceFact], label: str, value: Any, source: str, context: str = "") -> None:
    if value is None:
        return
    text = _compact_text(value, 180)
    if not text:
        return
    out.append(EvidenceFact(label=label, value=text, source=source, context=_compact_text(context, 180)))


def _proof_inventory(ctx: ClientContext, brief: dict[str, Any]) -> list[EvidenceFact]:
    facts: list[EvidenceFact] = []
    for number in brief.get("sourced_numbers") or []:
        if isinstance(number, dict):
            _add_fact(
                facts,
                "brief_sourced_number",
                number.get("number"),
                number.get("source") or "BriefV2",
                number.get("context") or "",
            )
    founder = ctx.v143_founder or {}
    voc = ctx.v143_voc or {}
    scarcity = ctx.v143_scarcity or {}
    if isinstance(founder, dict):
        for key in ("name", "bio", "company_revenue_m_eur", "age"):
            _add_fact(facts, f"v143_founder_{key}", founder.get(key), "clients_database.v143.founder")
    if isinstance(voc, dict):
        verbatims = voc.get("verbatims") or voc.get("quotes") or []
        if isinstance(verbatims, list):
            for idx, quote in enumerate(verbatims[:3], start=1):
                _add_fact(facts, f"v143_voc_quote_{idx}", quote, "clients_database.v143.voc")
    if isinstance(scarcity, dict):
        _add_fact(facts, "v143_scarcity", scarcity.get("summary") or scarcity, "clients_database.v143.scarcity")
    if isinstance(ctx.evidence, dict):
        items = ctx.evidence.get("items") or ctx.evidence.get("evidence") or []
        if isinstance(items, list):
            for idx, item in enumerate(items[:6], start=1):
                if isinstance(item, dict):
                    _add_fact(
                        facts,
                        f"evidence_{idx}",
                        item.get("claim") or item.get("text") or item.get("excerpt"),
                        "evidence_ledger.json",
                        item.get("source") or item.get("url") or "",
                    )
    return facts[:12]


def _visual_assets(ctx: ClientContext) -> dict[str, str]:
    assets: dict[str, str] = {}
    preferred = [
        "desktop_clean_fold",
        "mobile_clean_fold",
        "desktop_clean_full",
        "mobile_clean_full",
        "desktop_asis_fold",
        "mobile_asis_fold",
    ]
    for key in preferred:
        path = ctx.screenshots.get(key)
        if path:
            assets[key] = str(path)
    if not assets:
        # Mode 1 often creates a page type that does not exist yet. In that case,
        # reuse stable brand/product screenshots from existing canonical pages.
        base = ROOT / "data" / "captures" / ctx.client
        fallback_candidates = [
            ("home_desktop_fold", base / "home" / "screenshots" / "desktop_clean_fold.png"),
            ("home_mobile_fold", base / "home" / "screenshots" / "mobile_clean_fold.png"),
            ("pricing_desktop_fold", base / "pricing" / "screenshots" / "desktop_clean_fold.png"),
            ("lp_leadgen_desktop_fold", base / "lp_leadgen" / "screenshots" / "desktop_clean_fold.png"),
        ]
        for key, path in fallback_candidates:
            if path.exists():
                assets[key] = str(path)
    return assets


def _scent_contract(ctx: ClientContext, brief: dict[str, Any]) -> dict[str, Any]:
    traffic = brief.get("traffic_source") or []
    has_paid = any("ad" in str(item) for item in traffic)
    source = ctx.scent_trail or {}
    has_source = bool(source)
    return {
        "traffic_source": traffic,
        "requires_explicit_scent_source": bool(has_paid),
        "has_scent_source": has_source,
        "rule": (
            "If paid traffic is selected, ad/source message must be supplied before claiming scent match."
            if has_paid else
            "Scent is useful but not mandatory without paid-source context."
        ),
    }


def _risk_flags(
    *,
    ctx: ClientContext,
    mode: str,
    business_category: str,
    proof_inventory: list[EvidenceFact],
    scent_contract: dict[str, Any],
    visual_assets: dict[str, str],
) -> list[str]:
    flags: list[str] = []
    if mode == "replace" and not ctx.has_audit_complete:
        flags.append("mode_replace_missing_audit_or_recos")
    if mode != "genesis" and not ctx.brand_dna:
        flags.append("missing_brand_dna")
    if business_category == "generic_cro":
        flags.append("business_category_inferred_generic")
    if len(proof_inventory) < 2:
        flags.append("proof_light_no_invention_required")
    if scent_contract.get("requires_explicit_scent_source") and not scent_contract.get("has_scent_source"):
        flags.append("paid_scent_source_missing")
    if not ctx.design_grammar:
        flags.append("missing_design_grammar")
    if not ctx.aura_tokens:
        flags.append("missing_aura_tokens")
    if not visual_assets:
        flags.append("missing_visual_assets")
    return flags


def build_generation_context_pack(
    *,
    client: str,
    page_type: str,
    brief: dict[str, Any],
    mode: str = "complete",
    target_language: str = "FR",
    ctx: ClientContext | None = None,
) -> tuple[GenerationContextPack, ClientContext]:
    """Build the read-only context contract for GSG planning."""
    ctx = ctx or load_client_context(client, page_type)
    business_category = infer_business_category_from_context(ctx, brief)
    proof_inventory = _proof_inventory(ctx, brief)
    scent = _scent_contract(ctx, brief)
    visual_assets = _visual_assets(ctx)
    risk_flags = _risk_flags(
        ctx=ctx,
        mode=mode,
        business_category=business_category,
        proof_inventory=proof_inventory,
        scent_contract=scent,
        visual_assets=visual_assets,
    )
    pack = GenerationContextPack(
        version="gsg-generation-context-v27.2",
        mode=mode,
        client=client,
        page_type=page_type,
        target_language=target_language,
        audit_dependency_policy=MODE_AUDIT_DEPENDENCY.get(mode, "unknown"),
        artefacts={
            "available": list(ctx.available_artefacts),
            "missing": list(ctx.missing_artefacts),
            "completeness_pct": ctx.completeness_pct,
            "has_audit_complete": ctx.has_audit_complete,
            "has_visual_inputs": ctx.has_visual_inputs,
        },
        brand=_brand_summary(ctx),
        business={
            "category": business_category,
            "mode_policy": MODE_AUDIT_DEPENDENCY.get(mode, "unknown"),
        },
        audience=_audience_summary(ctx, brief),
        proof_inventory=proof_inventory,
        scent_contract=scent,
        visual_assets=visual_assets,
        design_sources={
            "brand_dna": bool(ctx.brand_dna),
            "design_grammar": bool(ctx.design_grammar),
            "aura_tokens": bool(ctx.aura_tokens),
            "screenshots_count": len(visual_assets),
            "perception": bool(ctx.perception),
            "spatial": bool(ctx.spatial),
        },
        risk_flags=risk_flags,
    )
    return pack, ctx


def format_context_pack_for_prompt(pack: dict[str, Any]) -> str:
    """Small prompt block for copy context; not a full artefact dump."""
    if not pack:
        return "## GENERATION CONTEXT\n(non disponible)"
    brand = pack.get("brand") or {}
    business = pack.get("business") or {}
    audience = pack.get("audience") or {}
    facts = pack.get("proof_inventory") or []
    lines = [
        "## GENERATION CONTEXT PACK",
        f"- Client: {pack.get('client')}",
        f"- Business category: {business.get('category')}",
        f"- Brand signature: {brand.get('signature') or '(unknown)'}",
        f"- Objective: {audience.get('objective')}",
        f"- Angle: {audience.get('angle')}",
        f"- Proof facts available: {len(facts)}",
        f"- Risk flags: {', '.join(pack.get('risk_flags') or []) or 'none'}",
    ]
    return "\n".join(lines)
