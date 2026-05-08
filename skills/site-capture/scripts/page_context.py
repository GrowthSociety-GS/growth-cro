#!/usr/bin/env python3
"""
page_context.py — P11.5/P11.9 (V19) : PageContext threadé + contrats Pydantic 4 stages.

Le pipeline 14 stages existant écrit des JSON à chaque étape, chaque consumer
re-lit. Résultat : points de failure multiples, re-dérivations implicites,
dérives possibles.

Ce module consolide en :
  Stage 1 CAPTURE   → {page.html, spatial_v9, capture.json}
  Stage 2 ANALYZE   → {perception, intent, scoring_pillars, scoring_aggregate}
  Stage 3 RECO      → {prompts, recos}
  Stage 4 DASHBOARD → {aggregated fleet data}

Chaque stage reçoit un `PageContext` et enrichit ses champs via des
`PageContextStage` typés Pydantic. Les consommateurs downstream reçoivent un
objet typé, plus besoin de re-lire 5 JSONs par page.

Usage :
    ctx = PageContext(client="japhy", page_type="home")
    pipeline = Pipeline()
    pipeline.run(ctx)  # populate stages 1→4 dans ctx

    # OU stage par stage si resume partiel
    stage_capture.run(ctx)
    stage_analyze.run(ctx)
    # ...

Pour V20 SaaS : chaque stage est un microservice indépendant qui sérialise
PageContext en RPC. Stateless, scalable.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from pydantic import BaseModel, Field
    _HAS_PYDANTIC = True
except ImportError:
    # Fallback graceful si pydantic pas installé (dev)
    from dataclasses import dataclass, field

    _HAS_PYDANTIC = False

    def BaseModel():  # type: ignore
        return dict

    def Field(default=None, **kw):  # type: ignore
        return default


# ────────────────────────────────────────────────────────────────
# STAGE 1 : CAPTURE
# ────────────────────────────────────────────────────────────────

class CaptureStageResult(BaseModel):
    """Output de Stage 1 (ghost_capture + native_capture --html)."""

    url: str = ""
    captured_at: str = ""  # ISO timestamp
    engine: str = "ghost_cloud"  # ghost_cloud | ghost_local | brightdata | headed
    html_path: Optional[str] = None  # Path vers page.html
    spatial: dict = Field(default_factory=dict)  # spatial_v9.json content
    dom_pillars: dict = Field(default_factory=dict)  # capture.json — 6 piliers sémantiques
    screenshots: dict = Field(default_factory=dict)  # {viewport: path}
    phantom_filter_stats: dict = Field(default_factory=dict)  # P11.12 stats
    duration_ms: int = 0
    errors: list[str] = Field(default_factory=list)


# ────────────────────────────────────────────────────────────────
# STAGE 2 : ANALYZE (perception + intent + scoring)
# ────────────────────────────────────────────────────────────────

class AnalyzeStageResult(BaseModel):
    """Output de Stage 2 — perception DBSCAN + intent + 6 blocs scoring + overlays."""

    perception: dict = Field(default_factory=dict)  # perception_v13.json
    intent: dict = Field(default_factory=dict)  # client_intent.json (client-level)
    scoring_pillars: dict = Field(default_factory=dict)  # {pillar: score_*.json}
    scoring_aggregate: dict = Field(default_factory=dict)  # score_page_type.json
    overlays: dict = Field(default_factory=dict)  # {semantic, contextual, applicability}
    golden_differential: list[dict] = Field(default_factory=list)  # P11.2 directives
    scent_trail: dict = Field(default_factory=dict)  # P11.15 (cross-page continuity)


# ────────────────────────────────────────────────────────────────
# STAGE 3 : RECO
# ────────────────────────────────────────────────────────────────

class RecoStageResult(BaseModel):
    """Output de Stage 3 — reco_enricher prepare + API enrich."""

    prompts_count: int = 0
    recos: list[dict] = Field(default_factory=list)
    model: str = ""
    n_ok: int = 0
    n_fallback: int = 0
    n_skipped: int = 0
    tokens_total: int = 0
    grounding_avg_score: Optional[float] = None


# ────────────────────────────────────────────────────────────────
# STAGE 4 : DASHBOARD
# ────────────────────────────────────────────────────────────────

class DashboardContribution(BaseModel):
    """Partie de la page à inclure dans le dashboard data contract."""

    client_id: str = ""
    page_type: str = ""
    pillars_compact: dict = Field(default_factory=dict)
    priority_distribution: dict = Field(default_factory=dict)
    overlays_transparency: dict = Field(default_factory=dict)
    recos_compact: list[dict] = Field(default_factory=list)


# ────────────────────────────────────────────────────────────────
# PAGE CONTEXT (Le "thread")
# ────────────────────────────────────────────────────────────────

class PageContext(BaseModel):
    """Objet porté de bout en bout du pipeline. Chaque stage mute ses champs.

    Règle : un stage ne modifie QUE son stage_N_result et lit les précédents.
    Pas de side effect sur les fichiers disque — ça se fait via une serialization
    externe après chaque stage si besoin de caching.
    """

    # Identité
    client: str
    page_type: str
    business_type: Optional[str] = None
    category: Optional[str] = None

    # Environment
    captures_dir: str = ""  # Path absolute au dossier de la page

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    pipeline_version: str = "v19.0.0"

    # Stage outputs
    stage1_capture: Optional[CaptureStageResult] = None
    stage2_analyze: Optional[AnalyzeStageResult] = None
    stage3_reco: Optional[RecoStageResult] = None
    stage4_dashboard: Optional[DashboardContribution] = None

    # Debug / tracing
    stage_timings_ms: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    # P11.15 — cross-page (pour scent trail, populate par l'orchestrateur fleet-level)
    sibling_pages: list[str] = Field(default_factory=list)  # autres pageTypes du même client


# ────────────────────────────────────────────────────────────────
# PIPELINE STAGES (interfaces abstraites — implémentations à venir)
# ────────────────────────────────────────────────────────────────

class PipelineStage:
    """Interface abstraite d'un stage de pipeline.
    Chaque stage implémente `run(ctx: PageContext) -> None` qui mute le contexte.
    """

    name: str = "abstract"

    def run(self, ctx: PageContext) -> None:  # pragma: no cover
        raise NotImplementedError(f"Stage {self.name} must implement run()")


class Stage1Capture(PipelineStage):
    """Wraps ghost_capture_cloud + native_capture --html.

    TODO P11.9 : migrer ghost_capture_cloud.py vers cette abstraction.
    Pour V19, ce stage est un wrapper over les scripts existants.
    """

    name = "1_capture"


class Stage2Analyze(PipelineStage):
    """Wraps perception_v13 + intent_detector + score_page_type orchestrator.

    Consolide ce qui était 8+ scripts séparés (perception, intent, 6 blocs scorers,
    semantic_scorer, contextual_overlay, applicability_overlay, utility_banner,
    specific_criteria) en un seul pipeline typé.
    """

    name = "2_analyze"


class Stage3Reco(PipelineStage):
    """Wraps reco_enricher_v13 prepare + API enrich."""

    name = "3_reco"


class Stage4Dashboard(PipelineStage):
    """Wraps build_dashboard_v17 per-page contribution."""

    name = "4_dashboard"


class Pipeline:
    """Orchestrateur des 4 stages.

    Usage :
        pipeline = Pipeline()
        ctx = PageContext(client="japhy", page_type="home")
        pipeline.run(ctx)
        # ctx contient maintenant les 4 stage results

    Pour V20 SaaS : chaque stage devient un job Celery indépendant, PageContext
    sérialisé en Postgres JSONB entre les étapes.
    """

    def __init__(self, stages: Optional[list[PipelineStage]] = None) -> None:
        self.stages = stages or [
            Stage1Capture(),
            Stage2Analyze(),
            Stage3Reco(),
            Stage4Dashboard(),
        ]

    def run(self, ctx: PageContext, from_stage: int = 1, to_stage: int = 4) -> PageContext:
        """Lance les stages de `from_stage` à `to_stage` inclus.
        Permet le resume partiel (ex: re-run uniquement stage 3 après modif reco prompt).
        """
        for i, stage in enumerate(self.stages, start=1):
            if i < from_stage or i > to_stage:
                continue
            t0 = datetime.utcnow()
            try:
                stage.run(ctx)
            except Exception as e:
                ctx.warnings.append(f"stage_{i}_{stage.name}_error: {e}")
                raise
            finally:
                dt_ms = int((datetime.utcnow() - t0).total_seconds() * 1000)
                ctx.stage_timings_ms[stage.name] = dt_ms
        return ctx


# ────────────────────────────────────────────────────────────────
# HELPER : charge un PageContext depuis disque (migration)
# ────────────────────────────────────────────────────────────────

def load_page_context_from_disk(page_dir: Path, client: str, page_type: str) -> PageContext:
    """Construit un PageContext en lisant les fichiers JSON existants du pipeline V17.
    Pour migration progressive : les scripts existants écrivent les JSONs, ce helper
    les re-hydrate en PageContext typé.
    """
    import json

    def _safe_load(p: Path) -> dict:
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}

    ctx = PageContext(
        client=client,
        page_type=page_type,
        captures_dir=str(page_dir),
    )

    # Stage 1 hydration
    capture_json = _safe_load(page_dir / "capture.json")
    spatial_json = _safe_load(page_dir / "spatial_v9.json")
    if capture_json or spatial_json:
        ctx.stage1_capture = CaptureStageResult(
            url=capture_json.get("meta", {}).get("url", ""),
            captured_at=capture_json.get("meta", {}).get("capturedAt", ""),
            html_path=str(page_dir / "page.html") if (page_dir / "page.html").exists() else None,
            spatial=spatial_json,
            dom_pillars=capture_json,
        )

    # Stage 2 hydration
    perception = _safe_load(page_dir / "perception_v13.json")
    intent = _safe_load(page_dir.parent / "client_intent.json")  # client-level
    spt = _safe_load(page_dir / "score_page_type.json")
    pillars = {
        p: _safe_load(page_dir / f"score_{p}.json")
        for p in ["hero", "persuasion", "ux", "coherence", "psycho", "tech"]
    }
    overlays = {
        "semantic": spt.get("semantic_overlay") or {},
        "contextual": spt.get("contextual_overlay") or {},
        "applicability": spt.get("applicability_overlay") or {},
    }
    if perception or spt:
        ctx.stage2_analyze = AnalyzeStageResult(
            perception=perception,
            intent=intent,
            scoring_pillars=pillars,
            scoring_aggregate=spt,
            overlays=overlays,
        )

    # Stage 3 hydration
    recos_final = _safe_load(page_dir / "recos_v13_final.json")
    if recos_final:
        ctx.stage3_reco = RecoStageResult(
            prompts_count=recos_final.get("n_prompts", 0),
            recos=recos_final.get("recos", []),
            model=recos_final.get("model", ""),
            n_ok=recos_final.get("n_ok", 0),
            n_fallback=recos_final.get("n_fallback", 0),
            n_skipped=recos_final.get("n_skipped", 0),
            tokens_total=recos_final.get("tokens_total", 0),
            grounding_avg_score=recos_final.get("grounding_avg_score"),
        )

    return ctx


if __name__ == "__main__":
    # Smoke test
    import sys
    from pathlib import Path as _P

    if len(sys.argv) < 3:
        print("Usage: python3 page_context.py <client> <page>")
        sys.exit(1)

    client = sys.argv[1]
    page = sys.argv[2]
    root = _P(__file__).resolve().parents[3]
    page_dir = root / "data" / "captures" / client / page

    ctx = load_page_context_from_disk(page_dir, client, page)

    print(f"PageContext: {client}/{page}")
    print(f"  captures_dir: {ctx.captures_dir}")
    print(f"  stage1_capture: {'OK' if ctx.stage1_capture else 'missing'}")
    print(f"  stage2_analyze: {'OK' if ctx.stage2_analyze else 'missing'}")
    print(f"  stage3_reco: {'OK' if ctx.stage3_reco else 'missing'}")
    if ctx.stage3_reco:
        print(f"    n_ok={ctx.stage3_reco.n_ok}, n_fallback={ctx.stage3_reco.n_fallback}, n_skipped={ctx.stage3_reco.n_skipped}")
