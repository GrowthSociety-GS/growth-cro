"""Pydantic models for the `runs` pipeline-trigger queue (Sprint 2 / Task 002).

Per CODE_DOCTRINE §TYPING : exposed at the frontier between :
  - Next.js webapp (API route handlers POSTing new runs)
  - Python worker daemon (claims pending rows + executes CLI dispatch)
  - Supabase REST PostgREST (persistence)

Mono-concern : I/O serialization. No I/O, no API calls — pure shape contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RunType = Literal[
    "audit", "experiment",
    "capture", "score", "recos", "gsg", "multi_judge", "reality", "geo",
]

RunStatus = Literal["pending", "running", "completed", "failed"]


class RunCreate(BaseModel):
    """Payload to insert a new pending run from the webapp."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: RunType
    client_id: str | None = None
    org_id: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class RunRow(BaseModel):
    """A row from the `runs` table as read by the worker daemon."""

    model_config = ConfigDict(extra="ignore", frozen=False)

    id: str
    org_id: str | None = None
    client_id: str | None = None
    type: RunType
    status: RunStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output_path: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    progress_pct: float | None = None
    created_at: datetime | None = None


class RunUpdate(BaseModel):
    """Partial update sent by the worker to claim / progress / complete / fail."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: RunStatus | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output_path: str | None = None
    error_message: str | None = None
    progress_pct: float | None = None
    metadata_json: dict[str, Any] | None = None
