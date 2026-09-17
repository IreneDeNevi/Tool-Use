# Architecture Overview

This project is a grounded research pipeline built to demonstrate professional tool-use patterns in an AI system. The goal is not to generate a plausible answer from memory, but to gather evidence from the web, retrieve relevant context, and produce a source-aware report.

## 1. High-level workflow

```text
User query
  |
  v
Planner Agent
  |
  v
Web Search Layer
  |
  v
Fetch / Crawl / Extract
  |
  v
Vector Memory (ChromaDB)
  |
  v
Summarizer Agent
  |
  v
Grounded report + artifacts + quality score
```

---

## 2. Main architectural principles

### Evidence-first execution
The system only proceeds when evidence is available. If the search layer yields no usable results, the workflow stops before generating a summary. This prevents a black-box answer from being presented as if it were grounded.

### Separation of concerns
The architecture cleanly separates:

- planning,
- search,
- crawling,
- memory storage,
- summarization,
- evaluation,
- export.

This makes the project easier to test, extend, and explain in a professional setting.

### Provider abstraction
The project is designed to support multiple model providers. The model layer is abstracted so it is not tightly coupled to a single backend.

### Reproducible research artifacts
Every run stores artifacts such as:

- the generated plan,
- retrieved search results,
- extracted summary,
- quality metrics,
- HTML export,
- PDF artifact file.

---

## 3. Component map

### app/
Core application logic and runtime definitions.

- `app/config.py`: environment and configuration loading
- `app/schemas.py`: validated domain models
- `app/orchestrator.py`: orchestrates the full workflow
- `app/report_export.py`: HTML/PDF export logic

### agents/
High-level reasoning agents.

- `agents/planner.py`: creates a structured research plan and normalizes search terms
- `agents/summarizer.py`: builds the grounded markdown summary

### tools/
Execution tools used by the pipeline.

- `tools/web_search.py`: SearXNG client with filtering and fallback logic
- `tools/crawel.py`: crawl and extract content from retrieved pages
- `tools/memory.py`: ChromaDB-based vector memory implementation

### models/
Provider abstraction and model wiring.

- `models/providers.py`: provider interface
- `models/factory.py`: provider factory
- `models/hf_provider.py`: Hugging Face implementation

### eval/
Evaluation heuristics.

- `eval/quality.py`: groundedness and source-awareness scoring

### tests/
The active regression suite.

- `tests/test_refactor.py`: core validation coverage

---

## 4. Why this architecture is stronger than a simple demo

A typical toy chatbot simply answers from model priors. This project instead follows a higher-quality system design:

- it searches the web,
- it retrieves evidence,
- it stores the evidence,
- it summarizes only what was actually supported,
- it computes quality metrics,
- it exports a reproducible artifact.

This is closer to how real AI tooling is designed in production-like environments.

---

## 5. Known limitations

This is still a research-oriented system rather than a full enterprise platform. Some natural next steps are:

- better reranking of retrieved sources,
- stronger citation extraction,
- more advanced evaluation strategies,
- support for additional model providers and data sources,
- a web UI or API layer for end users.

---

## 6. Professional takeaway

The architecture demonstrates portfolio-relevant skills in:

- agent orchestration,
- tool use and retrieval,
- source-grounded generation,
- structured validation,
- reproducible AI workflows,
- production-minded system design.
