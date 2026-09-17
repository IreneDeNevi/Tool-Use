from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas import ResearchPlan
from eval.quality import assess_report_quality
from models.factory import build_model_provider
from tools.crawel import crawl_many
from tools.memory import VectorMemory
from tools.web_search import searxng_search_many


class ResearchOrchestrator:
    """Coordinates the grounded research pipeline end-to-end."""

    def __init__(self, model_provider_name: str = "hf"):
        self.provider = build_model_provider(model_provider_name)
        self.memory = VectorMemory()

    async def run(self, user_query: str) -> dict[str, Any]:
        from agents.planner import PlannerAgent
        from agents.summarizer import SummarizerAgent

        planner = PlannerAgent(self.provider, self.memory)
        plan = planner.plan(user_query)

        search_results = await self._search(plan)
        if not search_results:
            raise RuntimeError(
                "No search results were retrieved. The workflow stopped before summarization to avoid a black-box answer without evidence."
            )

        documents = await self._fetch_and_index(search_results)
        summary = SummarizerAgent(self.provider, self.memory).summarize(documents, user_query)

        run_dir = Path(settings.project_root) / "artifacts" / "runs" / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "plan.json").write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "search_results.json").write_text(json.dumps([result for result in search_results], ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "summary.md").write_text(summary, encoding="utf-8")

        source_urls = [item.get("url") for item in search_results if item.get("url")]
        quality = assess_report_quality(summary, source_urls)
        (run_dir / "quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "plan": plan,
            "search_results": search_results,
            "documents": documents,
            "summary": summary,
            "run_dir": str(run_dir),
            "quality": quality,
        }

    async def _search(self, plan: ResearchPlan) -> list[Any]:
        terms = plan.search_terms or plan.core_topics
        return await searxng_search_many(
            queries=terms,
            language=settings.searxng_language,
            time_range=self._to_time_range(plan.freshness),
            engines=settings.searxng_engines or None,
            concurrency=4,
            allowed_domains=plan.allowed_domains,
        )

    async def _fetch_and_index(self, search_results: list[Any]) -> list[Any]:
        urls = list({item.get("url") for item in search_results if item.get("url")})
        crawled = await crawl_many(urls, respect_robots=True, concurrency=4)

        for item in crawled:
            if item.get("allowed") and item.get("text"):
                self.memory.upsert(
                    texts=[item["text"][:200000]],
                    metadatas=[{
                        "type": "web_page",
                        "url": item["url"],
                        "timestamp": int(time.time()),
                    }],
                )

        return crawled

    @staticmethod
    def _to_time_range(freshness: str) -> str | None:
        mapping = {"pd": "day", "pw": "week", "pm": "month", "py": "year"}
        return mapping.get(freshness, None)
