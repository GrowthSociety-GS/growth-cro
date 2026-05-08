#!/usr/bin/env python3
"""V26.A Evidence Ledger — preuves vérifiables pour chaque score et reco.

Architecture audit-ready (cf. ChatGPT Hardcore Audit Blueprint §3.2) :

  Chaque score et chaque reco doit pointer vers une EVIDENCE concrète :
  - screenshot crop (pixel-level)
  - DOM selector (technique)
  - texte observé (preuve textuelle)
  - bbox + viewport (localisation)
  - capture_hash (intégrité — la capture n'a pas changé)
  - model + prompt_version (traçabilité du juge)

  Sans ce ledger, une reco reste difficile à :
  - Auditer (« Pourquoi tu dis ça ? »)
  - Debunker (« Tu te trompes »)
  - Expliquer au client (« Voici la preuve »)

Schema EvidenceLedgerItem :
{
  "evidence_id": "ev_<client>_<page>_<criterion>_<seq>",
  "client": "japhy",
  "page": "home",
  "viewport": "desktop|mobile",
  "source_type": "vision|dom|hybrid_vision_dom|computed_style|llm_classifier|rule_deterministic|api_external",
  "dom_selector": "main section:first-of-type h1",
  "text_observed": "L'alimentation experte pour votre chien",
  "bbox": {"x": 120, "y": 188, "w": 620, "h": 92},
  "screenshot_crop": "crops/hero_01_desktop.png",
  "capture_hash": "sha256:abc123...",
  "model": "claude-haiku-4-5-20251001",
  "prompt_version": "vision_spatial_v24_3",
  "confidence": 0.91,
  "captured_at": "2026-04-29T14:32:11",
  "criterion_ref": "hero_01",
  "linked_to": {
    "score_files": ["score_hero.json"],
    "reco_ids": ["reco_per_01_001"]
  }
}

Storage : data/captures/<client>/<page>/evidence_ledger.json (1 file par
(client, page), JSON array d'items). Append-only normalement (les
evidences passées restent — versionnage via captured_at).

Usage :
    from evidence_ledger import EvidenceLedger

    el = EvidenceLedger(client="japhy", page="home", viewport="desktop")
    eid = el.add(
        source_type="vision+dom",
        dom_selector="main section:first-of-type h1",
        text_observed="L'alimentation experte pour votre chien",
        bbox={"x": 120, "y": 188, "w": 620, "h": 92},
        screenshot_crop="crops/hero_01_desktop.png",
        model="claude-haiku-4-5",
        prompt_version="vision_spatial_v24_3",
        confidence=0.91,
        criterion_ref="hero_01",
    )
    el.flush()  # writes evidence_ledger.json

    # Resolve evidence_id → item (pour debug/audit)
    item = el.resolve(eid)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any, Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"


def compute_capture_hash(file_path: pathlib.Path) -> str:
    """sha256:<hex> of file contents. Used to verify capture integrity over time."""
    if not file_path.exists():
        return "sha256:NOT_FOUND"
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


class EvidenceLedger:
    """Per-page evidence ledger. Append-friendly. Atomic writes."""

    def __init__(self, client: str, page: str, viewport: str = "desktop"):
        self.client = client
        self.page = page
        self.viewport = viewport
        self.client_dir = CAPTURES / client
        self.page_dir = self.client_dir / page
        self.page_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.page_dir / "evidence_ledger.json"
        self._items: list[dict] = []
        self._counter: dict[str, int] = {}  # criterion_ref → next seq #
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            try:
                d = json.loads(self.path.read_text())
                self._items = d.get("items", [])
                # Restore counter to avoid evidence_id collisions
                for it in self._items:
                    cr = it.get("criterion_ref") or "_global"
                    eid = it.get("evidence_id", "")
                    # Try to extract seq from "ev_japhy_home_hero_01_001"
                    parts = eid.split("_")
                    if parts and parts[-1].isdigit():
                        seq = int(parts[-1])
                        self._counter[cr] = max(self._counter.get(cr, 0), seq)
            except Exception:
                self._items = []
        self._loaded = True

    def add(
        self,
        source_type: str,
        dom_selector: Optional[str] = None,
        text_observed: Optional[str] = None,
        bbox: Optional[dict] = None,
        screenshot_crop: Optional[str] = None,
        capture_hash: Optional[str] = None,
        model: Optional[str] = None,
        prompt_version: Optional[str] = None,
        confidence: Optional[float] = None,
        criterion_ref: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> str:
        """Add an evidence item. Returns the generated evidence_id."""
        self._load()
        cr = criterion_ref or "_global"
        self._counter[cr] = self._counter.get(cr, 0) + 1
        seq = self._counter[cr]
        eid = f"ev_{self.client}_{self.page}_{cr}_{seq:03d}"

        item: dict[str, Any] = {
            "evidence_id": eid,
            "client": self.client,
            "page": self.page,
            "viewport": self.viewport,
            "source_type": source_type,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if dom_selector is not None:
            item["dom_selector"] = dom_selector
        if text_observed is not None:
            item["text_observed"] = (text_observed or "")[:500]
        if bbox is not None:
            item["bbox"] = bbox
        if screenshot_crop is not None:
            item["screenshot_crop"] = screenshot_crop
        if capture_hash is not None:
            item["capture_hash"] = capture_hash
        if model is not None:
            item["model"] = model
        if prompt_version is not None:
            item["prompt_version"] = prompt_version
        if confidence is not None:
            item["confidence"] = confidence
        if criterion_ref is not None:
            item["criterion_ref"] = criterion_ref
        if extra:
            item.update(extra)

        self._items.append(item)
        return eid

    def link(self, evidence_id: str, score_file: Optional[str] = None,
             reco_id: Optional[str] = None) -> None:
        """Link an existing evidence item to a score file or reco_id (back-pointer)."""
        for it in self._items:
            if it.get("evidence_id") == evidence_id:
                lt = it.setdefault("linked_to", {"score_files": [], "reco_ids": []})
                if score_file and score_file not in lt["score_files"]:
                    lt["score_files"].append(score_file)
                if reco_id and reco_id not in lt["reco_ids"]:
                    lt["reco_ids"].append(reco_id)
                return

    def resolve(self, evidence_id: str) -> Optional[dict]:
        """Return the evidence item matching evidence_id, or None."""
        self._load()
        for it in self._items:
            if it.get("evidence_id") == evidence_id:
                return dict(it)
        return None

    def items(self) -> list[dict]:
        self._load()
        return list(self._items)

    def flush(self) -> None:
        """Atomic write to disk (tmp + rename)."""
        self._load()
        out = {
            "version": "v26.A.1.0",
            "client": self.client,
            "page": self.page,
            "viewport": self.viewport,
            "n_items": len(self._items),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "items": self._items,
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        tmp.replace(self.path)


# ────────────────────────────────────────────────────────────────
# Convenience functions for downstream scripts
# ────────────────────────────────────────────────────────────────

def load_or_create(client: str, page: str, viewport: str = "desktop") -> EvidenceLedger:
    """Convenience constructor — same as EvidenceLedger() but explicit."""
    return EvidenceLedger(client, page, viewport)


def attach_evidence_to_score(
    score_file: pathlib.Path,
    evidence_ids: list[str],
    criterion_id: Optional[str] = None,
) -> None:
    """Add `evidence_ids` to a score_*.json (in place, atomic).
    If criterion_id is given, attaches at the per-criterion level :
        score['criteria'][i]['evidence_ids'] = [...]
    Otherwise at the file root :
        score['evidence_ids'] = [...]
    """
    if not score_file.exists():
        return
    try:
        d = json.loads(score_file.read_text())
    except Exception:
        return
    if criterion_id and "criteria" in d:
        for c in d["criteria"]:
            if c.get("id") == criterion_id:
                existing = set(c.get("evidence_ids") or [])
                existing.update(evidence_ids)
                c["evidence_ids"] = sorted(existing)
                break
    else:
        existing = set(d.get("evidence_ids") or [])
        existing.update(evidence_ids)
        d["evidence_ids"] = sorted(existing)
    tmp = score_file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    tmp.replace(score_file)


def attach_evidence_to_reco(
    recos_file: pathlib.Path,
    reco_id: str,
    evidence_ids: list[str],
) -> None:
    """Add `evidence_ids` to a specific reco in recos_v13_final.json."""
    if not recos_file.exists():
        return
    try:
        d = json.loads(recos_file.read_text())
    except Exception:
        return
    for r in d.get("recos", []):
        if r.get("reco_id") == reco_id or r.get("criterion_id") == reco_id:
            existing = set(r.get("evidence_ids") or [])
            existing.update(evidence_ids)
            r["evidence_ids"] = sorted(existing)
            break
    tmp = recos_file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    tmp.replace(recos_file)


# ────────────────────────────────────────────────────────────────
# CLI demo
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="japhy")
    ap.add_argument("--page", default="home")
    ap.add_argument("--viewport", default="desktop")
    ap.add_argument("--list", action="store_true", help="List items")
    args = ap.parse_args()

    el = EvidenceLedger(args.client, args.page, args.viewport)
    if args.list:
        for it in el.items():
            print(f"  {it['evidence_id']:50s} {it['source_type']:20s} {it.get('criterion_ref') or '-':10s}")
        print(f"\n  Total : {len(el.items())} items in {el.path}")
    else:
        # Demo : add a fake evidence
        eid = el.add(
            source_type="vision+dom",
            dom_selector="main section:first-of-type h1",
            text_observed="L'alimentation experte pour votre chien",
            bbox={"x": 120, "y": 188, "w": 620, "h": 92},
            model="claude-haiku-4-5-20251001",
            prompt_version="vision_spatial_v24_3",
            confidence=0.91,
            criterion_ref="hero_01",
        )
        el.flush()
        print(f"✓ Added evidence : {eid}")
        print(f"  Resolve → {json.dumps(el.resolve(eid), indent=2, ensure_ascii=False)[:200]} …")
