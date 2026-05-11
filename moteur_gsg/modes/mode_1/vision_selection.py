"""Sprint F V26.AC + AD-4 V26.AD+ — vision input picker for Sonnet.

``_select_vision_screenshots`` picks up to ``max_images`` screenshots of
the **client** (preferring fold variants under Anthropic's 8000 px input
height limit) plus up to ``max_golden_inspirations`` cross-cat **golden
inspiration** screenshots (Sprint AD-4 — Sonnet sees not just where the
brand IS but where it must reach visually).

Lives in its own module so the orchestrator + prompt_assembly can both
import without dragging in the prompt-block formatters.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Optional

from .philosophy_bridge import ROOT


# ROUTER RACINE V26.AC — load_client_context lives in scripts/, not in
# moteur_gsg/. The shim path is registered once at import.
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from client_context import ClientContext, load_client_context  # noqa: E402


def _select_vision_screenshots(
    ctx: ClientContext,
    fallback_page_for_vision: Optional[str],
    max_images: int = 2,
    philosophy_refs: Optional[list[dict]] = None,  # Sprint AD-4 V26.AD+ : golden inspirations
    max_golden_inspirations: int = 2,
) -> list[pathlib.Path]:
    """Sprint F V26.AC + AD-4 V26.AD+ — sélectionne les screenshots VISION Sonnet.

    Priorité :
    1. 1-2 screenshots du client (page demandée OU fallback page) — ce que la marque EST
    2. 1-2 screenshots des golden inspirations cross-cat (philosophy_refs) — ce que la marque
       DOIT atteindre comme niveau visuel (Sprint AD-4 : Sonnet voit l'objectif, pas que le statu quo)

    On préfère `_fold` (above-the-fold, sous la limite Anthropic 8000px de hauteur)
    plutôt que `_full` (rejeté car >8000px souvent).
    """
    selected: list[pathlib.Path] = []
    sources = ctx.screenshots
    if not sources and fallback_page_for_vision:
        fallback_ctx = load_client_context(ctx.client, fallback_page_for_vision)
        sources = fallback_ctx.screenshots

    # ── A. Screenshots client (max_images max) ──
    if sources:
        preferred_fold = ["desktop_clean_fold", "mobile_clean_fold"]
        for name in preferred_fold:
            if name in sources:
                selected.append(sources[name])
            if len(selected) >= max_images:
                break

        if len(selected) < max_images:
            for name in ["desktop_asis_fold", "mobile_asis_fold"]:
                if name in sources and sources[name] not in selected:
                    selected.append(sources[name])
                if len(selected) >= max_images:
                    break

    # ── B. Sprint AD-4 — Golden inspirations cross-cat (max_golden_inspirations) ──
    # On ajoute des screenshots de golden refs en plus du client. Sonnet voit donc
    # le client (à respecter en palette/typo) + les cibles esthétiques (à imiter en niveau).
    if philosophy_refs and max_golden_inspirations > 0:
        for ref in philosophy_refs[:max_golden_inspirations]:
            site = ref.get("site")
            page = ref.get("page", "home")
            if not site:
                continue
            golden_dir = ROOT / "data" / "golden" / site / page / "screenshots"
            if not golden_dir.exists():
                continue
            # Préférer fold desktop (sous limite 8000px)
            for fname in ["spatial_fold_desktop.png", "spatial_fold_mobile.png", "spatial_full_page.png"]:
                fp = golden_dir / fname
                if fp.exists() and fp not in selected:
                    selected.append(fp)
                    break  # un seul screenshot par golden ref

    return selected


__all__ = ["_select_vision_screenshots", "ClientContext", "load_client_context"]
