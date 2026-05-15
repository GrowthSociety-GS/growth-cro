"""moteur_gsg.core.brief_v2 — V26.AD Sprint I.

Spec figée : `.claude/docs/reference/FRAMEWORK_CADRAGE_GSG_V26AC.md`. Anti-hallucination : 30+ inputs
structurés en 5 sections. L'utilisateur ne livre plus 3 textareas vagues
{objectif, audience, angle} — il remplit un wizard avec required fields stricts.

Section 1 — MISSION : mode, page_type, client_url, target_language
Section 2 — BUSINESS BRIEF : objective, audience, angle, traffic_source, visitor_mode
Section 3 — INSPIRATIONS : urls, screenshots, anti-references, signature, emotion
Section 4 — MATÉRIEL : docs, citations, blog_urls, proofs, sourced_numbers, testimonials
Section 5 — VISUEL & DA : forbidden_patterns, logo, photos, font_override, palette

La dataclass `BriefV2` expose `validate()` qui retourne la liste des erreurs.
Les sous-dataclasses `SourcedNumber` et `Testimonial` sont des structures
typées pour empêcher Sonnet d'inventer des chiffres ou des testimoniaux.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Literal, Optional


# Enums déclarés via Literal — utilisés à la fois pour typing et validation runtime.
ModeType = Literal["complete", "replace", "extend", "elevate", "genesis"]

PageType = Literal[
    "home", "lp_listicle", "lp_sales", "lp_leadgen", "pdp",
    "collection", "pricing", "quiz_vsl", "vsl", "advertorial",
    "comparison", "signup", "challenge", "bundle_standalone",
    "squeeze", "webinar", "thank_you_page",
]

LangType = Literal["FR", "EN", "ES", "DE", "IT", "PT", "NL", "JP"]

TrafficSource = Literal[
    "cold_ad_meta", "cold_ad_google", "warm_retargeting",
    "organic_seo", "email_list", "referral", "direct",
]

VisitorMode = Literal["scan_30s", "read_5min", "decide_impulsive", "compare_research"]

ProofType = Literal[
    "logos_clients_tier1", "note_trustpilot_sourced", "etudes_citees",
    "chiffres_internes", "temoignages_named", "garantie_specifique", "certifications",
]

ForbiddenVisualPattern = Literal[
    "stock_photos", "gradient_mesh", "ai_generated_images",
    "checkmark_icons_systematic", "lifestyle_photography_hero",
    "glassmorphism", "drop_caps", "neumorphism",
]

# Sets runtime pour validation (les types Literal ne sont pas vérifiés à l'exécution par Python).
_ALLOWED_MODES = {"complete", "replace", "extend", "elevate", "genesis"}
_ALLOWED_PAGE_TYPES = {
    "home", "lp_listicle", "lp_sales", "lp_leadgen", "pdp", "collection",
    "pricing", "quiz_vsl", "vsl", "advertorial", "comparison", "signup",
    "challenge", "bundle_standalone", "squeeze", "webinar", "thank_you_page",
}
_ALLOWED_LANGS = {"FR", "EN", "ES", "DE", "IT", "PT", "NL", "JP"}
_ALLOWED_TRAFFIC = {
    "cold_ad_meta", "cold_ad_google", "warm_retargeting",
    "organic_seo", "email_list", "referral", "direct",
}
_ALLOWED_VISITOR_MODES = {"scan_30s", "read_5min", "decide_impulsive", "compare_research"}
_ALLOWED_PROOFS = {
    "logos_clients_tier1", "note_trustpilot_sourced", "etudes_citees",
    "chiffres_internes", "temoignages_named", "garantie_specifique", "certifications",
}
_ALLOWED_FORBIDDEN_VISUAL = {
    "stock_photos", "gradient_mesh", "ai_generated_images",
    "checkmark_icons_systematic", "lifestyle_photography_hero",
    "glassmorphism", "drop_caps", "neumorphism",
}


# ─────────────────────────────────────────────────────────────────────────────
# Sub-structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SourcedNumber:
    """Section 4.5 — chiffre interne avec source vérifiable (anti-invention)."""
    number: str
    source: str
    context: str

    def validate(self) -> list[str]:
        errors = []
        if not self.number or not self.number.strip():
            errors.append("SourcedNumber.number is empty")
        if not self.source or not self.source.strip():
            errors.append("SourcedNumber.source is empty (où vient ce chiffre ?)")
        if not self.context or not self.context.strip():
            errors.append("SourcedNumber.context is empty (que mesure-t-il ?)")
        return errors


@dataclass
class Testimonial:
    """Section 4.6 — testimonial nommé et autorisé (anti-Sarah-32-ans).

    V27.2-H Sprint 15 (T15-2) : anti-invention guard renforcé. Le brief
    doit fournir ``source_url`` (URL publique de la citation : G2,
    Trustpilot, blog client, communiqué presse, etc.) OU
    ``sourced_from="internal_brief"`` pour signifier explicitement que
    le testimonial vient d'une qualification interne non-publique
    (auquel cas le renderer marque ``[non-vérifié]`` overlay).

    Mathis 2026-05-15 : *"Screen 3 : c'est les vrais infos ça ? Les
    vrais avis ? J'en doute fortement"*. Cette validation refuse les
    testimonials sans aucune attribution vérifiable.
    """
    name: str
    position: str
    company: str
    quote: str
    photo_path: Optional[Path] = None
    authorized: bool = True
    source_url: Optional[str] = None  # T15-2: URL publique du témoignage
    sourced_from: Optional[str] = None  # T15-2: "internal_brief" si pas d'URL publique
    # V27.2-J Sprint 18 T18-2 : optional Unsplash portrait ID for the
    # avatar (replaces letter-monogram). Format `<photo-id>` matching
    # `https://images.unsplash.com/photo-<id>`.
    unsplash_portrait_id: Optional[str] = None

    def validate(self) -> list[str]:
        errors = []
        for fname in ("name", "position", "company", "quote"):
            v = getattr(self, fname)
            if not v or (isinstance(v, str) and not v.strip()):
                errors.append(f"Testimonial.{fname} is empty")
        if not self.authorized:
            errors.append(f"Testimonial.{self.name}: authorized=False — refus d'utilisation pour LP publique")
        if self.photo_path and not Path(self.photo_path).exists():
            errors.append(f"Testimonial.{self.name}: photo_path '{self.photo_path}' does not exist on disk")
        # T15-2 anti-invention guard: testimonial sans source publique ET
        # sans flag explicite internal_brief = refus.
        has_url = bool((self.source_url or "").strip())
        is_internal = (self.sourced_from or "").strip().lower() == "internal_brief"
        if not has_url and not is_internal:
            errors.append(
                f"Testimonial.{self.name}: ni source_url publique ni sourced_from='internal_brief' "
                f"— testimonial considéré inventé (anti-invention guard T15-2)."
            )
        return errors

    def is_verified(self) -> bool:
        """True if the testimonial has a public source URL (display normally).

        False = display with a [non-vérifié] overlay or skip entirely
        depending on the renderer policy.
        """
        return bool((self.source_url or "").strip())


# ─────────────────────────────────────────────────────────────────────────────
# Main BriefV2 dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BriefV2:
    """Brief utilisateur structuré — 5 sections du framework V26.AC.

    Construit côté webapp (wizard 5 étapes) ou via JSON file. La dataclass
    expose `validate()` qui retourne la liste des erreurs (vide = OK).
    """

    # — Section 1 : MISSION (4 fields) —
    mode: str  # ModeType
    page_type: str  # PageType
    target_language: str  # LangType
    client_url: Optional[str] = None  # required sauf genesis

    # — Section 2 : BUSINESS BRIEF (5 fields) —
    objective: str = ""
    audience: str = ""
    angle: str = ""
    traffic_source: list[str] = field(default_factory=list)  # list[TrafficSource]
    visitor_mode: str = "scan_30s"  # VisitorMode

    # — Section 3 : INSPIRATIONS & RÉFÉRENCES —
    inspiration_urls: list[str] = field(default_factory=list)
    inspiration_reasons: Optional[str] = None
    inspiration_screenshots: list[Path] = field(default_factory=list)
    anti_references: list[str] = field(default_factory=list)
    desired_signature: Optional[str] = None
    desired_emotion: Optional[str] = None

    # — Section 4 : MATÉRIEL CONTENU —
    source_documents: list[Path] = field(default_factory=list)
    founder_citations: list[str] = field(default_factory=list)
    client_blog_urls: list[str] = field(default_factory=list)
    available_proofs: list[str] = field(default_factory=list)  # list[ProofType]
    sourced_numbers: list[SourcedNumber] = field(default_factory=list)
    testimonials: list[Testimonial] = field(default_factory=list)
    existing_page_url: Optional[str] = None  # required Mode 2 REPLACE
    concept_description: Optional[str] = None  # required Mode 3 EXTEND
    # V27.2-H Sprint 15 (T15-3): path to a validated LP-Creator copy.md.
    # When present, the moteur GSG skips the Sonnet copy generation and
    # uses this copy as canonical (Mathis-validated 20/20 phrasing
    # preserved verbatim, named entities like Amazon/HBO kept).
    lp_creator_validated_copy_path: Optional[str] = None

    # — Section 5 : VISUEL & DA —
    forbidden_visual_patterns: list[str] = field(default_factory=list)
    client_logo: Optional[Path] = None
    product_photos_real: list[Path] = field(default_factory=list)
    font_override: Optional[str] = None
    palette_override: list[str] = field(default_factory=list)  # hex codes
    must_include_elements: list[str] = field(default_factory=list)

    # ─────────────────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """Retourne la liste des erreurs de validation (vide = brief valide)."""
        errors: list[str] = []

        # — Section 1 : MISSION —
        if self.mode not in _ALLOWED_MODES:
            errors.append(f"mode='{self.mode}' invalide. Allowed: {sorted(_ALLOWED_MODES)}")
        if self.page_type not in _ALLOWED_PAGE_TYPES:
            errors.append(f"page_type='{self.page_type}' invalide. Allowed: {sorted(_ALLOWED_PAGE_TYPES)}")
        if self.target_language not in _ALLOWED_LANGS:
            errors.append(f"target_language='{self.target_language}' invalide. Allowed: {sorted(_ALLOWED_LANGS)}")

        if self.mode != "genesis":
            if not self.client_url or not str(self.client_url).strip():
                errors.append("client_url required (sauf mode='genesis')")
            elif not str(self.client_url).startswith(("http://", "https://")):
                errors.append(f"client_url must start with http(s)://, got '{self.client_url}'")

        # — Section 2 : BUSINESS BRIEF —
        if not self.objective or len(self.objective.strip()) < 10:
            errors.append("objective too short (≥10 chars required, 1-2 phrases)")
        if not self.audience or len(self.audience.strip()) < 100:
            errors.append("audience too short (≥100 chars required — Persona + 3 peurs + 3 désirs + Schwartz level)")
        elif len(self.audience) > 1000:
            errors.append(f"audience too long ({len(self.audience)} chars > 1000)")
        if not self.angle or len(self.angle.strip()) < 50:
            errors.append("angle too short (≥50 chars required — hook éditorial / signature)")
        elif len(self.angle) > 500:
            errors.append(f"angle too long ({len(self.angle)} chars > 500)")

        if not self.traffic_source:
            errors.append("traffic_source required (≥1 source)")
        else:
            for ts in self.traffic_source:
                if ts not in _ALLOWED_TRAFFIC:
                    errors.append(f"traffic_source contains invalid '{ts}'. Allowed: {sorted(_ALLOWED_TRAFFIC)}")

        if self.visitor_mode not in _ALLOWED_VISITOR_MODES:
            errors.append(f"visitor_mode='{self.visitor_mode}' invalide. Allowed: {sorted(_ALLOWED_VISITOR_MODES)}")

        # — Section 3 : INSPIRATIONS (mode-conditionnel) —
        if self.mode == "elevate" and not self.inspiration_urls:
            errors.append("inspiration_urls (≥1) required pour mode='elevate'")
        if len(self.inspiration_urls) > 5:
            errors.append(f"inspiration_urls trop nombreuses ({len(self.inspiration_urls)} > 5)")
        for url in self.inspiration_urls:
            if not url.startswith(("http://", "https://")):
                errors.append(f"inspiration_urls contains invalid URL '{url}' (must start with http(s)://)")
        if len(self.inspiration_screenshots) > 10:
            errors.append(f"inspiration_screenshots trop nombreuses ({len(self.inspiration_screenshots)} > 10)")
        for path in self.inspiration_screenshots:
            if not Path(path).exists():
                errors.append(f"inspiration_screenshot '{path}' does not exist on disk")

        # — Section 4 : MATÉRIEL (proof consistency) —
        if len(self.source_documents) > 5:
            errors.append(f"source_documents trop nombreux ({len(self.source_documents)} > 5)")
        for path in self.source_documents:
            if not Path(path).exists():
                errors.append(f"source_document '{path}' does not exist on disk")

        for proof in self.available_proofs:
            if proof not in _ALLOWED_PROOFS:
                errors.append(f"available_proofs contains invalid '{proof}'. Allowed: {sorted(_ALLOWED_PROOFS)}")

        # Anti-invention : si proof="chiffres_internes" coché, sourced_numbers OBLIGATOIRE
        if "chiffres_internes" in self.available_proofs and not self.sourced_numbers:
            errors.append("sourced_numbers required if 'chiffres_internes' coché (anti-invention)")
        # Idem testimonials
        if "temoignages_named" in self.available_proofs and not self.testimonials:
            errors.append("testimonials required if 'temoignages_named' coché (anti-Sarah-32-ans)")

        for sn in self.sourced_numbers:
            errors.extend(sn.validate())
        for t in self.testimonials:
            errors.extend(t.validate())

        # Mode-specific required fields
        if self.mode == "replace":
            if not self.existing_page_url:
                errors.append("existing_page_url required pour mode='replace'")
            elif not self.existing_page_url.startswith(("http://", "https://")):
                errors.append(f"existing_page_url must start with http(s)://, got '{self.existing_page_url}'")
        if self.mode == "extend":
            if not self.concept_description or len(self.concept_description.strip()) < 20:
                errors.append("concept_description required pour mode='extend' (≥20 chars)")

        # — Section 5 : VISUEL & DA —
        for fp in self.forbidden_visual_patterns:
            # Patterns custom autorisés (free text), mais doivent être non-vides
            if not fp or not fp.strip():
                errors.append("forbidden_visual_patterns contains empty entry")
        if self.client_logo and not Path(self.client_logo).exists():
            errors.append(f"client_logo '{self.client_logo}' does not exist on disk")
        if len(self.product_photos_real) > 10:
            errors.append(f"product_photos_real trop nombreuses ({len(self.product_photos_real)} > 10)")
        for path in self.product_photos_real:
            if not Path(path).exists():
                errors.append(f"product_photo '{path}' does not exist on disk")
        for hex_color in self.palette_override:
            if not _is_valid_hex(hex_color):
                errors.append(f"palette_override contains invalid hex '{hex_color}' (expected #rrggbb or #rgb)")

        return errors

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────

    def is_valid(self) -> bool:
        return not self.validate()

    def to_legacy_brief(self) -> dict:
        """Mapping BriefV2 → dict legacy {objectif, audience, angle, notes} pour
        compat avec Mode 1 V26.AA / persona_narrator (qui prennent l'ancien dict).

        Les fields BriefV2 non-mappables sont packés dans `notes` (free text).
        """
        notes_lines = []
        if self.desired_signature:
            notes_lines.append(f"DESIRED SIGNATURE : {self.desired_signature}")
        if self.desired_emotion:
            notes_lines.append(f"DESIRED EMOTION : {self.desired_emotion}")
        if self.must_include_elements:
            notes_lines.append(f"MUST_INCLUDE : {', '.join(self.must_include_elements)}")
        if self.forbidden_visual_patterns:
            notes_lines.append(f"FORBID_VISUAL : {', '.join(self.forbidden_visual_patterns)}")
        if self.traffic_source:
            notes_lines.append(f"TRAFFIC : {', '.join(self.traffic_source)} / VISITOR_MODE : {self.visitor_mode}")
        if self.sourced_numbers:
            sn_lines = [f"  - {sn.number} (source: {sn.source}, context: {sn.context})" for sn in self.sourced_numbers]
            notes_lines.append("SOURCED_NUMBERS (anti-invention) :\n" + "\n".join(sn_lines))
        if self.testimonials:
            t_lines = [f"  - « {t.quote} » — {t.name}, {t.position} @ {t.company}" for t in self.testimonials if t.authorized]
            if t_lines:
                notes_lines.append("TESTIMONIALS (vérifiés) :\n" + "\n".join(t_lines))
        if self.client_blog_urls:
            notes_lines.append(f"CLIENT_BLOG_REFS : {', '.join(self.client_blog_urls)}")
        if self.existing_page_url:
            notes_lines.append(f"EXISTING_PAGE_TO_REPLACE : {self.existing_page_url}")
        if self.concept_description:
            notes_lines.append(f"CONCEPT (Mode 3 EXTEND) : {self.concept_description}")
        if self.inspiration_urls:
            notes_lines.append(f"INSPIRATION_URLS (Mode 4 ELEVATE) : {', '.join(self.inspiration_urls)}")

        # Sprint 13 / V27.2-G+ — preserve the rich BriefV2 fields as structured
        # data in addition to the legacy `notes` text blob, so downstream
        # consumers (planner._has_rich_listicle_signals, prompt_assembly.
        # _compact_brief_for_copy) can detect testimonials / sourced_numbers /
        # must_include_elements directly without re-parsing free-text notes.
        legacy: dict[str, Any] = {
            "objectif": self.objective,
            "objective": self.objective,
            "audience": self.audience,
            "angle": self.angle,
            "notes": "\n".join(notes_lines) if notes_lines else "",
        }
        if self.must_include_elements:
            legacy["must_include_elements"] = list(self.must_include_elements)
        if self.testimonials:
            legacy["testimonials"] = [
                {
                    "name": t.name,
                    "position": t.position,
                    "company": t.company,
                    "quote": t.quote,
                    "authorized": t.authorized,
                    # T15-2: propagate source attribution into the legacy
                    # brief so the renderer can decide between "verified"
                    # display and "[non-vérifié]" overlay.
                    "source_url": t.source_url or "",
                    "sourced_from": t.sourced_from or "",
                    "is_verified": t.is_verified(),
                    # T18-2: Unsplash portrait ID for the avatar.
                    "unsplash_portrait_id": t.unsplash_portrait_id or "",
                }
                for t in self.testimonials
                if t.authorized
            ]
        if self.sourced_numbers:
            legacy["sourced_numbers"] = [
                {"number": sn.number, "source": sn.source, "context": sn.context}
                for sn in self.sourced_numbers
            ]
        if self.concept_description:
            legacy["concept_description"] = self.concept_description
        # T15-3: propagate the canonical LP-Creator copy path so
        # mode_1_complete can short-circuit the Sonnet copy stage.
        if self.lp_creator_validated_copy_path:
            legacy["lp_creator_validated_copy_path"] = self.lp_creator_validated_copy_path
        if self.anti_references:
            legacy["anti_references"] = list(self.anti_references)
        if self.forbidden_visual_patterns:
            legacy["forbidden_visual_patterns"] = list(self.forbidden_visual_patterns)
        if self.available_proofs:
            legacy["available_proofs"] = list(self.available_proofs)
        if self.desired_signature:
            legacy["desired_signature"] = self.desired_signature
        if self.desired_emotion:
            legacy["desired_emotion"] = self.desired_emotion
        if self.traffic_source:
            legacy["traffic_source"] = list(self.traffic_source)
        if self.visitor_mode:
            legacy["visitor_mode"] = self.visitor_mode
        return legacy

    def to_dict(self) -> dict:
        """Serialize en dict JSON-friendly (Path → str, dataclasses → dict)."""
        d = asdict(self)
        # Path → str récursif
        d = _stringify_paths(d)
        return d

    @classmethod
    def from_dict(cls, raw: dict) -> "BriefV2":
        """Construit BriefV2 depuis dict (typiquement JSON parse). Convertit
        les sous-objets typés (sourced_numbers, testimonials)."""
        sns = [SourcedNumber(**sn) if isinstance(sn, dict) else sn for sn in raw.get("sourced_numbers", [])]
        ts = [Testimonial(**t) if isinstance(t, dict) else t for t in raw.get("testimonials", [])]

        kwargs = {k: v for k, v in raw.items() if k not in {"sourced_numbers", "testimonials"}}
        # Path fields — accept str → Path
        for path_field in ("client_logo",):
            if path_field in kwargs and kwargs[path_field]:
                kwargs[path_field] = Path(kwargs[path_field])
        for list_path_field in ("inspiration_screenshots", "source_documents", "product_photos_real"):
            if list_path_field in kwargs:
                kwargs[list_path_field] = [Path(p) for p in (kwargs[list_path_field] or [])]
        return cls(sourced_numbers=sns, testimonials=ts, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_valid_hex(s: str) -> bool:
    if not s or not s.startswith("#"):
        return False
    body = s[1:]
    if len(body) not in (3, 6, 8):  # #rgb, #rrggbb, #rrggbbaa
        return False
    return all(c in "0123456789abcdefABCDEF" for c in body)


def _stringify_paths(obj):
    if isinstance(obj, dict):
        return {k: _stringify_paths(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_paths(x) for x in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj
