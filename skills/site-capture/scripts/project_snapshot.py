#!/usr/bin/env python3
"""
project_snapshot.py — GrowthCRO V12 état complet du projet.

Produit 4 artefacts synchronisés à chaque appel :
  1. STATE.md          — arborescence, schéma de l'outil, interconnexions
  2. ARCHITECTURE.md   — flux de données, dépendances entre modules
  3. BACKLOG.md        — historique todo + à faire (source de vérité unique)
  4. .claude/memory/snapshots/YYYY-MM-DD_HH-MM.json — snapshot machine-readable

Usage :
    python skills/site-capture/scripts/project_snapshot.py
    python skills/site-capture/scripts/project_snapshot.py --note "P0.1 intégration layer 2 done"
    python skills/site-capture/scripts/project_snapshot.py --phase "P1.2" --status "in_progress"

Le snapshot est idempotent : à chaque appel, il régénère tout à partir de
l'état réel du repo (glob + read playbook + read scripts + read memory).
Il NE stocke PAS d'état manuel — tout est dérivé du filesystem.

BACKLOG.md est le SEUL fichier qui accumule de l'historique humain
(cases cochées, dates, notes). Le script le met à jour en append-only
sans écraser les notes existantes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter, OrderedDict
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[3]
PLAYBOOK = ROOT / "playbook"
SCRIPTS = ROOT / "skills" / "site-capture" / "scripts"
DATA_CAP = ROOT / "data" / "captures"
MEM_DIR = ROOT / ".claude" / "memory"
SNAPSHOTS_DIR = MEM_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# ───────────────────────── Version / meta ───────────────────────────────

VERSION = "1.0.0"
NOW = datetime.utcnow().isoformat() + "Z"


# ───────────────────────── Playbook audit ───────────────────────────────

def audit_blocs() -> dict:
    """Lit les 6 blocs V3 et extrait les métriques clés."""
    out = {}
    files = {
        "hero": "bloc_1_hero_v3.json",
        "persuasion": "bloc_2_persuasion_v3.json",
        "ux": "bloc_3_ux_v3.json",
        "coherence": "bloc_4_coherence_v3.json",
        "psycho": "bloc_5_psycho_v3.json",
        "tech": "bloc_6_tech_v3.json",
    }
    for pillar, fname in files.items():
        p = PLAYBOOK / fname
        if not p.exists():
            out[pillar] = {"status": "MISSING", "file": fname}
            continue
        d = json.loads(p.read_text())
        crits = d.get("criteria", []) or []
        killers_top = d.get("killers", []) or []
        killers_in_crits = [c for c in crits if c.get("killer")]
        vp = sum(1 for c in crits if "viewport" in str(c).lower())
        bcw = d.get("businessCategoryWeighting")
        ptw = d.get("pageTypeWeights")
        _killer_ids_union = sorted(
            {c.get("id") for c in killers_in_crits}
            | {k.get("criterionId") or k.get("id") for k in killers_top if isinstance(k, dict)}
        )
        out[pillar] = {
            "file": fname,
            "version": d.get("version"),
            "max": d.get("max"),
            "criteria_count": len(crits),
            "criteria_ids": [c.get("id") for c in crits],
            "killers_count": len(_killer_ids_union),
            "killers_ids": _killer_ids_union,
            "viewport_check_coverage": f"{vp}/{len(crits)}",
            "has_bcw": bool(bcw),
            "bcw_categories": list(bcw.keys()) if isinstance(bcw, dict) else [],
            "has_ptw": bool(ptw),
            "locked_at": d.get("lockedAt"),
            "amended_at": d.get("amendedAt"),
        }
    return out


def audit_page_types() -> dict:
    p = PLAYBOOK / "page_type_criteria.json"
    if not p.exists():
        return {"status": "MISSING"}
    d = json.loads(p.read_text())
    specs = d.get("pageTypeSpecs", {})
    return {
        "version": d.get("version"),
        "count": len(specs),
        "list": list(specs.keys()),
        "each": {
            k: {
                "role": v.get("role"),
                "exclusions_count": len(v.get("universalExclusions", v.get("universal_exclusions", []))),
                "specific_criteria_count": len(v.get("specificCriteria", v.get("specific_criteria", []))),
            }
            for k, v in specs.items()
        },
    }


def audit_playbooks() -> dict:
    """guardrails, anti_patterns, prerequisites, ab_angles, reco_mapping, doctrine_integration_matrix."""
    files = [
        "guardrails.json",
        "anti_patterns.json",
        "prerequisites.json",
        "ab_angles.json",
        "reco_mapping.json",
        "doctrine_integration_matrix.json",
    ]
    out = {}
    for f in files:
        p = PLAYBOOK / f
        if not p.exists():
            out[f] = {"status": "MISSING"}
            continue
        d = json.loads(p.read_text())
        # Extract relevant sizes
        info = {"exists": True, "size_bytes": p.stat().st_size}
        if f == "guardrails.json":
            info["count"] = len(d.get("guardrails", []))
        elif f == "anti_patterns.json":
            info["count"] = len(d.get("anti_patterns", []))
        elif f == "prerequisites.json":
            info["count"] = len(d.get("prerequisites", []))
        elif f == "ab_angles.json":
            info["criteria_with_angles"] = len(d.get("angles_by_criterion", {}))
        elif f == "reco_mapping.json":
            info["criteria_with_recos"] = len([k for k in d if not k.startswith("_")])
        elif f == "doctrine_integration_matrix.json":
            info["amendments"] = len(d.get("amendments", []))
            info["new_criteria"] = len(d.get("new_criteria", []))
            info["new_page_types"] = len(d.get("new_page_types", []))
        out[f] = info
    return out


def audit_doctrine_coverage() -> dict:
    """Vérifie que les amendments/new_criteria/new_page_types sont bien appliqués."""
    mx = PLAYBOOK / "doctrine_integration_matrix.json"
    if not mx.exists():
        return {"status": "MISSING"}
    m = json.loads(mx.read_text())

    blocs = {}
    for pillar, fname in [
        ("hero", "bloc_1_hero_v3.json"),
        ("persuasion", "bloc_2_persuasion_v3.json"),
        ("ux", "bloc_3_ux_v3.json"),
        ("coherence", "bloc_4_coherence_v3.json"),
        ("psycho", "bloc_5_psycho_v3.json"),
        ("tech", "bloc_6_tech_v3.json"),
    ]:
        p = PLAYBOOK / fname
        if p.exists():
            blocs[pillar] = json.loads(p.read_text())

    prefix_to_bloc = {"hero": "hero", "per": "persuasion", "ux": "ux",
                       "coh": "coherence", "psy": "psycho", "tech": "tech"}

    # Amendments — check bloc criteria AND page_type specific criteria (quiz_XX, etc.)
    ptc = PLAYBOOK / "page_type_criteria.json"
    pt_data = json.loads(ptc.read_text()) if ptc.exists() else {}
    pt_specific_criteria = {}
    for pt_name, pt_spec in pt_data.get("pageTypeSpecs", {}).items():
        for c in pt_spec.get("specificCriteria", []) or []:
            cid = c.get("id")
            if cid:
                pt_specific_criteria[cid] = c

    am_report = []
    for a in m.get("amendments", []):
        tc = a.get("target_criterion", "")
        prefix = tc.split("_")[0]
        bloc = prefix_to_bloc.get(prefix)
        found = None
        source = None
        if bloc:
            crits = blocs.get(bloc, {}).get("criteria", [])
            found = next((c for c in crits if c.get("id") == tc), None)
            if found:
                source = f"bloc_{bloc}"
        # Fall back to page_type specific criteria (quiz_XX, pdp_XX, home_XX)
        if not found and tc in pt_specific_criteria:
            found = pt_specific_criteria[tc]
            source = "page_type_criteria"
        marked = bool(found and (found.get("amendedAt") or found.get("v12_amendment") or found.get("amendments")))
        am_report.append({
            "id": a.get("id"),
            "target": tc,
            "bloc": bloc,
            "source": source,
            "target_found": bool(found),
            "amendment_marker": marked,
        })

    # New criteria
    nc_report = []
    for nc in m.get("new_criteria", []):
        cid = nc.get("new_criterion_id", "")
        bloc = nc.get("bloc")
        crits = blocs.get(bloc, {}).get("criteria", []) if bloc else []
        present = cid in [c.get("id") for c in crits]
        nc_report.append({"id": nc.get("id"), "criterion_id": cid, "bloc": bloc, "present": present})

    # New page types (reuse pt_data loaded above)
    pt_specs = pt_data.get("pageTypeSpecs", {})
    npt_report = []
    for npt in m.get("new_page_types", []):
        t = npt.get("type")
        npt_report.append({"id": npt.get("id"), "type": t, "present": t in pt_specs})

    return {
        "amendments": {
            "total": len(am_report),
            "found_in_bloc": sum(1 for r in am_report if r["target_found"]),
            "with_marker": sum(1 for r in am_report if r["amendment_marker"]),
            "details": am_report,
        },
        "new_criteria": {
            "total": len(nc_report),
            "present": sum(1 for r in nc_report if r["present"]),
            "details": nc_report,
        },
        "new_page_types": {
            "total": len(npt_report),
            "present": sum(1 for r in npt_report if r["present"]),
            "details": npt_report,
        },
    }


# ───────────────────────── Scripts audit ────────────────────────────────

SCORER_FILES = [
    "score_hero.py", "score_persuasion.py", "score_ux.py",
    "score_coherence.py", "score_psycho.py", "score_tech.py",
]

PERCEPTION_FILES = [
    "page_cleaner.py", "component_detector.py", "overlay_renderer.py",
    "overlay_burn.py", "component_validator.py", "perception_pipeline.py",
]

ORCHESTRATOR_FILES = [
    "score_page_type.py", "page_type_filter.py", "score_specific_criteria.py",
    "score_universal_extensions.py", "score_site.py", "reco_enricher.py",
]

CAPTURE_FILES = [
    "capture_site.py", "batch_capture.py", "batch_site.py",
    "batch_spatial_capture.py", "native_capture.py", "run_capture.py",
    "discover_pages.py", "run_discover.py", "ghost_capture.js",
    "spatial_bridge.py", "spatial_enrich.py", "spatial_scoring.py",
    "run_spatial_capture.py", "apify_enrich.py",
    "component_perception.py", "perception_inject.py", "semantic_mapper.py",
    "analyze_capture.py", "batch_rescore.py", "criterion_crops.py",
]


def _file_info(p: pathlib.Path) -> dict:
    if not p.exists():
        return {"exists": False}
    txt = p.read_text(errors="ignore")
    return {
        "exists": True,
        "lines": txt.count("\n") + 1,
        "size_bytes": p.stat().st_size,
        "sha1": hashlib.sha1(txt.encode("utf-8")).hexdigest()[:10],
        "first_docstring": _extract_docstring(txt),
    }


def _extract_docstring(txt: str) -> str:
    m = re.search(r'^"""(.*?)"""', txt, re.DOTALL | re.MULTILINE)
    if not m:
        return ""
    return m.group(1).strip().split("\n")[0][:200]


def _grep_count(path: pathlib.Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return len(re.findall(pattern, path.read_text(errors="ignore")))


def audit_scripts() -> dict:
    out = {}
    for group, files in [
        ("pillar_scorers", SCORER_FILES),
        ("perception_layer2", PERCEPTION_FILES),
        ("orchestrators", ORCHESTRATOR_FILES),
        ("capture_pipeline", CAPTURE_FILES),
    ]:
        out[group] = {f: _file_info(SCRIPTS / f) for f in files}
    # Root scripts
    out["root"] = {
        f.name: _file_info(f)
        for f in [ROOT / "reco_engine.py", ROOT / "spatial_reco.py",
                  ROOT / "generate_audit_data.py", ROOT / "generate_audit_data_v2.py"]
    }
    return out


def audit_integration() -> dict:
    """Vérifie l'intégration Perception Layer 2 → Scoring V3."""
    targets = {
        "scoring_reads_components": [
            (SCRIPTS / f, r"components\.json|component_detector|from\s+component_detector|perception_bridge|load_perception|has_component")
            for f in SCORER_FILES
        ],
        "reco_engine_reads_components": [
            (ROOT / "reco_engine.py", r"components\.json|critic_report|component_detector|perception_bridge|load_perception"),
        ],
        "reco_enricher_reads_components": [
            (SCRIPTS / "reco_enricher.py", r"components\.json|critic_report|component_detector|perception_bridge|load_perception"),
        ],
        "scorers_use_page_type_filter": [
            (SCRIPTS / f, r"page_type_filter|get_exclusions|page_type_criteria") for f in SCORER_FILES
        ],
        "scorers_use_bcw": [
            (SCRIPTS / f, r"businessCategoryWeighting|business_category_weighting|bcw") for f in SCORER_FILES
        ],
    }
    out = {}
    for key, checks in targets.items():
        res = {}
        for path, pattern in checks:
            res[path.name] = _grep_count(path, pattern)
        out[key] = res
    return out


# ───────────────────────── Captures audit ──────────────────────────────

def audit_captures() -> dict:
    if not DATA_CAP.exists():
        return {"status": "MISSING"}
    sites = [d for d in DATA_CAP.iterdir() if d.is_dir()]
    total_pages = 0
    pages_by_site = {}
    artefacts_per_page = Counter()
    verdicts = Counter()
    for site in sites:
        pages = [d for d in site.iterdir() if d.is_dir() and d.name != "__pycache__"]
        pages_by_site[site.name] = len(pages)
        total_pages += len(pages)
        for p in pages:
            for fname in ["spatial_v9.json", "spatial_v9_clean.json", "components.json",
                           "component_overlay.html", "component_overlay.png",
                           "critic_report.json", "capture.json",
                           "score_hero.json", "score_persuasion.json", "score_ux.json",
                           "score_coherence.json", "score_psycho.json", "score_tech.json",
                           "score_page_type.json", "reco_enriched.json"]:
                if (p / fname).exists():
                    artefacts_per_page[fname] += 1
            cr = p / "critic_report.json"
            if cr.exists():
                try:
                    v = json.loads(cr.read_text()).get("verdict")
                    if v:
                        verdicts[v] += 1
                except Exception:
                    pass
    return {
        "sites": len(sites),
        "total_pages": total_pages,
        "pages_by_site": pages_by_site,
        "artefacts_per_page": dict(artefacts_per_page.most_common()),
        "perception_verdicts": dict(verdicts),
    }


# ───────────────────────── Memory audit ────────────────────────────────

def audit_memory() -> dict:
    mem_space = pathlib.Path(
        "/Users/mathisfronty/Library/Application Support/Claude/"
        "local-agent-mode-sessions/5e08a9fe-5e63-4c28-b677-43b237c10f89/"
        "412cfc85-e020-4b70-be5f-a8e18be1f042/spaces/"
        "736befe1-dbee-4abd-9518-cebce9f92920/memory"
    )
    if not mem_space.exists():
        return {"status": "memory space not found"}
    files = sorted(mem_space.glob("*.md"))
    categorized = {"user": [], "feedback": [], "project": [], "reference": [], "other": []}
    for f in files:
        if f.name == "MEMORY.md":
            continue
        name = f.name
        if name.startswith("user_"):
            categorized["user"].append(name)
        elif name.startswith("feedback_"):
            categorized["feedback"].append(name)
        elif name.startswith("project_"):
            categorized["project"].append(name)
        elif name.startswith("reference_"):
            categorized["reference"].append(name)
        else:
            categorized["other"].append(name)
    return {
        "total": len(files) - 1,  # exclude MEMORY.md
        "categorized": {k: len(v) for k, v in categorized.items()},
        "files": categorized,
    }


# ───────────────────────── Rendering ───────────────────────────────────

def _tree(path: pathlib.Path, prefix: str = "", depth: int = 0, max_depth: int = 2,
          skip: set | None = None) -> list[str]:
    skip = skip or {"__pycache__", ".git", "node_modules", ".DS_Store", ".next"}
    lines = []
    if depth > max_depth:
        return lines
    try:
        entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name))
    except (PermissionError, FileNotFoundError):
        return lines
    visible = [e for e in entries if e.name not in skip and not e.name.startswith(".")]
    for i, e in enumerate(visible):
        is_last = (i == len(visible) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{e.name}{'/' if e.is_dir() else ''}")
        if e.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(_tree(e, prefix + extension, depth + 1, max_depth, skip))
    return lines


def render_state_md(snap: dict) -> str:
    lines = [
        "# GrowthCRO V12 — STATE",
        "",
        f"*Généré par `project_snapshot.py v{VERSION}` le {NOW}*",
        "",
        "Ce fichier est **régénéré automatiquement** à chaque snapshot. Il reflète",
        "l'état RÉEL du filesystem. Pour l'historique humain, voir `BACKLOG.md`.",
        "",
        "## 1. Arborescence racine (depth 2)",
        "",
        "```",
        f"{ROOT.name}/",
    ]
    lines.extend(_tree(ROOT, "", 0, 2))
    lines.append("```")
    lines.append("")

    # Playbook
    pb = snap["playbook_blocs"]
    lines.append("## 2. Playbook — 6 blocs V3")
    lines.append("")
    lines.append("| Pillar | File | Version | Max | Crit | Killers | VP check | BCW | PTW |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for pillar in ["hero", "persuasion", "ux", "coherence", "psycho", "tech"]:
        b = pb.get(pillar, {})
        lines.append(
            f"| {pillar} | `{b.get('file','?')}` | {b.get('version','?')} | "
            f"{b.get('max','?')} | {b.get('criteria_count','?')} | "
            f"{b.get('killers_count','?')} | {b.get('viewport_check_coverage','?')} | "
            f"{'✅' if b.get('has_bcw') else '❌'} | "
            f"{'✅' if b.get('has_ptw') else '❌'} |"
        )
    total_crits = sum(b.get("criteria_count", 0) for b in pb.values())
    total_killers = sum(b.get("killers_count", 0) for b in pb.values())
    lines.append("")
    lines.append(f"**Total critères : {total_crits}** · Killers : {total_killers}")
    lines.append("")

    # Page types
    pt = snap["page_types"]
    lines.append("## 3. Page types (page_type_criteria.json)")
    lines.append("")
    lines.append(f"- Version : {pt.get('version')}")
    lines.append(f"- **{pt.get('count')} pageTypes** : {', '.join(pt.get('list', []))}")
    lines.append("")

    # Other playbooks
    pbs = snap["playbooks"]
    lines.append("## 4. Autres playbooks")
    lines.append("")
    lines.append("| File | Metric | Value |")
    lines.append("|---|---|---|")
    for fname, info in pbs.items():
        if "status" in info:
            lines.append(f"| `{fname}` | status | {info['status']} |")
            continue
        for k, v in info.items():
            if k in ("exists",):
                continue
            lines.append(f"| `{fname}` | {k} | {v} |")
    lines.append("")

    # Doctrine coverage
    dc = snap["doctrine_coverage"]
    if "amendments" in dc:
        lines.append("## 5. Doctrine enrichie — couverture")
        lines.append("")
        am = dc["amendments"]
        nc = dc["new_criteria"]
        npt = dc["new_page_types"]
        lines.append(f"- **Amendments** : {am['with_marker']}/{am['total']} avec marqueur `amendedAt`")
        lines.append(f"- **New criteria** : {nc['present']}/{nc['total']} présents dans les blocs")
        lines.append(f"- **New page types** : {npt['present']}/{npt['total']} présents")
        lines.append("")
        # Flag les gaps
        gaps = []
        for r in am["details"]:
            if r["target_found"] and not r["amendment_marker"]:
                gaps.append(f"  - Amendment {r['id']} → `{r['target']}` ({r['bloc']}) : target trouvé mais pas de marqueur")
        if gaps:
            lines.append("### Gaps amendments")
            lines.extend(gaps)
            lines.append("")

    # Scripts
    sc = snap["scripts"]
    lines.append("## 6. Scripts — inventaire")
    lines.append("")
    for group in ["pillar_scorers", "perception_layer2", "orchestrators", "capture_pipeline", "root"]:
        lines.append(f"### {group}")
        lines.append("")
        lines.append("| File | Lines | SHA1 | Docstring |")
        lines.append("|---|---|---|---|")
        for fname, info in sc[group].items():
            if info.get("exists"):
                lines.append(
                    f"| `{fname}` | {info['lines']} | `{info['sha1']}` | "
                    f"{info.get('first_docstring','')[:80]} |"
                )
            else:
                lines.append(f"| `{fname}` | — | — | **MISSING** |")
        lines.append("")

    # Integration
    inte = snap["integration"]
    lines.append("## 7. Intégration Perception Layer 2 → Scoring V3")
    lines.append("")
    lines.append("Vérifie que les scorers consomment les artefacts Perception.")
    lines.append("")
    for check, results in inte.items():
        total = sum(results.values())
        lines.append(f"### `{check}` — total {total} refs")
        lines.append("")
        for f, c in results.items():
            mark = "✅" if c > 0 else "❌"
            lines.append(f"- {mark} `{f}` : {c} refs")
        lines.append("")

    # Captures
    cap = snap["captures"]
    if "sites" in cap:
        lines.append("## 8. Captures — état")
        lines.append("")
        lines.append(f"- **{cap['sites']} sites**, **{cap['total_pages']} pages**")
        lines.append("")
        lines.append("### Artefacts par page")
        lines.append("")
        lines.append("| Artefact | Pages |")
        lines.append("|---|---|")
        for f, c in cap["artefacts_per_page"].items():
            lines.append(f"| `{f}` | {c} |")
        lines.append("")
        lines.append(f"### Perception verdicts : {cap.get('perception_verdicts', {})}")
        lines.append("")

    # Memory
    mem = snap["memory"]
    lines.append("## 9. Memory")
    lines.append("")
    lines.append(f"- **{mem.get('total',0)} fichiers** dans memory space")
    lines.append(f"- Par type : {mem.get('categorized', {})}")
    lines.append("")

    lines.append("---")
    lines.append(f"*Snapshot sauvegardé : `.claude/memory/snapshots/{NOW.replace(':','-')[:16]}.json`*")
    lines.append("")
    return "\n".join(lines)


def render_architecture_md() -> str:
    return """# GrowthCRO V12 — ARCHITECTURE

*Régénéré à chaque snapshot. Flux de données entre modules.*

## Flux complet — de l'URL au reco enrichi

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. DISCOVERY                                                       │
│  run_discover.py → discover_pages.py                                │
│  Apify/Ghost → pages_discovered.json                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│  2. CAPTURE                                                         │
│  run_capture.py / batch_capture.py → native_capture.py              │
│    ├─ ghost_capture.js (Playwright) → capture_native.json           │
│    ├─ spatial_capture_v9.js injecté → spatial_v9.json               │
│    └─ screenshots desktop/mobile → *.png                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│  3. LAYER 2 PERCEPTION (V12 Phase 5)                                │
│  perception_pipeline.py                                             │
│    ├─ page_cleaner.py       → spatial_v9_clean.json                 │
│    ├─ component_detector.py → components.json (16 types)            │
│    ├─ overlay_renderer.py   → component_overlay.html                │
│    ├─ overlay_burn.py       → component_overlay.png (audit visuel)  │
│    └─ component_validator.py → critic_report.json                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│  4. SCORING V3 (6 blocs × 47 critères)                              │
│  score_page_type.py (orchestrateur)                                 │
│    ├─ page_type_filter.py : exclusions universelles par pageType    │
│    ├─ score_hero.py        → score_hero.json                        │
│    ├─ score_persuasion.py  → score_persuasion.json                  │
│    ├─ score_ux.py          → score_ux.json                          │
│    ├─ score_coherence.py   → score_coherence.json                   │
│    ├─ score_psycho.py      → score_psycho.json                      │
│    ├─ score_tech.py        → score_tech.json                        │
│    ├─ score_specific_criteria.py : 22 détecteurs d_* par pageType   │
│    └─ score_universal_extensions.py : 9 détecteurs additifs         │
│  → score_page_type.json (vue unifiée + exclusions tracées)          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│  5. SITE AGGREGATE                                                  │
│  score_site.py : moyenne pondérée par tier (primary/mandatory/opt)  │
│  → site_audit.json                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│  6. RECO ENRICHMENT                                                 │
│  reco_engine.py → reco brute par critère                            │
│  reco_enricher.py : enrichit avec                                   │
│    ├─ guardrails.json      → 11 guardrails                          │
│    ├─ anti_patterns.json   → 15 anti-patterns                       │
│    ├─ prerequisites.json   → cascade de 10 prérequis                │
│    ├─ ab_angles.json       → A/B variants Schwartz × biz_category   │
│    └─ ICE (impact × confidence × ease → effort_days)                │
│  → reco_enriched.json                                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Playbook — structure

```
playbook/
├── bloc_1_hero_v3.json           6 critères   BCW✓  PTW–
├── bloc_2_persuasion_v3.json    11 critères   BCW?  PTW✓
├── bloc_3_ux_v3.json             8 critères   BCW✓  PTW✓
├── bloc_4_coherence_v3.json      9 critères   BCW✓  PTW✓
├── bloc_5_psycho_v3.json         8 critères   BCW?  PTW✓
├── bloc_6_tech_v3.json           5 critères   BCW?  PTW✓
│                                 ═══════════
│                                 47 critères ✓ (doctrine)
│
├── page_type_criteria.json      18 pageTypes (home, pdp, collection,
│                                 lp_leadgen, lp_sales, blog, quiz_vsl,
│                                 pricing, checkout, listicle, advertorial,
│                                 comparison, vsl, challenge, thank_you_page,
│                                 bundle_standalone, squeeze, webinar)
│
├── guardrails.json              11 guardrails
├── anti_patterns.json           15 anti-patterns
├── prerequisites.json           10 prérequis + cascade
├── ab_angles.json                8 critères × biz × Schwartz
├── reco_mapping.json            39 critères × 3 niveaux (legacy, superseded)
└── doctrine_integration_matrix.json   12 amend + 8 new crit + 9 new pt
```

## Interconnexions clés

- `page_type_criteria.json` est lu par `page_type_filter.py` qui est importé
  par `score_page_type.py` (orchestrateur) ET par les 6 pillar scorers.
- `components.json` est produit par `component_detector.py` et **devrait** être
  consommé par les 6 pillar scorers + `reco_enricher.py` (actuellement DÉCONNECTÉ).
- `critic_report.json` est produit par `component_validator.py` et **devrait**
  alimenter `reco_enricher.py` en signal qualité de perception.
- `reco_enricher.py` lit les 4 playbooks enrichis (guardrails/anti-patterns/
  prerequisites/ab_angles) en plus du score_page_type.json.
- `reco_engine.py` est la V1 du moteur reco (root-level). Co-existe avec
  `reco_enricher.py` (skills/site-capture/scripts/). À rationaliser.

## Dual-viewport

Tous les 47 critères V3 ont `viewport_check` (desktop/mobile/both).
Dual-viewport scoring : min(D, M) par défaut, 0.7/0.3 DTC, 0.6/0.4 SaaS B2B + Luxe.

## Axiomes & règles permanentes

Voir `playbook/AXIOMES.md`. Principes clés :
- Qualité > vitesse
- Screenshots = preuve, DOM rendered = source of truth
- Jamais Notion auto sans demande
- Dual-viewport obligatoire sur tout critère visuel
- 5 sources internes/bloc minimum
"""


def render_backlog_md(snap: dict, append_note: str | None = None) -> str:
    """
    BACKLOG.md est append-only pour l'historique, mais régénère la section 'à faire'
    à partir du snapshot (matrice done/partial/todo dérivée des gaps).
    """
    # Si BACKLOG.md existe, on préserve la section HISTORIQUE
    backlog_path = ROOT / "BACKLOG.md"
    history_section = ""
    if backlog_path.exists():
        existing = backlog_path.read_text()
        m = re.search(r"## 🗓️ HISTORIQUE.*?(?=##\s|\Z)", existing, re.DOTALL)
        if m:
            history_section = m.group(0)
    if not history_section:
        history_section = """## 🗓️ HISTORIQUE

(Chaque étape importante ajoute une ligne avec sa date. Le script `project_snapshot.py`
append l'entrée via `--note`.)

"""

    # Append note si fourni
    if append_note:
        history_section += f"- **{NOW[:10]}** — {append_note}\n"

    # Section "À faire" dérivée des gaps
    pb = snap["playbook_blocs"]
    dc = snap["doctrine_coverage"]
    inte = snap["integration"]

    gaps = []
    # Couche 1
    if not pb.get("persuasion", {}).get("has_bcw"):
        gaps.append("- [ ] P0.2a — BCW Persuasion (bloc 2)")
    if not pb.get("psycho", {}).get("has_bcw"):
        gaps.append("- [ ] P0.2b — BCW Psycho (bloc 5)")
    if not pb.get("tech", {}).get("has_bcw"):
        gaps.append("- [ ] P0.2c — BCW Tech (bloc 6)")
    _coh_killers = pb.get("coherence", {}).get("killers_count", 0)
    if _coh_killers == 0:
        gaps.append("- [ ] P0.3 — Killers Cohérence (bloc 4, 0 actuel)")
    else:
        gaps.append(f"- [x] P0.3 — Killers Cohérence ({_coh_killers} killers bloc 4, 2026-04-14 DONE)")

    # Amendments sans marqueur
    if "amendments" in dc:
        missing = [r for r in dc["amendments"]["details"]
                   if r["target_found"] and not r["amendment_marker"]]
        if missing:
            gaps.append(f"- [ ] P0.4 — Marquer {len(missing)} amendments "
                        f"({', '.join(r['id'] for r in missing)}) "
                        f"avec `amendedAt`/`v12_amendment`")

    # Intégration Perception
    scoring_reads_comp = inte.get("scoring_reads_components", {})
    total_sc = sum(scoring_reads_comp.values())
    if total_sc == 0:
        gaps.append("- [ ] P0.1 — Intégrer Perception Layer 2 → Scoring V3 "
                    "(0 import actuel de components.json/critic_report dans pillar scorers)")

    # V1/V2 archive
    v1_files = [ROOT / "data" / "cro_criteria_v2.json",
                ROOT / "skills" / "cro-auditor" / "references" / "audit_criteria.md",
                ROOT / "data" / "_proto_data_blob.json"]
    if any(f.exists() for f in v1_files):
        gaps.append("- [ ] P1.1 — Archiver V1/V2 (cro_criteria_v2.json, audit_criteria.md, "
                    "_proto_data_blob.json)")

    # Schema reco
    if not (PLAYBOOK / "reco_schema.json").exists():
        gaps.append("- [ ] P1.2 — Créer `playbook/reco_schema.json` (JSON schema formel)")

    # Known backlog — reflect actual completion state
    # P1.3 : done if doctrine_integration_status.md exists
    if (PLAYBOOK / "doctrine_integration_status.md").exists():
        gaps.append("- [x] P1.3 — Tracking 6 updates reco + 5 gaps code dans doctrine_matrix (2026-04-14 DONE)")
    else:
        gaps.append("- [ ] P1.3 — Tracking 6 updates reco + 5 gaps code dans doctrine_matrix")

    # P1.4 : done if component_detector.py contains the product_card disqualifier
    cd_path = ROOT / "skills" / "site-capture" / "scripts" / "component_detector.py"
    if cd_path.exists() and "looks_like_product_card_not_cta_band" in cd_path.read_text(encoding="utf-8"):
        gaps.append("- [x] P1.4 — Phase 5.7 cta_band over-detection fix (2026-04-14 DONE — 13→1 sur edone/pdp)")
    else:
        gaps.append("- [ ] P1.4 — Phase 5.7 cta_band over-detection (PDP variant selectors)")

    # P2 : partial — done if quiz_03 detector registered
    sc_path = ROOT / "skills" / "site-capture" / "scripts" / "score_specific_criteria.py"
    if sc_path.exists() and "d_quiz_personalized_result" in sc_path.read_text(encoding="utf-8"):
        gaps.append("- [~] P2 — Phase 6 Quiz deep dive (3/5 DONE : exclusions, weights 70/30, quiz_03/04 — Étapes 2+5 scoped out)")
    else:
        gaps.append("- [ ] P2 — Phase 6 Quiz deep dive (5 sous-étapes)")

    # Future features (post-V12, portées webapp) — list statique, pas dérivé de l'état
    future_features = [
        "- [ ] **Export audit & reco (webapp future)** — fonction \"télécharger\" audit+reco "
        "format pro (PDF/Docx/partage URL) depuis la future webapp. PAS prioritaire V12 "
        "(Mathis 2026-04-14 : \"tout sera dispo en ligne, ajoute au backlog mais pas mtn\")",
        "- [ ] **Migration Vercel + Supabase + Claude Code** — passage Cowork → standalone "
        "(voir `project_growthcro_roadmap.md`)",
        "- [ ] **Phase 6 complète** — multi-capture quiz step-by-step + 3 benchmarks quiz "
        "(étapes 2 + 5 scopées out session 20260414, à reprendre si client quiz entrant)",
    ]

    content = f"""# GrowthCRO V12 — BACKLOG

*Section "À faire" régénérée automatiquement depuis l'état réel du projet.*
*Section "Historique" append-only — préservée entre snapshots.*

## ✅ À FAIRE — dérivé du snapshot {NOW[:16]}

{chr(10).join(gaps) if gaps else '*(Aucun gap détecté — everything green!)*'}

## 🗺️ FUTURE (post-V12, webapp)

{chr(10).join(future_features)}

{history_section}
"""
    return content


# ───────────────────────── Main ────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GrowthCRO V12 project snapshot")
    parser.add_argument("--note", type=str, help="Append note to BACKLOG history")
    parser.add_argument("--phase", type=str, help="Phase ID (e.g. P0.1)")
    parser.add_argument("--status", type=str, help="in_progress / done / blocked")
    args = parser.parse_args()

    # Build snapshot
    snap = {
        "version": VERSION,
        "generated_at": NOW,
        "playbook_blocs": audit_blocs(),
        "page_types": audit_page_types(),
        "playbooks": audit_playbooks(),
        "doctrine_coverage": audit_doctrine_coverage(),
        "scripts": audit_scripts(),
        "integration": audit_integration(),
        "captures": audit_captures(),
        "memory": audit_memory(),
    }

    # Notes
    note = args.note
    if args.phase and args.status:
        note = f"{args.phase} → {args.status}" + (f" · {args.note}" if args.note else "")

    # Write JSON snapshot
    json_path = SNAPSHOTS_DIR / f"{NOW.replace(':','-')[:16]}.json"
    json_path.write_text(json.dumps(snap, indent=2, ensure_ascii=False))

    # Write STATE.md
    state_md = render_state_md(snap)
    (ROOT / "STATE.md").write_text(state_md)

    # Write ARCHITECTURE.md
    (ROOT / "ARCHITECTURE.md").write_text(render_architecture_md())

    # Write BACKLOG.md
    backlog_md = render_backlog_md(snap, append_note=note)
    (ROOT / "BACKLOG.md").write_text(backlog_md)

    print(f"✅ Snapshot v{VERSION} @ {NOW}")
    print(f"   STATE.md          ({len(state_md)} chars)")
    print(f"   ARCHITECTURE.md")
    print(f"   BACKLOG.md        ({len(backlog_md)} chars)")
    print(f"   {json_path.relative_to(ROOT)}")
    if note:
        print(f"   note: {note}")


if __name__ == "__main__":
    main()
