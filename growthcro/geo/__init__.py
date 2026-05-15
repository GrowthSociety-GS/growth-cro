"""GrowthCRO GEO Monitor V31+ — generative-engine optimisation observatory.

Probes ChatGPT / Claude / Perplexity for brand presence on standard buyer-
intent queries. Persists per-engine responses to Supabase `geo_audits` so the
webapp `/geo` pane can surface :
  - 30-day presence trend per engine + cumulative cost
  - Worst-performing queries (the ones where the brand is invisible)
  - Engine × query coverage matrix for per-client drilldown

Mono-concern submodules:
  - scorer      : pure presence-score formula (no I/O, no SDK).
  - runner      : per-engine query execution + defensive no-key handling.
  - cli         : argparse + python -m growthcro.geo entrypoint.
"""
