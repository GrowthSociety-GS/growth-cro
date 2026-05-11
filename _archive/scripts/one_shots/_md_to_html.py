#!/usr/bin/env python3
"""Convert markdown to standalone HTML for ChatGPT-friendly upload."""
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "deliverables" / "CONVERSATION_2026-05-01_GSG_AUDIT_CHALLENGE.md"
HTML_PATH = ROOT / "deliverables" / "CONVERSATION_2026-05-01_GSG_AUDIT_CHALLENGE.html"

CSS = """
body {
  font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: #1a1a1a;
  max-width: 920px;
  margin: 40px auto;
  padding: 0 24px;
  background: #fefdf9;
}
h1 {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 36px;
  color: #0a0c14;
  border-bottom: 2px solid #d4a945;
  padding-bottom: 10px;
  margin-top: 36px;
}
h2 {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 26px;
  color: #0f1320;
  border-bottom: 1px solid #d8d4c8;
  padding-bottom: 6px;
  margin-top: 32px;
}
h3 { font-size: 19px; color: #1f2638; margin-top: 22px; }
h4 { font-size: 16px; color: #1f2638; margin-top: 18px; }
strong { color: #0a0c14; }
em { color: #4d4d4d; }
code {
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-size: 13px;
  background: #f4f1ea;
  color: #b34b3a;
  padding: 2px 6px;
  border-radius: 3px;
}
pre {
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-size: 12.5px;
  background: #f7f5ee;
  color: #1a1a1a;
  padding: 14px 16px;
  border-left: 3px solid #d4a945;
  border-radius: 4px;
  overflow-x: auto;
  line-height: 1.5;
}
pre code { background: transparent; color: inherit; padding: 0; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
  font-size: 14px;
}
th, td {
  border: 1px solid #c9c4b4;
  padding: 8px 11px;
  text-align: left;
  vertical-align: top;
}
th { background: #f4f1ea; font-weight: 600; color: #0a0c14; }
tr:nth-child(even) td { background: #faf8f1; }
blockquote {
  margin: 14px 0;
  padding: 10px 16px;
  border-left: 3px solid #4d8fff;
  background: #f4f7fc;
  color: #1f2638;
  font-style: italic;
}
hr { border: none; border-top: 1px solid #d8d4c8; margin: 24px 0; }
ul, ol { padding-left: 26px; }
li { margin: 4px 0; }
"""

def main():
    md_text = MD_PATH.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
    )
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GrowthCRO — Conversation Claude Code GSG Audit Challenge</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    HTML_PATH.write_text(html, encoding="utf-8")
    size_kb = HTML_PATH.stat().st_size / 1024
    print(f"OK -> {HTML_PATH}")
    print(f"   size: {size_kb:.1f} KB")

if __name__ == "__main__":
    main()
