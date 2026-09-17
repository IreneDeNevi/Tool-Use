from __future__ import annotations

from typing import Any


def assess_report_quality(report_markdown: str, source_urls: list[str]) -> dict[str, Any]:
    """Simple quality heuristic for grounded summaries."""
    citations = report_markdown.count("http")
    source_count = len(source_urls)
    has_sections = "#" in report_markdown or "##" in report_markdown
    has_summary = "summary" in report_markdown.lower() or "overview" in report_markdown.lower()

    if source_count == 0:
        groundedness_score = 0.0
    else:
        groundedness_score = min(
            1.0,
            max(
                0.0,
                (citations / max(1, source_count * 2)) + (0.3 if has_sections else 0.0) + (0.2 if has_summary else 0.0),
            ),
        )

    return {
        "citation_count": citations,
        "source_count": source_count,
        "has_sections": has_sections,
        "has_summary": has_summary,
        "groundedness_score": groundedness_score,
    }
