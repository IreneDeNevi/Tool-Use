from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import urllib.robotparser as robotparser

# crawl4ai è sync, quindi lo usiamo in thread
from crawl4ai import WebCrawler

def _sync_crawl(url: str, user_agent: str = "Mozilla/5.0 (compatible; ResearchBot/1.0)"):
    crawler = WebCrawler(user_agent=user_agent)
    result = crawler.crawl(url)
    # result.text_content: testo estratto pulito
    # result.html: HTML grezzo
    return {
        "text": (result.text_content or "")[:200000],
        "html": None,  # evita memorie giganti
    }

def _robots_allows(url: str, user_agent: str = "*") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # se robots.txt non è accessibile, per prudenza ritorna False o True secondo tua policy
        return False

async def crawl_many(urls: List[str], respect_robots: bool = True, concurrency: int = 5) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)

    async def _one(url: str):
        async with sem:
            if respect_robots and not await asyncio.to_thread(_robots_allows, url):
                return {"url": url, "allowed": False, "text": ""}
            try:
                data = await asyncio.to_thread(_sync_crawl, url)
                return {"url": url, "allowed": True, **data}
            except Exception as e:
                return {"url": url, "allowed": False, "error": str(e), "text": ""}

    return await asyncio.gather(*[_one(u) for u in urls])