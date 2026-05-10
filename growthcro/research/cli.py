"""argparse entrypoint — runs the full discovery + content + brand-identity pipeline."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from growthcro.research.brand_identity import extract_brand_identity
from growthcro.research.content import extract_structured_content, fetch_page_text
from growthcro.research.discovery import (
    PRIORITY_CATEGORIES,
    categorize_url,
    extract_links_from_url,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_intelligence(base_url: str, client_id: str, max_pages: int = 25, verbose: bool = True) -> dict:
    """Main intelligence pipeline."""
    root = _project_root()
    data_dir = root / "data" / "captures"
    parsed = urlparse(base_url)
    domain = parsed.netloc
    base = f"{parsed.scheme}://{domain}"

    output_dir = data_dir / client_id
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path("/tmp") / f"site_intel_{client_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"🔍 Site Intelligence — {base_url}")
        print(f"   Client: {client_id} | Max pages: {max_pages}")
        print()

    # ── Step 1: Discover pages from homepage ──
    if verbose:
        print("📡 Step 1: Discovering pages from homepage...")

    links = extract_links_from_url(base_url)

    common_paths = [
        "/a-propos", "/about", "/a-propos/notre-histoire", "/a-propos/avis-clients",
        "/a-propos/qualite", "/a-propos/comment-fonctionne", "/notre-histoire",
        "/avis", "/temoignages", "/qualite", "/faq", "/prix", "/tarifs",
        "/engagements", "/valeurs", "/presse", "/blog"
    ]
    for path in common_paths:
        links.add(path)

    clean_links: set[str] = set()
    for link in links:
        link = link.rstrip("/")
        if not link:
            link = "/"
        if len(link) > 150:
            continue
        if "?" in link or "#" in link:
            continue
        clean_links.add(link)

    if verbose:
        print(f"   Found {len(clean_links)} unique paths")

    # ── Step 2: Categorize ──
    categorized: dict[str, list[str]] = {}
    for path in clean_links:
        cat = categorize_url(path)
        categorized.setdefault(cat, []).append(path)

    if verbose:
        print("\n📂 Step 2: Categories discovered:")
        for cat in PRIORITY_CATEGORIES:
            if cat in categorized:
                print(f"   {cat}: {len(categorized[cat])} pages — {categorized[cat][:3]}")

    # ── Step 3: Fetch priority pages ──
    if verbose:
        print(f"\n🌐 Step 3: Fetching priority pages (max {max_pages})...")

    pages_fetched: dict[str, dict] = {}
    fetch_count = 0

    if verbose:
        print(f"   → Fetching: / (homepage)")
    text, ok = fetch_page_text(base_url, tmp_dir)
    if ok:
        pages_fetched["homepage"] = extract_structured_content(text, "homepage", base_url)
        fetch_count += 1

    for category in PRIORITY_CATEGORIES:
        if fetch_count >= max_pages:
            break

        paths = categorized.get(category, [])
        paths.sort(key=len)

        for path in paths[:3]:
            if fetch_count >= max_pages:
                break

            url = base + path
            if verbose:
                print(f"   → Fetching: {path} ({category})")

            text, ok = fetch_page_text(url, tmp_dir)
            if ok and len(text) < 200:
                ok = False

            if ok:
                page_key = f"{category}_{path.replace('/', '_').strip('_')}"
                pages_fetched[page_key] = extract_structured_content(text, category, url)
                fetch_count += 1
            else:
                if verbose:
                    print(f"     ✗ Failed or empty")

            time.sleep(0.5)

    # ── Step 4: Extract Brand Identity ──
    if verbose:
        print(f"\n🎨 Step 4: Extracting brand identity (colors, fonts, style)...")

    brand_identity: dict = {}
    homepage_html = ""

    ghost_page = data_dir / client_id / "home" / "page.html"
    if ghost_page.exists():
        homepage_html = ghost_page.read_text(errors="replace")
        if verbose:
            print(f"   Using cached ghost capture: {ghost_page} ({len(homepage_html)} chars)")
    else:
        try:
            result = subprocess.run(
                ["curl", "-sL", "--max-time", "20", "-A",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                 base_url],
                capture_output=True, text=True, timeout=25
            )
            if result.returncode == 0 and len(result.stdout) > 500:
                homepage_html = result.stdout
                if verbose:
                    print(f"   Fetched homepage HTML: {len(homepage_html)} chars")
        except Exception as e:
            if verbose:
                print(f"   ✗ Failed to fetch homepage: {e}")

    if homepage_html:
        brand_identity = extract_brand_identity(homepage_html, base_url, verbose=verbose)
        if verbose:
            p = brand_identity.get("palette", {})
            f = brand_identity.get("fonts", {})
            print(f"   ✅ Palette: primary={p.get('primary')}, bg={p.get('background')}, "
                  f"{len(p.get('all_colors', []))} colors total")
            print(f"   ✅ Fonts: heading={f.get('heading_font')}, body={f.get('body_font')}, "
                  f"{len(f.get('all_fonts', []))} fonts total")
            mood = brand_identity.get("style_mood", {})
            print(f"   ✅ Mood: {', '.join(mood.get('descriptors', []))}")
    else:
        if verbose:
            print("   ⚠️ No HTML available — brand identity extraction skipped")

    # ── Step 5: Build site_intel.json ──
    site_intel = {
        "meta": {
            "crawl_date": time.strftime("%Y-%m-%d"),
            "base_url": base_url,
            "client_id": client_id,
            "pages_discovered": len(clean_links),
            "pages_fetched": fetch_count,
            "categories_found": {cat: len(paths) for cat, paths in categorized.items() if cat != "other"},
            "has_brand_identity": bool(brand_identity),
            "note": "All content extracted from live pages. Never invented or assumed."
        },
        "brand_identity": brand_identity,
        "sitemap": {cat: paths for cat, paths in categorized.items()},
        "pages": pages_fetched,
        "summary": _build_summary(pages_fetched, client_id, base_url)
    }

    output_path = output_dir / "site_intel.json"
    output_path.write_text(json.dumps(site_intel, indent=2, ensure_ascii=False))

    if verbose:
        print(f"\n✅ Done! {fetch_count} pages extracted → {output_path}")
        print(f"   Categories: {', '.join(cat for cat in PRIORITY_CATEGORIES if cat in categorized)}")

    return site_intel


def _build_summary(pages: dict, client_id: str, base_url: str) -> dict:
    summary: dict = {
        "client_id": client_id,
        "base_url": base_url,
        "content_available": {}
    }
    for key, page in pages.items():
        cat = page.get("category", "other")
        summary["content_available"].setdefault(cat, []).append({
            "url": page["url"],
            "text_length": page["text_length"],
            "has_useful_content": page["text_length"] > 300
        })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="V15 Site Intelligence Crawler")
    parser.add_argument("--url", required=True, help="Base URL to crawl")
    parser.add_argument("--client", required=True, help="Client ID (slug)")
    parser.add_argument("--max-pages", type=int, default=25, help="Max pages to fetch (default 25)")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    args = parser.parse_args()

    result = run_intelligence(
        base_url=args.url,
        client_id=args.client,
        max_pages=args.max_pages,
        verbose=not args.quiet
    )

    print(json.dumps({"status": "OK", "pages_fetched": result["meta"]["pages_fetched"]}, indent=2))


if __name__ == "__main__":
    main()
