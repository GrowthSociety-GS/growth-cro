"""Page content fetching + structured extraction (text, certifications, prices, ratings)."""
from __future__ import annotations

import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path


class TextExtractor(HTMLParser):
    """Extract visible text from HTML, stripping scripts/styles."""

    def __init__(self):
        super().__init__()
        self.text: list[str] = []
        self.skip = False
        self.skip_tags = {"script", "style", "noscript", "svg", "path"}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip = True

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())

    def get_text(self) -> str:
        return "\n".join(self.text)


def fetch_page_text(url: str, tmp_dir: Path, timeout: int = 30) -> tuple[str, bool]:
    """Fetch a page via curl and extract text. Returns (text, success)."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=timeout + 5
        )

        if result.returncode == 0 and len(result.stdout) > 500:
            extractor = TextExtractor()
            extractor.feed(result.stdout)
            text = extractor.get_text()
            if len(text) > 100:
                return text, True

        return "", False
    except Exception as e:
        return f"ERROR: {e}", False


def ghost_fetch(url: str, output_path: Path, timeout: int = 35) -> tuple[str, bool]:
    """Fetch a page via ghost_capture.js (Playwright). Returns (text, success)."""
    ghost = Path(__file__).resolve().parents[2] / "scripts" / "ghost_capture.js"
    if not ghost.exists():
        return "", False

    try:
        subprocess.run(
            ["node", str(ghost), "--url", url, "--output", str(output_path)],
            capture_output=True, text=True, timeout=timeout
        )

        html_file = Path(str(output_path).replace(".json", "") + "/page.html")
        if not html_file.exists():
            html_file = output_path.parent / "page.html"

        if html_file.exists():
            html = html_file.read_text(errors="replace")
            extractor = TextExtractor()
            extractor.feed(html)
            return extractor.get_text(), True

        return "", False
    except Exception as e:
        return f"ERROR: {e}", False


def extract_structured_content(text: str, category: str, url: str) -> dict:
    """Extract structured data from page text based on category."""
    extracted = {
        "url": url,
        "category": category,
        "text_length": len(text),
        "raw_text_preview": text[:2000]
    }

    if category == "about":
        year_matches = re.findall(r'\b(19\d{2}|20[0-2]\d)\b', text)
        if year_matches:
            extracted["years_mentioned"] = list(set(year_matches))

        team_match = re.search(r'(\d+)\s*(?:collaborateurs|personnes|salariés|employés|membres|people|employees)', text, re.I)
        if team_match:
            extracted["team_size_mentioned"] = int(team_match.group(1))

    elif category == "testimonials":
        rating_match = re.search(r'(\d[.,]\d)\s*/\s*5', text)
        if rating_match:
            extracted["rating_found"] = rating_match.group(0)

        count_match = re.search(r'(\d[\d\s,.]*)\s*(?:avis|reviews|témoignages|notes)', text, re.I)
        if count_match:
            extracted["review_count_mentioned"] = count_match.group(0).strip()

    elif category == "quality":
        cert_patterns = [
            r'ISO\s*\d+', r'IFS\s*\w+', r'FEDIAF', r'BIO', r'AB',
            r'HACCP', r'GMP', r'NF\s*\w+', r'CE', r'AFNOR',
            r'B\s*Corp', r'Ecocert', r'Cosmos'
        ]
        certs = []
        for pattern in cert_patterns:
            if re.search(pattern, text, re.I):
                match = re.search(pattern, text, re.I)
                certs.append(match.group(0))
        if certs:
            extracted["certifications_found"] = certs

    elif category == "pricing":
        prices = re.findall(r'(\d+[.,]?\d*)\s*€', text)
        if prices:
            extracted["prices_found"] = prices[:10]

    return extracted
