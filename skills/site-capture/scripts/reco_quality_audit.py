#!/usr/bin/env python3
"""
reco_quality_audit.py — Scan des recos_v13_final.json existants et quality score
par reco. Permet de n'appliquer `--force` qu'aux recos sous un seuil, pour
minimiser le coût de re-enrichissement.

Score composé (0-10) :
  - grounding (0-3)   : client_name + H1 cité + CTA cité (utilise grounding_hints du prompts.json)
  - length (0-2)      : before+after+why > 400 chars (proxy densité info)
  - specificity (0-3) : verbatims, chiffres, CTA exact, URL relatif cité
  - non-generic (0-2) : pas de marqueurs vagues ("envisager", "optimiser", "améliorer" sans précision)

Usage :
  python3 reco_quality_audit.py                             # audit full fleet
  python3 reco_quality_audit.py --threshold 7               # flag recos score < 7
  python3 reco_quality_audit.py --threshold 7 --out to_redo.txt
  python3 reco_quality_audit.py --client japhy --verbose
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from collections import Counter, defaultdict
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

# Marqueurs génériques — leur présence = pénalité
GENERIC_PATTERNS = [
    r"\benvisag(er|ez)\b",
    r"\boptimis(er|ez)\b\s+(?:votre|le|la|les)?\s*(?!\w{4,})",  # "optimisez" sans objet
    r"\baméliore?r?\b\s*(?!de|l[ae]|les|vos)",
    r"\bil (?:serait|faudrait) (?:bien|préférable|judicieux)",
    r"\bpensez à\b",
    r"\bau global\b",
    r"\bde manière général",
    r"\ben règle général",
    r"\bune piste serait de\b",
    r"\bpourrait être\b",
]
_GENERIC_RE = re.compile("|".join(GENERIC_PATTERNS), re.I)

# Marqueurs de spécificité concrète
_VERBATIM_RE = re.compile(r'["«»"]([^"«»"]{6,100})["«»"]')  # citations
_PERCENT_RE = re.compile(r"\b\d{1,3}\s*%|\b[+-]\d+\s*%")
_PIXEL_RE = re.compile(r"\b\d{2,4}\s*(px|pixel)\b", re.I)
_URL_REL_RE = re.compile(r'/[a-z0-9\-_/]+(?:\.html|\?|\b)', re.I)
_CTA_QUOTE_RE = re.compile(r'«\s*([^»]{3,40})\s*»|"([^"]{3,40})"')


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _compact(s: str) -> str:
    return re.sub(r"[\W_]+", "", _norm(s))


def _client_name_matches(raw_name: str, haystack: str) -> bool:
    name = _norm(raw_name)
    if len(name) < 3:
        return False
    variants = {
        name,
        name.replace("_", " "),
        name.replace("-", " "),
    }
    compact_haystack = _compact(haystack)
    return any(v in haystack or _compact(v) in compact_haystack for v in variants if len(v) >= 3)


def _field(reco: dict, key: str) -> str:
    """Return a reco field as text; API outputs may contain nulls."""
    v = reco.get(key)
    return v if isinstance(v, str) else ""


def _reco_text(reco: dict) -> str:
    return " ".join([_field(reco, "before"), _field(reco, "after"), _field(reco, "why")])


def score_grounding(reco: dict, hints: dict) -> tuple[int, list[str]]:
    """Reproduit la logique de check_grounding() mais post-hoc."""
    issues = []
    if not hints:
        return 0, ["no_hints"]

    haystack = _norm(_reco_text(reco))

    score = 0
    client_name = hints.get("client_name") or ""
    if _client_name_matches(client_name, haystack):
        score += 1
    else:
        issues.append("client_name_missing")

    h1 = _norm(hints.get("h1_text") or "")
    sub = _norm(hints.get("subtitle_text") or "")
    if (len(h1) >= 8 and h1[: min(40, len(h1))] in haystack) or (
        len(sub) >= 8 and sub[: min(40, len(sub))] in haystack
    ):
        score += 1
    elif h1 or sub:
        issues.append("real_copy_not_cited")

    cta = _norm(hints.get("primary_cta_text") or "")
    if len(cta) >= 8 and cta in haystack:
        score += 1
    elif len(cta) < 8:
        score += 1  # bonus si pas de CTA à citer
    else:
        issues.append("cta_not_cited")

    return score, issues


def score_length(reco: dict) -> int:
    total = len(_field(reco, "before")) + len(_field(reco, "after")) + len(_field(reco, "why"))
    if total >= 600:
        return 2
    if total >= 400:
        return 1
    return 0


def score_specificity(reco: dict) -> tuple[int, list[str]]:
    """Détecte verbatims, chiffres, CTA exact, URL dans la reco."""
    issues = []
    text = _reco_text(reco)
    score = 0
    n_verbatim = len(_VERBATIM_RE.findall(text))
    if n_verbatim >= 2:
        score += 1
    n_pct = len(_PERCENT_RE.findall(text))
    n_px = len(_PIXEL_RE.findall(text))
    if n_pct + n_px >= 1:
        score += 1
    n_url = len(_URL_REL_RE.findall(text))
    n_cta = len(_CTA_QUOTE_RE.findall(text))
    if n_url + n_cta >= 1:
        score += 1
    if score == 0:
        issues.append("no_concrete_specifics")
    return score, issues


def score_non_generic(reco: dict) -> tuple[int, list[str]]:
    issues = []
    text = _reco_text(reco)
    matches = [m.group(0) for m in _GENERIC_RE.finditer(text)]
    n_generic = len(matches)
    if n_generic == 0:
        return 2, []
    if n_generic == 1:
        return 1, [f"1 generic marker: {matches[0]!r}"]
    issues.append(f"{n_generic} generic markers: {matches[:3]!r}")
    return 0, issues


def quality_score(reco: dict, hints: dict | None = None) -> dict:
    """Retourne {score, breakdown, issues}. Score global = 0-10."""
    gs, gi = score_grounding(reco, hints or {})
    ls = score_length(reco)
    ss, si = score_specificity(reco)
    ng, ngi = score_non_generic(reco)

    total = gs + ls + ss + ng
    is_fallback = reco.get("_fallback", False)
    is_skipped = reco.get("_skipped", False)
    if is_fallback:
        total = 0
    if is_skipped:
        total = 0

    return {
        "score": total,
        "max": 10,
        "breakdown": {
            "grounding": gs,
            "length": ls,
            "specificity": ss,
            "non_generic": ng,
        },
        "issues": gi + si + ngi + (["is_fallback"] if is_fallback else []) + (["is_skipped"] if is_skipped else []),
    }


def audit_page(page_dir: pathlib.Path) -> dict | None:
    """Audit un page_dir, retourne stats ou None si pas de data."""
    final = page_dir / "recos_v13_final.json"
    prompts = page_dir / "recos_v13_prompts.json"
    if not final.exists():
        return None

    try:
        final_data = json.loads(final.read_text())
    except Exception:
        return None

    # hints by criterion_id depuis prompts_data
    hints_by_crit = {}
    active_criteria = set()
    if prompts.exists():
        try:
            pdata = json.loads(prompts.read_text())
            for p in pdata.get("prompts", []):
                cid = p.get("criterion_id")
                if cid and not p.get("skipped"):
                    active_criteria.add(cid)
                    hints_by_crit[cid] = p.get("grounding_hints") or {}
        except Exception:
            pass

    recos_all = final_data.get("recos") or []
    recos = [
        r for r in recos_all
        if not r.get("_skipped")
        and not r.get("_superseded_by")
        and (not active_criteria or r.get("criterion_id") in active_criteria)
    ]
    scores = []
    weak_recos = []
    for r in recos:
        crit = r.get("criterion_id")
        hints = hints_by_crit.get(crit)
        qs = quality_score(r, hints)
        scores.append(qs["score"])
        if qs["score"] < 7:
            weak_recos.append({
                "criterion_id": crit,
                "score": qs["score"],
                "breakdown": qs["breakdown"],
                "issues": qs["issues"],
            })

    return {
        "n_recos": len(recos),
        "n_recos_total": len(recos_all),
        "n_excluded": len(recos_all) - len(recos),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "distribution": Counter(scores),
        "weak_count": len(weak_recos),
        "weak_recos": weak_recos[:10],  # sample
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="Filter un client")
    ap.add_argument("--threshold", type=int, default=7, help="Score min pour flag weak (default 7)")
    ap.add_argument("--out", help="Fichier de sortie client/page pour pages avec weak recos (à re-batch)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    by_score = Counter()
    total_weak_pages = []
    total_recos = 0
    total_weak_recos = 0
    avg_scores = []

    pattern = f"{args.client}/*" if args.client else "*/*"
    for final in sorted(CAPTURES.glob(f"{pattern}/recos_v13_final.json")):
        page_dir = final.parent
        client = page_dir.parent.name
        page_type = page_dir.name
        res = audit_page(page_dir)
        if not res:
            continue
        total_recos += res["n_recos"]
        total_weak_recos += res["weak_count"]
        avg_scores.append(res["avg_score"])
        for s, n in res["distribution"].items():
            by_score[s] += n
        if res["weak_count"] > 0 and res["avg_score"] < args.threshold:
            total_weak_pages.append((client, page_type, res["avg_score"], res["weak_count"]))
        if args.verbose:
            print(f"  {client}/{page_type}: avg={res['avg_score']:.1f}, weak={res['weak_count']}/{res['n_recos']}")
            if res["weak_recos"]:
                for w in res["weak_recos"][:3]:
                    print(f"    - {w['criterion_id']:8} score={w['score']} issues={w['issues'][:2]}")

    print(f"\n=== QUALITY AUDIT SUMMARY ===")
    print(f"Total recos audited : {total_recos}")
    print(f"Avg fleet score     : {round(sum(avg_scores) / len(avg_scores), 2) if avg_scores else 0}/10")
    print(f"Distribution par score :")
    for s in range(11):
        n = by_score.get(s, 0)
        bar = "█" * max(1, n // 20) if n else ""
        print(f"  {s:>2}/10 : {n:>5} {bar}")
    print(f"\nRecos faibles (<{args.threshold}) : {total_weak_recos}/{total_recos} ({100*total_weak_recos/max(1,total_recos):.1f}%)")
    print(f"Pages avec avg<{args.threshold} : {len(total_weak_pages)}")

    if args.out:
        # Output pages to re-run
        lines = [f"{c}/{p}" for c, p, _, _ in sorted(total_weak_pages)]
        pathlib.Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"\n✓ {len(lines)} pages à re-batch écrites dans {args.out}")


if __name__ == "__main__":
    main()
