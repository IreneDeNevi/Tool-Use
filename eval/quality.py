from __future__ import annotations

import re
from typing import Any


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _extract_explicit_citations(markdown: str) -> set[str]:
    candidates = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", markdown)
    candidates.extend(re.findall(r"https?://[^\s)\]]+", markdown))
    return {_normalize_url(url) for url in candidates if url.startswith("http")}


def attach_explicit_citations(report_markdown: str, source_urls: list[str]) -> str:
    """Append a numbered references section and normalize URL citations in-line."""
    clean_urls = []
    seen: set[str] = set()
    for url in source_urls:
        norm = _normalize_url(url)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        clean_urls.append(url)

    if not clean_urls:
        return report_markdown

    citation_map = { _normalize_url(url): idx for idx, url in enumerate(clean_urls, start=1) }
    refs_text = "\n\n## Sources\n\n"
    for idx, url in enumerate(clean_urls, start=1):
        refs_text += f"{idx}. {url}\n"

    updated = re.sub(r"https?://[^\s)\]]+", lambda m: f"[{citation_map.get(_normalize_url(m.group(0)), 1)}]", report_markdown)
    if "## Sources" in updated:
        return updated
    return updated.rstrip() + "\n\n" + refs_text


def assess_report_quality(report_markdown: str, source_urls: list[str]) -> dict[str, Any]:
    """Quality heuristic tuned to explicit evidence and source-backed reporting."""
    normalized_sources = list(dict.fromkeys(_normalize_url(url) for url in source_urls if url))
    explicit_citations = _extract_explicit_citations(report_markdown)
    citation_count = len(explicit_citations)
    source_count = len(normalized_sources)
    has_sections = bool(re.search(r"^#{1,6}\s+", report_markdown, flags=re.MULTILINE))
    has_summary = any(keyword in report_markdown.lower() for keyword in ("overview", "summary", "key takeaways", "findings"))

    if source_count == 0:
        return {
            "citation_count": citation_count,
            "source_count": 0,
            "has_sections": has_sections,
            "has_summary": has_summary,
            "citation_coverage": 0.0,
            "groundedness_score": 0.0,
        }

    sourced_coverage = 0.0
    overlapped = set(normalized_sources) & explicit_citations
    sourced_coverage = len(overlapped) / source_count

    structure_score = 0.35 if has_sections else 0.0
    summary_score = 0.2 if has_summary else 0.0
    citation_score = min(0.45, 0.45 * sourced_coverage + 0.1 * min(1.0, citation_count / max(1, source_count)))
    groundedness_score = min(1.0, max(0.0, 0.15 + citation_score + structure_score + summary_score))

    return {
        "citation_count": citation_count,
        "source_count": source_count,
        "has_sections": has_sections,
        "has_summary": has_summary,
        "citation_coverage": round(sourced_coverage, 3),
        "groundedness_score": round(groundedness_score, 3),
    }
