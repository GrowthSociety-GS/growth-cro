"""Pydantic v2 models for the recos pipeline (Issue #32).

Mono-concern: this module declares data shapes only. No business logic, no I/O,
no env reads. The recos pipeline (``growthcro.recos.orchestrator``) consumes
``RecoInput`` and produces ``RecoBatch`` at its public boundary.

V26.A invariant — Evidence Ledger
---------------------------------
Every ``RecoEnriched`` MUST carry a non-empty ``evidence_ids: list[str]`` so
that downstream consumers (dashboards, experiment engine, learning loop) can
trace any reco back to its grounding signals (captures, perception clusters,
scoring criteria, doctrine excerpts). This is enforced by
``Field(..., min_length=1)`` — instantiating ``RecoEnriched`` with an empty
``evidence_ids`` raises ``ValidationError``.

Shape mismatch note
-------------------
The legacy on-disk JSON (``data/captures/<slug>/<page>/recos_v13_final.json``)
contains LLM-side annotation fields prefixed with ``_`` (``_tokens``,
``_retry_count``, ``_grounding_score``, ``_fallback``, ``_dedup_kept``...).
These are not part of the public ``RecoEnriched`` contract — they describe
the *generation process*, not the *recommendation itself*. They live inside
``enrichment_meta`` at the batch level when callers need them. For a strict
round-trip from legacy JSON, use the ``RecoBatch.from_legacy_dict`` helper.

All models use ``ConfigDict(extra='forbid', frozen=True)`` — typing-strict
rollout doctrine.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ─────────────────────────────────────────────────────────────────────────────
# Evidence ledger (V26.A traceability)
# ─────────────────────────────────────────────────────────────────────────────

EvidenceSourceType = Literal["capture", "perception", "scoring", "doctrine"]


class EvidenceLedgerEntry(BaseModel):
    """V26.A traçabilité reco → evidence (capture id, criterion id, perception cluster)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    source_type: EvidenceSourceType
    criterion_id: str | None = None
    cluster_id: str | None = None
    excerpt: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Inputs / Outputs
# ─────────────────────────────────────────────────────────────────────────────

DoctrineVersion = Literal["v3.2.1", "v3.3"]
RecoPriority = Literal["P0", "P1", "P2", "P3"]


class RecoInput(BaseModel):
    """Public input to the recos orchestrator — a single page audit job."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    page_type: str
    data_dir: str = "data/captures"
    top: int = 0  # 0 = all applicable criteria
    doctrine_version: DoctrineVersion = "v3.2.1"
    options: dict[str, Any] = Field(default_factory=dict)


class RecoEnriched(BaseModel):
    """Reco enrichie via Sonnet 4.5 (reco_enricher_v13_api.py).

    V26.A: ``evidence_ids`` non-empty list required. Removing the
    ``min_length=1`` constraint breaks the traceability invariant.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    criterion_id: str
    priority: RecoPriority
    before: str
    after: str | None  # legacy fallback recos sometimes emit None
    why: str
    expected_lift_pct: float = Field(ge=0, le=50)
    effort_hours: int = Field(ge=1, le=80)
    implementation_notes: str
    # V26.A traceability — non-empty per invariant.
    evidence_ids: list[str] = Field(..., min_length=1)
    # Optional structural / scoring fields (present on enriched recos, absent on fallback).
    cluster_id: int | str | None = None
    cluster_role: str | None = None
    ice_score: float | None = None
    reco_type: str | None = None  # "fix" | "skip" | "preserve" | "amplify"
    preserves_usp: bool | None = None
    addresses_killer: str | None = None
    next_test_hypothesis: str | None = None
    roadmap_sequence: int | None = None
    depends_on_recos: list[str] = Field(default_factory=list)
    doctrine_thresholds_cited: list[str] = Field(default_factory=list)
    # Provenance — distinguishes a fallback (LLM failed) from a real enrichment.
    is_fallback: bool = False
    fallback_reason: str | None = None


class RecoBatch(BaseModel):
    """Output public de recos/orchestrator — batch de recos enrichies pour 1 page."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    page_type: str
    recos: list[RecoEnriched]
    evidence_ledger: list[EvidenceLedgerEntry] = Field(default_factory=list)
    # Free-form generation telemetry: model name, tokens, latency, retries...
    enrichment_meta: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_legacy_dict(cls, slug: str, page_type: str, raw: dict[str, Any]) -> "RecoBatch":
        """Build a RecoBatch from the legacy on-disk JSON (``recos_v13_final.json``).

        Strips LLM-annotation fields (``_tokens``, ``_grounding_score``...) into
        ``enrichment_meta`` and elevates ``_fallback`` / ``_fallback_reason`` to
        the typed ``is_fallback`` / ``fallback_reason`` boundary. Missing
        ``evidence_ids`` triggers a V26.A ``ValidationError`` — by design.
        """
        recos_out: list[RecoEnriched] = []
        meta_aggregate: dict[str, Any] = {
            "version": raw.get("version"),
            "model": raw.get("model"),
            "intent": raw.get("intent"),
            "n_prompts": raw.get("n_prompts"),
            "n_ok": raw.get("n_ok"),
            "n_fallback": raw.get("n_fallback"),
            "n_skipped": raw.get("n_skipped"),
            "tokens_total": raw.get("tokens_total"),
            "generated_at": raw.get("generated_at"),
        }
        per_reco_telemetry: list[dict[str, Any]] = []

        for r in raw.get("recos", []):
            tel = {k: v for k, v in r.items() if k.startswith("_")}
            if tel:
                per_reco_telemetry.append({"criterion_id": r.get("criterion_id"), **tel})

            payload = {k: v for k, v in r.items() if not k.startswith("_")}
            payload["is_fallback"] = bool(r.get("_fallback"))
            payload["fallback_reason"] = r.get("_fallback_reason")
            # Skipped recos still carry evidence_ids by construction in the orchestrator;
            # if a legacy file omits them, RecoEnriched will raise — V26.A enforced.
            recos_out.append(RecoEnriched.model_validate(payload))

        if per_reco_telemetry:
            meta_aggregate["per_reco_telemetry"] = per_reco_telemetry

        return cls(
            slug=slug,
            page_type=page_type,
            recos=recos_out,
            evidence_ledger=[],
            enrichment_meta={k: v for k, v in meta_aggregate.items() if v is not None},
        )


__all__ = [
    "EvidenceLedgerEntry",
    "EvidenceSourceType",
    "DoctrineVersion",
    "RecoPriority",
    "RecoInput",
    "RecoEnriched",
    "RecoBatch",
]
