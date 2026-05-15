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

import pathlib
import re
import time

from .legacy_lab_adapters import LegacyLabUnavailable, apply_fix_html_runtime

from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

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
    import anthropic
    import base64
    api = anthropic.Anthropic()

    # Build multimodal content
    content_blocks = []
    images_loaded = 0
    if image_paths:
        for img_path in image_paths:
            if not img_path.exists():
                if verbose:
                    logger.info(f"  ⚠️  Image not found, skip: {img_path}")
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
        logger.info(f"  → Sonnet MULTIMODAL (model={model}, prompt={sz} chars, images={images_loaded}, max_tokens={max_tokens}, T={temperature})...")

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
        logger.info(f"  ← Sonnet : in={msg.usage.input_tokens} out={msg.usage.output_tokens} ({dt:.1f}s) html={len(html)} chars")

    if not re.search(r"<!DOCTYPE\s+html>", html, re.IGNORECASE):
        if verbose:
            logger.info(f"  ⚠️  No <!DOCTYPE html> found. First 300 chars: {html[:300]}")

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
        logger.info(f"  → Sonnet single_pass (model={model}, prompt={sz} chars, max_tokens={max_tokens}, T={temperature})...")

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
        logger.info(f"  ← Sonnet : in={msg.usage.input_tokens} out={msg.usage.output_tokens} ({dt:.1f}s) html={len(html)} chars")

    # Sanity check : doit ressembler à du HTML
    if not re.search(r"<!DOCTYPE\s+html>", html, re.IGNORECASE):
        if verbose:
            logger.info(f"  ⚠️  No <!DOCTYPE html> found. First 300 chars: {html[:300]}")

    return {
        "html": html,
        "tokens_in": msg.usage.input_tokens,
        "tokens_out": msg.usage.output_tokens,
        "wall_seconds": round(dt, 1),
        "model": model,
        "raw_response_chars": len(raw),
    }


def call_sonnet_messages(
    system_messages: list[dict],
    user_turns_seq: list[dict],
    image_paths: list[pathlib.Path] | None = None,
    model: str = SONNET_MODEL,
    max_tokens: int = 8000,
    temperature: float = 0.7,
    verbose: bool = True,
) -> dict:
    """Sonnet 4.5 call using the V26.AG dialogue architecture (issue #13).

    Accepts the new shape produced by ``build_persona_narrator_prompt`` :

      * ``system_messages`` — list of ``{type, text, cache_control}`` blocks.
        Static blocks carry ``cache_control: ephemeral`` so the Anthropic
        SDK writes/reads the prefix cache natively (1.25× on first call,
        0.1× on subsequent identical-prefix calls).
      * ``user_turns_seq`` — pre-filled dialogue
        ``[{role, content}, ...]``. The LAST turn is the generation
        kickoff (already built by ``build_persona_narrator_prompt`` —
        the function injects the brief / mission as the final user turn).
      * ``image_paths`` — optional list of PNG/JPG to attach to the LAST
        user turn as base64 image content blocks (client screenshots +
        golden refs for Sprint AD-4 multimodal vision).

    The SDK handles the ``prompt-caching`` beta natively; no extra header
    is required for ``cache_control`` on Sonnet 4.5.

    Returns: dict {html, tokens_in, tokens_out, tokens_cached_read,
                   tokens_cached_write, wall_seconds, model, n_images,
                   raw_response_chars}.
    """
    import anthropic
    import base64

    api = anthropic.Anthropic()

    # Build messages array: copy user_turns_seq, then attach images to the
    # LAST user turn (vision context goes with the kickoff turn so the
    # model sees the brief AND the screenshots together).
    messages: list[dict] = []
    images_loaded = 0
    for i, turn in enumerate(user_turns_seq):
        if (
            i == len(user_turns_seq) - 1
            and turn["role"] == "user"
            and image_paths
        ):
            content_blocks: list[dict] = []
            for img_path in image_paths:
                if not img_path.exists():
                    if verbose:
                        logger.info(f"  ⚠️  Image not found, skip: {img_path}")
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
            content_blocks.append({"type": "text", "text": turn["content"]})
            messages.append({"role": "user", "content": content_blocks})
        else:
            messages.append({"role": turn["role"], "content": turn["content"]})

    if verbose:
        sys_chars = sum(len(b["text"]) for b in system_messages)
        user_chars = sum(
            len(t["content"]) if isinstance(t["content"], str) else 0
            for t in user_turns_seq
        )
        cached_blocks = sum(1 for b in system_messages if "cache_control" in b)
        logger.info(
            f"  → Sonnet messages (model={model}, system={sys_chars}c [{cached_blocks} cached], "
            f"user_turns={len(user_turns_seq)} ({user_chars}c), images={images_loaded}, "
            f"max_tokens={max_tokens}, T={temperature})..."
        )

    t0 = time.time()
    msg = api.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_messages,
        messages=messages,
    )
    dt = time.time() - t0

    raw = msg.content[0].text
    html = _strip_html_fences(raw)

    usage = msg.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0

    if verbose:
        cache_hint = ""
        if cache_read or cache_write:
            cache_hint = f" cache_read={cache_read} cache_write={cache_write}"
        logger.info(
            f"  ← Sonnet : in={usage.input_tokens}{cache_hint} out={usage.output_tokens} "
            f"({dt:.1f}s) html={len(html)} chars"
        )

    if not re.search(r"<!DOCTYPE\s+html>", html, re.IGNORECASE):
        if verbose:
            logger.info(f"  ⚠️  No <!DOCTYPE html> found. First 300 chars: {html[:300]}")

    return {
        "html": html,
        "tokens_in": usage.input_tokens,
        "tokens_out": usage.output_tokens,
        "tokens_cached_read": cache_read,
        "tokens_cached_write": cache_write,
        "wall_seconds": round(dt, 1),
        "model": model,
        "n_images": images_loaded,
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
            logger.info(f"  ⚠️  fix_html_runtime unavailable, skip post-process: {exc}")
        return html, {"applied": False, "reason": str(exc)}
    if verbose:
        n_fixes = len(info.get("fixes_applied", []))
        n_warnings = len(info.get("warnings", []))
        logger.info(f"  ✓ fix_html_runtime adapter: {n_fixes} fixes, {n_warnings} warnings")
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
    logger.info(f"\n✓ HTML saved : {args.out}")
    logger.info(f"  Tokens : in={out['tokens_in']} out={out['tokens_out']}")
    logger.info(f"  Wall   : {out['wall_seconds']}s")
    logger.info(f"  Fixes  : {out['fixes']}")
