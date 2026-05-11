#!/usr/bin/env python3
"""Convert markdown to PDF for the GSG audit conversation export."""
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "deliverables" / "CONVERSATION_2026-05-01_GSG_AUDIT_CHALLENGE.md"
PDF_PATH = ROOT / "deliverables" / "CONVERSATION_2026-05-01_GSG_AUDIT_CHALLENGE.pdf"

CSS = """
body {
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
}
h1 {
    font-family: 'Cormorant Garamond', 'Georgia', serif;
    font-size: 26pt;
    color: #0a0c14;
    border-bottom: 2px solid #d4a945;
    padding-bottom: 8px;
    margin-top: 28px;
    margin-bottom: 18px;
}
h2 {
    font-family: 'Cormorant Garamond', 'Georgia', serif;
    font-size: 19pt;
    color: #0f1320;
    border-bottom: 1px solid #d8d4c8;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 12px;
}
h3 {
    font-size: 14pt;
    color: #1f2638;
    margin-top: 18px;
    margin-bottom: 8px;
}
h4 {
    font-size: 12pt;
    color: #1f2638;
    margin-top: 14px;
    margin-bottom: 6px;
}
p { margin: 0 0 10px 0; }
strong { color: #0a0c14; }
em { color: #4d4d4d; }
code {
    font-family: 'JetBrains Mono', 'SF Mono', 'Menlo', monospace;
    font-size: 9.5pt;
    background-color: #f4f1ea;
    color: #b34b3a;
    padding: 1px 5px;
    border-radius: 3px;
}
pre {
    font-family: 'JetBrains Mono', 'SF Mono', 'Menlo', monospace;
    font-size: 9pt;
    background-color: #f7f5ee;
    color: #1a1a1a;
    padding: 10px 12px;
    border-left: 3px solid #d4a945;
    border-radius: 4px;
    overflow-x: auto;
    line-height: 1.4;
    white-space: pre-wrap;
    word-wrap: break-word;
}
pre code {
    background-color: transparent;
    color: inherit;
    padding: 0;
}
table {
    border-collapse: collapse;
    margin: 10px 0;
    width: 100%;
    font-size: 10pt;
}
th, td {
    border: 1px solid #c9c4b4;
    padding: 6px 9px;
    text-align: left;
    vertical-align: top;
}
th {
    background-color: #f4f1ea;
    font-weight: 600;
    color: #0a0c14;
}
tr:nth-child(even) td { background-color: #faf8f1; }
blockquote {
    margin: 12px 0;
    padding: 8px 14px;
    border-left: 3px solid #4d8fff;
    background-color: #f4f7fc;
    color: #1f2638;
    font-style: italic;
}
ul, ol {
    margin: 6px 0 12px 0;
    padding-left: 22px;
}
li { margin: 3px 0; }
hr {
    border: none;
    border-top: 1px solid #d8d4c8;
    margin: 18px 0;
}
"""

def main():
    md_text = MD_PATH.read_text(encoding="utf-8")
    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = "GrowthCRO — Conversation Claude Code GSG Audit Challenge"
    pdf.meta["author"] = "Mathis Fronty x Claude Opus 4.7"
    pdf.meta["subject"] = "Audit profond GSG/AURA + nouvelle stratégie post-audit"
    pdf.meta["keywords"] = "GrowthCRO, GSG, AURA, audit, ChatGPT, lp-creator"
    pdf.add_section(Section(md_text, paper_size="A4"), user_css=CSS)
    pdf.save(str(PDF_PATH))
    size_kb = PDF_PATH.stat().st_size / 1024
    print(f"OK -> {PDF_PATH}")
    print(f"   size: {size_kb:.1f} KB")

if __name__ == "__main__":
    main()
