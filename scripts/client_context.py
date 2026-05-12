"""client_context.py V26.AC Sprint F — ROUTER RACINE GrowthCRO.

Réponse à l'insight Mathis 2026-05-04 :
"On avait pris un virage où l'accès à toutes nos données, nos skills, etc. se
faisait à la racine en amont dans GrowthCRO et ensuite était prête à être
branchée, distribuée intelligemment à Audit ou GSG en fonction de qui on appelle."

L'insight Pivot V26.AA (doctrine racine partagée) doit s'étendre à TOUS les
artefacts client, pas juste la doctrine. Ce module est LE ROUTER CENTRAL.

Architecture :
  Audit Engine, GSG, Multi-judge consomment TOUS via `load_client_context(client, page_type)`.
  Plus jamais "j'ai oublié de charger X" ou "j'ai dupliqué un load_brand_dna".

Chaque artefact connu du système est référencé ici. Si un artefact existe sur
disque pour un client, il est automatiquement chargé. S'il manque, il apparaît
dans `missing_artefacts` (debug + telemetry).

Usage :
    from scripts.client_context import load_client_context

    ctx = load_client_context("weglot", page_type="lp_listicle")

    # Tous les artefacts disponibles via attributs
    ctx.brand_dna           # dict (palette, voix, diff E1) ou None
    ctx.aura_tokens         # dict (Golden Ratio + font blacklist) ou None
    ctx.screenshots         # {desktop_clean_full: Path, mobile_clean_full: Path, ...}
    ctx.perception          # dict DBSCAN clusters + roles ou None
    ctx.recos_final         # dict recos enrichies Sonnet ou None
    ctx.v143_founder        # dict Founder bio ou None
    ctx.v143_voc            # dict Voice of Customer Trustpilot ou None
    ctx.evidence            # dict preuves traçables ou None
    ctx.intent              # dict intent + audience structurée ou None
    ctx.design_grammar      # dict 7 prescriptifs ou None
    ctx.reality_layer       # dict ground truth Catchr/Meta/etc ou None

    # Métadonnées
    ctx.available_artefacts # list[str] des chargés avec succès
    ctx.missing_artefacts   # list[str] des absents

CLI :
    python3 scripts/client_context.py weglot lp_listicle  # rapport complet
    python3 scripts/client_context.py --availability-report-all  # tous clients
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPTURES = ROOT / "data" / "captures"


@dataclass
class ClientContext:
    """Contexte client unifié — TOUS les artefacts disponibles."""

    # Identification
    client: str
    page_type: Optional[str] = None

    # — Globaux client (data/captures/<client>/) —
    brand_dna: Optional[dict] = None
    intent: Optional[dict] = None
    canonical_tunnel: Optional[dict] = None
    discovered_pages: Optional[dict] = None
    site_audit: Optional[dict] = None
    scent_trail: Optional[dict] = None
    design_grammar: Optional[dict] = None
    aura_tokens: Optional[dict] = None  # peut être à la racine data/_aura_<c>.json OR captures/<c>/<p>/aura_tokens.json

    # — V143 enrichment (data/clients_database.json.v143.<client>.*) —
    v143_founder: Optional[dict] = None
    v143_voc: Optional[dict] = None
    v143_scarcity: Optional[dict] = None

    # — Per-page artefacts (data/captures/<client>/<page_type>/) —
    capture: Optional[dict] = None
    page_html_path: Optional[pathlib.Path] = None
    screenshots: dict[str, pathlib.Path] = field(default_factory=dict)
    perception: Optional[dict] = None
    spatial: Optional[dict] = None
    components: Optional[dict] = None
    critic_report: Optional[dict] = None

    # Scoring per-page
    score_pillars: dict[str, dict] = field(default_factory=dict)  # {hero, persuasion, ux, coherence, psycho, tech, utility_banner}
    score_page_type: Optional[dict] = None

    # Recos per-page
    recos_prompts: Optional[dict] = None
    recos_final: Optional[dict] = None
    recos_enriched: Optional[dict] = None
    recos_dedup_report: Optional[dict] = None

    # Evidence + lifecycle (V26.A+B)
    evidence: Optional[dict] = None

    # — Reality Layer V26.C (data/captures/<client>/<page>/reality_layer.json) —
    reality_layer: Optional[dict] = None

    # — Métadonnées —
    available_artefacts: list[str] = field(default_factory=list)
    missing_artefacts: list[str] = field(default_factory=list)

    @property
    def has_brand_dna(self) -> bool:
        return self.brand_dna is not None

    @property
    def has_visual_inputs(self) -> bool:
        """Sonnet peut faire de la vision multimodale ?"""
        return bool(self.screenshots) and self.brand_dna is not None

    @property
    def has_audit_complete(self) -> bool:
        """L'audit V26 est-il complet pour cette page ?"""
        return (self.score_page_type is not None
                and self.recos_final is not None
                and len(self.score_pillars) >= 4)

    @property
    def has_v143_enrichment(self) -> bool:
        return any([self.v143_founder, self.v143_voc, self.v143_scarcity])

    @property
    def has_reality_layer(self) -> bool:
        return self.reality_layer is not None

    @property
    def completeness_pct(self) -> float:
        """% d'artefacts disponibles sur le total possible."""
        total = len(self.available_artefacts) + len(self.missing_artefacts)
        return round(len(self.available_artefacts) / total * 100, 1) if total > 0 else 0


# ─────────────────────────────────────────────────────────────────────────────
# Chargeurs atomiques (1 par artefact)
# ─────────────────────────────────────────────────────────────────────────────

def _safe_json(p: pathlib.Path) -> Optional[dict]:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _load_brand_dna(client: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / "brand_dna.json")


def _load_intent(client: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / "client_intent.json")


def _load_canonical_tunnel(client: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / "canonical_tunnel.json")


def _load_discovered_pages(client: str) -> Optional[dict]:
    p = CAPTURES / client / "discovered_pages_v25.json"
    if p.exists():
        return _safe_json(p)
    return _safe_json(CAPTURES / client / "pages_discovered.json")


def _load_site_audit(client: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / "site_audit.json")


def _load_scent_trail(client: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / "scent_trail.json")


def _load_design_grammar(client: str) -> Optional[dict]:
    """Charge les 7 fichiers design_grammar/ (V30) pour un client."""
    dgd = CAPTURES / client / "design_grammar"
    if not dgd.exists():
        return None
    return {
        "tokens": _safe_json(dgd / "tokens.json"),
        "components": _safe_json(dgd / "component_grammar.json"),
        "sections": _safe_json(dgd / "section_grammar.json"),
        "composition": _safe_json(dgd / "composition_rules.json"),
        "forbidden": _safe_json(dgd / "brand_forbidden_patterns.json"),
        "gates": _safe_json(dgd / "quality_gates.json"),
        "tokens_css_path": dgd / "tokens.css" if (dgd / "tokens.css").exists() else None,
    }


def _load_aura(client: str, page_type: Optional[str] = None) -> Optional[dict]:
    """Charge AURA tokens (data/_aura_<client>.json racine OR captures/<c>/<p>/aura_tokens.json)."""
    # Priorité 1 : per-page (le plus récent)
    if page_type:
        per_page = CAPTURES / client / page_type / "aura_tokens.json"
        if per_page.exists():
            return _safe_json(per_page)
    # Priorité 2 : racine client
    racine = ROOT / "data" / f"_aura_{client}.json"
    return _safe_json(racine)


def _load_v143(client: str) -> dict:
    """Charge clients_database.json puis extrait .v143.<client>.* (founder, voc, scarcity)."""
    db_path = ROOT / "data" / "clients_database.json"
    db = _safe_json(db_path) or {}
    # Format possible : v143.<client> = {founder, voc, scarcity} OR {founder: {<client>: ...}, ...}
    v143 = db.get("v143", {}) or {}
    by_client = v143.get(client, {})
    if by_client:
        return {
            "founder": by_client.get("founder"),
            "voc": by_client.get("voc"),
            "scarcity": by_client.get("scarcity"),
        }
    return {"founder": None, "voc": None, "scarcity": None}


def _load_capture(client: str, page_type: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / page_type / "capture.json")


def _load_screenshots(client: str, page_type: str) -> dict[str, pathlib.Path]:
    """Liste les screenshots disponibles pour la page."""
    sd = CAPTURES / client / page_type / "screenshots"
    if not sd.exists():
        return {}
    out = {}
    for png in sd.glob("*.png"):
        # Format : desktop_asis_full.png, desktop_clean_full.png, mobile_*, etc.
        out[png.stem] = png
    return out


def _load_perception(client: str, page_type: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / page_type / "perception_v13.json")


def _load_spatial(client: str, page_type: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / page_type / "spatial_v9.json")


def _load_score_pillars(client: str, page_type: str) -> dict[str, dict]:
    pd = CAPTURES / client / page_type
    out = {}
    for pillar in ("hero", "persuasion", "ux", "coherence", "psycho", "tech", "utility_banner"):
        d = _safe_json(pd / f"score_{pillar}.json")
        if d:
            out[pillar] = d
    return out


def _load_recos_final(client: str, page_type: str) -> Optional[dict]:
    pd = CAPTURES / client / page_type
    for fn in ("recos_v13_final.json", "recos_v13_api.json", "recos_enriched.json"):
        d = _safe_json(pd / fn)
        if d:
            return d
    return None


def _load_evidence(client: str, page_type: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / page_type / "evidence_ledger.json")


def _load_reality_layer(client: str, page_type: str) -> Optional[dict]:
    return _safe_json(CAPTURES / client / page_type / "reality_layer.json")


# ─────────────────────────────────────────────────────────────────────────────
# Router central — load_client_context
# ─────────────────────────────────────────────────────────────────────────────

# Liste des artefacts attendus (pour audit completeness)
EXPECTED_GLOBAL_ARTEFACTS = [
    "brand_dna", "intent", "canonical_tunnel", "discovered_pages",
    "site_audit", "scent_trail", "design_grammar", "aura_tokens",
    "v143_founder", "v143_voc", "v143_scarcity",
]
EXPECTED_PER_PAGE_ARTEFACTS = [
    "capture", "screenshots", "perception", "spatial",
    "score_page_type", "recos_final", "evidence", "reality_layer",
]


def load_client_context(
    client: str,
    page_type: Optional[str] = None,
) -> ClientContext:
    """LE ROUTER CENTRAL — charge TOUT ce qui existe pour le client (+page si fourni).

    Utilisé par : Audit Engine, GSG (5 modes), Multi-judge.
    """
    ctx = ClientContext(client=client, page_type=page_type)

    # ── Globaux client ──
    artefact_loaders = [
        ("brand_dna", lambda: _load_brand_dna(client)),
        ("intent", lambda: _load_intent(client)),
        ("canonical_tunnel", lambda: _load_canonical_tunnel(client)),
        ("discovered_pages", lambda: _load_discovered_pages(client)),
        ("site_audit", lambda: _load_site_audit(client)),
        ("scent_trail", lambda: _load_scent_trail(client)),
        ("design_grammar", lambda: _load_design_grammar(client)),
        ("aura_tokens", lambda: _load_aura(client, page_type)),
    ]
    for name, loader in artefact_loaders:
        val = loader()
        if val is not None:
            setattr(ctx, name, val)
            ctx.available_artefacts.append(name)
        else:
            ctx.missing_artefacts.append(name)

    # ── V143 enrichment (split en 3 sub-artefacts) ──
    v143 = _load_v143(client)
    for sub in ("founder", "voc", "scarcity"):
        val = v143.get(sub)
        attr = f"v143_{sub}"
        if val is not None:
            setattr(ctx, attr, val)
            ctx.available_artefacts.append(attr)
        else:
            ctx.missing_artefacts.append(attr)

    # ── Per-page artefacts (si page_type fourni) ──
    if page_type:
        page_loaders = [
            ("capture", lambda: _load_capture(client, page_type)),
            ("perception", lambda: _load_perception(client, page_type)),
            ("spatial", lambda: _load_spatial(client, page_type)),
            ("score_page_type", lambda: _safe_json(CAPTURES / client / page_type / "score_page_type.json")),
            ("recos_final", lambda: _load_recos_final(client, page_type)),
            ("evidence", lambda: _load_evidence(client, page_type)),
            ("reality_layer", lambda: _load_reality_layer(client, page_type)),
        ]
        for name, loader in page_loaders:
            val = loader()
            if val is not None:
                setattr(ctx, name, val)
                ctx.available_artefacts.append(name)
            else:
                ctx.missing_artefacts.append(name)

        # Screenshots (dict)
        screens = _load_screenshots(client, page_type)
        if screens:
            ctx.screenshots = screens
            ctx.available_artefacts.append("screenshots")
        else:
            ctx.missing_artefacts.append("screenshots")

        # page_html
        page_html = CAPTURES / client / page_type / "page.html"
        if page_html.exists():
            ctx.page_html_path = page_html
            ctx.available_artefacts.append("page_html")
        else:
            ctx.missing_artefacts.append("page_html")

        # Score pillars
        pillars = _load_score_pillars(client, page_type)
        if pillars:
            ctx.score_pillars = pillars
            ctx.available_artefacts.append(f"score_pillars ({len(pillars)})")
        else:
            ctx.missing_artefacts.append("score_pillars")

    return ctx


def availability_report(client: str, page_type: Optional[str] = None) -> str:
    """Rapport markdown de complétude pour un client."""
    ctx = load_client_context(client, page_type)
    lines = [
        f"# Client Context Availability — {client} / {page_type or '(globals only)'}",
        "",
        f"**Completeness** : {ctx.completeness_pct}%",
        f"**Has brand_dna** : {ctx.has_brand_dna}",
        f"**Has visual inputs (screenshots + brand)** : {ctx.has_visual_inputs}",
        f"**Has audit complete** : {ctx.has_audit_complete}",
        f"**Has v143 enrichment** : {ctx.has_v143_enrichment}",
        f"**Has reality layer** : {ctx.has_reality_layer}",
        "",
        f"## ✅ Available ({len(ctx.available_artefacts)})",
        *[f"- {a}" for a in ctx.available_artefacts],
        "",
        f"## ❌ Missing ({len(ctx.missing_artefacts)})",
        *[f"- {a}" for a in ctx.missing_artefacts],
        "",
        "## Screenshots détaillés",
        *[f"  - {name} : {path.name}" for name, path in ctx.screenshots.items()],
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("client", nargs="?")
    ap.add_argument("page_type", nargs="?", default=None)
    ap.add_argument("--availability-report-all", action="store_true")
    args = ap.parse_args()

    if args.availability_report_all:
        # Iterate sur les 56 curatés
        curated = json.load(open(ROOT / "data" / "curated_clients_v26.json"))
        print("# Availability Report — 56 clients curatés V26\n")
        print("| Client | Brand DNA | AURA | Visual | Audit Page | V143 | Reality |")
        print("|---|---|---|---|---|---|---|")
        for c in curated["clients"]:
            slug = c["id"]
            page = c["page_types"][0] if c["page_types"] else None
            ctx = load_client_context(slug, page)
            print(f"| {slug} | {'✓' if ctx.has_brand_dna else '❌'} | {'✓' if ctx.aura_tokens else '❌'} | {'✓' if ctx.has_visual_inputs else '❌'} | {'✓' if ctx.has_audit_complete else '❌'} | {'✓' if ctx.has_v143_enrichment else '❌'} | {'✓' if ctx.has_reality_layer else '❌'} |")
        sys.exit(0)

    if not args.client:
        ap.error("client required (or use --availability-report-all)")

    print(availability_report(args.client, args.page_type))
