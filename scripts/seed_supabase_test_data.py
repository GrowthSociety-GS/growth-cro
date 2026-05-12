#!/usr/bin/env python3
"""Seed Supabase with realistic test data (3 clients + audits + recos + runs).

Idempotent via on_conflict upserts. Targets the Growth Society org.
Usage : SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/seed_supabase_test_data.py

Doctrine : env reads via growthcro.config (mono-concern, no business logic).
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Config (env reads — single source via growthcro.config in real code, inline here
# because this is a standalone bootstrap script run during setup, not a pipeline)
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xyazvwwjckhdmxnohadc.supabase.co")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
ORG_ID = os.environ.get("GROWTHCRO_ORG_ID", "571e55b2-b499-4126-831a-86a1ffa8a03a")  # Growth Society org

if not SERVICE_ROLE_KEY:
    print("❌ SUPABASE_SERVICE_ROLE_KEY env var required (admin-level, never commit)")
    sys.exit(1)

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=representation",
}


def upsert(table: str, rows: list[dict[str, Any]], on_conflict: str) -> list[dict[str, Any]]:
    """Upsert rows via REST. Returns inserted/updated rows."""
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}"
    resp = requests.post(url, headers=HEADERS, json=rows, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"❌ {table} upsert failed [{resp.status_code}]: {resp.text}")
        sys.exit(1)
    return resp.json() if resp.text else []


# ---------------------------------------------------------------------------
# Fixture data — 3 realistic clients with audits + recos
# ---------------------------------------------------------------------------
CLIENTS = [
    {
        "slug": "acme-saas",
        "name": "Acme SaaS",
        "business_category": "saas_b2b",
        "homepage_url": "https://acme-saas.example.com",
        "panel_role": "demo",
        "panel_status": "active",
        "brand_dna_json": {"tone": "professional", "primary_color": "#0066ff", "industry": "B2B SaaS"},
    },
    {
        "slug": "japhy-petfood",
        "name": "Japhy",
        "business_category": "ecommerce_dtc",
        "homepage_url": "https://japhy.fr",
        "panel_role": "demo",
        "panel_status": "active",
        "brand_dna_json": {"tone": "friendly", "primary_color": "#ff6b00", "industry": "Pet food DTC"},
    },
    {
        "slug": "doctolib-health",
        "name": "Doctolib",
        "business_category": "healthtech",
        "homepage_url": "https://doctolib.fr",
        "panel_role": "demo",
        "panel_status": "active",
        "brand_dna_json": {"tone": "trustworthy", "primary_color": "#107ACA", "industry": "Healthtech booking"},
    },
]

AUDITS_PER_CLIENT = [
    {
        "page_type": "home",
        "page_slug": "home",
        "page_url_suffix": "/",
        "scores_json": {
            "hero": 14,
            "persuasion": 26,
            "ux": 19,
            "coherence": 22,
            "psycho": 18,
            "tech": 12,
        },
        "total_score": 111.0,
        "total_score_pct": 75.5,
    },
    {
        "page_type": "pricing",
        "page_slug": "pricing",
        "page_url_suffix": "/pricing",
        "scores_json": {
            "hero": 11,
            "persuasion": 22,
            "ux": 17,
            "coherence": 20,
            "psycho": 15,
            "tech": 13,
        },
        "total_score": 98.0,
        "total_score_pct": 66.7,
    },
]

RECOS_TEMPLATES = [
    {
        "criterion_id": "hero_03",
        "priority": "P0",
        "effort": "M",
        "lift": "L",
        "title": "Ajouter un sous-titre concret sous le hero (test 5s + ratio 1:1)",
        "content_json": {
            "summary": "Le hero actuel n'explique pas la value prop en 5 secondes. Cible : un sous-titre 1 phrase + ratio texte/visuel 1:1.",
            "evidence_ids": ["hero_capture_001", "perception_cluster_hero"],
            "expected_lift_pct": 8.5,
        },
    },
    {
        "criterion_id": "per_03",
        "priority": "P0",
        "effort": "S",
        "lift": "M",
        "title": "CTA primaire non-générique : remplacer 'En savoir plus' par action verbale",
        "content_json": {
            "summary": "Le CTA principal utilise 'En savoir plus' (générique). Remplacer par 'Démarrer mon essai gratuit' OU 'Voir le tarif Pro'.",
            "evidence_ids": ["scoring_per_03_fail"],
            "expected_lift_pct": 5.2,
        },
    },
    {
        "criterion_id": "ux_05",
        "priority": "P1",
        "effort": "S",
        "lift": "M",
        "title": "Réduire le nombre de champs du form lead (actuellement 7, cible ≤4)",
        "content_json": {
            "summary": "Le form de capture lead a 7 champs. Best practice ≤4 pour B2B SaaS. Supprimer 'Téléphone' + 'Taille entreprise' (peut être post-signup).",
            "evidence_ids": ["form_analysis_002"],
            "expected_lift_pct": 12.0,
        },
    },
    {
        "criterion_id": "coh_03",
        "priority": "P1",
        "effort": "M",
        "lift": "M",
        "title": "Scent matching : message ads paid ne correspond pas au H1 landing",
        "content_json": {
            "summary": "Vos ads Meta promettent 'Audit gratuit en 60s' mais le H1 dit 'Solution CRO complète'. Aligner pour réduire bounce rate -25%.",
            "evidence_ids": ["scent_analysis_003", "ads_creative_audit"],
            "expected_lift_pct": 25.0,
        },
    },
    {
        "criterion_id": "psy_05",
        "priority": "P2",
        "effort": "S",
        "lift": "S",
        "title": "Ajouter social proof concret (logos clients OU testimonials chiffrés)",
        "content_json": {
            "summary": "Aucun social proof visible above-the-fold. Ajouter 3-5 logos clients reconnaissables OU 1 testimonial avec metric chiffrée.",
            "evidence_ids": ["psycho_audit_004"],
            "expected_lift_pct": 4.8,
        },
    },
]


def main() -> int:
    print(f"=== Seed Supabase test data ===")
    print(f"  URL: {SUPABASE_URL}")
    print(f"  Org: {ORG_ID}")
    print()

    # 1. Upsert clients (3)
    client_rows = [{**c, "org_id": ORG_ID} for c in CLIENTS]
    inserted_clients = upsert("clients", client_rows, on_conflict="org_id,slug")
    print(f"✓ {len(inserted_clients)} clients upserted")
    for c in inserted_clients:
        print(f"  • {c['name']} ({c['slug']}) → id={c['id']}")
    print()

    # 2. Audits (2 per client = 6 total)
    audit_rows = []
    for c in inserted_clients:
        for a in AUDITS_PER_CLIENT:
            audit_rows.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{c['slug']}-{a['page_slug']}")),
                "client_id": c["id"],
                "page_type": a["page_type"],
                "page_slug": a["page_slug"],
                "page_url": (c["homepage_url"] or "") + a["page_url_suffix"],
                "doctrine_version": "v3.2.1",
                "scores_json": a["scores_json"],
                "total_score": a["total_score"],
                "total_score_pct": a["total_score_pct"],
            })
    # NOTE: audits has no natural unique key beyond UUID — we use deterministic uuid5
    # to make the seed idempotent. Upsert on id.
    inserted_audits = upsert("audits", audit_rows, on_conflict="id")
    print(f"✓ {len(inserted_audits)} audits upserted (2 per client)")
    print()

    # 3. Recos (5 per audit = 30 total)
    reco_rows = []
    for audit in inserted_audits:
        for r_template in RECOS_TEMPLATES:
            reco_rows.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{audit['id']}-{r_template['criterion_id']}")),
                "audit_id": audit["id"],
                **r_template,
            })
    inserted_recos = upsert("recos", reco_rows, on_conflict="id")
    print(f"✓ {len(inserted_recos)} recos upserted (5 per audit)")
    print()

    # 4. Runs (1 completed audit run per client + 1 pending GSG run)
    run_rows = []
    for c in inserted_clients:
        # Completed audit run
        run_rows.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{c['slug']}-audit-run-001")),
            "org_id": ORG_ID,
            "client_id": c["id"],
            "type": "audit",
            "status": "completed",
            "started_at": "2026-05-10T09:00:00Z",
            "finished_at": "2026-05-10T09:03:42Z",
            "output_path": f"deliverables/audits/{c['slug']}/run_001/",
            "metadata_json": {
                "pages_audited": 2,
                "recos_generated": 10,
                "doctrine_version": "v3.2.1",
                "playwright_runtime_sec": 222,
                "anthropic_tokens": 18420,
            },
        })
        # Pending GSG run (for realtime feed demo)
        if c["slug"] == "japhy-petfood":
            run_rows.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{c['slug']}-gsg-run-001")),
                "org_id": ORG_ID,
                "client_id": c["id"],
                "type": "gsg",
                "status": "running",
                "started_at": "2026-05-12T16:50:00Z",
                "finished_at": None,
                "output_path": None,
                "metadata_json": {"page_type": "lp_listicle", "stage": "rendering"},
            })
    inserted_runs = upsert("runs", run_rows, on_conflict="id")
    print(f"✓ {len(inserted_runs)} runs upserted")
    print()

    print("═" * 60)
    print(f" SEED COMPLETE")
    print(f"  • {len(inserted_clients)} clients")
    print(f"  • {len(inserted_audits)} audits")
    print(f"  • {len(inserted_recos)} recos")
    print(f"  • {len(inserted_runs)} runs (1 pending GSG visible in live feed)")
    print(f" Dashboard URL : https://growth-cro.vercel.app")
    print("═" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
