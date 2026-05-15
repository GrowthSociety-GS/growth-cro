"""Pure presence-score computation for the GEO Monitor.

Mono-concern : I/O serialization — deterministic, dict↔float transform with
no Anthropic / OpenAI / Supabase SDK touched. Importable from a CI test
without any env vars set.

Formula (Task 009 spec) :
    presence_score = brand_weight + keyword_weight
        brand_weight   = 0.5 if the brand surfaces in the response (regex), else 0.0
        keyword_weight = 0.5 * min(1, keyword_hits / max(1, len(brand_keywords)))
    → bounded [0.0, 1.0]

The regex is case-insensitive and word-bounded to avoid false positives
("Apple" matching "applet" or "pineapple"). For multi-token brands ("Coca-
Cola") we escape the literal phrase. Keyword hits are deduplicated by token
so listing the same keyword 10× in the response counts once.

The output is :
    (presence_score: float, mentioned_terms: list[str])

`mentioned_terms` is the union of the matched brand + matched keywords —
persisted to `geo_audits.mentioned_terms` for the per-client drilldown.
"""
from __future__ import annotations

import re
from typing import Iterable


def _normalize(value: str | None) -> str:
    return (value or "").strip()


def _word_boundary_match(haystack: str, needle: str) -> bool:
    """Case-insensitive, word-bounded substring match.

    Treats hyphens and apostrophes as word characters so "Coca-Cola" and
    "L'Oréal" match as single tokens. Returns False on empty needle.
    """
    needle = _normalize(needle)
    if not needle:
        return False
    pattern = r"(?<![\w\-'])" + re.escape(needle) + r"(?![\w\-'])"
    return re.search(pattern, haystack, flags=re.IGNORECASE) is not None


def compute_presence_score(
    response_text: str | None,
    brand: str,
    brand_keywords: Iterable[str],
) -> tuple[float, list[str]]:
    """Return (presence_score, mentioned_terms) for a single engine response.

    Args:
        response_text: The raw text returned by the engine. None or empty
            yields (0.0, []).
        brand: The client's canonical brand name (e.g. "Stripe").
        brand_keywords: An iterable of differentiator keywords ("payment",
            "API", "infrastructure"). Empty iterable disables the keyword
            half of the formula (keyword_weight = 0).

    Returns:
        (score, mentioned_terms) — score is a float in [0.0, 1.0] (rounded
        to 4 decimals so it round-trips through Postgres numeric without
        FP noise) ; mentioned_terms is a sorted list of unique matched
        tokens (brand first if matched).
    """
    text = _normalize(response_text)
    if not text:
        return (0.0, [])

    matched: list[str] = []
    brand_weight = 0.0
    if _word_boundary_match(text, brand):
        brand_weight = 0.5
        matched.append(brand)

    # Deduplicate + skip empties.
    keywords = [_normalize(k) for k in brand_keywords if _normalize(k)]
    keywords = sorted(set(keywords), key=str.lower)
    hits: list[str] = []
    for kw in keywords:
        if _word_boundary_match(text, kw):
            hits.append(kw)

    if keywords:
        ratio = min(1.0, len(hits) / float(len(keywords)))
        keyword_weight = 0.5 * ratio
    else:
        keyword_weight = 0.0

    matched.extend(hits)
    # Preserve order : brand first if matched, then alphabetical keywords.
    seen: set[str] = set()
    deduped: list[str] = []
    for t in matched:
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(t)

    score = round(brand_weight + keyword_weight, 4)
    return (score, deduped)


__all__ = ["compute_presence_score"]
