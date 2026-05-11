"""Agency audit routes (axis #4 — orchestration).

Two new endpoints exposing the `audit_gads` + `audit_meta` modules:

- `POST /audit/gads` — runs the Google Ads audit pipeline (CSV → bundle + Notion).
- `POST /audit/meta` — runs the Meta Ads audit pipeline (CSV → bundle + Notion).
- `GET  /audit/list` — lists previously persisted audits under `data/audits/`.

The router never reads env (config-only rule), never calls an LLM directly,
and never re-implements the audit logic — it composes the thin-wrapper modules.
"""

from __future__ import annotations

import json
import pathlib
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from growthcro.audit_gads.orchestrator import AuditInputs as GadsInputs, run_audit as run_gads
from growthcro.audit_gads.notion_export import (
    render_bundle_json as gads_render_bundle_json,
    render_notion_markdown as gads_render_markdown,
    render_notion_payload as gads_render_payload,
)
from growthcro.audit_meta.orchestrator import AuditInputs as MetaInputs, run_audit as run_meta
from growthcro.audit_meta.notion_export import (
    render_bundle_json as meta_render_bundle_json,
    render_notion_markdown as meta_render_markdown,
    render_notion_payload as meta_render_payload,
)

router = APIRouter(prefix="/audit", tags=["agency-audits"])

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDITS_DIR = ROOT / "data" / "audits"


# ── request / response models ────────────────────────────────────────────────

class AuditRequest(BaseModel):
    """Common request body for both audit routes."""

    client_slug: str = Field(..., description="Client slug, e.g. 'growth-society-acme'.")
    csv_path: Optional[str] = Field(
        None,
        description=(
            "Absolute or repo-relative path to the CSV export. Either this OR"
            " `csv_text` must be provided."
        ),
    )
    csv_text: Optional[str] = Field(None, description="Raw CSV text (alternative to csv_path).")
    period_label: Optional[str] = Field(None, description="Period label, e.g. '2026-04'.")
    business_category: str = Field(
        "ecommerce", description="Business category hint: ecommerce / leadgen / saas / local."
    )
    notes: str = Field("", description="Free-form notes attached to the audit.")
    persist: bool = Field(
        True, description="If true, writes bundle.json / notion.md / notion_payload.json to disk."
    )


class AuditResponse(BaseModel):
    platform: Literal["google_ads", "meta_ads"]
    skill_name: str
    client_slug: str
    period: str
    row_count: int
    kpis: dict
    bundle: dict
    markdown: str
    notion_payload: dict
    artefacts: dict | None = None


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_csv(req: AuditRequest) -> tuple[Optional[pathlib.Path], Optional[str]]:
    if req.csv_text:
        return None, req.csv_text
    if req.csv_path:
        path = pathlib.Path(req.csv_path)
        if not path.is_absolute():
            path = ROOT / req.csv_path
        if not path.exists():
            raise HTTPException(404, f"CSV not found: {path}")
        return path, None
    raise HTTPException(422, "Either csv_path or csv_text must be provided.")


def _persist(bundle_dict: dict, markdown: str, payload: dict, kind: str, slug: str, period: str) -> dict:
    out_dir = AUDITS_DIR / kind / slug / period
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / "bundle.json"
    md_path = out_dir / "notion.md"
    payload_path = out_dir / "notion_payload.json"
    bundle_path.write_text(json.dumps(bundle_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "bundle": str(bundle_path),
        "markdown": str(md_path),
        "notion_payload": str(payload_path),
    }


# ── routes ───────────────────────────────────────────────────────────────────

@router.post("/gads", response_model=AuditResponse)
async def audit_gads(req: AuditRequest) -> AuditResponse:
    """Run a Google Ads audit (gads-auditor skill, CSV-driven)."""
    csv_path, csv_text = _resolve_csv(req)
    inputs = GadsInputs(
        client_slug=req.client_slug,
        csv_path=csv_path,
        csv_text=csv_text,
        period_label=req.period_label,
        business_category=req.business_category,
        notes=req.notes,
    )
    bundle = run_gads(inputs)
    bundle_dict = bundle.as_dict()
    markdown = gads_render_markdown(bundle_dict)
    payload = gads_render_payload(bundle_dict)
    artefacts = (
        _persist(bundle_dict, markdown, payload, "gads", req.client_slug, inputs.normalised_period())
        if req.persist
        else None
    )
    # ensure the bundle JSON is well-formed (smoke check)
    _ = gads_render_bundle_json(bundle_dict)
    return AuditResponse(
        platform="google_ads",
        skill_name=bundle.skill_name,
        client_slug=bundle_dict["client_slug"],
        period=bundle_dict["period"],
        row_count=bundle_dict["row_count"],
        kpis=bundle_dict["kpis"],
        bundle=bundle_dict,
        markdown=markdown,
        notion_payload=payload,
        artefacts=artefacts,
    )


@router.post("/meta", response_model=AuditResponse)
async def audit_meta(req: AuditRequest) -> AuditResponse:
    """Run a Meta Ads audit (meta-ads-auditor skill, CSV-driven)."""
    csv_path, csv_text = _resolve_csv(req)
    inputs = MetaInputs(
        client_slug=req.client_slug,
        csv_path=csv_path,
        csv_text=csv_text,
        period_label=req.period_label,
        business_category=req.business_category,
        notes=req.notes,
    )
    bundle = run_meta(inputs)
    bundle_dict = bundle.as_dict()
    markdown = meta_render_markdown(bundle_dict)
    payload = meta_render_payload(bundle_dict)
    artefacts = (
        _persist(bundle_dict, markdown, payload, "meta", req.client_slug, inputs.normalised_period())
        if req.persist
        else None
    )
    _ = meta_render_bundle_json(bundle_dict)
    return AuditResponse(
        platform="meta_ads",
        skill_name=bundle.skill_name,
        client_slug=bundle_dict["client_slug"],
        period=bundle_dict["period"],
        row_count=bundle_dict["row_count"],
        kpis=bundle_dict["kpis"],
        bundle=bundle_dict,
        markdown=markdown,
        notion_payload=payload,
        artefacts=artefacts,
    )


@router.get("/list")
async def list_audits(platform: Literal["gads", "meta", "all"] = "all") -> dict:
    """List persisted audits under data/audits/<platform>/<client>/<period>/."""
    platforms = ("gads", "meta") if platform == "all" else (platform,)
    audits: list[dict] = []
    if not AUDITS_DIR.exists():
        return {"audits": [], "total": 0}
    for plat in platforms:
        plat_dir = AUDITS_DIR / plat
        if not plat_dir.exists():
            continue
        for client_dir in sorted(plat_dir.iterdir()):
            if not client_dir.is_dir():
                continue
            for period_dir in sorted(client_dir.iterdir()):
                if not period_dir.is_dir():
                    continue
                bundle = period_dir / "bundle.json"
                if not bundle.exists():
                    continue
                audits.append(
                    {
                        "platform": plat,
                        "client_slug": client_dir.name,
                        "period": period_dir.name,
                        "bundle": str(bundle),
                        "markdown": str(period_dir / "notion.md"),
                        "notion_payload": str(period_dir / "notion_payload.json"),
                    }
                )
    return {"audits": audits, "total": len(audits)}
