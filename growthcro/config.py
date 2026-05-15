"""Single environment-variable boundary for GrowthCRO.

Every active code path reads env through this module. The cleanup epic's
mechanical gate is that `os.environ` and `os.getenv` appear in exactly one
file (this one). The acceptance grep is in the epic spec.

Public API
----------
    from growthcro.config import config

    # Optional accessors return None if unset.
    key = config.anthropic_api_key()         # Optional[str]
    if key:
        ...

    # Required accessors raise MissingConfigError if unset.
    key = config.require_anthropic_api_key()  # str

    # Booleans:
    if config.is_aggressive_cmp(): ...

    # Server / typed:
    port = config.port()                      # int, default 8000

    # System passthroughs (PATH, SHELL, etc.) — not part of the .env contract:
    path = config.system_env("PATH")
    env  = config.system_env_copy()           # dict, for subprocess

    # Startup validation (raises if any var in `require` is unset):
    config.validate(require=("ANTHROPIC_API_KEY",))

Design notes
------------
- Importing this module is side-effect free, except for loading `.env`
  via the embedded micro-loader (no `python-dotenv` dependency added).
- Validation happens when an accessor is called, not at import. A required
  accessor raises only at first call.
- The accessor functions are the *only* names this module exports for env
  access. Adding a new env var = adding an accessor here, plus regenerating
  `.env.example` from the schema in `_KNOWN_VARS`.
"""
from __future__ import annotations

import os
import pathlib
from functools import lru_cache
from typing import Optional


# ─────────────────────────────────────────────────────────────────────
# .env micro-loader (no new dependency)
# ─────────────────────────────────────────────────────────────────────
def _load_dotenv_once() -> None:
    """Load .env from repo root if present. Existing os.environ wins."""
    root = pathlib.Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    if not env_file.is_file():
        return
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


_load_dotenv_once()


# ─────────────────────────────────────────────────────────────────────
# Schema — known vars, used to regenerate .env.example
# ─────────────────────────────────────────────────────────────────────
# (var_name, required, default_or_hint, comment)
_KNOWN_VARS: tuple[tuple[str, bool, str, str], ...] = (
    ("ANTHROPIC_API_KEY",            True,  "",        "Claude API (Haiku scorer + Sonnet enricher). Required."),
    ("APIFY_TOKEN",                  False, "",        "Apify cloud capture. Required only when running the cloud capture path."),
    ("OPENAI_API_KEY",               False, "",        "Optional — used by some multi-judge judges."),
    ("PERPLEXITY_API_KEY",           False, "",        "Optional — GEO module."),
    ("GROWTHCRO_CRUX_KEY",           False, "",        "Optional — Chrome UX Report (web vitals)."),
    ("GROWTHCRO_PSI_KEY",            False, "",        "Optional — PageSpeed Insights (web vitals)."),
    ("GROWTHCRO_WEB_VITALS_PROVIDER", False, "none",   "'crux' | 'psi' | 'none'. Default 'none'."),
    ("BROWSER_WS_ENDPOINT",          False, "",        "Optional — remote browser websocket (Apify/Browserless)."),
    ("BRIGHTDATA_WSS",               False, "",        "Optional — BrightData browser proxy WSS."),
    ("BRIGHTDATA_AUTH",              False, "",        "Optional — BrightData auth token."),
    ("GHOST_HEADED",                 False, "0",       "'1' to run ghost_capture in headed mode for debugging."),
    ("AGGRESSIVE_CMP",               False, "0",       "'1' to enable aggressive CMP (cookie banner) handling."),
    ("PORT",                         False, "8000",    "FastAPI server port."),
    ("GROWTHCRO_LOG_LEVEL",          False, "INFO",    "Observability log level (DEBUG|INFO|WARNING|ERROR). Default INFO. See growthcro/observability/logger.py."),
    # ── Reality Layer V26.C — per-client credentials (Issue #23) ──────────────
    # Per-client convention: append `_<CLIENT_SLUG_UPPERCASE>` (e.g. `META_ACCESS_TOKEN_WEGLOT`).
    # The bare var name (no suffix) is a global fallback used by tooling tests only.
    # Reality Layer connectors look up `<VAR>_<SLUG_UPPER>` then fall back to `<VAR>`.
    # See `growthcro/reality/credentials.py` for inspector/validator.
    ("CATCHR_API_KEY",               False, "",        "Reality Layer — Catchr API key (GA4 wrapper used internally). Per-client: CATCHR_API_KEY_<SLUG>."),
    ("CATCHR_PROPERTY_ID",           False, "",        "Reality Layer — Catchr property ID. Per-client: CATCHR_PROPERTY_ID_<SLUG>."),
    ("GA4_SERVICE_ACCOUNT_JSON",     False, "",        "Reality Layer — Path to GA4 service account JSON. Per-client: GA4_SERVICE_ACCOUNT_JSON_<SLUG>."),
    ("GA4_PROPERTY_ID",              False, "",        "Reality Layer — GA4 numeric property ID. Per-client: GA4_PROPERTY_ID_<SLUG>."),
    ("META_ACCESS_TOKEN",            False, "",        "Reality Layer — Meta Marketing API access token. Per-client: META_ACCESS_TOKEN_<SLUG>."),
    ("META_AD_ACCOUNT_ID",           False, "",        "Reality Layer — Meta ad account ID (act_…). Per-client: META_AD_ACCOUNT_ID_<SLUG>."),
    ("GOOGLE_ADS_DEVELOPER_TOKEN",   False, "",        "Reality Layer — Google Ads developer token. Per-client: GOOGLE_ADS_DEVELOPER_TOKEN_<SLUG> (rare; usually global)."),
    ("GOOGLE_ADS_CLIENT_ID",         False, "",        "Reality Layer — Google Ads OAuth client ID. Per-client: GOOGLE_ADS_CLIENT_ID_<SLUG>."),
    ("GOOGLE_ADS_CLIENT_SECRET",     False, "",        "Reality Layer — Google Ads OAuth client secret. Per-client: GOOGLE_ADS_CLIENT_SECRET_<SLUG>."),
    ("GOOGLE_ADS_REFRESH_TOKEN",     False, "",        "Reality Layer — Google Ads OAuth refresh token. Per-client: GOOGLE_ADS_REFRESH_TOKEN_<SLUG>."),
    ("GOOGLE_ADS_CUSTOMER_ID",       False, "",        "Reality Layer — Google Ads customer ID (10-digit, no dashes). Per-client: GOOGLE_ADS_CUSTOMER_ID_<SLUG>."),
    ("SHOPIFY_STORE_DOMAIN",         False, "",        "Reality Layer — Shopify store domain (e.g. shop.myshopify.com). Per-client: SHOPIFY_STORE_DOMAIN_<SLUG>."),
    ("SHOPIFY_ADMIN_API_TOKEN",      False, "",        "Reality Layer — Shopify Admin API access token. Per-client: SHOPIFY_ADMIN_API_TOKEN_<SLUG>."),
    ("CLARITY_API_TOKEN",            False, "",        "Reality Layer — Microsoft Clarity Data Export token. Per-client: CLARITY_API_TOKEN_<SLUG>."),
    ("CLARITY_PROJECT_ID",           False, "",        "Reality Layer — Microsoft Clarity project ID. Per-client: CLARITY_PROJECT_ID_<SLUG>."),
    # ── Reality Layer V30 — OAuth (Task 011) ──────────────────────────────────
    # Defensive : when an OAuth app isn't provisioned, the webapp callback
    # returns 503 `connector_not_configured` and the Python poller returns
    # `SnapshotResult(skipped=True, reason='not_connected')`. Code ships now,
    # activates when Mathis provisions each OAuth app on the connector side.
    ("REALITY_TOKEN_ENCRYPTION_KEY", False, "",        "Reality Layer V30 — AES key (any string) used as pgcrypto session GUC `app.reality_token_key`. When missing, the encrypt() returns the sentinel '__no_key__' and the API surfaces an error."),
    ("REALITY_OAUTH_STATE_SECRET",   False, "",        "Reality Layer V30 — HMAC-SHA256 secret used to sign OAuth state. Mismatch → callback redirects with ?error=invalid_state."),
    ("CRON_SECRET",                  False, "",        "Vercel Cron — Bearer token validated by /api/cron/reality-poll. Vercel auto-injects this for Cron Jobs. Manual triggers must include `Authorization: Bearer <CRON_SECRET>`."),
    ("CATCHR_CLIENT_ID",             False, "",        "Reality Layer V30 — Catchr OAuth client_id. Provision at catchr.io/oauth."),
    ("CATCHR_CLIENT_SECRET",         False, "",        "Reality Layer V30 — Catchr OAuth client_secret."),
    ("META_ADS_CLIENT_ID",           False, "",        "Reality Layer V30 — Meta Ads OAuth client_id (Facebook App ID)."),
    ("META_ADS_CLIENT_SECRET",       False, "",        "Reality Layer V30 — Meta Ads OAuth app secret."),
    ("GOOGLE_ADS_OAUTH_CLIENT_ID",   False, "",        "Reality Layer V30 — Google Ads OAuth client_id (Cloud Console)."),
    ("GOOGLE_ADS_OAUTH_CLIENT_SECRET", False, "",      "Reality Layer V30 — Google Ads OAuth client_secret."),
    ("SHOPIFY_CLIENT_ID",            False, "",        "Reality Layer V30 — Shopify Partners app client_id."),
    ("SHOPIFY_CLIENT_SECRET",        False, "",        "Reality Layer V30 — Shopify Partners app client_secret."),
    ("CLARITY_CLIENT_ID",            False, "",        "Reality Layer V30 — Microsoft Clarity OAuth client_id (private beta — Clarity OAuth not GA)."),
    ("CLARITY_CLIENT_SECRET",        False, "",        "Reality Layer V30 — Microsoft Clarity OAuth client_secret."),
    ("NEXT_PUBLIC_APP_URL",          False, "",        "Reality Layer V30 — Public origin (https://growth-cro.vercel.app) used as OAuth redirect_uri prefix. When unset, fallback http://localhost:3000."),
)


class MissingConfigError(RuntimeError):
    """Raised when a required env var is unset at the moment it's needed."""

    def __init__(self, var: str, hint: str = ""):
        msg = f"Missing required env var: {var}"
        if hint:
            msg += f"  → {hint}"
        super().__init__(msg)
        self.var = var
        self.hint = hint


def _truthy(v: Optional[str]) -> bool:
    return (v or "").strip().lower() in ("1", "true", "yes", "on")


# ─────────────────────────────────────────────────────────────────────
# Config singleton
# ─────────────────────────────────────────────────────────────────────
class _Config:
    # ── API keys ─────────────────────────────────────────────────────
    def anthropic_api_key(self) -> Optional[str]:
        return os.environ.get("ANTHROPIC_API_KEY") or None

    def require_anthropic_api_key(self) -> str:
        v = self.anthropic_api_key()
        if not v:
            raise MissingConfigError(
                "ANTHROPIC_API_KEY",
                "Set this in .env (see .env.example) or export it before running.",
            )
        return v

    def apify_token(self) -> Optional[str]:
        return os.environ.get("APIFY_TOKEN") or None

    def require_apify_token(self) -> str:
        v = self.apify_token()
        if not v:
            raise MissingConfigError(
                "APIFY_TOKEN",
                "Cloud capture requires an Apify token. Get one at apify.com.",
            )
        return v

    def openai_api_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY") or None

    def perplexity_api_key(self) -> Optional[str]:
        return os.environ.get("PERPLEXITY_API_KEY") or None

    def crux_key(self) -> Optional[str]:
        return os.environ.get("GROWTHCRO_CRUX_KEY") or None

    def psi_key(self) -> Optional[str]:
        return os.environ.get("GROWTHCRO_PSI_KEY") or None

    def brightdata_auth(self) -> Optional[str]:
        return os.environ.get("BRIGHTDATA_AUTH") or None

    def brightdata_wss(self) -> Optional[str]:
        return os.environ.get("BRIGHTDATA_WSS") or None

    # ── Browser / runtime ────────────────────────────────────────────
    def browser_ws_endpoint(self) -> Optional[str]:
        return os.environ.get("BROWSER_WS_ENDPOINT") or None

    def is_ghost_headed(self) -> bool:
        return _truthy(os.environ.get("GHOST_HEADED"))

    # ── Server ───────────────────────────────────────────────────────
    def port(self, default: int = 8000) -> int:
        v = os.environ.get("PORT")
        try:
            return int(v) if v else default
        except ValueError:
            return default

    def web_vitals_provider(self, default: str = "none") -> str:
        return os.environ.get("GROWTHCRO_WEB_VITALS_PROVIDER", default)

    # ── Observability ────────────────────────────────────────────────
    def log_level(self, default: str = "INFO") -> str:
        """Observability log level read from `GROWTHCRO_LOG_LEVEL`.

        Returns the env value (uppercased) or `default` if unset. Consumed by
        `growthcro/observability/logger.py` at root-logger setup.
        """
        v = os.environ.get("GROWTHCRO_LOG_LEVEL")
        return (v or default).strip().upper()

    # ── Behavioral toggles ───────────────────────────────────────────
    def is_aggressive_cmp(self) -> bool:
        return _truthy(os.environ.get("AGGRESSIVE_CMP"))

    # ── Reality Layer V30 — OAuth + cron ─────────────────────────────
    def reality_token_encryption_key(self) -> Optional[str]:
        """AES key for pgcrypto encryption of OAuth tokens (Task 011)."""
        return os.environ.get("REALITY_TOKEN_ENCRYPTION_KEY") or None

    def reality_oauth_state_secret(self) -> Optional[str]:
        """HMAC-SHA256 secret for OAuth state validation (Task 011)."""
        return os.environ.get("REALITY_OAUTH_STATE_SECRET") or None

    def reality_oauth_client(self, connector: str) -> tuple[Optional[str], Optional[str]]:
        """Return (client_id, client_secret) for one of the 5 V30 OAuth apps.

        Connector keys : 'catchr' | 'meta_ads' | 'google_ads' | 'shopify' | 'clarity'.
        Defensive : returns (None, None) when the OAuth app is not provisioned.
        """
        prefix_map = {
            "catchr": "CATCHR",
            "meta_ads": "META_ADS",
            "google_ads": "GOOGLE_ADS_OAUTH",
            "shopify": "SHOPIFY",
            "clarity": "CLARITY",
        }
        prefix = prefix_map.get(connector)
        if not prefix:
            return (None, None)
        cid = os.environ.get(f"{prefix}_CLIENT_ID") or None
        secret = os.environ.get(f"{prefix}_CLIENT_SECRET") or None
        return (cid, secret)

    def cron_secret(self) -> Optional[str]:
        """Vercel Cron Bearer token (Task 011)."""
        return os.environ.get("CRON_SECRET") or None

    def app_public_url(self, default: str = "http://localhost:3000") -> str:
        """Public origin for OAuth redirect_uri (Task 011)."""
        return os.environ.get("NEXT_PUBLIC_APP_URL") or default

    # ── Reality Layer per-client lookup ──────────────────────────────
    def reality_client_env(self, var: str, client_slug: str) -> Optional[str]:
        """Resolve a Reality Layer credential for a given client slug.

        Lookup order:
          1. `<VAR>_<CLIENT_SLUG_UPPERCASE>` (per-client, takes precedence)
          2. `<VAR>` (global fallback)

        Returns None if neither is set. Never logs / never raises on missing.

        Used by `growthcro.reality.*` connectors (Issue #23). Centralises the
        lookup so connectors don't reimplement the convention.
        """
        # Normalise the slug: uppercase, hyphens → underscores, no leading digits.
        safe_slug = client_slug.upper().replace("-", "_")
        per_client = os.environ.get(f"{var}_{safe_slug}")
        if per_client:
            return per_client
        return os.environ.get(var) or None

    # ── System passthroughs (NOT part of the .env contract) ──────────
    def system_env(self, name: str, default: str = "") -> str:
        return os.environ.get(name, default)

    def system_env_copy(self) -> dict[str, str]:
        return os.environ.copy()

    def override_env(self, name: str, value: str) -> None:
        """CLI/runtime override. Use only when an arg-parsed value must
        propagate to subprocess env or to downstream config reads in the
        same process. Avoid for normal config — set values in .env."""
        os.environ[name] = value

    # ── Validation ───────────────────────────────────────────────────
    def validate(self, *, require: tuple[str, ...] = ()) -> None:
        for var in require:
            if not os.environ.get(var):
                hint = next(
                    (h for v, _r, _d, h in _KNOWN_VARS if v == var),
                    "",
                )
                raise MissingConfigError(var, hint)


@lru_cache(maxsize=1)
def get_config() -> _Config:
    return _Config()


config = get_config()


# ─────────────────────────────────────────────────────────────────────
# .env.example regeneration
# ─────────────────────────────────────────────────────────────────────
def render_env_example() -> str:
    lines = [
        "# GrowthCRO — environment variables",
        "# Auto-generated from growthcro/config.py::_KNOWN_VARS",
        "# Copy to `.env` and fill in your secrets. .env is gitignored.",
        "",
    ]
    required = [v for v in _KNOWN_VARS if v[1]]
    optional = [v for v in _KNOWN_VARS if not v[1]]
    if required:
        lines.append("# ── Required ─────────────────────────────────────────")
        for name, _r, default, comment in required:
            lines.append(f"# {comment}")
            lines.append(f"{name}={default}")
            lines.append("")
    if optional:
        lines.append("# ── Optional ─────────────────────────────────────────")
        for name, _r, default, comment in optional:
            lines.append(f"# {comment}")
            lines.append(f"{name}={default}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    # `python3 -m growthcro.config` regenerates .env.example.
    out = pathlib.Path(__file__).resolve().parent.parent / ".env.example"
    out.write_text(render_env_example(), encoding="utf-8")
    print(f"✓ wrote {out}")
