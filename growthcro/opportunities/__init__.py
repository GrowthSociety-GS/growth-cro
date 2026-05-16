"""Opportunity Layer — actionable CRO opportunities per page (Issue #47).

Single-concern split:
- schema.py   : thin re-export of the canonical models in
                ``growthcro.models.opportunity_models`` (TYPING axis,
                CODE_DOCTRINE convention).
- persist.py  : read / write ``opportunities.json`` for one
                (client_slug, page_type) pair. Atomic writes via
                ``tmpfile + rename``.

Out of scope here:
- Opportunity *generation* (orchestrator) — Issue #48.
- CLI entrypoint — Issue #49.
- LLM enrichment — Issue P1 (future).

Public re-exports below let callers ``from growthcro.opportunities import
Opportunity, OpportunityBatch, save_opportunities, load_opportunities``
without reaching into the inner modules.
"""
from growthcro.opportunities.persist import (
    load_opportunities,
    opportunities_path,
    save_opportunities,
)
from growthcro.opportunities.schema import Opportunity, OpportunityBatch

__all__ = [
    "Opportunity",
    "OpportunityBatch",
    "load_opportunities",
    "opportunities_path",
    "save_opportunities",
]
