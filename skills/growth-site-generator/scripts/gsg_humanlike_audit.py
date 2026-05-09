"""GSG Human-Like Audit V26.Z W1.b — juge en solo sur les 8 dimensions humaines.

Réponse à la découverte du test multi-judge initial : le skeptic mono-grille
(eval_grid 135 pts) s'aligne sur le defender parce que la GRILLE elle-même
est complaisante. Cette grille mesure des présence/absence (headline OK,
social proof présent, anti-slop bool×8) que Weglot iter8 satisfait tous —
mais elle ne mesure PAS ce que les humains experts pénalisent (concrétude
H2, densité narrative, originalité non-IA, signature visuelle nommable).

Ce script reprend les 8 dimensions du gsg_compare_audit.py (qui donnait 46/80
sur Weglot iter8) mais en mode SOLO : pas besoin d'une LP référence. Le juge
note chaque dimension 0-10 contre les standards "top 0.001% du marché".

Les 8 dimensions humaines :
1. Concrétude des H2 (images sensorielles, ton conversationnel)
2. Densité narrative (mots qui racontent vs liste features)
3. Activation Cialdini × 6 (autorité/preuve/rareté/sympathie/engagement/réciprocité)
4. Activation biais cognitifs (ancrage, loss aversion, IKEA, etc.)
5. Frameworks copy orchestrés (PAS intro / BAB section / FAQ)
6. Polish visuel anti-AI-slop "réel" (pas juste pattern présent, mais qualité)
7. Brand DNA respect "réel" (cohérence émotionnelle, pas juste couleurs)
8. Conversion architecture (séquence orchestrée, hook → tension → résolution → CTA)

Output : JSON sur la même structure que gsg_self_audit pour intégration
gsg_multi_judge :
  - persona = "humanlike"
  - totals.total / totals.total_max = sum(/80)
  - scores reformatés en blocks compatibles agreement computation

Usage CLI :
    python3 skills/growth-site-generator/scripts/gsg_humanlike_audit.py \\
        --html deliverables/weglot-listicle-V26Y-AURA.html \\
        --client weglot

Usage module :
    from gsg_humanlike_audit import audit_lp_humanlike
    result = audit_lp_humanlike(html_text, client="weglot")
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SONNET_MODEL = "claude-sonnet-4-5-20250929"


def strip_html(html: str, max_chars: int = 30000) -> str:
    """Garde le texte lisible, vire styles/scripts/tags."""
    no_style = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL)
    no_script = re.sub(r'<script.*?</script>', '', no_style, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', no_script)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


HUMANLIKE_PROMPT = """Tu es un **directeur créatif senior** (15+ ans, agences top-tier type Pentagram, Wieden+Kennedy, R/GA). Tu juges une landing page en 30 secondes — comme tu le ferais en review client. Ton job : trancher.

## RÈGLE D'OR

Tu ne juges PAS contre une checklist mécanique de présence/absence. Tu juges contre les **standards top 0.001% du marché actuel**. Tu donnes 10/10 UNIQUEMENT si cette page rivalise avec Linear, Stripe, Aesop, Glossier, Ramp dans leur catégorie respective. Sinon, tu es lucide et tu pénalises.

Posture : **DUR, HONNÊTE, ANCRÉ DANS L'EXEMPLE CONCRET.**
- 10/10 : indiscutablement excellent, je l'enverrais à mes pairs comme exemple
- 8-9/10 : très bon, cohérent, distinctive, mais une dimension manque pour être référence
- 6-7/10 : pro et fonctionnel, mais pattern "AI default" reconnaissable, manque d'âme
- 4-5/10 : surface polie mais creuse en fond, pas de point de vue tranché
- 1-3/10 : générique, template-like, déjà-vu mille fois

## LES 8 DIMENSIONS À NOTER (chacune 0-10)

### 1. Concrétude des H2 (images sensorielles, anti-paraphrase)
Excellent : H2 portent une image mentale précise, ton conversationnel, on visualise instantanément le bénéfice.
Médiocre : H2 abstraits, paraphrasent le H1, ou pure liste de features ("Réduisez les coûts", "Améliorez la performance").

### 2. Densité narrative (storytelling vs liste mécanique)
Excellent : le texte raconte une histoire ou installe une tension dramatique. On lit pour la suite.
Médiocre : succession de bullet points sans connexion, ton "feature dump", aucune curiosité créée.

### 3. Activation Cialdini × 6 (réellement présents, pas juste mentionnés)
Vérifier objectivement quels principes sont DÉPLOYÉS dans la page : autorité (logos clients tier-1, certif), preuve sociale (chiffres précis, témoignages), rareté (limite réelle), sympathie (humain visible), engagement (micro-commitment), réciprocité (don avant ask).
Excellent : 5-6 principes activés visiblement avec assets concrets.
Médiocre : 0-2 principes (souvent juste "logos clients" sans rien d'autre).

### 4. Activation biais cognitifs (ancrage, loss aversion, IKEA, dotation)
Excellent : 2-3 biais activés explicitement (ex: ancrage prix barré, FOMO daté, peur de la perte chiffrée).
Médiocre : zéro biais visible, juste des arguments rationnels.

### 5. Frameworks copy orchestrés (PAS / BAB / PASTOR / AIDA)
Excellent : un framework reconnaissable est ORCHESTRÉ dans la séquence (pas juste mentionné). Ex: PAS = problème nommé → agitation → solution.
Médiocre : structure plate, sections juxtaposées sans dynamique psycho.

### 6. Polish visuel anti-AI-slop "réel"
Excellent : signature visuelle nommable en 3-5 mots ("Editorial Press SaaS", "Brutalist Tech Warm"). Détails artisanaux. Distinctive.
Médiocre : techniques accumulées (mesh + grain + glass + drop caps...) mais sans thèse — "AI showcase mode". Reconnaissable comme généré par LLM.

### 7. Brand DNA respect "réel" (au-delà des couleurs)
Excellent : la voix, le rythme, les choix d'imagerie respectent la marque. La page POURRAIT être de cette marque sans logo.
Médiocre : couleurs OK, typo OK, mais ton générique, pas reconnaissable comme la marque.

### 8. Conversion architecture (séquence orchestrée hook → tension → résolution → CTA)
Excellent : architecture émotionnelle claire, chaque section sert le suivant, le CTA arrive au bon moment psychologique.
Médiocre : sections empilées sans flow, CTA n'importe où, pas d'arc narratif.

## OUTPUT JSON STRICT (rien d'autre)

{{
  "client": "{client}",
  "audit_version": "V26.Z.humanlike",
  "persona": "humanlike",
  "scores": {{
    "humanlike": {{
      "category_concretude_h2":         [{{"id": 1, "name": "Concrétude des H2",            "score": <0-10>, "rationale": "..."}}],
      "category_densite_narrative":     [{{"id": 2, "name": "Densité narrative",            "score": <0-10>, "rationale": "..."}}],
      "category_cialdini_activation":   [{{"id": 3, "name": "Cialdini × 6 activés",         "score": <0-10>, "rationale": "..."}}],
      "category_biais_cognitifs":       [{{"id": 4, "name": "Biais cognitifs activés",      "score": <0-10>, "rationale": "..."}}],
      "category_frameworks_copy":       [{{"id": 5, "name": "Frameworks copy orchestrés",   "score": <0-10>, "rationale": "..."}}],
      "category_polish_anti_ai_slop":   [{{"id": 6, "name": "Polish anti-AI-slop réel",     "score": <0-10>, "rationale": "..."}}],
      "category_brand_dna_respect":     [{{"id": 7, "name": "Brand DNA respect réel",       "score": <0-10>, "rationale": "..."}}],
      "category_conversion_architect":  [{{"id": 8, "name": "Conversion architecture",      "score": <0-10>, "rationale": "..."}}]
    }}
  }},
  "totals": {{
    "humanlike_score": <0-80>,
    "humanlike_max": 80,
    "total": <0-80>,
    "total_max": 80,
    "tier": "🏆 Top 0.001% ≥72 | ✅ Excellent 60-71 | ⚠️ Bon 45-59 | 🔴 Insuffisant <45"
  }},
  "signature_nommable": "<3-5 mots qui décrivent la signature visuelle, ou null si pas de signature distinctive>",
  "ai_default_patterns_detected": [
    "<liste des patterns IA reconnaissables présents : 'gradient mesh sans intention', 'parallel bullet lists', 'unlock/empower/seamless verbs', etc.>"
  ],
  "humanlike_strengths": [<3 forces réelles, formulation honnête>],
  "humanlike_weaknesses": [<3 faiblesses réelles, pas adoucies>],
  "verdict_paragraph": "<3-4 phrases du DA senior : qu'est-ce qui sort vraiment du lot, qu'est-ce qui sent l'IA, qu'est-ce qui empêche les 9-10/10>"
}}

JSON only, pas de markdown, sois sévère et précis. Si tu donnes des notes hautes (9-10), elles doivent être JUSTIFIÉES par des éléments AUDITABLES dans le HTML."""


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json\n"):
            text = text[5:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def audit_lp_humanlike(html: str, client: str, model: str = SONNET_MODEL,
                      verbose: bool = True) -> dict:
    """Évalue une LP HTML sur les 8 dimensions humaines (mode standalone, sans LP référence).

    Retourne un dict d'audit avec persona='humanlike' et structure compatible
    avec gsg_multi_judge.compute_agreement.
    """
    text = strip_html(html, max_chars=30000)
    brand_dna_fp = ROOT / "data" / "captures" / client / "brand_dna.json"
    brand_dna = json.loads(brand_dna_fp.read_text()) if brand_dna_fp.exists() else {}

    user_msg = f"""## BRAND DNA RÉFÉRENCE
{json.dumps(brand_dna, ensure_ascii=False, indent=2)[:2500]}

## LP À JUGER

### HTML structure (head + first lines)
```
{html[:3500]}
```

### COPY texte uniquement (max 30K chars)
{text}

Évalue cette LP solo contre les standards top 0.001% du marché actuel. Sois sévère."""

    system_prompt = HUMANLIKE_PROMPT.format(client=client)

    import anthropic
    client_api = anthropic.Anthropic()
    if verbose:
        print(f"  → Sonnet humanlike judge call (client={client}, prompt={len(user_msg)+len(system_prompt)} chars) ...", flush=True)
    msg = client_api.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.1,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = msg.content[0].text
    if verbose:
        print(f"  ← in={msg.usage.input_tokens} out={msg.usage.output_tokens}", flush=True)
    text_out = _strip_fences(raw)
    try:
        audit = json.loads(text_out)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text_out)
        if not m:
            raise ValueError(f"JSON parse failed. Raw first 500 chars: {text_out[:500]}")
        audit = json.loads(m.group(0))

    audit.setdefault("persona", "humanlike")
    audit.setdefault("model_used", model)
    audit.setdefault("tokens_in", msg.usage.input_tokens)
    audit.setdefault("tokens_out", msg.usage.output_tokens)
    return audit


def print_humanlike_summary(audit: dict, label: str = "HUMANLIKE") -> None:
    """Pretty-print du verdict humanlike."""
    t = audit.get("totals", {})
    print(f"\n══ {label} {audit.get('client','?').upper()} ══")
    print(f"  Persona : {audit.get('persona','?')}")
    print(f"  TOTAL   : {t.get('total','?')}/{t.get('total_max','?')} — {t.get('tier','?')}")

    print(f"\n  Per dimension (0-10) :")
    block = (audit.get("scores") or {}).get("humanlike", {})
    for cat_name, criteria in block.items():
        if criteria and isinstance(criteria, list):
            c = criteria[0]
            score = c.get("score", "?")
            sym = "🟢" if isinstance(score, (int, float)) and score >= 8 else (
                "🟡" if isinstance(score, (int, float)) and score >= 5 else "🔴")
            print(f"    {sym} {c.get('name','?'):35} {score}/10")

    sig = audit.get("signature_nommable")
    print(f"\n  Signature nommable : {sig if sig else '⚠️  AUCUNE — alarme'}")

    patterns = audit.get("ai_default_patterns_detected") or []
    if patterns:
        print(f"\n  Patterns IA détectés ({len(patterns)}) :")
        for p in patterns:
            print(f"    • {p}")

    print(f"\n  Strengths :")
    for s in audit.get("humanlike_strengths", []):
        print(f"    + {s}")

    print(f"\n  Weaknesses :")
    for w in audit.get("humanlike_weaknesses", []):
        print(f"    - {w}")

    print(f"\n  Verdict DA senior :")
    print(f"  {audit.get('verdict_paragraph', '?')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--client", required=True)
    ap.add_argument("--output", help="Path to save audit JSON (default: data/_audit_<client>_humanlike.json)")
    args = ap.parse_args()

    html_fp = pathlib.Path(args.html)
    if not html_fp.exists():
        sys.exit(f"❌ {html_fp} not found")
    html = html_fp.read_text()

    audit = audit_lp_humanlike(html, args.client)

    out_fp = pathlib.Path(args.output or (ROOT / "data" / f"_audit_{args.client}_humanlike.json"))
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(json.dumps(audit, ensure_ascii=False, indent=2))

    print_humanlike_summary(audit)
    print(f"\n  Audit saved: {out_fp.relative_to(ROOT) if out_fp.is_relative_to(ROOT) else out_fp}")


if __name__ == "__main__":
    main()
