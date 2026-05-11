#!/usr/bin/env python3
"""Migrate V27 static dataset to Supabase V28.

Reads ``deliverables/growth_audit_data.js`` (the V27 consolidated bundle:
56 clients x 185 pages x ~3045 recos) and idempotently UPSERTs rows into
the V28 Supabase tables (``clients``, ``audits``, ``recos``).

Idempotent: re-runs safe via ``(org_id, slug)`` and ``(client_id, page_type,
page_slug)`` natural keys.

Usage:
    SUPABASE_URL=https://xxx.supabase.co \
    SUPABASE_SERVICE_ROLE_KEY=eyJ... \
    ORG_SLUG=growth-society \
    python3 scripts/migrate_v27_to_supabase.py

The script intentionally uses only stdlib + ``urllib`` so it runs in any
env without ``pip install``. The Supabase REST endpoint (PostgREST) is used
directly via service-role auth; RLS is bypassed.

If env vars are missing, the script does a DRY-RUN: parses the dataset,
prints the rows it would upsert, exits 0. This makes the script safe to
run from CI smoke tests.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

# Add repo root to sys.path so we can import growthcro.config.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from growthcro import config as gc_config  # noqa: E402 — env access doctrine

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

V27_DATA_PATH = REPO_ROOT / "deliverables" / "growth_audit_data.js"
DOCTRINE_VERSION = "v3.2.1"  # current dataset baseline; V3.3 starts on next audit run.

_cfg = gc_config.get_config()


def _env(name: str, default: str | None = None) -> str | None:
    value = _cfg.system_env(name, default or "")
    return value if value else default


def _dry_run() -> bool:
    return not (_env("SUPABASE_URL") and _env("SUPABASE_SERVICE_ROLE_KEY"))


# ---------------------------------------------------------------------------
# V27 dataset parsing
# ---------------------------------------------------------------------------


def load_v27_bundle(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    marker = raw.find("= {")
    if marker < 0:
        raise ValueError("Could not find '= {' marker in V27 bundle")
    data_str = raw[marker + 2 :].rstrip().rstrip(";").strip()
    return json.loads(data_str)


def normalize_client(raw: dict[str, Any]) -> dict[str, Any]:
    panel = raw.get("panel") or {}
    return {
        "slug": str(raw["id"]),
        "name": raw.get("name") or raw["id"],
        "business_category": raw.get("business_type") or raw.get("category") or None,
        "homepage_url": raw.get("url") or None,
        "brand_dna_json": raw.get("v26", {}).get("brand_dna") or None,
        "panel_role": panel.get("role"),
        "panel_status": panel.get("status"),
    }


def normalize_audit(client_uuid: str, page: dict[str, Any]) -> dict[str, Any]:
    page_type = page.get("page_type") or "unknown"
    url = page.get("url") or ""
    # Derive a stable slug from URL or fall back to page_type ordinal.
    page_slug = url.rsplit("/", 1)[-1] or page_type
    pillars = page.get("pillars") or {}
    scores_json: dict[str, Any] = {"pillars": pillars}
    if "overlays" in page:
        scores_json["overlays"] = page["overlays"]
    if "audit_quality" in page:
        scores_json["audit_quality"] = page["audit_quality"]
    return {
        "client_id": client_uuid,
        "page_type": page_type,
        "page_slug": page_slug[:200],
        "page_url": url or None,
        "doctrine_version": DOCTRINE_VERSION,
        "scores_json": scores_json,
        "total_score": page.get("score_total"),
        "total_score_pct": page.get("score_pct"),
    }


def normalize_recos(audit_uuid: str, page: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for reco in page.get("recos") or []:
        priority = (reco.get("priority") or "P3").upper()
        if priority not in {"P0", "P1", "P2", "P3"}:
            priority = "P3"
        effort = (reco.get("effort") or None)
        if isinstance(effort, str):
            effort = effort.upper()[:1] if effort.upper()[:1] in {"S", "M", "L"} else None
        lift = reco.get("lift") or reco.get("impact") or None
        if isinstance(lift, str):
            lift = lift.upper()[:1] if lift.upper()[:1] in {"S", "M", "L"} else None
        title = (
            reco.get("title")
            or reco.get("name")
            or reco.get("criterion")
            or reco.get("criterion_id")
            or "(untitled reco)"
        )
        content = {
            k: v
            for k, v in reco.items()
            if k not in {"priority", "effort", "lift", "title", "criterion_id"}
        }
        out.append(
            {
                "audit_id": audit_uuid,
                "criterion_id": reco.get("criterion_id") or reco.get("criterion") or None,
                "priority": priority,
                "effort": effort,
                "lift": lift,
                "title": str(title)[:500],
                "content_json": content,
                "oco_anchors_json": reco.get("oco_anchors") or None,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Supabase REST (PostgREST) thin client
# ---------------------------------------------------------------------------


class SupabaseError(RuntimeError):
    pass


def _request(method: str, path: str, body: Any | None = None, headers: dict[str, str] | None = None) -> Any:
    url_base = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url_base or not key:
        raise SupabaseError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
    full = f"{url_base.rstrip('/')}/rest/v1/{path.lstrip('/')}"
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req_headers = {
        "apikey": key,
        "authorization": f"Bearer {key}",
        "content-type": "application/json",
        "prefer": "return=representation,resolution=merge-duplicates",
        **(headers or {}),
    }
    req = urlrequest.Request(full, data=payload, method=method, headers=req_headers)
    try:
        with urlrequest.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SupabaseError(f"HTTP {e.code} {method} {path}: {detail}") from e


def upsert_clients(rows: list[dict[str, Any]], org_id: str) -> dict[str, str]:
    """Returns mapping {slug -> uuid}."""
    if not rows:
        return {}
    enriched = [{"org_id": org_id, **r} for r in rows]
    res = _request(
        "POST",
        "clients?on_conflict=org_id,slug",
        body=enriched,
        headers={"prefer": "return=representation,resolution=merge-duplicates"},
    )
    return {r["slug"]: r["id"] for r in (res or [])}


def upsert_audits(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    # No unique key on (client_id, page_type, page_slug) — insert + dedupe is
    # caller's responsibility. We choose insert-only here; on re-run, the
    # script first deletes any existing rows for the migrated clients.
    res = _request("POST", "audits", body=rows)
    return [r["id"] for r in (res or [])]


def upsert_recos(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    # Batch to stay under PostgREST payload limits.
    inserted = 0
    batch = 500
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        res = _request("POST", "recos", body=chunk)
        inserted += len(res or [])
    return inserted


def delete_audits_for_clients(client_uuids: list[str]) -> None:
    if not client_uuids:
        return
    # PostgREST supports `client_id=in.(uuid1,uuid2,...)`.
    ids = ",".join(client_uuids)
    _request("DELETE", f"audits?client_id=in.({ids})")


def ensure_org(slug: str, name: str) -> str:
    """Idempotent. Returns org uuid. Requires the org to exist OR an owner_id env."""
    res = _request("GET", f"organizations?slug=eq.{slug}&select=id&limit=1")
    if res:
        return res[0]["id"]
    owner = _env("ORG_OWNER_ID")
    if not owner:
        raise SupabaseError(
            f"Organization '{slug}' not found and ORG_OWNER_ID not set. "
            "Create the org first via the webapp signup flow."
        )
    res = _request(
        "POST",
        "organizations",
        body=[{"slug": slug, "name": name, "owner_id": owner}],
    )
    return res[0]["id"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if not V27_DATA_PATH.exists():
        print(f"[migrate] Missing V27 bundle: {V27_DATA_PATH}", file=sys.stderr)
        return 2
    bundle = load_v27_bundle(V27_DATA_PATH)
    clients = bundle.get("clients") or []
    if not clients:
        print("[migrate] No clients in bundle.", file=sys.stderr)
        return 1

    fleet = bundle.get("fleet") or {}
    print(
        f"[migrate] V27 bundle: {len(clients)} clients · "
        f"{fleet.get('n_pages', '?')} pages · {fleet.get('n_recos', '?')} recos"
    )

    dry = _dry_run()
    if dry:
        print("[migrate] DRY-RUN (set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY to actually write).")

    # Normalize clients
    client_rows = [normalize_client(c) for c in clients]
    print(f"[migrate] Normalized {len(client_rows)} client rows.")

    if dry:
        # Just preview a couple rows and count audits/recos.
        n_audits = sum(len(c.get("pages") or []) for c in clients)
        n_recos = sum(len(p.get("recos") or []) for c in clients for p in (c.get("pages") or []))
        print(f"[migrate] Would upsert {len(client_rows)} clients / {n_audits} audits / {n_recos} recos.")
        print("[migrate] Sample client row:")
        print(json.dumps(client_rows[0], indent=2, ensure_ascii=False)[:1200])
        return 0

    # Live mode
    org_slug = _env("ORG_SLUG", "growth-society") or "growth-society"
    org_name = _env("ORG_NAME", "Growth Society") or "Growth Society"
    print(f"[migrate] Ensuring org '{org_slug}' ...")
    org_id = ensure_org(org_slug, org_name)
    print(f"[migrate]   org_id = {org_id}")

    print("[migrate] Upserting clients ...")
    slug_to_uuid = upsert_clients(client_rows, org_id=org_id)
    print(f"[migrate]   {len(slug_to_uuid)} clients upserted.")

    print("[migrate] Cleaning existing audits for these clients (re-run safe) ...")
    delete_audits_for_clients(list(slug_to_uuid.values()))

    # Now insert audits + recos per client
    total_audits, total_recos = 0, 0
    for raw_client in clients:
        slug = raw_client["id"]
        client_uuid = slug_to_uuid.get(slug)
        if not client_uuid:
            print(f"[migrate]   skip {slug} (no uuid)")
            continue
        audit_payloads = []
        per_page: list[tuple[int, dict[str, Any]]] = []
        for idx, page in enumerate(raw_client.get("pages") or []):
            audit_payloads.append(normalize_audit(client_uuid, page))
            per_page.append((idx, page))
        if not audit_payloads:
            continue
        audit_ids = upsert_audits(audit_payloads)
        total_audits += len(audit_ids)
        reco_payloads: list[dict[str, Any]] = []
        for audit_uuid, (_, page) in zip(audit_ids, per_page):
            reco_payloads.extend(normalize_recos(audit_uuid, page))
        if reco_payloads:
            n = upsert_recos(reco_payloads)
            total_recos += n
        # Tiny throttle to be polite with hosted Supabase rate-limits.
        time.sleep(0.05)

    print(f"[migrate] Done: {len(slug_to_uuid)} clients, {total_audits} audits, {total_recos} recos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
