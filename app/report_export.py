from __future__ import annotations

from html import escape
from io import BytesIO
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
    """Create a valid PDF report from the generated markdown summary."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    story: list[Any] = [
        Paragraph("Research report", styles["Title"]),
        Paragraph(f"Query: {escape(query)}", body_style),
        Spacer(1, 12),
    ]

    for line in markdown_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            story.append(Spacer(1, 6))
            continue

        if cleaned.startswith("# "):
            story.append(Paragraph(cleaned[2:], styles["Heading1"]))
        elif cleaned.startswith("## "):
            story.append(Paragraph(cleaned[3:], styles["Heading2"]))
        elif cleaned.startswith("- "):
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(cleaned[2:], body_style))],
                    bulletType="bullet",
                    leftIndent=18,
                    bulletFontName="Helvetica",
                    bulletFontSize=10,
                )
            )
        else:
            story.append(Paragraph(cleaned.replace("**", ""), body_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Sources", styles["Heading2"]))
    for source in sources:
        url = str(source.get("url") or "")
        title = str(source.get("title") or source.get("url") or "Source")
        if url:
            story.append(Paragraph(f"- {escape(title)}: {escape(url)}", body_style))
        else:
            story.append(Paragraph(f"- {escape(title)}", body_style))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    doc.build(story)
    return buffer.getvalue()
