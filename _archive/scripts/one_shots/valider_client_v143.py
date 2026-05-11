#!/usr/bin/env python3
"""
valider_client_v143.py — V14.3.1 onboarding/runtime gate for saas_autonomous mode.

Purpose
-------
Given a client from clients_database.json, verify that each pattern required in
V14.2.3 (11 doctrinal + 7 regulatory_flagged) has its v143.* fields filled
to the confidence threshold required for saas_autonomous mode.

Produces a GO/NO-GO verdict + per-pattern breakdown:
- OK       : field present + confidence ≥ threshold
- WARN     : field present but confidence below threshold (degraded rendering)
- BLOCK    : field missing/empty/default → pattern cannot render in saas mode

Usage
-----
  # Validate one client (exit 0 if GO, 2 if NO-GO)
  python3 scripts/valider_client_v143.py --client japhy

  # Validate all clients and print summary table
  python3 scripts/valider_client_v143.py --all

  # Output JSON report to file
  python3 scripts/valider_client_v143.py --client japhy --json reports/validator_japhy.json

  # Fail-hard on any BLOCK (exit 2)
  python3 scripts/valider_client_v143.py --client japhy --strict

Non-zero exits:
  1 : usage error
  2 : NO-GO (blocks present) when --strict
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "clients_database.json"


# -----------------------------------------------------------------------------
# V143 REQUIREMENTS — synchronized with scripts/generate_lp_from_audit.py
# -----------------------------------------------------------------------------

V143_REQUIREMENTS = {
    "pat_psy_02__doctrinal__001": {
        "name": "scarcity",
        "required_paths": ["v143.scarcity.proof_type"],
        "none_values": ["none", None, ""],
        "confidence_paths": {"v143.scarcity.proof_type": "v143.scarcity._confidence.proof_type"},
        "min_confidence": {"v143.scarcity.proof_type": 0.70},
        "consequence_saas": "disable_scarcity_mentions",
        "consequence_internal": "warn_operator_verify",
        "regulatory_flag": {"dgccrf_risk": "high", "ftc_risk": "high"},
    },
    "pat_psy_04__doctrinal__001": {
        "name": "loss_framing",
        "required_paths": ["v143.loss_framing_opt_in"],
        "none_values": [False, None],
        "consequence_saas": "disable_loss_framing_keep_risk_reversal",
        "consequence_internal": "warn_operator_verify",
        "regulatory_flag": {"dgccrf_risk": "medium", "ftc_risk": "medium"},
    },
    "pat_psy_05__doctrinal__001": {
        "name": "founder_authority",
        "required_paths": [
            "v143.founder.named",
            "v143.founder.name",
        ],
        "strong_paths": [
            "v143.founder.bio",
            "v143.founder.linkedin_url",
            "v143.founder.photo_url",
        ],
        "confidence_paths": {
            "v143.founder.named": "v143.founder._confidence.named",
            "v143.founder.name": "v143.founder._confidence.name",
            "v143.founder.linkedin_url": "v143.founder._confidence.linkedin_url",
        },
        "min_confidence": {
            "v143.founder.named": 0.85,
            "v143.founder.name": 0.85,
            "v143.founder.linkedin_url": 0.75,
        },
        "consequence_saas": "fallback_to_strict_3_signals",
        "consequence_internal": "warn_operator_verify",
        "regulatory_flag": {"dgccrf_risk": "medium", "ftc_risk": "high"},
    },
    "pat_psy_08__doctrinal__001": {
        "name": "voc_verbatims",
        "required_paths": ["v143.voc_verbatims"],
        "min_len": 3,
        "confidence_paths": {"v143.voc_verbatims": "v143.voc_meta._confidence"},
        "min_confidence": {"v143.voc_verbatims": 0.70},
        "consequence_saas": "disable_voc_section",
        "consequence_internal": "warn_operator_collect_voc",
        "regulatory_flag": {"dgccrf_risk": "high", "ftc_risk": "high"},
    },
    "pat_per_07__doctrinal__001": {
        "name": "archetype",
        "required_paths": ["v143.archetype_macro"],
        "consequence_saas": "default_archetype_from_category",
        "consequence_internal": "warn_operator_calibrate",
    },
    "pat_per_11__doctrinal__001": {
        "name": "awareness_stage",
        "required_paths": ["v143.audience_awareness_stage"],
        "consequence_saas": "default_stage_from_category",
        "consequence_internal": "warn_operator_calibrate",
    },
    "pat_coh_03__doctrinal__001": {
        "name": "scent_matching",
        "required_paths": ["v143.ad_copy_source.ad_primary_headline"],
        "consequence_saas": "skip_scent_score",
        "consequence_internal": "warn_operator_provide_ad",
        "regulatory_flag": {"dgccrf_risk": "low", "ftc_risk": "low"},
    },
    "pat_coh_04__doctrinal__001": {
        "name": "positioning_claims",
        "required_paths": ["v143.differentiator_claims"],
        "min_len": 1,
        "consequence_saas": "enforce_reformulation_without_unique_claims",
        "consequence_internal": "warn_operator_provide_proof",
        "regulatory_flag": {"dgccrf_risk": "high", "ftc_risk": "high"},
    },
    "pat_coh_05__doctrinal__001": {
        "name": "voice_tone_4d",
        "required_paths": [
            "v143.voice_tone_4d.formel",
            "v143.voice_tone_4d.expert",
            "v143.voice_tone_4d.serieux",
            "v143.voice_tone_4d.direct",
        ],
        "consequence_saas": "wizard_8q_calibration",
        "consequence_internal": "warn_operator_interview_brand",
    },
    "pat_coh_09__doctrinal__001": {
        "name": "unique_mechanism",
        "required_paths": ["v143.unique_mechanism.validation_answer"],
        "consequence_saas": "bascule_coh_04",
        "consequence_internal": "warn_operator_validate_mechanism",
        "regulatory_flag": {"dgccrf_risk": "medium", "ftc_risk": "medium"},
    },
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _get_path(obj, dotted: str):
    cur = obj
    for p in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur


def _is_empty(val, none_values=(None,)):
    if val in none_values:
        return True
    if val is None:
        return True
    if val == "" or val == []:
        return True
    return False


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def validate_pattern(pattern_id: str, reqs: dict, client: dict, mode: str) -> dict:
    """Check a single V14.2.3 pattern against client v143 data."""
    required_paths = reqs.get("required_paths", [])
    none_values = reqs.get("none_values", [None])
    min_len = reqs.get("min_len")
    confidence_paths = reqs.get("confidence_paths", {})
    min_confidence = reqs.get("min_confidence", {})

    missing = []
    low_conf = []
    strong_missing = []

    for path in required_paths:
        val = _get_path(client, path)
        empty = _is_empty(val, none_values=none_values)
        if min_len and isinstance(val, list) and len(val) < min_len:
            empty = True
        if empty:
            missing.append(path)
            continue
        # Confidence gate (if defined for this path)
        if path in confidence_paths:
            conf_val = _get_path(client, confidence_paths[path])
            thresh = min_confidence.get(path, 0.70)
            if conf_val is None:
                low_conf.append({"path": path, "confidence": None, "threshold": thresh})
            elif isinstance(conf_val, (int, float)) and conf_val < thresh:
                low_conf.append({"path": path, "confidence": conf_val, "threshold": thresh})

    # Strong paths = optional-but-preferred (bio, photo, linkedin for founder)
    for path in reqs.get("strong_paths", []):
        val = _get_path(client, path)
        if _is_empty(val):
            strong_missing.append(path)

    # Status resolution
    if missing:
        status = "BLOCK"
    elif low_conf:
        status = "WARN"
    elif strong_missing and len(strong_missing) >= len(reqs.get("strong_paths", [1])):
        # All strong paths missing = degraded
        status = "WARN"
    else:
        status = "OK"

    consequence = None
    if status != "OK":
        key = "consequence_saas" if mode == "saas_autonomous" else "consequence_internal"
        consequence = reqs.get(key)

    return {
        "pattern_id": pattern_id,
        "pattern_name": reqs.get("name", ""),
        "status": status,
        "missing": missing,
        "low_confidence": low_conf,
        "strong_missing": strong_missing,
        "consequence": consequence,
        "regulatory_flag": reqs.get("regulatory_flag"),
    }


def validate_client(client: dict, mode: str) -> dict:
    """Full validation for one client."""
    v143 = client.get("v143")
    if not v143:
        return {
            "client_id": client["id"],
            "mode": mode,
            "verdict": "NO-GO",
            "reason": "no v143 namespace (run backfill_v143_clients.py first)",
            "patterns": [],
            "counts": {"OK": 0, "WARN": 0, "BLOCK": len(V143_REQUIREMENTS)},
        }

    per_pattern = []
    counts = {"OK": 0, "WARN": 0, "BLOCK": 0}
    blocking_regulatory = []

    for pid, reqs in V143_REQUIREMENTS.items():
        result = validate_pattern(pid, reqs, client, mode)
        per_pattern.append(result)
        counts[result["status"]] += 1

        # In saas_autonomous, a BLOCK on a regulatory_flagged pattern is hard-stop
        if mode == "saas_autonomous" and result["status"] == "BLOCK" and result.get("regulatory_flag"):
            blocking_regulatory.append(result["pattern_name"])

    # Verdict logic
    if mode == "saas_autonomous":
        if blocking_regulatory:
            verdict = "NO-GO"
            reason = f"regulatory_flag patterns blocked: {blocking_regulatory}"
        elif counts["BLOCK"] > len(V143_REQUIREMENTS) // 2:
            verdict = "NO-GO"
            reason = f"too many blocks ({counts['BLOCK']}/{len(V143_REQUIREMENTS)})"
        elif counts["BLOCK"] > 0:
            verdict = "DEGRADED"
            reason = f"{counts['BLOCK']} pattern(s) blocked → degraded output"
        elif counts["WARN"] > 0:
            verdict = "GO-WITH-WARNINGS"
            reason = f"{counts['WARN']} pattern(s) below confidence threshold"
        else:
            verdict = "GO"
            reason = "all 10 V14.2.3 patterns satisfied"
    else:  # internal_agency
        if counts["BLOCK"] == len(V143_REQUIREMENTS):
            verdict = "NO-GO"
            reason = "no v143 fields filled at all"
        elif counts["BLOCK"] > 0:
            verdict = "GO-WITH-WARNINGS"
            reason = f"{counts['BLOCK']} pattern(s) blocked — operator must handle"
        elif counts["WARN"] > 0:
            verdict = "GO-WITH-WARNINGS"
            reason = f"{counts['WARN']} pattern(s) below confidence"
        else:
            verdict = "GO"
            reason = "all 10 V14.2.3 patterns satisfied"

    return {
        "client_id": client["id"],
        "client_name": client.get("identity", {}).get("enterprise") or client["id"],
        "mode": mode,
        "verdict": verdict,
        "reason": reason,
        "counts": counts,
        "patterns": per_pattern,
        "blocking_regulatory": blocking_regulatory,
        "completeness_pct": (client.get("v143") or {}).get("_meta", {}).get("completeness_pct"),
    }


# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------

def print_client_report(report: dict, verbose: bool = False) -> None:
    vid = {"GO": "[OK]", "GO-WITH-WARNINGS": "[WARN]", "DEGRADED": "[DEGR]", "NO-GO": "[BLOCK]"}[report["verdict"]]
    print(f"\n{vid} {report['client_name']} ({report['client_id']}) — mode={report['mode']}")
    print(f"   Verdict     : {report['verdict']}")
    print(f"   Reason      : {report['reason']}")
    c = report["counts"]
    print(f"   Breakdown   : OK={c['OK']}  WARN={c['WARN']}  BLOCK={c['BLOCK']} / 10 patterns")
    if report.get("completeness_pct") is not None:
        print(f"   Completeness: {report['completeness_pct']}%")
    if report.get("blocking_regulatory"):
        print(f"   !! Reg-flag BLOCKING: {', '.join(report['blocking_regulatory'])}")

    if verbose:
        for p in report["patterns"]:
            tag = {"OK": "ok", "WARN": "warn", "BLOCK": "blk"}[p["status"]]
            line = f"     - {tag} {p['pattern_name']:<22s} {p['pattern_id']}"
            if p["missing"]:
                line += f"\n         missing: {p['missing']}"
            if p["low_confidence"]:
                confs = [f"{lc['path']}={lc['confidence']} (<{lc['threshold']})" for lc in p["low_confidence"]]
                line += f"\n         low_conf: {confs}"
            if p["consequence"]:
                line += f"\n         → {p['consequence']}"
            print(line)


def print_summary_table(reports: list) -> None:
    print()
    print(f"{'Client':<22} {'Mode':<18} {'Verdict':<18} {'OK':>4} {'WARN':>5} {'BLOCK':>6} {'Compl':>7}")
    print("-" * 88)
    for r in reports:
        c = r["counts"]
        compl = f"{r.get('completeness_pct','?')}%" if r.get("completeness_pct") is not None else "?"
        print(f"{r['client_id']:<22} {r['mode']:<18} {r['verdict']:<18} {c['OK']:>4} {c['WARN']:>5} {c['BLOCK']:>6} {compl:>7}")
    print()
    by_verdict = {}
    for r in reports:
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1
    print(f"Total {len(reports)} clients: " + ", ".join(f"{k}={v}" for k, v in by_verdict.items()))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="V14.2.3 SaaS-autonomous validator")
    parser.add_argument("--client", help="Single client ID")
    parser.add_argument("--all", action="store_true", help="All clients")
    parser.add_argument("--mode", choices=["internal_agency", "saas_autonomous"],
                        default="saas_autonomous",
                        help="Validation mode (default: saas_autonomous)")
    parser.add_argument("--json", help="Write JSON report to this file")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 2 on any NO-GO")
    parser.add_argument("--verbose", action="store_true",
                        help="Show per-pattern detail")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[ERROR] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    with open(DB_PATH) as f:
        db = json.load(f)

    clients_raw = db.get("clients", [])
    if isinstance(clients_raw, list):
        clients_by_id = {c["id"]: c for c in clients_raw if "id" in c}
    else:
        clients_by_id = clients_raw

    if args.client:
        if args.client not in clients_by_id:
            print(f"[ERROR] client '{args.client}' not in DB", file=sys.stderr)
            return 1
        targets = [args.client]
    elif args.all:
        targets = sorted(clients_by_id.keys())
    else:
        print("[ERROR] specify --client <id> or --all", file=sys.stderr)
        return 1

    reports = []
    for cid in targets:
        client = clients_by_id[cid]
        report = validate_client(client, mode=args.mode)
        reports.append(report)

    # Output
    if len(reports) == 1:
        print_client_report(reports[0], verbose=args.verbose)
    else:
        print_summary_table(reports)
        if args.verbose:
            for r in reports:
                print_client_report(r, verbose=True)

    # JSON output
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "mode": args.mode,
            "n_clients": len(reports),
            "reports": reports,
        }, indent=2, ensure_ascii=False))
        print(f"\n[OK] JSON report written: {out}")

    # Exit status
    if args.strict:
        blocking = [r for r in reports if r["verdict"] == "NO-GO"]
        if blocking:
            print(f"\n[STRICT] {len(blocking)} client(s) NO-GO", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
