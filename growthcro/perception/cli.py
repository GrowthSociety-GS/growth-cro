"""argparse entrypoint for the perception pipeline (single page or fleet-wide --all)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from growthcro.perception.persist import process_page


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="Label client (ex: japhy)")
    ap.add_argument("--page", help="Page type (ex: home)")
    ap.add_argument("--data-dir", default="data/captures", help="Base data dir")
    ap.add_argument("--all", action="store_true", help="Process every client × page")
    args = ap.parse_args()

    base = Path(args.data_dir)
    if not base.exists():
        print(f"❌ {base} n'existe pas", file=sys.stderr)
        sys.exit(1)

    targets: list[tuple[Path, Path, Path]] = []
    if args.all:
        for client_dir in sorted(base.iterdir()):
            if not client_dir.is_dir():
                continue
            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir():
                    continue
                sp = page_dir / "spatial_v9_clean.json"
                if not sp.exists():
                    sp = page_dir / "spatial_v9.json"
                if sp.exists():
                    cp = page_dir / "capture.json"
                    out = page_dir / "perception_v13.json"
                    targets.append((sp, cp, out))
    else:
        if not args.client or not args.page:
            print("❌ --client et --page requis (ou --all)", file=sys.stderr)
            sys.exit(1)
        page_dir = base / args.client / args.page
        sp = page_dir / "spatial_v9_clean.json"
        if not sp.exists():
            sp = page_dir / "spatial_v9.json"
        if not sp.exists():
            print(f"❌ pas de spatial_v9 dans {page_dir}", file=sys.stderr)
            sys.exit(1)
        cp = page_dir / "capture.json"
        out = page_dir / "perception_v13.json"
        targets.append((sp, cp, out))

    print(f"→ {len(targets)} page(s) à traiter")
    ok = 0
    for sp, cp, out in targets:
        try:
            res = process_page(sp, cp, out)
            if res.get("status") == "ok":
                ok += 1
        except Exception as e:
            print(f"  ❌ {sp}: {e}")

    print(f"\n✓ {ok}/{len(targets)} pages processées")


if __name__ == "__main__":
    main()
