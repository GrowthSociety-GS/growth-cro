"""Reco doctrine + scope matrix caches, JSON validation, ICE compute, fallback template.

Single concern: data shape — loading reference doctrine JSONs, validating the
LLM's reco output, computing ICE/fallback dicts. No prompt strings, no API calls,
no orchestration.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────────
PLAYBOOK_DIR = Path("playbook")
SCOPE_MATRIX_PATH = Path("data/doctrine/criteria_scope_matrix_v1.json")
# RECO_TEMPLATES_PATH archived V19 — _style_templates_block returns "" if absent.
RECO_TEMPLATES_PATH = PLAYBOOK_DIR / "reco_templates_v14_1b.json"

# V23.D — page types with a funnel flow that gets a dedicated context block
FUNNEL_PAGE_TYPES = {"quiz_vsl", "lp_sales", "lp_leadgen", "signup", "lead_gen_simple"}

# Required keys on every successful LLM-produced reco. `headline` is optional
# for retro-compat but requested in the prompt.
REQUIRED_JSON_KEYS = {
    "before",
    "after",
    "why",
    "expected_lift_pct",
    "effort_hours",
    "priority",
    "implementation_notes",
}


# ────────────────────────────────────────────────────────────────
# Caches (module-level singletons; refreshed only on import)
# ────────────────────────────────────────────────────────────────
_scope_cache: dict[str, dict] = {}
_doctrine_cache: dict[str, Any] = {}
_reco_templates_cache: list[dict] | None = None
_killer_rules_cache: dict | None = None
_thresholds_cache: dict | None = None


# ────────────────────────────────────────────────────────────────
# Scope matrix
# ────────────────────────────────────────────────────────────────
def load_scope_matrix() -> dict[str, dict]:
    """Return {criterion_id: {scope, synergy_group, pillar}}. Memoised."""
    if _scope_cache:
        return _scope_cache
    if not SCOPE_MATRIX_PATH.exists():
        return {}
    try:
        m = json.load(open(SCOPE_MATRIX_PATH))
        for c in m.get("criteria", []):
            cid = c.get("id")
            if cid:
                _scope_cache[cid] = {
                    "scope": c.get("scope"),
                    "synergy_group": c.get("synergy_group"),
                    "pillar": c.get("pillar"),
                }
    except Exception:
        pass
    return _scope_cache


def criterion_scope(crit_id: str) -> str:
    """'ENSEMBLE' | 'ASSET' | 'UNKNOWN'. Default ENSEMBLE if absent."""
    idx = load_scope_matrix()
    return (idx.get(crit_id) or {}).get("scope") or "ENSEMBLE"


# ────────────────────────────────────────────────────────────────
# Reco templates V14 (style-only references)
# ────────────────────────────────────────────────────────────────
def load_reco_templates() -> list[dict]:
    global _reco_templates_cache
    if _reco_templates_cache is not None:
        return _reco_templates_cache
    if not RECO_TEMPLATES_PATH.exists():
        _reco_templates_cache = []
        return []
    try:
        data = json.load(open(RECO_TEMPLATES_PATH))
        _reco_templates_cache = data.get("templates") or []
    except Exception:
        _reco_templates_cache = []
    return _reco_templates_cache


def find_style_templates(
    crit_id: str,
    page_type: str,
    intent_slug: str,
    business_category: str,
    score_band: str = "critical",
    limit: int = 2,
) -> list[dict]:
    """Up to `limit` templates matching the context, ranked by specificity."""
    templates = load_reco_templates()
    if not templates:
        return []

    def match_score(t: dict) -> int:
        s = 0
        if t.get("criterion_id") == crit_id:
            s += 10
        if t.get("page_type") == page_type:
            s += 3
        if t.get("intent_slug") == intent_slug:
            s += 2
        if t.get("business_category") == business_category:
            s += 2
        if t.get("score_band") == score_band:
            s += 1
        return s

    ranked = [(match_score(t), t) for t in templates if t.get("criterion_id") == crit_id]
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in ranked[:limit]]


# ────────────────────────────────────────────────────────────────
# Doctrine loading (bloc_*_v3.json or bloc_*_v3-3.json + adjacent reference JSONs)
# ────────────────────────────────────────────────────────────────
def load_doctrine(doctrine_version: str = "3.2.1") -> dict:
    """Load doctrine blocs + adjacent reference JSONs.

    Default '3.2.1' loads bloc_*_v3.json (backward compatible — 56 clients existants).
    Pass doctrine_version='3.3' to opt into bloc_*_v3-3.json + cre_oco_tables.json
    + applicability_matrix_v2.json (CRE Fusion, Task #18).

    Cache key is doctrine_version-scoped: caller can switch versions in the same process.
    """
    from growthcro.scoring.pillars import resolve_doctrine_paths

    cache_key = f"_v{doctrine_version}"
    if cache_key in _doctrine_cache:
        return _doctrine_cache[cache_key]

    paths = resolve_doctrine_paths(doctrine_version)
    bundle: dict[str, Any] = {"doctrine_version": doctrine_version, "blocs": {}}

    bloc_glob = paths["bloc_glob"]
    for f in PLAYBOOK_DIR.glob(bloc_glob):
        try:
            d = json.load(open(f))
            # Strip suffix to get pillar key (bloc_1_hero_v3 → bloc_1_hero ; bloc_1_hero_v3-3 → bloc_1_hero)
            pillar = f.stem.replace("_v3-3", "").replace("_v3", "")
            bundle["blocs"][pillar] = d
        except Exception as e:
            print(f"cannot load {f}: {e}", file=sys.stderr)

    for name in ("anti_patterns", "guardrails", "prerequisites", "page_type_criteria", "ab_angles"):
        f = PLAYBOOK_DIR / f"{name}.json"
        if f.exists():
            try:
                bundle[name] = json.load(open(f))
            except Exception:
                pass

    # V3.3 — load cre_oco_tables.json + applicability_matrix_v2.json
    if doctrine_version == "3.3":
        oco_path = paths.get("oco_tables")
        if oco_path and oco_path.exists():
            try:
                bundle["cre_oco_tables"] = json.load(open(oco_path))
            except Exception as e:
                print(f"cannot load {oco_path}: {e}", file=sys.stderr)
        am2_path = paths.get("applicability_matrix")
        if am2_path and am2_path.exists():
            try:
                bundle["applicability_matrix_v2"] = json.load(open(am2_path))
            except Exception as e:
                print(f"cannot load {am2_path}: {e}", file=sys.stderr)

    _doctrine_cache[cache_key] = bundle
    return bundle


def get_criterion_doctrine(crit_id: str, doctrine_version: str = "3.2.1") -> dict | None:
    """Find the doctrine entry (label, scoring, rules) for one criterion.

    Pass doctrine_version='3.3' to read enriched criterion (research_first + oco_refs +
    ice_template + cre_alignment from bloc).
    """
    doc = load_doctrine(doctrine_version)
    for pillar_key, pillar_data in (doc.get("blocs") or {}).items():
        criteria = pillar_data.get("criteria") or pillar_data.get("criterions") or []
        for c in criteria:
            if c.get("criterion_id") == crit_id or c.get("id") == crit_id:
                return {
                    "pillar": pillar_key,
                    "criterion": c,
                    "cre_alignment": pillar_data.get("cre_alignment"),  # V3.3 only — None for V3.2.1
                }
    return None


def get_criterion_oco_refs(crit_id: str) -> list[str]:
    """V3.3 — return oco_refs (list of objection IDs from cre_oco_tables) for a criterion.

    Empty list when doctrine_version=3.3 not loaded or crit_id has no refs.
    Used by reco enricher to attach oco_anchors downstream.
    """
    doc = load_doctrine("3.3")
    for pillar_data in (doc.get("blocs") or {}).values():
        for c in pillar_data.get("criteria") or []:
            if c.get("id") == crit_id:
                return list(c.get("oco_refs") or [])
    return []


def get_criterion_research_first(crit_id: str) -> bool:
    """V3.3 — return True if criterion requires research_inputs to score correctly."""
    doc = load_doctrine("3.3")
    for pillar_data in (doc.get("blocs") or {}).values():
        for c in pillar_data.get("criteria") or []:
            if c.get("id") == crit_id:
                return bool(c.get("research_first"))
    return False


def get_criterion_anti_patterns(crit_id: str) -> list[dict]:
    doc = load_doctrine()
    ap_data = doc.get("anti_patterns") or {}
    if isinstance(ap_data, dict):
        inner = ap_data.get("anti_patterns")
        if isinstance(inner, dict):
            patterns = list(inner.values())
        elif isinstance(inner, list):
            patterns = inner
        else:
            patterns = [v for k, v in ap_data.items() if not k.startswith("_") and isinstance(v, dict)]
    else:
        patterns = ap_data if isinstance(ap_data, list) else []
    out = []
    for p in patterns:
        if not isinstance(p, dict):
            continue
        applies = p.get("applies_to") or p.get("linked_criteria") or p.get("criteria") or []
        if crit_id in applies:
            out.append(p)
    return out


# ────────────────────────────────────────────────────────────────
# Killer rules + thresholds
# ────────────────────────────────────────────────────────────────
def load_killer_rules() -> dict:
    global _killer_rules_cache
    if _killer_rules_cache is not None:
        return _killer_rules_cache
    f = PLAYBOOK_DIR / "killer_rules.json"
    if not f.exists():
        _killer_rules_cache = {}
        return {}
    try:
        _killer_rules_cache = json.load(open(f)).get("killer_rules", {})
    except Exception:
        _killer_rules_cache = {}
    return _killer_rules_cache


def load_thresholds() -> dict:
    global _thresholds_cache
    if _thresholds_cache is not None:
        return _thresholds_cache
    f = PLAYBOOK_DIR / "thresholds_benchmarks.json"
    if not f.exists():
        _thresholds_cache = {}
        return {}
    try:
        _thresholds_cache = json.load(open(f))
    except Exception:
        _thresholds_cache = {}
    return _thresholds_cache


# ────────────────────────────────────────────────────────────────
# Cluster picking + summary extraction
# ────────────────────────────────────────────────────────────────
CRITERION_ROLE_MAP: dict[str, str | None] = {
    "hero_": "HERO",
    "per_01": "HERO",
    "per_": "SOCIAL_PROOF",
    "ux_01": "HERO",
    "ux_": None,
    "coh_": "HERO",
    "psy_": "HERO",
    "tech_": None,
    "ut_": "UTILITY_BANNER",
}


def pick_cluster_for_criterion(crit_id: str, clusters: list[dict]) -> dict | None:
    preferred_role = CRITERION_ROLE_MAP.get(crit_id)
    if preferred_role is None:
        for prefix, role in CRITERION_ROLE_MAP.items():
            if crit_id.startswith(prefix):
                preferred_role = role
                break
    if preferred_role is None:
        return None
    for c in clusters:
        if c.get("role") == preferred_role:
            return c
    return None


def extract_cluster_text_summary(cluster: dict, all_elements: list[dict]) -> dict:
    texts: list[str] = []
    ctas: list[dict] = []
    headings: list[dict] = []
    images = 0
    for idx in cluster.get("element_indices", []):
        if idx >= len(all_elements):
            continue
        el = all_elements[idx]
        t = (el.get("text") or "").strip()
        if el.get("type") == "heading":
            headings.append(
                {
                    "tag": el.get("tag"),
                    "text": t,
                    "font_size": el.get("computedStyle", {}).get("fontSize"),
                }
            )
        elif el.get("type") == "cta":
            ctas.append(
                {
                    "text": t,
                    "href": el.get("href"),
                    "tag": el.get("tag"),
                }
            )
        elif el.get("type") == "image":
            images += 1
        if t:
            texts.append(t)
    return {
        "bbox": cluster.get("bbox"),
        "role": cluster.get("role"),
        "headings": headings[:6],
        "ctas": ctas[:8],
        "image_count": images,
        "joined_text": " · ".join(texts[:20])[:600],
    }


# ────────────────────────────────────────────────────────────────
# ICE estimate (used by prompt builder, computed once per criterion)
# ────────────────────────────────────────────────────────────────
def compute_ice_estimate(
    crit_id: str,
    pillar: str,
    current_score: float,
    max_score: float,
    vision_lifted: bool,
    intelligence_lifted: bool,
    killer_violated: bool,
    doctrine_version: str = "3.2.1",
    research_inputs_available: bool = False,
    voc_verbatims_available: bool = False,
) -> dict:
    """V23 — Pre-compute ICE estimate suggested to Haiku as a doctrinal starting point.

    V3.3 (Task #18) — when doctrine_version='3.3' and the criterion is research_dependent
    (cf. applicability_matrix_v2.json), apply Confidence penalty/boost:
    - penalty_if_no_research_inputs : -2 (rule_research_first_confidence_penalty)
    - boost_if_voc_available : +2 (rule_voc_available_confidence_boost)

    Default '3.2.1' behavior unchanged — backward compatible for 56 existing clients.
    """
    th = load_thresholds().get("ice_framework", {})
    impact_lever_by_pillar = th.get("impact_lever_by_pillar", {})
    impact_modifier_by_criterion = th.get("impact_modifier_by_criterion", {})

    pillar_lever = impact_lever_by_pillar.get(pillar, 1.0)
    crit_modifier = impact_modifier_by_criterion.get(crit_id, pillar_lever)
    score_pct = (current_score / max_score) if max_score else 0
    severity = (1 - score_pct)
    impact_raw = crit_modifier * (1 + severity * 2)
    impact = max(1, min(10, round(impact_raw * 2.5)))

    confidence = th.get("confidence_default", 7)
    if killer_violated:
        confidence = th.get("confidence_modifiers", {}).get("killer_violated", 9)
    elif vision_lifted or intelligence_lifted:
        confidence = th.get("confidence_modifiers", {}).get("vision_lifted", 8)

    # V3.3 — research-first adjustment
    if doctrine_version == "3.3":
        doc = load_doctrine("3.3")
        am2 = doc.get("applicability_matrix_v2") or {}
        research_dep_map = am2.get("research_dependent_by_criterion") or {}
        if research_dep_map.get(crit_id) is True:
            if not research_inputs_available:
                confidence = max(1, confidence - 2)
            if voc_verbatims_available:
                confidence = min(10, confidence + 2)

    pillar_to_ease_default = {
        "hero": 7,
        "persuasion": 6,
        "ux": 4,
        "coherence": 6,
        "psycho": 7,
        "tech": 4,
    }
    ease = pillar_to_ease_default.get(pillar, 5)

    ice_score = (impact * 2) + confidence + ease
    return {
        "impact_estimate": impact,
        "confidence_estimate": confidence,
        "ease_estimate": ease,
        "ice_score_estimate": ice_score,
        "priority_suggested": (
            "P0" if ice_score >= 30 else "P1" if ice_score >= 22 else "P2" if ice_score >= 14 else "P3"
        ),
        "doctrine_version": doctrine_version,
    }


def compute_ice_score_v13(reco: dict) -> float:
    """ICE = Impact × Confidence × Ease — final post-LLM score (0-100ish)."""
    lift = float(reco.get("expected_lift_pct") or 0)
    effort_h = float(reco.get("effort_hours") or 8)
    impact = min(10, max(1, lift / 1.5))
    effort_score = min(5, max(1, (effort_h / 8) + 1))
    conf_by_prio = {"P0": 1.0, "P1": 0.85, "P2": 0.7, "P3": 0.55}
    confidence = conf_by_prio.get(reco.get("priority"), 0.6)
    ice = impact * confidence * (6 - effort_score)
    return round(ice * 4, 1)


# ────────────────────────────────────────────────────────────────
# JSON parsing + validation (post-LLM)
# ────────────────────────────────────────────────────────────────
def extract_json_from_response(text: str) -> dict | None:
    """Extract the first valid JSON object from an LLM response (tolerates fences/prose)."""
    if not text:
        return None
    try:
        d = json.loads(text.strip())
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    blob = m.group(0)
    try:
        return json.loads(blob)
    except Exception:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", blob).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return None


def validate_reco(reco: dict) -> tuple[bool, str]:
    """(ok, error_msg). All required fields must be present and well-typed."""
    missing = REQUIRED_JSON_KEYS - set(reco.keys())
    if missing:
        return False, f"missing keys: {missing}"
    try:
        lift = float(reco.get("expected_lift_pct") or 0)
        if not (0 <= lift <= 50):
            return False, f"expected_lift_pct out of range: {lift}"
        # V25.D.4 — clamp effort=0 to 1 (LLM occasionally emits 0 for trivial fixes).
        effort_raw = reco.get("effort_hours")
        try:
            effort = int(effort_raw if effort_raw is not None else 0)
        except (ValueError, TypeError):
            effort = 0
        if effort <= 0:
            reco["effort_hours"] = 1
            effort = 1
        if effort > 80:
            return False, f"effort_hours out of range: {effort}"
        pri = reco.get("priority")
        if pri not in {"P0", "P1", "P2", "P3"}:
            return False, f"invalid priority: {pri}"
    except (ValueError, TypeError) as e:
        return False, f"type error: {e}"
    return True, ""


# ────────────────────────────────────────────────────────────────
# Fallback template (LLM hard-fail → V12-shaped reco kept visible)
# ────────────────────────────────────────────────────────────────
def fallback_reco_from_v12(v12_text: str, criterion_id: str, reason: str = "unknown") -> dict:
    return {
        "before": f"FALLBACK V12 — LLM échec post-retry ({reason}) — {v12_text[:200]}",
        "after": f"FALLBACK V12 — recommandation V12 non-enrichie ({reason}). Relance: --force --only {criterion_id}",
        "why": f"LLM enrichment failed after structured retry ({reason}) — V12 template-based reco restored for non-silent visibility.",
        "expected_lift_pct": 3.0,
        "effort_hours": 4,
        "priority": "P2",
        "implementation_notes": f"criterion={criterion_id} — fallback_reason={reason} — re-run with --force --only {criterion_id}",
        "_fallback": True,
        "_fallback_reason": reason,
    }


# ────────────────────────────────────────────────────────────────
# Killer-violation detection (page-level, observable signals only)
# ────────────────────────────────────────────────────────────────
def check_killer_violations(perception: dict, vision_signals: dict, crit_id: str) -> list[dict]:
    """Run killer_rules.json against page state. Returns visible violations."""
    rules = load_killer_rules()
    if not rules:
        return []
    violations: list[dict] = []

    desktop = vision_signals.get("desktop") or {}
    h1_present = bool(desktop.get("h1"))
    subtitle_present = bool(desktop.get("subtitle"))
    cta_present = bool(desktop.get("primary_cta"))
    fold_score = (desktop.get("fold_readability") or {}).get("score_1_to_5")
    sp_present = bool((desktop.get("social_proof_in_fold") or {}).get("present"))

    if not (h1_present and (subtitle_present or cta_present)):
        violations.append(rules.get("hero_5second_test_failure", {}))

    if isinstance(fold_score, int) and fold_score <= 2:
        if rules.get("hero_5second_test_failure") and rules["hero_5second_test_failure"] not in violations:
            violations.append(rules["hero_5second_test_failure"])

    bf_sections = desktop.get("below_fold_sections") or []
    proof_sections = [
        s for s in bf_sections
        if isinstance(s, dict)
        and s.get("type") in {"testimonials", "case_studies", "social_proof", "logos", "stats"}
    ]
    if not sp_present and not proof_sections:
        violations.append(rules.get("zero_concrete_proof", {}))

    return [v for v in violations if v]


# ────────────────────────────────────────────────────────────────
# V12 baseline computation (inlined from deprecated reco_enricher V12)
# ────────────────────────────────────────────────────────────────
def compute_recos_brutes_from_scores(page_dir: Path) -> list[dict]:
    """V24.0 — compute the criteria-to-treat list directly from score_<pillar>.json.

    For each criterion with score_pct < 75 (and not excluded by page_type filter),
    create a V12-shaped entry: {criterion_id, priority, _score_pct, _pillar, ...}.
    """
    recos_brutes: list[dict] = []
    seen_crits: set[str] = set()

    for sf in page_dir.glob("score_*.json"):
        stem = sf.stem
        if stem in {
            "score_utility_banner", "score_semantic", "score_intelligence",
            "score_page_type", "score_funnel", "score_specific_criteria",
        }:
            continue
        try:
            d = json.load(open(sf))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue

        pillar = stem.replace("score_", "")
        criteria = d.get("criteria") or d.get("kept_criteria") or d.get("criterions") or []
        for c in criteria:
            cid = c.get("criterion_id") or c.get("id")
            if not cid or cid in seen_crits:
                continue
            if c.get("applicable") is False:
                continue
            score_pct = c.get("score_pct")
            if score_pct is None:
                raw_score = c.get("score")
                raw_max = c.get("max") or c.get("max_score")
                if raw_score is not None and raw_max:
                    try:
                        score_pct = round(100 * float(raw_score) / float(raw_max), 1)
                    except Exception:
                        score_pct = None
            if score_pct is None:
                continue
            if score_pct >= 75:
                continue

            if score_pct < 40:
                priority = "P1"
            elif score_pct < 60:
                priority = "P2"
            else:
                priority = "P3"

            recos_brutes.append({
                "criterion_id": cid,
                "priority": priority,
                "_score_pct": score_pct,
                "_pillar": pillar,
                "anti_patterns": [],
                "reco_text": "",
                "ice_score": 0,
            })
            seen_crits.add(cid)

    return recos_brutes


# ────────────────────────────────────────────────────────────────
# Grounding check (post-LLM: client name + page elements appear in reco)
# ────────────────────────────────────────────────────────────────
_HINT_MIN_CHARS = 8


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _compact(s: str) -> str:
    return re.sub(r"[\W_]+", "", _norm(s))


def _client_name_matches(raw_name: str, haystack: str) -> bool:
    name = _norm(raw_name)
    if len(name) < 3:
        return False
    variants = {
        name,
        name.replace("_", " "),
        name.replace("-", " "),
    }
    compact_haystack = _compact(haystack)
    return any(v in haystack or _compact(v) in compact_haystack for v in variants if len(v) >= 3)


def check_grounding(reco: dict, hints: dict) -> tuple[int, list[str]]:
    """(grounding_score_0_to_3, issues[]). See split-map for scoring rules."""
    issues: list[str] = []
    if not hints:
        return 0, ["no_hints_provided"]

    haystack = _norm(" ".join([
        reco.get("before") or "",
        reco.get("after") or "",
        reco.get("why") or "",
    ]))

    score = 0
    client_name = hints.get("client_name") or ""
    if _client_name_matches(client_name, haystack):
        score += 1
    else:
        issues.append(f"client_name_missing:{_norm(client_name)!r}")

    h1 = _norm(hints.get("h1_text") or "")
    sub = _norm(hints.get("subtitle_text") or "")
    if (len(h1) >= _HINT_MIN_CHARS and h1[: min(40, len(h1))] in haystack) or (
        len(sub) >= _HINT_MIN_CHARS and sub[: min(40, len(sub))] in haystack
    ):
        score += 1
    else:
        if h1 or sub:
            issues.append("real_copy_not_cited")

    cta = _norm(hints.get("primary_cta_text") or "")
    if len(cta) >= _HINT_MIN_CHARS and cta in haystack:
        score += 1
    elif len(cta) < _HINT_MIN_CHARS:
        score += 1
    else:
        issues.append(f"cta_not_cited:{cta!r}")

    return score, issues


# ────────────────────────────────────────────────────────────────
# Opportunity Layer wiring (Issue #49)
# ────────────────────────────────────────────────────────────────
def build_opportunity_link_map(opp_batch: Any) -> dict[str, str]:
    """Map ``criterion_ref → opportunity.id`` from an ``OpportunityBatch``.

    Used by the recos orchestrator to attach ``linked_opportunity_id`` on
    each generated reco. ``opp_batch`` accepts ``None`` (page has no
    ``opportunities.json`` yet → empty map → backward compat) or any
    ``OpportunityBatch``-shaped object exposing ``.opportunities`` with
    ``criterion_ref`` and ``id`` per item.

    Pure function: no I/O. Caller (orchestrator) does the load.
    """
    if opp_batch is None:
        return {}
    out: dict[str, str] = {}
    for opp in getattr(opp_batch, "opportunities", []) or []:
        crit = getattr(opp, "criterion_ref", None)
        opp_id = getattr(opp, "id", None)
        if crit and opp_id:
            out[crit] = opp_id
    return out
