"""GSG scrap_inspiration — V26.Y.7

Prend 1-3 URLs d'inspiration fournies par l'user (ou découvertes par
golden_design_bridge) et extract leur DA via WebFetch + Haiku Vision.

Output : data/_inspirations/<slug>.json contenant :
  - palette dominante (3 hex max)
  - typo dominante (display + body)
  - signature visuelle distinctive (1 phrase)
  - motion signature
  - ce qu'on emprunte concrètement (1-2 techniques précises CSS-ready)

Mode hybride C : ces inspirations sont injectées dans le mega-prompt de
gsg_generate_lp.py comme "INSPIRATIONS À EMPRUNTER (cross-catégorie)".

Usage :
    python3 skills/growth-site-generator/scripts/scrap_inspiration.py \
        --urls https://stripe.com https://linear.app https://vercel.com \
        --tag-aspect tone visual business \
        --output data/_inspirations/weglot_inspis.json
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
import json
import pathlib
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]


def url_to_slug(url: str) -> str:
    p = urllib.parse.urlparse(url)
    return p.netloc.replace("www.", "").replace(".", "_") or "unknown"


def fetch_via_haiku(url: str, aspect: str = "visual") -> dict:
    """Appelle Haiku via API messages avec un prompt structuré sur l'URL.

    aspect ∈ {visual, tone, business}
      - visual : palette + typo + animation + composition
      - tone : ton, vocabulaire, voice
      - business : positionnement, audience, USP
    """
    import anthropic
    client = anthropic.Anthropic()

    aspect_prompts = {
        "visual": """Analyse l'identité visuelle de cette URL. Output JSON STRICT :
{
  "url": "...",
  "aspect": "visual",
  "palette_dominant": ["#hex1", "#hex2", "#hex3"],
  "typography_display": "famille font display dominante (1 max)",
  "typography_body": "famille font body dominante",
  "signature_visual_motif": "1 phrase précise sur ce qui rend ce site visuellement unique (anti-AI-slop)",
  "motion_signature": "1 phrase sur le motion/animation distinctif",
  "techniques_to_borrow": [
    {"name": "...", "css_pattern": "code/concept précis utilisable", "why": "1 phrase"}
  ]
}""",
        "tone": """Analyse le TON et la voix de cette URL. Output JSON STRICT :
{
  "url": "...",
  "aspect": "tone",
  "tone_keywords": ["...", "..."],
  "voice_signature_phrase": "phrase emblématique du site",
  "ctas_observed": ["...", "..."],
  "rhythm": "courte punchy | balanced | long narrative",
  "techniques_to_borrow": [
    {"name": "...", "example": "..."}
  ]
}""",
        "business": """Analyse le POSITIONNEMENT BUSINESS de cette URL. Output JSON STRICT :
{
  "url": "...",
  "aspect": "business",
  "category": "...",
  "audience": "...",
  "usp": "...",
  "differentiators": ["..."],
  "techniques_to_borrow": [
    {"name": "...", "why": "..."}
  ]
}"""
    }
    prompt = aspect_prompts.get(aspect, aspect_prompts["visual"])
    full_prompt = (
        f"URL : {url}\nAspect : {aspect}\n\n"
        f"Tu utilises ta connaissance générale du web et de cette marque.\n\n"
        f"{prompt}\n\nRetourne JSON only, pas de markdown."
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=900,
        temperature=0.2,
        messages=[{"role": "user", "content": full_prompt}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.lstrip("`")
        if raw.startswith("json\n"): raw = raw[5:]
        if raw.endswith("```"): raw = raw[:-3]
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"url": url, "aspect": aspect, "error": "parse_failed", "raw": raw[:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", nargs="+", required=True, help="1-3 URLs d'inspiration")
    ap.add_argument("--tag-aspect", nargs="+", default=None,
                    help="Aspect par URL (visual|tone|business). Default : visual partout.")
    ap.add_argument("--output", required=True, help="Path JSON output")
    args = ap.parse_args()

    if args.tag_aspect and len(args.tag_aspect) != len(args.urls):
        sys.exit(f"❌ {len(args.urls)} URLs mais {len(args.tag_aspect)} aspects")

    results = []
    for i, url in enumerate(args.urls):
        aspect = (args.tag_aspect[i] if args.tag_aspect else "visual")
        print(f"  → Scraping {url} (aspect={aspect}) ...", flush=True)
        r = fetch_via_haiku(url, aspect)
        r["_slug"] = url_to_slug(url)
        results.append(r)
        if "error" in r:
            print(f"    ⚠️  {r['error']}")
        else:
            print(f"    ✓ palette={r.get('palette_dominant', '?')} signature={r.get('signature_visual_motif', '?')[:60]}")

    out_fp = pathlib.Path(args.output)
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(json.dumps({
        "version": "V26.Y.7",
        "n_inspirations": len(results),
        "inspirations": results,
    }, ensure_ascii=False, indent=2))
    print(f"\n✓ Saved : {out_fp}")


if __name__ == "__main__":
    main()
