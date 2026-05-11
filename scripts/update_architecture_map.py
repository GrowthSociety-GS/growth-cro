#!/usr/bin/env python3
"""AST scan generator for WEBAPP_ARCHITECTURE_MAP.yaml — preserves human-curated fields between regens.

Walks the active code roots (growthcro/, moteur_gsg/, moteur_multi_judge/,
skills/, scripts/) and produces the canonical machine-readable architecture
map. For every Python source file it extracts:

    - the module docstring's first non-empty line (default `purpose`)
    - the top-level imports (project-local edges -> `depends_on`)
    - the top-level classes / functions (informational, not serialized for v1)

A reverse pass over the import graph populates `imported_by`. The YAML is
loaded back before write so any human-curated `purpose`, `inputs`, `outputs`,
`doctrine_refs`, `status`, `lifecycle_phase` survive subsequent regens. Only
`depends_on` and `imported_by` are unconditionally refreshed from AST.

The script is stdlib-only at scan time; PyYAML is required only when reading
or writing the YAML payload. Exit 0 on success, 1 on AST failure, 2 on YAML
serialization failure. ≤ 800 LOC, mono-concern (YAML regeneration), no env
access (no `growthcro.config` needed — this is meta-tooling).

Usage:
    python3 scripts/update_architecture_map.py
    python3 scripts/update_architecture_map.py --dry-run
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    print(f"PyYAML required: {exc}", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_YAML = ROOT / ".claude" / "docs" / "state" / "WEBAPP_ARCHITECTURE_MAP.yaml"

# Roots scanned for module entries. Order matters for stable output.
SCAN_ROOTS: tuple[str, ...] = (
    "growthcro",
    "moteur_gsg",
    "moteur_multi_judge",
    "skills/site-capture/scripts",
    "skills/growth-site-generator/scripts",
    "scripts",
    "SCHEMA",
)

# Per-root lifecycle defaults — overridable per-module via human curation.
ROOT_LIFECYCLE: dict[str, str] = {
    "growthcro/config": "infrastructure",
    "growthcro/lib": "infrastructure",
    "growthcro/api": "infrastructure",
    "growthcro/cli": "onboarding",
    "growthcro/capture": "runtime",
    "growthcro/perception": "runtime",
    "growthcro/scoring": "runtime",
    "growthcro/recos": "runtime",
    "growthcro/research": "onboarding",
    "growthcro/gsg_lp": "runtime",
    "moteur_gsg": "runtime",
    "moteur_multi_judge": "qa",
    "skills/site-capture": "runtime",
    "skills/growth-site-generator": "runtime",
    "scripts": "infrastructure",
    "SCHEMA": "infrastructure",
}

EXCLUDE_DIRS = {"__pycache__", "_archive", "_obsolete", ".git", ".venv"}


# ────────────────────────────────────────────────────────────────────────────
# 1. Filesystem walk + AST extraction
# ────────────────────────────────────────────────────────────────────────────


def _iter_python_files() -> list[Path]:
    """Walk SCAN_ROOTS, returning all active .py files sorted by path."""
    files: list[Path] = []
    for root_str in SCAN_ROOTS:
        root_path = ROOT / root_str
        if not root_path.exists():
            continue
        if root_path.is_file() and root_path.suffix == ".py":
            files.append(root_path)
            continue
        for p in sorted(root_path.rglob("*.py")):
            if any(part in EXCLUDE_DIRS for part in p.parts):
                continue
            if "deprecated" in p.name.lower():
                continue
            files.append(p)
    return files


def _module_key(path: Path) -> str:
    """Return the canonical module key for a .py file (e.g. `growthcro/capture/scorer`)."""
    rel = path.relative_to(ROOT)
    # Trim trailing .py
    parts = list(rel.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    # Drop __init__ leaves so `growthcro/capture/__init__.py` -> `growthcro/capture`
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return "/".join(parts)


def _extract_module_info(path: Path) -> tuple[str, list[str], list[str], list[str]]:
    """Parse a .py file and return (docstring_first_line, imports, classes, functions).

    On AST failure, the file is skipped (caller logs). Returns empty fields if
    the file is empty / parse error.
    """
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ("", [], [], [])
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return ("", [], [], [])

    docstring = ast.get_docstring(tree) or ""
    first_line = ""
    for raw in docstring.splitlines():
        stripped = raw.strip()
        if stripped:
            first_line = stripped
            break

    imports: list[str] = []
    classes: list[str] = []
    functions: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:  # relative import
                # mark with leading dot — handled by graph normalizer
                mod = "." * node.level + mod
            imports.append(mod)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            functions.append(node.name)

    return (first_line, imports, classes, functions)


# ────────────────────────────────────────────────────────────────────────────
# 2. Import-graph normalization + reverse edges
# ────────────────────────────────────────────────────────────────────────────


def _normalize_import(mod: str, source_key: str) -> str | None:
    """Resolve a raw import string to a canonical module key, or None if external.

    Project-local prefixes: `growthcro.*`, `moteur_gsg.*`, `moteur_multi_judge.*`.
    Relative imports (`.foo`) are resolved against the source module's package.
    Skill scripts use bare module names — resolved via lookup table.
    """
    if not mod:
        return None
    # Relative imports — resolve against the source's package
    if mod.startswith("."):
        leading = len(mod) - len(mod.lstrip("."))
        rest = mod.lstrip(".")
        source_parts = source_key.split("/")
        anchor = source_parts[: max(0, len(source_parts) - leading)]
        if rest:
            anchor.extend(rest.split("."))
        return "/".join(anchor) if anchor else None
    # Absolute project package
    if mod.startswith(("growthcro.", "moteur_gsg.", "moteur_multi_judge.")):
        return mod.replace(".", "/")
    if mod in {"growthcro", "moteur_gsg", "moteur_multi_judge"}:
        return mod
    # External / stdlib — out of map scope
    return None


def _build_graph(
    files: list[Path],
) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    """Return (per-module info, reverse-edge map).

    `info[key]` keys: `path` (relative), `_doc` (docstring 1st line), `depends_on`.
    `imported_by[key]` is built by inverting `depends_on`.
    """
    info: dict[str, dict[str, Any]] = {}
    imported_by: dict[str, set[str]] = defaultdict(set)

    keys_seen: set[str] = set()
    for path in files:
        key = _module_key(path)
        if not key:
            continue
        keys_seen.add(key)
        doc, imports, _classes, _funcs = _extract_module_info(path)
        info[key] = {
            "path": str(path.relative_to(ROOT)),
            "_doc": doc,
            "_raw_imports": imports,
        }

    # Second pass — normalize imports against the known key set
    for key, meta in info.items():
        depends_on: list[str] = []
        for raw in meta["_raw_imports"]:
            norm = _normalize_import(raw, key)
            if not norm:
                continue
            # Try direct match, then prefix match (e.g. `growthcro/lib/anthropic_client.foo`
            # may not exist but `growthcro/lib/anthropic_client` does)
            if norm in info and norm != key:
                depends_on.append(norm)
                imported_by[norm].add(key)
            else:
                # Try walking up the import path
                parts = norm.split("/")
                while parts:
                    candidate = "/".join(parts)
                    if candidate in info and candidate != key:
                        if candidate not in depends_on:
                            depends_on.append(candidate)
                            imported_by[candidate].add(key)
                        break
                    parts.pop()
        meta["depends_on"] = sorted(set(depends_on))

    return info, imported_by


# ────────────────────────────────────────────────────────────────────────────
# 3. Lifecycle / status defaults from path
# ────────────────────────────────────────────────────────────────────────────


def _infer_lifecycle(module_key: str) -> str:
    """Pick a sensible lifecycle phase from the module path."""
    for prefix, phase in ROOT_LIFECYCLE.items():
        if module_key.startswith(prefix):
            return phase
    return "runtime"


def _infer_status(module_key: str) -> str:
    """Default to `active`; `legacy` for skills/growth-site-generator (legacy lab adapter only).

    Human curation in the YAML overrides this.
    """
    if module_key.startswith("skills/growth-site-generator/scripts"):
        return "legacy"
    return "active"


# ────────────────────────────────────────────────────────────────────────────
# 4. YAML preservation of human-curated fields
# ────────────────────────────────────────────────────────────────────────────

# Fields refreshed on every regen
AUTO_FIELDS = {"path", "depends_on", "imported_by"}
# Fields preserved from prior YAML if present
HUMAN_FIELDS = {"purpose", "inputs", "outputs", "doctrine_refs", "status", "lifecycle_phase"}


def _load_existing_yaml() -> dict[str, Any]:
    if not OUTPUT_YAML.exists():
        return {}
    try:
        with OUTPUT_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        print(f"Warning: existing YAML unreadable, starting fresh ({exc})", file=sys.stderr)
        return {}
    return data if isinstance(data, dict) else {}


def _build_module_entry(
    key: str,
    info_entry: dict[str, Any],
    imported_by: set[str],
    existing: dict[str, Any],
) -> dict[str, Any]:
    """Merge AST-derived data with human-curated fields."""
    prior = existing.get(key, {}) if isinstance(existing.get(key), dict) else {}
    entry: dict[str, Any] = {
        "path": info_entry["path"],
        "purpose": prior.get("purpose") or info_entry["_doc"] or "TBD — fill purpose",
        "inputs": prior.get("inputs", []),
        "outputs": prior.get("outputs", []),
        "depends_on": info_entry["depends_on"],
        "imported_by": sorted(imported_by),
        "doctrine_refs": prior.get("doctrine_refs", []),
        "status": prior.get("status", _infer_status(key)),
        "lifecycle_phase": prior.get("lifecycle_phase", _infer_lifecycle(key)),
    }
    return entry


# ────────────────────────────────────────────────────────────────────────────
# 5. Static sections (data_artefacts + pipelines) — kept curated by Mathis
# ────────────────────────────────────────────────────────────────────────────


def _default_data_artefacts() -> dict[str, Any]:
    """Seed `data_artefacts:` block. Preserved across regens once written."""
    return {
        "data/captures/<client>/<page>/capture.json": {
            "producer": "growthcro/capture/scorer",
            "consumers": [
                "growthcro/perception/persist",
                "growthcro/scoring/persist",
                "skills/site-capture/scripts/multi_judge",
            ],
            "schema": "SCHEMA/score_pillar.schema.json (capture is upstream of pillar scores)",
            "cardinality": "1 per client per page",
        },
        "data/captures/<client>/<page>/spatial_v9.json": {
            "producer": "growthcro/capture/orchestrator (via spatial_v9.js DOM payload)",
            "consumers": ["growthcro/perception/persist", "growthcro/perception/heuristics"],
            "schema": "implicit — sections / bbox / hierarchy",
            "cardinality": "1 per client per page",
        },
        "data/captures/<client>/<page>/perception_v13.json": {
            "producer": "growthcro/perception/persist",
            "consumers": [
                "growthcro/scoring/persist",
                "growthcro/recos/orchestrator",
                "skills/site-capture/scripts/perception_bridge",
            ],
            "schema": "SCHEMA/perception_v13.schema.json",
            "cardinality": "1 per client per page",
        },
        "data/captures/<client>/<page>/score_{hero,persuasion,ux,coherence,psycho,tech}.json": {
            "producer": "growthcro/scoring/persist + growthcro/scoring/ux + legacy skills/score_*.py",
            "consumers": ["growthcro/recos/orchestrator", "growthcro/scoring/cli"],
            "schema": "SCHEMA/score_pillar.schema.json",
            "cardinality": "6 per client per page",
        },
        "data/captures/<client>/<page>/score_page_type.json": {
            "producer": "growthcro/scoring/persist + growthcro/scoring/specific/*",
            "consumers": ["growthcro/recos/orchestrator"],
            "schema": "SCHEMA/score_page_type.schema.json",
            "cardinality": "1 per client per page",
        },
        "data/captures/<client>/<page>/recos_enriched.json": {
            "producer": "growthcro/recos/orchestrator",
            "consumers": [
                "skills/site-capture/scripts/build_growth_audit_data",
                "growthcro/api/server",
            ],
            "schema": "SCHEMA/recos_enriched.schema.json",
            "cardinality": "1 per client per page",
        },
        "data/captures/<client>/<page>/evidence_ledger.json": {
            "producer": "skills/site-capture/scripts/evidence_ledger",
            "consumers": ["growthcro/recos/orchestrator", "deliverables/GrowthCRO-V27-CommandCenter.html"],
            "schema": "implicit — evidence per criterion",
            "cardinality": "1 per client per page",
        },
        "data/captures/<client>/brand_dna.json": {
            "producer": "skills/site-capture/scripts/brand_dna_extractor",
            "consumers": ["moteur_gsg/core/brand_intelligence", "moteur_gsg/core/context_pack"],
            "schema": "implicit — palette / typography / voice / proof",
            "cardinality": "1 per client",
        },
        "data/captures/<client>/design_grammar/*": {
            "producer": "skills/site-capture/scripts/design_grammar",
            "consumers": ["moteur_gsg/core/design_grammar_loader", "moteur_gsg/core/design_tokens"],
            "schema": "implicit — V30 design tokens",
            "cardinality": "1 per client (multi-file)",
        },
        "data/captures/<client>/client_intent.json": {
            "producer": "growthcro/perception/intent + skills/site-capture/scripts/intent_detector_v13",
            "consumers": ["growthcro/recos/prompts", "moteur_gsg/core/context_pack"],
            "schema": "implicit — intent matrix",
            "cardinality": "1 per client",
        },
        "data/captures/<client>/discovered_pages_v25.json": {
            "producer": "skills/site-capture/scripts/discover_pages_v25",
            "consumers": ["growthcro/cli/enrich_client", "growthcro/research/discovery"],
            "schema": "implicit — sitemap-style page inventory",
            "cardinality": "1 per client",
        },
        "data/clients_database.json": {
            "producer": "growthcro/cli/add_client + skills/webapp-publisher",
            "consumers": [
                "growthcro/api/server",
                "skills/site-capture/scripts/build_growth_audit_data",
            ],
            "schema": "SCHEMA/clients_database.schema.json",
            "cardinality": "1 (global)",
        },
        "deliverables/growth_audit_data.js": {
            "producer": "skills/site-capture/scripts/build_growth_audit_data",
            "consumers": ["deliverables/GrowthCRO-V27-CommandCenter.html"],
            "schema": "SCHEMA/dashboard_v17_data.schema.json",
            "cardinality": "1 (global)",
        },
        "data/learning/audit_based_proposals/*.json": {
            "producer": "skills/site-capture/scripts/learning_layer_v29_audit_based",
            "consumers": ["playbook/* (Mathis review)"],
            "schema": "implicit — 69 proposals V29",
            "cardinality": "1 per proposal (currently 69)",
        },
        "data/_pipeline_runs/<run-id>/multi_judge.json": {
            "producer": "moteur_multi_judge/orchestrator",
            "consumers": ["scripts/run_gsg_full_pipeline", "Mathis review"],
            "schema": "implicit — final_score_pct + doctrine + humanlike + killers",
            "cardinality": "1 per GSG run",
        },
        "data/_briefs_v2/<timestamp>_<client>_<page_type>_<run>.json": {
            "producer": "moteur_gsg/core/brief_v2 + brief_v2_prefiller",
            "consumers": ["moteur_gsg/orchestrator", "moteur_gsg/modes/*"],
            "schema": "implicit — BriefV2 contract",
            "cardinality": "1 per GSG intake",
        },
    }


def _default_pipelines() -> dict[str, Any]:
    """Seed `pipelines:` block. Preserved once written."""
    return {
        "audit_pipeline": {
            "stages": [
                "discovery (growthcro/research/discovery)",
                "capture (growthcro/capture/orchestrator → spatial_v9 + capture.json + page.html)",
                "perception (growthcro/perception/persist → perception_v13.json)",
                "scoring (growthcro/scoring/persist + scoring/specific/* → score_*.json)",
                "evidence (skills/site-capture/scripts/evidence_ledger → evidence_ledger.json)",
                "recos (growthcro/recos/orchestrator → recos_enriched.json)",
                "lifecycle (skills/site-capture/scripts/reco_lifecycle)",
            ],
            "entrypoint": "python -m growthcro.cli.capture_full <url> <client>",
            "duration": "< 5min per client (target)",
        },
        "gsg_pipeline": {
            "stages": [
                "intake_wizard (moteur_gsg/core/intake_wizard)",
                "brief_v2 (moteur_gsg/core/brief_v2 + prefiller + validator)",
                "context_pack (moteur_gsg/core/context_pack)",
                "doctrine_pack (moteur_gsg/core/doctrine_planner)",
                "visual_intelligence (moteur_gsg/core/visual_intelligence)",
                "creative_route_selector V27.2-F (moteur_gsg/core/creative_route_selector)",
                "visual_system V27.2-G (moteur_gsg/core/visual_system)",
                "page_plan (moteur_gsg/core/planner + component_library)",
                "copy_llm (moteur_gsg/core/copy_writer — JSON slots only)",
                "controlled_renderer (moteur_gsg/core/page_renderer_orchestrator)",
                "qa_runtime (moteur_gsg/core/minimal_guards)",
                "minimal_gates (moteur_gsg/modes/mode_1/visual_gates + runtime_fixes)",
                "multi_judge_optional (moteur_multi_judge/orchestrator)",
            ],
            "entrypoint": "python -m moteur_gsg.orchestrator --mode <complete|replace|extend|elevate|genesis>",
            "duration": "< 3min lite, < 8min with multi-judge",
        },
        "multi_judge": {
            "stages": [
                "doctrine_judge V3.2.1 (moteur_multi_judge/judges/doctrine_judge)",
                "humanlike_judge (moteur_multi_judge/judges/humanlike_judge)",
                "implementation_check (moteur_multi_judge/judges/implementation_check)",
            ],
            "invocation": "post-GSG QA, post-audit verification",
            "weighting": "70% doctrine / 30% humanlike (V26.AA Sprint 3)",
        },
        "reality_loop": {
            "stages": [
                "reality_layer collect (credentials GA4/Meta/Google/Shopify/Clarity — pending)",
                "experiment_engine A/B (skills/site-capture/scripts/experiment_engine)",
                "learning_v29_audit_based (skills/site-capture/scripts/learning_layer_v29_audit_based — 69 proposals)",
                "learning_v30_data_driven (pending — Bayesian update from reality)",
            ],
            "status": "partially active — V29 audit-based YES, Reality+Experiment+V30 PENDING credentials + 3 pilot clients",
        },
        "webapp": {
            "stages_v27_html": [
                "growthcro/cli/capture_full per-client run",
                "skills/site-capture/scripts/build_growth_audit_data consolidates data/captures/* → deliverables/growth_audit_data.js",
                "deliverables/GrowthCRO-V27-CommandCenter.html consumes the JS bundle",
            ],
            "stages_v28_nextjs_target": [
                "growthcro/api/server FastAPI exposed via Vercel edge functions",
                "5 microfrontends: audit-app, reco-app, gsg-studio, reality-monitor, learning-lab",
                "Supabase EU region (auth + tables clients/audits/recos/runs + realtime)",
            ],
            "status": "V27 HTML active (12MB growth_audit_data.js, 56 clients, 185 pages); V28 Next.js 0% — Epic #6",
        },
    }


# ────────────────────────────────────────────────────────────────────────────
# 6. Top-level YAML assembly
# ────────────────────────────────────────────────────────────────────────────


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return out.stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def _assemble_yaml(
    info: dict[str, dict[str, Any]],
    imported_by: dict[str, set[str]],
    existing: dict[str, Any],
) -> dict[str, Any]:
    # Modules: preserve human-curated fields per entry, refresh AST-derived ones.
    existing_modules = existing.get("modules", {}) if isinstance(existing.get("modules"), dict) else {}
    modules: dict[str, Any] = {}
    for key in sorted(info.keys()):
        modules[key] = _build_module_entry(key, info[key], imported_by.get(key, set()), existing_modules)

    # data_artefacts / pipelines: keep existing if present (curated), else seed defaults.
    existing_artefacts = existing.get("data_artefacts")
    data_artefacts = existing_artefacts if isinstance(existing_artefacts, dict) else _default_data_artefacts()

    existing_pipelines = existing.get("pipelines")
    pipelines = existing_pipelines if isinstance(existing_pipelines, dict) else _default_pipelines()

    return {
        "meta": {
            "version": "1.0.0",
            "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "source_commit": _git_head(),
            "generated_by": "scripts/update_architecture_map.py",
            "notes": (
                "Modules section auto-refreshed (path, depends_on, imported_by). "
                "purpose/inputs/outputs/doctrine_refs/status/lifecycle_phase are "
                "human-curated and preserved across regens."
            ),
        },
        "modules": modules,
        "data_artefacts": data_artefacts,
        "pipelines": pipelines,
    }


# ────────────────────────────────────────────────────────────────────────────
# 7. Custom YAML dumper for deterministic, diff-friendly output
# ────────────────────────────────────────────────────────────────────────────


class _ArchMapDumper(yaml.SafeDumper):
    """SafeDumper that disables alias re-use (keeps diffs local)."""

    def ignore_aliases(self, data: Any) -> bool:  # noqa: D401, ARG002
        return True


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    # Force plain style for short strings, fold-block (`>-`) is avoided for diff-friendliness.
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_ArchMapDumper.add_representer(str, _represent_str)


def _write_yaml(payload: dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        yaml.dump(
            payload,
            f,
            Dumper=_ArchMapDumper,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=120,
        )


# ────────────────────────────────────────────────────────────────────────────
# 8. CLI
# ────────────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="Compute the YAML payload, do not write")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_YAML,
        help="Override the output path (default: .claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    files = _iter_python_files()
    if not files:
        print("No Python files found in SCAN_ROOTS — abort.", file=sys.stderr)
        return 1

    try:
        info, imported_by = _build_graph(files)
    except (SyntaxError, ValueError) as exc:
        print(f"AST parse error: {exc}", file=sys.stderr)
        return 1

    existing = _load_existing_yaml()
    payload = _assemble_yaml(info, imported_by, existing)

    if args.dry_run:
        print(yaml.dump(payload["meta"], sort_keys=False, allow_unicode=True))
        print(f"# would write {len(payload['modules'])} modules to {args.output}")
        return 0

    try:
        _write_yaml(payload, args.output)
    except (OSError, yaml.YAMLError) as exc:
        print(f"YAML write failed: {exc}", file=sys.stderr)
        return 2

    print(
        f"Wrote {args.output.relative_to(ROOT)} — "
        f"{len(payload['modules'])} modules, "
        f"{len(payload['data_artefacts'])} data artefact patterns, "
        f"{len(payload['pipelines'])} pipelines."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
