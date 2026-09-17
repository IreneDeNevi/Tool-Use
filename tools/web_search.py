from __future__ import annotations

import asyncio
import os
from typing import Any
from urllib.parse import urlparse

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class SearxError(Exception):
    pass


def _base_url() -> str:
    url = os.getenv("SEARXNG_BASE_URL", "").rstrip("/")
    if not url:
        raise SearxError("SEARXNG_BASE_URL is not defined. Add it to your .env file.")
    return url


def _params(query: str, language: str | None, time_range: str | None, engines: list[str] | None, pageno: int = 1) -> dict[str, str]:
    params: dict[str, str] = {"q": query, "format": "json", "pageno": str(pageno)}
    if language:
        params["language"] = language
    if time_range:
        params["time_range"] = time_range
    if engines:
        params["engines"] = ",".join(engines)
    return params


def _searxng_secret() -> str | None:
    return os.getenv("SEARXNG_SECRET")


def _source_domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return None


def _matches_allowed_domains(url: str | None, allowed_domains: list[str] | None) -> bool:
    if not allowed_domains:
        return True
    if not url:
        return False
    domain = _source_domain(url)
    if not domain:
        return False
    allowed = {d.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/") for d in allowed_domains}
    return any(
        domain == candidate or domain.endswith(f".{candidate}") or candidate in domain
        for candidate in allowed
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
)
async def _query_single(
    session: aiohttp.ClientSession,
    query: str,
    language: str | None,
    time_range: str | None,
    engines: list[str] | None,
) -> list[dict[str, Any]]:
    url = f"{_base_url()}/search"
    params = _params(query, language, time_range, engines)
    timeout = aiohttp.ClientTimeout(total=30)
    headers: dict[str, str] = {}
    secret = _searxng_secret()
    if secret:
        headers["X-SEARXNG-SECRET"] = secret

    async with session.get(url, params=params, timeout=timeout, headers=headers) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise SearxError(f"HTTP {resp.status}: {text[:200]}")
        data = await resp.json()

    results: list[dict[str, Any]] = []
    for item in data.get("results", []):
        raw_url = item.get("url")
        results.append(
            {
                "query": query,
                "title": item.get("title"),
                "url": raw_url,
                "snippet": item.get("content") or item.get("snippet") or "",
                "engine": item.get("engine"),
                "category": item.get("category"),
                "source_domain": _source_domain(raw_url),
            }
        )
    return results


async def searxng_search_many(
    queries: list[str],
    language: str | None = None,
    time_range: str | None = None,
    engines: list[str] | None = None,
    concurrency: int = 5,
    allowed_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)

    async def _run_batch(current_time_range: str | None):
        async with aiohttp.ClientSession() as session:

            async def task(q: str):
                async with sem:
                    return await _query_single(session, q, language, current_time_range, engines)

            return await asyncio.gather(*[task(q) for q in queries], return_exceptions=True)

    results_batches = await _run_batch(time_range)
    final = _filter_results(results_batches, allowed_domains)

    if final or time_range is None:
        return final

    fallback_batches = await _run_batch(None)
    fallback_final = _filter_results(fallback_batches, allowed_domains)
    if fallback_final:
        return fallback_final
    return final


def _filter_results(results_batches: list[Any], allowed_domains: list[str] | None) -> list[dict[str, Any]]:
    final: list[dict[str, Any]] = []
    seen: set[str] = set()
    for batch in results_batches:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            url = item.get("url") or ""
            if not url:
                continue
            if not _matches_allowed_domains(url, allowed_domains):
                continue
            key = (url, item.get("query"))
            if key in seen:
                continue
            seen.add(key)
            final.append(item)

    if final or not allowed_domains:
        return final

    unfiltered: list[dict[str, Any]] = []
    seen_unfiltered: set[str] = set()
    for batch in results_batches:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            url = item.get("url") or ""
            if not url:
                continue
            key = (url, item.get("query"))
            if key in seen_unfiltered:
                continue
            seen_unfiltered.add(key)
            unfiltered.append(item)
    return unfiltered


def rank_search_results(results: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Score and sort results by textual relevance and authority signal."""
    q_tokens = {token.lower() for token in query.replace("-", " ").split() if token and len(token) > 2}
    ranked: list[dict[str, Any]] = []

    for item in results:
        title = (item.get("title") or "").lower()
        snippet = (item.get("snippet") or "").lower()
        url = (item.get("url") or "").lower()
        text = f"{title} {snippet} {url}"
        overlap = sum(1 for token in q_tokens if token in text)
        domain_score = 1.0 if any(domain in url for domain in ("python.org", "docs", "wikipedia.org", "arxiv.org", "github.com")) else 0.2
        score = overlap + domain_score + (0.5 if item.get("title") else 0.0)
        ranked.append({**item, "relevance_score": round(score, 3)})

    return sorted(ranked, key=lambda item: item.get("relevance_score", 0.0), reverse=True)


__all__ = ["searxng_search_many", "SearxError", "_matches_allowed_domains", "rank_search_results"]
