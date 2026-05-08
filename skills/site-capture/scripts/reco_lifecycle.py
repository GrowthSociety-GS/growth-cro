#!/usr/bin/env python3
"""V26.B Reco Lifecycle — state machine pour le cycle de vie des recos.

Architecture (cf. ChatGPT Hardcore Audit Blueprint §9.2) :

  generated
    ↓
  reviewed (humain ou auto-critic)
    ↓
  accepted (consultant valide)
    ↓
  ticket_created (Linear / Jira)
    ↓
  implemented (deployed prod)
    ↓
  qa_passed (vérif post-deploy)
    ↓
  experiment_started (A/B test live)
    ↓
  measured (sample size atteint, résultat stat-significatif)
    ↓
  won | lost | inconclusive
    ↓
  learning_applied | archived

Pourquoi : sans lifecycle, on génère des recos puis on oublie.
Le Learning Layer V28 a besoin du parcours complet pour calibrer
les confidence priors et faire évoluer la doctrine.

Storage : intégré dans chaque reco de recos_v13_final.json :
{
  "criterion_id": "hero_01",
  "before": "...",
  "after": "...",
  ...
  "lifecycle": {
    "status": "generated|reviewed|accepted|ticket_created|implemented|qa_passed|experiment_started|measured|won|lost|inconclusive|learning_applied|archived",
    "history": [
      {"status": "generated", "at": "2026-04-29T18:34", "by": "haiku-4-5", "note": null},
      {"status": "reviewed", "at": "2026-04-30T10:00", "by": "mathis", "note": "OK"},
      ...
    ],
    "owner": "mathis@growth-society.com",
    "ticket_url": "https://linear.app/growth/issue/GS-1234",
    "implemented_at": "2026-05-02T09:30",
    "experiment_id": "exp_japhy_hero_clarity_v1",
    "outcome": "won",
    "outcome_lift": 0.087,
    "outcome_confidence": 0.92
  }
}

Usage :
    from reco_lifecycle import RecoLifecycle, transition

    rl = RecoLifecycle(reco)
    rl.transition("reviewed", by="mathis", note="Approved")
    rl.transition("accepted", by="mathis")
    rl.set_ticket("https://linear.app/growth/issue/GS-1234")
    rl.transition("implemented", by="dev_team", at="2026-05-02T09:30")
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Optional

# State machine — allowed transitions
TRANSITIONS = {
    "generated": {"reviewed", "archived"},
    "reviewed": {"accepted", "rejected", "archived"},
    "rejected": {"archived"},
    "accepted": {"ticket_created", "archived"},
    "ticket_created": {"implemented", "abandoned", "archived"},
    "abandoned": {"archived"},
    "implemented": {"qa_passed", "qa_failed", "archived"},
    "qa_failed": {"implemented", "abandoned", "archived"},  # rework
    "qa_passed": {"experiment_started", "archived"},  # archive if no A/B
    "experiment_started": {"measured", "abandoned", "archived"},
    "measured": {"won", "lost", "inconclusive", "archived"},
    "won": {"learning_applied", "archived"},
    "lost": {"learning_applied", "archived"},
    "inconclusive": {"learning_applied", "experiment_started", "archived"},  # rerun
    "learning_applied": {"archived"},
    "archived": set(),  # terminal
}

VALID_STATUSES = set(TRANSITIONS.keys())


def init_lifecycle(by: str = "system", note: Optional[str] = None) -> dict:
    """Initialize a fresh lifecycle dict for a newly-generated reco."""
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "status": "generated",
        "history": [
            {"status": "generated", "at": now, "by": by, "note": note}
        ],
        "owner": None,
        "ticket_url": None,
        "implemented_at": None,
        "experiment_id": None,
        "outcome": None,
        "outcome_lift": None,
        "outcome_confidence": None,
    }


class RecoLifecycle:
    """Wrapper around a reco dict's lifecycle field. In-place mutations."""

    def __init__(self, reco: dict):
        self.reco = reco
        if "lifecycle" not in reco:
            reco["lifecycle"] = init_lifecycle(by="legacy_init")
        self.lc = reco["lifecycle"]

    def status(self) -> str:
        return self.lc.get("status", "generated")

    def transition(self, new_status: str, by: str = "system",
                   note: Optional[str] = None, at: Optional[str] = None,
                   strict: bool = True) -> bool:
        """Transition to new_status. Returns True if applied, False if rejected.
        If strict=True (default), raises ValueError on invalid transition."""
        cur = self.status()
        if new_status not in VALID_STATUSES:
            if strict:
                raise ValueError(f"Unknown status: {new_status}")
            return False
        if new_status not in TRANSITIONS.get(cur, set()):
            if strict:
                raise ValueError(f"Invalid transition: {cur} → {new_status}")
            return False
        self.lc["status"] = new_status
        when = at or time.strftime("%Y-%m-%dT%H:%M:%S")
        self.lc.setdefault("history", []).append({
            "status": new_status,
            "at": when,
            "by": by,
            "note": note,
        })
        return True

    def set_owner(self, owner: str) -> None:
        self.lc["owner"] = owner

    def set_ticket(self, url: str) -> None:
        self.lc["ticket_url"] = url

    def set_implemented(self, at: Optional[str] = None) -> None:
        self.lc["implemented_at"] = at or time.strftime("%Y-%m-%dT%H:%M:%S")

    def set_experiment(self, experiment_id: str) -> None:
        self.lc["experiment_id"] = experiment_id

    def set_outcome(self, outcome: str, lift: Optional[float] = None,
                    confidence: Optional[float] = None) -> None:
        if outcome not in ("won", "lost", "inconclusive"):
            raise ValueError(f"Invalid outcome: {outcome}")
        self.lc["outcome"] = outcome
        if lift is not None:
            self.lc["outcome_lift"] = lift
        if confidence is not None:
            self.lc["outcome_confidence"] = confidence


def upgrade_reco_file(file_path: pathlib.Path) -> dict:
    """Upgrade an existing recos_v13_final.json to add lifecycle dicts to
    recos that don't have one yet. Idempotent. Returns stats."""
    if not file_path.exists():
        return {"error": "not_found"}
    try:
        d = json.loads(file_path.read_text())
    except Exception as e:
        return {"error": f"parse:{e}"}

    n_added = 0
    n_existing = 0
    for r in d.get("recos", []):
        if "lifecycle" not in r:
            # Backfill : if reco is _superseded_by, mark as archived
            if r.get("_superseded_by"):
                lc = init_lifecycle(by="legacy_v23B_dedup", note=f"superseded_by:{r['_superseded_by']}")
                lc["status"] = "archived"
                lc["history"].append({
                    "status": "archived", "at": lc["history"][0]["at"],
                    "by": "legacy_v23B_dedup", "note": "superseded_by_dedup",
                })
            elif r.get("_skipped"):
                lc = init_lifecycle(by="legacy_skip", note=r.get("_skipped_reason"))
                lc["status"] = "archived"
                lc["history"].append({
                    "status": "archived", "at": lc["history"][0]["at"],
                    "by": "legacy_skip", "note": r.get("_skipped_reason", "skipped"),
                })
            else:
                lc = init_lifecycle(by="legacy_v25_upgrade")
            r["lifecycle"] = lc
            n_added += 1
        else:
            n_existing += 1

    if n_added > 0:
        tmp = file_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        tmp.replace(file_path)

    return {"added": n_added, "existing": n_existing, "total": len(d.get("recos", []))}


# ────────────────────────────────────────────────────────────────
# CLI : upgrade fleet entière
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--upgrade-all", action="store_true",
                    help="Add lifecycle dict to all existing recos_v13_final.json files")
    ap.add_argument("--client", help="Single client")
    ap.add_argument("--page", help="Single page (requires --client)")
    args = ap.parse_args()

    ROOT = pathlib.Path(__file__).resolve().parents[3]
    CAPTURES = ROOT / "data" / "captures"

    if args.upgrade_all:
        n_files = 0
        n_added_total = 0
        n_existing_total = 0
        for client_dir in sorted(CAPTURES.iterdir()):
            if not client_dir.is_dir() or client_dir.name.startswith("_") or client_dir.name.startswith("."):
                continue
            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir() or page_dir.name.startswith("_"):
                    continue
                f = page_dir / "recos_v13_final.json"
                if f.exists():
                    res = upgrade_reco_file(f)
                    if "error" not in res:
                        n_files += 1
                        n_added_total += res["added"]
                        n_existing_total += res["existing"]
        print(f"✓ Upgraded {n_files} reco files")
        print(f"  Added lifecycle : {n_added_total}")
        print(f"  Existing : {n_existing_total}")

    elif args.client and args.page:
        f = CAPTURES / args.client / args.page / "recos_v13_final.json"
        res = upgrade_reco_file(f)
        print(f"  {args.client}/{args.page}: {res}")
    else:
        # Demo
        reco = {"criterion_id": "hero_01", "before": "...", "after": "..."}
        rl = RecoLifecycle(reco)
        print(f"Initial status: {rl.status()}")
        rl.transition("reviewed", by="mathis", note="OK")
        rl.transition("accepted", by="mathis")
        rl.set_ticket("https://linear.app/growth/issue/GS-1234")
        rl.transition("ticket_created", by="mathis")
        print(f"Final status: {rl.status()}")
        print(f"History: {len(reco['lifecycle']['history'])} steps")
        print(json.dumps(reco["lifecycle"], indent=2, ensure_ascii=False))
