"""Compat shim — split into focused modules under ``moteur_gsg.core``.

Original 1,665 LOC file split in issue #8 (codebase-cleanup epic). New
import paths:

  * ``html_escaper``          — ``_e``, ``_paragraphs``
  * ``asset_resolver``        — ``_asset_src``, ``_asset_img``
  * ``fact_assembler``        — ``_facts``, ``_fact_chips``, ``_proof_strip``
  * ``hero_renderer``         — ``_hero_visual``
  * ``component_renderer``    — ``_reason_visual``, ``_component_bullets``,
                                ``_component_visual``
  * ``section_renderer``      — ``_render_component_section``,
                                ``_render_component_page``
  * ``css/{base,components,responsive}.py`` — stylesheet (3-way split)
  * ``page_renderer_orchestrator`` — public ``render_controlled_page`` entry

This shim re-exports the public entry so external consumers
(``from moteur_gsg.core.controlled_renderer import render_controlled_page``)
keep working. Removed in issue #11 once consumers migrate.
"""
from __future__ import annotations

from .page_renderer_orchestrator import render_controlled_page

__all__ = ["render_controlled_page"]
