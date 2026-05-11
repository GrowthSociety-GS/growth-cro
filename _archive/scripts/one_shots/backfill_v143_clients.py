#!/usr/bin/env python3
"""
backfill_v143_clients.py — V14.3.1

Migre data/clients_database.json : ajoute le namespace `v143.*` sur chaque client
en dérivant automatiquement ce qui peut l'être depuis les champs legacy
(identity, strategy, audience, brand, competition, traffic, performance).

Les champs non-dérivables reçoivent des défauts sûrs (none/false/[])
qui seront complétés par enrich_v143_public.py depuis les sources publiques.

Usage:
    python3 scripts/backfill_v143_clients.py                    # tous les clients
    python3 scripts/backfill_v143_clients.py --client japhy     # 1 client
    python3 scripts/backfill_v143_clients.py --dry-run          # preview sans écrire
    python3 scripts/backfill_v143_clients.py --force            # re-backfill même si v143 existe

Idempotent: skip les clients déjà backfillés sauf --force.
Backup: data/clients_database.json.pre-v143-backfill.<ISO>.json
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import shutil
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "clients_database.json"
SCHEMA_PATH = ROOT / "data" / "clients_database_schema_v143.json"

BACKFILL_VERSION = "0.1"

# ---------------------------------------------------------------------------
# Derivation dictionaries
# ---------------------------------------------------------------------------

# Schwartz 5 Stages of Awareness — string → int
AWARENESS_MAP = {
    "unaware": 1, "problem_unaware": 1,
    "problem_aware": 2, "pain_aware": 2,
    "solution_aware": 3,
    "product_aware": 4,
    "most_aware": 5, "brand_aware": 5,
}

# businessType + sector → défaut awareness_stage (si strategy.awarenessLevel absent)
BUSINESS_AWARENESS_DEFAULT = {
    "ecommerce": 2,      # DTC défaut
    "dtc": 2,
    "subscription": 2,
    "saas": 3,           # SaaS B2B default
    "b2b": 3,
    "enterprise": 5,
    "luxury": 4,
    "lead_gen": 2,
    "marketplace": 2,
    "edutech": 3,
    "healthtech": 3,
}

# Archetype macro inference — 5 buckets Mark & Pearson consolidés
# Signals: toneOfVoice + positioning keywords + sector
ARCHETYPE_PATTERNS = {
    "sage_ruler": [
        r"\bexpert\b", r"\bpremium\b", r"\bauthorit", r"\bscientif",
        r"\bprofession", r"\bexcellence\b", r"\bmasterfully\b",
        r"\bleader\b", r"\btrusted\b", r"\bresearch",
    ],
    "hero_outlaw": [
        r"\brebel\b", r"\bdisrupt", r"\bchallenge\b", r"\brevolution",
        r"\bbold\b", r"\bfearless", r"\bconquer", r"\bbreakthrough",
        r"\bunstoppable", r"\bdifferent",
    ],
    "lover_creator": [
        r"\bcraft", r"\bbeauty", r"\bartisan", r"\bpassion",
        r"\bcreative", r"\bexpressive", r"\bsensual", r"\belegant",
        r"\bdesign", r"\binspire",
    ],
    "jester_everyman": [
        r"\bfun\b", r"\bplay", r"\bjoy", r"\bfriend", r"\bsimple",
        r"\beveryone", r"\baccessible", r"\bhappy", r"\bsmile",
        r"\bcasual\b",
    ],
    "caregiver_innocent": [
        r"\bcaring\b", r"\bcare\b", r"\bprotect", r"\bsafe\b",
        r"\bnurtur", r"\bwellness", r"\bhealth", r"\bpur",
        r"\bgentle", r"\bhonest", r"\bauthentic\b", r"\bnatural\b",
    ],
}

# Sector-based archetype boost (when tone inconclusive)
SECTOR_ARCHETYPE_HINT = {
    "pet food": "caregiver_innocent",
    "pet tech": "caregiver_innocent",
    "wellness": "caregiver_innocent",
    "beauty": "lover_creator",
    "skincare": "lover_creator",
    "fashion": "lover_creator",
    "luxury": "sage_ruler",
    "finance": "sage_ruler",
    "insurance": "sage_ruler",
    "enterprise saas": "sage_ruler",
    "fitness": "hero_outlaw",
    "sport": "hero_outlaw",
    "energy drink": "hero_outlaw",
    "gaming": "jester_everyman",
    "entertainment": "jester_everyman",
    "food delivery": "jester_everyman",
    "healthtech": "caregiver_innocent",
    "edutech": "sage_ruler",
}

# Commoditized categories (high-competition, differentiation hard)
COMMODITIZED_PATTERNS = [
    r"accessoir", r"collier", r"harnais", r"coque", r"étui",
    r"t[- ]?shirt", r"mug", r"poster", r"bougie",
    r"complément alimentaire générique", r"gelules\b",
    r"dropship", r"white label",
]

# Voice & Tone 4D inference from toneOfVoice string
# Each tone keyword maps to (formel, expert, serieux, direct) weight vectors
TONE_4D_KEYWORDS = {
    "caring": (30, 40, 60, 40),
    "scientific": (60, 90, 80, 60),
    "innovative": (40, 70, 50, 70),
    "professional": (70, 70, 70, 60),
    "expert": (60, 90, 70, 60),
    "friendly": (20, 40, 30, 50),
    "casual": (10, 30, 20, 40),
    "premium": (80, 70, 80, 50),
    "luxury": (90, 60, 80, 40),
    "playful": (10, 20, 10, 50),
    "fun": (10, 20, 10, 60),
    "bold": (40, 50, 50, 90),
    "direct": (40, 50, 50, 90),
    "authentic": (30, 40, 60, 60),
    "honest": (30, 40, 70, 70),
    "empathique": (20, 30, 50, 40),
    "rigoureux": (70, 80, 80, 60),
    "accessible": (30, 40, 40, 50),
}

# Category maturity heuristic
MATURITY_HINTS = {
    "saturated": [r"\bcroquet", r"\brasoir", r"\bmatelas", r"\bmat[eé]las"],
    "mature": [r"\bsaas\b", r"\becommerce\b", r"\bbeauté\b", r"\bcosmétique\b"],
    "growth": [r"\bpet tech\b", r"\bnocode\b", r"\bai\b", r"\bia\b", r"\bfintech\b"],
    "early": [r"\bquantum\b", r"\bweb3\b", r"\bmetaverse\b"],
}

# ---------------------------------------------------------------------------
# Derivation functions
# ---------------------------------------------------------------------------

def _lower_join(*vals: Any) -> str:
    parts = []
    for v in vals:
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            parts.extend([str(x) for x in v if x])
        else:
            parts.append(str(v))
    return " ".join(parts).lower()


def derive_awareness_stage(client: dict) -> int:
    strategy = client.get("strategy", {}) or {}
    raw = strategy.get("awarenessLevel")
    if raw and isinstance(raw, str) and raw.lower() in AWARENESS_MAP:
        return AWARENESS_MAP[raw.lower()]

    identity = client.get("identity", {}) or {}
    biz = (identity.get("businessType") or "").lower()
    if biz in BUSINESS_AWARENESS_DEFAULT:
        return BUSINESS_AWARENESS_DEFAULT[biz]

    sector = (identity.get("sector") or "").lower()
    if "luxury" in sector or "premium" in sector:
        return 4
    if "enterprise" in sector or "b2b" in sector:
        return 5
    return 2  # DTC-safe default


def derive_archetype_macro(client: dict) -> tuple[str, str]:
    """Returns (archetype, derivation_source)"""
    brand = client.get("brand", {}) or {}
    identity = client.get("identity", {}) or {}

    signal_text = _lower_join(
        brand.get("toneOfVoice"),
        brand.get("positioning"),
        brand.get("valueProposition"),
        identity.get("sector"),
        identity.get("subsector"),
        identity.get("tags"),
    )

    # Score each archetype by regex hit count
    scores = {}
    for arch, patterns in ARCHETYPE_PATTERNS.items():
        hits = sum(1 for p in patterns if re.search(p, signal_text, re.IGNORECASE))
        scores[arch] = hits

    top = max(scores, key=scores.get)
    top_score = scores[top]

    # If tie or low confidence, use sector hint
    if top_score <= 1:
        subsector = (identity.get("subsector") or "").lower()
        sector = (identity.get("sector") or "").lower()
        for hint_key, hint_arch in SECTOR_ARCHETYPE_HINT.items():
            if hint_key in subsector or hint_key in sector:
                return hint_arch, "sector_hint"

    if top_score == 0:
        return "caregiver_innocent", "fallback_default"
    return top, "keyword_scoring"


def derive_voice_tone_4d(client: dict) -> dict:
    brand = client.get("brand", {}) or {}
    tone = (brand.get("toneOfVoice") or "").lower()

    if not tone:
        return {
            "formel": 40, "expert": 40, "serieux": 50, "direct": 50,
            "anchors": [],
            "derivation": "default_neutral",
        }

    matched = []
    acc = [0, 0, 0, 0]
    count = 0
    for kw, vec in TONE_4D_KEYWORDS.items():
        if kw in tone:
            matched.append(kw)
            acc = [a + b for a, b in zip(acc, vec)]
            count += 1

    if count == 0:
        return {
            "formel": 40, "expert": 40, "serieux": 50, "direct": 50,
            "anchors": [],
            "derivation": "no_match_default",
        }

    avg = [round(a / count) for a in acc]
    return {
        "formel": avg[0],
        "expert": avg[1],
        "serieux": avg[2],
        "direct": avg[3],
        "anchors": matched,  # raw tone keywords extracted
        "derivation": f"tone_4d_avg_{count}_matches",
    }


def derive_commoditized_flag(client: dict) -> tuple[bool, str]:
    identity = client.get("identity", {}) or {}
    text = _lower_join(
        identity.get("subsector"),
        identity.get("sector"),
        identity.get("tags"),
        client.get("products", {}).get("main") if client.get("products") else None,
    )
    for pat in COMMODITIZED_PATTERNS:
        if re.search(pat, text):
            return True, f"pattern_match:{pat}"
    # Saturated category = also commoditized
    for pat in MATURITY_HINTS["saturated"]:
        if re.search(pat, text):
            return True, f"saturated_market:{pat}"
    return False, "no_commoditized_signal"


def derive_category_maturity(client: dict) -> str:
    identity = client.get("identity", {}) or {}
    text = _lower_join(
        identity.get("subsector"),
        identity.get("sector"),
        identity.get("tags"),
    )
    for maturity, patterns in MATURITY_HINTS.items():
        for pat in patterns:
            if re.search(pat, text):
                return maturity
    return "mature"  # safe default


def derive_differentiator_claims(client: dict) -> list[dict]:
    claims = []

    # Source 1: brand.valueProposition
    brand = client.get("brand", {}) or {}
    vp = brand.get("valueProposition") or []
    if isinstance(vp, str):
        vp = [vp]
    for v in vp:
        if v:
            claims.append({
                "claim": v.strip(),
                "proof_type": "none",  # to be enriched
                "proof_reference": None,
                "source": "brand.valueProposition",
            })

    # Source 2: competition.differentiators
    comp = client.get("competition", {}) or {}
    diffs = comp.get("differentiators") or []
    if isinstance(diffs, str):
        diffs = [diffs]
    for d in diffs:
        if d and not any(c["claim"].lower() == d.strip().lower() for c in claims):
            claims.append({
                "claim": d.strip(),
                "proof_type": "none",
                "proof_reference": None,
                "source": "competition.differentiators",
            })

    return claims


def derive_dunford_positioning(client: dict) -> dict:
    brand = client.get("brand", {}) or {}
    comp = client.get("competition", {}) or {}
    identity = client.get("identity", {}) or {}

    alternatives = []
    dc = comp.get("directCompetitors") or []
    ic = comp.get("indirectCompetitors") or []
    if isinstance(dc, str):
        dc = [dc]
    if isinstance(ic, str):
        ic = [ic]
    alternatives = [x for x in dc + ic if x]

    return {
        "alternatives": alternatives,
        "unique_attributes": comp.get("differentiators") or [],
        "value_statement": brand.get("positioning") or "",
        "who_for": ", ".join(client.get("audience", {}).get("personas") or []),
        "market_frame": identity.get("sector") or identity.get("subsector") or "",
        "derivation": "legacy_brand_competition_audience",
    }


def derive_ad_copy_source(client: dict) -> dict:
    strategy = client.get("strategy", {}) or {}
    traffic = client.get("traffic", {}) or {}
    channels = (strategy.get("budget", {}) or {}).get("channels") or \
               traffic.get("channels") or {}

    # Detect dominant paid channel
    if isinstance(channels, dict):
        paid_channels = {k: v for k, v in channels.items()
                         if k in ("meta", "google_ads", "tiktok", "facebook", "instagram")}
        if paid_channels:
            # Take first non-zero budget
            for ch, val in paid_channels.items():
                if val:
                    platform = "meta" if "meta" in ch or "facebook" in ch else \
                               "google" if "google" in ch else \
                               "tiktok" if "tiktok" in ch else "none"
                    return {"platform": platform, "sample_ads": []}

    return {"platform": "none", "sample_ads": []}


def derive_competitive_context(client: dict) -> dict:
    commoditized, reason = derive_commoditized_flag(client)
    maturity = derive_category_maturity(client)
    return {
        "commoditized_flag": commoditized,
        "commoditized_derivation": reason,
        "category_maturity": maturity,
    }


def derive_v143_from_client(client: dict) -> dict:
    """Main derivation: build v143 namespace from legacy fields."""
    archetype_macro, arch_source = derive_archetype_macro(client)

    v143 = {
        # --- Auto-derived from legacy fields (high confidence) ---
        "audience_awareness_stage": derive_awareness_stage(client),
        "archetype_macro": archetype_macro,
        "archetype_fine": None,
        "voice_tone_4d": derive_voice_tone_4d(client),
        "differentiator_claims": derive_differentiator_claims(client),
        "dunford_positioning": derive_dunford_positioning(client),
        "ad_copy_source": derive_ad_copy_source(client),
        "competitive_context": derive_competitive_context(client),

        # --- Requires public source enrichment (defaults safe) ---
        "scarcity": {
            "claim_present": False,
            "proof_type": "none",
            "proof_reference": None,
            "suspected_fake": False,
            "_requires_enrichment": True,
        },
        "loss_framing_opt_in": False,  # explicit opt-in only
        "founder": {
            "named": False,
            "name": None,
            "bio": None,
            "photo_url": None,
            "linkedin_url": None,
            "company_age_years": None,
            "company_revenue_m_eur": None,
            "press_mentions": [],
            "_requires_enrichment": True,
        },
        "voc_verbatims": [],  # filled by enrich Module 2
        "unique_mechanism": {
            "name": None,
            "explanation": None,
            "validation_answer": None,
            "reuse_target": 0,
            "_requires_manual_review": True,
        },

        # --- Metadata ---
        "_meta": {
            "backfilled_at": dt.datetime.utcnow().isoformat() + "Z",
            "backfill_version": BACKFILL_VERSION,
            "enriched_at": None,
            "enrichment_sources": [],
            "archetype_derivation_source": arch_source,
            "completeness_pct": 0.0,  # computed below
        },
    }

    # Compute completeness %
    completeness = _compute_completeness(v143)
    v143["_meta"]["completeness_pct"] = completeness

    return v143


def _compute_completeness(v143: dict) -> float:
    """Ratio of fields with non-null/non-default values."""
    checks = [
        bool(v143.get("audience_awareness_stage")),
        v143.get("archetype_macro") not in (None, "caregiver_innocent"),  # default
        bool(v143.get("voice_tone_4d", {}).get("anchors")),
        bool(v143.get("differentiator_claims")),
        bool(v143.get("dunford_positioning", {}).get("value_statement")),
        v143.get("ad_copy_source", {}).get("platform") != "none",
        not v143.get("scarcity", {}).get("_requires_enrichment", True),
        not v143.get("founder", {}).get("_requires_enrichment", True),
        bool(v143.get("voc_verbatims")),
        bool(v143.get("unique_mechanism", {}).get("name")),
        bool(v143.get("competitive_context", {}).get("category_maturity")),
    ]
    return round(100 * sum(1 for x in checks if x) / len(checks), 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def backfill_client(client: dict, force: bool = False) -> tuple[dict, str]:
    """Returns (updated_client, status). Status = 'backfilled', 'skipped', 'force_rebackfilled'."""
    existing = client.get("v143")
    if existing and not force:
        return client, "skipped"

    v143 = derive_v143_from_client(client)
    client["v143"] = v143
    status = "force_rebackfilled" if existing else "backfilled"
    return client, status


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill v143 namespace on clients_database.json")
    parser.add_argument("--client", help="Single client ID (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--force", action="store_true", help="Re-backfill even if v143 present")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[ERROR] {DB_PATH} not found", file=sys.stderr)
        return 1

    # Load DB
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    clients_raw = db.get("clients")

    # Support both list (current) and dict-by-id formats
    if isinstance(clients_raw, list):
        clients_by_id = {c["id"]: c for c in clients_raw if "id" in c}
        db_shape = "list"
    elif isinstance(clients_raw, dict):
        clients_by_id = clients_raw
        db_shape = "dict"
    else:
        print(f"[ERROR] unexpected DB shape: {type(clients_raw)}", file=sys.stderr)
        return 1

    # Target clients
    if args.client:
        if args.client not in clients_by_id:
            print(f"[ERROR] client '{args.client}' not in DB", file=sys.stderr)
            return 1
        targets = [args.client]
    else:
        targets = list(clients_by_id.keys())

    stats = {"backfilled": 0, "skipped": 0, "force_rebackfilled": 0}
    details = []

    for cid in targets:
        client = clients_by_id[cid]
        updated, status = backfill_client(client, force=args.force)
        clients_by_id[cid] = updated
        stats[status] += 1

        v143 = updated.get("v143", {})
        completeness = v143.get("_meta", {}).get("completeness_pct", 0.0)
        archetype = v143.get("archetype_macro", "?")
        aware = v143.get("audience_awareness_stage", "?")
        details.append({
            "client": cid,
            "status": status,
            "archetype": archetype,
            "awareness": aware,
            "completeness_pct": completeness,
        })

        if args.verbose:
            print(f"  {cid:30s} [{status:20s}] archetype={archetype:20s} "
                  f"aware={aware} completeness={completeness:.1f}%")

    # Summary
    print("\n" + "=" * 70)
    print(f"BACKFILL V143 SUMMARY")
    print("=" * 70)
    print(f"Backfilled          : {stats['backfilled']}")
    print(f"Force re-backfilled : {stats['force_rebackfilled']}")
    print(f"Skipped (existing)  : {stats['skipped']}")
    print(f"Total targets       : {len(targets)}")

    if details:
        total_comp = sum(d["completeness_pct"] for d in details) / len(details)
        print(f"Avg completeness    : {total_comp:.1f}%")
        from collections import Counter
        arch_counter = Counter(d["archetype"] for d in details)
        aware_counter = Counter(d["awareness"] for d in details)
        print(f"Archetype distrib   : {dict(arch_counter)}")
        print(f"Awareness distrib   : {dict(sorted(aware_counter.items()))}")

    # Write
    if args.dry_run:
        print("\n[DRY-RUN] No changes written.")
        return 0

    # Backup
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_path = DB_PATH.with_suffix(f".pre-v143-backfill.{ts}.json")
    shutil.copy(DB_PATH, backup_path)
    print(f"\nBackup              : {backup_path.name}")

    # Write new DB — preserve original shape (list or dict)
    if db_shape == "list":
        # Rebuild list in same order, replace updated clients
        db["clients"] = [clients_by_id[c["id"]] for c in clients_raw if "id" in c]
    else:
        db["clients"] = clients_by_id

    if "metadata" not in db:
        db["metadata"] = {}
    db["metadata"]["last_v143_backfill"] = dt.datetime.utcnow().isoformat() + "Z"
    db["metadata"]["v143_backfill_version"] = BACKFILL_VERSION

    DB_PATH.write_text(
        json.dumps(db, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Written             : {DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
