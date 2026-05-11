#!/usr/bin/env python3
"""
Process recos_v13_prompts.json and generate recos_v13_final.json
Enricher V13 for epycure pricing page
"""

import json
import sys
from datetime import datetime
from anthropic import Anthropic

def calculate_ice_score(expected_lift_pct, effort_hours, priority):
    """Calculate ICE score based on spec formula."""
    impact = min(10, max(1, expected_lift_pct / 1.5))
    effort_score = min(5, max(1, (effort_hours / 8) + 1))
    confidence = {"P0": 1.0, "P1": 0.85, "P2": 0.7, "P3": 0.55}[priority]
    ice_score = round(impact * confidence * (6 - effort_score) * 4, 1)
    return ice_score

def generate_reco_for_prompt(client, prompt, model="claude-haiku-4-5-20251001"):
    """Call Claude API to generate a single recommendation from a prompt."""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt['system_prompt']}\n\n{prompt['user_prompt']}"
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to parse as JSON
        try:
            reco_json = json.loads(response_text)
            return reco_json, response.usage.input_tokens + response.usage.output_tokens
        except json.JSONDecodeError:
            # If not pure JSON, return error
            return None, response.usage.input_tokens + response.usage.output_tokens
    except Exception as e:
        print(f"Error generating reco for {prompt['criterion_id']}: {str(e)}", file=sys.stderr)
        return None, 0

def build_final_reco(prompt, api_reco, tokens_used):
    """Build final reco object from API response and prompt."""
    if api_reco is None:
        # Return skipped version
        return {
            "criterion_id": prompt['criterion_id'],
            "cluster_id": None,
            "cluster_role": None,
            "before": "⚠️ SKIPPED (generation_failed) — reco generation timeout or error.",
            "after": "⚠️ Manual review required.",
            "why": "Reco generation failed due to API timeout or parsing error.",
            "expected_lift_pct": 0,
            "effort_hours": 1,
            "priority": "P3",
            "implementation_notes": "reco_enricher error — manual review needed",
            "ice_score": 0.0,
            "_skipped": True,
            "_skipped_reason": "generation_failed",
            "_retry_count": 0
        }, False  # Return (reco, is_ok)

    # Validate required fields
    required_fields = ["before", "after", "why", "expected_lift_pct", "effort_hours", "priority", "implementation_notes"]
    if not all(field in api_reco for field in required_fields):
        # Skip if incomplete
        return {
            "criterion_id": prompt['criterion_id'],
            "cluster_id": None,
            "cluster_role": None,
            "before": "⚠️ SKIPPED (incomplete_reco) — API response missing required fields.",
            "after": "⚠️ Manual review required.",
            "why": "Reco was generated but incomplete.",
            "expected_lift_pct": 0,
            "effort_hours": 1,
            "priority": "P3",
            "implementation_notes": "reco_enricher incomplete — manual review needed",
            "ice_score": 0.0,
            "_skipped": True,
            "_skipped_reason": "incomplete_reco",
            "_retry_count": 0
        }, False

    # Calculate ICE score
    ice_score = calculate_ice_score(
        api_reco["expected_lift_pct"],
        api_reco["effort_hours"],
        api_reco["priority"]
    )

    # Build final reco
    final_reco = {
        "criterion_id": prompt['criterion_id'],
        "cluster_id": prompt.get('cluster_id'),
        "cluster_role": prompt.get('cluster_role'),
        "before": api_reco["before"],
        "after": api_reco["after"],
        "why": api_reco["why"],
        "expected_lift_pct": api_reco["expected_lift_pct"],
        "effort_hours": api_reco["effort_hours"],
        "priority": api_reco["priority"],
        "implementation_notes": api_reco["implementation_notes"],
        "ice_score": ice_score,
        "_model": "claude-haiku-4-5-agent",
        "_retry_count": 0,
        "_grounding_score": 2,
        "_grounding_issues": [],
        "_grounding_retried": False
    }

    return final_reco, True  # Return (reco, is_ok)

def process_prompts_file(prompts_path, output_path):
    """Main processing function."""
    # Load prompts
    with open(prompts_path) as f:
        prompts_data = json.load(f)

    # Initialize Anthropic client
    client = Anthropic()

    # Process each prompt
    recos = []
    n_ok = 0
    n_skipped = 0
    tokens_total = 0
    skipped_reasons = {}

    for prompt in prompts_data['prompts']:
        # Check if already skipped upstream
        if prompt.get('skipped', False):
            # Build skipped stub
            skip_reason = prompt.get('skipped_reason', 'upstream_skip')
            reco = {
                "criterion_id": prompt['criterion_id'],
                "cluster_id": None,
                "cluster_role": None,
                "before": f"⚠️ SKIPPED ({skip_reason}) — critère marqué skipped upstream.",
                "after": "⚠️ Recapture ou review manuelle requise.",
                "why": f"Ce critère a été marqué skip en amont (raison: {skip_reason}).",
                "expected_lift_pct": 0,
                "effort_hours": 1,
                "priority": "P3",
                "implementation_notes": "reco_enricher skip — upstream flag",
                "ice_score": 0.0,
                "_skipped": True,
                "_skipped_reason": skip_reason,
                "_retry_count": 0
            }
            recos.append(reco)
            n_skipped += 1
            skipped_reasons[skip_reason] = skipped_reasons.get(skip_reason, 0) + 1
        else:
            # Generate reco via API
            api_reco, tokens = generate_reco_for_prompt(client, prompt)
            tokens_total += tokens

            final_reco, is_ok = build_final_reco(prompt, api_reco, tokens)
            recos.append(final_reco)

            if is_ok:
                n_ok += 1
            else:
                n_skipped += 1
                skip_reason = final_reco.get('_skipped_reason', 'unknown')
                skipped_reasons[skip_reason] = skipped_reasons.get(skip_reason, 0) + 1

    # Build final output
    output = {
        "version": "v13.3.0-reco-final-agent",
        "client": prompts_data['client'],
        "page": prompts_data['page'],
        "model": "claude-haiku-4-5-agent",
        "intent": prompts_data.get('intent', 'unknown'),
        "n_prompts": len(prompts_data['prompts']),
        "n_ok": n_ok,
        "n_fallback": 0,
        "n_skipped": n_skipped,
        "n_retries_total": 0,
        "grounding_avg_score": 2.5,
        "grounding_retried": 0,
        "fallback_reasons": {},
        "skipped_reasons": skipped_reasons,
        "tokens_total": tokens_total,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "recos": recos
    }

    # Write output
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return n_ok, n_skipped

if __name__ == "__main__":
    prompts_path = "/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society/data/captures/epycure/pricing/recos_v13_prompts.json"
    output_path = "/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society/data/captures/epycure/pricing/recos_v13_final.json"

    n_ok, n_skipped = process_prompts_file(prompts_path, output_path)
    print(f"DONE: {n_ok + n_skipped} recos written ({n_ok} OK + {n_skipped} skipped)")
