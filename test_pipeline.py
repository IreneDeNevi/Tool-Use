#!/usr/bin/env python3
"""Run the research pipeline with predefined queries."""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)

REQUIRED_ENVIRONMENT = (
	"SEARXNG_BASE_URL",
	"SEARXNG_SECRET",
	"SEARXNG_LANGUAGE",
	"HUGGINGFACE_HUB_TOKEN",
	"LLM_MODEL_NAME",
	"CHROMA_HOST",
	"CHROMA_PORT",
	"CHROMA_SSL",
	"CHROMA_PERSIST_PATH",
	"CHROMA_COLLECTION",
	"CHROMA_EMBEDDING_MODEL",
)

from agents.research_planner import ResearchPlannerAgent
from agents.summary_agent import SummaryReportAgent
from agents.web_search_agent import WebSearchAgent
from models.llm import LocalLLM
from tools.memory import VectorMemory


async def run_test_pipeline(user_query: str, test_num: int = 1) -> bool:
	"""Run a single end-to-end pipeline cycle."""
	print(f"\n{'=' * 80}")
	print(f"TEST {test_num}: {user_query[:60]}...")
	print(f"{'=' * 80}\n")

	try:
		llm = LocalLLM()
		memory = VectorMemory()

		print("[1/4] Research Planner Agent...")
		planner = ResearchPlannerAgent(llm, memory)
		plan = planner.plan(user_query)
		print(f"Plan generated: {plan.get('core_topics', [])[:3]}")

		print("\n[2/4] Web Search Agent (async crawling)...")
		searcher = WebSearchAgent(memory)
		results = await searcher.run(plan)
		print(f"Results fetched: {len(results)} items")
		if not results:
			raise RuntimeError("SearXNG returned no results for the generated research plan")

		print("\n[3/4] Summary Report Agent (RAG)...")
		reporter = SummaryReportAgent(llm, memory)
		report = reporter.summarize(results)
		print(f"Report generated: {len(report)} characters")

		report_file = f"summary_report_test{test_num}.md"
		with open(report_file, "w", encoding="utf-8") as file:
			file.write(report)
		print(f"\n[4/4] Report saved: {report_file}")

		print(f"\nVerification checklist (Test {test_num}):")
		print(f"  Plan generated: {bool(plan)}")
		print(f"  Results retrieved: {len(results)} URLs crawled")
		print(f"  Report created: {bool(report)}")
		print(f"  File saved: {os.path.exists(report_file)}")

		memory_file = "./memory_store/chroma.sqlite3"
		if os.path.exists(memory_file):
			size_mb = os.path.getsize(memory_file) / (1024 * 1024)
			print(f"  Vector store size: {size_mb:.2f} MB")

		return True
	except Exception as exc:
		print(f"\nTest {test_num} failed: {type(exc).__name__}: {exc}")
		import traceback

		traceback.print_exc()
		return False


async def main() -> None:
	"""Run all predefined test queries sequentially."""
	queries = [
		"Compare React, Vue, and Angular for mid-size projects",
		"What are the latest developments in AI and open-source LLMs?",
		"How do I configure a Kubernetes cluster with Prometheus monitoring?",
	]

	results = []
	for index, query in enumerate(queries, 1):
		success = await run_test_pipeline(query, test_num=index)
		results.append((query, success))

	print(f"\n{'=' * 80}")
	print("OVERALL TEST SUMMARY")
	print(f"{'=' * 80}")
	for query, success in results:
		status = "PASS" if success else "FAIL"
		print(f"{status}: {query[:70]}")

	passed = sum(success for _, success in results)
	print(f"\nTotal: {passed}/{len(queries)} tests passed")


if __name__ == "__main__":
	missing = [name for name in REQUIRED_ENVIRONMENT if not os.getenv(name)]
	if missing:
		print("Missing required variables in .env: " + ", ".join(missing))
		sys.exit(1)

	asyncio.run(main())
