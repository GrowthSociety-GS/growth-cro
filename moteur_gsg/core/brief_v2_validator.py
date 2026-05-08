"""moteur_gsg.core.brief_v2_validator — V26.AD Sprint I.

Couche d'entrée : parse + valide un BriefV2 depuis JSON file ou dict.
Persiste l'audit trail dans `data/_briefs_v2/<timestamp>_<client>_<page_type>.json`
(garde-fou §8 framework cadrage).

API publique :
    parse_brief_v2_from_json(path) -> BriefV2
    parse_brief_v2_from_dict(raw)  -> BriefV2
    validate_or_raise(brief)        -> None  (raise BriefV2ValidationError sinon)
    archive_brief_v2(brief)         -> Path of archived JSON
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any

from .brief_v2 import BriefV2

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARCHIVE_DIR = ROOT / "data" / "_briefs_v2"


class BriefV2ValidationError(ValueError):
    """Brief V2 fails validation. The errors list is exposed via .errors."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(self._format())

    def _format(self) -> str:
        n = len(self.errors)
        bullets = "\n  - ".join(self.errors)
        return f"BriefV2 invalide ({n} erreur{'s' if n > 1 else ''}) :\n  - {bullets}"


# ─────────────────────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────────────────────

def parse_brief_v2_from_dict(raw: dict) -> BriefV2:
    """Construit un BriefV2 depuis un dict (typiquement JSON parse).

    Ne valide PAS — appelle ensuite `validate_or_raise(brief)` ou `brief.validate()`.
    """
    if not isinstance(raw, dict):
        raise TypeError(f"parse_brief_v2_from_dict: expected dict, got {type(raw).__name__}")
    return BriefV2.from_dict(raw)


def parse_brief_v2_from_json(path: pathlib.Path | str) -> BriefV2:
    """Charge + parse un BriefV2 depuis fichier JSON sur disque."""
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"BriefV2 JSON not found: {p}")
    raw = json.loads(p.read_text(encoding="utf-8"))
    return parse_brief_v2_from_dict(raw)


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_or_raise(brief: BriefV2) -> None:
    """Lève BriefV2ValidationError si invalide, retourne None sinon."""
    errors = brief.validate()
    if errors:
        raise BriefV2ValidationError(errors)


# ─────────────────────────────────────────────────────────────────────────────
# Audit trail (§8 garde-fou framework cadrage)
# ─────────────────────────────────────────────────────────────────────────────

def archive_brief_v2(brief: BriefV2, *, label: str | None = None) -> pathlib.Path:
    """Persiste le brief dans `data/_briefs_v2/<ts>_<slug>_<page>.json`.

    Le label (optionnel) est inclus dans le filename pour distinguer plusieurs
    soumissions du même client/page. Sinon timestamp seul.

    Returns: chemin du fichier écrit.
    """
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    slug_url = brief.client_url or "no_url"
    # extract slug-like from URL
    slug = (
        slug_url.replace("https://", "").replace("http://", "")
        .split("/")[0].replace(".", "_").replace("www_", "")
    )[:30]
    parts = [ts, slug, brief.page_type]
    if label:
        parts.append(label)
    filename = "_".join(parts) + ".json"
    out_path = ARCHIVE_DIR / filename
    out_path.write_text(
        json.dumps(brief.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# CLI utility — validate a JSON file from shell
# ─────────────────────────────────────────────────────────────────────────────

def _cli_main():
    import argparse
    p = argparse.ArgumentParser(description="Validate a BriefV2 JSON file")
    p.add_argument("json_file", help="Path to brief_v2.json")
    p.add_argument("--archive", action="store_true", help="Archive into data/_briefs_v2/ if valid")
    p.add_argument("--label", default=None, help="Optional label for archive filename")
    args = p.parse_args()

    try:
        brief = parse_brief_v2_from_json(args.json_file)
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        print(f"❌ Parse error: {e}")
        return 1

    errors = brief.validate()
    if errors:
        print(f"❌ BriefV2 invalide ({len(errors)} erreur{'s' if len(errors) > 1 else ''}) :")
        for err in errors:
            print(f"   - {err}")
        return 2

    print(f"✓ BriefV2 valide : mode={brief.mode}, page_type={brief.page_type}, lang={brief.target_language}")
    print(f"  client_url       : {brief.client_url}")
    print(f"  objective        : {brief.objective[:80]}{'...' if len(brief.objective) > 80 else ''}")
    print(f"  audience size    : {len(brief.audience)} chars")
    print(f"  angle size       : {len(brief.angle)} chars")
    print(f"  proofs           : {brief.available_proofs}")
    print(f"  sourced_numbers  : {len(brief.sourced_numbers)}")
    print(f"  testimonials     : {len(brief.testimonials)}")
    print(f"  forbidden visual : {brief.forbidden_visual_patterns}")

    if args.archive:
        path = archive_brief_v2(brief, label=args.label)
        print(f"\n  ✓ Archived → {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli_main())
