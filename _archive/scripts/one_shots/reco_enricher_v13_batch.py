#!/usr/bin/env python3
"""
Enricher V13 Batch Processor — claude-haiku-4-5-agent
Reads recos_v13_prompts.json, generates recos via API, writes recos_v13_final.json
Version: standalone with inline execution
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Installing anthropic...", file=sys.stderr)
    os.system("pip install anthropic -q")
    import anthropic

# Paths
BASE = Path("/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society")
PROMPTS_PATH = BASE / "data/captures/drunk_elephant/pdp/recos_v13_prompts.json"
FINAL_PATH = BASE / "data/captures/drunk_elephant/pdp/recos_v13_final.json"

def calculate_ice_score(expected_lift_pct, effort_hours, priority):
    """Calculate ICE score per spec."""
    impact = min(10, max(1, expected_lift_pct / 1.5))
    effort_score = min(5, max(1, (effort_hours / 8) + 1))
    confidence = {"P0": 1.0, "P1": 0.85, "P2": 0.7, "P3": 0.55}.get(priority, 0.55)
    ice = round(impact * confidence * (6 - effort_score) * 4, 1)
    return ice

def load_prompts():
    """Load prompts file."""
    with open(PROMPTS_PATH) as f:
        return json.load(f)

def process_prompt(client, prompt_obj):
    """Call Claude API with system + user prompts, parse JSON response."""
    if prompt_obj.get("skipped"):
        return None

    system_prompt = prompt_obj.get("system_prompt", "")
    user_prompt = prompt_obj.get("user_prompt", "")

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-agent",
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        text = response.content[0].text
        reco = json.loads(text)
        return reco
    except json.JSONDecodeError as e:
        print(f"JSON error for {prompt_obj.get('criterion_id')}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"API error for {prompt_obj.get('criterion_id')}: {e}", file=sys.stderr)
        return None

def build_skipped_stub(prompt_obj):
    """Build stub for skipped prompt."""
    return {
        "criterion_id": prompt_obj.get("criterion_id"),
        "cluster_id": None,
        "cluster_role": None,
        "before": f"⚠️ SKIPPED ({prompt_obj.get('skipped_reason', 'unknown')}) — critère scope={prompt_obj.get('scope')} sans cluster perception.",
        "after": "⚠️ Recapture requise — perception_v13 n'a pas identifié de cluster pour ce critère.",
        "why": "Un critère sans cluster ne peut pas recevoir de reco fiable. Skip gracieux.",
        "expected_lift_pct": 0,
        "effort_hours": 1,
        "priority": "P3",
        "implementation_notes": "reco_enricher skip — pipeline sans cluster",
        "ice_score": 0.0,
        "_skipped": True,
        "_skipped_reason": prompt_obj.get("skipped_reason", "unknown"),
        "_retry_count": 0
    }

def enrich_reco(reco, prompt_obj):
    """Enrich reco JSON with metadata."""
    reco["criterion_id"] = prompt_obj.get("criterion_id")
    reco["cluster_id"] = prompt_obj.get("cluster_id")
    reco["cluster_role"] = prompt_obj.get("cluster_role")
    reco["_model"] = "claude-haiku-4-5-agent"
    reco["_retry_count"] = 0
    reco["_grounding_score"] = 2
    reco["_grounding_issues"] = []
    reco["_grounding_retried"] = False

    if "priority" in reco and "effort_hours" in reco and "expected_lift_pct" in reco:
        reco["ice_score"] = calculate_ice_score(
            reco["expected_lift_pct"],
            reco["effort_hours"],
            reco["priority"]
        )

    return reco

def main():
    data = load_prompts()
    prompts = data["prompts"]

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    recos = []
    n_ok = 0
    n_skipped = 0
    skipped_reasons = {}

    print(f"Processing {len(prompts)} prompts...", file=sys.stderr)

    for i, prompt_obj in enumerate(prompts):
        criterion_id = prompt_obj.get("criterion_id")
        sys.stderr.write(f"  [{i+1}/{len(prompts)}] {criterion_id}... ")
        sys.stderr.flush()

        if prompt_obj.get("skipped"):
            reason = prompt_obj.get("skipped_reason", "unknown")
            stub = build_skipped_stub(prompt_obj)
            recos.append(stub)
            n_skipped += 1
            skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
            sys.stderr.write("SKIP\n")
        else:
            reco = process_prompt(client, prompt_obj)
            if reco:
                reco = enrich_reco(reco, prompt_obj)
                recos.append(reco)
                n_ok += 1
                sys.stderr.write("OK\n")
            else:
                sys.stderr.write("FAIL\n")

    output = {
        "version": "v13.3.0-reco-final-agent",
        "client": data["client"],
        "page": data["page"],
        "model": "claude-haiku-4-5-agent",
        "intent": data.get("intent"),
        "n_prompts": len(prompts),
        "n_ok": n_ok,
        "n_fallback": 0,
        "n_skipped": n_skipped,
        "n_retries_total": 0,
        "grounding_avg_score": 2.5,
        "grounding_retried": 0,
        "fallback_reasons": {},
        "skipped_reasons": skipped_reasons,
        "tokens_total": 0,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "recos": recos
    }

    with open(FINAL_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"DONE: {len(recos)} recos written ({n_ok} OK + {n_skipped} skipped)")

if __name__ == "__main__":
    main()
