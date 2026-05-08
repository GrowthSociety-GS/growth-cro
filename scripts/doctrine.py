"""GrowthCRO Doctrine Loader (V26.Z W4 — racine partagée Audit + GSG).

Réponse à la faille architecturale fondamentale identifiée par Mathis 2026-05-03 :
la doctrine V3.2 (54 critères + killer_rules + guardrails + thresholds) était
consommée UNIQUEMENT par l'Audit Engine. Le GSG inventait sa propre grille
(eval_grid.md /135) — duplication absurde + 3 systèmes de qualité parallèles
qui ne se parlaient pas.

Ce module expose la doctrine racine comme bibliothèque partagée :

  load_all_criteria()           → dict[criterion_id, criterion_dict] (54 critères)
  load_killer_rules()           → list[killer_rule_dict] (6 règles absolues)
  load_anti_patterns()          → list[anti_pattern_dict]
  load_thresholds()             → dict (seuils chiffrés cf bench)

  top_critical_for_page_type(page_type, n=7)
                                → list[criterion_id] : top N critères
                                  les plus importants pour CE page_type

  killer_rules_for_page_type(page_type)
                                → list[killer_rule_dict] applicables

  criterion_to_audit_prompt(criterion_id)
                                → str : bloc texte "comment scorer"
                                  (utilisé par score_<bloc>.py — déjà existant)

  criterion_to_gsg_principle(criterion_id)
                                → str : bloc texte "comment construire pour
                                  satisfaire ce critère" (NEW V26.Z W4 —
                                  c'est le pont audit→GSG)

USAGE
=====

GSG (génération brand+doctrine-aware, prompt court) :
    from doctrine import top_critical_for_page_type, killer_rules_for_page_type, criterion_to_gsg_principle

    page_type = "lp_listicle"
    top_crit = top_critical_for_page_type(page_type, n=7)
    principles = "\\n".join(criterion_to_gsg_principle(cid) for cid in top_crit)
    killers = killer_rules_for_page_type(page_type)
    # → injecte dans prompt court (pas mega-prompt)

Audit (déjà existant, inchangé) :
    Les score_<bloc>.py continuent de charger directement playbook/bloc_X_v3.json
    via leur GRID variable. Ce module les EXPOSE en bibliothèque pour que d'autres
    modules (GSG, multi-judge unifié, learning_layer) puissent consommer la même
    source.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAYBOOK = ROOT / "playbook"


# ─────────────────────────────────────────────────────────────────────────────
# Loaders bas-niveau
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_all_criteria() -> dict[str, dict]:
    """Charge les 54 critères V3.2 depuis playbook/bloc_*_v3.json + utility.

    Returns: dict[criterion_id, criterion_dict] où criterion_dict contient :
      id, label, pillar (hero|persuasion|ux|coherence|psycho|tech|utility),
      weight (= max), pageTypes (list ou "*"), businessCategories (list ou "*"),
      checkMethod (textual|visual|technical|hybrid), viewport_check,
      scoring (top/ok/critical), examples (top/ok/critical), killer (bool optionnel)
    """
    criteria: dict[str, dict] = {}
    for bloc_file in sorted(PLAYBOOK.glob("bloc_*_v3.json")):
        try:
            data = json.loads(bloc_file.read_text())
        except json.JSONDecodeError:
            continue
        # Resolve pillar from filename or content
        pillar_from_file = bloc_file.stem.split("_", 2)[-1].replace("_v3", "")
        # bloc_3_ux_v3 has 'bloc' key not 'pillar'
        pillar = data.get("pillar") or pillar_from_file
        for c in data.get("criteria", []):
            cid = c.get("id")
            if not cid:
                continue
            # Normalize structure (some files have 'weight', others 'max')
            c.setdefault("weight", c.get("max", 3))
            c.setdefault("pillar", pillar)
            c.setdefault("pageTypes", "*")
            c.setdefault("businessCategories", "*")
            criteria[cid] = c
    return criteria


@lru_cache(maxsize=1)
def load_killer_rules() -> list[dict]:
    """Charge les killer_rules (capping si violées)."""
    fp = PLAYBOOK / "killer_rules.json"
    if not fp.exists():
        return []
    data = json.loads(fp.read_text())
    rules = data.get("killer_rules") or []
    if isinstance(rules, dict):
        rules = list(rules.values())
    return rules


@lru_cache(maxsize=1)
def load_anti_patterns() -> list[dict]:
    """Charge les anti_patterns (patterns CRO/Design à interdire)."""
    fp = PLAYBOOK / "anti_patterns.json"
    if not fp.exists():
        return []
    data = json.loads(fp.read_text())
    return data.get("anti_patterns") or []


@lru_cache(maxsize=1)
def load_thresholds() -> dict:
    """Charge les seuils chiffrés (perf, hero, persuasion, ...)."""
    fp = PLAYBOOK / "thresholds_benchmarks.json"
    if not fp.exists():
        return {}
    return json.loads(fp.read_text())


@lru_cache(maxsize=1)
def load_page_type_config() -> dict:
    """Charge page_type_criteria.json — quels critères s'appliquent par page type."""
    fp = PLAYBOOK / "page_type_criteria.json"
    if not fp.exists():
        return {}
    return json.loads(fp.read_text())


@lru_cache(maxsize=1)
def load_guardrails() -> list[dict]:
    """Charge guardrails (règles transversales)."""
    fp = PLAYBOOK / "guardrails.json"
    if not fp.exists():
        return []
    data = json.loads(fp.read_text())
    return data.get("guardrails") or []


# ─────────────────────────────────────────────────────────────────────────────
# Filtrage par page_type (le pont audit→GSG)
# ─────────────────────────────────────────────────────────────────────────────

# Importance ranking par pillar : ordre décroissant des piliers les plus
# critiques pour la qualité d'une LP. Utilisé pour ordonner top_critical_for_page_type.
PILLAR_IMPORTANCE_DEFAULT = ["hero", "persuasion", "psycho", "ux", "coherence", "tech", "utility"]

# Variation par page_type : certains piliers comptent plus selon le type
PILLAR_IMPORTANCE_BY_PAGE_TYPE = {
    "lp_sales":    ["hero", "persuasion", "psycho", "ux", "coherence", "tech"],
    "lp_leadgen":  ["hero", "ux", "persuasion", "psycho", "coherence", "tech"],
    "lp_listicle": ["persuasion", "psycho", "hero", "coherence", "ux", "tech"],
    "listicle":    ["persuasion", "psycho", "hero", "coherence", "ux", "tech"],
    "advertorial": ["persuasion", "psycho", "hero", "coherence", "ux", "tech"],
    "pdp":         ["hero", "persuasion", "psycho", "ux", "tech", "coherence"],
    "home":        ["hero", "coherence", "ux", "persuasion", "psycho", "tech"],
    "pricing":     ["persuasion", "ux", "psycho", "hero", "coherence", "tech"],
    "quiz_vsl":    ["hero", "psycho", "ux", "persuasion", "coherence", "tech"],
}


# V3.2.1 (Sprint 2.5 V26.AA) : alias résolus avant le filtrage pour cohérence avec
# data/doctrine/applicability_matrix_v1.json.page_type_aliases. Permet à
# top_critical_for_page_type("lp_listicle") de matcher les critères avec
# pageTypes: ["listicle", ...].
PAGE_TYPE_ALIASES = {
    "lp_listicle": "listicle",
    "lp": "lp_leadgen",
    "signup": "lp_leadgen",
    "lead_gen_simple": "lp_leadgen",
}


def _resolve_page_type_alias(page_type: str) -> str:
    return PAGE_TYPE_ALIASES.get(page_type, page_type)


def _criterion_applies_to_page_type(criterion: dict, page_type: str) -> bool:
    """Vérifie si un critère s'applique à ce page_type.

    V3.2.1 : résout les alias avant le matching (ex: lp_listicle → listicle).
    """
    page_types = criterion.get("pageTypes", "*")
    if page_types == "*" or "*" in page_types:
        return True
    resolved = _resolve_page_type_alias(page_type)
    if isinstance(page_types, str):
        return page_types == page_type or page_types == resolved
    return page_type in page_types or resolved in page_types


def _criterion_priority_score(criterion: dict, pillar_order: list[str]) -> tuple[int, int]:
    """Score de priorité d'un critère pour ordering : (rang_pillar, -weight).

    Plus petit = plus prioritaire. Un critère du pillar prioritaire avec weight=3
    est devant un critère du pillar 2 avec weight=3.
    """
    pillar = criterion.get("pillar", "tech")
    pillar_rank = pillar_order.index(pillar) if pillar in pillar_order else len(pillar_order)
    weight = criterion.get("weight", 3) or 3
    is_killer = 1 if criterion.get("killer") else 0
    # Killer first, then pillar rank, then higher weight = more critical
    return (-is_killer, pillar_rank, -weight)


def top_critical_for_page_type(page_type: str, n: int = 7) -> list[str]:
    """Retourne les top N criterion_ids les plus critiques pour un page_type.

    Ordre :
      1. killer_rules (toujours en tête — règles absolues à ne jamais violer)
      2. critères du pillar le plus important pour ce page_type, weight élevé
      3. critères du pillar 2, etc.

    Args:
      page_type: ex "lp_listicle", "home", "pdp", "lp_sales"...
      n: nombre de critères à retourner (default 7 pour un prompt court)

    Returns: list[criterion_id] ordonnée par criticité décroissante.
    """
    all_crit = load_all_criteria()
    pillar_order = PILLAR_IMPORTANCE_BY_PAGE_TYPE.get(
        page_type, PILLAR_IMPORTANCE_DEFAULT
    )
    applicable = [
        (cid, c) for cid, c in all_crit.items()
        if _criterion_applies_to_page_type(c, page_type)
    ]
    applicable.sort(key=lambda kv: _criterion_priority_score(kv[1], pillar_order))
    return [cid for cid, _ in applicable[:n]]


def killer_rules_for_page_type(page_type: str) -> list[dict]:
    """Retourne les killer_rules applicables au page_type.

    Returns: list de killer_rule_dict avec id, name, rule, cap_score, etc.
    """
    rules = load_killer_rules()
    # Pour l'instant les killer rules sont universelles (pageType-agnostic
    # dans la doctrine V3.2). On retourne tout. Future : filtrer par
    # rule.applicable_page_types si ajouté à la doctrine.
    return rules


def get_criterion(criterion_id: str) -> Optional[dict]:
    """Retourne le dict d'un critère par son id."""
    return load_all_criteria().get(criterion_id)


# ─────────────────────────────────────────────────────────────────────────────
# Renderers : critère → bloc prompt
# ─────────────────────────────────────────────────────────────────────────────

def criterion_to_audit_prompt(criterion_id: str) -> str:
    """Format un critère en bloc texte pour SCORER une page existante.

    Utilisé par les juges (defender, skeptic, multi-judge unifié) pour évaluer
    une LP générée contre la doctrine V3.2.

    Format :
      ## <criterion_id> — <label> (max <weight> pts)
      [scoring]
      Top (3) : <description>
      OK (1.5) : <description>
      Critical (0) : <description>
    """
    c = get_criterion(criterion_id)
    if not c:
        return f"## {criterion_id} — UNKNOWN\n"
    s = c.get("scoring", {})
    weight = c.get("weight", 3)
    block = f"## {criterion_id} — {c.get('label', '?')} (max {weight} pts)\n"
    if c.get("killer"):
        cond = c.get("killerCondition", "")
        block += f"⛔ KILLER : {cond}\n"
    block += f"  Top ({weight}) : {s.get('top', '?')[:300]}\n"
    block += f"  OK ({weight/2}) : {s.get('ok', '?')[:200]}\n"
    block += f"  Critical (0) : {s.get('critical', '?')[:200]}\n"
    return block


def criterion_to_gsg_principle(criterion_id: str) -> str:
    """Format un critère en bloc texte CONSTRUCTIF pour GUIDER la création
    d'une page nouvelle qui respecte ce critère dès le départ.

    C'est le pont audit→GSG : même critère, usage inverse.
    Au lieu de "voici comment scorer", on dit "voici ce qu'il FAUT faire pour
    que ce critère soit naturellement satisfait".

    Format :
      ## <criterion_id> — <label>
      Principe constructif : <reformulation positive du "top">
      À éviter : <reformulation positive du "critical">
      [si killer] Règle absolue : <killer rule>
    """
    c = get_criterion(criterion_id)
    if not c:
        return f"## {criterion_id} — UNKNOWN\n"
    s = c.get("scoring", {})
    label = c.get("label", "?")
    top = (s.get("top") or "")[:280]
    critical = (s.get("critical") or "")[:200]
    block = f"## {criterion_id} — {label}\n"
    block += f"  → Faire : {top}\n"
    block += f"  → Éviter : {critical}\n"
    if c.get("killer"):
        cond = c.get("killerCondition", "")
        block += f"  ⛔ ABSOLUTE : {cond}\n"
    return block


def render_killer_rules_block(page_type: str) -> str:
    """Format les killer rules applicables en bloc texte court."""
    rules = killer_rules_for_page_type(page_type)
    if not rules:
        return ""
    block = "## ⛔ KILLER RULES — règles absolues, ne JAMAIS violer\n"
    for r in rules:
        rid = r.get("id", "?")
        rule = (r.get("rule") or "")[:200]
        criterion = r.get("criterion", "")
        block += f"  - **{rid}** ({criterion}) : {rule}\n"
    return block


def render_doctrine_for_gsg(page_type: str, n_critical: int = 7,
                             include_killer: bool = True) -> str:
    """Helper : rend tout le bloc doctrine pour un GSG prompt court.

    Inclut :
      - Top N critères en mode "principe constructif"
      - Killer rules (si include_killer)
    """
    block = f"# DOCTRINE V3.2 — TOP {n_critical} PRINCIPES CONSTRUCTIFS pour {page_type}\n\n"
    block += "Tu construis pour SATISFAIRE ces principes nativement, pas pour cocher une checklist.\n"
    block += "Ces critères représentent la doctrine accumulée sur 6 mois d'audit CRO.\n\n"

    top_ids = top_critical_for_page_type(page_type, n=n_critical)
    for cid in top_ids:
        block += criterion_to_gsg_principle(cid) + "\n"

    if include_killer:
        block += "\n" + render_killer_rules_block(page_type)
    return block


# ─────────────────────────────────────────────────────────────────────────────
# CLI / Smoke test
# ─────────────────────────────────────────────────────────────────────────────

def _print_smoke_test():
    """Smoke test pour valider que la doctrine se charge bien."""
    print("══ Doctrine V3.2 Smoke Test ══\n")

    all_crit = load_all_criteria()
    print(f"Total criteria loaded : {len(all_crit)}")
    by_pillar = {}
    for cid, c in all_crit.items():
        p = c.get("pillar", "?")
        by_pillar[p] = by_pillar.get(p, 0) + 1
    print(f"By pillar : {by_pillar}\n")

    killers = load_killer_rules()
    print(f"Killer rules loaded : {len(killers)}")
    for r in killers[:3]:
        print(f"  - {r.get('id', '?')} : {r.get('name', '?')}")
    print()

    print("Top 7 critical for 'lp_listicle' :")
    for cid in top_critical_for_page_type("lp_listicle", n=7):
        c = get_criterion(cid)
        print(f"  {cid:14s} ({c.get('pillar','?'):10s}) {c.get('label','?')[:80]}")
    print()

    print("Top 7 critical for 'home' :")
    for cid in top_critical_for_page_type("home", n=7):
        c = get_criterion(cid)
        print(f"  {cid:14s} ({c.get('pillar','?'):10s}) {c.get('label','?')[:80]}")
    print()

    print("Sample GSG principle (hero_01) :")
    print(criterion_to_gsg_principle("hero_01"))

    print("Sample audit prompt (hero_01) :")
    print(criterion_to_audit_prompt("hero_01"))

    print("\nFull doctrine block for 'lp_listicle' (3K chars max — pour mega-prompt court) :")
    block = render_doctrine_for_gsg("lp_listicle", n_critical=7)
    print(f"Block size : {len(block)} chars")
    print(block[:2000])


if __name__ == "__main__":
    _print_smoke_test()
