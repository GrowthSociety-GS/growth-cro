#!/usr/bin/env bash
# scripts/test_gsg_regression.sh — Issue #19 GSG Stratosphere regression gate.
#
# Verifies that the V27.2-G+ pipeline (animations + impeccable_qa
# integrated) does not regress the multi-judge score on:
#   * Weglot V27.2-D listicle baseline (deliverables/
#     weglot-lp_listicle-GSG-V27-2C-TRUE.html) — 70.9% pre-#19
#   * 3 new stratosphere LPs (japhy-pdp, stripe-pricing, linear-leadgen)
#     when their HTML is present in deliverables/gsg_stratosphere/
#
# Behavior
# --------
# 1. Always re-scores Weglot baseline → emits weglot_now_score.
# 2. For each new LP that exists on disk, scores it and compares
#    against weglot_now_score with a regression budget of 5pt (per
#    task #19 AC).
# 3. Exits 0 if all PRESENT LPs pass; 1 if any regresses > 5pt OR if
#    Weglot baseline itself regresses > 5pt vs the 70.9% benchmark.
# 4. Missing new LPs (e.g. no live API key yet) are reported as
#    skipped, not failures — see task #19 spec ("scaffold + document
#    live-run requirement"). The script remains green on structural
#    landing day; the human runner triggers it again after the live
#    generation pass.
#
# Usage
# -----
#     bash scripts/test_gsg_regression.sh
#     bash scripts/test_gsg_regression.sh --strict   # fail on missing
#
# Outputs (idempotent)
# --------------------
#   data/_pipeline_runs/_regression_19/weglot_now.json
#   data/_pipeline_runs/_regression_19/<client>_<page>_now.json
#   data/_pipeline_runs/_regression_19/_summary.json
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="data/_pipeline_runs/_regression_19"
mkdir -p "$OUT_DIR"

STRICT=0
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

BASELINE_SCORE="70.9"
REGRESSION_BUDGET="5.0"

echo "──────────────────────────────────────────────────────────"
echo "GSG Regression Gate — Issue #19 (V27.2-G+)"
echo "Baseline: Weglot V27.2-D listicle → ${BASELINE_SCORE}%"
echo "Budget:   ${REGRESSION_BUDGET}pt"
echo "──────────────────────────────────────────────────────────"

# Helper — score one HTML through the multi-judge orchestrator.
score_html() {
  local html_path="$1"
  local out_path="$2"
  local client="$3"
  local page_type="$4"

  if [[ ! -f "$html_path" ]]; then
    echo "SKIP  $client/$page_type — $html_path not on disk"
    return 2
  fi

  python3 -m moteur_multi_judge.orchestrator \
    --html "$html_path" \
    --client "$client" \
    --page-type "$page_type" \
    --output "$out_path" \
    >/dev/null 2>&1 || {
      echo "ERROR  $client/$page_type — multi_judge failed"
      return 3
    }
  return 0
}

# Helper — read final_score_pct from a multi_judge.json
score_of() {
  python3 - "$1" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.exists():
    print("0.0"); sys.exit(0)
data = json.loads(p.read_text())
print(data.get("final", {}).get("final_score_pct", 0.0))
PY
}

# Helper — bash-friendly float comparison via python3
delta_exceeds() {
  python3 - "$1" "$2" "$3" <<'PY'
import sys
old = float(sys.argv[1])
new = float(sys.argv[2])
budget = float(sys.argv[3])
# Regression iff new < old - budget
print("YES" if (old - new) > budget else "NO")
PY
}

FAIL=0
PASSED=0
SKIPPED=0
SUMMARY_JSON='{"baseline_pct":'"$BASELINE_SCORE"',"budget_pt":'"$REGRESSION_BUDGET"',"runs":['

# Re-score Weglot baseline
WEGLOT_HTML="deliverables/weglot-lp_listicle-GSG-V27-2C-TRUE.html"
WEGLOT_OUT="$OUT_DIR/weglot_now.json"
echo "→ Re-scoring Weglot V27.2-D baseline..."
if score_html "$WEGLOT_HTML" "$WEGLOT_OUT" "weglot" "lp_listicle"; then
  WEGLOT_NOW=$(score_of "$WEGLOT_OUT")
  echo "  weglot/lp_listicle  → ${WEGLOT_NOW}% (baseline ${BASELINE_SCORE}%)"
  reg=$(delta_exceeds "$BASELINE_SCORE" "$WEGLOT_NOW" "$REGRESSION_BUDGET")
  if [[ "$reg" == "YES" ]]; then
    echo "  ⛔ Weglot regressed > ${REGRESSION_BUDGET}pt"
    FAIL=$((FAIL+1))
  else
    echo "  ✓ Weglot stable within budget"
    PASSED=$((PASSED+1))
  fi
  SUMMARY_JSON+='{"client":"weglot","page_type":"lp_listicle","now":'"$WEGLOT_NOW"',"baseline":'"$BASELINE_SCORE"',"status":"'$([ "$reg" == "YES" ] && echo "regressed" || echo "stable")'"},'
else
  echo "  ⚠️  Weglot baseline rescored — skipped (file missing)"
  SKIPPED=$((SKIPPED+1))
  WEGLOT_NOW="$BASELINE_SCORE"
fi

# Score each new stratosphere LP if present
declare -a NEW_LPS=(
  "japhy:pdp:deliverables/gsg_stratosphere/japhy-pdp-v27_2_g.html"
  "stripe:pricing:deliverables/gsg_stratosphere/stripe-pricing-v27_2_g.html"
  "linear:lp_leadgen:deliverables/gsg_stratosphere/linear-leadgen-v27_2_g.html"
)

for entry in "${NEW_LPS[@]}"; do
  IFS=":" read -r client page_type html_path <<< "$entry"
  out_path="$OUT_DIR/${client}_${page_type}_now.json"
  echo "→ Scoring ${client}/${page_type}..."
  if score_html "$html_path" "$out_path" "$client" "$page_type"; then
    new_score=$(score_of "$out_path")
    echo "  ${client}/${page_type}  → ${new_score}%"
    reg=$(delta_exceeds "$WEGLOT_NOW" "$new_score" "$REGRESSION_BUDGET")
    if [[ "$reg" == "YES" ]]; then
      echo "  ⛔ ${client}/${page_type} regressed > ${REGRESSION_BUDGET}pt vs Weglot now"
      FAIL=$((FAIL+1))
    else
      echo "  ✓ ${client}/${page_type} within budget"
      PASSED=$((PASSED+1))
    fi
    SUMMARY_JSON+='{"client":"'"$client"'","page_type":"'"$page_type"'","now":'"$new_score"',"baseline":'"$WEGLOT_NOW"',"status":"'$([ "$reg" == "YES" ] && echo "regressed" || echo "stable")'"},'
  else
    code=$?
    if [[ "$code" == "2" ]]; then
      SKIPPED=$((SKIPPED+1))
      SUMMARY_JSON+='{"client":"'"$client"'","page_type":"'"$page_type"'","now":null,"baseline":'"$WEGLOT_NOW"',"status":"missing"},'
      if [[ "$STRICT" == "1" ]]; then
        echo "  ⛔ --strict mode: missing LP is a failure"
        FAIL=$((FAIL+1))
      fi
    else
      FAIL=$((FAIL+1))
    fi
  fi
done

# Trim trailing comma
SUMMARY_JSON="${SUMMARY_JSON%,}"
SUMMARY_JSON+="],\"fail_count\":$FAIL,\"pass_count\":$PASSED,\"skipped_count\":$SKIPPED}"

echo "$SUMMARY_JSON" | python3 -c "import json,sys; print(json.dumps(json.loads(sys.stdin.read()), indent=2))" > "$OUT_DIR/_summary.json"

echo "──────────────────────────────────────────────────────────"
echo "Summary: $PASSED passed, $FAIL failed, $SKIPPED skipped"
echo "Detail : $OUT_DIR/_summary.json"
echo "──────────────────────────────────────────────────────────"

if [[ "$FAIL" -gt 0 ]]; then
  echo "GSG_REGRESSION_GATE=FAIL"
  exit 1
fi
echo "GSG_REGRESSION_GATE=PASS"
exit 0
