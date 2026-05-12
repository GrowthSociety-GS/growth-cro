"""Reco CLI — single argparse entrypoint with `prepare` / `enrich` subcommands.

Single concern: parse argv, dispatch to orchestrator. All shims (legacy
`reco_enricher_v13.py` and `reco_enricher_v13_api.py` paths in `scripts/`
and `skills/site-capture/scripts/`) point here.

For backward compatibility with the historical flag-style invocation, the
old top-level flags (`--prepare`, `--all`, `--client`, `--page`, etc.) are
still accepted when no subcommand is provided. The deprecation path is to
move callers to the explicit subcommands.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from growthcro.models.recos_models import RecoInput
from growthcro.recos import client as _client
from growthcro.recos import orchestrator as _orch


# ────────────────────────────────────────────────────────────────
# `prepare` subcommand — assemble prompts (no API call, 0€)
# ────────────────────────────────────────────────────────────────
def _add_prepare_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--client", help="Client label (ignored when --all/--pages-file)")
    p.add_argument("--page", help="Page type (ignored when --all/--pages-file)")
    p.add_argument("--all", action="store_true", help="Iterate every client/page in --data-dir")
    p.add_argument("--pages-file", help="Text file with one 'client/page' line per page (targeted batch)")
    p.add_argument("--top", type=int, default=0, help="Top N criteria (0 = ALL applicable)")
    p.add_argument("--data-dir", default="data/captures")
    p.add_argument(
        "--min-confidence", type=float, default=0.5,
        help="Skip clients whose intent confidence < threshold",
    )


def _run_prepare(args: argparse.Namespace) -> None:
    if args.pages_file:
        pf = Path(args.pages_file)
        if not pf.exists():
            print(f"pages-file not found: {pf}", file=sys.stderr)
            sys.exit(1)
        total_pages = 0
        total_prompts = 0
        for line in pf.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("/")
            if len(parts) != 2:
                print(f"line ignored: {line!r} (expected 'client/page')", file=sys.stderr)
                continue
            client, page = parts
            try:
                out = _orch.prepare_prompts(client, page, args.top, Path(args.data_dir), strict=False)
                if out is None:
                    continue
                total_pages += 1
                try:
                    d = json.load(open(out))
                    total_prompts += len(d.get("prompts", []))
                except Exception:
                    pass
            except Exception as e:
                print(f"  ❌ {client}/{page}: {e}")
        print(f"\n✓ {total_pages} pages préparées, {total_prompts} prompts total (depuis pages-file)")
        return

    if args.all:
        base = Path(args.data_dir)
        total_pages = 0
        total_prompts = 0
        skipped = 0
        for client_dir in sorted(base.iterdir()):
            if not client_dir.is_dir():
                continue
            client = client_dir.name
            intent_file = client_dir / "client_intent.json"
            if not intent_file.exists():
                continue
            try:
                intent_data = json.load(open(intent_file))
            except Exception:
                continue
            conf = intent_data.get("confidence", 0) or 0
            if conf < args.min_confidence:
                print(f"  ⏭  {client}: skip (conf={conf:.2f} < {args.min_confidence})")
                skipped += 1
                continue
            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir():
                    continue
                perception_file = page_dir / "perception_v13.json"
                if not perception_file.exists():
                    continue
                try:
                    out = _orch.prepare_prompts(client, page_dir.name, args.top, Path(args.data_dir), strict=False)
                    if out is None:
                        continue
                    total_pages += 1
                    try:
                        d = json.load(open(out))
                        total_prompts += len(d.get("prompts", []))
                    except Exception:
                        pass
                except Exception as e:
                    print(f"  ❌ {client}/{page_dir.name}: {e}")
        print(f"\n✓ {total_pages} pages préparées, {total_prompts} prompts total, {skipped} clients skip (confidence)")
        return

    if not args.client or not args.page:
        print("--client et --page requis (ou --all / --pages-file)", file=sys.stderr)
        sys.exit(1)
    _orch.prepare_prompts(args.client, args.page, args.top, Path(args.data_dir))


# ────────────────────────────────────────────────────────────────
# `enrich` subcommand — call Claude on prepared prompts
# ────────────────────────────────────────────────────────────────
def _add_enrich_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--client")
    p.add_argument("--page")
    p.add_argument("--all", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="No API call, just estimate cost")
    p.add_argument("--data-dir", default="data/captures")
    p.add_argument("--model", default=_client.DEFAULT_MODEL)
    p.add_argument("--max-concurrent", type=int, default=5)
    p.add_argument("--force", action="store_true", help="Force re-call even if cache exists")
    p.add_argument("--pages-file", help="Targeted batch from a 'client/page' lines file")


def _run_enrich(args: argparse.Namespace) -> None:
    base = Path(args.data_dir)
    if args.dry_run:
        _orch.dry_run(base)
        return

    prompt_files: list[Path] = []
    out_files: list[Path] = []
    if args.pages_file:
        pf_list = Path(args.pages_file).read_text().splitlines()
        for line in pf_list:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("/")
            if len(parts) != 2:
                print(f"line ignored: {line!r} (expected client/page)", file=sys.stderr)
                continue
            client, page = parts
            pf = base / client / page / "recos_v13_prompts.json"
            if not pf.exists():
                print(f"missing: {pf}", file=sys.stderr)
                continue
            prompt_files.append(pf)
            out_files.append(base / client / page / "recos_v13_final.json")
        print(f"   pages-file: {len(prompt_files)} pages from {args.pages_file}")
    elif args.all:
        for cd in sorted(base.iterdir()):
            if not cd.is_dir():
                continue
            for pd in sorted(cd.iterdir()):
                if not pd.is_dir():
                    continue
                pf = pd / "recos_v13_prompts.json"
                if pf.exists():
                    prompt_files.append(pf)
                    out_files.append(pd / "recos_v13_final.json")
    else:
        if not args.client or not args.page:
            print("--client et --page requis (ou --all / --pages-file / --dry-run)", file=sys.stderr)
            sys.exit(1)
        pf = base / args.client / args.page / "recos_v13_prompts.json"
        if not pf.exists():
            print(f"{pf} manquant", file=sys.stderr)
            sys.exit(1)
        prompt_files.append(pf)
        out_files.append(base / args.client / args.page / "recos_v13_final.json")

    print(f"→ {len(prompt_files)} page(s), modèle={args.model}, concurrency={args.max_concurrent}")
    asyncio.run(_orch.run_async(prompt_files, out_files, args.model, args.max_concurrent, args.force))


# ────────────────────────────────────────────────────────────────
# `view` subcommand — typed read of the post-pipeline RecoBatch (Issue #32)
# ────────────────────────────────────────────────────────────────
def _add_view_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--client", required=True, help="Client slug (e.g. weglot)")
    p.add_argument("--page", required=True, help="Page type (e.g. home, lp_listicle)")
    p.add_argument("--data-dir", default="data/captures")


def _run_view(args: argparse.Namespace) -> None:
    """Read recos_v13_final.json via the typed RecoBatch boundary (V26.A enforced)."""
    ri = RecoInput(slug=args.client, page_type=args.page, data_dir=args.data_dir)
    try:
        batch = _orch.orchestrate_recos(ri)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(3)

    n_fb = sum(1 for r in batch.recos if r.is_fallback)
    n_ok = len(batch.recos) - n_fb
    print(f"{batch.slug}/{batch.page_type}: {len(batch.recos)} recos ({n_ok} OK, {n_fb} fallback)")
    for r in batch.recos:
        flag = "FB" if r.is_fallback else "OK"
        print(f"  [{flag}] {r.criterion_id} {r.priority} ev={len(r.evidence_ids)} — {r.before[:80]}")


# ────────────────────────────────────────────────────────────────
# Legacy flag-style invocation (back-compat for the 4 shimmed scripts)
# ────────────────────────────────────────────────────────────────
def _looks_like_legacy_invocation(argv: list[str]) -> str | None:
    """Return 'prepare' | 'enrich' | None depending on legacy flags present.

    The historical CLIs were:
      reco_enricher_v13.py     ... --prepare ...        → prepare
      reco_enricher_v13_api.py ... [--dry-run|--all] ... → enrich
    """
    if not argv:
        return None
    if argv[0] in {"prepare", "enrich", "view"}:
        return None  # already a subcommand, not legacy
    if "--prepare" in argv:
        return "prepare"
    # Heuristic: --dry-run / --model / --max-concurrent are enrich-only.
    if any(flag in argv for flag in ("--dry-run", "--model", "--max-concurrent", "--force")):
        return "enrich"
    # Last resort: if --all or --client/--page passed without --prepare, default to prepare
    # (the old reco_enricher_v13.py default behaviour).
    if any(flag in argv for flag in ("--all", "--pages-file", "--client", "--page")):
        return "prepare"
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="growthcro.recos",
        description="Reco V13 pipeline — prepare prompts (offline) then enrich via Claude.",
    )
    sub = parser.add_subparsers(dest="cmd")

    prep = sub.add_parser("prepare", help="Build LLM prompts from page captures (no API call)")
    _add_prepare_args(prep)

    enr = sub.add_parser("enrich", help="Call Claude on prepared prompts → final reco JSON")
    _add_enrich_args(enr)

    view = sub.add_parser(
        "view",
        help="Read recos_v13_final.json via the typed RecoBatch boundary (Issue #32, V26.A enforced)",
    )
    _add_view_args(view)

    return parser


def main(argv: list[str] | None = None) -> None:
    raw_argv = sys.argv[1:] if argv is None else argv

    legacy = _looks_like_legacy_invocation(raw_argv)
    if legacy is not None:
        # Legacy invocation: synthesise the subcommand argument before parsing.
        injected = [legacy] + [a for a in raw_argv if a != "--prepare"]
        # `--prepare` is the legacy "do prepare" toggle — drop it; `prepare`
        # subcommand is now positional.
        parser = _build_parser()
        args = parser.parse_args(injected)
    else:
        parser = _build_parser()
        args = parser.parse_args(raw_argv)

    if args.cmd == "prepare":
        _run_prepare(args)
    elif args.cmd == "enrich":
        _run_enrich(args)
    elif args.cmd == "view":
        _run_view(args)
    else:
        parser.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
