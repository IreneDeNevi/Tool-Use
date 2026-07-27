#!/usr/bin/env python3
"""
Test script to run the research pipeline with predefined queries.
Avoids interactive input issues and allows controlled testing.
"""

import os
import asyncio
import sys
from models.llm import LocalLLM
from tools.memory import VectorMemory
from agents.research_planner import ResearchPlannerAgent
from agents.web_search_agent import WebSearchAgent
from agents.summary_agent import SummaryReportAgent


async def run_test_pipeline(user_query: str, test_num: int = 1):
    """Run a single test cycle with one query."""
    print(f"\n{'='*80}")
    print(f"TEST {test_num}: {user_query[:60]}...")
    print(f"{'='*80}\n")

    try:
        # Initialize components
        llm = LocalLLM()
        memory = VectorMemory(path="./memory_store")

        # 1) Planning (sync LLM)
        print("[1/4] Research Planner Agent...")
        planner = ResearchPlannerAgent(llm, memory)
        plan = planner.plan(user_query)
        print(f"✅ Plan generated: {plan.get('core_topics', [])[:3]}")

        # 2) Search + Crawl (async)
        print("\n[2/4] Web Search Agent (async crawling)...")
        searcher = WebSearchAgent(memory)
        results = await searcher.run(plan)
        print(f"✅ Results fetched: {len(results)} items")

        # 3) Report (sync LLM, but with RAG from memory)
        print("\n[3/4] Summary Report Agent (RAG)...")
        reporter = SummaryReportAgent(llm, memory)
        report = reporter.summarize(results)
        print(f"✅ Report generated: {len(report)} characters")

        # 4) Save report
        report_file = f"summary_report_test{test_num}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[4/4] Report saved → {report_file}")

        # Verification checklist
        print(f"\n📋 Verification Checklist (Test {test_num}):")
        print(f"  ✅ Plan generated: {bool(plan)}")
        print(f"  ✅ Results retrieved: {len(results)} URLs crawled")
        print(f"  ✅ Report created: {bool(report)}")
        print(f"  ✅ File saved: {os.path.exists(report_file)}")

        # Memory check
        memory_dir = "./memory_store/chroma.sqlite3"
        if os.path.exists(memory_dir):
            size_mb = os.path.getsize(memory_dir) / (1024 * 1024)
            print(f"  ✅ Vector store growing: {size_mb:.2f} MB")

        print(f"\n✨ Test {test_num} completed successfully!\n")
        return True

    except Exception as exc:
        print(f"\n❌ Test {test_num} failed with error:")
        print(f"   {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all test queries sequentially."""
    queries = [
        "Confronta le differenze tra React, Vue e Angular per progetti mid-size",
        "Cosa è successo negli ultimi sviluppi di AI? Includi novità su LLM open-source",
        "Come configurare une cluster Kubernetes con monitoring Prometheus",
    ]

    results = []
    for i, query in enumerate(queries, 1):
        success = await run_test_pipeline(query, test_num=i)
        results.append((query, success))

    # Summary
    print(f"\n{'='*80}")
    print("📊 OVERALL TEST SUMMARY")
    print(f"{'='*80}")
    for query, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {query[:70]}")

    passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {passed}/{len(queries)} tests passed")


if __name__ == "__main__":
    # Set required environment variables if not already set
    os.environ.setdefault("SEARXNG_BASE_URL", "http://localhost:8080")
    os.environ.setdefault("SEARXNG_SECRET", "admin")
    os.environ.setdefault("SEARXNG_LANGUAGE", "it")

    if not os.getenv("HUGGINGFACE_HUB_TOKEN"):
        print("⚠️  Warning: HUGGINGFACE_HUB_TOKEN not set. LLM inference will fail.")
        print("   Set it with: export HUGGINGFACE_HUB_TOKEN=hf_xxx")
        sys.exit(1)

    # Run async pipeline
    asyncio.run(main())
