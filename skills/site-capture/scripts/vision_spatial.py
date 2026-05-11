#!/usr/bin/env python3
"""
vision_spatial.py — V20.CAPTURE C1' : Claude Vision Haiku 4.5 comme extracteur spatial.

Remplace Tesseract + semantic_mapper. Envoie le screenshot clean_full à Haiku 4.5
multimodal avec un schema JSON strict, reçoit en retour une extraction structurée
du layout avec bboxes :
  - hero (h1, subtitle, primary_cta, secondary_ctas, hero_image, social_proof_in_fold)
  - utility_banner (promo/compliance/cookie)
  - nav (items du header nav)
  - below_fold sections (social_proof, features, pricing, faq, footer signals)
  - fold_readability_score
  - visual_issues_flagged (low contrast, excessive ctas, text over image, etc.)

Coût estimé : ~$0.003 par image Haiku 4.5. Fleet 291 pages × 2 viewports = ~$1.75 total.

Usage :
    python3 vision_spatial.py --client japhy --page home --viewport desktop
    python3 vision_spatial.py --batch --max N
    python3 vision_spatial.py --batch --force    # re-run even if vision_*.json exists

Prérequis : pip install anthropic pillow
           ANTHROPIC_API_KEY dans .env

v1.0 — 2026-04-20
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import pathlib
import sys
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
from growthcro.config import config
CAPTURES = ROOT / "data" / "captures"
VISION_CACHE = ROOT / "data" / ".vision_cache"  # MD5-keyed Vision response cache (V24 axe 2)

# Load .env — override if env var is empty (Claude Code exports ANTHROPIC_API_KEY="")
MODEL = "claude-haiku-4-5-20251001"  # Haiku 4.5 multimodal
MAX_TOKENS = 4096

# Vision strategy :
#   - FOLD screenshot (viewport initial, ~900-1200px tall) → hero extraction premium
#   - Keep resolution high enough for Vision to read styled CTAs (white text on dark bg)
#   - Cap at 1600px wide, preserve aspect (no aggressive downsize)
# The below_fold sections are handled by spatial_v10 DOM dump, not Vision.
MAX_IMAGE_SIZE = {
    "desktop": (1600, 2000),
    "mobile": (500, 2000),
    "tablet": (1200, 2000),
}


# ────────────────────────────────────────────────────────────────
# Vision prompt & schema
# ────────────────────────────────────────────────────────────────

VISION_SYSTEM = """You are a CRO (conversion rate optimization) visual analyst extracting the structural layout of a landing page screenshot.

Your job is PURE EXTRACTION with strict bounding boxes (bbox). Do NOT interpret, judge, or recommend. Do NOT hallucinate. If a field is not visible, return null.

Coordinates:
- Origin (0,0) = top-left of the image.
- All bboxes in pixels of the IMAGE AS SHOWN TO YOU (not the original device-pixel screenshot).
- Format: {"x": int, "y": int, "w": int, "h": int}.

Rules:
- "hero" = the ABOVE-THE-FOLD section (first viewport the user sees, typically y=0 to ~900 on desktop).
- "utility_banner" = thin promo/cookie/compliance strip at y=0 (e.g., "-50% offer", cookie bar). It is NOT the primary CTA even if it contains a link.
- "primary_cta" in hero = the dominant action button in the hero, visually isolated, typically large/colored. Exclude nav links, utility banner, and secondary CTAs.
- "secondary_ctas" = other clickable elements in hero (e.g., "Learn more", video play, variants).
- "social_proof_in_fold" = trust signals visible in hero (Trustpilot, star ratings, logos bar, customer count).
- "below_fold_sections" = structural sections below fold (list them with bbox and type).

Accuracy over ambition: if you are not confident about an element, set confidence < 0.7 and explain in notes.
"""

VISION_USER_TMPL = """Analyze this {viewport} screenshot (size {w}×{h}) of a web page.

Return STRICTLY this JSON (no markdown, no comment). Be thorough but precise.

{{
  "image_size": {{"w": {w}, "h": {h}}},
  "viewport": "{viewport}",

  "hero": {{
    "bbox": {{"x": 0, "y": 0, "w": 0, "h": 0}},
    "h1": {{"text": "...", "bbox": {{...}}, "confidence": 0.0}} | null,
    "subtitle": {{"text": "...", "bbox": {{...}}, "confidence": 0.0}} | null,
    "primary_cta": {{
      "text": "...",
      "bbox": {{...}},
      "is_text_visible_in_screenshot": true,
      "style": {{"fill": "solid|outline|ghost", "color_family": "dark|brand|light", "rounded": true}},
      "confidence": 0.0
    }} | null,
    "secondary_ctas": [
      {{"text": "...", "bbox": {{...}}, "kind": "button|link|video", "confidence": 0.0}}
    ],
    "hero_image": {{"bbox": {{...}}, "description": "...", "confidence": 0.0}} | null,
    "social_proof_in_fold": {{"present": true, "type": "trustpilot|stars|logos|count|testimonial|none", "bbox": {{...}}, "snippet": "..."}} | null
  }},

  "utility_banner": {{
    "present": true,
    "bbox": {{...}},
    "text": "...",
    "type": "promo|cookie|compliance|announcement|none",
    "position": "top|bottom"
  }} | null,

  "nav": {{
    "bbox": {{...}},
    "items": [{{"text": "...", "bbox": {{...}}}}],
    "has_logo": true,
    "has_search": false,
    "has_cart": false,
    "has_cta_button": true
  }} | null,

  "below_fold_sections": [
    {{"type": "social_proof|features|pricing|faq|testimonials|footer|how_it_works|benefits|cta_band|other", "bbox": {{...}}, "headline": "...", "summary": "...", "confidence": 0.0}}
  ],

  "fold_readability": {{
    "score_1_to_5": 0,
    "issues": ["low_contrast_cta", "text_over_busy_image", "too_many_ctas", "unclear_hierarchy", "..."]
  }},

  "visual_issues_flagged": [
    {{"type": "...", "bbox": {{...}}, "description": "..."}}
  ],

  "model_notes": "..."
}}

IMPORTANT:
- If utility banner is present (y=0 promo/cookie strip), put it in `utility_banner`, NOT in `hero.primary_cta`.
- The primary_cta must be the dominant hero action, visually isolated, typically within the first 900px of height.
- Return ONLY the JSON object. No markdown fences, no preamble."""


# ────────────────────────────────────────────────────────────────
# Image preparation
# ────────────────────────────────────────────────────────────────

def prepare_image(img_path: pathlib.Path, viewport: str) -> tuple[str, int, int, float]:
    """
    Resize image to fit Vision budget. Return (base64_data, new_w, new_h, scale_to_original).

    scale_to_original : factor to multiply Vision bboxes by to get original image coords.
    """
    from PIL import Image

    max_w, max_h = MAX_IMAGE_SIZE.get(viewport, MAX_IMAGE_SIZE["desktop"])

    with Image.open(img_path) as im:
        orig_w, orig_h = im.size
        # Compute scale to fit both constraints
        scale_w = max_w / orig_w if orig_w > max_w else 1.0
        scale_h = max_h / orig_h if orig_h > max_h else 1.0
        scale = min(scale_w, scale_h, 1.0)

        if scale < 1.0:
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            im = im.resize((new_w, new_h), Image.LANCZOS)
        else:
            new_w, new_h = orig_w, orig_h

        # Convert to RGB for JPEG (smaller than PNG for API)
        if im.mode != "RGB":
            im = im.convert("RGB")

        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=85, optimize=True)
        b64 = base64.standard_b64encode(buf.getvalue()).decode("ascii")

    # scale_to_original : Vision returns coords in new_w/new_h space; multiply by 1/scale to get original image coords
    scale_back = 1.0 / scale if scale > 0 else 1.0
    return b64, new_w, new_h, scale_back


def scale_bbox_back(bbox: Optional[dict], factor: float) -> Optional[dict]:
    if not isinstance(bbox, dict):
        return bbox
    if factor == 1.0:
        return bbox
    try:
        return {
            "x": int(round(bbox.get("x", 0) * factor)),
            "y": int(round(bbox.get("y", 0) * factor)),
            "w": int(round(bbox.get("w", 0) * factor)),
            "h": int(round(bbox.get("h", 0) * factor)),
        }
    except Exception:
        return bbox


def recursively_scale_bboxes(obj, factor: float):
    """Walk the Vision response dict, multiplying any bbox by factor."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k == "bbox" and isinstance(v, dict) and "x" in v:
                obj[k] = scale_bbox_back(v, factor)
            else:
                recursively_scale_bboxes(v, factor)
    elif isinstance(obj, list):
        for item in obj:
            recursively_scale_bboxes(item, factor)


# ────────────────────────────────────────────────────────────────
# V24 axe 2 — MD5-keyed Vision cache
# ────────────────────────────────────────────────────────────────
# Skip API call if the (image_bytes + prompt + viewport + model) tuple was already
# resolved. Saves ~$5-8 per fleet re-run when screenshots are unchanged. Cache key
# includes prompt hash so editing VISION_SYSTEM/USER_TMPL automatically invalidates
# all entries (no stale results).

def _vision_cache_key(image_b64: str, viewport: str, img_w: int, img_h: int) -> str:
    """Stable key over (image content, prompt template, viewport+dims, model)."""
    user_prompt = VISION_USER_TMPL.format(viewport=viewport, w=img_w, h=img_h)
    h = hashlib.md5()
    h.update(image_b64.encode())
    h.update(b"|")
    h.update(VISION_SYSTEM.encode())
    h.update(b"|")
    h.update(user_prompt.encode())
    h.update(b"|")
    h.update(MODEL.encode())
    return h.hexdigest()


def _vision_cache_load(key: str) -> Optional[dict]:
    p = VISION_CACHE / f"{key}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        # Mark hit for caller traceability
        d["_cache_hit"] = True
        return d
    except Exception:
        return None


def _vision_cache_store(key: str, value: dict) -> None:
    try:
        VISION_CACHE.mkdir(parents=True, exist_ok=True)
        # Atomic write
        tmp = VISION_CACHE / f"{key}.json.tmp"
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
        tmp.replace(VISION_CACHE / f"{key}.json")
    except Exception as e:
        # Cache failure is non-fatal — just log
        print(f"  ⚠️ vision_cache store failed: {e}", file=sys.stderr)


# ────────────────────────────────────────────────────────────────
# Vision call
# ────────────────────────────────────────────────────────────────

def call_vision(b64_image: str, viewport: str, img_w: int, img_h: int,
                client, retries: int = 2, use_cache: bool = True) -> Optional[dict]:
    """Call Haiku Vision with retries on JSON parse failure.
    V24 axe 2: hash-based cache (skip API if same image+prompt already analyzed)."""
    if use_cache:
        cache_key = _vision_cache_key(b64_image, viewport, img_w, img_h)
        cached = _vision_cache_load(cache_key)
        if cached is not None:
            return cached
    user_prompt = VISION_USER_TMPL.format(viewport=viewport, w=img_w, h=img_h)

    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=VISION_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": b64_image,
                                },
                            },
                            {"type": "text", "text": user_prompt},
                        ],
                    }
                ],
            )

            text = resp.content[0].text if resp.content else ""
            text = text.strip()
            if text.startswith("```"):
                # Strip markdown fences if present
                text = text.lstrip("`")
                if text.startswith("json\n"):
                    text = text[5:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            parsed = json.loads(text)
            parsed["_api_usage"] = {
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            }
            parsed["_cache_hit"] = False
            # Store cache for next run
            if use_cache:
                _vision_cache_store(cache_key, parsed)
            return parsed
        except json.JSONDecodeError as e:
            last_err = f"JSONDecodeError: {e}"
            if attempt < retries:
                time.sleep(1.0)
                continue
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt < retries and ("rate" in str(e).lower() or "overloaded" in str(e).lower()):
                time.sleep(2.0 * (attempt + 1))
                continue
            break

    print(f"  ❌ Vision call failed: {last_err}", file=sys.stderr)
    return None


# ────────────────────────────────────────────────────────────────
# Main per-page
# ────────────────────────────────────────────────────────────────

def find_screenshot(page_dir: pathlib.Path, viewport: str) -> Optional[pathlib.Path]:
    """
    Prefer FOLD (viewport initial) for Vision because:
    - fullpage is too tall, aggressive resize destroys text readability
    - fold contains everything Vision needs for hero/CTA/banner disambiguation
    - below_fold sections use DOM spatial dump instead
    """
    ss_dir = page_dir / "screenshots"
    candidates = [
        ss_dir / f"{viewport}_clean_fold.png",     # v20 capture_v2 output (preferred)
        ss_dir / f"spatial_fold_{viewport}.png",   # v17 ghost_capture output
        ss_dir / f"{viewport}_asis_fold.png",      # fallback if clean failed
        ss_dir / f"{viewport}_clean_full.png",     # last resort (will be aggressively downsized)
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def process_page(client_name: str, page: str, viewport: str,
                 anthropic_client, force: bool = False) -> Optional[dict]:
    page_dir = CAPTURES / client_name / page
    out_path = page_dir / f"vision_{viewport}.json"
    if out_path.exists() and not force:
        print(f"⏭  {client_name}/{page}/{viewport} déjà traité")
        return json.loads(out_path.read_text())

    img_path = find_screenshot(page_dir, viewport)
    if not img_path:
        print(f"❌ aucun screenshot {viewport} pour {client_name}/{page}", file=sys.stderr)
        return None

    print(f"→ Vision {client_name}/{page}/{viewport} ({img_path.name})...")
    t0 = time.time()
    b64, new_w, new_h, scale_back = prepare_image(img_path, viewport)
    print(f"  resized to {new_w}×{new_h} (scale_back={scale_back:.3f})")

    vision = call_vision(b64, viewport, new_w, new_h, anthropic_client)
    if not vision:
        return None

    # Scale bboxes back to original image coordinates
    if scale_back != 1.0:
        recursively_scale_bboxes(vision, scale_back)

    vision["_meta"] = {
        "screenshot": img_path.name,
        "viewport": viewport,
        "resized_to": {"w": new_w, "h": new_h},
        "scale_applied_to_bboxes": scale_back,
        "model": MODEL,
        "timing_s": round(time.time() - t0, 2),
    }

    out_path.write_text(json.dumps(vision, ensure_ascii=False, indent=2))

    # Quick summary (robust to Vision returning unexpected types: list instead of dict, None, etc.)
    def _safe_text(obj, key="text", limit=40):
        if isinstance(obj, dict):
            v = obj.get(key)
            if isinstance(v, str):
                return v[:limit]
        return "NONE"

    hero = vision.get("hero") if isinstance(vision.get("hero"), dict) else {}
    cta_obj = hero.get("primary_cta") if isinstance(hero.get("primary_cta"), dict) else {}
    banner_obj = vision.get("utility_banner") if isinstance(vision.get("utility_banner"), dict) else {}
    h1_obj = hero.get("h1") if isinstance(hero.get("h1"), dict) else {}
    usage = vision.get("_api_usage", {})
    try:
        print(f"  ✓ primary_cta={_safe_text(cta_obj)!r}")
        print(f"    h1={_safe_text(h1_obj, limit=50)!r}")
        print(f"    utility_banner={_safe_text(banner_obj)!r}")
        print(f"    {usage.get('input_tokens', 0)} in / {usage.get('output_tokens', 0)} out tokens ({vision['_meta']['timing_s']}s)")
    except Exception as e:
        print(f"  ✓ (summary print skipped: {e})")
    return vision


def batch(anthropic_client, force: bool = False, max_n: Optional[int] = None,
          concurrent: int = 10) -> None:
    """
    Parallelized batch with ThreadPoolExecutor.
    Collects tasks (client, page, viewport), submits up to `concurrent` at once.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    clients = [d for d in CAPTURES.iterdir() if d.is_dir() and not d.name.startswith("_")]
    tasks = []
    for client_dir in sorted(clients):
        for page_dir in client_dir.iterdir():
            if not page_dir.is_dir() or page_dir.name == "screenshots":
                continue
            for viewport in ("desktop", "mobile"):
                if not find_screenshot(page_dir, viewport):
                    continue
                out = page_dir / f"vision_{viewport}.json"
                if out.exists() and not force:
                    continue
                tasks.append((client_dir.name, page_dir.name, viewport))

    if max_n:
        tasks = tasks[:max_n]

    total = len(tasks)
    print(f"═══ {total} pages × viewports to process with {concurrent} concurrent ═══")
    if not total:
        return

    ok = 0
    fail = 0
    total_in = 0
    total_out = 0
    with ThreadPoolExecutor(max_workers=concurrent) as ex:
        futures = {
            ex.submit(process_page, c, p, v, anthropic_client, force=force): (c, p, v)
            for c, p, v in tasks
        }
        for i, fut in enumerate(as_completed(futures), 1):
            c, p, v = futures[fut]
            try:
                r = fut.result()
                if r:
                    ok += 1
                    usage = r.get("_api_usage", {})
                    total_in += usage.get("input_tokens", 0)
                    total_out += usage.get("output_tokens", 0)
                else:
                    fail += 1
            except Exception as e:
                print(f"❌ {c}/{p}/{v}: {e}", file=sys.stderr)
                fail += 1
            if i % 10 == 0 or i == total:
                cost = (total_in * 1.0 + total_out * 5.0) / 1_000_000
                print(f"  progress {i}/{total}  ok={ok}  fail={fail}  cost=${cost:.3f}")

    cost = (total_in * 1.0 + total_out * 5.0) / 1_000_000  # Haiku 4.5 : $1/M in, $5/M out
    print(f"\n═══ Batch Vision: {ok} ok / {fail} fail — tokens {total_in}↑ / {total_out}↓ — cost ${cost:.3f} ═══")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--viewport", default="desktop", choices=["desktop", "mobile", "tablet"])
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max", type=int, help="Max pages in batch (for testing)")
    args = ap.parse_args()

    try:
        import anthropic
    except ImportError:
        print("❌ pip install anthropic pillow", file=sys.stderr)
        sys.exit(1)

    api_key = config.anthropic_api_key()
    if not api_key or api_key.startswith("sk-ant-ROTATE"):
        print("❌ ANTHROPIC_API_KEY manquant dans .env", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if args.batch:
        batch(client, force=args.force, max_n=args.max)
        return

    if not args.client or not args.page:
        ap.error("--client and --page required (or use --batch)")
    r = process_page(args.client, args.page, args.viewport, client, force=args.force)
    if not r:
        sys.exit(1)


if __name__ == "__main__":
    main()
