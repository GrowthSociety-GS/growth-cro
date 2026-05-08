# Reality Layer Pilot V26.AI — Kaiju Readiness

> Date : 2026-05-05
> Status : runtime wiring fixed, pilot blocked by missing credentials.
> Scope : `kaiju/home`, no score weighting, no fake data.

## Executive Verdict

Reality Layer was not ready to run even before credentials: the orchestrator resolved the repo root incorrectly from `skills/site-capture/scripts/reality_layer/`, so captured page URLs returned `no_url_found`.

This is fixed. The orchestrator now resolves URLs correctly and can dry-run Kaiju, Weglot and Seazon pages.

The real pilot is blocked for the right reason now: no Reality connector credentials are configured in `.env` for Kaiju, Weglot, Seazon or Japhy.

## What Was Fixed

- `skills/site-capture/scripts/reality_layer/orchestrator.py`
  - repo root fixed from `parents[3]` to `parents[4]`
  - added `--no-write` dry-run mode
  - added `--write-empty` diagnostic override
  - default write now skips empty outputs when no connector is active

- `skills/site-capture/scripts/build_growth_audit_data.py`
  - Reality is counted as active only when at least one connector returned data
  - error-only or credential-missing files do not make the webapp claim Reality is active
  - attempted pages are tracked separately as `n_pages_with_reality_attempted`

## Dry-Run Command

```bash
PYTHONPATH=skills/site-capture/scripts \
python3 -m reality_layer.orchestrator \
  --client kaiju \
  --page home \
  --days 30 \
  --no-write
```

Observed result:

```text
0/1 pages with at least 1 connector active
home URL resolved: https://www.kaiju.eu/
catchr: not_configured
meta_ads: not_configured
google_ads: not_configured
shopify: not_configured
clarity: not_configured
```

## Real Pilot Command

After credentials are configured:

```bash
PYTHONPATH=skills/site-capture/scripts \
python3 -m reality_layer.orchestrator \
  --client kaiju \
  --page home \
  --days 30
```

Expected output:

```text
data/captures/kaiju/home/reality_layer.json
```

Then rebuild webapp:

```bash
python3 skills/site-capture/scripts/build_growth_audit_data.py
node --check deliverables/growth_audit_data.js
```

## Required Env Vars For Kaiju

Minimum viable pilot is one connector, preferably Catchr or Shopify.

```text
CATCHR_API_KEY_KAIJU
CATCHR_PROPERTY_ID_KAIJU

META_ACCESS_TOKEN_KAIJU
META_AD_ACCOUNT_ID_KAIJU

GOOGLE_ADS_DEVELOPER_TOKEN_KAIJU
GOOGLE_ADS_CLIENT_ID_KAIJU
GOOGLE_ADS_CLIENT_SECRET_KAIJU
GOOGLE_ADS_REFRESH_TOKEN_KAIJU
GOOGLE_ADS_CUSTOMER_ID_KAIJU

SHOPIFY_STORE_DOMAIN_KAIJU
SHOPIFY_ADMIN_API_TOKEN_KAIJU

CLARITY_API_TOKEN_KAIJU
CLARITY_PROJECT_ID_KAIJU
```

## Product Rule

Do not write a `reality_layer.json` just to turn the webapp green.

Reality becomes active only when at least one real connector returns data. Until then, the correct status is `inactive`, with a working dry-run and exact credential checklist.

