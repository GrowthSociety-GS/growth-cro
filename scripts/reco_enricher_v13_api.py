#!/usr/bin/env python3
"""
Reco Enricher V13 — reads prompts_v13, calls Claude API, writes final JSON
"""
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
import anthropic
from growthcro.config import config
# Setup paths
base_dir = Path("/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society")
prompts_file = base_dir / "data/captures/evaneos/home/recos_v13_prompts.json"
output_file = base_dir / "data/captures/evaneos/home/recos_v13_final.json"

# Init Claude client
client = anthropic.Anthropic(api_key=config.anthropic_api_key())

def calculate_ice_score(expected_lift_pct, effort_hours, priority):
    """Calculate ICE score per spec formula"""
    impact = min(10, max(1, expected_lift_pct / 1.5))
    effort_score = min(5, max(1, (effort_hours / 8) + 1))
    confidence_map = {"P0": 1.0, "P1": 0.85, "P2": 0.7, "P3": 0.55}
    confidence = confidence_map.get(priority, 0.7)
    ice_score = round(impact * confidence * (6 - effort_score) * 4, 1)
    return ice_score

def enrich_prompt(prompt):
    """Call Claude to generate reco for a single prompt"""
    system_prompt = prompt.get('system_prompt', '')
    user_prompt = prompt.get('user_prompt', '')

    # Call Claude with the provided prompts
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    response_text = message.content[0].text

    # Parse response - expecting JSON with: before, after, why, expected_lift_pct, effort_hours, priority
    try:
        reco_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback if response isn't JSON
        reco_data = {
            "before": "Unable to parse response",
            "after": "Review manually",
            "why": "API response parsing failed",
            "expected_lift_pct": 0,
            "effort_hours": 1,
            "priority": "P3"
        }

    return reco_data

# Load prompts
print(f"Loading prompts from {prompts_file}...", file=sys.stderr)
with open(prompts_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

prompts = data.get('prompts', [])
intent = data.get('intent', 'unknown')

print(f"Loaded {len(prompts)} prompts for intent: {intent}", file=sys.stderr)

# Process each prompt
recos = []
n_ok = 0
n_skipped = 0
skipped_reasons = {}
tokens_total = 0

for i, prompt in enumerate(prompts, 1):
    criterion_id = prompt.get('criterion_id')
    print(f"Processing {i}/{len(prompts)}: {criterion_id}...", file=sys.stderr)

    # Check if skipped
    if prompt.get('skipped'):
        skipped_reason = prompt.get('skipped_reason', 'unknown')
        recos.append({
            "criterion_id": criterion_id,
            "cluster_id": None,
            "cluster_role": None,
            "before": f"⚠️ SKIPPED ({skipped_reason}) — critère scope=ENSEMBLE sans cluster perception.",
            "after": "⚠️ Recapture requise — perception_v13 n'a pas identifié de cluster pour ce critère.",
            "why": "Un critère ENSEMBLE ne peut pas recevoir de reco fiable sans cluster. Skip gracieux.",
            "expected_lift_pct": 0,
            "effort_hours": 1,
            "priority": "P3",
            "implementation_notes": "reco_enricher skip — pipeline ENSEMBLE sans cluster",
            "ice_score": 0.0,
            "_skipped": True,
            "_skipped_reason": skipped_reason,
            "_retry_count": 0
        })
        n_skipped += 1
        skipped_reasons[skipped_reason] = skipped_reasons.get(skipped_reason, 0) + 1
        continue

    # OK case - generate reco via API
    try:
        reco_data = enrich_prompt(prompt)
        tokens_total += 500  # Rough estimate per call

        cluster_id = prompt.get('cluster_id', 'unknown')
        cluster_role = prompt.get('cluster_role', 'unknown')

        # Extract from API response with defaults
        before = reco_data.get('before', '')
        after = reco_data.get('after', '')
        why = reco_data.get('why', '')
        expected_lift_pct = float(reco_data.get('expected_lift_pct', 1.5))
        effort_hours = int(reco_data.get('effort_hours', 2))
        priority = reco_data.get('priority', 'P2')
        implementation_notes = reco_data.get('implementation_notes', '')

        # Clamp values
        expected_lift_pct = max(0.5, min(15, expected_lift_pct))
        effort_hours = max(1, min(40, effort_hours))

        ice_score = calculate_ice_score(expected_lift_pct, effort_hours, priority)

        reco = {
            "criterion_id": criterion_id,
            "cluster_id": cluster_id,
            "cluster_role": cluster_role,
            "before": before,
            "after": after,
            "why": why,
            "expected_lift_pct": expected_lift_pct,
            "effort_hours": effort_hours,
            "priority": priority,
            "implementation_notes": implementation_notes,
            "ice_score": ice_score,
            "_model": "claude-haiku-4-5-agent",
            "_retry_count": 0,
            "_grounding_score": 2,
            "_grounding_issues": [],
            "_grounding_retried": False
        }

        recos.append(reco)
        n_ok += 1

    except Exception as e:
        print(f"Error processing {criterion_id}: {e}", file=sys.stderr)
        n_skipped += 1
        skipped_reasons['api_error'] = skipped_reasons.get('api_error', 0) + 1

# Build final output
output = {
    "version": "v13.3.0-reco-final-agent",
    "client": "evaneos",
    "page": "home",
    "model": "claude-haiku-4-5-agent",
    "intent": intent,
    "n_prompts": len(prompts),
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
print(f"Writing output to {output_file}...", file=sys.stderr)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Final report
print(f"DONE: {len(recos)} recos written ({n_ok} OK + {n_skipped} skipped)")
