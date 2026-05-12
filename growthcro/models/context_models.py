"""Pydantic v2 models for the GSG generation context contract.

Public surface consumed by ``moteur_gsg.modes.mode_1_complete`` (and any
future planner / persona-narrator callsite). Built to absorb the
``dict[str, Any] | None`` drift that ``context_pack.py`` previously
exported.

Mono-concern: **I/O serialization / typed contract**. No I/O, no env,
no orchestration logic. See ``docs/doctrine/CODE_DOCTRINE.md`` §axis 8.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ── Sub-models ──────────────────────────────────────────────────────────


class EvidenceFactModel(BaseModel):
    """Single proof fact entered into the inventory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    value: str
    source: str
    context: str = ""


class PageContext(BaseModel):
    """Page-level context: client slug, page_type, target language."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    page_type: str
    target_language: str = "FR"
    audit_dependency_policy: str = "unknown"


class ClientContext(BaseModel):
    """Client-level context summary surfaced to GSG planners.

    Mirrors the ``brand`` summary previously emitted as ``dict[str, Any]``
    by ``_brand_summary`` in ``context_pack.py``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str
    brand_name: str
    home_url: str | None = None
    signature: str | None = None
    preserve_count: int = 0
    amplify_count: int = 0
    fix_count: int = 0
    forbid_count: int = 0
    palette: list[str] = Field(default_factory=list)
    display_font: str | None = None
    body_font: str | None = None


# ── Public input / output ───────────────────────────────────────────────


class ContextPackInput(BaseModel):
    """Input contract for ``build_context_pack``.

    Kept narrow on purpose: orchestration callers pass these primitives
    + a free-form brief (typed at the caller, not here). The brief
    dict is intentionally outside this model — typing brief is a
    separate follow-up sprint.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client: str
    page_type: str
    mode: str = "complete"
    target_language: str = "FR"


class ContextPackOutput(BaseModel):
    """Output public de ``build_context_pack`` / ``build_generation_context_pack``.

    Consumed by ``moteur_gsg.modes.mode_1_complete`` (and any future
    planner / persona-narrator). Round-trip serializable via
    ``model_dump()`` / ``model_validate()``.

    NOTE: The ``artefacts`` / ``business`` / ``audience`` /
    ``scent_contract`` / ``design_sources`` payloads stay
    ``dict[str, Any]`` for now — they fan out to ~8 downstream
    consumers each expecting heterogeneous shapes. Tightening those
    is a follow-up sprint (one model per consumer surface).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    mode: str
    client: str
    page_type: str
    target_language: str
    audit_dependency_policy: str
    artefacts: dict[str, Any] = Field(default_factory=dict)
    brand: dict[str, Any] = Field(default_factory=dict)
    business: dict[str, Any] = Field(default_factory=dict)
    audience: dict[str, Any] = Field(default_factory=dict)
    proof_inventory: list[EvidenceFactModel] = Field(default_factory=list)
    scent_contract: dict[str, Any] = Field(default_factory=dict)
    visual_assets: dict[str, str] = Field(default_factory=dict)
    design_sources: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)

    # ── Backwards-compat helpers (replace dataclass ``asdict``) ─────────

    def to_dict(self) -> dict[str, Any]:
        """Dict form compatible with the legacy ``GenerationContextPack``."""
        return self.model_dump(mode="python")

    def page_context(self) -> PageContext:
        """Project a ``PageContext`` view (for callsites typed against it)."""
        return PageContext(
            slug=self.client,
            page_type=self.page_type,
            target_language=self.target_language,
            audit_dependency_policy=self.audit_dependency_policy,
        )

    def client_context(self) -> ClientContext:
        """Project a ``ClientContext`` view from the brand summary."""
        brand = self.brand or {}
        return ClientContext(
            slug=self.client,
            brand_name=str(brand.get("client_name") or self.client),
            home_url=brand.get("home_url"),
            signature=brand.get("signature"),
            preserve_count=int(brand.get("preserve_count") or 0),
            amplify_count=int(brand.get("amplify_count") or 0),
            fix_count=int(brand.get("fix_count") or 0),
            forbid_count=int(brand.get("forbid_count") or 0),
            palette=list(brand.get("palette") or []),
            display_font=brand.get("display_font"),
            body_font=brand.get("body_font"),
        )


__all__ = [
    "ClientContext",
    "ContextPackInput",
    "ContextPackOutput",
    "EvidenceFactModel",
    "PageContext",
]
