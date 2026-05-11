#!/usr/bin/env python3
"""
state.py — Auto-diagnostic GrowthCRO
─────────────────────────────────────
Lance ce script en 1re action de chaque nouvelle conversation Claude pour
connaître l'état réel du projet au moment T. Pas de mémoire, pas de cache :
la vérité vient du disque.

Usage :
    python3 state.py                    # dump complet
    python3 state.py --clients          # juste les clients
    python3 state.py --pipeline         # juste l'état pipeline
    python3 state.py --recent           # fichiers modifiés dans les 48h
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
CAPTURES = DATA / "captures"
SCRIPTS = ROOT / "skills" / "site-capture" / "scripts"
PLAYBOOK = ROOT / "playbook"

# ─────────────────────────────────────────────────────────────
# Pipeline stages (ordre canonique)
# ─────────────────────────────────────────────────────────────
PIPELINE_STAGES = [
    ("capture",       "capture.json",         "ghost_capture.js → batch_spatial_capture.py"),
    ("spatial_v9",    "spatial_v9.json",      "spatial_v9.js (via batch_spatial_capture)"),
    ("perception",    "perception_v13.json",  "python -m growthcro.perception.cli --all"),
    ("intent",        "client_intent.json",   "intent_detector_v13.py --all (per client)"),
    ("score_pillars", "score_hero.json",      "batch_rescore.py (6 piliers)"),
    ("score_page",    "score_page_type.json", "score_page_type.py <label> <pageType>"),
    ("recos_prep",    "recos_v13_prompts.json", "python -m growthcro.recos.cli prepare --all"),
    ("recos_api",     "recos_v13_final.json",   "python -m growthcro.recos.cli enrich --all (Sonnet)"),
]

def _count_stage(filename: str) -> int:
    return sum(1 for _ in CAPTURES.rglob(filename))

def _list_clients() -> list[dict]:
    try:
        db = json.loads((DATA / "clients_database.json").read_text(encoding="utf-8"))
    except Exception as e:
        return [{"error": f"clients_database.json: {e}"}]
    return db.get("clients", [])

def _scripts_status() -> list[dict]:
    out = []
    for p in sorted(SCRIPTS.glob("*.py")):
        if p.name.startswith("_") or p.name == "__init__.py":
            continue
        stat = p.stat()
        out.append({
            "name": p.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    for p in sorted(SCRIPTS.glob("*.js")):
        stat = p.stat()
        out.append({
            "name": p.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return out

def _playbooks_status() -> list[dict]:
    out = []
    for p in sorted(PLAYBOOK.glob("*.json")):
        stat = p.stat()
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            version = d.get("version") or d.get("doctrineVersion") or "–"
            status = d.get("status") or "–"
        except Exception:
            version, status = "–", "err"
        out.append({
            "name": p.name,
            "version": str(version)[:30],
            "status": str(status)[:15],
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
        })
    return out

def _recent_mods(hours: int = 48) -> list[dict]:
    cutoff = datetime.now() - timedelta(hours=hours)
    results = []
    for base in [SCRIPTS, PLAYBOOK, ROOT]:
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(seg in p.parts for seg in ("archive", "__pycache__", "node_modules", ".git")):
                continue
            mt = datetime.fromtimestamp(p.stat().st_mtime)
            if mt >= cutoff:
                results.append({
                    "path": str(p.relative_to(ROOT)),
                    "mtime": mt.strftime("%Y-%m-%d %H:%M"),
                })
    return sorted(results, key=lambda r: r["mtime"], reverse=True)[:40]

def _pipeline_state() -> list[dict]:
    rows = []
    for key, filename, producer in PIPELINE_STAGES:
        n = _count_stage(filename)
        rows.append({"stage": key, "file": filename, "count": n, "producer": producer})
    return rows

def _clients_summary():
    clients = _list_clients()
    captured = {p.parent.name if p.parent.parent == CAPTURES else p.parent.parent.name
                for p in CAPTURES.rglob("capture.json")}
    n_total = len(clients)
    n_captured = sum(1 for c in clients if c.get("id") in captured)
    return n_total, n_captured, captured

# ─────────────────────────────────────────────────────────────
# Rendering
# ─────────────────────────────────────────────────────────────
def _hr(title: str = ""):
    print()
    print("─" * 72)
    if title:
        print(f"  {title}")
        print("─" * 72)

def render_pipeline():
    _hr("PIPELINE STATE (count files on disk)")
    print(f"{'stage':<15} {'count':>6}   {'producer'}")
    for row in _pipeline_state():
        print(f"{row['stage']:<15} {row['count']:>6}   {row['producer']}")

def render_clients():
    _hr("CLIENTS")
    n_total, n_captured, captured = _clients_summary()
    print(f"Total clients in clients_database.json : {n_total}")
    print(f"Clients avec au moins 1 capture        : {n_captured}")
    print(f"Clients manquants (pas capturés)       : {n_total - n_captured}")
    # show missing
    clients = _list_clients()
    missing = [c.get("id") for c in clients if c.get("id") not in captured][:20]
    if missing:
        print(f"Sample missing: {missing}")

def render_scripts():
    _hr("SCRIPTS (skills/site-capture/scripts/)")
    rows = _scripts_status()
    print(f"{'script':<38} {'size':>7}  mtime")
    for r in rows:
        print(f"{r['name']:<38} {r['size_kb']:>6}k  {r['mtime']}")

def render_playbooks():
    _hr("PLAYBOOKS")
    rows = _playbooks_status()
    print(f"{'file':<42} {'version':<22} {'status':<12} mtime")
    for r in rows:
        print(f"{r['name']:<42} {r['version']:<22} {r['status']:<12} {r['mtime']}")

def render_recent():
    _hr("FICHIERS MODIFIÉS (dernières 48h)")
    for r in _recent_mods():
        print(f"  {r['mtime']}   {r['path']}")

def render_header():
    print(f"GrowthCRO state — {datetime.now().strftime('%Y-%m-%d %H:%M')}  — root: {ROOT.name}")

def render_hint():
    _hr("NEXT STEPS — lit toujours .claude/docs/reference/GROWTHCRO_MANIFEST.md avant d'agir")
    print("  1. cat .claude/docs/reference/GROWTHCRO_MANIFEST.md   # architecture cascade")
    print("  2. cat .claude/memory/MEMORY.md                       # index mémoires")
    print("  3. python3 state.py --recent             # ce qui a bougé récemment")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clients",  action="store_true")
    ap.add_argument("--pipeline", action="store_true")
    ap.add_argument("--scripts",  action="store_true")
    ap.add_argument("--playbook", action="store_true")
    ap.add_argument("--recent",   action="store_true")
    args = ap.parse_args()

    render_header()

    any_flag = any([args.clients, args.pipeline, args.scripts, args.playbook, args.recent])
    if not any_flag:
        render_pipeline()
        render_clients()
        render_playbooks()
        render_recent()
        render_hint()
        return

    if args.pipeline: render_pipeline()
    if args.clients:  render_clients()
    if args.scripts:  render_scripts()
    if args.playbook: render_playbooks()
    if args.recent:   render_recent()

if __name__ == "__main__":
    main()
