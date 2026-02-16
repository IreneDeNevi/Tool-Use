import asyncio, time
from typing import Dict, Any, List
from tools.web_search import brave_search_many
from tools.crawler import crawl_many
from tools.memory import VectorMemory

class WebSearchAgent:
    def __init__(self, memory: VectorMemory):
        self.memory = memory

    async def run(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        # decidi termini: se non presenti, usa core_topics
        terms = plan.get("search_terms") or plan.get("core_topics") or []
        freshness = plan.get("freshness", "pw")

        # 1) ricerche in parallelo
        serp = await brave_search_many(terms, freshness=freshness, per_query=8, concurrency=5)

        # 2) prendi le URL uniche
        urls = list({r["url"] for r in serp if r.get("url")})

        # 3) crawla in parallelo (rispettando robots.txt)
        crawled = await crawl_many(urls, respect_robots=True, concurrency=5)

        # 4) merge risultati per URL
        serp_by_url = {}
        for r in serp:
            u = r["url"]
            serp_by_url.setdefault(u, []).append(r)

        final = []
        now = int(time.time())
        texts, metas = [], []

        for c in crawled:
            u = c.get("url")
            text = c.get("text") or ""
            allowed = c.get("allowed", False)
            associated = serp_by_url.get(u, [])
            snippet = associated[0]["snippet"] if associated else ""
            query = associated[0]["query"] if associated else None
            title  = associated[0]["title"] if associated else None

            item = {
                "url": u,
                "allowed": allowed,
                "title": title,
                "snippet": snippet,
                "query": query,
                "text": text
            }
            final.append(item)

            # salva in memoria solo se consentito e con testo sufficiente
            if allowed and text.strip():
                texts.append(text[:200000])
                metas.append({
                    "type": "web_page",
                    "url": u,
                    "title": title,
                    "snippet": snippet,
                    "query": query,
                    "timestamp": now
                })

        if texts:
            self.memory.upsert(texts=texts, metadatas=metas)

        return final