"""Reco V13 generation pipeline — prompt prep + LLM enrichment.

The single-concern split (one file, one job) is:
- schema.py       : doctrine/threshold caches, scope matrix, JSON validation, ICE/fallback
- prompts.py      : prompt-string assembly only (data → string)
- client.py       : Anthropic SDK calls + JSON parsing + structured retry
- orchestrator.py : prepare_prompts() + per-page batch loop (process_page)
- cli.py          : argparse entrypoint with `prepare` / `enrich` subcommands

Public entrypoint for legacy script shims is `growthcro.recos.cli:main`.
"""
