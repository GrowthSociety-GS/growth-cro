#!/usr/bin/env python3
"""
spatial_bridge.py — Bridge module entre spatial_v9.json et les 6 scorers existants.

Fournit une API simple pour que chaque scorer charge et utilise les données spatiales V9
sans dupliquer le code de chargement/vérification.

Usage dans un scorer :
    from spatial_bridge import load_spatial, get_spatial_evidence

    spatial = load_spatial(label, page_type)   # charge spatial_v9.json si disponible
    sp_ev = get_spatial_evidence("hero", spatial)  # dict sp_* clés pour le pilier

Les clés retournées sont préfixées 'sp_' pour merge sûr dans l'evidence existante.
Si spatial_v9.json n'existe pas, toutes les fonctions retournent des dicts/valeurs vides
→ dégradation gracieuse, 0 impact sur les scores existants.

v1.0 — 2026-04-12
"""

import json
import pathlib
from typing import Dict, Any, Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS = pathlib.Path(__file__).resolve().parent

# Import spatial_scoring (pure functions, no I/O)
import sys
sys.path.insert(0, str(SCRIPTS))
try:
    from spatial_scoring import (
        is_v9_capture,
        enrich_hero_spatial,
        enrich_ux_spatial,
        enrich_persuasion_spatial,
        enrich_coherence_spatial,
        enrich_psycho_spatial,
        enrich_tech_spatial,
        compute_spatial_score,
        analyze_arc_narrative,
    )
    HAS_SPATIAL_SCORING = True
except ImportError:
    HAS_SPATIAL_SCORING = False


def load_spatial(label: str, page_type: str = "home") -> Optional[Dict[str, Any]]:
    """
    Charge spatial_v9.json pour un client/page.
    Retourne le dict complet ou None si le fichier n'existe pas.
    """
    spatial_path = ROOT / "data" / "captures" / label / page_type / "spatial_v9.json"
    if not spatial_path.exists():
        return None
    try:
        data = json.loads(spatial_path.read_text())
        # Quick validation: must have sections
        if not isinstance(data.get("sections"), list):
            return None
        return data
    except (json.JSONDecodeError, IOError):
        return None


def get_spatial_evidence(pillar: str, spatial: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Retourne un dict de clés sp_* pour un pilier donné.
    Si spatial est None ou spatial_scoring indisponible, retourne {}.

    pillar: "hero" | "ux" | "persuasion" | "coherence" | "psycho" | "tech"
    """
    if not spatial or not HAS_SPATIAL_SCORING:
        return {}

    ENRICHERS = {
        "hero": enrich_hero_spatial,
        "ux": enrich_ux_spatial,
        "persuasion": enrich_persuasion_spatial,
        "coherence": enrich_coherence_spatial,
        "psycho": enrich_psycho_spatial,
        "tech": enrich_tech_spatial,
    }

    enricher = ENRICHERS.get(pillar)
    if not enricher:
        return {}

    try:
        return enricher(spatial)
    except Exception:
        return {}


def get_spatial_score(spatial: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Retourne le score spatial composite (0-100) ou None si pas de données.
    """
    if not spatial or not HAS_SPATIAL_SCORING:
        return None
    try:
        return compute_spatial_score(spatial)
    except Exception:
        return None


def get_arc_narrative(spatial: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Retourne l'analyse arc narratif ou None.
    """
    if not spatial or not HAS_SPATIAL_SCORING:
        return None
    try:
        return analyze_arc_narrative(spatial)
    except Exception:
        return None


def has_spatial(label: str, page_type: str = "home") -> bool:
    """Check if spatial data exists for a client/page."""
    return (ROOT / "data" / "captures" / label / page_type / "spatial_v9.json").exists()


def spatial_summary(spatial: Optional[Dict[str, Any]]) -> str:
    """One-line summary for logging."""
    if not spatial:
        return "no spatial data"
    n_sections = len(spatial.get("sections", []))
    completeness = spatial.get("meta", {}).get("completeness", 0)
    return f"V9 spatial: {n_sections} sections, completeness={completeness}"
