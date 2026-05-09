#!/usr/bin/env python3
"""
api_server.py — API REST GrowthCRO (FastAPI).

Expose le pipeline de capture comme service HTTP.
Base pour l'outil interne et le futur SaaS.

Endpoints :
    POST /capture           Lancer une capture complète (ghost → parse → perception)
    GET  /capture/{label}   Récupérer les résultats d'un client
    GET  /captures          Lister tous les clients capturés
    GET  /health            Health check

Usage :
    # Dev (rechargement auto)
    uvicorn api_server:app --reload --port 8000

    # Prod
    python3 api_server.py

    # Docker
    docker run -p 8000:8000 -e BROWSER_WS_ENDPOINT=... -e ANTHROPIC_API_KEY=... growthcro

v1.0 — 2026-04-17
"""

import asyncio
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, HttpUrl

ROOT = pathlib.Path(__file__).resolve().parent
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
CAPTURES = ROOT / "data" / "captures"
GOLDEN = ROOT / "data" / "golden"
PYTHON_BIN = sys.executable

app = FastAPI(
    title="GrowthCRO API",
    description="Pipeline CRO automatisé : capture → scoring → recommandations",
    version="1.0.0",
)

# CORS (pour frontend futur)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════

class CaptureRequest(BaseModel):
    url: str
    label: str
    biz_category: str = "ecommerce"
    page_type: str = "home"
    cloud: bool = True  # Cloud mode by default for API
    skip_ghost: bool = False
    skip_capture: bool = False
    no_intent: bool = False


class CaptureStatus(BaseModel):
    label: str
    page_type: str
    status: str  # "pending", "running", "completed", "failed"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    artifacts: dict = {}


# In-memory job tracker (Redis en prod)
_jobs: dict[str, CaptureStatus] = {}


# ══════════════════════════════════════════════════════════════
# CAPTURE WORKER
# ══════════════════════════════════════════════════════════════

async def run_capture_pipeline(req: CaptureRequest, job_id: str):
    """Lance capture_full.py en subprocess async."""
    _jobs[job_id].status = "running"
    _jobs[job_id].started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    cmd = [
        PYTHON_BIN, str(ROOT / "capture_full.py"),
        req.url, req.label, req.biz_category,
        "--page-type", req.page_type,
    ]
    if req.cloud:
        cmd.append("--cloud")
    if req.skip_ghost:
        cmd.append("--skip-ghost")
    if req.skip_capture:
        cmd.append("--skip-capture")
    if req.no_intent:
        cmd.append("--no-intent")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        rc = proc.returncode

        if rc == 0:
            _jobs[job_id].status = "completed"
        else:
            _jobs[job_id].status = "failed"
            _jobs[job_id].error = f"exit={rc}"

    except asyncio.TimeoutError:
        _jobs[job_id].status = "failed"
        _jobs[job_id].error = "timeout (300s)"
    except Exception as e:
        _jobs[job_id].status = "failed"
        _jobs[job_id].error = str(e)[:200]

    _jobs[job_id].completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Collect artifacts
    page_dir = CAPTURES / req.label / req.page_type
    artifacts = {}
    for name in ["capture.json", "spatial_v9.json", "perception_v13.json", "page.html"]:
        f = page_dir / name
        if f.exists():
            artifacts[name] = {"exists": True, "size_kb": round(f.stat().st_size / 1024, 1)}
    screenshots = page_dir / "screenshots"
    if screenshots.exists():
        artifacts["screenshots"] = [p.name for p in screenshots.glob("*.png")]
    _jobs[job_id].artifacts = artifacts


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check."""
    has_ws = bool(config.browser_ws_endpoint())
    has_api_key = bool(config.anthropic_api_key())
    return {
        "status": "ok",
        "cloud_browser": "connected" if has_ws else "not configured",
        "anthropic_api": "configured" if has_api_key else "not configured",
        "captures_count": sum(1 for _ in CAPTURES.iterdir()) if CAPTURES.exists() else 0,
    }


@app.post("/capture")
async def start_capture(req: CaptureRequest, background_tasks: BackgroundTasks):
    """
    Lance une capture complète en arrière-plan.

    Retourne immédiatement un job_id à poller via GET /capture/status/{job_id}.
    """
    job_id = f"{req.label}_{req.page_type}_{int(time.time())}"

    _jobs[job_id] = CaptureStatus(
        label=req.label,
        page_type=req.page_type,
        status="pending",
    )

    background_tasks.add_task(run_capture_pipeline, req, job_id)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Capture lancée pour {req.label}/{req.page_type}",
        "poll_url": f"/capture/status/{job_id}",
    }


@app.get("/capture/status/{job_id}")
async def capture_status(job_id: str):
    """Statut d'un job de capture."""
    if job_id not in _jobs:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return _jobs[job_id]


@app.get("/captures")
async def list_captures():
    """Liste tous les clients capturés avec leurs pages."""
    if not CAPTURES.exists():
        return {"clients": [], "total": 0}

    clients = []
    for client_dir in sorted(CAPTURES.iterdir()):
        if not client_dir.is_dir():
            continue
        pages = []
        for page_dir in sorted(client_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            has_capture = (page_dir / "capture.json").exists()
            has_spatial = (page_dir / "spatial_v9.json").exists()
            has_perception = (page_dir / "perception_v13.json").exists()
            pages.append({
                "page_type": page_dir.name,
                "capture_json": has_capture,
                "spatial_v9": has_spatial,
                "perception_v13": has_perception,
            })
        if pages:
            clients.append({"label": client_dir.name, "pages": pages})

    return {"clients": clients, "total": len(clients)}


@app.get("/capture/{label}")
async def get_capture(label: str, page_type: str = "home"):
    """Récupère les données de capture d'un client."""
    page_dir = CAPTURES / label / page_type
    if not page_dir.exists():
        raise HTTPException(404, f"Capture '{label}/{page_type}' not found")

    result = {"label": label, "page_type": page_type}

    cap = page_dir / "capture.json"
    if cap.exists():
        result["capture"] = json.loads(cap.read_text())

    spatial = page_dir / "spatial_v9.json"
    if spatial.exists():
        result["spatial"] = json.loads(spatial.read_text())

    perception = page_dir / "perception_v13.json"
    if perception.exists():
        result["perception"] = json.loads(perception.read_text())

    return result


@app.get("/capture/{label}/screenshot/{filename}")
async def get_screenshot(label: str, filename: str, page_type: str = "home"):
    """Récupère un screenshot."""
    screenshot = CAPTURES / label / page_type / "screenshots" / filename
    if not screenshot.exists():
        raise HTTPException(404, f"Screenshot not found: {label}/{page_type}/{filename}")
    return FileResponse(screenshot, media_type="image/png")


# ══════════════════════════════════════════════════════════════
# BATCH ENDPOINT
# ══════════════════════════════════════════════════════════════

class BatchRequest(BaseModel):
    captures: list[CaptureRequest]
    concurrency: int = 3


@app.post("/batch")
async def start_batch(req: BatchRequest, background_tasks: BackgroundTasks):
    """Lance un batch de captures."""
    batch_id = f"batch_{int(time.time())}"
    job_ids = []

    for capture_req in req.captures:
        job_id = f"{capture_req.label}_{capture_req.page_type}_{int(time.time())}"
        _jobs[job_id] = CaptureStatus(
            label=capture_req.label,
            page_type=capture_req.page_type,
            status="pending",
        )
        background_tasks.add_task(run_capture_pipeline, capture_req, job_id)
        job_ids.append(job_id)

    return {
        "batch_id": batch_id,
        "job_ids": job_ids,
        "total": len(job_ids),
        "message": f"Batch de {len(job_ids)} captures lancé",
    }


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    port = config.port(default=8000)
    print(f"\n{'='*60}")
    print(f"GrowthCRO API Server v1.0")
    print(f"  Port: {port}")
    print(f"  Cloud browser: {'✅' if config.browser_ws_endpoint() else '❌ non configuré'}")
    print(f"  Anthropic API: {'✅' if config.anthropic_api_key() else '❌ non configuré'}")
    print(f"  Docs: http://localhost:{port}/docs")
    print(f"{'='*60}\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
