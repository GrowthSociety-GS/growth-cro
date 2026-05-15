"""Worker dispatcher — maps RunRow.type → CLI invocation + builds args.

Single concern : orchestration (run type → subprocess command). No I/O,
no Supabase calls — pure command builder + subprocess runner. The daemon
loop in `daemon.py` handles the Supabase coordination.

Source CLI signatures :
  - capture     : `python -m growthcro.capture.cli --url X --label Y --page-type Z --out-dir data/captures`
  - score       : `python -m growthcro.scoring.cli specific <label> <page>`
  - recos       : `python -m growthcro.recos.cli enrich --client X --page Y`
  - gsg         : `python -m moteur_gsg.orchestrator --mode <mode> --client X ...`
  - multi_judge : `python -m moteur_multi_judge.orchestrator --client X --page Y`
  - reality     : `python -m growthcro.reality.poller --client X` (NEW, task 011)
  - geo         : `python -m growthcro.geo --client X --engines all` (Task 009)
"""

from __future__ import annotations

import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAPTURES_DIR = REPO_ROOT / "data" / "captures"
SUBPROCESS_TIMEOUT_SEC = 600  # 10 min hard cap per run

# Mapping run.type → base CLI command. Args appended from RunRow.metadata_json.
RUN_TYPE_TO_CLI: dict[str, list[str]] = {
    "capture":     [sys.executable, "-m", "growthcro.capture.cli"],
    "score":       [sys.executable, "-m", "growthcro.scoring.cli", "specific"],
    "recos":       [sys.executable, "-m", "growthcro.recos.cli", "enrich"],
    "gsg":         [sys.executable, "-m", "moteur_gsg.orchestrator"],
    "multi_judge": [sys.executable, "-m", "moteur_multi_judge.orchestrator"],
    "reality":     [sys.executable, "-m", "growthcro.reality.poller"],
    "geo":         [sys.executable, "-m", "growthcro.geo"],
    # Legacy umbrellas — map to capture as default chain entry point
    "audit":       [sys.executable, "-m", "growthcro.capture.cli"],
    "experiment":  [sys.executable, "-c", "print('experiment dispatcher not implemented; see growthcro/experiments/')"],
}


@dataclass
class DispatchResult:
    """Outcome of a CLI subprocess invocation."""

    returncode: int
    stdout_tail: str  # last ~2KB
    stderr_tail: str
    duration_sec: float
    output_path: str | None = None  # absolute path to artefacts if known


def build_cli_command(run_type: str, metadata: dict[str, Any]) -> list[str]:
    """Compose the argv for a given run type + metadata.

    Args:
        run_type: one of RUN_TYPE_TO_CLI keys.
        metadata: dict from runs.metadata_json — contains the per-type args
            (client_slug, page_type, url, mode, etc.).

    Returns:
        argv list ready for subprocess.run.

    Raises:
        ValueError: if run_type is unknown.
    """
    if run_type not in RUN_TYPE_TO_CLI:
        raise ValueError(f"unknown run.type={run_type!r}; allowed={sorted(RUN_TYPE_TO_CLI)}")
    base = list(RUN_TYPE_TO_CLI[run_type])
    args = list(base)

    # Per-type arg mapping.
    if run_type in ("capture", "audit"):
        if url := metadata.get("url"):
            args += ["--url", str(url)]
        if client := metadata.get("client_slug"):
            args += ["--label", str(client)]
        if page := metadata.get("page_type"):
            args += ["--page-type", str(page)]
        args += ["--out-dir", str(DEFAULT_CAPTURES_DIR / str(metadata.get("client_slug", "unknown")))]

    elif run_type == "score":
        # `growthcro.scoring.cli specific <label> <page>` — positional
        if client := metadata.get("client_slug"):
            args.append(str(client))
        if page := metadata.get("page_type"):
            args.append(str(page))

    elif run_type == "recos":
        # `growthcro.recos.cli enrich --client X --page Y`
        if client := metadata.get("client_slug"):
            args += ["--client", str(client)]
        if page := metadata.get("page_type"):
            args += ["--page", str(page)]

    elif run_type == "gsg":
        if mode := metadata.get("mode"):
            args += ["--mode", str(mode)]
        if client := metadata.get("client_slug"):
            args += ["--client", str(client)]
        if page := metadata.get("page_type"):
            args += ["--page-type", str(page)]
        if objectif := metadata.get("objectif"):
            args += ["--objectif", str(objectif)]
        if audience := metadata.get("audience"):
            args += ["--audience", str(audience)]
        if angle := metadata.get("angle"):
            args += ["--angle", str(angle)]

    elif run_type == "multi_judge":
        if client := metadata.get("client_slug"):
            args += ["--client", str(client)]
        if page := metadata.get("page_type"):
            args += ["--page", str(page)]

    elif run_type == "reality":
        if client := metadata.get("client_slug"):
            args += ["--client", str(client)]
        if engine := metadata.get("engine"):
            args += ["--engine", str(engine)]

    elif run_type == "geo":
        if client := metadata.get("client_slug"):
            args += ["--client", str(client)]
        # Accept both `engines` (plural, spec) and `engine` (legacy singular).
        if engines := metadata.get("engines"):
            args += ["--engines", str(engines)]
        elif engine := metadata.get("engine"):
            args += ["--engines", str(engine)]
        if (limit := metadata.get("limit")) is not None:
            args += ["--limit", str(limit)]
        if brand := metadata.get("brand"):
            args += ["--brand", str(brand)]
        if keywords := metadata.get("keywords"):
            # Accept str or list — normalise to comma list.
            if isinstance(keywords, list):
                keywords = ",".join(str(k) for k in keywords)
            args += ["--keywords", str(keywords)]

    return args


def dispatch_run(run_type: str, metadata: dict[str, Any], *, timeout: int = SUBPROCESS_TIMEOUT_SEC) -> DispatchResult:
    """Execute the CLI for a given run type. Subprocess, captures output.

    Args:
        run_type: matching RUN_TYPE_TO_CLI key.
        metadata: dict of CLI args (client_slug, page_type, url, ...).
        timeout: subprocess hard cap in seconds.

    Returns:
        DispatchResult with returncode + stdout/stderr tail (~2KB each) +
        duration_sec.
    """
    argv = build_cli_command(run_type, metadata)
    cmd_str = " ".join(shlex.quote(a) for a in argv)
    logger.info(
        "dispatch_run start",
        extra={"run_type": run_type, "cmd": cmd_str, "metadata": metadata},
    )
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        duration = time.monotonic() - started
        logger.error(
            "dispatch_run timeout",
            extra={"run_type": run_type, "duration_sec": duration, "timeout": timeout},
        )
        return DispatchResult(
            returncode=124,
            stdout_tail=(e.stdout or b"").decode("utf-8", errors="replace")[-2000:] if isinstance(e.stdout, bytes) else (e.stdout or "")[-2000:],
            stderr_tail=f"subprocess.TimeoutExpired after {timeout}s",
            duration_sec=duration,
        )

    duration = time.monotonic() - started
    logger.info(
        "dispatch_run end",
        extra={"run_type": run_type, "returncode": proc.returncode, "duration_sec": round(duration, 2)},
    )
    return DispatchResult(
        returncode=proc.returncode,
        stdout_tail=(proc.stdout or "")[-2000:],
        stderr_tail=(proc.stderr or "")[-2000:],
        duration_sec=duration,
        output_path=_derive_output_path(run_type, metadata),
    )


def _derive_output_path(run_type: str, metadata: dict[str, Any]) -> str | None:
    """Best-effort derivation of where the CLI wrote its artefacts.

    Used to populate `runs.output_path` so the webapp UI can link back.
    """
    client = metadata.get("client_slug")
    page = metadata.get("page_type")
    if not client:
        return None
    base = DEFAULT_CAPTURES_DIR / str(client)
    if page:
        base = base / str(page)
    return str(base) if base.exists() else None
