"""V29 prep — GSG Brand DNA Extractor (Python+LLM hybrid).

Réponse à la critique ChatGPT Hardcore Audit (§4.3 "La DA ne peut pas
être une simple extraction de couleurs") + reco approche Python > LLM
sur 80% des dimensions :

- Phase 1 (Python pur, 80% coverage) : couleurs, typo, spacing, shapes,
  depth, motion, texture
- Phase 2 (LLM ciblé, 20% coverage) : voice tokens nuance, image direction,
  asset rules contextuels

Schema BrandDNA (cf ChatGPT §7.2) :
{
  "identity": {brand_name, category, market_position, audience, confidence},
  "visual_tokens": {
    "colors": {primary, secondary, neutrals, semantic},
    "typography": {heading, body, scale, line_height},
    "spacing": {container_max, section_y, grid_gap, card_padding},
    "shape": {radius_scale, dominant_radius, edge_language},
    "depth": {shadow_style, blur, elevation_levels},
    "texture": {noise, grain_strength, gradient_language, material},
    "motion": {easing, duration_ms, amplitude}
  },
  "voice_tokens": {tone, forbidden_words, preferred_cta_verbs, sentence_rhythm},
  "asset_rules": {photo_style, lighting, composition, do_not_use}
}

Storage : data/captures/<client>/brand_dna.json (per-client, not per-page)

Status V29 prep : squelette complet + Phase 1 colors implémenté + Phase 2
stubs prêts à brancher.

Usage :
    python3 skills/site-capture/scripts/brand_dna_extractor.py --client kaiju
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter
from typing import Any, Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"


# ────────────────────────────────────────────────────────────────
# Phase 1 — Colors (Python pur via Pillow + k-means scikit-learn)
# ────────────────────────────────────────────────────────────────

def extract_colors_from_screenshot(image_path: pathlib.Path, n_clusters: int = 8) -> dict:
    """Extract dominant color palette from a screenshot via k-means clustering.
    Returns {primary, secondary, neutrals, palette[], coverage_pct}.

    Usage : Pillow + scikit-learn (no LLM, déterministe, 100ms par image)."""
    try:
        from PIL import Image
        import numpy as np
        from sklearn.cluster import KMeans
    except ImportError:
        return {"error": "missing dependency: pip install Pillow numpy scikit-learn"}

    if not image_path.exists():
        return {"error": f"image not found: {image_path}"}

    try:
        img = Image.open(image_path).convert("RGB")
        # Downsample for speed (max 400×400)
        img.thumbnail((400, 400))
        arr = np.array(img).reshape(-1, 3)
        # Filter pure white / pure black (background noise)
        mask = ((arr.sum(axis=1) > 30) & (arr.sum(axis=1) < 720))
        arr = arr[mask]
        if len(arr) < 100:
            return {"error": "not enough non-bg pixels"}

        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        kmeans.fit(arr)
        centers = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        counts = Counter(labels)
        total = sum(counts.values())

        palette = []
        for idx in range(n_clusters):
            r, g, b = centers[idx]
            hex_col = f"#{r:02x}{g:02x}{b:02x}"
            pct = round(counts.get(idx, 0) / total, 4)
            palette.append({"hex": hex_col, "rgb": [int(r), int(g), int(b)], "coverage_pct": pct})

        # Sort by coverage
        palette.sort(key=lambda c: c["coverage_pct"], reverse=True)

        # Categorize : primary (most distinctive non-neutral), neutrals (close to grayscale)
        def _is_neutral(rgb):
            r, g, b = rgb
            return abs(r - g) < 15 and abs(g - b) < 15 and abs(r - b) < 15

        primary = next((c for c in palette if not _is_neutral(c["rgb"])), palette[0])
        neutrals = [c for c in palette if _is_neutral(c["rgb"])][:3]
        secondaries = [c for c in palette if not _is_neutral(c["rgb"]) and c != primary][:2]

        return {
            "primary": {"hex": primary["hex"], "coverage_pct": primary["coverage_pct"], "usage_hint": "cta|brand|headline"},
            "secondary": [{"hex": c["hex"], "coverage_pct": c["coverage_pct"]} for c in secondaries],
            "neutrals": [c["hex"] for c in neutrals],
            "palette_full": palette,
            "method": "python:Pillow+sklearn.KMeans",
            "n_clusters": n_clusters,
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:200]}"}


# ────────────────────────────────────────────────────────────────
# Phase 1 — Typography (Python pur via Playwright getComputedStyle)
# ────────────────────────────────────────────────────────────────

EXTRACT_TYPO_JS = r"""
() => {
    const out = {};
    const grab = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const cs = getComputedStyle(el);
        return {
            family: cs.fontFamily,
            size_px: parseFloat(cs.fontSize),
            weight: cs.fontWeight,
            line_height: cs.lineHeight,
            letter_spacing: cs.letterSpacing,
            text_transform: cs.textTransform,
        };
    };
    out.h1 = grab("h1");
    out.h2 = grab("h2");
    out.h3 = grab("h3");
    out.body = grab("p, body");
    out.button = grab("button, [role=button], .btn");
    return out;
}
"""


async def extract_typo_from_url(url: str) -> dict:
    """Extract typography tokens via Playwright getComputedStyle (no LLM, exact values)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright not installed"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(800)
                typo = await page.evaluate(EXTRACT_TYPO_JS)
                # Compute scale ratio
                scale = {}
                if typo.get("h1") and typo.get("body"):
                    if typo["h1"].get("size_px") and typo["body"].get("size_px"):
                        scale["h1_to_body"] = round(typo["h1"]["size_px"] / typo["body"]["size_px"], 2)
                if typo.get("h2") and typo.get("body"):
                    if typo["h2"].get("size_px") and typo["body"].get("size_px"):
                        scale["h2_to_body"] = round(typo["h2"]["size_px"] / typo["body"]["size_px"], 2)
                typo["scale"] = scale
                return typo
            finally:
                await ctx.close()
                await browser.close()
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:200]}"}


# ────────────────────────────────────────────────────────────────
# Phase 1 — Spacing / Shapes / Depth / Motion (Python pur)
# ────────────────────────────────────────────────────────────────

EXTRACT_VISUAL_JS = r"""
() => {
    const out = {};

    // Spacing
    const main = document.querySelector("main, body > div, body > main") || document.body;
    const cs_main = getComputedStyle(main);
    out.spacing = {
        container_max: parseFloat(cs_main.maxWidth) || null,
        section_padding_y: cs_main.paddingTop,
        section_margin_y: cs_main.marginTop,
    };

    // Shape : sample of border-radius across buttons + cards
    const buttons = Array.from(document.querySelectorAll("button, [role=button]")).slice(0, 5);
    const cards = Array.from(document.querySelectorAll("[class*='card'], article, [class*='box']")).slice(0, 5);
    const radii = [];
    for (const el of [...buttons, ...cards]) {
        const cs = getComputedStyle(el);
        const r = parseFloat(cs.borderRadius) || 0;
        if (r > 0) radii.push(r);
    }
    out.shape = {
        radius_samples: radii,
        radius_max: radii.length ? Math.max(...radii) : 0,
        radius_dominant: radii.length ? radii.sort((a,b) => b - a)[Math.floor(radii.length / 2)] : 0,
        edge_language: radii.length === 0 ? "sharp" : (Math.max(...radii) > 100 ? "pill" : (Math.max(...radii) > 12 ? "soft" : "subtle")),
    };

    // Depth : shadow samples
    const shadowEls = Array.from(document.querySelectorAll("[class*='card'], button, article")).slice(0, 10);
    const shadows = [];
    for (const el of shadowEls) {
        const sh = getComputedStyle(el).boxShadow;
        if (sh && sh !== "none") shadows.push(sh);
    }
    out.depth = {
        shadow_samples: shadows.slice(0, 5),
        shadow_count: shadows.length,
        shadow_style: shadows.length === 0 ? "none" : (shadows.length > 5 ? "material" : "soft"),
    };

    // Motion : check for transition/animation properties
    const motionEls = Array.from(document.querySelectorAll("button, a, [class*='card']")).slice(0, 10);
    const transitions = [];
    for (const el of motionEls) {
        const t = getComputedStyle(el).transition;
        if (t && t !== "all 0s ease 0s") transitions.push(t);
    }
    out.motion = {
        transition_samples: transitions.slice(0, 5),
        transition_count: transitions.length,
    };

    return out;
}
"""


async def extract_visual_tokens(url: str) -> dict:
    """Extract spacing/shape/depth/motion tokens via Playwright (no LLM)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright not installed"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(800)
                tokens = await page.evaluate(EXTRACT_VISUAL_JS)
                return tokens
            finally:
                await ctx.close()
                await browser.close()
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:200]}"}


# ────────────────────────────────────────────────────────────────
# Phase 2 — Voice / Image direction (LLM, ciblé)
# ────────────────────────────────────────────────────────────────

VOICE_LLM_SYSTEM = """Tu extrais le brand voice tokens d'un client à partir de sa copy réelle.

Retourne JSON strict (aucun texte autour) :
{
  "tone": ["expert", "warm", "direct", "playful", "consultative", "confident", "humble"],  // pick 2-3
  "forbidden_words": ["liste de mots qui ne ressemblent PAS à ce client"],
  "preferred_cta_verbs": ["liste 3-5 verbes CTA récurrents observés"],
  "sentence_rhythm": "short|balanced|editorial",
  "voice_signature_phrase": "<une phrase qui résume la voix de la marque>"
}"""


# V29 full — Phase 2 LLM Vision : image direction + asset rules
IMAGE_DIRECTION_LLM_SYSTEM = """Tu analyses la direction artistique des images d'une marque depuis des screenshots de fold.

Tu reçois 1-3 screenshots du hero/fold de pages de la marque.

Retourne JSON strict :
{
  "photo_style": "studio|lifestyle|editorial|ugc|3d|illustration|abstract|none",
  "lighting": "natural|studio_softbox|dramatic|moody|flat|none",
  "composition": "centered|asymmetric|grid|negative_space|cluttered|hero_dominant",
  "subject_focus": "people|product|abstract|landscape|lifestyle|brand",
  "color_treatment": "saturated|muted|monochrome|gradient|filter_consistent|none",
  "image_to_text_ratio": "image_dominant|balanced|text_dominant",
  "do_not_use": ["liste 3-5 styles/patterns à NE PAS utiliser pour rester fidèle à la marque"],
  "signature_visual_motif": "<une caractéristique visuelle distinctive>"
}"""


ASSET_RULES_LLM_SYSTEM = """Tu identifies les règles visuelles à respecter pour rester fidèle à une marque.

Tu reçois :
- Visual tokens extraits (couleurs, typo, spacing, shape, depth, motion, texture)
- Voice tokens (tone, sentence rhythm)
- 1-2 screenshots du fold

Retourne JSON strict :
{
  "asset_constraints": {
    "max_colors_per_section": <int>,
    "preferred_radius_use": "buttons|cards|both|images|none",
    "shadow_usage": "minimal|elevation_levels|none|dramatic",
    "image_overlay_allowed": <bool>,
    "iconography_style": "outline|filled|duotone|illustrated|emoji|none"
  },
  "do_not": [
    "liste 5-7 patterns à éviter pour cette marque (ex: 'gradient mesh psychedelic', 'hero centré symétrique', etc.)"
  ],
  "approved_techniques": [
    "liste 3-5 techniques visuelles autorisées et fidèles à la marque"
  ],
  "brand_fidelity_anchors": [
    "liste 3-5 éléments visuels QUI DOIVENT apparaître pour que ça ressemble vraiment à la marque"
  ]
}"""


def _resize_for_anthropic(p: pathlib.Path, max_w: int = 1568, max_size_mb: float = 4.5) -> bytes:
    """Resize PNG → JPEG bytes <5MB pour respecter limite Anthropic Vision API.
    Anthropic recommande max 1568px de large, et limite hard à 5MB (base64)."""
    from PIL import Image
    import io
    img = Image.open(p)
    if img.mode != "RGB":
        img = img.convert("RGB")
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
    # JPEG q=85 → ~3-5x plus petit que PNG, généralement <2MB
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    data = buf.getvalue()
    # Si encore trop gros, ré-encoder à q=70
    if len(data) > max_size_mb * 1024 * 1024:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70, optimize=True)
        data = buf.getvalue()
    return data


async def extract_image_direction_llm(client_api, client_slug: str,
                                       screenshots: list[pathlib.Path]) -> dict:
    """LLM Vision phase : analyse direction artistique depuis screenshots fold.
    Coût : ~$0.005 par client (1 call Haiku Vision avec 1-3 images)."""
    if not screenshots:
        return {"error": "no_screenshots"}
    import base64
    images = []
    for p in screenshots[:3]:
        try:
            jpg_bytes = _resize_for_anthropic(p)
            b64 = base64.b64encode(jpg_bytes).decode()
            images.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
        except Exception:
            continue
    if not images:
        return {"error": "no_readable_screenshots"}

    user_content = list(images) + [
        {"type": "text", "text": f"Marque : {client_slug}. Analyse la direction artistique. JSON strict."}
    ]
    try:
        resp = client_api.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            temperature=0,
            system=IMAGE_DIRECTION_LLM_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = resp.content[0].text if resp.content else ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.lstrip("`")
            if text.startswith("json\n"): text = text[5:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


async def extract_asset_rules_llm(client_api, client_slug: str,
                                   visual_tokens: dict, voice_tokens: dict,
                                   screenshots: list[pathlib.Path]) -> dict:
    """LLM phase : extract asset rules from combined Phase 1 outputs + screenshots.
    Coût : ~$0.005 par client (1 call Haiku Vision)."""
    import base64
    images = []
    for p in screenshots[:2]:
        try:
            jpg_bytes = _resize_for_anthropic(p)
            b64 = base64.b64encode(jpg_bytes).decode()
            images.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
        except Exception:
            continue

    text_summary = (
        f"Marque : {client_slug}\n\n"
        f"## Visual tokens extraits (Phase 1 Python)\n{json.dumps(visual_tokens, ensure_ascii=False, indent=2)[:1500]}\n\n"
        f"## Voice tokens extraits (Phase 2 LLM)\n{json.dumps(voice_tokens, ensure_ascii=False, indent=2)[:600]}\n\n"
        f"Identifie les règles d'asset pour rester fidèle à la marque. JSON strict."
    )
    user_content = list(images) + [{"type": "text", "text": text_summary}]
    try:
        resp = client_api.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            temperature=0,
            system=ASSET_RULES_LLM_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = resp.content[0].text if resp.content else ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.lstrip("`")
            if text.startswith("json\n"): text = text[5:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


async def extract_voice_tokens_llm(client_api, client_slug: str,
                                    copy_samples: list[str]) -> dict:
    """LLM Phase 2 : voice tokens nuancés depuis copy réelle.
    Coût : ~$0.01 par client (1 call Haiku ou Sonnet)."""
    if not copy_samples:
        return {"error": "no_copy_samples"}
    user_msg = f"## Marque : {client_slug}\n\n## Copy samples (extraits H1/H2/CTA/body) :\n\n"
    for i, s in enumerate(copy_samples[:20]):
        user_msg += f"{i+1}. {s[:200]}\n"
    user_msg += "\nExtrais le voice tokens. JSON strict."
    try:
        resp = client_api.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            temperature=0,
            system=VOICE_LLM_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text if resp.content else ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.lstrip("`")
            if text.startswith("json\n"): text = text[5:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except Exception as e:
        return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


# ────────────────────────────────────────────────────────────────
# Pipeline — orchestration
# ────────────────────────────────────────────────────────────────

def find_screenshot(client_dir: pathlib.Path) -> Optional[pathlib.Path]:
    """Best home screenshot for color extraction."""
    home_dir = client_dir / "home"
    if not home_dir.exists():
        return None
    candidates = [
        home_dir / "screenshots" / "desktop_clean_full.png",
        home_dir / "screenshots" / "desktop_clean_fold.png",
        home_dir / "screenshots" / "desktop_asis_fold.png",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Fallback : any PNG in home/screenshots/
    ss_dir = home_dir / "screenshots"
    if ss_dir.exists():
        for f in ss_dir.glob("*.png"):
            return f
    return None


def collect_copy_samples(client_dir: pathlib.Path) -> list[str]:
    """Gather H1/H2/CTA/body samples from perception across all pages."""
    samples = []
    for page_dir in client_dir.iterdir():
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        # From perception or vision
        for fname in ("perception_v13.json", "vision_desktop.json"):
            f = page_dir / fname
            if not f.exists():
                continue
            try:
                d = json.loads(f.read_text())
                # Vision schema
                hero = d.get("hero") or {}
                for k in ("h1", "subtitle"):
                    val = hero.get(k)
                    if isinstance(val, dict):
                        val = val.get("text")
                    if val and len(val) > 5:
                        samples.append(val)
                ctas = hero.get("primary_cta")
                if isinstance(ctas, dict):
                    samples.append(ctas.get("text", ""))
                # Perception schema (clusters)
                clusters = d.get("clusters") or {}
                hero_clu = clusters.get("HERO") or {}
                for k in ("h1", "subtitle"):
                    v = hero_clu.get(k)
                    if v and len(v) > 5:
                        samples.append(v)
            except Exception:
                continue
    # Dedup + cap
    samples = list(dict.fromkeys(s for s in samples if s))[:30]
    return samples


def extract_brand_dna(client: str, anthropic_client=None,
                      run_llm_phase: bool = True) -> dict:
    """Full Brand DNA extraction pipeline."""
    import asyncio
    client_dir = CAPTURES / client
    if not client_dir.exists():
        return {"error": f"no captures for {client}"}

    # Resolve home URL
    home_cap = client_dir / "home" / "capture.json"
    home_url = None
    if home_cap.exists():
        try:
            d = json.loads(home_cap.read_text())
            home_url = d.get("url") or (d.get("meta") or {}).get("url")
        except Exception:
            pass

    out: dict = {
        "version": "v29.prep.1.0",
        "client": client,
        "home_url": home_url,
        "visual_tokens": {},
        "voice_tokens": {},
        "asset_rules": {},
        "method": "python_phase1+llm_phase2_hybrid",
    }

    # Phase 1A — Colors
    screenshot = find_screenshot(client_dir)
    if screenshot:
        out["visual_tokens"]["colors"] = extract_colors_from_screenshot(screenshot)
        print(f"  ✓ colors extracted (screenshot {screenshot.name})")
    else:
        out["visual_tokens"]["colors"] = {"error": "no_screenshot_found"}

    # Phase 1B — Typography + visual tokens (live Playwright)
    if home_url:
        try:
            typo = asyncio.run(extract_typo_from_url(home_url))
            out["visual_tokens"]["typography"] = typo
            print(f"  ✓ typography extracted")
            visual = asyncio.run(extract_visual_tokens(home_url))
            out["visual_tokens"].update(visual)
            print(f"  ✓ visual tokens extracted (spacing/shape/depth/motion)")
        except Exception as e:
            out["visual_tokens"]["error"] = f"{type(e).__name__}:{str(e)[:120]}"

    # Phase 2 — Voice tokens (LLM)
    if run_llm_phase and anthropic_client:
        copy_samples = collect_copy_samples(client_dir)
        if copy_samples:
            out["voice_tokens"] = asyncio.run(
                extract_voice_tokens_llm(anthropic_client, client, copy_samples)
            )
            print(f"  ✓ voice tokens extracted (LLM, {len(copy_samples)} copy samples)")
        else:
            out["voice_tokens"] = {"error": "no_copy_samples"}

        # V29 full — image_direction + asset_rules (LLM Vision)
        # Collect fold screenshots from up to 3 pages
        fold_screenshots: list[pathlib.Path] = []
        for page_dir in client_dir.iterdir():
            if not page_dir.is_dir() or page_dir.name.startswith("_"):
                continue
            ss_dir = page_dir / "screenshots"
            if not ss_dir.exists():
                continue
            for fname in ("desktop_clean_fold.png", "desktop_clean_full.png", "spatial_fold_desktop.png"):
                f = ss_dir / fname
                if f.exists():
                    fold_screenshots.append(f)
                    break
            if len(fold_screenshots) >= 3:
                break

        if fold_screenshots:
            out["image_direction"] = asyncio.run(
                extract_image_direction_llm(anthropic_client, client, fold_screenshots)
            )
            print(f"  ✓ image_direction extracted (LLM Vision, {len(fold_screenshots)} screenshots)")
            out["asset_rules"] = asyncio.run(
                extract_asset_rules_llm(
                    anthropic_client, client, out["visual_tokens"],
                    out.get("voice_tokens", {}), fold_screenshots[:2]
                )
            )
            print(f"  ✓ asset_rules extracted (LLM Vision)")
        else:
            out["image_direction"] = {"error": "no_fold_screenshots"}
            out["asset_rules"] = {"error": "no_fold_screenshots"}
    else:
        out["voice_tokens"] = {"status": "skipped (--no-llm)"}
        out["image_direction"] = {"status": "skipped (--no-llm)"}
        out["asset_rules"] = {"status": "skipped (--no-llm)"}

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM phase 2 (Python pur)")
    args = ap.parse_args()

    anthropic_client = None
    if not args.no_llm:
        # Import lazily
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        try:
            from reco_enricher_v13_api import _load_dotenv_if_needed, _get_api_client
            anthropic_client = _get_api_client()
        except Exception as e:
            print(f"⚠️ LLM disabled: {e}")

    print(f"→ Brand DNA extraction : {args.client}")
    result = extract_brand_dna(args.client, anthropic_client, run_llm_phase=not args.no_llm)

    out_path = CAPTURES / args.client / "brand_dna.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    tmp.replace(out_path)
    print(f"\n→ Saved : {out_path}")
    print(f"  {len(result.get('visual_tokens', {}))} visual token groups, "
          f"{'voice OK' if not result.get('voice_tokens', {}).get('error') else 'voice FAIL'}")


if __name__ == "__main__":
    main()
