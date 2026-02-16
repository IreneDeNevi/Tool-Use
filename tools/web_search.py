from __future__ import annotations
import os
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import List, Dict, Any, Optional

class SearxError(Exception):
    pass

def _base_url() -> str:
    url = os.getenv("SEARXNG_BASE_URL", "").rstrip("/")
    if not url:
        raise SearxError("SEARXNG_BASE_URL non definita. Aggiungila nel .env")
    return url

def _params(query: str,
            language: Optional[str],
            time_range: Optional[str],
            engines: Optional[List[str]],
            pageno: int = 1) -> Dict[str, str]:
    params = {
        "q": query,
        "format": "json",
        "pageno": str(pageno)
    }
    if language:
        params["language"] = language
    if time_range:
        params["time_range"] = time_range      # day | month | year
    if engines:
        params["engines"] = ",".join(engines)
    return params

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
)
async def _query_single(session: aiohttp.ClientSession,
                        query: str,
                        language: Optional[str],
                        time_range: Optional[str],
                        engines: Optional[List[str]]) -> List[Dict[str, Any]]:
    url = f"{_base_url()}/search"
    params = _params(query, language, time_range, engines)
    timeout = aiohttp.ClientTimeout(total=30)

    async with session.get(url, params=params, timeout=timeout) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise SearxError(f"HTTP {resp.status}: {text[:200]}")
        data = await resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "query": query,
            "title": item.get("title"),
            "url": item.get("url"),
            "snippet": item.get("content") or item.get("snippet") or "",
            "engine": item.get("engine"),
            "category": item.get("category")
        })
    return results

async def searxng_search_many(queries: List[str],
                              language: Optional[str] = None,
                              time_range: Optional[str] = None,
                              engines: Optional[List[str]] = None,
                              concurrency: int = 5) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession() as session:

        async def task(q):
            async with sem:
                return await _query_single(
                    session, q, language, time_range, engines
                )

        results_batches = await asyncio.gather(
            *[task(q) for q in queries],
            return_exceptions=True
        )

    final = []
    for batch in results_batches:
        if isinstance(batch, Exception):
            continue
        final.extend(batch)
    return final