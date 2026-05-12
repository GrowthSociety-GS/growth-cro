#!/usr/bin/env python3
"""
score_contextual_overlay.py — P1.B Doctrine v3.2.0-draft (2026-04-18)

CONTEXTUAL (ENSEMBLE) SCORING LAYER
===================================
Runs AFTER semantic_overlay (Haiku) and BEFORE aggregation.
Applies synergy-group compensation rules to ENSEMBLE-scope criteria so that
individual elements (H1, subtitle, CTA, visuals, testimonials…) are no longer
judged in isolation but in ensemble context.

Reads:
  - data/doctrine/criteria_scope_matrix_v1.json   (scope + synergy groups)
  - perception_v13.json (optional, for spatial synergy check on HERO_ENSEMBLE)

Mutates (in place) bloc_results[pillar].kept_criteria when a compensation rule
fires, and returns a `contextual_overlay` trace dict for traceability.

Design principle (doctrine v3.2):
  - ASSET criteria (tech_*, psy_02 numeric anchoring, counts, presence) are
    INVARIANT — contextual layer NEVER touches them.
  - ENSEMBLE criteria may be rescued UPWARDS (weak element compensated by
    strong peers) OR penalized DOWNWARDS (contradiction flag, e.g. pushy
    urgency without risk reversal = "manipulation risk").
  - Every adjustment is traced with rule_id, before → after, rationale, peers.

Compensation rules implemented (v2, 2026-04-19 P11.4 — cap dynamique) :
  R1  HERO_RESCUE          weak hero_01 rescued by strong hero_02+04+05    → min(3.0, peers_avg × 0.9)
  R2  PROOF_RESCUE         weak per_04 rescued by psy_05+psy_08 quorum     → min(3.0, peers_avg × 0.9)
  R3  FIVE_SEC_RESCUE      weak coh_01 rescued by coh_02+coh_04 quorum     → min(3.0, peers_avg × 0.9)
  R4  BENEFIT_FLOW_RESCUE  weak per_02 rescued by strong per_01 on short   → min(3.0, per_01 × 0.9)
  R5  MANIPULATION_FLAG    strong urgency + weak risk-reversal = -0.5 psy_01 (penalty fixe)
  R6  UX_RHYTHM_RESCUE     weak ux_02 rescued by strong ux_01+ux_05        → min(3.0, peers_avg × 0.9)
  R7  COHERENCE_QUORUM     catch-all, ≥70% peers strong + target=0 → 0→cap(0.6× peers_avg) conservateur
  TECH_FOUNDATION           no compensation (rule set is no-op)

P11.4 change : avant V18 les rescues R1-R4/R6/R7 plafonnaient à 1.5/3 (tier=ok).
Depuis V18 : cap dynamique `peers_avg × 0.9` (R7 : × 0.6) avec max_cap=3.0 et
floor=1.5 (R7 floor=1.0). Ensemble vraiment fort → rescue peut atteindre tier=top (≥2.4/3).

Spatial synergy (optional, only if perception_v13.json present):
  - HERO_RESCUE only fires if H1, subtitle, CTA, visual are in same spatial
    cluster (proximity ≤ threshold). Else rule aborts with rationale
    "hero elements scattered — no ensemble coherence to compensate with".
"""
from __future__ import annotations

import json
import pathlib
import math
from datetime import datetime

# Try to locate doctrine matrix on import
_DEFAULT_MATRIX = None


def _find_doctrine_matrix() -> pathlib.Path | None:
    """Walk up from this file to find data/doctrine/criteria_scope_matrix_v1.json."""
    p = pathlib.Path(__file__).resolve()
    while p != p.parent:
        cand = p / "data" / "doctrine" / "criteria_scope_matrix_v1.json"
        if cand.exists():
            return cand
        p = p.parent
    return None


def load_doctrine_matrix(path: pathlib.Path | None = None) -> dict:
    """Load the criteria scope matrix. Cached."""
    global _DEFAULT_MATRIX
    if _DEFAULT_MATRIX is not None and path is None:
        return _DEFAULT_MATRIX
    if path is None:
        path = _find_doctrine_matrix()
    if path is None or not path.exists():
        return {"criteria": [], "synergy_groups": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if path is None or _DEFAULT_MATRIX is None:
        _DEFAULT_MATRIX = data
    return data


def _index_criteria(matrix: dict) -> dict:
    """criterion_id → {scope, synergy_group, pillar}."""
    idx = {}
    for c in matrix.get("criteria", []):
        idx[c["id"]] = {
            "scope": c.get("scope"),
            "synergy_group": c.get("synergy_group"),
            "pillar": c.get("pillar"),
        }
    return idx


def _index_kept_criteria(bloc_results: dict) -> dict:
    """Flatten bloc_results.kept_criteria into {cid: item} referenced in-place.
    Items here are live references — mutations propagate."""
    by_id = {}
    for pillar, blk in bloc_results.items():
        for item in (blk.get("kept_criteria") or []):
            cid = item.get("id") or item.get("criterion_id") or item.get("code")
            if cid:
                by_id[cid] = {"item": item, "pillar": pillar}
    return by_id


def _score_of(item: dict) -> float:
    v = item.get("score")
    try:
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


def _tier_from_score(score: float, max_score: float = 3.0) -> str:
    if max_score <= 0:
        return "critical"
    r = score / max_score
    if r >= 0.8:
        return "top"
    if r >= 0.5:
        return "ok"
    return "critical"


def _avg(scores: list[float]) -> float:
    return sum(scores) / len(scores) if scores else 0.0


def _load_perception_v13(capture_dir: pathlib.Path | None) -> dict | None:
    if not capture_dir:
        return None
    fp = capture_dir / "perception_v13.json"
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None


def _hero_spatial_coherent(perception: dict | None) -> tuple[bool, str]:
    """Check that H1, subtitle, CTA, visual are all in the hero spatial cluster.
    Returns (coherent, rationale).
    If perception data unavailable, return True to not block the rule."""
    if not perception:
        return True, "no perception_v13 — default coherent"
    clusters = perception.get("clusters") or perception.get("zones") or []
    if not clusters:
        return True, "no clusters in perception — default coherent"
    # Find hero cluster (first cluster with y <= 700 usually, or label HERO)
    hero = None
    for c in clusters:
        lbl = (c.get("label") or c.get("name") or c.get("zone") or "").upper()
        if "HERO" in lbl or lbl == "HEADER":
            hero = c
            break
    if hero is None and clusters:
        # fallback: topmost cluster
        hero = min(clusters, key=lambda c: c.get("y", 0))
    if not hero:
        return True, "hero cluster not identified — default coherent"
    # Check presence of H1 + subtitle + CTA + visual hints
    members = hero.get("members") or hero.get("elements") or hero.get("nodes") or []
    has = {"h1": False, "subtitle": False, "cta": False, "visual": False}
    for m in members:
        if isinstance(m, dict):
            tag = (m.get("tag") or m.get("type") or "").lower()
            role = (m.get("role") or "").lower()
            text = (m.get("text") or "").lower()
            if tag == "h1" or role == "heading":
                has["h1"] = True
            if tag in ("h2", "h3", "p") and len(text) > 20:
                has["subtitle"] = True
            if tag == "a" or role == "button" or "cta" in role:
                has["cta"] = True
            if tag in ("img", "video") or "image" in (m.get("type") or ""):
                has["visual"] = True
    count = sum(has.values())
    if count >= 3:
        return True, f"{count}/4 hero elements clustered together"
    return False, f"only {count}/4 hero elements in hero cluster — scattered"


# ═════════════════════════════════════════════════════════════════════════════
# COMPENSATION RULES
# Each rule has signature: (by_id, synergy_members, context) -> dict | None
# Returns a dict with {target, before, after, rule_id, rationale, peers} if
# rule fires; None otherwise.
# ═════════════════════════════════════════════════════════════════════════════

def _apply_rule(target_cid: str, by_id: dict, new_score: float, max_score: float,
                rule_id: str, rationale: str, peers: list[str]) -> dict | None:
    if target_cid not in by_id:
        return None
    it = by_id[target_cid]["item"]
    before_score = _score_of(it)
    if abs(new_score - before_score) < 0.01:
        return None
    before_tier = it.get("tier") or _tier_from_score(before_score, max_score)
    it["pre_contextual_score"] = round(before_score, 2)
    it["pre_contextual_tier"] = before_tier
    it["score"] = round(new_score, 2)
    it["tier"] = _tier_from_score(new_score, max_score)
    it["contextual_rule"] = rule_id
    it["contextual_rationale"] = rationale
    it["method"] = (it.get("method") or "regex") + "+contextual"
    return {
        "target": target_cid,
        "pillar": by_id[target_cid]["pillar"],
        "rule_id": rule_id,
        "before_score": round(before_score, 2),
        "after_score": round(new_score, 2),
        "delta": round(new_score - before_score, 2),
        "before_tier": before_tier,
        "after_tier": _tier_from_score(new_score, max_score),
        "rationale": rationale,
        "peers": peers,
    }


def _dynamic_rescue_score(peers_avg: float, multiplier: float = 0.9, max_cap: float = 3.0, floor: float = 1.5) -> float:
    """P11.4 — cap dynamique au lieu du plancher fixe 1.5.

    Avant V18 : rescue plafonné à 1.5/3 (tier=ok) même quand les peers avg 3.0.
    Après : score = min(max_cap, peers_avg * multiplier), floor=1.5.
    Ensemble fort → rescue peut atteindre tier=top (≥2.4/3).
    """
    return round(max(floor, min(max_cap, peers_avg * multiplier)), 2)


def rule_R1_hero_rescue(by_id: dict, ctx: dict) -> dict | None:
    """HERO_ENSEMBLE: weak hero_01 rescued by strong peers hero_02, hero_04, hero_05."""
    if "hero_01" not in by_id:
        return None
    s_h1 = _score_of(by_id["hero_01"]["item"])
    if s_h1 >= 1.5:
        return None  # not weak
    peers = ["hero_02", "hero_04", "hero_05"]
    peer_scores = [_score_of(by_id[p]["item"]) for p in peers if p in by_id]
    if len(peer_scores) < 2:
        return None
    peers_avg = _avg(peer_scores)
    if peers_avg < 2.0:
        return None
    # Check spatial coherence
    coherent, spatial_note = _hero_spatial_coherent(ctx.get("perception"))
    if not coherent:
        return None  # scattered hero — no rescue
    # P11.4 : cap dynamique — peers forts peuvent lift jusqu'à 2.7/3 (tier=top)
    new_score = _dynamic_rescue_score(peers_avg)
    rationale = (f"hero_01 critical ({s_h1}) rescued to {new_score} (dyn cap "
                 f"0.9 × peers_avg={peers_avg:.2f}): H1 promise carried by subtitle/visual/CTA. "
                 f"Spatial: {spatial_note}.")
    return _apply_rule("hero_01", by_id, new_score, 3.0, "R1_HERO_RESCUE", rationale, peers)


def rule_R2_proof_rescue(by_id: dict, ctx: dict) -> dict | None:
    """SOCIAL_PROOF_STACK: weak per_04 (testimonials/proofs) rescued by strong psy_05 + psy_08."""
    if "per_04" not in by_id:
        return None
    s = _score_of(by_id["per_04"]["item"])
    if s >= 1.5:
        return None
    peers = ["psy_05", "psy_08", "per_05"]
    peer_scores = [_score_of(by_id[p]["item"]) for p in peers if p in by_id]
    if len(peer_scores) < 2:
        return None
    peers_avg = _avg(peer_scores)
    if peers_avg < 2.0:
        return None
    new_score = _dynamic_rescue_score(peers_avg)
    rationale = (f"per_04 weak ({s}) rescued to {new_score} (dyn cap 0.9 × peers_avg={peers_avg:.2f}): "
                 f"authority signals (psy_05/08) + logos (per_05) carry trust.")
    return _apply_rule("per_04", by_id, new_score, 3.0, "R2_PROOF_RESCUE", rationale, peers)


def rule_R3_fivesec_rescue(by_id: dict, ctx: dict) -> dict | None:
    """COHERENCE_FULL: weak coh_01 (5-sec test) rescued by strong coh_02 + coh_04."""
    if "coh_01" not in by_id:
        return None
    s = _score_of(by_id["coh_01"]["item"])
    if s >= 1.5:
        return None
    peers = ["coh_02", "coh_04"]
    peer_scores = [_score_of(by_id[p]["item"]) for p in peers if p in by_id]
    if len(peer_scores) < 2:
        return None
    peers_avg = _avg(peer_scores)
    if peers_avg < 2.0:
        return None
    new_score = _dynamic_rescue_score(peers_avg)
    rationale = (f"coh_01 critical ({s}) rescued to {new_score} (dyn cap 0.9 × peers_avg={peers_avg:.2f}): "
                 f"target (coh_02) + positioning (coh_04) clarity compensate unclear 5-sec test.")
    return _apply_rule("coh_01", by_id, new_score, 3.0, "R3_FIVE_SEC_RESCUE", rationale, peers)


SHORT_PAGE_TYPES = {"lp_leadgen", "squeeze", "coming_soon", "home"}

def rule_R4_benefit_flow_rescue(by_id: dict, ctx: dict) -> dict | None:
    """BENEFIT_FLOW: weak per_02 (storytelling) rescued by strong per_01 on short pages."""
    page_type = ctx.get("page_type", "")
    if page_type not in SHORT_PAGE_TYPES:
        return None
    if "per_02" not in by_id:
        return None
    s = _score_of(by_id["per_02"]["item"])
    if s >= 1.5:
        return None
    peers = ["per_01"]
    if "per_01" not in by_id:
        return None
    s01 = _score_of(by_id["per_01"]["item"])
    if s01 < 2.5:
        return None
    new_score = _dynamic_rescue_score(s01)
    rationale = (f"per_02 weak ({s}) on short page ({page_type}) rescued to {new_score} "
                 f"(dyn cap 0.9 × per_01={s01}): storytelling less critical on LPs.")
    return _apply_rule("per_02", by_id, new_score, 3.0, "R4_BENEFIT_FLOW_RESCUE", rationale, peers)


def rule_R5_manipulation_flag(by_id: dict, ctx: dict) -> dict | None:
    """EMOTIONAL_DRIVERS: high urgency (psy_01) + weak risk-reversal (psy_04) = manipulation risk.
    Downgrade psy_01 by -0.5 with flag."""
    if "psy_01" not in by_id or "psy_04" not in by_id:
        return None
    s1 = _score_of(by_id["psy_01"]["item"])
    s4 = _score_of(by_id["psy_04"]["item"])
    if s1 < 2.5 or s4 > 1.0:
        return None
    new = max(0.0, s1 - 0.5)
    peers = ["psy_04"]
    rationale = (f"Manipulation flag: urgency psy_01={s1} paired with weak risk reversal "
                 f"psy_04={s4}. Pushy without safety net → -0.5 penalty on urgency.")
    it = by_id["psy_01"]["item"]
    it["manipulation_flag"] = True
    return _apply_rule("psy_01", by_id, new, 3.0, "R5_MANIPULATION_FLAG", rationale, peers)


def rule_R6_ux_rhythm_rescue(by_id: dict, ctx: dict) -> dict | None:
    """VISUAL_HIERARCHY: weak ux_02 rescued by strong ux_01 + ux_05."""
    if "ux_02" not in by_id:
        return None
    s = _score_of(by_id["ux_02"]["item"])
    if s >= 1.5:
        return None
    peers = ["ux_01", "ux_05"]
    peer_scores = [_score_of(by_id[p]["item"]) for p in peers if p in by_id]
    if len(peer_scores) < 2:
        return None
    peers_avg = _avg(peer_scores)
    if peers_avg < 2.5:
        return None
    new_score = _dynamic_rescue_score(peers_avg)
    rationale = (f"ux_02 weak ({s}) rescued to {new_score} (dyn cap 0.9 × peers_avg={peers_avg:.2f}): "
                 f"strong hierarchy (ux_01) + mobile fonts (ux_05) compensate rhythm.")
    return _apply_rule("ux_02", by_id, new_score, 3.0, "R6_UX_RHYTHM_RESCUE", rationale, peers)


def rule_R7_coherence_quorum(by_id: dict, ctx: dict, synergy_groups: dict, idx: dict) -> list[dict]:
    """Catch-all: for each synergy group except TECH_FOUNDATION, if ≥70% of ENSEMBLE
    members score >= 2.0 AND one member scores 0, bump it to 1.0.
    Prevents a single 0 dragging down a well-coherent ensemble."""
    adjustments = []
    for gid, group in synergy_groups.items():
        if gid == "TECH_FOUNDATION":
            continue
        members = [m for m in group.get("members", []) if m in by_id and idx.get(m, {}).get("scope") == "ENSEMBLE"]
        if len(members) < 3:
            continue
        scores = [_score_of(by_id[m]["item"]) for m in members]
        strong = [s for s in scores if s >= 2.0]
        zeroes = [(m, s) for m, s in zip(members, scores) if s < 0.5]
        if len(strong) / len(scores) >= 0.7 and zeroes:
            for target_cid, target_s in zeroes:
                # Skip if already adjusted by R1-R6
                it = by_id[target_cid]["item"]
                if it.get("contextual_rule"):
                    continue
                other_members = [m for m in members if m != target_cid]
                peer_avg = _avg([_score_of(by_id[m]["item"]) for m in other_members])
                # P11.4 — R7 reste plus conservateur (catch-all) : 0.6 au lieu de 0.9
                new_score = _dynamic_rescue_score(peer_avg, multiplier=0.6, floor=1.0)
                rationale = (f"Coherence quorum ({gid}): {len(strong)}/{len(scores)} peers "
                             f"strong (avg={peer_avg:.2f}). Lifting {target_cid} 0→{new_score} "
                             f"(dyn cap 0.6 × peers_avg).")
                adj = _apply_rule(target_cid, by_id, new_score, 3.0, "R7_COHERENCE_QUORUM",
                                   rationale, other_members)
                if adj:
                    adjustments.append(adj)
    return adjustments


# ═════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR ENTRY
# ═════════════════════════════════════════════════════════════════════════════

def apply_contextual_overlay(bloc_results: dict, page_type: str,
                              capture_dir: pathlib.Path | None = None,
                              matrix_path: pathlib.Path | None = None) -> dict:
    """Apply synergy-group compensation rules. Mutates bloc_results in place.
    Returns an overlay trace dict."""
    matrix = load_doctrine_matrix(matrix_path)
    synergy_groups = matrix.get("synergy_groups", {})
    idx = _index_criteria(matrix)
    if not idx:
        return {"applied": False, "reason": "doctrine matrix not available"}

    perception = _load_perception_v13(capture_dir)
    ctx = {"page_type": page_type, "perception": perception}
    by_id = _index_kept_criteria(bloc_results)
    adjustments: list[dict] = []

    # Fire rules R1-R6 in order
    for rule_fn in (
        rule_R1_hero_rescue,
        rule_R2_proof_rescue,
        rule_R3_fivesec_rescue,
        rule_R4_benefit_flow_rescue,
        rule_R5_manipulation_flag,
        rule_R6_ux_rhythm_rescue,
    ):
        adj = rule_fn(by_id, ctx)
        if adj:
            adjustments.append(adj)

    # Fire R7 catch-all
    quorum_adj = rule_R7_coherence_quorum(by_id, ctx, synergy_groups, idx)
    adjustments.extend(quorum_adj)

    # Recompute pillar totals for any pillar touched
    touched_pillars = {a["pillar"] for a in adjustments}
    pillar_deltas: dict[str, float] = {}
    for pillar in touched_pillars:
        blk = bloc_results.get(pillar, {})
        old_total = float(blk.get("rawTotal") or 0)
        raw_max = float(blk.get("rawMax") or 0)
        new_total = sum(_score_of(i) for i in (blk.get("kept_criteria") or []))
        # Add non-kept contributors preserved as "extensions" etc. — keep diff
        # Since kept_criteria is what rawTotal is built from (post-filter), recompute
        blk["pre_contextual_rawTotal"] = round(old_total, 2)
        blk["rawTotal"] = round(new_total, 2)
        blk["score100"] = round(new_total / raw_max * 100, 1) if raw_max else 0.0
        blk["contextual_delta"] = round(new_total - old_total, 2)
        pillar_deltas[pillar] = round(new_total - old_total, 2)

    # Group-level coherence stats (informational)
    group_stats = {}
    for gid, group in synergy_groups.items():
        members = [m for m in group.get("members", []) if m in by_id]
        if len(members) < 2:
            continue
        scores = [_score_of(by_id[m]["item"]) for m in members]
        mean = _avg(scores)
        var = _avg([(s - mean) ** 2 for s in scores])
        group_stats[gid] = {
            "members_present": len(members),
            "mean_score": round(mean, 2),
            "sigma": round(math.sqrt(var), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
        }

    total_delta = round(sum(a["delta"] for a in adjustments), 2)
    return {
        "applied": bool(adjustments),
        "version": "1.0 (doctrine v3.2.0-draft)",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "adjustments": adjustments,
        "adjustments_count": len(adjustments),
        "total_delta": total_delta,
        "by_pillar_delta": pillar_deltas,
        "perception_available": bool(perception),
        "group_stats": group_stats,
        "rules_fired": sorted({a["rule_id"] for a in adjustments}),
    }


# ═════════════════════════════════════════════════════════════════════════════
# CLI (for standalone testing on a capture dir)
# ═════════════════════════════════════════════════════════════════════════════

def _cli():
    import sys
    if len(sys.argv) < 3:
        print("Usage: score_contextual_overlay.py <label> <page_type>", file=sys.stderr)
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2]
    # Find project root
    p = pathlib.Path(__file__).resolve()
    while p != p.parent:
        if (p / "data" / "captures").exists():
            root = p
            break
        p = p.parent
    else:
        print("project root not found", file=sys.stderr)
        sys.exit(1)
    for sub in ("captures", "golden"):
        cap_dir = root / "data" / sub / label / page_type
        score_file = cap_dir / "score_page_type.json"
        if score_file.exists():
            break
    else:
        print(f"no score_page_type.json for {label}/{page_type}", file=sys.stderr)
        sys.exit(1)
    result = json.loads(score_file.read_text(encoding="utf-8"))
    bloc_results = result.get("universal", {}).get("byPillar", {})
    overlay = apply_contextual_overlay(bloc_results, page_type, capture_dir=cap_dir)
    print(json.dumps(overlay, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _cli()
