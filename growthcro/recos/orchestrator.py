"""Reco orchestration — per-page prompt preparation + per-page LLM batch loop.

Single concern: orchestrate the read-from-disk → call-prompts/client →
write-to-disk dance. No prompt strings, no API transport, no argparse.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from growthcro.recos import client as _client
from growthcro.recos import prompts as _prompts
from growthcro.recos import schema as _schema


# ────────────────────────────────────────────────────────────────
# Optional imports — kept lazy + tolerant of missing repos
# ────────────────────────────────────────────────────────────────
try:
    from golden_bridge import GoldenBridge  # type: ignore
    _golden_bridge = GoldenBridge(".")
    _GOLDEN_AVAILABLE = True
except ImportError:
    _golden_bridge = None
    _GOLDEN_AVAILABLE = False

try:
    from golden_differential import compute_differential_block as _golden_diff_block  # type: ignore
    _GOLDEN_DIFF_AVAILABLE = True
except ImportError:
    _golden_diff_block = None
    _GOLDEN_DIFF_AVAILABLE = False


# ────────────────────────────────────────────────────────────────
# prepare_prompts — page-level prompt assembly + JSON write
# ────────────────────────────────────────────────────────────────
def prepare_prompts(client: str, page: str, top: int, data_dir: Path, strict: bool = True) -> Path | None:
    page_dir = data_dir / client / page
    if not page_dir.exists():
        msg = f"{page_dir} n'existe pas"
        if strict:
            print(msg, file=sys.stderr)
            sys.exit(1)
        return None

    perception_path = page_dir / "perception_v13.json"
    capture_path = page_dir / "capture.json"
    intent_path = data_dir / client / "client_intent.json"

    if not perception_path.exists():
        msg = f"{perception_path} manquant (lance perception_v13.py d'abord)"
        if strict:
            print(msg, file=sys.stderr)
            sys.exit(1)
        return None
    if not intent_path.exists():
        msg = f"{intent_path} manquant (lance intent_detector_v13.py d'abord)"
        if strict:
            print(msg, file=sys.stderr)
            sys.exit(1)
        return None

    perception = json.load(open(perception_path))
    intent_data = json.load(open(intent_path))
    capture = json.load(open(capture_path)) if capture_path.exists() else {}

    # V24.0 — inline V12: derive criteria-to-treat from score_*.json directly.
    recos_v12_path_legacy = page_dir / "recos_enriched.json"
    if recos_v12_path_legacy.exists():
        try:
            recos_v12 = json.load(open(recos_v12_path_legacy)).get("recos", [])
        except Exception:
            recos_v12 = _schema.compute_recos_brutes_from_scores(page_dir)
    else:
        recos_v12 = _schema.compute_recos_brutes_from_scores(page_dir)

    # V21.C — skip criteria already covered by a holistic cluster prompt.
    cluster_covered_crits: set[str] = set()
    cluster_path = page_dir / "recos_v21_cluster_prompts.json"
    if cluster_path.exists():
        try:
            cd = json.load(open(cluster_path))
            for cp in cd.get("cluster_prompts") or []:
                cluster_covered_crits.update(cp.get("criteria_covered") or [])
        except Exception:
            pass
    if cluster_covered_crits:
        before_n = len(recos_v12)
        recos_v12 = [r for r in recos_v12 if r.get("criterion_id") not in cluster_covered_crits]
        skipped_n = before_n - len(recos_v12)
        if skipped_n:
            print(f"  [V21.C] {skipped_n} critères skippés (couverts par cluster holistique)")

    # V21.F.2 — USP signals
    usp_signals_path = page_dir / "usp_signals.json"
    usp_signals = None
    if usp_signals_path.exists():
        try:
            usp_signals = json.load(open(usp_signals_path))
        except Exception:
            pass

    # V21.F.2 — existing scores for "what_works" + current_score gating
    client_scores: dict[str, dict] = {}
    for score_file in page_dir.glob("score_*.json"):
        try:
            d = json.load(open(score_file))
            if isinstance(d, dict):
                criteria = d.get("criteria") or d.get("criterions") or []
                for c in criteria:
                    cid = c.get("criterion_id") or c.get("id")
                    if not cid:
                        continue
                    score_pct = c.get("score_pct")
                    if score_pct is None and c.get("score") is not None and c.get("max_score"):
                        try:
                            score_pct = round(100 * float(c["score"]) / float(c["max_score"]), 1)
                        except Exception:
                            score_pct = None
                    if score_pct is not None:
                        client_scores[cid] = {
                            "score_pct": score_pct,
                            "label": c.get("label") or c.get("name") or cid,
                            "source": score_file.stem,
                        }
        except Exception:
            pass

    # V21.B — Vision signals (ground truth)
    vision_signals: dict[str, dict] = {"desktop": {}, "mobile": {}}
    for vp in ("desktop", "mobile"):
        vp_path = page_dir / f"vision_{vp}.json"
        if vp_path.exists():
            try:
                v = json.load(open(vp_path))
                hero_v = v.get("hero") if isinstance(v.get("hero"), dict) else {}
                vision_signals[vp] = {
                    "h1": (hero_v.get("h1") or {}).get("text", "") if isinstance(hero_v.get("h1"), dict) else "",
                    "subtitle": (hero_v.get("subtitle") or {}).get("text", "") if isinstance(hero_v.get("subtitle"), dict) else "",
                    "primary_cta": (hero_v.get("primary_cta") or {}).get("text", "") if isinstance(hero_v.get("primary_cta"), dict) else "",
                    "social_proof_in_fold": hero_v.get("social_proof_in_fold") if isinstance(hero_v.get("social_proof_in_fold"), dict) else None,
                    "utility_banner": v.get("utility_banner") if isinstance(v.get("utility_banner"), dict) else None,
                    "below_fold_sections": [
                        {"type": s.get("type"), "headline": s.get("headline", "")[:100]}
                        for s in (v.get("below_fold_sections") or [])[:8]
                        if isinstance(s, dict)
                    ],
                    "fold_readability": v.get("fold_readability") if isinstance(v.get("fold_readability"), dict) else None,
                }
            except Exception:
                pass

    # Capture context — prefer Vision desktop signals over heuristic.
    hero_data = capture.get("hero", {}) or {}
    vis_d = vision_signals.get("desktop") or {}

    # V21.F.2 — businessCategory from canonical site_audit.json.
    site_audit_path = data_dir / client / "site_audit.json"
    business_category = None
    if site_audit_path.exists():
        try:
            sa = json.load(open(site_audit_path))
            business_category = sa.get("businessCategory") or sa.get("business_category")
        except Exception:
            pass
    if not business_category:
        business_category = capture.get("businessCategory") or capture.get("business_category")

    # V23.D — funnel data if applicable
    funnel_data = None
    if page in _schema.FUNNEL_PAGE_TYPES:
        funnel_path = page_dir / "score_funnel.json"
        if funnel_path.exists():
            try:
                funnel_data = json.load(open(funnel_path))
            except Exception:
                funnel_data = None

    capture_context = {
        "url": perception.get("meta", {}).get("url"),
        "h1": vis_d.get("h1") or hero_data.get("h1", ""),
        "subtitle": vis_d.get("subtitle") or hero_data.get("subtitle", ""),
        "primary_cta_text": (
            vis_d.get("primary_cta")
            or _prompts.hero_primary_cta_text(hero_data)
            or (perception.get("primary_cta") or {}).get("text", "")
        ),
        "primary_cta_href": (
            _prompts.hero_primary_cta_href(hero_data)
            or (perception.get("primary_cta") or {}).get("href", "")
        ),
        "businessCategory": business_category,
        "vision": vision_signals,
        "funnel": funnel_data,
    }

    def reco_rank(r: dict) -> float:
        priority_weight = {"P0": 4, "P1": 3, "P2": 2, "P3": 1}.get(r.get("priority"), 1)
        ap_weight = len(r.get("anti_patterns", []) or []) * 0.5
        ice = r.get("ice_score") or 0
        return priority_weight + ap_weight + (ice / 100)

    ranked = sorted(recos_v12, key=reco_rank, reverse=True)
    selected = ranked if top <= 0 else ranked[:top]

    prompts_out: list[dict] = []
    for r in selected:
        crit_id = r.get("criterion_id")
        if not crit_id:
            continue
        crit_doctrine = _schema.get_criterion_doctrine(crit_id)
        anti_pats = _schema.get_criterion_anti_patterns(crit_id)
        cluster = _schema.pick_cluster_for_criterion(crit_id, perception.get("clusters", []))
        cluster_sum = (
            _schema.extract_cluster_text_summary(cluster, perception.get("elements", []))
            if cluster
            else None
        )

        scope = _schema.criterion_scope(crit_id)
        if scope == "ENSEMBLE" and cluster is None:
            prompts_out.append(
                {
                    "criterion_id": crit_id,
                    "priority_v12": r.get("priority"),
                    "ice_v12": r.get("ice_score"),
                    "cluster_picked": None,
                    "cluster_id": None,
                    "skipped": True,
                    "skipped_reason": "no_cluster_for_ensemble",
                    "scope": scope,
                    "v12_reco_text": (r.get("reco_text") or "").strip()[:500],
                }
            )
            continue

        # V16 Golden Bridge context (optional)
        golden_ctx = None
        if _GOLDEN_AVAILABLE and _golden_bridge:
            client_cat = intent_data.get("category", "") or capture.get("businessCategory", "")
            golden_ctx = _golden_bridge.get_benchmark_context(client_cat, page, crit_id)

        client_cat = intent_data.get("category", "") or capture.get("businessCategory", "")
        priority_to_band = {"P0": "critical", "P1": "critical", "P2": "mid", "P3": "ok"}
        style_tpls = _schema.find_style_templates(
            crit_id=crit_id,
            page_type=page,
            intent_slug=intent_data.get("primary_intent", ""),
            business_category=client_cat,
            score_band=priority_to_band.get(r.get("priority"), "critical"),
            limit=2,
        )

        # Golden differential block (optional)
        differential_block = ""
        if _GOLDEN_DIFF_AVAILABLE:
            spatial_path = page_dir / "spatial_v9.json"
            spatial_data = None
            if spatial_path.exists():
                try:
                    spatial_data = json.load(open(spatial_path))
                except Exception:
                    pass
            try:
                differential_block = _golden_diff_block(
                    capture=capture,
                    spatial=spatial_data,
                    page_type=page,
                    business_type=client_cat,
                )
            except Exception:
                differential_block = ""

        killer_violations = _schema.check_killer_violations(perception, vision_signals, crit_id)

        # ICE estimate per criterion
        crit_pillar = "tech"
        if crit_doctrine:
            crit_pillar = (crit_doctrine.get("pillar") or "").replace("bloc_", "").replace("_", "")
            for prefix, p in (("hero", "hero"), ("persuasion", "persuasion"), ("ux", "ux"),
                              ("coherence", "coherence"), ("psycho", "psycho"), ("tech", "tech")):
                if prefix in (crit_doctrine.get("pillar") or "").lower():
                    crit_pillar = p
                    break
        crit_score_data = client_scores.get(crit_id, {})
        current_pct = crit_score_data.get("score_pct", 50)
        max_score_estimate = 3
        current_score_raw = (current_pct / 100) * max_score_estimate
        ice_estimate = _schema.compute_ice_estimate(
            crit_id=crit_id,
            pillar=crit_pillar,
            current_score=current_score_raw,
            max_score=max_score_estimate,
            vision_lifted=False,
            intelligence_lifted=False,
            killer_violated=bool(killer_violations),
        )

        user_prompt = _prompts.build_user_prompt(
            client=client,
            page_type=page,
            intent_data=intent_data,
            crit_id=crit_id,
            crit_doctrine=crit_doctrine,
            anti_patterns=anti_pats,
            v12_reco=r,
            cluster_summary=cluster_sum,
            capture_context=capture_context,
            golden_context=golden_ctx,
            style_templates=style_tpls,
            differential_block=differential_block,
            usp_signals=usp_signals,
            client_scores=client_scores,
            killer_violations=killer_violations,
            ice_estimate=ice_estimate,
        )

        grounding_hints = {
            "client_name": client,
            "h1_text": (capture_context.get("h1") or "").strip()[:100],
            "subtitle_text": (capture_context.get("subtitle") or "").strip()[:120],
            "primary_cta_text": (capture_context.get("primary_cta_text") or "").strip()[:60],
        }

        prompts_out.append(
            {
                "criterion_id": crit_id,
                "priority_v12": r.get("priority"),
                "ice_v12": r.get("ice_score"),
                "cluster_picked": cluster.get("role") if cluster else None,
                "cluster_id": cluster.get("cluster_id") if cluster else None,
                "scope": scope,
                "system_prompt": _prompts.PROMPT_SYSTEM,
                "user_prompt": user_prompt,
                "v12_reco_text": (r.get("reco_text") or "").strip()[:500],
                "grounding_hints": grounding_hints,
                "golden_annihilate": golden_ctx.get("annihilate", False) if golden_ctx else False,
                "golden_avg": golden_ctx.get("golden_avg") if golden_ctx else None,
            }
        )

    out_path = page_dir / "recos_v13_prompts.json"
    with open(out_path, "w") as f:
        json.dump(
            {
                "version": "v17.0.0-reco-prompts-hardened",
                "client": client,
                "page": page,
                "intent": intent_data.get("primary_intent"),
                "top_n": len(prompts_out),
                "prompts": prompts_out,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"  ✓ {client}/{page}: {len(prompts_out)} prompts prêts → {out_path.relative_to(Path('.'))}")
    return out_path


# ────────────────────────────────────────────────────────────────
# process_page — per-page LLM batch (called from CLI enrich subcommand)
# ────────────────────────────────────────────────────────────────
async def process_page(
    client_api,
    prompts_file: Path,
    out_file: Path,
    model: str,
    semaphore: asyncio.Semaphore,
    force: bool = False,
) -> dict:
    """{client, page, n_ok, n_fallback, n_skipped, tokens, n_retries}."""
    data = json.load(open(prompts_file))
    client = data.get("client")
    page = data.get("page")
    prompts = data.get("prompts", [])

    existing: dict[str, dict] = {}
    if out_file.exists() and not force:
        prev = json.load(open(out_file))
        for r in prev.get("recos", []):
            existing[r["criterion_id"]] = r

    write_lock = asyncio.Lock()

    def _snapshot_file(recos_dict: dict[str, dict], n_prompts: int) -> None:
        recos_list = list(recos_dict.values())
        n_skipped = sum(1 for r in recos_list if r.get("_skipped"))
        n_fallback = sum(1 for r in recos_list if r.get("_fallback"))
        n_ok = sum(1 for r in recos_list if not r.get("_fallback") and not r.get("_skipped"))
        tokens_total = sum(r.get("_tokens", 0) for r in recos_list)
        n_retries_total = sum(r.get("_retry_count", 0) for r in recos_list)
        fallback_reasons: dict[str, int] = {}
        for r in recos_list:
            if r.get("_fallback"):
                reason = r.get("_fallback_reason", "unknown")
                fallback_reasons[reason] = fallback_reasons.get(reason, 0) + 1
        skipped_reasons: dict[str, int] = {}
        for r in recos_list:
            if r.get("_skipped"):
                reason = r.get("_skipped_reason", "unknown")
                skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        grounded = [r.get("_grounding_score") for r in recos_list if r.get("_grounding_score") is not None]
        grounding_avg = round(sum(grounded) / len(grounded), 2) if grounded else None
        grounding_retried = sum(1 for r in recos_list if r.get("_grounding_retried"))
        out = {
            "version": "v13.3.0-reco-final",
            "client": client,
            "page": page,
            "model": model,
            "intent": data.get("intent"),
            "n_prompts": n_prompts,
            "n_ok": n_ok,
            "n_fallback": n_fallback,
            "n_skipped": n_skipped,
            "n_retries_total": n_retries_total,
            "grounding_avg_score": grounding_avg,
            "grounding_retried": grounding_retried,
            "fallback_reasons": fallback_reasons,
            "skipped_reasons": skipped_reasons,
            "tokens_total": tokens_total,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "recos": recos_list,
        }
        tmp = out_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        tmp.replace(out_file)

    async def _one(p: dict) -> dict | None:
        crit_id = p.get("criterion_id")
        if not crit_id:
            return None
        if crit_id in existing and not existing[crit_id].get("_fallback") and not existing[crit_id].get("_skipped"):
            return existing[crit_id]

        if p.get("skipped"):
            reason = p.get("skipped_reason", "unknown")
            scope = p.get("scope", "ENSEMBLE")
            reco = {
                "criterion_id": crit_id,
                "cluster_id": None,
                "cluster_role": None,
                "before": f"⚠️ SKIPPED ({reason}) — critère {crit_id} scope={scope} sans cluster perception.",
                "after": f"⚠️ Recapture requise — perception_v13 n'a pas identifié de cluster pour ce critère. Relancer `ghost_capture --headed` puis `perception_v13.py --client {client} --page {page}`.",
                "why": f"Un critère ENSEMBLE ({crit_id}) ne peut pas recevoir de reco fiable sans le cluster perceptuel (éléments H1/subtitle/CTA/visual qui l'entourent). Skip gracieux au lieu de générer du jus générique.",
                "expected_lift_pct": 0,
                "effort_hours": 1,
                "priority": "P3",
                "implementation_notes": f"reco_enricher skip : {reason}. Corriger en amont (re-capture).",
                "_skipped": True,
                "_skipped_reason": reason,
                "_tokens": 0,
                "_retry_count": 0,
            }
            async with write_lock:
                existing[crit_id] = reco
                _snapshot_file(existing, len(prompts))
            return reco

        async with semaphore:
            parsed, raw, tokens, retry_count, fb_reason = await _client.call_llm_with_structured_retry(
                client_api,
                p["system_prompt"],
                p["user_prompt"],
                model,
            )

            hints = p.get("grounding_hints") or {}
            grounding_score = None
            grounding_issues: list[str] = []
            grounding_retries = 0
            if parsed is not None and hints:
                grounding_score, grounding_issues = _schema.check_grounding(parsed, hints)
                if grounding_score < _client.MIN_GROUNDING_SCORE:
                    grounding_prompt = (
                        p["user_prompt"]
                        + "\n\n⚠️ RETRY GROUNDING: ta reco précédente était trop générique.\n"
                        + f"Issues: {', '.join(grounding_issues)}.\n"
                        + "Tu DOIS OBLIGATOIREMENT :\n"
                        + f"  - Mentionner '{hints.get('client_name', '')}' par son nom dans 'before' OU 'why'.\n"
                    )
                    if hints.get("h1_text"):
                        grounding_prompt += f"  - Citer l'extrait réel du H1 dans 'before' : \"{hints.get('h1_text')}\".\n"
                    if hints.get("primary_cta_text"):
                        grounding_prompt += f"  - Citer le texte exact du CTA actuel : \"{hints.get('primary_cta_text')}\".\n"
                    grounding_prompt += "Une reco interchangeable entre clients = reco ratée."

                    parsed2, raw2, tokens2, rc2, _fb2 = await _client.call_llm_with_structured_retry(
                        client_api,
                        p["system_prompt"],
                        grounding_prompt,
                        model,
                        max_structured_retries=1,
                    )
                    grounding_retries = 1
                    retry_count += rc2
                    tokens += tokens2
                    if parsed2 is not None:
                        score2, issues2 = _schema.check_grounding(parsed2, hints)
                        if score2 > grounding_score:
                            parsed = parsed2
                            grounding_score = score2
                            grounding_issues = issues2
                            raw = raw2 or raw

        if parsed is None:
            reco = _schema.fallback_reco_from_v12(p.get("v12_reco_text", ""), crit_id, reason=fb_reason or "unknown")
            reco["_tokens"] = tokens
            reco["_raw_sample"] = (raw or "")[:300]
            reco["_retry_count"] = retry_count
            reco["criterion_id"] = crit_id
            reco["cluster_id"] = p.get("cluster_id")
            reco["cluster_role"] = p.get("cluster_picked")
        else:
            parsed["criterion_id"] = crit_id
            parsed["cluster_id"] = p.get("cluster_id")
            parsed["cluster_role"] = p.get("cluster_picked")
            parsed["ice_score"] = _schema.compute_ice_score_v13(parsed)
            parsed["_tokens"] = tokens
            parsed["_retry_count"] = retry_count
            parsed["_grounding_score"] = grounding_score
            parsed["_grounding_issues"] = grounding_issues
            parsed["_grounding_retried"] = bool(grounding_retries)
            parsed["_model"] = model
            reco = parsed

        async with write_lock:
            existing[crit_id] = reco
            _snapshot_file(existing, len(prompts))
        return reco

    results = await asyncio.gather(*[_one(p) for p in prompts])
    results = [r for r in results if r is not None]

    n_skipped = sum(1 for r in results if r.get("_skipped"))
    n_fallback = sum(1 for r in results if r.get("_fallback"))
    n_ok = sum(1 for r in results if not r.get("_fallback") and not r.get("_skipped"))
    tokens_total = sum(r.get("_tokens", 0) for r in results)
    n_retries_total = sum(r.get("_retry_count", 0) for r in results)

    async with write_lock:
        _snapshot_file(existing, len(prompts))

    retry_note = f" · {n_retries_total} retries" if n_retries_total else ""
    skip_note = f" + {n_skipped} skip" if n_skipped else ""
    print(f"  ✓ {client}/{page}: {n_ok} OK + {n_fallback} fallback{skip_note} · {tokens_total} tokens{retry_note}")
    return {
        "client": client, "page": page, "n_ok": n_ok, "n_fallback": n_fallback,
        "n_skipped": n_skipped, "tokens": tokens_total, "n_retries": n_retries_total,
    }


# ────────────────────────────────────────────────────────────────
# Batch driver (used by CLI enrich subcommand)
# ────────────────────────────────────────────────────────────────
async def run_async(prompt_files: list[Path], out_files: list[Path], model: str, max_concurrent: int, force: bool):
    client_api = _client.make_client()
    sem = asyncio.Semaphore(max_concurrent)
    tasks = [process_page(client_api, pf, of, model, sem, force) for pf, of in zip(prompt_files, out_files)]
    results = await asyncio.gather(*tasks)
    total_ok = sum(r["n_ok"] for r in results)
    total_fb = sum(r["n_fallback"] for r in results)
    total_skipped = sum(r.get("n_skipped", 0) for r in results)
    total_tokens = sum(r["tokens"] for r in results)
    total_retries = sum(r.get("n_retries", 0) for r in results)
    retry_note = f" · {total_retries} retries" if total_retries else ""
    fb_note = f" · {total_fb} fallback" + (" ⚠️ VISIBLE" if total_fb else "")
    skip_note = f" · {total_skipped} skipped (cluster missing)" if total_skipped else ""
    print(f"\n✓ {len(results)} pages · {total_ok} OK{fb_note}{skip_note} · {total_tokens:,} tokens{retry_note}")


# ────────────────────────────────────────────────────────────────
# Dry-run cost estimator
# ────────────────────────────────────────────────────────────────
def dry_run(data_dir: Path) -> None:
    total_prompts = 0
    total_chars = 0
    pages = 0
    for cd in sorted(data_dir.iterdir()):
        if not cd.is_dir():
            continue
        for pd in sorted(cd.iterdir()):
            if not pd.is_dir():
                continue
            pf = pd / "recos_v13_prompts.json"
            if not pf.exists():
                continue
            pages += 1
            try:
                d = json.load(open(pf))
                for p in d.get("prompts", []):
                    total_prompts += 1
                    total_chars += len(p.get("system_prompt", "")) + len(p.get("user_prompt", ""))
            except Exception as e:
                print(f"  ❌ {pf}: {e}")
    tokens_in = total_chars / 4
    tokens_out = total_prompts * 400
    cost_sonnet = (tokens_in / 1_000_000) * 3 + (tokens_out / 1_000_000) * 15
    cost_haiku = (tokens_in / 1_000_000) * 1 + (tokens_out / 1_000_000) * 5
    print("\n=== DRY RUN SUMMARY ===")
    print(f"Pages prêtes: {pages}")
    print(f"Prompts total: {total_prompts}")
    print(f"Tokens estimés: ~{int(tokens_in):,} in + ~{int(tokens_out):,} out")
    print(f"Coût estimé Sonnet 4.6 : ${cost_sonnet:.2f}")
    print(f"Coût estimé Haiku 4.5  : ${cost_haiku:.2f}")
