"""V26.A.2 — Post-process score_*.json files to attach Evidence Ledger entries.

Approach NON-INVASIVE : au lieu de refacto les 6 scripts score_*.py
(risque régression), ce script post-processe les fichiers déjà produits :

1. Pour chaque page captée
2. Lit chaque score_<pillar>.json existant
3. Pour chaque critère, crée un EvidenceLedgerItem reflétant la preuve
   utilisée (DOM selector si disponible, text observed depuis evidence,
   bbox depuis spatial signals, capture_hash sha256)
4. Attache `evidence_ids[]` aux critères dans score_*.json (in place atomic)
5. Applique aussi à recos_v13_final.json (chaque reco hérite des
   evidence_ids du critère qu'elle traite)

Usage :
    python3 enrich_scores_with_evidence.py --client japhy --page home
    python3 enrich_scores_with_evidence.py --all  # panel entier

Idempotent : peut tourner plusieurs fois sans dupliquer.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from evidence_ledger import EvidenceLedger, compute_capture_hash

PILLAR_FILES = [
    "score_hero.json", "score_persuasion.json", "score_ux.json",
    "score_coherence.json", "score_psycho.json", "score_tech.json",
    "score_utility_banner.json",
]

PILLAR_TO_PROMPT_VERSION = {
    "score_hero.json": "score_hero_v23",
    "score_persuasion.json": "score_persuasion_v23",
    "score_ux.json": "score_ux_v23",
    "score_coherence.json": "score_coherence_v23",
    "score_psycho.json": "score_psycho_v23",
    "score_tech.json": "score_tech_v23",
    "score_utility_banner.json": "score_utility_banner_v23",
}


def _find_screenshot(page_dir: pathlib.Path, viewport: str = "desktop") -> Optional[pathlib.Path]:
    candidates = [
        page_dir / "screenshots" / f"{viewport}_clean_fold.png",
        page_dir / "screenshots" / f"{viewport}_clean_full.png",
        page_dir / "screenshots" / f"{viewport}_asis_fold.png",
        page_dir / "screenshots" / f"spatial_fold_{viewport}.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _bbox_from_evidence(evidence: dict) -> Optional[dict]:
    """Extract bbox from evidence dict (looks for sp_*_bbox keys)."""
    for k, v in evidence.items():
        if k.endswith("_bbox") and isinstance(v, dict):
            if all(x in v for x in ("x", "y", "w", "h")):
                return v
            if all(x in v for x in ("x", "y", "width", "height")):
                return {"x": v["x"], "y": v["y"], "w": v["width"], "h": v["height"]}
    return None


def _dom_selector_from_criterion(criterion_id: str) -> Optional[str]:
    """Best-guess DOM selector for a criterion."""
    mapping = {
        "hero_01": "main h1, body > * h1:first-of-type",
        "hero_02": "main h1 + p, h1 + h2, [class*='subtitle']",
        "hero_03": "header [class*='cta'], main button, main a[class*='btn']",
        "hero_04": "main img, main [class*='hero'] img, picture",
        "hero_05": "main [class*='proof'], main [class*='trust'], main [class*='review']",
        "hero_06": "main > section:first-of-type",
        "per_01": "main h1, main p, main [class*='benefit']",
        "per_02": "main [class*='proof'], main [class*='testimon']",
        "per_05": "footer, main [class*='guarant'], main [class*='trust']",
        "ux_01": "header nav, [role='navigation']",
        "ux_05": "form, input, [role='form']",
        "tech_01": "html",
        "tech_05": "head meta, html",
    }
    return mapping.get(criterion_id)


def _text_from_evidence(evidence: dict) -> Optional[str]:
    """Pick the most informative text from evidence dict."""
    for k in ("h1", "h1_text", "subtitle", "subtitle_text", "primary_cta_text", "text", "label"):
        v = evidence.get(k)
        if isinstance(v, str) and len(v) > 3:
            return v[:300]
    # Search nested
    for v in evidence.values():
        if isinstance(v, dict):
            for k in ("text", "label", "h1", "subtitle"):
                vv = v.get(k)
                if isinstance(vv, str) and len(vv) > 3:
                    return vv[:300]
    return None


def enrich_page(client: str, page: str, viewport: str = "desktop") -> dict:
    """Enrich all score_*.json + recos_v13_final.json for one page with
    Evidence Ledger entries. Returns stats."""
    page_dir = CAPTURES / client / page
    if not page_dir.exists():
        return {"error": "page_dir_not_found"}

    el = EvidenceLedger(client, page, viewport)
    screenshot = _find_screenshot(page_dir, viewport)
    capture_hash = compute_capture_hash(screenshot) if screenshot else None
    screenshot_rel = f"screenshots/{screenshot.name}" if screenshot else None

    n_evidence_created = 0
    pillars_processed = []

    # 1. Process each pillar score file
    for pillar_file in PILLAR_FILES:
        f = page_dir / pillar_file
        if not f.exists():
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if "criteria" not in d:
            continue

        prompt_version = PILLAR_TO_PROMPT_VERSION.get(pillar_file, "score_v23")
        pillars_processed.append(pillar_file)

        for crit in d["criteria"]:
            cid = crit.get("id")
            if not cid:
                continue
            # Skip if already enriched (idempotency)
            if crit.get("evidence_ids"):
                continue

            evidence_dict = crit.get("evidence", {}) or {}
            text_observed = _text_from_evidence(evidence_dict)
            bbox = _bbox_from_evidence(evidence_dict)
            dom_sel = _dom_selector_from_criterion(cid)

            eid = el.add(
                source_type="hybrid_vision_dom" if (text_observed and bbox) else (
                    "vision" if text_observed else ("dom" if dom_sel else "rule_deterministic")
                ),
                dom_selector=dom_sel,
                text_observed=text_observed,
                bbox=bbox,
                screenshot_crop=screenshot_rel,
                capture_hash=capture_hash,
                model="claude-haiku-4-5-20251001",  # default — Vision Haiku produced perception
                prompt_version=prompt_version,
                confidence=0.85,  # default — could be refined per-criterion
                criterion_ref=cid,
                extra={
                    "score_observed": crit.get("score"),
                    "score_max": crit.get("max"),
                    "verdict": crit.get("verdict"),
                    "rationale_excerpt": (crit.get("rationale") or "")[:200],
                },
            )
            crit["evidence_ids"] = [eid]
            el.link(eid, score_file=pillar_file)
            n_evidence_created += 1

        # Atomic write back
        tmp = f.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        tmp.replace(f)

    # Flush ledger to disk
    el.flush()

    # 2. Process recos_v13_final.json — link reco to its criterion's evidence
    recos_file = page_dir / "recos_v13_final.json"
    n_recos_linked = 0
    if recos_file.exists():
        try:
            rd = json.loads(recos_file.read_text())
            # Build criterion → evidence_ids map from EL
            crit_to_evidence: dict[str, list[str]] = {}
            for it in el.items():
                cr = it.get("criterion_ref")
                if cr:
                    crit_to_evidence.setdefault(cr, []).append(it["evidence_id"])
            for r in rd.get("recos", []):
                cid = r.get("criterion_id")
                if cid and cid in crit_to_evidence and not r.get("evidence_ids"):
                    r["evidence_ids"] = crit_to_evidence[cid]
                    n_recos_linked += 1
            tmp = recos_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(rd, ensure_ascii=False, indent=2))
            tmp.replace(recos_file)
        except Exception as e:
            return {"error": f"recos_enrich_fail:{e}"}

    return {
        "client": client,
        "page": page,
        "viewport": viewport,
        "pillars_processed": pillars_processed,
        "evidence_created": n_evidence_created,
        "recos_linked": n_recos_linked,
        "ledger_total_items": len(el.items()),
        "screenshot_used": screenshot.name if screenshot else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--viewport", default="desktop")
    args = ap.parse_args()

    if args.all:
        # Iterate panel
        n = 0
        total_evidence = 0
        total_recos = 0
        for client_dir in sorted(CAPTURES.iterdir()):
            if not client_dir.is_dir() or client_dir.name.startswith("_") or client_dir.name.startswith("."):
                continue
            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir() or page_dir.name.startswith("_"):
                    continue
                if not (page_dir / "score_hero.json").exists():
                    continue
                res = enrich_page(client_dir.name, page_dir.name, args.viewport)
                if "error" not in res:
                    n += 1
                    total_evidence += res["evidence_created"]
                    total_recos += res["recos_linked"]
                    sys.stderr.write(".")
                    sys.stderr.flush()
        sys.stderr.write("\n")
        print(f"✓ Enriched {n} pages")
        print(f"  Evidence ledger entries created : {total_evidence}")
        print(f"  Recos linked to evidence         : {total_recos}")
    elif args.client and args.page:
        res = enrich_page(args.client, args.page, args.viewport)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("❌ Provide --client AND --page, or --all", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
