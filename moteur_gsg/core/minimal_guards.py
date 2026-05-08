"""Deterministic guards for the minimal GSG path.

V26.AH Day 5 goal:
  - keep generation to 1 LLM call by default;
  - do not run an LLM polish pass over full HTML;
  - make CTA language, fonts, and proof discipline deterministic.
"""
from __future__ import annotations

import json
import pathlib
import re
from html import unescape
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
CAPTURES = ROOT / "data" / "captures"

AI_SLOP_FONT_BLACKLIST = {
    "Inter", "Roboto", "Arial", "Open Sans", "Lato", "Montserrat",
    "Poppins", "Nunito", "Helvetica",
}

FR_CTA_REPLACEMENTS = {
    "Start 10-day trial": "Tester gratuitement 10 jours",
    "Start 10 day trial": "Tester gratuitement 10 jours",
    "Start 10-day free trial": "Tester gratuitement 10 jours",
    "Start free trial": "Tester gratuitement",
    "Start for free": "Tester gratuitement",
    "Try for free": "Tester gratuitement",
    "Get started for free": "Démarrer gratuitement",
    "Get started": "Démarrer",
    "Start now": "Démarrer maintenant",
}

_NUM_RE = re.compile(
    r"(?<![\w])[-+]?\d{1,3}(?:[ \u00a0.,]\d{3})+(?:[,.]\d+)?\+?"
    r"|(?<![\w])[-+]?\d+(?:[,.]\d+)?\+?"
)

_UNIT_RE = re.compile(
    r"(?:%|€|k€|m€|x|×|jours?|days?|mois|months?|semaines?|weeks?|ans?|years?|"
    r"minutes?|mins?|secondes?|seconds?|sec|s|heures?|hours?|langues?|languages?|"
    r"sites?|clients?|brands?|personnes?|p|projets?|pages?|mots?|words?|sprints?|clics?|clicks?|"
    r"blocages?|bloquants?|pi[eè]ges?|"
    r"employ[eé]s?|employees?)",
    re.IGNORECASE,
)

_STRUCTURAL_RE = re.compile(
    r"\b(?:[1-9]|10|11|12)\s+(?:erreurs?|raisons?|etapes?|étapes?|sections?|points?|leviers?|questions?)\b",
    re.IGNORECASE,
)
_STRUCTURAL_NUMBER_RE = re.compile(
    r"\b(?:erreurs?|raisons?|etapes?|étapes?|sections?|points?|leviers?|questions?)\s+(?:[1-9]|10|11|12)\b",
    re.IGNORECASE,
)


def _safe_json(path: pathlib.Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _first_font(family: str | None) -> str | None:
    if not family:
        return None
    return family.split(",")[0].strip().strip("'\"")


def _font_stack(entry: Any) -> str | None:
    if isinstance(entry, dict):
        family = entry.get("family")
        if isinstance(family, str) and family.strip():
            return family.strip()
    return None


def choose_target_fonts(brand_dna: dict) -> dict[str, str]:
    """Pick deterministic font targets from Brand DNA.

    Brand-extracted fonts win, even if the family is common (Inter, Rubik,
    Arial). The AI-slop blacklist is a fallback guard, not a license to break a
    real brand system.
    """
    typo = ((brand_dna.get("visual_tokens") or {}).get("typography") or {})
    display = _font_stack(typo.get("h1")) or _font_stack(typo.get("h2")) or _font_stack(typo.get("h3"))

    body_candidates = []
    for key in ("body", "button", "h2", "h3"):
        body_candidates.append(_font_stack(typo.get(key)))

    body = None
    for candidate in body_candidates:
        if candidate:
            body = candidate
            break

    return {
        "display": display or body or "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "body": body or display or "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }


def _brief_text(brief: dict) -> str:
    parts: list[str] = []
    for key, value in (brief or {}).items():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))
        elif isinstance(value, dict):
            parts.extend(str(v) for v in value.values() if isinstance(v, (str, int, float)))
    return "\n".join(parts)


def _normalize_number(raw: str) -> str:
    value = raw.strip().replace("\u00a0", " ").replace("+", "")
    value = re.sub(r"^[+-]", "", value)
    if re.search(r"\d[ .,]\d{3}(?:[ .,]\d{3})*", value):
        value = re.sub(r"[ .,]", "", value)
    else:
        value = value.replace(",", ".")
    return value


def extract_number_tokens(text: str) -> set[str]:
    return {_normalize_number(m.group(0)) for m in _NUM_RE.finditer(text or "")}


def _number_category(context: str, normalized: str) -> str:
    ctx = context.lower()
    if normalized.isdigit() and 1900 <= int(normalized) <= 2100:
        return "year"
    if "%" in ctx:
        return "percent"
    if "€" in ctx or "k€" in ctx or "m€" in ctx:
        return "currency"
    if re.search(r"\b(?:langues?|languages?|sites?|clients?|brands?|marques?|personnes?|projets?|pages?|mots?|words?|sprints?|clics?|clicks?|blocages?|bloquants?|pi[eè]ges?|employ[eé]s?|employees?)\b", ctx):
        return "count"
    if re.search(r"\b(?:jours?|days?|mois|months?|semaines?|weeks?|ans?|years?|minutes?|mins?|secondes?|seconds?|sec|s|heures?|hours?)\b", ctx):
        return "time"
    if re.search(r"\d+\s*(?:j|d|h|min|mn|s)\b", ctx):
        return "time"
    return "plain"


def _number_category_from_match(normalized: str, after_text: str, context: str) -> str:
    """Classify a visible numeric claim from the nearest unit after the number."""
    if normalized.isdigit() and 1900 <= int(normalized) <= 2100:
        return "year"
    after = after_text.lower()
    if re.match(r"\s*%", after):
        return "percent"
    if re.match(r"\s*(?:€|k€|m€)", after):
        return "currency"
    if re.match(r"\s*(?:j|d|h|min|mn|s|jours?|days?|mois|months?|semaines?|weeks?|ans?|years?|minutes?|mins?|secondes?|seconds?|sec|heures?|hours?)\b", after):
        return "time"
    if re.match(r"\s*(?:langues?|languages?|sites?|clients?|brands?|marques?|personnes?|p|projets?|pages?|mots?|words?|sprints?|clics?|clicks?|blocages?|bloquants?|pi[eè]ges?|employ[eé]s?|employees?)\b", after):
        return "count"
    return _number_category(context, normalized)


def derive_primary_cta_label(brief: dict, target_language: str = "FR") -> str:
    for key in ("primary_cta_label", "primary_cta", "cta_label", "cta"):
        value = (brief or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    text = _brief_text(brief).lower()
    if target_language.upper().startswith("FR"):
        if "10j" in text or "10 jours" in text or "10-day" in text or "trial 10" in text:
            return "Tester gratuitement 10 jours"
        if "trial" in text or "essai" in text or "sans cb" in text or "sans carte" in text:
            return "Tester gratuitement"
        return "Démarrer gratuitement"
    return "Get started"


def derive_primary_cta_href(client: str, brief: dict) -> str:
    for key in ("primary_cta_href", "cta_href", "href"):
        value = (brief or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for page_type in ("home", "pricing"):
        capture = _safe_json(CAPTURES / client / page_type / "capture.json") or {}
        primary = (capture.get("hero") or {}).get("primaryCta") or {}
        href = primary.get("href")
        if isinstance(href, str) and href.strip():
            return href.strip()

    return "#start"


def _collect_capture_fact_numbers(client: str, max_entries: int = 10) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    text_keys = {
        "text", "title", "subtitle", "h1", "label", "snippet",
        "metaDescription", "ogDescription", "description",
    }

    def walk(value: Any, source: str, key: str = "") -> None:
        if len(entries) >= max_entries:
            return
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, source, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, source, key)
        elif key in text_keys and isinstance(value, str) and _NUM_RE.search(value):
            clean = " ".join(value.split())
            if len(clean) <= 180:
                entries.append({"number": ", ".join(sorted(extract_number_tokens(clean))), "source": source, "context": clean})

    for page_type in ("home", "pricing"):
        capture = _safe_json(CAPTURES / client / page_type / "capture.json")
        if capture:
            walk(capture.get("hero") or {}, f"{page_type}/capture.hero")
            if page_type == "home":
                early_headings = [
                    h for h in ((capture.get("structure") or {}).get("headings") or [])
                    if isinstance(h, dict) and int(h.get("order") or 999) <= 15
                ]
                walk(early_headings, f"{page_type}/capture.structure.headings")
            walk((capture.get("meta") or {}).get("metaDescription"), f"{page_type}/capture.meta")
    return entries[:max_entries]


def build_allowed_facts(client: str, brief: dict) -> tuple[list[dict[str, str]], set[str], dict[str, list[str]]]:
    facts: list[dict[str, str]] = []

    for item in (brief or {}).get("sourced_numbers") or []:
        if isinstance(item, dict):
            number = str(item.get("number") or "").strip()
            if number:
                facts.append({
                    "number": number,
                    "source": str(item.get("source") or "brief.sourced_numbers"),
                    "context": str(item.get("context") or ""),
                })
        elif isinstance(item, str) and item.strip():
            facts.append({"number": item.strip(), "source": "brief.sourced_numbers", "context": ""})

    for item in (brief or {}).get("allowed_numbers") or []:
        if isinstance(item, str) and item.strip():
            facts.append({"number": item.strip(), "source": "brief.allowed_numbers", "context": ""})

    brief_txt = _brief_text(brief)
    chunks = re.split(r"(?:\n+|(?<=[.!?])\s+)", brief_txt)
    for chunk in chunks:
        clean = " ".join(chunk.split())
        if clean and _NUM_RE.search(clean):
            facts.append({
                "number": ", ".join(sorted(extract_number_tokens(clean))),
                "source": "brief",
                "context": clean[:180],
            })

    facts.extend(_collect_capture_fact_numbers(client))

    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for fact in facts:
        key = (fact.get("number", ""), fact.get("context", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(fact)

    allowed_tokens: set[str] = set()
    allowed_categories: dict[str, set[str]] = {}
    for fact in deduped:
        fact_text = " ".join([fact.get("number", ""), fact.get("context", "")])
        for match in _NUM_RE.finditer(fact_text):
            token = _normalize_number(match.group(0))
            allowed_tokens.add(token)
            allowed_categories.setdefault(token, set()).add(
                _number_category_from_match(token, fact_text[match.end(): match.end() + 48], fact_text)
            )

    return deduped, allowed_tokens, {k: sorted(v) for k, v in allowed_categories.items()}


def build_minimal_constraints(
    client: str,
    page_type: str,
    brief: dict,
    brand_dna: dict,
    *,
    target_language: str = "FR",
    primary_cta_label: str | None = None,
    primary_cta_href: str | None = None,
) -> dict[str, Any]:
    fonts = choose_target_fonts(brand_dna)
    cta_label = primary_cta_label or derive_primary_cta_label(brief, target_language)
    cta_href = primary_cta_href or derive_primary_cta_href(client, brief)
    facts, allowed_tokens, allowed_categories = build_allowed_facts(client, brief)
    allowed_category_sets = {k: set(v) for k, v in (allowed_categories or {}).items()}
    if _NUM_RE.search(cta_label):
        facts.append({"number": ", ".join(sorted(extract_number_tokens(cta_label))), "source": "primary_cta_label", "context": cta_label})
        for match in _NUM_RE.finditer(cta_label):
            token = _normalize_number(match.group(0))
            allowed_tokens.add(token)
            allowed_category_sets.setdefault(token, set()).add(
                _number_category_from_match(token, cta_label[match.end(): match.end() + 48], cta_label)
            )
    return {
        "client": client,
        "page_type": page_type,
        "target_language": target_language,
        "primary_cta_label": cta_label,
        "primary_cta_href": cta_href,
        "target_display_font": fonts["display"],
        "target_body_font": fonts["body"],
        "allowed_facts": facts,
        "allowed_number_tokens": sorted(allowed_tokens),
        "allowed_number_categories": {k: sorted(v) for k, v in allowed_category_sets.items()},
    }


def format_minimal_constraints_block(constraints: dict[str, Any], max_facts: int = 8) -> str:
    facts = constraints.get("allowed_facts") or []
    target_display = constraints.get("target_display_font")
    target_body = constraints.get("target_body_font")
    allowed_font_names = _allowed_font_names(target_display, target_body)
    blocked_fonts = [
        font for font in sorted(AI_SLOP_FONT_BLACKLIST)
        if font.lower() not in allowed_font_names
    ]
    font_guard = (
        "- Fonts generiques interdites dans le CSS si elles ne viennent pas de la Brand DNA : "
        + ", ".join(blocked_fonts)
        + ".\n"
        if blocked_fonts
        else "- Fonts Brand DNA autorisees ; ne pas ajouter de font generique externe.\n"
    )

    def fact_priority(fact: dict[str, str]) -> tuple[int, str]:
        source = fact.get("source") or ""
        if "capture" in source:
            return (0, source)
        if source == "primary_cta_label":
            return (1, source)
        if source.startswith("v143") or source.startswith("recos"):
            return (2, source)
        if source == "brief.sourced_numbers":
            return (3, source)
        if source == "brief":
            return (4, source)
        return (5, source)

    facts = sorted(facts, key=fact_priority)
    fact_lines = []
    for fact in facts[:max_facts]:
        context = fact.get("context") or fact.get("number")
        fact_lines.append(f"- {context} (source: {fact.get('source', 'unknown')})")
    if not fact_lines:
        fact_lines.append("- Aucun chiffre source disponible.")

    return (
        "## CONTRAINTES DETERMINISTES DAY 5\n"
        f"- Langue cible obligatoire : {constraints.get('target_language', 'FR')}\n"
        f"- CTA primaire exact : \"{constraints.get('primary_cta_label')}\"\n"
        f"- URL CTA primaire : {constraints.get('primary_cta_href')}\n"
        f"- Font display : {target_display}\n"
        f"- Font body : {target_body}\n"
        + font_guard
        + "- N'integre jamais de font en base64 : pas de @font-face, pas de data:font, pas de blob asset. CSS font-family seulement.\n"
        "- Chiffres autorises UNIQUEMENT s'ils apparaissent ci-dessous ou dans le brief. Tout autre %, euro, mois, projet, client, cas nomme ou resultat chiffre est interdit.\n"
        "- Cette regle gagne sur la doctrine per_04 : si tu manques de preuves, tu omets. Tu n'inventes jamais une moyenne, un cout, un delai, un pourcentage, un trafic perdu ou un cas client.\n"
        f"- Tokens numeriques autorises : {', '.join(constraints.get('allowed_number_tokens') or []) or '(aucun)'}\n"
        + "\n".join(fact_lines)
        + "\n- Si une preuve manque, ecris qualitativement. Ne cree pas de cas client, pourcentage, cout, duree ou benchmark invente.\n"
    )


def _visible_text(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html or "", flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*$", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def find_unsourced_numeric_claims(
    html: str,
    allowed_tokens: set[str] | list[str],
    allowed_categories: dict[str, list[str]] | None = None,
) -> list[dict[str, str]]:
    allowed = set(allowed_tokens or [])
    categories = allowed_categories or {}
    text = _visible_text(html)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in _NUM_RE.finditer(text):
        raw = match.group(0)
        norm = _normalize_number(raw)
        start, end = match.span()
        if start >= 2 and text[start - 1] in {",", "."} and text[start - 2].isdigit():
            continue
        context = text[max(0, start - 70): min(len(text), end + 90)].strip()
        category_context = text[max(0, start - 48): min(len(text), end + 48)].strip()
        local_context = text[start: min(len(text), end + 48)].strip()
        after_text = text[end: min(len(text), end + 48)]

        if re.fullmatch(r"0[1-9]|1[0-2]", raw.strip()):
            continue
        if _STRUCTURAL_RE.search(context) or _STRUCTURAL_NUMBER_RE.search(context):
            continue
        if re.match(r"[-+]?\d+(?:[,.]\d+)?\+?\s*(?:e|eme|ème|ᵉ)\b", local_context, re.IGNORECASE):
            continue
        if norm.isdigit() and int(norm) <= 12 and not _UNIT_RE.search(local_context):
            continue
        category = _number_category_from_match(norm, after_text, category_context)
        if category == "plain" and norm.isdigit() and int(norm) <= 12:
            continue
        if norm in allowed and category in set(categories.get(norm, [])):
            continue
        if not _UNIT_RE.search(local_context) and not (norm.isdigit() and len(norm) >= 4):
            continue

        key = f"{norm}:{context[:120]}"
        if key in seen:
            continue
        seen.add(key)
        out.append({"number": raw, "normalized": norm, "category": category, "context": context})
        if len(out) >= 20:
            break
    return out


def repair_cta_language(html: str, target_language: str, primary_cta_label: str) -> tuple[str, list[str]]:
    if not target_language.upper().startswith("FR"):
        return html, []
    out = html
    repairs: list[str] = []
    replacements = dict(FR_CTA_REPLACEMENTS)
    replacements[primary_cta_label] = primary_cta_label
    for source, target in replacements.items():
        if source == target:
            continue
        if source in out:
            out = out.replace(source, primary_cta_label if source in FR_CTA_REPLACEMENTS else target)
            repairs.append(f"cta: {source} -> {primary_cta_label}")
    return out, repairs


def repair_ai_slop_fonts(html: str, target_display_font: str, target_body_font: str) -> tuple[str, list[str]]:
    out = html
    repairs: list[str] = []

    for slop in AI_SLOP_FONT_BLACKLIST:
        slop_url = slop.replace(" ", "+")
        pattern = rf"family={re.escape(slop_url)}(?=[\s\"&:'])"
        if re.search(pattern, out):
            out = re.sub(pattern, f"family={target_body_font.replace(' ', '+')}", out)
            repairs.append(f"google_fonts_url: {slop} -> {target_body_font}")

    for slop in AI_SLOP_FONT_BLACKLIST:
        for display_var in ("--font-display", "--font-heading", "--font-h1", "--font-h2", "--font-h3", "--font-title"):
            pat = rf"({re.escape(display_var)}\s*:\s*['\"]?)({re.escape(slop)})(['\"]?)"
            if re.search(pat, out):
                out = re.sub(pat, rf"\1{target_display_font}\3", out)
                repairs.append(f"css_var: {display_var} {slop} -> {target_display_font}")
        for body_var in ("--font-body", "--font-text", "--font-p", "--font-base", "--font-accent"):
            pat = rf"({re.escape(body_var)}\s*:\s*['\"]?)({re.escape(slop)})(['\"]?)"
            if re.search(pat, out):
                out = re.sub(pat, rf"\1{target_body_font}\3", out)
                repairs.append(f"css_var: {body_var} {slop} -> {target_body_font}")

        pat = rf"(font-family\s*:\s*['\"]?)({re.escape(slop)})(['\"]?)"
        if re.search(pat, out):
            out = re.sub(pat, rf"\1{target_body_font}\3", out)
            repairs.append(f"font-family: {slop} -> {target_body_font}")

    return out, repairs


def repair_common_unsourced_patterns(html: str) -> tuple[str, list[str]]:
    """Deterministic copy-safe rewrites for common unsourced numeric slips."""
    out = html
    repairs: list[str] = []

    patterns = [
        (r"\b[Ii]nstallation en \d+\s*(?:minutes?|mins?|min)\b", "Installation en quelques minutes", "installation_minutes"),
        (r"\ben \d+\s*(?:clics?|clicks?)\b", "en quelques clics", "click_count"),
        (r"\ben\s+1\s+journ[eé]e\b", "rapidement", "one_day_deployment"),
        (r"\bd[eè]s\s+le\s+jour\s+1\b", "dès les premiers suivis", "day_one"),
        (r"\bjour\s+1\b", "lancement", "day_one_short"),
        (r"\b30\s+minutes?\b", "un temps court", "thirty_minutes"),
        (r"\b2\s+jours?\b", "quelques jours", "two_days"),
        (r"\b2\s+ou\s+3\s+langues?\b", "quelques langues", "two_or_three_languages"),
        (r"\bapr[eè]s\s+3\s+mois\b", "après une période d'observation", "after_three_months"),
        (r"\bpendant\s+3\s+ans\b", "durablement", "for_three_years"),
        (r"\bmoins\s+de\s+24\s+heures?\b", "très vite", "twenty_four_hours"),
        (r"\b24\s+heures?\b", "très vite", "twenty_four_hours_short"),
        (r"\b2\s+mois\b", "des semaines", "two_months"),
        (r"\b3\s+[àa]\s+6\s+mois\b", "plusieurs mois", "three_to_six_months"),
        (r"\b6\s+mois\b", "plusieurs mois", "six_months"),
        (r"\b48\s+heures?\b", "un délai d'attente", "forty_eight_hours"),
        (r"\b\d+\s+versions?\s+linguistiques?\b", "plusieurs versions linguistiques", "language_versions_count"),
        (r"©\s*\d{4}\s+", "© ", "copyright_year"),
    ]
    for pattern, replacement, label in patterns:
        new_out, n = re.subn(pattern, replacement, out)
        if n:
            out = new_out
            repairs.append(f"{label}: {n} rewrite(s)")

    return out, repairs


def repair_unsourced_numeric_claims(html: str, constraints: dict[str, Any]) -> tuple[str, list[str]]:
    """Remove numeric claims that still fail the deterministic proof audit."""
    issues = find_unsourced_numeric_claims(
        html,
        set(constraints.get("allowed_number_tokens") or []),
        constraints.get("allowed_number_categories") or {},
    )
    out = html
    repairs: list[str] = []
    for item in issues:
        number = re.escape(item["number"])
        if item.get("category") == "percent":
            replacements = [
                (rf"\b{number}\s*%\s+de\b", "une grande partie de", "unsourced_percent_de"),
                (rf"\b{number}\s*%\b", "une part importante", "unsourced_percent"),
            ]
        elif item.get("category") == "time":
            replacements = [
                (rf"\b{number}\s*(?:jours?|days?|mois|months?|semaines?|weeks?|ans?|years?|minutes?|mins?|secondes?|seconds?|sec|heures?|hours?)\b", "un délai court", "unsourced_time"),
            ]
        else:
            replacements = []
        for pattern, replacement, label in replacements:
            out, n = re.subn(pattern, replacement, out, count=1, flags=re.IGNORECASE)
            if n:
                repairs.append(f"{label}: {item['number']} -> {replacement}")
                break
    return out, repairs


def _allowed_font_names(*font_stacks: str | None) -> set[str]:
    names: set[str] = set()
    for stack in font_stacks:
        if not stack:
            continue
        for part in str(stack).split(","):
            clean = part.strip().strip("'\"").lower()
            if clean:
                names.add(clean)
    return names


def check_font_violations(html: str, *, allowed_fonts: set[str] | None = None) -> list[str]:
    html_lower = (html or "").lower()
    violations = []
    allowed = allowed_fonts or set()
    for font in sorted(AI_SLOP_FONT_BLACKLIST):
        if font.lower() in allowed:
            continue
        if (
            f"family={font.replace(' ', '+')}".lower() in html_lower
            or f"'{font}'".lower() in html_lower
            or f'"{font}"'.lower() in html_lower
            or f"font-family: {font}".lower() in html_lower
        ):
            violations.append(font)
    return violations


def check_english_cta_violations(html: str, target_language: str) -> list[str]:
    if not target_language.upper().startswith("FR"):
        return []
    found = []
    for phrase in FR_CTA_REPLACEMENTS:
        if phrase in (html or ""):
            found.append(phrase)
    return found


def check_html_integrity(html: str) -> list[str]:
    issues = []
    html_lower = (html or "").lower()
    if not html_lower.lstrip().startswith("<!doctype html>"):
        issues.append("missing_doctype")
    if "<style" in html_lower and "</style>" not in html_lower:
        issues.append("unclosed_style")
    if "</body>" not in html_lower:
        issues.append("missing_body_close")
    if "</html>" not in html_lower:
        issues.append("missing_html_close")
    if "data:font" in html_lower or "@font-face" in html_lower:
        issues.append("embedded_font_asset")
    return issues


def audit_minimal_html(html: str, constraints: dict[str, Any]) -> dict[str, Any]:
    unsourced = find_unsourced_numeric_claims(
        html,
        set(constraints.get("allowed_number_tokens") or []),
        constraints.get("allowed_number_categories") or {},
    )
    integrity_issues = check_html_integrity(html)
    font_violations = check_font_violations(
        html,
        allowed_fonts=_allowed_font_names(
            constraints.get("target_display_font"),
            constraints.get("target_body_font"),
        ),
    )
    english_cta_violations = check_english_cta_violations(html, constraints.get("target_language", "FR"))
    return {
        "html_integrity_issues": integrity_issues,
        "font_violations": font_violations,
        "english_cta_violations": english_cta_violations,
        "unsourced_numeric_claims": unsourced,
        "pass": not integrity_issues
        and not unsourced
        and not font_violations
        and not english_cta_violations,
    }


def apply_minimal_postprocess(html: str, constraints: dict[str, Any], *, verbose: bool = True) -> tuple[str, dict[str, Any]]:
    repairs: list[str] = []
    out, cta_repairs = repair_cta_language(
        html,
        constraints.get("target_language", "FR"),
        constraints.get("primary_cta_label") or "Démarrer gratuitement",
    )
    repairs.extend(cta_repairs)

    out, font_repairs = repair_ai_slop_fonts(
        out,
        constraints.get("target_display_font") or "DM Sans",
        constraints.get("target_body_font") or "DM Sans",
    )
    repairs.extend(font_repairs)

    out, common_repairs = repair_common_unsourced_patterns(out)
    repairs.extend(common_repairs)

    out, numeric_repairs = repair_unsourced_numeric_claims(out, constraints)
    repairs.extend(numeric_repairs)

    audit = audit_minimal_html(out, constraints)
    report = {
        "repairs": repairs,
        "audit": audit,
        "constraints": {
            "target_language": constraints.get("target_language"),
            "primary_cta_label": constraints.get("primary_cta_label"),
            "primary_cta_href": constraints.get("primary_cta_href"),
            "target_display_font": constraints.get("target_display_font"),
            "target_body_font": constraints.get("target_body_font"),
            "allowed_number_tokens": constraints.get("allowed_number_tokens"),
        },
    }

    if verbose:
        print(f"  ✓ minimal postprocess repairs : {len(repairs)}", flush=True)
        if repairs:
            for repair in repairs[:8]:
                print(f"     - {repair}", flush=True)
        print(
            "  ✓ minimal audit : "
            f"fonts={len(audit['font_violations'])}, "
            f"english_cta={len(audit['english_cta_violations'])}, "
            f"html_integrity={len(audit['html_integrity_issues'])}, "
            f"unsourced_numbers={len(audit['unsourced_numeric_claims'])}, "
            f"pass={audit['pass']}",
            flush=True,
        )
        for issue in audit["html_integrity_issues"][:5]:
            print(f"     - html_integrity: {issue}", flush=True)
        for item in audit["unsourced_numeric_claims"][:5]:
            print(f"     - unsourced {item['number']}: {item['context'][:140]}", flush=True)

    return out, report
