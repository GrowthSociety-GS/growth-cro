#!/usr/bin/env python3
"""Sprint 10 / Task 016 — collapse 5 µfrontends to a single @growthcro/shell entry.

Updates `deliverables/architecture-explorer-data.js` per the D1.A monorepo
decision (2026-05-14). Idempotent : detects whether the collapse has already
been applied and exits 0. Run once at task ship time ; preserved in scripts/
for future architecture audits.

Scope of edits :
  1. pipelines[id=webapp_v28].extra.microfrontends     → 1 @growthcro/shell entry
  2. pipelines[id=webapp_v28].description / status     → reflect D1.A
  3. pipelines[id=webapp_v28].extra.skills_combo       → drop vercel-microfrontends
  4. pipelines[id=webapp].extra.stages_v28_nextjs_target → drop "5 microfrontends"
  5. skills_integration.combo_packs.webapp_nextjs.skills → drop vercel-microfrontends
  6. skills_integration.essentials                     → mark vercel-microfrontends dropped
  7. mermaid_views[idx=4 "5. Webapp"]                  → diagram reflects shell
  8. meta.revision_notes                               → append D1.A entry
  9. counts                                            → re-derive from arrays

Doctrine : CODE_DOCTRINE.md axis #3 (persistence) — pure I/O wrapper around a
JSON mutation. Stdlib only. No env access.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "deliverables" / "architecture-explorer-data.js"

REVISION_NOTE = "Architecture revised 2026-05-14 per D1.A monorepo decision"
SHELL_ENTRY = "@growthcro/shell v0.28.0 — consolidated Next.js 14 App Router shell (audits/recos/gsg/reality/learning/clients/settings under apps/shell/app/*) [ACTIVE]"


def load_data() -> tuple[str, dict, str]:
    """Parse window.ARCH = {...}; into (prefix, dict, suffix)."""
    raw = TARGET.read_text(encoding="utf-8")
    match = re.match(r"^(window\.ARCH\s*=\s*)(\{.*\})(;\s*)$", raw, re.DOTALL)
    if not match:
        sys.exit("[task-016] could not parse window.ARCH wrapper")
    prefix, body, suffix = match.group(1), match.group(2), match.group(3)
    return prefix, json.loads(body), suffix


def find_pipeline(data: dict, pipeline_id: str) -> dict | None:
    for pipe in data.get("pipelines", []):
        if pipe.get("id") == pipeline_id:
            return pipe
    return None


def update_webapp_v28(data: dict) -> bool:
    """Collapse pipelines.webapp_v28 to a single @growthcro/shell entry."""
    pipe = find_pipeline(data, "webapp_v28")
    if pipe is None:
        sys.exit("[task-016] pipelines[id=webapp_v28] not found")

    extra = pipe.setdefault("extra", {})
    current = extra.get("microfrontends", [])
    if current == [SHELL_ENTRY]:
        return False  # already collapsed

    extra["microfrontends"] = [SHELL_ENTRY]
    pipe["description"] = (
        "Next.js 14 (App Router) + Supabase EU. Consolidated single shell per "
        "D1.A monorepo decision (2026-05-14). Scale Growth Society 100+ clients."
    )
    pipe["status"] = (
        "V28 v2 — single @growthcro/shell v0.28.0 (FR-1 consolidation 2026-05-13, "
        "D1.A confirmed 2026-05-14)."
    )
    skills_combo = extra.get("skills_combo", "")
    if "vercel-microfrontends" in skills_combo:
        extra["skills_combo"] = skills_combo.replace(
            " + vercel-microfrontends", ""
        ).replace("vercel-microfrontends + ", "")
    extra["architecture_decision"] = (
        ".claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md (D1.A)"
    )
    return True


def update_webapp_stages(data: dict) -> bool:
    """Strip the '5 microfrontends' stage from pipelines.webapp."""
    pipe = find_pipeline(data, "webapp")
    if pipe is None:
        return False
    extra = pipe.setdefault("extra", {})
    stages = extra.get("stages_v28_nextjs_target", [])
    new_stages = [
        s for s in stages
        if "microfrontend" not in s.lower() or "shell" in s.lower()
    ]
    # Replace any survivor that still mentions µfrontends + ensure the shell line exists.
    new_stages = [
        "@growthcro/shell single Next.js 14 app (apps/shell/app/{audits,recos,gsg,reality,learning,clients,settings})"
        if "microfrontend" in s.lower() else s
        for s in stages
    ]
    if new_stages == stages:
        return False
    extra["stages_v28_nextjs_target"] = new_stages
    return True


def update_skills_integration(data: dict) -> bool:
    """Drop vercel-microfrontends from webapp_nextjs combo + mark essentials entry as dropped."""
    si = data.get("skills_integration", {})
    changed = False

    combos = si.get("combo_packs", {}).get("webapp_nextjs", {})
    skills = combos.get("skills", [])
    if "vercel-microfrontends" in skills:
        combos["skills"] = [s for s in skills if s != "vercel-microfrontends"]
        combos["max_session"] = max(2, combos.get("max_session", 4) - 1)
        combos["rationale"] = (
            "frontend-design pour composants, web-artifacts-builder pour shadcn/Tailwind, "
            "Figma si Mathis fournit un design. vercel-microfrontends DROPPED 2026-05-15 "
            "per D1.A monorepo decision (single @growthcro/shell)."
        )
        changed = True

    for entry in si.get("essentials", []):
        if entry.get("name") == "vercel-microfrontends":
            if entry.get("status") != "dropped":
                entry["installed"] = False
                entry["status"] = "dropped"
                entry["dropped_at"] = "2026-05-15"
                entry["dropped_reason"] = (
                    "D1.A monorepo decision (2026-05-14) — single @growthcro/shell, "
                    "no multi-zone routing. See MICROFRONTENDS_DECISION_2026-05-14.md."
                )
                entry["combo"] = None
                changed = True

    return changed


def update_mermaid_webapp(data: dict) -> bool:
    """Rewrite mermaid_views[4] (5. Webapp) to show a single shell node in V28 subgraph."""
    views = data.get("mermaid_views", [])
    target_title = "5. Webapp — V27 HTML today, V28 Next.js target"
    new_title = "5. Webapp — V27 HTML today, V28 Next.js shell (D1.A monorepo)"
    new_src = (
        "flowchart TD\n"
        "    subgraph V27[\"V27 HTML (legacy snapshot, 56 clients)\"]\n"
        "        AuditPipe[\"audit pipeline §2<br/>(56 clients × 185 pages)\"] --> CaptureTree[(\"data/captures/&lt;client&gt;/&lt;page&gt;/*<br/>~150 artefacts/page\")]\n"
        "        CaptureTree --> Builder[\"skills/build_growth_audit_data<br/>(consolidates the tree)\"]\n"
        "        Builder --> DashJS[(\"deliverables/growth_audit_data.js<br/>12 MB consolidated bundle\")]\n"
        "        DashJS --> CommandCenter[/\"deliverables/GrowthCRO-V27-CommandCenter.html<br/>11 panes\"/]\n"
        "        APIv1[\"growthcro/api/server<br/>FastAPI (legacy)\"] -.programmatic.-> CommandCenter\n"
        "    end\n\n"
        "    subgraph V28[\"V28 Next.js — @growthcro/shell (D1.A monorepo)\"]\n"
        "        SupabaseAuth[\"Supabase EU<br/>auth + tables clients/audits/recos/runs\"]\n"
        "        EdgeAPI[\"Next.js API routes<br/>/api/runs · /api/learning · /api/gsg\"]\n"
        "        Worker[\"growthcro/worker (Phase A local)<br/>Fly.io VM (Phase B future)\"]\n"
        "        Shell[\"@growthcro/shell v0.28.0<br/>apps/shell/app/{audits,recos,gsg,<br/>reality,learning,clients,settings}\"]\n"
        "        Realtime[\"Supabase Realtime<br/>channel public:runs\"]\n\n"
        "        SupabaseAuth --> Shell\n"
        "        EdgeAPI --> Shell\n"
        "        EdgeAPI --> Worker\n"
        "        Worker --> Realtime\n"
        "        Realtime --> Shell\n"
        "    end\n\n"
        "    AuditPipe -.same data tree.-> Worker"
    )

    for view in views:
        if view.get("title") in (target_title, new_title):
            if view.get("src") == new_src and view.get("title") == new_title:
                return False
            view["title"] = new_title
            view["src"] = new_src
            return True
    return False


def update_revision_notes(data: dict) -> bool:
    """Append the D1.A revision note to meta.revision_notes (create if absent)."""
    meta = data.setdefault("meta", {})
    notes = meta.setdefault("revision_notes", [])
    today = date.today().isoformat()
    entry = {"date": today, "note": REVISION_NOTE, "task_ref": "Sprint 10 / Task 016"}
    for existing in notes:
        if existing.get("note") == REVISION_NOTE:
            return False
    notes.append(entry)
    return True


def recount(data: dict) -> bool:
    """Re-derive counts from current arrays. Returns True if counts changed."""
    counts = data.setdefault("counts", {})
    new = {
        "modules": len(data.get("modules", [])),
        "pipelines": len(data.get("pipelines", [])),
        "data_artefacts": len(data.get("data_artefacts", [])),
        "essentials": len(data.get("skills_integration", {}).get("essentials", [])),
        "on_demand": len(data.get("skills_integration", {}).get("on_demand", [])),
        "excluded": len(data.get("skills_integration", {}).get("excluded", [])),
        "mermaid_views": len(data.get("mermaid_views", [])),
    }
    if counts == new:
        return False
    counts.update(new)
    return True


def main() -> int:
    prefix, data, suffix = load_data()

    changes = {
        "webapp_v28_collapse": update_webapp_v28(data),
        "webapp_stages_v28": update_webapp_stages(data),
        "skills_integration": update_skills_integration(data),
        "mermaid_webapp": update_mermaid_webapp(data),
        "revision_notes": update_revision_notes(data),
        "counts": recount(data),
    }
    if not any(changes.values()):
        print("[task-016] architecture-explorer-data.js already up to date (idempotent no-op)")
        return 0

    new_body = json.dumps(data, indent=2, ensure_ascii=False)
    TARGET.write_text(f"{prefix}{new_body}{suffix}", encoding="utf-8")
    applied = [k for k, v in changes.items() if v]
    print(f"[task-016] updated architecture-explorer-data.js : {', '.join(applied)}")
    print(f"[task-016] modules={data['counts']['modules']} pipelines={data['counts']['pipelines']} data_artefacts={data['counts']['data_artefacts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
