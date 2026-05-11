#!/usr/bin/env python3
"""Build playbook/bloc_*_v3-3.json from existing bloc_*_v3.json files.

Adds V3.3 CRE Fusion enrichments per criterion:
- research_first (bool): does this criterion require client research (visitor survey,
  chat logs, support tickets) to evaluate accurately?
- oco_refs (list): O/CO objection IDs from cre_oco_tables.json this criterion addresses.
- ice_template (dict): template { impact_estimator, confidence_factors, ease_factors }
  to pre-fill ICE scoring on the generated reco.

Plus a bloc-level `cre_alignment` section:
- 9step_phase: which CRO process phase (discovery|hypothesis|test|iterate)
- principle: governing CRE principle (e.g. "don't guess, discover")
- research_inputs_required: list of research_inputs the criterion class needs.

Backward compatible: V3.2.1 files are untouched. Run idempotently.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYBOOK = ROOT / "playbook"

# ─── Per-pillar CRE alignment defaults ───
PILLAR_CRE_ALIGNMENT = {
    "hero": {
        "9step_phase": "discovery",
        "principle": "Don't guess, discover — Hero must be tested against visitor research, not designer taste.",
        "research_inputs_required": ["visitor_surveys", "support_tickets", "chat_logs"],
        "notes": [
            "Hero ATF is where 5-second test plays out. Without research, you guess the promise visitors care about.",
            "O/CO mapping: hero must address top-3 objections explicitly (H1/sub/proof).",
        ],
    },
    "persuasion": {
        "9step_phase": "hypothesis",
        "principle": "Objections > features — every persuasion criterion answers a documented O/CO pair.",
        "research_inputs_required": ["visitor_surveys", "support_tickets", "chat_logs", "nps_responses"],
        "notes": [
            "Per_03 (objections) is the gravity center of this pillar. Without VOC, objections become invented.",
            "ICE template emphasizes confidence boost from real verbatims.",
        ],
    },
    "ux": {
        "9step_phase": "test",
        "principle": "Friction is measured, not assumed — heatmaps + session recordings beat 'looks clean'.",
        "research_inputs_required": ["session_recordings", "heatmaps_summary", "support_tickets"],
        "notes": [
            "UX criteria are test-phase: fixes ship as A/B variants with 95% confidence.",
            "Mobile-first scoring uses real device telemetry, not Chrome DevTools sim.",
        ],
    },
    "coherence": {
        "9step_phase": "discovery",
        "principle": "Scent matching = ad → LP → conversion path coherence (not designer-flavor coherence).",
        "research_inputs_required": ["ad_creative_audit", "visitor_surveys", "search_query_data"],
        "notes": [
            "Coh_03 (scent matching) requires ad copy + LP copy side-by-side audit.",
            "Coh_04 (VPC alignment) needs Jobs/Pains/Gains from interviews, not personas-as-templates.",
        ],
    },
    "psycho": {
        "9step_phase": "hypothesis",
        "principle": "Trigger only what the VOC reveals — manipulation = mismatch with real motivations.",
        "research_inputs_required": ["visitor_surveys", "voc_verbatims", "interview_transcripts"],
        "notes": [
            "Psy_08 (VOC) is THE upstream input — verbatims pulled from interviews & surveys.",
            "Psy_01/02 (urgency/scarcity) require legitimate reasons backed by data, never inflated.",
        ],
    },
    "tech": {
        "9step_phase": "test",
        "principle": "Tech is ASSET-level — measured, not estimated. 95% confidence comes from real telemetry.",
        "research_inputs_required": ["pagespeed_telemetry", "real_user_monitoring", "uptime_logs"],
        "notes": [
            "Tech criteria do not benefit from O/CO mapping the same way persuasion does.",
            "ICE template: confidence is anchored to telemetry availability; ease is engineer-hour estimate.",
        ],
    },
    "utility_elements": {
        "9step_phase": "iterate",
        "principle": "Peripherals (banners, modals, cookies) are tested last — they fix what funnel did not solve.",
        "research_inputs_required": ["session_recordings", "support_tickets"],
        "notes": [
            "Utility elements are iterate-phase: post-funnel optimization, not primary lever.",
            "O/CO mapping minimal — these are friction reducers, not value sellers.",
        ],
    },
}

# ─── Per-criterion research_first flags ───
# True = needs documented VOC / survey / ticket inputs before scoring well.
# False = can be scored from page artifact alone (ASSET-level).
RESEARCH_FIRST = {
    # Hero
    "hero_01": True,   # H1 promise must match what visitors care about
    "hero_02": True,   # subtitle clarifies the audience research result
    "hero_03": False,  # CTA visibility is technical
    "hero_04": False,  # visual coherence is asset-level
    "hero_05": False,  # social proof presence is asset-level
    "hero_06": True,   # 5-sec test requires real visitors (or research proxy)
    # Persuasion — heavy research dependency
    "per_01": True,
    "per_02": True,
    "per_03": True,
    "per_04": False,  # counting proof formats is asset-level
    "per_05": False,
    "per_06": True,   # FAQ requires real objection list
    "per_07": True,   # tone must match VOC
    "per_08": True,
    "per_09": True,   # awareness level = VOC-derived
    "per_10": False,
    "per_11": True,
    # UX
    "ux_01": False,
    "ux_02": False,
    "ux_03": True,    # reading pattern needs eyetracking/session research
    "ux_04": False,
    "ux_05": False,
    "ux_06": False,
    "ux_07": False,
    "ux_08": True,    # friction audit (5 types) benefits from session research
    # Coherence
    "coh_01": True,
    "coh_02": True,
    "coh_03": True,   # scent matching requires ad audit
    "coh_04": True,   # VPC alignment = Jobs/Pains/Gains from interviews
    "coh_05": False,
    "coh_06": False,
    "coh_07": True,
    "coh_08": False,
    "coh_09": True,
    # Psycho
    "psy_01": True,
    "psy_02": True,
    "psy_03": True,
    "psy_04": True,
    "psy_05": False,
    "psy_06": False,
    "psy_07": True,
    "psy_08": True,  # VOC is THE research_first criterion
    # Tech — all asset-level
    "tech_01": False,
    "tech_02": False,
    "tech_03": False,
    "tech_04": False,
    "tech_05": False,
    # Utility
    "ut_01": False,
    "ut_02": False,
    "ut_03": False,
    "ut_04": True,   # scent trail requires paid audit
    "ut_05": False,
    "ut_06": False,
    "ut_07": True,   # tonal coherence is VOC-derived
}

# ─── Per-criterion O/CO refs (page_type-scoped IDs from cre_oco_tables) ───
# Format: {criterion_id: ["<page_type>:<objection_id>"]}
# We pre-populate the structural backbone — page_type-specific objections live in cre_oco_tables.
OCO_REFS = {
    # Hero — addresses awareness/comprehension objections
    "hero_01": ["*:obj_value_unclear", "*:obj_not_for_me"],
    "hero_02": ["*:obj_value_unclear", "*:obj_not_for_me"],
    "hero_03": ["*:obj_what_next", "*:obj_friction_high"],
    "hero_04": ["*:obj_value_unclear", "*:obj_credibility_low"],
    "hero_05": ["*:obj_credibility_low", "*:obj_risk_high"],
    "hero_06": ["*:obj_attention_lost", "*:obj_value_unclear"],
    # Persuasion — addresses persuasion-stage objections
    "per_01": ["*:obj_value_unclear", "*:obj_not_for_me", "*:obj_too_expensive"],
    "per_02": ["*:obj_credibility_low", "*:obj_too_corporate"],
    "per_03": ["*:obj_too_expensive", "*:obj_risk_high", "*:obj_alternatives_exist", "*:obj_complexity_high"],
    "per_04": ["*:obj_credibility_low", "*:obj_risk_high"],
    "per_05": ["*:obj_credibility_low", "*:obj_no_real_users"],
    "per_06": ["*:obj_complexity_high", "*:obj_alternatives_exist", "*:obj_risk_high"],
    "per_07": ["*:obj_too_corporate", "*:obj_not_for_me"],
    "per_08": ["*:obj_too_corporate", "*:obj_ai_slop"],
    "per_09": ["*:obj_not_ready_yet", "*:obj_value_unclear"],
    "per_10": ["*:obj_complexity_high"],
    "per_11": ["*:obj_value_unclear", "*:obj_not_for_me"],
    # UX — addresses friction objections
    "ux_01": ["*:obj_attention_lost", "*:obj_complexity_high"],
    "ux_02": ["*:obj_attention_lost"],
    "ux_03": ["*:obj_too_long_to_read", "*:obj_attention_lost"],
    "ux_04": ["*:obj_what_next", "*:obj_friction_high"],
    "ux_05": ["*:obj_friction_high"],
    "ux_06": ["*:obj_attention_lost", "*:obj_what_next"],
    "ux_07": ["*:obj_friction_high"],
    "ux_08": ["*:obj_friction_high", "*:obj_form_too_long"],
    # Coherence — addresses fit/positioning objections
    "coh_01": ["*:obj_value_unclear"],
    "coh_02": ["*:obj_not_for_me"],
    "coh_03": ["*:obj_bait_and_switch", "*:obj_value_unclear"],
    "coh_04": ["*:obj_alternatives_exist", "*:obj_value_unclear"],
    "coh_05": ["*:obj_too_corporate"],
    "coh_06": ["*:obj_attention_lost", "*:obj_what_next"],
    "coh_07": ["*:obj_not_for_me", "*:obj_alternatives_exist"],
    "coh_08": ["*:obj_attention_lost"],
    "coh_09": ["*:obj_alternatives_exist", "*:obj_value_unclear"],
    # Psycho — addresses risk/emotion objections
    "psy_01": ["*:obj_not_ready_yet", "*:obj_credibility_low"],
    "psy_02": ["*:obj_not_ready_yet"],
    "psy_03": ["*:obj_too_expensive"],
    "psy_04": ["*:obj_risk_high"],
    "psy_05": ["*:obj_credibility_low"],
    "psy_06": ["*:obj_not_ready_yet", "*:obj_friction_high"],
    "psy_07": ["*:obj_value_unclear"],
    "psy_08": ["*:obj_not_for_me", "*:obj_too_corporate"],
    # Tech — addresses trust/credibility objections
    "tech_01": ["*:obj_friction_high"],
    "tech_02": ["*:obj_friction_high"],
    "tech_03": [],
    "tech_04": [],
    "tech_05": ["*:obj_risk_high", "*:obj_credibility_low"],
    # Utility
    "ut_01": ["*:obj_attention_lost"],
    "ut_02": ["*:obj_credibility_low"],
    "ut_03": ["*:obj_bait_and_switch"],
    "ut_04": ["*:obj_bait_and_switch"],
    "ut_05": ["*:obj_attention_lost"],
    "ut_06": ["*:obj_friction_high"],
    "ut_07": ["*:obj_too_corporate"],
}

# ─── ICE templates per pillar ───
# Used as starting point — Haiku may override with finer estimates.
ICE_TEMPLATE_BY_PILLAR = {
    "hero": {
        "impact_estimator": "high — hero is the 5-second filter; fixes here move CVR most reliably",
        "confidence_factors": {
            "base": 7,
            "boost_if_killer_violated": 9,
            "boost_if_vision_lifted": 8,
            "penalty_if_no_research_inputs": -2,
        },
        "ease_factors": {
            "base": 7,
            "copy_only": 8,
            "copy_plus_visual": 6,
            "structural_redesign": 4,
        },
    },
    "persuasion": {
        "impact_estimator": "medium-high — copy fixes ship in days; impact depends on VOC quality",
        "confidence_factors": {
            "base": 6,
            "boost_if_voc_available": 9,
            "boost_if_killer_violated": 9,
            "penalty_if_no_research_inputs": -3,
        },
        "ease_factors": {
            "base": 6,
            "copy_only": 8,
            "narrative_rewrite": 4,
            "faq_extension": 7,
        },
    },
    "ux": {
        "impact_estimator": "medium — UX fixes have ceiling, but compound across funnel",
        "confidence_factors": {
            "base": 6,
            "boost_if_session_recordings_available": 8,
            "boost_if_killer_violated": 9,
        },
        "ease_factors": {
            "base": 5,
            "css_only": 8,
            "component_swap": 5,
            "responsive_rebuild": 3,
        },
    },
    "coherence": {
        "impact_estimator": "high — fixes upstream eliminate downstream confusion",
        "confidence_factors": {
            "base": 7,
            "boost_if_voc_available": 9,
            "boost_if_ad_audit_done": 9,
        },
        "ease_factors": {
            "base": 5,
            "messaging_only": 7,
            "structural_reposition": 3,
        },
    },
    "psycho": {
        "impact_estimator": "medium-high — triggers must match VOC, otherwise zero or negative",
        "confidence_factors": {
            "base": 6,
            "boost_if_voc_available": 9,
            "penalty_if_manipulation_risk": -3,
        },
        "ease_factors": {
            "base": 7,
            "copy_only": 8,
            "garantie_redesign": 5,
        },
    },
    "tech": {
        "impact_estimator": "high on CVR — every 100ms latency = -1% CVR (Amazon)",
        "confidence_factors": {
            "base": 8,
            "boost_if_telemetry_available": 9,
        },
        "ease_factors": {
            "base": 4,
            "config_change": 7,
            "image_optim": 6,
            "framework_swap": 2,
        },
    },
    "utility_elements": {
        "impact_estimator": "low-medium — peripheral fixes have small but cumulative effect",
        "confidence_factors": {"base": 6},
        "ease_factors": {"base": 7, "copy_only": 8, "component_swap": 5},
    },
}

V3_3_CHANGELOG_ENTRY = {
    "version": "3.3.0-cre-fusion",
    "date": "2026-05-11",
    "trigger": "Task #18 webapp-stratosphere — fusion CRE methodology (skill cro-methodology) avec V3.2.1.",
    "notes": [
        "Backward compatible : V3.2.1 reste défaut pour 56 clients existants ; V3.3 sur opt-in via doctrine_version='3.3'.",
        "Per-criterion enrichments : research_first flag, oco_refs (to cre_oco_tables.json), ice_template (per-pillar starting point).",
        "Bloc-level cre_alignment section : 9step_phase / principle / research_inputs_required.",
        "Criteria sémantique INCHANGÉE : label, scoring (top/ok/critical), examples, antiPatterns, killer flags, weight, pageTypes — tous préservés.",
        "Anti-pattern #3 respecté : on enrichit, on ne réinvente pas la grille.",
    ],
}


def enrich_bloc(bloc_v3: dict) -> dict:
    """Return a V3.3 enriched copy of a bloc V3 dict."""
    b = copy.deepcopy(bloc_v3)

    # Update bloc-level metadata
    b["version"] = "3.3.0-cre-fusion"
    b["amendedAt"] = "2026-05-11"
    changelog = b.setdefault("changelog", [])
    if not any((e.get("version") == "3.3.0-cre-fusion") for e in changelog):
        changelog.insert(0, V3_3_CHANGELOG_ENTRY)

    # Pillar detection (some files use 'pillar', others have label hints)
    pillar = b.get("pillar") or _infer_pillar_from_criteria(b.get("criteria", []))
    b["pillar"] = pillar  # normalize

    # CRE alignment block
    cre_align = PILLAR_CRE_ALIGNMENT.get(pillar)
    if cre_align:
        b["cre_alignment"] = copy.deepcopy(cre_align)

    # Default ICE template (criterion-level can override)
    default_ice = ICE_TEMPLATE_BY_PILLAR.get(pillar, {})

    for c in b.get("criteria", []):
        cid = c.get("id")
        if not cid:
            continue
        c["research_first"] = bool(RESEARCH_FIRST.get(cid, False))
        c["oco_refs"] = list(OCO_REFS.get(cid, []))
        c["ice_template"] = copy.deepcopy(default_ice)

    return b


def _infer_pillar_from_criteria(criteria: list[dict]) -> str:
    if not criteria:
        return "unknown"
    first_id = criteria[0].get("id", "")
    prefix = first_id.split("_")[0] if first_id else ""
    return {
        "hero": "hero",
        "per": "persuasion",
        "ux": "ux",
        "coh": "coherence",
        "psy": "psycho",
        "tech": "tech",
        "ut": "utility_elements",
    }.get(prefix, prefix)


def main():
    sources = [
        ("bloc_1_hero_v3.json", "bloc_1_hero_v3-3.json"),
        ("bloc_2_persuasion_v3.json", "bloc_2_persuasion_v3-3.json"),
        ("bloc_3_ux_v3.json", "bloc_3_ux_v3-3.json"),
        ("bloc_4_coherence_v3.json", "bloc_4_coherence_v3-3.json"),
        ("bloc_5_psycho_v3.json", "bloc_5_psycho_v3-3.json"),
        ("bloc_6_tech_v3.json", "bloc_6_tech_v3-3.json"),
        ("bloc_utility_elements_v3.json", "bloc_utility_elements_v3-3.json"),
    ]
    written = 0
    for src_name, dst_name in sources:
        src = PLAYBOOK / src_name
        if not src.exists():
            print(f"  [skip] {src_name} missing")
            continue
        dst = PLAYBOOK / dst_name
        bloc_v3 = json.loads(src.read_text())
        bloc_v3_3 = enrich_bloc(bloc_v3)
        dst.write_text(json.dumps(bloc_v3_3, ensure_ascii=False, indent=2))
        print(f"  [ok] {dst_name}  ({len(bloc_v3_3.get('criteria', []))} criteria)")
        written += 1
    print(f"\nwrote {written} bloc V3.3 files in {PLAYBOOK}")


if __name__ == "__main__":
    main()
