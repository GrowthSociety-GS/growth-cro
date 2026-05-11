# growthcro.research

Site intelligence: brand identity + content discovery for a client URL.
Was `scripts/site_intelligence.py` before the #7 split.

## Modules
- `cli.py` — argparse entry (`run_intelligence` orchestrator).
- `brand_identity.py` — extracts logo, colors, typography signals.
- `content.py` — H1/H2/copy clustering + topic detection.
- `discovery.py` — sitemap + internal-link crawl (lightweight, no JS).

## Entrypoints
```bash
python -m growthcro.research.cli --client <label> --url <url>
```

## Imports from
- `growthcro.config`.
- `requests`, `beautifulsoup4`.

## Imported by
- `growthcro.cli.add_client` (auto-runs at client creation).
- `scripts/client_context.py`.
