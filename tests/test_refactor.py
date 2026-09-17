from app.schemas import ResearchPlan, SearchResult
from app.config import Settings
from eval.quality import assess_report_quality
from models.factory import build_model_provider
from agents.planner import PlannerAgent
from tools.web_search import _matches_allowed_domains, searxng_search_many


def test_research_plan_schema_is_valid():
    plan = ResearchPlan(
        intent="AI data engineer portfolio",
        core_topics=["agentic RAG", "web search tools"],
        related_topics=["vector memory", "crawling"],
        search_terms=["agentic RAG architecture", "web search tool use"],
        allowed_domains=["github.com", "arxiv.org"],
        freshness="pw",
        quality_constraints=["source grounding", "citation support"],
    )

    assert plan.intent == "AI data engineer portfolio"
    assert plan.search_terms[0].startswith("agentic")


def test_settings_loads_defaults():
    settings = Settings()
    assert settings.llm_model_name
    assert settings.chroma_collection


def test_model_factory_builds_hf_provider():
    provider = build_model_provider("hf")
    assert provider is not None
    assert provider.name == "hf"


def test_search_result_schema_is_valid():
    result = SearchResult(
        title="Example article",
        url="https://example.com/article",
        snippet="This is a snippet",
        source_domain="example.com",
        query="example query",
    )

    assert result.source_domain == "example.com"
    assert result.url.startswith("https://")


def test_allowed_domains_match_hostname_and_ignore_non_domain_labels():
    assert _matches_allowed_domains("https://docs.python.org/3/library/", ["python.org", "docs", "github.com"])
    assert _matches_allowed_domains("https://en.wikipedia.org/wiki/Python", ["wikipedia.org"])
    assert not _matches_allowed_domains("https://example.com/article", ["official docs"])


def test_quality_requires_sources_for_high_groundedness():
    score = assess_report_quality("# Summary\nThis is a summary without sources.", [])
    assert score["groundedness_score"] == 0.0


def test_planner_normalizes_search_terms_to_keywords():
    normalized = PlannerAgent.normalize_search_term("What is Python and why is it used in data engineering?")
    assert normalized.lower() == "python"
    assert "what" not in normalized.lower()


def test_searxng_search_many_retries_without_time_filter_when_filtered_results_are_empty(monkeypatch):
    seen = []

    async def fake_query_single(session, query, language, time_range, engines):
        seen.append((query, time_range))
        if time_range is None:
            return [{"url": "https://example.com/python", "query": query, "title": "Python", "content": "Python is a language"}]
        return []

    monkeypatch.setattr("tools.web_search._query_single", fake_query_single)

    import asyncio
    result = asyncio.run(searxng_search_many(["python"], time_range="year"))

    assert len(result) == 1
    assert result[0]["url"] == "https://example.com/python"
    assert ("python", "year") in seen
    assert ("python", None) in seen
