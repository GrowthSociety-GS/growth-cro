"""V26.X.2 — Detect canonical tunnel par client.

Problème (Mathis) : pour beaucoup de clients, lp_leadgen + lp_sales + quiz_vsl
capturent le MÊME tunnel sous des labels différents → recos dupliquées,
UX confuse, gaspillage budget.

Solution : détecter le tunnel canonique d'un client (le plus long / unique),
et marquer les autres LPs comme "convergent vers ce tunnel".

Heuristique :
1. Pour chaque client, lister les pages avec flow_summary.json
2. Pour chaque flow, extraire URL signatures des steps
3. Trouver le flow le plus long (= canonical) → étiqueter comme `canonical_tunnel`
4. Pour les autres flows : si leurs steps 2+ matchent steps du canonical → marquer
   `merges_into: <canonical_page>` + `merge_step: N` (à partir de quel step ils
   convergent)
5. Le step 1 de chaque LP reste audited pour la LP elle-même (l'entrée)

Output : data/captures/<client>/canonical_tunnel.json

Usage :
    python3 skills/site-capture/scripts/detect_canonical_tunnel.py --client japhy
    python3 skills/site-capture/scripts/detect_canonical_tunnel.py --all
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "captures"

FUNNEL_TYPES = {"quiz_vsl", "lp_sales", "lp_leadgen", "signup", "lead_gen_simple"}


def _norm_url(u: str) -> str:
    if not u:
        return ""
    p = urlparse(u)
    host = p.netloc.lower().replace("www.", "")
    path = p.path.rstrip("/").lower()
    # Strip query for tunnel comparison (often has step indices)
    return f"{host}{path}"


def detect_for_client(client: str) -> dict | None:
    cd = DATA / client
    if not cd.exists():
        return None

    flows = {}  # page → list of step URLs (normalized)
    raw_flows = {}  # page → flow_summary.json
    for pd in sorted(cd.iterdir()):
        if not pd.is_dir() or pd.name.startswith("_"):
            continue
        if pd.name not in FUNNEL_TYPES:
            continue
        fs = pd / "flow" / "flow_summary.json"
        if not fs.exists():
            continue
        try:
            d = json.loads(fs.read_text())
            steps = d.get("steps") or []
            if not steps:
                continue
            urls = [_norm_url(s.get("url") or "") for s in steps]
            flows[pd.name] = urls
            raw_flows[pd.name] = d
        except Exception:
            continue

    if not flows:
        return None

    # Step 1 : choose canonical = flow with most steps
    canonical = max(flows.keys(), key=lambda k: len(flows[k]))
    canonical_urls = set(flows[canonical])  # set of unique step URLs in canonical
    canonical_seq = flows[canonical]

    result = {
        "client": client,
        "canonical_tunnel": canonical,
        "canonical_n_steps": len(canonical_seq),
        "canonical_url_start": canonical_seq[0] if canonical_seq else None,
        "merges": {},  # page → {merge_step, n_lp_steps, n_tunnel_steps}
    }

    # Step 2 : for each non-canonical flow, detect merge point
    for page, urls in flows.items():
        if page == canonical:
            continue
        merge_step = None  # 1-indexed step where this flow merges into canonical
        for i, u in enumerate(urls, 1):
            if u and u in canonical_urls:
                merge_step = i
                break
        if merge_step:
            result["merges"][page] = {
                "merge_step": merge_step,
                "n_lp_steps": merge_step - 1,  # steps avant fusion = LP propre
                "n_tunnel_steps_shared": len(urls) - merge_step + 1,
                "first_canonical_url": urls[merge_step - 1] if merge_step <= len(urls) else None,
            }
        else:
            # No merge → flow indépendant (legitimate own funnel)
            result["merges"][page] = {"merge_step": None, "n_lp_steps": len(urls), "independent": True}

    return result


def write_canonical(client: str, result: dict) -> None:
    out = DATA / client / "canonical_tunnel.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        n_with_tunnel = 0
        n_with_merge = 0
        for cd in sorted(DATA.iterdir()):
            if not cd.is_dir() or cd.name.startswith(("_", ".")):
                continue
            r = detect_for_client(cd.name)
            if not r:
                continue
            write_canonical(cd.name, r)
            n_with_tunnel += 1
            n_merges = sum(1 for m in r["merges"].values() if m.get("merge_step"))
            n_indep = sum(1 for m in r["merges"].values() if m.get("independent"))
            if n_merges > 0:
                n_with_merge += 1
                print(f"  ✓ {cd.name}: canonical={r['canonical_tunnel']} ({r['canonical_n_steps']} steps) · merges={n_merges} · indep={n_indep}")
            else:
                print(f"  · {cd.name}: canonical={r['canonical_tunnel']} ({r['canonical_n_steps']} steps) · all indep")
        print(f"\n✓ {n_with_tunnel} clients analysés, {n_with_merge} avec ≥1 merge cross-page")
        return

    if not args.client:
        ap.error("--client OR --all required")
    r = detect_for_client(args.client)
    if not r:
        print(f"❌ {args.client}: aucun flow trouvé")
        sys.exit(1)
    write_canonical(args.client, r)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
