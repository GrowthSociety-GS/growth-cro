"""V26.X.5 — Audit per-step tunnel.

Problème (Mathis) : on audite seulement la step 0 (la LP d'entrée), pas
les autres steps du tunnel. Donc Japhy quiz_vsl 13 vraies étapes UX, mais
recos seulement sur l'étape 1.

Solution : pour chaque compressed_step, prompt Haiku/Vision avec :
- screenshot du step
- step_label
- vision_action (ce que l'utilisateur fait à cette étape)
- dom_widgets_count (signaux : payment, listbox, calendar, etc.)
- step_position (1/N)
- canonical_tunnel context (le client + la nature du quiz)

Output : 2-4 recos PAR STEP, focalisées sur les frictions spécifiques
(longueur form, friction cognitive, manque de progress bar, etc.)

Storage : data/captures/<client>/<page>/flow/step_recos.json
{
  "client": ..., "page": ...,
  "step_recos": {
    "step_1": [reco, reco, ...],
    "step_2": [reco, reco, ...],
    ...
  }
}

Usage :
    python3 skills/site-capture/scripts/audit_funnel_steps.py --client japhy --page quiz_vsl
    python3 skills/site-capture/scripts/audit_funnel_steps.py --all-funnels
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import pathlib
import sys
import time

import anthropic

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "captures"

MODEL = "claude-haiku-4-5-20251001"
PROMPT_VERSION = "V26.X.5"


def build_step_prompt(client: str, page: str, step_idx: int, total_steps: int,
                      step_label: str, primary_pattern: str, sub_actions: list,
                      dom_widgets: dict, business_type: str = "unknown") -> str:
    """Construit le prompt LLM pour auditer 1 compressed_step de funnel."""
    sub_summary = []
    for sa in sub_actions[:5]:
        target = sa.get('target', '')
        val = sa.get('value', '')
        sub_summary.append(f"  - {sa.get('pattern','?')}: {target}{f' = {val}' if val else ''}")

    signals = []
    if dom_widgets.get('payment_signals'): signals.append("💳 paiement détecté")
    if dom_widgets.get('iframe_payment'): signals.append("iframe Stripe/Paypal")
    if dom_widgets.get('listbox_present'): signals.append("listbox")
    if dom_widgets.get('calendar_present'): signals.append("calendrier")
    if dom_widgets.get('checkboxes_unchecked', 0) > 0:
        signals.append(f"{dom_widgets['checkboxes_unchecked']} cgv non-cochées")
    if dom_widgets.get('inputs', 0) > 0: signals.append(f"{dom_widgets['inputs']} inputs")
    if dom_widgets.get('buttons', 0) > 0: signals.append(f"{dom_widgets['buttons']} boutons")

    return f"""Tu es un expert CRO (Conversion Rate Optimization) qui audite UNE ÉTAPE PRÉCISE d'un tunnel/quiz.

CLIENT : {client}
PAGE D'ENTRÉE : {page} (business: {business_type})
ÉTAPE : {step_idx}/{total_steps}
LABEL : "{step_label}"
PATTERN : {primary_pattern}

ACTIONS UTILISATEUR à cette étape :
{chr(10).join(sub_summary) if sub_summary else '  (aucune)'}

WIDGETS DOM détectés :
  {' · '.join(signals) if signals else 'aucun signal particulier'}

(Le screenshot de l'étape est joint en image.)

DOCTRINE step-level :
- friction_form : ≤3 champs par step idéal, >5 = -11%/champ excédentaire
- progress_visible : barre progrès cruciale après step 2 (sweet spot 4-8 quiz)
- cognitive_load : 1 décision par step, ≥4 options = paralysis
- micro_reassurance : preuve/badge à chaque step pour maintenir engagement
- step_label_clarté : label step doit clarifier l'étape (pas "Page 3" mais "Choisis ta race")
- visual_hierarchy : CTA primaire 1 seul, options 2-4 max, espace fluid
- sticky_value_reminder : rappel bénéfice global toutes les 3-4 steps

CONSIGNES :
1. Identifie 2-4 PROBLÈMES spécifiques à CETTE étape (pas la LP, pas le tunnel global).
2. Sois CONCRET et FACTUEL : utilise le screenshot.
3. SI cette étape semble OK (pas de friction visible), retourne 0-1 reco max.
4. PAS de doublons avec les recos de la LP (étape 0).

Tu produis STRICTEMENT un JSON avec cette structure :
{{
  "step_idx": {step_idx},
  "step_label": "{step_label}",
  "recos": [
    {{
      "headline": "<6-12 mots, angle problématique spécifique step. Ex: 'Pas de progress bar visible step 5/13'>",
      "criterion_step": "<friction_form|progress_visible|cognitive_load|micro_reassurance|step_label_clarté|visual_hierarchy|sticky_value_reminder>",
      "before": "<observation factuelle de cette étape, ce qui pose problème>",
      "after": "<proposition concrète, code ou copy>",
      "why": "<2 phrases max : raison psycho/cognitive>",
      "priority": "P0|P1|P2|P3",
      "expected_lift_pct": <float 1-15>,
      "effort_hours": <int 1-40>,
      "ice_score": <int 0-200>
    }}
  ]
}}

Si AUCUN problème : `"recos": []`. Pas de fallback bullshit. Jamais de markdown, JSON only."""


async def call_llm_for_step(api, client_str, page, step, total, business_type, screenshot_path):
    """Appelle Haiku Vision pour auditer 1 step."""
    sa = step.get('sub_actions') or []
    img_data = None
    if screenshot_path and screenshot_path.exists():
        try:
            img_data = base64.standard_b64encode(screenshot_path.read_bytes()).decode("utf-8")
        except Exception:
            pass

    prompt = build_step_prompt(
        client=client_str, page=page,
        step_idx=step.get('step', 0), total_steps=total,
        step_label=step.get('step_label', ''),
        primary_pattern=step.get('primary_pattern', '?'),
        sub_actions=sa, dom_widgets=step.get('dom_widgets_count') or {},
        business_type=business_type,
    )

    content = []
    if img_data:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": img_data},
        })
    content.append({"type": "text", "text": prompt})

    try:
        msg = await api.messages.create(
            model=MODEL, max_tokens=1500, temperature=0.3,
            messages=[{"role": "user", "content": content}],
        )
        raw = msg.content[0].text.strip()
        # Strip ```json fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json\n")
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        result = json.loads(raw)
        return result, msg.usage.input_tokens, msg.usage.output_tokens
    except Exception as e:
        return {"step_idx": step.get('step'), "step_label": step.get('step_label'), "recos": [], "error": str(e)[:200]}, 0, 0


async def audit_one_funnel(client_str: str, page: str, business_type: str = "unknown") -> dict:
    flow_fp = DATA / client_str / page / "flow" / "flow_summary.json"
    if not flow_fp.exists():
        return {"client": client_str, "page": page, "error": "no_flow_summary"}

    d = json.loads(flow_fp.read_text())
    compressed = d.get("compressed_steps") or []
    if not compressed:
        return {"client": client_str, "page": page, "error": "no_compressed_steps"}

    api = anthropic.AsyncAnthropic()
    flow_dir = flow_fp.parent
    total = len(compressed)
    sem = asyncio.Semaphore(5)
    total_in = 0
    total_out = 0

    async def run_step(step):
        async with sem:
            ss_path = flow_dir / (step.get('screenshot_first') or f"step_{step.get('step',1):02d}.png")
            return await call_llm_for_step(api, client_str, page, step, total, business_type, ss_path)

    results = await asyncio.gather(*[run_step(s) for s in compressed])
    step_recos = {}
    for (res, ti, to) in results:
        total_in += ti; total_out += to
        sk = f"step_{res.get('step_idx', '?')}"
        step_recos[sk] = res

    out = {
        "client": client_str, "page": page,
        "model": MODEL, "version": PROMPT_VERSION,
        "n_steps_audited": total,
        "tokens": {"input": total_in, "output": total_out},
        "step_recos": step_recos,
    }
    out_fp = flow_dir / "step_recos.json"
    out_fp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return out


async def main_async(args):
    if args.all_funnels:
        # Trouve tous les flows funnel-type
        targets = []
        for fp in sorted(DATA.glob("*/*/flow/flow_summary.json")):
            if "_obsolete" in str(fp): continue
            client = fp.parent.parent.parent.name
            page = fp.parent.parent.name
            d = json.loads(fp.read_text())
            if d.get("compressed_steps"):
                targets.append((client, page))
        print(f"→ {len(targets)} funnels à auditer per-step")
        for c, p in targets:
            t0 = time.time()
            res = await audit_one_funnel(c, p)
            el = time.time() - t0
            n_recos = sum(len((v.get('recos') or [])) for v in (res.get('step_recos') or {}).values())
            print(f"  ✓ {c}/{p}: {res.get('n_steps_audited', 0)} steps · {n_recos} recos · {el:.0f}s")
    else:
        if not args.client or not args.page:
            print("❌ --client + --page OR --all-funnels", file=sys.stderr)
            sys.exit(1)
        res = await audit_one_funnel(args.client, args.page, args.business_type or "unknown")
        n_recos = sum(len((v.get('recos') or [])) for v in (res.get('step_recos') or {}).values())
        print(f"✓ {args.client}/{args.page}: {res.get('n_steps_audited', 0)} steps · {n_recos} recos")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--business-type", default="unknown")
    ap.add_argument("--all-funnels", action="store_true")
    args = ap.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        # Try to load from .env
        env_fp = ROOT / ".env"
        if env_fp.exists():
            for line in env_fp.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"')
                    break
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
