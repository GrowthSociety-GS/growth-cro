#!/usr/bin/env python3
"""
score_applicability_overlay.py — P2.A Doctrine v3.2.0-draft (2026-04-18)

APPLICABILITY OVERLAY LAYER (layer 3 of scoring doctrine)
=========================================================
Runs AFTER contextual_overlay and BEFORE pillar aggregation.

Applies applicability_matrix_v1.json rules:
  - status NA         → removes criterion from kept_criteria + rawMax
  - status REQUIRED   → 2× penalty multiplier when score == 0
  - status BONUS      → removes from rawMax, adds score as bonus (capped at +5% pillar max)
  - status OPTIONAL   → leaves score as-is but flags for dashboard (no penalty if 0)
  - business_type weight_bias → applied in orchestrator on final pillar score100

Reads:
  - data/doctrine/applicability_matrix_v1.json   (rules + business_types)
  - data/clients_database.json                    (label → business_type)

Public API:
    apply_applicability_overlay(bloc_results, label, page_type) -> trace dict
    get_business_type_for_label(label) -> str | None
    get_weight_bias(business_type) -> dict (default 1.0 per pillar)

Traceability:
  Every rule firing is recorded in the trace dict. Each affected kept_criterion
  gets fields: applicability_status, applicability_rule_id, pre_applicability_*.
  ASSET/ENSEMBLE classification is NOT touched (that's layer 1's concern).
"""
from __future__ import annotations
import json
import pathlib
from functools import lru_cache
from datetime import datetime
from typing import Any

# Locate project root
def _find_root() -> pathlib.Path:
    p = pathlib.Path(__file__).resolve()
    while p != p.parent:
        if (p / "data").is_dir() and (p / "playbook").is_dir():
            return p
        p = p.parent
    return pathlib.Path.cwd()


ROOT = _find_root()
APPLICABILITY_PATH = ROOT / "data" / "doctrine" / "applicability_matrix_v1.json"
CLIENTS_DB_PATH = ROOT / "data" / "clients_database.json"

DEFAULT_WEIGHT_BIAS = {"hero": 1.0, "persuasion": 1.0, "ux": 1.0,
                       "coherence": 1.0, "psycho": 1.0, "tech": 1.0}


@lru_cache(maxsize=1)
def load_matrix() -> dict:
    if not APPLICABILITY_PATH.exists():
        return {}
    return json.loads(APPLICABILITY_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_clients_db() -> dict:
    if not CLIENTS_DB_PATH.exists():
        return {"clients": []}
    return json.loads(CLIENTS_DB_PATH.read_text(encoding="utf-8"))


def get_business_type_for_label(label: str) -> str | None:
    """Look up business_type for a client label. Falls back to None.

    Source of truth: identity.businessType (camelCase nested). Legacy/P2 backfill
    may also have stored it at top-level business_type. Both are checked.
    Normalization: lower_snake_case (lead gen → lead_gen) for matrix compatibility.
    """
    db = load_clients_db()
    for c in db.get("clients", []):
        if c.get("id") != label:
            continue
        bt = (c.get("identity") or {}).get("businessType") or c.get("business_type")
        if not bt:
            return None
        # Normalise spellings to matrix keys (ecommerce, lead_gen, saas, content, app)
        s = str(bt).strip().lower().replace(" ", "_").replace("-", "_")
        alias = {"e_commerce": "ecommerce", "leadgen": "lead_gen", "lead": "lead_gen",
                 "b2b_saas": "saas", "b2c_saas": "saas", "mobile_app": "app",
                 "consumer_app": "app", "media": "content", "learning": "content",
                 "fintech": "saas", "saas_fintech": "saas",
                 "insurtech": "lead_gen", "insurance": "lead_gen",
                 "coaching": "lead_gen", "services": "lead_gen"}
        return alias.get(s, s)
    return None


def get_weight_bias(business_type: str | None) -> dict:
    """Pillar weight bias per business_type. Defaults to 1.0 everywhere if unknown."""
    if not business_type:
        return dict(DEFAULT_WEIGHT_BIAS)
    matrix = load_matrix()
    bt_spec = matrix.get("business_types", {}).get(business_type)
    if not bt_spec:
        return dict(DEFAULT_WEIGHT_BIAS)
    bias = dict(DEFAULT_WEIGHT_BIAS)
    bias.update(bt_spec.get("weight_bias", {}))
    return bias


def _rules_applicable(rule: dict, page_type: str, business_type: str | None) -> bool:
    applies = rule.get("applies_to", {})
    if not applies:
        return True
    if "pageType" in applies and page_type not in applies["pageType"]:
        return False
    if "business_type" in applies:
        if not business_type or business_type not in applies["business_type"]:
            return False
    return True


def _collect_rules_for(page_type: str, business_type: str | None) -> list[dict]:
    matrix = load_matrix()
    out = []
    for rule in matrix.get("applicability_rules", []):
        if rule.get("id") == "rule_excl_via_page_type_criteria":
            continue  # already applied by page_type_filter
        if _rules_applicable(rule, page_type, business_type):
            out.append(rule)
    return out


def _pillar_of(cid: str) -> str | None:
    prefixes = {"hero": "hero", "per": "persuasion", "ux": "ux",
                "coh": "coherence", "psy": "psycho", "tech": "tech"}
    for pref, pillar in prefixes.items():
        if cid.startswith(pref):
            return pillar
    return None


def _score_of(item: dict) -> float:
    v = item.get("score")
    try:
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


def _max_of(item: dict) -> float:
    for k in ("max", "maxScore", "rawMax"):
        v = item.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return 3.0


def apply_applicability_overlay(bloc_results: dict, label: str, page_type: str) -> dict:
    """Apply applicability_matrix rules to kept_criteria. Mutates bloc_results in place.
    Returns overlay trace dict."""
    matrix = load_matrix()
    if not matrix:
        return {"applied": False, "reason": "applicability_matrix not loaded"}

    # Resolve legacy page_type aliases (e.g. 'lp' → 'lp_leadgen') before rule matching
    page_type_input = page_type
    aliases = matrix.get("page_type_aliases", {}) or {}
    page_type = aliases.get(page_type, page_type)

    business_type = get_business_type_for_label(label)
    bias = get_weight_bias(business_type)
    rules = _collect_rules_for(page_type, business_type)

    # Index by criterion → list of applicable rules (most-specific wins: REQUIRED > NA > BONUS > OPTIONAL)
    STATUS_PRIORITY = {"REQUIRED": 4, "NA": 3, "BONUS": 2, "OPTIONAL": 1}
    per_crit_status: dict[str, dict] = {}
    for rule in rules:
        status = rule.get("status")
        if not status:
            continue
        for cid in rule.get("criteria", []):
            existing = per_crit_status.get(cid)
            if (existing is None
                    or STATUS_PRIORITY.get(status, 0) > STATUS_PRIORITY.get(existing["status"], 0)):
                per_crit_status[cid] = {"status": status, "rule_id": rule.get("id"),
                                         "rule_description": rule.get("description", "")}

    removed_na = []
    required_hits = []  # (cid, before, after)
    bonus_hits = []     # (cid, pillar, bonus_pts)
    optional_flags = []
    bonus_pool: dict[str, float] = {}  # pillar → accumulated bonus

    for pillar, blk in bloc_results.items():
        kept = list(blk.get("kept_criteria") or [])
        new_kept = []
        pillar_removed = []
        for item in kept:
            cid = item.get("id") or item.get("criterion_id") or item.get("code")
            if not cid:
                new_kept.append(item)
                continue
            entry = per_crit_status.get(cid)
            if not entry:
                new_kept.append(item)
                continue
            status = entry["status"]
            rule_id = entry["rule_id"]
            s = _score_of(item)
            m = _max_of(item)

            if status == "NA":
                item["pre_applicability_score"] = s
                item["pre_applicability_max"] = m
                item["applicability_status"] = "NA"
                item["applicability_rule_id"] = rule_id
                removed_na.append({"criterion": cid, "pillar": pillar, "rule_id": rule_id,
                                   "removed_score": s, "removed_max": m})
                pillar_removed.append(item)
                continue  # drop from kept_criteria

            if status == "REQUIRED" and s == 0:
                # Double penalty: we can't go below 0, so flag and add virtual rawMax bump
                item["applicability_status"] = "REQUIRED"
                item["applicability_rule_id"] = rule_id
                item["required_penalty_applied"] = True
                # Penalty: duplicate the max for this criterion (effectively 2× weight when score=0)
                item["pre_applicability_max"] = m
                item["max"] = m * 2
                required_hits.append({"criterion": cid, "pillar": pillar, "rule_id": rule_id,
                                       "before_max": m, "after_max": m * 2, "score": s})
                new_kept.append(item)
                continue

            if status == "BONUS":
                item["applicability_status"] = "BONUS"
                item["applicability_rule_id"] = rule_id
                item["pre_applicability_score"] = s
                item["pre_applicability_max"] = m
                bonus_pool[pillar] = bonus_pool.get(pillar, 0.0) + s
                bonus_hits.append({"criterion": cid, "pillar": pillar, "rule_id": rule_id,
                                    "bonus_pts": s})
                # Remove from kept_criteria: bonus is tracked separately
                pillar_removed.append(item)
                continue

            if status == "OPTIONAL":
                item["applicability_status"] = "OPTIONAL"
                item["applicability_rule_id"] = rule_id
                optional_flags.append({"criterion": cid, "pillar": pillar, "rule_id": rule_id})
                new_kept.append(item)
                continue

            # REQUIRED with s > 0 — just flag, no penalty
            if status == "REQUIRED":
                item["applicability_status"] = "REQUIRED"
                item["applicability_rule_id"] = rule_id
                new_kept.append(item)
                continue

            new_kept.append(item)

        # Recompute pillar rawTotal/rawMax
        old_total = float(blk.get("rawTotal") or 0)
        old_max = float(blk.get("rawMax") or 0)
        new_total = sum(_score_of(i) for i in new_kept)
        new_max = sum(_max_of(i) for i in new_kept)

        # Apply bonus: capped at +5% of original pillar max
        bonus = bonus_pool.get(pillar, 0.0)
        bonus_cap = 0.05 * old_max
        bonus_applied = min(bonus, bonus_cap)

        blk["kept_criteria"] = new_kept
        blk["pre_applicability_rawTotal"] = round(old_total, 2)
        blk["pre_applicability_rawMax"] = round(old_max, 2)
        blk["rawTotal"] = round(new_total + bonus_applied, 2)
        blk["rawMax"] = round(new_max, 2)
        blk["score100"] = round(blk["rawTotal"] / blk["rawMax"] * 100, 1) if blk["rawMax"] else 0.0
        if bonus_applied > 0:
            blk["applicability_bonus"] = round(bonus_applied, 2)
            blk["applicability_bonus_cap"] = round(bonus_cap, 2)
        blk["applicability_removed_count"] = len(pillar_removed)
        blk["applicability_delta_rawTotal"] = round(blk["rawTotal"] - old_total, 2)
        blk["applicability_delta_rawMax"] = round(blk["rawMax"] - old_max, 2)

    # Apply business_type weight_bias to score100 per pillar (stored as weighted_score100 — orchestrator picks)
    weighted_per_pillar = {}
    for pillar, blk in bloc_results.items():
        s = float(blk.get("score100") or 0)
        w = bias.get(pillar, 1.0)
        weighted_per_pillar[pillar] = {"score100": s, "weight": w, "weighted_score100": round(s * w, 2)}

    return {
        "applied": bool(removed_na or required_hits or bonus_hits or optional_flags),
        "version": "1.0 (doctrine v3.2.0-draft)",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "label": label,
        "page_type": page_type_input,
        "page_type_resolved": page_type,
        "business_type": business_type,
        "weight_bias": bias,
        "removed_na": removed_na,
        "required_hits": required_hits,
        "bonus_hits": bonus_hits,
        "optional_flags": optional_flags,
        "weighted_per_pillar": weighted_per_pillar,
        "rules_matched": sorted({r.get("id") for r in rules}),
        "rules_matched_count": len(rules),
    }
