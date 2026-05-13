#!/usr/bin/env python3
"""Migrate canonical disk audit truth to Supabase V28 (Wave C.1, 2026-05-14).

Replaces ``scripts/migrate_v27_to_supabase.py`` which reads
``deliverables/growth_audit_data.js`` — an aggregated bundle stripped of the
rich V13 enricher fields (``reco_text``, ``anti_patterns``, ``feasibility``,
``pillar``, ``schwartz_awareness``, ``ab_variants``, etc.). That's the root
cause confirmed by audit A.10 (2026-05-14): Supabase ``recos.content_json`` had
0% of the fields ``RichRecoCard.tsx`` expects.

This script walks ``data/captures/<client>/<page>/`` directly and UPSERTs:

- ``clients``  — slug, name, business_category, homepage_url, brand_dna_json,
                 panel_role, panel_status (panel from ``curated_clients_v27.json``,
                 brand_dna from ``data/captures/<c>/brand_dna.json``)
- ``audits``   — per (client, page_type) with ``scores_json`` = {pillars: 6
                 from ``score_<pillar>.json``, aggregate from
                 ``score_page_type.json``, overlays + specific + utility_banner}
- ``recos``    — per audit with **full** ``content_json`` preserving the rich
                 V13 enricher payload (one row per reco in ``recos_enriched.json``)

Idempotent: re-runs delete existing audits/recos for each client before
re-inserting (same pattern as the legacy script).

Usage:
    # Dry-run (no creds → reports what would happen)
    python3 scripts/migrate_disk_to_supabase.py

    # Live
    SUPABASE_URL=https://xxx.supabase.co \
    SUPABASE_SERVICE_ROLE_KEY=eyJ... \
    ORG_SLUG=growth-society \
    python3 scripts/migrate_disk_to_supabase.py

    # Single client (debug)
    python3 scripts/migrate_disk_to_supabase.py --only weglot

    # Skip clients table (audits + recos only — useful post-bootstrap)
    python3 scripts/migrate_disk_to_supabase.py --audits-only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from growthcro import config as gc_config  # noqa: E402 — env access doctrine

# ---------------------------------------------------------------------------
# Paths + constants
# ---------------------------------------------------------------------------

CAPTURES_DIR = REPO_ROOT / "data" / "captures"
PANEL_PATH = REPO_ROOT / "data" / "curated_clients_v27.json"
PANEL_FALLBACK = REPO_ROOT / "data" / "curated_clients_v26.json"
CLIENTS_DB = REPO_ROOT / "data" / "clients_database.json"
DOCTRINE_VERSION_DEFAULT = "v3.2.1"
PILLAR_FILES = (
    "score_hero.json",
    "score_persuasion.json",
    "score_ux.json",
    "score_coherence.json",
    "score_psycho.json",
    "score_tech.json",
)
UTILITY_BANNER_FILE = "score_utility_banner.json"
SPECIFIC_FILE = "score_specific.json"
SEMANTIC_FILE = "score_semantic.json"
PAGE_TYPE_FILE = "score_page_type.json"
RECOS_FILE = "recos_enriched.json"
BRAND_DNA_FILE = "brand_dna.json"

# Fields stored in dedicated reco columns — exclude from content_json to avoid
# duplication. Everything else from the rich enricher payload is preserved.
RECO_DEDICATED_COLS = {"priority", "effort", "lift", "title", "criterion_id"}

_cfg = gc_config.get_config()


def _env(name: str, default: str | None = None) -> str | None:
    value = _cfg.system_env(name, default or "")
    return value if value else default


def _dry_run() -> bool:
    return not (_env("SUPABASE_URL") and _env("SUPABASE_SERVICE_ROLE_KEY"))


# ---------------------------------------------------------------------------
# Disk readers — silent if file missing (returns None / empty)
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[migrate] WARN failed to read {path}: {exc}", file=sys.stderr)
        return None


def load_panel() -> dict[str, dict[str, Any]]:
    """Returns slug → panel entry (role + status + url + business_type)."""
    raw = _read_json(PANEL_PATH) or _read_json(PANEL_FALLBACK)
    if not raw:
        return {}
    clients = raw.get("clients") or raw.get("panel") or []
    out: dict[str, dict[str, Any]] = {}
    for entry in clients:
        slug = entry.get("id") or entry.get("slug")
        if slug:
            out[slug] = entry
    return out


def load_clients_db() -> dict[str, dict[str, Any]]:
    """Fallback metadata source from clients_database.json."""
    raw = _read_json(CLIENTS_DB) or {}
    if isinstance(raw, dict):
        if "clients" in raw:
            return {c.get("id") or c.get("slug"): c for c in (raw["clients"] or []) if c}
        return raw
    if isinstance(raw, list):
        return {c.get("id") or c.get("slug"): c for c in raw if c}
    return {}


def discover_clients() -> list[str]:
    """Walk data/captures/ and return list of client slugs (dirs with content)."""
    if not CAPTURES_DIR.is_dir():
        return []
    out: list[str] = []
    for entry in sorted(CAPTURES_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
            continue
        # A client dir is one that has at least one page subdir with recos_enriched.json
        has_recos = any(
            (sub / RECOS_FILE).exists() for sub in entry.iterdir() if sub.is_dir()
        )
        if has_recos or (entry / BRAND_DNA_FILE).exists():
            out.append(entry.name)
    return out


def discover_pages(client: str) -> list[str]:
    """Return list of page_type slugs for a client (dirs with recos_enriched.json)."""
    client_dir = CAPTURES_DIR / client
    if not client_dir.is_dir():
        return []
    out: list[str] = []
    for sub in sorted(client_dir.iterdir()):
        if not sub.is_dir() or sub.name.startswith("_"):
            continue
        if (sub / RECOS_FILE).exists() or (sub / PAGE_TYPE_FILE).exists():
            out.append(sub.name)
    return out


def load_brand_dna(client: str) -> dict[str, Any] | None:
    return _read_json(CAPTURES_DIR / client / BRAND_DNA_FILE)


def load_page_scores(client: str, page: str) -> dict[str, Any]:
    """Aggregate score_page_type + 6 pillars + utility_banner + overlays + specific."""
    page_dir = CAPTURES_DIR / client / page
    aggregate = _read_json(page_dir / PAGE_TYPE_FILE) or {}
    pillars: dict[str, Any] = {}
    for fname in PILLAR_FILES:
        data = _read_json(page_dir / fname)
        if data:
            pillar_id = data.get("pillar") or fname.replace("score_", "").replace(".json", "")
            pillars[pillar_id] = data
    utility_banner = _read_json(page_dir / UTILITY_BANNER_FILE)
    specific = _read_json(page_dir / SPECIFIC_FILE)
    semantic = _read_json(page_dir / SEMANTIC_FILE)
    return {
        "aggregate": aggregate.get("aggregate") if isinstance(aggregate, dict) else None,
        "pillars": pillars,
        "utility_banner": utility_banner,
        "specific": specific,
        "semantic_overlay": semantic,
        "applicability_overlay": (aggregate or {}).get("applicability_overlay"),
        "contextual_overlay": (aggregate or {}).get("contextual_overlay"),
        "funnel": (aggregate or {}).get("funnel"),
        "exclusions": (aggregate or {}).get("exclusions"),
        "doctrineVersion": (aggregate or {}).get("doctrineVersion") or DOCTRINE_VERSION_DEFAULT,
        "pageType": (aggregate or {}).get("pageType") or page,
        "generatedAt": (aggregate or {}).get("generatedAt"),
    }


def load_page_recos(client: str, page: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Returns (rich_recos_list, page_meta) from recos_enriched.json."""
    data = _read_json(CAPTURES_DIR / client / page / RECOS_FILE)
    if not data:
        return [], {}
    recos = data.get("recos") or []
    meta = {
        "doctrine_version": data.get("doctrine_version"),
        "enricher_version": data.get("enricher_version"),
        "business_category": data.get("business_category"),
        "page_type": data.get("page_type"),
        "schwartz_awareness": data.get("schwartz_awareness"),
        "v32_applicability_overlay": data.get("v32_applicability_overlay"),
        "v32_contextual_overlay": data.get("v32_contextual_overlay"),
    }
    return recos, meta


# ---------------------------------------------------------------------------
# Normalizers — disk shape → Supabase row shape
# ---------------------------------------------------------------------------


def normalize_client(
    slug: str, panel: dict[str, Any], clients_db: dict[str, Any], brand_dna: dict[str, Any] | None
) -> dict[str, Any]:
    p = panel or {}
    db = clients_db or {}
    return {
        "slug": slug,
        "name": p.get("name") or db.get("name") or slug,
        "business_category": (
            p.get("business_type") or p.get("category") or db.get("business_type") or db.get("category")
        ),
        "homepage_url": p.get("url") or db.get("url") or db.get("homepage_url"),
        "brand_dna_json": brand_dna,  # full disk JSON, no stripping
        "panel_role": (p.get("panel") or {}).get("role") if isinstance(p.get("panel"), dict) else p.get("panel_role"),
        "panel_status": (p.get("panel") or {}).get("status") if isinstance(p.get("panel"), dict) else p.get("panel_status"),
    }


def _bucket_effort_or_lift(val: Any) -> str | None:
    """Convert effort/lift to S/M/L per Supabase schema check constraint."""
    if isinstance(val, str):
        upper = val.upper()[:1]
        return upper if upper in {"S", "M", "L"} else None
    if isinstance(val, (int, float)) and val > 0:
        # int 1-5 (effort) or 0-100 (lift): conservative bucketing
        if val <= 5:
            return "S" if val <= 2 else ("M" if val <= 4 else "L")
        # treat as 0-100 score
        return "S" if val <= 33 else ("M" if val <= 66 else "L")
    if isinstance(val, dict):
        # feasibility dict from enricher: {effort_1to5, effort_days, feasibility_flag, ...}
        flag = (val.get("feasibility_flag") or "").lower()
        if flag in {"easy"}:
            return "S"
        if flag in {"medium"}:
            return "M"
        if flag in {"hard", "deferred"}:
            return "L"
        days = val.get("effort_days")
        if isinstance(days, (int, float)):
            return "S" if days <= 3 else ("M" if days <= 7 else "L")
    return None


def normalize_audit(
    client_uuid: str, page_type: str, page_meta: dict[str, Any], scores: dict[str, Any]
) -> dict[str, Any]:
    aggregate = scores.get("aggregate") or {}
    return {
        "client_id": client_uuid,
        "page_type": page_meta.get("page_type") or page_type or "unknown",
        "page_slug": (page_meta.get("page_type") or page_type)[:200],
        "page_url": None,
        "doctrine_version": (
            page_meta.get("doctrine_version") or scores.get("doctrineVersion") or DOCTRINE_VERSION_DEFAULT
        )[:50],
        "scores_json": {
            "aggregate": aggregate,
            "pillars": scores.get("pillars") or {},
            "utility_banner": scores.get("utility_banner"),
            "specific": scores.get("specific"),
            "semantic_overlay": scores.get("semantic_overlay"),
            "applicability_overlay": scores.get("applicability_overlay"),
            "contextual_overlay": scores.get("contextual_overlay"),
            "funnel": scores.get("funnel"),
            "exclusions": scores.get("exclusions"),
            "schwartz_awareness": page_meta.get("schwartz_awareness"),
            "enricher_version": page_meta.get("enricher_version"),
            "business_category": page_meta.get("business_category"),
        },
        "total_score": aggregate.get("rawTotal") or aggregate.get("score100"),
        "total_score_pct": aggregate.get("score100") or aggregate.get("score100_funnel_aware"),
    }


def normalize_recos(audit_uuid: str, recos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for reco in recos:
        priority = (reco.get("priority") or "P3").upper()
        if priority not in {"P0", "P1", "P2", "P3"}:
            priority = "P3"
        effort = _bucket_effort_or_lift(reco.get("effort") or reco.get("feasibility"))
        lift = _bucket_effort_or_lift(reco.get("lift") or reco.get("impact") or reco.get("ice_score"))
        # Title: prefer reco_text first sentence, else criterion_id (avoid generic
        # "(untitled reco)" — RichRecoCard falls back to criterion_id anyway).
        title = (
            reco.get("title")
            or _first_sentence(reco.get("reco_text"))
            or reco.get("criterion_id")
            or reco.get("criterion")
            or "(untitled reco)"
        )
        # content_json = FULL rich payload minus columns we already store
        content = {k: v for k, v in reco.items() if k not in RECO_DEDICATED_COLS}
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


def _first_sentence(text: Any) -> str | None:
    if not isinstance(text, str) or not text.strip():
        return None
    # Stop at first sentence boundary (period + space) or 140 chars max.
    s = text.strip().split(". ", 1)[0]
    return s[:140] if s else None


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


def ensure_org(slug: str, name: str) -> str:
    res = _request("GET", f"organizations?slug=eq.{slug}&select=id&limit=1")
    if res:
        return res[0]["id"]
    owner = _env("ORG_OWNER_ID")
    if not owner:
        raise SupabaseError(
            f"Organization '{slug}' not found and ORG_OWNER_ID not set. "
            "Create the org first via the webapp signup flow."
        )
    res = _request("POST", "organizations", body=[{"slug": slug, "name": name, "owner_id": owner}])
    return res[0]["id"]


def upsert_clients(rows: list[dict[str, Any]], org_id: str) -> dict[str, str]:
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


def lookup_clients_by_slug(org_id: str, slugs: list[str]) -> dict[str, str]:
    if not slugs:
        return {}
    in_clause = ",".join(slugs)
    res = _request(
        "GET",
        f"clients?org_id=eq.{org_id}&slug=in.({in_clause})&select=id,slug",
    )
    return {r["slug"]: r["id"] for r in (res or [])}


def delete_audits_for_clients(client_uuids: list[str]) -> None:
    if not client_uuids:
        return
    ids = ",".join(client_uuids)
    _request("DELETE", f"audits?client_id=in.({ids})")


def upsert_audits(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    res = _request("POST", "audits", body=rows)
    return [r["id"] for r in (res or [])]


def upsert_recos(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    inserted = 0
    batch = 200  # smaller batch — rich content_json can be hefty
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        res = _request("POST", "recos", body=chunk)
        inserted += len(res or [])
    return inserted


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Migrate disk audit truth to Supabase V28.")
    p.add_argument("--only", help="single client slug to migrate (debug)")
    p.add_argument("--audits-only", action="store_true", help="skip clients table upsert")
    p.add_argument("--dry-run", action="store_true", help="force dry-run even with creds set")
    return p.parse_args(argv)


def collect_per_client(slug: str) -> dict[str, Any]:
    """Returns {pages: [{page_type, scores, meta, recos}], brand_dna}."""
    brand_dna = load_brand_dna(slug)
    pages_data: list[dict[str, Any]] = []
    for page in discover_pages(slug):
        recos, meta = load_page_recos(slug, page)
        scores = load_page_scores(slug, page)
        pages_data.append({"page_type": page, "scores": scores, "meta": meta, "recos": recos})
    return {"brand_dna": brand_dna, "pages": pages_data}


def summarize_dry(panel: dict[str, Any], clients_db: dict[str, Any], slugs: list[str]) -> None:
    """Dry-run: print per-client + per-page counts + sample reco field richness."""
    total_pages = 0
    total_recos = 0
    rich_recos = 0  # recos with reco_text non-empty
    sample_done = False
    for slug in slugs:
        data = collect_per_client(slug)
        n_pages = len(data["pages"])
        n_recos = sum(len(p["recos"]) for p in data["pages"])
        n_rich = sum(
            1
            for p in data["pages"]
            for r in p["recos"]
            if (r.get("reco_text") or "").strip()
        )
        total_pages += n_pages
        total_recos += n_recos
        rich_recos += n_rich
        client_row = normalize_client(slug, panel.get(slug, {}), clients_db.get(slug, {}), data["brand_dna"])
        print(
            f"  {slug:30s}  pages={n_pages:2d}  recos={n_recos:3d}  rich={n_rich:3d}"
            f"  brand_dna={'✓' if data['brand_dna'] else '·'}"
            f"  category={client_row.get('business_category') or '?'}"
        )
        if not sample_done and data["pages"]:
            sample_page = data["pages"][0]
            if sample_page["recos"]:
                sample = sample_page["recos"][0]
                fields = sorted(sample.keys())
                print(f"\n  SAMPLE reco fields ({slug}/{sample_page['page_type']}, n={len(fields)}):")
                print(f"    {fields}")
                print(f"    reco_text[:160] = {repr((sample.get('reco_text') or '')[:160])}")
                print(f"    pillar = {sample.get('pillar')}")
                print(f"    anti_patterns_n = {len(sample.get('anti_patterns') or [])}\n")
                sample_done = True
    print(
        f"\n[migrate] TOTALS: {len(slugs)} clients · {total_pages} pages · "
        f"{total_recos} recos ({rich_recos} with reco_text non-empty, "
        f"{(rich_recos * 100 // total_recos) if total_recos else 0}%)"
    )


def main() -> int:
    args = parse_args()
    panel = load_panel()
    clients_db = load_clients_db()
    all_slugs = discover_clients()
    if args.only:
        slugs = [args.only] if args.only in all_slugs else []
        if not slugs:
            print(f"[migrate] client '{args.only}' not found under data/captures/", file=sys.stderr)
            return 2
    else:
        slugs = all_slugs

    if not slugs:
        print("[migrate] no clients to migrate (data/captures/ empty?)", file=sys.stderr)
        return 1

    dry = args.dry_run or _dry_run()
    mode = "DRY-RUN" if dry else "LIVE"
    print(f"[migrate] mode={mode}  clients={len(slugs)}  panel_entries={len(panel)}  db_entries={len(clients_db)}")

    if dry:
        summarize_dry(panel, clients_db, slugs)
        print("\n[migrate] (no writes — set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY to migrate live)")
        return 0

    # LIVE path
    org_slug = _env("ORG_SLUG", "growth-society") or "growth-society"
    org_name = _env("ORG_NAME", "Growth Society") or "Growth Society"
    print(f"[migrate] ensuring org '{org_slug}' ...")
    org_id = ensure_org(org_slug, org_name)
    print(f"[migrate]   org_id = {org_id}")

    # Collect rows
    client_rows: list[dict[str, Any]] = []
    per_client_data: dict[str, dict[str, Any]] = {}
    for slug in slugs:
        data = collect_per_client(slug)
        per_client_data[slug] = data
        client_rows.append(normalize_client(slug, panel.get(slug, {}), clients_db.get(slug, {}), data["brand_dna"]))

    # Upsert clients (or lookup-only)
    if args.audits_only:
        print("[migrate] --audits-only: skipping clients upsert, looking up existing uuids ...")
        slug_to_uuid = lookup_clients_by_slug(org_id, [r["slug"] for r in client_rows])
    else:
        print(f"[migrate] upserting {len(client_rows)} clients ...")
        slug_to_uuid = upsert_clients(client_rows, org_id=org_id)
    print(f"[migrate]   {len(slug_to_uuid)} clients mapped to uuid.")

    # Wipe existing audits for re-run safety
    print("[migrate] deleting existing audits for these clients (re-run safe) ...")
    delete_audits_for_clients(list(slug_to_uuid.values()))

    # Insert audits + recos per client
    total_audits, total_recos = 0, 0
    for slug in slugs:
        client_uuid = slug_to_uuid.get(slug)
        if not client_uuid:
            print(f"[migrate]   skip {slug} (no uuid)")
            continue
        data = per_client_data[slug]
        audit_rows = [
            normalize_audit(client_uuid, p["page_type"], p["meta"], p["scores"])
            for p in data["pages"]
        ]
        if not audit_rows:
            continue
        audit_ids = upsert_audits(audit_rows)
        total_audits += len(audit_ids)
        reco_rows: list[dict[str, Any]] = []
        for audit_uuid, page in zip(audit_ids, data["pages"]):
            reco_rows.extend(normalize_recos(audit_uuid, page["recos"]))
        if reco_rows:
            n = upsert_recos(reco_rows)
            total_recos += n
        time.sleep(0.05)  # rate-limit politesse

    print(f"[migrate] DONE: {len(slug_to_uuid)} clients · {total_audits} audits · {total_recos} recos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
