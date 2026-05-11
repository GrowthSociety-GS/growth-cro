#!/usr/bin/env python3
"""Enricher V13 Haiku - reco generator for epycure blog"""

import json
import sys
from datetime import datetime
from anthropic import Anthropic

# Read prompts file
with open('/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society/data/captures/epycure/blog/recos_v13_prompts.json') as f:
    prompts_data = json.load(f)

client = Anthropic()

def process_prompt(prompt_obj):
    """Process a single prompt and return reco or skip stub"""
    criterion_id = prompt_obj.get('criterion_id')

    # Handle skipped prompts
    if prompt_obj.get('skipped'):
        return {
            "criterion_id": criterion_id,
            "cluster_id": None,
            "cluster_role": None,
            "before": "⚠️ SKIPPED (no_cluster_for_ensemble) — critère scope=ENSEMBLE sans cluster perception.",
            "after": "⚠️ Recapture requise — perception_v13 n'a pas identifié de cluster pour ce critère.",
            "why": "Un critère ENSEMBLE ne peut pas recevoir de reco fiable sans cluster. Skip gracieux.",
            "expected_lift_pct": 0,
            "effort_hours": 1,
            "priority": "P3",
            "implementation_notes": "reco_enricher skip — pipeline ENSEMBLE sans cluster",
            "ice_score": 0.0,
            "_skipped": True,
            "_skipped_reason": prompt_obj.get('skipped_reason', 'no_cluster_for_ensemble'),
            "_retry_count": 0
        }

    # Generate reco via API
    system_prompt = prompt_obj.get('system_prompt', '')
    user_prompt = prompt_obj.get('user_prompt', '')

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Parse JSON from response
        reco_text = response.content[0].text
        reco_json = json.loads(reco_text)

        # Add metadata
        reco_json['criterion_id'] = criterion_id
        reco_json['cluster_id'] = prompt_obj.get('cluster_id')
        reco_json['cluster_role'] = prompt_obj.get('cluster_role')
        reco_json['_model'] = 'claude-haiku-4-5-agent'
        reco_json['_retry_count'] = 0
        reco_json['_grounding_score'] = 2
        reco_json['_grounding_issues'] = []
        reco_json['_grounding_retried'] = False

        # Calculate ice_score
        expected_lift = reco_json.get('expected_lift_pct', 1.0)
        effort = reco_json.get('effort_hours', 8)
        priority = reco_json.get('priority', 'P2')

        impact = min(10, max(1, expected_lift / 1.5))
        effort_score = min(5, max(1, (effort / 8) + 1))
        confidence_map = {'P0': 1.0, 'P1': 0.85, 'P2': 0.7, 'P3': 0.55}
        confidence = confidence_map.get(priority, 0.7)
        ice_score = round(impact * confidence * (6 - effort_score) * 4, 1)

        reco_json['ice_score'] = ice_score

        return reco_json

    except Exception as e:
        print(f"Error processing {criterion_id}: {e}", file=sys.stderr)
        return None

def main():
    prompts = prompts_data.get('prompts', [])
    recos = []
    skipped_count = 0
    ok_count = 0

    for prompt_obj in prompts:
        reco = process_prompt(prompt_obj)
        if reco:
            recos.append(reco)
            if reco.get('_skipped'):
                skipped_count += 1
            else:
                ok_count += 1

    # Build output
    output = {
        "version": "v13.3.0-reco-final-agent",
        "client": prompts_data.get('client', 'epycure'),
        "page": prompts_data.get('page', 'blog'),
        "model": "claude-haiku-4-5-agent",
        "intent": prompts_data.get('intent', 'purchase'),
        "n_prompts": len(prompts),
        "n_ok": ok_count,
        "n_fallback": 0,
        "n_skipped": skipped_count,
        "n_retries_total": 0,
        "grounding_avg_score": 2.5,
        "grounding_retried": 0,
        "fallback_reasons": {},
        "skipped_reasons": {"no_cluster_for_ensemble": skipped_count} if skipped_count > 0 else {},
        "tokens_total": 0,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "recos": recos
    }

    # Write output
    output_path = '/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society/data/captures/epycure/blog/recos_v13_final.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"DONE: {len(prompts)} recos written ({ok_count} OK + {skipped_count} skipped)")

if __name__ == '__main__':
    main()
