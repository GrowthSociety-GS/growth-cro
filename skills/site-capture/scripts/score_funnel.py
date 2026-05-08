#!/usr/bin/env python3
"""V21.H — Score le funnel COMPLET (vs juste l'intro).

Lit data/captures/<client>/<page>/flow/* (produit par capture_funnel_pipeline.py)
et calcule un score holistique du parcours :
  - funnel_01 : longueur appropriée (sweet spot 4-8 questions pour quiz)
  - funnel_02 : progress bar visible
  - funnel_03 : friction par step (champs requis vs optionnels)
  - funnel_04 : qualité du résultat (personnalisation visible)
  - funnel_05 : CTA finale claire (action concrète post-result)
  - funnel_06 : preuve sociale au long du flow
  - funnel_07 : recovery / save-state (peut-on revenir ?)

Output : data/captures/<client>/<page>/score_funnel.json

Usage : python3 score_funnel.py --client japhy --page quiz_vsl
        python3 score_funnel.py --all-funnels
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "captures"

PAGE_TYPE_TARGETS = {
    "quiz_vsl": {"min_steps": 3, "max_steps": 10, "ideal_steps": 6},
    "lp_leadgen": {"min_steps": 1, "max_steps": 5, "ideal_steps": 2},
    "lp_sales": {"min_steps": 1, "max_steps": 4, "ideal_steps": 2},
    "lead_gen_simple": {"min_steps": 1, "max_steps": 4, "ideal_steps": 2},
    "signup": {"min_steps": 1, "max_steps": 4, "ideal_steps": 2},
}


def score_funnel_01_length(steps_count: int, page_type: str) -> dict:
    """Longueur appropriée."""
    target = PAGE_TYPE_TARGETS.get(page_type, PAGE_TYPE_TARGETS["quiz_vsl"])
    ideal = target["ideal_steps"]
    if steps_count == 0:
        return {"score": 0, "max": 3, "verdict": "critical", "rationale": "Aucun step capturé — funnel inaccessible"}
    diff = abs(steps_count - ideal)
    if diff <= 1:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": f"Longueur idéale : {steps_count} steps (cible {ideal})"}
    if diff <= 3:
        return {"score": 2, "max": 3, "verdict": "ok", "rationale": f"Longueur acceptable : {steps_count} steps (cible {ideal})"}
    if steps_count > target["max_steps"]:
        return {"score": 1, "max": 3, "verdict": "warn", "rationale": f"Funnel trop long : {steps_count} steps — risque abandon"}
    return {"score": 1.5, "max": 3, "verdict": "warn", "rationale": f"Longueur à revoir : {steps_count} vs cible {ideal}"}


def score_funnel_02_progress(has_progress_bar: bool, n_steps: int) -> dict:
    """Progress bar visible."""
    if n_steps <= 1:
        return {"score": 1.5, "max": 3, "verdict": "ok", "rationale": "Funnel 1 step — progress bar non requise"}
    if has_progress_bar:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": "Progress bar détectée — visiteur sait où il en est"}
    return {"score": 0.5, "max": 3, "verdict": "critical", "rationale": "Pas de progress bar visible — friction cognitive"}


def score_funnel_03_friction(steps: list) -> dict:
    """Friction par step (champs requis)."""
    if not steps:
        return {"score": 0, "max": 3, "verdict": "critical", "rationale": "Pas de steps"}
    avg_inputs = sum(s.get("inputs", 0) for s in steps) / max(len(steps), 1)
    avg_radios = sum(s.get("radios", 0) for s in steps) / max(len(steps), 1)
    avg_options = sum(s.get("options", 0) + s.get("checks", 0) for s in steps) / max(len(steps), 1)

    # Friction model: text inputs > radio/checkbox in cognitive load
    friction_index = avg_inputs * 2 + avg_radios * 0.3 + avg_options * 0.5

    if friction_index < 1.0:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": f"Friction faible (idx {friction_index:.2f}) — clicks rapides"}
    if friction_index < 2.0:
        return {"score": 2, "max": 3, "verdict": "ok", "rationale": f"Friction acceptable (idx {friction_index:.2f})"}
    if friction_index < 4.0:
        return {"score": 1, "max": 3, "verdict": "warn", "rationale": f"Friction élevée (idx {friction_index:.2f}) — beaucoup de saisie"}
    return {"score": 0.5, "max": 3, "verdict": "critical", "rationale": f"Friction très élevée (idx {friction_index:.2f})"}


def score_funnel_04_result_quality(result_reached: bool, halt_reason: str | None) -> dict:
    """Qualité du résultat (atteint vs halté)."""
    if result_reached:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": "Page résultat atteinte — funnel complet"}
    if halt_reason == "no_next_button":
        return {"score": 1, "max": 3, "verdict": "warn", "rationale": "Funnel halté — heuristique n'a pas trouvé bouton next (interaction custom probable)"}
    if halt_reason == "max_steps_reached":
        return {"score": 1.5, "max": 3, "verdict": "warn", "rationale": "Funnel >max steps — possiblement trop long"}
    return {"score": 0.5, "max": 3, "verdict": "critical", "rationale": f"Funnel non complété : {halt_reason or 'unknown'}"}


def score_funnel_05_final_cta(steps: list, result_reached: bool) -> dict:
    """CTA finale présente (action concrète post-result)."""
    if not result_reached:
        return {"score": 0, "max": 3, "verdict": "critical", "rationale": "Pas de result page → CTA finale non vérifiable"}
    # Look at the last step
    last = steps[-1] if steps else {}
    body = (last.get("bodyText") or "").lower()
    cta_keywords = ["commander", "acheter", "essayer", "découvrir mon", "voir mon", "accéder", "buy", "purchase", "try", "see my", "view my", "access"]
    has_cta = any(k in body for k in cta_keywords)
    if has_cta:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": "CTA finale détectée sur page résultat"}
    return {"score": 1, "max": 3, "verdict": "warn", "rationale": "Pas de CTA action post-résultat clair"}


def score_funnel_06_proof_in_flow(steps: list) -> dict:
    """Preuve sociale visible le long du flow (rassurance)."""
    proof_keywords = ["clients", "utilisateurs", "users", "avis", "reviews", "trustpilot", "★", "garanti", "guarantee", "secure"]
    pages_with_proof = sum(
        1 for s in steps
        if any(k in (s.get("bodyText") or "").lower() for k in proof_keywords)
    )
    if pages_with_proof == 0:
        return {"score": 0.5, "max": 3, "verdict": "critical", "rationale": "Aucune preuve sociale dans le flow — risque drop-off"}
    ratio = pages_with_proof / max(len(steps), 1)
    if ratio >= 0.5:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": f"Preuve sociale présente sur {pages_with_proof}/{len(steps)} steps"}
    return {"score": 2, "max": 3, "verdict": "ok", "rationale": f"Preuve sociale partielle ({pages_with_proof}/{len(steps)} steps)"}


def score_funnel_07_recovery(steps: list) -> dict:
    """Recovery / save-state — bouton retour, sauvegarde progression."""
    progress_with_back = sum(
        1 for s in steps
        if "retour" in (s.get("progressText") or "").lower() or "back" in (s.get("progressText") or "").lower()
    )
    if progress_with_back >= len(steps) * 0.6:
        return {"score": 3, "max": 3, "verdict": "top", "rationale": "Bouton retour visible sur la majorité des steps"}
    if progress_with_back > 0:
        return {"score": 2, "max": 3, "verdict": "ok", "rationale": "Bouton retour partiellement visible"}
    return {"score": 1, "max": 3, "verdict": "warn", "rationale": "Pas de bouton retour détecté — pas de recovery"}


def score_funnel(client: str, page: str) -> dict | None:
    flow_dir = DATA_DIR / client / page / "flow"
    if not flow_dir.exists():
        return None
    summary_path = flow_dir / "flow_summary.json"
    if not summary_path.exists():
        return None
    try:
        summary = json.load(open(summary_path))
    except Exception:
        return None

    steps = summary.get("steps") or []
    aggregate = summary.get("aggregate") or {}
    has_progress_bar = aggregate.get("hasProgressBar", False)
    result_reached = summary.get("resultReached", False)
    halt_reason = summary.get("haltReason")
    # V26.X.3 : utiliser n_steps_real (compressed) au lieu de len(steps) raw
    # n_steps_real fusionne form_fill + Continuer sur même current_step_label
    n_real = summary.get("n_steps_real") or len(steps)

    # Run scorers
    criteria = []
    criteria.append({"id": "funnel_01_length", **score_funnel_01_length(n_real, page)})
    criteria.append({"id": "funnel_02_progress", **score_funnel_02_progress(has_progress_bar, n_real)})
    criteria.append({"id": "funnel_03_friction", **score_funnel_03_friction(steps)})
    criteria.append({"id": "funnel_04_result", **score_funnel_04_result_quality(result_reached, halt_reason)})
    criteria.append({"id": "funnel_05_final_cta", **score_funnel_05_final_cta(steps, result_reached)})
    criteria.append({"id": "funnel_06_proof", **score_funnel_06_proof_in_flow(steps)})
    criteria.append({"id": "funnel_07_recovery", **score_funnel_07_recovery(steps)})

    raw_total = sum(c["score"] for c in criteria)
    raw_max = sum(c["max"] for c in criteria)
    score100 = round(100 * raw_total / raw_max, 1) if raw_max else 0

    out = {
        "version": "V21.H",
        "client": client,
        "page": page,
        "rawTotal": round(raw_total, 2),
        "rawMax": raw_max,
        "score100": score100,
        "criteria": criteria,
        "flow_meta": {
            "steps_captured": len(steps),       # raw : sub-actions
            "n_steps_real": n_real,              # vrais steps UX (compressed)
            "result_reached": result_reached,
            "halt_reason": halt_reason,
            "has_progress_bar": has_progress_bar,
        },
    }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client")
    parser.add_argument("--page")
    parser.add_argument("--all-funnels", action="store_true")
    args = parser.parse_args()

    targets = []
    if args.all_funnels:
        for cd in sorted(DATA_DIR.iterdir()):
            if not cd.is_dir() or cd.name.startswith(("_", ".")):
                continue
            for pd in sorted(cd.iterdir()):
                if pd.is_dir() and (pd / "flow" / "flow_summary.json").exists():
                    targets.append((cd.name, pd.name))
    elif args.client and args.page:
        targets.append((args.client, args.page))
    else:
        parser.error("--all-funnels OR (--client + --page)")

    ok = 0
    for c, p in targets:
        result = score_funnel(c, p)
        if result is None:
            print(f"  ⚠️  {c}/{p}: no flow data")
            continue
        out_path = DATA_DIR / c / p / "score_funnel.json"
        with open(out_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        ok += 1
        print(f"  ✓ {c}/{p}: score100={result['score100']}% (steps={result['flow_meta']['steps_captured']}, reached={result['flow_meta']['result_reached']})")

    print(f"\n═══ Summary: {ok}/{len(targets)} funnels scored ═══")


if __name__ == "__main__":
    main()
