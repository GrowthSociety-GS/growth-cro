"""Canonical GSG contract and static validation helpers.

This is the source of truth for the "one GSG" boundary:

- public product name: GSG
- public skill: skills/gsg
- public engine: moteur_gsg
- legacy lab: skills/growth-site-generator/scripts, read-only through adapters

It is intentionally deterministic and generation-free. Run
`python3 scripts/check_gsg_canonical.py` before any new GSG generation sprint.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

from moteur_gsg.orchestrator import list_supported_modes
from moteur_gsg.core.creative_route_selector import creative_route_selector_status
from moteur_gsg.core.legacy_lab_adapters import legacy_component_status
from moteur_gsg.core.visual_system import visual_system_status

ROOT = pathlib.Path(__file__).resolve().parents[2]

PUBLIC_MODES = ["complete", "replace", "extend", "elevate", "genesis"]
ALLOWED_ALIASES = ["complete_v26aa", "persona"]


PRODUCT_CONTRACT: dict[str, dict[str, Any]] = {
    "complete": {
        "label": "Mode 1 COMPLETE",
        "role": "Nouvelle LP autonome pour une marque existante.",
        "depends_on_audit_engine": False,
        "required_inputs": ["client_url_or_slug", "page_type", "BriefV2"],
        "canonical_entrypoint": "moteur_gsg.orchestrator.generate_lp(mode='complete')",
        "default_runtime": "moteur_gsg.modes.mode_1_complete",
        "status": "active_structured_route_selector_v27_2_f",
    },
    "replace": {
        "label": "Mode 2 REPLACE",
        "role": "Refonte d'une page auditee avec correction des gaps Audit/Reco.",
        "depends_on_audit_engine": True,
        "required_inputs": ["client_slug", "page_type audite", "score_page_type.json", "recos_v13_final.json"],
        "canonical_entrypoint": "moteur_gsg.orchestrator.generate_lp(mode='replace')",
        "default_runtime": "moteur_gsg.modes.mode_2_replace",
        "status": "active_audit_bridge",
    },
    "extend": {
        "label": "Mode 3 EXTEND",
        "role": "Nouveau concept pour une marque existante.",
        "depends_on_audit_engine": False,
        "required_inputs": ["client_slug", "page_type", "concept", "BriefV2"],
        "canonical_entrypoint": "moteur_gsg.orchestrator.generate_lp(mode='extend')",
        "default_runtime": "moteur_gsg.modes.mode_3_extend",
        "status": "active_minimal_bridge",
    },
    "elevate": {
        "label": "Mode 4 ELEVATE",
        "role": "Alternative plus ambitieuse avec inspirations explicites.",
        "depends_on_audit_engine": False,
        "required_inputs": ["client_slug", "page_type", "inspiration_urls", "BriefV2"],
        "canonical_entrypoint": "moteur_gsg.orchestrator.generate_lp(mode='elevate')",
        "default_runtime": "moteur_gsg.modes.mode_4_elevate",
        "status": "active_minimal_bridge",
    },
    "genesis": {
        "label": "Mode 5 GENESIS",
        "role": "Brief seul, sans URL client existante.",
        "depends_on_audit_engine": False,
        "required_inputs": ["brand_name", "category", "audience", "offer", "cta_type", "proofs"],
        "canonical_entrypoint": "moteur_gsg.orchestrator.generate_lp(mode='genesis')",
        "default_runtime": "moteur_gsg.modes.mode_5_genesis",
        "status": "prototype_write_scope_warning",
    },
}


CANONICAL_LAYERS = [
    {
        "layer": "intake_wizard",
        "current_files": [
            "skills/gsg/SKILL.md",
            "moteur_gsg/core/intake_wizard.py",
            "scripts/run_gsg_full_pipeline.py",
            "scripts/check_gsg_intake_wizard.py",
        ],
        "decision": "active_raw_request_to_brief_v2_v27_2_e",
    },
    {
        "layer": "brief_v2",
        "current_files": [
            "moteur_gsg/core/brief_v2.py",
            "moteur_gsg/core/brief_v2_prefiller.py",
            "moteur_gsg/core/brief_v2_validator.py",
        ],
        "decision": "keep",
    },
    {
        "layer": "context_pack_read_only",
        "current_files": [
            "scripts/client_context.py",
            "moteur_gsg/core/context_pack.py",
            "moteur_gsg/core/brand_intelligence.py",
        ],
        "decision": "active_generation_context_pack_v27_2",
    },
    {
        "layer": "visual_intelligence",
        "current_files": [
            "moteur_gsg/core/visual_intelligence.py",
            "moteur_gsg/core/creative_route_selector.py",
            "moteur_gsg/core/component_library.py",
            "moteur_gsg/core/visual_system.py",
            "moteur_gsg/core/design_tokens.py",
            "skills/growth-site-generator/scripts/aura_compute.py",
            "skills/growth-site-generator/scripts/creative_director.py",
            "skills/growth-site-generator/scripts/golden_design_bridge.py",
        ],
        "decision": "active_contract_v27_2_aura_cd_golden_structural_inputs",
    },
    {
        "layer": "planner_deterministic",
        "current_files": [
            "data/layout_archetypes/*.json",
            "moteur_gsg/core/planner.py",
            "moteur_gsg/core/component_library.py",
            "moteur_gsg/core/pattern_library.py",
            "moteur_gsg/core/doctrine_planner.py",
            "skills/cro-library/references/patterns.json",
        ],
        "decision": "active_page_type_and_cro_pattern_contract_v27_2",
    },
    {
        "layer": "design_tokens",
        "current_files": [
            "moteur_gsg/core/design_tokens.py",
            "skills/growth-site-generator/scripts/aura_compute.py",
            "moteur_gsg/core/design_grammar_loader.py",
        ],
        "decision": "active_tokens_v27_2_aura_inputs_from_visual_intelligence",
    },
    {
        "layer": "bounded_copy_llm",
        "current_files": ["moteur_gsg/core/copy_writer.py", "moteur_gsg/core/prompt_assembly.py"],
        "decision": "active_guided_copy_engine_v27_2",
    },
    {
        "layer": "renderer_and_qa",
        "current_files": [
            "moteur_gsg/core/controlled_renderer.py",
            "moteur_gsg/core/visual_system.py",
            "moteur_gsg/modes/mode_1_complete.py",
            "moteur_multi_judge/orchestrator.py",
            "skills/growth-site-generator/scripts/fix_html_runtime.py",
        ],
        "decision": "active_native_renderer_with_real_capture_assets",
    },
]


CALL_GRAPH: list[dict[str, str]] = [
    {
        "from": "skills/gsg/SKILL.md",
        "to": "scripts/run_gsg_full_pipeline.py",
        "type": "documented_cli",
    },
    {
        "from": "raw user request / future webapp wizard",
        "to": "moteur_gsg/core/intake_wizard.py",
        "type": "deterministic_generation_request",
    },
    {
        "from": "moteur_gsg/core/intake_wizard.py",
        "to": "moteur_gsg/core/brief_v2_prefiller.py",
        "type": "prefill_brief_v2_from_root_context",
    },
    {
        "from": "scripts/run_gsg_full_pipeline.py",
        "to": "moteur_gsg.orchestrator.generate_lp",
        "type": "canonical_minimal_default",
    },
    {
        "from": "moteur_gsg.orchestrator.generate_lp",
        "to": "moteur_gsg/modes/mode_1_complete.py",
        "type": "mode_complete_default",
    },
    {
        "from": "moteur_gsg/modes/mode_1_complete.py",
        "to": "moteur_gsg/core/{context_pack,doctrine_planner,visual_intelligence,creative_route_selector,component_library,visual_system,planner,pattern_library,design_tokens,copy_writer,controlled_renderer}.py",
        "type": "controlled_default",
    },
    {
        "from": "moteur_gsg/core/visual_intelligence.py",
        "to": "moteur_gsg/core/creative_route_selector.py",
        "type": "structured_cd_golden_route_contract",
    },
    {
        "from": "moteur_gsg/core/creative_route_selector.py",
        "to": "moteur_gsg/core/legacy_lab_adapters.py:get_golden_design_benchmark",
        "type": "compact_golden_benchmark_no_prompt_dump",
    },
    {
        "from": "moteur_gsg/core/pipeline_single_pass.py",
        "to": "moteur_gsg/core/legacy_lab_adapters.py:apply_fix_html_runtime",
        "type": "explicit_adapter",
    },
    {
        "from": "moteur_gsg/modes/mode_1_complete.py",
        "to": "moteur_gsg/core/legacy_lab_adapters.py:creative_director",
        "type": "explicit_adapter_opt_in",
    },
    {
        "from": "moteur_multi_judge/judges/humanlike_judge.py",
        "to": "skills/growth-site-generator/scripts/gsg_humanlike_audit.py",
        "type": "legacy_wrapper_post_run_only",
    },
    {
        "from": "moteur_multi_judge/judges/implementation_check.py",
        "to": "skills/growth-site-generator/scripts/fix_html_runtime.py",
        "type": "legacy_wrapper_post_run_only",
    },
]


FREEZE_MATRIX: list[dict[str, str]] = [
    {
        "path": "skills/gsg/SKILL.md",
        "decision": "keep",
        "reason": "Unique public GSG skill.",
    },
    {
        "path": "moteur_gsg/",
        "decision": "keep",
        "reason": "Unique public engine/API.",
    },
    {
        "path": "skills/growth-site-generator/scripts/aura_compute.py",
        "decision": "migrate",
        "reason": "Turn into deterministic design tokens.",
    },
    {
        "path": "skills/growth-site-generator/scripts/creative_director.py",
        "decision": "migrate",
        "reason": "Keep route choice, remove prompt dumping.",
    },
    {
        "path": "skills/growth-site-generator/scripts/golden_design_bridge.py",
        "decision": "migrate",
        "reason": "Use selected patterns only.",
    },
    {
        "path": "skills/growth-site-generator/scripts/fix_html_runtime.py",
        "decision": "keep_adapter",
        "reason": "Runtime QA is useful and deterministic.",
    },
    {
        "path": "skills/growth-site-generator/scripts/gsg_generate_lp.py",
        "decision": "freeze",
        "reason": "Mega-prompt V26.Z public entrypoint is dangerous.",
    },
    {
        "path": "skills/growth-site-generator/scripts/gsg_multi_judge.py",
        "decision": "freeze",
        "reason": "Legacy eval_grid /135 replaced by moteur_multi_judge.",
    },
    {
        "path": "skills/mode-1-launcher/SKILL.md",
        "decision": "freeze",
        "reason": "Redundant with skills/gsg public skill.",
    },
    {
        "path": "moteur_gsg/core/brief_v15_builder.py",
        "decision": "mode2_only",
        "reason": "Audit bridge contract, not main GSG brief.",
    },
]


def build_canonical_snapshot() -> dict[str, Any]:
    """Return the full generation-free canonical GSG snapshot."""
    return {
        "product_name": "GSG",
        "public_skill": "skills/gsg/SKILL.md",
        "public_engine": "moteur_gsg",
        "legacy_lab": "skills/growth-site-generator/scripts",
        "public_modes": PUBLIC_MODES,
        "allowed_aliases": ALLOWED_ALIASES,
        "supported_modes_runtime": list_supported_modes(),
        "product_contract": PRODUCT_CONTRACT,
        "canonical_layers": CANONICAL_LAYERS,
        "freeze_matrix": FREEZE_MATRIX,
        "call_graph": CALL_GRAPH,
        "legacy_components": legacy_component_status(),
        "creative_route_selector": creative_route_selector_status(),
        "visual_system": visual_system_status(),
    }


def validate_canonical_contract() -> dict[str, Any]:
    """Validate static boundaries without generating HTML or calling LLMs."""
    errors: list[str] = []
    warnings: list[str] = []

    runtime_modes = set(list_supported_modes())
    missing = [m for m in PUBLIC_MODES if m not in runtime_modes]
    if missing:
        errors.append(f"Missing public modes in orchestrator: {missing}")

    extra_publicish = sorted(runtime_modes - set(PUBLIC_MODES) - set(ALLOWED_ALIASES))
    if extra_publicish:
        warnings.append(f"Unexpected extra modes in orchestrator: {extra_publicish}")

    if not (ROOT / "skills" / "gsg" / "SKILL.md").exists():
        errors.append("Missing active public skill: skills/gsg/SKILL.md")

    if (ROOT / "skills" / "growth-site-generator" / "SKILL.md").exists():
        errors.append("Legacy growth-site-generator has an active SKILL.md; archive or disable it.")

    pipeline_cli = ROOT / "scripts" / "run_gsg_full_pipeline.py"
    if not pipeline_cli.exists():
        errors.append("Missing scripts/run_gsg_full_pipeline.py")
    else:
        pipeline_text = pipeline_cli.read_text(errors="ignore")
        if "--request" not in pipeline_text:
            errors.append("run_gsg_full_pipeline.py must expose --request for raw GSG intake")
        if "--prepare-only" not in pipeline_text:
            errors.append("run_gsg_full_pipeline.py must expose --prepare-only for wizard preview")
        if "--generation-path" not in pipeline_text:
            errors.append("run_gsg_full_pipeline.py must expose --generation-path minimal|sequential")
        if "--generation-strategy" not in pipeline_text:
            errors.append("run_gsg_full_pipeline.py must expose --generation-strategy controlled|single_pass")

    intake = ROOT / "moteur_gsg" / "core" / "intake_wizard.py"
    if not intake.exists():
        errors.append("Missing moteur_gsg/core/intake_wizard.py")

    controlled_smoke = ROOT / "scripts" / "check_gsg_controlled_renderer.py"
    if not controlled_smoke.exists():
        errors.append("Missing scripts/check_gsg_controlled_renderer.py")
    component_smoke = ROOT / "scripts" / "check_gsg_component_planner.py"
    if not component_smoke.exists():
        errors.append("Missing scripts/check_gsg_component_planner.py")
    visual_smoke = ROOT / "scripts" / "check_gsg_visual_renderer.py"
    if not visual_smoke.exists():
        errors.append("Missing scripts/check_gsg_visual_renderer.py")
    route_smoke = ROOT / "scripts" / "check_gsg_creative_route_selector.py"
    if not route_smoke.exists():
        errors.append("Missing scripts/check_gsg_creative_route_selector.py")
    intake_smoke = ROOT / "scripts" / "check_gsg_intake_wizard.py"
    if not intake_smoke.exists():
        errors.append("Missing scripts/check_gsg_intake_wizard.py")

    for required in (
        ROOT / ".claude" / "docs" / "architecture" / "GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md",
        ROOT / "moteur_gsg" / "core" / "context_pack.py",
        ROOT / "moteur_gsg" / "core" / "intake_wizard.py",
        ROOT / "moteur_gsg" / "core" / "visual_intelligence.py",
        ROOT / "moteur_gsg" / "core" / "creative_route_selector.py",
        ROOT / "moteur_gsg" / "core" / "component_library.py",
        ROOT / "moteur_gsg" / "core" / "visual_system.py",
    ):
        if not required.exists():
            errors.append(f"Missing V27.2 GSG contract file: {required.relative_to(ROOT)}")

    mode2 = ROOT / "moteur_gsg" / "modes" / "mode_2_replace.py"
    if mode2.exists():
        text = mode2.read_text(errors="ignore")
        for required in ("score_page_type.json", "recos_v13_final.json"):
            if required not in text:
                errors.append(f"Mode 2 must explicitly require {required}")

    genesis = ROOT / "moteur_gsg" / "modes" / "mode_5_genesis.py"
    if genesis.exists() and '"data" / "captures"' in genesis.read_text(errors="ignore"):
        warnings.append("Mode 5 GENESIS still writes pseudo brand_dna under data/captures; isolate in next reconstruction sprint.")

    mode1_launcher = ROOT / "skills" / "mode-1-launcher" / "SKILL.md"
    if mode1_launcher.exists() and "FROZEN" not in mode1_launcher.read_text(errors="ignore"):
        warnings.append("skills/mode-1-launcher/SKILL.md exists and is not marked FROZEN.")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "snapshot": build_canonical_snapshot(),
    }


def format_markdown(snapshot: dict[str, Any] | None = None) -> str:
    """Render the canonical snapshot as compact markdown."""
    snap = snapshot or build_canonical_snapshot()
    lines = [
        "# GSG Canonical Snapshot",
        "",
        f"- Product name: `{snap['product_name']}`",
        f"- Public skill: `{snap['public_skill']}`",
        f"- Public engine: `{snap['public_engine']}`",
        f"- Legacy lab: `{snap['legacy_lab']}`",
        f"- Public modes: `{', '.join(snap['public_modes'])}`",
        "",
        "## Mode Contract",
    ]
    for mode in PUBLIC_MODES:
        item = snap["product_contract"][mode]
        audit = "yes" if item["depends_on_audit_engine"] else "no"
        lines.append(f"- `{mode}`: {item['role']} Audit dependency: {audit}. Status: `{item['status']}`.")

    lines.extend(["", "## Freeze / Migration Matrix"])
    for item in snap["freeze_matrix"]:
        lines.append(f"- `{item['decision']}` `{item['path']}` — {item['reason']}")

    lines.extend(["", "## Call Graph"])
    for edge in snap["call_graph"]:
        lines.append(f"- `{edge['from']}` -> `{edge['to']}` ({edge['type']})")

    lines.extend(["", "## Legacy Components"])
    for name, meta in snap["legacy_components"].items():
        exists = "exists" if meta["exists"] else "missing"
        lines.append(f"- `{name}`: `{meta['policy']}` -> `{meta['target']}` ({exists})")
    return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument("--validate", action="store_true", help="Validate and exit non-zero on errors.")
    args = parser.parse_args()

    report = validate_canonical_contract() if args.validate else {"snapshot": build_canonical_snapshot()}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if args.validate:
            print(f"Canonical GSG check: {'PASS' if report['ok'] else 'FAIL'}")
            for err in report["errors"]:
                print(f"ERROR: {err}")
            for warn in report["warnings"]:
                print(f"WARN: {warn}")
            print()
        print(format_markdown(report["snapshot"]))
    return 0 if not args.validate or report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
