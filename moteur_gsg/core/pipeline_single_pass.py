"""Pipeline Single-Pass V26.AA Sprint 3.

1 call Sonnet → HTML (default Mode 1). Pas de pipeline 4 stages, pas de mega-prompt
sursaturé. La leçon empirique du 2026-05-03 : gsg_minimal v1 (1 prompt 3K + règle
renoncement) bat V26.Z BESTOF (4 stages, 3500 LoC) de +4pts humanlike avec
coût ÷75.

Composants :
  - call_sonnet(system, user)  : appel Anthropic, retour HTML brut
  - apply_runtime_fixes(html)  : patch bugs courants (counter à 0, reveal sans JS,
                                  opacity 0 sans animation) — réutilise V26.Z P0
                                  fix_html_runtime.py via import dynamique
  - single_pass(system, user)  : orchestre les 2 — 1 call + post-process auto

Coût attendu : ~$0.10-0.15 par run (input ~3K tokens + output ~6K tokens Sonnet 4.5).
Wall : ~30-90s.
"""
from __future__ import annotations

import os
import pathlib
import re
import time
from typing import Any

from .legacy_lab_adapters import LegacyLabUnavailable, apply_fix_html_runtime

ROOT = pathlib.Path(__file__).resolve().parents[2]
SONNET_MODEL = "claude-sonnet-4-5-20250929"


def _strip_html_fences(raw: str) -> str:
    """Sonnet renvoie parfois ```html ... ``` malgré l'instruction. Strip."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("html\n"):
            text = text[5:]
        elif text.startswith("html"):
            text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def call_sonnet_multimodal(
    system_prompt: str,
    user_message: str,
    image_paths: list[pathlib.Path] | None = None,
    model: str = SONNET_MODEL,
    max_tokens: int = 8000,
    temperature: float = 0.7,
    verbose: bool = True,
) -> dict:
    """Sonnet 4.5 multimodal — accepte text + images (PNG/JPG) en input.

    Phase 2.1 V26.AC Sprint F : Sonnet VOIT le client au lieu de coder à l'aveugle.

    Args:
      image_paths: list de Path PNG/JPG à donner en INPUT VISION. Max 5 images
                   recommandé (token budget). Sonnet 4.5 accepte jusqu'à 100.

    Returns: dict {html, tokens_in, tokens_out, wall_seconds, model, n_images}
    """
    import anthropic, base64
    api = anthropic.Anthropic()

    # Build multimodal content
    content_blocks = []
    images_loaded = 0
    if image_paths:
        for img_path in image_paths:
            if not img_path.exists():
                if verbose:
                    print(f"  ⚠️  Image not found, skip: {img_path}", flush=True)
                continue
            ext = img_path.suffix.lower().lstrip(".")
            media_type = "image/png" if ext == "png" else f"image/{ext}"
            with open(img_path, "rb") as f:
                img_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": img_b64},
            })
            images_loaded += 1

    content_blocks.append({"type": "text", "text": user_message})

    if verbose:
        sz = len(system_prompt) + len(user_message)
        print(f"  → Sonnet MULTIMODAL (model={model}, prompt={sz} chars, images={images_loaded}, max_tokens={max_tokens}, T={temperature})...", flush=True)

    t0 = time.time()
    msg = api.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": content_blocks}],
    )
    dt = time.time() - t0

    raw = msg.content[0].text
    html = _strip_html_fences(raw)

    if verbose:
        print(f"  ← Sonnet : in={msg.usage.input_tokens} out={msg.usage.output_tokens} ({dt:.1f}s) html={len(html)} chars", flush=True)

    if not re.search(r"<!DOCTYPE\s+html>", html, re.IGNORECASE):
        if verbose:
            print(f"  ⚠️  No <!DOCTYPE html> found. First 300 chars: {html[:300]}", flush=True)

    return {
        "html": html,
        "tokens_in": msg.usage.input_tokens,
        "tokens_out": msg.usage.output_tokens,
        "wall_seconds": round(dt, 1),
        "model": model,
        "n_images": images_loaded,
        "raw_response_chars": len(raw),
    }


def call_sonnet(
    system_prompt: str,
    user_message: str,
    model: str = SONNET_MODEL,
    max_tokens: int = 8000,
    temperature: float = 0.7,
    verbose: bool = True,
) -> dict:
    """Appel Sonnet pour générer le HTML.

    Returns: dict {html, tokens_in, tokens_out, wall_seconds, model}
    """
    import anthropic
    api = anthropic.Anthropic()

    if verbose:
        sz = len(system_prompt) + len(user_message)
        print(f"  → Sonnet single_pass (model={model}, prompt={sz} chars, max_tokens={max_tokens}, T={temperature})...", flush=True)

    t0 = time.time()
    msg = api.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    dt = time.time() - t0

    raw = msg.content[0].text
    html = _strip_html_fences(raw)

    if verbose:
        print(f"  ← Sonnet : in={msg.usage.input_tokens} out={msg.usage.output_tokens} ({dt:.1f}s) html={len(html)} chars", flush=True)

    # Sanity check : doit ressembler à du HTML
    if not re.search(r"<!DOCTYPE\s+html>", html, re.IGNORECASE):
        if verbose:
            print(f"  ⚠️  No <!DOCTYPE html> found. First 300 chars: {html[:300]}", flush=True)

    return {
        "html": html,
        "tokens_in": msg.usage.input_tokens,
        "tokens_out": msg.usage.output_tokens,
        "wall_seconds": round(dt, 1),
        "model": model,
        "raw_response_chars": len(raw),
    }


def apply_runtime_fixes(html: str, verbose: bool = True) -> tuple[str, dict]:
    """Patch les bugs runtime courants via the explicit legacy-lab adapter.

    Bugs ciblés (cf V26.Z P0) :
      - Counter à 0 (compteur animé qui démarre à 0 et reste à 0)
      - Reveal-pattern sans JS (sections invisibles avec opacity:0 + transform)
      - opacity 0 sans animation associée

    Returns: (html_fixed, fixes_applied_dict)
    """
    try:
        fixed, info = apply_fix_html_runtime(html, inject_js=False)
    except LegacyLabUnavailable as exc:
        if verbose:
            print(f"  ⚠️  fix_html_runtime unavailable, skip post-process: {exc}", flush=True)
        return html, {"applied": False, "reason": str(exc)}
    if verbose:
        n_fixes = len(info.get("fixes_applied", []))
        n_warnings = len(info.get("warnings", []))
        print(f"  ✓ fix_html_runtime adapter: {n_fixes} fixes, {n_warnings} warnings", flush=True)
    return fixed, {"applied": True, **info}


def single_pass(
    system_prompt: str,
    user_message: str,
    model: str = SONNET_MODEL,
    max_tokens: int = 8000,
    temperature: float = 0.7,
    apply_fixes: bool = True,
    verbose: bool = True,
) -> dict:
    """Orchestre 1 call Sonnet + post-process auto.

    Returns: {
        html, html_raw, tokens_in, tokens_out, wall_seconds, model,
        fixes: dict des bugs runtime patchés
    }
    """
    result = call_sonnet(
        system_prompt, user_message,
        model=model, max_tokens=max_tokens, temperature=temperature,
        verbose=verbose,
    )
    html_raw = result["html"]

    if apply_fixes:
        html_fixed, fixes_info = apply_runtime_fixes(html_raw, verbose=verbose)
    else:
        html_fixed, fixes_info = html_raw, {"applied": False, "reason": "skipped"}

    return {
        "html": html_fixed,
        "html_raw": html_raw,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "wall_seconds": result["wall_seconds"],
        "model": result["model"],
        "fixes": fixes_info,
        "html_chars_raw": len(html_raw),
        "html_chars_fixed": len(html_fixed),
    }


if __name__ == "__main__":
    # CLI smoke : appel Sonnet réel sur un mini-prompt
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="Tu es un expert HTML. Génère un HTML simple.")
    ap.add_argument("--user", default="Crée une page hello world avec un H1 et un paragraphe.")
    ap.add_argument("--out", default="/tmp/single_pass_test.html")
    args = ap.parse_args()
    out = single_pass(args.system, args.user, max_tokens=2000)
    pathlib.Path(args.out).write_text(out["html"])
    print(f"\n✓ HTML saved : {args.out}")
    print(f"  Tokens : in={out['tokens_in']} out={out['tokens_out']}")
    print(f"  Wall   : {out['wall_seconds']}s")
    print(f"  Fixes  : {out['fixes']}")
