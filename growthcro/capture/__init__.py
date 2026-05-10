"""GrowthCRO capture package — single concern: collect raw page artifacts.

Layered modules (no back-references):
    cli           → orchestrator → browser / cloud / dom → persist
    scorer (standalone — static-HTML extraction, called via shim)

Public re-exports kept minimal; sub-agents import the concrete module.
"""
