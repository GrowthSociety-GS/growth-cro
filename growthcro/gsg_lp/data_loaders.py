"""Data loaders for the GSG mega-prompt pipeline.

Each helper is a thin wrapper around a file read or a subprocess call:

  * ``load_brand_dna(client)``       — reads ``data/captures/<client>/brand_dna.json``,
                                       hard-fails on absence (caller has to handle).
  * ``load_design_grammar(client)``  — soft-loads up to 6 design_grammar V30
                                       JSON files; returns ``{}`` for clients
                                       without a ``design_grammar/`` directory.
  * ``compute_aura_tokens(...)``     — subprocess to ``aura_compute.py``
                                       (mode B fixé V26.Y.2). Hard-fails on
                                       non-zero exit.
  * ``golden_bridge_prompt(vector)`` — subprocess to ``golden_design_bridge.py``
                                       returning the prompt block (string).
  * ``auto_fix_runtime(html, ...)``  — V26.Z P0 adapter on top of
                                       ``fix_html_runtime.fix_html_runtime``.

Split from ``gsg_generate_lp.py`` (issue #8). Path constants ``ROOT``,
``DATA``, ``SCRIPTS`` live here as the single source of truth.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "captures"
SCRIPTS = ROOT / "skills" / "growth-site-generator" / "scripts"

# Make sibling scripts importable (creative_director, fix_html_runtime,
# gsg_pipeline_sequential, gsg_multi_judge, …)
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


# V26.Z P0 — fix_html_runtime is in scripts/, may not exist in test envs.
try:
    from fix_html_runtime import fix_html_runtime, detect_runtime_bugs  # noqa: F401
    _RUNTIME_FIX_AVAILABLE = True
except ImportError:
    _RUNTIME_FIX_AVAILABLE = False


def auto_fix_runtime(html: str, label: str = "", verbose: bool = True) -> tuple[str, dict]:
    """V26.Z P0 — applique fix_html_runtime() automatiquement après une génération.

    Toujours injecte le JS fallback (counter + reveal) si nécessaire.
    Toujours patch CSS direct si reveal pattern détecté.

    Returns: (fixed_html, report) — report contient before/after broken_score
    pour traçabilité.
    """
    if not _RUNTIME_FIX_AVAILABLE:
        return html, {"skipped": "fix_html_runtime not importable"}

    fixed_html, report = fix_html_runtime(html, inject_js=True, fix_reveal_pattern=True)
    before = report["before"]
    after = report["after"]
    if verbose:
        if before["broken_score"] > 0.0:
            print(f"  [P0 auto-fix{f' {label}' if label else ''}] "
                  f"broken_score: {before['broken_score']} ({before['broken_severity']}) "
                  f"→ {after['broken_score']} ({after['broken_severity']})", flush=True)
            if report.get("fixed_counters"):
                print(f"    fixed counters: {report['fixed_counters']}", flush=True)
            if report.get("fixed_reveal_pairs"):
                print(f"    fixed reveal pairs: {report['fixed_reveal_pairs']}", flush=True)
            if report.get("injected_js"):
                print(f"    injected runtime JS fallback (counter + reveal)", flush=True)
        else:
            print(f"  [P0 auto-fix{f' {label}' if label else ''}] no rendering bugs detected", flush=True)
    return fixed_html, report


def load_brand_dna(client: str) -> dict:
    """Load ``data/captures/<client>/brand_dna.json`` or sys.exit on miss."""
    fp = DATA / client / "brand_dna.json"
    if not fp.exists():
        sys.exit(f"❌ {fp} not found. Run brand_dna_extractor first.")
    return json.loads(fp.read_text())


def load_design_grammar(client: str) -> dict:
    """Load les 7 fichiers prescriptifs design_grammar V30 d'un client.

    V26.Z W2 : ces fichiers étaient générés pour 51 clients mais JAMAIS lus
    par le générateur (faille découverte dans l'audit post-V26.Y). Ce loader
    + render_design_grammar_block() les injecte enfin dans le mega-prompt.

    Retourne dict vide si client n'a pas de design_grammar/ (graceful fallback).
    """
    dg_dir = DATA / client / "design_grammar"
    if not dg_dir.is_dir():
        return {}
    grammar = {}
    for json_file in ("composition_rules.json", "section_grammar.json",
                      "component_grammar.json", "brand_forbidden_patterns.json",
                      "quality_gates.json", "tokens.json"):
        fp = dg_dir / json_file
        if fp.exists():
            try:
                grammar[json_file.replace(".json", "")] = json.loads(fp.read_text())
            except json.JSONDecodeError:
                pass
    return grammar


def compute_aura_tokens(client: str, energy: float, tonality: float,
                         business: str, registre: str) -> dict:
    """Lance aura_compute en mode B fixé."""
    bd_fp = DATA / client / "brand_dna.json"
    out_fp = ROOT / "data" / f"_aura_{client}.json"
    cmd = [
        "python3", str(SCRIPTS / "aura_compute.py"),
        "--brand-dna", str(bd_fp),
        "--energy", str(energy),
        "--tonality", str(tonality),
        "--business", business,
        "--registre", registre,
        "--output", str(out_fp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(f"❌ aura_compute failed: {r.stderr}")
    return json.loads(out_fp.read_text())


def golden_bridge_prompt(vector: dict, top: int = 5) -> str:
    """Lance golden_design_bridge.py et retourne le prompt block."""
    cmd = [
        "python3", str(SCRIPTS / "golden_design_bridge.py"),
        "--vector", json.dumps(vector),
        "--top", str(top),
        "--prompt",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        return f"(golden bridge failed: {r.stderr})"
    # Strip first line "Loaded N profiles..." if present
    out = r.stdout
    lines = out.split("\n")
    return "\n".join(l for l in lines if not l.startswith("Loaded "))


__all__ = [
    "ROOT",
    "DATA",
    "SCRIPTS",
    "auto_fix_runtime",
    "load_brand_dna",
    "load_design_grammar",
    "compute_aura_tokens",
    "golden_bridge_prompt",
]
