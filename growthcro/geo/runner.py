"""GEO Monitor — per-engine query execution with defensive no-key handling.

Mono-concern : API client. One small entry point `run_engine()` that takes a
(engine, query, brand, keywords) tuple and returns a `RunResult` whether or
not the relevant API key is provisioned.

Engines :
  - anthropic   : `anthropic.Anthropic.messages.create(...)` — SDK already a
                  runtime dep (requirements.txt).
  - openai      : HTTPS POST to v1/chat/completions via stdlib urllib (no
                  new pip dep — `openai` SDK not in requirements.txt).
  - perplexity  : HTTPS POST to v1/chat/completions (OpenAI-compatible
                  schema) via stdlib urllib.

Defensive : if the relevant key is missing, returns a sentinel `RunResult`
with `skipped=True` + `skip_reason='no_api_key'`. The UI and the dispatcher
both treat this as a non-error empty row — the migration ships before the
keys are provisioned, so this path is exercised on every preview deploy.

Env var lookups go through `growthcro.config.config` exclusively (CLAUDE.md
anti-pattern #9). `OPENAI_API_KEY` and `PERPLEXITY_API_KEY` accessors are
already declared on `_Config` and listed in `_KNOWN_VARS`.

Cost estimate :
  - anthropic   : claude-haiku-4-5 ~ $0.001 / 1k input + $0.005 / 1k output
  - openai      : gpt-4o-mini ~ $0.00015 / 1k input + $0.0006 / 1k output
  - perplexity  : sonar-small ~ $0.0002 / 1k tokens (approx)
We surface a rough `cost_usd` per call based on token usage when available,
or 0.0 when the engine response doesn't expose tokens. Never zero on a
successful call — fallback is a flat 0.001 USD so the cumulative card has
signal even before the engines report usage payloads.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable, Literal

from growthcro.config import config
from growthcro.geo.scorer import compute_presence_score
from growthcro.observability.logger import get_logger

logger = get_logger(__name__)

EngineName = Literal["anthropic", "openai", "perplexity"]
SUPPORTED_ENGINES: tuple[EngineName, ...] = ("anthropic", "openai", "perplexity")

_HTTP_TIMEOUT_SEC = 30.0
_MAX_OUTPUT_TOKENS = 600
_FALLBACK_COST_USD = 0.001


@dataclass
class RunResult:
    """Outcome of a single engine probe.

    Persisted by the CLI to Supabase `geo_audits` (one row per probe) and
    serialized to JSON for the worker dispatcher's stdout tail.
    """

    engine: EngineName
    query: str
    response_text: str | None = None
    presence_score: float | None = None
    mentioned_terms: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    skipped: bool = False
    skip_reason: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "query": self.query,
            "response_text": self.response_text,
            "presence_score": self.presence_score,
            "mentioned_terms": list(self.mentioned_terms),
            "cost_usd": float(self.cost_usd),
            "skipped": bool(self.skipped),
            "skip_reason": self.skip_reason,
            "error": self.error,
        }


def _resolve_key(engine: EngineName) -> str | None:
    if engine == "anthropic":
        return config.anthropic_api_key()
    if engine == "openai":
        return config.openai_api_key()
    if engine == "perplexity":
        return config.perplexity_api_key()
    return None


def _http_json_post(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SEC) as resp:  # noqa: S310 — known HTTPS URLs only
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw) if raw else {}


def _call_anthropic(api_key: str, query: str) -> tuple[str, float]:
    try:
        import anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover — SDK is in requirements.txt
        raise RuntimeError(f"anthropic SDK not installed: {exc}") from exc
    client = anthropic.Anthropic(api_key=api_key, timeout=_HTTP_TIMEOUT_SEC, max_retries=2)
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=_MAX_OUTPUT_TOKENS,
        messages=[{"role": "user", "content": query}],
    )
    # SDK exposes a typed `content` list — concatenate text blocks.
    parts: list[str] = []
    for blk in getattr(msg, "content", []) or []:
        text = getattr(blk, "text", None)
        if isinstance(text, str):
            parts.append(text)
    text_out = "\n".join(parts).strip()
    usage = getattr(msg, "usage", None)
    in_tokens = float(getattr(usage, "input_tokens", 0) or 0)
    out_tokens = float(getattr(usage, "output_tokens", 0) or 0)
    cost = (in_tokens / 1000.0) * 0.001 + (out_tokens / 1000.0) * 0.005
    return text_out, max(cost, _FALLBACK_COST_USD)


def _call_openai(api_key: str, query: str) -> tuple[str, float]:
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": query}],
        "max_tokens": _MAX_OUTPUT_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = _http_json_post("https://api.openai.com/v1/chat/completions", headers, payload)
    choices = data.get("choices") or []
    text_out = ""
    if isinstance(choices, list) and choices:
        first = choices[0]
        msg = first.get("message") if isinstance(first, dict) else None
        if isinstance(msg, dict):
            text_out = str(msg.get("content") or "").strip()
    usage = data.get("usage") if isinstance(data, dict) else None
    in_tokens = float((usage or {}).get("prompt_tokens") or 0)
    out_tokens = float((usage or {}).get("completion_tokens") or 0)
    cost = (in_tokens / 1000.0) * 0.00015 + (out_tokens / 1000.0) * 0.0006
    return text_out, max(cost, _FALLBACK_COST_USD)


def _call_perplexity(api_key: str, query: str) -> tuple[str, float]:
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": query}],
        "max_tokens": _MAX_OUTPUT_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = _http_json_post("https://api.perplexity.ai/chat/completions", headers, payload)
    choices = data.get("choices") or []
    text_out = ""
    if isinstance(choices, list) and choices:
        first = choices[0]
        msg = first.get("message") if isinstance(first, dict) else None
        if isinstance(msg, dict):
            text_out = str(msg.get("content") or "").strip()
    usage = data.get("usage") if isinstance(data, dict) else None
    total_tokens = float((usage or {}).get("total_tokens") or 0)
    cost = (total_tokens / 1000.0) * 0.0002
    return text_out, max(cost, _FALLBACK_COST_USD)


def run_engine(
    engine: EngineName,
    query: str,
    brand: str,
    brand_keywords: Iterable[str],
) -> RunResult:
    """Execute a single (engine, query) probe. Never raises.

    Returns a `RunResult` with one of three shapes :
      1. skipped=True, skip_reason='no_api_key' — when the key is unset.
      2. skipped=False, error='<message>' — when the SDK / HTTP call fails.
      3. skipped=False, response_text + presence_score — happy path.

    The CLI persists every result, so the UI can surface skipped+errored
    probes (the consultant SEES that GEO is dormant — vs silent absence).
    """
    if engine not in SUPPORTED_ENGINES:
        return RunResult(
            engine=engine,
            query=query,
            error=f"unknown engine {engine!r}",
        )
    api_key = _resolve_key(engine)
    if not api_key:
        logger.info(
            "geo.run_engine skipped",
            extra={"engine": engine, "reason": "no_api_key"},
        )
        return RunResult(
            engine=engine,
            query=query,
            skipped=True,
            skip_reason="no_api_key",
        )

    started = time.monotonic()
    try:
        if engine == "anthropic":
            text, cost = _call_anthropic(api_key, query)
        elif engine == "openai":
            text, cost = _call_openai(api_key, query)
        else:
            text, cost = _call_perplexity(api_key, query)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            body = ""
        logger.warning(
            "geo.run_engine http_error",
            extra={"engine": engine, "code": exc.code, "body": body},
        )
        return RunResult(engine=engine, query=query, error=f"http_{exc.code}: {body[:160]}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("geo.run_engine network_error", extra={"engine": engine, "err": str(exc)})
        return RunResult(engine=engine, query=query, error=f"network: {exc}")
    except Exception as exc:  # pragma: no cover — defensive last-resort
        logger.warning("geo.run_engine sdk_error", extra={"engine": engine, "err": str(exc)})
        return RunResult(engine=engine, query=query, error=f"sdk: {exc}")

    score, terms = compute_presence_score(text, brand, list(brand_keywords))
    duration = round(time.monotonic() - started, 2)
    logger.info(
        "geo.run_engine ok",
        extra={"engine": engine, "duration_sec": duration, "score": score, "cost_usd": cost},
    )
    return RunResult(
        engine=engine,
        query=query,
        response_text=text or None,
        presence_score=score,
        mentioned_terms=terms,
        cost_usd=round(cost, 6),
    )


__all__ = ["RunResult", "SUPPORTED_ENGINES", "EngineName", "run_engine"]
