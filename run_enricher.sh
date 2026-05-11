#!/bin/bash
# Wrapper to invoke the reco-enricher v13 API batch from this repo.
# Pre-#9, this script cd'd into a stale iCloud path; updated for the cleanup epic.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m growthcro.recos.cli enrich "$@"
