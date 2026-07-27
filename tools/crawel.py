from __future__ import annotations
import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse
from urllib import robotparser

import aiohttp
import trafilatura
from bs4 import BeautifulSoup


def _robots_allowed(url: str, user_agent: str = "*", cache: Dict[str, robotparser.RobotFileParser] | None = None) -> bool:
    if cache is None:
        cache = {}

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    parser = cache.get(base)
    if parser is None:
        parser = robotparser.RobotFileParser()
        parser.set_url(f"{base}/robots.txt")
        try:
            parser.read()
        except Exception:
            return True
        cache[base] = parser

    return parser.can_fetch(user_agent, url)


async def _fetch_url(session: aiohttp.ClientSession, url: str, timeout_seconds: int = 20) -> Dict[str, Any]:
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ToolUseBot/1.0; +https://example.com)"
        }

        async with session.get(url, timeout=timeout, headers=headers) as resp:
            if resp.status != 200:
                return {"url": url, "allowed": False, "error": f"HTTP {resp.status}", "text": ""}
            html = await resp.text(errors="ignore")
    except Exception as exc:
        return {"url": url, "allowed": False, "error": str(exc), "text": ""}

    text = trafilatura.extract(html, include_comments=False, output_format="text")
    if not text:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

    return {"url": url, "allowed": True, "text": (text or "")[:200_000]}


async def crawl_many(urls: List[str], respect_robots: bool = True, concurrency: int = 5) -> List[Dict[str, Any]]:
    """Crawl a list of URLs using aiohttp and extract readable text."""
    sem = asyncio.Semaphore(concurrency)
    out: List[Dict[str, Any]] = []
    robots_cache: Dict[str, robotparser.RobotFileParser] = {}

    async with aiohttp.ClientSession() as session:
        async def task(url: str) -> Dict[str, Any]:
            async with sem:
                if respect_robots and not _robots_allowed(url, cache=robots_cache):
                    return {"url": url, "allowed": False, "error": "Disallowed by robots.txt", "text": ""}
                return await _fetch_url(session, url)

        results = await asyncio.gather(*[task(url) for url in urls], return_exceptions=False)
        out.extend(results)

    return out
