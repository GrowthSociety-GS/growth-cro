"""Pytest fixture for the SSRF URL validator (issue #40).

Run: ``python3 -m pytest tests/capture/test_url_validator.py -v``

Network: a single ``socket.getaddrinfo`` call per VALID URL (real DNS).
The 5 valid URLs use well-known public hosts (example.com, weglot.com). If
the runner is offline, monkeypatch ``socket.getaddrinfo`` in conftest.

The 5 reject URLs all fail BEFORE any DNS lookup (literal-IP path or scheme
gate), so they pass offline.
"""
from __future__ import annotations

import pytest

from growthcro.capture.url_validator import (
    URLValidationError,
    URLValidationResult,
    validate_url,
)


# ── Valid URLs (5) ──────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com:8080",
        "https://www.weglot.com",
        "https://www.example.com/path?x=1",
        "https://example.org:443",
    ],
)
def test_valid_urls_accepted(url: str) -> None:
    result = validate_url(url)
    assert isinstance(result, URLValidationResult)
    assert result.url == url
    assert result.scheme in {"http", "https"}
    assert result.hostname
    assert result.port in {80, 443, 8080, 8443}
    assert len(result.resolved_ips) >= 1


# ── Reject URLs (5) — all must fail without network ─────────────────────────
@pytest.mark.parametrize(
    ("url", "expected_reason"),
    [
        ("http://localhost:9000/admin", "blocked_hostname"),
        ("http://169.254.169.254/latest/meta-data/", "blocked_private_ip"),
        ("file:///etc/passwd", "blocked_scheme"),
        ("http://10.0.0.1", "blocked_private_ip"),
        ("http://192.168.1.1:22", "blocked_port"),
    ],
)
def test_invalid_urls_rejected(url: str, expected_reason: str) -> None:
    with pytest.raises(URLValidationError) as exc_info:
        validate_url(url)
    assert exc_info.value.reason == expected_reason
    assert exc_info.value.url == url


# ── Hardening — additional gates beyond the 10 mandated by acceptance ──────
@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "javascript:alert(1)",
        "data:text/html,<script>",
        "gopher://evil.example/",
        "https://127.0.0.1/",
        "https://[::1]/",
        "http://metadata.google.internal/",
        "http://0.0.0.0/",
        "http://example.com:22",
        "http://example.com:25",
    ],
)
def test_additional_rejects(url: str) -> None:
    with pytest.raises(URLValidationError):
        validate_url(url)


def test_result_is_frozen() -> None:
    result = validate_url("https://example.com")
    with pytest.raises(Exception):  # pydantic ValidationError on frozen mutation
        result.scheme = "ftp"  # type: ignore[misc]


def test_argparse_type_validator_accepts_valid() -> None:
    from growthcro.capture.url_validator import argparse_url_type

    assert argparse_url_type("https://example.com") == "https://example.com"


def test_argparse_type_validator_raises_on_invalid() -> None:
    import argparse

    from growthcro.capture.url_validator import argparse_url_type

    with pytest.raises(argparse.ArgumentTypeError):
        argparse_url_type("http://localhost:9000/")
