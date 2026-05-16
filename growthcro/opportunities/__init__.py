"""Opportunity Layer — actionable CRO opportunities per page (Issue #47).

Single-concern split:
- persist.py      : read / write ``opportunities.json`` for one
                    (client_slug, page_type) pair. Atomic writes via
                    ``tmpfile + rename``.
- orchestrator.py : deterministic generation from scoring artefacts (Issue #48).

Canonical Pydantic models live in ``growthcro.models.opportunity_models``
(TYPING axis per ``docs/doctrine/CODE_DOCTRINE.md``). Re-exported below for
ergonomic ``from growthcro.opportunities import Opportunity`` callers.

Out of scope here:
- CLI entrypoint — Issue #49.
- LLM enrichment — Issue P1 (future).
"""
from growthcro.models.opportunity_models import Opportunity, OpportunityBatch
from growthcro.opportunities.orchestrator import generate_opportunities
from growthcro.opportunities.persist import (
    load_opportunities,
    opportunities_path,
    save_opportunities,
)

__all__ = [
    "Opportunity",
    "OpportunityBatch",
    "generate_opportunities",
    "load_opportunities",
    "opportunities_path",
    "save_opportunities",
]
