"""Opportunity Layer — schema re-export (Issue #47).

The canonical Pydantic models live in ``growthcro.models.opportunity_models``
(TYPING axis per ``docs/doctrine/CODE_DOCTRINE.md``). This module is a thin
re-export so internal consumers can write ``from
growthcro.opportunities.schema import Opportunity`` without coupling to the
models package layout.

Do NOT add new model definitions here — extend ``opportunity_models.py``
instead and re-export below.
"""
from growthcro.models.opportunity_models import (
    Category,
    DoctrineVersion,
    Opportunity,
    OpportunityBatch,
    Owner,
    Severity,
)

__all__ = [
    "Category",
    "DoctrineVersion",
    "Opportunity",
    "OpportunityBatch",
    "Owner",
    "Severity",
]
