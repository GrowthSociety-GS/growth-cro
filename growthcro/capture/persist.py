"""Capture artifact serialization — single concern: write spatial_v9.json + capture.json + page.html.

No browser, no parsing logic — just pure I/O assemblers consumed by the
orchestrator (cloud capture) and the scorer (static parser). Both call
sites converge here to keep the on-disk schema in one place.
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any


def assemble_spatial_v9(*, url: str, label: str, page_type: str,
                        perception_tree: Any, stages: list,
                        errors: list, completeness: float) -> dict:
    """Build the spatial_v9.json payload (cloud capture artifact)."""
    final_capture = {
        "meta": (perception_tree or {}).get("meta", {
            "url": url,
            "label": label,
            "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "completeness": completeness,
        }),
        "stagesCompleted": stages,
        "errors": errors,
        **(perception_tree or {}),
    }
    # Enrich meta (preserve original behaviour)
    final_capture["meta"]["label"] = label
    final_capture["meta"]["pageType"] = page_type
    final_capture["meta"]["engine"] = "ghost_capture_cloud.py"
    final_capture["meta"]["completeness"] = completeness
    return final_capture


def write_spatial_v9(out_dir: pathlib.Path, payload: dict) -> pathlib.Path:
    """Persist spatial_v9.json. Returns the file path."""
    json_path = out_dir / "spatial_v9.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def write_html(out_dir: pathlib.Path, html: str) -> pathlib.Path:
    """Persist page.html (rendered DOM dump)."""
    html_path = out_dir / "page.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def write_capture_json(out_dir: pathlib.Path, payload: dict) -> pathlib.Path:
    """Persist capture.json (static-parser scorer artifact)."""
    cap_path = out_dir / "capture.json"
    cap_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return cap_path
