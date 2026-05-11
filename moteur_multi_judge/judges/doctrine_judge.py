"""Doctrine Judge V26.AA — juge unifié sur les 54 critères V3.2 (racine partagée).

Réponse à l'insight Mathis 2026-05-03 : la doctrine V3.2 doit être consommée par
TOUS les juges (audit + GSG + multi-judge), pas par 3 grilles parallèles inventées.

Remplace l'ancien `eval_grid /135` (gsg_self_audit Defender + Skeptic) par le
playbook racine. 54 critères + 6 killer_rules — la doctrine accumulée sur 6 mois
d'audit CRO, validée sur 105+ clients.

Logique :
  - Charge les 54 critères via scripts/doctrine.py (Sprint 1 V26.AA)
  - Filtre par page_type (ex: hero_04 N/A pour lp_listicle, applicable pour pdp)
  - Group par pilier (hero/persuasion/ux/coherence/psycho/tech/utility)
  - 1 call Sonnet par pilier (parallélisé via ThreadPoolExecutor → ~30s wall vs ~3min séquentiel)
  - Aggregate : total = somme scores, total_max = somme weights des critères applicables
  - Killer rules : si critère.killer = True ET score = 0 → cap automatique 50% du max
  - Output structure compatible orchestrator multi-judge

Coût attendu : ~$0.10-0.20 par audit (7 calls × ~$0.02 chacun, parallélisés).

Usage CLI :
    python3 moteur_multi_judge/judges/doctrine_judge.py \\
        --html deliverables/weglot-listicle-MINIMAL.html \\
        --client weglot --page-type lp_listicle

Usage module :
    from moteur_multi_judge.judges.doctrine_judge import audit_lp_doctrine
    result = audit_lp_doctrine(html, client="weglot", page_type="lp_listicle")
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import sys
import time

# Make scripts/doctrine.py importable
_THIS = pathlib.Path(__file__).resolve()
ROOT = _THIS.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from doctrine import (  # noqa: E402
    load_all_criteria,
    _criterion_applies_to_page_type,
    criterion_to_audit_prompt,
    get_criterion,
)

SONNET_MODEL = "claude-sonnet-4-5-20250929"

PILLARS = ["hero", "persuasion", "ux", "coherence", "psycho", "tech", "utility"]


def strip_html(html: str, max_chars: int = 20000) -> str:
    no_style = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    no_script = re.sub(r"<script.*?</script>", "", no_style, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", no_script)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


SYSTEM_PROMPT_TEMPLATE = """Tu es un **expert CRO senior** (15+ ans audit landing pages). Tu juges une LP contre la **doctrine V3.2 GrowthCRO** — 54 critères accumulés sur 6 mois d'audit, validés sur 105+ clients.

## RÈGLE D'OR

Tu juges chaque critère selon son barème ternaire (TOP / OK / CRITICAL) et tu donnes le score ENTIER correspondant :
- **TOP** = `weight` (ex: 3 si max=3) — la LP rivalise avec Linear/Stripe/Cursor sur ce critère
- **OK** = `weight/2` (ex: 1.5 si max=3) — présent mais générique, ou 50% des conditions du TOP
- **CRITICAL** = `0` — absent, faux, ou explicitement contraire au critère

Posture : **DUR, ANCRÉ DANS LE FACTUEL, EVIDENCE-BASED.**
- Donne TOP UNIQUEMENT si tu peux citer un extrait HTML précis qui le prouve
- Si un critère ne s'applique pas vraiment au page_type courant, donne `verdict: "N/A"` et `score: null`
- Sois sévère mais juste : pas de complaisance, pas de procès d'intention

## PILIER À NOTER : {pillar} ({n_criteria} critères)

{criteria_block}

## DELIVERY

Tu DOIS appeler l'outil `submit_pillar_audit` avec le pillar `{pillar}` et la liste des criteria scorés dans l'ORDRE indiqué ci-dessus. N'écris pas de texte hors de l'appel d'outil."""


# Anthropic tools schema — force structured output (élimine les JSON parse failures
# qu'on avait en parsant du raw text quand Sonnet met des guillemets non-échappés
# dans rationale ou evidence).
TOOL_SUBMIT_AUDIT = {
    "name": "submit_pillar_audit",
    "description": "Submit the doctrine V3.2 ternary audit for the requested pillar. Use this tool exclusively — no free-form text response.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pillar": {
                "type": "string",
                "description": "Pillar name (hero, persuasion, ux, coherence, psycho, tech, utility)",
            },
            "criteria": {
                "type": "array",
                "description": "One entry per criterion of the pillar, in the order listed in the system prompt.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "criterion_id (e.g. hero_01)"},
                        "score": {
                            "type": ["number", "null"],
                            "description": "weight (TOP), weight/2 (OK), 0 (CRITICAL), or null if N/A",
                        },
                        "verdict": {
                            "type": "string",
                            "enum": ["TOP", "OK", "CRITICAL", "N/A"],
                        },
                        "evidence": {
                            "type": "string",
                            "description": "HTML extract or factual observation, ≤200 chars",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "2-3 sentences explaining the score and what's missing to reach the next tier",
                        },
                    },
                    "required": ["id", "score", "verdict", "evidence", "rationale"],
                },
            },
        },
        "required": ["pillar", "criteria"],
    },
}


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json\n"):
            text = text[5:]
        elif text.startswith("json"):
            text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _criteria_for_pillar(pillar: str, page_type: str) -> list[dict]:
    """Critères du pilier applicables au page_type."""
    all_crit = load_all_criteria()
    return [
        c for c in all_crit.values()
        if c.get("pillar") == pillar and _criterion_applies_to_page_type(c, page_type)
    ]


def _build_pillar_system_prompt(pillar: str, criteria: list[dict]) -> str:
    blocks = [criterion_to_audit_prompt(c["id"]) for c in criteria]
    return SYSTEM_PROMPT_TEMPLATE.format(
        pillar=pillar,
        n_criteria=len(criteria),
        criteria_block="\n".join(blocks),
    )


def _judge_pillar(
    pillar: str,
    criteria: list[dict],
    html: str,
    brand_dna: dict,
    page_type: str,
    client: str,
    model: str,
    verbose: bool = True,
) -> dict:
    """Score 1 pilier (1 call Sonnet)."""
    if not criteria:
        return {"pillar": pillar, "criteria": [], "_tokens_in": 0, "_tokens_out": 0}

    text = strip_html(html, max_chars=18000)

    user_msg = f"""## PAGE TYPE
{page_type}

## CLIENT
{client}

## BRAND DNA RÉFÉRENCE (extrait pour évaluer cohérence brand)
{json.dumps(brand_dna, ensure_ascii=False, indent=2)[:2000]}

## LP À JUGER

### HTML structure (head + first 3K chars pour évaluer crit visuels/tech)
```html
{html[:3000]}
```

### COPY texte uniquement (max 18K chars pour évaluer crit textuels)
{text}

Score chaque critère du pilier {pillar} ci-dessus selon la doctrine V3.2 ternaire."""

    system_prompt = _build_pillar_system_prompt(pillar, criteria)

    import anthropic
    api = anthropic.Anthropic()

    if verbose:
        n = len(criteria)
        sz = len(user_msg) + len(system_prompt)
        print(f"  → Sonnet doctrine_judge pillar={pillar} ({n} crit, prompt={sz} chars)...", flush=True)

    t0 = time.time()
    msg = api.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.1,
        system=system_prompt,
        tools=[TOOL_SUBMIT_AUDIT],
        tool_choice={"type": "tool", "name": "submit_pillar_audit"},
        messages=[{"role": "user", "content": user_msg}],
    )
    dt = time.time() - t0

    if verbose:
        print(f"  ← {pillar}: in={msg.usage.input_tokens} out={msg.usage.output_tokens} ({dt:.1f}s)", flush=True)

    # tool_choice forces a tool_use block — extract its already-parsed input dict.
    result = None
    for block in msg.content:
        block_type = getattr(block, "type", None)
        if block_type == "tool_use":
            result = block.input
            break
    if result is None:
        raw_blocks = [getattr(b, "type", "?") for b in msg.content]
        raise ValueError(
            f"No tool_use block in Sonnet response (pillar={pillar}, blocks={raw_blocks})"
        )

    result["_tokens_in"] = msg.usage.input_tokens
    result["_tokens_out"] = msg.usage.output_tokens
    return result


def _check_killer_rules(pillar_results: list[dict]) -> tuple[bool, list[dict]]:
    """Détecte les critères flaggés killer=true qui ont CRITICAL/score=0."""
    all_crit = load_all_criteria()
    violations = []
    for r in pillar_results:
        for c in r.get("criteria", []):
            cid = c.get("id")
            crit = all_crit.get(cid)
            if not crit:
                continue
            if not crit.get("killer"):
                continue
            score = c.get("score")
            verdict = c.get("verdict")
            # Killer condition: score 0 OR verdict CRITICAL (et non N/A)
            if verdict == "CRITICAL" or (score == 0 and verdict != "N/A"):
                violations.append({
                    "id": cid,
                    "label": crit.get("label"),
                    "killer_reason": crit.get("killerReason"),
                    "evidence": c.get("evidence"),
                    "rationale": c.get("rationale"),
                })
    return (len(violations) > 0, violations)


def _compute_tier(pct: float) -> str:
    if pct >= 85: return "Exceptionnel"
    if pct >= 75: return "Excellent"
    if pct >= 65: return "Bon"
    return "Insuffisant"


def audit_lp_doctrine(
    html: str,
    client: str,
    page_type: str = "lp_listicle",
    model: str = SONNET_MODEL,
    verbose: bool = True,
    parallel: bool = True,
) -> dict:
    """Score une LP HTML sur les 54 critères V3.2 (filtrés par page_type).

    Returns:
        Audit dict avec totals, killer_rules_violated, pillars summary, details.
    """
    # Brand DNA
    brand_dna_fp = ROOT / "data" / "captures" / client / "brand_dna.json"
    brand_dna = json.loads(brand_dna_fp.read_text()) if brand_dna_fp.exists() else {}

    # Build per-pillar tasks (only pillars with applicable criteria)
    tasks = []
    for pillar in PILLARS:
        criteria = _criteria_for_pillar(pillar, page_type)
        if criteria:
            tasks.append((pillar, criteria))

    if verbose:
        n_total = sum(len(c) for _, c in tasks)
        print(f"\n══ Doctrine Judge V26.AA — {client} / {page_type} ══")
        print(f"  Pillars: {len(tasks)} | Criteria applicable: {n_total}")

    pillar_results: list[dict] = []
    t0 = time.time()
    if parallel and len(tasks) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futures = {
                ex.submit(_judge_pillar, p, c, html, brand_dna, page_type, client, model, verbose): p
                for p, c in tasks
            }
            for fut in concurrent.futures.as_completed(futures):
                pillar_results.append(fut.result())
    else:
        for p, c in tasks:
            pillar_results.append(_judge_pillar(p, c, html, brand_dna, page_type, client, model, verbose))
    dt = time.time() - t0

    if verbose:
        print(f"  ✓ All pillars judged ({dt:.1f}s wall)")

    # Sort pillar_results by canonical PILLARS order for deterministic output
    pillar_results.sort(key=lambda r: PILLARS.index(r["pillar"]) if r["pillar"] in PILLARS else 99)

    # Aggregate
    total = 0.0
    total_max = 0.0
    n_top = n_ok = n_critical = n_na = 0
    for r in pillar_results:
        for c in r.get("criteria", []):
            verdict = c.get("verdict")
            score = c.get("score")
            crit = get_criterion(c.get("id"))
            if verdict == "N/A" or score is None or not crit:
                n_na += 1
                continue
            total += float(score)
            total_max += float(crit.get("weight", 3))
            if verdict == "TOP": n_top += 1
            elif verdict == "OK": n_ok += 1
            elif verdict == "CRITICAL": n_critical += 1

    raw_total = total

    # Killer rules detection → cap automatique 50% du max
    killer_triggered, killer_violations = _check_killer_rules(pillar_results)
    cap_note = None
    if killer_triggered:
        cap_value = total_max * 0.5
        if total > cap_value:
            cap_note = f"Cap killer rule appliqué : {raw_total:.1f} → {cap_value:.1f} (50% du max — {len(killer_violations)} killer{'s' if len(killer_violations)>1 else ''} violé{'s' if len(killer_violations)>1 else ''})"
            total = cap_value

    pct = (total / total_max * 100) if total_max > 0 else 0
    tier = _compute_tier(pct)

    # Per-pillar summary
    pillars_summary = {}
    for r in pillar_results:
        p_total = 0.0
        p_max = 0.0
        for c in r.get("criteria", []):
            if c.get("verdict") == "N/A" or c.get("score") is None:
                continue
            p_total += float(c.get("score", 0))
            crit = get_criterion(c.get("id"))
            if crit:
                p_max += float(crit.get("weight", 3))
        pillars_summary[r["pillar"]] = {
            "total": round(p_total, 1),
            "max": round(p_max, 1),
            "pct": round((p_total / p_max * 100) if p_max > 0 else 0, 1),
            "n_criteria": len(r.get("criteria", [])),
        }

    audit = {
        "client": client,
        "page_type": page_type,
        "audit_version": "V26.AA.doctrine",
        "persona": "doctrine",
        "totals": {
            "doctrine_score": round(total, 1),
            "doctrine_max": round(total_max, 1),
            "doctrine_score_raw": round(raw_total, 1),
            "total": round(total, 1),
            "total_max": round(total_max, 1),
            "total_pct": round(pct, 1),
            "tier": tier,
            "n_top": n_top,
            "n_ok": n_ok,
            "n_critical": n_critical,
            "n_na": n_na,
        },
        "killer_rules_violated": killer_triggered,
        "killer_violations": killer_violations,
        "cap_note": cap_note,
        "pillars": pillars_summary,
        "details": pillar_results,
        "model_used": model,
        "tokens_in": sum(r.get("_tokens_in", 0) for r in pillar_results),
        "tokens_out": sum(r.get("_tokens_out", 0) for r in pillar_results),
        "wall_seconds": round(dt, 1),
    }
    return audit


def print_doctrine_summary(audit: dict, label: str = "DOCTRINE V3.2") -> None:
    t = audit.get("totals", {})
    pillars = audit.get("pillars", {})
    print(f"\n══ {label} {audit.get('client', '?').upper()} (page_type={audit.get('page_type', '?')}) ══")
    print(f"  Persona       : {audit.get('persona', '?')}")
    print(f"  TOTAL         : {t.get('total', '?')}/{t.get('total_max', '?')} ({t.get('total_pct', '?')}%) — {t.get('tier', '?')}")
    print(f"  Verdicts      : 🟢 {t.get('n_top', '?')} TOP / 🟡 {t.get('n_ok', '?')} OK / 🔴 {t.get('n_critical', '?')} CRITICAL / ⚪ {t.get('n_na', '?')} N/A")
    print(f"  Tokens        : in={audit.get('tokens_in', '?')} out={audit.get('tokens_out', '?')} ({audit.get('wall_seconds', '?')}s wall)")

    if audit.get("killer_rules_violated"):
        print(f"\n  ⛔ KILLER RULES VIOLATED ({len(audit.get('killer_violations', []))}) :")
        for v in audit.get("killer_violations", []):
            print(f"     - {v.get('id')} : {v.get('label')}")
        if audit.get("cap_note"):
            print(f"     {audit.get('cap_note')}")

    print(f"\n  Per pillar :")
    for p in PILLARS:
        if p not in pillars:
            continue
        s = pillars[p]
        sym = "🟢" if s.get("pct", 0) >= 75 else ("🟡" if s.get("pct", 0) >= 65 else "🔴")
        print(f"    {sym} {p:12s} {s.get('total', '?'):>5}/{s.get('max', '?'):<5} ({s.get('pct', '?'):>5}%) — {s.get('n_criteria', '?')} crit")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True, help="Path to LP HTML file")
    ap.add_argument("--client", required=True, help="Client slug (must match data/captures/<client>/brand_dna.json)")
    ap.add_argument("--page-type", default="lp_listicle", help="Page type (lp_listicle, home, pdp, lp_sales, ...)")
    ap.add_argument("--output", help="Path to save audit JSON (default: data/_audit_<client>_doctrine.json)")
    ap.add_argument("--no-parallel", action="store_true", help="Disable per-pillar parallelism")
    ap.add_argument("--model", default=SONNET_MODEL)
    args = ap.parse_args()

    html_fp = pathlib.Path(args.html)
    if not html_fp.exists():
        sys.exit(f"❌ {html_fp} not found")
    html = html_fp.read_text()

    audit = audit_lp_doctrine(
        html, args.client, args.page_type,
        model=args.model,
        parallel=not args.no_parallel,
    )

    out_fp = pathlib.Path(args.output or (ROOT / "data" / f"_audit_{args.client}_doctrine.json"))
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(json.dumps(audit, ensure_ascii=False, indent=2))

    print_doctrine_summary(audit)
    print(f"\n  Audit saved : {out_fp.relative_to(ROOT) if out_fp.is_relative_to(ROOT) else out_fp}")


if __name__ == "__main__":
    main()
