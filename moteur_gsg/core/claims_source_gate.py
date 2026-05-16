"""ClaimsSourceGate — deterministic HTML validator for claim provenance.

Mono-concern (axis: validation). No I/O, no LLM. Pure parse + lookup.

Purpose
-------
A GSG (Growth Site Generator) HTML page MUST attach a `data-evidence-id`
attribute to every renderable *claim* — numbers, testimonials, logos, proof
strips, statistic figures. Each `data-evidence-id` must resolve to an entry
in the page's `evidence_ledger.json` whose `source_type` is one of the
strict, observable provenances: ``vision``, ``dom``, ``api_external``,
``rule_deterministic`` (plus the hybrid spellings ``vision+dom`` /
``hybrid_vision_dom``). A claim sourced solely from an LLM classifier
(``source_type="llm_classifier"``) is **invalid** — the gate refuses ship.

V26.A invariant — every claim rendered must be traceable to a deterministic
or human-observable signal. This module enforces that invariant before
output reaches the multi-judge stage.

Detection patterns
------------------
The HTML parser looks for the canonical proof markup used by the GSG
templates:

  * ``<span class="number">``, ``<span class="stat">``, ``<strong class="claim">``
  * ``<li class="proof-strip">``, ``<li class="proof">``, ``<li class="trust-indicator">``
  * ``<blockquote class="testimonial">``, ``<div class="testimonial-card">``,
    any element carrying ``data-testimonial``
  * ``<img class="logo-strip">``, ``<img class="trust-logo">``, any element
    carrying ``data-logo``

In addition, a regex sweep flags free-text claims:
  * percentages (``\\d+%``),
  * round numbers >10 (``\\b\\d{2,}\\b`` outside other markup),
  * currency tokens (``\\$\\d+``, ``€\\d+``),
  * ratings (``\\d/5``, ``\\d stars``).

Use
---
    from moteur_gsg.core.claims_source_gate import (
        validate_claims_sources, ClaimsSourceError,
    )

    report = validate_claims_sources(html, evidence_ledger)
    if not report.gate_passed:
        # In --ship-strict mode (Wave 3 wire site)
        report.raise_if_failed()

    # Otherwise tag and continue
    output_meta["claims_source_gate_failed"] = not report.gate_passed
    output_meta["claims_source_report"] = report.model_dump()

Wire
----
**Not wired in this commit.** The mode_1 wire (post-impeccable_qa,
pre-multi-judge) is deferred to Wave 3 to avoid a merge race with
issue #50 (VerdictGate). See `.claude/epics/growthcro-stratosphere-p0/51.md`
section "Wire mode_1" for the integration spec.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public source-type contract (matches docstring of
# skills/site-capture/scripts/evidence_ledger.py extension)
# ─────────────────────────────────────────────────────────────────────────────

EvidenceSourceType = Literal[
    "vision", "dom", "api_external", "rule_deterministic",
    "vision+dom", "hybrid_vision_dom",
]

_STRICT_SOURCE_TYPES: frozenset[str] = frozenset({
    "vision", "dom", "api_external", "rule_deterministic",
    "vision+dom", "hybrid_vision_dom",
})


def is_strict_source_type(source_type: str | None) -> bool:
    """True iff `source_type` belongs to the strict observable provenance set.

    `llm_classifier` and any unknown value are rejected — see V26.A invariant
    documented in the module header. ``None`` is rejected (no source = invalid).
    """
    if not source_type:
        return False
    return source_type in _STRICT_SOURCE_TYPES


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic v2 report shape
# ─────────────────────────────────────────────────────────────────────────────


class Claim(BaseModel):
    """One renderable claim found in the HTML.

    `selector` is a human-readable approximation (tag + class) — not a strict
    CSS selector. `text_excerpt` is the inner-text observed (≤200 chars).
    `evidence_id` is None when the claim has no `data-evidence-id` attribute
    (which is itself a gate failure — `is_valid=False`). `is_valid` is True
    only when the attribute is present *and* points to a ledger entry with a
    strict `source_type`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    selector: str = Field(min_length=1)
    text_excerpt: str
    evidence_id: str | None = None
    is_valid: bool


class ClaimsSourceReport(BaseModel):
    """Result of `validate_claims_sources`. Aggregates per-claim verdicts.

    `gate_passed` is the single shipping signal: True iff every detected claim
    has both a `data-evidence-id` and a strict `source_type` in the ledger.
    Use `raise_if_failed()` to short-circuit in `--ship-strict` mode.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    claims_found: list[Claim] = Field(default_factory=list)
    claims_total: int = Field(ge=0)
    claims_with_valid_source: int = Field(ge=0)
    claims_missing_source: list[Claim] = Field(default_factory=list)
    claims_invalid_source: list[Claim] = Field(default_factory=list)
    gate_passed: bool

    def raise_if_failed(self) -> None:
        """Raise `ClaimsSourceError` if `gate_passed` is False (no-op otherwise)."""
        if not self.gate_passed:
            raise ClaimsSourceError(self)


class ClaimsSourceError(Exception):
    """Raised when one or more claims lack a strict provenance source.

    Carries the full `ClaimsSourceReport` so callers can render a structured
    failure (which claims, which selectors, missing vs invalid).
    """

    def __init__(self, report: ClaimsSourceReport) -> None:
        self.report = report
        n_miss = len(report.claims_missing_source)
        n_inv = len(report.claims_invalid_source)
        super().__init__(
            f"ClaimsSourceGate refused ship: "
            f"{n_miss} claim(s) without data-evidence-id, "
            f"{n_inv} claim(s) with non-strict source_type."
        )


# ─────────────────────────────────────────────────────────────────────────────
# HTML parsing — stdlib HTMLParser (no bs4 dep)
# ─────────────────────────────────────────────────────────────────────────────

# Tag/class combinations that mark a claim element.
_CLAIM_CLASSES: dict[str, frozenset[str]] = {
    "span":       frozenset({"number", "stat"}),
    "strong":     frozenset({"claim"}),
    "li":         frozenset({"proof-strip", "proof", "trust-indicator"}),
    "blockquote": frozenset({"testimonial"}),
    "div":        frozenset({"testimonial-card"}),
    "img":        frozenset({"logo-strip", "trust-logo"}),
}

# Data attributes that mark a claim element regardless of tag/class.
_CLAIM_DATA_ATTRS: frozenset[str] = frozenset({"data-testimonial", "data-logo"})

# Free-text claim patterns (applied to a stripped-text view of the document).
_TEXT_CLAIM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b\d{1,3}%"),                         # 78%, 100%
    re.compile(r"[\$€£]\s?\d+(?:[\.,]\d+)?\b"),        # $99, €1,200
    re.compile(r"\b\d+(?:[\.,]\d+)?\s*/\s*5\b"),       # 4.8/5
    re.compile(r"\b\d+\s*stars?\b", re.IGNORECASE),    # 5 stars
)
# Round numbers >10 are detected separately to avoid false positives on years.
_ROUND_NUMBER_RX = re.compile(r"\b\d{2,}\b")


def _classes(attrs: list[tuple[str, str | None]]) -> frozenset[str]:
    for k, v in attrs:
        if k == "class" and v:
            return frozenset(v.split())
    return frozenset()


def _data_evidence_id(attrs: list[tuple[str, str | None]]) -> str | None:
    for k, v in attrs:
        if k == "data-evidence-id":
            return v or None
    return None


def _has_claim_data_attr(attrs: list[tuple[str, str | None]]) -> bool:
    keys = {k for k, _ in attrs}
    return bool(keys & _CLAIM_DATA_ATTRS)


def _matches_claim_class(tag: str, attrs: list[tuple[str, str | None]]) -> bool:
    wanted = _CLAIM_CLASSES.get(tag.lower())
    if not wanted:
        return False
    return bool(_classes(attrs) & wanted)


class _ClaimExtractor(HTMLParser):
    """One-pass HTML walker. Collects structured claims + the *uncovered*
    plain-text view (text that is NOT already inside a DOM-anchored claim
    element). This split prevents free-text regex from double-counting a
    number that also lives in a `<span class="number">` block.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.claims: list[tuple[str, str | None, list[str]]] = []
        # Stack of currently-open claim contexts: (selector, evidence_id, text_buf)
        self._open_claims: list[tuple[str, str | None, list[str]]] = []
        # Plain text outside any open claim element — fed to free-text scan.
        self._uncovered_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        is_claim = _matches_claim_class(tag, attrs) or _has_claim_data_attr(attrs)
        if is_claim:
            cls_part = ".".join(sorted(_classes(attrs))) if _classes(attrs) else ""
            sel = f"{tag}.{cls_part}" if cls_part else tag
            eid = _data_evidence_id(attrs)
            text_buf: list[str] = []
            self._open_claims.append((sel, eid, text_buf))
        # img tags are void — handle inline (no text inside)
        if tag.lower() == "img" and is_claim:
            sel, eid, text_buf = self._open_claims.pop()
            alt = next((v for k, v in attrs if k == "alt"), None) or ""
            text_buf.append(alt)
            self.claims.append((sel, eid, text_buf))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # `<img ... />` self-closing — same as starttag for our purposes.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self._open_claims) - 1, -1, -1):
            sel, _eid, _buf = self._open_claims[i]
            if sel.split(".", 1)[0] == tag.lower():
                self.claims.append(self._open_claims.pop(i))
                return

    def handle_data(self, data: str) -> None:
        if self._open_claims:
            for _, _, buf in self._open_claims:
                buf.append(data)
        else:
            self._uncovered_text.append(data)

    def get_uncovered_text(self) -> str:
        return " ".join(s for s in self._uncovered_text if s.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Public entrypoint
# ─────────────────────────────────────────────────────────────────────────────


def _to_lookup(evidence_ledger: object) -> dict[str, dict]:
    """Normalise the ledger argument into ``{evidence_id: item_dict}``.

    Accepts:
      * a plain ``dict`` with an ``"items"`` key (the on-disk JSON shape),
      * a plain ``dict`` that is already ``{evidence_id: item}``,
      * an object exposing ``items()`` returning ``list[dict]``
        (the ``EvidenceLedger`` class in
        ``skills/site-capture/scripts/evidence_ledger.py``).

    Unknown shapes return an empty dict — downstream every lookup misses and
    every claim is flagged as ``missing_source`` (safe failure).
    """
    items_iter: list[dict] | None = None
    if isinstance(evidence_ledger, dict):
        if "items" in evidence_ledger and isinstance(evidence_ledger["items"], list):
            items_iter = evidence_ledger["items"]
        else:
            # Assume {evidence_id: item} mapping already
            return {k: v for k, v in evidence_ledger.items() if isinstance(v, dict)}
    elif hasattr(evidence_ledger, "items") and callable(evidence_ledger.items):
        candidate = evidence_ledger.items()
        if isinstance(candidate, list):
            items_iter = candidate
    if items_iter is None:
        return {}
    return {
        item.get("evidence_id"): item
        for item in items_iter
        if isinstance(item, dict) and item.get("evidence_id")
    }


def _extract_text_claims(plain_text: str) -> list[Claim]:
    """Scan free text for numeric/proof claims that have no DOM marker.

    Every match in plain text necessarily lacks a `data-evidence-id` (it's
    flat text), so each is recorded as `is_valid=False` directly.
    """
    found: list[Claim] = []
    seen_excerpts: set[str] = set()

    for pat in _TEXT_CLAIM_PATTERNS:
        for m in pat.finditer(plain_text):
            excerpt = m.group(0).strip()
            if excerpt in seen_excerpts:
                continue
            seen_excerpts.add(excerpt)
            found.append(Claim(
                selector="text:claim_pattern",
                text_excerpt=excerpt[:200],
                evidence_id=None,
                is_valid=False,
            ))

    for m in _ROUND_NUMBER_RX.finditer(plain_text):
        n = int(m.group(0))
        if n <= 10 or 1900 <= n <= 2100:
            continue  # skip ages / years
        excerpt = m.group(0).strip()
        if excerpt in seen_excerpts:
            continue
        seen_excerpts.add(excerpt)
        found.append(Claim(
            selector="text:round_number",
            text_excerpt=excerpt[:200],
            evidence_id=None,
            is_valid=False,
        ))
    return found


def validate_claims_sources(
    html: str,
    evidence_ledger: object,
) -> ClaimsSourceReport:
    """Parse `html`, extract claims, validate each against `evidence_ledger`.

    `evidence_ledger` accepts any of the shapes described in `_to_lookup`.
    The function never raises on bad input — it returns a report with
    `gate_passed=False` and `claims_missing_source` populated. Use
    `report.raise_if_failed()` (or `ClaimsSourceError`) for strict-mode
    enforcement.
    """
    lookup = _to_lookup(evidence_ledger)
    parser = _ClaimExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        logger.warning(
            "claims_source_gate.html_parse_failed",
            extra={"error": str(exc)[:200]},
        )

    claims_found: list[Claim] = []
    claims_missing: list[Claim] = []
    claims_invalid: list[Claim] = []
    n_valid = 0

    # DOM-anchored claims
    for selector, eid, text_buf in parser.claims:
        excerpt = (" ".join(s.strip() for s in text_buf if s.strip()))[:200]
        if eid is None:
            claim = Claim(
                selector=selector,
                text_excerpt=excerpt,
                evidence_id=None,
                is_valid=False,
            )
            claims_found.append(claim)
            claims_missing.append(claim)
            continue
        ledger_item = lookup.get(eid)
        source_type = (ledger_item or {}).get("source_type")
        if ledger_item is None or not is_strict_source_type(source_type):
            if ledger_item is None:
                logger.warning(
                    "claims_source_gate.evidence_id_not_in_ledger",
                    extra={"evidence_id": eid, "selector": selector},
                )
            else:
                # Backward-compat: pre-existing `llm_classifier` entries are
                # logged once at WARN so legacy ledgers don't crash but still
                # block the ship (V26.A invariant).
                logger.warning(
                    "claims_source_gate.invalid_source_type",
                    extra={
                        "evidence_id": eid,
                        "source_type": source_type,
                        "selector": selector,
                    },
                )
            claim = Claim(
                selector=selector,
                text_excerpt=excerpt,
                evidence_id=eid,
                is_valid=False,
            )
            claims_found.append(claim)
            claims_invalid.append(claim)
            continue
        claim = Claim(
            selector=selector,
            text_excerpt=excerpt,
            evidence_id=eid,
            is_valid=True,
        )
        claims_found.append(claim)
        n_valid += 1

    # Free-text claims (numbers, percentages, currencies, ratings) — restricted
    # to text outside any DOM-anchored claim element to avoid double-counting.
    text_claims = _extract_text_claims(parser.get_uncovered_text())
    for tc in text_claims:
        claims_found.append(tc)
        claims_missing.append(tc)

    gate_passed = (len(claims_missing) + len(claims_invalid)) == 0
    report = ClaimsSourceReport(
        claims_found=claims_found,
        claims_total=len(claims_found),
        claims_with_valid_source=n_valid,
        claims_missing_source=claims_missing,
        claims_invalid_source=claims_invalid,
        gate_passed=gate_passed,
    )
    logger.info(
        "claims_source_gate.report",
        extra={
            "claims_total": report.claims_total,
            "claims_valid": report.claims_with_valid_source,
            "claims_missing": len(claims_missing),
            "claims_invalid": len(claims_invalid),
            "gate_passed": gate_passed,
        },
    )
    return report


__all__ = [
    "Claim",
    "ClaimsSourceError",
    "ClaimsSourceReport",
    "EvidenceSourceType",
    "is_strict_source_type",
    "validate_claims_sources",
]
