"""GSG Brand DNA Diff V26.Z E1 — ajoute le 4e quadrant "Fix" au brand_dna existant.

Réponse à la faille #2 du diagnostic post-audit (Brand DNA descriptif) :
notre extraction V29 capture preserve (brand_fidelity_anchors), amplify
(approved_techniques), forbid (do_not, forbidden_words) — mais le quadrant
"Fix" (ce qui est MAUVAIS chez la marque actuelle qu'il FAUT corriger) est
totalement absent.

ChatGPT V26 GOD MODE et l'audit humanlike Phase 1+E2 confirment : sans Fix,
le générateur reproduit la médiocrité existante au lieu de l'élever. Quand
le humanlike détecte "palette pastel sans grain artisanal" ou "tone oscillant
forcé", c'est précisément la signature d'un Brand DNA descriptif qui copie
sans corriger.

E1 résout en ajoutant une Phase 3 LLM Vision NON-DESTRUCTIVE qui :
1. Lit le brand_dna.json existant (Phase 1+2 V29)
2. Charge 2-3 fold screenshots du site actuel
3. Demande à Sonnet Vision : "voici la marque actuelle, voici son DNA
   extrait, voici la page actuelle. Qu'est-ce qui :
     - PRESERVE = à garder absolument (forces réelles)
     - AMPLIFY = à pousser plus loin (potentiel sous-exploité)
     - FIX     = à corriger (faiblesses concrètes auditables)
     - FORBID  = à interdire (anti-patterns brand)"
4. Save dans brand_dna.json au champ `diff{}` (merge non-destructif)
5. Compatible avec gsg_generate_lp qui peut maintenant exposer ce diff
   au mega-prompt (E1.b suite) pour forcer Sonnet à AMPLIFIER+FIXER, pas
   reproduire.

Usage CLI :
    python3 skills/site-capture/scripts/brand_dna_diff_extractor.py \\
        --client weglot \\
        [--force]  # re-extract même si diff existe déjà

Usage module :
    from brand_dna_diff_extractor import extract_diff
    diff = extract_diff(client="weglot")
    # → {"preserve": [...], "amplify": [...], "fix": [...], "forbid": [...]}

Coût : ~$0.05 par client (1 call Sonnet Vision, ~3K input + ~2K output).
Industrialisable sur 51 clients : ~$2.50 total.
"""
from __future__ import annotations

import sys as _sys
import pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[3]))

# Load .env into os.environ BEFORE any anthropic SDK construction.
# growthcro.config._load_dotenv_once() runs at import time; without this line,
# downstream modules construct anthropic.Anthropic() with an empty env and
# crash on missing ANTHROPIC_API_KEY.
import growthcro.config  # noqa: F401,E402 — side-effect import for env load

import argparse
import base64
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"
SONNET_MODEL = "claude-sonnet-4-5-20250929"


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json\n"):
            text = text[5:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _resize_for_anthropic(p: pathlib.Path, max_w: int = 1568, max_size_mb: float = 4.5) -> bytes:
    """Resize image to fit Anthropic Vision constraints (max 5MB, 8K dimension)."""
    from PIL import Image
    import io
    img = Image.open(p)
    if img.mode != "RGB":
        img = img.convert("RGB")
    if img.width > max_w:
        ratio = max_w / img.width
        new_h = int(img.height * ratio)
        img = img.resize((max_w, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    data = buf.getvalue()
    if len(data) > max_size_mb * 1024 * 1024:
        # Re-compress with lower quality
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70, optimize=True)
        data = buf.getvalue()
    return data


def _find_fold_screenshots(client_dir: pathlib.Path, max_n: int = 3) -> list[pathlib.Path]:
    """Récupère jusqu'à N fold screenshots (home prioritaire) pour LLM Vision."""
    screenshots: list[pathlib.Path] = []
    # Home first
    for page_name in ["home", "homepage", "index"]:
        page_dir = client_dir / page_name
        if page_dir.is_dir():
            ss_dir = page_dir / "screenshots"
            if ss_dir.exists():
                for fname in ("desktop_clean_fold.png", "desktop_clean_full.png",
                              "desktop_asis_fold.png", "spatial_fold_desktop.png"):
                    f = ss_dir / fname
                    if f.exists():
                        screenshots.append(f)
                        break
    # Fill up with other pages
    for page_dir in sorted(client_dir.iterdir()):
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        if page_dir.name in ("home", "homepage", "index", "design_grammar"):
            continue
        ss_dir = page_dir / "screenshots"
        if not ss_dir.exists():
            continue
        for fname in ("desktop_clean_fold.png", "desktop_clean_full.png",
                      "spatial_fold_desktop.png"):
            f = ss_dir / fname
            if f.exists() and f not in screenshots:
                screenshots.append(f)
                break
        if len(screenshots) >= max_n:
            break
    return screenshots[:max_n]


DIFF_SYSTEM = """Tu es **directeur créatif senior + brand strategist** (15+ ans, agences top-tier). Tu reçois :
- Le Brand DNA extrait V29 (Phase 1 Python + Phase 2 LLM Vision) d'une marque
- 1-3 fold screenshots du site actuel de cette marque

Ta mission : produire le **Brand DNA Diff** en 4 quadrants opérationnels que ChatGPT V26 et l'audit GSG ont identifié comme la couche manquante. Le brand_dna actuel décrit ce qui EST. Toi tu produis ce qu'il FAUT FAIRE.

## RÈGLE D'OR — Ancrer dans l'évidence visuelle

Chaque entrée des 4 listes doit être :
- **Auditable** (ancrée dans un élément précis du screenshot ou du DNA)
- **Actionnable** (un générateur LP doit pouvoir l'exécuter)
- **Spécifique** (pas "améliorer le design", mais "remplacer le hero centré symétrique par une asymétrie 60/40")

## LES 4 QUADRANTS

### preserve — Forces RÉELLES auditables à garder absolument
Ce qui marche déjà chez cette marque, qu'un générateur ne doit JAMAIS détruire. Anchors visuels reconnaissables, ton de voix qui résonne, codes établis. Si la palette primary fait partie de l'identité forte → preserve. Si une typo serif unique sert l'autorité → preserve.

### amplify — Potentiel sous-exploité à pousser plus loin
Choses présentes mais timides, qui mériteraient d'être ÉLEVÉES dans la prochaine itération. Ex : "le ton expert est là mais dilué — amplifier en éliminant les hedges 'might' 'could'". Ex : "la palette sombre existe mais sous-utilisée — amplifier en hero full-bleed".

### fix — Faiblesses CONCRÈTES de la marque actuelle qu'il FAUT corriger
Le quadrant le plus important — celui qui manque dans le brand_dna actuel. Ce qui est MAUVAIS aujourd'hui qu'un générateur LP doit explicitement améliorer. Ex :
- "CTAs trop polis 'Get started' — manque urgence active"
- "Hiérarchie visuelle plate, H1 et H2 quasi même taille"
- "Témoignages anonymes sans visage humain — manque sympathie Cialdini"
- "Densité texte uniforme, pas de respiration éditoriale"
- "Palette pastel safe — manque contraste pour attaquer hiérarchie"
SI la marque actuelle est déjà top-tier sur tous les axes, le quadrant fix peut être court (2-3 entrées) — mais ne le laisse JAMAIS vide.

### forbid — Anti-patterns brand interdits absolus
Ce qu'aucune génération ne doit jamais inclure. Patterns IA reconnaissables, codes du secteur opposé à l'identité, mots/visuels off-brand. Souvent reprend partiellement les do_not/forbidden_words existants en les rendant plus tranchants.

## OUTPUT JSON STRICT

{
  "client": "<client>",
  "diff_version": "v26.z.E1.1",
  "preserve": [
    {"item": "<courte description, 5-15 mots>", "evidence": "<élément précis vu dans DNA ou screenshot>"}
  ],
  "amplify": [
    {"item": "<directive amplify>", "evidence": "<où c'est sous-exploité>", "how": "<comment l'amplifier dans une LP>"}
  ],
  "fix": [
    {"item": "<faiblesse concrète>", "evidence": "<où c'est mauvais aujourd'hui>", "fix_directive": "<comment le corriger>", "priority": "high|medium|low"}
  ],
  "forbid": [
    {"item": "<anti-pattern>", "reason": "<pourquoi off-brand>"}
  ],
  "summary": "<3-4 phrases qui résume la posture stratégique du Diff : qu'est-ce que cette marque DOIT devenir dans sa prochaine LP, vs ce qu'elle EST aujourd'hui>"
}

JSON only, pas de markdown autour. Sois SPÉCIFIQUE et AUDITABLE."""


def extract_diff(client: str, model: str = SONNET_MODEL,
                 force: bool = False, verbose: bool = True) -> dict:
    """Extract Brand DNA Diff (preserve/amplify/fix/forbid) for a client.

    Modifies brand_dna.json in-place by adding/updating the `diff` field.
    Returns the diff dict (also accessible at brand_dna.diff after save).

    Si `force=False` et `diff` existe déjà → no-op (return existing).
    """
    client_dir = CAPTURES / client
    bd_fp = client_dir / "brand_dna.json"
    if not bd_fp.exists():
        raise FileNotFoundError(f"{bd_fp} not found. Run brand_dna_extractor first.")

    brand_dna = json.loads(bd_fp.read_text())

    if not force and brand_dna.get("diff"):
        if verbose:
            print(f"  ⚠️  diff already exists for {client} (use --force to re-extract)")
        return brand_dna["diff"]

    # Find fold screenshots
    screenshots = _find_fold_screenshots(client_dir, max_n=3)
    if not screenshots:
        return {"error": "no_fold_screenshots_found",
                "hint": "Run capture pipeline first to produce desktop_clean_fold.png"}

    if verbose:
        print(f"  ✓ Found {len(screenshots)} fold screenshots: "
              f"{', '.join(s.parent.parent.name for s in screenshots)}")

    # Encode screenshots
    image_blocks = []
    for ss_path in screenshots:
        try:
            data = _resize_for_anthropic(ss_path)
            image_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(data).decode("ascii"),
                },
            })
        except Exception as e:
            if verbose:
                print(f"  ⚠️  skipped {ss_path.name}: {e}")
            continue

    if not image_blocks:
        return {"error": "no_screenshots_loadable"}

    # Build user message with brand_dna context
    bd_summary = json.dumps({
        "identity": brand_dna.get("identity", {}),
        "visual_tokens": {
            "colors": (brand_dna.get("visual_tokens") or {}).get("colors", {}),
            "typography": (brand_dna.get("visual_tokens") or {}).get("typography", {}),
        },
        "voice_tokens": brand_dna.get("voice_tokens", {}),
        "image_direction": brand_dna.get("image_direction", {}),
        "asset_rules": brand_dna.get("asset_rules", {}),
    }, ensure_ascii=False, indent=2)[:4500]

    text_msg = f"""## Client : {client.upper()}

## Brand DNA actuel (Phase 1+2 V29)
```json
{bd_summary}
```

Voici {len(image_blocks)} screenshot(s) du site actuel. Produis le Brand DNA Diff (preserve/amplify/fix/forbid) en JSON strict. Sois ancré dans l'évidence visible et le DNA extrait."""

    content_blocks = image_blocks + [{"type": "text", "text": text_msg}]

    import anthropic
    client_api = anthropic.Anthropic()
    if verbose:
        total_chars = len(text_msg) + sum(len(b.get("source", {}).get("data", ""))
                                           for b in image_blocks if "source" in b) // 1000
        print(f"  → Sonnet diff extraction (text={len(text_msg)} chars + {len(image_blocks)} images base64) ...", flush=True)
    msg = client_api.messages.create(
        model=model,
        max_tokens=3000,
        temperature=0.2,
        system=DIFF_SYSTEM,
        messages=[{"role": "user", "content": content_blocks}],
    )
    raw = msg.content[0].text
    if verbose:
        print(f"  ← in={msg.usage.input_tokens} out={msg.usage.output_tokens}", flush=True)

    text = _strip_fences(raw)
    try:
        diff = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError(f"Diff parse failed. Raw first 500: {text[:500]}")
        diff = json.loads(m.group(0))

    # Add metadata
    diff.setdefault("client", client)
    diff.setdefault("diff_version", "v26.z.E1.1")
    diff["model_used"] = model
    diff["tokens_in"] = msg.usage.input_tokens
    diff["tokens_out"] = msg.usage.output_tokens
    diff["screenshots_used"] = [str(s.relative_to(ROOT)) for s in screenshots]

    # Merge non-destructively into brand_dna.json
    brand_dna["diff"] = diff
    brand_dna["version"] = "v29.E1.1"  # bump version to signal diff present
    bd_fp.write_text(json.dumps(brand_dna, ensure_ascii=False, indent=2))
    if verbose:
        print(f"  ✓ diff saved to {bd_fp.relative_to(ROOT)} (merged non-destructively)")

    return diff


def print_diff_summary(diff: dict) -> None:
    """Pretty-print the Brand DNA Diff."""
    print(f"\n══ BRAND DNA DIFF — {diff.get('client', '?').upper()} ══")
    summary = diff.get("summary", "")
    if summary:
        print("\n  Summary :")
        print(f"  {summary}")

    for cat, label, sym in [
        ("preserve", "PRESERVE", "🟢"),
        ("amplify", "AMPLIFY", "🟡"),
        ("fix", "FIX", "🔴"),
        ("forbid", "FORBID", "⛔"),
    ]:
        items = diff.get(cat) or []
        print(f"\n  {sym} {label} ({len(items)})")
        for it in items[:8]:
            if isinstance(it, dict):
                main = it.get("item", "?")
                if cat == "fix":
                    pri = it.get("priority", "?")
                    print(f"    [{pri}] {main}")
                    if it.get("fix_directive"):
                        print(f"           → {it['fix_directive']}")
                elif cat == "amplify" and it.get("how"):
                    print(f"    {main}")
                    print(f"      → {it['how']}")
                else:
                    print(f"    {main}")
                if it.get("evidence"):
                    print(f"      evidence: {it['evidence']}")
            else:
                print(f"    {it}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--force", action="store_true",
                    help="Re-extract even if diff already exists in brand_dna.json")
    args = ap.parse_args()

    print(f"\n══ Brand DNA Diff Extractor — {args.client} ══\n")
    diff = extract_diff(args.client, force=args.force)

    if diff.get("error"):
        print(f"\n❌ Error: {diff['error']}")
        if diff.get("hint"):
            print(f"   Hint: {diff['hint']}")
        sys.exit(1)

    print_diff_summary(diff)


if __name__ == "__main__":
    main()
