#!/usr/bin/env python3
"""
perception_bridge.py — Bridge Layer 2 Perception → Scoring V3.

Consomme `components.json` et `critic_report.json` produits par le pipeline de
perception (Phase 5) et expose des helpers aux 6 scorers + reco_enricher.

Architecture : additif, non-bloquant (toutes les helpers retournent des valeurs
neutres si les artefacts sont absents). Les scorers importent via try/except
pour garder la rétro-compatibilité.

Usage :
    from perception_bridge import (
        load_perception,
        has_component, count_component, get_component,
        get_verdict, get_critic_violations,
        perception_signals,
    )

    p = load_perception(label="japhy", page_type="home", root=ROOT)
    if has_component(p, "hero_band"):
        ...
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional


# ─── Loaders ─────────────────────────────────────────────────────────

def _resolve_page_dir(label: str, page_type: Optional[str], root: pathlib.Path) -> pathlib.Path:
    """Retourne le dossier de capture, en gérant les layouts flat et multi-page."""
    if page_type:
        multi = root / "data" / "captures" / label / page_type
        if multi.exists():
            return multi
    # fallback flat
    flat = root / "data" / "captures" / label
    return flat


def load_components(label: str, page_type: Optional[str], root: pathlib.Path) -> Dict[str, Any]:
    """Charge components.json si présent, sinon retourne un dict vide neutre."""
    page_dir = _resolve_page_dir(label, page_type, root)
    path = page_dir / "components.json"
    if not path.exists():
        return {"_available": False, "components": [], "unclassified_sections": []}
    try:
        data = json.loads(path.read_text())
        data["_available"] = True
        return data
    except Exception as e:
        return {"_available": False, "_error": str(e), "components": [], "unclassified_sections": []}


def load_critic(label: str, page_type: Optional[str], root: pathlib.Path) -> Dict[str, Any]:
    """Charge critic_report.json si présent, sinon retourne un dict vide neutre."""
    page_dir = _resolve_page_dir(label, page_type, root)
    path = page_dir / "critic_report.json"
    if not path.exists():
        return {"_available": False, "verdict": "UNKNOWN", "violations": [], "severity_counts": {}}
    try:
        data = json.loads(path.read_text())
        data["_available"] = True
        return data
    except Exception as e:
        return {"_available": False, "_error": str(e), "verdict": "UNKNOWN", "violations": [], "severity_counts": {}}


def load_perception(label: str, page_type: Optional[str], root: pathlib.Path) -> Dict[str, Any]:
    """Charge components + critic en un seul appel. Forme standard consommée par les scorers."""
    components = load_components(label, page_type, root)
    critic = load_critic(label, page_type, root)
    return {
        "_available": components.get("_available") or critic.get("_available") or False,
        "components": components,
        "critic": critic,
    }


# ─── Component helpers ───────────────────────────────────────────────

def _components_list(perception: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Retourne la liste des components détectés (toujours une liste, même si absente)."""
    if "components" in perception and isinstance(perception.get("components"), dict):
        # shape from load_perception()
        return perception["components"].get("components", []) or []
    # shape from load_components() directly
    return perception.get("components", []) or []


def has_component(perception: Dict[str, Any], type_name: str, min_confidence: float = 0.0) -> bool:
    """True si au moins un component du type demandé est détecté (avec conf >= min)."""
    for c in _components_list(perception):
        if c.get("type") == type_name and (c.get("confidence") or 0) >= min_confidence:
            return True
    return False


def count_component(perception: Dict[str, Any], type_name: str, min_confidence: float = 0.0) -> int:
    """Compte les occurrences d'un type de component."""
    return sum(
        1
        for c in _components_list(perception)
        if c.get("type") == type_name and (c.get("confidence") or 0) >= min_confidence
    )


def get_component(perception: Dict[str, Any], type_name: str) -> Optional[Dict[str, Any]]:
    """Retourne le premier component du type demandé (ou None)."""
    for c in _components_list(perception):
        if c.get("type") == type_name:
            return c
    return None


def get_components(perception: Dict[str, Any], type_name: str) -> List[Dict[str, Any]]:
    """Retourne tous les components du type demandé (liste, peut être vide)."""
    return [c for c in _components_list(perception) if c.get("type") == type_name]


def component_types_present(perception: Dict[str, Any]) -> List[str]:
    """Retourne la liste unique des types de components présents."""
    return sorted({c.get("type") for c in _components_list(perception) if c.get("type")})


def component_atf(perception: Dict[str, Any]) -> List[str]:
    """Types présents dans la zone ATF (y < 360)."""
    return sorted({
        c.get("type")
        for c in _components_list(perception)
        if c.get("atf") and c.get("type")
    })


# ─── Critic helpers ──────────────────────────────────────────────────

def _critic_dict(perception: Dict[str, Any]) -> Dict[str, Any]:
    if "critic" in perception and isinstance(perception.get("critic"), dict):
        return perception["critic"]
    return perception


def get_verdict(perception: Dict[str, Any]) -> str:
    """OK | DEGRADED | BLOCKED | UNKNOWN."""
    return _critic_dict(perception).get("verdict", "UNKNOWN")


def get_critic_violations(perception: Dict[str, Any], severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Liste des violations critic. Filtrage par severity optionnel (CRITICAL/WARNING/INFO)."""
    violations = _critic_dict(perception).get("violations", []) or []
    if severity:
        sev = severity.upper()
        violations = [v for v in violations if (v.get("severity") or "").upper() == sev]
    return violations


def has_violation(perception: Dict[str, Any], rule_code: str) -> bool:
    """True si une violation critic avec ce code (ex: C1, W2) est active."""
    for v in _critic_dict(perception).get("violations", []) or []:
        if (v.get("code") or "").upper() == rule_code.upper():
            return True
    return False


# ─── Evidence builders (pour les scorers) ────────────────────────────

def perception_signals(perception: Dict[str, Any]) -> Dict[str, Any]:
    """Retourne un dict compact d'evidence prêt à merger dans un evidence scorer.

    Clés préfixées `pc_` pour ne pas collisionner avec spatial (`sp_`) ou DOM.
    """
    if not perception.get("_available"):
        return {"pc_available": False}
    comps = _components_list(perception)
    critic = _critic_dict(perception)
    return {
        "pc_available": True,
        "pc_verdict": critic.get("verdict", "UNKNOWN"),
        "pc_num_components": len(comps),
        "pc_types": component_types_present(perception),
        "pc_atf_types": component_atf(perception),
        "pc_classification_rate": critic.get("classification_rate_pct"),
        "pc_violations_count": len(critic.get("violations", []) or []),
        "pc_has_hero": has_component(perception, "hero_band"),
        "pc_has_nav": has_component(perception, "nav_bar"),
        "pc_has_footer": has_component(perception, "footer"),
        "pc_has_social_proof": (
            has_component(perception, "social_proof_logos")
            or has_component(perception, "testimonial_block")
        ),
        "pc_num_cta_bands": count_component(perception, "cta_band"),
        "pc_num_value_prop": count_component(perception, "value_prop_stack"),
        "pc_has_pricing": has_component(perception, "pricing_tiers"),
        "pc_has_faq": has_component(perception, "faq_accordion"),
        "pc_has_form": has_component(perception, "form_block"),
        "pc_has_video": has_component(perception, "video_block"),
    }


# ─── CLI debug ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: perception_bridge.py <label> [page_type]", file=sys.stderr)
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    root = pathlib.Path(__file__).resolve().parents[3]
    perception = load_perception(label, page_type, root)
    signals = perception_signals(perception)
    print(json.dumps(signals, indent=2, ensure_ascii=False))
