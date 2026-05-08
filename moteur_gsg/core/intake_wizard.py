"""Deterministic GSG intake/wizard contract.

This layer is the product entrypoint before BriefV2. It turns a rough user
request into a structured generation request, then pre-fills BriefV2 through the
root client context. It does not call an LLM and it does not generate HTML.
"""
from __future__ import annotations

import json
import pathlib
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse

from .brief_v2 import BriefV2
from .brief_v2_prefiller import prefill_brief_v2_from_client

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLIENTS_DB = ROOT / "data" / "clients_database.json"
DRAFT_DIR = ROOT / "data" / "_briefs_v2_drafts"

PAGE_TYPE_ALIASES = {
    "lp_listicle": ("lp_listicle", "listicle", "liste", "10 raisons", "raisons"),
    "advertorial": ("advertorial", "article natif", "native article"),
    "lp_sales": ("lp_sales", "sales page", "page sales", "page de vente", "longform sales"),
    "lp_leadgen": ("lp_leadgen", "leadgen", "lead gen", "lead generation", "formulaire"),
    "pdp": ("pdp", "product page", "fiche produit", "page produit"),
    "pricing": ("pricing", "tarifs", "pricing page", "page pricing", "page tarif"),
    "home": ("home", "homepage", "home page", "accueil"),
    "comparison": ("comparison", "comparatif", "comparison page"),
    "quiz_vsl": ("quiz_vsl", "quiz vsl", "quiz"),
    "vsl": ("vsl", "video sales letter"),
}

MODE_ALIASES = {
    "replace": ("replace", "refonte", "remplacer", "refaire", "page existante"),
    "extend": ("extend", "nouveau concept", "concept nouveau", "extension"),
    "elevate": ("elevate", "inspiration", "inspirations", "plus ambitieux", "elevate"),
    "genesis": ("genesis", "sans url", "nouvelle marque", "brand from scratch"),
    "complete": ("complete", "nouvelle lp", "lp autonome", "landing page", "génère", "genere"),
}

LANG_ALIASES = {
    "FR": ("fr", "français", "francais", "en français", "en francais"),
    "EN": ("en", "anglais", "english", "in english"),
    "ES": ("es", "espagnol", "spanish"),
    "DE": ("de", "allemand", "german"),
    "IT": ("it", "italien", "italian"),
    "PT": ("pt", "portugais", "portuguese"),
    "NL": ("nl", "néerlandais", "neerlandais", "dutch"),
    "JP": ("jp", "japonais", "japanese"),
}


@dataclass
class GSGGenerationRequest:
    """User-level request before BriefV2."""

    raw_request: str
    mode: str = "complete"
    page_type: str = ""
    target_language: str = "FR"
    client_slug: str = ""
    client_url: str = ""
    objective: str = ""
    audience: str = ""
    angle: str = ""
    primary_cta_label: str | None = None
    primary_cta_href: str | None = None
    existing_page_url: str | None = None
    concept_description: str | None = None
    inspiration_urls: list[str] = field(default_factory=list)
    inferred: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WizardQuestion:
    """Question the future webapp should ask before generation."""

    id: str
    field: str
    priority: str
    question: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GSGIntakeResult:
    request: GSGGenerationRequest
    brief: BriefV2 | None
    sources: dict[str, str]
    context_summary: dict[str, Any]
    validation_errors: list[str]
    questions: list[WizardQuestion]

    @property
    def ready_to_generate(self) -> bool:
        return bool(self.brief) and not self.validation_errors and not self.questions

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "brief": self.brief.to_dict() if self.brief else None,
            "sources": self.sources,
            "context_summary": self.context_summary,
            "validation_errors": self.validation_errors,
            "questions": [q.to_dict() for q in self.questions],
            "ready_to_generate": self.ready_to_generate,
        }


def _compact_text(value: Any, max_chars: int = 600) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:max_chars]


def _safe_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s,;)'\"\]]+", text or "")


def _slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    return host.split(".")[0].replace("-", "_")


def _clients_index() -> list[dict[str, str]]:
    data = _safe_json(CLIENTS_DB)
    out = []
    for item in data.get("clients") or []:
        identity = item.get("identity") or {}
        slug = item.get("id") or ""
        url = identity.get("url") or ""
        names = {
            slug,
            str(slug).replace("_", " "),
            identity.get("name") or "",
            identity.get("enterprise") or "",
        }
        out.append({
            "slug": slug,
            "url": url,
            "names": " ".join(n.lower() for n in names if n),
        })
    return out


def _resolve_client(text: str, explicit_url: str | None = None) -> tuple[str, str, str]:
    urls = _extract_urls(explicit_url or text)
    if urls:
        url = urls[0]
        return _slug_from_url(url), url, "url"

    haystack = f" {text.lower()} "
    candidates = []
    for item in _clients_index():
        names = [n for n in item["names"].split(" ") if len(n) >= 3]
        phrase_names = [n for n in item["names"].split("  ") if len(n) >= 3]
        matched = False
        for name in set(names + phrase_names):
            if f" {name} " in haystack or name in haystack:
                matched = True
                break
        if matched:
            candidates.append(item)
    if candidates:
        candidates.sort(key=lambda item: len(item["slug"]))
        return candidates[0]["slug"], candidates[0]["url"], "client_name"
    return "", "", "missing"


def _infer_from_aliases(text: str, aliases: dict[str, tuple[str, ...]], default: str = "") -> tuple[str, str]:
    lower = text.lower()
    for value, needles in aliases.items():
        for needle in needles:
            if needle.lower() in lower:
                return value, needle
    return default, "default" if default else "missing"


def _infer_language(text: str, default: str = "FR") -> tuple[str, str]:
    lower = text.lower()
    for lang, aliases in LANG_ALIASES.items():
        if re.search(rf"\b{lang.lower()}\b", lower):
            return lang, lang
        for alias in aliases:
            if alias in lower:
                return lang, alias
    return default, "default"


FIELD_MARKERS = (
    "audience",
    "persona",
    "cible",
    "target",
    "objectif",
    "objective",
    "but",
    "angle",
    "hook",
    "concept",
)


def _extract_after_markers(text: str, markers: tuple[str, ...], max_chars: int) -> str:
    for marker in markers:
        next_marker = "|".join(re.escape(value) for value in FIELD_MARKERS if value != marker)
        match = re.search(
            rf"{re.escape(marker)}\s*[:=]\s*(.+?)(?=\s+(?:{next_marker})\s*[:=]|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            return _compact_text(match.group(1), max_chars)
    return ""


def _infer_objective(text: str, page_type: str) -> tuple[str, str]:
    explicit = _extract_after_markers(text, ("objectif", "objective", "but"), 240)
    if explicit:
        return explicit, "explicit_marker"
    lower = text.lower()
    if any(k in lower for k in ("trial", "signup", "inscription", "essai")):
        return "Convertir en signup / inscription trial via une landing page cadrée.", "intent_keyword"
    if any(k in lower for k in ("lead", "rdv", "rendez-vous", "demo", "démo")):
        return "Capturer un lead qualifié et l'amener vers une demande de démo ou rendez-vous.", "intent_keyword"
    if page_type == "pricing":
        return "Clarifier la décision pricing et pousser vers l'action principale sans confusion.", "page_type_default"
    return "", "missing"


def _infer_audience(text: str) -> tuple[str, str]:
    explicit = _extract_after_markers(text, ("audience", "persona", "cible", "target"), 1000)
    if explicit:
        return explicit, "explicit_marker"
    # Keep this conservative. We do not invent a persona from a brand name.
    role_match = re.search(
        r"((?:head|vp|lead|directeur|directrice|responsable|fondateur|founder|pm|product|growth|marketing|engineering)[^.]{60,700})",
        text,
        re.IGNORECASE,
    )
    if role_match:
        return _compact_text(role_match.group(1), 1000), "role_phrase"
    return "", "missing"


def _infer_angle(text: str, page_type: str, client_slug: str) -> tuple[str, str]:
    explicit = _extract_after_markers(text, ("angle", "hook", "concept"), 500)
    if explicit:
        return explicit, "explicit_marker"
    lower = text.lower()
    if page_type == "lp_listicle":
        count = re.search(r"\b(5|6|7|8|9|10|11|12)\s+(?:raisons?|reasons?)\b", lower)
        n = count.group(1) if count else "10"
        return (
            f"{n} raisons concrètes de comprendre pourquoi {client_slug or 'la marque'} mérite l'attention maintenant, avec un angle éditorial utile et sans preuve inventée.",
            "page_type_default",
        )
    return "", "missing"


def _infer_cta(text: str) -> tuple[str | None, str | None, str]:
    lower = text.lower()
    if "10 jours" in lower or "10j" in lower or "10-day" in lower:
        return "Tester gratuitement 10 jours", None, "trial_keyword"
    if "demo" in lower or "démo" in lower:
        return "Demander une démo", None, "demo_keyword"
    if "signup" in lower or "inscription" in lower or "trial" in lower:
        return "Tester gratuitement", None, "signup_keyword"
    return None, None, "missing"


def parse_generation_request(
    raw_request: str,
    *,
    client_url: str | None = None,
    page_type: str | None = None,
    mode: str | None = None,
    target_language: str | None = None,
    objective: str | None = None,
    audience: str | None = None,
    angle: str | None = None,
) -> GSGGenerationRequest:
    """Parse a rough user request into deterministic request fields."""
    text = raw_request or ""
    slug, resolved_url, client_source = _resolve_client(text, client_url)
    inferred: dict[str, str] = {"client": client_source}

    inferred_page_type, page_source = _infer_from_aliases(text, PAGE_TYPE_ALIASES, default="lp_listicle")
    inferred_mode, mode_source = _infer_from_aliases(text, MODE_ALIASES, default="complete")
    inferred_lang, lang_source = _infer_language(text, default="FR")
    objective_value, objective_source = _infer_objective(text, page_type or inferred_page_type)
    audience_value, audience_source = _infer_audience(text)
    angle_value, angle_source = _infer_angle(text, page_type or inferred_page_type, slug)
    cta_label, cta_href, cta_source = _infer_cta(text)

    inferred.update({
        "page_type": "explicit_arg" if page_type else page_source,
        "mode": "explicit_arg" if mode else mode_source,
        "target_language": "explicit_arg" if target_language else lang_source,
        "objective": "explicit_arg" if objective else objective_source,
        "audience": "explicit_arg" if audience else audience_source,
        "angle": "explicit_arg" if angle else angle_source,
        "primary_cta_label": cta_source,
    })

    urls = _extract_urls(text)
    inspiration_urls = urls[1:] if resolved_url and urls else []

    return GSGGenerationRequest(
        raw_request=raw_request,
        mode=mode or inferred_mode,
        page_type=page_type or inferred_page_type,
        target_language=target_language or inferred_lang,
        client_slug=slug,
        client_url=client_url or resolved_url,
        objective=objective or objective_value,
        audience=audience or audience_value,
        angle=angle or angle_value,
        primary_cta_label=cta_label,
        primary_cta_href=cta_href,
        inspiration_urls=inspiration_urls,
        inferred=inferred,
    )


def _question(field: str, priority: str, question: str, reason: str) -> WizardQuestion:
    return WizardQuestion(id=f"ask_{field}", field=field, priority=priority, question=question, reason=reason)


def _questions_for_request(request: GSGGenerationRequest, brief: BriefV2 | None, validation_errors: list[str]) -> list[WizardQuestion]:
    questions: list[WizardQuestion] = []
    if not request.client_url:
        questions.append(_question(
            "client_url", "P0",
            "Quelle est l'URL du client ou de la marque à respecter ?",
            "Modes complete/replace/extend/elevate ont besoin du contexte client.",
        ))
    if not request.page_type:
        questions.append(_question(
            "page_type", "P0",
            "Quel type de page veux-tu générer : lp_listicle, advertorial, lp_sales, lp_leadgen, home, pdp, pricing ?",
            "Le page type pilote doctrine, planner, modules visuels et copy slots.",
        ))
    if request.mode == "replace" and not request.existing_page_url:
        questions.append(_question(
            "existing_page_url", "P0",
            "Quelle URL exacte faut-il refondre ?",
            "Mode 2 replace dépend explicitement de l'audit/recos de la page existante.",
        ))
    if request.mode == "extend" and not request.concept_description:
        questions.append(_question(
            "concept_description", "P0",
            "Quel est le concept nouveau à créer pour cette marque ?",
            "Mode 3 extend doit cadrer le concept avant le planner.",
        ))
    if request.mode == "elevate" and not request.inspiration_urls:
        questions.append(_question(
            "inspiration_urls", "P0",
            "Quelles URLs d'inspiration veux-tu utiliser pour challenger la DA actuelle ?",
            "Mode 4 elevate exige au moins une inspiration explicite.",
        ))

    errors = " | ".join(validation_errors)
    if "audience too short" in errors:
        questions.append(_question(
            "audience", "P0",
            "Décris l'audience : rôle, taille/contexte, 3 peurs, 3 désirs, niveau de conscience Schwartz.",
            "Le GSG ne doit pas inventer le persona. C'est le principal input humain.",
        ))
    if "objective too short" in errors:
        questions.append(_question(
            "objective", "P0",
            "Quel est l'objectif business concret de cette page ?",
            "L'objectif pilote CTA, proof policy et structure de persuasion.",
        ))
    if "angle too short" in errors:
        questions.append(_question(
            "angle", "P1",
            "Quel angle ou hook doit rendre cette page mémorable ?",
            "L'angle évite la page générique même si la doctrine est bonne.",
        ))
    return questions


def build_intake_from_user_request(
    raw_request: str,
    *,
    client_url: str | None = None,
    page_type: str | None = None,
    mode: str | None = None,
    target_language: str | None = None,
    objective: str | None = None,
    audience: str | None = None,
    angle: str | None = None,
) -> GSGIntakeResult:
    """Full deterministic intake: raw request -> request -> BriefV2 draft."""
    request = parse_generation_request(
        raw_request,
        client_url=client_url,
        page_type=page_type,
        mode=mode,
        target_language=target_language,
        objective=objective,
        audience=audience,
        angle=angle,
    )
    sources: dict[str, str] = {}
    context_summary: dict[str, Any] = {}
    brief: BriefV2 | None = None
    validation_errors: list[str] = []

    if request.client_url:
        brief, sources, ctx = prefill_brief_v2_from_client(
            client_url=request.client_url,
            page_type=request.page_type,
            target_language=request.target_language,
            mode=request.mode,
            objective_override=request.objective or None,
            audience_override=request.audience or None,
            angle_override=request.angle or None,
        )
        brief.existing_page_url = request.existing_page_url
        brief.concept_description = request.concept_description
        brief.inspiration_urls = request.inspiration_urls or brief.inspiration_urls
        validation_errors = brief.validate()
        context_summary = {
            "client": ctx.client,
            "page_type": ctx.page_type,
            "completeness_pct": ctx.completeness_pct,
            "available_count": len(ctx.available_artefacts),
            "missing_count": len(ctx.missing_artefacts),
            "has_brand_dna": ctx.has_brand_dna,
            "has_visual_inputs": ctx.has_visual_inputs,
            "has_audit_complete": ctx.has_audit_complete,
        }
    else:
        validation_errors = ["client_url required (sauf mode='genesis')"]

    questions = _questions_for_request(request, brief, validation_errors)
    return GSGIntakeResult(
        request=request,
        brief=brief,
        sources={**sources, **{f"inferred.{k}": v for k, v in request.inferred.items()}},
        context_summary=context_summary,
        validation_errors=validation_errors,
        questions=questions,
    )


def format_intake_for_review(result: GSGIntakeResult) -> str:
    """Markdown review block for CLI/webapp preview."""
    request = result.request
    lines = [
        "# GSG Intake Review",
        "",
        "## Demande",
        f"> {request.raw_request}",
        "",
        "## Generation Request",
        f"- mode: `{request.mode}` ({request.inferred.get('mode')})",
        f"- client: `{request.client_slug or '(missing)'}`",
        f"- client_url: `{request.client_url or '(missing)'}` ({request.inferred.get('client')})",
        f"- page_type: `{request.page_type or '(missing)'}` ({request.inferred.get('page_type')})",
        f"- target_language: `{request.target_language}` ({request.inferred.get('target_language')})",
        f"- primary_cta_label: `{request.primary_cta_label or '(default later)'}` ({request.inferred.get('primary_cta_label')})",
        "",
        "## Context Pack Preview",
        json.dumps(result.context_summary, ensure_ascii=False, indent=2),
    ]
    if result.brief:
        lines.extend([
            "",
            "## BriefV2 Draft",
            f"- objective: {result.brief.objective}",
            f"- audience chars: {len(result.brief.audience)}",
            f"- angle: {result.brief.angle}",
            f"- traffic_source: {result.brief.traffic_source}",
            f"- visitor_mode: {result.brief.visitor_mode}",
            f"- sourced_numbers: {len(result.brief.sourced_numbers)}",
            f"- forbidden_visual_patterns: {len(result.brief.forbidden_visual_patterns)}",
        ])
    if result.validation_errors:
        lines.extend(["", f"## Validation Errors ({len(result.validation_errors)})"])
        lines.extend(f"- {err}" for err in result.validation_errors)
    if result.questions:
        lines.extend(["", f"## Wizard Questions ({len(result.questions)})"])
        for q in result.questions:
            lines.append(f"- [{q.priority}] `{q.field}` — {q.question}")
            lines.append(f"  Reason: {q.reason}")
    else:
        lines.append("\n## Ready\nBriefV2 validé : prêt pour génération canonique.")
    return "\n".join(lines)


def archive_intake_draft(result: GSGIntakeResult, *, label: str | None = None) -> pathlib.Path:
    """Save raw request + draft brief + questions, valid or not."""
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    slug = result.request.client_slug or "unknown"
    page_type = result.request.page_type or "unknown_page"
    parts = [ts, slug, page_type]
    if label:
        parts.append(label)
    path = DRAFT_DIR / ("_".join(parts) + ".json")
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return path
