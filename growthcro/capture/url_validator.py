"""SSRF-safe URL validator for the Playwright crawler.

Mono-concern (axis: ``validation``). Pure gate called before ``page.goto``
in :mod:`growthcro.capture.orchestrator` and at argparse time in
:mod:`growthcro.capture.cli`. Stdlib + Pydantic v2 only; no env, no logging.

Rules (any failure rejects): scheme ∈ {http, https}; hostname ∉
BLOCKED_HOSTNAMES; port ∈ ALLOWED_PORTS; every resolved IP outside
PRIVATE_NETWORKS (DNS rebinding defense). See AUDIT_DECISION_DOSSIER
§6 P0.7 / §10.1 #1 + CODE_DOCTRINE axis 5.
"""
from __future__ import annotations

import socket
from ipaddress import ip_address, ip_network
from typing import Final
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict

# ─────────────────────────────────────────────────────────────────────────────
# Policy constants — adjust here, not at call sites.
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_SCHEMES: Final[frozenset[str]] = frozenset({"http", "https"})

BLOCKED_HOSTNAMES: Final[frozenset[str]] = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
        "metadata",
        "metadata.google.internal",
        "metadata.aws.internal",
        "metadata.tencentyun.com",
    }
)

PRIVATE_NETWORKS: Final[tuple[str, ...]] = (
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "0.0.0.0/8",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
)

# Ports < 80 are blocked outright (avoids SSH/22, SMTP/25, RDP/3389, etc.).
# 80, 443, 8080, 8443 are the only common HTTP/S surfaces we crawl.
ALLOWED_PORTS: Final[frozenset[int]] = frozenset({80, 443, 8080, 8443})

_PRIVATE_NETS = tuple(ip_network(cidr) for cidr in PRIVATE_NETWORKS)


# ─────────────────────────────────────────────────────────────────────────────
# Public types
# ─────────────────────────────────────────────────────────────────────────────
class URLValidationError(ValueError):
    """Raised when a URL fails the SSRF gate.

    Attributes
    ----------
    reason: short machine-readable token (``"blocked_scheme"``, …).
    url:    the offending input (verbatim, for log/error display).
    """

    def __init__(self, reason: str, url: str) -> None:
        self.reason = reason
        self.url = url
        super().__init__(f"URL rejected ({reason}): {url}")


class URLValidationResult(BaseModel):
    """Typed outcome of :func:`validate_url`. Always returned on success."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    url: str
    scheme: str
    hostname: str
    port: int
    resolved_ips: tuple[str, ...]


# ─────────────────────────────────────────────────────────────────────────────
# Core API
# ─────────────────────────────────────────────────────────────────────────────
def validate_url(url: str) -> URLValidationResult:
    """Validate a user-supplied URL against the SSRF policy.

    Returns
    -------
    URLValidationResult
        Frozen Pydantic model with resolved metadata.

    Raises
    ------
    URLValidationError
        On any policy violation. ``.reason`` carries a stable token
        (``blocked_scheme`` / ``missing_hostname`` / ``blocked_hostname`` /
        ``blocked_port`` / ``dns_failure`` / ``blocked_private_ip``).
    """
    if not isinstance(url, str) or not url.strip():
        raise URLValidationError("empty_url", str(url))

    parsed = urlparse(url.strip())

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise URLValidationError("blocked_scheme", url)

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise URLValidationError("missing_hostname", url)

    if hostname in BLOCKED_HOSTNAMES:
        raise URLValidationError("blocked_hostname", url)

    # Port: explicit when present, otherwise scheme default.
    try:
        port = parsed.port if parsed.port is not None else (443 if scheme == "https" else 80)
    except ValueError as exc:  # malformed port string
        raise URLValidationError("blocked_port", url) from exc
    if port not in ALLOWED_PORTS:
        raise URLValidationError("blocked_port", url)

    # If hostname is already a literal IP, validate it directly.
    resolved_ips: list[str] = []
    literal_ip = _try_literal_ip(hostname)
    if literal_ip is not None:
        if _is_private(literal_ip):
            raise URLValidationError("blocked_private_ip", url)
        resolved_ips.append(literal_ip)
    else:
        # DNS rebinding defense: resolve and check EVERY answer.
        try:
            infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise URLValidationError("dns_failure", url) from exc
        for info in infos:
            sockaddr = info[4]
            ip_str = sockaddr[0]
            # Strip IPv6 zone-id (e.g. "fe80::1%en0") so ip_address parses.
            ip_clean = ip_str.split("%", 1)[0]
            if _is_private(ip_clean):
                raise URLValidationError("blocked_private_ip", url)
            if ip_clean not in resolved_ips:
                resolved_ips.append(ip_clean)

    return URLValidationResult(
        url=url,
        scheme=scheme,
        hostname=hostname,
        port=port,
        resolved_ips=tuple(resolved_ips),
    )


# ─────────────────────────────────────────────────────────────────────────────
# argparse adapter — keeps CLI feedback fast & user-friendly.
# ─────────────────────────────────────────────────────────────────────────────
def argparse_url_type(value: str) -> str:
    """Type validator for ``argparse.add_argument(..., type=...)``.

    Returns the URL unchanged on success so the CLI keeps its existing
    string-typed contract; raises :class:`argparse.ArgumentTypeError` with
    a human-readable reason on failure.
    """
    import argparse  # local: avoid argparse cost on hot capture path

    try:
        validate_url(value)
    except URLValidationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


# ─────────────────────────────────────────────────────────────────────────────
# Internals
# ─────────────────────────────────────────────────────────────────────────────
def _try_literal_ip(hostname: str) -> str | None:
    """Return the IP string if ``hostname`` is already a literal, else None.

    IPv6 literals arrive bracket-stripped from ``urlparse.hostname``.
    """
    candidate = hostname
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    try:
        ip_address(candidate)
    except ValueError:
        return None
    return candidate


def _is_private(ip_str: str) -> bool:
    """True if ``ip_str`` falls in any blocked network or is link-local/loopback."""
    try:
        addr = ip_address(ip_str)
    except ValueError:
        # Unparseable → treat as untrusted.
        return True
    if addr.is_loopback or addr.is_link_local or addr.is_private or addr.is_multicast:
        return True
    if addr.is_unspecified or addr.is_reserved:
        return True
    return any(addr in net for net in _PRIVATE_NETS)
