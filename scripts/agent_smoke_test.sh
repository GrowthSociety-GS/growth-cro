#!/usr/bin/env bash
# scripts/agent_smoke_test.sh — Issue #10
# Verifies each .claude/agents/*.md sub-agent's first/canonical command resolves.
# Each block invokes the agent's primary entry in --help / dry-run mode and
# asserts a non-error exit. We don't run the full pipelines (those would call
# Anthropic), just confirm the modules import + the CLIs are reachable.

set -e

cd "$(git rev-parse --show-toplevel)"

ok() { echo "  ✓ OK"; }

echo "→ capabilities-keeper: python3 scripts/audit_capabilities.py"
python3 scripts/audit_capabilities.py >/dev/null
ok

echo "→ capture-worker: python3 -m growthcro.cli.capture_full --help"
python3 -m growthcro.cli.capture_full --help >/dev/null
echo "→ capture-worker: python3 -m growthcro.cli.add_client --help"
python3 -m growthcro.cli.add_client --help >/dev/null
echo "→ capture-worker: python3 -m growthcro.cli.enrich_client --help"
python3 -m growthcro.cli.enrich_client --help >/dev/null
echo "→ capture-worker: python3 -m growthcro.capture.cli --help"
python3 -m growthcro.capture.cli --help >/dev/null
echo "→ capture-worker: python3 -m growthcro.perception.cli --help"
python3 -m growthcro.perception.cli --help >/dev/null
ok

echo "→ scorer: python3 -m growthcro.scoring.cli --help (dispatcher)"
# The dispatcher exits 1 with usage when called with no args; we only assert
# that it printed "Subcommands:" (proves our dispatcher loaded, not the legacy
# argparse-only entrypoint).
out=$(python3 -m growthcro.scoring.cli --help 2>&1 || true)
echo "$out" | grep -q "Subcommands:" || { echo "  ✗ scoring.cli dispatcher missing"; exit 1; }
echo "→ scorer: python3 -m growthcro.scoring.cli specific (usage probe)"
out=$(python3 -m growthcro.scoring.cli specific 2>&1 || true)
echo "$out" | grep -q "specific <label>" || { echo "  ✗ specific subcommand broken"; exit 1; }
echo "→ scorer: python3 -m growthcro.scoring.cli ux (usage probe)"
out=$(python3 -m growthcro.scoring.cli ux 2>&1 || true)
echo "$out" | grep -q "ux <label>" || { echo "  ✗ ux subcommand broken"; exit 1; }
echo "→ scorer: page_type orchestrator help"
python3 skills/site-capture/scripts/score_page_type.py 2>&1 | grep -q "Usage" \
  || { echo "  ✗ score_page_type.py usage missing"; exit 1; }
echo "→ scorer: batch_rescore importable (no --help mode; assert module-level parse OK)"
# batch_rescore.py runs work at import time; just confirm the file is parseable.
python3 -c "import ast; ast.parse(open('skills/site-capture/scripts/batch_rescore.py').read())" \
  || { echo "  ✗ batch_rescore.py unparseable"; exit 1; }
ok

echo "→ reco-enricher: python3 -m growthcro.recos.cli prepare --help"
python3 -m growthcro.recos.cli prepare --help >/dev/null
echo "→ reco-enricher: python3 -m growthcro.recos.cli enrich --help"
python3 -m growthcro.recos.cli enrich --help >/dev/null
ok

echo "→ doctrine-keeper: doctrine module imports"
python3 -c "
from growthcro.recos import schema as _s
assert hasattr(_s, 'compute_recos_brutes_from_scores'), 'recos.schema API missing'
from growthcro.scoring.specific import DETECTORS, TERNARY  # noqa
print('  doctrine modules importable')
" >/dev/null
ok

echo ""
echo "ALL AGENT SMOKE TESTS PASS"
