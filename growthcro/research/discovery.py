"""URL discovery + categorization — sitemap-style crawl of a client's domain."""
from __future__ import annotations

import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse


# ── Page categories with URL patterns ───────────────────────────────────────
PAGE_CATEGORIES: dict[str, list[str]] = {
    "about": [
        r"/a-propos", r"/about", r"/qui-sommes-nous", r"/notre-histoire",
        r"/our-story", r"/histoire", r"/company", r"/team", r"/equipe",
        r"/notre-equipe", r"/our-team", r"/fondateur", r"/founder"
    ],
    "testimonials": [
        r"/avis", r"/temoignages", r"/testimonials", r"/reviews",
        r"/clients?[\-/]", r"/success-stories", r"/cas-clients",
        r"/retours-clients", r"/customer-stories"
    ],
    "quality": [
        r"/qualite", r"/quality", r"/engagements", r"/commitments",
        r"/certifications", r"/notre-demarche", r"/fabrication",
        r"/manufacturing", r"/ingredients", r"/composition",
        r"/notre-savoir-faire", r"/expertise"
    ],
    "how_it_works": [
        r"/comment-[cç]a-marche", r"/how-it-works", r"/fonctionnement",
        r"/process", r"/decouvrir", r"/getting-started",
        r"/comment-[cç]a-fonctionne"
    ],
    "press": [
        r"/presse", r"/press", r"/media", r"/actualites", r"/news",
        r"/blog/presse", r"/ils-parlent-de-nous", r"/in-the-press"
    ],
    "faq": [
        r"/faq", r"/aide", r"/help", r"/questions", r"/support",
        r"/centre-aide"
    ],
    "values": [
        r"/valeurs", r"/values", r"/mission", r"/impact",
        r"/responsabilite", r"/rse", r"/csr", r"/durabilite",
        r"/sustainability", r"/manifeste", r"/manifesto"
    ],
    "pricing": [
        r"/prix", r"/pricing", r"/tarifs", r"/plans", r"/offres",
        r"/formules", r"/abonnement"
    ],
    "product": [
        r"/produits?", r"/products?", r"/collections?", r"/shop",
        r"/boutique", r"/catalogue"
    ],
    "blog": [
        r"/blog", r"/articles?", r"/journal", r"/magazine",
        r"/ressources", r"/resources", r"/guides?"
    ],
    "legal": [
        r"/mentions-legales", r"/legal", r"/cgv", r"/cgu",
        r"/privacy", r"/confidentialite", r"/cookies"
    ]
}

# Priority order — about/testimonials/quality first (most useful for LP generation)
PRIORITY_CATEGORIES: list[str] = [
    "about", "testimonials", "quality", "how_it_works", "values",
    "press", "pricing", "faq", "product", "blog", "legal"
]


class LinkExtractor(HTMLParser):
    """Extract all internal links from HTML."""

    def __init__(self, base_domain: str):
        super().__init__()
        self.links: set[str] = set()
        self.base_domain = base_domain

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self._process_link(value)

    def _process_link(self, href: str) -> None:
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return
        if any(href.lower().endswith(ext) for ext in [".pdf", ".jpg", ".png", ".gif", ".svg", ".css", ".js", ".zip"]):
            return

        parsed = urlparse(href)

        if not parsed.netloc:
            path = parsed.path
            if path and not path.startswith("/"):
                path = "/" + path
            if path:
                self.links.add(path)
        elif self.base_domain in parsed.netloc:
            if parsed.path:
                self.links.add(parsed.path)


def categorize_url(path: str) -> str:
    """Categorize a URL path into a content category."""
    path_lower = path.lower()
    for category, patterns in PAGE_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, path_lower):
                return category
    return "other"


def extract_links_from_url(url: str, timeout: int = 20) -> set[str]:
    """Fetch a page and extract all internal links."""
    parsed = urlparse(url)
    domain = parsed.netloc

    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=timeout + 5
        )

        if result.returncode == 0:
            extractor = LinkExtractor(domain)
            extractor.feed(result.stdout)
            return extractor.links
    except Exception:
        pass

    return set()
