"""Deterministic ``data-evidence-id`` assignment for the GSG renderer (Issue #52).

Mono-concern (axis: ``prompt_assembly`` — content/evidence wiring). No I/O,
no LLM. Pure helpers.

Purpose
-------
``moteur_gsg.core.claims_source_gate`` (Wave 3 wired in mode_1_complete)
refuses ship when a rendered claim lacks a ``data-evidence-id`` attribute
or points to a ledger entry whose ``source_type`` is not in the strict
observable enum. Without this module the renderer emits ZERO
``data-evidence-id`` attributes — 100% of claims fall through to the
free-text regex sweep and the gate blocks every strict-mode run.

This module provides:

* :func:`make_evidence_id` — deterministic SHA-based id reproducible from
  the same ``(client, page, kind, value)`` tuple. Renderer and any
  consumer (mode_1 ledger merger, judge) compute the same id without
  having to read state from disk.
* :func:`build_claim_index` — turns a brief V2 dict into a normalised
  index of every claim that CAN be sourced (sourced_numbers,
  testimonials, logos_clients_tier1) with the deterministic id pre-baked.
* :func:`find_id_for_*` — three normalised lookups (number, testimonial
  quote, logo name) that the renderer calls inline while emitting HTML.
* :func:`wrap_numbers_with_evidence` — string transformer that wraps a
  detected number token in ``<span class="number" data-evidence-id="…">``
  ONLY when the index has a match. Numbers without a match render as
  bare text (gate then catches them as ``text:claim_pattern`` — V26.A
  fail-loud invariant).
* :func:`build_brief_evidence_items` — emits ledger-shaped dicts that a
  caller (mode_1) can merge into ``evidence_ledger.json`` before
  ``validate_claims_sources``. Source type is ``api_external`` when the
  brief entry carries a ``source_url`` (publicly verifiable), else
  ``rule_deterministic`` (brief is part of the deterministic build
  context, validated by the brief owner).
* :func:`augment_evidence_ledger_with_brief` — convenience wrapper that
  merges brief items into a loaded ledger dict (in-place safe — returns
  a new dict).

Wire (NOT in this commit — file ``moteur_gsg/modes/`` is out of scope
for Issue #52)
-----
``mode_1_complete.py`` ``§ 2c.1 Claims Source Gate`` should call
``augment_evidence_ledger_with_brief(evidence_ledger, brief, client,
page_type)`` immediately before ``validate_claims_sources(html, …)`` so
the gate's lookup contains the brief-derived items the renderer wired
into the HTML. Without that 1-line merge, brief-sourced ``data-evidence-id``
values move from ``claims_missing_source`` to ``claims_invalid_source``
(eid present but lookup misses) — still a gate failure, just a
different failure mode. Tracked separately.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)


ClaimKind = Literal["number", "testimonial", "logo"]

_EVIDENCE_ID_PREFIX = "ev_brief_"
_EVIDENCE_ID_HASH_LEN = 12  # 12 hex chars → 48 bits, > 2^40 collision space

# Numbers eligible for wrapping. Matches percentages, currencies, ratings,
# and round-number tokens >10 (skipping likely years 1900-2100). Kept
# narrow to avoid over-wrapping (a wrapped element with no match still
# renders bare, but minimises CSS noise).
_NUMBER_TOKEN_RX = re.compile(
    r"\b\d{1,3}\s*%"
    r"|[\$€£]\s?\d+(?:[\.,]\d+)?\b"
    r"|\b\d+(?:[\.,]\d+)?\s*/\s*5\b"
    r"|\b\d+\s*stars?\b"
    r"|\+\d+\s*%"
    r"|\b\d{2,}(?:[\s,.]?\d{3})*\b",
    re.IGNORECASE,
)
_YEAR_RX = re.compile(r"^(19|20)\d{2}$")

# Source-type mapping for brief-derived evidence items.
_SOURCE_TYPE_WITH_URL = "api_external"
_SOURCE_TYPE_NO_URL = "rule_deterministic"


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic v2 — public claim index shape
# ─────────────────────────────────────────────────────────────────────────────


class ClaimEntry(BaseModel):
    """One brief-derived claim, normalised and pre-id'd.

    ``normalised_value`` is the lower-cased, stripped form used by the
    substring lookup. ``raw_value`` retains the original (for emitting back
    into the ledger item). ``source_url`` decides whether the resulting
    ledger item gets ``source_type=api_external`` or ``rule_deterministic``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=4)
    kind: ClaimKind
    raw_value: str
    normalised_value: str
    source: str = ""
    source_url: str = ""
    context: str = ""


class ClaimIndex(BaseModel):
    """Materialised index of every brief claim, queryable by kind."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    client: str
    page: str
    numbers: list[ClaimEntry] = Field(default_factory=list)
    testimonials: list[ClaimEntry] = Field(default_factory=list)
    logos: list[ClaimEntry] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation + ID helpers
# ─────────────────────────────────────────────────────────────────────────────


def _normalise(value: str) -> str:
    """Lower-case, strip accents, collapse whitespace."""
    if not value:
        return ""
    nkfd = unicodedata.normalize("NFKD", value)
    stripped = "".join(c for c in nkfd if not unicodedata.combining(c))
    return " ".join(stripped.lower().split())


def make_evidence_id(client: str, page: str, kind: ClaimKind, value: str) -> str:
    """Return a deterministic evidence id for ``(client, page, kind, value)``.

    Same inputs → same id (sha256 truncated to 12 hex chars, prefixed
    ``ev_brief_``). Used by both the renderer (when wrapping) and by
    :func:`build_brief_evidence_items` (when emitting matching ledger items)
    so the two sides agree without needing a shared registry.
    """
    payload = f"{client.lower()}|{page.lower()}|{kind}|{_normalise(value)}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_EVIDENCE_ID_HASH_LEN]
    return f"{_EVIDENCE_ID_PREFIX}{digest}"


# ─────────────────────────────────────────────────────────────────────────────
# Index construction (brief V2 → ClaimIndex)
# ─────────────────────────────────────────────────────────────────────────────


def _entry_from_sourced_number(
    sn: dict[str, Any], client: str, page: str,
) -> ClaimEntry | None:
    number = (sn.get("number") or "").strip()
    if not number:
        return None
    return ClaimEntry(
        evidence_id=make_evidence_id(client, page, "number", number),
        kind="number",
        raw_value=number,
        normalised_value=_normalise(number),
        source=(sn.get("source") or "").strip(),
        source_url=(sn.get("source_url") or "").strip(),
        context=(sn.get("context") or "").strip(),
    )


def _entry_from_testimonial(
    t: dict[str, Any], client: str, page: str,
) -> ClaimEntry | None:
    quote = (t.get("quote") or "").strip()
    if not quote:
        return None
    # First 80 normalised chars suffice for substring matching — full
    # quotes can be very long.
    key = _normalise(quote)[:80]
    return ClaimEntry(
        evidence_id=make_evidence_id(client, page, "testimonial", quote),
        kind="testimonial",
        raw_value=quote,
        normalised_value=key,
        source=(t.get("name") or t.get("company") or "").strip(),
        source_url=(t.get("source_url") or "").strip(),
        context=(t.get("position") or t.get("company") or "").strip(),
    )


def _entry_from_logo(
    name: str, client: str, page: str, source_url: str = "",
) -> ClaimEntry | None:
    raw = (name or "").strip()
    if not raw:
        return None
    return ClaimEntry(
        evidence_id=make_evidence_id(client, page, "logo", raw),
        kind="logo",
        raw_value=raw,
        normalised_value=_normalise(raw),
        source="client_logos_tier1",
        source_url=source_url,
        context="",
    )


def build_claim_index(
    brief: dict[str, Any] | None, client: str, page_type: str,
) -> ClaimIndex:
    """Index every brief-sourced claim into a :class:`ClaimIndex`.

    Safe on ``None`` / empty briefs — returns an empty index. The renderer
    queries this index inline; lookup misses produce HTML without a
    ``data-evidence-id`` (the gate then catches them as missing source).
    """
    brief = brief or {}
    numbers: list[ClaimEntry] = []
    for sn in (brief.get("sourced_numbers") or []):
        if not isinstance(sn, dict):
            continue
        entry = _entry_from_sourced_number(sn, client, page_type)
        if entry is not None:
            numbers.append(entry)
    testimonials: list[ClaimEntry] = []
    for t in (brief.get("testimonials") or []):
        if not isinstance(t, dict):
            continue
        entry = _entry_from_testimonial(t, client, page_type)
        if entry is not None:
            testimonials.append(entry)
    logos: list[ClaimEntry] = []
    for name in (brief.get("client_logos_tier1") or []):
        if not isinstance(name, str):
            continue
        entry = _entry_from_logo(name, client, page_type)
        if entry is not None:
            logos.append(entry)
    logger.info(
        "evidence_id_injector.index_built",
        extra={
            "client": client,
            "page": page_type,
            "numbers": len(numbers),
            "testimonials": len(testimonials),
            "logos": len(logos),
        },
    )
    return ClaimIndex(
        client=client, page=page_type,
        numbers=numbers, testimonials=testimonials, logos=logos,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Lookups (called by the renderer inline)
# ─────────────────────────────────────────────────────────────────────────────


def find_id_for_number(text: str, idx: ClaimIndex) -> str | None:
    """Return the evidence id for the first brief number that appears in ``text``.

    Lookup is bidirectional substring on the normalised form — "111 368"
    matches "111 368 marques" and vice-versa. Returns ``None`` on miss.
    """
    if not text:
        return None
    norm = _normalise(text)
    if not norm:
        return None
    for entry in idx.numbers:
        nv = entry.normalised_value
        if not nv:
            continue
        if nv in norm or norm in nv:
            return entry.evidence_id
    return None


def find_id_for_testimonial(quote: str, idx: ClaimIndex) -> str | None:
    """Return the evidence id for the brief testimonial whose quote matches ``quote``.

    Matches on the first 60 normalised chars — exact-match prefix is
    enough since testimonial text comes verbatim from the brief.
    """
    if not quote:
        return None
    key = _normalise(quote)[:60]
    if not key:
        return None
    for entry in idx.testimonials:
        ev = entry.normalised_value[:60]
        if ev and (ev in key or key in ev):
            return entry.evidence_id
    return None


def find_id_for_logo(name: str, idx: ClaimIndex) -> str | None:
    """Return the evidence id for the logo whose name matches ``name`` (case-insensitive)."""
    if not name:
        return None
    norm = _normalise(name)
    if not norm:
        return None
    for entry in idx.logos:
        if entry.normalised_value == norm:
            return entry.evidence_id
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Number-wrapping transformer (plain text → HTML spans)
# ─────────────────────────────────────────────────────────────────────────────


def wrap_numbers_with_evidence(text: str, idx: ClaimIndex) -> str:
    """Wrap matched numeric tokens in ``text`` with claim-class span markup.

    Numbers WITH a matching brief entry render as::

        <span class="number" data-evidence-id="ev_brief_<hash>">100%</span>

    Numbers WITHOUT a match render bare (the gate then catches them as
    free-text claims — fail-loud invariant). The wrapped form satisfies
    ClaimsSourceGate's tag/class detector (``span.number``).

    ``text`` MUST already be HTML-escape-safe at input — this function
    does NOT escape its input. It only inserts span markup around tokens
    that already exist in the text. Used inside the renderer AFTER
    ``html_escaper._e`` runs on a leaf string.
    """
    if not text or not idx.numbers:
        return text

    def _sub(match: re.Match[str]) -> str:
        token = match.group(0).strip()
        if not token:
            return match.group(0)
        # Skip years — they're false positives most of the time.
        digits_only = token.replace(",", "").replace(".", "").replace(" ", "")
        if _YEAR_RX.fullmatch(digits_only):
            return match.group(0)
        eid = find_id_for_number(token, idx)
        if eid is None:
            return match.group(0)
        return f'<span class="number" data-evidence-id="{eid}">{match.group(0)}</span>'

    return _NUMBER_TOKEN_RX.sub(_sub, text)


# ─────────────────────────────────────────────────────────────────────────────
# Brief → ledger items (consumed by mode_1 wire, future)
# ─────────────────────────────────────────────────────────────────────────────


def _ledger_item(entry: ClaimEntry, client: str, page: str) -> dict[str, Any]:
    source_type = _SOURCE_TYPE_WITH_URL if entry.source_url else _SOURCE_TYPE_NO_URL
    text_observed = entry.raw_value if entry.kind != "testimonial" else entry.raw_value[:200]
    return {
        "evidence_id": entry.evidence_id,
        "client": client,
        "page": page,
        "viewport": "n/a",
        "source_type": source_type,
        "source_origin": "brief.sourced_numbers" if entry.kind == "number"
        else ("brief.testimonials" if entry.kind == "testimonial"
              else "brief.client_logos_tier1"),
        "text_observed": text_observed,
        "external_url": entry.source_url,
        "external_publisher": entry.source,
        "context": entry.context,
    }


def build_brief_evidence_items(
    brief: dict[str, Any] | None, client: str, page_type: str,
) -> list[dict[str, Any]]:
    """Emit ledger-shaped items for every brief claim.

    The returned shape matches the on-disk evidence_ledger.json items
    schema (``evidence_id``, ``source_type``, ``text_observed``, …) and
    is safe to append to ``ledger["items"]``. Source type is
    ``api_external`` for any entry with a ``source_url`` (G2, Trustpilot,
    case-study URL, etc.) and ``rule_deterministic`` otherwise (validated
    by brief owner, part of the build context).
    """
    idx = build_claim_index(brief, client, page_type)
    items: list[dict[str, Any]] = []
    for entry in idx.numbers:
        items.append(_ledger_item(entry, client, page_type))
    for entry in idx.testimonials:
        items.append(_ledger_item(entry, client, page_type))
    for entry in idx.logos:
        items.append(_ledger_item(entry, client, page_type))
    return items


def augment_evidence_ledger_with_brief(
    ledger: dict[str, Any] | None,
    brief: dict[str, Any] | None,
    client: str,
    page_type: str,
) -> dict[str, Any]:
    """Return a NEW ledger dict with brief evidence items merged in.

    Pure function — does NOT mutate the input ledger. Duplicate
    ``evidence_id`` values (already present from a prior run) are skipped
    so calling this twice is idempotent. Use this from ``mode_1_complete``
    immediately before ``validate_claims_sources``::

        evidence_ledger = augment_evidence_ledger_with_brief(
            evidence_ledger, brief, client, page_type,
        )
        report = validate_claims_sources(html, evidence_ledger)
    """
    base = dict(ledger) if isinstance(ledger, dict) else {"items": []}
    existing_items = list(base.get("items") or [])
    seen_ids = {
        item.get("evidence_id")
        for item in existing_items
        if isinstance(item, dict) and item.get("evidence_id")
    }
    appended = 0
    for new_item in build_brief_evidence_items(brief, client, page_type):
        if new_item["evidence_id"] in seen_ids:
            continue
        existing_items.append(new_item)
        seen_ids.add(new_item["evidence_id"])
        appended += 1
    base["items"] = existing_items
    base["n_items"] = len(existing_items)
    if appended:
        logger.info(
            "evidence_id_injector.ledger_augmented",
            extra={"client": client, "page": page_type, "appended": appended},
        )
    return base


__all__ = [
    "ClaimEntry",
    "ClaimIndex",
    "ClaimKind",
    "augment_evidence_ledger_with_brief",
    "build_brief_evidence_items",
    "build_claim_index",
    "find_id_for_logo",
    "find_id_for_number",
    "find_id_for_testimonial",
    "make_evidence_id",
    "wrap_numbers_with_evidence",
]
