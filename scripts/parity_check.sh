#!/usr/bin/env bash
# scripts/parity_check.sh — pipeline parity baseline + check
#
# Usage:
#   bash scripts/parity_check.sh <client_id> --baseline   # write baseline
#   bash scripts/parity_check.sh <client_id> --compare    # compare to latest
#   bash scripts/parity_check.sh <client_id>              # alias for --compare
#
# Walks data/captures/<client>/ for canonical pipeline JSON outputs
# (capture / perception / pillars / page-type / recos), strips volatile
# fields, sorts keys (jq -S), and hashes each file. Baseline lives at
# _archive/parity_baselines/<client>/<ISO-date>/ with a `latest` symlink.
#
# A re-run with --compare against an unchanged tree exits 0 (no drift).
# Any byte-level delta in semantically meaningful fields exits 1.
#
# Exit codes:
#   0  parity OK (or baseline written)
#   1  parity DRIFT
#   2  bad invocation
#   3  no baseline to compare against

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: parity_check.sh <client_id> [--baseline|--compare]" >&2
  exit 2
fi

CLIENT="$1"
MODE="${2:---compare}"

case "$MODE" in
  --baseline|--compare) ;;
  *) echo "unknown mode: $MODE (use --baseline or --compare)" >&2; exit 2 ;;
esac

command -v jq      >/dev/null 2>&1 || { echo "jq required"      >&2; exit 2; }
command -v shasum  >/dev/null 2>&1 || { echo "shasum required"  >&2; exit 2; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAPTURES="$ROOT/data/captures/$CLIENT"
BASELINE_ROOT="$ROOT/_archive/parity_baselines/$CLIENT"

# Canonical pipeline stage filenames (per state.py PIPELINE_STAGES + sibling outputs).
STAGES=(
  "capture.json"
  "spatial_v9.json"
  "perception_v13.json"
  "client_intent.json"
  "score_hero.json"
  "score_psycho.json"
  "score_persuasion.json"
  "score_coherence.json"
  "score_utility_banner.json"
  "score_specific_criteria.json"
  "score_page_type.json"
  "recos_v13_prompts.json"
  "recos_v13_final.json"
  "recos_enriched.json"
)

# Volatile-field scrubber. Removes any object key matching the regex anywhere
# in the JSON tree. Score values, reco IDs, payload structure are preserved.
MASK_FILTER='
def scrub:
  if type == "object" then
    with_entries(
      select(.key | test("^(timestamp|timestamps|generated_at|generatedAt|created_at|createdAt|updated_at|updatedAt|mtime|run_id|runId|uuid|id_run|cache_key|fingerprint|elapsed_ms|elapsed|duration_ms|started_at|finished_at|completed_at)$") | not)
    )
    | with_entries(.value |= scrub)
  elif type == "array" then
    map(scrub)
  else
    .
  end;
scrub
'

ts="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

manifest="$work_dir/MANIFEST.txt"
: > "$manifest"

# Discover stage files for this client.
found_count=0
if [[ -d "$CAPTURES" ]]; then
  while IFS= read -r f; do
    base="$(basename "$f")"
    for stage in "${STAGES[@]}"; do
      if [[ "$base" == "$stage" ]]; then
        rel="${f#$ROOT/}"
        out="$work_dir/$rel"
        mkdir -p "$(dirname "$out")"
        if jq -S "$MASK_FILTER" "$f" > "$out" 2>/dev/null; then
          sha="$(shasum -a 256 "$out" | awk '{print $1}')"
          printf "%s  %s\n" "$sha" "$rel" >> "$manifest"
          found_count=$((found_count + 1))
        else
          echo "[WARN] jq failed on $f" >&2
        fi
        break
      fi
    done
  done < <(find "$CAPTURES" -type f -name "*.json" 2>/dev/null | sort)
fi

# Stable manifest order (sha + relpath; relpath is unique per stage file).
sort "$manifest" -o "$manifest"

if [[ "$MODE" == "--baseline" ]]; then
  out_dir="$BASELINE_ROOT/$ts"
  mkdir -p "$out_dir"
  if [[ "$found_count" -gt 0 ]]; then
    (cd "$work_dir" && tar cf - data) | (cd "$out_dir" && tar xf -)
  fi
  cp "$manifest" "$out_dir/MANIFEST.txt"

  # Per-stage tally for the README.
  tally=""
  for s in "${STAGES[@]}"; do
    n=$(grep -cE "/${s}\$" "$manifest" || true)
    tally+="$(printf '%s\n' "- \`${s}\`: ${n}")"$'\n'
  done

  cat > "$out_dir/README.md" <<EOF
# Parity baseline — \`${CLIENT}\` — ${ts}

- Files snapshotted: ${found_count}
- Mask: keys matching \`timestamp|generated_at|mtime|run_id|uuid|...\` scrubbed at every depth.
- Encoding: \`jq -S\` (sorted keys), UTF-8.
- Compare command: \`bash scripts/parity_check.sh ${CLIENT} --compare\`

## Stage coverage
${tally}

## Notes
If \`Files snapshotted\` is 0, the client has no \`data/captures/${CLIENT}/\` outputs
on disk at the time of baseline. The parity contract still applies: any future
run that produces stage files for this client must reproduce identical scrubbed
JSON when re-run on the same code+inputs. The cleanup epic does not regenerate
data; baseline locks the *output shape* the pipeline currently emits.
EOF

  ln -snf "$ts" "$BASELINE_ROOT/latest"

  echo "✓ Baseline written: $out_dir"
  echo "  Files snapshotted: $found_count"
  exit 0
fi

# Compare mode.
latest="$BASELINE_ROOT/latest"
if [[ ! -e "$latest" ]]; then
  echo "✗ No baseline at $latest — run with --baseline first" >&2
  exit 3
fi
baseline_manifest="$latest/MANIFEST.txt"
if [[ ! -f "$baseline_manifest" ]]; then
  echo "✗ Missing $baseline_manifest" >&2
  exit 3
fi

if diff -u "$baseline_manifest" "$manifest" >/tmp/parity_check_diff.$$; then
  echo "✓ Parity OK — $found_count files match baseline"
  rm -f /tmp/parity_check_diff.$$
  exit 0
else
  echo "✗ Parity DRIFT — diff:"
  cat /tmp/parity_check_diff.$$
  rm -f /tmp/parity_check_diff.$$
  exit 1
fi
