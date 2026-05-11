"""Meta Ads audit CLI (axis #5).

Usage:
    python -m growthcro.audit_meta.cli --client <slug> --csv <path> [--out-dir <path>]
                                       [--period <label>] [--business-category <cat>]
                                       [--notes <text>] [--no-write] [--json]

Persists three artefacts under `data/audits/meta/<client>/<period>/`:
- `bundle.json` (full structured audit)
- `notion.md` (Markdown template A–H)
- `notion_payload.json` (Notion-API ready blocks)

The CLI never reads env, never calls an LLM. It composes orchestrator (axis #4)
+ notion_export (axis #8) and writes results to disk.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from growthcro.audit_meta.notion_export import (
    render_bundle_json,
    render_notion_markdown,
    render_notion_payload,
)
from growthcro.audit_meta.orchestrator import AuditInputs, run_audit


def _project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def _default_out_dir(client_slug: str, period: str) -> pathlib.Path:
    return _project_root() / "data" / "audits" / "meta" / client_slug / period


def _write_outputs(bundle_dict: dict, markdown: str, payload: dict, out_dir: pathlib.Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / "bundle.json"
    md_path = out_dir / "notion.md"
    payload_path = out_dir / "notion_payload.json"
    bundle_path.write_text(render_bundle_json(bundle_dict), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "bundle": str(bundle_path),
        "markdown": str(md_path),
        "notion_payload": str(payload_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="growthcro.audit_meta.cli",
        description="Run a Meta Ads audit via the meta-ads-auditor skill (thin wrapper).",
    )
    parser.add_argument("--client", required=True, help="Client slug (e.g. growth-society-acme).")
    parser.add_argument(
        "--csv",
        required=True,
        type=pathlib.Path,
        help="Path to Meta Ads Manager CSV export.",
    )
    parser.add_argument("--out-dir", type=pathlib.Path, default=None, help="Output directory.")
    parser.add_argument("--period", default=None, help="Period label, e.g. '2026-04' or 'last_30d'.")
    parser.add_argument(
        "--business-category",
        default="ecommerce",
        help="Business category hint for the skill (ecommerce / leadgen / saas / local).",
    )
    parser.add_argument("--notes", default="", help="Free-form notes attached to the audit.")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip disk writes (preview only). Used by tests and the API route.",
    )
    parser.add_argument("--json", action="store_true", help="Print the bundle JSON to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    csv_path = args.csv
    if not csv_path.exists():
        print(f"[audit_meta] CSV not found: {csv_path}", file=sys.stderr)
        return 2

    inputs = AuditInputs(
        client_slug=args.client,
        csv_path=csv_path,
        period_label=args.period,
        business_category=args.business_category,
        notes=args.notes,
    )

    bundle = run_audit(inputs)
    bundle_dict = bundle.as_dict()
    markdown = render_notion_markdown(bundle_dict)
    payload = render_notion_payload(bundle_dict)

    if args.json:
        print(render_bundle_json(bundle_dict))

    if args.no_write:
        if not args.json:
            print(
                f"[audit_meta] preview ok — client={args.client} period={inputs.normalised_period()}"
                f" rows={bundle_dict['row_count']}"
            )
        return 0

    out_dir = args.out_dir or _default_out_dir(args.client, inputs.normalised_period())
    artefacts = _write_outputs(bundle_dict, markdown, payload, out_dir)
    print(f"[audit_meta] artefacts written → {out_dir}")
    for name, path in artefacts.items():
        print(f"  - {name}: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry
    raise SystemExit(main())
