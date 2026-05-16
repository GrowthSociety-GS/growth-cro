# `_archive/architecture_pre_d1a/` — pre-D1.A architecture docs

Archived 2026-05-16 by issue [#41](https://github.com/GrowthSociety-GS/growth-cro/issues/41).

## Context

Documents in this folder describe webapp architectures from **before** `PRODUCT_BOUNDARIES_V26AH §3-bis D1.A` (2026-05-14, Mathis stamp 2026-05-14T16:30Z), which locked the **single shell** topology (`webapp/apps/shell/` only, microfrontends retired).

## Why archived, not deleted

Design rationale (especially around microfrontends multi-zone, Supabase RLS, Vercel topology choices) remains valuable as historical reference for future architecture decisions. Each archived doc carries a banner at the top pointing to its current canonical replacement.

## Living source of truth

Architecture decisions today live in:

- [`.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md`](../../.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md) — product boundaries + topology decisions (D1.A onwards)
- [`.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`](../../.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml) — machine-readable module + data-artefact map (auto-updated each epic)

## Contents

| File | Original path | Archived |
| --- | --- | --- |
| `GROWTHCRO_ARCHITECTURE_V1_SUPERSEDED_2026-05-14.md` | `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (2026-05-11 V28 target, 256 LOC) | 2026-05-16 (issue #41) |
| `GROWTHCRO_ARCHITECTURE_V1_dotclaude_copy_SUPERSEDED_2026-05-14.md` | `.claude/docs/architecture/GROWTHCRO_ARCHITECTURE_V1.md` (2026-04-05 "complete webapp" V1, 897 LOC) | 2026-05-16 (issue #41) |
