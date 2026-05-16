"""moteur_gsg.creative_engine — Creative Exploration Engine (epic gsg-creative-renaissance, CR-01).

Calls Claude Opus 4.7 to imagine 3–5 bold creative directions for a given
LP context (brief V2 + Brand DNA + Design Grammar + page_type + business
category) and writes the typed ``CreativeRouteBatch`` to disk for the
downstream Visual Judge (CR-02) and Visual Composer (CR-04) to consume.

Public API:

    from moteur_gsg.creative_engine import (
        CreativeRoute,
        CreativeRouteBatch,
        RouteThesis,
        CreativeEngineError,
        explore_routes,
        save_creative_routes,
        load_creative_routes,
        creative_routes_path,
    )

Architecture (mono-concern, 4 axes — cf. ``docs/doctrine/CODE_DOCTRINE.md``):

- ``orchestrator.py`` — ORCHESTRATION axis. Builds the Opus system prompt
  (4 sections, hard limit 8000 chars) and parses the JSON output via the
  shared ``recos.schema.extract_json_from_response`` helper. Retries once
  via Sonnet self-correction if the first parse fails. Never falls back
  to synthetic routes — raises ``CreativeEngineError`` on second failure
  so the caller can surface the upstream issue (V26.A invariant: no fake
  outputs in the typed pipeline).
- ``persist.py`` — PERSISTENCE axis. Atomic tmpfile + ``os.replace`` write
  to ``data/captures/<client>/<page>/creative_routes.json``.
- ``cli.py`` — CLI axis. ``python3 -m moteur_gsg.creative_engine.cli
  explore --client <slug> --page <page_type>``.
- (TYPING lives in ``growthcro.models.creative_models`` — pinned in
  commit 1 of CR-01 so CR-02/CR-03 unblock without waiting for this.)
"""
from __future__ import annotations

from growthcro.models.creative_models import (
    BusinessCategory,
    CreativeRoute,
    CreativeRouteBatch,
    RouteThesis,
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
)

from moteur_gsg.creative_engine.orchestrator import (
    CreativeEngineError,
    explore_routes,
)
from moteur_gsg.creative_engine.persist import (
    creative_routes_path,
    load_creative_routes,
    save_creative_routes,
)

__all__ = [
    "BusinessCategory",
    "CreativeEngineError",
    "CreativeRoute",
    "CreativeRouteBatch",
    "RouteThesis",
    "SYSTEM_PROMPT_HARD_LIMIT_CHARS",
    "creative_routes_path",
    "explore_routes",
    "load_creative_routes",
    "save_creative_routes",
]
