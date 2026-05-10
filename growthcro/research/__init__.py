"""Research layer — full-site crawler + brand-identity extractor (orthogonal to perception)."""
from growthcro.research.discovery import (
    PAGE_CATEGORIES,
    PRIORITY_CATEGORIES,
    LinkExtractor,
    categorize_url,
    extract_links_from_url,
)
from growthcro.research.content import (
    TextExtractor,
    extract_structured_content,
    fetch_page_text,
    ghost_fetch,
)
from growthcro.research.brand_identity import extract_brand_identity, StyleExtractor

__all__ = [
    "PAGE_CATEGORIES", "PRIORITY_CATEGORIES",
    "LinkExtractor", "categorize_url", "extract_links_from_url",
    "TextExtractor", "extract_structured_content", "fetch_page_text", "ghost_fetch",
    "extract_brand_identity", "StyleExtractor",
]
