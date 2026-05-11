#!/usr/bin/env bash
# run_full_pipeline.sh — enchaîne phases 3 → 7 en séquence
# Usage: bash run_full_pipeline.sh 2>&1 | tee data/captures/_logs/full_pipeline_$(date +%Y%m%dT%H%M).log
set -euo pipefail

ROOT="/sessions/relaxed-busy-goldberg/mnt/Mathis - Stratégie CRO Interne - Growth Society"
cd "$ROOT"
S="skills/site-capture/scripts"

banner() {
  echo ""
  echo "════════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════════════════════════"
}

banner "PHASE 2b — Semantic mapper (batch, pour semantic_map + criterion_crops)"
python3 "$S/semantic_mapper.py" --batch || true

banner "PHASE 3-4 — Perception pipeline (cleaner + detector + overlay + critic)"
python3 "$S/perception_pipeline.py" --all || true

banner "PHASE 5 — batch_rescore (6 pillars + specific + page_type)"
python3 "$S/batch_rescore.py"

banner "PHASE 6 — batch_enrich (reco_engine + reco_enricher)"
python3 "$S/batch_enrich.py"

banner "PHASE 6b — criterion_crops (batch) — pour highlights screenshot par critère"
python3 "$S/criterion_crops.py" --batch

banner "PHASE 7 — generate_audit_data_v12"
python3 generate_audit_data_v12.py

banner "✅ PIPELINE DONE"
date
ls -la prototype/growthcro_audit_data_v12.js
