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

    # ── Behavioral toggles ───────────────────────────────────────────
    def is_aggressive_cmp(self) -> bool:
        return _truthy(os.environ.get("AGGRESSIVE_CMP"))

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
