"""Explicit adapters for the V26.Z growth-site-generator legacy lab.

The canonical GSG engine lives in `moteur_gsg`. A few useful components still
live in `skills/growth-site-generator/scripts` while they are migrated. This
module is the only sanctioned bridge from the canonical engine to that lab:
all imports are explicit, typed at the boundary, and fail soft unless the caller
chooses to surface the error.
"""
from __future__ import annotations

import importlib.util
import contextlib
import io
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEGACY_LAB = ROOT / "skills" / "growth-site-generator" / "scripts"


class LegacyLabUnavailable(RuntimeError):
    """Raised when a legacy lab component cannot be loaded."""


LEGACY_COMPONENTS: dict[str, dict[str, str]] = {
    "aura_compute.py": {
        "policy": "migrate",
        "target": "moteur_gsg/core/design_tokens.py",
        "reason": "AURA should become computed tokens, not a prompt blob.",
    },
    "creative_director.py": {
        "policy": "migrate",
        "target": "moteur_gsg/core/planner.py",
        "reason": "Keep route selection, remove mega-prompt coupling.",
    },
    "golden_design_bridge.py": {
        "policy": "migrate",
        "target": "moteur_gsg/core/pattern_library.py",
        "reason": "Keep selected patterns, never dump the full reference library.",
    },
    "fix_html_runtime.py": {
        "policy": "keep_adapter",
        "target": "moteur_gsg/core/qa_runtime.py",
        "reason": "Useful deterministic implementation check until native port.",
    },
    "gsg_humanlike_audit.py": {
        "policy": "keep_adapter",
        "target": "moteur_multi_judge/judges/humanlike_judge.py",
        "reason": "Useful post-run judge, never a generation gate.",
    },
    "gsg_generate_lp.py": {
        "policy": "freeze_entrypoint",
        "target": "none",
        "reason": "Mega-prompt V26.Z lab. Must not be public GSG entrypoint.",
    },
    "gsg_multi_judge.py": {
        "policy": "freeze_entrypoint",
        "target": "moteur_multi_judge/orchestrator.py",
        "reason": "Legacy eval_grid /135 parallel judge replaced by doctrine V3.2.",
    },
    "gsg_pipeline_sequential.py": {
        "policy": "freeze_entrypoint",
        "target": "moteur_gsg/core/pipeline_sequential.py",
        "reason": "Useful forensic stage idea, not default runtime.",
    },
    "gsg_best_of_n.py": {
        "policy": "freeze_entrypoint",
        "target": "moteur_gsg/core/best_of_n.py",
        "reason": "Good concept, but must be rebuilt on canonical prompts/judges.",
    },
}


def legacy_script_path(script_name: str) -> pathlib.Path:
    """Return the absolute path for a known legacy lab script."""
    return LEGACY_LAB / script_name


def legacy_component_status() -> dict[str, dict[str, Any]]:
    """Inventory of known lab components and their canonical migration policy."""
    status: dict[str, dict[str, Any]] = {}
    for script_name, meta in LEGACY_COMPONENTS.items():
        fp = legacy_script_path(script_name)
        status[script_name] = {
            **meta,
            "path": str(fp.relative_to(ROOT)) if fp.exists() else str(fp),
            "exists": fp.exists(),
        }
    return status


def load_legacy_module(script_name: str, module_alias: str | None = None):
    """Load a legacy script as a module through one explicit adapter point."""
    fp = legacy_script_path(script_name)
    if not fp.exists():
        raise LegacyLabUnavailable(f"{script_name} not found at {fp}")

    alias = module_alias or f"growthcro_legacy_{pathlib.Path(script_name).stem}"
    spec = importlib.util.spec_from_file_location(alias, fp)
    if not spec or not spec.loader:
        raise LegacyLabUnavailable(f"Cannot load import spec for {script_name}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def apply_fix_html_runtime(
    html: str,
    *,
    inject_js: bool = False,
    fix_reveal_pattern: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Run the legacy runtime HTML fixer behind a stable canonical API."""
    mod = load_legacy_module("fix_html_runtime.py", "growthcro_legacy_fix_html_runtime")
    if not hasattr(mod, "fix_html_runtime"):
        raise LegacyLabUnavailable("fix_html_runtime.py has no fix_html_runtime()")
    fixed, report = mod.fix_html_runtime(
        html,
        inject_js=inject_js,
        fix_reveal_pattern=fix_reveal_pattern,
    )
    return fixed, report if isinstance(report, dict) else {"report": report}


def generate_creative_routes(
    *,
    client: str,
    page_type: str,
    brand_dna: dict[str, Any],
    design_grammar: dict[str, Any] | None,
    business_context: str,
    target_url: str = "",
    verbose: bool = True,
) -> dict[str, Any]:
    """Call the legacy Creative Director route generator via explicit adapter."""
    mod = load_legacy_module("creative_director.py", "growthcro_legacy_creative_director")
    if not hasattr(mod, "generate_routes"):
        raise LegacyLabUnavailable("creative_director.py has no generate_routes()")
    return mod.generate_routes(
        brand_dna,
        design_grammar or {},
        business_context,
        page_type,
        client,
        target_url=target_url,
        verbose=verbose,
    )


def select_creative_route(
    *,
    routes_data: dict[str, Any],
    brand_dna: dict[str, Any],
    business_context: str,
    mode: str = "auto",
    custom_route_file: pathlib.Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Call the legacy Creative Director route selector via explicit adapter."""
    mod = load_legacy_module("creative_director.py", "growthcro_legacy_creative_director")
    if not hasattr(mod, "select_route"):
        raise LegacyLabUnavailable("creative_director.py has no select_route()")
    return mod.select_route(
        routes_data,
        brand_dna,
        business_context,
        mode=mode,
        custom_route_path=custom_route_file,
        verbose=verbose,
    )


def render_creative_route_block(
    route: dict[str, Any],
    selection_meta: dict[str, Any] | None = None,
) -> str:
    """Render a selected route as the compact prompt block used by Mode 1."""
    mod = load_legacy_module("creative_director.py", "growthcro_legacy_creative_director")
    if not hasattr(mod, "render_creative_route_block"):
        raise LegacyLabUnavailable("creative_director.py has no render_creative_route_block()")
    return mod.render_creative_route_block(route, selection_meta)


def get_golden_design_benchmark(target_vector: dict[str, Any]) -> dict[str, Any]:
    """Return selected Golden Bridge references for a target aesthetic vector."""
    mod = load_legacy_module("golden_design_bridge.py", "growthcro_legacy_golden_design_bridge")
    if not hasattr(mod, "GoldenDesignBridge"):
        raise LegacyLabUnavailable("golden_design_bridge.py has no GoldenDesignBridge")
    # The legacy constructor prints inventory stats. Suppress that noise here:
    # the canonical engine should return structured telemetry, not stdout blobs.
    with contextlib.redirect_stdout(io.StringIO()):
        bridge = mod.GoldenDesignBridge()
        return bridge.get_design_benchmark(target_vector)
