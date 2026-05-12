"""Prompt Assembly V26.AA Sprint 3.

Assemble un prompt COURT (≤10K chars hard limit) pour le Mode 1 COMPLETE en
combinant 3 sources de vérité :

  1. **Doctrine V3.2 racine partagée** (scripts/doctrine.py) — top 7 critères
     pour le page_type + killer_rules absolues, en mode "principes constructifs"
     (pas checklist — les principes guident la création, ne servent pas à cocher).

  2. **Brand Intelligence** (core.brand_intelligence) — brand_dna V29 + diff E1
     prescriptif. La voix, la palette, les FORBID/AMPLIFY/FIX sont injectés.

  3. **Brief** — 3 questions courtes (objectif, audience, angle).

ANTI-PATTERN ÉVITÉ (cf design doc V26.AA §8.1) : mega-prompt sursaturé > 15K
chars qui pousse Sonnet à cocher des cases au lieu de créer.

LEÇON gsg_minimal v1 (humanlike 70/80 — meilleur run actuel) : la concision +
règle de RENONCEMENT (mieux vaut omettre que mettre creux) bat le pipeline
4-stages V26.Z BESTOF (humanlike 66/80).

Output : (system_prompt, user_message) — 2 strings prêts à passer à Sonnet.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Make scripts/doctrine.py importable
sys.path.insert(0, str(ROOT / "scripts"))
from doctrine import (  # noqa: E402
    top_critical_for_page_type,
    criterion_to_gsg_principle,
    render_killer_rules_block,
)

from .brand_intelligence import format_brand_block  # noqa: E402
from .design_grammar_loader import load_design_grammar, format_design_grammar_block, has_design_grammar  # noqa: E402
from .minimal_guards import format_minimal_constraints_block  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# System prompt — identity + règles d'or + format output
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es **directeur créatif senior** (15+ ans, agences top-tier type Pentagram, Wieden+Kennedy, R/GA) doublé d'un **expert CRO** (200+ LPs auditées avec doctrine GrowthCRO V3.2). Tu CRÉES des landing pages qui rivalisent avec Linear, Stripe, Cursor, Aesop, Glossier dans leur catégorie.

## RÈGLES D'OR (à respecter ABSOLUMENT)

### 1. Concision et renoncement
**Mieux vaut OMETTRE qu'inclure du creux.** Si tu n'as pas une preuve concrète, un chiffre source, un témoignage nommé : ne fais pas semblant. Une LP courte avec 100% de claims sourcés bat une LP longue avec 50% de bullshit générique. Les seuls chiffres autorisés sont ceux listés dans le bloc CONTRAINTES DETERMINISTES ou explicitement présents dans le brief.

### 2. Brand DNA = contrainte créative non négociable
Tu reçois ci-dessous le brand DNA du client (voix, palette, typo, archetype). Tu RESPECTES la voix et tu APPLIQUES le diff prescriptif (PRESERVE / AMPLIFY / FIX / FORBID). Si la marque interdit "complex" → tu n'utilises JAMAIS le mot. Si la marque interdit "gradient mesh" → tu ne mets pas de gradient mesh, point.

### 3. Doctrine V3.2 = principes constructifs (pas checklist)
Tu reçois les TOP 7 critères CRO pour ce page_type, formulés en mode "à FAIRE" (pas "à scorer"). Tu construis ta LP pour qu'ils soient SATISFAITS NATIVEMENT. Tu ne coches pas mécaniquement — tu intègres comme un DA senior intègre la grid system : sans y penser, c'est dans les fibres.

### 4. Règles absolues (killer rules)
Les killer_rules listées sont des INTERDITS absolus. Les violer = échec total de la LP. Ex: "test 5 secondes failed + ratio 1:1 cassé" → cap la note → pas négociable.

### 5. Signature visuelle nommable
Ta LP doit avoir une **signature visuelle nommable en 3-5 mots** (ex: "Editorial Press SaaS", "Brutalist Tech Warm", "Quiet Luxury Data"). Pas de "AI showcase mode" qui empile gradient mesh + grain + glass + drop caps sans thèse. Une thèse, exécutée propre.

### 6. HTML autocontenu mobile-first
- Un seul fichier HTML auto-contenu (CSS inline dans `<style>`, pas de fichiers externes hormis fonts Google ou data URIs)
- Mobile-first (375px) puis desktop (1440px)
- Sémantique correcte (`<header>`, `<main>`, `<section>`, `<article>`, `<footer>`)
- Une seule balise `<h1>` (test 5s + accessibilité)
- Texte dans la langue cible indiquée dans le bloc CONTRAINTES DETERMINISTES
- Aucun `@font-face`, aucune font base64, aucun `data:font`, aucun blob asset. Utilise uniquement `font-family` CSS avec fallbacks.
- Aucune image dépendant d'un host externe (utilise SVG inline léger ou formes CSS sobres pour les visuels)

## FORMAT OUTPUT

Tu DOIS répondre avec uniquement le HTML complet, commençant par `<!DOCTYPE html>` et finissant par `</html>`. Pas de markdown wrapper. Pas d'explication. Le HTML brut, tel qu'il sera servi au visiteur."""


# ─────────────────────────────────────────────────────────────────────────────
# User message builder — brand + doctrine + brief
# ─────────────────────────────────────────────────────────────────────────────

def build_user_message(
    client: str,
    page_type: str,
    brief: dict,
    brand_dna: dict,
    n_critical: int = 7,
    creative_route_block: str = "",
    inject_design_grammar: bool = True,
    minimal_constraints: dict | None = None,
) -> str:
    """Construit le user message Mode 1.

    Args:
      client: slug du client
      page_type: ex "lp_listicle", "home", "pdp"
      brief: dict avec clés objectif / audience / angle (3 questions courtes)
      brand_dna: brand DNA chargé via brand_intelligence.load_brand_dna(client)
      n_critical: nombre de critères doctrine à injecter (default 7)
      creative_route_block: bloc texte rendu par creative_director.render_creative_route_block (Sprint B V26.AA)
      inject_design_grammar: charger design_grammar_loader si dispo (Sprint B V26.AA)
      minimal_constraints: contraintes deterministes Day 5 (CTA, langue, preuves, fonts)

    Returns: user message string (~4-6K chars cible).
    """
    sections: list[str] = []

    # ── 1. Contexte mission ────────────────────────────────────
    sections.append(f"# MISSION — Crée une landing page de type `{page_type}` pour le client `{client}`.\n")

    # ── 2. Brief (3 questions) ─────────────────────────────────
    sections.append("## BRIEF (réponses du client à 3 questions)")
    objectif = brief.get("objectif") or brief.get("goal") or "(non spécifié — déduis depuis brand DNA)"
    audience = brief.get("audience") or brief.get("cible") or "(non spécifié — déduis depuis brand DNA)"
    angle = brief.get("angle") or brief.get("hook") or "(non spécifié — propose ton meilleur angle)"
    sections.append(f"- **Objectif business** : {objectif}")
    sections.append(f"- **Audience cible** : {audience}")
    sections.append(f"- **Angle / hook éditorial** : {angle}")
    if brief.get("notes"):
        sections.append(f"- **Notes additionnelles** : {brief['notes']}")

    # ── 2b. Contraintes deterministes Day 5 ───────────────────
    if minimal_constraints:
        sections.append("\n" + format_minimal_constraints_block(minimal_constraints))

    # ── 3. Brand DNA ──────────────────────────────────────────
    brand_block = format_brand_block(brand_dna, max_chars=2400 if minimal_constraints else 3500)
    sections.append("\n" + brand_block)

    # ── 3b. Design Grammar V30 (Sprint B V26.AA — branché) ────
    if inject_design_grammar and has_design_grammar(client):
        grammar = load_design_grammar(client)
        dg_block = format_design_grammar_block(grammar, max_chars=2200)
        if dg_block:
            sections.append("\n" + dg_block)

    # ── 3c. Creative Route (Sprint B V26.AA — optionnel) ──────
    if creative_route_block:
        sections.append("\n" + creative_route_block)

    # ── 4. Doctrine V3.2 — top N principes constructifs ───────
    sections.append(f"\n## DOCTRINE V3.2 — TOP {n_critical} PRINCIPES CONSTRUCTIFS pour `{page_type}`")
    sections.append("Tu construis pour SATISFAIRE ces principes nativement, pas pour cocher une checklist.")
    sections.append("Ces critères représentent 6 mois d'audit CRO sur 105+ clients — c'est notre IP.\n")
    top_ids = top_critical_for_page_type(page_type, n=n_critical)
    for cid in top_ids:
        principle = criterion_to_gsg_principle(cid)
        sections.append(principle)

    # ── 5. Killer rules absolues ──────────────────────────────
    killer_block = render_killer_rules_block(page_type)
    if killer_block:
        sections.append("\n" + killer_block)

    # ── 6. Final reminder ────────────────────────────────────
    sections.append(
        "\n## DERNIER MOT\n"
        "Génère la LP HTML complète. Si tu hésites entre 2 options, choisis celle qui :\n"
        "  1. Respecte le brand DNA (voix, palette, FORBID)\n"
        "  2. Active 5+ critères doctrine ci-dessus dès le 1er fold\n"
        "  3. A une signature visuelle nommable en 3-5 mots (le plus important)\n"
        "Concision > exhaustivité. Pas de bullshit générique. Aucun chiffre hors contraintes deterministes.\n"
        "Si une règle doctrine te demande plus de preuves que les contraintes n'en fournissent, les contraintes gagnent : tu omets la preuve au lieu d'inventer.\n"
        "\nMaintenant, livre le HTML."
    )

    return "\n".join(sections)


def build_mode1_prompt(
    client: str,
    page_type: str,
    brief: dict,
    brand_dna: dict,
    n_critical: int = 7,
    creative_route_block: str = "",
    inject_design_grammar: bool = True,
    minimal_constraints: dict | None = None,
) -> tuple[str, str]:
    """API publique pour Mode 1 COMPLETE.

    Returns: (system_prompt, user_message) — 2 strings prêts pour Sonnet.

    Hard guard : si user_message > 12K chars (raised from 10K Sprint B pour
    inclure design_grammar + creative_route), on tronque les sections moins
    critiques (brand_block max_chars réduit, design_grammar skipped).
    """
    user = build_user_message(
        client, page_type, brief, brand_dna,
        n_critical=n_critical,
        creative_route_block=creative_route_block,
        inject_design_grammar=inject_design_grammar,
        minimal_constraints=minimal_constraints,
    )
    if len(user) > 12000:
        # Trim brand block harder
        # Re-build with smaller brand_dna budget
        from .brand_intelligence import format_brand_block as _fbb
        sections: list[str] = []
        sections.append(f"# MISSION — Crée une landing page de type `{page_type}` pour le client `{client}`.\n")
        sections.append("## BRIEF")
        sections.append(f"- Objectif : {brief.get('objectif', '?')}")
        sections.append(f"- Audience : {brief.get('audience', '?')}")
        sections.append(f"- Angle : {brief.get('angle', '?')}")
        if minimal_constraints:
            sections.append("\n" + format_minimal_constraints_block(minimal_constraints, max_facts=6))
        sections.append("\n" + _fbb(brand_dna, max_chars=2000))
        sections.append(f"\n## DOCTRINE V3.2 — TOP {n_critical} pour `{page_type}`")
        for cid in top_critical_for_page_type(page_type, n=n_critical):
            sections.append(criterion_to_gsg_principle(cid))
        killer_block = render_killer_rules_block(page_type)
        if killer_block:
            sections.append("\n" + killer_block)
        sections.append(
            "\nGénère la LP HTML. Concision > exhaustivité. Brand DNA non négociable. "
            "Doctrine = principes constructifs, pas checklist. Signature visuelle nommable. "
            "Aucun chiffre hors contraintes deterministes."
        )
        user = "\n".join(sections)
    return (SYSTEM_PROMPT, user)


def estimate_prompt_size(client: str, page_type: str, brief: dict, brand_dna: dict) -> dict:
    """Helper debug — montre la taille du prompt sans appeler Sonnet."""
    sys_, user = build_mode1_prompt(client, page_type, brief, brand_dna)
    return {
        "system_chars": len(sys_),
        "user_chars": len(user),
        "total_chars": len(sys_) + len(user),
        "system_lines": sys_.count("\n"),
        "user_lines": user.count("\n"),
    }


if __name__ == "__main__":
    # Smoke test : Weglot listicle
    from .brand_intelligence import load_brand_dna

    client = "weglot"
    page_type = "lp_listicle"
    brief = {
        "objectif": "Convertir les visiteurs growth/produit SaaS en trial gratuit Weglot",
        "audience": "Head of Growth / PM / Engineering Lead dans SaaS B2B 50-500 personnes ayant déjà un site live et envisageant l'internationalisation",
        "angle": "Listicle éditorial 'Les 7 raisons pour lesquelles les équipes growth choisissent Weglot' — voix Growth Society, ton enquête, preuves chiffrées",
    }
    brand_dna = load_brand_dna(client)

    sys_, user = build_mode1_prompt(client, page_type, brief, brand_dna)
    sizes = estimate_prompt_size(client, page_type, brief, brand_dna)
    print(f"\n══ Mode 1 prompt assembly — {client} / {page_type} ══")
    print(f"  System : {sizes['system_chars']} chars / {sizes['system_lines']} lines")
    print(f"  User   : {sizes['user_chars']} chars / {sizes['user_lines']} lines")
    print(f"  TOTAL  : {sizes['total_chars']} chars (gate ≤10000 user)")
    print("\n--- USER MESSAGE PREVIEW (first 3000) ---\n")
    print(user[:3000])
    print("\n--- USER MESSAGE PREVIEW (last 1500) ---\n")
    print(user[-1500:])
