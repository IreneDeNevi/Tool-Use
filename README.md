# Grounded Research Agent with Tool Use

A portfolio-grade research agent that plans a query, searches the web, retrieves relevant pages, stores them in a vector memory, and generates a grounded Markdown report with source-aware citations.

## Why this project

This project demonstrates a practical tool-use architecture for AI systems:

- the model is not left to answer from memory alone
- search, retrieval, and reporting are separated into explicit components
- results are grounded in retrieved documents
- the workflow is structured and reproducible
- the system is designed to be provider-agnostic and easy to extend

## Core architecture

```text
User query
  |
  v
Planner Agent
  |
  v
Web Search Tool -> Fetch/Crawl Tool -> Vector Memory
  |
  v
Summarizer Agent
  |
  v
Markdown report + quality metrics + run artifacts
```

## Components

- `app/config.py`: project settings and runtime configuration
- `app/schemas.py`: domain models and validated payloads
- `app/orchestrator.py`: end-to-end pipeline orchestration
- `agents/planner.py`: structured research plan generation
- `agents/summarizer.py`: grounded summary generation
- `tools/web_search.py`: filtered SearXNG search client
- `tools/crawel.py`: async crawling and text extraction
- `tools/memory.py`: ChromaDB-backed persistent vector memory
- `models/providers.py`: provider contract
- `models/factory.py`: model provider selection
- `eval/quality.py`: lightweight quality heuristics

## Setup

1. Create a virtual environment and install dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

2. Copy the environment template:

```bash
cp .env.example .env
```

3. Fill in the required values in `.env`.

```env
SEARXNG_BASE_URL=http://localhost:8080
SEARXNG_SECRET=
HUGGINGFACE_HUB_TOKEN=your_token_here
LLM_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.3
```

4. Start SearXNG:

```bash
docker compose up -d searxng
```

5. Run the app:

```bash
python main.py
```

## Example workflow

```python
from app.orchestrator import ResearchOrchestrator

orchestrator = ResearchOrchestrator()
result = await orchestrator.run("How do agentic RAG systems differ from classic RAG?")
print(result["summary"])
```

## Portfolio value

This repository demonstrates:

- tool-use design patterns
- source-grounded generation
- retrieval-augmented reasoning
- persistent memory with vector search
- model abstraction for provider flexibility
- production-friendly separation of concerns

## Limitations

This is a solid foundation for a portfolio project, but it is still a research-oriented pipeline rather than a full enterprise system. The next natural steps are:

- stronger evaluation methods
- better citation extraction and grounding validation
- more robust reranking and document filtering
- optional support for additional providers and backends

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
