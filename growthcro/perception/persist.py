"""Page-level orchestration — flatten elements, score noise, cluster, assign roles, write JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path

from growthcro.perception.heuristics import (
    FOLD_Y,
    NOISE_KEYWORDS,
    VIEWPORT_W,
    bbox_area,
    bbox_center,
    compute_noise_score,
    parse_font_size,
)
from growthcro.perception.intent import assign_cluster_role
from growthcro.perception.vision import (
    compute_adaptive_eps,
    dbscan_1d_vertical,
    refine_clusters_by_y_gap,
)


def process_page(spatial_path: Path, capture_path: Path, out_path: Path) -> dict:
    """Process one page: flatten → noise_score → cluster → roles → write perception_v13.json."""
    with open(spatial_path) as f:
        spatial = json.load(f)
    capture = {}
    if capture_path.exists():
        with open(capture_path) as f:
            capture = json.load(f)

    # Flatten elements (ignore the buggy V12 sections)
    raw_els = []
    for sec in spatial.get("sections", []):
        for el in sec.get("elements", []):
            el_copy = dict(el)
            el_copy["_src_section_id"] = sec.get("id")
            el_copy["_src_section_type"] = sec.get("type")
            raw_els.append(el_copy)

    # Dedup: V12 capture nearly always doubles elements.
    seen = {}
    all_els = []
    for el in raw_els:
        bbox = el.get("bbox") or {}
        key = (
            el.get("tag"),
            el.get("type"),
            (el.get("text") or "").strip(),
            bbox.get("x"),
            bbox.get("y"),
            bbox.get("w"),
            bbox.get("h"),
        )
        if key in seen:
            continue
        seen[key] = True
        all_els.append(el)

    dedup_dropped = len(raw_els) - len(all_els)
    if dedup_dropped > 0:
        print(f"  ℹ️  dédup: {len(raw_els)} → {len(all_els)} (-{dedup_dropped} duplicates)")

    if not all_els:
        print(f"  ⚠️  {spatial_path} : aucun élément, skip.")
        return {"status": "empty"}

    # Page context
    max_y = max(
        (el.get("bbox", {}).get("y", 0) + el.get("bbox", {}).get("h", 0) for el in all_els),
        default=1,
    )
    page_context = {"max_y": max_y, "viewport_w": VIEWPORT_W, "fold_y": FOLD_Y}

    # 1. Noise scoring
    for el in all_els:
        ns = compute_noise_score(el, page_context)
        el["noise_score"] = ns["noise_score"]
        el["noise_reasons"] = ns["noise_reasons"]

    # 2. Filter true noise (>=60) from clustering, keep them tagged
    NOISE_THRESHOLD = 60
    non_noise_els = [el for el in all_els if el.get("noise_score", 0) < NOISE_THRESHOLD]
    noise_els = [el for el in all_els if el.get("noise_score", 0) >= NOISE_THRESHOLD]

    # 3a. Pre-extract NAV zone (y<100, tags a|button, short text) so DBSCAN doesn't merge nav with hero.
    NAV_ZONE_Y = 100
    nav_els = []
    rest_els = []
    for el in non_noise_els:
        y = el.get("bbox", {}).get("y", 999999)
        h = el.get("bbox", {}).get("h", 0)
        txt = (el.get("text") or "").strip()
        is_nav = (
            y < NAV_ZONE_Y
            and (y + h) < NAV_ZONE_Y + 50
            and el.get("type") in ("cta", "heading")
            and 0 < len(txt) < 30
            and not re.search(r"^(commencer|démarrer|faire.le.quiz|start)", txt, re.I)
        )
        if is_nav:
            nav_els.append(el)
        else:
            rest_els.append(el)

    # 3b. Adaptive DBSCAN on rest (excluding nav)
    if len(rest_els) >= 2:
        centers = [bbox_center(el.get("bbox", {})) for el in rest_els]
        eps = compute_adaptive_eps(centers)
        labels = dbscan_1d_vertical(rest_els, eps=eps, min_samples=2)
        labels = refine_clusters_by_y_gap(rest_els, labels, gap_threshold=eps * 1.2)
    else:
        eps = 200.0
        labels = [-1] * len(rest_els)

    for el, lab in zip(rest_els, labels):
        el["cluster_id"] = int(lab) if lab >= 0 else None

    # NAV becomes its own cluster if ≥2 elements
    if len(nav_els) >= 2:
        nav_cluster_id = (max((l for l in labels if l is not None and l >= 0), default=-1) + 1)
        for el in nav_els:
            el["cluster_id"] = nav_cluster_id
            el["_is_nav_prezone"] = True
    else:
        for el in nav_els:
            el["cluster_id"] = None
            rest_els.append(el)

    for el in noise_els:
        el["cluster_id"] = None

    non_noise_els = rest_els + (nav_els if len(nav_els) >= 2 else [])

    # 4. Build clusters dict
    clusters_map: dict[int, list[dict]] = {}
    for el in non_noise_els:
        cid = el.get("cluster_id")
        if cid is None:
            continue
        clusters_map.setdefault(cid, []).append(el)

    clusters_out = []
    for cid, cluster_els in sorted(clusters_map.items()):
        role_info = assign_cluster_role(cluster_els, page_context)
        xs = [e.get("bbox", {}).get("x", 0) for e in cluster_els]
        ys = [e.get("bbox", {}).get("y", 0) for e in cluster_els]
        xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in cluster_els]
        yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in cluster_els]
        bbox = {
            "x": min(xs) if xs else 0,
            "y": min(ys) if ys else 0,
            "w": (max(xws) - min(xs)) if xs else 0,
            "h": (max(yhs) - min(ys)) if ys else 0,
        }
        clusters_out.append(
            {
                "cluster_id": cid,
                "role": role_info["role"],
                "confidence": role_info["confidence"],
                "alt_roles": role_info["alt_roles"],
                "bbox": bbox,
                "element_count": len(cluster_els),
                "has_h1": role_info["has_h1"],
                "has_cta": role_info["has_cta"],
                "rel_y": role_info["rel_y"],
                "element_indices": [all_els.index(e) for e in cluster_els],
            }
        )

    clusters_out.sort(key=lambda c: c["bbox"]["y"])

    # 5b. Merge fold clusters into HERO
    fold_cut = FOLD_Y + 100
    fold_candidates = [c for c in clusters_out if c["bbox"]["y"] + c["bbox"]["h"] <= fold_cut]
    fold_heros = [c for c in fold_candidates if c["role"] not in ("NAV", "UTILITY_BANNER", "FOOTER")]

    merged_hero_done = False
    if fold_heros and len(fold_heros) >= 2:
        has_h1_anywhere = any(c["has_h1"] for c in fold_heros)
        has_cta_anywhere = any(c["has_cta"] for c in fold_heros)
        has_big_heading_anywhere = False
        for c in fold_heros:
            for idx in c["element_indices"]:
                e = all_els[idx]
                if e.get("type") == "heading":
                    if parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 32:
                        has_big_heading_anywhere = True
                        break
            if has_big_heading_anywhere:
                break

        if (has_h1_anywhere or has_big_heading_anywhere) and has_cta_anywhere:
            merged = sorted(fold_heros, key=lambda c: c["bbox"]["y"])
            base = merged[0]
            all_indices = []
            for c in merged:
                all_indices.extend(c["element_indices"])
            all_indices = sorted(set(all_indices))

            base_elems = [all_els[i] for i in all_indices]
            xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
            ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
            xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
            yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
            merged_bbox = {
                "x": min(xs),
                "y": min(ys),
                "w": max(xws) - min(xs),
                "h": max(yhs) - min(ys),
            }
            has_h1_merged = any(e.get("tag") == "h1" for e in base_elems)
            has_cta_merged = any(e.get("type") == "cta" for e in base_elems)

            hero_cluster = {
                "cluster_id": base["cluster_id"],
                "role": "HERO",
                "confidence": 90,
                "alt_roles": [],
                "bbox": merged_bbox,
                "element_count": len(all_indices),
                "has_h1": has_h1_merged,
                "has_cta": has_cta_merged,
                "rel_y": (round(merged_bbox["y"] / max_y, 3), round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                "element_indices": all_indices,
                "_merged_from": [c["cluster_id"] for c in merged],
            }

            for i in all_indices:
                all_els[i]["cluster_id"] = hero_cluster["cluster_id"]

            clusters_out = [c for c in clusters_out if c["cluster_id"] not in hero_cluster["_merged_from"]]
            clusters_out.append(hero_cluster)
            clusters_out.sort(key=lambda c: c["bbox"]["y"])
            merged_hero_done = True

    if not merged_hero_done:
        hero_exists = any(c["role"] == "HERO" for c in clusters_out)
        if not hero_exists:
            for c in clusters_out:
                if c["bbox"]["y"] < fold_cut and c["has_h1"]:
                    c["role"] = "HERO"
                    c["confidence"] = 70
                    break

    # 5c. ORPHAN HERO RESCUE
    rescue_fold_cut = FOLD_Y * 2
    hero_exists_now = any(c["role"] == "HERO" for c in clusters_out)
    if not hero_exists_now:
        fold_orphans = [
            el for el in non_noise_els
            if el.get("cluster_id") is None
            and el.get("bbox", {}).get("y", 999999) < rescue_fold_cut
        ]
        excluded_cids = {c["cluster_id"] for c in clusters_out
                         if c["role"] in ("NAV", "UTILITY_BANNER", "FOOTER")}
        fold_extra = [
            el for el in non_noise_els
            if el.get("cluster_id") is not None
            and el.get("cluster_id") not in excluded_cids
            and el.get("bbox", {}).get("y", 999999) < rescue_fold_cut
        ]
        hero_pool = fold_orphans + fold_extra
        if hero_pool:
            has_h1_pool = any(e.get("tag") == "h1" for e in hero_pool)
            has_big_heading_pool = any(
                e.get("type") == "heading"
                and parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 32
                for e in hero_pool
            )
            has_cta_pool = any(e.get("type") == "cta" for e in hero_pool)

            if (has_h1_pool or has_big_heading_pool) and has_cta_pool:
                all_indices = sorted(set(all_els.index(e) for e in hero_pool))
                base_elems = [all_els[i] for i in all_indices]
                xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
                ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
                xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
                yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
                merged_bbox = {
                    "x": min(xs), "y": min(ys),
                    "w": max(xws) - min(xs), "h": max(yhs) - min(ys),
                }
                hero_cid = max((c["cluster_id"] for c in clusters_out), default=-1) + 1
                hero_cluster = {
                    "cluster_id": hero_cid,
                    "role": "HERO",
                    "confidence": 75,
                    "alt_roles": [],
                    "bbox": merged_bbox,
                    "element_count": len(all_indices),
                    "has_h1": any(e.get("tag") == "h1" for e in base_elems),
                    "has_cta": any(e.get("type") == "cta" for e in base_elems),
                    "rel_y": (round(merged_bbox["y"] / max_y, 3),
                              round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                    "element_indices": all_indices,
                    "_reconstituted_from_orphans": True,
                }
                for i in all_indices:
                    all_els[i]["cluster_id"] = hero_cid
                absorbed_cids = {e.get("cluster_id") for e in fold_extra if e.get("cluster_id") is not None}
                absorbed_cids.discard(hero_cid)
                clusters_out = [c for c in clusters_out if c["cluster_id"] not in absorbed_cids]
                clusters_out.append(hero_cluster)
                clusters_out.sort(key=lambda c: c["bbox"]["y"])

            elif has_h1_pool or has_big_heading_pool:
                all_indices = sorted(set(all_els.index(e) for e in hero_pool
                                         if e.get("tag") in ("h1", "h2") or e.get("type") == "heading"))
                if all_indices:
                    base_elems = [all_els[i] for i in all_indices]
                    xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
                    ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
                    xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
                    yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
                    merged_bbox = {
                        "x": min(xs), "y": min(ys),
                        "w": max(xws) - min(xs), "h": max(yhs) - min(ys),
                    }
                    hero_cid = max((c["cluster_id"] for c in clusters_out), default=-1) + 1
                    hero_cluster = {
                        "cluster_id": hero_cid,
                        "role": "HERO",
                        "confidence": 60,
                        "alt_roles": [],
                        "bbox": merged_bbox,
                        "element_count": len(all_indices),
                        "has_h1": any(e.get("tag") == "h1" for e in base_elems),
                        "has_cta": False,
                        "rel_y": (round(merged_bbox["y"] / max_y, 3),
                                  round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                        "element_indices": all_indices,
                        "_reconstituted_from_orphans": True,
                        "_hero_without_cta": True,
                    }
                    for i in all_indices:
                        all_els[i]["cluster_id"] = hero_cid
                    clusters_out.append(hero_cluster)
                    clusters_out.sort(key=lambda c: c["bbox"]["y"])

    # 5c-tier3. HERO FALLBACK ULTIME
    hero_exists_now = any(c["role"] == "HERO" for c in clusters_out)
    if not hero_exists_now:
        candidate = None
        for c in sorted(clusters_out, key=lambda x: x["bbox"]["y"]):
            if c["role"] in ("NAV", "UTILITY_BANNER", "FOOTER"):
                continue
            if c["bbox"]["y"] >= rescue_fold_cut:
                continue
            c_elems = [all_els[i] for i in c.get("element_indices", [])]
            has_cta_c = any(e.get("type") == "cta" for e in c_elems)
            has_heading_c = any(
                (e.get("tag") in ("h1", "h2", "h3") or e.get("type") == "heading")
                and parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 18
                for e in c_elems
            )
            if has_cta_c or has_heading_c:
                candidate = c
                break
        if candidate is not None:
            candidate["role"] = "HERO"
            candidate["confidence"] = 50
            candidate["_hero_tier3_fallback"] = True
        else:
            pool = [
                el for el in non_noise_els
                if el.get("bbox", {}).get("y", 999999) < rescue_fold_cut
                and (el.get("type") in ("heading", "cta") or el.get("tag") in ("h1", "h2", "h3"))
            ]
            if pool:
                pool.sort(key=lambda e: e.get("bbox", {}).get("y", 0))
                top_pool = pool[:6]
                all_indices = sorted(set(all_els.index(e) for e in top_pool))
                base_elems = [all_els[i] for i in all_indices]
                xs = [e.get("bbox", {}).get("x", 0) for e in base_elems]
                ys = [e.get("bbox", {}).get("y", 0) for e in base_elems]
                xws = [e.get("bbox", {}).get("x", 0) + e.get("bbox", {}).get("w", 0) for e in base_elems]
                yhs = [e.get("bbox", {}).get("y", 0) + e.get("bbox", {}).get("h", 0) for e in base_elems]
                merged_bbox = {
                    "x": min(xs), "y": min(ys),
                    "w": max(xws) - min(xs), "h": max(yhs) - min(ys),
                }
                hero_cid = max((c["cluster_id"] for c in clusters_out), default=-1) + 1
                hero_cluster = {
                    "cluster_id": hero_cid,
                    "role": "HERO",
                    "confidence": 45,
                    "alt_roles": [],
                    "bbox": merged_bbox,
                    "element_count": len(all_indices),
                    "has_h1": any(e.get("tag") == "h1" for e in base_elems),
                    "has_cta": any(e.get("type") == "cta" for e in base_elems),
                    "rel_y": (round(merged_bbox["y"] / max_y, 3),
                              round((merged_bbox["y"] + merged_bbox["h"]) / max_y, 3)),
                    "element_indices": all_indices,
                    "_reconstituted_from_orphans": True,
                    "_hero_tier3_fallback": True,
                }
                for i in all_indices:
                    all_els[i]["cluster_id"] = hero_cid
                clusters_out.append(hero_cluster)
                clusters_out.sort(key=lambda c: c["bbox"]["y"])

    # 5d. PRICING RESCUE (page-type aware)
    _pt_candidates = [
        spatial.get("meta", {}).get("pageType"),
        (capture.get("meta", {}) or {}).get("pageType"),
        spatial_path.parent.name,
    ]
    page_type_guess = ""
    for _pt in _pt_candidates:
        if _pt and str(_pt).strip().lower() not in ("unknown", "none", ""):
            page_type_guess = str(_pt)
            break
    if not page_type_guess:
        page_type_guess = spatial_path.parent.name or ""
    is_pricing_page = bool(re.search(r"pricing|tarif|abonnement|plan", page_type_guess.lower()))

    if is_pricing_page:
        has_pricing_role = any(c["role"] == "PRICING" for c in clusters_out)
        price_re = re.compile(
            r"\d+[\s,.]*\d*\s*(€|\$|eur|euro)(\s*/\s*(mois|an|year|month))?"
            r"|\d+[.,]\d{2}\s*(€|\$)"
            r"|gratuit(?:ement)?|free(?: forever)?|\bessai\b",
            re.I,
        )
        if not has_pricing_role:
            for c in clusters_out:
                if c["role"] in ("HERO", "NAV", "UTILITY_BANNER", "FOOTER"):
                    continue
                alt = [r for r, s in (c.get("alt_roles") or [])]
                if "PRICING" in alt:
                    c["role"] = "PRICING"
                    c["confidence"] = max(c.get("confidence", 0), 75)
                    has_pricing_role = True
                    break
            if not has_pricing_role:
                for c in clusters_out:
                    if c["role"] in ("HERO", "NAV", "UTILITY_BANNER", "FOOTER", "PRICING"):
                        continue
                    cluster_text = " ".join(
                        (all_els[i].get("text") or "") for i in c.get("element_indices", [])
                    )
                    if price_re.search(cluster_text):
                        c["role"] = "PRICING"
                        c["confidence"] = 70
                        c["_pricing_rescued"] = True
                        has_pricing_role = True
                        break

        if not has_pricing_role:
            for c in clusters_out:
                if c["role"] in ("NAV", "UTILITY_BANNER", "FOOTER"):
                    continue
                cluster_text = " ".join(
                    (all_els[i].get("text") or "") for i in c.get("element_indices", [])
                )
                if price_re.search(cluster_text):
                    existing_alt = list(c.get("alt_roles") or [])
                    existing_alt = [(r, s) for (r, s) in existing_alt if r != "PRICING"]
                    c["alt_roles"] = [("PRICING", 75)] + existing_alt
                    c["_pricing_dual_label"] = True
                    if c["role"] != "HERO":
                        c["role"] = "PRICING"
                        c["confidence"] = max(c.get("confidence", 0), 65)
                    has_pricing_role = True
                    break

    # 6. Page-level summary
    role_counter: dict[str, int] = {}
    for c in clusters_out:
        role_counter[c["role"]] = role_counter.get(c["role"], 0) + 1

    # 7. Primary CTA (in HERO cluster, else any fold cluster)
    primary_cta = None
    hero_clusters = [c for c in clusters_out if c["role"] == "HERO"]
    for c in hero_clusters:
        for idx in c["element_indices"]:
            el = all_els[idx]
            if el.get("type") == "cta" and el.get("text"):
                if not primary_cta or bbox_area(el.get("bbox", {})) > bbox_area(primary_cta.get("bbox", {})):
                    primary_cta = {
                        "text": el.get("text"),
                        "href": el.get("href"),
                        "bbox": el.get("bbox"),
                        "cluster_id": c["cluster_id"],
                    }

    output = {
        "version": "v13.0.0-perception",
        "meta": {
            "source_spatial": str(spatial_path),
            "source_capture": str(capture_path) if capture_path.exists() else None,
            "url": spatial.get("meta", {}).get("url") or (capture.get("meta", {}) or {}).get("url"),
            "page_type": (
                (lambda v: v if v and v != "unknown" else None)(spatial.get("meta", {}).get("pageType"))
                or (lambda v: v if v and v != "unknown" else None)((capture.get("meta", {}) or {}).get("pageType"))
                or (lambda v: v if v and v != "unknown" else None)((capture.get("meta", {}) or {}).get("page_type"))
                or spatial_path.parent.name
            ),
            "page_max_y": max_y,
            "eps_used": round(eps, 1) if len(non_noise_els) >= 2 else None,
        },
        "stats": {
            "total_elements": len(all_els),
            "noise_filtered": len(noise_els),
            "clusters": len(clusters_out),
            "roles": role_counter,
        },
        "elements": [
            {
                **e,
                "_src_section_id": e.get("_src_section_id"),
                "_src_section_type": e.get("_src_section_type"),
            }
            for e in all_els
        ],
        "clusters": clusters_out,
        "primary_cta": primary_cta,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"  ✓ {spatial_path.parent.name}: "
        f"{len(all_els)}el / {len(noise_els)}noise / {len(clusters_out)}clusters / "
        f"roles={role_counter}"
    )
    return {"status": "ok", "clusters": len(clusters_out), "roles": role_counter}
