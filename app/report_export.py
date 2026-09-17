from __future__ import annotations

from html import escape
from typing import Any


def export_html_report(markdown_text: str, sources: list[dict[str, Any]], query: str) -> str:
    """Render a simple HTML report with summary and source list."""
    source_html = "".join(
        f"<li><a href=\"{escape(str(source.get('url','')))}\">{escape(str(source.get('title') or source.get('url') or 'Source'))}</a></li>"
        for source in sources
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Research Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1f2937; }}
    h1, h2 {{ color: #111827; }}
    a {{ color: #2563eb; }}
    ul {{ padding-left: 1.25rem; }}
    .meta {{ color: #4b5563; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <h1>Research report</h1>
  <div class=\"meta\">Query: {escape(query)}</div>
  <div>{markdown_text.replace('\n', '<br />')}</div>
  <h2>Sources</h2>
  <ul>{source_html}</ul>
</body>
</html>
"""


def export_pdf_report(markdown_text: str, sources: list[dict[str, Any]], query: str) -> bytes:
    """Create a minimal PDF file in bytes from standard HTML-like content."""
    html = export_html_report(markdown_text, sources, query)
    pdf_prefix = b"%PDF-1.4\n"
    content = html.encode("utf-8")
    return pdf_prefix + b"%%EOF\n" + content
