#!/usr/bin/env python3
"""
validate_utility_banner.py — Validation Étape 1a : Bloc 7 UTILITY_BANNER

Lance score_utility_banner.py sur 3 cas de figure connus et imprime un rapport
qui valide (ou invalide) le comportement attendu :

  Cas A : JAPHY / home       — PAS de cluster UTILITY_BANNER → skip propre (applicable=false)
  Cas B : SEONI / home       — cluster ancien mis-classé UTILITY_BANNER → fix height-gate → MODAL
  Cas C : <promo client>     — vrai banner promo "livraison offerte/-20%" → scoring PROMO

Usage :
    python3 skills/site-capture/scripts/validate_utility_banner.py
    python3 skills/site-capture/scripts/validate_utility_banner.py --cas-c tediber
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = pathlib.Path(__file__).resolve().parent
CAPTURES = ROOT / "data" / "captures"

DEFAULT_CAS = [
    ("A", "japhy",  "home", "Pas de UTILITY_BANNER attendu → applicable=False"),
    ("B", "seoni",  "home", "Ancien faux positif UTILITY_BANNER → doit être MODAL maintenant"),
    ("C", "tediber","home", "Banner promo livraison → variant PROMO attendu"),
]

def _load_perception(label: str, page: str) -> dict | None:
    p = CAPTURES / label / page / "perception_v13.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def _roles_from_perception(perc: dict) -> list[str]:
    roles = []
    if isinstance(perc.get("roles"), list):
        for r in perc["roles"]:
            if isinstance(r, dict):
                roles.append(r.get("role") or r.get("name") or "")
            else:
                roles.append(str(r))
    elif isinstance(perc.get("clusters"), list):
        for c in perc["clusters"]:
            role = c.get("role") or c.get("best_role")
            if role:
                roles.append(role)
    return roles

def _has_utility_banner(perc: dict) -> bool:
    return "UTILITY_BANNER" in _roles_from_perception(perc)

def _has_modal(perc: dict) -> bool:
    return "MODAL" in _roles_from_perception(perc)

def run_scorer(label: str, page: str) -> dict:
    script = SCRIPTS / "score_utility_banner.py"
    r = subprocess.run(
        [sys.executable, str(script), label, page],
        capture_output=True, text=True, timeout=60,
    )
    out_file = CAPTURES / label / page / "score_utility_banner.json"
    data = {}
    if out_file.exists():
        try:
            data = json.loads(out_file.read_text(encoding="utf-8"))
        except Exception as e:
            data = {"error": f"parse: {e}"}
    return {
        "returncode": r.returncode,
        "stdout_tail": r.stdout[-400:],
        "stderr_tail": r.stderr[-400:],
        "data": data,
    }

def validate_case(case: str, label: str, page: str, expected: str) -> dict:
    perc = _load_perception(label, page)
    if perc is None:
        return {"case": case, "label": label, "page": page, "status": "MISSING perception_v13.json"}

    has_ub = _has_utility_banner(perc)
    has_modal = _has_modal(perc)
    result = run_scorer(label, page)
    data = result["data"]
    applicable = data.get("applicable")
    variant = data.get("variant")
    total_21 = data.get("total_21")
    killers = data.get("killers_fired") or []
    contrib = data.get("contribution_page_score_pct")

    # Verdict
    verdict = []
    if case == "A":  # japhy home : no cluster
        if has_ub:
            verdict.append("❌ UTILITY_BANNER détecté (ne devrait pas)")
        else:
            verdict.append("✓ Pas de UTILITY_BANNER")
        if applicable is False:
            verdict.append("✓ scorer skip propre (applicable=False)")
        else:
            verdict.append(f"❌ scorer applicable={applicable}, attendu False")
    elif case == "B":  # seoni home : should be MODAL not UTILITY_BANNER
        if has_ub and not has_modal:
            verdict.append("❌ UTILITY_BANNER présent, height-gate n'a pas switché vers MODAL")
        elif has_modal:
            verdict.append("✓ MODAL détecté (fix height-gate appliqué)")
        elif not has_ub:
            verdict.append("✓ Plus de UTILITY_BANNER (reclassé autre chose)")
    elif case == "C":  # promo client
        if not has_ub:
            verdict.append("⚠️ UTILITY_BANNER pas détecté — vérifier si le client a vraiment un banner")
        else:
            verdict.append("✓ UTILITY_BANNER détecté")
            if variant == "PROMO":
                verdict.append("✓ variant=PROMO")
            else:
                verdict.append(f"⚠️ variant={variant}, attendu PROMO")
            if total_21 is not None:
                verdict.append(f"ℹ️ total_21={total_21} (killers={len(killers)}, contribution={contrib}%)")

    return {
        "case": case,
        "label": label,
        "page": page,
        "expected": expected,
        "has_utility_banner_in_perception": has_ub,
        "has_modal_in_perception": has_modal,
        "scorer_applicable": applicable,
        "scorer_variant": variant,
        "scorer_total_21": total_21,
        "scorer_killers": killers,
        "scorer_contribution_pct": contrib,
        "verdict": verdict,
        "rc": result["returncode"],
        "stderr_tail": result["stderr_tail"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cas-a", default="japhy")
    ap.add_argument("--cas-b", default="seoni")
    ap.add_argument("--cas-c", default="tediber")
    ap.add_argument("--json", action="store_true", help="output JSON only")
    args = ap.parse_args()

    cas = [
        ("A", args.cas_a,  "home", "Pas de UTILITY_BANNER attendu → applicable=False"),
        ("B", args.cas_b,  "home", "Ancien faux positif UTILITY_BANNER → doit être MODAL maintenant"),
        ("C", args.cas_c,  "home", "Banner promo livraison → variant PROMO attendu"),
    ]

    results = [validate_case(*c) for c in cas]

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    print("═" * 72)
    print(" VALIDATION ÉTAPE 1a — Bloc 7 UTILITY_BANNER")
    print("═" * 72)
    for r in results:
        print()
        print(f"── Cas {r['case']}: {r['label']}/{r['page']}")
        print(f"   Attendu : {r['expected']}")
        print(f"   Perception : UTILITY_BANNER={r['has_utility_banner_in_perception']}, MODAL={r['has_modal_in_perception']}")
        print(f"   Scorer     : applicable={r['scorer_applicable']}, variant={r['scorer_variant']}, "
              f"total_21={r['scorer_total_21']}, killers={r['scorer_killers']}, contrib={r['scorer_contribution_pct']}%")
        for v in r["verdict"]:
            print(f"   {v}")
        if r.get("stderr_tail"):
            print(f"   stderr: {r['stderr_tail'][:200]}")

    print()
    print("═" * 72)
    fails = sum(1 for r in results for v in r["verdict"] if v.startswith("❌"))
    warns = sum(1 for r in results for v in r["verdict"] if v.startswith("⚠️"))
    print(f"  {'✓ OK' if fails == 0 else '❌ ' + str(fails) + ' FAILS'}  ({warns} warnings)")
    print("═" * 72)

if __name__ == "__main__":
    main()
