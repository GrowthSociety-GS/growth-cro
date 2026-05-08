# Webapp V27 Command Center — Static MVP Stratospheric Track

> Date : 2026-05-05
> Status : shipped as static HTML MVP.
> Entry : `deliverables/GrowthCRO-V27-CommandCenter.html`

## Executive Verdict

The next product step is not Reality metrics. A strong GrowthCRO V1 can start with Audit + Recos + GSG if the experience is coherent, actionable and demonstrable.

Reality Layer remains a long-term moat, but it is not a blocker for a stratospheric functional webapp.

## What Shipped

### 1. Webapp V27 Command Center

New static app:

```text
deliverables/GrowthCRO-V27-CommandCenter.html
```

It reads the existing runtime dataset:

```text
deliverables/growth_audit_data.js
```

It keeps the V26 observatory intact and adds a focused V27 product layer:

- Command Center fleet overview
- client roster with search, sort and panel role filter
- selected client detail
- screenshot-first page inspection
- pillar bars
- prioritized recos
- GSG handoff view
- end-to-end Weglot demo

### 2. Audit & Reco Command Center

The webapp now turns audit data into a triage surface:

- P0/P1 visible immediately
- page score and evidence summary
- top recos sorted by priority then ICE
- client panel role visible
- screenshots used as visual proof

### 3. GSG Reconstruction Track

The GSG is not rebuilt as a bigger prompt. The V27 track starts with a deterministic handoff:

```text
scripts/build_audit_to_gsg_brief.mjs
```

This script creates a structured brief from existing audit/reco data:

- audit source
- top recos
- brand tokens
- deterministic layout plan
- copy contract
- renderer contract
- LLM boundary
- risk flags for proof/VoC/urgency

### 4. Audit/Reco To GSG Connection

Generated demo artifacts:

```text
deliverables/gsg_demo/weglot-home-gsg-v27.json
deliverables/gsg_demo/weglot-home-gsg-v27.md
deliverables/gsg_demo/weglot-home-gsg-v27-preview.html
deliverables/gsg_demo/v27-command-center-qa.png
```

The bridge is deliberately read-only on audit/reco data. It does not run scoring, does not call Reality, and does not let the LLM decide structure.

### 5. End-To-End Demo

Default demo target:

```text
weglot / home
```

Flow:

```text
Audit score -> P0 recos -> deterministic brief -> controlled preview -> post-run judge boundary
```

## Product Rule Added

When a reco asks for testimonials, reviews, G2 ratings, Trustpilot, urgency or scarcity, the bridge adds risk flags. The GSG can reserve the section, but cannot invent proof.

Examples:

- `requires_real_voc`
- `requires_external_proof_source`
- `urgency_must_be_truthful`

## Commands

Build the demo brief:

```bash
node scripts/build_audit_to_gsg_brief.mjs --client weglot --page home
```

Open the static V27 webapp:

```text
deliverables/GrowthCRO-V27-CommandCenter.html
```

## Validation

- `node --check scripts/build_audit_to_gsg_brief.mjs`
- inline script parse for `GrowthCRO-V27-CommandCenter.html`
- JSON validation for `weglot-home-gsg-v27.json`
- Playwright file render:
  - 56 clients loaded
  - GSG handoff view loaded
  - brief length ~7k chars
  - zero console/page errors

## Remaining Product Work

1. Make V27 the default webapp entry after Mathis review.
2. Add a true generated LP renderer behind the deterministic brief.
3. Add post-run deterministic judges in the V27 UI.
4. Add side-by-side current page vs generated page.
5. Add manual client business-lock editing later, not inside static HTML.

