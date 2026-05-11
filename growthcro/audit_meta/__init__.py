"""Meta Ads audit module — thin wrapper around `anthropic-skills:meta-ads-auditor`.

Exposes a small public surface so callers (CLI, FastAPI route) can:

* parse a Meta Ads Manager CSV export into the canonical input bundle,
* invoke the audit orchestrator (which delegates analysis to the Anthropic skill),
* render the resulting findings as a Notion-ready page using the Growth Society
  template (sections A–H).

The module is a thin wrapper by design (Issue #22 AD-7): it MUST NOT reimplement
the audit logic — that is the skill's job. See `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`
combo pack `agency_products`.
"""

from growthcro.audit_meta.orchestrator import (
    AuditBundle,
    AuditInputs,
    AuditOutputs,
    run_audit,
)
from growthcro.audit_meta.notion_export_meta import (
    NOTION_TEMPLATE_SECTIONS,
    render_notion_markdown,
    render_notion_payload,
)

__all__ = [
    "AuditBundle",
    "AuditInputs",
    "AuditOutputs",
    "NOTION_TEMPLATE_SECTIONS",
    "render_notion_markdown",
    "render_notion_payload",
    "run_audit",
]
