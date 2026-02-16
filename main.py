import asyncio
from models.llm import LocalLLM
from tools.memory import VectorMemory
from agents.research_planner import ResearchPlannerAgent
from agents.web_search_agent import WebSearchAgent
from agents.summary_agent import SummaryReportAgent

async def async_pipeline(user_query: str):
    llm = LocalLLM()
    memory = VectorMemory(path="./memory_store")

    # 1) Pianificazione (sync LLM)
    planner = ResearchPlannerAgent(llm, memory)
    plan = planner.plan(user_query)
    print("Piano di ricerca:", plan)

    # 2) Ricerca + Crawl (async)
    searcher = WebSearchAgent(memory)
    results = await searcher.run(plan)
    print(f"Risultati totali: {len(results)}")

    # 3) Report (sync LLM, ma con RAG dalla memoria)
    reporter = SummaryReportAgent(llm, memory)
    report = reporter.summarize(results)

    with open("summary_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report salvato → summary_report.md")

def main():
    user_input = input("Descrivi la tua ricerca:\n> ")
    asyncio.run(async_pipeline(user_input))

if __name__ == "__main__":
    main()