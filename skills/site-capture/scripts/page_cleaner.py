#!/usr/bin/env python3
"""
page_cleaner.py — GrowthCRO V12 Phase 5.1 : nettoyage post-capture.

Post-processe `spatial_v9.json` pour produire `spatial_v9_clean.json` :
  1. Dédupliquer les sections (même bbox + même contenu texte signature)
  2. Retirer les éléments reconnus comme "bruit" (chat widgets, popups,
     consent banners non-fermés, back-to-top, social floating shares)
  3. Retirer les sections vides ou minuscules sans contenu sémantique
  4. Tagger la section footer explicitement (par position + signal texte)
  5. Produire un `cleanup_report` auditable (quoi retiré / pourquoi)

Principe Mathis : la capture (DOM rendered) reste source of truth —
cleaner ne supprime QUE du bruit non-sémantique (widgets injectés, overlays
non liés au contenu de la LP). Jamais de contenu CRO.

Usage :
  python page_cleaner.py <label> <pageType>
  python page_cleaner.py --all   # traite toutes les captures

Lit : data/captures/<label>/<pageType>/spatial_v9.json
Écrit : data/captures/<label>/<pageType>/spatial_v9_clean.json
"""
from __future__ import annotations

import json
import re
import sys
import pathlib
import hashlib
from datetime import datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"


# ─────────────────────────── Noise patterns ──────────────────────────────

# Classes/IDs qui signalent un widget tiers (chat, popup, etc.)
NOISE_CLASS_ID_PATTERNS = [
    # Chat widgets
    r"intercom[-_]",
    r"drift[-_]",
    r"hubspot[-_]chat",
    r"hubspot-messages",
    r"crisp[-_]",
    r"tidio[-_]",
    r"freshchat",
    r"zendesk[-_]web",
    r"livechat",
    r"tawk[-_]",
    r"olark",
    r"userlike",
    r"smartsupp",
    r"zopim",
    r"chatbot",
    r"chat[-_]widget",
    r"chat[-_]launcher",
    r"messenger[-_]bubble",

    # Popups / modals génériques
    r"optinmonster",
    r"sumome",
    r"getsitecontrol",
    r"omnisend[-_]popup",
    r"klaviyo[-_]form",
    r"mailchimp[-_]popup",
    r"privy[-_]",
    r"popupmaker",
    r"poptin",
    r"spin-to-win",

    # Consent banners non-supprimés
    r"onetrust",
    r"didomi",
    r"cookiebot",
    r"cookieinformation",
    r"axeptio",
    r"tarteaucitron",
    r"gdpr[-_]banner",
    r"cookie[-_]notice",
    r"cookie[-_]consent",

    # Social floats / share buttons
    r"addthis[-_]",
    r"addtoany",
    r"sharethis[-_]",
    r"social[-_]float",
    r"share[-_]sidebar",

    # Back-to-top / scroll helpers
    r"back[-_]to[-_]top",
    r"scroll[-_]to[-_]top",
    r"scrollup",

    # Analytics / tracking overlays visibles (rare mais arrive)
    r"hotjar[-_]",
    r"ab[-_]tasty",
    r"kameleoon",
    r"vwo[-_]",

    # Notifs push
    r"onesignal[-_]bell",
    r"pushengage",
    r"webpush[-_]",

    # Wheel-of-fortune / gamification popups
    r"spinwheel",
    r"wheelofpromise",
    r"luckyorange",
]

NOISE_REGEX = re.compile("|".join(NOISE_CLASS_ID_PATTERNS), re.I)

# Texte qui signale un élément popup non-contenu (fallback)
NOISE_TEXT_PATTERNS = [
    r"^accepter (?:tous )?les cookies",
    r"^accepter (?:et )?continuer",
    r"^refuser (?:tous )?les cookies",
    r"^personnaliser mes choix",
    r"^accept(?:ing)? all cookies",
    r"rejoignez notre newsletter",
    r"join our newsletter",
    r"subscribe to our newsletter",
    r"inscrivez-vous (?:à notre newsletter|ici)",
    r"chat (?:avec nous|with us|now)",
    r"besoin d'aide.{0,3}$",
    r"need help.{0,3}$",
    r"retour (?:en|vers le) haut",
    r"back to top",
    r"ouvrir le tchat",
]

NOISE_TEXT_REGEX = re.compile("|".join(NOISE_TEXT_PATTERNS), re.I)


# ─────────────────────────── Helpers ─────────────────────────────────────

def _element_signature(el: dict) -> str:
    """Signature courte d'un élément pour détecter duplicates.

    NOTE : spatial_v9.js stocke img/video/form via `type` (sans `tag` field).
    On normalise pour que le signature soit stable. Pour les éléments visuels
    (images/videos) sans texte, on utilise src+bbox pour différencier.
    Sans ça, N logos presse identiques en carousel se retrouvent tous avec
    signature "||" → dédupliqués à 1.
    """
    tag = (el.get("tag") or "").lower()
    if not tag:
        type_to_tag = {"image": "img", "video": "video", "form": "form"}
        tag = type_to_tag.get((el.get("type") or "").lower(), "")
    text = (el.get("text") or "").strip()[:80]
    cls = (el.get("class") or "")[:40] if isinstance(el.get("class"), str) else ""
    # Pour les médias (pas de texte), ajouter src+bbox pour différencier
    media_key = ""
    if tag in ("img", "video") and not text:
        bb = el.get("bbox") or {}
        src = (el.get("src") or "")[:80]
        alt = (el.get("alt") or "")[:40]
        media_key = f"|{src}|{alt}|{bb.get('x',0)},{bb.get('y',0)}"
    return f"{tag}|{text}|{cls}{media_key}"


def _section_signature(sec: dict) -> str:
    """Signature d'une section pour déduplication."""
    bb = sec.get("bbox", {})
    key = f"{bb.get('x',0)}-{bb.get('y',0)}-{bb.get('w',0)}-{bb.get('h',0)}"
    elts = sec.get("elements", [])
    sigs = sorted([_element_signature(e) for e in elts if isinstance(e, dict)])
    digest = hashlib.sha1("|".join(sigs).encode("utf-8")).hexdigest()[:10]
    return f"{key}|{digest}"


def _is_noise_element(el: dict) -> tuple[bool, str | None]:
    """Heuristique : l'élément est-il du bruit non-CRO ?"""
    if not isinstance(el, dict):
        return True, "not_a_dict"

    cls = el.get("class") or ""
    if not isinstance(cls, str):
        cls = " ".join(cls) if isinstance(cls, list) else str(cls)
    eid = el.get("id") or ""

    combined = f"{cls} {eid}".lower()
    m = NOISE_REGEX.search(combined)
    if m:
        return True, f"noise_class_id:{m.group(0)}"

    txt = (el.get("text") or "").strip()
    if txt and NOISE_TEXT_REGEX.search(txt):
        return True, f"noise_text:{txt[:40]}"

    # Element is tiny (probably decorative) AND has no text AND no tag of interest
    # Normalize spatial_v9 convention: type='image'/'video'/'form' → tag
    tag = (el.get("tag") or "").lower()
    if not tag:
        type_to_tag = {"image": "img", "video": "video", "form": "form"}
        tag = type_to_tag.get((el.get("type") or "").lower(), "")
    bb = el.get("bbox") or el.get("rect") or {}
    w = bb.get("w") or bb.get("width") or 0
    h = bb.get("h") or bb.get("height") or 0
    if tag not in ("h1", "h2", "h3", "h4", "h5", "h6", "a", "button", "input", "img", "video", "form", "iframe"):
        if (w * h) < 400 and not txt:  # <20×20 px vide
            return True, "tiny_empty_decorative"
    # Tiny icon-level images (<12px) = decorative
    if tag == "img" and (w * h) < 150:
        return True, "tiny_icon_decorative"

    return False, None


def _is_section_empty_or_tiny(sec: dict) -> tuple[bool, str | None]:
    bb = sec.get("bbox", {})
    w = bb.get("w", 0) or bb.get("width", 0)
    h = bb.get("h", 0) or bb.get("height", 0)
    elts = sec.get("elements", [])
    if not elts:
        # Toute section sans éléments DOM est décorative (bg image, spacer, etc.)
        # → retirer pour component detection. Le screenshot reste source of truth
        # pour le spatial/DA si besoin.
        if h < 100:
            return True, "empty_and_short"
        return True, f"empty_no_elements_h{h}"
    # Section avec éléments mais tous du bruit = à supprimer
    return False, None


# ─────────────────────────── Core cleanup ────────────────────────────────

def clean_capture(data: dict) -> dict:
    """Retourne une copie nettoyée de spatial_v9.json + cleanup_report."""
    sections_in = data.get("sections", []) or []
    report = {
        "input_sections_count": len(sections_in),
        "duplicates_removed": [],
        "noise_elements_filtered": [],
        "empty_sections_removed": [],
        "footer_tagged": False,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cleaner_version": "v1.0.0-phase5.1",
    }

    # Pass 1: déduplicate sections
    seen_sigs: dict[str, int] = {}
    deduped: list[dict] = []
    for idx, sec in enumerate(sections_in):
        sig = _section_signature(sec)
        if sig in seen_sigs:
            report["duplicates_removed"].append({
                "section_index": idx,
                "duplicate_of": seen_sigs[sig],
                "bbox": sec.get("bbox"),
            })
            continue
        seen_sigs[sig] = idx
        deduped.append(sec)

    # Pass 2: filtrer éléments de bruit
    cleaned_sections: list[dict] = []
    for sec in deduped:
        elts_in = sec.get("elements", []) or []
        elts_out: list[dict] = []
        for e in elts_in:
            is_noise, reason = _is_noise_element(e)
            if is_noise:
                report["noise_elements_filtered"].append({
                    "section_bbox": sec.get("bbox"),
                    "tag": e.get("tag") if isinstance(e, dict) else None,
                    "text": (e.get("text") or "")[:60] if isinstance(e, dict) else "",
                    "reason": reason,
                })
                continue
            elts_out.append(e)
        # Dédupliquer elements internes (même signature)
        seen_el_sigs = set()
        elts_dedup = []
        for e in elts_out:
            if not isinstance(e, dict):
                elts_dedup.append(e)
                continue
            esig = _element_signature(e)
            if esig in seen_el_sigs:
                continue
            seen_el_sigs.add(esig)
            elts_dedup.append(e)
        sec2 = {**sec, "elements": elts_dedup}
        cleaned_sections.append(sec2)

    # Pass 3: retirer sections vides/minuscules SANS contenu sémantique
    final_sections: list[dict] = []
    for sec in cleaned_sections:
        is_empty, reason = _is_section_empty_or_tiny(sec)
        if is_empty:
            report["empty_sections_removed"].append({
                "bbox": sec.get("bbox"),
                "reason": reason,
            })
            continue
        final_sections.append(sec)

    # Pass 4: tagger le footer (section la plus basse + textes footer typiques)
    if final_sections:
        # Tri par y ascendant
        final_sections_sorted = sorted(
            final_sections,
            key=lambda s: s.get("bbox", {}).get("y", 0),
        )
        # Candidat footer = dernière section OU section dont contenu = liens mentions/contact
        FOOTER_KEYWORDS_RE = re.compile(
            r"mentions l[ée]gales|cgv|cgu|politique de confidentialit|"
            r"conditions g[ée]n[ée]rales|contact|newsletter|nous suivre|"
            r"follow us|copyright|©|all rights reserved",
            re.I,
        )
        for sec in final_sections_sorted:
            txt_blob = " ".join(
                (e.get("text") or "") for e in sec.get("elements", []) if isinstance(e, dict)
            )
            if FOOTER_KEYWORDS_RE.search(txt_blob):
                sec["_component_hint"] = "footer"
                report["footer_tagged"] = True
                break
        # Fallback: dernière section = footer
        if not report["footer_tagged"] and final_sections_sorted:
            final_sections_sorted[-1]["_component_hint"] = "footer"
            report["footer_tagged"] = True

        final_sections = final_sections_sorted

    report["output_sections_count"] = len(final_sections)
    report["reduction_pct"] = round(
        100.0 * (1 - len(final_sections) / max(1, len(sections_in))), 1
    )

    out = {**data, "sections": final_sections, "_cleanup_report": report}
    return out


# ─────────────────────────── Orchestration ───────────────────────────────

def clean_capture_file(spatial_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    data = json.loads(spatial_path.read_text(encoding="utf-8"))
    out = clean_capture(data)
    out_path = spatial_path.parent / "spatial_v9_clean.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out_path, out["_cleanup_report"]


def _print_report(label: str, page_type: str, report: dict):
    print(f"✅ {label}/{page_type} cleaned")
    print(f"   Sections: {report['input_sections_count']} → {report['output_sections_count']} "
          f"(-{report['reduction_pct']}%)")
    print(f"   Duplicates removed: {len(report['duplicates_removed'])}")
    print(f"   Noise elements filtered: {len(report['noise_elements_filtered'])}")
    print(f"   Empty sections removed: {len(report['empty_sections_removed'])}")
    print(f"   Footer tagged: {report['footer_tagged']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: page_cleaner.py <label> <pageType>  |  page_cleaner.py --all", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--all":
        for spatial_path in sorted(CAPTURES.glob("*/*/spatial_v9.json")):
            label = spatial_path.parent.parent.name
            page_type = spatial_path.parent.name
            try:
                _, report = clean_capture_file(spatial_path)
                _print_report(label, page_type, report)
            except Exception as e:
                print(f"❌ {label}/{page_type}: {e}", file=sys.stderr)
        return

    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    spatial_path = CAPTURES / label / page_type / "spatial_v9.json"
    if not spatial_path.exists():
        print(f"❌ Not found: {spatial_path}", file=sys.stderr)
        sys.exit(2)
    out_path, report = clean_capture_file(spatial_path)
    _print_report(label, page_type, report)
    print(f"   → {out_path}")


if __name__ == "__main__":
    main()
