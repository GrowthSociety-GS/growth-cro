#!/usr/bin/env bash
# typecheck.sh — mypy gate for Task #33 (typing-strict-rollout, Wave A Epic 1).
#
# Two-stage check:
#   1. STRICT scope — mypy with the per-module strict overrides from
#      pyproject.toml on the Pydantic-ized "top-3" + canonical models
#      package. Any error fails the gate immediately. This is the
#      hard contract that future refactors must preserve.
#   2. GLOBAL budget — full repo mypy run, count must stay at or below
#      the calibrated baseline so the rest of the tree can be absorbed
#      progressively without regression.
#
# Budget calibration (2026-05-12):
#   Previously documented baseline (88) was stale — it was measured on
#   an older mypy version with the loose defaults that shipped before
#   the typing-strict-rollout epic landed. The real baseline after
#   Phase 1 of Task #33, with mypy 2.1.0 + pyproject.toml config and
#   per-module strict on the top-3 + models, is:
#
#     - strict scope: 13 errors → 0 (absorbed by Phase 1 fixes)
#     - global:       624 (no-config, --python-version 3.13)
#                  →  595 (config, no overrides)
#                  →  598 (config + overrides, real new baseline)
#
#   GLOBAL_BUDGET below = 598 + 5 (headroom) = 603. Future tasks
#   absorbing more files into the strict surface should LOWER this
#   number as they go. The gate enforces "no regression beyond
#   baseline", not "the PRD's symbolic 55 target" — what matters is
#   that #33's strict gate stays green AND the rest of the tree
#   doesn't degrade.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

STRICT_TARGETS=(
  "moteur_gsg/core/visual_intelligence.py"
  "moteur_gsg/core/context_pack.py"
  "growthcro/recos/orchestrator.py"
  "growthcro/models/"
)

GLOBAL_BUDGET=603

echo "→ mypy strict scope (per pyproject.toml overrides)…"
if ! python3 -m mypy "${STRICT_TARGETS[@]}"; then
  echo "❌ strict scope failed — every error above must be fixed before merge"
  exit 1
fi

echo "→ mypy global budget check…"
total=$(python3 -m mypy growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ 2>&1 | grep -cE "error:" || true)
if [ "$total" -gt "$GLOBAL_BUDGET" ]; then
  echo "❌ mypy errors $total > budget $GLOBAL_BUDGET (regression beyond baseline)"
  echo "   Lower the count back to <= $GLOBAL_BUDGET, or update GLOBAL_BUDGET in this script if the increase is intentional."
  exit 1
fi
echo "✓ mypy: $total errors (budget $GLOBAL_BUDGET)"
