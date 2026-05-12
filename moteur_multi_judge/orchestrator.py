"""Multi-Judge Orchestrator V26.AA Sprint 3.

Orchestre les 3 juges complémentaires sur une LP HTML générée :

  1. doctrine_judge.py     → 54 critères V3.2 (notre IP CRO) — Sprint 2 V26.AA
  2. humanlike_judge       → 8 dim sensorielles (V26.Z W1.b — gardé)
  3. implementation_check  → sanity Python (V26.Z P0 — gardé universel)

Pondération final_score (validée par Mathis 2026-05-03 design doc Q1) :
  - 70% doctrine V3.2 (l'IP fonctionnelle/CRO)
  - 30% humanlike (sensoriel/signature/polish)
  - Pénalité implementation_check si bugs critiques (counter à 0, opacity sans anim)

Si killer rule doctrine violée → cap déjà appliqué dans doctrine_judge.audit_lp_doctrine.

Output : audit unifié structuré pour la webapp / dashboard.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from moteur_multi_judge.judges.doctrine_judge import audit_lp_doctrine

# humanlike_judge : encore dans skills/growth-site-generator (V26.Z, à move Sprint 7)
sys.path.insert(0, str(ROOT / "skills" / "growth-site-generator" / "scripts"))
import importlib.util


def _load_humanlike_module():
    """Charge gsg_humanlike_audit.py V26.Z dynamiquement (pas encore migré)."""
    fp = ROOT / "skills" / "growth-site-generator" / "scripts" / "gsg_humanlike_audit.py"
    if not fp.exists():
        return None
    spec = importlib.util.spec_from_file_location("gsg_humanlike_audit_v26z", fp)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_implementation_module():
    """Charge fix_html_runtime.py V26.Z (qui contient detect_runtime_bugs)."""
    fp = ROOT / "skills" / "growth-site-generator" / "scripts" / "fix_html_runtime.py"
    if not fp.exists():
        return None
    spec = importlib.util.spec_from_file_location("fix_html_runtime_v26z", fp)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _humanlike_pct(audit: dict) -> float:
    t = audit.get("totals", {})
    total = t.get("total") or t.get("humanlike_score") or 0
    total_max = t.get("total_max") or t.get("humanlike_max") or 80
    if not total_max:
        return 0
    return round(float(total) / float(total_max) * 100, 1)


def _impl_penalty(impl_report: dict) -> float:
    """Pénalité en pourcentage points (0-25) selon la sévérité des bugs runtime.

    Critical (counter à 0 sans JS, opacity 0 sans animation, reveal sans JS) → -10pp chacun
    Warning → -2pp chacun, plafond -25pp total.
    """
    if not impl_report:
        return 0.0
    fixes = impl_report.get("bugs_detected") or impl_report.get("warnings") or []
    if not isinstance(fixes, list):
        fixes = []
    n_crit = 0
    n_warn = 0
    for item in fixes:
        sev = (item.get("severity") if isinstance(item, dict) else "") or "warning"
        if sev.lower() in ("critical", "error", "fatal"):
            n_crit += 1
        else:
            n_warn += 1
    pen = min(25.0, n_crit * 10 + n_warn * 2)
    return float(pen)


def _verdict_tier(pct: float) -> str:
    if pct >= 85: return "🏆 Exceptionnel"
    if pct >= 75: return "✅ Excellent"
    if pct >= 65: return "🟡 Bon"
    if pct >= 50: return "⚠️ Moyen"
    return "🔴 Insuffisant"


def run_multi_judge(
    html: str,
    client: str,
    page_type: str = "lp_listicle",
    *,
    weight_doctrine: float = 0.7,
    weight_humanlike: float = 0.3,
    skip_humanlike: bool = False,
    skip_implementation: bool = False,
    verbose: bool = True,
) -> dict:
    """Audit complet d'une LP HTML par les 3 juges complémentaires.

    Args:
      html: HTML brut de la LP
      client: slug client (charge brand_dna pour les juges)
      page_type: ex "lp_listicle"
      weight_doctrine / weight_humanlike : pondération final_score (default 70/30)

    Returns: audit dict avec :
      - doctrine : output complet doctrine_judge
      - humanlike : output complet humanlike_judge
      - implementation : output detect_runtime_bugs
      - final : {final_score_pct, verdict, weighted_score, impl_penalty, breakdown}
      - totals_meta : tokens / wall / cost aggregates
    """
    if verbose:
        print(f"\n══ Multi-Judge V26.AA — {client} / {page_type} ══")

    grand_t0 = time.time()
    audit: dict = {"client": client, "page_type": page_type, "audit_version": "V26.AA.multi_judge"}

    # ── 1. Doctrine V3.2 (Sprint 2) ─────────────────────────
    if verbose:
        print("\n→ Juge 1/3 : Doctrine V3.2 (54 critères, paralllélisé par pilier)...")
    doctrine_audit = audit_lp_doctrine(html, client, page_type, verbose=verbose, parallel=True)
    audit["doctrine"] = doctrine_audit

    # ── 2. Humanlike (V26.Z W1.b) ───────────────────────────
    humanlike_audit = {}
    if not skip_humanlike:
        if verbose:
            print("\n→ Juge 2/3 : Humanlike (8 dim sensorielles, persona DA senior)...")
        hl_mod = _load_humanlike_module()
        if hl_mod and hasattr(hl_mod, "audit_lp_humanlike"):
            try:
                humanlike_audit = hl_mod.audit_lp_humanlike(html, client, verbose=verbose)
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  humanlike judge failed: {e}", flush=True)
                humanlike_audit = {"error": str(e)}
        else:
            humanlike_audit = {"error": "humanlike module not loadable"}
    audit["humanlike"] = humanlike_audit

    # ── 3. Implementation Check (V26.Z P0) ──────────────────
    impl_report = {}
    if not skip_implementation:
        if verbose:
            print("\n→ Juge 3/3 : Implementation Check (counter, reveal, opacity bugs)...")
        impl_mod = _load_implementation_module()
        if impl_mod and hasattr(impl_mod, "detect_runtime_bugs"):
            try:
                impl_report = impl_mod.detect_runtime_bugs(html)
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  impl check failed: {e}", flush=True)
                impl_report = {"error": str(e)}
        else:
            impl_report = {"error": "implementation module not loadable"}
    audit["implementation"] = impl_report

    # ── 4. Compute weighted final score ──────────────────────
    doctrine_pct = doctrine_audit.get("totals", {}).get("total_pct", 0)
    humanlike_pct = _humanlike_pct(humanlike_audit) if not humanlike_audit.get("error") else None
    impl_pen = _impl_penalty(impl_report)

    if humanlike_pct is not None:
        weighted = (weight_doctrine * doctrine_pct + weight_humanlike * humanlike_pct)
    else:
        # Fallback : si humanlike fail, on utilise juste doctrine
        weighted = doctrine_pct
    final_pct = max(0.0, weighted - impl_pen)

    audit["final"] = {
        "final_score_pct": round(final_pct, 1),
        "weighted_score_pct": round(weighted, 1),
        "verdict": _verdict_tier(final_pct),
        "impl_penalty_pct": round(impl_pen, 1),
        "breakdown": {
            "doctrine_pct": doctrine_pct,
            "doctrine_weight": weight_doctrine,
            "humanlike_pct": humanlike_pct,
            "humanlike_weight": weight_humanlike,
        },
        "killer_rules_violated": doctrine_audit.get("killer_rules_violated", False),
        "killer_violations": doctrine_audit.get("killer_violations", []),
    }

    # ── 5. Telemetry ────────────────────────────────────────
    grand_dt = time.time() - grand_t0
    tokens_in = (
        doctrine_audit.get("tokens_in", 0)
        + (humanlike_audit.get("tokens_in", 0) if isinstance(humanlike_audit, dict) else 0)
    )
    tokens_out = (
        doctrine_audit.get("tokens_out", 0)
        + (humanlike_audit.get("tokens_out", 0) if isinstance(humanlike_audit, dict) else 0)
    )
    cost = tokens_in / 1e6 * 3 + tokens_out / 1e6 * 15
    audit["totals_meta"] = {
        "wall_seconds": round(grand_dt, 1),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate_usd": round(cost, 3),
    }

    if verbose:
        print("\n══ Multi-Judge — DONE ══")
        print(f"  Doctrine V3.2  : {doctrine_pct}% ({_verdict_tier(doctrine_pct)})")
        if humanlike_pct is not None:
            print(f"  Humanlike      : {humanlike_pct}% ({_verdict_tier(humanlike_pct)})")
        else:
            print("  Humanlike      : ⚠️ failed")
        if impl_pen:
            print(f"  Impl penalty   : -{impl_pen:.1f}pp")
        print("  ═════════════════════════════════════")
        print(f"  FINAL SCORE    : {final_pct}% — {_verdict_tier(final_pct)}")
        print(f"  Coût total     : ${audit['totals_meta']['cost_estimate_usd']} | Wall : {grand_dt:.1f}s")
        if audit["final"]["killer_rules_violated"]:
            print(f"  ⛔ KILLER RULES VIOLATED ({len(audit['final']['killer_violations'])})")

    return audit


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--client", required=True)
    ap.add_argument("--page-type", default="lp_listicle")
    ap.add_argument("--output")
    args = ap.parse_args()

    html = pathlib.Path(args.html).read_text()
    audit = run_multi_judge(html, args.client, args.page_type, verbose=True)

    out = pathlib.Path(args.output or (ROOT / "data" / f"_multi_judge_{args.client}.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(f"\n✓ Audit saved : {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
