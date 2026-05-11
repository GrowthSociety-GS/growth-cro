#!/usr/bin/env python3
"""Convert V26.Z bundle markdown to PDF + TXT for ChatGPT upload."""
from pathlib import Path
import shutil
from markdown_pdf import MarkdownPdf, Section

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "GROWTHCRO_FULL_AUDIT_BUNDLE_V26Z_2026-05-02.md"
PDF_PATH = ROOT / "GROWTHCRO_FULL_AUDIT_BUNDLE_V26Z_2026-05-02.pdf"
TXT_PATH = ROOT / "GROWTHCRO_FULL_AUDIT_BUNDLE_V26Z_2026-05-02.txt"

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
}
h3 { font-size: 14pt; color: #1f2638; margin-top: 18px; }
h4 { font-size: 12pt; color: #1f2638; margin-top: 14px; }
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
    padding: 10px 12px;
    border-left: 3px solid #d4a945;
    border-radius: 4px;
    overflow-x: auto;
    line-height: 1.4;
    white-space: pre-wrap;
}
pre code { background-color: transparent; color: inherit; padding: 0; }
table { border-collapse: collapse; margin: 10px 0; width: 100%; font-size: 10pt; }
th, td { border: 1px solid #c9c4b4; padding: 6px 9px; text-align: left; vertical-align: top; }
th { background-color: #f4f1ea; font-weight: 600; color: #0a0c14; }
tr:nth-child(even) td { background-color: #faf8f1; }
blockquote {
    margin: 12px 0; padding: 8px 14px;
    border-left: 3px solid #4d8fff;
    background-color: #f4f7fc;
    color: #1f2638; font-style: italic;
}
ul, ol { margin: 6px 0 12px 0; padding-left: 22px; }
li { margin: 3px 0; }
hr { border: none; border-top: 1px solid #d8d4c8; margin: 18px 0; }
"""

def main():
    md_text = MD_PATH.read_text(encoding="utf-8")

    # Generate PDF
    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = "GrowthCRO V26.Z — Full Audit Bundle for ChatGPT"
    pdf.meta["author"] = "Mathis Fronty x Claude Opus 4.7"
    pdf.meta["subject"] = "Bundle de challenge post-V26.Z (humanlike 66/80, gap collègue 1pt)"
    pdf.add_section(Section(md_text, paper_size="A4"), user_css=CSS)
    pdf.save(str(PDF_PATH))
    pdf_size = PDF_PATH.stat().st_size / 1024

    # Generate TXT (just copy md, ChatGPT lit md comme txt)
    shutil.copy(MD_PATH, TXT_PATH)
    txt_size = TXT_PATH.stat().st_size / 1024

    print(f"OK PDF -> {PDF_PATH.name} ({pdf_size:.1f} KB)")
    print(f"OK TXT -> {TXT_PATH.name} ({txt_size:.1f} KB)")
    print(f"OK MD  -> {MD_PATH.name} ({MD_PATH.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
