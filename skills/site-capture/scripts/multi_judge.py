"""V26.D Multi-judge — disagreement tracking entre Haiku, règles déterministes, Sonnet.

Réponse à la critique ChatGPT Hardcore Audit (§5.3 "Danger du one model judge") :
"Haiku intervient dans trop de rôles. Tu crées un biais de juge unique.
L'architecture cible doit mesurer les désaccords entre modèles et règles.
Quand Vision dit 'social proof présent', DOM dit 'introuvable', scorer dit
'faible', Sonnet dit 'contexte luxe' → ces conflits doivent devenir signaux
de review humain ou arbitrage."

Approche ciblée (pas Sonnet partout — coût) :
1. Haiku score le critère normalement (déjà fait dans score_*.py)
2. Règles déterministes scorent en parallèle (existing logic)
3. Calcul agreement_score (0-1) entre Haiku et règles
4. Si agreement < threshold (default 0.5) → trigger Sonnet review (arbitrage)
5. Logger tout désaccord dans data/captures/<client>/<page>/disagreement_log.json

Économie : ~80% des critères sont en accord → Sonnet appelé seulement sur
les ~20% problématiques. Coût : ~$0.50 par run fleet (vs ~$5 si Sonnet
systématique).

Pour Learning Layer V28 :
- Track win rate par disagreement type
- Identifier patterns "Haiku se trompe systématiquement sur X" → ajuster prompt
- Identifier patterns "règles trop strictes sur Y" → ajuster doctrine

Storage : data/captures/<client>/<page>/disagreement_log.json
{
  "version": "v26.D.1.0",
  "client": "kaiju",
  "page": "home",
  "judges_used": ["haiku", "rules", "sonnet_arbitrage"],
  "disagreements": [
    {
      "criterion_id": "hero_01",
      "judges": {
        "haiku": {"score": 12, "max": 18, "reason": "H1 clair, social proof visible"},
        "rules": {"score": 6, "max": 18, "reason": "killer_rule fired: missing primary_cta"},
        "sonnet": {"score": 10, "max": 18, "reason": "contexte luxe, CTA secondaire OK"}
      },
      "agreement_score": 0.33,
      "winner": "sonnet",  // judge final picked
      "logged_at": "2026-04-29T20:15:00",
      "evidence_ids": ["ev_kaiju_home_hero_01_001", "ev_kaiju_home_hero_01_002"]
    }
  ]
}
"""
from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any, Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

DEFAULT_AGREEMENT_THRESHOLD = 0.5  # below this → trigger Sonnet arbitrage


def _normalize_score(score: float, max_score: float) -> float:
    """Returns 0-1 normalized."""
    return max(0.0, min(1.0, score / max_score)) if max_score > 0 else 0.0


def compute_agreement(judges: dict[str, dict]) -> float:
    """Compute agreement score (0-1) between N judges.
    Each judge dict has {score, max}. Returns 1 - mean_pairwise_distance."""
    norms = []
    for j_name, j_data in judges.items():
        if j_data.get("score") is None or j_data.get("max") is None:
            continue
        norms.append(_normalize_score(j_data["score"], j_data["max"]))
    if len(norms) < 2:
        return 1.0
    # Compute mean pairwise distance
    n_pairs = 0
    total_dist = 0.0
    for i in range(len(norms)):
        for j in range(i + 1, len(norms)):
            total_dist += abs(norms[i] - norms[j])
            n_pairs += 1
    mean_dist = total_dist / n_pairs if n_pairs > 0 else 0.0
    return round(1.0 - mean_dist, 3)


def needs_arbitrage(judges: dict[str, dict],
                    threshold: float = DEFAULT_AGREEMENT_THRESHOLD) -> bool:
    """True if disagreement is severe enough to trigger Sonnet."""
    return compute_agreement(judges) < threshold


SONNET_ARBITRAGE_SYSTEM = """Tu es un juge senior CRO. Deux juges (Haiku + règles déterministes) sont en désaccord sur un critère d'audit.

Tu reçois :
- criterion_id + label
- les 2 scores avec leurs justifications
- le contexte business (vertical, intent, persona, USP)
- les éléments réels (Vision : h1, cta, hero, social proof | DOM : computed signals)

Ton rôle : trancher avec une justification ancrée dans le contexte et les éléments réels.
Tu peux donner raison à l'un, à l'autre, ou proposer un score intermédiaire.

Output JSON STRICT :
{
  "score": <int 0-max>,
  "max": <int>,
  "winner": "haiku|rules|own_judgment",
  "reason": "<phrase courte ancrée>",
  "evidence_priority": "<vision|dom|hybrid>"
}"""


def call_sonnet_arbitrage(client_api, criterion_id: str, criterion_label: str,
                          haiku_judgment: dict, rules_judgment: dict,
                          context: dict, evidence_summary: str) -> Optional[dict]:
    """Call Sonnet to arbitrate. Returns its judgment dict, or None on failure."""
    user_msg = f"""## Critère en désaccord
- ID : {criterion_id}
- Label : {criterion_label}
- Max score : {haiku_judgment.get('max', '?')}

## Juge Haiku
- Score : {haiku_judgment.get('score')}/{haiku_judgment.get('max')}
- Reason : {haiku_judgment.get('reason', '(aucune)')[:300]}

## Juge Règles déterministes
- Score : {rules_judgment.get('score')}/{rules_judgment.get('max')}
- Reason : {rules_judgment.get('reason', '(aucune)')[:300]}

## Contexte business
- Vertical : {context.get('business_category', '?')}
- Intent : {context.get('primary_intent', '?')}
- Persona : {context.get('persona', '?')}
- USP : {context.get('usp_signals', [])}

## Évidence réelle
{evidence_summary[:1500]}

Tranche."""
    try:
        resp = client_api.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            temperature=0,
            system=SONNET_ARBITRAGE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text if resp.content else ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.lstrip("`")
            if text.startswith("json\n"): text = text[5:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            m = re.search(r"\{[\s\S]*\}", text)
            return json.loads(m.group(0)) if m else None
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


def log_disagreement(client: str, page: str, criterion_id: str,
                     judges: dict[str, dict], winner: str,
                     evidence_ids: list[str] | None = None) -> None:
    """Append a disagreement record to data/captures/<client>/<page>/disagreement_log.json."""
    log_path = CAPTURES / client / page / "disagreement_log.json"
    log = {"version": "v26.D.1.0", "client": client, "page": page, "disagreements": []}
    if log_path.exists():
        try:
            log = json.loads(log_path.read_text())
        except Exception:
            pass
    agreement = compute_agreement(judges)
    log.setdefault("disagreements", []).append({
        "criterion_id": criterion_id,
        "judges": judges,
        "agreement_score": agreement,
        "winner": winner,
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "evidence_ids": evidence_ids or [],
    })
    log["judges_used"] = sorted(set(log.get("judges_used", [])) | set(judges.keys()))
    log["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    tmp = log_path.with_suffix(".json.tmp")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=2))
    tmp.replace(log_path)


# ────────────────────────────────────────────────────────────────
# Demo
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Demo : 2 juges en désaccord
    judges = {
        "haiku": {"score": 14, "max": 18, "reason": "H1 clair, social proof visible"},
        "rules": {"score": 6, "max": 18, "reason": "killer_rule: missing primary_cta"},
    }
    agreement = compute_agreement(judges)
    print(f"Agreement score: {agreement}")
    print(f"Needs arbitrage: {needs_arbitrage(judges)}")
    if needs_arbitrage(judges):
        print(f"  → trigger Sonnet arbitrage")
    log_disagreement("kaiju", "home", "hero_01", judges, winner="rules",
                     evidence_ids=["ev_kaiju_home_hero_01_001"])
    print("✓ Logged to data/captures/kaiju/home/disagreement_log.json")
