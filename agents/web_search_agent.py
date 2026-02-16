
import os
import asyncio
import time
from typing import Dict, Any, List
from tools.web_search import searxng_search_many
from tools.crawel import crawl_many     
from tools.memory import VectorMemory


class WebSearchAgent:
    def __init__(self, memory: VectorMemory):
        self.memory = memory

    async def run(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:

        # 1) Ricava i termini
        terms = plan.get("search_terms") or plan.get("core_topics") or []

        # 2) Freshness → time_range SearXNG
        freshness = plan.get("freshness", "pw")
        time_range = {
            "pd": "day",
            "pm": "month",
            "py": "year"
        }.get(freshness, None)

        # 3) Config da .env
        language = os.getenv("SEARXNG_LANGUAGE", "it")
        engines = None
        if os.getenv("SEARXNG_ENGINES"):
            engines = os.getenv("SEARXNG_ENGINES").split(",")

        # 4) Query parallele a SearXNG
        serp = await searxng_search_many(
            terms,
            language=language,
            time_range=time_range,
            engines=engines,
            concurrency=5
        )

        # 5) Crawling delle URL
        urls = list({r["url"] for r in serp if r.get("url")})
        crawled = await crawl_many(urls, respect_robots=True, concurrency=5)

        # 6) Merge + salvataggio memoria
        now = int(time.time())
        final_results = []
        for entry in crawled:
            url = entry["url"]
            body = entry.get("text", "")
            allowed = entry.get("allowed", False)
            origin = [x for x in serp if x["url"] == url]

            result = {
                "url": url,
                "allowed": allowed,
                "text": body,
                "snippet": origin[0]["snippet"] if origin else "",
                "engine": origin[0]["engine"] if origin else None,
                "category": origin[0]["category"] if origin else None,
                "query": origin[0]["query"] if origin else None
            }
            final_results.append(result)

            if allowed and body.strip():
                self.memory.upsert(
                    texts=[body[:200000]],
                    metadatas=[{
                        "type": "web_page",
                        "url": url,
                        "query": result["query"],
                        "engine": result["engine"],
                        "timestamp": now
                    }]
                )

        return final_results
