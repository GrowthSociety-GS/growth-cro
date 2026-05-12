#!/usr/bin/env python3
"""Architecture Explorer data extractor — single concern: YAML → JS bake.

Reads `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` (the source of truth
for the 251-module / 7-pipeline / 17-data_artefact GrowthCRO architecture) and
emits `deliverables/architecture-explorer-data.js` — a single JS file that
defines `window.ARCH = {...}` consumed by `deliverables/architecture-explorer.html`.

Idempotent: re-running on an unchanged YAML produces byte-identical JS output
(meta.generated_at is fixed at the YAML's own value, not regen time).

Companion: also reads the 6 Mermaid blocks from `WEBAPP_ARCHITECTURE_MAP.md`
and bakes them into the JS so the HTML can render them as tabs.
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / ".claude" / "docs" / "state" / "WEBAPP_ARCHITECTURE_MAP.yaml"
MD_PATH = ROOT / ".claude" / "docs" / "state" / "WEBAPP_ARCHITECTURE_MAP.md"
OUT_PATH = ROOT / "deliverables" / "architecture-explorer-data.js"


def _package_of(module_id: str) -> str:
    """Infer top-level package for grouping (growthcro / moteur_gsg / skills / ...)."""
    parts = module_id.split("/")
    if not parts:
        return "misc"
    head = parts[0]
    # growthcro/* groups
    if head == "growthcro" and len(parts) > 1:
        return f"growthcro/{parts[1]}"
    if head == "moteur_gsg" and len(parts) > 1:
        return f"moteur_gsg/{parts[1]}"
    if head == "skills" and len(parts) > 1:
        return f"skills/{parts[1]}"
    if head == "webapp" and len(parts) > 1:
        return f"webapp/{parts[1]}"
    return head


def _extract_mermaid_blocks(md_text: str) -> list[dict]:
    """Find every ```mermaid ... ``` block, paired with the nearest ## heading above."""
    blocks: list[dict] = []
    # Walk by line, track current section
    lines = md_text.splitlines()
    current_title = "Untitled"
    in_block = False
    buf: list[str] = []
    for line in lines:
        if line.startswith("## "):
            current_title = line[3:].strip()
        if line.strip() == "```mermaid" and not in_block:
            in_block = True
            buf = []
            continue
        if line.strip() == "```" and in_block:
            blocks.append({"title": current_title, "src": "\n".join(buf)})
            in_block = False
            buf = []
            continue
        if in_block:
            buf.append(line)
    return blocks


def _normalize_modules(modules_raw: dict) -> list[dict]:
    """Flatten + normalize the modules map into a list with stable IDs."""
    out: list[dict] = []
    for mod_id, payload in (modules_raw or {}).items():
        if not isinstance(payload, dict):
            continue
        out.append({
            "id": mod_id,
            "path": payload.get("path") or mod_id,
            "purpose": payload.get("purpose") or "",
            "inputs": payload.get("inputs") or [],
            "outputs": payload.get("outputs") or [],
            "depends_on": payload.get("depends_on") or [],
            "imported_by": payload.get("imported_by") or [],
            "doctrine_refs": payload.get("doctrine_refs") or [],
            "status": payload.get("status") or "active",
            "lifecycle_phase": payload.get("lifecycle_phase") or "runtime",
            "package": _package_of(mod_id),
        })
    return sorted(out, key=lambda m: m["id"])


def _normalize_pipelines(pipelines_raw: dict) -> list[dict]:
    out: list[dict] = []
    for pid, payload in (pipelines_raw or {}).items():
        if not isinstance(payload, dict):
            continue
        out.append({
            "id": pid,
            "description": payload.get("description") or "",
            "stages": payload.get("stages") or [],
            "entrypoint": payload.get("entrypoint") or "",
            "duration": payload.get("duration") or "",
            "status": payload.get("status") or "",
            "extra": {k: v for k, v in payload.items()
                      if k not in {"description", "stages", "entrypoint", "duration", "status"}},
        })
    return sorted(out, key=lambda p: p["id"])


def _normalize_artefacts(artefacts_raw: dict) -> list[dict]:
    out: list[dict] = []
    for aid, payload in (artefacts_raw or {}).items():
        if not isinstance(payload, dict):
            continue
        out.append({
            "id": aid,
            "producer": payload.get("producer") or "",
            "consumers": payload.get("consumers") or [],
            "schema": payload.get("schema") or "",
            "cardinality": payload.get("cardinality") or "",
            "extra": {k: v for k, v in payload.items()
                      if k not in {"producer", "consumers", "schema", "cardinality"}},
        })
    return sorted(out, key=lambda a: a["id"])


def _normalize_skills(skills_raw: dict) -> dict:
    """Pass through the skills_integration section, ensuring lists exist."""
    if not skills_raw:
        return {"combo_packs": {}, "essentials": [], "on_demand": [], "excluded": [],
                "anti_cacophonie_rules": []}
    return {
        "meta": skills_raw.get("meta") or {},
        "combo_packs": skills_raw.get("combo_packs") or {},
        "essentials": skills_raw.get("essentials") or [],
        "on_demand": skills_raw.get("on_demand") or [],
        "excluded": skills_raw.get("excluded") or [],
        "anti_cacophonie_rules": skills_raw.get("anti_cacophonie_rules") or [],
    }


def main() -> int:
    if not YAML_PATH.exists():
        print(f"ERROR: missing {YAML_PATH}", file=sys.stderr)
        return 1
    if not MD_PATH.exists():
        print(f"WARNING: missing {MD_PATH} — mermaid views will be empty", file=sys.stderr)

    data = yaml.safe_load(YAML_PATH.read_text())
    md_text = MD_PATH.read_text() if MD_PATH.exists() else ""

    payload = {
        "meta": data.get("meta") or {},
        "modules": _normalize_modules(data.get("modules") or {}),
        "pipelines": _normalize_pipelines(data.get("pipelines") or {}),
        "data_artefacts": _normalize_artefacts(data.get("data_artefacts") or {}),
        "skills_integration": _normalize_skills(data.get("skills_integration")),
        "mermaid_views": _extract_mermaid_blocks(md_text),
    }

    # Counts for the header KPIs
    payload["counts"] = {
        "modules": len(payload["modules"]),
        "pipelines": len(payload["pipelines"]),
        "data_artefacts": len(payload["data_artefacts"]),
        "essentials": len(payload["skills_integration"].get("essentials") or []),
        "on_demand": len(payload["skills_integration"].get("on_demand") or []),
        "excluded": len(payload["skills_integration"].get("excluded") or []),
        "mermaid_views": len(payload["mermaid_views"]),
    }

    # Group modules by package for sidebar
    by_package: dict[str, list[str]] = {}
    for m in payload["modules"]:
        by_package.setdefault(m["package"], []).append(m["id"])
    payload["modules_by_package"] = {k: sorted(v) for k, v in sorted(by_package.items())}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    js = "window.ARCH = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    OUT_PATH.write_text(js)

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} — "
          f"{payload['counts']['modules']} modules, "
          f"{payload['counts']['pipelines']} pipelines, "
          f"{payload['counts']['data_artefacts']} artefacts, "
          f"{payload['counts']['mermaid_views']} mermaid views, "
          f"{size_kb:.1f} KB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
