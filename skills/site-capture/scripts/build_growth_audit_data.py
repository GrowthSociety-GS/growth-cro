#!/usr/bin/env python3
"""
build_growth_audit_data.py — Build data consolidé pour `GrowthCRO-V26-WebApp.html`.

Assemble par client : métadonnées + pages + recos V13 + criterion_crops
(y_start/y_end/highlights) + chemins relatifs vers screenshots.

Output : deliverables/growth_audit_data.js (window.GROWTH_AUDIT_DATA = {...})

Ne embed PAS les screenshots (trop gros). Les images sont chargées via paths
relatifs `../data/captures/.../screenshots/*.png` quand l'HTML est ouvert
en file:// dans un browser.
"""
from __future__ import annotations

import json
import pathlib
from collections import defaultdict
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"
CLIENTS_DB = ROOT / "data" / "clients_database.json"
CURATED_PANEL_V27 = ROOT / "data" / "curated_clients_v27.json"
CURATED_PANEL_V26 = ROOT / "data" / "curated_clients_v26.json"
OUT = ROOT / "deliverables" / "growth_audit_data.js"
LEARNING_DIR = ROOT / "data" / "learning"


def load_clients_db() -> dict:
    if not CLIENTS_DB.exists():
        return {}
    db = json.loads(CLIENTS_DB.read_text())
    clients = db.get("clients") if isinstance(db, dict) else db
    if isinstance(clients, list):
        return {c.get("id"): c for c in clients}
    return clients or {}


def load_curated_panel() -> tuple[list[dict], dict]:
    panel_path = CURATED_PANEL_V27 if CURATED_PANEL_V27.exists() else CURATED_PANEL_V26
    if not panel_path.exists():
        return [], {}
    raw = json.loads(panel_path.read_text())
    clients = raw.get("clients") if isinstance(raw, dict) else raw
    entries = []
    seen = set()
    for item in clients or []:
        if isinstance(item, str):
            entry = {"id": item}
        elif isinstance(item, dict):
            entry = dict(item)
        else:
            continue
        client_id = entry.get("id") or entry.get("client_id") or entry.get("slug")
        if not client_id or client_id in seen:
            continue
        entry["id"] = client_id
        entries.append(entry)
        seen.add(client_id)
    meta = {
        "path": str(panel_path.relative_to(ROOT)),
        "version": raw.get("version") if isinstance(raw, dict) else "",
        "status": raw.get("status") if isinstance(raw, dict) else "",
        "note": raw.get("note") if isinstance(raw, dict) else "",
        "role_counts": ((raw.get("fleet") or {}).get("role_counts") or (raw.get("meta") or {}).get("role_counts") or {}) if isinstance(raw, dict) else {},
        "status_counts": ((raw.get("fleet") or {}).get("status_counts") or (raw.get("meta") or {}).get("status_counts") or {}) if isinstance(raw, dict) else {},
        "created_from_declared_fleet": (raw.get("meta") or {}).get("created_from_declared_fleet") if isinstance(raw, dict) else {},
        "declared_fleet": raw.get("fleet") if isinstance(raw, dict) else {},
    }
    return entries, meta


def safe_load(p: pathlib.Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def status_block(status: str, count: int = 0, total: int | None = None, note: str = "") -> dict:
    """Small, explicit status object for the static observatory."""
    out = {"status": status, "count": count, "note": note}
    if total is not None:
        out["total"] = total
    return out


def reality_has_active_connector(reality: dict | None) -> bool:
    """Treat Reality as active only when at least one connector returned data."""
    if not isinstance(reality, dict):
        return False
    active = ((reality.get("computed") or {}).get("active_connectors") or [])
    if active:
        return True
    sources = reality.get("sources") or {}
    return any(isinstance(v, dict) and not v.get("error") for v in sources.values())


# Glossaire jargon → langue claire (P11.17 reco simplification)
JARGON_MAP = {
    r"\bATF\b": "zone visible sans scroller",
    r"\babove[- ]the[- ]fold\b": "zone visible au chargement",
    r"\bfold\b": "ligne de flottaison",
    r"\bCTA\b": "bouton d'action",
    r"\bUGC\b": "contenu créé par les clients",
    r"\bLCP\b": "temps de chargement visuel",
    r"\bCLS\b": "stabilité visuelle",
    r"\bINP\b": "réactivité au clic",
    r"\bAOV\b": "panier moyen",
    r"\bMQL\b": "prospect qualifié marketing",
    r"\bSQL\b": "prospect qualifié commercial",
    r"\bthumb zone\b": "zone accessible au pouce",
    r"\bbbox\b": "zone de l'élément",
    r"\bviewport\b": "écran visible",
    r"\bz[- ]index\b": "superposition visuelle",
    r"\bHick[- ]Hyman\b": "loi du nombre limité de choix",
    r"\bscent trail\b": "fil de continuité du funnel",
    r"\bnear[- ]CTA\b": "près du bouton d'action",
    r"\bWCAG\b": "norme accessibilité web",
    r"\boverlay\b": "calque par-dessus",
}


def declutter_jargon(text: str) -> str:
    """Remplace les termes techniques par du français clair."""
    import re
    result = text or ""
    for pattern, replacement in JARGON_MAP.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _load_crops_v2(page_dir: pathlib.Path, viewport: str) -> dict:
    """Load criterion_crops_v2_<viewport>.json if present, else fallback V17 crops."""
    v2_path = page_dir / f"criterion_crops_v2_{viewport}.json"
    if v2_path.exists():
        d = safe_load(v2_path)
        return d.get("crops", {}) or {}
    # Fallback : V17 crops from capture.json (desktop only — mobile has none in V17)
    if viewport == "desktop":
        capture = safe_load(page_dir / "capture.json")
        return capture.get("criterion_crops", {}) or {}
    return {}


def _load_vision_meta(page_dir: pathlib.Path, viewport: str) -> dict:
    """Return hero/CTA/banner extracted by Vision for display."""
    p = page_dir / f"vision_{viewport}.json"
    if not p.exists():
        return {}
    v = safe_load(p)
    hero = v.get("hero") or {}
    return {
        "h1": (hero.get("h1") or {}).get("text", "") if isinstance(hero.get("h1"), dict) else "",
        "subtitle": (hero.get("subtitle") or {}).get("text", "") if isinstance(hero.get("subtitle"), dict) else "",
        "primary_cta": (hero.get("primary_cta") or {}).get("text", "") if isinstance(hero.get("primary_cta"), dict) else "",
        "utility_banner": (v.get("utility_banner") or {}).get("text", "") if isinstance(v.get("utility_banner"), dict) else "",
        "fold_readability_score": (v.get("fold_readability") or {}).get("score_1_to_5") if isinstance(v.get("fold_readability"), dict) else None,
    }


def page_summary(page_dir: pathlib.Path) -> dict:
    """Assemble pour une page : scores, recos, crops, screenshots paths."""
    capture = safe_load(page_dir / "capture.json")
    score_agg = safe_load(page_dir / "score_page_type.json")
    recos_final = safe_load(page_dir / "recos_v13_final.json")

    # V20 : load dual-viewport crops. Fallback to V17 crops if v2 absent.
    crops_desktop = _load_crops_v2(page_dir, "desktop")
    crops_mobile = _load_crops_v2(page_dir, "mobile")
    # Vision-extracted hero data per viewport (more accurate than V17 semantic_mapper)
    vision_desktop = _load_vision_meta(page_dir, "desktop")
    vision_mobile = _load_vision_meta(page_dir, "mobile")

    semantic_map = capture.get("semantic_map", [])
    hero = capture.get("hero") or {}

    # Screenshots relatifs depuis deliverables/
    page_rel = page_dir.relative_to(ROOT)
    ss_dir = page_rel / "screenshots"

    screenshots = {
        "desktop_full": f"../{ss_dir}/desktop_clean_full.png",
        "desktop_fold": f"../{ss_dir}/desktop_clean_fold.png",
        "mobile_full": f"../{ss_dir}/mobile_clean_full.png",
        "mobile_fold": f"../{ss_dir}/mobile_clean_fold.png",
        "annotated": f"../{ss_dir}/spatial_annotated_desktop.png",
    }
    # Garde uniquement les chemins qui existent réellement
    screenshots = {k: v for k, v in screenshots.items() if (ROOT / v.replace("../", "", 1)).exists()}

    # Pillar scores compacts
    pillars = {}
    for p in ["hero", "persuasion", "ux", "coherence", "psycho", "tech"]:
        sp = safe_load(page_dir / f"score_{p}.json")
        if sp:
            pillars[p] = {
                "score": sp.get("finalTotal", sp.get("rawTotal", 0)),
                "max": sp.get("maxFull", sp.get("max", 0)),
                "pct": sp.get("score100", 0),
                "killer": sp.get("killerTriggered", False),
            }

    # Overlays transparency (P11.6)
    overlays = {
        "semantic": score_agg.get("semantic_overlay") or {},
        "contextual": score_agg.get("contextual_overlay") or {},
        "applicability": score_agg.get("applicability_overlay") or {},
    }

    # V21 — Load cluster holistic recos (SYNERGY_GROUP-level)
    cluster_final = safe_load(page_dir / "recos_v21_cluster_final.json")

    # Collect criteria covered by clusters (to avoid double-counting in individuals)
    cluster_covered_crits = set()
    for cl in (cluster_final.get("clusters") or []):
        if cl.get("_fallback") or cl.get("_error"):
            continue
        cluster_covered_crits.update(cl.get("criteria_covered") or [])

    # Recos nettoyées (jargon → français clair)
    recos_clean = []

    # V21 cluster recos first (holistic, priority visible)
    for cl in (cluster_final.get("clusters") or []):
        if cl.get("_fallback") or cl.get("_error"):
            continue
        # Priority / ICE : prendre la valeur du LLM si bien retournée, sinon fallback
        priority = cl.get("priority") or "P1"
        ice_score = cl.get("ice_score") or 50
        # Build a "multi-crop" for cluster : top-most criteria's crop as the primary highlight
        covered = cl.get("criteria_covered") or []
        primary_cid = covered[0] if covered else None
        crop_desktop = crops_desktop.get(primary_cid, {}) if primary_cid else {}
        crop_mobile = crops_mobile.get(primary_cid, {}) if primary_cid else {}
        # Aggregate highlights from all covered criteria for richer display
        all_highlights_desktop = []
        all_highlights_mobile = []
        for c_cid in covered:
            cd_desktop = crops_desktop.get(c_cid, {})
            cd_mobile = crops_mobile.get(c_cid, {})
            all_highlights_desktop.extend(cd_desktop.get("highlights") or [])
            all_highlights_mobile.extend(cd_mobile.get("highlights") or [])
        if all_highlights_desktop and crop_desktop:
            crop_desktop = dict(crop_desktop)
            crop_desktop["highlights"] = all_highlights_desktop[:6]  # cap at 6
        if all_highlights_mobile and crop_mobile:
            crop_mobile = dict(crop_mobile)
            crop_mobile["highlights"] = all_highlights_mobile[:6]

        recos_clean.append({
            "is_cluster": True,
            "cluster_id": cl.get("cluster_id"),
            "criteria_covered": covered,
            "criterion_id": cl.get("cluster_id"),  # legacy field for compat with webapp code
            "priority": priority,
            "ice_score": ice_score,
            "problem_headline": declutter_jargon(cl.get("problem_headline", "")),
            "before": declutter_jargon(cl.get("before", "")),
            "after": declutter_jargon(cl.get("after", "")),
            "why": declutter_jargon(cl.get("why", "")),
            "notes": declutter_jargon(cl.get("implementation_notes", "")),
            "lift": cl.get("expected_lift_pct"),
            "effort": cl.get("effort_hours"),
            "crop": crop_desktop,
            "crops": {"desktop": crop_desktop, "mobile": crop_mobile},
            # V26.A — Evidence Ledger : preuves vérifiables
            "evidence_ids": cl.get("evidence_ids") or [],
            # V26.B — Reco Lifecycle
            "lifecycle": cl.get("lifecycle") or None,
        })

    # V13 individual recos — skip those covered by clusters (avoid duplicates)
    for r in (recos_final.get("recos") or []):
        if r.get("_fallback") or r.get("_skipped"):
            continue
        cid = r.get("criterion_id")
        if cid in cluster_covered_crits:
            continue  # V21 cluster handles it
        crop_desktop = crops_desktop.get(cid, {})
        crop_mobile = crops_mobile.get(cid, {})
        recos_clean.append({
            "is_cluster": False,
            "criterion_id": cid,
            "priority": r.get("priority"),
            "ice_score": r.get("ice_score"),
            "before": declutter_jargon(r.get("before", "")),
            "after": declutter_jargon(r.get("after", "")),
            "why": declutter_jargon(r.get("why", "")),
            "notes": declutter_jargon(r.get("implementation_notes", "")),
            "lift": r.get("expected_lift_pct"),
            "effort": r.get("effort_hours"),
            "crop": crop_desktop,
            "crops": {"desktop": crop_desktop, "mobile": crop_mobile},
            # V26.A — Evidence Ledger : preuves vérifiables (DOM + bbox + crop + hash)
            "evidence_ids": r.get("evidence_ids") or [],
            # V26.B — Reco Lifecycle : status + history du parcours generated→won
            "lifecycle": r.get("lifecycle") or None,
        })

    # Audit quality metadata
    audit_quality = {
        "capture_confidence": 1.0,  # TODO : from ocr_diff.json when available
        "phantom_filtered_count": 0,  # TODO : from spatial phantom_filter_stats
        "semantic_overrides": len(overlays["semantic"].get("criteria_overridden", [])),
        "contextual_rescues": len(overlays["contextual"].get("adjustments", [])),
    }
    ocr_diff = safe_load(page_dir / "ocr_diff.json")
    if ocr_diff:
        audit_quality["capture_confidence"] = ocr_diff.get("confidence", 1.0)
        audit_quality["ocr_flags"] = ocr_diff.get("flags", [])

    # V23.D — Funnel data (only for pages with score_funnel.json)
    aggregate = score_agg.get("aggregate", {}) or {}
    funnel_block = score_agg.get("funnel") or {}
    funnel_data = None
    if funnel_block.get("score100") is not None:
        flow_meta = funnel_block.get("flow_meta") or {}
        funnel_data = {
            "applicable": True,
            "score100": funnel_block.get("score100"),
            "score100_intro_only": aggregate.get("score100_intro_only"),
            "score100_funnel_aware": aggregate.get("score100_funnel_aware"),
            "weight_intro": (aggregate.get("funnel_weight_applied") or {}).get("intro"),
            "weight_flow": (aggregate.get("funnel_weight_applied") or {}).get("flow"),
            "criteria": funnel_block.get("criteria") or [],
            "flow_meta": flow_meta,
            "steps_captured": flow_meta.get("steps_captured", 0),
            "result_reached": flow_meta.get("result_reached", False),
            "halt_reason": flow_meta.get("halt_reason"),
            "has_progress_bar": flow_meta.get("has_progress_bar", False),
        }
    elif funnel_block.get("applicable"):
        # Funnel applicable but score_funnel.json missing
        funnel_data = {"applicable": True, "score100": None, "missing_capture": True}

    return {
        "page_type": page_dir.name,
        "url": capture.get("meta", {}).get("url") or hero.get("url", ""),
        "score_total": aggregate.get("rawTotal") or score_agg.get("rawTotal", 0),
        "score_max": aggregate.get("rawMax") or score_agg.get("rawMax", 117),
        "score_pct": aggregate.get("score100") or score_agg.get("score100", 0),
        "priority_distribution": recos_final.get("fleet_pri_dist") or {
            "P0": sum(1 for r in recos_clean if r.get("priority") == "P0"),
            "P1": sum(1 for r in recos_clean if r.get("priority") == "P1"),
            "P2": sum(1 for r in recos_clean if r.get("priority") == "P2"),
            "P3": sum(1 for r in recos_clean if r.get("priority") == "P3"),
        },
        "pillars": pillars,
        "overlays": overlays,
        "semantic_zones": semantic_map,  # pour afficher dans l'UI
        "hero": {
            # V17 heuristic (legacy compat)
            "h1": hero.get("h1", ""),
            "subtitle": hero.get("subtitle", ""),
            "primary_cta": (hero.get("primaryCta") or {}).get("label", ""),
        },
        "hero_vision": {  # V20 — Vision-extracted, more accurate
            "desktop": vision_desktop,
            "mobile": vision_mobile,
        },
        "screenshots": screenshots,
        "audit_quality": audit_quality,
        "recos": recos_clean,
        "n_recos": len(recos_clean),
        # V23.D — funnel scoring (None for non-funnel pages)
        "funnel": funnel_data,
        # V25.D.4 — INLINE flow_summary.json (sinon fetch file:// échoue)
        "funnel_flow": _safe_load_flow(page_dir),
        # V26.X.5 — Per-step audit recos
        "step_recos": _safe_load_step_recos(page_dir),
    }


def _safe_load_step_recos(page_dir):
    """V26.X.5 — Inline step_recos.json (per-step audit du tunnel)."""
    fp = page_dir / "flow" / "step_recos.json"
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text())
    except Exception:
        return None


def _safe_load_flow(page_dir):
    """V25.D.4 + V26.X.3 — Inline flow_summary.json + compressed_steps.
    Préserve raw steps (audit trail) + compressed_steps (vraies étapes UX
    après merge form_fill+Continuer sur même current_step_label)."""
    fp = page_dir / "flow" / "flow_summary.json"
    if not fp.exists():
        return None
    try:
        d = json.loads(fp.read_text())
        steps = []
        for st in (d.get("steps") or []):
            steps.append({
                "step": st.get("step"),
                "url": st.get("url"),
                "screenshot": st.get("screenshot"),
                "vision_action": st.get("vision_action"),
                "exec_result": st.get("exec_result"),
                "dom_widgets_count": st.get("dom_widgets_count"),
                "stuck_dom_count": st.get("stuck_dom_count"),
            })
        return {
            "url": d.get("url"),
            "viewport": d.get("viewport"),
            "max_steps": d.get("max_steps"),
            "steps": steps,
            "compressed_steps": d.get("compressed_steps") or [],
            "n_steps_raw": d.get("n_steps_raw") or len(steps),
            "n_steps_real": d.get("n_steps_real") or len(steps),
            "result_reached": d.get("result_reached"),
            "haltReason": d.get("haltReason"),
            "tokens_total": d.get("tokens_total"),
            "model": d.get("model"),
            "version": d.get("version"),
            "headed_mode": d.get("headed_mode"),
            "aggregate": d.get("aggregate"),
        }
    except Exception:
        return None


def build_client_data(client_id: str, clients_db: dict, panel_entry: dict | None = None) -> dict:
    client_dir = CAPTURES / client_id
    if not client_dir.exists():
        return {}
    info = clients_db.get(client_id) or {}
    panel_entry = panel_entry or {}
    identity = info.get("identity") or {}
    declared_page_types = set(panel_entry.get("page_types") or [])

    pages = []
    for pd in sorted(client_dir.iterdir()):
        if not pd.is_dir():
            continue
        if declared_page_types and pd.name not in declared_page_types:
            continue
        try:
            summary = page_summary(pd)
            if summary.get("n_recos", 0) > 0 or summary.get("score_total", 0) > 0:
                pages.append(summary)
        except Exception as e:
            print(f"  ⚠ {client_id}/{pd.name}: {e}")

    # Fleet aggregates
    total_recos = sum(p["n_recos"] for p in pages)
    total_p0 = sum((p["priority_distribution"].get("P0", 0)) for p in pages)
    total_p1 = sum((p["priority_distribution"].get("P1", 0)) for p in pages)
    total_p2 = sum((p["priority_distribution"].get("P2", 0)) for p in pages)
    total_p3 = sum((p["priority_distribution"].get("P3", 0)) for p in pages)
    avg_score = round(sum(p["score_pct"] for p in pages) / max(1, len(pages)), 1)

    # Scent trail cross-page
    scent_path = client_dir / "scent_trail.json"
    scent_trail = safe_load(scent_path)

    # V26.X.2 — canonical_tunnel detection (cross-page merge into shared funnel)
    canonical_tunnel = safe_load(client_dir / "canonical_tunnel.json")

    # V25.D.4 — Inline V26 panels data (fetch file:// échoue en open html direct)
    v26_data = _build_v26_inline(client_id, client_dir)

    return {
        "id": client_id,
        "name": panel_entry.get("display_name") or identity.get("name") or info.get("name") or client_id.replace("_", " ").title(),
        "brand": (info.get("brand") or {}).get("name", ""),
        "url": identity.get("url", info.get("url", "")),
        "business_type": identity.get("businessType") or info.get("business_type") or panel_entry.get("business_type") or "unknown",
        "category": info.get("category") or panel_entry.get("category", ""),
        "panel": {
            "source": panel_entry.get("source") or "curated_clients_v26",
            "display_name": panel_entry.get("display_name"),
            "role": panel_entry.get("panel_role") or "runtime_panel",
            "status": panel_entry.get("status") or "keep",
            "role_confidence": panel_entry.get("role_confidence"),
            "reason_in_panel": panel_entry.get("reason_in_panel") or "",
            "declared_n_pages": panel_entry.get("n_pages"),
            "declared_avg_score_pct": panel_entry.get("avg_score_pct"),
            "declared_page_types": panel_entry.get("page_types") or [],
        },
        "n_pages": len(pages),
        "n_recos_total": total_recos,
        "priority_distribution": {"P0": total_p0, "P1": total_p1, "P2": total_p2, "P3": total_p3},
        "avg_score_pct": avg_score,
        "pages": pages,
        "scent_trail": scent_trail,
        "v26": v26_data,
        "canonical_tunnel": canonical_tunnel,
    }


def _build_v26_inline(client_id, client_dir):
    """V25.D.4 — Inline les artifacts V26+ par client (Brand DNA, Design Grammar, GEO, Reality)."""
    out = {
        "evidence_count": 0,
        "lifecycle_summary": {},
        "pages": {},
        "_summary": {},
        "module_status": {},
        "brand_dna": None,
        "design_grammar": None,
        "geo_audit": None,
        "geo_monitor": None,
        "reality_layer": None,
    }
    # Evidence count (sum across pages)
    n_pages = 0
    n_pages_with_evidence = 0
    n_pages_with_reality = 0
    n_pages_with_reality_attempted = 0
    n_disagreements = 0
    total_recos = 0
    experiment_runs = 0
    reality_pages = {}

    for pd in client_dir.iterdir():
        if not pd.is_dir() or pd.name.startswith("_"):
            continue
        n_pages += 1
        page_meta = {
            "evidence_count": 0,
            "n_recos_final": 0,
            "has_reality": False,
            "disagreement_count": 0,
            "experiment_runs": 0,
        }
        ev = pd / "evidence_ledger.json"
        if ev.exists():
            try:
                d = json.loads(ev.read_text())
                items = d.get("items") or d.get("evidence") or []
                if isinstance(items, list):
                    page_meta["evidence_count"] = len(items)
                elif isinstance(items, dict):
                    page_meta["evidence_count"] = len(items)
                out["evidence_count"] += page_meta["evidence_count"]
                if page_meta["evidence_count"]:
                    n_pages_with_evidence += 1
            except Exception:
                pass
        # Lifecycle aggregation across all recos
        rf = pd / "recos_v13_final.json"
        if rf.exists():
            try:
                d = json.loads(rf.read_text())
                recos = d.get("recos") or []
                page_meta["n_recos_final"] = len(recos)
                total_recos += page_meta["n_recos_final"]
                for r in recos:
                    lc = (r.get("lifecycle") or {}).get("status", "generated")
                    out["lifecycle_summary"][lc] = out["lifecycle_summary"].get(lc, 0) + 1
            except Exception:
                pass
        page_reality = safe_load(pd / "reality_layer.json")
        if page_reality:
            page_meta["reality_attempted"] = True
            n_pages_with_reality_attempted += 1
            page_meta["has_reality"] = reality_has_active_connector(page_reality)
            if page_meta["has_reality"]:
                n_pages_with_reality += 1
            reality_pages[pd.name] = page_reality
        disagreement = safe_load(pd / "disagreement_log.json")
        if disagreement:
            disagreements = disagreement.get("disagreements") or []
            page_meta["disagreement_count"] = len(disagreements) if isinstance(disagreements, list) else 0
            n_disagreements += page_meta["disagreement_count"]
        exp_dir = pd / "experiments"
        if exp_dir.is_dir():
            page_meta["experiment_runs"] = len(list(exp_dir.glob("*.json")))
            experiment_runs += page_meta["experiment_runs"]
        out["pages"][pd.name] = page_meta
    # Brand DNA
    bd = client_dir / "brand_dna.json"
    if bd.exists():
        try:
            out["brand_dna"] = json.loads(bd.read_text())
        except Exception:
            pass
    # Design Grammar (7 fichiers)
    dg = client_dir / "design_grammar"
    if dg.is_dir():
        out["design_grammar"] = {}
        for f in dg.iterdir():
            if f.suffix == ".json":
                try:
                    out["design_grammar"][f.stem] = json.loads(f.read_text())
                except Exception:
                    pass
            elif f.suffix == ".css":
                try:
                    out["design_grammar"][f.stem + "_css"] = f.read_text()
                except Exception:
                    pass
    # GEO Audit (1 file at client level)
    ga = client_dir / "geo_audit.json"
    if ga.exists():
        try:
            out["geo_audit"] = json.loads(ga.read_text())
        except Exception:
            pass
    # GEO Monitor cache
    gm = client_dir / "geo_monitor_cache.json"
    if gm.exists():
        try:
            out["geo_monitor"] = json.loads(gm.read_text())
        except Exception:
            pass
    # Reality Layer aggregated metrics. Prefer legacy client aggregate if present,
    # else expose page-level runtime outputs from reality_layer/orchestrator.py.
    rl = client_dir / "reality_layer_metrics.json"
    if rl.exists():
        try:
            out["reality_layer"] = json.loads(rl.read_text())
        except Exception:
            pass
    elif reality_pages:
        out["reality_layer"] = {
            "source": "page_reality_layer_json",
            "n_pages": len(reality_pages),
            "pages": reality_pages,
        }
    out["_summary"] = {
        "n_pages": n_pages,
        "total_recos": total_recos,
        "evidence_count": out["evidence_count"],
        "n_pages_with_evidence": n_pages_with_evidence,
        "n_pages_with_reality": n_pages_with_reality,
        "n_pages_with_reality_attempted": n_pages_with_reality_attempted,
        "n_disagreements": n_disagreements,
        "n_experiment_runs": experiment_runs,
    }
    out["module_status"] = {
        "evidence_ledger": status_block("active" if out["evidence_count"] else "inactive", out["evidence_count"], None, "page evidence items"),
        "reco_lifecycle": status_block("active" if out["lifecycle_summary"] else "inactive", total_recos, None, "recos with lifecycle status"),
        "brand_dna": status_block("active" if out["brand_dna"] else "inactive", 1 if out["brand_dna"] else 0, 1, "client-level brand_dna.json"),
        "design_grammar": status_block("active" if out["design_grammar"] else "inactive", len(out["design_grammar"] or {}), None, "design_grammar files inlined"),
        "geo_monitor": status_block("active" if (out["geo_audit"] or out["geo_monitor"]) else "inactive", 1 if (out["geo_audit"] or out["geo_monitor"]) else 0, 1, "client-level GEO artifacts"),
        "reality_layer": status_block("active" if n_pages_with_reality else "inactive", n_pages_with_reality, n_pages, "pages with at least 1 active Reality connector"),
        "experiment_engine": status_block("active" if experiment_runs else "inactive", experiment_runs, None, "experiment run specs on disk"),
    }
    return out


def build_fleet_module_status(all_clients: list[dict], total_pages: int) -> dict:
    total_clients = len(all_clients)
    n_reco_clients = sum(1 for c in all_clients if c.get("n_recos_total", 0) > 0)
    n_brand = sum(1 for c in all_clients if (c.get("v26") or {}).get("brand_dna"))
    n_dg = sum(1 for c in all_clients if (c.get("v26") or {}).get("design_grammar"))
    n_geo = sum(1 for c in all_clients if ((c.get("v26") or {}).get("geo_audit") or (c.get("v26") or {}).get("geo_monitor")))
    n_reality_clients = sum(1 for c in all_clients if ((c.get("v26") or {}).get("_summary") or {}).get("n_pages_with_reality", 0) > 0)
    n_reality_pages = sum(((c.get("v26") or {}).get("_summary") or {}).get("n_pages_with_reality", 0) for c in all_clients)
    n_reality_attempted = sum(((c.get("v26") or {}).get("_summary") or {}).get("n_pages_with_reality_attempted", 0) for c in all_clients)
    n_evidence = sum((c.get("v26") or {}).get("evidence_count", 0) for c in all_clients)
    n_lifecycle = sum(sum(((c.get("v26") or {}).get("lifecycle_summary") or {}).values()) for c in all_clients)
    n_experiment_runs = sum(((c.get("v26") or {}).get("_summary") or {}).get("n_experiment_runs", 0) for c in all_clients)
    learning_proposals = len(list((LEARNING_DIR / "audit_based_proposals").glob("*.json"))) if (LEARNING_DIR / "audit_based_proposals").is_dir() else 0
    learning_stats = (LEARNING_DIR / "audit_based_stats.json").exists()
    return {
        "audit_engine": status_block("active", total_pages, total_pages, "captured/scored pages in static dataset"),
        "recommendations_engine": status_block("active", n_reco_clients, total_clients, "clients with recos in webapp"),
        "evidence_ledger": status_block("active" if n_evidence else "partial", n_evidence, None, "evidence items on disk"),
        "reco_lifecycle": status_block("active" if n_lifecycle else "inactive", n_lifecycle, None, "lifecycle states are generated-only until human review/experiments"),
        "brand_dna": status_block("partial", n_brand, total_clients, "brand_dna.json coverage"),
        "design_grammar": status_block("partial", n_dg, total_clients, "design_grammar coverage"),
        "reality_layer": status_block("active" if n_reality_pages else "inactive", n_reality_pages, total_pages, f"{n_reality_clients} clients with active Reality data; {n_reality_attempted} pages attempted"),
        "experiment_engine": status_block("active" if n_experiment_runs else "inactive", n_experiment_runs, None, "calculator available; no measured experiment runs found" if not n_experiment_runs else "experiment specs found"),
        "geo_monitor": status_block("partial" if n_geo else "inactive", n_geo, total_clients, "clients with geo_audit or geo_monitor_cache"),
        "learning_layer": status_block("partial" if (learning_proposals or learning_stats) else "inactive", learning_proposals, None, "audit-based doctrine proposals only; no measured experiment learning yet"),
        "gsg": status_block("frozen", 0, None, "GSG frozen during Audit/Reco/Webapp stabilization"),
        "webapp": status_block("static_mvp", total_clients, total_clients, "static HTML/JS observatory, not Next/Supabase runtime"),
    }


def main() -> None:
    clients_db = load_clients_db()
    print(f"→ Loaded {len(clients_db)} client entries from DB")
    panel_entries, panel_meta = load_curated_panel()
    panel_by_id = {entry["id"]: entry for entry in panel_entries}
    panel_ids = [entry["id"] for entry in panel_entries]
    if panel_ids:
        print(f"→ Loaded curated panel: {len(panel_ids)} clients from {panel_meta.get('path')}")

    all_clients = []
    total_pages = 0
    capture_ids = {cd.name for cd in CAPTURES.iterdir() if cd.is_dir() and not cd.name.startswith("_")}
    missing_panel_captures = []
    empty_panel_clients = []
    skipped_capture_dirs = []

    if panel_ids:
        candidate_ids = panel_ids
        missing_panel_captures = [client_id for client_id in panel_ids if client_id not in capture_ids]
        skipped_capture_dirs = sorted(capture_ids - set(panel_ids))
    else:
        candidate_ids = sorted(capture_ids)
        known_client_ids = set(clients_db.keys())
        if known_client_ids:
            skipped_capture_dirs = [client_id for client_id in candidate_ids if client_id not in known_client_ids]
            candidate_ids = [client_id for client_id in candidate_ids if client_id in known_client_ids]

    for client_id in candidate_ids:
        if client_id in missing_panel_captures:
            continue
        data = build_client_data(client_id, clients_db, panel_by_id.get(client_id))
        if data and data.get("n_pages", 0) > 0:
            all_clients.append(data)
            total_pages += data["n_pages"]
        else:
            empty_panel_clients.append(client_id)

    # Fleet aggregates
    fleet = {
        "n_clients": len(all_clients),
        "n_pages": total_pages,
        "n_recos": sum(c["n_recos_total"] for c in all_clients),
        "p0": sum(c["priority_distribution"]["P0"] for c in all_clients),
        "p1": sum(c["priority_distribution"]["P1"] for c in all_clients),
        "p2": sum(c["priority_distribution"]["P2"] for c in all_clients),
        "p3": sum(c["priority_distribution"]["P3"] for c in all_clients),
        "avg_score_pct": round(sum(c["avg_score_pct"] for c in all_clients) / max(1, len(all_clients)), 1),
    }
    module_status = build_fleet_module_status(all_clients, total_pages)
    fleet["module_status"] = module_status

    # Group by panel role + business_type + page_type for dashboard aggregates
    by_panel_role = defaultdict(lambda: {"n_clients": 0, "n_pages": 0, "avg_score": 0, "total_p0": 0})
    by_business = defaultdict(lambda: {"n_clients": 0, "n_pages": 0, "avg_score": 0, "total_p0": 0})
    by_page_type = defaultdict(lambda: {"n_pages": 0, "avg_score": 0, "total_p0": 0})
    for c in all_clients:
        role = (c.get("panel") or {}).get("role") or "runtime_panel"
        by_panel_role[role]["n_clients"] += 1
        by_panel_role[role]["n_pages"] += c["n_pages"]
        by_panel_role[role]["total_p0"] += c["priority_distribution"]["P0"]
        by_panel_role[role]["avg_score"] += c["avg_score_pct"] * c["n_pages"]

        bt = c["business_type"]
        by_business[bt]["n_clients"] += 1
        by_business[bt]["n_pages"] += c["n_pages"]
        by_business[bt]["total_p0"] += c["priority_distribution"]["P0"]
        by_business[bt]["avg_score"] += c["avg_score_pct"] * c["n_pages"]
        for p in c["pages"]:
            pt = p["page_type"]
            by_page_type[pt]["n_pages"] += 1
            by_page_type[pt]["avg_score"] += p["score_pct"]
            by_page_type[pt]["total_p0"] += p["priority_distribution"].get("P0", 0)

    for role, v in by_panel_role.items():
        v["avg_score"] = round(v["avg_score"] / max(1, v["n_pages"]), 1)
    for bt, v in by_business.items():
        v["avg_score"] = round(v["avg_score"] / max(1, v["n_pages"]), 1)
    for pt, v in by_page_type.items():
        v["avg_score"] = round(v["avg_score"] / max(1, v["n_pages"]), 1)

    data = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "v27.0.0-panel-roles",
            "note": "Data consolidé pour GrowthCRO-V26-WebApp.html depuis le panel runtime data/curated_clients_v27.json si présent, sinon V26. Les rôles panel distinguent business candidates, goldens, benchmarks, Mathis picks et supplements.",
            "panel_source": panel_meta or {"path": str(CLIENTS_DB.relative_to(ROOT)), "version": "db_fallback"},
            "panel_size": len(panel_ids) if panel_ids else len(candidate_ids),
            "panel_built": len(all_clients),
            "panel_missing_captures": missing_panel_captures,
            "panel_empty_clients": empty_panel_clients,
            "skipped_capture_dirs": skipped_capture_dirs,
        },
        "fleet": fleet,
        "module_status": module_status,
        "by_panel_role": dict(by_panel_role),
        "by_business": dict(by_business),
        "by_page_type": dict(by_page_type),
        "clients": all_clients,
    }

    # V26.X.4 — Inject Growth Society Brand DNA (dogfooding)
    gs_dna_path = ROOT / "data" / "_growth_society" / "brand_dna.json"
    if gs_dna_path.exists():
        try:
            data["_growth_society_dna"] = json.loads(gs_dna_path.read_text())
        except Exception:
            pass

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"/* Auto-generated by build_growth_audit_data.py at {data['meta']['generated_at']} */\n"
                   f"window.GROWTH_AUDIT_DATA = {json.dumps(data, ensure_ascii=False)};\n")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"\n✅ Growth audit data built: {len(all_clients)} clients, {total_pages} pages, {fleet['n_recos']} recos")
    if missing_panel_captures:
        print(f"   missing panel captures: {', '.join(missing_panel_captures)}")
    if empty_panel_clients:
        print(f"   panel clients without usable pages: {', '.join(empty_panel_clients)}")
    if skipped_capture_dirs:
        print(f"   skipped non-panel capture dirs: {', '.join(skipped_capture_dirs[:12])}" + ("…" if len(skipped_capture_dirs) > 12 else ""))
    print(f"   → {OUT.relative_to(ROOT)} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
