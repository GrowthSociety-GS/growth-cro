#!/usr/bin/env python3
"""Upload 14 GB screenshots filesystem → Supabase Storage bucket `screenshots`.

SP-11 fix prod : `data/captures/<client>/<page>/screenshots/*.png` = 14 GB /
4831 PNG. Vercel serverless can't bundle that → `/api/screenshots/...` 404 in
prod. This script idempotently mirrors every PNG into the Supabase Storage
bucket created by `supabase/migrations/20260513_0005_screenshots_storage.sql`,
preserving the path scheme `<client>/<page>/<filename>.png` so the route
handler can construct public URLs deterministically.

Usage:
    SUPABASE_URL=https://xyazvwwjckhdmxnohadc.supabase.co \\
    SUPABASE_SERVICE_ROLE_KEY=eyJ... \\
    python3 scripts/upload_screenshots_to_supabase.py

Without those env vars, the script does a DRY-RUN : walks the filesystem,
prints what it would upload, exits 0. Safe to run from CI smoke tests.

Stdlib only (urllib) — no pip install needed. Mirrors the pattern of
`scripts/migrate_v27_to_supabase.py`.

Idempotency : Supabase Storage REST honours the `x-upsert: true` header so
re-runs overwrite existing objects in place. Filesize hash check is not
needed — the 4831 PNG are immutable per capture run.

Exit codes:
    0 — success (or DRY-RUN)
    1 — partial failure (some files failed; summary printed)
    2 — fatal config error (missing path, etc.)
"""

from __future__ import annotations

import os
import ssl
import sys
import time
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

# Add repo root to sys.path so we can import growthcro.config.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from growthcro import config as gc_config  # noqa: E402 — env access doctrine

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CAPTURES_DIR = REPO_ROOT / "data" / "captures"
BUCKET = "screenshots"
PROGRESS_EVERY = 50  # log every N files

# Filter — only upload the 8 screenshots used by AuditScreenshotsPanel.
# Skips the heavy `spatial_*.png` (pipeline-internal Claude vision annotations,
# 2-5 MB each, never displayed in the webapp). Reduces 14 GB → ~140 MB.
USEFUL_SCREENSHOT_FILENAMES = frozenset(
    {
        "desktop_asis_fold.png",
        "desktop_asis_full.png",
        "desktop_clean_fold.png",
        "desktop_clean_full.png",
        "mobile_asis_fold.png",
        "mobile_asis_full.png",
        "mobile_clean_fold.png",
        "mobile_clean_full.png",
    }
)

_cfg = gc_config.get_config()


def _env(name: str, default: str | None = None) -> str | None:
    value = _cfg.system_env(name, default or "")
    return value if value else default


def _dry_run() -> bool:
    return not (_env("SUPABASE_URL") and _env("SUPABASE_SERVICE_ROLE_KEY"))


# macOS Python 3.13 ships without a default CA bundle in some installs (Homebrew
# + python.org), which makes `urllib` SSL handshakes fail. If `certifi` is
# available (already installed for the migrate scripts in some envs) we use its
# bundle; otherwise we fall back to the system default. Pure stdlib path stays
# functional on Linux/CI where the system CA bundle is fine.
def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore[import-not-found]
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


_SSL_CTX = _ssl_context()


# ---------------------------------------------------------------------------
# Filesystem walk
# ---------------------------------------------------------------------------

SLUG_OK = "abcdefghijklmnopqrstuvwxyz0123456789_-"


def _safe_dir(name: str) -> bool:
    """Mirror the webapp's slug regex : alnum + _-, no leading `_`/`.`, no dots."""
    if not name or name[0] in "_.":
        return False
    return all(c in SLUG_OK for c in name.lower())


def _safe_png(name: str) -> bool:
    if not name.lower().endswith(".png"):
        return False
    stem = name[:-4].lower()
    return bool(stem) and stem[0] not in "._" and all(c in SLUG_OK for c in stem)


def walk_screenshots() -> list[tuple[str, str, str, Path]]:
    """Yield (client, page, filename, absolute_path) tuples for every PNG
    under `data/captures/<client>/<page>/screenshots/*.png` that passes the
    same slug/filename whitelist enforced by the webapp's route handler.
    Skips `_*` / `.` directories at every level (matches `listDirSafe` in
    `captures-fs.ts`).
    """
    out: list[tuple[str, str, str, Path]] = []
    if not CAPTURES_DIR.exists():
        return out
    for client_dir in sorted(CAPTURES_DIR.iterdir()):
        if not client_dir.is_dir() or not _safe_dir(client_dir.name):
            continue
        for page_dir in sorted(client_dir.iterdir()):
            if not page_dir.is_dir() or not _safe_dir(page_dir.name):
                continue
            shots_dir = page_dir / "screenshots"
            if not shots_dir.is_dir():
                continue
            for png in sorted(shots_dir.iterdir()):
                if not png.is_file() or not _safe_png(png.name):
                    continue
                # Filter — skip spatial_*.png and other pipeline-internal
                # variants. Only the 8 standard filenames used by the webapp.
                if png.name.lower() not in USEFUL_SCREENSHOT_FILENAMES:
                    continue
                out.append((client_dir.name, page_dir.name, png.name, png))
    return out


# ---------------------------------------------------------------------------
# Supabase Storage REST upload (one object per request, idempotent via upsert)
# ---------------------------------------------------------------------------


class UploadError(RuntimeError):
    pass


def _upload(client: str, page: str, filename: str, abs_path: Path) -> None:
    """POST a single PNG to /storage/v1/object/<bucket>/<client>/<page>/<filename>.
    Uses `x-upsert: true` so a re-run overwrites the existing object instead
    of erroring with 409 Duplicate.
    """
    url_base = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    if not url_base or not key:
        raise UploadError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
    object_path = f"{client}/{page}/{filename}"
    full = f"{url_base.rstrip('/')}/storage/v1/object/{BUCKET}/{object_path}"
    payload = abs_path.read_bytes()
    headers = {
        "authorization": f"Bearer {key}",
        "content-type": "image/png",
        "x-upsert": "true",
        "cache-control": "public, max-age=3600",
    }
    # POST is the documented verb for creating an object. `x-upsert: true`
    # makes it idempotent (Supabase Storage will replace if the key exists).
    req = urlrequest.Request(full, data=payload, method="POST", headers=headers)
    try:
        with urlrequest.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
            resp.read()
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        raise UploadError(f"HTTP {e.code} {object_path}: {detail}") from e
    except urlerror.URLError as e:
        raise UploadError(f"URLError {object_path}: {e.reason}") from e


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if not CAPTURES_DIR.exists():
        print(
            f"[upload-screenshots] Missing captures dir: {CAPTURES_DIR}",
            file=sys.stderr,
        )
        # Not a fatal error in dry-run — just skip everything.
        if _dry_run():
            print("[upload-screenshots] DRY-RUN — nothing to walk, exit 0.")
            return 0
        return 2

    items = walk_screenshots()
    if not items:
        print("[upload-screenshots] No PNG found under data/captures/.")
        return 0
    print(
        f"[upload-screenshots] Found {len(items)} PNG across "
        f"{len({(c, p) for c, p, _, _ in items})} (client, page) tuples."
    )

    dry = _dry_run()
    if dry:
        print(
            "[upload-screenshots] DRY-RUN "
            "(set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY to actually upload)."
        )
        # Print first 3 + last 3 for sanity.
        head = items[:3]
        tail = items[-3:] if len(items) > 6 else []
        for client, page, fn, abs_path in head:
            size_kb = abs_path.stat().st_size // 1024
            print(f"[upload-screenshots]   {client}/{page}/{fn}  ({size_kb} KB)")
        if tail:
            print(f"[upload-screenshots]   ... ({len(items) - 6} more) ...")
            for client, page, fn, abs_path in tail:
                size_kb = abs_path.stat().st_size // 1024
                print(f"[upload-screenshots]   {client}/{page}/{fn}  ({size_kb} KB)")
        total_mb = sum(p.stat().st_size for _, _, _, p in items) // (1024 * 1024)
        print(f"[upload-screenshots] Total payload : ~{total_mb} MB.")
        return 0

    # Live mode
    bucket_url = f"{_env('SUPABASE_URL')}/storage/v1/object/{BUCKET}"
    print(f"[upload-screenshots] Target bucket : {bucket_url}")
    started = time.time()
    success_count = 0
    fail_count = 0
    failures: list[str] = []
    for idx, (client, page, fn, abs_path) in enumerate(items, 1):
        try:
            _upload(client, page, fn, abs_path)
            success_count += 1
        except UploadError as e:
            fail_count += 1
            failures.append(str(e))
        if idx % PROGRESS_EVERY == 0 or idx == len(items):
            elapsed = time.time() - started
            rate = idx / elapsed if elapsed > 0 else 0.0
            print(
                f"[upload-screenshots] ({idx}/{len(items)}) "
                f"ok={success_count} fail={fail_count} "
                f"rate={rate:.1f} files/s elapsed={elapsed:.0f}s"
            )

    elapsed = time.time() - started
    print(
        f"[upload-screenshots] Done in {elapsed:.0f}s — "
        f"success={success_count} fail={fail_count}"
    )
    if failures:
        print("[upload-screenshots] First 5 failures:")
        for msg in failures[:5]:
            print(f"  - {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
