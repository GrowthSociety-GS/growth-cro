"""V26.X.3 — Compresse les flow_summary steps en mergant les sub-actions
sur la même étape conceptuelle.

Problème (Mathis) : 147% d'inflation. Japhy quiz_vsl 18 steps "raw" mais
seulement ~11 vrais étapes UX (form_fill + Continuer + form_fill = 1 step).

Heuristique : fusionner les steps consécutifs ayant le même
`vision_action.current_step_label`. Vision a déjà détecté l'étape
conceptuelle, on s'appuie dessus.

Output :
  - Ajoute `compressed_steps` au flow_summary.json (liste de groupes)
  - Recalcule `n_steps_real` (vs len(steps) brut)
  - Préserve `steps` original (audit trail)

Format compressed_step :
{
  step: 1,                    # 1-indexed step UX
  step_label: "...",          # current_step_label (canonical)
  url: "...",                 # url at start
  sub_actions: [              # liste des actions exécutées sur cette étape
    {action, target, value, exec_strategy, raw_step_idx}
  ],
  primary_pattern: "...",     # selection_card | form_fill | nav (le 1er non-nav)
  screenshot_first: "...",    # screenshot du 1er sub-action
  dom_widgets_count: {...},   # widgets de la dernière sub-action (état final)
}

Usage :
    python3 skills/site-capture/scripts/compress_flow_steps.py --client japhy --page quiz_vsl
    python3 skills/site-capture/scripts/compress_flow_steps.py --all
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "captures"


def compress(steps: list[dict]) -> list[dict]:
    """Fusionne les steps consécutifs avec même current_step_label."""
    if not steps:
        return []
    groups: list[dict] = []
    cur: dict | None = None
    for raw_idx, s in enumerate(steps, 1):
        va = s.get("vision_action") or {}
        label = (va.get("current_step_label") or "").strip()
        if not cur or cur["step_label"] != label:
            # Démarrer un nouveau groupe
            if cur:
                groups.append(cur)
            cur = {
                "step": len(groups) + 1,
                "step_label": label or f"step_{raw_idx}",
                "url": s.get("url"),
                "sub_actions": [],
                "primary_pattern": None,
                "screenshot_first": s.get("screenshot"),
                "dom_widgets_count": s.get("dom_widgets_count") or {},
            }
        # Ajouter sub-action
        pat = va.get("pattern", "")
        cur["sub_actions"].append({
            "action": va.get("action"),
            "pattern": pat,
            "target": va.get("target_text") or va.get("target_input_name"),
            "value": va.get("value"),
            "exec_strategy": (s.get("exec_result") or {}).get("strategy"),
            "executed": (s.get("exec_result") or {}).get("executed"),
            "raw_step_idx": raw_idx,
            "screenshot": s.get("screenshot"),
        })
        # Pattern primary = 1er pattern non-nav
        if cur["primary_pattern"] is None and pat and pat != "nav":
            cur["primary_pattern"] = pat
        elif cur["primary_pattern"] is None:
            cur["primary_pattern"] = pat
        # Mettre à jour widgets count à la dernière sub-action (état final)
        cur["dom_widgets_count"] = s.get("dom_widgets_count") or cur["dom_widgets_count"]
    if cur:
        groups.append(cur)
    return groups


def process_one(fp: pathlib.Path) -> dict:
    d = json.loads(fp.read_text())
    steps = d.get("steps") or []
    compressed = compress(steps)
    d["compressed_steps"] = compressed
    d["n_steps_raw"] = len(steps)
    d["n_steps_real"] = len(compressed)
    fp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    return {"raw": len(steps), "real": len(compressed), "compression_ratio": (len(steps) - len(compressed)) / max(1, len(steps))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        n = 0
        total_raw = 0
        total_real = 0
        for fp in sorted(DATA.glob("*/*/flow/flow_summary.json")):
            if "_obsolete" in str(fp):
                continue
            r = process_one(fp)
            n += 1
            total_raw += r["raw"]
            total_real += r["real"]
            label = f"{fp.parent.parent.parent.name}/{fp.parent.parent.name}"
            if r["raw"] != r["real"]:
                print(f"  ✓ {label:32} {r['raw']:>3} → {r['real']:>3}")
        print(f"\n✓ {n} flows · {total_raw} raw → {total_real} real ({100*(total_raw-total_real)/max(1,total_raw):.1f}% compression)")
        return

    if not args.client or not args.page:
        ap.error("--client + --page OR --all")
    fp = DATA / args.client / args.page / "flow" / "flow_summary.json"
    if not fp.exists():
        print(f"❌ {fp} not found", file=sys.stderr)
        sys.exit(1)
    r = process_one(fp)
    print(f"✓ {args.client}/{args.page}: {r['raw']} raw → {r['real']} real")


if __name__ == "__main__":
    main()
