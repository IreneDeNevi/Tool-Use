from __future__ import annotations
import os
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import List, Dict, Any

BRAVE_URL = os.getenv("BRAVE_URL", "")

class SearchError(Exception):
    pass

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
)
async def brave_search_one(session: aiohttp.ClientSession, query: str, freshness: str = "pw", count: int = 8) -> List[Dict[str, Any]]:
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": os.getenv("BRAVE_API_KEY", "")
    }
    if not headers["X-Subscription-Token"]:
        raise SearchError("BRAVE_API_KEY non impostata nell'ambiente.")

    params = {"q": query, "freshness": freshness, "count": count}

    async with session.get(BRAVE_URL, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise SearchError(f"Brave API status={resp.status} body={text[:300]}")
        data = await resp.json()

    results = []
    for group in ("web", "news"):
        if group in data and "results" in data[group]:
            for r in data[group]["results"]:
                results.append({
                    "query": query,
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("description") or r.get("snippet") or ""
                })
    return results

async def brave_search_many(queries: List[str], freshness: str = "pw", per_query: int = 8, concurrency: int = 5) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        async def _task(q):
            async with sem:
                return await brave_search_one(session, q, freshness=freshness, count=per_query)
        batches = await asyncio.gather(*[_task(q) for q in queries], return_exceptions=True)

    final = []
    for b in batches:
        if isinstance(b, Exception):
            # puoi loggare b
            continue
        final.extend(b)
    return final