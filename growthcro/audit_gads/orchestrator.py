"""Google Ads audit orchestration (axis #4 — orchestration).

Thin wrapper that:

1. parses a Google Ads Editor CSV export (or accepts pre-parsed rows),
2. shapes the canonical `AuditBundle` payload the `anthropic-skills:gads-auditor`
   skill consumes,
3. computes a deterministic preview using CSV-derived KPIs so the module is
   useful even without an interactive skill invocation,
4. delegates the *qualitative* analysis (recommendations, next steps) to the
   skill by leaving narrative slots clearly labelled `<<SKILL_FILLED>>` — the
   Anthropic skill output is dropped in place by the caller.

This module never reads env (config-only rule), never calls an LLM directly,
and never writes to disk — persistence happens in the CLI (axis #5) so the
orchestrator stays single-concern (axis #4).
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

# ── canonical Notion-template sections (A–H) ────────────────────────────────
SECTIONS = ("A", "B", "C", "D", "E", "F", "G", "H")
SECTION_TITLES = {
    "A": "Overview (compte, période, KPIs globaux)",
    "B": "Campagnes (Search + Shopping + PMax + Demand Gen)",
    "C": "Keywords / Audiences",
    "D": "Creatives (ads + assets)",
    "E": "Conversions (tracking, attribution, valeur)",
    "F": "Recommandations priorisées (quick wins + structural)",
    "G": "Next steps actionables (timeline)",
    "H": "Annexes (CSV exports + screenshots)",
}

# Slot marker the Anthropic skill replaces during interactive invocation.
SKILL_SLOT = "<<SKILL_FILLED>>"


# ── data classes ─────────────────────────────────────────────────────────────

@dataclass
class AuditInputs:
    """Inputs accepted by the audit pipeline.

    Today: CSV path or in-memory CSV text (Google Ads Editor / Reports format).
    V2 (out of scope #22): direct API export via OAuth — see README follow-ups.
    """

    client_slug: str
    csv_path: pathlib.Path | None = None
    csv_text: str | None = None
    period_label: str | None = None
    business_category: str = "ecommerce"
    notes: str = ""

    def normalised_period(self) -> str:
        return self.period_label or "last_30d"


@dataclass
class AuditOutputs:
    """Audit results shaped for Notion + JSON consumers."""

    sections: dict[str, dict] = field(default_factory=dict)
    kpis: dict[str, float | str] = field(default_factory=dict)
    raw_rows: list[dict] = field(default_factory=list)
    skill_invocation: dict = field(default_factory=dict)
    generated_at: str = ""


@dataclass
class AuditBundle:
    """Top-level envelope returned to CLI / API consumers."""

    inputs: AuditInputs
    outputs: AuditOutputs
    platform: str = "google_ads"
    skill_name: str = "anthropic-skills:gads-auditor"

    def as_dict(self) -> dict:
        return {
            "platform": self.platform,
            "skill_name": self.skill_name,
            "client_slug": self.inputs.client_slug,
            "period": self.inputs.normalised_period(),
            "business_category": self.inputs.business_category,
            "notes": self.inputs.notes,
            "generated_at": self.outputs.generated_at,
            "kpis": self.outputs.kpis,
            "sections": self.outputs.sections,
            "skill_invocation": self.outputs.skill_invocation,
            "row_count": len(self.outputs.raw_rows),
        }


# ── CSV parsing ──────────────────────────────────────────────────────────────

CANONICAL_KEYS = {
    "campaign": ("Campaign", "Campagne", "campaign_name"),
    "campaign_type": ("Campaign type", "Type de campagne", "campaign_type"),
    "status": ("Status", "Statut"),
    "impressions": ("Impressions", "Impr."),
    "clicks": ("Clicks", "Clics"),
    "cost": ("Cost", "Coût", "Spend", "Dépense"),
    "conversions": ("Conversions", "Conv."),
    "conv_value": (
        "Conv. value",
        "Conversion value",
        "Valeur de conversion",
        "Valeur conv.",
    ),
    "ctr": ("CTR", "Taux de clics"),
    "avg_cpc": ("Avg. CPC", "CPC moy."),
    "cpa": ("Cost / conv.", "CPA"),
    "roas": ("ROAS", "Conv. value / cost"),
}


def _coerce_float(value: str | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    text = text.replace(" ", "").replace("%", "").replace(",", ".")
    text = text.replace("€", "").replace("$", "").replace("USD", "").replace("EUR", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _coerce_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _pick(row: dict, keys: tuple) -> str:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return ""


def parse_gads_csv(csv_text: str) -> list[dict]:
    """Parse a Google Ads Editor / Reports CSV into canonical row dicts."""
    rows: list[dict] = []
    if not csv_text:
        return rows
    reader = csv.DictReader(io.StringIO(csv_text))
    for raw in reader:
        normalised = {key: _pick(raw, canonical) for key, canonical in CANONICAL_KEYS.items()}
        if not normalised["campaign"]:
            continue
        rows.append(
            {
                "campaign": _coerce_str(normalised["campaign"]),
                "campaign_type": _coerce_str(normalised["campaign_type"]) or "search",
                "status": _coerce_str(normalised["status"]) or "enabled",
                "impressions": int(_coerce_float(normalised["impressions"])),
                "clicks": int(_coerce_float(normalised["clicks"])),
                "cost": round(_coerce_float(normalised["cost"]), 2),
                "conversions": _coerce_float(normalised["conversions"]),
                "conv_value": _coerce_float(normalised["conv_value"]),
                "ctr_pct": _coerce_float(normalised["ctr"]),
                "avg_cpc": _coerce_float(normalised["avg_cpc"]),
                "cpa": _coerce_float(normalised["cpa"]),
                "roas": _coerce_float(normalised["roas"]),
            }
        )
    return rows


# ── KPI roll-up ──────────────────────────────────────────────────────────────

def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if not denominator:
        return default
    return numerator / denominator


def compute_kpis(rows: Iterable[dict]) -> dict[str, float | int]:
    rows = list(rows)
    impressions = sum(r["impressions"] for r in rows)
    clicks = sum(r["clicks"] for r in rows)
    cost = sum(r["cost"] for r in rows)
    conversions = sum(r["conversions"] for r in rows)
    conv_value = sum(r["conv_value"] for r in rows)
    return {
        "campaigns": len(rows),
        "impressions": impressions,
        "clicks": clicks,
        "cost": round(cost, 2),
        "conversions": round(conversions, 2),
        "conv_value": round(conv_value, 2),
        "ctr_pct": round(_safe_div(clicks, impressions) * 100.0, 2),
        "avg_cpc": round(_safe_div(cost, clicks), 2),
        "cpa": round(_safe_div(cost, conversions), 2),
        "roas": round(_safe_div(conv_value, cost), 2),
    }


# ── section builders (deterministic preview) ─────────────────────────────────

def _section_overview(inputs: AuditInputs, kpis: dict) -> dict:
    return {
        "title": SECTION_TITLES["A"],
        "summary": (
            f"Audit Google Ads pour {inputs.client_slug} — période {inputs.normalised_period()}."
            f" {kpis['campaigns']} campagne(s) analysée(s)."
        ),
        "kpis": kpis,
        "notes": inputs.notes,
    }


def _section_campaigns(rows: list[dict]) -> dict:
    by_type: dict[str, dict] = {}
    for row in rows:
        bucket = by_type.setdefault(
            row["campaign_type"].lower() or "search",
            {"campaigns": 0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0},
        )
        bucket["campaigns"] += 1
        bucket["cost"] += row["cost"]
        bucket["conversions"] += row["conversions"]
        bucket["conv_value"] += row["conv_value"]
    breakdown = [
        {
            "campaign_type": ctype,
            "campaigns": data["campaigns"],
            "cost": round(data["cost"], 2),
            "conversions": round(data["conversions"], 2),
            "conv_value": round(data["conv_value"], 2),
            "roas": round(_safe_div(data["conv_value"], data["cost"]), 2),
        }
        for ctype, data in sorted(by_type.items())
    ]
    return {
        "title": SECTION_TITLES["B"],
        "breakdown_by_type": breakdown,
        "top_campaigns": sorted(rows, key=lambda r: r["cost"], reverse=True)[:5],
    }


def _section_skill_slot(letter: str, hint: str) -> dict:
    return {
        "title": SECTION_TITLES[letter],
        "narrative": SKILL_SLOT,
        "skill_hint": hint,
    }


def _section_recommendations() -> dict:
    return {
        "title": SECTION_TITLES["F"],
        "quick_wins": SKILL_SLOT,
        "structural": SKILL_SLOT,
        "skill_hint": (
            "Le skill gads-auditor remplit cette section: 5–10 quick-wins (≤2 semaines)"
            " + 3–5 changements structurels (≥4 semaines), chacun avec impact estimé,"
            " effort, owner suggéré."
        ),
    }


def _section_next_steps() -> dict:
    return {
        "title": SECTION_TITLES["G"],
        "timeline": SKILL_SLOT,
        "skill_hint": (
            "Le skill ordonne les recommandations sur une timeline 0–4 semaines / 4–12 semaines."
        ),
    }


def _section_annexes(inputs: AuditInputs, row_count: int) -> dict:
    csv_ref = str(inputs.csv_path) if inputs.csv_path else "<csv en mémoire>"
    return {
        "title": SECTION_TITLES["H"],
        "csv_reference": csv_ref,
        "row_count": row_count,
        "screenshots_dir": f"data/audits/gads/{inputs.client_slug}/screenshots/",
        "skill_hint": "Annexes complétées par le skill (captures Search Terms, Auction Insights, etc.).",
    }


def _build_sections(inputs: AuditInputs, rows: list[dict], kpis: dict) -> dict[str, dict]:
    return {
        "A": _section_overview(inputs, kpis),
        "B": _section_campaigns(rows),
        "C": _section_skill_slot(
            "C",
            "Keywords + audiences: top + bottom performers, search terms à exclure, niveaux d'enchères.",
        ),
        "D": _section_skill_slot(
            "D",
            "Creatives: ad copy variants, RSA strength, image/video assets, Pmax assets coverage.",
        ),
        "E": _section_skill_slot(
            "E",
            "Tracking: GA4 import, GTM tags, value tracking, attribution model, EEC.",
        ),
        "F": _section_recommendations(),
        "G": _section_next_steps(),
        "H": _section_annexes(inputs, len(rows)),
    }


# ── public entrypoint ────────────────────────────────────────────────────────

def _load_csv_text(inputs: AuditInputs) -> str:
    if inputs.csv_text:
        return inputs.csv_text
    if inputs.csv_path:
        return pathlib.Path(inputs.csv_path).read_text(encoding="utf-8")
    return ""


def run_audit(inputs: AuditInputs) -> AuditBundle:
    """Run the Google Ads audit pipeline (parse + structure + skill-slot fill).

    Returns a fully shaped `AuditBundle`. Narrative sections (C, D, E, F, G)
    contain `<<SKILL_FILLED>>` markers that the Anthropic skill replaces during
    interactive invocation. The deterministic preview (A, B, H) is computed
    directly from the CSV so the module is testable without LLM access.
    """
    csv_text = _load_csv_text(inputs)
    rows = parse_gads_csv(csv_text)
    kpis = compute_kpis(rows)
    sections = _build_sections(inputs, rows, kpis)

    outputs = AuditOutputs(
        sections=sections,
        kpis=kpis,
        raw_rows=rows,
        skill_invocation={
            "skill": "anthropic-skills:gads-auditor",
            "trigger": "audit Google Ads",
            "max_session_skills": 3,
            "combo": "agency_products",
            "csv_rows_passed": len(rows),
            "slots_to_fill": [letter for letter in SECTIONS if SKILL_SLOT in json.dumps(sections[letter])],
        },
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    return AuditBundle(inputs=inputs, outputs=outputs)
