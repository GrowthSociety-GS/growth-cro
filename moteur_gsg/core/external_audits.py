"""External audit subprocess wrappers — V27.2-L Sprint 20 (T20-1/2).

Wraps the Node.js subprocess audits (axe-core a11y + lighthouse perf)
behind clean Python interfaces. Each function takes a path to an HTML
file, spawns the subprocess, parses the JSON output line, returns a
normalized dict.

Both wrappers return a defensive fallback dict (score=None, error
message) when the subprocess fails — no exception ever propagates to
the pipeline. Mathis 2026-05-15 *"qualité > vitesse"* — if a11y or
perf audits are unavailable, the pipeline should still produce HTML
and surface the failure visibly in the run summary.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parent.parent.parent
_A11Y_SCRIPT = _ROOT / "scripts" / "a11y_audit.js"
_PERF_SCRIPT = _ROOT / "scripts" / "perf_audit.js"


def _run_node_audit(script_path: Path, html_path: str, timeout_s: int) -> dict[str, Any]:
    """Run a Node.js audit subprocess and parse its single JSON line."""
    if not script_path.is_file():
        return {"error": f"audit script not found: {script_path}", "score": None, "passed": False}
    node_bin = shutil.which("node")
    if not node_bin:
        return {"error": "node binary not found in PATH", "score": None, "passed": False}
    try:
        proc = subprocess.run(
            [node_bin, str(script_path), html_path],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(_ROOT),
        )
    except subprocess.TimeoutExpired:
        return {"error": f"audit timed out after {timeout_s}s", "score": None, "passed": False}
    except Exception as exc:
        return {"error": f"subprocess failed: {exc}", "score": None, "passed": False}

    # The script prints a single JSON line on stdout. Pick the last line
    # that parses as JSON (some npm packages emit warnings on stdout).
    stdout_lines = (proc.stdout or "").splitlines()
    for line in reversed(stdout_lines):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    stderr_tail = (proc.stderr or "")[-300:]
    return {
        "error": f"no JSON output found. exit={proc.returncode}. stderr={stderr_tail}",
        "score": None,
        "passed": False,
    }


def run_a11y_audit(html_path: str, timeout_s: int = 90) -> dict[str, Any]:
    """Run the axe-core WCAG2A+AA scan on the rendered HTML.

    Returns:
      {version, score(0-100), passed(bool), violations[], n_violations,
       n_passes, n_incomplete}
    """
    return _run_node_audit(_A11Y_SCRIPT, html_path, timeout_s)


def run_perf_audit(html_path: str, timeout_s: int = 180) -> dict[str, Any]:
    """Run the Lighthouse performance audit on the rendered HTML.

    Returns:
      {version, score(0-100), perf_score(0-1), passed, lcp_ms, cls,
       tbt_ms, fcp_ms, si_ms}
    """
    return _run_node_audit(_PERF_SCRIPT, html_path, timeout_s)


__all__ = ["run_a11y_audit", "run_perf_audit"]
