"""audit_capabilities.py V26.AC Sprint E — système anti-oubli auto-discovery.

Réponse au constat Mathis 2026-05-04 : "j'en ai marre que t'oublies tout, va
falloir un système imparable pour rien oublier".

Ce script scan le repo et produit `CAPABILITIES_REGISTRY.json` qui liste
TOUTES les capacités du projet (skills, scripts, moteurs, data outputs)
avec leur état de branchement (ACTIVE / ORPHANED_FROM_GSG / ORPHANED_FROM_AUDIT
/ DEPRECATED).

Le but : avant tout sprint code GSG, on regarde le registry. On voit ce qui
existe DÉJÀ et qu'on a oublié de brancher. Plus jamais "j'ai recodé un voice
extractor parce que j'ai oublié qu'on l'avait" ou "j'ai oublié AURA".

Pipeline :
  1. Walk skills/, scripts/, moteur_*/ → liste tous les .py
  2. Pour chaque .py : extraire docstring (1ère triple-quote) + imports
  3. Cross-reference : qui import qui (graph imports)
  4. Walk data/captures/<client>/<page_type>/ → types de .json artefacts
  5. Cross-reference avec EXPECTED_GSG_CONSUMERS (ce que le GSG DEVRAIT consume)
  6. Output CAPABILITIES_REGISTRY.json + .claude/docs/state/CAPABILITIES_SUMMARY.md (Mathis review)

Usage :
    python3 scripts/audit_capabilities.py
    python3 scripts/audit_capabilities.py --diff  # diff vs registry précédent
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
from collections import defaultdict
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "CAPABILITIES_REGISTRY.json"
SUMMARY_PATH = ROOT / ".claude" / "docs" / "state" / "CAPABILITIES_SUMMARY.md"

# Folders à scanner pour .py
SCAN_FOLDERS = [
    "skills/site-capture/scripts",
    "skills/growth-site-generator/scripts",
    "skills/cro-auditor",
    "skills/cro-library",
    "skills/gsg",
    "skills/client-context-manager",
    "skills/audit-bridge-to-gsg",
    "skills/mode-1-launcher",
    "skills/webapp-publisher",
    "scripts",
    "moteur_gsg/orchestrator.py",
    "moteur_gsg/core",
    "moteur_gsg/modes",
    "moteur_multi_judge/orchestrator.py",
    "moteur_multi_judge/judges",
]

# Folders ARCHIVE (à ignorer pour le registry actif)
ARCHIVE_FOLDERS = ["_archive", "_roadmap_v27", "__pycache__"]

# Files that mention capabilities to document or validate them, without being
# runtime consumers. Counting these as consumers makes the anti-oubli registry
# falsely optimistic.
CONSUMER_IGNORE_PATHS = {
    "scripts/audit_capabilities.py",
    "moteur_gsg/core/canonical_registry.py",
}

# Some registry/adapter files mention legacy script filenames to document policy,
# not because they execute them. Keep actual adapter wrappers counted, but avoid
# marking policy-only entries as wired.
CONSUMER_IGNORE_IMPORTS_BY_PATH = {
    "moteur_gsg/core/legacy_lab_adapters.py": {
        "aura_compute",
        "aura_extract",
        "gsg_best_of_n",
        "gsg_generate_lp",
        "gsg_humanlike_audit",
        "gsg_multi_judge",
        "gsg_pipeline_sequential",
    },
}

# Capacités que le GSG DEVRAIT consommer (mapping cible)
EXPECTED_GSG_CONSUMERS = {
    "aura_compute.py": ["moteur_gsg/modes/", "moteur_gsg/core/"],
    "aura_extract.py": ["moteur_gsg/modes/", "moteur_gsg/core/"],
    "brand_dna_extractor.py": ["moteur_gsg/core/brand_intelligence.py"],  # ✓ déjà
    "brand_dna_diff_extractor.py": ["moteur_gsg/core/brand_intelligence.py"],  # ✓ déjà
    "design_grammar.py": ["moteur_gsg/modes/"],  # branché OPT-IN
    "creative_director.py": ["moteur_gsg/core/legacy_lab_adapters.py", "moteur_gsg/modes/"],  # branché OPT-IN via adapter
    "golden_design_bridge.py": ["moteur_gsg/core/legacy_lab_adapters.py"],  # branché via adapter, prompt block à structurer
    "fix_html_runtime.py": ["moteur_gsg/core/legacy_lab_adapters.py", "moteur_gsg/core/pipeline_single_pass.py"],  # ✓ via adapter
    "vision_spatial.py": ["moteur_gsg/core/"],
    "perception_v13.py": ["moteur_gsg/core/"],
    "intent_detector_v13.py": ["moteur_gsg/core/"],
    "enrich_v143_public.py": ["moteur_gsg/core/"],
    "evidence_ledger.py": ["moteur_gsg/core/"],
    "doctrine.py": ["moteur_gsg/core/prompt_assembly.py", "moteur_multi_judge/judges/doctrine_judge.py"],
    "score_hero.py": ["moteur_multi_judge/"],
    "reco_enricher_v13_api.py": ["moteur_gsg/core/"],
}

# V26.AC Sprint H : capacités consummées via OUTPUT JSON (pas import direct)
# → router racine `client_context.py` charge ces outputs au runtime
# Le registry doit les considérer ACTIVE (pas orphan HIGH)
INDIRECTLY_WIRED_VIA_OUTPUT = {
    "aura_compute.py": "outputs `data/_aura_<client>.json` + `aura_tokens.json` consumed by client_context.load_client_context() via _load_aura()",
    "aura_extract.py": "supports aura_compute pipeline",
    "vision_spatial.py": "outputs `spatial_v9.json` consumed by client_context._load_spatial()",
    "perception_v13.py": "outputs `perception_v13.json` consumed by client_context._load_perception()",
    "intent_detector_v13.py": "outputs `client_intent.json` consumed by client_context._load_intent()",
    "evidence_ledger.py": "outputs `evidence_ledger.json` consumed by client_context._load_evidence()",
    "design_grammar.py": "outputs `design_grammar/tokens.css + tokens.json + ...` consumed by mode_1_persona_narrator._load_tokens_css() + client_context._load_design_grammar()",
    "reco_enricher_v13_api.py": "outputs `recos_v13_final.json` consumed by client_context._load_recos_final()",
    "enrich_v143_public.py": "outputs `clients_database.json.v143.*` consumed by client_context._load_v143()",
    "score_hero.py": "outputs `score_hero.json` consumed by client_context._load_score_pillars() + doctrine_judge",
    "score_persuasion.py": "idem score_hero pattern",
    "score_ux.py": "idem",
    "score_coherence.py": "idem",
    "score_psycho.py": "idem",
    "score_tech.py": "idem",
    "score_utility_banner.py": "idem",
    "score_page_type.py": "outputs `score_page_type.json` orchestrateur final",
    "playwright_capture_v2.py": "outputs `capture.json` + `screenshots/*.png` consumed by client_context",
    "brand_dna_extractor.py": "outputs `brand_dna.json` consumed by client_context._load_brand_dna()",
    "brand_dna_diff_extractor.py": "outputs `brand_dna.diff.*` consumed via brand_dna",
}

# Data artefacts (per-client/page) que le GSG devrait consume
EXPECTED_GSG_DATA_INPUTS = {
    "brand_dna.json": "ACTIVE — GenerationContextPack + design_tokens + brand_intelligence",
    "design_grammar/tokens.json": "ACTIVE_PARTIAL — GenerationContextPack/design_tokens; deeper component grammar still to wire",
    "screenshots/desktop_clean_fold.png": "ACTIVE — GenerationContextPack + Mode 1 controlled renderer visual_assets hero",
    "screenshots/mobile_clean_fold.png": "ACTIVE — GenerationContextPack + Mode 1 controlled renderer visual_assets hero",
    "screenshots/desktop_clean_full.png": "ACTIVE_CONTEXT_ONLY — inventoried by GenerationContextPack; not yet a component-planning input",
    "screenshots/mobile_clean_full.png": "ACTIVE_CONTEXT_ONLY — inventoried by GenerationContextPack; not yet a component-planning input",
    "perception_v13.json": "ACTIVE_CONTEXT_ONLY — loaded by client_context and surfaced in GenerationContextPack design_sources; not yet decisive",
    "spatial_v9.json": "ACTIVE_CONTEXT_ONLY — loaded by client_context and surfaced in GenerationContextPack design_sources; not yet decisive",
    "score_page_type.json": "USED Mode 2 REPLACE only (gaps audit)",
    "recos_v13_final.json": "ACTIVE_CONTEXT_ONLY / MODE2 — loaded by client_context; Mode 2 dependency, not Mode 1 driver",
    "evidence_ledger.json": "ACTIVE_PARTIAL — proof inventory in GenerationContextPack; deeper evidence gating still to wire",
    "client_intent.json": "ACTIVE — audience/objective context via GenerationContextPack",
    "aura_tokens.json": "ACTIVE_PARTIAL — design_tokens consumes AURA with VisualIntelligencePack input; full aura_compute migration pending",
}


def _is_archived(path: pathlib.Path) -> bool:
    return any(part in ARCHIVE_FOLDERS for part in path.parts)


def _extract_docstring(filepath: pathlib.Path) -> str:
    try:
        text = filepath.read_text(errors="ignore")
    except Exception:
        return ""
    # Match """docstring""" or '''docstring''' first triple-quote block
    m = re.search(r'^[^"\']*?("""|\'\'\')(.*?)\1', text, re.DOTALL | re.MULTILINE)
    if m:
        doc = m.group(2).strip()
        # Take first paragraph or up to 250 chars
        first_para = doc.split("\n\n")[0].strip()
        return first_para[:300]
    return ""


def _extract_imports(filepath: pathlib.Path) -> list[str]:
    """Liste les modules importés (relatifs ou absolus depuis ROOT).

    V26.AD : détecte aussi les string-based dispatch `"module.path:func"`
    utilisés par les orchestrateurs (importlib dynamique) — sinon les modes
    branchés via `_MODE_REGISTRY` apparaissent comme orphelins à tort.
    """
    try:
        text = filepath.read_text(errors="ignore")
    except Exception:
        return []
    imports = set()
    for m in re.finditer(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', text, re.MULTILINE):
        mod = m.group(1) or m.group(2)
        if mod and not mod.startswith(("os", "sys", "json", "re", "pathlib", "time", "typing", "collections", "argparse", "anthropic", "concurrent", "importlib")):
            imports.add(mod.split(".")[0])
            # capture the LAST segment too — used for module-name-as-id matching
            last = mod.rsplit(".", 1)[-1]
            if last and last != mod.split(".")[0]:
                imports.add(last)

    # V26.AD — string-based dynamic dispatch ("module.path:func_name")
    for m in re.finditer(r'["\']([\w_]+(?:\.[\w_]+)+):[\w_]+["\']', text):
        dotted = m.group(1)
        last_seg = dotted.rsplit(".", 1)[-1]
        if last_seg:
            imports.add(last_seg)
        first_seg = dotted.split(".")[0]
        if first_seg and first_seg not in {"os", "sys", "json", "re", "pathlib"}:
            imports.add(first_seg)

    # V26.AD+ — importlib.util.spec_from_file_location() with module name OR .py filename
    # Pattern : spec_from_file_location("module_name", path_var_or_string)
    for m in re.finditer(r'spec_from_file_location\s*\(\s*["\']([\w_]+)["\']', text):
        imports.add(m.group(1))
    # Pattern : direct file ref `... / "filename.py"` (loader pattern)
    for m in re.finditer(r'["\']([\w_]+)\.py["\']', text):
        imports.add(m.group(1))

    return sorted(imports)


def scan_python_files() -> list[dict]:
    """Walk tous les .py actifs (hors archive)."""
    results = []
    for folder in SCAN_FOLDERS:
        target = ROOT / folder
        if not target.exists():
            continue
        if target.is_file() and target.suffix == ".py":
            files = [target]
        else:
            files = sorted(target.rglob("*.py"))
        for f in files:
            if _is_archived(f):
                continue
            rel = f.relative_to(ROOT)
            results.append({
                "id": f.stem,
                "path": str(rel),
                "filename": f.name,
                "what": _extract_docstring(f),
                "imports": _extract_imports(f),
                "size_bytes": f.stat().st_size,
                "mtime": time.strftime("%Y-%m-%d", time.localtime(f.stat().st_mtime)),
            })
    return results


def build_consumed_by_graph(files: list[dict]) -> dict[str, list[str]]:
    """Retourne dict[capability_id, list[paths qui l'importent]]."""
    consumed_by = defaultdict(set)
    for f in files:
        if f["path"] in CONSUMER_IGNORE_PATHS:
            continue
        ignored_imports = CONSUMER_IGNORE_IMPORTS_BY_PATH.get(f["path"], set())
        for imp in f["imports"]:
            if imp in ignored_imports:
                continue
            consumed_by[imp].add(f["path"])
    return {k: sorted(v) for k, v in consumed_by.items()}


def detect_data_artefacts(client_sample: str = "weglot") -> dict:
    """Liste les types de .json/png artefacts disponibles dans un client échantillon."""
    cd = ROOT / "data" / "captures" / client_sample
    if not cd.exists():
        return {}
    artefacts = defaultdict(list)
    for f in cd.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            relname = f.relative_to(cd)
            ext = f.suffix
            artefacts[ext].append(str(relname))
    return {k: sorted(v) for k, v in artefacts.items()}


def determine_status(filename: str, path: str, consumed_by: list[str], imports: list[str]) -> tuple[str, str]:
    """Détermine status (ACTIVE/ORPHANED/PARTIAL) + criticality.

    V26.AC Sprint H : check INDIRECTLY_WIRED_VIA_OUTPUT pour détecter les
    capacités consummées via leur output JSON (pas via import direct).
    """
    expected = EXPECTED_GSG_CONSUMERS.get(filename)
    indirect_note = INDIRECTLY_WIRED_VIA_OUTPUT.get(filename)

    if expected is None:
        if not consumed_by:
            # Pas d'imports directs MAIS peut-être consummé via output
            if indirect_note:
                return ("ACTIVE_INDIRECT_VIA_OUTPUT", "low")
            return ("POTENTIALLY_ORPHANED", "review_needed")
        return ("ACTIVE", "low")

    expected_paths_norm = [e.rstrip("/") for e in expected]
    actually_wired = any(
        any(c.startswith(ep) or ep in c for ep in expected_paths_norm)
        for c in consumed_by
    )

    if actually_wired:
        return ("ACTIVE_WIRED_AS_EXPECTED", "ok")
    if indirect_note:
        # Pas d'import direct mais output JSON consummé → ACTIVE
        return ("ACTIVE_INDIRECT_VIA_OUTPUT", "ok")
    if consumed_by:
        return ("PARTIAL — wired elsewhere not GSG", "medium")
    return ("ORPHANED_FROM_GSG — should be wired", "HIGH")


def build_registry() -> dict:
    files = scan_python_files()
    consumed_by = build_consumed_by_graph(files)
    data_artefacts = detect_data_artefacts("weglot")

    capabilities = []
    for f in files:
        cb = consumed_by.get(f["id"], [])
        status, crit = determine_status(f["filename"], f["path"], cb, f["imports"])
        cap = {
            **f,
            "consumed_by": cb,
            "status": status,
            "criticality": crit,
        }
        # Si dans EXPECTED_GSG_CONSUMERS, ajoute "should_be_consumed_by"
        expected = EXPECTED_GSG_CONSUMERS.get(f["filename"])
        if expected:
            cap["should_be_consumed_by"] = expected
        capabilities.append(cap)

    # Stats globales
    stats = {
        "total_files": len(capabilities),
        "active_wired": sum(1 for c in capabilities if c["status"] == "ACTIVE_WIRED_AS_EXPECTED"),
        "active_indirect": sum(1 for c in capabilities if c["status"] == "ACTIVE_INDIRECT_VIA_OUTPUT"),
        "active_misc": sum(1 for c in capabilities if c["status"] == "ACTIVE"),
        "orphaned_from_gsg_HIGH": sum(1 for c in capabilities if c["criticality"] == "HIGH"),
        "partial_wired": sum(1 for c in capabilities if "PARTIAL" in c["status"]),
        "potentially_orphaned": sum(1 for c in capabilities if c["status"] == "POTENTIALLY_ORPHANED"),
    }

    return {
        "version": "v1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stats": stats,
        "capabilities": sorted(capabilities, key=lambda c: (
            0 if c["criticality"] == "HIGH" else (1 if c["criticality"] == "medium" else 2),
            c["filename"]
        )),
        "data_artefacts_per_client_sample_weglot": data_artefacts,
        "expected_gsg_data_inputs": EXPECTED_GSG_DATA_INPUTS,
        "_doctrine": (
            "Cette registry est la SOURCE DE VÉRITÉ des capacités existantes. "
            "Avant tout sprint code GSG/audit : `python3 scripts/audit_capabilities.py` "
            "puis lire .claude/docs/state/CAPABILITIES_SUMMARY.md. Si une capacité critique 'ORPHANED_FROM_GSG' "
            "pertinente pour le sprint à venir, OBLIGATION de soit la brancher soit "
            "expliquer pourquoi on la skip."
        ),
    }


def render_summary_md(registry: dict) -> str:
    lines = [
        f"# Capabilities Summary — {registry['generated_at']}",
        "",
        "**Source de vérité** : `CAPABILITIES_REGISTRY.json` (auto-généré par `scripts/audit_capabilities.py`).",
        "",
        "## Stats globales",
        "",
    ]
    for k, v in registry["stats"].items():
        lines.append(f"- **{k}** : {v}")

    # Section ORPHELINS HIGH PRIORITY
    lines.append("")
    lines.append("## 🔴 ORPHELINS critiques (HIGH priority — à brancher au GSG)")
    lines.append("")
    lines.append("| Filename | Path | What | Should be consumed by |")
    lines.append("|---|---|---|---|")
    high_orphans = [c for c in registry["capabilities"] if c["criticality"] == "HIGH"]
    for c in high_orphans:
        what = (c.get("what") or "").replace("|", "/").replace("\n", " ")[:120]
        should = ", ".join(c.get("should_be_consumed_by", []))
        lines.append(f"| `{c['filename']}` | {c['path']} | {what} | {should} |")

    # Section ACTIFS WIRED
    lines.append("")
    lines.append("## ✅ Actifs branchés correctement")
    lines.append("")
    active = [c for c in registry["capabilities"] if c["status"] == "ACTIVE_WIRED_AS_EXPECTED"]
    for c in active:
        what = (c.get("what") or "").replace("|", "/").replace("\n", " ")[:100]
        lines.append(f"- `{c['filename']}` — {what}")

    # Section PARTIAL (branché ailleurs mais pas GSG)
    lines.append("")
    lines.append("## ⚠️ Branchés ailleurs mais PAS au GSG")
    lines.append("")
    partial = [c for c in registry["capabilities"] if "PARTIAL" in c["status"]]
    for c in partial:
        what = (c.get("what") or "").replace("|", "/").replace("\n", " ")[:100]
        cb = ", ".join(c.get("consumed_by", []))[:200]
        lines.append(f"- `{c['filename']}` — {what} (consumé par : {cb})")

    # Section data artefacts orphelins
    lines.append("")
    lines.append("## 📊 Data artefacts disponibles (Weglot sample)")
    lines.append("")
    lines.append("| Artefact path | Status (GSG perspective) |")
    lines.append("|---|---|")
    for path, status in registry["expected_gsg_data_inputs"].items():
        lines.append(f"| `{path}` | {status} |")

    # Reminder doctrine
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🛡️ Doctrine anti-oubli")
    lines.append("")
    lines.append(registry["_doctrine"])
    lines.append("")
    lines.append("**Pour Claude (sub-agents et conv principal)** : avant tout sprint code GSG/audit :")
    lines.append("1. Lire ce fichier")
    lines.append("2. Si capacité 'ORPHANED_FROM_GSG' HIGH dans le scope du sprint → branchement obligatoire OU justification écrite")
    lines.append("3. Pas de 'code from scratch' sans avoir grep le registry pour vérifier que ça n'existe pas déjà")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", action="store_true", help="Show diff vs previous registry")
    args = ap.parse_args()

    print("\n══ AUDIT CAPABILITIES — auto-discovery V26.AC ══\n")
    registry = build_registry()

    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2))
    SUMMARY_PATH.write_text(render_summary_md(registry))

    print(f"  Files scanned       : {registry['stats']['total_files']}")
    print(f"  Active wired direct : {registry['stats']['active_wired']}")
    print(f"  Active indirect via output : {registry['stats']['active_indirect']} ⭐ V26.AC")
    print(f"  Active misc         : {registry['stats']['active_misc']}")
    print(f"  🔴 Orphans HIGH     : {registry['stats']['orphaned_from_gsg_HIGH']}")
    print(f"  ⚠️ Partial wired     : {registry['stats']['partial_wired']}")
    print(f"  Potentially orph    : {registry['stats']['potentially_orphaned']}")
    print(f"\n  ✓ Saved : CAPABILITIES_REGISTRY.json")
    print(f"  ✓ Saved : .claude/docs/state/CAPABILITIES_SUMMARY.md")
    print(f"\n  → Read .claude/docs/state/CAPABILITIES_SUMMARY.md to see what's orphaned + what should be wired.")


if __name__ == "__main__":
    main()
