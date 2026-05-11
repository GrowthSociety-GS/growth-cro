"""Meta Ads audit orchestration (axis #4 — orchestration).

Thin wrapper that:

1. parses a Meta Ads Manager CSV export (or accepts pre-parsed rows),
2. shapes the canonical `AuditBundle` payload the
   `anthropic-skills:meta-ads-auditor` skill consumes,
3. computes a deterministic preview using CSV-derived KPIs so the module is
   useful even without an interactive skill invocation,
4. delegates qualitative analysis (audiences, creatives, recos, next steps)
   to the skill by leaving narrative slots labelled `<<SKILL_FILLED>>` — the
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
    "A": "Overview compte Meta (Facebook + Instagram)",
    "B": "Campagnes (ASC, Advantage+, conversions, leads)",
    "C": "Audiences (broad + lookalike + custom + retargeting)",
    "D": "Creatives (ad copy + visuels + video assets)",
    "E": "Conversions (Pixel + CAPI + offline events)",
    "F": "Recommandations priorisées (quick wins + structural)",
    "G": "Next steps actionables (timeline)",
    "H": "Annexes (CSV exports + screenshots)",
}

SKILL_SLOT = "<<SKILL_FILLED>>"


# ── data classes ─────────────────────────────────────────────────────────────

@dataclass
class AuditInputs:
    """Inputs accepted by the audit pipeline.

    Today: CSV path or in-memory CSV text (Meta Ads Manager export).
    V2 (out of scope #22): Meta Marketing API direct.
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
    sections: dict[str, dict] = field(default_factory=dict)
    kpis: dict[str, float | str] = field(default_factory=dict)
    raw_rows: list[dict] = field(default_factory=list)
    skill_invocation: dict = field(default_factory=dict)
    generated_at: str = ""


@dataclass
class AuditBundle:
    inputs: AuditInputs
    outputs: AuditOutputs
    platform: str = "meta_ads"
    skill_name: str = "anthropic-skills:meta-ads-auditor"

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
    "campaign": ("Campaign name", "Nom de la campagne", "Campaign"),
    "objective": ("Objective", "Objectif"),
    "buying_type": ("Buying type", "Type d'achat"),
    "delivery": ("Delivery", "Diffusion"),
    "impressions": ("Impressions", "Impr."),
    "reach": ("Reach", "Couverture"),
    "clicks": ("Clicks (all)", "Link clicks", "Clics (tous)"),
    "ctr": ("CTR (all)", "CTR (link)", "CTR (toutes)"),
    "cpm": ("CPM", "CPM (cost per 1,000 impressions)"),
    "cpc": ("CPC (all)", "CPC (link)"),
    "spend": ("Amount spent (USD)", "Amount spent (EUR)", "Spend", "Dépenses"),
    "purchases": ("Purchases", "Achats", "Website purchases"),
    "purchase_value": (
        "Purchases conversion value",
        "Website purchases conversion value",
        "Valeur de conversion des achats",
    ),
    "leads": ("Leads", "On-Facebook leads", "Form leads"),
    "frequency": ("Frequency", "Fréquence"),
    "roas": ("Purchase ROAS", "Website purchase ROAS", "ROAS achats"),
}


def _coerce_float(value) -> float:
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


def parse_meta_csv(csv_text: str) -> list[dict]:
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
                "objective": _coerce_str(normalised["objective"]) or "outcome_sales",
                "buying_type": _coerce_str(normalised["buying_type"]) or "auction",
                "delivery": _coerce_str(normalised["delivery"]) or "active",
                "impressions": int(_coerce_float(normalised["impressions"])),
                "reach": int(_coerce_float(normalised["reach"])),
                "clicks": int(_coerce_float(normalised["clicks"])),
                "ctr_pct": _coerce_float(normalised["ctr"]),
                "cpm": _coerce_float(normalised["cpm"]),
                "cpc": _coerce_float(normalised["cpc"]),
                "spend": round(_coerce_float(normalised["spend"]), 2),
                "purchases": _coerce_float(normalised["purchases"]),
                "purchase_value": _coerce_float(normalised["purchase_value"]),
                "leads": _coerce_float(normalised["leads"]),
                "frequency": _coerce_float(normalised["frequency"]),
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
    reach = sum(r["reach"] for r in rows)
    clicks = sum(r["clicks"] for r in rows)
    spend = sum(r["spend"] for r in rows)
    purchases = sum(r["purchases"] for r in rows)
    purchase_value = sum(r["purchase_value"] for r in rows)
    leads = sum(r["leads"] for r in rows)
    return {
        "campaigns": len(rows),
        "impressions": impressions,
        "reach": reach,
        "clicks": clicks,
        "spend": round(spend, 2),
        "purchases": round(purchases, 2),
        "purchase_value": round(purchase_value, 2),
        "leads": round(leads, 2),
        "ctr_pct": round(_safe_div(clicks, impressions) * 100.0, 2),
        "cpm": round(_safe_div(spend, impressions) * 1000.0, 2),
        "cpc": round(_safe_div(spend, clicks), 2),
        "cpa": round(_safe_div(spend, purchases), 2),
        "roas": round(_safe_div(purchase_value, spend), 2),
    }


# ── section builders (deterministic preview) ─────────────────────────────────

def _section_overview(inputs: AuditInputs, kpis: dict) -> dict:
    return {
        "title": SECTION_TITLES["A"],
        "summary": (
            f"Audit Meta Ads pour {inputs.client_slug} — période {inputs.normalised_period()}."
            f" {kpis['campaigns']} campagne(s) analysée(s)."
        ),
        "kpis": kpis,
        "notes": inputs.notes,
    }


def _section_campaigns(rows: list[dict]) -> dict:
    by_objective: dict[str, dict] = {}
    for row in rows:
        bucket = by_objective.setdefault(
            row["objective"].lower() or "outcome_sales",
            {
                "campaigns": 0,
                "spend": 0.0,
                "purchases": 0.0,
                "purchase_value": 0.0,
                "leads": 0.0,
            },
        )
        bucket["campaigns"] += 1
        bucket["spend"] += row["spend"]
        bucket["purchases"] += row["purchases"]
        bucket["purchase_value"] += row["purchase_value"]
        bucket["leads"] += row["leads"]
    breakdown = [
        {
            "objective": obj,
            "campaigns": data["campaigns"],
            "spend": round(data["spend"], 2),
            "purchases": round(data["purchases"], 2),
            "purchase_value": round(data["purchase_value"], 2),
            "leads": round(data["leads"], 2),
            "roas": round(_safe_div(data["purchase_value"], data["spend"]), 2),
        }
        for obj, data in sorted(by_objective.items())
    ]
    return {
        "title": SECTION_TITLES["B"],
        "breakdown_by_objective": breakdown,
        "top_campaigns": sorted(rows, key=lambda r: r["spend"], reverse=True)[:5],
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
            "Le skill meta-ads-auditor remplit cette section: 5–10 quick-wins"
            " (≤2 semaines) + 3–5 changements structurels (≥4 semaines), chacun"
            " avec impact estimé, effort, owner suggéré (creative, audience, tracking)."
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
        "screenshots_dir": f"data/audits/meta/{inputs.client_slug}/screenshots/",
        "skill_hint": (
            "Annexes complétées par le skill (captures Audience overlap, Pixel events,"
            " ASC Advantage+ breakdown, Creative library)."
        ),
    }


def _build_sections(inputs: AuditInputs, rows: list[dict], kpis: dict) -> dict[str, dict]:
    return {
        "A": _section_overview(inputs, kpis),
        "B": _section_campaigns(rows),
        "C": _section_skill_slot(
            "C",
            "Audiences: broad / lookalike / custom / retargeting — overlap, taille,"
            " saturation, advantage+ audience usage.",
        ),
        "D": _section_skill_slot(
            "D",
            "Creatives: ad copy variants, hooks, UGC ratio, video vs static,"
            " creative fatigue, top performers, dynamic creative optimisation.",
        ),
        "E": _section_skill_slot(
            "E",
            "Tracking: Pixel events, Conversions API (CAPI) coverage, offline events,"
            " EMQ (event match quality), iOS14 attribution windows.",
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
    """Run the Meta Ads audit pipeline (parse + structure + skill-slot fill).

    Returns a fully shaped `AuditBundle`. Narrative sections (C, D, E, F, G)
    contain `<<SKILL_FILLED>>` markers that the Anthropic skill replaces during
    interactive invocation. The deterministic preview (A, B, H) is computed
    directly from the CSV so the module is testable without LLM access.
    """
    csv_text = _load_csv_text(inputs)
    rows = parse_meta_csv(csv_text)
    kpis = compute_kpis(rows)
    sections = _build_sections(inputs, rows, kpis)

    outputs = AuditOutputs(
        sections=sections,
        kpis=kpis,
        raw_rows=rows,
        skill_invocation={
            "skill": "anthropic-skills:meta-ads-auditor",
            "trigger": "audit Meta Ads",
            "max_session_skills": 3,
            "combo": "agency_products",
            "csv_rows_passed": len(rows),
            "slots_to_fill": [letter for letter in SECTIONS if SKILL_SLOT in json.dumps(sections[letter])],
        },
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    return AuditBundle(inputs=inputs, outputs=outputs)
