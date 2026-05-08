#!/usr/bin/env python3
"""
pick_diverse_pages.py — sélection équitable de N pages pour batch reco ciblé.

Objectif : minimiser le coût d'un batch --force en gardant la diversité
(business_type × pageType × variété de clients). Pondère par représentativité
des segments et tire des pages distinctes (pas 3 pages du même client avant
d'explorer un autre client).

Usage :
  python3 pick_diverse_pages.py --n 50 [--out pages.txt]
  python3 pick_diverse_pages.py --n 50 --biz ecommerce,saas,lead_gen
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
from collections import defaultdict
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"
CLIENTS_DB = ROOT / "data" / "clients_database.json"


def load_client_biz_map() -> dict[str, str]:
    if not CLIENTS_DB.exists():
        return {}
    db = json.loads(CLIENTS_DB.read_text())
    clients = db.get("clients") if isinstance(db, dict) else db
    if isinstance(clients, list):
        return {
            c.get("id"): (c.get("identity") or {}).get("businessType") or c.get("business_type") or "unknown"
            for c in clients
            if c.get("id")
        }
    if isinstance(clients, dict):
        return {
            cid: (c.get("identity") or {}).get("businessType") or c.get("business_type") or "unknown"
            for cid, c in clients.items()
        }
    return {}


def collect_candidates(client_biz: dict[str, str]) -> dict[tuple[str, str], list[str]]:
    """Retourne {(biz, pageType): [client/pageType, ...]} où prompts + intent existent."""
    segments: dict[tuple[str, str], list[str]] = defaultdict(list)
    for pf in sorted(CAPTURES.glob("*/*/recos_v13_prompts.json")):
        page_dir = pf.parent
        client_dir = page_dir.parent
        intent_path = client_dir / "client_intent.json"
        if not intent_path.exists():
            continue
        biz = client_biz.get(client_dir.name, "unknown")
        segments[(biz, page_dir.name)].append(f"{client_dir.name}/{page_dir.name}")
    return segments


# Priorités par segment — prop. à l'importance business × couverture doctrine
# Plus le poids est haut, plus de pages sont sélectionnées.
SEGMENT_WEIGHTS = {
    ("ecommerce", "home"): 4,
    ("ecommerce", "pdp"): 4,
    ("ecommerce", "collection"): 3,
    ("ecommerce", "pricing"): 2,
    ("ecommerce", "quiz_vsl"): 2,
    ("ecommerce", "blog"): 1,
    ("saas", "home"): 4,
    ("saas", "pricing"): 4,
    ("saas", "lp_leadgen"): 2,
    ("saas", "pdp"): 2,
    ("saas", "blog"): 2,
    ("lead_gen", "home"): 3,
    ("lead_gen", "pricing"): 2,
    ("lead_gen", "blog"): 2,
    ("lead_gen", "quiz_vsl"): 2,
    ("fintech", "home"): 2,
    ("fintech", "pricing"): 2,
    ("fintech", "lp_sales"): 1,
    ("app", "home"): 2,
    ("app", "pricing"): 2,
    ("app", "pdp"): 1,
    ("insurtech", "home"): 1,
}


# Clients "canoniques" à inclure en priorité (connus, data de qualité)
PRIORITY_CLIENTS = {
    "japhy", "alan", "sezane", "doctolib", "stripe", "notion", "qonto",
    "wise", "welcome_to_the_jungle", "revolut", "spendesk", "pennylane",
    "treatwell", "payfit", "manomano", "blablacar", "backmarket",
    "epycure", "big_moustache", "typology", "tediber", "asphalte",
}


def pick(segments: dict[tuple[str, str], list[str]], n: int, seed: int = 42) -> list[str]:
    """Retourne une liste de `client/page` diversifiée de taille ≤ n.

    Heuristique :
      1. Score par segment : SEGMENT_WEIGHTS × log(1 + taille_segment)
      2. Alloue par proportion du score total.
      3. Dans chaque segment, priorise PRIORITY_CLIENTS puis random.
      4. Caps global : max 2 pages/client sauf si segment sous-peuplé.
    """
    rng = random.Random(seed)
    import math

    # 1. Score segments
    scored: list[tuple[float, tuple[str, str], list[str]]] = []
    for seg_key, pages in segments.items():
        w = SEGMENT_WEIGHTS.get(seg_key, 0)
        if w == 0:
            continue  # segment hors priorité
        score = w * math.log(1 + len(pages))
        scored.append((score, seg_key, pages))

    total_score = sum(s for s, _, _ in scored)
    if total_score <= 0:
        return []

    # 2. Alloc par proportion (arrondi, min 1 si segment présent)
    alloc: dict[tuple[str, str], int] = {}
    for s, seg_key, _ in scored:
        alloc[seg_key] = max(1, round(n * s / total_score))

    # Ajuste pour coller à n
    while sum(alloc.values()) > n:
        # Retire 1 au segment avec le plus haut count
        k_max = max(alloc, key=lambda k: alloc[k])
        if alloc[k_max] <= 1:
            break
        alloc[k_max] -= 1
    while sum(alloc.values()) < n:
        k_min = min(alloc, key=lambda k: alloc[k] / max(1, SEGMENT_WEIGHTS.get(k, 1)))
        alloc[k_min] += 1

    # 3. Tire pages par segment
    selected: list[str] = []
    client_count: dict[str, int] = defaultdict(int)
    for seg_key, pages in segments.items():
        if seg_key not in alloc:
            continue
        k = alloc[seg_key]
        # Split priority clients vs rest
        prio = [p for p in pages if p.split("/")[0] in PRIORITY_CLIENTS]
        rest = [p for p in pages if p.split("/")[0] not in PRIORITY_CLIENTS]
        rng.shuffle(prio)
        rng.shuffle(rest)
        pool = prio + rest
        picked = 0
        for p in pool:
            if picked >= k:
                break
            client = p.split("/")[0]
            if client_count[client] >= 2:  # max 2 per client
                continue
            selected.append(p)
            client_count[client] += 1
            picked += 1
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--out", default=None)
    ap.add_argument("--biz", help="Filter biz types (comma separated)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    client_biz = load_client_biz_map()
    all_segments = collect_candidates(client_biz)

    if args.biz:
        wanted = set(args.biz.split(","))
        all_segments = {k: v for k, v in all_segments.items() if k[0] in wanted}

    selected = pick(all_segments, args.n, seed=args.seed)

    print(f"=== {len(selected)} pages sélectionnées ===")
    by_biz_pt = defaultdict(int)
    by_client = defaultdict(int)
    for p in selected:
        client, pt = p.split("/")
        biz = client_biz.get(client, "unknown")
        by_biz_pt[(biz, pt)] += 1
        by_client[client] += 1
    print("\nPar segment :")
    for (biz, pt), n in sorted(by_biz_pt.items()):
        print(f"  {biz:<12} × {pt:<12} : {n}")
    print(f"\nClients distincts : {len(by_client)}")

    if args.out:
        pathlib.Path(args.out).write_text("\n".join(selected) + "\n")
        print(f"\n✓ Écrit dans {args.out}")
    else:
        print("\n--- pages list ---")
        for p in selected:
            print(p)


if __name__ == "__main__":
    main()
