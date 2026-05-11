#!/usr/bin/env python3
"""
web_vitals_adapter.py — GrowthCRO V12 S-04 adapter Web Vitals.

STATUS : stub actif. Les 3 providers ci-dessous sont implémentés à minima mais
désactivés par défaut (`PROVIDER = "dom_hints"`). Pour basculer en prod, définir
l'env var `GROWTHCRO_WEB_VITALS_PROVIDER` à :
  - "lighthouse"    → exécute `lighthouse` CLI en local (nécessite `npm i -g lighthouse`)
  - "psi"           → appelle PageSpeed Insights API (nécessite `GROWTHCRO_PSI_KEY`)
  - "crux"          → appelle CrUX API (nécessite `GROWTHCRO_CRUX_KEY`)
  - "dom_hints" (default) → pas d'appel externe, utilise les hints DOM déjà captés

Doctrine seuils (A-10) : CLS<0.1 / LCP<2.5s / INP<200ms.
  - Top : 3/3 passent
  - OK  : 2/3
  - Critical : ≤1/3 OU API indisponible ET hints DOM négatifs

Retourne toujours :
  {
    "provider": str,
    "available": bool,
    "metrics": {"lcp_ms": float|None, "cls": float|None, "inp_ms": float|None},
    "thresholds_passed": int (0-3),
    "verdict": "top"|"ok"|"critical"|"unknown",
    "source_url": str|None,
    "fetched_at": iso8601|None,
    "fallback_reason": str|None,
  }
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any
from growthcro.config import config
# Doctrine thresholds (A-10)
LCP_THRESHOLD_MS = 2500
CLS_THRESHOLD = 0.10
INP_THRESHOLD_MS = 200


def _verdict(passed: int) -> str:
    if passed >= 3:
        return "top"
    if passed >= 2:
        return "ok"
    return "critical"


def _count_passed(lcp: float | None, cls: float | None, inp: float | None) -> int:
    p = 0
    if lcp is not None and lcp < LCP_THRESHOLD_MS:
        p += 1
    if cls is not None and cls < CLS_THRESHOLD:
        p += 1
    if inp is not None and inp < INP_THRESHOLD_MS:
        p += 1
    return p


# ───────────────────────────── Providers ─────────────────────────────

def _run_lighthouse(url: str, timeout: int = 60) -> dict[str, Any]:
    """Run local lighthouse CLI. Returns metrics dict or raises."""
    cmd = ["lighthouse", url, "--output=json", "--quiet",
           "--chrome-flags=--headless --no-sandbox"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"lighthouse exit {r.returncode}: {r.stderr[:200]}")
    data = json.loads(r.stdout)
    audits = data.get("audits", {})
    return {
        "lcp_ms": audits.get("largest-contentful-paint", {}).get("numericValue"),
        "cls": audits.get("cumulative-layout-shift", {}).get("numericValue"),
        "inp_ms": audits.get("interaction-to-next-paint", {}).get("numericValue"),
    }


def _run_psi(url: str, api_key: str, timeout: int = 30) -> dict[str, Any]:
    """Call PageSpeed Insights API. Returns metrics dict."""
    qs = urllib.parse.urlencode({
        "url": url, "key": api_key,
        "strategy": "mobile", "category": "PERFORMANCE",
    })
    api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?{qs}"
    with urllib.request.urlopen(api, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    lr = (payload.get("lighthouseResult") or {}).get("audits", {})
    return {
        "lcp_ms": lr.get("largest-contentful-paint", {}).get("numericValue"),
        "cls": lr.get("cumulative-layout-shift", {}).get("numericValue"),
        "inp_ms": lr.get("interaction-to-next-paint", {}).get("numericValue"),
    }


def _run_crux(url: str, api_key: str, timeout: int = 30) -> dict[str, Any]:
    """Call CrUX API. Returns p75 metrics dict."""
    api = f"https://chromeuxreport.googleapis.com/v1/records:queryRecord?key={api_key}"
    body = json.dumps({"url": url, "formFactor": "PHONE"}).encode("utf-8")
    req = urllib.request.Request(api, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    metrics = (payload.get("record") or {}).get("metrics", {}) or {}
    def _p75(k):
        m = metrics.get(k, {})
        pct = m.get("percentiles", {}).get("p75")
        return float(pct) if pct is not None else None
    return {
        "lcp_ms": _p75("largest_contentful_paint"),
        "cls": _p75("cumulative_layout_shift"),
        "inp_ms": _p75("interaction_to_next_paint"),
    }


# ───────────────────────────── Adapter façade ────────────────────────

def fetch_web_vitals(url: str, dom_hints: dict | None = None) -> dict[str, Any]:
    """Entrypoint adapter. Returns a uniform envelope regardless of provider."""
    provider = config.web_vitals_provider("dom_hints").lower()
    now = datetime.utcnow().isoformat() + "Z"
    envelope: dict[str, Any] = {
        "provider": provider,
        "available": False,
        "metrics": {"lcp_ms": None, "cls": None, "inp_ms": None},
        "thresholds_passed": 0,
        "verdict": "unknown",
        "source_url": url,
        "fetched_at": None,
        "fallback_reason": None,
    }

    try:
        if provider == "lighthouse":
            m = _run_lighthouse(url)
        elif provider == "psi":
            key = config.psi_key()
            if not key:
                raise EnvironmentError("GROWTHCRO_PSI_KEY not set")
            m = _run_psi(url, key)
        elif provider == "crux":
            key = config.crux_key()
            if not key:
                raise EnvironmentError("GROWTHCRO_CRUX_KEY not set")
            m = _run_crux(url, key)
        elif provider == "dom_hints":
            # Pas d'appel externe → restitue simplement verdict vide + marque "dom_fallback"
            envelope["fallback_reason"] = "provider=dom_hints (no external call)"
            envelope["provider_notes"] = (
                "Utilise uniquement les hints DOM captés par ghost_capture. "
                "Activer `GROWTHCRO_WEB_VITALS_PROVIDER=psi|lighthouse|crux` pour mesures réelles."
            )
            return envelope
        else:
            envelope["fallback_reason"] = f"Unknown provider '{provider}' — expected lighthouse|psi|crux|dom_hints"
            return envelope

        envelope["metrics"] = m
        envelope["thresholds_passed"] = _count_passed(m.get("lcp_ms"), m.get("cls"), m.get("inp_ms"))
        envelope["verdict"] = _verdict(envelope["thresholds_passed"])
        envelope["available"] = True
        envelope["fetched_at"] = now
    except Exception as e:
        envelope["fallback_reason"] = f"{type(e).__name__}: {e}"

    return envelope


# ───────────────────────────── CLI ───────────────────────────────────

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--provider", default=None,
                   help="Force provider (overrides env). Options: lighthouse|psi|crux|dom_hints")
    args = p.parse_args()
    if args.provider:
        config.override_env("GROWTHCRO_WEB_VITALS_PROVIDER", args.provider)
    r = fetch_web_vitals(args.url)
    print(json.dumps(r, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
