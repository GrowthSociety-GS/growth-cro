# enrich_v143_public.py — archived 2026-05-10 (Issue #6)

## Why archived

Per the codebase-cleanup epic Issue #6 split-map (`Mathis decisions, locked`):
this 1,339-LOC script was orthogonal to the reco generation domain that
Issue #6 was consolidating. Keeping it next to the recos pipeline added
god-file pressure with zero shared concern, so it was moved out instead of
being merged into `growthcro/recos/`.

## What it does (preserved here for future reference)

Three orthogonal enrichment modules bundled into one CLI:

1. **Founder enrichment** — LinkedIn + About-page scrape → name / bio / photo.
2. **Voice-of-Customer (VoC)** — Trustpilot + Google Reviews + native review pages.
3. **Scarcity signal extraction** — regex over already-captured page DOM/text.

The only thing it shared with reco generation was reading
`ANTHROPIC_API_KEY` (via raw `urllib.request` POSTs to `/v1/messages`,
not the SDK). It does NOT use the doctrine playbook, perception clusters,
or any prompt-building shared with `growthcro/recos/`.

## Status

- **Archived, not deleted.** `git log --follow` will trace its history
  through this move.
- **Not wired into the active reco pipeline** as of 2026-05-10 (`state.py`
  + `audit_capabilities.py` baseline confirms no caller).
- **Not migrated to `growthcro.config` / `growthcro.lib.anthropic_client`**
  — that work is intentionally deferred until the V14.3+ enrichment
  pipeline is re-specified.

## If you need it back

If a V14.3+ enrichment pipeline is re-specified and these three modules
are required:

1. Re-spec each concern as a separate single-purpose module under
   `growthcro/enrichment/{founder,voc,scarcity}.py`.
2. Replace the raw `urllib.request` Anthropic POSTs with
   `growthcro.lib.anthropic_client.get_anthropic_client()` (single SDK
   surface, retries handled, key validated via `growthcro.config`).
3. Wire it into the fleet runner explicitly so it shows up in
   `audit_capabilities.py` registry.

Do **not** restore the file as-is — the original raw-HTTP + bundled-concerns
shape was exactly the god-file pattern Issue #6 cleaned up.
