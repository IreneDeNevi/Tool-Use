from __future__ import annotations
import asyncio
from typing import List, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig  # v0.8.x API

async def _crawl_one(crawler: AsyncWebCrawler, url: str) -> Dict[str, Any]:
    run_cfg = CrawlerRunConfig(  # Config minimale; estendibile (timeout, filters, ecc.)
        page_timeout=20,
    )
    result = await crawler.arun(url=url, config=run_cfg)
    # result.markdown: testo pulito per LLM; result.html: se ti serve l’HTML
    text = (result.markdown or result.clean_text or "")[:200_000]
    return {"url": url, "allowed": True, "text": text}

async def crawl_many(urls: List[str], respect_robots: bool = True, concurrency: int = 5) -> List[Dict[str, Any]]:
    # Nota: Crawl4AI integra già gestione browser; robots.txt va gestito a monte se vuoi bloccare.
    sem = asyncio.Semaphore(concurrency)
    browser_cfg = BrowserConfig(headless=True, verbose=False)

    out: List[Dict[str, Any]] = []
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        async def task(u: str):
            async with sem:
                try:
                    return await _crawl_one(crawler, u)
                except Exception as e:
                    return {"url": u, "allowed": False, "error": str(e), "text": ""}

        results = await asyncio.gather(*[task(u) for u in urls], return_exceptions=False)
        out.extend(results)

    return out