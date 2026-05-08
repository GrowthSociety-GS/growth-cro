#!/usr/bin/env python3
"""
reco_enricher_v13_api.py — Couche 3 Oracle Perception V13 : mode API

Prend en entrée les `recos_v13_prompts.json` (produits par reco_enricher_v13.py --prepare)
et les passe à l'API Anthropic pour produire les vraies recos LLM finales.

Produit `recos_v13_final.json` par page avec :
  - before / after / why / expected_lift_pct / effort_hours / priority / implementation_notes
  - ice_score calculé depuis expected_lift_pct × (6 - clamp(effort_hours/8, 0.5, 5))
  - fallback template si parsing JSON échoue
  - cache par (client, page, criterion) : skip si déjà fait

Usage (sera actif quand ANTHROPIC_API_KEY défini) :
    # Dry-run (n'appelle pas l'API, vérifie juste que tous les prompts sont là)
    python3 reco_enricher_v13_api.py --dry-run --all

    # Un seul client/page (test qualité)
    python3 reco_enricher_v13_api.py --client japhy --page home

    # Batch complet
    python3 reco_enricher_v13_api.py --all --model claude-sonnet-4-6 --max-concurrent 5

Environment variables requises :
    ANTHROPIC_API_KEY=sk-ant-xxx   (sinon refuse de run)

Coûts estimés (29 clients × ~30 prompts/page × ~3 pages/client = ~2600 calls) :
    - claude-sonnet-4-6 : ~$15-25 par full batch
    - claude-haiku-4-5  : ~$2-4 par full batch
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────
# CONSTANTES
# ────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # Haiku suffit pour les recos
FALLBACK_MODEL = "claude-haiku-4-5"  # si quota/rate limit
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0
REQUIRED_JSON_KEYS = {"before", "after", "why", "expected_lift_pct", "effort_hours", "priority", "implementation_notes"}
# V26.X.5 : `headline` est OPTIONNEL pour rétro-compat, mais demandé dans le prompt


# ────────────────────────────────────────────────────────────────
# API CLIENT (lazy import anthropic pour ne pas require tant qu'on n'appelle pas)
# ────────────────────────────────────────────────────────────────

def _load_dotenv_if_needed():
    """P11.7 — auto-load .env si ANTHROPIC_API_KEY absent, évite d'avoir à
    `source .env` manuellement avant chaque run. Sans dépendance externe."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    # Cherche .env dans cwd + parents jusqu'à 5 niveaux
    from pathlib import Path as _P
    cur = _P.cwd()
    for _ in range(6):
        env_path = cur / ".env"
        if env_path.exists():
            try:
                for line in env_path.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    # Override si la clé est absente OU vide (Claude Desktop set
                    # ANTHROPIC_API_KEY="" qui bloquerait le fallback sinon).
                    if k and not os.environ.get(k):
                        os.environ[k] = v
                return
            except Exception:
                return
        if cur.parent == cur:
            break
        cur = cur.parent


def _get_api_client():
    """Lazy : import anthropic seulement quand on l'appelle effectivement."""
    _load_dotenv_if_needed()
    try:
        import anthropic  # type: ignore
    except ImportError:
        print("❌ Le package `anthropic` n'est pas installé. `pip install anthropic`", file=sys.stderr)
        sys.exit(1)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY non défini dans l'environnement NI dans .env", file=sys.stderr)
        print("   Ajouter dans .env : ANTHROPIC_API_KEY=sk-ant-xxx", file=sys.stderr)
        sys.exit(1)
    # Timeout 60s + retry SDK 3 fois sur rate-limits/overloaded (évite blocage indéfini).
    return anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=3)


# ────────────────────────────────────────────────────────────────
# PARSING JSON ROBUSTE (le LLM peut bavarder avant/après)
# ────────────────────────────────────────────────────────────────

def extract_json_from_response(text: str) -> dict | None:
    """Extrait le premier bloc JSON valide de la réponse LLM, même s'il y a du texte autour."""
    if not text:
        return None
    # Essai 1 : parse direct
    try:
        d = json.loads(text.strip())
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    # Essai 2 : regex sur le premier { ... }
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    blob = m.group(0)
    try:
        return json.loads(blob)
    except Exception:
        # Essai 3 : retirer les ```json et ``` markdown
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", blob).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return None


def validate_reco(reco: dict) -> tuple[bool, str]:
    """Retourne (ok, error_msg). Tous les champs requis doivent être présents et typés correctement."""
    missing = REQUIRED_JSON_KEYS - set(reco.keys())
    if missing:
        return False, f"missing keys: {missing}"
    try:
        lift = float(reco.get("expected_lift_pct") or 0)
        if not (0 <= lift <= 50):
            return False, f"expected_lift_pct out of range: {lift}"
        # V25.D.4 fix : LLM produit parfois effort_hours=0 (tâche ultra-rapide).
        # Clamp à 1 minimum au lieu de rejeter en fallback V12 (31.7% fleet bug).
        effort_raw = reco.get("effort_hours")
        try:
            effort = int(effort_raw if effort_raw is not None else 0)
        except (ValueError, TypeError):
            effort = 0
        if effort <= 0:
            reco["effort_hours"] = 1
            effort = 1
        if effort > 80:
            return False, f"effort_hours out of range: {effort}"
        pri = reco.get("priority")
        if pri not in {"P0", "P1", "P2", "P3"}:
            return False, f"invalid priority: {pri}"
    except (ValueError, TypeError) as e:
        return False, f"type error: {e}"
    return True, ""


def compute_ice_score_v13(reco: dict) -> float:
    """ICE = Impact × Confidence × Ease. On en a déjà un framework V12 : impact × (6 - effort).
    V13 : on mappe expected_lift_pct → impact (0-10), effort_hours → effort (1-5).
    """
    lift = float(reco.get("expected_lift_pct") or 0)
    effort_h = float(reco.get("effort_hours") or 8)
    # Impact : lift 0-15% → 1-10
    impact = min(10, max(1, lift / 1.5))
    # Effort : 1h → 1, 8h → 3, 40h → 5
    effort_score = min(5, max(1, (effort_h / 8) + 1))
    # Confidence par priorité
    conf_by_prio = {"P0": 1.0, "P1": 0.85, "P2": 0.7, "P3": 0.55}
    confidence = conf_by_prio.get(reco.get("priority"), 0.6)
    # ICE normalisé (0-100)
    ice = impact * confidence * (6 - effort_score)
    return round(ice * 4, 1)  # *4 pour étaler sur ~0-100


# ────────────────────────────────────────────────────────────────
# FALLBACK TEMPLATE (si LLM échoue)
# ────────────────────────────────────────────────────────────────

def fallback_reco_from_v12(v12_text: str, criterion_id: str, reason: str = "unknown") -> dict:
    """Produit une reco dégradée depuis le texte V12, pour garantir qu'on a tjrs un output.

    P11.3.1 — le flag _fallback_reason rend la cause explicite pour le dashboard ;
    P11.3.6 — la chaîne '(FALLBACK V12' est préfixée pour détection grep.
    """
    return {
        "before": f"⚠️ FALLBACK V12 — LLM échec post-retry ({reason}) — {v12_text[:200]}",
        "after": f"⚠️ FALLBACK V12 — recommandation V12 non-enrichie ({reason}). Relance: --force --only {criterion_id}",
        "why": f"LLM enrichment failed after structured retry ({reason}) — V12 template-based reco restored for non-silent visibility.",
        "expected_lift_pct": 3.0,
        "effort_hours": 4,
        "priority": "P2",
        "implementation_notes": f"criterion={criterion_id} — fallback_reason={reason} — re-run with --force --only {criterion_id}",
        "_fallback": True,
        "_fallback_reason": reason,
    }


# ────────────────────────────────────────────────────────────────
# CALL LLM (async avec retry)
# ────────────────────────────────────────────────────────────────

async def call_llm_async(client, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 2048) -> tuple[dict | None, str, int]:
    """Retourne (reco_dict | None, raw_text, tokens_used). Retry automatique sur rate limit réseau.

    V23.0.opt — system passé en list of blocks avec cache_control:ephemeral pour
    bénéficier du prompt caching (1× write puis 0.1× read). Le system_prompt est
    statique inter-pages → cache hit garanti dès le 2ème call.
    """
    loop = asyncio.get_event_loop()
    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            response = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=[
                        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
                    ],
                    messages=[{"role": "user", "content": user_prompt}],
                ),
            )
            raw = response.content[0].text if response.content else ""
            usage = response.usage
            tokens = getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0)
            tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0
            tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
            parsed = extract_json_from_response(raw)
            return parsed, raw, tokens
        except Exception as e:
            last_err = str(e)
            msg = last_err.lower()
            if "rate" in msg or "429" in msg or "overload" in msg:
                wait = RETRY_BACKOFF ** (attempt + 1)
                await asyncio.sleep(wait)
                continue
            # Erreur non-retriable
            break
    return None, last_err, 0


# ────────────────────────────────────────────────────────────────
# P11.3.4 — GROUNDING CHECK (client name + éléments réels de la page)
# ────────────────────────────────────────────────────────────────

# Seuils minimum (chars) avant de considérer qu'un hint est "check-worthy".
# H1 de 2 mots est trop court pour servir de preuve de grounding.
_HINT_MIN_CHARS = 8


def _norm(s: str) -> str:
    """Normalisation pour matching tolérant (lowercase, espaces collapses)."""
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _compact(s: str) -> str:
    return re.sub(r"[\W_]+", "", _norm(s))


def _client_name_matches(raw_name: str, haystack: str) -> bool:
    name = _norm(raw_name)
    if len(name) < 3:
        return False
    variants = {
        name,
        name.replace("_", " "),
        name.replace("-", " "),
    }
    compact_haystack = _compact(haystack)
    return any(v in haystack or _compact(v) in compact_haystack for v in variants if len(v) >= 3)


def check_grounding(reco: dict, hints: dict) -> tuple[int, list[str]]:
    """Retourne (grounding_score_0_to_3, issues[]).
    - +1 si client_name présent dans before/why/after
    - +1 si H1 OU subtitle réel cité (substring match sur ≥ _HINT_MIN_CHARS)
    - +1 si CTA réel cité OU pas de CTA dans les hints (bonus par défaut)

    On check sur la concatenation before+after+why. 'implementation_notes' ignoré.
    """
    issues = []
    if not hints:
        return 0, ["no_hints_provided"]

    # V23 — Defensive: Haiku can return null for reco_type=skip cases
    haystack = _norm(" ".join([
        reco.get("before") or "",
        reco.get("after") or "",
        reco.get("why") or "",
    ]))

    score = 0

    client_name = hints.get("client_name") or ""
    if _client_name_matches(client_name, haystack):
        score += 1
    else:
        issues.append(f"client_name_missing:{_norm(client_name)!r}")

    h1 = _norm(hints.get("h1_text") or "")
    sub = _norm(hints.get("subtitle_text") or "")
    if (len(h1) >= _HINT_MIN_CHARS and h1[: min(40, len(h1))] in haystack) or (
        len(sub) >= _HINT_MIN_CHARS and sub[: min(40, len(sub))] in haystack
    ):
        score += 1
    else:
        if h1 or sub:
            issues.append("real_copy_not_cited")

    cta = _norm(hints.get("primary_cta_text") or "")
    if len(cta) >= _HINT_MIN_CHARS and cta in haystack:
        score += 1
    elif len(cta) < _HINT_MIN_CHARS:
        score += 1  # bonus : pas de CTA à citer, on ne pénalise pas
    else:
        issues.append(f"cta_not_cited:{cta!r}")

    return score, issues


# ────────────────────────────────────────────────────────────────
# P11.3.1 — STRUCTURED RETRY SUR JSON-FAIL / VALIDATION-FAIL
# ────────────────────────────────────────────────────────────────

MAX_STRUCTURED_RETRIES = 2  # 1 appel initial + 2 retries correctifs = 3 tentatives max
MIN_GROUNDING_SCORE = 1  # /3 — si < 1, retry grounding une fois. Seuil relâché vs 2 pour éviter
# retry sur 85% des cas (test japhy/home 2026-04-19) : beaucoup de recos citent le client
# implicitement (H1 cité, CTA cité) sans forcément dropper le nom de marque dans before/why.


async def call_llm_with_structured_retry(
    client,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_structured_retries: int = MAX_STRUCTURED_RETRIES,
) -> tuple[dict | None, str, int, int, str]:
    """Appelle le LLM puis, si la sortie n'est pas un JSON valide OU ne passe pas
    validate_reco, retry jusqu'à max_structured_retries fois avec un prompt correctif
    qui cite la contrainte violée. Ne tombe sur fallback V12 qu'après épuisement
    des retries structurés.

    Retour : (parsed_valide | None, last_raw, tokens_total, retry_count, fallback_reason).
    fallback_reason = "" si succès ; sinon "parse_failed" ou "validation_failed: <err>".
    """
    retry_count = 0
    last_raw = ""
    last_err = ""
    tokens_total = 0
    current_user = user_prompt

    for attempt in range(1 + max_structured_retries):
        parsed, raw, tokens = await call_llm_async(client, system_prompt, current_user, model)
        tokens_total += tokens
        if raw:
            last_raw = raw

        # Cas 1 : aucun JSON extractible
        if parsed is None:
            last_err = "parse_failed"
            if attempt < max_structured_retries:
                retry_count += 1
                current_user = (
                    user_prompt
                    + "\n\n⚠️ RETRY (structured): ta réponse précédente ne contenait pas de JSON extractible.\n"
                    + "Réponds UNIQUEMENT avec un objet JSON valide (commence par `{`, finit par `}`).\n"
                    + "Pas de texte avant, pas de texte après, pas de ```json fences."
                )
                continue
            return None, last_raw, tokens_total, retry_count, last_err

        # Cas 2 : JSON parsé mais invalide (schéma)
        ok, err = validate_reco(parsed)
        if ok:
            return parsed, last_raw, tokens_total, retry_count, ""

        last_err = f"validation_failed: {err}"
        if attempt < max_structured_retries:
            retry_count += 1
            current_user = (
                user_prompt
                + f"\n\n⚠️ RETRY (structured): ta réponse JSON a échoué la validation — {err}.\n"
                + "Corrige UNIQUEMENT ce point. Respecte strictement :\n"
                + "- keys obligatoires : before, after, why, expected_lift_pct, effort_hours, priority, implementation_notes\n"
                + "- expected_lift_pct : nombre entre 0 et 50\n"
                + "- effort_hours : entier entre 1 et 80\n"
                + "- priority : exactement l'une de 'P0','P1','P2','P3'\n"
                + "- ne renvoie QUE le JSON, rien d'autre."
            )
            continue
        return None, last_raw, tokens_total, retry_count, last_err

    return None, last_raw, tokens_total, retry_count, last_err


# ────────────────────────────────────────────────────────────────
# PROCESS UNE PAGE
# ────────────────────────────────────────────────────────────────

async def process_page(
    client_api,
    prompts_file: Path,
    out_file: Path,
    model: str,
    semaphore: asyncio.Semaphore,
    force: bool = False,
) -> dict:
    """Retourne {client, page, n_prompts, n_ok, n_fallback, tokens_total}."""
    data = json.load(open(prompts_file))
    client = data.get("client")
    page = data.get("page")
    prompts = data.get("prompts", [])

    # Cache : si out_file existe, on repart du dict existant (resume)
    # RÉSILIENCE SaaS : chaque reco est écrite dès qu'elle finit → no data lost on kill
    existing: dict[str, dict] = {}
    if out_file.exists() and not force:
        prev = json.load(open(out_file))
        for r in prev.get("recos", []):
            existing[r["criterion_id"]] = r

    # Lock pour write atomique (pas de race entre coroutines)
    write_lock = asyncio.Lock()

    def _snapshot_file(recos_dict: dict[str, dict], n_prompts: int) -> None:
        """Écrit l'état courant sur disque. Appelé après chaque reco."""
        recos_list = list(recos_dict.values())
        n_skipped = sum(1 for r in recos_list if r.get("_skipped"))
        n_fallback = sum(1 for r in recos_list if r.get("_fallback"))
        n_ok = sum(1 for r in recos_list if not r.get("_fallback") and not r.get("_skipped"))
        tokens_total = sum(r.get("_tokens", 0) for r in recos_list)
        # P11.3.1 — stats retry structuré pour visibilité dashboard + grep
        n_retries_total = sum(r.get("_retry_count", 0) for r in recos_list)
        fallback_reasons = {}
        for r in recos_list:
            if r.get("_fallback"):
                reason = r.get("_fallback_reason", "unknown")
                fallback_reasons[reason] = fallback_reasons.get(reason, 0) + 1
        # P11.3.3 — stats skip pour dashboard
        skipped_reasons = {}
        for r in recos_list:
            if r.get("_skipped"):
                reason = r.get("_skipped_reason", "unknown")
                skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        # P11.3.4 — stats grounding pour dashboard
        grounded = [r.get("_grounding_score") for r in recos_list if r.get("_grounding_score") is not None]
        grounding_avg = round(sum(grounded) / len(grounded), 2) if grounded else None
        grounding_retried = sum(1 for r in recos_list if r.get("_grounding_retried"))
        out = {
            "version": "v13.3.0-reco-final",  # P11.3.4 bumped — grounding post-check + retry
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
        # Écriture atomique via tmp + rename (évite fichier corrompu si kill pendant write)
        tmp = out_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        tmp.replace(out_file)

    async def _one(p):
        crit_id = p.get("criterion_id")
        if not crit_id:
            return None
        if crit_id in existing and not existing[crit_id].get("_fallback") and not existing[crit_id].get("_skipped"):
            # Skip (cache hit)
            return existing[crit_id]

        # P11.3.3 — Honor upstream skip flag (critère ENSEMBLE sans cluster).
        # Pas d'appel API : on écrit un stub explicite pour le dashboard.
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
            # P11.3.1 — structured retry sur JSON-fail / validation-fail avant fallback V12
            parsed, raw, tokens, retry_count, fb_reason = await call_llm_with_structured_retry(
                client_api,
                p["system_prompt"],
                p["user_prompt"],
                model,
            )

            # P11.3.4 — grounding check : si reco valide mais ignore client/éléments
            # réels → une relance ciblée avant d'accepter
            hints = p.get("grounding_hints") or {}
            grounding_score = None
            grounding_issues: list[str] = []
            grounding_retries = 0
            if parsed is not None and hints:
                grounding_score, grounding_issues = check_grounding(parsed, hints)
                if grounding_score < MIN_GROUNDING_SCORE:
                    # Retry une fois avec prompt correctif qui cite les hints
                    grounding_prompt = (
                        p["user_prompt"]
                        + "\n\n⚠️ RETRY GROUNDING: ta reco précédente était trop générique.\n"
                        + f"Issues: {', '.join(grounding_issues)}.\n"
                        + f"Tu DOIS OBLIGATOIREMENT :\n"
                        + f"  - Mentionner '{hints.get('client_name', '')}' par son nom dans 'before' OU 'why'.\n"
                    )
                    if hints.get("h1_text"):
                        grounding_prompt += f"  - Citer l'extrait réel du H1 dans 'before' : \"{hints.get('h1_text')}\".\n"
                    if hints.get("primary_cta_text"):
                        grounding_prompt += f"  - Citer le texte exact du CTA actuel : \"{hints.get('primary_cta_text')}\".\n"
                    grounding_prompt += "Une reco interchangeable entre clients = reco ratée."

                    parsed2, raw2, tokens2, rc2, fb2 = await call_llm_with_structured_retry(
                        client_api,
                        p["system_prompt"],
                        grounding_prompt,
                        model,
                        max_structured_retries=1,  # 1 appel + 1 correctif max, on bascule sinon
                    )
                    grounding_retries = 1
                    retry_count += rc2
                    tokens += tokens2
                    if parsed2 is not None:
                        score2, issues2 = check_grounding(parsed2, hints)
                        if score2 > grounding_score:
                            parsed = parsed2
                            grounding_score = score2
                            grounding_issues = issues2
                            raw = raw2 or raw

        if parsed is None:
            # Fallback V12 visible : _fallback=True + _fallback_reason explicite (P11.3.6)
            reco = fallback_reco_from_v12(p.get("v12_reco_text", ""), crit_id, reason=fb_reason or "unknown")
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
            parsed["ice_score"] = compute_ice_score_v13(parsed)
            parsed["_tokens"] = tokens
            parsed["_retry_count"] = retry_count
            parsed["_grounding_score"] = grounding_score
            parsed["_grounding_issues"] = grounding_issues
            parsed["_grounding_retried"] = bool(grounding_retries)
            parsed["_model"] = model
            reco = parsed

        # ✍️ WRITE-PER-RECO : persist immédiatement sous lock
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

    # Snapshot final (déjà fait par la dernière write-per-reco, mais on garantit la cohérence)
    async with write_lock:
        _snapshot_file(existing, len(prompts))

    retry_note = f" · {n_retries_total} retries" if n_retries_total else ""
    skip_note = f" + {n_skipped} skip" if n_skipped else ""
    print(f"  ✓ {client}/{page}: {n_ok} OK + {n_fallback} fallback{skip_note} · {tokens_total} tokens{retry_note}")
    return {"client": client, "page": page, "n_ok": n_ok, "n_fallback": n_fallback,
            "n_skipped": n_skipped, "tokens": tokens_total, "n_retries": n_retries_total}


# ────────────────────────────────────────────────────────────────
# DRY RUN : pas d'appel API, juste vérifie les prompts
# ────────────────────────────────────────────────────────────────

def dry_run(data_dir: Path) -> None:
    """Vérifie que tous les prompts sont présents + estime le coût."""
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
    # Estimation tokens (rough : 1 token ≈ 4 chars)
    tokens_in = total_chars / 4
    tokens_out = total_prompts * 400  # ~400 out tokens par reco
    # Coût Sonnet 4.6 : $3/M input, $15/M output
    cost_sonnet = (tokens_in / 1_000_000) * 3 + (tokens_out / 1_000_000) * 15
    # Coût Haiku 4.5 : $1/M input, $5/M output
    cost_haiku = (tokens_in / 1_000_000) * 1 + (tokens_out / 1_000_000) * 5
    print(f"\n=== DRY RUN SUMMARY ===")
    print(f"Pages prêtes: {pages}")
    print(f"Prompts total: {total_prompts}")
    print(f"Tokens estimés: ~{int(tokens_in):,} in + ~{int(tokens_out):,} out")
    print(f"Coût estimé Sonnet 4.6 : ${cost_sonnet:.2f}")
    print(f"Coût estimé Haiku 4.5  : ${cost_haiku:.2f}")


# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────

async def _run_async(prompt_files: list[Path], out_files: list[Path], model: str, max_concurrent: int, force: bool):
    client_api = _get_api_client()
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="N'appelle pas l'API, estime juste le coût")
    ap.add_argument("--data-dir", default="data/captures")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-concurrent", type=int, default=5)
    ap.add_argument("--force", action="store_true", help="Force re-call même si le cache existe")
    ap.add_argument("--pages-file", help="Fichier avec une ligne par 'client/page' — batch ciblé")
    args = ap.parse_args()

    base = Path(args.data_dir)
    if args.dry_run:
        dry_run(base)
        return

    # Collecter les pages à traiter
    prompt_files = []
    out_files = []
    if args.pages_file:
        # Batch ciblé depuis fichier (ex: pick_diverse_pages.py --out top50.txt)
        pf_list = Path(args.pages_file).read_text().splitlines()
        for line in pf_list:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("/")
            if len(parts) != 2:
                print(f"⚠️  ligne ignorée: {line!r} (attendu client/page)", file=sys.stderr)
                continue
            client, page = parts
            pf = base / client / page / "recos_v13_prompts.json"
            if not pf.exists():
                print(f"⚠️  manquant: {pf}", file=sys.stderr)
                continue
            prompt_files.append(pf)
            out_files.append(base / client / page / "recos_v13_final.json")
        print(f"   pages-file: {len(prompt_files)} pages chargées depuis {args.pages_file}")
    elif args.all:
        for cd in sorted(base.iterdir()):
            if not cd.is_dir():
                continue
            for pd in sorted(cd.iterdir()):
                if not pd.is_dir():
                    continue
                pf = pd / "recos_v13_prompts.json"
                if pf.exists():
                    prompt_files.append(pf)
                    out_files.append(pd / "recos_v13_final.json")
    else:
        if not args.client or not args.page:
            print("❌ --client et --page requis (ou --all / --pages-file / --dry-run)", file=sys.stderr)
            sys.exit(1)
        pf = base / args.client / args.page / "recos_v13_prompts.json"
        if not pf.exists():
            print(f"❌ {pf} manquant", file=sys.stderr)
            sys.exit(1)
        prompt_files.append(pf)
        out_files.append(base / args.client / args.page / "recos_v13_final.json")

    print(f"→ {len(prompt_files)} page(s), modèle={args.model}, concurrency={args.max_concurrent}")
    asyncio.run(_run_async(prompt_files, out_files, args.model, args.max_concurrent, args.force))


if __name__ == "__main__":
    main()
