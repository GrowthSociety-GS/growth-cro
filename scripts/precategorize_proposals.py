#!/usr/bin/env python3
"""Pre-categorize 69 audit-based doctrine proposals for Mathis review (Task #18 DoD).

For each proposal in data/learning/audit_based_proposals/dup_v29_*.json:
- Extract proposal_id, type, subtype, affected_criteria, scope, evidence
- Apply heuristics to assign a pré-verdict (propose_accept / propose_reject / propose_defer)
- Emit a markdown table to data/learning/audit_based_proposals/REVIEW_2026-05-11.md

Heuristics:
- subtype=strict_rule_too_punitive AND business_category=unknown (large N) → propose_accept
  (recalibration likely needed when the segment is generic).
- subtype=strict_rule_too_punitive AND business_category in {fintech, app} → propose_defer
  (segment-specific patterns may be legitimate signal).
- subtype=tighten_lax_rule → propose_reject (rare, requires evidence of false negatives, not
  available in proposal data).
- crit_id in tech_* AND subtype=tighten → propose_reject (tech is ASSET-level, deterministic).
- evidence.pct_critical >90% → propose_accept (overwhelming signal).
- evidence.pct_critical 70-90% → propose_defer (significant but reviewable).
- evidence.pct_critical <70% → propose_reject (insufficient sample).

Mathis remplit la colonne `Mathis_final` à la review. Aucune action taken yet.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROPOSALS_DIR = ROOT / "data" / "learning" / "audit_based_proposals"
OUTPUT_FILE = PROPOSALS_DIR / "REVIEW_2026-05-11.md"


def categorize(prop: dict) -> tuple[str, str]:
    """Return (pre_verdict, rationale).

    Subtypes observed in V29 proposals (2026-05-04):
    - strict_rule_too_punitive : pct_critical élevé sur un segment → considérer assouplir
    - lax_rule_under_discriminating : pct_top élevé (souvent 100%) → considérer durcir
    """
    subtype = prop.get("subtype", "")
    affected = prop.get("affected_criteria", [])
    crit_id = affected[0] if affected else ""
    scope = prop.get("scope", {})
    bcat = scope.get("business_category", "")
    evidence = prop.get("evidence", {})
    pct_critical = float(evidence.get("pct_critical", 0))
    pct_top = float(evidence.get("pct_top", 0))
    n_pages = int(evidence.get("n_pages_evaluated", 0))

    # ── lax_rule_under_discriminating : rule lets everyone pass → may need tighten
    if subtype == "lax_rule_under_discriminating":
        # Tech is ASSET-level — high pct_top = the metric is good, not the rule lax
        if crit_id.startswith("tech_"):
            return ("propose_reject", f"tech_* is ASSET-level; {pct_top:.0f}% TOP reflects deterministic metric, not lax rule")
        # 100% TOP in 'unknown' on small N — likely artifact, not real signal
        if pct_top >= 100 and n_pages < 15 and bcat == "unknown":
            return ("propose_reject", f"100% TOP on small generic sample (n={n_pages}, unknown) = noise, not lax rule signal")
        # 100% TOP in specific segment with >20 pages — segment may genuinely excel
        if pct_top >= 95 and n_pages >= 20:
            return ("propose_defer", f"{bcat} hits {pct_top:.0f}% TOP on {n_pages} pages — verify if rule lax OR segment excellent")
        # Lower thresholds — insufficient evidence
        return ("propose_reject", f"insufficient evidence for tightening ({pct_top:.0f}% top, n={n_pages}, {bcat})")

    # ── strict_rule_too_punitive : pct_critical high → consider relaxing
    if subtype == "strict_rule_too_punitive":
        if pct_critical >= 90 and n_pages >= 8:
            return ("propose_accept", f"overwhelming signal {pct_critical:.0f}% critical on {n_pages} pages ({bcat}) — recalibrate strict bound")
        if bcat == "unknown" and pct_critical >= 80:
            return ("propose_accept", f"generic segment 'unknown' with {pct_critical:.0f}% critical → strict bound likely off")
        if bcat in {"fintech", "app", "saas"} and pct_critical >= 70:
            return ("propose_defer", f"{bcat} segment-specific pattern {pct_critical:.0f}% — may be legitimate, verify 3-5 sample pages")
        if pct_critical < 70:
            return ("propose_reject", f"insufficient signal {pct_critical:.0f}% critical ({n_pages} pages) — keep current bound")
        return ("propose_defer", f"borderline {pct_critical:.0f}% on {n_pages} pages ({bcat}) — Mathis tranche")

    # Default
    return ("propose_defer", f"unclassified subtype={subtype}, pct_critical={pct_critical:.0f}%, pct_top={pct_top:.0f}%")


def main():
    proposals = sorted(PROPOSALS_DIR.glob("dup_v29_*.json"))
    print(f"Found {len(proposals)} proposals")

    rows = []
    verdict_counts = {"propose_accept": 0, "propose_reject": 0, "propose_defer": 0}

    for f in proposals:
        try:
            prop = json.loads(f.read_text())
        except Exception as e:
            print(f"  ! skip {f.name}: {e}")
            continue
        pid = prop.get("proposal_id", f.stem)
        # Short title
        subtype = prop.get("subtype", "")
        crit = ",".join(prop.get("affected_criteria", []))
        bcat = prop.get("scope", {}).get("business_category", "")
        title = f"{crit} / {subtype} / {bcat}"
        verdict, rationale = categorize(prop)
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        rows.append({
            "proposal_id": pid,
            "title": title,
            "pre_verdict": verdict,
            "rationale": rationale,
        })

    # Sort by verdict then crit_id
    verdict_order = {"propose_accept": 0, "propose_defer": 1, "propose_reject": 2}
    rows.sort(key=lambda r: (verdict_order.get(r["pre_verdict"], 99), r["title"]))

    # Render markdown
    md = ["# Doctrine Proposals Review — 2026-05-11 (Task #18 V3.3 CRE Fusion)\n"]
    md.append(f"**Total proposals**: {len(rows)}")
    md.append(f"**Pré-verdicts distribution**:")
    md.append(f"- `propose_accept`: {verdict_counts['propose_accept']}")
    md.append(f"- `propose_defer`: {verdict_counts['propose_defer']}")
    md.append(f"- `propose_reject`: {verdict_counts['propose_reject']}\n")
    md.append("**Méthode** : pré-catégorisation automatique via `scripts/precategorize_proposals.py` (heuristiques sur pct_critical, n_pages, business_category, criterion family). Mathis valide/corrige la colonne `Mathis_final`.\n")
    md.append("**Heuristiques** :")
    md.append("- subtype=strict_rule_too_punitive AND pct_critical≥90% AND n_pages≥8 → `propose_accept` (overwhelming signal)")
    md.append("- subtype=strict_rule_too_punitive AND business_category=unknown AND pct_critical≥80% → `propose_accept` (segment générique = bound off)")
    md.append("- subtype=strict_rule_too_punitive AND business_category∈{fintech,app,saas} AND pct_critical≥70% → `propose_defer` (segment-specific peut-être légitime)")
    md.append("- subtype=strict_rule_too_punitive AND pct_critical<70% → `propose_reject` (insufficient signal)")
    md.append("- subtype=lax_rule_under_discriminating AND crit_id ∈ tech_* → `propose_reject` (ASSET-level = mesure déterministe)")
    md.append("- subtype=lax_rule_under_discriminating AND pct_top≥95% AND n_pages≥20 → `propose_defer` (vérifier si règle lax OU segment excellent)")
    md.append("- subtype=lax_rule_under_discriminating AND pct_top≥100% AND n_pages<15 → `propose_reject` (artifact, pas signal)\n")
    md.append("---\n")
    md.append("| # | proposal_id | title | pré-verdict | rationale | Mathis_final |")
    md.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        # Truncate rationale to 140 chars
        rat = r["rationale"].replace("|", "/")
        if len(rat) > 140:
            rat = rat[:137] + "..."
        # Shorten proposal_id for table readability
        pid_short = r["proposal_id"].replace("dup_v29_2026_05_04_", "")
        md.append(f"| {i} | `{pid_short}` | {r['title']} | `{r['pre_verdict']}` | {rat} | |")

    md.append("\n---\n")
    md.append("## Notes pour Mathis\n")
    md.append("1. Les `propose_accept` recommandent de **assouplir** le strict bound du critère pour le segment (typiquement raise the `top` threshold OR lower the `critical` threshold).")
    md.append("2. Les `propose_defer` méritent un échantillon de 3-5 pages humanlike du segment pour vérifier si le pattern est légitime (marché) ou un bug scorer.")
    md.append("3. Les `propose_reject` peuvent être archivés directement (`data/learning/audit_based_proposals/_rejected/`) — leur signal n'est pas suffisant.")
    md.append("4. Aucune doctrine modifiée tant que Mathis n'a pas rempli `Mathis_final`. La colonne `Mathis_final` accepte : `accept` / `reject` / `defer` / `<override comment>`.\n")
    md.append("## Action items downstream (post-review)\n")
    md.append("- Pour chaque `accept` final : éditer le bloc V3.2.1 correspondant + bumper PATCH version + déplacer la proposal dans `_accepted/`.")
    md.append("- Pour chaque `reject` final : déplacer la proposal dans `_rejected/`.")
    md.append("- Pour chaque `defer` final : laisser dans `audit_based_proposals/` avec annotation Mathis dans le fichier proposal lui-même (`mathis_notes` field).\n")

    OUTPUT_FILE.write_text("\n".join(md))
    print(f"\nwrote {OUTPUT_FILE}")
    print(f"  accept: {verdict_counts['propose_accept']}")
    print(f"  defer:  {verdict_counts['propose_defer']}")
    print(f"  reject: {verdict_counts['propose_reject']}")


if __name__ == "__main__":
    main()
