# Split map — Issue #6 (recos god files → `growthcro/recos/`)

> **Mathis decisions (2026-05-10) — locked**:
> - **Archive `enrich_v143_public.py` NOW** → `_archive/scripts/enrich_v143_public_2026-05-10/` + README de dépréciation. Hors scope recos.
> - CLI: subcommands `prepare` + `enrich` sous un seul entry `growthcro.recos.cli`.
> - `growthcro.config` API confirmed: `from growthcro.config import config; config.anthropic_api_key()` (Optional) ou `config.require_anthropic_api_key()` (raises `MissingConfigError`). Lazy: validation au premier appel, pas à l'import.
> - **#6 owns the creation of `growthcro/lib/anthropic_client.py`** — autres agents (#7/#8) doivent `git pull --rebase` avant de l'importer.


## Duplicate verification (CRITICAL)

| Pair | Result | Canonical |
|---|---|---|
| `scripts/reco_enricher_v13.py` (139 LOC) vs `skills/site-capture/scripts/reco_enricher_v13.py` (1,690) | **NOT identical** — root is a stub (hard-coded Evaneos data, no API) | skills version |
| `scripts/reco_enricher_v13_api.py` (184) vs `skills/site-capture/scripts/reco_enricher_v13_api.py` (743) | **NOT identical** — root is minimal wrapper | skills version |
| `scripts/enrich_v143_public.py` (1,339) | Orthogonal domain (founder/VoC/scarcity enrichment, not recos) | **ARCHIVE** |

→ Both root variants become shims; both skills variants become the new canonical (collapsed into `growthcro/recos/`).

## File: `reco_enricher_v13.py` (canonical, 1,690 LOC)

Prompt preparation engine. Takes V12 baseline recos + doctrine (`bloc_*.json`) + anti-patterns + client intent, builds rich LLM prompts grounded in real page elements (H1, CTA text, clusters). Outputs `recos_v13_prompts.json`. Two modes: `--prepare` (dump prompts) + `--enrich-from` (merge LLM responses).

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `schema.py` | 50–111 | Doctrine + scope matrix caches, templates | 80 |
| `prompts.py` | 200–1120 | All prompt-building functions (vision, business, ICE, killer, funnel, V12 ref) | 520 |
| `orchestrator.py` | 1257–1593 | `prepare_prompts()`, --all/--pages-file/--top filtering | 280 |
| `cli.py` | 1594–1690 | argparse + main() dispatcher | 50 |

**Env vars**: none (reads `playbook/` + scope matrix path).

## File: `reco_enricher_v13_api.py` (canonical, 743 LOC)

Batched API client. Reads prompts → calls Claude (Haiku/Sonnet) → final reco JSON (before/after/why/expected_lift_pct/effort_hours/priority). Includes retry, JSON parsing fallback, dry-run, concurrent dispatch.

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `client.py` | 42–104, 110–161 | Anthropic init (`_get_api_client()`, `.env` loader), JSON extraction/validation | 150 |
| `cli.py` (extends from v13) | 160–743 | Batch orchestration (--all, --dry-run, --model, --max-concurrent), retry loop | 300 |

**Env vars**: `ANTHROPIC_API_KEY` (lazy `_load_dotenv_if_needed()` walks parents) → route via `growthcro.config`.

## File: `enrich_v143_public.py` (1,339 LOC) — **ARCHIVE**

Three orthogonal modules: Founder (LinkedIn + About → name/bio/photo) · VoC (Trustpilot + Google + native review pages) · Scarcity (regex on existing captures).

**Domain orthogonal** to reco generation. Shares only `ANTHROPIC_API_KEY`. No prompt-building, no doctrine, no perception clusters.

**Action**: move to `_archive/scripts/enrich_v143_public_2026-05-10/` with README explaining deprecation. If V14.3+ enrich pipeline supersedes it, link from README.

## Cross-file dedup

**Anthropic client setup** (3 sites):
- `reco_enricher_v13_api.py` L89–103: `_get_api_client()`, `_load_dotenv_if_needed()`
- `enrich_client.py` L59–64 + L505: lazy `import anthropic` + `Anthropic()`
- `enrich_v143_public.py` L130–161: raw `urllib.request` POST to `/v1/messages`

**Proposal**: extract `growthcro/lib/anthropic_client.py`:
```python
def get_anthropic_client() -> anthropic.Anthropic:
    """Lazy-load .env, validate key, return SDK client."""
    api_key = config.require("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=3)
```
Used by `growthcro/recos/client.py` + (later) `enrich_client.py`. Skip migrating `enrich_v143_public` (archived).

**Retry/backoff**: SDK `max_retries=3` already covers it — no custom code needed.

**Prompt-fragment helpers**: all already isolated in v13 → `prompts.py`. No cross-file dup.

## Shim plan

`scripts/reco_enricher_v13.py`:
```python
#!/usr/bin/env python3
"""Shim — use growthcro.recos.cli (removed in #11)."""
from growthcro.recos.cli import main
if __name__ == "__main__":
    main()
```

`scripts/reco_enricher_v13_api.py`:
```python
#!/usr/bin/env python3
"""Shim — use growthcro.recos.cli --enrich (removed in #11)."""
from growthcro.recos.cli import main
if __name__ == "__main__":
    main()
```

Same pattern for the two `skills/site-capture/scripts/reco_enricher_v13*.py` paths.

## Final layout

```
growthcro/recos/
├── __init__.py
├── schema.py          (~80 LOC)   doctrine cache + scope matrix
├── prompts.py         (~520)      data-shape only
├── client.py          (~150)      Anthropic wrapper, JSON parse/validate
├── orchestrator.py    (~280)      prepare_prompts() + batch loops
└── cli.py             (~330)      argparse, --prepare / --enrich subcommands

growthcro/lib/
└── anthropic_client.py (~40)     shared SDK client factory
```

Total ~1,400 LOC across 5 files. All ≤ 800.

## Open questions for Mathis

1. **`enrich_v143_public.py` archive**: confirm V14.3+ enrichment pipeline (somewhere in fleet runner?) supersedes it, or keep as-is until #10/#11 (orphan-wiring) decides? **Recommendation: archive now**, it's not wired into the active reco pipeline.
2. **CLI shape**: unify `--prepare` and `--enrich` under one `growthcro.recos.cli` with subcommands (`prepare`, `enrich`), or keep two CLI entrypoints? **Recommendation: subcommands** — fewer shims, clearer.
3. **`growthcro.config` API for `ANTHROPIC_API_KEY`**: confirm `config.require("ANTHROPIC_API_KEY")` raises `MissingConfigError` at import-time vs lazy at first call. Lazy preferred (avoids breaking `--prepare` mode which needs no API).
